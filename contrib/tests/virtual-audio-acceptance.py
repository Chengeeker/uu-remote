#!/usr/bin/env python3
"""Run against an isolated Pulse-compatible daemon whose default is uu-test-physical.
Never reads a real output monitor, prints sample values, or persists sound content.
Usage: PULSE_SERVER=unix:/private/test/socket python3 virtual-audio-acceptance.py /path/to/binary
"""
import json, math, os, pathlib, signal, struct, subprocess, sys, tempfile, threading, time
binary = str(pathlib.Path(sys.argv[1]).resolve())
def pactl(*args):
    return subprocess.check_output(['pactl', *args], text=True, stderr=subprocess.DEVNULL).strip()
assert pactl('get-default-sink') == 'uu-test-physical', 'Requires an isolated test daemon'
assert os.environ.get('PULSE_SERVER', '').startswith('unix:'), 'Set an explicit private test socket'

def sink_id(name):
    return next(line.split()[0] for line in pactl('list','short','sinks').splitlines() if line.split()[1] == name)

def input_sinks():
    return [line.split()[1] for line in pactl('list','short','sink-inputs').splitlines()]

with tempfile.TemporaryDirectory(prefix='uu-audio-test-') as directory:
    env = dict(os.environ, UU_CONFIG=str(pathlib.Path(directory)/'config.json'))
    record = pathlib.Path(directory)/'virtual_audio.json'
    probe = None
    playback = subprocess.Popen(['pacat','--playback','--raw','--format=s16le','--rate=48000','--channels=2','--latency-msec=30'],
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    stopped = threading.Event()
    # Synthetic, bounded, repeating waveform. No sample data is logged or saved.
    block = b''.join(struct.pack('<hh', *(2*[int(4000*math.sin(2*math.pi*440*n/48000))])) for n in range(4800))
    def publish():
        try:
            while not stopped.is_set():
                playback.stdin.write(block); playback.stdin.flush(); time.sleep(.08)
        except (BrokenPipeError, ValueError):
            pass
    writer = threading.Thread(target=publish, daemon=True); writer.start()
    def start():
        return subprocess.Popen([binary,'virtual-audio-probe'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    def wait_virtual():
        deadline = time.monotonic()+3
        while time.monotonic()<deadline:
            if pactl('get-default-sink') == 'uu-remote-sink': return
            time.sleep(.05)
        raise AssertionError('virtual default not selected')
    try:
        time.sleep(.3)
        assert sink_id('uu-test-physical') in input_sinks()
        probe = start(); wait_virtual()
        assert sink_id('uu-remote-sink') in input_sinks(), 'Existing stream not moved'
        recording = subprocess.Popen(['parec','--device=uu-remote-sink.monitor','--raw','--format=s16le','--rate=48000','--channels=2','--latency-msec=30'],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            # Drain continuously: sleeping with a PIPE can fill it with startup silence
            # and prevent later signal bytes from reaching the reader.
            try:
                samples, _ = recording.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                recording.terminate(); samples, _ = recording.communicate(timeout=2)
            assert samples and any(samples), f'Synthetic monitor absent/silent: bytes={len(samples)}'
        finally:
            if recording.poll() is None: recording.kill(); recording.wait()
        assert probe.wait(timeout=8) == 0
        assert pactl('get-default-sink') == 'uu-test-physical' and not record.exists()
        assert sink_id('uu-test-physical') in input_sinks(), 'Stream not restored'
        probe = start(); wait_virtual(); probe.kill(); probe.wait(timeout=2)
        assert record.exists()
        probe = start(); assert probe.wait(timeout=8) == 0
        assert pactl('get-default-sink') == 'uu-test-physical' and not record.exists()
        assert not any('sink_name=uu-remote-sink' in line for line in pactl('list','short','modules').splitlines())
        print(json.dumps(dict(existing_stream_moved=True, synthetic_monitor_signal=True, restored=True, sigkill_recovered=True)))
    finally:
        stopped.set(); playback.terminate(); playback.wait(timeout=2); writer.join(timeout=1)
        if probe is not None and probe.poll() is None: probe.kill(); probe.wait()
        # If an assertion interrupted routing, the next probe recovers and restores it.
        if record.exists(): subprocess.run([binary,'virtual-audio-probe'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
