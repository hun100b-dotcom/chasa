# -*- coding: utf-8 -*-
"""
시즌 1 일반 적(혼) 구성표 생성기 (기획서 부록 F의 단일 출처)

왜 이 파일이 있나:
  구역마다 "어떤 혼이 몇 %로, 한 번에 몇 마리, 언제 사나운 적이 나오나"를
  한 표로 정해 두어야 코드(스폰)와 QA(시뮬)와 서사(땅의 상처)가 같은 숫자를 본다.
  숫자를 바꿀 때는 이 파일만 고치고 다시 돌린다.

실행:
  python3 tools/mobs_s1.py [부록 마크다운을 쓸 폴더]
  → data/mobs_s1.json + <폴더>/appendix-F.md

출처:
  - 혼의 나이(갓 죽은·해 넘긴·오래된)와 대기 시간: WORLD-BIBLE §4, balance.json WAIT_*
  - 구역마다 "주로 나오는 혼": WORLD-BIBLE §4-1, SCENARIO-ACT2·ACT3 구역 표
  - 덩어리 확률(고리마다 +5%, 상한 25%): tools/route_s1.py와 같은 함수
  - 사나운 적(맺힘·공격 +50%, 얼룩 3개 겹침): balance.json FIERCE_MULT, STAIN_SUMMON_COUNT
  - 물 혼·숫자 혼·무적 혼 보정: balance.json WATER_SOUL_CAST_BONUS, SEAL_MISSING_CAST_BONUS, NAMED_SOUL_CAST_BONUS
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_s1 import ZONES, ring_lump  # 고리·덩어리 확률은 동선 표와 같은 값을 쓴다

# ── 혼 종류 ─────────────────────────────────────────────
# 나이(age)는 죽은 지 얼마나 됐는지로 정해진 값이라 바뀌지 않는다(서사 확정 10-24).
AGES = [
    dict(id="fresh", name="갓 죽은 혼", wait=10.0, maedhim=100, memory="또렷한 한 줄(최근 목격담)"),
    dict(id="year", name="해 넘긴 혼", wait=7.0, maedhim=100, memory="흐린 한 줄"),
    dict(id="old", name="오래된 혼", wait=4.0, maedhim=100, memory="조각 한 줄"),
]
LUMP = dict(id="lump", name="덩어리", wait=4.0, maedhim=400, tendo=False,
            note="파혼만 된다. 파혼하면 엉켜 있던 이름 목록이 잠깐 보인다")

# 특수 표지(tag): 나이와 따로 붙는다. 갓 죽은 물 혼, 오래된 숫자 혼처럼 겹칠 수 있다.
TAGS = {
    "water": dict(name="물 혼", rule="물가에서 일어난다. 천도 캐스팅 −0.5초. 밀물 신호 뒤 20초 안에 못 붙잡으면 그 밤엔 가라앉아 사라진다",
                  source="QA 채택(WATER_SOUL_CAST_BONUS, WATER_TIDE_WINDOW)"),
    "number": dict(name="숫자 혼", rule="명부에 번호로만 적혔다(인 없음). 천도 캐스팅 +0.5초, 기억은 짧은 한 줄. B-08을 천도하면 ④의 숫자 혼은 이름을 되찾는다(인 흐림 +0.25초)",
                   source="QA 채택(SEAL_MISSING_CAST_BONUS) · 서사 ACT2"),
    "soldier": dict(name="병사 혼", rule="셋이 한 대열로 함께 일어난다. B-05 처결 전에는 병사 혼의 20%가 '번호 병사'(맺힘·공격 +30%)",
                    source="서사 ACT2(B-05 번호 병사) · 기획 제안(대열·20%)"),
    "miner": dict(name="광부 혼", rule="둘씩 일어난다. 등불을 들고 있어 쓰러지면 2초 동안 주변 시야가 밝아진다(갱도 구역의 어둠을 덜어 줌)",
                  source="기획 제안"),
    "homeless": dict(name="무적 혼", rule="호적에 오른 적이 없어 명부에 처음부터 이름이 없다(인 없음 +0.5초). 낮에 별명을 들은 혼은 −0.5초(하한 0.5초). B-11을 천도하면 ⑥ 무적 혼 전원이 별명으로 천도 가능",
                     source="QA 채택(NAMED_SOUL_CAST_BONUS) · 서사 ACT3"),
}

# ── 구역 구성 ───────────────────────────────────────────
# 구역 이름: (갓 죽은, 해 넘긴, 오래된) 비율(덩어리를 뺀 나머지 안에서), 덩어리 가산(%p), {표지: 비율}, 한 줄 이유
MIX = {
    "솔고개 마을": ((70, 25, 5), 0, {}, "요즘 상여가 자주 나가는 마을. 첫 밤의 무대라 대기가 긴 갓 죽은 혼이 대부분"),
    "보릿들": ((25, 60, 15), 0, {"water": 15}, "몇 해 전 큰물이 난 논밭. 해 넘긴 혼 위주, 둑 쪽에 물 혼"),
    "물막이 골": ((10, 50, 40), 0, {"water": 40}, "옛 나루. 큰물 밤에 떠내려간 사람들. 물 혼이 많다"),
    "폐당집": ((5, 25, 70), 5, {}, "오래전부터 파혼된 파편이 모이는 곳(WORLD-BIBLE). 오래된 혼과 덩어리"),
    "장터거리": ((60, 30, 10), 0, {}, "사람 많은 장터. 역병을 '고뿔'이라 한 사이 죽은 이들"),
    "동헌 터": ((30, 50, 20), 0, {}, "관아 터. 명단을 지운 곳이라 해 넘긴 혼이 맴돈다"),
    "역병막": ((30, 50, 20), 0, {}, "역병은 몇 해 전 여름에 돌았고, 지금은 해마다 '고뿔'로 몇 명씩 죽는다(서사 확정 10-24). 해 넘긴 혼이 더 많다"),
    "무덤골": ((10, 40, 50), 0, {}, "새 무덤과 사십 년 된 무덤이 섞인 골"),
    "무너진 산성": ((40, 50, 10), 0, {"soldier": 30}, "아랫마을(산 사람)과 성터가 겹친다. 마을 혼과 병사 혼이 반반"),
    "화살골": ((10, 50, 40), 0, {"soldier": 60}, "밤마다 번호 부르는 소리. 병사 혼이 많다"),
    "군막 터": ((5, 25, 70), 0, {"soldier": 70}, "진법도만 남은 평지. 오래된 병사 혼"),
    "큰 무덤": ((0, 20, 80), 5, {"soldier": 50}, "서른일곱이 한 구덩이에. 덩어리가 많다"),
    "광부촌": ((50, 40, 10), 0, {"miner": 40, "number": 15}, "목패 걸이 마을. 돌아오지 않은 광부"),
    "선탄장": ((50, 40, 10), 0, {"miner": 20, "number": 15}, "석탄 고르는 아낙들. 광부보다 마을 혼이 많다"),
    "큰 갱도": ((10, 50, 40), 0, {"miner": 60, "number": 25}, "끝없는 어둠. 해 넘긴 광부 혼"),
    "무너진 막장": ((0, 30, 70), 0, {"miner": 50, "number": 50}, "'13 나감'. 숫자 혼이 절반"),
    "포구": ((50, 40, 10), 0, {"water": 25}, "선창과 객주. 바다에서 돌아오지 않은 사람들"),
    "소금밭": ((50, 10, 40), 0, {"water": 15}, "소금 더미가 혼불처럼 빛나 헷갈린다(시야)"),
    "망부석 곶": ((40, 50, 10), 0, {"water": 35}, "헛묘 마흔둘. 몸 없는 무덤"),
    "난파 여울": ((0, 50, 50), 0, {"water": 60}, "썰물 때만 바닥이 드러나는 여울. 물 혼이 가장 많다"),
    "저잣거리": ((50, 40, 10), 0, {"homeless": 30}, "등불이 많아 혼불이 잘 안 보인다(시야 대비 낮음)"),
    "큰 다리 밑": ((40, 50, 10), 0, {"homeless": 60}, "다리 밑 움막. 무적 혼이 가장 많다"),
    "빈민 움막촌": ((20, 60, 20), 0, {"homeless": 50}, "검은여울에서 올라온 사람들의 자식들"),
    "성문 밖": ((0, 30, 70), 5, {"homeless": 30}, "팻말 없는 구덩이 무덤. 덩어리가 많다"),
}

BASE_CONCURRENT = 4      # 한 구역에 동시에 서 있는 적 수 = 4 + 고리 (첫 밤 balance.json ENEMY_COUNT 5와 같음)
CONCURRENT_CAP = 10      # 휴대폰 성능과 화면 읽기를 위해 10에서 멈춘다
NAMED_PER_ZONE = 6       # 관할당 이름혼 24(서사 S-4) ÷ 구역 4

# 보스 처결이 그 관할의 혼 구성을 바꾸는 것(서사 보스 표에서 그대로)
BOSS_EFFECTS = [
    ("B-01 파혼", "물막이 골", "덩어리 +10%p (큰 얼룩 지대)"),
    ("B-03 천도", "②", "이름혼 인 없음 → 흐림 (+0.5초 → +0.25초)"),
    ("B-05 천도", "③", "덩어리 −10%p, 번호 병사 0%"),
    ("B-08 천도", "④", "숫자 혼이 이름을 되찾음 (+0.5초 → +0.25초, 긴 기억)"),
    ("B-11 천도", "⑥", "무적 혼 전원 별명으로 천도 (−0.5초)"),
]

# 사나운 적이 나오는 조건. 사나운 적 = 맺힘·공격 +50%(FIERCE_MULT), 쓰러뜨리면 귀한 장비 확정
FIERCE = [
    dict(id="X1", name="얼룩 셋", when="원념 얼룩 3개가 겹치면 그 자리에서 1마리", status="QA 채택(P-010)",
         why="파혼의 대가가 세계 안에서 보인다(덩어리 = 파혼이 만든 것)"),
    dict(id="X2", name="흐르는 얼룩", when="물 혼이 있는 구역(보릿들·물막이 골·⑤)에서는 얼룩이 초당 0.5m씩 물 낮은 쪽으로 흘러 모인다. 그래서 X1이 더 자주 생긴다. 이렇게 생긴 사나운 적은 '큰물귀신' 모습",
         status="서사 BOSS-01(큰물 단계) 확장 · 제안", why="물가에서 파혼하면 얼룩이 한곳에 모인다는 것을 몸으로 배운다"),
    dict(id="X3", name="놓친 혼", when="한 밤에 처결 대기를 3번 넘기면, 그 뒤로 대기를 넘긴 혼은 맺힘 50%로 일어나는 대신 사나운 적으로 일어난다",
         status="제안", why="고르지 않는 것도 선택이다. 천도도 파혼도 안 하고 미루면 값을 치른다"),
    dict(id="X4", name="업의 그늘", when="업 30 이상이면 새로 일어나는 적 중 3%, 업 60 이상이면 6%가 사나운 적",
         status="제안", why="파혼 습관이 밤의 위험으로 돌아온다. 숫자가 아니라 무서운 적으로 느껴진다"),
]


def build():
    rows = []
    for j, name, ring, base, _sh, _cut, boss, act in ZONES:
        ages, lump_add, tags, why = MIX[name]
        lump = min(0.25, ring_lump(ring) + lump_add / 100.0)
        rest = 1 - lump
        mix = {a["id"]: round(rest * w / 100.0, 3) for a, w in zip(AGES, ages)}
        mix["lump"] = round(lump, 3)
        rows.append(dict(
            jurisdiction=j, zone=name, ring=ring, act=act, boss=boss,
            mix=mix, tags={k: v / 100.0 for k, v in tags.items()},
            concurrent=min(CONCURRENT_CAP, BASE_CONCURRENT + ring),
            named_souls=NAMED_PER_ZONE, why=why,
        ))
    return dict(_설명="tools/mobs_s1.py가 만든 파일. 직접 고치지 말고 생성기를 고친다.",
                ages=AGES, lump=LUMP, tags=TAGS, fierce=FIERCE, fierce_mult=1.5,
                boss_effects=[dict(when=a, where=b, effect=c) for a, b, c in BOSS_EFFECTS],
                zones=rows)


def pct(x):
    return "%d%%" % round(x * 100)


def md(data):
    L = []
    A = L.append
    A("## 부록 F. 시즌 1 일반 적 구성표")
    A("")
    A("구역마다 어떤 혼이 몇 %로 나오는지, 한 번에 몇 마리인지, 사나운 적이 언제 나오는지를 정한다. 혼의 나이와 대기 시간은 세계관 값(WORLD-BIBLE)을, 구역의 성격은 서사 구역 표의 \"주로 나오는 혼\"을, 보정 수치는 QA 채택값을 그대로 쓴다. 값은 `data/mobs_s1.json`(생성기 `tools/mobs_s1.py`)과 같다.")
    A("")
    A("### F-1. 혼의 종류")
    A("")
    A("**나이**는 죽은 지 얼마나 됐는지로 정해진 값이라 하룻밤이 지나도 바뀌지 않는다(서사 확정). 나이가 많을수록 처결 대기가 짧아 빨리 골라야 한다.")
    A("")
    A("| 나이 | 처결 대기 | 맺힘 | 천도하면 기억 |")
    A("|---|---|---|---|")
    for a in data["ages"]:
        A("| %s | %g초 | %d | %s |" % (a["name"], a["wait"], a["maedhim"], a["memory"]))
    A("| 덩어리 | %g초 | %d | 천도 불가. %s |" % (data["lump"]["wait"], data["lump"]["maedhim"], data["lump"]["note"]))
    A("")
    A("**표지**는 나이와 따로 붙는 특징이다. 관할의 \"땅의 상처\"가 혼의 모습으로 드러난다.")
    A("")
    A("| 표지 | 규칙 | 출처 |")
    A("|---|---|---|")
    for k, t in data["tags"].items():
        A("| %s | %s | %s |" % (t["name"], t["rule"], t["source"]))
    A("")
    A("### F-2. 구역별 구성")
    A("")
    A("나이 비율은 덩어리를 뺀 나머지를 나눈 값이다(네 칸을 더하면 100%%). 표지 비율은 그 구역 혼 중 표지가 붙는 몫이다. 동시 수 = 4 + 고리(상한 10). 구역마다 이름혼 %d명(관할당 24)." % NAMED_PER_ZONE)
    A("")
    A("| 관할 | 구역 | 고리 | 갓 죽은 | 해 넘긴 | 오래된 | 덩어리 | 표지 | 동시 | 왜 |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for z in data["zones"]:
        tg = ", ".join("%s %s" % (data["tags"][k]["name"], pct(v)) for k, v in z["tags"].items()) or "—"
        m = z["mix"]
        A("| %s | %s | %d | %s | %s | %s | %s | %s | %d | %s |" % (
            z["jurisdiction"], z["zone"], z["ring"], pct(m["fresh"]), pct(m["year"]), pct(m["old"]), pct(m["lump"]),
            tg, z["concurrent"], z["why"]))
    A("")
    A("### F-3. 보스 처결이 바꾸는 것")
    A("")
    A("| 처결 | 어디 | 바뀌는 것 |")
    A("|---|---|---|")
    for e in data["boss_effects"]:
        A("| %s | %s | %s |" % (e["when"], e["where"], e["effect"]))
    A("")
    A("### F-4. 사나운 적이 나오는 조건")
    A("")
    A("사나운 적은 맺힘·공격이 +50%이고, 쓰러뜨리면 귀한 장비가 확정으로 나온다(부록 A-3 등급 표). 조건은 넷이고(번호는 X를 쓴다. 서사 단서 번호 F1~F73과 섞이지 않게) 모두 \"내가 고른 것(또는 고르지 않은 것)\"에서 나온다.")
    A("")
    A("| 조건 | 언제 | 상태 | 왜 |")
    A("|---|---|---|---|")
    for f in data["fierce"]:
        A("| %s %s | %s | %s | %s |" % (f["id"], f["name"], f["when"], f["status"], f["why"]))
    A("")
    A("### F-5. 확인 요청")
    A("")
    A("| 누구 | 무엇 |")
    A("|---|---|")
    A("| QA | 동시 수 4+고리(상한 10) / X2 얼룩 흐름 초당 0.5m / X3 '놓친 혼 3번' / X4 업 30·60에 3%·6% / 덩어리 가산 +5%p 세 곳(폐당집·큰 무덤·성문 밖) |")
    A("| 서사 | (확인 완료 10-24) 병사 혼 대열·광부 혼 등불 좋음. ② 구역표 맞음, 역병막만 해 넘긴 혼이 더 많게 고침 |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = build()
    with open(os.path.join(root, "data", "mobs_s1.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "planning")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "appendix-F.md"), "w", encoding="utf-8") as f:
        f.write(md(data))
    for z in data["zones"]:
        print(z["zone"], z["mix"], z["concurrent"])
