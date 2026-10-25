#!/usr/bin/env python3
"""
build_field_data.py — 아트팀 필드 배치표(field_5x5.json 등)를 유니티가 읽는 한 파일(field.json)로 줄이고,
쓰는 GLB 모델을 Resources/Models/Field/ 에 모은다.

왜? 아트 배치표는 블렌더 좌표(x=동, y=북, z=위)와 파일 경로가 길게 들어 있다. 게임은 그중 필요한 것만 짧은 표로 읽는다.
  - 좌표: 유니티 (x, 높이, z) = (x, z, y). 회전: 유니티 yaw = -rot (아트 약속)
  - 마을 배치표(solgogae_village.json)는 필드의 village_offset_m 만큼 옮겨 합친다
  - 풀밭 칸(표에 없는 칸)은 코드가 채운다(5천 칸을 표에 적지 않으려고)
사용: python3 tools/build_field_data.py <assets3d 폴더>
"""
import json, os, shutil, sys

art = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = os.path.join(root, "unity", "Assets", "Resources")
f = json.load(open(os.path.join(art, "layouts", "field_5x5.json"), encoding="utf-8"))
v = json.load(open(os.path.join(art, "layouts", "solgogae_village.json"), encoding="utf-8"))
lights_src = json.load(open(os.path.join(art, "layouts", "field_5x5_lights.json"), encoding="utf-8"))
ox, oy = f["village_offset_m"]

used = set()
items = []

# 큰 강 조각(물판·바닥 상자가 8m 칸으로 나뉜 것)은 새 연속 높이맵+물로 대체됐다. 다리·나루터 같은 구조물은 그대로 둔다
RIVER_SKIP = {"br_deep", "br_rapids", "br_shore"}

def add(name, x, y, rot, z=0.0, tile=0):
    if name in RIVER_SKIP: return
    used.add(name)
    items.append({"n": name, "x": round(x, 2), "z": round(y, 2), "y": round(z, 2), "r": int(rot) % 360, "t": tile})

TILE = f["tile_m"] if "tile_m" in f else f["grid"]["tile_m"]
for t in f["tiles"]:
    add(t["tile"], t["ix"] * TILE + TILE / 2, t["iy"] * TILE + TILE / 2, t.get("rot", 0), t.get("z", 0.0), 1)
for p in f["props"]:
    add(p["prop"], p["x"], p["y"], p.get("rot", 0), p.get("z", 0.0))
for s in f["structures"]:
    if "pieces" in s:
        for q in s["pieces"]: add(q["piece"], q["x"], q["y"], q.get("rot", 0), q.get("z", 0.0))
    else:
        add(s["piece"], s["x"], s["y"], s.get("rot", 0), s.get("z", 0.0))
# 마을(원점이 필드의 (ox, oy))
for b in v["buildings"]:
    for q in b["pieces"]: add(q["piece"], q["x"] + ox, q["y"] + oy, q.get("rot", 0), q.get("z", 0.0))
for p in v["props"]:
    add(p["prop"], p["x"] + ox, p["y"] + oy, p.get("rot", 0), p.get("z", 0.0))

# 바닥 채움 소품(아트 field_cover.json: 풀·꽃·보리 이랑·돌·강변 소품). 기본은 tier 1(밭·강변·길가 소품, 약 5천)만 넣는다.
# 풀·꽃(tier 2, 약 2만)은 수가 많아 코드가 GPU 인스턴싱·거리 컬링을 갖춘 뒤에 환경변수 FIELD_COVER_TIER=2 로 켠다. 0 이면 전부 뺀다.
cover_tier = int(os.environ.get("FIELD_COVER_TIER", "1"))
cp = os.path.join(art, "layouts", "field_cover.json")
if cover_tier > 0 and os.path.exists(cp):
    n0 = len(items)
    for c in json.load(open(cp, encoding="utf-8"))["props"]:
        if c["tier"] <= cover_tier: add(c["prop"], c["x"], c["y"], c["rot"], c.get("z", 0.0))
    print("바닥 채움 소품", len(items) - n0, "(tier <=", cover_tier, ")")

markers = [{"kind": m["kind"], "name": m["name"], "x": m["x"], "z": m["y"]} for m in f["markers"]]
lights = [{"x": l["x"], "z": l["y"], "y": l["z"], "color": l["color"], "intensity": l["intensity"], "range": l["range_m"],
           "flicker": 1 if l.get("flicker") else 0} for l in lights_src["lights"]]
# 보스 바닥 싸움터(2호 월화 굿판·3호 서 의원 마당): 그 안의 나무·바위·무덤을 치워 붉은 칸이 가려지지 않게 한다. 건물(당집·움막)은 남긴다.
# 좌표는 Core/Boss.cs 의 보스 자리와 같다 — 한쪽을 바꾸면 이쪽도 바꿀 것. (x, z, 반지름 m)
BOSS_CLEAR = [(580.0, 521.0, 10.0), (46.0, 453.0, 8.0)]
KEEP = ("prop_ruined_shrine", "prop_quarantine_hut")
before = len(items)
items = [i for i in items if i["t"] or i["n"].startswith(KEEP) or not any(((i["x"] - cx) ** 2 + (i["z"] - cz) ** 2) ** 0.5 < r for cx, cz, r in BOSS_CLEAR)]
print("보스 싸움터에서 치운 물건", before - len(items))
out = {"size": f["grid"]["tiles"][0] * TILE, "tile": TILE, "items": items, "markers": markers, "lights": lights}
with open(os.path.join(res, "Data", "field.json"), "w", encoding="utf-8") as fp:
    json.dump(out, fp, ensure_ascii=False, separators=(",", ":"))

# 적 군집 자리(아트 구역표 field_5x5_zones.json): 데이터에 한 번 굽는다. 인원은 size_hint "중(5~7)" 의 가운데 값
import re
zp = os.path.join(art, "layouts", "field_5x5_zones.json")
camps = []
if os.path.exists(zp):
    zs = json.load(open(zp, encoding="utf-8"))
    for zn in zs["zones"]:
        for c in zn.get("enemy_camps", []):
            nums = [int(v) for v in re.findall(r"\d+", c.get("size_hint", "5"))]
            n = round(sum(nums) / len(nums)) if nums else 5
            camps.append({"x": c["x"], "z": c["y"], "r": c["radius_m"], "n": n, "zone": zn["name"], "theme": zn.get("enemy_theme", "")})
zones_out = []
if os.path.exists(zp):
    for zn in zs["zones"]:
        fg = zn.get("fog") or {}
        r = zn["rect_m"]
        zones_out.append({"name": zn["name"], "x0": r[0], "z0": r[1], "x1": r[2], "z1": r[3],
                          "fog": fg.get("color", "#33405F"), "density": fg.get("density", 0.006)})
with open(os.path.join(res, "Data", "field_camps.json"), "w", encoding="utf-8") as fp:
    json.dump({"camps": camps, "zones": zones_out}, fp, ensure_ascii=False, separators=(",", ":"))
print("군집", len(camps))

# 모델 모으기: 어느 폴더에 있든 이름으로 찾는다(풀밭은 코드가 쓰니 항상 포함)
used.add("terrain_tile_grass")
dst = os.path.join(res, "Models", "Field"); os.makedirs(dst, exist_ok=True)
missing = []
for n in sorted(used):
    src = None
    for sub in ("terrain", "nature", "blackrapids", "hanok", "props", "night"):
        c = os.path.join(art, sub, n + ".glb")
        if os.path.exists(c): src = c; break
    if src: shutil.copyfile(src, os.path.join(dst, n + ".glb"))
    else: missing.append(n)
print("항목", len(items), "마커", len(markers), "불빛", len(lights), "모델", len(used) - len(missing), "없음", missing)
