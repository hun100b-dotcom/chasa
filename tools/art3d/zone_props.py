"""구역 개성 소품: 폐당집 무덤 터(1막)와 검은여울 역병 분위기(2막). 실행: python3 zone_props.py [이름 ...]
규약은 life_props.py와 같다(원점=바닥 한가운데, 정면=-Y, 1단위=1m)."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def ruined_shrine():
    """무너진 당집: 돌 기단 8×6m(계단), 기둥 6개 중 2개 부러짐, 내려앉은 지붕 반쪽, 넘어진 들보, 금줄과 부적, 보랏빛 혼불 등. 높이 약 3.4m."""
    p = [box("base", (8.4, 6.4, 0.5), (0, 0, 0.25), "stone"), box("step1", (2.6, 0.5, 0.2), (0, -3.4, 0.1), "stone"), box("step2", (2.2, 0.5, 0.2), (0, -3.15, 0.3), "stone_dark")]
    for i, (x, y, h) in enumerate(((-3, -2, 2.6), (0, -2, 2.6), (3, -2, 1.1), (-3, 2, 2.6), (0, 2, 0.8), (3, 2, 2.6))):
        p.append(cyl(f"pillar{i}", 0.2, 0.17, h, (x, y, 0.5), "pillar" if h > 2 else "wood_dark", 6))
    p += [box("wallBack", (6.6, 0.3, 2.2), (0, 2.8, 1.6), "mud"), box("wallSide", (0.3, 3.0, 1.5), (-3.4, 0.6, 1.25), "mud")]
    p += [cyl("roofHalf", 4.4, 0.4, 1.3, (-1.6, 0.6, 2.8), "thatch", 4, rot=(0.25, 0.1, math.pi / 4)), box("beamFall", (4.0, 0.25, 0.25), (1.4, -1.2, 0.75), "wood_dark", rot=(0, 0.25, 0.5)), box("beamFall2", (2.4, 0.2, 0.2), (2.0, 0.6, 0.65), "wood", rot=(0, -0.2, -0.4))]
    p += [box("rope", (5.5, 0.04, 0.04), (0, -2.05, 2.15), "thatch")] + [box(f"charm{i}", (0.14, 0.02, 0.4), (-2.2 + i * 1.1, -2.07, 1.9), "hanji", rot=(0, 0, 0.05 * (i % 3 - 1))) for i in range(5)]
    p += [box("altar", (1.4, 0.7, 0.55), (0, 1.8, 0.775), "stone_dark"), sphere("fire", 0.16, (0, 1.8, 1.25), mat("soul_lump", 2.0), 6, 4)]
    return p + [sphere(f"rubble{i}", 0.3, (-3.8 + i * 0.7, -3.6 - (i % 2) * 0.4, 0.2), "stone", 5, 4, (1.3, 1, 0.6)) for i in range(5)]

def tomb_old():
    """오래된 무덤: 반쯤 내려앉은 봉분, 기울어진 비석, 깨진 상석. 지름 2.2m."""
    return [sphere("mound", 1.1, (0, 0, 0.35), "slope_side", 7, 4, (1.0, 1.0, 0.32)), sphere("hollow", 0.45, (0.2, 0.1, 0.34), "ink", 6, 4, (1.0, 1.0, 0.18)),
            box("stele", (0.4, 0.12, 1.0), (-0.3, -1.45, 0.5), "stone_dark", rot=(0.0, 0.28, 0.2)), box("slabA", (0.6, 0.4, 0.14), (0.2, -0.95, 0.07), "stone", rot=(0, 0, 0.3)), box("slabB", (0.4, 0.35, 0.12), (0.75, -1.1, 0.06), "stone_dark", rot=(0, 0, -0.5)), sphere("candle", 0.08, (0.2, -0.95, 0.22), mat("soul_fresh", 2.5), 5, 4), box("paper", (0.12, 0.02, 0.3), (-0.3, -1.52, 1.15), "hanji", rot=(0, 0.28, 0.2))]

def mangjang():
    """만장(장례 깃발) 세 줄: 긴 대에 흰 천과 붉은 글씨 띠. 높이 3.6m."""
    p = []
    for i, x in enumerate((-1.0, 0.0, 1.0)):
        h = 3.6 - i * 0.3
        p += [cyl(f"pole{i}", 0.04, 0.03, h, (x, 0, 0), "wood_dark", 5), box(f"cloth{i}", (0.55, 0.03, 1.6), (x + 0.3, 0, h - 0.9), "hanji", rot=(0, 0, 0.06 * (i - 1))), box(f"ink{i}", (0.1, 0.035, 0.9), (x + 0.3, -0.01, h - 0.9), "ink")]
    return p + [box("tie", (2.6, 0.05, 0.05), (0, 0, 0.9), "thatch")]

def soulfire_lantern():
    """혼불 석등: 돌 기둥 위 등불방에 푸른 혼불. 높이 1.8m. Light_soulfire_lantern."""
    return [cyl("foot", 0.35, 0.3, 0.2, (0, 0, 0), "stone", 6), cyl("pillar", 0.14, 0.12, 0.8, (0, 0, 0.2), "stone", 6), cyl("lampBase", 0.3, 0.3, 0.12, (0, 0, 1.0), "stone_dark", 6),
            box("lampBody", (0.34, 0.34, 0.34), (0, 0, 1.12), "stone"), sphere("flame", 0.12, (0, 0, 1.28), mat("soul_fresh", 2.2), 6, 4), cyl("roof", 0.42, 0.05, 0.3, (0, 0, 1.46), "stone_dark", 6)]

def plague_rope():
    """역병 금줄: 기둥 둘 사이 금줄에 붉은 부적과 쑥 다발. 폭 4m, 높이 2m. 길을 막는 경고."""
    p = [cyl(f"post{s}", 0.07, 0.06, 2.2, (s * 2.0, 0, 0), "wood_dark", 5) for s in (-1, 1)] + [box("rope", (4.0, 0.05, 0.05), (0, 0, 1.85), "thatch"), box("rope2", (4.0, 0.05, 0.05), (0, 0, 1.55), "thatch")]
    p += [box(f"charm{i}", (0.14, 0.02, 0.42), (-1.5 + i * 0.75, -0.03, 1.5), "red") for i in range(5)] + [cyl(f"herb{i}", 0.09, 0.03, 0.35, (-1.1 + i * 1.1, -0.03, 1.2), "leaf", 5, rot=(math.pi, 0, 0)) for i in range(3)]
    return p

def quarantine_hut():
    """격리 움막: 기둥 둘에 기대 세운 짚 지붕과 거적 문. 3×2.6m, 높이 1.9m."""
    return [cyl("postL", 0.07, 0.06, 1.9, (-1.3, -1.1, 0), "wood_dark", 5), cyl("postR", 0.07, 0.06, 1.9, (1.3, -1.1, 0), "wood_dark", 5), box("roof", (3.2, 3.2, 0.12), (0, 0.2, 1.0), "thatch", rot=(0.62, 0, 0)),
            box("matDoor", (1.1, 0.06, 1.2), (0, -1.08, 0.6), "reed"), box("floor", (2.8, 2.2, 0.08), (0, 0.4, 0.04), "wood_dark"), box("sideL", (0.08, 2.2, 1.0), (-1.4, 0.4, 0.5), "reed"), box("sideR", (0.08, 2.2, 1.0), (1.4, 0.4, 0.5), "reed"),
            box("backW", (2.8, 0.08, 1.1), (0, 1.45, 0.55), "reed"), box("ribbon", (0.05, 0.03, 0.5), (0.6, -1.12, 1.5), "red")]

def herb_pot():
    """약탕 화로: 돌 화로 위 약탕관에서 푸른 기운이 오른다. Light_herb_pot(연한 연두 불빛). 높이 1m."""
    return [cyl("hearth", 0.5, 0.42, 0.4, (0, 0, 0), "stone_dark", 7), cyl("embers", 0.36, 0.36, 0.05, (0, 0, 0.4), mat("gold", 1.6), 7), cyl("potBody", 0.34, 0.26, 0.32, (0, 0, 0.5), "jar", 8), cyl("potTop", 0.2, 0.2, 0.1, (0, 0, 0.82), "wood_dark", 8),
            sphere("steam", 0.16, (0, 0, 1.1), mat("#8BD6A0", 1.2), 6, 4), box("fan", (0.45, 0.02, 0.3), (0.65, -0.1, 0.25), "thatch", rot=(0, 0, 0.5)), box("stoolSeat", (0.5, 0.4, 0.05), (-0.95, 0.0, 0.34), "wood"), cyl("stoolLeg", 0.1, 0.08, 0.34, (-0.95, 0, 0), "wood_dark", 5)]

def foul_pool():
    """독기 웅덩이: 납작한 탁한 녹갈색 물. 지름 3m, 높이 0.04m(바닥 위에 얹는 장식). 가운데 부글 거품."""
    return [cyl("pool", 1.5, 1.4, 0.04, (0, 0, 0), "#33402B", 9)] + [sphere(f"bubble{i}", 0.12 + 0.03 * (i % 3), (math.cos(i * 1.9) * 0.7, math.sin(i * 1.9) * 0.7, 0.05), mat("#8BD6A0", 0.7), 5, 4, (1, 1, 0.5)) for i in range(5)]

def sick_mats():
    """병자 거적자리: 거적 세 장에 누운 이불 모양. 4×2m."""
    p = []
    for i, x in enumerate((-1.3, 0.0, 1.3)):
        p += [box(f"mat{i}", (1.0, 1.9, 0.05), (x, 0, 0.025), "reed"), box(f"quilt{i}", (0.8, 1.2, 0.14), (x, 0.2, 0.12), "hanji" if i != 1 else "blue_cloth"), sphere(f"head{i}", 0.14, (x, -0.55, 0.15), "face", 5, 4)]
    return p

def plague_banner():
    """역병 깃발: 낮은 대에 흰 깃발과 붉은 X 부적. 높이 2.4m."""
    return [cyl("pole", 0.05, 0.04, 2.4, (0, 0, 0), "wood_dark", 5), box("flag", (0.8, 0.03, 1.1), (0.45, 0, 1.75), "hanji"), box("x1", (0.7, 0.035, 0.08), (0.45, -0.01, 1.75), "red", rot=(0, 0.75, 0)), box("x2", (0.7, 0.035, 0.08), (0.45, -0.01, 1.75), "red", rot=(0, -0.75, 0)), cyl("cap", 0.07, 0.0, 0.2, (0, 0, 2.4), "red", 5)]

# ── 길목 랜드마크(걸을 때 눈에 걸리는 큰 것) ────────────────────────────────────────────────
def big_rock():
    """큰 바위: 높이 3.6m, 폭 5m의 바위 무더기와 이끼 윗면. 길가 이정표 노릇."""
    p = [sphere("main", 2.3, (0, 0, 1.96), "stone_dark", 7, 5, (1.15, 0.95, 0.85)), sphere("side", 1.5, (2.0, -0.6, 1.13), "stone", 6, 4, (1.1, 1.0, 0.75)), sphere("small", 1.0, (-2.2, 0.8, 0.6), "stone", 6, 4, (1.2, 1.0, 0.6)), sphere("moss", 1.5, (-0.2, 0.1, 3.1), "leaf_dark", 6, 4, (1.2, 1.0, 0.35))]
    return p + [sphere(f"pebble{i}", 0.3, (math.cos(i * 1.7) * 3.2, math.sin(i * 1.7) * 2.6, 0.18), "stone", 5, 4, (1.2, 1, 0.6)) for i in range(5)]

def old_tree():
    """고목(당산나무): 줄기 지름 1.8m, 높이 8m. 굵은 줄기에 금줄과 흰 종이, 넓은 잎 덩어리. 높이 8.5m."""
    p = [cyl("trunk", 0.95, 0.65, 4.8, (0, 0, 0), "bark", 8), cyl("rootA", 0.5, 0.2, 0.8, (0.9, 0.3, 0.35), "bark", 5, rot=(0, 1.0, 0)), cyl("rootB", 0.5, 0.2, 0.8, (-0.9, -0.4, 0.35), "bark", 5, rot=(0, -1.0, 0)),
         cyl("limbL", 0.35, 0.2, 2.6, (-0.5, 0, 3.6), "bark", 6, rot=(0, -0.9, 0)), cyl("limbR", 0.35, 0.2, 2.6, (0.5, 0, 3.8), "bark", 6, rot=(0, 0.9, 0))]
    p += [sphere("crownA", 2.8, (0, 0, 6.6), "zelkova_dark", 7, 5, (1.0, 1.0, 0.8)), sphere("crownB", 2.2, (-2.7, 0.5, 5.4), "zelkova", 7, 5, (1.0, 1.0, 0.8)), sphere("crownC", 2.2, (2.7, -0.4, 5.6), "zelkova_dark", 7, 5, (1.0, 1.0, 0.8))]
    p += [cyl("ring", 0.85, 0.85, 0.08, (0, 0, 1.4), "thatch", 8)] + [box(f"paper{i}", (0.1, 0.02, 0.3), (math.cos(i * 1.57) * 0.88, math.sin(i * 1.57) * 0.88, 1.15), "hanji") for i in range(4)] + [sphere("hollow", 0.35, (0, -0.85, 0.7), "ink", 5, 4, (1, 0.4, 1.3))]
    return p

def small_shrine():
    """사당(작은 당집): 돌 기단 위 3×3m 한 칸 집, 맞배지붕, 앞 등불. 높이 3.2m. 정면 -Y. Light_small_shrine."""
    p = [box("base", (3.6, 3.6, 0.4), (0, 0, 0.2), "stone"), box("step", (1.4, 0.5, 0.2), (0, -2.0, 0.1), "stone_dark")]
    p += [cyl(f"pillar{i}", 0.1, 0.09, 2.0, (sx * 1.2, sy * 1.2, 0.4), "pillar", 6) for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1)))]
    p += [box("back", (2.5, 0.12, 1.9), (0, 1.2, 1.35), "mud"), box("door", (1.1, 0.08, 1.6), (0, -1.15, 1.2), "wood_dark"), box("roof", (4.2, 4.0, 0.14), (0, 0, 2.55), "thatch"), cyl("ridge", 2.4, 0.2, 0.8, (0, 0, 2.55), "thatch", 4, rot=(0, 0, math.pi / 4)),
          cyl("lampPost", 0.04, 0.04, 1.2, (1.7, -1.9, 0.4), "wood_dark", 5), sphere("lamp", 0.12, (1.7, -1.9, 1.6), mat("gold", 1.6), 6, 4)]
    return p

def pass_cairn():
    """고갯마루 돌무더기: 지름 3m 돌무더기 위에 솟대와 금줄, 헝겊 띠. 높이 3.4m. 지나가는 이가 돌을 얹는 곳."""
    p = [sphere(f"pile{i}", 0.55 + 0.05 * (i % 3), (math.cos(i * 0.85) * (0.9 - i * 0.05), math.sin(i * 0.85) * (0.9 - i * 0.05), 0.35 + i * 0.07), "stone" if i % 2 else "stone_dark", 5, 4, (1.2, 1.1, 0.7)) for i in range(14)]
    p += [cyl("pole", 0.05, 0.04, 3.4, (0, 0, 0.4), "wood_dark", 5), sphere("bird", 0.14, (0, 0, 3.55), "wood", 5, 4), box("rope", (1.8, 0.04, 0.04), (0.9, 0, 2.7), "thatch", rot=(0, 0.2, 0))]
    return p + [box(f"rag{i}", (0.08, 0.02, 0.5), (0.2 + i * 0.3, 0, 2.45), "red" if i % 2 else "hanji") for i in range(4)]

KIT = [("ruined_shrine", ruined_shrine, "무너진 당집"), ("tomb_old", tomb_old, "오래된 무덤"), ("mangjang", mangjang, "만장"), ("soulfire_lantern", soulfire_lantern, "혼불 석등"),
       ("plague_rope", plague_rope, "역병 금줄"), ("quarantine_hut", quarantine_hut, "격리 움막"), ("herb_pot", herb_pot, "약탕 화로"), ("foul_pool", foul_pool, "독기 웅덩이"), ("sick_mats", sick_mats, "병자 거적"), ("plague_banner", plague_banner, "역병 깃발"),
       ("big_rock", big_rock, "큰 바위"), ("old_tree", old_tree, "고목"), ("small_shrine", small_shrine, "사당"), ("pass_cairn", pass_cairn, "고갯마루 돌무더기")]
LIGHTS = {"small_shrine": ("Light_small_shrine", (1.7, -1.9, 1.6), "#FFB066", 0.9, 8.0), "ruined_shrine": ("Light_ruined_shrine", (0, 1.8, 1.3), "#B58CFF", 1.0, 10.0), "soulfire_lantern": ("Light_soulfire_lantern", (0, 0, 1.28), "#9FDCFF", 0.8, 7.0), "herb_pot": ("Light_herb_pot", (0, 0, 1.0), "#A8E6B8", 0.7, 6.0)}

def build(key, fn):
    reset(); o = join(f"prop_{key}", fn()); lo, hi = bounds(o)
    if key in LIGHTS: n, pos, col, it, rg = LIGHTS[key]; light_empty(o, n, pos, col, intensity=it, range_m=rg, flicker=True)
    export(o, os.path.join(OUT, "props", f"prop_{key}.glb"))
    return {"name": f"prop_{key}", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}

if __name__ == "__main__":
    import json
    want = sys.argv[1:]; res = [build(k, f) for k, f, n in KIT if not want or k in want]
    for r in res: print(r)
    json.dump(res, open(os.path.join(OUT, "props", "_report_zone.json"), "w"), ensure_ascii=False, indent=1)
    if not want:
        reset()
        for i, (k, f, n) in enumerate(KIT): o = join(f"prop_{k}", f()); o.location = ((i % 5 - 2) * 9, -(i // 5) * 9 + 9, 0)
        setup_render(52, (0, 0, 1.0), size=(1280, 900), ground_size=60); render(os.path.join(OUT, "previews", "zone_props_14.png"))
