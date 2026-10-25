"""시즌 2 보스 8종 본체: B-13 줄의 맨 앞 노인, B-14 돌아선 혼들의 덩어리, B-15 숫자를 처음 쓴 서리, B-16 벼루지기, B-17 아홉째 문지기, B-18 인을 훔친 혼, B-19 첫 차사, B-20 큰 물막이. 실행: python3 boss_s2.py [이름 ...] [--sheets]
틀은 boss_act2/3와 같다(뼈 9개 Root/Hips/Chest/Head/UpperArm.L·R/Hand.L·R/Prop, 클립 10개 Idle·Windup·Attack·Hit1·Hit2·Stagger·Kneel·KneelHold·Tendo·Pahon, 원점=바닥 한가운데, 정면=-Y).
근거: planning/combat/appendix-E2.md(패턴·약점), SCENARIO-MASTER 보스표(사연). 각자 '약점 소품'을 Prop 뼈나 손에 달아 약점이 눈에 보이게 했다:
 B-13 말뚝+배 정박 때 태울 줄 선 혼(코드) / B-14 이름 쪽지 떠다님 / B-15 도장·붓 / B-16 기억 조각(먹 방울) / B-17 졸음(눈 감음, 종) / B-18 이마의 인 자국(약점 이마 3초) / B-19 그림자(버티기) / B-20 이름 조각 소용돌이(부르기).
B-14·B-20은 천도 불가·덩어리 원형이라 사람 모양이 아니다: 큰 덩어리 + 팔 둘. 키: B-14 3.2 m, B-20 6.0 m(마당 반경 22). 보스 발광은 눈·도장 불빛 정도만."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import to_group
import anim
import boss_act2 as B2
from boss_act2 import P, arm_pair, OUT
INK = "#1E1C24"; PAPER = "#E4E0D4"; ASHG = "#8A8780"; VERM = "#9A3A30"; SOULC = "#7FD6C8"; HEMP = "#A89E84"

def body(p, s, robe, robe2, skin, head_r=0.14, hat=None, skirt_r=(0.36, 0.3, 0.26), sleeve_r=(0.09, 0.075)):
    """공통 사람 몸통: 치마 자락·가슴·머리·양팔. 보스마다 위에 장신구를 덧붙인다."""
    h, hip, sh = s["h"], s["hip"], s["sh"]
    p["Hips"] += [lathe("skirt", [(0.1, skirt_r[0]), (hip * 0.45, skirt_r[1]), (hip * 0.8, skirt_r[2]), (hip, skirt_r[2] * 0.85)], 9, robe2, fn=lambda i, k, th, z, rr: (rr * (1 + 0.1 * (1 if k % 2 else -1) * (1 - i / 3.0)), z)),
                  box("shoeL", (0.14, 0.28, 0.1), (0.12, -0.1, 0.05), "hat"), box("shoeR", (0.14, 0.28, 0.1), (-0.12, -0.1, 0.05), "hat")]
    p["Chest"] += [lathe("torso", [(hip, 0.25), (hip + 0.22, 0.27), (sh - 0.2, 0.27), (sh - 0.05, 0.2), (sh + 0.02, 0.1)], 9, robe, scale=(1.1, 0.82, 1.0))]
    p["Head"] += [sphere("head", head_r, (0, 0, h - 0.18), skin, 8, 6, (1, 0.95, 1.1))]
    arm_pair(p, s, robe, robe2, sleeve_r[0], sleeve_r[1], skin)
def eyes(p, s, col, z=None, glow=1.2):
    z = z if z is not None else s["h"] - 0.15
    p["Head"] += [box("eyeL", (0.04, 0.02, 0.025), (0.055, -0.13, z), mat(col, glow)), box("eyeR", (0.04, 0.02, 0.025), (-0.055, -0.13, z), mat(col, glow))]

# ───────── B-13 줄의 맨 앞 노인 ─────────
SPEC13 = dict(h=1.85, hip=0.85, sh=1.4, neck=1.55, sw=0.32, hand=0.95, hx=0.4, hy=-0.28, prop=1.0)
def b13():
    """줄의 맨 앞 노인 1.85m: 등이 굽은 마른 노인, 백 년 묵은 흰 상복, 허리에 구멍 닳은 엽전 꿰미, 오른손에 나루 말뚝 토막. 백발 수염. 뒤(Prop)에 끝없이 이어진 줄의 첫 밧줄."""
    r = random.Random(113); p = P(); s = SPEC13; body(p, s, "#CFC9B4", "#B4AE98", "#C9BBA6", 0.13)
    p["Head"] += [box("beard", (0.2, 0.05, 0.3), (0, -0.1, s["h"] - 0.36), "#E8E4DA"), cyl("hat_brim", 0.34, 0.34, 0.02, (0, 0, s["h"] - 0.02), HEMP, 12), cyl("hat_crown", 0.14, 0.1, 0.16, (0, 0, s["h"] - 0.02), HEMP, 8)]
    eyes(p, s, "#CFE8E0", glow=0.6)
    p["Chest"] += [box("hunch", (0.34, 0.3, 0.3), (0, 0.16, s["sh"] - 0.12), "#B4AE98", rot=(0.4, 0, 0))]
    for i in range(10): p["Chest"].append(cyl(f"coin{i}", 0.04, 0.04, 0.012, (-0.2 + i * 0.044, -0.24, s["hip"] + 0.1 - 0.015 * (i % 2)), "#B09468", 8, rot=(math.pi / 2, 0, 0)))   # 엽전 꿰미
    hx, hy = -s["hx"], s["hy"]; p["Hand.R"] += [cyl("stake", 0.06, 0.07, 0.9, (hx, hy - 0.05, s["hand"] - 0.45), "#5A4430", 6), box("stake_rope", (0.14, 0.14, 0.05), (hx, hy - 0.05, s["hand"] + 0.02), HEMP)]
    p["Prop"] += [limb("line", (0, 0.6, 0.12), (0, 3.0, 0.12), 0.04, 0.04, HEMP, 4), sphere("knot", 0.08, (0, 0.6, 0.14), HEMP, 5, 4)]
    return p
# ───────── B-14 돌아선 혼들의 덩어리 ─────────
SPEC14 = dict(h=3.2, hip=1.1, sh=2.3, neck=2.6, sw=0.9, hand=1.5, hx=1.6, hy=-0.6, prop=2.2)
def b14():
    """돌아선 혼들의 덩어리 3.2m: 기다리다 돌아선 혼 수백이 엉긴 큰 덩어리. 회청색 몸 덩이 여럿, 등을 돌린 얼굴들(뒤통수만 보임), 엉킨 팔 둘. 주변에 이름 쪽지가 맴돈다(주우면 굳음)."""
    r = random.Random(114); p = P(); s = SPEC14; BODY = ["#6A7078", "#5A6068", "#7A8088", "#4E545C"]
    for i in range(9): a = r.uniform(0, 6.28); d = r.uniform(0.2, 1.1); p["Hips" if i < 3 else "Chest"].append(sphere(f"blob{i}", r.uniform(0.55, 0.95), (math.cos(a) * d, math.sin(a) * d, 0.7 + r.uniform(0, 1.7)), BODY[i % 4], 7, 5, (1, 1, 1.15)))
    for i in range(14):   # 등 돌린 머리들
        a = r.uniform(0, 6.28); z = r.uniform(0.6, 2.9); d = 0.9 + 0.2 * math.sin(z)
        p["Chest"].append(sphere(f"nape{i}", 0.17, (math.cos(a) * d, math.sin(a) * d, z), "#8C8F94", 6, 4, (1, 1, 1.1)))
        p["Chest"].append(box(f"hair{i}", (0.2, 0.05, 0.14), (math.cos(a) * (d + 0.06), math.sin(a) * (d + 0.06), z + 0.08), INK, rot=(0, 0, a)))
    p["Head"] += [sphere("crown", 0.45, (0, 0.1, s["h"] - 0.35), "#6A7078", 7, 5), box("slip_a", (0.2, 0.01, 0.3), (0.2, -0.4, s["h"] - 0.4), PAPER)]
    p["Head"] += [box("eyeL", (0.06, 0.03, 0.03), (0.15, -0.45, s["h"] - 0.3), mat("#BFE8FF", 0.7)), box("eyeR", (0.06, 0.03, 0.03), (-0.15, -0.45, s["h"] - 0.3), mat("#BFE8FF", 0.7))]
    for sx, n, hn in ((1, "UpperArm.L", "Hand.L"), (-1, "UpperArm.R", "Hand.R")):
        sh_ = (sx * s["sw"], 0, s["sh"]); hd = (sx * s["hx"], s["hy"], s["hand"]); p[n].append(limb("arm" + n[-1], sh_, hd, 0.28, 0.2, "#5A6068", 6)); p[hn].append(sphere("fist" + n[-1], 0.3, (hd[0], hd[1], hd[2] - 0.1), "#6A7078", 6, 4))
        for k in range(4): p[hn].append(limb(f"finger{n[-1]}{k}", (hd[0] + sx * 0.1 * (k - 1.5), hd[1] - 0.15, hd[2] - 0.2), (hd[0] + sx * 0.15 * (k - 1.5), hd[1] - 0.5, hd[2] - 0.5), 0.05, 0.03, "#8C8F94", 4))
    for i in range(10): a = i / 10 * math.tau; p["Prop"].append(box(f"slip{i}", (0.2, 0.012, 0.3), (math.cos(a) * 2.0, math.sin(a) * 2.0, 1.2 + 0.4 * (i % 3)), PAPER, rot=(0, 0.25, a + math.pi / 2)))
    return p
# ───────── B-15 숫자를 처음 쓴 서리 ─────────
SPEC15 = dict(h=2.0, hip=0.9, sh=1.5, neck=1.65, sw=0.35, hand=1.1, hx=0.42, hy=-0.3, prop=1.0)
def b15():
    """숫자를 처음 쓴 서리 2.0m: 먹빛 관복에 흰 숫자 띠를 줄줄이 단 야윈 서리. 갓은 쓰지 않고 묶은 상투, 오른손에 긴 붓, 왼손에 도장. 등 뒤로 숫자 두루마리가 떠 있다."""
    r = random.Random(115); p = P(); s = SPEC15; body(p, s, "#34303A", "#26242C", "#C9BFAE", 0.13)
    p["Head"] += [sphere("topknot", 0.08, (0, 0.02, s["h"] + 0.02), INK, 6, 4), box("band", (0.3, 0.3, 0.03), (0, 0, s["h"] - 0.1), PAPER)]
    eyes(p, s, "#FFE0A0", glow=0.8)
    for i in range(9): p["Chest"].append(box(f"num{i}", (0.07, 0.012, 0.22 + 0.05 * (i % 3)), (-0.24 + i * 0.06, -0.24, s["sh"] - 0.35 - 0.04 * (i % 2)), PAPER))     # 숫자 띠
    hx, hy = -s["hx"], s["hy"]; p["Hand.R"] += [cyl("brush", 0.02, 0.02, 1.0, (hx, hy - 0.2, s["hand"] + 0.2), "#3A2C26", 5, rot=(0.9, 0, 0)), sphere("brush_tip", 0.05, (hx, hy - 0.65, s["hand"] + 0.55), INK, 5, 4, (1, 1, 2))]
    p["Hand.L"] += [box("seal_stone", (0.14, 0.14, 0.16), (s["hx"], hy - 0.08, s["hand"] + 0.05), "#6E6A64"), box("seal_face", (0.12, 0.12, 0.02), (s["hx"], hy - 0.08, s["hand"] - 0.05), VERM)]
    for i in range(5): p["Prop"].append(box(f"scroll{i}", (0.5, 0.02, 0.9), (-1.0 + i * 0.5, 0.9, 1.3 + 0.15 * (i % 2)), PAPER, rot=(0, 0.15 * (i - 2), 0.05 * i)))
    return p
# ───────── B-16 벼루지기 ─────────
SPEC16 = dict(h=2.15, hip=0.95, sh=1.6, neck=1.78, sw=0.45, hand=1.1, hx=0.5, hy=-0.32, prop=1.2)
def b16():
    """벼루지기 2.15m: 먹으로 얼룩진 두툼한 도포의 사내. 얼굴은 먹으로 검게 칠해졌고 두 손에 먹 막대를 쥐고 간다. 등에 작은 벼루(Prop)를 졌고 먹물이 흘러내린다."""
    r = random.Random(116); p = P(); s = SPEC16; body(p, s, "#3A3842", "#2A2830", "#2E2C34", 0.15, sleeve_r=(0.11, 0.09))
    eyes(p, s, "#E8E4D0", glow=0.5)
    p["Head"] += [box("topknot", (0.1, 0.1, 0.12), (0, 0, s["h"] - 0.02), INK), box("splat", (0.2, 0.02, 0.1), (0.1, -0.14, s["h"] - 0.2), "#4A4650")]
    for i in range(6): p["Chest"].append(box(f"stain{i}", (r.uniform(.1, .3), 0.012, r.uniform(.1, .4)), (r.uniform(-.22, .22), -0.25, r.uniform(0.9, 1.5)), "#14121A", rot=(0, 0, r.uniform(-.4, .4))))
    for sx in (1, -1): p["Hand.L" if sx > 0 else "Hand.R"].append(box(f"inkstick{sx}", (0.06, 0.06, 0.45), (sx * s["hx"], s["hy"] - 0.08, s["hand"] + 0.1), "#14121A", rot=(0.4, 0, 0)))
    p["Prop"] += [cyl("inkstone", 0.55, 0.6, 0.25, (0, 0.45, 1.3), "#58554F", 12, rot=(0.25, 0, 0)), cyl("ink_pool", 0.45, 0.45, 0.03, (0, 0.43, 1.54), INK, 12, rot=(0.25, 0, 0))]
    p["Prop"] += [limb(f"drip{i}", (-0.3 + i * 0.3, 0.3, 1.2), (-0.3 + i * 0.3, 0.25, 0.4 + 0.2 * (i % 2)), 0.03, 0.02, INK, 4) for i in range(3)]
    return p
# ───────── B-17 아홉째 문지기 ─────────
SPEC17 = dict(h=2.7, hip=1.15, sh=2.0, neck=2.2, sw=0.55, hand=1.3, hx=0.65, hy=-0.35, prop=1.4)
def b17():
    """아홉째 문지기 2.7m: 어깨가 넓은 갑옷 문지기. 눈을 감고 서서 존다(졸음 창). 오른손에 육모방망이, 허리에 큰 종, 등(Prop)에 문짝 조각과 열쇠 꾸러미. 투구 끈이 풀려 있다."""
    r = random.Random(117); p = P(); s = SPEC17; ARM = "#4A4E5C"; body(p, s, ARM, "#34303A", "#B8A890", 0.17, sleeve_r=(0.14, 0.11))
    p["Chest"] += [box("pauldronL", (0.5, 0.4, 0.2), (0.6, 0, s["sh"] - 0.02), "#6A6E7C"), box("pauldronR", (0.5, 0.4, 0.2), (-0.6, 0, s["sh"] - 0.02), "#6A6E7C"), box("breast", (0.6, 0.1, 0.5), (0, -0.28, s["sh"] - 0.45), "#6A6E7C")]
    p["Head"] += [sphere("helm", 0.24, (0, 0, s["h"] - 0.12), "#6A6E7C", 8, 5, (1, 1, 0.9)), box("helm_brim", (0.5, 0.5, 0.04), (0, 0, s["h"] - 0.26), "#4A4E5C"), box("strapL", (0.03, 0.02, 0.3), (0.12, -0.15, s["h"] - 0.48), "#7A5A3A", rot=(0, 0, 0.2)), box("closedL", (0.08, 0.01, 0.012), (0.06, -0.17, s["h"] - 0.3), INK), box("closedR", (0.08, 0.01, 0.012), (-0.06, -0.17, s["h"] - 0.3), INK)]
    hx, hy = -s["hx"], s["hy"]; p["Hand.R"] += [cyl("club", 0.07, 0.1, 1.5, (hx, hy - 0.1, s["hand"] - 0.2), "#4A3A2E", 6, rot=(0.2, 0, 0)), sphere("club_head", 0.12, (hx, hy - 0.4, s["hand"] + 0.5), "#3A2C26", 6, 4)]
    p["Hips"] += [cyl("bell", 0.28, 0.34, 0.45, (0.4, -0.3, s["hip"] - 0.1), "iron", 8), sphere("clapper", 0.07, (0.4, -0.3, s["hip"] - 0.4), "#6A6E7C", 5, 4)]
    p["Prop"] += [box("door_chip", (0.9, 0.08, 1.4), (0, 0.5, 1.5), "#34303A", rot=(0, 0.1, 0)), cyl("keyring", 0.2, 0.2, 0.03, (0.5, 0.45, 1.0), "iron", 10, rot=(math.pi / 2, 0, 0))] + [box(f"key{i}", (0.04, 0.02, 0.2), (0.5 + 0.06 * (i - 2), 0.45, 0.8), "iron") for i in range(5)]
    return p
# ───────── B-18 인을 훔친 혼 ─────────
SPEC18 = dict(h=1.9, hip=0.85, sh=1.42, neck=1.58, sw=0.34, hand=1.0, hx=0.4, hy=-0.28, prop=1.0)
def b18():
    """인을 훔친 혼 1.9m: 얼굴이 없다(흰 민낯 가면, 이름이 없어서). 이마 자리에 붉은 인 자국 네모(약점 이마 3초)가 빛난다. 헐렁한 회색 도포, 두 손에 훔친 인 돌을 받쳐 들었다. 주위에 붉은 인 일곱이 맴돈다."""
    r = random.Random(118); p = P(); s = SPEC18; body(p, s, "#6E6A64", "#58554F", "#E4E0D4", 0.13)
    p["Head"] += [box("mask_blank", (0.2, 0.03, 0.26), (0, -0.115, s["h"] - 0.2), "#EDEAE0"), box("forehead_seal", (0.1, 0.02, 0.1), (0, -0.14, s["h"] - 0.08), mat("#E04A3A", 1.8)), cyl("hood", 0.17, 0.2, 0.2, (0, 0.02, s["h"] - 0.05), "#58554F", 8)]
    for sx, hn in ((1, "Hand.L"), (-1, "Hand.R")): p[hn].append(box(f"palm{sx}", (0.12, 0.2, 0.04), (sx * s["hx"] * 0.6, s["hy"] - 0.12, s["hand"] + 0.05), "#EDEAE0"))
    p["Hand.R"] += [box("seal_stone", (0.2, 0.2, 0.22), (-s["hx"] * 0.5, s["hy"] - 0.16, s["hand"] + 0.2), "#58554F"), box("seal_face", (0.18, 0.18, 0.03), (-s["hx"] * 0.5, s["hy"] - 0.16, s["hand"] + 0.09), VERM)]
    for i in range(7): a = i / 7 * math.tau; p["Prop"].append(box(f"seal{i}", (0.24, 0.24, 0.24), (math.cos(a) * 1.2, math.sin(a) * 1.2, 1.1 + 0.2 * (i % 2)), VERM, rot=(0, 0, a)))
    return p
# ───────── B-19 첫 차사 ─────────
SPEC19 = dict(h=2.2, hip=0.95, sh=1.65, neck=1.8, sw=0.4, hand=1.1, hx=0.5, hy=-0.3, prop=1.0)
def b19():
    """첫 차사 2.2m: 영웅·흑월과 같은 갓·도포 실루엣인데 색이 바래 회백색이고 낡았다. 갓 테가 깨졌고 눈은 청록 불씨. 오른손에 끊어진 첫 사슬(굵은 고리), 왼손은 빈 손바닥. 뒤(Prop)에 땅에 눕는 긴 그림자 형상(그림자 버티기)."""
    r = random.Random(119); p = P(); s = SPEC19; body(p, s, "#8A8780", "#6E6A64", "#BDB6A8", 0.14)
    p["Head"] += [cyl("gat_brim", 0.5, 0.5, 0.03, (0, 0, s["h"] + 0.0), "#4A4650", 14), cyl("gat_crown", 0.16, 0.14, 0.22, (0, 0, s["h"] + 0.02), "#4A4650", 8), box("crack", (0.22, 0.02, 0.03), (0.3, -0.05, s["h"] + 0.02), "#26242C", rot=(0, 0, 0.5))]
    eyes(p, s, SOULC, z=s["h"] - 0.17, glow=1.3)
    hx, hy = -s["hx"], s["hy"]
    for i in range(10): p["Hand.R"].append(box(f"link{i}", (0.1, 0.035, 0.14), (hx, hy - 0.05 - 0.04 * i, s["hand"] - 0.05 - i * 0.1), "iron", rot=(0, (i % 2) * 1.5708, 0)))
    p["Hand.R"].append(sphere("chain_cut", 0.08, (hx, hy - 0.3, 0.05), "#26242C", 5, 4))
    p["Hand.L"] += [box("open_palm", (0.14, 0.24, 0.03), (s["hx"], hy - 0.12, s["hand"] + 0.1), "#BDB6A8", rot=(0.3, 0, 0))]
    p["Prop"] += [box("shadow_body", (0.7, 1.8, 0.02), (0, 1.1, 0.02), "#14121A"), sphere("shadow_head", 0.2, (0, 2.1, 0.02), "#14121A", 6, 3, (1, 1, 0.1)), box("shadow_gat", (0.9, 0.5, 0.02), (0, 2.25, 0.02), "#14121A")]
    return p
# ───────── B-20 큰 물막이 ─────────
SPEC20 = dict(h=6.0, hip=2.0, sh=4.2, neck=4.8, sw=1.6, hand=2.6, hx=2.6, hy=-1.0, prop=3.0)
def b20():
    """큰 물막이 6.0m: 모든 관할에서 깨진 이름이 흘러와 고인 거대한 덩어리. 물빛 몸 덩이 위에 이름 조각(나무 판)이 박혔고, 물이 흘러내리는 팔 둘. 가운데에 비어 있는 큰 얼굴 자리. 둘레에 이름 조각이 소용돌이친다(부르기)."""
    r = random.Random(120); p = P(); s = SPEC20; WTR = mat_alpha("#4A7A8A", 0.7, 0.3); WTR2 = "#2E4E5C"
    for i in range(12): a = r.uniform(0, 6.28); d = r.uniform(0.4, 2.0); p["Hips" if i < 4 else "Chest"].append(sphere(f"mass{i}", r.uniform(1.0, 1.8), (math.cos(a) * d, math.sin(a) * d, 1.5 + r.uniform(0, 3.6)), WTR2 if i % 2 else "#3A6272", 8, 5, (1, 1, 1.1)))
    for i in range(40): a = r.uniform(0, 6.28); z = r.uniform(0.8, 5.0); d = 1.9 + 0.5 * math.sin(z); p["Chest"].append(box(f"tag{i}", (0.28, 0.03, 0.4), (math.cos(a) * d, math.sin(a) * d, z), "#B09468" if i % 3 else PAPER, rot=(0, 0.2, a + math.pi / 2)))
    p["Head"] += [sphere("face_hole", 0.9, (0, -0.4, s["h"] - 0.8), "#14161C", 8, 5, (1, 0.5, 1.1)), box("eyeL", (0.14, 0.04, 0.08), (0.35, -0.82, s["h"] - 0.7), mat("#BFE8FF", 1.0)), box("eyeR", (0.14, 0.04, 0.08), (-0.35, -0.82, s["h"] - 0.7), mat("#BFE8FF", 1.0))]
    for sx, n, hn in ((1, "UpperArm.L", "Hand.L"), (-1, "UpperArm.R", "Hand.R")):
        sh_ = (sx * s["sw"], 0, s["sh"]); hd = (sx * s["hx"], s["hy"], s["hand"]); p[n].append(limb("arm" + n[-1], sh_, hd, 0.7, 0.5, WTR2, 6)); p[hn].append(sphere("fist" + n[-1], 0.7, (hd[0], hd[1], hd[2] - 0.2), "#3A6272", 6, 4))
        for k in range(5): p[hn].append(limb(f"drip{n[-1]}{k}", (hd[0] + 0.15 * (k - 2), hd[1], hd[2] - 0.3), (hd[0] + 0.2 * (k - 2), hd[1], 0.1), 0.06, 0.03, WTR, 4))
    for i in range(24): a = i / 24 * math.tau * 2.0; rr = 3.4 + 0.12 * i; p["Prop"].append(box(f"swirl{i}", (0.3, 0.03, 0.42), (math.cos(a) * rr, math.sin(a) * rr, 1.0 + 0.12 * i), "#B09468" if i % 2 else PAPER, rot=(0, 0.2, a + math.pi / 2)))
    return p
BOSS = [("boss_b13_old_man", b13, SPEC13), ("boss_b14_mass", b14, SPEC14), ("boss_b15_clerk", b15, SPEC15), ("boss_b16_inkkeeper", b16, SPEC16), ("boss_b17_gatekeeper", b17, SPEC17), ("boss_b18_sealthief", b18, SPEC18), ("boss_b19_first_chasa", b19, SPEC19), ("boss_b20_great_dam", b20, SPEC20)]
SIG = {"boss_b13_old_man": dict(wind=dict(R=-70, L=-20, lean=-6, tw=-10, nod=-4), atk=dict(R=-20, L=-20, lean=18, tw=10, nod=8), kneel_drop=-0.35),     # 말뚝을 들어 땅을 짚음
       "boss_b14_mass": dict(wind=dict(R=-140, L=-140, lean=-8, tw=0, nod=-6), atk=dict(R=-20, L=-20, lean=20, tw=0, nod=10), kneel_drop=-0.6),               # 두 팔을 들었다 내려침
       "boss_b15_clerk": dict(wind=dict(R=-120, L=-40, lean=-10, tw=-12, nod=-6), atk=dict(R=-30, L=-30, lean=20, tw=12, nod=10), kneel_drop=-0.45),
       "boss_b16_inkkeeper": dict(wind=dict(R=-100, L=-100, lean=-12, tw=0, nod=-8), atk=dict(R=-25, L=-25, lean=24, tw=0, nod=12), kneel_drop=-0.5),
       "boss_b17_gatekeeper": dict(wind=dict(R=-160, L=-20, lean=-16, tw=-14, nod=-10), atk=dict(R=-20, L=-20, lean=26, tw=14, nod=14), kneel_drop=-0.55),
       "boss_b18_sealthief": dict(wind=dict(R=-110, L=-110, lean=-12, tw=0, nod=-8), atk=dict(R=-40, L=-40, lean=18, tw=0, nod=10), kneel_drop=-0.4),
       "boss_b19_first_chasa": dict(wind=dict(R=-150, L=-60, lean=-14, tw=-16, nod=-8), atk=dict(R=-25, L=-40, lean=26, tw=16, nod=12), kneel_drop=-0.5),
       "boss_b20_great_dam": dict(wind=dict(R=-150, L=-150, lean=-10, tw=0, nod=-6), atk=dict(R=-15, L=-15, lean=16, tw=0, nod=8), kneel_drop=-0.9)}
B2.SIG.update(SIG)
if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    res = [B2.build(*b, sheets="--sheets" in sys.argv) for b in BOSS if not only or b[0] in only]
    for r in res: print(r["name"], r["tris"], r["size_m"], r["verify"]["joints"], len(r["verify"]["animations"]))
    if not only:
        json.dump({"fps": anim.FPS, "bosses": res}, open(os.path.join(OUT, "boss", "_s2_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        for i, (name, fn, spec) in enumerate(BOSS):
            p = fn(); parts = []
            for bone, objs in p.items(): parts += to_group(objs, bone)
            o = join(name, parts); o.location = ((i % 4 - 1.5) * 8.0 if i != 7 else 0, -(i // 4) * 9.0 - (4 if i == 7 else 0), 0)
        setup_render(30, (0, -5, 2.0), size=(1600, 900), ground_size=70); render(os.path.join(OUT, "previews", "bosses_s2_50deg.png"))
