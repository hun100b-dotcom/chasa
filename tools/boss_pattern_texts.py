# -*- coding: utf-8 -*-
# 코드팀이 붙일 보스 패턴 3개(B-01 큰물 단계 bigwater · 물살 flood, B-10 기울기 tilt)와 원념 짙은 구역 경고의 문구.
# 왜 따로 두나: 패턴은 싸움 한복판에 뜨므로 글이 짧아야 하고, 보스 말풍선 상한(보스당 3줄)을 넘지 않게 한곳에서 센다.
#   - B-01은 컷 말풍선이 이미 3줄(배 떠나오 · 한 사람만 더 · 아직 못 건넸소) → 새 줄을 만들지 않고 "한 사람만 더"를 범람 때 다시 쓴다.
#   - B-10은 컷에 말풍선이 없다 → 패턴 말풍선 3줄까지. 진실(줄을 끊었다, ★F24)은 천도 기억 몫이라 싸움 중에는 "붙들어라"까지만.
# 화면 경고: 한 줄 22자 · 두 줄까지 · 끝 마침표 없음. 느낌표는 위험 알림에만(hud-controls-spec §10). 결말 비밀 낱말(큰물 등)은 화면에 안 쓴다.
# 실행: python3 tools/boss_pattern_texts.py → docs/narrative/boss_pattern_texts.json
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'boss_pattern_texts.json')

# event: 코드 이름표(sound-call-check의 flood · bigwater · tilt와 같은 말) / when: 띄우는 때 / bubble: 보스 머리 위 말풍선(1.5초) / warn: 화면 위 가운데 경고(2초) / sfx: 사운드팀 이름표(있는 것)
PATTERNS = {
 'B-01': {'name': '나루 영감', 'existing_bubbles': ['배 떠나오.', '…한 사람만 더.', '아직… 못 건넸소.'],
  'events': [
   {'event': 'bigwater', 'when': '맺힘 50% — 물이 불어 바닥이 18 m → 11 m로 좁아지기 시작할 때(한 번)',
    'bubble': '…한 사람만 더.', 'bubble_reuse': True, 'warn': '물이 분다 — 발 디딜 곳이 줄어든다!', 'sfx': 'sfx.boss.naru.bigwater'},
   {'event': 'flood', 'when': '물살 밀기 예고(처음 한 번만 글자, 소리는 매번)', 'warn': '물살 — 띠 밖으로!', 'sfx': 'sfx.boss.naru.flood'},
   {'event': 'stain_merge', 'when': '물에 뜬 파혼 얼룩 셋이 모여 거센 혼이 일어설 때(매번)', 'warn': '얼룩 셋이 모여 일어선다!',
    'note': '기획 문서의 "큰물귀신"은 화면에 쓰지 않는다(결말 낱말). 이름 띠는 "물에 뜬 얼룩"'},
   {'event': 'weak_tilt', 'when': '휩쓸기 뒤 배가 기울어 1.5초 무방비(처음 한 번만 글자)', 'warn': '배가 기울었다'},
  ]},
 'B-10': {'name': '만선호 선장', 'existing_bubbles': [],
  'events': [
   {'event': 'tilt', 'when': '갑판이 처음 기울 때(한 번). 그 뒤 기울기는 글자 없이 소리 · 화면 기울임만',
    'bubble': '줄 잡아라. 놓지 마라.', 'warn': '갑판이 기운다 — 미끄러진다!', 'sfx': 'sfx.boss.seonjang.tilt'},
   {'event': 'storm', 'when': '맺힘 50% — 기울기 주기 6초 → 4초로 바뀔 때(한 번)',
    'bubble': '붙들어라… 다 붙들어.', 'warn': '폭풍 — 갑판이 더 자주 기운다!', 'sfx_note': '전용 소리 없음 — sfx.boss.seonjang.tilt를 두 번 겹쳐 쓴다'},
   {'event': 'weak_rope', 'when': '줄 끊기 뒤 늘어진 밧줄 끝을 사슬로 끌어 선장이 넘어질 때(처음 한 번만 말풍선)',
    'bubble': '…무겁다.', 'warn': '밧줄 끝 — 끌어당겨라', 'note': '처음 넘어질 때 한 번. 말풍선이 진실(F24)을 앞질러 말하지 않게 한 낱말'},
  ]},
}

# 원념 짙은 구역(위험 지역: 10초마다 혼 3~6 + 덩어리). 지역 들어섬 알림 자리(상단 가운데), 2초.
DANGER = {
 'enter': '원념이 짙다 — 혼이 몰려든다!',
 'enter_sub': '천도는 더 위험하다',
 'leave': '원념이 옅어졌다',
 'karma_high': '원념이 짙다 — 발밑이 끈적하다!',
 'rule': {
  'enter': '처음 들어설 때마다(나갔다 30초 안에 다시 들어오면 생략). enter + 0.4초 뒤 enter_sub를 둘째 줄로. sfx.danger.enter',
  'enter_sub': '그 세이브에서 처음 세 번만(가르치는 줄). 천도 · 파혼 어느 쪽도 권하지 않고 사실만',
  'leave': '구역을 벗어날 때, 글만(소리 없음)',
  'karma_high': '업 30 이상이면 enter 대신(얼룩이 잘 붙는 몸이 됐다는 감각). 숫자 설명 없음',
 },
}

ok = set(chr(c) for c in range(0x20, 0x7f))
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: ok.add(bytes([hi, lo]).decode('euc-kr'))
        except Exception: pass
ok |= set("·…—–‘’“”×%+-~「」")
BANNED = ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌', '열두째', '여덟째', '횃불', '큰물')  # ip-scan:allow (금지어 검사 목록)


def chk(t, n=22):
    assert len(t) <= n, (t, len(t))
    for ch in t: assert ch in ok, (t, ch)
    for w in BANNED: assert w not in t, (t, w)


for b, p in PATTERNS.items():
    new = [e['bubble'] for e in p['events'] if 'bubble' in e and not e.get('bubble_reuse')]
    assert len(p['existing_bubbles']) + len(new) <= 3, (b, '보스 말풍선 3줄 상한')
    for e in p['events']:
        if 'bubble' in e: chk(e['bubble'])
        if e.get('bubble_reuse'): assert e['bubble'] in p['existing_bubbles']
        chk(e['warn']); assert not e['warn'].endswith('.')
for k in ('enter', 'enter_sub', 'leave', 'karma_high'):
    chk(DANGER[k]); assert not DANGER[k].endswith('.')

if __name__ == '__main__':
    json.dump({'_설명': '보스 패턴 말풍선 · 경고(B-01 범람 · 큰물귀신, B-10 기울기)와 원념 짙은 구역 경고. tools/boss_pattern_texts.py로 생성. 서사 2026-10-26',
               'patterns': PATTERNS, 'danger_zone': DANGER},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('patterns', sum(len(p['events']) for p in PATTERNS.values()), '| danger', 4)
