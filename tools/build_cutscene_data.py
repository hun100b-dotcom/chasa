#!/usr/bin/env python3
"""
build_cutscene_data.py — 서사팀 컷신 대본(data/cutscenes_b01.json)을 유니티가 읽는 납작한 표(cutscenes_b01.json)로 줄인다.
게임이 쓰는 것만 뽑는다: 시각(t)·카메라(모드/대상/시간/확대)·대사(글자/모양/길이)·길이·입력 잠금·적 멈춤·건너뛰기 가능.
보상·세계 변화(ui 칸)는 이미 천도/파혼 코드가 처리하므로 가져오지 않는다. 원본은 고치지 않는다.
사용: python3 tools/build_cutscene_data.py
"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cuts = []
# 1막 보스 셋(나루 영감·월화·서 의원) 대본을 하나의 표로 합친다. 보스 2·3 은 게임에 아직 없어 데이터만 미리 실린다
srcs = [json.load(open(os.path.join(root, "data", "cutscenes_%s.json" % b), encoding="utf-8")) for b in ("b01", "b02", "b03")]
for c in [x for sr in srcs for x in sr["cutscenes"]]:
    steps = []
    for s in c["steps"]:
        cam = s.get("camera") or {}
        line = s.get("line") or {}
        steps.append({
            "t": s["t"], "cam": cam.get("mode", ""), "camTo": cam.get("to", ""), "camTime": cam.get("time", 0.0),
            "zoom": cam.get("zoom", 0.0), "shake": 1.0 if cam.get("strength") == "big" else 0.0,
            "text": line.get("text", ""), "style": line.get("style", ""), "lineDur": line.get("duration", 0.0),
        })
    cuts.append({"id": c["id"], "duration": c["duration"], "lock": bool(c.get("input_lock")),
                 "pause": c.get("world") == "pause_enemies", "skippable": bool(c.get("skippable")), "steps": steps})
path = os.path.join(root, "unity", "Assets", "Resources", "Data", "cutscenes_b01.json")   # 이름은 b01 이지만 1막 보스 셋을 모두 담는다
json.dump({"cuts": cuts}, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("컷", len(cuts))
