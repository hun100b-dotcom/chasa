# -*- coding: utf-8 -*-
# 2막(③ 붉은재 싸움터 · ④ 쇳골 광산) 엿듣기 밀도 보강 — 마을 소문 15자리.
# 왜: 1막은 단서 말 8 + 소문 13(+첫 밤 15)인데, 2막은 단서 말 9뿐이고 소문이 0이었다. 길을 걸어도 귀 아이콘이 드물어
#     "산 사람이 사는 땅"이 비어 보였다. 1막 수준(구역마다 소문 2~3)으로 채운다.
# 소문의 일: 그 땅의 상처(사람을 번호로 부르는 곳)를 풍경으로 들려주고, 이름 있는 혼(S-049~S-083)의 삶을 미리 비춘다.
# 지킨 것(npc_act2.py 머리말 그대로):
#  - 단서 아님(clue null). 기록 탭 "들은 말". 업 10 이상 반쪽, 업 60 이상 닫힘(마을 소문 규칙).
#  - 보스 단서와 겹치는 말 금지: 서른일곱 · 술 붓기 · 깃발 아저씨 · 일곱 · 장군 위패(③) / 목패 七 · 열셋 · 열넷 · 반장 · 장부 앞장/뒷장 · 머릿수 보상(④).
#  - 산 사람끼리의 말. 이름은 짓지 않고 역할로(혼의 이름은 이미 있는 것만). 밤에는 담 너머 목소리만.
# 실행: python3 tools/overhear_act2.py → docs/narrative/overhear_act2.json
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'docs', 'narrative', 'overhear_act2.json')
MAP = os.path.join(ROOT, 'unity', 'Assets', 'Resources', 'Data', 'act2_map.json')  # 기획 act2_map.json의 코드 사본
SOULS = {s['id']: s for s in json.load(open(os.path.join(ROOT, 'docs', 'narrative', 'soul_memories.json'), encoding='utf-8'))['souls']}

# (id, 시간, 자리, 담 너머?, [(말한 이, 말)], 반쪽, 비추는 혼)
R = [
 # ── ③ 산성 아랫마을 · 산성 · 화살골 · 큰 무덤 ──
 ('R2-01', '낮', '아랫마을 마당', False, [('빨래하는 아낙', '이장 어른 가시고는 관아 서찰 읽어 줄 사람이 없어.'), ('그 동무', '읽어 봐야 숫자뿐이라던데.')], '이장 어른 가시고는…', 'S-058'),
 ('R2-02', '저녁', '아랫마을 우물', False, [('석수 제자', '성돌 밑에서 썩은 목패가 또 나왔어요.'), ('물 긷는 노인', '도로 묻어라. 읽지 말고.')], '성돌 밑에서…', 'S-051'),
 ('R2-03', '저녁', '벌초꾼 집', True, [('벌초꾼 아들', '큰 무덤은 아무리 베도 어디가 끝인지 모르겠어요.'), ('그 어미', '그러니 다 베라. 다 누구 자리다.')], '큰 무덤은 아무리 베도…', 'S-052'),
 ('R2-04', '낮', '화살골 어귀', False, [('약초 캐는 이웃', '바위틈엔 손 넣지 마. 녹슨 촉에 벤다.'), ('그 딸', '분녀 아지매는 맨손으로도 잘 캤는데.')], '바위틈엔 손 넣지…', 'S-050'),
 ('R2-05', '낮', '산성 문', False, [('나무꾼', '해 지면 성안에서 수 세는 소리가 난대.'), ('나무꾼 동무', '세다가 끊기는 게 더 무섭지.')], '해 지면 성안에서…', 'S-053'),
 ('R2-06', '밤', '이장 집', True, [('이장네 아들', '아버님이 받아 둔 관아 명단, 태울까요.'), ('이장네 안사람', '두어라. 거기엔 태울 이름도 없다.')], '관아 명단, 태울까요…', 'S-058'),
 ('R2-07', '낮', '아랫마을 남쪽 어귀', False, [('지나가는 장꾼', '건넛골 사람들도 그 골짜기에 묻혔다더구먼.'), ('장꾼 동무', '죽고 나면 이쪽 저쪽이 어디 있나.')], '건넛골 사람들도…', 'S-063'),
 ('R2-08', '낮', '작은 무덤 떼', False, [('무덤 돌보는 아낙', '설이가 큰 무덤 굿을 하다 말았대.'), ('그 시누이', '부를 이름을 못 받아서 그랬다지.')], '설이가 큰 무덤 굿을…', 'S-057'),
 # ── ④ 광부촌 · 선탄장 · 큰 갱도 ──
 ('R2-09', '새벽', '광부촌 어귀', False, [('교대 광부', '산신각에 막걸리 붓던 영감이 요새 안 보여.'), ('교대 광부 동무', '그 양반 가고는 아무도 안 붓지.')], '산신각에 막걸리…', 'S-083'),
 ('R2-10', '저녁', '국밥집', False, [('국밥집 아들', '외상은 번호 말고 이름으로 적어 주시오.'), ('늙은 광부', '…이름이 뭐였더라. 다들 번호로만 불러서.')], '외상은 번호 말고…', 'S-069'),
 ('R2-11', '낮', '노새 마구간', False, [('마부', '갑돌이 없으니 노새가 말을 안 들어.'), ('마부 동무', '제 이름 불러 주던 사람은 노새도 아는 게지.')], '갑돌이 없으니…', 'S-070'),
 ('R2-12', '저녁', '광부촌 우물가', False, [('선탄장 아낙', '복례 딸이 어미 자리에 앉았더라.'), ('다른 아낙', '손톱 까매지는 거 보면 속상해서 원.')], '복례 딸이…', 'S-068'),
 ('R2-13', '낮', '갱 입구', False, [('교대 광부', '버팀목 또 아끼래. 나무값이 비싸다고.'), ('교대 광부 동무', '그 나무값보다 싼 게 누군데.')], '버팀목 또 아끼래…', 'S-073'),
 ('R2-14', '밤', '순돌 집', True, [('순돌네 아이', '아버지 목패는 언제 돌려준대요?'), ('순돌네 안사람', '떼어 온 사람이 있대. 내일 갖다준다더라.')], '아버지 목패는…', 'S-067'),
 ('R2-15', '낮', '갱도 골 중간 버팀목', False, [('목수 제자', '이 버팀목, 목수 어른이 세운 거야. 아직 안 휘었어.'), ('짐꾼', '사람은 갔는데 나무는 버티네.')], '이 버팀목…', 'S-073'),
]
ZONE_REGION = {'FortressVillage': '③', 'Fortress': '③', 'ArrowValley': '③', 'Camp': '③', 'BigTomb': '③',
               'MinerTown': '④', 'Sorting': '④', 'MainShaft': '④', 'Collapse': '④'}

ok = set(chr(c) for c in range(0x20, 0x7f))
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: ok.add(bytes([hi, lo]).decode('euc-kr'))
        except Exception: pass
ok |= set("·…—–‘’“”×%+-~「」")
BANNED = ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌', '열두째', '여덟째', '횃불', '큰물',  # ip-scan:allow (금지어 검사 목록)
          '서른일곱', '깃발 아저씨', '일곱', '위패', '열셋', '열넷', '반장', '앞장', '뒷장', '머릿수', '술 붓', '술을 붓')  # 2막 보스 단서 낱말


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
    assert sid in SOULS, sid
    for sp, ln in lines: chk(sp, 10); chk(ln, 40)
    chk(half, 22); assert half.endswith('…')
from collections import Counter
reg = Counter(ZONE_REGION[places[pl]['zone']] for _, _, pl, *_ in R)
assert reg['③'] >= 7 and reg['④'] >= 7, reg

spots = [{'id': rid, 'time': tm, 'zone': places[pl]['zone'], 'place': pl, 'x': places[pl]['x'], 'y': places[pl]['y'], 'verb': '엿듣기',
          'through_wall': wall, 'lines': [{'speaker': sp, 'text': ln} for sp, ln in lines], 'line_half': half, 'clue': None,
          'echoes_soul': sid, 'echoes_name': SOULS[sid]['name']} for rid, tm, pl, wall, lines, half, sid in R]
data = {
    '_설명': '2막 엿듣기 밀도 보강(마을 소문 15). tools/overhear_act2.py로 생성. 서사 2026-10-26. 자리 · 좌표는 기획 act2_map.json places',
    'rule': {
        'record': '단서 아님(clue null). 기록 탭 "들은 말". 업 10 이상 line_half, 업 60 이상 닫힘(npc_act1 rules.karma와 같음)',
        'unlock': '그 구역에 밤에 처음 들어간 다음 낮부터(보스 단서와 같은 열림). 각 자리 하루 한 번',
        'through_wall': 'true = 담 너머 목소리(사람 모델 없음, 귀 아이콘은 벽에). 밤 자리는 모두 담 너머',
        'echo': 'echoes_soul의 혼을 천도해 장례를 봤으면 다음 낮부터 이 자리는 닫는다(그 집 이야기가 장례로 끝났으므로)',
        'density': '③ 8 · ④ 7. 1막(소문 13)과 같은 수준. 보스 단서 말 9와 겹치는 자리는 피했다',
    },
    'spots': spots,
}
if __name__ == '__main__':
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('act2 rumors', len(R), dict(reg))
