"""3막 보스 본체: B-12 흑월 차사(1차 등장에도 같이 씀), B-09 망부석 아낙, B-10 만선호 선장, B-11 다리 밑 왕초. 실행: python3 boss_act3.py [이름 ...] [--sheets]
근거: docs/narrative/SCENARIO-ACT3.md §보스, planning/openworld/act3/act3_map.json(싸움터). 틀은 boss_act2.py 와 같다(뼈 9개, 클립 10개, 이름·길이 동일 → 코드 연결 같음).
흑월은 '또 하나의 차사': 주인공과 같은 실루엣(검은 갓·검은 도포·사슬)을 일부러 닮되 키가 크고 야위었다. 눈은 붉게 빛나고, 갓에 초승달 장식, 한 손에 명부(이름이 지워진 장), 다른 손에 끌리는 사슬, 허공에 찢긴 명부 쪽 일곱이 돈다.
눈 쌓인 어깨는 B-12 싸움터(성문 밖 눈밭) 분위기다. 1차(B-04, ① 무덤골)에도 같은 모델을 쓴다: 눈 조각(snow*)은 Prop이 아니라 몸에 붙어 있으니 1차에서 거슬리면 코드가 노드 이름 snow* 만 끄면 된다."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import to_group, rig
import anim
import boss_act2 as B2
from boss_act2 import P, bones_for, arm_pair, OUT
BLK, BLK2, BONE, RED = "#1E1E26", "#2E2E3A", "#E8DDA8", "#B02A2A"

SPEC12 = dict(h=2.25, hip=0.95, sh=1.65, neck=1.8, sw=0.4, hand=1.1, hx=0.5, hy=-0.3, prop=1.0)
def b12():
    """흑월 차사 2.25m: 야윈 키 큰 검은 차사. 끌리는 긴 도포 자락, 어깨에 쌓인 눈, 붉은 눈, 갓에 초승달. 오른손 사슬, 왼손 명부."""
    r = random.Random(112); p = P(); s = SPEC12
    p["Hips"] += [lathe("skirt", [(0.05, 0.4), (0.4, 0.36), (0.75, 0.3), (0.95, 0.24)], 10, BLK, fn=lambda i, k, th, z, rr: (rr * (1 + 0.1 * (1 if k % 2 else -1) * (1 - i / 3.0)), z + (0.05 * (k % 3) if i == 0 else 0))),
                  box("shoeL", (0.14, 0.3, 0.1), (0.13, -0.1, 0.05), "hat"), box("shoeR", (0.14, 0.3, 0.1), (-0.13, -0.1, 0.05), "hat")]
    p["Hips"] += [box(f"tatter{i}", (0.1, 0.02, r.uniform(0.3, 0.55)), (-0.35 + i * 0.12, -0.34, 0.3), BLK2, rot=(0.08, 0, r.uniform(-.1, .1))) for i in range(7)]       # 해진 자락
    p["Chest"] += [lathe("torso", [(0.95, 0.26), (1.15, 0.27), (1.4, 0.28), (1.58, 0.22), (1.66, 0.1)], 9, BLK, scale=(1.1, 0.8, 1.0)), box("sash", (0.52, 0.42, 0.09), (0, 0, 1.0), RED), box("collar", (0.24, 0.2, 0.05), (0, -0.06, 1.66), BONE)]
    for sx in (1, -1): p["Chest"].append(sphere(f"snow_sh{sx}", 0.17, (sx * 0.4, 0, 1.68), "#E8EAEE", 6, 4, (1.3, 1, 0.45)))      # 어깨에 쌓인 눈
    for i in range(10):   # 몸에 감긴 사슬: 나선 고리
        a = i / 10 * math.tau * 1.5; z = 1.1 + i * 0.045
        p["Chest"].append(box(f"wrap{i}", (0.1, 0.05, 0.05), (math.cos(a) * 0.29, math.sin(a) * 0.22, z), "iron", rot=(0, 0, a + math.pi / 2)))
    p["Head"] += [sphere("head", 0.14, (0, 0, 1.84), "#C9C2B6", 8, 6, (1, 0.95, 1.12)), cyl("gat_brim", 0.52, 0.52, 0.03, (0, 0, 1.97), "hat", 14), cyl("gat_crown", 0.17, 0.13, 0.32, (0, 0, 1.97), "hat", 9),
                  cyl("moon_disc", 0.07, 0.07, 0.02, (0, -0.14, 2.14), "#E8E6D8", 10, rot=(math.pi / 2, 0, 0)), cyl("moon_cut", 0.06, 0.06, 0.024, (0.03, -0.14, 2.15), "hat", 10, rot=(math.pi / 2, 0, 0)),     # 초승달 장식
                  box("eyeL", (0.05, 0.02, 0.03), (0.06, -0.14, 1.87), mat("#FF4040", 1.4)), box("eyeR", (0.05, 0.02, 0.03), (-0.06, -0.14, 1.87), mat("#FF4040", 1.4)), box("brim_snow", (0.5, 0.2, 0.025), (0, 0.18, 2.0), "#E8EAEE", rot=(0.1, 0, 0)), box("gat_strap", (0.02, 0.02, 0.4), (0.13, -0.08, 1.76), RED)]
    arm_pair(p, s, BLK, "#E8E6D8", 0.085, 0.07, "#C9C2B6")
    # 오른손 사슬: 손목에서 땅으로 늘어진 고리 열여덟(번갈아 돌려 고리 모양), 끝은 바닥에 끌린다
    hx, hy = -s["hx"], s["hy"]
    for i in range(18):
        t = i / 17; z = s["hand"] - 0.05 - t * 1.0; y = hy - 0.05 - 0.35 * math.sin(t * math.pi * 0.9) * 0.6 - t * 0.15
        p["Hand.R"].append(box(f"link{i}", (0.07, 0.025, 0.1), (hx, y, max(z, 0.04)), "iron", rot=(0, (i % 2) * 1.5708, 0)))
    p["Hand.R"].append(sphere("chain_end", 0.09, (hx, hy - 0.5, 0.06), "iron", 5, 4))
    # 왼손 명부: 열린 장. 이름이 있어야 할 자리가 먹으로 지워져 있다
    bx, by, bz = s["hx"] * 0.55, hy - 0.22, s["hand"] + 0.2
    p["Hand.L"] += [box("ledger_cover", (0.5, 0.06, 0.38), (bx, by, bz), "#2A2420", rot=(0.2, 0, 0)), box("ledger_pages", (0.46, 0.05, 0.34), (bx, by - 0.01, bz), BONE, rot=(0.2, 0, 0))]
    p["Hand.L"] += [box(f"blot{i}", (0.3 - 0.03 * i, 0.003, 0.025), (bx, by - 0.045, bz + 0.12 - i * 0.05), "ink", rot=(0.2, 0, 0)) for i in range(5)]
    for i in range(7):    # 찢긴 명부 쪽 일곱: 허공을 천천히 돈다
        a = i / 7 * math.tau; rr = 1.0 + 0.1 * (i % 2)
        p["Prop"].append(box(f"page{i}", (0.22, 0.004, 0.3), (math.cos(a) * rr, math.sin(a) * rr, 0.6 + (i % 4) * 0.35), BONE, rot=(0.3 * math.sin(a * 2), 0.2, a)))
    return p


# ───────────────────────── B-09 망부석 아낙 ─────────────────────────
SPEC9 = dict(h=2.3, hip=0.9, sh=1.55, neck=1.72, sw=0.36, hand=1.0, hx=0.4, hy=-0.35, prop=0.3)
def b09():
    """망부석 아낙 2.3m: 허리 아래가 바위와 붙어 있는 젖은 여인. 젖은 저고리, 등을 덮은 긴 머리, 오른손에 남편의 옷 한 벌(헛묘에 묻지 못한 옷). 발치에 물결 고리 셋(Prop)."""
    r = random.Random(109); p = P(); s = SPEC9; WET = "#6E7E8E"; ROCKC = "#6E6A62"
    p["Hips"] += [lathe("rock", [(0.0, 0.62), (0.3, 0.7), (0.6, 0.6), (0.9, 0.46), (1.1, 0.3)], 8, ROCKC, fn=lambda i, k, th, z, rr: (rr * (1 + 0.14 * math.sin(k * 2.1 + i)), z)), sphere("rock_l", 0.35, (0.5, -0.2, 0.3), "#58554F", 6, 4), sphere("rock_r", 0.3, (-0.45, -0.3, 0.25), "#58554F", 6, 4)]
    p["Hips"] += [sphere(f"moss{i}", 0.14, (r.uniform(-0.5, 0.5), r.uniform(-0.5, 0.2), r.uniform(0.2, 0.9)), "#58704A", 5, 3, (1, 1, 0.5)) for i in range(5)]
    p["Hips"] += [lathe("chima", [(0.85, 0.34), (0.95, 0.3), (1.05, 0.26)], 9, "#5E6A76", fn=lambda i, k, th, z, rr: (rr * (1 + 0.06 * math.sin(k * 3.0)), z - 0.1 * (k % 2)))]       # 바위에 물려 흘러내린 젖은 치마
    p["Chest"] += [lathe("torso", [(1.0, 0.22), (1.2, 0.24), (1.4, 0.24), (1.52, 0.2), (1.58, 0.1)], 9, WET, scale=(1.05, 0.8, 1.0)), box("goreum", (0.1, 0.03, 0.4), (0.02, -0.2, 1.22), "#B8B2A0", rot=(0, 0, 0.2))]      # 젖은 저고리와 옷고름
    p["Head"] += [sphere("head", 0.13, (0, 0, 1.76), "#B8B6AC", 8, 6, (1, 0.95, 1.1)), box("closed_l", (0.04, 0.01, 0.01), (0.05, -0.13, 1.78), "ink"), box("closed_r", (0.04, 0.01, 0.01), (-0.05, -0.13, 1.78), "ink")]
    p["Head"] += [box(f"hair{i}", (0.05, 0.03, r.uniform(0.7, 1.15)), (-0.12 + i * 0.03, 0.12 + 0.02 * (i % 3), 1.62 - (0.7 + 0.1 * (i % 3)) / 2 + 0.05), "#16161C", rot=(0.12, 0, r.uniform(-.06, .06))) for i in range(9)]     # 등을 덮는 긴 머리
    p["Head"] += [sphere("hair_top", 0.15, (0, 0.03, 1.8), "#16161C", 7, 5, (1, 1.05, 0.9))]
    arm_pair(p, s, WET, None, 0.08, 0.065, "#B8B6AC")
    hx, hy = -s["hx"], s["hy"]            # 남편의 옷: 오른손 앞 가슴께, 접은 흰 옷과 늘어진 소매 둘
    p["Hand.R"] += [box("clothes", (0.34, 0.2, 0.2), (hx, hy - 0.12, s["hand"] + 0.05), "#D8D2BE", rot=(0.2, 0, 0.1)), box("sleeveA", (0.1, 0.05, 0.42), (hx - 0.14, hy - 0.12, s["hand"] - 0.2), "#D8D2BE", rot=(0, 0, 0.12)), box("sleeveB", (0.1, 0.05, 0.36), (hx + 0.14, hy - 0.12, s["hand"] - 0.18), "#D8D2BE", rot=(0, 0, -0.12))]
    wm = mat_alpha("#7FB4D8", 0.35, 0.25)
    for i, rr in enumerate((1.5, 2.1, 2.7)): p["Prop"].append(lathe(f"ripple{i}", [(0.0, rr), (0.03, rr + 0.1)], 16, wm, loc=(0, 0, 0.04 + 0.01 * i), caps=(False, False)))     # 물결 고리
    return p

# ───────────────────────── B-10 만선호 선장 ─────────────────────────
SPEC10 = dict(h=2.1, hip=0.9, sh=1.55, neck=1.7, sw=0.38, hand=1.0, hx=0.45, hy=-0.3, prop=1.0)
def b10():
    """만선호 선장 2.1m: 젖은 패랭이와 해진 뱃사람 옷, 손에 끊긴 밧줄(끝에 매듭 일곱), 허리에 감은 밧줄 고리. 등 뒤(Prop)에 줄에 매달린 흐린 선원 일곱."""
    r = random.Random(110); p = P(); s = SPEC10; COAT = "#4A5A66"; ROPE = "#B4A66A"
    p["Hips"] += [lathe("skirt", [(0.1, 0.34), (0.4, 0.3), (0.75, 0.26), (0.95, 0.22)], 9, "#3A4650", fn=lambda i, k, th, z, rr: (rr * (1 + 0.1 * (1 if k % 2 else -1) * (1 - i / 3.0)), z)), box("bootL", (0.16, 0.32, 0.14), (0.12, -0.1, 0.07), "hat"), box("bootR", (0.16, 0.32, 0.14), (-0.12, -0.1, 0.07), "hat")]
    p["Hips"] += [box(f"tatter{i}", (0.08, 0.02, r.uniform(0.25, 0.5)), (-0.3 + i * 0.1, -0.3, 0.3), "#3A4650", rot=(0.08, 0, r.uniform(-.1, .1))) for i in range(7)]
    p["Chest"] += [lathe("torso", [(0.95, 0.24), (1.15, 0.27), (1.38, 0.28), (1.5, 0.22), (1.56, 0.1)], 9, COAT, scale=(1.1, 0.85, 1.0)), box("band", (0.5, 0.4, 0.08), (0, 0, 1.0), "#6A4A36")]
    for i in range(3): p["Chest"].append(cyl(f"coil{i}", 0.3 - 0.01 * i, 0.3 - 0.01 * i, 0.06, (0, 0, 1.04 + 0.07 * i), ROPE, 9))       # 허리에 감은 밧줄
    p["Head"] += [sphere("head", 0.14, (0, 0, 1.78), "#BDB4A4", 8, 6, (1, 0.95, 1.1)), box("beard", (0.18, 0.04, 0.16), (0, -0.12, 1.66), "#D8D0C0"), box("eyeL", (0.04, 0.02, 0.025), (0.055, -0.135, 1.81), mat("#BFE8FF", 1.0)), box("eyeR", (0.04, 0.02, 0.025), (-0.055, -0.135, 1.81), mat("#BFE8FF", 1.0)),
                  cyl("paengi_brim", 0.38, 0.38, 0.025, (0, 0, 1.9), "#8A7A5A", 12), cyl("paengi_crown", 0.15, 0.1, 0.2, (0, 0, 1.9), "#8A7A5A", 8), box("drip", (0.02, 0.02, 0.12), (0.28, -0.1, 1.82), mat_alpha("#7FB4D8", 0.5, 0.2))]
    arm_pair(p, s, COAT, "#3A4650", 0.09, 0.075, "#BDB4A4")
    hx, hy = -s["hx"], s["hy"]            # 오른손 끊긴 밧줄: 매듭 일곱, 끝은 풀어져 갈라짐
    for i in range(14): p["Hand.R"].append(sphere(f"rp{i}", 0.04, (hx, hy - 0.05 - i * 0.07, s["hand"] - 0.05 - i * 0.06 + 0.01 * math.sin(i)), ROPE, 4, 3))
    for i in range(7): p["Hand.R"].append(sphere(f"knot{i}", 0.065, (hx, hy - 0.05 - i * 0.14, s["hand"] - 0.05 - i * 0.12), "#8A7A4A", 5, 4))
    p["Hand.R"] += [limb(f"frayed{i}", (hx, hy - 1.0, s["hand"] - 0.9), (hx + (i - 1) * 0.1, hy - 1.15, 0.05), 0.02, 0.01, ROPE, 4) for i in range(3)]
    gm = mat_alpha("#BFE8FF", 0.26, 0.7)
    p["Prop"].append(limb("line", (-1.4, 0.7, 2.0), (1.4, 0.7, 2.0), 0.02, 0.02, ROPE, 4))
    for i in range(7): x = -1.2 + i * 0.4; p["Prop"] += [cyl(f"gb{i}", 0.12, 0.08, 0.7, (x, 0.7, 0.6), gm, 6), sphere(f"gh{i}", 0.09, (x, 0.7, 1.4), gm, 5, 4), limb(f"gr{i}", (x, 0.7, 1.5), (x, 0.7, 2.0), 0.015, 0.015, gm, 3)]    # 줄에 매달린 선원 혼 일곱
    return p

# ───────────────────────── B-11 다리 밑 왕초 ─────────────────────────
SPEC11 = dict(h=1.75, hip=0.8, sh=1.3, neck=1.45, sw=0.32, hand=0.85, hx=0.38, hy=-0.28, prop=1.0)
def b11():
    """다리 밑 왕초 1.75m: 누더기 위에 기운 도포를 걸친 마른 사내. 목에 나무 조각을 줄줄이 꿴 목걸이(아이들 별명), 맨 아래 조각은 비어 있다. 주변에 이름표 여섯(Prop)이 맴돈다."""
    r = random.Random(111); p = P(); s = SPEC11; ROBE = "#6A5E48"; PATCH = ["#7A4A3A", "#4A5A6A", "#8A7A52"]
    p["Hips"] += [lathe("skirt", [(0.1, 0.34), (0.35, 0.3), (0.62, 0.27), (0.78, 0.24)], 9, ROBE, fn=lambda i, k, th, z, rr: (rr * (1 + 0.1 * (1 if k % 2 else -1) * (1 - i / 3.0)), z)), box("shoeL", (0.13, 0.24, 0.09), (0.11, -0.08, 0.04), "hat"), box("shoeR", (0.13, 0.24, 0.09), (-0.11, -0.08, 0.04), "hat")]
    p["Hips"] += [box(f"patch{i}", (0.16, 0.02, 0.14), (r.uniform(-0.2, 0.2), -0.3, r.uniform(0.2, 0.6)), PATCH[i % 3], rot=(0, 0, r.uniform(-.3, .3))) for i in range(5)]
    p["Chest"] += [lathe("torso", [(0.8, 0.22), (0.98, 0.24), (1.18, 0.24), (1.32, 0.19), (1.38, 0.09)], 9, ROBE, scale=(1.1, 0.85, 1.0)), box("rope_belt", (0.46, 0.36, 0.05), (0, 0, 0.84), "#B4A66A")]
    p["Chest"] += [box(f"p{i}", (0.14, 0.02, 0.12), (r.uniform(-0.18, 0.18), -0.2, r.uniform(1.0, 1.3)), PATCH[i % 3], rot=(0, 0, r.uniform(-.3, .3))) for i in range(4)]
    for i in range(23):   # 나무 조각 목걸이: 줄에 꿴 별명 조각 스물 남짓(끝 하나는 비어 있다)
        t = i / 22; a = math.pi * (0.1 + 0.8 * t); x = -math.cos(a) * 0.24; z = 1.38 - math.sin(a) * 0.34
        p["Chest"].append(box(f"tag{i}", (0.045, 0.012, 0.075), (x, -0.22 - 0.02 * math.sin(a), z), "#B09468" if i < 22 else "#E6DFC8", rot=(0, 0, (t - 0.5) * 1.2)))
    p["Chest"] += [limb("string", (-0.24, -0.2, 1.4), (0.24, -0.2, 1.4), 0.008, 0.008, "#4A3A2E", 3)]
    p["Head"] += [sphere("head", 0.13, (0, 0, 1.55), "#C9B8A0", 8, 6, (1, 0.95, 1.1)), box("scruff", (0.16, 0.03, 0.08), (0, -0.12, 1.45), "#6A6458"), box("eyeL", (0.04, 0.02, 0.025), (0.05, -0.12, 1.58), mat("#FFE0A0", 0.8)), box("eyeR", (0.04, 0.02, 0.025), (-0.05, -0.12, 1.58), mat("#FFE0A0", 0.8)),
                  box("rag_band", (0.3, 0.2, 0.05), (0, 0, 1.66), "#8A5A44"), box("rag_tail", (0.06, 0.02, 0.2), (0.12, 0.14, 1.56), "#8A5A44", rot=(0.2, 0, 0.1))]
    arm_pair(p, s, ROBE, "#8A7A52", 0.075, 0.06, "#C9B8A0")
    for i in range(6):    # 맴도는 이름표: 별명이 불리면 일어서는 혼의 표시
        a = i / 6 * math.tau; rr = 0.95
        p["Prop"].append(box(f"name{i}", (0.2, 0.02, 0.28), (math.cos(a) * rr, math.sin(a) * rr, 0.9 + 0.1 * (i % 2)), "#B09468", rot=(0, 0.2, a + math.pi / 2)))
    return p

BOSS3 = [("boss_b09_mangbu_ahnak", b09, SPEC9), ("boss_b10_captain", b10, SPEC10), ("boss_b11_wangcho", b11, SPEC11), ("boss_b12_heugwol", b12, SPEC12)]
B2.SIG["boss_b09_mangbu_ahnak"] = dict(wind=dict(R=-125, L=-30, lean=-10, tw=-14, nod=-6), atk=dict(R=-35, L=-30, lean=22, tw=12, nod=10), kneel_drop=-0.4)   # 옷을 머리 위로 들었다 바다 쪽으로 내던짐
B2.SIG["boss_b10_captain"] = dict(wind=dict(R=-165, L=-20, lean=-12, tw=-20, nod=-8), atk=dict(R=-20, L=-30, lean=26, tw=18, nod=12), kneel_drop=-0.45)   # 밧줄을 뒤로 젖혔다 직선으로 휘두름
B2.SIG["boss_b11_wangcho"] = dict(wind=dict(R=-75, L=-75, lean=-10, tw=-6, nod=-8), atk=dict(R=-110, L=-110, lean=14, tw=0, nod=8), kneel_drop=-0.4)   # 두 팔을 벌려 별명을 부름
B2.SIG["boss_b12_heugwol"] = dict(wind=dict(R=-150, L=-100, lean=-14, tw=-16, nod=-8), atk=dict(R=-25, L=-60, lean=28, tw=16, nod=12), kneel_drop=-0.5)   # 사슬을 높이 들었다 명부와 함께 앞으로 내림

if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    res = [B2.build(*b, sheets="--sheets" in sys.argv) for b in BOSS3 if not only or b[0] in only]
    for r in res: print(r["name"], r["tris"], r["size_m"], r["verify"]["joints"], len(r["verify"]["animations"]))
    json.dump({"fps": anim.FPS, "bosses": res}, open(os.path.join(OUT, "boss", "_act3_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
    reset()
    for i, (name, fn, spec) in enumerate(BOSS3):
        p = fn(); parts = []
        for bone, objs in p.items(): parts += to_group(objs, bone)
        o = join(name, parts); o.location = ((i - (len(BOSS3) - 1) / 2) * 4.6, 0, 0)
    setup_render(19, (0, 0, 1.2), size=(1500, 620), ground_size=40); render(os.path.join(OUT, "previews", "bosses_act3_50deg.png"))
