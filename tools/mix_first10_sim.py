# 처음 10분 믹스 시뮬레이터(기획·사운드, 2026-10-26). 실행: python3 tools/mix_first10_sim.py [--new] [--waitduck=0.7] [크기.json] [--wav]
# 실제 소리 파일을 지금 코드의 크기 규칙으로 장면별로 섞고, 중요한 소리(대기 똑딱·예고)가 다른 소리보다 몇 dB 위에 있는지 잰다(3 dB 미만 = 묻힘)
# 처음 10분 소리 한 줄 시뮬레이터: 실제 파일을 지금 코드의 크기 규칙으로 섞고, 몰림·묻힘을 잰다
import numpy as np, scipy.io.wavfile as w, scipy.signal as sg, subprocess, json, sys, os
ROOT='/home/claude/chasa/unity/Assets/Resources/Audio/'; SR=44100
G=next((json.load(open(a)) for a in sys.argv[1:] if a.endswith('.json')),{})   # 크기 덮어쓰기(고친 믹스 시험용)
BGM_SET=0.8; SFX_SET=1.0
IMPORTANT=('sfx.wait.tick','sfx.wait.final','sfx.warn','sfx.enemy.telegraph','sfx.enemy.mote.telegraph','sfx.elite.pounce.telegraph','sfx.elite.slam.telegraph','sfx.kneel')
cache={}
def load(id_, folder='Sfx'):
    k=(id_,folder)
    if k not in cache:
        f=ROOT+folder+'/'+id_.replace('.','_')+('.wav' if folder=='Sfx' else '.ogg')
        if f.endswith('.ogg'):
            raw=subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout; x=np.frombuffer(raw,np.float32).copy()
        else:
            r,x=w.read(f); x=x.astype(np.float32)/32768; x=x.mean(1) if x.ndim>1 else x
        cache[k]=x
    return cache[k]
def vol(id_):
    for p,v in G.items():
        if id_.startswith(p): return v
    if id_.startswith('sfx.step'): return .45
    return 1.0
class Scene:
    def __init__(s,name,sec):
        s.name=name; s.n=int(sec*SR); s.imp={}; s.rest=np.zeros(s.n); s.events=[]; s.bgm=np.zeros(s.n); s.ducks=[]
    def sfx(s,id_,t,g=1.0):
        x=load(id_)*vol(id_)*g*SFX_SET; i=int(t*SR); j=min(s.n,i+len(x))
        if i>=s.n: return
        if id_.startswith(IMPORTANT):
            k=(id_,round(t,2)); a=np.zeros(s.n); a[i:j]=x[:j-i]; s.imp[k]=a
        else: s.rest[i:j]+=x[:j-i]
        s.events.append((round(t,2),id_))
    def loop(s,id_,t0,t1,g,folder='Sfx'):
        x=load(id_,folder); i=int(t0*SR); j=min(s.n,int(t1*SR)); L=j-i
        y=np.tile(x,L//len(x)+1)[:L]*g
        f=int(.3*SR); y[:f]*=np.linspace(0,1,f); y[-f:]*=np.linspace(1,0,f)
        (s.bgm if folder=='BGM' else s.rest)[i:j]+=y
    def mix(s):
        g=np.ones(s.n)
        for t0,t1,mult in s.ducks:
            i,j=int(t0*SR),min(s.n,int(t1*SR)); g[i:j]=np.minimum(g[i:j],mult)
        g=np.convolve(g,np.ones(int(.2*SR))/int(.2*SR),'same')
        m=s.rest+s.bgm*g
        for a in s.imp.values(): m=m+a
        return m
BANDS=[(250,500),(500,1000),(1000,2000),(2000,4000),(4000,8000)]
def bandE(x):
    out=[]
    for lo,hi in BANDS:
        b,a=sg.butter(2,[lo/(SR/2),hi/(SR/2)],'band'); out.append(sg.lfilter(b,a,x))
    return out
def analyse(sc, label=''):
    m=sc.mix(); rows=[]
    for (id_,t),a in sc.imp.items():
        e=a**2; idx=np.where(e>e.max()*10**(-1.5))[0]
        if len(idx)==0: continue
        i0,i1=idx[0],idx[-1]+1; i1=max(i1,i0+int(.03*SR))
        other=m-a
        best=-99
        for ca,oa in zip(bandE(a[i0:i1]),bandE(other[i0:i1])):
            c=10*np.log10((ca**2).mean()+1e-12); o=10*np.log10((oa**2).mean()+1e-12); best=max(best,c-o)
        rows.append((t,id_,round(best,1)))
    # 몰림: 0.4초 창 평균 크기(dBFS RMS)와 동시에 시작한 소리 수
    win=int(.4*SR); hop=int(.1*SR); peaks=[]
    for i in range(0,len(m)-win,hop):
        r=10*np.log10((m[i:i+win]**2).mean()+1e-12); peaks.append((round(i/SR,1),round(r,1)))
    top=sorted(peaks,key=lambda p:-p[1])[:3]
    ev=sorted(sc.events); dens=max((sum(1 for t,_ in ev if a<=t<a+1.0),a) for a,_ in ev) if ev else (0,0)
    return rows, top, dens, 20*np.log10(np.abs(m).max()+1e-9)
import sys; sys.argv=[sys.argv[0]]+sys.argv[1:]
import numpy as np
NEW = '--new' in sys.argv   # 제안한 대기 똑딱 규칙(남은 초 기준, final 뒤 멈춤)
WD=float(next((a.split('=')[1] for a in sys.argv if a.startswith('--waitduck=')),'1'))
def ticks(sc, t0, T, kind, final=True, stop=None):
    left=T; nt=.3; dt=1/60; t=t0; done=False
    sc.ducks.append((t0,min(t0+T,stop or 1e9),WD))
    while left>0 and (stop is None or t<stop):
        if not done and left<=1.5 and final: sc.sfx('sfx.wait.final',t); done=True
        if NEW and done: break
        nt-=dt
        if nt<=0:
            sc.sfx('sfx.wait.tick.'+kind,t)
            nt = (.18+(1-.18)*min(1,max(0,(left-1.5)/6))) if NEW else (.15+(1-.15)*max(0,min(1,left/T)))
        left-=dt; t+=dt
def combo(sc,t,n):
    for k in range(n):
        b=t+k*1.3; sc.sfx('sfx.hit.chain',b); sc.sfx('sfx.hit.chain',b+.38); sc.sfx('sfx.hit.heavy',b+.8)
def walk(sc,t0,t1):
    t=t0
    while t<t1: sc.sfx('sfx.step.dirt.%d'%(1+int(t*4)%4),t); t+=.25
BE=.5*BGM_SET; BC=.45*BGM_SET
def bed(sc,t0,t1,g=.6): sc.loop('amb.village.night',t0,t1,g*SFX_SET)
def bgm(sc,id_,t0,t1,g): sc.loop(id_,t0,t1,g,'BGM')
def tendo(sc,t,cast=1.5,warn=()):
    sc.sfx('sfx.tendo.vision.close',t); sc.loop('tendo.cast',0,0,0) if False else None
    x=load('sfx.tendo.cast'); i=int(t*SR); L=int(cast*SR); y=np.tile(x,2)[:L]
    sc.rest[i:i+L]+=y[:max(0,min(L,sc.n-i))]
    for (id_,dt) in warn: sc.sfx(id_,t+dt)
    sc.sfx('sfx.tendo.done.chain',t+cast); sc.sfx('sfx.reward.honbul',t+cast+.5)

S=[]
# A 첫 싸움 + 첫 천도 (1:00 ~ 1:35 → 0~16초)
a=Scene('A 첫 혼 싸움·첫 천도(1:00~1:30)',16); bed(a,0,16); bgm(a,'bgm_solgogae_combat',0,6.5,BC)
combo(a,.5,4); a.sfx('sfx.enemy.telegraph',1.2); a.sfx('sfx.dodge',2.0)
a.sfx('sfx.kneel',6.0); a.sfx('sfx.exec.card.open',6.25); a.loop('bgm_solgogae_finish',6.0,12,BC,'BGM')
tendo(a,8.0); a.sfx('sfx.reward.bar.open',10.2); bgm(a,'bgm_solgogae_night',12,16,BE); S.append(a)
# B 둘러싸임: 하나 꿇고(10초 대기) 둘이 계속 싸움, 그 사이 천도(2:30~2:50)
b=Scene('B 둘러싸임 3: 꿇은 혼 대기 + 두 혼 공격 중 천도(2:40~2:55)',16); bed(b,0,16); bgm(b,'bgm_solgogae_combat',0,16,BC)
combo(b,0,2); b.sfx('sfx.kneel',2.6); ticks(b,2.6,10,'fresh',stop=9.5)
combo(b,3.2,2); b.sfx('sfx.enemy.telegraph',4.0); b.sfx('sfx.enemy.telegraph',5.6); b.sfx('sfx.dodge',4.6); b.sfx('sfx.player.hurt',6.4)
tendo(b,8.0,warn=(('sfx.warn.plain',.4),('sfx.warn.wind',1.0)))
b.sfx('sfx.drop.land',10.2); b.sfx('sfx.drop.beam.common',10.2); S.append(b)
# C 박돌쇠 천도: 대기 10초 → 천도 → 기억 + 품계 인 + 시계 풀림
c=Scene('C 박돌쇠 천도 + 품계 2(5:00)',20); bed(c,0,20); bgm(c,'bgm_solgogae_night',0,20,BE*0.7)
c.sfx('sfx.kneel',.5); c.loop('bgm_solgogae_finish',.5,7,BC,'BGM'); ticks(c,.5,10,'fresh',stop=7.5)
tendo(c,6.0)
if NEW: c.sfx('sfx.clue',8.7); c.sfx('sfx.rank.seal',9.5); c.sfx('sfx.reward.bar.open',10.1)
else: c.sfx('sfx.clue',8.1); c.sfx('sfx.rank.seal',8.3); c.sfx('sfx.reward.bar.open',8.6)
S.append(c)
# C2 박돌쇠 파혼
c2=Scene('C2 박돌쇠 파혼 + 품계 2(5:00)',12); bed(c2,0,12); bgm(c2,'bgm_solgogae_night',0,12,BE*0.7)
c2.sfx('sfx.kneel',.5); ticks(c2,.5,10,'fresh',stop=3.5)
c2.sfx('sfx.pahon.burst.chain',3.5); c2.sfx('sfx.reward.coin.pop',3.55); c2.sfx('sfx.reward.coin.gather',4.1); c2.sfx('sfx.rank.seal',4.9 if NEW else 4.2); c2.sfx('sfx.reward.bar.open',5.5 if NEW else 4.5); S.append(c2)
# D 거센 혼 + 잔넋 셋, 거센 혼 대기 7초 동안 잔넋 공격
d=Scene('D 거센 혼(7:00): 예고·잔넋·대기 7초 중 공격',22); bed(d,0,22); bgm(d,'bgm_solgogae_combat',0,22,BC)
d.sfx('sfx.elite.appear',0); d.sfx('sfx.elite.call',.8); combo(d,1.5,3)
d.sfx('sfx.elite.slam.telegraph',2.2); d.sfx('sfx.elite.slam',3.4); d.sfx('sfx.elite.pounce.telegraph',5.0); d.sfx('sfx.elite.pounce',6.0); d.sfx('sfx.dodge',5.7)
d.sfx('sfx.mote.spawn',6.5); combo(d,6.8,2); d.sfx('sfx.kneel',9.5); ticks(d,9.5,7,'year',stop=15.2)
d.sfx('sfx.enemy.mote.telegraph',10.5); d.sfx('sfx.enemy.mote.telegraph',12.3); combo(d,10.8,2); d.sfx('sfx.player.hurt',11.4)
d.sfx('sfx.pahon.burst.chain',15.2); d.sfx('sfx.reward.coin.pop',15.25); d.sfx('sfx.reward.coin.gather',15.85); d.sfx('sfx.drop.land',15.6); d.sfx('sfx.drop.beam.fine',15.6); S.append(d)
# 걷기(0:25~0:50): 발소리 vs 바탕·음악
e=Scene('E 걷기(0:25)',8); bed(e,0,8); bgm(e,'bgm_solgogae_night',0,8,BE); walk(e,0,8); S.append(e)

report=[]
for sc in S:
    rows,top,dens,pk=analyse(sc)
    bad=[r for r in rows if r[2]<3]
    report.append(dict(scene=sc.name,peak_dbfs=round(pk,1),loudest_04s=top,busiest_1s=dens,important=len(rows),buried=[(t,i,v) for t,i,v in sorted(bad)]))
    if '--wav' in sys.argv:
        m=sc.mix(); m=m/max(1,np.abs(m).max()/0.98); w.write(f'{sc.name[0]}{"_new" if NEW else ""}.wav',SR,(np.clip(m,-1,1)*32767).astype(np.int16))
print(json.dumps(report,ensure_ascii=False,indent=1))
