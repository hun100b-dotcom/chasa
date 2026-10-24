# -*- coding: utf-8 -*-
"""
시즌 2 지역 동선 생성기 (기획서 부록 C-2의 단일 출처, 부록 C의 확장)

왜 이 파일이 있나:
  시즌 2(4~5막, ⑦~⑩)는 이승과 저승의 경계라 서낭당에서 아주 멀다.
  그래도 "밤은 늘 서낭당에서 시작"(서사 확정)이므로, 걸음만으로는 밤이 다 길에 쓰인다.
  서사가 정한 "배 한 척 → 두 척(B-13 천도, ⑦~⑩ 귀환 단축)"을 실제 숫자로 바꿔
  '오늘 밤 어디까지 갈 것인가'가 시즌 2에서도 성립하는지 계산한다.

실행:
  python3 tools/route_s2.py [부록 마크다운을 쓸 폴더]
  → data/route_s2.json + <폴더>/appendix-C2.md

단위: 걸음 초(9m/s). 미터 = 초 × 9.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_s1 import MOVE_SPEED, ring_reward, ring_lump, TRAVEL_REWARDS as S1_REWARDS

NIGHT_LEN = {4: 1350, 5: 1500}     # 1~3막(900/1050/1200)에 이어 150초씩. QA 확인 요청
DAWN_GAP = 300                      # 새벽 틈 5분(서사 ACT4, QA 유지). 밤 마지막 300초 안에 들어 있다(밤에 더해지지 않음)
CLUE_TIME = 60                      # 새벽 틈에 단서 셋을 줍는 데 드는 시간(동사 셋 + 사이 걸음, 부록 B 기준 어림)

HUB_TO_FERRY = 70                   # 서낭당 → 물막이 골 나루(부록 C 물막이 골 편도와 같다)
FERRY_CUT_B01 = S1_REWARDS["B-01"]["cut"]  # 시즌 1에서 B-01을 천도했으면 이 구간이 −17.5%
BOAT_RIDE = 45                      # 사공의 배: 물막이 골 나루 ↔ ⑦ 빈 나루 마을
BOAT_INTERVAL = {1: 60, 2: 30}      # 배 한 척이면 60초마다, 두 척(B-13 천도)이면 30초마다 온다
BANK_WALK = 150                     # 배를 안 타고 강둑길로 걸으면 물막이 골 나루 → 빈 나루 마을


def boat_leg(boats):
    """배 구간 = 평균 기다림(간격의 절반) + 타는 시간."""
    return BOAT_INTERVAL[boats] / 2 + BOAT_RIDE


# 구역: (관할, 구역, 고리, 빈 나루 마을에서 걸음 초, 쉼터까지 초 {보스: 초}, 보스, 막, 새벽 틈 있나)
# 구역 이름은 서사 막 문서(ACT4·ACT5)를 따랐다. MASTER §2의 ⑨·⑩ 이름과 다르다(확인 요청).
ZONES = [
    ("⑦", "갈대늪", 6, 20, {}, None, 4, True),
    ("⑦", "빈 나루 마을", 6, 0, {}, "B-13 줄의 맨 앞 노인", 4, True),
    ("⑦", "먹물 여울", 7, 40, {}, None, 4, True),
    ("⑦", "물안개 둑", 7, 60, {}, "B-14 돌아선 혼들의 덩어리", 4, True),
    ("⑧", "서리 숙사", 7, 70, {}, None, 4, True),
    ("⑧", "먹방", 7, 85, {}, "B-16 벼루지기", 4, True),
    ("⑧", "문서 창고", 8, 100, {}, "B-15 숫자를 처음 쓴 서리", 4, True),
    ("⑧", "숫자 마당", 8, 110, {}, None, 4, True),
    ("⑨", "빈 고을", 8, 115, {"B-17": 0}, None, 5, False),
    ("⑨", "아홉째 문", 8, 125, {"B-17": 10}, "B-17 아홉째 문지기", 5, False),
    ("⑨", "도장 없는 장터", 8, 135, {"B-17": 20}, None, 5, False),
    ("⑨", "인장 굴", 8, 145, {"B-17": 30}, "B-18 인을 훔친 혼", 5, False),
    ("⑩", "처음 마을", 8, 145, {"B-17": 30}, None, 5, True),
    ("⑩", "사슬 무덤", 8, 155, {"B-17": 40}, None, 5, True),
    ("⑩", "우물터", 8, 165, {"B-17": 50}, "B-19 첫 차사", 5, True),
    ("⑩", "물막이 바닥", 8, 175, {"B-17": 60}, "B-20 큰 물막이", 5, True),
]

# 시즌 2의 '길' 보상(서사 보스 표). 시즌 1의 B-01 나루 지름길도 계속 쓰인다.
TRAVEL_REWARDS_S2 = {
    "B-01": dict(kind="carry", name="나루 지름길(시즌 1)", note="서낭당 → 물막이 골 나루 구간 −17.5%. 시즌 2 길목 컷신에서 나룻배가 다리처럼 이어진다", status="확정(서사)"),
    "B-13": dict(kind="boat", name="배 두 척", note="사공의 배가 30초마다 온다(평균 기다림 30 → 15초)", status="서사 확정 · 간격은 제안"),
    "B-17": dict(kind="shelter", name="빈 관할 쉼터", note="⑨ 빈 고을이 귀환 지점이 된다. ⑨·⑩ 어디서든 여기까지만 오면 된다", status="서사 확정 · 위치는 제안"),
}

# ⑨ 기억 지도(서사 ACT5): 지도가 없는 땅. 천도한 혼의 기억이 지형을 그려 준다.
# 지도가 비어 있으면 ⑨ 안에서 걷는 길이 1.2배(헤맨다). 천도로 지도가 다 그려지면 1.0배.
LOST_MULT = 1.2
NINTH_ENTRY = 110   # ⑨는 빈 나루 마을에서 110초 지점(숫자 마당)부터 시작한다


def one_way(w, j, b01, boats, lost):
    """서낭당 → 구역 편도. 배 구간과 강둑길 중 짧은 쪽."""
    ferry = HUB_TO_FERRY * (1 - FERRY_CUT_B01) if b01 else HUB_TO_FERRY
    mid = min(boat_leg(boats), BANK_WALK)
    inner = w
    if j in ("⑨", "⑩") and lost:
        inner = NINTH_ENTRY + (w - NINTH_ENTRY) * LOST_MULT
    return ferry + mid + inner


def build():
    rows = []
    for j, name, ring, w, shel, boss, act, dawn in ZONES:
        night = NIGHT_LEN[act]
        go = one_way(w, j, False, 1, True)
        back_base = go
        # 보상을 모두 얻었을 때: B-01·B-13 천도, ⑨ 지도 완성, B-17 쉼터
        go_best = one_way(w, j, True, 2, False)
        back_best = min([go_best] + [s for b, s in shel.items()])
        dawn_ok_base = dawn and back_base <= DAWN_GAP - CLUE_TIME
        dawn_ok_best = dawn and back_best <= DAWN_GAP - CLUE_TIME
        rows.append(dict(
            jurisdiction=j, zone=name, ring=ring, act=act, boss=boss,
            from_ferry_village=w, one_way_sec=round(go), one_way_best_sec=round(go_best),
            return_best_sec=round(back_best),
            walk_share_base=round((go + back_base) / night, 3),
            walk_share_best=round((go_best + back_best) / night, 3),
            reward_mult=ring_reward(ring), lump_chance=round(ring_lump(ring), 2),
            dawn_gap=dawn, dawn_clues_and_return_base=dawn_ok_base, dawn_clues_and_return_best=dawn_ok_best,
            shelters=shel,
        ))
    return dict(
        _설명="tools/route_s2.py가 만든 파일. 직접 고치지 말고 생성기를 고친다. 단위는 걸음 초(9m/s).",
        night_len=NIGHT_LEN, dawn_gap=DAWN_GAP, clue_time=CLUE_TIME,
        hub_to_ferry=HUB_TO_FERRY, boat_ride=BOAT_RIDE, boat_interval=BOAT_INTERVAL, bank_walk=BANK_WALK,
        lost_mult=LOST_MULT, travel_rewards=TRAVEL_REWARDS_S2, zones=rows,
    )


def pct(x):
    return "%d%%" % round(x * 100)


def md(data):
    L = []
    A = L.append
    A("## 부록 C-2. 시즌 2 지역 동선 (부록 C 확장)")
    A("")
    A("시즌 2의 ⑦~⑩은 이승과 저승의 경계라 서낭당에서 아주 멀다. 그래도 밤은 늘 서낭당에서 시작한다(서사 확정). 걸음만으로 가면 밤이 길에 다 쓰이므로, 서사가 정한 **사공의 배**(한 척 → B-13 천도 시 두 척)를 이동 수단으로 쓴다. 값은 `data/route_s2.json`(생성기 `tools/route_s2.py`)과 같다.")
    A("")
    A("### C2-1. 길의 짜임")
    A("")
    A("```")
    A("[서낭당] ─ 70초(B-01 천도 시 58초) ─ [① 물막이 골 나루]")
    A("                                        │ 사공의 배: 기다림 평균 30초(두 척이면 15초) + 45초")
    A("                                        │ 또는 강둑길 걸어서 150초(기다림 없음)")
    A("                                   [⑦ 빈 나루 마을] ─ 갈대늪 · 먹물 여울 · 물안개 둑")
    A("                                        │ 하류로 걸어서")
    A("                                   [⑧ 명부전 담장 밖] 70~110초")
    A("                                        │")
    A("                                   [⑨ 빈 관할] 115~145초 ★B-17 쉼터(빈 고을)")
    A("                                        │")
    A("                                   [⑩ 열째 관할] 145~175초 (빈 나루 마을에서)")
    A("```")
    A("")
    A("| 규칙 | 값 | 왜 |")
    A("|---|---|---|")
    A("| 밤 길이 | 4막 %d초 · 5막 %d초 | 1~3막(900·1050·1200)에 이어 150초씩 |" % (NIGHT_LEN[4], NIGHT_LEN[5]))
    A("| 사공의 배 | 물막이 골 나루 ↔ 빈 나루 마을, 타는 시간 %d초, 한 척이면 %d초마다 · 두 척이면 %d초마다 | B-13 천도 보상 \"⑦~⑩ 귀환 단축\"(서사)을 숫자로. 배를 기다릴지 강둑길로 걸을지가 작은 선택이 된다 |" % (BOAT_RIDE, BOAT_INTERVAL[1], BOAT_INTERVAL[2]))
    A("| 강둑길 | %d초, 기다림 없음 | 배가 막 떠났을 때의 대안. 평균으로는 배가 빠르다 |" % BANK_WALK)
    A("| 나루 지름길(시즌 1 B-01) | 서낭당 → 나루 −17.5% | 시즌 1의 천도가 시즌 2에서도 갚는다(시즌 사이 넘어가는 값: 보스 처결 결과) |")
    A("| ⑨ 기억 지도 | 지도가 비어 있으면 ⑨·⑩ 안의 걸음 ×%.1f, 천도한 혼의 기억이 지도를 그리면 ×1.0 | 서사 ACT5 \"길을 찾으려면 천도해야 한다\" |" % LOST_MULT)
    A("| 빈 관할 쉼터(B-17 천도) | ⑨ 빈 고을이 귀환 지점. ⑨는 0~30초, ⑩은 30~60초 | 시즌 2 마지막 관할을 \"갈 만한 곳\"으로 만드는 천도 보상 |")
    A("| 새벽 틈 | 밤의 마지막 %d초. 적이 더 일어나지 않고 ⑦⑧⑩에서 단서 동사가 열린다. ⑨에는 없다 | 서사 ACT4. 밤에 더해지는 시간이 아니라 밤 안에 있다(QA: 지름길과 겹치지 않게). 단서를 줍는 데 쓴 시간만큼 귀환이 빠듯해진다 — 낮을 건너뛰는 값과 같은 자리 |" % DAWN_GAP)
    A("")
    A("### C2-2. 구역별 거리")
    A("")
    A("\"보상 없음\"은 시즌 1의 B-01도 시즌 2의 길 보상도 없을 때(배 한 척, ⑨ 지도 빈칸), \"보상 다\"는 B-01·B-13·B-17 천도와 ⑨ 지도 완성일 때다. \"새벽 틈\"은 단서 셋(약 %d초)을 줍고도 동트기 전에 돌아올 수 있는지다." % CLUE_TIME)
    A("")
    A("| 관할 | 구역 | 고리 | 편도(보상 없음) | 귀환(보상 다) | 왕복 비율 없음 → 다 | 보상 배율 · 덩어리 | 새벽 틈 단서+귀환 | 보스 |")
    A("|---|---|---|---|---|---|---|---|---|")
    for z in data["zones"]:
        if not z["dawn_gap"]:
            dawn = "새벽 틈 없음"
        else:
            dawn = ("○" if z["dawn_clues_and_return_base"] else "×") + " → " + ("○" if z["dawn_clues_and_return_best"] else "×")
        A("| %s | %s | %d | %d초 | %d초 | %s → %s | ×%.2f · %s | %s | %s |" % (
            z["jurisdiction"], z["zone"], z["ring"], z["one_way_sec"], z["return_best_sec"],
            pct(z["walk_share_base"]), pct(z["walk_share_best"]), z["reward_mult"], pct(z["lump_chance"]),
            dawn, z["boss"] or "—"))
    A("")
    A("### C2-3. 막마다 무게")
    A("")
    zs = data["zones"]
    def share(name, key):
        return pct([z for z in zs if z["zone"] == name][0][key])
    A("| 막 | 밤 | 가까운 곳 | 먼 곳 | 읽는 법 |")
    A("|---|---|---|---|---|")
    A("| 4막 (⑦⑧) | %d초 | 빈 나루 마을: 왕복 %s | 숫자 마당: 왕복 %s | 배를 탈지 걸을지, 새벽 틈에 단서를 주울지가 고민. B-13(배 두 척)이 ⑦⑧ 전체를 가볍게 한다 |" % (
        NIGHT_LEN[4], share("빈 나루 마을", "walk_share_base"), share("숫자 마당", "walk_share_base")))
    A("| 5막 (⑨⑩) | %d초 | 빈 고을: 왕복 %s | 물막이 바닥: 왕복 %s → B-17 쉼터 뒤 %s | ⑨에서 천도하지 않으면 지도가 비어 헤매고, B-17을 천도하면 ⑩이 가까워진다. 시즌 2 마지막 대결 앞의 무게는 ⑥(43%%)과 비슷하게 맞췄다 |" % (
        NIGHT_LEN[5], share("빈 고을", "walk_share_base"), share("물막이 바닥", "walk_share_base"), share("물막이 바닥", "walk_share_best")))
    A("")
    A("새벽 틈과 쉼터가 맞물린다: ⑩은 쉼터 없이는 새벽 틈에 단서를 줍고 돌아올 수 없고, B-17을 천도해 쉼터가 생기면 가능해진다. ⑨는 새벽이 오지 않아(서사) 단서가 먹지기의 흔적으로 대신 나온다.")
    A("")
    A("### C2-4. 확인 요청")
    A("")
    A("| 누구 | 무엇 |")
    A("|---|---|")
    A("| 서사 | 사공의 배가 차사를 **물막이 골 나루까지 태워 돌아오는 것**(새 설정: 사공은 산 혼만이 아니라 일하는 차사도 실어 나른다) / ⑨·⑩ 구역 이름이 MASTER §2(인 없는 마을·거꾸로 선 장승길·빈 관아·인의 구덩이 / 첫 나루·사슬 무덤·명부의 바닥·큰 물막이)와 ACT5(빈 고을·아홉째 문·도장 없는 장터·인장 굴 / 처음 마을·사슬 무덤·우물터·물막이 바닥)가 다르다. 이 부록은 ACT5를 따랐다 / 빈 관할 쉼터 위치를 빈 고을로 둔 것 |")
    A("| QA | 밤 길이 1350·1500 / 배 간격 60·30초, 타는 시간 45초 / 강둑길 150초 / ⑨ 헤맴 ×1.2 / 새벽 틈을 밤 안에 두는 것 / 물막이 바닥 보상 없음 왕복 45% / B-17 쉼터가 ⑩ 왕복을 절반 가까이 줄이는데, B-17 파혼 보상(문지기의 열쇠)이 그만큼 매력 있는지 |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = build()
    with open(os.path.join(root, "data", "route_s2.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "planning")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "appendix-C2.md"), "w", encoding="utf-8") as f:
        f.write(md(data))
    for z in data["zones"]:
        print(z["zone"], z["one_way_sec"], z["return_best_sec"], z["walk_share_base"], z["walk_share_best"], z["dawn_clues_and_return_base"], z["dawn_clues_and_return_best"])
