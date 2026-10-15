# Headless desktop error: evidence boundary

No wire behavior change is made for desktop offers in `UU_DESKTOP_BACKEND=none`.
The viewer can continue showing reconnecting. Do not treat the auto-unlock failure `-5` as a
capture-unavailable error: its observed context is different.

Bounded inspection of the official macOS host's retained disassembly found the protobuf
`gv_pb.ReportError` metadata at 0x1003ef0f0 and fields `action`, `errorCode`, `errorMsg`,
`typeValue`. Capture-manager diagnostics include “captureSetting failed no video track
available” (0x100017584) and “restartCapture failed no video track available” (0x10001c028).
These establish that the official host has capture failure branches, but do not establish a
numeric ReportError mapping or the correct pre-peer signaling response for a host with no desktop.
A REA string query did not return during this run; retained disassembly was used as the bounded
fallback. This is incomplete evidence, not proof that no official error code exists.

Before changing the protocol, trace the relevant failure branch to its actual send call and
confirm the official viewer's response. No proprietary binary, disassembly dump or credentials
are included in this repository.
