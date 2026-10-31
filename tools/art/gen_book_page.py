"""명부 '세로 책 한 쪽' 한지 바탕 생성기.
왜: #64에서 명부가 가로 펼침(두 쪽)에서 좁고 긴 세로 책 한 권이 됐는데, 두 쪽짜리 그림의 왼쪽만 잘라 써서 오른쪽 금테가 잘렸다.
    그래서 한 쪽짜리 그림을 새로 그린다: 먹색 표지 + 금 테두리 + 한지 한 쪽 + 왼쪽 책등(붉은 오침 실).
산출: assets/sprites/ui/ui_book_page.png 와 같은 파일을 unity/Assets/Resources/Sprites/ui/ 에도 복사(.meta 는 따로 커밋).
화면에서는 9조각(가장자리는 고정, 가운데만 늘림)으로 써서 폰 세로·PC 어느 비율에서도 금테가 일정하게 보인다. 조각 폭 = SLICE.
실행: python3 tools/art/gen_book_page.py"""
import os, random, shutil
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
W, H = 640, 704          # 화면 최대 크기(620×660)보다 약간 커서 늘림이 거의 없다
SLICE = 56               # 9조각 가장자리 폭(표지 + 한지 가장자리가 이 안에 들어온다)
K = 3                    # 계단 현상을 줄이려 3배로 그린 뒤 줄인다
INK, GOLD = (42, 42, 56), (212, 169, 78)
PAPER_A, PAPER_B, EDGE, SEAL = (246, 236, 217), (228, 213, 184), (185, 168, 136), (181, 71, 63)

def torn(x0, y0, x1, y1, rng, amp=2.6, step=8):
    """가장자리가 살짝 찢긴 한지 윤곽(가장자리 점들을 위아래로 조금씩 흔든다)."""
    pts = []
    for x in range(x0, x1, step): pts.append((x, y0 + rng.uniform(-amp, amp)))
    for y in range(y0, y1, step): pts.append((x1 + rng.uniform(-amp, amp), y))
    for x in range(x1, x0, -step): pts.append((x, y1 + rng.uniform(-amp, amp)))
    for y in range(y1, y0, -step): pts.append((x0 + rng.uniform(-amp, amp), y))
    return [(px * K, py * K) for px, py in pts]

def main():
    rng = random.Random(64)
    im = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 표지: 먹색 둥근 판 + 금 바깥선 + 안쪽 가는 금선
    d.rounded_rectangle((2 * K, 2 * K, (W - 2) * K, (H - 2) * K), 14 * K, fill=INK, outline=GOLD, width=3 * K)
    d.rounded_rectangle((12 * K, 12 * K, (W - 12) * K, (H - 12) * K), 8 * K, outline=GOLD + (128,), width=1 * K)
    # 한지 한 쪽: 위→아래 대각 그라데이션을 따로 만들어 찢긴 윤곽으로 오려 붙인다
    px0, py0, px1, py1 = 30, 30, W - 30, H - 30
    grad = Image.new("RGBA", (W * K, H * K))
    gd = ImageDraw.Draw(grad)
    for i in range(0, (W + H) * K, 2):   # 대각선 띠로 칠해 그라데이션
        t = i / ((W + H) * K)
        c = tuple(int(PAPER_A[j] + (PAPER_B[j] - PAPER_A[j]) * t) for j in range(3)) + (255,)
        gd.line((i, 0, i - H * K, H * K), fill=c, width=3)
    mask = Image.new("L", im.size, 0)
    poly = torn(px0, py0, px1, py1, rng)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    im.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.line(poly + [poly[0]], fill=EDGE + (255,), width=2 * K, joint="curve")
    fib = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(fib)   # 섬유는 별도 층에 그려 반투명이 '덮어쓰기'가 아니라 '섞이게' 한다
    # 한지 결(짧은 섬유 선) — 가운데 조각에만 두어 늘어나도 티가 안 난다
    for _ in range(300):
        x, y = rng.uniform(SLICE, W - SLICE), rng.uniform(SLICE, H - SLICE)
        d.line((x * K, y * K, (x + rng.uniform(-24, 24)) * K, (y + rng.uniform(-7, 7)) * K), fill=(217, 199, 166, 120), width=K)
    im = Image.alpha_composite(im, fib)
    # 왼쪽 책등: 한지 왼쪽 가장자리에 부드러운 그림자(글자 여백 안쪽이라 글을 가리지 않는다)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rectangle((px0 * K, py0 * K, (px0 + 22) * K, py1 * K), fill=(42, 42, 56, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(10 * K))
    sh.putalpha(Image.composite(sh.getchannel("A"), Image.new("L", im.size, 0), mask))
    im = Image.alpha_composite(im, sh)
    d = ImageDraw.Draw(im)
    # 책등 오침 실: 표지 왼쪽 띠 가운데를 지나는 붉은 실 한 줄(세로로 늘어나도 끊기지 않게 이어진 선)
    d.line((15 * K, 40 * K, 15 * K, (H - 40) * K), fill=SEAL + (235,), width=3 * K)
    im = im.resize((W, H), Image.LANCZOS)
    out = os.path.join(ROOT, "assets", "sprites", "ui", "ui_book_page.png")
    im.save(out)
    dst = os.path.join(ROOT, "unity", "Assets", "Resources", "Sprites", "ui", "ui_book_page.png")
    shutil.copyfile(out, dst)
    print("saved", out, im.size)

if __name__ == "__main__":
    main()
