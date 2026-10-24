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
    return C

if __name__ == "__main__":
    reset(); anim.setup_scene()
    o = join("boss_naru", naru(False)); arm = rig(o, BONES); man = []
    for cn, (keys, interp, loop, ev) in clips().items():
        i = anim.clip(arm, cn, keys, interp); i.update({"loop": loop, "events": ev}); man.append(i)
    if "--sheets" in sys.argv:
        setup_render(8.0, (0, 0, 1.2), size=(260, 300), ground_size=14)
        for c in man:
            if c["name"] != "Idle": anim.sheet(arm, c["name"], {"Windup": [0, 20, 40, 56, 65], "Swing": [0, 4, 8, 11, 14, 24, 41]}[c["name"]], os.path.join(OUT, "previews", f"anim_naru_{c['name']}"), cell=(260, 300))
    p = os.path.join(OUT, "boss", "boss_naru.glb"); anim.export_rig(arm, p); v = anim.verify(p); print(v)
    json.dump({"fps": anim.FPS, "clips": man, "verify": v}, open(os.path.join(OUT, "boss", "_naru_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
