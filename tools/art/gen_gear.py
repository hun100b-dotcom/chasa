"""장비 아이콘: 무기 5계열 + 갓·도포·띠·신·노리개 = 10종 × 5등급(50종) + 세트 3종 외형(주인공 도포 변형 3장).
기획서 6절 기준: 장비 7칸 = 무기(두 벌 바꿔 들기) · 갓 · 도포 · 띠 · 신 · 노리개 2.
gen_sprites3.run() 이 부른다. 아이콘 96×96, 피벗 중앙, 등급 테두리는 icons/frame_*.png 를 위에 겹친다.
5등급: 흔한(한지) / 손본(청록) / 귀한(금) / 이름 있는(붉은) / 한 벌(기억 보라, 세트 부품).
갓 칸의 외형은 흑립을 쓴다."""
import os, re

HANJI, TEAL, GOLD, RED, VIO = "#F3E7D3", "#4FA8A0", "#D4A94E", "#E85C41", "#C9B0FF"
GRADES = [("common", HANJI), ("crafted", TEAL), ("rare", GOLD), ("named", RED), ("set", VIO)]
SLOTS = ["w_cheolsak", "w_bangmangi", "w_yoryeong", "w_samjichang", "w_but", "gat", "dopo", "tti", "sin", "norigae"]
SLOT_KO = {"w_cheolsak": "무기·철삭", "w_bangmangi": "무기·육모방망이", "w_yoryeong": "무기·요령", "w_samjichang": "무기·삼지창", "w_but": "무기·명부 붓", "gat": "갓(흑립)", "dopo": "도포", "tti": "띠", "sin": "신(미투리)", "norigae": "노리개"}
BODY = "#2A2A38"; BODY2 = "#3C3C52"


def shape(slot, c, gi):
    """슬롯별 기본 실루엣. c = 등급 포인트색, gi = 등급 번호(0~4). 등급이 높을수록 장식이 늘어난다."""
    w = 3 + (gi > 0)
    if slot == "w_cheolsak":   # 고리진 사슬 + 끝 추
        links = "".join(f'<ellipse cx="{48+30*__import__("math").cos(t/7*6.283):.0f}" cy="{44+26*__import__("math").sin(t/7*6.283):.0f}" rx="9" ry="6" transform="rotate({t*51} {48+30*__import__("math").cos(t/7*6.283):.0f} {44+26*__import__("math").sin(t/7*6.283):.0f})" fill="none" stroke="{c}" stroke-width="{w}"/>' for t in range(7))
        return links + f'<circle cx="48" cy="80" r="9" fill="{BODY2}" stroke="{c}" stroke-width="{w}"/><path d="M48,70 L48,60" stroke="{c}" stroke-width="3"/>'
    if slot == "gat":
        return f'<ellipse cx="48" cy="58" rx="40" ry="10" fill="{BODY}" stroke="{c}" stroke-width="{w}"/><path d="M32,58 L35,24 Q48,16 61,24 L64,58 Z" fill="{BODY2}" stroke="{c}" stroke-width="{w}"/>' + (f'<path d="M34,50 L62,50" stroke="{c}" stroke-width="3"/>' if gi > 1 else "")
    if slot == "dopo":
        return f'<path d="M34,14 L62,14 L84,82 L12,82 Z" fill="{BODY}" stroke="{c}" stroke-width="{w}"/><path d="M48,14 L48,82" stroke="{BODY2}" stroke-width="3"/>' + (f'<path d="M34,14 L48,34 L62,14" fill="none" stroke="{c}" stroke-width="3"/>' if gi > 0 else "")
    if slot == "tti":
        return f'<path d="M10,40 L86,40 L86,58 L10,58 Z" fill="{RED}" stroke="{c}" stroke-width="{w}"/><circle cx="48" cy="49" r="10" fill="#B8402A" stroke="{c}" stroke-width="3"/><path d="M44,58 L36,84 M52,58 L62,84" stroke="{RED}" stroke-width="6"/>'
    if slot == "sin":
        return f'<path d="M12,58 Q10,38 30,38 L42,60 Q40,74 22,74 Q12,72 12,58 Z M54,58 Q52,38 72,38 L84,60 Q82,74 64,74 Q54,72 54,58 Z" fill="#8A7A5A" stroke="{c}" stroke-width="{w}"/>' + f'<path d="M20,52 L34,50 M62,52 L76,50" stroke="{BODY}" stroke-width="3"/>'
    if slot == "norigae":
        return f'<circle cx="48" cy="26" r="12" fill="{BODY2}" stroke="{c}" stroke-width="{w}"/><path d="M48,38 L48,50" stroke="{c}" stroke-width="3"/><circle cx="48" cy="54" r="7" fill="{c}"/><path d="M40,60 L34,86 M48,60 L48,90 M56,60 L62,86" stroke="{RED}" stroke-width="4"/>'
    if slot == "w_bangmangi":   # 육모(여섯 모) 방망이: 굵은 몽둥이 + 쇠띠 2개
        return f'<g transform="rotate(35 48 48)"><path d="M40,8 L56,8 L58,84 L38,84 Z" fill="#6B4A2E" stroke="{c}" stroke-width="{w}"/><rect x="36" y="22" width="24" height="7" fill="{BODY2}"/><rect x="36" y="58" width="24" height="7" fill="{BODY2}"/></g>'
    if slot == "w_yoryeong":    # 요령: 손잡이 달린 놋쇠 종
        return f'<rect x="43" y="6" width="10" height="26" fill="#8A6A22" stroke="{c}" stroke-width="2"/><path d="M26,32 Q24,60 14,76 L82,76 Q72,60 70,32 Z" fill="{GOLD}" stroke="{c}" stroke-width="{w}"/><circle cx="48" cy="82" r="6" fill="#6B4E14"/>'
    if slot == "w_samjichang":  # 삼지창: 세 갈래 날 + 긴 자루
        return f'<g transform="rotate(30 48 48)"><rect x="45" y="30" width="6" height="60" fill="#6B4A2E"/><path d="M30,32 L30,8 L38,30 M44,32 L48,2 L52,32 M58,30 L66,8 L66,32" fill="none" stroke="{c}" stroke-width="{w+1}" stroke-linejoin="round"/><path d="M30,32 L66,32" stroke="{c}" stroke-width="4"/></g>'
    return f'<g transform="rotate(35 48 48)"><rect x="45" y="30" width="6" height="58" fill="#6B4A2E"/><rect x="41" y="26" width="14" height="8" fill="{GOLD}"/><path d="M38,26 Q48,-10 58,26 Z" fill="#0A0A12" stroke="{c}" stroke-width="{w}"/></g>'


def deco(gi, c):
    """등급 장식: 귀한 = 보석 점, 이름 있는 = 붉은 광, 한 벌 = 보라 광 + 반짝임"""
    o = ""
    if gi >= 2: o += f'<circle cx="78" cy="18" r="6" fill="{c}"/><circle cx="76" cy="16" r="2" fill="#fff"/>'
    if gi == 3: o += f'<circle cx="48" cy="48" r="46" fill="{RED}" opacity=".14" filter="url(#bl)"/>'
    if gi == 4: o += f'<circle cx="48" cy="48" r="46" fill="{VIO}" opacity=".22" filter="url(#bl)"/>' + "".join(f'<path d="M{x},{y-6} L{x+2},{y} L{x+8},{y+2} L{x+2},{y+4} L{x},{y+10} L{x-2},{y+4} L{x-8},{y+2} L{x-2},{y} Z" fill="#fff" opacity=".85"/>' for x, y in [(14, 18), (82, 40), (20, 80)])
    return o


def run(add, src):
    wrap = lambda b: f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><defs><filter id="bl"><feGaussianBlur stdDeviation="6"/></filter></defs>{b}</svg>'
    for slot in SLOTS:
        for gi, (g, c) in enumerate(GRADES):
            add("gear", f"gear_{slot}_{g}", 96, 96, wrap(deco(gi, c) + shape(slot, c, gi)), (.5, .5), f"장비 아이콘 · {SLOT_KO[slot]} · 등급 {g}")
    # 전설 테두리(기존 frame_* 4종에 1종 추가)
    fr = f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><defs><filter id="bl"><feGaussianBlur stdDeviation="3"/></filter></defs><rect x="3" y="3" width="90" height="90" rx="12" fill="{VIO}" opacity=".12"/><rect x="3" y="3" width="90" height="90" rx="12" fill="none" stroke="{VIO}" stroke-width="4"/><rect x="8" y="8" width="80" height="80" rx="8" fill="none" stroke="{VIO}" stroke-width="1.5" opacity=".7"/><rect x="3" y="3" width="90" height="90" rx="12" fill="none" stroke="{VIO}" stroke-width="8" opacity=".3" filter="url(#bl)"/></svg>'
    add("icons", "frame_set", 96, 96, fr, (.5, .5), "등급 테두리 · set(한 벌) · 색 #C9B0FF")
    # 세트 3종: 주인공 정면(idle)의 색을 바꾸고 장식을 덧붙인 외형
    base = open(os.path.join(src, "characters", "chasa_idle.svg")).read()
    SETS = {
        "wolhwa": ("월화 세트(굿옷)", {"#232338": "#3A1F2A", "#0A0A12": "#1C0C14"}, f'<path d="M-70,170 L70,170 M-90,250 L90,250" stroke="{GOLD}" stroke-width="7" opacity=".9" transform="translate(128,53) scale(.5)"/><path d="M-60,60 L-80,200" stroke="{RED}" stroke-width="10" opacity=".8" transform="translate(128,53) scale(.5)"/>'),
        "miner": ("광부 세트(쇳골)", {"#232338": "#2E2E2E", "#0A0A12": "#161616"}, f'<path d="M-80,80 L80,80 M-90,200 L90,200" stroke="#B8A26A" stroke-width="8" opacity=".9" transform="translate(128,53) scale(.5)"/><circle cx="0" cy="-20" r="14" fill="#FFD27A" transform="translate(128,53) scale(.5)"/>'),
        "heukwol": ("흑월 세트", {"#232338": "#101018", "#0A0A12": "#000000"}, f'<path d="M-34,40 L-70,165 L-120,275 L-60,355 M34,40 L70,165 L110,275 L50,355" stroke="{RED}" stroke-width="9" fill="none" opacity=".95" transform="translate(128,53) scale(.5)"/><path d="M-24,3 L-22,70" stroke="{RED}" stroke-width="7" transform="translate(128,53) scale(.5)"/>'),
    }
    for sid, (ko, rep, over) in SETS.items():
        s = base
        for a, b in rep.items(): s = s.replace(a, b)
        s = s.replace("</svg>", over + "</svg>")
        add("characters", f"chasa_set_{sid}", 256, 256, s, (128 / 256, 232 / 256), f"세트 외형 · {ko} (정면 idle 변형)")
