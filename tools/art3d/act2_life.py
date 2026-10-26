"""2막 ③ 붉은재 아랫마을 · ④ 쇳골 광부촌 · 들판 생활 소품 24종.
왜 이렇게: 2막 배치표(act2_layout.json, 소품 422개)를 보면 아랫마을에는 집이 한 채도 없고(술독·땔감·울타리뿐), 광부촌엔 움막 일곱, 들판은 거의 비었다. 
 지도(act2_map.json)에는 술도가·이장 집·약초 아낙 집·벌초꾼 집·사당·석수 일터, 국밥집·순돌 집·노새 마구간·광산 주인집이 '자리'로만 있어서 그 자리에 설 집과 생활 소품을 만든다.
색 뼈대(act2_kit.py와 같음): 붉은재=붉은 흙 #9A5A3E·젖은 성돌 #7E7E78·낡은 붉은 깃 / 쇳골=쇠찌꺼기 #2E2C30·녹슨 광석 #6A3A2A·누런 흙 #A8864E. 불빛은 따뜻한 등불(주황은 파혼 전용이라 쓰지 않음).
접두: a2v_=아랫마을 · a2m_=광부촌 · a2f_=들판. 규약은 act2_kit과 같다(1유닛=1m, 원점=바닥 한가운데, 정면=-Y, 문은 -Y). 출력 assets3d/act2/.
실행: python3 act2_life.py → assets3d/act2/a2*_*.glb, _report_act2_life.json, previews/act2_life_50deg.png"""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); TAU = math.tau
STONE, STONE_D, RED_SOIL, LOAM, SLAG, ORE, RUST = "#77746A", "#585650", "#9A5A3E", "#A8864E", "#2E2C30", "#6A3A2A", "#7A4A30"
WARM = "#FFB066"; DRY = "#A8955A"; DRY_D = "#7E6E3E"

def hut(w, d, h, wall, roof, stones=False, door_x=0.0, tag=""):
    """초가/널집 공통 몸체: 기단 + 벽 + 지붕(얹은 돌) + 문 + 창. 문은 -Y."""
    p = [box(f"base{tag}", (w + 0.4, d + 0.4, 0.25), (0, 0, 0.125), STONE_D), box(f"wall{tag}", (w, d, h), (0, 0, 0.25 + h / 2), wall),
         prism(f"roof{tag}", w + 1.2, d + 1.0, 1.1, (0, 0, 0.25 + h), roof), box(f"door{tag}", (0.8, 0.08, 1.6), (door_x, -d / 2 - 0.01, 1.05), "wood_dark"), box(f"win{tag}", (0.6, 0.08, 0.5), (-w / 2 + 0.8, -d / 2 - 0.01, 1.7), "wood_dark"),
         box(f"step{tag}", (1.2, 0.5, 0.15), (door_x, -d / 2 - 0.4, 0.075), STONE)]
    if stones:   # 바람에 날리지 않게 얹은 돌들
        r = random.Random(3); p += [sphere(f"rf{tag}{i}", 0.17, (r.uniform(-w / 2, w / 2), r.uniform(-d / 2, d / 2) * 0.8, 0.25 + h + 0.7 + r.uniform(0, 0.25)), STONE, 5, 3, (1, 1, 0.6)) for i in range(7)]
    return p

# ───────── ③ 붉은재 아랫마을 ─────────
def house_sul():
    """술도가 집: 큰 초가(5×3.6m) + 처마 밑 누룩 말림 시렁 + 앞마당 술독 둘. 지붕에 돌."""
    p = hut(5.0, 3.6, 2.2, RED_SOIL, "thatch", True, 1.2)
    p += [limb("rackL", (-2.0, -2.5, 0), (-2.0, -2.5, 1.7), 0.05, 0.04, "wood", 4), limb("rackR", (0.2, -2.5, 0), (0.2, -2.5, 1.7), 0.05, 0.04, "wood", 4), limb("rackBar", (-2.0, -2.5, 1.65), (0.2, -2.5, 1.65), 0.04, 0.04, "wood", 4)]
    p += [box(f"nuruk{i}", (0.22, 0.22, 0.2), (-1.8 + i * 0.4, -2.5, 1.45), "#C9B38A") for i in range(5)] + [lathe(f"jar{i}", [(0, 0.2), (0.2, 0.34), (0.45, 0.4), (0.7, 0.3), (0.8, 0.22)], 8, "jar", loc=(2.3 + i * 0.9, -2.3, 0)) for i in range(2)]
    return p
def house_small():
    """붉은 흙벽 초가(4×3m): 지붕에 돌을 얹었다. 이장 집·벌초꾼 집·순돌 집처럼 평범한 집."""
    return hut(4.0, 3.0, 2.0, RED_SOIL, "thatch", True, 0.6) + [box("firewood", (0.9, 0.4, 0.5), (1.6, -1.9, 0.3), "wood"), box("jar", (0.3, 0.3, 0.45), (-1.7, -1.9, 0.25), "jar")]
def house_herb():
    """약초 집(3.6×3m): 처마 밑에 약초 묶음이 거꾸로 매달리고 마당에 약초 멍석."""
    p = hut(3.6, 3.0, 2.0, "#B08A5C", "thatch", False, 0.4)
    p += [limb("bar", (-1.8, -1.8, 1.9), (1.2, -1.8, 1.9), 0.03, 0.03, "wood", 4)] + [cone for i in range(7) for cone in (limb(f"herb{i}", (-1.6 + i * 0.4, -1.8, 1.9), (-1.6 + i * 0.4, -1.8, 1.45), 0.04, 0.09, "#6F8A4A" if i % 2 else "#8A8A4A", 4),)]
    p += [box("mat", (1.2, 0.9, 0.04), (-1.2, -2.7, 0.03), "#C9B764")] + [sphere(f"leaf{i}", 0.1, (-1.5 + (i % 3) * 0.3, -2.9 + (i // 3) * 0.3, 0.08), "#5F7A3A", 4, 3, (1.2, 1, 0.4)) for i in range(6)]
    return p
def stone_cutter():
    """석수 일터: 반쯤 다듬은 성돌 셋, 작업 받침, 정·망치, 돌 부스러기 무더기. 4×3m."""
    r = random.Random(5); p = [box("cut1", (1.2, 0.8, 0.8), (-1.0, 0, 0.4), STONE), box("cut2", (1.0, 0.7, 0.55), (0.5, 0.3, 0.28), "#6E706C"), box("cut3", (1.5, 0.9, 0.4), (-0.2, -1.0, 0.2), STONE_D, rot=(0, 0, 0.2)), box("rough", (0.9, 0.9, 1.0), (1.6, -0.5, 0.5), STONE_D, rot=(0, 0, 0.5))]
    p += [box("chisel", (0.05, 0.05, 0.3), (-0.4, -0.5, 0.82), "#3A3A44", rot=(0.3, 0, 0)), box("mallet_h", (0.04, 0.04, 0.35), (-0.55, -0.5, 0.78), "wood", rot=(0, 1.2, 0)), box("mallet_head", (0.14, 0.08, 0.08), (-0.38, -0.5, 0.8), "#4A4A52")]
    p += [sphere(f"chip{i}", r.uniform(0.04, 0.1), (r.uniform(-1.6, 1.0), r.uniform(-1.6, 0.4), 0.04), STONE, 4, 3, (1, 1, 0.5)) for i in range(18)] + [limb("sled", (1.0, 0.2, 0.0), (2.4, 0.6, 0.1), 0.05, 0.05, "wood_dark", 4)]
    return p
def persimmon_line():
    """감 말림 줄: 기둥 둘 사이 줄에 곶감 꼬치가 열두 개. 붉은재의 가을 표시. 폭 3m, 높이 2m."""
    p = [limb("pL", (-1.5, 0, 0), (-1.5, 0, 2.0), 0.05, 0.04, "wood_dark", 4), limb("pR", (1.5, 0, 0), (1.5, 0, 2.0), 0.05, 0.04, "wood_dark", 4), limb("bar", (-1.5, 0, 1.95), (1.5, 0, 1.95), 0.03, 0.03, "wood", 4)]
    for i in range(12):
        x = -1.35 + i * 0.245; p += [limb(f"s{i}", (x, 0, 1.95), (x, 0, 1.3), 0.008, 0.008, "thatch", 3)] + [sphere(f"k{i}{j}", 0.06, (x, 0, 1.75 - j * 0.14), "#B5532A", 5, 3, (1, 1, 0.9)) for j in range(3)]
    return p
def red_wall_low():
    """붉은 흙 낮은 돌담: 돌 + 붉은 흙 사이, 위에 기와 쪽 대신 풀. 길이 4m, 높이 1m."""
    r = random.Random(9); p = []
    for row in range(3):
        x = -2.0 + (0.3 if row % 2 else 0)
        while x < 1.8:
            bw = r.uniform(0.5, 0.8); p.append(box(f"b{row}_{len(p)}", (bw * 0.95, 0.5, 0.32), (x + bw / 2, r.uniform(-0.03, 0.03), 0.16 + row * 0.32), r.choice([STONE, STONE_D, RED_SOIL]))); x += bw
    p += [box("top_grass", (4.0, 0.3, 0.08), (0, 0, 1.0), DRY)]
    return p

# ───────── ④ 쇳골 광부촌 ─────────
def soup_house():
    """국밥집: 널집 한쪽을 터서 큰 솥을 건 가게 + 평상 둘 + 등 한 줄. 5×3.2m."""
    p = hut(4.2, 2.8, 2.0, "#7A5A3A", "thatch", False, 1.0, "a") + [box("bench1", (1.6, 0.5, 0.45), (-1.0, -2.3, 0.25), "wood"), box("bench2", (1.6, 0.5, 0.45), (1.2, -2.5, 0.25), "wood", rot=(0, 0, 0.2))]
    p += [lathe("cauldron", [(0, 0.0), (0.05, 0.2), (0.35, 0.35), (0.5, 0.32), (0.52, 0.3)], 9, "#2E2A2A", loc=(-1.9, -1.6, 0.4)), cyl("hearth", 0.5, 0.5, 0.4, (-1.9, -1.6, 0.0), STONE_D, 8), box("lantern", (0.2, 0.2, 0.28), (0.0, -1.6, 2.0), mat(WARM, 2.0)), limb("lantern_cord", (0, -1.6, 2.4), (0, -1.6, 2.15), 0.01, 0.01, "thatch", 3)]
    return p
def mule():
    """노새: 선 채로 고개를 숙인 갈색 짐승. 몸 1.6m, 높이 1.4m. 등에 짐 자루 한 쌍."""
    p = [box("body", (0.5, 1.3, 0.55), (0, 0, 0.95), "#6A5040"), box("neck", (0.2, 0.4, 0.5), (0, -0.7, 1.1), "#6A5040", rot=(0.5, 0, 0)), box("head", (0.2, 0.45, 0.22), (0, -1.0, 0.95), "#5A4030", rot=(0.4, 0, 0)), box("ear_l", (0.05, 0.05, 0.22), (-0.07, -0.9, 1.25), "#5A4030"), box("ear_r", (0.05, 0.05, 0.22), (0.07, -0.9, 1.25), "#5A4030"), limb("tail", (0, 0.65, 1.1), (0, 0.8, 0.5), 0.04, 0.02, "#3A2A20", 3)]
    p += [limb(f"leg{i}", (sx * 0.17, sy * 0.45, 0.7), (sx * 0.17, sy * 0.45, 0.0), 0.06, 0.04, "#5A4030", 4) for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1)))] + [box("sack_l", (0.28, 0.5, 0.4), (-0.38, 0.0, 1.2), "#9C8858"), box("sack_r", (0.28, 0.5, 0.4), (0.38, 0.0, 1.2), "#9C8858")]
    return p
def stable():
    """노새 마구간: 한쪽 지붕 헛간 + 구유 + 짚 + 말뚝(노새는 따로). 4×3m."""
    p = [limb(f"post{i}", (x, y, 0), (x, y, 2.0 if y < 0 else 1.6), 0.07, 0.06, "wood_dark", 5) for i, (x, y) in enumerate(((-2, -1.4), (2, -1.4), (-2, 1.4), (2, 1.4)))]
    p += [box("roof", (4.6, 3.6, 0.14), (0, 0, 1.95), "thatch", rot=(0.18, 0, 0)), box("back", (4.0, 0.12, 1.5), (0, 1.45, 0.85), "wood_dark"), box("trough", (1.4, 0.4, 0.3), (0.0, 0.9, 0.3), "wood"), box("hay", (1.6, 1.0, 0.18), (-0.2, 0.3, 0.09), "#C9B764"), box("rail", (3.8, 0.08, 0.08), (0, -1.4, 0.9), "wood")]
    p += [sphere(f"hay{i}", 0.2, (-1.5 + i * 0.7, 1.1, 0.2), "#C9B764", 5, 3, (1.4, 1, 0.8)) for i in range(3)]
    return p
def owner_house():
    """광산 주인집(작은 기와 사랑채 6×4m): 기와 지붕·붉은 기둥·댓돌, 앞에 낮은 담 한쪽. 쇳골에서 유일한 기와."""
    p = [box("gidan", (6.4, 4.6, 0.5), (0, 0, 0.25), STONE), box("wall", (5.6, 3.6, 2.2), (0, 0, 1.6), "hanji")]
    p += [limb(f"pil{i}", (x, -1.85, 0.5), (x, -1.85, 2.8), 0.11, 0.1, "pillar", 6) for i, x in enumerate((-2.8, -0.95, 0.95, 2.8))] + [box("beam", (6.0, 0.25, 0.25), (0, -1.85, 2.9), "pillar"), box("door", (1.6, 0.08, 1.7), (0, -1.82, 1.45), "wood_dark"), prism("roof", 7.6, 5.8, 1.5, (0, 0, 2.9), "tile")]
    p += [box("step", (2.0, 0.6, 0.3), (0, -2.8, 0.15), STONE_D), box("fence", (3.0, 0.2, 1.1), (-2.8, -4.2, 0.55), STONE_D)] + [box(f"coalmark{i}", (0.3, 0.02, 0.2), (-1.2 + i * 0.8, -2.34, 0.5 + 0.25 * (i % 2)), SLAG) for i in range(4)]
    return p
def coal_stack():
    """집 앞 땔 석탄 더미 + 삼태기. 반경 0.9m, 높이 0.8m. 검은 가루가 바닥에 번져 있음."""
    r = random.Random(12); p = [disc_("dust", 1.1, SLAG)]
    p += [sphere(f"c{i}", r.uniform(0.12, 0.22), (r.uniform(-0.5, 0.5), r.uniform(-0.5, 0.5), r.uniform(0.1, 0.5) * (1 - 0.0)), SLAG if i % 3 else "#3E3C42", 5, 3, (1, 1, 0.8)) for i in range(16)] + [box("basket", (0.5, 0.35, 0.25), (0.8, -0.5, 0.13), "#9A8450", rot=(0, 0, 0.3))]
    return p
def disc_(name, r, col, h=0.02): return cyl(name, r, r, h, (0, 0, 0), col, 10)
def dusty_clothes():
    """검은 먼지 묻은 빨래줄: 줄 하나에 잿빛으로 물든 옷 다섯. 폭 3m, 높이 1.8m."""
    p = [limb("pL", (-1.5, 0, 0), (-1.5, 0, 1.8), 0.05, 0.04, "wood_dark", 4), limb("pR", (1.5, 0, 0), (1.5, 0, 1.75), 0.05, 0.04, "wood_dark", 4)]
    pts = [(-1.5 + 3.0 * i / 6, 0, 1.75 - 0.14 * math.sin(math.pi * i / 6)) for i in range(7)]
    p += [limb(f"l{i}", pts[i], pts[i + 1], 0.012, 0.012, "thatch", 3) for i in range(6)]
    for i, c in zip(range(1, 6), ("#8A8478", "#6E6A62", "#9A9486", "#5E5A54", "#8A8478")): x, _, z = pts[i]; p.append(box(f"cl{i}", (0.34, 0.03, 0.8 - 0.06 * (i % 3)), (x, 0, z - 0.45), c, rot=(0, 0, 0.05 * i)))
    return p
def pick_rack():
    """곡괭이 걸이: 말뚝 틀에 곡괭이 셋·삽 하나·등불 모자 둘이 걸림. 폭 2m, 높이 1.8m."""
    p = [limb("pL", (-1.0, 0, 0), (-1.0, 0, 1.8), 0.06, 0.05, "wood_dark", 5), limb("pR", (1.0, 0, 0), (1.0, 0, 1.8), 0.06, 0.05, "wood_dark", 5), limb("bar", (-1.05, 0, 1.6), (1.05, 0, 1.6), 0.04, 0.04, "wood", 4)]
    for i in range(3): x = -0.6 + i * 0.5; p += [limb(f"h{i}", (x, 0.03, 1.55), (x, 0.03, 0.7), 0.025, 0.025, "wood", 4), box(f"head{i}", (0.5, 0.05, 0.07), (x, 0.03, 1.55), "#3A3A44", rot=(0, 0.2, 0))]
    p += [limb("shaft", (0.9, 0.03, 1.55), (0.9, 0.03, 0.6), 0.025, 0.025, "wood", 4), box("spade", (0.2, 0.03, 0.28), (0.9, 0.03, 0.5), "#3A3A44")] + [cyl(f"cap{i}", 0.13, 0.13, 0.08, (-0.9 + i * 1.8, -0.1, 1.3), "#6A5A3A", 6) for i in range(2)]
    return p
def water_barrel():
    """물통 둘과 바가지: 광부가 씻는 물. 통 지름 0.7m. 물 위에 검은 가루."""
    p = [lathe(f"barrel{i}", [(0, 0.35), (0.12, 0.38), (0.4, 0.36), (0.8, 0.32), (0.9, 0.3)], 10, "wood", loc=(i * 0.9, 0, 0)) for i in range(2)] + [cyl(f"water{i}", 0.3, 0.3, 0.02, (i * 0.9, 0, 0.88), "#2E3A40", 9) for i in range(2)]
    p += [cyl("ladle", 0.1, 0.08, 0.06, (0.4, -0.5, 0.0), "#CDB77A", 6), limb("ladle_h", (0.4, -0.5, 0.05), (0.7, -0.75, 0.05), 0.015, 0.015, "wood", 3)]
    return p
def lamp_string():
    """등 줄: 기둥 둘에 걸린 줄에 종이등 다섯(좁은 길 따라 늘어놓는 광부촌 길잡이). 폭 4m, 높이 2.4m. Light_ 하나."""
    p = [limb("pL", (-2.0, 0, 0), (-2.0, 0, 2.4), 0.05, 0.04, "wood_dark", 4), limb("pR", (2.0, 0, 0), (2.0, 0, 2.4), 0.05, 0.04, "wood_dark", 4)]
    pts = [(-2.0 + 4.0 * i / 8, 0, 2.3 - 0.3 * math.sin(math.pi * i / 8)) for i in range(9)]
    p += [limb(f"l{i}", pts[i], pts[i + 1], 0.012, 0.012, "thatch", 3) for i in range(8)] + [box(f"lamp{i}", (0.2, 0.2, 0.3), (pts[1 + i * 1.5 if False else int(1 + i * 1.5)][0], 0, pts[int(1 + i * 1.5)][2] - 0.25), mat(WARM, 1.8)) for i in range(5)]
    return p

# ───────── 들판 ─────────
def dry_grass():
    """마른 풀 무더기: 누런 풀잎 마흔 가닥. 반경 0.7m, 높이 0.9m."""
    r = random.Random(21); p = []
    for i in range(70): a = r.uniform(0, TAU); d = r.uniform(0, 0.8); h = r.uniform(0.7, 1.4); lean = r.uniform(0.05, 0.35); p.append(limb(f"g{i}", (math.cos(a) * d, math.sin(a) * d, 0), (math.cos(a) * (d + lean), math.sin(a) * (d + lean), h), 0.015, 0.004, DRY if i % 3 else DRY_D, 3))
    return p
def red_rock():
    """붉은 바위: 철분 녹이 번진 둥근 바위 둘. 지름 1.6m, 높이 1.1m."""
    return [sphere("r1", 0.8, (0, 0, 0.38), "#8A5A44", 7, 5, (1, 0.9, 0.7)), sphere("r2", 0.45, (0.7, -0.3, 0.2), "#7A4E3C", 6, 4, (1, 1, 0.7)), sphere("rust", 0.62, (-0.1, 0.1, 0.55), "#A8643E", 6, 4, (1, 0.9, 0.4))]
def thorn_bush():
    """가시덤불: 휘어진 마른 줄기 얽힘. 반경 0.9m, 높이 0.9m. 붉은 열매 몇 알."""
    r = random.Random(33); p = []
    for i in range(14): a = r.uniform(0, TAU); p += [limb(f"t{i}", (0, 0, 0.05), (math.cos(a) * r.uniform(0.5, 0.95), math.sin(a) * r.uniform(0.5, 0.95), r.uniform(0.4, 0.95)), 0.03, 0.01, "#5E4A34", 3)]
    p += [sphere(f"b{i}", 0.04, (r.uniform(-0.6, 0.6), r.uniform(-0.6, 0.6), r.uniform(0.3, 0.8)), "#8A2A2A", 4, 3) for i in range(6)]
    return p
def dead_tree():
    """고사목: 잎 없는 굵은 나무 줄기 + 휜 가지 다섯. 높이 4.5m. 쿼터뷰에서 키 큰 점."""
    p = [limb("trunk", (0, 0, 0), (0.1, 0, 3.0), 0.3, 0.14, "#4A3A30", 6)] + [limb(f"br{i}", (0.1, 0, 2.2 + i * 0.3), (0.1 + math.cos(i * 1.7) * (0.9 + 0.2 * i), math.sin(i * 1.7) * (0.9 + 0.2 * i), 3.3 + i * 0.35), 0.1, 0.02, "#4A3A30", 4) for i in range(5)]
    p.append(limb("top", (0.1, 0, 3.0), (0.25, 0.1, 4.5), 0.12, 0.02, "#4A3A30", 4)); return p
def boundary_stone():
    """경계 돌: 서 있는 긴 돌 하나, 이끼와 붉은 줄 한 줄(밭·땅 경계). 높이 1.2m."""
    return [box("stone", (0.45, 0.3, 1.2), (0, 0, 0.55), STONE, rot=(0.05, 0, 0.1)), box("top", (0.38, 0.25, 0.2), (0.0, 0.0, 1.2), "#6E706C", rot=(0.05, 0, 0.1)), box("mark", (0.4, 0.02, 0.1), (0.0, -0.16, 0.7), "#8A2A2A"), sphere("moss", 0.2, (0.0, 0.0, 0.1), "#58704A", 5, 3, (1.3, 1, 0.5))]
def persimmon_tree():
    """감나무: 굵은 줄기 + 성긴 잎 덩이 + 붉은 감 열둘. 높이 4.5m. 붉은재의 표지."""
    r = random.Random(41); p = [limb("trunk", (0, 0, 0), (0.1, 0, 2.6), 0.28, 0.15, "bark", 6)]
    p += [sphere(f"leaf{i}", 0.8, (math.cos(i * 1.3) * 0.7, math.sin(i * 1.3) * 0.7, 3.4 + (i % 2) * 0.4), "#7A8A3A" if i % 2 else "#5E7A3A", 6, 4, (1, 1, 0.7)) for i in range(5)] + [sphere("leaf_c", 0.9, (0.1, 0, 3.8), "#6E8A3A", 6, 4, (1, 1, 0.7))]
    p += [sphere(f"kam{i}", 0.09, (math.cos(i * 0.52) * 1.2, math.sin(i * 0.52) * 1.2, 3.05 + r.uniform(0, 0.4)), "#C2552A", 5, 4) for i in range(12)]
    return p
def dry_plot():
    """마른 밭 한 뙈기: 두둑 다섯 줄 + 말라붙은 줄기 몇 개. 4×3m."""
    r = random.Random(51); p = [box("soil", (4.0, 3.0, 0.05), (0, 0, 0.025), "#6E5030")]
    p += [box(f"ridge{i}", (3.8, 0.35, 0.18), (0, -1.2 + i * 0.6, 0.12), "#8A6038") for i in range(5)] + [limb(f"stalk{i}", (r.uniform(-1.8, 1.8), -1.2 + (i % 5) * 0.6, 0.2), (r.uniform(-1.8, 1.8), -1.2 + (i % 5) * 0.6, 0.55), 0.012, 0.006, DRY_D, 3) for i in range(14)]
    return p
def cairn_red():
    """붉은 돌탑: 붉은 돌 일곱 단(길 표지). 높이 1.4m."""
    return [sphere(f"s{i}", 0.42 - i * 0.04, (0.02 * (i % 3), -0.02 * (i % 2), 0.2 + i * 0.2), ["#8A5A44", "#77746A", "#9A6044"][i % 3], 6, 4, (1, 1, 0.65)) for i in range(7)]
def ore_vein_rock():
    """광맥 바위: 검은 바위에 녹슨 광석 줄이 번뜩이는 큰 돌. 지름 2m, 높이 1.5m. 쇳골 들판 표지."""
    return [sphere("rock", 1.0, (0, 0, 0.55), "#3E3C42", 7, 5, (1, 0.9, 0.7)), box("vein1", (1.4, 0.04, 0.1), (0, -0.82, 0.7), RUST, rot=(0, 0.3, 0)), box("vein2", (0.9, 0.04, 0.08), (0.2, -0.85, 0.4), "#A8643E", rot=(0, -0.2, 0)), sphere("ore", 0.3, (0.7, -0.5, 0.2), ORE, 5, 4, (1, 1, 0.7))]

LIST = [("a2v_house_sul", house_sul, "술도가 집"), ("a2v_house_small", house_small, "붉은 흙벽 초가"), ("a2v_house_herb", house_herb, "약초 집"), ("a2v_stone_cutter", stone_cutter, "석수 일터"), ("a2v_persimmon_line", persimmon_line, "곶감 줄"), ("a2v_red_wall_low", red_wall_low, "붉은 낮은 담"),
        ("a2m_soup_house", soup_house, "국밥집"), ("a2m_mule", mule, "노새"), ("a2m_stable", stable, "마구간"), ("a2m_owner_house", owner_house, "광산 주인집"), ("a2m_coal_stack", coal_stack, "석탄 더미"), ("a2m_dusty_clothes", dusty_clothes, "먼지 빨래줄"), ("a2m_pick_rack", pick_rack, "곡괭이 걸이"), ("a2m_water_barrel", water_barrel, "물통"), ("a2m_lamp_string", lamp_string, "등 줄"),
        ("a2f_dry_grass", dry_grass, "마른 풀"), ("a2f_red_rock", red_rock, "붉은 바위"), ("a2f_thorn_bush", thorn_bush, "가시덤불"), ("a2f_dead_tree", dead_tree, "고사목"), ("a2f_boundary_stone", boundary_stone, "경계 돌"), ("a2f_persimmon_tree", persimmon_tree, "감나무"), ("a2f_dry_plot", dry_plot, "마른 밭"), ("a2f_cairn_red", cairn_red, "붉은 돌탑"), ("a2f_ore_vein_rock", ore_vein_rock, "광맥 바위")]
LIGHTS = {"a2m_soup_house": [("Light_soup_lamp", (0.0, -1.6, 2.0), WARM, 0.8, 6.0, True)], "a2m_lamp_string": [("Light_lamp_string", (0.0, 0.0, 2.0), WARM, 0.9, 7.0, True)]}

def run():
    rep = []
    for key, fn, nm in LIST:
        reset(); o = join(key, fn()); [light_empty(o, n, pos, c, i, r, f) for n, pos, c, i, r, f in LIGHTS.get(key, [])]
        lo, hi = bounds(o); export(o, os.path.join(OUT, "act2", key + ".glb"))
        rep.append({"name": key, "label": nm, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
    json.dump(rep, open(os.path.join(OUT, "act2", "_report_act2_life.json"), "w"), ensure_ascii=False, indent=1)
    for part, pre in (("a", "a2v_"), ("b", "a2m_"), ("c", "a2f_")):
        reset(); items = [(k, f) for k, f, _ in LIST if k.startswith(pre)]
        for i, (k, f) in enumerate(items): o = join(f"p{i}", f()); o.location = ((i % 5 - 2) * 6.0, 4.0 - (i // 5) * 6.0, 0)
        setup_render(30, (0, -2.0, 0.8), size=(1600, 900), ground_size=60); bpy.context.scene.cycles.samples = 28
        render(os.path.join(OUT, "previews", f"act2_life_{part}_50deg.png"))
    return rep
if __name__ == "__main__":
    for r in run(): print(r["name"], r["tris"], r["size_m"], "min_z", r["min_z"])
