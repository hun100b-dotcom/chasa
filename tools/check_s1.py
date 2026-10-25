# -*- coding: utf-8 -*-
# 시즌 1 서사 데이터 일관성 검사기 (1~3막 json 교차 검사).
# 왜: 서사 데이터는 생성기 20여 개가 따로 만든다. 같은 혼의 기억·같은 단서의 대사·같은 사람 id가
#   파일마다 조금씩 어긋나면 코드가 엉뚱한 글을 띄운다. 사람 눈으로는 못 찾으니 기계가 맞춰 본다.
# 원본(SSOT, 하나뿐인 진짜): soul_memories.json(혼·기억·F) / boss_clues_actN(단서) / npc_actN(사람).
# 실행: python3 tools/check_s1.py   (어긋남이 있으면 목록을 찍고 종료코드 1)
import json, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.join(HERE, '..', 'docs', 'narrative')
J = lambda f: json.load(open(os.path.join(ND, f), encoding='utf-8'))
SM = J('soul_memories.json')
SOUL = {s['id']: s for s in SM['souls']}
FACTS = SM['facts']
ERR = []
def err(where, msg): ERR.append(f'[{where}] {msg}')

# ───── 0. 모든 파일 읽기 ─────
files = {os.path.basename(p): json.load(open(p, encoding='utf-8')) for p in sorted(glob.glob(os.path.join(ND, '*.json')))}

def walk(o, path=''):
    """json 안의 모든 (경로, 값) 쌍."""
    if isinstance(o, dict):
        for k, v in o.items(): yield from walk(v, f'{path}.{k}')
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from walk(v, f'{path}[{i}]')
    else:
        yield path, o

# ───── 1. 혼·보스 id가 원본에 있나 ─────
ID_RE = re.compile(r'\b([SB]-\d{2,3})\b')
for fn, d in files.items():
    if fn == 'soul_memories.json': continue
    for p, v in walk(d):
        if isinstance(v, str):
            for m in ID_RE.findall(v):
                if m not in SOUL and not m.startswith('B-04') and m not in ('B-13', 'B-14', 'B-15', 'B-16', 'B-17', 'B-18', 'B-19', 'B-20', 'B-28', 'B-29', 'B-30', 'B-31'):
                    err(fn, f'{p}: 원본에 없는 id {m}')

# ───── 2. 기억 글이 원본과 같나(memories_actN, funerals, 단서 밤 대체, 컷신 기억 줄) ─────
for n in (1, 2, 3):
    for r in files[f'memories_act{n}.json']['souls']:
        s = SOUL.get(r['id'])
        if not s: err(f'memories_act{n}', f"{r['id']} 원본 없음"); continue
        if r['memory'] != s['memory']: err(f'memories_act{n}', f"{r['id']} 기억 글이 원본과 다름")
        if r.get('fact') != s.get('fact'): err(f'memories_act{n}', f"{r['id']} F 번호가 원본과 다름")
    for f in files[f'funerals_act{n}.json']['funerals']:
        s = SOUL[f['soul']]
        if f['memory_link'] != s['memory']: err(f'funerals_act{n}', f"{f['soul']} memory_link가 원본과 다름")
        if not s.get('funeral'): err(f'funerals_act{n}', f"{f['soul']} 원본에 funeral 표시가 없는데 장례가 있음")
# 장례 표시가 있는데 장례 대본이 없는 혼
have_fun = {f['soul'] for n in (1, 2, 3) for f in files[f'funerals_act{n}.json']['funerals']} | {'S-001'}
for s in SM['souls']:
    if s.get('funeral') and s.get('region') in range(1, 7) and s.get('layer') != 'below' and s['id'] not in have_fun:
        err('funerals', f"{s['id']} {s['name']}: 원본엔 장례 대상인데 장례 대본 없음")

# ───── 3. 보스 단서: 원본 F·밤 대체 기억·사람 id·대사 ─────
bc = {}
bc.update({k: v for k, v in files['npc_act1.json']['boss_clues'].items()})
for n in (2, 3):
    for k, v in files[f'boss_clues_act{n}.json']['boss_clues'].items():
        if k in bc and k != 'B-12': err('boss_clues', f'{k}가 두 파일에 있음')
        if k == 'B-12' and 'B-12' in bc:
            bc['B-12_act1'] = bc.pop('B-12')
        bc[k] = v
clue_ids = {}
for k, b in bc.items():
    for c in b.get('clues', []):
        if c['id'] in clue_ids: err('boss_clues', f"단서 id {c['id']}가 {clue_ids[c['id']]}와 {k}에 겹침")
        clue_ids[c['id']] = k
        if c.get('soul') and c.get('memory') and c['memory'] != SOUL[c['soul']]['memory']:
            err('boss_clues', f"{c['id']} 밤 대체 기억이 원본과 다름")
    bid = k.split('_')[0]
    if b.get('decisive') and SOUL.get(bid, {}).get('fact') != b['decisive']:
        err('boss_clues', f"{bid} decisive {b['decisive']} ≠ 원본 {SOUL.get(bid, {}).get('fact')}")
    if len(b.get('clues', [])) not in (4,) and not k.endswith('_act1'):
        err('boss_clues', f'{k} 단서 수 {len(b.get("clues", []))}(4여야 함)')

# 사람 id
NPC = {}
for n in (1, 2, 3):
    for p in files[f'npc_act{n}.json']['npcs']:
        if p['id'] in NPC: err('npc', f"{p['id']} 사람 id 겹침")
        NPC[p['id']] = p
for k, b in bc.items():
    for c in b.get('clues', []):
        if c.get('npc') and c['npc'] not in NPC: err('boss_clues', f"{c['id']} npc {c['npc']} 없음")

# 단서 대사 = 사람 시간표 대사
for pid, p in NPC.items():
    for e in p.get('schedule') or []:
        c = e.get('clue')
        if not c: continue
        if c not in clue_ids: err('npc', f'{pid} 시간표의 단서 {c}가 단서 표에 없음'); continue
        src = next(x for x in bc[clue_ids[c]]['clues'] if x['id'] == c)
        if src.get('line') and e.get('line') and (src['line'] != e['line'] or src.get('line_half') != e.get('line_half')):
            err('npc', f'{pid} {c} 대사가 단서 표와 다름')
        if src.get('npc') and src['npc'] != pid and not (src.get('line') is None and e.get('line') is None):
            err('npc', f"{pid} 시간표에 {c}가 있지만 단서 표의 npc는 {src['npc']}")
    for c in p.get('clue_lines', []):
        src = next((x for x in bc[clue_ids.get(c['clue'], '')]['clues'] if x['id'] == c['clue']), None) if c['clue'] in clue_ids else None
        if not src: err('npc', f"{pid} clue_lines {c['clue']} 없음")
        elif src.get('line') != c.get('line'): err('npc', f"{pid} {c['clue']} clue_lines 대사가 다름")

# ───── 4. 컷신 기억 줄 ─────
for fn in [f for f in files if f.startswith('cutscenes_')]:
    for c in files[fn]['cutscenes']:
        for s in c['steps']:
            l = s.get('line')
            if l and l.get('style') == 'memory':
                spk = l['speaker']
                if spk in SOUL and l['text'] != SOUL[spk]['memory']:
                    err(fn, f"{c['id']} t={s['t']} 기억 줄이 원본과 다름")

# ───── 5. F 번호 ─────
F_RE = re.compile(r'\bF(\d{1,2})\b')
for fn, d in files.items():
    for p, v in walk(d):
        if isinstance(v, str):
            for m in F_RE.findall(v):
                if f'F{m}' not in FACTS: err(fn, f'{p}: 없는 단서 F{m}')

# ───── 6. 별명(무적 혼) ─────
m3 = {r['id']: r for r in files['memories_act3.json']['souls']}
for x in files['npc_act3.json']['nickname_lines']:
    r = m3.get(x['soul'])
    if not r or not r['mujeok'] or r['nickname'] != x['nickname']: err('npc_act3', f"별명 {x['soul']} {x['nickname']} 어긋남")
nick_souls = {x['soul'] for x in files['npc_act3.json']['nickname_lines']}
for r in m3.values():
    if r['mujeok'] and r['nickname'] and r['id'] not in nick_souls: err('npc_act3', f"{r['id']} 별명 '{r['nickname']}'을 말하는 사람이 없음")
fun3 = {f['soul']: f for f in files['funerals_act3.json']['funerals']}
for sid, f in fun3.items():
    if bool(f.get('mujeok')) != bool(m3[sid]['mujeok']): err('funerals_act3', f'{sid} 무적 표시가 기억 데이터와 다름')

# ───── 7. 글 규칙(금지어·밤 번호·초혼·이름·추위) ─────
BANNED = ['신과함께', '강림', '해원맥', '덕춘', 'Along with the Gods', '멸귀수도전', '도깨비의 세계', '디아블로', 'Diablo', '슈퍼캣', 'Supercat']
NIGHT_NO = re.compile(r'밤 ?\d{2,3}(?![:\d])')   # "밤 13:00"(세션 시각)은 제외
COLD = re.compile(r'차누|춥|추워|한기|으슬')
for fn, d in files.items():
    for p, v in walk(d):
        if not isinstance(v, str): continue
        for w in BANNED:
            if w in v: err(fn, f'{p}: IP 금지어 "{w}"')
        if fn != 'soul_memories.json' and fn not in ('memories_act1.json',) and NIGHT_NO.search(v) and 'nights' not in p:
            err(fn, f'{p}: 밤 번호가 남아 있음 "{NIGHT_NO.search(v).group()}"(월드 시계 전환으로 무효)')
        if '초혼' in v and fn != 'endings_s1.json' and '전용' not in v:   # 규칙을 설명하는 글은 제외
            err(fn, f'{p}: "초혼"은 결말 A 전용')
        if '동이' in v and fn not in ('endings_s1.json', 'soul_memories.json') and '동이 트' not in v:
            err(fn, f'{p}: 이름 "동이"는 결말 A에서만')
        # 추위 말: 산 사람의 대사·혼잣말 칸에서만 본다(규칙 설명 칸 제외). 박돌쇠 아내 한 줄은 허용
        if fn != 'endings_s1.json' and COLD.search(v) and re.search(r'\.(text|line|line_half|barks\.[^.]+\[\d+\])$', p) and '어째 이리 차누' not in v:
            err(fn, f'{p}: 추위 말 "{v}"(당할미 외 금지)')

# ───── 결과 ─────
print(f'검사한 파일 {len(files)}개, 혼 {len(SOUL)}, 사람 {len(NPC)}, 단서 {len(clue_ids)}')
if ERR:
    print(f'어긋남 {len(ERR)}건'); [print(' -', e) for e in ERR]; sys.exit(1)
print('어긋남 0건 → 통과')
