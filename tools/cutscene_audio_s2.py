# -*- coding: utf-8 -*-
"""
시즌2 컷신 54컷(docs/narrative/cutscenes_s2.json)의 '소리 대본' 덧칠표 (기획·사운드, 2026-10-25)

시즌1(tools/cutscene_audio_s1.py)과 모양이 같다. 대본은 서사팀 파일이라 직접 고치지 않고,
(컷 id, 박자 시각 t)를 열쇠로 '여기에 소리를 더 얹어라 / 바꿔라 / 음악을 이렇게 해라'만 적는다.

시즌2(저승)에서 지킨 것:
  - 산 것의 소리 없음. 대본의 amb.dawn.birds(C-18 40.0 ⑨의 첫 새벽)는 amb.dawn.still로 바꿨다.
    ⑨에 새벽이 '와도' 새는 없다. 서사가 새를 꼭 원하면 replace 한 줄만 지우면 된다.
  - 광산 소리(amb.mine.*)로 임시로 적힌 자리는 저승 환경음(amb.inkroom·amb.sealcave)으로 바꿨다.
  - 말 없는 박자(입 모양만, 오래 바라봄, "3초 그대로")에는 일부러 아무것도 얹지 않았다. 음악도 내려서 침묵을 들리게 한다.

실행:  python3 tools/cutscene_audio_s2.py            → data/cutscene_audio_s2.json
       python3 tools/cutscene_audio_s2.py 대본.json  → 모든 열쇠가 대본에 있는지·소리 id가 다 있는지 검사도 함

항목 모양은 시즌1과 같다. add 안의 항목은 아래 넷 중 하나다.
  "id"                      한 번 튼다
  {"id", "gain", "delay"}   크기와 시작 시각을 정해 튼다
  {"id", "repeat", "every"} 여러 번 튼다
  {"id", "loop": true}      반복해서 튼다. 끌 때는 {"stop": "id", "fade"}

replace와 music 쓰는 법도 시즌1과 같다.
  replace: {"대본 id": "바꿀 id"}
  music:   duck / silence / resume / layer / play

주의: music의 duck {"to": 1.0}은 '강제 층(전투)은 그대로 두고 크기만 원래대로' 돌리는 법이다.
보스전 도중의 맺힘 컷(BOAT·P30·GIFT·P2·P3)에서 resume을 쓰면 전투 층 강제가 풀리므로 이것을 쓴다.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DUCK_IN = {"op": "duck", "to": 0.35, "fade": 0.8}           # 등장 컷: 지역 음악을 낮춘다(보스가 먼저 보이게)
TO_COMBAT = {"op": "layer", "id": "combat", "fade": 1.0}     # 등장 컷 끝 = 보스전 시작
TENDO_IN = {"op": "silence", "fade": 0.4}                    # 천도: 음악을 비워 명부 소리만
PAHON_IN = {"op": "silence", "fade": 0.1}                    # 파혼: 폭발과 함께 뚝
RESUME_SLOW = {"op": "resume", "fade": 3.0}
RESUME = {"op": "resume", "fade": 2.0}
MID_DUCK = {"op": "duck", "to": 0.5, "fade": 0.4}            # 보스전 도중 맺힘 컷(층은 그대로)
MID_BACK = {"op": "duck", "to": 1.0, "fade": 1.0}


def cut(d, t, **kv):
    d.setdefault(t, {}).update(kv)


def boss(code, intro_len, intro=None, tendo=None, tendo_len=None, pahon=None, kneel=None, mids=None):
    """보스 한 명의 컷들. 대본에 있는 박자에만 얹는다(없는 컷은 만들지 않음)"""
    out = {}
    i = out[code + "-INTRO"] = {0.0: {"music": DUCK_IN}}
    cut(i, intro_len, music=TO_COMBAT)
    for t, v in (intro or {}).items(): i.setdefault(t, {}).update(v)
    out[code + "-KNEEL"] = {0.0: {"music": {"op": "layer", "id": "finish", "fade": 0.3}}}
    if kneel: out[code + "-KNEEL"][0.0].update(kneel)
    if tendo_len:
        td = out[code + "-TENDO"] = {0.0: {"music": TENDO_IN}, tendo_len: {"music": RESUME_SLOW}}
        for t, v in (tendo or {}).items(): td.setdefault(t, {}).update(v)
    pd = out[code + "-PAHON"] = {0.0: {"music": PAHON_IN}, 2.5: {"music": RESUME}}
    for t, v in (pahon or {}).items(): pd.setdefault(t, {}).update(v)
    for name, (length, adds) in (mids or {}).items():      # 보스전 도중 맺힘 컷
        m = out[code + "-" + name] = {0.0: {"music": MID_DUCK}, length: {"music": MID_BACK}}
        for t, v in adds.items(): m.setdefault(t, {}).update(v)
    return out


CUTS = {}

# ---- 시즌2 여는 장면 ----
CUTS["C-14"] = {
    0.0: {"add": [{"id": "amb.river.mist", "loop": True}], "music": {"op": "play", "id": "bgm_s2_open", "fade": 4.0, "fallback": "silence"},
          "note": "대본의 amb.river.mist 한 번에 더해 반복으로 깔아 둔다(30.0에서 끔)"},
    6.0: {"add": [{"id": "sfx.step.dirt.1", "repeat": 12, "every": 1.1, "gain": 0.35}, {"id": "sfx.step.dirt.2", "delay": 0.55, "repeat": 12, "every": 1.1, "gain": 0.35}],
          "note": "자동 걷기 발소리(작게). 물빛이 먹빛이 될수록 발소리 말고는 남는 게 없다"},
    20.0: {"add": [{"id": "cut.hull.creak", "delay": 1.6, "gain": 0.5}], "note": "천도판: 배를 하나 더 밟음. 파혼판(같은 t)에서도 판자 삐걱으로 들려 괜찮다"},
    30.0: {"add": [{"stop": "amb.river.mist", "fade": 4.0}], "music": {"op": "duck", "to": 0.5, "fade": 3.0}},   # 안개 속: 강 소리가 먹먹해지다 사라짐
    38.0: {"add": [{"id": "amb.styx.ferry", "loop": True, "gain": 0.8}], "note": "안개가 걷히며 줄의 웅얼거림이 들려온다(뜻 없음)"},
    50.0: {"music": {"op": "duck", "to": 0.7, "fade": 2.0}},
    58.0: {"add": ["sfx.keeper.note"]},
    60.0: {"add": [{"stop": "amb.styx.ferry", "fade": 3.0}], "music": RESUME_SLOW}}
CUTS["C-14S"] = {
    0.0: {"music": {"op": "play", "id": "bgm_s1_dawn", "fade": 2.0, "fallback": "silence"}, "note": "시즌1 마지막 새벽 곡을 요약에 다시 쓴다"},
    30.0: {"add": [{"id": "amb.snow.wind", "loop": True, "gain": 0.5}]},
    45.0: {"add": [{"stop": "amb.snow.wind", "fade": 2.0}]},
    60.0: {"music": {"op": "silence", "fade": 3.0}}}
CUTS["C-15"] = {
    0.0: {"music": {"op": "duck", "to": 0.5, "fade": 2.0}, "note": "걷기 가능 컷. 지역 환경음(amb.styx.ferry)은 ZoneAmbient가 이미 튼다 — 겹쳐 틀지 않는다"},
    10.0: {"add": [{"id": "cut.soul.brush", "repeat": 5, "every": 2.4, "gain": 0.4}], "note": "혼이 고개 숙일 때마다 옷깃 스침(아주 작게). 번진 먹 판에서는 비켜서는 소리로 들린다"},
    60.0: {"music": {"op": "duck", "to": 0.2, "fade": 2.0}, "note": "입술만 움직이는 혼 — 음악을 거의 비워 '소리 없음'이 들리게"},
    75.0: {"add": [{"id": "sfx.styx.boat.arrive", "gain": 0.6}], "music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    90.0: {"music": RESUME}}

# ---- 장례 변주(틀) ----
CUTS["RITE-BAEUNG"] = {0.0: {"music": {"op": "duck", "to": 0.3, "fade": 1.0}, "add": [{"id": "sfx.styx.boat.arrive", "gain": 0.7}]},
                       12.0: {"add": [{"id": "sfx.styx.line.step", "gain": 0.6}]},           # 줄이 한 칸 움직임
                       22.0: {"add": [{"id": "cut.oar.row", "gain": 0.6, "delay": 0.5}]},
                       30.0: {"music": RESUME_SLOW}}
CUTS["RITE-JEONGSEO"] = {0.0: {"music": {"op": "duck", "to": 0.3, "fade": 1.0}},
                         30.0: {"music": RESUME_SLOW}}
CUTS["RITE-JOIN"] = {0.0: {"music": {"op": "duck", "to": 0.3, "fade": 1.0}},
                     6.0: {"add": [{"id": "sfx.fragment.link", "delay": 0.3}]},              # 세 음이 한 화음으로
                     14.0: {"add": ["sfx.chain.unrust"]},
                     20.0: {"music": RESUME_SLOW}}

# ---- ⑦ 보스 ----
CUTS.update(boss("B13", 4.5,
    intro={0.0: {"replace": {"amb.river.mist": "sfx.styx.boat.arrive"}},                       # 강 배경은 지역음이 이미 깔림 → 배가 들어오는 소리로
           1.6: {"add": [{"id": "sfx.styx.line.step", "gain": 0.6, "delay": 0.4}]}},              # 몇 혼이 배에 오름
    tendo_len=9.5,
    tendo={7.0: {"add": [{"id": "sfx.styx.boat.arrive", "delay": 1.0, "gain": 0.6}, {"id": "sfx.styx.line.step", "delay": 1.8}]}},   # 두 번째 배 / 줄이 처음으로 한 칸
    pahon={0.0: {"add": [{"id": "cut.boat.break", "gain": 0.6}]}},                              # 말뚝이 부러짐(나무)
    mids={"BOAT": (3.0, {0.0: {"replace": {"cut.hull.creak": "sfx.styx.boat.arrive"}}})}))
CUTS.update(boss("B14", 4.0,
    intro={0.0: {"add": [{"id": "amb.names.many", "gain": 0.45}]}},                            # 덩어리의 얼굴들(한 번만, 14초 꼬리)
    pahon={0.8: {"add": [{"id": "sfx.name.slip.float", "delay": 0.4, "gain": 0.6}]},
           5.0: {"add": [{"id": "cut.color.shift", "gain": 0.5}], "note": "안개가 걷힘"}}))
CUTS["B14-PAHON"][6.0] = {"music": RESUME_SLOW}                                              # 이 컷은 6초(파혼만 있는 보스)
del CUTS["B14-PAHON"][2.5]

# ---- ⑧ 보스 ----
CUTS.update(boss("B15", 4.5,
    intro={1.8: {"add": [{"id": "cut.stroke.scatter", "gain": 0.4}]},                          # 적은 줄이 번져 사라짐
           3.2: {"add": [{"id": "cut.seal.set", "gain": 0.7}, {"id": "sfx.map.draw", "delay": 0.3, "gain": 0.6}]}},   # 도장 + 바닥이 칸으로 나뉨
    tendo_len=8.0,
    pahon={1.5: {"add": [{"id": "cut.tag.drop", "gain": 0.7}]}},                               # 번호 도장이 굴러 멈춤
    mids={"P30": (3.0, {0.0: {"add": [{"id": "cut.ledger.open", "gain": 0.6}]}})}))
CUTS.update(boss("B16", 4.5,
    intro={1.6: {"add": [{"id": "cut.names.glow", "gain": 0.5}]}},                             # 기억 줄들이 벼루 둘레를 돎
    tendo_len=8.5,
    tendo={5.5: {"add": [{"id": "cut.names.glow", "gain": 0.6}]}},
    pahon={1.5: {"add": [{"id": "cut.stone.crack", "gain": 0.5}]}}))
CUTS["C-16"] = {
    0.0: {"replace": {"amb.mine.wind": "amb.inkroom"}, "music": {"op": "silence", "fade": 2.0},
          "note": "대본 메모 '먹방 바람 대신 쓸 소리는 사운드팀 몫' → amb.inkroom(먹방). 음악 없이 방의 공기만"},
    46.0: {"add": ["sfx.keeper.note"]},
    70.0: {"add": [{"stop": "amb.inkroom", "fade": 3.0}], "music": {"op": "resume", "fade": 4.0},
           "note": "다음 쪽지가 오지 않는 침묵이 연출 — 음악도 천천히만 돌아온다"}}

# ---- ⑨ ----
CUTS["C-17"] = {
    0.0: {"add": [{"id": "amb.blank.market", "loop": True, "gain": 0.5}], "music": {"op": "silence", "fade": 2.0}},
    10.0: {"note": "10초 동안 아무것도 얹지 않는다(그가 나를 오래 본다)"},
    32.0: {"add": [{"id": "sfx.step.dirt.1", "gain": 0.35}, {"id": "sfx.step.dirt.2", "delay": 0.6, "gain": 0.28},
                   {"id": "sfx.step.dirt.3", "delay": 1.2, "gain": 0.2}, {"id": "sfx.step.dirt.1", "delay": 1.8, "gain": 0.12}]},   # 안개 속으로 멀어지는 걸음
    40.0: {"add": ["sfx.keeper.note"]},
    50.0: {"add": [{"stop": "amb.blank.market", "fade": 3.0}], "music": RESUME_SLOW}}
CUTS.update(boss("B17", 4.5,
    tendo_len=10.0,
    tendo={4.0: {"note": "대본: 3초 그대로, 소리 없음 — 아무것도 얹지 않는다"},
           7.0: {"add": [{"id": "sfx.map.draw", "gain": 0.7}]}},                               # 문 둘레가 기억 지도로
    pahon={0.8: {"add": [{"id": "cut.gate.creak", "gain": 0.6}]}, 1.5: {"add": [{"id": "cut.tag.drop", "gain": 0.8}]}}))   # 열린 문이 흔들림 / 육모방망이
CUTS.update(boss("B18", 4.5,
    intro={0.0: {"replace": {"amb.mine.shaft": "amb.sealcave"}},
           3.2: {"add": ["cut.seal.thud"]}},                                                   # 또 찍는다
    tendo_len=7.5,
    tendo={4.0: {"add": [{"id": "sfx.step.dirt.1", "gain": 0.3}, {"id": "sfx.step.dirt.2", "delay": 0.6, "gain": 0.3}]}},   # 먹지기가 굴 입구에
    pahon={0.8: {"add": [{"id": "cut.beads.scatter", "gain": 0.6}]}},                          # 인 조각들이 흩어짐
    mids={"GIFT": (3.0, {})}))
CUTS["B18-GIFT-TENDO"] = {0.0: {"music": TENDO_IN}, 8.0: {"music": RESUME_SLOW}}
CUTS["C-18"] = {
    0.0: {"music": {"op": "silence", "fade": 1.5}},
    40.0: {"replace": {"amb.dawn.birds": "amb.dawn.still"}, "add": [{"id": "cut.color.shift", "gain": 0.5}],
           "music": {"op": "play", "id": "bgm_s1_dawn", "fade": 6.0, "fallback": "silence"},
           "note": "저승엔 새가 없다 → 바람 없는 새벽. 처음 오는 새벽이라 시즌1 새벽 곡을 아주 천천히 들인다"},
    48.0: {"add": ["sfx.keeper.note"], "music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    60.0: {"music": {"op": "resume", "fade": 4.0}}}

# ---- ⑩ ----
CUTS.update(boss("B19", 4.5,
    intro={3.2: {"add": [{"id": "cut.straw.set", "gain": 0.6}]}},                              # 새끼줄을 듦
    tendo_len=9.5,
    tendo={1.8: {"add": [{"id": "cut.names.glow", "gain": 0.4}], "note": "깨뜨리지 않고 끝나는 새벽 — 작게"},
           4.5: {"add": [{"id": "sfx.chain.unrust", "delay": 0.5}]}},
    pahon={0.8: {"add": [{"id": "cut.salt.scatter", "gain": 0.5}]}, 1.5: {"add": [{"id": "cut.chain.drag", "gain": 0.5}]}},
    mids={"P30": (4.0, {0.8: {"music": {"op": "silence", "fade": 0.3}, "note": "시즌2 첫 대사 한 줄 — 음악을 비운다"}})}))
CUTS["B20-INTRO"] = {
    0.0: {"replace": {"amb.river.mist": "amb.bigdam"}, "music": {"op": "duck", "to": 0.2, "fade": 1.0}},
    3.0: {"note": "대본 요청 amb.names.many 는 반복으로 켠다(크기 = 물막이 눈금 + 시즌1 파혼 수 — 코드가 gain 을 곱할 것)",
          "add": [{"id": "amb.names.many", "loop": True}]},
    6.0: {"music": {"op": "play", "id": "bgm_s2_bigdam", "fade": 1.0, "fallback": "combat"}}}
CUTS["B20-P2"] = {0.0: {"music": MID_DUCK, "add": [{"id": "cut.names.glow", "gain": 0.5}]}, 6.0: {"music": MID_BACK}}
CUTS["B20-P3"] = {0.0: {"music": {"op": "duck", "to": 0.35, "fade": 0.5}, "add": [{"id": "cut.stone.crack", "gain": 0.6}]}, 6.0: {"music": MID_BACK}}
CUTS["B20-KNEEL"] = {0.0: {"music": {"op": "duck", "to": 0.3, "fade": 0.5}}}
CUTS["C-20A"] = {
    0.0: {"add": [{"stop": "amb.names.many", "fade": 3.0}], "music": {"op": "play", "id": "bgm_s2_finale_a", "fade": 3.0, "fallback": "silence"}},
    10.0: {"add": [{"id": "amb.river.mist", "loop": True, "delay": 6.0}], "note": "강이 흐르기 시작한 뒤로는 맑은 강 소리를 깐다"},
    22.0: {"add": [{"id": "sfx.styx.boat.arrive", "repeat": 3, "every": 2.5, "gain": 0.6}, {"id": "sfx.styx.line.step", "delay": 1.0, "gain": 0.6}]},   # 배가 두 척, 세 척 / 줄이 움직임
    44.0: {"note": "사공 입술만 — 어미의 이름은 소리로도 내지 않는다"},
    64.0: {"music": {"op": "silence", "fade": 0.5}, "add": [{"id": "sfx.styx.boat.arrive", "delay": 1.0, "gain": 0.5}],
           "note": "대본: 5초 그대로, 음악도 멈춘다"},
    76.0: {"music": {"op": "duck", "to": 0.5, "fade": 3.0}},
    88.0: {"add": [{"stop": "amb.river.mist", "fade": 8.0}], "music": {"op": "duck", "to": 0.3, "fade": 4.0}},
    100.0: {"music": {"op": "silence", "fade": 4.0}, "note": "크레딧이 이어 틀거나 대기 화면"}}
CUTS["C-20B"] = {
    0.0: {"add": [{"stop": "amb.names.many", "fade": 0.5}], "music": {"op": "silence", "fade": 0.1}},
    2.0: {"add": [{"id": "cut.river.rush", "delay": 7.7, "repeat": 1, "every": 7.7}], "note": "대본 한 번(7.7초) + 이어서 한 번 더 = 약 15초. 파일 끝과 처음이 이어지게 만들어 둠"},
    16.0: {"add": [{"id": "cut.soul.rise", "repeat": 3, "every": 1.4, "gain": 0.5}]},               # 흩어진 혼들이 다시 떠도는 혼으로
    34.0: {"add": [{"id": "cut.oar.row", "gain": 0.5}], "music": {"op": "play", "id": "bgm_s2_finale_b", "fade": 4.0, "fallback": "silence"}},
    46.0: {"add": [{"id": "sfx.styx.boat.arrive", "gain": 0.5}], "music": {"op": "duck", "to": 0.4, "fade": 2.0}},
    56.0: {"add": ["sfx.keeper.note"]},
    68.0: {"music": {"op": "duck", "to": 0.2, "fade": 3.0}},
    80.0: {"music": {"op": "silence", "fade": 4.0}}}

SILENT_BY_DESIGN = (
    "일부러 소리를 안 얹은 박자: 입 모양만 움직이는 박자(C-15 60.0, B15-TENDO 1.8, C-20A 44.0), 오래 바라보는 박자(C-17 10.0), "
    "'3초 그대로·소리 없음'(B17-TENDO 4.0), 우는 소리 없는 울음(B16-INTRO 3.6), 웃음(B16-TENDO 4.0), 장례 변주의 {stopped}·{moving} "
    "(기억 글이 말한다), 무릎 컷의 0.4·1.5(처결 고르는 시간). 저승은 나를 보지만 아무도 말을 걸지 않는다 — 소리가 비어야 그게 들린다")

MUSIC_FILES = {
    "_설명": "시즌2 컷에서 부를 곡(오너 Gemini 지시문 42~45 — 아직 없음). 없으면 Temp 임시 대역 → 그것도 없으면 fallback. 파일은 Resources/Audio/BGM/<id>",
    "bgm_s2_open": "42 시즌2 여는 장면 — 먹빛으로 검어지는 강, 끝없는 줄",
    "bgm_s2_bigdam": "43 물막이 바닥 결전(B-20) — 수천의 이름 덩어리",
    "bgm_s2_finale_a": "44 풀어내기판 — 강이 흐르고 배가 늘어남, 그러나 돌아옴",
    "bgm_s2_finale_b": "45 파혼판 — 사나운 강 뒤의 빈 기슭",
    "bgm_s1_dawn": "(재사용) C-14S 요약·C-18 ⑨의 첫 새벽"}


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
        print("대본 박자 모두 맞음:", len(src), "컷 중", len(CUTS), "컷에 지시")
    data = {"_설명": __doc__.strip().split("\n\n")[0] + " — 생성: tools/cutscene_audio_s2.py",
            "music_files": MUSIC_FILES, "silent_by_design": SILENT_BY_DESIGN,
            "cuts": {k: {f"{t:.1f}": v for t, v in sorted(c.items())} for k, c in CUTS.items()}}
    with open(os.path.join(ROOT, "data/cutscene_audio_s2.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(len(CUTS), "컷,", sum(len(c) for c in CUTS.values()), "박자에 소리·음악 지시")


if __name__ == "__main__":
    main()
