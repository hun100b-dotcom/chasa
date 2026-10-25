"""3막 지역 키트 1차: ⑤ 갯마을(포구·소금밭·망부석 곶·난파 여울). 실행: python3 act3_kit.py [이름 ...]
왜 이 순서인가: 기획 act3_map.json 에서 ⑤가 먼저 걸어 들어갈 곳(강둑길→소금밭→포구)이고, ⑥은 2차에 만든다(docs/ACT3-KIT-PLAN.md).
규약은 act2_kit.py 와 같다(원점=바닥 한가운데, 정면=-Y, 1단위=1m, 재질은 색만, 불빛은 발광+Light_ 빈 오브젝트). 불은 따뜻한 등불색(#FFB066), 주황은 파혼 전용이라 쓰지 않는다.
색 뼈대: 바닷바람에 바랜 나무(#8A8478)·소금 흰색(#E6E2D6, 혼불 청록과 겹치지 않게 따뜻한 흰색)·젖은 갯벌(#5E5A50)·타르 먹은 지붕(#3A3632)·이엉(#B4A66A).
출력: assets3d/act3/ (접두 harbor_ / salt_ / cape_ / shoal_)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
SEA_WOOD = "#8A8478"; SEA_WOOD_D = "#6A645A"; SALT = "#E6E2D6"; MUD = "#5E5A50"; TAR = "#3A3632"; THATCH = "#B4A66A"; ROCK = "#6E6A62"; ROCK_D = "#58554F"; WARM = "#FFB066"

def harbor_pier():
    """나무 선창 한 칸 4×3m: 바닷바람에 바랜 널판을 깔고 아래 말뚝 여섯(바다 속 3m까지 박혀 있어 바다 위에 놓아도 떠 보이지 않는다, 널판 높이 +0.55m). 가장자리는 닳아 들쭉날쭉."""
    r = random.Random(31); p = []
    for i in range(10): p.append(box(f"plank{i}", (3.0 + r.uniform(-.05, .05), 0.38, 0.07), (0, -1.5 + i * 0.32 + 0.16, 0.55 + r.uniform(0, .015)), SEA_WOOD if i % 3 else SEA_WOOD_D))
    p += [box(f"bear{i}", (4.0, 0.14, 0.12), (0, -1.2 + i * 1.2, 0.46), SEA_WOOD_D) for i in range(3)]
    p += [cyl(f"pile{i}", 0.1, 0.12, 3.5, (-1.7 + (i % 2) * 3.4, -1.3 + (i // 2) * 1.3, -3.0), SEA_WOOD_D, 6) for i in range(6)]
    return p

def harbor_gauge_post():
    """물때 눈금 말뚝 높이 3m: 25분 주기 썰물·밀물 높이를 읽는 말뚝. 흰 눈금 열두 줄(굵은 줄은 셋마다)."""
    p = [cyl("post", 0.12, 0.14, 3.0, (0, 0, 0), SEA_WOOD_D, 6)]
    for i in range(12): p.append(box(f"tick{i}", (0.3 if i % 3 == 0 else 0.2, 0.04, 0.04), (0, -0.13, 0.4 + i * 0.2), SALT))
    p += [box("cap", (0.34, 0.34, 0.1), (0, 0, 3.0), TAR)]
    return p

def harbor_boat():
    """선창에 묶인 빈 배 4.5×1.4m: 뱃전이 낮은 나룻배. 안은 비었고 노가 가로로 걸쳐 있다. 밤엔 줄에 묶여 흔들리는 것이 보인다(흔들림은 코드)."""
    p = [sphere("hull", 1.0, (0, 0, 0.3), SEA_WOOD_D, 10, 5, (2.25, 0.7, 0.35)), sphere("hull_in", 0.9, (0, 0, 0.42), "#4A463E", 10, 4, (2.15, 0.6, 0.3))]
    p += [box("seat1", (0.1, 1.1, 0.06), (0.6, 0, 0.45), SEA_WOOD), box("seat2", (0.1, 1.0, 0.06), (-0.7, 0, 0.45), SEA_WOOD)]
    p += [cyl("oar", 0.03, 0.03, 2.4, (0.1, 0, 0.62), SEA_WOOD, 5, rot=(0, 1.57, 0.1)), box("oar_blade", (0.5, 0.14, 0.03), (1.3, 0.1, 0.62), SEA_WOOD)]
    p += [limb("rope", (2.1, 0, 0.45), (3.1, -0.3, 0.25), 0.025, 0.025, THATCH, 4)]
    return p

def harbor_net_frame():
    """그물 너는 틀 4×1m, 높이 2.4m: 긴 장대 둘 사이에 그물을 널어 말린다. 그물은 얇은 격자 판과 늘어진 가닥, 부표(나무 공) 몇 개."""
    r = random.Random(33); p = [cyl("poleL", 0.07, 0.08, 2.6, (-2.0, 0, 0), SEA_WOOD_D, 6), cyl("poleR", 0.07, 0.08, 2.6, (2.0, 0, 0), SEA_WOOD_D, 6), cyl("bar", 0.05, 0.05, 4.0, (-2.0, 0, 2.4), SEA_WOOD, 6, rot=(0, 1.5708, 0))]
    p += [box("net", (3.8, 0.03, 1.5), (0, 0, 1.6), "#9A9068")]
    p += [box(f"strand{i}", (0.02, 0.02, r.uniform(0.3, 0.6)), (-1.7 + i * 0.4, 0, 0.8), "#9A9068") for i in range(9)]
    p += [sphere(f"float{i}", 0.07, (-1.6 + i * 0.9, -0.03, 2.2), "#B4A06A", 5, 3) for i in range(5)]
    return p

def harbor_net_pile():
    """그물 더미 1.4m: 말려 두려고 쌓은 그물 뭉치와 부표."""
    r = random.Random(34); p = [sphere("heap", 0.6, (0, 0, 0.3), "#9A9068", 7, 4, (1.2, 1.0, 0.55))]
    p += [sphere(f"fl{i}", 0.07, (r.uniform(-.5, .5), r.uniform(-.4, .4), 0.5 + r.uniform(0, .1)), "#B4A06A", 5, 3) for i in range(5)]
    return p

def harbor_jar():
    """젓갈독 무리 1.6m: 옹기 독 넷과 돌 눌러놓은 뚜껑."""
    p = []
    for i, (x, y, s) in enumerate(((-0.4, 0.0, 1.0), (0.3, -0.2, 0.8), (0.1, 0.45, 0.9), (-0.5, 0.5, 0.7))):
        p += [sphere(f"jar{i}", 0.3 * s, (x, y, 0.3 * s), "#6A4A36", 8, 5, (1, 1, 1.1)), cyl(f"lid{i}", 0.2 * s, 0.2 * s, 0.05, (x, y, 0.62 * s), "#4A3A2E", 7), sphere(f"stone{i}", 0.07, (x, y, 0.68 * s), ROCK, 5, 3)]
    return p

def harbor_gaekju_house():
    """객주 집 8×6m, 높이 5m: 기와 얹은 긴 집. 마루가 앞으로 나와 있고(장부 펼치는 자리), 처마에 등. 포구에서 가장 큰 집."""
    p = [box("floor", (8.0, 6.0, 0.5), (0, 0, 0.25), ROCK_D), box("wall", (7.4, 4.6, 2.4), (0, 0.4, 1.7), "#CFC7B0"), box("porch", (6.0, 1.6, 0.18), (0, -2.8, 0.65), "wood")]
    p += [cyl(f"pil{i}", 0.12, 0.12, 2.5, (-2.8 + i * 1.4, -3.4, 1.9), "pillar", 6) for i in range(5)]
    p += [box(f"door{i}", (1.0, 0.1, 1.7), (-2.4 + i * 1.6, -1.95, 1.3), "wood_dark") for i in range(4)]
    p += [prism("roof", 8.8, 6.8, 1.9, (0, 0, 2.9), "tile"), box("eave_lamp", (0.22, 0.22, 0.3), (0, -3.5, 2.5), WARM)]
    return p

def harbor_inn():
    """포구 주막 6×5m, 높이 4m: 이엉 지붕 낮은 집, 문 앞 술 평상과 등 하나. 선원이 들르는 곳."""
    p = [box("floor", (6.0, 5.0, 0.4), (0, 0, 0.2), ROCK_D), box("wall", (5.4, 4.2, 2.0), (0, 0.3, 1.4), "#C2B898"), prism("roof", 6.8, 5.8, 1.7, (0, 0, 2.4), THATCH)]
    p += [box("bench", (2.2, 0.7, 0.1), (-1.2, -2.8, 0.55), "wood"), box("bench_l1", (0.1, 0.5, 0.5), (-2.1, -2.8, 0.25), "wood_dark"), box("bench_l2", (0.1, 0.5, 0.5), (-0.3, -2.8, 0.25), "wood_dark"), box("door", (1.1, 0.1, 1.6), (1.2, -1.8, 1.2), "wood_dark"), box("lamp", (0.2, 0.2, 0.3), (2.0, -2.2, 2.2), WARM)]
    return p

def harbor_lamp_hut():
    """등대지기 막 3×3m: 선창 끝 작은 막과 키 큰 등대 장대. 장대 끝에 등롱."""
    p = [box("hut", (3.0, 3.0, 1.8), (0, 0, 0.9), "#B4A98A"), prism("roof", 3.6, 3.6, 1.2, (0, 0, 1.8), THATCH), box("door", (0.8, 0.08, 1.3), (0, -1.52, 0.7), "wood_dark")]
    p += [cyl("mast", 0.08, 0.1, 4.8, (2.2, 0, 0), SEA_WOOD_D, 6), box("lantern", (0.35, 0.35, 0.45), (2.2, 0, 4.7), WARM)]
    return p

def salt_pan():
    """염전 칸 4×4m: 낮은 흙둑으로 둘러싼 얕은 판에 흰 소금 껍질. 네 칸을 이어 놓으면 바둑판이 된다."""
    r = random.Random(41); p = [box("bed", (3.6, 3.6, 0.06), (0, 0, 0.03), "#C9C2B0")]
    p += [box("dikeN", (4.0, 0.3, 0.2), (0, 1.85, 0.1), "#7A6E58"), box("dikeS", (4.0, 0.3, 0.2), (0, -1.85, 0.1), "#7A6E58"), box("dikeE", (0.3, 4.0, 0.2), (1.85, 0, 0.1), "#7A6E58"), box("dikeW", (0.3, 4.0, 0.2), (-1.85, 0, 0.1), "#7A6E58")]
    p += [box(f"crust{i}", (r.uniform(.5, 1.0), r.uniform(.5, 1.0), 0.05), (r.uniform(-1.3, 1.3), r.uniform(-1.3, 1.3), 0.095), SALT) for i in range(7)]
    return p

def salt_pile():
    """소금 더미 높이 1.6m: 달빛에 혼불처럼 빛난다. 흰색은 따뜻하게(#E6E2D6) 두어 청록 혼불과 구분하고, 발광은 약하게 둔다."""
    p = [sphere("mound", 1.1, (0, 0, 0.5), SALT, 9, 5, (1.2, 1.0, 0.75)), sphere("mound2", 0.6, (1.0, 0.4, 0.25), SALT, 7, 4, (1, 1, 0.7))]
    p += [box("tarp", (1.6, 1.2, 0.04), (-0.2, -0.3, 1.0), "#7A7060", rot=(0.4, 0.2, 0.1))]
    return p

def salt_warehouse():
    """소금 창고 6×4m, 높이 3.8m: 통나무 벽 위에 이엉 지붕. 문이 크고 문턱이 높다(소금이 젖지 않게)."""
    p = [box("floor", (6.0, 4.0, 0.5), (0, 0, 0.25), ROCK_D), box("wall", (5.4, 3.6, 2.0), (0, 0, 1.5), "#9A8E70"), prism("roof", 6.6, 4.6, 1.6, (0, 0, 2.5), THATCH)]
    p += [box("door", (1.6, 0.12, 1.8), (0, -1.85, 1.4), "wood_dark")] + [box(f"log{i}", (5.5, 0.1, 0.1), (0, -1.82, 0.7 + i * 0.4), "#7A6A4A") for i in range(4)]
    return p

def salt_dike():
    """염전 둑 4m: 흙을 돋운 긴 둑 위에 마른 풀 몇 포기."""
    r = random.Random(42); p = [box("dike", (4.0, 0.9, 0.4), (0, 0, 0.2), "#7A6E58"), box("dike_top", (3.8, 0.5, 0.15), (0, 0, 0.45), "#8A7E66")]
    p += [cyl(f"grass{i}", 0.01, 0.03, r.uniform(0.3, 0.5), (r.uniform(-1.8, 1.8), r.uniform(-0.3, 0.3), 0.52), "#8A8A58", 4) for i in range(10)]
    return p

def cape_waiting_rock():
    """망부석 높이 7m: 바다를 바라보는 사람 모양 바위. 둥근 머리, 어깨, 한쪽으로 기운 몸. 곶 끝(1215,690) 발치 가까이."""
    p = [sphere("base", 2.2, (0, 0, 0.9), ROCK, 8, 5, (1.3, 1.0, 0.8)), sphere("body", 1.2, (0.1, 0, 3.3), ROCK, 8, 5, (0.75, 0.55, 1.9)), sphere("shoulder", 0.9, (0.1, 0, 4.8), ROCK_D, 7, 4, (1.15, 0.6, 0.5)), sphere("head", 0.75, (0.2, 0.05, 5.8), ROCK, 8, 5, (0.9, 0.85, 1.05))]
    p += [sphere("shawl", 0.9, (-0.2, -0.3, 4.1), ROCK_D, 7, 4, (1.1, 0.5, 0.9))]
    return p

def cape_hutmyo():
    """헛묘 한 기 1.6m: 시체 없는 봉분. 작은 흙 무덤 위에 돌 한 개와 마른 풀."""
    p = [sphere("mound", 0.8, (0, 0, 0.1), "#8A7A5A", 8, 4, (1.0, 1.3, 0.5)), box("stone", (0.3, 0.12, 0.45), (0, -0.95, 0.22), ROCK, rot=(0, 0, 0.08))]
    return p

def cape_new_grave():
    """새 무덤 한 기 2m(S-086 몸이 든 무덤): 흙이 아직 짙고 봉분이 높고 돌은 없다. 헛묘와 달리 막 쌓은 흙색."""
    p = [sphere("mound", 1.0, (0, 0, 0.15), "#5A4A36", 9, 5, (0.95, 1.4, 0.6)), box("marker", (0.08, 0.08, 0.7), (0, -1.5, 0.35), SEA_WOOD)]
    return p

def shoal_wreck():
    """난파선 반쯤 가라앉은 갑판 9×4m(B-10 싸움판): 기운 갑판 널과 부러진 돛대, 드러난 갈빗대. 위가 평평한 쪽이 싸움 자리."""
    r = random.Random(51); p = [box("deck", (7.0, 3.6, 0.15), (0, 0, 0.5), SEA_WOOD, rot=(0.0, 0.05, 0.0))]
    p += [box(f"dplank{i}", (7.0, 0.02, 0.17), (0, -1.6 + i * 0.4, 0.52), SEA_WOOD_D) for i in range(9)]
    p += [box(f"rib{i}", (0.18, 0.18, 2.2), (-3.0 + i * 1.5, 1.9, 1.2), SEA_WOOD_D, rot=(0.2, 0, 0)) for i in range(5)] + [box(f"ribL{i}", (0.18, 0.18, 1.6), (-3.0 + i * 1.5, -1.9, 1.0), SEA_WOOD_D, rot=(-0.25, 0, 0)) for i in range(4)]
    p += [cyl("mast", 0.18, 0.2, 3.6, (-1.0, 0, 0.5), SEA_WOOD_D, 6, rot=(0.0, 0.9, 0.2)), box("hatch", (1.2, 1.0, 0.1), (2.0, 0.2, 0.62), TAR)]
    p += [sphere(f"barn{i}", 0.08, (r.uniform(-3, 3), r.uniform(-1.6, 1.6), 0.6), "#B8B4A4", 4, 3) for i in range(12)]
    return p

def shoal_rock():
    """여울 바위 2.5m(B10-D3): 썰물 때 드러나는 따개비 붙은 바위. 바닥이 젖어 짙다."""
    r = random.Random(52); p = [sphere("rock", 1.2, (0, 0, 0.7), ROCK_D, 8, 5, (1.2, 0.9, 0.8)), sphere("rock2", 0.7, (1.1, 0.3, 0.3), ROCK, 6, 4)]
    p += [sphere(f"barn{i}", 0.06, (r.uniform(-.8, .8), r.uniform(-.6, .6), 0.9 + r.uniform(0, .5)), "#B8B4A4", 4, 3) for i in range(14)]
    return p

def shoal_plank():
    """갯골 널판 3×0.8m: B-10 천도 뒤 갯골 위에 걸리는 난파선 널판. 썰물에도 건널 수 있게 길게 걸친다."""
    p = [box("plank", (3.0, 0.8, 0.1), (0, 0, 0.3), SEA_WOOD), box("batten1", (0.1, 0.8, 0.05), (-0.8, 0, 0.38), SEA_WOOD_D), box("batten2", (0.1, 0.8, 0.05), (0.8, 0, 0.38), SEA_WOOD_D)]
    return p

def _deck_mat():
    """다리 상판 전용 재질 M_bridge_deck: 상판·난간 전부가 이 한 재질만 쓴다. 코드가 플레이어가 다리 밑에 들면 이 재질의 알파만 낮추면 되도록(다른 곳과 재질이 섞이지 않게) 이름을 따로 둔다."""
    import bpy
    m = bpy.data.materials.get("M_bridge_deck")
    if m is None:
        m = bpy.data.materials.new("M_bridge_deck"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = hex2rgb("#8C877A"); b.inputs["Roughness"].default_value = 0.9
    return m

def bridge_deck():
    """큰 다리 상판 한 칸 8×6m, 바닥에서 높이 3.6m: 돌 상판과 양옆 낮은 난간 벽(돌 기둥 여섯). 이름 규칙 bridge_deck*, 재질은 M_bridge_deck 하나뿐.
    기둥(bridge_pier*)과 따로 내보내므로 두 모델의 원점을 같은 자리(다리 중앙 바닥)에 놓으면 맞는다."""
    dm = _deck_mat(); p = [box("slab", (8.0, 6.0, 0.5), (0, 0, 3.35), dm)]
    p += [box("rail_n", (8.0, 0.35, 0.8), (0, 2.8, 3.9), dm), box("rail_s", (8.0, 0.35, 0.8), (0, -2.8, 3.9), dm)]
    p += [box(f"post{i}", (0.5, 0.5, 1.1), (-3.75 + i * 1.5, s * 2.8, 4.0), dm) for i in range(6) for s in (1, -1)]
    return p

def bridge_pier():
    """큰 다리 기둥·바닥 8×6m: 돌 다릿발 둘과 보, 아래 둔치 바닥. 이름 규칙 bridge_pier*. 상판 아래로 들어서는 B-11 싸움판 가림 없이 위가 비어 보이게 상판과 분리."""
    p = [box(f"pier{i}", (1.2, 4.0, 3.2), (-2.4 + i * 4.8, 0, 1.6), ROCK_D) for i in range(2)]
    p += [box("beam", (8.0, 1.0, 0.3), (0, 0, 3.0), ROCK), box("floor", (8.0, 6.0, 0.1), (0, 0, 0.05), "#6A645A")]
    return p

def tide_water():
    """썰물·밀물 물판 64×64m: 갯골·난파 여울용 물. 코드가 높이를 25분 주기로 오르내린다. 이름 규칙 tide_water*. 큰 강 물(river_water)과 같은 물 재질."""
    return [water_plane("tide_water", -32, -32, 64, 64, 0.0, deep=False)]

# ───────────────────────── ⑥ 도성 아랫마을 ─────────────────────────
CITY = "#8E8A80"; CITY_D = "#6E6A62"; SNOW = "#E8EAEE"; MAT = "#9A8A64"; CLOTH = "#B8AE96"

def city_wall():
    """도성 성벽 한 칸 8×2m, 높이 8m: 큰 반듯한 돌을 줄맞춰 쌓고 위에 여장(낮은 담) 열. 안쪽 도성은 못 들어가므로 벽만 높게. 눈이 위에 얇게 쌓였다."""
    r = random.Random(61); p = []; z = 0.0; row = 0
    while z < 7.2:
        rh = 0.9; x = -4.0 + (0.0 if row % 2 else 0.5)
        while x < 4.0 - 0.05:
            bw = min(1.4, 4.0 - x); p.append(box(f"b{row}_{len(p)}", (bw * 0.97, 2.0, rh * 0.96), (x + bw / 2, r.uniform(-0.03, 0.03), z + rh / 2), CITY if (row + len(p)) % 3 else CITY_D)); x += bw
        z += rh; row += 1
    p += [box(f"merlon{i}", (0.6, 0.8, 0.7), (-3.6 + i * 0.8, -0.5, 7.55), CITY_D) for i in range(10)] + [box("walk", (8.0, 1.0, 0.2), (0, 0.5, 7.3), CITY), box("snow", (8.0, 1.2, 0.08), (0, 0.4, 7.45), SNOW)]
    return p

def city_gate():
    """도성 닫힌 성문 + 문루 한 채 12×4m, 높이 13m: 큰 돌 문틀에 굳게 닫힌 두 짝 문(쇠 못), 위에 기와 문루. 못 들어가는 문이라 문짝을 또렷하게."""
    p = [box("pierL", (3.2, 4.0, 8.0), (-4.4, 0, 4.0), CITY), box("pierR", (3.2, 4.0, 8.0), (4.4, 0, 4.0), CITY), box("lintel", (12.0, 4.0, 1.4), (0, 0, 8.7), CITY_D)]
    p += [box("doorL", (2.7, 0.5, 6.2), (-1.4, -1.4, 3.2), "wood_dark"), box("doorR", (2.7, 0.5, 6.2), (1.4, -1.4, 3.2), "wood_dark"), box("bar", (5.8, 0.3, 0.25), (0, -1.75, 3.2), "iron")]
    p += [sphere(f"stud{i}", 0.09, (-2.3 + (i % 4) * 1.55, -1.7, 1.4 + (i // 4) * 1.4), "iron", 4, 3) for i in range(12)]
    p += [box("tower_floor", (11.0, 3.6, 0.3), (0, 0, 9.5), "wood"), box("tower_wall", (9.6, 3.0, 2.2), (0, 0, 10.7), "#C8BFA8")] + [cyl(f"pil{i}", 0.2, 0.2, 2.4, (-4.6 + i * 1.84, -1.7, 9.6), "pillar", 6) for i in range(6)]
    p += [prism("roof", 12.6, 5.0, 2.6, (0, 0, 11.8), "tile"), box("snow", (11.0, 1.0, 0.1), (0, 0, 14.35), SNOW)]
    return p

def city_skyline():
    """도성 안 기와지붕 실루엣 띠 16×30m(깊이 30m): 낮은 디테일의 지붕 선만. 성벽 너머로 살짝 보이게 낮은 지붕 열 줄. 벽과 안개 사이를 채운다."""
    r = random.Random(62); p = []
    for row in range(5):
        for i in range(7):
            w = r.uniform(3.0, 5.0); d = r.uniform(3.0, 5.0)
            cx = -7.5 + i * 2.5 + r.uniform(-.5, .5); cy = row * 6.0 + 2.0; zr = 9.0 + r.uniform(0, 1.2) + row * 0.3
            p.append(box(f"body{row}_{i}", (w * 0.9, d * 0.9, zr), (cx, cy, zr / 2), "#5A5650"))      # 아래는 어두운 몸통(보이지 않는 안쪽이라 낮은 디테일)
            p.append(prism(f"ro{row}_{i}", w, d, r.uniform(1.0, 1.8), (cx, cy, zr), "tile"))
    return p

def market_stall():
    """저잣 좌판 3×2m, 높이 2.6m: 평상 위에 천 차양. 위에 곡식·짚신 몇 점."""
    r = random.Random(63); p = [box("table", (3.0, 1.6, 0.9), (0, 0, 0.45), "wood")] + [cyl(f"pole{i}", 0.05, 0.05, 2.6, (x, y, 0), "wood_dark", 5) for i, (x, y) in enumerate(((-1.4, -0.9), (1.4, -0.9), (-1.4, 0.9), (1.4, 0.9)))]
    p += [box("awning", (3.4, 2.2, 0.06), (0, 0, 2.6), CLOTH, rot=(0.2, 0, 0))] + [sphere(f"goods{i}", 0.17, (-1.1 + i * 0.37, r.uniform(-0.4, 0.4), 1.0), "#B09468" if i % 2 else "#8A6A44", 5, 3) for i in range(7)]
    return p

def market_ricecake_stall():
    """떡장수 좌판 2.4m(떡시루 K-003 장면): 김 오르는 큰 시루 하나와 접시 둘, 낮은 평상."""
    p = [box("table", (2.4, 1.3, 0.8), (0, 0, 0.4), "wood"), cyl("sirut", 0.55, 0.6, 0.6, (-0.5, 0, 0.8), "#6A4A36", 9), cyl("sirut_lid", 0.6, 0.55, 0.08, (-0.5, 0, 1.4), "#4A3A2E", 9)]
    p += [cyl("plate1", 0.25, 0.25, 0.04, (0.6, -0.2, 0.8), "#D8D0BC", 8), cyl("plate2", 0.22, 0.22, 0.04, (0.8, 0.3, 0.8), "#D8D0BC", 8), sphere("cake1", 0.1, (0.6, -0.2, 0.9), "#F2EEE0", 5, 3), sphere("cake2", 0.1, (0.8, 0.3, 0.9), "#F2EEE0", 5, 3)]
    return p

def market_jige():
    """짐꾼 지게 한 벌 1.2m(B-12 곰 행렬 소품 S-104): 세워 둔 지게와 묶은 짐 보따리."""
    p = [cyl("legL", 0.04, 0.04, 1.4, (-0.25, 0, 0), "wood_dark", 5, rot=(0, 0.12, 0)), cyl("legR", 0.04, 0.04, 1.4, (0.25, 0, 0), "wood_dark", 5, rot=(0, -0.12, 0)), box("bar1", (0.6, 0.05, 0.05), (0, 0, 0.5), "wood_dark"), box("bar2", (0.55, 0.05, 0.05), (0, 0, 1.0), "wood_dark"), box("pack", (0.5, 0.35, 0.45), (0, -0.2, 0.8), "#9A8A64")]
    return p

def market_lantern_string():
    """저잣 등불 줄 6m: 장대 둘 사이 줄에 매단 등 일곱. 밤에 등불이 많다(혼불과 겹치지 않게 주황 끝 따뜻한 노랑)."""
    p = [cyl("poleL", 0.06, 0.06, 4.0, (-3.0, 0, 0), "wood_dark", 5), cyl("poleR", 0.06, 0.06, 4.0, (3.0, 0, 0), "wood_dark", 5)]
    p += [box(f"lamp{i}", (0.22, 0.22, 0.3), (-2.4 + i * 0.8, 0, 3.6 - 0.35 * math.sin(i / 6 * math.pi)), WARM) for i in range(7)] + [limb("rope", (-3.0, 0, 3.9), (3.0, 0, 3.9), 0.012, 0.012, "#4A3A2E", 4)]
    return p

def market_tile_house():
    """저잣 기와집(반 2층) 7×5m, 높이 6.4m: 아래층 가게 문이 열려 있고 위에 작은 누마루."""
    p = [box("floor", (7.0, 5.0, 0.4), (0, 0, 0.2), CITY_D), box("wall1", (6.4, 4.4, 2.4), (0, 0, 1.6), "#CFC7B0"), box("wall2", (5.0, 3.6, 1.8), (0, 0.4, 3.7), "#CFC7B0"), prism("roof1", 7.6, 5.6, 1.1, (0, 0, 2.8), "tile"), prism("roof2", 6.0, 4.4, 1.4, (0, 0.4, 4.6), "tile")]
    p += [box("shopdoor", (3.0, 0.1, 1.8), (0, -2.25, 1.3), "wood_dark"), box("lamp", (0.2, 0.2, 0.3), (-2.4, -2.5, 2.3), WARM)]
    return p

def shack_a():
    """움막촌 판잣집 A 3×3m, 높이 2.4m: 얇은 널과 천 지붕, 기운 벽. 검은여울 역병 피해 올라온 사람들의 집."""
    r = random.Random(64); p = [box(f"pl{i}", (0.34, 0.06, 1.7), (-1.3 + i * 0.35, -1.4, 1.0 + r.uniform(-.05, .05)), "#8A7A5E" if i % 2 else "#74664E", rot=(0, 0, r.uniform(-.05, .05))) for i in range(8)]
    p += [box("back", (3.0, 0.1, 1.7), (0, 1.4, 1.0), "#74664E"), box("sideL", (0.1, 2.8, 1.7), (-1.4, 0, 1.0), "#8A7A5E"), box("sideR", (0.1, 2.8, 1.7), (1.4, 0, 1.0), "#74664E"), box("roof", (3.6, 3.4, 0.08), (0, 0, 1.95), CLOTH, rot=(0.12, 0, 0)), box("door", (0.8, 0.06, 1.3), (0.5, -1.45, 0.7), "wood_dark")]
    return p

def shack_b():
    """움막촌 판잣집 B 4×3m, 높이 2.6m: 기둥 넷 위에 짚 지붕을 얹고 앞이 트인 뒤 움막. 거적 문."""
    p = [cyl(f"pole{i}", 0.07, 0.07, 2.2, (x, y, 0), "wood_dark", 5) for i, (x, y) in enumerate(((-1.8, -1.3), (1.8, -1.3), (-1.8, 1.3), (1.8, 1.3)))]
    p += [prism("roof", 4.6, 3.6, 1.0, (0, 0, 2.2), THATCH), box("back", (3.6, 0.08, 2.0), (0, 1.3, 1.1), MAT), box("matdoor", (1.0, 0.05, 1.5), (-0.6, -1.3, 0.85), MAT)]
    return p

def shack_well():
    """움막촌 우물 1.6m: 돌 우물에 두레박과 낮은 지붕 틀."""
    p = [cyl("ring", 0.8, 0.8, 0.7, (0, 0, 0), CITY, 9), cyl("water", 0.55, 0.55, 0.02, (0, 0, 0.55), "#2A3038", 9), cyl("postL", 0.05, 0.05, 1.6, (-0.8, 0, 0), "wood_dark", 5), cyl("postR", 0.05, 0.05, 1.6, (0.8, 0, 0), "wood_dark", 5), cyl("beam", 0.04, 0.04, 1.8, (-0.9, 0, 1.6), "wood_dark", 5, rot=(0, 1.5708, 0)), box("bucket", (0.2, 0.2, 0.22), (0.1, 0, 1.2), "wood")]
    return p

def city_gatekeeper_hut():
    """문지기 막 3.5×3m, 높이 3.2m(N-602 아들 문지기): 성벽 곁 작은 막, 앞에 방 붙이는 판."""
    p = [box("hut", (3.5, 3.0, 2.0), (0, 0, 1.0), "#B4A98A"), prism("roof", 4.1, 3.6, 1.2, (0, 0, 2.0), "tile"), box("door", (0.9, 0.08, 1.4), (0, -1.55, 0.75), "wood_dark"), box("board", (1.2, 0.08, 1.6), (2.2, -1.2, 1.4), "wood"), box("notice", (0.9, 0.02, 1.1), (2.2, -1.25, 1.4), "#E6DFC8")]
    return p

def city_gate_inn():
    """성문 밖 주막 6×4.5m, 높이 3.8m(N-603 노파): 이엉 지붕 낮은 집, 밤엔 등 하나만. 앞 평상."""
    p = [box("floor", (6.0, 4.5, 0.4), (0, 0, 0.2), CITY_D), box("wall", (5.4, 3.9, 1.9), (0, 0.2, 1.35), "#BDB293"), prism("roof", 6.6, 5.2, 1.6, (0, 0, 2.3), THATCH), box("bench", (2.2, 0.7, 0.1), (-1.2, -2.7, 0.55), "wood"), box("door", (1.0, 0.1, 1.5), (1.4, -1.75, 1.15), "wood_dark"), box("snow", (6.4, 4.8, 0.06), (0, 0, 3.55), SNOW), box("lamp", (0.2, 0.2, 0.3), (2.3, -2.2, 2.2), WARM)]
    return p

def city_pit_grave():
    """팻말 없는 구덩이 무덤(B-12 마당) 3×2m: 얕게 파인 흙 구덩이와 눈 덮인 가장자리, 팻말은 없다. 한쪽에 흩어진 흙."""
    p = [box("rim", (3.2, 2.4, 0.12), (0, 0, 0.06), "#6A5E4A"), box("pit", (2.6, 1.8, 0.05), (0, 0, 0.02), "#2E2822"), box("spoil", (1.0, 0.7, 0.3), (1.8, 0.2, 0.15), "#5E5240"), box("snow1", (1.2, 0.7, 0.06), (-1.9, 0.9, 0.12), SNOW), box("snow2", (0.9, 0.6, 0.06), (-1.6, -1.0, 0.12), SNOW)]
    return p

def snow_patch():
    """눈 쌓인 얼룩 바닥 판 6×6m: 성문 밖 눈밭. 눈 녹은 자리(주막 앞)는 이 판을 빼서 표현한다."""
    r = random.Random(65); p = [box(f"sn{i}", (r.uniform(1.5, 3.0), r.uniform(1.5, 3.0), 0.05), (r.uniform(-2, 2), r.uniform(-2, 2), 0.025 + i * 0.002), SNOW) for i in range(6)]
    return p

def river_hut_mat():
    """다리 밑 거적 움막 2.5m(N-601 쥐똥이 거적): 다리 기둥에 기댄 거적 지붕 낮은 움막."""
    p = [box("back", (2.5, 0.1, 1.2), (0, 0.9, 0.7), MAT, rot=(0.2, 0, 0)), box("roof", (2.7, 2.2, 0.06), (0, 0, 1.25), MAT, rot=(-0.15, 0, 0)), box("floor", (2.3, 1.8, 0.04), (0, 0, 0.03), "#6A5E48"), cyl("pole", 0.05, 0.05, 1.3, (-1.2, -0.9, 0), "wood_dark", 5), cyl("pole2", 0.05, 0.05, 1.3, (1.2, -0.9, 0), "wood_dark", 5)]
    return p

def river_bank():
    """큰내 둑 4m: 돌과 흙을 쌓은 둑 한 칸. 위에 마른 풀."""
    r = random.Random(66); p = [box("bank", (4.0, 1.4, 0.7), (0, 0, 0.35), "#7A6E58"), box("top", (3.8, 1.0, 0.1), (0, 0, 0.75), "#8A7E66")] + [sphere(f"st{i}", r.uniform(0.15, 0.3), (r.uniform(-1.8, 1.8), -0.7, 0.2), ROCK, 5, 3) for i in range(5)]
    return p

def cliff_edge_wall():
    """벼랑 가장자리 낮은 돌담 4m, 높이 0.8m: 1막·⑥ 남쪽 끝에서 걸어 내려가지 못하게 하는 보이는 막(기획 요청). 이끼와 풀이 낀 거친 돌."""
    r = random.Random(71); p = []
    for i in range(7): p.append(box(f"st{i}", (r.uniform(0.5, 0.65), 0.55, r.uniform(0.5, 0.8)), (-1.8 + i * 0.6 + r.uniform(-.03, .03), r.uniform(-.04, .04), 0.35), ROCK if i % 2 else ROCK_D, rot=(0, 0, r.uniform(-.06, .06))))
    p += [sphere(f"moss{i}", 0.12, (r.uniform(-1.7, 1.7), -0.2, 0.7), "#58704A", 5, 3, (1, 1, 0.5)) for i in range(4)]
    return p

KIT = [(f.__name__, f) for f in (harbor_pier, harbor_gauge_post, harbor_boat, harbor_net_frame, harbor_net_pile, harbor_jar, harbor_gaekju_house, harbor_inn, harbor_lamp_hut,
       salt_pan, salt_pile, salt_warehouse, salt_dike, cape_waiting_rock, cape_hutmyo, cape_new_grave, shoal_wreck, shoal_rock, shoal_plank, bridge_deck, bridge_pier, tide_water, city_wall, city_gate, city_skyline, market_stall, market_ricecake_stall, market_jige, market_lantern_string, market_tile_house, shack_a, shack_b, shack_well, city_gatekeeper_hut, city_gate_inn, city_pit_grave, snow_patch, river_hut_mat, river_bank, cliff_edge_wall)]
LIGHTS = {"market_lantern_string": ("Light_market_lamps", (0, 0, 3.4), WARM, 1.4, 9.0, True), "market_tile_house": ("Light_market_house", (-2.4, -2.5, 2.3), WARM, 0.9, 6.0, True), "city_gate_inn": ("Light_gate_inn", (2.3, -2.2, 2.2), WARM, 0.8, 5.0, True), "harbor_gaekju_house": ("Light_gaekju", (0, -3.5, 2.5), WARM, 1.0, 7.0, True), "harbor_inn": ("Light_inn", (2.0, -2.2, 2.2), WARM, 1.0, 6.0, True), "harbor_lamp_hut": ("Light_lamp_hut", (2.2, 0, 4.7), WARM, 1.4, 14.0, True)}

def build(name, fn):
    reset(); o = join(name, fn()); lo, hi = bounds(o)
    if name in LIGHTS: n, pos, col, it, rg, fl = LIGHTS[name]; light_empty(o, n, pos, col, intensity=it, range_m=rg, flicker=fl)
    export(o, os.path.join(OUT, "act3", f"{name}.glb"))
    return {"name": name, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}

if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "act3"), exist_ok=True)
    want = sys.argv[1:]; res = [build(k, f) for k, f in KIT if not want or k in want]
    for r in res: print(r)
    if not want:
        json.dump(res, open(os.path.join(OUT, "act3", "_report_act3.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        for i, (k, f) in enumerate(KIT): o = join(k, f()); o.location = ((i % 6 - 2.5) * 17.0, -(i // 6) * 14.0, 0)
        setup_render(100, (0, -35.0, 2.0), elev=50, size=(1500, 900), ground_size=160); bpy.context.scene.cycles.samples = 24
        render(os.path.join(OUT, "previews", "act3_harbor_50deg.png"))
