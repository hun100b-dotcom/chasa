"""시즌 3 아래층 보스 마당 11곳(B-21~B-31). 실행: python3 s3_arenas.py [id ...]
아래층은 위층 지형을 다시 쓰고 조명·색만 바꾼다(SCENARIO-MASTER §S-1). 그래서 땅을 새로 파지 않고, 보스 마당마다 '평평한 판 + 낮은 가장자리 + 마당 장치' 하나를 얹는 방식으로 만든다.
 · 판(floor): 윗면 높이 0, 반경 R(기획 s3-bosses-draft 표). 아래로 0.6m 치마가 둘러 있어 위층 지형이 울퉁불퉁해도 틈이 보이지 않는다. 코드는 마당 중심의 위층 지형 높이에 놓으면 된다.
 · 가장자리(rim): 쿼터뷰 가림 방지로 북쪽(+Y)은 1.2m 이하, 남쪽(-Y, 카메라 쪽)은 절반 높이(기획 규칙). 마당 안에는 1.5m 넘는 것을 두지 않는다(B-25 버팀목 2.6m만 예외).
 · 보스 모델이 이미 자기 Prop(뒤집힌 배, 광부 열둘 등)을 갖고 있어 마당과 겹치지 않게 나눴다: 마당=땅·가장자리·바깥 소품, 보스=약점 소품.
 · 이벤트 소품(눕히기/깨뜨리기 뒤 놓는 것)은 마당 파일에 넣지 않고 s3_arenas.json의 events에 kit 이름과 자리만 적었다(코드가 때맞춰 놓는다).
출력: assets3d/s3/s3_arena_bXX.glb, assets3d/layouts/s3_arenas.json(자리·반경·장치 수치), 미리보기 previews/s3_arenas_50deg.png."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import s3_kit as K
OUT = K.OUT
def rim(R, n, gap, hn, hs, col, col2, r, tag):
    """가장자리: n개 둥근 바위/흙둑을 R 둘레에 놓는다. 북쪽(+Y)=hn, 남쪽(-Y)=hs 높이. gap=[(각도,폭)]은 출입구로 비운다."""
    out = []
    for i in range(n):
        a = i / n * math.tau; 
        if any(abs((a - g0 + math.pi) % math.tau - math.pi) < w for g0, w in gap): continue
        h = hs if math.sin(a) < -0.2 else hn; h *= r.uniform(0.8, 1.15)
        out.append(sphere(f"{tag}{i}", r.uniform(1.0, 1.6), (math.cos(a) * (R + 0.8), math.sin(a) * (R + 0.8), h * 0.2), col if i % 2 else col2, 6, 4, (1.2, 1.0, h / 1.4)))
    return out
# 마당 정의: id, boss, 월드 중심(x,y), 반경, 바닥색, 가장자리(개수, 북높이, 남높이, 색1, 색2), 출입구 각도, 소품[(kit,x,y,rot)], 이벤트, 조명, 장치 수치
ARENAS = [
 dict(id="b21", boss="B-21 윤 영감의 백", at=(404, 288), R=16, floor="#2E3A3E", rim=(18, 1.2, 0.5, "#3A3228", "#2A241C"), gap=[(math.pi * 1.5, 0.35)], note="소 밑 바닥. 1막 B-01 나루 영감 자리 바로 아래. 물 차오름 신호(배 판자 +10초)",
      props=[("mud_pool", -6, 5, 0), ("mud_pool", 5, -5, 0.4), ("mud_pool", -2, -8, 1.0), ("lying_shadow_pair", 8, 4, 1.2), ("lying_shadow", -9, -2, 0.6), ("name_tag_thread", 4, 6, 0), ("name_tag_thread", -5, -3, 0)],
      events=[("on_lay", "barley_sheaf", 0, 0, 0)], mech=dict(water_steps_s=20, fail_s=90, boat_sweep_width_m=4.0)),
 dict(id="b22", boss="B-22 줄에 묶인 일곱", at=(1215, 690), R=15, floor="#2A3030", rim=(14, 1.2, 0.5, "#2E3236", "#24282C"), gap=[(math.pi * 1.5, 0.4)], note="바다굴 안쪽 바위 마당. 썰물 밤(8분 이상)에만 연다. 입구 (1190,660)",
      props=[("sea_cave_rock", -11, 4, 0.5), ("sea_cave_rock", 11, 6, 2.5), ("sea_cave_rock", 0, 12, 1.5), ("wreck_ribs", -17, 0, 1.57), ("wreck_ribs", 17, 4, -1.57), ("mud_pool", 0, -9, 0)],
      events=[], mech=dict(circle_radius_m=6, seven_in_s=15, tide_win_s=20)),
 dict(id="b23", boss="B-23 물 밑 매듭", at=(500, 262), R=20, floor="#2E3C44", rim=(20, 1.0, 0.4, "#3A4A4E", "#2A363A"), gap=[], note="닻 여울(물이 빠져도 무릎 깊이). 원 반경 20→16(안쪽 실을 먼저 건드릴 때 1회). 위치는 기획 제안이라 지도 확정 시 옮겨도 됨",
      props=[("hanging_threads", 10, 12, 0), ("hanging_threads", -12, 8, 0), ("hanging_threads", 14, -6, 0), ("hanging_threads", -8, -13, 0), ("name_tag_thread", 6, 7, 0), ("name_tag_thread", -7, 5, 0), ("name_tag_thread", 8, -7, 0), ("name_tag_thread", -9, -6, 0), ("lying_shadow", 13, 2, 0.8), ("lying_shadow", -14, -2, 2.2), ("lying_shadow", 3, 14, 4.0), ("lying_shadow", -2, -15, 1.0)],
      events=[("on_phase3", "capsized_boat", 0, 0, 0.3)], mech=dict(outer_threads=24, shrink_to_m=16, hold_s=3, hold_times=2)),
 dict(id="b24", boss="B-24 한 구덩이의 두 진", at=(90, 1185), R=18, floor="#3A3228", rim=(0, 0, 0, "#3E382E", "#352E26"), gap=[], note="봉분 한가운데 빈 굴. 바닥이 가운데에서 둘로 갈라진다(갈라진 틈은 장식, 걸을 수 있음)",
      props=[("tomb_wall", 0, 21, 3.14), ("tomb_wall", 16, 14, 3.9), ("tomb_wall", -16, 14, 2.4), ("tomb_wall", 20, -4, 4.7), ("tomb_wall", -20, -4, 1.6), ("lying_shadow", -8, 9, 1.57), ("lying_shadow", -8, 7, 1.57), ("lying_shadow", 8, 9, 1.57), ("lying_shadow", 8, 7, 1.57), ("lying_shadow", -11, -6, 0.2), ("lying_shadow", 11, -6, -0.2)],
      events=[("on_lay", "fallen_standards", 0, 0, 0)], mech=dict(charge_period_s=6, charge_band_m=3, formation_radius_m=7, split_floor=True), split=True),
 dict(id="b25", boss="B-25 반장 칠성의 백", at=(705, 1192), R=12, floor="#3A3228", rim=(0, 0, 0, "#3E382E", "#352E26"), gap=[], note="막장 안쪽, 쌓인 돌 앞. 원 반경 12→9m(30초마다 1m). 버팀목 셋은 보스 모델이 갖고 있다",
      props=[("rubble_pile", 0, 14, 0), ("rubble_pile", -6, 13, 0.4), ("rubble_pile", 6, 13, -0.4), ("rusty_cart", -9, -2, 0.3), ("rusty_cart", 10, -3, 2.9), ("mine_beam_broken", 11, 6, 0.5), ("lying_shadow", -9, 7, 1.0), ("lying_shadow", 9, 8, -0.8)],
      events=[("on_phase2", "mine_beam", 0, 0, 0)], mech=dict(radius_start_m=12, radius_min_m=9, shrink_every_s=30, hold_ring_m=2.0, beams=3, beam_hold_s=20)),
 dict(id="b26", boss="B-26 역병 마흔과 마흔", at=(110, 500), R=16, floor="#6A6858", rim=(16, 1.2, 0.5, "#4A4234", "#3A3228"), gap=[], note="석회 구덩이 한가운데(흰 가루에 발자국이 남는다). 위치는 1막 무덤골 흑월 1차 자리 아래 — 좌표 미확정, 임시 제안",
      props=[("lime_band", 0, 5, 0), ("lime_band", 0, -5, 0), ("fallen_medicine_chest", 12, 6, 2.0), ("lying_shadow_pair", -9, 6, 0.4), ("lying_shadow_pair", 8, -8, 1.9)],
      events=[("on_lay", "blank_stones_row", 0, 0, 0)], mech=dict(fog_radius_m=4, fog_count=2, slow=0.2, lower_layer_pull_s=10)),
 dict(id="b27", boss="B-27 서생 이명의 백", at=(-500, 185), R=18, floor="#2E2A26", rim=(18, 1.2, 0.5, "#3A3228", "#2A241C"), gap=[], note="성문 밖 구덩이 가장 오래된 겹(바닥이 온통 글씨). 성문 그림자가 120초에 걸쳐 반경 100→50%",
      props=[("floor_strokes", 0, 0, 0), ("floor_strokes", 8, 6, 0.8), ("floor_strokes", -8, 6, 2.1), ("floor_strokes", 7, -7, 1.3), ("floor_strokes", -9, -6, 0.3), ("unmarked_mound", -12, 8, 0), ("unmarked_mound", 13, 9, 0), ("bridge_footing", 0, 19, 0)],
      events=[("on_break", "ink_silt_islet", 0, 0, 0)], mech=dict(shadow_s=120, shadow_to=0.5, frozen_dps_pct=2, scribe_pose="붓끝이 떨린다")),
 dict(id="b28", boss="B-28 벼루 밑의 손", at=(880, 700), R=14, floor="#1E1C24", rim=(16, 1.0, 0.45, "#14121A", "#1E1C24"), gap=[], note="먹 앙금 한가운데. 머리 위 벼루 바닥(보스 모델 Prop, 속 빈 틀)이 천장처럼 돈다. 이동 −15%",
      props=[("ink_silt_islet", -7, 5, 0), ("ink_silt_islet", 8, -4, 0.7), ("ink_silt_islet", 2, 8, 1.4), ("quarters_bunk", -12, 6, 0.5), ("quarters_bunk", 12, 6, -0.4)],
      events=[("on_phase2", "ink_silt_islet", 0, 0, 0)], mech=dict(rain_period_s=4, rain_count=4, rain_radius_m=2, powder_pools_max=8, ceiling_stop_s=3)),
 dict(id="b29", boss="B-29 사잣밥 할미의 백", at=(380, 880), R=10, floor="#3A322A", rim=(0, 0, 0, "#3A3228", "#2E2820"), gap=[], note="빈 고을 맨 끝 집 방 안(구들이 반쯤 내려앉음). 지붕 없음, 남쪽 벽 반 높이. 구들 9칸 3×3(2m), 중 3칸이 뜨거워진다. 위치는 기획 제안(북쪽 끝)",
      props=[(f"ondol_tile", (c % 3 - 1) * 2.0, (c // 3 - 1) * 2.0, 0) for c in range(9)] + [("offering_set", -5, 7, 0), ("offering_set", 5, 7, 0.1), ("lying_shadow", -4, 5, 0.3), ("lying_shadow", 4, 5, -0.3), ("quarters_bunk", 0, 10, 0)],
      events=[("on_phase2", "ondol_hot_tile", 0, 0, 0)], mech=dict(grid="3x3", cell_m=2.0, hot_cells=3, hot_swap_s=8, hot_dps_pct=4, table_stand_s=3, regen_pause_s=15)),
 dict(id="b30", boss="B-30 첫 우물 — 어미의 백", at=(380, -320), R=14, floor="#2E3C44", rim=(0, 0, 0, "#3A3834", "#2E2C28"), gap=[], note="우물 밑 원형 무대(벽을 따라 물이 오르내림, 주기 8초 = 오름 3 + 내림 5). 바깥 고리 9~14m가 물에 잠긴다",
      props=[("well_wall", 0, 15, 3.14), ("well_wall", 13, 8, 3.9), ("well_wall", -13, 8, 2.4), ("well_wall", 15, -6, 4.7), ("well_wall", -15, -6, 1.6), ("well_wall", 0, -16, 0), ("well_rope", 0, 0, 0), ("lying_shadow", 6, 4, 1.0), ("lying_shadow", -6, 4, -1.0), ("lying_shadow", 5, -6, 2.0), ("lying_shadow", -5, -6, 4.0)],
      events=[("on_phase3", "dawn_flood_line", 0, -12, 0)], mech=dict(wave_period_s=8, wave_up_s=3, wave_down_s=5, wave_ring_m=[9, 14], rope_hold_s=3, rope_holds=3, rope_window_s=5)),
 dict(id="b31", boss="B-31 나의 백", at=(404, 288), R=16, floor="#1E2A30", rim=(18, 1.2, 0.5, "#14121A", "#1E1C24"), gap=[], note="물막이 골 소 가장 깊은 곳 — 물속에서 타는 횃불 하나(B-21 자리 바로 더 아래). 사슬 길이 8m에 묶인다. 8막 끝 전까지 닫혀 있다",
      props=[("torch_in_water", 0, 11, 0), ("barley_sheaf", -6, -8, 0), ("mud_pool", 7, 5, 0), ("mud_pool", -8, 4, 1.0), ("lying_shadow", 10, -3, 0.5), ("lying_shadow", -11, -5, 2.0)],
      events=[("on_phase3", "name_tag_thread", 0, 0, 0)], mech=dict(chain_len_m=8.0, push_period_s=4, push_m=3, lights_per_40=1, lights_max=7, push_cut_per_light=0.12)),
]
def build_arena(a):
    r = random.Random(hash(a["id"]) & 0xFFFF); R = a["R"]; parts = []
    parts += [cyl("floor", R + 0.4, R + 0.4, 0.4, (0, 0, -0.4), a["floor"], 28), cyl("skirt", R + 1.4, R + 2.2, 0.6, (0, 0, -1.0), "#2A241C", 24)]   # 윗면 높이 0, 아래 치마
    if a.get("split"): parts += [box("crack", (0.5, R * 2, 0.02), (0, 0, 0.0), "#14100C"), box("crack_edge", (1.1, R * 2, 0.012), (0, 0, 0.0), "#2A241C")]
    n, hn, hs, c1, c2 = a["rim"]
    if n: parts += rim(R, n, a["gap"], hn, hs, c1, c2, r, "rim")
    for k, x, y, rot in a["props"]:
        for i, o in enumerate(dict(K.KIT)[k]()):
            lx, ly = o.location.x, o.location.y; c, s_ = math.cos(rot), math.sin(rot)
            o.location.x = x + lx * c - ly * s_; o.location.y = y + lx * s_ + ly * c; o.rotation_euler.z += rot      # 소품 원점을 기준으로 부품 위치를 함께 돌린다
            parts.append(o)
    return parts
if __name__ == "__main__":
    want = sys.argv[1:]; res = []; reg = []
    os.makedirs(os.path.join(OUT, "s3"), exist_ok=True)
    for a in ARENAS:
        if want and a["id"] not in want: continue
        reset(); parts = build_arena(a); o = join("s3_arena_" + a["id"], parts); lo, hi = bounds(o)
        export(o, os.path.join(OUT, "s3", f"s3_arena_{a['id']}.glb"))
        res.append({"id": a["id"], "tris": tris(o), "size_m": [round(hi.x - lo.x, 1), round(hi.y - lo.y, 1), round(hi.z - lo.z, 1)]})
        reg.append({k: a[k] for k in ("id", "boss", "at", "R", "note", "mech")} | {"file": f"s3/s3_arena_{a['id']}.glb", "floor_top_y": 0.0, "place_y_offset_m": 0.02, "events": [{"when": w, "prop": f"s3_{k}", "x": x, "y": y, "rot": rot} for w, k, x, y, rot in a["events"]]})
        print(res[-1])
    if not want:
        json.dump({"_설명": "시즌3 아래층 보스 마당 11곳. at=월드 중심(x,y)이고 마당은 위층 지형 높이에 얹는다(floor_top_y=0은 파일 안 높이. 지형과 윗면이 같은 높이면 면이 깜빡이므로 place_y_offset_m=0.02만큼 올려 놓을 것). 마당 파일은 평평한 판+낮은 가장자리+바깥 소품, 이벤트 소품은 events에 때와 자리만. mech=기획 수치 그대로(코드가 읽을 값).", "arenas": reg}, open(os.path.join(OUT, "layouts", "s3_arenas.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        for i, a in enumerate(ARENAS): o = join(a["id"], build_arena(a)); o.location = ((i % 4 - 1.5) * 52.0, -(i // 4) * 52.0, 0.03)    # 미리보기 바닥판과 겹쳐 깜빡이는 것(z-fighting)을 피해 3cm 띄움
        setup_render(215, (0, -62.0, 1.0), elev=50, size=(1600, 1000), ground_size=400); bpy.context.scene.cycles.samples = 24
        render(os.path.join(OUT, "previews", "s3_arenas_50deg.png"))
