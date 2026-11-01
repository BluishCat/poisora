"""アプリアイコン（案D: P モノグラム）を描いて assets/ に書き出す。

    .venv\\Scripts\\python.exe scripts\\gen_icon.py

出力:
    assets/poisora.ico  … exe 用（16〜256px のマルチサイズ）
    assets/poisora.png  … ウィンドウ（タイトルバー・タスクバー）用 256px
    assets/poisora.svg  … 同じ図形の SVG（README や SNS 用の原本）

図形は 128x128 の座標系で定義し、サイズごとに 16 倍で描いてから縮小する
（Pillow の図形描画はアンチエイリアスが無いため）。
"""
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]
SUPERSAMPLE = 16

BG = (255, 255, 255, 255)
BORDER = (214, 228, 245, 255)       # #D6E4F5
SKY_TOP = (77, 168, 255)            # #4DA8FF
SKY_BOTTOM = (26, 111, 224)         # #1A6FE0
CLOUD = (255, 255, 255, 255)

# --- 図形（128 座標系）---
CORNER = 28
P_TOP, P_BOTTOM = 24, 104           # P のグラデーション範囲
P_STEM = (38, 24, 56, 104)          # 縦棒
P_BOWL_RECT = (38, 24, 70, 76)      # 丸の左側の四角
P_BOWL_ARC = (44, 24, 96, 76)       # 丸（中心 70,50 半径 26）の右半分
CLOUD_CIRCLES = [(60, 53, 5), (67, 48, 7), (74, 53, 5)]   # (cx, cy, r)
CLOUD_BASE = (60, 52, 74, 58)       # 雲の底を平らにする四角


def _sc(box, s):
    return tuple(v * s for v in box)


def render(size):
    s = size * SUPERSAMPLE / 128
    big = size * SUPERSAMPLE
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 背景（角丸の白地 + 薄い枠）
    d.rounded_rectangle((0, 0, big - 1, big - 1), radius=CORNER * s, fill=BG)
    d.rounded_rectangle(_sc((2, 2, 126, 126), s), radius=26 * s,
                        outline=BORDER, width=max(1, round(4 * s)))

    # P の形のマスク
    mask = Image.new("L", (big, big), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle(_sc(P_STEM, s), fill=255)
    md.rectangle(_sc(P_BOWL_RECT, s), fill=255)
    md.pieslice(_sc(P_BOWL_ARC, s), start=-90, end=90, fill=255)

    # 縦グラデーションを P で切り抜いて重ねる
    grad = Image.new("RGBA", (big, big))
    gd = ImageDraw.Draw(grad)
    y0, y1 = P_TOP * s, P_BOTTOM * s
    for y in range(big):
        t = min(1.0, max(0.0, (y - y0) / (y1 - y0)))
        c = tuple(round(a + (b - a) * t) for a, b in zip(SKY_TOP, SKY_BOTTOM))
        gd.line((0, y, big, y), fill=c + (255,))
    img.paste(grad, (0, 0), mask)

    # P の丸の中の雲
    for cx, cy, r in CLOUD_CIRCLES:
        d.ellipse(_sc((cx - r, cy - r, cx + r, cy + r), s), fill=CLOUD)
    d.rectangle(_sc(CLOUD_BASE, s), fill=CLOUD)

    return img.resize((size, size), Image.Resampling.LANCZOS)


def _hex(rgb):
    return "#%02X%02X%02X" % rgb[:3]


def svg():
    clouds = "\n".join(
        f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF"/>' for cx, cy, r in CLOUD_CIRCLES)
    bx0, by0, bx1, by1 = CLOUD_BASE
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <linearGradient id="sky" gradientUnits="userSpaceOnUse" x1="0" y1="{P_TOP}" x2="0" y2="{P_BOTTOM}">
      <stop offset="0" stop-color="{_hex(SKY_TOP)}"/>
      <stop offset="1" stop-color="{_hex(SKY_BOTTOM)}"/>
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="{CORNER}" fill="#FFFFFF"/>
  <rect x="2" y="2" width="124" height="124" rx="26" fill="none" stroke="{_hex(BORDER)}" stroke-width="4"/>
  <path d="M38 104 V24 H70 A26 26 0 0 1 70 76 H56 V104 Z" fill="url(#sky)"/>
{clouds}
  <rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" fill="#FFFFFF"/>
</svg>
"""


def main():
    os.makedirs(ASSETS, exist_ok=True)
    images = {n: render(n) for n in ICO_SIZES}
    largest = images[ICO_SIZES[-1]]
    largest.save(os.path.join(ASSETS, "poisora.png"))
    # 各サイズを個別に縮小した画像をそのまま格納する（Pillow に再縮小させない）
    largest.save(os.path.join(ASSETS, "poisora.ico"), format="ICO",
                 sizes=[(n, n) for n in ICO_SIZES],
                 append_images=[images[n] for n in ICO_SIZES[:-1]])
    with open(os.path.join(ASSETS, "poisora.svg"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(svg())
    print("wrote", ", ".join(f"assets/poisora.{e}" for e in ("ico", "png", "svg")))


if __name__ == "__main__":
    main()
