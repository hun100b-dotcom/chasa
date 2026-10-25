"""필드 '바닥 채움' 키트 — 풀 뭉치·들꽃·보리 이랑·돌·강변 소품·밭 소품. 실행: python3 cover_kit.py  (Blender 5.x, bpy)
왜 만드나(오너 지시): 나무·덤불만 있고 땅이 텅 비어 보였다. 보릿들(탁 트인 밭)·길가·강변은 '발밑 1m 이하의 작은 것'이 빠져 있다.
규약은 nature.py 와 같다: GLB, 1유닛=1m, 원점=바닥 한가운데, 재질은 베이스컬러만. 모두 낮고(0.1~1.4m) 가벼워서(대부분 60~200 삼각형)
수천 개를 흩뿌려도(GPU 인스턴싱) 버틴다. 충돌(몸 막힘)은 넣지 않는다 — 걸어 지나가는 장식이다.
산출: assets3d/nature/cover_*.glb, assets3d/nature/_report_cover.json, assets3d/previews/cover_kit_50deg.png"""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
TAU = math.tau

# ── 색: 지형 알베도(terrain_ground.py)의 풀·보리 색과 같은 계열로 맞춘다(바닥과 따로 놀지 않게)
G_DARK, G_MID, G_LIGHT, G_DRY = "#4F7A3B", "#678546", "#8AA357", "#A09F5C"
B_GREEN, B_GOLD, B_EAR = "#8FA24E", "#C9B764", "#D8C26A"

def blade_set(n, h, spread, cols, seed, bend=0.35, w=0.05, line=None):
    """풀잎 n장. line=(길이m) 이면 원 대신 한 줄(이랑)로 늘어선다. 잎마다 키·기울기·색이 조금씩 다르다."""
    r = random.Random(seed); p = []
    for i in range(n):
        if line:
            x, y = (r.random() - .5) * 2 * w * 0.6, (r.random() - .5) * line
        else:
            a0 = r.random() * TAU; d = math.sqrt(r.random()) * spread; x, y = math.cos(a0) * d, math.sin(a0) * d
        a = r.random() * TAU; hh = h * (0.65 + r.random() * 0.6); b = bend * (0.4 + r.random() * 0.9)
        tip = (x + math.cos(a) * b * hh * 0.5, y + math.sin(a) * b * hh * 0.5, hh)
        p.append(limb(f"blade{i}", (x, y, 0.02), tip, w, 0.0, cols[i % len(cols)], 3))
    return p

def grass_a(): return blade_set(20, 0.5, 0.34, [G_MID, G_LIGHT, "#9DB863"], 21, 0.5, 0.07)
def grass_b(): return blade_set(24, 0.78, 0.4, [G_DRY, "#B8A468", G_LIGHT], 22, 0.6, 0.06)
def grass_c(): return blade_set(12, 0.3, 0.26, [G_MID, "#7BA050"], 23, 0.35, 0.06)

def stalks_with_ears(n, h, spread, seed, line=None, ripe=0.6, w=0.035):
    """보리·벼과 줄기. 이삭(길쭉한 노란 알갱이)을 줄기 끝에 단다. ripe=이삭 달린 줄기 비율."""
    r = random.Random(seed); p = []
    for i in range(n):
        if line:
            x, y = (r.random() - .5) * 0.22, (r.random() - .5) * line
        else:
            a0 = r.random() * TAU; d = math.sqrt(r.random()) * spread; x, y = math.cos(a0) * d, math.sin(a0) * d
        a = r.random() * TAU; hh = h * (0.8 + r.random() * 0.35); b = 0.18 * (0.5 + r.random())
        tip = (x + math.cos(a) * b * hh * 0.5, y + math.sin(a) * b * hh * 0.5, hh)
        p.append(limb(f"st{i}", (x, y, 0.02), tip, w, 0.012, B_GREEN if r.random() > 0.35 else G_LIGHT, 3))
        if r.random() < ripe:
            # 이삭: 줄기 끝을 따라 살짝 누운 작은 원뿔
            p.append(limb(f"ear{i}", tip, (tip[0] + math.cos(a) * 0.05, tip[1] + math.sin(a) * 0.05, tip[2] + 0.16), 0.032, 0.006, B_EAR if r.random() > 0.4 else B_GOLD, 4))
    return p
def barley_a(): return stalks_with_ears(14, 0.85, 0.3, 31)
def barley_clumps(seed, length, h, ripe, step=0.36):
    """이랑 한 줄을 포기(뭉치) 단위로 만든다: 포기마다 곧은 줄기 3대 + 바깥으로 휘어진 넓은 잎 3장. 가는 막대기만 줄지어 선 모양을 막는다."""
    r = random.Random(seed); p = []
    n = int(length / step)
    for k in range(n):
        y = -length / 2 + (k + 0.5) * step + (r.random() - .5) * 0.08
        for i in range(3):
            a = r.random() * TAU; hh = h * (0.85 + r.random() * 0.3); tip = (math.cos(a) * 0.04, y + math.sin(a) * 0.04, hh)
            p.append(limb(f"s{k}_{i}", (0, y, 0.02), tip, 0.045, 0.018, B_GREEN if r.random() > 0.3 else G_LIGHT, 3))
            if r.random() < ripe: p.append(limb(f"e{k}_{i}", tip, (tip[0], tip[1] + 0.02, tip[2] + 0.2), 0.045, 0.01, B_EAR if r.random() > 0.35 else B_GOLD, 4))
        for i in range(3):
            a = (i / 3 + r.random() * 0.2) * TAU; ln = 0.42 + r.random() * 0.14
            p.append(limb(f"l{k}_{i}", (0, y, 0.02), (math.cos(a) * ln * 0.55, y + math.sin(a) * ln * 0.55, h * 0.62), 0.065, 0.0, "#7C9650" if i % 2 else "#678546", 3))
    return p
def barley_row(): return barley_clumps(32, 3.8, 0.78, 0.5)                 # 이랑 한 줄 3.8m. 지형 이랑(칸 안 7줄, 1.04m 간격, 남북)과 같은 방향으로 놓는다
def barley_row_ripe(): return barley_clumps(33, 3.8, 0.92, 0.95)           # 누렇게 익은 쪽(구역 단위로 섞어 변화)

def flower_stem(x, y, h, col, head=0.07, seed=0):
    r = random.Random(seed); a = r.random() * TAU; tip = (x + math.cos(a) * 0.05, y + math.sin(a) * 0.05, h)
    return [limb("fs", (x, y, 0.02), tip, 0.014, 0.01, G_DARK, 3), sphere("fh", head, (tip[0], tip[1], h + head * 0.5), col, 5, 3, (1, 1, 0.7))]
def flowers(cols, n, h, spread, seed, head=0.07):
    r = random.Random(seed); p = blade_set(8, 0.22, spread, [G_MID, G_DARK], seed + 1, 0.4, 0.035)
    for i in range(n):
        a0 = r.random() * TAU; d = math.sqrt(r.random()) * spread
        p += flower_stem(math.cos(a0) * d, math.sin(a0) * d, h * (0.7 + r.random() * 0.6), cols[i % len(cols)], head, seed * 7 + i)
    return p
def flower_mix(): return flowers(["#EDE8D0", "#E8C15A", "#9A7FD0", "#EDE8D0"], 12, 0.32, 0.35, 41)
def flower_white(): return flowers(["#EDE8D0", "#F6F1E0"], 10, 0.4, 0.3, 42, 0.08)      # 개망초 느낌
def lily_red():
    """상사화(꽃무릇): 잎 없이 붉은 꽃만 솟는 저승 꽃. 강변·무덤가에 둔다. 꽃은 가느다란 호를 그리는 붉은 꽃잎 여섯 장."""
    r = random.Random(43); p = []
    for i in range(5):
        a0 = r.random() * TAU; d = math.sqrt(r.random()) * 0.28; x, y = math.cos(a0) * d, math.sin(a0) * d; h = 0.5 + r.random() * 0.25
        p.append(limb(f"s{i}", (x, y, 0.02), (x, y, h), 0.015, 0.012, "#7A8A4A", 3))
        for k in range(6):
            a = k / 6 * TAU + r.random() * 0.3
            p.append(limb(f"p{i}{k}", (x, y, h), (x + math.cos(a) * 0.17, y + math.sin(a) * 0.17, h + 0.06 - 0.04 * (k % 2)), 0.012, 0.004, "#C23B3B", 3))
    return p
def thistle():
    r = random.Random(44); p = blade_set(9, 0.3, 0.3, ["#5E7A3E", G_DARK], 44, 0.6, 0.045)
    for i in range(3):
        a0 = r.random() * TAU; d = r.random() * 0.15; x, y = math.cos(a0) * d, math.sin(a0) * d; h = 0.55 + r.random() * 0.25
        p += [limb(f"ts{i}", (x, y, 0.02), (x, y, h), 0.016, 0.012, G_DARK, 3), sphere(f"th{i}", 0.07, (x, y, h + 0.04), "#8E5CB5", 5, 3), sphere(f"tb{i}", 0.06, (x, y, h - 0.03), G_MID, 5, 3)]
    return p

# ── 돌·흙
def rock(name, r, c, mat_, sq=(1, 1, 0.6), seg=6, rings=4, rot=(0, 0, 0)): return sphere(name, r, c, mat_, seg, rings, sq, rot)
def pebbles(n, spread, seed, cols=("#B7AE98", "#86816F", "#9C9684"), rmin=0.05, rmax=0.13):
    r = random.Random(seed); p = []
    for i in range(n):
        a = r.random() * TAU; d = math.sqrt(r.random()) * spread; rr = rmin + r.random() * (rmax - rmin)
        p.append(rock(f"pb{i}", rr, (math.cos(a) * d, math.sin(a) * d, rr * 0.35), cols[i % len(cols)], (1, 0.8 + r.random() * 0.4, 0.55), 5, 3, (0, 0, r.random() * TAU)))
    return p
def stones_a(): return pebbles(7, 0.45, 51)
def stones_b(): return [rock("big", 0.42, (0, 0, 0.16), "#86816F", (1.1, 0.9, 0.6)), rock("mid", 0.24, (0.5, 0.2, 0.08), "#9C9684", (1, 1, 0.55)), sphere("moss", 0.3, (0, 0, 0.3), "#3E5E35", 6, 3, (1, 0.9, 0.3))] + pebbles(4, 0.7, 52)
def stones_shore(): return pebbles(16, 0.85, 53, ("#A8A89A", "#7F8478", "#B9B6A4", "#6E7468"), 0.06, 0.16) + [rock("flat", 0.4, (0.1, -0.1, 0.07), "#8A8E82", (1.3, 1, 0.3))]
def wet_boulder(): return [rock("b", 0.62, (0, 0, 0.16), "#6E7468", (1.2, 1, 0.55), 7, 5), rock("c", 0.3, (0.7, 0.25, 0.06), "#7F8478", (1.2, 1, 0.5)), sphere("slime", 0.4, (0, 0, 0.1), "#3E5E35", 6, 3, (1.1, 0.9, 0.3))]
def mud_patch(): return [sphere("m", 0.9, (0, 0, 0.0), "#5C4A33", 8, 3, (1.0, 0.8, 0.07)), sphere("m2", 0.5, (0.6, 0.3, 0.0), "#4F3F2B", 7, 3, (1.0, 1, 0.08))] + pebbles(3, 0.7, 54, ("#7A6648", "#8D8878"), 0.04, 0.08)
def leaf_litter():
    r = random.Random(55); p = [sphere("l", 0.8, (0, 0, 0.0), "#7A5636", 8, 3, (1.0, 0.9, 0.06))]
    for i in range(10):
        a = r.random() * TAU; d = math.sqrt(r.random()) * 0.7
        p.append(box(f"lf{i}", (0.13, 0.07, 0.01), (math.cos(a) * d, math.sin(a) * d, 0.04), ["#8B6A34", "#A0763A", "#6C4A2A"][i % 3], (0, 0, r.random() * TAU)))
    return p
def moss_patch(): return [sphere("m", 0.75, (0, 0, 0.0), "#3E5E35", 8, 3, (1.0, 0.85, 0.1)), sphere("m2", 0.4, (0.5, -0.2, 0.0), "#4E7340", 7, 3, (1.0, 1.0, 0.12))] + blade_set(10, 0.12, 0.6, ["#4E7340", "#5A7B3E"], 56, 0.2, 0.03)

# ── 강변
def driftwood():
    return [limb("log", (-0.95, 0, 0.12), (0.95, 0.15, 0.2), 0.14, 0.1, "#6B5E50", 6), limb("br1", (-0.2, 0.02, 0.17), (-0.5, 0.45, 0.4), 0.05, 0.01, "#6B5E50", 4), limb("br2", (0.3, 0.07, 0.19), (0.55, -0.4, 0.35), 0.045, 0.01, "#6B5E50", 4),
            cyl("cut", 0.14, 0.12, 0.04, (0.95, 0.15, 0.1), "#B8A468", 6, (0, math.pi / 2, 0.15))] + pebbles(4, 0.9, 57)
def cattail():
    """부들: 갈색 소시지 이삭이 달린 키 큰 풀. 갈대(1.8~2.5m)보다 낮은 1.3m 라 강변 앞줄에 둔다."""
    r = random.Random(58); p = []
    for i in range(7):
        a0 = r.random() * TAU; d = math.sqrt(r.random()) * 0.35; x, y = math.cos(a0) * d, math.sin(a0) * d; h = 1.0 + r.random() * 0.5
        a = r.random() * TAU; tip = (x + math.cos(a) * 0.08, y + math.sin(a) * 0.08, h)
        p += [limb(f"c{i}", (x, y, 0.02), tip, 0.02, 0.012, "#7A8A4A", 3), cyl(f"h{i}", 0.04, 0.04, 0.2, (tip[0] - 0.0, tip[1], h - 0.3), "#6C4A2A", 5)]
    return p + blade_set(14, 0.8, 0.45, ["#6E8A44", "#5A7B3E"], 59, 0.5, 0.04)
def reed_short(): return blade_set(30, 1.1, 0.55, ["#B4A66A", "#9C9060", "#8A8A50"], 60, 0.4, 0.04)

# ── 밭·길가 소품
def straw_stand():
    """볏단(짚단) 세워 둔 것: 세 단을 서로 기대어 묶은 모양."""
    p = []
    for i in range(3):
        a = i / 3 * TAU; tip = (math.cos(a) * 0.06, math.sin(a) * 0.06, 0.95)
        p.append(limb(f"sh{i}", (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.0), tip, 0.2, 0.06, "#C9B764", 6))
    return p + [cyl("band", 0.1, 0.1, 0.05, (0, 0, 0.72), "#6B4A2E", 6), blade_set(6, 0.18, 0.4, ["#C9B764"], 61, 0.5, 0.03)[0]]
def hoe_basket():
    """밭 한켠에 두고 간 호미와 소쿠리."""
    r = random.Random(62)
    p = [cyl("bk", 0.28, 0.22, 0.2, (0.4, 0.1, 0.0), "#B89A55", 8), cyl("bk_in", 0.24, 0.2, 0.02, (0.4, 0.1, 0.18), "#5A3E2A", 8),
         limb("hoeh", (-0.5, -0.2, 0.05), (0.1, -0.05, 0.14), 0.025, 0.025, "#6B4A2E", 4), box("hoeb", (0.14, 0.04, 0.02), (-0.55, -0.22, 0.04), "#3A3A44", (0, 0, 0.3))]
    return p + [sphere(f"vg{i}", 0.06, (0.35 + r.random() * 0.1, 0.05 + r.random() * 0.1, 0.22), "#E8C15A", 4, 3) for i in range(3)]
def stone_wall():
    """밭두렁 돌담 한 토막(길이 2m, 높이 0.55m). 돌을 둥글게 쌓은 모양."""
    r = random.Random(63); p = []
    for row in range(3):
        n = 5 - row
        for i in range(n):
            rr = 0.2 - row * 0.02 + r.random() * 0.04
            p.append(rock(f"w{row}{i}", rr, (-0.8 + row * 0.2 + i * 0.4, (r.random() - .5) * 0.1, 0.12 + row * 0.17),
                          ["#86816F", "#9C9684", "#706A5A"][(i + row) % 3], (1.2, 1.0, 0.8), 6, 4, (0, 0, r.random() * TAU)))
    return p + [sphere("mosscap", 0.35, (0.2, 0, 0.5), "#3E5E35", 6, 3, (1.5, 0.8, 0.25))]
def boundary_stake():
    return [cyl("stk", 0.05, 0.04, 0.85, (0, 0, 0), "#6B4A2E", 5), box("tag", (0.18, 0.02, 0.2), (0.09, 0, 0.72), "#E8DDA8", (0, 0, 0.1)), box("tag2", (0.02, 0.02, 0.2), (0.0, 0, 0.72), "#E85C41")] + pebbles(3, 0.25, 64, ("#86816F",), 0.04, 0.09)
def wayside_cairn():
    """길가 작은 돌탑(소원 쌓기). 서낭당 돌무더기보다 훨씬 작고 흔한 것."""
    r = random.Random(65); p = []
    for i, (rr, z) in enumerate([(0.26, 0.1), (0.2, 0.26), (0.15, 0.38), (0.1, 0.48)]):
        p.append(rock(f"c{i}", rr, ((r.random() - .5) * 0.05, (r.random() - .5) * 0.05, z), ["#86816F", "#9C9684", "#706A5A", "#B7AE98"][i], (1, 1, 0.7), 6, 4))
    return p + pebbles(5, 0.5, 66)
def cow_dung_hay():
    """볏짚 흩어진 자리(수레 지나간 길가)."""
    r = random.Random(67); p = []
    for i in range(12):
        a = r.random() * TAU; d = math.sqrt(r.random()) * 0.5
        c = (math.cos(a) * d, math.sin(a) * d, 0.03)
        p.append(limb(f"h{i}", c, (c[0] + math.cos(r.random() * TAU) * 0.35, c[1] + math.sin(r.random() * TAU) * 0.35, 0.05), 0.012, 0.004, ["#C9B764", "#B89A55"][i % 2], 3))
    return p

COVER = {"grass_a": grass_a, "grass_b": grass_b, "grass_c": grass_c, "barley_a": barley_a, "barley_row": barley_row, "barley_row_ripe": barley_row_ripe,
         "flower_mix": flower_mix, "flower_white": flower_white, "lily_red": lily_red, "thistle": thistle,
         "stones_a": stones_a, "stones_b": stones_b, "stones_shore": stones_shore, "wet_boulder": wet_boulder, "mud_patch": mud_patch, "leaf_litter": leaf_litter, "moss_patch": moss_patch,
         "driftwood": driftwood, "cattail": cattail, "reed_short": reed_short,
         "straw_stand": straw_stand, "hoe_basket": hoe_basket, "stone_wall": stone_wall, "boundary_stake": boundary_stake, "wayside_cairn": wayside_cairn, "hay_scatter": cow_dung_hay}

def run():
    rep = []
    for key, fn in COVER.items():
        reset(); o = join(f"cover_{key}", fn()); lo, hi = bounds(o)
        rep.append({"name": f"cover_{key}", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
        export(o, os.path.join(OUT, "nature", f"cover_{key}.glb"))
    json.dump(rep, open(os.path.join(OUT, "nature", "_report_cover.json"), "w"), ensure_ascii=False, indent=1)
    # 미리보기: 26종을 나란히(50° 직교). barley_row 는 길어서 따로 둔다
    reset(); cols = 7
    for i, key in enumerate(COVER):
        o = join(f"cover_{key}", COVER[key]()); o.location = ((i % cols - 3) * 4.4, -(i // cols) * 3.6 + 5.4, 0)
    setup_render(34, (0, 3, 0.3), size=(1500, 900), ground_size=60)
    render(os.path.join(OUT, "previews", "cover_kit_50deg.png"))
    return rep

if __name__ == "__main__":
    rep = run()
    print(len(rep), "종, 최대 삼각형", max(r["tris"] for r in rep), "최소 z", min(r["min_z"] for r in rep))
    print([(r["name"], r["tris"]) for r in rep])
