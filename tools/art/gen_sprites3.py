"""② 검은여울 변형: 역병 사망자 혼(3단계 × 서기/무릎) + 지역 HUD 변형.
gen_sprites.py 의 main() 이 혼 그림을 다 쓴 뒤 run(MANIFEST, SRC)를 부른다.
방식: 기본 혼 SVG 를 읽어, 그 위에 '역병 표식'(석회색 반점 + 지워진 이름 먹줄)만 덧칠한다.
왜 덧칠인가: 단계 색(하늘/노랑/주황)이 그대로 남아야 처결 대기 시간(10/7/4초)이 한눈에 읽힌다."""
import os, random, re

LIME = "#C8C3A0"; INKB = "#0F1729"; GOLD = "#D4A94E"; DEEP = "#0F1729"; NIGHT = "#16213E"
SRC = None; MAN = None


def add(folder, name, w, h, svg, pivot, note, tint=False):
    d = os.path.join(SRC, folder); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + ".svg"), "w").write(svg)
    MAN.append({"file": f"{folder}/{name}.png", "w": w, "h": h, "pivotX": pivot[0], "pivotY": pivot[1], "ppu": 128, "tint": tint, "note": note})


def plague(kind, kneel):
    base = f"soul_{['fresh','day','old'][kind]}{'_kneel' if kneel else ''}"
    s = open(os.path.join(SRC, "enemies", base + ".svg")).read()
    rnd = random.Random(40 + kind * 2 + kneel)
    y0 = 150 if kneel else 128          # 몸통 시작 높이(서 있을 때/무릎 꿇었을 때)
    marks = ""
    # 석회색 반점: 몸통 위 불규칙 4~6개. 반투명이라 단계 색이 비친다
    for _ in range(5):
        x, y, r = 72 + rnd.random() * 48, y0 + 6 + rnd.random() * (60 if not kneel else 50), 4 + rnd.random() * 5
        marks += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{LIME}" opacity=".78"/>'
    # 지워진 이름: 가슴을 가로지르는 먹줄 두 번(명단에서 이름을 지운 표시) — 갓 죽은 혼은 선명, 오래될수록 흐려진다
    op = [.95, .7, .5][kind]
    marks += f'<path d="M70,{y0+22} L124,{y0+16} M72,{y0+30} L120,{y0+28}" stroke="{INKB}" stroke-width="4.5" stroke-linecap="round" opacity="{op}"/>'
    # 머리 위 석회 가루(역병막 석회): 아주 옅은 점
    for _ in range(6):
        marks += f'<circle cx="{60+rnd.random()*76:.0f}" cy="{(y0-70)+rnd.random()*60:.0f}" r="1.8" fill="{LIME}" opacity=".7"/>'
    out = s.replace("</svg>", marks + "</svg>")
    add("enemies", base + "_plague", 192, 256, out, (96 / 192, 236 / 256),
        f"② 검은여울 역병 사망자 · {['갓 죽은','해 넘긴','오래된'][kind]} 혼{' · 무릎 꿇음' if kneel else ''} (석회 반점 + 지워진 이름 먹줄)")


def hud_region():
    # ② 전용 HUD: 금 테두리 → 석회색 테두리 + 모서리 파임. 같은 크기·같은 9-slice 라 코드는 이미지만 갈아 끼우면 된다.
    save = lambda n, w, h, b, d="", p=(.5, .5), note="", t=False: add("hud", n, w, h,
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{d}</defs>{b}</svg>', p, note, t)
    save("gauge_frame_r2", 192, 24, f'<rect x="1" y="1" width="190" height="22" rx="4" fill="#0A1022" stroke="{LIME}" stroke-width="2"/><rect x="5" y="5" width="182" height="14" rx="2" fill="{NIGHT}"/><path d="M1,8 L8,1 M191,16 L184,23" stroke="{LIME}" stroke-width="2"/>', note="② 게이지 틀(석회 테두리 · 모서리 파임) · 9-slice 좌우 12px")
    save("panel_hanji_r2", 128, 128, f'<rect x="2" y="2" width="124" height="124" rx="6" fill="{NIGHT}" stroke="{LIME}" stroke-width="3" opacity=".96"/><rect x="10" y="10" width="108" height="108" rx="3" fill="none" stroke="#3B4C7A" stroke-width="2"/><path d="M10,34 V10 H34 M94,10 H118 V34 M118,94 V118 H94 M34,118 H10 V94" stroke="{LIME}" stroke-width="3" fill="none"/><path d="M60,10 h8 M60,118 h8" stroke="#0F1729" stroke-width="5"/>', note="② 패널 · 9-slice 24px")
    save("timer_ring_bg_r2", 128, 128, f'<circle cx="64" cy="64" r="54" fill="none" stroke="#0A1022" stroke-width="12" opacity=".85"/><circle cx="64" cy="64" r="60" fill="none" stroke="{LIME}" stroke-width="2" opacity=".7"/><circle cx="64" cy="64" r="48" fill="none" stroke="{LIME}" stroke-width="2" stroke-dasharray="4 6" opacity=".5"/>', note="② 처결 타이머 링 배경(점선 안쪽 = 번호 칸 느낌)")
    sky = '<linearGradient id="sky2" x1="0" x2="1"><stop offset="0" stop-color="#5A6B8C"/><stop offset=".25" stop-color="#2C3350"/><stop offset=".7" stop-color="#0F1729"/><stop offset="1" stop-color="#3A5A7C"/></linearGradient>'
    save("night_bar_r2", 480, 32, f'<rect x="2" y="6" width="476" height="20" rx="4" fill="url(#sky2)" stroke="{LIME}" stroke-width="2"/>', sky, note="② 하룻밤 시간 바(해 질 녘이 붉지 않고 흐린 회청 — 비·안개 읍성)")


def region_soul(region, kind, kneel):
    """③ 붉은재: 번호 패(이름 대신 번호) + 녹슨 화살 / ④ 쇳골: 석탄 가루 + 목패. 단계 색은 그대로 둔다."""
    base = f"soul_{['fresh','day','old'][kind]}{'_kneel' if kneel else ''}"
    s = open(os.path.join(SRC, "enemies", base + ".svg")).read()
    rnd = random.Random(90 + kind * 3 + kneel + (50 if region == 4 else 0))
    y0 = 150 if kneel else 128
    m = ""
    if region == 3:
        m += f'<rect x="84" y="{y0+8}" width="26" height="32" rx="2" fill="{HANJI_}" opacity=".92" stroke="#2A2A38" stroke-width="2"/><path d="M90,{y0+18} h14 M90,{y0+26} h14 M90,{y0+34} h10" stroke="#2A2A38" stroke-width="2.5"/>'
        m += f'<path d="M122,{y0+4} L98,{y0+44} M122,{y0+4} l-7,2 M122,{y0+4} l1,7" stroke="#8A4A32" stroke-width="3.5" stroke-linecap="round"/>'
    else:
        for _ in range(14):
            m += f'<circle cx="{66+rnd.random()*64:.0f}" cy="{y0+rnd.random()*(70 if not kneel else 56):.0f}" r="{1.5+rnd.random()*2.5:.1f}" fill="#14141C" opacity=".8"/>'
        m += f'<path d="M88,{y0+4} L108,{y0+4} L106,{y0+30} L90,{y0+30} Z" fill="#8A6A3E" stroke="#3E2A14" stroke-width="2"/><circle cx="98" cy="{y0+10}" r="2" fill="#3E2A14"/><path d="M93,{y0+20} h10" stroke="#3E2A14" stroke-width="2"/>'
    add("enemies", base + f"_r{region}", 192, 256, s.replace("</svg>", m + "</svg>"), (96 / 192, 236 / 256),
        f"{'③ 붉은재 번호 병사 혼(번호 패 + 녹슨 화살)' if region == 3 else '④ 쇳골 광부 혼(석탄 가루 + 목패)'} · {['갓 죽은','해 넘긴','오래된'][kind]}{' · 무릎' if kneel else ''}")


HANJI_ = "#F3E7D3"


def hud_region_n(region, col, accent_note):
    sfx = f"_r{region}"
    sv = lambda n, w, h, b, d="", note="": add("hud", n, w, h, f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{d}</defs>{b}</svg>', (.5, .5), note)
    sv("gauge_frame" + sfx, 192, 24, f'<rect x="1" y="1" width="190" height="22" rx="11" fill="#0A1022" stroke="{col}" stroke-width="2"/><rect x="5" y="5" width="182" height="14" rx="7" fill="{NIGHT}"/>', note=f"{accent_note} 게이지 틀 · 9-slice 12px")
    sv("panel_hanji" + sfx, 128, 128, f'<rect x="2" y="2" width="124" height="124" rx="10" fill="{NIGHT}" stroke="{col}" stroke-width="3" opacity=".96"/><rect x="10" y="10" width="108" height="108" rx="6" fill="none" stroke="#3B4C7A" stroke-width="2"/><path d="M10,34 V10 H34 M94,10 H118 V34 M118,94 V118 H94 M34,118 H10 V94" stroke="{col}" stroke-width="3" fill="none"/>', note=f"{accent_note} 패널 · 9-slice 24px")
    sv("timer_ring_bg" + sfx, 128, 128, f'<circle cx="64" cy="64" r="54" fill="none" stroke="#0A1022" stroke-width="12" opacity=".85"/><circle cx="64" cy="64" r="60" fill="none" stroke="{col}" stroke-width="2" opacity=".7"/><circle cx="64" cy="64" r="48" fill="none" stroke="{col}" stroke-width="2" opacity=".4"/>', note=f"{accent_note} 처결 타이머 링 배경")


def fx_weapons():
    """무기 3계열 타격 이펙트(각 3프레임, 512×256, 중심=공격 기준점 (256,128)). 쿼터뷰라 바닥 타원 위에 눕혀 그린다."""
    import math
    W, H, CX, CY = 512, 256, 256, 128
    wrap = lambda b, d="": f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{d}<filter id="b3"><feGaussianBlur stdDeviation="3"/></filter></defs>{b}</svg>'
    for f in range(3):
        # 요령: 번지는 소리 고리(금색 → 흰색), 바깥으로 갈수록 얇고 흐려진다
        r0 = [70, 130, 200][f]; b = ""
        for k in range(3):
            r = r0 - k * 34
            if r > 10: b += f'<ellipse cx="{CX}" cy="{CY}" rx="{r}" ry="{r/2}" fill="none" stroke="{GOLD}" stroke-width="{[8,5,3][f]}" opacity="{[.95,.7,.45][k]*[1,.85,.6][f]}"/>'
        b += f'<ellipse cx="{CX}" cy="{CY}" rx="{r0*.5}" ry="{r0*.25}" fill="#fff" opacity="{[.5,.3,.1][f]}" filter="url(#b3)"/>'
        for i in range(8):
            t = i / 8 * 2 * math.pi
            b += f'<circle cx="{CX+r0*.9*math.cos(t):.0f}" cy="{CY+r0*.45*math.sin(t):.0f}" r="3" fill="#FFF3C4" opacity=".8"/>'
        add("fx", f"fx_bell_{f}", W, H, wrap(b), (.5, .5), "무기 요령 타격 · 소리 고리 반경 약 3m(제안)")
        # 삼지창: 앞으로 뻗는 세 줄기 찌르기 선(가운데가 가장 김)
        L = [150, 230, 190][f]; b = ""
        for dy, ln in [(-26, .7), (0, 1), (26, .7)]:
            b += f'<path d="M{CX-60},{CY+dy} L{CX-60+L*ln},{CY+dy+dy*.2}" stroke="{CHAIN}" stroke-width="{[10,14,8][f]}" stroke-linecap="round" opacity=".9"/><path d="M{CX-60},{CY+dy} L{CX-60+L*ln},{CY+dy+dy*.2}" stroke="#fff" stroke-width="3" opacity=".7"/>'
        b += f'<path d="M{CX-60+L},{CY-34} L{CX-60+L+34},{CY} L{CX-60+L},{CY+34}" fill="none" stroke="#fff" stroke-width="4" opacity="{[.4,.9,.5][f]}"/>'
        add("fx", f"fx_trident_{f}", W, H, wrap(b), (.5, .5), "무기 삼지창 타격 · 직선 관통(제안 폭 3칸)")
        # 명부 붓: 먹 한 획(굵었다 가늘어지는 호) + 먹 방울, 가장자리 기억색
        a = [.45, 1, 1][f]; b = ""
        path = f"M{CX-180},{CY+50} Q{CX-40},{CY-70} {CX+190},{CY+10}"
        b += f'<path d="{path}" stroke="{MEMORY_}" stroke-width="{[14,30,20][f]}" fill="none" stroke-linecap="round" opacity="{.5*a}" filter="url(#b3)"/>'
        b += f'<path d="{path}" stroke="#0A0A12" stroke-width="{[8,22,14][f]}" fill="none" stroke-linecap="round" opacity="{a}" stroke-dasharray="{[260,520,520][f]} 600"/>'
        for i in range(5 if f else 2):
            b += f'<circle cx="{CX+60+i*34}" cy="{CY-30+((i*37)%50)}" r="{3+(i%3)*2}" fill="#0A0A12" stroke="{MEMORY_}" stroke-width="1.5"/>'
        add("fx", f"fx_brush_{f}", W, H, wrap(b), (.5, .5), "무기 명부 붓 타격 · 먹 한 획 호(제안 부채꼴)")


MEMORY_ = "#C9B0FF"; CHAIN = "#BFE8FF"


def run(manifest, src):
    global SRC, MAN
    SRC, MAN = src, manifest
    for k in range(3):
        plague(k, False); plague(k, True)
    fx_weapons()
    import gen_ui_kit
    gen_ui_kit.run(add)
    import gen_gear
    gen_gear.run(add, SRC)
    hud_region()
    for r in (3, 4):
        for k in range(3):
            region_soul(r, k, False); region_soul(r, k, True)
    hud_region_n(3, '#B0704F', '③')
    hud_region_n(4, '#B8A26A', '④')
