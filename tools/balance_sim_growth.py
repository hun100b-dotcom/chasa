#!/usr/bin/env python3
"""기획서 6절 성장 임시값 QA 검증: (②) 장비 상한이 천도↔파혼 뒤집힘 구간을 깨는지 (④) 품계 곡선.
기본 모델은 tools/balance_sim_tendo_pahon.py 를 그대로 가져와(kv=2, lam=0.6) 값만 바꿔 돌린다."""
src = open('tools/balance_sim_tendo_pahon.py', encoding='utf-8').read().split("rows=[]")[0]
def run(T1v, T2v, bonus=0.0, kv=2.0, lam=0.6):
    g = {}
    s = src.replace("T1,T2=1.5,0.8", f"T1,T2={T1v},{T2v}").replace(
        "BONUS=float(sys.argv[1]) if len(sys.argv)>1 else 0.0", f"BONUS={bonus}")
    exec(s, g)
    def flip(chain):
        for n in range(0, 10):
            t, _, _ = g['tendo'](n, chain, lam, kv); p, _ = g['pahon'](n, lam, kv)
            if p > t: return n
    return flip(False), flip(True)   # (첫 천도, 연속 천도) 일 때 파혼이 처음 이기는 주변 적 수
print("뒤집힘 경계(적 수)  기본:", run(1.5, 0.8))
print("  캐스팅 -30%:", run(1.05, 0.56))
print("  기울기 옵션(+10% 느림):", run(1.65, 0.88))
print("  파혼 피해 가치 +3:", run(1.5, 0.8, 3.0))
tot = lambda L, k=40: sum(k * i ** 1.5 for i in range(1, L + 1))
print("품계 비용 40·L^1.5 누적 40품계:", round(tot(40)), "50품계:", round(tot(50)))
for r in (15, 25, 40):
    print(f"  넋 {r}/분: 40품계 {tot(40)/r/60:.0f}h, 50품계 {tot(50)/r/60:.0f}h")
