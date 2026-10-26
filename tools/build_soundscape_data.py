#!/usr/bin/env python3
"""1막 주변 소리 배치표(data/act1_soundscape.json)를 유니티 JsonUtility 가 읽는 납작한 표로 바꾼다.
왜? 원본은 한글 키 사전·배열의 배열이라 JsonUtility 가 못 읽는다. 사용: python3 tools/build_soundscape_data.py"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(root, "data", "act1_soundscape.json"), encoding="utf-8"))
out = {
    "beds": [{"zone": k, "id": v} for k, v in d["beds"].items() if not k.startswith("_")],
    "points": d["points"],
    "props": [{"prop": k, **v} for k, v in d["by_prop"].items() if not k.startswith("_")],
    "loner": {k: v for k, v in d["loner"].items() if not k.startswith("_")},
    "sprinkles": [{"zone": z, "id": a[0], "lo": a[1], "hi": a[2], "night": len(a) < 4 or a[3] == "night"} for z, arr in d["sprinkles"].items() if not z.startswith("_") for a in arr],
    # 낮 바탕(표에 없는 구역은 옛 amb.field 그대로)·물줄기 선 소리(2026-10-26 검은여울 보강)
    "beds_day": [{"zone": k, "id": v} for k, v in d.get("beds_day", {}).items() if not k.startswith("_")],
    "lines": [{"id": v["id"], "x1": v["from"][0], "z1": v["from"][1], "x2": v["to"][0], "z2": v["to"][1], "min": v["min"], "max": v["max"], "night_only": v.get("when") == "night"} for k, v in d.get("lines", {}).items() if not k.startswith("_")],
}
for p in out["props"]:
    p.setdefault("every_m", 0); p.setdefault("when", ""); p.setdefault("group", ""); p.setdefault("day_gain", 1.0); p.setdefault("inside_lowpass_hz", 0)
with open(os.path.join(root, "unity", "Assets", "Resources", "Data", "act1_soundscape.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print("beds", len(out["beds"]), "points", len(out["points"]), "props", len(out["props"]), "sprinkles", len(out["sprinkles"]))
