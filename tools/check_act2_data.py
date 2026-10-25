#!/usr/bin/env python3
"""
check_act2_data.py — 서사 2막 데이터(docs/narrative/*_act2.json)가 1막과 같은 구조로 읽히는지 검사한다(2막 지도가 오면 바로 연결하려고).
 · memories_act2: 혼 칸이 1막과 같고, 이름이 1막과 겹치지 않는다
 · funerals_act2: 장례마다 천도·파혼·처결 못 함 갈래, 박자 칸이 1막과 같다(condition 문구는 목록으로 보여 준다)
 · npc_act2: 1막과 달리 일정표(schedule) 없이 barks·link_soul 만 있다 → 2막 지도·자리 데이터를 받을 때까지 NpcWorld 에 넣지 않음
사용: python3 tools/check_act2_data.py   (문제가 있으면 종료 코드 1)
"""
import json, os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p): return json.load(open(os.path.join(root, p), encoding="utf-8"))
bad = []
m1, m2 = load("data/memories_act1.json"), load("docs/narrative/memories_act2.json")
need = {"name", "age", "seal", "memory", "tint", "fact", "mystery", "decisive", "boss", "funeral"}
for s in m2["souls"]:
    miss = need - set(s.keys())
    if miss: bad.append("memories_act2 %s: 칸 없음 %s" % (s.get("name"), sorted(miss)))
dup = {s["name"] for s in m1["souls"]} & {s["name"] for s in m2["souls"]}
if dup: bad.append("1막·2막 혼 이름 겹침 %s" % sorted(dup))
f1, f2 = load("docs/narrative/funerals_act1.json"), load("docs/narrative/funerals_act2.json")
k1 = set(f1["funerals"][0].keys()); conds = set()
for f in f2["funerals"]:
    if set(f.keys()) != k1: bad.append("funerals_act2 %s: 칸 다름 %s" % (f.get("id"), set(f.keys()) ^ k1))
    br = {b["branch"] for b in f["branches"]}
    if br != {"천도", "파혼", "처결 못 함"}: bad.append("funerals_act2 %s: 갈래 %s" % (f["id"], br))
    for b in f["branches"]:
        ts = [s["t"] for s in b["steps"]]
        if ts != sorted(ts): bad.append("funerals_act2 %s %s: 박자 시간이 순서대로가 아님" % (f["id"], b["branch"]))
        for s in b["steps"]:
            if s.get("condition"): conds.add(s["condition"])
n2 = load("docs/narrative/npc_act2.json")
noSched = sum(1 for x in n2["npcs"] if "schedule" not in x)
print("2막 기억 %d명 · 장례 %d개 · 장례 조건 %s · 산 사람 %d명(일정표 없는 사람 %d명)" % (len(m2["souls"]), len(f2["funerals"]), sorted(conds), len(n2["npcs"]), noSched))
if noSched: print("알림: npc_act2 는 일정표가 없어 NpcWorld 에 아직 못 넣는다(2막 지도·자리 대기)")
for b in bad: print("문제:", b)
sys.exit(1 if bad else 0)
