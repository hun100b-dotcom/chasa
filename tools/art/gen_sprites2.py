"""도술 이펙트 3종(각 3프레임)과 장비 아이콘(3칸 × 3등급 + 이름 있는 물건 1) + 등급 테두리 4종.
gen_sprites.py 의 main() 이 끝에 run()을 부른다. 좌표계는 gen_sprites 와 같다."""
import gen_sprites as G
from gen_sprites import save, rg, lg, HANJI, AMBIENT, GOLD, RED, CHEON, CHAIN, MEMORY, DEEP, NIGHT

W, H = 512, 256            # 이펙트 캔버스: 바닥에 눕는 2:1 타원(쿼터뷰), 중심 = 대상 발 위치
CX, CY = 256, 128


def ell(r, **kw):
    a = " ".join(f'{k.replace("_","-")}="{v}"' for k, v in kw.items())
    return f'<ellipse cx="{CX}" cy="{CY}" rx="{r}" ry="{r/2}" {a}/>'


def fx_call(f):   # 붙잡아 부르기: 청록 고리가 좁혀 들며 혼불이 가운데로 끌려온다(대기 시간 +3초)
    r = [236, 170, 96][f]
    d = rg("fa", CHEON, .35, 0)
    b = f'<ellipse cx="{CX}" cy="{CY}" rx="{r+10}" ry="{(r+10)/2}" fill="url(#fa)"/>' + ell(r, fill="none", stroke=CHEON, stroke_width=6, opacity=[.5, .8, 1][f])
    b += ell(r * .72, fill="none", stroke="#EFFFFA", stroke_width=2, opacity=.55, stroke_dasharray="10 8")
    import math
    for i in range(10):
        t = i / 10 * 2 * math.pi + f * .35
        rr = r * (1.05 - .45 * (f / 2)) - (i % 3) * 14
        x, y = CX + rr * math.cos(t), CY + rr * math.sin(t) / 2
        b += f'<path d="M{x:.0f},{y-14:.0f} q-8,12 0,20 q8,-8 0,-20" fill="{CHEON}" opacity=".9"/><circle cx="{x:.0f}" cy="{y-2:.0f}" r="3" fill="#EFFFFA"/>'
    save("fx", f"fx_call_{f}", W, H, b, d, pivot=(.5, .5), note="도술 붙잡아 부르기 · 6m 반경")


def fx_bind(f):   # 휘감기: 철삭이 나선으로 감겨 조여든다(적 1.5초 묶기)
    r = [220, 150, 84][f]
    b = ""
    for k, sc in enumerate([1, .78, .56]):
        b += ell(r * sc, fill="none", stroke=CHAIN, stroke_width=9 - k * 2, stroke_dasharray="22 9", opacity=.95 - k * .15)
        b += ell(r * sc, fill="none", stroke="#fff", stroke_width=2, stroke_dasharray="22 9", opacity=.35)
    b += f'<path d="M{CX-r},{CY} Q{CX},{CY-r*.9} {CX+r},{CY}" stroke="{CHAIN}" stroke-width="5" fill="none" stroke-dasharray="14 8" opacity=".6"/>'
    b += f'<circle cx="{CX}" cy="{CY}" r="{12 + f*4}" fill="{RED}" opacity="{.3 + f*.2}"/>'
    save("fx", f"fx_bind_{f}", W, H, b, "", pivot=(.5, .5), note="도술 휘감기 · 4m 반경 · 1.5초 묶기")


def fx_burst(f):  # 터뜨리기: 원념 얼룩이 부풀어 터진다(반경 2.5m 맺힘 40)
    import math
    d = rg("ba", "#7B4FD6", .8, 0) + rg("bb", RED, .9, 0)
    r = [70, 140, 210][f]
    b = f'<ellipse cx="{CX}" cy="{CY}" rx="{r}" ry="{r/2}" fill="url(#ba)"/>'
    if f == 0:
        b += f'<ellipse cx="{CX}" cy="{CY}" rx="60" ry="30" fill="#2A103C"/><path d="M{CX-50},{CY} L{CX-10},{CY-8} L{CX+10},{CY+10} L{CX+52},{CY-2}" stroke="{RED}" stroke-width="4" fill="none"/>'
    else:
        for i in range(14):
            t = i / 14 * 2 * math.pi + .2
            r1, r2 = r * .35, r * (.8 + (i % 3) * .08)
            x1, y1 = CX + r1 * math.cos(t), CY + r1 * math.sin(t) / 2
            x2, y2 = CX + r2 * math.cos(t), CY + r2 * math.sin(t) / 2
            b += f'<path d="M{x1:.0f},{y1:.0f} L{x2:.0f},{y2:.0f}" stroke="{RED if i % 2 else "#9A5CFF"}" stroke-width="{9 - f*2}" stroke-linecap="round"/>'
        b += ell(r * .9, fill="none", stroke=RED, stroke_width=6 - f * 2, opacity=1 - f * .35)
        if f == 2:
            b += ell(30, fill="#1A0F2A", opacity=.6)    # 터진 자리에 남는 그을음
    save("fx", f"fx_burst_{f}", W, H, b, d, pivot=(.5, .5), note="도술 터뜨리기 · 얼룩 폭파 2.5m")


# ---- 장비 아이콘 (96×96) ----
ICON = 96
FRAMES = [("common", HANJI), ("crafted", AMBIENT), ("rare", GOLD), ("named", RED)]
GR = {0: ("#A98A5E", "#6B4A2E", "#8A8A92"), 1: ("#7A5A34", "#4FA8A0", "#B6C2CC"), 2: ("#5C3A1E", "#D4A94E", "#F0DFA8")}


def club(g):       # 육모방망이: 여섯 모, 위가 굵다. 손본=쇠띠+청록 끈, 귀한=금띠+문양
    wood, trim, hi = GR[g]
    b = f'<g transform="translate(48,48) rotate(40)"><path d="M-9,-38 L9,-38 L7,38 L-7,38 Z" fill="{wood}"/><path d="M-9,-38 L-2,-38 L-2,38 L-7,38 Z" fill="#fff" opacity=".14"/>'
    if g >= 1:
        b += f'<rect x="-10" y="-18" width="20" height="6" fill="{trim}"/><rect x="-9" y="18" width="18" height="6" fill="{trim}"/>'
    if g == 2:
        b += f'<path d="M-6,-6 L0,-12 L6,-6 L0,0 Z" fill="{trim}"/><circle cx="0" cy="-38" r="5" fill="{trim}"/>'
    b += f'<path d="M-3,38 q-6,10 3,16" stroke="{trim if g else "#B8B0A0"}" stroke-width="3" fill="none"/></g>'
    return b


def dopo(g):       # 도포: 넓은 소매. 손본=청록 깃, 귀한=금 깃+문양
    cloth = ["#4A4A56", "#2E3A5C", "#1E1E32"][g]
    trim = [HANJI, AMBIENT, GOLD][g]
    b = f'<path d="M34,14 L62,14 L74,40 L90,62 L84,70 L68,56 L72,90 L24,90 L28,56 L12,70 L6,62 L22,40 Z" fill="{cloth}"/>'
    b += f'<path d="M34,14 L48,36 L62,14" fill="none" stroke="{trim}" stroke-width="4"/><path d="M28,56 L72,56" stroke="{RED}" stroke-width="5"/>'
    if g == 2:
        b += f'<circle cx="48" cy="72" r="6" fill="none" stroke="{GOLD}" stroke-width="2"/><path d="M22,40 L12,62 M74,40 L84,62" stroke="{GOLD}" stroke-width="2"/>'
    return b


def noriga(g):     # 노리개: 매듭 + 술. 손본=청록 매듭, 귀한=금 매듭+방울
    col = [HANJI, AMBIENT, GOLD][g]
    b = f'<path d="M48,10 L48,34" stroke="{col}" stroke-width="4"/><path d="M48,34 q-16,0 -16,12 q0,12 16,12 q16,0 16,-12 q0,-12 -16,-12 Z" fill="none" stroke="{col}" stroke-width="5"/>'
    b += f'<path d="M48,34 L48,58 M34,40 L62,52 M62,40 L34,52" stroke="{col}" stroke-width="3" opacity=".8"/>'
    for i, x in enumerate((38, 48, 58)):
        b += f'<path d="M{x},58 L{x-3},{82+(i%2)*4} M{x},58 L{x+3},{82+(i%2)*4}" stroke="{RED if g else "#B8B0A0"}" stroke-width="3"/>'
    if g == 2:
        b += f'<circle cx="48" cy="64" r="7" fill="{GOLD}"/><rect x="45" y="62" width="6" height="4" fill="#0F1729"/>'
    return b


def bell():        # 월화의 방울(이름 있는 물건, 노리개 칸): 파혼 반경 +1m
    return (f'<path d="M48,8 L48,20" stroke="{HANJI}" stroke-width="4"/><path d="M26,66 Q28,28 48,22 Q68,28 70,66 Z" fill="#C9A05A"/><path d="M30,60 Q32,34 46,28" stroke="#fff" stroke-width="3" opacity=".4" fill="none"/>'
            f'<ellipse cx="48" cy="66" rx="22" ry="5" fill="#8A6A2A"/><circle cx="48" cy="72" r="6" fill="#8A6A2A"/><path d="M40,48 h16 M38,56 h20" stroke="{RED}" stroke-width="3"/>'
            f'<path d="M48,78 q-6,10 0,16 q6,-6 0,-16" fill="{RED}"/>')


def gear():
    for g, name in enumerate(["common", "crafted", "rare"]):
        save("icons", f"icon_weapon_{name}", ICON, ICON, club(g), "", pivot=(.5, .5), note=f"무기(육모방망이) · 등급 {name}")
        save("icons", f"icon_dopo_{name}", ICON, ICON, dopo(g), "", pivot=(.5, .5), note=f"도포 · 등급 {name}")
        save("icons", f"icon_noriga_{name}", ICON, ICON, noriga(g), "", pivot=(.5, .5), note=f"노리개 · 등급 {name}")
    save("icons", "icon_named_wolhwa_bell", ICON, ICON, bell(), "", pivot=(.5, .5), note="월화의 방울(이름 있는 물건, 노리개 칸)")
    for name, col in FRAMES:
        d = lg("fr", col, col, o1=.18, o2=.05)
        b = f'<rect x="3" y="3" width="90" height="90" rx="12" fill="#0F1729" opacity=".92"/><rect x="3" y="3" width="90" height="90" rx="12" fill="url(#fr)"/><rect x="3" y="3" width="90" height="90" rx="12" fill="none" stroke="{col}" stroke-width="4"/>'
        if name in ("rare", "named"):
            b += f'<rect x="8" y="8" width="80" height="80" rx="8" fill="none" stroke="{col}" stroke-width="1.5" opacity=".6"/>'
        save("icons", f"frame_{name}", ICON, ICON, b, d, pivot=(.5, .5), note=f"등급 테두리 · {name} · 색 {col}")


def run():
    for f in range(3):
        fx_call(f); fx_bind(f); fx_burst(f)
    gear()


# ================= 대조 후 추가분: 기획서 시연판(6-8)에서 빠져 있던 그림 =================
import re, os


def extra():
    from gen_sprites import SRC, prop, MANIFEST
    # 1) 원념 얼룩(바닥 데칼): 파혼의 대가. 3겹 겹치면 사나운 적이 나온다 → 겹침 단계별 3장
    for i, a in enumerate([.55, .75, .95]):
        d = rg("st", "#7B4FD6", .85, 0)
        b = f'<ellipse cx="128" cy="64" rx="120" ry="60" fill="url(#st)" opacity="{a}"/><ellipse cx="128" cy="64" rx="{60+i*18}" ry="{30+i*9}" fill="#1A0F2A" opacity=".85"/>'
        b += ''.join(f'<path d="M{128+dx},{64+dy} q{sx},{sy} {ex},{ey}" stroke="{RED}" stroke-width="3" fill="none" opacity=".8"/>' for dx, dy, sx, sy, ex, ey in [(-40,0,-20,-10,-30,6),(30,6,18,10,30,-4),(0,-18,6,-10,-4,-14)][:i + 1])
        save("fx", f"stain_{i}", 256, 128, b, d, pivot=(.5, .5), note=f"원념 얼룩 · 겹침 {i+1}단계(반경 2m = 128px 폭 기준 타원)")
    # 2) 사나운 적: 오래된 혼 위에 붉은 불길 + 뿔. 맺힘·공격력 +50% 표시
    s = open(os.path.join(SRC, "enemies", "soul_old.svg")).read()
    m = re.search(r"<defs>(.*?)</defs>(.*)</svg>", s, re.S)
    defs, body = m.group(1), m.group(2)
    extra_b = ('<ellipse cx="96" cy="150" rx="94" ry="120" fill="#FF2A2A" opacity=".22" filter="url(#blur8)"/>'
               f'<path d="M80,52 L72,22 L90,44 Z M112,52 L120,22 L102,44 Z" fill="{RED}"/>'
               '<path d="M96,236 q-30,-70 -6,-120 M100,236 q30,-70 8,-120" stroke="#FF2A2A" stroke-width="3" fill="none" opacity=".6"/>')
    save("enemies", "soul_fierce", 192, 256, extra_b + body, defs, pivot=(96 / 192, 236 / 256), note="사나운 적(얼룩 3겹 소환 / 맺힘·공격 +50%)")
    # 3) 서낭당(허브 건물)
    def p_seonangdang():
        return ('<path d="M-46,-4 L0,18 L46,-4 L46,-30 L0,-8 L-46,-30 Z" fill="url(#wall)"/>'
                '<path d="M-66,-34 Q-60,-70 0,-78 Q60,-70 66,-34 L0,-6 Z" fill="url(#roof)"/>'
                f'<rect x="-8" y="-30" width="16" height="20" fill="#1A1020"/><rect x="-5" y="-27" width="10" height="14" fill="{CHEON}" opacity=".5"/>'
                f'<path d="M-62,-30 L62,-30" stroke="{HANJI}" stroke-width="3" stroke-dasharray="6 5"/>'
                + ''.join(f'<path d="M{x},-30 q3,12 -1,26" stroke="{c}" stroke-width="5" fill="none"/>' for x, c in [(-40, "#3B6FD1"), (-20, "#E8C640"), (0, RED), (20, HANJI), (40, "#22262E")]))
    prop("seonangdang", 2, 2, p_seonangdang)
    # 4) 드롭: 맺힘 0 때 한 번 떨어지는 물건. 등급색 빛기둥 + 작은 꾸러미
    for name, col in G_FRAMES:
        d = lg("lb", col, col, o1=0, o2=.55) + rg("lg", col, .6, 0)
        b = f'<ellipse cx="64" cy="168" rx="52" ry="18" fill="url(#lg)"/><rect x="40" y="20" width="48" height="150" fill="url(#lb)"/>'
        b += f'<path d="M44,160 L84,160 L78,140 L50,140 Z" fill="#3A2A1E" stroke="{col}" stroke-width="3"/><circle cx="64" cy="140" r="5" fill="{col}"/>'
        save("fx", f"loot_{name}", 128, 192, b, d, pivot=(.5, 168 / 192), note=f"드롭 · 등급 {name}")
    # 5) HUD 추가
    d = f'<linearGradient id="tb" x1="0" x2="1"><stop offset="0" stop-color="{CHEON}"/><stop offset=".5" stop-color="#3B4C7A"/><stop offset="1" stop-color="{RED}"/></linearGradient>'
    save("hud", "tilt_bar", 256, 28, f'<rect x="2" y="8" width="252" height="12" rx="6" fill="url(#tb)" stroke="{GOLD}" stroke-width="2"/><path d="M128,2 L128,26" stroke="{HANJI}" stroke-width="2" opacity=".6"/>', d, pivot=(.5, .5), note="기울기 막대(왼쪽 천도 ~ 오른쪽 파혼)")
    save("hud", "tilt_marker", 20, 28, f'<path d="M10,2 L18,14 L10,26 L2,14 Z" fill="{HANJI}" stroke="#0F1729" stroke-width="2"/>', "", pivot=(.5, .5), note="기울기 마커")
    save("hud", "joystick_base", 256, 256, f'<circle cx="128" cy="128" r="120" fill="#0F1729" opacity=".55" stroke="{GOLD}" stroke-width="4"/><circle cx="128" cy="128" r="84" fill="none" stroke="#3B4C7A" stroke-width="3" stroke-dasharray="8 8"/>', "", pivot=(.5, .5), note="모바일 가상 조이스틱 바닥")
    save("hud", "joystick_knob", 96, 96, f'<defs>{rg("jk", CHEON, .5, 0)}</defs><circle cx="48" cy="48" r="46" fill="url(#jk)"/><circle cx="48" cy="48" r="32" fill="#16213E" stroke="{CHEON}" stroke-width="4"/>', "", pivot=(.5, .5), note="모바일 조이스틱 손잡이")
    skills = {"call": (CHEON, '<circle cx="64" cy="64" r="24" fill="none" stroke="#EFFFFA" stroke-width="5"/><path d="M64,18 q-14,16 -10,32 M64,110 q14,-16 10,-32 M18,64 q16,-14 32,-10 M110,64 q-16,14 -32,10" stroke="#EFFFFA" stroke-width="5" fill="none"/>'),
              "bind": (CHAIN, f'<ellipse cx="64" cy="64" rx="38" ry="20" fill="none" stroke="{CHAIN}" stroke-width="6" stroke-dasharray="12 6"/><ellipse cx="64" cy="64" rx="24" ry="12" fill="none" stroke="{CHAIN}" stroke-width="6" stroke-dasharray="10 6"/><circle cx="64" cy="64" r="6" fill="{RED}"/>'),
              "burst": ("#9A5CFF", f'<path d="M64,22 L72,50 L100,44 L82,66 L106,86 L76,82 L64,108 L54,82 L24,88 L46,66 L26,44 L56,50 Z" fill="{RED}" stroke="#9A5CFF" stroke-width="4" stroke-linejoin="round"/>')}
    for k, (col, ic) in skills.items():
        save("hud", f"btn_skill_{k}", 128, 128, f'<defs>{rg("sk", col, .7, 0)}</defs><circle cx="64" cy="64" r="62" fill="url(#sk)"/><circle cx="64" cy="64" r="48" fill="#0F1729" stroke="{col}" stroke-width="4"/><g transform="translate(64 64) scale(.66) translate(-64 -64)">{ic}</g>', "", pivot=(.5, .5), note={"call": "도술 1 붙잡아 부르기", "bind": "도술 2 휘감기", "burst": "도술 3 터뜨리기"}[k])
    save("hud", "btn_weapon_swap", 128, 128, f'<circle cx="64" cy="64" r="62" fill="#16213E" stroke="{GOLD}" stroke-width="4"/><path d="M32,50 L82,50 L72,38 M96,78 L46,78 L56,90" stroke="{HANJI}" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>', "", pivot=(.5, .5), note="무기 바꿔 들기(Tab·버튼)")
    save("hud", "btn_plus", 64, 64, f'<circle cx="32" cy="32" r="30" fill="#16213E" stroke="{CHEON}" stroke-width="3"/><path d="M32,16 V48 M16,32 H48" stroke="{CHEON}" stroke-width="6" stroke-linecap="round"/>', "", pivot=(.5, .5), note="능력치 +1 배분")
    save("hud", "banner_result", 640, 160, f'<rect x="3" y="3" width="634" height="154" rx="18" fill="#0F1729" opacity=".92" stroke="{GOLD}" stroke-width="4"/><rect x="14" y="14" width="612" height="132" rx="10" fill="none" stroke="#3B4C7A" stroke-width="2"/><path d="M14,40 V14 H40 M600,14 H626 V40 M626,120 V146 H600 M40,146 H14 V120" stroke="{GOLD}" stroke-width="4" fill="none"/>', "", pivot=(.5, .5), note="결과 화면 배너(9-slice 테두리 40px)")


G_FRAMES = [("common", HANJI), ("crafted", AMBIENT), ("rare", GOLD), ("named", RED)]
_run0 = run


def run():
    _run0()
    extra()
