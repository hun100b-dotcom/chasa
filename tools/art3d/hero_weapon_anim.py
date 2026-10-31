"""주인공 무기별 동작(60fps). 철삭 외 4계열(육모방망이·요령방울·삼지창·명부 붓) × {3타 공격, 무기 꺼내 들기(Draw), 천도(Tendo), 파혼(Pahon)} + 철삭 꺼내 들기.
철삭의 공격 3타·Cast·Pahon은 hero_anim.py의 기존 동작(Attack, Attack2, Attack3, Cast, Pahon)을 그대로 쓴다.
이름 규칙: <Weapon>_Attack1/2/3, <Weapon>_Draw, <Weapon>_Tendo, <Weapon>_Pahon  (Weapon = Mace, Bell, Trident, Brush, Chain(Draw만)).
시간은 코드팀 WeaponTable(unity/Assets/Scripts/WeaponTable.cs)의 windup/swing/recover(초)를 60fps 프레임으로 바꿔 맞췄다(철삭 Config.COMBO도 같은 방식).
  때리는 순간(event hit)은 선딜 끝 + 휘두름 절반. 3타(내려찍기·종·찌르기)는 hit_start~hit_end 구간.
무기를 쥐는 방향(소켓): 손 뼈 Hand.R에 달 때 블렌더 X축 회전값이 무기마다 다르다(SOCKET_ROT_X). 철삭만 기존 90°.
자세는 '손의 방향'이 아니라 '팔이 가리키는 방향'과 '무기가 가리키는 방향'(방위각 az: 정면 0·왼쪽 +90·뒤 180·오른쪽 −90, 고각 el: 위 +)으로 적고,
손목 회전은 풀어서(역산) 넣는다 — 그래야 무기가 의도한 방향을 정확히 가리킨다."""
import math
from mathutils import Vector, Euler, Matrix

# 소켓 회전(블렌더 X축, 도): 무기 +Z가 향하는 방향 = (0, -sin θ, cos θ). θ=90 → 정면 수평, 0 → 위, 180 → 아래
SOCKET_ROT_X = {"Chain": 90, "Mace": 40, "Bell": 20, "Trident": 30, "Brush": 55}
def dirv(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
def w0(weapon):
    t = math.radians(SOCKET_ROT_X[weapon]); return Vector((0, -math.sin(t), math.cos(t)))

def _eul(q): return tuple(round(math.degrees(a), 3) for a in q.to_euler("XYZ"))

def arm_to(az, el):
    """팔(아래로 늘어진 기본 자세)이 (az, el) 방향을 가리키게 하는 회전."""
    return _eul(Vector((0, 0, -1)).rotation_difference(dirv(az, el)))

def hand_for(weapon, arm_az, arm_el, w_az, w_el):
    """팔이 (arm_az,arm_el)을 가리킬 때 무기가 (w_az,w_el)을 가리키도록 하는 손 회전."""
    Ra = Euler([math.radians(a) for a in arm_to(arm_az, arm_el)], "XYZ").to_matrix()
    u = Ra.inverted() @ dirv(w_az, w_el)
    return _eul(w0(weapon).rotation_difference(u))

STEP_L = {"UpperLeg.L": {"r": (-38, 0, 0)}, "LowerLeg.L": {"r": (14, 0, 0)}, "UpperLeg.R": {"r": (22, 0, 0)}, "LowerLeg.R": {"r": (24, 0, 0)}, "Foot.R": {"r": (-20, 0, 0)}}
STEP_R = {"UpperLeg.R": {"r": (-38, 0, 0)}, "LowerLeg.R": {"r": (14, 0, 0)}, "UpperLeg.L": {"r": (22, 0, 0)}, "LowerLeg.L": {"r": (24, 0, 0)}, "Foot.L": {"r": (-20, 0, 0)}}
WIDE = {"UpperLeg.L": {"r": (-30, 0, 18)}, "LowerLeg.L": {"r": (22, 0, 0)}, "UpperLeg.R": {"r": (-8, 0, -18)}, "LowerLeg.R": {"r": (30, 0, 0)}}
SQUAT = {"UpperLeg.L": {"r": (-40, 0, 6)}, "LowerLeg.L": {"r": (52, 0, 0)}, "UpperLeg.R": {"r": (-40, 0, -6)}, "LowerLeg.R": {"r": (52, 0, 0)}}

def P(w, arm=None, wd=None, armL=None, chest=(0, 0, 0), hips=(0, 0, 0), hl=(0, 0, 0), head=(0, 0, 0), legs=None):
    """한 자세. arm=(az,el) 오른팔 방향, wd=(az,el) 무기 방향, armL=(az,el) 왼팔 방향. chest/hips=(rx,ry,rz) 도, hl=엉덩이 이동(m)."""
    d = {}
    if arm is not None:
        d["UpperArm.R"] = {"r": arm_to(*arm)}
        if wd is not None: d["Hand.R"] = {"r": hand_for(w, arm[0], arm[1], wd[0], wd[1])}
    if armL is not None: d["UpperArm.L"] = {"r": arm_to(*armL)}
    d["Chest"] = {"r": chest}; d["Hips"] = {"r": hips, "l": hl}
    if head and any(head): d["Head"] = {"r": head}
    if legs: d.update(legs)
    return d

def fr(sec): return max(1, round(sec * 60))
TIM = {   # WeaponTable.cs (windup, swing, recover)초 ×3타
    "Mace": [(0.16, 0.18, 0.22), (0.16, 0.18, 0.22), (0.28, 0.22, 0.45)],
    "Bell": [(0.12, 0.20, 0.20), (0.12, 0.20, 0.20), (0.22, 0.24, 0.40)],
    "Trident": [(0.16, 0.12, 0.22), (0.16, 0.12, 0.22), (0.26, 0.14, 0.42)],
    "Brush": [(0.14, 0.10, 0.20), (0.14, 0.10, 0.20), (0.24, 0.12, 0.38)],
}
def attack(w, i, wind, hit, follow, extra=None):
    """공격 하나: 0 → 선딜 끝(wind) → 휘두름 중간(hit) → 휘두름 끝(follow) → 후딜 → 0. 3타(i=2)는 follow 뒤 유지 키를 더 둘 수 있다."""
    a, s, r = (fr(x) for x in TIM[w][i]); tot = a + s + r; h = a + s // 2
    keys = [(0, {}), (a, wind), (h, hit), (a + s, follow)]
    ev = {"hit": h, "windup_end": a, "swing_end": a + s, "windup_sec": TIM[w][i][0], "swing_sec": TIM[w][i][1], "recover_sec": TIM[w][i][2]}
    if extra:   # [(프레임 오프셋(휘두름 끝 이후), 자세)]
        for off, p in extra: keys.append((a + s + off, p))
    keys.append((tot, {})); return keys, ev, tot

def clips():
    C = {}
    # ───────────── 육모방망이: 근접 3.2m, 느리고 묵직. 1·2타 대각 휘두름, 3타 두 손 내려찍기(반경 3m)
    W = "Mace"
    k, ev, _ = attack(W, 0, P(W, (-70, 60), (-150, 70), (-20, 20), (0, 0, -32), (0, 0, -16), (0, 0, 0.0), (0, 0, 0), None),
                      P(W, (-20, 15), (20, -25), (30, -10), (8, 0, 26), (0, 0, 12), (0, -0.2, 0), None, STEP_L), P(W, (35, -20), (80, -40), (60, -30), (14, 0, 46), (0, 0, 24), (0, -0.26, 0), None, STEP_L))
    C["Mace_Attack1"] = (k, "LINEAR", False, ev)
    k, ev, _ = attack(W, 1, P(W, (60, 20), (95, 25), (50, 30), (0, 0, 42), (0, 0, 20), (0, 0, 0), None, None),
                      P(W, (-10, 5), (-40, -10), (20, 5), (8, 0, -22), (0, 0, -12), (0, -0.2, 0), None, STEP_R), P(W, (-70, -10), (-100, -10), (0, -10), (14, 0, -46), (0, 0, -24), (0, -0.26, 0), None, STEP_R))
    C["Mace_Attack2"] = (k, "LINEAR", False, ev)
    up = P(W, (-10, 80), (180, 75), (10, 80), (-26, 0, 0), (-8, 0, 0), (0, 0.1, -0.06), (10, 0, 0), None)
    mid = P(W, (0, 40), (0, 20), (0, 40), (14, 0, 0), (6, 0, 0), (0, -0.1, -0.08), None, None)
    slam = P(W, (0, -30), (0, -65), (0, -30), (46, 0, 0), (20, 0, 0), (0, -0.26, -0.16), (-14, 0, 0), STEP_L)
    a, s, r = (fr(x) for x in TIM[W][2])
    C["Mace_Attack3"] = ([(0, {}), (a, up), (a + s // 2, mid), (a + s, slam), (a + s + 14, slam), (a + s + r, {})], "LINEAR", False,
                         {"hit_start": a + s - 3, "hit_end": a + s + 14, "impact": a + s, "windup_end": a, "swing_end": a + s, "windup_sec": TIM[W][2][0], "swing_sec": TIM[W][2][1], "recover_sec": TIM[W][2][2]})
    # ───────────── 요령방울: 360° 원 범위 짧고 빠름. 1·2타 방울을 흔들어 울리고, 3타는 두 손으로 높이 들었다 내려 종을 친다
    W = "Bell"
    k, ev, _ = attack(W, 0, P(W, (-50, 55), (-90, 50), (30, 40), (0, 0, -16), (0, 0, -8), (0, 0, 0), (0, 0, 6), None),
                      P(W, (5, 50), (20, 25), (30, 40), (4, 0, 20), (0, 0, 10), (0, -0.05, 0), None, None), P(W, (15, 40), (40, 40), (30, 30), (6, 0, 28), (0, 0, 14), (0, -0.08, 0), None, None))
    C["Bell_Attack1"] = (k, "LINEAR", False, ev)
    k, ev, _ = attack(W, 1, P(W, (10, 50), (50, 45), (-20, 40), (0, 0, 20), (0, 0, 10), (0, 0, 0), None, None),
                      P(W, (-20, 50), (-30, 25), (-20, 40), (4, 0, -20), (0, 0, -10), (0, -0.05, 0), None, None), P(W, (-40, 40), (-70, 40), (-20, 30), (6, 0, -28), (0, 0, -14), (0, -0.08, 0), None, None))
    C["Bell_Attack2"] = (k, "LINEAR", False, ev)
    a, s, r = (fr(x) for x in TIM[W][2])
    up = P(W, (0, 85), (180, 80), (0, 85), (-18, 0, -30), (-6, 0, -30), (0, 0.06, 0), (8, 0, 0), None)
    mid = P(W, (0, 30), (0, 5), (0, 30), (4, 0, 40), (4, 0, 40), (0, -0.05, -0.04), None, None)
    toll = P(W, (0, -15), (0, -40), (0, -15), (26, 0, 60), (10, 0, 60), (0, -0.1, -0.1), (-12, 0, 0), STEP_L)
    C["Bell_Attack3"] = ([(0, {}), (a, up), (a + s // 2, mid), (a + s, toll), (a + s + 10, toll), (a + s + r, {})], "LINEAR", False,
                         {"hit_start": a + s // 2, "hit_end": a + s + 6, "impact": a + s, "windup_end": a, "swing_end": a + s, "windup_sec": TIM[W][2][0], "swing_sec": TIM[W][2][1], "recover_sec": TIM[W][2][2]})
    # ───────────── 삼지창: 4.4m 좁고 긴 찌르기(관통 3). 1·2타 위·아래 찌르기, 3타 크게 내딛어 꿰어 들어 올림
    W = "Trident"
    lead = (20, 10)
    k, ev, _ = attack(W, 0, P(W, (-125, -15), (-3, 8), lead, (0, 0, -36), (0, 0, -16), (0, 0.04, 0), None, STEP_L),
                      P(W, (-12, 5), (-2, 6), lead, (8, 0, 22), (0, 0, 10), (0, -0.28, 0), None, STEP_L), P(W, (-10, 5), (-2, 6), lead, (10, 0, 24), (0, 0, 12), (0, -0.34, 0), None, STEP_L))
    C["Trident_Attack1"] = (k, "LINEAR", False, ev)
    k, ev, _ = attack(W, 1, P(W, (-120, 30), (-3, -12), lead, (0, 0, -30), (0, 0, -14), (0, 0.04, 0), None, STEP_R),
                      P(W, (-14, -5), (-2, -14), lead, (14, 0, 18), (0, 0, 8), (0, -0.28, -0.05), None, STEP_R), P(W, (-12, -5), (-2, -14), lead, (16, 0, 20), (0, 0, 10), (0, -0.34, -0.06), None, STEP_R))
    C["Trident_Attack2"] = (k, "LINEAR", False, ev)
    a, s, r = (fr(x) for x in TIM[W][2])
    back = P(W, (-150, 12), (0, 22), (30, 10), (-6, 0, -58), (0, 0, -24), (0, 0.1, 0.0), (4, 0, 0), WIDE)
    thrust = P(W, (-6, 14), (0, 18), (20, 10), (22, 0, 28), (6, 0, 14), (0, -0.55, -0.1), (-6, 0, 0), WIDE)
    lift = P(W, (-4, 38), (0, 52), (20, 30), (10, 0, 22), (0, 0, 10), (0, -0.5, -0.06), (-12, 0, 0), WIDE)
    C["Trident_Attack3"] = ([(0, {}), (a, back), (a + s // 2, thrust), (a + s, thrust), (a + s + 8, lift), (a + s + 16, lift), (a + s + r, {})], "LINEAR", False,
                            {"hit": a + s // 2, "hit_start": a + s // 2, "hit_end": a + s + 4, "windup_end": a, "swing_end": a + s, "windup_sec": TIM[W][2][0], "swing_sec": TIM[W][2][1], "recover_sec": TIM[W][2][2]})
    # ───────────── 명부 붓: 6m 원거리 먹물(투사체). 1·2타 손목으로 휙 긋고, 3타 높이 들었다 도장 찍듯 찍는다
    W = "Brush"
    k, ev, _ = attack(W, 0, P(W, (-70, 40), (-100, 60), (30, 20), (0, 0, -22), (0, 0, -10), (0, 0, 0), None, None),
                      P(W, (-10, 25), (30, -20), (30, 20), (6, 0, 14), (0, 0, 8), (0, -0.06, 0), None, STEP_L), P(W, (20, 10), (70, -35), (30, 20), (8, 0, 26), (0, 0, 14), (0, -0.1, 0), None, STEP_L))
    C["Brush_Attack1"] = (k, "LINEAR", False, ev)
    k, ev, _ = attack(W, 1, P(W, (40, 25), (80, 40), (-20, 20), (0, 0, 24), (0, 0, 12), (0, 0, 0), None, None),
                      P(W, (-10, 25), (-30, -15), (-20, 20), (6, 0, -14), (0, 0, -8), (0, -0.06, 0), None, STEP_R), P(W, (-50, 15), (-80, -30), (-20, 20), (8, 0, -26), (0, 0, -14), (0, -0.1, 0), None, STEP_R))
    C["Brush_Attack2"] = (k, "LINEAR", False, ev)
    a, s, r = (fr(x) for x in TIM[W][2])
    up = P(W, (-30, 85), (180, 80), (20, 60), (-20, 0, -12), (-6, 0, 0), (0, 0.08, -0.02), (8, 0, 0), None)
    stamp = P(W, (0, 20), (0, -50), (0, 20), (28, 0, 0), (12, 0, 0), (0, -0.2, -0.1), (-8, 0, 0), STEP_L)
    C["Brush_Attack3"] = ([(0, {}), (a, up), (a + s // 2, P(W, (0, 55), (0, 10), (0, 40), (6, 0, 0), (3, 0, 0), (0, -0.1, -0.04))), (a + s, stamp), (a + s + 8, stamp), (a + s + r, {})], "LINEAR", False,
                          {"hit": a + s, "windup_end": a, "swing_end": a + s, "windup_sec": TIM[W][2][0], "swing_sec": TIM[W][2][1], "recover_sec": TIM[W][2][2]})

    # ───────────── 무기 꺼내 들기(Draw, 30f = WEAPON_SWAP_TIME 0.5초): 등·허리에서 뽑아 한 번 멋을 부리고 자세를 잡는다.
    # 이벤트: swap_hide(옛 무기 숨김) f9, swap_show(새 무기 보임) f13. 코드는 이 두 프레임에서 손의 무기 모델을 갈아 끼운다.
    def back_pull(w): return P(w, (170, -15), (180, 0), (-20, -10), (4, 0, -26), (0, 0, -14), (0, 0.04, 0), None, None)
    def draw(w, flourish):
        keys = [(0, {}), (7, P(w, (150, -20), (180, -10), None, (6, 0, -22), (0, 0, -10), (0, 0.03, 0), None, None)), (13, back_pull(w))]
        keys += flourish; keys.append((30, {}))
        return keys, "BEZIER", False, {"swap_hide": 9, "swap_show": 13, "swap_sec": 0.5}
    C["Chain_Draw"] = draw("Chain", [(20, P("Chain", (0, 75), (0, 90 - 0.01), (0, 50), (-6, 0, 0), (0, 0, 20), (0, -0.04, 0))), (25, P("Chain", (-30, 50), (-90, 20), None, (4, 0, 0), (0, 0, -16)))])
    C["Mace_Draw"] = draw("Mace", [(20, P("Mace", (-30, 70), (0, 88), (30, 30), (-6, 0, 10), (0, 0, 0), (0, 0, 0))), (25, P("Mace", (-60, 35), (-110, 55), None, (4, 0, -8), (0, 0, -6), (0, -0.04, 0)))])
    C["Bell_Draw"] = draw("Bell", [(19, P("Bell", (0, 80), (0, 86), (0, 70), (-8, 0, 0), (0, 0, 0), (0, 0, 0))), (22, P("Bell", (0, 80), (90, 60), (0, 70), (-8, 0, 14), (0, 0, 8))), (25, P("Bell", (0, 80), (-90, 60), (0, 70), (-8, 0, -14), (0, 0, -8)))])
    C["Trident_Draw"] = draw("Trident", [(19, P("Trident", (0, 40), (90, 30), (30, 20), (6, 0, 20), (0, 0, 10), (0, -0.04, 0), None, STEP_L)), (24, P("Trident", (-20, 10), (0, 88), (20, 10), (2, 0, 0), (0, 0, 0), (0, -0.04, 0), None, STEP_L))])
    C["Brush_Draw"] = draw("Brush", [(19, P("Brush", (-40, 40), (-50, 20), (20, 20), (4, 0, -20), (0, 0, -10), (0, 0, 0))), (24, P("Brush", (30, 30), (50, 20), (20, 20), (4, 0, 20), (0, 0, 10), (0, -0.04, 0)))])

    # ───────────── 천도(Tendo, 60f): 0~14 들어 올림 → 14~46 버팀(코드는 천도 시간만큼 이 구간을 반복/늘림) → 46~60 마무리(넋을 보내는 동작).
    ev_t = {"hold_start": 14, "hold_end": 46, "finish_start": 46, "finish_peak": 52}
    def hold_osc(w, base, alt, n):   # 버팀 구간을 base↔alt로 번갈아(방울 울림·붓 글씨)
        return [(14 + 4 * i, base if i % 2 == 0 else alt) for i in range(1, n + 1)]
    W = "Mace"   # 땅에 세운 방망이에 두 손을 얹고 고개 숙여 넋을 달랜다 → 들어 올려 보낸다
    plant = P(W, (0, -40), (0, -80), (0, -40), (16, 0, 0), (6, 0, 0), (0, -0.04, -0.03), (24, 0, 0))
    plant2 = P(W, (0, -40), (0, -80), (0, -40), (20, 0, 0), (8, 0, 0), (0, -0.05, -0.04), (28, 0, 0))
    C["Mace_Tendo"] = ([(0, {}), (14, plant), (30, plant2), (46, plant), (52, P(W, (0, 30), (0, 80), (0, 30), (-14, 0, 0), (-4, 0, 0), (0, 0.04, 0), (-18, 0, 0))), (60, {})], "BEZIER", False, ev_t)
    W = "Bell"   # 방울을 높이 들어 흔든다(울림 소리가 넋을 달램). 마무리에서 크게 한 번 울리고 내린다
    b = P(W, (10, 60), (0, 80), (0, 45), (-6, 0, 0), (0, 0, 0), (0, 0, 0)); bl = P(W, (10, 60), (40, 70), (0, 45), (-6, 0, 6), (0, 0, 3), (0, 0, 0)); br = P(W, (10, 60), (-40, 70), (0, 45), (-6, 0, -6), (0, 0, -3), (0, 0, 0))
    keys = [(0, {}), (14, b)] + [(14 + 3 * i, bl if i % 2 else br) for i in range(1, 11)] + [(46, b), (50, P(W, (0, 85), (180, 60), (0, 80), (-16, 0, 0), (-6, 0, 0), (0, 0, 0))), (54, P(W, (0, 30), (0, 10), (0, 40), (14, 0, 0), (6, 0, 0), (0, -0.04, 0))), (60, {})]
    C["Bell_Tendo"] = (keys, "BEZIER", False, ev_t)
    W = "Trident"   # 창 꽁무니를 땅에 세우고 왼손바닥을 넋에게 내민다 → 끝을 하늘로 들어 올려 보낸다
    st = P(W, (-30, -5), (0, 90), (35, 40), (-2, 0, 14), (0, 0, 6), (0, 0, 0), (4, 0, 0), None); st2 = P(W, (-30, -5), (0, 90), (30, 46), (-4, 0, 14), (0, 0, 6), (0, 0, 0), (6, 0, 0), None)
    C["Trident_Tendo"] = ([(0, {}), (14, st), (30, st2), (46, st), (52, P(W, (-10, 80), (0, 88), (30, 80), (-14, 0, 0), (-4, 0, 0), (0, 0.03, 0), (-20, 0, 0))), (60, {})], "BEZIER", False, ev_t)
    W = "Brush"   # 허공에 이름을 쓰듯 붓을 놀린다 → 마지막 한 점을 찍어 마무리
    p1 = P(W, (-15, 50), (0, 50), (25, 35), (6, 0, -8), (0, 0, -4), (0, 0, 0)); p2 = P(W, (10, 45), (30, 40), (25, 35), (6, 0, 8), (0, 0, 4), (0, 0, 0)); p3 = P(W, (-5, 60), (-20, 55), (25, 35), (4, 0, 0), (0, 0, 0), (0, 0, 0))
    C["Brush_Tendo"] = ([(0, {}), (14, p1), (20, p2), (26, p3), (32, p1), (38, p2), (46, p3), (52, P(W, (0, 25), (0, -50), (20, 20), (24, 0, 0), (10, 0, 0), (0, -0.06, -0.04), (-10, 0, 0))), (60, {})], "BEZIER", False, ev_t)

    # ───────────── 파혼(Pahon, 25f): 8프레임에 터뜨린다. 10프레임부터 피하기로 끊을 수 있다(recover_dodge_from).
    ev_p = {"hit": 8, "recover_dodge_from": 10}
    W = "Mace"   # 머리 위로 들었다가 땅을 내리친다(넉백이 먼 무기)
    C["Mace_Pahon"] = ([(0, {}), (6, P(W, (-10, 80), (180, 78), (10, 80), (-24, 0, 0), (-8, 0, 0), (0, 0.08, -0.04), (8, 0, 0))), (8, P(W, (0, -25), (0, -70), (0, -25), (44, 0, 0), (18, 0, 0), (0, -0.28, -0.14), (-12, 0, 0), STEP_L)), (13, P(W, (0, -25), (0, -70), (0, -25), (44, 0, 0), (18, 0, 0), (0, -0.28, -0.14), (-12, 0, 0), STEP_L)), (25, {})], "LINEAR", False, ev_p)
    W = "Bell"   # 가슴께로 모았다가 두 팔을 활짝 벌리며 방울을 터뜨리듯 흔든다
    C["Bell_Pahon"] = ([(0, {}), (6, P(W, (20, 25), (0, 85), (-20, 25), (14, 0, 0), (6, 0, 0), (0, -0.04, 0))), (8, P(W, (-85, 35), (-90, 50), (85, 35), (-14, 0, 0), (-6, 0, 0), (0, 0.02, 0))), (11, P(W, (-80, 40), (-60, 55), (80, 40), (-12, 0, 0), (-4, 0, 0))), (14, P(W, (-85, 35), (-110, 45), (85, 35), (-14, 0, 0), (-6, 0, 0))), (25, {})], "LINEAR", False, ev_p)
    W = "Trident"   # 창을 당겼다가 쭉 찔러 꿰고, 위로 튕겨 던진다(꿰어 날린다)
    C["Trident_Pahon"] = ([(0, {}), (6, P(W, (-140, 8), (0, 15), (25, 10), (0, 0, -40), (0, 0, -18), (0, 0.08, 0), None, WIDE)), (8, P(W, (-5, 12), (0, 14), (20, 10), (22, 0, 26), (6, 0, 12), (0, -0.5, -0.1), None, WIDE)), (11, P(W, (-5, 40), (0, 62), (20, 30), (10, 0, 22), (0, 0, 10), (0, -0.48, -0.06), (-10, 0, 0), WIDE)), (25, {})], "LINEAR", False, ev_p)
    W = "Brush"   # 붓을 뒤로 젖혔다가 먹을 흩뿌리듯 크게 휘둘러 도장처럼 찍는다
    C["Brush_Pahon"] = ([(0, {}), (6, P(W, (-120, 60), (-150, 70), (30, 40), (-10, 0, -42), (0, 0, -20), (0, 0.06, 0))), (8, P(W, (20, 22), (40, -10), (30, 40), (8, 0, 34), (0, 0, 16), (0, -0.16, -0.04), None, STEP_L)), (11, P(W, (75, 12), (100, 0), (30, 40), (10, 0, 52), (0, 0, 24), (0, -0.2, -0.05), None, STEP_L)), (25, {})], "LINEAR", False, ev_p)
    return C


# ───────────── 시트(확인용 그림)에서만 쓰는 무기 붙이기. 내보내는 GLB에는 무기를 넣지 않는다(코드가 소켓에 따로 붙임).
def attach(arm, w):
    """무기 w(Chain·Mace·Bell·Trident·Brush)를 Hand.R 뼈 머리 위치에 소켓 회전(SOCKET_ROT_X)으로 붙이고 오브젝트를 돌려준다."""
    import weapons
    fn = {"Chain": weapons.chain, "Mace": weapons.bangmang, "Bell": weapons.yoryeong, "Trident": weapons.samjichang, "Brush": weapons.myeongbu}[w]
    import bpy
    from lib3d import join
    o = join("wpn_" + w, fn())
    o.matrix_basis = Matrix.Identity(4)
    o.parent = arm; o.parent_type = "BONE"; o.parent_bone = "Hand.R"
    o.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    Pm = o.matrix_world.copy()          # 부모 역행렬을 0으로 둔 상태의 세계 위치 = 뼈 기준틀
    head = arm.matrix_world @ arm.data.bones["Hand.R"].head_local
    D = Matrix.Translation(head) @ Matrix.Rotation(math.radians(SOCKET_ROT_X[w]), 4, "X")
    o.matrix_parent_inverse = Pm.inverted() @ D
    bpy.context.view_layer.update()
    return o
