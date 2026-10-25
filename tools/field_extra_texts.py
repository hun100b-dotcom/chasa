# -*- coding: utf-8 -*-
# 감사(planning/audit/filter-audit-1026.md) 보강 두 가지의 서사 문구.
#   5) 넋길 추가 도착점 — 보스를 "천도한" 관할에만 보스 마당 가장자리에 도착점이 하나 더 생긴다(코드 SoulRoad.extraDestination[bossId]).
#      여기서는 그 도착점의 이름(넋길 목록 · 알림 "넋길 — 이름")과 처음 닿았을 때의 한 줄.
#   6) 외톨이 야영지 — field_camps.json 20곳 가운데 7곳에 "떨어져 앉은 혼"(무리에서 12 m 넘게 떨어져 혼자 무릎 꿇는 혼 1~2).
#      여기서는 그 혼의 기억 한 줄(천도 보상)과, 낮에 그 근처에서 산 사람이 하는 엿듣기 한 줄(업 10이면 반쪽).
# 왜 문구가 필요한가: 감사의 뜻은 "천도할 틈을 지도에 심는 것". 혼자 앉은 까닭이 기억에 있어야 그 혼을 보내는 일이 의미가 된다.
# 규칙: 한 줄 22자 안(알림 · 이름), 기억은 40자 안, 마침표는 기억 · 엿듣기에만(대사 문장). 글꼴 KS X 1001. 결말 비밀 낱말 금지.
# 실행: python3 tools/field_extra_texts.py → docs/narrative/field_extra_texts.json
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'docs', 'narrative', 'field_extra_texts.json')
CAMPS = json.load(open(os.path.join(ROOT, 'unity', 'Assets', 'Resources', 'Data', 'field_camps.json'), encoding='utf-8'))['camps']
SOULS = json.load(open(os.path.join(ROOT, 'docs', 'narrative', 'soul_memories.json'), encoding='utf-8'))['souls']

# ── 넋길 추가 도착점(보스 천도한 관할만). B-04는 처결이 없고, 시즌 3 보스는 아래층이라 넋길과 무관 ──
ROAD = {
 'B-01': ('물막이 골 나루터', '삿대 꽂던 자리가 비어 있다'),
 'B-02': ('폐당집 마당', '대숲이 조용하다'),
 'B-03': ('역병막 의원 움막', '약작두 날이 내려와 있다'),
 'B-05': ('산성 깃대 터', '깃대가 땅에 누워 있다'),
 'B-06': ('군막 터', '번호 대신 이름을 부른 자리'),
 'B-07': ('무너진 막장 어귀', '곡괭이 소리가 그쳤다'),
 'B-08': ('광산 주인집 앞', '장부가 덮여 있다'),
 'B-09': ('망부석 곶', '바위 위에 아무도 없다'),
 'B-10': ('난파 여울 언덕', '갑판에 아무도 없다'),
 'B-11': ('큰 다리 밑', '아이들이 별명을 부른다'),
 'B-12': ('성문 밖 눈밭', '구덩이 위 눈이 고르다'),
 'B-13': ('빈 나루 말뚝', '맨 앞자리가 한 칸 움직였다'),
 'B-14': ('물안개 둑', '돌아선 혼들이 다시 섰다'),
 'B-15': ('문서 창고 앞', '맨 안쪽 서랍이 닫혀 있다'),
 'B-16': ('먹방 큰 벼루 곁', '먹 가는 소리가 고르다'),
 'B-17': ('아홉째 문 앞', '문 앞에 아무도 서 있지 않다'),
 'B-18': ('인장 굴 어귀', '굴 안이 어둡지 않다'),
 'B-19': ('처음 마을 우물터', '두레박이 걸려 있다'),
 'B-20': ('물막이 바닥', '물이 아래로 흐른다'),
}

# ── 외톨이 야영지 7곳(지역마다 고르게: 검은여울 1 · 솔고개 마을 1 · 보릿들 2 · 물막이 골 2 · 폐당집 1) ──
# camp = field_camps.json 순번(0부터). 기획이 다른 곳을 고르면 같은 지역 안에서 문구를 그대로 옮긴다.
LONER = [
 {'camp': 2, 'zone': '검은여울', 'who': '역병막 문밖에서 자던 사내',
  'memory': '식구한테 옮을까 봐 문밖에서 잤다. 그 버릇이 아직 남았다.',
  'overhear': ('약방 앞 아낙', '그 집 바깥양반은 끝까지 문밖에서 잤다지.', '그 집 바깥양반은…')},
 {'camp': 5, 'zone': '솔고개 마을', 'who': '마을 안에 들지 않던 떠돌이',
  'memory': '마을 안으로는 한 번도 안 들어갔다. 개가 짖을까 봐.',
  'overhear': ('고샅 아이', '장승 밖 원두막에 늘 누가 앉아 있었는데.', '장승 밖 원두막에…')},
 {'camp': 7, 'zone': '보릿들', 'who': '허수아비 곁 새 쫓던 아이',
  'memory': '다들 새참 먹으러 갔다. 나는 새를 보느라 못 갔다.',
  'overhear': ('밭일하는 아낙', '허수아비 곁에서 혼자 딸랑이 흔들던 애 있었잖여.', '허수아비 곁에서…')},
 {'camp': 10, 'zone': '보릿들', 'who': '이삭 줍던 노파',
  'memory': '남의 밭 이삭이라, 줍다 말고 늘 멀찍이 앉아 쉬었다.',
  'overhear': ('밭주인', '올해는 이삭 줍는 할매가 안 보이네.', '올해는 이삭…')},
 {'camp': 12, 'zone': '물막이 골', 'who': '벼랑 밑 피리 불던 사내',
  'memory': '사람 모인 데선 피리를 못 불었다. 그래서 벼랑 밑에 앉았다.',
  'overhear': ('나무꾼', '벼랑 밑에서 피리 소리 났다는 얘기 들었어?', '벼랑 밑에서…')},
 {'camp': 15, 'zone': '물막이 골', 'who': '약초 캐던 사내',
  'memory': '약초는 사람 없는 데 난다. 그래서 늘 혼자였다.',
  'overhear': ('장꾼', '물막이 골 약초꾼, 올봄엔 장에 안 내려오대.', '물막이 골 약초꾼…')},
 {'camp': 18, 'zone': '폐당집', 'who': '굿판 담 너머로 기웃대던 머슴',
  'memory': '굿판에는 끼지 못했다. 담 너머로 구경만 했다.',
  'overhear': ('곱단네', '굿 할 적마다 담 너머로 기웃대던 머슴 있었잖아.', '굿 할 적마다…')},
]
LONER_RULE = {
    'soul': '떨어져 앉은 혼 1~2. 첫째가 이 줄의 혼, 둘째는 그 지역 공용 기억(generic_pool)에서. 맺힘 · 넋은 보통 혼과 같다',
    'overhear': '엿듣기는 낮에 그 야영지 가장 가까운 길에서. 단서가 아니라 들은 말(기록 탭) — 보스 단서 수에 들지 않는다. 업 10 이상이면 반쪽(line_half)',
    'why': '혼자 앉은 까닭이 기억에 있다 → 무리에서 떨어진 그 혼을 먼저 보내는 일이 뜻을 갖는다(감사 6번)',
}

ok = set(chr(c) for c in range(0x20, 0x7f))
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: ok.add(bytes([hi, lo]).decode('euc-kr'))
        except Exception: pass
ok |= set("·…—–‘’“”×%+-~「」")
BANNED = ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌', '열두째', '여덟째', '횃불', '큰물')  # ip-scan:allow (금지어 검사 목록)


def chk(t, n):
    assert len(t) <= n, (t, len(t))
    for ch in t: assert ch in ok, (t, ch)
    for w in BANNED: assert w not in t, (t, w)


olds = {s['memory'] for s in SOULS}
for b, (nm, ln) in ROAD.items():
    chk('넋길 — ' + nm, 22); chk(ln, 22); assert not ln.endswith('.')
for x in LONER:
    assert CAMPS[x['camp']]['zone'] == x['zone'], x
    chk(x['memory'], 40); assert x['memory'] not in olds
    sp, line, half = x['overhear']
    chk(line, 40); chk(half, 22)
from collections import Counter
assert len(LONER) == 7 and Counter(x['zone'] for x in LONER) == Counter({'보릿들': 2, '물막이 골': 2, '검은여울': 1, '솔고개 마을': 1, '폐당집': 1})

data = {
    '_설명': '감사 1026 보강 문구 — 넋길 추가 도착점(보스 천도 관할) · 외톨이 야영지 7곳. tools/field_extra_texts.py로 생성. 서사 2026-10-26',
    'soulroad_extra': {'rule': '보스를 천도한 관할만, 밤에만. 이름은 넋길 목록과 알림 "넋길 — 이름". 처음 닿을 때 한 줄(알림, 1.5초). 파혼한 관할은 기존 서낭당만',
                       'stops': [{'boss': b, 'name': nm, 'first_arrival': ln} for b, (nm, ln) in ROAD.items()]},
    'loner_camps': {'rule': LONER_RULE,
                    'camps': [dict(camp=x['camp'], zone=x['zone'], x=CAMPS[x['camp']]['x'], z=CAMPS[x['camp']]['z'], who=x['who'],
                                   memory=x['memory'], overhear={'speaker': x['overhear'][0], 'line': x['overhear'][1], 'line_half': x['overhear'][2]})
                              for x in LONER]},
}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('road', len(ROAD), '| loner', len(LONER))
