"""시즌 2 저승 ⑦~⑩ 걸어갈 길 점검: 막힘 원(배치표 소품)과 물(땅 높이<0)을 빼고, 몸 반지름 0.5 m + 여유 0.5 m(폭 2 m 길)로 입구·장소·보스 마당이 이어지는지 본다.
실행: python3 s2_walkcheck.py → assets3d/layouts/s2_walkcheck_report.json. 한계: ⑦ 강 건너기는 배(코드)·여울이라 강 서쪽 장소만 이어짐을 본다."""
import os, sys, json, math
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
import place_s2 as P, terrain_s2 as T
LAY = P.LAY
ENTRY = {7: (60, 250), 8: (620, 570), 9: (540, 900), 10: (470, -20)}
def points(rid):
    pts = {}
    if rid == 7:
        for k, v in T.M7["places"].items(): pts[k] = (v["x"], v["y"])
        for a in T.M7["boss_arenas"]: pts["마당 " + a["boss"]] = (a["x"], a["y"])
        for z in T.M7["rest_points"]: pts[z["name"]] = (z["x"], z["y"])
    else:
        R = T.M8["regions"][str(rid)]
        for k, v in R["places"].items(): pts[k] = (v["x"], v["y"])
        for a in R["boss_arenas"]: pts["마당 " + a["boss"]] = (a["x"], a["y"])
        for z in R["rest_points"]: pts[z["name"]] = (z["x"], z["y"])
    return pts
def run(rid):
    P.load_h(rid); T.setup(rid); X0, Y0, W, H = T.X0, T.Y0, T.W, T.H
    lay = json.load(open(os.path.join(LAY, f"s2_r{rid}_layout.json"), encoding="utf-8"))["props"]
    blocked = np.zeros((H + 1, W + 1), bool); gx = X0 + np.arange(W + 1); gy = Y0 + np.arange(H + 1)
    for p in lay:
        r = P.RAD.get(p["prop"], 0.0)
        if p["prop"].startswith(("hanok_", "prop_")): r = 1.1 if "gidan" in p["prop"] or "wall" in p["prop"] or "pillar" in p["prop"] else (1.0 if p["prop"] == "prop_dolddam" else 0.0)
        if r <= 0: continue
        i0, i1 = max(0, int(p["x"] - r - 2 - X0)), min(W + 1, int(p["x"] + r + 3 - X0)); j0, j1 = max(0, int(p["y"] - r - 2 - Y0)), min(H + 1, int(p["y"] + r + 3 - Y0))
        if i0 >= i1 or j0 >= j1: continue
        blocked[j0:j1, i0:i1] |= np.hypot(gx[None, i0:i1] - p["x"], gy[j0:j1, None] - p["y"]) < r
    G = P.HG[rid][4]
    if rid == 7: blocked |= G < 0.0                                    # 물(⑦ 강만, ⑩ 물막이 바닥은 마른 땅)
    clr = ndimage.distance_transform_edt(~blocked); walk = clr >= 1.0
    lab, n = ndimage.label(walk)
    def cell(x, y): return int(np.clip(round(y - Y0), 0, H)), int(np.clip(round(x - X0), 0, W))
    def nearest(x, y, rad=6):
        j, i = cell(x, y)
        if walk[j, i]: return j, i
        best = None
        for dj in range(-rad, rad + 1):
            for di in range(-rad, rad + 1):
                nj, ni = j + dj, i + di
                if 0 <= nj <= H and 0 <= ni <= W and walk[nj, ni] and (best is None or math.hypot(dj, di) < best[0]): best = (math.hypot(dj, di), nj, ni)
        return (best[1], best[2]) if best else None
    e = nearest(*ENTRY[rid]); elab = lab[e] if e else -1; out = {}
    for k, (x, y) in points(rid).items():
        c = nearest(x, y); out[k] = {"xy": [x, y], "reach": bool(c and lab[c] == elab), "snap_m": round(math.hypot(c[1] + X0 - x, c[0] + Y0 - y), 1) if c else None}
    bad = [k for k, v in out.items() if not v["reach"]]; return {"entry": ENTRY[rid], "points": len(out), "unreachable": bad, "detail": out}
if __name__ == "__main__":
    rep = {f"r{r}": run(r) for r in (7, 8, 9, 10)}
    for k, v in rep.items(): print(k, "점", v["points"], "못 닿음", v["unreachable"])
    json.dump(rep, open(os.path.join(LAY, "s2_walkcheck_report.json"), "w"), ensure_ascii=False, indent=1)
