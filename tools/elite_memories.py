# -*- coding: utf-8 -*-
# 거센 혼(이름 띠 강적)의 기억 — 첫 판 EL-001(두레 좌상 오봉) + 구역 공용 줄 30(시즌 1 ①~⑥ 18, 시즌 2 ⑦~⑩ 12).
# 근거: 기획 planning/combat/first-elite-and-dosul-cards.md §3(id 규칙 EL-<지역 두 자리>-<번호 두 자리>, 구역마다 3줄).
# 왜 따로: 거센 혼은 이름 없는 강적이라 혼 목록(soul_memories souls)에 넣지 않는다. 천도하면 그 구역 줄에서 하나(그 판에 이미 본 줄은 뺌).
# 글 규칙: 거센 혼은 "화가 덜 풀린 혼" — 억울함 · 다 못 한 일 한 가지. 결말 비밀(큰물 밤 둑 · 횃불 · 열둘) · 시즌 3 사실(사슬 무덤 · 첫 우물)은 쓰지 않는다.
#   기존 혼의 기억 줄과 겹치지 않게(자체 검사), 글꼴 KS X 1001 글자만, 동그라미 숫자는 지역 이름으로.
# 실행: python3 tools/elite_memories.py → docs/narrative/elite_memories.json
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'elite_memories.json')
SOULS = json.load(open(os.path.join(HERE, '..', 'docs', 'narrative', 'soul_memories.json'), encoding='utf-8'))

FIRST = {'id': 'EL-001', 'name': '두레 좌상 오봉', 'band': '거센 혼', 'region': 1, 'zone': 'Field',
         'where': '첫 밤 보릿들 둑길 들머리(기획 §1-1)',
         'life': '보릿들 두레패를 이끌던 좌상. 징을 쳐 들일꾼을 모았다. 올봄 보리 베기 마지막 날 둑길 들머리에서 징채를 쥔 채 쓰러졌다.',
         'memory': '징을 치면 들판이 다 모였다. 아무도 오지 않아서, 더 세게 쳤다.',
         'tint': '징 놋빛', 'funeral': False,
         'note': '이름 띠는 「거센 혼」. 이름은 천도할 때 명부에서 처음 읽힌다. 부르기(맺힘 50%) 울부짖음에 징 소리를 섞는다. 잔넋 셋은 그의 두레패가 아니라 징 소리에 끌려온 들판의 잔넋. 파혼하면 징이 한 번 갈라지는 소리, 기억 없음'}

POOL = {
 (1, '솔고개'): ['보리는 다 벴는데 아무도 새참을 내오지 않았다.',
               '장날 싸움에서 진 채로 죽었다. 아직 주먹이 안 펴진다.',
               '빚 문서를 태우러 가던 길이었다. 불씨가 먼저 꺼졌다.'],
 (2, '검은여울'): ['장세를 두 번 냈다. 세 번째는 못 내겠다고 했다.',
               '외상값 받으러 간 집 문 앞에서 쓰러졌다. 문은 끝내 안 열렸다.',
               '고뿔이라고 하라기에 고뿔이라고 했다. 그래도 화가 안 풀린다.'],
 (3, '붉은재'): ['물러서라는 북은 끝내 울리지 않았다.',
              '칼을 놓으면 진 것 같아서 못 놓았다.',
              '누구와 싸우는지 모르고 싸웠다. 아직도 모른다.'],
 (4, '쇳골'): ['한 자만 더 파라고 했다. 그 한 자가 무너졌다.',
             '품삯을 쌀로 준다더니 돌가루를 주었다.',
             '곡괭이 소리가 그치면 무서워서 더 세게 내리쳤다.'],
 (5, '갯마을'): ['풍랑이 온다는데 선주가 배를 내보냈다.',
              '객주에게 뱃삯을 떼였다. 바다에서도 그 생각만 났다.',
              '만선 깃발을 달고 돌아오는 꿈을 백 번 꾸었다.'],
 (6, '도성'): ['성문 닫히는 소리를 바로 코앞에서 들었다.',
             '품을 팔러 왔는데 아무도 나를 사지 않았다.',
             '관아 문 앞에서 사흘을 외쳤다. 북은 치지 못하게 했다.'],
 (7, '삼도천'): ['줄이 줄지 않는다. 앞사람 뒤통수만 보고 섰다.',
              '배가 오다가 돌아간다. 몇 번 봤는지 셀 수도 없다.',
              '노잣돈을 쥐고 왔는데 받을 사람이 없다.'],
 (8, '명부전 담장 밖'): ['이름 대신 숫자를 받았다. 숫자로는 아무도 나를 안 부른다.',
                    '문서 한 장이 모자라 들어가지 못했다.',
                    '담장 너머에서 누가 부르는 것 같았다. 문은 안 열렸다.'],
 (9, '빈 고을'): ['인 없는 이름이라 아무도 데리러 오지 않았다.',
              '문패를 걸었는데 읽어 주는 사람이 없었다.',
              '기다리는 것도 화가 난다. 그래도 또 기다렸다.'],
 (10, '열째 관할'): ['여기가 끝이라고 들었다. 끝에도 줄이 있었다.',
                 '이름을 잃었다. 찾으러 온 길도 잃었다.',
                 '백 년을 세다가 셈을 잊었다. 화는 안 잊었다.'],
}

# 검사: 글꼴 · 금지어 · 기존 혼 기억과 겹침 · 줄 수
ok = set(chr(c) for c in range(0x20, 0x7f))
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: ok.add(bytes([hi, lo]).decode('euc-kr'))
        except Exception: pass
ok |= set("·…—–‘’“”×%+-~「」")
BANNED = ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌', '열두째', '여덟째', '횃불', '큰물', '우물', '사슬 무덤')
olds = {s['memory'] for s in SOULS['souls']}
rows = []
for (r, nm), lines in POOL.items():
    assert len(lines) == 3
    for i, ln in enumerate(lines, 1):
        rows.append({'id': f'EL-{r:02d}-{i:02d}', 'region': r, 'region_name': nm, 'season': 1 if r <= 6 else 2, 'memory': ln})
for x in rows + [FIRST]:
    t = x['memory'] + x.get('life', '')
    for ch in t: assert ch in ok, (x['id'], ch)
    for w in BANNED: assert w not in t, (x['id'], w)
    assert x['memory'] not in olds, x['id']
    assert len(x['memory']) <= 40, x['id']
assert len(rows) == 30 and len({x['memory'] for x in rows}) == 30

data = {'_설명': '거센 혼 기억 — 첫 판 EL-001 + 구역 공용 줄 30. tools/elite_memories.py로 생성. 서사 2026-10-26',
        'rules': {'pick': '천도하면 그 구역 줄에서 하나(그 판에 이미 본 줄은 뺀다). 파혼은 기억 없음',
                  'band': '이름 띠는 언제나 「거센 혼」. 첫 판(EL-001)만 천도할 때 명부에서 이름이 읽힌다',
                  'season3': '시즌 3 아래층은 거센 혼 대신 백 — 줄 없음'},
        'first': FIRST, 'pool': rows}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('first 1 + pool', len(rows))
