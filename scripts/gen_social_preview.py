"""GitHub の Social preview 画像（1280x640）を描いて assets/ に書き出す。

    .venv\\Scripts\\python.exe scripts\\gen_social_preview.py

出力:
    assets/social-preview.png … リポジトリの Settings > General > Social preview にアップロードする
                                 （API では設定できないため手動。X・Bluesky などのリンクカードに出る）

アイコンは gen_icon.py の render() で描き直すので、アイコンの図形を変えたらこちらも作り直す。
フォントは Windows 標準（Segoe UI・游ゴシック）を使う。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from gen_icon import render, SKY_BOTTOM  # noqa: E402

W, H = 1280, 640
S = 2  # 2 倍で描いて縮小する（文字と図形のアンチエイリアス用）
OUT = os.path.join(ROOT, "assets", "social-preview.png")
F = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts") + os.sep

TOP, BOTTOM = (246, 250, 255), (214, 232, 255)
NAVY = (22, 48, 92)
BLUE = SKY_BOTTOM
GRAY = (84, 100, 124)


def font(name, size, index=0):
    return ImageFont.truetype(F + name, size * S, index=index)


img = Image.new("RGB", (W * S, H * S))
d = ImageDraw.Draw(img)
for y in range(H * S):
    t = y / (H * S - 1)
    d.line((0, y, W * S, y), fill=tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)))

# 四隅にうっすら雲
clouds = Image.new("RGBA", img.size, (0, 0, 0, 0))
cd = ImageDraw.Draw(clouds)
for cx, cy, r in [(1150, 90, 70), (1230, 60, 55), (1080, 110, 45), (90, 600, 80), (190, 625, 60), (10, 590, 50)]:
    cd.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=(255, 255, 255, 150))
img.paste(clouds, (0, 0), clouds)

# アイコン（影付き）
ICON = 360
ix, iy = 110, (H - ICON) // 2
shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle(
    ((ix + 6) * S, (iy + 14) * S, (ix + ICON + 6) * S, (iy + ICON + 14) * S),
    radius=int(ICON * 28 / 128) * S, fill=(26, 70, 140, 70))
shadow = shadow.filter(ImageFilter.GaussianBlur(18 * S))
img.paste(shadow, (0, 0), shadow)
icon = render(ICON * S)
img.paste(icon, (ix * S, iy * S), icon)

# 文字
tx = ix + ICON + 70
maxw = (W - 70 - tx) * S


def fit(text, name, size, index=0):
    while size > 10:
        f = font(name, size, index)
        if d.textlength(text, font=f) <= maxw:
            return f
        size -= 1
    return font(name, size, index)


lines = [
    ("Poisora", fit("Poisora", "segoeuib.ttf", 128), NAVY, 0),
    ("Windows 用 Bluesky クライアント", fit("Windows 用 Bluesky クライアント", "YuGothB.ttc", 44), BLUE, 18),
    ("一覧で流し読み・スペースキーで未読ジャンプ", fit("一覧で流し読み・スペースキーで未読ジャンプ", "YuGothM.ttc", 30), GRAY, 34),
    ("無料・オープンソース（MIT）", fit("無料・オープンソース（MIT）", "YuGothM.ttc", 30), GRAY, 12),
]
heights = []
for text, f, _, gap in lines:
    b = d.textbbox((0, 0), text, font=f)
    heights.append((b[1], b[3] - b[1], gap * S))
total = sum(h + g for _, h, g in heights)
y = (H * S - total) // 2
for (text, f, color, _), (top, h, gap) in zip(lines, heights):
    y += gap
    d.text((tx * S, y - top), text, font=f, fill=color)
    y += h

url = "github.com/BluishCat/poisora"
uf = font("segoeui.ttf", 24)
d.text(((W - 48) * S - d.textlength(url, font=uf), (H - 44) * S), url, font=uf, fill=GRAY)

img = img.resize((W, H), Image.Resampling.LANCZOS)
img.save(OUT, optimize=True)
print("wrote", os.path.relpath(OUT, ROOT), os.path.getsize(OUT), "bytes")
