"""보스가 꿇은 동안(천도 시전 2초) 날아오는 압박의 '바닥 경고 그림' 세트.
왜: 천도 시전 중에는 시야가 먹으로 60%만 보이고(가장자리 먹 번짐), 바닥엔 처결 대기 고리도 깔려 있다.
 폰(6.1", 2340×1080)에서 줌 24 m이면 1 m가 약 71 픽셀 = 눈에 0.45 mm. 기존 경고 테두리(5.9 cm)는 0.26 mm라 고리·먹에 묻힌다.
 그래서 모든 경고 테두리를 '월드 12 cm 한지색 + 먹 바깥선'으로 굵게 새로 그리고(폰 24 m에서 0.55 mm 이상), 모양으로도 종류를 구분한다.
규칙(접근성 v1.4): 위험 = 밝은 한지색 #FFF4E0 테두리 + 위험 빨강 #E85C41 35% 채움(코드가 바깥→안으로 차오르게 마스크). 주황 #E8683A(파혼)은 쓰지 않는다.
 안전 자리 = 한지색 '점선' 테두리 + 옥색 흰빛 25% 채움 + 안쪽을 가리키는 ▸ 눈금. 위험은 실선·안전은 점선이라 색을 못 봐도 구분된다.
크기 약속: 모든 그림은 1 m = 128 픽셀로 그렸다. 코드는 '월드 크기(m) ÷ 그림 크기(m)'만큼 스케일하면 테두리 굵기가 12 cm 근처로 유지된다(너무 크게 늘리면 얇아진다).
산출: assets3d/ui/boss_warn/*.png (1배·@2x) + _boss_warn.json(그림 크기·용도) → unity/Assets/Resources/Sprites/boss_warn/
실행: python3 boss_kneel_warn.py"""
import os, sys, math, json, shutil
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import ui_lib as U

SUB = "boss_warn"
S = 2                       # 2배 작업(저장은 1배·@2x)
PPM = 128                   # 1 m = 128 px (1배 기준)
CREAM = (255, 244, 224); INKC = (26, 20, 16); RED = (232, 92, 65); JADE = (215, 255, 245); INK_NAVY = (15, 23, 41)
BW = 0.12                   # 한지색 테두리 월드 굵기(m)
OW = 0.04                   # 먹 바깥선(m) — 한지색 양옆에 하나씩. 밝은 바닥·어두운 먹 가장자리 양쪽에서 선이 살아남게 한다.

def px(m): return int(round(m * PPM * S))
def canvas(w_m, h_m): return Image.new("RGBA", (px(w_m), px(h_m)), (0, 0, 0, 0))
def border_rect(d, W, H, inset=0.02, dashed=False):
    """사각 테두리: 먹(바깥·안쪽)+한지색. dashed면 점선(안전 자리)."""
    i = px(inset); b = px(BW); o = px(OW)
    def seg(x0, y0, x1, y1, col, wd):
        if not dashed: d.line([(x0, y0), (x1, y1)], fill=col, width=wd); return
        L = math.hypot(x1 - x0, y1 - y0); n = max(2, int(L / px(0.5)))
        for k in range(n):
            if k % 2: continue
            a, c = k / n, (k + 1) / n; d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * c, y0 + (y1 - y0) * c)], fill=col, width=wd)
    cs = [(i + b // 2, i + b // 2), (W - i - b // 2, i + b // 2), (W - i - b // 2, H - i - b // 2), (i + b // 2, H - i - b // 2)]
    for col, wd in ((INKC + (210,), b + 2 * o), (CREAM + (255,), b)):
        for k in range(4): seg(*cs[k], *cs[(k + 1) % 4], col, wd)
        if not dashed:      # 모서리 이음 둥글게(선 끝 틈 메우기)
            for (x, y) in cs: d.ellipse([x - wd / 2, y - wd / 2, x + wd / 2, y + wd / 2], fill=col)
def border_circle(d, c, R, dashed=False, ticks=0, tick_in=True):
    b = px(BW); o = px(OW)
    for col, wd in ((INKC + (210,), b + 2 * o), (CREAM + (255,), b)):
        if not dashed: d.ellipse([c - R, c - R, c + R, c + R], outline=col, width=wd)
        else:
            n = 28
            for k in range(n):
                if k % 2: continue
                a0 = k / n * 360; a1 = (k + 1) / n * 360; d.arc([c - R, c - R, c + R, c + R], a0, a1, fill=col, width=wd)
    for k in range(ticks):      # 안쪽을 가리키는 삼각 눈금(낙석·안전 표시): 한지색 + 먹 윤곽
        a = k / ticks * math.tau; r0 = R + px(0.10); r1 = R + px(0.55) if tick_in else R - px(0.4)
        tip = (c + math.cos(a) * (R + px(0.12)), c + math.sin(a) * (R + px(0.12))); w = px(0.22)
        base = (c + math.cos(a) * r0 + (r1 - r0) * 0, c + math.sin(a) * r0)
        bx, by = c + math.cos(a) * r1, c + math.sin(a) * r1; nx, ny = -math.sin(a), math.cos(a)
        tri = [tip, (bx + nx * w, by + ny * w), (bx - nx * w, by - ny * w)]
        d.polygon(tri, fill=CREAM + (255,), outline=INKC + (230,))
        d.line(tri + [tri[0]], fill=INKC + (230,), width=px(0.03))

FILES = {}
def put(img, name, note, size_m):
    U.save(img, name, SUB, note=note); w, h = img.size[0] // 2, img.size[1] // 2
    FILES[name] = {"size_px": [w, h], "size_m": list(size_m), "px_per_m": PPM, "note": note}

# ── 1) 원(거적·물귀신 큰 원): 지름 5 m ──────────────────────────────────────
def circle(d_m=5.0, fill=False, hatch=False):
    im = canvas(d_m + 0.3, d_m + 0.3); W = im.size[0]; c = W / 2; R = c - px(0.15 + BW / 2 + OW)
    if fill:
        yy, xx = np.mgrid[0:W, 0:W]; m = (np.hypot(xx - c, yy - c) < R)
        a = np.where(m, 0.35, 0.0)
        if hatch:     # 거적(짚자리) 결: 가는 비스듬 줄무늬. 다른 원 경고와 '무늬'로 구분
            st = ((xx + yy) / px(0.28)) % 1.0 < 0.22; a = np.where(m & st, 0.62, a)
        arr = np.zeros((W, W, 4), np.uint8); arr[..., :3] = RED; arr[..., 3] = (a * 255).astype(np.uint8); return Image.fromarray(arr, "RGBA")
    d = ImageDraw.Draw(im); border_circle(d, c, R); return im

# ── 2) 칸(낙인 파동·호령 대형 한 칸): 한 변 2 m ──────────────────────────────
def cell(side=2.0, fill=False):
    im = canvas(side, side); W = im.size[0]
    if fill:
        arr = np.zeros((W, W, 4), np.uint8); arr[..., :3] = RED; i = px(0.02 + BW + OW); arr[i:W - i, i:W - i, 3] = int(255 * 0.35); return Image.fromarray(arr, "RGBA")
    d = ImageDraw.Draw(im); border_rect(d, W, W)
    return im

# ── 3) 띠(파도 한 줄·갑판 기울기 길): 1.6 m × 6 m (가로로 눕혀 쓴다) ─────────
def band(w_m=1.6, l_m=6.0, fill=False):
    im = canvas(w_m, l_m); W, H = im.size
    if fill:
        arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = RED; i = px(0.02 + BW + OW); arr[i:H - i, i:W - i, 3] = int(255 * 0.35)
        yy = np.mgrid[0:H, 0:W][0]; ch = ((yy // px(0.9)) % 2 == 0); arr[i:H - i, i:W - i, 3] = np.where(ch[i:H - i, i:W - i], int(255 * 0.35), int(255 * 0.27)); return Image.fromarray(arr, "RGBA")
    d = ImageDraw.Draw(im); border_rect(d, W, H); return im

# ── 4) 안전 자리(점선): 칸·띠 ───────────────────────────────────────────────
def safe_rect(w_m, h_m):
    """안전 자리 = 점선 한지 테두리 + 옥색 흰빛 25% + 안쪽을 가리키는 ▸ 눈금 4개(위험 장판과 모양이 완전히 다르다)."""
    im = canvas(w_m, h_m); W, H = im.size; i = px(0.02 + BW + OW)
    arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = JADE; arr[i:H - i, i:W - i, 3] = int(255 * 0.38); im = Image.fromarray(arr, "RGBA"); d = ImageDraw.Draw(im)
    border_rect(d, W, H, dashed=True)
    ch = px(0.2)       # 안쪽을 향한 ▶ 눈금: 각 변 가운데에 하나
    for (cx, cy, ang) in ((W / 2, i + px(0.5), 90), (W / 2, H - i - px(0.5), -90), (i + px(0.5), H / 2, 0), (W - i - px(0.5), H / 2, 180)):
        a = math.radians(ang); tip = (cx + math.cos(a) * ch, cy + math.sin(a) * ch); nx, ny = -math.sin(a), math.cos(a)
        tri = [tip, (cx - math.cos(a) * ch * 0.5 + nx * ch * 0.8, cy - math.sin(a) * ch * 0.5 + ny * ch * 0.8), (cx - math.cos(a) * ch * 0.5 - nx * ch * 0.8, cy - math.sin(a) * ch * 0.5 - ny * ch * 0.8)]
        d.polygon(tri, fill=CREAM + (255,)); d.line(tri + [tri[0]], fill=INKC + (230,), width=px(0.03))
    return im

# ── 5) 낙석 그림자: 지름 3 m ────────────────────────────────────────────────
def rock(fill=False, on_you=False):
    """낙석 = 땅에 짙은 먹 그림자가 깔리고 가장자리에서 안쪽을 가리키는 삼각 눈금 8개(떨어지는 방향). 빨강 채움은 가장자리 띠로만(가운데는 어둡게 → '그림자'로 읽힘).
    on_you(내 발밑)은 바깥에 점선 큰 고리 + ▼ 눈금 4개를 더해, 시선이 내 발에서 멈추게 한다."""
    D = 3.0 + (1.8 if on_you else 0) + 0.9; im = canvas(D, D); W = im.size[0]; c = W / 2; R = px(1.5)
    if fill:
        yy, xx = np.mgrid[0:W, 0:W]; r = np.hypot(xx - c, yy - c) / R; m = r < 1
        a_ink = np.where(m, 0.30 + 0.30 * np.clip(1 - r, 0, 1) ** 0.8, 0); a_red = np.where(m, np.clip((r - 0.45) / 0.55, 0, 1) * 0.35, 0)
        arr = np.zeros((W, W, 4), np.float32)
        tot = np.clip(a_ink + a_red, 1e-4, 1); arr[..., :3] = (np.array(INK_NAVY)[None, None] * (a_ink / tot)[..., None] + np.array(RED)[None, None] * (a_red / tot)[..., None]); arr[..., 3] = np.clip(a_ink + a_red - a_ink * a_red, 0, 1) * 255
        return Image.fromarray(arr.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im); border_circle(d, c, R, ticks=8)
    if on_you:
        R2 = px(2.35); border_circle(d, c, R2, dashed=True)
    return im

# ── 6) 갑판 기울기 방향(화살 3겹): 4 m × 2 m, 오른쪽(+x)을 가리킴 ─────────────
def deck_arrow(fill=False):
    im = canvas(4.0, 2.0); W, H = im.size; d = ImageDraw.Draw(im); b = px(BW); o = px(OW)
    def chev(x0):
        h = H * 0.42; w = px(0.8); pts = [(x0, H / 2 - h), (x0 + w, H / 2), (x0, H / 2 + h), (x0 + px(0.5), H / 2 + h), (x0 + px(0.5) + w, H / 2), (x0 + px(0.5), H / 2 - h)]
        return pts
    for k in range(3):
        pts = chev(px(0.45 + k * 1.0));
        if fill: d.polygon(pts, fill=RED + (int(255 * 0.55),))
        else:
            d.line(pts + [pts[0]], fill=INKC + (210,), width=b + 2 * o, joint="curve"); d.line(pts + [pts[0]], fill=CREAM + (255,), width=b, joint="curve")
    return im

# ── 7) 물 혼 나오는 자리: 지름 2 m ──────────────────────────────────────────
def spawn():
    """물 혼(물귀신) 나오는 자리 = 한지색 물결 고리 둘(안쪽 실선·바깥 점선) + 가운데 붉은 물방울(▼ 모양). 채움 없음(처결 대기 고리처럼 바닥을 덮지 않게)."""
    im = canvas(2.0, 2.0); W = im.size[0]; c = W / 2; d = ImageDraw.Draw(im)
    border_circle(d, c, px(0.55)); border_circle(d, c, px(0.92), dashed=True)
    r = px(0.2); cy = c + px(0.08)
    d.ellipse([c - r, cy - r, c + r, cy + r], fill=RED + (255,), outline=CREAM + (255,), width=px(0.04))
    pts = [(c, cy - px(0.5)), (c - r * 0.9, cy - r * 0.45), (c + r * 0.9, cy - r * 0.45)]
    d.polygon(pts, fill=RED + (255,)); d.line(pts + [pts[0]], fill=CREAM + (255,), width=px(0.04)); return im

def run():
    put(circle(), "warn_circle_border_L", "원 경고 테두리 지름 5 m(그림 5.3 m 안에 반경 2.5 m). 한지 12 cm + 먹선. 거적(r3)은 6/5.3 배로 키움", (5.3, 5.3))
    put(circle(fill=True), "warn_circle_fill_red", "원 경고 채움(빨강 35%, 안쪽으로 차오르는 마스크는 코드)", (5.3, 5.3))
    put(circle(fill=True, hatch=True), "warn_mat_fill", "거적 던지기 원 채움: 비스듬 짚결 줄무늬(다른 원 경고와 무늬로 구분). 반경 3 m·예고 0.8초·느려짐 2초", (5.3, 5.3))
    put(cell(), "warn_cell_border_L", "칸 경고 테두리 한 변 2 m + 모서리 꺾쇠(낙인 파동 12칸·호령 대형)", (2.0, 2.0))
    put(cell(fill=True), "warn_cell_fill_red", "칸 경고 채움 빨강 35%", (2.0, 2.0))
    put(band(), "warn_band_border_L", "띠 경고 테두리 1.6×6 m(파도 한 줄·물살). 가로로 눕혀 쓴다", (1.6, 6.0))
    put(band(fill=True), "warn_band_fill_red", "띠 경고 채움 빨강 35%, 0.9 m 마디 옅은 줄", (1.6, 6.0))
    put(safe_rect(2.0, 2.0), "warn_safe_cell", "안전 칸(낙인 13번째 칸·호령 틈 칸): 점선 한지 테두리 + 옥색 흰빛 25% + 안쪽 ▸ 눈금", (2.0, 2.0))
    put(safe_rect(1.6, 6.0), "warn_safe_band", "안전 띠(파도 줄의 안전 구간): 점선 한지 테두리 + 옥색 흰빛 25%", (1.6, 6.0))
    put(rock(), "warn_rock_border_L", "낙석 그림자 테두리 지름 3 m: 한지 고리 + 안쪽을 가리키는 삼각 눈금 8개", (3.9, 3.9))
    put(rock(fill=True), "warn_rock_fill", "낙석 그림자 채움: 가운데 짙은 먹(#0F1729) + 가장자리 빨강 35%", (3.9, 3.9))
    put(rock(on_you=True), "warn_rock_border_you_L", "내 발밑 낙석: 위 고리 + 바깥 점선 고리(지름 4.7 m)와 눈금 4개. 3개 중 하나만 겹쳐 얹는다", (5.7, 5.7))
    put(deck_arrow(), "warn_deck_arrow_border_L", "갑판 기울기 방향 화살 3겹 테두리 4×2 m, 오른쪽(+x)이 앞. 코드가 미끄러지는 방향으로 돌려 놓는다", (4.0, 2.0))
    put(deck_arrow(fill=True), "warn_deck_arrow_fill", "갑판 기울기 화살 채움(빨강 55%). 한 겹씩 차례로 켜면 방향이 읽힘", (4.0, 2.0))
    put(spawn(), "warn_spawn", "물 혼 나오는 자리: 물결 고리 둘 + 붉은 물방울. 채움 없음", (2.0, 2.0))
    json.dump(FILES, open(os.path.join(U.UI, "_boss_warn.json"), "w"), ensure_ascii=False, indent=1)
    U.dump_manifest("ui_manifest.json")
    dst = os.path.join(os.path.dirname(__file__), "..", "..", "unity", "Assets", "Resources", "Sprites", SUB); os.makedirs(dst, exist_ok=True)
    for f in os.listdir(os.path.join(U.UI, SUB)):
        shutil.copy(os.path.join(U.UI, SUB, f), os.path.join(dst, f))
    print(len(FILES), "장 저장")

if __name__ == "__main__":
    run()
