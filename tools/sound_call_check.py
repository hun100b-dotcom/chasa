"""소리 호출 교차 점검 (기획·사운드): 코드 브랜치에서 부르는 소리 id 와 만든 소리 목록을 맞대어 본다.
쓰는 법: python3 tools/sound_call_check.py <코드 브랜치를 내려받은 폴더> [결과 json 경로]
  - 코드(.cs)의 문자열과 Resources/Data/*.json(컷신 sfx·audio 명령 포함)에서 id 를 모은다
  - "sfx.swing." + 무기 같은 조합은 알려진 값으로 펼친다(무기 5종·발소리 재질 6×4·장비 등급 4)
  - 만든 목록 = 이 저장소 data/sfx_files.json, 있는 파일 = 코드 브랜치의 Resources/Audio/Sfx/*.wav + SfxSynth 합성 id"""
import re,os,json,glob,collections,sys
C=os.path.abspath(sys.argv[1])
ME=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTP=sys.argv[2] if len(sys.argv)>2 else os.path.join(ME,'data/sound_call_check.json')
ID=re.compile(r'(?<![\w.])((?:sfx|amb|cut|mus|vo)\.[a-z0-9_]+(?:\.[a-z0-9_]+)*)(\.?)')
called=collections.defaultdict(set); prefixes=collections.defaultdict(set)
for f in glob.glob(C+'/unity/Assets/Scripts/**/*.cs',recursive=True):
    src=open(f,encoding='utf-8').read(); rel=os.path.relpath(f,C+'/unity/Assets/Scripts')
    for m in re.finditer(r'"([^"\n]*)"(\s*\+)?',src):
        s=m.group(1)
        for mm in ID.finditer(s):
            idv=mm.group(1)
            if (mm.group(2)=='.' or s.endswith('.')) and m.group(2): prefixes[idv+'.'].add(rel)
            elif m.group(2) and s==idv: prefixes[idv].add(rel)   # "sfx.hit" + ...
            else: called[idv].add(rel)
# 자료(json)에서 부르는 것
for f in glob.glob(C+'/unity/Assets/Resources/Data/*.json'):
    rel='Data/'+os.path.basename(f)
    for mm in ID.finditer(open(f,encoding='utf-8').read()):
        called[mm.group(1)].add(rel)
# 동적 조합 펼치기(알려진 것)
W=['chain','mace','bell','trident','brush']; dyn=set()
for p in ('sfx.swing.','sfx.pahon.burst.','sfx.tendo.done.'):
    for w in W: dyn.add(p+w)
for w in W[1:]: dyn|={f'sfx.hit.{w}',f'sfx.hit.{w}.heavy'}
dyn|={'sfx.hit.chain','sfx.hit.heavy'}
for mat in ['dirt','grass','gravel','paddy','leaves','water']:
    for n in range(1,5): dyn.add(f'sfx.step.{mat}.{n}')
for g in ['common','fine','rare','named']: dyn.add('sfx.drop.beam.'+g)
for d in dyn: called[d].add('(조합)')
# 있는 것
files_code={os.path.splitext(os.path.basename(f))[0] for f in glob.glob(C+'/unity/Assets/Resources/Audio/Sfx/*.wav')}
synth=set(re.findall(r'"((?:sfx|amb|cut|mus|vo)\.[a-z0-9_.]+)"',open(C+'/unity/Assets/Scripts/Core/SfxSynth.cs').read()))
made={s['id']:s for s in json.load(open(ME+'/data/sfx_files.json'))['sounds']}
packs=json.load(open(ME+'/data/audio_packs.json')); kind_pack={}
for p,v in packs['packs'].items():
    for i in (v.get('sfx') or v.get('sounds') or []): kind_pack[i]=p
def fname(i): return i.replace('.','_')
S1={'core','act1','act2','act3'}
# 실제 쓰는 id 만(파일 이름과 헷갈리는 것 제외: 끝이 확장자 등)
called={k:v for k,v in called.items() if not k.endswith(('_json','.json','.wav','.ogg','.png')) and not (k+'.' in prefixes and k not in made)}   # 'sfx.hit' 처럼 조합의 앞부분만 있는 것은 뺀다
not_called=[i for i in made if i not in called]
missing=[i for i in called if fname(i) not in files_code and i not in synth]
miss_pr=[i for i in missing if i in made]; miss_none=[i for i in missing if i not in made]
res=dict(made=len(made),called=len(called),
  not_called=sorted(not_called,key=lambda i:(kind_pack.get(i,'?') not in S1,kind_pack.get(i,'?'),i)),
  miss_pr36=sorted(miss_pr), miss_none=sorted(miss_none), prefixes={k:sorted(v) for k,v in prefixes.items()},
  where={i:sorted(called[i]) for i in missing})
json.dump(res,open(OUTP,'w'),ensure_ascii=False,indent=1)
print('made',len(made),'called',len(called),'notcalled',len(not_called),'S1 notcalled',sum(kind_pack.get(i) in S1 for i in not_called),'missing(on PR36)',len(miss_pr),'missing(nowhere)',len(miss_none))
print('prefixes',dict(prefixes))
print('nowhere:',miss_none)
print('결과:',OUTP)
