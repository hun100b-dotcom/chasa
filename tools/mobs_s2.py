# -*- coding: utf-8 -*-
"""
시즌 2 일반 적(혼) 구성표 생성기 (기획서 부록 F-2의 단일 출처)

왜 이 파일이 있나:
  시즌 2(⑦~⑩, 4·5막)는 저승 쪽 땅이라 혼의 종류와 규칙이 시즌 1과 다르다
  (줄 선 혼, 돌아선 혼, 인 없는 혼, 이름 조각, 옛 차사 혼, 물막이 눈금).
  구역마다 "무엇이 몇 %로, 한 번에 몇 마리, 언제 사나운 적이 나오나"를
  한 표로 정해 두어야 코드(스폰)·QA(시뮬)·서사(땅의 상처)가 같은 숫자를 본다.

실행:
  python3 tools/mobs_s2.py [부록 마크다운을 쓸 폴더]
  → data/mobs_s2.json + <폴더>/appendix-F2.md

출처:
  - 구역과 고리: tools/route_s2.py ZONES (같은 표를 그대로 가져온다)
  - 혼의 나이·대기 시간·사나운 적 X1~X4: tools/mobs_s1.py (시즌이 바뀌어도 읽는 법은 같게)
  - 구역마다 "주로 나오는 혼"과 새 규칙: 서사 SCENARIO-ACT4 §1·§2, SCENARIO-ACT5 §1·§2
  - 확정 수치: balance.json (NAME_PICKUP_WINDOW, DAM_TICK_*, TURNED_SOUL_NEOK_RATIO,
    NAME_JOIN_REWARD_MULT, MEMORY_MAP_RADIUS, SEAL_MISSING_CAST_BONUS)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_s2 import ZONES                      # 시즌 2 구역 16곳(관할·구역·고리·…)
from mobs_s1 import AGES, LUMP, FIERCE, BASE_CONCURRENT, CONCURRENT_CAP  # 시즌 1과 같은 기본값

# ── 덩어리 ─────────────────────────────────────────────
# 시즌 1 공식(고리마다 +5%, 상한 25%)을 그대로 쓰면 고리 6~8인 시즌 2는 모든 구역이 25%가 된다.
# 그런데 서사(ACT4)는 "⑦~⑩에서 깨진 가루는 곧장 하류의 큰 물막이로 흘러간다"고 정했다.
# 그래서 시즌 2는 덩어리가 구역에 덜 남고(기본 10%), 가루가 고이는 네 곳에만 몰린다(+15%p).
S2_LUMP_BASE = 0.10
S2_LUMP_POOL = 0.15   # 물안개 둑·숫자 마당·아홉째 문·물막이 바닥

# ── 시즌 2 표지(tag) ───────────────────────────────────
# kind: enemy(싸우는 혼) / obstacle(때리면 안 되는 혼). 줄 선 혼만 obstacle이다.
TAGS = {
    "line": dict(kind="obstacle", name="줄 선 혼",
                 rule="배를 기다리며 줄에 선 혼. 싸우지 않는다(장애물). 실수로 때리면 그 혼이 줄을 떠나 돌아선 혼이 된다. 업 30 이상이면 등을 돌리고 엿듣기를 막는다",
                 source="서사 ACT4 §1·B-13"),
    "turned": dict(kind="enemy", name="돌아선 혼",
                   rule="줄에서 지쳐 돌아선 혼. 천도하면 줄로 돌아간다(넋은 일반의 40%, 기억은 '기다림' 한 줄)",
                   source="서사 ACT4 · QA 채택(TURNED_SOUL_NEOK_RATIO 0.4)"),
    "number": dict(kind="enemy", name="숫자 혼",
                   rule="이름 대신 번호로 적힌 혼. ⑦에서는 시즌 1과 같다(천도 캐스팅 +0.5초). ⑧ 숫자 마당에서는 기본 천도 불가(파혼만). 시즌 1에서 그 혼의 고향 관할 이름을 되찾아 줬다면(B-05·B-08·B-11 천도) 번호 옆에 이름이 떠 바로 천도된다. B-15를 천도하면 전원 이름 회복",
                   source="서사 ACT4 §0 · 비율은 기획 제안"),
    "sealless": dict(kind="enemy", name="인 없는 혼",
                     rule="아홉째 인이 없어 아무도 데리러 오지 않은 혼. 천도 캐스팅 +0.5초. 천도하면 그 혼의 기억이 주변 반경 8m의 지도를 그린다(B-17 천도 뒤 12m). 파혼한 자리는 빈 종이로 남는다",
                     source="서사 ACT5 · QA 채택(SEAL_MISSING_CAST_BONUS, MEMORY_MAP_RADIUS)"),
    "fragment": dict(kind="enemy", name="이름 조각",
                     rule="깨진 이름의 조각. 하나로는 천도할 수 없다. 같은 색 조각 셋을 사슬로 모아 한 이름으로 이으면 천도된다(보상 3배). 4막·⑨에서 주운 이름 쪽지는 조각 하나로 친다. 조각을 그냥 파혼하면 빠르지만 물막이 눈금이 오른다",
                     source="서사 ACT5 · QA 채택(NAME_JOIN_REWARD_MULT 3)"),
    "old_chasa": dict(kind="enemy", name="옛 차사 혼",
                      rule="이름을 끝내 못 찾고 흩어진 옛 차사. 녹슨 사슬로 나를 끌어당긴다(예고 0.8초, 직선 8m). 맺힘 150. 천도하면 '이름을 부르기만 하면 됐던 시절'의 기억 한 줄. B-19를 천도하면 이름을 되찾고 더는 싸우지 않는다",
                      source="서사 ACT5 사슬 무덤 · 사슬·수치는 기획 제안"),
}

# ── 구역 구성 ───────────────────────────────────────────
# 구역 이름: (갓 죽은, 해 넘긴, 오래된) 비율(덩어리를 뺀 나머지 안에서), 고이는 곳인가, {표지: 비율}, 줄 선 혼 수, 한 줄 이유
# 저승 쪽 땅이라 갓 죽은 혼은 거의 없다. 시즌 1에서 대기를 넘겨 놓친 혼이 여기 '해 넘긴 혼'으로 다시 온다.
MIX = {
    "갈대늪": ((5, 25, 70), False, {"turned": 50}, 0, "은빛 갈대에 가루가 걸린 강가. 오래된 혼과 돌아선 혼"),
    "빈 나루 마을": ((20, 50, 30), False, {"turned": 40}, 24, "강가의 줄. 줄 선 혼(장애물) 사이로 돌아선 혼이 떠돈다"),
    "먹물 여울": ((5, 30, 65), False, {"number": 40}, 0, "관아에서 버린 먹물이 섞여 흐른다. 숫자 혼이 떠내려온다"),
    "물안개 둑": ((0, 30, 70), True, {"turned": 30}, 0, "이름 수천이 들리는 둑. 덩어리가 많다(B-14)"),
    "서리 숙사": ((0, 60, 40), False, {}, 0, "서리들의 행랑. 신참 서리 혼(해 넘긴)이 많다. 서리들은 차사를 보지만 말을 걸지 않는다"),
    "먹방": ((0, 20, 80), False, {}, 0, "천도된 기억을 가는 작업장. 오래된 혼"),
    "문서 창고": ((0, 20, 80), False, {"number": 20}, 0, "끝없는 서가. 오래된 혼, 번호 사본 사이의 숫자 혼"),
    "숫자 마당": ((10, 40, 50), True, {"number": 100}, 0, "번호순으로 선 혼들. 전원 숫자 혼, 덩어리가 고인다"),
    "빈 고을": ((0, 20, 80), False, {"sealless": 100}, 0, "문패 없는 솔고개. 인 없는 혼(대부분 오래된)"),
    "아홉째 문": ((0, 30, 70), True, {"sealless": 100}, 0, "문 앞에 몰린 혼과 덩어리"),
    "도장 없는 장터": ((10, 30, 60), False, {"sealless": 100}, 0, "서로 '어이'라고만 부르는 장. 인 없는 혼"),
    "인장 굴": ((0, 20, 80), False, {"sealless": 100}, 0, "B-18의 굴. 이마가 짓무른 인 없는 혼"),
    "처음 마을": ((0, 10, 90), False, {"fragment": 60}, 0, "늘 같은 새벽빛. 이름 조각과 오래된 혼"),
    "사슬 무덤": ((0, 10, 90), False, {"old_chasa": 40, "fragment": 40}, 0, "녹슨 사슬이 비석처럼. 옛 차사 혼과 이름 조각"),
    "우물터": ((0, 10, 90), False, {"fragment": 50}, 0, "B-19의 우물. 이름 조각"),
    "물막이 바닥": ((0, 10, 90), True, {"fragment": 70}, 0, "모든 관할의 깨진 이름이 고인 곳. 이름 조각과 덩어리"),
}

NAMED_PER_ZONE = 6        # 관할당 이름혼 24(서사 S-4) ÷ 구역 4. 시즌 1과 같다
OLD_CHASA_HP = 150        # 옛 차사 혼 맺힘(일반 100의 1.5배, 사나운 적보다 약간 낮게)
INKKEEPER_NOTES = 18      # ⑨에 먹지기가 흘린 이름 쪽지(서사 ACT5 제안 18장, 구역당 4~5장)

# 시즌 2 공통 규칙(⑦~⑩ 어디서나)
RULES = [
    ("물막이 눈금", "⑦~⑩에서 파혼할 때마다 하류의 큰 물막이(B-20)가 커진다. 일반 파혼 +1, 보스 파혼 +10. 화면 구석에 늘 보인다", "QA 채택(DAM_TICK_PAHON 1, DAM_TICK_BOSS_PAHON 10)"),
    ("이름 줍기", "파혼할 때 흩어지는 가루 속에 이름 쪽지 한 장이 2.0초 떠오른다. 사슬로 낚으면 '이름만 남은 기억'을 얻고 그 파혼의 물막이 눈금이 절반만 오른다", "QA 채택(NAME_PICKUP_WINDOW 2.0, DAM_TICK_PICKUP_FACTOR 0.5)"),
    ("주운 쪽지의 쓰임", "주운 이름 쪽지는 ⑩에서 이름 조각 하나로 치고, B-20 풀어내기 조건(기억한 이름 ÷ 물막이 크기 ≥ 0.6)의 '기억한 이름'에 더해진다", "서사 ACT5 · QA 채택(RELEASE_RATIO_MIN 0.6)"),
    ("먹지기의 쪽지", "이름 줍기를 놓친 사람을 위해 ⑨ 먹지기의 흔적 근처에 그가 대신 주운 쪽지 %d장(구역당 4~5장). 4막에서 성실히 주웠다면 같은 자리에서 '너도 주웠구나' 쪽지만 나온다(보상 중복 없음)" % INKKEEPER_NOTES, "서사 ACT5(qa 합의 10-24) · 개수는 QA 확인 요청"),
    ("⑨ 기억 지도", "⑨는 지도가 빈 종이다. 천도할 때마다 그 자리 반경 8m가 그려진다. 지도가 비어 있는 동안 ⑨ 안 걸음은 1.2배(헤맴)", "서사 ACT5 · QA 채택 · 헤맴 배율은 부록 C-2"),
]

# 보스 처결이 그 관할의 혼 구성을 바꾸는 것(서사 보스 표에서)
BOSS_EFFECTS = [
    ("B-13 천도", "⑦", "줄이 한 칸 움직인다. 돌아선 혼 −10%p(줄로 돌아간 몫)"),
    ("B-14 파혼", "⑦", "주운 쪽지 수만큼 줄 끝에 희미한 혼이 다시 선다(줄 선 혼 +). 0장이면 아무도 안 선다"),
    ("B-15 천도", "⑧ · 모든 관할", "숫자 마당 혼 전원 이름 회복(천도 가능). 이후 어느 관할에서든 숫자 혼의 천도 가산 +0.5초가 사라진다"),
    ("B-17 천도", "⑨", "기억 지도 반경 8m → 12m. 빈 고을이 쉼터"),
    ("B-18 천도", "⑨", "아홉째 인 회복: 인 없는 혼이 보통 혼이 된다(+0.5초 사라짐), 지도가 한꺼번에 그려지고 ⑨에 새벽 틈이 생긴다"),
    ("B-19 천도", "⑩ 사슬 무덤", "옛 차사 혼이 이름을 되찾아 더는 싸우지 않는다(처결 대기 상태로 선다)"),
]

# 시즌 2에서 더해지는 사나운 적 조건. X1~X4(시즌 1)는 그대로 이어진다.
FIERCE_S2 = [
    dict(id="X5", name="물막이 역류", when="물막이 눈금이 50·100·150을 넘는 순간, 그 밤 지금 구역에 가루 귀신(사나운 적) 1마리. 같은 문턱은 한 번만",
         status="제안", why="파혼의 값이 B-20까지 미뤄지지 않고 지금 밤에도 한 번씩 얼굴을 내민다"),
    dict(id="X6", name="빈 종이", when="⑨에서 지도가 그려지지 않은 칸에서 일어나는 적의 5%가 사나운 적",
         status="제안", why="천도로 길을 그린 땅은 안전하고, 파혼만 한 땅은 다음 밤에도 위험하다"),
    dict(id="X7", name="흩어진 색", when="⑩에서 같은 색 이름 조각 하나를 파혼하면, 남은 두 조각이 엉겨 사나운 적 1마리가 된다",
         status="제안", why="잇기를 시작했다가 깨뜨리면 대가가 바로 온다. 이을지 깰지를 조각마다 고르게 한다"),
]


def build():
    rows = []
    for j, name, ring, _walk, _sh, boss, act, _dawn in ZONES:
        ages, pool, tags, line, why = MIX[name]
        lump = S2_LUMP_BASE + (S2_LUMP_POOL if pool else 0)
        rest = 1 - lump
        mix = {a["id"]: round(rest * w / 100.0, 3) for a, w in zip(AGES, ages)}
        mix["lump"] = round(lump, 3)
        rows.append(dict(
            jurisdiction=j, zone=name, ring=ring, act=act, boss=boss,
            mix=mix, tags={k: v / 100.0 for k, v in tags.items()},
            line_souls=line,
            concurrent=min(CONCURRENT_CAP, BASE_CONCURRENT + ring),
            named_souls=NAMED_PER_ZONE, why=why,
        ))
    return dict(_설명="tools/mobs_s2.py가 만든 파일. 직접 고치지 말고 생성기를 고친다.",
                ages=AGES, lump=LUMP, lump_base=S2_LUMP_BASE, lump_pool=S2_LUMP_POOL,
                tags=TAGS, old_chasa_hp=OLD_CHASA_HP, inkkeeper_notes=INKKEEPER_NOTES,
                rules=[dict(name=a, rule=b, source=c) for a, b, c in RULES],
                fierce_s1=FIERCE, fierce_s2=FIERCE_S2, fierce_mult=1.5,
                boss_effects=[dict(when=a, where=b, effect=c) for a, b, c in BOSS_EFFECTS],
                zones=rows)


def pct(x):
    return "%d%%" % round(x * 100)


def md(data):
    L = []
    A = L.append
    A("## 부록 F-2. 시즌 2 일반 적 구성표")
    A("")
    A("부록 F(시즌 1)와 같은 틀이다. 혼의 나이·대기 시간과 사나운 적 X1~X4는 시즌 1 값을 그대로 잇고, 시즌 2(⑦~⑩)에서 새로 생기는 혼과 규칙만 더한다. 구역 성격은 서사 SCENARIO-ACT4·ACT5의 \"주로 나오는 혼\"을, 확정 수치는 QA 4·5막 검증을 따른다. 값은 `data/mobs_s2.json`(생성기 `tools/mobs_s2.py`)과 같다.")
    A("")
    A("### F2-1. 시즌 2에 새로 나오는 혼")
    A("")
    A("| 표지 | 싸우나 | 규칙 | 출처 |")
    A("|---|---|---|---|")
    for k, t in data["tags"].items():
        A("| %s | %s | %s | %s |" % (t["name"], "장애물(때리면 안 됨)" if t["kind"] == "obstacle" else "싸운다", t["rule"], t["source"]))
    A("")
    A("### F2-2. 시즌 2 공통 규칙")
    A("")
    A("| 규칙 | 내용 | 출처 |")
    A("|---|---|---|")
    for r in data["rules"]:
        A("| %s | %s | %s |" % (r["name"], r["rule"], r["source"]))
    A("")
    A("### F2-3. 구역별 구성")
    A("")
    A("나이 비율은 덩어리를 뺀 나머지를 나눈 값이다. 덩어리는 시즌 1 공식을 쓰지 않는다: 깨진 가루가 하류의 큰 물막이로 흘러가기 때문에(서사 ACT4) 기본 %s이고, 가루가 고이는 네 곳(물안개 둑·숫자 마당·아홉째 문·물막이 바닥)만 %s다. 동시 수 = 4 + 고리(상한 10). 줄 선 혼은 적 수에 넣지 않는다." % (
        pct(data["lump_base"]), pct(data["lump_base"] + data["lump_pool"])))
    A("")
    A("| 관할 | 구역 | 고리 | 갓 죽은 | 해 넘긴 | 오래된 | 덩어리 | 표지 | 동시 | 왜 |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for z in data["zones"]:
        tg = [("%s %s" % (data["tags"][k]["name"], pct(v))) for k, v in z["tags"].items()]
        if z["line_souls"]:
            tg.append("줄 선 혼 %d(장애물)" % z["line_souls"])
        m = z["mix"]
        A("| %s | %s | %d | %s | %s | %s | %s | %s | %d | %s |" % (
            z["jurisdiction"], z["zone"], z["ring"], pct(m["fresh"]), pct(m["year"]), pct(m["old"]), pct(m["lump"]),
            ", ".join(tg) or "—", z["concurrent"], z["why"]))
    A("")
    A("### F2-4. 보스 처결이 바꾸는 것")
    A("")
    A("| 처결 | 어디 | 바뀌는 것 |")
    A("|---|---|---|")
    for e in data["boss_effects"]:
        A("| %s | %s | %s |" % (e["when"], e["where"], e["effect"]))
    A("")
    A("### F2-5. 사나운 적이 나오는 조건")
    A("")
    A("시즌 1의 X1~X4(얼룩 셋·흐르는 얼룩·놓친 혼·업의 그늘)는 그대로 이어진다. 시즌 2에서 셋을 더한다. 모두 \"내가 깨뜨린 것\"에서 나온다.")
    A("")
    A("| 조건 | 언제 | 상태 | 왜 |")
    A("|---|---|---|---|")
    for f in data["fierce_s2"]:
        A("| %s %s | %s | %s | %s |" % (f["id"], f["name"], f["when"], f["status"], f["why"]))
    A("")
    A("### F2-6. 확인 요청")
    A("")
    A("| 누구 | 무엇 |")
    A("|---|---|")
    A("| QA | 시즌 2 덩어리 10%%/25%%(시즌 1 공식 대신) / 옛 차사 혼 맺힘 %d, 사슬 끌기 예고 0.8초 / 먹지기 쪽지 %d장 / X5 문턱 50·100·150 / X6 5%% / X7 흩어진 색 / 시즌 2는 오래된 혼(대기 4초)이 많아 X3 '놓친 혼'이 자주 켜질 수 있다 |" % (data["old_chasa_hp"], data["inkkeeper_notes"]))
    A("| 서사 | 서리 숙사의 '신참 서리 혼'은 싸우는 혼으로 봤다(서리 NPC와 따로) / 숫자 혼의 이름이 시즌 1 고향 관할에 따라 뜨는 규칙 / 옛 차사 혼이 사슬로 끌어당기는 연출 / B-13 천도 뒤 돌아선 혼 −10%p |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = build()
    with open(os.path.join(root, "data", "mobs_s2.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "planning")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "appendix-F2.md"), "w", encoding="utf-8") as f:
        f.write(md(data))
    for z in data["zones"]:
        print(z["zone"], z["mix"], z["concurrent"])
