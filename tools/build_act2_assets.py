#!/usr/bin/env python3
"""
build_act2_assets.py — 아트의 2막 산출물(assets3d/)을 유니티 Resources 에 넣는다. 몇 번을 돌려도 같은 결과(다시 돌려도 안전).
 1) assets3d/terrain_act2/*  → Resources/Terrain2/*.bytes   (직사각 768×640m 땅: terrain.json·heightmap·splat_a·splat_b. 층 그림·잔무늬는 1막 것을 쓴다)
 2) assets3d/act2/*.glb       → Resources/Models/Field/*.glb (2막 소품 모델)
 3) assets3d/layouts/act2_layout.json → Resources/Data/field.json 에 합침(z>=640 인 옛 항목은 먼저 지우고 다시 넣는다 = 멱등)
사용: python3 tools/build_act2_assets.py [assets3d 폴더, 기본 assets3d]
"""
import json, os, shutil, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
art = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "assets3d")
res = os.path.join(root, "unity", "Assets", "Resources")
# 1) 땅
tdir = os.path.join(res, "Terrain2"); os.makedirs(tdir, exist_ok=True)
src = os.path.join(art, "terrain_act2")
for n, dst in (("terrain.json", "terrain.json"), ("heightmap.png", "heightmap.bytes"), ("splat_a.png", "splat_a.bytes"), ("splat_b.png", "splat_b.bytes")):
    shutil.copyfile(os.path.join(src, n), os.path.join(tdir, dst))
# 2) 모델
mdir = os.path.join(res, "Models", "Field")
lay = json.load(open(os.path.join(art, "layouts", "act2_layout.json"), encoding="utf-8"))
names = sorted({p["prop"] for p in lay["props"]})
copied = 0
for n in names:
    a = os.path.join(art, "act2", n + ".glb"); b = os.path.join(mdir, n + ".glb")
    if os.path.exists(a) and not os.path.exists(b): shutil.copyfile(a, b); copied += 1
    elif not os.path.exists(a) and not os.path.exists(b): print("경고: 모델 없음", n)
# 3) 배치표 합치기
fp = os.path.join(res, "Data", "field.json")
f = json.load(open(fp, encoding="utf-8"))
f["items"] = [i for i in f["items"] if not (i["z"] >= 640.0 and 0.0 <= i["x"] < 768.0)]   # 이미 합쳐 둔 2막 항목(z>=640, x<768)만 뺀다(멱등). 3막 항목(x>=768, x<0)은 build_act3_assets.py 가 맡는다
items = [{"n": p["prop"], "x": round(p["x"], 2), "z": round(p["y"], 2), "y": round(p.get("z", 0.0), 2), "r": int(p.get("rot", 0)) % 360, "t": 0} for p in lay["props"]]
f["items"] += items
json.dump(f, open(fp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("땅 4파일, 모델 %d개 복사(종류 %d), 배치 %d개 합침 → field.json 항목 %d" % (copied, len(names), len(items), len(f["items"])))
