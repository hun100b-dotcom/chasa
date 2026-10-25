"""HUD 보조 그림(3차). 실행: python3 hud_art3.py
hint_plate: 밝은 낮 화면에서 스킬바 위 안내 글자(무기 철삭 (Tab) · 회피 점 · Space 피하기)가 배경에 묻히던 문제를 막는 먹판.
왜 판을 까나: 글자 외곽선만으로는 낮 풀밭(밝은 황록) 위 흰 글씨가 안 읽힌다(a271cff 캡처). 명세 §0-4 '모든 글자에 외곽선 또는 그림자'는 최소 조건이고,
밝은 배경에서는 먹판(남청 먹 55~60%)이 가장 확실하다. 어두운 밤 화면에서는 판이 거의 안 보이게 가장자리를 부드럽게 한다."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from ui_lib import *

def plate(w, h, r, alpha):
    S = 2; im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=r * S, fill=ABYSS + (alpha,))
    a = im.split()[3].filter(ImageFilter.GaussianBlur(3 * S)); im.putalpha(a.point(lambda v: min(255, int(v * 1.25))))   # 가장자리를 번지게
    return im
save(plate(64, 32, 12, 150), "hint_plate", "hud", nine=[20, 14, 20, 14], note="스킬바 위 안내 글자(14~16px) 뒤 먹판. 9칸 늘이기. 글자 폭+양옆 24px 로 늘려 깔 것. 낮에 필요, 밤엔 거의 안 보임")
dump_manifest("ui_manifest.json")
print("ok")
