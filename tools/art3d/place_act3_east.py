"""3막 ⑤ 갯마을 소품 배치표. 실행: python3 place_act3_east.py → assets3d/layouts/act3_east_layout.json, act3_east_report.json
방식은 place_act2.py 와 같다(길 3m·장소 점 비움, 막히면 6m 안 열린 땅으로 옮기고 walk_snap, z=땅 높이). 차이: 바다 위(선창·배)는 높이를 직접 준다, 물판(tide_water)은 바다가 있는 곳에만 자동으로 깐다.
높이 약속: 썰물 -0.5, 밀물 +0.6. 선창 널판은 1.5(밀물보다 높음), 배·물판 기준 z는 썰물 높이(-0.5)이고 코드가 올린다."""
import os, sys, json, math, random
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MAP = "/mnt/project-files/planning/openworld/act3/act3_map.json"
TER = os.path.join(ROOT, "assets3d", "terrain_act3_east"); LAY = os.path.join(ROOT, "assets3d", "layouts")
X0, Y0, W, H = 768, 0, 512, 1024; HMIN, HMAX = -3.0, 10.0; LOW = -0.5
RNG = random.Random(3033)
M = json.load(open(MAP))
_hm = np.array(Image.open(os.path.join(TER, "heightmap.png")).convert("RGBA")).astype(np.int64)
HGT = ((_hm[..., 0] << 8) | _hm[..., 1]) / 65535.0 * (HMAX - HMIN) + HMIN
def ground(x, y):
    fx = min(max(x - X0, 0), W - 1e-6); fy = min(max(y - Y0, 0), H - 1e-6); i, j = int(fx), int(fy); tx, ty = fx - i, fy - j
    a = HGT[j, i] * (1 - tx) + HGT[j, i + 1] * tx; b = HGT[j + 1, i] * (1 - tx) + HGT[j + 1, i + 1] * tx
    return float(a * (1 - ty) + b * ty)
RAD = {"harbor_pier": 0.0, "harbor_gauge_post": 0.3, "harbor_boat": 0.0, "harbor_net_frame": 1.0, "harbor_net_pile": 0.8, "harbor_jar": 0.8, "harbor_gaekju_house": 4.2, "harbor_inn": 3.4, "harbor_lamp_hut": 2.0,
       "salt_pan": 0.0, "salt_pile": 1.4, "salt_warehouse": 3.4, "salt_dike": 2.0, "cape_waiting_rock": 3.0, "cape_hutmyo": 0.9, "cape_new_grave": 1.0, "shoal_wreck": 0.0, "shoal_rock": 1.6, "shoal_plank": 0.0, "tide_water": 0.0}
def folder(n): return "act3"
ROADS = []
for r in M["roads"]:
    P = r["points"]
    for a, b in zip(P[:-1], P[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
        for k in range(n):
            x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
            if X0 <= x <= X0 + W and Y0 <= y <= Y0 + H: ROADS.append((x, y, r["id"]))
KEEP = [(n, p["x"], p["y"], 1.6) for n, p in M["places"].items() if X0 <= p["x"] <= X0 + W] + [(s["name"], s["x"], s["y"], 3.0) for s in M["shrines"] if s["x"] >= X0] + [(b["name"], b["x"], b["y"], b["radius_m"] * 0.55) for b in M["boss_arenas"] if b["x"] >= X0]
PLACED = []; DROPPED = []
def clear_ok(name, x, y):
    r = RAD.get(name, 1.0)
    if r <= 0: return True
    if any(math.hypot(rx - x, ry - y) < r + 1.5 for rx, ry, _ in ROADS): return False
    if any(math.hypot(kx - x, ky - y) < r + kr for _, kx, ky, kr in KEEP): return False
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
    # ── 포구 ──
    for k in range(10): add("harbor_pier", 1108 + k * 4.0, 440, 0, "선창(R3-3 끝, 바다 위 널판 높이 1.5)" if k == 0 else "", force=True, z=0.95)
    add("harbor_gauge_post", 1128, 443, 0, "물때 눈금 말뚝", force=True, z=0.95); add("harbor_gauge_post", 1146, 437, 0, "물때 눈금 말뚝", force=True, z=0.95)
    for x, y, r in [(1126, 452, 80), (1138, 428, 100), (1152, 450, 90), (1164, 430, 85)]: add("harbor_boat", x, y, r, "묶인 빈 배(흔들림은 코드, 기준 z=썰물 높이)", force=True, z=0.1)
    add("harbor_lamp_hut", 1132, 452, 0, "등대지기 막", force=True)
    for x, y in [(1000, 455), (1003, 463), (1010, 450)]: add("harbor_net_frame", x, y, 0, "그물 너는 마당(B09-D2 엿듣기 자리)" if x == 1000 else "")
    for x, y in [(993, 447), (1018, 461), (1022, 447)]: add("harbor_net_pile", x, y, RNG.uniform(0, 360))
    add("harbor_gaekju_house", 1052, 478, 180, "객주 집(마루 앞 (1048,466), B10-D1 장부)")
    add("harbor_inn", 1020, 408, 180, "포구 주막(B10-D2)")
    add("harbor_lamp_hut", 985, 475, 90, "갯골댁 집"); add("harbor_lamp_hut", 1070, 405, 270, "순덕 집")
    for x, y in [(1064, 466), (1040, 468), (1012, 404), (1090, 440)]: add("harbor_jar", x, y, RNG.uniform(0, 360))
    # ── 소금밭 (800,180)-(960,320): 둑 사이 칸 ──
    for gx in range(812, 950, 8):
        for gy in range(190, 312, 8): add("salt_pan", gx, gy, 0)
    for x, y in [(842, 246), (870, 258), (905, 262), (930, 292), (820, 290)]: add("salt_pile", x, y, RNG.uniform(0, 360), "소금 더미(달빛에 혼불처럼 보임)")
    add("salt_warehouse", 900, 300, 0, "소금 창고"); add("harbor_lamp_hut", 915, 305, 90, "덕보 집")
    for k in range(8): add("salt_dike", 822 + k * 17, 250, 0, "염전 둑(B09-D 염전 둑 880,250 주변)" if k == 3 else "")
    # ── 망부석 곶 ──
    add("cape_waiting_rock", 1236, 690, 90, "망부석(바다를 향함, 원 바깥 동쪽 끝)", force=True)
    for ix in range(7):
        for iy in range(6): add("cape_hutmyo", 1112 + ix * 3.6, 622 + iy * 3.6, RNG.uniform(-12, 12), "헛묘(마흔둘, B09-D1)", force=True)
    add("cape_new_grave", 1122, 646, 0, "S-086 새 무덤(몸이 든 무덤)", force=True); add("harbor_lamp_hut", 1105, 625, 0, "헛묘지기 집", force=True)
    # ── 난파 여울 ──
    add("shoal_wreck", 1135, 100, 20, "B-10 반쯤 가라앉은 배 갑판(썰물 밤에만 걸어 들어감)", force=True, z=0.0)
    for x, y in [(1098, 124), (1110, 160), (1160, 132), (1172, 82)]: add("shoal_rock", x, y, RNG.uniform(0, 360), "여울 바위(B10-D3)" if x == 1098 else "", z=0.0)
    # ── 물판: 바다가 있는 칸에만 ──
    for cx in range(X0 + 32, X0 + W, 64):
        for cy in range(32, H, 64):
            j0, j1, i0, i1 = cy - 32, cy + 32, cx - X0 - 32, cx - X0 + 32
            if (HGT[j0:j1 + 1, i0:i1 + 1] < LOW + 0.3).any(): PLACED.append({"prop": "tide_water", "file": "assets3d/act3/tide_water.glb", "x": cx, "y": cy, "rot": 0, "z": LOW, "r": 0.0, "note": "물판(코드가 높이를 썰물 -0.5↔밀물 +0.6으로 움직임)"})
build()
def main():
    bad = []
    for p in PLACED:
        if p.get("by_design") or p["r"] <= 0: continue
        for n, kx, ky, kr in KEEP:
            if math.hypot(kx - p["x"], ky - p["y"]) < p["r"] + kr - 0.01: bad.append((p["prop"], p["x"], p["y"], n))
    out = [{k: v for k, v in p.items() if k != "r"} for p in PLACED]
    json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "place_act3_east.py가 만든다. z=땅 높이(terrain_act3_east), 선창 1.5, 물판 -0.5", "props": out}, open(os.path.join(LAY, "act3_east_layout.json"), "w"), ensure_ascii=False, indent=1)
    rep = {"count": len(out), "dropped": DROPPED, "overlaps": bad, "moved": [p for p in out if "walk_snap" in p], "per_model": {n: sum(1 for p in out if p["prop"] == n) for n in sorted({p["prop"] for p in out})}}
    json.dump(rep, open(os.path.join(LAY, "act3_east_report.json"), "w"), ensure_ascii=False, indent=1)
    print("놓은 소품", len(out), "| 옮긴", len(rep["moved"]), "| 못 놓음", len(DROPPED), "| 겹침", len(bad)); print(rep["per_model"])
    for d in DROPPED[:10]: print("  못 놓음", d)
if __name__ == "__main__": main()
