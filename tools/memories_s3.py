# -*- coding: utf-8 -*-
# 시즌 3 "백의 밤"(6~8막, ①~⑩ 아래층) 백(魄) 기억 데이터 생성기 — memories_act4·5.py와 같은 틀.
# 왜 따로 만드나: soul_memories.json(원본)은 시즌 1~3 전체라 크고, 백 120명이 시즌 1·2의 누구와 짝인지
#   (그 혼을 천도했나 파혼했나에 따라 손이 빨라지거나 · 비켜서거나 · 주인 없는 백이 되는지)를 코드가 바로 읽을 표가 없다.
# 원본이 바뀌면 이 스크립트를 다시 돌린다(손으로 고치지 않는다 — 원본이 하나여야 어긋나지 않는다).
# 규칙 근거: season3_outline.json(world · rules), SCENARIO-ACT6~8. 밤 번호는 쓰지 않는다(월드 시계).
# 실행: python3 tools/memories_s3.py → docs/narrative/memories_s3.json
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.join(HERE, '..', 'docs', 'narrative')
SM = json.load(open(os.path.join(ND, 'soul_memories.json'), encoding='utf-8'))
S3 = json.load(open(os.path.join(ND, 'season3_outline.json'), encoding='utf-8'))
OUT = os.path.join(ND, 'memories_s3.json')
ALL = {s['id']: s for s in SM['souls']}
for f in ('memories_act4.json', 'memories_act5.json'):
    for s in json.load(open(os.path.join(ND, f), encoding='utf-8'))['souls']:
        ALL.setdefault(s['id'], s)

ACT = {1: 6, 5: 6, 7: 6, 3: 7, 4: 7, 2: 7, 6: 7, 8: 8, 9: 8, 10: 8}

# 아래층이 언제 열리나(밤 번호 대신, 기획 10-25 S3-Q1: 앞 보스 처결 / 앞 관할 아래층 첫 진입 뒤 7번째 새벽).
# 어느 아래층이든 "밤에만"(저녁 2분 동안 물이 빠지고 밤이 시작되면 열림, 새벽 2분 동안 다시 참).
OPENS = {
    1: '시즌 3 첫 밤부터(C-21 뒤)',
    5: '① 아래 금줄이 풀린 뒤(B-21 처결 / ① 아래 첫 진입 뒤 7번째 새벽)',
    7: '⑤ 아래 금줄이 풀린 뒤(B-22 처결 / ⑤ 아래 첫 진입 뒤 7번째 새벽)',
    3: '7막 첫 밤부터(C-23 → C-24 뒤. B-23은 5일 강제 개방이라 늘 온다)',
    4: '③ 아래 금줄이 풀린 뒤(B-24 처결 / ③ 아래 첫 진입 뒤 7번째 새벽)',
    2: '②·⑥ 금줄이 함께 풀린 뒤(B-25 처결 / ④ 아래 첫 진입 뒤 7번째 새벽)',
    6: '②·⑥ 금줄이 함께 풀린 뒤(B-25 처결 / ④ 아래 첫 진입 뒤 7번째 새벽)',
    8: '8막 첫 밤부터(C-27 → C-28 뒤. B-26·B-27 둘 다 처결 / ②⑥ 아래 중 먼저 들어간 곳 첫 진입 뒤 7번째 새벽)',
    9: '⑧ 아래 금줄이 풀린 뒤(B-28 처결 / ⑧ 아래 첫 진입 뒤 7번째 새벽)',
    10: '⑨ 아래 금줄이 풀린 뒤(B-29 처결 / ⑨ 아래 첫 진입 뒤 7번째 새벽)',
}

# 장례 종류 → 눕힌 이튿날 무엇이 보이나(산 사람이 있는 ①~⑥ 낮 / ⑦~⑩ 새벽 틈).
FUNERAL = {
    'reverse': {6: '이튿날 낮, 거꾸로 장례가 앞으로 다시 재생된다 — 빈 몸 자리에 떠밀려 온 물건을 묻는다(F53)',
                8: '이튿날 새벽 틈, 위층에서 그 일꾼이 일을 놓고 줄에 선다(⑧~⑩은 산 사람이 없어 이름 새기기 대신)'},
    'carve': '이튿날 낮, 산 사람이 그 자리에 이름을 새긴다(비석·목패·팻말). 새길 사람이 없으면(혼도 파혼, 낮 단서도 없음) 차사가 사슬 끝으로 대신 긋는다 — 반쪽(F51)',
    'group': '여럿을 함께 묻는다(한 무덤·한 비석). 무리의 다른 백을 다 눕힌 이튿날 한 번에',
    False: '장례 장면 없음. ⑦ 줄 밑이면 바로 위 줄에서 그 혼의 발목 실이 풀려 말려 올라간다(위아래 짝)',
    True: '이미 장례를 받았다(누운 백) — 상호작용 없이 기억만 읽힌다',
}

# 특별한 백. 왜 따로 적나: 보스·결말에 걸려 있어 코드가 이름으로 찾아야 한다.
SPECIAL = {
    'S-184': '열한 몸(둑 밑) — 월화(B-02) 천도면 이마에 이름 또렷 · 낮 단서 없이 바로 눕힘 / 파혼이면 캐스팅 +0.5초',
    'S-185': '열한 몸 맨 끝 — "오른팔이 비어 있었다". 열두째 빈자리 옆(F52 → F72). 8막 전엔 설명하지 않는다',
    'S-186': '열한 몸(둑 밑)',
    'S-188': '개똥이 — 눕히면 B-31 2단계가 짧게 끝난다(이미 건너간 아이, F71)',
    'S-192': '물속 꺼지지 않는 불을 본 백(F56) — 7막 엔딩에서 당할미가 같은 불빛을 본다',
    'S-191': '소 밑의 무명 백 — 이름을 아는 사람이 없다. 눕히면 차사가 대신 부른다(반쪽, F51)',
    'S-200': 'B-22 일곱 가운데 돌석 — 망부석 아낙(B-09) 천도면 이름이 또렷',
    'S-201': 'B-22 일곱 가운데 하나(보스 싸움 안에서 함께 눕는다)',
    'S-202': 'B-22 일곱 가운데 하나(보스 싸움 안에서 함께 눕는다)',
    'S-204': '검은 갓 옛 차사의 백(F63 출처) — 사슬이 손목에서 빠진 차사',
    'S-207': '박돌쇠 옆자리 — "따뜻한 쪽은 다 위로 갔다". 장례를 받은 사람의 백은 여기 없다(F54)',
    'S-209': '목패 "열넷"의 몸 — 눕히면 B25-D4 자동, B-25 눕히기에 아래 물길에서 대답이 온다',
    'S-214': 'B-23 매듭 실 끝(보스 싸움 안에서 풀린다)',
    'S-215': 'B-23 매듭 실 끝(보스 싸움 안에서 풀린다)',
    'S-216': 'B-23 매듭 실 끝(보스 싸움 안에서 풀린다)',
    'S-223': '기수 대돌(B-05)의 동생 — 형의 손을 쥐고 있다. B-24에서 대돌과 함께',
    'S-229': 'B-25 막장 안 광부(보스 싸움 안에서 함께)',
    'S-230': 'B-25 막장 안 광부(보스 싸움 안에서 함께)',
    'S-231': '갱도 목수 — 시즌 1 S-073 천도면 B-25 버팀목 하나가 처음부터 단단',
    'S-259': '이미 누운 백(차사가 된 거지) — spawn laid. 무덤 위 녹슨 사슬, 손목에 사슬 없음(F63)',
    'S-261': '옛 서리 — 서생 곁에 누웠다(F62 출처). B-27 무대 가장자리',
    'S-262': '왕초 — 까치(S-263)를 업은 채. 둘을 함께 눕힌다(따로 하면 캐스팅이 끊긴다). 시즌 1 B-11 천도면 별명으로',
    'S-263': '까치 — 왕초(S-262)와 함께만',
    'S-264': '둑에서 건져진 사내 — B-31 3단계 일곱의 빛 가운데 반드시 하나(F64)',
    'S-272': '벼루지기의 옛 짝 — 눕히면 B-28 시 두 줄 모두(F67), B28-D4 자동',
    'S-278': 'B29-D2를 말하는 아이(S-148)의 몸',
    'S-280': '백한 켤레째 짚신(B29-D3)',
    'S-287': '인을 훔친 혼(B-18)의 몸 — 시즌 2 B-18 천도면 비켜선다',
    'S-275': '숫자를 처음 쓴 서리(B-15)의 몸 — 시즌 2 B-15 천도면 비켜선다',
    'S-296': '솔고개 첫 차사(S-045)의 몸 — 새끼줄 시절 차사',
    'S-299': '노를 깎던 목수 — 사공의 노(그 사람 정체는 말하지 않는다)',
    'S-300': '사공에게 노를 건넨 혼 — 물이 솔고개 쪽으로 흐른다(F70)',
}

# 관할마다 덧붙는 규칙(season3_outline world.regions.special을 혼 단위로 내린 것)
REGION_RULE = {
    5: '물때: 밀물 신호 뒤 20초 안에 못 눕히면 모래에 다시 묻혀 그 밤엔 사라진다(다음 썰물 밤에 다시)',
    4: '목패 번호: 이름을 모르면 번호로 눕힐 수 있다(캐스팅 +0.5초, 목패에 번호). 시즌 1 B-08 천도면 이름으로',
    6: '별명도 이름이다: 시즌 1 B-11 천도면 무적 백을 별명으로 눕힌다(팻말에 별명)',
    3: '덩어리 백: 아는 이름을 부르면 한 몸씩 떨어져 무릎 꿇는다(동시 표시 12몸)',
    2: '두 겹: 위 겹 이름은 약장 감초 밑(B26-D3), 아래 겹 이름은 서생의 명단(B-27)',
    9: '할머니 차례가 먼저: B-29를 눕히면 ⑨ 남은 백 캐스팅 −0.5초',
    10: '사슬 무덤: 차사의 백을 눕히면 위의 사슬이 빠져 쓰러진다(무덤이 끝남)',
}

def link_rules(link, act):
    """시즌 1·2 짝(link)이 있을 때 천도/파혼에 따라 이 백이 어떻게 달라지나."""
    if not link: return None
    if link == 'player': return None
    src = ALL.get(link)
    season = 2 if (src and (src.get('region') or 0) >= 7) else 1
    on_tendo = '캐스팅 −0.5초(이름을 이미 안다, 하한 0.5초)' if act == 6 else '스스로 일어나 비켜선다 — 전투 없이 바로 눕힘, 자리는 아래층 지름길(F58)'
    zone = (src or {}).get('zone')
    on_pahon = '주인 없는 백 — 이름 실이 끊겨 있다. 거꾸로 장례 단서 1개를 먼저 찾아야 눕힌다' + (f'(그 사람이 살던 {zone} 위층 낮)' if zone and act < 8 else '(위층 새벽 틈, 거꾸로 명부)') + '. 깨뜨리기는 언제나'
    return {'season': season, 'name': (src or {}).get('name'), 'on_tendo': on_tendo, 'on_pahon': on_pahon}

rows = []
for s in SM['souls']:
    if not (s['id'].startswith('S-') and s.get('type') == 'baek'): continue
    r, act = s['region'], ACT[s['region']]
    fk = s.get('funeral')
    fun = FUNERAL[fk]
    if isinstance(fun, dict): fun = fun[6 if act < 8 else 8]
    if fk == 'reverse' and act == 7: fun = FUNERAL['carve']   # 7막 땅 밑은 이름 새기기가 기본(ACT7 §7)
    row = {'id': s['id'], 'name': s['name'], 'act': act, 'region': r, 'zone': s['zone'], 'opens': OPENS[r],
           'spawn': s.get('spawn', 'fixed'), 'memory_id': s.get('memory_id'), 'memory': s['memory'],
           'tint': s.get('tint'), 'fact': s.get('fact'), 'weight': s.get('weight'),
           'funeral': fk, 'funeral_scene': fun, 'link': s.get('link')}
    lr = link_rules(s.get('link'), act)
    if lr: row['link_rule'] = lr
    if r in REGION_RULE: row['region_rule'] = REGION_RULE[r]
    if s['id'] in SPECIAL: row['special'] = SPECIAL[s['id']]
    rows.append(row)

# ───── 자체 검사 ─────
assert len(rows) == 120, len(rows)
for k in SPECIAL: assert any(r['id'] == k for r in rows), k
bad = re.compile(r'춥|추워|추위|한기|으슬|차누|초혼')
for r in rows:
    for v in (r['memory'], r.get('special', ''), r['funeral_scene']):
        assert not bad.search(v), (r['id'], v)
    assert re.search(r'(?<!한 )동이(?! 트| 튼)', r['memory']) is None, r['id']

out = {
 '_설명': '시즌 3 "백의 밤" 백 120의 기억 · 짝 · 장례 데이터. tools/memories_s3.py로 생성. 손으로 고치지 말 것(원본 soul_memories.json)',
 '_version': '2026-10-25 초안',
 'rules': {
  'memory': '백의 기억은 생각이 아니라 몸의 감각 한 줄. 말하지 않는다',
  'opens': '아래층은 밤에만(저녁 2분 동안 물이 빠지고 밤이 시작되면 열림, 새벽 30초 전 경고, 새벽 2분 동안 참). 새벽에 남아 있으면 계단 위로 떠밀려 올라온다(벌 없음, 기획 10-25)',
  'lay': S3['world']['lay_down'],
  'break': S3['world']['break'],
  'link': '6막: 짝 혼을 천도했으면 캐스팅 −0.5초 / 7·8막: 비켜선다. 짝 혼을 파혼했으면 주인 없는 백(link_rule)',
  'no_link': '짝이 없는 백(시즌 3에서 처음 만나는 사람)은 보통 눕히기. 이름은 거꾸로 장례 · 명부에서 얻는다',
  'far_light': '눕힐 때마다 그 혼이 ⑦에서 배를 탈 수 있게 되고, 배가 닿을 때마다 서낭당의 저편 불빛이 하나 는다',
  'count': '눕히기는 "보낸 혼 수"(B-23 조건 · B-31 일곱의 빛 · 업 감쇠(천도와 똑같이, 기획 Y2))에 더한다. 깨뜨리기는 업 +1(이름 백)',
 },
 'opens': {str(k): v for k, v in OPENS.items()},
 'baek': rows,
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
from collections import Counter
print(len(rows), 'baek,', sum(1 for r in rows if 'link_rule' in r), 'linked,', dict(Counter(r['act'] for r in rows)))
