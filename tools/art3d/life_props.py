"""생활감 소품 키트(농촌 풍경·길가·무덤·가축). 실행: python3 life_props.py [이름 ...]
왜: 오너 피드백 '필드가 텅 비어 있다'. 마을·밭·길가·숲 가장자리에 놓을 작은 이야깃거리를 코드로 만든다.
규약은 props.py와 같다: 원점=바닥 한가운데, 정면=-Y, 1단위=1m, 재질은 기본색만."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def haystack():
    """볏가리: 짚단을 원뿔로 쌓고 꼭대기를 묶는다. 지름 2m, 높이 2.1m."""
    return [cyl("stack", 1.0, 0.55, 1.2, (0, 0, 0.1), "thatch", 8), cyl("top", 0.55, 0.0, 0.8, (0, 0, 1.3), "thatch", 8), box("base", (2.0, 2.0, 0.1), (0, 0, 0.05), "wood_dark"), cyl("tie", 0.2, 0.2, 0.08, (0, 0, 1.55), "wood", 6)]

def fence():
    """싸리 울타리 3m: 말뚝 4개에 가로대 두 줄과 가는 세로 막대."""
    p = [cyl(f"post{i}", 0.06, 0.05, 1.1, (-1.5 + i, 0, 0), "wood_dark", 5) for i in range(4)]
    p += [box("rail1", (3.0, 0.05, 0.05), (0, 0, 0.35), "wood"), box("rail2", (3.0, 0.05, 0.05), (0, 0, 0.8), "wood")]
    p += [box(f"twig{i}", (0.03, 0.03, 0.95), (-1.4 + i * 0.2, -0.04, 0.5), "reed") for i in range(15)]
    return p

def cart():
    """수레: 짐칸 1.5×0.9m, 바퀴 둘, 앞으로 뻗은 손잡이 두 개."""
    p = [box("bed", (1.5, 0.9, 0.1), (0, 0, 0.62), "wood")] + [box(f"side{s}", (1.5, 0.06, 0.28), (0, s * 0.42, 0.8), "wood_dark") for s in (-1, 1)]
    p += [cyl(f"wheel{s}", 0.42, 0.42, 0.08, (0, s * 0.52, 0.42), "wood_dark", 10, rot=(math.pi / 2, 0, 0)) for s in (-1, 1)]
    p += [box(f"shaft{s}", (0.06, 1.5, 0.06), (s * 0.35, -1.1, 0.55), "wood", rot=(0.12, 0, 0)) for s in (-1, 1)]
    p += [cyl(f"sack{i}", 0.2, 0.17, 0.4, (-0.35 + i * 0.35, 0, 0.67), "hanji", 6) for i in range(3)]
    return p

def firewood():
    """장작더미: 통나무 3단 쌓기. 1.6×0.7m, 높이 0.7m."""
    p = []
    for row, n in enumerate((6, 5, 4)):
        for i in range(n): p.append(cyl(f"log{row}_{i}", 0.12, 0.12, 0.7, (-0.7 + i * 0.28 + row * 0.14, 0.0, 0.14 + row * 0.2), "bark", 6, rot=(math.pi / 2, 0, 0)))
    p += [box("stakeA", (0.05, 0.05, 0.8), (-0.85, 0.42, 0.4), "wood_dark"), box("stakeB", (0.05, 0.05, 0.8), (0.85, 0.42, 0.4), "wood_dark")]
    return p

def scarecrow():
    """허수아비: 십자 막대에 베옷, 삿갓. 높이 약 2m. 팔을 벌린 정면이 -Y."""
    return [cyl("pole", 0.04, 0.04, 1.9, (0, 0, 0), "wood_dark", 5), box("arms", (1.5, 0.05, 0.05), (0, 0, 1.45), "wood"), cyl("robe", 0.16, 0.3, 0.7, (0, 0, 0.8), "hanji", 6),
            box("sleeveL", (0.45, 0.04, 0.3), (0.5, 0, 1.3), "hanji"), box("sleeveR", (0.45, 0.04, 0.3), (-0.5, 0, 1.3), "hanji"), sphere("head", 0.15, (0, 0, 1.68), "thatch", 6, 5), cyl("hat", 0.34, 0.05, 0.16, (0, 0, 1.78), "reed", 8)]

def wonduumak():
    """원두막: 기둥 넷 위에 마루(높이 1.5m)와 초가 지붕, 사다리. 2.6×2.6m, 높이 3.4m."""
    p = [cyl(f"leg{i}", 0.09, 0.08, 1.5, (sx * 1.1, sy * 1.1, 0), "wood_dark", 5) for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1)))]
    p += [box("floor", (2.6, 2.6, 0.1), (0, 0, 1.55), "wood")] + [cyl(f"post{i}", 0.06, 0.06, 1.3, (sx * 1.15, sy * 1.15, 1.6), "wood_dark", 5) for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1)))]
    p += [cyl("roof", 2.3, 0.15, 0.95, (0, 0, 2.85), "thatch", 4, rot=(0, 0, math.pi / 4))]
    p += [box("ladderL", (0.05, 0.05, 1.6), (-0.25, -1.45, 0.8), "wood", rot=(0.25, 0, 0)), box("ladderR", (0.05, 0.05, 1.6), (0.25, -1.45, 0.8), "wood", rot=(0.25, 0, 0))]
    p += [box(f"rung{i}", (0.5, 0.04, 0.04), (0, -1.4 - 0.0 + i * -0.0, 0.3 + i * 0.3), "wood", rot=(0.25, 0, 0)) for i in range(4)]
    return p

def signpost():
    """이정표(길 갈림 팻말): 기둥에 화살 팻말 둘. 높이 1.9m."""
    return [cyl("post", 0.07, 0.06, 1.9, (0, 0, 0), "wood_dark", 6), box("arrowA", (0.8, 0.05, 0.22), (0.38, -0.07, 1.55), "wood"), box("tipA", (0.18, 0.05, 0.22), (0.84, -0.07, 1.55), "wood", rot=(0, 0, 0.0)),
            box("arrowB", (0.7, 0.05, 0.2), (-0.33, -0.07, 1.2), "wood"), box("tag", (0.2, 0.03, 0.3), (0, -0.08, 0.8), "hanji"), box("capp", (0.2, 0.2, 0.08), (0, 0, 1.92), "wood_dark")]

def grave():
    """봉분(무덤): 둥근 흙무덤과 앞의 작은 상석·비석. 지름 2.4m, 높이 1.1m."""
    return [sphere("mound", 1.2, (0, 0, 0.54), "ground", 8, 5, (1.0, 1.0, 0.45)), box("table", (0.8, 0.45, 0.25), (0, -1.55, 0.125), "stone"), box("stele", (0.35, 0.12, 0.9), (0, -2.05, 0.45), "stone_dark"), box("steleTop", (0.4, 0.14, 0.1), (0, -2.05, 0.93), "stone_dark")]

def cairn():
    """돌탑: 납작한 돌을 쌓아 올린 것(서낭당 곁). 높이 1.4m."""
    return [sphere(f"s{i}", r, (0.04 * ((i % 3) - 1), 0.03 * (i % 2), z + 0.13), "stone" if i % 2 else "stone_dark", 6, 4, (1.2, 1.1, 0.55)) for i, (r, z) in enumerate(((0.55, 0.18), (0.45, 0.46), (0.38, 0.7), (0.3, 0.92), (0.22, 1.1), (0.15, 1.26)))]

def millstone():
    """맷돌: 맷돌 두 짝과 손잡이. 지름 0.9m."""
    return [cyl("bottom", 0.45, 0.45, 0.14, (0, 0, 0), "stone", 10), cyl("top", 0.42, 0.42, 0.14, (0, 0, 0.14), "stone_dark", 10), cyl("handle", 0.03, 0.03, 0.3, (0.3, 0, 0.28), "wood", 5)]

def sacks():
    """곡식 자루 더미: 자루 5개를 두 단으로. 1.2×0.8m."""
    return [cyl(f"sack{i}", 0.22, 0.2, 0.55, ((i % 3 - 1) * 0.42 + (0.2 if i > 2 else 0), (-0.2 if i > 2 else 0.15), 0.0 if i < 3 else 0.5), "hanji" if i % 2 else "reed", 7) for i in range(5)]

def cow():
    """소(누렁소): 몸통·머리·다리 넷·뿔·꼬리. 길이 2m, 높이 1.3m. 머리가 -Y."""
    p = [box("body", (0.75, 1.4, 0.7), (0, 0.1, 0.95), "thatch"), box("head", (0.38, 0.5, 0.4), (0, -0.85, 1.05), "thatch", rot=(0.35, 0, 0)), box("snout", (0.3, 0.2, 0.25), (0, -1.12, 0.85), "mud"),
         box("hump", (0.5, 0.5, 0.25), (0, -0.35, 1.38), "thatch")]
    p += [box(f"leg{i}", (0.16, 0.16, 0.7), (sx * 0.27, sy, 0.35), "thatch") for i, (sx, sy) in enumerate(((-1, -0.45), (1, -0.45), (-1, 0.65), (1, 0.65)))]
    p += [cyl(f"horn{s}", 0.04, 0.0, 0.3, (s * 0.2, -0.78, 1.28), "silver", 5, rot=(0, -s * 0.8, 0)) for s in (-1, 1)] + [box("tail", (0.05, 0.05, 0.6), (0, 0.85, 0.95), "thatch", rot=(0.25, 0, 0))]
    return p

def stepstones():
    """디딤돌 길: 납작한 돌 6개가 구불구불. 길이 4.5m."""
    r = random.Random(7)
    return [cyl(f"st{i}", 0.34 + r.random() * 0.1, 0.3, 0.1, (math.sin(i * 1.1) * 0.35, -2.2 + i * 0.85, 0.0), "stone" if i % 2 else "stone_dark", 7) for i in range(6)]

def log_pile():
    """쓰러진 통나무와 그루터기."""
    return [cyl("log", 0.22, 0.2, 2.2, (0, 0, 0.23), "bark", 7, rot=(0, math.pi / 2, 0)), cyl("stump", 0.3, 0.26, 0.45, (1.6, 0.5, 0.02), "bark", 7), cyl("stumpTop", 0.26, 0.26, 0.03, (1.6, 0.5, 0.45), "wood", 7), cyl("branch", 0.05, 0.03, 0.8, (-0.4, 0.0, 0.35), "bark", 5, rot=(0.9, 0, 0.3))]

def campfire():
    """모닥불: 돌 고리, 장작, 불씨(발광). 밤 소품이라 Light_campfire 표시를 붙인다. 지름 1.1m."""
    p = [sphere(f"rock{i}", 0.13, (math.cos(i * math.tau / 7) * 0.45, math.sin(i * math.tau / 7) * 0.45, 0.13), "stone_dark", 5, 4) for i in range(7)]
    p += [cyl(f"wood{i}", 0.04, 0.04, 0.6, (0, 0, 0.14), "bark", 5, rot=(1.2, 0, i * 1.05)) for i in range(3)]
    p += [cyl("flame", 0.17, 0.0, 0.5, (0, 0, 0.2), mat("gold", 2.2), 6)]
    return p

def mill():
    """방앗간(물레방아 집): 흙벽 4.6×3.6m 초가 + 동쪽 벽에 물레방아(지름 3m). 물레방아 쪽(+X)을 개울에 맞대어 놓는다. 앞=-Y."""
    p = [box("base", (4.8, 3.8, 0.3), (-0.4, 0, 0.15), "stone"), box("wall", (4.4, 3.4, 1.9), (-0.4, 0, 1.25), "mud"), box("door", (1.1, 0.08, 1.5), (-1.2, -1.72, 0.9), "wood_dark"),
         cyl("roof", 3.6, 0.35, 1.4, (-0.4, 0, 2.2), "thatch", 4, rot=(0, 0, math.pi / 4)), box("beamF", (4.6, 0.08, 0.1), (-0.4, -1.75, 2.2), "wood_dark")]
    for sy in (-0.9, 0.9): p.append(box(f"axle{sy}", (1.4, 0.12, 0.12), (2.3, sy, 1.55), "wood_dark"))
    for sy in (-0.7, 0.7):
        p.append(cyl(f"rim{sy}", 1.5, 1.5, 0.08, (2.9, sy, 0.05), "wood", 12, rot=(0, 0, 0)))
    wheel = [cyl("hub", 0.25, 0.25, 1.9, (2.9, 0, 1.55), "wood_dark", 6, rot=(math.pi / 2, 0, 0))]
    for i in range(12):
        a = i * math.tau / 12; c, s = math.cos(a), math.sin(a)
        for sy in (-0.7, 0.7): wheel.append(box(f"spoke{i}_{sy}", (1.5, 0.1, 0.1), (2.9 + c * 0.75, sy, 1.55 + s * 0.75), "wood", rot=(0, -a, 0)))
        wheel.append(box(f"paddle{i}", (0.1, 1.5, 0.45), (2.9 + c * 1.5, 0, 1.55 + s * 1.5), "wood_dark", rot=(0, -a, 0)))
    p = [q for q in p if not q.name.startswith("rim")]
    return p + wheel + [box("chute", (0.3, 1.0, 0.1), (2.9, 0, 3.2), "wood"), box("sackA", (0.5, 0.4, 0.5), (-2.4, -1.3, 0.55), "hanji"), box("sackB", (0.5, 0.4, 0.4), (-2.4, -0.8, 0.5), "reed")]

KIT = [("haystack", haystack, "볏가리"), ("fence", fence, "싸리 울타리 3m"), ("cart", cart, "수레"), ("firewood", firewood, "장작더미"), ("scarecrow", scarecrow, "허수아비"),
       ("wonduumak", wonduumak, "원두막"), ("signpost", signpost, "이정표"), ("grave", grave, "봉분 무덤"), ("cairn", cairn, "돌탑"), ("millstone", millstone, "맷돌"),
       ("sacks", sacks, "곡식 자루"), ("cow", cow, "소"), ("stepstones", stepstones, "디딤돌"), ("log_pile", log_pile, "통나무와 그루터기"), ("campfire", campfire, "모닥불(불빛)"), ("mill", mill, "방앗간(물레방아)")]

def build(key, fn):
    reset(); o = join(f"prop_{key}", fn()); lo, hi = bounds(o)
    if key == "campfire": light_empty(o, "Light_campfire", (0, 0, 0.6), "#FFB066", intensity=1.1, range_m=9.0, flicker=True)
    info = {"name": f"prop_{key}", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}
    export(o, os.path.join(OUT, "props", f"prop_{key}.glb")); return info

if __name__ == "__main__":
    import json
    want = sys.argv[1:]; res = [build(k, f) for k, f, n in KIT if not want or k in want]
    for r in res: print(r)
    json.dump(res, open(os.path.join(OUT, "props", "_report_life.json"), "w"), ensure_ascii=False, indent=1)
    if not want:   # 한 장 미리보기: 5열 3행
        reset(); objs = []
        for i, (k, f, n) in enumerate(KIT):
            o = join(f"prop_{k}", f()); o.location = ((i % 5 - 2) * 4.2, -(i // 5) * 4.2 + 4.2, 0); objs.append(o)
        setup_render(24, (0, 0, 1.0), size=(1280, 840), ground_size=40); render(os.path.join(OUT, "previews", "life_props_15.png"))
