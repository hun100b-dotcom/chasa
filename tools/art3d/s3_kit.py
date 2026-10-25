"""시즌 3 아래층 키트(약 30종). 실행: python3 s3_kit.py [이름 ...]
규약은 s2_kit과 같다(원점=바닥 한가운데, 정면=-Y, 1단위=1m, 재질은 색만, 불빛은 발광 면 + Light_ 빈 오브젝트). 출력: assets3d/s3/ (접두 s3_).
아래층은 위층 지형·타일을 다시 쓰고 조명·색만 바꾸므로(SCENARIO-MASTER §S-1) 이 키트는 '아래층에만 있는 것'만 만든다: 못 묻힌 몸이 누운 자리, 흙·석회·먹·물의 단면, 보스 마당 장치.
윤리 규칙(서사 season3_outline world.ethics): 유해는 '누운 그림자 · 흙과 뼈의 단면 · 감각 한 줄'로만. 훼손 묘사 없음 → 몸은 납작한 어두운 윤곽(s3_lying_shadow)으로만 그린다. 글자 없음(획 모양 상자만).
색 뼈대: 젖은 흙(#3E382E)·진흙(#5A4C3A)·석회(#D8D4C6)·먹(#1E1C24)·물빛 회청(#2E3C44)·실 흰빛(#B8C4C0)·목재(#5A4636). 쿼터뷰 가림 규칙: 보스 마당 안에는 높은 것(1.5m 초과)을 두지 않는다(버팀목 2.6m만 예외, 기획 지정)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
SOIL = "#3E382E"; MUD = "#5A4C3A"; LIME = "#D8D4C6"; INK = "#1E1C24"; WATER = "#2E3C44"; THREAD = "#B8C4C0"; WOOD = "#5A4636"; WOOD_D = "#3E3024"; STONE = "#6A6862"; STONE_D = "#4A4844"; BONE = "#CFC8B4"; ROPE = "#9A8C6A"; EMBER = "#E8683A"

def lying_shadow():
    """누운 그림자 1.8×0.5m: 못 묻힌 몸. 납작하게 어두운 윤곽 하나(머리 쪽이 약간 둥글다). 얼굴·손발 없음."""
    return [box("body", (0.46, 1.5, 0.05), (0, 0, 0.0), "#1E1A16"), sphere("head", 0.2, (0, 0.8, 0.0), "#1E1A16", 6, 3, (1, 1, 0.2))]
def lying_shadow_pair():
    """나란히 누운 그림자 둘 1.2×1.8m: 어깨를 맞대고 누웠다."""
    return [box("b0", (0.46, 1.5, 0.05), (-0.3, 0, 0.0), "#1E1A16"), sphere("h0", 0.2, (-0.3, 0.8, 0.0), "#1E1A16", 6, 3, (1, 1, 0.2)), box("b1", (0.44, 1.4, 0.05), (0.3, 0.05, 0.0), "#262018"), sphere("h1", 0.19, (0.3, 0.8, 0.0), "#262018", 6, 3, (1, 1, 0.2))]
def linked_arms_eleven():
    """엮인 팔 열하나 지름 6m(둑 밑): 열한 몸이 팔을 엮어 둥글게 누웠고 열두째 자리 하나가 비었다(연한 윤곽만). 벽 아님, 높이 0.06m."""
    p = []
    for i in range(12):
        a = i / 12 * math.tau; x, y = math.cos(a) * 2.2, math.sin(a) * 2.2
        if i == 11: p += [box("empty_slot", (0.5, 1.5, 0.02), (x, y, 0.0), "#4A443A", rot=(0, 0, a)), box("slot_edge", (0.6, 1.6, 0.015), (x, y, -0.005), "#6A6252", rot=(0, 0, a))]; continue
        p += [box(f"b{i}", (0.46, 1.5, 0.05), (x, y, 0.0), "#1E1A16", rot=(0, 0, a)), limb(f"link{i}", (x, y, 0.04), (math.cos(a + 0.52) * 2.2, math.sin(a + 0.52) * 2.2, 0.04), 0.06, 0.06, "#2A241C", 4)]
    return p
def half_stake():
    """박다 만 말뚝 셋(둑 밑) 1.1m: 반쯤 박힌 굵은 말뚝이 기울어 있다. 망치 자국."""
    return [cyl(f"st{i}", 0.12, 0.14, 1.1 - 0.2 * i, (-0.8 + i * 0.8, 0, 0), WOOD_D, 6, rot=(0.12 * (i - 1), 0.1 * (i - 1), 0)) for i in range(3)] + [box("mallet", (0.3, 0.14, 0.14), (1.4, -0.3, 0.07), WOOD)]
def mud_pool():
    """흙탕 웅덩이 지름 3m: 납작한 진흙 원판. 이동 둔화 표시용 바닥 장판 바탕."""
    return [cyl("pool", 1.5, 1.5, 0.03, (0, 0, 0.0), "#4A3E30", 12), cyl("pool_in", 1.0, 1.0, 0.035, (0, 0, 0.0), "#3A3026", 10)]
def capsized_boat():
    """뒤집힌 나룻배 4.2×1.5m(B-21 마당): 바닥이 위로 오른 낡은 배, 늑골 둘, 판자가 한두 장 빠졌다. 높이 0.9m."""
    return [box("hull", (1.5, 4.2, 0.55), (0, 0, 0.28), WOOD), box("hull_top", (1.1, 3.8, 0.3), (0, 0, 0.68), WOOD_D), box("keel", (0.14, 3.6, 0.1), (0, 0, 0.9), "#34281E"), box("rib0", (1.7, 0.1, 0.1), (0, -1.2, 0.45), "#34281E"), box("rib1", (1.7, 0.1, 0.1), (0, 1.2, 0.45), "#34281E"), box("loose", (0.4, 1.2, 0.04), (1.1, 0.4, 0.03), WOOD, rot=(0, 0, 0.5))]
def wreck_ribs():
    """난파선 늑골 5m(⑤ 아래): 짐승 뼈처럼 서 있는 배의 갈비뼈 여섯 쌍. 높이 2.2m. 마당 밖 가장자리용."""
    p = [box("keel", (0.3, 5.0, 0.25), (0, 0, 0.15), WOOD_D)]
    for i in range(6):
        y = -2.3 + i * 0.92
        for sx in (1, -1): p += [limb(f"r{i}{sx}", (sx * 0.1, y, 0.2), (sx * 1.0, y, 1.5), 0.1, 0.07, WOOD, 5), limb(f"r2{i}{sx}", (sx * 1.0, y, 1.5), (sx * 0.8, y, 2.2 - 0.05 * i), 0.07, 0.05, WOOD, 5)]
    return p
def sea_cave_rock():
    """바다굴 바위 3×2m(⑤ 마당): 젖어 검은 둥근 바위, 위에 따개비 자국(흰 점)과 해초."""
    r = random.Random(3); p = [sphere("rock", 1.3, (0, 0, 0.0), "#2E3236", 8, 5, (1.1, 0.8, 0.6))]
    p += [sphere(f"barn{i}", 0.05, (r.uniform(-.9, .9), r.uniform(-.5, .5), r.uniform(.3, .75)), "#CFC8B4", 4, 3) for i in range(8)] + [limb(f"weed{i}", (-0.6 + i * 0.5, -0.4, 0.5), (-0.65 + i * 0.5, -0.5, 0.15), 0.05, 0.02, "#3A4A3A", 4) for i in range(3)]
    return p
def hanging_threads():
    """줄 밑의 실 다발 높이 3.4m(⑦ 줄 밑): 위(위층 줄 선 혼의 발목)에서 내려온 가는 실 일곱 가닥과 맨 위 발바닥 납작판. 실 굵기 0.02m라 시야를 가리지 않는다."""
    r = random.Random(4); p = []
    for i in range(7): p += [limb(f"th{i}", (r.uniform(-.3, .3), r.uniform(-.3, .3), 3.4), (r.uniform(-.1, .1), r.uniform(-.1, .1), 0.1), 0.018, 0.012, THREAD, 3), box(f"sole{i}", (0.1, 0.24, 0.02), (r.uniform(-.3, .3), r.uniform(-.3, .3), 3.4), "#4A4640")]
    return p
def name_tag_thread():
    """이름표 실 높이 1.2m: 땅에서 솟은 가는 실 끝에 이름표(글자 없는 종이 쪽지) 하나."""
    return [limb("th", (0, 0, 0.0), (0.05, 0, 1.1), 0.02, 0.015, THREAD, 3), box("tag", (0.22, 0.02, 0.32), (0.05, 0, 1.2), "#E4E0D4", rot=(0, 0.2, 0.1)), box("tag_dark", (0.06, 0.022, 0.1), (0.05, -0.002, 1.2), INK)]
def tomb_wall():
    """큰 무덤 단면 벽 한 칸 6×2m, 높이 3.5m(③ 마당 바깥 벽): 흙과 흰 돌·뼛조각이 층층이 박힌 단면. 마당 밖 가장자리에만."""
    r = random.Random(5); p = [box(f"layer{i}", (6.0, 2.0, 0.7), (0, 0, 0.35 + i * 0.7), [SOIL, MUD, "#4A4034", "#352E26", MUD][i]) for i in range(5)]
    p += [cyl(f"bone{i}", 0.03, 0.03, r.uniform(0.2, 0.5), (r.uniform(-2.6, 2.6), -1.02, r.uniform(0.4, 3.2)), BONE, 5, rot=(1.57, 0, r.uniform(0, 3))) for i in range(12)]
    p += [box(f"root{i}", (0.06, 0.06, r.uniform(0.6, 1.4)), (r.uniform(-2.8, 2.8), -1.03, r.uniform(2.6, 3.4)), "#4A3A2A", rot=(0, 0, r.uniform(-.5, .5))) for i in range(5)]
    return p
def fallen_standards():
    """쓰러진 깃대 둘 X자 3.2m(B-24 눕히기): 두 기수가 내려놓은 깃대가 X로 겹쳐 누웠다. 헝겊 둘(한쪽은 번호 획 상자, 한쪽은 소매 헝겊)."""
    return [cyl("poleA", 0.05, 0.04, 3.2, (-1.4, -1.2, 0.05), "#5A4430", 6, rot=(0, 1.57, 0.6)), cyl("poleB", 0.05, 0.04, 3.2, (-1.4, 1.2, 0.05), "#5A4430", 6, rot=(0, 1.57, -0.6)), box("flagA", (0.7, 0.5, 0.02), (0.6, 0.9, 0.06), "#7A2A2A", rot=(0, 0, 0.5)), box("flagB", (0.7, 0.5, 0.02), (0.6, -0.9, 0.06), "#C8BFA0", rot=(0, 0, -0.5))]
def rusty_cart():
    """녹슨 수레 2.2×1.0m(④ 물 찬 갱도): 바퀴 둘 달린 광차. 광석 대신 흙이 반쯤. 높이 0.9m."""
    return [box("bed", (2.0, 0.9, 0.5), (0, 0, 0.5), "#5A3A2A"), box("soil", (1.8, 0.8, 0.1), (0, 0, 0.78), SOIL)] + [cyl(f"wheel{i}", 0.3, 0.3, 0.08, (-0.7 + i * 1.4, 0.52, 0.3), "#4A3226", 8, rot=(1.57, 0, 0)) for i in range(2)] + [cyl(f"wheelB{i}", 0.3, 0.3, 0.08, (-0.7 + i * 1.4, -0.52, 0.3), "#4A3226", 8, rot=(1.57, 0, 0)) for i in range(2)]
def mine_beam():
    """버팀목 높이 2.6m(B-25 마당, 셋): 굵은 기둥과 가로 대들보. 곁 2m 안에서 버티는 자리를 바닥 고리로 표시한다."""
    return [cyl("post", 0.15, 0.13, 2.6, (0, 0, 0), "#6A4E34", 7), box("cap", (0.9, 0.18, 0.12), (0, 0, 2.6), WOOD_D), box("wedge", (0.3, 0.3, 0.1), (0, 0, 0.05), WOOD_D), cyl("hold_ring", 2.0, 2.0, 0.015, (0, 0, 0.0), "#8A7448", 18)]
def mine_beam_broken():
    """꺾인 버팀목 1.6m: 가운데서 꺾여 기울어졌다(20초 뒤 꺾인 상태)."""
    return [cyl("low", 0.15, 0.14, 1.0, (0, 0, 0), "#6A4E34", 7), cyl("high", 0.13, 0.12, 1.5, (0.5, 0, 0.7), "#6A4E34", 7, rot=(0, 1.0, 0)), box("splinter", (0.1, 0.1, 0.3), (0.1, 0, 0.9), "#C8B890", rot=(0, 0.3, 0))]
def rubble_pile():
    """무너진 돌흙더미 2.4×2m(④ 막장 앞): 흙과 돌이 쌓여 길을 막았다(쌓인 돌). 높이 1.2m."""
    r = random.Random(6); p = [sphere("mound", 1.2, (0, 0, 0.0), SOIL, 7, 4, (1.0, 0.9, 0.55))]
    p += [box(f"stone{i}", (r.uniform(.2, .5), r.uniform(.2, .45), r.uniform(.15, .35)), (r.uniform(-.9, .9), r.uniform(-.7, .7), r.uniform(.1, .6)), STONE if i % 2 else STONE_D, rot=(r.uniform(0, .5), r.uniform(0, .5), r.uniform(0, 3))) for i in range(10)]
    return p
def lime_band():
    """석회 띠 폭 1.2m, 길이 8m(② 구덩이): 흙을 가르는 흰 석회 줄. 발자국이 남는 것처럼 살짝 도드라진 판. 높이 0.04m."""
    return [box("band", (8.0, 1.2, 0.04), (0, 0, 0.0), LIME)] + [box(f"print{i}", (0.18, 0.34, 0.015), (-3.4 + i * 1.0, 0.2 * ((-1) ** i), 0.045), "#BAB6A8") for i in range(7)]
def fallen_medicine_chest():
    """내려앉은 약장 1.6×0.6m(② 역병막 마루 밑): 마루 널을 뚫고 박힌 서랍장. 서랍 몇이 열렸다(감초 밑 이름 자리). 높이 1.4m."""
    p = [box("chest", (1.4, 0.6, 1.3), (0, 0, 0.65), "#5A3A2A", rot=(0.12, 0, 0.1))] + [box(f"drawer{i}", (0.28, 0.02, 0.2), (-0.5 + (i % 4) * 0.34, -0.31, 0.3 + (i // 4) * 0.3), "#3E2A1E") for i in range(8)]
    p += [box("open_drawer", (0.28, 0.3, 0.16), (0.17, -0.5, 0.58), "#4A3224"), box("floorplank0", (1.4, 0.2, 0.05), (-0.9, 0.8, 0.05), WOOD, rot=(0, 0, 0.4)), box("floorplank1", (1.2, 0.2, 0.05), (0.9, 0.9, 0.05), WOOD, rot=(0, 0, -0.3))]
    return p
def blank_stones_row():
    """빈 돌 열 3m(B-26 눕힌 뒤): 아무것도 새기지 않은 작은 돌 다섯이 나란히 선다. 높이 0.5m."""
    return [box(f"bs{i}", (0.34, 0.14, 0.5 - 0.03 * (i % 2)), (-1.2 + i * 0.6, 0, 0.25), "#B8B4A4") for i in range(5)]
def unmarked_mound():
    """팻말 없는 흙무덤 지름 2m(⑥ 아래): 팻말도 비석도 없는 낮은 봉분. 높이 0.5m."""
    return [sphere("mound", 1.0, (0, 0, 0.0), "#6A5A44", 8, 4, (1, 1, 0.5)), box("fresh", (0.8, 0.5, 0.02), (0.1, -0.5, 0.3), "#4A3E30", rot=(0.4, 0, 0))]
def bridge_footing():
    """다리 기초 돌덩이 3×2m(⑥ 다리 밑): 다리를 받치던 큰 돌. 돌 사이에 누운 그림자 둘. 높이 1.4m."""
    return [box("stone0", (1.6, 1.6, 1.4), (-0.7, 0, 0.7), STONE), box("stone1", (1.4, 1.5, 1.1), (0.9, 0.1, 0.55), STONE_D), box("lintel", (3.0, 0.6, 0.3), (0.1, 0, 1.5), STONE), box("shadow0", (0.4, 1.3, 0.04), (0.2, -1.4, 0.0), "#1E1A16"), box("shadow1", (0.4, 1.3, 0.04), (0.8, -1.4, 0.0), "#262018")]
def floor_strokes():
    """바닥 글씨 판 4×4m(B-27 마당): 흙바닥에 쓰인 글씨의 획 모양(읽히는 글자는 없다). 높이 0.01m."""
    r = random.Random(7); return [box("patch", (4.0, 4.0, 0.012), (0, 0, 0.0), "#4A4034")] + [box(f"stroke{i}", (r.uniform(0.2, 0.7), 0.06, 0.012), (r.uniform(-1.7, 1.7), r.uniform(-1.7, 1.7), 0.01), "#1E1C24", rot=(0, 0, r.uniform(0, 3.14))) for i in range(26)]
def ink_silt_islet():
    """먹 앙금 진흙 덩이 지름 3m(⑧ 아래): 검은 진흙이 둥글게 솟은 곳. 이동 −15% 바닥 표시. 높이 0.25m."""
    return [sphere("silt", 1.5, (0, 0, 0.0), "#14121A", 9, 4, (1, 1, 0.16)), sphere("ripple", 1.1, (0, 0, 0.02), "#1E1C24", 8, 3, (1, 1, 0.12))]
def quarters_bunk():
    """서리 숙사 침상 2.4×1.2m(⑧ 숙사 밑): 일하다 잠든 자세로 앉은 그림자가 책상에 엎드려 있다. 높이 1.0m."""
    return [box("bench", (2.2, 0.8, 0.4), (0, 0, 0.2), WOOD_D), box("desk", (1.4, 0.6, 0.06), (0, -0.3, 0.8), WOOD), box("slumped", (0.5, 0.4, 0.5), (0, 0.0, 0.65), "#1E1A16", rot=(0.4, 0, 0)), box("brush", (0.04, 0.3, 0.02), (0.4, -0.4, 0.86), INK)]
def ondol_tile():
    """구들 칸 한 장 2×2m(B-29 방 바닥): 구들장. 9장을 3×3으로 깐다. 높이 0.08m."""
    return [box("slab", (1.96, 1.96, 0.08), (0, 0, 0.0), "#5A5246"), box("crack", (1.6, 0.04, 0.085), (0, 0.2, 0.0), "#2E2A24")]
def ondol_hot_tile():
    """뜨거운 구들 칸 2×2m(B-29 2단계): 아궁이 불이 올라와 가장자리가 붉게 빛난다. 발광 면(붉은 틈) + Light_ 하나. 예고 1.2초 동안 켠다."""
    return [box("slab", (1.96, 1.96, 0.08), (0, 0, 0.0), "#5A5246")] + [box(f"glow{i}", (1.8, 0.1, 0.09), (0, -0.8 + i * 0.53, 0.0), mat(EMBER, 1.8)) for i in range(4)]
def offering_set():
    """사잣밥 한 벌 0.9×0.6m(⑨ 집집의 머리맡): 밥 그릇·짚신·엽전이 낮은 상 위에 놓였다. 식은 밥."""
    return [box("tray", (0.9, 0.5, 0.04), (0, 0, 0.3), WOOD)] + [cyl(f"leg{i}", 0.03, 0.03, 0.3, (-0.38 + 0.76 * (i % 2), -0.18 + 0.36 * (i // 2), 0), WOOD_D, 4) for i in range(4)] + [cyl("bowl", 0.1, 0.07, 0.1, (-0.25, 0, 0.34), "#E8E4D8", 8), sphere("rice", 0.08, (-0.25, 0, 0.42), "#F4F0E4", 6, 4, (1, 1, 0.6)), box("sandal", (0.1, 0.24, 0.03), (0.05, 0, 0.36), "#A89868"), cyl("coin", 0.04, 0.04, 0.01, (0.3, 0, 0.35), "#B09468", 8)]
def seal_floor_mark():
    """인장 굴 바닥 붉은 자국 3×0.6m(⑨ 아래): 이마 높이 붉은 자국이 바닥까지 이어졌다. 납작한 붉은 띠와 번진 가장자리. 높이 0.02m."""
    return [box("mark", (3.0, 0.6, 0.02), (0, 0, 0.0), "#7A2A24"), box("edge", (3.3, 0.8, 0.012), (0, 0, -0.004), "#4A2A24")]
def chain_root():
    """사슬 무덤 밑 뿌리 높이 1.4m(⑩ 아래): 땅에서 사슬이 내려와 흙 속 어딘가로 사라진다. 사슬 끝은 흙 위로 손목 모양 돌기(손은 그리지 않음)."""
    p = [sphere("mound", 0.9, (0, 0, 0.0), "#4A4034", 7, 4, (1, 1, 0.45))] + [box(f"l{i}", (0.1, 0.03, 0.14), (0, 0, 1.4 - i * 0.12), "iron", rot=(0, (i % 2) * 1.57, 0)) for i in range(10)]
    p += [cyl("cuff", 0.12, 0.1, 0.1, (0.0, -0.1, 0.18), "iron", 6, rot=(0.8, 0, 0))]
    return p
def well_wall():
    """우물 밑 벽 한 칸 폭 5m 호, 높이 1.4m(B-30 마당 둘레): 돌을 쌓은 둥근 벽의 일부. 벽을 타고 물이 흐른 자국(물 오름 표시줄 3개). 마당 안쪽이 -Y."""
    p = [box("wall", (5.0, 0.8, 1.2), (0, 0.4, 0.6), STONE_D), box("coping", (5.2, 1.0, 0.2), (0, 0.4, 1.3), STONE)]
    p += [box(f"stream{i}", (0.1, 0.02, 1.1), (-1.8 + i * 1.8, -0.01, 0.65), "#4A6A7A") for i in range(3)] + [box(f"glow{i}", (0.08, 0.02, 0.5), (-1.8 + i * 1.8, -0.02, 0.9), mat("#7FB0C0", 0.6)) for i in range(3)]
    return p
def well_rope():
    """늘어진 새끼줄 높이 6m(B-30 2단계): 우물 위에서 내려온 굵은 새끼줄. 맨 위는 우물 주둥이(그림 밖)로 이어진다. 굵기 0.1m라 가림 적음."""
    return [limb("rope", (0, 0, 6.0), (0.1, 0.05, 0.4), 0.07, 0.06, ROPE, 5), box("knot", (0.18, 0.18, 0.14), (0.08, 0.03, 0.9), ROPE), cyl("bucket", 0.18, 0.22, 0.24, (0.12, 0.05, 0.2), WOOD, 8)]
def torch_in_water():
    """물속에서 타는 횃불 높이 1.8m(B-31 마당): 가라앉은 말뚝 위 횃불. 물속인데 꺼지지 않는다 → 발광 불꽃 + Light_ 하나(따뜻한 색)."""
    return [cyl("stake", 0.07, 0.09, 1.5, (0, 0, 0), "#3E3024", 6), cyl("wrap", 0.1, 0.09, 0.3, (0, 0, 1.4), "#2A2018", 7), sphere("flame", 0.16, (0, 0, 1.78), mat("#FFB347", 2.0), 6, 5, (1, 1, 1.7))]
def barley_sheaf():
    """떠 있는 보릿단 0.6m(B-31, 개똥이의 보릿단): 묶음 하나가 물 위에 떠 있다."""
    return [cyl("sheaf", 0.2, 0.13, 0.55, (0, 0, 0.0), "#B8A468", 8, rot=(0.2, 0, 0.3)), box("band", (0.34, 0.34, 0.05), (0, 0, 0.0), ROPE, rot=(0.2, 0, 0.3))] + [limb(f"ear{i}", (0, 0, 0.5), (math.cos(i) * 0.14, math.sin(i) * 0.14, 0.7), 0.02, 0.01, "#C8B070", 3) for i in range(6)]
def dawn_flood_line():
    """새벽 물 차오름 경계선 폭 6m: 물이 올라올 선을 알리는 물빛 띠 한 칸(30초 전 경고). 낮은 투명 띠."""
    return [box("line", (6.0, 0.3, 0.02), (0, 0, 0.0), mat_alpha("#7FB0C0", 0.5, 0.5)), box("line_b", (6.0, 0.12, 0.03), (0, 0, 0.0), "#9ACCDA")]

KIT = [(f.__name__, f) for f in (lying_shadow, lying_shadow_pair, linked_arms_eleven, half_stake, mud_pool, capsized_boat, wreck_ribs, sea_cave_rock, hanging_threads, name_tag_thread, tomb_wall, fallen_standards, rusty_cart, mine_beam,
        mine_beam_broken, rubble_pile, lime_band, fallen_medicine_chest, blank_stones_row, unmarked_mound, bridge_footing, floor_strokes, ink_silt_islet, quarters_bunk, ondol_tile, ondol_hot_tile, offering_set, seal_floor_mark,
        chain_root, well_wall, well_rope, torch_in_water, barley_sheaf, dawn_flood_line)]
LIGHTS = {"torch_in_water": ("Light_torch", (0, 0, 1.8), (1.0, 0.7, 0.3), 1.8, 9.0, True), "ondol_hot_tile": ("Light_hot", (0, 0, 0.5), (1.0, 0.4, 0.2), 0.8, 4.0, True)}
def build(name, fn):
    reset(); o = join("s3_" + name, fn()); lo, hi = bounds(o)
    if name in LIGHTS: n, pos, col, it, rg, fl = LIGHTS[name]; light_empty(o, n, pos, col, intensity=it, range_m=rg, flicker=fl)
    export(o, os.path.join(OUT, "s3", f"s3_{name}.glb"))
    return {"name": "s3_" + name, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}
if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "s3"), exist_ok=True)
    want = sys.argv[1:]; res = [build(k, f) for k, f in KIT if not want or k in want]
    if not want:
        json.dump(res, open(os.path.join(OUT, "s3", "_report_s3.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        for i, (k, f) in enumerate(KIT): o = join(k, f()); o.location = ((i % 7 - 3) * 10.0, -(i // 7) * 10.0, 0)
        setup_render(75, (0, -20.0, 1.5), elev=50, size=(1500, 900), ground_size=140); bpy.context.scene.cycles.samples = 24
        render(os.path.join(OUT, "previews", "s3_kit_50deg.png"))
    print(len(res), "종, 삼각형 최대", max(r["tris"] for r in res))
