"""시즌 3 보스 11종 본체(B-21~B-31, 모두 '백(魄)' = 장례를 못 치른 몸). 실행: python3 boss_s3.py [이름 ...] [--sheets]
틀은 boss_s2와 같다(뼈 9개, 클립 10개, 60fps, 원점=바닥 한가운데, 정면=-Y). 근거: planning/combat/s3-bosses-draft.md(패턴·약점), docs/narrative/season3_outline.json(사연).
시즌 2 보스가 '혼'이라 청록 불씨·흰 가면이었다면, 백은 '몸'이라 눈에 불을 켜지 않는다: 젖은 흙빛 살갗, 물때·석회·먹이 묻은 옷, 얼굴은 반쯤 그림자. 발광은 B-31의 횃불, 마지막 손짓 정도만.
대사 0줄이라 입은 그리지 않는다. 글자는 쓰지 않는다(명단·글씨는 획 모양 상자로만).
Prop 뼈에 '약점 소품'을 달았다: B-21 뒤집힌 배와 물 실 / B-22 일곱 몸을 묶은 줄 / B-23 사공의 배·이름표 / B-24 건너편 기수와 두 진 / B-25 버팀목 셋 / B-26 석회 띠 / B-27 바닥 글씨 획 / B-28 돌아가는 벼루 바닥 / B-29 밥상 / B-30 새끼줄 / B-31 일곱의 빛과 보릿단."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import to_group
import anim
import boss_act2 as B2
from boss_act2 import P, arm_pair, OUT
from boss_s2 import body, INK, PAPER, ASHG, VERM, HEMP
MUD = "#6A5A48"; SKIN_W = "#8E8576"; WET = "#4A4E50"; LIME = "#D8D4C6"; SOIL = "#5A4A3A"; ROPE = "#9A8C6A"; BOAT = "#4A3A2E"

def faceshade(p, s, r=0.13):
    """얼굴을 반쯤 가리는 젖은 머리칼: 백은 눈을 밝히지 않으므로 그림자로 '표정 없음'을 만든다."""
    p["Head"] += [box("hair_front", (r * 2.0, 0.04, 0.12), (0, -r * 0.95, s["h"] - 0.12), INK), box("hair_back", (r * 2.0, 0.08, 0.3), (0, r * 0.7, s["h"] - 0.22), INK)]

# ───────── B-21 마지막 손님 — 윤 영감의 백 ─────────
SPEC21 = dict(h=1.7, hip=0.8, sh=1.28, neck=1.45, sw=0.3, hand=0.9, hx=0.38, hy=-0.26, prop=0.5)
def b21():
    """윤 영감의 백 1.7m: 물에 불은 흰 도포, 한 손에 엽전 다섯 닢(미리 치른 뱃삯), 한 손은 앞으로 뻗었다. 배는 뒤집혀 등 뒤(Prop)에 있고 물 실이 영감 발목을 배에 묶는다."""
    r = random.Random(121); p = P(); s = SPEC21; body(p, s, "#B8B4A2", "#8E8A7A", SKIN_W, 0.13); faceshade(p, s)
    p["Head"] += [cyl("hat_brim", 0.3, 0.3, 0.02, (0, 0, s["h"] + 0.0), HEMP, 10), cyl("hat_crown", 0.12, 0.09, 0.14, (0, 0, s["h"] + 0.0), HEMP, 8)]
    for i in range(5): p["Hand.L"].append(cyl(f"coin{i}", 0.035, 0.035, 0.01, (s["hx"] + 0.02 * (i % 2), s["hy"] - 0.12, s["hand"] + 0.04 + 0.012 * i), "#B09468", 8))
    p["Hand.R"] += [box("reach", (0.1, 0.22, 0.04), (-s["hx"], s["hy"] - 0.2, s["hand"] + 0.1), SKIN_W, rot=(0.3, 0, 0))]
    p["Prop"] += [box("hull", (1.5, 4.2, 0.55), (0, 1.9, 0.28), BOAT), box("hull_top", (1.1, 3.8, 0.3), (0, 1.9, 0.68), "#3E3024"), box("keel", (0.14, 3.6, 0.1), (0, 1.9, 0.9), "#34281E"), box("rib0", (1.7, 0.1, 0.1), (0, 0.6, 0.45), "#34281E"), box("rib1", (1.7, 0.1, 0.1), (0, 3.2, 0.45), "#34281E")]     # 뒤집힌 나룻배(바닥이 위로)
    p["Prop"] += [limb(f"thread{i}", (0.1 * (i - 1), 0.1, 0.1), (0.5 * (i - 1), 1.2, 0.6), 0.025, 0.02, "#8FB0B8", 4) for i in range(3)]
    p["Prop"] += [box(f"plank{i}", (0.4, 1.2, 0.04), (-1.2 + i * 0.8, 3.6, 0.05 + 0.2 * (i % 2)), "#5A4636", rot=(0, 0.2 * (i - 1), 0.4 * (i - 1))) for i in range(4)]
    return p
# ───────── B-22 줄에 묶인 일곱 ─────────
SPEC22 = dict(h=1.75, hip=0.82, sh=1.32, neck=1.5, sw=0.32, hand=0.95, hx=0.4, hy=-0.28, prop=0.9)
def b22():
    """줄에 묶인 일곱 1.75m: 가운데 갑판꾼 돌석과 원을 이룬 여섯, 합쳐 일곱 몸이 한 줄에 묶여 있다. 모두 젖은 베잠방이에 맨발, 줄은 끊긴 채 가운데로 모인다."""
    r = random.Random(122); p = P(); s = SPEC22; body(p, s, "#7C7468", "#5E564A", SKIN_W, 0.13); faceshade(p, s)
    p["Head"] += [box("headcloth", (0.3, 0.3, 0.05), (0, 0, s["h"] - 0.04), "#C8C0A8")]
    p["Hand.R"] += [limb("rope_in_hand", (-s["hx"], s["hy"], s["hand"]), (-s["hx"] - 0.9, s["hy"] - 0.3, 0.2), 0.04, 0.035, ROPE, 4)]
    for i in range(6):     # 둘레 여섯 몸: 반경 3m 원, 안쪽을 보고 선 몸통+머리(작은 단순형)
        a = i / 6 * math.tau + 0.3; x, y = math.cos(a) * 3.0, math.sin(a) * 3.0
        p["Prop"] += [cyl(f"sailor{i}", 0.26, 0.18, 1.0, (x, y, 0.0), "#7C7468", 7, rot=(0, 0, a)), sphere(f"shead{i}", 0.13, (x, y, 1.12), SKIN_W, 6, 4), box(f"scloth{i}", (0.28, 0.28, 0.05), (x, y, 1.24), "#C8C0A8"),
                       limb(f"line{i}", (x, y, 0.8), (0, 0, 0.8), 0.03, 0.03, ROPE, 4)]
    for i in range(18): a0, a1 = i / 18 * math.tau, (i + 1) / 18 * math.tau; p["Prop"].append(limb(f"ring{i}", (math.cos(a0) * 3.0, math.sin(a0) * 3.0, 0.78), (math.cos(a1) * 3.0, math.sin(a1) * 3.0, 0.78), 0.03, 0.03, ROPE, 4))     # 일곱을 묶은 줄 고리(속이 빈 원)
    return p
# ───────── B-23 물 밑 매듭 ─────────
SPEC23 = dict(h=4.4, hip=1.6, sh=3.4, neck=3.8, sw=1.3, hand=2.2, hx=2.2, hy=-0.8, prop=2.6)
def b23():
    """물 밑 매듭 4.4m: 실 수천 가닥이 엉킨 둥근 덩어리. 가닥 끝마다 이름 쪽지와 누운 몸의 그림자, 맨 위에 사공의 배가 걸려 있다. 사람 모양이 아니어서 팔 둘은 굵은 실 다발."""
    r = random.Random(123); p = P(); s = SPEC23; TH = ["#6E6A58", "#8A8268", "#4E5A5C", "#9A8C6A"]
    for i in range(46):
        a = r.uniform(0, 6.28); z = r.uniform(0.6, 3.8); d = r.uniform(0.2, 1.5) * (1.0 - abs(z - 2.2) / 3.2 + 0.4)
        a2 = a + r.uniform(1.0, 2.6); z2 = max(0.3, z + r.uniform(-1.2, 1.2)); d2 = r.uniform(0.3, 1.5)
        p["Hips" if z < 1.6 else "Chest"].append(limb(f"thread{i}", (math.cos(a) * d, math.sin(a) * d, z), (math.cos(a2) * d2, math.sin(a2) * d2, z2), r.uniform(0.07, 0.13), r.uniform(0.05, 0.1), TH[i % 4], 5))
    for i in range(14): a = r.uniform(0, 6.28); z = r.uniform(0.8, 3.6); p["Chest"].append(box(f"tag{i}", (0.22, 0.03, 0.32), (math.cos(a) * 1.7, math.sin(a) * 1.7, z), PAPER if i % 3 else "#B09468", rot=(0, 0.2, a + math.pi / 2)))
    p["Head"] += [sphere("core", 0.55, (0, -0.2, s["h"] - 0.9), "#2E3236", 7, 5, (1, 0.7, 1.0)), box("eyeL", (0.08, 0.03, 0.05), (0.2, -0.7, s["h"] - 0.8), mat("#BFE8FF", 0.5)), box("eyeR", (0.08, 0.03, 0.05), (-0.2, -0.7, s["h"] - 0.8), mat("#BFE8FF", 0.5))]
    for sx, n, hn in ((1, "UpperArm.L", "Hand.L"), (-1, "UpperArm.R", "Hand.R")):
        sh_ = (sx * s["sw"], 0, s["sh"]); hd = (sx * s["hx"], s["hy"], s["hand"])
        for k in range(4): p[n].append(limb(f"bund{n[-1]}{k}", (sh_[0] + 0.1 * k, 0, sh_[2] - 0.1 * k), (hd[0] + 0.1 * (k - 1.5), hd[1], hd[2]), 0.14, 0.1, TH[k], 5))
        p[hn].append(sphere("knotfist" + n[-1], 0.38, (hd[0], hd[1], hd[2] - 0.1), "#6E6A58", 6, 4))
    p["Prop"] += [prism("boat", 1.4, 3.6, 0.7, (0.3, 0.6, 4.1), BOAT, rot=(0.15, 0.1, 0.3)), box("oar", (0.08, 2.4, 0.06), (-0.4, 0.6, 4.6), "#5A4636", rot=(0.2, 0, 0.5))]
    for i in range(12): a = i / 12 * math.tau; p["Prop"].append(limb(f"outer{i}", (math.cos(a) * 1.8, math.sin(a) * 1.8, 0.3), (math.cos(a) * 4.5, math.sin(a) * 4.5, 0.05), 0.05, 0.04, "#C8C09A", 4))   # 바깥 실: 밝을수록 바깥
    return p
# ───────── B-24 한 구덩이의 두 진 ─────────
SPEC24 = dict(h=2.4, hip=1.0, sh=1.7, neck=1.9, sw=0.48, hand=1.2, hx=0.58, hy=-0.34, prop=1.2)
def _pennant(p, bone, x, y, z0, flag, rot=0.0):
    """깃대와 깃발(글자 없음). 이쪽은 번호(획 상자 여러 줄), 건너편은 소매 속 수놓은 이름 자리(작은 헝겊)로 구분한다."""
    p[bone] += [cyl(f"pole{x:.0f}{y:.0f}", 0.05, 0.04, 3.0, (x, y, 0.0), "#5A4430", 6), box(f"flag{x:.0f}{y:.0f}", (0.8, 0.03, 0.5), (x + 0.45, y, 2.7), flag, rot=(0, 0, rot))]
def b24():
    """한 구덩이의 두 진 2.4m: 가운데 이쪽 기수(번호 군기, 쇠 갑옷)와 건너편 기수(Prop, 헝겊 군기), 양쪽 뒤로 두 진의 병사 열둘씩(반투명)."""
    r = random.Random(124); p = P(); s = SPEC24; body(p, s, "#4E5260", "#3A3E4C", SKIN_W, 0.15, sleeve_r=(0.12, 0.1)); faceshade(p, s, 0.15)
    p["Head"] += [sphere("helm", 0.2, (0, 0, s["h"] - 0.1), "#5A5E6A", 8, 5, (1, 1, 0.85)), cyl("helm_brim", 0.27, 0.27, 0.03, (0, 0, s["h"] - 0.2), "#4A4E5C", 10)]
    p["Chest"] += [box("breast", (0.5, 0.1, 0.4), (0, -0.25, s["sh"] - 0.4), "#6A6E7C")]
    _pennant(p, "Hand.R", -s["hx"], s["hy"], 0.0, "#7A2A2A")
    for i in range(6): p["Hand.R"].append(box(f"num{i}", (0.06, 0.012, 0.12), (-s["hx"] + 0.2 + 0.1 * (i % 3), s["hy"] - 0.02, 2.8 - 0.14 * (i // 3)), PAPER))     # 번호 획 상자
    gm = mat_alpha("#9AA0A8", 0.3, 0.5)
    for i in range(12):
        row, col = divmod(i, 4); x = -1.8 + col * 1.2; y = 1.2 + row * 1.0
        p["Prop"] += [cyl(f"sold{i}", 0.2, 0.14, 0.9, (x, y, 0.0), gm, 6), sphere(f"sh{i}", 0.11, (x, y, 1.02), gm, 5, 4), cyl(f"spear{i}", 0.015, 0.015, 1.7, (x + 0.18, y, 0.0), gm, 4)]
    # 건너편: 기수 + 병사 (보스 맞은편 6m, 정면 보기)
    fy = 6.5
    p["Prop"] += [cyl("rival_body", 0.3, 0.2, 1.3, (0, fy, 0.0), "#5A4A3A", 8), sphere("rival_head", 0.17, (0, fy, 1.5), SKIN_W, 6, 5), sphere("rival_helm", 0.2, (0, fy, 1.58), "#6A5A4A", 7, 4, (1, 1, 0.7)), cyl("rival_pole", 0.05, 0.04, 3.0, (0.4, fy, 0.0), "#5A4430", 6), box("rival_flag", (0.7, 0.03, 0.5), (0.8, fy, 2.7), "#C8BFA0")]
    p["Prop"] += [box(f"stitch{i}", (0.08, 0.012, 0.03), (0.65 + 0.1 * i, fy - 0.02, 2.7 + 0.06 * (i % 2)), "#8A3A3A") for i in range(5)]
    for i in range(12):
        row, col = divmod(i, 4); x = -1.8 + col * 1.2; y = fy + 1.2 + row * 1.0
        p["Prop"] += [cyl(f"rsold{i}", 0.2, 0.14, 0.9, (x, y, 0.0), gm, 6), sphere(f"rsh{i}", 0.11, (x, y, 1.02), gm, 5, 4)]
    return p
# ───────── B-25 반장 칠성의 백 ─────────
SPEC25 = dict(h=1.8, hip=0.8, sh=1.3, neck=1.46, sw=0.34, hand=0.95, hx=0.42, hy=-0.28, prop=0.6)
def b25():
    """반장 칠성의 백 1.8m: 흙먼지로 회갈색이 된 베옷, 등불 모자(불은 꺼졌고 심지만 붉게 남음), 양손에 곡괭이. 둘레에 광부 열둘이 누웠거나 기대었고, 버팀목 셋이 선 자리(Prop)가 있다."""
    r = random.Random(125); p = P(); s = SPEC25; body(p, s, "#6A5E50", "#4E4438", "#8A7C68", 0.14); faceshade(p, s, 0.14)
    p["Head"] += [cyl("hat_brim", 0.26, 0.26, 0.03, (0, 0, s["h"] - 0.04), "#4A3A2E", 10), cyl("hat_crown", 0.15, 0.13, 0.14, (0, 0, s["h"] - 0.02), "#4A3A2E", 8), box("lamp", (0.08, 0.06, 0.08), (0, -0.16, s["h"] + 0.02), "#6A6E7C"), box("wick", (0.03, 0.03, 0.03), (0, -0.2, s["h"] + 0.02), mat("#E04A3A", 0.9))]
    for hn, sx in (("Hand.R", -1), ("Hand.L", 1)): p[hn] += [cyl(f"pickaxe{sx}", 0.04, 0.04, 1.1, (sx * s["hx"], s["hy"] - 0.05, s["hand"] - 0.4), "#5A4430", 6, rot=(0.3, 0, 0)), box(f"pickhead{sx}", (0.5, 0.06, 0.08), (sx * s["hx"], s["hy"] - 0.3, s["hand"] + 0.4), "#6A6E7C", rot=(0.3, 0, 0))]
    for i in range(12):     # 광부 열둘: 길게 누운 몸(작은 상자 몸통+머리)
        a = i / 12 * math.tau; x, y = math.cos(a) * 3.2, math.sin(a) * 3.2
        p["Prop"] += [box(f"miner{i}", (0.4, 1.3, 0.22), (x, y, 0.11), "#5E5444", rot=(0, 0, a + math.pi / 2)), sphere(f"mhead{i}", 0.12, (x - math.cos(a) * 0.0 + math.sin(a) * 0.5, y - math.cos(a) * 0.5, 0.18), "#7C705E", 5, 4)]
    for i in range(3):      # 버팀목 셋
        a = i / 3 * math.tau + 0.5; x, y = math.cos(a) * 2.0, math.sin(a) * 2.0
        p["Prop"] += [cyl(f"prop{i}", 0.14, 0.12, 2.6, (x, y, 0.0), "#6A4E34", 7), box(f"cap{i}", (0.8, 0.16, 0.1), (x, y, 2.6), "#5A4430", rot=(0, 0, a))]
    return p
# ───────── B-26 역병 마흔과 마흔 ─────────
SPEC26 = dict(h=3.0, hip=1.0, sh=2.3, neck=2.6, sw=0.9, hand=1.5, hx=1.5, hy=-0.6, prop=1.3)
def b26():
    """두 겹 구덩이 3.0m: 위 겹(잿빛 몸 덩이)과 아래 겹(더 짙은 몸 덩이)이 흰 석회 띠를 사이에 두고 엉긴 덩어리. 팔 둘은 두 겹에서 각각 뻗은 것. 석회 띠가 몸을 가로지른다."""
    r = random.Random(126); p = P(); s = SPEC26; UP = ["#8E8A80", "#7C786C", "#9A968A"]; LOW = ["#4E4A42", "#3E3A34", "#5A564C"]
    for i in range(8): a = r.uniform(0, 6.28); d = r.uniform(0.2, 1.0); p["Hips"].append(sphere(f"low{i}", r.uniform(0.5, 0.85), (math.cos(a) * d, math.sin(a) * d, 0.6 + r.uniform(0, 0.8)), LOW[i % 3], 7, 5, (1, 1, 1.1)))
    for i in range(9): a = r.uniform(0, 6.28); d = r.uniform(0.2, 1.0); p["Chest"].append(sphere(f"up{i}", r.uniform(0.5, 0.85), (math.cos(a) * d, math.sin(a) * d, 1.7 + r.uniform(0, 1.0)), UP[i % 3], 7, 5, (1, 1, 1.1)))
    p["Hips"].append(cyl("lime_band_low", 1.5, 1.5, 0.12, (0, 0, 1.15), LIME, 14)); p["Chest"].append(cyl("lime_band_up", 1.4, 1.4, 0.1, (0, 0, 2.15), LIME, 14))
    for i in range(10): a = r.uniform(0, 6.28); z = r.uniform(0.6, 2.8); d = 1.0 + 0.1 * math.sin(z * 2); p["Chest"].append(sphere(f"nape{i}", 0.15, (math.cos(a) * d, math.sin(a) * d, z), "#8C8A80" if z > 1.6 else "#5A564C", 6, 4, (1, 1, 1.1)))
    p["Head"] += [sphere("crown", 0.42, (0, 0.1, s["h"] - 0.3), "#8E8A80", 7, 5), box("eyeL", (0.05, 0.03, 0.03), (0.13, -0.38, s["h"] - 0.26), mat("#D8D4C6", 0.4)), box("eyeR", (0.05, 0.03, 0.03), (-0.13, -0.38, s["h"] - 0.26), mat("#D8D4C6", 0.4))]
    for sx, n, hn, C in ((1, "UpperArm.L", "Hand.L", UP[0]), (-1, "UpperArm.R", "Hand.R", LOW[0])):
        sh_ = (sx * s["sw"], 0, s["sh"]); hd = (sx * s["hx"], s["hy"], s["hand"]); p[n].append(limb("arm" + n[-1], sh_, hd, 0.26, 0.2, C, 6)); p[hn].append(sphere("fist" + n[-1], 0.28, (hd[0], hd[1], hd[2] - 0.1), C, 6, 4))
    for i in range(10): a = i / 10 * math.tau; p["Prop"].append(box(f"stone{i}", (0.3, 0.06, 0.22), (math.cos(a) * 2.6, math.sin(a) * 2.6, 0.12), "#B8B4A4", rot=(0, 0, a)))      # 빈 돌
    return p
# ───────── B-27 마지막 줄 — 서생 이명의 백 ─────────
SPEC27 = dict(h=1.78, hip=0.82, sh=1.34, neck=1.5, sw=0.3, hand=0.95, hx=0.38, hy=-0.28, prop=0.4)
def b27():
    """서생 이명의 백 1.78m: 먹 얼룩과 겨울 서리가 낀 낡은 서생 두루마기, 굽은 어깨, 상투. 오른손에 붓을 쥐고 떤다. 발치(Prop)에는 바닥을 덮은 글씨의 획 모양이 번져 있다(읽히는 글자는 없다)."""
    r = random.Random(127); p = P(); s = SPEC27; body(p, s, "#5A5A62", "#44444C", "#8A8478", 0.13); faceshade(p, s)
    p["Head"] += [sphere("topknot", 0.07, (0, 0.02, s["h"] + 0.02), INK, 6, 4)]
    for i in range(7): p["Chest"].append(box(f"inkstain{i}", (r.uniform(.08, .2), 0.012, r.uniform(.1, .3)), (r.uniform(-.2, .2), -0.25, r.uniform(0.8, 1.3)), "#14121A", rot=(0, 0, r.uniform(-.5, .5))))
    for i in range(10): p["Chest"].append(sphere(f"frost{i}", 0.04, (r.uniform(-.25, .25), -0.2, r.uniform(0.9, 1.4)), "#DCE6EA", 4, 3))
    hx, hy = -s["hx"], s["hy"]; p["Hand.R"] += [cyl("brush", 0.02, 0.02, 0.8, (hx, hy - 0.15, s["hand"] + 0.1), "#3A2C26", 5, rot=(0.9, 0, 0)), sphere("brush_tip", 0.04, (hx, hy - 0.5, s["hand"] + 0.4), INK, 5, 4, (1, 1, 2))]
    p["Hand.L"].append(box("sheet", (0.2, 0.01, 0.28), (s["hx"], s["hy"] - 0.1, s["hand"] + 0.05), PAPER))
    for i in range(40):    # 바닥 글씨: 획 모양 상자(글자로 읽히지 않게 무작위 방향·길이)
        a = r.uniform(0, 6.28); d = r.uniform(0.6, 5.0); p["Prop"].append(box(f"stroke{i}", (r.uniform(0.15, 0.5), 0.05, 0.01), (math.cos(a) * d, math.sin(a) * d, 0.012), "#1E1C24", rot=(0, 0, r.uniform(0, 3.14))))
    return p
# ───────── B-28 벼루 밑의 손 ─────────
SPEC28 = dict(h=2.15, hip=0.95, sh=1.6, neck=1.78, sw=0.45, hand=1.2, hx=0.5, hy=-0.32, prop=4.4)
def b28():
    """벼루지기의 백 2.15m: 먹 앙금에 반쯤 잠긴 몸. 온몸이 검은 진흙, 손만 희게 씻겨 있고 먹 막대를 쥐고 둥글게 돌린다. 머리 위(Prop)에 천장처럼 돌아가는 벼루 바닥(반경 4m, 먹 홈 소용돌이)."""
    r = random.Random(128); p = P(); s = SPEC28; body(p, s, "#2A2830", "#1E1C24", "#2E2C34", 0.15, sleeve_r=(0.11, 0.09)); faceshade(p, s, 0.15)
    p["Hips"].append(cyl("silt_skirt", 0.7, 0.9, 0.25, (0, 0, 0.0), "#14121A", 10))
    for hn, sx in (("Hand.L", 1), ("Hand.R", -1)): p[hn] += [sphere(f"white_hand{sx}", 0.09, (sx * s["hx"], s["hy"] - 0.05, s["hand"] - 0.02), PAPER, 6, 4), box(f"inkstick{sx}", (0.05, 0.05, 0.4), (sx * s["hx"], s["hy"] - 0.1, s["hand"] + 0.12), "#14121A", rot=(0.4, 0, 0))]
    for i in range(18): a0, a1 = i / 18 * math.tau, (i + 1) / 18 * math.tau; p["Prop"] += [limb(f"rim{i}", (math.cos(a0) * 4.0, math.sin(a0) * 4.0, 4.4), (math.cos(a1) * 4.0, math.sin(a1) * 4.0, 4.4), 0.18, 0.18, "#58554F", 5), limb(f"groove{i}", (math.cos(a0) * 2.4, math.sin(a0) * 2.4, 4.4), (math.cos(a1) * 2.4, math.sin(a1) * 2.4, 4.4), 0.08, 0.08, INK, 4)]
    p["Prop"].append(sphere("hub", 0.5, (0, 0, 4.4), "#58554F", 6, 4))
    for i in range(6): a = i / 6 * math.tau; p["Prop"].append(limb(f"spoke{i}", (0, 0, 4.4), (math.cos(a) * 4.0, math.sin(a) * 4.0, 4.4), 0.1, 0.1, "#3A3842", 4))     # 도는 것이 보이도록 살만 둔 벼루 바닥(쿼터뷰 가림 방지: 속이 빈 틀)
    p["Prop"] += [limb(f"drip{i}", (math.cos(i * 2.1) * 2.0, math.sin(i * 2.1) * 2.0, 4.3), (math.cos(i * 2.1) * 2.0, math.sin(i * 2.1) * 2.0, 3.3), 0.04, 0.025, INK, 4) for i in range(5)]
    return p
# ───────── B-29 백 년의 사잣밥 ─────────
SPEC29 = dict(h=1.35, hip=0.55, sh=1.0, neck=1.13, sw=0.26, hand=0.7, hx=0.32, hy=-0.28, prop=0.5)
def b29():
    """사잣밥 할미의 백 1.35m: 허리 굽은 작은 할미. 백 년 묵어 회백색으로 마른 흰 치마저고리, 쪽머리. 두 손은 밥상 쪽으로 모아 내밀었다. 앞(Prop)에 사잣밥 세 그릇·짚신 세 켤레·엽전 세 닢이 놓인 낮은 상."""
    r = random.Random(129); p = P(); s = SPEC29; body(p, s, "#C8C4B2", "#A8A494", "#9A9282", 0.12, skirt_r=(0.3, 0.26, 0.22), sleeve_r=(0.07, 0.06)); faceshade(p, s, 0.12)
    p["Head"] += [sphere("bun", 0.07, (0, 0.1, s["h"] - 0.12), "#D8D4C6", 6, 4), box("pin", (0.2, 0.02, 0.02), (0, 0.1, s["h"] - 0.12), "#B09468")]
    p["Chest"] += [box("stoop", (0.3, 0.26, 0.26), (0, 0.12, s["sh"] - 0.1), "#A8A494", rot=(0.4, 0, 0))]
    for sx in (1, -1): p["Hand.L" if sx > 0 else "Hand.R"].append(box(f"offer{sx}", (0.1, 0.2, 0.04), (sx * s["hx"] * 0.7, s["hy"] - 0.15, s["hand"] + 0.05), "#9A9282", rot=(0.2, 0, 0)))
    p["Prop"] += [box("table", (1.4, 0.7, 0.04), (0, -1.0, 0.4), "#5A4636")] + [cyl(f"leg{i}", 0.04, 0.04, 0.4, (-0.6 + 1.2 * (i % 2), -1.25 + 0.5 * (i // 2), 0.0), "#4A3A2E", 5) for i in range(4)]
    for i in range(3):
        x = -0.45 + i * 0.45; p["Prop"] += [cyl(f"bowl{i}", 0.12, 0.08, 0.1, (x, -0.95, 0.44), "#E8E4D8", 8), sphere(f"rice{i}", 0.1, (x, -0.95, 0.52), "#F4F0E4", 6, 4, (1, 1, 0.7)),
                                           box(f"sandal{i}", (0.1, 0.26, 0.03), (x, -1.2, 0.44), "#A89868"), cyl(f"coinp{i}", 0.04, 0.04, 0.01, (x, -0.72, 0.445), "#B09468", 8)]
    return p
# ───────── B-30 첫 우물 — 어미의 백 ─────────
SPEC30 = dict(h=1.6, hip=0.72, sh=1.2, neck=1.36, sw=0.28, hand=0.8, hx=0.34, hy=-0.28, prop=3.0)
def b30():
    """어미의 백 1.6m: 물에 젖어 달라붙은 긴 머리가 얼굴을 덮고, 젖은 베치마. 한 손에 작은 신발 한 짝. 위(Prop)에서 새끼줄이 우물 위로부터 내려와 허리를 감는다(첫 차사의 백이 당기는 줄)."""
    r = random.Random(130); p = P(); s = SPEC30; body(p, s, "#8E8E84", "#6A6A62", SKIN_W, 0.12, skirt_r=(0.34, 0.3, 0.26))
    p["Head"] += [sphere("wethair", 0.15, (0, 0.02, s["h"] - 0.17), INK, 7, 5, (1.05, 1.05, 1.2))] + [limb(f"lock{i}", (-0.1 + i * 0.05, -0.08, s["h"] - 0.2), (-0.12 + i * 0.06, -0.14, s["h"] - 0.7), 0.025, 0.012, INK, 4) for i in range(5)]
    p["Hand.L"] += [box("tiny_shoe", (0.06, 0.12, 0.04), (s["hx"], s["hy"] - 0.12, s["hand"] + 0.02), "#C8B88A"), box("shoe_toe", (0.05, 0.04, 0.03), (s["hx"], s["hy"] - 0.2, s["hand"] + 0.03), "#C8B88A")]
    p["Hips"].append(cyl("rope_coil", 0.32, 0.3, 0.06, (0, 0, s["hip"] + 0.05), ROPE, 10))
    p["Prop"] += [limb("saekkijul", (0, 0, 0.85), (0.2, 0.1, 6.2), 0.05, 0.05, ROPE, 5), box("rope_knot", (0.14, 0.14, 0.12), (0.05, 0.02, 1.9), ROPE), cyl("bucket", 0.16, 0.2, 0.22, (0.2, 0.1, 5.6), "#5A4636", 8)]
    for i in range(3): p["Prop"].append(limb(f"wet{i}", (-0.4 + i * 0.4, 0.5, 0.0), (-0.4 + i * 0.4, 0.5, 0.35), 0.05, 0.02, "#7FA0B0", 4))
    return p
# ───────── B-31 나의 백 ─────────
SPEC31 = dict(h=1.85, hip=0.88, sh=1.42, neck=1.6, sw=0.34, hand=1.0, hx=0.42, hy=-0.28, prop=1.2)
def b31():
    """나의 백 1.85m: 큰물 밤의 젊은이. 물에 불어 어두운 살갗, 베잠방이, 오른손에 물속에서도 꺼지지 않는 횃불(발광), 왼손은 앞으로 뻗었고 손목에 내 사슬 끝이 감겼다. 둘레에 일곱의 빛(작은 발광구)과 떠 있는 보릿단."""
    r = random.Random(131); p = P(); s = SPEC31; body(p, s, "#6E665A", "#524C42", "#7A7062", 0.13, skirt_r=(0.28, 0.25, 0.22)); faceshade(p, s)
    p["Head"] += [box("headband", (0.28, 0.28, 0.03), (0, 0, s["h"] - 0.1), "#C8C0A8")]
    hx, hy = -s["hx"], s["hy"]
    p["Hand.R"] += [cyl("torch", 0.045, 0.05, 0.9, (hx, hy - 0.1, s["hand"] - 0.1), "#4A3A2E", 6, rot=(0.15, 0, 0)), sphere("flame", 0.13, (hx, hy - 0.22, s["hand"] + 0.5), mat("#FFB347", 2.2), 6, 5, (1, 1, 1.6))]
    p["Hand.L"] += [box("reach", (0.1, 0.24, 0.04), (s["hx"], s["hy"] - 0.2, s["hand"] + 0.12), "#7A7062", rot=(0.3, 0, 0))] + [box(f"wlink{i}", (0.07, 0.025, 0.1), (s["hx"], s["hy"] - 0.02 + 0.0, s["hand"] - 0.06 - 0.08 * i), "iron", rot=(0, (i % 2) * 1.5708, 0)) for i in range(5)]
    for i in range(7): a = i / 7 * math.tau; p["Prop"].append(sphere(f"light{i}", 0.09, (math.cos(a) * 2.2, math.sin(a) * 2.2, 1.6 + 0.2 * (i % 2)), mat("#FFE9A8", 1.6), 5, 4))
    p["Prop"] += [cyl("child_body", 0.12, 0.09, 0.5, (1.4, -1.5, 0.9), "#6E665A", 6, rot=(1.5, 0, 0.4)), sphere("child_head", 0.08, (1.4, -1.85, 0.95), "#7A7062", 5, 4), limb("child_thread", (1.4, -1.5, 0.95), (0.4, -0.3, 1.0), 0.02, 0.02, "#8FB0B8", 4)]   # 실에 감긴 작은 몸(여덟째, 개똥이의 백)
    p["Prop"] += [cyl("sheaf", 0.14, 0.1, 0.5, (-1.0, -1.6, 0.9), "#B8A468", 7, rot=(0.2, 0, 0.3)), box("sheaf_band", (0.3, 0.3, 0.04), (-1.0, -1.6, 0.9), ROPE, rot=(0.2, 0, 0.3))]
    return p
BOSS = [("boss_b21_yun", b21, SPEC21), ("boss_b22_seven", b22, SPEC22), ("boss_b23_knot", b23, SPEC23), ("boss_b24_two_ranks", b24, SPEC24), ("boss_b25_chilseong", b25, SPEC25), ("boss_b26_two_layers", b26, SPEC26),
        ("boss_b27_scribe", b27, SPEC27), ("boss_b28_inkhand", b28, SPEC28), ("boss_b29_grandma", b29, SPEC29), ("boss_b30_mother", b30, SPEC30), ("boss_b31_myself", b31, SPEC31)]
SIG = {"boss_b21_yun": dict(wind=dict(R=-60, L=-120, lean=-8, tw=-8, nod=-4), atk=dict(R=-20, L=-20, lean=20, tw=8, nod=8), kneel_drop=-0.3),
       "boss_b22_seven": dict(wind=dict(R=-150, L=-40, lean=-10, tw=-14, nod=-6), atk=dict(R=-30, L=-30, lean=22, tw=14, nod=10), kneel_drop=-0.45),
       "boss_b23_knot": dict(wind=dict(R=-140, L=-140, lean=-8, tw=0, nod=-4), atk=dict(R=-20, L=-20, lean=14, tw=0, nod=6), kneel_drop=-0.6),
       "boss_b24_two_ranks": dict(wind=dict(R=-150, L=-30, lean=-14, tw=-10, nod=-8), atk=dict(R=-20, L=-30, lean=24, tw=10, nod=12), kneel_drop=-0.5),
       "boss_b25_chilseong": dict(wind=dict(R=-140, L=-140, lean=-12, tw=0, nod=-6), atk=dict(R=-20, L=-20, lean=26, tw=0, nod=12), kneel_drop=-0.4),
       "boss_b26_two_layers": dict(wind=dict(R=-140, L=-140, lean=-8, tw=0, nod=-6), atk=dict(R=-20, L=-20, lean=18, tw=0, nod=8), kneel_drop=-0.6),
       "boss_b27_scribe": dict(wind=dict(R=-120, L=-30, lean=-8, tw=-12, nod=-6), atk=dict(R=-30, L=-30, lean=20, tw=12, nod=10), kneel_drop=-0.4),
       "boss_b28_inkhand": dict(wind=dict(R=-100, L=-100, lean=-10, tw=0, nod=-6), atk=dict(R=-25, L=-25, lean=22, tw=0, nod=10), kneel_drop=-0.5),
       "boss_b29_grandma": dict(wind=dict(R=-80, L=-80, lean=-6, tw=0, nod=-4), atk=dict(R=-30, L=-30, lean=16, tw=0, nod=8), kneel_drop=-0.2),
       "boss_b30_mother": dict(wind=dict(R=-90, L=-60, lean=-8, tw=-6, nod=-4), atk=dict(R=-25, L=-25, lean=18, tw=6, nod=8), kneel_drop=-0.35),
       "boss_b31_myself": dict(wind=dict(R=-130, L=-40, lean=-10, tw=-14, nod=-6), atk=dict(R=-20, L=-30, lean=24, tw=14, nod=10), kneel_drop=-0.4)}
B2.SIG.update(SIG)
if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    res = [B2.build(*b, sheets="--sheets" in sys.argv) for b in BOSS if not only or b[0] in only]
    for r in res: print(r["name"], r["tris"], r["size_m"], r["verify"]["joints"], len(r["verify"]["animations"]))
    if not only:
        json.dump({"fps": anim.FPS, "bosses": res}, open(os.path.join(OUT, "boss", "_s3_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        for i, (name, fn, spec) in enumerate(BOSS):
            p = fn(); parts = []
            for bone, objs in p.items(): parts += to_group(objs, bone)
            o = join(name, parts); o.location = ((i % 4 - 1.5) * 10.0, -(i // 4) * 11.0, 0)
        setup_render(34, (0, -9, 2.0), size=(1800, 1000), ground_size=80); render(os.path.join(OUT, "previews", "bosses_s3_50deg.png"))
