"""보스 '낚아챌 점' 소품 3종(코드가 지금은 색 구슬 대역으로 씀): B-09 아낙이 던지는 남편의 옷, B-12 물속에 잠긴 횃불, B-05 대돌의 군기.
왜: 사슬로 낚아채는 약점 창은 플레이어가 '무엇을 낚는지' 한눈에 알아야 한다. 구슬 대신 이야기가 있는 물건으로 보여 준다(옷=기다림, 횃불=불씨, 군기=불린 이름).
규약: 1유닛=1m, 원점=바닥 한가운데(옷은 공중에 던져진 것이라 원점에서 1.0m 위가 몸통 중심), 정면 -Y. 발광은 횃불 불꽃 한 면만. 낚아챌 지점은 노드 이름 `GrabPoint`(빈 오브젝트)로 표시.
실행: python3 tools/art3d/boss_grab_props.py → assets3d/boss/grab/*.glb, 미리보기 assets3d/previews/boss_grab_props_50deg.png"""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from boss_act2 import OUT
OUTG = os.path.join(OUT, "boss", "grab")
CLOTH = "#E8E2D0"; CLOTH_D = "#CFC7B0"; GOLD = "#D8B04A"; WOOD = "#5A4430"; WOOD_D = "#3E2E22"; FLAGRED = "#8E2F2A"; INK = "#1E1A18"; IRON = "iron"

def grab_clothes():
    """B-09 남편의 흰 겹저고리: 소매를 펼치고 공중에 던져진 모양. 가슴에 금빛 고름(낚을 자리)."""
    z = 1.0; p = [box("body", (0.5, 0.12, 0.62), (0, 0, z), CLOTH, rot=(0.25, 0, 0.12)), box("collar", (0.28, 0.14, 0.08), (0, -0.01, z + 0.33), CLOTH_D, rot=(0.25, 0, 0.12)),
                  box("hem", (0.56, 0.1, 0.1), (0, 0.03, z - 0.34), CLOTH_D, rot=(0.25, 0, 0.12))]
    for sx in (1, -1): p += [box(f"sleeve{sx}", (0.55, 0.1, 0.2), (sx * 0.5, 0.0, z + 0.12 - sx * 0.05), CLOTH, rot=(0.2, 0, sx * 0.35)), box(f"cuff{sx}", (0.12, 0.11, 0.21), (sx * 0.78, 0.02, z + 0.22 - sx * 0.1), CLOTH_D, rot=(0.2, 0, sx * 0.35))]
    p += [box("goreum1", (0.06, 0.03, 0.34), (0.03, -0.08, z + 0.1), GOLD, rot=(0.25, 0, -0.1)), box("goreum2", (0.05, 0.03, 0.28), (-0.06, -0.08, z + 0.04), GOLD, rot=(0.25, 0, 0.18)), sphere("knot", 0.05, (0, -0.09, z + 0.2), GOLD, 5, 4)]
    p += [box(f"fold{i}", (0.4, 0.015, 0.02), (0, -0.065, z - 0.2 + i * 0.16), CLOTH_D, rot=(0.25, 0, 0.12)) for i in range(3)]
    return p, (0, -0.1, z + 0.2)

def grab_torch():
    """B-12 물속에서 타는 횃불: 비스듬히 박힌 나무 자루, 젖은 천을 감은 머리, 불꽃(발광) 한 면, 둘레 물결 고리."""
    p = [cyl("pole", 0.045, 0.06, 1.5, (0, 0, 0.0), WOOD, 6, rot=(0.18, 0, 0.1)), cyl("wrap", 0.11, 0.09, 0.32, (0.05, -0.13, 1.38), WOOD_D, 7, rot=(0.18, 0, 0.1)),
         box("band1", (0.2, 0.2, 0.03), (0.05, -0.13, 1.3), IRON, rot=(0.18, 0, 0.1)), box("band2", (0.2, 0.2, 0.03), (0.05, -0.13, 1.46), IRON, rot=(0.18, 0, 0.1))]
    p += [prism("flame", 0.2, 0.2, 0.5, (0.05, -0.13, 1.54), mat("#FFB347", 2.2)), prism("flame_in", 0.1, 0.1, 0.36, (0.05, -0.13, 1.56), mat("#FFE9A8", 2.6))]
    p += [lathe(f"ripple{i}", [(0.0, 0.5 + i * 0.35), (0.0, 0.46 + i * 0.35)], 16, "#9FB6BC", caps=(False, False)) if False else cyl(f"ripple{i}", 0.28 + i * 0.14, 0.28 + i * 0.14, 0.02, (0, 0, 0.02 + i * 0.005), "#9FB6BC", 18) for i in range(2)]
    return p, (0.05, -0.13, 1.45)

def grab_flag():
    """B-05 대돌의 군기: 땅에 꽂힌 깃대 2.4m, 찢어진 붉은 깃발에 지워지다 만 이름 줄, 꼭대기 삼지창. 아래쪽 천 끝(낚을 자리)이 늘어져 있다."""
    r = random.Random(105); p = [cyl("pole", 0.045, 0.06, 2.4, (0, 0, 0.0), WOOD, 6), sphere("base_stone", 0.2, (0, 0, 0.06), "#6B655C", 5, 3, (1.3, 1.3, 0.5))]
    p += [box("prongC", (0.04, 0.04, 0.3), (0, 0, 2.4), IRON), box("prongL", (0.035, 0.035, 0.22), (-0.09, 0, 2.38), IRON, rot=(0, -0.2, 0)), box("prongR", (0.035, 0.035, 0.22), (0.09, 0, 2.38), IRON, rot=(0, 0.2, 0)), box("prongBar", (0.2, 0.04, 0.035), (0, 0, 2.3), IRON)]
    p += [box("cloth", (0.8, 0.02, 1.1), (0.46, 0, 1.78), FLAGRED, rot=(0, 0.04, 0)), box("hoist", (0.06, 0.04, 1.1), (0.04, 0, 1.78), WOOD_D)]
    for i in range(5): p.append(box(f"tatter{i}", (0.12, 0.018, r.uniform(0.28, 0.5)), (0.12 + i * 0.15, 0.0, 1.2 - r.uniform(0.0, 0.1)), FLAGRED, rot=(0.0, 0.05 * (i - 2), r.uniform(-.12, .12))))   # 아래로 찢겨 늘어진 천 끝
    for i in range(6): p.append(box(f"name{i}", (r.uniform(0.28, 0.5), 0.022, 0.03), (0.4, -0.012, 1.98 - i * 0.14), INK))      # 이름 줄(읽을 수 없게 번짐)
    return p, (0.8, -0.05, 1.12)

KIT = [("boss_grab_clothes_b09", grab_clothes), ("boss_grab_torch_b12", grab_torch), ("boss_grab_flag_b05", grab_flag)]
if __name__ == "__main__":
    os.makedirs(OUTG, exist_ok=True); rep = []
    for name, fn in KIT:
        reset(); parts, gp = fn(); o = join(name, parts); lo, hi = bounds(o)
        g = bpy.data.objects.new("GrabPoint", None); g.empty_display_type = "PLAIN_AXES"; g.empty_display_size = 0.12; bpy.context.collection.objects.link(g); g.location = gp; g.parent = o
        g["role"] = "chain_grab_point"
        if name == "boss_grab_torch_b12": light_empty(o, "Light_grab_torch", (0.05, -0.13, 1.7), (1.0, 0.7, 0.35), intensity=1.6, range_m=7.0, flicker=True)
        export(o, os.path.join(OUTG, name + ".glb")); rep.append({"name": name, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "grab_point": list(gp)}); print(rep[-1])
    json.dump(rep, open(os.path.join(OUTG, "_report_grab.json"), "w"), ensure_ascii=False, indent=1)
    reset()
    for i, (k, f) in enumerate(KIT): o = join(k, f()[0]); o.location = ((i - 1) * 3.0, 0, 0)
    setup_render(8, (0, 0, 1.2), elev=50, size=(1200, 600), ground_size=20); bpy.context.scene.cycles.samples = 32
    render(os.path.join(OUT, "previews", "boss_grab_props_50deg.png"))
