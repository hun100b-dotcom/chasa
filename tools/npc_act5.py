# -*- coding: utf-8 -*-
# 5막(⑨ 빈 관할 · ⑩ 열째 관할) '말하는 이' 초안 생성기 — npc_act4.py와 같은 모양.
# ⑨는 인 없는 혼들(죽어도 아무도 데리러 오지 않아 기다리다 늙은 혼), ⑩은 옛 차사들이 말한다.
# 이들은 처결 대상이 아니라 배경 무리다(⑨의 이름 있는 혼·⑩ 이름 조각과는 따로). 차사에게 직접 말하지 않는다.
# ⑨는 새벽 틈이 없다 → 보스 단서 대사는 '언제나' 들린다(먹지기의 흔적 둘레). ⑩은 새벽 틈이 돌아온다.
# 좌표는 기획 ⑨·⑩ 지도가 나오면 붙인다. 지금은 장소 이름만.
# 실행: python3 tools/npc_act5.py → docs/narrative/npc_act5.json
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.join(HERE, '..', 'docs', 'narrative')
OUT = os.path.join(ND, 'npc_act5.json')
S2 = json.load(open(os.path.join(ND, 'season2_outline.json'), encoding='utf-8'))
CLUES = {c['id']: c for b in S2['boss_clues'].values() for c in b['clues']}

# barks 금지 말: 보스 단서·F 단서와 겹치는 것, 추위, 이름.
#  ⑨: 인·문지기·졸다·도둑·이마·굴·종 / ⑩: 첫 차사·어미·우물·신발·새끼줄·사공·노·사슬(사슬 무덤 이야기는 단서 몫)
BANNED_IN_BARKS = ('인', '문지기', '졸', '도둑', '이마', '굴', '종',
                   '첫 차사', '어미', '우물', '신발', '새끼줄', '사공', '노 ', '사슬',
                   '춥', '추워', '한기', '차누', '으슬')

NPCS = [
 # ───── ⑨ 빈 관할 (인 없는 혼들. 서로 "어이"라고만 부른다) ─────
 {'id': 'N-901', 'name': '장터 끝 혼들', 'region': 9, 'zone': 'SeallessMarket', 'link_soul': None,
  'role': '도장 없는 장터 끝 바위 둘레에 모여 앉은 인 없는 혼들. B-17 이야기는 단서(B17-D1) 대사로만',
  'barks': {'언제나': ['어이, 거기.', '오늘도 안 오네.', '앉아, 앉아.']},
  'schedule': [
   {'time': '언제나', 'place': '장터 끝 바위', 'verb': '엿듣기', 'clue': 'B17-D1', 'note': 'NinthGate에 처음 들어간 다음 밤부터(⑨는 새벽이 없다)'}]},
 {'id': 'N-902', 'name': '장터 한가운데 혼들', 'region': 9, 'zone': 'SeallessMarket', 'link_soul': None,
  'role': '이름을 쓰지 않고 사고파는 혼들. 외상도 계약도 없다. B-18 이야기는 단서(B18-D1) 대사로만',
  'barks': {'언제나': ['어이, 이거 얼마요.', '그냥 가져가.', '어이! 거스름!']},
  'schedule': [
   {'time': '언제나', 'place': '장터 한가운데', 'verb': '엿듣기', 'clue': 'B18-D1', 'note': 'SealCave에 처음 들어간 다음 밤부터'}]},
 {'id': 'N-903', 'name': '빈 고을 이웃들', 'region': 9, 'zone': 'BlankTown', 'link_soul': None,
  'role': '문패 없는 집들의 이웃. 솔고개 사람들과 똑같이 산다 — 이름만 없다. ⑨가 "인을 잃은 모든 고을이 겹친 곳"임을 보여 주는 배경',
  'barks': {'언제나': ['어이, 밥 먹었소?', '오늘은 누가 오려나.', '불 좀 빌려 줘.']},
  'schedule': [{'time': '언제나', 'place': '빈 고을 고샅', 'verb': None, 'clue': None}]},
 # ───── ⑩ 열째 관할 (옛 차사들. 새벽 틈이 돌아온다) ─────
 {'id': 'N-1001', 'name': '사슬 무덤의 옛 차사들', 'region': 10, 'zone': 'ChainGraves', 'link_soul': None,
  'role': '이름을 끝내 못 찾고 흩어진 차사들의 그림자. 제 사슬 곁에 선다. B-19 이야기는 단서(B19-D1) 대사로만. B-20 강제 개방 전날 저녁 예고 한 줄',
  'barks': {'밤': ['오늘도 몇이 깨졌나.', '바닥이 또 높아졌어.'], '새벽 틈': ['빛 든다.'], '저녁': ['갓 바로 써.']},
  'special': None,   # 아래에서 season2_outline B-20 force_hint를 베껴 붙인다
  'schedule': [
   {'time': '밤', 'place': '사슬 무덤', 'verb': None, 'clue': None},
   {'time': '새벽 틈', 'place': '사슬 무덤', 'verb': '엿듣기', 'clue': 'B19-D1', 'note': 'WellYard에 밤에 처음 들어간 다음 새벽 틈부터'},
   {'time': '낮', 'place': '사슬 무덤', 'verb': None, 'clue': None},
   {'time': '저녁', 'place': '사슬 무덤', 'verb': None, 'clue': None}]},
 {'id': 'N-1002', 'name': '처음 마을 사람들', 'region': 10, 'zone': 'FirstVillage', 'link_soul': None,
  'role': '아주 오래된 마을의 혼들. 늘 같은 새벽빛 속에서 하루를 되풀이한다. 그 새벽 일은 말하지 않는다(우물가 노파·누이 등 이름 있는 혼의 기억 몫)',
  'barks': {'새벽 틈': ['또 이 새벽이네.', '닭이 안 우는구먼.'], '낮': ['짚 좀 걷어.'], '저녁': ['해가 안 지네.']},
  'schedule': [
   {'time': '새벽 틈', 'place': '처음 마을 고샅', 'verb': None, 'clue': None},
   {'time': '낮', 'place': '처음 마을 고샅', 'verb': None, 'clue': None},
   {'time': '저녁', 'place': '처음 마을 고샅', 'verb': None, 'clue': None}]},
]

fh = S2['boss_clues']['B-20']['force_hint']
assert fh['npc'] == 'N-1001'
for p in NPCS:
    p['unlock'] = {9: '⑨ 금줄이 풀린 뒤(4막 끝 C-16 / ⑧ 첫 진입 뒤 7번째 새벽)',
                   10: '⑩ 금줄이 풀린 뒤(B-18 처결 / ⑨ 첫 진입 뒤 7번째 새벽)'}[p['region']]
    if p['id'] == 'N-1001':
        p['special'] = {'B20_force_hint': fh['line'], 'when': fh['when'], 'note': 'season2_outline B-20 force_hint. 보스 대사 수에 세지 않는 혼잣말'}
    p['clue_lines'] = []
    for e in p['schedule']:
        if e.get('clue'):
            c = CLUES[e['clue']]
            assert c.get('npc') == p['id'], (e['clue'], c.get('npc'))
            e['line'], e['line_half'] = c['line'], c['line_half']
            p['clue_lines'].append({'clue': c['id'], 'verb': c['verb'], 'place': c['place'], 'line': c['line'], 'line_half': c['line_half']})
    for xs in p['barks'].values():
        for x in xs:
            assert not any(w in x for w in BANNED_IN_BARKS), (p['id'], x)
            assert len(x) <= 14, (p['id'], x)
Z5 = ('BlankTown', 'NinthGate', 'SeallessMarket', 'SealCave', 'FirstVillage', 'ChainGraves', 'WellYard', 'BigDam')
for c in CLUES.values():
    if c['verb'] == '엿듣기' and c['zone'] in Z5:
        assert any(cl['clue'] == c['id'] for p in NPCS for cl in p['clue_lines']), c['id']

out = {
    '_설명': '5막(⑨ 빈 관할 · ⑩ 열째 관할)의 말하는 이 초안. tools/npc_act5.py로 생성. 손으로 고치지 말 것. 좌표는 기획 ⑨⑩ 지도가 나오면',
    '_version': '2026-10-25 초안',
    'zones': {**S2['world']['regions']['9']['zones'], **S2['world']['regions']['10']['zones']},
    'rules': {
        'no_living': '⑨⑩엔 산 사람이 없다. 말하는 이는 배경 무리(처결 대상 아님, 사슬이 닿지 않는다)',
        'speaker': '저희끼리 하는 말. 차사에게 하지 않는다. ⑨에선 서로 "어이"라고만 부른다(이름 금지가 곧 땅의 상처)',
        'region9_time': '⑨는 새벽 틈이 없어 시간표가 "언제나" 한 칸. 빛은 rules.region9_light(season2_outline)',
        'dawn_gap': '⑩은 새벽 틈이 돌아온다(새벽 2분 + 낮 처음 6분 = 8분, ⑦과 같음)',
        'barks': '시간대마다 0~3줄, 12자 안팎. 단서 아님, 기록 안 함. 보스 단서·F 단서·추위 말·이름 금지',
        'karma_seen': '업 10 반쪽 / 30 보스 엿듣기 닫힘 + 가까운 무리가 말을 멈춤 / 60 전원이 말을 멈춤',
        'line_count': '혼잣말·단서 대사·예고 한 줄은 대사 15줄 상한·보스 말풍선 어느 쪽에도 세지 않는다',
    },
    'npcs': NPCS,
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(NPCS), 'speakers,', sum(len(p['clue_lines']) for p in NPCS), 'clue lines')
