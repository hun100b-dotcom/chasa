#!/usr/bin/env python3
"""《차사》 원고(부마다 마크다운 여러 개) → 전자책 한 장짜리 HTML.

왜 이렇게 만드나:
  - 원고는 docs/novel/part1/*.md, part2/*.md … 에만 둔다(고칠 곳이 한 군데).
  - 전자책은 그 원고를 읽어서 '찍어 내는' 결과물이다. 원고를 고치면 이 스크립트만 다시 돌리면 된다.
  - 부(part)가 늘면 아래 PARTS 표에 한 줄만 더하면 된다.

쓰는 법:
  python3 docs/novel/ebook/build.py            # → docs/novel/ebook/dist/chasa-part1.html
  python3 docs/novel/ebook/build.py 출력경로.html
"""
import html
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent          # docs/novel/ebook
NOVEL = HERE.parent                                     # docs/novel
TEMPLATE = HERE / "template.html"                       # 화면 틀(디자인·조작 코드)
READ_SPEED = 600                                        # 1분에 읽는 글자 수(공백 포함, 소설을 천천히 읽는 속도로 잡음)

# 부 목록: (원고 폴더, 부 번호, 부 이름, 계획한 장 수(프롤로그 포함), 표제지 한 줄)
#   계획한 장 수보다 원고가 적으면 '아직 쓰는 중'으로 보여 준다(독자에게 정직하게).
#   표제지 한 줄(epigraph, 부 첫머리에 놓는 짧은 글)은 그 부를 관통하는 그림 하나로 고른다.
PARTS = [
    ("part1", "제1부", "솔고개", 15, ""),
    ("part2", "제2부", "검은여울", 12, "지운 자리는 하얗게 남는다."),
]
# 1부를 새 기준(문장 흐름 3판)으로 처음부터 다시 쓰는 동안만 쓰는 표(2026-10-25~).
#   여기 적힌 파일은 목차에 '새로 씀' 표시가 붙고, 안 적힌 장은 옛 원고라는 뜻이다.
#   왜: 새 장과 옛 장이 한 책에 섞여 있으니, 오너가 어디까지가 새 원고인지 목차만 보고 알 수 있어야 한다.
#   장을 하나 다시 쓸 때마다 파일 이름을 더하고, 1부를 다 다시 쓰면 이 표를 비운다.
REWRITTEN = {"part1": {"00-prologue.md", "01.md", "02.md", "03.md", "04.md", "05.md", "06.md", "07.md", "08.md", "09.md"}}
NUM_WORD = ["영", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열", "열한", "열두",
            "열세", "열네", "열다섯", "열여섯"]


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


def chapter_files(folder: pathlib.Path):
    """원고 폴더에서 '장' 파일만 고른다. 이름이 숫자로 시작하는 것만(00-prologue.md, 15.md …).
    CARDS.md 같은 설계 메모는 책에 들어가면 안 되므로 뺀다."""
    return sorted(f for f in folder.glob("*.md") if f.name[:1].isdigit())


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "dist" / "chasa-part1.html"
    chapters, rows, total = [], [], 0
    parts_meta, meta_bits = [], []
    for pi, (folder, num, name, planned, epi) in enumerate(PARTS):
        files = chapter_files(NOVEL / folder)
        if not files:
            continue                      # 아직 한 장도 없는 부는 책에 넣지 않는다
        short = num.replace("제", "")      # "제2부" → "2부"
        written = len(files)
        side = "다 씀" if written >= planned else f"{planned}장 중 {written}장"
        new_set = REWRITTEN.get(folder, set())
        if new_set:   # 다시 쓰는 중인 부는 '새로 쓴 장 수 / 전체'를 보여 준다
            side = f"다시 쓰는 중 · 새로 쓴 장 {sum(1 for f in files if f.name in new_set)}/{written}"
        rows.append(
            f'      <li class="toc-part"><span class="tp-num">{esc(num)}</span>'
            f'<span class="tp-name">{esc(name)}</span><span class="tp-side">{esc(side)}</span></li>'
        )
        parts_meta.append({"num": num, "short": short, "name": name, "planned": planned,
                           "written": written, "epi": esc(epi)})
        for k, f in enumerate(files):
            i = len(chapters)             # 책 전체에서 몇 번째 마당인가(0 = 프롤로그). 1부 번호는 예전 판과 같다.
            label, title, body, chars = convert(f.read_text(encoding="utf-8"))
            total += chars
            mins = max(1, round(chars / READ_SPEED))
            mark = "서" if label == "프롤로그" else label.replace("장", "")   # 도장 안에 들어갈 글자
            chapters.append({"label": label, "title": title, "mark": mark, "mins": mins, "chars": chars,
                             "html": body, "part": f"{num} {name}", "pi": len(parts_meta) - 1, "first": k == 0})
            href = "#prologue" if i == 0 else f"#ch{i}"
            rows.append(
                f'      <li><a href="{href}" data-ch="{i}">'
                f'<span class="seal" data-state="none" aria-hidden="true">{esc(mark)}</span>'
                f'<span class="t-main"><span class="t-label">{esc(label)}'
                + ('<span class="t-new">새로 씀</span>' if f.name in new_set else "")
                + f'</span><span class="t-title">{esc(title)}</span></span>'
                f'<span class="t-side">약 {mins}분</span></a></li>'
            )
        # 표지 아래 안내 줄: "1부 「솔고개」 프롤로그와 열네 장" / "2부 「검은여울」 세 장(쓰는 중)"
        has_pro = files[0].name.startswith("00")
        n_ch = written - (1 if has_pro else 0)
        what = ("프롤로그와 " if has_pro else "") + f"{NUM_WORD[n_ch] if n_ch < len(NUM_WORD) else n_ch} 장"
        meta_bits.append(f"{short} 「{name}」 {what}" + ("" if written >= planned else "(쓰는 중)"))

    # 다 읽는 데 걸리는 시간: 30분 단위로 반올림해 "약 4시간 반"처럼 쓴다
    half_hours = round(total / READ_SPEED / 30)
    hours, half = divmod(half_hours, 2)
    total_time = f"약 {hours}시간" + (" 반" if half else "")
    man = round(total / 10000)   # 만 자 단위

    last = parts_meta[-1]
    end_toast = (f"{last['short']}는 여기까지 썼습니다" if last["written"] < last["planned"]
                 else f"{last['short']} 끝입니다")
    data = json.dumps({"title": "차사", "parts": parts_meta, "endToast": end_toast, "chapters": chapters},
                      ensure_ascii=False)
    data = data.replace("</", "<\\/")   # 본문에 '</'가 있어도 <script>가 중간에 닫히지 않게

    # 표지 세로 글: 부마다 한 줄(세로쓰기에서 줄바꿈 = 왼쪽으로 새 줄). 숫자는 눕지 않게 세운다.
    cover_sub = "<br>".join(
        f'제<span class="tcu">{p["short"].replace("부", "")}</span>부 {esc(p["name"])}' for p in parts_meta)
    doc_title = "차사 " + "·".join(p["short"].replace("부", "") for p in parts_meta) + "부"   # "차사 1·2부"
    meta = "장편소설 · " + " · ".join(meta_bits) + f" · 약 {man}만 자 · 다 읽는 데 {total_time}"

    page = TEMPLATE.read_text(encoding="utf-8")
    page = (page.replace("{{TOC_ROWS}}", "\n".join(rows))
                .replace("{{BOOK_JSON}}", data)
                .replace("{{DOC_TITLE}}", doc_title)
                .replace("{{COVER_SUB}}", cover_sub)
                .replace("{{COVER_SEAL}}", esc(last["name"]))
                .replace("{{META}}", esc(meta)))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"부 {len(parts_meta)}개, 마당 {len(chapters)}개, 본문 {total:,}자, {total_time} → {out} ({out.stat().st_size/1024:.0f}KB)")


if __name__ == "__main__":
    main()
