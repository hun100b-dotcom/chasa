# -*- coding: utf-8 -*-
# 서낭당 5곳(아트 PR #37, docs/SEONANG-SET.md)의 문구 + 처음 10분 솔고개 첫 밤 엿듣기 보강.
#   1) seonang: 서낭당마다 "처음 만져 볼 때"(그 서낭당에서 F를 처음 누를 때) 한 번 뜨는 두 줄과,
#      쉬기를 마친 뒤 기존 시스템 줄("서낭당에 이름을 걸어 두었다") 다음에 뜨는 풍경 한 줄(낮·밤 풀에서 하나).
#      ①은 "산 사람이 만든 것은 손이 지나가고, 사람이 놓지 않은 것만 닿는다"(세계 이치, 소설 2장)를 처음 보여 주는 자리다.
#   2) first_night: 게임을 처음 켠 첫 밤(밤 9시 무렵 깨어남 → 박돌쇠 처결까지 시계 멈춤 → 그 밤 끝까지)에만 들리는 엿듣기 13자리.
#      지금 첫 밤에 들을 수 있는 말은 순임(저녁)·윤 소사네 제사(자시) 둘뿐이라, 걷는 길(서낭당 → 정자 → 우물 → 보릿들 둑 → 대장간)에
#      약 40초마다 하나씩 귀 아이콘이 걸리도록 채운다. 모두 단서가 아닌 소문(clue null) — 기록 탭 "들은 말"에만 남는다.
# 지킨 것: 산 사람끼리 하는 말(혼잣말은 당할미만 → 여기엔 당할미 없음) · 지나가는 그를 두고 "춥다" 하지 않음(물·불·종이만 흔들림) ·
#          천도/파혼 뒤 흔적은 같은 무게(정답 표시 금지) · 결말 비밀 낱말 금지 · 덕만의 제사 낱말 안 씀.
# 글자 규칙: 화면 알림(서낭당 줄)은 한 줄 22자 · 두 줄까지 · 끝 마침표 없음. 엿듣기 대사는 40자 안, 반쪽(line_half)은 22자 안.
# 실행: python3 tools/seonang_texts.py → docs/narrative/seonang_texts.json
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'docs', 'narrative', 'seonang_texts.json')
PLACES = json.load(open(os.path.join(ROOT, 'data', 'art', 'npc_places_act1.json'), encoding='utf-8'))['places']

# ── 1) 서낭당 5곳 ──
# first_touch: 두 줄(줄마다 22자). rest_day / rest_night: 쉬기 뒤 한 줄 풀(하나 고름, 같은 줄 연달아 금지).
# after_boss: 그 관할 보스를 처결한 뒤 낮 쉬기 첫 번에 rest_day 대신 한 번(천도·파혼 같은 무게).
SEONANG = [
 {'model': 'prop_seonangdang_solgogae', 'zone': '① 솔고개 마을',
  'first_touch': ['금줄에 손이 그대로 지나간다', '서낭나무 껍질만 손바닥에 닿는다'],
  'rest_day': ['볕이 드는데 발밑이 비어 있다', '오방색 헝겊 다섯이 바람에 논다'],
  'rest_night': ['제물상 촛불이 이쪽으로 눕는다', '떡 냄새가 아직 남아 있다'],
  'rest_halmi': '할미가 문득 이쪽을 돌아본다',
  'note': 'rest_halmi는 당할미가 서낭당에 있을 때(새벽·저녁)만 rest_* 대신. 찬 기운을 아는 산 사람은 할미뿐(WORLD-BIBLE §5-1)'},
 {'model': 'prop_seonangdang_boritdeul', 'zone': '② 보릿들',
  'first_touch': ['솟대 장대에 손이 지나간다', '발밑 흙만 축축하게 닿는다'],
  'rest_day': ['보리 이삭 단지가 가득하다', '솟대 새가 마을 쪽을 본다'],
  'rest_night': ['짚단 냄새가 난다', '멀리 물꼬 소리가 들린다']},
 {'model': 'prop_seonangdang_mulmagi', 'zone': '③ 물막이 골 어귀',
  'first_touch': ['소금이 물 쪽으로만 뿌려져 있다', '푸른 헝겊이 젖어 늘어졌다'],
  'rest_day': ['물독 둘이 가득 차 있다', '젖은 마당에 발자국이 없다'],
  'rest_night': ['골 아래서 물소리가 올라온다', '기운 장승이 물 쪽을 본다'],
  'after_boss': {'boss': 'B-01', 'tendo': '소금 무더기를 누가 쓸어 냈다', 'pahon': '물 쪽 소금 선이 한 줄 늘었다'}},
 {'model': 'prop_seonangdang_geomeun', 'zone': '④ 검은여울 어귀',
  'first_touch': ['금줄이 가운데서 끊겨 있다', '당집 문에 널을 엇대어 박았다'],
  'rest_day': ['장꾼들이 이 앞을 돌아서 간다', '재 원 밖에 발자국이 많다'],
  'rest_night': ['촛불 심지가 젖은 채 있다', '재 원 안이 고요하다'],
  'after_boss': {'boss': 'B-03', 'tendo': '문에 박힌 널 하나가 빠져 있다', 'pahon': '재 원이 한 겹 더 둘러졌다'}},
 {'model': 'prop_seonangdang_pyedang', 'zone': '⑤ 폐당집 어귀',
  'first_touch': ['깨진 그릇 조각이 손에 닿는다', '누가 쓰던 것인지 모른다'],
  'rest_day': ['내려앉은 지붕에 볕이 든다', '고사목에 걸 가지가 마땅찮다'],
  'rest_night': ['혼불 하나가 꺼지지 않는다', '꺼진 향 냄새가 오래 남았다'],
  'after_boss': {'boss': 'B-02', 'tendo': '그릇 조각이 한데 모여 있다', 'pahon': '그릇 조각이 더 잘게 깨져 있다'},
  'note': '⑤는 아직 배치 자리 없음(SEONANG-SET). 깨진 그릇이 닿는 것은 죽은 이의 물건이라서(세계 이치) — 풀어 말하지 않는다'},
]
SEONANG_RULE = {
    'first_touch': '그 서낭당에서 F(쉬기·넋길·만져 보기 무엇이든)를 처음 누를 때 한 번. 화면 하단 월드 안내 자리, 두 줄 3초. 저장(seonangTouched)',
    'rest': '쉬기를 마친 뒤 기존 줄 "서낭당에 이름을 걸어 두었다" 다음 0.6초 뒤에 한 줄 2.5초. 낮이면 rest_day, 밤이면 rest_night에서 하나(직전과 다른 줄)',
    'after_boss': '그 관할 보스 처결 뒤 첫 낮 쉬기 한 번만 rest_day 대신. 천도·파혼 둘 다 같은 길이 · 같은 자리',
    'death_wake': '첫 죽음(M13): 가장 가까운 서낭당에서 깨어날 때 한 줄 — 서사 확인',
}
DEATH_WAKE = '아직 보낼 이름이 남았다'

# ── 2) 첫 밤 엿듣기(솔고개, 처음 10분) ──
# near = npc_places_act1.json 자리 이름, off = 그 자리에서 (동, 북) m. through = 담·창호지 너머(사람 모델 없이 소리만 — 아트 추가 없음).
# cond: any = 첫 밤 내내 / first_judge = 첫 처결 뒤 / before:S-001 = 박돌쇠 처결 전 / tendo:S-001 · pahon:S-001 = 처결 뒤 그 갈래만.
FIRST_NIGHT = [
 {'id': 'FN-01', 'near': '서낭당 고개 고갯마루', 'off': [0, -4], 'through': False, 'cond': 'any',
  'lines': [('늦은 장꾼', '해 지고는 이 고개 안 넘는 법인데.'), ('장꾼 동무', '서낭당 앞에서 침이나 세 번 뱉고 가세.')],
  'half': '해 지고는 이 고개…', 'note': '등불 든 장꾼 둘이 마을 쪽으로 내려간다(이동 중 엿듣기, 6초 따라 걷기)'},
 {'id': 'FN-02', 'near': '마을 어귀 정자', 'off': [1, 0], 'through': False, 'cond': 'before:S-001',
  'lines': [('정자 사내', '대장간 날은 받았나.'), ('담뱃대 노인', '아직. 자꾸 걸리는 게 있다더구먼.')],
  'half': '대장간 날은…', 'note': '날 받기(소설 2·3장): 보내지 못한 혼이 있는 집은 날을 못 받는다. 풀어 말하지 않는다'},
 {'id': 'FN-02b', 'near': '마을 어귀 정자', 'off': [1, 0], 'through': False, 'cond': 'tendo:S-001',
  'lines': [('정자 사내', '대장간 날 받았다네. 내일 아침이래.'), ('담뱃대 노인', '그래. 걸리던 게 풀렸구먼.')],
  'half': '대장간 날 받았다네…'},
 {'id': 'FN-02c', 'near': '마을 어귀 정자', 'off': [1, 0], 'through': False, 'cond': 'pahon:S-001',
  'lines': [('정자 사내', '대장간은 날 안 받고 그냥 묻는다네.'), ('담뱃대 노인', '…조등만 걸어 두라 그래.')],
  'half': '대장간은 날 안 받고…', 'note': '파혼한 이름혼 = 장례 없이 대문에 조등만(첫 세션 정본)'},
 {'id': 'FN-03', 'near': '당할미 집', 'off': [4, 0], 'through': True, 'cond': 'any',
  'lines': [('옆집 아낙', '할미는 오늘도 안 들어오셨네.'), ('옆집 사내', '그 양반은 밤엔 서낭당이 집이여.')],
  'half': '할미는 오늘도…'},
 {'id': 'FN-04', 'near': '우물가', 'off': [0, 0], 'through': False, 'cond': 'first_judge',
  'lines': [('밤물 긷는 아낙', '아까 물독 물이 혼자 일렁였어.'), ('그 딸', '바람도 없는데요.')],
  'half': '아까 물독 물이…', 'note': '첫 혼을 처결한 그 우물가. 그가 남긴 흔적은 물만 흔들린다(세계 이치)'},
 {'id': 'FN-05', 'near': '우물가', 'off': [-5, 3], 'through': True, 'cond': 'any',
  'lines': [('창호지 너머 아낙', '오늘 밤엔 문고리 꼭 걸어요.'), ('창호지 너머 사내', '대장간 양반 가고는 밤마다 그 소리네.')],
  'half': '오늘 밤엔 문고리…'},
 {'id': 'FN-06', 'near': '우물가', 'off': [6, -2], 'through': True, 'cond': 'before:S-001',
  'lines': [('잠 못 든 아이', '엄마, 대장간 할아버지 이제 망치 안 쳐?'), ('아이 어미', '…그래. 이제 자.')],
  'half': '엄마, 대장간 할아버지…'},
 {'id': 'FN-07', 'near': '윤 소사네 마당', 'off': [0, 2], 'through': False, 'cond': 'any',
  'lines': [('윤 소사네 아들', '어머니가 늘 차리던 상이다.'), ('윤 소사네 며느리', '올해는 제가 메를 지을게요.')],
  'half': '어머니가 늘 차리던…', 'note': '자시 제사(B01-D1 지켜보기) 앞 준비. 제사가 시작되면 닫힌다'},
 {'id': 'FN-08', 'near': '도씨네 집', 'off': [3, 0], 'through': True, 'cond': 'any',
  'lines': [('도씨네 아낙', '줄배 줄이 또 풀렸대. 아무도 안 만졌는데.'), ('도씨네 사내', '그 얘긴 할미 앞에서 하지 마라.')],
  'half': '줄배 줄이 또…', 'note': '나루 영감(B-01) 쪽으로 눈을 돌리는 소문. 단서 아님'},
 {'id': 'FN-09', 'near': '보릿들 둑', 'off': [-6, 0], 'through': False, 'cond': 'any',
  'lines': [('물꼬 보는 아비', '둑 위로는 올라가지 마라. 해 지면 거긴 우리 자리가 아니다.'), ('그 아들', '…누구 자린데요?')],
  'half': '둑 위로는 올라가지…', 'note': '둑길 싸움(2:30) 전에 들으면 좋다. 등불 하나, 물꼬만 보고 돌아간다'},
 {'id': 'FN-10', 'near': '대장간', 'off': [-4, 3], 'through': True, 'cond': 'before:S-001',
  'lines': [('용득', '풀무 불은 꺼뜨리지 마라.'), ('금순', '아버지 오시면 쇠 달구신다고요?')],
  'half': '풀무 불은 꺼뜨리지…', 'note': '대장간 뒤 담 너머. 문 앞의 박돌쇠와 싸우기 전에 들을 수 있게 뒤쪽에 둔다'},
 {'id': 'FN-11', 'near': '대장간', 'off': [-4, -3], 'through': True, 'cond': 'before:S-001',
  'lines': [('박돌쇠 아내', '그 양반 쓰러질 때 나는 우물에 가 있었다.'), ('용득', '어머니 탓 아니에요.')],
  'half': '그 양반 쓰러질 때…', 'fact_hint': 'F1', 'note': '박돌쇠 기억("아무도 오지 않았다")의 그림자. 기억 문장을 미리 말하지 않는다'},
 {'id': 'FN-12', 'near': '대장간', 'off': [-4, 3], 'through': True, 'cond': 'tendo:S-001',
  'lines': [('금순', '오라버니, 화로 불이 방금 한 번 일었어.'), ('용득', '…날 받으러 가자. 아침에.')],
  'half': '화로 불이 방금…', 'note': 'FN-10 자리를 대신한다. 불만 흔들린다(세계 이치)'},
 {'id': 'FN-13', 'near': '대장간', 'off': [-4, 3], 'through': True, 'cond': 'pahon:S-001',
  'lines': [('금순', '오라버니, 문풍지가 한 번 크게 울었어.'), ('용득', '…문고리 걸어라.')],
  'half': '문풍지가 한 번…', 'note': 'FN-10 자리를 대신한다. 종이만 흔들린다(세계 이치). FN-12와 같은 길이'},
]
FIRST_NIGHT_RULE = {
    'when': '세이브의 첫 밤에만(깨어남 → 그 밤 새벽까지). 다음 밤부터는 npc_act1 일정대로. 각 자리 한 번',
    'through': 'true = 담·창호지 너머 목소리. 사람 모델 없이 그 자리에서 소리만 나고 머리 위 귀 아이콘은 벽에 붙는다. 엿듣기 원 3 m · 6초는 같다',
    'record': '단서 아님(clue null, 소문). 기록 탭 "들은 말". 업 10 이상이면 half, 업 60 이상이면 닫힘(마을 소문 규칙)',
    'pace': '깨어남(0:20)부터 박돌쇠(5:00)까지 걷는 길에 귀 아이콘이 약 40초마다 하나씩 보이게 놓았다. 기존 둘(순임 B01-D3, 윤 소사네 제사 B01-D1)과 겹치지 않음',
    'speaker': '대화창 이름 탭 = lines[].speaker. 두 줄이 차례로 뜬다(30자/초)',
}

# ── 검사 ──
ok = set(chr(c) for c in range(0x20, 0x7f))
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: ok.add(bytes([hi, lo]).decode('euc-kr'))
        except Exception: pass
ok |= set("·…—–‘’“”×%+-~「」")
BANNED = ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌', '열두째', '여덟째', '횃불', '큰물')  # ip-scan:allow (금지어 검사 목록)


def chk(t, n, toast=False):
    assert len(t) <= n, (t, len(t))
    for ch in t: assert ch in ok, (t, ch)
    for w in BANNED: assert w not in t, (t, w)
    if toast: assert not t.endswith('.'), t


seen = set()
for s in SEONANG:
    assert len(s['first_touch']) <= 2
    toasts = s['first_touch'] + s['rest_day'] + s['rest_night'] + ([s['rest_halmi']] if 'rest_halmi' in s else [])
    if 'after_boss' in s: toasts += [s['after_boss']['tendo'], s['after_boss']['pahon']]
    for t in toasts:
        chk(t, 22, True); assert t not in seen, t; seen.add(t)
chk(DEATH_WAKE, 22, True)
ids = set()
for o in FIRST_NIGHT:
    assert o['near'] in PLACES and PLACES[o['near']]['zone'] in ('Hub', 'Village', 'Field'), o['id']
    assert o['id'] not in ids; ids.add(o['id'])
    for sp, ln in o['lines']: chk(sp, 10); chk(ln, 40)
    chk(o['half'], 22); assert o['half'].endswith('…')
assert len([o for o in FIRST_NIGHT if o['cond'] in ('any', 'first_judge', 'before:S-001')]) >= 10

def pos(o):
    p = PLACES[o['near']]
    return {'zone': p['zone'], 'x': round(p['x'] + o['off'][0], 1), 'y': round(p['y'] + o['off'][1], 1)}

data = {
    '_설명': '서낭당 5곳 문구(처음 만져 볼 때 · 쉬기) + 첫 밤 솔고개 엿듣기 보강. tools/seonang_texts.py로 생성. 서사 2026-10-26',
    'seonang': {'rule': SEONANG_RULE, 'death_wake': DEATH_WAKE, 'shrines': SEONANG},
    'first_night_overhear': {'rule': FIRST_NIGHT_RULE, 'spots': [
        dict({'id': o['id'], 'near': o['near'], 'pos': pos(o), 'through_wall': o['through'], 'cond': o['cond'],
              'lines': [{'speaker': sp, 'text': ln} for sp, ln in o['lines']], 'line_half': o['half'], 'clue': None},
             **({'fact_hint': o['fact_hint']} if 'fact_hint' in o else {}), **({'note': o['note']} if 'note' in o else {}))
        for o in FIRST_NIGHT]},
}
if __name__ == '__main__':
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('seonang', len(SEONANG), '| first_night', len(FIRST_NIGHT))
