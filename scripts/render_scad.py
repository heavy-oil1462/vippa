#!/usr/bin/env python3
"""Headless OpenSCAD renderer (no GUI, no X server needed).

By default fetches OpenSCAD (+ Mesa software GL for PNG output) from
nixpkgs and renders via EGL surfaceless. Never download binaries manually
in the sandbox: there, everything comes from the nix store.

No-nix escape hatch: set OPENSCAD=/path/to/openscad and that binary is
used as-is, with the caller's environment untouched (a workstation with
a working GL stack needs nothing extra). The nix path is the pinned
default, and CI uses it too: Mesa's software rasterizer through EGL
surfaceless needs no GPU or X server on the runner.

Usage:
    scripts/render_scad.py <file.scad> [output.(png|stl|dxf)] [extra openscad args...]

Examples:
    scripts/render_scad.py cad/main_assembly.scad                 # -> cad/main_assembly.png
    scripts/render_scad.py cad/panels/example_panel.scad /tmp/panel.stl  # manifold check / export
    scripts/render_scad.py cad/main_assembly.scad top.png --camera=0,0,0,0,0,0,1500 --projection=o
    scripts/render_scad.py cad/main_assembly.scad hero.png --supersample=2  # smooth edges

--supersample=N renders a PNG N times larger and averages it down,
since OpenSCAD has no antialiasing. Plain Python, a few seconds at 2.

Notes (learned in earlier projects, do not rediscover):
- The sandbox's LD_LIBRARY_PATH=/lib makes nix binaries load the system
  libc and crash. We override it with only the GL libs nix should see.
- PNG rendering needs GL: use Mesa software rendering via
  EGL_PLATFORM=surfaceless (no X/xvfb required).
"""

import os
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

_STORE_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "vippa-nix-paths"

# Pinned to a release branch instead of the registry's nixpkgs-unstable:
# hydra has NOT built openscad-unstable on unstable (its lld link fails, so
# `nix build nixpkgs#openscad-unstable` falls into an hour-long source build
# that dies the same way), while the release branches carry the identical
# snapshot prebuilt in cache.nixos.org. scripts/firmware.py takes ESPHome
# (2026.5.1, Zigbee on the ESP32-H2) from this pin too.
NIXPKGS = "github:NixOS/nixpkgs/nixos-26.05"


def nix_path(attr: str) -> str:
    """Resolve a nixpkgs attribute to its store path (cached across runs)."""
    cache = _STORE_CACHE / attr
    if cache.exists():
        p = cache.read_text().strip()
        if Path(p).exists():
            return p
    out = subprocess.run(
        ["nix", "build", f"{NIXPKGS}#{attr}", "--no-link", "--print-out-paths"],
        check=True, capture_output=True, text=True,
    ).stdout.strip().splitlines()[-1]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(out)
    return out


def openscad_binary() -> str:
    """The OpenSCAD to use: $OPENSCAD if set, else the pinned nix one."""
    return os.environ.get("OPENSCAD") or nix_path("openscad-unstable") + "/bin/openscad"


def openscad_version() -> str:
    """Version string of the active OpenSCAD (e.g. '2026.06.28')."""
    proc = subprocess.run([openscad_binary(), "--version"],
                          capture_output=True, text=True, check=True)
    # "OpenSCAD version 2026.06.28" on stderr (stdout on some builds)
    return (proc.stderr + proc.stdout).split()[-1]


def _png_rows(path: str):
    """Width, height and unfiltered rows of an 8-bit RGB or RGBA PNG."""
    data = Path(path).read_bytes()
    pos, idat = 8, b""
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
            assert depth == 8 and ctype in (2, 6), f"{path}: unsupported PNG"
            bpp = 3 if ctype == 2 else 4
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    raw, stride = zlib.decompress(idat), w * bpp
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        row = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 255
        elif f == 2:
            row = bytearray((a + b) & 255 for a, b in zip(row, prev))
        elif f == 3:
            for i in range(stride):
                left = row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b, c = prev[i], prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                row[i] = (row[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(row)
        prev = row
    return w, h, bpp, rows


def downscale_png(src: str, dst: str, n: int) -> None:
    """Average n x n pixel blocks of src into dst (RGB)."""
    w, h, bpp, rows = _png_rows(src)
    ow, oh = w // n, h // n
    out = bytearray()
    for oy in range(oh):
        acc = [0] * (w * 3)
        for row in rows[oy * n:(oy + 1) * n]:
            for ch in range(3):
                for x, v in enumerate(row[ch::bpp]):
                    acc[x * 3 + ch] += v
        line = bytearray(ow * 3)
        for ox in range(ow):
            for ch in range(3):
                line[ox * 3 + ch] = sum(acc[(ox * n + k) * 3 + ch] for k in range(n)) // (n * n)
        out += b"\0" + line

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    Path(dst).write_bytes(b"\x89PNG\r\n\x1a\n"
                          + chunk(b"IHDR", struct.pack(">IIBBBBB", ow, oh, 8, 2, 0, 0, 0))
                          + chunk(b"IDAT", zlib.compress(bytes(out), 9)) + chunk(b"IEND", b""))


def render(scad: str, out: str, extra_args=None) -> subprocess.CompletedProcess:
    """Render one .scad file. Returns the CompletedProcess (check output/stderr)."""
    extra_args = list(extra_args or [])
    ss = [a for a in extra_args if a.startswith("--supersample=")]
    if ss:
        n = int(ss[0].split("=")[1])
        extra_args = [a for a in extra_args if a not in ss]
        size = next((a for a in extra_args if a.startswith("--imgsize")), "--imgsize=1600,1200")
        w, h = (int(v) for v in size.split("=")[1].split(","))
        extra_args = [a for a in extra_args if a != size] + [f"--imgsize={w * n},{h * n}"]
        with tempfile.TemporaryDirectory() as td:
            big = str(Path(td) / "big.png")
            proc = render(scad, big, extra_args)
            if proc.returncode == 0:
                downscale_png(big, out, n)
        return proc
    external = "OPENSCAD" in os.environ
    openscad = openscad_binary()

    env = dict(os.environ)
    args = ["--backend", "Manifold"]
    if out.endswith(".png"):
        if not external:
            mesa, glvnd = nix_path("mesa"), nix_path("libglvnd")
            env.update(
                LD_LIBRARY_PATH=f"{glvnd}/lib:{mesa}/lib",
                __EGL_VENDOR_LIBRARY_FILENAMES=f"{mesa}/share/glvnd/egl_vendor.d/50_mesa.json",
                EGL_PLATFORM="surfaceless",
                LIBGL_ALWAYS_SOFTWARE="1",
            )
        if not any(a.startswith("--imgsize") for a in extra_args):
            args += ["--imgsize", "1600,1200"]
        if not any(a.startswith("--camera") for a in extra_args):
            args += ["--viewall", "--autocenter"]
    elif not external:
        # Non-GL outputs: keep nix libs only, the system /lib crashes nix binaries.
        env["LD_LIBRARY_PATH"] = ""

    cmd = [openscad, *args, *extra_args, "-o", out, scad]
    return subprocess.run(cmd, env=env, capture_output=True, text=True)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    scad = argv[1]
    out = argv[2] if len(argv) > 2 and not argv[2].startswith("-") else str(Path(scad).with_suffix(".png"))
    extra = argv[3:] if len(argv) > 2 and not argv[2].startswith("-") else argv[2:]
    proc = render(scad, out, extra)
    sys.stderr.write(proc.stderr)
    if proc.returncode == 0:
        print(f"rendered {scad} -> {out}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
