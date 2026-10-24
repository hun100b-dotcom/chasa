#!/usr/bin/env python3
# QA 시뮬: 기획서 부록 B-5 엽전 흐름과 다시 굴리기 비용 곡선 검증.
# 왜? 엽전이 장비로 끝없이 빨려 들어가 파혼 쪽 성장이 천도 쪽을 앞지르는지(기획 의도: 비용이 오르는 이유) 확인한다.
# 사용: python3 tools/balance_sim_economy.py
import json, random, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = {k: v['value'] for k, v in json.load(open(os.path.join(ROOT, 'data', 'balance.json'), encoding='utf-8')).items()}

PAHON_COIN = B['PAHON_COIN']                      # 일반 파혼 엽전
base, step, mx = B['REROLL_BASE'], B['REROLL_STEP'], B['REROLL_MAX']
def cost(n): return min(mx, base + step * n)       # n번 굴린 물건의 다음 굴림 비용

print("== 다시 굴리기 비용 곡선 (같은 물건)")
cum = 0
for n in range(0, 12):
    cum += cost(n)
    print(f"  {n+1}번째 {cost(n):>3} / 누적 {cum}")

# 원하는 옵션 종류(8종 중 이미 가진 것 제외)가 나올 때까지 굴리는 횟수 기대값. 옵션 3개 보유 → 후보 5종 중 원하는 1종: p=1/5
def expected_cost(opts_owned, trials=20000):
    cands = 8 - opts_owned; tot = 0; tot_n = 0
    for _ in range(trials):
        n = 0; c = 0
        while True:
            c += cost(n); n += 1
            if random.randrange(cands) == 0: break
        tot += c; tot_n += n
    return tot_n / trials, tot / trials
random.seed(1)
print("== 원하는 옵션 한 줄을 맞추는 데 드는 기대 굴림·엽전 (옵션 N개 보유 중)")
for k in (1, 2, 3):
    n, c = expected_cost(k)
    print(f"  보유 {k}개: 평균 {n:.1f}번, 엽전 {c:.0f}")

print("== 한 밤 엽전 수입 vs 위 비용 (기획 목표: 파혼 100~150 / 반반 60~80 / 천도 30~50)")
# 밤 길이 480초(첫 밤), 파혼 한 번 평균 처리 시간 가정(걸어 이동·때림·R). 보스 파혼 30.
for name, pahon, boss in (("파혼 위주", 22, 0), ("반반", 12, 0), ("천도 위주", 5, 0)):
    income = pahon * PAHON_COIN + boss
    n, c = expected_cost(3)
    print(f"  {name}: 파혼 {pahon}회 → 엽전 {income:.0f} → 한 줄 맞추기({c:.0f})까지 {c/income:.1f}밤")
print("  (보스 파혼 +", B['BOSS_PAHON_COIN'], "엽전은 밤당 1회 한정이라 별도)")

# 광석: 풀기만으로 매듭 올리기 광석을 모을 때 (드롭 35%·무릎 꿇은 혼 N마리)
drop = B['DROP_CHANCE']
print("== 광석 수급: 풀기 광석(흔한1·손본3·귀한8) 대 매듭 올리기 필요량(3 / 10)")
rare, crafted = B['DROP_RARITY_RARE'], B['DROP_RARITY_CRAFTED']
avg_ore = rare * 8 + crafted * 3 + (1 - rare - crafted) * 1
for kneel in (10, 20, 30):
    drops = kneel * drop
    print(f"  무릎 꿇린 혼 {kneel} → 드롭 {drops:.1f}개 → 광석 약 {drops*avg_ore:.0f}")
