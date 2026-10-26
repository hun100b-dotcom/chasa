"""1막 솔고개 처음 10분 길 소품 9종(보릿들 둑길·마을 어귀 길).
왜: 처음 5분 흐름(first-5-minutes.md)은 시작 위치(196,30) → 우물 → 보릿들 둑길(290,113, '둘러싸임' 싸움) → 대장간(박돌쇠) 순으로 걷는다. 이 길 둘레 소품을 세어 보니(8 m 안) 시작 길 6개, 마을 서쪽 길 0~5개,
 둑길 동쪽 끝(x 233~297)은 0~2개로 거의 비어 있었다. 둑길은 처음 전투를 하는 곳이라 '농사짓는 사람이 있던 자리'로 읽혀야 하는데 보리밭 바닥뿐이어서 이 소품을 만든다.
 접두 a1r_(act1 route). 규약은 act3_kit과 같다(1유닛=1m, 원점=바닥 한가운데, 정면=-Y). 주황은 쓰지 않는다(파혼 전용). 불빛 없음(낮 길이라).
출력 assets3d/props/a1r_*.glb(+ unity/Assets/Resources/Models/Field/). 실행: python3 act1_route.py → _report_act1_route.json, previews/act1_route_50deg.png"""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); TAU = math.tau
STRAW, STRAW_D, BARLEY, SOIL, WOODC, STONEC = "#C2A85E", "#9A8248", "#B8A85A", "#6B5A3E", "#7A5C3A", "#8A8A82"

def sheaf_stack():
    """보릿단 세워 말림 1.6m: 보릿단 다섯을 원뿔로 세워 끝을 묶어 말린다. 높이 1.4m."""
    p = []
    for i in range(5):
        a = i * TAU / 5; x, y = math.cos(a) * 0.35, math.sin(a) * 0.35
        p.append(limb(f"s{i}", (x, y, 0), (x * 0.25, y * 0.25, 1.35), 0.2, 0.05, STRAW if i % 2 else STRAW_D, 6))
    p += [sphere("cap", 0.2, (0, 0, 1.38), STRAW_D, 5, 3, (1, 1, 0.7)), cyl("band", 0.3, 0.3, 0.05, (0, 0, 0.55), "#6A5A3A", 8)]; return p
def water_gate():
    """물꼬(논·밭 물길 터는 작은 문) 2.4m: 도랑을 가로지른 널문과 양쪽 흙 둑. 널을 올리면 물이 든다."""
    return [box("ditch", (2.4, 0.7, 0.05), (0, 0, 0.0), "#4A5E70"), box("bankL", (1.0, 1.2, 0.3), (-1.4, 0, 0.15), SOIL), box("bankR", (1.0, 1.2, 0.3), (1.4, 0, 0.15), SOIL),
            box("board", (0.06, 0.8, 0.45), (0, 0, 0.25), WOODC), box("postL", (0.08, 0.08, 0.7), (-0.0, -0.45, 0.35), "wood_dark"), box("postR", (0.08, 0.08, 0.7), (0.0, 0.45, 0.35), "wood_dark"),
            limb("pull", (0, 0, 0.5), (0.0, 0.0, 0.85), 0.03, 0.03, "wood", 4)]
def lean_to():
    """원두막 3×3m, 높이 3m: 기둥 넷 위에 마루를 높이 올리고 짚 지붕. 사다리 하나. 밭 지키는 사람이 앉는 자리."""
    p = [cyl(f"po{i}", 0.08, 0.09, 2.6, (x, y, 0), "wood_dark", 5) for i, (x, y) in enumerate(((-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)))]
    p += [box("floor", (2.8, 2.8, 0.1), (0, 0, 1.2), WOODC), prism("roof", 3.4, 3.4, 0.9, (0, 0, 2.6), STRAW_D)]
    p += [limb("ladL", (-0.35, -1.5, 0), (-0.35, -1.25, 1.25), 0.04, 0.04, "wood", 4), limb("ladR", (0.35, -1.5, 0), (0.35, -1.25, 1.25), 0.04, 0.04, "wood", 4)] + [box(f"rung{i}", (0.7, 0.04, 0.04), (0, -1.5 + i * 0.06, 0.25 + i * 0.25), "wood") for i in range(4)]
    p += [box("mat", (1.2, 0.9, 0.03), (0.3, 0.2, 1.27), "#C9B764"), box("gourd", (0.2, 0.2, 0.15), (-0.7, 0.6, 1.32), "#CDBF8A")]; return p
def bird_line():
    """새 쫓는 줄 5m, 높이 2.2m: 장대 둘 사이 줄에 헝겊과 깡통 쪽이 매달려 바람에 흔들린다(새 쫓는 소리)."""
    r = random.Random(91); p = [cyl("pL", 0.05, 0.05, 2.3, (-2.5, 0, 0), "wood_dark", 5), cyl("pR", 0.05, 0.05, 2.3, (2.5, 0, 0), "wood_dark", 5), limb("rope", (-2.5, 0, 2.2), (2.5, 0, 2.1), 0.012, 0.012, "#A89868", 3)]
    for i in range(9): x = -2.2 + i * 0.55; p += [limb(f"t{i}", (x, 0, 2.17), (x, 0, 1.75), 0.006, 0.006, "#A89868", 3), box(f"c{i}", (0.14, 0.02, 0.2) if i % 2 else (0.08, 0.08, 0.1), (x, 0, 1.65), "#E6DFC8" if i % 2 else "#8A8A92", rot=(0, 0, r.uniform(-.2, .2)))]
    return p
def gourd_trellis():
    """박 덩굴 시렁 2.4m, 높이 1.8m: 대나무 시렁에 덩굴이 오르고 하얀 박이 달렸다."""
    r = random.Random(92); p = [limb(f"b{i}", (-1.1 + i * 0.55, 0, 0), (-1.1 + i * 0.55, 0, 1.8), 0.035, 0.03, "#8A9A5A", 4) for i in range(5)] + [limb(f"h{k}", (-1.1, 0, 0.7 + k * 0.5), (1.1, 0, 0.7 + k * 0.5), 0.02, 0.02, "#8A9A5A", 4) for k in range(3)]
    p += [sphere(f"leaf{i}", 0.2, (r.uniform(-1.1, 1.1), r.uniform(-.1, .1), r.uniform(0.8, 1.7)), "#5E7A3A", 5, 3, (1.3, 0.5, 0.9)) for i in range(12)] + [sphere(f"gourd{i}", 0.17, (-0.7 + i * 0.7, -0.05, 1.15 - (i % 2) * 0.25), "#E8E2C8", 6, 4, (1, 1, 1.2)) for i in range(3)]; return p
def manure_heap():
    """두엄 더미 2m: 짚과 거름을 쌓아 덮어 둔 더미. 위에 짚 덮개, 가장자리에 삽 하나."""
    return [sphere("heap", 1.0, (0, 0, 0.55), "#4A3A28", 7, 4, (1.1, 0.9, 0.55)), sphere("straw", 0.8, (0.0, 0.0, 0.85), STRAW_D, 6, 3, (1.1, 0.9, 0.35)), limb("shovel", (1.0, -0.7, 0.0), (0.7, -0.4, 0.9), 0.025, 0.025, "wood", 4), box("blade", (0.2, 0.02, 0.22), (1.02, -0.72, 0.1), "#3A3A44")]
def ridge_marker():
    """두렁 말뚝 0.9m: 밭 두렁 끝에 박은 말뚝에 하얀 헝겊을 감았다(눈에 띄는 밭 경계 표지)."""
    return [cyl("post", 0.06, 0.07, 1.1, (0, 0, 0), "wood_dark", 5), box("cloth", (0.2, 0.2, 0.28), (0, 0, 0.9), "#E6DFC8"), limb("tail", (0.1, 0, 1.0), (0.3, -0.1, 0.75), 0.02, 0.01, "#E6DFC8", 3), sphere("base", 0.2, (0, 0, 0.05), STONEC, 5, 3, (1, 1, 0.4))]
def wayside_rest():
    """길가 쉼터 2m: 납작한 돌 의자와 짐을 받쳐 두는 작대기 하나(지게 짐꾼이 쉬는 자리)."""
    return [box("seat", (1.5, 0.6, 0.3), (0, 0, 0.15), STONEC), box("seat_top", (1.5, 0.6, 0.06), (0, 0, 0.33), "#9A9A92"), box("leg1", (0.2, 0.5, 0.15), (-0.55, 0, 0.0), "#6E6E68"), limb("prop_stick", (0.9, -0.3, 0.0), (0.7, -0.1, 1.1), 0.03, 0.03, "wood", 4), limb("prop_fork", (0.7, -0.1, 1.1), (0.62, -0.1, 1.25), 0.025, 0.02, "wood", 4), sphere("bundle", 0.22, (-0.2, 0.0, 0.5), "#8A7A5E", 5, 4, (1.3, 1, 0.9))]
def drink_jars():
    """길가 물독 1.2m: 지나가는 사람이 마시라고 내놓은 독 둘과 바가지, 덮개 널."""
    j = lambda n, x, h: lathe(n, [(0, 0.2), (0.12, 0.34), (h * 0.5, 0.42), (h * 0.85, 0.3), (h, 0.2)], 8, "jar", loc=(x, 0, 0))
    return [j("j1", -0.35, 0.8), j("j2", 0.35, 0.65), box("lid", (0.5, 0.5, 0.04), (0.35, 0.0, 0.68), "#8A7A5E"), sphere("gourd", 0.12, (0.9, -0.3, 0.08), "#CDBF8A", 5, 3, (1, 1, 0.6)), box("stand", (1.6, 0.6, 0.06), (0, 0, 0.0), "#6A645A")]

LIST = [("a1r_sheaf_stack", sheaf_stack, "보릿단 말림"), ("a1r_water_gate", water_gate, "물꼬"), ("a1r_lean_to", lean_to, "원두막"), ("a1r_bird_line", bird_line, "새 쫓는 줄"), ("a1r_gourd_trellis", gourd_trellis, "박 시렁"),
        ("a1r_manure_heap", manure_heap, "두엄 더미"), ("a1r_ridge_marker", ridge_marker, "두렁 말뚝"), ("a1r_wayside_rest", wayside_rest, "길가 쉼터"), ("a1r_drink_jars", drink_jars, "길가 물독")]

def run():
    rep = []
    for key, fn, nm in LIST:
        reset(); o = join(key, fn()); lo, hi = bounds(o); export(o, os.path.join(OUT, "props", key + ".glb"))
        rep.append({"name": key, "label": nm, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
    json.dump(rep, open(os.path.join(OUT, "props", "_report_act1_route.json"), "w"), ensure_ascii=False, indent=1)
    reset()
    for i, (k, f, _) in enumerate(LIST): o = join(f"p{i}", f()); o.location = ((i % 5 - 2) * 5.0, 2.5 - (i // 5) * 5.0, 0)
    setup_render(32, (0, -1.5, 0.8), size=(1600, 900), ground_size=60); bpy.context.scene.cycles.samples = 28
    render(os.path.join(OUT, "previews", "act1_route_50deg.png")); return rep
if __name__ == "__main__":
    for r in run(): print(r["name"], r["tris"], r["size_m"], "min_z", r["min_z"])
