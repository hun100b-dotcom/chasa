# 3막 🔴 수치 검증 (P1-043). 기존 시뮬(balance_sim_tendo_pahon.py)의 단순 모델을 재사용. 결과 해석은 docs/BALANCE-ACT3.md
import importlib.util, sys, io, contextlib
sys.argv = ['x', '0']
spec = importlib.util.spec_from_file_location('s', '/home/claude/chasa/tools/balance_sim_tendo_pahon.py')
with contextlib.redirect_stdout(io.StringIO()):
    s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
def tendo_T(n, T, lam):   # 천도 초당 기대 넋 (주변 싸우는 적 n마리, 캐스팅 T초)
    dmg = n * (T / s.ATK_INT) * s.ATK_DMG * s.RANGE_P
    return (s.NEOK + s.MEM * s.MEM_VAL - lam * dmg) / (T + s.APPROACH)
def flip(T, lam, kv=2.0):  # 처음 파혼이 이기는 n
    for n in range(0, 9):
        if tendo_T(n, T, lam) < s.pahon(n, lam, kv)[0]: return n
    return 9
print("[1] 물 혼: 천도 캐스팅 -1초. 처음 파혼이 이득이 되는 주변 적 수 (kv=2)")
print("lam    기본1.5  물혼0.5  물혼(연속)0.3")
for lam in (0.2, 0.6, 1.5):
    print(f"{lam:<5}  {flip(1.5,lam):^7}  {flip(0.5,lam):^7}  {flip(0.3,lam):^9}")
print("  n=0 초당 넋:", {T: round(tendo_T(0, T, 0.6), 1) for T in (1.5, 0.5, 0.3)}, " 파혼 n=0:", round(s.pahon(0, 0.6, 2)[0], 1))
print("\n[1b] 밀물 20초 창: 한 마리 처리 시간 = 맺힘 깎기 K + 접근 0.6 + 캐스팅. 창 안에 몇 마리 천도 가능?")
for K in (1.5, 2.5, 4.0):
    for T in (1.5, 0.5):
        print(f"  깎기 {K}s 캐스팅 {T}s -> {20/(K+0.6+T):.1f}마리", end=" |")
    print()
print("\n[2] B-10: 선원 7명 천도 시 선장 맺힘 -10%씩. 보스 전투 6분(360s, 임시) 기준")
cast = 1.5 + 0.6
for pct in (0.10, 0.05):
    t = 7 * (cast + 0.4)   # 선원 하나 처리(깎기 0.4 가정, 이미 약한 졸개)
    saved = 360 * min(7 * pct, 1.0)
    print(f"  -{int(pct*100)}%/명: 선원 7명 천도 {t:.0f}s 투자 → 전투 {saved:.0f}s 절약 (이득비 {saved/t:.1f}배)")
print("  파혼 쪽: 기울기 감소 = 전투 난이도 ↓ (임시: 받는 피해 -25%%) → 360s 전투 체감 90s 절약 / 선원 7명 파혼 약 %.0fs" % (7 * 1.0))
print("\n[3] B-12 3페이즈: 물 혼 천도 시 보스 맺힘 -X% (미정). 3페이즈 맺힘 구간 25%")
for x in (0.10, 0.05, 0.03):
    print(f"  -{int(x*100)}%/마리: 25% 구간을 {0.25/x:.0f}마리 천도로 소진 (물 혼 12명 있음)")
print("\n[4] 무적 혼 낮 단서: 별명 들으면 천도 가능. 캐스팅 -0.5초 (B-11, 연속 0.8 → 하한 필요)")
for T in (1.5, 1.0, 0.8, 0.3):
    print(f"  캐스팅 {T}s: 천도 n=0 초당 {tendo_T(0, T, 0.6):.1f}  (파혼 {s.pahon(0,0.6,2)[0]:.1f})")
