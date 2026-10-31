"""Inline the screenshots of every *.source.html in this folder into one self-contained HTML file each."""
import base64
import io
import pathlib
import re

from PIL import Image

folder = pathlib.Path(__file__).parent


def inline(match):
    buffer = io.BytesIO()
    Image.open(folder / match.group(1)).save(buffer, "WEBP", lossless=True, method=6)
    return 'src="data:image/webp;base64,' + base64.b64encode(buffer.getvalue()).decode() + '"'


for source in folder.glob("*.source.html"):
    html = re.sub(r'src="([^"]+\.png)"', inline, source.read_text(encoding="utf-8"))
    target = folder / source.name.replace(".source.html", ".html")
    target.write_text(html, encoding="utf-8")
    print(f"{target.name} {len(html) // 1024} KB")
