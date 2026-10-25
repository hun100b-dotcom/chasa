# -*- coding: utf-8 -*-
# 4막(⑦ 삼도천 기슭 · ⑧ 명부전 담장 밖) 천도 '기억 조각' 데이터 생성기 — memories_act1.py와 같은 틀.
# 지금은 ⑦만 담는다(코디 10-25 "⑦부터"). ⑧은 REGIONS에 8을 더하고 아래 표들을 채우면 된다.
# 왜 따로 만드나: soul_memories.json(원본)은 시즌 1~3 전체라 크다. 코드는 막 단위로 읽는 게 쉽다.
# 원본이 바뀌면 이 스크립트를 다시 돌린다(손으로 고치지 않는다 — 원본이 하나여야 어긋나지 않는다).
# 1막과 다른 점(⑦은 저승이라 산 사람이 없다):
#   - 제사 덤(jesa_extra) 대신 배웅(send_off): 상주 대신 줄 선 혼들이 하는 장례 변주(SCENARIO-ACT4 §1).
#   - 밤 번호(nights) 대신 열리는 때(opens): 월드 시계 전환으로 밤 번호는 쓰지 않는다.
#   - 돌아선 혼(turned): 이름 없는 무작위 혼 중 ⑦ 전용. 천도하면 줄로 돌아간다(넋 적음, 기억은 '기다림' 한 줄).
# 실행: python3 tools/memories_act4.py → docs/narrative/memories_act4.json
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'docs', 'narrative', 'soul_memories.json')
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'memories_act4.json')
d = json.load(open(SRC, encoding='utf-8'))

REGIONS = (7,)   # ⑧은 다음 차례

AGE = {'fresh': '갓 죽은', 'year': '해 넘긴', 'old': '오래된'}
BOSS_AGE = {'B-13': 'old', 'B-14': 'old'}   # 둘 다 백 년 가까이 기다린 혼

# 단서(F)가 메인 미스터리에 어떻게 닿는가
AXIS = {}
for f in ['F4', 'F7', 'F12', 'F13', 'F14', 'F31', 'F32', 'F33']: AXIS[f] = 'main'   # 저승 고장(줄·가루·숫자·차사)
for f in ['F8', 'F15']: AXIS[f] = 'self'                                           # 나는 누구인가(당할미의 아들)

# 구역이 언제 열리나(밤 번호 대신). 시즌 2 첫 진입 = C-14 뒤 ⑦ 나루 앞.
OPENS = {
    'Ferrytown': '시즌 2 첫 진입부터(C-14 → 줄 C-15)',
    'Reeds': '시즌 2 첫 진입부터',
    'InkRapids': '시즌 2 첫 진입부터',
    'Dam': '시즌 2 첫 진입부터(둑 너머 ⑧ 길은 B-14 처결 뒤, 못 하면 ⑦ 첫 진입 뒤 7번째 새벽에 강제로 풀림)',
}

# 배웅(⑦의 장례 변주, 약 30초, 대사 0줄). SCENARIO-ACT4 §1 표 그대로.
# 왜 원본 funeral 표시는 false인가: 원본의 funeral은 "이승 장례"다. 배웅은 저승 변주라 따로 적는다.
# 마지막 컷(#7)은 사잣밥 대신 나룻불 하나가 켜진다(시즌 1 끝에 꺼진 불이 보낸 사람 수만큼 다시 켜짐).
SEND_OFF = {
    'S-121': {'stopped': '아이가 맡아 둔 빈자리',
              'moving': '뒤에서 한 혼이 걸어와 그 자리에 선다. 엄마인지는 모른다. 아이가 손을 잡는다'},
    'S-122': {'stopped': '빈 손바닥',
              'moving': '줄 선 혼들이 엽전을 한 닢씩 건네 손바닥이 찬다',
              'if': {'B-13 천도': '노인의 구멍 닳은 엽전도 한 닢 섞여 있다'}},
    'S-125': {'stopped': '줄 밖의 발자국',
              'moving': '줄 선 혼들이 한 칸씩 물러나 그를 원래 자리에 넣어 준다'},
    'S-048': {'stopped': '강을 향해 벌린 입',
              'moving': '배에 오르기 직전 뒤돌아 이승 쪽을 본다. 입 모양이 한 이름을 부른다(소리 없음)',
              'note': '그 이름은 나의 이름이다 — F9가 있는 플레이어만 알아본다. 화면에 글자로 쓰지 않는다'},
}

# 돌아선 혼(이름 없는 무작위 혼, ⑦ 전용) 천도 때 뜨는 '기다림' 한 줄. 미스터리 없음.
# 왜 따로 두나: generic 줄(fresh·year·old)은 이승의 삶을 말한다. 돌아선 혼은 이미 한 번 천도된 혼이라 삶보다 기다림이 남았다.
# 규칙: 1인칭, 12~24자, 이름·숫자·F 단서·보스 단서 말(먼저 가시오·칼금·엽전·노잣돈) 금지, 추위 말 금지.
TURNED = [
    '줄에 서 있었다. 얼마나였는지 모른다.',
    '앞사람 등만 봤다. 얼굴은 잊었다.',
    '배가 오는 소리는 들었다. 한 번도 닿지 않았다.',
    '누가 부를 줄 알았다. 아무도 안 불렀다.',
    '내 차례가 언제였더라.',
    '돌아서니 발이 가벼웠다. 그래서 무서웠다.',
]

rows = []
for s in d['souls']:
    if s.get('region') not in REGIONS or s.get('type') == 'baek' or s.get('layer') == 'below':
        continue  # 4막 = ⑦(⑧)의 혼과 보스만. 물 밑 백은 시즌 3(6막)
    t = BOSS_AGE.get(s['id'], s['type'])
    f = s.get('fact')
    rows.append({
        'id': s['id'], 'name': s['name'], 'region': s['region'], 'zone': s['zone'],
        'opens': OPENS.get(s['zone']),
        'age': t, 'age_ko': AGE.get(t), 'boss': s['type'] == 'boss',
        'seal': s['seal'],              # clear 또렷 / faded 흐림(+0.25초) / missing 없음(+0.5초)
        'memory_id': s['memory_id'], 'memory': s['memory'], 'tint': s.get('tint'),
        'fact': f, 'fact_text': d['facts'].get(f) if f else None,
        'mystery': bool(f), 'mystery_axis': AXIS.get(f) if f else None,
        'decisive': s.get('weight') == 'decisive',  # ★ 전모 단서(보스 천도로만)
        'weight': s.get('weight'), 'funeral': s.get('funeral'),
        'send_off': SEND_OFF.get(s['id']),          # 배웅(⑦ 장례 변주). 없으면 null
    })
rows.sort(key=lambda r: (r['region'], r['boss'], r['id']))
for k in SEND_OFF: assert any(r['id'] == k for r in rows), k
for x in TURNED: assert not any(w in x for w in ('먼저 가시오', '칼금', '엽전', '노잣돈', '춥', '추워', '한기')), x

out = {
    '_설명': '4막(⑦ 삼도천 기슭, ⑧은 다음 차례) 천도 기억 조각. 원본 soul_memories.json에서 tools/memories_act4.py로 생성. 손으로 고치지 말 것.',
    'source_version': d.get('_version'),
    'rules': {
        'count': '천도 1회 = 기억 조각 1(결말 기준 150에 셈). 같은 혼은 한 번만',
        'mystery': 'mystery=true인 혼을 천도하면 그 fact가 추리판에 켜진다. decisive(★)는 보스 천도로만',
        'axis': {'main': '저승이 고장 났다(줄·가루·숫자·차사)', 'self': '나는 누구인가(당할미의 아들)'},
        'dawn_gap': '⑦엔 산 사람이 없다. 보스 단서는 새벽 틈(동트기 직전 새벽)에 줄 선 혼들에게서 엿듣고, 말뚝·노·노잣돈을 지켜보고 만진다(npc_act4.json)',
        'karma_seen': '저승도 업을 본다: 업 30 이상이면 가까운 줄 선 혼이 등을 돌리고(연출), 60 이상이면 줄 전체가 등을 돌리고 혼잣말도 멈춘다. 엿듣기 반쪽/닫힘은 시즌 1과 같음',
        'turned': '돌아선 혼(이름 없는 무작위 혼, ⑦ 전용): 천도하면 줄 끝으로 돌아간다. 넋 적음. 기억은 turned 줄에서 한 줄(미스터리 없음). generic과 같이 셈',
        'dam': '⑦~⑩에서 파혼하면 가루가 곧장 하류 큰 물막이(B-20)에 쌓여 물막이 눈금이 오른다(F32). 이름 줍기(1.5초 뜨는 쪽지를 사슬로 낚기)에 성공하면 절반만 오른다(F33). B-14는 선택이 없어 업 +0',
        'send_off': '배웅: 상주 대신 줄 선 혼들이 하는 장례 변주(약 30초, 대사 0줄). #2 멈춘 것 → #6 다시 움직이는 것 → #7 나룻불 하나가 켜진다. 천도 뒤 그 혼이 줄로 돌아가는 다음 새벽에',
        'season1_line': '시즌 1에서 천도한 이름혼은 ⑦ 줄에 서서 나를 보면 고개를 숙인다. 파혼한 혼의 자리는 번진 먹 자국(C-15). 천도 대상이 아니다',
        'pahon': '파혼하면 기억 조각 없음, 그 혼의 fact 출처 하나를 잃는다(추리판에 번진 먹 자국)'},
    'souls': rows,
    'turned': TURNED,
    'generic': {k: v for k, v in d['generic_pool'].items() if not k.startswith('_')},
    'facts': {k: d['facts'][k] for k in sorted({r['fact'] for r in rows if r['fact']}, key=lambda x: int(x[1:]))},
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(rows), 'souls,', sum(r['mystery'] for r in rows), 'mystery,', len(SEND_OFF), 'send_off')
