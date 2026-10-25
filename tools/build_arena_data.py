#!/usr/bin/env python3
"""
build_arena_data.py — 아트팀 보스 싸움터 배치표(boss_arenas.json)를 유니티가 읽는 짧은 표로 줄이고,
쓰는 소품 GLB·바닥 무늬·예고 장판 그림을 Resources 로 복사한다.
왜? 좌표(블렌더 x 동·y 북)·긴 경로·설명글을 게임이 직접 읽지 않게 하려고. 유니티 좌표는 (x, 높이, z)=(x, z, y).
사용: python3 tools/build_arena_data.py <assets3d 폴더>
"""
import json, os, shutil, sys

art = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = os.path.join(root, "unity", "Assets", "Resources")
src = json.load(open(os.path.join(art, "layouts", "boss_arenas.json"), encoding="utf-8"))
out, used = [], set()
for key, a in sorted(src["arenas"].items()):
    props = []
    for p in a["props"]:
        used.add(p["prop"])
        props.append({"n": p["prop"], "x": p["x"], "z": p["y"], "r": int(p.get("rot", 0)), "c": p.get("cup", -1)})
    lights = [{"x": l["x"], "z": l["y"], "h": l["z"], "col": l["color"], "i": l["intensity"], "range": l["range_m"],
               "flicker": bool(l.get("flicker")), "weak": "약점" in l.get("tag", "")} for l in a.get("lights", [])]
    out.append({"id": int(key[1:]), "x": a["boss_pos"]["x"], "z": a["boss_pos"]["y"], "decal": os.path.basename(a["decal"]["file"]).replace(".png", ""),
                "decalSize": a["decal"]["size_m"], "waterLevel": a["medium"].startswith("물"), "props": props, "lights": lights})
json.dump({"arenas": out}, open(os.path.join(res, "Data", "boss_arenas.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
dst = os.path.join(res, "Models", "Field"); os.makedirs(dst, exist_ok=True)
for n in sorted(used):
    shutil.copyfile(os.path.join(art, "props", n + ".glb"), os.path.join(dst, n + ".glb"))
sp = os.path.join(res, "Sprites", "boss"); os.makedirs(sp, exist_ok=True)
for f in sorted(os.listdir(os.path.join(art, "boss"))):
    if f.endswith(".png") and (f.startswith("arena_") or f.startswith("tele_")):
        shutil.copyfile(os.path.join(art, "boss", f), os.path.join(sp, f))
print("싸움터", len(out), "소품 종류", len(used))
