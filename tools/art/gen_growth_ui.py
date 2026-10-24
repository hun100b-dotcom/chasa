"""성장 UI 시안 4화면 × PC(1280×720)/폰(390×844) = 8장 생성기.
화면: ① 인벤토리+장비 7칸 ② 도술 트리 3갈래 ③ 능력치 창 ④ 넋/인 조합.
상태: 도형 시안(레이아웃·위계·터치 크기 확인용). 슬롯 7종·능력치 목록은 '제안'이며 기획 확정 전.
폰 규칙: 터치 목표 ≥ 48px, 본문 ≥ 14px, 한 손 엄지 닿는 하단에 주 버튼."""
import os
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "ui")
NIGHT, DEEP, TEAL, HANJI, RED, GOLD, INK = "#16213E", "#0F1729", "#4FA8A0", "#F3E7D3", "#E85C41", "#D4A94E", "#2A2A38"
CHAIN, CHEON, VIO = "#BFE8FF", "#5FE3C0", "#C9B0FF"
GRADE = {"일반": "#F3E7D3", "공들인": "#4FA8A0", "귀한": "#D4A94E", "이름 있는": "#E85C41"}
SOUL = ["#BFE8FF", "#FFCC55", "#FF6A3D", "#9A5CFF"]
SLOTS = ["철삭(무기)", "흑립(머리)", "도포(몸)", "붉은 띠(허리)", "미투리(발)", "노리개", "인장"]

def T(x, y, s, size=15, fill=HANJI, anchor="start", bold=False):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" text-anchor="{anchor}"{" font-weight=\"bold\"" if bold else ""}>{s}</text>'
def R(x, y, w, h, fill="none", stroke=None, sw=2, rx=8, op=1):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st} opacity="{op}"/>'
def frame(w, h, title, body, mobile):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="sans-serif"><rect width="{w}" height="{h}" fill="{DEEP}"/>'
            f'<defs><radialGradient id="bgg" cx="50%" cy="30%" r="80%"><stop offset="0" stop-color="#1D2C52"/><stop offset="1" stop-color="{DEEP}"/></radialGradient></defs><rect width="{w}" height="{h}" fill="url(#bgg)"/>'
            + R(8, 8, w-16, h-16, "none", GOLD, 2, 14, .6)
            + T(24 if not mobile else 20, 44 if not mobile else 40, title, 24 if not mobile else 20, HANJI, "start", True)
            + body + '</svg>')
def slot(x, y, s, label="", grade=None, icon=True):
    c = GRADE.get(grade, "#3B4C7A")
    o = R(x, y, s, s, "#0F1729", c, 3, 10)
    if grade and icon: o += f'<path d="M{x+s*.3},{y+s*.7} L{x+s*.5},{y+s*.25} L{x+s*.7},{y+s*.7} Z" fill="{c}" opacity=".8"/>'
    if label: o += T(x+s/2, y+s+16, label, 12, HANJI, "middle")
    return o
def tabs(w, y, names, active, mobile):
    o = ""; tw = (w - 32) / len(names)
    for i, n in enumerate(names):
        a = i == active
        o += R(16 + i * tw, y, tw - 6, 44, NIGHT if a else DEEP, GOLD if a else "#3B4C7A", 2, 8) + T(16 + i * tw + (tw - 6) / 2, y + 28, n, 15, GOLD if a else HANJI, "middle", a)
    return o
def btn(x, y, w, h, label, col=GOLD):
    return R(x, y, w, h, "#241A0F", col, 3, 12) + T(x + w / 2, y + h / 2 + 6, label, 17, col, "middle", True)

TABS = ["장비", "도술", "능력", "조합"]

def inv(mobile):
    W, H = (390, 844) if mobile else (1280, 720)
    b = ""
    if mobile:
        b += tabs(W, 60, TABS, 0, True)
        # 장비 7칸: 가운데 실루엣 + 둘레 슬롯 (상단 영역 320px)
        b += R(16, 116, W-32, 330, NIGHT, "#3B4C7A", 2, 12, .9)
        b += f'<path d="M{W/2-18},300 L{W/2-12},186 L{W/2+12},186 L{W/2+18},300 Z" fill="{INK}"/><ellipse cx="{W/2}" cy="170" rx="30" ry="7" fill="#000"/><rect x="{W/2-8}" y="150" width="16" height="20" fill="#000"/>'
        pos = [(24, 150), (W/2-26, 126), (24, 240), (W-76, 240), (W/2-26, 380), (W-76, 150), (24, 330)]
        for (x, y), n, g in zip(pos, SLOTS, ["귀한", "공들인", "이름 있는", "일반", "공들인", None, "일반"]):
            b += slot(x, y, 52, "", g) + T(x + 26, y + 66, n.split('(')[0], 12, HANJI, 'middle')
        b += T(W/2, 436, "슬롯을 누르면 아래 목록이 해당 종류로 걸러집니다", 12, TEAL, "middle")
        # 인벤토리 그리드 5열
        b += T(20, 478, "가방 18/30", 15, HANJI, "start", True)
        for i in range(15):
            x, y = 16 + (i % 5) * 72, 492 + (i // 5) * 72
            b += slot(x, y, 64, "", ["일반", "공들인", "귀한", "일반", None][i % 5] if i < 9 else None)
        b += btn(16, H - 76, W - 32, 56, "착용하기")
    else:
        b += tabs(520, 60, TABS, 0, False)
        b += R(24, 120, 480, 560, NIGHT, "#3B4C7A", 2, 12, .9)
        b += f'<path d="M264,420 L272,230 L296,230 L304,420 Z" fill="{INK}"/><ellipse cx="284" cy="212" rx="44" ry="9" fill="#000"/><rect x="274" y="180" width="20" height="30" fill="#000"/><path d="M270,320 L298,320" stroke="{RED}" stroke-width="6"/>'
        pos = [(60, 200), (254, 130), (60, 320), (436-24, 320), (254, 560), (436-24, 200), (60, 440)]
        for (x, y), n, g in zip(pos, SLOTS, ["귀한", "공들인", "이름 있는", "일반", "공들인", None, "일반"]):
            b += slot(x, y, 68, n, g)
        b += T(284, 664, "철삭 · 흑립 · 도포 · 붉은 띠 · 미투리 · 노리개 · 인장", 12, TEAL, "middle")
        b += T(540, 90, "가방 18/30", 18, HANJI, "start", True)
        for i in range(30):
            x, y = 540 + (i % 8) * 90, 110 + (i // 8) * 90
            b += slot(x, y, 80, "", ["일반", "공들인", "귀한", "일반", None, "이름 있는", None, "공들인"][i % 8] if i < 18 else None)
        b += R(540, 480, 700, 160, NIGHT, GOLD, 2, 12, .95) + T(560, 512, "월화의 방울 (이름 있는)", 18, RED, "start", True) + T(560, 542, "파혼 반경 +1m · 천도 캐스팅 +0.2초", 15, HANJI) + T(560, 570, "'열두째 잔이 엎어진 뒤로, 이 방울은 소리를 내지 않는다.'", 14, TEAL)
        b += btn(1000, 600, 220, 52, "착용하기")
    return frame(W, H, "장비", b, mobile)

def tree(mobile):
    W, H = (390, 844) if mobile else (1280, 720)
    b = ""; branches = [("붙잡아 부르기", CHEON, ["넓게", "빠르게", "끌어당김", "연쇄", "정지"]), ("휘감기", CHAIN, ["오래", "넓게", "독", "가시", "결박"]), ("터뜨리기", RED, ["반경", "연쇄", "불꽃", "역류", "파문"])]
    if mobile:
        b += tabs(W, 60, TABS, 1, True)
        b += T(20, 130, "넋 14", 18, CHEON, "start", True)
        for bi, (n, c, nodes) in enumerate(branches):
            x = 20 + bi * 120
            b += T(x + 50, 170, n, 14, c, "middle", True)
            b += f'<path d="M{x+50},190 L{x+50},{190+4*86}" stroke="{c}" stroke-width="4" opacity=".4"/>'
            for k, nm in enumerate(nodes):
                y = 190 + k * 86
                st = 0 if k < 2 else (1 if k == 2 else 2)
                b += f'<circle cx="{x+50}" cy="{y+28}" r="28" fill="{DEEP}" stroke="{c if st<2 else "#3B4C7A"}" stroke-width="{4 if st==1 else 3}" opacity="{1 if st<2 else .6}"/>' + (f'<circle cx="{x+50}" cy="{y+28}" r="16" fill="{c}"/>' if st == 0 else "")
                b += T(x + 50, y + 74, nm, 12, HANJI, "middle")
        b += R(16, H - 150, W - 32, 70, NIGHT, GOLD, 2, 12) + T(28, H - 120, "휘감기 · 독 (선택됨)", 15, CHAIN, "start", True) + T(28, H - 98, "묶은 적이 초당 피해를 입음 · 비용 넋 3", 13, HANJI)
        b += btn(16, H - 66, W - 32, 52, "익히기 (넋 3)")
    else:
        b += tabs(520, 60, TABS, 1, False)
        b += T(1240, 90, "넋 14", 20, CHEON, "end", True)
        for bi, (n, c, nodes) in enumerate(branches):
            x = 130 + bi * 380
            b += T(x, 140, n, 20, c, "middle", True)
            b += f'<path d="M{x},170 L{x},{170+4*100}" stroke="{c}" stroke-width="4" opacity=".4"/>'
            for k, nm in enumerate(nodes):
                y = 170 + k * 100; st = 0 if k < 2 else (1 if k == 2 else 2)
                b += f'<circle cx="{x}" cy="{y+30}" r="32" fill="{DEEP}" stroke="{c if st<2 else "#3B4C7A"}" stroke-width="{4 if st==1 else 3}" opacity="{1 if st<2 else .6}"/>' + (f'<circle cx="{x}" cy="{y+30}" r="18" fill="{c}"/>' if st == 0 else "") + T(x + 50, y + 36, nm, 15, HANJI)
        b += R(640, 560, 600, 130, NIGHT, GOLD, 2, 12, .95) + T(664, 596, "휘감기 · 독", 20, CHAIN, "start", True) + T(664, 626, "묶은 적이 초당 피해를 입음", 15, HANJI) + btn(1000, 620, 220, 52, "익히기 (넋 3)")
    return frame(W, H, "도술", b, mobile)

STATS = [("맺힘 저항(체력)", 120, 200, "+14"), ("철삭 길이", 5.5, 10, "+0.5m"), ("천도 속도", 2.0, 4, "-0.1초"), ("파혼 반경", 3.0, 6, "+1m"), ("이동 속도", 5, 8, ""), ("시야 반경", 100, 120, "")]
def stats(mobile):
    W, H = (390, 844) if mobile else (1280, 720)
    b = ""
    if mobile:
        b += tabs(W, 60, TABS, 2, True)
        for i, (n, v, mx, d) in enumerate(STATS):
            y = 130 + i * 92
            b += R(16, y, W - 32, 80, NIGHT, "#3B4C7A", 2, 12, .9) + T(30, y + 28, n, 16, HANJI, "start", True) + T(W - 30, y + 28, f"{v}", 18, GOLD, "end", True)
            b += R(30, y + 44, W - 60, 12, DEEP, None, 0, 6) + R(30, y + 44, (W - 60) * v / mx, 12, TEAL, None, 0, 6)
            if d: b += T(W - 30, y + 72, f"장비 {d}", 13, CHEON, "end")
        b += btn(16, H - 76, W - 32, 56, "자세히 (수치 근거)")
    else:
        b += tabs(520, 60, TABS, 2, False)
        b += R(24, 120, 560, 560, NIGHT, "#3B4C7A", 2, 12, .9) + f'<path d="M284,560 L292,260 L316,260 L324,560 Z" fill="{INK}"/><ellipse cx="304" cy="240" rx="50" ry="10" fill="#000"/><rect x="292" y="200" width="24" height="36" fill="#000"/>'
        for i, (n, v, mx, d) in enumerate(STATS):
            y = 130 + i * 90
            b += T(620, y + 24, n, 18, HANJI, "start", True) + T(1240, y + 24, f"{v}", 20, GOLD, "end", True) + R(620, y + 40, 620, 14, DEEP, None, 0, 7) + R(620, y + 40, 620 * v / mx, 14, TEAL, None, 0, 7)
            if d: b += T(1240, y + 74, f"장비 {d}", 14, CHEON, "end")
    return frame(W, H, "능력", b, mobile)

def combine(mobile):
    W, H = (390, 844) if mobile else (1280, 720)
    b = ""
    if mobile:
        b += tabs(W, 60, TABS, 3, True)
        b += T(20, 130, "넋 (재료)", 15, HANJI, "start", True)
        for i in range(4): b += R(16 + i * 90, 142, 82, 82, DEEP, SOUL[i], 3, 12) + f'<circle cx="{57+i*90}" cy="{176}" r="14" fill="{SOUL[i]}"/>' + T(57 + i * 90, 212, f"×{[7,4,2,1][i]}", 14, HANJI, "middle")
        b += R(16, 250, W - 32, 300, NIGHT, GOLD, 2, 14, .95)
        for i in range(3): b += R(40 + i * 108, 280, 92, 92, DEEP, "#3B4C7A", 3, 12) + T(86 + i * 108, 336, "넋", 15, "#3B4C7A", "middle")
        b += f'<path d="M{W/2-14},396 L{W/2},420 L{W/2+14},396" fill="{GOLD}"/>' + R(W/2-52, 430, 104, 104, DEEP, VIO, 4, 14) + T(W/2, 488, "룬", 20, VIO, "middle", True)
        b += R(16, 570, W - 32, 90, NIGHT, "#3B4C7A", 2, 12) + T(30, 600, "인(因): 흐림", 16, GOLD, "start", True) + T(30, 626, "인이 또렷할수록 룬 효과가 커집니다.", 13, HANJI) + T(30, 648, "없음  ·  흐림  ·  또렷", 13, TEAL)
        b += btn(16, H - 76, W - 32, 56, "조합하기")
    else:
        b += tabs(520, 60, TABS, 3, False)
        b += T(24, 130, "넋 (재료)", 18, HANJI, "start", True)
        for i in range(4): b += R(24, 150 + i * 120, 140, 100, DEEP, SOUL[i], 3, 12) + f'<circle cx="68" cy="{200+i*120}" r="18" fill="{SOUL[i]}"/>' + T(150, 208 + i * 120, f"×{[7,4,2,1][i]}", 18, HANJI, "end", True) + T(94, 240 + i * 120, ["갓 죽은", "해 넘긴", "오래된", "덩어리"][i], 12, HANJI, "middle")
        b += R(220, 120, 560, 560, NIGHT, GOLD, 2, 14, .95)
        for i in range(3): b += R(280 + i * 150, 170, 120, 120, DEEP, "#3B4C7A", 3, 12) + T(340 + i * 150, 240, "넋", 18, "#3B4C7A", "middle")
        b += f'<path d="M486,320 L500,350 L514,320" fill="{GOLD}"/>' + R(436, 370, 128, 128, DEEP, VIO, 4, 16) + T(500, 442, "룬", 24, VIO, "middle", True)
        b += btn(380, 590, 240, 56, "조합하기")
        b += R(820, 120, 420, 270, NIGHT, "#3B4C7A", 2, 12) + T(844, 160, "인(因): 흐림", 20, GOLD, "start", True) + T(844, 194, "인이 또렷할수록 룬 효과가 커집니다.", 15, HANJI) + T(844, 232, "없음   ·   흐림   ·   또렷", 15, TEAL) + R(844, 250, 372, 12, DEEP, None, 0, 6) + R(844, 250, 372 * .45, 12, GOLD, None, 0, 6)
    return frame(W, H, "조합", b, mobile)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [("equip", inv), ("skilltree", tree), ("stats", stats), ("combine", combine)]:
        for mob in (False, True):
            fp = os.path.join(OUT, f"growth_{name}_{'phone' if mob else 'pc'}.svg")
            open(fp, "w", encoding="utf-8").write(fn(mob)); print(fp)
