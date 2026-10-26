"""시즌 1 보스 파혼 결말 보강(서사 docs/narrative/S1-BOSS-ENDINGS-CHECK.md 3절): 클로즈업 물건 5 + 파혼 뒤 낮 풍경 자국 4.
원칙(서사): 파혼 컷의 마지막 0.3~0.5초는 '그 사람의 물건'. 단서를 모았던 사람이 무엇을 깨뜨렸는지 바로 알아야 하니 낮 단서 물건과 같은 것을 가까이서 보여 준다.
 낮 풍경 자국은 파혼 기록이 있을 때만 그 자리에 세우는 물건(만질 수 없음, 새 대사·수치 변화 없음).
클로즈업 5(카메라 1~1.5 m 거리로 찍는 물건이라 면 수를 넉넉히): prop_closeup_flagpole(B-05) · prop_closeup_mokpae(B-07) · prop_closeup_ledger_back(B-08) · prop_closeup_rope7(B-10) · prop_closeup_blank_tag(B-11)
낮 풍경 4: prop_trace_banner_up(B-05, 내리지 않고 펄럭이는 군기) · prop_trace_armor_empty(B-06, 선 채로 남은 빈 갑주) · prop_trace_mokpae_gap(B-07, 목패 하나가 빈 걸이 판) · prop_trace_anchor_rope(B-10, 썰물에 드러난 밧줄 감긴 닻)
규약: 1단위=1m, 원점=바닥(물건이 놓이는 면) 한가운데, 정면(카메라)=-Y, 재질 색만, 발광 없음. 주황 안 씀. 글자는 새김/먹 막대로 만들어 숫자·한자를 글로 쓰지 않는다(七은 막대 둘로 읽히는 새김).
실행: python3 bossend_props.py [이름 ...] → assets3d/props/ + unity Resources/Models/Props/ + _report_bossend.json"""
import sys, os, math, json, random, shutil
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); UNITY = os.path.join(OUT, "..", "unity", "Assets", "Resources", "Models", "Props")
WOOD = "#8A6A44"; WOOD_D = "#5A4330"; WOOD_L = "#C8A878"; INKC = "#1E1814"; CREAM = "#E8DCC0"; CHAR = "#241A14"; FLAG = "#8A2A2A"; IRON = "#4A4A52"; IRON_L = "#7A7A84"; ROPE = "#B4A66A"; ROPE_D = "#8A7A48"

# ── 클로즈업 5 ──────────────────────────────────────────────────────────────
def closeup_flagpole():
    """깃대 조각(B-05): 부러진 깃대 0.8 m 토막이 비스듬히 누웠다. 앞면에 칼로 판 이름 줄 열 — 위 여섯은 깊고 또렷(먹 채움), 아래 넷은 닳아 흐릿. 한쪽 끝은 쪼개져 뾰족, 다른 끝에 낡은 붉은 천 조각이 묶임."""
    r = random.Random(105); p = []; tilt = (0.0, math.radians(86), math.radians(-14))
    p.append(cyl("pole", 0.055, 0.048, 0.8, (-0.4, 0, 0.06), WOOD, 10, rot=(0, math.radians(90), math.radians(-12))))
    for k in range(5): p.append(cyl(f"splin{k}", 0.012, 0.0, 0.16 + 0.04 * k, (-0.42 - 0.002 * k, 0.012 * (k - 2), 0.06 + 0.005 * k), WOOD_L, 4, rot=(0, math.radians(-90), math.radians(-12 + 9 * (k - 2)))))
    for i in range(10):   # 새김: 깃대 앞(-Y)면을 따라 열 줄. 줄마다 짧은 칼금 셋
        t = -0.30 + i * 0.075; deep = i < 6
        for j in range(3):
            p.append(box(f"cut{i}_{j}", (0.026 if deep else 0.018, 0.006, 0.006 if deep else 0.004), (t + r.uniform(-0.006, 0.006), -0.052, 0.06 + (j - 1) * 0.016 + t * 0.12), INKC if deep else WOOD_D, rot=(0, 0, r.uniform(-0.5, 0.5))))
    p.append(box("rag", (0.2, 0.012, 0.07), (0.30, -0.055, 0.075), FLAG, rot=(0, 0, math.radians(-12)))); p.append(box("rag2", (0.1, 0.012, 0.05), (0.40, -0.05, 0.03), FLAG, rot=(0.4, 0, -0.5)))
    p.append(cyl("knot", 0.06, 0.06, 0.02, (0.26, -0.01, 0.075), ROPE, 8, rot=(0, math.radians(90), math.radians(-12))))
    return p

def closeup_mokpae():
    """닳은 목패(B-07): 칠성의 七 목패. 0.2×0.3 m 널조각, 구멍에 짚끈. 늘 만지던 테두리만 반들반들 닳아 밝고(밝은 테두리 띠), 가운데에 七(막대 둘: 가로 하나 + 꺾인 세로)이 깊게 새겨졌다."""
    p = [box("tag_back", (0.22, 0.03, 0.32), (0, 0, 0.17), WOOD_D), box("tag", (0.2, 0.03, 0.3), (0, -0.004, 0.17), WOOD)]
    for sx in (-1, 1): p.append(box(f"worn_side{sx}", (0.022, 0.032, 0.3), (sx * 0.1, -0.005, 0.17), WOOD_L))                                       # 닳아 밝은 옆 테두리
    p += [box("worn_top", (0.2, 0.032, 0.022), (0, -0.005, 0.31), WOOD_L), box("worn_bot", (0.2, 0.032, 0.022), (0, -0.005, 0.03), WOOD_L)]
    p += [box("seven_h", (0.12, 0.012, 0.025), (0, -0.02, 0.19), INKC), box("seven_v", (0.025, 0.012, 0.17), (-0.005, -0.02, 0.165), INKC), box("seven_hook", (0.06, 0.012, 0.024), (0.022, -0.02, 0.085), INKC, rot=(0, 0, 0.45))]   # 七
    p += [cyl("hole", 0.022, 0.022, 0.04, (0, 0.0, 0.29), INKC, 8, rot=(math.radians(90), 0, 0))]
    p += chain_pts("cord", [(-0.04, -0.02, 0.31), (-0.07, -0.02, 0.38), (0, -0.02, 0.44), (0.07, -0.02, 0.38), (0.04, -0.02, 0.31)], 0.012, 0.012, ROPE, 5)
    p += [box("wood_grain", (0.012, 0.004, 0.22), (-0.05, -0.02, 0.17), WOOD_D), box("wood_grain2", (0.01, 0.004, 0.18), (0.06, -0.02, 0.15), WOOD_D)]
    return p

def closeup_ledger_back():
    """타다 남은 장부 뒷장 귀퉁이(B-08): 종이 한 귀퉁이 0.34×0.28 m. 불에 먹힌 쪽 가장자리는 까맣게 숯이 되고 안으로 갈색 번짐, 남은 종이에 이름 줄 열넷(작은 먹 막대, 몇 줄은 잘려 끝만 보임). 숫자 앞장이 아니라 사람 이름이 적힌 뒷장이라는 게 읽히게 줄이 가지런하다."""
    r = random.Random(108); p = []
    p.append(box("paper", (0.34, 0.28, 0.008), (0, 0, 0.004), CREAM))
    # 타서 먹힌 가장자리: 오른쪽 위로 갈수록 크게 깎인 불규칙 숯 띠(회전한 상자 여러 개)
    for i in range(11):
        t = i / 10; x = 0.17 - 0.03 * (1 - t); y = -0.14 + t * 0.28 + 0.0
        wd = 0.05 + 0.07 * math.sin(t * math.pi) + r.uniform(0, 0.03)
        p.append(box(f"char{i}", (wd, 0.045, 0.012), (x - wd / 2 + 0.01, y, 0.008), CHAR, rot=(0, 0, r.uniform(-0.5, 0.5)))); p.append(box(f"brown{i}", (wd + 0.04, 0.05, 0.010), (x - wd / 2 - 0.02, y, 0.006), "#6A4A30", rot=(0, 0, r.uniform(-0.4, 0.4))))
    p.append(box("hole", (0.05, 0.04, 0.012), (-0.01, 0.06, 0.009), CHAR, rot=(0, 0, 0.6)))
    for i in range(14):    # 이름 줄 열넷(세로 두 칸에 일곱씩)
        col, row = divmod(i, 7); x0 = -0.15 + col * 0.11; y = 0.11 - row * 0.034; L = 0.085 - (0.02 if col == 1 and row < 3 else 0)
        for k in range(int(L / 0.014)): p.append(box(f"n{i}_{k}", (0.008, 0.016, 0.005), (x0 + k * 0.012, y + r.uniform(-0.002, 0.002), 0.011), INKC))
    p.append(box("fold_shadow", (0.34, 0.01, 0.003), (0, -0.08, 0.0085), "#CDBE9A"))
    return p

def closeup_rope7():
    """매듭 일곱 달린 밧줄(B-10): 선장이 일곱 이름을 하나씩 묶어 센 밧줄. 1.3 m가 완만한 S자로 누워 있고 같은 간격으로 굵은 매듭 일곱, 한끝은 풀려 올이 갈라짐, 다른 끝은 닻줄 고리."""
    pts = [(-0.62 + 0.103 * i, 0.12 * math.sin(i * 0.55), 0.03) for i in range(13)]
    p = chain_pts("rope", pts, 0.026, 0.026, ROPE, 6)
    for k in range(7):
        i = 1 + k * 1.5; x = -0.62 + 0.103 * i; y = 0.12 * math.sin(i * 0.55)
        p += [sphere(f"knot{k}", 0.05, (x, y, 0.045), ROPE_D, 8, 6, (1.15, 0.9, 0.9)), sphere(f"knotb{k}", 0.034, (x + 0.02, y - 0.02, 0.07), ROPE, 6, 4)]
    for j in range(5): p.append(limb(f"fray{j}", (0.62, 0.12 * math.sin(12 * 0.55), 0.03), (0.74 + 0.02 * j, 0.12 * math.sin(12 * 0.55) + (j - 2) * 0.03, 0.02), 0.011, 0.003, ROPE, 4))
    p.append(cyl("eye", 0.07, 0.07, 0.03, (-0.7, 0.0, 0.02), ROPE_D, 10)); p.append(cyl("eye_hole", 0.035, 0.035, 0.034, (-0.7, 0.0, 0.022), INKC, 8))
    return p

def closeup_blank_tag():
    """아무것도 새기지 않은 나무 조각(B-11): 왕초가 가르친 아이들 별명 조각과 같은 모양인데 비어 있다. 0.18×0.26 m, 결만 있고 새김 없음. 옆에 쓰지 못한 칼 하나와 깎인 부스러기 한 줌(새기려다 만 흔적)."""
    r = random.Random(111)
    p = [box("tag", (0.18, 0.025, 0.26), (0, 0, 0.14), WOOD_L), box("edge", (0.19, 0.022, 0.27), (0, 0.004, 0.14), WOOD)]
    p += [box(f"grain{i}", (0.004, 0.002, r.uniform(0.12, 0.2)), (-0.07 + i * 0.035, -0.014, 0.14), "#B99A68") for i in range(5)]
    p += [cyl("hole", 0.02, 0.02, 0.03, (0, 0, 0.25), INKC, 8, rot=(math.radians(90), 0, 0))] + chain_pts("cord", [(-0.03, -0.015, 0.26), (-0.05, -0.015, 0.32), (0, -0.015, 0.36), (0.05, -0.015, 0.32), (0.03, -0.015, 0.26)], 0.01, 0.01, ROPE, 5)
    p += [box("knife_blade", (0.09, 0.012, 0.018), (0.19, 0.03, 0.01), IRON_L, rot=(0, 0, 0.35)), box("knife_handle", (0.08, 0.02, 0.022), (0.26, 0.05, 0.012), WOOD_D, rot=(0, 0, 0.35))]
    p += [box(f"curl{i}", (r.uniform(0.02, 0.04), 0.008, 0.004), (-0.19 + r.uniform(-0.04, 0.04), 0.0 + r.uniform(-0.04, 0.05), 0.004 + 0.002 * i), "#D8BE90", rot=(0, 0, r.uniform(0, 3))) for i in range(7)]
    return p

# ── 낮 풍경 자국 4 ──────────────────────────────────────────────────────────
def trace_banner_up():
    """내리지 않고 펄럭이는 군기(B-05, 성벽 위): 곧은 깃대 3.6 m가 돌무더기에 꽂혀 있고 큰 붉은 깃발 1.5×1.0 m가 바람에 한쪽으로 휘어 펄럭인다. 가장자리가 해져 삐죽(찢긴 군기 sanseong_banner_torn의 '내리지 못한' 짝)."""
    r = random.Random(131); p = [cyl("cairn", 0.55, 0.38, 0.4, (0, 0, 0), "#585650", 7), cyl("pole", 0.055, 0.045, 3.6, (0, 0, 0.3), WOOD_D, 7), sphere("finial", 0.07, (0, 0, 3.92), IRON, 6, 4)]
    for i in range(8):   # 깃발: 가로 판 8장이 바람 쪽(+X)으로 갈수록 처지고 휘어 물결
        x = 0.1 + i * 0.18; z = 3.5 - 0.07 * i - 0.05 * math.sin(i * 1.2)
        p.append(box(f"flag{i}", (0.2, 0.025, 0.95 - 0.07 * (i % 3)), (x, 0.05 * math.sin(i * 1.0), z - 0.45), FLAG, rot=(0, 0, 0.04 * math.sin(i * 1.5))))
    p += [box(f"frayL{i}", (0.05, 0.02, r.uniform(0.15, 0.35)), (0.25 + i * 0.25, 0.04, 2.9 - r.uniform(0, 0.1)), FLAG) for i in range(5)] + [box("tie1", (0.1, 0.05, 0.06), (0.04, 0, 3.55), "#C8A878"), box("tie2", (0.1, 0.05, 0.06), (0.04, 0, 3.0), "#C8A878")]
    return p

def trace_armor_empty():
    """선 채로 남은 빈 갑주(B-06, 군막 터): 사람 키(1.75 m) 갑주 한 벌이 나무 틀 위에 반듯이 서 있다. 투구 속·소매 속은 어둡게 비었다. 만질 수 없음. 번호를 부르던 장수의 것이라 가슴에 칠하지 않은 빈 번호 판이 붙었다."""
    r = random.Random(132); STEEL = "#6A6E78"; LACE = "#7A3A2A"
    p = [cyl("stand_pole", 0.04, 0.04, 1.75, (0, 0.12, 0.0), WOOD_D, 6), box("stand_foot", (0.7, 0.4, 0.06), (0, 0.12, 0.03), WOOD_D), box("stand_arm", (1.15, 0.05, 0.05), (0, 0.1, 1.38), WOOD_D)]
    p += [cyl("helmet", 0.2, 0.12, 0.26, (0, 0, 1.5), STEEL, 10), sphere("helmet_top", 0.14, (0, 0, 1.76), STEEL, 8, 5, (1, 1, 0.7)), cyl("helmet_brim", 0.26, 0.2, 0.04, (0, 0, 1.48), IRON, 10), cyl("plume", 0.025, 0.03, 0.3, (0, 0.0, 1.9), FLAG, 5)]
    p += [box("face_dark", (0.18, 0.02, 0.14), (0, -0.1, 1.5), INKC)]
    p += [box("chest", (0.5, 0.26, 0.55), (0, 0, 1.1), STEEL), box("chest_plate", (0.4, 0.04, 0.42), (0, -0.14, 1.12), "#8A8E98"), box("num_plate", (0.14, 0.012, 0.2), (0, -0.165, 1.12), CREAM)]
    for i in range(6): p.append(box(f"lace{i}", (0.5, 0.03, 0.012), (0, -0.14, 0.9 + i * 0.07), LACE))
    for sx in (-1, 1):
        p += [box(f"shoulder{sx}", (0.22, 0.28, 0.1), (sx * 0.36, 0, 1.38), STEEL), limb(f"sleeve{sx}", (sx * 0.36, 0, 1.36), (sx * 0.62, 0.0, 1.02), 0.09, 0.07, "#3A3A48", 6), box(f"gauntlet{sx}", (0.12, 0.12, 0.16), (sx * 0.64, 0, 0.95), IRON)]
    for k in range(5): p.append(box(f"skirt{k}", (0.12, 0.05, 0.4), (-0.24 + k * 0.12, -0.1, 0.64), STEEL if k % 2 else "#7A7E88", rot=(0.12, 0, 0)))
    p += [box("under_robe", (0.46, 0.2, 0.55), (0, 0, 0.4), "#3A3A48"), box("shin_l", (0.12, 0.12, 0.3), (-0.12, 0, 0.17), IRON), box("shin_r", (0.12, 0.12, 0.3), (0.12, 0, 0.17), IRON)]
    return p

def trace_mokpae_gap():
    """목패 하나가 빈 목패 걸이 판(B-07, 광부촌): 기존 soegol_mokpae_board에서 七 목패(태그 6)와 그 새김만 빼 걸이 고리만 남긴다."""
    import act2_kit as K
    p = [o for o in K.soegol_mokpae_board() if o.name not in ("tag6", "mark6")]
    return p

def trace_anchor_rope():
    """썰물에 드러난 밧줄 감긴 닻(B-10, 난파 여울): 개펄에 반쯤 박힌 닻. 몸대 1.5 m가 비스듬히 서고 갈고리 날개가 개펄 속, 위 가로막대가 드러났다. 밧줄이 몸대를 세 바퀴 감고 개펄 위로 길게 늘어져 해초가 엉켰다."""
    r = random.Random(140); MUD = "#4A4234"; p = [cyl("mud", 0.9, 0.7, 0.14, (0, 0, -0.02), MUD, 10)]
    tilt = math.radians(14)
    p.append(cyl("shank", 0.06, 0.05, 1.5, (0, 0, 0.0), IRON, 7, rot=(tilt, 0, 0))); p.append(box("stock", (0.9, 0.07, 0.07), (0, -0.28, 1.45), WOOD_D, rot=(tilt, 0, 0)))
    for sx in (-1, 1): p += [limb(f"fluke{sx}", (0, 0.1, 0.12), (sx * 0.55, 0.12, 0.34), 0.06, 0.03, IRON, 6), cyl(f"palm{sx}", 0.09, 0.0, 0.2, (sx * 0.56, 0.12, 0.32), IRON, 4)]
    p.append(sphere("ring", 0.1, (0, -0.32, 1.52), IRON, 8, 4, (1, 0.3, 1)))
    for k in range(3): p += chain_pts(f"wrap{k}", [(-0.07, -0.1 - 0.01 * k, 0.45 + 0.2 * k), (0, -0.14, 0.5 + 0.2 * k), (0.07, -0.1, 0.55 + 0.2 * k), (0, -0.04, 0.6 + 0.2 * k)], 0.028, 0.028, ROPE_D, 5)
    pts = [(0.05, -0.1, 0.4), (0.3, -0.5, 0.1), (0.8, -0.8, 0.05), (1.5, -0.9, 0.04), (2.3, -1.3, 0.04), (3.0, -1.2, 0.03)]
    p += chain_pts("trail", pts, 0.03, 0.026, ROPE_D, 5)
    p += [box(f"weed{i}", (r.uniform(0.15, 0.3), 0.02, 0.02), (0.6 + i * 0.5, -0.85 - 0.1 * i, 0.07), "#3F5F3A", rot=(0, 0, r.uniform(0, 3))) for i in range(5)]
    return p

KIT = [("closeup_flagpole", closeup_flagpole, "깃대 조각 클로즈업(B-05)"), ("closeup_mokpae", closeup_mokpae, "닳은 목패 클로즈업(B-07)"), ("closeup_ledger_back", closeup_ledger_back, "타다 남은 장부 뒷장(B-08)"),
       ("closeup_rope7", closeup_rope7, "매듭 일곱 밧줄(B-10)"), ("closeup_blank_tag", closeup_blank_tag, "새기지 않은 나무 조각(B-11)"),
       ("trace_banner_up", trace_banner_up, "펄럭이는 군기(B-05 낮)"), ("trace_armor_empty", trace_armor_empty, "빈 갑주(B-06 낮)"), ("trace_mokpae_gap", trace_mokpae_gap, "목패 빈 걸이 판(B-07 낮)"), ("trace_anchor_rope", trace_anchor_rope, "밧줄 감긴 닻(B-10 낮)")]

def build(key, fn):
    reset(); parts = fn(); o = join(f"prop_{key}", parts); lo, hi = bounds(o); path = os.path.join(OUT, "props", f"prop_{key}.glb"); export(o, path)
    os.makedirs(UNITY, exist_ok=True); shutil.copy(path, os.path.join(UNITY, os.path.basename(path)))
    return {"name": f"prop_{key}", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}

if __name__ == "__main__":
    want = sys.argv[1:]; res = [build(k, f) for k, f, n in KIT if not want or k in want]
    for r in res: print(r)
    if not want: json.dump(res, open(os.path.join(OUT, "props", "_report_bossend.json"), "w"), ensure_ascii=False, indent=1)
