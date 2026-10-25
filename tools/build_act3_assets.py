#!/usr/bin/env python3
"""
build_act3_assets.py — 아트의 3막 산출물(assets3d/)을 유니티 Resources 에 넣는다. 몇 번을 돌려도 같은 결과(다시 돌려도 안전).
 1) assets3d/terrain_act3_east/*  → Resources/Terrain3E/*.bytes  (⑤ 갯마을 512×1024m, 원점 (768,0))
    assets3d/terrain_act3_west/*  → Resources/Terrain3W/*.bytes  (⑥ 도성 아랫마을 640×640m, 원점 (-640,0))
 2) assets3d/act3/*.glb → Resources/Models/Field/*.glb (3막 소품·다리·물판 모델)
 3) assets3d/layouts/act3_east_layout.json · act3_west_layout.json → Resources/Data/field.json 에 합침
    (x>=768 · x<0 · z<0(해안 띠) 인 옛 항목은 먼저 지우고 다시 넣는다 = 멱등)
사용: python3 tools/build_act3_assets.py [assets3d 폴더, 기본 assets3d]
"""
import json, os, shutil, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
art = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "assets3d")
res = os.path.join(root, "unity", "Assets", "Resources")
for src_dir, dst_dir in (("terrain_act3_east", "Terrain3E"), ("terrain_act3_west", "Terrain3W"), ("terrain_act3_coast", "Terrain3C")):
    tdir = os.path.join(res, dst_dir); os.makedirs(tdir, exist_ok=True)
    for n, dst in (("terrain.json", "terrain.json"), ("heightmap.png", "heightmap.bytes"), ("splat_a.png", "splat_a.bytes"), ("splat_b.png", "splat_b.bytes")):
        shutil.copyfile(os.path.join(art, src_dir, n), os.path.join(tdir, dst))
mdir = os.path.join(res, "Models", "Field")
props = []
for n in ("east", "west", "coast"):
    props += json.load(open(os.path.join(art, "layouts", "act3_%s_layout.json" % n), encoding="utf-8"))["props"]
copied = 0
for n in sorted({p["prop"] for p in props}):
    a = os.path.join(art, "act3", n + ".glb"); b = os.path.join(mdir, n + ".glb")
    if os.path.exists(a) and (not os.path.exists(b) or os.path.getsize(a) != os.path.getsize(b)): shutil.copyfile(a, b); copied += 1
    elif not os.path.exists(a) and not os.path.exists(b): print("경고: 모델 없음", n)
fp = os.path.join(res, "Data", "field.json")
f = json.load(open(fp, encoding="utf-8"))
f["items"] = [i for i in f["items"] if 0.0 <= i["x"] < 768.0 and i["z"] >= 0.0]   # 이미 합쳐 둔 3막 항목(동 x>=768, 서 x<0)은 뺀다(멱등). 2막(z>=640, x<768)은 그대로
items = [{"n": p["prop"], "x": round(p["x"], 2), "z": round(p["y"], 2), "y": round(p.get("z", 0.0), 2), "r": int(p.get("rot", 0)) % 360, "t": 0} for p in props]
# 해안 띠 벼랑 돌담 일부는 z>=0·0<=x<768 에 놓여 위 필터로는 안 지워진다 → 같은 (이름, x, z) 인 옛 항목을 따로 지운다(멱등)
newkeys = {(i["n"], i["x"], i["z"]) for i in items}
f["items"] = [i for i in f["items"] if (i["n"], round(i["x"], 2), round(i["z"], 2)) not in newkeys]
f["items"] += items
json.dump(f, open(fp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("땅 12파일, 모델 %d개 복사, 배치 %d개 합침 → field.json 항목 %d" % (copied, len(items), len(f["items"])))
