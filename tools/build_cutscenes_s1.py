#!/usr/bin/env python3
"""
build_cutscenes_s1.py — 시즌1 컷신 대본(docs/narrative/cutscenes_s1.json: 2막 B-05~08, 3막 B-09~11, 흑월 B-12, 끝 C-12A/B·C-13)과
소리 대본(data/cutscene_audio_s1.json)을 합쳐 유니티 컷 표(Resources/Data/cutscenes_s1.json)로 만든다.
코드는 보스마다 '<보스 컷 이름>-INTRO/KNEEL/TENDO/PAHON/NOCLUE'(JudgeSystem.BossCut)를 부르므로, 이 파일이 있으면 2·3막 보스 연출이 저절로 붙는다.
소리 덧칠 규칙(사운드팀):
  add      : 그 박자(+delay 초)에 효과음. repeat n·every s 이면 그만큼 되풀이. loop 이면 컷 끝까지 반복 재생, stop 이면 그 반복 소리를 fade 로 끈다
  replace  : 그 박자부터 같은 컷의 소리 id 를 바꿔 튼다(예: 감기는 소리 → 눈 위로 떨어지는 사슬)
  music    : duck/silence/resume/layer/play — 단계의 audio 칸에 "music:op:id:to:fade:fallback" 로 옮긴다
  (gain 은 Sfx 가 소리 크기 인자를 아직 안 받아 무시한다)
사용: python3 tools/build_cutscenes_s1.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = json.load(open(os.path.join(root, "docs", "narrative", "cutscenes_s1.json"), encoding="utf-8"))["cutscenes"]
aud = json.load(open(os.path.join(root, "data", "cutscene_audio_s1.json"), encoding="utf-8"))["cuts"]
have = {x["id"] for x in json.load(open(os.path.join(root, "data", "sfx_files.json"), encoding="utf-8"))["sounds"]}
ZOOM = {"quarter": 1.0, "slow_zoom_in": 1.3, "low_move": 1.3, "side_track": 1.15, "tilt_up": 1.0, "move": 1.3, "pull_out": 0.9, "follow": 1.2, "close": 1.6,
        "fade_in": 1.2, "fade_out": 1.2, "black": 1.2, "push": 1.3, "pull": 1.1, "crane": 1.1, "track": 1.15, "orbit": 1.2, "two_shot": 0.95, "hold": 0.0, "cut": 0.0, "pan": 0.0, "shake": 0.0}

def convert(c):
    steps = []
    def at(t):
        t = round(t, 3)
        for s in steps:
            if s["t"] == t: return s
        s = {"t": t}; steps.append(s); return s
    for st in c["steps"]:
        cam = st.get("camera", {}); row = at(st["t"])
        if cam:
            mode = cam.get("mode")
            row["cam"] = "return" if mode == "return" else "pan"; row["camTime"] = cam.get("time", 1.0)
            if cam.get("to"): row["camTo"] = cam["to"]
            z = cam.get("zoom") or ZOOM.get(mode, 0.0)
            if z: row["zoom"] = z
            if mode == "shake": row["shake"] = cam.get("amount", 0.6)
        ids = list(row.get("sfx", [])) + list(st.get("sfx", []))
        for rq in st.get("sfx_request", []):
            i = rq.split("(")[0].strip()
            if i in have and i not in ids: ids.append(i)
        if ids: row["sfx"] = ids
        ln = st.get("line")
        if isinstance(ln, dict) and ln.get("text"): row["text"] = ln["text"]; row["style"] = ln.get("style", "bubble"); row["lineDur"] = ln.get("duration", 2.5)
        if st.get("weather"): row["weather"] = st["weather"]
    # 소리 대본 덧칠
    rep = {}
    for ts in sorted(aud.get(c["id"], {}), key=float):
        t = float(ts); b = aud[c["id"]][ts]
        rep.update(b.get("replace", {}))
        if rep:   # 이 박자부터 바꿔 틀 소리: 이 박자 이후 단계의 sfx 에 적용
            for s in steps:
                if s["t"] >= t and s.get("sfx"): s["sfx"] = [rep.get(i, i) for i in s["sfx"]]
        for a in b.get("add", []):
            if isinstance(a, str): a = {"id": a}
            if "stop" in a:
                at(t).setdefault("audio", []).append("stop:%s:%s" % (a["stop"], a.get("fade", 0.5))); continue
            sid = rep.get(a["id"], a["id"])
            if a.get("loop"):
                at(t + a.get("delay", 0)).setdefault("audio", []).append("loop:%s:%s" % (sid, a.get("fade", 0.5))); continue
            n = a.get("repeat", 1); every = a.get("every", 0)
            for k in range(n):
                s = at(t + a.get("delay", 0) + k * every); s.setdefault("sfx", []).append(sid)
        m = b.get("music")
        if m:
            at(t).setdefault("audio", []).append("music:%s:%s:%s:%s:%s" % (m["op"], m.get("id", ""), m.get("to", ""), m.get("fade", 1.0), m.get("fallback", "")))
    steps.sort(key=lambda r: r["t"])
    return {"id": c["id"], "duration": c["duration"], "lock": bool(c.get("input_lock", True)), "pause": c.get("world") == "pause_enemies",
            "skippable": c.get("skippable", True), "steps": steps}

cuts = [convert(c) for c in src]
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "cutscenes_s1.json")
json.dump({"cuts": cuts}, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("시즌1 컷", len(cuts), "소리 단계", sum(1 for c in cuts for s in c["steps"] if s.get("audio")))
