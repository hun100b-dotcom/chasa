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
      when="꿇는 순간 한 번 + 잔 파동 하나가 지나간 직후마다(다음 파동까지 약 4.5초)",
      why="엎어진 열두째 잔 칸이 늘 안전하다는 것을 말로 가리킨다(설화를 읽은 사람의 천도)"),
 dict(boss="B-03", name="서 의원", existing=2, line="잠깐… 그 사람 이름이.",
      when="번호 낙인 파동 하나가 지나간 직후(다음 파동까지 4초)",
      why="번호만 부르던 의원이 이름에서 막히는 틈 = 낙인 파동도 쉬는 틈"),
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
# ---- 시즌 2 (제안) ----------------------------------------------------------------
# 왜: 기획 s2-act1-rules-skim(10-26) S3 — 시즌 2 보스 8종에도 '꿇은 동안 약한 압박 하나'를 넣는다.
# 압박은 기획 s2-bosses-openworld "꿇은 동안의 약한 압박"(10-26)대로. 여기는 그 압박이 쉬는 틈을 알리는 한마디(그 보스 기억 결에서).
# 시즌 2 코드는 시즌 1을 PC로 끝까지 확인한 뒤라 status=제안(구현 때 그대로 쓰면 된다).
KNEEL_S2 = [
 dict(boss="B-13", name="줄의 맨 앞 노인", existing=0, line="…뒤에서 우는 소리가 그쳤소.",
      when="꿇는 순간 + 줄 파도 한 줄이 지나간 직후(다음 파도까지 4.5초, B13_KNEEL_WAVE_GAP)",
      why="기억 '뒤에 누가 울고 있었지'의 그림자. 우는 소리가 그친 사이 = 줄이 안 밀려오는 틈"),
 dict(boss="B-15", name="숫자를 처음 쓴 서리", existing=0, line="내 곁 한 칸은… 아직 비었다.",
      when="번호 칸 8칸이 사라진 직후(다음까지 4.5초, B15_KNEEL_CELL_GAP)",
      why="서리 둘레 2.8 m 안 칸 하나는 늘 안전 — 그것을 서리 자신이 알린다(B-06 '빈자리는 내 곁에'와 같은 틀). 단서 F35 낱말(잊지 않는 한)은 쓰지 않는다"),
 dict(boss="B-16", name="벼루지기", existing=0, line="먹이… 잠깐 가라앉는다.",
      when="소용돌이가 꺼지는 순간(꺼진 2.5초 = 시전 틈, B16_KNEEL_VORTEX_OFF)",
      why="소용돌이가 멎는 틈을 먹이 가라앉는 그림으로"),
 dict(boss="B-17", name="아홉째 문지기", existing=0, line="…눈이, 감긴다.",
      when="종 충격파 직후(다음 종까지 4.5초, B17_KNEEL_BELL_GAP)",
      why="천 년 감지 않은 눈이 감기는 것 = 종이 쉬는 틈. 싸움 중 졸음 패턴(2.0초)과 같은 결"),
 dict(boss="B-18", name="인을 훔친 혼", existing=0, line="또… 안 찍혔다.",
      when="검은 인 자리 2곳이 찍히고 사라진 직후(다음까지 4.5초, B18_KNEEL_SEAL_GAP)",
      why="기억 '찍었다. 안 찍혔다'의 되풀이. 인을 다 나눠 준 뒤 빈손인 틈"),
 dict(boss="B-19", name="첫 차사", existing=1, line="내 그늘에 들어서… 불러라.",
      when="꿇는 순간 + 새벽빛 1초가 지난 직후(B19_KNEEL_DAWN_GAP 4.5)",
      why="보스 뒤 그림자 2.8 m 안에서 시전하면 새벽빛에 안 끊긴다 — 새벽을 겪은 첫 차사가 자기 그늘을 내준다(기억 M-B19). 기존 1줄(B19-P30) + 1 = 2줄. C-20A는 천도 뒤 컷 대사라 따로"),
 dict(boss="B-20", name="큰 물막이", existing=0, line="…하나씩, 하나씩 불러 다오.",
      when="물살 띠가 지나간 직후마다(4.5초 간격, 대기 10초에 두 번. 눈금 300 이상이면 띠가 둘이어도 같은 줄)",
      why="수천의 목소리가 한목소리로 잦아드는 틈. 풀어내기(아는 이름 부르기)와 같은 뜻"),
]
SKIP_S2 = {
 "B-14": "돌아선 혼들의 덩어리는 천도 불가 — 천도 때를 알릴 말이 필요 없다",
}

# ---- 시즌 3 (제안) — 백은 말하지 않는다(season3_outline baek · 보스 lines 0) ----------------
# 그래서 틈을 알리는 것은 말풍선이 아니라 몸짓 하나 + 압박 소리의 끝. 화면 글 0줄.
# 압박은 기획 s3-act6-rules-skim Y3(10-26).
KNEEL_S3 = [
 dict(boss="B-21", name="윤 영감의 백", line=None,
      signal="뱃전을 쥔 손가락 하나가 풀렸다가 다시 쥔다",
      when="배가 쓸고 간 띠 한 줄이 지나간 직후(다음 띠까지 4.5초, B21_KNEEL_SWEEP_GAP)",
      why="'손을 놓으면 못 건넌다'는 한(han)이 잠깐 느슨해지는 틈 = 지금 부르면 손을 놓는다(3단계 '손을 놓다'와 같은 몸짓의 앞마디)"),
 dict(boss="B-22", name="줄에 묶인 일곱", line=None,
      signal="당겨졌던 줄이 한 번 늘어지고, 일곱이 고개를 같이 숙인다",
      when="줄 당김 직후(다음 당김까지 4.5초, B22_KNEEL_ROPE_GAP)",
      why="하나가 끌려가면 여섯이 당기는 줄 — 당김이 끝나 늘어진 때가 함께 부를 때. 줄을 끊지 않고 눕히는 결말(lay)과 같은 그림"),
]
# 7 · 8막(기획 s3-bosses-draft §5, 10-26). 틈마다 몸짓 하나 — 그 백의 한(han)이 잠깐 풀리는 그림
KNEEL_S3 += [
 dict(boss="B-24", name="한 구덩이의 두 진", line=None, signal="두 깃대가 같은 쪽으로 기운다",
      when="진 돌진 띠가 지나간 직후(B24_KNEEL_CHARGE_GAP 4.5)", why="'누가 우리 편인가' — 흙 속에선 편이 없다는 그림. 돌진이 쉬는 틈"),
 dict(boss="B-25", name="반장 칠성의 백", line=None, signal="흙 묻은 손이 손가락 하나를 접는다",
      when="흙 무너짐 원이 다 떨어진 직후(B25_KNEEL_DIRT_GAP 4.5)", why="세는 사람(칠성)의 몸짓. 하나를 셀 동안 흙이 쉰다. 1막 B-07 '다 떨어졌다'와 같은 자리"),
 dict(boss="B-26", name="역병 마흔과 마흔", line=None, signal="위 겹 손 하나가 아래 겹 손을 덮는다",
      when="아래 겹 손이 솟았다 들어간 직후(B26_KNEEL_HAND_GAP 4.5)", why="위는 미안하고 아래는 온기를 놓지 못한다(han) — 덮는 손이 아래 손을 잠깐 붙잡아 두는 틈"),
 dict(boss="B-27", name="서생 이명의 백", line=None, signal="붓끝이 마지막 줄 앞에서 멈춘다",
      when="붓 휘두르기가 지나간 직후마다(B27_KNEEL_BRUSH_GAP 4.5, 대기 10초에 두 번)", why="han '마지막 줄을 비워 두었다'의 멈춤. 이름 · 내력은 화면에 쓰지 않는다"),
 dict(boss="B-28", name="벼루지기의 백", line=None, signal="붓 모양 손이 반 줄을 쓰다 멈춘다",
      when="먹물 비가 그친 직후(B28_KNEEL_RAIN_GAP 4.5)", why="'시를 잊었다' — 반 줄에서 멈추는 몸. 시즌 2 B-16 '먹이 잠깐 가라앉는다'와 짝"),
 dict(boss="B-29", name="사잣밥 할미의 백", line=None, signal="할미가 밥상의 김을 손으로 덮는다",
      when="뜨거운 칸이 바뀐 직후(B29_KNEEL_HOT_GAP 4.5)", why="'밥이 식기 전에 차사가 와야 한다' — 식지 않게 덮는 동안이 부를 때"),
 dict(boss="B-30", name="어미의 백과 새끼줄", line=None, signal="우물 속 새끼줄이 한 번 느슨해진다",
      when="물줄기가 지나간 직후(B30_KNEEL_SPOUT_GAP 4.5)", why="2단계 '줄을 함께 붙잡고 버티기'의 끝 그림. 사공 연출과 겹치지 않게 줄만"),
]
SKIP_S3 = {"B-23": "물 밑 매듭은 3단계 배 받치기(버티기)가 압박 몫이라 따로 없음(기획 Y3)",
           "B-31": "나의 백은 결말이라 압박 없음(기획 G1, 흑월 2차와 같은 까닭) — 서사 찬성: 결말의 무게는 손이 아니라 이야기"}

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
    for k in KNEEL + KNEEL_S2:
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
               "rule": RULE, "kneel": KNEEL, "skip": SKIP,
               "kneel_s2": {"status": "제안 — 시즌 2 코드 전. 압박은 기획 s2-bosses-openworld 꿇은 동안의 약한 압박(10-26)", "lines": KNEEL_S2, "skip": SKIP_S2},
               "kneel_s3": {"status": "제안 — 시즌 3 코드 전. 백은 말하지 않아 말풍선 대신 몸짓(signal) + 압박 소리의 끝", "lines": KNEEL_S3, "skip": SKIP_S3}}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("시즌2 제안", len(KNEEL_S2), "명 /", "보스", len(KNEEL), "명 (새 줄", sum(1 for k in KNEEL if not k.get("reuse")), ", 다시 씀", sum(1 for k in KNEEL if k.get("reuse")), ") → boss_kneel_lines.json, 검사 통과")
