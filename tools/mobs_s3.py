# -*- coding: utf-8 -*-
"""
시즌 3 일반 적(백) 구성표 생성기 (기획서 부록 F-3의 단일 출처)

왜 이 파일이 있나:
  시즌 3의 상대는 혼이 아니라 장례를 못 치른 몸(백)이다(서사 ACT6~8).
  백은 혼처럼 '죽은 지 얼마나 됐나'로 나뉘지 않고, 대신
  "어떤 상처로 묻혔나(물 밑·한 구덩이·막힌 갱·번호·별명·저승 일꾼)"로 나뉜다.
  구역마다 "무엇이 몇 %로, 한 번에 몇, 언제 사나운 적이 나오나"를 한 표로 정해
  코드(스폰)·QA(시뮬)·서사(땅의 상처)가 같은 숫자를 보게 한다.

실행:
  python3 tools/mobs_s3.py [부록 마크다운을 쓸 폴더]
  → data/mobs_s3.json + <폴더>/appendix-F3.md

출처:
  - 구역·막·고리: tools/route_s3.py ZONES·RING_BY_ACT (같은 표를 그대로 가져온다)
  - 구역마다 "주로 나오는 백"과 새 규칙: 서사 SCENARIO-ACT6·7·8 구역 표와 규칙 표
  - QA 확정값: BAEK_*_CAST_BONUS, BAEK_PAHON_KARMA 1, BAEK_TIDE_WINDOW 20, BAEK_SKIP_RATIO_DEFAULT 0.5,
    LUMP_VISIBLE_BODIES_MAX 12, LUMP_PAHON_KARMA_* 0.1/3, CHAIN_BREAK_* +10%/+1몸, SLOW_STACK_MAX 0.35
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_s3 import ZONES, RING_BY_ACT
from mobs_s1 import BASE_CONCURRENT, CONCURRENT_CAP

# ── 백의 기본 ──────────────────────────────────────────
# 백은 나이로 나뉘지 않는다. 처결 대기는 하나로 둔다(해 넘긴 혼과 같은 7초).
BAEK = dict(name="백", wait=7.0, maedhim=100, cast=2.0,
            memory="감각 한 줄(생각이 아니라 몸의 느낌. 예: '발이 시렸다')",
            note="원념의 실(검은 물줄기)에 묶여 누워 있다. 실을 끊으면(전투) 무릎 꿇고, 이름을 불러 눕힌다")
LUMP_BAEK = dict(name="덩어리 백", maedhim_per_body=100, visible_max=12,
                 note="한 구덩이에 함께 묻힌 몸들. 아는 이름을 부르면(1초) 한 몸씩 떨어져 무릎 꿇는다. 모르는 몸은 깨뜨려 떼어 낸다")
THREAD = dict(name="원념의 실", maedhim=60, wait=0,
              note="백도 혼도 아니다. 실이 끌어올린 '물에 엉킨 손'·'흙 손' 같은 것. 쓰러뜨리면 사라지고 처결도 업도 없다")

# 특수 표지(tag). kind: enemy(싸운다) / guard(B-29 전에는 싸우지 않고 방을 지킨다)
TAGS = {
    "tide": dict(kind="enemy", name="물때 백", rule="⑤ 바다의 몸. 밀물 신호 뒤 20초 안에 눕히지 못하면 모래에 다시 묻혀 그 밤엔 사라진다. 다음 썰물 밤에 다시 드러난다(영영 잃지 않음)",
                 source="서사 ACT6 · QA 채택(BAEK_TIDE_WINDOW 20)"),
    "pair": dict(kind="enemy", name="줄 밑 백", rule="⑦ 줄 선 혼의 몸. 눕히면 바로 위 줄에서 그 혼의 발목 실이 풀려 말려 올라간다(위아래가 한 화면에 움직인다). 장례를 받은 사람(박돌쇠)의 백은 없다 — 빈자리로 보인다",
                 source="서사 ACT6 §3"),
    "number": dict(kind="enemy", name="목패 백", rule="④ 갱의 몸. 이름을 모르면 목패 번호로 눕힌다(캐스팅 +0.5초, 이튿날 목패에 번호가 새겨진다 — 반쪽). 시즌 1 B-08을 천도했으면 전원 이름으로",
                   source="서사 ACT7 · QA 채택(BAEK_NUMBER_CAST_BONUS 0.5)"),
    "nickname": dict(kind="enemy", name="무적 백", rule="⑥ 이름을 가져 본 적 없는 몸. 별명도 이름이다. 시즌 1 B-11을 천도했으면 별명으로 눕힌다(캐스팅 정상, 이튿날 팻말에 별명). 왕초의 백은 아이를 업고 있어 둘을 함께 눕혀야 한다",
                     source="서사 ACT7 §4"),
    "worker": dict(kind="enemy", name="일꾼 백", rule="⑧~⑩ 저승 일꾼(서리·부엌 할미)의 몸. 눕히면 위층에서 그 일꾼이 일을 놓고 줄에 선다(저승이 조금씩 빈다)",
                   source="서사 ACT8(F65)"),
    "waiting": dict(kind="guard", name="아랫목 백", rule="⑨ 오지 않는 차사를 기다리며 자기 집 아랫목에 누운 몸. B-29 할미가 눕기 전에는 '할머니 차례가 먼저'라며 눕지 않고 방을 지킨다(싸우지 않는 장애물, 깨뜨리기만 된다). B-29를 눕히면 전원 캐스팅 −0.5초",
                    source="서사 ACT8 B-29 · 해석은 기획(확인 요청)"),
    "chasa": dict(kind="enemy", name="차사의 백", rule="⑩ 사슬 무덤의 사슬마다 아래에 묶인 옛 차사의 몸. 눕히면 위의 사슬이 땅에서 빠져 녹슨 채 쓰러진다 — 무덤이 하나씩 끝난다. 맺힘 150(시즌 2 옛 차사 혼과 같음)",
                  source="서사 ACT8(F68) · 맺힘은 기획 제안"),
}

# 구역: (백 %, 덩어리 백 %, 실 %), {표지: 비율}, 한 줄 이유
MIX = {
    "둑 밑": ((80, 0, 20), {}, "큰물 밤 둑에서 쓸려 간 사람들. 가운데 팔을 엮은 열한 몸(시즌 1 월화를 천도했으면 바로, 파혼했으면 +0.5초)과 열두째 빈자리"),
    "소 밑": ((60, 0, 40), {}, "나룻배와 함께 가라앉은 사람들. 실이 '물에 엉킨 손'을 많이 끌어올린다"),
    "난파 여울 바닥": ((75, 0, 25), {"tide": 100}, "바다에서 돌아오지 못한 어부·해녀. 전원 물때를 따른다"),
    "곶 밑 바다굴": ((70, 0, 30), {"tide": 100}, "썰물에만 열리는 굴(B-22)"),
    "줄 밑": ((85, 0, 15), {"pair": 100}, "줄 선 혼들의 몸. 모든 관할에서 흘러와 모였다"),
    "닻 여울": ((40, 0, 60), {"pair": 100}, "매듭(B-23) 둘레. 실이 많다"),
    "큰 무덤 속": ((40, 40, 20), {}, "두 편이 한 구덩이에. 덩어리 백이 많다"),
    "화살골 뿌리 밑": ((70, 10, 20), {}, "건너편 병사들이 흩어져 묻힌 곳"),
    "물 찬 갱도": ((75, 5, 20), {"number": 60}, "갱에서 죽은 광부들. 목패 번호가 많다"),
    "막힌 막장 안쪽": ((80, 0, 20), {"number": 100}, "막장의 열셋(B-25). 전원 목패"),
    "석회 구덩이": ((30, 50, 20), {}, "역병 두 겹(B-26). 덩어리 백이 가장 많다"),
    "역병막 마루 밑": ((80, 0, 20), {}, "마루 밑으로 기어든 간병하던 사람들과 아이들"),
    "성문 밖 구덩이": ((50, 30, 20), {"nickname": 60}, "무연고 겹겹(B-27). 맨 위 겹에 아이를 업은 왕초"),
    "다리 기초 밑": ((80, 0, 20), {"nickname": 50}, "다리를 놓다 깔린 석수와 떠돌이. 이미 누운 백 하나(S-259)는 건드릴 수 없고 기억만 읽힌다"),
    "숙사 밑": ((80, 0, 20), {"worker": 90}, "일하다 잠든 자세의 서리·부엌 할미"),
    "먹 앙금": ((70, 0, 30), {"worker": 80}, "먹방 일꾼·벼루지기(B-28). 앙금에서 실이 많이 솟는다"),
    "아랫목": ((85, 0, 15), {"waiting": 100}, "집집마다 아랫목에 누운 몸과 머리맡의 밥상(B-29)"),
    "인장 굴 바닥": ((70, 0, 30), {}, "굴 사람들과 인을 훔친 혼의 몸"),
    "사슬 무덤 밑": ((70, 0, 30), {"chasa": 80}, "꽂힌 사슬마다 아래에 차사의 몸"),
    "첫 우물 밑": ((70, 0, 30), {}, "처음 마을 사람들(B-30)"),
    "물막이 골 소 가장 깊은 곳": ((0, 0, 100), {}, "B-31 무대. 백은 나의 백 하나뿐이고, 실만 솟는다"),
}

RULES = [
    ("눕히기", "실을 끊어 무릎 꿇은 백의 이름을 불러 눕힌다. 캐스팅 2.0초. 그 사람의 혼을 시즌 1·2에서 천도했으면 −0.5초, 파혼했으면 +0.5초, 번호로 부르면 +0.5초(하한 0.5초). 눕힐 때마다 저편 나룻불이 하나 는다", "서사 ACT6 · QA 채택(BAEK_*_CAST_BONUS)"),
    ("깨뜨리기", "즉시. 큰 폭발로 주변 정리. 업 +1. 그 백의 혼은 ⑦ 줄에서 돌아선다(영영 저편에 못 닿는다)", "서사 ACT6 · QA 채택(BAEK_PAHON_KARMA 1)"),
    ("주인 없는 백", "시즌 1·2에서 그 사람의 혼을 파혼했으면 이름 실이 끊겨 있다. 눕히려면 낮 단서 1개(거꾸로 장례)를 먼저 찾는다. 단서 없이도 깨뜨리기는 된다", "서사 ACT6"),
    ("비켜서는 백(7·8막)", "시즌 1·2에서 그 사람의 혼을 천도했으면 다가가면 스스로 일어나 비켜선다. 싸움 없이 바로 눕히고, 그 자리에 굴이 열려 아래층 지름길이 된다. 시즌 3부터 시작한 기본 상태는 약 절반", "서사 ACT7 · QA 채택(BAEK_SKIP_RATIO_DEFAULT 0.5)"),
    ("덩어리 백(7막)", "아는 이름을 부를 때마다(1초) 한 몸씩 떨어진다. 화면엔 12몸까지, 나머지는 덩어리 안. 모르는 몸을 깨뜨려 떼어 내면 몸당 업 +0.1, 덩어리 하나당 상한 +3", "QA 채택(LUMP_VISIBLE_BODIES_MAX, LUMP_PAHON_KARMA_*)"),
    ("6막 끊기판의 값", "6막을 B-23 끊기로 끝냈으면 7막 적 공격력 +10%(얼룩·소환엔 적용 안 함), 덩어리 백 +1몸", "QA 채택(CHAIN_BREAK_*)"),
    ("둔화 합산", "앙금·웅덩이·안개 등 이동 둔화는 겹쳐도 −35%에서 멈춘다", "QA 채택(SLOW_STACK_MAX)"),
]

BOSS_EFFECTS = [
    ("시즌 1 B-02(월화) 천도 / 파혼", "① 둑 밑", "열한 몸의 이마에 이름이 또렷 → 낮 단서 없이 바로 눕힘 / 파혼이면 이름이 흐려 +0.5초"),
    ("시즌 1 B-08 천도", "④", "장부 뒷장의 열네 이름 → 목패 백 전원 이름으로 눕힘(번호 +0.5초 없음)"),
    ("시즌 1 B-11 천도", "⑥", "무적 백을 별명으로 눕힘. 팻말에 별명이 새겨진다"),
    ("B-23 끊기", "7막 전체", "적 공격력 +10%, 덩어리 백 +1몸"),
    ("B-29 눕히기", "⑨", "아랫목 백이 눕기 시작한다. ⑨ 남은 백 전원 캐스팅 −0.5초"),
    ("시즌 2 ⑧~⑩ 천도", "8막", "그 혼의 백은 비켜선다(7막 규칙 그대로)"),
]

# 사나운 적 조건: 시즌 1 X1~X4는 그대로, 시즌 2 X5~X7은 ⑦~⑩ 위층에서만. 시즌 3에서 둘을 더한다.
FIERCE_S3 = [
    dict(id="X8", name="물에 잠긴 밤", when="물 차오름 경고(30초 전) 뒤에도 아래층에 남아 있으면, 차오르는 물에서 사나운 적 1마리가 일어난다(한 밤에 한 번)",
         status="제안", why="\"오늘 밤 얼마나 깊이\"(기둥 3)의 욕심에 값이 붙는다. 손실 50%보다 먼저 보이는 경고"),
    dict(id="X9", name="굳은 덩어리", when="덩어리 백 하나에서 모르는 몸을 깨뜨려 6몸 넘게 떼어 내면, 남은 덩어리가 사나운 적으로 굳는다(맺힘·공격 +50%)",
         status="제안", why="이름을 모아 오는 대신 깨뜨려 떼어 내는 길이 빠르기만 하지 않게 한다. 업 상한 +3만으로는 손에 잡히는 대가가 약하다"),
]


def build():
    rows = []
    for j, name, above, _L, boss, act, _clue in ZONES:
        (b, lump, th), tags, why = MIX[name]
        ring = RING_BY_ACT[act]
        rows.append(dict(
            jurisdiction=j, zone=name, act=act, ring=ring, boss=boss,
            mix=dict(baek=b / 100.0, lump_baek=lump / 100.0, thread=th / 100.0),
            tags={k: v / 100.0 for k, v in tags.items()},
            concurrent=min(CONCURRENT_CAP, BASE_CONCURRENT + ring), why=why,
        ))
    return dict(_설명="tools/mobs_s3.py가 만든 파일. 직접 고치지 말고 생성기를 고친다.",
                baek=BAEK, lump_baek=LUMP_BAEK, thread=THREAD, tags=TAGS,
                rules=[dict(name=a, rule=b, source=c) for a, b, c in RULES],
                boss_effects=[dict(when=a, where=b, effect=c) for a, b, c in BOSS_EFFECTS],
                fierce_s3=FIERCE_S3, fierce_mult=1.5, zones=rows)


def pct(x):
    return "%d%%" % round(x * 100)


def md(data):
    L = []
    A = L.append
    A("## 부록 F-3. 시즌 3 일반 적 구성표 (백)")
    A("")
    A("부록 F·F-2와 같은 틀이다. 시즌 3의 상대는 장례를 못 치른 **몸(백)**이라 혼처럼 나이로 나뉘지 않고, \"어떤 상처로 묻혔나\"로 나뉜다. 구역 성격은 서사 SCENARIO-ACT6·7·8의 \"주로 나오는 백\"을, 확정 수치는 QA 6·7·8막 검증을 따른다. 값은 `data/mobs_s3.json`(생성기 `tools/mobs_s3.py`)과 같다.")
    A("")
    A("### F3-1. 백의 종류")
    A("")
    A("| 종류 | 처결 대기 | 맺힘 | 설명 |")
    A("|---|---|---|---|")
    A("| %s | %g초 | %d | %s. 눕히면 기억은 %s |" % (data["baek"]["name"], data["baek"]["wait"], data["baek"]["maedhim"], data["baek"]["note"], data["baek"]["memory"]))
    A("| %s | — | 몸당 %d | %s |" % (data["lump_baek"]["name"], data["lump_baek"]["maedhim_per_body"], data["lump_baek"]["note"]))
    A("| %s | 없음 | %d | %s |" % (data["thread"]["name"], data["thread"]["maedhim"], data["thread"]["note"]))
    A("")
    A("**표지**는 그 몸이 묻힌 상처다.")
    A("")
    A("| 표지 | 싸우나 | 규칙 | 출처 |")
    A("|---|---|---|---|")
    for k, t in data["tags"].items():
        A("| %s | %s | %s | %s |" % (t["name"], "싸운다" if t["kind"] == "enemy" else "B-29 전에는 방을 지키는 장애물", t["rule"], t["source"]))
    A("")
    A("### F3-2. 시즌 3 공통 규칙")
    A("")
    A("| 규칙 | 내용 | 출처 |")
    A("|---|---|---|")
    for r in data["rules"]:
        A("| %s | %s | %s |" % (r["name"], r["rule"], r["source"]))
    A("")
    A("### F3-3. 구역별 구성")
    A("")
    A("백·덩어리 백·실을 더하면 100%다. 표지 비율은 그 구역 백 중 표지가 붙는 몫이다. 동시 수 = 4 + 고리(상한 10). 고리는 부록 C-3(6막 9 · 7막 10 · 8막 11).")
    A("")
    A("| 막 | 관할 | 아래층 구역 | 백 | 덩어리 백 | 실 | 표지 | 동시 | 왜 |")
    A("|---|---|---|---|---|---|---|---|---|")
    for z in data["zones"]:
        tg = ", ".join("%s %s" % (data["tags"][k]["name"], pct(v)) for k, v in z["tags"].items()) or "—"
        m = z["mix"]
        A("| %d | %s | %s | %s | %s | %s | %s | %d | %s |" % (
            z["act"], z["jurisdiction"], z["zone"], pct(m["baek"]), pct(m["lump_baek"]), pct(m["thread"]),
            tg, z["concurrent"], z["why"]))
    A("")
    A("### F3-4. 앞선 처결이 바꾸는 것")
    A("")
    A("| 처결 | 어디 | 바뀌는 것 |")
    A("|---|---|---|")
    for e in data["boss_effects"]:
        A("| %s | %s | %s |" % (e["when"], e["where"], e["effect"]))
    A("")
    A("### F3-5. 사나운 적이 나오는 조건")
    A("")
    A("시즌 1의 X1~X4는 아래층에서도 그대로이고, 시즌 2의 X5~X7은 ⑦~⑩ 위층 규칙이라 아래층엔 없다. 시즌 3에서 둘을 더한다. 조건 번호는 X를 쓴다(서사 단서 번호 F와 섞이지 않게).")
    A("")
    A("| 조건 | 언제 | 상태 | 왜 |")
    A("|---|---|---|---|")
    for f in data["fierce_s3"]:
        A("| %s %s | %s | %s | %s |" % (f["id"], f["name"], f["when"], f["status"], f["why"]))
    A("")
    A("### F3-6. 확인 요청")
    A("")
    A("| 누구 | 무엇 |")
    A("|---|---|")
    A("| QA | 백 처결 대기 7초 하나로 / 실(잡몹) 맺힘 60·업 없음 / 차사의 백 맺힘 150 / X8 경고 뒤 남으면 사나운 적 1 / X9 덩어리에서 6몸 넘게 깨뜨리면 굳음 / 구역별 실 비율 15~60% |")
    A("| 서사 | 백을 나이 대신 '묻힌 상처'로 나눈 것 / ⑨ 아랫목 백은 B-29 전에는 눕지 않는 장애물로 해석(깨뜨리기만 됨) / 원념의 실이 끌어올린 '손'을 처결 없는 잡몹으로 둔 것 / B-31 무대에는 실만 솟는다 |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = build()
    with open(os.path.join(root, "data", "mobs_s3.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "planning")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "appendix-F3.md"), "w", encoding="utf-8") as f:
        f.write(md(data))
    for z in data["zones"]:
        print(z["zone"], z["mix"], z["concurrent"])
