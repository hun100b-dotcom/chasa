"""마을·장터·관아 터 소품 14종(대장간·주막·장터 약방·동헌 터·옥에 놓는 것). 실행: python3 town_props.py [이름 ...]
규약은 life_props.py와 같다(원점=바닥 한가운데, 정면=-Y, 1단위=1m, 재질은 색만, 빛나는 것은 발광, Light_ 빈 오브젝트로 불빛 위치 표시).
주황은 파혼 전용이라 옷·소품에는 안 쓰고, 대장간 화덕 불빛만 불의 색(붉은 노랑)으로 둔다."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
SOOT = "#2A2420"; ASH = "#4A4642"

def anvil():
    """모루: 나무 그루터기 위에 쇠 모루(뿔 달림). 높이 0.85m, 폭 0.7m."""
    return [cyl("stump", 0.27, 0.24, 0.55, (0, 0, 0), "wood", 8), box("body", (0.52, 0.2, 0.16), (0, 0, 0.62), "iron"), box("waist", (0.2, 0.16, 0.1), (0, 0, 0.55), "iron"), cyl("horn", 0.09, 0.0, 0.28, (0.3, 0, 0.7), "iron", 6, rot=(0, math.pi / 2, 0)), box("face", (0.3, 0.22, 0.04), (-0.12, 0, 0.72), "stone")]

def forge():
    """대장간 화덕: 돌 화덕 1.5×1.1m, 위로 좁아지는 흙 굴뚝, 앞에 풀무(손잡이 달림). 불씨는 발광, Light_forge. 높이 2.3m."""
    p = [box("hearth", (1.5, 1.1, 0.8), (0, 0, 0.4), "stone_dark"), box("mouth", (0.8, 0.12, 0.35), (0, -0.55, 0.55), "ink"), box("coals", (0.7, 0.6, 0.05), (0, -0.05, 0.82), mat("#E8683A", 1.6)),
         box("hoodA", (1.2, 0.9, 0.5), (0, 0.05, 1.05), "mud"), box("hoodB", (0.8, 0.6, 0.6), (0, 0.1, 1.6), "mud"), box("flue", (0.4, 0.4, 0.6), (0, 0.1, 2.0), "mud"),
         box("bellows", (0.5, 0.9, 0.3), (-1.1, 0, 0.35), "wood_dark"), box("bellowsTop", (0.5, 0.9, 0.06), (-1.1, 0, 0.55), "wood"), box("bellowsHandle", (0.06, 0.06, 0.7), (-1.1, 0.55, 0.85), "wood", rot=(0.4, 0, 0)), box("pipe", (0.8, 0.07, 0.07), (-0.5, -0.1, 0.5), "iron")]
    return p

def quench_trough():
    """담금질 물통: 속을 판 통나무 물구유. 1.3×0.5m, 높이 0.45m, 어두운 물."""
    return [box("base", (1.3, 0.5, 0.4), (0, 0, 0.2), "wood_dark"), box("water", (1.1, 0.3, 0.02), (0, 0, 0.4), "#2B3A4A"), box("legL", (0.1, 0.4, 0.1), (-0.5, 0, 0.05), "wood"), box("legR", (0.1, 0.4, 0.1), (0.5, 0, 0.05), "wood")]

def tool_rack():
    """연장 걸이: 기둥 둘에 가로대, 망치·집게·부젓가락이 걸림. 1.6×0.2m, 높이 1.5m."""
    p = [cyl("postL", 0.05, 0.05, 1.5, (-0.75, 0, 0), "wood_dark", 5), cyl("postR", 0.05, 0.05, 1.5, (0.75, 0, 0), "wood_dark", 5), box("bar", (1.6, 0.06, 0.06), (0, 0, 1.3), "wood_dark")]
    for i, x in enumerate((-0.5, -0.15, 0.2, 0.55)): p += [box(f"tool{i}", (0.05, 0.03, 0.5), (x, -0.06, 1.0), "iron"), box(f"toolHead{i}", (0.16 if i % 2 == 0 else 0.07, 0.05, 0.1), (x, -0.06, 0.72), "iron")]
    return p

def pyeongsang():
    """평상: 낮은 마루 1.9×1.2m(높이 0.4)와 작은 상, 막걸리 사발 둘. 주막 앞마당용."""
    p = [box("deck", (1.9, 1.2, 0.08), (0, 0, 0.4), "wood")] + [box(f"leg{i}", (0.1, 0.1, 0.4), (x, y, 0.2), "wood_dark") for i, (x, y) in enumerate(((-0.85, -0.5), (0.85, -0.5), (-0.85, 0.5), (0.85, 0.5)))]
    p += [box("table", (0.7, 0.45, 0.2), (0.25, 0, 0.54), "wood_dark"), cyl("bowlA", 0.06, 0.08, 0.06, (0.1, -0.05, 0.64), "hanji", 7), cyl("bowlB", 0.06, 0.08, 0.06, (0.42, 0.05, 0.64), "hanji", 7), cyl("jugs", 0.08, 0.06, 0.18, (-0.6, 0.2, 0.44), "jar", 7)]
    return p

def market_stall():
    """장터 좌판: 기둥 넷, 비스듬한 차양(삼베색), 물건을 늘어놓은 널판 상. 폭 2.0m 깊이 1.2m 높이 2.1m."""
    p = [cyl(f"post{i}", 0.04, 0.04, 2.0 if y > 0 else 1.7, (x, y, 0), "wood_dark", 5) for i, (x, y) in enumerate(((-0.95, -0.5), (0.95, -0.5), (-0.95, 0.5), (0.95, 0.5)))]
    p += [box("awning", (2.2, 1.5, 0.05), (0, 0, 1.85), "reed", rot=(0.17, 0, 0)), box("table", (1.8, 0.7, 0.07), (0, -0.2, 0.75), "wood"), box("tableLegL", (0.08, 0.6, 0.75), (-0.8, -0.2, 0.37), "wood_dark"), box("tableLegR", (0.08, 0.6, 0.75), (0.8, -0.2, 0.37), "wood_dark")]
    cols = ["#8A6B4A", "#6F9A4A", "#B4A66A", "#C8B68A", "#7C6A55"]
    p += [sphere(f"goods{i}", 0.12, (-0.7 + i * 0.35, -0.2 + 0.1 * (i % 2), 0.9), cols[i % 5], 5, 4) for i in range(5)] + [box(f"sack{i}", (0.3, 0.25, 0.3), (-0.5 + i * 1.0, 0.35, 0.15), "thatch") for i in range(2)]
    return p

def candy_stand():
    """엿판 자리: 지게형 받침 위 엿 상자(뚜껑 열림)와 엿 조각, 엿 자르는 가위·엿목판. 높이 1.1m."""
    p = [box("tray", (0.8, 0.6, 0.12), (0, 0, 0.8), "wood"), box("rim", (0.84, 0.64, 0.05), (0, 0, 0.9), "wood_dark")]
    p += [box(f"cand{i}", (0.12, 0.12, 0.05), (-0.28 + 0.14 * (i % 5), -0.14 + 0.2 * (i // 5), 0.94), "yellow_cloth") for i in range(10)]
    p += [box("legL", (0.06, 0.5, 0.8), (-0.35, 0, 0.4), "wood_dark", rot=(0, 0.15, 0)), box("legR", (0.06, 0.5, 0.8), (0.35, 0, 0.4), "wood_dark", rot=(0, -0.15, 0)), box("scissors", (0.3, 0.03, 0.03), (0.55, -0.1, 0.5), "iron")]
    return p

def charred_pillar():
    """불에 탄 기둥: 그을린 둥근 기둥, 윗부분이 꺾여 쪼개짐, 밑동에 재. 높이 2.4m."""
    return [cyl("pillar", 0.22, 0.17, 1.9, (0, 0, 0), SOOT, 7), box("splitA", (0.3, 0.2, 0.7), (0.05, 0, 2.2), SOOT, rot=(0, 0.35, 0.1)), box("splitB", (0.18, 0.18, 0.5), (-0.1, 0.05, 2.0), "#1A1614", rot=(0, -0.3, 0)),
            cyl("ash", 0.6, 0.55, 0.05, (0, 0, 0), ASH, 7), sphere("ember", 0.06, (0.12, -0.12, 0.3), mat("#9A3A2A", 0.9), 4, 3)]

def burnt_desk():
    """다리 하나 탄 서안(글 읽는 낮은 책상): 상판이 한쪽으로 기울고 가장자리가 숯. 폭 1.1m, 높이 0.45m."""
    p = [box("top", (1.1, 0.5, 0.06), (0, 0, 0.36), "wood_dark", rot=(0.0, 0.1, 0)), box("char", (0.4, 0.5, 0.065), (0.35, 0, 0.375), SOOT, rot=(0.0, 0.1, 0))]
    p += [box(f"leg{i}", (0.07, 0.07, 0.34), (x, y, 0.17), "wood_dark") for i, (x, y) in enumerate(((-0.45, -0.18), (-0.45, 0.18), (0.45, 0.18)))] + [box("stump", (0.07, 0.07, 0.08), (0.45, -0.18, 0.04), SOOT)]
    p += [cyl("ash", 0.8, 0.7, 0.03, (0.1, 0, 0), ASH, 7), box("ink", (0.12, 0.08, 0.04), (-0.2, 0, 0.42), "ink")]
    return p

def burnt_cabinet():
    """탄 문서함: 반쯤 타 내려앉은 서랍장. 한 장만 멀쩡한 한지가 맨 위 칸에 삐져나와 있다(단서). 0.9×0.5×0.8m, 한지는 약한 발광."""
    p = [box("body", (0.9, 0.5, 0.7), (0, 0, 0.35), SOOT), box("topChar", (0.9, 0.5, 0.06), (0.05, 0, 0.72), "#1A1614", rot=(0, 0.12, 0)), box("doorL", (0.4, 0.04, 0.5), (-0.2, -0.27, 0.35), "wood_dark"), box("doorHang", (0.4, 0.04, 0.5), (0.4, -0.45, 0.2), SOOT, rot=(0, 0, 0.9))]
    p += [box(f"paper{i}", (0.3, 0.22, 0.02), (0.1 - 0.12 * i, -0.1, 0.74 + 0.02 * i), "#3A342F", rot=(0, 0.1 * i, 0.3 * i)) for i in range(3)] + [box("goodPaper", (0.26, 0.2, 0.012), (-0.05, -0.28, 0.5), mat("#F3E7D3", 0.35), rot=(0.2, 0, 0.2))]
    p += [cyl("ash", 0.85, 0.7, 0.03, (0, 0, 0), ASH, 7)]
    return p

def ash_heap():
    """무너진 동헌 잔해 더미: 그을린 들보 토막과 재, 기와 조각. 폭 3m, 높이 0.7m. 동헌 터 곳곳에 놓는다."""
    p = [cyl("ash", 1.5, 1.2, 0.08, (0, 0, 0.1), ASH, 8), box("beamA", (2.2, 0.28, 0.28), (0, -0.2, 0.3), SOOT, rot=(0, 0.15, 0.4)), box("beamB", (1.6, 0.25, 0.25), (0.2, 0.4, 0.5), "#1A1614", rot=(0, -0.2, -0.5)), box("beamC", (1.2, 0.22, 0.22), (-0.4, 0.2, 0.62), SOOT, rot=(0.3, 0.2, 1.2))]
    p += [box(f"tile{i}", (0.34, 0.22, 0.05), (math.cos(i * 2.1) * 0.9, math.sin(i * 2.1) * 0.7, 0.06), "#3A3A44", rot=(0.1 * i, 0.15, i * 1.3)) for i in range(6)]
    return p

def prison_wall():
    """옥 돌담(둥근): 지름 약 11m 원형 돌담, 높이 2.4m, 남쪽(-Y)이 3.4m 비어 문이 선다. 안쪽에 낮은 돌 기단. 원점=원 중심."""
    p = []; R = 5.5; n = 24
    for i in range(n):
        a = math.radians(i * 360 / n)
        if abs(((math.degrees(a) - 270 + 180) % 360) - 180) < 17: continue          # 남쪽 문 자리
        x, y = R * math.cos(a), R * math.sin(a)
        p += [box(f"blk{i}", (1.5, 0.55, 2.4), (x, y, 1.2), "stone_dark" if i % 3 else "stone", rot=(0, 0, a + math.pi / 2)), box(f"cap{i}", (1.6, 0.7, 0.18), (x, y, 2.47), "stone", rot=(0, 0, a + math.pi / 2))]
    p += [cyl("floor", 5.4, 5.4, 0.04, (0, 0, 0), "#4A4642", 24)]
    return p

def prison_gate():
    """옥문: 굵은 기둥 둘에 두꺼운 널문(쇠띠·자물쇠·작은 살창), 옆에 횃대(Light_prison_gate). 폭 3.4m, 높이 2.8m. 원점=문 가운데 바닥."""
    p = [cyl("postL", 0.2, 0.18, 2.8, (-1.6, 0, 0), "pillar", 7), cyl("postR", 0.2, 0.18, 2.8, (1.6, 0, 0), "pillar", 7), box("lintel", (3.7, 0.3, 0.3), (0, 0, 2.65), "wood_dark"), box("door", (2.9, 0.18, 2.3), (0, 0, 1.2), "wood"),
         box("band1", (2.9, 0.2, 0.12), (0, -0.01, 0.6), "iron"), box("band2", (2.9, 0.2, 0.12), (0, -0.01, 1.7), "iron"), box("lock", (0.2, 0.1, 0.25), (0.2, -0.13, 1.15), "iron"), box("window", (0.5, 0.2, 0.3), (0, -0.01, 1.95), "ink")]
    p += [box(f"bar{i}", (0.04, 0.22, 0.34), (-0.18 + i * 0.12, -0.03, 1.95), "iron") for i in range(4)] + [cyl("torchPole", 0.04, 0.04, 1.6, (2.1, -0.3, 0), "wood_dark", 5), cyl("torchHead", 0.07, 0.1, 0.18, (2.1, -0.3, 1.6), "iron", 6), sphere("flame", 0.09, (2.1, -0.3, 1.88), mat("#FFD27A", 2.0), 5, 4, (1, 1, 1.5))]
    return p

KIT = [("anvil", anvil, "모루"), ("forge", forge, "대장간 화덕"), ("quench_trough", quench_trough, "담금질 물통"), ("tool_rack", tool_rack, "연장 걸이"), ("pyeongsang", pyeongsang, "평상"), ("market_stall", market_stall, "장터 좌판"), ("candy_stand", candy_stand, "엿판 자리"),
       ("charred_pillar", charred_pillar, "탄 기둥"), ("burnt_desk", burnt_desk, "탄 서안"), ("burnt_cabinet", burnt_cabinet, "탄 문서함"), ("ash_heap", ash_heap, "잔해 더미"), ("prison_wall", prison_wall, "옥 돌담"), ("prison_gate", prison_gate, "옥문")]
LIGHTS = {"forge": ("Light_forge", (0, -0.2, 1.0), "#FF9A4A", 1.4, 10.0), "prison_gate": ("Light_prison_gate", (2.1, -0.3, 1.9), "#FFC878", 1.0, 9.0), "burnt_cabinet": ("Light_burnt_cabinet", (-0.05, -0.28, 0.6), "#F3E7D3", 0.35, 3.0)}

def build(key, fn):
    reset(); o = join(f"prop_{key}", fn()); lo, hi = bounds(o)
    if key in LIGHTS: n, pos, col, it, rg = LIGHTS[key]; light_empty(o, n, pos, col, intensity=it, range_m=rg, flicker=key != "burnt_cabinet")
    export(o, os.path.join(OUT, "props", f"prop_{key}.glb"))
    return {"name": f"prop_{key}", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}

if __name__ == "__main__":
    want = sys.argv[1:]; res = [build(k, f) for k, f, n in KIT if not want or k in want]
    for r in res: print(r)
    if not want:
        json.dump(res, open(os.path.join(OUT, "props", "_report_town.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        small = [(k, f) for k, f, n in KIT if k not in ("prison_wall", "prison_gate")]
        for i, (k, f) in enumerate(small): o = join(f"prop_{k}", f()); o.location = ((i % 6 - 2.5) * 3.0, -(i // 6) * 3.0, 0)
        setup_render(19, (0, -1.5, 0.6), elev=40, size=(1400, 700), ground_size=40); bpy.context.scene.cycles.samples = 24; render(os.path.join(OUT, "previews", "town_props.png"))
