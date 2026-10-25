"""필드 혼 '유형' 3종: 넋두리(멀리서 원념을 던짐) · 잔넋(작게 무리 지음) · 묻힌 혼(땅에서 솟음).
왜: 지금 필드 혼은 떠돈 시간 4등급(갓 죽은·해 넘긴·오래된·덩어리)이 같은 몸이라 싸움이 단조롭다. 등급은 '색·크기·세기', 유형은 '몸·행동'으로 갈라 한눈에 읽히게 한다.
  → 유형 3 × 등급 4 = 12종. 파일명 soul_<유형>_<등급>.glb  (유형: wail·mote·buried, 등급: fresh·day·old·lump)
  → 등급색은 기존 혼과 같다(갓 죽은 하늘빛 · 해 넘긴 황금빛 · 오래된 갈회색 · 덩어리 보랏빛). 주황은 파혼 전용이라 쓰지 않는다.
동작(60fps): 공통 Float(떠돌기) / Windup(공격 예고, 번쩍 신호 flash) / Attack(공격) / Kneel(무릎, 끝 자세 유지) + 유형별 추가
  wail   : 뼈 Root·Body·Arm·Orb. Orb는 손에 쥔 원념 구(예비동작에서 커지고 던질 때 사라짐 → 코드가 release 프레임에 투사체 fx_wonnyeom_orb를 손 위치에서 쏜다)
  mote   : 뼈 Root·Body. 작고 빠르다(키 0.5m). 여럿이 모여 다닌다
  buried : 뼈 Root·Body·ArmL·ArmR + 추가 동작 Hidden(땅속 대기) / Sink(다시 가라앉음). Root에 붙은 흙무더기만 보이다가 Windup에서 솟는다
규칙: 모델 원점=바닥, 정면=−Y, 1단위=1m. 몸은 발광(emission) 재질, 눈은 어두운 face 재질."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import rig, to_group
import anim
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
GRADES = {"fresh": ("soul_fresh", 0.55, 0.7, 3.2), "day": ("soul_day", 0.62, 0.55, 3.0), "old": ("soul_old", 0.7, 0.25, 1.1), "lump": ("soul_lump", 0.6, 0.6, 2.8)}   # 색키, 겉껍질 알파, 겉껍질 발광, 핵 발광
WON = "#B04FD0"     # 원념(던지는 구) 색: 자주빛 보라. 주황 아님

def mats(g):
    key, a, e, c = GRADES[g]; return mat_alpha(key, a, e), mat(key, c), mat(key, 1.0)

def eyes(z, y, dx=0.07, w=0.05, h=0.075, ox=0, slit=0.0):
    out = []
    for s in (1, -1):
        out.append(sphere("eye", 1, (ox + s * dx, y, z), "face", 7, 5, (w / 2, 0.012, h / 2)) if not slit else box("eye", (w, 0.016, h * 0.4), (ox + s * dx, y, z), "face", rot=(0, -s * slit, 0)))
    return out

# ───────────────────────── 모델 ─────────────────────────
def wail(g):
    """넋두리: 키 크고 구부정, 입을 벌린 채 운다. 오른팔이 길게 늘어져 손에 원념 구를 쥔다. 높이 약 1.55m."""
    sh, core, sol = mats(g); r = random.Random(21)
    body = lathe("body", [(0.30, 0.0), (0.45, 0.2), (0.85, 0.24), (1.15, 0.17), (1.3, 0.1)], 9, sh, scale=(1.0, 0.9, 1.0), rot=(0.12, 0, 0))
    torso = [body, sphere("head", 0.18, (0, -0.1, 1.42), sh, 9, 6), sphere("core", 0.12, (0, 0, 0.8), core, 7, 5, (1, 1, 1.5))]
    torso += eyes(1.46, -0.265, dx=0.07, w=0.055, h=0.06, slit=0.35) + [sphere("mouth", 1, (0, -0.28, 1.36), "face", 7, 5, (0.045, 0.02, 0.07))]
    for i in range(6):   # 해진 밑단·머리카락 가닥
        a = i / 6 * math.tau + 0.2; ln = r.uniform(0.2, 0.36)
        torso += chain_pts(f"rag{i}", [(math.cos(a) * 0.18, math.sin(a) * 0.15, 0.34), (math.cos(a) * 0.22, math.sin(a) * 0.19, 0.34 - ln * 0.5), (math.cos(a) * 0.25 + r.uniform(-0.03, 0.03), math.sin(a) * 0.2, 0.34 - ln)], 0.045, 0.006, sol, 5)
    torso += chain_pts("hairL", [(0.1, -0.02, 1.5), (0.18, 0.04, 1.3), (0.2, 0.06, 1.1)], 0.04, 0.006, sol, 5) + chain_pts("hairR", [(-0.1, -0.02, 1.5), (-0.18, 0.04, 1.3), (-0.2, 0.06, 1.1)], 0.04, 0.006, sol, 5)
    armL = [limb("armL", (0.2, -0.03, 1.1), (0.3, -0.12, 0.62), 0.055, 0.075, sol, 6), sphere("handL", 0.07, (0.31, -0.13, 0.57), sol, 6, 4)]
    armR = [limb("armR", (-0.2, -0.03, 1.1), (-0.3, -0.1, 0.52), 0.06, 0.085, sol, 6), sphere("handR", 0.085, (-0.31, -0.11, 0.46), sol, 6, 4)]
    orb = [sphere("orb", 0.15, (-0.31, -0.13, 0.4), mat(WON, 4.0), 8, 6), sphere("orbShell", 0.23, (-0.31, -0.13, 0.4), mat_alpha(WON, 0.32, 1.2), 8, 6)]
    return to_group(torso + armL, "Body") + to_group(armR, "Arm") + to_group(orb, "Orb")

def mote(g):
    """잔넋: 콩알만 한 혼. 큰 눈 두 개와 짧은 불꽃, 꼬리 한 가닥. 키 약 0.5m. 떼로 몰려다닌다."""
    sh, core, sol = mats(g)
    body = lathe("body", [(0.04, 0.0), (0.08, 0.1), (0.2, 0.15), (0.32, 0.12), (0.4, 0.06)], 9, sh)
    p = [body, sphere("core", 0.07, (0, 0.0, 0.22), core, 7, 5, (1, 1, 1.2))] + eyes(0.26, -0.135, dx=0.05, w=0.055, h=0.07)
    p += chain_pts("flame", [(0, 0, 0.4), (0.012, 0, 0.47), (-0.012, 0, 0.53)], 0.035, 0.004, sol, 5) + chain_pts("tail", [(0, 0.05, 0.1), (0.06, 0.12, 0.04), (0.1, 0.17, 0.02)], 0.04, 0.005, sol, 5)
    return to_group(p, "Body")

def buried(g):
    """묻힌 혼: 흙무더기(항상 보임)에서 몸통·긴 팔이 솟는다. 몸은 땅속 −1.5m에서 시작해 높이 약 1.7m까지 올라온다. 머리는 뒤로 젖히고, 긴 머리카락이 앞으로 늘어진다."""
    sh, core, sol = mats(g); r = random.Random(33); soil = mat("#4B3A2A", 0.0); soil2 = mat("#5E4A36", 0.0)
    mound = [sphere("mound", 0.62, (0, 0, 0.0), soil, 9, 5, (1.0, 1.0, 0.3)), sphere("clod1", 0.2, (0.45, -0.1, 0.06), soil2, 6, 4, (1, 1, 0.6)), sphere("clod2", 0.16, (-0.42, 0.18, 0.05), soil2, 6, 4, (1, 1, 0.6)), sphere("clod3", 0.13, (0.1, 0.5, 0.04), soil, 6, 4, (1, 1, 0.6))]
    for i in range(5):   # 흙 위로 삐져나온 머리카락 가닥(예고)
        a = i * 1.3 + 0.4; mound += chain_pts(f"hair{i}", [(math.cos(a) * 0.3, math.sin(a) * 0.3, 0.1), (math.cos(a) * 0.34, math.sin(a) * 0.34, 0.26), (math.cos(a) * 0.3 + 0.05, math.sin(a) * 0.32, 0.38)], 0.025, 0.004, sol, 4)
    body = lathe("body", [(0.0, 0.26), (0.3, 0.26), (0.8, 0.27), (1.15, 0.2), (1.3, 0.12)], 9, sh, scale=(1.0, 0.85, 1.0))
    torso = [body, sphere("head", 0.19, (0, 0.02, 1.48), sh, 9, 6), sphere("core", 0.14, (0, 0, 0.85), core, 7, 5, (1, 1, 1.5))] + eyes(1.5, -0.18, dx=0.075, w=0.06, h=0.08, slit=0.25) + [sphere("mouth", 1, (0, -0.19, 1.4), "face", 7, 5, (0.05, 0.02, 0.06))]
    for i in range(7):   # 앞으로 늘어진 긴 머리카락
        a = (i - 3) * 0.28; ln = r.uniform(0.6, 0.95)
        torso += chain_pts(f"lhair{i}", [(math.sin(a) * 0.18, -0.12, 1.6), (math.sin(a) * 0.24, -0.2, 1.3), (math.sin(a) * 0.26, -0.22, 1.6 - ln)], 0.03, 0.005, sol, 5)
    arms = {}
    for nm, sx in (("ArmL", 1), ("ArmR", -1)):
        a = [limb("arm" + nm, (sx * 0.27, 0, 1.15), (sx * 0.38, -0.12, 0.5), 0.06, 0.085, sol, 6), sphere("hand" + nm, 0.09, (sx * 0.39, -0.13, 0.43), sol, 6, 4)]
        for k in range(4): a.append(cyl(f"fing{nm}{k}", 0.02, 0.005, 0.15, (sx * 0.39 + (k - 1.5) * 0.04, -0.14, 0.34), sol, 4, rot=(0, 0, 0)))
        arms[nm] = a
    return to_group(mound, "Root") + to_group(torso, "Body") + to_group(arms["ArmL"], "ArmL") + to_group(arms["ArmR"], "ArmR")

# ───────────────────────── 뼈·동작 ─────────────────────────
B_WAIL = [("Root", None, (0, 0, 0), (0, 0, 0.2)), ("Body", "Root", (0, 0, 0), (0, 0, 0.6)), ("Arm", "Body", (-0.2, -0.03, 1.1), (-0.3, -0.1, 0.52)), ("Orb", "Arm", (-0.31, -0.13, 0.4), (-0.31, -0.13, 0.6))]
B_MOTE = [("Root", None, (0, 0, 0), (0, 0, 0.1)), ("Body", "Root", (0, 0, 0.05), (0, 0, 0.3))]
B_BURIED = [("Root", None, (0, 0, 0), (0, 0, 0.2)), ("Body", "Root", (0, 0, 0), (0, 0, 0.6)), ("ArmL", "Body", (0.27, 0, 1.15), (0.38, -0.12, 0.5)), ("ArmR", "Body", (-0.27, 0, 1.15), (-0.38, -0.12, 0.5))]

def S(r=(0, 0, 0), s=(1, 1, 1), l=(0, 0, 0)): return {"r": r, "s": s, "l": l}

def clips_wail():
    B = lambda **k: {"Body": S(**k)}
    fl_a = {**B(r=(3, 0, -4)), "Arm": S(r=(4, 0, 6)), "Orb": S(s=(0.9, 0.9, 0.9))}; fl_b = {"Root": {"l": (0, 0, 0.09)}, **B(r=(-3, 0, 4), s=(0.98, 0.98, 1.03)), "Arm": S(r=(-3, 0, -5)), "Orb": S(s=(1.05, 1.05, 1.05))}
    C = {"Float": ([(0, fl_a), (45, fl_b), (90, fl_a)], "BEZIER", True, {})}
    # 예고 42f(0.7s): 몸을 젖히며 오른팔을 뒤·위로 치켜들고 원념 구가 커진다. 28f에 번쩍 → 던질 때까지 버틴다
    w1 = {**B(r=(-10, 0, 8), s=(1.04, 1.04, 0.93)), "Arm": S(r=(95, 0, 0)), "Orb": S(s=(0.5, 0.5, 0.5))}
    w2 = {**B(r=(-22, 0, 12), s=(1.1, 1.1, 0.86)), "Arm": S(r=(165, 0, 0)), "Orb": S(s=(1.25, 1.25, 1.25))}
    w3 = {**B(r=(-24, 0, 14), s=(1.12, 1.12, 0.84)), "Arm": S(r=(172, 0, 0)), "Orb": S(s=(1.45, 1.45, 1.45))}
    C["Windup"] = ([(0, {**fl_a, "Orb": S(s=(0.1, 0.1, 0.1))}), (14, w1), (28, w2), (36, w3), (42, w3)], "BEZIER", False, {"flash": 28, "end_pose_held": True, "orb_grow_from": 0, "orb_full": 36})
    th = {**B(r=(26, 0, -10), s=(0.93, 0.93, 1.08), l=(0, -0.25, 0)), "Arm": S(r=(-120, 0, 0)), "Orb": S(s=(0.02, 0.02, 0.02))}
    C["Attack"] = ([(0, w3), (5, th), (9, {**B(r=(14, 0, -6), l=(0, -0.12, 0)), "Arm": S(r=(-150, 0, 0)), "Orb": S(s=(0.01, 0.01, 0.01))}), (22, {"Orb": S(s=(0.1, 0.1, 0.1))})], "LINEAR", False, {"release": 5, "release_bone": "Orb", "projectile": "fx_wonnyeom_orb"})
    kn = {**B(r=(26, 0, 0), s=(1.14, 1.14, 0.55)), "Arm": S(r=(8, 0, 12)), "Orb": S(s=(0.01, 0.01, 0.01))}
    C["Kneel"] = ([(0, {}), (10, {**B(r=(-6, 0, 0), s=(1.06, 1.06, 0.82)), "Arm": S(r=(30, 0, 0)), "Orb": S(s=(0.3, 0.3, 0.3))}), (22, kn), (40, {**kn, "Body": S(r=(28, 0, 0), s=(1.15, 1.15, 0.53))})], "BEZIER", False, {"end_pose_held": True})
    return C

def clips_mote():
    B = lambda **k: {"Body": S(**k)}
    C = {"Float": ([(0, {**B(r=(4, 0, -8)), "Root": {"l": (0, 0, 0)}}), (10, {**B(r=(-4, 0, 8), s=(0.97, 0.97, 1.06)), "Root": {"l": (0, 0, 0.07)}}), (20, {**B(r=(4, 0, -8)), "Root": {"l": (0, 0, 0)}}), (30, {**B(r=(-4, 0, 8), s=(0.97, 0.97, 1.06)), "Root": {"l": (0, 0, 0.07)}}), (40, {**B(r=(4, 0, -8)), "Root": {"l": (0, 0, 0)}})], "BEZIER", True, {})}
    sq = B(r=(-10, 0, 0), s=(1.18, 1.18, 0.72)); sq2 = B(r=(-12, 0, 6), s=(1.22, 1.22, 0.68)); sq3 = B(r=(-12, 0, -6), s=(1.22, 1.22, 0.68))
    C["Windup"] = ([(0, {}), (6, sq), (9, sq2), (12, sq3), (15, sq2), (18, sq3)], "LINEAR", False, {"flash": 9, "end_pose_held": True})   # 몸을 웅크려 부르르 떨고 번쩍(0.3초)
    lung = {"Root": {"l": (0, -0.55, 0.08)}, **B(r=(35, 0, 0), s=(0.86, 0.86, 1.2))}
    C["Attack"] = ([(0, sq3), (4, lung), (6, lung), (14, {})], "LINEAR", False, {"hit": 4})
    pop = B(r=(18, 0, 0), s=(1.3, 1.3, 0.3))
    C["Kneel"] = ([(0, {}), (6, B(r=(-8, 0, 0), s=(1.1, 1.1, 0.8))), (14, pop), (24, B(r=(20, 0, 0), s=(1.34, 1.34, 0.26)))], "BEZIER", False, {"end_pose_held": True})
    return C

def clips_buried():
    B = lambda **k: {"Body": S(**k)}
    sunk = {"Body": S(l=(0, 0, -1.6), r=(0, 0, 0)), "ArmL": S(r=(-170, 0, 0)), "ArmR": S(r=(-170, 0, 0))}
    C = {}
    r1 = {**sunk, "Root": S(s=(1.03, 1.03, 1.08))}; r2 = {**sunk, "Root": S(s=(0.99, 0.99, 0.97), r=(0, 0, 3))}; r3 = {**sunk, "Root": S(s=(1.02, 1.02, 1.04), r=(0, 0, -3))}
    C["Hidden"] = ([(0, sunk), (15, r1), (30, r2), (45, r3), (60, sunk)], "BEZIER", True, {})   # 땅속 대기: 흙무더기만 꿈틀
    shake1 = {**sunk, "Root": S(r=(0, 0, 4), s=(1.05, 1.05, 1.15))}; shake2 = {**sunk, "Root": S(r=(0, 0, -5), s=(1.07, 1.07, 1.2))}
    burst = {"Body": S(l=(0, 0, -0.9), r=(-8, 0, 0)), "ArmL": S(r=(-175, 0, -18)), "ArmR": S(r=(-175, 0, 18)), "Root": S(s=(1.1, 1.1, 0.8))}
    up = {"Body": S(l=(0, 0, -0.25), r=(-12, 0, 0)), "ArmL": S(r=(-160, 0, -35)), "ArmR": S(r=(-160, 0, 35)), "Root": S(s=(1.05, 1.05, 0.9))}
    full = {"Body": S(l=(0, 0, 0), r=(-10, 0, 0), s=(1.0, 1.0, 1.0)), "ArmL": S(r=(-135, 0, -45)), "ArmR": S(r=(-135, 0, 45))}
    C["Windup"] = ([(0, sunk), (8, shake1), (14, shake2), (20, shake1), (26, burst), (30, up), (36, full), (44, {**full, "Body": S(l=(0, 0, 0), r=(-14, 0, 0), s=(1.05, 1.05, 0.95))})], "BEZIER", False, {"flash": 26, "emerge_peak": 30, "end_pose_held": True, "ground_dust_at": 26})
    slam = {"Body": S(l=(0, -0.45, 0), r=(30, 0, 0), s=(0.94, 0.94, 1.06)), "ArmL": S(r=(-60, 0, 8)), "ArmR": S(r=(-60, 0, -8))}
    C["Attack"] = ([(0, full), (6, slam), (9, slam), (20, {})], "LINEAR", False, {"hit": 6})
    kn = {"Body": S(l=(0, 0, -0.6), r=(34, 0, 0), s=(1.1, 1.1, 0.6)), "ArmL": S(r=(10, 0, 14)), "ArmR": S(r=(10, 0, -14))}
    C["Kneel"] = ([(0, {}), (12, {"Body": S(l=(0, 0, -0.25), r=(14, 0, 0), s=(1.05, 1.05, 0.85)), "ArmL": S(r=(-20, 0, 8)), "ArmR": S(r=(-20, 0, -8))}), (26, kn), (40, {**kn, "Body": S(l=(0, 0, -0.7), r=(38, 0, 0), s=(1.12, 1.12, 0.56))})], "BEZIER", False, {"end_pose_held": True})
    C["Sink"] = ([(0, full), (10, {**up, "Root": S(s=(1.05, 1.05, 0.9))}), (22, {**sunk, "Root": S(s=(1.1, 1.1, 0.8))}), (30, sunk)], "BEZIER", False, {"ground_dust_at": 22})
    return C

TYPES = {"wail": (wail, B_WAIL, clips_wail, "넋두리", "원념을 던지는 원거리 혼"), "mote": (mote, B_MOTE, clips_mote, "잔넋", "작게 무리 짓는 혼"), "buried": (buried, B_BURIED, clips_buried, "묻힌 혼", "땅에서 솟는 혼")}

def orb_fx():
    """던지는 원념 구(투사체): 보랏빛 구 + 겉껍질 + 뒤로 끌리는 꼬리 3가닥. 지름 0.35m, 길이 0.9m. 원점=구 중심, 꼬리는 +Y(뒤) 쪽. 정면=−Y(날아가는 방향)."""
    p = [sphere("orb", 0.16, (0, 0, 0), mat(WON, 4.0), 8, 6), sphere("shell", 0.25, (0, 0, 0), mat_alpha(WON, 0.35, 1.3), 8, 6)]
    for i, (dx, dz) in enumerate(((0, 0), (0.07, 0.05), (-0.06, -0.05))):
        p += chain_pts(f"tail{i}", [(dx * 0.4, 0.12, dz * 0.4), (dx, 0.4, dz), (dx * 1.4, 0.72, dz * 1.4)], 0.07 - 0.015 * i, 0.006, mat(WON, 2.0), 5)
    return p

if __name__ == "__main__":
    only = sys.argv[1:]; rep = []; mans = {}
    reset(); o = join("fx_wonnyeom_orb", orb_fx()); lo, hi = bounds(o); export(o, os.path.join(OUT, "fx", "fx_wonnyeom_orb.glb")); rep.append({"name": "fx_wonnyeom_orb", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)]})
    for t, (fn, bones, cl, ko, desc) in TYPES.items():
        for g in GRADES:
            name = f"soul_{t}_{g}"
            if only and name not in only and t not in only: continue
            reset(); anim.setup_scene(); o = join(name, fn(g)); arm = rig(o, bones); man = []
            for cn, (keys, interp, loop, ev) in cl().items():
                i = anim.clip(arm, cn, keys, interp); i.update({"loop": loop, "events": ev}); man.append(i)
            if g == "fresh" or (t == "buried" and g == "old"):
                big = 3.4 if t != "mote" else 1.6; cz = 0.75 if t != "mote" else 0.25
                setup_render(big, (0, 0, cz), size=(200, 260), ground_size=8)
                for c in man:
                    n = c["frames"]; anim.sheet(arm, c["name"], sorted({0, n // 4, n // 2, 3 * n // 4, n - 1}), os.path.join(OUT, "previews", f"anim_{name}_{c['name']}"), ortho=big, center=(0, 0, cz), cell=(200, 260))
            p = os.path.join(OUT, "souls", f"{name}.glb"); anim.export_rig(arm, p); v = anim.verify(p); rep.append(v); mans[t] = {"label": ko, "desc": desc, "clips": man, "bones": [b[0] for b in bones]}
            lo, hi = bounds(o) if False else (None, None)
    json.dump({"fps": anim.FPS, "grades": list(GRADES), "types": mans, "files": rep}, open(os.path.join(OUT, "souls", "_soul_types_manifest.json"), "w"), ensure_ascii=False, indent=1)
    print(len(rep), "개")
