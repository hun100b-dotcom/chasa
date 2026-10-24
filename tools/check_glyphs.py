#!/usr/bin/env python3
# 화면 글자 점검: 코드 안의 한글·기호가 글꼴(Noto Sans KR 부분 글꼴, KS X 1001 한글 2350자 + 영숫자·기호)에 있는지 검사.
# 왜? 글꼴에 없는 글자는 화면에서 네모(▯)로 깨진다. 푸시 전에 돌려 미리 잡는다.
# 사용: python3 tools/check_glyphs.py        (문제가 있으면 종료코드 1)
import re, glob, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ok = set(chr(c) for c in range(0x20, 0x7f)) | set("\n\t")
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try: ok.add(bytes([hi, lo]).decode('euc-kr'))
        except Exception: pass
ok |= set("·…—–‘’“”×→←↑↓▶◀●○■□★☆♥♦%+-~※「」『』《》〈〉①②③④⑤")
bad = {}
for f in glob.glob(os.path.join(ROOT, 'unity', 'Assets', 'Scripts', '**', '*.cs'), recursive=True):
    if os.sep + 'Editor' + os.sep in f: continue
    for i, line in enumerate(open(f, encoding='utf-8'), 1):
        code = line.split('//')[0]            # 주석은 화면에 안 나오므로 제외
        for m in re.findall(r'"((?:[^"\\]|\\.)*)"', code):
            for ch in m:
                if ord(ch) > 127 and ch not in ok: bad.setdefault(ch, []).append(f"{os.path.relpath(f, ROOT)}:{i}")
for ch, where in bad.items(): print(f"글꼴에 없음 '{ch}' (U+{ord(ch):04X}): {', '.join(where[:3])}")
print("글자 점검:", "문제 없음" if not bad else f"{len(bad)}종 문제")
sys.exit(1 if bad else 0)
