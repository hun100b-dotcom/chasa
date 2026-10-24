#!/usr/bin/env python3
"""
차사 임시 스프라이트 생성기 (아트팀).
왜 코드로 그리나: 힉스필드 연결 전까지 "분위기가 전달되는" 임시 그림을 빠르게, 같은 규칙으로, 다시 뽑을 수 있게 하기 위해서다.
사용: python3 tools/art/gen_sprites.py  → SVG를 assets/sprites_src/ 에 쓰고, render_sprites.js 가 PNG로 바꾼다.
규칙: 좌표 원점은 각 스프라이트의 '발(바닥) 기준점'. manifest.json 에 피벗(0~1)을 적는다.
색은 docs/art/palette-tokens.json 의 값만 쓴다(주변 소품의 갈색·회색은 낮은 채도 보조색).
"""
import json, os, random, math

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SRC = os.path.join(ROOT, "assets", "sprites_src")
MANIFEST = []          # (파일 경로, 폭, 높이, 피벗x, 피벗y, tint 여부, 설명)

# ---- 팔레트 토큰(palette-tokens.json과 같은 값) ----
NIGHT = "#16213E"; DEEP = "#0F1729"; HANJI = "#F3E7D3"; AMBIENT = "#4FA8A0"
RED = "#E85C41"; GOLD = "#D4A94E"; INK = "#2A2A38"; CHAIN = "#BFE8FF"
CHEON = "#5FE3C0"; MEMORY = "#C9B0FF"
SOUL = ["#BFE8FF", "#FFCC55", "#FF6A3D", "#9A5CFF"]


def svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}'
            f'<filter id="blur4" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>'
            f'<filter id="blur2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2"/></filter>'
            f'<filter id="blur8" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="8"/></filter>'
            f'</defs>{body}</svg>')


def save(folder, name, w, h, body, defs="", pivot=(0.5, 0.9), tint=False, note=""):
    d = os.path.join(SRC, folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name + ".svg"), "w") as f:
        f.write(svg(w, h, body, defs))
    MANIFEST.append({"file": f"{folder}/{name}.png", "w": w, "h": h, "pivotX": pivot[0], "pivotY": pivot[1],
                     "ppu": 128, "tint": tint, "note": note})


def lg(id_, c1, c2, x1=0, y1=0, x2=0, y2=1, o1=1, o2=1):
    """세로(기본) 선형 그라디언트: 위→아래 명암"""
    return (f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{c1}" stop-opacity="{o1}"/><stop offset="1" stop-color="{c2}" stop-opacity="{o2}"/></linearGradient>')


def rg(id_, c, o_in=1, o_out=0):
    return (f'<radialGradient id="{id_}"><stop offset="0" stop-color="{c}" stop-opacity="{o_in}"/>'
            f'<stop offset="1" stop-color="{c}" stop-opacity="{o_out}"/></radialGradient>')


def rim(sid, fill, rimcol=AMBIENT, dx=-4, dy=0):
    """림 라이트: 같은 모양을 림색으로 먼저 깔고, 몸색 모양을 살짝 옮겨 덮어 오른쪽에 빛 테두리만 남긴다"""
    return (f'<use xlink:href="#{sid}" fill="{rimcol}"/>'
            f'<use xlink:href="#{sid}" fill="{fill}" transform="translate({dx},{dy})"/>')


def shadow(cx, cy, rx, ry, op=.55):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#000" opacity="{op}" filter="url(#blur4)"/>'


# =========================================================
# 1) 주인공 (256×256, 발 기준 (128, 232)). 좌우 한쪽만 그리고 Unity에서 flipX
# =========================================================
def chasa(pose, name=None, tilt=0, bob=0, hit=False):
    W = 448 if pose == "swing" else 256
    H = 256
    ox, oy, s = 128, 53, .5          # 몸통 좌표계: 목 중앙이 (0,0), .5배로 줄여 쓴다
    defs = lg("body", "#232338", "#0A0A12") + lg("band", "#F07A5E", "#B8402A") + lg("hat", "#2E2E46", "#0E0E18") + rg("soul", CHEON, .9, 0) + rg("orb", CHEON, 1, 0)
    # 공통 몸통(도포) · 흑립은 sid로 정의해 림 라이트에 재사용
    shapes = ('<g id="coat"><path d="M-34,40 L34,40 L70,165 L110,275 L50,355 L-60,355 L-120,275 L-70,165 Z"/></g>'
              '<g id="hat"><ellipse cx="0" cy="3" rx="92" ry="17"/><path d="M-30,3 L-26,-53 Q0,-69 26,-53 L30,3 Z"/></g>')
    arms = {
        "idle":  ('<path d="M-34,40 L-120,135 L-135,195 L-90,185 L-62,135 Z"/><path d="M34,40 L110,120 L170,165 L150,203 L88,165 Z"/>'),
        "swing": ('<path d="M-34,40 L-120,135 L-135,195 L-90,185 L-62,135 Z"/><path d="M34,40 L120,40 L240,0 L248,48 L120,92 Z"/>'),
        "cast":  ('<path d="M-34,40 L-82,120 L-30,195 L-8,150 Z"/><path d="M34,40 L82,120 L30,195 L8,150 Z"/>'),
    }[pose]
    shapes += f'<g id="arms">{arms}</g>'
    g = f'<g transform="rotate({tilt} {ox} 232) translate({ox},{oy + bob}) scale({s})">'
    g += shapes
    # 철삭(사슬) — 몸 뒤에서 늘어지는/휘두르는 선
    if pose == "idle":
        g += f'<path d="M165,200 Q195,290 150,335" stroke="{CHAIN}" stroke-width="7" fill="none" stroke-dasharray="16 7" stroke-linecap="round"/>'
    if pose == "swing":
        g += f'<path d="M240,20 Q370,-90 560,60" stroke="{CHAIN}" stroke-width="8" fill="none" stroke-dasharray="18 8" stroke-linecap="round"/><path d="M240,20 Q370,-90 560,60" stroke="#fff" stroke-width="3" fill="none" opacity=".35"/>'
        g += f'<circle cx="560" cy="60" r="26" fill="url(#orb)"/>'
    if pose == "cast":
        g += f'<circle cx="0" cy="150" r="120" fill="url(#soul)" opacity=".55"/>'
    # 몸: 림 라이트 + 본체
    g += rim("coat", "url(#body)") + rim("arms", "url(#body)") + rim("hat", "url(#hat)")
    # 도포 접힌 선, 갓 윗면 하이라이트
    g += f'<path d="M-6,45 L-18,350 M18,45 L34,350 M-44,150 L-70,340" stroke="#000" stroke-width="5" opacity=".35" fill="none"/>'
    g += f'<ellipse cx="0" cy="-2" rx="84" ry="11" fill="none" stroke="#3E3E5C" stroke-width="3"/>'
    g += f'<path d="M-24,-18 Q0,-27 24,-18" stroke="#4A4A6C" stroke-width="3" fill="none"/>'
    # 붉은 띠(허리 + 늘어진 끈)
    g += f'<path d="M-54,135 L54,135 L58,160 L-58,160 Z" fill="url(#band)"/><path d="M32,160 L44,225 L26,225 Z" fill="url(#band)"/>'
    g += f'<path d="M-54,135 L54,135" stroke="#FFB8A5" stroke-width="3" opacity=".6"/>'
    # 혼불(어깨 곁)
    if pose != "cast":
        g += f'<g transform="translate(-130,120)"><circle r="46" fill="url(#soul)"/><path d="M0,28 q-20,-26 0,-60 q20,34 0,60" fill="{CHEON}"/><path d="M0,16 q-9,-14 0,-32 q9,18 0,32" fill="#EFFFFA"/></g>'
    else:
        g += f'<circle cx="0" cy="155" r="30" fill="url(#orb)"/><circle cx="0" cy="155" r="13" fill="#EFFFFA"/>'
    if hit:   # 피격: 붉은 번쩍임을 몸 위에 한 겹 덮는다
        g += f'<use xlink:href="#coat" fill="{RED}" opacity=".55"/><use xlink:href="#hat" fill="{RED}" opacity=".4"/>'
    g += '</g>'
    body = shadow(128, 232, 56, 12) + g
    save("characters", name or f"chasa_{pose}", W, H, body, defs, pivot=(128 / W, 232 / H), note="주인공 · 정면, 좌우는 flipX")


# =========================================================
# 2) 혼 4종 (192×256, 발 기준 (96, 236))
# =========================================================
def ghost(kind, kneel=False):
    W, H = 192, 256
    col = SOUL[kind]
    defs = rg("aura", col, .55, 0) + lg("gown", "#F4FAFF" if kind == 0 else col, col, o1=.95, o2=.12)
    ox, oy = 96, 236
    top = 72 if not kneel else 128    # 머리 높이: 무릎 꿇으면 낮아진다
    body = f'<ellipse cx="96" cy="{top + 40}" rx="88" ry="{110 if not kneel else 80}" fill="url(#aura)"/>'
    body += shadow(96, 236, 44, 9, .45)
    g = ""
    if kind == 0:   # 갓 죽은 혼: 거의 사람. 또렷한 윤곽, 생전 옷차림, 표정이 읽힌다
        if kneel:
            g += f'<path d="M58,236 Q54,170 70,150 L122,150 Q140,170 134,236 Z" fill="url(#gown)"/>'
            g += f'<path d="M76,158 L116,158 L110,184 L82,184 Z" fill="#7AA8D8" opacity=".8"/>'
            g += f'<circle cx="96" cy="{top}" r="19" fill="#EAF6FF"/>'
            g += f'<path d="M78,{top-6} Q96,{top-26} 114,{top-6} Q104,{top-14} 96,{top-12} Q88,{top-14} 78,{top-6}" fill="#1B2438"/>'
            g += f'<circle cx="89" cy="{top+3}" r="2" fill="#223"/><circle cx="103" cy="{top+3}" r="2" fill="#223"/><path d="M90,{top+13} q6,-3 12,0" stroke="#223" fill="none"/>'
        else:
            g += f'<path d="M62,236 Q56,150 74,118 L118,118 Q138,150 130,236 Z" fill="url(#gown)"/>'
            g += f'<path d="M72,118 L120,118 L116,150 L76,150 Z" fill="#7AA8D8" opacity=".85"/><path d="M92,118 L100,150" stroke="{HANJI}" stroke-width="3"/>'
            g += f'<circle cx="96" cy="{top}" r="19" fill="#EAF6FF"/>'
            g += f'<path d="M78,{top-6} Q96,{top-26} 114,{top-6} Q104,{top-14} 96,{top-12} Q88,{top-14} 78,{top-6}" fill="#1B2438"/>'
            g += f'<circle cx="89" cy="{top+3}" r="2" fill="#223"/><circle cx="103" cy="{top+3}" r="2" fill="#223"/><path d="M90,{top+13} q6,-3 12,0" stroke="#223" fill="none"/>'
            g += f'<path d="M68,130 Q50,160 60,190" stroke="#EAF6FF" stroke-width="9" fill="none" stroke-linecap="round" opacity=".9"/><path d="M124,130 Q142,160 132,190" stroke="#EAF6FF" stroke-width="9" fill="none" stroke-linecap="round" opacity=".9"/>'
    elif kind == 1:  # 해 넘긴 혼: 윤곽이 번지고 아래가 물에 번진 듯 흐른다
        extra = 0 if not kneel else 0
        g += f'<g filter="url(#blur2)">'
        g += f'<path d="M60,236 Q52,{top+40} 72,{top+20} L120,{top+20} Q142,{top+40} 132,236 Q120,222 110,240 Q100,224 92,242 Q80,224 60,236 Z" fill="url(#gown)"/>'
        g += f'<circle cx="96" cy="{top}" r="19" fill="#FFE9B0" opacity=".9"/>'
        g += '</g>'
        g += f'<circle cx="89" cy="{top+2}" r="2.2" fill="#3A2A10" opacity=".7"/><circle cx="103" cy="{top+2}" r="2.2" fill="#3A2A10" opacity=".7"/>'
        if not kneel:
            g += f'<path d="M72,{top+30} Q56,{top+58} 62,{top+80}" stroke="#FFE9B0" stroke-width="8" fill="none" opacity=".6" filter="url(#blur2)"/><path d="M120,{top+30} Q136,{top+58} 130,{top+80}" stroke="#FFE9B0" stroke-width="8" fill="none" opacity=".6" filter="url(#blur2)"/>'
    elif kind == 2:  # 오래된 혼: 비율 붕괴, 얼굴 없음, 팔이 길게 늘어짐
        hh = top - 10 if not kneel else top
        g += f'<path d="M70,236 Q50,{hh+50} 78,{hh+16} L112,{hh+16} Q140,{hh+60} 124,236 L112,222 L100,244 L90,224 L80,242 Z" fill="url(#gown)" filter="url(#blur2)"/>'
        g += f'<ellipse cx="96" cy="{hh}" rx="16" ry="23" fill="#2A0F08" opacity=".92"/>'
        g += f'<path d="M80,{hh+24} Q40,{hh+80} 46,{236 - (0 if not kneel else 20)}" stroke="#FF8A5C" stroke-width="7" fill="none" opacity=".75" stroke-linecap="round"/>'
        g += f'<path d="M112,{hh+24} Q152,{hh+90} 146,{236 - (0 if not kneel else 20)}" stroke="#FF8A5C" stroke-width="7" fill="none" opacity=".75" stroke-linecap="round"/>'
        g += f'<path d="M90,{hh-4} q6,6 12,0" stroke="#FF6A3D" stroke-width="2" fill="none" opacity=".5"/>'
    else:           # 덩어리: 여러 혼이 엉겨 개별 형태가 사라진 보라 덩이, 닫힌 사슬 고리
        rnd = random.Random(7)
        for cx, cy, r in [(76, 170, 40), (120, 164, 38), (96, 128, 34), (96, 200, 36), (66, 214, 24), (132, 210, 22)]:
            g += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#7B4FD6" opacity=".78"/><circle cx="{cx-6}" cy="{cy-8}" r="{r*.6}" fill="#9A5CFF" opacity=".5"/>'
        g += f'<circle cx="84" cy="136" r="5" fill="{HANJI}" opacity=".9"/><circle cx="106" cy="132" r="5" fill="{HANJI}" opacity=".9"/><circle cx="92" cy="146" r="3" fill="#111"/>'
        g += f'<path d="M44,158 q-12,-18 -2,-28 M150,200 q16,-2 22,-14" stroke="{HANJI}" stroke-width="5" fill="none" stroke-linecap="round" opacity=".85"/>'
        g += f'<ellipse cx="96" cy="206" rx="78" ry="32" fill="none" stroke="{RED}" stroke-width="3.5" stroke-dasharray="9 7"/>'
    save("enemies", f"soul_{['fresh','day','old','lump'][kind]}{'_kneel' if kneel else ''}", W, H, body + g, defs,
         pivot=(ox / W, oy / H), note=["갓 죽은 혼 10초", "해 넘긴 혼 7초", "오래된 혼 4초", "덩어리(천도 불가)"][kind] + (" · 무릎 꿇음(처결 대기)" if kneel else " · 서 있음"))


# =========================================================
# 3) 타일 (128×64 마름모) 12장(6종×변형 2)
# =========================================================
TILES = [("dirt_road", "#8C6F4E", "#6F5638", "pebble"), ("yard", "#6D5A44", "#54452F", "pebble"), ("grass", "#3E5A44", "#2E4634", "blade"),
         ("paddy", "#4F6B49", "#5B8AA0", "water"), ("stone_path", "#7C808A", "#5E626C", "slab"), ("stepping_stones", "#4C7C96", "#8E9AA8", "water")]


def tile(name, base, dark, mode, v):
    rnd = random.Random(hash(name) % 1000 + v * 31)
    defs = lg("tg", base, dark, o1=1, o2=1) + '<clipPath id="dia"><path d="M64,0 L128,32 L64,64 L0,32 Z"/></clipPath>'
    b = f'<g clip-path="url(#dia)"><rect width="128" height="64" fill="url(#tg)"/>'
    for _ in range(26):
        x, y = rnd.uniform(8, 120), rnd.uniform(6, 58)
        if mode == "pebble":
            b += f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rnd.uniform(1.5,4):.1f}" ry="{rnd.uniform(1,2.2):.1f}" fill="{dark}" opacity=".7"/>'
        elif mode == "blade":
            b += f'<path d="M{x:.1f},{y:.1f} l{rnd.uniform(-2,2):.1f},-7" stroke="#6E9A6C" stroke-width="1.6" opacity=".8"/>'
        elif mode == "water":
            b += f'<path d="M{x:.1f},{y:.1f} q6,-3 12,0" stroke="#CFE6F2" stroke-width="1.4" fill="none" opacity=".55"/>'
        else:
            b += f'<path d="M{x:.1f},{y:.1f} l{rnd.uniform(6,14):.1f},{rnd.uniform(-3,3):.1f}" stroke="{dark}" stroke-width="1.8" opacity=".6"/>'
    if name == "stone_path":
        b += f'<path d="M64,6 L64,58 M20,32 L108,32" stroke="{dark}" stroke-width="2" opacity=".7"/>'
    if name == "stepping_stones":
        for cx, cy in [(44, 26), (74, 38), (96, 24)]:
            b += f'<ellipse cx="{cx}" cy="{cy}" rx="13" ry="6" fill="#9A9EA8"/><ellipse cx="{cx}" cy="{cy-1.5}" rx="11" ry="4.5" fill="#B4B8C2"/>'
    # 가장자리 어둡게(타일 이음매 구분용으로 아주 약하게)
    b += f'<path d="M64,0 L128,32 L64,64 L0,32 Z" fill="none" stroke="#000" stroke-width="2" opacity=".18"/></g>'
    save("tiles", f"tile_{name}_{'ab'[v]}", 128, 64, b, defs, pivot=(0.5, 0.5), note="바닥 타일 · 마름모 128×64")


# =========================================================
# 4) 소품 12종 (footprint 기준점 = 바닥 중심)
# =========================================================
def prop(name, w, h, fn):
    hw = 32 * (w + h); hh = 16 * (w + h)
    W = 2 * hw + 48; H = 300
    ox, oy = W / 2, H - hh - 16
    defs = lg("wall", "#9A8A70", "#6C5E48") + lg("thatch", "#D6B468", "#A07C3C") + lg("roof", "#4A566E", "#2A3244") + lg("wood", "#8A5C38", "#5A3A22") + lg("stone", "#B0B4BE", "#7C808A") + lg("leaf", "#3D6E5C", "#22443A")
    b = shadow(ox, oy, hw * .55, hh * .55, .5) + f'<g transform="translate({ox},{oy})">{fn()}</g>'
    save("props", f"prop_{name}", int(W), H, b, defs, pivot=(0.5, oy / H), note=f"소품 · 차지하는 칸 {w}×{h}")


def p_choga():
    return ('<path d="M-62,-6 L0,22 L62,-6 L62,-44 L0,-16 L-62,-44 Z" fill="url(#wall)"/>'
            '<path d="M-82,-40 Q-74,-84 0,-98 Q74,-84 82,-40 L0,-2 Z" fill="url(#thatch)"/>'
            '<path d="M-82,-40 L0,-2 L82,-40" stroke="#7A5E2C" stroke-width="4" fill="none"/>'
            '<path d="M-40,-62 L-20,-30 M0,-80 L0,-16 M30,-66 L48,-34" stroke="#8C6A2E" stroke-width="3" opacity=".6"/>'
            '<rect x="-10" y="-28" width="20" height="26" rx="2" fill="#2A1C12"/><rect x="-6" y="-24" width="12" height="18" fill="#E8C86A" opacity=".55"/>')


def p_giwa():
    return ('<path d="M-80,-8 L0,30 L80,-8 L80,-42 L0,-4 L-80,-42 Z" fill="#E4DAC6"/>'
            '<path d="M-108,-50 Q-98,-44 -80,-44 L0,-6 L80,-44 Q98,-44 108,-50 Q94,-106 0,-114 Q-94,-106 -108,-50 Z" fill="url(#roof)"/>'
            '<path d="M-98,-54 Q0,-12 98,-54" stroke="#7A86A2" stroke-width="3" fill="none"/>'
            '<path d="M-60,-84 Q0,-66 60,-84 M-76,-68 Q0,-46 76,-68" stroke="#1E2434" stroke-width="3" fill="none" opacity=".6"/>'
            '<rect x="-36" y="-32" width="24" height="26" fill="#7A4A2A"/><rect x="12" y="-32" width="24" height="26" fill="#7A4A2A"/><path d="M-24,-32 v26 M24,-32 v26" stroke="#E8C86A" stroke-width="2" opacity=".6"/>')


def p_dam():
    s = ""
    for x, y, c in [(-44, -10, "#8B8F99"), (-14, -8, "#A0A4AE"), (18, -10, "#868A94"), (48, -8, "#9A9EA8"), (-28, -28, "#9A9EA8"), (4, -26, "#868A94"), (34, -28, "#A0A4AE"), (-10, -44, "#8B8F99")]:
        s += f'<ellipse cx="{x}" cy="{y}" rx="17" ry="12" fill="{c}"/><ellipse cx="{x-3}" cy="{y-4}" rx="10" ry="5" fill="#fff" opacity=".12"/>'
    return s


def p_jang():
    s = ""
    for x, h, w in [(-44, 36, 14), (0, 48, 17), (38, 30, 12)]:
        s += (f'<path d="M{x-w},0 Q{x-w-8},{-h/2} {x-w+4},{-h} L{x+w-4},{-h} Q{x+w+8},{-h/2} {x+w},0 Z" fill="url(#wood)"/>'
              f'<rect x="{x-w+2}" y="{-h-7}" width="{2*w-4}" height="8" rx="3" fill="#4A2E18"/><path d="M{x-w+5},{-h+6} Q{x-w+2},{-h/2} {x-w+7},-6" stroke="#fff" stroke-width="3" opacity=".15" fill="none"/>')
    return s


def p_umul():
    return ('<ellipse cx="0" cy="-8" rx="32" ry="16" fill="url(#stone)"/><ellipse cx="0" cy="-12" rx="22" ry="10" fill="#0A1020"/><ellipse cx="0" cy="-11" rx="14" ry="5" fill="#2C4A6C" opacity=".7"/>'
            '<rect x="-36" y="-76" width="6" height="68" fill="url(#wood)"/><rect x="30" y="-76" width="6" height="68" fill="url(#wood)"/><rect x="-42" y="-84" width="84" height="8" fill="url(#wood)"/>'
            f'<path d="M0,-76 L0,-40" stroke="{HANJI}" stroke-width="2"/><rect x="-9" y="-40" width="18" height="14" rx="2" fill="#7A4A2A"/>')


def p_namu():
    s = ('<path d="M-14,0 Q-10,-54 -26,-104 L26,-104 Q10,-54 14,0 Z" fill="#4A3828"/><path d="M-6,-10 Q-4,-60 -14,-100" stroke="#6A5238" stroke-width="3" fill="none" opacity=".6"/>'
         '<circle cx="0" cy="-132" r="66" fill="url(#leaf)"/><circle cx="-42" cy="-106" r="36" fill="url(#leaf)"/><circle cx="44" cy="-108" r="34" fill="url(#leaf)"/>'
         '<circle cx="-14" cy="-150" r="30" fill="#4C8470" opacity=".55"/>')
    for i, c in enumerate(["#3B6FD1", "#E8C640", "#E85C41", "#F3E7D3", "#22262E"]):
        x = -44 + i * 22
        s += f'<path d="M{x},-92 q5,16 -2,40 l9,-3 q5,-20 0,-37 Z" fill="{c}"/>'
    return s


def p_dol():
    s = ""
    for x, y, r, c in [(-18, -9, 18, "#868A94"), (18, -9, 17, "#9A9EA8"), (0, -26, 15, "#A8ACB6"), (-4, -42, 10, "#8B8F99")]:
        s += f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r*.7}" fill="{c}"/><ellipse cx="{x-4}" cy="{y-5}" rx="{r*.5}" ry="{r*.25}" fill="#fff" opacity=".15"/>'
    return s


def p_jangseung():
    return ('<path d="M-15,0 L-13,-90 L13,-90 L15,0 Z" fill="url(#wood)"/><path d="M-17,-90 L0,-106 L17,-90 Z" fill="#5A3A22"/>'
            f'<circle cx="-5" cy="-70" r="3.5" fill="{HANJI}"/><circle cx="5" cy="-70" r="3.5" fill="{HANJI}"/><path d="M-7,-56 h14 v5 h-14 z" fill="{RED}"/><path d="M-9,-80 l6,-4 M9,-80 l-6,-4" stroke="#2A1810" stroke-width="3"/>'
            '<path d="M-15,-30 h30" stroke="#2A1810" stroke-width="2" opacity=".4"/>')


def p_sangyeo():
    return (f'<rect x="-90" y="-16" width="180" height="7" fill="url(#wood)"/><rect x="-46" y="-56" width="92" height="44" fill="{HANJI}"/>'
            f'<path d="M-60,-56 Q-54,-64 -46,-68 L46,-68 Q54,-64 60,-56 L0,-92 Z" fill="#E8C86A"/><path d="M-70,-54 L70,-54 L54,-64 L-54,-64 Z" fill="{RED}"/>'
            '<rect x="-32" y="-48" width="14" height="30" fill="#E85C41" opacity=".7"/><rect x="18" y="-48" width="14" height="30" fill="#3B6FD1" opacity=".7"/>'
            f'<path d="M-46,-12 q-4,16 2,22 M46,-12 q4,16 -2,22" stroke="{HANJI}" stroke-width="5" fill="none"/>')


def p_pyeong():
    return ('<rect x="-56" y="-32" width="112" height="10" fill="#B58B54"/><path d="M-56,-22 h112" stroke="#6A4A28" stroke-width="2"/>'
            + ''.join(f'<rect x="{x}" y="-22" width="7" height="22" fill="url(#wood)"/>' for x in (-52, 45)))


def p_jigae():
    return ('<path d="M-20,0 L-13,-76 M20,0 L13,-76" stroke="#6B4A2E" stroke-width="8"/><path d="M-15,-26 L15,-26 M-14,-50 L14,-50" stroke="#6B4A2E" stroke-width="6"/>'
            '<path d="M-24,-76 Q-16,-98 -11,-86 M24,-76 Q16,-98 11,-86" stroke="#6B4A2E" stroke-width="6" fill="none"/>')


def p_sotdae():
    return (f'<rect x="-3" y="-118" width="7" height="118" fill="url(#wood)"/><path d="M-16,-116 L10,-116 L24,-130 L8,-124 L-2,-134 L-7,-122 Z" fill="{AMBIENT}"/><circle cx="-10" cy="-120" r="2" fill="#fff" opacity=".8"/>')


# =========================================================
# 5) 첫 보스 나루 영감 (384×320)
# =========================================================
def boss_naru(attack):
    W, H = 384, 320
    defs = lg("hull", "#3B3F52", "#14161F") + lg("robe", "#586080", "#262B3E") + rg("mist", "#BFE8FF", .45, 0)
    ox, oy = 192, 270
    b = f'<ellipse cx="{ox}" cy="{oy-10}" rx="170" ry="38" fill="url(#mist)"/>'
    b += shadow(ox, oy + 6, 120, 16, .6)
    g = '<g id="hullg"><path d="M-150,-20 Q0,50 150,-20 L128,10 Q0,70 -128,10 Z"/></g>'
    g += rim("hullg", "url(#hull)")
    # 영감: 삿갓 + 낡은 도포. 반쯤 가라앉은 배 위에서 삿대를 짚는다
    g += '<g id="old"><path d="M-30,-18 L30,-18 L44,-110 L-44,-110 Z"/><circle cx="0" cy="-124" r="20"/></g>' + rim("old", "url(#robe)")
    g += f'<path d="M-60,-130 Q0,-182 60,-130 Q0,-122 -60,-130 Z" fill="#6B5A3A"/><path d="M-60,-130 Q0,-182 60,-130" stroke="#3C3220" stroke-width="3" fill="none"/>'
    g += f'<circle cx="-8" cy="-120" r="2.4" fill="#D8D0C0"/><circle cx="9" cy="-120" r="2.4" fill="#D8D0C0"/>'
    if attack:   # 삿대 휩쓸기 예비동작: 삿대를 크게 뒤로 젖힌다
        g += f'<path d="M44,-96 L170,-190 M170,-190 L186,-206" stroke="#7A5A34" stroke-width="9" stroke-linecap="round"/><path d="M70,-120 A130,130 0 0 1 150,-40" stroke="{RED}" stroke-width="5" fill="none" stroke-dasharray="10 8" opacity=".85"/>'
    else:
        g += f'<path d="M44,-90 L96,40" stroke="#7A5A34" stroke-width="9" stroke-linecap="round"/>'
    # 칼금 새긴 삿대 끝과 물결
    g += f'<path d="M-170,-6 q20,-10 40,0 t40,0 M120,6 q20,-10 40,0 t40,0" stroke="#CFE6F2" stroke-width="3" fill="none" opacity=".5"/>'
    # 제사상 엽전 다섯 닢(서사 소품)
    g += ''.join(f'<circle cx="{-110+i*14}" cy="-26" r="6" fill="{GOLD}"/><rect x="{-112+i*14}" y="-28" width="4" height="4" fill="#0F1729"/>' for i in range(5))
    b += f'<g transform="translate({ox},{oy})">{g}</g>'
    save("boss", f"boss_naru_{'attack' if attack else 'idle'}", W, H, b, defs, pivot=(ox / W, oy / H), note="1호 보스 나루 영감" + (" · 삿대 휩쓸기 예비동작" if attack else ""))


# =========================================================
# 6) HUD
# =========================================================
def hud():
    # 게이지(틀 + 채움): 채움은 흰색, Unity에서 Image Type=Filled + Tint
    save("hud", "gauge_frame", 192, 24, f'<rect x="1" y="1" width="190" height="22" rx="11" fill="#0A1022" stroke="{GOLD}" stroke-width="2"/><rect x="5" y="5" width="182" height="14" rx="7" fill="#16213E"/>', pivot=(0.5, 0.5), note="게이지 틀 · 9-slice 권장(좌우 12px)")
    save("hud", "gauge_fill", 182, 14, f'<rect width="182" height="14" rx="7" fill="#fff"/><rect y="0" width="182" height="6" rx="3" fill="#fff" opacity=".35"/>', pivot=(0, 0.5), tint=True, note="게이지 채움(흰색 → Tint로 맺힘=붉은색, 체력=청록 등)")
    # 처결 타이머 링: 두 장 — 배경 링(고정), 채움 링(흰색, Radial 360 Fill)
    ring = lambda col, op: f'<circle cx="64" cy="64" r="54" fill="none" stroke="{col}" stroke-width="12" opacity="{op}"/>'
    save("hud", "timer_ring_bg", 128, 128, ring("#0A1022", .85) + f'<circle cx="64" cy="64" r="60" fill="none" stroke="{GOLD}" stroke-width="2" opacity=".7"/><circle cx="64" cy="64" r="48" fill="none" stroke="{GOLD}" stroke-width="2" opacity=".4"/>', pivot=(.5, .5), note="처결 대기 타이머 링 배경")
    save("hud", "timer_ring_fill", 128, 128, ring("#fff", 1), pivot=(.5, .5), tint=True, note="처결 대기 타이머 링 채움(Image Filled Radial360, 시간 따라 색: 하늘→노랑→주황)")
    # 천도 버튼(청록 불꽃/연꽃) · 파혼 버튼(붉은 균열 원)
    cheon = (f'<defs>{rg("g1", CHEON, .8, 0)}</defs><circle cx="64" cy="64" r="62" fill="url(#g1)"/><circle cx="64" cy="64" r="48" fill="#0F1729" stroke="{CHEON}" stroke-width="4"/>'
             f'<path d="M64,34 q-20,22 -20,38 a20,20 0 0 0 40,0 q0,-16 -20,-38 Z" fill="{CHEON}"/><path d="M64,50 q-9,12 -9,22 a9,9 0 0 0 18,0 q0,-10 -9,-22 Z" fill="#EFFFFA"/>')
    save("hud", "btn_cheondo", 128, 128, cheon, pivot=(.5, .5), note="천도 버튼 아이콘(혼불)")
    pahon = (f'<defs>{rg("g2", "#E8683A", .75, 0)}</defs><circle cx="64" cy="64" r="62" fill="url(#g2)"/><circle cx="64" cy="64" r="48" fill="#0F1729" stroke="{RED}" stroke-width="4"/>'
             f'<path d="M64,26 L56,52 L72,62 L58,84 L68,102 M56,52 L38,58 M72,62 L92,56" stroke="{RED}" stroke-width="6" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
    save("hud", "btn_pahon", 128, 128, pahon, pivot=(.5, .5), note="파혼 버튼 아이콘(균열)")
    # 재화·상태 아이콘 64×64
    save("hud", "icon_neok", 64, 64, f'<defs>{rg("g3",CHEON,.7,0)}</defs><circle cx="32" cy="32" r="30" fill="url(#g3)"/><path d="M32,10 q-14,16 -14,28 a14,14 0 0 0 28,0 q0,-12 -14,-28 Z" fill="{CHEON}"/><path d="M32,24 q-6,8 -6,15 a6,6 0 0 0 12,0 q0,-7 -6,-15 Z" fill="#EFFFFA"/>', pivot=(.5, .5), note="넋(힘) 아이콘")
    save("hud", "icon_memory", 64, 64, f'<path d="M12,14 L46,10 L54,40 L22,54 L10,34 Z" fill="{HANJI}"/><path d="M18,22 L42,18 M20,32 L48,28 M22,42 L40,48" stroke="{MEMORY}" stroke-width="3" opacity=".9"/><path d="M12,14 L46,10 L54,40 L22,54 L10,34 Z" fill="none" stroke="{MEMORY}" stroke-width="3"/>', pivot=(.5, .5), note="기억 조각 아이콘(한지 쪽지)")
    save("hud", "icon_yeopjeon", 64, 64, f'<circle cx="32" cy="32" r="26" fill="{GOLD}"/><circle cx="32" cy="32" r="22" fill="none" stroke="#8A6A22" stroke-width="2"/><rect x="25" y="25" width="14" height="14" fill="#0F1729"/><path d="M14,22 Q20,12 30,10" stroke="#fff" stroke-width="3" opacity=".4" fill="none"/>', pivot=(.5, .5), note="엽전(파혼 보상) 아이콘")
    save("hud", "icon_karma", 64, 64, f'<circle cx="32" cy="32" r="28" fill="#1A1020" stroke="{MEMORY}" stroke-width="2" opacity=".9"/><path d="M32,12 C14,16 14,34 32,34 C50,34 50,52 32,52 M22,22 C34,18 44,26 32,32 M42,42 C30,46 20,40 32,34" stroke="{RED}" stroke-width="5" fill="none" stroke-linecap="round"/>', pivot=(.5, .5), note="업 아이콘(검붉은 매듭)")
    # 시야 축소 비네트(1024×1024): 가운데는 투명, 가장자리는 남청 먹. 천도 캐스팅 중 크기를 줄여 시야 60%를 만든다
    vd = ('<radialGradient id="vg" cx="50%" cy="50%" r="50%">'
          f'<stop offset="0" stop-color="{DEEP}" stop-opacity="0"/><stop offset="0.52" stop-color="{DEEP}" stop-opacity="0"/>'
          f'<stop offset="0.72" stop-color="{DEEP}" stop-opacity=".78"/><stop offset="1" stop-color="{DEEP}" stop-opacity="1"/></radialGradient>')
    save("hud", "vision_vignette", 1024, 1024, '<rect width="1024" height="1024" fill="url(#vg)"/>', vd, pivot=(.5, .5), note="시야 축소 가장자리 먹 번짐(Unity에서 크기 조절로 반경 100%→60%)")
    # 기억색 테두리: 흰색 링(보라 등으로 Tint)
    save("hud", "memory_rim", 1024, 1024, '<defs><radialGradient id="mr" cx="50%" cy="50%" r="50%"><stop offset=".6" stop-color="#fff" stop-opacity="0"/><stop offset=".86" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs><rect width="1024" height="1024" fill="url(#mr)"/>', pivot=(.5, .5), tint=True, note="기억색 테두리(천도 성공 0.3초 번쩍, 기억색으로 Tint)")
    # 밤 시간 바(해 질 → 동트기): 틀 + 달/해 마커
    tb = f'<defs>{lg("sky","#E8683A","#0F1729",1,0,0,0)}<linearGradient id="sky2" x1="0" x2="1"><stop offset="0" stop-color="#E8683A"/><stop offset=".25" stop-color="#3A2A5C"/><stop offset=".7" stop-color="#0F1729"/><stop offset="1" stop-color="#3A5A7C"/></linearGradient></defs>'
    tb += f'<rect x="2" y="6" width="476" height="20" rx="10" fill="url(#sky2)" stroke="{GOLD}" stroke-width="2"/>'
    save("hud", "night_bar", 480, 32, tb, pivot=(.5, .5), note="하룻밤 시간 바(해 질 녘→동트기)")
    save("hud", "night_marker", 32, 32, f'<circle cx="16" cy="16" r="13" fill="{HANJI}"/><circle cx="22" cy="12" r="11" fill="#0F1729"/><circle cx="16" cy="16" r="13" fill="none" stroke="{GOLD}" stroke-width="2"/>', pivot=(.5, .5), note="시간 바 마커(달)")
    # 한지 패널(9-slice): 모서리 24px
    save("hud", "panel_hanji", 128, 128, f'<rect x="2" y="2" width="124" height="124" rx="14" fill="#16213E" stroke="{GOLD}" stroke-width="3" opacity=".96"/><rect x="10" y="10" width="108" height="108" rx="8" fill="none" stroke="#3B4C7A" stroke-width="2"/><path d="M10,34 V10 H34 M94,10 H118 V34 M118,94 V118 H94 M34,118 H10 V94" stroke="{GOLD}" stroke-width="3" fill="none"/>', pivot=(.5, .5), note="패널 · 9-slice(테두리 24px)")


def main():
    for p in ["idle", "swing", "cast"]:
        chasa(p)
    chasa("idle", "chasa_walk_a", tilt=-4, bob=-3)    # 걷기 2프레임: 몸을 좌우로 기울이며 위아래로 흔든다
    chasa("idle", "chasa_walk_b", tilt=4, bob=0)
    chasa("idle", "chasa_hit", tilt=-9, bob=2, hit=True)
    for k in range(4):
        ghost(k)
        if k < 3:
            ghost(k, kneel=True)
    for name, base, dark, mode in TILES:
        for v in (0, 1):
            tile(name, base, dark, mode, v)
    for n, w, h, fn in [("choga", 2, 2, p_choga), ("giwa", 3, 2, p_giwa), ("stone_wall", 2, 1, p_dam), ("jars", 1, 1, p_jang), ("well", 1, 1, p_umul),
                        ("seonang_tree", 2, 2, p_namu), ("cairn", 1, 1, p_dol), ("jangseung", 1, 1, p_jangseung), ("sangyeo", 2, 1, p_sangyeo),
                        ("pyeongsang", 2, 1, p_pyeong), ("jigae", 1, 1, p_jigae), ("sotdae", 1, 1, p_sotdae)]:
        prop(n, w, h, fn)
    boss_naru(False)
    boss_naru(True)
    hud()
    with open(os.path.join(ROOT, "assets", "sprites_src", "manifest.json"), "w") as f:
        json.dump({"ppu": 128, "filter": "Bilinear", "mipmaps": False, "compression": "None", "sprites": MANIFEST}, f, ensure_ascii=False, indent=1)
    print(len(MANIFEST), "sprites")


if __name__ == "__main__":
    main()
