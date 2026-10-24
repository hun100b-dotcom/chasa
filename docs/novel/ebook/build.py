#!/usr/bin/env python3
"""《차사》 1부 원고(마크다운 15개) → 전자책 한 장짜리 HTML.

왜 이렇게 만드나:
  - 원고는 docs/novel/part1/*.md 에만 둔다(고칠 곳이 한 군데).
  - 전자책은 그 원고를 읽어서 '찍어 내는' 결과물이다. 원고를 고치면 이 스크립트만 다시 돌리면 된다.

쓰는 법:
  python3 docs/novel/ebook/build.py            # → docs/novel/ebook/dist/chasa-part1.html
  python3 docs/novel/ebook/build.py 출력경로.html
"""
import html
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent          # docs/novel/ebook
PART = HERE.parent / "part1"                            # 원고 폴더
TEMPLATE = HERE / "template.html"                       # 화면 틀(디자인·조작 코드)
READ_SPEED = 600                                        # 1분에 읽는 글자 수(공백 포함, 소설을 천천히 읽는 속도로 잡음)


def esc(text: str) -> str:
    """HTML에서 특별한 뜻이 있는 글자(&, <, >)를 글자 그대로 보이게 바꾼다."""
    return html.escape(text, quote=False)


def convert(md: str):
    """원고 한 장을 (장 이름, 제목, 본문 HTML, 글자 수)로 바꾼다.

    원고에서 쓰는 표시는 다섯 가지뿐이다:
      # 1장 · 제목   → 장 머리
      ---            → 장면이 바뀌는 자리
      > 글           → 먹지기 쪽지(명부 여백의 글)
      *글*           → 기억 한 줄(줄 전체가 기울임일 때)
      그 밖의 줄     → 문단
    """
    lines = md.splitlines()
    head = lines[0].lstrip("#").strip()
    label, title = [x.strip() for x in head.split("·", 1)]
    blocks, chars = [], 0
    for raw in lines[1:]:
        s = raw.strip()
        if not s:
            continue
        if s == "---":
            blocks.append('<p class="brk" aria-hidden="true">· · ·</p>')
            continue
        if s.startswith(">"):
            text = s.lstrip(">").strip()
            chars += len(text)
            blocks.append(f'<aside class="slip" aria-label="명부 여백의 쪽지"><p>{esc(text)}</p></aside>')
            continue
        if len(s) > 2 and s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            text = s[1:-1].strip()
            chars += len(text)
            blocks.append(f'<p class="mem">{esc(text)}</p>')
            continue
        chars += len(s)
        blocks.append(f"<p>{esc(s)}</p>")
    return label, title, "\n".join(blocks), chars


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "dist" / "chasa-part1.html"
    files = sorted(PART.glob("*.md"))   # 00-prologue.md, 01.md … 14.md (이름 순서 = 장 순서)
    chapters, rows, total = [], [], 0
    for i, f in enumerate(files):
        label, title, body, chars = convert(f.read_text(encoding="utf-8"))
        total += chars
        mins = max(1, round(chars / READ_SPEED))
        mark = "서" if label == "프롤로그" else label.replace("장", "")   # 도장 안에 들어갈 글자
        chapters.append({"label": label, "title": title, "mark": mark, "mins": mins, "chars": chars, "html": body})
        href = "#prologue" if i == 0 else f"#ch{i}"
        rows.append(
            f'      <li><a href="{href}" data-ch="{i}">'
            f'<span class="seal" data-state="none" aria-hidden="true">{esc(mark)}</span>'
            f'<span class="t-main"><span class="t-label">{esc(label)}</span><span class="t-title">{esc(title)}</span></span>'
            f'<span class="t-side">약 {mins}분</span></a></li>'
        )

    # 다 읽는 데 걸리는 시간: 30분 단위로 반올림해 "약 4시간 반"처럼 쓴다
    half_hours = round(total / READ_SPEED / 30)
    hours, half = divmod(half_hours, 2)
    total_time = f"약 {hours}시간" + (" 반" if half else "")
    man = round(total / 10000)   # 만 자 단위

    data = json.dumps({"title": "차사", "part": "1부 솔고개", "chapters": chapters}, ensure_ascii=False)
    data = data.replace("</", "<\\/")   # 본문에 '</'가 있어도 <script>가 중간에 닫히지 않게

    page = TEMPLATE.read_text(encoding="utf-8")
    page = (page.replace("{{TOC_ROWS}}", "\n".join(rows))
                .replace("{{BOOK_JSON}}", data)
                .replace("{{TOTAL_MAN}}", str(man))
                .replace("{{TOTAL_TIME}}", total_time))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"장 {len(chapters)}개, 본문 {total:,}자, {total_time} → {out} ({out.stat().st_size/1024:.0f}KB)")


if __name__ == "__main__":
    main()
