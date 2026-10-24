# -*- coding: utf-8 -*-
"""
시즌 3 지역 동선 데이터 생성기 (기획서 부록 C-3의 단일 출처)

왜 이 파일이 있나:
  시즌 3 「백의 밤」은 새 땅이 아니라 이미 걸어 본 땅의 '아래층'(물 밑·땅 밑)이다.
  아래층은 물이 빠진 동안만 열리고 동틀 무렵 물이 다시 찬다(서사 ACT6 "물 빠진 밤").
  그래서 "오늘 밤 얼마나 깊이 내려갈까"(기둥 3)는
  위층 걸음(시즌 1·2 길) + 내려가기 + 아래층 걸음 + 다시 올라오기의 합이다.
  이 합을 한 표에서 계산해야 기획서·QA·코드가 같은 숫자를 본다.

실행:
  python3 tools/route_s3.py [부록 마크다운을 쓸 폴더]
  → data/route_s3.json + <폴더>/appendix-C3.md

출처:
  - 위층 걸음: tools/route_s1.py(①~⑥), tools/route_s2.py(⑦~⑩) — 같은 함수를 그대로 쓴다
  - 아래층 구역·보스·지름길: 서사 SCENARIO-ACT6·ACT7·ACT8 구역 표와 보스 표
  - QA 확정값: FLOOD_WARNING_TIME 30, FLOOD_LOSS_RATIO 0.5, B21_SHORTCUT_CUT 0.15,
    INK_SILT_SLOW 0.15, COMPASS_BACK_SLOW_MAX 0.1, SLOW_STACK_MAX 0.35
단위: 걸음 초(이동 속도 9m/s로 싸움 없이 곧장 걸은 시간). 미터 = 초 × 9.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route_s1 as S1
import route_s2 as S2

MOVE_SPEED = S1.MOVE_SPEED

# ── 밤과 물 ─────────────────────────────────────────────
# 시즌 2 마지막 막(1500초)에서 더 늘리지 않는다. 휴대폰 한 판 25분이 상한이라고 봤다(QA 확인 요청).
NIGHT_LEN = {6: 1500, 7: 1500, 8: 1500}
WATER_DROP = 30         # 밤이 시작되고 물이 빠져 아래층이 열리기까지(초). 위층을 걷는 동안 빠진다
FLOOD_WARNING = 30      # 물 차오름 30초 전 경고(QA 채택 FLOOD_WARNING_TIME)
FLOOD_LOSS = 0.5        # 아래층에서 물에 잠기면 그날 넋·엽전 절반 손실(QA 채택. 단서·장례 해금·도감은 보존)
DESCENT = 15            # 위층 → 아래층 내려가기(둑 허리·무너진 봉분·갱 옆 굴). 올라오기도 같다
RIVERBED = 150          # 물 빠진 강바닥으로 물막이 골 소 → ⑦ 줄 밑(시즌 2 강둑길과 같은 길이)
WELL_PASSAGE = 60       # ⑩ 첫 우물 밑 물길 → 물막이 골 소(서사 F70, B-30 눕히기 뒤 열림)
SILT_SLOW = 0.15        # ⑧ 먹 앙금 이동 −15%(QA 채택 INK_SILT_SLOW)
COMPASS_SLOW = 0.10     # 8막 사슬 나침반: 가장 깊은 곳에서 되돌아갈 때 최대 −10%(QA 채택)
RING_BY_ACT = {6: 9, 7: 10, 8: 11}   # 난이도 고리. 시즌 2 마지막(8)에 이어 막마다 한 칸

# 시즌 3 길 보상(서사 보스 표). kind: lower_cut(그 관할 아래층 걸음을 줄임) / link(관할 사이 아래층 길) / exit(돌아오는 새 길)
TRAVEL_REWARDS_S3 = {
    "B-21": dict(kind="riverbed_cut", name="소 밑 지름길", cut=0.15, status="QA 채택(B21_SHORTCUT_CUT)",
                 note="물막이 골 소 → ⑦ 줄 밑 강바닥 길 −15%. 시즌 1 B-01 나루 지름길(위층)과 구간이 달라 겹치지 않는다"),
    "B-22": dict(kind="lower_cut", name="곶 밑 지름길", cut=0.15, where="⑤", status="서사 확정 · 비율 제안",
                 note="⑤ 아래층 걸음 −15%"),
    "B-24": dict(kind="link", name="봉분 밑 지름길", where="③→④", status="서사 확정",
                 note="③ 아래층에서 ④ 아래층으로 바로. 한 밤에 두 관할 아래층"),
    "B-25": dict(kind="link", name="막장 지름길", where="④→⑤", status="서사 확정",
                 note="④ 아래층에서 ⑤ 아래층으로"),
    "B-26": dict(kind="link", name="무덤골 지름길", where="②→⑥", status="서사 확정",
                 note="사십 년 전 피난민이 걸었던 길. ② 아래층에서 ⑥ 아래층으로"),
    "B-27": dict(kind="link", name="성문 밖 지름길", where="⑥→8막 입구", status="서사 확정",
                 note="8막 ⑧ 아래층으로 바로 내려가는 길"),
    "B-28": dict(kind="lower_cut", name="먹 앙금 지름길", cut=0.15, where="⑧", status="서사 확정 · 비율 제안",
                 note="⑧ 아래층 걸음 −15%"),
    "B-29": dict(kind="lower_cut", name="빈 고을 지름길", cut=0.15, where="⑨", status="서사 확정 · 비율 제안",
                 note="⑨ 아래층 걸음 −15%"),
    "B-30": dict(kind="exit", name="첫 우물 지름길", where="⑩→물막이 골 소", status="서사 확정(F70)",
                 note="⑩ 바닥과 솔고개 물막이 골 소는 같은 물. ⑩ 아래층에서 서낭당 바로 아래로 올라온다"),
}

# 아래층 구역: (관할, 구역, 바로 위 구역(위층 이름), 아래층 걸음 초, 보스, 막, 낮 단서 형식)
# 위층 이름은 route_s1/route_s2의 구역 이름과 같아야 한다(거기서 위층 걸음을 가져온다).
ZONES = [
    ("①", "둑 밑", "보릿들", 20, None, 6, "거꾸로 장례(낮)"),
    ("①", "소 밑", "물막이 골", 30, "B-21 마지막 손님(윤 영감의 백)", 6, "거꾸로 장례(낮)"),
    ("⑤", "난파 여울 바닥", "난파 여울", 20, None, 6, "거꾸로 장례(낮)"),
    ("⑤", "곶 밑 바다굴", "망부석 곶", 30, "B-22 줄에 묶인 일곱", 6, "거꾸로 장례(낮)"),
    ("⑦", "줄 밑", "빈 나루 마을", 20, None, 6, "새벽 틈"),
    ("⑦", "닻 여울", "빈 나루 마을", 80, "B-23 물 밑 매듭", 6, "조건형(단서 없음)"),
    ("③", "큰 무덤 속", "큰 무덤", 30, "B-24 한 구덩이의 두 진", 7, "이름 새기는 장례(낮)"),
    ("③", "화살골 뿌리 밑", "화살골", 25, None, 7, "이름 새기는 장례(낮)"),
    ("④", "물 찬 갱도", "큰 갱도", 25, None, 7, "이름 새기는 장례(낮)"),
    ("④", "막힌 막장 안쪽", "무너진 막장", 35, "B-25 반장 칠성의 백", 7, "이름 새기는 장례(낮)"),
    ("②", "석회 구덩이", "무덤골", 25, "B-26 두 겹 구덩이", 7, "이름 새기는 장례(낮)"),
    ("②", "역병막 마루 밑", "역병막", 15, None, 7, "이름 새기는 장례(낮)"),
    ("⑥", "성문 밖 구덩이", "성문 밖", 30, "B-27 서생 이명의 백", 7, "이름 새기는 장례(낮)"),
    ("⑥", "다리 기초 밑", "큰 다리 밑", 20, None, 7, "이름 새기는 장례(낮)"),
    ("⑧", "숙사 밑", "서리 숙사", 20, None, 8, "거꾸로 명부(새벽 틈)"),
    ("⑧", "먹 앙금", "먹방", 30, "B-28 벼루 밑의 손", 8, "거꾸로 명부(새벽 틈)"),
    ("⑨", "아랫목", "빈 고을", 25, "B-29 백 년의 사잣밥 할미", 8, "거꾸로 명부(새벽 틈 또는 먹지기 흔적)"),
    ("⑨", "인장 굴 바닥", "인장 굴", 25, None, 8, "거꾸로 명부(새벽 틈 또는 먹지기 흔적)"),
    ("⑩", "사슬 무덤 밑", "사슬 무덤", 25, None, 8, "거꾸로 명부(새벽 틈)"),
    ("⑩", "첫 우물 밑", "우물터", 35, "B-30 첫 우물(어미의 백)", 8, "거꾸로 명부(새벽 틈)"),
    ("①", "물막이 골 소 가장 깊은 곳", "물막이 골", 40, "B-31 나의 백", 8, "결말 조건(단서 없음)"),
]

# 위층 쉼터(물 차오름 전에 닿으면 귀환 성공). 시즌 1·2 쉼터 + 서사 ACT6 "포구 등대"
EXTRA_SHELTERS = {"⑤": ("포구 등대", 215)}   # 서사 ACT6이 처음 이름을 붙였다. 위치는 포구(부록 C 포구 편도 215초)로 봤다


def upper(name, best):
    """서낭당 → 위층 구역 편도, 그리고 그 구역 → 가장 가까운 귀환 지점(서낭당·쉼터)."""
    for j, n, ring, base, shel, cuts, boss, act in S1.ZONES:
        if n == name:
            if not best:
                return base, base
            back = S1.best_return(base, shel, cuts, set(S1.TRAVEL_REWARDS))
            return base, back
    for j, n, ring, w, shel, boss, act, dawn in S2.ZONES:
        if n == name:
            go = S2.one_way(w, j, best, 2 if best else 1, not best)
            back = min([go] + list(shel.values())) if best else go
            return go, back
    raise KeyError(name)


def lower_walk(j, L, best):
    """아래층 걸음. 앙금(⑧)은 느리고, 지름길을 얻은 관할은 줄어든다."""
    w = L / (1 - SILT_SLOW) if j == "⑧" else L
    if best:
        for b, r in TRAVEL_REWARDS_S3.items():
            if r["kind"] == "lower_cut" and r.get("where") == j:
                w *= 1 - r["cut"]
    return w


def seventh_lower_go(best):
    """⑦ 아래층(줄 밑)까지: 배를 타고 빈 나루에서 내려가거나, 물막이 골 소에서 강바닥으로 걷거나 — 짧은 쪽."""
    by_boat, _ = upper("빈 나루 마을", best)
    by_boat += DESCENT
    hub = S2.HUB_TO_FERRY * (1 - S2.FERRY_CUT_B01) if best else S2.HUB_TO_FERRY
    bed = RIVERBED * (1 - TRAVEL_REWARDS_S3["B-21"]["cut"]) if best else RIVERBED
    by_bed = hub + DESCENT + bed
    return min(by_boat, by_bed), ("배" if by_boat <= by_bed else "강바닥")


def build():
    rows = []
    for j, name, above, L, boss, act, clue in ZONES:
        night = NIGHT_LEN[act]
        out = {}
        for tag, best in (("base", False), ("best", True)):
            if j == "⑦":
                go_top, how = seventh_lower_go(best)
                go = go_top + lower_walk(j, L, best)
                back = go
            else:
                up_go, up_back = upper(above, best)
                if j in EXTRA_SHELTERS:
                    up_back = min(up_back, EXTRA_SHELTERS[j][1])
                low = lower_walk(j, L, best)
                go = up_go + DESCENT + low
                back_low = low * (1 + COMPASS_SLOW) if act == 8 else low   # 8막: 사슬이 깊은 쪽으로 당긴다
                back = up_back + DESCENT + back_low
                how = "위층"
                # B-30 눕히기 뒤 ⑩ 아래층은 첫 우물 물길로 물막이 골 소에 올라온다(F70)
                if best and j == "⑩":
                    hub = S2.HUB_TO_FERRY * (1 - S2.FERRY_CUT_B01)
                    via_well = hub + DESCENT + WELL_PASSAGE + low
                    if via_well < go:
                        go, how = via_well, "첫 우물 물길"
                    back = min(back, hub + DESCENT + WELL_PASSAGE + back_low)
            out[tag] = (go, back, how)
        go_b, back_b, _ = out["base"]
        go_g, back_g, how_g = out["best"]
        # 아래층에 머물 수 있는 시간 = 밤 − 물 빠지기 − 가는 길 − 돌아오는 길 − 경고 여유
        stay_b = night - max(WATER_DROP, 0) - go_b - back_b - FLOOD_WARNING
        stay_g = night - max(WATER_DROP, 0) - go_g - back_g - FLOOD_WARNING
        rows.append(dict(
            jurisdiction=j, zone=name, above=above, lower_walk_sec=L, act=act, ring=RING_BY_ACT[act],
            reward_mult=S1.ring_reward(RING_BY_ACT[act]), boss=boss, clue_form=clue,
            one_way_sec=round(go_b), return_sec=round(back_b),
            one_way_best_sec=round(go_g), return_best_sec=round(back_g), best_route=how_g,
            walk_share_base=round((go_b + back_b) / night, 3),
            walk_share_best=round((go_g + back_g) / night, 3),
            stay_base_sec=round(stay_b), stay_best_sec=round(stay_g),
        ))
    return dict(
        _설명="tools/route_s3.py가 만든 파일. 직접 고치지 말고 생성기를 고친다. 단위는 걸음 초(9m/s).",
        night_len=NIGHT_LEN, water_drop=WATER_DROP, flood_warning=FLOOD_WARNING, flood_loss=FLOOD_LOSS,
        descent=DESCENT, riverbed=RIVERBED, well_passage=WELL_PASSAGE, silt_slow=SILT_SLOW,
        compass_slow=COMPASS_SLOW, ring_by_act=RING_BY_ACT, extra_shelters=EXTRA_SHELTERS,
        travel_rewards=TRAVEL_REWARDS_S3, zones=rows,
    )


def pct(x):
    return "%d%%" % round(x * 100)


def md(data):
    L = []
    A = L.append
    A("## 부록 C-3. 시즌 3 지역 동선 (아래층)")
    A("")
    A("시즌 3 「백의 밤」은 새 땅이 아니라 이미 걸은 땅의 **아래층**(물 밑·땅 밑)이다. 해가 지면 물이 빠져 아래층이 열리고, 동틀 무렵 물이 다시 찬다(서사 ACT6 \"물 빠진 밤\"). 그래서 한 밤의 걸음은 **위층 길(시즌 1·2와 같다) + 내려가기 + 아래층 걸음 + 다시 올라오기**다. 거리는 걸음 초(9m/s), 값은 `data/route_s3.json`(생성기 `tools/route_s3.py`)과 같다. 위층 걸음은 부록 C·C-2의 생성기를 그대로 불러 쓴다.")
    A("")
    A("### C3-1. 물 빠진 밤의 시계")
    A("")
    A("| 항목 | 값 | 왜 |")
    A("|---|---|---|")
    A("| 밤 길이 | 6·7·8막 모두 %d초 | 시즌 2 마지막과 같다. 휴대폰 한 판 25분을 넘기지 않는다(제안) |" % data["night_len"][6])
    A("| 물 빠지기 | 밤 시작 %d초 뒤 아래층이 열린다 | 위층을 걷는 동안 빠지므로 기다림이 거의 없다(제안) |" % data["water_drop"])
    A("| 물 차오름 경고 | %d초 전 | QA 채택(FLOOD_WARNING_TIME). 동트기 경고와 같은 값 |" % data["flood_warning"])
    A("| 아래층에서 잠기면 | 그날 넋·엽전 %s 손실, 단서·장례 해금·도감은 보존 | QA 채택(FLOOD_LOSS_RATIO) |" % pct(data["flood_loss"]))
    A("| 내려가기·올라오기 | 각 %d초 | 둑 허리·무너진 봉분·갱 옆 굴을 타고 내려간다(제안) |" % data["descent"])
    A("| 8막 되돌아오기 | 아래층 걸음 +%s | 사슬 나침반이 깊은 쪽으로 당긴다(QA 채택 COMPASS_BACK_SLOW_MAX) |" % pct(data["compass_slow"]))
    A("| ⑧ 먹 앙금 | 아래층 걸음 ÷ 0.85 | 발목까지 빠진다(QA 채택 INK_SILT_SLOW −15%) |")
    A("| ⑦ 아래층 가는 길 | 배(시즌 2 길)와 물 빠진 강바닥(물막이 골 소에서 %d초) 중 짧은 쪽 | 강이 마르는 시즌이라 걸어서도 간다 |" % data["riverbed"])
    A("| 고리(난이도) | 6막 9 · 7막 10 · 8막 11 | 시즌 2(6~8)에 이어 막마다 한 칸. 보상 배율 ×%.2f~×%.2f |" % (S1.ring_reward(9), S1.ring_reward(11)))
    A("")
    A("### C3-2. 구역별 걸음")
    A("")
    A("\"보상 없음\"은 시즌 1·2 길 보상도 시즌 3 지름길도 없는 경우, \"보상 전부\"는 시즌 1·2 길 보상(나루 지름길·배 두 척·쉼터·⑨ 지도)과 시즌 3 지름길을 모두 얻은 경우다. **머물 시간** = 밤 − 물 빠지기 − 가는 길 − 돌아오는 길 − 경고 30초. 이 시간 안에서 싸우고 줍는다.")
    A("")
    A("| 막 | 관할 | 아래층 구역 | 위층 | 편도(없음→전부) | 왕복 비율 | 머물 시간 | 가장 빠른 길 | 보스 | 단서 형식 |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for z in data["zones"]:
        A("| %d | %s | %s | %s | %d → %d초 | %s → %s | %d → %d초 | %s | %s | %s |" % (
            z["act"], z["jurisdiction"], z["zone"], z["above"], z["one_way_sec"], z["one_way_best_sec"],
            pct(z["walk_share_base"]), pct(z["walk_share_best"]), z["stay_base_sec"], z["stay_best_sec"],
            z["best_route"], z["boss"] or "—", z["clue_form"]))
    A("")
    far = max(data["zones"], key=lambda z: z["walk_share_base"])
    A("가장 먼 곳은 %s %s다(보상 없음 왕복 %s, 머물 시간 %d초). 그래도 머물 시간이 보스 한 판(5~8분)보다 길어 막히지 않는다." % (
        far["jurisdiction"], far["zone"], pct(far["walk_share_base"]), far["stay_base_sec"]))
    A("")
    A("### C3-3. 시즌 3 길 보상")
    A("")
    A("| 보스 | 이름 | 종류 | 효과 | 상태 |")
    A("|---|---|---|---|---|")
    kinds = {"riverbed_cut": "강바닥 길 단축", "lower_cut": "아래층 걸음 단축", "link": "아래층 연결", "exit": "새 귀환 길"}
    for b, r in data["travel_rewards"].items():
        eff = r["note"]
        if "cut" in r:
            eff = "−%s. %s" % (pct(r["cut"]), r["note"])
        A("| %s 눕히기 | %s | %s | %s | %s |" % (b, r["name"], kinds[r["kind"]], eff, r["status"]))
    A("")
    A("**첫 우물 지름길(B-30)이 시즌 3 동선의 끝맺음이다.** ⑩ 아래층은 시즌 2 길로는 서낭당에서 가장 멀다. 그런데 B-30을 눕히면 ⑩ 바닥이 솔고개 물막이 골 소와 이어져(F70), 게임에서 가장 먼 땅이 서낭당 바로 아래가 된다. 최종 보스 B-31(물막이 골 소)도 그래서 서낭당 가까이에 있다 — 첫 밤의 그 나루로 돌아온다.")
    A("")
    A("**비켜서는 백**(7·8막): 시즌 1·2에서 천도한 사람의 백은 스스로 일어나 비켜서고, 그 자리에 굴이 열려 아래층 지름길이 된다(서사 ACT7). 표에는 넣지 않았다(사람마다 다르다). 시즌 3부터 시작한 기본 상태는 약 절반이 비켜선다(QA 채택 BAEK_SKIP_RATIO_DEFAULT 0.5).")
    A("")
    A("### C3-4. 확인 요청")
    A("")
    A("| 누구 | 무엇 |")
    A("|---|---|")
    A("| QA | 밤 길이 1500초 유지(더 늘리지 않음) / 물 빠지기 30초 / 내려가기 15초 / 강바닥 150초·B-21 −15%% 적용 구간 / 첫 우물 물길 60초 / 곶 밑·먹 앙금·빈 고을 지름길 −15%% / 고리 9·10·11 |")
    A("| 서사 | '포구 등대' 쉼터를 포구 자리로 봤다 / ⑦ 아래층을 강바닥으로도 걸어갈 수 있다(물이 빠지는 시즌) / 물막이 골 소의 B-31 자리가 서낭당 가까이라는 것(첫 밤의 나루로 돌아옴) |")
    return "\n".join(L).replace("%%", "%") + "\n"


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = build()
    with open(os.path.join(root, "data", "route_s3.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "planning")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "appendix-C3.md"), "w", encoding="utf-8") as f:
        f.write(md(data))
    for z in data["zones"]:
        print(z["act"], z["jurisdiction"], z["zone"], z["one_way_sec"], z["one_way_best_sec"],
              z["walk_share_base"], z["walk_share_best"], z["stay_base_sec"], z["best_route"])
