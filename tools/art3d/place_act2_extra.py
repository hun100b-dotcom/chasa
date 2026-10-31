"""2막 ③④ 마을·들판 생활 소품 배치표(act2_extra.json). place_act2.py의 규칙(길 3m·장소 중심 비움·겹침 검사·땅 높이 붙이기)을 그대로 쓰고,
이미 놓인 422개(act2_layout.json) 위에 '추가로' 놓는다(그래서 별도 파일, 코드팀은 act2_layout.json 옆에 같이 읽으면 된다).
왜 이렇게: 아랫마을에는 집이 한 채도 없고(술독·땔감·울타리뿐) 들판이 거의 비어 있었다. 지도의 장소(술도가·이장 집·약초 아낙 집·벌초꾼 집·국밥집·노새 마구간·주인집…)에 집을 세우고, 들판에는 마른 풀·붉은 바위·고사목·감나무 같은 것을 비탈이 가파르지 않은 곳에 흩는다.
집은 문이 -Y(남쪽)라 장소 점의 북쪽(+y)에 세워 문이 그 점을 보게 한다.
실행: python3 tools/art3d/place_act2_extra.py → assets3d/layouts/act2_extra.json, act2_extra_report.json"""
import os, sys, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import place_act2 as P
R = random.Random(7)
P.RAD.update({"a2v_house_sul": 3.4, "a2v_house_small": 2.6, "a2v_house_herb": 2.4, "a2v_stone_cutter": 2.2, "a2v_persimmon_line": 1.6, "a2v_red_wall_low": 2.0,
              "a2m_soup_house": 3.0, "a2m_mule": 0.9, "a2m_stable": 2.6, "a2m_owner_house": 3.8, "a2m_coal_stack": 1.0, "a2m_dusty_clothes": 1.6, "a2m_pick_rack": 1.1, "a2m_water_barrel": 0.8, "a2m_lamp_string": 2.0,
              "a2f_dry_grass": 0.5, "a2f_red_rock": 1.0, "a2f_thorn_bush": 0.8, "a2f_dead_tree": 0.5, "a2f_boundary_stone": 0.4, "a2f_persimmon_tree": 0.7, "a2f_dry_plot": 2.4, "a2f_cairn_red": 0.5, "a2f_ore_vein_rock": 1.3})
N0 = len(P.PLACED)

def slope(x, y, d=2.0):
    g = [P.ground(x + dx, y + dy) for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d))]; return max(g) - min(g)
def put(name, x, y, rot=0, note="", maxslope=1.2, **kw):
    if slope(x, y) > maxslope or P.ground(x, y) < 0.0: return None      # 가파르거나 물가·구덩이는 피한다
    return P.add(name, x, y, rot, note, **kw)
def scatter_in(name, rc, n, margin=3, maxslope=0.6, note=""):
    got = 0
    for _ in range(n * 8):
        if got >= n: break
        if put(name, R.uniform(rc[0] + margin, rc[2] - margin), R.uniform(rc[1] + margin, rc[3] - margin), R.uniform(0, 360), note, maxslope): got += 1
    return got
def inside(x, y, rc, m=0): return rc[0] + m <= x <= rc[2] - m and rc[1] + m <= y <= rc[3] - m
VIL, MINE, SORT = P.rect("FortressVillage"), P.rect("MinerTown"), P.rect("Sorting")

# ── ③ 붉은재 아랫마을 ──
put("a2v_house_sul", 96, 899, 0, "술도가 집(술독 밭 북쪽, 문이 술도가 뒤뜰을 봄)", 3.0)
put("a2v_house_small", 104, 857, 0, "이장 집"); put("a2v_house_herb", 82, 855, 0, "약초 아낙 집"); put("a2v_house_small", 125, 847, 0, "벌초꾼 집")
put("a2v_stone_cutter", 143, 921, 0, "석수 일터(쌓다 만 성벽 아래)")
for x, y in ((118, 888), (72, 868)): put("a2v_persimmon_line", x, y, R.choice((0, 180)), "곶감 줄")
for k in range(5): put("a2v_house_small", R.uniform(VIL[0] + 8, VIL[2] - 8), R.uniform(VIL[1] + 8, VIL[3] - 10), R.choice((0, 0, 0, 90)), "마을 빈 집 터")
for y in range(808, 920, 5): put("a2v_red_wall_low", 62, y, 90, "마을 서쪽 담")
for x in range(70, 172, 5): put("a2v_red_wall_low", x, 806, 0, "마을 남쪽 담(어귀 가운데는 길이라 비움)")
scatter_in("a2f_persimmon_tree", VIL, 6, 4, 0.8, "마을 감나무"); scatter_in("a2f_dry_grass", VIL, 14, 3, 0.8); scatter_in("a2f_boundary_stone", VIL, 3, 4, 0.8)
# ── ④ 광부촌 ──
put("a2m_soup_house", 462, 882, 0, "국밥집"); put("a2m_stable", 492, 851, 0, "노새 마구간"); put("a2m_mule", 493, 846, 190, "노새 한 마리", force=True)
put("a2m_owner_house", 505, 986, 0, "광산 주인집(쇳골에서 유일한 기와)", 2.5)
for x, y in ((440, 850), (452, 905), (478, 892), (500, 880)): put("a2m_coal_stack", x, y, R.uniform(0, 360), "집 앞 석탄 더미")
for x, y in ((425, 878), (485, 868)): put("a2m_dusty_clothes", x, y, R.choice((0, 180)), "먼지 빨래줄")
for x, y in ((468, 848), (540, 960)): put("a2m_pick_rack", x, y, 0, "곡괭이 걸이")
for x, y in ((474, 832), (469, 840)): put("a2m_water_barrel", x, y, R.uniform(0, 360), "우물가 물통")
for x, y in ((445, 810), (482, 822), (452, 900), (520, 905)): put("a2m_lamp_string", x, y, R.choice((0, 90)), "광부촌 등 줄")
for k in range(4): put("soegol_miner_hut", R.uniform(MINE[0] + 6, MINE[2] - 6), R.uniform(MINE[1] + 8, MINE[3] - 8), R.choice((0, 20, 180)), "광부촌 움막 보강")
for x, y in ((590, 880), (645, 868), (610, 840)): put("a2m_coal_stack", x, y, R.uniform(0, 360), "선탄장 석탄 더미")
put("a2m_water_barrel", 600, 855, 0, "선탄장 물통"); scatter_in("a2f_ore_vein_rock", SORT, 3, 5, 0.8)
# ── 들판: 구역 밖 넓은 땅에 흩는다 ──
FIELD = (4, 644, 764, 1276)
def field(name, n, maxslope=0.5, where=None):
    got = 0
    for _ in range(n * 10):
        if got >= n: break
        x, y = R.uniform(FIELD[0], FIELD[2]), R.uniform(FIELD[1], FIELD[3])
        if where and not where(x, y): continue
        if put(name, x, y, R.uniform(0, 360), "", maxslope): got += 1
    return got
cnt = {}
cnt["dry_grass"] = field("a2f_dry_grass", 260, 0.9); cnt["red_rock"] = field("a2f_red_rock", 70, 1.2); cnt["thorn_bush"] = field("a2f_thorn_bush", 70, 0.9); cnt["dead_tree"] = field("a2f_dead_tree", 45, 1.0)
cnt["boundary_stone"] = field("a2f_boundary_stone", 22, 0.6); cnt["persimmon_tree"] = field("a2f_persimmon_tree", 28, 0.6, lambda x, y: x < 400)       # 감나무는 붉은재(서쪽)
cnt["ore_vein_rock"] = field("a2f_ore_vein_rock", 30, 1.2, lambda x, y: x > 400); cnt["cairn_red"] = field("a2f_cairn_red", 12, 0.8)
cnt["dry_plot"] = sum(1 for cx, cy in ((90, 830), (150, 860), (60, 900), (470, 905), (430, 880)) if put("a2f_dry_plot", cx + R.uniform(-8, 8), cy + R.uniform(-6, 6), R.choice((0, 90)), "마른 밭", 0.6))

mine = [{k: v for k, v in p.items() if k != "r"} for p in P.PLACED[N0:]]
json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "place_act2_extra.py가 만든다. 직접 고치지 말고 스크립트를 고친다. act2_layout.json 옆에 같이 읽는다. z=땅 높이", "props": mine}, open(os.path.join(P.LAY, "act2_extra.json"), "w"), ensure_ascii=False, indent=1)
per = {}
for p in mine: per[p["prop"]] = per.get(p["prop"], 0) + 1
json.dump({"count": len(mine), "dropped": [list(map(lambda v: round(v, 1) if isinstance(v, float) else v, d)) for d in P.DROPPED], "field_counts": cnt, "per_model": per, "moved": sum(1 for p in mine if "walk_snap" in p)}, open(os.path.join(P.LAY, "act2_extra_report.json"), "w"), ensure_ascii=False, indent=1)
print("추가", len(mine), per)
