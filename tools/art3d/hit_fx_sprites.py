"""1막 손맛 이펙트 그림(스프라이트) 모음. 실행: python3 hit_fx_sprites.py
왜: 무기를 휘둘러도 맞는 자리에 보이는 것이 하얀 번쩍(재질)과 숫자뿐이었다. 타격감 권장값(planning/combat/feel)은 '작은 타는 거의 안 흔들리고, 큰 타·파혼만 확 크게'라서
화면을 흔드는 대신 맞은 자리의 작고 짧은 그림이 손맛을 맡아야 한다. 그래서 무기마다 모양이 다른 '명중 그림' 5종 × (보통·마무리 2크기), 피격 번쩍, 천도·파혼·처결 대기 보강 그림을 만든다.
규약: 가로로 이어 붙인 띠 PNG(프레임 정사각 256², 투명 배경, 글자 없음). 효과의 '앞쪽'은 오른쪽(+X)이고 코드가 때린 방향으로 돌린다. 중심 = 프레임 중심.
색 원칙: 주황은 파혼 전용, 보라는 원념(적) 전용, 청백은 천도. 무기 명중 그림은 어두운 땅·밝은 땅 모두에서 읽히게 흰 중심 + 얇은 어두운 테두리.
시간: 명중 그림 전체 0.20초(6프레임 = 프레임당 0.033초), 마무리 0.30초(프레임당 0.05초). 첫 두 프레임이 가장 밝다 → 히트스톱(3~6프레임) 동안 맞은 모습이 멈춘 화면에 이미 보이도록.
산출: assets3d/fx/hit/*.png + _manifest_hit.json, 같은 파일을 unity/Assets/Resources/Sprites/fx/hit/ 에도 복사(.meta는 유니티가 만든다), 미리보기 previews/hit_fx_sheet.png."""
import os, math, json, random, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(ROOT, "assets3d", "fx", "hit"); UNITY = os.path.join(ROOT, "unity", "Assets", "Resources", "Sprites", "fx", "hit")
S = 256; SS = 4; W = S * SS    # 프레임 한 변 256, 4배로 그려 줄인다(가장자리 부드럽게)
def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def ease_out(t): return 1 - (1 - t) ** 3
def new(): return Image.new("RGBA", (W, W), (0, 0, 0, 0))
def fade(t, hold=0.25):
    """0~1 시간 → 불투명도: 처음 hold 동안 최대, 그다음 서서히 0."""
    return 1.0 if t < hold else max(0.0, 1 - (t - hold) / (1 - hold)) ** 1.4
def glow(im, radius, strength=1.0):
    """그린 그림 뒤에 번지는 빛을 깔아 준다(같은 색으로 흐려 겹침)."""
    b = im.filter(ImageFilter.GaussianBlur(radius * SS))
    a = np.array(b).astype(float); a[..., 3] *= strength
    return Image.alpha_composite(Image.fromarray(a.clip(0, 255).astype(np.uint8)), im)
def tint_alpha(im, k):
    a = np.array(im).astype(float); a[..., 3] *= k; return Image.fromarray(a.clip(0, 255).astype(np.uint8))
def done(frames, name, fps_note):
    """프레임 리스트(W×W)를 256²로 줄여 가로 띠로 저장하고 매니페스트 항목을 돌려준다."""
    strip = Image.new("RGBA", (S * len(frames), S), (0, 0, 0, 0))
    for i, f in enumerate(frames): strip.paste(f.resize((S, S), Image.LANCZOS), (i * S, 0))
    strip.save(os.path.join(OUT, name + ".png")); return {"file": name + ".png", "frames": len(frames), "frame_px": S, **fps_note}
def arc_poly(cx, cy, r, a0, a1, w0, w1, n=28):
    """a0→a1(도) 호를 따라 굵기가 w0→w1로 변하는 초승달 모양 다각형(점 목록)."""
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n; a = math.radians(a0 + (a1 - a0) * u); w = w0 + (w1 - w0) * math.sin(math.pi * u) ** 0.8 * 1.0
        outer.append((cx + math.cos(a) * (r + w / 2), cy - math.sin(a) * (r + w / 2))); inner.append((cx + math.cos(a) * (r - w / 2), cy - math.sin(a) * (r - w / 2)))
    return outer + inner[::-1]

# ───────── 철삭: 사슬 채찍이 스치는 초승달 + 불똥 ─────────
def chain(big=False):
    n = 6; fr = []; rnd = random.Random(11 if not big else 12); k = 1.35 if big else 1.0
    sparks = [(rnd.uniform(-35, 35), rnd.uniform(0.4, 1.0)) for _ in range(9 if big else 6)]
    for i in range(n):
        t = 0.12 + 0.88 * i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx, cy = W * 0.36, W * 0.5
        sweep = ease_out(min(1, t * 3.4)); a1 = -50 + 100 * sweep; R = W * 0.26 * k
        wmax = W * (0.15 if big else 0.11) * (1 - 0.55 * t)
        d.polygon(arc_poly(cx, cy, R, -50, a1, 0, wmax), fill=rgb("#BFE8FF") + (255,))                 # 겉 번짐색
        d.polygon(arc_poly(cx, cy, R, -50, a1, 0, wmax * 0.55), fill=(255, 255, 255, 255))               # 흰 중심
        im = glow(tint_alpha(im, fade(t, 0.2)), 9, 0.8)
        d = ImageDraw.Draw(im)
        for ang, sp in sparks:                                                                                      # 불똥: 호 끝에서 바깥으로 튀며 줄어듦
            a = math.radians(ang + a1 * 0.2); dist = W * (0.1 + 0.34 * ease_out(t) * sp) * k; x = cx + R + math.cos(a) * dist * 0.9; y = cy - math.sin(a) * dist; rr = W * 0.012 * (1 - t) * (1.4 if big else 1)
            if rr > 1: d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255, int(255 * fade(t, 0.1))))
        fr.append(im)
    return fr
# ───────── 육모방망이: 둔탁한 별 모양 충격 + 먼지 고리 ─────────
def mace(big=False):
    n = 6; fr = []; k = 1.4 if big else 1.0
    for i in range(n):
        t = 0.12 + 0.88 * i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx = cy = W / 2
        ring_r = W * (0.1 + 0.3 * ease_out(t)) * k
        if t > 0.1: d.ellipse([cx - ring_r, cy - ring_r * 0.7, cx + ring_r, cy + ring_r * 0.7], outline=rgb("#D8C8A8") + (int(200 * fade(t, 0.2)),), width=int(W * 0.03 * (1 - t) + 2))   # 먼지 고리(위에서 본 타원)
        pts = []; spikes = 8; R0 = W * (0.06 + 0.26 * ease_out(min(1, t * 1.6))) * k
        for j in range(spikes * 2):
            a = j / (spikes * 2) * math.tau + 0.2; r = R0 if j % 2 == 0 else R0 * 0.42; pts.append((cx + math.cos(a) * r, cy - math.sin(a) * r))
        star = new(); sd = ImageDraw.Draw(star); sd.polygon(pts, fill=rgb("#F3E7D3") + (255,)); sd.polygon([(cx + (x - cx) * 0.6, cy + (y - cy) * 0.6) for x, y in pts], fill=(255, 255, 255, 255))
        star = glow(tint_alpha(star, fade(t, 0.15)), 7, 0.7); im = Image.alpha_composite(im, star)
        fr.append(im)
    return fr
# ───────── 요령방울: 겹쳐 퍼지는 울림 고리(소리의 파문) ─────────
def bell(big=False):
    n = 6; fr = []; k = 1.4 if big else 1.0
    for i in range(n):
        t = 0.12 + 0.88 * i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx = cy = W / 2
        for j, (delay, col) in enumerate(((0.0, "#FFF2C8"), (0.18, "#D4A94E"), (0.36, "#7FD6C8") if big else (0.36, "#D4A94E"))):
            tt = (t - delay) / (1 - delay)
            if tt <= 0: continue
            r = W * (0.05 + 0.4 * ease_out(tt)) * k; a = int(255 * fade(tt, 0.1) * (1 - 0.2 * j)); wd = max(2, int(W * 0.035 * (1 - tt)))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=rgb(col) + (a,), width=wd)
        for j in range(8):           # 고리에서 퍼지는 짧은 점선 틱
            a = j / 8 * math.tau; r0 = W * (0.1 + 0.34 * ease_out(t)) * k; r1 = r0 + W * 0.04 * (1 - t)
            d.line([cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * r1, cy + math.sin(a) * r1], fill=rgb("#FFF2C8") + (int(255 * fade(t, 0.1)),), width=3)
        fr.append(glow(im, 6, 0.6))
    return fr
# ───────── 삼지창: 세 줄 찌르기 + 점 번쩍 ─────────
def trident(big=False):
    n = 6; fr = []; k = 1.35 if big else 1.0
    for i in range(n):
        t = 0.12 + 0.88 * i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx, cy = W * 0.3, W / 2
        L = W * 0.55 * ease_out(min(1, t * 5)) * k
        for off, ln in ((-0.09, 0.8), (0.0, 1.0), (0.09, 0.8)):
            y = cy + off * W * k; w = max(3, int(W * 0.022 * (1 - t * 0.6))); d.polygon([(cx, y - w), (cx + L * ln, y), (cx, y + w)], fill=rgb("#DCEBFF") + (255,))
        d.ellipse([cx - W * 0.07 * (1 - t) * k, cy - W * 0.07 * (1 - t) * k, cx + W * 0.07 * (1 - t) * k, cy + W * 0.07 * (1 - t) * k], fill=(255, 255, 255, 255))
        im = glow(tint_alpha(im, fade(t, 0.2)), 6, 0.9); fr.append(im)
    return fr
# ───────── 명부 붓: 먹 튐 ─────────
def brush(big=False):
    n = 6; fr = []; rnd = random.Random(21 if not big else 22); k = 1.35 if big else 1.0
    blobs = [(rnd.uniform(0, math.tau), rnd.uniform(0.3, 1.0), rnd.uniform(0.02, 0.06)) for _ in range(10 if big else 7)]
    for i in range(n):
        t = 0.12 + 0.88 * i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx = cy = W / 2
        for ang, sp, sz in blobs:
            dist = W * (0.04 + 0.34 * ease_out(t) * sp) * k; x = cx + math.cos(ang) * dist; y = cy + math.sin(ang) * dist * 0.85; rr = W * sz * (1 - 0.3 * t) * (1.3 if big else 1.0)
            d.ellipse([x - rr * 1.25, y - rr * 1.25, x + rr * 1.25, y + rr * 1.25], fill=(246, 244, 236, int(255 * fade(t, 0.3))))   # 종이색 테두리(밝은 땅에서도 먹이 읽힘이 아니라 어두운 땅에서 읽히게)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=rgb("#14121A") + (int(255 * fade(t, 0.3)),))
            if t > 0.1: d.line([cx, cy, x, y], fill=rgb("#14121A") + (int(200 * fade(t, 0.2)),), width=max(2, int(rr * 0.5)))
        r = W * 0.1 * (1 - t) * k; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb("#14121A") + (int(255 * fade(t, 0.4)),))
        fr.append(im)
    return fr
# ───────── 피격 번쩍: 맞은 자리에 짧게 뜨는 흰 점광(별 4갈래) ─────────
def hit_flash():
    n = 4; fr = []
    for i in range(n):
        t = i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx = cy = W / 2; R = W * (0.34 - 0.14 * t); r = R * 0.16
        for a0 in (0, 90):
            a = math.radians(a0); d.polygon([(cx + math.cos(a) * R, cy - math.sin(a) * R), (cx - math.sin(a) * r, cy - math.cos(a) * r), (cx - math.cos(a) * R, cy + math.sin(a) * R), (cx + math.sin(a) * r, cy + math.cos(a) * r)], fill=(255, 255, 255, 255))
        d.ellipse([cx - R * 0.35, cy - R * 0.35, cx + R * 0.35, cy + R * 0.35], fill=(255, 255, 255, 255))
        fr.append(glow(tint_alpha(im, fade(t, 0.3)), 10, 1.0))
    return fr
# ───────── 차사가 맞았을 때 화면 가장자리 붉은 번쩍(한 장, 코드가 알파로 0.15초 깜빡임) ─────────
def player_hit_vignette():
    w, h = 512, 288; y, x = np.mgrid[0:h, 0:w]; dx = (x - w / 2) / (w / 2); dy = (y - h / 2) / (h / 2); r = np.sqrt(dx ** 2 * 0.8 + dy ** 2)
    a = np.clip((r - 0.55) / 0.55, 0, 1) ** 1.8; img = np.zeros((h, w, 4), np.uint8); img[..., 0] = 200; img[..., 1] = 30; img[..., 2] = 36; img[..., 3] = (a * 190).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(OUT, "hit_player_vignette.png")); return {"file": "hit_player_vignette.png", "frames": 1, "frame_px": [w, h], "life_s": 0.15, "note": "화면 전체에 늘려 덮고 알파를 0.15초 안에 1→0. 가장자리만 붉고 가운데는 비어 시야를 안 가린다"}
# ───────── 천도: 위로 오르는 청백 불티(느림=보냄) ─────────
def tendo_motes():
    n = 8; fr = []; rnd = random.Random(31); pts = [(rnd.uniform(-0.28, 0.28), rnd.uniform(0.0, 0.6), rnd.uniform(0.012, 0.03)) for _ in range(16)]
    for i in range(n):
        t = i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx = W / 2
        for x0, h0, sz in pts:
            y = W * (0.9 - (h0 + 0.5 * t) * 1.2 * 0.8); x = cx + W * x0 * (1 + 0.3 * t) + math.sin(t * 5 + h0 * 9) * W * 0.012; a = int(255 * min(1, t * 4) * (1 - t) ** 0.7); rr = W * sz
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=rgb("#EAF4FF") + (a,))
        fr.append(glow(im, 5, 1.0))
    return fr
# ───────── 파혼: 주황 충격 고리 + 중심 번쩍(히트스톱 8프레임 동안은 첫 프레임을 붙잡아 둔다) ─────────
def pahon_ring():
    n = 8; fr = []
    for i in range(n):
        t = i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx = cy = W / 2; r = W * (0.08 + 0.4 * ease_out(t))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=rgb("#FFB347") + (int(255 * fade(t, 0.1)),), width=max(3, int(W * 0.05 * (1 - t))))
        r2 = r * 0.82; d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=rgb("#FFE0A0") + (int(200 * fade(t, 0.1)),), width=max(2, int(W * 0.02 * (1 - t))))
        if t < 0.5: rr = W * 0.22 * (1 - t * 2); d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(255, 255, 255, int(255 * (1 - t * 2))))
        fr.append(glow(im, 8, 0.9))
    return fr
# ───────── 처결 대기: 마지막 2초 경고 맥박(고리 바깥으로 번지는 빛) 3색 ─────────
def wait_pulse(col):
    n = 4; fr = []
    for i in range(n):
        t = i / (n - 1); im = new(); d = ImageDraw.Draw(im); cx = cy = W / 2; r = W * (0.3 + 0.12 * t)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=rgb(col) + (int(255 * (1 - t) ** 0.8),), width=max(3, int(W * 0.04 * (1 - 0.5 * t))))
        fr.append(glow(im, 8, 1.0))
    return fr

GROUPS = [("hit_chain", chain, False, dict(life_s=0.20, fps=30, weapon="철삭", use="보통 타")), ("hit_chain_big", chain, True, dict(life_s=0.30, fps=20, weapon="철삭", use="3타 마무리·견인 명중")),
          ("hit_mace", mace, False, dict(life_s=0.20, fps=30, weapon="육모방망이", use="보통 타")), ("hit_mace_big", mace, True, dict(life_s=0.30, fps=20, weapon="육모방망이", use="3타 내려찍기")),
          ("hit_bell", bell, False, dict(life_s=0.20, fps=30, weapon="요령방울", use="보통 타")), ("hit_bell_big", bell, True, dict(life_s=0.30, fps=20, weapon="요령방울", use="3타 종")),
          ("hit_trident", trident, False, dict(life_s=0.20, fps=30, weapon="삼지창", use="보통 타")), ("hit_trident_big", trident, True, dict(life_s=0.30, fps=20, weapon="삼지창", use="3타 찌르기")),
          ("hit_brush", brush, False, dict(life_s=0.20, fps=30, weapon="명부 붓", use="보통 타")), ("hit_brush_big", brush, True, dict(life_s=0.30, fps=20, weapon="명부 붓", use="3타 먹 뿌리기"))]
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); os.makedirs(UNITY, exist_ok=True); man = {}
    for name, fn, big, meta in GROUPS: man[name] = done(fn(big), name, meta)
    man["hit_flash"] = done(hit_flash(), "hit_flash", dict(life_s=0.12, fps=33, use="모든 명중 위에 겹치는 흰 점광. 적 재질 번쩍(0.09초)과 같이"))
    man["tendo_motes"] = done(tendo_motes(), "tendo_motes", dict(life_s=0.8, fps=10, use="천도 완료 슬로모(0.35초) 동안 시작해 0.8초 위로 오르며 사라짐. 흔들림·번쩍 없음(보냄)"))
    man["pahon_ring"] = done(pahon_ring(), "pahon_ring", dict(life_s=0.4, fps=20, use="파혼 폭발: 히트스톱 8프레임 동안 첫 프레임에 붙들었다가 풀리며 반경 끝(3.55m)까지 퍼짐. 주황은 파혼 전용"))
    for k, c in (("fresh", "#8FD8FF"), ("day", "#FFD966"), ("old", "#C0704A")): man[f"wait_pulse_{k}"] = done(wait_pulse(c), f"wait_pulse_{k}", dict(life_s=0.5, fps=8, use="처결 대기 남은 2초부터 0.5초마다 맥박(고리 지름 1.8m 기준). 소리 예고와 같이"))
    man["hit_player_vignette"] = player_hit_vignette()
    json.dump({"_설명": "1막 손맛 이펙트 그림. 띠 PNG를 frame_px 정사각으로 잘라 life_s 동안 차례로. 앞쪽=+X(코드가 회전). 글자 없음.", "sprites": man}, open(os.path.join(OUT, "_manifest_hit.json"), "w"), ensure_ascii=False, indent=1)
    for f in os.listdir(OUT):
        if f.endswith((".png", ".json")): shutil.copy(os.path.join(OUT, f), os.path.join(UNITY, f))
    # 미리보기: 프레임을 어두운 땅·밝은 땅 위에 나란히(위 어두움 / 아래 밝음)
    names = [k for k in man if k != "hit_player_vignette"]; fw = 8 * 96; rows = len(names)
    sheet = Image.new("RGBA", (fw * 2 + 10, rows * 96), (0, 0, 0, 255))
    for r, k in enumerate(names):
        im = Image.open(os.path.join(OUT, man[k]["file"])); n = man[k]["frames"]
        for side, bg in enumerate(((40, 44, 40, 255), (178, 170, 150, 255))):
            tile = Image.new("RGBA", (96 * n, 96), bg); fr = im.resize((96 * n, 96), Image.LANCZOS); tile = Image.alpha_composite(tile, fr); sheet.paste(tile, (side * (fw + 10), r * 96))
    sheet.convert("RGB").save(os.path.join(ROOT, "assets3d", "previews", "hit_fx_sheet.png"))
    print(len(man), "개", sorted(man))
