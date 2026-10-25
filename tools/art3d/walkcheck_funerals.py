"""1막 장례(funeral_targets_act1.json)·제사 지켜보기(jesa_watch_act1.json) 새 자리의 걷기 확인. 실행: python3 tools/art3d/walkcheck_funerals.py
각 좌표의 여유폭(막힌 곳 가장자리까지 거리)을 재고, 1.0m(폭 2m 길) 미만이면 가까운 열린 땅(1.2m 이상)을 제안한다. 서낭당 ①에서 그 자리까지 폭 2m 길이 이어지는지도 본다.
행렬 경로는 인접한 두 점 사이 직선을 따라 가장 좁은 곳(여유폭)을 잰다. 결과: assets3d/layouts/funeral_walk_report.json (기획이 walk_ok·좌표를 옮길 때 쓴다)."""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
import walkcheck as W
from walk_fix import snap
PL = "/mnt/project-files/planning/data"
def clear(G, x, y): j, i = G.idx(x, y); return float(G.cl[j, i]) if G.inside(x, y) else -1.0
def main():
    bl = W.load(); G = W.Grid(bl, 0, 0, 640, 640, 0.5); hub = (188, 36); rep = {"funerals": [], "jesa": []}; bad = 0
    def judge(label, xy, reach=True):
        nonlocal bad
        c = clear(G, *xy); s = snap(G, xy[0], xy[1], want=1.2, rad=6.0); w = G.widest(hub, tuple(xy))[0] if (reach and G.inside(*xy)) else None   # 마을 밖(장터·무덤골)은 도달 검사를 walkcheck.py 의 36쌍이 맡는다
        ok = c >= 1.0 and (w is None or w >= 2.0)
        if not ok: bad += 1
        return {"label": label, "xy": list(xy), "clearance_m": round(c, 2), "reach_from_hub_m": None if w is None else round(w, 2), "ok": ok, "snap_to": None if s == tuple(xy) else [round(s[0], 2), round(s[1], 2)]}
    t = json.load(open(os.path.join(PL, "funeral_targets_act1.json"), encoding="utf-8"))
    for f in t["funerals"]:
        r = {"soul": f["soul"], "name": f["name"], "points": []}
        for k in ("gate", "chasa_start", "sajabap"):
            if k in f and f[k]: r["points"].append(judge(k, f[k]))
        for k in ("stop_object", "restart_object", "noje", "exit"):
            if k in f and f[k] and f[k].get("xy"): r["points"].append(judge(k, f[k]["xy"], reach=k != "exit"))
        pr = f.get("procession") or []; worst = 99.0
        for a, b in zip(pr, pr[1:]):
            n = max(2, int(math.dist(a, b) / 0.5))
            for q in range(n + 1): worst = min(worst, clear(G, a[0] + (b[0] - a[0]) * q / n, a[1] + (b[1] - a[1]) * q / n))
        r["procession_min_clearance_m"] = round(worst, 2) if pr else None; r["procession_ok"] = (not pr) or worst >= 1.0
        if not r["procession_ok"]: bad += 1
        rep["funerals"].append(r)
    j = json.load(open(os.path.join(PL, "jesa_watch_act1.json"), encoding="utf-8"))
    for s in j["spots"]:
        xy = [s["x"], s["z"]] if "z" in s and "x" in s else None
        if xy: rep["jesa"].append({"id": s.get("id"), "soul_name": s.get("soul_name"), **judge("spot", xy)})
    json.dump(rep, open(os.path.join(W.LAY, "funeral_walk_report.json"), "w"), ensure_ascii=False, indent=1)
    for f in rep["funerals"]:
        for p in f["points"]:
            if not p["ok"]: print("막힘", f["name"], p["label"], p["xy"], "여유", p["clearance_m"], "도달", p["reach_from_hub_m"], "→ 제안", p["snap_to"])
        if not f["procession_ok"]: print("행렬 좁음", f["name"], f["procession_min_clearance_m"])
    for s in rep["jesa"]:
        if not s["ok"]: print("막힘(제사)", s["id"], s["soul_name"], s["xy"], "여유", s["clearance_m"], "도달", s["reach_from_hub_m"], "→ 제안", s["snap_to"])
    print("점검", sum(len(f["points"]) for f in rep["funerals"]) + len(rep["jesa"]), "곳 + 행렬", len(rep["funerals"]), "줄, 문제", bad)
if __name__ == "__main__": main()
