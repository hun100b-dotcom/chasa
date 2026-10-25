#!/usr/bin/env python3
"""
build_first_session_cuts.py — 서사 '첫 세션 대본'(docs/narrative/first_session_scripts.json)을
유니티 컷신 표(Resources/Data/cutscenes_first_session.json)로 옮긴다. 오프닝(OPENING)·박돌쇠 장례(FUNERAL_TENDO / FUNERAL_NONE).
파혼 갈래는 '아무 일도 없다'가 canon 이라 컷을 만들지 않는다(조등 소품만).
대사·자막이 거의 없는 것이 canon: 글자는 소리 자막(sfx, 대괄호)이 대부분이다. 소리가 없는 지금은 기본으로 보여 준다.
사용: python3 tools/build_first_session_cuts.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = json.load(open(os.path.join(root, "docs", "narrative", "first_session_scripts.json"), encoding="utf-8"))

# 서사의 카메라 대상 이름 → 유니티 CutTarget 이름(좌표는 GameMain.CutTarget). 모르는 대상은 장례 마당으로
TARGET = {"forge_inside": "forge", "procession": "funeral", "gate": "funeral", "sky": "funeral", "torch": "player"}
# 카메라 모드 → 확대 배율(1 = 평소). 서사 문구를 눈대중으로 옮긴 임시값
ZOOM = {"quarter": 1.0, "slow_zoom_in": 1.3, "low_move": 1.3, "side_track": 1.15, "tilt_up": 1.0, "move": 1.3, "pull_out": 0.9,
        "follow": 1.2, "close": 1.6, "fade_in": 1.2, "fade_out": 1.2, "black": 1.2}

CAPTIONS = False   # 소리 자막(접근성): 서사 확정 — 소리가 들어오면 접근성 설정에서만 켠다. 설정 화면이 생기면 런타임 옵션으로

def convert(cid, data, lock):
    steps = data["steps"]
    out = []
    for i, st in enumerate(steps):
        t = st["t"]; cam = st.get("camera", {})
        mode = cam.get("then") if cam.get("then") in ZOOM else cam.get("mode")
        row = {"t": t}
        if cam:
            row["cam"] = "pan"
            row["camTo"] = TARGET.get(cam.get("to"), "funeral" if cid != "OPENING" else "player")
            row["camTime"] = cam.get("time", 2.0)
            if mode in ZOOM: row["zoom"] = ZOOM[mode]
        if st.get("control"): row["ctl"] = st["control"]
        nxt = steps[i + 1]["t"] if i + 1 < len(steps) else data["duration"]
        if st.get("sfx"): row["sfx"] = st["sfx"]   # 틀 효과음 id 들(소리가 생겼으니 글자 자막은 기본으로 끈다)
        if CAPTIONS and st.get("caption"):
            row["text"] = st["caption"]; row["style"] = "sfx"; row["lineDur"] = max(1.5, nxt - t)
        out.append(row)
    out.append({"t": max(0.0, data["duration"] - 0.5), "cam": "return", "camTime": 1.5})
    return {"id": cid, "duration": data["duration"], "lock": lock, "pause": False, "skippable": data.get("skippable", False), "steps": out}

cuts = []
op = src["opening"]
c = convert("OPENING", op, True); c["pause"] = True; c["skippable"] = False   # 입력 잠금·시계 멈춤·건너뛰기 불가(서사 확정)
cuts.append(c)
for b in src["funeral"]["branches"]:
    if b["branch"] == "천도": cuts.append(convert("FUNERAL_TENDO", b, True))
    elif b["branch"] == "처결 못 함":
        c = convert("FUNERAL_NONE", b, False)
        # 아내의 한 줄(차사가 마당 안에 있을 때만 — 지금은 마당에서 시작하는 컷이라 항상 보인다)
        for st in b["steps"]:
            if st.get("line"):
                c["steps"].append({"t": st["t"], "text": st["line"]["text"], "style": "bubble", "lineDur": st["line"]["duration"]})
        c["steps"].sort(key=lambda r: r["t"])
        cuts.append(c)
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "cutscenes_first_session.json")
json.dump({"cuts": cuts}, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("컷", [c["id"] for c in cuts])
