"""동이(컨셉 B 넓은 소매) 로우폴리 + 뼈대, 혼 4종 로우폴리. 실행: python3 characters.py
화면에는 '동이' 이름을 쓰지 않는다(결말 A 전까지 비공개). 파일명은 hero_chasa로 둔다.
키: 몸 1.65m(흑립 제외), 흑립 포함 약 1.95m. 정면 +Z, 위 +Y, 원점은 발바닥 한가운데.
뼈대 이름은 사람형 표준 이름(Hips/Spine/Chest/Neck/Head/UpperArm.L …). 왼쪽(.L)은 캐릭터의 왼쪽 = glTF +X."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def to_group(objs, bone):
    for o in objs:
        vg = o.vertex_groups.new(name=bone)
        vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
    return objs

def hero(chain=False):
    """chain=True면 오른손에 사슬을 감은 옛 모양. 기본은 사슬 없는 주먹(사슬은 chain_wrap()로 따로 내보냄)."""
    parts = []
    A = 0.5   # 팔이 벌어진 각도(라디안): A자 자세
    # 몸통 계열
    parts += to_group([cyl("skirt", 0.44, 0.25, 1.0, (0, 0, 0.1), "ink", 8)], "Hips")                      # 밑단이 퍼지는 긴 도포
    parts += to_group([cyl("sash", 0.25, 0.25, 0.08, (0, 0, 1.0), "red", 8),
                       box("sash_end", (0.09, 0.03, 0.4), (0.1, -0.25, 0.78), "red"),
                       box("sash_end2", (0.08, 0.03, 0.32), (0.17, -0.25, 0.8), "red", rot=(0, 0.15, 0))], "Hips")  # 붉은 띠와 늘어진 끝
    parts += to_group([cyl("torso", 0.23, 0.2, 0.48, (0, 0, 1.0), "cloth", 8),
                       box("collar", (0.15, 0.03, 0.34), (0, -0.17, 1.3), "hanji", rot=(0, 0.0, 0)),
                       box("collar_l", (0.07, 0.03, 0.3), (0.06, -0.175, 1.31), "hanji", rot=(0, 0.45, 0)),
                       box("collar_r", (0.07, 0.03, 0.3), (-0.06, -0.175, 1.31), "hanji", rot=(0, -0.45, 0))], "Chest")
    parts += to_group([cyl("neck", 0.07, 0.07, 0.1, (0, 0, 1.46), "face", 6)], "Neck")
    parts += to_group([sphere("head", 0.13, (0, 0, 1.58), "face", 7, 5),
                       cyl("hat_brim", 0.33, 0.33, 0.03, (0, 0, 1.68), "hat", 10),
                       cyl("hat_crown", 0.14, 0.11, 0.24, (0, 0, 1.7), "hat", 8),
                       box("hat_band", (0.3, 0.02, 0.025), (0, -0.115, 1.665), "red"),
                       box("strap_l", (0.02, 0.02, 0.2), (0.1, -0.1, 1.55), "red"), box("strap_r", (0.02, 0.02, 0.2), (-0.1, -0.1, 1.55), "red")], "Head")
    # 팔: 넓은 소매(어깨는 좁고 손목 쪽이 크게 퍼짐)
    for sx, side in ((1, "L"), (-1, "R")):
        sh = Vector((sx * 0.23, 0, 1.4))
        d = Vector((sx * math.sin(A), 0, -math.cos(A)))
        theta = math.pi - sx * A
        parts += to_group([cyl(f"sleeve_{side}", 0.07, 0.18, 0.58, tuple(sh), "cloth", 8, rot=(0, theta, 0))], f"UpperArm.{side}")
        hand = sh + d * 0.6
        hp = [sphere(f"hand_{side}", 0.06, tuple(hand), "face", 5, 4)]
        if side == "R" and chain:   # 오른손에 철삭을 감는다
            for i in range(6):
                a = i / 6 * math.tau
                hp.append(box(f"chain{i}", (0.05, 0.05, 0.025), (hand.x + math.cos(a) * 0.1, hand.y + math.sin(a) * 0.1, hand.z + 0.02), "chain", rot=(0, 0, a + 0.8)))
            for i in range(4):   # 늘어진 사슬 고리
                hp.append(box(f"link{i}", (0.045, 0.02, 0.07), (hand.x - 0.05, hand.y - 0.04, hand.z - 0.1 - i * 0.075), "chain", rot=(0, 0, 0.0 if i % 2 else 0.9)))
        else:             # 왼손 곁에 혼불
            hp.append(sphere("orb", 0.09, (hand.x + 0.2, hand.y - 0.08, hand.z + 0.18), mat("cheondo", 1.5), 6, 4))
        parts += to_group(hp, f"Hand.{side}")
    # 신발(밑단 아래로 살짝)
    for sx, side in ((1, "L"), (-1, "R")):
        parts += to_group([box(f"shoe_{side}", (0.15, 0.3, 0.09), (sx * 0.13, -0.08, 0.045), "hat")], f"Foot.{side}")
    return parts

BONES = [  # (이름, 부모, 머리(head), 꼬리(tail)) — 블렌더 좌표(Z 위, 정면 -Y)
    ("Root", None, (0, 0, 0), (0, 0, 0.12)), ("Hips", "Root", (0, 0, 0.95), (0, 0, 1.05)), ("Spine", "Hips", (0, 0, 1.05), (0, 0, 1.25)),
    ("Chest", "Spine", (0, 0, 1.25), (0, 0, 1.45)), ("Neck", "Chest", (0, 0, 1.45), (0, 0, 1.52)), ("Head", "Neck", (0, 0, 1.52), (0, 0, 1.95)),
    ("UpperArm.L", "Chest", (0.27, 0, 1.4), (0.55, 0, 1.0)), ("Hand.L", "UpperArm.L", (0.55, 0, 1.0), (0.6, 0, 0.9)),
    ("UpperArm.R", "Chest", (-0.27, 0, 1.4), (-0.55, 0, 1.0)), ("Hand.R", "UpperArm.R", (-0.55, 0, 1.0), (-0.6, 0, 0.9)),
    ("UpperLeg.L", "Hips", (0.13, 0, 0.95), (0.13, 0, 0.5)), ("LowerLeg.L", "UpperLeg.L", (0.13, 0, 0.5), (0.13, 0, 0.09)), ("Foot.L", "LowerLeg.L", (0.13, 0, 0.09), (0.13, -0.2, 0.02)),
    ("UpperLeg.R", "Hips", (-0.13, 0, 0.95), (-0.13, 0, 0.5)), ("LowerLeg.R", "UpperLeg.R", (-0.13, 0, 0.5), (-0.13, 0, 0.09)), ("Foot.R", "LowerLeg.R", (-0.13, 0, 0.09), (-0.13, -0.2, 0.02)),
]

def rig(mesh, bones=None):
    bones = bones or BONES
    arm = bpy.data.armatures.new("Armature"); ao = bpy.data.objects.new("Armature", arm)
    bpy.context.collection.objects.link(ao)
    bpy.context.view_layer.objects.active = ao; ao.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for n, par, h, t in bones:
        b = arm.edit_bones.new(n); b.head = h; b.tail = t
        if par: b.parent = eb[par]
        eb[n] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.parent = ao
    m = mesh.modifiers.new("Armature", "ARMATURE"); m.object = ao
    return ao

def chain_wrap():
    """영웅 오른손에 감겨 있던 사슬(감은 고리 6 + 늘어진 고리 4)을 손 위치 기준(0,0,0)으로 따로 만든 것. 소켓: Hand.R 머리 위치."""
    hand = Vector((0, 0, 0)); p = []
    for i in range(6):
        a = i / 6 * math.tau
        p.append(box(f"chain{i}", (0.05, 0.05, 0.025), (math.cos(a) * 0.1, math.sin(a) * 0.1, 0.02), "chain", rot=(0, 0, a + 0.8)))
    for i in range(4):
        p.append(box(f"link{i}", (0.045, 0.02, 0.07), (-0.05, -0.04, -0.1 - i * 0.075), "chain", rot=(0, 0, 0.0 if i % 2 else 0.9)))
    return p

def souls():
    S = {}
    def eyes(z, y, c="face", dx=0.07, s=0.035, ox=0):
        return [box("eyeL", (s, 0.02, s * 1.5), (ox + dx, y, z), c), box("eyeR", (s, 0.02, s * 1.5), (ox - dx, y, z), c)]
    def fresh(o=0):   # 갓 죽은 혼: 곧은 물방울
        return [sphere("body", 0.24, (o, 0, 0.58), mat("soul_fresh", 0.7), 8, 6, (1, 1, 1.25)), cyl("tip", 0.13, 0.0, 0.32, (o, 0, 0.9), mat("soul_fresh", 0.7), 8),
                cyl("tail", 0.03, 0.13, 0.4, (o, 0.03, 0.0), mat("soul_fresh", 0.7), 6, rot=(0.25, 0, 0))] + eyes(0.64, -0.23, ox=o)
    def day(o=0):     # 해 넘긴 혼: 키 큰 몸에 팔이 늘어짐
        m = mat("soul_day", 0.7)
        p = [cyl("body", 0.27, 0.2, 0.85, (o, 0, 0.18), m, 8), sphere("head", 0.2, (o, 0, 1.15), m, 8, 6), cyl("tail", 0.0, 0.2, 0.3, (o, 0, 0.0), m, 8)]
        for sx in (-1, 1):
            p.append(box(f"arm{sx}", (0.1, 0.1, 0.62), (o + sx * 0.33, 0, 0.62), m, rot=(0, sx * 0.2, 0)))
        return p + eyes(1.17, -0.19, dx=0.075, ox=o)
    def old(o=0):     # 오래된 혼: 구부정, 가시, 긴 꼬리
        m = mat("soul_old", 0.2)
        p = [sphere("body", 0.36, (o, 0.05, 0.6), m, 8, 6, (1.1, 1.0, 0.9)), cyl("tail", 0.0, 0.3, 0.45, (o, 0.15, 0.0), m, 7, rot=(-0.3, 0, 0))]
        for i, (a, z) in enumerate([(0.2, 0.95), (1.0, 1.0), (2.1, 0.95), (3.0, 0.9), (4.0, 0.95), (5.2, 1.0)]):
            p.append(cyl(f"spike{i}", 0.08, 0.0, 0.34, (o + math.cos(a) * 0.22, 0.05 + math.sin(a) * 0.22, z - 0.05), m, 5))
        return p + eyes(0.7, -0.33, dx=0.1, s=0.045, ox=o)
    def lump(o=0):    # 덩어리: 겹친 구름
        m = mat("soul_lump", 0.6); p = []
        for i, (x, y, z, r) in enumerate([(-0.32, 0, 0.57, 0.42), (0.3, 0.05, 0.67, 0.48), (0, -0.05, 0.42, 0.42), (-0.02, 0.1, 1.07, 0.34), (0.1, -0.1, 0.77, 0.3)]):
            p.append(sphere(f"blob{i}", r, (o + x, y, z), m, 7, 5))
        for i, a in enumerate((0.5, 2.4, 4.4)):
            p.append(cyl(f"spike{i}", 0.09, 0.0, 0.32, (o + math.cos(a) * 0.5, math.sin(a) * 0.4, 0.2), m, 5, rot=(0.0, 0.6 * math.cos(a), 0)))
        return p
    return {"fresh": fresh, "day": day, "old": old, "lump": lump}

if __name__ == "__main__":
    rep = []
    reset()
    parts = hero(); o = join("hero_chasa", parts); rig(o)
    lo, hi = bounds(o)
    rep.append({"name": "hero_chasa", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "bones": len(BONES), "materials": len(o.data.materials)})
    export(o, os.path.join(OUT, "characters", "hero_chasa.glb"), apply=False)
    setup_render(2.8, (0, 0, 1.0), size=(540, 720), ground_size=12)
    render(os.path.join(OUT, "previews", "hero_chasa.png"))
    for key, fn in souls().items():
        reset(); o = join(f"soul_{key}", fn()); lo, hi = bounds(o)
        rep.append({"name": f"soul_{key}", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "materials": len(o.data.materials)})
        export(o, os.path.join(OUT, "souls", f"soul_{key}.glb"))
    reset()
    for i, (key, fn) in enumerate(souls().items()):
        join(f"s{i}", fn(o=(i - 1.5) * 1.5))
    setup_render(7.5, (0, 0, 0.6), size=(900, 420), ground_size=14)
    render(os.path.join(OUT, "previews", "souls_4.png"))
    for r in rep: print(r)
    json.dump(rep, open(os.path.join(OUT, "characters", "_report_characters.json"), "w"), ensure_ascii=False, indent=1)
