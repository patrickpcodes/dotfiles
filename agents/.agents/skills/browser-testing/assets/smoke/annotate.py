"""Draw click arrows (amber) and change boxes (red) on a raw screenshot, then crop it.

Usage: python annotate.py spec.json
spec: {"src": "raw/x.png", "out": "x.png", "crop": [l, t, r, b], "scale": 1,
       "clicks": [{"rect": [l, t, r, b], "label": "1 Clicked Save", "from": "left|right|above|below"}],
       "boxes": [{"rect": [l, t, r, b], "label": "Owner saved.", "label_at": "above|below"}]}
Rects are page CSS pixels; "scale" converts them to screenshot pixels (1.5 for phone presets). Crop is in screenshot pixels.
"""
import json
import math
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

SCALE = 3
RED = (230, 36, 41, 255)
AMBER = (255, 176, 0, 255)
INK = (20, 20, 20, 255)
WHITE = (255, 255, 255, 255)

folder = pathlib.Path(__file__).parent
spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
base = Image.open(folder / spec["src"]).convert("RGBA")
layer = Image.new("RGBA", (base.width * SCALE, base.height * SCALE), (0, 0, 0, 0))
draw = ImageDraw.Draw(layer)
try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 13 * SCALE)
except OSError:
    font = ImageFont.load_default(13 * SCALE)
left_edge, top_edge, right_edge, bottom_edge = [v * SCALE for v in spec.get("crop") or [0, 0, base.width, base.height]]


def s(values):
    return [v * SCALE * spec.get("scale", 1) for v in values]


def tag(x, y, text, fill, color, anchor_below=False):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    w, h = right - left + 14 * SCALE, bottom - top + 8 * SCALE
    x = min(max(x, left_edge + 2 * SCALE), right_edge - w - 2 * SCALE)
    y = y if anchor_below else y - h
    y = min(max(y, top_edge + 2 * SCALE), bottom_edge - h - 2 * SCALE)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=5 * SCALE, fill=fill)
    draw.text((x + 7 * SCALE - left, y + 4 * SCALE - top), text, font=font, fill=color)
    return x, y, w, h


for box in spec.get("boxes", []):
    l, t, r, b = s(box["rect"])
    pad = 4 * SCALE
    draw.rounded_rectangle([l - pad, t - pad, r + pad, b + pad], radius=4 * SCALE, outline=RED, width=3 * SCALE)
    if box.get("label"):
        below = box.get("label_at") == "below" or t - pad < 26 * SCALE
        tag(l - pad, (b + pad + 3 * SCALE) if below else (t - pad - 3 * SCALE), box["label"], RED, WHITE, anchor_below=below)

for click in spec.get("clicks", []):
    l, t, r, b = s(click["rect"])
    cx, cy = (l + r) / 2, (t + b) / 2
    side = click.get("from", "left")
    gap, length = 6 * SCALE, 56 * SCALE
    tip = {"left": (l - gap, cy), "right": (r + gap, cy), "above": (cx, t - gap), "below": (cx, b + gap)}[side]
    dx, dy = {"left": (-1, 0.55), "right": (1, 0.55), "above": (0.55, -1), "below": (0.55, 1)}[side]
    norm = math.hypot(dx, dy)
    tail = (tip[0] + dx / norm * length, tip[1] + dy / norm * length)
    angle = math.atan2(tip[1] - tail[1], tip[0] - tail[0])
    head = 15 * SCALE
    wing = lambda a: (tip[0] - head * math.cos(angle + a), tip[1] - head * math.sin(angle + a))
    for color, width in ((INK, 8 * SCALE), (AMBER, 5 * SCALE)):
        draw.line([tail, ((wing(0.45)[0] + wing(-0.45)[0]) / 2, (wing(0.45)[1] + wing(-0.45)[1]) / 2)], fill=color, width=width)
    draw.polygon([tip, wing(0.45), wing(-0.45)], fill=AMBER, outline=INK, width=2 * SCALE)
    text = click["label"]
    tw = draw.textbbox((0, 0), text, font=font)[2] + 14 * SCALE
    tx = tail[0] - tw if dx < 0 else tail[0] if dx > 0 else tail[0] - tw / 2
    ty = tail[1] if dy > 0 else tail[1]
    tag(tx, ty, text, AMBER, INK, anchor_below=dy > 0)

overlay = layer.resize(base.size, Image.LANCZOS)
out = Image.alpha_composite(base, overlay).convert("RGB")
if spec.get("crop"):
    out = out.crop(spec["crop"])
out.save(folder / spec["out"])
print(spec["out"], out.size)
