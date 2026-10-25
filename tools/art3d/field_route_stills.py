"""처음 10분 길(깨어남 → 솔고개 → 보릿들 → 물막이 골 → 나루 영감)을 실제 게임 카메라(줌 24 m·피치 58°·세로 FOV 35°)로 낮·밤 한 장씩 그린다.
왜: 줌이 멀어지면 화면에 담기는 땅이 넓어져 '텅 빈 풀밭'·'하얗게 탄 길'·'회색 안개판'이 한눈에 들어온다. 이런 곳을 소품·조명으로 고칠 수 있게 길을 따라가며 확인한다.
각 장: 주인공(해당 자리) + 해 넘긴 혼 하나(처결 대기 고리) + 혼 하나를 얹고, 길 진행 방향(북)으로 바라본다.
측정(장마다): ① 타서 흰 픽셀 비율(밝기 ≥0.92) ② 평평한 회색 칸 비율(32px 칸의 밝기 표준편차 <0.02·채도 <0.15 — 안개판처럼 아무 무늬 없이 회색) ③ 같은 모양 풀 바닥뿐인 칸 비율(채도·밝기 변화가 풀 색 범위이고 표준편차 <0.035)
산출: assets3d/previews/route10/f10_{n}_{day,night}.png, 요약 시트 route10_sheet_{day,night}.png, assets3d/previews/route10/_route10.json
실행: FS_TAG=_x python3 field_route_stills.py [day|night]   (밤은 기본, 낮은 FS_DAY=1 환경변수가 필요해 인자 day로 지정)"""
import os, sys, math, json
mode = sys.argv[1] if len(sys.argv) > 1 else "night"
if mode == "day": os.environ["FS_DAY"] = "1"
os.environ.setdefault("FS_SAMPLES", "48")
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import field_scene as F
from mathutils import Vector
DIST, PITCH = 24, 58
# (이름, 주인공 x,y, 화면 설명)
STOPS = [("1_wake", 193.0, 30.0, "깨어남: 서낭당 고개(시작 위치)"), ("2_well", 198.0, 47.5, "마을 길(우물가 쪽)"), ("3_west", 170.0, 58.0, "마을 서쪽 길"),
         ("4_bank", 240.0, 132.0, "보릿들 둑길"), ("5_field", 321.0, 200.0, "보릿들 가운데→물막이"), ("6_weir", 357.0, 272.0, "물막이 골 어귀"), ("7_naru", 397.0, 281.0, "나루 영감(보스 자리 앞)")]
LENS = 32.1      # 가로 36 mm 센서에서 세로 FOV 35°(16:9)가 되는 초점거리
for n, x, y, ttl in STOPS:
    p = math.radians(PITCH); tgt = (x, y + 0.6, 0.0); loc = (x, y + 0.6 - math.cos(p) * DIST, math.sin(p) * DIST)
    def ex(x=x, y=y, n=n):
        F.pose("hero_chasa", x, y, 0.0, 0, "Idle", 20)
        F.pose("soul_day", x + 3.2, y + 3.5, 0.0, 200, "Kneel", 36); F.put("fx_wait_ring_day", x + 3.2, y + 3.5, 0.04, 0, scale=0.9 * 2 / 2.12)
        F.pose("soul_fresh", x - 3.6, y + 4.6, 0.0, 160, "Idle", 20)
        if n == "7_naru": F.pose("boss_naru", 404, 288, 0.55, 0, "Idle", 10)
    F.SHOTS["f10_" + n] = dict(win=(x - 52, y - 30, x + 52, y + 62), cam=(loc, tgt, LENS), size=(1920, 1080), title=ttl, extras=[ex])

def metrics(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255; lum = a.mean(-1); mx = a.max(-1); mn = a.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-3)
    H, W = lum.shape; B = 32; h, w = H // B, W // B; blk = lum[:h * B, :w * B].reshape(h, B, w, B).transpose(0, 2, 1, 3).reshape(h, w, -1); std = blk.std(-1); ml = blk.mean(-1)
    sb = sat[:h * B, :w * B].reshape(h, B, w, B).transpose(0, 2, 1, 3).reshape(h, w, -1).mean(-1)
    sky = np.zeros((h, w), bool); sky[: int(h * 0.08)] = True      # 맨 위 띠(하늘 가장자리)는 뺀다
    flat_grey = (std < 0.02) & (sb < 0.15) & ~sky; flat_floor = (std < 0.035) & ~sky
    return {"burned_px": round(float((lum >= 0.92).mean()), 4), "flat_grey_blocks": round(float(flat_grey.mean()), 3), "flat_floor_blocks": round(float(flat_floor.mean()), 3), "mean_lum": round(float(lum.mean()), 3)}

if __name__ == "__main__":
    out = os.path.join(F.A3, "previews", "route10"); os.makedirs(out, exist_ok=True); res = {}; tag = "day" if mode == "day" else "night"
    for n, x, y, ttl in STOPS:
        k = "f10_" + n; path = F.run(k); dst = os.path.join(out, f"{k}_{tag}.png"); os.replace(path, dst); res[f"{n}_{tag}"] = {"title": ttl, **metrics(dst)}; print(n, res[f"{n}_{tag}"], flush=True)
    jp = os.path.join(out, "_route10.json"); old = json.load(open(jp)) if os.path.exists(jp) else {}; old.update(res); json.dump(old, open(jp, "w"), ensure_ascii=False, indent=1)
