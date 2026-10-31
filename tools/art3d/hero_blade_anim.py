"""주인공 검·도 전용 동작(60fps). 환도(Sword)·월도(Glaive) + 둘이 같이 쓰는 돌진 공격·반격.
  환도 = 빠른 4연타 검: Sword_Attack1~4 + Sword_Heavy(발도: 칼집에서 뽑으며 한 번에 베는 강타)
  월도 = 넓고 무거운 3연타 도: Glaive_Attack1~3 + Glaive_Spin(한 바퀴 휘돌려 베기)
  공용  = Dash_Attack(돌진 공격: 몸을 던져 찌르듯 베기), Counter(반격: 0.15초 막기 창 + 되받아치기)
왜 따로 만드나: 시안의 검·도가 철퇴·삼지창 동작을 빌려 써서 '칼질'로 안 읽혔다. 철퇴는 내려찍고 삼지창은 찌르지만 칼은 '베어 가르는' 동작이라 몸 쓰임이 다르다.
규약은 hero_weapon_anim.py와 같다: 자세는 팔·무기가 가리키는 방위각(az: 정면 0·왼쪽 +90·뒤 180·오른쪽 −90)·고각(el: 위 +)으로 적고,
손목 회전은 코드가 역산한다. 두 무기 모두 소켓 회전(SOCKET_ROT_X)이 90°라 '공용' 동작은 어느 쪽을 들어도 같은 자세가 맞는다.
이벤트: hit(때리는 프레임), hit_start/hit_end(맞는 구간), windup_end, swing_end, *_sec(선딜·휘두름·후딜 초). 이동·회전 거리는 코드(루트 모션 없음).
추가 이벤트: chain_from(이 프레임부터 다음 타 입력 받음 = 후딜 절반), cancel_from(피하기로 끊을 수 있는 프레임)."""
import hero_weapon_anim as hwa
from hero_weapon_anim import P, fr, STEP_L, STEP_R, WIDE, SQUAT

# 두 무기 모두 쥐는 방향(소켓)은 철삭과 같은 90°: 칼날이 정면 수평을 향한 상태가 기본
hwa.SOCKET_ROT_X["Sword"] = 90
hwa.SOCKET_ROT_X["Glaive"] = 90
SHARED = {"Dash_Attack": "Sword", "Counter": "Sword"}   # 공용 동작은 시트에 환도를 들려 그린다(소켓이 같아 월도도 똑같이 맞는다)

# (선딜, 휘두름, 후딜) 초 — 환도는 짧고 빠르게, 월도는 길고 묵직하게
hwa.TIM["Sword"] = [(0.07, 0.08, 0.13), (0.07, 0.08, 0.13), (0.08, 0.09, 0.14), (0.16, 0.10, 0.30)]
hwa.TIM["Glaive"] = [(0.20, 0.16, 0.28), (0.20, 0.16, 0.28), (0.32, 0.22, 0.50)]

def _ev(w, i, ev, tot):
    """공통 이벤트 덧붙이기: 후딜의 절반부터 다음 타 입력을 받는다(chain_from), 피하기 캔슬은 휘두름이 끝난 직후부터(cancel_from)."""
    a, s, r = (fr(x) for x in hwa.TIM[w][i])
    ev["chain_from"] = a + s + r // 2
    ev["cancel_from"] = a + s + 2
    return ev

def clips():
    C = {}
    # ───────────── 환도(검): 빠른 4연타. 1·2타 좌우 가로베기, 3타 아래에서 위로 올려베기, 4타 두 발 모아 내려 가르는 마무리
    W = "Sword"
    k, ev, _ = hwa.attack(W, 0,
        P(W, (-75, 25), (-120, 30), (30, -10), (0, 0, -34), (0, 0, -16), (0, 0, 0.0), (0, 0, 8), None),
        P(W, (-15, 10), (15, 5), (30, -10), (6, 0, 22), (0, 0, 10), (0, -0.14, 0), None, STEP_L),
        P(W, (35, 0), (80, -15), (40, -10), (10, 0, 40), (0, 0, 20), (0, -0.2, 0), None, STEP_L))
    C["Sword_Attack1"] = (k, "LINEAR", False, _ev(W, 0, ev, 0))
    k, ev, _ = hwa.attack(W, 1,
        P(W, (45, 15), (100, 10), (-30, -10), (0, 0, 36), (0, 0, 18), (0, 0, 0), (0, 0, -8), None),
        P(W, (-10, 5), (-20, 0), (-20, -10), (6, 0, -22), (0, 0, -10), (0, -0.14, 0), None, STEP_R),
        P(W, (-60, -5), (-95, -10), (-30, -10), (10, 0, -42), (0, 0, -20), (0, -0.2, 0), None, STEP_R))
    C["Sword_Attack2"] = (k, "LINEAR", False, _ev(W, 1, ev, 0))
    k, ev, _ = hwa.attack(W, 2,    # 올려베기: 왼쪽 아래에서 오른쪽 위로 쳐 올린다
        P(W, (40, -35), (90, -45), (30, -20), (14, 0, 30), (6, 0, 14), (0, 0.02, -0.1), None, WIDE),
        P(W, (-20, 30), (-25, 35), (30, -10), (-4, 0, -6), (0, 0, -6), (0, -0.2, -0.02), None, STEP_L),
        P(W, (-45, 60), (-60, 62), (30, 0), (-12, 0, -30), (0, 0, -16), (0, -0.24, 0), (-8, 0, 0), STEP_L))
    C["Sword_Attack3"] = (k, "LINEAR", False, _ev(W, 2, ev, 0))
    a, s, r = (fr(x) for x in hwa.TIM[W][3])    # 4타: 두 손으로 머리 위까지 들었다 한 걸음 내딛으며 내려 가른다(맞는 순간은 내려온 끝)
    up = P(W, (-10, 80), (180, 75), (10, 80), (-26, 0, 0), (-8, 0, 0), (0, 0.1, -0.06), (10, 0, 0), None)
    mid = P(W, (0, 40), (0, 25), (0, 40), (12, 0, 0), (5, 0, 0), (0, -0.12, -0.08), None, None)
    cut = P(W, (0, -20), (0, -38), (0, -20), (40, 0, 0), (18, 0, 0), (0, -0.3, -0.14), (-12, 0, 0), STEP_L)
    C["Sword_Attack4"] = ([(0, {}), (a, up), (a + s // 2, mid), (a + s, cut), (a + s + 12, cut), (a + s + r, {})], "LINEAR", False,
                          _ev(W, 3, {"hit": a + s, "hit_start": a + s - 2, "hit_end": a + s + 6, "windup_end": a, "swing_end": a + s, "windup_sec": hwa.TIM[W][3][0], "swing_sec": hwa.TIM[W][3][1], "recover_sec": hwa.TIM[W][3][2]}, 0))
    # ───────────── 환도 발도(Sword_Heavy): 왼 허리 칼집에 손을 얹고 깊이 웅크렸다가, 뽑으며 단번에 가로로 가른다. 길게 숨을 참는 만큼 한 방이 크다
    a, s, r = fr(0.30), fr(0.07), fr(0.40); h = a + s // 2
    crouch0 = P(W, (50, -30), (160, -15), (75, -40), (8, 0, 18), (4, 0, 8), (0, -0.02, -0.08), (4, 0, 0), WIDE)
    crouch = P(W, (60, -45), (150, -10), (75, -45), (14, 0, 36), (10, 0, 18), (0, -0.04, -0.16), (6, 0, 0), WIDE)
    draw = P(W, (10, 5), (10, 3), (75, -45), (-6, 0, -10), (0, 0, -6), (0, -0.3, -0.12), None, WIDE)
    sweep = P(W, (-85, 10), (-105, 10), (60, -40), (-8, 0, -50), (0, 0, -28), (0, -0.46, -0.14), None, WIDE)
    hold = P(W, (-130, 35), (-150, 38), (50, -35), (-4, 0, -64), (0, 0, -34), (0, -0.5, -0.12), None, WIDE)
    C["Sword_Heavy"] = ([(0, {}), (a // 2, crouch0), (a, crouch), (h, draw), (a + s, sweep), (a + s + 8, hold), (a + s + 16, hold), (a + s + r, {})], "LINEAR", False,
                        {"hit": h, "hit_start": h - 1, "hit_end": a + s + 4, "windup_end": a, "swing_end": a + s, "windup_sec": 0.30, "swing_sec": 0.07, "recover_sec": 0.40,
                         "charge_hold_from": a // 2, "cancel_from": a + s + 8,
                         "note": "발도: 선딜 구간(웅크림)은 길게 눌러 모을 수 있고 모은 시간만큼 끌어 늘려 쓴다(windup_end 직전 프레임에서 정지)"})

    # ───────────── 월도(도): 넓고 무거운 3연타. 1·2타 큰 반원 가로베기(몸 전체를 실어 돌림), 3타 도약 내려찍기(범위 큼)
    W = "Glaive"
    def twohand(az_arm, el_arm, az_w, el_w, chest, hips, hl, legs=None, head=None):
        """두 손 자세: 왼손은 자루 앞쪽을 받치므로 오른팔 방향과 비슷하게 아래로 조금 내려 둔다."""
        return P(W, (az_arm, el_arm), (az_w, el_w), (az_arm * 0.55 + 10, el_arm - 18), chest, hips, hl, head, legs)
    k, ev, _ = hwa.attack(W, 0,
        twohand(-100, 20, -140, 22, (4, 0, -52), (0, 0, -26), (0, 0.06, 0), None, (0, 0, 10)),
        twohand(-10, 8, 5, 4, (10, 0, 22), (0, 0, 12), (0, -0.22, -0.04), STEP_L),
        twohand(55, 0, 105, -12, (14, 0, 52), (0, 0, 26), (0, -0.3, -0.06), STEP_L))
    C["Glaive_Attack1"] = (k, "LINEAR", False, _ev(W, 0, ev, 0))
    k, ev, _ = hwa.attack(W, 1,    # 되돌려 치기: 왼쪽 뒤에서 오른쪽 앞으로, 올려 베며 지나간다
        twohand(70, -5, 125, -10, (6, 0, 56), (0, 0, 28), (0, 0.06, 0), None, (0, 0, -10)),
        twohand(-10, 12, -15, 8, (10, 0, -20), (0, 0, -10), (0, -0.22, -0.04), STEP_R),
        twohand(-75, 30, -115, 34, (14, 0, -54), (0, 0, -28), (0, -0.3, -0.06), STEP_R))
    C["Glaive_Attack2"] = (k, "LINEAR", False, _ev(W, 1, ev, 0))
    a, s, r = (fr(x) for x in hwa.TIM[W][2])    # 3타: 머리 위로 크게 들고 살짝 뛰어올라 몸무게 전부를 실어 내려찍는다
    up = twohand(-8, 88, 180, 72, (-30, 0, 0), (-10, 0, 0), (0, 0.14, 0.1), {"UpperLeg.L": {"r": (10, 0, 0)}, "LowerLeg.L": {"r": (24, 0, 0)}, "UpperLeg.R": {"r": (10, 0, 0)}, "LowerLeg.R": {"r": (24, 0, 0)}}, (10, 0, 0))
    mid = twohand(0, 45, 0, 28, (16, 0, 0), (6, 0, 0), (0, -0.12, 0.04), None)
    slam = twohand(0, -22, 0, -55, (50, 0, 0), (22, 0, 0), (0, -0.4, -0.22), WIDE, (-14, 0, 0))
    C["Glaive_Attack3"] = ([(0, {}), (a, up), (a + s // 2, mid), (a + s, slam), (a + s + 16, slam), (a + s + r, {})], "LINEAR", False,
                           {"hit_start": a + s - 3, "hit_end": a + s + 16, "impact": a + s, "windup_end": a, "swing_end": a + s, "windup_sec": hwa.TIM[W][2][0], "swing_sec": hwa.TIM[W][2][1], "recover_sec": hwa.TIM[W][2][2],
                            "chain_from": a + s + r // 2, "cancel_from": a + s + 8})
    # 월도 회전베기(Glaive_Spin): 낮게 몸을 감았다가 자루를 옆으로 길게 뻗은 채 한 바퀴(−360°, 오른쪽이 앞으로 가는 시계 방향) 돌아 주변을 쓴다
    a, s, r = fr(0.20), fr(0.45), fr(0.30)
    coil = twohand(-100, 5, -150, 0, (14, 0, -50), (4, 0, -24), (0, 0.04, -0.14), SQUAT, (0, 0, 14))
    def spin(rz):
        d = twohand(-85, 8, -92, 2, (6, 0, 0), (0, 0, rz), (0, 0, -0.04), WIDE)
        return d
    spin_keys = [(a + round(s * t / 4), spin(-90 * t)) for t in (1, 2, 3, 4)]
    end = twohand(-60, 5, -100, 0, (10, 0, 0), (0, 0, 0), (0, -0.04, -0.1), WIDE)
    C["Glaive_Spin"] = ([(0, {}), (a // 2, {**coil, "Hips": {"r": (0, 0, -12), "l": (0, 0.04, -0.08)}}), (a, coil)] + spin_keys[:-1] + [(a + s, {**spin(-360)}), (a + s + 6, end), (a + s + r, {})], "LINEAR", False,
                        {"hit_start": a + 3, "hit_end": a + s - 2, "windup_end": a, "swing_end": a + s, "windup_sec": 0.20, "swing_sec": 0.45, "recover_sec": 0.30, "spin_total_deg": -360, "cancel_from": a + s + 4,
                         "note": "회전은 Hips 한 뼈가 −360°. 이동은 제자리(코드가 원하면 앞으로 1.2m 밀 것)"})

    # ───────────── 공용 돌진 공격(Dash_Attack): 몸을 낮게 접었다가 한 발에 쭉 파고들며 베어 지나간다(약 3.5m 이동은 코드가 맡음)
    W = "Sword"
    a, s, r = fr(0.12), fr(0.14), fr(0.26)
    load = P(W, (-120, 15), (-6, 12), (35, 15), (24, 0, -24), (14, 0, -12), (0, 0.1, -0.16), (8, 0, 0), WIDE)
    drive = P(W, (-8, 14), (0, 12), (25, 20), (36, 0, 12), (18, 0, 6), (0, -0.55, -0.2), (-12, 0, 0), WIDE)
    pass_ = P(W, (-30, 6), (-40, 5), (30, 20), (44, 0, 24), (22, 0, 12), (0, -0.7, -0.26), (-14, 0, 0), WIDE)
    C["Dash_Attack"] = ([(0, {}), (a, load), (a + s // 2, drive), (a + s, pass_), (a + s + 6, pass_), (a + s + r, {})], "LINEAR", False,
                        {"dash_start": a, "dash_end": a + s, "hit_start": a + 2, "hit_end": a + s + 2, "hit": a + s // 2, "windup_end": a, "swing_end": a + s, "windup_sec": 0.12, "swing_sec": 0.14, "recover_sec": 0.26,
                         "travel_hint_m": 3.5, "cancel_from": a + s + 8, "note": "공용: 환도·월도 어느 쪽이든 그대로 쓴다. 이동 거리는 코드(루트 모션 없음)"})

    # ───────────── 공용 반격(Counter): 몸을 틀어 날을 세워 막는다(막기 창 f2~f11 = 0.15초) → 튕겨 내고 → 몸을 감았다가 되받아쳐 가른다(f19)
    guard = P(W, (-35, 50), (-18, 78), (30, 45), (-8, 0, -16), (0, 0, -8), (0, 0.1, -0.02), (6, 0, 0), STEP_R)
    flick = P(W, (-60, 38), (-70, 50), (30, 42), (-4, 0, -34), (0, 0, -16), (0, 0.08, 0), (4, 0, 0), STEP_R)
    tuck = P(W, (-85, 22), (-130, 26), (30, 20), (6, 0, -46), (0, 0, -22), (0, 0.04, -0.06), (0, 0, 6), WIDE)
    riposte = P(W, (-12, 8), (10, 4), (40, -5), (12, 0, 32), (0, 0, 16), (0, -0.34, -0.04), (0, 0, -4), STEP_L)
    follow = P(W, (35, -2), (78, -10), (45, -5), (12, 0, 46), (0, 0, 24), (0, -0.4, -0.04), None, STEP_L)
    C["Counter"] = ([(0, {}), (4, guard), (11, guard), (13, flick), (16, tuck), (19, riposte), (23, follow), (29, follow), (36, {})], "LINEAR", False,
                    {"parry_start": 2, "parry_end": 11, "parry_window_sec": 0.15, "hit": 19, "hit_start": 18, "hit_end": 24, "windup_end": 16, "swing_end": 23, "cancel_from": 30,
                     "note": "f2~f11 막기 창(0.15초). 창 안에 맞으면 f13 튕김 → f19 되받아치기. 창이 비면 f11 이후 자세 유지 없이 후딜(코드가 Hit로 끊음)"})
    return C
