"""M14 로딩 화면 세트: 지역마다 그림 한 장 + 팁 줄 묶음(구역별 팁 판).
왜 이렇게: 기획 명세는 '지역 넘을 때 그림 한 장 + 팁 한 줄(22자 이내)'이다. 1막 앞 3장(솔고개·물막이 골·폐당집)은 이미 있어서,
여기서는 빠진 지역(보릿들·검은여울)과 시즌 2·3(저승판·아래층)의 그림을 더하고, 지역별 팁 줄 표(loading_tips.json)를 한 파일로 모아 코드가 읽게 한다.
그림은 기존 밤 장면 렌더를 1920×1080으로 키워 가장자리·아래를 어둡게 마무리한다(막대·팁 판이 얹힐 자리 확보).
팁 문구는 아트가 낸 **초안**이다(기획이 고침). 22자 넘는 줄은 스크립트가 막는다.
실행: python3 loading_tips.py → assets3d/title/loading_{4_boritdeul,5_geomeun,6_jeoseung,7_areucheung}.jpg, assets3d/title/loading_tips.json, assets3d/previews/loading_tips_sheet.jpg"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import ui_lib as U
from title_assets import grade

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
PRE = os.path.join(ROOT, "previews"); OUT = os.path.join(ROOT, "title")

# 지역 → (그림 원본, 확대 영역 비율(좌,위,우,아래), 파일 이름). 시즌 2·3 원본은 50° 미리보기라 가운데를 잘라 쓴다.
ZONES = [
    ("boritdeul", "scene_hamlet_final.jpg", None, "loading_4_boritdeul"),
    ("geomeun", "scene_plague_final.jpg", None, "loading_5_geomeun"),
    ("jeoseung", "scene_naru_final.jpg", None, "loading_6_jeoseung"),
    ("areucheung", "scene_stream_final.jpg", None, "loading_7_areucheung"),
]
# 시즌 2·3 그림은 임시 대역(나루·개울 밤 장면). 시즌 전용 장면 렌더가 생기면 같은 파일 이름으로 교체한다.
# 팁 초안(22자 이내). 1막은 '지금 코드에 있는 규칙'만, 시즌 2·3은 시즌 진입 명세(season-entry-10min.md)의 새 규칙 6줄씩.
TIPS = {
    "solgogae": ("솔고개 마을 어귀", "loading_1_solgogae", ["서낭당에서 쉬면 몸을 추스른다", "바닥 빛줄기 색이 장비 등급이다", "[Space]로 구르면 공격을 피한다"]),
    "mulmagi": ("물막이 골", "loading_2_mulmagi", ["둘러싸이면 한 방향으로 빠져나가자", "혼이 꿇으면 [E] 천도 [R] 파혼", "꿇은 혼은 10초 안에 처결하자"]),
    "pyedang": ("폐당집 터", "loading_3_pyedang", ["땅이 꿈틀하면 발밑을 보자", "예고가 뜨면 0.5초 안에 구르자", "이름 띠가 붙은 혼은 강하다"]),
    "boritdeul": ("보릿들", "loading_4_boritdeul", ["[Q]로 먼 혼을 끌어올 수 있다", "얼룩을 밟으면 걸음이 느려진다", "밤에는 서낭당에서 넋길을 탄다"]),
    "geomeun": ("검은여울", "loading_5_geomeun", ["얕은 여울에선 물살에 밀리지 말자", "[M]으로 지도를 펼쳐 길을 본다", "사람 곁에 머물면 말이 들린다"]),
    "jeoseung": ("저승판(시즌 2)", "loading_6_jeoseung", ["새벽 틈에 줄 가운데를 들어 보자", "배웅하는 혼은 서두르지 않는다", "파혼 뒤 이름 쪽지를 잡아 보자", "돌아선 혼은 둘째부터 쪽지가 떨어진다", "가루는 바람 방향으로 흩어진다", "나룻불이 켜지면 한 칸 나아간 것"]),
    "areucheung": ("아래층(시즌 3)", "loading_7_areucheung", ["물이 빠지면 둑 계단이 열린다", "물이 차서 떠밀려도 잃는 건 없다", "원념의 실을 끊으면 백이 꿇는다", "[E] 눕히기 [R] 깨뜨리기", "빈 이름 칸은 낮에 단서를 찾자", "눕힌 업은 물에 씻겨 나간다"]),
}
# 서사·기획 쪽이 고친 팁이 loading_tips.json에 있으면 그 문구를 우선한다(이 스크립트는 그림·미리보기만 다시 뽑고, 사람이 고친 문구를 덮어쓰지 않는다)
_J = os.path.join(OUT, "loading_tips.json")
if os.path.exists(_J):
    for _z, _v in json.load(open(_J)).get("zones", {}).items():
        if _z in TIPS: TIPS[_z] = (_v.get("title", TIPS[_z][0]), TIPS[_z][1], _v["tips"])
for z, (_, _, ls) in TIPS.items():
    for t in ls: assert len(t) <= 22, f"{z}: {t} ({len(t)}자)"

def make_pic(src, crop, name):
    im = Image.open(os.path.join(PRE, src)).convert("RGB"); w, h = im.size
    if crop: im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    # 16:9로 맞춰 자르고 키운다
    w, h = im.size; tw = int(h * 16 / 9)
    if tw <= w: x0 = (w - tw) // 2; im = im.crop((x0, 0, x0 + tw, h))
    else: th = int(w * 9 / 16); y0 = (h - th) // 2; im = im.crop((0, y0, w, y0 + th))
    im = grade(im.resize((1920, 1080), Image.LANCZOS), 0.55); im.save(os.path.join(OUT, name + ".jpg"), quality=88); return im

def run():
    pics = {}
    for z, src, crop, name in ZONES: pics[z] = make_pic(src, crop, name)
    for z, (_, name, _) in TIPS.items():
        if z not in pics: pics[z] = Image.open(os.path.join(OUT, name + ".jpg")).convert("RGB")
    man = {"note": "로딩 화면 지역 세트. 화면 전체에 image를 깔고, 높이 90%에 로딩 막대(loading_bar_*), 그 위 y=0.82에 팁 판(first10/loading_tip_plate 960×64)을 가운데 놓고 팁 한 줄(22px)을 얹는다. 팁은 지역 줄 묶음에서 로딩마다 하나씩 돌린다(같은 줄 연속 금지). 시즌 2·3은 지역 대신 시즌 줄 묶음을 쓴다.", "tip_plate": {"y_norm": 0.82, "size_px": [960, 64], "font_px": 22, "max_chars": 22}, "zones": {}}
    for z, (title, name, tips) in TIPS.items(): man["zones"][z] = {"title": title, "image": name + ".jpg", "tips": tips}
    json.dump(man, open(os.path.join(OUT, "loading_tips.json"), "w"), ensure_ascii=False, indent=1)
    # 미리보기: 7장 축소 + 팁 판 + 막대
    plate = Image.open(os.path.join(ROOT, "ui", "first10", "loading_tip_plate.png")).convert("RGBA"); bar = Image.open(os.path.join(OUT, "loading_bar_frame.png")).convert("RGBA")
    f = U.font(22); cells = []
    for z, (title, name, tips) in TIPS.items():
        c = pics[z].convert("RGBA"); c.alpha_composite(plate, ((1920 - plate.width) // 2, int(1080 * 0.82))); d = ImageDraw.Draw(c)
        d.text((960 + 20, int(1080 * 0.82) + 32), tips[0], font=f, fill=U.INK, anchor="mm")
        c.alpha_composite(bar, ((1920 - bar.width) // 2, int(1080 * 0.90))); d.text((60, 50), title, font=U.font(36), fill=(240, 232, 214)); cells.append(c.convert("RGB").resize((640, 360), Image.LANCZOS))
    W = Image.new("RGB", (640 * 4, 360 * 2), (20, 20, 24))
    for i, c in enumerate(cells): W.paste(c, ((i % 4) * 640, (i // 4) * 360))
    W.save(os.path.join(PRE, "loading_tips_sheet.jpg"), quality=86)

if __name__ == "__main__": run(); print("ok")
