"""적 공격 예고 장판 한 벌(아트, 2026-10-31) — 개편안 P0-5 '모든 적 공격은 같은 문법으로 예고'의 바닥 그림.
실행: python3 tools/art3d/overhaul_tele.py   (결과: assets3d/ui/overhaul/tele/ + unity/Assets/Resources/Sprites/overhaul/tele/)

같은 문법(모든 혼·거센 혼 공통)
 1) 바닥에 범위가 처음부터 옅게 보인다(_ghost) — 어디가 위험한지는 선딜 시작 0초부터 읽힌다.
 2) 같은 모양의 붉은 채움(_fill)이 중심(원)·꼭짓점(부채꼴)·뒤쪽 끝(띠)에서 '안으로 차오른다'. 다 차는 순간이 판정이다.
    (코드: 채움 스프라이트 크기를 0→1로 키운다. 원·부채꼴은 가운데 기준 정비례, 띠·선은 가로(길이)만 키우고 뒤쪽 끝이 기준점.)
 3) 테두리(_border)는 늘 한지색 굵은 실선(+먹 바깥선). 밝은 풀밭·어두운 밤 어디서나 윤곽이 선다.
 4) 파혼 범위(tele/pahon_*)는 반대 문법: 주황 점선 + 바깥 톱니, 채움 없음. 위험(빨강·실선·차오름) ↔ 내 기술(주황·점선·빈 안쪽)이 색을 못 봐도 갈린다.
단위: 1 m = 128 px(기존 보스 경고 boss_warn과 같음). 테두리 굵기는 늘 12 cm 정도라 크기마다 따로 구운 그림이다(스케일 금지, 채움·잔상만 스케일 가능).
수정 전 확인: python3 tools/art3d/overhaul_tele_check.py"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overhaul_lib import *

PPM = 128          # 1 m당 픽셀
F = 2              # 그릴 때 배율(큰 그림이라 4배 대신 2배)
BORDER_PX = 15     # 한지 선 굵기 ≈ 12 cm
PAD = 14           # 테두리 바깥 여유(먹 바깥선까지 잘리지 않게)


def new(w, h): return Image.new("RGBA", (w * F, h * F), (0, 0, 0, 0))


def stroke_path(d, pts, width, col, closed=True):
    P = [(x * F, y * F) for x, y in pts] + ([(pts[0][0] * F, pts[0][1] * F)] if closed else [])
    d.line(P, fill=col, width=max(1, int(width * F)), joint="curve")
    r = width * F / 2
    for x, y in P[:-1] if closed else P:       # 꺾이는 곳·끝을 둥글게(선만 그으면 꼭짓점이 갈라진다)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def border_strokes(d, pts, closed=True):
    """먹 바깥선(굵게) → 한지 실선(12 cm) → 안쪽 가는 먹선 순서로 같은 길을 세 번 그린다."""
    stroke_path(d, pts, BORDER_PX + 8, rgba((18, 20, 30), 235), closed)
    stroke_path(d, pts, BORDER_PX, rgba(HANJI, 255), closed)
    stroke_path(d, pts, 3, rgba((18, 20, 30), 200), closed)


def circle_pts(cx, cy, r, a0=0, a1=360, n=180):
    return [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * r, cy + math.sin(math.radians(a0 + (a1 - a0) * i / n)) * r) for i in range(n + 1)]


def hatch_rgba(w, h, gap=20, ang=45):
    """채움 무늬: 밝은 붉은 빗금 ↔ 어두운 붉은 먹빗금이 번갈아. 왜 둘 다냐: 빨강 한 가지 투명판은 밝은 풀밭과 밝기가 비슷해
    흑백·색약에서 '채워졌는지'가 안 보인다. 한 줄은 밝게(+), 한 줄은 어둡게(−) 해서 어떤 바닥 위에서도 줄무늬로 읽힌다."""
    yy, xx = np.mgrid[0:h * F, 0:w * F].astype(np.float32)
    band = (((xx + yy) / F / gap) % 1.0) < 0.5
    arr = np.zeros((h * F, w * F, 4), np.float32)
    lt = np.array((255, 112, 84), np.float32); dk = np.array((92, 20, 28), np.float32)
    arr[..., :3] = np.where(band[..., None], lt, dk); arr[..., 3] = np.where(band, 150, 125)
    return arr


def shape_mask(kind, w, h, geo):
    m = Image.new("L", (w * F, h * F), 0); d = ImageDraw.Draw(m)
    if kind == "circle":
        r = geo["r"] * PPM; cx = cy = w / 2; d.ellipse([(cx - r) * F, (cy - r) * F, (cx + r) * F, (cy + r) * F], fill=255)
    elif kind == "cone":
        r = geo["r"] * PPM; half = geo["deg"] / 2; cx, cy = PAD, h / 2
        d.polygon([(cx * F, cy * F)] + [(x * F, y * F) for x, y in circle_pts(cx, cy, r, -half, half, 90)], fill=255)
    else:  # band
        d.rounded_rectangle([PAD * F, PAD * F, (w - PAD) * F, (h - PAD) * F], radius=(geo["w"] * PPM / 2 * 0.25) * F, fill=255)
    return m


def geometry(kind, **g):
    if kind == "circle":
        r = g["r"] * PPM; side = int(2 * r + 2 * PAD); return side, side, g
    if kind == "cone":
        r = g["r"] * PPM; half = math.radians(g["deg"] / 2)
        return int(r + 2 * PAD), int(2 * r * math.sin(half) + 2 * PAD), g
    L, W = g["l"] * PPM, g["w"] * PPM
    return int(L + 2 * PAD), int(W + 2 * PAD), g


def outline_pts(kind, w, h, g):
    inset = BORDER_PX / 2
    if kind == "circle":
        return circle_pts(w / 2, h / 2, g["r"] * PPM - inset)
    if kind == "cone":
        r = g["r"] * PPM; half = g["deg"] / 2; cx, cy = PAD, h / 2
        ang = math.radians(half)
        # 꼭짓점·두 변·호를 안쪽으로 inset만큼 접어 넣는다(변은 안쪽으로, 꼭짓점은 사이각 이등분선 따라 전진)
        tip = (cx + inset / math.sin(ang), cy)
        return [tip] + circle_pts(cx, cy, r - inset, -half + 2.2, half - 2.2, 90)
    return [(PAD + inset, PAD + inset), (w - PAD - inset, PAD + inset), (w - PAD - inset, h - PAD - inset), (PAD + inset, h - PAD - inset)]


def make(kind, tag, **g):
    w, h, g = geometry(kind, **g)
    # 1) 테두리
    im = new(w, h); d = ImageDraw.Draw(im); border_strokes(d, outline_pts(kind, w, h, g))
    save(im, f"tele2_{tag}_border", "tele", w, h, "예고 테두리: 한지 실선 12cm + 먹 바깥선. 늘 켜 둔다(선딜 시작~판정). 크기를 바꾸지 말 것", pivot=pv(kind, w, h), x2=w <= 360)
    # 2) 잔상(범위 전체 옅게)
    m = shape_mask(kind, w, h, g); gh = new(w, h)
    solid = Image.new("RGBA", gh.size, rgba(RED, 36)); gh.paste(solid, (0, 0), m)
    save(gh, f"tele2_{tag}_ghost", "tele", w, h, "범위 전체를 옅게 깔기(알파 14%) — 선딜 0초부터 켜 둔다", pivot=pv(kind, w, h), x2=w <= 360)
    # 3) 채움(빗금+앞가장자리 밝은 선): 코드가 0→1로 키워 '안으로 차오르게'
    fill = Image.fromarray(hatch_rgba(w, h).astype(np.uint8), "RGBA"); out = new(w, h); out.paste(fill, (0, 0), m)
    ed = new(w, h); de = ImageDraw.Draw(ed)                       # 차오르는 '앞가장자리'(진행선): 크기를 키우면 함께 움직여 어디까지 찼는지 보인다
    if kind == "circle": stroke_path(de, circle_pts(w / 2, h / 2, g["r"] * PPM - 3), 6, rgba(HANJI, 235))
    elif kind == "cone": stroke_path(de, circle_pts(PAD, h / 2, g["r"] * PPM - 3, -g["deg"] / 2 + 1.5, g["deg"] / 2 - 1.5, 90), 6, rgba(HANJI, 235), closed=False)
    else: stroke_path(de, [(w - PAD - 3, PAD + 8), (w - PAD - 3, h - PAD - 8)], 6, rgba(HANJI, 235), closed=False)
    ed2 = new(w, h); ed2.paste(ed, (0, 0), m); out.alpha_composite(ed2)
    save(out, f"tele2_{tag}_fill", "tele", w, h, fill_note(kind), pivot=pv(kind, w, h), x2=w <= 360)


def pv(kind, w, h):
    """채움을 키울 때 기준점(그림 안 비율, 왼쪽 위 0,0). 코드는 이 점을 월드의 '혼 쪽 시작점'에 맞춘다."""
    if kind == "circle": return [0.5, 0.5]
    if kind == "cone": return [round(PAD / w, 4), 0.5]
    return [round(PAD / w, 4), 0.5]


def fill_note(kind):
    return {"circle": "채움: 가운데 기준 정비례 0→1로 키운다(원이 안쪽에서 바깥으로 차오름)",
            "cone": "채움: 꼭짓점(왼쪽 가운데) 기준 정비례 0→1(부채꼴이 꼭짓점에서 퍼져 나감)",
            "band": "채움: 뒤쪽 끝(왼쪽) 기준 가로(길이)만 0→1(혼에서 앞으로 번져 나감), 세로 1 고정"}[kind]


# ------------------------------------------------------------------ 파혼(반대 문법)과 혼 발밑 표시
def make_pahon(r, tag):
    side = int(2 * r * PPM + 2 * PAD + 20); im = new(side, side); d = ImageDraw.Draw(im); c = side / 2; R = r * PPM
    n = max(28, int(r * 12))
    for i in range(n):                                                                              # 점선 고리(주황, 먹 바깥선 포함)
        a0 = 360 * i / n; a1 = a0 + 360 / n * 0.55
        for wd, col in ((14, rgba((18, 20, 30), 230)), (8, rgba(ORANGE, 255))):
            d.arc([(c - R) * F, (c - R) * F, (c + R) * F, (c + R) * F], a0, a1, fill=col, width=int(wd * F))
    nt = max(24, int(r * 10))
    for i in range(nt):                                                                             # 바깥 톱니
        t = 2 * math.pi * (i + .5) / nt; r0, r1 = R + 9, R + 24; hw = 0.5 * math.pi / nt
        pts = [(c + math.cos(t - hw) * r0, c + math.sin(t - hw) * r0), (c + math.cos(t) * r1, c + math.sin(t) * r1), (c + math.cos(t + hw) * r0, c + math.sin(t + hw) * r0)]
        d.polygon([(x * F, y * F) for x, y in pts], fill=rgba(ORANGE, 255))
    save(im, f"tele2_pahon_{tag}", "tele", side, side, f"파혼 범위 반경 {r} m — 주황 점선 + 바깥 톱니, 채움 없음(위험 장판과 반대 문법). 색을 못 봐도 점선·톱니로 갈린다", pivot=[0.5, 0.5], x2=side <= 360)


def make_foot():
    """혼 발밑 '벼르는 숨': 공격을 준비하는 혼 발밑에서 붉은 원판이 차오른다(몸이 붉게 차오름과 짝). 여러 혼 중 '누가 때리려는지' 한눈에."""
    side = 200; im = new(side, side); d = ImageDraw.Draw(im); c = side / 2
    d.ellipse([(c - 44) * F, (c - 44) * F, (c + 44) * F, (c + 44) * F], fill=rgba(RED, 120))
    yy, xx = np.mgrid[0:side * F, 0:side * F].astype(np.float32); rr = np.hypot(xx - c * F, yy - c * F) / F
    glow = np.clip((rr - 20) / 40, 0, 1) * (rr < 52)                                                # 가장자리로 갈수록 붉게
    arr = np.zeros((side * F, side * F, 4), np.float32); arr[..., 0], arr[..., 1], arr[..., 2] = RED; arr[..., 3] = glow * 120
    im.alpha_composite(Image.fromarray(arr.astype(np.uint8), "RGBA"))
    stroke_path(d, circle_pts(c, c, 52, 0, 360, 120), 8, rgba((18, 20, 30), 230)); stroke_path(d, circle_pts(c, c, 52, 0, 360, 120), 4, rgba(HANJI, 255))
    save(im, "tele2_foot", "tele", side, side, "공격 예고 중인 혼 발밑 고리(반경 52px = 약 0.4 m, 혼 몸 크기에 맞게 코드가 키움). 예고 시작에 켜고 판정 순간 끈다", pivot=[0.5, 0.5])


if __name__ == "__main__":
    for r in (1.6, 2.0, 2.5, 3.0, 3.5): make("circle", f"circle_r{str(r).replace('.', '_')}", r=r)
    make("cone", "cone90_r2_2", r=2.2, deg=90)          # 기본 혼 근접(ENEMY_ATTACK_RANGE 2.2)
    make("cone", "cone90_r1_6", r=1.6, deg=90)          # 잔넋(SOULTYPE_MOTE_RANGE 1.6)
    make("band", "band_6x1_6", l=6.0, w=1.6)             # 거센 혼 덮치기 띠(ELITE_POUNCE_LEN·W)
    make("band", "line_14x0_6", l=14.0, w=0.6)           # 넋두리 던지기 궤적(SOULTYPE_WAIL_ORB_RANGE_M 14)
    make_pahon(3.0, "r3_0"); make_pahon(4.5, "r4_5"); make_foot(); dump_manifest()
    print("ok", len(MANIFEST))
