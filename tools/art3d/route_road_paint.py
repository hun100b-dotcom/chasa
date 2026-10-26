"""처음 10분 길의 흙길을 3 m 폭으로 굵힌다(땅 섞기 그림 splat_a의 R=흙).
왜: 24 m 점검(docs/ROUTE10-STILLS.md)에서 길이 1 m 가는 선이라 화면에서 거의 안 보여(보릿들·둑길 장면 모두 풀 한 장) 길 찾기가 안 됐다.
 처음에는 nav_points 웨이포인트(꺾는 점)를 이어 칠했으나 그 선은 숲·밭을 비스듬히 가로질러(확인판 road_before_after 참고) 어색해서 버리고, '이미 있는 가는 길'을 굵히는 방식으로 바꿨다.
방법: 흙(R>150) 중 가는 선만(두꺼운 덩어리=마당·무덤 터는 제외: 침식 뒤 팽창한 '덩어리'를 빼면 선만 남는다) 골라 반경 1.0 m 부풀리고 가장자리 0.8 m를 풀과 섞는다. 영역은 처음 10분 구간(x 150~420, y 15~315)만.
멱등: 원본을 splat_a_orig.png 로 한 번 백업하고 항상 원본에서 계산한다. 결과는 assets3d/terrain/splat_a.png + unity Resources/Terrain/splat_a.bytes(같은 PNG).
실행: python3 route_road_paint.py → 그다음 python3 place_act1_route.py (길 위 소품을 비우는 계산이 이 흙길을 읽는다)"""
import os, sys, math, json, shutil
import numpy as np
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
T = os.path.join(ROOT, "assets3d", "terrain"); U = os.path.join(ROOT, "unity", "Assets", "Resources", "Terrain")
REGION = (150, 15, 420, 315)       # x0, y0, x1, y1 (m)
orig = os.path.join(T, "splat_a_orig.png")
if not os.path.exists(orig): shutil.copy(os.path.join(T, "splat_a.png"), orig)
from PIL import ImageFilter
s = np.array(Image.open(orig)).astype(np.float32); H, W = s.shape[:2]
x0, y0, x1, y1 = REGION; m = np.zeros((H, W), np.uint8); m[y0:y1, x0:x1] = (s[y0:y1, x0:x1, 0] > 150) * 255
im = Image.fromarray(m); blob = im.filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(7)); blob = np.asarray(blob.filter(ImageFilter.MaxFilter(5))) > 0      # 두꺼운 덩어리(+여유)
thin = (m > 0) & ~blob
wide = Image.fromarray((thin * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))           # 반경 2 px(=2 m) 부풀림 → 폭 약 5 m가 되니 아래에서 줄인다
wide = Image.fromarray((thin * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))           # 반경 1 m 부풀림 → 폭 3 m
wgt = np.asarray(wide.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255; wgt = np.clip(wgt * 1.25, 0, 1); wgt[:y0] = 0; wgt[y1:] = 0; wgt[:, :x0] = 0; wgt[:, x1:] = 0
dirt = np.array([226, 30, 0, 0], np.float32)
out = s * (1 - wgt[..., None]) + dirt * wgt[..., None]
out[..., 0] = np.maximum(out[..., 0], s[..., 0]); out[..., 3] = np.where(wgt > 0.2, np.minimum(out[..., 3], s[..., 3] * (1 - wgt)), s[..., 3])
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(T, "splat_a.png"), optimize=True)
shutil.copy(os.path.join(T, "splat_a.png"), os.path.join(U, "splat_a.bytes"))
json.dump({"region_m": REGION, "thin_px": int(thin.sum()), "widened_px": int((wgt > 0.5).sum())}, open(os.path.join(T, "_route_road.json"), "w"), ensure_ascii=False, indent=1); print(int(thin.sum()), int((wgt > 0.5).sum()))
