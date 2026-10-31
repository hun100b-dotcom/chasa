"""동이 컨셉 3안(정면·측면) + 혼 4종 실루엣 시트. 쇼룸/3D 대역용.
이유: 3D로 옮기기 쉽도록 정면·측면을 같은 높이·같은 기준선에 나란히 둔다.
고정 5요소(흑립·검은 도포·붉은 띠·철삭·혼불)는 3안 모두 유지하고 '실루엣'만 다르게 한다.
도구: Higgsfield 미연결 → 자체 SVG 파이프라인(작업 컨셉용)."""
import os, subprocess, math
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = "/mnt/project-files/art"
INK, DEEP, RED, CHAIN, CHEON, HANJI, GOLD = "#2A2A38", "#0F1729", "#E85C41", "#BFE8FF", "#5FE3C0", "#F3E7D3", "#D4A94E"
def chain(pts, w=5):
    # 사슬: 고리 타원을 경로 위에 늘어놓는다
    o = ""
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 11))
        for k in range(n):
            t = k / n; x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            a = math.degrees(math.atan2(y2 - y1, x2 - x1)) + (90 if k % 2 else 0)
            o += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="7" ry="4" transform="rotate({a:.0f} {x:.0f} {y:.0f})" fill="none" stroke="{CHAIN}" stroke-width="{w}"/>'
    return o
def orb(x, y, r=14):
    return f'<circle cx="{x}" cy="{y}" r="{r*2.2}" fill="{CHEON}" opacity=".18"/><circle cx="{x}" cy="{y}" r="{r}" fill="{CHEON}"/><circle cx="{x-r*.3}" cy="{y-r*.3}" r="{r*.35}" fill="#fff" opacity=".8"/>'
def hero(v, view, cx):
    """v: A/B/C, view: front/side. 바닥선 y=500, 키 약 480."""
    P = {"A": dict(brim=92, crown=58, ch=62, coat=70, hem=84, slv=0, tail=0),
         "B": dict(brim=74, crown=50, ch=52, coat=58, hem=120, slv=1, tail=0),
         "C": dict(brim=104, crown=46, ch=84, coat=62, hem=70, slv=0, tail=1)}[v]
    side = view == "side"
    k = .55 if side else 1                        # 측면은 몸 폭을 줄인다
    top = 500 - 480; hy = top + 44                # 갓 챙 높이
    s = ""
    # 도포(몸) — 어깨 폭 → 밑단
    sh, hem, hy2 = P["coat"] * k, P["hem"] * k, 500
    s += f'<path d="M{cx-sh*.55:.0f},{hy+60} L{cx+sh*.55:.0f},{hy+60} L{cx+hem:.0f},{hy2} L{cx-hem:.0f},{hy2} Z" fill="{INK}"/>'
    if P["tail"]:   # C: 뒤로 길게 늘어진 자락
        bx = cx + (hem + 40 if side else hem * .2)
        s += f'<path d="M{cx+sh*.3:.0f},{hy+120} L{bx:.0f},{hy2+6} L{cx+hem*.5:.0f},{hy2} Z" fill="#1A1A26"/>'
    # 소매
    if not side:
        w = 46 if P["slv"] else 24
        for sgn in (-1, 1):
            x0 = cx + sgn * sh * .55
            s += f'<path d="M{x0:.0f},{hy+64} L{x0+sgn*(w+30):.0f},{hy+190} L{x0+sgn*(w+4):.0f},{hy+258} L{x0-sgn*6:.0f},{hy+190} Z" fill="#232338"/>'
    else:
        s += f'<path d="M{cx-8},{hy+64} L{cx+34},{hy+180} L{cx+6},{hy+240} L{cx-18},{hy+170} Z" fill="#232338"/>'
    # 붉은 띠(허리) + 늘어진 끝
    bw = (sh * 1.0 + 6) if not side else sh * 1.0 + 4
    s += f'<rect x="{cx-bw*.6:.0f}" y="{hy+170}" width="{bw*1.2:.0f}" height="12" fill="{RED}"/><path d="M{cx+bw*.3:.0f},{hy+182} l10,70 l10,-6 l-4,-64 Z" fill="{RED}"/>'
    # 깃(동정)
    s += f'<path d="M{cx-12*k-6:.0f},{hy+58} L{cx:.0f},{hy+110} L{cx+12*k+6:.0f},{hy+58} Z" fill="{HANJI}" opacity=".9"/>'
    # 얼굴(어둠) + 목
    s += f'<rect x="{cx-12:.0f}" y="{hy+36}" width="24" height="26" fill="#0A0A12"/>'
    # 철삭: A 허리 늘어짐 / B 손에 감음 / C 어깨→허리 사선
    if v == "A": s += chain([(cx - sh * .5, hy + 180), (cx - sh * .9, hy + 250), (cx - sh * 1.3, hy + 330)] if not side else [(cx - 20, hy + 180), (cx - 40, hy + 270), (cx - 20, hy + 340)])
    if v == "B": s += chain([(cx + sh * 1.4, hy + 250), (cx + sh * 2.0, hy + 190), (cx + sh * 2.6, hy + 260), (cx + sh * 2.0, hy + 330)] if not side else [(cx + 30, hy + 240), (cx + 70, hy + 200), (cx + 100, hy + 270)])
    if v == "C": s += chain([(cx - sh * .5, hy + 64), (cx + sh * .1, hy + 120), (cx + sh * .7, hy + 178), (cx + sh * .9, hy + 260)] if not side else [(cx - 12, hy + 64), (cx + 8, hy + 130), (cx + 24, hy + 190), (cx + 10, hy + 280)])
    # 혼불
    ox = cx + (sh * 2.0 if v == "B" and not side else (sh + 52)); s += orb(ox, hy + 270 if v == "B" else hy + 140)
    # 흑립: 챙(납작 타원) + 통
    b, ch = P["brim"] * (.75 if side else 1), P["ch"]
    s += f'<path d="M{cx-P["crown"]*(.7 if side else 1)/2:.0f},{hy} L{cx-P["crown"]*(.55 if side else .8)/2:.0f},{hy-ch} Q{cx},{hy-ch-16} {cx+P["crown"]*(.55 if side else .8)/2:.0f},{hy-ch} L{cx+P["crown"]*(.7 if side else 1)/2:.0f},{hy} Z" fill="#0E0E18"/>'
    s += f'<ellipse cx="{cx}" cy="{hy+2}" rx="{b}" ry="{16 if side else 18}" fill="#14141F"/><path d="M{cx-b*.6:.0f},{hy+14} Q{cx},{hy+34} {cx+b*.6:.0f},{hy+14}" stroke="{RED}" stroke-width="3" fill="none"/>'
    return s
def soul_shapes():
    S = {}
    # 갓 죽은 혼: 작고 곧은 물방울+짧은 꼬리 / 해 넘긴 혼: 팔 늘어진 키 큰 / 오래된: 구부정·가시·긴 꼬리 / 덩어리: 겹친 큰 덩이
    S["갓 죽은 혼"] = ('<path d="M0,-70 C40,-30 38,30 0,40 C-38,30 -40,-30 0,-70Z"/><path d="M-8,36 Q0,70 10,60 Q4,48 8,36Z"/>', "10초")
    S["해 넘긴 혼"] = ('<path d="M0,-84 C26,-84 30,-50 24,-30 L40,40 L22,34 L8,60 L-8,34 L-26,44 L-24,-30 C-30,-50 -26,-84 0,-84Z"/><path d="M-24,-20 L-64,30 L-50,42 L-22,6Z M24,-20 L64,30 L50,42 L22,6Z"/>', "7초")
    S["오래된 혼"] = ('<path d="M-40,-30 C-30,-70 30,-76 44,-40 L56,-52 L52,-20 L70,-24 L50,6 C40,40 26,60 30,76 L10,52 L-14,84 L-18,48 C-50,40 -56,0 -40,-30Z"/><path d="M-30,-60 L-44,-84 L-18,-66Z M10,-72 L20,-98 L26,-68Z"/>', "4초")
    S["덩어리"] = ('<circle cx="-30" cy="10" r="38"/><circle cx="26" cy="-10" r="44"/><circle cx="0" cy="40" r="40"/><circle cx="-6" cy="-40" r="28"/><path d="M-60,40 l-20,30 l30,-10Z M50,40 l26,30 l-34,-4Z"/>', "파혼만")
    return S
def page():
    figs = ""
    for i, v in enumerate("ABC"):
        for j, view in enumerate(("front", "side")):
            cx = 140 + i * 520 + j * 250
            figs += f'<g>{hero(v, view, cx)}</g><text x="{cx}" y="534" fill="{HANJI}" font-size="14" text-anchor="middle">{"정면" if j == 0 else "측면"}</text>'
        figs += f'<text x="{140+i*520+125}" y="-50" fill="{GOLD}" font-size="26" text-anchor="middle" font-weight="bold">{["A 단정한 차사","B 넓은 소매","C 긴 자락"][i]}</text>'
        figs += f'<text x="{140+i*520+125}" y="-24" fill="{HANJI}" font-size="14" text-anchor="middle">{["표준 비율 · 챙 넓은 흑립 · 사슬이 허리에서 늘어짐","소매·밑단이 퍼져 움직임이 읽힘 · 사슬을 손에 감음","높은 흑립 · 뒤로 긴 자락 · 사슬이 어깨→허리 사선"][i]}</text>'
    g = "".join(f'<line x1="{x}" y1="100" x2="{x}" y2="650" stroke="#ffffff10"/>' for x in (520, 1040))
    # 쿼터뷰 거리 검증: 같은 그림을 작게(키 90px) 한 줄로
    small = "".join(f'<g transform="translate({60+i*520+440} 640) scale(.19)"><g transform="translate({-(140+i*520)} -500)">{hero(v,"front",140+i*520)}</g></g>' for i, v in enumerate("ABC"))
    small = "".join(f'<g transform="translate({300+i*520} 650) scale(.2) translate({-(140+i*520)} -500)">{hero(v,"front",140+i*520)}</g>' for i, v in enumerate("ABC"))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1560" height="830" font-family="Noto Sans KR,sans-serif"><rect width="1560" height="830" fill="{DEEP}"/>{g}<g transform="translate(0 110)">{figs}</g><line x1="40" y1="670" x2="1520" y2="670" stroke="#ffffff22"/><text x="40" y="700" fill="{HANJI}" font-size="13">쿼터뷰 거리 읽힘 검사(키 약 100px)</text><g transform="translate(0 150)">{small}</g></svg>'
def souls():
    S = soul_shapes(); cols = ["#BFE8FF", "#FFCC55", "#FF6A3D", "#9A5CFF"]; o = ""
    for i, (n, (d, t)) in enumerate(S.items()):
        cx = 190 + i * 380
        o += f'<g transform="translate({cx} 230) scale(1.3)"><g fill="{cols[i]}" opacity=".95">{d}</g></g>'
        o += f'<g transform="translate({cx} 410) scale(.5)"><g fill="#000">{d}</g></g><g transform="translate({cx-90} 410) scale(.28)"><g fill="#000">{d}</g></g>'
        o += f'<text x="{cx}" y="62" fill="{cols[i]}" font-size="22" text-anchor="middle" font-weight="bold">{n}</text><text x="{cx}" y="86" fill="{HANJI}" font-size="14" text-anchor="middle">처결 대기 {t}</text>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1560" height="490" font-family="Noto Sans KR,sans-serif"><rect width="1560" height="490" fill="{DEEP}"/><rect y="340" width="1560" height="150" fill="#6c7a92"/><text x="20" y="332" fill="{HANJI}" font-size="13">아래 줄: 밝은 바닥 위 검은 실루엣(쿼터뷰 거리 크기 2종) — 모양만으로 구분되는지 검사</text>{o}</svg>'
if __name__ == "__main__":
    tmp = "/tmp/hc"; os.makedirs(tmp, exist_ok=True)
    js = ["const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"]
    for n, svg, w, h in [("hero_concepts_ABC", page(), 1560, 830), ("soul_silhouettes_4", souls(), 1560, 490)]:
        f = f"{tmp}/{n}.svg"; open(f, "w", encoding="utf-8").write(svg)
        js.append(f"{{const p=await b.newPage({{viewport:{{width:{w},height:{h}}}}});await p.goto('file://{f}');await p.screenshot({{path:'{OUT}/{n}.png'}});}}")
    js.append("await b.close()})()"); open(f"{tmp}/r.cjs", "w").write("\n".join(js))
    subprocess.run(["node", f"{tmp}/r.cjs"], env={**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()}, check=True)
