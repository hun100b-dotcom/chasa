"""미니맵·큰 지도의 지도 그림: 필드 전체(640m×640m)를 위에서 본 한지·먹 톤 지도.
왜 데이터로 그리나: 지도는 월드와 어긋나면 안 된다 → 높이지도(물), 땅 섞기(splat), 타일(길·보리·개울), 소품(나무·무덤), 구조물(집·다리), 구역표를 그대로 읽어서 같은 좌표로 그린다.
방향: 북쪽이 위(월드 y+ = 그림 위쪽), 동쪽이 오른쪽. 원점 = 남서쪽. 1m = PX_PER_M 픽셀.
출력(assets3d/ui/map/):
  map_field.png(2048², 한지 지도 본체, 글자 없음) / map_field_1024.png(미니맵용 축소) / map_labels.png(구역 이름, 투명 바탕) /
  map_unexplored.png(안 가 본 곳을 덮는 빈 한지, 2048² 가로세로 이어짐 아님·전체 덮개) / map_meta.json(좌표 규칙·구역·표식 좌표)
사용: python3 minimap.py [map|labels|all]"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__)); A3 = os.path.join(HERE, "..", "..", "assets3d")
OUT = os.path.join(A3, "ui", "map"); os.makedirs(OUT, exist_ok=True)
WORLD = 640.0; SIZE = 2048; S = SIZE / WORLD          # 픽셀/미터 = 3.2
HANJI = np.array([243, 231, 211], np.float32) / 255      # 한지 바탕 #F3E7D3 (palette-tokens)
INK = np.array([42, 42, 56], np.float32) / 255            # 도포 먹 #2A2A38
rng = np.random.RandomState(11)

def P(x, y): return (x * S, (WORLD - y) * S)               # 월드(m) → 그림 픽셀(북쪽 위)
def hx(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

def noise(w, h, cell, seed):
    r = np.random.RandomState(seed); g = r.rand(max(2, h // cell + 2), max(2, w // cell + 2)).astype(np.float32)
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255

def fbm(w, h, cells, seed):
    t = 0; a = 1.0; tot = 0
    for i, c in enumerate(cells): t = t + noise(w, h, c, seed + i) * a; tot += a; a *= 0.55
    return t / tot

def layer_mask(draw_fn, blur=0.0):
    im = Image.new("L", (SIZE, SIZE), 0); draw_fn(ImageDraw.Draw(im))
    return im.filter(ImageFilter.GaussianBlur(blur)) if blur else im

def paint(canvas, mask, color, alpha=1.0):
    a = (np.asarray(mask, np.float32) / 255 * alpha)[..., None]
    return canvas * (1 - a) + np.asarray(color, np.float32)[None, None, :] * a

def wobble(img_arr, amp=2.2, cells=48, seed=5):
    """붓으로 그은 듯 선이 살짝 흔들리게: 노이즈로 화소를 조금씩 옮긴다."""
    h, w = img_arr.shape[:2]
    dx = (fbm(w, h, [cells, cells * 3], seed) - 0.5) * 2 * amp; dy = (fbm(w, h, [cells, cells * 3], seed + 9) - 0.5) * 2 * amp
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32); x0 = np.clip((xs + dx).astype(int), 0, w - 1); y0 = np.clip((ys + dy).astype(int), 0, h - 1)
    return img_arr[y0, x0]

def load():
    d = json.load(open(os.path.join(A3, "layouts", "field_5x5.json")))
    im = np.asarray(Image.open(os.path.join(A3, "terrain", "heightmap.png")))
    h = (im[..., 0].astype(np.float32) * 256 + im[..., 1]) / 65535 * 9 - 1          # 행 0 = 남쪽
    sa = np.asarray(Image.open(os.path.join(A3, "terrain", "splat_a.png"))).astype(np.float32) / 255
    sb = np.asarray(Image.open(os.path.join(A3, "terrain", "splat_b.png"))).astype(np.float32) / 255
    return d, h, sa, sb

def to_img(a):   # 월드 격자(행0=남쪽) → 그림(행0=북쪽)
    return np.flipud(a)

def resize(a, n=SIZE): return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((n, n), Image.BICUBIC))

def build_map():
    d, h, sa, sb = load()
    W = H = SIZE
    # ① 한지 바탕: 큰 얼룩 + 가는 섬유 + 가장자리가 누렇게 낡음
    base = np.ones((H, W, 3), np.float32) * HANJI
    paper = fbm(W, H, [256, 64, 16, 4], 3)[..., None]; base = base * (0.93 + 0.12 * paper)
    fib = noise(W, H, 3, 8)[..., None]; fx = np.asarray(Image.fromarray((np.clip(noise(W, H, 90, 4) * 255, 0, 255)).astype(np.uint8)).resize((W, H)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None] / 255
    base = base * (1 - 0.035 * np.clip(fib - 0.55, 0, 1) * 3) - 0.0
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32); ed = np.minimum(np.minimum(xs, W - xs), np.minimum(ys, H - ys)) / (W * 0.5)
    age = np.clip(1 - ed / 0.16, 0, 1)[..., None] ** 1.6 * (0.55 + 0.45 * paper)
    base = base * (1 - age * 0.22) + np.array([0.62, 0.45, 0.25], np.float32) * age * 0.12
    c = base.copy()

    # ② 땅 번짐(담채): 풀=옅은 쑥색, 흙=황토, 자갈=회색, 낙엽=적갈, 논=청록 — 한지에 물감이 번진 듯 크게 흐리게
    def lay(a, color, k, bl=7):
        m = np.clip(to_img(resize(a)), 0, 1); m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(bl)), np.float32)
        return paint(c, Image.fromarray(m.astype(np.uint8)), color, k)
    c = lay(sa[..., 1], hx("#A9B88A"), 0.42)      # 풀
    c = lay(sa[..., 0], hx("#C9A66B"), 0.46)      # 흙
    c = lay(sa[..., 2], hx("#A5A39A"), 0.50)      # 자갈
    c = lay(sa[..., 3], hx("#9DBB9A"), 0.55)      # 논
    c = lay(sb[..., 0], hx("#A8704C"), 0.38)      # 낙엽
    # 구름 번짐(물감 얼룩) — 평면이 단조롭지 않게
    cl = fbm(W, H, [220, 90, 30], 21)[..., None]; c = c * (0.95 + 0.10 * cl)

    # ③ 땅의 높낮이: 산수화처럼 옅은 먹 음영(높이지도 기울기) + 등고선 조금
    hh = to_img(resize(h)); gy, gx = np.gradient(hh * 7.0)
    shade = np.clip(-(gx * 0.7 + gy * 0.7) * 5.0 + 0.0, -1, 1)   # 북서쪽 빛
    sm = np.asarray(Image.fromarray(((shade * 0.5 + 0.5) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255 - 0.5
    c = c * (1 - np.clip(-sm, 0, 1)[..., None] * 0.28) + np.clip(sm, 0, 1)[..., None] * 0.05

    # ④ 보리밭·비탈·개울 타일
    tiles = d["tiles"]; T = 8.0
    def trect(t, pad=0.0):
        x0, y0 = t["ix"] * T, t["iy"] * T; return [*P(x0 - pad, y0 + T + pad), *P(x0 + T + pad, y0 - pad)]
    barley = [t for t in tiles if t["tile"] == "terrain_tile_barley"]
    m = layer_mask(lambda dr: [dr.rectangle(trect(t), fill=255) for t in barley], 2.0); c = paint(c, m, hx("#D9B866"), 0.55)
    hatch = layer_mask(lambda dr: [dr.line([P(t["ix"] * T + 1 + k * 1.6, t["iy"] * T + 1.0), P(t["ix"] * T + 1 + k * 1.6, t["iy"] * T + T - 1.0)], fill=255, width=1) for t in barley for k in range(5)])
    c = paint(c, hatch, hx("#8E6B2E"), 0.55)                                    # 보리 이삭 줄무늬(세로 짧은 획)
    slopes = [t for t in tiles if t["tile"].startswith("terrain_tile_slope") or t["tile"].startswith("terrain_tile_bank") or t["tile"] == "terrain_tile_cliff_wall"]
    hs = layer_mask(lambda dr: [dr.line([P(t["ix"] * T + 0.8, t["iy"] * T + 0.8 + k * 1.9), P(t["ix"] * T + T - 0.8, t["iy"] * T + 0.8 + k * 1.9 - 0.7)], fill=255, width=1) for t in slopes for k in range(4)], 0.6)
    c = paint(c, hs, INK, 0.38)                                                 # 비탈 해칭(가는 먹선 여러 줄)

    # ⑤ 숲: 소나무=세모 겹침 먹, 느티=동그란 덩이, 마른나무=가는 가지, 덤불=점
    props = d["props"]
    def pts(prefix): return [(p["x"], p["y"]) for p in props if p["prop"].startswith(prefix)]
    dens = layer_mask(lambda dr: [dr.ellipse([*(np.array(P(x, y)) - 9), *(np.array(P(x, y)) + 9)], fill=70) for x, y in pts("nature_pine") + pts("nature_zelkova")], 12)
    c = paint(c, dens, hx("#6F8B6A"), 0.40)                                      # 숲 바탕 담채
    tr = Image.new("L", (W, H), 0); td = ImageDraw.Draw(tr)
    for i, (x, y) in enumerate(pts("nature_pine")):
        px, py = P(x + rng.uniform(-.8, .8), y + rng.uniform(-.8, .8)); s = rng.uniform(4.2, 6.0)
        td.polygon([(px, py - s * 1.5), (px - s, py + s * .2), (px + s, py + s * .2)], fill=255); td.polygon([(px, py - s * .6), (px - s * 1.15, py + s * 1.0), (px + s * 1.15, py + s * 1.0)], fill=255)
    for i, (x, y) in enumerate(pts("nature_zelkova")):
        px, py = P(x, y); s = rng.uniform(4.5, 6.5); td.ellipse([px - s, py - s * .8, px + s, py + s * .8], fill=255)
    c = paint(c, tr, hx("#3D5240"), 0.82)
    dead = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(dead)
    for x, y in pts("nature_dead"):
        px, py = P(x, y); dd.line([(px, py + 3), (px + rng.uniform(-2, 2), py - 6)], fill=255, width=1); dd.line([(px, py - 2), (px + 3.5, py - 5.5)], fill=255, width=1); dd.line([(px, py - 3), (px - 3, py - 6)], fill=255, width=1)
    c = paint(c, dead, hx("#5B5A60"), 0.85)
    bu = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(bu)
    for i, (x, y) in enumerate(pts("nature_bush") + pts("terrain_bush")):
        if i % 3: continue
        px, py = P(x, y); bd.ellipse([px - 1.8, py - 1.5, px + 1.8, py + 1.5], fill=255)
    c = paint(c, bu, hx("#6E8559"), 0.7)
    rk = Image.new("L", (W, H), 0); rd = ImageDraw.Draw(rk)
    for x, y in pts("terrain_rock_cluster") + pts("terrain_rock_medium"):
        px, py = P(x, y); rd.polygon([(px - 3.2, py + 1.8), (px - 1.4, py - 2.6), (px + 1.6, py - 2.4), (px + 3.4, py + 1.8)], fill=255)
    c = paint(c, rk, hx("#6A6A70"), 0.75)
    gv = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(gv)
    for x, y in pts("prop_grave") + pts("prop_tomb_old"):
        px, py = P(x, y); gd.ellipse([px - 3.6, py - 2.2, px + 3.6, py + 2.6], outline=255, width=1)
    c = paint(c, gv, INK, 0.7)                                                   # 무덤: 먹 타원 봉분

    # ⑥ 길: 길 타일 중심끼리 이어 두꺼운 황토 길 + 먹 가장자리
    road = [t for t in tiles if t["tile"].startswith("terrain_tile_road")]; cs = {(t["ix"], t["iy"]) for t in road}
    def rpath(dr, w):
        for (ix, iy) in cs:
            x, y = ix * T + 4, iy * T + 4
            dr.ellipse([*(np.array(P(x, y)) - w / 2), *(np.array(P(x, y)) + w / 2)], fill=255)
            for dx, dy in ((1, 0), (0, 1)):
                if (ix + dx, iy + dy) in cs: dr.line([P(x, y), P(x + dx * T, y + dy * T)], fill=255, width=int(w))
    edge = layer_mask(lambda dr: rpath(dr, 4.4 * S + 5)); core = layer_mask(lambda dr: rpath(dr, 4.4 * S))
    c = paint(c, edge, hx("#6B5238"), 0.55); c = paint(c, core, hx("#E4CD9C"), 0.95)
    c = paint(c, ImageChops.multiply(core, Image.fromarray((noise(W, H, 7, 3) * 255).astype(np.uint8))), hx("#BFA06A"), 0.3)

    # ⑦ 물: 높이지도 < 물높이(0.18) + 개울 타일(br_*·stream). 푸른 먹 번짐 + 깊은 곳 짙게 + 가장자리 흰 거품선
    wm = to_img(resize((h < 0.18).astype(np.float32)))
    deep = to_img(resize((h < -0.05).astype(np.float32)))
    stream = [t for t in tiles if t["tile"] in ("terrain_tile_stream", "br_shore", "br_deep", "br_rapids")]
    sm_ = layer_mask(lambda dr: [dr.rectangle(trect(t), fill=255) for t in stream if t["tile"] == "terrain_tile_stream"], 2.0)
    wmask = Image.fromarray((np.clip(wm, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)); wmask = ImageChops.lighter(wmask, sm_)
    wmask = Image.fromarray(((np.asarray(wmask, np.float32) / 255 > 0.45) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))
    c = paint(c, wmask, hx("#5D86A8"), 0.78)
    dmask = Image.fromarray((np.clip(deep, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)); c = paint(c, dmask, hx("#2F4F78"), 0.50)
    rip = Image.new("L", (W, H), 0); rp = ImageDraw.Draw(rip); wmn = np.asarray(wmask) > 140
    for i in range(1800):                                                         # 잔물결: 물 위 가는 가로 호선
        x = rng.randint(0, W); y = rng.randint(0, H)
        if wmn[y, x]: rp.arc([x - 7, y - 2, x + 7, y + 3], 200, 340, fill=255, width=1)
    c = paint(c, rip, hx("#EAF2F5"), 0.65)
    contour = np.asarray(wmask.filter(ImageFilter.FIND_EDGES), np.float32) / 255; c = c * (1 - np.clip(contour * 1.3, 0, 1)[..., None] * 0.55) + np.array([0.12, 0.2, 0.3], np.float32) * np.clip(contour * 1.3, 0, 1)[..., None] * 0.55

    # ⑧ 구조물: 기와=먹 회색 지붕, 초가=황토 지붕, 다리=회색 돌, 나룻배·서낭당은 아이콘이 따로 있으니 작은 표시만
    def foot(s):
        ps = s.get("pieces") or []
        if ps:
            xs_ = [p["x"] for p in ps]; ys_ = [p["y"] for p in ps]; return (min(xs_) - 1.6, min(ys_) - 1.6, max(xs_) + 1.6, max(ys_) + 1.6)
        return (s["x"] - 2, s["y"] - 2, s["x"] + 2, s["y"] + 2)
    roofs = {"choga4": "#C2A064", "choga8": "#C2A064", "giwa8": "#4F5360", "uiwon": "#4F5360", "jeongja": "#8C4B3E", "daejanggan": "#4F5360", "donghun_burnt": "#3A3436"}
    bl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd2 = ImageDraw.Draw(bl); ol = Image.new("L", (W, H), 0); od = ImageDraw.Draw(ol)
    for s in d["structures"]:
        k = s.get("kind") or s.get("piece")
        if k in roofs:
            x0, y0, x1, y1 = foot(s); a, b2 = P(x0, y1), P(x1, y0); col = tuple(int(v * 255) for v in hx(roofs[k]))
            bd2.rectangle([a, b2], fill=col + (255,)); od.rectangle([a, b2], outline=255, width=2); od.line([((a[0] + b2[0]) / 2, a[1]), ((a[0] + b2[0]) / 2, b2[1])], fill=255, width=1)   # 용마루 한 줄
        elif k == "br_stone_bridge":
            a, b2 = P(s["x"] - 4, s["y"] + 2.4), P(s["x"] + 4, s["y"] - 2.4); bd2.rectangle([a, b2], fill=(150, 146, 138, 255)); od.rectangle([a, b2], outline=255, width=2)
        elif k in ("br_ferry_dock", "br_road_pad"):
            a, b2 = P(s["x"] - 3, s["y"] + 2), P(s["x"] + 3, s["y"] - 2); bd2.rectangle([a, b2], fill=(120, 96, 66, 255)); od.rectangle([a, b2], outline=255, width=1)
        elif k in ("prop_mill", "prop_forge", "prop_prison_wall"):
            a, b2 = P(s["x"] - 3, s["y"] + 2.4), P(s["x"] + 3, s["y"] - 2.4); bd2.rectangle([a, b2], fill=(110, 98, 90, 255)); od.rectangle([a, b2], outline=255, width=1)
    sh = Image.new("L", (W, H), 0); sh.paste(bl.split()[3].filter(ImageFilter.GaussianBlur(3)).transform((W, H), Image.AFFINE, (1, 0, -4, 0, 1, -4)))   # 떨어지는 그림자
    c = paint(c, sh, INK, 0.25)
    bc = np.asarray(bl).astype(np.float32) / 255; c = c * (1 - bc[..., 3:4]) + bc[..., :3] * bc[..., 3:4]
    c = paint(c, ol, INK, 0.85)
    hy = Image.new("L", (W, H), 0); hyd = ImageDraw.Draw(hy)
    for p in props:                                                               # 짚더미·허수아비·울타리: 아주 작은 점선
        if p["prop"].startswith("prop_haystack"):
            px, py = P(p["x"], p["y"]); hyd.ellipse([px - 3, py - 3, px + 3, py + 3], fill=255)
    c = paint(c, hy, hx("#B58F3E"), 0.9)
    # ⑨ 먹선 흔들림(한 번에): 선·물감이 모두 손으로 그은 듯 아주 살짝 번지게
    c = wobble(c, 1.7, 40, 5)
    # ⑩ 가장자리: 월드 끝은 먹이 옅게 번져 사라진다(바깥은 한지) + 옅은 테두리선 한 줄
    fade = np.clip((ed - 0.012) / 0.02, 0, 1)[..., None]
    c = base * (1 - fade) + c * fade
    bo = Image.new("L", (W, H), 0); ImageDraw.Draw(bo).rectangle([int(0.012 * W), int(0.012 * H), W - int(0.012 * W), H - int(0.012 * H)], outline=255, width=2)
    c = paint(c, bo.filter(ImageFilter.GaussianBlur(0.7)), INK, 0.55)
    # 마지막 색 톤: 전체에 아주 약한 먹 번짐 + 대비
    c = np.clip((c - 0.5) * 1.05 + 0.5, 0, 1)
    im = Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8)); im.save(os.path.join(OUT, "map_field.png"), optimize=True)
    im.resize((1024, 1024), Image.LANCZOS).save(os.path.join(OUT, "map_field_1024.png"), optimize=True)
    return im

def build_unexplored():
    """안 가 본 곳을 덮는 빈 한지: 같은 한지 바탕에 옅은 먹 얼룩. 지나간 자리를 이 덮개에서 부드러운 원으로 지워 열면(알파) 지도가 드러난다."""
    W = H = SIZE
    paper = fbm(W, H, [256, 64, 16, 4], 3)[..., None]; base = np.ones((H, W, 3), np.float32) * HANJI * (0.93 + 0.12 * paper)
    smear = fbm(W, H, [300, 120, 40], 77)[..., None]; base = base * (1 - 0.10 * smear) + hx("#B9AD97") * 0.10 * smear
    im = Image.fromarray((np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)); im.save(os.path.join(OUT, "map_unexplored.png"), optimize=True)

def build_labels(d):
    """구역 이름 붓글씨(투명 바탕). 위치는 구역 사각형의 중심에서 조금 보정. 글자는 따로라 코드가 켜고 끌 수 있다."""
    import title_assets as ta
    W = H = SIZE; lab = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    spots = {"검은여울": (88, 560, 64), "솔고개 마을": (196, 106, 58), "보릿들": (330, 246, 70), "물막이 골": (384, 478, 62), "폐당집": (570, 624, 54)}
    for z in d["zones"]:
        nm = z["name"]; x, y, size = spots.get(nm, ((z["rect_m"][0] + z["rect_m"][2]) / 2, (z["rect_m"][1] + z["rect_m"][3]) / 2, 56))
        m = ta.brush_text(nm, size * 2, pad=10).resize((int(ta.brush_text(nm, size * 2, pad=10).width * 0.62), int(ta.brush_text(nm, size * 2, pad=10).height * 0.62)), Image.LANCZOS)
        px, py = P(x, y); a = np.asarray(m, np.float32) / 255; col = np.zeros((*a.shape, 4), np.uint8); col[..., :3] = (np.array([42, 32, 30]) ).astype(np.uint8); col[..., 3] = (a * 215).astype(np.uint8)
        lab.alpha_composite(Image.fromarray(col, "RGBA"), (int(px - m.width / 2), int(py - m.height / 2)))
    lab.save(os.path.join(OUT, "map_labels.png"), optimize=True)

def build_meta(d):
    mk = [{"kind": m["kind"], "name": m["name"], "x": m["x"], "y": m["y"]} for m in d["markers"]]
    meta = {"_설명": "지도 그림 좌표 규칙. 코드는 월드 좌표(x=동, y=북, 단위 m)를 그림 픽셀로 바꿔 아이콘을 놓는다.",
            "world_m": WORLD, "image_px": SIZE, "px_per_m": S, "north": "그림 위쪽", "origin": "월드 (0,0) = 그림 왼쪽 아래",
            "to_pixel": "px = x * px_per_m ; py = (world_m - y) * px_per_m   (유니티 UV: u = x/world_m, v = y/world_m, 아래가 v=0)",
            "files": {"map": "map_field.png", "map_small": "map_field_1024.png", "labels": "map_labels.png", "unexplored": "map_unexplored.png"},
            "zones": d["zones"], "markers": mk,
            "unexplored_use": "map_unexplored.png 를 지도 위에 얹고, 플레이어가 지나간 반경(권장 38m)을 부드러운 원(가장자리 12m 페더)으로 알파 0으로 지운다. 서낭당·보스 자리는 한 번 가면 영구 공개.",
            "minimap_view_m": {"radius_steps": [30, 40, 60], "note": "표준 명세 §2: 반경 30/40/60m. map_field.png 는 3.2px/m 라 반경 40m(지름 80m)가 정확히 256px = 미니맵 RenderTexture 256 과 1:1. 30m는 확대, 60m는 축소해서 쓴다. 원형 마스크는 minimap_mask_260.png"}}
    json.dump(meta, open(os.path.join(OUT, "map_meta.json"), "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"; d = json.load(open(os.path.join(A3, "layouts", "field_5x5.json")))
    sys.path.insert(0, HERE)
    if what in ("map", "all"): build_map(); build_unexplored()
    if what in ("labels", "all"): build_labels(d)
    build_meta(d); print("완료")
