"""2막 지역 건물·지형 키트 밑작업: ③ 붉은재(산성 아랫마을·싸움터)와 ④ 쇳골 광산. 실행: python3 act2_kit.py [이름 ...]
왜 지금 만드나: 2막은 아직 자료(지도·배치)가 없어서 '조각 키트'부터 만든다. 지도가 오면 이 조각으로 바로 배치할 수 있다.
설정 근거: 붉은재=산성 싸움터·산성 아랫마을 술도가 노인·큰 무덤(술잔 서른일곱)·화살골 바위틈 부러진 깃대·산성 쉼터(planning/combat/appendix-E), 쇳골=광산·갱도 지름길·광부(등불 모자+곡괭이)·광석 길(appendix-B/C).
규약은 town_props.py와 같다(원점=바닥 한가운데, 정면=-Y, 1단위=1m, 재질은 색만, 불빛은 발광+Light_ 빈 오브젝트). 주황은 파혼 전용이라 불은 따뜻한 등불색(#FFB066).
색 뼈대: 붉은재=붉은 흙(#9A5A3E)·젖은 성돌(#7E7E78)·낡은 붉은 깃(#8A2A2A) / 쇳골=쇠찌꺼기(#2E2C30)·녹슨 광석(#6A3A2A)·누런 흙(#A8864E).
출력: assets3d/act2/ (폴더를 새로 둠, 에셋 이름 접두 sanseong_ / soegol_)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
STONE = "#77746A"; STONE_D = "#585650"; RED_SOIL = "#9A5A3E"; FLAG = "#8A2A2A"; SLAG = "#2E2C30"; ORE = "#6A3A2A"; RUST = "#7A4A30"; LOAM = "#A8864E"; MOSS = "#58704A"
WARM = "#FFB066"

def rubble(rng, n, spread, base_z=0.0, mats=(STONE, STONE_D), size=(0.12, 0.3), tag="rb"):
    """흩어진 돌 조각: 크기·기울기가 제각각인 납작한 상자."""
    out = []
    for i in range(n):
        s = rng.uniform(*size)
        out.append(box(f"{tag}{i}", (s, s * rng.uniform(0.7, 1.2), s * 0.6), (rng.uniform(-spread[0], spread[0]), rng.uniform(-spread[1], spread[1]), base_z + s * 0.25), rng.choice(mats), rot=(rng.uniform(-.3, .3), rng.uniform(-.3, .3), rng.uniform(0, 3))))
    return out

def blocks(rng, w, h, x0=0.0, y=0.0, depth=0.9, rows=None, mats=(STONE, STONE_D, "#6E706C"), z0=0.0, tag="bl"):
    """성벽 돌 쌓기: 줄마다 높이가 조금씩 다르고 엇갈려 쌓인 큰 돌."""
    out = []; z = z0; r = 0
    while z < z0 + h - 0.05:
        rh = min(rng.uniform(0.32, 0.46), z0 + h - z); x = -w / 2 + (0.0 if r % 2 else rng.uniform(0.2, 0.5))
        while x < w / 2 - 0.1:
            bw = min(rng.uniform(0.55, 1.0), w / 2 - x)
            if bw > 0.15: out.append(box(f"{tag}{r}_{len(out)}", (bw * 0.97, depth, rh * 0.96), (x0 + x + bw / 2, y + rng.uniform(-0.03, 0.03), z + rh / 2), rng.choice(mats)))
            x += bw
        z += rh; r += 1
    return out

# ───────────────────────── 붉은재 · 산성 아랫마을 ─────────────────────────
def sanseong_wall_straight():
    """산성 성벽 한 칸 4×1.1m, 높이 3.2m(여장 포함). 큰 돌을 엇갈려 쌓고 위에 낮은 담(여장) 네 개, 아래쪽엔 이끼."""
    r = random.Random(11); p = blocks(r, 4.0, 2.7, depth=1.0)
    p += [box(f"merlon{i}", (0.7, 0.5, 0.5), (-1.5 + i * 1.0, -0.2, 2.95), STONE_D) for i in range(4)] + [box("walkway", (4.0, 0.5, 0.12), (0, 0.3, 2.7), "#6E706C")]
    p += [box(f"moss{i}", (r.uniform(.4, .9), 1.02, 0.18), (r.uniform(-1.7, 1.7), 0, r.uniform(0.1, 0.5)), MOSS) for i in range(4)]
    return p

def sanseong_wall_ruin():
    """무너진 성벽 4m: 한쪽은 높고 가운데는 허물어져 돌무더기. 싸움터 옆 길목용."""
    r = random.Random(12); p = blocks(r, 1.7, 2.6, x0=-1.15, depth=0.95, tag="blA") + blocks(r, 1.1, 1.0, x0=1.4, depth=0.95, tag="blB")
    p += rubble(r, 22, (1.3, 0.9), mats=(STONE, STONE_D, "#6E706C"), size=(0.2, 0.55), tag="fall")
    return p

def sanseong_gate():
    """산성 문 6×2.2m, 높이 5.2m: 돌 문기둥 둘에 둥근 홍예(돌 쐐기를 둥글게), 위에 문루. 문짝은 열려 있고 한쪽이 부서짐."""
    r = random.Random(13)
    p = blocks(r, 1.7, 3.4, x0=-2.15, depth=2.0, tag="pL") + blocks(r, 1.7, 3.4, x0=2.15, depth=2.0, tag="pR")
    for i in range(9):   # 홍예: 반원 위에 쐐기돌 아홉
        a = math.pi * (i + 0.5) / 9; cx, cz = math.cos(a) * 1.3, 2.4 + math.sin(a) * 1.3
        p.append(box(f"arch{i}", (0.55, 2.0, 0.5), (cx, 0, cz + 0.9), STONE, rot=(0, -(a - math.pi / 2), 0)))
    p += [box("deck", (6.0, 2.2, 0.2), (0, 0, 4.15), "#6E706C"), box("beam", (5.4, 0.3, 0.3), (0, -0.9, 4.45), "wood_dark")]
    p += [cyl(f"post{i}", 0.12, 0.12, 0.9, (-2.5 + i * 1.25, -0.9, 4.25), "pillar", 6) for i in range(5)]
    p += [prism("roof", 6.6, 2.8, 0.9, (0, 0, 4.9), "tile")]
    p += [box("doorL", (0.25, 1.2, 3.0), (-1.55, 0.9, 1.5), "wood_dark", rot=(0, 0, 0.9)), box("doorR_broken", (0.25, 0.8, 1.6), (1.4, 0.7, 0.8), "wood_dark", rot=(0.3, 0, -0.3))]
    return p

def sanseong_tower():
    """산성 망루 3.2×3.2m, 높이 7m: 돌 아랫단 위에 사방이 트인 나무 누각과 기와 지붕, 꼭대기에 낡은 붉은 깃."""
    r = random.Random(14)
    p = blocks(r, 3.2, 3.2, depth=3.0, tag="base", mats=(STONE, STONE_D))
    p += [cyl(f"pillar{i}", 0.13, 0.13, 2.2, (x, y, 3.2), "pillar", 6) for i, (x, y) in enumerate(((-1.3, -1.3), (1.3, -1.3), (-1.3, 1.3), (1.3, 1.3)))]
    p += [box("floor", (3.2, 3.2, 0.14), (0, 0, 3.25), "wood"), box("rail_f", (2.8, 0.08, 0.1), (0, -1.3, 3.9), "wood_dark"), box("rail_b", (2.8, 0.08, 0.1), (0, 1.3, 3.9), "wood_dark"),
          pyramid("roof", 4.2, 4.2, 1.4, (0, 0, 5.4), "tile"), cyl("flag_pole", 0.04, 0.04, 1.7, (0, 0, 6.6), "wood_dark", 5), box("flag", (0.7, 0.03, 0.4), (0.38, 0, 8.0 - 0.15 - 0.6), FLAG, rot=(0, 0, 0.1))]
    return p

def sanseong_palisade():
    """목책 3m: 끝을 뾰족하게 깎은 통나무 열둘을 줄 세우고 가로대 둘로 묶음. 몇 개는 기울어 있다."""
    r = random.Random(15); p = []
    for i in range(12):
        h = r.uniform(1.7, 2.2); x = -1.4 + i * 0.255
        p += [cyl(f"log{i}", 0.1, 0.1, h, (x, 0, 0), "wood_dark", 6, rot=(r.uniform(-.06, .06), r.uniform(-.06, .06), 0)), cyl(f"tip{i}", 0.1, 0.0, 0.25, (x, 0, h), "wood", 6)]
    p += [box("tie1", (3.1, 0.08, 0.1), (0, 0.1, 0.6), "wood"), box("tie2", (3.1, 0.08, 0.1), (0, 0.1, 1.3), "wood")]
    return p

def sanseong_banner_torn():
    """부러진 깃대와 찢긴 붉은 깃: 5m 깃대가 기울어 선 채 위쪽이 꺾이고 깃발이 갈가리 찢겨 늘어짐."""
    r = random.Random(16)
    p = [cyl("pole", 0.06, 0.05, 3.4, (0, 0, 0), "wood_dark", 6, rot=(0, 0.07, 0)), cyl("snap", 0.05, 0.03, 0.9, (0.3, 0, 3.3), "wood", 6, rot=(0, 1.0, 0))]
    p += [box(f"rag{i}", (0.09, 0.02, r.uniform(0.7, 1.4)), (0.15 + i * 0.1, 0, 3.3 - 0.45 - 0.2 * i), FLAG, rot=(0, r.uniform(-.1, .1), r.uniform(-.1, .1))) for i in range(5)]
    p += [cyl("cairn_base", 0.5, 0.4, 0.3, (0, 0, 0), STONE_D, 6)]
    return p

def sanseong_big_mound():
    """큰 무덤(싸움에서 죽은 이들을 한 구덩이에 묻은 봉분): 지름 5m 풀 덮인 둥근 흙무덤, 앞에 돌 상석과 술잔 서른일곱."""
    r = random.Random(17)
    p = [sphere("mound", 2.6, (0, 0.6, 0), "#5A6E3C", 12, 6, (1.0, 0.95, 0.5)), sphere("bare", 1.3, (-0.4, 0.8, 0.25), RED_SOIL, 8, 4, (1.0, 0.8, 0.3))]
    p += [box("sangseok", (1.6, 0.9, 0.4), (0, -2.2, 0.2), STONE), box("sangseok_top", (1.7, 1.0, 0.1), (0, -2.2, 0.45), STONE_D)]
    for i in range(37):   # 술잔 서른일곱: 상석 앞에 여섯 줄로, 몇 개는 쓰러져 있다
        row, col = divmod(i, 7); x = -1.4 + col * 0.46 + (0.2 if row % 2 else 0); y = -2.9 - row * 0.3
        tip = r.random() < 0.15
        p.append(cyl(f"cup{i}", 0.07, 0.05, 0.08, (x + r.uniform(-.04, .04), y + r.uniform(-.04, .04), 0.04 if not tip else 0.05), "hanji", 5, rot=(1.5 if tip else 0, 0, r.uniform(0, 3))))
    return p

def sanseong_arrow_field():
    """화살 꽂힌 땅: 싸움이 있던 자리에 화살 열한 대가 비스듬히 꽂혀 있다(깃은 낡은 붉은색). 폭 3m."""
    r = random.Random(18); p = []
    for i in range(11):
        x, y = r.uniform(-1.4, 1.4), r.uniform(-1.2, 1.2); t = r.uniform(-.5, .5); u = r.uniform(.2, .5)
        p += [cyl(f"shaft{i}", 0.012, 0.012, 0.8, (x, y, 0.0), "wood", 4, rot=(u, t, 0)), box(f"fletch{i}", (0.05, 0.01, 0.12), (x + math.sin(t) * 0.7, y - math.sin(u) * 0.7, 0.62), FLAG, rot=(u, t, 0))]
    return p

def sanseong_arrow_rock():
    """화살골 바위: 사람 키의 두 배 바위 틈에 부러진 깃대 조각이 끼어 있다(이름 여섯이 또렷하다 — 만져 보기 단서 자리)."""
    r = random.Random(19)
    p = [sphere("rockA", 1.5, (0, 0, 0.9), STONE, 8, 5, (1.2, 1.0, 1.1)), sphere("rockB", 1.1, (1.3, 0.3, 0.6), STONE_D, 7, 4, (1, 1, 1)), sphere("rockC", 0.8, (-1.2, -0.4, 0.45), "#6E706C", 7, 4)]
    p += [box("crack", (0.1, 0.12, 1.4), (0.3, -1.1, 1.0), "ink"), cyl("shard", 0.04, 0.04, 0.9, (0.3, -1.12, 1.3), "wood_dark", 5, rot=(0.0, 0.2, 0)), box("shard_flag", (0.3, 0.02, 0.2), (0.45, -1.12, 1.55), FLAG)]
    p += rubble(r, 8, (1.8, 1.4), size=(0.15, 0.3))
    return p

def sanseong_spear_rack():
    """창꽂이: 나무틀에 창 여섯 자루, 창날은 녹슬었고 몇 자루는 쓰러졌다. 1.8×0.5m."""
    r = random.Random(20)
    p = [box("frame_b", (1.8, 0.1, 0.1), (0, 0, 0.35), "wood_dark"), box("frame_t", (1.8, 0.1, 0.1), (0, 0, 1.0), "wood_dark"), cyl("legL", 0.06, 0.06, 1.1, (-0.85, 0, 0), "wood_dark", 5), cyl("legR", 0.06, 0.06, 1.1, (0.85, 0, 0), "wood_dark", 5)]
    for i in range(6):
        x = -0.7 + i * 0.28; down = i == 4
        p += [cyl(f"spear{i}", 0.02, 0.02, 2.4, (x, 0, 0.1), "wood", 4, rot=(1.2 if down else 0.05, 0, 0.2 if down else 0)), cyl(f"head{i}", 0.04, 0.0, 0.25, (x, -0.0 if not down else -1.2, 2.5 if not down else 0.5), RUST, 4)]
    return p

def sanseong_tent():
    """군막: 낡은 베 천막 3×4m, 높이 2.2m. 한쪽 자락이 걷혀 있고 안은 어둡다. 말뚝과 줄."""
    p = [prism("canvas", 3.0, 4.0, 2.0, (0, 0, 0.2), "#B9AE92"), box("door_dark", (1.0, 0.05, 1.3), (0, -2.0, 0.85), "ink"), box("hem", (3.1, 4.1, 0.2), (0, 0, 0.1), "#8E8468")]
    p += [cyl(f"stake{i}", 0.04, 0.04, 0.5, (x, y, 0), "wood_dark", 4, rot=(0.3 if y < 0 else -0.3, 0, 0)) for i, (x, y) in enumerate(((-1.9, -2.3), (1.9, -2.3), (-1.9, 2.3), (1.9, 2.3)))]
    return p

def sanseong_sul_vat():
    """술도가 술독 밭: 큰 옹기 독 셋과 시루, 누룩 널. 2.6×1.4m. 산성 아랫마을 노인이 술을 붓는 그 술독."""
    p = []
    for i, (x, y, s) in enumerate(((-0.8, 0, 1.0), (0.2, 0.15, 1.15), (1.0, -0.1, 0.9))):
        p += [lathe(f"vat{i}", [(0, 0.25 * s), (0.2 * s, 0.38 * s), (0.5 * s, 0.45 * s), (0.85 * s, 0.34 * s), (0.95 * s, 0.26 * s)], 9, "jar", loc=(x, y, 0)), cyl(f"lid{i}", 0.3 * s, 0.3 * s, 0.05, (x, y, 0.95 * s), "wood", 8)]
    p += [box("nuruk_board", (1.0, 0.5, 0.05), (0, -0.9, 0.35), "wood"), box("nuruk_leg1", (0.06, 0.4, 0.35), (-0.4, -0.9, 0), "wood_dark"), box("nuruk_leg2", (0.06, 0.4, 0.35), (0.4, -0.9, 0), "wood_dark")]
    p += [cyl(f"nuruk{i}", 0.12, 0.12, 0.07, (-0.35 + i * 0.23, -0.9, 0.4), "#C9B38A", 7) for i in range(4)]
    return p

def sanseong_stairs():
    """산길 돌계단 2×4m, 높이 1.6m: 거친 돌판 열 단, 가장자리에 흙이 쏠려 있다."""
    r = random.Random(23)
    p = [box(f"step{i}", (2.0 + r.uniform(-.1, .1), 0.45, 0.16 * (i + 1)), (r.uniform(-.05, .05), -1.8 + i * 0.4, 0.08 * (i + 1)), STONE if i % 2 else "#6E706C") for i in range(10)]
    p += [box("soil_L", (0.4, 4.0, 0.3), (-1.2, 0, 0.15), RED_SOIL, rot=(0.35, 0, 0)), box("soil_R", (0.4, 4.0, 0.3), (1.2, 0, 0.15), RED_SOIL, rot=(0.35, 0, 0))]
    return p

def sanseong_beacon():
    """봉수대: 돌을 둥글게 쌓은 낮은 탑 2.4m, 꼭대기 불구덩이에 꺼져 가는 불씨. Light_beacon."""
    r = random.Random(24)
    p = [cyl("tower", 1.2, 0.9, 2.2, (0, 0, 0), STONE, 10), cyl("rim", 1.0, 1.0, 0.2, (0, 0, 2.2), STONE_D, 10), cyl("pit", 0.8, 0.8, 0.05, (0, 0, 2.4), SLAG, 10), sphere("embers", 0.3, (0, 0, 2.45), mat(WARM, 1.6), 6, 4, (1, 1, 0.5))]
    p += blocks(r, 0.0, 0.0) + [box(f"burn{i}", (0.06, 0.06, 0.4), (r.uniform(-.4, .4), r.uniform(-.4, .4), 2.55), SLAG, rot=(r.uniform(-.5, .5), r.uniform(-.5, .5), 0)) for i in range(5)]
    return p

# ───────────────────────── 쇳골 광산 ─────────────────────────
def soegol_mine_entrance():
    """갱도 입구 6×4m, 높이 4.5m: 누런 바위 벽에 구멍을 뚫고 갱목 문틀을 세움. 안은 새까맣고 문틀 옆 등불. Light_mine_lamp."""
    r = random.Random(31)
    p = [sphere("cliff", 3.2, (0, 1.6, 1.8), "#7A6C58", 10, 6, (1.3, 0.9, 0.95)), sphere("cliffL", 1.6, (-2.8, 0.8, 1.0), "#6E6250", 8, 5), sphere("cliffR", 1.7, (2.9, 0.9, 1.1), "#85775F", 8, 5)]
    p += [box("hole", (1.8, 1.0, 2.1), (0, -1.0, 1.05), "#050508"), cyl("postL", 0.17, 0.17, 2.3, (-1.05, -1.5, 0), "wood", 6), cyl("postR", 0.17, 0.17, 2.3, (1.05, -1.5, 0), "wood", 6), box("lintel", (2.6, 0.3, 0.3), (0, -1.5, 2.3), "wood_dark")]
    p += [box("brace1", (0.12, 0.12, 0.9), (-0.8, -1.5, 2.0), "wood", rot=(0, -0.8, 0)), box("brace2", (0.12, 0.12, 0.9), (0.8, -1.5, 2.0), "wood", rot=(0, 0.8, 0)), box("sign", (0.9, 0.06, 0.4), (0, -1.7, 2.8), "wood_dark")]
    p += [cyl("lamp_pole", 0.04, 0.04, 1.6, (1.6, -1.6, 0), "wood_dark", 5), box("lamp", (0.2, 0.2, 0.28), (1.6, -1.6, 1.6), mat(WARM, 2.0))]
    p += rubble(r, 14, (3.2, 1.0), base_z=0, mats=("#6E6250", SLAG, ORE), size=(0.15, 0.4)) 
    return p

def soegol_timber_frame():
    """갱목 문틀 1칸: 갱도 안을 받치는 기둥 둘과 들보 하나, 비스듬한 버팀. 폭 2.2m 높이 2.3m. 이어 붙이면 갱도가 된다."""
    return [cyl("postL", 0.14, 0.14, 2.2, (-1.0, 0, 0), "wood", 6), cyl("postR", 0.14, 0.14, 2.2, (1.0, 0, 0), "wood", 6), box("beam", (2.4, 0.28, 0.26), (0, 0, 2.2), "wood_dark"), box("braceL", (0.1, 0.1, 0.7), (-0.75, 0, 1.95), "wood", rot=(0, -0.8, 0)), box("braceR", (0.1, 0.1, 0.7), (0.75, 0, 1.95), "wood", rot=(0, 0.8, 0)), box("plank", (2.0, 0.06, 0.12), (0, 0.12, 1.2), "wood_dark")]

def soegol_rail():
    """광차 레일 3m: 쇠 레일 둘과 나무 침목 여섯. 레일 간격 0.7m, 높이 0.12m."""
    return [box("railL", (0.06, 3.0, 0.07), (-0.35, 0, 0.1), "iron"), box("railR", (0.06, 3.0, 0.07), (0.35, 0, 0.1), "iron")] + [box(f"tie{i}", (0.95, 0.14, 0.07), (0, -1.25 + i * 0.5, 0.035), "wood_dark") for i in range(6)]

def soegol_cart():
    """광차: 쇠 바퀴 넷 달린 사각 통, 광석이 수북이 실림. 1.1×1.5m, 높이 0.95m."""
    r = random.Random(34)
    p = [box("bed", (0.95, 1.4, 0.5), (0, 0, 0.5), "#4A3A32"), box("rimF", (1.0, 0.06, 0.08), (0, -0.7, 0.78), "iron"), box("rimB", (1.0, 0.06, 0.08), (0, 0.7, 0.78), "iron"), box("coupler", (0.08, 0.3, 0.08), (0, -0.85, 0.45), "iron")]
    p += [cyl(f"wheel{i}", 0.15, 0.15, 0.06, (x, y, 0.15), "iron", 8, rot=(0, math.pi / 2, 0)) for i, (x, y) in enumerate(((-0.5, -0.45), (0.5, -0.45), (-0.5, 0.45), (0.5, 0.45)))]
    p += [sphere(f"ore{i}", r.uniform(.12, .2), (r.uniform(-.3, .3), r.uniform(-.5, .5), 0.82 + r.uniform(0, .12)), ORE if i % 3 else SLAG, 5, 3) for i in range(11)]
    return p

def soegol_ore_pile():
    """광석 더미 2.2×1.8m, 높이 0.9m: 붉은 갈색과 검은 덩이가 섞여 쌓였다. 몇 개는 푸르스름하게 번뜩임(쇠 맛)."""
    r = random.Random(35); p = []
    for i in range(34):
        a = r.uniform(0, 6.28); d = r.uniform(0, 0.9) ** 1.2; sz = r.uniform(0.14, 0.3)
        p.append(sphere(f"ore{i}", sz, (math.cos(a) * d * 1.1, math.sin(a) * d * 0.9, max(0.1, 0.8 - d * 0.7) * 0.5 + sz * 0.3), [ORE, SLAG, RUST, "#4A3028", "#46506A"][i % 5], 5, 3, (1, 1, 0.8), rot=(r.uniform(0, 3), r.uniform(0, 3), 0)))
    return p

def soegol_slag_heap():
    """쇠찌꺼기 더미(폐석) 4×3m, 높이 1.6m: 검은 덩어리가 산사태처럼 흘러내린 비탈. 쇳골 바닥 곳곳에 놓을 큰 지형 조각."""
    r = random.Random(36)
    p = [sphere("body", 1.9, (0, 0, 0), SLAG, 9, 5, (1.1, 0.85, 0.55))]
    for i in range(40):   # 덩어리: 몸통 표면 위에 얹는다(몸통은 반쯤 묻힌 납작 타원체라 높이를 표면식으로 구한다)
        a = r.uniform(0, 6.28); d = r.uniform(0.1, 0.95); sz = r.uniform(0.16, 0.36)
        p.append(sphere(f"chunk{i}", sz, (math.cos(a) * d * 2.0, math.sin(a) * d * 1.5, 1.0 * math.sqrt(max(0.0, 1 - d * d)) - 0.05), [SLAG, "#444048", RUST, "#242226", "#5A4A44"][i % 5], 5, 3, (1, 1, 0.7), rot=(r.uniform(0, 3), 0, 0)))
    return p

def soegol_windlass():
    """도르래 틀(광석 끌어올림): 나무 A자 틀에 바퀴와 줄, 끝에 광석 바구니가 매달림. 2×1.5m, 높이 3m."""
    p = [limb("legL", (-1.0, -0.5, 0), (0, 0, 2.9), 0.09, 0.07, "wood", 5), limb("legR", (1.0, -0.5, 0), (0, 0, 2.9), 0.09, 0.07, "wood", 5), limb("legBL", (-1.0, 0.5, 0), (0, 0, 2.9), 0.09, 0.07, "wood", 5), limb("legBR", (1.0, 0.5, 0), (0, 0, 2.9), 0.09, 0.07, "wood", 5)]
    p += [cyl("wheel", 0.4, 0.4, 0.12, (0, 0, 2.6), "wood_dark", 10, rot=(0, math.pi / 2, 0)), cyl("axle", 0.05, 0.05, 1.0, (0, 0, 2.6), "iron", 5, rot=(0, math.pi / 2, 0)), cyl("rope", 0.025, 0.025, 1.7, (0, 0, 0.9), "reed", 4)]
    p += [cyl("bucket", 0.28, 0.22, 0.4, (0, 0, 0.5), "wood_dark", 8), box("band", (0.6, 0.6, 0.05), (0, 0, 0.7), "iron"), cyl("crank", 0.03, 0.03, 0.5, (0.62, 0, 2.6), "iron", 4, rot=(0, 0, 0.0))]
    return p

def soegol_miner_hut():
    """광부 움막: 통나무 반 칸 위에 짚·널을 비스듬히 얹은 한쪽 지붕집 3×2.6m, 높이 2.2m. 문은 가마니. 앞에 등불."""
    p = [box("back_wall", (3.0, 0.15, 2.0), (0, 1.2, 1.0), "wood_dark"), box("sideL", (0.15, 2.4, 1.6), (-1.5, 0, 0.8), "wood_dark"), box("sideR", (0.15, 2.4, 1.6), (1.5, 0, 0.8), "wood_dark"),
         box("roof", (3.4, 3.0, 0.14), (0, -0.05, 1.85), "thatch", rot=(0.22, 0, 0)), box("door_mat", (0.9, 0.06, 1.5), (0.4, -1.2, 0.75), "#9C8858"), cyl("front_post", 0.08, 0.08, 1.7, (-1.5, -1.2, 0), "wood", 5), cyl("front_post2", 0.08, 0.08, 1.7, (1.5, -1.2, 0), "wood", 5),
         box("sleeping_mat", (1.4, 0.8, 0.06), (-0.5, 0.3, 0.03), "#9C8858")]
    p += [box("lantern", (0.16, 0.16, 0.22), (-1.5, -1.3, 1.45), mat(WARM, 1.8))]
    return p

def soegol_lantern_post():
    """광부 등불 기둥: 2.6m 나무 기둥 끝에 쇠 걸이, 종이등. 갱도 가는 길 표시. Light_soegol_post."""
    return [cyl("pole", 0.06, 0.07, 2.6, (0, 0, 0), "wood_dark", 5), box("arm", (0.5, 0.05, 0.05), (0.25, 0, 2.5), "iron"), box("lamp", (0.22, 0.22, 0.32), (0.5, 0, 2.2), mat(WARM, 2.0)), box("cap", (0.28, 0.28, 0.04), (0.5, 0, 2.38), "iron"), box("base_stones", (0.5, 0.5, 0.2), (0, 0, 0.1), STONE_D)]

def soegol_ore_basket():
    """광석 지게 바구니와 곡괭이: 대나무 바구니에 광석이 담기고, 옆에 곡괭이가 기대 있다. 0.7m."""
    r = random.Random(40)
    p = [cyl("basket", 0.3, 0.38, 0.55, (0, 0, 0), "#B09468", 8), cyl("rim", 0.31, 0.31, 0.04, (0, 0, 0.55), "wood", 8)]
    p += [sphere(f"o{i}", 0.12, (r.uniform(-.15, .15), r.uniform(-.15, .15), 0.58 + r.uniform(0, 0.08)), ORE if i % 2 else SLAG, 5, 3) for i in range(5)]
    p += [cyl("pick_handle", 0.025, 0.025, 1.1, (0.5, -0.1, 0), "wood", 5, rot=(0, -0.35, 0)), box("pick_head", (0.36, 0.05, 0.05), (0.31, -0.1, 1.07), "iron", rot=(0, -0.35, 0))]
    return p

def soegol_wash_flume():
    """선광 물길 4m: 비스듬히 놓인 나무 홈통(광석을 물에 씻어 고르는 곳). 다리 셋, 안에 붉게 탁한 물."""
    p = [box("floor", (0.7, 4.0, 0.06), (0, 0, 0.7), "wood"), box("wallL", (0.06, 4.0, 0.3), (-0.35, 0, 0.85), "wood_dark"), box("wallR", (0.06, 4.0, 0.3), (0.35, 0, 0.85), "wood_dark"), box("water", (0.62, 3.9, 0.02), (0, 0, 0.76), "#7A5A44")]
    p += [box(f"leg{i}", (0.1, 0.1, 0.7 - i * 0.12), (0, -1.6 + i * 1.6, (0.7 - i * 0.12) / 2), "wood_dark") for i in range(3)] + [box("ripple_bar", (0.6, 0.05, 0.08), (0, 0.3, 0.8), "wood")]
    p += [sphere(f"stone{i}", 0.08, (-0.15 + i * 0.15, -0.8 - i * 0.3, 0.79), STONE, 5, 3) for i in range(3)]
    return p

def soegol_smelter():
    """용광로(쇠 녹이는 가마) 지름 2.2m, 높이 4m: 위로 좁아지는 흙·돌 굴뚝, 아래 불구멍이 이글이글. 풀무 둘. Light_smelter."""
    r = random.Random(43)
    p = [lathe("stack", [(0.0, 1.1), (0.8, 0.95), (2.2, 0.7), (3.4, 0.5), (4.0, 0.42)], 10, "#6A5A4A", fn=lambda i, k, th, z, rr: (rr * (1 + 0.04 * (1 if k % 2 else -1)), z)), box("mouth", (0.9, 0.3, 0.7), (0, -1.0, 0.55), "#050508"), box("fire", (0.7, 0.1, 0.5), (0, -1.1, 0.55), mat("#FFB066", 2.4)),
         box("tap", (0.3, 0.5, 0.2), (0.7, -0.9, 0.2), "iron"), sphere("slag_run", 0.3, (0.9, -1.4, 0.05), mat("#E8683A", 1.4), 6, 3, (1.6, 1, 0.2))]
    for sx in (-1, 1): p += [box(f"bellows{sx}", (0.6, 1.1, 0.5), (sx * 1.4, -0.4, 0.3), "wood_dark"), box(f"bellows_top{sx}", (0.6, 1.1, 0.07), (sx * 1.4, -0.4, 0.58), "wood"), limb(f"pipe{sx}", (sx * 1.2, -0.9, 0.4), (sx * 0.4, -1.0, 0.6), 0.06, 0.05, "iron", 5)]
    p += [box(f"band{i}", (1.9 - i * 0.35, 1.9 - i * 0.35, 0.07), (0, 0, 0.9 + i * 0.9), "iron") for i in range(3)]
    p += rubble(r, 10, (1.8, 1.8), mats=(SLAG, RUST), size=(0.15, 0.35))
    return p

def soegol_ingot_stack():
    """쇳덩이 더미 1.2×0.8m: 납작한 쇳덩이를 엇갈려 쌓음. 맨 위 하나는 아직 붉게 식는 중(옅은 발광)."""
    p = []
    for i in range(12):
        row, col = divmod(i, 4)
        if row == 2 and col > 1: continue
        p.append(box(f"ingot{i}", (0.34, 0.2, 0.1), (-0.45 + col * 0.38 + (0.17 if row % 2 else 0), 0.0, 0.05 + row * 0.1), "#4A4A56" if i % 3 else "#3A3A44"))
    p.append(box("hot", (0.34, 0.2, 0.06), (-0.1, 0, 0.33), mat("#B04A32", 0.7)))
    return p

def soegol_rope_fence():
    """갱 입구 막이: 말뚝 넷에 낡은 밧줄을 건 임시 울타리 3m, 푯말 하나(붉은 헝겊). 폐갱도 입구용."""
    p = [cyl(f"stake{i}", 0.05, 0.05, 1.1, (-1.5 + i * 1.0, 0, 0), "wood_dark", 5, rot=(0, (i - 1.5) * 0.04, 0)) for i in range(4)]
    p += [limb(f"rope{j}{i}", (-1.5 + i * 1.0, 0, 0.9 - j * 0.3), (-0.5 + i * 1.0, 0, 0.8 - j * 0.3), 0.015, 0.015, "reed", 4) for j in range(2) for i in range(3)]
    p += [box("cloth", (0.3, 0.02, 0.3), (0.5, -0.02, 0.8), FLAG)]
    return p

def soegol_scree():
    """붉은 자갈 비탈(광산 바닥 조각) 3×3m: 낮게 깔린 모난 자갈과 쇠찌꺼기 부스러기."""
    r = random.Random(46)
    return [box(f"s{i}", (s := r.uniform(.12, .4), s * r.uniform(.6, 1.2), s * .5), (r.uniform(-1.4, 1.4), r.uniform(-1.4, 1.4), s * .2), r.choice([RUST, SLAG, LOAM, "#6E6250"]), rot=(r.uniform(-.3, .3), r.uniform(-.3, .3), r.uniform(0, 3))) for i in range(34)]

KIT = [(f.__name__, f) for f in (sanseong_wall_straight, sanseong_wall_ruin, sanseong_gate, sanseong_tower, sanseong_palisade, sanseong_banner_torn, sanseong_big_mound, sanseong_arrow_field, sanseong_arrow_rock, sanseong_spear_rack, sanseong_tent, sanseong_sul_vat, sanseong_stairs, sanseong_beacon,
       soegol_mine_entrance, soegol_timber_frame, soegol_rail, soegol_cart, soegol_ore_pile, soegol_slag_heap, soegol_windlass, soegol_miner_hut, soegol_lantern_post, soegol_ore_basket, soegol_wash_flume, soegol_smelter, soegol_ingot_stack, soegol_rope_fence, soegol_scree)]
LIGHTS = {"sanseong_beacon": ("Light_beacon", (0, 0, 2.7), WARM, 1.6, 12.0, True), "soegol_mine_entrance": ("Light_mine_lamp", (1.6, -1.7, 1.6), WARM, 1.2, 8.0, True), "soegol_lantern_post": ("Light_soegol_post", (0.5, 0, 2.2), WARM, 1.0, 7.0, True),
          "soegol_smelter": ("Light_smelter", (0, -1.4, 0.7), "#FF9A4A", 1.8, 11.0, True), "soegol_miner_hut": ("Light_miner_hut", (-1.5, -1.5, 1.45), WARM, 0.8, 5.0, True)}

def build(name, fn):
    reset(); o = join(name, fn()); lo, hi = bounds(o)
    if name in LIGHTS: n, pos, col, it, rg, fl = LIGHTS[name]; light_empty(o, n, pos, col, intensity=it, range_m=rg, flicker=fl)
    export(o, os.path.join(OUT, "act2", f"{name}.glb"))
    return {"name": name, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}

if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "act2"), exist_ok=True)
    want = sys.argv[1:]; res = [build(k, f) for k, f in KIT if not want or k in want]
    for r in res: print(r)
    if not want:
        json.dump(res, open(os.path.join(OUT, "act2", "_report_act2.json"), "w"), ensure_ascii=False, indent=1)
        for grp, pre in (("sanseong", "sanseong_"), ("soegol", "soegol_")):
            reset(); items = [(k, f) for k, f in KIT if k.startswith(pre)]
            for i, (k, f) in enumerate(items): o = join(k, f()); o.location = ((i % 5 - 2) * 7.5, -(i // 5) * 7.5, 0)
            setup_render(40, (0, -7.5, 1.5), elev=50, size=(1500, 800), ground_size=80); bpy.context.scene.cycles.samples = 24
            render(os.path.join(OUT, "previews", f"act2_{grp}_50deg.png"))
