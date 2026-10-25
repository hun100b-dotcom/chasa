#!/usr/bin/env python3
"""
build_named_souls.py — 첫 세션에 나오는 '이름혼'(박돌쇠·윤 소사·연이·장 둑지기·곽 뱃꾼·방물장수 막례)의 배치표를 만든다.
나이·인(seal)은 서사 원본(data/memories_act1.json)에서 읽고, 자리는 서사 첫 세션 흐름(first_session.json)의 장면을 필드 좌표로 옮긴 임시값이다.
(좌표 확정은 아트·기획 몫. 값만 아래 PLACES 를 고치면 된다.)
seal: clear 또렷(+0) / faded 흐림(처결 대기 +0.25초) / missing 없음(+0.5초) — 서사 규칙.
ledger: 명부 몫이면 True(박돌쇠·곽 뱃꾼), 명부 밖(추가 수확)이면 False.
사용: python3 tools/build_named_souls.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mem = json.load(open(os.path.join(root, "data", "memories_act1.json"), encoding="utf-8"))
by = {s["name"]: s for s in mem["souls"]}
PLACES = [  # 이름, 필드 x, z (임시), 명부 몫 여부
    ("박돌쇠", 182, 68, True), ("윤 소사", 205, 58, False), ("연이", 207, 54, False),
    ("장 둑지기", 184, 174, False), ("곽 뱃꾼", 372, 312, True), ("방물장수 막례", 384, 306, False),
]
AGE = {"fresh": 0, "year": 1, "old": 2}
SEAL = {"clear": 0.0, "faded": 0.25, "missing": 0.5}
out = []
for name, x, z, ledger in PLACES:
    s = by[name]
    out.append({"name": name, "x": x, "z": z, "age": AGE[s["age"]], "wait": SEAL[s["seal"]], "ledger": ledger})
# 갈림(고르는 자리): 서사 첫 세션의 갈림 하나(우물가 혼자 있는 무명 혼, 대기 시간이 멈춤)와 갈림 둘(보릿들 둑길 넷에 둘러싸임)
GROUPS = [
    {"id": "galim1", "x": 176, "z": 52, "n": 1, "trigger": 28, "frozen": True},
    {"id": "galim2", "x": 160, "z": 176, "n": 4, "trigger": 22, "frozen": False},
]
out = {"souls": out, "groups": GROUPS}
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "named_souls.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("이름혼", len(out["souls"]), "갈림", len(GROUPS))
