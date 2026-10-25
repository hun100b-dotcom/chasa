"""길 막힘 정리: ① NPC·이름혼 자리를 '걸어서 설 수 있는 열린 땅'(여유폭 1.2m 이상)으로 옮기고 ② 길찾기용 파일(접근 지점·경로·여유폭 지도)을 만든다.
왜: 코드팀 봇이 서낭당 단서·이름혼에게 가다 순간이동한 원인은 (a) 목표점이 서낭나무(막힘 반지름 2.2m) 안쪽이라 닿을 수 없음 (b) 담·집 안쪽에 박힌 자리 (c) 직선으로만 걸어 담에 막힘.
이 스크립트는 반복해 돌려도 같은 결과(멱등). 사용: python3 tools/art3d/walk_fix.py"""
import os, sys, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import walkcheck as W
from PIL import Image
ROOT = W.ROOT; LAY = W.LAY
FILES = [os.path.join(LAY, "npc_places_act1.json"), os.path.join(ROOT, "data", "art", "npc_places_act1.json")]
SEONANG = [(188, 36), (186, 39)]       # 서낭당 나무(막힘 반지름 2.2m): 나무 밑동에 서는 자리는 옮기지 않고 '접근 지점'을 따로 준다

def snap(G, x, y, want=1.2, rad=6.0):
    j, i = G.idx(x, y)
    if G.cl[j, i] >= want: return x, y
    r = int(rad / G.res); best = None
    for dj in range(-r, r + 1):
        for di in range(-r, r + 1):
            nj, ni = j + dj, i + di
            if 0 <= nj < G.h and 0 <= ni < G.w and G.cl[nj, ni] >= want:
                d = math.hypot(dj, di)
                if best is None or d < best[0]: best = (d, nj, ni)
    if best is None: return x, y
    return G.xy(best[1], best[2])

def main():
    b = W.load(); G = W.Grid(b, 0, 0, 640, 640, 0.5); moved = []
    for fp in FILES:
        if not os.path.exists(fp): continue
        d = json.load(open(fp, encoding="utf-8"))
        for sec in ("places", "named_souls_first_session"):
            for k, v in d.get(sec, {}).items():
                if any(math.hypot(v["x"] - sx, v["y"] - sy) < 3.2 for sx, sy in SEONANG): continue
                orig = v.get("walk_snap", {}).get("from", [v["x"], v["y"]])
                nx, ny = snap(G, orig[0], orig[1])
                if (round(nx, 1), round(ny, 1)) != (v["x"], v["y"]) or "walk_snap" in v:
                    if (round(nx, 1), round(ny, 1)) != tuple(orig):
                        v["walk_snap"] = {"from": list(orig), "why": "서 있을 자리가 담·집·나무 막힘 안쪽이라 열린 땅(여유폭 1.2m↑)으로 옮김"}; v["x"], v["y"] = round(nx, 1), round(ny, 1); moved.append((k, orig, (v["x"], v["y"])))
                    elif "walk_snap" in v: del v["walk_snap"]
        json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("옮긴 자리", len({m[0] for m in moved}))
    for m in sorted({(a, tuple(o), n) for a, o, n in moved}): print("  ", m[0], m[1], "→", m[2])
    # ── 길찾기 파일 ──
    P = W.points(); G1 = W.Grid(b, 0, 0, 640, 640, 1.0)
    pts = {}
    for k, v in P.items():
        j, i = G.idx(*v); own = float(G.cl[j, i])
        ax, ay = snap(G, v[0], v[1], 1.0, 8.0) if own < 1.0 else v
        # 서낭나무처럼 중심이 막힌 곳이면 '남쪽(시작 쪽)에서 다가가는' 열린 지점을 우선
        if own < 0 and any(math.hypot(v[0] - sx, v[1] - sy) < 3.2 for sx, sy in SEONANG):
            for dy in np.arange(2.4, 7.0, 0.25):
                jj, ii = G.idx(v[0], v[1] - dy)
                if G.cl[jj, ii] >= 1.0: ax, ay = G.xy(jj, ii); break
        pts[k] = {"xy": [round(v[0], 1), round(v[1], 1)], "clearance_m": round(own, 2), "approach_xy": [round(ax, 1), round(ay, 1)]}
    spawn = P["시작 위치(마을 남쪽 입구)"]; hub = pts["서낭당·넋길 이동 지점 ①(마을)"]["approach_xy"]
    def simplify(path_cells, need, G):
        xs = [G.xy(*c) for c in path_cells[::-1]]
        if not xs: return []
        out = [xs[0]]; i = 0
        def ok(a, bq):
            n = max(2, int(math.hypot(bq[0] - a[0], bq[1] - a[1]) / 0.5))
            for t in range(n + 1):
                x = a[0] + (bq[0] - a[0]) * t / n; y = a[1] + (bq[1] - a[1]) * t / n; jj, ii = G.idx(x, y)
                if G.cl[jj, ii] < need: return False
            return True
        while i < len(xs) - 1:
            j = len(xs) - 1
            while j > i + 1 and not ok(xs[i], xs[j]): j -= 1
            out.append(xs[j]); i = j
        return out
    GV = W.Grid(b, 150, 14, 240, 110, 0.5); routes = {}
    for src_name, src in (("시작 위치", spawn), ("서낭당 ①", hub)):
        for k, v in pts.items():
            if k.startswith("자리 서낭당") and k != "자리 서낭당 고개 고갯마루": pass
            inv = 150 <= v["approach_xy"][0] <= 240 and 14 <= v["approach_xy"][1] <= 110 and 150 <= src[0] <= 240
            GG = GV if inv else G1
            wd, path, s, t = GG.widest(src, tuple(v["approach_xy"]), 4.0)
            wp = simplify(path, 1.0 if wd >= 1.0 else 0.5, GG)
            routes[f"{src_name}→{k}"] = {"width_m": round(wd, 2), "waypoints": [[round(x, 1), round(y, 1)] for x, y in wp]}
    nav = {"note": "길찾기 점검·이동 보조(아트). points: 주요 지점과 '닿을 수 있는 접근 지점(approach_xy)'. routes: 시작 위치/서낭당 ①에서 각 지점까지 폭 2m 이상 길의 꺾는 점(웨이포인트, 필드 절대 m, x=동 y=북 / Unity는 (x, 높이, y)). 봇은 목표 대신 approach_xy를 향해 웨이포인트를 차례로 따라가면 막히지 않는다.",
           "min_width_m": W.MIN_W, "points": pts, "routes": routes,
           "clearance_map": {"file": "nav_clearance_1m.png", "grid_m": 1.0, "origin_xy": [0, 0], "size": [640, 640], "decode": "여유폭(m) = 픽셀값/20 (0=막힘·0.5m 미만, 20↑ = 폭 2m 길 통과 가능). 가로=x(동), 세로는 위가 y=639(북)", "player_radius_m": W.PLAYER_R}}
    json.dump(nav, open(os.path.join(LAY, "nav_points.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cl = np.clip(G1.cl, 0, 12.7); img = (cl * 20).round().astype(np.uint8)[::-1]
    Image.fromarray(img, "L").save(os.path.join(LAY, "nav_clearance_1m.png"), optimize=True)
    print("접근 지점", len(pts), "경로", len(routes), "폭 부족 경로", sum(1 for r in routes.values() if r["width_m"] < W.MIN_W))
if __name__ == "__main__": main()
