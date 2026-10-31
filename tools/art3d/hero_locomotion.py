"""주인공 이동 동작: 달리기·출발·멈춤·방향 전환·회피 구르기, 그리고 도포 자락·갓끈 흔들림 굽기.
핵심 원칙 = '발이 땅에서 미끄러지지 않게'. 달리는 속도 5.5m/s(명세 §3-2)에서, 땅에 닿은 발은 땅 위에 그대로 있고 몸이 그 위를 지나간다.
 - 땅에 닿은 동안 발목의 앞뒤 위치는 (몸이 간 거리)만큼 정확히 뒤로 밀린다 → 코드가 Root를 5.5m/s로 옮기면 발이 바닥에 붙어 보인다.
 - 다리는 2마디 IK(발 위치를 정하면 허벅지·무릎 각도를 계산)로 매 프레임 직접 풀어서 찍는다. 눈대중 각도를 쓰지 않는 이유가 이것.
 - 공중에 뜬 발(휘두름)은 땅에 닿는 순간의 속도가 땅 속도와 같도록 곡선(에르미트)으로 이어서, 닿을 때 '탁' 튀지 않게 한다.
좌표·부호: anim.py 머리말과 같다(+X 왼쪽, -Y 앞, 다리의 rx 음수=앞으로). 길이 단위 m, 각도 도, 60fps."""
import math
import bpy
from anim import _apply, FPS

V = 5.5                  # 달리기 속도 m/s (명세 §3-2, 전력질주 없음)
VF = V / FPS             # 한 프레임에 가는 거리 = 0.0917 m
L1, L2, ANK = 0.45, 0.41, 0.09     # 허벅지·정강이 길이, 발목 높이(뼈대와 같은 값)
SW = 0.3208              # 땅에 닿은 발의 앞뒤 쓸림 절반: 8프레임 × 0.0917 m ÷ 2 (한 발이 8프레임 동안 땅에 닿는다)
CYC = 30                 # 달리기 한 바퀴 30프레임 = 0.5초 = 두 걸음 → 초당 4걸음, 한 걸음 1.375m, 두 걸음(주기) 2.75m
LAST_ST = 7              # 땅에 닿은 마지막 프레임(0~7이 닿음, 8~29가 공중)
HEEL = 22.0              # 박차고 나갈 때 뒤꿈치가 들리는 각도
O_Y, O_Z = -0.2, -0.07   # 발목에서 발끝까지 (뼈대 Foot의 head→tail)
LEAN = 8.0               # 달릴 때 몸 앞기울기

def sm(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def herm(p0, m0, p1, m1, u):
    u2, u3 = u * u, u * u * u
    return (2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1

# ───────────────────────── 발·다리 ─────────────────────────
def pivot(flat_y, psi):
    """발끝을 땅에 박은 채 뒤꿈치만 들 때의 발목 위치(박차는 순간 발끝은 안 미끄러진다)."""
    p = math.radians(psi); cy = flat_y + O_Y
    return cy - (O_Y * math.cos(p) - O_Z * math.sin(p)), 0.02 - (O_Y * math.sin(p) + O_Z * math.cos(p))

def stance_state(g):
    """땅에 닿은 동안(g=0~7): 발목이 매 프레임 VF만큼 뒤로 밀린다."""
    fy = -SW + VF * g; psi = HEEL * sm((g - 5) / 2) if g > 5 else 0.0
    y, z = pivot(fy, psi); return y, z, psi

def foot_state(g):
    """달리기 한 바퀴(30프레임) 중 한 발의 상태 (발목 y, z, 발 기울기 도, 땅에 닿았나). g=그 발의 닿는 순간부터 센 프레임."""
    g %= CYC
    if g <= LAST_ST + 1e-9:
        y, z, psi = stance_state(g); return y, z, psi, True
    u = (g - LAST_ST) / (CYC - LAST_ST); n = CYC - LAST_ST
    y0, z0, ps0 = stance_state(LAST_ST); ya, za, _ = stance_state(LAST_ST - 0.1)
    m0y, m0z = (y0 - ya) / 0.1 * n, (z0 - za) / 0.1 * n
    y = herm(y0, m0y, -SW, VF * n, u)                                  # 닿을 때 속도 = 땅 속도 → 안 미끄러짐
    z = herm(z0, m0z, ANK, 0.0, u) + 0.26 * math.sin(math.pi * u) ** 1.4   # 발을 든 높이(약 0.3m)
    psi = ps0 * (1 - u) ** 2.5 - 10 * math.sin(math.pi * u) ** 2        # 박차던 발끝이 내려오며 발끝 살짝 들림
    return y, z, psi, False

def run_foot(side, f):
    """side 'L' 은 0프레임에 닿고 'R' 은 15프레임에 닿는다(반 바퀴 어긋남)."""
    return foot_state(f - (0 if side == "L" else 15))

def dz_run(f):
    """달릴 때 골반 높이(웅크림 -0.13 위아래 0.035): 발이 땅 한가운데를 밟을 때 가장 낮고 공중에서 가장 높다."""
    return -0.13 + 0.035 * math.cos(2 * math.pi * (f - 11) / 15)

def ik(Hy, Hz, Ay, Az):
    """골반 관절 H와 발목 목표 A(평면 y,z) → (허벅지 세계각 α, 정강이 세계각 β, 무릎 굽힘 δ, 닿았나) 도. 각도는 '아래로 늘어진 뼈가 뒤(+y)로 갈수록 +'."""
    dy, dz = Ay - Hy, Az - Hz; D = math.hypot(dy, dz); clamped = False
    if D > L1 + L2 - 1e-4: D = L1 + L2 - 1e-4; clamped = True
    gam = math.atan2(dy, -dz)
    cd = max(-1.0, min(1.0, (D * D - L1 * L1 - L2 * L2) / (2 * L1 * L2))); d = math.acos(cd)
    phi = math.atan2(L2 * math.sin(d), L1 + L2 * math.cos(d)); a = gam - phi
    return math.degrees(a), math.degrees(a + d), math.degrees(d), clamped

def fk(Hy, Hz, a, d):
    """검산용: 각도에서 발목 위치를 되짚는다."""
    a, b = math.radians(a), math.radians(a + d)
    return Hy + L1 * math.sin(a) + L2 * math.sin(b), Hz - L1 * math.cos(a) - L2 * math.cos(b)

def legs(dz, ly, hips_rx, feet):
    """feet={'L':(y,z,psi),'R':...} → 다리 세 뼈의 포즈와 허벅지 세계각."""
    spec, alpha = {}, {}
    for s, (y, z, psi) in feet.items():
        a, b, d, _ = ik(ly, 0.95 + dz, y, z); alpha[s] = a
        spec[f"UpperLeg.{s}"] = {"r": (a - hips_rx, 0, 0)}; spec[f"LowerLeg.{s}"] = {"r": (d, 0, 0)}; spec[f"Foot.{s}"] = {"r": (psi - b, 0, 0)}
    return spec, alpha

# ───────────────────────── 윗몸 ─────────────────────────
def lerp_spec(a, b, t):
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, {}), b.get(k, {}); o = {}
        for key in ("r", "l"):
            if key in va or key in vb:
                x, y = va.get(key, (0, 0, 0)), vb.get(key, (0, 0, 0)); o[key] = tuple(x[i] + (y[i] - x[i]) * t for i in range(3))
        out[k] = o
    return out

def upper_run(al, hips_rx, su=1.0, bank=0.0):
    """달리는 윗몸: 팔은 반대쪽 다리와 엇갈려 흔들고, 가슴은 골반 반대로 틀며, 머리는 수평을 지킨다. su=달리기 정도(0~1)."""
    aL, aR = al["L"], al["R"]
    tw = 7.0 * max(-1.0, min(1.0, (aR - aL) / 45.0))        # 왼발이 앞이면 오른 어깨가 앞으로(+)
    arm = lambda a: max(-55.0, min(40.0, -10 + 0.85 * a))
    aL_arm, aR_arm = arm(aR), arm(aL)
    d = {"Spine": {"r": (2 * su, bank * 0.15, 0.4 * tw)}, "Chest": {"r": (3 * su, bank * 0.35, 0.6 * tw)},
         "Head": {"r": (-(hips_rx + 5 * su) + 3 * su, -bank * 1.2, -0.7 * tw)},
         "UpperArm.L": {"r": (aL_arm, -8, 0)}, "UpperArm.R": {"r": (aR_arm, 8, 0)},
         "Hand.L": {"r": (-20 + 0.6 * aL_arm, 0, 0)}, "Hand.R": {"r": (-20 + 0.6 * aR_arm, 0, 0)}}
    return d

def compose(idle_a, dz, ly, hips_rx, feet, su=1.0, bank=0.0, add=None):
    """한 프레임의 전신 자세: 다리(IK) + 윗몸(달리기↔서있기 섞기) + 골반."""
    lg, al = legs(dz, ly, hips_rx, feet)
    up = upper_run(al, hips_rx, su, bank)
    base = {k: v for k, v in idle_a.items() if k != "Hips"}
    spec = lerp_spec(base, up, su)
    spec.update(lg)
    if bank:
        for s in "LR": spec[f"UpperLeg.{s}"]["r"] = (spec[f"UpperLeg.{s}"]["r"][0], -bank * 0.9, 0)   # 몸이 기울어도 다리는 땅에 수직
    spec["Hips"] = {"r": (hips_rx, bank, 0), "l": (0, ly, dz)}
    if add:
        for k, v in add.items():
            cur = spec.get(k, {}); n = dict(cur)
            for key in ("r", "l"):
                if key in v: x = cur.get(key, (0, 0, 0)); n[key] = tuple(x[i] + v[key][i] for i in range(3))
            spec[k] = n
    return spec, al

def trapezoid(v):
    S = [0.0]
    for i in range(1, len(v)): S.append(S[-1] + (v[i - 1] + v[i]) / 2 / FPS)
    return S

# ───────────────────────── 동작 만들기 ─────────────────────────
def mk_run(idle_a, bank=0.0, n=CYC):
    keys, contact = [], {"L": [], "R": []}
    for f in range(n + 1):
        feet = {s: run_foot(s, f)[:3] for s in "LR"}
        spec, _ = compose(idle_a, dz_run(f), -0.02, LEAN, feet, 1.0, bank)
        keys.append((f, spec))
        for s in "LR": contact[s].append(run_foot(s, f)[3])
    v = [V] * (n + 1)
    return keys, {"v": v, "S": trapezoid(v), "contact": contact}

def mk_start(idle_a):
    """출발 10프레임(+11번째 프레임 = Run 0번과 같은 자세). 속도 0→5.5m/s를 5프레임(0.083초)에 올린다.
    오른발이 뒤에서 밀고(0~6), 왼발이 먼저 나가 10프레임에 땅에 닿는다. 그때 오른발은 Run과 같은 공중 자세로 이어진다."""
    N = 10; v = [V * min(1.0, f / 5) for f in range(N + 1)]; S = trapezoid(v)
    tgtR = run_foot("R", 0); velR = [(run_foot("R", 0.5)[i] - run_foot("R", -0.5)[i]) for i in range(3)]
    stR6 = lambda f: pivot(S[min(f, 6)], HEEL * sm((min(f, 6) - 4) / 2) if f > 4 else 0.0)
    keys, contact = [], {"L": [], "R": []}
    for f in range(N + 1):
        su = sm(f / 6)
        # 오른발: 6프레임까지 땅에 붙은 채 몸이 앞으로 가며 뒤로 쓸림(발끝 고정) → 공중 → 10프레임에 Run 0번 상태
        if f <= 6:
            psi = HEEL * sm((f - 4) / 2) if f > 4 else 0.0; y, z = pivot(S[f], psi); R = (y, z, psi)
        else:
            u = (f - 6) / 4; y6, z6 = stR6(6); y5, z5 = stR6(5); ps6 = HEEL
            R = (herm(y6, (y6 - y5) * 4, tgtR[0], velR[0] * 4, u), herm(z6, (z6 - z5) * 4, tgtR[1], velR[1] * 4, u) + 0.05 * math.sin(math.pi * u), herm(ps6, 0, tgtR[2], 0, u))
        # 왼발: 0프레임엔 제자리, 1프레임부터 앞으로 휘둘러 10프레임에 Run 0번(앞 -SW)에 속도를 맞춰 닿는다
        if f == 0: Lf = (0.0, ANK, 0.0)
        else:
            u = (f - 1) / 9
            Lf = (herm(0.0, 0.0, -SW, VF * 9, u), herm(ANK, 0, ANK, 0, u) + 0.2 * math.sin(math.pi * u) ** 1.2, 14 * math.sin(math.pi * u) ** 2 * (1 - u))
        feet = {"L": Lf, "R": R}
        rf = (f + 20) % CYC
        dz = sm(f / 6) * dz_run(rf); lean = LEAN * sm(f / 5) + 5.0 * math.sin(math.pi * f / N)
        spec, _ = compose(idle_a, dz, -0.02 * sm(f / 6), lean, feet, su)
        keys.append((f, spec)); contact["L"].append(f in (0, 10)); contact["R"].append(f <= 6)
    return keys, {"v": v, "S": S, "contact": contact}

def mk_stop(idle_a):
    """멈춤 15프레임. 속도 5.5→0 을 4프레임(0.067초)에. Run 11번 프레임(오른발이 닿기 직전)에서 시작하고 끝은 Idle 0번 자세.
    오른발이 2프레임에 몸 바로 아래에 '쿵' 짚어 브레이크가 되고, 왼발이 8프레임에 따라와 나란히 선다."""
    N = 15; v = [V * max(0.0, 1 - f / 4) for f in range(N + 1)]; S = trapezoid(v); Send = S[4]
    r0 = run_foot("R", 11); l0 = run_foot("L", 11)
    vel = lambda s, f: [(run_foot(s, f + 0.5)[i] - run_foot(s, f - 0.5)[i]) for i in range(3)]
    vR, vL = vel("R", 11), vel("L", 11)
    keys, contact = [], {"L": [], "R": []}
    for f in range(N + 1):
        # 오른발: 2프레임에 닿아 끝까지 박힌다(월드에 고정 → 몸 기준 위치 = S(f) - Send)
        if f < 2:
            u = f / 2; y2 = S[2] - Send
            R = (herm(r0[0], vR[0] * 2, y2, VF * 0 + v[2] / FPS * 2, u), herm(r0[1], vR[1] * 2, ANK, 0, u), herm(r0[2], 0, 0, 0, u))
        else: R = (S[f] - Send, ANK, 0.0)
        # 왼발: 공중에서 따라와 8프레임에 제자리(0)에 선다
        if f < 8:
            u = f / 8
            L = (herm(l0[0], vL[0] * 8, 0.0, 0.0, u), herm(l0[1], vL[1] * 8, ANK, 0, u) + 0.08 * math.sin(math.pi * u), herm(l0[2], 0, 0, 0, u))
        else: L = (0.0, ANK, 0.0)
        # 오른발이 몸 앞에 짚였다가(S(f)-Send<0) 몸이 멈추면 0 → 왼발 위치 0과 같아진다
        w = sm(f / 3)
        dz = (1 - w) * dz_run(11 + f) + w * (1 - sm(f / 13)) * (-0.14 - 0.07 * math.sin(math.pi * min(f, 6) / 6))
        lean = LEAN * (1 - sm(f / 10)) - 9.0 * math.sin(math.pi * min(f / 10, 1.0))
        su = 1 - sm(f / 13)
        spec, _ = compose(idle_a, dz, -0.02 * (1 - sm(f / 13)), lean, {"L": L, "R": R}, su)
        keys.append((f, spec)); contact["R"].append(f >= 2); contact["L"].append(f >= 8)
    return keys, {"v": v, "S": S, "contact": contact}

def knots(pts, f):
    """(프레임, 값) 점들 사이를 코사인으로 부드럽게 잇는다."""
    if f <= pts[0][0]: return pts[0][1]
    for (f0, a), (f1, b) in zip(pts, pts[1:]):
        if f0 <= f <= f1: return a + (b - a) * 0.5 * (1 - math.cos(math.pi * (f - f0) / (f1 - f0)))
    return pts[-1][1]

def mk_turn180(idle_a, sign=1):
    """제자리 180도 돌기 12프레임. 몸 전체 회전(0.1초=6프레임)은 코드가 Root로 돌리고, 이 동작은 '머리→가슴이 먼저 돌아가고 골반이 따라오는' 시차와 도포 펄럭임만 더한다.
    sign=+1 왼쪽으로 돎, -1 오른쪽으로 돎."""
    N = 12; yaw = [180.0 / 0.1 if f < 6 else 0.0 for f in range(N + 1)]     # 도/초 (보조 뼈가 읽는다)
    chest = [(0, 0), (2, 20), (4, 16), (7, -5), (10, 2), (12, 0)]; head = [(0, 0), (2, 35), (4, 22), (7, -8), (10, 3), (12, 0)]
    keys, contact = [], {"L": [], "R": []}
    feet = {"L": (0.0, ANK, 0.0), "R": (0.0, ANK, 0.0)}
    for f in range(N + 1):
        spec, _ = compose(idle_a, -0.07 * math.sin(math.pi * min(f / 9, 1.0)), 0.0, 4.0 * math.sin(math.pi * f / N), feet, 0.0)
        c, h = knots(chest, f) * sign, knots(head, f) * sign
        fl = 16 * math.sin(math.pi * min(f / 8, 1.0))      # 소매가 벌어지는 정도
        spec["Spine"] = {"r": (0, 0, c * 0.4)}; spec["Chest"] = {"r": (0, 0, c * 0.6)}; spec["Head"] = {"r": (0, 0, h - c)}
        spec["UpperArm.L"] = {"r": (0, -2 - fl, 0)}; spec["UpperArm.R"] = {"r": (0, 2 + fl, 0)}
        keys.append((f, spec)); contact["L"].append(True); contact["R"].append(True)
    return keys, {"v": [0.0] * (N + 1), "S": [0.0] * (N + 1), "contact": contact, "yaw": [y * sign for y in yaw], "pivot": True}

def roll_travel(vmid, N=18):
    v = []
    for f in range(N + 1):
        if f <= 3: v.append(V + (vmid - V) * sm(f / 3))
        elif f <= 14: v.append(vmid)
        else: v.append(vmid + (V - vmid) * sm((f - 14) / 4))
    return v

def mk_roll(idle_a, mesh, arm):
    """회피 구르기 18프레임(0.3초) = 명세 §3-2(거리 4m, 0.3초, 무적 0.2초=12프레임).
    0~3 웅크리며 파고듦 → 3~14 몸을 웅크린 채 앞으로 한 바퀴(360도) → 14~18 일어서며 Run 0번 자세로 끝(바로 달리기로 이어진다).
    구르는 동안 Root 뼈를 뒤집으며 땅에 몸이 파묻히지 않게 높이를 자동으로 보정한다."""
    N = 18
    lo, hi = 0.0, 40.0
    for _ in range(40):                      # 이동 거리가 정확히 4.0m가 되는 중간 속도 이분 탐색
        mid = (lo + hi) / 2
        if trapezoid(roll_travel(mid))[-1] < 4.0: lo = mid
        else: hi = mid
    v = roll_travel(lo); S = trapezoid(v)
    run0, _ = compose(idle_a, dz_run(0), -0.02, LEAN, {s: run_foot(s, 0)[:3] for s in "LR"}, 1.0)
    TUCK = {"Hips": {"r": (24, 0, 0), "l": (0, -0.04, -0.30)}, "Spine": {"r": (14, 0, 0)}, "Chest": {"r": (30, 0, 0)}, "Neck": {"r": (10, 0, 0)}, "Head": {"r": (22, 0, 0)},
            "UpperArm.L": {"r": (-95, -20, 0)}, "UpperArm.R": {"r": (-95, 20, 0)}, "Hand.L": {"r": (-50, 0, 0)}, "Hand.R": {"r": (-50, 0, 0)},
            "UpperLeg.L": {"r": (-124, 0, 0)}, "UpperLeg.R": {"r": (-124, 0, 0)}, "LowerLeg.L": {"r": (125, 0, 0)}, "LowerLeg.R": {"r": (125, 0, 0)},
            "Foot.L": {"r": (30, 0, 0)}, "Foot.R": {"r": (30, 0, 0)}}
    P = (-0.05, 0.6)     # 구르는 중심(y,z)
    keys = []; lifts = []
    for f in range(N + 1):
        tk = sm(f / 3) if f <= 3 else (1.0 if f <= 14 else sm((N - f) / 4))
        spec = lerp_spec(run0, TUCK, tk)
        th = 0.0 if f <= 3 else (360.0 * knots([(3, 0.0), (14, 1.0)], f) if f < 14 else 0.0)
        c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
        ry_, rz_ = P[0] * c - P[1] * s_, P[0] * s_ + P[1] * c
        loc = [0.0, P[0] - ry_, P[1] - rz_]
        spec["Root"] = {"r": (th, 0, 0), "l": tuple(loc)}
        # 땅 보정: 이 자세에서 가장 낮은 점이 바닥(0)에 딱 닿게 Root를 위아래로 옮긴다(구르는 동안만)
        if 3 <= f <= 14:
            for pb in arm.pose.bones: _apply(pb, spec.get(pb.name, {}))
            bpy.context.view_layer.update()
            ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
            mz = min((ev.matrix_world @ vv.co).z for vv in me.vertices); ev.to_mesh_clear()
            w = sm((f - 3) / 1.5) * sm((14 - f) / 1.5) if f not in (3, 14) else 0.0
            lifts.append(((0.01 - mz) * w)); spec["Root"]["l"] = (0.0, loc[1], loc[2] + (0.01 - mz) * w)
        keys.append((f, spec))
    for pb in arm.pose.bones: _apply(pb, {})
    return keys, {"v": v, "S": S, "contact": {"L": [False] * (N + 1), "R": [False] * (N + 1)}, "sec_gain": 0.3, "roll_lift_max_m": round(max(lifts), 3) if lifts else 0.0, "roll_v_mid": round(lo, 2)}

def clips(idle_a, mesh, arm):
    """이름 → (키, 보간, 반복?, 사건, 메타). 메타는 보조 뼈 굽기와 발 미끄러짐 검사가 읽는다."""
    C = {}
    k, m = mk_run(idle_a); C["Run"] = (k, "LINEAR", True, {"cycle_frames": CYC, "contact_L": [0, LAST_ST], "contact_R": [15, 15 + LAST_ST]}, m)
    k, m = mk_run(idle_a, 12.0); C["Run_TurnL"] = (k, "LINEAR", True, {"cycle_frames": CYC, "bank_deg": 12}, {**m, "yaw": [150.0] * (CYC + 1)})
    k, m = mk_run(idle_a, -12.0); C["Run_TurnR"] = (k, "LINEAR", True, {"cycle_frames": CYC, "bank_deg": -12}, {**m, "yaw": [-150.0] * (CYC + 1)})
    k, m = mk_start(idle_a); C["Run_Start"] = (k, "LINEAR", False, {"ends_as_run_frame": 0, "play_frames": 10, "full_speed_frame": 5}, m)
    k, m = mk_stop(idle_a); C["Run_Stop"] = (k, "LINEAR", False, {"starts_from_run_frame": 11, "stopped_frame": 4, "plant_frame": 2}, m)
    k, m = mk_turn180(idle_a, 1); C["Turn180_L"] = (k, "LINEAR", False, {"root_turn_frames": 6, "settle_frame": 10}, m)
    k, m = mk_turn180(idle_a, -1); C["Turn180_R"] = (k, "LINEAR", False, {"root_turn_frames": 6, "settle_frame": 10}, m)
    k, m = mk_roll(idle_a, mesh, arm); C["Roll"] = (k, "LINEAR", False, {"iframe_start": 2, "iframe_end": 14, "travel_m": 4.0, "roll_start": 3, "roll_end": 14}, m)
    return C

# ───────────────────────── 보조 뼈 흔들림 굽기 ─────────────────────────
def _lim(x, a, b): return max(a, min(b, x))

class Spring:
    """각도 하나를 목표로 끌어당기는 스프링-댐퍼(흔들리다 가라앉는 움직임). 4번 쪼개 풀어 안정."""
    def __init__(self, hz, zeta): self.w = 2 * math.pi * hz; self.z = zeta; self.x = 0.0; self.v = 0.0
    def step(self, target, dt=1.0 / FPS, sub=4):
        h = dt / sub
        for _ in range(sub):
            acc = self.w * self.w * (target - self.x) - 2 * self.z * self.w * self.v
            self.v += acc * h; self.x += self.v * h
        return self.x

def _angles(pb):
    t, h = pb.tail, pb.head; d = t - h
    return d

def bake_secondary(arm, act, meta, f0, f1, kA=0.3):
    """완성된 동작을 한 프레임씩 읽어 몸이 어떻게 움직이는지(앞뒤·좌우·위아래 가속, 허벅지 각도, 몸 기울기, 달리는 바람, 돎)를 구하고,
    도포 자락 4개·갓끈 4개·허리띠 끝 3개·노리개 술이 스프링으로 따라 흔들리는 값을 매 프레임 키로 굽는다.
    Unity에서는 이 키가 그대로 재생되므로 코드가 따로 할 일은 없다(실시간 물리를 쓰고 싶으면 같은 뼈에 스프링 본을 붙이면 된다)."""
    sc = bpy.context.scene; fr = list(range(int(f0), int(f1) + 1)); n = len(fr)
    g = meta.get("sec_gain", 1.0); v = meta.get("v") or [0.0] * n; S = meta.get("S") or [0.0] * n; yaw = meta.get("yaw") or [0.0] * n
    P = arm.pose.bones; samp = []
    for f in fr:
        sc.frame_set(f); bpy.context.view_layer.update()
        hp, hd = P["Hips"].head.copy(), P["Hips"].tail - P["Hips"].head
        hh, hhd = P["Head"].head.copy(), P["Head"].tail - P["Head"].head
        tl, tr = P["UpperLeg.L"].tail - P["UpperLeg.L"].head, P["UpperLeg.R"].tail - P["UpperLeg.R"].head
        samp.append({"hp": hp, "hh": hh, "hpitch": math.degrees(math.atan2(-hd.y, hd.z)), "hroll": math.degrees(math.atan2(hd.x, hd.z)),
                     "pitch": math.degrees(math.atan2(-hhd.y, hhd.z)), "aL": math.degrees(math.atan2(tl.y, -tl.z)), "aR": math.degrees(math.atan2(tr.y, -tr.z))})
    def acc(key, axis, sign=1.0):
        pos = [sign * getattr(s[key], axis) for s in samp]
        return [(pos[min(i + 1, n - 1)] - 2 * pos[i] + pos[max(i - 1, 0)]) * FPS * FPS for i in range(n)]
    # 앞쪽 가속 = 몸이 앞(-y)으로 가속하는 정도. 이동(root)분은 속도표(v)에서 더한다.
    dv = [(v[min(i + 1, n - 1)] - v[max(i - 1, 0)]) * FPS / (2 if 0 < i < n - 1 else 1) for i in range(n)]
    afH = [a + d for a, d in zip(acc("hp", "y", -1.0), dv)]; afD = [a + d for a, d in zip(acc("hh", "y", -1.0), dv)]
    alH = acc("hp", "x"); alD = acc("hh", "x"); azH = acc("hp", "z")
    alH = [a + v[i] * math.radians(yaw[i]) for i, a in enumerate(alH)]; alD = [a + v[i] * math.radians(yaw[i]) for i, a in enumerate(alD)]
    SK = {b: [Spring(3.4, 0.30), Spring(3.4, 0.30)] for b in ("Skirt_F", "Skirt_B", "Skirt_L", "Skirt_R")}
    ST = {b: [Spring(3.1, 0.28), Spring(3.1, 0.28)] for b in ("Strap.L1", "Strap.R1")}; ST.update({b: [Spring(4.6, 0.22), Spring(4.6, 0.22)] for b in ("Strap.L2", "Strap.R2")})
    SA = {"SashA1": [Spring(3.8, 0.3), Spring(3.8, 0.3)], "SashA2": [Spring(4.6, 0.26), Spring(4.6, 0.26)], "SashB1": [Spring(4.0, 0.3), Spring(4.0, 0.3)], "Orn": [Spring(5.0, 0.25), Spring(5.0, 0.25)]}
    # 처음 상태: 첫 프레임 목표에 이미 맞춰 둔다(동작이 시작될 때 튀지 않게)
    out = {b: [] for b in list(SK) + list(ST) + list(SA)}
    def targets(i):
        s = samp[i]; w = v[i] / V; af, al, az = afH[i] * g, alH[i] * g, azH[i] * g
        aL, aR = s["aL"], s["aR"]; hp, hr = _lim(s["hpitch"], -25, 25), _lim(s["hroll"], -25, 25)   # 구르기처럼 몸이 뒤집힐 때 보정값이 폭주하지 않게 제한
        spin = math.radians(yaw[i]) * g * 0.0
        t = {}
        fl = _lim(-0.5 * az / 9.8 * 9.8 * 0.05, -12, 12)       # 아래로 확 내려앉으면 자락이 위로 들려 벌어진다
        base_rx = _lim(kA * af, -22, 22) - 0.6 * hp
        base_ry = _lim(0.45 * al, -18, 18) - 0.6 * hr
        t["Skirt_F"] = (_lim(base_rx + 3 * w + 0.55 * min(aL, aR, 0) - fl, -26, 10), _lim(base_ry, -20, 20) + 0.0)
        t["Skirt_B"] = (_lim(base_rx + 14 * w + 0.5 * max(aL, aR, 0) + fl, -6, 28), _lim(base_ry, -20, 20))
        t["Skirt_L"] = (_lim(base_rx + 9 * w + 0.28 * aL, -22, 24), _lim(base_ry - fl * 0.8, -26, 14))
        t["Skirt_R"] = (_lim(base_rx + 9 * w + 0.28 * aR, -22, 24), _lim(base_ry + fl * 0.8, -14, 26))
        for k in t: t[k] = (t[k][0] * (1 if g >= 0.99 else 0.7 + 0.3 * g), t[k][1])
        dH = afD[i] * g; dl = alD[i] * g
        hrx = _lim(0.5 * kA * dH + 3 * w - 0.8 * _lim(s["pitch"], -25, 25), -35, 6); hry = _lim(0.35 * dl, -22, 22) - 0.5 * hr
        for sd in "LR":
            t[f"Strap.{sd}1"] = (hrx, hry); t[f"Strap.{sd}2"] = (_lim(hrx * 1.35, -45, 8), _lim(hry * 1.3, -30, 30))
        sx = _lim(0.5 * kA * af + 2 * w - 0.5 * hp, -14, 7); sy = _lim(0.3 * al, -14, 14) - 0.4 * hr
        t["SashA1"] = (sx, sy); t["SashA2"] = (_lim(sx * 1.4, -20, 9), _lim(sy * 1.3, -20, 20)); t["SashB1"] = (_lim(sx * 1.2, -16, 8), _lim(sy * 1.2, -18, 18))
        t["Orn"] = (_lim(0.7 * kA * af - 0.5 * hp, -22, 8), _lim(0.5 * al, -22, 22) - 0.5 * hr)
        return t
    t0 = targets(0)
    for b, sp in {**SK, **ST, **SA}.items():
        sp[0].x, sp[1].x = t0[b]
    for i, f in enumerate(fr):
        t = targets(i)
        for b, sp in {**SK, **ST, **SA}.items():
            # 두 번째 마디(…2)는 첫 마디가 흔들리는 만큼 한 박자 늦게 따라오도록 첫 마디 각도를 목표에 반영
            tx, ty = t[b]
            if b in ("Strap.L2", "Strap.R2", "SashA2"):
                par = {"Strap.L2": "Strap.L1", "Strap.R2": "Strap.R1", "SashA2": "SashA1"}[b]
                tx += 0.5 * (out[par][-1][0] - t[par][0]) if out[par] else 0.0
            out[b].append((sp[0].step(tx), sp[1].step(ty)))
    ad = arm.animation_data
    for i, f in enumerate(fr):
        for b in out:
            pb = P[b]; rx, ry = out[b][i]
            _apply(pb, {"r": (_lim(rx, -50, 50), _lim(ry, -40, 40), 0)})
            pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f); pb.keyframe_insert("scale", frame=f)
    for pb in P: _apply(pb, {})
    return {b: {"rx_max": round(max(abs(x[0]) for x in out[b]), 1), "ry_max": round(max(abs(x[1]) for x in out[b]), 1)} for b in out}

# ───────────────────────── 발 미끄러짐 검사 ─────────────────────────
def measure_slide(arm, act, meta, f0, f1):
    """땅에 닿은 발끝(Foot 뼈 tail)의 '세계 앞뒤 위치'(= 몸 기준 y - 이동 거리 S)가 프레임 사이에 얼마나 움직이는지 잰다. 0이면 완전히 안 미끄러짐."""
    sc = bpy.context.scene; ad = arm.animation_data; ad.use_nla = False; ad.action = act
    S = meta.get("S"); c = meta.get("contact")
    if S is None or c is None: ad.action = None; ad.use_nla = True; return None
    pos = {"L": [], "R": []}
    for f in range(int(f0), int(f1) + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        for s in "LR": pos[s].append((arm.pose.bones[f"Foot.{s}"].tail.y,))
    ad.action = None; ad.use_nla = True
    worst, tot, cnt = 0.0, 0.0, 0
    for s in "LR":
        for i in range(len(pos[s]) - 1):
            if c[s][i] and c[s][i + 1]:
                # 월드 y = 몸 기준 y + Root 위치(앞이 -y 이므로 -S). 닿은 발은 이게 변하면 안 된다.
                w0 = pos[s][i][0] - S[i]; w1 = pos[s][i + 1][0] - S[i + 1]
                d = abs(w1 - w0) * 1000; worst = max(worst, d); tot += d; cnt += 1
    return {"max_mm_per_frame": round(worst, 2), "mean_mm_per_frame": round(tot / cnt, 3) if cnt else 0.0, "contact_pairs": cnt}

def implied_speed(arm, act, f0, f1):
    """동작만 보고 '발이 미끄러지지 않으려면 몇 m/s로 가야 하나'를 구한다(걷기 같은 옛 동작의 권장 속도): 더 낮은 발끝의 뒤로 밀리는 속도 중앙값."""
    sc = bpy.context.scene; ad = arm.animation_data; ad.use_nla = False; ad.action = act
    ys, zs = [], []
    for f in range(int(f0), int(f1) + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        ys.append([arm.pose.bones[f"Foot.{s}"].tail.y for s in "LR"]); zs.append([arm.pose.bones[f"Foot.{s}"].tail.z for s in "LR"])
    ad.action = None; ad.use_nla = True
    sp = []
    for i in range(len(ys) - 1):
        k = 0 if zs[i][0] + zs[i + 1][0] < zs[i][1] + zs[i + 1][1] else 1
        if min(zs[i][k], zs[i + 1][k]) < 0.06: sp.append((ys[i + 1][k] - ys[i][k]) * FPS)
    sp.sort(); return round(sp[len(sp) // 2], 2) if sp else None
