"""3막 장례 대상 이름혼 10명(⑤ 갯마을 5 + ⑥ 도성 5)의 무릎 꿇는 자리 정하기(전엔 대문 남쪽 8m 임시). 2막 act2_soul_spots.py와 같은 규칙.
왜: 이름혼은 집(막·좌판) 가까이 있어야 장례 연결이 자연스럽고, 임시 8m 남쪽은 바다·성벽·길에 걸릴 수 있다.
규칙: 대문(gate)에서 2.5~4 m 안, 길 가운데 1.2 m·서낭당 4 m·이미 놓은 소품(배치표 3종)과 1.5 m 이상 떨어진 열린 땅, 물에 잠기는 낮은 땅(z<0.3)은 제외(⑤는 썰물 때만 드러나는 땅이라 안 됨). 남쪽 → 그 둘레 순.
실행: python3 tools/art3d/act3_soul_spots.py → assets3d/layouts/act3_soul_spots.json"""
import os, sys, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); LAY = os.path.join(ROOT, "assets3d", "layouts")
M = json.load(open("/mnt/project-files/planning/openworld/act3/act3_map.json")) if os.path.exists("/mnt/project-files/planning/openworld/act3/act3_map.json") else json.load(open(os.path.join(ROOT, "unity/Assets/Resources/Data/act3_map.json")))
def hm(d, hmin, hmax):
    a = np.array(Image.open(os.path.join(ROOT, "assets3d", d, "heightmap.png")).convert("RGBA")).astype(np.int64); return ((a[..., 0] << 8) | a[..., 1]) / 65535.0 * (hmax - hmin) + hmin
TER = {"east": (768, 0, hm("terrain_act3_east", -7.0, 10.0)), "west": (-640, 0, hm("terrain_act3_west", -7.0, 9.0))}
def ground(x, y):
    ox, oy, H = TER["east" if x >= 768 else "west"]; i = int(min(max(x - ox, 0), H.shape[1] - 2)); j = int(min(max(y - oy, 0), H.shape[0] - 2)); return float(H[j, i])
R0 = {"snow_patch", "tide_water", "city_skyline", "city_wall", "bridge_deck", "market_lantern_string"}   # 바닥 장식·먼 배경은 막지 않음
placed = []
for n in ("east", "west"):
    for p in json.load(open(os.path.join(LAY, f"act3_{n}_layout.json")))["props"]:
        r = 0.0 if p["prop"] in R0 else (1.0 if p["prop"] == "salt_pan" else 1.5)
        if r > 0: placed.append((p["x"], p["y"], r))
roads = []
for r in M["roads"]:
    P = r["points"]
    for a, b in zip(P[:-1], P[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
        roads += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
def free(x, y, gate):
    if ground(x, y) < 0.3: return False
    if any(math.hypot(px - x, py - y) < pr + 1.5 for px, py, pr in placed if math.hypot(px - gate[0], py - gate[1]) > 1.2): return False   # 대문 바로 곁 소품(집 자체)은 건너뜀
    if any(math.hypot(rx - x, ry - y) < 1.2 for rx, ry in roads): return False
    return all(math.hypot(s["x"] - x, s["y"] - y) >= 4 for s in M["shrines"])
SPECIAL = {"S-089": (1141.0, 440.0, (1137.0, 440.0), 1.5)}   # 등대지기 막: 기획 대문(1130,450)은 바다 바닥(z -2.5)이라 선창 끝 널판 위(막 (1141,440), 널판 윗면 z 1.5)로 옮김
out = []
for f in M["funerals"]:
    gx, gy = f["gate"]; best = None
    if f["soul"] in SPECIAL:
        sx, sy, kx, kz = SPECIAL[f["soul"]]
        out.append({"soul": f["soul"], "name": f["name"], "gate": [sx, sy], "gate_planned": f["gate"], "kneel_xy": list(kx[:2]), "dist_to_gate_m": 4.0, "z": kz, "faces_gate": True, "note": "선창 널판 위. 이름혼은 막(동쪽)을 향해 앉음"}); print(f["soul"], "선창 위", kx); continue
    for d in (2.5, 3.0, 3.5, 4.0):
        for a in (270, 250, 290, 230, 310, 200, 340, 180, 0, 90, 135, 45):
            x, y = gx + d * math.cos(math.radians(a)), gy + d * math.sin(math.radians(a))
            if free(x, y, (gx, gy)): best = (round(x, 1), round(y, 1), d, a); break
        if best: break
    out.append({"soul": f["soul"], "name": f["name"], "gate": f["gate"], "kneel_xy": list(best[:2]) if best else None, "dist_to_gate_m": best[2] if best else None,
                "z": round(ground(best[0], best[1]), 2) if best else None, "faces_gate": True})
    print(f["soul"], f["name"], f["gate"], "→", best)
json.dump({"note": "act3_soul_spots.py가 만든다. kneel_xy=이름혼 무릎 자리(필드 절대), faces_gate=대문을 향해 앉음. 집 모델은 막·좌판이 아직 없어 코드팀이 충돌과 맞춰 확인", "spots": out}, open(os.path.join(LAY, "act3_soul_spots.json"), "w"), ensure_ascii=False, indent=1)
