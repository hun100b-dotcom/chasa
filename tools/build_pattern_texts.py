#!/usr/bin/env python3
"""서사 boss_pattern_texts.json → Resources/Data/pattern_texts.json (JsonUtility 가 읽는 납작한 표).
events: key("B-01.bigwater") · bubble · warn · sfx / danger: 원념 짙은 구역 문구. 사용: python3 tools/build_pattern_texts.py"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(root, "docs", "narrative", "boss_pattern_texts.json"), encoding="utf-8"))
ev = []
for b, v in d["patterns"].items():
    for e in v["events"]:
        ev.append({"key": b + "." + e["event"], "bubble": e.get("bubble", ""), "warn": e.get("warn", ""), "sfx": e.get("sfx", "")})
z = d["danger_zone"]
out = {"events": ev, "enter": z["enter"], "enter_sub": z["enter_sub"], "leave": z["leave"], "karma_high": z["karma_high"]}
json.dump(out, open(os.path.join(root, "unity", "Assets", "Resources", "Data", "pattern_texts.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("events", len(ev))
