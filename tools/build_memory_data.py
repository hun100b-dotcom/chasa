#!/usr/bin/env python3
"""
build_memory_data.py — 서사팀 data/memories_act1.json 을 유니티가 읽는 납작한 표(memory_flat.json)로 줄인다.
(JsonUtility 가 사전(dict)을 못 읽고, 게임에 필요한 칸만 쓰려고.) 원본은 고치지 않는다.
사용: python3 tools/build_memory_data.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = json.load(open(os.path.join(root, "data", "memories_act1.json"), encoding="utf-8"))
out = {
    "fresh": s["generic"]["fresh"], "year": s["generic"]["year"], "old": s["generic"]["old"],
    "souls": [{"name": x["name"], "memory": x["memory"], "tint": x.get("tint", ""), "fact": x.get("fact", ""),
               "mystery": bool(x.get("mystery")), "decisive": bool(x.get("decisive")), "boss": bool(x.get("boss")), "jesa": x.get("jesa_extra") or ""}
              for x in s["souls"]],
}
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "memory_flat.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("혼", len(out["souls"]), "공용", len(out["fresh"]) + len(out["year"]) + len(out["old"]))
