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
    """나무 선창 한 칸 4×3m: 바닷바람에 바랜 널판을 깔고 아래 말뚝 여섯. 가장자리는 닳아 들쭉날쭉."""
    r = random.Random(31); p = []
    for i in range(10): p.append(box(f"plank{i}", (3.0 + r.uniform(-.05, .05), 0.38, 0.07), (0, -1.5 + i * 0.32 + 0.16, 0.55 + r.uniform(0, .015)), SEA_WOOD if i % 3 else SEA_WOOD_D))
    p += [box(f"bear{i}", (4.0, 0.14, 0.12), (0, -1.2 + i * 1.2, 0.46), SEA_WOOD_D) for i in range(3)]
    p += [cyl(f"pile{i}", 0.1, 0.12, 1.2, (-1.7 + (i % 2) * 3.4, -1.3 + (i // 2) * 1.3, 0.0), SEA_WOOD_D, 6) for i in range(6)]
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

KIT = [(f.__name__, f) for f in (harbor_pier, harbor_gauge_post, harbor_boat, harbor_net_frame, harbor_net_pile, harbor_jar, harbor_gaekju_house, harbor_inn, harbor_lamp_hut,
       salt_pan, salt_pile, salt_warehouse, salt_dike, cape_waiting_rock, cape_hutmyo, cape_new_grave, shoal_wreck, shoal_rock, shoal_plank)]
LIGHTS = {"harbor_gaekju_house": ("Light_gaekju", (0, -3.5, 2.5), WARM, 1.0, 7.0, True), "harbor_inn": ("Light_inn", (2.0, -2.2, 2.2), WARM, 1.0, 6.0, True), "harbor_lamp_hut": ("Light_lamp_hut", (2.2, 0, 4.7), WARM, 1.4, 14.0, True)}

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
        for i, (k, f) in enumerate(KIT): o = join(k, f()); o.location = ((i % 5 - 2) * 10.0, -(i // 5) * 9.0, 0)
        setup_render(62, (0, -13.5, 2.0), elev=50, size=(1500, 900), ground_size=110); bpy.context.scene.cycles.samples = 24
        render(os.path.join(OUT, "previews", "act3_harbor_50deg.png"))
