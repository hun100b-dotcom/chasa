# -*- coding: utf-8 -*-
# 품계가 오를 때 나오는 한 줄(품계 2~20). 막대 이름은 「명부의 일」(기획 10-26, hud-controls-spec v1.5).
# 왜 이런 결인가: 품계는 "처결 셈" — 천도든 파혼이든 명부의 일로 센다. 위(명부를 내려보내는 쪽)는 몇을 처리했는지만 센다.
#   그래서 문구는 칭찬하지 않고, 명부 · 먹 · 인 같은 일의 물건이 조금씩 바뀌는 것만 보여 준다.
#   뒤로 갈수록 "셈이 이름보다 먼저 보인다"처럼 일이 사람을 닮게 바꾸는 서늘함이 조금 묻어난다(2막 번호 · 3막 장부와 같은 결).
# 지킨 것: 천도 · 파혼 어느 쪽도 가리키지 않는다. 사슬 · 몸(시즌 3 F63), 정체(F9), 저승 재판 그림은 쓰지 않는다.
# 표시: 화면 가운데 붉은 품계 인 1.0초 + 「계급명 — 문구」 한 줄(22자 안, 마침표 없음). 계급명은 Ko.RankTitle과 같은 셈.
# 실행: python3 tools/rank_texts.py → docs/narrative/rank_texts.json
import json, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'narrative', 'rank_texts.json')

LINES = {
    2: '명부가 한 장 늘었다',          # first-5-minutes 5:00 정본
    3: '먹이 조금 짙어졌다',
    4: '장 넘기는 손이 빨라졌다',
    5: '명부 끈을 한 번 더 감는다',
    6: '새 장이 먼저 와 있다',
    7: '부르는 소리가 멀리 간다',
    8: '인주 빛이 한 결 붉다',
    9: '명부가 손에 익었다',
    10: '줄 사이가 좁아졌다',
    11: '장 수를 세지 않게 되었다',
    12: '명부 표지가 닳기 시작했다',
    13: '위에서 장이 두 장씩 온다',
    14: '붉은 인이 손끝에 묻는다',
    15: '셈이 이름보다 먼저 보인다',
    16: '명부가 한 뼘 두꺼워졌다',
    17: '먹 냄새가 손에서 안 빠진다',
    18: '빈 장이 남지 않는다',
    19: '위는 여전히 답이 없다',
    20: '셀 것이 아직 남았다',
}
LATER = ['명부가 한 장 늘었다', '셀 것이 아직 남았다', '먹이 조금 짙어졌다']  # 21~50: 이 셋을 차례로 돌린다


def title(rank):  # unity Ko.RankTitle과 같은 셈
    if rank < 2: return '견습'
    i = rank - 2
    if i >= 18: return '정1품'
    return ('종' if i % 2 == 0 else '정') + str(9 - i // 2) + '품'


ok = set(chr(c) for c in range(0x20, 0x7f))
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: ok.add(bytes([hi, lo]).decode('euc-kr'))
        except Exception: pass
ok |= set("·…—–‘’“”×%+-~「」")
BANNED = ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌', '열두째', '여덟째', '횃불', '큰물',  # ip-scan:allow (금지어 검사 목록)
          '사슬', '넋', '엽전', '천도', '파혼', '잘했', '훌륭')  # 처결 갈래 · 몸 · 칭찬 금지
rows = []
for r in range(2, 21):
    full = f'{title(r)} — {LINES[r]}'
    assert len(full) <= 22 and not full.endswith('.'), full
    for ch in full: assert ch in ok, (full, ch)
    for w in BANNED: assert w not in full, (full, w)
    rows.append({'rank': r, 'title': title(r), 'line': LINES[r], 'show': full})
assert len(set(LINES.values())) == len(LINES)
assert title(2) == '종9품' and title(19) == '정1품' and title(20) == '정1품'

if __name__ == '__main__':
    json.dump({'_설명': '품계 오름 문구(품계 2~20). tools/rank_texts.py로 생성. 서사 2026-10-26',
               'rule': {'show': '화면 가운데 붉은 품계 인 1.0초 + show 한 줄(2.0초) + sfx.ui.rank.up. 천도 · 파혼 같은 크기 · 같은 길이',
                        'bar': '막대 이름 「명부의 일」(먹빛 + 끝에 붉은 인). 문구는 막대 이름과 같은 결 — 명부 · 먹 · 인의 변화만',
                        'later': '21~50은 later 셋을 차례로 돌린다(계급명은 정1품 그대로)'},
               'ranks': rows, 'later': LATER},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ranks', len(rows))
