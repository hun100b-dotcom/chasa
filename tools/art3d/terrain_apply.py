"""새 지형(terrain_ground.py의 높이표)에 맞춰 field_5x5.json의 소품 높이를 다시 계산한다. 실행: python3 terrain_apply.py
순서: field_layout.py → terrain_apply.py → field_export.py → field_lights.py.
왜: 땅에 ±17cm 자연 굴곡을 넣었으므로 나무·바위·소품의 gz(=땅 윗면 높이)를 지형에 맞춰야 뜨거나 묻히지 않는다.
건물·구조물 둘레는 지형이 평평하게 눌려 있어(terrain_ground FLAT) 구조물 z는 그대로 둔다. 검은여울 강 조각(br_*) 위 소품은 그대로 둔다."""
import os, json
import numpy as np
import terrain_ground as tg

path = os.path.join(tg.A3, "layouts", "field_5x5.json")
F = json.load(open(path, encoding="utf-8")); n = 0
for p in F["props"]:
    if p["prop"].startswith("br_"): continue
    tx, ty = int(p["x"] // tg.T), int(p["y"] // tg.T)
    if 0 <= tx < tg.NC and 0 <= ty < tg.NC and tg.is_br[ty, tx]: continue
    gz = float(tg.height_at(np.array([p["x"]]), np.array([p["y"]]))[0]); p["gz"] = round(gz, 2); p["z"] = round(gz - 0.3, 2); n += 1
F["ground"] = {"mode": "terrain_chunks", "note": "땅은 assets3d/terrain/chunk_{cx}_{cy}.glb(지형+땅 그림)로 깐다. tiles[]는 br_*(검은여울 강 조각)만 실제로 놓고 나머지 지형 타일은 쓰지 않는다(옛 호환용으로만 남김). props[].gz는 새 지형 높이에 맞춰 다시 계산됨.",
               "height_table": "assets3d/terrain/terrain_height_2m.png", "manifest": "assets3d/terrain/_terrain_manifest.json"}
json.dump(F, open(path, "w"), ensure_ascii=False, indent=1); print("props 높이 재계산", n)
