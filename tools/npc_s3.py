# -*- coding: utf-8 -*-
# 시즌 3 "백의 밤" 말하는 이 표 — npc_act4·5.py와 같은 모양.
# 왜 새 사람을 거의 안 만드나: 시즌 3은 같은 고을의 아래층이다. 위층 낮에 말하는 사람은 시즌 1에서 이미 만난 그 사람들
#   (윤 소사네 아들 · 포구 아낙들 · 아들 문지기 …)이어야 "같은 고을의 다른 이야기"가 된다. 그래서 시즌 1 · 2의 N-번호를 다시 쓰고
#   시즌 3에서 해야 할 일(새 단서 대사 · 새 혼잣말)만 덧붙인다. 새 사람은 광부 과부의 딸(N-407) 하나.
# 혼이 말하는 단서(S-148 · S-172)는 rules.soul_speaker: 그 혼을 시즌 2에서 천도했으면 같은 말이 ⑦ 줄에서 들린다.
# 아래층엔 산 사람이 없다 → 말하는 이는 모두 위층(낮 · 새벽 틈). 좌표는 시즌 1 · 2 npc 표의 같은 장소를 쓴다(아래층 지도는 아직 없음).
# 실행: python3 tools/npc_s3.py → docs/narrative/npc_s3.json
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.join(HERE, '..', 'docs', 'narrative')
S3 = json.load(open(os.path.join(ND, 'season3_outline.json'), encoding='utf-8'))
CLUES = {c['id']: c for b in S3['boss_clues'].values() for c in b['clues']}
OLD = {}
for f in ('npc_act1.json', 'npc_act2.json', 'npc_act3.json', 'npc_act4.json', 'npc_act5.json'):
    for p in json.load(open(os.path.join(ND, f), encoding='utf-8'))['npcs']:
        OLD[p['id']] = (f, p)
SOULS = {s['id']: s for f in ('memories_act4.json', 'memories_act5.json')
         for s in json.load(open(os.path.join(ND, f), encoding='utf-8'))['souls']}

# 혼잣말 금지 말: 보스 단서와 겹치는 말(몸 · 꺼내다 · 묻다 · 팻말 · 명단 …은 단서 몫), 추위, 결말 A 전용 말, 이름.
BANNED = ('몸이라도', '꺼내', '팻말', '명단', '소매', '줄을 끊', '사잣밥', '우물', '어머니',
          '춥', '추워', '추위', '한기', '차누', '으슬', '초혼')

# 시즌 3에서 다시 나오는 사람들. barks_s3 = 시즌 3에만 더하는 혼잣말(시간대마다 0~3줄, 14자 이내).
ENTRIES = [
 {'npc': 'N-103', 'region': 1, 'when_s3': '① 아래가 열린 뒤', 'clue': 'B21-D2', 'time': '낮', 'place': '나루(줄배 앞)',
  'barks_s3': {'낮': ['물이 또 빠졌다네.', '배가 바닥에 닿았어.']},
  'after_lay': 'B-21 눕힌 이튿날 낮 — 빈 엽전 끈을 묻는 장례의 상주. 위패 앞에 처음으로 무덤',
  'after_break': '나루에 서서 강만 본다(혼잣말 없음)'},
 {'npc': 'N-501', 'region': 5, 'when_s3': '⑤ 아래가 열린 뒤', 'clue': 'B22-D2', 'time': '낮', 'place': '그물 너는 마당',
  'barks_s3': {'낮': ['썰물이 길어졌어.', '곶 밑 굴이 열렸대.']},
  'after_lay': 'B-22 눕힌 이튿날 낮 — 밧줄 토막을 한 무덤에 묻는 장례에 함께 선다',
  'after_break': '그물만 깁는다'},
 {'npc': 'N-303', 'region': 3, 'when_s3': '③ 아래가 열린 뒤', 'clue': 'B24-D2', 'time': '낮', 'place': '마을 사당 앞',
  'barks_s3': {'낮': ['큰 무덤이 내려앉았어.', '흙이 밤마다 울어.']},
  'after_lay': 'B-24 눕힌 이튿날 낮 — 큰 무덤 앞 비석(앞면 서른일곱, 뒷면 건너편)을 세우는 사람들 맨 앞',
  'after_break': '제사는 여전히 한쪽만'},
 {'npc': 'N-407', 'new': True, 'name': '광부 과부의 딸', 'region': 4, 'zone': 'MinerTown', 'link_soul': 'S-075',
  'role': '광부 과부(S-075)와 막장 안 남편(S-239)의 딸. 시즌 3에서 처음 말한다. 목패 걸이 앞을 지난다',
  'when_s3': '④ 아래가 열린 뒤', 'clue': 'B25-D2', 'time': '낮', 'place': '광부촌 우물가',
  'barks_s3': {'낮': ['갱 물이 빠졌대.', '목패 걸이 녹 좀 봐.']},
  'after_lay': 'B-25 눕힌 이튿날 낮 — 목패 열넷이 걸이에서 떼어질 때 그중 하나(아버지 것)를 받는다',
  'after_break': '빈 고리를 올려다본다'},
 {'npc': 'N-205', 'region': 2, 'when_s3': '② 아래가 열린 뒤', 'clue': 'B26-D2', 'time': '낮', 'place': '동헌 터 앞',
  'barks_s3': {'낮': ['무덤골 흙이 꺼졌어.', '할아버지 붓 어딨지.']},
  'after_lay': 'B-26 눕힌 이튿날 낮 — 다시 나붙은 진짜 명단 앞에서 손가락으로 할아버지 글씨를 짚는다',
  'after_break': '동헌 터에서 혼자 논다'},
 {'npc': 'N-602', 'region': 6, 'when_s3': '⑥ 아래가 열린 뒤', 'clue': 'B27-D2', 'time': '낮', 'place': '성문',
  'barks_s3': {'낮': ['성문 밖 땅이 꺼졌어.', '새 붓 하나 사야겠군.']},
  'after_lay': 'B-27 눕힌 이튿날 낮 — 성문 밖 구덩이 앞에 팻말을 세운다(서적상 노인 가게의 새 붓으로 쓴 두 글자)',
  'after_break': '성문을 제때 닫는다'},
 {'npc': 'N-802', 'region': 8, 'when_s3': '⑧ 아래가 열린 뒤', 'clue': 'B28-D2', 'time': '새벽 틈', 'place': '먹방 문간',
  'barks_s3': {'밤': ['벼루 밑이 울려.'], '새벽 틈': ['오늘 먹은 무겁네.']},
  'after_lay': 'B-28 눕힌 뒤 — 벼루지기가 갈기를 멈추자 일꾼들도 하나둘 손을 놓는다',
  'after_break': '먹을 계속 나른다'},
 {'npc': 'N-701', 'region': 7, 'when_s3': '시즌 3 내내', 'clue': None, 'time': '저녁', 'place': '줄 가운데',
  'barks_s3': {'밤': ['발목이 당겨.', '배가 또 돌아왔네.'], '저녁': ['오늘은 몇이 닿았나.']},
  'special_s3': {'B23_force_hint': S3['boss_clues']['B-23']['force_hint']['line'], 'when': S3['boss_clues']['B-23']['force_hint']['when']},
  'after_lay': 'B-23 풀기 뒤 — 줄이 처음으로 한꺼번에 움직인다. 혼잣말이 "닿았대."로 바뀐다',
  'after_break': '끊긴 실의 혼들이 기슭을 떠돈다'},
 {'npc': 'N-101', 'region': 1, 'when_s3': '시즌 3 내내', 'clue': None, 'time': '저녁', 'place': '서낭당 나무 아래',
  'barks_s3': {},
  'special_s3': {'B31_force_hint': S3['boss_clues']['B-31']['force_hint']['line'], 'when': S3['boss_clues']['B-31']['force_hint']['when']},
  'after_lay': '결말 장면은 endings_s1(정본). 시즌 3 비트는 season3_outline.halmi',
  'after_break': '결말 C — 매일 짚신을 고쳐 놓는다'},
]

SOUL_SPEAKERS = [
 {'soul': 'S-148', 'clue': 'B29-D2', 'where_if_unsent': '⑨ 빈 고을 고샅(새벽 틈)', 'where_if_sent': '⑦ 줄(저녁)', 'if_pahon': '단서 없음(나머지 3개로)'},
 {'soul': 'S-172', 'clue': 'B30-D2', 'where_if_unsent': '⑩ 처음 마을 우물가(새벽 틈)', 'where_if_sent': '⑦ 줄(저녁)', 'if_pahon': '단서 없음(나머지 3개로)'},
]

out_rows = []
for e in ENTRIES:
    if e.get('new'):
        assert e['npc'] not in OLD, e['npc']
        base = {'name': e['name'], 'zone': e['zone'], 'role': e['role'], 'link_soul': e.get('link_soul'), 'source': 'npc_s3(새)'}
    else:
        f, p = OLD[e['npc']]
        base = {'name': p['name'], 'zone': p.get('zone'), 'role': p.get('role'), 'source': f}
    row = {'id': e['npc'], **base, 'region': e['region'], 'when_s3': e['when_s3'], 'barks_s3': e['barks_s3'],
           'after_lay': e['after_lay'], 'after_break': e['after_break']}
    if e.get('special_s3'): row['special_s3'] = e['special_s3']
    sch = {'time': e['time'], 'place': e['place'], 'verb': None, 'clue': None}
    if e['clue']:
        c = CLUES[e['clue']]
        assert c.get('npc') == e['npc'], (e['clue'], c.get('npc'))
        sch.update({'verb': c['verb'], 'clue': c['id'], 'line': c['line'], 'line_half': c['line_half']})
    row['schedule_s3'] = [sch]
    for xs in e['barks_s3'].values():
        for x in xs:
            assert not any(w in x for w in BANNED), (e['npc'], x)
            assert len(x) <= 14, (e['npc'], x)
    out_rows.append(row)

for s in SOUL_SPEAKERS:
    c = CLUES[s['clue']]
    assert c.get('npc') == s['soul'] and s['soul'] in SOULS, s
    s.update({'name': SOULS[s['soul']]['name'], 'line': c['line'], 'line_half': c['line_half']})

# 엿듣기 단서는 모두 말하는 이가 있어야 한다
for c in CLUES.values():
    if c['verb'] == '엿듣기':
        assert any(r['schedule_s3'][0].get('clue') == c['id'] for r in out_rows) or any(s['clue'] == c['id'] for s in SOUL_SPEAKERS), c['id']

out = {
 '_설명': '시즌 3 말하는 이 표. tools/npc_s3.py로 생성. 손으로 고치지 말 것. 시즌 1 · 2의 같은 사람(N-번호)에 시즌 3 몫만 덧붙인다',
 '_version': '2026-10-25 초안',
 'rules': {
  'who': '아래층엔 산 사람이 없다. 말하는 이는 모두 위층 — ①~⑥ 낮(산 사람), ⑦~⑩ 새벽 틈(혼 무리). 차사에게 직접 말하지 않는다',
  'barks': '시즌 3 혼잣말은 시간대마다 0~3줄, 14자 이내. 단서 아님, 기록 안 함. 보스 단서와 겹치는 말 · 추위 말 · 이름 금지. 시즌 1 · 2 혼잣말 위에 더한다',
  'after': 'after_lay / after_break = 그 보스를 눕혔을 때 / 깨뜨렸을 때 이 사람이 하는 일(낮 장례 · 혼잣말 변화)',
  'karma_seen': '업 10 반쪽 / 30 보스 엿듣기 닫힘 + 가까운 사람이 말을 멈춤 / 60 전원이 말을 멈춤(시즌 1 · 2 그대로)',
  'soul_speaker': S3['rules']['soul_speaker'],
  'line_count': '혼잣말 · 단서 대사 · 예고 한 줄은 대사 15줄 상한 · 보스 말풍선 어느 쪽에도 세지 않는다',
 },
 'npcs': out_rows,
 'soul_speakers': SOUL_SPEAKERS,
}
json.dump(out, open(os.path.join(ND, 'npc_s3.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out_rows), 'speakers,', len(SOUL_SPEAKERS), 'soul speakers')
