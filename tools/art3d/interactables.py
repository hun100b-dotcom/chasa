"""1막 F 상호작용 물건 모델 — 유품 6 + 재 1, 단서 물건(굿상·탄 문서함), 줍기(엽전 꾸러미·쑥), 빛기둥 4, 서낭당 쉬기 자리.
실행: python3 interactables.py   (Blender 5.x, bpy)  산출: assets3d/props/*.glb, _report_interact.json, previews/interactables_50deg.png
기준 문서: planning/data/interactables-act1.md + interactables_act1.json (모델 이름 prop_keep_* · prop_gut_table · prop_burnt_docbox 는 그 JSON 의 model 값과 같다).
규약은 props.py 와 같다: GLB, 1유닛=1m, 원점=바닥 한가운데, 재질 베이스컬러만(빛 나는 면만 발광), 정면 -Y.
빛 표시: 코드가 켜고 끌 수 있게 '반투명 빛 덩이'를 자식 메시 `Glow` 로 따로 붙인다(유품=보라 #C9B0FF, 단서=금 #D4A94E).
  - 유품은 밤에만 6m 안에서 희미하게 → 코드가 Glow 를 그 조건에서만 보이게(또는 알파를 거리로 조절). 낮엔 모델만 보인다.
  - 줍기 물건의 빛기둥은 모델 안에 넣지 않고 fx_pickup_pillar_* 를 같은 자리에 따로 세운다(등급 색이 달라서).
주황은 파혼 전용이라 빛에 쓰지 않는다(화로 불은 등롱과 같은 따뜻한 #FFB066)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
TAU = math.tau
IRON, WOOD, WOOD_D, CLOTH_W = "#3A3A44", "#6B4A2E", "#4A3322", "#E8DDA8"
PORC, CLAY, INDIGO, ASH, CHAR = "#E8E4D8", "#7A4A2E", "#2F4A8A", "#6A645A", "#2A2420"

def disc(name, r, z, col, h=0.02, segs=10, alpha=None, emit=0.0):
    return cyl(name, r, r, h, (0, 0, z), mat_alpha(col, alpha, emit) if alpha else col, segs)

# ───────── 유품 6 ─────────
def keep_tongs():
    """식은 집게: 납작한 돌 위에 놓인 쇠집게. 집게 끝에 서리 같은 푸른 기운(식었다는 표시)."""
    p = [box("slab", (0.55, 0.34, 0.08), (0, 0, 0.04), "stone"), box("slab2", (0.4, 0.26, 0.05), (0.05, 0, 0.1), "stone_dark")]
    for s in (-1, 1):
        p.append(limb(f"arm{s}", (-0.22, s * 0.015, 0.16), (0.27, s * 0.055, 0.15), 0.017, 0.013, IRON, 5))
        p.append(limb(f"grip{s}", (-0.22, s * 0.015, 0.16), (-0.34, s * 0.07, 0.14), 0.014, 0.016, WOOD_D, 5))
    p += [sphere("pivot", 0.025, (-0.05, 0, 0.17), IRON, 5, 3), sphere("frost", 0.035, (0.28, 0, 0.15), "#8FA6C8", 5, 3, (1.4, 1, 0.7))]
    return p
def keep_bowl():
    """덮은 밥그릇: 소반 위에 뚜껑 덮은 그릇, 곁에 다 탄 초 토막(제삿밥)."""
    p = [cyl("tray", 0.3, 0.28, 0.035, (0, 0, 0), WOOD_D, 10), cyl("tray_in", 0.26, 0.26, 0.01, (0, 0, 0.035), WOOD, 10)]
    p.append(lathe("bowl", [(0.04, 0.0), (0.045, 0.07), (0.12, 0.13), (0.2, 0.15), (0.25, 0.14)], 10, PORC, loc=(0, 0, 0.04)))
    p.append(lathe("lid", [(0.0, 0.16), (0.04, 0.15), (0.09, 0.1), (0.1, 0.0)], 10, PORC, loc=(0, 0, 0.27)))
    p += [sphere("knob", 0.035, (0, 0, 0.395), "#C9C5B5", 5, 3), cyl("candle", 0.03, 0.03, 0.09, (0.22, 0.1, 0.035), "#EDE8D0", 6), cyl("wick", 0.005, 0.005, 0.03, (0.22, 0.1, 0.125), CHAR, 4)]
    return p
def keep_steamer():
    """식은 떡시루: 질그릇 시루, 베보자기를 덮고 시룻번(밀가루 띠)이 갈라져 있다. 세 돌 위에 올림."""
    p = [sphere(f"rest{i}", 0.12, (math.cos(i * 2.09) * 0.28, math.sin(i * 2.09) * 0.28, 0.05), "stone", 5, 3, (1, 1, 0.55)) for i in range(3)]
    p.append(lathe("pot", [(0.0, 0.2), (0.12, 0.3), (0.38, 0.32), (0.5, 0.3)], 11, CLAY, loc=(0, 0, 0.1)))
    p += [cyl("band", 0.31, 0.31, 0.04, (0, 0, 0.58), "#D8D0C0", 11), sphere("cloth", 0.3, (0, 0, 0.62), CLOTH_W, 9, 4, (1, 1, 0.35))]
    p += [limb(f"fold{i}", (0, 0, 0.7), (math.cos(i * 2.4) * 0.32, math.sin(i * 2.4) * 0.32, 0.54), 0.02, 0.01, CLOTH_W, 3) for i in range(4)]
    return p
def keep_lamp():
    """꺼진 둑 등잔: 나룻불 장대 끝에 달렸던 종이 등. 종이가 찢어졌고 안은 새까맣다."""
    p = [cyl("pole", 0.045, 0.035, 1.25, (0, 0, 0), WOOD_D, 6), box("arm", (0.55, 0.05, 0.05), (0.26, 0, 1.22), WOOD_D), limb("hook", (0.5, 0, 1.2), (0.5, 0, 1.08), 0.012, 0.012, IRON, 4)]
    p.append(lathe("paper", [(0.0, 0.12), (0.08, 0.17), (0.2, 0.18), (0.3, 0.13), (0.34, 0.07)], 8, "#CFC7AE", loc=(0.5, 0, 0.76), skip=lambda i, k: (i == 2 and k in (1, 2))))
    p += [cyl("inside", 0.1, 0.1, 0.2, (0.5, 0, 0.8), CHAR, 6), cyl("ring_t", 0.08, 0.08, 0.02, (0.5, 0, 1.1), IRON, 8), cyl("ring_b", 0.07, 0.07, 0.02, (0.5, 0, 0.76), IRON, 8)]
    p += [box("scrap", (0.05, 0.005, 0.14), (0.62, 0.02, 0.62), "#CFC7AE", (0.2, 0, 0.5))]   # 떨어져 나간 종이 조각
    return p
def keep_oar():
    """부러진 노 손잡이: 갯벌에 꽂힌 노의 윗동. 끝이 쪼개졌고 줄이 감겨 있다."""
    p = [limb("shaft", (0, 0, 0), (0.16, 0.04, 1.05), 0.06, 0.045, WOOD, 7), cyl("grip", 0.062, 0.062, 0.22, (0.1, 0.025, 0.55), "#B89A55", 7, (0, -0.15, 0))]
    for i in range(4):
        a = i * 1.6; p.append(limb(f"split{i}", (0.16, 0.04, 1.02), (0.16 + math.cos(a) * 0.07, 0.04 + math.sin(a) * 0.07, 1.16 + 0.03 * i), 0.02, 0.0, "#B8A468", 4))
    p += [sphere(f"mud{i}", 0.12, (math.cos(i * 2.1) * 0.16, math.sin(i * 2.1) * 0.16, 0.03), "#5C4A33", 6, 3, (1, 1, 0.35)) for i in range(3)]
    return p
def keep_bundle():
    """젖은 비단 보따리: 남색 비단을 묶은 보따리, 매듭 끝에서 물이 떨어지고 바닥에 물웅덩이."""
    p = [disc("puddle", 0.4, 0.0, "#2A3A5A", 0.012, 12, 0.7), sphere("bag", 0.27, (0, 0, 0.2), INDIGO, 9, 5, (1.1, 1, 0.8)), sphere("bag2", 0.2, (0.08, 0.02, 0.3), "#3A5CA8", 8, 4)]
    p += [limb("ear1", (0, 0, 0.45), (-0.12, 0.05, 0.62), 0.05, 0.02, INDIGO, 5), limb("ear2", (0, 0, 0.45), (0.14, -0.04, 0.6), 0.05, 0.02, "#3A5CA8", 5), sphere("knot", 0.06, (0, 0, 0.46), "#2A3F78", 6, 3)]
    p += [sphere(f"drip{i}", 0.02, (0.2 + i * 0.05, -0.1 + i * 0.04, 0.1 + i * 0.08), "#5A7CC0", 4, 3, (1, 1, 1.5)) for i in range(3)]
    return p
def keep_ash():
    """재(파혼 뒤): 유품이 재가 되어 남은 자리. 같은 자리·같은 크기, 회색 재 더미와 흩어진 부스러기. F 안내 없이 보기만."""
    r = random.Random(77); p = [sphere("heap", 0.32, (0, 0, 0.02), ASH, 8, 3, (1.1, 1, 0.22)), sphere("heap2", 0.18, (0.12, 0.05, 0.05), "#7A746A", 6, 3, (1, 1, 0.3))]
    for i in range(10):
        a = r.random() * TAU; d = 0.25 + r.random() * 0.3
        p.append(box(f"bit{i}", (0.05, 0.03, 0.01), (math.cos(a) * d, math.sin(a) * d, 0.01), [ASH, "#4A463E", "#8A847A"][i % 3], (0, 0, r.random() * TAU)))
    return p

# ───────── 단서 물건 ─────────
def gut_table():
    """굿상(폐당집): 잔 열두 개가 놓였던 자리. 열한 개는 서 있고 열두째 하나만 엎어져 있다."""
    p = [box("top", (1.5, 0.8, 0.07), (0, 0, 0.74), WOOD), box("cloth", (1.1, 0.6, 0.012), (0, 0, 0.785), "#B33A3A")]
    p += [box(f"leg{i}", (0.07, 0.07, 0.72), (sx * 0.68, sy * 0.33, 0.36), WOOD_D) for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)])]
    for i in range(12):
        x = -0.5 + (i % 6) * 0.2; y = -0.12 + (i // 6) * 0.24
        if i == 11: p.append(cyl("cup_down", 0.045, 0.07, 0.07, (x, y, 0.79), PORC, 8, (math.pi, 0, 0))); p[-1].location.z += 0.07   # 엎어진 열두째 잔
        else: p.append(cyl(f"cup{i}", 0.04, 0.06, 0.07, (x, y, 0.79), PORC, 8))
    p += [cyl("burner", 0.07, 0.05, 0.08, (0.62, 0.0, 0.79), IRON, 8), cyl("candle_l", 0.025, 0.025, 0.2, (-0.68, 0.28, 0.79), "#EDE8D0", 5), cyl("candle_r", 0.025, 0.025, 0.2, (-0.68, -0.28, 0.79), "#EDE8D0", 5)]
    return p
def burnt_docbox():
    """탄 문서함(동헌 터): 새까맣게 그을린 문서함. 뚜껑이 열려 있고 타다 만 종이 끝이 삐져나왔다. 그은 줄 끝에 한 줄만 반듯하다."""
    p = [box("body", (0.9, 0.55, 0.5), (0, 0, 0.25), CHAR), box("rim", (0.94, 0.59, 0.05), (0, 0, 0.5), "#1A1612"), box("lid", (0.9, 0.5, 0.05), (0, 0.4, 0.55), "#1A1612", (math.radians(-100), 0, 0)),
         box("lock", (0.1, 0.03, 0.12), (0, -0.28, 0.4), IRON), box("band1", (0.05, 0.57, 0.52), (-0.3, 0, 0.25), IRON), box("band2", (0.05, 0.57, 0.52), (0.3, 0, 0.25), IRON)]
    r = random.Random(81)
    for i in range(7):
        p.append(box(f"paper{i}", (0.42, 0.3, 0.008), (r.uniform(-0.15, 0.15), r.uniform(-0.1, 0.1), 0.52 + i * 0.012), ["#CFC4A6", "#B8AE92", "#8A8068"][i % 3], (0, 0, r.uniform(-0.4, 0.4))))
    p.append(box("straight_line", (0.3, 0.012, 0.004), (0.03, 0.0, 0.62), "#2A2A38"))   # 반듯한 한 줄
    p += [sphere(f"cinder{i}", 0.09, (r.uniform(-0.6, 0.6), r.uniform(-0.5, 0.5), 0.01), "#3A342C", 5, 3, (1, 1, 0.12)) for i in range(5)]
    return p

# ───────── 줍기 ─────────
def coin_bundle():
    """엽전 꾸러미: 짚끈에 꿴 엽전 한 줄(엽전 열 닢)을 둘둘 말아 매듭지은 것. 엽전은 가운데 네모 구멍."""
    p = [cyl("rope_ring", 0.13, 0.13, 0.02, (0, 0, 0.0), "#C9B764", 10)]
    for i in range(9):
        a = i * 0.7; p.append(cyl(f"coin{i}", 0.07, 0.07, 0.014, (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.02 + i * 0.016), "#B8A468" if i % 2 else "#8A7A4A", 10))
        p.append(box(f"hole{i}", (0.026, 0.026, 0.004), (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.036 + i * 0.016), CHAR))
    p += [limb("tail1", (0.0, 0.0, 0.17), (0.18, 0.04, 0.06), 0.012, 0.008, "#C9B764", 4), limb("tail2", (0.0, 0.0, 0.17), (-0.12, 0.1, 0.05), 0.012, 0.008, "#C9B764", 4), sphere("knot", 0.03, (0, 0, 0.17), "#B89A55", 5, 3)]
    return p
def herb_mugwort():
    """쑥 한 포기: 은빛 도는 초록 잎이 방사형으로 갈라져 올라온다(쑥 잎 끝이 뾰족하게 갈라진 모양을 길쭉한 잎 두 겹으로)."""
    r = random.Random(91); p = []
    for i in range(11):
        a = i / 11 * TAU + r.random() * 0.3; h = 0.26 + r.random() * 0.2; d = 0.04 + r.random() * 0.03
        tip = (math.cos(a) * (d + 0.17), math.sin(a) * (d + 0.17), h)
        p.append(limb(f"leaf{i}", (math.cos(a) * d, math.sin(a) * d, 0.02), tip, 0.045, 0.0, ["#9DB89A", "#7C9A78", "#B4C8AE"][i % 3], 3))
        mid = (tip[0] * 0.55, tip[1] * 0.55, h * 0.7); p.append(limb(f"lobe{i}", mid, (mid[0] + math.cos(a + 1.1) * 0.08, mid[1] + math.sin(a + 1.1) * 0.08, mid[2] + 0.05), 0.03, 0.0, "#8AA888", 3))
    p.append(cyl("crown", 0.04, 0.03, 0.06, (0, 0, 0), "#7A8A5A", 5))
    return p

# ───────── 빛기둥(줍기 표시) ─────────
def pillar(col):
    """바닥 빛기둥: 높이 2m 투명 원기둥 + 바닥 빛 고리. 등급 색은 코드가 재질 색만 바꿔도 되게 단색 하나로."""
    return [cyl("beam", 0.16, 0.05, 2.0, (0, 0, 0.02), mat_alpha(col, 0.28, 1.6), 8), cyl("beam_core", 0.05, 0.02, 1.9, (0, 0, 0.02), mat_alpha(col, 0.5, 2.4), 6), disc("ring", 0.3, 0.0, col, 0.015, 14, 0.6, 1.8)]

# ───────── 서낭당 쉬기 자리 ─────────
def seonang_rest():
    """서낭당 쉬는 자리(반경 3m 원): 돌 두른 다짐 마당, 납작한 돌 의자 둘 + 짚방석, 쑥 달이는 작은 화로(약탕관), 소원 헝겊 말뚝 셋.
    서낭당 건물(prop_seonangdang)은 따로 두고 이 소품을 그 앞마당 가운데 놓는다. 중심=화로. 따뜻한 불빛 하나(Light_seonang_rest)."""
    r = random.Random(101); p = [disc("floor", 2.7, 0.0, "#A08B62", 0.03, 24)]
    for i in range(18):   # 가장자리 돌 두름(몇 개는 빠뜨려 손길이 닿은 느낌)
        if i in (4, 11): continue
        a = i / 18 * TAU; rr = 0.2 + r.random() * 0.1
        p.append(sphere(f"edge{i}", rr, (math.cos(a) * 2.85, math.sin(a) * 2.85, 0.08), ["#86816F", "#9C9684", "#706A5A"][i % 3], 6, 3, (1.2, 1, 0.55), (0, 0, r.random() * TAU)))
    for k, (x, y, rot) in enumerate([(-1.45, -0.55, 0.3), (1.35, 0.9, 2.9)]):   # 돌 의자 + 짚방석
        p += [box(f"seat{k}", (1.3, 0.5, 0.3), (x, y, 0.15), "stone", (0, 0, rot)), box(f"seat_top{k}", (1.36, 0.54, 0.05), (x, y, 0.32), "stone_dark", (0, 0, rot)), cyl(f"mat{k}", 0.3, 0.3, 0.05, (x, y, 0.34), "#C9B764", 9)]
    # 화로: 돌 둘레 + 숯불 + 삼발이 + 약탕관(쑥 달이는 단지)
    p.append(cyl("hearth", 0.5, 0.45, 0.22, (0, 0, 0.0), "stone_dark", 9)); p.append(cyl("ember_bed", 0.34, 0.3, 0.02, (0, 0, 0.22), "#2A2420", 9))
    p.append(cyl("ember", 0.26, 0.2, 0.03, (0, 0, 0.235), mat("#FFB066", 3.0), 8))
    for i in range(3):
        a = i / 3 * TAU + 0.5; p.append(limb(f"tripod{i}", (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.22), (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.62), 0.025, 0.02, IRON, 4))
    p.append(lathe("kettle", [(0.0, 0.14), (0.06, 0.2), (0.2, 0.22), (0.3, 0.16), (0.34, 0.1)], 9, "#3A2E28", loc=(0, 0, 0.6)))
    p += [cyl("lid", 0.1, 0.1, 0.03, (0, 0, 0.94), "#2A2420", 8), sphere("lid_knob", 0.03, (0, 0, 0.98), IRON, 4, 3), limb("spout", (0.18, 0, 0.78), (0.34, 0, 0.88), 0.03, 0.02, "#3A2E28", 5)]
    p += [sphere(f"steam{i}", 0.07 + i * 0.03, (0.36 + i * 0.04, 0.0, 0.95 + i * 0.16), mat_alpha("#E8EEF0", 0.28 - i * 0.07), 5, 3) for i in range(3)]
    # 소원 헝겊 말뚝 셋(오방색 헝겊: 청·황·백) — 서낭당 금줄 기둥 대신 바닥 말뚝
    for k, (x, y, col) in enumerate([(2.2, -1.2, "#3E64B0"), (-2.0, 1.4, "#E8C15A"), (0.4, 2.45, "#EDE8D0")]):
        p += [limb(f"stake{k}", (x, y, 0.0), (x + 0.04, y, 1.5), 0.04, 0.03, WOOD_D, 5), box(f"cloth{k}", (0.45, 0.02, 0.1), (x + 0.28, y, 1.4), col, (0, 0, 0.1)), box(f"cloth{k}b", (0.35, 0.02, 0.09), (x + 0.22, y, 1.22), col, (0.1, 0, -0.05))]
    return p, [("Light_seonang_rest", (0, 0, 0.5), "#FFB066", 0.8, 6.5, True)]

# ───────── 짜 맞추기 ─────────
def glow_for(main, parts_fn):
    g = join("Glow", parts_fn()); g.parent = main; return g
def keep_glow(): return [disc("g_disc", 0.45, 0.01, "#C9B0FF", 0.01, 12, 0.18, 1.2), sphere("g_orb", 0.1, (0, 0, 0.62), mat_alpha("#C9B0FF", 0.22, 1.6), 6, 4), sphere("g_orb2", 0.06, (0.2, 0.05, 0.45), mat_alpha("#C9B0FF", 0.22, 1.6), 5, 3)]
def clue_glow(): return [disc("g_disc", 0.6, 0.01, "#D4A94E", 0.01, 12, 0.18, 1.2), sphere("g_orb", 0.12, (0, 0, 1.0), mat_alpha("#D4A94E", 0.22, 1.6), 6, 4)]

KIT = [("keep_tongs", keep_tongs, "keep"), ("keep_bowl", keep_bowl, "keep"), ("keep_steamer", keep_steamer, "keep"), ("keep_lamp", keep_lamp, "keep"), ("keep_oar", keep_oar, "keep"), ("keep_bundle", keep_bundle, "keep"), ("keep_ash", keep_ash, None),
       ("gut_table", gut_table, "clue"), ("burnt_docbox", burnt_docbox, "clue"), ("coin_bundle", coin_bundle, None), ("herb_mugwort", herb_mugwort, None)]
PILLARS = {"white": "#F3E7D3", "green": "#8FE0A8", "gold": "#D4A94E", "violet": "#C9B0FF"}

def make(key):
    if key == "seonang_rest":
        parts, lights = seonang_rest(); o = join("prop_seonang_rest", parts); [light_empty(o, n, pos, c, i, r, f) for n, pos, c, i, r, f in lights]; return o
    for k, fn, glow in KIT:
        if k == key:
            o = join(f"prop_{k}", fn())
            if glow: glow_for(o, keep_glow if glow == "keep" else clue_glow)
            return o
    if key.startswith("fx_pickup_pillar_"): return join(key, pillar(PILLARS[key.rsplit("_", 1)[1]]))

def run():
    rep = []; keys = [k for k, _, _ in KIT] + ["seonang_rest"]
    names = [("props", f"prop_{k}", k) for k in keys] + [("fx", f"fx_pickup_pillar_{c}", f"fx_pickup_pillar_{c}") for c in PILLARS]
    for sub, name, key in names:
        reset(); o = make(key); lo, hi = bounds(o)
        extra = [c.name for c in o.children]
        rep.append({"name": name, "dir": sub, "tris": tris(o) + sum(tris(c) for c in o.children if c.type == "MESH"), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "children": extra})
        export(o, os.path.join(OUT, sub, name + ".glb"))
    json.dump(rep, open(os.path.join(OUT, "props", "_report_interact.json"), "w"), ensure_ascii=False, indent=1)
    # 미리보기: 낮 50°. 위 줄=유품 7, 가운데=단서·줍기, 아래=빛기둥 4 + 서낭당 쉬기(큼)
    reset(); cols = 7; i = 0
    for k, fn, glow in KIT:
        o = join(f"prop_{k}", fn())
        if glow: glow_for(o, keep_glow if glow == "keep" else clue_glow)
        o.location = ((i % cols - 3) * 2.2, -(i // cols) * 2.4 + 2.2, 0); i += 1
    for j, c in enumerate(PILLARS):
        o = join(f"pl{j}", pillar(PILLARS[c])); o.location = ((j - 1.5) * 2.0 - 4.2, -4.6, 0)
    parts, lights = seonang_rest(); o = join("rest", parts); o.location = (4.0, -7.4, 0)
    setup_render(17, (0, -3.2, 0.3), size=(1600, 1000), ground_size=40)
    render(os.path.join(OUT, "previews", "interactables_50deg.png"))
    return rep

if __name__ == "__main__":
    rep = run(); print(len(rep), "종", [(r["name"], r["tris"]) for r in rep])
