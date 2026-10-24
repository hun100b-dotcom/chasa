# -*- coding: utf-8 -*-
"""
시즌 1 지역 동선 데이터 생성기 (기획서 부록 C의 단일 출처)

왜 이 파일이 있나:
  "오늘 밤 어디까지 갈 것인가"(기둥 3)는 결국 '걸어서 몇 초'의 문제다.
  구역마다 서낭당까지 몇 초인지, 어떤 보스를 천도하면 몇 초로 줄어드는지를
  한 표에서 계산해야 기획서·QA·코드가 같은 숫자를 본다.
  숫자를 바꿀 때는 이 파일만 고치고 다시 돌린다.

실행:
  python3 tools/route_s1.py [부록 마크다운을 쓸 폴더]
  → data/route_s1.json (코드·QA용 표) + <폴더>/appendix-C.md (기획서용 글)

단위:
  모든 거리는 '걸음 초'다. 이동 속도 9m/s(data/balance.json PLAYER_MOVE_SPEED)로
  싸움 없이 곧장 걸었을 때 걸리는 시간이다. 미터 = 초 × 9.
"""
import json
import os
import sys

MOVE_SPEED = 9.0  # m/s. balance.json PLAYER_MOVE_SPEED와 같아야 한다

# 막마다 정규 밤 길이(초). 첫 밤만 480초(튜토리얼, 서사 확정)
NIGHT_LEN = {1: 900, 2: 1050, 3: 1200}
FIRST_NIGHT = 480

# 고리(서낭당에서 몇 겹 바깥인가)마다 보상 배율과 덩어리 확률.
# balance.json MAP_REWARD_PER_RING(+25%/고리), MAP_LUMP_BASE(5%) + MAP_LUMP_PER_RING(+5%/고리)를 그대로 쓰되,
# 덩어리는 25%에서 멈춘다(바깥이 '파혼만 되는 곳'이 되지 않게).
REWARD_PER_RING = 0.25
LUMP_BASE, LUMP_PER_RING, LUMP_CAP = 0.05, 0.05, 0.25


def ring_reward(r):
    return 1 + REWARD_PER_RING * (r - 1)


def ring_lump(r):
    return min(LUMP_CAP, LUMP_BASE + LUMP_PER_RING * (r - 1))


# 천도 보상 중 '길'에 관한 것들. kind: shortcut(지름길, 비율로 줄임) / shelter(쉼터, 귀환 지점이 됨) / link(관할 사이 새 길)
# 서사 SCENARIO-MASTER 보스 표의 천도 보상을 그대로 옮겼다. 비율은 B-01(−17.5%)과 B-07(−15%, 서사 확인 10-24)이 확정.
TRAVEL_REWARDS = {
    "B-01": dict(kind="shortcut", name="나루 지름길", cut=0.175, status="확정",
                 note="물막이 골 강을 건너는 길. 물막이 골과 그 하류(⑤ 갯마을 강둑길)에 적용"),
    "B-02": dict(kind="shelter", name="폐당집 쉼터", status="확정(서사)",
                 note="동트기 전 여기에 닿아도 귀환 성공"),
    "B-06": dict(kind="shelter", name="산성 쉼터", status="확정(서사)",
                 note="③ 붉은재의 귀환 지점"),
    "B-07": dict(kind="shortcut", name="갱도 지름길", cut=0.15, status="확정(서사 10-24)",
                 note="④ 막장에서 ⑤ 포구로 이어지는 굴. ⑤로 가는 두 번째 길(B-01을 파혼해도 ⑤가 멀지 않게)"),
    "B-10": dict(kind="link", name="난파 여울 지름길", status="확정(서사)",
                 note="썰물을 기다리지 않고 ⑤↔⑥을 오간다. 서낭당 귀환은 줄지 않고, 한 밤에 두 관할을 돌 수 있게 된다"),
}

# 구역: (관할, 구역 이름, 고리, 서낭당까지 편도 걸음 초, 쉼터까지 초 {보스: 초}, 적용되는 지름길 [보스], 이 구역의 보스, 열리는 막)
ZONES = [
    ("①", "솔고개 마을", 1, 30, {}, [], None, 1),
    ("①", "보릿들", 1, 40, {"B-02": 30}, [], None, 1),
    ("①", "물막이 골", 2, 70, {"B-02": 25}, ["B-01"], "B-01 나루 영감", 1),
    ("①", "폐당집", 2, 80, {"B-02": 0}, [], "B-02 월화", 1),
    ("②", "장터거리", 1, 45, {}, [], None, 1),
    ("②", "동헌 터", 2, 70, {}, [], None, 1),
    ("②", "역병막", 2, 85, {}, [], "B-03 서 의원", 1),
    ("②", "무덤골", 3, 105, {}, [], "흑월 1차(처결 없음)", 1),
    ("③", "무너진 산성", 3, 125, {"B-06": 0}, [], "B-05 기수 대돌", 2),
    ("③", "화살골", 3, 135, {"B-06": 25}, [], None, 2),
    ("③", "군막 터", 4, 155, {"B-06": 30}, [], "B-06 이름 없는 장수", 2),
    ("③", "큰 무덤", 4, 165, {"B-06": 40}, [], None, 2),
    ("④", "광부촌", 3, 120, {}, [], "B-08 장부꾼 염씨", 2),
    ("④", "선탄장", 3, 135, {}, [], None, 2),
    ("④", "큰 갱도", 4, 160, {}, [], None, 2),
    ("④", "무너진 막장", 4, 180, {}, [], "B-07 갱도 반장 칠성", 2),
    ("⑤", "포구", 5, 215, {}, ["B-01", "B-07"], None, 3),
    ("⑤", "소금밭", 5, 225, {}, ["B-01", "B-07"], None, 3),
    ("⑤", "망부석 곶", 5, 245, {}, ["B-01", "B-07"], "B-09 망부석 아낙", 3),
    ("⑤", "난파 여울", 6, 265, {}, ["B-01", "B-07"], "B-10 만선호 선장", 3),
    ("⑥", "저잣거리", 5, 205, {}, [], None, 3),
    ("⑥", "큰 다리 밑", 5, 220, {}, [], "B-11 다리 밑 왕초", 3),
    ("⑥", "빈민 움막촌", 6, 240, {}, [], None, 3),
    ("⑥", "성문 밖", 6, 260, {}, [], "B-12 흑월 2차", 3),
]
ACT_OF = {"①": 1, "②": 1, "③": 2, "④": 2, "⑤": 3, "⑥": 3}


def best_return(base, shelters, shortcuts, tendo):
    """천도한 보스 집합(tendo)으로 귀환 걸음을 계산한다.
    지름길은 겹치지 않는다: 여러 길 중 가장 짧은 것 하나만 쓴다(천도 쏠림을 막는 규칙)."""
    cands = [base]
    for b in shortcuts:
        if b in tendo:
            cands.append(base * (1 - TRAVEL_REWARDS[b]["cut"]))
    for b, sec in shelters.items():
        if b in tendo:
            cands.append(sec)
    return round(min(cands))


def build():
    all_tendo = set(TRAVEL_REWARDS)
    rows = []
    for j, name, ring, base, shel, cuts, boss, act in ZONES:
        best = best_return(base, shel, cuts, all_tendo)
        night = NIGHT_LEN[ACT_OF[j]]
        rows.append(dict(
            jurisdiction=j, zone=name, ring=ring, act=ACT_OF[j],
            one_way_sec=base, one_way_m=round(base * MOVE_SPEED),
            best_return_sec=best,
            walk_share_base=round(base * 2 / night, 3),  # 왕복 걸음이 밤에서 차지하는 비율(천도 보상 없음)
            walk_share_best=round((base + best) / night, 3),  # 가는 길은 그대로, 돌아오는 길만 줄어든다
            reward_mult=ring_reward(ring), lump_chance=round(ring_lump(ring), 2),
            shelters={b: s for b, s in shel.items()}, shortcuts=cuts, boss=boss,
        ))
    return dict(
        _설명="tools/route_s1.py가 만든 파일. 직접 고치지 말고 생성기를 고친다. 단위는 걸음 초(9m/s).",
        move_speed=MOVE_SPEED, night_len=NIGHT_LEN, first_night=FIRST_NIGHT,
        ring=dict(reward_per_ring=REWARD_PER_RING, lump_base=LUMP_BASE, lump_per_ring=LUMP_PER_RING, lump_cap=LUMP_CAP),
        travel_rewards=TRAVEL_REWARDS, zones=rows,
    )


def pct(x):
    return "%d%%" % round(x * 100)


def md(data):
    L = []
    L.append("## 부록 C. 시즌 1 지역 동선")
    L.append("")
    L.append("기둥 3 \"오늘 밤 어디까지 갈 것인가\"가 성립하도록 시즌 1의 여섯 관할·스물네 구역을 어떻게 잇는지 정한다. 거리는 모두 **걸음 초**다. 이동 속도 9m/s로 싸움 없이 곧장 걸었을 때의 시간이고, 미터로는 ×9다. 값은 `data/route_s1.json`(생성기 `tools/route_s1.py`)과 같다.")
    L.append("")
    L.append("### C-1. 큰 그림")
    L.append("")
    L.append("허브는 끝까지 **서낭당 고개 하나**다(서사 확정). 동쪽이 ① 솔고개, 서쪽 고개 너머가 ② 검은여울이다. 2막 관할은 그 바깥에, 3막 관할은 가장 바깥에 있다. 막이 오를수록 밤이 길어지지만 길은 그보다 더 길어져서, 3막에는 걸음만으로 밤의 40%가 넘게 든다. 그 무게를 천도 보상(지름길·쉼터)이 덜어 준다.")
    L.append("")
    L.append("```")
    L.append("                 [④ 쇳골 광산] ── 갱도 지름길(B-07) ──┐")
    L.append("                      │ 산길                          ▼")
    L.append("[③ 붉은재]          [① 솔고개]── 물막이 골 ── 나루(B-01) ── 강둑길 ──[⑤ 갯마을 포구]")
    L.append("  산성 쉼터(B-06)     │   폐당집 쉼터(B-02)                              │")
    L.append("      │              │                                         난파 여울(B-10)")
    L.append("[② 검은여울] ─ 고개 ─ (서낭당 고개 · 허브)                                    │")
    L.append("      │ 큰길                                                                │")
    L.append("[⑥ 도성 아랫마을] ─────────────────── 해안 길(썰물) ─────────────────────────┘")
    L.append("```")
    L.append("")
    L.append("### C-2. 길의 규칙")
    L.append("")
    L.append("| 규칙 | 내용 | 왜 |")
    L.append("|---|---|---|")
    L.append("| 출발은 늘 서낭당 | 해 질 녘 명부를 받는 곳이 서낭당 나무뿐이라 밤은 언제나 허브에서 시작한다 | 서사 규칙(명부는 서낭당 가지에만 내려온다) |")
    L.append("| 밤에는 빨리 가기 없음 | 밤에는 걸어서만 간다. 낮에만 구역을 골라 바로 간다(부록 B) | 거리가 곧 위험이어야 \"어디까지\"가 고민이 된다 |")
    L.append("| 귀환 = 안전 지점 반경 안 | 서낭당(반경 4m, 장승 사이) 또는 열린 쉼터에 동트기 전 닿으면 성공. 못 닿으면 명부 밖 넋·엽전을 모두 잃고 명부 몫·성장·단서는 남는다 | 서사·밸런스 확정값 |")
    L.append("| 지름길은 겹치지 않는다 | 한 구역에 지름길이 둘 열려도 가장 짧은 길 하나만 쓴다(곱해서 줄지 않는다) | 천도를 많이 할수록 길이 끝없이 짧아지면 파혼이 오답이 된다 |")
    L.append("| 쉼터는 돌아오는 곳일 뿐 | 쉼터에서 다음 밤을 시작하지는 않는다. 동트기 안전 지점만 된다 | 출발까지 바꾸면 허브가 비고 거리의 긴장이 사라진다 |")
    L.append("| 바깥일수록 보상도, 덩어리도 | 고리마다 보상 +25%, 덩어리(파혼만 되는 혼) 확률 +5%p(최대 25%) | 멀리 갈수록 많이 얻지만 파혼할 일도 늘어난다 |")
    L.append("| 혼불 길잡이 | 남은 밤이 \"가장 가까운 안전 지점까지 걸음 × 1.5 + 30초\"보다 적어지면 혼불이 그쪽으로 기운다. 동트기 경고(30초 전)와 따로 온다 | 숫자를 안 보는 사람도 돌아설 때를 안다 |")
    L.append("")
    L.append("### C-3. 천도가 여는 길")
    L.append("")
    L.append("천도는 장기 이득(앞으로의 모든 밤), 파혼은 즉시 이득이라는 원칙(9절)을 길로 옮긴 것이다. 아래 다섯 보스는 천도하면 길이 바뀌고, 파혼하면 길은 그대로이되 엽전·장비를 바로 준다.")
    L.append("")
    L.append("| 보스 | 천도하면 열리는 길 | 무엇이 줄어드나 | 상태 |")
    L.append("|---|---|---|---|")
    for b, r in data["travel_rewards"].items():
        what = {"shortcut": "귀환 걸음 −%g%%" % (r.get("cut", 0) * 100), "shelter": "가까운 구역의 귀환 지점이 생김", "link": "한 밤에 두 관할"}[r["kind"]]
        L.append("| %s | %s | %s. %s | %s |" % (b, r["name"], what, r["note"], r["status"]))
    L.append("")
    L.append("**길이 하나로 막히지 않게.** ⑤ 갯마을로 가는 지름길은 둘이다(B-01 나루, B-07 갱도). 1막에서 나루 영감을 파혼한 플레이어도 2막 갱도 반장을 천도하면 ⑤가 거의 같은 만큼 가까워진다. 서사의 \"한 선택이 이야기를 막지 않는다\"는 규칙을 길에도 적용했다.")
    L.append("")
    L.append("### C-4. 구역 스물넷의 거리")
    L.append("")
    L.append("\"왕복 비율\"은 그 구역까지 갔다가 돌아오는 걸음이 그 막의 밤(1막 900초 · 2막 1050초 · 3막 1200초)에서 차지하는 몫이다. 왼쪽은 천도 보상이 없을 때, 오른쪽은 길에 관한 천도 보상을 모두 얻었을 때다.")
    L.append("")
    L.append("| 관할 | 구역 | 고리 | 편도 걸음 | 귀환(천도 보상 모두) | 왕복 비율 | 보상 배율 · 덩어리 | 보스 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for z in data["zones"]:
        L.append("| %s | %s | %d | %d초 (%dm) | %d초 | %s → %s | ×%.2f · %s | %s |" % (
            z["jurisdiction"], z["zone"], z["ring"], z["one_way_sec"], z["one_way_m"], z["best_return_sec"],
            pct(z["walk_share_base"]), pct(z["walk_share_best"]), z["reward_mult"], pct(z["lump_chance"]), z["boss"] or "—"))
    L.append("")
    L.append("### C-5. 막마다 \"오늘 밤 어디까지\"")
    L.append("")
    L.append("| 막 | 밤 | 가까운 밤 | 먼 밤 | 고민의 모양 |")
    L.append("|---|---|---|---|---|")
    L.append("| 1막 (①②) | 900초 | 솔고개 마을·장터거리: 왕복 7~10% | 무덤골: 왕복 23% | 거리는 아직 가볍다. 고민은 \"①로 갈까 ②로 갈까\". 폐당집 쉼터(B-02 천도)가 ① 바깥을 거의 공짜로 만든다 |")
    L.append("| 2막 (③④) | 1050초 | 산성·광부촌: 왕복 약 23% | 무너진 막장: 왕복 34% | ③은 쉼터(B-06)가 생기면 가까워지고, ④는 쉼터가 없다. \"쉼터 있는 ③을 돌까, 먼 ④를 칠까\" |")
    L.append("| 3막 (⑤⑥) | 1200초 | 저잣거리: 왕복 34% | 성문 밖·난파 여울: 왕복 43~44% | 가장 무겁다. ⑤는 지름길 둘 중 하나가 있으면 33~40%로 줄고, ⑥은 줄일 길이 없다(마지막 대결 앞의 긴장). 난파 여울 지름길(B-10)로 ⑤와 ⑥을 한 밤에 이어 돌 수 있다 |")
    L.append("")
    L.append("목표선(QA 확인 요청): 천도 보상 없이 가장 먼 구역 왕복이 밤의 **45% 이하**, 길 보상을 얻은 관할은 **40% 이하**. ⑥만은 일부러 줄일 길을 두지 않아 43%로 남긴다(시즌 마지막 대결 앞). 이 규칙은 **시즌 1 동선에만** 적용한다. 시즌 3에서 B-26 보상으로 ⑥ 아래층 지름길이 생긴다. 이동 속도 옵션(상한 +20%)을 끼면 성문 밖도 약 36%가 된다.")
    L.append("")
    L.append("### C-6. 구역의 안쪽")
    L.append("")
    L.append("- 구역 하나는 반경 약 18m의 뼈대 지형이다(balance.json MAP_ZONE_RADIUS). 뼈대는 손으로 짜고 안쪽 배치만 규칙으로 만든다(8절). 이 부록의 거리는 구역 중심 사이를 잰 것이다.")
    L.append("- 구역과 구역은 좁은 **목**(고갯길·둑길·골목)으로 잇는다. 목에는 혼이 적게 나오고 얼룩이 생기지 않는다. 돌아오는 길이 싸움 때문에 무한히 길어지지 않게 하는 장치다.")
    L.append("- 보스 구역에는 보스 자리와 별도로 **물러날 목**이 하나 있다. 그 목을 넘으면 보스전이 처음으로 돌아간다(부록 B-2).")
    L.append("")
    L.append("### C-7. 처결 필터 검사")
    L.append("")
    L.append("| 기능 | 천도와 파혼의 선택을 더 재미있게 만드는가 |")
    L.append("|---|---|")
    L.append("| 지름길·쉼터 | 보스 천도가 \"앞으로의 모든 밤\"을 넓힌다. 파혼은 지금 엽전·장비를 준다. 두 이득이 다른 축에 있어 한쪽이 늘 정답이 되지 않는다 |")
    L.append("| 지름길 겹치지 않음 | 천도를 많이 해도 길은 한 번만 짧아진다. 파혼 위주 플레이어와의 거리 차이가 일정 이상 벌어지지 않는다 |")
    L.append("| 바깥의 덩어리 | 멀리 갈수록 보상이 크지만 파혼할 수밖에 없는 혼도 많아진다. 업을 감수하고 멀리 갈지 고른다 |")
    L.append("| ⑤로 가는 두 길 | 한 번의 파혼이 뒷날의 길을 영영 막지 않는다 |")
    L.append("")
    L.append("### C-8. 맞출 것")
    L.append("")
    L.append("| 누구 | 무엇 |")
    L.append("|---|---|")
    L.append("| 서사 | 갱도 지름길 −15%(확정) / 쉼터는 귀환만, 밤은 늘 서낭당에서 시작(확정, 시즌 3 위층 쉼터도 같음) / ⑥에 줄일 길이 없는 것은 **시즌 1 동선에만**(확정: 시즌 3 B-26 보상으로 ⑥ 아래층 지름길이 생긴다) |")
    L.append("| QA | 막마다 왕복 비율 목표선 / 덩어리 상한 25% / 혼불 길잡이 공식 |")
    L.append("| 코드 | `data/route_s1.json`을 지도 데이터로 읽기, 귀환 판정에 쉼터 추가, 지름길 하나만 적용 |")
    L.append("| 아트 | 관할 사이 목(고갯길·둑길·갱도·해안 길)의 모습, 쉼터 표지(장승·돌무더기) |")
    return "\n".join(L)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = build()
    with open(os.path.join(root, "data", "route_s1.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "planning")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "appendix-C.md"), "w", encoding="utf-8") as f:
        f.write(md(data))
    for z in data["zones"]:
        print(z["zone"], z["one_way_sec"], z["best_return_sec"], z["walk_share_base"], z["walk_share_best"])
