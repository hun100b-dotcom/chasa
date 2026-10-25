"""2막 장례 대상 이름혼 9명의 무릎 꿇는 자리 정하기(전엔 대문 남쪽 8m 임시).
왜: 이름혼은 집 대문 가까이 무릎 꿇어 있어야 장례 연결이 자연스럽고, 8m 남쪽은 길·벼랑·담에 걸릴 수 있다.
규칙: 대문에서 2.5~4m 안, 길 가운데·서낭당은 피하고, 이미 놓은 소품(act2_layout)과 1.5m 이상 떨어진 열린 땅. 대문 앞 길쪽(남쪽·길 방향)을 먼저 본다.
실행: python3 tools/art3d/act2_soul_spots.py → assets3d/layouts/act2_soul_spots.json"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
import place_act2 as P
MAP = P.M
def free(x, y):
    for p in P.PLACED:
        if p["r"] > 0 and math.hypot(p["x"] - x, p["y"] - y) < p["r"] + 1.5: return False
    for rx, ry, rid in P.ROADS:
        if rid not in P.SKIP_ROAD and math.hypot(rx - x, ry - y) < 1.2: return False
    for s in MAP["shrines"]:
        if math.hypot(s["x"] - x, s["y"] - y) < 4: return False
    return True
out = []
for f in MAP["funerals"]:
    gx, gy = f["gate"]; best = None
    for d in (2.5, 3.0, 3.5, 4.0):
        for a in (270, 250, 290, 230, 310, 200, 340, 180, 0, 90):       # 270° = 남쪽(대문 앞), 먼저 남쪽 근처부터
            x, y = gx + d * math.cos(math.radians(a)), gy + d * math.sin(math.radians(a))
            if free(x, y): best = (round(x, 1), round(y, 1), d, a); break
        if best: break
    out.append({"soul": f["soul"], "name": f["name"], "gate": f["gate"], "kneel_xy": list(best[:2]) if best else None, "dist_to_gate_m": best[2] if best else None,
                "z": round(P.ground(best[0], best[1]), 2) if best else None, "faces_gate": True})
    print(f["soul"], f["gate"], "→", best)
json.dump({"note": "act2_soul_spots.py가 만든다. kneel_xy=이름혼 무릎 자리(필드 절대), faces_gate=대문을 향해 앉음. 마을 집·담은 아직 act2_layout에 없어 코드팀이 집 충돌과 맞춰 확인", "spots": out},
          open(os.path.join(P.LAY, "act2_soul_spots.json"), "w"), ensure_ascii=False, indent=1)
