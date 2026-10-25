"""무기 5계열 전후 비교 렌더. 실행: python3 weapon_compare.py  → assets3d/previews/q_before_weapons.png / q_after_weapons.png
무기를 세워 비스듬히(3/4 각도) 한 자루씩 같은 조명으로 찍어 한 줄로 이어 붙인다. 옛 모양은 *_v1 함수."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import weapons, look_v2
from PIL import Image
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d", "previews")
BEFORE = [weapons.chain_v1, weapons.bangmang_v1, weapons.yoryeong_v1, weapons.samjichang_v1, weapons.myeongbu_v1]
AFTER = [look_v2.chain2, look_v2.bangmang2, look_v2.yoryeong2, look_v2.samjichang2, look_v2.myeongbu2]
W_, H_ = 340, 560
for tag, fns in (("before", BEFORE), ("after", AFTER)):
    row = Image.new("RGB", (W_ * 5, H_))
    for i, fn in enumerate(fns):
        reset(); o = join("w", fn()); lo, hi = bounds(o); o.rotation_euler = (0, 0, math.radians(-30)); bpy.context.view_layer.update()
        h = hi.z - lo.z; cz = (hi.z + lo.z) / 2; ortho = max(h * 1.08, 0.9) * (H_ / H_)
        setup_render(ortho * (W_ / H_) if False else ortho * 1.0, (0, 0, cz), elev=16, size=(W_, H_), ground=False, ground_size=6)
        bpy.context.scene.cycles.samples = 40
        p = os.path.join(OUT, "_tmp_w.png"); render(p); row.paste(Image.open(p).convert("RGB"), (W_ * i, 0)); os.remove(p)
    row.save(os.path.join(OUT, f"q_{tag}_weapons.png"))
print("ok")
