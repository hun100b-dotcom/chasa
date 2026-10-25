"""3막 ⑤ 갯마을 · ⑥ 도성 아랫마을 생활 소품 34종.
왜 이렇게: 3막 배치표(act3_east/west/coast_layout.json)를 구역별로 세어 보니 100m×100m(1만 ㎡)당 소품이 난파 여울 2.2개, 성문 밖 2.2개, 움막촌 5.1개, 포구 7.1개, 소금밭 6.7개로 비어 있었다(저잣거리 14.8·망부석 곶 17.6은 괜찮음).
 그래서 비어 있는 곳에 '사람이 살고 일한 흔적'을 채운다: 포구(생선 말림대·엎어 둔 배·밧줄 말뚝·궤짝·미역 줄·소금 가마니·소금막), 해안·여울(유목·굴 붙은 바위·갯풀·게통발·난파선 뼈대·조개 더미),
 성문 밖 눈밭(눈 덮인 고사목·울타리·버려진 수레·화톳불 통·눈 얹은 돌탑·볏짚단), 움막촌(빨래줄·흙 화덕·독 받침·거적 천막·판자 더미·닭장), 저잣(궤짝·천 시렁·통 둘).
접두: a3h_=포구·소금밭 · a3c_=해안·여울·곶 · a3g_=성문 밖 · a3s_=움막촌·다리 밑 · a3k_=저잣거리. 규약은 act3_kit과 같다(1유닛=1m, 원점=바닥 한가운데, 정면=-Y).
색: 바닷바람에 바랜 나무 #8A8478·소금 흰색 #E6E2D6(따뜻한 흰색, 혼불 청록과 안 겹침)·갯벌 #5E5A50·눈 #E8EAEE. 불빛은 따뜻한 등불색(주황 #E8683A은 파혼 전용이라 안 쓴다).
출력 assets3d/act3/. 실행: python3 act3_life.py → a3*_*.glb, _report_act3_life.json, previews/act3_life_{a..e}_50deg.png"""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
def lathe_rz(name, rings, *a, **k):
    """(반지름, 높이) 순서로 적은 윤곽을 lib3d.lathe 의 (높이, 반지름) 순서로 바꿔 부른다 — 옹기·통을 눈으로 그리기 쉽게."""
    return lathe(name, [(z, r) for r, z in rings], *a, **k)
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); TAU = math.tau
SEA, SEA_D, SALT, MUD, TAR, THATCH, ROCK, ROCK_D, WARM = "#8A8478", "#6A645A", "#E6E2D6", "#5E5A50", "#3A3632", "#B4A66A", "#6E6A62", "#58554F", "#FFB066"
SNOW, CITY, CITY_D, MAT, CLOTH, ROPE = "#E8EAEE", "#8E8A80", "#6E6A62", "#9A8A64", "#B8AE96", "#A89868"

# ───────── 포구·소금밭 (a3h_) ─────────
def fish_rack():
    """생선 말림대 4×1.2m, 높이 1.8m: 기둥 넷에 가로대 두 단, 갈라 말린 생선이 줄줄이 걸렸다. 포구 마당의 표지."""
    r = random.Random(71); p = [cyl(f"po{i}", 0.06, 0.07, 1.9, (x, y, 0), SEA_D, 5) for i, (x, y) in enumerate(((-1.9, -0.5), (1.9, -0.5), (-1.9, 0.5), (1.9, 0.5)))]
    for k, z in enumerate((1.35, 1.8)):
        p += [limb(f"bar{k}{s}", (-1.9, s * 0.5, z), (1.9, s * 0.5, z), 0.035, 0.035, SEA, 4) for s in (-1, 1)]
        p += [box(f"fish{k}_{i}", (0.1, 0.03, r.uniform(0.35, 0.5)), (-1.7 + i * 0.28, 0, z - 0.28), "#B8AE8C" if i % 2 else "#9A9078", rot=(0, 0, r.uniform(-.08, .08))) for i in range(14)]
    return p
def boat_upturned():
    """엎어 둔 배 4×1.5m, 높이 0.8m: 수리하려고 뒤집어 받침목에 올린 나룻배. 바닥에 타르를 발랐다."""
    return [sphere("hull", 1.0, (0, 0, 0.55), TAR, 10, 5, (2.0, 0.72, 0.5)), sphere("keel", 1.0, (0, 0, 0.9), SEA_D, 10, 3, (1.9, 0.07, 0.07)), box("log1", (0.2, 1.6, 0.2), (-1.0, 0, 0.1), SEA), box("log2", (0.2, 1.6, 0.2), (1.0, 0, 0.1), SEA),
            box("patch", (0.6, 0.5, 0.03), (0.5, -0.45, 0.78), "#8A7A5E", rot=(0.4, 0, 0)), limb("oar", (-2.2, -1.0, 0.05), (-0.4, -1.2, 0.05), 0.03, 0.03, SEA, 4)]
def rope_post():
    """밧줄 말뚝 0.9m: 굵은 말뚝에 밧줄이 서너 바퀴 감겼다. 선창 가장자리·마당 모서리에 줄지어 선다."""
    p = [cyl("post", 0.14, 0.17, 0.9, (0, 0, 0), SEA_D, 6), cyl("cap", 0.17, 0.12, 0.1, (0, 0, 0.9), TAR, 6)]
    p += [cyl(f"coil{i}", 0.2, 0.2, 0.05, (0, 0, 0.3 + i * 0.08), ROPE, 8) for i in range(4)] + [limb("tail", (0.2, 0, 0.35), (0.9, -0.4, 0.04), 0.03, 0.03, ROPE, 4)]
    return p
def crate_stack():
    """궤짝 더미 1.6m: 젓갈·생선 나무 궤짝 셋을 어긋나게 쌓고 위에 그물 한 장."""
    return [box("c1", (0.9, 0.6, 0.5), (-0.3, 0, 0.25), SEA), box("c2", (0.9, 0.6, 0.5), (0.5, 0.1, 0.25), SEA_D, rot=(0, 0, 0.1)), box("c3", (0.8, 0.6, 0.5), (0.0, 0.0, 0.75), SEA, rot=(0, 0, -0.15)), box("net", (0.9, 0.7, 0.04), (0.0, 0.0, 1.02), "#9A9068", rot=(0, 0, 0.3)), box("slat", (0.9, 0.04, 0.06), (-0.3, -0.31, 0.3), SEA_D)]
def seaweed_line():
    """미역 줄 4m, 높이 1.8m: 기둥 둘 사이 줄에 미역 가닥이 널렸다(검푸른 빛)."""
    r = random.Random(73); p = [cyl("pL", 0.06, 0.06, 1.9, (-2.0, 0, 0), SEA_D, 5), cyl("pR", 0.06, 0.06, 1.9, (2.0, 0, 0), SEA_D, 5), limb("rope", (-2.0, 0, 1.8), (2.0, 0, 1.75), 0.02, 0.02, ROPE, 3)]
    p += [box(f"w{i}", (0.16, 0.03, r.uniform(0.5, 0.9)), (-1.8 + i * 0.3, 0, 1.75 - 0.4), "#2F3F34" if i % 2 else "#3A4A3A", rot=(0, 0, r.uniform(-.1, .1))) for i in range(13)]
    return p
def clam_basket():
    """조개 바구니 0.9m: 대나무 바구니에 조개와 호미. 갯벌에서 막 돌아온 모양."""
    r = random.Random(74); p = [lathe_rz("basket", [(0, 0.0), (0.3, 0.02), (0.4, 0.3), (0.45, 0.45)], 8, "#A8955A"), limb("hoe", (0.5, -0.1, 0.02), (1.0, -0.3, 0.3), 0.025, 0.025, SEA, 4), box("hoe_blade", (0.12, 0.03, 0.14), (1.02, -0.32, 0.34), "#3A3A44")]
    p += [sphere(f"cl{i}", 0.07, (r.uniform(-.2, .2), r.uniform(-.2, .2), 0.4 + r.uniform(0, .08)), "#CFC8B0", 5, 3, (1, 1, 0.6)) for i in range(7)]
    return p
def firewood_stack():
    """땔감 더미 2×0.9m, 높이 1m: 소나무 쪼갠 장작을 켜켜이 쌓고 위에 이엉 한 장."""
    r = random.Random(75); p = []
    for row in range(4):
        for i in range(6 - row // 2): p.append(cyl(f"lg{row}_{i}", 0.09, 0.09, 0.85, (-0.9 + i * 0.36 + (0.18 if row % 2 else 0), 0.0, 0.1 + row * 0.2), "#7A5A3A" if (i + row) % 2 else "#6B4A2E", 6, rot=(1.5708, 0, 0)))
    p.append(box("cover", (2.0, 1.0, 0.05), (0, 0, 0.98), THATCH, rot=(0.15, 0, 0))); return p
def tar_barrel():
    """타르 통과 솥 1m: 배 바닥 칠할 타르를 끓이는 검은 통과 그을린 돌 화덕. 연기 자국."""
    return [cyl("hearth", 0.5, 0.45, 0.35, (0, 0, 0), ROCK_D, 8), cyl("pot", 0.38, 0.32, 0.42, (0, 0, 0.35), "#2A2826", 8), cyl("tar", 0.3, 0.3, 0.02, (0, 0, 0.76), "#15130F", 8), limb("ladle", (0.2, 0, 0.75), (0.95, -0.3, 0.55), 0.025, 0.025, SEA, 4), cyl("soot", 0.2, 0.2, 0.01, (0.6, 0.4, 0.0), "#2A2826", 6)]
def salt_sack_stack():
    """소금 가마니 더미 1.6m: 짚 가마니 여섯을 쌓았다. 주둥이를 묶은 새끼줄."""
    p = []
    for i in range(3): p.append(sphere(f"s{i}", 0.38, (-0.5 + i * 0.5, 0, 0.3), THATCH, 6, 4, (0.9, 0.75, 0.8)))
    for i in range(2): p.append(sphere(f"t{i}", 0.38, (-0.25 + i * 0.5, 0.05, 0.8), "#C8BA7C", 6, 4, (0.9, 0.75, 0.8)))
    p.append(sphere("u", 0.38, (0.0, 0.05, 1.28), THATCH, 6, 4, (0.9, 0.75, 0.8))); p += [box("salt_leak", (0.4, 0.3, 0.02), (0.9, -0.5, 0.01), SALT)]; return p
def salt_yoke():
    """소금 지게 1.2m: 소금 가마니 둘을 진 채 세워 둔 지게와 작대기. 소금밭 일꾼이 잠깐 놓고 간 모양."""
    return [limb("legL", (-0.3, 0, 0), (-0.3, 0.3, 1.0), 0.04, 0.04, "wood_dark", 4), limb("legR", (0.3, 0, 0), (0.3, 0.3, 1.0), 0.04, 0.04, "wood_dark", 4), box("rung1", (0.7, 0.04, 0.04), (0, 0.15, 0.5), "wood_dark"), box("rung2", (0.7, 0.04, 0.04), (0, 0.28, 0.95), "wood_dark"),
            sphere("sk1", 0.3, (0, 0.45, 0.45), THATCH, 6, 4, (1, 0.8, 0.9)), sphere("sk2", 0.28, (0, 0.5, 0.95), "#C8BA7C", 6, 4, (1, 0.8, 0.9)), limb("stick", (0.5, -0.4, 0), (0.45, -0.1, 1.1), 0.03, 0.03, SEA, 4)]
def brine_trough():
    """소금물 구유 2.4×0.8m: 바닷물을 가둔 긴 나무 구유와 물 긷는 바가지."""
    return [box("t1", (2.4, 0.8, 0.12), (0, 0, 0.35), SEA_D), box("sideA", (2.4, 0.08, 0.35), (0, -0.4, 0.5), SEA), box("sideB", (2.4, 0.08, 0.35), (0, 0.4, 0.5), SEA), box("endA", (0.08, 0.8, 0.35), (-1.2, 0, 0.5), SEA_D), box("endB", (0.08, 0.8, 0.35), (1.2, 0, 0.5), SEA_D),
            box("brine", (2.3, 0.7, 0.02), (0, 0, 0.62), "#B8C0C0"), box("leg1", (0.14, 0.7, 0.35), (-0.9, 0, 0.17), SEA_D), box("leg2", (0.14, 0.7, 0.35), (0.9, 0, 0.17), SEA_D), sphere("gourd", 0.14, (1.5, -0.2, 0.15), "#CDBF8A", 5, 3, (1, 1, 0.6))]
def salt_shed():
    """소금막 3.5×2.5m, 높이 2.6m: 소금 졸이는 가마솥을 덮은 사방이 트인 낮은 막. 아궁이 그을음, 통나무 땔감."""
    p = [cyl(f"po{i}", 0.08, 0.08, 2.0, (x, y, 0), SEA_D, 5) for i, (x, y) in enumerate(((-1.6, -1.1), (1.6, -1.1), (-1.6, 1.1), (1.6, 1.1)))]
    p += [prism("roof", 4.2, 3.0, 1.0, (0, 0, 2.0), THATCH), box("hearth", (1.4, 1.0, 0.45), (0, 0.2, 0.22), ROCK_D), lathe_rz("kettle", [(0, 0.0), (0.6, 0.15), (0.75, 0.3), (0.7, 0.35)], 9, "#2A2826", loc=(0, 0.2, 0.45)), box("white", (1.1, 0.8, 0.02), (0, 0.2, 0.84), SALT)]
    p += [cyl(f"lg{i}", 0.08, 0.08, 0.7, (-1.5 + i * 0.2, -0.8, 0.1), "#7A5A3A", 5, rot=(1.5708, 0, 0)) for i in range(5)]; return p

# ───────── 해안·여울·곶 (a3c_) ─────────
def driftwood():
    """유목 무더기 3m: 바다가 밀어 올린 하얗게 바랜 통나무와 가지. 밑동에 해초 한 줌."""
    return [limb("log1", (-1.4, 0.0, 0.2), (1.3, 0.3, 0.3), 0.2, 0.15, "#B8B0A0", 6), limb("log2", (-0.8, 0.5, 0.15), (1.0, -0.4, 0.4), 0.12, 0.09, "#A8A090", 5), limb("br1", (0.2, 0.2, 0.3), (0.6, 0.6, 0.9), 0.06, 0.02, "#B8B0A0", 4), limb("br2", (-0.4, 0.1, 0.3), (-0.7, -0.4, 0.8), 0.05, 0.02, "#B8B0A0", 4), sphere("weed", 0.3, (-1.4, 0.0, 0.1), "#2F3F34", 5, 3, (1, 1, 0.4))]
def barnacle_rock():
    """굴 붙은 갯바위 2.2m: 젖은 바위 밑동에 하얀 굴껍데기가 다닥다닥, 꼭대기는 갈매기 똥으로 흰 얼룩."""
    r = random.Random(77); p = [sphere("rock", 1.0, (0, 0, 0.6), ROCK, 7, 5, (1.1, 0.9, 0.75)), sphere("rock2", 0.55, (0.9, -0.4, 0.3), ROCK_D, 6, 4, (1, 1, 0.7)), sphere("top", 0.4, (-0.1, 0, 1.15), "#D8D4C8", 5, 3, (1, 1, 0.3))]
    p += [sphere(f"b{i}", 0.06, (math.cos(a) * 1.05 * 1.1, math.sin(a) * 0.9, 0.12 + r.uniform(0, 0.25)), "#D8D4C8", 4, 3) for i, a in enumerate(r.uniform(0, TAU) for _ in range(26))]; return p
def seagrass():
    """갯풀 무더기 1.2m: 소금기에 누렇게 선 질긴 풀 서른 가닥."""
    r = random.Random(78); p = []
    for i in range(34): a = r.uniform(0, TAU); d = r.uniform(0, 0.5); h = r.uniform(0.5, 1.1); p.append(limb(f"g{i}", (math.cos(a) * d, math.sin(a) * d, 0), (math.cos(a) * (d + r.uniform(.05, .3)), math.sin(a) * (d + .2), h), 0.014, 0.004, "#8A9A5A" if i % 3 else "#A8A468", 3))
    return p
def crab_pots():
    """게통발 더미 1.6m: 대나무 둥근 통발 셋을 쌓고 부표 줄. 아가리가 깔때기 모양."""
    p = []
    for i, (x, y, z) in enumerate(((-0.5, 0, 0.3), (0.5, 0.05, 0.3), (0.0, 0.0, 0.85))): p += [cyl(f"pot{i}", 0.4, 0.35, 0.55, (x, y, z - 0.3), "#A8955A", 8), cyl(f"mouth{i}", 0.18, 0.12, 0.1, (x, y, z + 0.25), "#6A5A3A", 6)]
    p += [limb("rope", (0.0, 0.0, 1.2), (1.0, -0.6, 0.1), 0.02, 0.02, ROPE, 3), sphere("float", 0.1, (1.05, -0.62, 0.12), "#B4A06A", 5, 3)]; return p
def hull_ribs():
    """난파선 뼈대 4m, 높이 2m: 모래에 반쯤 묻혀 갈비뼈처럼 드러난 선체 늑골 일곱과 용골. 난파 여울 표지."""
    p = [limb("keel", (-2.0, 0, 0.05), (2.0, 0, 0.15), 0.09, 0.09, SEA_D, 5)]
    for i in range(7):
        x = -1.8 + i * 0.6; s = 1.0 - abs(i - 3) * 0.14; p += [limb(f"rL{i}", (x, 0, 0.1), (x, -1.0 * s, 1.6 * s), 0.07, 0.04, SEA_D, 4), limb(f"rR{i}", (x, 0, 0.1), (x, 1.0 * s, 1.5 * s), 0.07, 0.04, SEA_D, 4)]
    p += [box("plank", (1.4, 0.2, 0.05), (1.0, -0.7, 0.3), SEA, rot=(0, 0.1, 0.2)), sphere("weed", 0.35, (-2.0, 0, 0.1), "#2F3F34", 5, 3, (1, 1, 0.4))]; return p
def shell_heap():
    """조개껍데기 더미 1.6m: 오래 쌓인 조개 무덤. 하얗게 바랜 껍데기 알갱이."""
    r = random.Random(79); p = [sphere("mound", 0.8, (0, 0, 0.1), "#C8C0A8", 7, 4, (1.2, 1.0, 0.35))]
    p += [sphere(f"sh{i}", 0.07, (r.uniform(-.8, .8), r.uniform(-.7, .7), 0.2 + r.uniform(0, .1)), "#E6E0CC", 4, 3, (1, 1, 0.5)) for i in range(18)]; return p

# ───────── 성문 밖 눈밭 (a3g_) ─────────
def snow_dead_tree():
    """눈 덮인 고사목 높이 4.5m: 잎 없는 가지마다 눈이 얹혔다."""
    p = [limb("trunk", (0, 0, 0), (0.1, 0, 3.0), 0.28, 0.13, "#4A3A30", 6)] + [limb(f"br{i}", (0.1, 0, 2.1 + i * 0.3), (0.1 + math.cos(i * 1.9) * (0.9 + 0.2 * i), math.sin(i * 1.9) * (0.9 + 0.2 * i), 3.2 + i * 0.3), 0.09, 0.02, "#4A3A30", 4) for i in range(5)]
    p += [box(f"sn{i}", (0.7, 0.2, 0.06), (0.1 + math.cos(i * 1.9) * (0.5 + 0.1 * i), math.sin(i * 1.9) * (0.5 + 0.1 * i), 2.75 + i * 0.3), SNOW, rot=(0, 0, i * 1.9)) for i in range(5)] + [sphere("drift", 0.6, (0, 0, 0.05), SNOW, 6, 3, (1.3, 1.1, 0.3))]; return p
def snow_fence():
    """눈 쌓인 낮은 울타리 4m, 높이 1m: 말뚝과 가로대, 윗면에 눈."""
    p = [limb(f"po{i}", (-1.8 + i * 0.9, 0, 0), (-1.8 + i * 0.9, 0, 1.0), 0.05, 0.04, "wood_dark", 4) for i in range(5)] + [limb("bar1", (-1.8, 0, 0.8), (1.8, 0, 0.8), 0.03, 0.03, "wood", 4), limb("bar2", (-1.8, 0, 0.45), (1.8, 0, 0.45), 0.03, 0.03, "wood", 4)]
    p += [box("snow", (4.0, 0.14, 0.06), (0, 0, 1.03), SNOW), box("drift", (3.6, 0.5, 0.1), (0, -0.2, 0.05), SNOW)]; return p
def abandoned_cart():
    """버려진 수레 2.4×1.2m: 바퀴 하나가 빠져 기운 손수레, 짐칸에 눈과 빈 가마니."""
    return [box("bed", (1.6, 1.0, 0.1), (0, 0, 0.55), "wood"), box("sideA", (1.6, 0.06, 0.3), (0, -0.5, 0.7), "wood_dark"), box("sideB", (1.6, 0.06, 0.3), (0, 0.5, 0.7), "wood_dark"), cyl("wheel", 0.45, 0.45, 0.08, (0.2, -0.65, 0.45), "wood_dark", 9, rot=(1.5708, 0, 0)), limb("shaftA", (-0.8, -0.35, 0.5), (-2.2, -0.35, 0.1), 0.04, 0.04, "wood", 4), limb("shaftB", (-0.8, 0.35, 0.5), (-2.2, 0.35, 0.1), 0.04, 0.04, "wood", 4),
            box("snow", (1.4, 0.8, 0.08), (0.0, 0.0, 0.64), SNOW), sphere("sack", 0.3, (-0.3, 0.1, 0.72), "#B8AE96", 5, 3, (1, 0.7, 0.5)), limb("prop", (0.7, 0.5, 0.5), (0.8, 0.7, 0.0), 0.04, 0.04, "wood", 4)]
def brazier():
    """화톳불 통 1.4m: 문지기가 쬐는 쇠 화덕 통. 불빛(Light_)이 눈 위에 번진다."""
    p = [cyl("bowl", 0.5, 0.35, 0.35, (0, 0, 0.8), "#2A2826", 8), cyl("coal", 0.42, 0.42, 0.03, (0, 0, 1.12), mat(WARM, 2.4), 8)] + [limb(f"leg{i}", (math.cos(i * 2.094) * 0.3, math.sin(i * 2.094) * 0.3, 0.8), (math.cos(i * 2.094) * 0.5, math.sin(i * 2.094) * 0.5, 0.0), 0.04, 0.04, "#2A2826", 4) for i in range(3)]
    p += [limb(f"lg{i}", (-0.3 + i * 0.3, 0.1, 1.12), (-0.1 + i * 0.1, -0.1, 1.3), 0.05, 0.04, "#3A2A1E", 4) for i in range(3)] + [cyl("ash", 0.7, 0.7, 0.01, (0, 0, 0.0), "#4A4640", 8)]; return p
def snow_cairn():
    """눈 얹은 돌탑 1.5m: 길손이 쌓은 작은 돌탑, 윗면마다 눈."""
    p = []
    for i in range(6): p += [sphere(f"s{i}", 0.42 - i * 0.05, (0.02 * (i % 3), 0, 0.2 + i * 0.22), ROCK if i % 2 else CITY, 6, 4, (1, 1, 0.65)), sphere(f"sn{i}", 0.28 - i * 0.03, (0.02 * (i % 3), 0, 0.3 + i * 0.22), SNOW, 5, 3, (1, 1, 0.25))]
    return p
def straw_bundle():
    """볏짚단 1.2m: 눈 맞은 짚단 세 개를 기대 세웠다."""
    return [limb(f"b{i}", (x, 0, 0.0), (x * 0.6, 0.0, 1.1), 0.22, 0.12, "#B89A55", 6) for i, x in enumerate((-0.3, 0.1, 0.45))] + [box("snow", (0.9, 0.5, 0.05), (0.1, 0, 1.12), SNOW), box("band", (0.6, 0.5, 0.03), (0.1, 0, 0.6), ROPE)]
def bare_shrub():
    """마른 떨기나무 0.9m: 눈 위로 삐죽 나온 잔가지 덤불."""
    r = random.Random(81); p = [limb(f"t{i}", (0, 0, 0.05), (math.cos(a) * r.uniform(0.3, 0.7), math.sin(a) * r.uniform(0.3, 0.7), r.uniform(0.5, 0.95)), 0.025, 0.006, "#5E4A34", 3) for i, a in enumerate(r.uniform(0, TAU) for _ in range(12))]
    p.append(sphere("snow", 0.45, (0, 0, 0.05), SNOW, 5, 3, (1.1, 1.1, 0.2))); return p

# ───────── 움막촌·다리 밑 (a3s_) ─────────
def laundry_line():
    """움막 빨래줄 3.5m, 높이 1.9m: 장대 둘 사이에 기운 헌 옷 몇 벌이 얼어붙었다."""
    r = random.Random(82); p = [cyl("pL", 0.05, 0.05, 2.0, (-1.75, 0, 0), SEA_D, 5), cyl("pR", 0.05, 0.05, 2.0, (1.75, 0, 0), SEA_D, 5), limb("line", (-1.75, 0, 1.9), (1.75, 0, 1.85), 0.012, 0.012, ROPE, 3)]
    p += [box(f"cl{i}", (r.uniform(.3, .5), 0.03, r.uniform(.5, .9)), (-1.3 + i * 0.62, 0, 1.4), c, rot=(0, 0, r.uniform(-.05, .05))) for i, c in enumerate(("#8A7A64", "#6E6A62", "#A89E84", "#74664E", "#9A8F78"))]; return p
def clay_stove():
    """흙 화덕 1m: 진흙으로 빚은 야외 화덕에 낡은 솥과 그을음. 움막 앞 부엌."""
    return [cyl("body", 0.5, 0.4, 0.7, (0, 0, 0), "#8A6A4A", 8), cyl("mouth", 0.18, 0.18, 0.3, (0, -0.45, 0.1), "#2A2826", 6, rot=(1.5708, 0, 0)), lathe_rz("pot", [(0, 0.0), (0.3, 0.1), (0.35, 0.28), (0.3, 0.32)], 8, "#2A2826", loc=(0, 0, 0.7)), box("soot", (0.4, 0.04, 0.3), (0, -0.45, 0.2), "#2A2826"), limb("chimney", (0.3, 0.2, 0.6), (0.4, 0.3, 1.3), 0.08, 0.06, "#8A6A4A", 5)]
def jar_stand():
    """독 받침 1.6m: 돌을 괸 널 위에 금 간 독 셋. 빗물·식수를 받는다."""
    p = [box("stage", (1.6, 0.6, 0.12), (0, 0, 0.22), SEA), box("s1", (0.2, 0.5, 0.18), (-0.6, 0, 0.09), ROCK), box("s2", (0.2, 0.5, 0.18), (0.6, 0, 0.09), ROCK)]
    p += [lathe_rz(f"j{i}", [(0, 0.0), (0.2, 0.1), (0.38, 0.35), (0.3, 0.6), (0.18, 0.68)], 8, "jar", loc=(-0.5 + i * 0.5, 0, 0.28)) for i in range(3)] + [box("lid", (0.3, 0.3, 0.04), (0.5, 0, 0.98), SEA_D)]; return p
def rag_tent():
    """거적 천막 3×2.4m, 높이 1.7m: 장대 둘에 거적을 비스듬히 걸친 눕는 자리. 안에 짚."""
    return [limb("poleL", (-1.3, 0, 0), (-1.3, 0, 1.7), 0.05, 0.04, "wood_dark", 4), limb("poleR", (1.3, 0, 0), (1.3, 0, 1.7), 0.05, 0.04, "wood_dark", 4), limb("ridge", (-1.3, 0, 1.7), (1.3, 0, 1.7), 0.03, 0.03, "wood", 4), box("matA", (2.8, 1.5, 0.05), (0, -0.7, 0.9), MAT, rot=(0.9, 0, 0)), box("matB", (2.8, 1.3, 0.05), (0, 0.65, 0.95), "#8A7A58", rot=(-0.95, 0, 0)), box("straw", (2.0, 1.0, 0.1), (0, 0, 0.06), "#B89A55")]
def plank_stack():
    """판자 더미 2×0.8m, 높이 0.8m: 떠내려온 널판을 주워 쌓았다. 못 박힌 끝."""
    r = random.Random(84); p = [box(f"pl{i}", (2.0 - r.uniform(0, .3), 0.28, 0.08), (r.uniform(-.1, .1), -0.25 + (i % 3) * 0.26, 0.05 + (i // 3) * 0.1), "#8A7A5E" if i % 2 else "#74664E", rot=(0, 0, r.uniform(-.06, .06))) for i in range(9)]
    p += [box("ground", (0.1, 0.8, 0.1), (-0.6, 0, 0.0), SEA_D)]; return p
def hen_coop():
    """닭장 1.2m: 널과 짚으로 얽은 작은 닭장, 앞에 횃대 하나. 움막촌에도 산 것이 있다는 표지."""
    return [box("coop", (1.0, 0.8, 0.6), (0, 0, 0.55), "#8A7A5E"), prism("roof", 1.3, 1.0, 0.35, (0, 0, 0.85), THATCH), limb("legA", (-0.4, -0.3, 0), (-0.4, -0.3, 0.25), 0.04, 0.04, "wood_dark", 4), limb("legB", (0.4, -0.3, 0), (0.4, -0.3, 0.25), 0.04, 0.04, "wood_dark", 4), limb("perch", (-0.5, -0.8, 0.2), (0.5, -0.8, 0.2), 0.025, 0.025, "wood", 4), box("hole", (0.25, 0.04, 0.25), (0, -0.41, 0.45), "#2A2826"), sphere("hen", 0.12, (0.2, -0.8, 0.32), "#B8AE96", 5, 3, (1, 1.3, 1))]

# ───────── 저잣거리 (a3k_) ─────────
def mk_crates():
    """저잣 궤짝 더미 1.8m: 장사 짐 궤짝 넷과 위에 얹은 보자기."""
    return [box("c1", (0.8, 0.6, 0.6), (-0.5, 0, 0.3), "wood"), box("c2", (0.8, 0.6, 0.6), (0.4, 0.05, 0.3), "wood_dark"), box("c3", (0.8, 0.6, 0.6), (-0.1, 0, 0.9), "wood", rot=(0, 0, 0.1)), box("c4", (0.6, 0.5, 0.45), (1.3, 0, 0.22), "wood_dark"), box("cloth", (0.7, 0.5, 0.04), (-0.1, 0, 1.22), "#8A3A3A", rot=(0, 0, 0.2))]
def mk_cloth_rack():
    """옷감 시렁 2.4m, 높이 2m: 천 필이 걸린 'ㅍ'자 시렁. 흰·쪽·누른 천이 번갈아."""
    p = [cyl("pL", 0.05, 0.05, 2.0, (-1.1, 0, 0), "wood_dark", 5), cyl("pR", 0.05, 0.05, 2.0, (1.1, 0, 0), "wood_dark", 5), limb("bar", (-1.1, 0, 1.9), (1.1, 0, 1.9), 0.035, 0.035, "wood", 4)]
    p += [box(f"cl{i}", (0.34, 0.03, 1.0), (-0.8 + i * 0.4, 0, 1.38), c) for i, c in enumerate(("#E6DFC8", "#3E64B0", "#E8C15A", "#E6DFC8", "#7A5A6A", "#3E64B0"))]; return p
def mk_barrels():
    """통 둘 1.4m: 장터 뒤에 세운 물통과 술통."""
    return [lathe_rz("b1", [(0, 0.0), (0.32, 0.02), (0.4, 0.4), (0.32, 0.8), (0, 0.8)], 9, "wood", loc=(-0.4, 0, 0)), lathe_rz("b2", [(0, 0.0), (0.28, 0.02), (0.36, 0.35), (0.28, 0.7), (0, 0.7)], 9, "wood_dark", loc=(0.45, 0.1, 0)), box("hoop1", (0.84, 0.84, 0.03), (-0.4, 0, 0.25), "#3A3A44"), box("hoop2", (0.84, 0.84, 0.03), (-0.4, 0, 0.55), "#3A3A44")]

LIST = [("a3h_fish_rack", fish_rack, "생선 말림대"), ("a3h_boat_upturned", boat_upturned, "엎어 둔 배"), ("a3h_rope_post", rope_post, "밧줄 말뚝"), ("a3h_crate_stack", crate_stack, "궤짝 더미"), ("a3h_seaweed_line", seaweed_line, "미역 줄"), ("a3h_clam_basket", clam_basket, "조개 바구니"),
        ("a3h_firewood_stack", firewood_stack, "땔감 더미"), ("a3h_tar_barrel", tar_barrel, "타르 통"), ("a3h_salt_sack_stack", salt_sack_stack, "소금 가마니"), ("a3h_salt_yoke", salt_yoke, "소금 지게"), ("a3h_brine_trough", brine_trough, "소금물 구유"), ("a3h_salt_shed", salt_shed, "소금막"),
        ("a3c_driftwood", driftwood, "유목"), ("a3c_barnacle_rock", barnacle_rock, "굴 붙은 갯바위"), ("a3c_seagrass", seagrass, "갯풀"), ("a3c_crab_pots", crab_pots, "게통발"), ("a3c_hull_ribs", hull_ribs, "난파선 뼈대"), ("a3c_shell_heap", shell_heap, "조개 더미"),
        ("a3g_snow_dead_tree", snow_dead_tree, "눈 덮인 고사목"), ("a3g_snow_fence", snow_fence, "눈 울타리"), ("a3g_abandoned_cart", abandoned_cart, "버려진 수레"), ("a3g_brazier", brazier, "화톳불 통"), ("a3g_snow_cairn", snow_cairn, "눈 돌탑"), ("a3g_straw_bundle", straw_bundle, "볏짚단"), ("a3g_bare_shrub", bare_shrub, "마른 떨기나무"),
        ("a3s_laundry_line", laundry_line, "빨래줄"), ("a3s_clay_stove", clay_stove, "흙 화덕"), ("a3s_jar_stand", jar_stand, "독 받침"), ("a3s_rag_tent", rag_tent, "거적 천막"), ("a3s_plank_stack", plank_stack, "판자 더미"), ("a3s_hen_coop", hen_coop, "닭장"),
        ("a3k_crates", mk_crates, "저잣 궤짝"), ("a3k_cloth_rack", mk_cloth_rack, "옷감 시렁"), ("a3k_barrels", mk_barrels, "통 둘")]
LIGHTS = {"a3g_brazier": [("Light_brazier", (0.0, 0.0, 1.3), WARM, 1.2, 8.0, True)], "a3h_salt_shed": [("Light_salt_shed", (0.0, 0.2, 1.0), WARM, 0.8, 5.0, True)], "a3h_tar_barrel": [("Light_tar_fire", (0.0, 0.0, 0.3), WARM, 0.6, 4.0, True)]}

def run():
    rep = []
    for key, fn, nm in LIST:
        reset(); o = join(key, fn()); [light_empty(o, n, pos, c, i, r, f) for n, pos, c, i, r, f in LIGHTS.get(key, [])]
        lo, hi = bounds(o); export(o, os.path.join(OUT, "act3", key + ".glb"))
        rep.append({"name": key, "label": nm, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
    json.dump(rep, open(os.path.join(OUT, "act3", "_report_act3_life.json"), "w"), ensure_ascii=False, indent=1)
    if "--nopreview" in sys.argv: return rep
    for part, pre in (("a", "a3h_"), ("b", "a3c_"), ("c", "a3g_"), ("d", "a3s_"), ("e", "a3k_")):
        reset(); items = [(k, f) for k, f, _ in LIST if k.startswith(pre)]
        for i, (k, f) in enumerate(items): o = join(f"p{i}", f()); o.location = ((i % 6 - 2.5) * 5.0, 3.0 - (i // 6) * 5.5, 0)
        setup_render(32, (0, -1.5, 0.8), size=(1600, 900), ground_size=60); bpy.context.scene.cycles.samples = 28
        render(os.path.join(OUT, "previews", f"act3_life_{part}_50deg.png"))
    return rep
if __name__ == "__main__":
    for r in run(): print(r["name"], r["tris"], r["size_m"], "min_z", r["min_z"])
