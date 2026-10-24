"""주인공 동작 10개(60fps). 타격감 값표(planning/combat/feel)와 data/growth.json 철삭 수치의 프레임 수에 맞춘다.
철삭 1타 선딜 5f·휘두름 9f·후딜 8f=22f / 2타 같은 22f / 3타 선딜 10f·휘두름 18f·후딜 22f=50f / 피하기 19f(무적 2~15f) / 파혼 후딜 15f.
때리는 순간(event hit)은 코드팀 요청대로 Attack1이 전체의 45% 지점(f10)이다."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import hero, rig, BONES
import anim
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def mirror(spec):
    """좌우 대칭(걷기 한 걸음 뒤 반대 발)."""
    sw = lambda n: n.replace(".L", ".#").replace(".R", ".L").replace(".#", ".R")
    out = {}
    for k, v in spec.items():
        v = dict(v)
        if "r" in v: rx, ry, rz = v["r"]; v["r"] = (rx, -ry, -rz)
        if "l" in v: x, y, z = v["l"]; v["l"] = (-x, y, z)
        out[sw(k)] = v
    return out

def walk_keys():
    # 접지(왼발 앞) / 지나감(오른발 들림) 두 자세와 그 좌우 대칭으로 36프레임 한 바퀴
    A = {"UpperLeg.L": {"r": (-28, 0, 0)}, "LowerLeg.L": {"r": (4, 0, 0)}, "Foot.L": {"r": (24, 0, 0)},
         "UpperLeg.R": {"r": (18, 0, 0)}, "LowerLeg.R": {"r": (30, 0, 0)}, "Foot.R": {"r": (-48, 0, 0)},
         "UpperArm.R": {"r": (-22, 0, 0)}, "UpperArm.L": {"r": (18, 0, 0)}, "Chest": {"r": (2, 0, 7)}, "Hips": {"r": (0, 0, -5), "l": (0, 0, 0)}, "Head": {"r": (0, 0, -3)}}
    B = {"UpperLeg.L": {"r": (0, 0, 0)}, "UpperLeg.R": {"r": (-26, 0, 0)}, "LowerLeg.R": {"r": (48, 0, 0)}, "Foot.R": {"r": (-22, 0, 0)},
         "Chest": {"r": (2, 0, 0)}, "Hips": {"r": (0, 0, 0), "l": (0, 0, 0.035)}}
    return [(0, A), (9, B), (18, mirror(A)), (27, mirror(B)), (36, A)]

IDLE = {}
def idle_keys():
    a = {"Chest": {"r": (-1.5, 0, 0)}, "Head": {"r": (1.2, 0, 0)}, "UpperArm.L": {"r": (0, -2, 0)}, "UpperArm.R": {"r": (0, 2, 0)}, "Hips": {"l": (0, 0, 0)}}
    b = {"Chest": {"r": (1.5, 0, 0)}, "Head": {"r": (-1.2, 0, 0)}, "UpperArm.L": {"r": (0, 2, 0)}, "UpperArm.R": {"r": (0, -2, 0)}, "Hips": {"l": (0, 0, 0.012)}}
    return [(0, a), (48, b), (96, a)]

def slash(arm_rz, chest_rz, hips_rz, lean=0, shift=0, **kw):
    """한 자세: 오른팔을 옆으로 들고(ry 55) 위에서 본 방향 arm_rz로 돌린다."""
    d = {"UpperArm.R": {"r": (0, 55, arm_rz)}, "Hand.R": {"r": (0, 0, 0)}, "UpperArm.L": {"r": (0, -20, 0)},
         "Chest": {"r": (lean, 0, chest_rz)}, "Hips": {"r": (0, 0, hips_rz), "l": (0, shift, kw.get("dz", 0))}, "Head": {"r": (0, 0, -chest_rz * 0.5)}}
    d.update(kw.get("extra", {})); return d

def clips():
    C = {}
    C["Idle"] = (idle_keys(), "BEZIER", True, None)
    C["Walk"] = (walk_keys(), "BEZIER", True, None)
    # 1타 횡베기: 오른쪽 뒤로 젖힘(f5) → 왼쪽 앞으로 휘두름(f14) → 복귀(f22)
    C["Attack"] = ([(0, {}), (5, slash(-25, -32, -10, 6, 0.04)), (10, slash(55, 4, 2, 6, -0.06)), (14, slash(95, 38, 14, 4, -0.1)), (22, {})], "LINEAR", False, {"hit": 10, "windup_end": 5, "swing_end": 14})
    # 2타 역횡베기: 왼쪽에서 오른쪽으로 되받아침
    C["Attack2"] = ([(0, {}), (5, slash(105, 38, 14, 6, -0.04)), (10, slash(40, 0, 0, 6, -0.06)), (14, slash(-20, -35, -12, 4, -0.1)), (22, {})], "LINEAR", False, {"hit": 10, "windup_end": 5, "swing_end": 14})
    # 3타 회전 후려치기: 웅크려 젖힘(10f) → 한 바퀴 회전(18f) → 긴 후딜(22f)
    spin = lambda rz: {"Root": {"r": (0, 0, rz)}}
    def s3(rz, arm=70, ch=0, dz=-0.05):
        d = slash(arm, ch, 0, 10, -0.05, dz=dz); d.update(spin(rz)); return d
    C["Attack3"] = ([(0, {}), (10, {**slash(-45, -55, -20, 14, 0.06, dz=-0.07), **spin(0)}), (14.5, s3(90)), (19, s3(180)), (23.5, s3(270)), (28, s3(360, 80, 8)), (36, {"Root": {"r": (0, 0, 360)}, "Chest": {"r": (4, 0, 0)}, "UpperArm.R": {"r": (0, 20, 0)}}),
                     (50, {"Root": {"r": (0, 0, 360)}})], "LINEAR", False, {"hit_start": 14, "hit_end": 28, "windup_end": 10, "swing_end": 28})
    # 피하기: 앞으로 낮게 파고듦(무적 2~15f)
    lunge = {"Chest": {"r": (32, 0, 0)}, "Head": {"r": (-18, 0, 0)}, "Hips": {"r": (14, 0, 0), "l": (0, -0.12, 0)}, "UpperLeg.L": {"r": (-38, 0, 0)}, "LowerLeg.L": {"r": (10, 0, 0)}, "UpperLeg.R": {"r": (30, 0, 0)}, "LowerLeg.R": {"r": (30, 0, 0)},
             "UpperArm.L": {"r": (40, -10, 0)}, "UpperArm.R": {"r": (44, 10, 0)}}
    C["Dodge"] = ([(0, {}), (4, lunge), (14, lunge), (19, {})], "BEZIER", False, {"iframe_start": 2, "iframe_end": 15})
    # 맞음: 뒤로 젖혀지며 팔이 벌어짐(18f)
    rec = {"Chest": {"r": (-22, 0, 0)}, "Head": {"r": (-20, 0, 0)}, "Hips": {"r": (-6, 0, 0), "l": (0, 0.09, 0)}, "UpperArm.L": {"r": (10, -28, 0)}, "UpperArm.R": {"r": (10, 28, 0)}}
    half = {k: {**v, "r": tuple(a * 0.35 for a in v["r"]), **({"l": tuple(a * 0.35 for a in v["l"])} if "l" in v else {})} for k, v in rec.items()}
    C["Hit"] = ([(0, {}), (3, rec), (8, half), (18, {})], "BEZIER", False, {"impact": 3})
    # 천도 시전: 두 팔을 위로(14f) → 버티며 호흡(32f) → 내림(14f) 총 60f
    up = {"UpperArm.L": {"r": (0, -140, 0)}, "UpperArm.R": {"r": (0, 140, 0)}, "Chest": {"r": (-8, 0, 0)}, "Head": {"r": (-10, 0, 0)}, "Hips": {"r": (0, 0, 0)}}
    up2 = {**up, "Chest": {"r": (-11, 0, 0)}, "UpperArm.L": {"r": (0, -146, 0)}, "UpperArm.R": {"r": (0, 146, 0)}}
    C["Cast"] = ([(0, {}), (14, up), (30, up2), (46, up), (60, {})], "BEZIER", False, {"hold_start": 14, "hold_end": 46})
    # 파혼: 웅크려 감았다가(6f) 확 터뜨림(f8) → 굳은 뒤 풀림(15f) 총 25f
    coil = {"Chest": {"r": (24, 0, 0)}, "Head": {"r": (-8, 0, 0)}, "Hips": {"r": (10, 0, 0), "l": (0, -0.04, 0)}, "UpperArm.L": {"r": (-55, 40, 0)}, "UpperArm.R": {"r": (-55, -40, 0)}, "UpperLeg.L": {"r": (-12, 0, 0)}, "UpperLeg.R": {"r": (-12, 0, 0)}}
    burst = {"Chest": {"r": (-16, 0, 0)}, "Head": {"r": (-10, 0, 0)}, "Hips": {"r": (-6, 0, 0)}, "UpperArm.L": {"r": (0, -95, 0)}, "UpperArm.R": {"r": (0, 95, 0)}}
    C["Pahon"] = ([(0, {}), (6, coil), (8, burst), (13, burst), (25, {})], "LINEAR", False, {"hit": 8, "recover_dodge_from": 10})
    return C

def build():
    reset(); anim.setup_scene()
    o = join("hero_chasa", hero()); arm = rig(o)
    return o, arm

if __name__ == "__main__":
    o, arm = build(); man = []
    for name, (keys, interp, loop, ev) in clips().items():
        info = anim.clip(arm, name, keys, interp); info.update({"loop": loop, "events": ev or {}}); man.append(info)
    if "--sheets" in sys.argv:
        setup_render(3.0, (0, 0, 1.0), size=(220, 280), ground_size=10)
        for c in man:
            n = c["frames"]; fr = sorted({0, *[round(n * t) for t in (0.2, 0.4, 0.6, 0.8)], n - 1}) if c["name"] not in ("Attack", "Attack2") else [0, 5, 8, 10, 12, 14, 21]
            anim.sheet(arm, c["name"], fr, os.path.join(OUT, "previews", f"anim_hero_{c['name']}"))
    path = os.path.join(OUT, "characters", "hero_chasa.glb")
    anim.export_rig(arm, path)
    v = anim.verify(path); print(v)
    json.dump({"fps": anim.FPS, "clips": man, "verify": v}, open(os.path.join(OUT, "characters", "_hero_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
