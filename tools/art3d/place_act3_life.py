"""3막 ⑤ 갯마을 · ⑥ 도성 아랫마을 생활 소품 추가 배치표. 실행: python3 place_act3_life.py → assets3d/layouts/act3_east_extra.json, act3_west_extra.json, act3_extra_report.json
왜 이렇게: act3_east/west_layout.json 은 구역마다 1만 ㎡당 소품이 2~7개로 비어 있었다(난파 여울 2.2, 성문 밖 2.2, 움막촌 5.1, 포구 7.1, 소금밭 6.7).
 place_act3_east.py·place_act3_west.py 의 규칙(길 1.5m+반경 비움·장소 점 비움·겹침 검사·땅 높이 붙이기)을 그대로 쓰고, 이미 놓인 것 위에 '추가로' 놓는다(그래서 별도 파일 — 코드팀은 기존 배치표 옆에 같이 읽는다).
 바닷가 소품(유목·갯풀·조개 더미·갯바위·난파선 뼈대)은 땅 높이가 썰물(-0.5) 안팎인 갯벌·모래턱에만 놓아, 썰물 때 드러나고 밀물 때 잠긴다.
 눈밭 소품은 성문 밖(눈 얼룩 판이 깔린 곳) 둘레에만, 움막촌·저잣 소품은 각 구역 사각형 안에만 놓는다. 소품 배치마다 비탈이 가팔라(>1m/2m) 뜨거나 묻히는 자리는 건너뛴다.
작성: 아트. 직접 고치지 말고 스크립트를 고친다."""
import os, sys, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import place_act3_east as E, place_act3_west as W
R = random.Random(3099)
NEW = {"a3h_fish_rack": 2.4, "a3h_boat_upturned": 2.4, "a3h_rope_post": 0.4, "a3h_crate_stack": 1.0, "a3h_seaweed_line": 0.0, "a3h_clam_basket": 0.5, "a3h_firewood_stack": 1.2, "a3h_tar_barrel": 0.8, "a3h_salt_sack_stack": 1.0, "a3h_salt_yoke": 0.7, "a3h_brine_trough": 1.4, "a3h_salt_shed": 2.6,
       "a3c_driftwood": 1.6, "a3c_barnacle_rock": 1.4, "a3c_seagrass": 0.5, "a3c_crab_pots": 1.0, "a3c_hull_ribs": 2.2, "a3c_shell_heap": 1.0,
       "a3g_snow_dead_tree": 0.6, "a3g_snow_fence": 2.0, "a3g_abandoned_cart": 1.6, "a3g_brazier": 0.7, "a3g_snow_cairn": 0.5, "a3g_straw_bundle": 0.6, "a3g_bare_shrub": 0.5,
       "a3s_laundry_line": 0.0, "a3s_clay_stove": 0.7, "a3s_jar_stand": 1.0, "a3s_rag_tent": 1.8, "a3s_plank_stack": 1.0, "a3s_hen_coop": 0.7,
       "a3k_crates": 1.2, "a3k_cloth_rack": 0.0, "a3k_barrels": 0.9}
for m in (E, W): m.RAD.update(NEW)
def slope(m, x, y, d=2.0):
    g = [m.ground(x + dx, y + dy) for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d))]; return max(g) - min(g)
def put(m, name, x, y, rot=0, note="", lo=-9.0, hi=99.0, maxslope=1.0, **kw):
    """lo~hi: 땅 높이가 이 범위일 때만 놓는다(갯벌 소품은 -0.45~1.2, 마른 땅 소품은 0.1 이상). 파일 경로는 같은 act3 폴더."""
    g = m.ground(x, y)
    if not (lo <= g <= hi) or slope(m, x, y) > maxslope: return None
    return m.add(name, x, y, rot, note, **kw)
def scatter(m, name, rc, n, lo=-9.0, hi=99.0, maxslope=1.0, note="", margin=2, tries=14, where=None):
    got = 0
    for _ in range(n * tries):
        if got >= n: break
        x, y = R.uniform(rc[0] + margin, rc[2] - margin), R.uniform(rc[1] + margin, rc[3] - margin)
        if where and not where(x, y): continue
        if put(m, name, x, y, R.uniform(0, 360), note if got == 0 else "", lo, hi, maxslope): got += 1
    return got
# 모듈마다 add() 가 파일 경로를 act3/<이름>.glb 로 만든다 → 새 소품도 같은 폴더(assets3d/act3/)에 둔다.
CNT = {}
def tally(k, v): CNT[k] = CNT.get(k, 0) + v
nE, nW = len(E.PLACED), len(W.PLACED)

# ═════════ ⑤ 갯마을 ═════════
HARBOR, SALT, SHOAL, CAPE = (960, 360, 1110, 500), (800, 180, 960, 320), (1040, 40, 1200, 180), (1090, 600, 1250, 760)
# 포구: 그물 마당 옆 말림대·미역 줄, 선창 어귀 밧줄 말뚝, 배·궤짝·조개·땔감
for x, y, r in ((1004, 440, 0), (1012, 470, 180), (985, 450, 90)): put(E, "a3h_fish_rack", x, y, r, "생선 말림대(그물 마당 곁)" if x == 1004 else "", 0.1, maxslope=1.5)
for x, y in ((1090, 430), (1085, 470)): put(E, "a3h_boat_upturned", x, y, R.choice((0, 15, 170)), "엎어 둔 배(수리 중)", 0.1, maxslope=1.5)
for x, y in ((1102, 436), (1102, 444), (1096, 452), (1100, 428)): put(E, "a3h_rope_post", x, y, 0, "선창 어귀 밧줄 말뚝" if y == 436 else "", 0.1, maxslope=1.5, force=True) if E.ground(x, y) > 0 else None
put(E, "a3h_seaweed_line", 1060, 445, 0, "미역 줄", 0.1, maxslope=1.5, force=True); put(E, "a3h_seaweed_line", 1040, 495, 20, "미역 줄", 0.1, maxslope=1.5, force=True)
put(E, "a3h_tar_barrel", 1092, 455, 20, "배 칠하는 타르 통(Light_ 하나)", 0.1, maxslope=1.5)
tally("harbor", sum(scatter(E, n, HARBOR, c, 0.1, 3.0, 1.5) for n, c in (("a3h_crate_stack", 6), ("a3h_clam_basket", 5), ("a3h_firewood_stack", 4), ("a3c_seagrass", 10), ("a3c_driftwood", 2))))
# 소금밭: 소금막·가마니·지게·구유(밭 가장자리와 둑 곁)
put(E, "a3h_salt_shed", 845, 308, 0, "소금막(가마솥에 졸이는 곳, Light_ 하나)", 0.1, maxslope=1.5); put(E, "a3h_salt_shed", 935, 200, 0, "소금막", 0.1, maxslope=1.5)
tally("salt", sum(scatter(E, n, SALT, c, 0.1, 3.0, 1.5) for n, c in (("a3h_salt_sack_stack", 7), ("a3h_salt_yoke", 6), ("a3h_brine_trough", 5), ("a3h_firewood_stack", 3), ("a3c_seagrass", 12))))
# 난파 여울: 바닷물이 드나드는 갯벌·모래턱
for x, y, r in ((1120, 90, 20), (1070, 120, 160), (1165, 150, 70)): put(E, "a3c_hull_ribs", x, y, r, "묻힌 난파선 뼈대" if x == 1120 else "", -0.7, 1.4, 2.0)
tally("shoal", sum(scatter(E, n, SHOAL, c, -0.7, 1.4, 1.6) for n, c in (("a3c_driftwood", 8), ("a3c_barnacle_rock", 10), ("a3c_shell_heap", 6), ("a3c_seagrass", 12), ("a3c_crab_pots", 3))))
# 곶·바닷가: 땅 높이 0~1.2 인 둘레(바다에 맞닿은 띠)에 드문드문
tally("cape", sum(scatter(E, n, CAPE, c, 0.0, 1.6, 1.8, margin=1) for n, c in (("a3c_driftwood", 4), ("a3c_barnacle_rock", 6), ("a3c_seagrass", 12), ("a3c_crab_pots", 3), ("a3c_shell_heap", 3))))
shore = lambda x, y: -0.2 <= E.ground(x, y) <= 1.4
tally("shore", sum(scatter(E, n, (790, 20, 1270, 1010), c, -0.2, 1.4, 1.6, margin=6, where=shore, tries=60) for n, c in (("a3c_driftwood", 12), ("a3c_barnacle_rock", 14), ("a3c_seagrass", 40), ("a3c_shell_heap", 6), ("a3c_crab_pots", 4))))

# ═════════ ⑥ 도성 아랫마을 ═════════
GATE, SHACKS, BRIDGE, MARKET = (-560, 140, -440, 290), (-560, 380, -450, 540), (-430, 330, -330, 470), (-330, 370, -150, 520)
# 성문 밖: 화톳불은 문지기 막·주막 곁, 수레는 길가, 고사목·울타리·돌탑은 눈 얼룩 판 둘레
put(W, "a3g_brazier", -541, 244, 0, "문지기 화톳불(Light_ 하나)", 0.0, force=True); put(W, "a3g_brazier", -478, 262, 0, "주막 앞 화톳불", 0.0)
put(W, "a3g_abandoned_cart", -520, 222, 40, "버려진 수레(눈 쌓임)", 0.0); put(W, "a3g_abandoned_cart", -462, 190, 330, "", 0.0)
for y in (190, 200, 210): put(W, "a3g_snow_fence", -535, y + 10, 90, "눈 쌓인 낮은 울타리(성벽 따라)" if y == 190 else "", 0.0)
snow = [(p["x"], p["y"]) for p in W.PLACED if p["prop"] == "snow_patch"]
def near_snow(x, y): return any(math.hypot(x - sx, y - sy) < 9 for sx, sy in snow)
tally("gate", sum(scatter(W, n, GATE, c, 0.0, 99, 1.8, where=near_snow, tries=40) for n, c in (("a3g_snow_dead_tree", 7), ("a3g_snow_cairn", 5), ("a3g_straw_bundle", 6), ("a3g_bare_shrub", 16), ("a3g_snow_fence", 3))))
# 움막촌 + 다리 밑 둔치
for x, y, r in ((-505, 430, 0), (-470, 455, 180), (-520, 505, 20), (-478, 500, 160)): put(W, "a3s_laundry_line", x, y, r, "움막촌 빨래줄" if x == -505 else "", 0.1, maxslope=2.0)
tally("shacks", sum(scatter(W, n, SHACKS, c, 0.1, 99, 1.8) for n, c in (("a3s_clay_stove", 5), ("a3s_jar_stand", 4), ("a3s_rag_tent", 5), ("a3s_plank_stack", 5), ("a3s_hen_coop", 4), ("shack_a", 4), ("shack_b", 3), ("a3g_straw_bundle", 3), ("a3g_bare_shrub", 6))))
tally("bridge", sum(scatter(W, n, BRIDGE, c, 0.1, 99, 1.8) for n, c in (("a3s_rag_tent", 3), ("a3s_plank_stack", 2), ("a3s_laundry_line", 1), ("a3s_clay_stove", 2), ("a3s_jar_stand", 1))))
# 저잣거리: 좌판 뒤 짐과 시렁
tally("market", sum(scatter(W, n, MARKET, c, 0.1, 99, 1.5) for n, c in (("a3k_crates", 8), ("a3k_cloth_rack", 5), ("a3k_barrels", 7), ("a3s_jar_stand", 2))))
# 성벽 안쪽이 아닌 ⑥ 바깥 풀밭·강둑: 마른 떨기·돌탑·짚단을 드문드문(걸어갈 때 텅 비지 않게)
tally("field", sum(scatter(W, n, (-550, 20, -20, 330), c, 0.2, 99, 1.2, margin=8, tries=40) for n, c in (("a3g_bare_shrub", 20), ("a3g_snow_cairn", 4), ("a3g_straw_bundle", 6), ("a3g_snow_dead_tree", 6))))

def dump(m, n0, fname):
    mine = [{k: v for k, v in p.items() if k != "r"} for p in m.PLACED[n0:]]
    json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": f"place_act3_life.py가 만든다. 직접 고치지 말고 스크립트를 고친다. {fname.replace('_extra','_layout')} 옆에 같이 읽는다. z=땅 높이", "props": mine}, open(os.path.join(m.LAY, fname), "w"), ensure_ascii=False, indent=1)
    return mine
e, w = dump(E, nE, "act3_east_extra.json"), dump(W, nW, "act3_west_extra.json")
per = lambda L: {n: sum(1 for p in L if p["prop"] == n) for n in sorted({p["prop"] for p in L})}
json.dump({"east": len(e), "west": len(w), "dropped_east": [list(map(lambda v: round(v, 1) if isinstance(v, float) else v, d)) for d in E.DROPPED[:]], "dropped_west": [list(map(lambda v: round(v, 1) if isinstance(v, float) else v, d)) for d in W.DROPPED[:]],
           "zone_counts": CNT, "moved": sum(1 for p in e + w if "walk_snap" in p), "per_model_east": per(e), "per_model_west": per(w)}, open(os.path.join(E.LAY, "act3_extra_report.json"), "w"), ensure_ascii=False, indent=1)
print("동", len(e), "서", len(w), "구역별", CNT, "옮긴", sum(1 for p in e + w if "walk_snap" in p), "못 놓음", len(E.DROPPED), len(W.DROPPED))
print(per(e)); print(per(w))
