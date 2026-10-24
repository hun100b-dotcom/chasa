#!/usr/bin/env python3
# 수치 원본(data/balance.json) → Godot(config.gd)·Unity(Balance.cs)로 값을 맞춰 주는 도구.
# 왜 있나? 엔진이 Unity로 확정됐는데 수치가 godot/config.gd 에만 있으면 엔진을 옮길 때 값이 사라진다.
#   원본은 엔진과 무관한 JSON 한 곳. 두 엔진 쪽 파일은 여기서 따라온다. (docs/TECH-STACK.md "JSON 원본" 원칙)
# 사용:
#   python3 tools/sync_balance.py            # JSON → config.gd 값 반영 + Balance.cs 생성
#   python3 tools/sync_balance.py --check    # 어긋났는지만 검사(고치지 않음). 어긋나면 종료코드 1
#   python3 tools/sync_balance.py --import   # (최초 1회용) config.gd 의 숫자·참/거짓 상수를 JSON 으로 뽑는다
# 수치를 바꿀 땐 data/balance.json 의 "value" 만 고치고 이 도구를 돌린다. config.gd 를 직접 고치면 --check 가 잡는다.
import json, re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_P = os.path.join(ROOT, 'data', 'balance.json')
GD_P = os.path.join(ROOT, 'godot', 'config.gd')
CS_P = os.path.join(ROOT, 'unity', 'Assets', 'Scripts', 'Balance.cs')
# const KEY := 값   # 주석   (값이 숫자 또는 true/false 인 한 줄짜리만 대상. 색·배열·딕셔너리는 엔진 쪽에 남긴다)
LINE = re.compile(r'^const ([A-Z][A-Z0-9_]*)\s*:?=\s*(-?\d+(?:\.\d+)?|true|false)\s*(?:#\s*(.*))?$')

def parse_gd(text):
    out = {}
    for ln in text.splitlines():
        m = LINE.match(ln)
        if m:
            v = m.group(2)
            out[m.group(1)] = (v == 'true') if v in ('true', 'false') else (float(v) if '.' in v else int(v))
    return out

def fmt_gd(v):
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, float): return repr(v)
    return str(v)

def cs_type(v):
    return 'bool' if isinstance(v, bool) else ('float' if isinstance(v, float) else 'int')

def fmt_cs(v):
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, float): return repr(v) + 'f'
    return str(v)

def import_json():
    text = open(GD_P, encoding='utf-8').read()
    data = {}
    for ln in text.splitlines():
        m = LINE.match(ln)
        if m:
            v = m.group(2)
            val = (v == 'true') if v in ('true', 'false') else (float(v) if '.' in v else int(v))
            data[m.group(1)] = {'value': val, 'note': (m.group(3) or '').strip()}
    json.dump(data, open(JSON_P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(data)}개 상수를 {JSON_P} 로 뽑았다')

def sync(check):
    data = json.load(open(JSON_P, encoding='utf-8'))
    text = open(GD_P, encoding='utf-8').read()
    cur = parse_gd(text)
    bad = []
    for k, e in data.items():
        if k not in cur: bad.append(f'{k}: config.gd 에 없음')
        elif cur[k] != e['value'] or type(cur[k]) is not type(e['value']): bad.append(f'{k}: config.gd={cur[k]} JSON={e["value"]}')
    for k in cur:
        if k not in data: bad.append(f'{k}: JSON 에 없음 (config.gd 에만 있음)')
    # Balance.cs 내용
    lines = ['// 자동 생성 파일 — 직접 고치지 말 것. 원본: data/balance.json, 생성: python3 tools/sync_balance.py',
             '// 왜 자동 생성인가? 수치를 엔진과 무관한 JSON 한 곳에 두고, Unity 는 여기서 따라오게 하려는 것.',
             'public static class Balance', '{']
    for k, e in data.items():
        note = f'  // {e["note"]}' if e.get('note') else ''
        lines.append(f'    public const {cs_type(e["value"])} {k} = {fmt_cs(e["value"])};{note}')
    lines.append('}')
    cs = '\n'.join(lines) + '\n'
    old_cs = open(CS_P, encoding='utf-8').read() if os.path.exists(CS_P) else ''
    if old_cs != cs: bad.append('Balance.cs 가 JSON 과 다름')
    if check:
        if bad:
            print('어긋남:\n  ' + '\n  '.join(bad)); sys.exit(1)
        print(f'일치 ({len(data)}개)'); return
    new_lines = []
    for ln in text.splitlines():
        m = LINE.match(ln)
        if m and m.group(1) in data:
            v = data[m.group(1)]['value']
            ln = re.sub(r'(:?=\s*)(-?\d+(?:\.\d+)?|true|false)', lambda mm: mm.group(1) + fmt_gd(v), ln, count=1)
        new_lines.append(ln)
    open(GD_P, 'w', encoding='utf-8').write('\n'.join(new_lines) + ('\n' if text.endswith('\n') else ''))
    os.makedirs(os.path.dirname(CS_P), exist_ok=True)
    open(CS_P, 'w', encoding='utf-8').write(cs)
    print(f'동기화 완료 ({len(data)}개). 고친 것 외 어긋남: {len(bad)}건 반영됨')

if __name__ == '__main__':
    if '--import' in sys.argv: import_json()
    else: sync('--check' in sys.argv)
