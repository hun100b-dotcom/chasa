# -*- coding: utf-8 -*-
# 2막 보스 넷(B-05 기수 대돌, B-06 이름 없는 장수, B-07 갱도 반장 칠성, B-08 장부꾼 염씨)의 한(恨) 구조와 단서 사슬.
# 틀은 1막(npc_act1.json의 boss_clues)과 같다: 보스마다 단서 4개 = 낮 3(엿듣기·지켜보기·만져 보기, 동사가 모두 다름) + 밤 대체 1.
#   그중 3개를 모으면 천도할 수 있다(2개 이하면 파혼만).
# 1막보다 더한 것(코디 요청 10-25, "한 구조"):
#   han        = 그 보스가 붙들고 있는 것(한 문장)
#   belief     = 보스가 믿고 있는 틀린 생각(그래서 떠나지 못한다)
#   truth      = 천도 기억이 보여 주는 실제(★ 전모 단서)
#   points_to  = 단서 하나하나가 한의 어느 쪽을 비추는가 — 단서 셋을 모으면 belief가 왜 틀렸는지 플레이어가 먼저 짐작하게 한다
# 좌표·시간표는 2막 지도가 나오면 기획과 맞춘다. 지금 place는 구역 안 자리 이름(제안)이다.
# 실행: python3 tools/boss_clues_act2.py → docs/narrative/boss_clues_act2.json
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'boss_clues_act2.json')
SRC = json.load(open(os.path.join(HERE, '..', 'docs', 'narrative', 'soul_memories.json'), encoding='utf-8'))
MEM = {s['id']: s for s in SRC['souls']}

def C(cid, verb, zone, place, what, points_to, npc=None, line=None, half=None, text=None, soul=None, time='낮', note=None, alt=None):
    """단서 하나. 엿듣기는 line/half(업 10 이상), 만져 보기는 text(물건 위 한 줄), 밤 대체는 soul."""
    c = {'id': cid, 'verb': verb, 'time': time, 'zone': zone, 'place': place, 'npc': npc, 'what': what, 'points_to': points_to}
    if line: c['line'], c['line_half'] = line, half
    if text: c['text'] = text
    if soul:
        c['soul'] = soul
        c['memory'] = MEM[soul]['memory']   # 밤 대체 단서 = 그 혼을 천도할 때 나오는 기억(원본 그대로)
    if alt: c['alt'] = alt
    if note: c['note'] = note
    return {k: v for k, v in c.items() if v is not None}

BOSSES = {
 'B-05': {
  'name': '기수 대돌', 'region': 3, 'zone': 'Fortress', 'arena': '무너진 산성 깃대 터',
  'sentence': '잊혀 가는 서른일곱의 이름',
  'han': '쓰러진 동료 서른일곱의 이름을 혼자 외워 밤마다 불렀다. 하나씩 잊혀 간다. 오늘은 서른하나까지',
  'belief': '내가 잊으면 그 이름은 세상에서 사라진다. 그러니 내가 계속 불러야 한다',
  'truth': '잊은 여섯은 깃대에 새겨 두었고, 마을은 해마다 서른일곱 잔을 부어 왔다. 이름을 붙든 것은 그 혼자가 아니었다(★F22: 이름을 새긴 물건 하나가 혼을 붙잡아 준다)',
  'decisive': 'F22', 'zone_opens': 'Fortress에 밤에 처음 들어간 다음 낮',
  'clues': [
   C('B05-D1', '지켜보기', 'Fortress', '큰 무덤 앞 / 술도가 뒤뜰', '술 서른일곱 잔', '마을도 서른일곱을 세어 왔다(그 혼자 기억한 게 아니다)',
     npc='N-301', note='술도가 노인(S-049)을 천도해 장례를 봤으면 손녀가 큰 무덤 앞에 술을 붓는 모습(서른일곱 잔 + 할아버지 몫 한 잔). 아직이면 술도가 뒤뜰에 엎어 둔 빈 술독 서른일곱을 지켜본다. 어느 쪽이든 같은 단서. 파혼했으면 술독만'),
   C('B05-D2', '엿듣기', 'Fortress', '산성 아랫마을 골목', '아이들의 "깃발 아저씨" 놀이', '아이들 놀이 속에 아직 "부르는 사람"이 살아 있다',
     npc='N-302', line='깃발 아저씨가 부른다! 대답 안 하면 술래다!', half='깃발 아저씨가 부른다…'),
   C('B05-D3', '만져 보기', 'ArrowValley', '화살골 바위틈', '부러진 깃대 조각', '잊은 이름들이 깃대에 남아 있다',
     text='칼금으로 새긴 이름들. 여섯만 또렷하다.', time='언제나(물건은 밤에도 만질 수 있다)'),
   C('B05-D4', '밤 대체', 'Fortress', '산성 위', '산성 지기 천도 기억', '깃발 든 사람이 아직 안 내려왔다',
     soul='S-056', time='밤'),
  ],
  'tendo': '봉분에 이름 서른일곱이 새겨진다. ③ 덩어리 확률 −10%p. 무덤 앞에 마을 사람들이 다시 술을 붓는 낮 풍경',
  'pahon': '찢어진 군기(장비). 업 +3',
  'hidden': 'B-05를 먼저 천도하면 B-06의 단서 하나(B06-D4)가 저절로 채워진다 — 기수는 장수의 이름도 외우고 있었다',
 },
 'B-06': {
  'name': '이름 없는 장수', 'region': 3, 'zone': 'Camp', 'arena': '군막 터',
  'sentence': '번호로 불러 이긴 싸움에 살아남은 번호가 없다',
  'han': '부하들을 번호로 불러 진을 짰다. 이름을 부르면 다들 고향 얼굴이 되어 앞을 못 봤기 때문이다. 살아남은 번호가 하나도 없다',
  'belief': '번호로 부른 것이 옳았다. 이름을 불렀다면 더 빨리 무너졌을 것이다',
  'truth': '번호로 불린 이들은 죽어서도 명부에 들리지 않는다. 그는 이기려고 부하들의 이름을 지웠고, 그 이름들이 지금 그를 떠나지 못하게 한다(★F17)',
  'decisive': 'F17', 'zone_opens': 'Camp에 밤에 처음 들어간 다음 낮',
  'clues': [
   C('B06-D1', '지켜보기', 'Fortress', '마을 사당', '위패 "장군지위" — 이름이 없다', '마을은 그를 기리지만 이름을 모른다(그 자신도 이름 없이 남았다)',
     npc='N-303', note='사당 노인이 위패 앞을 쓴다. 위패 글자는 그대로 보여도 된다(전승 표기, 이름이 없다는 것이 단서)'),
   C('B06-D2', '엿듣기', 'Fortress', '마을 사당 앞', '노인의 말', '번호는 부하들에게 자랑이었다 — 그가 지운 것이 무엇이었는지',
     npc='N-303', line='장군은 우리 아버지를 일곱이라고 불렀지. 아버지는 그게 자랑이었대.', half='장군은 우리 아버지를…'),
   C('B06-D3', '만져 보기', 'Camp', '군막 터 기둥 자리', '찢어진 진법도', '진법도에는 숫자뿐이다',
     text='동그라미마다 숫자뿐이다. 이름은 하나도 없다.', time='언제나(물건은 밤에도 만질 수 있다)'),
   C('B06-D4', '밤 대체', 'ArrowValley', '화살골', '병사 일곱 천도 기억', '번호로 불린 이가 그 번호를 붙들고 있다',
     soul='S-059', time='밤', alt='또는 B-05 기수 대돌을 먼저 천도하면 저절로 채워진다'),
  ],
  'tendo': '산성 쉼터(③의 동트기 안전 지점)',
  'pahon': '장수의 갑주(방어 장비). 업 +3',
  'hidden': None,
 },
 'B-07': {
  'name': '갱도 반장 칠성', 'region': 4, 'zone': 'Collapse', 'arena': '무너진 막장',
  'sentence': '세어도 세어도 하나가 모자란다',
  'han': '무너지는 갱도에서 번호를 불러 한 명씩 내보냈다. 열셋까지. 하나가 모자란다 — 몇 번을 세도',
  'belief': '아직 안에 한 사람이 남았다. 그 사람을 내보내기 전에는 나갈 수 없다',
  'truth': '모자란 하나는 자기 자신이다. 자기 번호(칠)를 세지 않았다. 천도 캐스팅 중 마지막으로 센다: "…열셋. 그리고 — 칠성."(★F18)',
  'decisive': 'F18', 'zone_opens': 'Collapse에 밤에 처음 들어간 다음 낮',
  'clues': [
   C('B07-D1', '지켜보기', 'MinerTown', '목패 걸이 판', '돌아오지 않은 목패 열넷 중 "七"', '돌아오지 않은 목패 가운데 반장의 것이 있다',
     npc='N-404', note='교대 광부들이 아침에 목패를 건다. 오래 걸려 있는 목패 열넷이 그대로다. 그중 七자 목패만 테두리가 닳았다(반장이 늘 만지던 것)'),
   C('B07-D2', '엿듣기', 'Sorting', '선탄장 평상', '선탄장 아낙들의 말', '반장은 언제나 맨 마지막에 나왔다',
     npc='N-401', line='반장님은 맨 마지막에 나온다고 늘 그랬지.', half='반장님은 맨 마지막에…'),
   C('B07-D3', '만져 보기', 'Collapse', '막장 입구 바위', '분필 글씨 "13 나감"', '나간 사람은 열셋에서 끝났다',
     text='바위에 분필 글씨. 13 나감.', time='언제나(물건은 밤에도 만질 수 있다)', note='분필 글씨는 소품이라 숫자를 보여도 된다(단서 그 자체)'),
   C('B07-D4', '밤 대체', 'Collapse', '막장 안쪽', '막장의 광부 천도 기억', '반장은 자기 번호를 안 불렀다',
     soul='S-079', time='밤'),
  ],
  'tendo': '갱도 지름길(④ → ⑤ 갯마을 가는 길)',
  'pahon': '광석 대량(제작 재료). 업 +3',
  'hidden': '이 보스전에서는 광부 혼을 파혼하면 반장의 셈이 틀려 맺힘이 회복된다 — 1막과 반대의 압박(전투 규칙, 기획 부록 E)',
 },
 'B-08': {
  'name': '장부꾼 염씨', 'region': 4, 'zone': 'MinerTown', 'arena': '광산 주인집(광부촌 위)',
  'sentence': '아무도 넘기지 않은 뒷장',
  'han': '주인의 명으로 죽음을 장부에 "손실 열넷"이라 적었다. 밤마다 뒷장에 열네 사람의 이름을 몰래 적었다. 아무도 뒷장을 보지 않았다',
  'belief': '뒷장에 적어 두었으니 이름은 남는다. 누군가는 언젠가 뒷장을 넘길 것이다',
  'truth': '누군가 앞장(숫자)만 베껴 갔다 — 위로, 저승 관아로. 저승의 숫자 명부는 이승 장부를 베낀 것이다(★F20)',
  'decisive': 'F20', 'zone_opens': 'MinerTown에 밤에 처음 들어간 다음 낮',
  'clues': [
   C('B08-D1', '지켜보기', 'MinerTown', '주인집 마루', '광산 주인이 장부 앞장만 넘긴다', '아무도 뒷장을 보지 않는다',
     npc='N-406'),
   C('B08-D2', '엿듣기', 'MinerTown', '광부촌 우물가', '광부 과부의 말', '죽음이 머릿수로 셈해졌다',
     npc='N-403', line='보상은 머릿수로 줬지. 우리 그이는 한 머리였어.', half='보상은 머릿수로…'),
   C('B08-D3', '만져 보기', 'MinerTown', '주인집 장부함', '장부 뒷장 귀가 접혀 있다', '뒷장에 무언가 있다 — 펼쳐 본 사람이 없다',
     text='뒷장 귀가 접혀 있다. 한 번도 펴지 않은 자국이다.', time='낮(주인집은 밤에 닫힌다)'),
   C('B08-D4', '밤 대체', 'MinerTown', '주인집 부엌', '주인집 하녀 천도 기억', '뒷장은 귀가 접힌 채 그대로였다',
     soul='S-074', time='밤'),
  ],
  'tendo': '④ 이름혼 전원 인 "없음 → 흐림"(천도 캐스팅 가산 +0.5 → +0.25초). 숫자 혼이 이름을 되찾아 천도 가능, 짧은 기억 대신 긴 기억',
  'pahon': '장부의 금(엽전 ×80). 업 +3. ④ 이름혼은 끝까지 "인 없음"',
  'hidden': '천도 기억의 "위로"는 저승 관아를 가리킨다. 먹지기 쪽지 "위에서 숫자로 적으라는 영이 왔다. 나는 안 한다."와 같은 무렵에 나오게 한다',
 },
}

# 기획 2막 지도(act2_map.json)의 좌표와 구역을 붙인다(10-25). 자리 이름은 서사가 정했고 지도가 그 이름을 그대로 썼다.
# 왜 지도에서 읽나: 좌표는 아트가 지형을 깔며 옮길 수 있어서, 숫자를 여기 따로 적어 두면 어긋난다.
MAP = '/mnt/project-files/planning/openworld/act2/act2_map.json'
if os.path.exists(MAP):
    amap = json.load(open(MAP, encoding='utf-8'))
    xy = {c['id']: c['xy'] for c in amap['boss_clues']}
    places = amap['places']
    for b in BOSSES.values():
        for c in b['clues']:
            if c['id'] in xy:
                c['xy'] = [{'place': q['place'], 'x': q['x'], 'y': q['y']} for q in xy[c['id']]]
                z = places.get(xy[c['id']][0]['place'], {}).get('zone')
                if z: c['zone'] = z   # 지도 구역 이름을 따른다(예: 아랫마을은 FortressVillage)
    MAP_NOTE = '좌표 xy는 기획 act2_map.json(x=동, y=북, m)에서 붙임. 아트가 옮기면 그 파일이 우선'
else:
    MAP_NOTE = '지도 없음(좌표 미정)'

data = {
 '_설명': '2막 보스 한(恨) 구조와 단서 사슬. tools/boss_clues_act2.py로 생성. 서사 2026-10-25. 1막 보스 단서(npc_act1.json의 boss_clues)와 같은 틀에 han·belief·truth·points_to를 더했다',
 'rules': {
  'boss_clue': '보스마다 단서 4개(낮 3 + 밤 대체 1). 3개 이상이면 천도, 2개 이하면 파혼만. 낮 단서 셋은 동사가 모두 다르다',
  'karma': '업 10: 엿듣기는 line_half, 만져 보기는 글 반만(단서 인정) / 업 30: 보스 엿듣기 닫힘, 단서 물건은 "손이 미끄러진다" / 업 60: 소문까지 닫힘',
  'structure': 'belief(보스가 믿는 것) → 단서 셋이 각각 그 믿음의 빈틈을 비춘다(points_to) → 천도 기억이 truth를 보여 준다. 단서는 정답을 말하지 않고 플레이어가 먼저 짐작하게 한다',
  'numbers': '보스의 숫자(서른일곱·일곱·열셋·열넷)는 단서 물건과 단서 대사에만 쓴다. barks·장례 자막에는 쓰지 않는다',
  'npc': 'npc는 npc_act2.json의 산 사람 id. 단서 대사는 npc_act2 schedule에도 같은 글자로 들어 있다',
  'map': MAP_NOTE,
 },
 'boss_clues': BOSSES,
}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(BOSSES), 'bosses')
