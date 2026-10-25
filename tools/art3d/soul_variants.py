"""혼 지역 변형: 기본 혼 4종(fresh/day/old/lump) × 지역 3곳(검은여울 역병·붉은재 번호 병사·쇳골 광부) = 12종.
왜 색+부착물만 바꾸나: 모양(실루엣)이 같아야 '같은 혼인데 사는 곳에 따라 달라졌다'가 한눈에 읽히고, 모델 수만 늘고 제작비는 안 는다.
규칙: 주황은 파혼 전용이라 쓰지 않는다. 혼은 발광(emission) 재질을 그대로 유지한다.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import souls
from fx import annulus
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def mix(a, b, t):
    """두 색(#RRGGBB)을 t 비율로 섞는다."""
    a, b = PAL.get(a, a).lstrip("#"), PAL.get(b, b).lstrip("#")
    return "#" + "".join(f"{round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t):02X}" for i in (0, 2, 4))

# 혼 종류별 기준점: (머리 중심 z, 머리 반지름, 정면 y, 가슴 z)
ANCHOR = {"fresh": (0.66, 0.24, -0.23, 0.55), "day": (1.15, 0.2, -0.19, 0.85), "old": (0.75, 0.36, -0.33, 0.55), "lump": (1.15, 0.34, -0.2, 0.7)}
BASE = {"fresh": "soul_fresh", "day": "soul_day", "old": "soul_old", "lump": "soul_lump"}

def tint(parts, base_key, color, t):
    """혼 몸통(발광 재질)의 색만 지역 색으로 섞는다. 눈 같은 어두운 재질은 그대로."""
    src = PAL[base_key]
    for o in parts:
        for i, m in enumerate(o.data.materials):
            if m and m.name.startswith("M_" + base_key):
                if m.get("alpha"):   # 반투명 겉껍질은 알파·발광을 그대로 두고 색만 섞는다
                    o.data.materials[i] = mat_alpha(mix(src, color, t), m["alpha"], m["emit"])
                else:
                    o.data.materials[i] = mat(mix(src, color, t), max(0.7, m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value))

def region_extra(region, kind):
    hz, hr, fy, cz = ANCHOR[kind]
    e = []
    if region == "yeoksa":      # 검은여울 역병: 몸에 돋은 푸른 멍울과 흘러내리는 물방울
        for i, (a, z) in enumerate([(0.6, 0.3), (2.4, 0.5), (4.1, 0.2), (5.3, 0.45)]):
            e.append(sphere(f"boil{i}", 0.09, (math.cos(a) * hr * 0.9, math.sin(a) * hr * 0.9 - 0.02, cz + z * 0.4), "slope_line", 5, 4))
        e.append(cyl("drip", 0.03, 0.0, 0.2, (hr * 0.5, fy + 0.05, cz - 0.1), "water", 5))
    elif region == "bungjae":   # 붉은재 번호 병사: 낡은 전립과 가슴의 번호표
        e += [cyl("cap", hr * 0.95, hr * 0.35, 0.18, (0, 0, hz + hr * 0.8), "iron", 8), cyl("brimcap", hr * 1.25, hr * 1.25, 0.03, (0, 0, hz + hr * 0.75), "iron", 8),
              box("tag", (0.2, 0.03, 0.24), (0, fy - 0.01, cz), "hanji"), box("tagbar", (0.12, 0.035, 0.05), (0, fy - 0.02, cz + 0.04), "ink"), box("tagbar2", (0.12, 0.035, 0.05), (0, fy - 0.02, cz - 0.05), "ink")]
    elif region == "soegol":    # 쇳골 광부: 등불 달린 광부 모자와 곡괭이
        e += [cyl("helmet", hr * 1.0, hr * 0.7, 0.2, (0, 0, hz + hr * 0.75), "stone_dark", 8), sphere("lamp", 0.07, (0, fy - 0.02, hz + hr * 0.85), mat("gold", 1.2), 5, 4),
              limb("pickaxe", (hr + 0.12, fy + 0.1, cz - 0.15), (hr + 0.25, fy + 0.1, cz + 0.55), 0.025, 0.025, "wood", 4), box("pickhead", (0.28, 0.04, 0.05), (hr + 0.25, fy + 0.1, cz + 0.55), "iron")]
    elif region in ("number", "number_named"):   # 쇳골 숫자 혼(인 없음): 명부에 번호로만 적힌 광부. 광부 혼(등불·곡괭이)과 달리 불 꺼진 투구 + 목 쇠고리 + 가슴 아래까지 늘어진 큰 번호 목패
        e += [cyl("helmet", hr * 1.0, hr * 0.7, 0.2, (0, 0, hz + hr * 0.75), "#4A4640", 8), box("lamp_dead", (0.07, 0.05, 0.06), (0, fy - 0.02, hz + hr * 0.85), "#2A2826")]
        collar = annulus("collar", hr * 0.62, hr * 0.92, 0.04, hz - hr * 0.95, "iron", 10); e.append(collar)
        tz = cz - 0.12   # 목패 중심 높이(가슴 아래로 늘어진다)
        e += [limb("cord_l", (-hr * 0.55, fy + 0.05, hz - hr * 0.9), (-0.1, fy - 0.02, tz + 0.22), 0.012, 0.012, "wood_dark", 3), limb("cord_r", (hr * 0.55, fy + 0.05, hz - hr * 0.9), (0.1, fy - 0.02, tz + 0.22), 0.012, 0.012, "wood_dark", 3),
              box("numtag", (0.3, 0.035, 0.42), (0, fy - 0.03, tz), "#8A7A5E"), box("numtag_hole", (0.05, 0.04, 0.05), (0, fy - 0.035, tz + 0.17), "#2A2826")]
        e += [box(f"tally{i}", (0.2, 0.04, 0.035), (0, fy - 0.045, tz + 0.08 - i * 0.09), "#2A2826") for i in range(3)]   # 번호를 새긴 홈(글자 없음: 번호는 홈 줄로만 읽힌다)
        if region == "number_named":   # B-08 천도 뒤: 번호 옆에 이름이 떠 있다 → 목패 옆에 발광 이름 쪽지가 붙는다(글자 없음)
            e += [box("name_slip", (0.15, 0.015, 0.24), (0.21, fy - 0.05, tz - 0.02), mat("#F3E7D3", 1.4), rot=(0, 0, 0.12)), limb("slip_thread", (0.15, fy - 0.04, tz + 0.12), (0.2, fy - 0.05, tz + 0.1), 0.006, 0.006, "#F3E7D3", 3)]
    return e

REGIONS = {"yeoksa": ("검은여울 역병", "#5E8F63", 0.75), "bungjae": ("붉은재 번호 병사", "#7C86A6", 0.7), "soegol": ("쇳골 광부", "#8C8478", 0.7), "number": ("쇳골 숫자 혼", "#7A7C84", 0.5), "number_named": ("쇳골 숫자 혼(이름 되찾음)", "#7A7C84", 0.5)}

def variant(kind, region, o=0):
    parts = souls()[kind](o)
    tint(parts, BASE[kind], REGIONS[region][1], REGIONS[region][2])
    ex = region_extra(region, kind)
    for p in ex: p.location.x += o   # 부착물도 같은 자리로 옮긴다
    return parts + ex

if __name__ == "__main__":
    rep = []
    for region in REGIONS:
        for kind in BASE:
            reset(); o = join(f"soul_{kind}_{region}", variant(kind, region)); lo, hi = bounds(o)
            rep.append({"name": o.name, "region": REGIONS[region][0], "tris": tris(o), "min_z": round(lo.z, 3), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)]})
            export(o, os.path.join(OUT, "souls", f"soul_{kind}_{region}.glb"))
    # 미리보기: 행=지역(기본 포함 4행), 열=혼 4종
    reset()
    for r, region in enumerate((None, "soegol", "number", "number_named")):
        for c, kind in enumerate(BASE):
            parts = souls()[kind](c * 1.6) if region is None else variant(kind, region, c * 1.6)
            for p in parts: p.location.y += 0  # 기준 유지
            j = join(f"s{r}{c}", parts); j.location.y = -r * 2.0
    setup_render(8.5, (2.4, -3.0, 0.5), size=(1100, 800), ground_size=20)
    render(os.path.join(OUT, "previews", "souls_regions_50deg.png"))
    json.dump(rep, open(os.path.join(OUT, "souls", "_report_variants.json"), "w"), ensure_ascii=False, indent=1)
    print(len(rep), "종", "최대 삼각형", max(r["tris"] for r in rep), "최소 z", min(r["min_z"] for r in rep))
