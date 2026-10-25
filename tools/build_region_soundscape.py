#!/usr/bin/env python3
"""2·3막 주변 소리 배치표(data/act2_soundscape.json, act3_soundscape.json)를 유니티 JsonUtility 가 읽는 납작한 표로 합친다.
왜? 원본은 한글 키 사전·배열의 배열이라 JsonUtility 가 못 읽는다(1막 build_soundscape_data.py 와 같은 사정).
사용: python3 tools/build_region_soundscape.py  → unity/Assets/Resources/Data/region_soundscape.json"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {"beds": [], "points": [], "overhear": [], "sprinkles": [], "props": [], "timed": []}
for n in (2, 3):
    d = json.load(open(os.path.join(root, "data", "act%d_soundscape.json" % n), encoding="utf-8"))
    for code, v in d["beds"].items():
        if code.startswith("_") or not any(v): continue   # [밤, 낮] 둘 다 null 이면 ZoneAmbient 그대로
        out["beds"].append({"code": code, "night": v[0] or "", "day": v[1] or ""})
    for p in d["points"]:
        out["points"].append({"id": p["id"], "x": p["x"], "z": p["z"], "min": p["min"], "max": p["max"], "when": p["when"], "unlock": p.get("unlock", "")})
    for spot, v in d["overhear"].items():
        if isinstance(v, dict) and "id" in v: out["overhear"].append({"spot": spot, "id": v["id"]})
    for code, arr in d["sprinkles"].items():
        if code.startswith("_"): continue
        for a in arr: out["sprinkles"].append({"code": code, "id": a[0], "lo": a[1], "hi": a[2], "when": a[3] if len(a) > 3 else ""})
    for prop, v in d.get("by_prop", {}).items():
        if not prop.startswith("_"): out["props"].append({"prop": prop, "id": v["id"], "min": v["min"], "max": v["max"], "nearest": v["nearest"], "gain": 0.7})   # 감나무: 1막 고목 소리를 0.7배
    for sid, v in d.get("timed", {}).items():
        if not sid.startswith("_"): out["timed"].append({"id": sid, "zones": v["zones"]})
json.dump(out, open(os.path.join(root, "unity", "Assets", "Resources", "Data", "region_soundscape.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print({k: len(v) for k, v in out.items()})
