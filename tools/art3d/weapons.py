"""무기 5종 로우폴리: 철삭·육모방망이·요령방울·삼지창·명부 붓.
규약: GLB, 1유닛=1m, 원점=쥐는 곳(손바닥 한가운데), 무기의 '긴 방향'이 블렌더 +Z(glTF에서는 +Y, 위쪽).
소켓: 영웅 Hand.R(또는 Hand.L) 뼈의 머리 위치에 원점을 놓고, 무기 +Y가 캐릭터 앞(+Z)을 향하도록 X축으로 +90° 돌린다(아래 manifest의 socket).
영웅 Hand.R 머리 위치(기본 자세, 캐릭터 기준 m): x=-0.52, 앞뒤 0, 높이 0.87. 주먹은 둥근 구라서 어느 방향이든 자연스럽다."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def L(name, a, b, r1, r2, m, segs=6): return limb(name, a, b, r1, r2, m, segs)

def chain_v1():
    """철삭: 가죽 손잡이 + 감긴 사슬 + 늘어진 사슬 + 끝추. 사슬 길이는 짧게 두고, 늘어나는 연출은 코드 이펙트가 맡는다."""
    p = [cyl("grip", 0.035, 0.035, 0.28, (0, 0, -0.14), "wood_dark", 6), cyl("capA", 0.05, 0.05, 0.03, (0, 0, 0.14), "iron", 6), cyl("capB", 0.05, 0.05, 0.03, (0, 0, -0.17), "iron", 6)]
    for i in range(5): p.append(cyl(f"coil{i}", 0.07, 0.07, 0.025, (0, 0, -0.1 + i * 0.045), mat("chain", 0.5), 8))
    for i in range(9):   # 곧게 뻗은 사슬 고리(번갈아 90° 돌려 끼움)
        p.append(box(f"link{i}", (0.05, 0.02, 0.085), (0, 0, 0.2 + i * 0.075), mat("chain", 0.5), rot=(0, 0, 0 if i % 2 else math.pi / 2)))
    p += [sphere("weight", 0.07, (0, 0, 0.93), "iron", 6, 4), cyl("spike", 0.045, 0.0, 0.16, (0, 0, 0.97), "iron", 5)]
    return p

from look_v2 import chain2 as chain   # 2차 다듬기(look_v2.py). 옛 모양은 chain_v1

def bangmang():
    """육모방망이: 여섯 모 나무 몽둥이, 끝이 굵고 쇠테 두 줄, 손잡이 끈."""
    return [cyl("grip", 0.03, 0.03, 0.2, (0, 0, -0.1), "wood_dark", 6), cyl("body", 0.04, 0.075, 0.5, (0, 0, 0.1), "wood", 6), cyl("head", 0.075, 0.07, 0.1, (0, 0, 0.6), "wood", 6),
            cyl("band1", 0.08, 0.08, 0.025, (0, 0, 0.53), "iron", 6), cyl("band2", 0.08, 0.08, 0.025, (0, 0, 0.64), "iron", 6), cyl("cap", 0.04, 0.0, 0.04, (0, 0, 0.7), "wood_dark", 6),
            box("strap", (0.025, 0.02, 0.2), (0.035, 0, -0.05), "red", rot=(0, 0.1, 0))]

def yoryeong():
    """요령방울: 손잡이 위 십자 가지에 놋쇠 방울 셋과 붉은 끈."""
    p = [cyl("grip", 0.025, 0.03, 0.26, (0, 0, -0.13), "wood", 6), cyl("hub", 0.045, 0.045, 0.04, (0, 0, 0.13), "gold", 6)]
    for i, a in enumerate((0, 2.1, 4.2)):
        x, y = math.cos(a) * 0.14, math.sin(a) * 0.14
        p += [L(f"arm{i}", (0, 0, 0.15), (x, y, 0.26), 0.012, 0.012, "gold", 4), sphere(f"bell{i}", 0.07, (x, y, 0.3), "gold", 7, 5, (1, 1, 0.9)), cyl(f"lip{i}", 0.075, 0.09, 0.03, (x, y, 0.22), "gold", 7),
              sphere(f"clap{i}", 0.02, (x, y, 0.2), "iron", 4, 3), L(f"rope{i}", (0, 0, -0.1), (x * 0.4, y * 0.4, -0.32), 0.008, 0.008, "red", 4)]
    p.append(sphere("top", 0.05, (0, 0, 0.2), "gold", 6, 4))
    return p

def samjichang():
    """삼지창: 긴 자루와 세 갈래 쇠날, 붉은 술. 키 1.7m."""
    p = [cyl("shaft", 0.025, 0.025, 1.6, (0, 0, -0.5), "wood", 6), cyl("butt", 0.035, 0.015, 0.06, (0, 0, -0.56), "iron", 6), cyl("socket", 0.04, 0.04, 0.12, (0, 0, 1.05), "iron", 6)]
    p += [box("cross", (0.3, 0.04, 0.04), (0, 0, 1.17), "iron")]
    for i, x in enumerate((-0.14, 0, 0.14)):
        h = 0.5 if i == 1 else 0.38
        p.append(cyl(f"prong{i}", 0.028, 0.0, h, (x, 0, 1.17), "iron", 4))
    p += [cyl("tassel", 0.03, 0.06, 0.2, (0, 0, 0.82), "red", 6)]
    return p

def myeongbu():
    """명부 붓: 굵은 대와 먹 머금은 큰 붓털, 끝은 붉은 먹. 뒤에 매단 두루마리 쪽지."""
    p = [cyl("shaft", 0.02, 0.03, 0.9, (0, 0, -0.3), "wood", 6), cyl("ferrule", 0.045, 0.05, 0.1, (0, 0, 0.6), "gold", 6),
         cyl("bristle", 0.06, 0.0, 0.34, (0, 0, 0.7), "ink", 7), cyl("tip", 0.012, 0.0, 0.1, (0, 0, 0.98), "red", 5), sphere("knob", 0.035, (0, 0, -0.32), "gold", 6, 4)]
    p += [box("tag", (0.1, 0.01, 0.16), (0.05, 0, 0.3), "hanji", rot=(0, 0.2, 0)), L("tagstr", (0, 0, 0.42), (0.05, 0, 0.36), 0.006, 0.006, "red", 3), box("tagline", (0.06, 0.012, 0.02), (0.05, 0, 0.32), "ink", rot=(0, 0.2, 0))]
    return p

W = [("weapon_chain", "철삭", chain, "Hand.R", "기준 무기. 사슬 길이는 1.2m까지만, 늘어나는 연출은 코드 이펙트"), ("weapon_bangmang", "육모방망이", bangmang, "Hand.R", "짧은 한 손 둔기"),
     ("weapon_yoryeong", "요령방울", yoryeong, "Hand.R", "도술형. 방울이 흔들리는 연출은 코드에서 회전"), ("weapon_samjichang", "삼지창", samjichang, "Hand.R", "긴 무기. 쥐는 곳은 자루 가운데에서 약간 아래"),
     ("weapon_myeongbu", "명부 붓", myeongbu, "Hand.R", "파혼/천도 문서 무기. 쪽지는 붓대에 달림")]

if __name__ == "__main__":
    rep = []
    for key, ko, fn, bone, note in W:
        reset(); o = join(key, fn()); lo, hi = bounds(o)
        rep.append({"name": key, "label": ko, "tris": tris(o), "length_m": round(hi.z - lo.z, 2), "z_range_m": [round(lo.z, 2), round(hi.z, 2)], "width_m": round(max(hi.x - lo.x, hi.y - lo.y), 2),
                    "socket": {"bone": bone, "position_in_bone_m": [0, 0, 0], "blade_axis_in_file": "+Y(glTF 위쪽)", "aim_blade_to": "캐릭터 앞(+Z glTF)", "rotate_deg_x": 90, "hero_hand_R_rest_pos_m": [-0.52, 0.87, 0.0]}, "note": note})
        export(o, os.path.join(OUT, "weapons", f"{key}.glb"))
    reset()
    for i, (key, ko, fn, bone, note) in enumerate(W):
        o = join(key, fn()); o.rotation_euler = (math.radians(90), 0, 0); o.location = ((i - 2) * 1.2, 0, 0.9)   # 눕혀서 한 줄로
    setup_render(7.0, (0, 0, 0.8), size=(1200, 420), ground_size=14)
    render(os.path.join(OUT, "previews", "weapons_5_50deg.png"))
    json.dump({"note": "원점=쥐는 곳. socket 참고", "weapons": rep}, open(os.path.join(OUT, "weapons", "_weapons_manifest.json"), "w"), ensure_ascii=False, indent=1)
    for r in rep: print(r["name"], r["tris"], r["length_m"])
