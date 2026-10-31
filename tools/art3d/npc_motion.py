"""마을 사람(NPC) 일하는 동작·걸음·쪼그려 쉬기·놀람. npcs.py가 불러 쓴다.
공용(모두): Idle · Talk · Walk(사람마다 속도·보폭이 다르고 발이 안 미끄러짐) · SitDown/SquatRest/StandUp(쪼그려 쉬기) · Startle/StartleHold/StartleRecover(혼이 다가올 때 놀라 움츠림)
역할별: 대장장이 Hammer·Bellows, 우물가 DrawWater·Laundry, 흥정 Haggle·Hawk, 제사 Offer·Bow, 노래놀이 Play, 책 Read, 지킴 Guard·Stamp 등(ROLE 표).
좌표·부호는 anim.py 머리말과 같다. 길이는 키 1.0m 기준으로 짜고 키 배율 k를 곱해 쓴다(아이도 같은 모양, 보폭만 짧게).
팔 표기 (앞, 바깥, 굽힘) 도: 앞=앞으로 들어 올림, 바깥=옆으로 벌림, 굽힘=팔꿈치(손 뼈)를 앞으로 접음."""
import math
import hero_locomotion as hl
from hero_locomotion import ik, legs, sm, herm, ANK, L1, L2, lerp_spec

FPS = 60

def clamp(x, a, b): return max(a, min(b, x))

# ── 자세 도우미 ───────────────────────────────────────────────────────────────
def P(lean=0.0, twist=0.0, hn=0.0, hz=0.0, ht=0.0, R=(0, 0, 0), L=(0, 0, 0), dz=0.0, hy=0.0, hrx=0.0, hrz=0.0, hry=0.0, add=None):
    """윗몸 자세 하나. lean=가슴 앞숙임(+), twist=가슴 비틂, hn=머리 숙임(+), hz=머리 돌림, ht=머리 갸웃."""
    d = {"Spine": {"r": (lean * 0.3, 0, twist * 0.4)}, "Chest": {"r": (lean * 0.7, 0, twist * 0.6)}, "Head": {"r": (hn - lean - hrx, ht - hry, hz - twist - hrz)},
         "UpperArm.R": {"r": (-R[0], R[1], 0)}, "Hand.R": {"r": (-R[2], 0, 0)}, "UpperArm.L": {"r": (-L[0], -L[1], 0)}, "Hand.L": {"r": (-L[2], 0, 0)},
         "Hips": {"r": (hrx, hry, hrz), "l": (0, hy, dz)}}
    if add:
        for k, v in add.items(): d[k] = {**d.get(k, {}), **v}
    return d

STAND = {"UpperLeg.L": {"r": (0, 0, 0)}, "UpperLeg.R": {"r": (0, 0, 0)}}

def stand_legs(dz=0.0, hy=0.0, hrx=0.0, spread=0.0):
    """두 발을 제자리에 평평히 두고 골반 높이만 바꾼다(IK: 무릎이 알아서 굽는다)."""
    return legs(dz, hy, hrx, {"L": (0.0, ANK, 0.0), "R": (0.0, ANK, 0.0)})[0]

def full(upper, dz=0.0, hy=0.0, hrx=0.0, feet=None):
    """윗몸 자세 + 다리 IK."""
    feet = feet or {"L": (0.0, ANK, 0.0), "R": (0.0, ANK, 0.0)}
    spec = dict(upper); spec.update(legs(dz, hy, hrx, feet)[0]); h = dict(spec.get("Hips", {})); h["r"] = (hrx, h.get("r", (0, 0, 0))[1], h.get("r", (0, 0, 0))[2]); h["l"] = (0, hy, dz); spec["Hips"] = h
    return spec

def scale_keys(keys, k):
    """긴 단위(이동)를 키 배율 k로 키운다."""
    out = []
    for f, spec in keys:
        d = {}
        for b, v in spec.items():
            v = dict(v)
            if "l" in v: v["l"] = tuple(a * k for a in v["l"])
            d[b] = v
        out.append((f, d))
    return out

def loopfix(keys):
    keys = list(keys); keys[-1] = (keys[-1][0], keys[0][1]); return keys

# ── 걷기 (발 고정) ────────────────────────────────────────────────────────────
def walk(sl, N, lean=0.0, hold=None, swing=0.5, cover=False, bob_extra=0.0, heel=14.0, head_hn=0.0):
    """sl=한 걸음 길이(키 1.0m 기준 m), N=두 걸음 한 바퀴 프레임. 속도 = sl × 120/N (키 배율 전). 땅에 닿은 발은 몸이 간 만큼 정확히 뒤로 밀린다.
    hold={'R':(앞,바깥,굽힘)}: 그 팔은 흔들지 않고 고정(쟁반·물동이·지팡이 등). 골반 높이는 다리가 닿을 수 있는 한도 안에서 자동으로 정한다."""
    v = sl * 120.0 / N; VFn = v / FPS; Ts = round(0.60 * N); sw = N - Ts; sweep = VFn * Ts / 2
    def stance(g):
        fy = -sweep + VFn * g; psi = heel * sm((g - (Ts - 3)) / 3) if g > Ts - 3 else 0.0
        y, z = hl.pivot(fy, psi); return y, z, psi
    def foot(g):
        g %= N
        if g <= Ts: y, z, p = stance(g); return y, z, p, True
        u = (g - Ts) / sw; y0, z0, p0 = stance(Ts); ya, za, _ = stance(Ts - 0.1)
        m0y, m0z = (y0 - ya) / 0.1 * sw, (z0 - za) / 0.1 * sw
        y = herm(y0, m0y, -sweep, VFn * sw, u); z = herm(z0, m0z, ANK, 0.0, u) + 0.09 * math.sin(math.pi * u) ** 1.2
        return y, z, p0 * (1 - u) ** 2 - 6 * math.sin(math.pi * u) ** 2, False
    R_ = L1 + L2 - 0.02
    zs = []
    for f in range(N):
        lim = 9.0
        for off in (0, N // 2):
            y, z, _, c = foot(f - off)
            if c: lim = min(lim, z + math.sqrt(max(0.05, R_ * R_ - y * y)))
        zs.append(min(0.95 - 0.004, lim) - 0.95 + bob_extra)
    zs = [sum(zs[(i + j) % N] for j in range(-2, 3)) / 5 for i in range(N)]      # 5프레임 평균: 골반이 매끄럽게 출렁
    keys, contact = [], {"L": [], "R": []}; al_hist = []
    for f in range(N + 1):
        fi = f % N; fL = foot(f); fR = foot(f - N // 2)
        spec_l, al = legs(zs[fi], -0.0, lean * 0.4, {"L": fL[:3], "R": fR[:3]})
        aL, aR = al["L"], al["R"]; tw = clamp((aR - aL) / 40.0, -1, 1)
        arm = lambda a: clamp(swing * a, -35, 30)
        R = hold["R"] if hold and "R" in hold else (-arm(aL), 6, 0); L = hold["L"] if hold and "L" in hold else (-arm(aR), 6, 0)
        up = P(lean=lean * 0.6, twist=4.0 * tw, hn=head_hn, hz=-2.0 * tw, R=R, L=L, hrz=-2.5 * tw, hrx=lean * 0.4)
        sp = dict(up); sp.update(spec_l); sp["Hips"] = {"r": (lean * 0.4, 0, -2.5 * tw), "l": (0, 0, zs[fi])}
        keys.append((f, sp)); contact["L"].append(fL[3]); contact["R"].append(fR[3])
    return keys, {"speed_n": v, "contact": contact, "N": N, "sl": sl}

# ── 쪼그려 쉬기 ───────────────────────────────────────────────────────────────
SQ = dict(dz=-0.56, hy=0.10, hrx=18.0)
def squat_pose(arms=(55, 12, 30), lean=24.0, hn=-8.0, ht=0.0):
    up = P(lean=lean, hn=hn, ht=ht, R=arms, L=arms)
    return full(up, SQ["dz"], SQ["hy"], SQ["hrx"], {"L": (-0.10, ANK, 0.0), "R": (-0.10, ANK, 0.0)})

def sit_down(idle, N=30):
    """서 있다가 쪼그려 앉는다 30프레임: 먼저 몸을 살짝 숙이고(예비) 무릎을 접어 내려앉는다. 다리는 IK로 매 프레임 새로 풀어서 무릎이 어색하게 꺾이지 않는다."""
    keys = []
    for f in range(N + 1):
        tt = sm(f / N); pre = 8 * math.sin(math.pi * min(tt * 2, 1)) * (1 - tt)
        dz, hy, hrx = SQ["dz"] * tt, SQ["hy"] * tt, SQ["hrx"] * tt
        feet = {s: (-0.10 * tt, ANK, 0.0) for s in "LR"}
        up = P(lean=24 * tt + pre, hn=-8 * tt, R=(55 * tt, 12 * tt, 30 * tt), L=(55 * tt, 12 * tt, 30 * tt))
        keys.append((f, full(up, dz, hy, hrx, feet)))
    return keys

def squat_rest(N=120):
    out = []
    for f in range(N + 1):
        ph = math.sin(2 * math.pi * f / N)            # 숨쉬기(들썩)
        sway = math.sin(2 * math.pi * f / N * 2)
        out.append((f, squat_pose((55, 12, 30), 24 + 1.2 * ph, -8 + 2.0 * sway, 2.0 * sway)))
    return out

def stand_up(N=30):
    """일어서기 30프레임: 앉기를 거꾸로 돌린다(손으로 무릎을 짚듯 일어나는 느낌은 윗몸 숙임이 대신한다)."""
    return [(i, spec) for i, (_, spec) in enumerate(reversed(sit_down(None, N)))]

# ── 놀람(움츠림) ─────────────────────────────────────────────────────────────
def startle_pose(child=False, k=1.0):
    """혼이 가까이 올 때: 몸을 움츠리고 팔로 얼굴·가슴을 가리며 한 발 뒤로. 아이는 더 깊이 웅크리고 손으로 머리를 감싼다."""
    dz = -0.20 if child else -0.12
    arms = (95, 18, 120) if child else (70, 12, 105)
    up = P(lean=22 if child else 16, hn=14, hz=0, R=arms, L=arms, dz=dz, hy=0.04, hrx=6)
    return full(up, dz, 0.06, 6.0, {"L": (0.05, ANK, 0.0), "R": (-0.06, ANK, 0.0)})

def startle(idle, child):
    st = startle_pose(child); keys = [(0, idle)]
    over = lerp_spec(idle, st, 1.25)       # 순간 더 움츠렸다가(과장) 자리 잡는다
    keys += [(4, over), (8, lerp_spec(idle, st, 0.9)), (14, st), (22, st)]
    return keys, "BEZIER", False, {"flinch": 4, "end_pose_held": True}

def startle_hold(child):
    st = startle_pose(child); keys = []
    for f in range(0, 61, 3):
        tr = (1.2 if (f // 3) % 2 == 0 else -1.2) * (1.6 if child else 1.0)   # 덜덜 떨림
        a = {**st, "Chest": {"r": (st["Chest"]["r"][0] + tr * 0.6, 0, tr * 0.8)}, "Head": {"r": (st["Head"]["r"][0] - tr * 0.5, 0, tr)}}
        keys.append((f, a))
    return keys, "LINEAR", True, {}

def startle_recover(idle):
    st = startle_pose(False); keys = []
    for f in range(0, 37):
        t = sm(f / 36); a = lerp_spec(st, idle, t)
        # 안도의 한숨: 중간에 어깨가 한 번 크게 내려감
        a["Chest"] = {"r": (a["Chest"]["r"][0] + 3 * math.sin(math.pi * t), 0, a["Chest"]["r"][2])}
        keys.append((f, a))
    return keys, "LINEAR", False, {"sigh": 18}

# ── 역할 동작 ─────────────────────────────────────────────────────────────────
def cyc(N, fn, step=None):
    step = step or max(2, N // 24); fs = list(range(0, N, step)) + [N]
    return [(f, fn(f / N)) for f in fs]

TAU = 2 * math.pi
def hammer(idle):
    """망치질 54프레임(0.9초): 망치를 머리 위로 들었다가(0~14) 온몸으로 내리친다(20, 쾅) 튕겨 올림. 왼손은 집게로 쇠를 붙들고 있다."""
    def p(R, lean, dz, hn, L=(40, 12, 60)): return full(P(lean=lean, hn=hn, R=R, L=L, dz=dz, hy=-0.02 * (lean > 8)), dz, 0.0, 0.0)
    up = p((135, 8, 30), -8, 0.0, -2); hit = p((28, 6, 6), 18, -0.06, 16); mid = p((80, 8, 18), 6, -0.02, 6)
    return [(0, mid), (14, up), (18, lerp_spec(up, hit, 0.6)), (20, hit), (28, hit), (40, mid), (54, mid)], "BEZIER", True, {"hit": 20, "lift": 14}

def bellows(idle):
    """풀무질 72프레임: 두 팔을 번갈아 밀고 당겨 풀무를 누른다. 몸이 따라 출렁."""
    def f(t):
        a = math.sin(TAU * t); R = (40 + 28 * a, 12, 50 - 10 * a); L = (40 - 28 * a, 12, 50 + 10 * a)
        return full(P(lean=10 + 4 * a, twist=5 * a, hn=10, R=R, L=L, dz=-0.03), -0.03)
    return loopfix(cyc(72, f, 3)), "BEZIER", True, {"push": [18, 54]}

def draw_water(idle):
    """두레박 당기기 72프레임: 두 손을 번갈아 줄을 끌어올리며 몸을 뒤로 젖힌다."""
    def f(t):
        a = math.sin(TAU * t); R = (85 - 45 * max(a, 0) - 10 * min(a, 0), 8, 60); L = (60 + 35 * min(a, 0), 8, 55 + 25 * max(a, 0))
        pull = max(a, 0)
        return full(P(lean=-8 * pull + 4, hn=6, R=R, L=L, dz=-0.04, hy=0.03 * pull), -0.04, 0.03 * pull, 0)
    return loopfix(cyc(72, f, 3)), "BEZIER", True, {"pull": 18}

def laundry(idle):
    """빨래 48프레임: 쪼그려 앉아 두 손을 번갈아 빨랫감을 문지른다."""
    def f(t):
        a = math.sin(TAU * t * 2)
        return squat_pose((62 + 12 * a, 14, 34 - 8 * a), 30, 10)
    out = []
    for fr in range(0, 49, 3):
        t = fr / 48; a = math.sin(TAU * t * 2)
        arms_r = (62 + 12 * a, 14, 34 - 8 * a); arms_l = (62 - 12 * a, 14, 34 + 8 * a)
        up = P(lean=30, hn=10, R=arms_r, L=arms_l)
        out.append((fr, full(up, SQ["dz"], SQ["hy"], SQ["hrx"], {"L": (-0.10, ANK, 0.0), "R": (-0.10, ANK, 0.0)})))
    return loopfix(out), "LINEAR", True, {"scrub": [6, 18, 30, 42]}

def haggle(idle, free="both"):
    """흥정 96프레임: 손바닥을 펴 보이고(0~) 어깨를 으쓱하고(24) 한 손으로 값을 가리킨다(60). free: 쓸 수 있는 팔 R/L/both."""
    def arm(a, side):
        return a if free in ("both", side) else None
    def pose(R, L, lean, hn, ht, twist):
        R = R if free in ("both", "R") else (6, 6, 0); L = L if free in ("both", "L") else (6, 6, 0)
        return full(P(lean=lean, hn=hn, ht=ht, twist=twist, R=R, L=L), 0, 0, 0)
    A = pose((50, 30, 45), (42, 30, 45), 2, 4, 0, 0); B = pose((38, 48, 70), (34, 48, 70), -2, -4, 8, 4)
    C = pose((88, 10, 12), (20, 12, 20), 6, 6, -4, -4); D = pose((60, 36, 55), (60, 36, 55), 0, 2, -6, 3)
    return [(0, A), (24, B), (40, A), (60, C), (72, C), (84, D), (96, A)], "BEZIER", True, {"point": 60, "shrug": 24}

def hawk(idle):
    """엿장수 아이 호객 72프레임: 한 손을 입에 모아 외치고(0~30) 반대 손을 크게 흔든다(36~72). 고개를 젖힌다."""
    def f(t):
        s = math.sin(TAU * t * 2)
        R = (110, 14, 120) if t < 0.5 else (60, 40, 30); L = (30, 20, 20) if t < 0.5 else (130 + 14 * s, 30, 25)
        return full(P(lean=-4, hn=-10, R=R, L=L), 0, 0, 0)
    ks = [(0, f(0.0)), (12, f(0.17)), (24, f(0.33)), (34, f(0.47)), (40, f(0.55)), (52, f(0.72)), (62, f(0.86)), (72, f(0.0))]
    return ks, "BEZIER", True, {"shout": [12, 24]}

def wave_stick(idle):
    """엿 막대 흔들기 48프레임(오른손 소품): 막대를 위로 들고 좌우로 흔든다."""
    ks = []
    for fr in range(0, 49, 4):
        s = math.sin(TAU * fr / 48); ks.append((fr, full(P(lean=-2, hn=-6, ht=4 * s, R=(140 + 10 * s, 18 + 14 * s, 20), L=(10, 12, 0), dz=0.01 * abs(s)), 0.01 * abs(s))))
    return ks, "BEZIER", True, {}

def chant(idle):
    """선소리 72프레임: 오른손 요령(종)을 흔들며 고개를 젖혀 소리 낸다. 종은 12프레임마다 한 번(event ring)."""
    ks = []
    for fr in range(0, 73, 4):
        s = math.sin(TAU * fr / 12); b = max(0, math.sin(TAU * fr / 72))
        ks.append((fr, full(P(lean=-6 - 2 * b, hn=-12 * (0.4 + 0.6 * b), R=(105 + 12 * s, 10, 40 + 14 * s), L=(15, 22, 10), dz=-0.01 * b), -0.01 * b)))
    return ks, "LINEAR", True, {"ring": [0, 12, 24, 36, 48, 60]}

def ritual(idle):
    """무녀 손 비비기 120프레임: 두 손을 가슴 앞에 모아 비비다 60프레임에 깊이 절한다."""
    ks = []
    for fr in range(0, 121, 4):
        t = fr / 120; bow = max(0, math.sin(TAU * t)) ** 2 * 1.0; rub = math.sin(TAU * fr / 10)
        R = (62 + 5 * rub, -4, 100); L = (62 - 5 * rub, -4, 100)
        ks.append((fr, full(P(lean=6 + 26 * bow, hn=6 + 6 * bow, R=R, L=L, dz=-0.03 * bow), -0.03 * bow, 0.0, 8 * bow)))
    return loopfix(ks), "LINEAR", True, {"bow": 30}

def offer(idle):
    """제사 지내는 아들 120프레임: 향로를 두 손으로 받쳐 들고 조용히 선다. 30~90프레임 사이 천천히 고개를 숙인다."""
    ks = []
    for fr in range(0, 121, 4):
        t = fr / 120; b = sm(1 - abs(t * 2 - 1) * 1.6)
        ks.append((fr, full(P(lean=4 + 18 * b, hn=8 + 10 * b, R=(68, 6, 62), L=(58, 6, 70), dz=-0.02 * b), -0.02 * b)))
    return loopfix(ks), "LINEAR", True, {}

def bow(idle):
    """절하기 90프레임(비반복): 허리를 깊이 숙이고(30) 잠시 머문 뒤(50) 일어난다."""
    def p(b, k): return full(P(lean=b, hn=0, R=(50 * k, 6, 30 * k), L=(50 * k, 6, 30 * k), dz=-0.05 * k), -0.05 * k, 0, 6 * k)
    return [(0, idle), (30, p(55, 1)), (56, p(55, 1)), (90, idle)], "BEZIER", False, {"deepest": 30}

def play(idle):
    """노래놀이 48프레임: 손뼉 치며(10, 34) 제자리에서 깡충 뛴다(24프레임쯤 공중)."""
    ks = []
    for fr in range(0, 49, 2):
        t = fr / 48; air = max(0, math.sin(TAU * t)) ** 0.8; crouch = max(0, -math.sin(TAU * t)) * 0.6
        dz = 0.04 * air - 0.07 * crouch
        feet = {s: (0.0, ANK + 0.12 * air, 8.0 * air) for s in "LR"}
        clap = max(0, math.cos(TAU * (t * 2 - 0.2))) ** 6
        R = (50 + 25 * clap, 4 + 20 * (1 - clap), 80); L = R
        ks.append((fr, full(P(lean=-2 * air + 6 * crouch, hn=-4 * air, R=R, L=L, dz=dz), dz, 0.0, 0.0, feet)))
    return loopfix(ks), "LINEAR", True, {"clap": [10, 34], "jump": 24}

def read(idle):
    """책 읽기 120프레임(왼손 책): 책을 가슴 앞에 들고 고개를 숙였다 들며 몸을 앞뒤로 흔든다. 60프레임에 오른손으로 장을 넘긴다."""
    ks = []
    for fr in range(0, 121, 4):
        t = fr / 120; s = math.sin(TAU * t * 2); turn = max(0, math.sin(TAU * (t - 0.5))) ** 2
        ks.append((fr, full(P(lean=4 + 3 * s, hn=16 + 4 * s, R=(70 + 20 * turn, 14 - 10 * turn, 90 - 40 * turn), L=(58, 4, 100), twist=1.5 * s), 0)))
    return loopfix(ks), "LINEAR", True, {"page_turn": 60}

def guard(idle, tool="keys"):
    """지키기 240프레임: 꼿꼿이 서서 천천히 좌우를 둘러본다(머리 -22°~+22°). 가끔 체중을 옮긴다."""
    ks = []
    for fr in range(0, 241, 8):
        t = fr / 240; hz = 22 * math.sin(TAU * t); sh = math.sin(TAU * t * 2)
        R = (24, 8, 40) if tool == "staff" else (30, 6, 60)
        ks.append((fr, full(P(lean=-2, hn=0, hz=hz, R=R, L=(4, 8, 0), twist=0.0, hrz=-1.5 * sh), 0.0, 0.0, 0)))
    return loopfix(ks), "LINEAR", True, {}

def stamp(idle):
    """곤장 내려찍기 42프레임(사령): 곤장을 들어(0~20) 땅에 쾅(24) 찍고 버틴다."""
    up = full(P(lean=-4, R=(110, 6, 30), L=(30, 14, 40), dz=0), 0); dn = full(P(lean=14, hn=8, R=(35, 6, 10), L=(30, 14, 40), dz=-0.05), -0.05)
    return [(0, idle), (18, up), (24, dn), (34, dn), (42, idle)], "BEZIER", False, {"hit": 24}

def mix(idle):
    """약 짓기 72프레임: 상 앞에서 두 손으로 약재를 갈고 봉지를 접는다. 고개를 숙여 들여다본다."""
    ks = []
    for fr in range(0, 73, 4):
        t = fr / 72; a = math.sin(TAU * t * 2); b = math.cos(TAU * t * 2)
        ks.append((fr, full(P(lean=14, hn=20, R=(55 + 8 * a, 6, 80 + 10 * b), L=(50 - 8 * a, 6, 75 - 10 * b), twist=2 * a), 0)))
    return loopfix(ks), "LINEAR", True, {}

def serve(idle):
    """쟁반 들고 서기 120프레임: 오른팔로 쟁반을 가슴 앞에 받치고 왼손은 가끔 머리를 매만진다."""
    ks = []
    for fr in range(0, 121, 8):
        t = fr / 120; s = math.sin(TAU * t); hair = max(0, math.sin(TAU * t * 1.0 - 1.6)) ** 3
        ks.append((fr, full(P(lean=1, hn=2 + 3 * s, hz=6 * s, R=(70, 6, 60), L=(12 + 80 * hair, 10 + 10 * hair, 20 + 100 * hair)), 0)))
    return loopfix(ks), "LINEAR", True, {}

def rope(idle):
    """줄배 줄 감기 60프레임: 왼손에 쥔 줄 타래에 오른손으로 줄을 당겨 감는다."""
    ks = []
    for fr in range(0, 61, 4):
        t = fr / 60; s = math.sin(TAU * t); pull = max(0, math.sin(TAU * t))
        ks.append((fr, full(P(lean=6 + 3 * pull, hn=10, R=(30 + 60 * pull, 14 - 6 * pull, 20 + 80 * pull), L=(54, 8, 62)), 0)))
    return loopfix(ks), "LINEAR", True, {"pull": 15}

def reins(idle):
    """덕만 고삐 96프레임: 고삐를 쥔 오른손으로 버티며 몸을 뒤로 젖히고, 왼손은 허리에 얹는다."""
    ks = []
    for fr in range(0, 97, 6):
        t = fr / 96; s = math.sin(TAU * t * 2)
        ks.append((fr, full(P(lean=-7 + 2 * s, hn=-2, R=(58 + 8 * s, 14, 28), L=(8, 44, 100), dz=-0.03, hy=0.03 + 0.01 * s), -0.03, 0.03 + 0.01 * s, 0)))
    return loopfix(ks), "LINEAR", True, {}


def reach_up(idle):
    """위로 손 뻗어 매달기 96프레임(순임 천 묶기·섭섭이 등 걸기): 발끝을 세우듯 몸을 늘여 두 팔을 머리 위로 올려 걸고(40) 손을 거두어 내린다."""
    def p(a, up, hn): return full(P(lean=-4 * up, hn=hn, R=(a, 8, 50 * up), L=(a * 0.9, 8, 40 * up), dz=0.015 * up), 0.015 * up, 0, 0)
    hi = p(150, 1, -14); lo = p(60, 0.4, 4)
    return [(0, idle), (22, lo), (40, hi), (46, p(158, 1, -14)), (52, hi), (64, hi), (84, lo), (96, idle)], "BEZIER", False, {"tie": 46}

def doze(idle):
    """졸기 240프레임(옥지기): 서서 꾸벅꾸벅. 고개가 천천히 떨어지다(0~130) 퍼뜩 올라오고(140, 깜짝) 다시 천천히 떨어진다."""
    def sink(fr):
        if fr < 134: return sm(fr / 134)
        if fr < 146: return 1 - sm((fr - 134) / 12) * 1.0
        return sm((fr - 146) / 94) * 0.8
    ks = []
    for fr in range(0, 241, 6):
        d = sink(fr); ks.append((fr, full(P(lean=6 * d, hn=48 * d, ht=4 * d, R=(22, 8, 40), L=(4, 8, 0)), 0)))
    ks[-1] = (240, ks[0][1])
    return ks, "LINEAR", True, {"jerk": 140}

def scribble(idle):
    """쪼그려 앉아 막대로 흙에 글씨 쓰기 96프레임(노경수 손주): 막대 든 오른팔로 획을 긋고 고개를 갸웃한다."""
    ks = []
    for fr in range(0, 97, 4):
        t = fr / 96; s = math.sin(TAU * t * 3); c = math.cos(TAU * t * 3)
        ks.append((fr, full(P(lean=28, hn=12 + 3 * s, ht=3 * c, R=(70 + 10 * s, 14 + 12 * c, 20), L=(40, 18, 30)), SQ["dz"], SQ["hy"], SQ["hrx"], {"L": (-0.10, ANK, 0.0), "R": (-0.10, ANK, 0.0)})))
    return loopfix(ks), "LINEAR", True, {"stroke": [10, 42, 74]}

def read_notice(idle):
    """방(榜) 읽기 120프레임(사령): 방을 한 손에 펼쳐 들고 가슴을 펴 소리 내어 읽는다. 끝에서 방을 접어 내린다."""
    ks = []
    for fr in range(0, 121, 6):
        t = fr / 120; talk = abs(math.sin(TAU * t * 5)); fold = sm((t - 0.85) / 0.15)
        ks.append((fr, full(P(lean=-3, hn=-4 + 8 * fold + 3 * talk, hz=5 * math.sin(TAU * t), R=(75 - 40 * fold, 8, 55 - 30 * fold), L=(24, 12, 20), twist=1.5 * math.sin(TAU * t)), 0)))
    return loopfix(ks), "LINEAR", True, {"read": [0, 60]}

def place_bowl(idle):
    """쪼그려 사발 놓기 96프레임(은실): 앉아서 두 손으로 사발을 섬돌에 내려놓고(40) 손을 모아 잠시 머문다(64)."""
    def p(R, L, lean, hn): return full(P(lean=lean, hn=hn, R=R, L=L), SQ["dz"], SQ["hy"], SQ["hrx"], {"L": (-0.10, ANK, 0.0), "R": (-0.10, ANK, 0.0)})
    a = p((70, 10, 70), (66, 10, 70), 26, 4); b = p((92, 8, 40), (88, 8, 40), 34, 12); c = p((50, 12, 20), (50, 12, 20), 26, 8)
    return [(0, a), (30, b), (40, b), (56, c), (84, c), (96, a)], "BEZIER", True, {"set_down": 40}

def tap_pipe(idle):
    """담뱃대 털기 96프레임(갑술 영감): 담뱃대를 입에서 빼 무릎에 톡톡 턴다(40, 52) 후 한숨."""
    ks = []
    for fr in range(0, 97, 4):
        t = fr / 96; tap = max(0, math.sin(TAU * (t - 0.35) * 5)) if 0.35 < t < 0.6 else 0.0
        R = (90 - 55 * tap - 20 * (1 if 0.3 < t < 0.65 else 0), 10, 70 - 30 * tap) if True else None
        ks.append((fr, full(P(lean=8 + 3 * tap, hn=14, R=R, L=(14, 8, 10)), 0)))
    return loopfix(ks), "LINEAR", True, {"tap": [44, 52]}

def open_fan(idle):
    """부러진 부채 펼쳐 보기 150프레임(당할미): 두 손으로 부채를 가슴 앞에 펴 들고 살을 하나씩 세다(60) 한숨 쉬며 접는다."""
    ks = []
    for fr in range(0, 151, 6):
        t = fr / 150; cnt = max(0, math.sin(TAU * t * 6)) * (1 if 0.25 < t < 0.7 else 0); sigh = max(0, math.sin(math.pi * (t - 0.7) / 0.2)) if 0.7 < t < 0.9 else 0
        ks.append((fr, full(P(lean=8 + 4 * sigh, hn=16 - 4 * cnt + 4 * sigh, R=(60, 10, 80 + 10 * cnt), L=(62, 10, 70)), 0)))
    return loopfix(ks), "LINEAR", True, {"count": [30, 50, 70, 90]}

def squat_coil(idle):
    """쪼그려 앉아 고삐 감기 72프레임(덕만, 둑에 앉아): 오른손으로 고삐를 끌어 왼팔에 둥글게 감는다."""
    ks = []
    for fr in range(0, 73, 4):
        t = fr / 72; pull = max(0, math.sin(TAU * t)); 
        ks.append((fr, full(P(lean=26, hn=10, R=(40 + 40 * pull, 12 - 6 * pull, 40 + 60 * pull), L=(66, 6, 70)), SQ["dz"], SQ["hy"], SQ["hrx"], {"L": (-0.10, ANK, 0.0), "R": (-0.10, ANK, 0.0)})))
    return loopfix(ks), "LINEAR", True, {"pull": 18}

# ── 사람별 표 ─────────────────────────────────────────────────────────────────
# 걸음: (보폭 sl[키1.0m 기준], 두 걸음 프레임 N, 앞기울기, 고정 팔, 흔들기 세기)
def walk_preset(s, cover):
    sid = s["id"]; child = s.get("child"); props = s.get("props", [])
    if s.get("walk"): return dict(s["walk"])                  # 명세가 걸음을 직접 정한 경우(애도객: 느린 행렬·상여 메기)
    if "jar_on_head" in props: return dict(sl=0.46, N=70, lean=0, hold={"R": (150, 20, 20)}, swing=0.35, head_hn=-2)       # 물동이 이고(오른팔로 받침)
    if "tray" in props: return dict(sl=0.46, N=64, lean=0, hold={"R": (70, 6, 60)}, swing=0.4)                                 # 쟁반 받침
    if "jige" in props: return dict(sl=0.50, N=68, lean=10, hold={"R": (25, 18, 70), "L": (25, 18, 70)}, swing=0.2)            # 지게 끈 쥐고
    if "bundle" in props: return dict(sl=0.55, N=64, lean=4, hold={"R": (25, 6, 20)}, swing=0.4)                               # 지팡이
    if s.get("hunch"): return dict(sl=0.40, N=76, lean=12, hold={"R": (22, 6, 15)} if "bell" not in props else None, swing=0.35)  # 구부정한 노인
    if child: return dict(sl=0.55, N=46, lean=2, swing=0.7, heel=18.0)
    if cover: return dict(sl=0.46, N=62, lean=1, swing=0.4)                                                                    # 치마·도포: 걸음 좁게
    return dict(sl=0.62, N=64, lean=2, swing=0.55)

# ── 장례·제사 동작(애도객 전용 + 마을 사람 공용 Weep·MournStand) ────────────────────────────
def weep(idle, child=False):
    """곡(哭) 서서 울기 120프레임 반복: 두 손으로 얼굴을 가리고 어깨를 떨며 두 번 크게 흐느낀다.
    왜: 대사 없이 슬픔을 전하려면 '얼굴 가린 손 + 떨리는 어깨'가 가장 멀리서도 읽힌다(쿼터뷰에서 얼굴 표정은 안 보인다). 이벤트 sob=흐느낌 순간(곡 소리 맞춤)."""
    ks = []
    for fr in range(0, 121, 3):
        t = fr / 120; sob = max(0.0, math.sin(TAU * 2 * t)) ** 2; trem = math.sin(TAU * 14 * t) * (0.4 + 1.6 * sob)
        arms = (96 + 3 * sob, 6, 128 + 4 * sob)
        up = P(lean=12 + 14 * sob + (4 if child else 0), hn=20 + 12 * sob, R=arms, L=arms, twist=1.4 * trem)
        up["Chest"] = {"r": (up["Chest"]["r"][0] + 2.2 * trem * 0.5, 0, up["Chest"]["r"][2] + 2.6 * trem)}
        ks.append((fr, full(up, -0.02 * sob)))
    return loopfix(ks), "LINEAR", True, {"sob": 22}

def mourn_stand(idle):
    """고개 숙이고 서 있기 180프레임 반복: 두 손을 모으고 고개를 떨군 채 숨만 쉰다. 100프레임쯤 오른손 손등으로 눈가를 한 번 훔친다.
    왜: 장례 행렬 옆·노제 구경에 서 있는 마을 사람 모두가 쓰는 '조용한 애도'. 우는 사람(Weep) 사이에 이게 섞여야 장면이 단조롭지 않다."""
    ks = []
    for fr in range(0, 181, 4):
        t = fr / 180; br = math.sin(TAU * t * 2); wipe = max(0.0, math.sin(math.pi * (t - 0.52) / 0.16)) if 0.52 <= t <= 0.68 else 0.0
        R = (60 + 38 * wipe, 6 - 4 * wipe, 92 + 36 * wipe); L = (58, 6, 88)
        ks.append((fr, full(P(lean=7 + 1.0 * br + 3 * wipe, hn=18 + 1.5 * br + 4 * wipe, R=R, L=L), 0)))
    return loopfix(ks), "LINEAR", True, {"wipe": 100}

def wail(idle):
    """애고곡(주저앉아 우는 곡) 150프레임 반복: 쪼그려 앉은 채 앞으로 엎드려 한 손으로 땅을 치며 운다(SitDown → Wail → StandUp으로 잇는다).
    왜: 상주·아내의 슬픔은 서서 우는 동네 사람보다 한 단계 커야 읽힌다. 땅 치는 순간(pound)에 쿵 소리·먼지 한 점을 맞춘다."""
    ks = []
    for fr in range(0, 151, 3):
        t = fr / 150; sob = max(0.0, math.sin(TAU * 3 * t)) ** 2; pound = max(0.0, math.sin(TAU * 3 * t - 0.9)) ** 6
        up = P(lean=32 + 14 * sob, hn=-6 + 14 * sob, R=(80 - 40 * pound, 10, 24), L=(88, 12, 16))
        ks.append((fr, full(up, SQ["dz"] + 0.02, SQ["hy"], SQ["hrx"], {"L": (-0.10, ANK, 0.0), "R": (-0.10, ANK, 0.0)})))
    return loopfix(ks), "LINEAR", True, {"pound": 14}

def hug_shoes(idle):
    """아버지 짚신을 품에 안고 선 모습 120프레임 반복(막내딸): 두 팔로 가슴에 꼭 안고 울지 않는다. 숨만 크게 쉬고 고개가 아주 조금 떨린다.
    왜: 시나리오 '막내딸(10대)은 울지 않고 짚신을 품에 안고 있다'. 큰 동작이 없어야 오히려 슬픔이 읽힌다."""
    ks = []
    for fr in range(0, 121, 6):
        t = fr / 120; br = math.sin(TAU * t)
        ks.append((fr, full(P(lean=5 + 1.2 * br, hn=12 + 1.0 * br, R=(78, -10, 112), L=(78, -10, 112), ht=1.2 * math.sin(TAU * t * 3)), 0)))
    return loopfix(ks), "LINEAR", True, {}

def hold_flag(idle):
    """만장 깃대 들고 서기 120프레임 반복: 두 손으로 깃대를 가슴께에 세워 쥐고 바람에 맞춰 몸이 아주 조금 흔들린다."""
    ks = []
    for fr in range(0, 121, 6):
        t = fr / 120; sw = math.sin(TAU * t)
        ks.append((fr, full(P(lean=2 + 1 * sw, hn=10, twist=1.5 * sw, R=(62, 8, 80), L=(52, 8, 82)), 0)))
    return loopfix(ks), "LINEAR", True, {}

def pour_cup(idle):
    """노제 술잔 올리기 150프레임(비반복): 두 손으로 잔을 받쳐 앞으로 내밀어 올리고(50) 천천히 땅에 부은 뒤(80) 절 한 번(130)."""
    def pose(cup, bow, pour):
        return full(P(lean=6 + 30 * bow + 8 * pour, hn=14, R=(72 + 14 * cup, 6, 70 - 20 * pour), L=(66 + 10 * cup, 6, 78), dz=-0.04 * bow), -0.04 * bow, 0, 6 * bow)
    return [(0, idle), (24, pose(0, 0, 0)), (50, pose(1, 0, 0)), (66, pose(1, 0, 0)), (82, pose(1, 0, 1)), (100, pose(0.5, 0, 1)), (112, pose(0, 0, 0)), (130, pose(0, 1, 0)), (150, idle)], "BEZIER", False, {"raise": 50, "pour": 82}


EXTRA_FN = {"HugShoes": hug_shoes, "HoldFlag": hold_flag, "PourCup": pour_cup, "Wail": wail}   # 애도객 전용 역할 동작
ROLE = {   # id → 역할 동작 이름들 (설명은 위 함수 머리말)
 "N101": ["Ritual", "Bow", "OpenFan", "ReachUp"], "N102": ["RopeCoil", "ReachUp"], "N103": ["Offer", "Bow"], "N104a": ["Play"], "N104b": ["Play"], "N104c": ["Play"], "N105": ["Chant", "TapPipe"],
 "N106": ["Haggle"], "N107": ["DrawWater", "Laundry"], "N108": ["HoldReins", "SquatCoil"], "N109": ["Hammer", "Bellows"], "N110a": ["Haggle"], "N110b": ["Haggle"],
 "N201": ["Haggle"], "N202": ["Mix", "Haggle", "PlaceBowl"], "N203": ["Serve", "Haggle", "ReachUp"], "N204a": ["WaveStick", "Haggle"], "N204b": ["Hawk", "Haggle"], "N205": ["Read", "Scribble"], "N206": ["Guard", "Doze"], "N207": ["Guard", "Stamp", "ReadNotice"]}
FREE = {"N110b": "L", "N203": "L", "N204a": "L", "N106": "L", "N202": "R"}   # 소품 든 쪽을 뺀 자유로운 팔

def role_clips(s, idle):
    out = {}
    for nm in ROLE.get(s["id"], []):
        if nm == "Haggle": out[nm] = haggle(idle, FREE.get(s["id"], "both"))
        elif nm == "Guard": out[nm] = guard(idle, "staff" if "gonjang" in s.get("props", []) else "keys")
        else:
            fn = {**EXTRA_FN, "Hammer": hammer, "Bellows": bellows, "DrawWater": draw_water, "Laundry": laundry, "Hawk": hawk, "WaveStick": wave_stick, "Chant": chant, "Ritual": ritual,
                  "Offer": offer, "Bow": bow, "Play": play, "Read": read, "Stamp": stamp, "Mix": mix, "Serve": serve, "RopeCoil": rope, "HoldReins": reins, "ReachUp": reach_up, "Doze": doze, "Scribble": scribble, "ReadNotice": read_notice, "PlaceBowl": place_bowl, "TapPipe": tap_pipe, "OpenFan": open_fan, "SquatCoil": squat_coil}[nm]
            r = fn(idle); out[nm] = r if len(r) == 4 else (r[0], "LINEAR", True, {})
    return out
