"""맞는 쪽 손맛 동작 모음: 피격 반응 3단계, 무릎 꿇기, 천도로 흩어짐, 파혼으로 깨짐 (혼 몸·보스 공용 도구).
이름: Hit1(움찔) / Hit2(밀려남) / Stagger(크게 휘청) / Kneel(맺힘 0 무릎, 다듬음) / Tendo(천도로 흩어짐) / Pahon(파혼으로 깨짐).
원칙
 1) 위치 이동은 코드의 넉백(KNOCKBACK_TIME 0.2초 안에 1.0~3.5m)이 맡는다. 이 동작은 몸의 눌림·젖힘·되돌림만 그린다 → 이중으로 밀리지 않는다.
 2) 히트스톱(3~8프레임) 동안 동작은 멈춘다. 그래서 0번 프레임을 이미 '맞은 직후 자세'(최대의 35~50%)로 둔다. 멈춘 화면에도 맞은 모습이 보이고, 재개되면 최대치로 간다.
 3) 맞은 직후 흰 번쩍(ENEMY_FLASH_TIME 0.09초 = 5.4프레임)은 코드가 재질로 처리한다.
혼은 팔다리 없는 덩어리라 눌림(squash)·늘임(stretch)·기울기로만 표현. 정면 -Y, 혼을 때리는 차사는 앞쪽에 있으니 뒤로 젖힌다(rx 음수)."""
import math
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

def S(r=(0, 0, 0), s=(1, 1, 1), l=(0, 0, 0)): return {"r": r, "s": s, "l": l}
def mix(k, r, s, l=(0, 0, 0)):
    """강도 k(0~1+)로 자세를 섞는다: 눌림은 1에서 s까지."""
    return S(tuple(x * k for x in r), tuple(1 + (x - 1) * k for x in s), tuple(x * k for x in l))

# 형태별 곁뼈(팔·구슬)의 반응. 강도 k, 방향 d(+1 =맞은 방향으로 젖힘, -1 = 되돌림)
def extras(t, k):
    if t == "wail": return {"Arm": S(r=(28 * k, 0, 10 * k)), "Orb": S(s=(1 - 0.35 * min(k, 1.2),) * 3)}
    if t == "buried": return {"ArmL": S(r=(-30 * k, 0, 18 * k)), "ArmR": S(r=(-30 * k, 0, -18 * k))}
    return {}

def hit(t, kind):
    """kind: Hit1/Hit2/Stagger. t: basic|mote|wail|buried."""
    B = lambda k, r, s, l=(0, 0, 0), sw=0.0: {"Body": mix(k, r, s, l), **extras(t, k * (1 if sw == 0 else sw))}
    if kind == "Hit1":     # 움찔 10f(0.17초): 살짝 젖혔다가 곧바로 돌아온다 — 1타(밀려남 1.0m)
        P = lambda k: B(k, (-9, 0, 2), (1.07, 1.07, 0.91), (0, 0.03, 0))
        return ([(0, P(0.45)), (2, P(1.0)), (5, P(0.4)), (10, {})], "BEZIER", False, {"peak": 2, "recover_start": 5, "knockback_hint_m": 1.0})
    if kind == "Hit2":     # 밀려남 16f(0.27초): 크게 젖히고 반동으로 되튄 뒤 가라앉는다 — 2타(1.3m)·견인
        P = lambda k: B(k, (-22, 0, 4), (1.14, 1.14, 0.8), (0, 0.06, 0))
        return ([(0, P(0.5)), (3, P(1.0)), (7, B(0.4, (8, 0, -2), (0.96, 0.96, 1.07))), (11, P(0.2)), (16, {})], "BEZIER", False, {"peak": 3, "rebound": 7, "recover_start": 11, "knockback_hint_m": 1.3})
    # 크게 휘청 30f(0.5초): 크게 젖혀 휘청거리다 두어 번 흔들려 중심을 잡는다 — 3타(3.5m)·파혼 명중
    R = lambda r, s, k=1.0: B(k, r, s)
    return ([(0, B(0.5, (-36, 0, 10), (1.2, 1.2, 0.7), (0, 0.1, 0))), (4, B(1.0, (-36, 0, 10), (1.2, 1.2, 0.7), (0, 0.1, 0))), (9, R((14, 0, -8), (0.95, 0.95, 1.1), 1.0)),
             (14, R((-14, 0, 7), (1.08, 1.08, 0.88), 0.9)), (19, R((7, 0, -4), (0.98, 0.98, 1.04), 0.6)), (24, R((-3, 0, 2), (1.02, 1.02, 0.97), 0.4)), (30, {})],
            "BEZIER", False, {"peak": 4, "sway_peaks": [9, 14, 19, 24], "recover_start": 24, "knockback_hint_m": 3.5})

def kneel(t, tail):
    """맺힘 0 → 무릎 꿇음 36f. 다듬은 점: ① 버티다 한 번 움찔(예비) ② 쿵 하고 눌림 ③ 반동으로 살짝 튀었다 ④ 가라앉아 끝 자세 유지. tail=형태별 끝 자세(기존과 같아서 Tendo/Pahon이 이어받는다).
    event thud=14 (코드가 바닥 먼지·소리), end_pose_held."""
    B = lambda **k: {"Body": S(**k)}
    ex = lambda k: extras(t, k)
    sag = {**B(r=(-6, 0, 0), s=(1.05, 1.05, 0.9)), **ex(0.3)}
    thud = {**B(r=(32, 0, 0), s=(1.2, 1.2, 0.46)), **ex(-0.3)}
    bounce = {**B(r=(22, 0, 0), s=(1.1, 1.1, 0.7)), **ex(0.2)}
    return ([(0, {}), (6, sag), (14, thud), (19, bounce), (27, tail), (36, tail)], "BEZIER", False, {"thud": 14, "bounce": 19, "end_pose_held": True})

TAIL = {  # 기존 Kneel의 끝 자세(수정 전과 같다)
    "basic": {"Body": S(r=(26, 0, 0), s=(1.15, 1.15, 0.53))},
    "mote": {"Body": S(r=(20, 0, 0), s=(1.34, 1.34, 0.26))},
    "wail": {"Body": S(r=(28, 0, 0), s=(1.15, 1.15, 0.53)), "Arm": S(r=(8, 0, 12)), "Orb": S(s=(0.01, 0.01, 0.01))},
    "buried": {"Body": S(l=(0, 0, -0.7), r=(38, 0, 0), s=(1.12, 1.12, 0.56)), "ArmL": S(r=(10, 0, 14)), "ArmR": S(r=(10, 0, -14))},
}

def tendo(t):
    """천도로 흩어짐 48f(0.8초): 무릎 꿇은 혼이 일어나 위로 길게 늘어나며 가늘어져 빛으로 풀린다. 맨 끝은 크기 0에 가깝다(코드가 같은 시점에 빛 알갱이를 뿜는다).
    events: lift=10(일어남) glow=24(밝아짐 시작) burst=36(알갱이 폭발) gone=47(모델 숨김)."""
    k0 = TAIL[t]; B = lambda **k: S(**k)
    up = {"buried": (-160, 0, -35)}.get(t)
    def arms(a):
        if t == "wail": return {"Arm": S(r=(150 * a, 0, 0)), "Orb": S(s=(0.01,) * 3)}
        if t == "buried": return {"ArmL": S(r=(-160 * a, 0, -35 * a)), "ArmR": S(r=(-160 * a, 0, 35 * a))}
        return {}
    zoff = -0.6 if t == "buried" else 0.0     # 묻힌 혼은 흙에서 반쯤 가라앉은 채 시작
    f = lambda zr, sx, sz, a, rz=0, rx=0, lz=0: {"Root": S(l=(0, 0, zr)), "Body": S(r=(rx, 0, rz), s=(sx, sx, sz), l=(0, 0, lz)), **arms(a)}
    return ([(0, k0), (10, f(0.04, 1.0, 0.95, 0.3, lz=zoff * 0.6)), (24, f(0.25, 0.9, 1.25, 0.8, rz=6, rx=-4, lz=zoff * 0.2)), (36, f(0.9, 0.55, 1.75, 1.0, rz=-10, rx=-6)),
             (44, f(1.7, 0.18, 2.3, 1.0, rz=14)), (47, f(2.1, 0.02, 2.5, 1.0, rz=18))], "BEZIER", False, {"lift": 10, "glow": 24, "burst": 36, "gone": 47, "hide_after": 47})

def pahon(t):
    """파혼으로 깨짐 18f(0.3초): 몸이 들썩이며 금이 가고(눌렸다) 안에서 터져 부풀며 사라진다. 파편은 fx_hon_shards.glb(주황=파혼색)를 코드가 같은 프레임에 터뜨린다.
    events: crack=5(금), shatter=9(터짐·파편 발사), gone=13(모델 숨김). PAHON_HITSTOP_FRAMES 8 동안은 0번 자세로 정지(떨림만)."""
    k0 = TAIL[t]
    def sq(sx, sz, rz=0, r=0, a=None): return {"Body": S(r=(r, 0, rz), s=(sx, sx, sz)), "Root": S(r=(0, 0, rz * 0.5)), **(a or {})}
    arms = lambda v: {"Arm": S(r=(v, 0, 0))} if t == "wail" else ({"ArmL": S(r=(v, 0, 0)), "ArmR": S(r=(v, 0, 0))} if t == "buried" else {})
    return ([(0, k0), (2, sq(1.18, 0.4, 7, 22, arms(30))), (4, sq(1.1, 0.5, -7, 18, arms(40))), (5, sq(1.3, 0.34, 4, 16, arms(50))), (7, sq(1.2, 1.1, -3, -8, arms(80))),
             (9, sq(1.85, 1.6, 0, -14, arms(110))), (11, sq(2.3, 1.1, 0, -10, arms(140))), (13, sq(0.02, 0.02)), (18, sq(0.02, 0.02))], "LINEAR", False,
            {"crack": 5, "shatter": 9, "gone": 13, "hide_after": 13})

def soul_clips(t):
    """혼 한 형태에 더할 동작 6개. t: basic|mote|wail|buried"""
    C = {k: hit(t, k) for k in ("Hit1", "Hit2", "Stagger")}
    C["Kneel"] = kneel(t, TAIL[t]); C["Tendo"] = tendo(t); C["Pahon"] = pahon(t)
    return C
