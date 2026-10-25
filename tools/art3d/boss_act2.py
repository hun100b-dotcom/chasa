"""2막 보스 본체 밑작업: B-05 기수 대돌, B-06 이름 없는 장수, B-07 갱도 반장 칠성, B-08 장부꾼 염씨. 실행: python3 boss_act2.py [--sheets]
근거: docs/narrative/boss_clues_act2.json (서사 2026-10-25: 보스의 한·믿음·단서 물건), planning/openworld/act2/act2_map.json (싸움터 자리).
모양은 단서에서 가져왔다: 대돌=깃대·찢긴 군기·이름 띠(잊혀 가는 이름), 장수=얼굴 없는 흰 천·번호패 치마(이름을 지우고 번호로 부름), 칠성=등불 모자·목패 열넷·곡괭이(세어도 하나가 모자람), 염씨=두꺼운 장부·붓·떠도는 뒷장(뒷장에 몰래 적은 이름).
뼈 규칙: 6원형(Root/Hips/Chest/Head/UpperArm.L·R/Prop)에 Hand.L·R을 더한 9개(월화·서 의원과 같다). 팔은 아래로 늘어진 자세가 기준이라 rx가 음수면 앞/위로 든다(Hips/Chest rx 양수=앞으로 숙임).
동작(60fps): Idle 120f 반복 / Windup 40f(번쩍 30, 끝=판정 직전 자세) / Attack 24f(명중 f6) / Hit1 10f / Hit2 18f / Stagger 36f / Kneel 45f / KneelHold 120f 반복 / Tendo 150f(흩어짐 dissolve=140) / Pahon 90f. 이름·길이는 1막 보스와 같은 틀이라 코드 연결이 같다.
숫자(서른일곱·일곱·열셋·열넷)는 모델의 사물 수로만 쓴다(글자 없음). 이름·분위기는 서사 확인 전."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import to_group, rig
import anim
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
KEYS = ("Root", "Hips", "Chest", "Head", "UpperArm.L", "UpperArm.R", "Hand.L", "Hand.R", "Prop")
IRON_B, IRON_L, CLOTH_B, FLAG, BONE = "#4A4E5C", "#6A6E7C", "#3B4468", "#8A2A2A", "#E8DDA8"
def P(): return {k: [] for k in KEYS}

def bones_for(spec):
    """spec: h(키), hip(골반 높이), sh(어깨 높이), neck(목 높이), sw(어깨 반폭), hand(손목 높이), hx(손 x 위치), hy(손 y 위치, 앞이 음수), prop(소품 뼈 높이)"""
    h, hip, sh, nk, sw, hz, hx, hy = (spec[k] for k in ("h", "hip", "sh", "neck", "sw", "hand", "hx", "hy"))
    return [("Root", None, (0, 0, 0), (0, 0, 0.3)), ("Hips", "Root", (0, 0, hip), (0, 0, hip + 0.15)), ("Chest", "Hips", (0, 0, hip + 0.15), (0, 0, sh)), ("Head", "Chest", (0, 0, nk), (0, 0, h)),
            ("UpperArm.L", "Chest", (sw, 0, sh), (hx, hy, hz)), ("Hand.L", "UpperArm.L", (hx, hy, hz), (hx, hy - 0.1, hz - 0.1)),
            ("UpperArm.R", "Chest", (-sw, 0, sh), (-hx, hy, hz)), ("Hand.R", "UpperArm.R", (-hx, hy, hz), (-hx, hy - 0.1, hz - 0.1)), ("Prop", "Root", (0, 0, spec["prop"]), (0, 0, spec["prop"] + 0.2))]

def arm_pair(p, spec, sleeve, cuff=None, r0=0.11, r1=0.09, hand_m="skin"):
    """양팔: 어깨→손목 늘어진 팔과 손. 손은 Hand 뼈에 묶는다."""
    for sx, n, hn in ((1, "UpperArm.L", "Hand.L"), (-1, "UpperArm.R", "Hand.R")):
        sh = (sx * spec["sw"], 0, spec["sh"]); hd = (sx * spec["hx"], spec["hy"], spec["hand"])
        p[n].append(limb("arm" + n[-1], sh, hd, r0, r1, sleeve, 6))
        if cuff: p[n].append(sphere("cuff" + n[-1], r1 * 1.15, tuple(hd), cuff, 6, 4, (1, 1, 0.8)))
        p[hn].append(sphere("hand" + n[-1], r1 * 0.95, (hd[0], hd[1], hd[2] - 0.05), hand_m, 6, 4))

# ───────────────────────── B-05 기수 대돌 ─────────────────────────
SPEC5 = dict(h=2.5, hip=1.0, sh=1.75, neck=1.95, sw=0.5, hand=1.2, hx=0.6, hy=-0.35, prop=1.4)
def b05():
    """기수 대돌 2.5m: 쇠 갑옷의 거구. 오른손에 꼭대기가 부러진 깃대와 찢긴 붉은 군기, 깃대엔 칼금(이름 새긴 자국). 어깨에서 흰 '이름 띠'가 늘어지고, 등 뒤에 흐릿한 병졸 여섯이 따라온다(잊혀 가는 이름들)."""
    r = random.Random(51); p = P(); s = SPEC5
    p["Hips"] += [lathe("skirt", [(0.35, 0.5), (0.6, 0.46), (0.85, 0.4), (1.0, 0.36)], 9, CLOTH_B, fn=lambda i, k, th, z, rr: (rr * (1 + 0.05 * (1 if k % 2 else -1)), z + (0.04 * (k % 3) if i == 0 else 0))), cyl("lames", 0.46, 0.4, 0.3, (0, 0, 0.7), IRON_B, 9)]
    p["Hips"] += [cyl("legL", 0.17, 0.14, 0.4, (0.2, 0, 0.02), "hat", 6), cyl("legR", 0.17, 0.14, 0.4, (-0.2, 0, 0.02), "hat", 6), box("bootL", (0.22, 0.34, 0.14), (0.2, -0.06, 0.07), "hat"), box("bootR", (0.22, 0.34, 0.14), (-0.2, -0.06, 0.07), "hat")]
    p["Chest"] += [lathe("torso", [(1.0, 0.36), (1.25, 0.44), (1.5, 0.5), (1.72, 0.44), (1.8, 0.2)], 9, IRON_B, scale=(1.1, 0.85, 1.0)), box("belt", (0.9, 0.6, 0.12), (0, 0, 1.02), "gold"), box("sash1", (0.12, 0.66, 1.0), (0.18, 0, 1.45), FLAG, rot=(0, 0, 0)), box("plate", (0.5, 0.1, 0.55), (0, -0.4, 1.5), IRON_L)]
    for sx in (1, -1): p["Chest"].append(sphere(f"pad{sx}", 0.27, (sx * 0.58, 0, 1.72), IRON_L, 7, 5, (1, 1, 0.8)))
    for i in range(14):   # 이름 띠: 어깨 끈에서 늘어진 흰 천 조각 열넷(보스의 서른일곱 중 눈에 띄는 일부)
        x = -0.55 + i * 0.085; ln = r.uniform(0.35, 0.7)
        p["Chest"] += [box(f"strip{i}", (0.06, 0.012, ln), (x, -0.43, 1.62 - ln / 2), BONE, rot=(0.1, 0, r.uniform(-.1, .1))), box(f"ink{i}", (0.03, 0.014, 0.05), (x, -0.44, 1.5 - r.uniform(0, ln * 0.6)), "ink")]
    p["Head"] += [sphere("head", 0.19, (0, 0, 2.08), "skin", 7, 5), cyl("helm", 0.24, 0.1, 0.3, (0, 0, 2.1), IRON_B, 8), cyl("brim", 0.3, 0.3, 0.04, (0, 0, 2.1), IRON_L, 10), box("plume", (0.06, 0.06, 0.35), (0, 0.08, 2.4), FLAG, rot=(0.3, 0, 0)), box("strap", (0.04, 0.02, 0.2), (0.12, -0.16, 1.95), "hat"),
                  box("eyeL", (0.05, 0.02, 0.04), (0.08, -0.17, 2.1), mat("#E8DDA8", 1.2)), box("eyeR", (0.05, 0.02, 0.04), (-0.08, -0.17, 2.1), mat("#E8DDA8", 1.2)), box("brow", (0.26, 0.02, 0.04), (0, -0.175, 2.15), "hat")]
    arm_pair(p, s, IRON_B, IRON_L, 0.13, 0.11)
    # 오른손의 깃대: 손목 위치(-0.6,-0.35)에 수직. 꼭대기가 부러졌고 칼금이 새겨짐
    hx, hy = -s["hx"], s["hy"]
    p["Hand.R"] += [cyl("pole", 0.06, 0.05, 3.2, (hx, hy, 0.0), "wood_dark", 6), cyl("snap", 0.05, 0.02, 0.3, (hx + 0.08, hy, 3.2), "wood", 5, rot=(0, 0.5, 0)), box("banner_top", (0.9, 0.04, 0.5), (hx + 0.5, hy, 2.9), FLAG, rot=(0, 0, 0.04))]
    p["Hand.R"] += [box(f"rag{i}", (0.16, 0.03, r.uniform(0.6, 1.2)), (hx + 0.12 + i * 0.17, hy + 0.01, 2.65 - 0.4 - 0.1 * i), FLAG, rot=(0, r.uniform(-.1, .1), r.uniform(-.08, .08))) for i in range(5)]
    p["Hand.R"] += [box(f"notch{i}", (0.09, 0.025, 0.015), (hx, hy - 0.06, 1.5 + i * 0.09), "ink", rot=(0, 0, r.uniform(-.4, .4))) for i in range(12)]
    # 따라오는 흐린 병졸 여섯: 반투명 하늘빛(잊혀 가는 이름) — Prop 뼈에 묶어 천천히 흔들 수 있다
    gm = mat_alpha("#BFE8FF", 0.28, 0.8)
    for i, (x, y) in enumerate([(-1.0, 1.0), (0.1, 1.5), (1.1, 1.1), (-0.5, 2.0), (0.7, 2.2), (1.6, 1.9)]):
        p["Prop"] += [cyl(f"gb{i}", 0.2, 0.12, 0.8, (x, y, 0.0), gm, 6), sphere(f"gh{i}", 0.11, (x, y, 0.92), gm, 5, 4), cyl(f"gp{i}", 0.02, 0.02, 1.2, (x + 0.2, y, 0.0), gm, 4)]
    return p

# ───────────────────────── B-06 이름 없는 장수 ─────────────────────────
SPEC6 = dict(h=2.35, hip=0.95, sh=1.65, neck=1.82, sw=0.42, hand=1.15, hx=0.52, hy=-0.3, prop=1.1)
def b06():
    """이름 없는 장수 2.35m: 얼굴 자리에 눈코 없는 흰 천(이름이 지워짐), 번호패 치마(좁은 널빤지 서른 장이 허리에 둘러 늘어짐), 어깨에 긴 붉은 전포, 오른손에 영기(작은 명령 깃), 왼허리에 환도. Prop은 허공에 도는 일곱 진(陣) 원반."""
    r = random.Random(52); p = P(); s = SPEC6; ARM = "#3A3E52"
    p["Hips"] += [cyl("legs", 0.3, 0.22, 0.95, (0, 0, 0.0), "cloth", 8), box("bootL", (0.2, 0.32, 0.16), (0.14, -0.05, 0.08), "hat"), box("bootR", (0.2, 0.32, 0.16), (-0.14, -0.05, 0.08), "hat")]
    for i in range(30):   # 번호패 치마
        a = i / 30 * math.tau; rr = 0.44
        p["Hips"].append(box(f"tag{i}", (0.1, 0.02, r.uniform(0.38, 0.5)), (math.cos(a) * rr, math.sin(a) * rr * 0.8, 0.95 - 0.28), BONE if i % 5 else "#CFC4A6", rot=(0, 0, a + math.pi / 2)))
    p["Hips"] += [cyl("tag_cord", 0.45, 0.45, 0.04, (0, 0, 0.98), "hat", 12, rot=(0, 0, 0)), box("sheath", (0.07, 0.07, 0.95), (0.4, -0.12, 0.35), "hat", rot=(0, 0.25, 0.0)), box("hilt", (0.08, 0.08, 0.22), (0.46, -0.12, 0.98), "gold", rot=(0, 0.25, 0))]
    p["Chest"] += [lathe("torso", [(1.0, 0.3), (1.25, 0.34), (1.5, 0.37), (1.68, 0.33), (1.76, 0.15)], 9, ARM, scale=(1.15, 0.8, 1.0)), box("studs", (0.5, 0.05, 0.4), (0, -0.28, 1.4), "gold"), box("belt", (0.7, 0.5, 0.1), (0, 0, 1.0), FLAG)]
    p["Chest"] += [limb("cape", (0, 0.2, 1.7), (0.0, 0.5, 0.35), 0.28, 0.16, "#6A2A2A", 6), box("cape_back", (0.7, 0.05, 1.2), (0, 0.3, 1.1), "#6A2A2A", rot=(-0.12, 0, 0)), box("shoulderband", (0.7, 0.4, 0.06), (0, 0, 1.7), "gold")]
    for sx in (1, -1): p["Chest"].append(box(f"epaulet{sx}", (0.34, 0.3, 0.1), (sx * 0.48, 0, 1.7), ARM, rot=(0, sx * 0.3, 0)))
    p["Head"] += [sphere("mask", 0.17, (0, 0, 1.95), "#EDE4D0", 8, 6, (1, 0.95, 1.1)), cyl("hat_b", 0.34, 0.34, 0.03, (0, 0, 2.02), "hat", 12), cyl("hat_c", 0.2, 0.14, 0.26, (0, 0, 2.04), "hat", 10), box("hat_plume", (0.05, 0.05, 0.36), (0, 0.06, 2.36), FLAG, rot=(0.25, 0, 0)), box("mask_tie", (0.34, 0.02, 0.03), (0, 0.0, 1.92), "#CFC4A6"), box("tie_tail", (0.03, 0.02, 0.3), (0.0, 0.18, 1.8), "#CFC4A6")]
    arm_pair(p, s, ARM, "gold", 0.1, 0.085)
    hx, hy = -s["hx"], s["hy"]
    p["Hand.R"] += [cyl("flag_pole", 0.025, 0.025, 1.5, (hx, hy, 0.55), "wood_dark", 5), box("flag", (0.5, 0.03, 0.4), (hx + 0.25, hy, 1.85), FLAG), box("flag_mark", (0.14, 0.035, 0.14), (hx + 0.25, hy - 0.01, 1.85), BONE)]
    for i in range(7):   # 진법 원반 일곱: 허공에 둥글게
        a = i / 7 * math.tau
        p["Prop"].append(cyl(f"jin{i}", 0.13, 0.13, 0.02, (math.cos(a) * 1.15, math.sin(a) * 1.15, 0.0), mat_alpha("#E8DDA8", 0.7, 0.5), 8))
    return p

# ───────────────────────── B-07 갱도 반장 칠성 ─────────────────────────
SPEC7 = dict(h=2.2, hip=0.95, sh=1.6, neck=1.78, sw=0.42, hand=1.05, hx=0.5, hy=-0.25, prop=0.9)
def b07():
    """갱도 반장 칠성 2.2m: 어깨가 굽은 광부. 그을린 얼굴에 눈만 희고, 이마에 등불 달린 삿갓(불이 켜져 있다), 허리에 목패 열넷(그중 하나만 테두리가 닳아 밝다), 어깨에 밧줄 타래, 오른손 곡괭이, 왼손 분필. Prop은 갱도 먼지."""
    r = random.Random(53); p = P(); s = SPEC7; SOOT = "#2E2A28"
    p["Hips"] += [cyl("legs", 0.28, 0.2, 0.95, (0, 0, 0.0), "#4A3C30", 8), box("bootL", (0.2, 0.34, 0.18), (0.14, -0.05, 0.09), SOOT), box("bootR", (0.2, 0.34, 0.18), (-0.14, -0.05, 0.09), SOOT), box("wrapL", (0.3, 0.3, 0.2), (0.14, 0, 0.3), "#8A7A5A"), box("wrapR", (0.3, 0.3, 0.2), (-0.14, 0, 0.3), "#8A7A5A")]
    for i in range(14):   # 목패 열넷: 허리끈에 매달림. 일곱째(七)만 밝고 닳음
        a = math.radians(-70 + i * 10.7)
        p["Hips"].append(box(f"mokpae{i}", (0.09, 0.015, 0.16), (math.sin(a) * 0.4, -math.cos(a) * 0.4 * 0.8, 0.74), "#D8C898" if i == 6 else "#6B4A2E", rot=(0, 0, -a)))
    p["Hips"] += [cyl("mokcord", 0.38, 0.38, 0.03, (0, 0, 0.9), "reed", 10)]
    p["Chest"] += [lathe("torso", [(1.0, 0.28), (1.25, 0.33), (1.45, 0.35), (1.62, 0.3), (1.7, 0.12)], 8, "#6A5A4A", scale=(1.1, 0.8, 1.0)), box("vest_open", (0.2, 0.05, 0.6), (0, -0.28, 1.35), "#3A3024"), box("hump", (0.5, 0.3, 0.3), (0, 0.18, 1.6), "#6A5A4A")]
    p["Chest"] += [cyl("rope", 0.3, 0.3, 0.1, (0.0, 0.05, 1.68), "reed", 8, rot=(0.0, 0.9, 0)), cyl("rope2", 0.28, 0.28, 0.1, (0.0, 0.05, 1.6), "#9C8858", 8, rot=(0.0, 0.9, 0))]
    p["Head"] += [sphere("head", 0.16, (0, 0, 1.92), SOOT, 7, 5, (1, 0.95, 1.05)), box("eyeL", (0.045, 0.02, 0.035), (0.06, -0.15, 1.95), "#F3E7D3"), box("eyeR", (0.045, 0.02, 0.035), (-0.06, -0.15, 1.95), "#F3E7D3"), box("mouth", (0.08, 0.02, 0.02), (0, -0.15, 1.85), "#8A5A4A"),
                  cone_hat(0, 0, 2.02), box("lamp", (0.12, 0.08, 0.14), (0, -0.28, 2.1), mat("#FFB066", 2.2)), box("lamp_mount", (0.06, 0.1, 0.05), (0, -0.2, 2.03), "iron")]
    arm_pair(p, s, "#6A5A4A", "#8A7A5A", 0.1, 0.085, SOOT)
    hx, hy = -s["hx"], s["hy"]
    p["Hand.R"] += [cyl("pick_handle", 0.03, 0.03, 1.25, (hx, hy, 0.4), "wood", 5), box("pick_head", (0.7, 0.07, 0.07), (hx, hy, 1.65), "iron"), cyl("pick_tipL", 0.04, 0.0, 0.2, (hx + 0.42, hy, 1.65), "iron", 4, rot=(0, math.pi / 2, 0)), cyl("pick_tipR", 0.04, 0.0, 0.2, (hx - 0.42, hy, 1.65), "iron", 4, rot=(0, -math.pi / 2, 0))]
    p["Hand.L"] += [box("chalk", (0.035, 0.035, 0.12), (s["hx"], s["hy"] - 0.02, s["hand"] - 0.06), "#F3E7D3")]
    p["Prop"] += [sphere(f"dust{i}", r.uniform(0.05, 0.1), (r.uniform(-1.2, 1.2), r.uniform(-1.2, 1.2), r.uniform(0.2, 1.8)), mat_alpha("#8A7A6A", 0.3, 0.0), 5, 3) for i in range(14)]
    return p

def cone_hat(x, y, z):
    """갱도 삿갓: 넓고 낮은 짚 삿갓(위로 살짝 솟음)."""
    return lathe("miner_hat", [(0.0, 0.34), (0.05, 0.3), (0.14, 0.17), (0.22, 0.05), (0.24, 0.0)], 10, "#B09468", loc=(x, y, z), caps=(True, True))

# ───────────────────────── B-08 장부꾼 염씨 ─────────────────────────
SPEC8 = dict(h=2.0, hip=0.9, sh=1.5, neck=1.65, sw=0.33, hand=1.15, hx=0.4, hy=-0.35, prop=1.2)
def b08():
    """장부꾼 염씨 2.0m: 마른 서기. 먹물 번진 청회색 도포, 둥근 안경, 얇은 수염, 작은 갓. 두 손에 두꺼운 장부(한쪽 귀가 접힌 뒷장), 허리에 주판과 붓통. Prop은 허공에 떠도는 뒷장 열네 장(이름을 몰래 적은 것)."""
    r = random.Random(54); p = P(); s = SPEC8; ROBE = "#5A6478"
    p["Hips"] += [lathe("skirt", [(0.1, 0.42), (0.4, 0.36), (0.75, 0.28), (0.95, 0.24)], 10, ROBE, fn=lambda i, k, th, z, rr: (rr * (1 + 0.05 * (1 if k % 2 else -1)), z)), box("shoeL", (0.14, 0.26, 0.1), (0.12, -0.12, 0.05), "hat"), box("shoeR", (0.14, 0.26, 0.1), (-0.12, -0.12, 0.05), "hat")]
    p["Hips"] += [box("ink_stain", (0.3, 0.02, 0.2), (0.1, -0.33, 0.35), "ink", rot=(0, 0, 0.1)), box("abacus", (0.3, 0.05, 0.18), (-0.3, -0.18, 0.88), "wood"), box("abacus_rod", (0.3, 0.06, 0.02), (-0.3, -0.18, 0.88), "gold"), cyl("brush_case", 0.035, 0.035, 0.34, (0.32, -0.16, 0.72), "wood_dark", 5, rot=(0, 0.3, 0))]
    p["Chest"] += [lathe("torso", [(0.95, 0.24), (1.15, 0.26), (1.35, 0.26), (1.5, 0.2), (1.56, 0.1)], 9, ROBE, scale=(1.1, 0.8, 1.0)), box("sash", (0.5, 0.4, 0.07), (0, 0, 0.98), "#2A2A38"), box("collar", (0.22, 0.2, 0.05), (0, -0.05, 1.55), BONE)]
    p["Head"] += [sphere("head", 0.14, (0, 0, 1.76), "#C9B8A0", 8, 6, (1, 0.95, 1.1)), box("moustache", (0.12, 0.02, 0.025), (0, -0.14, 1.72), "#D8D0C0"), box("goatee", (0.03, 0.02, 0.12), (0, -0.13, 1.64), "#D8D0C0"),
                  cyl("spec_l", 0.04, 0.04, 0.01, (0.055, -0.14, 1.79), mat_alpha("#BFE8FF", 0.5, 0.6), 8, rot=(math.pi / 2, 0, 0)), cyl("spec_r", 0.04, 0.04, 0.01, (-0.055, -0.14, 1.79), mat_alpha("#BFE8FF", 0.5, 0.6), 8, rot=(math.pi / 2, 0, 0)),
                  cyl("gat_brim", 0.24, 0.24, 0.02, (0, 0, 1.9), "hat", 12), cyl("gat_crown", 0.1, 0.09, 0.16, (0, 0, 1.9), "hat", 9), box("gat_strap", (0.02, 0.02, 0.35), (0.12, -0.08, 1.72), "red")]
    arm_pair(p, s, ROBE, "#2A2A38", 0.085, 0.07, "#C9B8A0")
    # 장부: 두 손목 사이(앞 가슴 높이). 왼손 쪽에 붙여 두 팔이 함께 든다. 책등·표지·종이·접힌 귀
    bx, by, bz = 0.0, s["hy"] - 0.08, s["hand"] + 0.05
    for hn in ("Hand.L",):
        p[hn] += [box("ledger_cover", (0.62, 0.1, 0.46), (bx, by, bz), "#4A3322"), box("ledger_pages", (0.56, 0.08, 0.4), (bx, by - 0.01, bz), "#E8DDA8"), box("ledger_spine", (0.04, 0.12, 0.46), (bx + 0.32, by, bz), "#2A2420"), box("fold", (0.1, 0.085, 0.1), (bx - 0.25, by - 0.05, bz - 0.17), "#CFC4A6", rot=(0, 0, 0.7))]
        p[hn] += [box(f"line{i}", (0.4, 0.003, 0.012), (bx, by - 0.055, bz + 0.15 - i * 0.05), "ink") for i in range(6)]
    p["Hand.R"] += [cyl("brush", 0.012, 0.012, 0.3, (-s["hx"], s["hy"] - 0.05, s["hand"] - 0.02), "wood", 4, rot=(0.9, 0, 0)), sphere("brush_tip", 0.02, (-s["hx"], s["hy"] - 0.2, s["hand"] + 0.1), "ink", 4, 3)]
    for i in range(14):   # 뒷장 열네 장: 얇은 종이가 허공에 떠 천천히 돈다
        a = i / 14 * math.tau; rr = 0.9 + 0.15 * (i % 3)
        p["Prop"].append(box(f"page{i}", (0.26, 0.004, 0.34), (math.cos(a) * rr, math.sin(a) * rr, (i % 5) * 0.18 - 0.2), "#E8DDA8", rot=(0.3 * math.sin(a * 2), 0.2, a)))
    return p

BOSS = [("boss_b05_daedol2", b05, SPEC5), ("boss_b06_jangsu", b06, SPEC6), ("boss_b07_chilseong", b07, SPEC7), ("boss_b08_yeom", b08, SPEC8)]
# 보스마다 다른 '예고→내리침' 몸짓. f=앞/위로 든 정도(rx 음수), lean=앞으로 숙임, tw=몸통 비틀기
SIG = {"boss_b05_daedol2": dict(wind=dict(R=-160, L=-60, lean=-14, tw=-18, nod=-10), atk=dict(R=-40, L=-50, lean=26, tw=14, nod=14), kneel_drop=-0.5),   # 깃대 위로 치켜들었다 찍음
       "boss_b06_jangsu": dict(wind=dict(R=-170, L=-20, lean=-8, tw=-10, nod=-12), atk=dict(R=-95, L=-20, lean=10, tw=6, nod=6), kneel_drop=-0.5),   # 영기를 높이 들었다 앞을 가리킴
       "boss_b07_chilseong": dict(wind=dict(R=-175, L=-30, lean=-16, tw=-22, nod=-10), atk=dict(R=-30, L=-40, lean=32, tw=20, nod=16), kneel_drop=-0.45),   # 곡괭이를 어깨 뒤로 젖혔다 내려찍음
       "boss_b08_yeom": dict(wind=dict(R=-70, L=-85, lean=-10, tw=-6, nod=-8), atk=dict(R=-110, L=-120, lean=18, tw=0, nod=10), kneel_drop=-0.4)}   # 장부를 가슴께로 펴 들었다 앞으로 확 내밂

def clips(name):
    sg = SIG[name]
    def pose(R=0, L=0, lean=0, tw=0, nod=0, drop=0, hturn=0, rs=0, ls=0):
        return {"Chest": {"r": (lean, 0, tw)}, "Hips": {"r": (0, 0, hturn), "l": (0, 0, drop)}, "Head": {"r": (nod, 0, 0)}, "UpperArm.R": {"r": (R, rs, 0)}, "UpperArm.L": {"r": (L, ls, 0)}, "Prop": {"r": (0, 0, 0)}}
    a = pose(nod=1.5); b = pose(lean=2, nod=-1, R=-3, L=-3)
    C = {}
    C["Idle"] = ([(0, a), (60, b), (120, a)], "BEZIER", True, {})
    w, k = sg["wind"], sg["atk"]
    wp = pose(**w); ap = pose(**k)
    C["Windup"] = ([(0, a), (14, pose(R=w["R"] * 0.3, L=w["L"] * 0.3, lean=w["lean"] * 0.4, nod=w["nod"] * 0.4)), (30, wp), (40, {**wp, "Chest": {"r": (w["lean"] - 2, 0, w["tw"] - 3)}})], "BEZIER", False, {"windup_end": 40, "hit": 40, "tell": 0, "flash": 30, "loaded": 30})
    C["Attack"] = ([(0, wp), (6, ap), (14, ap), (24, a)], "LINEAR", False, {"hit": 6})
    C["Hit1"] = ([(0, pose(lean=-4, nod=-3)), (2, pose(lean=-6, nod=-5)), (10, a)], "BEZIER", False, {"peak": 2})
    C["Hit2"] = ([(0, pose(lean=-7, nod=-6)), (3, pose(lean=-14, nod=-12, drop=-0.04, R=8, L=8)), (8, pose(lean=4, nod=3)), (18, a)], "BEZIER", False, {"peak": 3, "rebound": 8})
    C["Stagger"] = ([(0, pose(lean=-11, nod=-9)), (5, pose(lean=-22, nod=-18, drop=-0.1, hturn=-8, R=20, L=20)), (12, pose(lean=8, nod=8, drop=-0.05, hturn=6)), (20, pose(lean=-8, nod=-6, hturn=-4)), (28, pose(lean=3, nod=2)), (36, a)], "BEZIER", False, {"peak": 5})
    kd = sg["kneel_drop"]; kn = pose(drop=kd, lean=16, nod=18, R=-10, L=-10)
    C["Kneel"] = ([(0, a), (10, pose(drop=kd * 0.3, lean=6, nod=6)), (24, pose(drop=kd * 0.7, lean=12, nod=12)), (45, kn)], "BEZIER", False, {"thud": 24})
    kh2 = pose(drop=kd, lean=14, nod=15, R=-8, L=-8)
    C["KneelHold"] = ([(0, kn), (60, kh2), (120, kn)], "BEZIER", True, {})
    C["Tendo"] = ([(0, kn), (40, pose(drop=kd * 0.4, lean=8, nod=8)), (70, pose()), (110, pose(lean=-4, nod=-8, R=-40, L=-40)), (140, pose(lean=-6, nod=-12, R=-80, L=-80)), (150, pose(lean=-6, nod=-12, R=-80, L=-80))], "BEZIER", False, {"stand_up": 70, "dissolve": 140})
    C["Pahon"] = ([(0, a), (6, pose(R=-70, L=-70, lean=-20, nod=-18)), (30, pose(R=-60, L=-60, lean=-14, nod=-12, drop=-0.05)), (60, pose(R=10, L=10, lean=16, nod=18, drop=kd)), (90, pose(R=0, L=0, lean=18, nod=20, drop=kd * 1.1))], "BEZIER", False, {"hit": 6, "shatter": 60})
    return C

def build(name, fn, spec, sheets=False):
    reset(); anim.setup_scene(); p = fn(); parts = []
    for bone, objs in p.items(): parts += to_group(objs, bone)
    o = join(name, parts); arm = rig(o, bones_for(spec)); lo, hi = bounds(o); man = []
    for cname, (keys, interp, loop, ev) in clips(name).items():
        i = anim.clip(arm, cname, keys, interp); i.update({"loop": loop, "events": ev}); man.append(i)
    if sheets:
        setup_render(4.6, (0, 0, 1.2), size=(250, 330), ground_size=14)
        for c in man:
            if c["name"] in ("Idle", "KneelHold", "Hit1", "Hit2", "Stagger", "Pahon"): continue
            n = c["frames"]; fr = sorted({0, round(n * 0.25), round(n * 0.5), round(n * 0.75), n - 1})
            anim.sheet(arm, c["name"], fr, os.path.join(OUT, "previews", f"anim_{name}_{c['name']}"), cell=(250, 330), ortho=4.6, center=(0, 0, 1.2))
    path = os.path.join(OUT, "boss", f"{name}.glb"); anim.export_rig(arm, path); v = anim.verify(path)
    return {"name": name, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "clips": man, "verify": v}

if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    res = [build(*b, sheets="--sheets" in sys.argv) for b in BOSS if not only or b[0] in only]
    for r in res: print(r["name"], r["tris"], r["size_m"], r["verify"]["joints"], len(r["verify"]["animations"]))
    if not only:
        json.dump({"fps": anim.FPS, "bosses": res}, open(os.path.join(OUT, "boss", "_act2_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        for i, (name, fn, spec) in enumerate(BOSS):
            p = fn(); parts = []
            for bone, objs in p.items(): parts += to_group(objs, bone)
            o = join(name, parts); o.location = ((i - 1.5) * 4.6, 0, 0)
        setup_render(19, (0, 0, 1.2), size=(1500, 620), ground_size=40); render(os.path.join(OUT, "previews", "bosses_act2_50deg.png"))
