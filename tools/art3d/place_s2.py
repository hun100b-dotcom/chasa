"""시즌 2 저승 ⑦~⑩ 배치표 만들기. 실행: python3 place_s2.py → assets3d/layouts/s2_r7_layout.json ~ s2_r10_layout.json, s2_walk_report.json
좌표: 저승 좌표계 하나(x=동, y=북). z는 terrain_s2_r*/heightmap.png에서 읽어 모델 바닥을 땅에 붙인다. rot 0 = 남쪽(-Y)이 앞, 위에서 볼 때 반시계(Unity yaw = -rot, 1~3막과 같음).
규칙: 길 가운데 3 m·보스 마당(반경 + 2 m)·장소 중심은 비운다(일부러 둔 것은 by_design). 막히면 6 m 안 열린 땅으로 옮기고 walk_snap에 원래 좌표를 남긴다.
기획 지시: 마당은 평평·가림 없음 / ⑧ 마당 안 서가 없음, 남쪽 서가는 반 높이(s2_archive_shelf_low) / ⑧ 큰 벼루 둘레 2 m 금지(막힘 반지름 3.2) / ⑨ 인장 굴은 지붕 없는 바위 틈 / ⑨ 빈 고을은 솔고개 마을 배치 복사(문패·위패 없음)."""
import os, sys, json, math, random
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import terrain_s2 as T
ROOT = T.ROOT; LAY = os.path.join(ROOT, "assets3d", "layouts"); RNG = random.Random(4004)
HG = {}
def load_h(rid):
    T.setup(rid); a = np.array(Image.open(os.path.join(T.OUT, "heightmap.png")).convert("RGBA")).astype(np.int64)
    HG[rid] = (T.X0, T.Y0, T.W, T.H, ((a[..., 0] << 8) | a[..., 1]) / 65535.0 * (T.HMAX - T.HMIN) + T.HMIN)
def ground(rid, x, y):
    X0, Y0, W, H, G = HG[rid]; fx = min(max(x - X0, 0), W - 1e-6); fy = min(max(y - Y0, 0), H - 1e-6); i, j = int(fx), int(fy); tx, ty = fx - i, fy - j
    return float((G[j, i] * (1 - tx) + G[j, i + 1] * tx) * (1 - ty) + (G[j + 1, i] * (1 - tx) + G[j + 1, i + 1] * tx) * ty)
RAD = {"s2_ferry_post": 0.4, "s2_ferry_hut": 2.4, "s2_ferry_inn_site": 2.6, "s2_ink_rock": 1.6, "s2_nabulbul": 0.7, "s2_clerk_barrack": 3.4, "s2_clerk_kitchen": 2.2, "s2_inkroom_house": 3.0, "s2_big_inkstone": 3.2,
       "s2_archive_shelf": 2.0, "s2_archive_shelf_low": 2.0, "s2_archive_desk": 1.0, "s2_ninth_slot": 2.2, "s2_number_board": 0.6, "s2_yard_desk": 1.0, "s2_myeongbu_wall": 2.1, "s2_myeongbu_gate": 3.5,
       "s2_ninth_gate": 4.0, "s2_seal_market_stall": 1.6, "s2_seal_cave_rock_a": 2.4, "s2_seal_cave_rock_low": 1.6, "s2_seal_stone": 0.6, "s2_first_hut": 2.0, "s2_old_well": 1.3, "s2_chain_grave": 1.3,
       "s2_chain_stake": 0.4, "s2_big_dam_wall": 3.2, "s2_first_lantern": 0.3, "s2_dam_wall": 2.0, "s2_reed_dust": 0.0, "s2_queue_stake": 0.0, "s2_ferry_pier": 0.0, "s2_ferry_boat": 0.0, "s2_dam_stone_step": 0.0, "s2_old_charcoal_mark": 0.0,
       "nature_dead_a": 0.6, "nature_dead_b": 0.6, "nature_dead_c": 0.6, "nature_silvergrass_a": 0.0, "nature_silvergrass_b": 0.0, "nature_reed_a": 0.0, "nature_reed_b": 0.0, "cover_stones_a": 0.0, "cover_moss_patch": 0.0}
def folder(n): return "nature" if n.startswith(("nature_", "cover_")) else "s2"

class Region:
    def __init__(self, rid):
        self.rid = rid; load_h(rid); T.setup(rid); self.R = T.R; self.X0, self.Y0, self.W, self.H = T.X0, T.Y0, T.W, T.H
        self.props = []; self.placed = []; self.dropped = []; self.roads = []
        for r in self.R["roads"]:
            P = r["points"]
            for a, b in zip(P[:-1], P[1:]):
                n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]))); self.roads += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
        self.keep = [(a["x"], a["y"], a["radius_m"] + 2.0) for a in self.R["arenas"]]
    def inside(self, x, y, m=2.0): return self.X0 + m <= x <= self.X0 + self.W - m and self.Y0 + m <= y <= self.Y0 + self.H - m
    def ok(self, name, x, y, force=False):
        r = RAD.get(name, 1.0)
        if not self.inside(x, y): return False
        if force: return True
        if any(math.hypot(x - kx, y - ky) < kr + r for kx, ky, kr in self.keep): return False
        if r > 0 and any(math.hypot(x - a, y - b) < 3.0 + r for a, b in self.roads[::2]): return False
        if r > 0 and any(math.hypot(x - px, y - py) < pr + r for px, py, pr in self.placed if pr > 0): return False
        return ground(self.rid, x, y) > 0.05 or name in ("s2_ferry_boat", "s2_ferry_pier", "s2_ink_rock")
    def snap(self, name, x, y):
        for d in (2, 4, 6):
            for a in range(0, 360, 30):
                nx, ny = x + d * math.cos(math.radians(a)), y + d * math.sin(math.radians(a))
                if self.ok(name, nx, ny): return nx, ny
        return None
    def add(self, name, x, y, rot=0, note="", force=False, z=None, snap=True):
        if not self.inside(x, y): return None
        sn = (x, y) if (force or self.ok(name, x, y)) else (self.snap(name, x, y) if snap else None)
        if sn is None: self.dropped.append((name, x, y)); return None
        p = {"prop": name, "file": f"assets3d/{folder(name)}/{name}.glb", "x": round(sn[0], 2), "y": round(sn[1], 2), "rot": int(rot) % 360, "z": round(ground(self.rid, *sn) if z is None else z, 2)}
        if note: p["note"] = note
        if sn != (x, y): p["walk_snap"] = {"from": [x, y], "to": [round(sn[0], 2), round(sn[1], 2)]}
        if force: p["by_design"] = True
        self.props.append(p); self.placed.append((sn[0], sn[1], RAD.get(name, 1.0))); return p
    def scatter(self, name, n, rect, note="", tries=40, gap=0.0, rot=None):
        k = 0; t = 0
        while k < n and t < n * tries:
            t += 1; x, y = RNG.uniform(rect[0], rect[2]), RNG.uniform(rect[1], rect[3])
            if self.add(name, x, y, RNG.uniform(0, 360) if rot is None else rot, note, snap=False): k += 1
        return k
    def save(self):
        rep = {"props": len(self.props), "dropped": len(self.dropped), "snapped": sum(1 for p in self.props if "walk_snap" in p), "dropped_list": self.dropped[:20]}
        json.dump({"units": "m", "axes": "x=동, y=북(저승 좌표계)", "region": self.rid, "note": "place_s2.py가 만든다. 직접 고치지 말고 스크립트를 고친다", "props": self.props}, open(os.path.join(LAY, f"s2_r{self.rid}_layout.json"), "w"), ensure_ascii=False, indent=1)
        return rep
def ring(cx, cy, r, n, a0=0): return [(cx + r * math.cos(a0 + i * 2 * math.pi / n), cy + r * math.sin(a0 + i * 2 * math.pi / n), math.degrees(a0 + i * 2 * math.pi / n)) for i in range(n)]
SCAT = ("nature_dead_a", "nature_dead_b", "nature_dead_c", "nature_silvergrass_a", "nature_silvergrass_b", "cover_stones_a")

def r7():
    g = Region(7)
    # 나루: 말뚝·널판·배 (기획: 말뚝 앞 B-13 마당 동쪽 끝이 물가)
    g.add("s2_ferry_post", 420, 256, 0, "나루 말뚝(B13-D2 지켜보기 자리 (420,256))", force=True)
    for k in range(2): g.add("s2_ferry_pier", 422.0 + k * 4.0, 250, 0, "나루 널판(배가 닿는 곳)", force=True, z=0.0)
    g.add("s2_ferry_boat", 446, 236, 80, "나룻배 대역 자리(N-703 풍경 배는 코드, 이것은 말뚝 곁에 묶인 빈 배)", force=True, z=-0.05)
    # 줄 표지 말뚝(줄 따라 6 m 간격, 마당 서쪽 밖에서 끝)
    q = M7q = T.M7["queue_line"]["points"]
    for a, b in zip(q[:-1], q[1:]):
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]) // 6)
        for k in range(1, n + 1):
            x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
            g.add("s2_queue_stake", x, y, 0, "줄 표지 말뚝", force=(x < 388), snap=False)
    # 빈 나루 마을
    for (hx, hy, r_) in [(240, 180, 0), (262, 196, 20), (250, 300, 0), (280, 320, 10), (305, 190, 180), (335, 180, 200), (345, 300, 0), (370, 322, 20), (320, 318, 0), (240, 270, 90), (390, 190, 160), (230, 230, 80), (360, 270, 0)]:
        g.add("s2_ferry_hut", hx, hy, r_, "빈 나루 마을 집")
    g.add("s2_ferry_inn_site", 280, 296, 0, "빈 주막 터(나룻불 쉼터 NB7-2)", force=True); g.add("s2_nabulbul", 280, 290, 0, "나룻불 쉼터 NB7-2", force=True)
    g.add("s2_nabulbul", 70, 250, 0, "나룻불 쉼터 NB7-1 저승 어귀", force=True)
    g.scatter("s2_reed_dust", 70, (40, 300, 220, 480), "깨진 가루 걸린 갈대(낮 가루 줍기 자리)", gap=1.0)
    for nm in ("nature_reed_a", "nature_reed_b", "nature_silvergrass_a", "nature_silvergrass_b"): g.scatter(nm, 110, (40, 300, 220, 480), "갈대늪")
    for k in range(12): g.add("s2_ink_rock", 460 + RNG.uniform(0, 120), 390 + RNG.uniform(0, 100), RNG.uniform(0, 360), "먹물 여울 바위", snap=False)
    g.add("s2_ink_rock", 520, 440, 0, "먹물 여울 바위(기획 장소)", force=True)
    for x in range(384, 560, 4):                                         # 물안개 둑 위 가장자리(북쪽·남쪽 턱)
        for y in (130, 42): g.add("s2_dam_wall", x + 2, y, 0, "물안개 둑 턱", force=True, z=1.8 - 0.4) if not (440 < x < 500 and y == 130) else None
    g.add("s2_ink_rock", 470, -8 if False else 30, 0, "둑 끝 바위", snap=False)
    for nm in SCAT: g.scatter(nm, 150, (g.X0 + 10, g.Y0 + 10, g.X0 + g.W - 10, g.Y0 + g.H - 10), "저승 풀·마른 나무")
    return g
def r8():
    g = Region(8)
    g.add("s2_nabulbul", 640, 600, 0, "나룻불 쉼터 NB8-1 숙사 어귀", force=True)
    for (x, y, r_) in [(700, 650, 0), (700, 662, 0), (700, 674, 0), (680, 700, 90), (720, 726, 0)]: g.add("s2_clerk_barrack", x, y, r_, "서리 숙사 행랑")
    g.add("s2_clerk_kitchen", 728, 702, 0, "숙사 부엌(N-801·N-804)", force=True)
    # 먹방: 가운데 큰 벼루(B-16 자리), 건물은 마당(반경 14+2) 밖 모서리
    g.add("s2_big_inkstone", 880, 700, 0, "먹방 가운데 큰 벼루(둘레 2 m 못 들어감, 막힘 반지름 3.2)", force=True)
    for (x, y, r_) in [(836, 654, 0), (924, 654, 0), (836, 748, 180), (924, 748, 180), (905, 636, 0)]: g.add("s2_inkroom_house", x, y, r_, "먹방 건물")
    # 문서 창고: 남쪽(y<896) 반 높이 서가, 북쪽(y≥896) 높은 서가. 마당 밖(반경+2) 규칙은 ok()가 지킨다. 복도는 x 1056~1064
    for y in range(828, 896, 8):
        for x in list(range(988, 1052, 4)) + list(range(1068, 1136, 4)): g.add("s2_archive_shelf_low", x + 2, y, 0, "서가(남쪽 반 높이, 쿼터뷰 가림 방지)", snap=False)
    for y in range(904, 980, 8):
        for x in list(range(988, 1052, 4)) + list(range(1068, 1136, 4)): g.add("s2_archive_shelf", x + 2, y, 0, "서가(마당 밖)", snap=False)
    g.add("s2_ninth_slot", 1010, 900, 0, "아홉째 칸(⑨로 가는 문, 먼지 없는 빈 칸)", force=True, z=0.3)
    g.add("s2_archive_desk", 1082, 930, 0, "그의 책상(B15-D3 만져 보기)", force=True)
    g.add("s2_archive_shelf", 1120, 968, 0, "창고 맨 안쪽 서가(B15-D2 지켜보기)", force=True)
    # 숫자 마당: 번호 판 격자
    for x in range(748, 896, 14):
        for y in range(850, 960, 14): g.add("s2_number_board", x, y, RNG.choice([0, 0, 180]), "숫자 마당 번호 판")
    g.add("s2_yard_desk", 800, 880, 0, "마당 책상(N-803)", force=True)
    # 명부전 담장 y=1040 (문 (900,1040) 폭 6 m는 비움) + 닫힌 본당 문
    for x in range(562, 1200, 4):
        if abs(x - 900) > 5: g.add("s2_myeongbu_wall", x, 1040, 0, "명부전 담장", force=True)
    g.add("s2_myeongbu_gate", 900, 1040, 0, "명부전 본당 문(끝까지 닫힘)", force=True)
    for nm in SCAT: g.scatter(nm, 60, (g.X0 + 10, g.Y0 + 10, g.X0 + g.W - 10, 1030), "저승 풀·마른 나무")
    return g
def r9():
    g = Region(9)
    # 빈 고을 = 1막 솔고개 마을 배치 복사(문패·위패는 모델에 없음 → 그대로 '비어 있음'). 마을 원점 (380,880)
    V = json.load(open(os.path.join(LAY, "solgogae_village.json"), encoding="utf-8")); OX, OY = 380, 880
    for b in V["buildings"]:
        for q in b["pieces"]:
            nm = q["piece"]; fp = q["file"]; p = {"prop": nm, "file": fp, "x": round(q["x"] + OX, 2), "y": round(q["y"] + OY, 2), "rot": q.get("rot", 0) % 360, "z": q.get("z", 0.0), "note": f"빈 고을(솔고개 {b['id']} 복사)"}
            g.props.append(p)
    for q in V["props"]:
        p = {"prop": q["prop"], "file": q["file"], "x": round(q["x"] + OX, 2), "y": round(q["y"] + OY, 2), "rot": q.get("rot", 0) % 360, "z": q.get("z", 0.0), "note": "빈 고을(솔고개 소품 복사)"}
        g.props.append(p); g.placed.append((p["x"], p["y"], RAD.get(q["prop"], 1.0)))
    g.add("s2_nabulbul", 388, 868, 0, "빈 고을 서낭나무 자리 NB9-1(빈 종이)", force=True)
    g.add("s2_ninth_gate", 200, 1078, 0, "아홉째 문(위 인 자리 (200,1078)는 비어 있음)", force=True)
    for (x, y) in [(150, 830), (166, 830), (182, 830), (218, 830), (234, 830), (250, 830), (150, 890), (166, 890), (234, 890), (250, 890), (200, 800)]: g.add("s2_seal_market_stall", x, y, 0, "도장 없는 장터 판")
    for (x, y) in [(140, 900), (190, 870), (210, 850), (96, 960), (70, 1000), (110, 990), (205, 1056)]: g.add("s2_seal_stone", x, y, RNG.uniform(0, 360), "도장 돌(인이 없음)", force=(x, y) == (205, 1056))
    # 인장 굴: 바위 담 고리(동쪽 입구 틈, 남쪽은 낮은 바위). 바위는 마당 반경 12 + 2 밖 r 28~36
    cx, cy = 30.0, 985.0
    for (x, y, a) in ring(cx, cy, 30, 28):
        ad = ((a + 180) % 360) - 180
        if abs(ad) < 26: continue
        low = 245 < (a % 360) < 295
        g.add("s2_seal_cave_rock_low" if low else "s2_seal_cave_rock_a", x, y, a + 90, "인장 굴 바위 담(지붕 없음)", force=True)
    for nm in SCAT: g.scatter(nm, 70, (g.X0 + 10, 620, g.X0 + g.W - 10, g.Y0 + g.H - 10), "저승 풀·마른 나무")
    return g
def r10():
    g = Region(10)
    g.add("s2_nabulbul", 360, -180, 0, "처음 마을 우물 나룻불 NB10-1", force=True)
    for (x, y, r_) in [(310, -250, 0), (330, -240, 20), (350, -250, 0), (372, -238, 330), (394, -250, 0), (312, -222, 90), (336, -214, 0), (390, -214, 180), (316, -190, 0), (344, -160, 0), (376, -160, 20), (405, -176, 0)]:
        g.add("s2_first_hut", x, y, r_, "처음 마을 집")
    g.add("s2_old_well", 398, -300, 0, "처음 마을 우물(B19-D2 우물가, 마당 원 바깥 북동)", force=True)
    for (x, y, a) in ring(360, -200, 10, 6): g.add("s2_old_charcoal_mark", x, y, a, "마당 그을림")
    for k in range(10): g.add("s2_first_lantern", 300 + RNG.uniform(0, 120), -260 + RNG.uniform(0, 120), 0, "처음 마을 새벽 등", snap=False)
    for (x, y) in [(540 + (i % 7) * 18, -290 + (i // 7) * 24) for i in range(28)]: g.add("s2_chain_grave", x + RNG.uniform(-3, 3), y + RNG.uniform(-3, 3), RNG.uniform(0, 360), "사슬 무덤", snap=False)
    g.add("s2_chain_stake", 540, -200, 0, "사슬 무덤 맨 앞 말뚝(B19-D3)", force=True)
    # 큰 물막이 바닥: 둘러싼 돌벽 고리(북쪽 60°는 내려오는 길이라 비움)
    for (x, y, a) in ring(560, -520, 104, 36):
        if 60 < a % 360 < 120: continue
        g.add("s2_big_dam_wall", x, y, a + 90, "큰 물막이 벽(바닥을 둘러쌈)", force=True)
    for k in range(6): g.add("s2_dam_stone_step", 560, -420 - k * 2.0, 0, "물막이 바닥으로 내려가는 돌계단", force=True)
    g.add("s2_ink_rock", 470, -8, 0, "먹지기 붓 표시 바위(⑦ 안개 벽이 걷힐 때 표시, 기획 (470,-8))", force=True)
    for nm in SCAT: g.scatter(nm, 110, (g.X0 + 10, g.Y0 + 10, g.X0 + g.W - 10, g.Y0 + g.H - 10), "저승 풀·마른 나무")
    return g
if __name__ == "__main__":
    want = [int(a) for a in sys.argv[1:]] or [7, 8, 9, 10]; rep = {}
    for rid in want:
        g = {7: r7, 8: r8, 9: r9, 10: r10}[rid](); rep[f"r{rid}"] = g.save(); print(rid, rep[f"r{rid}"])
    json.dump(rep, open(os.path.join(LAY, "s2_walk_report.json"), "w"), ensure_ascii=False, indent=1)
