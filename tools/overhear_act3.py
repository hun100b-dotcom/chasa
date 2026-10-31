# -*- coding: utf-8 -*-
# 3막(⑤ 갯마을 포구 · ⑥ 도성 아랫마을) 엿듣기 밀도 보강 — 마을 소문 15자리. overhear_act2.py와 같은 모양.
# 왜: 3막은 단서 말 8 + 별명 말(무적 혼 천도 열쇠)뿐이고 마을 소문이 0이었다. 1막 수준(구역마다 2~3)으로 채운다.
# 지킨 것(npc_act3.py 머리말 그대로):
#  - 단서 아님(clue null). 업 10 반쪽, 업 60 닫힘.
#  - 보스 단서 낱말 금지: 만선호 · 선장 · 헛묘 · 장부 · 빗(⑤) / 왕초 · 기둥 별명 · 서생 · 방 · 붓(⑥), 숫자 마흔둘 · 일곱.
#  - ⑥ 무적 혼의 별명은 소문에서 절대 말하지 않는다(별명을 들으면 그 혼이 천도 가능해지는 장치라, nickname_lines에서만).
#  - 결말 비밀(횃불 · 큰물 · 여덟째 · 일곱째)을 말하는 혼(S-096, S-120)과 흑월 쪽 혼(S-102 · S-112 · S-117 · S-118)은 비추지 않는다.
# 실행: python3 tools/overhear_act3.py → docs/narrative/overhear_act3.json
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'docs', 'narrative', 'overhear_act3.json')
MAP = os.path.join(ROOT, 'unity', 'Assets', 'Resources', 'Data', 'act3_map.json')  # 기획 act3_map.json의 코드 사본
SOULS = {s['id']: s for s in json.load(open(os.path.join(ROOT, 'docs', 'narrative', 'memories_act3.json'), encoding='utf-8'))['souls']}
NICK = {s['nickname'] for s in SOULS.values() if s.get('nickname')}

# (id, 시간, 자리, 담 너머?, [(말한 이, 말)], 반쪽, 비추는 혼)
R = [
 # ── ⑤ 포구 · 소금밭 · 망부석 곶 · 난파 여울 ──
 ('R3-01', '저녁', '갯골댁 집', False, [('그물 아낙', '갯골댁 그물은 아직 그 코 하나가 비었더라.'), ('옆집 아낙', '기우지 마. 그 집에서 그렇게 두랬어.')], '갯골댁 그물은…', 'S-085'),
 ('R3-02', '낮', '소금 창고', False, [('염전 일꾼', '주인은 오늘도 우리를 판으로 세더라.'), ('일꾼 동무', '한 판 두 판… 그럼 우린 소금이냐.')], '주인은 오늘도…', 'S-092'),
 ('R3-03', '밤', '덕보 집', True, [('덕보네 안사람', '아주버님은 끝내 안 올라오셨지.'), ('덕보네 아들', '소금이나 한 줌 바다에 뿌려 드려요.')], '아주버님은 끝내…', 'S-087'),
 ('R3-04', '저녁', '순덕 집', False, [('순덕 어미', '혼례 옷은 장롱에 그대로 둬라.'), ('순덕 동생', '배 오는 날 입는다고 했으니까요.')], '혼례 옷은 장롱에…', 'S-088'),
 ('R3-05', '새벽', '등대지기 막', False, [('선창 어부', '등잔이 아침까지 켜져 있었대.'), ('어부 동무', '끄면 배가 길 잃는다고, 그 영감 버릇이지.')], '등잔이 아침까지…', 'S-089'),
 ('R3-06', '낮', '염전 둑', False, [('소금 짓는 아낙', '소금 할미는 이름 적은 쪽지를 독에 묻었대.'), ('그 딸', '썩지 말라고요? 할미다워.')], '소금 할미는…', 'S-100'),
 ('R3-07', '낮', '여울 북쪽 갯바위', False, [('해녀', '말순이가 마지막 숨비소리 낸 데가 저기야.'), ('젊은 해녀', '물 위엔 아무도 없었다면서요.')], '말순이가 마지막…', 'S-093'),
 ('R3-08', '낮', '포구 어귀', False, [('늙은 어부', '수군 명부엔 노 젓는 손만 적혔다더라.'), ('어부 동무', '손 말고 얼굴도 있었는데.')], '수군 명부엔…', 'S-099'),
 # ── ⑥ 저잣거리 · 큰 다리 · 움막촌 · 성문 밖 ──
 ('R3-09', '낮', '떡장수 좌판', False, [('옆 좌판 상인', '떡장수 할미 자리에 아이들이 아직 와.'), ('상인 동무', '떡 하나 더 얹어 주던 손을 찾는 게지.')], '떡장수 할미 자리에…', 'S-103'),
 ('R3-10', '밤', '문지기 막', True, [('문지기네 안사람', '아버님은 늘 문을 늦게 닫으셨잖아요.'), ('아들 문지기', '…누가 아직 밖에 있다고 하셨지.')], '아버님은 늘 문을…', 'S-107'),
 ('R3-11', '낮', '저잣거리 한가운데', False, [('장꾼', '객사한 나그네 고향엔 기별도 안 갔대.'), ('장꾼 동무', '누가 가. 어디서 왔는지도 모르는데.')], '객사한 나그네…', 'S-108'),
 ('R3-12', '낮', '큰 다리', False, [('다리 건너는 사내', '돌마다 일꾼 이름 새긴다더니 다리 이름뿐이네.'), ('그 동무', '이름 새기는 값이 더 비쌌나 보지.')], '돌마다 일꾼 이름…', 'S-116'),
 ('R3-13', '저녁', '움막촌 우물', False, [('움막촌 아낙', '호적이 없으니 애 이름을 어디다 올리나.'), ('이웃 아낙', '우물 돌에라도 새겨 둬. 여긴 아무도 안 세.')], '호적이 없으니…', 'S-105'),
 ('R3-14', '새벽', '성문', False, [('성문 앞 장꾼', '성문 밖 구덩이엔 또 팻말 없이 묻었대.'), ('장꾼 동무', '팻말 값도 없는 사람들이지.')], '성문 밖 구덩이엔…', 'S-115'),
 ('R3-15', '저녁', '저잣거리 한가운데', False, [('좌판 상인', '광대 탈을 벗겨 보니 아무도 얼굴을 몰랐대.'), ('상인 동무', '탈 쓰고 산 세월이 더 길었으니.')], '광대 탈을 벗겨…', 'S-119'),
]
ZONE_REGION = {'Harbor': '⑤', 'SaltField': '⑤', 'WaitingRock': '⑤', 'WreckShoal': '⑤',
               'Market': '⑥', 'BridgeUnder': '⑥', 'Shacks': '⑥', 'CityGate': '⑥'}
SKIP = {'S-096', 'S-120', 'S-102', 'S-112', 'S-117', 'S-118'}  # 결말 비밀 · 흑월 쪽 혼

ok = set(chr(c) for c in range(0x20, 0x7f))
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: ok.add(bytes([hi, lo]).decode('euc-kr'))
        except Exception: pass
ok |= set("·…—–‘’“”×%+-~「」")
BANNED = ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌', '열두째', '여덟째', '횃불', '큰물',  # ip-scan:allow (금지어 검사 목록)
          '만선호', '선장', '헛묘', '장부', '빗', '왕초', '서생', '방', '붓', '마흔', '일곱')  # 3막 보스 단서 낱말


def chk(t, n):
    assert len(t) <= n, (t, len(t))
    for ch in t: assert ch in ok, (t, ch)
    for w in BANNED: assert w not in t, (t, w)


places = {p['name'] if isinstance(p, dict) and 'name' in p else k: p for k, p in json.load(open(MAP, encoding='utf-8'))['places'].items()}
ids = set()
for rid, tm, pl, wall, lines, half, sid in R:
    assert rid not in ids; ids.add(rid)
    assert tm in ('새벽', '낮', '저녁', '밤') and pl in places, (rid, pl)
    if tm == '밤': assert wall, (rid, '밤엔 담 너머만')
    assert sid in SOULS and sid not in SKIP, sid
    assert not any(nk in ln for nk in NICK for _, ln in lines), (rid, '별명 금지')
    for sp, ln in lines: chk(sp, 10); chk(ln, 40)
    chk(half, 22); assert half.endswith('…')
from collections import Counter
reg = Counter(ZONE_REGION[places[pl]['zone']] for _, _, pl, *_ in R)
assert reg['⑤'] >= 7 and reg['⑥'] >= 7, reg

spots = [{'id': rid, 'time': tm, 'zone': places[pl]['zone'], 'place': pl, 'x': places[pl]['x'], 'y': places[pl]['y'], 'verb': '엿듣기',
          'through_wall': wall, 'lines': [{'speaker': sp, 'text': ln} for sp, ln in lines], 'line_half': half, 'clue': None,
          'echoes_soul': sid, 'echoes_name': SOULS[sid]['name']} for rid, tm, pl, wall, lines, half, sid in R]
data = {
    '_설명': '3막 엿듣기 밀도 보강(마을 소문 15). tools/overhear_act3.py로 생성. 서사 2026-10-26. 자리 · 좌표는 기획 act3_map.json places',
    'rule': {
        'record': '단서 아님(clue null). 기록 탭 "들은 말". 업 10 이상 line_half, 업 60 이상 닫힘(npc_act1 rules.karma와 같음)',
        'unlock': '그 구역에 밤에 처음 들어간 다음 낮부터(보스 단서와 같은 열림). 각 자리 하루 한 번',
        'through_wall': 'true = 담 너머 목소리(사람 모델 없음, 귀 아이콘은 벽에). 밤 자리는 모두 담 너머',
        'echo': 'echoes_soul의 혼을 천도해 장례를 봤으면 다음 낮부터 이 자리는 닫는다(그 집 이야기가 장례로 끝났으므로)',
        'density': '⑤ 8 · ⑥ 7. 1막(소문 13)과 같은 수준. 보스 단서 · 별명 말 자리와 겹치지 않게 시간 · 자리를 비켰다',
        'nickname': '소문에는 무적 혼의 별명이 없다(별명은 천도 열쇠라 npc_act3 nickname_lines에서만). 자체 검사',
    },
    'spots': spots,
}
if __name__ == '__main__':
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('act3 rumors', len(R), dict(reg))
