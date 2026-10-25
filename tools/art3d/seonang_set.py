"""시즌 1 서낭당 5곳 외형 차별화 + 3D 넋길 입구(혼불 줄) 모델.
왜 이렇게: 서낭당은 쉬기·넋길 이동의 거점인데 지금은 다섯 곳이 같은 모델이라 '어디에 왔는가'가 안 읽힌다. 멀리서도 구역이 보이도록
 ① 솔고개 마을 = 가장 가꿔진 곳(장승 한 쌍·금줄·제물상·오방색 헝겊)  ② 보릿들 = 농사(솟대·짚단·보리 이삭 단지·장승 하나)
 ③ 물막이 골 = 물가(이끼 낀 높은 돌탑·물동이·소금 무더기·기운 장승·푸른 헝겊)  ④ 검은여울 = 역병(끊어진 금줄·재 원·소금 선·당집 문에 엇댄 널·잿빛 헝겊)
 ⑤ 폐당집 어귀 = 폐허(고사목·쓰러진 장승·내려앉은 지붕·깨진 그릇·꺼진 향·혼불 하나)
로 **먼 실루엣(장승 수, 솟대, 고사목, 돌탑 높이)** 과 **헝겊 색**을 다르게 했다. 몸통(나무·돌무더기·당집) 자리는 기존 prop_seonangdang와 같아 파일만 바꿔 끼우면 된다.
넋길 입구는 '서낭당 혼불 줄'(IP 점검: 둥근 문·돌 고리 금지): 말뚝 둘 + 늘어진 새끼줄 + 매달린 혼불 다섯. 길 따라 세우는 혼불 등(prop_soulpath_lamp)은 따로.
실행: python3 seonang_set.py → assets3d/props/prop_seonangdang_{solgogae,boritdeul,mulmagi,geomeun,pyedang}.glb, prop_soulpath_gate(_off).glb, prop_soulpath_lamp(_off).glb, 미리보기 previews/seonang_set_50deg.png"""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import props as P
from interactables import disc

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); TAU = math.tau
FLAME, FLAME_CORE = "#9A5CFF", "#E6D6FF"   # 혼불색(보라). 주황은 파혼 전용이라 쓰지 않는다
IRON, WOOD_D = "#3A3A44", "#4A3322"

def placed(o, loc, rot=(0, 0, 0), scale=1.0):
    """합친 소품 하나를 자리·방향·크기에 놓는다(나중에 전체 join 때 변환이 적용됨)."""
    o.location = loc; o.rotation_euler = rot; o.scale = (scale,) * 3; return o

def drop(parts, *prefixes):
    """기본 서낭당 조각 중 이름이 prefix로 시작하는 것을 지운다(헝겊·나뭇잎 등을 구역에 맞게 바꾸려고)."""
    keep = []
    for o in parts:
        if any(o.name.startswith(p) for p in prefixes): bpy.data.objects.remove(o, do_unlink=True)
        else: keep.append(o)
    return keep

def jang(x, y, rot=0.0, tilt=0.0, scale=1.0, col=None, lying=False):
    """장승 한 기둥. lying=True면 눕는다. tilt=기울기(라디안, +X 쪽으로 눕는다)."""
    o = join("js", P.jangseung())
    if col:   # 얼굴색을 구역색으로 칠하는 대신 몸 전체 재질을 덮어쓴다(역병 장승은 먹빛)
        o.data.materials.clear(); o.data.materials.append(mat(col))
    if lying: return placed(o, (x, y, 0.28 * scale), (0, math.pi / 2 - 0.08, rot), scale)
    return placed(o, (x, y, 0), (0, tilt, rot), scale)

def table(x, y, items=("rice", "fruit"), lit=True):
    """제물상: 나무 작은 상 + 떡 쌓기/과일/촛불. lit=False면 촛불이 꺼져 있다."""
    p = [box("tbl_top", (1.0, 0.5, 0.06), (x, y, 0.5), "wood"), box("tbl_l", (0.06, 0.4, 0.5), (x - 0.42, y, 0.25), "wood_dark"), box("tbl_r", (0.06, 0.4, 0.5), (x + 0.42, y, 0.25), "wood_dark")]
    if "rice" in items: p += [cyl(f"ricecake{k}", 0.17 - k * 0.03, 0.15 - k * 0.03, 0.06, (x - 0.22, y, 0.53 + k * 0.06), "#F3E7D3", 8) for k in range(3)]
    if "fruit" in items: p += [sphere(f"fruit{k}", 0.07, (x + 0.1 + k * 0.13, y + (k % 2) * 0.06 - 0.03, 0.6), "#B5472F" if k != 1 else "#D8A83C", 5, 4) for k in range(3)]
    for k, dx in enumerate((-0.42, 0.42)):
        p.append(cyl(f"candle{k}", 0.025, 0.025, 0.14, (x + dx * 0.8, y + 0.14, 0.53), "hanji", 5))
        p.append(sphere(f"flame{k}", 0.03, (x + dx * 0.8, y + 0.14, 0.7), mat("#FFB066", 3.0) if lit else "#4A4440", 4, 3, (1, 1, 1.6)))
    return p

def rope_line(a, b, sag, n=8, r=0.03, z_end=None, col="thatch", broken_at=None):
    """a→b 사이 처진 새끼줄. broken_at(0~1)이면 거기서 끊겨 양쪽이 늘어진다."""
    pts = []
    for i in range(n + 1):
        t = i / n; x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t; z = a[2] + (b[2] - a[2]) * t - sag * math.sin(math.pi * t)
        if broken_at is not None:
            if t < broken_at: z = a[2] - (a[2] - 0.25) * (t / broken_at) ** 2 * 0.9
            elif t > broken_at + 0.12: z = b[2] - (b[2] - 0.3) * ((1 - t) / (1 - broken_at - 0.12)) ** 2 * 0.9 if False else b[2] - 0.9 * (1 - (1 - t) / (1 - broken_at - 0.12)) * 0 - sag * 0.2
        pts.append((x, y, z))
    out = []
    for i in range(n):
        if broken_at is not None and broken_at <= (i + 0.5) / n < broken_at + 0.12: continue
        A, B = Vector(pts[i]), Vector(pts[i + 1]); out.append(limb(f"rope{i}", A, B, r, r, col, 4))
    return out, pts

def paper_strips(pts, col="hanji", every=1, h=0.3, skip=()):
    return [box(f"paper{i}", (0.1, 0.02, h), (pts[i][0], pts[i][1], pts[i][2] - h / 2 - 0.02), col) for i in range(1, len(pts) - 1, every) if i not in skip]

def cloths(spec):
    """나무에 매단 헝겊: spec=[(색, 각도, 높이)]"""
    out = []
    for i, (c, a, z) in enumerate(spec):
        ox, oy = -1.0 + math.cos(a) * 0.5, 0.6 + math.sin(a) * 0.5
        out.append(box(f"cloth{i}", (0.16, 0.03, 1.0), (ox, oy, z), c, rot=(0, 0, a + 1.57)))
    return out

def sotdae_():
    return join("sot", P.sotdae())

def stones_stack(x, y, n, base_r, col_a="stone", col_b="stone_dark", moss=False):
    out = []; r = random.Random(7)
    for i in range(n):
        rr = base_r * (1 - i * 0.09); out.append(sphere(f"tower{i}", rr, (x + (r.random() - 0.5) * 0.08, y + (r.random() - 0.5) * 0.08, base_r * 0.5 + i * base_r * 0.62), "#5F7A52" if (moss and i % 2 == 0) else (col_a if i % 2 else col_b), 6, 4, (1, 1, 0.65)))
    return out

# ── 구역별 조립 ─────────────────────────────────────────────────────────────────────────────────
def v_solgogae():
    p = drop(P.seonangdang(), "cloth", "rope")
    p += cloths([("red", 0.0, 2.6), ("#3E64B0", 1.3, 2.4), ("#E8C15A", 2.6, 2.6), ("hanji", 3.9, 2.4), ("ink", 5.2, 2.6)])   # 오방색 다섯
    p.append(box("rope", (1.2, 0.05, 0.05), (-1.0, 0.6, 2.9), "thatch"))
    p += [jang(-1.5, -2.5, 0.0, 0.0, 1.0), jang(1.1, -2.5, 0.0, 0.0, 0.92)]            # 남·여 장승 한 쌍
    r, pts = rope_line((-1.5, -2.5, 1.7), (1.1, -2.5, 1.7), 0.25); p += r + paper_strips(pts)
    p += table(-0.2, -1.3, ("rice", "fruit"), True)
    p += [disc("yard", 2.3, 0.0, "#A08B62", 0.03, 18)]
    return p

def v_boritdeul():
    p = drop(P.seonangdang(), "cloth", "rope")
    p += cloths([("#E8C15A", 0.4, 2.6), ("#8FB04A", 2.4, 2.4), ("#E8C15A", 4.3, 2.55)])
    p.append(box("rope", (1.2, 0.05, 0.05), (-1.0, 0.6, 2.9), "thatch"))
    p.append(placed(sotdae_(), (2.9, -1.3, 0), (0, 0, 0), 0.95))                              # 솟대
    p.append(placed(join("js", P.jangseung()), (-1.9, -2.3, 0), (0, 0, 0), 1.0))               # 장승 하나
    for k, (x, y) in enumerate(((0.3, -2.0), (0.75, -1.7))):   # 짚단 둘(묶음 끈)
        p += [cyl(f"straw{k}", 0.32, 0.22, 0.85, (x, y, 0), "#C9B764", 8), cyl(f"strawtie{k}", 0.31, 0.31, 0.06, (x, y, 0.4), "wood_dark", 8)]
    p += [lathe("jar", [(0, 0.0), (0.06, 0.2), (0.22, 0.28), (0.3, 0.22), (0.34, 0.1)], 8, "jar", loc=(-0.6, -1.3, 0))]   # 이삭 단지
    for k in range(7): p.append(limb(f"ear{k}", (-0.6 + (k - 3) * 0.03, -1.3, 0.32), (-0.6 + (k - 3) * 0.1, -1.3 + (k % 2) * 0.05, 0.85 + (k % 3) * 0.06), 0.012, 0.03, "#D8B84A", 4))
    r, pts = rope_line((-1.9, -2.3, 1.5), (-0.9, -2.3, 1.5), 0.15, 4); p += r
    p += [disc("yard", 2.2, 0.0, "#9C8A5A", 0.03, 18)]
    return p

def v_mulmagi():
    p = drop(P.seonangdang(), "cloth", "rope")
    p += cloths([("#3E64B0", 0.2, 2.5), ("#7FB8D8", 2.1, 2.3), ("hanji", 4.1, 2.5), ("#3E64B0", 5.3, 2.35)])
    p.append(box("rope", (1.2, 0.05, 0.05), (-1.0, 0.6, 2.9), "thatch"))
    p += stones_stack(2.9, -0.4, 7, 0.34, "#6F7F72", "#55645A", moss=True)                         # 높은 이끼 돌탑
    p.append(placed(join("js", P.jangseung()), (-2.0, -2.2, 0), (0, 0.2, 0.15), 1.0))             # 기운 장승
    for k, (x, y) in enumerate(((-0.5, -1.8), (0.25, -2.0))):                                      # 물동이 둘
        p += [lathe(f"pot{k}", [(0, 0.0), (0.05, 0.22), (0.2, 0.36), (0.33, 0.52), (0.22, 0.7), (0.18, 0.78)], 8, "#5E6E6A", loc=(x, y, 0)), cyl(f"potwater{k}", 0.16, 0.16, 0.02, (x, y, 0.72), "water", 8)]
    p.append(sphere("salt", 0.5, (1.0, -1.7, 0.275), "#EDEDE6", 7, 4, (1, 0.8, 0.55)))                  # 소금 무더기
    p += [box("saltslab", (1.0, 0.8, 0.08), (1.0, -1.7, 0.04), "stone_dark")]
    p += [disc("wet", 2.5, 0.0, "#3E4A4A", 0.03, 18)]                                               # 젖은 마당
    return p

def v_geomeun():
    p = drop(P.seonangdang(), "cloth", "rope", "crown")
    for i, (x, y, z, r) in enumerate([(-1.0, 0.6, 4.7, 1.7), (-2.0, 0.5, 4.0, 1.1), (0.0, 0.9, 4.1, 1.2)]):   # 잎이 성글고 어둡다
        p.append(sphere(f"crown{i}", r, (x, y, z), "leaf_dark", 7, 5, (1, 1, 0.7)))
    p += cloths([("#9A9A94", 0.3, 2.5), ("#6A6A66", 2.2, 2.3), ("hanji", 4.2, 2.55)])
    p.append(box("rope", (1.2, 0.05, 0.05), (-1.0, 0.6, 2.9), "thatch"))
    p += [box("plankA", (1.1, 0.05, 0.14), (1.6, 1.12, 0.7), "wood_dark", rot=(0, 0.7, 0)), box("plankB", (1.1, 0.05, 0.14), (1.6, 1.12, 0.7), "wood_dark", rot=(0, -0.7, 0))]   # 당집 문에 엇댄 널(출입 금지)
    p += [jang(-1.6, -2.4, 0.0, 0.0, 1.0, col="#2A2A38"), jang(1.3, -2.4, 0.0, 0.07, 0.9, col="#2A2A38")]
    r, pts = rope_line((-1.6, -2.4, 1.7), (1.3, -2.4, 1.7), 0.25, 8, broken_at=0.45); p += r + paper_strips(pts, "#B8B2A0", 1, 0.3, skip=(3, 4))   # 가운데가 끊긴 금줄
    p += [disc("ash", 1.2, 0.0, "#8A8A86", 0.04, 14), disc("saltline", 1.9, 0.0, "#EDEDE6", 0.02, 18)]   # 재 원 + 소금 선(바깥 큰 원이 아래 깔림)
    p.append(cyl("candle", 0.03, 0.03, 0.18, (0.1, -1.0, 0.04), "#B8B2A0", 5)); p.append(sphere("candlecold", 0.03, (0.1, -1.0, 0.24), "#3A3A3C", 4, 3, (1, 1, 1.4)))
    return p

def v_pyedang():
    p = drop(P.seonangdang(), "cloth", "rope", "crown", "hut_roof")
    p += [limb("bare_a", (-1.0, 0.6, 3.2), (-1.6, 0.3, 5.0), 0.2, 0.05, "#4A3A30", 5), limb("bare_b", (-1.0, 0.6, 3.0), (0.1, 1.0, 4.6), 0.18, 0.04, "#4A3A30", 5), limb("bare_c", (-1.2, 0.6, 3.8), (-2.3, 1.2, 5.3), 0.1, 0.03, "#4A3A30", 4), limb("bare_d", (-0.9, 0.6, 3.9), (-0.3, -0.2, 5.4), 0.1, 0.03, "#4A3A30", 4)]   # 고사목 가지
    p.append(prism("hut_roof", 1.7, 1.4, 0.6, (1.5, 1.6, 0.9), "tile", rot=(0.0, 0.16, 0.0)))   # 내려앉은 지붕
    p.append(box("fallen_beam", (1.5, 0.12, 0.12), (0.8, 0.9, 0.35), "wood_dark", rot=(0, 0.3, 0.4)))
    p.append(jang(-1.2, -2.3, 0.35, lying=True, scale=1.0)); p.append(jang(1.4, -2.6, 0.0, 0.0, 0.8, col="#4A4034"))   # 쓰러진 것 + 낡아 선 것
    r, pts = rope_line((1.4, -2.6, 1.4), (0.2, -2.6, 0.2), 0.0, 5, col="#6B5E50"); p += r                         # 부러져 늘어진 금줄
    r2, _ = rope_line((-0.4, -1.2, 0.04), (-1.5, -1.8, 0.04), 0.0, 4, col="#6B5E50"); p += r2
    for k in range(5): p.append(box(f"shard{k}", (0.16, 0.12, 0.03), (0.4 + k * 0.17, -1.4 + (k % 2) * 0.22, 0.03), "#8B6A52", rot=(0.2, 0, k * 1.3)))   # 깨진 그릇
    p.append(cyl("incense", 0.02, 0.02, 0.12, (0.1, -1.0, 0.0), "#3A3A3C", 4))
    p.append(sphere("hon_fire", 0.1, (2.1, -1.0, 1.1), mat(FLAME, 3.0), 6, 4, (1, 1, 1.5))); p.append(sphere("hon_core", 0.05, (2.1, -1.0, 1.08), mat(FLAME_CORE, 4.0), 5, 3, (1, 1, 1.5)))
    p += [disc("yard", 2.3, 0.0, "#6B6252", 0.03, 18)]
    return p

VARIANTS = [("solgogae", "솔고개 마을", v_solgogae, [("Light_seonang_a", (0.0, -1.3, 1.0), "#FFB066", 0.7, 6.0, True)]),
            ("boritdeul", "보릿들", v_boritdeul, []), ("mulmagi", "물막이 골 어귀", v_mulmagi, []),
            ("geomeun", "검은여울 어귀", v_geomeun, []), ("pyedang", "폐당집 어귀", v_pyedang, [("Light_hon_fire", (2.1, -1.0, 1.1), FLAME, 0.6, 5.0, True)])]

# ── 넋길 입구 ───────────────────────────────────────────────────────────────────────────────────
def flame(name, x, y, z, lit, s=1.0):
    """물방울 모양 혼불(아래 둥글고 위가 뾰족). lit=False면 낮: 불 꺼진 잿빛 한지 등."""
    body = lathe(name, [(0, 0.0), (0.05, 0.07), (0.14, 0.1), (0.24, 0.07), (0.34, 0.0)], 7, mat(FLAME, 2.6) if lit else "#B8B2A0", scale=(s, s, s), loc=(x, y, z))
    core = lathe(name + "c", [(0.05, 0.0), (0.1, 0.04), (0.17, 0.045), (0.24, 0.0)], 6, mat(FLAME_CORE, 3.5) if lit else "#D8D2C0", scale=(s, s, s), loc=(x, y, z + 0.02))
    return [body, core]

def soulpath_gate(lit=True):
    """넋길 입구: 말뚝 둘 + 늘어진 새끼줄 + 매달린 혼불 다섯. 폭 3.6m, 높이 2.3m. 문이 아니라 '줄'이라 사이로 그냥 지나간다. 원점=길 한가운데 바닥."""
    p = [limb("postL", (-1.6, 0, 0), (-1.62, 0, 2.2), 0.1, 0.07, "wood_dark", 6), limb("postR", (1.6, 0, 0), (1.62, 0, 2.2), 0.1, 0.07, "wood_dark", 6),
         cyl("footL", 0.28, 0.2, 0.3, (-1.6, 0, 0), "stone_dark", 6), cyl("footR", 0.28, 0.2, 0.3, (1.6, 0, 0), "stone_dark", 6),
         box("knotL", (0.3, 0.08, 0.5), (-1.45, -0.1, 1.55), "#B8B2A0"), box("knotR", (0.3, 0.08, 0.5), (1.45, -0.1, 1.55), "#B8B2A0")]
    r, pts = rope_line((-1.6, 0, 2.05), (1.6, 0, 2.05), 0.35, 12, 0.035); p += r
    drops = [(2, 0.55), (4, 0.4), (6, 0.7), (8, 0.45), (10, 0.6)]   # (줄 마디, 매단 길이): 길이가 들쭉날쭉해야 줄에 달린 불로 읽힌다
    for i, L in drops:
        x, y, z = pts[i]; p.append(limb(f"str{i}", (x, y, z), (x, y, z - L), 0.012, 0.012, "thatch", 4)); p += flame(f"hon{i}", x, y, z - L - 0.45, lit, 1.5)
    p += [box(f"slab{k}", (0.9, 0.7, 0.07), (0.0, 1.0 + k * 1.0, 0.035), "stone_dark", rot=(0, 0, 0.1 * (k - 1))) for k in range(3)]   # 발판 돌(고리 아닌 일자)
    p.append(disc("bleed", 1.7, 0.0, "ink", 0.02, 16, 0.22, 0.0))                                              # 바닥에 번진 먹
    return p

def soulpath_lamp(lit=True):
    """길 따라 세우는 혼불 등: 납작 돌 + 낮은 말뚝 + 혼불 하나. 높이 1.1m."""
    p = [cyl("base", 0.28, 0.22, 0.1, (0, 0, 0), "stone_dark", 6), limb("stake", (0, 0, 0.08), (0.02, 0, 0.75), 0.05, 0.035, "wood_dark", 5), box("band", (0.16, 0.16, 0.05), (0.02, 0, 0.62), "#B8B2A0")]
    return p + flame("hon", 0.0, 0.0, 0.76, lit, 1.3)

def run():
    rep = []; os.makedirs(os.path.join(OUT, "props"), exist_ok=True)
    for key, nm, fn, lights in VARIANTS:
        reset(); o = join(f"prop_seonangdang_{key}", fn()); [light_empty(o, n, pos, c, i, r, f) for n, pos, c, i, r, f in lights]
        lo, hi = bounds(o); export(o, os.path.join(OUT, "props", f"prop_seonangdang_{key}.glb"))
        rep.append({"name": f"prop_seonangdang_{key}", "zone": nm, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "lights": [l[0] for l in lights]})
    for nm, fn, lights in (("prop_soulpath_gate", soulpath_gate, [("Light_hon_gate", (0, 0, 1.4), FLAME, 0.9, 7.0, True)]), ("prop_soulpath_lamp", soulpath_lamp, [("Light_hon_lamp", (0, 0, 0.9), FLAME, 0.5, 4.0, True)])):
        for lit in (True, False):
            reset(); name = nm + ("" if lit else "_off"); o = join(name, fn(lit))
            if lit: [light_empty(o, n, pos, c, i, r, f) for n, pos, c, i, r, f in lights]
            lo, hi = bounds(o); export(o, os.path.join(OUT, "props", name + ".glb"))
            rep.append({"name": name, "zone": "넋길", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "lit": lit})
    json.dump(rep, open(os.path.join(OUT, "props", "_report_seonang_set.json"), "w"), ensure_ascii=False, indent=1)
    # 미리보기: 낮 50°(윗줄 5곳) + 밤 50°(아랫줄 같은 5곳, 넋길 입구·혼불 등)
    for night, fname in ((False, "seonang_set_50deg.png"), (True, "seonang_set_night_50deg.png")):
        reset()
        for i, (key, nm, fn, lights) in enumerate(VARIANTS): o = join(f"v{i}", fn()); o.location = ((i - 2) * 6.2, 0, 0)
        g = join("gate", soulpath_gate(night)); g.location = (-9.3, -7.0, 0)
        for k in range(3): l = join(f"lamp{k}", soulpath_lamp(night)); l.location = (-5.0 + k * 1.8, -7.0, 0)
        setup_render(31, (0, -2.2, 1.0), size=(2000, 900), ground_size=60, night=night)
        bpy.context.scene.cycles.samples = 40; render(os.path.join(OUT, "previews", fname))
    return rep

if __name__ == "__main__":
    for r in run(): print(r["name"], r["tris"], r["size_m"], "min_z", r["min_z"])
