#!/usr/bin/env python3
"""
B-03 서 의원(기록 원형) 바닥 번호 칸 패턴 — 회피 가능성·약점 창 시뮬 (QA, 가정 명시)
가정(아트 시트 P2-041 원문을 못 받아서 제안 요약만 사용): 5×5 칸, 예고 0.8초, 약점 3초.
모르는 값은 인자로 바꿔 돌릴 수 있게 둔다: 칸 한 변(m), 한 번에 터지는 칸 수, 반응 시간, 플레이어 속도.
출력: 한 번에 터지는 칸 수별 '맞지 않을 확률'. 플레이어 위치는 무작위.
"""
import random, math, sys
CELL = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
REACT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25   # 사람 반응 시간(초)
SPEED = 9.0                                                  # PLAYER_MOVE_SPEED
WARN = 0.8
N = 5
reach = max(0.0, (WARN - REACT) * SPEED)  # 반응 뒤 움직일 수 있는 거리
def safe_prob(k, trials=20000):
    ok = 0
    for _ in range(trials):
        cells = [(i, j) for i in range(N) for j in range(N)]
        bad = set(random.sample(cells, k))
        px, py = random.uniform(0, N * CELL), random.uniform(0, N * CELL)
        # 도달 가능한 안전 칸이 있나(칸 중심까지 거리 - 칸 반크기 ≤ reach 로 근사)
        surv = False
        for (i, j) in cells:
            if (i, j) in bad: continue
            cx, cy = (i + .5) * CELL, (j + .5) * CELL
            d = max(0.0, math.hypot(cx - px, cy - py) - CELL * 0.5 + 0.5)  # 몸 반지름 0.5 보정
            if d <= reach: surv = True; break
        ok += surv
    return ok / trials
print(f"칸 {CELL}m, 반응 {REACT}s, 예고 {WARN}s → 반응 후 이동 가능 거리 {reach:.2f}m")
for k in (5, 8, 10, 12, 15, 18, 20):
    print(f"  한 번에 {k:2d}칸 터짐 → 피할 확률 {safe_prob(k)*100:5.1f}%")
# 약점 창: 3초 동안 철삭·육모방망이 평균 피해 (콤보 표 기준)
chain = (12 + 14 + 30) / (0.09 + .15 + .13 + .08 + .15 + .13 + .16 + .3 + .36)
mace = (18 + 20 + 38) / (0.16 + .18 + .22 + .16 + .18 + .22 + .28 + .22 + .45)
print(f"초당 피해: 철삭 {chain:.1f}, 육모방망이 {mace:.1f} (명중 100% 가정)")
for hp in (600, 900, 1200):
    print(f"  보스 맺힘 {hp}: 약점 3초 창 {math.ceil(hp / (chain * 3))}번(철삭) / {math.ceil(hp / (mace * 3))}번(방망이) 필요")
