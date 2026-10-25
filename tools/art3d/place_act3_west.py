"""3막 ⑥ 도성 아랫마을 소품 배치표. 실행: python3 place_act3_west.py → assets3d/layouts/act3_west_layout.json, act3_west_report.json
방식은 place_act3_east.py 와 같다. 성벽 x=-560 에 city_wall 을 잇고 닫힌 성문(-558,215), 그 뒤로 기기와 지붕 띠(city_skyline), 저잣거리·움막촌·성문 밖 주막, 큰 다리(bridge_deck·bridge_pier, 축 y=400)를 놓는다.
다리: 상판 윗면은 둔치보다 3.9m 높고 terrain_act3_west.py 가 양끝 둑길을 3.9m로 올려 두었다. 기획은 다리를 (-380,410)에 두었으나 B-11 마당(-382,392)이 상판 밑에 들도록 축을 y=400으로 10m 내렸다(상판 폭 6m: 395~405)."""
import os, sys, json, math, random
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MAP = "/mnt/project-files/planning/openworld/act3/act3_map.json"
TER = os.path.join(ROOT, "assets3d", "terrain_act3_west"); LAY = os.path.join(ROOT, "assets3d", "layouts")
X0, Y0, W, H = -640, 0, 640, 640; HMIN, HMAX = -1.5, 9.0
RNG = random.Random(3066); M = json.load(open(MAP))
_hm = np.array(Image.open(os.path.join(TER, "heightmap.png")).convert("RGBA")).astype(np.int64)
HGT = ((_hm[..., 0] << 8) | _hm[..., 1]) / 65535.0 * (HMAX - HMIN) + HMIN
def ground(x, y):
    fx = min(max(x - X0, 0), W - 1e-6); fy = min(max(y - Y0, 0), H - 1e-6); i, j = int(fx), int(fy); tx, ty = fx - i, fy - j
    a = HGT[j, i] * (1 - tx) + HGT[j, i + 1] * tx; b = HGT[j + 1, i] * (1 - tx) + HGT[j + 1, i + 1] * tx
    return float(a * (1 - ty) + b * ty)
RAD = {"city_wall": 0.0, "city_gate": 0.0, "city_skyline": 0.0, "market_stall": 1.8, "market_ricecake_stall": 1.4, "market_jige": 0.5, "market_lantern_string": 0.0, "market_tile_house": 3.6, "shack_a": 1.9, "shack_b": 2.3, "shack_well": 0.9,
       "city_gatekeeper_hut": 2.4, "city_gate_inn": 3.3, "city_pit_grave": 1.6, "snow_patch": 0.0, "river_hut_mat": 1.4, "river_bank": 2.0, "bridge_deck": 0.0, "bridge_pier": 0.0}
ROADS = []
for r in M["roads"]:
    P = r["points"]
    for a, b in zip(P[:-1], P[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
        for k in range(n):
            x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
            if X0 <= x <= X0 + W and Y0 <= y <= Y0 + H: ROADS.append((x, y, r["id"]))
KEEP = [(n, p["x"], p["y"], 1.6) for n, p in M["places"].items() if X0 <= p["x"] < 0] + [(s["name"], s["x"], s["y"], 3.0) for s in M["shrines"] if s["x"] < 0] + [(b["name"], b["x"], b["y"], b["radius_m"] * 0.55) for b in M["boss_arenas"] if b["x"] < 0]
PLACED = []; DROPPED = []
def clear_ok(name, x, y):
    r = RAD.get(name, 1.0)
    if r <= 0: return True
    if any(math.hypot(rx - x, ry - y) < r + 1.5 for rx, ry, _ in ROADS): return False
    if any(math.hypot(kx - x, ky - y) < r + kr for _, kx, ky, kr in KEEP): return False
    if abs(x + 380) < 20 + r: return False        # 큰내와 다리 둑길은 비운다
    return not any(q["r"] > 0 and math.hypot(q["x"] - x, q["y"] - y) < (r + q["r"]) * 0.8 for q in PLACED)
def snap(name, x, y, rad=6.0):
    for k in range(1, int(rad / 0.5) + 1):
        for a in range(0, 360, 20):
            nx, ny = x + k * 0.5 * math.cos(math.radians(a)), y + k * 0.5 * math.sin(math.radians(a))
            if clear_ok(name, nx, ny): return round(nx, 2), round(ny, 2)
    return None
def add(name, x, y, rot=0, note="", force=False, z=None):
    if not (X0 + 2 <= x <= X0 + W - 2 and Y0 + 2 <= y <= Y0 + H - 2): return None
    sn = (x, y) if (force or clear_ok(name, x, y)) else snap(name, x, y)
    if sn is None: DROPPED.append((name, x, y)); return None
    p = {"prop": name, "file": f"assets3d/act3/{name}.glb", "x": round(sn[0], 2), "y": round(sn[1], 2), "rot": int(rot) % 360, "z": round(ground(*sn) if z is None else z, 2), "r": RAD.get(name, 1.0)}
    if note: p["note"] = note
    if sn != (x, y): p["walk_snap"] = {"from": [x, y], "to": [round(sn[0], 2), round(sn[1], 2)]}
    if force: p["by_design"] = True
    PLACED.append(p); return p
def build():
    # ── 성벽 x=-560 (닫힌 성문 둘레 12m는 비운다), 벽 뒤 지붕 띠 ──
    for y in range(4, 640, 8):
        if abs(y - 215) < 10: continue
        add("city_wall", -560, y, 270, "도성 서쪽 성벽(높이 8m)" if y == 4 else "", force=True, z=1.0)
    add("city_gate", -560, 215, 270, "닫힌 성문+문루(N-602 문지기 자리)", force=True, z=1.0)
    for y in range(8, 640, 20): add("city_skyline", -568, y, 90, "성벽 너머 기와지붕 실루엣 띠(깊이 30m, 낮은 디테일)" if y == 8 else "", force=True, z=1.0)
    # ── 저잣거리 (-330,370)-(-150,520), 큰길 y≈440 ──
    for x in range(-322, -150, 15):
        add("market_stall", x, 450, 180, "저잣 좌판(북쪽 줄)"); add("market_stall", x + 5, 431, 0, "저잣 좌판(남쪽 줄)")
    add("market_ricecake_stall", -225, 460, 180, "떡장수 좌판(K-003 떡시루)", force=True); add("market_jige", -262, 428, 0, "짐꾼 지게 자리(S-104)", force=True)
    for x in range(-312, -150, 28): add("market_lantern_string", x, 441, 90, "저잣 등불 줄(길 건너)", force=True)
    for x in (-300, -266, -226, -190): add("market_tile_house", x, 482, 180, "저잣 기와집(북쪽)"); add("market_tile_house", x - 8, 403, 0, "저잣 기와집(남쪽)")
    # ── 큰 다리(축 y=400, x −400~−360 다섯 칸) 와 둔치 ──
    for k, x in enumerate((-396, -388, -380, -372, -364)):
        add("bridge_pier", x, 400, 0, "큰 다리 기둥·바닥" if k == 0 else "", force=True, z=0.3); add("bridge_deck", x, 400, 0, "큰 다리 상판·난간(재질 M_bridge_deck, B-11 반투명)" if k == 0 else "", force=True, z=0.3)
    add("river_hut_mat", -405, 362, 0, "쥐똥이 거적(B11-D2)", force=True); add("river_hut_mat", -392, 372, 20, "다리 밑 거적 앞", force=True)
    # ── 움막촌 (-560,380)-(-450,540) ──
    for x, y, t in [(-520, 420, "shack_a"), (-505, 450, "shack_b"), (-490, 480, "shack_a"), (-530, 500, "shack_b"), (-470, 510, "shack_a"), (-515, 395, "shack_b"), (-475, 420, "shack_a")]: add(t, x, y, RNG.choice((0, 90, 180)), "움막촌 판잣집")
    add("shack_a", -495, 470, 0, "움막촌 어미 판잣집(S-105 어미)", force=True); add("shack_well", -480, 440, 0, "움막촌 우물", force=True)
    # ── 성문 밖 (-560,140)-(-440,290): 눈밭 ──
    add("city_gatekeeper_hut", -546, 252, 270, "문지기 막(N-602)", force=True); add("city_gate_inn", -470, 265, 0, "성문 밖 주막(N-603, B12-D2)", force=True)
    add("city_pit_grave", -508, 160, 0, "팻말 없는 구덩이 무덤(B-12 마당)", force=True)
    for x in range(-548, -450, 6):
        for y in range(146, 286, 6):
            if math.hypot(x + 470, y - 265) > 14: add("snow_patch", x, y, RNG.uniform(0, 360))
build()
def main():
    bad = []
    for p in PLACED:
        if p.get("by_design") or p["r"] <= 0: continue
        for n, kx, ky, kr in KEEP:
            if math.hypot(kx - p["x"], ky - p["y"]) < p["r"] + kr - 0.01: bad.append((p["prop"], p["x"], p["y"], n))
    out = [{k: v for k, v in p.items() if k != "r"} for p in PLACED]
    json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "place_act3_west.py가 만든다. z=땅 높이(terrain_act3_west). 다리 축 y=400, 상판 z 둔치 0.3 기준", "props": out}, open(os.path.join(LAY, "act3_west_layout.json"), "w"), ensure_ascii=False, indent=1)
    rep = {"count": len(out), "dropped": DROPPED, "overlaps": bad, "moved": [p for p in out if "walk_snap" in p], "per_model": {n: sum(1 for p in out if p["prop"] == n) for n in sorted({p["prop"] for p in out})}}
    json.dump(rep, open(os.path.join(LAY, "act3_west_report.json"), "w"), ensure_ascii=False, indent=1)
    print("놓은 소품", len(out), "| 옮긴", len(rep["moved"]), "| 못 놓음", len(DROPPED), "| 겹침", len(bad)); print(rep["per_model"])
    for d in DROPPED[:10]: print("  못 놓음", d)
if __name__ == "__main__": main()
