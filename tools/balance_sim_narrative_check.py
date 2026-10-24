import importlib.util,sys
sys.argv=['x','0']
spec=importlib.util.spec_from_file_location('s','/home/claude/chasa/tools/balance_sim_tendo_pahon.py')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()):
    s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
def tendo_T(n,T,lam):
    dmg=n*(T/s.ATK_INT)*s.ATK_DMG*s.RANGE_P
    return (s.NEOK+s.MEM*s.MEM_VAL-lam*dmg)/(T+s.APPROACH)
def flip(T,lam,kv):
    for n in range(0,9):
        if tendo_T(n,T,lam) < s.pahon(n,lam,kv)[0]: return n   # 처음 파혼이 이기는 n
    return 9
print("처음 파혼이 이득이 되는 주변 적 수 (클수록 천도가 오래 버팀)  kv=2")
print("lam   일반1.5  흐림1.75  없음2.0  보스2.5  연속0.8")
for lam in (0.2,0.6,1.5):
    print(f"{lam:<4}  "+"  ".join(f"{flip(T,lam,2.0):^7}" for T in (1.5,1.75,2.0,2.5,0.8)))
print("\n천도 1회 기대 넋/초 (n=0): ", {T:round(tendo_T(0,T,0.6),1) for T in (0.8,1.5,1.75,2.0,2.5)})
# 지름길: 한 밤 20분, 귀환 이동 비중 가정
print("\n지름길 가치(넋 환산): 1분 = 100넋 가정, 밤 20분, 귀환 이동 3분/밤 (임시)")
for cut in (0.4,0.2,0.1):
    per=cut*3*100
    print(f" -{int(cut*100)}%: 한 밤 {per:.0f} 넋 상당, 앞으로 10밤이면 {per*10:.0f}  (보스 파혼 즉시 보상: 엽전 10 + 업3)")
