"""Derive 16-bit height.png + ao.png from existing Poly Haven CC0 normal/diffuse maps.

Trick #8. Free only (numpy). Method: Poisson integrate of the tangent-space
normal (nor.jpg) to a height field, then a cavity AO from that height.
Alignment is 1:1 with diff.jpg / nor.jpg in the same folder.

Usage:
  python3 derive_height.py                # stone, terracotta, brick
  python3 derive_height.py textures/stone

Does not overwrite official scene files. Output is textures/<set>/{height,ao}.png
(16-bit grayscale). Licence: derived from the existing CC0 maps
(build_scene.py: textures/* are Poly Haven CC0).
"""
from __future__ import annotations
import os, sys, struct, zlib
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = ("stone", "terracotta", "brick")


def load_norm(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, dtype=np.float32) / 255.0
    n = a * 2.0 - 1.0
    # OpenGL-style: +Y up. Avoid div0 on flat-ish pixels.
    nz = np.clip(n[:, :, 2], 0.15, 1.0)
    gx = -n[:, :, 0] / nz
    gy = -n[:, :, 1] / nz
    return gx, gy


def poisson_integrate(gx, gy, iters=250):
    """Jacobi Poisson solve: laplace H = div(grad). Neumann-ish (copy edges)."""
    div = np.zeros_like(gx)
    div[:, 1:] += gx[:, 1:] - gx[:, :-1]
    div[1:, :] += gy[1:, :] - gy[:-1, :]
    h = np.zeros_like(div)
    for i in range(iters):
        n = np.zeros_like(h)
        n[1:-1, 1:-1] = 0.25 * (
            h[1:-1, 2:] + h[1:-1, :-2] + h[2:, 1:-1] + h[:-2, 1:-1] - div[1:-1, 1:-1]
        )
        n[0, :] = n[1, :]
        n[-1, :] = n[-2, :]
        n[:, 0] = n[:, 1]
        n[:, -1] = n[:, -2]
        h = n
        if i % 80 == 79:
            h -= h.mean()
    h -= h.mean()
    # robust normalize to 0..1 around mid 0.5
    s = np.percentile(np.abs(h), 99.5) or 1.0
    h = np.clip(h / (2.0 * s) + 0.5, 0.0, 1.0)
    return h.astype(np.float32)


def ao_from_height(h, radius=3):
    """Cavity AO: darker where height is below a local blur (stand-in, no bake)."""
    im = Image.fromarray((np.clip(h, 0, 1) * 255.0).astype(np.uint8), mode="L")
    blur = np.asarray(im.filter(ImageFilter.GaussianBlur(radius=float(radius))), dtype=np.float32) / 255.0
    cav = np.clip(blur - h, 0.0, 1.0)
    ao = np.clip(1.0 - 2.5 * cav, 0.0, 1.0)
    return ao.astype(np.float32)


def save_u16(path, a):
    """Write a 16-bit grayscale PNG (Pillow on this box cannot emit mode I as PNG)."""
    h, w = a.shape
    raw = (np.clip(a, 0, 1) * 65535.0 + 0.5).astype(">u2")
    rows = b"".join(b"\x00" + raw[i].tobytes() for i in range(h))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", w, h, 16, 0, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(rows, 9)))
        f.write(chunk(b"IEND", b""))


def derive(folder, iters=250):
    nor = os.path.join(folder, "nor.jpg")
    if not os.path.isfile(nor):
        raise SystemExit(f"missing {nor}")
    gx, gy = load_norm(nor)
    h = poisson_integrate(gx, gy, iters=iters)
    ao = ao_from_height(h)
    hp = os.path.join(folder, "height.png")
    ap = os.path.join(folder, "ao.png")
    save_u16(hp, h)
    save_u16(ap, ao)
    return hp, ap, h.shape


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    folders = argv or [os.path.join(HERE, "textures", s) for s in SETS]
    for f in folders:
        hp, ap, shape = derive(f)
        print(f"OK {f} {shape[1]}x{shape[0]} -> {os.path.basename(hp)} {os.path.getsize(hp)}B, {os.path.basename(ap)} {os.path.getsize(ap)}B")


if __name__ == "__main__":
    main()
