"""보스 싸움터 3곳: 나루 영감(나루터 물 위) · 월화(폐당집 굿판) · 서 의원(역병막 마당).
산출(모두 assets3d/ 아래):
  props/prop_*.glb            새 소품 14종 + 오방기 5색(규약은 zone_props.py와 같음: 원점=바닥 한가운데, 정면=-Y, 1단위=1m, 불빛은 Light_ 빈 오브젝트)
  boss/arena_*.png            바닥 무늬 3장(arena_b01/b02/b03_floor.png) + 패턴 예고 장판 그림 6장(tele_*.png)
  layouts/boss_arenas.json    싸움터별 중심·바닥 높이·소품 배치·조명·예고 장판 규격(코드팀은 이 JSON만 읽으면 된다)
바닥 무늬 그림 규약: 정사각 RGBA, 그림의 위쪽=북(+y), 오른쪽=동(+x), 그림 한가운데=보스 자리. 땅 위 size_m 정사각 판(quad)에 깔고 땅보다 0.04m 띄운다.
예고 장판 그림 규약: 흰색+알파(색은 코드가 입힘). 가운데 알파는 옅게(0.3), 가장자리는 선명하게(1.0)라 색을 칠하면 '칸 안이 점점 붉어지는' 연출이 된다.
실행: python3 boss_arenas.py [props|floors|tele|layout|all]  (기본 all)"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

# ───────────────────────────── 싸움터 기본 정보(코드팀 Boss.cs / balance.json 에서 가져온 값) ─────────────────────────────
HM = None
def ground_z(x, y):
    """heightmap.png(R·G 16비트, −1~8m, 행0=y0)에서 땅 높이."""
    global HM
    if HM is None:
        im = np.array(Image.open(os.path.join(OUT, "terrain", "heightmap.png")).convert("RGB")).astype(float)
        HM = (im[..., 0] * 256 + im[..., 1]) / 65535 * 9 - 1
    return float(HM[int(round(y)), int(round(x))])
def arena_ground(x, y, r):
    ys, xs = np.mgrid[int(y - r):int(y + r) + 1, int(x - r):int(x + r) + 1]; ground_z(x, y)
    v = HM[ys, xs][(xs - x) ** 2 + (ys - y) ** 2 <= r * r]; return float(v.max())

ARENAS = {
    "B01": dict(name="나루 영감 · 나루터", x=404.0, y=288.0, radius=18.0, inner=11.0, floor_m=44.0, water=True),
    "B02": dict(name="월화 · 폐당집 굿판", x=580.0, y=521.0, radius=9.6, ring=7.0, floor_m=24.0),
    "B03": dict(name="서 의원 · 역병막 마당", x=46.0, y=453.0, radius=8.0, cell=2.0, grid=5, floor_m=14.0),
}

# ───────────────────────────── 1) 소품(블렌더) ─────────────────────────────
def build_props(want=None):
    from lib3d import reset, join, export, bounds, tris, box, cyl, sphere, mat, light_empty
    def mooring_post():
        """나룻말뚝: 물가에 박은 굵은 말뚝. 목에 밧줄 매듭과 흰 헝겊, 위에 푸른 혼불 등. 높이 2.4m. 큰물이 차오르는 11m 경계를 눈에 띄게 한다."""
        p = [cyl("post", 0.16, 0.13, 2.2, (0, 0, 0), "wood_dark", 6), cyl("cap", 0.19, 0.12, 0.12, (0, 0, 2.2), "wood", 6), cyl("knot", 0.2, 0.2, 0.1, (0, 0, 1.5), "thatch", 6), cyl("knot2", 0.19, 0.19, 0.08, (0, 0, 1.3), "thatch", 6)]
        p += [box("rope", (0.05, 0.05, 0.9), (0.2, 0, 0.55), "thatch", rot=(0, 0.15, 0)), box("rag", (0.12, 0.02, 0.5), (0.22, 0, 1.08), "hanji", rot=(0, 0, 0.1))]
        p += [box("hook", (0.3, 0.04, 0.04), (0.15, 0, 2.05), "iron"), cyl("lampStr", 0.01, 0.01, 0.18, (0.3, 0, 1.85), "thatch", 4), cyl("lamp", 0.1, 0.08, 0.2, (0.3, 0, 1.65), mat("soul_fresh", 2.0), 6)]
        return p
    def flood_marker():
        """큰물 표시 탑: 돌 세 개를 쌓고 갈대 묶음과 흰 헝겊을 꽂은 바깥 경계 표시. 높이 1.5m."""
        p = [sphere("s1", 0.55, (0, 0, 0.25), "stone_dark", 6, 4, (1.3, 1.1, 0.6)), sphere("s2", 0.38, (0.05, 0, 0.62), "stone", 6, 4, (1.2, 1.0, 0.7)), sphere("s3", 0.24, (0, 0, 0.9), "stone", 5, 4)]
        p += [cyl("pole", 0.03, 0.025, 1.5, (0.02, 0, 0.9), "wood_dark", 5), box("flag", (0.45, 0.02, 0.3), (0.26, 0, 2.25), "hanji", rot=(0, 0, 0.08))]
        p += [cyl(f"reed{i}", 0.02, 0.01, 1.0 + 0.1 * (i % 3), (math.cos(i * 1.3) * 0.35, math.sin(i * 1.3) * 0.3, 0.4), "reed", 4, rot=(0.12 * math.sin(i), 0.12 * math.cos(i), 0)) for i in range(5)]
        return p
    def broken_pole():
        """부러진 삿대: 갈대 속에 기울어 박힌 삿대. 칼금 열한 개와 반만 그어진 열두째(서사 단서). 길이 3m."""
        p = [cyl("pole", 0.05, 0.04, 2.6, (0, 0, 0), "wood", 6, rot=(0.0, 0.22, 0)), cyl("tip", 0.04, 0.0, 0.5, (0.55, 0, 2.5), "wood", 5, rot=(0, 0.5, 0)), box("snap", (0.14, 0.08, 0.06), (0.5, 0, 2.55), "hanji", rot=(0, 0.6, 0))]
        for i in range(12):
            h = 0.35 + i * 0.1; w = 0.08 if i < 11 else 0.04
            p.append(box(f"cut{i}", (w, 0.012, 0.012), (0.04 + h * 0.22, -0.05, h), "ink"))
        return p
    def arena_cup():
        """굿판 잔(바로 선 것): 굽 높은 하얀 사기잔. 지름 0.6m·높이 0.5m(코드 임시 원기둥을 갈아 끼움)."""
        return [cyl("foot", 0.16, 0.2, 0.12, (0, 0, 0), "hanji", 8), cyl("stem", 0.1, 0.14, 0.2, (0, 0, 0.1), "hanji", 8), cyl("bowl", 0.3, 0.2, 0.22, (0, 0, 0.3), "hanji", 10), cyl("rim", 0.31, 0.31, 0.03, (0, 0, 0.5), "gold", 10),
                cyl("liquid", 0.26, 0.26, 0.02, (0, 0, 0.47), mat("#6A1F1F", 0.0), 10)]
    def arena_cup_down():
        """엎어진 열두째 잔: 같은 잔을 뒤집어 비스듬히 놓고 엎질러진 붉은 얼룩. 늘 안전한 자리의 표식. 지름 0.7m."""
        return [cyl("bowl", 0.2, 0.3, 0.22, (0.05, 0, 0.12), "hanji", 10, rot=(0.25, 0.1, 0)), cyl("foot", 0.2, 0.16, 0.12, (0.05, 0.03, 0.3), "hanji", 8, rot=(0.25, 0.1, 0)),
                cyl("spill", 0.38, 0.34, 0.02, (-0.15, -0.15, 0.0), mat("#6A1F1F", 0.0), 9), cyl("stain2", 0.2, 0.18, 0.02, (-0.55, -0.35, 0.0), mat("#6A1F1F", 0.0), 7)]
    def arena_gutsang():
        """굿상(싸움터용 큰 것. 컷신용 작은 prop_gutsang과 별개): 낮은 상 위에 흰 천, 과일 탑, 붉은 초 두 자루, 팥시루, 부러진 살의 부채. 폭 2.6m·깊이 1.2m·높이 1.4m. Light_gutsang(따뜻한 촛불)."""
        p = [box("table", (2.6, 1.2, 0.7), (0, 0, 0.35), "wood_dark"), box("cloth", (2.7, 1.3, 0.04), (0, 0, 0.72), "hanji"), box("hang", (2.2, 0.03, 0.5), (0, -0.66, 0.5), "hanji")]
        for i, (x, h) in enumerate(((-0.9, 0.45), (-0.55, 0.38), (0.3, 0.4), (0.75, 0.5))):
            p += [cyl(f"plate{i}", 0.2, 0.17, 0.08, (x, 0.1, 0.74), "stone", 7)] + [sphere(f"fruit{i}_{k}", 0.09, (x + 0.05 * (k % 2) - 0.03, 0.1, 0.84 + k * 0.1), "berry" if i % 2 else "gold", 5, 4) for k in range(int(h * 8) - 2)]
        p += [cyl(f"candle{s}", 0.04, 0.04, 0.4, (s * 1.0, -0.2, 0.74), "red", 6) for s in (-1, 1)] + [sphere(f"flame{s}", 0.05, (s * 1.0, -0.2, 1.18), mat("#FFC060", 2.5), 5, 4, (1, 1, 1.6)) for s in (-1, 1)]
        p += [cyl("sirut", 0.2, 0.17, 0.26, (0.0, 0.25, 0.74), "mud", 8), box("fanHandle", (0.04, 0.3, 0.02), (-0.3, -0.3, 0.77), "wood"), box("fanA", (0.3, 0.02, 0.18), (-0.38, -0.5, 0.82), "hanji", rot=(0, 0, 0.5))]
        return p
    def obangki(color):
        def f():
            """오방기: 긴 깃대 끝에 삼각 깃발과 술. 높이 4.4m. 동 청·남 적·서 백·북 흑·중앙 황."""
            p = [cyl("pole", 0.05, 0.035, 4.2, (0, 0, 0), "wood_dark", 5), sphere("finial", 0.08, (0, 0, 4.3), "gold", 5, 4), cyl("base", 0.3, 0.22, 0.3, (0, 0, 0), "stone_dark", 6)]
            p += [box(f"flag{i}", (0.55 - 0.1 * i, 0.025, 0.42 - 0.07 * i), (0.3 + 0.12 * i, 0, 3.85 - 0.0 * i), color, rot=(0, 0, 0.04 * i)) for i in range(4)]
            p += [box("flagTail", (0.9, 0.025, 0.1), (0.5, 0, 3.55), color, rot=(0, 0, -0.12)), box("fringe", (0.5, 0.02, 0.07), (0.3, 0, 3.4), "gold")]
            return p
        return f
    def brazier():
        """굿판 화로: 쇠 세발 위 둥근 화로에 붉은 불. 높이 1.1m. Light_brazier(주황붉은 불빛)."""
        p = [cyl(f"leg{i}", 0.04, 0.03, 0.8, (math.cos(i * 2.094) * 0.28, math.sin(i * 2.094) * 0.28, 0.0), "iron", 5, rot=(math.sin(i * 2.094) * 0.18, -math.cos(i * 2.094) * 0.18, 0)) for i in range(3)]
        p += [cyl("bowl", 0.42, 0.28, 0.28, (0, 0, 0.8), "iron", 8), cyl("embers", 0.36, 0.36, 0.05, (0, 0, 1.06), mat("#FF5A30", 2.2), 8)]
        p += [sphere(f"fl{i}", 0.13 - 0.02 * i, (math.sin(i * 2.0) * 0.1, math.cos(i * 2.0) * 0.1, 1.2 + i * 0.16), mat("#FF8A3A", 2.4), 5, 4, (1, 1, 1.5)) for i in range(3)]
        return p
    def medicine_chest_big():
        """큰 약장: 다섯 칸×여섯 줄 서랍, 놋 고리 손잡이. 맨 아래 가운데 서랍만 청록(약점 '진짜 명단' 칸). 폭 2.6m·깊이 0.9m·높이 2.4m. 정면=-Y."""
        p = [box("body", (2.6, 0.9, 2.3), (0, 0, 1.15), "wood_dark"), box("top", (2.8, 1.0, 0.1), (0, 0, 2.35), "wood"), box("plinth", (2.7, 0.95, 0.12), (0, 0, 0.06), "wood")]
        for r in range(6):
            for c in range(5):
                x = -1.04 + c * 0.52; z = 0.42 + r * 0.33; bottom = (r == 0 and c == 2)
                p += [box(f"dr{r}{c}", (0.46, 0.04, 0.28), (x, -0.47, z), mat("#4FA8A0", 0.9) if bottom else ("wood" if (r + c) % 2 else "pillar")), box(f"kn{r}{c}", (0.07, 0.04, 0.04), (x, -0.51, z), "gold"),
                      box(f"lb{r}{c}", (0.2, 0.012, 0.07), (x, -0.5, z + 0.07), "hanji")]
        return p
    def name_board_row():
        """명패 줄: 기둥 둘 사이에 끈으로 매단 이름표 열두 장. 지워진 환자들의 이름(일부는 먹으로 지워짐). 폭 4m·높이 2.2m."""
        p = [cyl(f"post{s}", 0.07, 0.06, 2.2, (s * 2.0, 0, 0), "wood_dark", 5) for s in (-1, 1)] + [box("cord", (4.0, 0.03, 0.03), (0, 0, 2.0), "thatch")]
        for i in range(12):
            x = -1.76 + i * 0.32; p += [box(f"str{i}", (0.01, 0.01, 0.25), (x, 0, 1.88), "thatch"), box(f"tab{i}", (0.2, 0.025, 0.42), (x, 0, 1.55), "hanji", rot=(0, 0, 0.08 * math.sin(i * 1.7))), box(f"nm{i}", (0.05, 0.03, 0.28 if i % 3 else 0.1), (x, -0.012, 1.55), "ink")]
            if i % 3 == 0: p.append(box(f"x{i}", (0.2, 0.03, 0.04), (x, -0.02, 1.55), "red", rot=(0, 0.6, 0)))
        return p
    def corner_stone():
        """낙인 모서리석: 번호 칸 마당의 네 모서리를 표시하는 돌. 윗면에 붉은 도장 자국, 옆에 푸른 초록 등불. 높이 1.0m. Light_corner_stone(탁한 연두)."""
        return [box("stone", (0.6, 0.6, 0.8), (0, 0, 0.4), "stone_dark", rot=(0, 0, 0.1)), box("top", (0.66, 0.66, 0.1), (0, 0, 0.84), "stone"), cyl("seal", 0.2, 0.2, 0.03, (0, 0, 0.92), "red", 8),
                box("sealX", (0.3, 0.04, 0.03), (0, 0, 0.95), "hanji"), box("sealY", (0.04, 0.3, 0.03), (0, 0, 0.95), "hanji"), sphere("glow", 0.1, (0.0, 0, 1.12), mat("#9FE0B0", 1.8), 6, 4)]
    def brand_rack():
        """낙인 인두 걸이: 숯불 위 쇠틀에 벌겋게 달군 인두 다섯 자루. 폭 1.6m·높이 1.3m. Light_brand_rack(붉은 불빛)."""
        p = [box("coal", (1.6, 0.6, 0.3), (0, 0, 0.15), "stone_dark"), box("embers", (1.4, 0.45, 0.05), (0, 0, 0.32), mat("#FF4A28", 2.2))]
        p += [cyl(f"legF{s}", 0.04, 0.04, 1.1, (s * 0.75, -0.25, 0.0), "iron", 5) for s in (-1, 1)] + [cyl(f"legB{s}", 0.04, 0.04, 1.1, (s * 0.75, 0.25, 0.0), "iron", 5) for s in (-1, 1)] + [box("bar", (1.6, 0.05, 0.05), (0, 0, 1.1), "iron")]
        for i in range(5):
            x = -0.55 + i * 0.275; p += [cyl(f"iron{i}", 0.02, 0.02, 0.75, (x, 0, 0.5), "iron", 5), box(f"head{i}", (0.1, 0.1, 0.08), (x, 0, 0.45), mat("#FF5A30", 2.0))]
        return p
    PROPS = [("mooring_post", mooring_post, ("#9FDCFF", 1.0, 9.0, "Light_mooring_post", (0.3, 0, 1.65))), ("flood_marker", flood_marker, None), ("broken_pole", broken_pole, None),
             ("arena_cup", arena_cup, None), ("arena_cup_down", arena_cup_down, None), ("arena_gutsang", arena_gutsang, ("#FFB066", 1.1, 8.0, "Light_arena_gutsang", (0, 0, 1.2))),
             ("obangki_blue", obangki("#3A6FB5"), None), ("obangki_red", obangki("#D6452E"), None), ("obangki_yellow", obangki("#E0B84A"), None), ("obangki_white", obangki("#EDE6D8"), None), ("obangki_black", obangki("#2A2A3A"), None),
             ("brazier", brazier, ("#FF7A3A", 1.4, 11.0, "Light_brazier", (0, 0, 1.25))), ("medicine_chest_big", medicine_chest_big, ("#4FA8A0", 0.6, 5.0, "Light_chest_weak", (0, -0.7, 0.45))),
             ("name_board_row", name_board_row, None), ("corner_stone", corner_stone, ("#8FE0A8", 0.9, 7.0, "Light_corner_stone", (0, 0, 1.12))), ("brand_rack", brand_rack, ("#FF5A30", 1.2, 8.0, "Light_brand_rack", (0, 0, 0.6)))]
    res = []
    for key, fn, lt in PROPS:
        if want and key not in want: continue
        reset(); o = join(f"prop_{key}", fn()); lo, hi = bounds(o)
        if lt: col, it, rg, nm, pos = lt; light_empty(o, nm, pos, col, intensity=it, range_m=rg, flicker=True)
        export(o, os.path.join(OUT, "props", f"prop_{key}.glb"))
        res.append({"name": f"prop_{key}", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}); print(res[-1])
    json.dump(res, open(os.path.join(OUT, "props", "_report_arena.json"), "w"), ensure_ascii=False, indent=1)

# ───────────────────────────── 2) 바닥 무늬 그림 ─────────────────────────────
def _noise(n, scale, seed):
    r = np.random.RandomState(seed); g = r.rand(n // scale + 2, n // scale + 2)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC); return np.asarray(im, np.float32) / 255
def _hex(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def _font(sz): return ImageFont.truetype(FONT, sz)
HANJA = "零一二三四五六七八九十"
def hanja(n):
    if n <= 10: return HANJA[n]
    if n < 20: return "十" + HANJA[n - 10]
    return HANJA[n // 10] + "十" + (HANJA[n % 10] if n % 10 else "")

def _finish(base, draw_fn, path, n):
    """base=(n,n,3) 색, draw_fn(ImageDraw RGBA 레이어, S배 확대). 알파는 draw_fn이 지정한 바닥 모양(L 마스크)을 따른다."""
    pass

def floor_b02():
    """월화 굿판 24m(64px/m): 짚자리 둥근 판(반경 9.6) + 오방색 띠 + 잔 열두 자리(한자 번호) + 12칸 선 + 가운데 황색 오방 무늬 + 붉은 얼룩."""
    PPM = 64; n = 24 * PPM; C = n / 2; S = 2; N = n * S
    yy, xx = np.mgrid[0:N, 0:N]; r = np.hypot(xx - N / 2, yy - N / 2) / (PPM * S); ang = (np.degrees(np.arctan2(-(yy - N / 2), xx - N / 2)) % 360)
    nz = _noise(N, 16 * S, 1) * 0.5 + _noise(N, 4 * S, 2) * 0.5
    weave = (np.sin((xx + yy) / (PPM * S) * 22) * 0.5 + np.sin((xx - yy) / (PPM * S) * 22) * 0.5) * 0.06
    straw = np.array(_hex("#7A6842"), np.float32) * (0.82 + 0.3 * nz[..., None] + weave[..., None])
    img = Image.fromarray(np.clip(straw, 0, 255).astype(np.uint8)).convert("RGBA"); base = img; layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)   # 반투명 그림은 따로 그린 층을 합쳐야 섞인다
    P = lambda a, rad: (N / 2 + math.cos(math.radians(a)) * rad * PPM * S, N / 2 - math.sin(math.radians(a)) * rad * PPM * S)
    # 바깥 테두리: 어두운 널 가장자리와 붉은 줄
    for rad, col, w in ((9.55, (58, 40, 28, 255), 0.35), (9.15, (200, 70, 50, 255), 0.09), (7.95, (240, 231, 211, 230), 0.05)):
        d.ellipse([N / 2 - rad * PPM * S, N / 2 - rad * PPM * S, N / 2 + rad * PPM * S, N / 2 + rad * PPM * S], outline=col, width=int(w * PPM * S))
    # 오방색 띠(잔 고리 r=7): 72°씩 청 적 황 백 흑
    colors = [("#3A6FB5", 0), ("#D6452E", 72), ("#E0B84A", 144), ("#EDE6D8", 216), ("#3A3A4A", 288)]
    for h, a0 in colors:
        d.arc([N / 2 - 7 * PPM * S, N / 2 - 7 * PPM * S, N / 2 + 7 * PPM * S, N / 2 + 7 * PPM * S], start=-a0 - 72 + 360, end=-a0 + 360, fill=_hex(h) + (235,), width=int(0.34 * PPM * S))
    # 12칸 선(30° 부채꼴 경계)과 잔 자리
    for i in range(12):
        a = i * 30
        for off in (-15, 15):
            d.line([P(a + off, 1.6), P(a + off, 8.9)], fill=(240, 231, 211, 90), width=int(0.04 * PPM * S))
        cx, cy = P(a, 7.0); rad = 0.55 * PPM * S
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(40, 28, 22, 200), outline=(240, 231, 211, 255), width=int(0.06 * PPM * S))
        if i == 11:   # 엎어진 열두째: 붉은 X와 번쩍이는 안전 표시(청록 테두리)
            d.ellipse([cx - rad * 1.45, cy - rad * 1.45, cx + rad * 1.45, cy + rad * 1.45], outline=(95, 227, 192, 255), width=int(0.08 * PPM * S))
            d.line([(cx - rad * .6, cy - rad * .6), (cx + rad * .6, cy + rad * .6)], fill=(232, 92, 65, 255), width=int(0.07 * PPM * S)); d.line([(cx - rad * .6, cy + rad * .6), (cx + rad * .6, cy - rad * .6)], fill=(232, 92, 65, 255), width=int(0.07 * PPM * S))
        tx, ty = P(a, 8.55); f = _font(int(0.62 * PPM * S)); tw = d.textlength(hanja(i + 1), font=f)
        d.text((tx - tw / 2, ty - 0.33 * PPM * S), hanja(i + 1), font=f, fill=(240, 231, 211, 255 if i != 11 else 255))
    # 가운데 황색 판과 오방 무늬(보스가 서는 자리)
    d.ellipse([N / 2 - 3.1 * PPM * S, N / 2 - 3.1 * PPM * S, N / 2 + 3.1 * PPM * S, N / 2 + 3.1 * PPM * S], fill=_hex("#B8943C") + (255,), outline=(58, 40, 28, 255), width=int(0.12 * PPM * S))
    for rad, w in ((2.7, 0.06), (1.6, 0.05)): d.ellipse([N / 2 - rad * PPM * S, N / 2 - rad * PPM * S, N / 2 + rad * PPM * S, N / 2 + rad * PPM * S], outline=(58, 40, 28, 255), width=int(w * PPM * S))
    for h, a0 in colors:   # 오방 점
        cx, cy = P(a0 + 36, 2.15); rad = 0.26 * PPM * S; d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=_hex(h) + (255,), outline=(58, 40, 28, 255), width=int(0.04 * PPM * S))
    d.ellipse([N / 2 - 0.4 * PPM * S, N / 2 - 0.4 * PPM * S, N / 2 + 0.4 * PPM * S, N / 2 + 0.4 * PPM * S], fill=(180, 50, 38, 255))
    # 엎질러진 붉은 얼룩(열두째 잔 쪽)
    rs = np.random.RandomState(5)
    for _ in range(26):
        a = 330 + rs.randn() * 14; rad = 7.0 + rs.randn() * 1.0; cx, cy = P(a, rad); s = rs.rand() * 0.22 * PPM * S + 0.05 * PPM * S
        d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=(110, 30, 28, 150))
    # 원 밖은 투명(부드러운 가장자리)
    img = Image.alpha_composite(base, layer); mask = np.clip((9.75 - r) / 0.25, 0, 1); img.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
    img = img.resize((n, n), Image.LANCZOS); img.save(os.path.join(OUT, "boss", "arena_b02_floor.png")); return img

def floor_b03():
    """서 의원 역병막 마당 14m(64px/m): 다진 흙바닥 위에 석회로 그은 5×5 번호 칸(칸 2m, 한자 번호 一~二十五) + 재(약초 태운 자국) 둘레 + 낙인 얼룩."""
    PPM = 64; n = 14 * PPM; S = 2; N = n * S
    yy, xx = np.mgrid[0:N, 0:N]; r = np.hypot(xx - N / 2, yy - N / 2) / (PPM * S)
    nz = _noise(N, 24 * S, 11) * 0.55 + _noise(N, 6 * S, 12) * 0.3 + _noise(N, 2 * S, 13) * 0.15
    earth = np.array(_hex("#6B5A44"), np.float32) * (0.72 + 0.5 * nz[..., None])
    # 갈라진 틈
    img = Image.fromarray(np.clip(earth, 0, 255).astype(np.uint8)).convert("RGBA"); base = img; layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    rs = np.random.RandomState(7)
    for _ in range(40):
        x, y = rs.rand(2) * N; pts = [(x, y)]
        for k in range(rs.randint(3, 7)): x += rs.randn() * 0.5 * PPM * S; y += rs.randn() * 0.5 * PPM * S; pts.append((x, y))
        d.line(pts, fill=(30, 22, 16, 110), width=max(2, int(0.025 * PPM * S)))
    cell = 2.0 * PPM * S; x0 = N / 2 - 2.5 * cell
    for i in range(5):        # i = 동쪽으로 갈수록 +(코드 CellPos i), j = 북쪽으로 갈수록 +. 번호 = i*5+j+1
        for j in range(5):
            cx0 = x0 + i * cell; cy0 = N / 2 + 2.5 * cell - (j + 1) * cell
            shade = 14 if (i + j) % 2 else 0
            d.rectangle([cx0 + 3, cy0 + 3, cx0 + cell - 3, cy0 + cell - 3], fill=(245, 235, 215, 20 + shade))
            num = i * 5 + j + 1; f = _font(int(0.5 * PPM * S)); t = hanja(num); tw = d.textlength(t, font=f)
            d.text((cx0 + cell / 2 - tw / 2, cy0 + cell / 2 - 0.36 * PPM * S), t, font=f, fill=(35, 26, 22, 170))
    for k in range(6):   # 석회 줄(조금 삐뚤게)
        a = x0 + k * cell
        for (p0, p1) in (((a, N / 2 - 2.5 * cell), (a, N / 2 + 2.5 * cell)), ((x0, N / 2 - 2.5 * cell + k * cell), (x0 + 5 * cell, N / 2 - 2.5 * cell + k * cell))):
            d.line([p0, p1], fill=(238, 232, 214, 235), width=int(0.075 * PPM * S))
    # 모서리 낙인 자국(붉은 동그라미 + 十)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = N / 2 + sx * 2.5 * cell, N / 2 + sy * 2.5 * cell; rad = 0.34 * PPM * S
            d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(190, 60, 48, 230), width=int(0.07 * PPM * S)); d.line([(cx - rad * .6, cy), (cx + rad * .6, cy)], fill=(190, 60, 48, 230), width=int(0.06 * PPM * S)); d.line([(cx, cy - rad * .6), (cx, cy + rad * .6)], fill=(190, 60, 48, 230), width=int(0.06 * PPM * S))
    # 둘레: 약재 태운 재(검은 점)와 푸른 독기 얼룩
    for _ in range(420):
        a = rs.rand() * 2 * math.pi; rr = 6.2 + rs.rand() * 0.8 + abs(rs.randn()) * 0.1; cx = N / 2 + math.cos(a) * rr * PPM * S; cy = N / 2 + math.sin(a) * rr * PPM * S; s = (0.03 + rs.rand() * 0.1) * PPM * S
        d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=(24, 20, 18, 150))
    for _ in range(30):
        a = rs.rand() * 2 * math.pi; rr = 5.2 + rs.rand() * 1.6; cx = N / 2 + math.cos(a) * rr * PPM * S; cy = N / 2 + math.sin(a) * rr * PPM * S; s = (0.2 + rs.rand() * 0.35) * PPM * S
        d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=(90, 130, 105, 40))
    # 보스가 서는 한가운데 칸(i=2,j=2): 의원의 발자리(붉은 도장 반경 2.5m의 옅은 윤곽)
    rad = 2.5 * PPM * S; d.ellipse([N / 2 - rad, N / 2 - rad, N / 2 + rad, N / 2 + rad], outline=(190, 60, 48, 90), width=int(0.05 * PPM * S))
    img = Image.alpha_composite(base, layer); mask = np.clip((6.95 - r) / 0.5, 0, 1); img.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
    img = img.resize((n, n), Image.LANCZOS); img.save(os.path.join(OUT, "boss", "arena_b03_floor.png")); return img

def floor_b01():
    """나루 영감 나루터 44m(32px/m): 물 위 두 겹 경계. 바깥(반경 18m)=처음 싸움터 가장자리(물이 얕아지는 어두운 띠 + 거품), 안쪽(반경 11m)=큰물이 차오른 뒤의 경계(밝은 흰 점선 + 푸른 띠).
    가운데는 보스 배가 도는 물살 무늬(소용돌이 줄). 물 표면 위에 얹는 반투명 판."""
    PPM = 32; n = 44 * PPM; S = 2; N = n * S
    yy, xx = np.mgrid[0:N, 0:N]; r = np.hypot(xx - N / 2, yy - N / 2) / (PPM * S); th = np.arctan2(yy - N / 2, xx - N / 2)
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0)); a = np.zeros((N, N), np.float32); col = np.zeros((N, N, 3), np.float32)
    def band(r0, r1, c, al):
        m = np.clip(1 - np.abs((r - (r0 + r1) / 2) / ((r1 - r0) / 2)) ** 3, 0, 1) * al
        nonlocal a, col
        add = m > a; col[add] = c; a = np.maximum(a, m)
    nz = _noise(N, 12 * S, 21)
    band(17.2, 18.4, (40, 60, 70), 0.55)                         # 바깥 경계: 어두운 젖은 띠
    foam = np.clip(1 - np.abs(r - 17.9) / 0.25, 0, 1) * (nz > 0.45); a = np.maximum(a, foam * 0.85); col[foam > 0.3] = (225, 238, 240)
    band(10.3, 11.7, (130, 190, 230), 0.5)                       # 안쪽 경계: 푸른 띠
    dash = (np.sin(th * 72) > 0.1) * np.clip(1 - np.abs(r - 11.0) / 0.12, 0, 1); a = np.maximum(a, dash * 0.95); col[dash > 0.3] = (240, 248, 255)
    sw = (np.sin(th * 3 + r * 1.6) > 0.82) * np.clip((9.5 - r) / 3, 0, 1) * np.clip((r - 2.2) / 1.5, 0, 1); a = np.maximum(a, sw * 0.28); col[sw > 0.3] = (200, 225, 240)   # 가운데 소용돌이 줄
    # 가운데 배 자리(보스 서는 곳) 얇은 둥근 선
    ring = np.clip(1 - np.abs(r - 2.6) / 0.08, 0, 1); a = np.maximum(a, ring * 0.6); col[ring > 0.3] = (232, 92, 65)
    out = np.dstack([np.clip(col, 0, 255), np.clip(a * 255, 0, 255)]).astype(np.uint8)
    im = Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(0.8 * S)).resize((n, n), Image.LANCZOS)
    im.save(os.path.join(OUT, "boss", "arena_b01_floor.png")); return im

def teles():
    """예고 장판 그림 6장(흰색+알파, 코드가 색을 입힘). 반경/폭은 그림 가장자리=1 기준이라 코드가 스케일만 맞춘다."""
    def edgefill(mask_in, edge_w, fill=0.3, S=4):
        """mask_in: 안쪽 1 / 밖 0 의 실수 배열 → 가장자리 선명 + 안쪽 옅음 알파."""
        m = mask_in > 0.5   # scipy가 없어서 흐림(가우시안)으로 '가장자리에서 얼마나 안쪽인가'를 어림한다
        bl = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(edge_w * 0.55)), np.float32) / 255
        edge = np.clip((1 - bl) * 2.2, 0, 1) * m; return np.clip(m * fill + edge * (1 - fill), 0, 1)
    def save(a, name, size):
        im = Image.fromarray(np.dstack([np.full(a.shape, 255, np.uint8)] * 3 + [(a * 255).astype(np.uint8)]), "RGBA").resize(size, Image.LANCZOS); im.save(os.path.join(OUT, "boss", name))
    N = 1024; yy, xx = np.mgrid[0:N, 0:N]; cx = N / 2
    # 원(반경=가장자리)
    r = np.hypot(xx - cx, yy - cx) / (N / 2 - 4); circ = edgefill((r < 1).astype(float), 22)
    stripe = (np.sin((xx + yy) / 26) > 0.55) * (r < 0.97) * 0.07; save(np.clip(circ + stripe, 0, 1), "tele_circle.png", (256, 256))
    # 부채꼴(꼭짓점=가운데, 동쪽(오른쪽)으로 벌어짐): 120°, 30°
    for deg, nm in ((120, "tele_sector120.png"), (30, "tele_sector30.png")):
        ang = np.degrees(np.arctan2(-(yy - cx), xx - cx)); m = ((r < 1) & (np.abs(ang) <= deg / 2)).astype(float)
        a = edgefill(m, 22); save(np.clip(a + m * (np.sin((xx + yy) / 26) > 0.55) * 0.07, 0, 1), nm, (256, 256))
    # 직선(폭 1.5 : 길이 6 = 1:4, 아래=보스 쪽, 위=끝)
    W, H = 256, 1024; yy2, xx2 = np.mgrid[0:H, 0:W]; m = ((xx2 > 6) & (xx2 < W - 6) & (yy2 > 6) & (yy2 < H - 6)).astype(float); a = edgefill(m, 20)
    chev = ((np.abs(xx2 - W / 2) * 0.7 + (yy2 % 160)) % 160 < 14) * m * 0.2; save(np.clip(a + chev, 0, 1), "tele_line.png", (128, 512))
    # 칸(한 변=1)
    N2 = 512; yy3, xx3 = np.mgrid[0:N2, 0:N2]; m = ((xx3 > 8) & (xx3 < N2 - 8) & (yy3 > 8) & (yy3 < N2 - 8)).astype(float); a = edgefill(m, 18)
    cor = np.zeros_like(a); L = 90
    for (x0, y0) in ((8, 8), (N2 - 8 - L, 8), (8, N2 - 8 - L), (N2 - 8 - L, N2 - 8 - L)): cor[y0:y0 + L, x0:x0 + 26] = 1; cor[y0:y0 + 26, x0:x0 + L] = 1
    cor[:, :] *= m; save(np.clip(a + cor * 0.5, 0, 1), "tele_cell.png", (128, 128))
    # 가로 띠 3:1(물살 밀기, 오른쪽으로 밀림: 화살 무늬)
    W, H = 1024, 256; yy4, xx4 = np.mgrid[0:H, 0:W]; m = ((xx4 > 6) & (xx4 < W - 6) & (yy4 > 6) & (yy4 < H - 6)).astype(float); a = edgefill(m, 20)
    arrow = (((xx4 % 200) - 100 + np.abs(yy4 - H / 2) * 0.9) % 200 < 20) * m * 0.3; save(np.clip(a + arrow, 0, 1), "tele_band.png", (512, 128))
    print("예고 장판 6장 저장")

# ───────────────────────────── 3) 배치표 JSON ─────────────────────────────
def polar(cx, cy, a, r): return cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r

def layout():
    A = {}
    # ── B01 나루터
    c = ARENAS["B01"]; cx, cy = c["x"], c["y"]; props = []; gz = 0.0
    for k in range(8):
        a = 22.5 + k * 45; x, y = polar(cx, cy, a, 11.0); props.append({"prop": "prop_mooring_post", "x": round(x, 2), "y": round(y, 2), "rot": round(a - 90, 1), "note": "큰물 안쪽 경계(반경 11m) 말뚝"})
    for k in range(6):
        a = 15 + k * 60; x, y = polar(cx, cy, a, 17.8); props.append({"prop": "prop_flood_marker", "x": round(x, 2), "y": round(y, 2), "rot": round(a - 90, 1), "note": "처음 싸움터 바깥 경계(반경 18m) 표시탑"})
    props += [{"prop": "prop_broken_pole", "x": 397.5, "y": 292.5, "rot": 20, "note": "부러진 삿대(칼금 열한 개+반 개 단서). 나루 계단 곁 갈대 속"},
              {"prop": "prop_brazier", "x": 399.5, "y": 295.0, "rot": 0, "note": "물가 화톳불(싸움터 서쪽 따뜻한 불빛, 보스 반대편 대비)"}]
    A["B01"] = dict(name=c["name"], boss_pos={"x": cx, "y": cy}, ground_z=round(ground_z(cx, cy), 2), arena_radius_m=18.0, shrink_radius_m=11.0, medium="물 위(배)",
                    decal={"file": "assets3d/boss/arena_b01_floor.png", "size_m": 44.0, "z_above_water": 0.05, "note": "물 표면 위에 얹는 반투명 판. 반경 18m 바깥 띠=처음 가장자리, 반경 11m 점선 띠=큰물(50%) 뒤 경계"},
                    props=props, lights=[{"x": cx, "y": cy, "z": 4.5, "color": "#7FA8E8", "intensity": 1.0, "range_m": 22.0, "flicker": False, "tag": "싸움터 위 차가운 달빛 무리(전투 중에만)"}],
                    telegraph=[{"pattern": "삿대 휩쓸기", "tex": "tele_sector120.png", "radius_m": 4.0, "warn_s": 0.6}, {"pattern": "삿대 내려찍기", "tex": "tele_line.png", "length_m": 6.0, "width_m": 1.5, "warn_s": 0.8},
                               {"pattern": "물살 밀기", "tex": "tele_band.png", "width_m": 3.0, "warn_s": 1.0, "note": "길이는 싸움터 지름"}])
    # ── B02 굿판
    c = ARENAS["B02"]; cx, cy = c["x"], c["y"]; props = []
    gzv = round(arena_ground(cx, cy, 9.6), 2)
    for i in range(12):
        x, y = polar(cx, cy, i * 30, 7.0); props.append({"prop": "prop_arena_cup_down" if i == 11 else "prop_arena_cup", "x": round(x, 2), "y": round(y, 2), "rot": round(i * 30 - 90, 1), "cup": i, "note": "열두째(번호 11) 엎어진 잔: 늘 안전" if i == 11 else "잔 앞 부채꼴 칸이 열림"})
    for nm, a, r_ in (("blue", 0, 10.4), ("black", 90, 10.4), ("white", 180, 10.4), ("red", 270, 10.4), ("yellow", 62, 10.0)):
        x, y = polar(cx, cy, a, r_); props.append({"prop": f"prop_obangki_{nm}", "x": round(x, 2), "y": round(y, 2), "rot": round(a - 90, 1), "note": "오방기"})
    for a in (45, 135, 225, 315):
        x, y = polar(cx, cy, a, 9.1); props.append({"prop": "prop_brazier", "x": round(x, 2), "y": round(y, 2), "rot": a - 90, "note": "굿판 화로(굿판 가장자리 붉은 불빛)"})
    x, y = polar(cx, cy, 118, 10.0); props.append({"prop": "prop_arena_gutsang", "x": round(x, 2), "y": round(y, 2), "rot": round(118 - 90, 1), "note": "굿상. 처결 뒤 굿상 머리에 옥이의 신칼 / 월화의 방울이 굴러 와 멈추는 자리 쪽"})
    for k, a in enumerate((200, 250, 305)):
        x, y = polar(cx, cy, a, 12.4); props.append({"prop": "prop_mangjang", "x": round(x, 2), "y": round(y, 2), "rot": a - 90, "note": "굿판 둘레 만장(바깥)"})
    A["B02"] = dict(name=c["name"], boss_pos={"x": cx, "y": cy}, ground_z=gzv, arena_radius_m=9.6, ring_radius_m=7.0, cups=12, safe_cup=11, medium="폐당집 터 평지(+2.3m 고지)",
                    decal={"file": "assets3d/boss/arena_b02_floor.png", "size_m": 24.0, "z_above_ground": 0.04, "note": "그림 위=북·오른쪽=동. 잔 i는 중심에서 (cos 30i°, sin 30i°)×7m(코드 CupPos와 일치). 한자 번호는 i+1"},
                    props=props,
                    lights=[{"x": cx, "y": cy, "z": 3.2, "color": "#E8503A", "intensity": 0.9, "range_m": 13.0, "flicker": True, "tag": "굿판 한가운데 붉은 무기운"}, {"x": cx, "y": cy, "z": 7.0, "color": "#A28CFF", "intensity": 0.5, "range_m": 18.0, "flicker": False, "tag": "폐당집 보랏빛 혼불 하늘빛"}],
                    telegraph=[{"pattern": "잔이 열린다", "tex": "tele_sector30.png", "radius_m": 8.0, "warn_s": 1.0, "note": "잔 i 앞 30° 부채꼴(잔 방향 = 30i°), 한 번에 3칸(50% 이하 4칸, 0.9초)"}, {"pattern": "붉은 천 휘감기", "tex": "tele_line.png", "length_m": 9.0, "width_m": 1.0, "warn_s": 0.7}])
    # ── B03 역병막
    c = ARENAS["B03"]; cx, cy = c["x"], c["y"]; props = []
    gzv = round(arena_ground(cx, cy, 8.0), 2)
    for sx in (-1, 1):
        for sy in (-1, 1): props.append({"prop": "prop_corner_stone", "x": round(cx + sx * 5.9, 2), "y": round(cy + sy * 5.9, 2), "rot": 0, "note": "번호 칸 모서리석(10×10m의 네 귀퉁이 바깥)"})
    props += [{"prop": "prop_medicine_chest_big", "x": cx, "y": round(cy + 8.6, 2), "rot": 0, "note": "큰 약장(북쪽 가장자리, 정면=남쪽). 맨 아래 가운데 서랍이 '진짜 명단'. 처결 뒤 씻은 붓이 놓이는 자리"},
              {"prop": "prop_name_board_row", "x": round(cx - 7.6, 2), "y": cy, "rot": 90, "note": "지워진 이름 줄(서쪽)"}, {"prop": "prop_name_board_row", "x": round(cx + 7.6, 2), "y": cy, "rot": 90, "note": "지워진 이름 줄(동쪽)"},
              {"prop": "prop_brand_rack", "x": round(cx + 7.0, 2), "y": round(cy - 6.6, 2), "rot": 160, "note": "낙인 인두 걸이(남동쪽, 붉은 불빛)"},
              {"prop": "prop_quarantine_hut", "x": round(cx - 8.4, 2), "y": round(cy - 6.6, 2), "rot": 30, "note": "격리 움막(바깥 둘레)"}, {"prop": "prop_quarantine_hut", "x": round(cx - 9.6, 2), "y": round(cy + 5.0, 2), "rot": -30, "note": "격리 움막"},
              {"prop": "prop_herb_pot", "x": round(cx + 6.4, 2), "y": round(cy + 7.0, 2), "rot": 0, "note": "약탕 화로"}, {"prop": "prop_herb_pot", "x": round(cx - 6.0, 2), "y": round(cy + 7.4, 2), "rot": 0, "note": "약탕 화로"},
              {"prop": "prop_plague_rope", "x": round(cx, 2), "y": round(cy - 9.6, 2), "rot": 0, "note": "마당 어귀 금줄(남쪽)"}, {"prop": "prop_sick_lantern", "x": round(cx - 7.6, 2), "y": round(cy - 4.0, 2), "rot": 0, "note": "초록 등불"}, {"prop": "prop_sick_lantern", "x": round(cx + 7.8, 2), "y": round(cy + 3.0, 2), "rot": 180, "note": "초록 등불"}]
    A["B03"] = dict(name=c["name"], boss_pos={"x": cx, "y": cy}, ground_z=gzv, arena_radius_m=8.0, grid=5, cell_m=2.0, medium="검은여울 서쪽 둑 평지",
                    decal={"file": "assets3d/boss/arena_b03_floor.png", "size_m": 14.0, "z_above_ground": 0.04, "note": "그림 위=북·오른쪽=동. 칸 (i,j)는 코드 CellPos와 같다: i=동쪽 +, j=북쪽 +, 번호 = i*5+j+1(한자)"},
                    props=props,
                    lights=[{"x": cx, "y": cy, "z": 3.4, "color": "#7FC49A", "intensity": 0.8, "range_m": 12.0, "flicker": True, "tag": "마당 위 탁한 연두 빛"}, {"x": cx, "y": round(cy + 8.4, 2), "z": 0.6, "color": "#4FA8A0", "intensity": 0.7, "range_m": 5.0, "flicker": False, "tag": "약장 맨 아래 서랍(약점) 청록 — 약점이 열릴 때만 켠다"}],
                    telegraph=[{"pattern": "번호 낙인", "tex": "tele_cell.png", "size_m": 2.0, "warn_s": 0.8, "note": "칸 16개(50% 이하 20개) 동시"}, {"pattern": "붉은 도장 찍기", "tex": "tele_circle.png", "radius_m": 2.5, "warn_s": 0.7}])
    # 무기·전투 진행 연출 안내
    doc = {"note": "보스 싸움터 3곳 배치표. 좌표는 필드 m(x 동·y 북, Unity z=y). 소품 z는 땅 높이에 붙이면 된다(ground_z는 반경 내 최고 높이). rot=반시계 도, 0이면 정면이 남쪽.",
           "telegraph_textures": {"dir": "assets3d/boss/", "files": ["tele_circle.png", "tele_sector120.png", "tele_sector30.png", "tele_line.png", "tele_cell.png", "tele_band.png"],
                                  "usage": "흰색+알파 그림. 코드가 색을 입히고 예고 시간 동안 알파/색을 올린다(0.3→1). 부채꼴·원은 반지름=그림 반폭, 직선은 아래가 보스 쪽, 띠는 오른쪽이 미는 방향."},
           "arenas": A}
    json.dump(doc, open(os.path.join(OUT, "layouts", "boss_arenas.json"), "w"), ensure_ascii=False, indent=1); print("배치표 저장", {k: len(v["props"]) for k, v in A.items()})
    return doc

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("props", "all"): build_props(sys.argv[2:] or None)
    if what in ("floors", "all"): floor_b01(); floor_b02(); floor_b03(); print("바닥 무늬 3장 저장")
    if what in ("tele", "all"): teles()
    if what in ("layout", "all"): layout()
