# -*- coding: utf-8 -*-
"""
시즌1 컷신 44컷(docs/narrative/cutscenes_s1.json)의 '소리 대본' 덧칠표 (기획·사운드, 2026-10-25)

왜 따로 두나:
  컷신 대본은 서사팀 파일(생성기 tools/cutscenes_s1.py)이라 사운드팀이 직접 고치지 않는다.
  대신 같은 (컷 id, 박자 시각 t)를 열쇠로 '여기에 소리를 더 얹어라 / 음악을 이렇게 바꿔라'만 적는다.
  CutscenePlayer 가 박자를 틀 때 대본의 sfx 에 이 표의 add 를 더하고, music 을 BgmPlayer 에 넘기면 된다.

실행:  python3 tools/cutscene_audio_s1.py            → data/cutscene_audio_s1.json
       python3 tools/cutscene_audio_s1.py 대본.json  → 모든 열쇠가 대본에 있는지·소리 id가 다 있는지 검사도 함

항목 모양(add 안):
  "id"                          그냥 한 번 틀기
  {"id", "gain", "delay"}       크기(배수)·늦춰 틀기(초)
  {"id", "repeat", "every"}     여러 번(간격 초) — 매듭 일곱 개, 일곱 사람 건지기
  {"id", "loop": true}          반복 소리 켜기(컷이 끝나거나 stop 이 올 때까지)
  {"stop": "id", "fade"}        반복 소리 끄기
replace: {"대본 id": "바꿀 id"} — 같은 순간에 더 맞는 소리가 생겼을 때
music:   {"op": "duck", "to", "fade"} 낮추기 / {"op": "silence", "fade"} 끄기 / {"op": "resume", "fade"} 평소 층으로
         {"op": "layer", "id": "combat"|"finish"} 필드 BGM 층 바꾸기 / {"op": "play", "id", "fade", "fallback"} 곡 하나 틀기(파일 없으면 fallback)
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DUCK_IN = {"op": "duck", "to": 0.35, "fade": 0.8}           # 등장 컷: 지역 음악을 낮춘다(보스가 먼저 보이게)
TO_COMBAT = {"op": "layer", "id": "combat", "fade": 1.0}     # 등장 컷 끝 = 보스전 시작
TENDO_IN = {"op": "silence", "fade": 0.4}                    # 천도 컷: 음악을 비워 명부·기억 소리만(bgm.json '처결 중 BGM 쉼'과 같은 결)
PAHON_IN = {"op": "silence", "fade": 0.1}                    # 파혼: 폭발과 함께 뚝 끊는다
RESUME_SLOW = {"op": "resume", "fade": 3.0}
RESUME = {"op": "resume", "fade": 2.0}


def boss(code, intro, tendo, pahon, kneel=None, tendo_end=7.5):
    """2·3막 보스 한 명의 컷 다섯 개. 비어 있는 박자에만 소리를 더한다"""
    out = {}
    out[code + "-INTRO"] = {0.0: {"music": DUCK_IN}, 4.5: {"music": TO_COMBAT}}
    for t, v in intro.items(): out[code + "-INTRO"].setdefault(t, {}).update(v)
    out[code + "-KNEEL"] = {0.0: {"music": {"op": "layer", "id": "finish", "fade": 0.3}}}   # 무릎 = 종 한 번(bgm.json finish 층)
    if kneel: out[code + "-KNEEL"][0.0].update(kneel)
    out[code + "-TENDO"] = {0.0: {"music": TENDO_IN}, tendo_end: {"music": RESUME_SLOW}}
    for t, v in tendo.items(): out[code + "-TENDO"].setdefault(t, {}).update(v)
    out[code + "-PAHON"] = {0.0: {"music": PAHON_IN}, 2.5: {"music": RESUME}}
    for t, v in pahon.items(): out[code + "-PAHON"].setdefault(t, {}).update(v)
    return out


CUTS = {}
# ---- 2막 ----
CUTS.update(boss("B05",
    intro={2.4: {"add": [{"id": "cut.soldier.rise", "delay": 1.0, "gain": 0.8}]}},                         # 입을 열 '때마다' — 두 번째 혼
    tendo={1.5: {"add": ["cut.names.glow"]}},                                                 # 칼금 이름에 하나씩 빛
    pahon={1.5: {"add": [{"id": "cut.cloth.flutter", "gain": 0.8}]}}))                       # 찢어진 군기 펄럭
CUTS.update(boss("B06",
    intro={1.6: {"add": [{"id": "sfx.boss.general.formation", "delay": 0.5}]},
           3.0: {"add": [{"id": "cut.war.drum", "repeat": 2, "every": 0.6}, {"id": "sfx.boss.general.formation", "delay": 1.2}]}},
    kneel={"add": [{"id": "cut.tag.drop", "delay": 0.5}]},                                    # 북채가 땅에 떨어짐
    tendo={3.0: {"add": [{"id": "cut.tag.drop", "repeat": 3, "every": 0.6, "gain": 0.8}]}},   # 대본의 패 소리 뒤로 두 개 더
    pahon={0.0: {"add": ["cut.paper.burn"]}, 0.8: {"add": [{"id": "cut.tag.drop", "repeat": 3, "every": 0.15, "gain": 0.5}]}}))   # 진법도가 불티로 / 숫자 패가 흩어짐
CUTS.update(boss("B07",
    intro={},
    tendo={1.0: {"music": {"op": "silence", "fade": 0.0}, "note": "칠성의 한 줄 — 효과음도 0.6초 비운다"},
           5.0: {"add": [{"id": "amb.sea.wind", "loop": True}]}},
    pahon={0.0: {"add": [{"id": "cut.stone.crack", "delay": 0.1}]}}, tendo_end=8.0))
CUTS.update(boss("B08",
    intro={1.6: {"add": [{"id": "sfx.boss.yeom.land", "delay": 0.6, "gain": 0.7}]},
           3.2: {"add": [{"id": "sfx.boss.yeom.backpage", "gain": 0.7}]}},
    kneel={"add": [{"id": "sfx.ui.ledger.close", "delay": 0.3}]},                             # 장부를 품에 안고 덮음
    tendo={3.0: {"add": ["cut.paper.ascend"]}},
    pahon={0.0: {"add": ["cut.paper.burn"]}, 1.5: {"add": ["cut.coins.spill"]}}))
# ---- 3막 ----
CUTS.update(boss("B09",
    intro={},
    tendo={},
    pahon={0.0: {"add": ["sfx.boss.mangbu.wave"]}, 0.8: {"add": [{"id": "cut.cloth.flutter", "gain": 0.8}]}, 1.5: {"add": ["cut.stone.crack"]}},
    tendo_end=8.0))
CUTS.update(boss("B10",
    intro={2.6: {"add": ["sfx.boss.seonjang.rope.telegraph", {"id": "cut.hull.creak", "delay": 0.4, "gain": 0.7}]}},
    kneel={"add": [{"id": "cut.hull.creak", "gain": 0.6}]},
    tendo={4.0: {"add": [{"id": "cut.rope.untie", "repeat": 6, "every": 0.28, "delay": 0.28}]},   # 대본의 한 번 + 여섯 = 일곱 매듭
           7.0: {"add": [{"id": "cut.lantern.light", "gain": 0.7}]}},                                  # 젖은 돌길이 드러남
    pahon={0.0: {"add": ["cut.boat.break"]}, 0.8: {"add": ["sfx.boss.seonjang.crew.fall"]}, 1.5: {"add": ["cut.anchor.drop"]}},
    tendo_end=8.5))
CUTS.update(boss("B11",
    intro={1.4: {"add": ["cut.soul.rise"]}, 3.6: {"add": ["sfx.boss.wangcho.turn"]}},             # 3.6은 조건 박자: 조건일 때만
    tendo={1.5: {"add": ["cut.names.glow"], "note": "목걸이 조각 다섯 음 — 마지막 빈 조각은 소리 없음(일부러)"},
           4.5: {"add": [{"id": "cut.brush.stroke", "gain": 0.8}]}},                                 # 명부에 '왕초'가 적힘
    pahon={0.0: {"add": ["cut.cloth.flutter"]}, 0.8: {"add": ["cut.beads.scatter"]}, 1.5: {"add": [{"id": "cut.coins.spill", "gain": 0.7}]}},
    tendo_end=8.0))
CUTS["B11-AFTER"] = {0.0: {"music": {"op": "duck", "to": 0.25, "fade": 1.0}}, 6.0: {"music": RESUME_SLOW}}
# ---- 흑월 2차 결전 ----
CUTS["B12-INTRO"] = {
    0.0: {"add": [{"id": "amb.snow.wind", "loop": True}], "music": {"op": "silence", "fade": 1.5}},
    2.5: {"add": [{"id": "cut.chain.drag", "gain": 0.5}]},                                         # 사슬 끝이 눈에 줄을 남김(작게)
    6.0: {"add": [{"id": "sfx.boss.heukwol.steal", "gain": 0.6}]},                                 # 천도하는 손짓
    8.0: {"music": {"op": "play", "id": "bgm_s1_heukwol", "fade": 1.0, "fallback": "combat"}}}
CUTS["B12-P2"] = {0.0: {"music": {"op": "duck", "to": 0.75, "fade": 0.1}, "note": "전투 쪽 sfx.boss.heukwol.line.draw 와 겹치지 않게, 이 컷에서는 대본 cut.chain.drag 만"},
                  2.5: {"music": {"op": "resume", "fade": 1.2}}}
CUTS["B12-P3"] = {0.0: {"add": ["sfx.boss.heukwol.flood", {"stop": "amb.snow.wind", "fade": 2.0}], "replace": {"amb.rain": "amb.weather.rain.heavy"}},
                  1.0: {"add": [{"id": "cut.lantern.light", "gain": 0.5}]}}                         # 물 위 횃불 하나
CUTS["B12-KNEEL"] = {
    0.0: {"add": [{"stop": "amb.weather.rain.heavy", "fade": 2.5}], "music": {"op": "duck", "to": 0.3, "fade": 1.5}},
    1.5: {"replace": {"cut.chain.wrap": "sfx.boss.heukwol.chain.down"}, "note": "전투 쪽 chain.down 은 이 컷이 대신 튼다(두 번 울리지 않게)"},
    2.8: {"music": {"op": "silence", "fade": 0.5}, "note": "흑월의 한 줄. 이 줄 뒤로 처결할 때까지 음악 없음 — 눈바람만"},
    5.6: {"add": [{"id": "amb.snow.wind", "loop": True}]}}
# ---- 시즌 1 끝 ----
CUTS["C-12A"] = {
    0.0: {"music": {"op": "silence", "fade": 0.5}},
    2.0: {"add": [{"stop": "amb.snow.wind", "fade": 2.0}]},
    4.0: {"add": [{"id": "amb.weather.rain.heavy", "loop": True}, {"id": "sfx.weather.thunder.far", "delay": 1.5, "gain": 0.7}],
          "music": {"op": "play", "id": "bgm_s1_finale_a", "fade": 4.0, "fallback": "silence"}},
    10.0: {"add": [{"id": "cut.splash.pull", "repeat": 6, "every": 2.3, "delay": 2.3, "gain": 0.85}], "note": "대본의 한 번 + 여섯 = 일곱 사람"},
    26.0: {"music": {"op": "duck", "to": 0.6, "fade": 2.0}},
    32.0: {"music": {"op": "duck", "to": 0.35, "fade": 1.0}},
    38.0: {"add": [{"id": "cut.splash.pull", "gain": 0.8}]},
    46.0: {"add": [{"id": "cut.seal.fade", "delay": 1.0, "gain": 0.7}]},                            # 이름 자리에 획이 없다
    54.0: {"note": "C-01 t=15.0 과 같은 cut.chain.wrap — 같은 소리라서 겹침(F9)이 귀로도 맞는다. 바꾸지 말 것"},
    60.0: {"add": [{"stop": "amb.weather.rain.heavy", "fade": 3.0}], "music": {"op": "duck", "to": 0.3, "fade": 1.0}},
    66.0: {"add": ["cut.color.shift", {"id": "amb.snow.wind", "loop": True, "gain": 0.6}], "music": {"op": "duck", "to": 0.7, "fade": 4.0}},
    82.0: {"music": {"op": "duck", "to": 0.4, "fade": 2.0}},
    90.0: {"music": {"op": "silence", "fade": 3.0}}}
CUTS["C-12B"] = {
    0.0: {"music": {"op": "silence", "fade": 0.05}},
    8.0: {"replace": {"cut.chain.wrap": "sfx.boss.heukwol.chain.down"}, "note": "감기는 소리가 아니라 눈 위로 떨어지는 사슬"},
    12.0: {"add": ["cut.soul.brush"]},
    20.0: {"note": "대본 amb.snow.wind 는 반복으로 튼다", "add": [{"id": "amb.snow.wind", "loop": True}]},
    35.0: {"add": [{"id": "cut.seal.fade", "gain": 0.6}]},                                          # 추리판 빈칸이 번진 채
    50.0: {"music": {"op": "play", "id": "bgm_s1_finale_b", "fade": 3.0, "fallback": "silence"}},
    60.0: {"add": [{"stop": "amb.snow.wind", "fade": 3.0}], "music": {"op": "silence", "fade": 3.0}}}
CUTS["C-13"] = {
    0.0: {"note": "대본 amb.dawn.birds 는 반복으로 튼다", "add": [{"id": "amb.dawn.birds", "loop": True}],
          "music": {"op": "play", "id": "bgm_s1_dawn", "fade": 6.0, "fallback": "silence"}},
    4.0: {"add": [{"id": "cut.straw.set", "delay": 2.0}]},
    16.0: {"add": [{"id": "sfx.step.dirt.1", "gain": 0.6}, {"id": "sfx.step.dirt.2", "delay": 0.55, "gain": 0.6}, {"id": "sfx.step.dirt.3", "delay": 1.1, "gain": 0.5}]},
    24.0: {"add": ["cut.straw.set"], "note": "A판(고쳐 놓음)일 때만. B판은 소리 없음"},
    34.0: {"music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    44.0: {"add": [{"stop": "amb.dawn.birds", "fade": 2.0}], "music": {"op": "silence", "fade": 3.0},
           "note": "대본: '소리는 빼고 바람만' — 나룻불이 꺼지는 소리를 일부러 만들지 않는다. 34.0의 바람 한 줄기 꼬리만 남는다"},
    58.0: {"add": [{"id": "cut.brush.stroke", "gain": 0.6}]},                                       # 먹지기 쪽지
    68.0: {"music": {"op": "play", "id": "bgm_s1_credits", "fade": 3.0, "fallback": "silence"}},
    80.0: {"note": "크레딧이 이어 틀거나, 대기 화면이면 6초에 걸쳐 끈다"}}

SILENT_BY_DESIGN = (
    "아래 박자는 일부러 소리를 안 얹었다: 입 모양만 움직이는 박자(B05·B07 INTRO, B10-TENDO 1.5 이름 부르기), "
    "고개를 돌리고 마주 보는 박자(B09-TENDO 1.5·3.5, B11-AFTER 2.0), 빛나지 않는 마지막 조각(B11-TENDO 3.5), "
    "비워 둔 마지막 줄(B12-P2 1.5), 무릎 컷의 0.4·1.5(처결 고르는 시간 — finish 종 꼬리만), "
    "B12-P3 2.0(흑월의 파혼은 전투 쪽 소리가 낸다). 소리가 없어야 그 순간이 무겁다")

MUSIC_FILES = {
    "_설명": "시즌1 끝 컷에서 부를 곡(아직 없음 — 오너 Gemini 지시문 21~25). 없으면 fallback. 파일이 생기면 Resources/Audio/BGM/<id>",
    "bgm_s1_heukwol": "21 흑월 결전(성문 밖 눈밭, 전투)",
    "bgm_s1_finale_a": "22 천도 A판 — 큰물 밤의 기억(가장 중요한 곡)",
    "bgm_s1_finale_b": "23 파혼 B판 — 빈 눈밭",
    "bgm_s1_dawn": "24 시즌1 마지막 새벽(서낭당)",
    "bgm_s1_credits": "25 끝 글씨·크레딧"}


def ids_in(v):
    for a in v.get("add", []):
        if isinstance(a, str): yield a
        elif "id" in a: yield a["id"]
    yield from v.get("replace", {}).values()


def main():
    made = {s["id"] for s in json.load(open(os.path.join(ROOT, "data/sfx_files.json"), encoding="utf-8"))["sounds"]}
    bad = sorted({i for c in CUTS.values() for v in c.values() for i in ids_in(v) if i not in made})
    if bad: sys.exit("없는 소리: " + ", ".join(bad))
    if len(sys.argv) > 1:                                   # 대본과 맞춰 보기
        src = {c["id"]: {float(s["t"]) for s in c["steps"]} for c in json.load(open(sys.argv[1], encoding="utf-8"))["cutscenes"]}
        miss = [(k, t) for k, c in CUTS.items() for t in c if k not in src or t not in src[k]]
        if miss: sys.exit("대본에 없는 박자: " + str(miss))
        print("대본 박자 모두 맞음:", len(src), "컷")
    data = {"_설명": __doc__.strip().split("\n\n")[0] + " — 생성: tools/cutscene_audio_s1.py",
            "music_files": MUSIC_FILES, "silent_by_design": SILENT_BY_DESIGN,
            "cuts": {k: {f"{t:.1f}": v for t, v in sorted(c.items())} for k, c in CUTS.items()}}
    with open(os.path.join(ROOT, "data/cutscene_audio_s1.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(len(CUTS), "컷,", sum(len(c) for c in CUTS.values()), "박자에 소리·음악 지시")


if __name__ == "__main__":
    main()
