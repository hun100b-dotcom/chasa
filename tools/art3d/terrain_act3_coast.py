"""3막 해안 길 띠 땅 만들기(벼랑 아래 해안). 실행: python3 terrain_act3_coast.py → assets3d/terrain_act3_coast/, 배치 assets3d/layouts/act3_coast_layout.json
기획 답(2026-10-25): 1막 땅은 그대로(가장자리 0.3 m). 가장자리에서 남쪽 3~4 m 사이를 급경사로 깎아 해안 길 바닥을 −6.5 m 로 하고, 바다 수면은 썰물 −7.5 m, 밀물 −6.0 m(밀물에 갯골 셋이 잠김). 1막·⑥ 쪽 가장자리에는 0.8 m 돌담을 둔다.
땅: 월드 x −640~1280, y −128~0 (1920×128 m), origin_m [-640,-128]. 위쪽(북쪽) 가장자리 높이는 이웃 땅(⑥ 남쪽 줄, 1막 남쪽 줄, 사이 128 m 빈칸=0.3 m, ⑤ 남쪽 줄)을 그대로 따라가므로 이음매가 없다.
해안 길 바닥 −6.5, 갯골 셋(900,−62)(420,−80)(−200,−80)은 바닥 −7.2 로 폭 ±4 m 패여 밀물(−6.0)에 1.2 m 잠기고 썰물(−7.5)엔 드러난다. 남쪽 28 m 는 깊은 바다(−12)로 떨어진다.
⑥ 쪽 오르막은 terrain_act3_west.py(−420,0 에서 시작), ⑤ 쪽 내리막은 terrain_act3.py(988,0 에서 끝남)가 맡는다."""
import os, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "assets3d", "terrain_act3_coast"); LAY = os.path.join(ROOT, "assets3d", "layouts")
X0, Y0, W, H = -640, -128, 1920, 128
HMIN, HMAX = -13.0, 8.0
FLOOR, LOWT, HIGHT, GAET = -6.5, -7.5, -6.0, -7.2
GAETGOL = [900, 420, -200]
def sstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def dec(png, hmin, hmax):
    a = np.array(Image.open(png).convert("RGBA")).astype(np.int64); return ((a[..., 0] << 8) | a[..., 1]) / 65535.0 * (hmax - hmin) + hmin
def top_row():
    """북쪽 가장자리(y=0) 높이 1921 칸: 이웃 땅 남쪽 줄에서 가져온다."""
    xs = np.arange(W + 1) + X0; top = np.full(W + 1, 0.3)
    west = dec(os.path.join(ROOT, "assets3d", "terrain_act3_west", "heightmap.png"), -7.0, 9.0)[0]       # x −640..0
    act1 = dec(os.path.join(ROOT, "assets3d", "terrain", "heightmap.png"), -1.0, 8.0)[0]               # x 0..640
    east = dec(os.path.join(ROOT, "assets3d", "terrain_act3_east", "heightmap.png"), -7.0, 10.0)[0]    # x 768..1280
    gap = dec(os.path.join(ROOT, "assets3d", "terrain_gap", "heightmap.png"), -7.0, 10.0)[0]            # x 640..768 (틈 땅)
    for i, x in enumerate(xs):
        if x <= 0: top[i] = west[min(int(x + 640), len(west) - 1)]
        elif x <= 640: top[i] = act1[min(int(x), len(act1) - 1)]
        elif 640 < x < 768: top[i] = gap[min(int(x - 640), len(gap) - 1)]
        elif x >= 768: top[i] = east[min(int(x - 768), len(east) - 1)]
    return top
def build():
    xs = np.arange(W + 1, dtype=np.float64) + X0; ys = np.arange(H + 1, dtype=np.float64) + Y0
    X, Y = np.meshgrid(xs, ys); T = -Y                      # T = 가장자리에서 남쪽으로 떨어진 거리(m), 행 0 = 가장 남쪽(y −128)
    top = top_row()[None, :].repeat(H + 1, 0)
    cliff = sstep(0.0, 3.5, T)                              # 3.5 m 안에 이웃 높이 → 바닥
    h = top * (1 - cliff) + FLOOR * cliff
    sea = sstep(100.0, 128.0, T); h = h * (1 - sea) + (-12.0) * sea
    for gx in GAETGOL:
        m = (1 - sstep(4.0, 9.0, np.abs(X - gx))) * sstep(8.0, 14.0, T) * (1 - sstep(100, 128, T))
        h = h * (1 - m) + GAET * m
    n = (np.sin(X * 0.21) * np.cos(Y * 0.37) + np.sin(X * 0.053 + Y * 0.11)) * 0.06 * sstep(3.5, 8, T)       # 바닥 잔물결
    return np.clip(h + n, HMIN + 0.01, HMAX - 0.01), X, Y, T
def write(h, T):
    os.makedirs(OUT, exist_ok=True)
    v = np.round(np.clip((h - HMIN) / (HMAX - HMIN), 0, 1) * 65535).astype(np.uint32)
    rgba = np.zeros(h.shape + (4,), np.uint8); rgba[..., 0] = v >> 8; rgba[..., 1] = v & 255; rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "heightmap.png"))
    gy, gx = np.gradient(h); slope = np.hypot(gx, gy)[:H, :W]
    hh = h[:H, :W]
    gravel = np.clip(0.2 + 0.9 * sstep(0.5, 1.2, slope), 0, 1); dirt = np.clip(1 - gravel, 0, 1) * sstep(-6.9, -6.4, hh); salt = np.zeros_like(dirt)
    A = np.stack([dirt, np.zeros_like(dirt), gravel, salt], -1)
    Image.fromarray((A * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "splat_a.png"))
    foam = (sstep(-8.2, -7.6, hh) * (1 - sstep(-7.2, -6.6, hh))); wet = sstep(-7.8, -6.8, hh) * (1 - sstep(-6.2, -5.8, hh))
    z = np.zeros_like(foam); B = np.stack([z, foam, wet, np.ones_like(z)], -1)
    Image.fromarray((B * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "splat_b.png"))
    return slope
def main():
    h, X, Y, T = build(); slope = write(h, T)
    # 미리보기: 위가 북쪽, 높이를 색으로
    img = np.clip((h + 12) / 14.0, 0, 1); rgb = np.stack([img * 200 + 30, img * 190 + 40, img * 150 + 60], -1).astype(np.uint8)[::-1]
    Image.fromarray(rgb).resize((W // 2, H * 2), Image.NEAREST).save(os.path.join(ROOT, "assets3d", "previews", "act3_coast_terrain_map.png"))
    json.dump({"origin_m": [X0, Y0], "size_x_m": W, "size_z_m": H, "size": W, "height_res_x": W + 1, "height_res_z": H + 1, "splat_res_x": W, "splat_res_z": H, "height_min_m": HMIN, "height_max_m": HMAX,
               "coast_floor_m": FLOOR, "tide_low_m": LOWT, "tide_high_m": HIGHT, "gaetgol_floor_m": GAET, "gaetgol_x": GAETGOL,
               "layers": {"dirt": "해안 모랫길", "gravel": "벼랑 바위", "splat_b.G": "물거품(썰물선)", "splat_b.B": "젖은 바닥(밀물에 잠기는 높이)"},
               "note": "아트 terrain_act3_coast.py가 만든다. 행 0=남쪽(월드 y −128). 북쪽 가장자리는 이웃 땅과 같은 높이. 이 띠의 물판은 z −7.5(썰물)↔−6.0(밀물)로 오르내림(⑤ 항구의 −0.5↔+0.6과는 다른 물높이)."}, open(os.path.join(OUT, "terrain.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 배치: 벼랑 가장자리 돌담(1막·⑥ 쪽, 오르막 길목은 비움), 해안 물판
    props = []
    top = top_row()
    for x in range(-558, 768, 4):
        t = top[int(x + 640)]
        if t < -1.0: continue                        # ⑥ 오르막 골짜기 등 이미 낮은 곳은 막지 않는다
        props.append({"prop": "cliff_edge_wall", "file": "assets3d/act3/cliff_edge_wall.glb", "x": x, "y": 1.5, "rot": 0, "z": round(float(t), 2), "note": "벼랑 가장자리 돌담 0.8m(걸어 내려가지 못하게)"})
    for cx in range(-608, 1280, 64):
        for cy in (-96, -32):
            props.append({"prop": "tide_water", "file": "assets3d/act3/tide_water.glb", "x": cx, "y": cy, "rot": 0, "z": LOWT, "note": "해안 물판(기준 z 썰물 -7.5, 코드가 밀물 -6.0까지 올림)"})
    json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "terrain_act3_coast.py가 만든다", "props": props}, open(os.path.join(LAY, "act3_coast_layout.json"), "w"), ensure_ascii=False, indent=1)
    gy_ = {}
    for gx in GAETGOL: gy_[str(gx)] = round(float(h[int(-80 - Y0), int(gx - X0)]), 2)
    print("높이", round(float(h.min()), 2), round(float(h.max()), 2), "| 갯골 바닥", gy_, "| 길 바닥(x=600,y=-70)", round(float(h[int(-70 - Y0), int(600 - X0)]), 2), "| 소품", len(props))
if __name__ == "__main__": main()
