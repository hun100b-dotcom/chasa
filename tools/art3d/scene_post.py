"""밤 장면 후처리: 먼 곳(화면 위쪽)에 푸른 안개, 가장자리 어둡게(비네팅).
왜: Blender 월드 안개(볼륨)는 장면 전체를 검게 먹어서 쓸 수 없었다. 대신 쿼터뷰에서 '멀수록 위쪽'이라는 점을 써서 그림 위에서 안개를 얹는다."""
import sys, os
from PIL import Image
import numpy as np
A3 = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d", "previews")
def post(key):
    src = os.path.join(A3, f"scene_{key}.png"); im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32) / 255
    h, w, _ = im.shape; ys = np.linspace(0, 1, h)[:, None]; xs = np.linspace(-1, 1, w)[None, :]
    fog = np.array([0.20, 0.26, 0.40], np.float32)
    k = (np.clip(1 - ys / 0.55, 0, 1) ** 1.6 * 0.42)[..., None]            # 위쪽일수록 짙게
    im = im * (1 - k) + fog * k
    vig = (1 - 0.35 * np.clip((xs ** 2 + (ys * 2 - 1) ** 2) / 2, 0, 1))[..., None]   # 비네팅
    im = np.clip(im * vig, 0, 1)
    out = os.path.join(A3, f"scene_{key}_final.jpg"); Image.fromarray((im * 255).astype(np.uint8)).save(out, quality=88); return out
if __name__ == "__main__":
    for k in sys.argv[1:]: print(post(k))
