# 1막(① 솔고개 · ② 검은여울) 천도 '기억 조각' 데이터 생성기
# 왜 따로 만드나: soul_memories.json(원본, 혼 202·백 120)은 시즌 1~3 전체라 크다.
# 코드 6단계(성장)·7단계(첫 보스)는 1막만 쓰므로, 원본에서 1막 혼만 뽑아 쓰기 쉬운 모양으로 옮긴다.
# 원본이 바뀌면 이 스크립트를 다시 돌린다(손으로 고치지 않는다 — 원본이 하나여야 어긋나지 않는다).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'docs', 'narrative', 'soul_memories.json')
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'memories_act1.json')
d = json.load(open(SRC, encoding='utf-8'))

# 떠돈 시간 등급(혼의 나이). 보스는 원본 type이 'boss'라서 이야기 기준으로 따로 적는다.
AGE = {'fresh': '갓 죽은', 'year': '해 넘긴', 'old': '오래된'}
BOSS_AGE = {'B-01': 'year', 'B-02': 'year', 'B-03': 'year'}  # 셋 다 몇 해 전(큰물·역병)에 죽었다

# 단서(F)가 메인 미스터리 "저승이 고장 났다"에 어떻게 닿는가
AXIS = {}
for f in ['F1', 'F3', 'F4', 'F5', 'F6', 'F7', 'F12', 'F13', 'F14', 'F15']: AXIS[f] = 'main'   # 고장 그 자체와 원인
for f in ['F10', 'F11']: AXIS[f] = 'mirror'    # 이승 관아도 이름을 지웠다(거울)
for f in ['F8', 'F9']: AXIS[f] = 'self'        # 나는 누구인가
AXIS['F2'] = 'background'                     # 큰물 밤(모든 일의 시작)

ZONE_NIGHTS = {'Village': '2~4', 'Field': '2~4', 'Ravine': '4~6', 'Shrine': '7~10',
               'Market': '13~15', 'Yamen': '14~17', 'Plague': '16~20', 'Graves': '18~22'}

rows = []
for s in d['souls']:
    if s.get('region') not in (1, 2) or s.get('type') == 'baek' or s.get('layer') == 'below':
        continue  # 1막 = 관할 ①②의 혼과 보스만(시즌 3 백 제외)
    t = BOSS_AGE.get(s['id'], s['type'])
    f = s.get('fact')
    rows.append({
        'id': s['id'], 'name': s['name'], 'region': s['region'], 'zone': s['zone'],
        'nights': ZONE_NIGHTS.get(s['zone']),
        'age': t, 'age_ko': AGE.get(t), 'boss': s['type'] == 'boss',
        'seal': s['seal'],              # clear 또렷 / faded 흐림(+0.25초) / missing 없음(+0.5초)
        'memory_id': s['memory_id'], 'memory': s['memory'], 'tint': s.get('tint'),
        'fact': f, 'fact_text': d['facts'].get(f) if f else None,
        'mystery': bool(f), 'mystery_axis': AXIS.get(f) if f else None,
        'decisive': s.get('weight') == 'decisive',  # ★ 전모 단서(보스 천도로만)
        'weight': s.get('weight'), 'funeral': s.get('funeral'),
    })
rows.sort(key=lambda r: (r['region'], r['boss'], r['id']))
out = {
    '_설명': '1막(① 솔고개 · ② 검은여울) 천도 기억 조각. 원본 soul_memories.json에서 tools/memories_act1.py로 생성. 손으로 고치지 말 것.',
    'source_version': d.get('_version'),
    'rules': {
        'count': '천도 1회 = 기억 조각 1(결말 기준 150에 셈). 같은 혼은 한 번만',
        'mystery': 'mystery=true인 혼을 천도하면 그 fact가 추리판에 켜진다. decisive(★)는 보스 천도로만',
        'axis': {'main': '저승이 고장 났다(고장과 원인)', 'mirror': '이승 관아도 이름을 지웠다', 'self': '나는 누구인가', 'background': '큰물 밤'},
        'generic': '이름 없는 무작위 혼은 generic 줄에서 뽑는다(미스터리 없음, 한 판에 한 줄 한 번)',
        'pahon': '파혼하면 기억 조각 없음, 그 혼의 fact 출처 하나를 잃는다(추리판에 번진 먹 자국)'},
    'souls': rows,
    'generic': {k: v for k, v in d['generic_pool'].items() if not k.startswith('_')},
    'facts': {k: d['facts'][k] for k in ['F%d' % i for i in range(1, 16)]},
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(rows), 'souls,', sum(r['mystery'] for r in rows), 'mystery')
