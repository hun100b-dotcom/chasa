"""UI 재료 키트: 한지 창 · 먹 붓선 테두리 · 붉은 인 · 12지시 시각 고리 · 달 8장 · 세로 이름표 · 등급 테두리 5종 · 처결 고리.
출처: 기획팀 UI 밑그림(재료 넷: 밤 남청 · 한지 · 먹 · 붉은 인, 금은 귀한 것에만, 천도 청록·파혼 주황은 그 둘만).
gen_sprites3.run() 이 부른다. 모든 그림은 9조각(9-slice) 또는 고정 크기이며 파일명은 ui/ 아래."""
import random, math

HANJI, INK, RED, GOLD, NIGHT, TEAL, ORANGE = "#F3E7D3", "#2A2A38", "#E85C41", "#D4A94E", "#16213E", "#5FE3C0", "#E8683A"


def wrap(w, h, b, d=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{d}'
            '<filter id="rough"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="3"/></filter>'
            '<filter id="blur"><feGaussianBlur stdDeviation="2"/></filter></defs>' + b + '</svg>')


def torn(w, h, m, seed, amp=3.0):
    """가장자리가 살짝 찢긴 사각형 경로(한지 창 윤곽). 사방 모서리 m 안쪽은 9조각 고정부라 같은 규칙으로 이어진다."""
    r = random.Random(seed); pts = []
    step = 8
    for x in range(m, w - m + 1, step): pts.append((x, m / 2 + r.uniform(-amp, amp)))
    for y in range(m, h - m + 1, step): pts.append((w - m / 2 + r.uniform(-amp, amp), y))
    for x in range(w - m, m - 1, -step): pts.append((x, h - m / 2 + r.uniform(-amp, amp)))
    for y in range(h - m, m - 1, -step): pts.append((m / 2 + r.uniform(-amp, amp), y))
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"


def run(add):
    # 1) 한지 창 256×256, 9조각 모서리 48
    r = random.Random(11)
    fib = "".join(f'<path d="M{r.uniform(20,236):.0f},{r.uniform(20,236):.0f} l{r.uniform(-18,18):.0f},{r.uniform(-6,6):.0f}" stroke="#D9C7A6" stroke-width="1" opacity=".5"/>' for _ in range(70))
    p = torn(256, 256, 24, 5)
    b = (f'<path d="{p}" fill="url(#hj)" stroke="#B9A888" stroke-width="2"/>{fib}'
         f'<path d="{p}" fill="none" stroke="{INK}" stroke-width="1.5" opacity=".55" transform="translate(128 128) scale(.93) translate(-128 -128)"/>')
    d = '<linearGradient id="hj" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F6ECD9"/><stop offset="1" stop-color="#E4D5B8"/></linearGradient>'
    add("ui", "ui_hanji_panel", 256, 256, wrap(256, 256, b, d), (.5, .5), "한지 창 · 9조각(모서리 48px) · 가장자리 살짝 찢김")
    # 2) 먹 붓선 테두리 두 종(가는/겹) 128×128, 9조각 모서리 28, 가운데는 투명
    def brush(x1, y1, x2, y2, w, seed):
        rr = random.Random(seed); pts = []
        n = 14
        for i in range(n + 1):
            t = i / n; ww = w * (.55 + .45 * math.sin(math.pi * t) + rr.uniform(-.1, .1))
            pts.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, ww))
        up = " ".join(f"{x - (0 if y1 != y2 else 0):.1f},{y - ww / 2 if y1 == y2 else y:.1f}" for x, y, ww in [])  # 미사용(가독용)
        if y1 == y2:
            top = " L".join(f"{x:.1f},{y - ww / 2:.1f}" for x, y, ww in pts); bot = " L".join(f"{x:.1f},{y + ww / 2:.1f}" for x, y, ww in reversed(pts))
        else:
            top = " L".join(f"{x - ww / 2:.1f},{y:.1f}" for x, y, ww in pts); bot = " L".join(f"{x + ww / 2:.1f},{y:.1f}" for x, y, ww in reversed(pts))
        return f'<path d="M{top} L{bot}Z" fill="{INK}" filter="url(#rough)"/>'
    thin = "".join([brush(8, 10, 120, 10, 4, 1), brush(8, 118, 120, 118, 4, 2), brush(10, 8, 10, 120, 4, 3), brush(118, 8, 118, 120, 4, 4)])
    add("ui", "ui_ink_border_thin", 128, 128, wrap(128, 128, thin), (.5, .5), "먹 붓선 테두리 · 가는 한 겹 · 9조각(모서리 28px)")
    dbl = thin + "".join([brush(14, 18, 114, 18, 2, 5), brush(14, 110, 114, 110, 2, 6), brush(18, 14, 18, 114, 2, 7), brush(110, 14, 110, 114, 2, 8)])
    add("ui", "ui_ink_border_double", 128, 128, wrap(128, 128, dbl), (.5, .5), "먹 붓선 테두리 · 겹선 · 9조각(모서리 28px)")
    # 3) 붉은 인 아이콘 64×64 (선택·새것·천도함) + 파혼 = 먹으로 그은 줄 (128×24)
    def seal(ch):
        b = (f'<rect x="6" y="6" width="52" height="52" rx="3" fill="{RED}" filter="url(#rough)"/>'
             f'<rect x="12" y="12" width="40" height="40" fill="none" stroke="{HANJI}" stroke-width="2" opacity=".85"/>'
             f'<text x="32" y="45" font-size="32" font-weight="700" fill="{HANJI}" text-anchor="middle" font-family="Noto Serif KR,serif">{ch}</text>')
        return wrap(64, 64, b)
    for nm, ch, note in [("select", "印", "선택/확정"), ("new", "新", "새것"), ("cheondo", "度", "천도함")]:
        add("ui", f"ui_seal_{nm}", 64, 64, seal(ch), (.5, .5), f"붉은 인 · {note} (누르면 0.15초 도장 찍힘 움직임)")
    add("ui", "ui_strike_pahon", 128, 24, wrap(128, 24, f'<path d="M4,14 Q30,6 64,12 T124,10" stroke="{INK}" stroke-width="6" stroke-linecap="round" fill="none" filter="url(#rough)"/><path d="M10,16 Q40,12 70,16" stroke="{ORANGE}" stroke-width="2" fill="none" opacity=".7"/>'), (.5, .5), "파혼 기록 = 먹으로 그은 줄")
    # 4) 12지시 눈금 고리 512×512: 바깥 금 테두리, 12지, 동틀녘(자~인 사이) 붉은 호
    zs = "子丑寅卯辰巳午未申酉戌亥"
    b = f'<circle cx="256" cy="256" r="250" fill="none" stroke="{GOLD}" stroke-width="6"/><circle cx="256" cy="256" r="204" fill="none" stroke="#3B4C7A" stroke-width="3"/>'
    b += f'<path d="M256,6 A250,250 0 0 1 433,79" fill="none" stroke="{RED}" stroke-width="14"/>'
    for i, c in enumerate(zs):
        a = i / 12 * 2 * math.pi - math.pi / 2
        x, y = 256 + 227 * math.cos(a), 256 + 227 * math.sin(a) + 9
        b += f'<text x="{x:.0f}" y="{y:.0f}" font-size="26" fill="#C4C2BC" text-anchor="middle" font-family="Noto Serif KR,serif">{c}</text>'
        for k in range(1, 5):
            a2 = a + k * (2 * math.pi / 12) / 5
            b += f'<path d="M{256+244*math.cos(a2):.0f},{256+244*math.sin(a2):.0f} L{256+236*math.cos(a2):.0f},{256+236*math.sin(a2):.0f}" stroke="#3B4C7A" stroke-width="2"/>'
    add("ui", "ui_time_ring", 512, 512, wrap(512, 512, b), (.5, .5), "시각 고리 · 12지시 눈금 · 붉은 호=동틀녘 · 미니맵 둘레")
    add("ui", "ui_marker_sun", 48, 48, wrap(48, 48, f'<defs><radialGradient id="sg"><stop offset="0" stop-color="#FFE9B0"/><stop offset="1" stop-color="#E8683A" stop-opacity="0"/></radialGradient></defs><circle cx="24" cy="24" r="22" fill="url(#sg)"/><circle cx="24" cy="24" r="9" fill="#FFD27A"/>'), (.5, .5), "해 표시")
    add("ui", "ui_marker_moon", 48, 48, wrap(48, 48, f'<circle cx="24" cy="24" r="22" fill="{HANJI}" opacity=".15" filter="url(#blur)"/><circle cx="24" cy="24" r="10" fill="{HANJI}"/><circle cx="29" cy="21" r="9" fill="{NIGHT}"/>'), (.5, .5), "달 표시")
    # 5) 달 모양 8장 64×64 (그믐~보름~그믐 순환)
    for i in range(8):
        k = i / 8                      # 0=삭, .5=보름
        lit = HANJI; dark = "#232B4A"
        b = f'<circle cx="32" cy="32" r="26" fill="{dark}" stroke="#3B4C7A" stroke-width="2"/>'
        ph = math.cos(2 * math.pi * k)  # 1=삭 → -1=보름
        rx = abs(ph) * 26
        if k < .5:   # 오른쪽부터 차오름
            b += f'<path d="M32,6 A26,26 0 0 1 32,58 A{rx:.1f},26 0 0 {1 if ph>0 else 0} 32,6Z" fill="{lit}"/>'
        else:
            b += f'<path d="M32,6 A26,26 0 0 0 32,58 A{rx:.1f},26 0 0 {0 if ph>0 else 1} 32,6Z" fill="{lit}"/>'
        add("ui", f"ui_moon_{i}", 64, 64, wrap(64, 64, b), (.5, .5), f"달 모양 {i}/8 ({['그믐','초승','상현','차오름','보름','기움','하현','그믐 직전'][i]})")
    # 6) 세로쓰기 이름표 받침 96×256 (먹 판 + 금 테두리 + 위아래 매듭 못)
    b = f'<rect x="8" y="8" width="80" height="240" rx="6" fill="{INK}" stroke="{GOLD}" stroke-width="3"/><rect x="16" y="16" width="64" height="224" fill="none" stroke="#B9A888" stroke-width="1" opacity=".7"/><circle cx="48" cy="22" r="4" fill="{GOLD}"/><circle cx="48" cy="234" r="4" fill="{GOLD}"/>'
    add("ui", "ui_nameplate_v", 96, 256, wrap(96, 256, b), (.5, .5), "세로쓰기 이름표 받침(대화창)")
    # 7) 등급 테두리 5종 96×96 — 색을 못 구분해도 모양으로 구별: 1 가는 먹선 / 2 겹선 / 3 금 겹선 / 4 붉은 인 모서리 / 5 매듭 모서리
    def rr(x, c, w, extra=""): return f'<rect x="{x}" y="{x}" width="{96-2*x}" height="{96-2*x}" rx="6" fill="none" stroke="{c}" stroke-width="{w}"{extra}/>'
    g = {1: rr(4, "#C4C2BC", 2),
         2: rr(4, "#C4C2BC", 3) + rr(10, "#C4C2BC", 1.5),
         3: rr(4, GOLD, 3) + rr(10, GOLD, 1.5),
         4: rr(4, "#C4C2BC", 3) + f'<rect x="64" y="4" width="28" height="28" fill="{RED}"/><text x="78" y="26" font-size="20" fill="{HANJI}" text-anchor="middle" font-family="Noto Serif KR,serif" font-weight="700">印</text>',
         5: rr(4, "#C9B0FF", 3) + "".join(f'<g transform="translate({x},{y})"><circle r="7" fill="none" stroke="#C9B0FF" stroke-width="2.5"/><path d="M-7,0 Q0,-9 7,0 Q0,9 -7,0" fill="none" stroke="#C9B0FF" stroke-width="2"/></g>' for x, y in [(8, 8), (88, 8), (8, 88), (88, 88)])}
    for k, nm in [(1, "흔한: 가는 먹선"), (2, "손본: 겹선"), (3, "귀한: 금 겹선"), (4, "이름 있는: 붉은 인"), (5, "한 벌: 매듭")]:
        add("ui", f"ui_grade_{k}", 96, 96, wrap(96, 96, g[k]), (.5, .5), f"등급 테두리 {k} · {nm} (색 없이도 모양으로 구별)")
    # 8) 처결 대기 고리(혼 나이 색 3) 128×64 바닥 타원 — 흰색 말고 색 그대로, 줄어드는 부분은 코드가 채움
    for nm, c in [("fresh", "#BFE8FF"), ("day", "#FFCC55"), ("old", "#FF6A3D")]:
        b = f'<ellipse cx="64" cy="32" rx="60" ry="28" fill="none" stroke="#0A1022" stroke-width="9" opacity=".6"/><ellipse cx="64" cy="32" rx="60" ry="28" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
        add("ui", f"ui_judge_ring_{nm}", 128, 64, wrap(128, 64, b), (.5, .5), f"처결 대기 고리 · 혼 나이 색({nm}) · 코드가 호 길이로 시간 표시", tint=False)
    # 9) 2차 키트(시각 고리 테두리·막대·도술 틀/아이콘·천도 파혼 버튼·명부 책) — gen_ui_kit2.py
    import gen_ui_kit2
    gen_ui_kit2.run(add)
