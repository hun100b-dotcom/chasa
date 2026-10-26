# -*- coding: utf-8 -*-
# 3막(⑤ 갯마을 포구 · ⑥ 도성 아랫마을) 산 사람 초안 생성기 — npc_act2.py와 같은 모양.
# 왜 지금은 초안인가: 3막 지도가 아직 없다. 그래서 "누가 사는가 + 혼잣말(barks) + 단서 대사 + 별명 대사"만 먼저 정하고,
# 시간표(schedule)·좌표는 기획 3막 지도가 나오면 2막처럼 지도 파일에서 읽어 붙인다.
# 3막에서 더한 것: nickname_lines — ⑥ 무적 혼은 낮에 그 별명을 엿들어야 그 밤 천도할 수 있다.
#   그래서 별명을 말하는 산 사람이 꼭 있어야 하고, 그 대사는 이 파일에만 있다(별명 목록은 memories_act3.json의 nickname).
# 실행: python3 tools/npc_act3.py → docs/narrative/npc_act3.json
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'npc_act3.json')
ND = os.path.join(HERE, '..', 'docs', 'narrative')
BC = json.load(open(os.path.join(ND, 'boss_clues_act3.json'), encoding='utf-8'))
MEMS = {r['id']: r for r in json.load(open(os.path.join(ND, 'memories_act3.json'), encoding='utf-8'))['souls']}
CLUES = {c['id']: c for b in BC['boss_clues'].values() for c in b['clues']}

# barks 규칙(1·2막과 같음):
#  - 시간대마다 0~3줄, 12자 안팎. 산 사람의 혼잣말이고 단서가 아니다(기록 안 함).
#  - 보스 단서와 겹치는 말 금지: 만선호·선장·헛묘 수·장부·빗(⑤) / 왕초·기둥 별명·서생·방·붓(⑥).
#  - 보스 숫자(마흔둘·일곱) 금지. 추위 말 금지.
#  - 이름은 짓지 않고 역할로 부른다. 별명은 ⑥ 무적 혼을 위한 것이라 nickname_lines에서만 말한다.
NPCS = [
 # ───── ⑤ 갯마을 포구 ─────
 {'id': 'N-501', 'name': '그물 깁는 아낙들', 'region': 5, 'zone': 'Harbor', 'link_soul': None,
  'role': '그물 너는 마당에서 그물을 깁는 아낙들. 만선호 이야기는 보스 단서(B09-D2) 대사로만',
  'barks': {'낮': ['그물코 또 터졌네.', '볕 좋을 때 말려.', '바늘 어디 뒀어?'], '저녁': ['그물 걷어야지.']}},
 {'id': 'N-502', 'name': '헛묘지기 손자', 'region': 5, 'zone': 'WaitingRock', 'link_soul': 'S-086',
  'role': '헛묘지기 영감(S-086)의 손자. 할아버지 장례 뒤 곶 아래 무덤 풀을 뽑는다',
  'barks': {'낮': ['풀이 또 났네.', '삽이 무겁다.']}},
 {'id': 'N-503', 'name': '객주', 'region': 5, 'zone': 'Harbor', 'link_soul': None,
  'role': '포구 객주 집 주인. 배와 짐을 적는다. 장부 펼치는 모습은 보스 단서(B10-D1)라 barks와 섞지 않는다',
  'barks': {'낮': ['뱃삯은 선불이오.', '젓갈 몇 독이요?'], '저녁': ['등불 내걸어라.']}},
 {'id': 'N-504', 'name': '포구 주막 노인', 'region': 5, 'zone': 'Harbor', 'link_soul': None,
  'role': '포구 주막을 지키는 노인. 선장 이야기는 보스 단서(B10-D2) 대사로만',
  'barks': {'낮': ['탁주 한 사발 더?'], '저녁': ['바람이 바뀌었구먼.', '물 들어오는 소리네.']}},
 # ───── ⑥ 도성 아랫마을 ─────
 {'id': 'N-601', 'name': '다리 밑 아이들', 'region': 6, 'zone': 'BridgeUnder', 'link_soul': None,
  'role': '다리 밑 떠돌이 아이들. 왕초 이야기(B11-D1·D2)와 동무 별명(쥐똥이·외팔이)을 말한다',
  'barks': {'낮': ['내 차례야!', '거적 개 놔.', '엿장수 왔다!'], '저녁': ['불 피우자.']}},
 {'id': 'N-602', 'name': '아들 문지기', 'region': 6, 'zone': 'CityGate', 'link_soul': 'S-107',
  'role': '성문 문지기(S-107)의 아들. 아버지 장례 뒤 문지기 일을 잇는다. 방 붙이는 모습은 보스 단서(B12-D1)',
  'barks': {'낮': ['통행패 보이시오.'], '저녁': ['문 닫소! 서두르시오!']}},
 {'id': 'N-603', 'name': '성문 밖 주막 노파', 'region': 6, 'zone': 'CityGate', 'link_soul': None,
  'role': '성문 밖에서 사십 년 넘게 주막을 해 온 노파. 서생 이야기는 보스 단서(B12-D2) 대사로만',
  'barks': {'낮': ['국 데워 줄까.'], '저녁': ['문 닫혔어, 자고 가.']},
  'special': {'B12_force_hint': '내일 밤엔 눈밭에 나가지들 마.', 'note': 'B-12 강제 개방 전날 저녁 한 번만(boss_clues_act3 B-12 force_hint)'}},
 # 별명을 말할 사람이 더 필요해서 둘을 더했다(무적 혼 천도 조건 때문 — 서사 10-25)
 {'id': 'N-604', 'name': '저잣거리 상인들', 'region': 6, 'zone': 'Market', 'link_soul': None,
  'role': '좌판 상인들. 장터 무적 혼(곰·키다리·끗발)의 별명을 말한다',
  'barks': {'낮': ['싸요 싸!', '떨이요, 떨이!', '자리 비켜!'], '저녁': ['좌판 걷자.']}},
 {'id': 'N-605', 'name': '움막촌 이웃 아낙', 'region': 6, 'zone': 'Shacks', 'link_soul': None,
  'role': '움막촌 아낙. 움막촌 무적 혼(복실이 어멈·여울 아재·삼신 할미)의 별명을 말한다. 움막촌 어미(S-105) 장례에서 배냇저고리에 이름을 바느질하는 사람',
  'barks': {'낮': ['물 길러 가야지.', '애 업고 어딜 가.'], '저녁': ['아궁이 불 봐라.']}},
]

# 별명 대사: (말하는 사람, 무적 혼, 대사, 반쪽). 반쪽에도 별명이 남아야 한다 — 업 10이어도 별명은 들린다.
# 업 60 이상이면 소문이라 닫힌다(그러면 ⑥은 파혼만 남는 고을이 된다 — 기획서 의도).
# 왜 이렇게 쓰나: 별명만 알려 주고 그 사람의 사연(F 단서)은 말하지 않는다. 사연은 천도 기억이 말한다.
NICK = [
 ('N-604', 'S-104', '곰이 없으니 짐이 안 줄어.', '곰이 없으니…'),
 ('N-604', 'S-110', '키다리가 안 보이네, 짐은 누가 지나.', '키다리가 안 보이네…'),
 ('N-604', 'S-111', '끗발 영감 자리가 비었구먼.', '끗발 영감 자리가…'),
 ('N-605', 'S-105', '복실이 어멈 빨래가 아직 걸려 있네.', '복실이 어멈 빨래가…'),
 ('N-605', 'S-113', '여울 아재네 움막이 비었더라.', '여울 아재네 움막이…'),
 ('N-605', 'S-114', '삼신 할미가 받은 애가 벌써 걷네.', '삼신 할미가 받은 애가…'),
 ('N-601', 'S-106', '쥐똥이 자리 비워 둬. 걔 자리야.', '쥐똥이 자리 비워…'),
 ('N-601', 'S-109', '외팔이 형이 돌팔매 일등이었는데.', '외팔이 형이 돌팔매…'),
]
nick_lines = []
for npc, soul, line, half in NICK:
    m = MEMS[soul]
    assert m['mujeok'] and m['nickname'] and m['nickname'] in half, soul   # 별명 목록과 어긋나면 멈춘다
    nick_lines.append({'npc': npc, 'soul': soul, 'nickname': m['nickname'], 'zone': m['zone'],
                       'line': line, 'line_half': half, 'time': '낮', 'karma_close': 60})

for n in NPCS:
    n['clue_lines'] = [{'clue': c['id'], 'verb': c['verb'], 'place': c['place'], **({'line': c['line'], 'line_half': c['line_half']} if c.get('line') else {})}
                       for c in CLUES.values() if c.get('npc') == n['id']]
    n['nickname_lines'] = [x['soul'] for x in nick_lines if x['npc'] == n['id']]
    n['unlock'] = '3막 금줄(강둑길·큰길·갱도 출구)이 풀린 뒤 = 2막 보스 넷을 모두 처결한 밤의 다음 새벽. ⑤⑥ 순서 자유'

# ───── 시간표: 기획 3막 지도(act3_map.json의 npc_schedules)의 자리·시간대를 그대로 쓴다(10-25) ─────
# 왜: 자리·좌표는 기획 몫, 말·단서는 서사 몫. 같은 내용을 두 번 적으면 어긋난다.
# 지도에 없는 사람(N-604·605, 서사가 별명 때문에 더함)은 schedule이 비어 있고 기획에 요청해 둔다.
import re
MAP = '/mnt/project-files/planning/openworld/act3/act3_map.json'
amap = json.load(open(MAP, encoding='utf-8')) if os.path.exists(MAP) else None
for n in NPCS:
    key = next((k for k in (amap or {}).get('npc_schedules', {}) if k.split(' ')[0] == n['id']), None)
    if not key:
        n['schedule'] = None
        continue
    sched = []
    for t, rows in amap['npc_schedules'][key].items():
        for r in rows:
            e = {'time': t, 'place': r['place'], 'x': r.get('x'), 'y': r.get('y'), 'verb': r.get('verb'), 'clue': r.get('clue')}
            c = CLUES.get(r.get('clue'))
            if c and c.get('line'):
                e['line'], e['line_half'] = c['line'], c['line_half']
            if r.get('memo'):
                e['note'] = r['memo']
            sched.append(e)
    n['schedule'] = sched
    times = {e['time'] for e in sched}
    n['barks'] = {t: v for t, v in n['barks'].items() if t in times}  # 서 있지 않는 시간대의 말은 뺀다

no_nick = [k for k, v in MEMS.items() if v['mujeok'] and not v['nickname']]
data = {
 '_설명': '3막 산 사람 초안(서사 10-25). 단서 대사는 boss_clues_act3.json과 같은 글자, 별명은 memories_act3.json의 nickname과 같다. 시간표·좌표는 3막 지도가 나오면 붙인다',
 '_version': 1,
 'zones': {'Harbor': '포구', 'SaltField': '소금밭', 'WaitingRock': '망부석 곶', 'WreckShoal': '난파 여울',
           'Market': '저잣거리', 'BridgeUnder': '큰 다리 밑', 'Shacks': '움막촌', 'CityGate': '성문 밖'},
 'rules': {
  'barks': '시간대마다 0~3줄, 12자 안팎. 단서 아님, 기록 안 함. 보스 단서·F 단서·추위 말 금지',
  'speaker': '모든 말은 산 사람의 혼잣말이거나 산 사람끼리 하는 말이다. 차사에게 하지 않는다',
  'names': '3막 산 사람은 이름 없이 역할로 부른다. 별명은 무적 혼의 것만, nickname_lines에서만',
  'nickname': '엿들은 때부터 그 무적 혼을 천도할 수 있다(10-26 \'그날 밤\' → \'들은 때부터\' — 낮 필드의 무적 혼도 같은 규칙, field_nicknames_act3.json). 추리판에 기록되지 않고 혼 머리 위와 처결 카드 ▲ 칸에 별명이 뜬다. 엿듣기 말풍선 속 별명은 ▲ 칸과 같은 색. 업 10: 반쪽(별명은 들림) / 업 60: 닫힘',
  'no_nickname': '별명을 아는 산 사람이 없는 오래된 무적 혼 %s는 B-11 왕초 천도 뒤에만 천도할 수 있다' % ', '.join(sorted(no_nick)),
 },
 'npcs': NPCS,
 'nickname_lines': nick_lines,
}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(NPCS), 'npcs,', len(nick_lines), 'nickname lines')
