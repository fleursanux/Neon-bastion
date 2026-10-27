#!/usr/bin/env python3
"""Dessine les icônes de l'application (noyau néon) avec Pillow.
Usage : python3 icons.py <dossier de sortie>"""
import sys, math, pathlib
from PIL import Image, ImageDraw, ImageFilter

def hexagon(cx, cy, r, rot):
    return [(cx + r * math.cos(rot + i * math.pi / 3), cy + r * math.sin(rot + i * math.pi / 3)) for i in range(6)]

def icon(size, mask=False):
    S = 4  # sur-échantillonnage pour des bords lisses
    W = size * S
    k = (0.72 if mask else 0.9) * W / 512
    c = W / 2
    base = Image.new('RGB', (W, W), (10, 14, 24))
    glow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse([c - 230 * k, c - 230 * k, c + 230 * k, c + 230 * k], fill=(62, 242, 200, 60))
    lines = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(lines)
    d.polygon(hexagon(c, c, 200 * k, math.pi / 6), outline=(62, 242, 200, 255), width=int(22 * k))
    d.polygon(hexagon(c, c, 120 * k, 0), outline=(255, 79, 163, 255), width=int(14 * k))
    d.ellipse([c - 42 * k, c - 42 * k, c + 42 * k, c + 42 * k], fill=(94, 240, 255, 255))
    blur = lines.filter(ImageFilter.GaussianBlur(18 * k))
    out = base.convert('RGBA')
    out = Image.alpha_composite(out, glow.filter(ImageFilter.GaussianBlur(60 * k)))
    out = Image.alpha_composite(out, blur)
    out = Image.alpha_composite(out, blur)
    out = Image.alpha_composite(out, lines)
    return out.convert('RGB').resize((size, size), Image.LANCZOS)

dest = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'icons')
dest.mkdir(parents=True, exist_ok=True)
for name, size, mask in [('icon-192.png', 192, False), ('icon-512.png', 512, False), ('maskable-512.png', 512, True), ('apple-touch-icon.png', 180, False)]:
    icon(size, mask).save(dest / name, optimize=True)
print('Icônes créées dans', dest)
