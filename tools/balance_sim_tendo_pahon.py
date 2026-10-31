# 사용: python3 tools/balance_sim_tendo_pahon.py [폭발 피해 가치(적 1마리당 넋), 기본 0]  — 결과 해석은 docs/BALANCE-SIM-P1-040.md
# 천도 vs 파혼 기대값 시뮬 (P1-040). 단순 모델, 숫자는 COMBAT-SPEC/config.gd 값.
import random
T1,T2=1.5,0.8          # 천도 캐스팅 (일반/연속)
ATK_INT,ATK_DMG,RANGE_P=2.0,12,0.75   # 공격 간격, 피해, 사거리 안에서 실제로 맞을 확률(예비동작 회피 감안, 임시)
NEOK,MEM=10,1; COIN,KARMA=5,1
MEM_VAL=4.0            # 기억 조각 1개의 가치(넋 환산, 임시)
APPROACH=0.6
import sys
BONUS=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
def tendo(n,chain,lam,kv):
    T=T2 if chain else T1
    dmg=n*(T/ATK_INT)*ATK_DMG*RANGE_P
    reward=NEOK+MEM*MEM_VAL
    return (reward - lam*dmg)/(T+APPROACH), dmg, T
def pahon(n,lam,kv,n_hit=None):
    n_hit=n if n_hit is None else n_hit
    # 폭발은 반경 안 적을 경직+밀어냄 → 다음 한 번의 공격을 막는다(적당 평균 한 번 × 0.5 확률로 아낌)
    saved=n_hit*ATK_DMG*RANGE_P*0.5
    reward=COIN - kv*KARMA + lam*saved + 0.35*n_hit*0.0  # 폭발 35 피해는 맺힘 35% 깎음 → 아래 bonus
    bonus=n_hit*BONUS
    return (reward+bonus)/(0.25+APPROACH), -saved
rows=[]
print("n=주변 싸우는 적 수 / lam=체력 1의 가치(넋) / kv=업 1의 가치(넋)")
for kv in (0.5,2.0,5.0):
  for lam in (0.2,0.6,1.5):
    line=[]
    for n in range(0,7):
        t,_,_=tendo(n,False,lam,kv); tc,_,_=tendo(n,True,lam,kv); p,_=pahon(n,lam,kv)
        w='T' if t>p else 'P'
        wc='T' if tc>p else 'P'
        line.append(f"{n}:{w}{wc}")
    print(f"kv={kv:<4} lam={lam:<4}  "+"  ".join(line))
print()
print("값 예: kv=2 lam=0.6")
for n in range(0,7):
    t,d,T=tendo(n,False,0.6,2); tc,dc,_=tendo(n,True,0.6,2); p,s=pahon(n,0.6,2)
    print(f"n={n} 천도 {t:5.1f}/s(피해 {d:4.1f}) 연속천도 {tc:5.1f}/s(피해 {dc:4.1f}) 파혼 {p:5.1f}/s")
# 연쇄 악용: 연속 천도를 5초 창으로 무한 이어갈 때 시간당 넋
print()
for n in (0,2):
    per=(NEOK)/(T2+APPROACH); first=(NEOK)/(T1+APPROACH)
    print(f"n={n} 혼 공급이 충분할 때 시간당 넋: 첫 천도 {first*60:.0f}/분, 연쇄 {per*60:.0f}/분 (x{per/first:.2f})")
