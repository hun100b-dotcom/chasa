"""칠복네 개 소품(장례·제사 장면, 솔고개 기와집 담 모퉁이). 실행: python3 dog_props.py
근거: planning/data/jesa_watch_act1.json J-004, interactables_act1.json K-004 (소설 6장: 칠복이 엮은 개집은 비어 있고, 개 누렁이는 사흘째 안 들어온다. 개는 나중에 풀씨를 묻히고 돌아온다).
그래서 모델 셋을 만든다.
 - prop_gaejip_empty : 빈 개집(J-004 자리용). 개 없음.
 - prop_keep_gaejip : 같은 개집 + 유품 Glow(K-004 '빈 개집'). 짚을 촘촘히 엮은 모양.
 - prop_nureongi    : 누렁이(돌아온 뒤 장면용). 앉은 자세 정적 모델, 털에 풀씨가 묻어 있다. 원점=앞발 사이 바닥.
규약은 interactables.py와 같다(1m, 원점=바닥 한가운데, 정면 -Y, 베이스컬러만)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import interactables as ia
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
STRAW, STRAW_D, FUR, FUR_D = "#C9B15E", "#9C8444", "#C9923A", "#A8742C"

def gaejip():
    """짚을 촘촘히 엮은 둥근 개집 0.9×1.0m, 높이 0.75m. 입구는 앞(-Y)에 어둡게 뚫려 있고, 짚 띠가 가로로 감겼다. 앞에 빈 밥그릇과 풀린 끈."""
    r = random.Random(61)
    p = [lathe("dome", [(0.0, 0.5), (0.2, 0.52), (0.45, 0.44), (0.65, 0.3), (0.76, 0.0)], 10, STRAW, scale=(1.0, 1.05, 1.0), fn=lambda i, k, th, z, rr: (rr * (1 + r.uniform(-0.03, 0.03)), z), skip=lambda i, k: i <= 1 and k in (7, 8)),
         box("door_dark", (0.36, 0.1, 0.4), (0, -0.46, 0.22), "#0A0A10")]
    p += [cyl(f"band{i}", 0.5 - i * 0.07, 0.5 - i * 0.07, 0.035, (0, 0, 0.14 + i * 0.16), STRAW_D, 10, rot=(0, 0, 0.2 * i)) for i in range(4)]
    p += [cyl("bowl", 0.14, 0.1, 0.07, (0.4, -0.6, 0), "#6E5A44", 8), cyl("bowl_in", 0.1, 0.1, 0.01, (0.4, -0.6, 0.065), "#2A2420", 8), limb("cord", (-0.15, -0.5, 0.03), (-0.55, -0.85, 0.02), 0.012, 0.012, "#B4A66A", 4), sphere("cord_knot", 0.03, (-0.15, -0.5, 0.05), "#B4A66A", 4, 3)]
    p += [box(f"straw{i}", (0.03, 0.2, 0.01), (r.uniform(-0.3, 0.3), -0.8 - r.uniform(0, 0.2), 0.01), STRAW, rot=(0, 0, r.uniform(0, 3))) for i in range(6)]
    return p

def nureongi():
    """누렁이: 누런 털의 중간 크기 개가 앞을 보고 앉은 모습. 키 0.6m. 귀가 처지고 꼬리가 땅에 늘어졌다. 털 몇 곳에 풀씨(연두 점)가 묻음."""
    r = random.Random(62)
    p = [sphere("body", 0.26, (0, 0.15, 0.3), FUR, 8, 5, (0.9, 1.25, 1.0)), sphere("chest", 0.2, (0, -0.1, 0.35), "#E0B060", 7, 5, (1.0, 0.9, 1.1)), sphere("head", 0.15, (0, -0.2, 0.58), FUR, 8, 5, (1.0, 1.0, 0.95)), sphere("muzzle", 0.075, (0, -0.33, 0.54), "#E0B060", 6, 4, (1.0, 1.1, 0.8)), sphere("nose", 0.025, (0, -0.4, 0.55), "#14141F", 4, 3)]
    p += [sphere("eyeL", 0.02, (0.06, -0.33, 0.62), "#14141F", 4, 3), sphere("eyeR", 0.02, (-0.06, -0.33, 0.62), "#14141F", 4, 3)]
    for sx in (-1, 1):
        p += [limb(f"ear{sx}", (sx * 0.1, -0.15, 0.68), (sx * 0.19, -0.14, 0.5), 0.05, 0.03, FUR_D, 4), limb(f"leg{sx}", (sx * 0.1, -0.2, 0.3), (sx * 0.1, -0.3, 0.02), 0.06, 0.045, FUR, 5), sphere(f"paw{sx}", 0.05, (sx * 0.1, -0.32, 0.03), "#E0B060", 5, 3, (1, 1.3, 0.6)),
              sphere(f"haunch{sx}", 0.13, (sx * 0.18, 0.28, 0.14), FUR, 6, 4, (1, 1.2, 1.0))]
    p += chain_pts("tail", [(0, 0.45, 0.1), (0.12, 0.62, 0.05), (0.22, 0.72, 0.02)], 0.045, 0.02, FUR_D, 4)
    p += [sphere(f"seed{i}", 0.014, (r.uniform(-0.18, 0.18), r.uniform(-0.1, 0.4), r.uniform(0.3, 0.52)), "#8FB04A", 4, 3) for i in range(7)]   # 풀씨
    return p

def build(name, parts_fn, glow=None):
    reset(); o = join(name, parts_fn())
    if glow: ia.glow_for(o, glow)
    lo, hi = bounds(o)
    export(o, os.path.join(OUT, "props", name + ".glb"))
    return {"name": name, "tris": tris(o) + sum(tris(c) for c in o.children if c.type == "MESH"), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "children": [c.name for c in o.children]}

if __name__ == "__main__":
    rep = [build("prop_gaejip_empty", gaejip), build("prop_keep_gaejip", gaejip, ia.keep_glow), build("prop_nureongi", nureongi)]
    for x in rep: print(x)
    json.dump(rep, open(os.path.join(OUT, "props", "_report_dog.json"), "w"), ensure_ascii=False, indent=1)
    reset(); o = join("a", gaejip()); o2 = join("b", gaejip()); ia.glow_for(o2, ia.keep_glow); o2.location = (2.2, 0, 0); o3 = join("c", nureongi()); o3.location = (4.4, 0, 0)
    setup_render(8, (2.2, 0, 0.3), size=(1100, 500), ground_size=20); render(os.path.join(OUT, "previews", "dog_props_50deg.png"))
