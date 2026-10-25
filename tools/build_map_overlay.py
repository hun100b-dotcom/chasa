#!/usr/bin/env python3
"""
build_map_overlay.py — 기획의 2·3막 지도(act2_map.json, act3_map.json)를 미니맵·큰 지도가 읽는 한 파일(map_overlay.json)로 합친다.
왜: 지도 그림(아트)은 1막 필드(0~640m)뿐이다. 그 밖(2·3막)은 지도 범위·구역 상자·길·서낭당·보스 자리를 '데이터'로 받아 도형으로 그린다.
막이 늘면(4막~) 이 스크립트에 지도 파일 이름만 더하면 범위가 자동으로 넓어진다.
사용: python3 tools/build_map_overlay.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = os.path.join(root, "unity", "Assets", "Resources", "Data")
ACT1 = [0.0, 0.0, 640.0, 640.0]   # 1막 필드(아트 지도 있음)
out = {"fills": [], "zones": [], "roads": [], "shrines": [], "bosses": []}
ext = list(ACT1)
def grow(r):
    ext[0] = min(ext[0], r[0]); ext[1] = min(ext[1], r[1]); ext[2] = max(ext[2], r[2]); ext[3] = max(ext[3], r[3])
for act in (2, 3):
    p = os.path.join(res, "act%d_map.json" % act)
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding="utf-8"))
    rects = []
    if "field" in d: rects.append(d["field"]["rect_m"])
    for v in d.get("fields", {}).values(): rects.append(v["rect_m"])
    for r in rects:
        out["fills"].append({"act": act, "rect": [float(x) for x in r]}); grow(r)
    for z in d["zones"]:
        out["zones"].append({"act": act, "name": z["name"], "code": z["code"], "rect": [float(x) for x in z["rect_m"]]}); grow(z["rect_m"])
    for r in d["roads"]:
        out["roads"].append({"act": act, "name": r["name"], "pts": [float(c) for pt in r["points"] for c in pt]})
        for pt in r["points"]: grow([pt[0], pt[1], pt[0], pt[1]])
    for s in d["shrines"]:
        out["shrines"].append({"act": act, "name": s["name"], "x": float(s["x"]), "z": float(s["y"])})
    for b in d["boss_arenas"]:
        out["bosses"].append({"act": act, "name": b["name"], "x": float(b["x"]), "z": float(b["y"])})
out["extent"] = [float(x) for x in ext]
json.dump(out, open(os.path.join(res, "map_overlay.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("지도 범위", ext, "· 구역", len(out["zones"]), "길", len(out["roads"]), "서낭당", len(out["shrines"]), "보스", len(out["bosses"]))
