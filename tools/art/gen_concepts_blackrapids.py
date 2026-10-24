"""검은여울 읍성(② 관할) 타일·소품 실루엣 시트 + 3호 보스 B-03 서 의원 콘셉트 시트 생성기.
왜 코드로 그리나: 도형 초안은 수정이 잦아서, 숫자만 바꾸면 시트 전체가 다시 그려지게 한다.
규칙: 작품명 참조 없음. 색은 docs/art/palette-tokens.json 의 값만 쓰고, 이 관할 전용 색은 '제안'으로 따로 표시한다."""
import os
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "concepts")

# --- 팔레트 (palette-tokens.json) ---
BG, DEEP, TEAL, HANJI, RED, GOLD, INK = "#0F1729", "#16213E", "#4FA8A0", "#F3E7D3", "#E85C41", "#D4A94E", "#2A2A38"
CHAIN, CHEON, VIOLET, STAIN = "#BFE8FF", "#5FE3C0", "#C9B0FF", "#7B4FD6"
# --- 검은여울 전용 제안색 (오너 승인 전까지 '제안') ---
LIME, WET, ASH = "#C8C3A0", "#3A4457", "#5A5A63"   # 석회/젖은 돌/재

def diamond(cx, cy, fill, w=64, h=32, stroke=BG):
    return f'<path d="M{cx},{cy-h} L{cx+w},{cy} L{cx},{cy+h} L{cx-w},{cy} Z" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
def t(x, y, s, fill=HANJI, size=14, anchor="middle", bold=False):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" text-anchor="{anchor}"{" font-weight=\"bold\"" if bold else ""}>{s}</text>'

# ---------- 1. 타일·소품 시트 ----------
def tiles_props():
    W, H = 1260, 1520
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="sans-serif"><rect width="{W}" height="{H}" fill="{BG}"/>']
    o += [t(24, 38, "검은여울 읍성 타일·소품 실루엣 시트 (쿼터뷰 2:1, 도형 초안)", HANJI, 22, "start", True),
          t(24, 60, "② 관할 4구역: 장터거리 · 동헌 터 · 역병막 · 무덤골. 타일 한 칸 = 128×64px. 검정으로 칠해도 읽히는지로 먼저 확정. 작품명 참조 없음.", TEAL, 12, "start"),
          t(24, 98, "A. 바닥 타일 8종 (구역 색은 솔고개보다 차갑고 젖어 있다 — 성벽 안은 흙이 아니라 돌)", GOLD, 15, "start", True)]
    tiles = [("젖은 돌길", WET, "장터거리 · 비 온 뒤 번들, 물웅덩이 반사", "stone"),
             ("장터 흙", "#5B4D3E", "좌판 사이 밟힌 흙", "dirt"),
             ("동헌 박석", "#4A4F5E", "관아 터 · 네모 석판이 가지런함", "slab"),
             ("그을린 바닥", "#2F2D33", "불탄 문서함 주변, 재가 흩어짐", "ash"),
             ("역병막 멍석", "#8A7B58", "짚 멍석. 석회 가루가 뿌려져 하얗다", "straw"),
             ("석회 선", LIME, "막 둘레에 그은 하얀 줄 = 들어가면 안 되는 선", "lime"),
             ("무덤골 잔디", "#2F4535", "이름 없는 봉분 사이 마른 풀", "grass"),
             ("검은 물", "#1D2C47", "여울 가장자리. 걸으면 느려지는 칸(제안)", "water")]
    for i, (name, c, desc, kind) in enumerate(tiles):
        cx, cy = 110 + (i % 4) * 300, 170 + (i // 4) * 150
        o.append(f'<g transform="translate({cx},{cy})">{diamond(0,0,c)}')
        if kind == "stone":
            o.append(f'<path d="M-40,-4 L-10,-18 M-8,6 L24,-8 M10,14 L40,0 M-24,12 L-6,4" stroke="{TEAL}" stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/>')
        elif kind == "slab":
            o.append(f'<path d="M-32,-8 L0,-24 L32,-8 L0,8 Z M0,8 L0,24" fill="none" stroke="{BG}" stroke-width="2"/>')
        elif kind == "ash":
            o.append(f'<circle cx="-14" cy="-4" r="9" fill="{ASH}" opacity=".5"/><circle cx="18" cy="6" r="7" fill="{ASH}" opacity=".5"/>')
        elif kind == "straw":
            o.append(f'<path d="M-44,0 L-12,-16 M-26,10 L12,-8 M0,18 L40,-2" stroke="#6B5E40" stroke-width="3"/><circle cx="-6" cy="2" r="10" fill="{LIME}" opacity=".35"/>')
        elif kind == "lime":
            o.append(f'<path d="M-52,6 L52,-6" stroke="{BG}" stroke-width="1" opacity=".4"/>')
        elif kind == "grass":
            o.append(f'<path d="M-30,6 l4,-10 M-6,-6 l4,-10 M20,8 l4,-10 M30,-2 l3,-8" stroke="#5E7A4C" stroke-width="2"/>')
        elif kind == "water":
            o.append(f'<ellipse cx="0" cy="0" rx="34" ry="12" fill="none" stroke="{CHAIN}" stroke-opacity=".4"/>')
        o.append('</g>')
        o += [t(cx, cy+62, name, HANJI, 14, bold=True), t(cx, cy+80, desc, TEAL, 11)]
    o.append(t(24, 520, "B. 소품 16종 (footprint = 차지하는 칸 수, 앵커 = 발 닿는 점)", GOLD, 15, "start", True))
    props = [("성벽 조각", "2×1", "wall"), ("장터 좌판", "2×1", "stall"), ("등롱 장대", "1×1", "lantern"), ("곤장대", "1×1", "rack"),
             ("우물", "1×1", "well"), ("옥 창살", "2×1", "bars"), ("불탄 문서함", "1×1", "chest"), ("약장 (보스방)", "2×1", "yakjang"),
             ("역병막 움막", "2×2", "hut"), ("멍석 환자(혼 자리)", "1×1", "mat"), ("약탕 화로", "1×1", "brazier"), ("석회 가마니", "1×1", "sack"),
             ("이름 없는 봉분", "2×2", "mound"), ("빈 비석 받침", "1×1", "stele"), ("번호 팻말", "1×1", "sign"), ("분류 상자 (보스방)", "1×1", "box")]
    for i, (name, fp, kind) in enumerate(props):
        cx, cy = 150 + (i % 4) * 320, 680 + (i // 4) * 210
        o.append(f'<rect x="{cx-140}" y="{cy-132}" width="280" height="170" rx="10" fill="{HANJI}" opacity=".9"/>')
        g = [f'<g transform="translate({cx},{cy})" fill="#000">']
        if kind == "wall": g.append('<path d="M-66,0 L-66,-78 L-48,-78 L-48,-92 L-30,-92 L-30,-78 L-12,-78 L-12,-92 L6,-92 L6,-78 L24,-78 L24,-92 L42,-92 L42,-78 L66,-78 L66,0 L0,30 Z"/>')
        elif kind == "stall": g.append('<path d="M-76,-52 L0,-96 L76,-52 L58,-46 L58,-50 L-58,-50 L-58,-46 Z"/><path d="M-52,-40 L-46,0 M52,-40 L46,0 M-52,-40 L52,-40" stroke="#000" stroke-width="8" fill="none"/><rect x="-30" y="-30" width="60" height="14"/>')
        elif kind == "lantern": g.append('<rect x="-3" y="-90" width="6" height="90"/><rect x="-16" y="-110" width="32" height="26" rx="6"/><ellipse cx="0" cy="2" rx="18" ry="7"/>')
        elif kind == "rack": g.append('<path d="M-30,0 L-30,-60 L30,-60 L30,0 M-30,-40 L30,-40 M-22,0 L-22,-20 M22,0 L22,-20" stroke="#000" stroke-width="7" fill="none"/>')
        elif kind == "well": g.append('<ellipse cx="0" cy="-10" rx="30" ry="14"/><rect x="-30" y="-10" width="60" height="22"/><path d="M-26,-12 L-26,-60 L26,-60 L26,-12" stroke="#000" stroke-width="6" fill="none"/>')
        elif kind == "bars": g.append('<path d="M-50,0 L-50,-70 M-30,0 L-30,-70 M-10,0 L-10,-70 M10,0 L10,-70 M30,0 L30,-70 M50,0 L50,-70 M-56,-72 L56,-72" stroke="#000" stroke-width="7"/>')
        elif kind == "chest": g.append('<path d="M-30,0 L-30,-34 L0,-48 L30,-34 L30,0 L0,16 Z"/><path d="M-12,-50 L-4,-70 L6,-52" stroke="#000" stroke-width="3" fill="none"/>')
        elif kind == "yakjang": g.append('<rect x="-48" y="-96" width="96" height="96"/><path d="M-48,-64 L48,-64 M-48,-32 L48,-32 M-16,-96 L-16,0 M16,-96 L16,0" stroke="#fff" stroke-opacity=".25" stroke-width="2"/><rect x="-14" y="-22" width="28" height="18" fill="none" stroke="'+CHEON+'" stroke-width="3"/>')
        elif kind == "hut": g.append('<path d="M-76,-30 Q0,-130 76,-30 L60,-22 L60,0 L-60,0 L-60,-22 Z"/><path d="M-12,0 L-12,-30 L12,-30 L12,0 Z" fill="#DDD3BF"/>')
        elif kind == "mat": g.append('<path d="M-36,0 L0,-14 L36,0 L0,14 Z"/><ellipse cx="0" cy="-16" rx="10" ry="14"/>')
        elif kind == "brazier": g.append('<path d="M-18,0 L-14,-26 L14,-26 L18,0 Z"/><ellipse cx="0" cy="-30" rx="22" ry="8"/><path d="M-6,-40 q6,-18 12,0" stroke="#000" stroke-width="4" fill="none"/>')
        elif kind == "sack": g.append('<path d="M-22,0 Q-30,-30 -12,-46 L12,-46 Q30,-30 22,0 Z"/>')
        elif kind == "mound": g.append('<path d="M-70,0 Q-60,-66 0,-70 Q60,-66 70,0 L0,34 Z"/>')
        elif kind == "stele": g.append('<rect x="-18" y="-76" width="36" height="76" rx="14"/><rect x="-30" y="-8" width="60" height="12"/>')
        elif kind == "sign": g.append('<rect x="-3" y="-60" width="6" height="60"/><rect x="-22" y="-82" width="44" height="30"/>')
        else: g.append('<path d="M-26,0 L-26,-30 L0,-44 L26,-30 L26,0 L0,14 Z"/>')
        g.append('</g>')
        o += g
        o += [t(cx, cy+58, f"{name}  ({fp})", HANJI, 13, bold=True)]
    o += [t(24, 1505, "※ 검정 실루엣만으로 구별되는지가 합격선. 구역 전용 제안색(석회 #C8C3A0 · 젖은 돌 #3A4457 · 재 #5A5A63)은 오너 승인 전 palette-tokens.json 에 넣지 않는다.", TEAL, 12, "start"), '</svg>']
    return "".join(o)

# ---------- 2. 보스 B-03 서 의원 ----------
def seo():
    W, H = 1260, 1060
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="sans-serif"><rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<defs><filter id="gl"><feGaussianBlur stdDeviation="5"/></filter></defs>',
         t(24, 38, "3호 보스 B-03 서 의원 — 콘셉트 시트 (기록형, 역병막)", HANJI, 22, "start", True),
         t(24, 60, "사또의 명으로 환자 이름을 명단에서 지운 의원. 한(恨): 진짜 명단을 약장 맨 아래 칸에 숨겼다. 작품명 참조 없음.", TEAL, 12, "start")]

    def figure(cx, cy, pose):
        g = [f'<g transform="translate({cx},{cy})">']
        # 그림자
        g.append('<ellipse cx="0" cy="0" rx="62" ry="18" fill="#000" opacity=".5"/>')
        # 약장(등 뒤 방패) — 서랍 격자
        g.append(f'<g transform="translate(0,-8)"><rect x="-104" y="-250" width="208" height="170" fill="{INK}" stroke="{RIM(pose)}" stroke-width="3"/>')
        for r in range(4):
            for c in range(7):
                g.append(f'<rect x="{-100+c*29}" y="{-246+r*28}" width="26" height="24" fill="#1B1B26" stroke="{GOLD}" stroke-opacity=".5"/>')
        # 맨 아래 칸: 진짜 명단
        glow = CHEON if pose == "weak" else "#1B1B26"
        if pose == "weak":
            g.append(f'<rect x="-100" y="-134" width="200" height="50" fill="{CHEON}" opacity=".55" filter="url(#gl)"/>')
        g.append(f'<rect x="-100" y="-134" width="200" height="50" fill="{glow}" stroke="{CHEON}" stroke-width="2"/></g>')
        # 몸: 먹물 번호가 적힌 긴 도포
        g.append(f'<path d="M-46,-6 L-34,-150 L34,-150 L46,-6 Q0,14 -46,-6 Z" fill="#20202B" stroke="{HANJI}" stroke-opacity=".25"/>')
        for i, (x, y, s) in enumerate([(-18, -120, "七"), (10, -96, "九"), (-8, -70, "二"), (16, -44, "十一"), (-20, -28, "三")]):
            g.append(t(x, y, s, HANJI, 14))
        # 복건 모자 + 얼굴 없는 먹빛
        g.append(f'<path d="M-24,-150 L-20,-196 L20,-196 L24,-150 Z" fill="#111119"/><ellipse cx="0" cy="-206" rx="22" ry="26" fill="#111119"/>')
        g.append(f'<ellipse cx="0" cy="-168" rx="16" ry="14" fill="{HANJI}" opacity=".85"/>')   # 천으로 가린 얼굴
        # 팔·도구
        if pose == "idle":
            g.append(f'<path d="M-34,-136 L-70,-80 L-62,-60" stroke="#20202B" stroke-width="14" stroke-linecap="round" fill="none"/>'
                     f'<path d="M34,-136 L62,-100 L70,-70" stroke="#20202B" stroke-width="14" stroke-linecap="round" fill="none"/>'
                     f'<rect x="60" y="-72" width="20" height="26" fill="{RED}"/>')   # 도장
        elif pose == "stamp":
            g.append(f'<path d="M34,-136 L56,-220 L52,-262" stroke="#20202B" stroke-width="14" stroke-linecap="round" fill="none"/>'
                     f'<rect x="38" y="-300" width="32" height="40" fill="{RED}" stroke="{HANJI}" stroke-width="2"/>'
                     f'<text x="54" y="-272" fill="{HANJI}" font-size="20" text-anchor="middle">七</text>'
                     f'<path d="M-34,-136 L-70,-100" stroke="#20202B" stroke-width="14" stroke-linecap="round"/>')
        else:  # weak: 서랍을 연 상태, 도장 내려놓음
            g.append(f'<path d="M-34,-136 L-70,-96 L-60,-76" stroke="#20202B" stroke-width="14" stroke-linecap="round" fill="none"/>'
                     f'<path d="M34,-136 L50,-100 L40,-86" stroke="#20202B" stroke-width="14" stroke-linecap="round" fill="none"/>'
                     f'<rect x="-84" y="-60" width="20" height="26" fill="{RED}" opacity=".5"/>')
        g.append('</g>')
        return "".join(g)
    def RIM(p): return {"idle": VIOLET, "stamp": RED, "weak": CHEON}[p]

    o.append(t(24, 100, "A. 세 가지 상태 (같은 실루엣, 한 가지 변수만 다름)", GOLD, 15, "start", True))
    for cx, pose, name, sub in [(220, "idle", "기본", "약장을 등에 진 채 번호를 읽는다"),
                                (620, "stamp", "도장 번호 낙인 예비동작", "붉은 도장을 높이 든 순간 = 피할 신호"),
                                (1020, "weak", "약점 노출 (밑칸 열림)", "맨 아래 칸이 청록으로 빛남 = 진짜 명단")]:
        o.append(figure(cx, 470, pose))
        o += [t(cx, 510, name, HANJI, 15, bold=True), t(cx, 530, sub, TEAL, 11)]

    # 전투방 번호 칸
    o.append(t(24, 590, "B. 전투방 — 바닥 번호 칸 분류 패턴 (5×5 일부)", GOLD, 15, "start", True))
    n = 5
    for gy in range(n):
        for gx in range(n):
            cx = 330 + (gx - gy) * 56
            cy = 700 + (gx + gy) * 28
            hot = (gx, gy) in [(1, 1), (3, 2), (2, 3)]
            c = "#5A2A2A" if hot else "#2B3040"
            o.append(diamond(cx, cy, c, 56, 28, "#0F1729"))
            o.append(t(cx, cy+4, str(gx*n+gy+1), RED if hot else HANJI, 12))
    o += [t(330, 960, "붉은 칸 = 곧 낙인이 찍힐 번호 (0.8초 예고 후 폭발)", RED, 12)]
    steps = ["1) 서 의원이 번호 3개를 부른다 (소리 + 칸이 붉게 점멸).",
             "2) 불린 번호의 칸에 서 있으면 낙인을 맞는다. 안 불린 칸으로 옮겨 피한다.",
             "3) 3회 피하면 의원이 기침하며 멈춘다 (약점 노출 3초): 맨 아래 칸이 열려 진짜 명단이 빛난다.",
             "4) 이때 때리면 맺힘 크게 감소. 천도하면 명단이 명부에 실려 이름혼의 인이 '없음→흐림'.",
             "5) 파혼하면 약장이 터져 회복약 대량 · 업 +3 (설계서 기준)."]
    for i, s in enumerate(steps):
        o.append(t(640, 700 + i * 44, s, HANJI, 13, "start"))

    # 팔레트
    o.append(t(24, 1020, "사용색:", GOLD, 13, "start", True))
    for i, (c, lab) in enumerate([(INK, "먹빛 #2A2A38"), (HANJI, "한지 #F3E7D3"), (RED, "붉은 도장 #E85C41"), (GOLD, "금 #D4A94E"), (CHEON, "약점 #5FE3C0"), (VIOLET, "기억 테두리 #C9B0FF")]):
        o.append(f'<rect x="{110+i*190}" y="1006" width="22" height="22" fill="{c}" stroke="{HANJI}" stroke-opacity=".3"/>' + t(138+i*190, 1022, lab, HANJI, 11, "start"))
    o.append('</svg>')
    return "".join(o)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [("P2-040-blackrapids-tiles-props.svg", tiles_props), ("P2-041-boss-b03-seo-uiwon.svg", seo)]:
        open(os.path.join(OUT, name), "w", encoding="utf-8").write(fn())
        print("wrote", name)
