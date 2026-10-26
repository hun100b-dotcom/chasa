# -*- coding: utf-8 -*-
# 4막(⑦ 삼도천 기슭 · ⑧ 명부전 담장 밖) '말하는 이' 초안 생성기 — npc_act1~3.py와 같은 모양.
# 왜 '산 사람'이 아니라 '말하는 이'인가: ⑦~⑩엔 산 사람이 없다(시즌 2 규칙). 대신 이미 천도되어 배를 기다리는
#   '줄 선 혼'들이 말한다. 이들은 처결 대상이 아니다(때리면 돌아선 혼이 된다 — B-13 전투 규칙과 같음).
#   모두 차사에게 직접 말하지 않는다. 들으라는 듯 저희끼리 떠들 뿐이다(SCENARIO-ACT4 §0).
# 시간표 칸: 시즌 1의 '낮'은 ⑦에서 '새벽 틈'(동트기 직전 새벽)이다. 보스 단서는 새벽 틈에만 들린다.
# 좌표(x, y): 기획 r7_map.json·r8_r10_map.json(10-25)의 places에서 장소 이름으로 읽어 붙인다(저승은 이승과 좌표 원점이 따로).
# ⑧의 말하는 이는 저승 서리·일꾼이다. 그들은 차사를 본다. 아무도 말을 걸지 않는다(F34). 업 높은 차사가 지나가면 말을 멈춘다.
# 실행: python3 tools/npc_act4.py → docs/narrative/npc_act4.json
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.join(HERE, '..', 'docs', 'narrative')
OUT = os.path.join(ND, 'npc_act4.json')
S2 = json.load(open(os.path.join(ND, 'season2_outline.json'), encoding='utf-8'))
MEMS = {r['id']: r for r in json.load(open(os.path.join(ND, 'memories_act4.json'), encoding='utf-8'))['souls']}
CLUES = {c['id']: c for b in S2['boss_clues'].values() for c in b['clues']}
MAP7 = '/mnt/project-files/planning/openworld/act4/r7_map.json'
# 왜 공유 폴더에서 읽나: 지도는 기획 몫이고 원본이 거기 하나다. 없으면(다른 기계) 좌표 없이 만든다.
MAP810 = '/mnt/project-files/planning/openworld/act4/r8_r10_map.json'
PLACES = {}   # {관할 번호: {장소 이름: {x, y}}}
if os.path.exists(MAP7): PLACES[7] = json.load(open(MAP7, encoding='utf-8'))['places']
if os.path.exists(MAP810):
    for k, v in json.load(open(MAP810, encoding='utf-8'))['regions'].items(): PLACES[int(k)] = v['places']

# barks(혼잣말) 규칙 — 1~3막과 같음:
#  - 시간대마다 0~3줄, 12자 안팎. 단서가 아니다(기록 안 함).
#  - 보스 단서와 겹치는 말 금지: 먼저 가시오·칼금·엽전·노잣돈(B-13) / 둑·쪽지(B-14).
#  - 추위 말 금지(당할미만 느낀다). 이름 금지(역할로 부른다). 사공의 정체·어미 이름은 시즌 4 고리라 말하지 않는다.
BANNED_IN_BARKS = ('먼저 가시오', '칼금', '엽전', '노잣돈', '둑', '쪽지',          # B-13·B-14
                   '상소', '숫자', '도장', '벼루', '울', '먹 냄새', '인',              # B-15·B-16·F35~F38
                   '춥', '추워', '한기', '차누', '으슬')

NPCS = [
 {'id': 'N-701', 'name': '줄 선 혼들(줄 가운데)', 'region': 7, 'zone': 'Ferrytown', 'link_soul': None,
  'role': '이승에서 천도되어 나루까지 왔지만 배를 기다리는 혼들. 처결 대상 아님(장애물). B-13 노인 이야기는 단서(B13-D1) 대사로만',
  'special': {'gate_hint': '윗길 서리들이 내일은 문 연대.', 'when': '⑧ 금줄(명부전 길)이 강제로 풀리기 전날 저녁 한 번', 'note': '기획 gates_rule 예고 한 줄. 대사 수에 세지 않는 혼잣말'},
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
  'appears': {'need': 'B-13 천도', 'variant': {'B-12 천도(시즌 1)': '흑월', '그 밖': '이름 없는 차사 혼'},
              'if_pahon': 'B-13을 파혼했으면 두 번째 배는 4막 끝(C-16 먹지기의 빈 책상) 뒤에야 생긴다 — 사공 없는 빈 배, 노에 먹이 묻어 있다(먹지기가 띄웠다). 진행은 막지 않고 늦출 뿐',
              'why': '배가 두 척이 되는 것은 노인이 처음으로 배에 오른 결과다(B-13 천도). 파혼하면 줄 맨 앞이 빈 채로 남으니, 배를 늘린 손은 노인이 아니라 먹지기여야 맞다'},
  'boat': '⑦~⑩ 나루를 잇는 탈것(귀환 단축). 밤·새벽 틈에 나루 말뚝 앞에서 4분마다 떠난다(기획 r7_map boat)',
  'schedule': [
   {'time': '밤', 'place': '강 위', 'verb': None, 'clue': None, 'note': '⑦~⑩ 귀환 단축(배 두 척)'},
   {'time': '새벽 틈', 'place': '나루 말뚝 앞', 'verb': None, 'clue': None}]},

 # ───── ⑧ 명부전 담장 밖 (서리·일꾼. 바쁜 사무실) ─────
 {'id': 'N-801', 'name': '출근하는 서리들', 'region': 8, 'zone': 'ClerkQuarters', 'link_soul': None,
  'role': '숙사 행랑에서 관아로 출근하는 서리들. 차사를 보지만 말을 걸지 않는다. B-15 이야기는 단서(B15-D1) 대사로만',
  'special': {'gate_hint': '아홉째 칸 뒤 먼지가 내일은 털리겠군.', 'when': '⑨ 금줄(아홉째 칸 뒤 문)이 강제로 풀리기 전날 저녁 한 번', 'note': '기획 gates_rule 예고 한 줄'},
  'barks': {'새벽 틈': ['늦겠네, 서둘러.', '갓끈 똑바로 매.'], '낮': ['오늘 몇 권이오?', '붓 마를 새가 없네.'], '저녁': ['빨래 걷어.', '국 식는다.']},
  'schedule': [
   {'time': '밤', 'place': '숙사 행랑', 'verb': None, 'clue': None, 'note': '등불 아래 밀린 글씨를 쓴다'},
   {'time': '새벽 틈', 'place': '숙사 행랑(출근길)', 'verb': '엿듣기', 'clue': 'B15-D1', 'note': 'Archive에 밤에 처음 들어간 다음 새벽 틈부터'},
   {'time': '낮', 'place': '관아 마당', 'verb': None, 'clue': None},
   {'time': '저녁', 'place': '숙사 부엌', 'verb': None, 'clue': None}]},
 {'id': 'N-802', 'name': '먹방 일꾼들', 'region': 8, 'zone': 'InkRoom', 'link_soul': None,
  'role': '벼루 곁에서 먹을 나르고 이름표를 붙이는 일꾼들. B-16 이야기는 단서(B16-D1) 대사로만. 먹 냄새 이야기는 S-129 기억 몫이라 하지 않는다',
  'barks': {'밤': ['물 더 길어 와.', '덩이 식혀.'], '새벽 틈': ['문 열어라.'], '낮': ['허리 펴고 해.', '이건 어디 놔?']},
  'schedule': [
   {'time': '밤', 'place': '먹방 안', 'verb': None, 'clue': None},
   {'time': '새벽 틈', 'place': '먹방 문간', 'verb': '엿듣기', 'clue': 'B16-D1', 'note': 'InkRoom에 밤에 처음 들어간 다음 새벽 틈부터'},
   {'time': '낮', 'place': '먹방 안', 'verb': None, 'clue': None},
   {'time': '저녁', 'place': '먹방 뒷마당', 'verb': None, 'clue': None}]},
 {'id': 'N-803', 'name': '마당 책상 서리', 'region': 8, 'zone': 'NumberYard', 'link_soul': None,
  'role': '숫자 마당 한쪽 책상에 앉은 서리. ⑧의 장례 변주 "정서"를 하는 사람 — 천도된 숫자 혼의 이름을 먹으로 다시 적는다. 말하지 않는다. 시즌 1 이승 장례의 상주 자리',
  'barks': {},
  'silent': True,
  'schedule': [
   {'time': '밤', 'place': '마당 책상', 'verb': None, 'clue': None, 'note': '번호를 부르며 명부를 맞춘다(소리 없이 입만)'},
   {'time': '새벽 틈', 'place': '마당 책상', 'verb': None, 'clue': None, 'note': '정서 장면(그 밤 천도한 숫자 혼 하나)'},
   {'time': '낮', 'place': '마당 책상', 'verb': None, 'clue': None},
   {'time': '저녁', 'place': '마당 책상', 'verb': None, 'clue': None}]},
 {'id': 'N-804', 'name': '숙사 부엌 사람들', 'region': 8, 'zone': 'ClerkQuarters', 'link_soul': None,
  'role': '서리 숙사 부엌에서 밥을 짓는 사람들. 차사 밥은 차리지 않는다(S-139 기억과 맞물림). S-139 정서 뒤엔 밥 한 그릇을 따로 차려 둔다',
  'barks': {'새벽 틈': ['불 지펴.'], '낮': ['솥 닦아 둬.', '쌀 일어라.'], '저녁': ['상 내가.', '서리님들 오신다.']},
  'schedule': [
   {'time': '새벽 틈', 'place': '숙사 부엌', 'verb': None, 'clue': None},
   {'time': '낮', 'place': '숙사 부엌', 'verb': None, 'clue': None},
   {'time': '저녁', 'place': '숙사 부엌', 'verb': None, 'clue': None}]},
]

# 단서 대사 붙이기 — 원본은 season2_outline.json의 단서 표 하나. 여기서 베껴 오기만 한다(어긋나지 않게).
for p in NPCS:
    p['unlock'] = '시즌 2 첫 진입부터(C-14 뒤)' if p['region'] == 7 else '⑧ 금줄(명부전 길)이 풀린 뒤(B-14 처결 / ⑦ 첫 진입 뒤 7번째 새벽)'
    for x in (p.get('special') or {}).get('gate_hint', ''),: assert not any(w in x for w in BANNED_IN_BARKS if w not in ('인',)), x
    for e in p['schedule']:
        pl = PLACES.get(p['region'], {}).get(e['place'])
        if pl: e['x'], e['y'] = pl['x'], pl['y']
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
    if c['verb'] == '엿듣기' and c['zone'] in ('Reeds', 'Ferrytown', 'InkRapids', 'Dam', 'ClerkQuarters', 'InkRoom', 'Archive', 'NumberYard'):
        assert any(cl['clue'] == c['id'] for p in NPCS for cl in p['clue_lines']), c['id']

out = {
    '_설명': '4막(⑦ 삼도천 기슭 · ⑧ 명부전 담장 밖)의 말하는 이 초안. tools/npc_act4.py로 생성. 손으로 고치지 말 것. ⑦ 좌표는 기획 r7_map.json, ⑧ 좌표는 기획 r8_r10_map.json places(맞춤 끝, 서사 10-26)',
    '_version': '2026-10-25 초안',
    'zones': {**S2['world']['regions']['7']['zones'], **S2['world']['regions']['8']['zones']},
    'rules': {
        'no_living': '⑦~⑩엔 산 사람이 없다. ⑦ 말하는 이는 이미 천도되어 배를 기다리는 줄 선 혼들(처결 대상 아님, 때리면 돌아선 혼이 됨). ⑧은 저승 서리·일꾼(처결 대상 아님, 사슬이 닿지 않는다)',
        'worker_vs_soul': '⑧ 이름혼(S-127~144 — 서리·귀졸·부엌 할미 등)은 일을 놓은 뒤 이름이 흐려져 밤에 맺힌 혼이다. 시즌 1 혼과 같은 그림(흐린 몸·맺힘 막대·머리 위 이름)이라 일하는 이(또렷한 몸, 사슬 안 닿음, 겨냥 테 없음)와 한눈에 갈린다. 같은 자리에서 헷갈리지 않게 밤엔 일하는 이가 집 안(행랑·먹방 안)에만 있고, 이름혼은 마당·처마 밑에 선다. 이름혼은 시즌 1처럼 밤에만(NamedSoulSpawns) — 서사 10-26',
        'dawn_gap': '새벽 틈 = 새벽 2분 + 낮 처음 6분 = 8분(기획 r7_map dawn_gap). 보스 단서 대사는 이때만 들린다. 시즌 1의 낮 칸에 해당',
        'day': '저승의 낮은 고요하다. 낮 나머지엔 싸움이 없고, ⑦에선 배웅 찾기·가루 줍기·나룻불 쉼터 정비(기획 r7_map day_in_underworld)',
        'send_off_slot': '⑦ 배는 새벽 틈 시작에 나루 말뚝 앞에 2분 닿는다. 그때 배웅 하나가 열린다: 그 밤 천도한 ⑦ 혼의 배웅(memories_act4 rite)이 먼저, 없으면 낮에 찾아 둔 시즌 1 이름혼의 배웅 대기 하나',
        'season1_send_off': '시즌 1 이름혼 배웅(⑦ 장례 자리): #2 줄 끝에 선 그 혼이 시즌 1에서 들고 있던 것을 그대로 든 채 멈춰 있다 → #6 배에 오르며 나에게 고개를 숙인다 → #7 나룻불 하나가 켜진다. 대사 0줄. 혼마다 따로 쓰지 않는다(시즌 1 장례 데이터의 물건을 그대로 쓴다)',
        'speaker': '모든 말은 저희끼리 하는 말이다. 차사에게 하지 않는다. 들으라는 듯 떠들 뿐',
        'barks': '시간대마다 0~3줄, 12자 안팎. 단서 아님, 기록 안 함. 보스 단서·F 단서·추위 말·이름 금지',
        'karma_seen': '업 10 반쪽 / 30 보스 엿듣기 닫힘 + ⑦ 가까운 줄 선 혼이 등을 돌림, ⑧ 가까운 서리가 말을 멈춤 / 60 ⑦ 줄 전체가 등을 돌리고 ⑧ 서리 전원이 말을 멈춤(혼잣말도)',
        'silent': '사공(N-703·704)과 마당 책상 서리(N-803)는 말하지 않는다. 입 모양·몸짓만. 대사 수에 세지 않는다',
        'line_count': '이 파일의 말은 혼잣말과 단서 대사뿐이라 대사 15줄 상한·보스 말풍선 어느 쪽에도 세지 않는다',
    },
    'npcs': NPCS,
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(NPCS), 'speakers,', sum(len(p['clue_lines']) for p in NPCS), 'clue lines')
