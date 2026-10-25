"""먼 거리용 단순 모델(LOD) 자동 생성. 실행: python3 lod.py
LOD0 = 원본, LOD1 = 면 수를 줄인 모델(Decimate), LOD2 = 크기와 색만 맞춘 덩어리(12면 이하).
왜: 필드 배치물이 6천 개라 멀리 있는 것까지 전부 자세히 그리면 무겁다. 뼈대(스킨) 있는 캐릭터는 대상이 아니다.
결과: assets3d/lod/<이름>_lod1.glb, <이름>_lod2.glb + lod/_lod_manifest.json(거리 규칙 포함)."""
import sys, os, json, glob, math
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import reset, export, tris, bounds, join, box, cyl

A3 = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); OUT = os.path.join(A3, "lod")
SRC = ["nature/nature_*.glb", "props/prop_*.glb", "terrain/terrain_bush*.glb", "terrain/terrain_rock*.glb", "blackrapids/br_willow*.glb", "blackrapids/br_reed_field.glb", "night/night_*.glb"]

def avg_color(o):
    cols = []
    for m in o.data.materials:
        try: cols.append(tuple(m.node_tree.nodes["Principled BSDF"].inputs[0].default_value)[:3])
        except Exception: pass
    return tuple(sum(c[i] for c in cols) / len(cols) for i in range(3)) if cols else (0.5, 0.5, 0.5)

def run():
    os.makedirs(OUT, exist_ok=True); man = {}
    files = sorted(f for pat in SRC for f in glob.glob(os.path.join(A3, pat)))
    for fp in files:
        name = os.path.splitext(os.path.basename(fp))[0]
        reset(); bpy.ops.import_scene.gltf(filepath=fp)
        meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        if not meshes: continue
        for o in bpy.data.objects: o.select_set(False)
        for o in meshes: o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        if len(meshes) > 1: bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active; o.parent = None
        n0 = tris(o); lo, hi = bounds(o); size = [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)]
        col = avg_color(o); ent = {"tris0": n0, "size_m": size}
        if n0 >= 60:   # 면이 적은 모델은 줄여도 의미가 없다
            md = o.modifiers.new("dec", "DECIMATE"); md.ratio = 0.4; bpy.ops.object.modifier_apply(modifier="dec")
            o.name = name + "_lod1"; export(o, os.path.join(OUT, f"{name}_lod1.glb")); ent["tris1"] = tris(o)
        # LOD2: 같은 크기의 단순 덩어리(바닥 z=0 유지). 키 큰 것은 원뿔, 나머지는 상자
        reset(); h = size[2]; w = max(size[0], size[1])
        if "pine" in name or "zelkova" in name or "willow" in name: parts = [cyl("lod2", w * 0.5, 0.0, h, (0, 0, 0), "pine", 6)]
        else: parts = [box("lod2", (max(size[0], 0.1), max(size[1], 0.1), max(h, 0.1)), (0, 0, max(h, 0.1) / 2), "ground")]
        o2 = join(name + "_lod2", parts)
        for m in o2.data.materials:
            b = m.node_tree.nodes["Principled BSDF"]; b.inputs[0].default_value = (*col, 1.0)
        export(o2, os.path.join(OUT, f"{name}_lod2.glb")); ent["tris2"] = tris(o2); man[name] = ent
    rules = {"lod0_to_m": 40, "lod1_to_m": 90, "lod2_to_m": 160, "cull_beyond_m": 160,
             "small_props_cull_m": 70, "small_props_note": "키 1.5m 이하 소품(항아리·장작·자루·돌탑 등)은 70m 밖에서 아예 숨긴다",
             "instancing": "같은 prop 이름끼리 한 번에 그린다(GPU Instancing). 위치 목록은 layouts/field_5x5_instances.json(청크 128m별)",
             "lod_group_tip": "나무는 LOD2를 구름 모양 한 덩어리로 써도 됨. 모델 이름 + _lod1/_lod2 로 짝지음"}
    json.dump({"rules": rules, "models": man}, open(os.path.join(OUT, "_lod_manifest.json"), "w"), ensure_ascii=False, indent=1)
    print(len(man), "개 모델 LOD 생성")

if __name__ == "__main__": run()
