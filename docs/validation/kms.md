# Experimental KMS backend

Build on Linux with `cargo build --release --features kms` (Debian `libdrm-dev`, Arch `libdrm`).
Explicitly set `UU_DESKTOP_BACKEND=kms`; `UU_KMS_DEVICE` defaults to `/dev/dri/card0`, a primary
node, not a render node. Nothing selects KMS automatically. The normal binary has no KMS feature.

This prototype reads the primary plane of the first active CRTC via universal-plane enumeration, libdrm GETFB2 and MAP_DUMB, copies linear
XRGB8888/ARGB8888 rows into BGRA, and sends the existing FFmpeg pipeline. Scaling and encoding
still copy through CPU memory; this is not Sunshine's zero-copy GPU capture. It does not set modes,
become DRM master, change VT, disable locks or unlock sessions. Lock/greeter visibility is a goal,
not a guarantee: no active output, non-mappable/tiled/compressed buffers, overlay-only content and
mode changes can fail. Restart the host after mode changes. Tearing is possible; overlay/cursor planes are not composited.
Unsupported formats/maps return explicit local errors. A successful read does not establish GPU
buffer visibility: the virtio/virgl VM returned solid black at the GDM greeter even with universal
primary-plane enumeration and capability granted. This is **failed visual acceptance**, not working
login-screen support. GPU-rendered buffers likely need dma-buf/EGL import and GPU-to-CPU download;
that path is not implemented by this MAP_DUMB prototype. An initial uniformly black frame emits a
warning, but legitimate black screens cannot be distinguished reliably from stale GPU storage.

## Permissions and security

GETFB2 framebuffer handles require DRM master or `CAP_SYS_ADMIN`. If deliberately accepting the
risk on a disposable machine, install the reviewed binary in a root-owned, non-user-writable path,
then run `sudo setcap cap_sys_admin+ep /path/to/uuremote-server`. The service account also needs
primary card access (usually a narrowly managed `video` group). **CAP_SYS_ADMIN is broad** and
applies to the whole network-facing process, including dependencies; it is not a sandbox for capture.
Never set the capability on an unreviewed build or general-purpose FFmpeg. Systemd
`NoNewPrivileges=yes`, bounding sets, mounts and containers may prevent it from taking effect.
Use `getcap` to inspect and `sudo setcap -r /path/to/uuremote-server` to revoke; replacing a binary
requires a new explicit capability grant. No install script grants it automatically.

`UU_INPUT_BACKEND=uinput` is separate and needs `/dev/uinput`; without it KMS does not fall back
to an unrelated X11 session. KMS has no clipboard session, so clipboard support is not advertised.
Capturing the greeter/lock screen can expose information hidden by desktop portal consent. Restrict
remote access and the service account accordingly. Test first with `desktop-probe` (no path means
no screenshot saved), then `desktop-video-probe`, including permission denial, lock, greeter,
mode changes and capability revocation. Intel/AMD/real-login-screen verification remains required.

Reference design: [Sunshine Linux capture](https://github.com/LizardByte/Sunshine/tree/master/src/platform/linux).
