# -*- coding: utf-8 -*-
"""업 칸 세 개의 이름과, 칸에 들어설 때·나올 때 뜨는 한 줄 → docs/narrative/karma_tier_texts.json

왜 따로 두나: 업 칸(10/30/60)은 기획 karma-s1-check 2-3절에서 '벌'이 아니라
'다른 길'(검은 갓 차사를 닮아 가는 손)이 되었다. 문구가 칭찬도 꾸중도 하지 않게
한곳에 모아 두고, 금지어 검사를 여기서 돌린다.
서사 2026-10-26
"""
import json, os, sys

# 칸 이름 — 일부러 피한 것:
#  · '흑월'  : 업 30은 1막 첫날에도 닿을 수 있는데 그 이름은 1막 끝 목격 전에 나오면 안 된다
#  · '검은 갓': 나루 기억(M-B01)의 결정 단서 낱말이라 기억보다 먼저 보이면 안 된다
#  · '그늘'  : 서낭당·폐당집 같은 쉼터(동트기 피난처)를 가리키는 말이라 뜻이 겹친다
TIERS = [
    {
        "at": 10, "id": "stained_eye", "name": "물든 눈",
        "enter": "얼룩이 고일 자리가 먼저 보인다",
        "leave": "얼룩 자리가 다시 흐려진다",
        "does": "얼룩 셋이 겹칠 자리 · 거센 혼이 일어날 자리가 1초 먼저 보인다",
    },
    {
        "at": 30, "id": "linked_chain", "name": "잇단 사슬",
        "enter": "사슬이 곁의 혼까지 닿는다",
        "leave": "사슬이 다시 한 혼에만 닿는다",
        "hint": "파혼 뒤 [R] 곁의 혼도",
        "does": "파혼 직후 1초 안 4 m 안 다른 꿇은 혼에 R → 걸어가지 않고 깨뜨림(한 번에 하나씩)",
    },
    {
        "at": 60, "id": "lightless_path", "name": "빛 없는 길",
        "enter": "빛 없는 넋이 손에 남는다",
        "leave": "빛 없는 넋이 더는 오지 않는다",
        "does": "파혼한 혼 넋의 10%를 '빛 없는 넋'으로 받음(인 만들기에 2:1)",
    },
]

RULE = {
    "show": "칸에 들어설 때 한 번: 큰 글 칸 이름 1.0초 + 작은 줄 enter 2.0초(품계 인과 같은 자리 · 같은 크기, 겹치면 품계 인 뒤에 대기줄로). 소리는 품계와 다른 낮은 소리",
    "leave": "업 감쇠로 칸 아래로 내려가면 왼쪽 알림에 leave 한 줄만(가운데 연출 없음)",
    "hint": "잇단 사슬 hint는 칸에 처음 들어선 뒤 첫 파혼 때 한 번만, 처결 카드 자리 아래",
    "tone": "칭찬도 꾸중도 하지 않는다. 몸과 손에 생긴 일만 적는다. 칸 이름은 인물 창 업 줄 옆에 '업 34 · 잇단 사슬'처럼",
    "rain": "비 오는 밤(업 숨김)에는 들어섬 · 나옴 문구도 다음 맑은 밤 첫 처결까지 미룬다",
}

BANNED = ["흑월", "검은 갓", "그늘", "초혼", "동이", "춥", "추워", "추위", "한기", "으슬", "시왕", "염라",
          "재판", "형벌", "열두째", "여덟째", "횃불", "큰물", "벌", "죄", "잘", "좋", "훌륭", "강해", "힘이"]

def check():
    bad = []
    for t in TIERS:
        for k in ("name", "enter", "leave", "hint"):
            s = t.get(k)
            if not s:
                continue
            if len(s) > 22: bad.append(f"{t['at']} {k} 22자 넘음: {s}")
            if s.endswith("."): bad.append(f"{t['at']} {k} 마침표: {s}")
            for w in BANNED:
                if w in s: bad.append(f"{t['at']} {k} 금지어 '{w}': {s}")
            for c in s:
                try: c.encode("euc-kr")
                except UnicodeEncodeError: bad.append(f"{t['at']} {k} 글꼴 밖 글자 {c!r}")
    return bad

if __name__ == "__main__":
    bad = check()
    for b in bad: print("✗", b)
    if bad: sys.exit(1)
    out = os.path.join(os.path.dirname(__file__), "..", "docs", "narrative", "karma_tier_texts.json")
    json.dump({"_설명": "업 칸 이름 · 들어섬/나옴 한 줄. tools/karma_tier_texts.py로 생성. 서사 2026-10-26 (기획 karma-s1-check 2-3)",
               "rule": RULE, "tiers": TIERS}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("업 칸", len(TIERS), "개 → karma_tier_texts.json, 검사 통과")
