"""1호 보스 나루 영감 로우폴리 시험. 밤 나루에서 배를 타고 삿대를 휘두르는 늙은 뱃사공.
산출: boss_naru.glb(서 있는 모습, 삿대는 물에 꽂음), boss_naru_attack.glb(삿대를 크게 젖힌 예비동작).
규약: GLB, 1유닛=1m, 원점=배 바닥 한가운데(물 위), 정면 +Z(뱃머리 방향). 뼈대 8개."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import to_group, rig
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
BONES = [  # 뼈 위치를 실제 모델에 맞춤(영감은 배 뒤쪽 y=0.9에 서 있다). 오른팔 아래에 삿대 뼈가 붙어 팔과 함께 돈다.
    ("Root", None, (0, 0, 0), (0, 0, 0.2)), ("Boat", "Root", (0, 0, 0.1), (0, -1.0, 0.2)), ("Hips", "Boat", (0, 0.9, 0.5), (0, 0.9, 1.0)), ("Chest", "Hips", (0, 0.9, 1.0), (0, 0.9, 1.4)),
    ("Head", "Chest", (0, 0.9, 1.4), (0, 0.9, 1.9)), ("UpperArm.L", "Chest", (0.22, 0.9, 1.4), (0.42, 0.7, 0.95)), ("UpperArm.R", "Chest", (-0.22, 0.9, 1.4), (-0.4, 0.4, 1.05)),
    ("Pole", "UpperArm.R", (-0.22, 0.9, 1.4), (-0.5, -0.1, 0.0))]

def naru(attack=False):
    # 좌표: 뱃머리가 -Y(블렌더), 배 길이는 Y축. 영감은 배 가운데보다 뒤쪽(+Y)에 서서 삿대를 짚는다.
    L = 4.4
    boat = [box("floor", (1.0, 3.8, 0.1), (0, 0, 0.14), "hull"),
            box("sideL", (0.1, 3.9, 0.55), (0.56, 0, 0.36), "hull", rot=(0, -0.16, 0)), box("sideR", (0.1, 3.9, 0.55), (-0.56, 0, 0.36), "hull", rot=(0, 0.16, 0)),
            cyl("bow", 0.55, 0.0, 0.9, (0, -1.9, 0.56), "hull", 4, rot=(math.pi / 2, 0, math.pi / 4)), cyl("stern", 0.55, 0.12, 0.5, (0, 1.95, 0.56), "hull", 4, rot=(-math.pi / 2, 0, math.pi / 4)),
            box("bench", (1.0, 0.18, 0.1), (0, -0.4, 0.55), "wood_dark")]
    # 엽전 다섯 닢(제사상 소품)
    boat += [cyl(f"coin{i}", 0.07, 0.07, 0.02, (-0.25 + i * 0.12, -1.0, 0.2), "gold", 6) for i in range(5)]
    water = [cyl("mist", 3.1, 3.1, 0.04, (0, 0, 0), mat("chain", 0.5), 12), cyl("water", 2.2, 2.2, 0.05, (0, 0, 0), "water", 12)]
    ox, oy = 0, 0.9
    man = [cyl("robe", 0.44, 0.22, 1.0, (ox, oy, 0.18), "robe", 8), cyl("torso", 0.22, 0.2, 0.4, (ox, oy, 1.1), "robe", 8), box("belt", (0.48, 0.3, 0.07), (ox, oy, 1.1), "ink")]
    head = [sphere("head", 0.13, (ox, oy, 1.6), "old_skin", 6, 4), cone := cyl("sagat", 0.66, 0.05, 0.3, (ox, oy, 1.66), "sagat", 10),
            box("beard", (0.14, 0.05, 0.3), (ox, oy - 0.12, 1.42), "beard"), box("eyeL", (0.025, 0.02, 0.025), (ox + 0.05, oy - 0.12, 1.62), "hanji"), box("eyeR", (0.025, 0.02, 0.025), (ox - 0.05, oy - 0.12, 1.62), "hanji")]
    # 팔과 삿대
    shL, shR = (ox + 0.22, oy, 1.4), (ox - 0.22, oy, 1.4)
    if attack:   # 예비동작: 삿대를 크게 뒤로 젖힘
        handR = (ox - 0.45, oy - 0.45, 1.35); pole_a = (ox - 0.55, oy + 0.9, 2.5); pole_b = (ox - 0.2, oy - 1.9, 0.7)
    else:        # 서 있음: 삿대를 물에 꽂고 선다
        handR = (ox - 0.4, oy - 0.5, 1.05); pole_a = (ox - 0.35, oy - 0.35, 2.7); pole_b = (ox - 0.5, oy - 1.0, 0.0)
    handL = (ox + 0.42, oy - 0.2, 0.95)
    armL = [limb("armL", shL, handL, 0.07, 0.15, "robe", 6), sphere("handL", 0.06, handL, "old_skin", 5, 4)]
    armR = [limb("armR", shR, handR, 0.07, 0.15, "robe", 6), sphere("handR", 0.06, handR, "old_skin", 5, 4)]
    # 삿대: 손을 지나는 긴 장대(칼금 하나)
    d = (Vector(pole_b) - Vector(pole_a)).normalized()
    pole = [limb("pole", pole_a, pole_b, 0.04, 0.05, "wood", 5), box("notch", (0.1, 0.1, 0.05), tuple(Vector(pole_b) - d * 0.2), "red", rot=tuple(Vector((0, 0, 1)).rotation_difference(d).to_euler()))]
    parts = to_group(boat, "Boat") + to_group(water, "Root") + to_group(man[:1], "Hips") + to_group(man[1:], "Chest") + to_group(head, "Head") + to_group(armL, "UpperArm.L") + to_group(armR, "UpperArm.R") + to_group(pole, "Pole")
    return parts

if __name__ == "__main__":
    rep = []
    for name, atk in (("boss_naru", False), ("boss_naru_attack", True)):
        reset(); o = join(name, naru(atk)); rig(o, BONES)
        lo, hi = bounds(o)
        rep.append({"name": name, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "bones": len(BONES)})
        export(o, os.path.join(OUT, "boss", f"{name}.glb"), apply=False)
    # 미리보기: 서 있음과 예비동작을 나란히
    reset()
    a = join("a", naru(False)); a.location = (-4.0, 0, 0)
    b = join("b", naru(True)); b.location = (4.0, 0, 0)
    setup_render(11, (0, 0, 1.1), size=(1000, 600), ground_size=20)
    render(os.path.join(OUT, "previews", "boss_naru_50deg.png"))
    json.dump(rep, open(os.path.join(OUT, "boss", "_report_boss.json"), "w"), ensure_ascii=False, indent=1)
    for r in rep: print(r)
