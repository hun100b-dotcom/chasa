"""혼 동작 4개(60fps): Float(떠돌기, 반복 90f) / Windup(공격 예고 33f=0.55초, 번쩍 신호 f21) / Attack(공격 18f, 명중 f5) / Kneel(무릎 꿇음 36f, 끝 자세 유지).
혼은 팔다리가 없는 덩어리라 '몸 전체'를 눌러 늘이고 기울이는 방식(스쿼시·스트레치)으로 표현한다. 뼈는 Root(제자리 이동)와 Body(눌림·기울기) 둘뿐.
기본 4종과 지역 변형 12종 모두 같은 동작을 담는다."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import souls, rig, to_group
from soul_variants import variant, REGIONS, BASE
import anim
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
BONES = [("Root", None, (0, 0, 0), (0, 0, 0.2)), ("Body", "Root", (0, 0, 0), (0, 0, 0.6))]

def clips():
    B = lambda r=(0, 0, 0), s=(1, 1, 1), l=(0, 0, 0): {"Body": {"r": r, "s": s, "l": l}}
    C = {}
    fl_a = {"Root": {"l": (0, 0, 0)}, **B((3, 0, -4))}; fl_b = {"Root": {"l": (0, 0, 0.09)}, **B((-3, 0, 4), (0.98, 0.98, 1.03))}
    C["Float"] = ([(0, fl_a), (45, fl_b), (90, fl_a)], "BEZIER", True, {})
    w1 = B((-14, 0, 0), (1.08, 1.08, 0.85)); w2 = B((-18, 0, 0), (1.12, 1.12, 0.8)); w3 = B((-18, 0, 1.5), (1.13, 1.12, 0.79))
    C["Windup"] = ([(0, fl_a), (12, w1), (21, w2), (27, w3), (33, w2)], "BEZIER", False, {"flash": 21, "end_pose_held": True})
    lunge = {"Root": {"l": (0, -0.7, 0)}, **B((30, 0, 0), (0.88, 0.88, 1.18))}
    C["Attack"] = ([(0, w2), (4, lunge), (6, lunge), (12, {"Root": {"l": (0, -0.3, 0)}, **B((8, 0, 0), (1.04, 1.04, 0.94))}), (18, {})], "LINEAR", False, {"hit": 5})
    kn = {**B((24, 0, 0), (1.14, 1.14, 0.55)), "Root": {"l": (0, 0, 0)}}; kn2 = {**B((26, 0, 0), (1.15, 1.15, 0.53))}
    C["Kneel"] = ([(0, {}), (10, B((-6, 0, 0), (1.06, 1.06, 0.82))), (20, kn), (36, kn2)], "BEZIER", False, {"end_pose_held": True})
    return C

if __name__ == "__main__":
    rep = []
    jobs = [(f"soul_{k}", lambda k=k: souls()[k]()) for k in BASE] + [(f"soul_{k}_{r}", lambda k=k, r=r: variant(k, r)) for r in REGIONS for k in BASE]
    for name, fn in jobs:
        reset(); anim.setup_scene()
        o = join(name, to_group(fn(), "Body")); arm = rig(o, BONES)
        man = []
        for cn, (keys, interp, loop, ev) in clips().items():
            i = anim.clip(arm, cn, keys, interp); i.update({"loop": loop, "events": ev}); man.append(i)
        if name == "soul_old_soegol":
            setup_render(2.6, (0, 0, 0.6), size=(200, 240), ground_size=8)
            for c in man: anim.sheet(arm, c["name"], sorted({0, c["frames"] // 3, 2 * c["frames"] // 3, c["frames"] - 1}), os.path.join(OUT, "previews", f"anim_soul_{c['name']}"), ortho=2.6, cell=(200, 240))
        p = os.path.join(OUT, "souls", f"{name}.glb"); anim.export_rig(arm, p); v = anim.verify(p); rep.append(v)
    json.dump({"fps": anim.FPS, "clips": man, "files": rep}, open(os.path.join(OUT, "souls", "_soul_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
    print(len(rep), "개", {(r["skins"], r["joints"], len(r["animations"])) for r in rep})
