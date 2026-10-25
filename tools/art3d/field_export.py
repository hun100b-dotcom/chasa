"""코드팀용 보조 목록 두 가지를 field_5x5.json에서 뽑는다.
1) layouts/field_5x5_instances.json — 같은 모델끼리 묶고 청크(128m)별로 나눈 위치 목록(GPU 인스턴싱·청크 로딩용)
2) layouts/field_5x5_zones.json — 구역별 분위기·밀도·적 군집 후보 enemy_camps(구역당 3~5곳, 반경 m)
실행: python3 field_export.py  (field_layout.py를 먼저 돌려 field_5x5.json을 갱신해 둘 것)"""
import os, json, math, random
from collections import defaultdict
A3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets3d", "layouts")
F = json.load(open(os.path.join(A3, "field_5x5.json"))); T = 8; CH = 128

# 1) 인스턴스 묶음
inst = defaultdict(lambda: defaultdict(list))
for p in F["props"]: inst[p["prop"]][f'{int(p["x"] // CH)}_{int(p["y"] // CH)}'].append([p["x"], p["y"], p["rot"], p.get("z", 0.0)])
tiles = defaultdict(lambda: defaultdict(list))
for t in F["tiles"]: tiles[t["tile"]][f'{int(t["ix"] * T // CH)}_{int(t["iy"] * T // CH)}'].append([t["ix"], t["iy"], t["rot"], t["z"]])
out = {"units": "m", "axes": "x=동, y=북(유니티 (x,z)=(x,y)), rot=반시계 도", "chunk_m": CH,
       "note": "props: 모델 이름 → 청크 '열_행' → [x, y, rot, z]. 같은 모델은 GPU 인스턴싱 한 번에. tiles는 [ix, iy, rot, z](칸 중심 = ix*8+4).",
       "props": {k: dict(v) for k, v in inst.items()}, "tiles": {k: dict(v) for k, v in tiles.items()},
       "counts": {"prop_kinds": len(inst), "prop_total": sum(len(l) for v in inst.values() for l in v.values())}}
json.dump(out, open(os.path.join(A3, "field_5x5_instances.json"), "w"), ensure_ascii=False, separators=(",", ":"))

# 2) 구역 성격과 적 군집 후보
grid = {(t["ix"], t["iy"]): t for t in F["tiles"]}
BAD = ("br_rapids", "br_deep", "br_shore", "terrain_tile_stream", "terrain_tile_paddy", "terrain_tile_cliff_wall", "terrain_tile_slope_straight", "terrain_tile_slope_corner_out", "terrain_tile_slope_corner_in", "terrain_tile_road", "terrain_tile_bank")
def walkable(x, y):
    ix, iy = int(x // T), int(y // T); t = grid.get((ix, iy))
    return 0 <= ix < 80 and 0 <= iy < 80 and (t is None or not t["tile"].startswith(BAD))
def near_struct(x, y, r):
    return any((q["x"] - x) ** 2 + (q["y"] - y) ** 2 < r * r for s in F["structures"] for q in (s.get("pieces") or [s]))
SPAWN = (196, 30); rnd = random.Random(2026)
STYLE = {
 "솔고개 마을": {"mood": "밤에도 등불이 켜진 안전한 고향. 집이 촘촘하고 마당마다 가축·장독·볏가리.", "density": "집 7채+변두리 6채, 소품 매우 많음", "enemy": "마을 안은 적 없음. 변두리 밖에만 떠도는 혼.", "camps": 3},
 "보릿들": {"mood": "넓고 트인 밭. 이랑·허수아비·원두막이 있는 쓸쓸한 들판. 시야가 열려 멀리서 혼이 보인다.", "density": "나무 적고 밭 칸 많음, 가운데 촌락 하나", "enemy": "허수아비 곁·밭고랑 사이 혼 무리(해 넘긴 혼 중심).", "camps": 5},
 "물막이 골": {"mood": "개울과 벼랑 사이 좁고 빽빽한 숲 골짜기. 방앗간이 외딴 불빛.", "density": "숲 군집 매우 빽빽, 갈대·바위", "enemy": "개울가·벼랑 아래 오래된 혼과 보스 1호(나루 영감) 주변 호위.", "camps": 5},
 "폐당집": {"mood": "고지의 무너진 당집과 무덤 터. 마른 나무, 무덤 무리, 푸른 혼불.", "density": "마른 나무·무덤 많음, 길 좁음", "enemy": "무덤 곁 원념 덩어리와 오래된 혼.", "camps": 4},
 "검은여울": {"mood": "어두운 강, 돌다리, 나루터, 약초·역병 기운(2막). 물가 갈대와 버드나무.", "density": "물가 소품 집중, 숲 중간", "enemy": "강둑·나루터 역병 혼(멍울). 의원 집은 안전지대.", "camps": 4}}
zones_out = []
for z in F["zones"]:
    x0, y0, x1, y1 = z["rect_m"]; st = STYLE[z["name"]]; camps = []; tries = 0
    while len(camps) < st["camps"] and tries < 4000:
        tries += 1; mg = 3 if z["name"] == "솔고개 마을" else 12; x = round(rnd.uniform(x0 + mg, x1 - mg), 1); y = round(rnd.uniform(y0 + mg, y1 - mg), 1); r = rnd.choice((6, 8) if mg == 3 else (8, 10, 12, 14))
        if not all(walkable(x + dx, y + dy) for dx, dy in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r))): continue
        if z["name"] == "솔고개 마을" and not (x < 176 or x > 216 or y < 24 or y > 96): continue   # 마을 안쪽 제외
        if math.hypot(x - SPAWN[0], y - SPAWN[1]) < (45 if z["name"] == "솔고개 마을" else 60) or near_struct(x, y, r + 4): continue
        if any(math.hypot(x - c["x"], y - c["y"]) < 40 for c in camps): continue
        camps.append({"x": x, "y": y, "radius_m": r, "size_hint": rnd.choice(("소(3~4)", "중(5~7)", "중(5~7)", "대(8~10)"))})
    zones_out.append({"name": z["name"], "rect_m": z["rect_m"], "mood": st["mood"], "density": st["density"], "enemy_theme": st["enemy"], "enemy_camps": camps})
json.dump({"units": "m", "axes": "x=동, y=북", "spawn": SPAWN, "note": "enemy_camps는 걸을 수 있는 풀밭·밭 위에서 건물에서 4m 이상, 시작점에서 60m 이상, 군집끼리 40m 이상 떨어진 자리. 후보일 뿐이니 코드에서 가감하세요.", "zones": zones_out},
          open(os.path.join(A3, "field_5x5_zones.json"), "w"), ensure_ascii=False, indent=1)
print("인스턴스", out["counts"], "군집", {z["name"]: len(z["enemy_camps"]) for z in zones_out})
