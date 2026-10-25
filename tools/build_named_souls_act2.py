#!/usr/bin/env python3
"""
build_named_souls_act2.py — 2막 장례 대상 이름혼 9명의 배치표(named_souls_act2.json). 모양은 named_souls.json 과 같다.
자리는 임시: 기획 act2_map.json 의 funerals[].gate(대문)에서 남쪽 8m(집 앞 길). 아트가 확정하면 이 표의 PLACES 만 고치면 된다.
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
out = []
for f in amap["funerals"]:
    s = by[f["soul"]]
    out.append({"name": f["name"], "x": f["gate"][0], "z": f["gate"][1] - 8, "age": AGE[s["age"]], "wait": SEAL[s["seal"]], "ledger": False})
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "named_souls_act2.json")
json.dump({"souls": out, "groups": []}, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("2막 이름혼", len(out))
