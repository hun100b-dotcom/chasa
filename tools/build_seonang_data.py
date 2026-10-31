#!/usr/bin/env python3
"""서사 seonang_texts.json 을 유니티 JsonUtility 가 읽는 납작한 표(Resources/Data/seonang_flat.json)로 바꾼다.
서낭당 5곳 문구(처음 만짐·쉬기 낮/밤·보스 뒤)와 첫 밤 솔고개 엿듣기 15자리. 사용: python3 tools/build_seonang_data.py"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(root, "docs", "narrative", "seonang_texts.json"), encoding="utf-8"))
sh = []
for s in d["seonang"]["shrines"]:
    ab = s.get("after_boss") or {}
    sh.append({"model": s["model"], "first_touch": s["first_touch"], "rest_day": s["rest_day"], "rest_night": s["rest_night"],
               "rest_halmi": s.get("rest_halmi", ""), "boss": int(ab["boss"][2:]) if ab else 0,
               "tendo": ab.get("tendo", ""), "pahon": ab.get("pahon", "")})
fn = []
for o in d["first_night_overhear"]["spots"]:
    fn.append({"id": o["id"], "x": o["pos"]["x"], "z": o["pos"]["y"], "cond": o["cond"], "wall": bool(o["through_wall"]),
               "speakers": [l["speaker"] for l in o["lines"]], "lines": [l["text"] for l in o["lines"]], "half": o["line_half"]})
out = {"shrines": sh, "death_wake": d["seonang"]["death_wake"], "overhear": fn}
with open(os.path.join(root, "unity", "Assets", "Resources", "Data", "seonang_flat.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print("shrines", len(sh), "overhear", len(fn))
