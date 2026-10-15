# v0.1.7 development validation

Baseline: v0.1.6 (`7beb3ae`), isolated feature branch. No deployment or release is implied.

- VAAPI: explicit selection, NV12 upload/scale order, GOP, no B-frames, async depth and AUD
  option test. Virtio/virgl exposes VideoProc only, so Intel/AMD encoding is **未实机验证**.
  Both capture pipelines are compiled/tested. Process and in-process XDamage probes failed
  hardware initialization and delivered CPU fallback with an IDR. In-process x11grab/invalid-device fallback also passed with an IDR, using an isolated FFmpeg 6 prefix (FFmpeg configure names that input `xcbgrab`).
- Virtual audio: PulseAudio (isolated daemon) and PipeWire-pulse null-sink selection, default restoration,
  module cleanup and recovery after SIGKILL passed. PipeWire monitor Opus encoding passed.
  Runtime routing changes restart the scoped
  audio producer. An isolated-daemon fixture checks an already-playing synthetic stream is
  moved, the monitor contains nonzero signal, and the stream is restored. Audibility at an
  official viewer remains a human check.
- User bus: dedicated VM boot with display-manager disabled and linger enabled: virtual Xfce
  and host services active, cloud availability ready, authenticated X11 capture 1920x1080.
  User-manager-activated GNOME Terminal inherited DISPLAY=:99 and its window was found there.
  GTK input fixture: absolute/relative pointer, click and synthetic text passed, 9 down/9 up.
  See [Mac checklist](../../contrib/virtual-desktop/ACCEPTANCE.md) for official client acceptance.
- Arch/Omarchy-equivalent Hyprland: native Wayland capture and five-frame H.264/IDR probe passed.
  uinput fixture received motion, click, synthetic text and balanced 9 down/9 up. The old fixture's
  exact-32-pixel relative flag remains false with compositor scaling/sensitivity; cursor position
  did advance after relative injection, so no exact delta claim is made. Native clipboard passed
  incoming Unicode, empty, maximum UTF-8, no echo, outgoing Unicode/empty and oversized rejection.
  Official Mac end-to-end acceptance remains a human checklist.
- Headless error: no proven official unavailable-desktop code; behavior retained.
- KMS: virtio's active 1152x648 linear framebuffer was readable, both from a capability-granted
  root-owned binary and while no compositor owned DRM master. Opening an unowned primary node
  may implicitly grant DRM master; the prototype makes no explicit master/modeset calls.
  With Hyprland owning DRM master, unprivileged capture failed clearly; capability-granted
  capture and five-frame H.264/IDR probe passed. Capability grants were revoked after testing.
  A GDM greeter session existed, but its captured PNG was solid black. This is a failed visual
  acceptance, despite successful read calls. Intel/AMD, lock/greeter and overlay coverage remain unverified.

These results are development checks before review. Do not claim official
Mac client acceptance or Intel/AMD validation from unit tests or successful VM framebuffer reads.

Test matrix: macOS default / wayland / wayland,portal / wayland,portal,kms each 110 passed,
1 ignored. Linux default 110 passed/1 ignored; wayland, wayland,portal and wayland,portal,kms
each 110 passed/2 ignored. Linux inproc-av: 110 passed/1 ignored, FFmpeg 6.1.2 + isolated
libclang 18 (rolling Arch clang 23 is incompatible with the existing bindgen 0.64).
