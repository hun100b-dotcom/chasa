"""UI 재료 키트 2차: 시각 고리 테두리 · 생명/맺힘 막대 · 도술 4칸 틀 · 도술 액티브 15종 아이콘 · 천도/파혼 버튼 · 명부 책(펼침면·세로 탭).
출처: 기획팀 UI 밑그림(밤 남청·한지·먹·붉은 인) + 기획서 6-4(도술 세 갈래). gen_ui_kit.run() 끝에서 불린다.
색 규칙: 천도 청록·파혼 주황은 그 둘(버튼·표식)에만 쓴다. 갈래 색 = 부름 청록(천도 쪽) / 줄 사슬 청백(중립) / 얼룩 보라(원념).
 금은 깊은 도술 3종·귀한 것에만. 붉은 인은 #B5473F 계열(#E85C41은 화면에서 주황으로 읽혀 쓰지 않는다).
아이콘은 모두 128×128, 어두운 판 + 한지색 그림 + 갈래색 포인트. 글씨는 넣지 않는다(이름은 코드가 쓴다)."""
import math, random
from gen_ui_kit import wrap, torn, HANJI, INK, GOLD, NIGHT, TEAL, ORANGE

DEEP = "#0F1729"; CHAIN = "#BFE8FF"; VIO = "#9A5CFF"; VIO_L = "#C9B0FF"; REDS = "#B5473F"; REDD = "#8E2F2F"; LINE = "#3B4C7A"; PAPER_EDGE = "#B9A888"
ACC = {"bureum": TEAL, "jul": CHAIN, "eolluk": VIO_L}


# ---------------------------------------------------------------- 도술 아이콘 15종
def plate(deep, acc):
    """아이콘 판: 어두운 남청 바탕 + 갈래색 안쪽 가는 선. 깊은 도술은 금 겹선."""
    s = ('<defs><linearGradient id="pl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1D2A4D"/><stop offset="1" stop-color="#0F1729"/></linearGradient></defs>'
         '<rect x="3" y="3" width="122" height="122" rx="14" fill="url(#pl)" stroke="#3B4C7A" stroke-width="3"/>'
         f'<rect x="9" y="9" width="110" height="110" rx="10" fill="none" stroke="{acc}" stroke-width="1.5" opacity=".45"/>')
    if deep:
        s += (f'<rect x="3" y="3" width="122" height="122" rx="14" fill="none" stroke="{GOLD}" stroke-width="3"/>'
              f'<rect x="7" y="7" width="114" height="114" rx="11" fill="none" stroke="{GOLD}" stroke-width="1.2"/>')
    return s


def drop(cx, cy, k=1.0, fill=HANJI, op=.95):
    """혼 모양(물방울). 눈 두 점은 먹."""
    x, y = lambda v: cx + v * k, lambda v: cy + v * k
    return (f'<path d="M{x(0)},{y(-26)} C{x(14)},{y(-8)} {x(20)},{y(2)} {x(20)},{y(12)} A{20*k},{20*k} 0 0 1 {x(-20)},{y(12)} C{x(-20)},{y(2)} {x(-14)},{y(-8)} {x(0)},{y(-26)}Z" fill="{fill}" opacity="{op}"/>'
            f'<circle cx="{x(-7)}" cy="{y(10)}" r="{2.6*k}" fill="{INK}"/><circle cx="{x(7)}" cy="{y(10)}" r="{2.6*k}" fill="{INK}"/>')


def link(cx, cy, ang, acc, w=15, h=9, sw=3):
    return f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="{h/2}" fill="none" stroke="{acc}" stroke-width="{sw}" transform="translate({cx:.1f} {cy:.1f}) rotate({ang:.1f})"/>'


def ring_links(cx, cy, r, n, acc, w=15, h=9, sw=3):
    return "".join(link(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), 360 * i / n + 90 + (0 if i % 2 == 0 else 0), acc, w, h, sw if i % 2 == 0 else sw - 1) for i in range(n))


def arrow(x1, y1, x2, y2, c, sw=3):
    a = math.atan2(y2 - y1, x2 - x1); L = 8
    p1 = (x2 - L * math.cos(a - .5), y2 - L * math.sin(a - .5)); p2 = (x2 - L * math.cos(a + .5), y2 - L * math.sin(a + .5))
    return (f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{c}" stroke-width="{sw}" stroke-linecap="round"/>'
            f'<path d="M{p1[0]:.1f},{p1[1]:.1f} L{x2},{y2} L{p2[0]:.1f},{p2[1]:.1f}" stroke="{c}" stroke-width="{sw}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


def blot(cx, cy, r, fill, seed, op=.9):
    """먹 번짐 같은 불규칙 얼룩."""
    rr = random.Random(seed); pts = []
    for i in range(14):
        a = 2 * math.pi * i / 14; q = r * rr.uniform(.72, 1.15)
        pts.append((cx + q * math.cos(a), cy + q * math.sin(a)))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
    return f'<path d="{d}" fill="{fill}" opacity="{op}" stroke-linejoin="round" stroke="{fill}" stroke-width="6"/>'


def icons():
    H, T_, C, V, G = HANJI, TEAL, CHAIN, VIO_L, GOLD
    ic = []   # (파일 id, 갈래, 깊은가, 한글 이름, 그림)
    # ---- 부름(천도 쪽): 청록 ----
    ic.append(("bureum_1", "bureum", 0, "붙잡아 부르기", drop(64, 70, .95) + f'<path d="M92,56 Q102,70 92,84 M100,46 Q118,70 100,94 M36,56 Q26,70 36,84 M28,46 Q10,70 28,94" stroke="{T_}" stroke-width="4" fill="none" stroke-linecap="round"/><ellipse cx="64" cy="102" rx="26" ry="6" fill="none" stroke="{T_}" stroke-width="3" opacity=".8"/>'))
    ic.append(("bureum_2", "bureum", 0, "혼불 날리기", f'<defs><radialGradient id="fl"><stop offset="0" stop-color="#E8FFF8"/><stop offset=".5" stop-color="{T_}"/><stop offset="1" stop-color="{T_}" stop-opacity="0"/></radialGradient><linearGradient id="tl" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{T_}" stop-opacity="0"/><stop offset="1" stop-color="{T_}" stop-opacity=".9"/></linearGradient></defs>'
        f'<path d="M22,104 C40,86 56,70 78,48 L98,60 C80,76 62,92 22,104Z" fill="url(#tl)"/><circle cx="88" cy="42" r="26" fill="url(#fl)"/><circle cx="88" cy="42" r="10" fill="#F0FFFA"/><circle cx="40" cy="62" r="4" fill="{T_}"/><circle cx="60" cy="36" r="3" fill="{T_}" opacity=".8"/><circle cx="104" cy="82" r="3" fill="{T_}" opacity=".8"/>'))
    ic.append(("bureum_3", "bureum", 0, "이름 비추기", f'<path d="M64,26 L98,100 L30,100Z" fill="{T_}" opacity=".22"/><circle cx="64" cy="24" r="9" fill="{H}"/><circle cx="64" cy="24" r="14" fill="none" stroke="{T_}" stroke-width="2.5"/><rect x="45" y="66" width="38" height="36" rx="3" fill="{H}"/><path d="M57,72 v24 M64,72 v24 M71,72 v24" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>'))
    ic.append(("bureum_4", "bureum", 0, "배웅길", f'<path d="M58,24 L70,24 L104,106 L24,106Z" fill="{DEEP}" stroke="{T_}" stroke-width="3" stroke-linejoin="round"/><path d="M64,34 v10 M64,54 v14 M64,78 v18" stroke="{H}" stroke-width="4" stroke-linecap="round" opacity=".85"/><circle cx="64" cy="20" r="11" fill="{T_}" opacity=".35"/><circle cx="64" cy="20" r="5.5" fill="#F0FFFA"/><path d="M40,92 l-4,-4 M88,92 l4,-4" stroke="{T_}" stroke-width="3" stroke-linecap="round"/>'))
    pts = [(64 + 36 * math.cos(2 * math.pi * i / 7 - math.pi / 2), 64 + 36 * math.sin(2 * math.pi * i / 7 - math.pi / 2)) for i in range(7)]
    ic.append(("bureum_5", "bureum", 1, "일곱 이름", "".join(f'<path d="M{pts[i][0]:.1f},{pts[i][1]:.1f} L{pts[(i+1)%7][0]:.1f},{pts[(i+1)%7][1]:.1f}" stroke="{T_}" stroke-width="2.5" opacity=".7"/>' for i in range(7))
        + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{T_}" stroke="{H}" stroke-width="2"/>' for x, y in pts) + f'<circle cx="64" cy="64" r="9" fill="{H}"/><circle cx="64" cy="64" r="15" fill="none" stroke="{G}" stroke-width="2.5"/>'))
    # ---- 줄(중립): 사슬 청백 ----
    ic.append(("jul_1", "jul", 0, "휘감기", ring_links(64, 64, 36, 8, C, 19, 11, 3.5) + drop(64, 68, .75)))
    ic.append(("jul_2", "jul", 0, "여럿 끌기", "".join(f'<circle cx="{x}" cy="{y}" r="8" fill="{H}"/>' + arrow(x + 10, y, 76, 64 + (y - 64) * .25, C, 3) for x, y in [(26, 34), (20, 64), (26, 94)]) + f'<circle cx="92" cy="64" r="14" fill="none" stroke="{C}" stroke-width="4"/><circle cx="92" cy="64" r="5" fill="{C}"/>'))
    ic.append(("jul_3", "jul", 0, "매듭 걸음", f'<path d="M14,50 h34 M10,64 h40 M14,78 h34" stroke="{H}" stroke-width="4" stroke-linecap="round" opacity=".8"/><path d="M54,64 C54,40 82,40 82,64 C82,88 54,88 54,64Z" fill="none" stroke="{C}" stroke-width="5"/><path d="M82,64 C82,52 98,52 100,64 C98,76 82,76 82,64" fill="none" stroke="{C}" stroke-width="5"/>' + arrow(88, 100, 112, 100, C, 4)))
    ic.append(("jul_4", "jul", 0, "한 줄 꿰기", drop(32, 66, .62) + drop(96, 66, .62) + f'<path d="M12,66 H116" stroke="{C}" stroke-width="4" stroke-linecap="round"/>' + link(64, 66, 0, C, 22, 13, 3.5) + f'<circle cx="64" cy="66" r="3" fill="{C}"/>'))
    ic.append(("jul_5", "jul", 1, "쇠사슬 울", ring_links(64, 64, 38, 12, C, 17, 10, 3.5) + f'<circle cx="64" cy="64" r="7" fill="{H}"/><circle cx="64" cy="64" r="14" fill="none" stroke="{G}" stroke-width="2" opacity=".9"/>'))
    # ---- 얼룩(원념): 보라 ----
    rays = "".join(f'<path d="M{64+22*math.cos(a):.1f},{64+22*math.sin(a):.1f} L{64+44*math.cos(a):.1f},{64+44*math.sin(a):.1f}" stroke="{H}" stroke-width="4" stroke-linecap="round"/>' for a in [i * math.pi / 4 + .2 for i in range(8)])
    ic.append(("eolluk_1", "eolluk", 0, "터뜨리기", blot(64, 64, 20, VIO, 5) + rays + f'<circle cx="64" cy="64" r="8" fill="{V}"/>'))
    ic.append(("eolluk_2", "eolluk", 0, "원념 두르기", f'<circle cx="64" cy="44" r="10" fill="{H}"/><path d="M50,100 L54,58 H74 L78,100Z" fill="{H}"/>' + "".join(f'<path d="M{64+r*math.cos(a):.1f},{64+r*math.sin(a):.1f} A{r},{r} 0 0 1 {64+r*math.cos(a+1.5):.1f},{64+r*math.sin(a+1.5):.1f}" stroke="{VIO}" stroke-width="7" fill="none" stroke-linecap="round"/>' for r, a in [(40, .3), (40, 3.4), (30, 1.8)])))
    ic.append(("eolluk_3", "eolluk", 0, "얼룩 타기", blot(64, 88, 30, VIO, 8, .75) + f'<circle cx="64" cy="46" r="8" fill="{H}"/><path d="M52,56 h24 l-4,26 h-16Z" fill="{H}"/>' + "".join(f'<path d="M{20+i*12},{26+i*0} l8,8 l-8,8" stroke="{V}" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="{.45+.25*i}" transform="translate({0} {4*i})"/>' for i in range(3))))
    ic.append(("eolluk_4", "eolluk", 0, "깨진 이름 던지기", f'<path d="M20,98 C46,92 70,70 92,38" stroke="{V}" stroke-width="5" fill="none" stroke-linecap="round" opacity=".55"/>'
        f'<path d="M70,26 L96,22 L100,48 L82,52Z" fill="{H}"/><path d="M80,28 v18" stroke="{INK}" stroke-width="3.5"/><path d="M96,58 L112,50 L114,74 L102,70Z" fill="{H}"/><path d="M54,44 L72,52 L62,70 L48,62Z" fill="{H}" opacity=".9"/><circle cx="36" cy="82" r="3.5" fill="{V}"/><circle cx="52" cy="96" r="3" fill="{V}"/>'))
    ic.append(("eolluk_5", "eolluk", 1, "검은 갓의 그림자", f'<ellipse cx="64" cy="100" rx="40" ry="8" fill="{VIO}" opacity=".55"/><circle cx="26" cy="104" r="4" fill="{VIO}"/><circle cx="104" cy="106" r="3" fill="{VIO}"/>'
        f'<path d="M44,78 V44 Q64,30 84,44 V78Z" fill="#0A0A12" stroke="{H}" stroke-width="3" stroke-linejoin="round"/><ellipse cx="64" cy="78" rx="46" ry="13" fill="#0A0A12" stroke="{H}" stroke-width="3"/><path d="M46,64 Q64,70 82,64" stroke="{V}" stroke-width="3" fill="none"/>'))
    return ic


# ---------------------------------------------------------------- 본체
def run(add):
    # 1) 시각 고리 테두리 512×512: 위=자시. 12지 눈금 + 구간 호(동틀녘 붉은·낮 한지·해질녘 금·밤 남청). 가운데는 비어 있어 미니맵이 들어간다.
    #    구간 비율은 시계 40분안(동틀녘 2·낮 14·해질녘 2·밤 22 = 5%·35%·5%·55%). 동틀녘이 동쪽(묘, 오른쪽 90°) 중심.
    def arc(a0, a1, r, col, w, op=1):
        p = lambda a: (256 + r * math.sin(math.radians(a)), 256 - r * math.cos(math.radians(a)))
        (x0, y0), (x1, y1) = p(a0), p(a1)
        return f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 {1 if (a1-a0)%360>180 else 0} 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{col}" stroke-width="{w}" opacity="{op}"/>'
    D0, DL, DU, NT = 18, 126, 18, 198      # 각도 폭(합 360)
    s0 = 90 - D0 / 2                       # 동틀녘 시작각
    b = '<circle cx="256" cy="256" r="252" fill="none" stroke="#0A1022" stroke-width="10" opacity=".6"/>'
    b += arc(s0 + D0 + DL + DU, s0 + 360, 228, "#1B2A52", 24) + arc(s0 + D0, s0 + D0 + DL, 228, "#E4D5B8", 24, .85)
    b += arc(s0, s0 + D0, 228, REDS, 24) + arc(s0 + D0 + DL, s0 + D0 + DL + DU, 228, GOLD, 24, .9)
    b += f'<circle cx="256" cy="256" r="252" fill="none" stroke="{GOLD}" stroke-width="5"/><circle cx="256" cy="256" r="213" fill="none" stroke="{GOLD}" stroke-width="2.5" opacity=".8"/><circle cx="256" cy="256" r="240" fill="none" stroke="{INK}" stroke-width="1.5" opacity=".7"/>'
    for i, c in enumerate("子丑寅卯辰巳午未申酉戌亥"):
        a = math.radians(i * 30)
        x, y = 256 + 228 * math.sin(a), 256 - 228 * math.cos(a) + 9
        b += f'<text x="{x:.0f}" y="{y:.0f}" font-size="24" fill="{INK}" text-anchor="middle" font-family="Noto Serif KR,serif" font-weight="700">{c}</text>' if (s0 + D0 <= i * 30 <= s0 + D0 + DL) else f'<text x="{x:.0f}" y="{y:.0f}" font-size="24" fill="#C4C2BC" text-anchor="middle" font-family="Noto Serif KR,serif" font-weight="700">{c}</text>'
        for k in range(1, 5):
            a2 = math.radians(i * 30 + k * 6)
            b += f'<path d="M{256+252*math.sin(a2):.0f},{256-252*math.cos(a2):.0f} L{256+244*math.sin(a2):.0f},{256-244*math.cos(a2):.0f}" stroke="{GOLD}" stroke-width="2" opacity=".7"/>'
    for a in (0, 90, 180, 270):   # 사방 매듭 못
        b += f'<circle cx="{256+252*math.sin(math.radians(a)):.0f}" cy="{256-252*math.cos(math.radians(a)):.0f}" r="7" fill="{GOLD}" stroke="#0A1022" stroke-width="2"/>'
    add("ui", "ui_time_ring_frame", 512, 512, wrap(512, 512, b), (.5, .5), "시각 고리 테두리(미니맵 둘레, 가운데 투명) · 위=자시 · 구간 호: 동틀녘 붉음 가운데=동(90°, 폭 18°)·낮 한지(126°)·해질녘 금(18°)·밤 남청(198°), 시계방향 · 12지 글씨(낮 구간 먹색) · 해·달 표시는 ui_marker_sun/moon을 반지름 228px 위에 돌린다")

    # 2) 생명 막대(왼쪽 아래 붉은 띠): 틀 320×32(9조각, 좌우 모서리 16), 채움 304×16, 잔상 304×16
    b = (f'<rect x="2" y="2" width="316" height="28" rx="8" fill="{DEEP}" fill-opacity=".88" stroke="{GOLD}" stroke-width="2" stroke-opacity=".75"/>'
         f'<rect x="7" y="7" width="306" height="18" rx="5" fill="#0A1022" stroke="{INK}" stroke-width="1.5"/>'
         f'<circle cx="6" cy="16" r="3" fill="{GOLD}"/><circle cx="314" cy="16" r="3" fill="{GOLD}"/>')
    add("ui", "ui_bar_vital_frame", 320, 32, wrap(320, 32, b), (0, .5), "생명 막대 틀 · 9조각(좌우 16px) · 안쪽 홈 x7~313,y7~25에 채움이 들어간다")
    for nm, c0, c1, op, note in [("fill", REDS, REDD, 1, "생명 채움(붉은 인 색) · 코드가 가로로 잘라 쓴다"), ("ghost", HANJI, "#CDBB98", .7, "생명 잔상(맞은 만큼 한지색이 잠깐 남았다 줄어듦)")]:
        d = f'<defs><linearGradient id="vf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/></linearGradient></defs>'
        bb = f'<rect x="0" y="0" width="304" height="16" rx="4" fill="url(#vf)" opacity="{op}"/>' + ('<rect x="0" y="2" width="304" height="3" rx="1.5" fill="#fff" opacity=".18"/>' if nm == "fill" else "")
        add("ui", f"ui_bar_vital_{nm}", 304, 16, wrap(304, 16, bb, d), (0, .5), note)

    # 3) 맺힘 막대(적 머리 위): 한 줄 96×14 / 보스·귀한 적 금 테두리 / 덩어리(두 줄) 96×26. 채움 88×8
    def gframe(h, col, sw, rows):
        s = f'<rect x="1.5" y="1.5" width="93" height="{h-3}" rx="{h/2-1.5 if rows==1 else 7}" fill="#0A1022" fill-opacity=".85" stroke="{col}" stroke-width="{sw}"/>'
        for r in range(rows):
            y = 3 + r * 12
            s += f'<rect x="4" y="{y+1.5 if rows==1 else y+1}" width="88" height="8" rx="3" fill="#16213E"/>'
        return s
    add("ui", "ui_bar_gyeol_frame", 96, 14, wrap(96, 14, gframe(14, HANJI, 1.5, 1).replace('y="4.5"', 'y="3"')), (.5, .5), "맺힘 막대 틀(한 줄) · 안쪽 홈 x4~92")
    add("ui", "ui_bar_gyeol_frame_gold", 96, 14, wrap(96, 14, gframe(14, GOLD, 2, 1)), (.5, .5), "맺힘 막대 틀(보스·귀한 적: 금 테두리)")
    add("ui", "ui_bar_gyeol_frame_x2", 96, 28, wrap(96, 28, gframe(28, HANJI, 1.5, 2)), (.5, .5), "맺힘 막대 틀(덩어리: 두 줄). 위 줄 홈 y4~12, 아래 줄 홈 y16~24")
    d = f'<defs><linearGradient id="gf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E6F6FF"/><stop offset="1" stop-color="#7FB8E0"/></linearGradient></defs>'
    add("ui", "ui_bar_gyeol_fill", 88, 8, wrap(88, 8, '<rect width="88" height="8" rx="3" fill="url(#gf)"/>', d), (0, .5), "맺힘 채움(사슬 청백)")
    add("ui", "ui_bar_gyeol_ghost", 88, 8, wrap(88, 8, f'<rect width="88" height="8" rx="3" fill="{HANJI}" opacity=".65"/>'), (0, .5), "맺힘 잔상")

    # 4) 도술 4칸 틀
    def corner(x, y, sx, sy, col):
        return f'<path d="M{x},{y+sy*14} V{y} H{x+sx*14}" stroke="{col}" stroke-width="3" fill="none" stroke-linecap="square"/>'
    base = lambda stroke, sw, fill: (f'<rect x="3" y="3" width="90" height="90" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    slot = base(HANJI, 2.5, "#0F1729") + f'<rect x="9" y="9" width="78" height="78" rx="5" fill="none" stroke="{LINE}" stroke-width="1.5"/>' + corner(7, 7, 1, 1, GOLD) + corner(89, 7, -1, 1, GOLD) + corner(7, 89, 1, -1, GOLD) + corner(89, 89, -1, -1, GOLD)
    add("ui", "ui_skill_slot", 96, 96, wrap(96, 96, slot), (.5, .5), "도술 칸 틀(기본) · 안쪽 78×78에 아이콘을 맞춘다 · 4칸 + 무기 기술 칸에 같은 틀")
    hot = base(REDS, 4, "#2A1620") + f'<rect x="9" y="9" width="78" height="78" rx="5" fill="{REDS}" opacity=".22"/>' + corner(7, 7, 1, 1, HANJI) + corner(89, 7, -1, 1, HANJI) + corner(7, 89, 1, -1, HANJI) + corner(89, 89, -1, -1, HANJI)
    add("ui", "ui_skill_slot_hot", 96, 96, wrap(96, 96, hot), (.5, .5), "도술 칸 틀(누름/발동 중: 붉은 인 테두리와 붉은 번짐)")
    ready = base(HANJI, 2.5, "#0F1729") + f'<rect x="3" y="3" width="90" height="90" rx="8" fill="none" stroke="{HANJI}" stroke-width="7" opacity=".22" filter="url(#blur)"/>' + corner(7, 7, 1, 1, GOLD) + corner(89, 7, -1, 1, GOLD) + corner(7, 89, 1, -1, GOLD) + corner(89, 89, -1, -1, GOLD)
    add("ui", "ui_skill_slot_ready", 96, 96, wrap(96, 96, ready), (.5, .5), "도술 칸 틀(쓸 수 있게 된 순간 0.3초 번쩍: 기본 틀 위에 겹쳐 페이드)")
    cool = ('<defs><radialGradient id="cw" cx=".5" cy=".5" r=".7"><stop offset="0" stop-color="#0A1022" stop-opacity=".78"/><stop offset="1" stop-color="#0A1022" stop-opacity=".92"/></radialGradient></defs>'
            '<rect x="5" y="5" width="86" height="86" rx="6" fill="url(#cw)"/>')
    add("ui", "ui_skill_slot_cool", 96, 96, wrap(96, 96, cool), (.5, .5), "도술 칸 재사용 대기 덮개(먹 번짐). 코드가 Image.Radial360으로 시계 방향으로 걷어낸다")
    add("ui", "ui_skill_key_tab", 32, 22, wrap(32, 22, f'<rect x="1.5" y="1.5" width="29" height="19" rx="3" fill="{HANJI}" stroke="{INK}" stroke-width="1.5"/>'), (.5, .5), "단축키 쪽지(한지 작은 표). 글씨(1·2·3·4·Q)는 코드가 먹색으로 쓴다")
    plate9 = (f'<path d="{torn(256,128,16,21,2.2)}" fill="{DEEP}" fill-opacity=".9" stroke="{GOLD}" stroke-width="2" stroke-opacity=".7"/>'
              f'<path d="{torn(256,128,16,21,2.2)}" fill="none" stroke="{HANJI}" stroke-width="1" opacity=".25" transform="translate(128 64) scale(.95) translate(-128 -64)"/>')
    add("ui", "ui_skill_bar_plate", 256, 128, wrap(256, 128, plate9), (.5, .5), "도술 줄 바탕(9조각, 모서리 32px). 슬롯 틀 4칸 + 무기칸 아래에 깐다")
    for k, c in ACC.items():
        add("ui", f"ui_skill_pip_{k}", 16, 16, wrap(16, 16, f'<circle cx="8" cy="8" r="6" fill="{c}" stroke="#0A1022" stroke-width="2"/>'), (.5, .5), f"도술 갈래 표식 점({ {'bureum':'부름','jul':'줄','eolluk':'얼룩'}[k] }) · 칸 모서리에 붙임")

    # 5) 도술 액티브 15종 아이콘 128×128
    for fid, br, deep, nm, art in icons():
        acc = ACC[br]
        body = plate(deep, acc) + f'<g stroke-linejoin="round">{art}</g>'
        add("ui", f"icon_skill_{fid}", 128, 128, wrap(128, 128, body), (.5, .5), f"도술 아이콘 · {nm}" + (" (깊은 도술: 금 겹선)" if deep else "") + f" · 갈래색={ {'bureum':'청록(부름)','jul':'사슬 청백(줄)','eolluk':'보라(얼룩)'}[br] }")

    # 6) 천도 / 파혼 버튼 128×128 + 길게 누르기 홈 고리
    def btn(col, pressed, sym, wash):
        fill = f'<circle cx="64" cy="64" r="56" fill="url(#bd)"/>'
        d = f'<defs><radialGradient id="bd" cx=".5" cy=".4" r=".7"><stop offset="0" stop-color="{"#24365F" if not pressed else wash}"/><stop offset="1" stop-color="#0A1022"/></radialGradient></defs>'
        ring = f'<circle cx="64" cy="64" r="58" fill="none" stroke="{col}" stroke-width="{7 if pressed else 5}"/><circle cx="64" cy="64" r="49" fill="none" stroke="#0A1022" stroke-width="4" opacity=".6"/>'
        glow = f'<circle cx="64" cy="64" r="60" fill="none" stroke="{col}" stroke-width="10" opacity=".35" filter="url(#blur)"/>' if pressed else ""
        return d + glow + fill + ring + sym
    cheon = (f'<path d="M34,86 C54,84 56,66 70,56 C80,50 90,46 96,40" stroke="{TEAL}" stroke-width="4" fill="none" stroke-linecap="round" opacity=".65" stroke-dasharray="1 9"/>'
             + drop(60, 74, .62) + f'<path d="M52,44 L64,30 L76,44" stroke="{HANJI}" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="64" cy="24" r="6" fill="#F0FFFA"/><circle cx="64" cy="24" r="11" fill="{TEAL}" opacity=".35"/>')
    pah = (f'<path d="M64,30 C76,46 84,56 84,68 A20,20 0 0 1 64,88 L58,68 L68,58 L56,44Z" fill="{HANJI}" opacity=".95"/><path d="M64,30 C54,44 44,56 44,68 A20,20 0 0 0 58,87 L54,68 L62,58 L50,46Z" fill="{HANJI}" opacity=".95" transform="translate(-6 2)"/>'
           + "".join(f'<path d="M{64+30*math.cos(a):.1f},{66+30*math.sin(a):.1f} L{64+44*math.cos(a):.1f},{66+44*math.sin(a):.1f}" stroke="{ORANGE}" stroke-width="4.5" stroke-linecap="round"/>' for a in [math.radians(x) for x in (-70, -35, 0, 35, 70, 110, 145, 180, 215, 250)]))
    for nm, col, sym, wash, note in [("cheondo", TEAL, cheon, "#1E5E58", "천도 버튼(길게 누르기 · 청록)"), ("pahon", ORANGE, pah, "#7A3A1E", "파혼 버튼(톡 · 주황)")]:
        add("ui", f"ui_btn_{nm}", 128, 128, wrap(128, 128, btn(col, False, sym, wash)), (.5, .5), note + " · 혼이 무릎 꿇었을 때만 공격 버튼 옆에 뜬다")
        add("ui", f"ui_btn_{nm}_pressed", 128, 128, wrap(128, 128, btn(col, True, sym, wash)), (.5, .5), note + " · 눌림(안이 물들고 테두리가 두꺼워짐)")
    add("ui", "ui_btn_hold_ring", 144, 144, wrap(144, 144, f'<circle cx="72" cy="72" r="66" fill="none" stroke="#0A1022" stroke-width="10" opacity=".7"/><circle cx="72" cy="72" r="66" fill="none" stroke="{LINE}" stroke-width="4"/>'), (.5, .5), "천도 버튼 둘레의 길게 누르기 홈 고리. 청록 채움은 코드가 Image.Radial360으로 그린다(흰색 호 스프라이트 따로 필요 없음)")

    # 7) 명부 책: 펼침면 1024×640, 세로 탭 2종(64×168, 9조각 위아래 28)
    W, Hh = 1024, 640
    r = random.Random(77)
    fib = "".join(f'<path d="M{r.uniform(40,980):.0f},{r.uniform(40,600):.0f} l{r.uniform(-24,24):.0f},{r.uniform(-7,7):.0f}" stroke="#D9C7A6" stroke-width="1" opacity=".5"/>' for _ in range(260))
    pgL, pgR = torn(512, 600, 20, 31, 2.5), torn(512, 600, 20, 32, 2.5)
    d = ('<linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F6ECD9"/><stop offset="1" stop-color="#E4D5B8"/></linearGradient>'
         '<linearGradient id="gut" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2A2A38" stop-opacity="0"/><stop offset=".5" stop-color="#2A2A38" stop-opacity=".38"/><stop offset="1" stop-color="#2A2A38" stop-opacity="0"/></linearGradient>')
    b = (f'<rect x="2" y="2" width="{W-4}" height="{Hh-4}" rx="14" fill="{INK}" stroke="{GOLD}" stroke-width="3"/>'
         f'<rect x="12" y="12" width="{W-24}" height="{Hh-24}" rx="8" fill="none" stroke="{GOLD}" stroke-width="1" opacity=".5"/>'
         f'<path d="{pgL}" fill="url(#pg)" stroke="{PAPER_EDGE}" stroke-width="2" transform="translate(14 20)"/><path d="{pgR}" fill="url(#pg)" stroke="{PAPER_EDGE}" stroke-width="2" transform="translate(498 20)"/>{fib}'
         f'<rect x="452" y="22" width="120" height="596" fill="url(#gut)"/>'
         + "".join(f'<circle cx="512" cy="{y}" r="5" fill="{INK}"/><path d="M512,{y-40} V{y+40}" stroke="{REDS}" stroke-width="3" opacity=".9"/>' for y in (96, 208, 320, 432, 544)))
    b += "".join(f'<path d="M505,{y} h14" stroke="{REDS}" stroke-width="3.5" stroke-linecap="round"/>' for y in (96, 208, 320, 432, 544))
    add("ui", "ui_book_spread", W, Hh, wrap(W, Hh, b, d), (.5, .5), "명부 책 펼침면(한지 두 쪽 + 가운데 오침 붉은 실 + 먹 표지 테두리). 장비·도술·능력·인·기록 화면의 바탕. 한지 안쪽 여백 약 40px 안에 내용을 놓는다")
    tab = lambda fill, extra: (f'<path d="M64,3 H22 Q3,3 3,22 V146 Q3,165 22,165 H64Z" fill="{fill}" stroke="{PAPER_EDGE if fill==HANJI else GOLD}" stroke-width="2.5"/>' + extra)
    add("ui", "ui_book_tab", 64, 168, wrap(64, 168, tab(INK, f'<path d="M14,28 V140" stroke="#B9A888" stroke-width="1" opacity=".5"/><circle cx="14" cy="14" r="3" fill="{GOLD}"/><circle cx="14" cy="154" r="3" fill="{GOLD}"/>')), (1, .5), "책 등 세로 탭(눌리지 않은 것: 먹 판). 오른쪽 끝이 책 왼쪽 표지에 닿는다 · 9조각(위아래 28px)")
    add("ui", "ui_book_tab_active", 64, 168, wrap(64, 168, tab(HANJI, f'<path d="M14,28 V140" stroke="{PAPER_EDGE}" stroke-width="1" opacity=".7"/><rect x="6" y="6" width="8" height="12" fill="{REDS}"/><circle cx="14" cy="154" r="3" fill="{REDS}"/>')), (1, .5), "책 등 세로 탭(선택됨: 한지색이라 펼침면과 이어져 보임 + 붉은 인 표식)")
