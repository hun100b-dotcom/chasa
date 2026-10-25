#!/usr/bin/env python3
"""서사 overhear_act2/act3.json(2·3막 소문 엿듣기 30자리) → Resources/Data/overhear_flat.json. 사용: python3 tools/build_overhear_data.py"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = {"새벽": 0, "낮": 1, "저녁": 2, "밤": 3}
out = []
for act, fn in ((2, "overhear_act2"), (3, "overhear_act3")):
    d = json.load(open(os.path.join(root, "docs", "narrative", fn + ".json"), encoding="utf-8"))
    for s in d["spots"]:
        out.append({"id": s["id"], "act": act, "time": T[s["time"]], "x": s["x"], "z": s["y"], "place": s["place"],
                    "speakers": [l["speaker"] for l in s["lines"]], "lines": [l["text"] for l in s["lines"]], "half": s["line_half"],
                    "echo": s.get("echoes_name") or ""})
json.dump({"spots": out}, open(os.path.join(root, "unity", "Assets", "Resources", "Data", "overhear_flat.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("spots", len(out))
