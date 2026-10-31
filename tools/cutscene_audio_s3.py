# -*- coding: utf-8 -*-
"""
시즌3 컷신 89컷(docs/narrative/cutscenes_s3.json)의 '소리 대본' 덧칠표 (기획·사운드, 2026-10-25 밤)

모양은 시즌1·2(tools/cutscene_audio_s1.py · _s2.py)와 같다. 대본은 서사팀 파일이라 고치지 않고,
(컷 id, 박자 시각 t)를 열쇠로 '여기에 소리를 더 얹어라 / 바꿔라 / 음악을 이렇게 해라'만 적는다.
대본의 sfx_request(새 소리 26개)는 sfx_render.py 에 만들어 두었고, 서사가 sfx 로 옮긴다(sfx_map.promote).

시즌3에서 지킨 것:
  - 백(몸)은 보스여도 '혼'이 아니다. 그래서 시즌1 소리를 백 판으로 바꾼다.
      sfx.kneel → sfx.baek.kneel(젖은 흙 무릎) · sfx.pahon.burst → sfx.baek.break(흙·물째 터짐)
      저편 나룻불의 cut.lantern.light → sfx.farlight.on(아주 먼 불 + 여린 화음 = 시즌3 진행 소리)
  - 아래층 장면에 대본이 임시로 적은 위층 소리(amb.river.mist · amb.sea.wind · amb.mine.shaft)는 그 구역 아래층 환경음으로 바꿨다.
  - 새소리(amb.dawn.birds)는 솔고개 새벽(C-23A/B · C-31A/B)에만 있다. 이승 위층이라 그대로 둔다.
  - 입 모양 박자(칠성의 셈 B25-LAY 4.8 · 사공의 부름 B30-LAY 4.8 · 당할미 B-31B 70.0)에는 아무것도 얹지 않는다. 음악도 내린다.
  - 보스 곡: B-23 매듭 · B-27 이명 · B-31 나의 백은 전용 곡(bgm_s3_*)을 play 한다. 없으면 지역 combat.

실행:  python3 tools/cutscene_audio_s3.py            → data/cutscene_audio_s3.json
       python3 tools/cutscene_audio_s3.py 대본.json  → 모든 열쇠가 대본에 있는지·소리 id가 다 있는지 검사도 함
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DUCK_IN = {"op": "duck", "to": 0.35, "fade": 0.8}           # 등장 컷: 지역 음악을 낮춘다(보스가 먼저 보이게)
TO_COMBAT = {"op": "layer", "id": "combat", "fade": 1.0}     # 등장 컷 끝 = 보스전 시작
LAY_IN = {"op": "silence", "fade": 0.4}                      # 눕히기: 음악을 비워 명부·흙 소리만
BREAK_IN = {"op": "silence", "fade": 0.1}                    # 깨뜨리기: 폭발과 함께 뚝
RESUME_SLOW = {"op": "resume", "fade": 3.0}
RESUME = {"op": "resume", "fade": 2.0}
MID_DUCK = {"op": "duck", "to": 0.5, "fade": 0.4}            # 보스전 도중 맺힘 컷(층은 그대로)
MID_BACK = {"op": "duck", "to": 1.0, "fade": 1.0}
BAEK = {"sfx.kneel": "sfx.baek.kneel", "sfx.pahon.burst": "sfx.baek.break"}
FAR = {"cut.lantern.light": "sfx.farlight.on"}


def cut(d, t, **kv):
    for k, v in kv.items():
        if k in ("add",) and k in d.setdefault(t, {}): d[t][k] += v
        elif k == "replace" and k in d.setdefault(t, {}): d[t][k].update(v)
        else: d.setdefault(t, {})[k] = v


def boss(code, intro_len, lay_len, light_t, below=None, below_t=0.0, swap=None, song=None, intro=None, lay=None, brk=None, kneel=None, mids=None, nocond=False, brk_len=2.5):
    """보스 한 명의 컷들. 대본에 있는 박자에만 얹는다"""
    out = {}
    i = out[code + "-INTRO"] = {0.0: {"music": DUCK_IN}}
    if below:   # 아래층 구역 환경음을 깔아 둔다(보스전 내내 — ZoneAmbient 가 이어 받는다)
        cut(i, below_t, add=[{"id": below, "loop": True, "gain": 0.8}])
        if swap: cut(i, below_t, replace={swap: below})
    cut(i, intro_len, music=({"op": "play", "id": song, "fade": 1.0, "fallback": "combat"} if song else TO_COMBAT))
    for t, v in (intro or {}).items(): cut(i, t, **v)
    k = out[code + "-KNEEL"] = {0.0: {"music": {"op": "layer", "id": "finish", "fade": 0.3}, "replace": {"sfx.kneel": "sfx.baek.kneel"}}}
    for t, v in (kneel or {}).items(): cut(k, t, **v)
    if nocond: out[code + "-NOCOND"] = {0.0: {"music": {"op": "duck", "to": 0.6, "fade": 0.3}}}
    if lay_len:
        L = out[code + "-LAY"] = {0.0: {"music": LAY_IN}, light_t: {"replace": dict(FAR)}, lay_len: {"music": RESUME_SLOW}}
        for t, v in (lay or {}).items(): cut(L, t, **v)
        B = out[code + "-BREAK"] = {0.0: {"music": BREAK_IN, "replace": {"sfx.pahon.burst": "sfx.baek.break"}}, brk_len: {"music": RESUME}}
        for t, v in (brk or {}).items(): cut(B, t, **v)
    for name, (length, adds) in (mids or {}).items():      # 보스전 도중 맺힘 컷
        m = out[code + "-" + name] = {0.0: {"music": MID_DUCK}, length: {"music": MID_BACK}}
        for t, v in adds.items(): cut(m, t, **v)
    return out


CUTS = {}

# ---- 여는 장면 · 요약 ----
CUTS["C-21"] = {
    0.0: {"add": [{"id": "amb.river.mist", "loop": True}], "music": {"op": "play", "id": "bgm_s3_open", "fade": 3.0, "fallback": "silence"},
          "note": "대본의 강 소리 한 번에 더해 반복으로 깔아 둔다(16.0에서 물속으로 바뀜)"},
    8.0: {"add": [{"id": "amb.thread.hum", "loop": True, "gain": 0.5}], "note": "카메라가 발목까지 내려가면 실이 처음 '들린다'"},
    16.0: {"add": [{"stop": "amb.river.mist", "fade": 1.5}, {"id": "amb.underwater.low", "loop": True}], "music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    28.0: {"add": [{"stop": "amb.underwater.low", "fade": 1.0}, {"stop": "amb.thread.hum", "fade": 1.0}, {"id": "sfx.water.drain", "gain": 0.6}],
           "music": {"op": "duck", "to": 0.8, "fade": 2.0}, "note": "해 질 녘 물 빠짐 = 게임 중 sfx.water.drain 과 같은 소리를 함께(플레이어가 귀로 배워 둠)"},
    38.0: {"add": [{"id": "amb.below.dambed", "loop": True, "gain": 0.8}]},
    48.0: {"music": {"op": "duck", "to": 0.4, "fade": 1.5}, "note": "열한 몸·빈 오른팔: 설명 대신 음악을 낮춘다"},
    56.0: {"music": {"op": "duck", "to": 0.8, "fade": 1.0}},
    62.0: {"add": ["sfx.keeper.note"]},
    70.0: {"add": [{"stop": "amb.below.dambed", "fade": 2.0}], "music": RESUME_SLOW}}
CUTS["C-21S"] = {
    0.0: {"music": {"op": "play", "id": "bgm_s1_dawn", "fade": 2.0, "fallback": "silence"}},
    30.0: {"add": [{"id": "amb.styx.ferry", "loop": True, "gain": 0.6}]},
    45.0: {"add": [{"stop": "amb.styx.ferry", "fade": 2.0}, {"id": "amb.thread.hum", "loop": True, "gain": 0.5}], "music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    60.0: {"add": [{"stop": "amb.thread.hum", "fade": 2.0}], "music": RESUME_SLOW}}

# ---- 물 주기 · 공통 틀 ----
CUTS["S3-DUSK"] = {0.0: {"add": [{"id": "sfx.water.drain", "gain": 0.7}], "note": "대본의 cut.water.recede(짧게) 위에 게임 중 물 빠짐 소리 첫머리를 겹친다"}}
CUTS["S3-DAWN-WARN"] = {0.0: {"add": ["sfx.water.warn"], "music": {"op": "duck", "to": 0.7, "fade": 0.5},
                              "note": "천도·눕히기 중에도 들리는 경고(bypass). 2분 차오름은 이 뒤에 amb.water.rising + bgm_s3_rising 을 코드가 깐다"},
                        2.0: {"music": {"op": "duck", "to": 1.0, "fade": 2.0}}}
CUTS["S3-DAWN-PUSH"] = {0.0: {"add": [{"stop": "amb.water.rising", "fade": 1.0}, "sfx.flood.pushup"], "music": {"op": "duck", "to": 0.4, "fade": 0.3}},
                        3.0: {"music": RESUME, "note": "벌 없음: 위층 곡으로 부드럽게 돌아온다"}}
CUTS["RITE-REVERSE"] = {0.0: {"music": {"op": "duck", "to": 0.4, "fade": 1.0}}, 16.0: {"music": {"op": "duck", "to": 0.2, "fade": 2.0}, "note": "#1 빈 것 — 단서는 비어 있음으로 들린다"},
                        24.0: {"music": RESUME_SLOW}}
CUTS["LEDGER-REVERSE"] = {0.0: {"music": {"op": "duck", "to": 0.4, "fade": 1.0}}, 12.0: {"music": {"op": "duck", "to": 0.2, "fade": 1.5}}, 16.0: {"music": RESUME_SLOW}}
CUTS["BAEK-LAY"] = {0.0: {"music": {"op": "duck", "to": 0.5, "fade": 0.3}, "add": [{"stop": "amb.thread.hum", "fade": 0.5}]},
                    0.6: {"add": [{"id": "sfx.baek.laydown", "delay": 1.4}], "note": "몸이 다 누운 뒤 완료음(흙이 숨 내쉼 + 방울)"},
                    3.0: {"music": RESUME}}
CUTS["BAEK-BREAK"] = {0.0: {"replace": {"sfx.pahon.burst": "sfx.baek.break"}, "add": [{"stop": "amb.thread.hum", "fade": 0.1}, {"id": "cut.bones.crumble", "delay": 0.1, "gain": 0.7}]}}
CUTS["STEP-ASIDE"] = {0.0: {"add": ["sfx.baek.stepaside"], "note": "대본 요청 cut.soil.shift(가까이) 위에 게임 중 비켜섬 소리"}}
CUTS["OWNERLESS"] = {0.0: {"add": [{"id": "cut.seal.fade", "gain": 0.5}]}}
CUTS["THREAD-RISE"] = {0.0: {"music": {"op": "duck", "to": 0.6, "fade": 0.5}}, 3.0: {"music": RESUME}}
CUTS["FAR-LIGHT-FIRST"] = {0.0: {"replace": dict(FAR), "music": {"op": "duck", "to": 0.4, "fade": 1.5}},
                           6.0: {"music": {"op": "duck", "to": 0.25, "fade": 1.0}, "note": "당할미는 말하지 않는다 — 음악만 더 내린다"},
                           12.0: {"music": RESUME_SLOW}}

# ---- 6막 ① ⑤ ⑦ ----
CUTS.update(boss("B21", 4.5, 11.0, 8.0, brk_len=3.2, below="amb.below.poolbed", swap="amb.river.mist", mids={"FLOOD": (3.0, {0.0: {"add": [{"id": "sfx.boss.yun.waist", "delay": 0.8, "gain": 0.6}]}})},
                 lay={6.5: {"add": [{"id": "sfx.baek.laydown", "delay": 1.0}]}}))
CUTS.update(boss("B22", 4.5, 13.0, 10.0, below="amb.below.wreckbed", swap="amb.sea.wind", mids={"SEVEN": (2.5, {})},
                 lay={8.0: {"add": [{"id": "sfx.baek.laydown", "delay": 1.0}]}}, kneel={0.0: {"replace": {"sfx.kneel": "sfx.boss.seven.kneel"}}}))
CUTS.update(boss("B23", 5.5, None, 0.0, below="amb.below.knotdeep", swap="amb.river.mist", song="bgm_s3_knot", nocond=True,
                 mids={"TIGHTEN": (2.5, {0.0: {"add": [{"id": "sfx.boss.knot.tighten.telegraph", "gain": 0.7}]}}),
                       "BOAT": (3.0, {0.0: {"add": ["sfx.boss.knot.snag"]}})}))
CUTS["C-23A"] = {
    0.0: {"add": [{"stop": "amb.below.knotdeep", "fade": 3.0}], "music": {"op": "play", "id": "bgm_s1_dawn", "fade": 4.0, "fallback": "silence"},
          "note": "(재사용) 첫 배가 닿는 새벽 — 시즌1 끝 새벽 곡. 매듭 실이 감겨 올라가는 소리 뒤로 천천히"},
    10.0: {"add": [{"id": "sfx.styx.line.step", "repeat": 3, "every": 2.0, "gain": 0.6}], "note": "줄 전체가 움직인다(시즌2 장치음 재사용)"},
    22.0: {"add": [{"id": "amb.river.mist", "loop": True, "gain": 0.7}]},
    38.0: {"add": [{"id": "sfx.farlight.on", "delay": 1.5, "repeat": 4, "every": 1.2, "gain": 0.7}], "note": "불빛이 줄지어 켜진다"},
    56.0: {"add": [{"stop": "amb.river.mist", "fade": 3.0}], "music": {"op": "duck", "to": 0.6, "fade": 2.0}},
    64.0: {"music": {"op": "duck", "to": 0.35, "fade": 2.0}, "note": "짚신을 고쳐 놓지 않는다 — 소리 없이"},
    72.0: {"add": ["sfx.keeper.note"]},
    84.0: {"music": {"op": "silence", "fade": 5.0}}, 90.0: {"music": RESUME_SLOW}}
CUTS["C-23B"] = {
    0.0: {"replace": {"sfx.pahon.burst": "sfx.baek.break"}, "add": [{"stop": "amb.below.knotdeep", "fade": 0.5}], "music": {"op": "silence", "fade": 0.1}},
    6.0: {"add": [{"id": "cut.soul.rise", "repeat": 3, "every": 1.5, "gain": 0.4}]},
    18.0: {"add": [{"id": "amb.river.mist", "loop": True, "gain": 0.6}], "music": {"op": "play", "id": "bgm_s2_finale_b", "fade": 4.0, "fallback": "silence"},
           "note": "(재사용) 빈 기슭 곡 — 닿긴 하지만 군데군데 비어 있음"},
    36.0: {"add": [{"id": "sfx.farlight.on", "delay": 1.5, "repeat": 2, "every": 2.4, "gain": 0.6}], "note": "켜지는 불이 드문드문"},
    50.0: {"add": [{"stop": "amb.river.mist", "fade": 3.0}]},
    62.0: {"add": ["sfx.keeper.note"]},
    80.0: {"music": {"op": "silence", "fade": 5.0}}, 90.0: {"music": RESUME_SLOW}}

# ---- 7막 ③ ④ ② ⑥ ----
CUTS["C-24"] = {
    0.0: {"music": {"op": "play", "id": "bgm_below_earth_night", "fade": 3.0, "fallback": "silence"}},
    8.0: {"add": [{"stop": "amb.wind.dry", "fade": 2.0}, {"id": "amb.below.tombpit", "loop": True}], "music": {"op": "duck", "to": 0.6, "fade": 2.0}},
    24.0: {"music": {"op": "duck", "to": 0.3, "fade": 1.0}, "note": "땅속 북이 들리게 음악을 비킨다"},
    36.0: {"music": {"op": "duck", "to": 0.7, "fade": 2.0}},
    48.0: {"add": [{"stop": "amb.below.tombpit", "fade": 3.0}]},
    60.0: {"music": RESUME_SLOW}}
CUTS.update(boss("B24", 4.5, 12.0, 10.0, brk_len=3.2, below="amb.below.tombpit", mids={"MASS": (3.0, {0.0: {"add": [{"id": "sfx.boss.armies.charge", "gain": 0.6}]}})},
                 lay={9.0: {"add": [{"id": "sfx.baek.laydown", "delay": 0.5}]}}))
CUTS.update(boss("B25", 4.5, 13.0, 11.0, below="amb.below.sealedface", swap="amb.mine.shaft", mids={"PROP": (3.0, {0.0: {"add": ["sfx.boss.chilseong.collapse.telegraph"]}})},
                 lay={4.8: {"music": {"op": "silence", "fade": 0.3}, "note": "입 모양만 — 소리 없음"}, 9.0: {"add": [{"id": "sfx.boss.chilseong.count", "gain": 0.6}, {"id": "sfx.baek.laydown", "delay": 1.6}]}},
                 kneel={0.0: {"note": "입 모양 '열둘' — 소리 없이"}}))
CUTS.update(boss("B26", 4.5, 11.0, 9.0, below="amb.below.limepit", mids={"SPLIT": (3.0, {0.0: {"add": [{"id": "sfx.boss.plague.fall", "delay": 0.6, "gain": 0.7}]}})},
                 lay={8.5: {"add": ["sfx.baek.laydown"]}}, kneel={0.0: {"add": [{"id": "sfx.boss.plague.stones", "gain": 0.6}]}}))
CUTS.update(boss("B27", 4.5, 13.0, 11.0, below="amb.below.gatepit", song="bgm_s3_imyeong",
                 mids={"GATE": (3.0, {0.0: {"add": [{"id": "sfx.boss.imyeong.gate", "loop": True, "delay": 2.0, "gain": 0.6}],
                                            "note": "닫히는 소리 뒤로 성문 끄응을 반복으로 남긴다(게임 중 남은 시간에 따라 코드가 키움)"}})},
                 lay={0.0: {"add": [{"stop": "sfx.boss.imyeong.gate", "fade": 1.0}]}, 10.0: {"add": ["sfx.baek.laydown"]}},
                 brk={0.0: {"add": [{"stop": "sfx.boss.imyeong.gate", "fade": 0.1}]}}))
CUTS["C-27A"] = {
    0.0: {"music": {"op": "play", "id": "bgm_below_earth_finish", "fade": 0.5, "fallback": "silence"}, "note": "짧은 처결 곡 뒤로 바람만"},
    20.0: {"music": {"op": "silence", "fade": 1.0}},
    28.0: {"add": [{"id": "cut.chain.drag", "repeat": 2, "every": 6.0, "gain": 0.5}], "music": {"op": "play", "id": "bgm_s3_mybaek", "fade": 6.0, "fallback": "silence"},
           "note": "사슬 줄이 땅을 기어 물막이 골로 — 마지막 싸움 곡을 아주 작게 미리 들려 준다"},
    48.0: {"music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    60.0: {"add": [{"stop": "amb.underwater.low", "fade": 2.0}], "music": {"op": "duck", "to": 0.3, "fade": 2.0}},
    72.0: {"add": ["sfx.keeper.note"]},
    84.0: {"music": {"op": "silence", "fade": 5.0}}, 90.0: {"music": RESUME_SLOW}}
CUTS["C-27B"] = {
    0.0: {"music": {"op": "silence", "fade": 0.5}, "add": [{"id": "amb.wind.dry", "loop": True, "gain": 0.6}], "note": "빈 자리 — 음악 없이 바람만"},
    20.0: {"add": [{"stop": "amb.wind.dry", "fade": 3.0}]},
    28.0: {"add": [{"id": "cut.chain.drag", "repeat": 2, "every": 6.0, "gain": 0.5}], "music": {"op": "play", "id": "bgm_s3_mybaek", "fade": 6.0, "fallback": "silence"}},
    48.0: {"music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    60.0: {"add": [{"stop": "amb.underwater.low", "fade": 2.0}], "music": {"op": "duck", "to": 0.3, "fade": 2.0}},
    72.0: {"add": ["sfx.keeper.note"]},
    84.0: {"music": {"op": "silence", "fade": 5.0}}, 90.0: {"music": RESUME_SLOW}}

# ---- 8막 ⑧ ⑨ ⑩ · 최종 ----
CUTS["C-28"] = {
    0.0: {"music": {"op": "play", "id": "bgm_below_ink_night", "fade": 3.0, "fallback": "silence"}, "add": [{"id": "cut.chain.taut", "gain": 0.5}],
          "note": "사슬이 하류를 가리킴 — 당김 소리 하나"},
    8.0: {"add": [{"id": "amb.below.inksilt", "loop": True, "delay": 2.0}]},
    22.0: {"music": {"op": "duck", "to": 0.4, "fade": 2.0}},
    46.0: {"music": {"op": "duck", "to": 0.7, "fade": 2.0}, "note": "일꾼들이 고개를 든다 — 웅얼거림 없음(저승 규칙: 업과 상관없이 이 장면은 말 없음)"},
    60.0: {"add": [{"stop": "amb.below.inksilt", "fade": 3.0}], "music": RESUME_SLOW}}
CUTS.update(boss("B28", 4.5, 14.0, 12.0, below="amb.below.inksilt", mids={"DUST": (3.0, {0.0: {"add": [{"id": "sfx.boss.byeoru.inkrain", "gain": 0.5}]}})},
                 lay={10.0: {"add": ["sfx.baek.laydown"]}}))
CUTS.update(boss("B29", 4.5, 14.0, 12.0, below="amb.below.ondol", mids={"FLOOR": (2.5, {0.0: {"add": ["sfx.boss.halmi.ondol"]}})},
                 lay={7.0: {"add": ["sfx.baek.laydown"]}}, kneel={0.0: {"add": [{"id": "sfx.boss.halmi.shoes", "delay": 0.3, "gain": 0.8}]}}))
CUTS.update(boss("B30", 4.5, 17.0, 15.0, brk_len=3.2, below="amb.below.wellbottom", swap="amb.river.mist",
                 mids={"ROPE": (3.0, {0.0: {"add": [{"id": "sfx.boss.mother.rope.hold", "gain": 0.6}]}}),
                       "OAR": (4.0, {0.0: {"add": [{"id": "sfx.boss.mother.oar", "delay": 0.5}]}})},
                 lay={4.8: {"music": {"op": "silence", "fade": 0.3}, "note": "사공의 부름 — 입 모양만, 소리도 자막도 없음"},
                      8.0: {"add": [{"id": "sfx.boss.mother.shoe", "gain": 0.8}, {"id": "sfx.baek.laydown", "delay": 1.2}]}}))
CUTS["C-30"] = {
    0.0: {"add": [{"stop": "amb.below.wellbottom", "fade": 2.0}], "music": {"op": "duck", "to": 0.3, "fade": 2.0}},
    16.0: {"add": [{"stop": "amb.underwater.low", "fade": 2.0}], "music": {"op": "play", "id": "bgm_solgogae_night", "fade": 4.0, "fallback": "silence"},
           "note": "1막 첫 장면과 같은 자리 — 솔고개 곡이 돌아온다(처음과 끝은 같은 물)"},
    26.0: {"music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    40.0: {"music": RESUME_SLOW}}
CUTS["B31-INTRO"] = {0.0: {"music": {"op": "duck", "to": 0.3, "fade": 1.0}, "add": [{"id": "amb.below.pooldeep", "loop": True, "gain": 0.6}, {"id": "sfx.boss.mybaek.torch", "loop": True, "delay": 1.0}]},
                     6.0: {"music": {"op": "play", "id": "bgm_s3_mybaek", "fade": 1.5, "fallback": "combat"}}}
CUTS["B31-EIGHTH"] = {0.0: {"music": MID_DUCK, "add": [{"id": "sfx.boss.mybaek.child", "gain": 0.8}],
                            "note": "S-188 눕힘 판(보릿단만)에서도 같은 소리 — 실이 이미 끊겨 있으니 끝의 툭만 남는 셈"}, 4.0: {"music": MID_BACK}}
CUTS["B31-SEVEN"] = {0.0: {"music": MID_DUCK, "add": ["sfx.boss.mybaek.push", {"id": "sfx.boss.mybaek.lights", "delay": 0.8}]}, 5.0: {"music": MID_BACK}}
CUTS["B31-KNEEL"] = {0.0: {"music": {"op": "silence", "fade": 1.0}, "replace": {"sfx.kneel": "sfx.boss.mybaek.tether"},
                           "add": [{"id": "sfx.boss.mybaek.finish", "delay": 0.8}],
                           "note": "백은 무릎 꿇지 않는다 → 무릎 소리 대신 사슬이 팽. 처결 대기 15초 = 마무리 15초 소리(물속이 걷힘)"}}
CUTS["B31-NOCOND"] = {0.0: {"add": [{"id": "cut.seal.fade", "gain": 0.6}]}}
CUTS["C-31A"] = {
    0.0: {"add": [{"stop": "sfx.boss.mybaek.torch", "fade": 2.0}, {"stop": "amb.below.pooldeep", "fade": 4.0}], "music": {"op": "silence", "fade": 0.5}},
    6.0: {"add": [{"id": "sfx.baek.laydown", "delay": 1.2}]},
    14.0: {"music": {"op": "play", "id": "bgm_s3_end_a", "fade": 4.0, "fallback": "silence"}},
    70.0: {"music": {"op": "duck", "to": 0.5, "fade": 2.0}},
    78.0: {"music": {"op": "duck", "to": 0.15, "fade": 1.5}, "note": "부름(사람 목소리 첫 줄) — 음악을 거의 비운다"},
    90.0: {"music": {"op": "duck", "to": 0.8, "fade": 3.0}},
    100.0: {"music": {"op": "duck", "to": 0.15, "fade": 1.5}, "note": "대답 — 차사의 목소리"},
    116.0: {"music": {"op": "duck", "to": 0.8, "fade": 3.0}},
    140.0: {"music": {"op": "duck", "to": 0.4, "fade": 2.0}},
    152.0: {"music": {"op": "duck", "to": 0.2, "fade": 2.0}, "note": "선택 — 입력 기다리는 동안 시간이 멈춘다. 음악은 작게 계속"},
    160.0: {"music": {"op": "duck", "to": 0.9, "fade": 3.0}},
    225.0: {"music": {"op": "silence", "fade": 8.0}, "note": "크레딧은 bgm_s1_credits 를 이어 틀 것(크레딧 화면 쪽)"}}
CUTS["C-31B"] = {
    0.0: {"add": [{"stop": "sfx.boss.mybaek.torch", "fade": 1.0}, {"stop": "amb.below.pooldeep", "fade": 4.0}, {"id": "sfx.baek.laydown", "delay": 3.0}],
          "music": {"op": "silence", "fade": 0.5}},
    14.0: {"music": {"op": "play", "id": "bgm_s3_end_b", "fade": 4.0, "fallback": "silence"}},
    70.0: {"music": {"op": "duck", "to": 0.3, "fade": 2.0}, "note": "입술만 움직인다 — 소리 없음"},
    96.0: {"music": {"op": "duck", "to": 0.15, "fade": 1.5}, "note": "한 줄(당할미 목소리)"},
    110.0: {"music": {"op": "duck", "to": 0.8, "fade": 3.0}},
    122.0: {"add": ["sfx.keeper.note"]},
    136.0: {"add": [{"id": "cut.chain.taut", "gain": 0.4}], "note": "풀리지 않고 가벼워질 뿐 — 아주 작은 당김"},
    165.0: {"music": {"op": "silence", "fade": 6.0}}, 180.0: {"music": RESUME_SLOW}}
CUTS["C-31C"] = {
    0.0: {"replace": {"sfx.pahon.burst": "sfx.baek.break"}, "add": [{"stop": "sfx.boss.mybaek.torch", "fade": 0.1}, {"id": "cut.bones.crumble", "delay": 0.1, "gain": 0.7}],
          "music": {"op": "silence", "fade": 0.1}},
    10.0: {"add": [{"id": "cut.water.rise", "gain": 0.6}, {"id": "amb.below.pooldeep", "loop": True, "delay": 2.0, "gain": 0.5}],
           "music": {"op": "play", "id": "bgm_s3_end_c", "fade": 4.0, "fallback": "silence"}},
    24.0: {"add": [{"stop": "amb.below.pooldeep", "fade": 4.0}]},
    40.0: {"add": ["sfx.keeper.note"]},
    96.0: {"add": [{"id": "sfx.pahon.burst", "delay": 1.0, "repeat": 3, "every": 1.6, "gain": 0.15}],
           "note": "아주 먼 들판의 깨뜨림 셋 — 시즌1 파혼 소리 그대로, 아주 작게(그것이 나였다)"},
    110.0: {"music": {"op": "silence", "fade": 6.0}}, 120.0: {"music": RESUME_SLOW}}
CUTS["S3-HALMI-TABLE"] = {0.0: {"music": {"op": "duck", "to": 0.6, "fade": 1.0}, "add": [{"id": "sfx.boss.halmi.table", "delay": 2.0, "gain": 0.6}],
                                "note": "B-29 상 차림과 같은 소리 — 그때 귀로도 알아보게"}, 10.0: {"music": RESUME}}

SILENT_BY_DESIGN = (
    "일부러 소리를 안 얹은 박자: 입 모양(칠성의 셈 B25-KNEEL·B25-LAY 4.8, 사공의 부름 B30-LAY 4.8, 당할미 C-31B 70.0), "
    "당할미가 보기만 하는 박자(FAR-LIGHT-FIRST 6.0, C-23A 64.0, C-27A 60.0), 열한 몸의 빈 오른팔(C-21 48.0), "
    "무릎 컷의 0.4·1.5(처결 고르는 시간), 거꾸로 장례의 {empty}. 백은 말하지 않는다 — 소리가 비어야 그게 들린다")

MUSIC_FILES = {
    "_설명": "시즌3 컷에서 부를 곡. 없으면 Temp 임시 대역 → 그것도 없으면 fallback. 파일은 Resources/Audio/BGM/<id>",
    "bgm_s3_open": "62 시즌3 여는 장면(C-21)",
    "bgm_s3_knot": "56 B-23 매듭", "bgm_s3_imyeong": "57 B-27 이명", "bgm_s3_mybaek": "58 B-31 나의 백(C-27A/B 28초에 미리 작게)",
    "bgm_s3_end_a": "59 결말 A", "bgm_s3_end_b": "60 결말 B", "bgm_s3_end_c": "61 결말 C",
    "bgm_below_earth_night": "49 (C-24)", "bgm_below_earth_finish": "51 (C-27A 첫머리)", "bgm_below_ink_night": "52 (C-28)",
    "bgm_s1_dawn": "(재사용) C-21S 요약 · C-23A 첫 배가 닿음", "bgm_s2_finale_b": "(재사용) C-23B 빈 기슭",
    "bgm_solgogae_night": "(재사용) C-30 처음과 같은 물"}


def ids_in(v):
    for a in v.get("add", []):
        if isinstance(a, str): yield a
        elif "id" in a: yield a["id"]
    yield from v.get("replace", {}).values()


def main():
    made = {s["id"] for s in json.load(open(os.path.join(ROOT, "data/sfx_files.json"), encoding="utf-8"))["sounds"]}
    bad = sorted({i for c in CUTS.values() for v in c.values() for i in ids_in(v) if i not in made})
    if bad: sys.exit("없는 소리: " + ", ".join(bad))
    temp = set(json.load(open(os.path.join(ROOT, "data/bgm_temp.json"), encoding="utf-8"))["clips"]) | {"bgm_solgogae_night"}
    nomus = sorted({v["music"]["id"] for c in CUTS.values() for v in c.values() if v.get("music", {}).get("op") == "play" and v["music"]["id"] not in temp})
    if nomus: sys.exit("없는 곡: " + ", ".join(nomus))
    if len(sys.argv) > 1:                                   # 대본과 맞춰 보기
        cs = json.load(open(sys.argv[1], encoding="utf-8"))["cutscenes"]
        src = {c["id"]: {float(s["t"]) for s in c["steps"]} for c in cs}
        miss = [(k, t) for k, c in CUTS.items() for t in c if k not in src or t not in src[k]]
        if miss: sys.exit("대본에 없는 박자: " + str(miss))
        # replace 의 '바꿀 대상'이 그 박자의 sfx 에 정말 있는지
        sfx_at = {(c["id"], float(s["t"])): set(s.get("sfx", [])) for c in cs for s in c["steps"]}
        wrong = [(k, t, a) for k, c in CUTS.items() for t, v in c.items() for a in v.get("replace", {}) if a not in sfx_at.get((k, t), set())]
        if wrong: print("참고 — 그 박자에 없는 바꾸기 대상(무시됨):", wrong)
        print("대본 박자 모두 맞음:", len(src), "컷 중", len(CUTS), "컷에 지시")
    data = {"_설명": __doc__.strip().split("\n\n")[0] + " — 생성: tools/cutscene_audio_s3.py",
            "music_files": MUSIC_FILES, "silent_by_design": SILENT_BY_DESIGN,
            "cuts": {k: {f"{t:.1f}": v for t, v in sorted(c.items())} for k, c in CUTS.items()}}
    with open(os.path.join(ROOT, "data/cutscene_audio_s3.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(len(CUTS), "컷,", sum(len(c) for c in CUTS.values()), "박자에 소리·음악 지시")


if __name__ == "__main__":
    main()
