# 3막(⑤ 갯마을 · ⑥ 도성) 천도 '기억 조각' 데이터 생성기 — memories_act2.py와 같은 모양
# 3막에서 더한 것: water(⑤ 물 혼 — 시신 없음, 캐스팅 −0.5초, 밀물에 떠밀림)와
#   mujeok/nickname(⑥ 무적 혼 — 낮에 별명을 엿들어야 천도 가능. 별명을 말하는 산 사람 대사는 npc_act3.json).
# 다른 점: 월드 시계가 이어서 흐르므로 '나오는 밤(nights)' 칸은 넣지 않는다(밤 단위 폐지, 10-25).
# 왜 따로 만드나: soul_memories.json(원본, 혼 202·백 120)은 시즌 1~3 전체라 크다.
# 코드가 막 단위로 읽기 쉽게, 원본에서 2막 혼만 뽑아 옮긴다.
# 원본이 바뀌면 이 스크립트를 다시 돌린다(손으로 고치지 않는다 — 원본이 하나여야 어긋나지 않는다).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'docs', 'narrative', 'soul_memories.json')
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'memories_act3.json')
d = json.load(open(SRC, encoding='utf-8'))

# 떠돈 시간 등급(혼의 나이). 보스는 원본 type이 'boss'라서 이야기 기준으로 따로 적는다.
AGE = {'fresh': '갓 죽은', 'year': '해 넘긴', 'old': '오래된'}
BOSS_AGE = {'B-09': 'year', 'B-10': 'year', 'B-11': 'year', 'B-12': 'old'}  # 아낙·선장·왕초는 몇 해 안 됨 / 흑월은 사십 년

# 단서(F)가 메인 미스터리 "저승이 고장 났다"에 어떻게 닿는가
AXIS = {}
for f in ['F24', 'F27', 'F28', 'F29']: AXIS[f] = 'main'      # 저승 쪽 고장(외 몇 명으로 차사를 뽑음, 서생=흑월, 횃불 젊은이, 차사 여럿)
for f in ['F23', 'F30']: AXIS[f] = 'body'                    # 몸은 물 밑에 남는다(시즌 3 백의 밤)
for f in ['F25', 'F26']: AXIS[f] = 'mirror'                  # 이승 호적에 없으면 명부에도 없다 / 이름은 불러 주는 사람이 만든다
AXIS['F9'] = 'self'

# ⑤ 물 혼: 시신이 바다에서 돌아오지 않은 혼(원본에 표시가 없어 서사가 정함). 기억에 '몸이 물에 있다'는 결이 있는 혼.
WATER = {'S-090', 'S-091', 'S-093', 'S-097', 'S-098', 'S-099', 'B-09', 'B-10'}
# 장례가 있는 혼(S-085~089)은 몸이 돌아온 혼이라 넣지 않는다(갯마을에서 귀한 '몸 있는 장례').

# ⑥ 무적 혼: 호적에 오른 적 없는 혼. 낮에 별명을 엿들으면 그 밤 천도 가능(B-11 천도 뒤엔 전원 가능).
# nickname=None인 혼은 별명을 기억하는 산 사람이 없다(오래된 혼) → B-11 천도 뒤에만 천도할 수 있다.
MUJEOK = {
    'S-104': '곰', 'S-105': '복실이 어멈', 'S-106': '쥐똥이', 'S-109': '외팔이', 'S-110': '키다리',
    'S-111': '끗발', 'S-113': '여울 아재', 'S-114': '삼신 할미',
    'S-115': None, 'S-116': None, 'S-118': None, 'S-119': None,  # 보스 B-11(왕초)은 넣지 않는다 — 보스는 단서 3개 규칙만 따른다
}

# 제사 집 지켜보기 덧붙임 한 줄(기획 부록 B-4, 서사 10-25).
# 낮에 그 집 제사를 지켜본 뒤 그 이름혼을 천도하면 기억 끝에 한 줄이 더 붙는다.
# 왜 이렇게 쓰나: 기억 조각 수(결말 150)에 세지 않는 "덤"이라, 새 F 단서나 보스 단서를 담으면 안 된다.
# 그래서 사건이 아니라 그 사람의 손버릇·식구·마지막 하루 같은 삶의 결만 쓴다(1인칭, 기억과 같은 목소리).
JESA_EXTRA = {
    'S-085': '며느리 손은 빠르다. 그물코 세는 것만 아직 서툴지.',
    'S-086': '삽자루는 손자 키에 맞춰 잘라 두었다. 아직 좀 길 거다.',
    'S-087': '소금 지게는 왼어깨로 졌다. 오른어깨는 형 몫이라고.',
    'S-088': '저고리 고름은 내가 달았다. 어머니보다 바늘땀이 곱다.',
    'S-089': '심지는 딸이 잘랐다. 내가 자르면 늘 그을음이 났다.',
    'S-103': '떡판은 새벽마다 콩고물부터 털었다. 애들이 그걸 좋아해서.',
    'S-104': '짐은 언제나 오른어깨부터. 왼쪽은 남의 짐 받아 줄 자리.',
    'S-105': '아이는 젖 먹고 나면 꼭 내 귓불을 쥐고 잤다.',
    'S-106': '거적 밑에 엿 한 가락 감춰 뒀다. 형님 몫이었다.',
    'S-107': '빗장은 해 지고 숨 열 번 쉰 뒤에 질렀다. 혹시 몰라서.',
}

rows = []
for s in d['souls']:
    if s.get('region') not in (5, 6) or s.get('type') == 'baek' or s.get('layer') == 'below':
        continue  # 3막 = 관할 ⑤⑥의 혼과 보스만(시즌 3 백 제외)
    t = BOSS_AGE.get(s['id'], s['type'])
    f = s.get('fact')
    rows.append({
        'id': s['id'], 'name': s['name'], 'region': s['region'], 'zone': s['zone'],
        'age': t, 'age_ko': AGE.get(t), 'boss': s['type'] == 'boss',
        'seal': s['seal'],              # clear 또렷 / faded 흐림(+0.25초) / missing 없음(+0.5초)
        'memory_id': s['memory_id'], 'memory': s['memory'], 'tint': s.get('tint'),
        'fact': f, 'fact_text': d['facts'].get(f) if f else None,
        'mystery': bool(f), 'mystery_axis': AXIS.get(f) if f else None,
        'decisive': s.get('weight') == 'decisive',  # ★ 전모 단서(보스 천도로만)
        'weight': s.get('weight'), 'funeral': s.get('funeral'),
        'jesa_extra': JESA_EXTRA.get(s['id']),  # 제사 집 지켜보기 덤(조각 수에 안 셈). 없으면 null
        'water': s['id'] in WATER,               # ⑤ 물 혼(캐스팅 −0.5초, 밀물에 떠밀림, 다음 썰물 밤에 다시 떠오름)
        'mujeok': s['id'] in MUJEOK,             # ⑥ 무적 혼(별명을 엿들어야 천도)
        'nickname': MUJEOK.get(s['id']),         # 엿듣기로 듣는 별명. null + mujeok=true면 B-11 천도 뒤에만
    })
rows.sort(key=lambda r: (r['region'], r['boss'], r['id']))
# 땅의 새 규칙 혼 기억(기획 act3-entry-10min 10-26): 3막 첫 10분은 낮이고 이름혼은 밤에만 선다.
# 첫 물 혼(⑤) · 첫 무적 혼(⑥, 별명을 듣고 천도)의 천도에서 generic 대신 그 땅 줄이 나오게 해 3막 첫 기억을 2분 안으로.
# 단서 없음 · 조각 1 · 한 판에 한 줄 한 번. 3막 보스 단서 낱말 금지.
FIELD_POOL = {
    'water': ['물이 들어오는 소리를 세다가 잊었다.',
              '그물이 무거웠다. 그 뒤는 생각나지 않는다.',
              '뭍 쪽에서 누가 부르는 것 같았는데.'],
    'mujeok': ['이름은 몰라도 다들 그렇게 불렀다. 그걸로 됐다.',
               '누가 불러 주면 돌아봤다. 그게 내 이름이었다.',
               '장터에선 별명이 이름보다 빨랐다.'],
}
for _v in FIELD_POOL.values():
    for _ln in _v:
        assert len(_ln) <= 40 and not any(w in _ln for w in ('만선호', '선장', '헛묘', '장부', '빗', '왕초', '서생', '방', '붓', '마흔', '일곱', '동이')), _ln
out = {
    '_설명': '3막(⑤ 갯마을 · ⑥ 도성) 천도 기억 조각. 원본 soul_memories.json에서 tools/memories_act3.py로 생성. 손으로 고치지 말 것.',
    'source_version': d.get('_version'),
    'rules': {
        'count': '천도 1회 = 기억 조각 1(결말 기준 150에 셈). 같은 혼은 한 번만',
        'mystery': 'mystery=true인 혼을 천도하면 그 fact가 추리판에 켜진다. decisive(★)는 보스 천도로만',
        'axis': {'main': '저승이 고장 났다(외 몇 명·서생·횃불·차사 여럿)', 'body': '몸은 물 밑에 남는다(시즌 3 고리)', 'mirror': '이승 호적과 이름 부르기', 'self': '나는 누구인가'},
        'water': '물 혼: 천도 캐스팅 −0.5초(하한 0.5초). 밀물 신호 뒤 20초 안에 못 붙잡으면 그 밤은 사라진다(넋 0·기억 0). 다음 썰물 밤에 난파 여울로 다시 떠오른다',
        'mujeok': '무적 혼: 기본 천도 불가(파혼만). 낮에 그 별명을 엿들었으면 그 밤 천도 가능. nickname이 null이면 B-11 천도 뒤에만. B-11 천도 뒤엔 전원 가능',
        'generic': '이름 없는 무작위 혼은 generic 줄에서 뽑는다(미스터리 없음, 한 판에 한 줄 한 번)',
        'field_pool': '필드의 물 혼 · 무적 혼(이름혼 아님)을 천도하면 generic 대신 field_pool[water/mujeok]에서 한 줄(한 판에 한 줄 한 번, 다 쓰면 generic). 단서 없음, 조각 1',
        'jesa_extra': '낮에 그 집 제사를 지켜본 뒤 천도하면 기억 끝에 덧붙는 한 줄. 기억 조각 수에 세지 않는다. 장례 대상 이름혼만 있다',
        'pahon': '파혼하면 기억 조각 없음, 그 혼의 fact 출처 하나를 잃는다(추리판에 번진 먹 자국)'},
    'souls': rows,
    'generic': {k: v for k, v in d['generic_pool'].items() if not k.startswith('_')},
    'field_pool': FIELD_POOL,
    'facts': {k: d['facts'][k] for k in ['F%d' % i for i in range(23, 31)]},
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(rows), 'souls,', sum(r['mystery'] for r in rows), 'mystery')
