"""B-02 월화·B-03 서 의원 보스 본체: 모델(뼈대 포함)과 동작. 실행: python3 boss_b02_b03.py [--sheets]
왜: 서사 컷신(cutscenes_b02/b03.json)과 기획 보스표(boss_s1.json)의 장면·기술을 몸이 실제로 할 수 있어야 코드팀이 컷신을 부를 수 있다.
몸 모양은 bosses.py(6원형)의 월화·서 의원을 바탕으로 컷신에 나온 소품을 더했다: 월화=오방 쾌자·오른손 살 부러진 부채·왼손 방울,
서 의원=기운 탕건·등짐 약장(맨 아랫단 왼쪽 서랍이 밀려 나옴, 청록 약점판)·몸 앞 장부. 뼈 이름은 6원형 규칙(Root/Hips/Chest/Head/UpperArm.L·R/Prop)을 그대로 두고
Hand.L·R(손·소품), 서 의원만 Case(약장)·Drawer(서랍)를 더했다. 동작은 60fps, 이름·길이·event 프레임은 아래 clips() 참고.
팔 방향 규칙(눈으로 확인한 부호): 옆으로 벌린 팔 앞으로=왼팔 rz 음수/오른팔 rz 양수, 위로=왼팔 ry 음수/오른팔 ry 양수. 몸통 rx 양수=앞으로 숙임, rz 양수=왼쪽으로 돌림."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import to_group, rig
import bosses, anim
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
RED = "#A33A3A"; TEAL = "#6FD6C0"
OBANG = ["#3E64B0", "#E8C15A", "hanji", RED, "#2A2A38"]

def drop(objs):
    """쓰지 않기로 한 조각은 장면에서 지운다(안 지우면 미리보기에 남고 이름만 겹친다)."""
    for o in objs: bpy.data.objects.remove(o, do_unlink=True)

def bones_wolhwa():
    return [("Root", None, (0, 0, 0), (0, 0, 0.2)), ("Hips", "Root", (0, 0, 0.95), (0, 0, 1.05)), ("Chest", "Hips", (0, 0, 1.05), (0, 0, 1.47)), ("Head", "Chest", (0, 0, 1.47), (0, 0, 2.0)),
            ("UpperArm.L", "Chest", (0.3, 0, 1.4), (1.0, -0.17, 1.1)), ("Hand.L", "UpperArm.L", (1.0, -0.17, 1.1), (1.05, -0.2, 1.0)),
            ("UpperArm.R", "Chest", (-0.3, 0, 1.4), (-1.0, -0.17, 1.1)), ("Hand.R", "UpperArm.R", (-1.0, -0.17, 1.1), (-1.05, -0.2, 1.0)), ("Prop", "Root", (0, 0, 1.05), (0, 0, 1.26))]

def wolhwa():
    """월화: bosses.wolhwa 바탕 + 오방 쾌자, 왼손(캐릭터 왼쪽=+X)에 방울, 오른손에 살 부러진 부채. 손은 Hand 뼈로 분리."""
    p, h = bosses.wolhwa()
    for sx, side in ((1, "L"), (-1, "R")):
        keep = [o for o in p[f"UpperArm.{side}"] if o.name.startswith("sleeve")]; drop([o for o in p[f"UpperArm.{side}"] if o not in keep]); p[f"UpperArm.{side}"] = keep
    hands = {"L": [], "R": []}
    for sx, side in ((1, "L"), (-1, "R")): hands[side].append(sphere("hand", 0.075, (sx * 1.0, -0.17, 1.1), "skin", 5, 4))
    # 쾌자(소매 없는 긴 조끼): 앞가슴에서 허리까지 오방색 줄 네 개(흰색은 무복 자체)
    p["Chest"] += [box(f"kwaeja{i}", (0.09, 0.03, 0.62), (-0.18 + i * 0.12, -0.265, 1.2), c) for i, c in enumerate(OBANG[:4] + [OBANG[0]])]
    p["Hips"] += [box(f"kwaejaHem{i}", (0.1, 0.03, 0.5), (-0.22 + i * 0.14, -0.4, 0.75), OBANG[i % 5]) for i in range(4)]
    # 왼손 방울(칠성방울 8개): 손바닥 위로 들어 올린 손잡이, 위쪽 바퀴에 놋쇠 방울
    hx, hy, hz = 1.0, -0.2, 1.1
    hands["L"] += [cyl("bHandle", 0.03, 0.025, 0.28, (hx, hy, hz - 0.1), "wood_dark", 6), cyl("bHub", 0.07, 0.07, 0.06, (hx, hy, hz + 0.18), "gold", 8)]
    for i in range(8):
        a = i / 8 * math.tau; x, y = hx + 0.15 * math.cos(a), hy + 0.15 * math.sin(a)
        hands["L"] += [sphere(f"bell{i}", 0.055, (x, y, hz + 0.18), "gold", 6, 4), box(f"bArm{i}", (0.15, 0.015, 0.015), ((hx + x) / 2, (hy + y) / 2, hz + 0.18), "gold", rot=(0, 0, a))]
    # 오른손 살 부러진 부채(살 9개 중 둘 빠지고 하나 꺾임)
    fx, fy, fz = -1.0, -0.22, 1.1
    hands["R"] += [cyl("fHandle", 0.03, 0.025, 0.2, (fx, fy, fz - 0.05), "wood_dark", 6)]
    for i in range(9):
        if i in (5, 6): continue
        a = math.radians(-64 + i * 16); ln = 0.25 if i == 3 else 0.52
        hands["R"].append(box(f"rib{i}", (0.1, 0.015, ln), (fx + math.sin(a) * ln / 2, fy, fz + 0.15 + math.cos(a) * ln / 2), OBANG[i % 5], rot=(0, a, 0)))
    p["Hand.L"] = hands["L"]; p["Hand.R"] = hands["R"]
    return p, h

def bones_seo():
    return [("Root", None, (0, 0, 0), (0, 0, 0.2)), ("Hips", "Root", (0, 0, 0.9), (0, 0, 1.0)), ("Chest", "Hips", (0, 0, 1.0), (0, 0, 1.4)), ("Head", "Chest", (0, 0, 1.4), (0, 0, 1.9)),
            ("UpperArm.L", "Chest", (0.22, 0, 1.4), (0.35, -0.5, 1.2)), ("Hand.L", "UpperArm.L", (0.35, -0.5, 1.2), (0.35, -0.6, 1.15)),
            ("UpperArm.R", "Chest", (-0.22, 0, 1.4), (-0.35, -0.5, 1.2)), ("Hand.R", "UpperArm.R", (-0.35, -0.5, 1.2), (-0.35, -0.6, 1.15)),
            ("Prop", "Root", (0, 0, 1.0), (0, 0, 1.2)), ("Case", "Chest", (0, 0.45, 1.3), (0, 0.45, 1.8)), ("Drawer", "Case", (0.2, 0.7, 1.0), (0.2, 0.9, 1.0))]

def seo():
    """서 의원: bosses.seo 바탕. 갓 대신 기운 탕건, 마른 몸, 등에 약장(석 단 두 칸, 서랍 6개)과 붉은 띠, 손은 Hand 뼈. 약장 서랍은 뒤(+Y)를 본다."""
    p, h = bosses.seo()
    # 장부는 몸을 가리지 않게 작게 다시 만든다(원래 0.9×1.1m가 정면 카메라에서 몸 전체를 덮었다). 책등은 주황 빨강 대신 포도주색
    drop(p["Prop"]); p["Prop"] = [box("book", (0.7, 0.1, 0.8), (0, -0.62, 1.1), "hanji", rot=(0.2, 0, 0)), box("spine", (0.08, 0.14, 0.84), (-0.36, -0.62, 1.1), RED), box("line1", (0.46, 0.02, 0.05), (0.04, -0.68, 1.3), "ink"), box("line2", (0.46, 0.02, 0.05), (0.04, -0.68, 1.1), "ink"), box("line3", (0.38, 0.02, 0.05), (0.0, -0.68, 0.9), "ink")] + \
                [box(f"strip{i}", (0.14, 0.02, 0.5), (-0.5 + i * 0.33, -0.78, 0.5 + (i % 2) * 0.12), "hanji", rot=(0, 0.1 * (i - 1.5), 0)) for i in range(4)]
    keep = [o for o in p["Head"] if o.name not in ("brim", "crown")]; drop([o for o in p["Head"] if o not in keep]); p["Head"] = keep
    for o in [cyl("tgBand", 0.15, 0.15, 0.06, (0, 0, 1.72), "hat", 10, rot=(0.0, 0.14, 0)), cyl("tgLow", 0.14, 0.12, 0.12, (0, 0, 1.78), "hat", 10, rot=(0, 0.14, 0)), cyl("tgUp", 0.095, 0.075, 0.1, (0.02, 0, 1.9), "iron", 8, rot=(0, 0.14, 0))]: p["Head"].append(o)
    for sx, side in ((1, "L"), (-1, "R")):
        keep = [o for o in p[f"UpperArm.{side}"] if o.name.startswith("arm")]; drop([o for o in p[f"UpperArm.{side}"] if o not in keep]); p[f"UpperArm.{side}"] = keep
        p[f"Hand.{side}"] = [sphere("hand", 0.075, (sx * 0.35, -0.55, 1.17), "old_skin", 5, 4)]
    p["Hand.R"] += [box("inkStain", (0.1, 0.05, 0.05), (-0.35, -0.55, 1.17), "#5A4630")]   # 손끝이 먹과 약물로 갈색
    # 약장: 폭 0.75·깊이 0.42·높이 1.05, 몸 뒤에 지고 서랍 면이 +Y를 본다
    W, D, H = 0.75, 0.42, 1.05; cx, cy, cz0 = 0.0, 0.5, 0.8
    case = [box("back", (W, 0.04, H), (cx, cy - D / 2 + 0.02, cz0 + H / 2), "wood_dark"), box("sideL", (0.04, D, H), (cx - W / 2 + 0.02, cy, cz0 + H / 2), "wood_dark"), box("sideR", (0.04, D, H), (cx + W / 2 - 0.02, cy, cz0 + H / 2), "wood_dark"),
            box("top", (W, D, 0.04), (cx, cy, cz0 + H), "wood_dark"), box("bottom", (W, D, 0.04), (cx, cy, cz0), "wood_dark"), box("mid", (0.04, D, H), (cx, cy, cz0 + H / 2), "wood_dark")]
    dh = (H - 0.08) / 3
    for r in range(3):
        for c in range(2):
            if r == 0 and c == 0: continue
            x = cx + (1 if c == 0 else -1) * (W / 4)
            case += [box(f"dr{r}{c}", (W / 2 - 0.05, 0.04, dh - 0.04), (x, cy + D / 2 - 0.02, cz0 + 0.06 + dh * (r + 0.5)), "wood"), box(f"kn{r}{c}", (0.05, 0.04, 0.05), (x, cy + D / 2 + 0.02, cz0 + 0.06 + dh * (r + 0.5)), "gold")]
    case += [box("bandMid", (W + 0.05, D + 0.05, 0.06), (cx, cy, cz0 + 0.55), RED)]
    p["Case"] = case
    dx = cx + W / 4; dz = cz0 + 0.06 + dh * 0.5   # 맨 아랫단 왼쪽(캐릭터 왼쪽=+X) 서랍
    drw = [box("dFront", (W / 2 - 0.05, 0.04, dh - 0.04), (dx, cy + D / 2 - 0.02, dz), "wood"), box("dKnob", (0.05, 0.04, 0.05), (dx, cy + D / 2 + 0.02, dz), "gold"), box("dBox", (W / 2 - 0.1, D - 0.1, dh - 0.1), (dx, cy, dz), "wood_dark"),
           box("dGlow", (W / 2 - 0.03, 0.02, dh - 0.02), (dx, cy + D / 2 + 0.045, dz), mat(TEAL, 1.6))]
    p["Drawer"] = drw
    # 붉은 어깨끈(앞으로 넘어와 가슴 앞에서 만남)
    p["Chest"] += [box("strapL", (0.07, 0.55, 0.07), (0.2, 0.25, 1.45), RED), box("strapR", (0.07, 0.55, 0.07), (-0.2, 0.25, 1.45), RED), box("strapFL", (0.07, 0.04, 0.5), (0.1, -0.235, 1.2), RED, rot=(0, -0.3, 0)), box("strapFR", (0.07, 0.04, 0.5), (-0.1, -0.235, 1.2), RED, rot=(0, 0.3, 0))]
    return p, h

# ── 동작 ─────────────────────────────────────────────────────────────────────────
def mir(a, b): return {"L": a, "R": b}
def wol_clips():
    """월화. 팔은 옆으로 벌어진 자세가 기준이다(앞=왼팔 rz 음수·오른팔 rz 양수, 위=왼팔 ry 음수·오른팔 ry 양수)."""
    C = {}
    def pose(**k):
        d = {"Chest": {"r": (k.get("lean", 0), 0, k.get("twist", 0))}, "Hips": {"r": (0, 0, k.get("hturn", 0)), "l": (0, 0, k.get("drop", 0))}, "Head": {"r": (k.get("nod", 0), 0, k.get("hz", 0))},
             "UpperArm.L": {"r": (0, -k.get("lup", 0), -k.get("lfw", 0))}, "UpperArm.R": {"r": (0, k.get("rup", 0), k.get("rfw", 0))}, "Hand.L": {"r": (k.get("lh", 0), 0, 0)}, "Hand.R": {"r": (k.get("rh", 0), 0, 0)},
             "Prop": {"r": (0, 0, k.get("ring", 0))}}
        return d
    a = pose(ring=0, nod=1); b = pose(ring=10, nod=-1, lup=4, rup=4)
    C["Idle"] = ([(0, a), (48, b), (96, a)], "BEZIER", True, {})
    # 등장 5초 중 1.4초 이후(3.6초=216f): 등 돌린 채 서 있다가(0) 방울을 한 번 흔들고(36f) 열두째 잔 쪽으로 고개를 돌리다 멈춘다(132f)
    back = pose(hturn=180, lfw=15, rfw=15)
    C["Intro"] = ([(0, back), (24, {**back, **pose(hturn=180, lup=15, lfw=30, rfw=15, rup=0)}), (36, pose(hturn=180, lup=35, lfw=40, lh=-30)), (48, pose(hturn=180, lup=20, lfw=25)), (96, pose(hturn=180, lfw=10, rfw=10)),
                   (132, pose(hturn=180, hz=-50, nod=6)), (216, pose(hturn=180, hz=-50, nod=6))], "BEZIER", False, {"bell_ring": 36, "head_turn": 132})
    # 잔이 열린다(예비 1.0초=60f): 두 팔을 들어 올리고 방울을 높이 든다 → 내리치기
    up = pose(lup=55, rup=55, lfw=10, rfw=10, lean=-6, nod=-6, lh=-35, ring=25); down = pose(lup=-10, rup=-10, lfw=40, rfw=40, lean=12, nod=10, lh=-10, ring=60)
    C["Open"] = ([(0, a), (24, pose(lup=25, rup=25, lean=-3)), (54, up), (60, up), (66, down), (84, down), (104, a)], "BEZIER", False, {"windup_end": 60, "hit": 66, "flash": 54})
    # 붉은 천 휘감기(예비 0.7초=42f): 오른팔을 뒤로 젖혔다가 앞으로 길게 휘두름
    wnd = pose(rfw=-60, rup=20, twist=-30, hturn=-10, lean=2); whip = pose(rfw=80, rup=0, twist=40, hturn=12, lean=8, rh=-20)
    C["Whip"] = ([(0, a), (28, pose(rfw=-35, rup=10, twist=-15)), (42, wnd), (46, whip), (66, whip), (90, a)], "LINEAR", False, {"windup_end": 42, "hit": 46})
    # 2페이즈 '거꾸로 굿': 제자리에서 반 바퀴씩 돌며 팔을 휘두름
    C["Phase2"] = ([(0, a), (20, pose(lup=40, rup=40, hturn=-60)), (40, pose(lup=30, rup=30, hturn=-150, ring=40)), (60, pose(lup=40, rup=40, hturn=-240, ring=80)), (80, pose(lup=30, rup=30, hturn=-330, ring=120)), (96, pose(hturn=-360, ring=140)), (120, pose(ring=140))], "LINEAR", False, {"spin_start": 0})
    # 처결 대기: 굿판 가운데 주저앉는다(방울이 굴러 나가고 부채는 놓지 않는다)
    kn = pose(drop=-0.62, lean=14, nod=16, lup=-30, rup=-20, lfw=20, rfw=20, lh=20)
    C["Kneel"] = ([(0, a), (12, pose(drop=-0.2, lean=6, lfw=20, rfw=10, lh=40)), (24, pose(drop=-0.4, lean=10, lfw=25, lup=-10, lh=30)), (45, kn), (90, kn)], "BEZIER", False, {"bell_drop": 8})
    kh = pose(drop=-0.62, lean=15, nod=18, lup=-30, rup=-20, lfw=20, rfw=20); kh2 = pose(drop=-0.62, lean=13, nod=15, lup=-28, rup=-18, lfw=20, rfw=20)
    C["KneelHold"] = ([(0, kh), (60, kh2), (120, kh)], "BEZIER", True, {})
    # 천도 7.5초 중 몸의 동작: 일어서(0~90f) 엎어진 열두째 잔을 두 손으로 세우고(90~150f) 잠깐 내민 뒤(180~240f) 부채를 접어 굿상에 눕히고(270~330f) 흩어질 자세
    stand = pose(); bendcup = pose(lean=38, nod=20, lup=-15, rup=-15, lfw=70, rfw=70, lh=-30); hold = pose(lean=12, nod=-4, lup=0, rup=0, lfw=75, rfw=75, lh=-60)
    C["Tendo"] = ([(0, kh), (60, pose(drop=-0.25, lean=8, nod=8)), (90, stand), (120, bendcup), (150, bendcup), (180, hold), (240, hold), (255, bendcup), (300, pose(lean=14, rfw=60, lfw=10)), (345, pose(lean=0, nod=-8, lup=30, rup=30)), (390, pose(lean=0, nod=-10, lup=40, rup=40))], "BEZIER", False,
                  {"stand_up": 90, "cup_set": 150, "cup_offer": 210, "fan_lay": 300, "dissolve": 390})
    # 파혼 2.5초: 폭발에 젖혀져 팔이 흩어진 뒤 주저앉는다
    C["Pahon"] = ([(0, a), (6, pose(lup=70, rup=70, lean=-20, nod=-18, hz=0, lh=-60)), (30, pose(lup=60, rup=60, lean=-14, nod=-12, drop=-0.05)), (90, pose(lup=-20, rup=-20, lean=18, nod=20, drop=-0.45)), (150, pose(lup=-30, rup=-30, lean=20, nod=22, drop=-0.62))], "BEZIER", False, {"blast": 6})
    C["Hurt"] = ([(0, a), (5, pose(lean=-10, nod=-8, lup=8, rup=8)), (20, a)], "BEZIER", False, {})
    return C

def seo_clips():
    """서 의원. 팔은 앞으로 모은 자세가 기준(들기 rx 음수, 벌리기 rz). 약장(Case)은 등에서 가슴 움직임을 따르고 Drawer는 +Y(뒤)로 민다."""
    C = {}
    def pose(**k):
        return {"Chest": {"r": (k.get("lean", 0), 0, k.get("twist", 0))}, "Hips": {"r": (0, 0, k.get("hturn", 0)), "l": (0, 0, k.get("drop", 0))}, "Head": {"r": (k.get("nod", 0), 0, k.get("hz", 0))},
                "UpperArm.L": {"r": (-k.get("lup", 0), 0, -k.get("lout", 0))}, "UpperArm.R": {"r": (-k.get("rup", 0), 0, k.get("rout", 0))}, "Hand.L": {"r": (-k.get("lh", 0), 0, 0)}, "Hand.R": {"r": (-k.get("rh", 0), 0, 0)},
                "Case": {"r": (k.get("case", 0), 0, 0)}, "Drawer": {"l": (0, k.get("slide", 0), 0)}, "Prop": {"r": (0, 0, k.get("book", 0))}}
    a = pose(lean=1, nod=1, book=0); b = pose(lean=-1, nod=-1, book=4)
    C["Idle"] = ([(0, a), (48, b), (96, a)], "BEZIER", True, {})
    # 등장 중 1.4초 이후: 기침하며 서랍이 조금 밀려 나왔다가 들어간다(36f)
    cough = lambda s, l: pose(lean=l, nod=l * 0.6, case=-l * 0.5, slide=s)
    C["Intro"] = ([(0, a), (30, a), (36, cough(0.0, 4)), (42, cough(0.12, 10)), (48, cough(0.12, 3)), (54, cough(0.12, 11)), (66, cough(0.0, 2)), (84, a), (210, a)], "LINEAR", False, {"cough": 42, "drawer_out": 42, "drawer_in": 66})
    # 번호 부르기(예비 0.8초=48f): 오른손을 높이 들어 번호를 부르고 앞으로 찍듯 내림
    up = pose(rup=70, rout=20, lean=-6, nod=-8, rh=20, lup=10); call = pose(rup=20, rout=0, lean=12, nod=10, rh=-15, lup=10)
    C["Call"] = ([(0, a), (30, pose(rup=35, rout=10)), (48, up), (52, call), (72, call), (96, a)], "BEZIER", False, {"windup_end": 48, "hit": 52})
    # 붉은 도장 찍기(예비 0.7초=42f): 두 팔을 머리 위로, 앞으로 내리찍음
    st_up = pose(rup=100, lup=100, rout=10, lout=10, lean=-12, nod=-10); st_dn = pose(rup=25, lup=25, lean=22, nod=14, rh=-25, lh=-25)
    C["Stamp"] = ([(0, a), (28, pose(rup=55, lup=55, lean=-5)), (42, st_up), (46, st_dn), (66, st_dn), (90, a)], "LINEAR", False, {"windup_end": 42, "hit": 46})
    # 명단 줄이기(2페이즈): 장부가 빠르게 넘어가고 몸이 한 번 떨림
    C["Phase2"] = ([(0, a), (18, pose(lean=-8, nod=-6, book=40, rup=40, lup=40)), (48, pose(lean=4, nod=4, book=160, rup=20, lup=20)), (72, a), (96, a)], "LINEAR", False, {"book_flip": 18})
    # 약점 노출(낙인 세 번 피함, 3초=180f): 기침하며 멈춘다. 돌아선 채 서랍이 열려 청록 약점판이 보임(빛은 코드가 켬)
    cg = lambda l, s, t: pose(lean=l, nod=l * 0.7, case=-l * 0.4, slide=s, hturn=t)
    C["Cough"] = ([(0, a), (18, cg(12, 0.0, 60)), (30, cg(14, 0.14, 150)), (45, cg(6, 0.14, 180)), (60, cg(16, 0.14, 180)), (75, cg(6, 0.14, 180)), (90, cg(14, 0.14, 180)), (105, cg(6, 0.14, 180)), (135, cg(10, 0.14, 180)), (165, cg(6, 0.0, 90)), (180, a)], "LINEAR", False,
                  {"drawer_out": 30, "drawer_in": 165, "turn_back_done": 45})
    # 처결 대기: 약장을 내려놓고 무릎 꿇어 손바닥을 들여다본다
    kn = pose(drop=-0.55, lean=18, nod=26, rup=18, lup=18, rh=40, lh=40, case=-8)
    C["Kneel"] = ([(0, a), (30, pose(drop=-0.2, lean=10, nod=12, case=-12)), (60, kn), (90, kn)], "BEZIER", False, {"case_down": 30})
    kh = pose(drop=-0.55, lean=18, nod=26, rup=18, lup=18, rh=40, lh=40, case=-8); kh2 = pose(drop=-0.55, lean=16, nod=24, rup=17, lup=17, rh=40, lh=40, case=-6)
    C["KneelHold"] = ([(0, kh), (60, kh2), (120, kh)], "BEZIER", True, {})
    # 천도 7.5초: 서랍을 열어 마른 붓을 뉘고(90~150f) 명부가 넘어가는 동안 서 있다가(210f) 탕건을 고쳐 쓰고(300f) 움막 줄을 돌아본 뒤(330f) 흩어진다
    C["Tendo"] = ([(0, kh), (45, pose(drop=-0.2, lean=10, nod=14)), (90, pose(lean=18, nod=16, slide=0.14, rh=10, rup=30, lup=20, case=-6)), (140, pose(lean=24, nod=22, slide=0.14, rup=45, rh=-10, case=-8)), (170, pose(lean=14, nod=14, slide=0.0)),
                   (230, pose(lean=0, nod=0, book=10)), (285, pose(rup=95, rout=10, rh=30, nod=-4)), (305, pose(rup=95, rout=10, rh=20, nod=-6)), (330, pose(hturn=-60, hz=-20, rup=10)), (390, pose(hturn=-60, hz=-20, nod=-8))], "BEZIER", False,
                  {"drawer_open": 90, "brush_place": 140, "drawer_close": 170, "hat_fix": 300, "look_back": 330, "dissolve": 390})
    # 파혼: 약장이 터진다(몸은 젖혀지고 서랍이 튀어나옴)
    C["Pahon"] = ([(0, a), (6, pose(lean=-22, nod=-18, rup=60, lup=60, slide=0.3, case=14)), (30, pose(lean=-12, nod=-10, rup=40, lup=40, slide=0.3, case=10)), (90, pose(lean=18, nod=20, drop=-0.3, rup=10, lup=10, slide=0.3)), (150, pose(lean=22, nod=24, drop=-0.55, rup=15, lup=15, slide=0.3))], "BEZIER", False, {"burst": 6})
    C["Hurt"] = ([(0, a), (5, pose(lean=-9, nod=-7, case=6)), (20, a)], "BEZIER", False, {})
    return C

BOSS = [("boss_b02_wolhwa", wolhwa, bones_wolhwa, wol_clips, 2.1), ("boss_b03_seo", seo, bones_seo, seo_clips, 2.0)]

def build(name, fn, bn, cl, h, export=True, sheets=False):
    reset(); anim.setup_scene(); p, _ = fn(); parts = []
    for bone, objs in p.items(): parts += to_group(objs, bone)
    o = join(name, parts); arm = rig(o, bn()); lo, hi = bounds(o); man = []
    for cname, (keys, interp, loop, ev) in cl().items():
        i = anim.clip(arm, cname, keys, interp); i.update({"loop": loop, "events": ev}); man.append(i)
    if sheets:
        setup_render(3.9, (0, 0, 1.0), size=(250, 300), ground_size=14)
        for c in man:
            n = c["frames"]; fr = sorted({0, round(n * 0.2), round(n * 0.4), round(n * 0.6), round(n * 0.8), n - 1})
            if c["name"] in ("Idle", "KneelHold", "Hurt"): continue
            anim.sheet(arm, c["name"], fr, os.path.join(OUT, "previews", f"anim_{name}_{c['name']}"), cell=(250, 300), ortho=3.9, center=(0, 0, 1.0))
    path = os.path.join(OUT, "boss", f"{name}.glb")
    if export: anim.export_rig(arm, path)
    v = anim.verify(path) if export else None
    return {"name": name, "tris": tris(o), "height_m": round(hi.z, 2), "bones": [b[0] for b in bn()], "clips": man, "verify": v}

if __name__ == "__main__":
    res = [build(*b, sheets="--sheets" in sys.argv) for b in BOSS]
    for r in res: print(r["name"], r["tris"], r["height_m"], r["verify"]["joints"], r["verify"]["animations"])
    json.dump({"fps": anim.FPS, "note": "6원형 뼈 규칙 + Hand.L/R. 서 의원은 Case(약장)·Drawer(서랍) 추가. 약점 청록판(dGlow)은 Drawer 뼈에 붙은 발광 재질(코드가 켜고 끈다)", "bosses": res}, open(os.path.join(OUT, "boss", "_b02_b03_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
