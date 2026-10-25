#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《차사》 소설 장 점검기.

왜 만들었나:
  지난 원고에는 오타, 반복 구문("시야가 돌아왔다" 등), 본문 속 게임 메모가 많았다.
  사람 눈으로만 고르면 놓치므로, 장을 하나 쓸 때마다 이 스크립트로 기계적인 실수를 먼저 거른다.
  (문장의 맛은 사람이 본다. 이 도구는 '틀린 것'과 '너무 자주 나오는 꼴'만 찾는다.)
  2026-10-25 중간 점검 뒤로는 'AI 티'로 읽히던 문장 버릇(부정-정정, 명사 끝맺음, 셋 맞춤,
  풀어 말하기, 장마다 되풀이되던 구절)과 긴 문장 비율·대화 문단 수도 센다.
  1~20장은 아직 이 기준 이전에 쓴 원고라 버릇 오류가 나온다 — 퇴고 때 고칠 목록으로 쓴다.
  2026-10-25 오너 지적 두 번으로 '문장 끝'(~다 ~다 ~다)과 '문장 흐름'(뚝뚝 끊김)도 센다.

쓰는 법:
  python3 check_chapter.py 장파일.md [장파일2.md ...]
  여러 파일을 주면 파일별 결과 + 부(part)별 합계(반복 구문 상한은 부 하나 전체 기준)를 함께 보여 준다.
  파일 경로에 part2가 들어 있으면 2부 규칙(아직 나오면 안 되는 말 목록)을 쓴다. 그 밖에는 1부 규칙.
"""

import difflib
import json
import os
import re
import sys

# 이 스크립트와 같은 폴더의 원문 목록(기억 한 줄, 정해진 대사)을 읽는다.
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "canon_lines.json"), encoding="utf-8") as f:
    CANON = json.load(f)

# 원문 기억 한 줄 전부(이름혼 + 이름 없는 혼 공용 줄)
CANON_MEMORIES = [v["line"] for v in CANON["memories"].values()] + CANON["generic"]

# 본문에 나오면 안 되는 게임 용어(소설은 게임 설명서가 아니다)
GAME_TERMS = [
    "HP", "캐스팅", "쿨타임", "스폰", "보스", "튜토리얼", "퀘스트", "레벨업", "처결 대기",
    "넉백", "시야 60", "1.5초", "2.0초", "업 +", "구역", "허브", "플레이어", "도감", "추리판",
    "게임 대응", "맺힘 수치", "대미지", "버프", "디버프",
]

# 시대에 맞지 않는 말(조선풍 산골에 시계·미터는 없다)
ANACHRONISM = ["분 동안", "초 동안", "미터", "킬로", "퍼센트", "%", "시계", "분 뒤", "초 뒤"]

# 지난 원고에서 실제로 나온 오타(왼쪽이 틀린 말). 새로 찾으면 여기에 더한다.
TYPOS = {
    "눈앞이 좋아": "눈앞이 좁아", "좋아진 시야": "좁아진 시야", "좋아진 땅": "좁아진 땅",
    "곡 배꼴": "곽 뱃꾼", "어젤밤": "어젯밤", "쉬터": "쉼터", "몽쳐": "뭉쳐", "몰 번": "몇 번",
    "셀이 되면": "셋이 되면", "중터에": "중턱에", "뒤모습": "뒷모습", "끼와 대패": "끌과 대패",
    "깎어": "깎아", "탑백": "대팻밥", "구다리": "고리짝", "천에 쌓다": "천에 쌌다",
    "장구를 쳐다": "장구를 쳤다", "팔팽": "팽팽", "좀아지": "좁아지", "하얗었다": "하얬다",
    "이생에서": "이승에서", "부뚯막": "부뚜막", "그어내기": "긋기", "불실하게": "(삭제)",
}

# 반복되면 문장이 늘어지는 구문과 1부 전체 상한(SKILL.md §3·§6)
REPEAT_LIMITS = {
    "시야가 돌아왔다": 2,
    "말은 거기서 끊겼다": 1,
    "그냥 알았다": 1,
    "알고 있었다는 듯이": 1,
    "입속에서 굴려": 1,
    "오래 보았다": 4,
    "알 수 없었다": 4,
    "처음으로": 8,
    "아무것도 없었다": 3,
    # 2부(15~17장)를 쓰며 한 번씩 써 버린 그림. 같은 부에서 또 나오면 공식처럼 읽힌다.
    "감겨 들며": 2,
    "젖은, 동그란": 1,
    "등 뒤는 어둠이었다": 1,
    "돌아볼 수 없었다": 2,
}

# 감정 이름(몸과 사물로 보여 주어야 한다). 장 하나에 2개까지 봐준다.
EMOTION_WORDS = [
    "슬펐", "슬픔이", "두려웠", "무서웠", "안도했", "안도가", "부끄러웠", "부끄러움",
    "외로웠", "외로움", "기뻤", "행복했", "화가 났", "분노가", "죄책감", "서글펐",
]

# 번역투 표지(남발 금지). 숫자는 장 하나 상한.
TRANSLATIONESE = {"에 의해": 0, "을 가지고 있었다": 0, "를 가지고 있었다": 0, "하는 중이었다": 1,
                  "하기 시작했다": 3, "마치 ": 3}

# ── 문장 버릇(2026-10-25 중간 점검) ─────────────────────────────────────────
# 왜: 1~20장을 세어 보니 문장 하나하나는 괜찮은데 같은 '꼴'이 장마다 쌓여
#     기계가 쓴 리듬(AI 티)으로 읽혔다. 꼴마다 장 하나에 쓸 수 있는 개수를 정해 둔다.
#     (1~20장 평균: 부정-정정 약 9번, 명사 끝맺음 약 13번 → 절반 아래로)
STYLE_LIMITS = {
    # "A가 아니라 B", "A가 아니었다. B였다" — 아니라고 한 뒤 고쳐 말하는 버릇
    "부정-정정": (r"(?:이|가) 아니라|아니었다\.", 4),
    # "무엇을 세는 손이었다." 처럼 행동을 명사 하나로 묶어 정리하는 버릇
    "명사 끝맺음": (r"[가-힣]+ (?:손|발|자리|소리|냄새|얼굴|등|눈|빛|사람|몸|목소리|길|날|밤|물)(?:이었다|였다)\.", 6),
}
# 장을 넘어 되풀이되던 구절(1~20장에서 13~16개 장에 나옴). 장 하나 상한.
PER_CHAPTER_LIMITS = {"얼굴이 돌아왔다": 1, "그의 혼불로 왔다": 1, "한 번 더": 2, "숨 한 번": 2,
                      "그는 사슬을 냈다": 1, "오히려": 1}
# 보여 준 뒤 뜻을 풀어 말하는 문장(독자가 스스로 알아챌 몫을 빼앗는다). 경고만.
EXPLAIN_PATTERNS = [r"다는 것은 [^.\n]{0,30}(?:것|뜻)이었다", r"(?:이번이|그것이) 처음이었다", r"그래도 알았다"]
LONG_SENT = 30            # 이보다 긴 문장(띄어쓰기 포함 글자 수)을 '긴 문장'으로 센다
LONG_SHARE_MIN = 0.25     # 긴 문장이 이 비율보다 적으면 리듬이 한 가지로 굳는다(1~20장은 7.9%)
                          # 2026-10-25 04:14 오너 지적("~다 ~다 ~다") 뒤 15% → 25%로 올림

# ── 문장 끝 리듬(2026-10-25 04:14 KST 오너 지적: "~다 ~다 ~다 이게 뭐냐") ───────────────
# 왜: 1·2부 서술 문장의 85%가 '~다'로 끝났고(프롤로그 96%), 같은 끝이 최장 51문장 연달아 섰다.
#     그런데도 점검기는 문장 끝을 한 번도 세지 않았다. 그래서 이제 센다.
# 한국어 과거 서술이 '~다'로 끝나는 것 자체는 자연스럽다. 귀에 걸리는 것은
#     (1) 같은 '꼴'(예: ~었다.)이 비슷한 길이로 줄지어 서는 것,
#     (2) 꼴이 달라도 '~다'만 길게 이어지는 것이다.
#     그래서 끝 모양을 꼴(아래 ending_form)로 나눠 (1)을 오류로, (2)를 길이 기준으로 잡는다.
# 고치는 법(SKILL.md §3-1): 어미 앞부분 바꾸기(었다/ㄴ다/있었다/것이었다/터였다),
#     체언·부사로 끊기, 도치, 문장 길이 크게 바꾸기, 쉼표·연결 어미로 잇기, 대화 넣기.
#     '~했지.' '~인가.' 같은 어색한 어미를 숫자 맞추려고 넣지 않는다(목표는 리듬).
FORM_RUN_MAX = 2          # 같은 꼴은 두 번까지만 연달아. 셋째부터 오류 —
FORM_RUN_LONG_AVG = 40    # 단, 그 세 문장이 평균 40자 이상으로 길면 봐준다(긴 문장의 끝은 귀에 덜 걸린다)
FORM_RUN_HARD = 3         # 넷째부터는 길이와 상관없이 오류
                          # 왜(2026-10-25 10:32): 짧은 문장에서는 끝이 바로 귀에 박혀 '~었다. ~었다.'로 들리지만,
                          #     마흔 자 넘게 흐르는 문장 셋은 끝보다 내용이 먼저 들린다. 짧은 셋만 막아야
                          #     끝을 바꾸려고 문장을 끊는 일(뚝뚝 끊김)이 생기지 않는다.
DA_RUN_MAX = 4            # '~다'(꼴 무관)가 다섯 문장 이상 연달아 서는데
DA_RUN_SHORT_AVG = 30     # 그 다섯 문장의 평균 길이가 이보다 짧으면 오류('짧은 ~다'가 줄 선 것)
                          # 왜(2026-10-25 10:32 고침): 처음에는 '~다' 다섯 문장 연속을 길이와 상관없이 막았다.
                          #     그랬더니 연속을 끊으려고 조각 문장을 끼워 넣어 글이 뚝뚝 끊겼다(오너 두 번째 지적).
                          #     40자 넘는 문장 다섯이 '~다'로 끝나는 것은 보통 소설의 숨이다. 귀에 걸리는 것은
                          #     짧은 '~다'가 줄지어 서는 것이므로, 연속은 길이와 함께 본다.
DA_PER_1000_WARN = 30     # 서술 1천 자에 '~다' 끝이 이보다 많으면 경고(귀에 '~다'가 들리는 잦기)
                          # 왜(2026-10-25 10:32 바꿈): 전에는 '~다' 비율(%)로 봤는데, 비율을 낮추려면 조각 문장을
                          #     늘려야 해서 글이 끊겼다. 귀에 걸리는 것은 비율이 아니라 '얼마나 자주' 들리느냐다.
                          #     옛 1장 48번(문장이 짧아서), 새 1장 20번대. 문장을 이으면 자연히 준다.

# ── 문장 흐름(2026-10-25 10:32 KST 오너 지적: "문장이 뚝뚝 끊기는 느낌") ───────────────
# 왜: '~다'를 피하려고 조각 문장("챙 넓은 검은 갓.")과 짧은 문장을 늘렸더니 이번에는 글이 끊겼다.
#     새로 쓴 1장: 서술 문장의 26%가 조각, 23%가 15자 이하, 한 문장짜리 문단 30개.
#     해법은 끝을 바꾸는 것이 아니라 문장을 잇는 것이다(이음말·긴 문장·대화. SKILL §3-2).
SHORT_SENT = 15           # 이 길이 이하(띄어쓰기 포함)를 '짧은 문장'으로 센다
SHORT_RUN_MAX = 2         # 짧은 문장은 두 개까지만 연달아. 셋째부터 오류
SHORT_SHARE_MAX = 0.15    # 짧은 문장이 서술 문장의 15%를 넘으면 오류
FRAG_SHARE_WARN = 0.12    # 조각 문장('~다'로 안 끝나는 서술: 체언·부사구·도치·물음)이 12%를 넘으면 경고
FRAG_SHARE_MAX = 0.18     # 18%를 넘으면 오류(이음말로 앞뒤 문장에 붙인다)
AVG_SENT_MIN = 30         # 서술 문장 평균 길이가 이보다 짧으면 오류(1~20장 평균 17자, 새 1장 첫 판 32자)
ONE_LINE_PARA_WARN = 12   # 한 문장짜리 서술 문단이 이보다 많으면 경고(장면을 끊는 한 줄은 아껴 쓴다)


def ending_form(sentence: str) -> str:
    """문장 끝 '꼴'을 고른다. 귀에 같은 소리로 들리는 끝끼리 한 꼴로 묶는다.
    - '다 아님'      : 체언·부사·도치·물음·말줄임·소리말 따위로 끝남
    - '있었다/없었다' : 있음·없음의 과거(있었다, 없었다, 남아 있었다…)
    - '~이었다'      : 체언+지정 과거(것이었다, 터였다, 뿐이었다, 갓이었다…)
    - '~었다'        : 그 밖의 과거(갔다, 보았다, 내려앉았다, 않았다…) — 받침 ㅆ 바로 뒤 '다'
    - '~ㄴ다'        : 현재(간다, 본다, 먹는다)
    - '~이다'        : 체언+지정 현재(것이다, 때문이다)
    - '~다(그 밖)'    : 형용사·있다류 현재(차갑다, 같다, 있다, 없다)"""
    t = re.sub(r"[\s\"”’'」』)\]]+$", "", sentence)
    t = re.sub(r"[.?!…~]+$", "", t)
    if not t.endswith("다"):
        return "다 아님"
    last = t.split()[-1] if t.split() else t
    if re.search(r"(?:있|없)었다$", last):
        return "있었다/없었다"
    if re.search(r"(?:이었다|것이었다|터였다|뿐이었다|셈이었다|참이었다|때였다|무렵이었다)$", last):
        return "~이었다"
    if re.search(r"(?:있다|없다|겠다)$", last):
        return "~다(그 밖)"
    if re.search(r"이다$", last):
        return "~이다"
    prev = t[-2] if len(t) >= 2 else ""
    if "가" <= prev <= "힣":
        jong = (ord(prev) - 0xAC00) % 28
        if jong == 20:            # 받침 ㅆ → 과거
            return "~었다"
        if jong == 4 or prev == "는":   # 받침 ㄴ 또는 '는' → 현재 동사
            return "~ㄴ다"
    return "~다(그 밖)"


def narration_flow(text: str):
    """읽는 순서대로 (종류, 문장)을 늘어놓는다. 대화 문단·쪽지·장면 구분은 흐름을 끊는 표지로 넣는다.
    문단이 바뀌어도 서술이 이어지면 귀에는 이어서 들리므로 끊지 않는다."""
    out = []
    for para in re.split(r"\n\s*\n", text):
        p = para.strip()
        if not p or p.startswith("#"):
            continue
        if p.startswith("---"):
            out.append(("끊김", ""))
            continue
        if p.startswith(">"):
            out.append(("쪽지", p))
            continue
        if p[0] in "\"“'‘「":
            out.append(("대화", p))
            continue
        p = p.replace("*", "")
        for s in re.split(r"(?<=[.?!…])\s+", p):
            s = s.strip()
            if s:
                out.append(("서술", s))
    return out


def form_run_hit(form_seq) -> bool:
    """같은 꼴로 이어진 문장들(form_seq, 마지막이 지금 문장)이 걸리는지.
    셋째는 세 문장 평균이 FORM_RUN_LONG_AVG보다 짧을 때만, 넷째부터는 언제나 걸린다."""
    n = len(form_seq)
    if n <= FORM_RUN_MAX:
        return False
    if n > FORM_RUN_HARD:
        return True
    last = form_seq[-(FORM_RUN_MAX + 1):]
    return sum(len(x) for x in last) / len(last) < FORM_RUN_LONG_AVG


def ending_rhythm(text: str) -> dict:
    """같은 꼴 3연속 자리, '~다' 최장 연속, '~다' 비율을 센다."""
    flow = narration_flow(text)
    nar = [s for k, s in flow if k == "서술"]
    da = [s for s in nar if ending_form(s) != "다 아님"]
    form_hits, da_hits = [], []
    prev_form, form_seq, da_max = None, [], 0
    da_seq, da_hit_this_run = [], False   # 지금 이어지는 '~다' 문장들, 이 연속에서 이미 걸렸는지
    for kind, s in flow:
        if kind != "서술":
            prev_form, form_seq, da_seq, da_hit_this_run = None, [], [], False
            continue
        f = ending_form(s)
        form_seq = form_seq + [s] if f == prev_form else [s]   # 지금 이어지는 같은 꼴 문장들
        prev_form = f
        if f != "다 아님" and form_run_hit(form_seq):
            form_hits.append(f"[{f}] …{s[-24:]}")
        if f != "다 아님":
            da_seq.append(s)
        else:
            da_seq, da_hit_this_run = [], False
        da_max = max(da_max, len(da_seq))
        # 다섯 문장째부터: 마지막 다섯의 평균 길이가 짧으면 한 연속에 한 번만 오류로 센다
        if len(da_seq) > DA_RUN_MAX and not da_hit_this_run:
            last = da_seq[-(DA_RUN_MAX + 1):]
            if sum(len(x) for x in last) / len(last) < DA_RUN_SHORT_AVG:
                da_hits.append(f"…{s[-24:]}")
                da_hit_this_run = True
    nar_chars = sum(len(x) for x in nar)
    return {"서술 문장": len(nar), "~다 비율": len(da) / max(1, len(nar)), "~다 최장 연속": da_max,
            "1천 자당 ~다": len(da) * 1000 / max(1, nar_chars),
            "같은 꼴 3연속": form_hits, "~다 5연속": da_hits}


def sentence_flow(text: str) -> dict:
    """문장 흐름(뚝뚝 끊김)을 잰다: 서술 문장 평균 길이, 짧은 문장 비율과 3연속, 조각 비율, 한 줄 문단.
    짧은 문장 연속은 대화·쪽지·장면 구분에서 새로 센다(문단이 바뀌어도 서술이 이어지면 이어서 센다)."""
    flow = narration_flow(text)
    nar = [s for k, s in flow if k == "서술"]
    if not nar:
        return {"평균 길이": 0, "짧은 비율": 0.0, "짧은 3연속": [], "조각 비율": 0.0, "한 줄 문단": []}
    short_hits, run = [], []
    for kind, s in flow:
        if kind == "서술" and len(s) <= SHORT_SENT:
            run.append(s)
            if len(run) == SHORT_RUN_MAX + 1:
                short_hits.append(" / ".join(run))
        else:
            run = []
    one_line = []
    paras = [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip() and not x.strip().startswith("#")]
    is_dlg = [p[0] in "\"“'‘「" for p in paras]
    for i, p in enumerate(paras):
        if p.startswith(("---", ">")) or is_dlg[i]:
            continue
        # 대화 바로 앞뒤의 한 줄은 말하는 사람의 몸짓·말머리라 따로 서는 것이 자연스럽다 → 세지 않는다
        if (i > 0 and is_dlg[i - 1]) or (i + 1 < len(paras) and is_dlg[i + 1]):
            continue
        ss = [x for x in re.split(r"(?<=[.?!…])\s+", p.replace("*", "")) if x.strip()]
        if len(ss) == 1:
            one_line.append(ss[0])
    return {
        "평균 길이": sum(len(s) for s in nar) / len(nar),
        "짧은 비율": sum(1 for s in nar if len(s) <= SHORT_SENT) / len(nar),
        "짧은 3연속": short_hits,
        "조각 비율": sum(1 for s in nar if ending_form(s) == "다 아님") / len(nar),
        "한 줄 문단": one_line,
    }



def sentence_marks(text: str):
    """확인 페이지용: 서술 문장마다 {'form': 꼴, 'hit': 걸림}을 읽는 순서대로 돌려준다.
    걸림 = 같은 꼴 연속(form_run_hit) · 짧은 '~다' 다섯 연속 · 짧은 문장 세 연속에 든 문장.
    점검기와 같은 판정을 쓰려고 여기 둔다(페이지가 따로 세면 둘이 어긋난다)."""
    texts, marks = [], []
    prev_form, form_seq, da_idx, short_idx = None, [], [], []
    for kind, s in narration_flow(text):
        if kind != "서술":
            prev_form, form_seq, da_idx, short_idx = None, [], [], []
            continue
        i = len(texts)
        texts.append(s)
        f = ending_form(s)
        marks.append({"form": f, "hit": False})
        form_seq = form_seq + [s] if f == prev_form else [s]
        prev_form = f
        if f != "다 아님" and form_run_hit(form_seq):
            marks[i]["hit"] = True
        da_idx = da_idx + [i] if f != "다 아님" else []
        if len(da_idx) > DA_RUN_MAX:
            last = da_idx[-(DA_RUN_MAX + 1):]
            if sum(len(texts[j]) for j in last) / len(last) < DA_RUN_SHORT_AVG:
                for j in last:
                    marks[j]["hit"] = True
        short_idx = short_idx + [i] if len(s) <= SHORT_SENT else []
        if len(short_idx) > SHORT_RUN_MAX:
            for j in short_idx[-(SHORT_RUN_MAX + 1):]:
                marks[j]["hit"] = True
    return marks


DIALOGUE_MIN = 8          # 따옴표로 시작하는 문단(산 사람의 말) 최소. 혼자만 나오는 장이면 경고를 무시해도 된다


def sentences(text: str):
    """본문을 문장 단위로 자른다(쪽지 인용 '>' 줄과 기울임 별표는 뺀다)."""
    out = []
    for para in text.splitlines():
        para = para.strip()
        if not para or para == "---" or para.startswith("#") or para.startswith(">"):
            continue
        para = para.replace("*", "")
        for s in re.split(r"(?<=[.?!…])\s+|(?<=[.?!][\"”’])\s+", para):
            s = s.strip()
            if s:
                out.append(s)
    return out


def triads(text: str):
    """같은 꼴 문장 셋이 나란히 선 곳을 찾는다(셋 맞춤).
    기준: 한 문단 안에서 이웃한 세 문장의 마지막 어절이 같고(예: '들었다.'),
    세 문장 모두 앞쪽에 '~은/는/에는' 같은 주제 표지가 있다."""
    found = []
    for para in text.splitlines():
        para = para.strip()
        if not para or para.startswith((">", "#", "---")):
            continue
        ss = [s.strip() for s in re.split(r"(?<=[.?!])\s+", para.replace("*", "")) if s.strip()]
        for i in range(len(ss) - 2):
            three = ss[i:i + 3]
            tails = {s.split()[-1] for s in three}
            if len(tails) != 1 or next(iter(tails)) in ("있었다.", "없었다.", "않았다."):
                continue
            if all(re.search(r"[가-힣](?:은|는|에는|에게는) ", s[: max(8, len(s) // 2)]) for s in three):
                found.append(" / ".join(x[:18] + "…" for x in three))
    return found


# 오감 어림 지표(정확하지 않다. 0이면 그 감각을 잊었다는 신호로만 본다)
SENSE = {
    "소리": ["소리", "울렸", "울렸다", "들렸", "삐걱", "철썩", "사락", "쨍", "웅얼", "메아리", "요령"],
    "냄새": ["냄새", "내음", "비린", "향내", "쇳내", "탄내", "누린", "김이 올랐"],
    "촉감": ["차가", "차갑", "축축", "서늘", "젖은", "감촉", "닿았", "까끌", "미끄러", "무게"],
}


def strip_md(text: str) -> str:
    """제목·인용 표시 같은 마크다운 기호를 빼고 순수 본문만 남긴다(분량 계산용)."""
    lines = []
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        lines.append(re.sub(r"^[>\-\*\s]+", "", line))
    return "\n".join(lines)


def part_of(path: str) -> str:
    """파일 경로로 몇 부 원고인지 고른다(docs/novel/part2/... → 'part2'). 모르면 1부로 본다."""
    m = re.search(r"part(\d+)", path.replace("\\", "/"))
    return f"part{m.group(1)}" if m else "part1"


def not_yet_lines(part: str):
    """그 부에서 아직 나오면 안 되는 말 목록. 예전 파일 형식(not_in_part1)도 읽는다."""
    table = CANON.get("not_yet")
    if table:
        return table.get(part, table.get("part1", []))
    return CANON.get("not_in_part1", [])


def check_file(path: str) -> dict:
    """장 파일 하나를 점검해 결과를 사전으로 돌려준다."""
    text = open(path, encoding="utf-8").read()
    part = part_of(path)
    body = strip_md(text)
    res = {"file": os.path.basename(path), "part": part, "errors": [], "warnings": [], "counts": {}}

    # 1) 분량: 공백 포함 글자 수와 공백 뺀 글자 수
    res["counts"]["글자(공백 포함)"] = len(body.replace("\n", ""))
    res["counts"]["글자(공백 제외)"] = len(re.sub(r"\s", "", body))

    # 2) 기울임 문장 = 기억 한 줄. 원문과 한 글자라도 다르면 오류
    italics = re.findall(r"(?<!\*)\*([^*\n]+)\*(?!\*)", text)
    for it in italics:
        s = it.strip()
        if s in CANON_MEMORIES:
            continue
        best = difflib.get_close_matches(s, CANON_MEMORIES, n=1, cutoff=0.55)
        if best:
            res["errors"].append(f"기억 한 줄이 원문과 다름:\n      쓴 것: {s}\n      원문 : {best[0]}")
        else:
            res["warnings"].append(f"원문 목록에 없는 기울임(강조라면 괜찮다): {s[:40]}")

    # 3) 게임 용어·시대착오·오타
    for w in GAME_TERMS:
        if w in text:
            res["errors"].append(f"게임 용어: '{w}' ×{text.count(w)}")
    for w in ANACHRONISM:
        if w in body:
            res["warnings"].append(f"시대에 안 맞을 수 있는 말: '{w}' ×{body.count(w)}")
    for wrong, right in TYPOS.items():
        if wrong in text:
            res["errors"].append(f"오타: '{wrong}' → '{right}'")

    # 4) 이 부에 아직 나오면 안 되는 대사(흑월 대사·뒤 시즌 쪽지 등)
    for w in not_yet_lines(part):
        if w in text:
            res["errors"].append(f"{part[-1]}부에 아직 나오면 안 되는 말: '{w}'")
    # 4-0) 흑월의 본명은 시즌 1·2 원고에 쓰지 않는다(서사팀 확정). '이명'이 낱말로 보이면 알린다.
    for m in re.finditer(r"(?<![가-힣])이명(?![가-힣])", body):
        around = body[max(0, m.start() - 6): m.end() + 6].replace("\n", " ")
        res["warnings"].append(f"'이명'이 보인다(흑월 본명 누설인지 확인): …{around}…")

    # 4-1) 주인공 이름 보호: '동이'는 "동이 트다" 꼴로만 써야 한다(결말 장치).
    #      "동이야", "동이는", "동이가" 처럼 사람 이름으로 쓰인 곳을 찾는다.
    #      앞 글자가 한글이면 다른 낱말의 일부다(예: "밑동이", "물동이") → 이름이 아니므로 건너뛴다.
    for m in re.finditer(r"(?<![가-힣])동이(?!\s?(트|튼|텄|틀|터|트기|트는|트던|트면|트자|트려|터 오|터오))", body):
        around = body[max(0, m.start() - 6): m.end() + 6].replace("\n", " ")
        res["errors"].append(f"'동이'가 '동이 트다' 꼴이 아닌 곳(이름 누설 위험): …{around}…")

    # 5) 반복 구문·감정 이름·번역투 세기
    res["counts"]["반복"] = {k: body.count(k) for k in REPEAT_LIMITS if body.count(k)}
    emo = {w: body.count(w) for w in EMOTION_WORDS if body.count(w)}
    res["counts"]["감정 이름"] = emo
    if sum(emo.values()) > 2:
        res["warnings"].append(f"감정 이름이 많다({sum(emo.values())}개): {emo}")
    for w, lim in TRANSLATIONESE.items():
        c = body.count(w)
        if c > lim:
            res["warnings"].append(f"번역투/남발: '{w.strip()}' ×{c} (상한 {lim})")

    # 6) 오감 어림
    res["counts"]["오감"] = {k: sum(body.count(w) for w in ws) for k, ws in SENSE.items()}
    for k, v in res["counts"]["오감"].items():
        if v < 2:
            res["warnings"].append(f"{k} 감각이 거의 없다({v})")

    # 7) '그녀'는 되도록 쓰지 않는다
    c = body.count("그녀")
    if c > 3:
        res["warnings"].append(f"'그녀' ×{c} — 당할미·아낙·아이·이름으로 바꿀 수 있나")

    # 8) 문장 버릇(AI 티). 상한을 넘으면 오류 — 고쳐 쓴 뒤 다시 돌린다.
    style = {}
    for name, (pat, lim) in STYLE_LIMITS.items():
        n = len(re.findall(pat, body))
        style[name] = n
        if n > lim:
            res["errors"].append(f"문장 버릇 '{name}' ×{n} (장 하나 상한 {lim})")
    for ph, lim in PER_CHAPTER_LIMITS.items():
        n = body.count(ph)
        if n > lim:
            res["errors"].append(f"장마다 되풀이되던 구절 '{ph}' ×{n} (장 하나 상한 {lim})")
    tri = triads(text)
    style["셋 맞춤"] = len(tri)
    if len(tri) > 1:
        res["warnings"].append(f"같은 꼴 문장 셋 나란히 ×{len(tri)} — 가장 센 하나만 남길 수 있나: {tri[:2]}")
    for pat in EXPLAIN_PATTERNS:
        for m in re.finditer(pat, body):
            res["warnings"].append(f"보여 준 뒤 풀어 말하기?: …{body[max(0, m.start() - 10): m.end()]}…")
    ss = sentences(text)
    if ss:
        long_share = sum(1 for s in ss if len(s) > LONG_SENT) / len(ss)
        style["긴 문장 비율"] = f"{long_share:.0%}"
        if long_share < LONG_SHARE_MIN:
            res["errors"].append(f"{LONG_SENT}자 넘는 문장이 {long_share:.0%} — {LONG_SHARE_MIN:.0%} 이상이어야 리듬이 산다"
                                 "(물·기억·행렬·장례 장면을 길게 흐르게)")
    dlg = sum(1 for line in text.splitlines() if line.strip().startswith(("\"", "“")))
    style["대화 문단"] = dlg
    if dlg < DIALOGUE_MIN:
        res["warnings"].append(f"대화 문단 {dlg}개 — 산 사람의 말이 {DIALOGUE_MIN}문단은 있어야 책이 숨을 쉰다(혼자만 나오는 장이면 무시)")
    res["counts"]["문장 버릇"] = style

    # 9) 문장 끝 리듬(2026-10-25 오너 지적). 같은 꼴 연속·짧은 '~다' 5연속은 오류, 1천 자당 '~다'는 경고.
    rh = ending_rhythm(text)
    res["counts"]["문장 끝"] = {"서술 문장": rh["서술 문장"], "~다 비율": f"{rh['~다 비율']:.0%}",
                             "1천 자당 ~다": round(rh["1천 자당 ~다"], 1),
                             "~다 최장 연속": rh["~다 최장 연속"], "같은 꼴 연속": len(rh["같은 꼴 3연속"]),
                             "짧은 ~다 5연속": len(rh["~다 5연속"])}
    if rh["같은 꼴 3연속"]:
        res["errors"].append(f"같은 꼴 문장 끝이 연달아 ×{len(rh['같은 꼴 3연속'])}"
                             f"(짧은 셋은 평균 {FORM_RUN_LONG_AVG}자 미만, 넷은 길이와 상관없이 — 두 문장을 잇거나 끝을 바꾼다): "
                             f"{rh['같은 꼴 3연속'][:4]}")
    if rh["~다 5연속"]:
        res["errors"].append(f"짧은 '~다' 문장이 다섯 이상 줄지어 섬(평균 {DA_RUN_SHORT_AVG}자 미만) ×{len(rh['~다 5연속'])}"
                             f"(두 문장을 이음말로 잇거나 대화를 넣는다. 조각 문장으로 끊지 않는다): {rh['~다 5연속'][:4]}")
    if rh["1천 자당 ~다"] > DA_PER_1000_WARN:
        res["warnings"].append(f"서술 1천 자에 '~다' 끝이 {rh['1천 자당 ~다']:.0f}번 — {DA_PER_1000_WARN}번 아래로"
                               "(끝을 바꾸려 끊지 말고 두 문장을 이어 문장 수를 줄인다)")

    # 10) 문장 흐름(2026-10-25 10:32 오너 지적: "문장이 뚝뚝 끊기는 느낌"). SKILL §3-2.
    fl = sentence_flow(text)
    res["counts"]["문장 흐름"] = {"평균 길이": f"{fl['평균 길이']:.0f}자", "짧은 문장": f"{fl['짧은 비율']:.0%}",
                               "짧은 3연속": len(fl["짧은 3연속"]), "조각": f"{fl['조각 비율']:.0%}",
                               "한 줄 문단": len(fl["한 줄 문단"])}
    if fl["평균 길이"] and fl["평균 길이"] < AVG_SENT_MIN:
        res["errors"].append(f"서술 문장 평균 {fl['평균 길이']:.0f}자 — {AVG_SENT_MIN}자 이상이어야 글이 이어져 읽힌다")
    if fl["짧은 3연속"]:
        res["errors"].append(f"짧은 문장({SHORT_SENT}자 이하)이 세 번 연달아 ×{len(fl['짧은 3연속'])}"
                             f"(둘을 한 문장으로 잇는다): {fl['짧은 3연속'][:3]}")
    if fl["짧은 비율"] > SHORT_SHARE_MAX:
        res["errors"].append(f"짧은 문장({SHORT_SENT}자 이하)이 서술의 {fl['짧은 비율']:.0%} — {SHORT_SHARE_MAX:.0%} 아래로")
    if fl["조각 비율"] > FRAG_SHARE_MAX:
        res["errors"].append(f"조각 문장('~다'로 안 끝나는 서술)이 {fl['조각 비율']:.0%} — {FRAG_SHARE_MAX:.0%} 아래로"
                             "(앞뒤 문장에 이음말로 붙인다. 조각은 장면이 크게 멈출 때만)")
    elif fl["조각 비율"] > FRAG_SHARE_WARN:
        res["warnings"].append(f"조각 문장이 {fl['조각 비율']:.0%} — {FRAG_SHARE_WARN:.0%} 넘으면 끊겨 읽히기 시작한다")
    if len(fl["한 줄 문단"]) > ONE_LINE_PARA_WARN:
        res["warnings"].append(f"한 문장짜리 서술 문단 {len(fl['한 줄 문단'])}개 — {ONE_LINE_PARA_WARN}개 넘으면 끊겨 읽힌다"
                               "(크게 멈추는 자리만 남기고 앞뒤 문단에 붙인다)")
    return res


def main(paths):
    total_repeat = {}   # {부: {구문: 횟수}}
    n_err = 0
    for p in paths:
        r = check_file(p)
        print(f"\n■ {r['file']}")
        print(f"  분량: {r['counts']['글자(공백 포함)']:,}자(공백 포함) / {r['counts']['글자(공백 제외)']:,}자(공백 제외)")
        print(f"  오감(소리·냄새·촉감): {r['counts']['오감']}")
        print(f"  문장 버릇: {r['counts']['문장 버릇']}")
        print(f"  문장 끝: {r['counts']['문장 끝']}")
        print(f"  문장 흐름: {r['counts']['문장 흐름']}")
        if r["counts"]["반복"]:
            print(f"  반복 구문: {r['counts']['반복']}")
        bucket = total_repeat.setdefault(r["part"], {})
        for k, v in r["counts"]["반복"].items():
            bucket[k] = bucket.get(k, 0) + v
        for e in r["errors"]:
            print(f"  ✗ {e}")
        for w in r["warnings"]:
            print(f"  △ {w}")
        n_err += len(r["errors"])
    if len(paths) > 1:
        for part, bucket in sorted(total_repeat.items()):
            print(f"\n■ {part[-1]}부 합계(반복 구문 상한은 부 하나 전체 기준)")
            for k, v in bucket.items():
                lim = REPEAT_LIMITS[k]
                mark = "✗" if v > lim else "○"
                print(f"  {mark} '{k}' ×{v} (상한 {lim})")
                if v > lim:
                    n_err += 1
    print(f"\n오류 {n_err}개" + (" — 고친 뒤 다시 돌린다." if n_err else " — 통과."))
    return 1 if n_err else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
