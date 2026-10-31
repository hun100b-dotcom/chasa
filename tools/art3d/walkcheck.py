"""걸어갈 길 점검기(길찾기 점검). 필드 배치표에서 Unity와 똑같은 규칙(FieldRules.BlockerRadius 의 동그라미 충돌)으로 막힌 곳을 만들고,
'폭 2m 이상으로 이어진 길'이 주요 지점 사이에 있는지 검사한다. 배치를 고친 뒤 이 도구를 돌려 막힌 곳이 0인지 확인한다.
 - 여유폭(clearance) = 그 점에서 가장 가까운 막힌 곳 가장자리까지의 거리. 폭 2m 길 = 여유폭 1.0m 이상인 점들의 이어짐. 플레이어 몸(반지름 0.5m)만 지나가려면 0.5m 이상.
 - 두 지점 사이 '가장 넓은 길의 가장 좁은 곳'(병목 폭)을 구한다. 이 값이 2.0m 이상이면 합격.
사용: python3 tools/art3d/walkcheck.py            # 마을+주요 지점 전부(1m 격자) 점검 보고
      python3 tools/art3d/walkcheck.py --json out.json   # 코드팀 자동 점검용 결과
다른 팀 확인용: Unity 쪽은 같은 식 (FieldRules.BlockerRadius + PLAYER_RADIUS 0.5)이므로 결과가 같아야 한다."""
import os, sys, json, math, heapq
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
LAY = os.path.join(ROOT, "assets3d", "layouts")
MIN_W = 2.0          # 요구 길 폭(m)
PLAYER_R = 0.5

def blocker_radius(name):
    """unity/Assets/Scripts/Core/FieldRules.cs BlockerRadius 와 같은 표(한쪽을 바꾸면 이쪽도 바꾼다)."""
    if name is None: return 0.0
    if name == "br_deep": return 0.0         # 큰 강은 새 높이맵+물로 대체되어 배치표 조각은 안 쓴다(물 충돌은 이 도구 범위 밖)
    if name.startswith("terrain_tile_") or name.startswith("br_"):
        return {"br_willow_a": 0.7, "br_willow_b": 0.7, "br_herb_rack": 1.2, "br_jars": 0.6, "br_med_sign": 0.3}.get(name, 0.0)
    if name.startswith("hanok_"): return 1.1 if ("gidan" in name or "wall" in name or "pillar" in name) else 0.0
    if name.startswith("nature_"):
        if any(k in name for k in ("pine", "zelkova", "dead")): return 0.6
        return 0.5 if "bamboo" in name else 0.0
    if name == "terrain_rock_small": return 0.7
    if name == "terrain_rock_medium": return 1.3
    if name == "terrain_rock_cluster": return 2.0
    return {"prop_gaejip_empty": 0.6, "prop_market_drum_frame": 0.5, "prop_seonangdang": 2.2, "prop_dolddam": 1.0, "prop_jangdok": 0.7, "prop_jangseung": 0.4, "prop_umul": 1.3, "prop_sangyeo": 1.5, "prop_sotdae": 0.3, "prop_choga": 2.5, "prop_giwa": 2.5, "night_torch_stand": 0.3}.get(name, 0.0)

def load(extra_removed=()):
    """(x, y, 반지름, 이름) 목록 — 필드 배치표 + 마을 배치표(옮김 포함). build_field_data.py 와 같은 합치기."""
    f = json.load(open(os.path.join(LAY, "field_5x5.json"), encoding="utf-8")); v = json.load(open(os.path.join(LAY, "solgogae_village.json"), encoding="utf-8"))
    ox, oy = f["village_offset_m"]; out = []
    def add(n, x, y):
        r = blocker_radius(n)
        if r > 0: out.append((x, y, r, n))
    for p in f["props"]: add(p["prop"], p["x"], p["y"])
    for s in f["structures"]:
        for q in (s.get("pieces") or [s]): add(q.get("piece"), q["x"], q["y"])
    for b in v["buildings"]:
        for q in b["pieces"]: add(q["piece"], q["x"] + ox, q["y"] + oy)
    for p in v["props"]: add(p["prop"], p["x"] + ox, p["y"] + oy)
    ep = os.path.join(LAY, "act1_extra.json")   # 1막 추가 소품(개집·북틀 등, place_act1_extra.py)
    if os.path.exists(ep):
        for p in json.load(open(ep, encoding="utf-8"))["props"]: add(p["prop"], p["x"], p["y"])
    lp = os.path.join(LAY, "act1_life.json")   # 1막 생활 소품(place_act1_life.py)
    if os.path.exists(lp):
        for p in json.load(open(lp, encoding="utf-8"))["props"]: add(p["prop"], p["x"], p["y"])
    return out

def points():
    """주요 지점: 서낭당·시작·마을·보스 마커 + NPC 자리표 + 이름혼 자리 + 보스 마당."""
    f = json.load(open(os.path.join(LAY, "field_5x5.json"), encoding="utf-8")); P = {}
    for m in f["markers"]:
        if m["kind"] in ("seonang", "spawn", "boss", "village", "ruin", "doctor", "soulpath"): P[m["name"]] = (m["x"], m["y"])
    P["보스 ② 월화 마당"] = (580.0, 521.0); P["보스 ③ 서 의원 마당"] = (46.0, 453.0)
    ap = os.path.join(ROOT, "data", "art", "npc_places_act1.json")
    if os.path.exists(ap):
        a = json.load(open(ap, encoding="utf-8"))
        for k, v in a.get("named_souls_first_session", {}).items(): P["이름혼 " + k] = (v["x"], v["y"])
        for k, v in a.get("places", {}).items(): P["자리 " + k] = (v["x"], v["y"])
    return P

class Grid:
    def __init__(self, blockers, x0, y0, x1, y1, res=1.0):
        self.x0, self.y0, self.res = x0, y0, res
        self.w, self.h = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
        cl = np.full((self.h, self.w), 99.0, np.float32)
        gx = x0 + np.arange(self.w) * res; gy = y0 + np.arange(self.h) * res
        for (x, y, r, n) in blockers:
            reach = r + 6.0
            i0, i1 = max(0, int((x - reach - x0) / res)), min(self.w, int((x + reach - x0) / res) + 2)
            j0, j1 = max(0, int((y - reach - y0) / res)), min(self.h, int((y + reach - y0) / res) + 2)
            if i0 >= i1 or j0 >= j1: continue
            d = np.hypot(gx[None, i0:i1] - x, gy[j0:j1, None] - y) - r
            cl[j0:j1, i0:i1] = np.minimum(cl[j0:j1, i0:i1], d)
        self.cl = cl
    def idx(self, x, y): return int(round((y - self.y0) / self.res)), int(round((x - self.x0) / self.res))
    def inside(self, x, y):
        j, i = self.idx(x, y); return 0 <= j < self.h and 0 <= i < self.w
    def widest(self, a, b, start_slack=6.0):
        """a→b 병목 폭(가장 넓은 길의 가장 좁은 곳)과 그 길(격자 칸 목록). 시작·끝이 막힌 곳 안이면 가까운 열린 칸(start_slack m 이내)에서 시작한다."""
        sj, si = self.best_near(a, start_slack); tj, ti = self.best_near(b, start_slack)
        best = np.full((self.h, self.w), -1e9, np.float32); prev = {}
        best[sj, si] = self.cl[sj, si]; pq = [(-self.cl[sj, si], sj, si)]
        while pq:
            nb, j, i = heapq.heappop(pq); nb = -nb
            if nb < best[j, i] - 1e-6: continue
            if (j, i) == (tj, ti): break
            for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nj, ni = j + dj, i + di
                if 0 <= nj < self.h and 0 <= ni < self.w:
                    w = min(nb, float(self.cl[nj, ni]))
                    if w > best[nj, ni]: best[nj, ni] = w; prev[(nj, ni)] = (j, i); heapq.heappush(pq, (-w, nj, ni))
        path = []; c = (tj, ti)
        while c in prev: path.append(c); c = prev[c]
        return float(best[tj, ti]), path, (sj, si), (tj, ti)
    def best_near(self, p, slack):
        j, i = self.idx(*p); rad = int(slack / self.res) + 1
        j0, j1, i0, i1 = max(0, j - rad), min(self.h, j + rad + 1), max(0, i - rad), min(self.w, i + rad + 1)
        sub = self.cl[j0:j1, i0:i1]; k = np.unravel_index(np.argmax(sub), sub.shape); return j0 + k[0], i0 + k[1]
    def straight_min(self, a, b):
        """a→b 직선 위 여유폭의 최솟값(봇이 곧장 걸어가면 막히는지 보는 참고값)."""
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / self.res)); m = 99.0
        for t in range(n + 1):
            x = a[0] + (b[0] - a[0]) * t / n; y = a[1] + (b[1] - a[1]) * t / n
            if self.inside(x, y): j, i = self.idx(x, y); m = min(m, float(self.cl[j, i]))
        return m
    def xy(self, j, i): return self.x0 + i * self.res, self.y0 + j * self.res

def run(blockers=None, res=1.0, quiet=False):
    blockers = blockers or load(); P = points()
    village = {k: v for k, v in P.items() if 160 <= v[0] <= 232 and 24 <= v[1] <= 100}
    hub = P.get("서낭당·넋길 이동 지점 ①(마을)", (188, 36)); res_out = {"min_width_m": MIN_W, "pairs": [], "points": {}}
    # 마을 안 지점끼리: 0.5m 격자
    G = Grid(blockers, 150, 14, 240, 110, 0.5)
    spawn = P.get("시작 위치(마을 남쪽 입구)", (196, 30))
    for k, v in sorted(village.items()):
        w, path, s, t = G.widest(spawn, v); j, i = G.idx(*v); own = float(G.cl[j, i])
        ok = w >= MIN_W; sm = G.straight_min(spawn, v); res_out["pairs"].append({"from": "시작 위치", "to": k, "to_xy": v, "bottleneck_m": round(w, 2), "ok": ok, "point_clearance_m": round(own, 2), "straight_line_blocked": sm < PLAYER_R})
    # 마을 밖 주요 지점(서낭당 ②③④, 보스 마당 등)까지: 서낭당 ①에서 1m 격자
    G2 = Grid(blockers, 0, 0, 640, 640, 1.0)
    far = {k: v for k, v in P.items() if k not in village and (k.startswith("서낭당") or k.startswith("이름혼") or k.startswith("보스") or "보스" in k or k.startswith("폐당집") or k.startswith("넋길") or "의원" in k)}
    for k, v in sorted(far.items()):
        w, path, s, t = G2.widest(hub, v); res_out["pairs"].append({"from": "서낭당 ①(마을)", "to": k, "to_xy": v, "bottleneck_m": round(w, 2), "ok": w >= MIN_W})
    bad = [p for p in res_out["pairs"] if not p["ok"]]
    if not quiet:
        for p in res_out["pairs"]: print(("OK " if p["ok"] else "막힘"), f'{p["bottleneck_m"]:6.2f}m', ("직선막힘" if p.get("straight_line_blocked") else "        "), f'{p["from"]} → {p["to"]} {tuple(p["to_xy"])}')
        print(f"검사 {len(res_out['pairs'])}쌍, 폭 {MIN_W}m 미만 {len(bad)}쌍, 직선으로 가면 막히는 쌍(참고) {sum(1 for p in res_out['pairs'] if p.get('straight_line_blocked'))}")
    return res_out, G, bad

if __name__ == "__main__":
    out, G, bad = run()
    if "--json" in sys.argv: json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
    sys.exit(1 if bad else 0)
