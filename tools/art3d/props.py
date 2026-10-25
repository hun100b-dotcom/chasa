"""한국 소품 키트 10종. 실행: python3 props.py [이름 ...]  (이름 생략하면 전부)
각 함수는 바닥 한가운데를 원점으로, 정면(-Y, 내보내면 +Z)을 보는 모델을 만들어 돌려준다."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
TAU = math.tau

def choga():
    """초가: 흙벽 + 짚 지붕. 4×3m, 높이 약 3.1m."""
    p = [box("base", (4.4, 3.4, 0.25), (0, 0, 0.125), "stone"),
         box("wall", (4.0, 3.0, 2.0), (0, 0, 1.25), "mud"),
         pyramid("roof", 5.2, 4.2, 1.1, (0, 0, 2.2), "thatch", top=0.0) if False else prism("roof", 5.2, 4.2, 1.25, (0, 0, 2.2), "thatch"),
         box("roof_rim", (5.2, 0.12, 0.18), (0, -2.1, 2.25), "thatch"),
         box("door", (0.85, 0.08, 1.5), (0.7, -1.54, 1.0), "wood_dark"),
         box("window", (0.7, 0.08, 0.6), (-1.1, -1.54, 1.55), "wood_dark"),
         box("step", (1.1, 0.5, 0.15), (0.7, -1.85, 0.075), "stone_dark"),
         box("firewood", (0.9, 0.35, 0.5), (-1.6, -1.75, 0.3), "wood")]
    return p

def giwa():
    """기와집: 기단 + 붉은 기둥 + 흰 벽 + 검은 기와 + 처마 끝 올림. 6×4m, 높이 약 4m."""
    p = [box("gidan", (6.4, 4.6, 0.5), (0, 0, 0.25), "stone"),
         box("wall", (5.6, 3.6, 2.2), (0, 0, 1.6), "hanji")]
    for i, x in enumerate((-2.8, -0.95, 0.95, 2.8)):
        p.append(box(f"pillar{i}", (0.22, 0.22, 2.3), (x, -1.85, 1.65), "pillar"))
    p += [box("beam", (6.0, 0.25, 0.25), (0, -1.85, 2.9), "pillar"),
          box("door", (1.6, 0.08, 1.7), (0, -1.82, 1.45), "wood_dark"),
          prism("roof", 7.6, 5.8, 1.5, (0, 0, 2.9), "tile")]
    for sx in (-1, 1):  # 처마 끝이 살짝 올라간 모양
        p.append(box(f"eave{sx}", (0.5, 6.0, 0.18), (sx * 3.85, 0, 3.05), "tile", rot=(0, sx * 0.35, 0)))
    p.append(box("ridge", (7.8, 0.3, 0.28), (0, 0, 4.4), "tile"))
    return p

def dolddam():
    """돌담: 둥근 돌을 엇갈려 쌓은 3m 한 토막, 높이 1.1m. 이어 붙이기 쉽게 양끝 길이를 3m로 맞춘다."""
    r = random.Random(7); p = []
    rows = [(0.0, 5), (0.34, 4), (0.66, 5), (0.96, 4)]
    for ri, (z, n) in enumerate(rows):
        w = 3.0 / n
        for i in range(n):
            x = -1.5 + w * (i + 0.5) + (r.random() - .5) * 0.05
            s = (w * 0.98, 0.5 + r.random() * 0.08, 0.34 + r.random() * 0.04)
            p.append(box(f"s{ri}_{i}", s, (x, (r.random() - .5) * 0.06, z + s[2] / 2), "stone" if (ri + i) % 3 else "stone_dark", rot=(0, 0, (r.random() - .5) * 0.2)))
    p.append(box("cap", (3.0, 0.62, 0.12), (0, 0, 1.2), "thatch"))
    return p

def jangdok():
    """장독대: 돌 바닥 위에 항아리 6개. 크기 3.0×1.8m."""
    p = [box("plat", (3.0, 1.8, 0.2), (0, 0, 0.1), "stone")]
    spots = [(-1.0, -0.45, 0.42), (0.0, -0.5, 0.5), (1.0, -0.45, 0.4), (-0.7, 0.4, 0.34), (0.15, 0.45, 0.4), (1.0, 0.4, 0.3)]
    for i, (x, y, r) in enumerate(spots):
        h = r * 2.0
        p += [cyl(f"jar{i}a", r * 0.72, r, h * 0.55, (x, y, 0.2), "jar", 8),
              cyl(f"jar{i}b", r, r * 0.55, h * 0.4, (x, y, 0.2 + h * 0.55), "jar", 8),
              cyl(f"jar{i}lid", r * 0.5, r * 0.42, h * 0.12, (x, y, 0.2 + h * 0.95), "wood_dark", 8)]
    return p

def sotdae():
    """솟대: 긴 장대 끝에 새 세 마리. 높이 5m."""
    p = [cyl("pole", 0.11, 0.07, 4.6, (0, 0, 0), "wood", 6), cyl("foot", 0.3, 0.2, 0.35, (0, 0, 0), "stone", 6)]
    for i, (dz, a) in enumerate([(4.5, 0), (3.95, 2.2), (3.45, 4.2)]):
        ox, oy = math.cos(a) * 0.12, math.sin(a) * 0.12
        p += [cyl(f"bird{i}b", 0.11, 0.05, 0.4, (ox, oy, dz), "wood", 5, rot=(0, math.pi / 2, a)),
              sphere(f"bird{i}h", 0.07, (ox + math.cos(a) * 0.22, oy + math.sin(a) * 0.22, dz + 0.1), "wood", 5, 4),
              box(f"bird{i}t", (0.28, 0.12, 0.03), (ox - math.cos(a) * 0.3, oy - math.sin(a) * 0.3, dz + 0.02), "wood")]
    return p

def geumjul():
    """금줄: 기둥 둘 사이에 새끼줄을 늘이고 한지 종이를 단다. 폭 3.4m."""
    p = [cyl("postL", 0.09, 0.07, 1.8, (-1.7, 0, 0), "wood", 6), cyl("postR", 0.09, 0.07, 1.8, (1.7, 0, 0), "wood", 6)]
    n = 8; pts = []
    for i in range(n + 1):
        t = i / n; x = -1.7 + 3.4 * t
        z = 1.65 - 0.28 * math.sin(math.pi * t)   # 가운데가 처진 줄
        pts.append((x, 0, z))
    for i in range(n):
        a, b = Vector(pts[i]), Vector(pts[i + 1]); mid = (a + b) / 2; d = b - a
        p.append(box(f"rope{i}", (d.length, 0.045, 0.045), mid, "thatch", rot=(0, -math.atan2(d.z, d.x), 0)))
    for i in range(1, n, 1):
        x, _, z = pts[i]
        p.append(box(f"paper{i}", (0.1, 0.02, 0.32), (x, 0, z - 0.2), "hanji"))
    return p

def seonangdang():
    """서낭당: 당산나무 + 돌무더기 + 작은 당집 + 걸린 천. 나무 높이 약 6.5m, 폭 약 5m."""
    p = [cyl("trunk", 0.55, 0.32, 3.4, (-1.0, 0.6, 0), "bark", 7),
         cyl("root", 0.8, 0.55, 0.45, (-1.0, 0.6, 0), "bark", 7)]
    for i, (x, y, z, r) in enumerate([(-1.0, 0.6, 5.0, 1.9), (-2.0, 0.5, 4.2, 1.35), (0.0, 0.9, 4.4, 1.4), (-1.0, -0.3, 4.1, 1.2)]):
        p.append(sphere(f"crown{i}", r, (x, y, z), "leaf" if i % 2 == 0 else "leaf_dark", 7, 5, (1, 1, 0.8)))
    r = random.Random(3)
    for i in range(9):  # 돌무더기
        a = r.random() * TAU; d = r.random() * 0.7
        rr = 0.28 + r.random() * 0.15
        p.append(sphere(f"rock{i}", rr, (1.5 + math.cos(a) * d, -0.2 + math.sin(a) * d, rr * 0.75 + (0.28 if d < 0.35 else 0)), "stone" if i % 2 else "stone_dark", 6, 4, (1, 1, 0.75)))
    p += [box("hut_base", (1.5, 1.2, 0.2), (1.6, 1.6, 0.1), "stone"),
          box("hut", (1.2, 0.9, 1.0), (1.6, 1.6, 0.7), "pillar"),
          prism("hut_roof", 1.7, 1.4, 0.6, (1.6, 1.6, 1.2), "tile"),
          box("hut_door", (0.45, 0.04, 0.7), (1.6, 1.13, 0.6), "wood_dark")]
    for i, (c, a) in enumerate([("red", 0.0), ("blue_cloth", 2.1), ("yellow_cloth", 4.2), ("hanji", 5.2)]):  # 나무에 매단 오방색 천
        ox, oy = -1.0 + math.cos(a) * 0.5, 0.6 + math.sin(a) * 0.5
        p.append(box(f"cloth{i}", (0.08, 0.02, 0.7), (ox, oy, 2.5 - (i % 2) * 0.2), c))
    p.append(box("rope", (1.2, 0.05, 0.05), (-1.0, 0.6, 2.9), "thatch"))
    return p

def sangyeo():
    """상여: 두 장대에 얹은 꽃상여. 길이 5m, 높이 약 2.4m."""
    p = [box("poleL", (5.0, 0.12, 0.12), (0, -0.55, 0.9), "wood"), box("poleR", (5.0, 0.12, 0.12), (0, 0.55, 0.9), "wood"),
         box("deck", (2.6, 1.4, 0.18), (0, 0, 1.1), "wood_dark"),
         box("body", (2.2, 1.1, 0.8), (0, 0, 1.6), "hanji"),
         box("stripe", (2.24, 1.14, 0.14), (0, 0, 1.3), "red"),
         pyramid("roof", 2.9, 1.8, 0.7, (0, 0, 2.0), "tile", top=0.55)]
    for i, x in enumerate((-2.0, -0.7, 0.7, 2.0)):
        p.append(box(f"crossL{i}", (0.1, 0.1, 0.9), (x, -0.55, 0.45), "wood"))
    for sx in (-1, 1): p.append(box(f"tassel{sx}", (0.06, 0.06, 0.4), (sx * 1.4, 0, 1.85), "red"))
    return p

def umul():
    """우물: 돌 둘레 + 두레박 지붕 틀. 폭 1.6m, 높이 약 2.1m."""
    p = []
    n = 8
    for i in range(n):
        a = i / n * TAU
        p.append(box(f"ring{i}", (0.42, 0.22, 0.55), (math.cos(a) * 0.48, math.sin(a) * 0.48, 0.275), "stone" if i % 2 else "stone_dark", rot=(0, 0, a + math.pi / 2)))
    p += [cyl("water", 0.36, 0.36, 0.05, (0, 0, 0.3), "water", 8),
          box("postL", (0.12, 0.12, 1.7), (-0.65, 0, 0.85), "wood"), box("postR", (0.12, 0.12, 1.7), (0.65, 0, 0.85), "wood"),
          box("beam", (1.5, 0.14, 0.14), (0, 0, 1.7), "wood"),
          prism("roof", 1.9, 1.3, 0.45, (0, 0, 1.75), "thatch", rot=(0, 0, math.pi / 2)) if False else prism("roof", 1.9, 1.3, 0.45, (0, 0, 1.75), "thatch"),
          box("rope", (0.03, 0.03, 0.55), (0, 0, 1.4), "thatch"), cyl("bucket", 0.12, 0.1, 0.18, (0, 0, 1.1), "wood_dark", 6)]
    return p

def jangseung():
    """장승: 얼굴을 새긴 나무 기둥. 높이 2.6m."""
    p = [cyl("post", 0.26, 0.24, 2.0, (0, 0, 0), "wood", 6),
         box("head", (0.62, 0.5, 0.72), (0, 0, 2.15), "wood"),
         box("hat", (0.78, 0.62, 0.2), (0, 0, 2.6), "wood_dark"),
         box("browL", (0.2, 0.05, 0.05), (-0.16, -0.27, 2.32), "ink", rot=(0, 0.25, 0)), box("browR", (0.2, 0.05, 0.05), (0.16, -0.27, 2.32), "ink", rot=(0, -0.25, 0)),
         box("eyeL", (0.13, 0.05, 0.1), (-0.16, -0.26, 2.2), "hanji"), box("eyeR", (0.13, 0.05, 0.1), (0.16, -0.26, 2.2), "hanji"),
         box("pupilL", (0.05, 0.06, 0.07), (-0.16, -0.27, 2.2), "ink"), box("pupilR", (0.05, 0.06, 0.07), (0.16, -0.27, 2.2), "ink"),
         box("nose", (0.12, 0.12, 0.22), (0, -0.3, 2.1), "wood_dark"),
         box("mouth", (0.3, 0.05, 0.08), (0, -0.27, 1.9), "red"),
         box("tooth", (0.1, 0.06, 0.08), (-0.08, -0.27, 1.86), "hanji"),
         box("sash", (0.55, 0.03, 0.1), (0, -0.25, 1.55), "red")]
    return p

PROPS = {"choga": choga, "giwa": giwa, "dolddam": dolddam, "jangdok": jangdok, "sotdae": sotdae, "geumjul": geumjul,
         "seonangdang": seonangdang, "sangyeo": sangyeo, "umul": umul, "jangseung": jangseung}
NAMES = {"choga": "초가", "giwa": "기와집", "dolddam": "돌담", "jangdok": "장독대", "sotdae": "솟대", "geumjul": "금줄",
         "seonangdang": "서낭당", "sangyeo": "상여", "umul": "우물", "jangseung": "장승"}

def build(key, preview=True):
    reset()
    o = join(f"prop_{key}", PROPS[key]())
    lo, hi = bounds(o)
    info = {"name": f"prop_{key}", "label": NAMES[key], "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)],
            "min_z": round(lo.z, 3), "materials": len(o.data.materials)}
    export(o, os.path.join(OUT, "props", f"prop_{key}.glb"))
    if preview:
        c = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (hi.z) / 2)
        setup_render(max(hi.x - lo.x, hi.z * 1.2, 2.5) * 1.45, c, ground_size=30)
        render(os.path.join(OUT, "previews", f"prop_{key}.png"))
    return info

if __name__ == "__main__":
    import json
    keys = sys.argv[1:] or list(PROPS)
    res = [build(k) for k in keys]
    for r in res: print(r)
    json.dump(res, open(os.path.join(OUT, "props", "_report_props.json"), "w"), ensure_ascii=False, indent=1)
