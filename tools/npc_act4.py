# -*- coding: utf-8 -*-
# 4막 ⑦ 삼도천 기슭 '말하는 이' 초안 생성기 — npc_act1~3.py와 같은 모양(⑧은 다음 차례).
# 왜 '산 사람'이 아니라 '말하는 이'인가: ⑦~⑩엔 산 사람이 없다(시즌 2 규칙). 대신 이미 천도되어 배를 기다리는
#   '줄 선 혼'들이 말한다. 이들은 처결 대상이 아니다(때리면 돌아선 혼이 된다 — B-13 전투 규칙과 같음).
#   모두 차사에게 직접 말하지 않는다. 들으라는 듯 저희끼리 떠들 뿐이다(SCENARIO-ACT4 §0).
# 시간표 칸: 시즌 1의 '낮'은 ⑦에서 '새벽 틈'(동트기 직전 새벽)이다. 보스 단서는 새벽 틈에만 들린다.
# 좌표(x, y)는 기획 ⑦ 지도가 나오면 act3처럼 지도 파일에서 읽어 붙인다. 지금은 장소 이름만.
# 실행: python3 tools/npc_act4.py → docs/narrative/npc_act4.json
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.join(HERE, '..', 'docs', 'narrative')
OUT = os.path.join(ND, 'npc_act4.json')
S2 = json.load(open(os.path.join(ND, 'season2_outline.json'), encoding='utf-8'))
MEMS = {r['id']: r for r in json.load(open(os.path.join(ND, 'memories_act4.json'), encoding='utf-8'))['souls']}
CLUES = {c['id']: c for b in S2['boss_clues'].values() for c in b['clues']}

# barks(혼잣말) 규칙 — 1~3막과 같음:
#  - 시간대마다 0~3줄, 12자 안팎. 단서가 아니다(기록 안 함).
#  - 보스 단서와 겹치는 말 금지: 먼저 가시오·칼금·엽전·노잣돈(B-13) / 둑·쪽지(B-14).
#  - 추위 말 금지(당할미만 느낀다). 이름 금지(역할로 부른다). 사공의 정체·어미 이름은 시즌 4 고리라 말하지 않는다.
BANNED_IN_BARKS = ('먼저 가시오', '칼금', '엽전', '노잣돈', '둑', '쪽지', '춥', '추워', '한기', '차누', '으슬')

NPCS = [
 {'id': 'N-701', 'name': '줄 선 혼들(줄 가운데)', 'region': 7, 'zone': 'Ferrytown', 'link_soul': None,
  'role': '이승에서 천도되어 나루까지 왔지만 배를 기다리는 혼들. 처결 대상 아님(장애물). B-13 노인 이야기는 단서(B13-D1) 대사로만',
  'barks': {'밤': ['배 언제 와.', '한 칸도 안 움직였어.', '앞에 누구 있소?'],
            '새벽 틈': ['물안개 걷힌다.', '저기 건너편 보여?']},
  'schedule': [
   {'time': '밤', 'place': '줄 가운데', 'verb': None, 'clue': None, 'note': '줄을 지킨다. 밤 혼(처결 대상)이 줄 옆을 떠돈다'},
   {'time': '새벽 틈', 'place': '줄 가운데', 'verb': '엿듣기', 'clue': 'B13-D1', 'note': 'Ferrytown에 밤에 처음 들어간 다음 새벽 틈부터'},
   {'time': '낮', 'place': '줄 가운데', 'verb': None, 'clue': None, 'note': '말없이 선다(저승의 낮은 고요하다)'},
   {'time': '저녁', 'place': '줄 가운데', 'verb': None, 'clue': None}]},
 {'id': 'N-702', 'name': '줄 끝의 새로 온 혼들', 'region': 7, 'zone': 'Ferrytown', 'link_soul': None,
  'role': '막 도착해 줄 끝에 선 혼들. 시즌 1에서 내가 천도한 이름혼도 여기 선다(말없이 고개를 숙인다, C-15). B-14 처결 뒤 주운 쪽지 수만큼 희미한 혼이 이 뒤에 다시 선다',
  'barks': {'밤': ['여기가 끝이오?', '뒤에 또 오네.'], '새벽 틈': ['줄이 참 길다.']},
  'schedule': [
   {'time': '밤', 'place': '줄 끝', 'verb': None, 'clue': None},
   {'time': '새벽 틈', 'place': '줄 끝', 'verb': None, 'clue': None},
   {'time': '낮', 'place': '줄 끝', 'verb': None, 'clue': None},
   {'time': '저녁', 'place': '줄 끝', 'verb': None, 'clue': None}]},
 {'id': 'N-703', 'name': '마지막 사공', 'region': 7, 'zone': 'Ferrytown', 'link_soul': None,
  'role': '백 년째 배 한 척을 젓는 사공. 말하지 않는다. 노를 저을 때 입술만 움직인다(누군가의 이름, 소리 없음 — S-126 기억과 맞물림). 정체는 5막 ⑩에서 F45로, 더 깊은 것은 시즌 4 고리',
  'barks': {},
  'silent': True,
  'schedule': [
   {'time': '밤', 'place': '강 위', 'verb': '지켜보기', 'clue': None, 'note': '배가 하류 안개 속으로 반쯤 갔다가 돌아온다(F12 — 하류가 막혀 끝까지 못 간다). 단서 아님, 풍경'},
   {'time': '새벽 틈', 'place': '나루 말뚝 앞', 'verb': None, 'clue': None, 'note': '배가 잠깐 닿는다. 몇 혼만 탄다. 줄은 줄지 않는다'},
   {'time': '낮', 'place': '강 위', 'verb': None, 'clue': None},
   {'time': '저녁', 'place': '강 위', 'verb': None, 'clue': None}]},
 {'id': 'N-704', 'name': '두 번째 배 사공', 'region': 7, 'zone': 'Ferrytown', 'link_soul': None,
  'role': 'B-13 천도로 배가 두 척이 된 뒤에만 나온다. 시즌 1에서 흑월(B-12)을 천도했다면 갓을 쓴 흑월, 아니면 이름 없는 차사 혼. 첫 사공과 강 위에서 서로 갓을 숙인다. 말하지 않는다',
  'barks': {},
  'silent': True,
  'appears': {'need': 'B-13 천도', 'variant': {'B-12 천도(시즌 1)': '흑월', '그 밖': '이름 없는 차사 혼'}},
  'schedule': [
   {'time': '밤', 'place': '강 위', 'verb': None, 'clue': None, 'note': '⑦~⑩ 귀환 단축(배 두 척)'},
   {'time': '새벽 틈', 'place': '나루 말뚝 앞', 'verb': None, 'clue': None}]},
]

# 단서 대사 붙이기 — 원본은 season2_outline.json의 단서 표 하나. 여기서 베껴 오기만 한다(어긋나지 않게).
for p in NPCS:
    p['unlock'] = '시즌 2 첫 진입부터(C-14 뒤)'
    p['clue_lines'] = []
    for e in p['schedule']:
        if e.get('clue'):
            c = CLUES[e['clue']]
            assert c.get('npc') == p['id'], (e['clue'], c.get('npc'))
            e['line'], e['line_half'] = c['line'], c['line_half']
            p['clue_lines'].append({'clue': c['id'], 'verb': c['verb'], 'place': c['place'], 'line': c['line'], 'line_half': c['line_half']})
    for t, xs in p['barks'].items():
        for x in xs:
            assert not any(w in x for w in BANNED_IN_BARKS), (p['id'], x)
            assert len(x) <= 14, (p['id'], x)
# 말하는 이가 필요한 단서(⑦ 엿듣기)는 빠짐없이 누군가 말해야 한다
for c in CLUES.values():
    if c['verb'] == '엿듣기' and c['zone'] in ('Reeds', 'Ferrytown', 'InkRapids', 'Dam'):
        assert any(cl['clue'] == c['id'] for p in NPCS for cl in p['clue_lines']), c['id']

out = {
    '_설명': '4막 ⑦ 삼도천 기슭의 말하는 이 초안(⑧은 다음 차례). tools/npc_act4.py로 생성. 손으로 고치지 말 것. 좌표는 기획 ⑦ 지도가 나오면 붙인다',
    '_version': '2026-10-25 초안',
    'zones': {k: v for k, v in S2['world']['regions']['7']['zones'].items()},
    'rules': {
        'no_living': '⑦엔 산 사람이 없다. 말하는 이는 이미 천도되어 배를 기다리는 줄 선 혼들이고 처결 대상이 아니다. 때리면 돌아선 혼(처결 대상)이 된다',
        'speaker': '모든 말은 저희끼리 하는 말이다. 차사에게 하지 않는다. 들으라는 듯 떠들 뿐',
        'dawn_gap': '보스 단서 대사는 새벽 틈(동트기 직전 새벽)에만 들린다. 시즌 1의 낮 칸에 해당',
        'barks': '시간대마다 0~3줄, 12자 안팎. 단서 아님, 기록 안 함. 보스 단서·F 단서·추위 말·이름 금지',
        'karma_seen': '업 10 반쪽 / 30 가까운 줄 선 혼이 등을 돌리고 보스 엿듣기 닫힘 / 60 줄 전체가 등을 돌리고 혼잣말도 멈춤',
        'silent': '사공(N-703·704)은 말하지 않는다. 입 모양·몸짓만. 대사 수에 세지 않는다',
        'line_count': '이 파일의 말은 혼잣말과 단서 대사뿐이라 대사 15줄 상한·보스 말풍선 어느 쪽에도 세지 않는다',
    },
    'npcs': NPCS,
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(NPCS), 'speakers,', sum(len(p['clue_lines']) for p in NPCS), 'clue lines')
