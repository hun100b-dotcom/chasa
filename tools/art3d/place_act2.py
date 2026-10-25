"""2막 배치표 만들기: 산성 아랫마을·무너진 산성·화살골·군막 터·큰 무덤·광부촌·선탄장·큰 갱도(갱도 골)·무너진 막장.
왜 이렇게 하나: 기획 지도(planning/openworld/act2/act2_map.json)의 구역·길·장소를 읽어, 2막 키트(act2_kit.py)와 소품을 땅(terrain_act2) 위에 놓는다.
- 좌표: x=동, y=북(필드 절대). 2막은 x 0~768, y 640~1280. rot = 위에서 볼 때 반시계(Unity yaw = -rot, 1막과 같은 약속).
- z(높이)는 terrain_act2/heightmap.png 에서 읽어 모델 바닥을 땅에 붙인다(평평한 1막과 달리 2막은 언덕·협곡이 있다).
- 길(roads) 가운데 3m 폭, 장소·서낭당·보스 마당 중심은 비워 둔다. 막히면 6m 안의 열린 땅으로 옮기고 walk_snap에 원래 좌표를 남긴다.
- 갱도 골(R2-9)은 지붕 없는 협곡 모듈을 길 따라 이어 붙이고 양옆에 협곡 벽을 세운다(쿼터뷰 카메라가 위에서 길을 볼 수 있게).
실행: python3 tools/art3d/place_act2.py → assets3d/layouts/act2_layout.json, act2_walk_report.json"""
import os, sys, json, math, random
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MAP = "/mnt/project-files/planning/openworld/act2/act2_map.json"
if not os.path.exists(MAP): MAP = os.path.join(ROOT, "assets3d", "layouts", "act2_map.json")  # 기획 파일 복사본(없으면 위 경로 필수)
TER = os.path.join(ROOT, "assets3d", "terrain_act2")
LAY = os.path.join(ROOT, "assets3d", "layouts")
X0, Y0, W, H = 0, 640, 768, 640
HMIN, HMAX = -1.0, 14.0
RNG = random.Random(2025)

M = json.load(open(MAP))
_hm = np.array(Image.open(os.path.join(TER, "heightmap.png")).convert("RGBA")).astype(np.int64)
HGT = ((_hm[..., 0] << 8) | _hm[..., 1]) / 65535.0 * (HMAX - HMIN) + HMIN   # [행(남→북), 열(서→동)]

def ground(x, y):
    """(x,y) 땅 높이(m). 칸 사이는 이웃 칸을 섞어 부드럽게."""
    fx = min(max(x - X0, 0), W - 1e-6); fy = min(max(y - Y0, 0), H - 1e-6)
    i, j = int(fx), int(fy); tx, ty = fx - i, fy - j
    a = HGT[j, i] * (1 - tx) + HGT[j, i + 1] * tx; b = HGT[j + 1, i] * (1 - tx) + HGT[j + 1, i + 1] * tx
    return float(a * (1 - ty) + b * ty)

# 충돌 반지름(m): 걸어 다닐 때 비켜 가야 하는 크기. 키트 크기표 기준(큰 변의 절반 안팎).
RAD = {"sanseong_wall_straight": 2.0, "sanseong_wall_ruin": 2.0, "sanseong_wall_unfinished": 2.0, "sanseong_gate": 3.0, "sanseong_tower": 2.0,
       "sanseong_palisade": 1.6, "sanseong_banner_torn": 0.5, "sanseong_big_mound": 3.5, "sanseong_arrow_field": 0.8, "sanseong_arrow_rock": 2.0,
       "sanseong_spear_rack": 1.0, "sanseong_tent": 2.2, "sanseong_sul_vat": 1.0, "sanseong_stairs": 1.5, "sanseong_beacon": 1.2, "sanseong_shrine": 2.2,
       "sanseong_wipae": 0.3, "sanseong_jinbeop_map": 0.9, "sanseong_flag_shard": 0.4, "sanseong_geumjul_jangseung_pair": 1.8,
       "soegol_mine_entrance": 4.0, "soegol_timber_frame": 1.2, "soegol_rail": 0.5, "soegol_cart": 0.8, "soegol_ore_pile": 1.0, "soegol_slag_heap": 2.0,
       "soegol_windlass": 1.2, "soegol_miner_hut": 1.8, "soegol_lantern_post": 0.4, "soegol_ore_basket": 0.5, "soegol_wash_flume": 2.0,
       "soegol_smelter": 2.0, "soegol_ingot_stack": 0.8, "soegol_rope_fence": 1.6, "soegol_scree": 1.5, "soegol_mokpae_board": 1.4,
       "soegol_sorting_bench": 1.4, "soegol_chalk_rock": 1.6, "soegol_canyon_wall": 3.0, "soegol_gol_module": 0.0}   # 갱도 골 바닥 모듈은 걷는 곳이라 0

def folder(name): return "props" if name.startswith("prop_") else "act2"

def road_pts():
    """길 꺾은선을 1m 간격 점으로 쪼갠다(거리 검사용)."""
    out = []
    for r in M["roads"]:
        P = r["points"]
        for a, b in zip(P[:-1], P[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
            for k in range(n): out.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n, r["id"]))
        out.append((P[-1][0], P[-1][1], r["id"]))
    return out
ROADS = road_pts()
SKIP_ROAD = {"R2-9", "R2-12"}      # 갱도 골은 모듈이 길 자체라서 거리 검사에서 뺀다

def keep_points():
    """비워 둘 점: 장소·서낭당·보스 마당 중심·장례 물건. (이름, x, y, 비울 반지름)"""
    k = []
    for n, p in M["places"].items(): k.append((n, p["x"], p["y"], 1.6))
    for s in M["shrines"]: k.append((s["name"], s["x"], s["y"], 3.0))
    for b in M["boss_arenas"]: k.append((b["name"], b["x"], b["y"], b["radius_m"] * 0.55))
    return k
KEEP = keep_points()

PLACED = []
def clear_ok(name, x, y, by_design=False):
    """이 자리에 놓아도 걷기·장면이 막히지 않나. 길 3m·장소 비움·이미 놓은 소품과 겹침을 본다."""
    r = RAD.get(name, 1.0)
    if r <= 0 or by_design: return True
    for rx, ry, rid in ROADS:
        if rid in SKIP_ROAD: continue
        if math.hypot(rx - x, ry - y) < r + 1.5: return False
    for n, kx, ky, kr in KEEP:
        if math.hypot(kx - x, ky - y) < r + kr: return False
    for q in PLACED:
        if q["r"] > 0 and math.hypot(q["x"] - x, q["y"] - y) < (r + q["r"]) * 0.8: return False
    return True

def snap(name, x, y, rad=6.0):
    if clear_ok(name, x, y): return x, y
    best = None
    for k in range(1, int(rad / 0.5) + 1):
        for a in range(0, 360, 20):
            nx, ny = x + k * 0.5 * math.cos(math.radians(a)), y + k * 0.5 * math.sin(math.radians(a))
            if clear_ok(name, nx, ny): return round(nx, 2), round(ny, 2)
    return None

def add(name, x, y, rot=0, note="", force=False, sink=0.0):
    """소품 하나 놓기. force=True 는 설계상 길·장소 위(문·갱 입구·금줄 등)."""
    if not (X0 + 2 <= x <= X0 + W - 2 and Y0 + 2 <= y <= Y0 + H - 2): return None
    sn = (x, y) if (force or clear_ok(name, x, y)) else snap(name, x, y)
    if sn is None: DROPPED.append((name, x, y)); return None
    p = {"prop": name, "file": f"assets3d/{folder(name)}/{name}.glb", "x": round(sn[0], 2), "y": round(sn[1], 2), "rot": int(rot) % 360,
         "z": round(ground(sn[0], sn[1]) - sink, 2), "r": RAD.get(name, 1.0)}
    if note: p["note"] = note
    if (sn[0], sn[1]) != (x, y): p["walk_snap"] = {"from": [x, y], "to": [round(sn[0], 2), round(sn[1], 2)]}
    if force: p["by_design"] = True
    PLACED.append(p); return p
DROPPED = []

def rect(code): return next(z["rect_m"] for z in M["zones"] if z["code"] == code)
def scatter(name, rc, n, margin=4, rot_rand=True, note=""):
    x0, y0, x1, y1 = rc
    got = 0
    for _ in range(n * 6):
        if got >= n: break
        if add(name, RNG.uniform(x0 + margin, x1 - margin), RNG.uniform(y0 + margin, y1 - margin), RNG.uniform(0, 360) if rot_rand else 0, note): got += 1
def line(name, a, b, step, rot=None, note="", jitter=0.0, force=False):
    d = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(d / step))
    ang = math.degrees(math.atan2(-(b[0] - a[0]), (b[1] - a[1]))) if rot is None else rot   # +Y 축을 선 방향으로
    for k in range(n + 1):
        t = k / n
        add(name, a[0] + (b[0] - a[0]) * t + RNG.uniform(-jitter, jitter), a[1] + (b[1] - a[1]) * t + RNG.uniform(-jitter, jitter), ang, note, force)

def build():
    PLACED.clear(); DROPPED.clear()
    # ── ③ 산성 아랫마을 (60,800)-(175,925): 술도가, 사당, 쌓다 만 성벽 ──
    add("sanseong_geumjul_jangseung_pair", 101, 668, 0, "R2-1 2막 금줄(1막 마지막 일 뒤 풀림)", force=True)
    add("sanseong_geumjul_jangseung_pair", 441, 648, 0, "R2-2 2막 금줄", force=True)
    add("sanseong_shrine", 112, 793, 0, "SH2-1 붉은재 서낭당 자리 장식(서낭당 규칙 원은 코드)", force=True)
    for x, y in [(86, 884), (92, 887), (88, 891), (95, 889), (84, 879), (97, 892)]: add("sanseong_sul_vat", x, y, RNG.uniform(0, 360), "술도가 뒤뜰 술독 무리 B05-D1")
    line("sanseong_wall_unfinished", (140, 915), (160, 917), 4.0, 90, "S-051 석수가 쌓다 만 성벽")
    add("sanseong_wipae", 132.5, 902, 0, "마을 사당 위패 '장군지위'", force=True)
    scatter("prop_firewood", rect("FortressVillage"), 4, 6); scatter("prop_fence", rect("FortressVillage"), 5, 6)
    # ── 무너진 산성 (70,950)-(185,1070): 문·성벽·망루, 성마당(125,1018) r16 은 비운다 ──
    add("sanseong_gate", 118, 944, 0, "산성 문(성 문 앞 서낭당 SH2-3은 B-06 천도 뒤 열림)", force=True)
    add("sanseong_stairs", 114, 975, 0, "R2-3 갈지자 돌계단"); add("sanseong_stairs", 120, 992, 0)
    line("sanseong_wall_straight", (74, 952), (112, 952), 4.0, 90, "산성 남벽 왼쪽"); line("sanseong_wall_straight", (126, 952), (182, 952), 4.0, 90, "산성 남벽 오른쪽")
    line("sanseong_wall_ruin", (74, 1062), (180, 1062), 6.0, 90, "무너진 북벽")
    for y in range(962, 1062, 8):
        add("sanseong_wall_ruin", 76, y, 0); add("sanseong_wall_straight" if y % 16 else "sanseong_wall_ruin", 180, y, 0)
    add("sanseong_tower", 78, 950, 0); add("sanseong_tower", 182, 950, 0); add("sanseong_tower", 182, 1064, 0, "산성 위"); add("sanseong_beacon", 160, 1040, 0, "봉화대 터")
    add("sanseong_banner_torn", 125, 1018, 0, "B-05 깃대 터 찢긴 깃발", force=True)
    for k in range(5): add("sanseong_flag_shard", 125 + 5.5 * math.cos(k * 1.26), 1018 + 5.5 * math.sin(k * 1.26), RNG.uniform(0, 360), "깃대 조각(깃발 꽂기 반경 6m)", force=True)
    # ── 화살골 (200,900)-(310,1025): 바위틈 화살 ──
    for x, y in [(212, 935), (228, 948), (236, 968), (270, 984), (292, 1008), (300, 992)]: add("sanseong_arrow_rock", x, y, RNG.uniform(0, 360), "양옆 벼랑 바위")
    add("sanseong_arrow_rock", 262, 972, 0, "B05-D3 만져 보기: 바위틈 화살촉", force=True)
    scatter("sanseong_arrow_field", rect("ArrowValley"), 14, 6); scatter("soegol_scree", rect("ArrowValley"), 6, 8)
    # ── 군막 터 (190,1085)-(305,1190): 천막 기둥 자리, 진법도, 창꽂이 ──
    for x, y in [(210, 1110), (225, 1150), (270, 1105), (285, 1150), (214, 1175), (280, 1176)]: add("sanseong_tent", x, y, RNG.uniform(-20, 20), "천막 터")
    for x, y in [(210, 1135), (280, 1128), (236, 1162), (258, 1163)]: add("sanseong_spear_rack", x, y, RNG.uniform(0, 360))
    add("sanseong_jinbeop_map", 232, 1124, 0, "진법도(B-06 단서)"); add("sanseong_palisade", 195, 1100, 90); add("sanseong_palisade", 195, 1112, 90)
    line("sanseong_palisade", (192, 1186), (300, 1186), 3.2, 0, "군막 북쪽 목책")
    # ── 큰 무덤 (40,1130)-(145,1240) ──
    add("sanseong_big_mound", 90, 1190, 0, "비석 없는 큰 봉분", force=True)
    for x, y in [(55, 1200), (62, 1212), (70, 1198), (48, 1215), (60, 1185), (110, 1215), (120, 1200)]: add("prop_grave", x, y, RNG.uniform(-15, 15), "작은 무덤 떼")
    scatter("prop_dolddam", rect("BigTomb"), 4, 6)
    # ── ④ 광부촌 (410,800)-(545,925) ──
    add("sanseong_shrine", 455, 793, 0, "SH2-2 산신각(서낭당 규칙 원은 코드)", force=True)
    for x, y, r in [(432, 862, 0), (445, 890, 20), (462, 875, 180), (470, 905, 10), (432, 835, 0), (480, 860, 90), (492, 842, 0)]: add("soegol_miner_hut", x, y, r)
    add("soegol_mokpae_board", 520, 935, 0, "목패 걸이 판(2막 꿀팁: 이름 목패)", force=True)
    add("soegol_windlass", 490, 920, 0); add("soegol_lantern_post", 458, 800, 0); add("soegol_lantern_post", 470, 836, 0); add("soegol_lantern_post", 520, 925, 0)
    add("soegol_ore_basket", 466, 840, 0); add("soegol_ore_basket", 505, 915, 40)
    # 광산 주인집 앞마당(505,952) r14: 담 대신 밧줄 울타리로 폭 가로 띠를 연다
    line("soegol_rope_fence", (493, 940), (518, 940), 3.2, 0, "주인집 앞마당 가장자리", force=False)
    # ── 선탄장 (565,825)-(665,915) ──
    for x, y, r in [(612, 872, 0), (600, 860, 0), (622, 885, 90), (590, 888, 0)]: add("soegol_sorting_bench", x, y, r, "선탄 평상" if (x, y) == (612, 872) else "")
    for x, y in [(640, 845), (650, 865), (575, 905), (655, 900), (630, 835)]: add("soegol_slag_heap", x, y, RNG.uniform(0, 360), "슬래그 무더기")
    add("soegol_cart", 585, 878, 70); add("soegol_cart", 645, 880, 100); add("soegol_smelter", 650, 830, 0, "제련로")
    add("soegol_wash_flume", 604, 845, 0); add("soegol_ingot_stack", 592, 855, 0); add("soegol_ore_pile", 628, 862, 0); add("soegol_ore_pile", 575, 870, 0)
    line("soegol_rail", (545, 870), (612, 870), 3.0, 90, "R2-8 선탄장 길 레일", force=True)
    # ── 갱 입구·갱 오르막 R2-7 ──
    add("soegol_mine_entrance", 560, 984, 215, "갱 입구(큰 갱도 시작)", force=True); add("soegol_timber_frame", 552, 976, 0); add("soegol_timber_frame", 570, 992, 0)
    add("sanseong_wipae", 552, 985, 0, "갱 입구 산신 돌(S-083)", force=True)
    line("soegol_rail", (500, 925), (560, 980), 3.0, None, "R2-7 레일", force=True)
    # ── 갱도 골 R2-9: 협곡 모듈을 길 따라 이어붙이고 양옆 벽 ──
    P = [r for r in M["roads"] if r["id"] == "R2-9"][0]["points"]
    seg = []
    for a, b in zip(P[:-1], P[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, round(d / 7.0))
        for k in range(n): seg.append(((a[0] + (b[0] - a[0]) * (k + .5) / n, a[1] + (b[1] - a[1]) * (k + .5) / n), math.degrees(math.atan2(-(b[0] - a[0]), (b[1] - a[1])))))
    for (x, y), ang in seg:
        add("soegol_gol_module", x, y, ang, "갱도 골 바닥(지붕 없음)", force=True)
        nx, ny = -math.cos(math.radians(ang)) * -1, 0
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for side in (-1, 1):       # 길 오른쪽/왼쪽 수직 방향(+X 축을 회전한 것)
            add("soegol_canyon_wall", x + side * 4.6 * ca, y + side * 4.6 * sa, ang + (0 if side > 0 else 180), "갱도 골 벽", force=True)
    for (x, y), ang in seg[1::2]: add("soegol_timber_frame", x, y, ang + 90, "버팀목 아치(카메라 가림 없게 낮은 틀)", force=True)
    add("soegol_rail", 640, 1090, 30, "갱도 골 레일", force=True); add("soegol_lantern_post", 640, 1086, 0)
    # ── 무너진 막장 (665,1150)-(750,1235): 분필 바위, 낙반, B-07 마당(705,1192) r14 ──
    add("soegol_chalk_rock", 690, 1170, 0, "막장 입구 분필 '13 나감'", force=True)
    for x, y in [(715, 1170), (730, 1200), (688, 1210), (720, 1222), (738, 1182)]: add("soegol_scree", x, y, RNG.uniform(0, 360), "낙반")
    add("soegol_timber_frame", 700, 1205, 90, "칠성 마당 버팀목")
build()

def main():
    # 열린 땅 점검: 놓은 소품의 충돌 원이 길(R2-9 제외)·장소 점에 닿는지
    bad = []
    for p in PLACED:
        if p.get("by_design") or p["r"] <= 0: continue
        for n, kx, ky, kr in KEEP:
            if math.hypot(kx - p["x"], ky - p["y"]) < p["r"] + kr - 0.01: bad.append((p["prop"], p["x"], p["y"], n))
        for rx, ry, rid in ROADS:
            if rid in SKIP_ROAD: continue
            if math.hypot(rx - p["x"], ry - p["y"]) < p["r"] + 1.49: bad.append((p["prop"], p["x"], p["y"], rid)); break
    out = [{k: v for k, v in p.items() if k != "r"} for p in PLACED]
    json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "place_act2.py가 만든다. 직접 고치지 말고 스크립트를 고친다. z=땅 높이(terrain_act2)", "props": out},
              open(os.path.join(LAY, "act2_layout.json"), "w"), ensure_ascii=False, indent=1)
    rep = {"count": len(out), "dropped_no_open_ground": [list(map(lambda v: round(v, 1) if isinstance(v, float) else v, d)) for d in DROPPED],
           "overlaps": bad, "moved": [p for p in out if "walk_snap" in p],
           "per_model": {n: sum(1 for p in out if p["prop"] == n) for n in sorted({p["prop"] for p in out})}}
    json.dump(rep, open(os.path.join(LAY, "act2_walk_report.json"), "w"), ensure_ascii=False, indent=1)
    print("놓은 소품", len(out), "| 옮긴 것", len(rep["moved"]), "| 놓지 못한 것", len(DROPPED), "| 겹침", len(bad))
    for d in DROPPED[:12]: print("  못 놓음", d)
    for b in bad[:12]: print("  겹침", b)
if __name__ == "__main__": main()
