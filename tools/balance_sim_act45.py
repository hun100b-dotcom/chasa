# 4·5막 🔴 수치 검증 (P1-044). 결과 해석은 docs/BALANCE-ACT45.md. 모델은 balance_sim_act3.py 와 같은 단순 기대값, 가정은 임시.
import importlib.util, sys, io, contextlib
sys.argv = ['x', '0']
spec = importlib.util.spec_from_file_location('s', '/home/claude/chasa/tools/balance_sim_tendo_pahon.py')
with contextlib.redirect_stdout(io.StringIO()):
    s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
def tendo_T(n, T, lam):
    dmg = n * (T / s.ATK_INT) * s.ATK_DMG * s.RANGE_P
    return (s.NEOK + s.MEM * s.MEM_VAL - lam * dmg) / (T + s.APPROACH)
def flip(T, lam, kv=2.0):
    for n in range(0, 9):
        if tendo_T(n, T, lam) < s.pahon(n, lam, kv)[0]: return n
    return 9
print("[1] B-14 번호 낙인: 10초간 캐스팅 +1초(→2.5). 처음 파혼이 이득이 되는 주변 적 수 (kv=2)")
print("lam   일반1.5  낙인+1.0(2.5)  낙인+0.5(2.0)")
for lam in (0.2, 0.6, 1.5):
    print(f"{lam:<4}  {flip(1.5,lam):^7}  {flip(2.5,lam):^13}  {flip(2.0,lam):^13}")
print("\n[2] B-19 버티기 -12%/회 vs B-10 선원 -5%/명 (이득비 = 전투 360s 절약 / 투자 시간)")
for name, cut, per in (("B-10 선원 -5%", .05, 2.5), ("B-19 버티기 -12%", .12, 3.0 + 2.0), ("B-19 버티기 -10%", .10, 3.0 + 2.0), ("B-19 버티기 -8%", .08, 3.0 + 2.0)):
    n = 1.0 / cut
    print(f"  {name}: 보스 맺힘 전부 소진까지 {n:.1f}회, 투자 {n*per:.0f}s, 이득비 {360/(n*per):.1f}배")
print("\n[3] N-A5-3 풀어내기 조건 비율 R/S  (R=천도 수+이름 쪽지+이은 이름, S=물막이 눈금+시즌1 파혼 수)")
print("    눈금 규칙(제안): 4막~ 일반 파혼 +1, 이름 줍기 성공 시 +0.5, 보스 파혼 +10. 시즌1 파혼 수는 그대로 더함.")
ARCH = {  #   천도수, S1파혼, S2 4~5막 파혼, 줍기성공률, 보스파혼수(4막~), 이은이름
 "천도 위주":        dict(T=800, p1=40,  p2=40,  q=0.5, bp=0, joined=60),
 "균형":              dict(T=500, p1=150, p2=150, q=0.5, bp=1, joined=40),
 "파혼 위주(성실)":  dict(T=200, p1=300, p2=300, q=0.9, bp=2, joined=30),
 "파혼 위주(반쯤)":  dict(T=200, p1=300, p2=300, q=0.5, bp=3, joined=10),
 "파혼 위주(방치)":  dict(T=200, p1=300, p2=300, q=0.1, bp=4, joined=0),
 "전부 파혼":        dict(T=30,  p1=500, p2=500, q=0.0, bp=4, joined=0),
}
print("  유형              R      S     R/S")
res = {}
for k, a in ARCH.items():
    R = a['T'] + a['q'] * a['p2'] + a['joined']
    S = a['p2'] * (1 - 0.5 * a['q']) + 10 * a['bp'] + a['p1']
    res[k] = R / S
    print(f"  {k:<14} {R:6.0f} {S:6.0f}  {R/S:5.2f}")
print("  → 성실한 파혼 위주 ≈ 1.0, 방치 ≈ 0.4. 그 사이 0.6 이 기준이면 성실은 닿고 방치는 파혼만 (반쯤 성실 q=0.5 파혼 위주는 약 0.67 로 경계)")
for th in (0.4, 0.6, 1.0):
    print(f"  기준 {th}: " + ", ".join(f"{k}={'풀어내기' if v>=th else '파혼만'}" for k, v in res.items()))
print("\n[4] B-15 안전 칸: 천도 25마다 1칸 → 천도 수별 칸 수 (아레나 한 변 칸 수 가정 상한 6)")
for T in (25, 100, 300, 800):
    print(f"  천도 {T}: {T//25}칸 → 상한 6 적용 시 {min(6, T//25)}칸")
print("\n[5] 이름 조각 이어붙이기(⑩): 같은 색 3조각을 사슬로 모아 이으면 천도. 시간·보상 균형")
join_time = 3 * 1.5 + 1.5   # 조각 낚기 3회 + 이은 이름 천도 캐스팅
base = tendo_T(0, 1.5, 0.6) * (1.5 + 0.6)   # 일반 천도 1회 가치
pahon3 = 3 * (s.COIN - 2.0 * s.KARMA) # 조각 3개 파혼 (눈금 비용 제외)
print(f"  일반 천도 1회 가치 {base:.1f} (시간 2.1s). 이은 이름 소요 {join_time+0.6:.1f}s. 시간 대비 같아지려면 가치 {base/2.1*(join_time+0.6):.0f}. 조각 3개 파혼 가치 {pahon3:.1f} (시간 2.6s)")
print(f"  → 이은 이름 천도 보상을 일반의 약 3배(가치 {3*base:.0f}) 이상으로")
