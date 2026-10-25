#!/usr/bin/env python3
"""
build_named_souls_act2.py — 2막 장례 대상 이름혼 9명의 배치표(named_souls_act2.json). 모양은 named_souls.json 과 같다.
자리: 아트 act2_soul_spots.json 의 kneel_xy(확정). 없으면 기획 act2_map.json funerals[].gate 남쪽 8m(임시). 아트가 확정하면 이 표의 PLACES 만 고치면 된다.
나이·대기 시간은 서사 memories_act2.json(age·seal). ledger=False(명부 밖: 넋·엽전만, 2막 명부 몫 규칙은 기획 확정 전).
사용: python3 tools/build_named_souls_act2.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mem = json.load(open(os.path.join(root, "docs", "narrative", "memories_act2.json"), encoding="utf-8"))
by = {s["id"]: s for s in mem["souls"]}
amap = json.load(open(os.path.join(root, "unity", "Assets", "Resources", "Data", "act2_map.json"), encoding="utf-8"))
AGE = {"fresh": 0, "year": 1, "old": 2}
SEAL = {"clear": 0.0, "faded": 0.25, "missing": 0.5}
# 아트가 확정한 무릎 자리(assets3d/layouts/act2_soul_spots.json, 대문 남쪽 2.5m 열린 땅)가 있으면 그것을 쓴다. 없으면 대문 남쪽 8m
spots = {}
sp = os.path.join(root, "assets3d", "layouts", "act2_soul_spots.json")
if os.path.exists(sp):
    spots = {x["soul"]: x["kneel_xy"] for x in json.load(open(sp, encoding="utf-8"))["spots"]}
out = []
for f in amap["funerals"]:
    s = by[f["soul"]]
    kx, kz = spots.get(f["soul"], (f["gate"][0], f["gate"][1] - 8))
    out.append({"name": f["name"], "x": kx, "z": kz, "age": AGE[s["age"]], "wait": SEAL[s["seal"]], "ledger": False})
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "named_souls_act2.json")
json.dump({"souls": out, "groups": []}, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("2막 이름혼", len(out))
