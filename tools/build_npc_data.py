#!/usr/bin/env python3
"""
build_npc_data.py — 서사팀 NPC 데이터(data/npc_act1.json)를 유니티가 읽기 쉬운 납작한 표(npc_flat.json)로 만든다.

왜? 유니티의 JsonUtility 는 '이름이 자유로운 사전(dict)'을 못 읽는다. 원본은 보스 이름(B-01…)이 키라서 그대로는 못 읽는다.
그래서 (1) 일정표를 한 줄씩 펴고 (2) 보스 단서를 목록으로 바꾼다. 원본은 고치지 않는다.
사용: python3 tools/build_npc_data.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = json.load(open(os.path.join(root, "data", "npc_act1.json"), encoding="utf-8"))
TIME = {"새벽": 0, "낮": 1, "저녁": 2, "밤": 3}   # 0 동틀녘 1 낮 2 해질녘 3 밤 (WorldClock 의 ClockPhase 순서)
rows = []
for n in src["npcs"]:
    for s in n["schedule"]:
        rows.append({
            "npc": n["id"], "name": n["name"], "region": n["region"], "unlock": n.get("unlock_night", 1),
            "time": TIME[s["time"]], "zone": s["zone"], "place": s["place"], "verb": s.get("verb", ""),
            "line": s.get("line", ""), "half": s.get("line_half", ""), "clue": s.get("clue") or "",
        })
clues = []
for boss, b in src["boss_clues"].items():
    if not isinstance(b, dict): continue
    for c in b.get("clues", []):
        clues.append({"boss": boss, "id": c["id"], "verb": c.get("verb", ""), "time": TIME.get(c.get("time", "낮"), 1),
                      "zone": c.get("zone", ""), "place": c.get("place", ""), "npc": c.get("npc") or "", "what": c.get("what", "")})
places = [{"place": k, "ox": v["offset_m"][0], "oz": v["offset_m"][1]} for k, v in src.get("places", {}).items()]
# 아트가 필드 절대 좌표(x=동, y=북 m)로 확정한 자리가 있으면 그것을 우선한다 (data/art/npc_places_act1.json)
art_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "art", "npc_places_act1.json")
if os.path.exists(art_path):
    art = json.load(open(art_path, encoding="utf-8"))["places"]
    n = 0
    for pl in places:
        a = art.get(pl["place"])
        if a: pl["ax"], pl["az"], pl["abs"] = a["x"], a["y"], 1; n += 1
    print("아트 확정 좌표 적용", n, "/", len(places))
out = {"entries": rows, "clues": clues, "places": places}
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "npc_flat.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("일정", len(rows), "단서", len(clues))
