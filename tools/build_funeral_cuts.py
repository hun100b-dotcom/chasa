#!/usr/bin/env python3
"""
build_funeral_cuts.py — 서사 1막 장례 대본 8개(docs/narrative/funerals_act1.json)를 유니티 컷 표(Resources/Data/cutscenes_funerals.json)로 옮긴다.
컷 이름: FUN-S002_TENDO(천도 48초) / FUN-S002_NONE(처결 못 함 12초). 파혼은 조등만이라 컷이 없다. 박돌쇠 장례는 기본형(build_first_session_cuts.py)을 쓴다.
카메라는 모두 그 집 마당('funeral' 대상, 코드가 혼마다 좌표를 바꿔 준다). condition 이 붙은 박자는 cond 로 옮겨, 그 조건일 때만 적용된다.
사용: python3 tools/build_funeral_cuts.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = json.load(open(os.path.join(root, "docs", "narrative", "funerals_act1.json"), encoding="utf-8"))
ZOOM = {"quarter": 1.0, "slow_zoom_in": 1.3, "low_move": 1.3, "side_track": 1.15, "tilt_up": 1.0, "move": 1.3, "pull_out": 0.9, "follow": 1.2, "close": 1.6, "fade_in": 1.2, "fade_out": 1.2, "black": 1.2}

# 사운드팀이 만든 소리 id 모음. 대본의 sfx_request 가운데 여기 있는 것은 sfx 로 옮겨 실제로 틀고, 아직 없는 것은 건너뛴다
have = {x["id"] for x in json.load(open(os.path.join(root, "data", "sfx_files.json"), encoding="utf-8"))["sounds"]}

def convert(cid, b, lock):
    out = []
    for st in b["steps"]:
        cam = st.get("camera", {}); mode = cam.get("then") if cam.get("then") in ZOOM else cam.get("mode")
        row = {"t": st["t"]}
        if cam:
            row["cam"] = "pan"; row["camTime"] = cam.get("time", 2.0)
            # 서사 카메라 대상 → 기획 funeral_targets 좌표 종류: 멈춘 것 / 대문 / 그 밖(다시 움직이는 것·제사상·개·부엌 …) / 노제·사라지는 자리
            to = cam.get("to"); row["camTo"] = {"stopped_thing": "funeral_stop", "gate": "funeral_gate", "procession": "funeral_noje", "sky": "funeral_exit"}.get(to, "funeral_restart" if to else "funeral_gate")
            if mode in ZOOM: row["zoom"] = ZOOM[mode]
        if st.get("control"): row["ctl"] = st["control"]
        ids = list(st.get("sfx", []))
        for rq in st.get("sfx_request", []):
            i = rq.split("(")[0].strip()   # "amb.rooster(먼 닭울음)" → amb.rooster
            if i in have and i not in ids: ids.append(i)
        if ids: row["sfx"] = ids
        if st.get("condition"): row["cond"] = st["condition"]
        out.append(row)
    out.append({"t": max(0.0, b["duration"] - 0.5), "cam": "return", "camTime": 1.5})
    out.sort(key=lambda r: r["t"])   # 시간 순(같은 시각은 원래 순서 유지)
    return {"id": cid, "duration": b["duration"], "lock": lock, "pause": False, "skippable": b.get("skippable", True), "steps": out}

# 2막 장례(docs/narrative/funerals_act2.json)가 있으면 같이 변환한다. 집 좌표(제사 지켜보기 자리)가 2막 지도와 함께 와야 실제로 열린다
p2 = os.path.join(root, "docs", "narrative", "funerals_act2.json")
if os.path.exists(p2):
    f2 = json.load(open(p2, encoding="utf-8"))["funerals"]
    ids = {f["id"] for f in src["funerals"]}
    assert not any(f["id"] in ids for f in f2), "장례 id 겹침"
    src["funerals"] = src["funerals"] + f2
cuts = []
for f in src["funerals"]:
    for b in f["branches"]:
        if b["branch"] == "천도": cuts.append(convert(f["id"].replace("FUN-", "FUN-") + "_TENDO", b, True))
        elif b["branch"] == "처결 못 함": cuts.append(convert(f["id"] + "_NONE", b, False))
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "cutscenes_funerals.json")
json.dump({"cuts": cuts}, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
# 혼 이름 → 컷 이름 색인(JudgeSystem 이 장례 대상을 알아본다)
idx = [{"soul": f["name"].replace(" 장례", ""), "id": f["id"]} for f in src["funerals"]]
json.dump({"funerals": idx}, open(os.path.join(os.path.dirname(path), "funerals_index.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("컷", len(cuts), [c["id"] for c in cuts][:4])
