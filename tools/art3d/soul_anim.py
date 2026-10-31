"""혼 동작(60fps; 아래 4개 + hit_react.py의 Hit1·Hit2·Stagger·Tendo·Pahon, Kneel은 그쪽 것으로 대체): Float(떠돌기, 반복 90f) / Windup(공격 예고 33f=0.55초, 번쩍 신호 f21) / Attack(공격 18f, 명중 f5) / Kneel(무릎 꿇음 36f, 끝 자세 유지).
혼은 팔다리가 없는 덩어리라 '몸 전체'를 눌러 늘이고 기울이는 방식(스쿼시·스트레치)으로 표현한다. 뼈는 Root(제자리 이동)와 Body(눌림·기울기) 둘뿐.
기본 4종과 지역 변형 12종 모두 같은 동작을 담는다."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import souls, rig, to_group
from soul_variants import variant, REGIONS, BASE
import anim
import hit_react as hr
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
BONES = [("Root", None, (0, 0, 0), (0, 0, 0.2)), ("Body", "Root", (0, 0, 0), (0, 0, 0.6))]

def clips():
    B = lambda r=(0, 0, 0), s=(1, 1, 1), l=(0, 0, 0): {"Body": {"r": r, "s": s, "l": l}}
    C = {}
    fl_a = {"Root": {"l": (0, 0, 0)}, **B((3, 0, -4))}; fl_b = {"Root": {"l": (0, 0, 0.09)}, **B((-3, 0, 4), (0.98, 0.98, 1.03))}
    C["Float"] = ([(0, fl_a), (45, fl_b), (90, fl_a)], "BEZIER", True, {})
    # 고친 점(10-25): 앞에서 보면 뒤로 젖히는 것(rx)은 거의 안 보여 예고가 안 읽혔다(앞모습 변화율 측정). 좌우로 기우뚱(ry)하며 옆으로 넓게 눌려 앞모습에도 모양이 변한다.
    # 부풀어 오르며 떠오름(앞모습에서 키·폭이 함께 커져 한눈에 '벼르는' 모양) + 좌우 떨림
    R = lambda z: {"Root": {"l": (0, 0, z)}}
    w1 = {**B((-14, -9, 0), (1.14, 1.14, 1.1)), **R(0.07)}; w2 = {**B((-18, 11, 0), (1.3, 1.3, 1.22)), **R(0.16)}; w3 = {**B((-18, -11, 1.5), (1.32, 1.32, 1.24)), **R(0.17)}
    C["Windup"] = ([(0, fl_a), (8, w1), (14, w2), (21, w3), (27, w2), (33, w3)], "BEZIER", False, {"flash": 21, "end_pose_held": True})
    lunge = {"Root": {"l": (0, -0.7, 0)}, **B((30, 0, 0), (0.88, 0.88, 1.18))}
    C["Attack"] = ([(0, w2), (4, lunge), (6, lunge), (12, {"Root": {"l": (0, -0.3, 0)}, **B((8, 0, 0), (1.04, 1.04, 0.94))}), (18, {})], "LINEAR", False, {"hit": 5})
    kn = {**B((24, 0, 0), (1.14, 1.14, 0.55)), "Root": {"l": (0, 0, 0)}}; kn2 = {**B((26, 0, 0), (1.15, 1.15, 0.53))}
    C["Kneel"] = ([(0, {}), (10, B((-6, 0, 0), (1.06, 1.06, 0.82))), (20, kn), (36, kn2)], "BEZIER", False, {"end_pose_held": True})
    C.update(hr.soul_clips("basic"))   # 피격 3단계·다듬은 무릎·천도로 흩어짐·파혼으로 깨짐(hit_react.py)
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
