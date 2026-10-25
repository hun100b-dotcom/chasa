#!/usr/bin/env python3
"""
build_npc_act2.py — 2막 산 사람·단서 자리를 유니티가 읽는 납작한 표(npc_flat_act2.json)로 만든다. (npc_flat.json 과 같은 모양)

왜 따로? 1막 표(npc_flat)는 서사 data/npc_act1.json 에서 만들고, 2막 좌표는 기획 act2_map.json(절대 좌표, x=동 y=북)에 있다.
  - 시간표·자리: act2_map.json 의 npc_schedules (좌표 포함)
  - 단서 말: 서사 boss_clues_act2.json (엿듣기 line / 만져 보기 text). 지켜보기는 대사가 없어 '무엇을 보는가'(what)를 짧은 글로 쓴다
    → 서사가 지켜보기 줄을 쓰면 npc_act2.json schedule 의 line 이 우선한다(아래 코드가 먼저 본다).
  - 혼잣말(barks): npc_act2.json
사용: python3 tools/build_npc_act2.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(root, *p)
TIME = {"새벽": 0, "낮": 1, "저녁": 2, "밤": 3}
npc = json.load(open(R("docs", "narrative", "npc_act2.json"), encoding="utf-8"))
amap = json.load(open(R("unity", "Assets", "Resources", "Data", "act2_map.json"), encoding="utf-8"))
clues = json.load(open(R("docs", "narrative", "boss_clues_act2.json"), encoding="utf-8"))["boss_clues"]
clue_by_id = {c["id"]: dict(c, boss=b) for b, v in clues.items() for c in v["clues"]}
by_id = {n["id"]: n for n in npc["npcs"]}

rows, places = [], {}
for key, sched in amap["npc_schedules"].items():
    nid = key.split()[0]; n = by_id.get(nid)
    if not n: continue
    for tname, spots in sched.items():
        for s in spots:
            places[s["place"]] = (s["x"], s["y"])
            clue = s.get("clue") or ""
            c = clue_by_id.get(clue, {})
            # 서사 일정표의 같은 칸에 line 이 있으면 그것을 먼저 쓴다
            line = half = ""
            for ns in n["schedule"]:
                if ns["time"] == tname and ns["place"] == s["place"] and ns.get("line"):
                    line, half = ns["line"], ns.get("line_half", "")
            if not line and c:
                line = c.get("line") or c.get("what", "")
                half = c.get("line_half") or line
            if not line and not clue: continue   # 말도 단서도 없는 줄
            rows.append({"npc": nid, "name": n["name"], "region": n["region"], "unlock": 1, "time": TIME[tname],
                         "zone": n["zone"], "place": s["place"], "verb": s.get("verb") or "", "line": line, "half": half,
                         "clue": clue, "barks": n.get("barks", {}).get(tname, [])})
# 사람 없이 물건에만 달린 단서(만져 보기)와 밤 대체 단서
cl = []
for bc in amap["boss_clues"]:
    c = clue_by_id[bc["id"]]
    if c.get("npc"): continue
    xy = bc["xy"][0]; places[xy["place"]] = (xy["x"], xy["y"])
    what = c.get("text") or c.get("what", "")
    cl.append({"boss": bc["boss"], "id": bc["id"], "verb": c["verb"], "time": 1, "zone": c.get("zone", ""),
               "place": xy["place"], "npc": "", "what": what})
pl = [{"place": k, "ox": 0, "oz": 0, "ax": v[0], "az": v[1], "abs": 1} for k, v in places.items()]
out = {"entries": rows, "clues": cl, "places": pl}
path = R("unity", "Assets", "Resources", "Data", "npc_flat_act2.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("2막 일정", len(rows), "물건 단서", len(cl), "자리", len(pl))
