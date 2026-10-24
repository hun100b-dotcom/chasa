"""지형 타일 18종. 한 칸 = 8m × 8m(코드의 땅 한 칸 128m 안에 16×16으로 깔린다). 실행: python3 terrain_tiles.py
규약: 원점=타일 바닥 한가운데, 흙 두께 0.3m(윗면 z=0.3), 정면 -Y. 길·논두렁은 모서리 가운데에서 이어진다(폭 3.2m / 1.0m).
회전은 90도 단위로만 쓴다. 바위·풀은 타일 위에 얹는 소품(바닥 없음)이다."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from lib3d import _obj
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
T = 8.0; TH = 0.3

def slab(material="ground"): return box("slab", (T, T, TH), (0, 0, TH / 2), material)
def strip(x0, x1, y0, y1, w_mat="road", z=TH, t=0.02): return box("strip", (x1 - x0, y1 - y0, t), ((x0 + x1) / 2, (y0 + y1) / 2, z + t / 2), w_mat)

def heightfield(name, hf, n=4, rise=2.0):
    """높이 함수 hf(u,v)->0..1 (u=x방향, v=y방향, 0..1)로 윗면을 만든다. 윗면은 풀색, 옆 치마는 흙색."""
    bm = bmesh.new(); V = {}
    for i in range(n + 1):
        for j in range(n + 1):
            u, v = i / n, j / n
            V[i, j] = bm.verts.new((-T / 2 + T * u, -T / 2 + T * v, TH + rise * hf(u, v)))
    for i in range(n):
        for j in range(n):
            bm.faces.new((V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]))
    top = _obj(name + "_top", bm, "slope_top")
    bm2 = bmesh.new()
    def edge(pts):
        for a, b in zip(pts, pts[1:]):
            za, zb = TH + rise * hf(*a[2]), TH + rise * hf(*b[2])
            v = [bm2.verts.new((a[0], a[1], 0)), bm2.verts.new((b[0], b[1], 0)), bm2.verts.new((b[0], b[1], zb)), bm2.verts.new((a[0], a[1], za))]
            bm2.faces.new(v)
    P = lambda u, v: (-T / 2 + T * u, -T / 2 + T * v, (u, v))
    edge([P(i / n, 0) for i in range(n + 1)]); edge([P(1, j / n) for j in range(n + 1)])
    edge([P(1 - i / n, 1) for i in range(n + 1)]); edge([P(0, 1 - j / n) for j in range(n + 1)])
    bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
    side = _obj(name + "_side", bm2, "slope_side")
    return [top, side, box("under", (T, T, 0.02), (0, 0, 0.01), "mud")]

def rocks(n, spread, sizes, seed, ground_z=0.0):
    r = random.Random(seed); p = []
    for i in range(n):
        a = r.random() * math.tau; d = r.random() * spread
        s = sizes[0] + r.random() * (sizes[1] - sizes[0])
        sz = 0.8 + r.random() * 0.3
        p.append(sphere(f"rock{i}", s, (math.cos(a) * d, math.sin(a) * d, s * sz + ground_z), "stone" if i % 3 else "stone_dark", 5, 3, (1.0 + r.random() * 0.3, 1.0, sz), rot=(0, 0, r.random() * 3)))
    return p

def tuft(x, y, h, material, r, n=5):
    rr = random.Random(int(x * 100 + y * 10 + 3)); p = []
    for i in range(n):
        a = i / n * math.tau + rr.random()
        p.append(cyl("blade", 0.06, 0.0, h * (0.8 + rr.random() * 0.4), (x + math.cos(a) * r, y + math.sin(a) * r, 0.07), material, 4, rot=(math.cos(a) * 0.25, math.sin(a) * 0.25, 0)))
    return p

def tiles():
    t = {}
    t["tile_grass"] = ("풀바닥", [slab()], "기본 바닥")
    w = 1.6
    t["tile_road_straight"] = ("흙길 직진", [slab(), strip(-T / 2, T / 2, -w, w)], "동서로 이어짐, 폭 3.2m")
    t["tile_road_corner"] = ("흙길 모서리", [slab(), strip(-w, T / 2, -w, w), strip(-w, w, -T / 2, w)], "동쪽과 남쪽으로 이어짐")
    t["tile_road_t"] = ("흙길 삼거리", [slab(), strip(-T / 2, T / 2, -w, w), strip(-w, w, -T / 2, -w)], "동·서·남쪽으로 이어짐")
    t["tile_road_end"] = ("흙길 끝(마당)", [slab(), strip(-w, T / 2, -w, w), cyl("round", 2.4, 2.4, 0.02, (-0.4, 0, TH), "road", 10)], "동쪽에서 들어와 마당으로 끝남")
    # 논: 둘레 논두렁 + 안쪽 물 논
    rim = [box("rimN", (T, 0.8, 0.4), (0, T / 2 - 0.4, TH + 0.1), "leaf_dark"), box("rimS", (T, 0.8, 0.4), (0, -T / 2 + 0.4, TH + 0.1), "leaf_dark"),
           box("rimE", (0.8, T - 1.6, 0.4), (T / 2 - 0.4, 0, TH + 0.1), "leaf_dark"), box("rimW", (0.8, T - 1.6, 0.4), (-T / 2 + 0.4, 0, TH + 0.1), "leaf_dark")]
    paddy = [slab("mud")] + rim + [box("water", (T - 1.6, T - 1.6, 0.04), (0, 0, TH + 0.04), "water")] + [box(f"rice{i}", (0.06, 0.06, 0.25), (-2.6 + (i % 6) * 1.04, -2.6 + (i // 6) * 1.04, TH + 0.2), "leaf") for i in range(36)]
    t["tile_paddy"] = ("논(둘레 논두렁)", paddy, "물 찬 논 한 칸")
    t["tile_bank_straight"] = ("논두렁 직진", [slab(), box("bank", (T, 1.0, 0.45), (0, 0, TH + 0.225), "mud"), box("top", (T, 0.6, 0.04), (0, 0, TH + 0.47), "leaf")], "동서로 이어지는 폭 1m 둑")
    t["tile_bank_corner"] = ("논두렁 모서리", [slab(), box("bankE", (T / 2 + 0.5, 1.0, 0.45), (T / 4 - 0.25, 0, TH + 0.225), "mud"), box("bankS", (1.0, T / 2 + 0.5, 0.45), (0, -T / 4 + 0.25, TH + 0.225), "mud")], "동쪽과 남쪽으로 이어짐")
    # 비탈: 북쪽(+Y)으로 올라간다. 윗면 높이 0.3 → 2.3m
    ang = math.atan2(2.0, T)
    cont = [box(f"contour{i}", (T, 0.1, 0.03), (0, -T / 2 + T * f, TH + 2.0 * f + 0.02), "slope_line", rot=(-ang, 0, 0)) for i, f in enumerate((0.25, 0.5, 0.75))]
    t["tile_slope_straight"] = ("비탈 직진", heightfield("slope", lambda u, v: v) + cont, "남쪽 낮은 쪽 → 북쪽 높은 쪽, 높이차 2m, 등고선 3줄")
    t["tile_slope_corner_out"] = ("비탈 볼록 모서리", heightfield("slope", lambda u, v: min(u, v) ** 1.0), "언덕 모서리(바깥으로 볼록)")
    t["tile_slope_corner_in"] = ("비탈 오목 모서리", heightfield("slope", lambda u, v: max(u, v)), "움푹 파인 모서리")
    t["tile_cliff_wall"] = ("벼랑 벽", [slab("cliff_dark")] + [box(f"blk{i}", (1.6 + (i % 2) * 0.3, 1.4, 1.2), (-3.5 + i * 1.4, 3.2 + (i % 2) * 0.1, TH + 0.6), "cliff_light" if i % 2 else "cliff_dark") for i in range(6)] + [box("top", (T, 1.6, 0.04), (0, 3.3, TH + 1.22), "slope_top"), box("shadow", (T, 0.1, 1.2), (0, 2.45, TH + 0.6), "ink")], "북쪽 가장자리를 따라 선 바위벽 2m")
    # 소품(타일 위에 얹음)
    t["rock_small"] = ("바위 작은 것", rocks(2, 0.3, (0.3, 0.5), 1), "높이 0.5m")
    t["rock_medium"] = ("바위 중간", rocks(1, 0, (1.0, 1.2), 2), "높이 1.3m")
    t["rock_cluster"] = ("바위 무리", rocks(7, 2.2, (0.5, 1.3), 3), "5m 폭 무리")
    t["bush_low"] = ("풀숲(낮음)", sum([tuft(x, y, 0.55, "leaf", 0.12) for x, y in [(-0.8, 0.2), (0, -0.5), (0.7, 0.4), (0.2, 0.9), (-0.4, -1.0), (1.0, -0.6)]], []), "무릎 높이 풀")
    t["bush_tall"] = ("풀숲(키 큼)", [sphere(f"b{i}", r, (x, y, r * 1.15), "leaf" if i % 2 else "leaf_dark", 6, 4, (1, 1, 1.15)) for i, (x, y, r) in enumerate([(0, 0, 0.9), (0.9, 0.3, 0.7), (-0.8, 0.2, 0.75), (0.2, -0.8, 0.6)])], "허리 높이 수풀")
    t["bush_flower"] = ("꽃 핀 풀숲", sum([tuft(x, y, 0.5, "leaf", 0.12) for x, y in [(-0.6, 0.1), (0.3, -0.4), (0.7, 0.5), (-0.2, 0.8)]], []) + [box(f"f{i}", (0.1, 0.1, 0.1), (-0.8 + i * 0.4, 0.2 * ((i * 7) % 5 - 2), 0.55 + (i % 2) * 0.1), c) for i, c in enumerate(["red", "gold", "hanji", "gold", "red"])], "붉은·노란 들꽃 섞임")
    return t

def build_piece(key):
    before = set(bpy.context.scene.objects)
    label, parts, note = tiles()[key]
    for o in list(set(bpy.context.scene.objects) - before - set(parts)): bpy.data.objects.remove(o)
    return join(f"terrain_{key}", parts), label, note

def export_all():
    rep = []
    for key in tiles():
        reset(); o, label, note = build_piece(key); lo, hi = bounds(o)
        rep.append({"name": f"terrain_{key}", "label": label, "note": note, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
        export(o, os.path.join(OUT, "terrain", f"terrain_{key}.glb"))
    json.dump({"tile_m": T, "thickness_m": TH, "cell_128m_holds": "16 x 16 tiles", "front": "-Y(내보내면 +Z)", "tiles": rep}, open(os.path.join(OUT, "terrain", "_tiles_manifest.json"), "w"), ensure_ascii=False, indent=1)
    return rep

def place(key, x, y, z=0, rot=0):
    o, _, _ = build_piece(key); o.location = (x, y, z); o.rotation_euler = (0, 0, math.radians(rot)); return o

def demo():
    """5×5(40m) 시험판: 길이 가운데를 지나고, 오른쪽 위는 논, 왼쪽 위는 비탈 언덕, 바위·풀숲을 얹는다."""
    reset()
    grid = {}
    for i in range(5):
        for j in range(5): grid[i, j] = ("tile_grass", 0)
    for i in range(5): grid[i, 2] = ("tile_road_straight", 0)
    grid[2, 2] = ("tile_road_t", 0); grid[2, 1] = ("tile_road_straight", 90); grid[2, 0] = ("tile_road_end", 90)
    # 논(오른쪽 위 2×2) + 논두렁
    for i in (3, 4):
        for j in (3, 4): grid[i, j] = ("tile_paddy", 0)
    grid[3, 1] = ("tile_bank_straight", 0); grid[4, 1] = ("tile_bank_straight", 0)
    # 비탈: 왼쪽 위 언덕 (v=북으로 올라가는 비탈 한 줄, 위는 평평한 풀 +2m 대신 비탈만)
    grid[0, 3] = ("tile_slope_straight", 0); grid[1, 3] = ("tile_slope_straight", 0); grid[0, 4] = ("tile_cliff_wall", 0); grid[1, 4] = ("tile_cliff_wall", 0)
    for (i, j), (k, r) in grid.items():
        place(k, (i - 2) * T, (j - 2) * T, 0, r)
    for k, x, y in [("rock_cluster", -14, -10), ("rock_medium", 12, -6), ("rock_small", -6, -3), ("bush_tall", 8, -12), ("bush_low", -10, 4), ("bush_low", 18, 6), ("bush_tall", 6, 8)]:
        place(k, x, y, TH)
    setup_render(54, (0, 0, 0), size=(1280, 900), ground_size=100)
    render(os.path.join(OUT, "previews", "terrain_tiles_demo_50deg.png"))

if __name__ == "__main__":
    rep = export_all()
    print(len(rep), "종, 최대 삼각형", max(r["tris"] for r in rep), "최소 z", min(r["min_z"] for r in rep))
    demo()
