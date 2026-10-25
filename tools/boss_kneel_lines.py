# -*- coding: utf-8 -*-
"""보스가 무릎 꿇은 동안 압박 사이에 하는 한마디 → docs/narrative/boss_kneel_lines.json

왜: 기획 boss-final-moment-act1-2 · act3(10-26)이 '꿇은 동안 4~5초 간격의 약한 압박'을 넣었다.
천도(2초)는 압박 사이에 때를 맞춰야 들어간다. 그 '때'를 글자 경고 대신 보스 자신의 말로 알린다.
→ 말풍선이 뜨면 다음 압박까지 약 4초 = 지금 부르면 된다.
보스 말풍선은 보스당 3줄 상한(코디 10-25). 이미 3줄인 보스는 있는 줄을 다시 쓴다.
서사 2026-10-26
"""
import json, os, sys

KNEEL = [
 dict(boss="B-02", name="월화", existing=3, reuse=True, line="…열두째는 누구 몫이었더라.",
      when="꿇는 순간 한 번 + 잔 파동이 지나간 직후마다(다음 파동까지 약 4.5초)",
      why="엎어진 열두째 잔 칸이 늘 안전하다는 것을 말로 가리킨다(설화를 읽은 사람의 천도)"),
 dict(boss="B-03", name="서 의원", existing=2, line="잠깐… 그 사람 이름이.",
      when="번호 낙인 파동이 지나간 직후(다음 파동까지 4초)",
      why="번호만 부르던 의원이 이름에서 막히는 틈 = 파동이 멎는 틈"),
 dict(boss="B-05", name="기수 대돌", existing=0, line="번호는… 끝까지 서 있어라.",
      when="꿇는 순간 한 번(이름 불린 병사가 같이 무릎 꿇을 때)",
      why="서 있는 번호 병사(최대 2)만 치우면 천도가 안전하다는 것을 알린다"),
 dict(boss="B-06", name="이름 없는 장수", existing=0, line="빈자리는… 내 곁에 둬라.",
      when="마지막 호령 대형이 지나간 직후(다음 대형까지 4.5초)",
      why="대형의 빈칸이 늘 장수 2.8 m 안에 있다 — 거기서 부르면 된다"),
 dict(boss="B-07", name="갱도 칠성", existing=1, line="다 떨어졌다… 나와도 된다.",
      when="낙석 그림자 셋이 다 떨어진 직후(다음 낙석까지 4.5초)",
      why="광부를 부르던 목소리 그대로 — 지금이 안전한 틈"),
 dict(boss="B-08", name="장부꾼 염씨", existing=0, line="…이 장은 다 셌다.",
      when="숫자 종이 넉 장이 다 떨어진 직후(다음 넉 장까지 4.5초). 지뢰는 남는다",
      why="세기를 멈춘 사이 = 종이가 안 나는 틈"),
 dict(boss="B-09", name="망부석 아낙", existing=0, line="물 빠졌네… 아직 안 왔네.",
      when="파도 한 줄이 물러난 직후(다음 파도까지 4.5초)",
      why="기다리던 이가 안 온 물때 = 파도가 쉬는 틈"),
 dict(boss="B-10", name="만선호 선장", existing=3, reuse=True, line="줄 잡아라. 놓지 마라.",
      when="꿇은 동안 갑판이 기울기 시작할 때(미끄러짐 뒤 다음 기울기까지 약 4.5초)",
      why="이 말이 나오면 미끄러진다 — 멈추면 높은 쪽에 서서 부른다. 새 줄은 상한(3)이라 쓰지 않음"),
 dict(boss="B-11", name="다리 밑 왕초", existing=0, line="에이… 잠이나 자자.",
      when="거적을 던져 떨어진 직후(다음 거적까지 4.5초)",
      why="앉은 채 던지다 드러눕는 틈"),
]
SKIP = {
 "B-01": "나루 영감은 b01-naru-final-check(꿇은 뒤 5초 물 혼 두 번째 물결)이라 압박 사이 틈이 따로 없다. 말풍선 3줄 그대로",
 "B-04": "흑월 1차는 처결 없음",
 "B-12": "흑월 2차는 압박 없음(기획 예외) — 있는 한마디 '이번엔 내가 기억하마. 불러 보아라.'만",
}
RULE = {
 "show": "보스 머리 위 말풍선 1.5초(JudgeSystem.BossBubble). 화면 위 경고 글은 띄우지 않는다 — 말이 곧 신호",
 "count": "한 번 꿇을 때 최대 두 번(꿇는 순간 · 첫 압박 뒤). 같은 싸움에서 두 번째로 꿇으면 첫 압박 뒤 한 번만",
 "sound": "말풍선과 함께 그 보스 압박 소리의 끝(잦아드는 소리)을 한 번 — 소리만 듣고도 틈을 알게",
 "limit": "보스 말풍선 3줄 상한(코디 10-25). 새 줄을 더해도 보스마다 3줄 안",
}

BANNED = ["초혼", "동이", "춥", "추워", "추위", "한기", "으슬", "시왕", "염라", "재판", "형벌", "열두째는 너", "여덟째", "횃불", "큰물", "흑월", "검은 갓"]
ACT2 = ["서른일곱", "일곱", "위패", "열셋", "열넷", "반장", "앞장", "뒷장", "머릿수", "술 붓"]
ACT3 = ["만선호", "선장", "헛묘", "장부", "빗", "왕초", "서생", "방", "붓", "마흔", "일곱"]
ACT_OF = {"B-05": ACT2, "B-06": ACT2, "B-07": ACT2, "B-08": ACT2, "B-09": ACT3, "B-10": ACT3, "B-11": ACT3}


def check():
    bad = []
    for k in KNEEL:
        s = k["line"]
        if len(s) > 22: bad.append(f"{k['boss']} 22자 넘음")
        if not k.get("reuse") and k["existing"] + 1 > 3: bad.append(f"{k['boss']} 3줄 상한 넘음")
        for w in BANNED + ACT_OF.get(k["boss"], []):
            if w in s and not k.get("reuse"): bad.append(f"{k['boss']} 금지어 '{w}': {s}")
        for c in s:
            if c in "…": continue
            try: c.encode("euc-kr")
            except UnicodeEncodeError: bad.append(f"{k['boss']} 글꼴 밖 {c!r}")
    return bad


if __name__ == "__main__":
    bad = check()
    for b in bad: print("✗", b)
    if bad: sys.exit(1)
    out = os.path.join(os.path.dirname(__file__), "..", "docs", "narrative", "boss_kneel_lines.json")
    json.dump({"_설명": "보스가 꿇은 동안 압박 사이 한마디(천도할 때 신호). tools/boss_kneel_lines.py로 생성. 서사 2026-10-26 (기획 boss-final-moment-act1-2 · act3)",
               "rule": RULE, "kneel": KNEEL, "skip": SKIP}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("보스", len(KNEEL), "명 (새 줄", sum(1 for k in KNEEL if not k.get("reuse")), ", 다시 씀", sum(1 for k in KNEEL if k.get("reuse")), ") → boss_kneel_lines.json, 검사 통과")
