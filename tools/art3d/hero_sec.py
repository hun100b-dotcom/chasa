"""주인공 보조 뼈(도포 자락·갓끈·허리띠 끝·노리개) — 몸 뼈 16개는 그대로 두고 12개를 덧붙인다.
왜 덧붙이기만 하나: 옛 동작(공격·피하기 등)과 코드팀이 이미 쓰는 뼈 이름은 하나도 바뀌지 않아야 하기 때문.
옛 동작은 이 뼈를 건드리지 않아도 되고(기본 자세), 움직이는 동작에는 hero_locomotion.bake_secondary()가 흔들림을 구워 넣는다.
뼈 이름 규칙: 자락 Skirt_F/B/L/R(앞·뒤·왼·오른), 갓끈 Strap.L1/L2/R1/R2(위→아래), 허리띠 끝 SashA1/A2/B1, 노리개 술 Orn."""
import math
import bpy
from mathutils import Vector
from look_v2 import hero2

# (이름, 부모, 머리, 꼬리) — 블렌더 좌표(Z 위, 정면 -Y, +X 캐릭터 왼쪽). 모양(look_v2.hero2)의 좌표와 같다.
SEC_BONES = [
    ("Skirt_F", "Hips", (0.0, -0.20, 0.78), (0.0, -0.24, 0.25)),
    ("Skirt_B", "Hips", (0.0, 0.20, 0.78), (0.0, 0.24, 0.25)),
    ("Skirt_L", "Hips", (0.22, 0.0, 0.78), (0.26, 0.0, 0.25)),
    ("Skirt_R", "Hips", (-0.22, 0.0, 0.78), (-0.26, 0.0, 0.25)),
    ("Strap.L1", "Head", (0.12, -0.04, 1.665), (0.095, -0.14, 1.42)), ("Strap.L2", "Strap.L1", (0.095, -0.14, 1.42), (0.07, -0.205, 1.12)),
    ("Strap.R1", "Head", (-0.12, -0.04, 1.665), (-0.095, -0.14, 1.42)), ("Strap.R2", "Strap.R1", (-0.095, -0.14, 1.42), (-0.07, -0.205, 1.12)),
    ("SashA1", "Hips", (0.09, -0.27, 0.94), (0.12, -0.31, 0.62)), ("SashA2", "SashA1", (0.12, -0.31, 0.62), (0.14, -0.38, 0.22)),
    ("SashB1", "Hips", (0.14, -0.27, 0.93), (0.30, -0.31, 0.52)),
    ("Orn", "Hips", (-0.2, -0.22, 0.80), (-0.2, -0.235, 0.56)),
]
SEC_NAMES = [b[0] for b in SEC_BONES]

def _sm(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def _world(o):
    return [o.matrix_world @ v.co for v in o.data.vertices]

def _weights(o, fn):
    """fn(좌표) -> {뼈: 가중치}. 합이 1이 되게 만들어 넣는다(옛 100% 묶음은 지운다)."""
    o.vertex_groups.clear()
    groups = {}
    for v, p in zip(o.data.vertices, _world(o)):
        w = fn(p); s = sum(w.values()) or 1.0
        for b, x in w.items():
            if x <= 1e-4: continue
            if b not in groups: groups[b] = o.vertex_groups.new(name=b)
            groups[b].add([v.index], x / s, "REPLACE")

def _skirt(p):
    # 높이가 내려갈수록(허리 0.8m → 밑단 0.25m) 흔들리는 비중이 커지고, 방향(앞·뒤·좌·우)에 따라 가까운 뼈에 나눠 묶는다
    t = _sm((0.80 - p.z) / 0.55) ** 1.1
    phi = math.atan2(p.x, -p.y)            # 0=앞, +90°=왼쪽, 180°=뒤
    c = {"Skirt_F": 0.0, "Skirt_L": math.pi / 2, "Skirt_B": math.pi, "Skirt_R": -math.pi / 2}
    w = {}
    for b, a in c.items():
        d = math.atan2(math.sin(phi - a), math.cos(phi - a))
        w[b] = max(0.0, math.cos(d)) ** 2 * t
    w["Hips"] = 1.0 - t
    return w

def _strap(side):
    def f(p):
        wh = _sm((p.z - 1.50) / 0.16)       # 챙 가까이는 머리에 붙어 있고
        w2 = (1 - wh) * _sm((1.40 - p.z) / 0.2)   # 아래로 갈수록 끝마디가 더 흔들린다
        return {"Head": wh, f"Strap.{side}1": 1 - wh - w2, f"Strap.{side}2": w2}
    return f

def _tailA(p):
    wh = _sm((p.z - 0.80) / 0.14); w2 = (1 - wh) * _sm((0.60 - p.z) / 0.25)
    return {"Hips": wh, "SashA1": 1 - wh - w2, "SashA2": w2}

def _tailB(p):
    wh = _sm((p.z - 0.78) / 0.15)
    return {"Hips": wh, "SashB1": 1 - wh}

def _tassel(p):
    wh = _sm((p.z - 0.74) / 0.07)
    return {"Hips": wh, "Orn": 1 - wh}

def hero_sec():
    """look_v2.hero2()의 조각들을 만들고, 흔들릴 조각만 가중치를 새로 준다."""
    parts = hero2()
    for o in parts:
        n = o.name
        if n.startswith("skirt") or n.startswith("lining"): _weights(o, _skirt)
        elif n.startswith("tailA"): _weights(o, _tailA)
        elif n.startswith("tailB"): _weights(o, _tailB)
        elif n.startswith("orn_tassel"): _weights(o, _tassel)
        elif n.startswith("strapL"): _weights(o, _strap("L"))
        elif n.startswith("strapR"): _weights(o, _strap("R"))
        elif n.startswith("bead"):
            side = "L" if _world(o)[0].x > 0 else "R"
            _weights(o, _strap(side))
    return parts
