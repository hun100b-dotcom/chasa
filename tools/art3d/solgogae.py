"""솔고개 마을 3D 배치(첫 구역). 소품 GLB를 불러와 배치하고, 배치표(JSON)와 50° 미리보기를 낸다.
좌표: 위에서 본 평면, x=동쪽(m), y=북쪽(m). 원점=마을 길 한가운데. rot=위에서 볼 때 반시계 방향 각도(도), 0이면 정면이 남쪽(화면 아래).
코드팀: 유니티는 왼손 좌표계이므로 glTF를 불러오면 x가 뒤집혀 보일 수 있다. 배치표의 (x, y)는 '북쪽을 위로 둔 지도' 기준이고,
유니티에서는 (x, 0, y), 회전은 -rot로 쓰면 지도와 같게 놓인다."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from kit_buildings import place_building
ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
P = lambda k: os.path.join(ROOT, "props", f"prop_{k}.glb")

L = []   # (소품, x, y, rot, 설명)
def put(k, x, y, rot=0, note=""): L.append((k, x, y, rot, note))
# 입구(남쪽)
put("jangseung", -2.5, -23, 0, "입구 장승(남)"); put("jangseung", 2.5, -23, 0, "입구 장승(여)")
put("geumjul", 0, -23, 0, "입구 금줄(두 장승 사이를 가로지름)")
put("sotdae", 5.0, -22.5, 0, "마을 어귀 솟대")
put("seonangdang", -10, -21, 0, "서낭당과 당산나무(마을 밖 어귀)")
put("sangyeo", -15, -26, 90, "빈 상여(어귀 곁, 복선)")
# 길 서쪽 집(동쪽을 봄 rot=90)
B = []   # 키트로 세우는 집: (종류, x, y, rot, 설명)
B += [("choga4", -8.5, -13, 90, "서쪽 초가"), ("choga8", -8.5, -3, 90, "서쪽 긴 초가(방 둘)"), ("choga4", -8.5, 7, 90, "서쪽 초가")]
put("jangdok", -13.5, -4, 90, "서쪽 집 뒤 장독대")
# 길 동쪽 집(서쪽을 봄 rot=-90)
B += [("choga4", 8.5, -10, -90, "동쪽 초가"), ("choga4", 8.5, 0, -90, "동쪽 초가"), ("choga8", 8.5, 9, -90, "동쪽 긴 초가(방 둘)")]
put("jangdok", 13.5, 1, -90, "동쪽 집 뒤 장독대")
# 마을 한가운데 우물과 북쪽 큰 집
put("umul", 4.2, -5.5, 0, "마을 우물(모이는 자리)")
B += [("giwa8", 0, 19, 0, "북쪽 끝 기와집(마을에서 가장 큰 집)")]
# 돌담: 서쪽·동쪽 울타리(3m 토막을 길 방향으로 잇는다)
for i in range(11):
    y = -16 + i * 3.0
    put("dolddam", -15.5, y, 90, "서쪽 돌담"); put("dolddam", 15.5, y, 90, "동쪽 돌담")
for i in range(4):   # 북쪽 담 일부(큰 집 좌우)
    put("dolddam", -13.5 + i * 3.0, 24, 0, "북쪽 돌담(서)"); put("dolddam", 4.5 + i * 3.0, 24, 0, "북쪽 돌담(동)")

def run():
    reset()
    bpy.ops.import_scene.gltf(filepath=P("choga"))   # 먼저 워밍업 후 제거
    for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o)
    cache = {}
    for k, x, y, rot, note in L:
        bpy.ops.import_scene.gltf(filepath=P(k))
        objs = [o for o in bpy.context.selected_objects if o.type == "MESH"]
        o = objs[0]
        for e in bpy.context.selected_objects:
            if e is not o and e.type != "MESH": bpy.data.objects.remove(e)
        o.parent = None; o.rotation_mode = 'XYZ'
        o.location = (x, y, 0); o.rotation_euler = (0, 0, math.radians(rot))
        for s in bpy.context.selected_objects: s.select_set(False)
    kit = {}
    def kitobj(f):
        if f not in kit:
            bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "..", f))
            ms = [o for o in bpy.context.selected_objects if o.type == "MESH"]; m = ms[0]
            for e in bpy.context.selected_objects:
                if e is not m and e.type != "MESH": bpy.data.objects.remove(e)
            m.parent = None; m.rotation_mode = 'XYZ'; m.location = (1000, 1000, 0)
            kit[f] = m
        return kit[f]
    placed = []
    for i, (kind, x, y, rot, note) in enumerate(B):
        for p in place_building(kind, x, y, rot):
            o = kitobj(p["file"]).copy(); bpy.context.collection.objects.link(o)
            o.location = (p["x"], p["y"], p["z"]); o.rotation_euler = (0, 0, math.radians(p["rot"]))
        placed.append({"id": f"house_{i:02d}", "kind": kind, "x": x, "y": y, "rot": rot, "note": note, "pieces": place_building(kind, x, y, rot)})
    for m in kit.values(): m.location = (1000, 1000, -50)
    road = box("road", (3.4, 52, 0.04), (0, -2, 0.02), "road")
    plaza = box("plaza", (7, 5, 0.04), (3.4, -5.5, 0.045), "road")
    setup_render(66, (0, -2, 0), elev=50, size=(1280, 1000), ground_size=90)
    render(os.path.join(ROOT, "previews", "solgogae_village_50deg.png"))
    out = {"map": "솔고개 마을(첫 구역) v2 — 집은 한옥 조각 키트로 조립", "how_to": "buildings[].pieces는 이미 세계 좌표(x,y,z,rot). 그대로 한옥 조각 GLB를 놓으면 집이 선다.", "units": "m", "axes": "x=동, y=북, rot=반시계 도(0=정면이 남쪽)", "origin": "마을 길 한가운데",
           "buildings": placed,
           "props": [{"prop": f"prop_{k}", "file": f"assets3d/props/prop_{k}.glb", "x": x, "y": y, "rot": rot, "note": n} for k, x, y, rot, n in L],
           "counts": {k: sum(1 for a in L if a[0] == k) for k in sorted({a[0] for a in L})}}
    json.dump(out, open(os.path.join(ROOT, "layouts", "solgogae_village.json"), "w"), ensure_ascii=False, indent=1)
    print(out["counts"], len(L), "건물", len(B), "조각", sum(len(b["pieces"]) for b in placed))
os.makedirs(os.path.join(ROOT, "layouts"), exist_ok=True)
if __name__ == "__main__": run()
