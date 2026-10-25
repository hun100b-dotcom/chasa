"""품질 다듬기 전후 비교 렌더(주인공 3방향·혼 4종 낮/밤·마을 사람 얼굴 4명). 실행: python3 quality_compare.py before|after [hero] [souls] [faces]
같은 카메라·같은 조명으로 찍어야 전후가 공정하게 비교된다. 결과: assets3d/previews/q_{before|after}_{hero,souls,souls_night,faces}.png
'before'는 코드가 바뀐 뒤에는 옛 모양(characters.hero_v1/souls_v1, npcs의 옛 얼굴)을 못 찍으니, 옛 사진은 보존된 파일을 쓴다."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import characters
from PIL import Image
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d", "previews")
tag = sys.argv[1] if len(sys.argv) > 1 else "after"
want = sys.argv[2:] or ["hero", "souls", "faces"]
HERO = characters.hero_v1 if tag == "before" else characters.hero
SOULS = characters.souls_v1 if tag == "before" else characters.souls
def fast(): bpy.context.scene.cycles.samples = 48

if "hero" in want:
    imgs = []
    for ang in (0, 38, 150):
        reset(); o = join("hero", HERO()); o.rotation_euler = (0, 0, math.radians(ang)); bpy.context.view_layer.update()
        setup_render(2.6, (0, 0, 0.98), size=(520, 700), ground_size=10); fast(); p = os.path.join(OUT, f"_tmp_h{ang}.png"); render(p); imgs.append(Image.open(p).convert("RGB")); os.remove(p)
    W = Image.new("RGB", (520 * 3, 700)); [W.paste(im, (520 * i, 0)) for i, im in enumerate(imgs)]; W.save(os.path.join(OUT, f"q_{tag}_hero.png"))
if "souls" in want:
    for night, suf in ((False, ""), (True, "_night")):
        reset()
        for i, (key, fn) in enumerate(SOULS().items()): join(f"s{i}", fn(o=(i - 1.5) * 1.5))
        setup_render(6.6, (0, 0, 0.62), size=(1100, 460), ground_size=14, night=night); fast(); render(os.path.join(OUT, f"q_{tag}_souls{suf}.png"))
if "faces" in want:
    import npcs
    ids = ["N106", "N105", "N205", "N109"]
    reset()
    for i, sid in enumerate(ids):
        s = [x for x in npcs.SPECS if x["id"] == sid][0]; P, cover = npcs.build_body(s); objs = []
        for b, ps in P.items(): objs += npcs.to_group(list(ps), b)
        o = join(f"n{i}", objs); o.location = (i * 0.9, 0, 0)
    setup_render(3.7, (0.9 * 1.5, 0, 1.4), elev=14, size=(1300, 460), ground_size=14); fast(); render(os.path.join(OUT, f"q_{tag}_faces.png"))
