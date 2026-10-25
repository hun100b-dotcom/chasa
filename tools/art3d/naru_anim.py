"""나루 영감 동작: Idle(반복 96f) / Windup(예비동작 66f≈1.1초, 보스 큰 기술 예고 기준) / Swing(삿대 휘두르기 42f: 휘두름 14f, 명중 f8, 후딜 28f).
오른팔과 삿대 뼈가 함께 돌고, 상체가 뒤틀려 힘을 싣는다. 배는 흔들린다."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from boss_naru import naru, BONES
from characters import rig
import anim
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def clips():
    C = {}
    a = {"Boat": {"r": (1.5, 0, -1), "l": (0, 0, 0)}, "Chest": {"r": (1, 0, 0)}}; b = {"Boat": {"r": (-1.5, 0, 1), "l": (0, 0, 0.03)}, "Chest": {"r": (-1, 0, 0)}}
    C["Idle"] = ([(0, a), (48, b), (96, a)], "BEZIER", True, {})
    # 예비동작: 삿대 끝이 뒤로 젖혀지고(팔 +110°) 상체가 오른쪽으로 감긴다
    def wind(k=1.0, sh=0):
        return {"UpperArm.R": {"r": (95 * k, 0, 0)}, "Pole": {"r": (15 * k, 0, -10 * k)}, "Chest": {"r": (6 * k, 0, -42 * k)}, "Hips": {"r": (0, 0, -14 * k)}, "Head": {"r": (0, 0, 20 * k)}, "UpperArm.L": {"r": (-20 * k, -25 * k, 0)}, "Boat": {"r": (-3 * k, 0, 0)}}
    C["Windup"] = ([(0, {}), (20, wind(0.35)), (56, wind(1.0)), (60, {**wind(1.0), "Chest": {"r": (6, 0, -45)}}), (66, wind(1.0))], "BEZIER", False, {"flash": 54, "end_pose_held": True})
    sw = lambda k=1.0: {"UpperArm.R": {"r": (-75 * k, 0, 0)}, "Pole": {"r": (-10 * k, 0, 25 * k)}, "Chest": {"r": (8 * k, 0, 55 * k)}, "Hips": {"r": (0, 0, 20 * k)}, "Head": {"r": (0, 0, -25 * k)}, "UpperArm.L": {"r": (10 * k, 20 * k, 0)}, "Boat": {"r": (4 * k, 0, 0), "l": (0, -0.12 * k, 0)}}
    C["Swing"] = ([(0, wind(1.0)), (8, sw(0.45)), (14, sw(1.0)), (24, sw(0.9)), (42, {})], "LINEAR", False, {"hit": 8, "swing_end": 14})
    # ── 맞는 쪽 손맛(10-25) ── 보스는 위치가 안 밀리고(코드 넉백 0 권장) 몸이 젖혀지며 배가 출렁인다. 0번 프레임 = 히트스톱에 멈춰 보일 '맞은 직후' 자세.
    R_ = lambda **k: {n_: {"r": v} for n_, v in k.items()}
    C["Hit1"] = ([(0, R_(Chest=(-5, 0, 2), Head=(-5, 0, 0), Boat=(-1.5, 0, 0))), (2, R_(Chest=(-8, 0, 3), Head=(-8, 0, 0), Boat=(-2.5, 0, 0))), (10, {})], "BEZIER", False, {"peak": 2})
    h2 = R_(Chest=(-16, 0, 6), Head=(-14, 0, 0), Boat=(-4, 0, 2), Hips=(-4, 0, 0)); h2["UpperArm.R"] = {"r": (14, 0, 0)}; h2["Pole"] = {"r": (6, 0, 0)}
    C["Hit2"] = ([(0, R_(Chest=(-8, 0, 3), Head=(-7, 0, 0))), (3, h2), (8, R_(Chest=(5, 0, -2), Head=(4, 0, 0), Boat=(2, 0, -1))), (18, {})], "BEZIER", False, {"peak": 3, "rebound": 8})
    st = R_(Chest=(-26, 0, 10), Head=(-20, 0, 0), Boat=(-6, 0, 3), Hips=(-8, 0, 0)); st["UpperArm.R"] = {"r": (30, 0, 0)}; st["UpperArm.L"] = {"r": (20, 10, 0)}; st["Hips"]["l"] = (0, 0.12, 0)
    C["Stagger"] = ([(0, R_(Chest=(-12, 0, 5), Head=(-10, 0, 0))), (5, st), (12, R_(Chest=(10, 0, -4), Boat=(3, 0, -2), Head=(6, 0, 0))), (20, R_(Chest=(-10, 0, 3), Boat=(-2, 0, 1))), (28, R_(Chest=(3, 0, -1))), (36, {})], "BEZIER", False, {"peak": 5, "sway_peaks": [12, 20, 28]})
    kn = {"Hips": {"l": (0, 0, -0.42)}, "Chest": {"r": (16, 0, 0)}, "Head": {"r": (22, 0, 0)}, "UpperArm.R": {"r": (10, 0, 0)}, "UpperArm.L": {"r": (14, 0, 0)}, "Pole": {"r": (-14, 0, 10)}, "Boat": {"r": (2, 0, 0)}}
    kn2 = {**kn, "Chest": {"r": (14, 0, 0)}, "Head": {"r": (19, 0, 0)}, "Boat": {"r": (-1.5, 0, 0), "l": (0, 0, 0.02)}}
    C["Kneel"] = ([(0, {}), (14, {"Hips": {"l": (0, 0, -0.1)}, "Chest": {"r": (6, 0, 0)}, "Head": {"r": (8, 0, 0)}}), (26, {**kn, "Hips": {"l": (0, 0, -0.5)}, "Boat": {"r": (4, 0, 0)}}), (40, kn), (60, kn)], "BEZIER", False, {"thud": 26, "end_pose_held": True})
    C["KneelHold"] = ([(0, kn), (60, kn2), (120, kn)], "BEZIER", True, {})
    # 천도 3.5초(210f): 일어서(0~60) 삿대를 배에 눕히고(60~130) 깊이 허리를 숙여(130~170) 흩어진다
    pole_down = {"UpperArm.R": {"r": (-50, 0, 0)}, "Pole": {"r": (-70, 0, 8)}, "Chest": {"r": (8, 0, 0)}, "Head": {"r": (6, 0, 0)}}
    bow = {"Chest": {"r": (32, 0, 0)}, "Head": {"r": (26, 0, 0)}, "UpperArm.R": {"r": (-50, 0, 0)}, "UpperArm.L": {"r": (22, 0, 0)}, "Pole": {"r": (-70, 0, 8)}}
    C["Tendo"] = ([(0, kn), (30, {"Hips": {"l": (0, 0, -0.18)}, "Chest": {"r": (10, 0, 0)}, "Head": {"r": (12, 0, 0)}}), (60, {}), (110, pole_down), (130, pole_down), (170, bow), (200, bow), (210, bow)], "BEZIER", False, {"stand_up": 60, "pole_set": 110, "bow": 170, "dissolve": 210})
    # 파혼 2초(120f): 폭발에 젖혀져 삿대를 놓치고 주저앉는다
    C["Pahon"] = ([(0, {}), (6, {"Chest": {"r": (-30, 0, 0)}, "Head": {"r": (-24, 0, 0)}, "UpperArm.R": {"r": (60, 0, 0)}, "UpperArm.L": {"r": (50, 30, 0)}, "Pole": {"r": (30, 0, 14)}, "Boat": {"r": (-7, 0, 0)}}),
                   (30, {"Chest": {"r": (-14, 0, 0)}, "Head": {"r": (-12, 0, 0)}, "UpperArm.R": {"r": (30, 0, 0)}, "Pole": {"r": (20, 0, 10)}, "Hips": {"l": (0, 0, -0.1)}}), (80, kn), (120, kn)], "BEZIER", False, {"blast": 6})
    return C

if __name__ == "__main__":
    reset(); anim.setup_scene()
    o = join("boss_naru", naru(False)); arm = rig(o, BONES); man = []
    for cn, (keys, interp, loop, ev) in clips().items():
        i = anim.clip(arm, cn, keys, interp); i.update({"loop": loop, "events": ev}); man.append(i)
    if "--sheets" in sys.argv:
        setup_render(8.0, (0, 0, 1.2), size=(260, 300), ground_size=14)
        for c in man:
            if c["name"] in ("Idle", "KneelHold") or c["name"] not in ("Windup", "Swing", "Hit1", "Hit2", "Stagger", "Kneel", "Tendo", "Pahon"): continue
            if True: anim.sheet(arm, c["name"], {"Windup": [0, 20, 40, 56, 65], "Swing": [0, 4, 8, 11, 14, 24, 41], "Hit1": [0, 2, 5, 10], "Hit2": [0, 3, 8, 18], "Stagger": [0, 5, 12, 20, 36], "Kneel": [0, 14, 26, 60], "Tendo": [0, 60, 110, 170, 210], "Pahon": [0, 6, 30, 80, 120]}[c["name"]], os.path.join(OUT, "previews", f"anim_naru_{c['name']}"), cell=(260, 300))
    p = os.path.join(OUT, "boss", "boss_naru.glb"); anim.export_rig(arm, p); v = anim.verify(p); print(v)
    json.dump({"fps": anim.FPS, "clips": man, "verify": v}, open(os.path.join(OUT, "boss", "_naru_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
