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
LONG_SHARE_MIN = 0.15     # 긴 문장이 이 비율보다 적으면 리듬이 한 가지로 굳는다(1~20장은 7.9%)
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
