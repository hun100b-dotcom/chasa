"""파혼 결말 보강 물건 9개 미리보기(클로즈업 5는 가까이, 낮 자국 4는 쿼터뷰 50°). 산출: assets3d/previews/bossend_props.png. 실행: python3 bossend_check.py"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from PIL import Image, ImageDraw, ImageFont
A = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
ELEV = int(sys.argv[1]) if len(sys.argv) > 1 else 50
ITEMS = [("closeup_flagpole", 1.1, 0.12), ("closeup_mokpae", 0.7, 0.22), ("closeup_ledger_back", 0.55, 0.02), ("closeup_rope7", 1.8, 0.05), ("closeup_blank_tag", 0.7, 0.2),
         ("trace_banner_up", 5.0, 1.8), ("trace_armor_empty", 3.0, 1.0), ("trace_mokpae_gap", 3.5, 1.0), ("trace_anchor_rope", 4.8, 0.7)]
f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 20); S = 420; sheet = Image.new("RGB", (S * 3, S * 3), (40, 44, 48)); d = ImageDraw.Draw(sheet)
for i, (k, sc, zc) in enumerate(ITEMS):
    reset(); bpy.ops.import_scene.gltf(filepath=os.path.join(A, "props", f"prop_{k}.glb")); setup_render(sc, (0, 0, zc), elev=ELEV, size=(S, S), ground_size=12)
    sce = bpy.context.scene; sce.cycles.samples = 24; p = os.path.join(A, "previews", "_be.png"); sce.render.filepath = p; bpy.ops.render.render(write_still=True)
    sheet.paste(Image.open(p).convert("RGB"), ((i % 3) * S, (i // 3) * S)); d.text(((i % 3) * S + 6, (i // 3) * S + 4), k, fill=(255, 240, 200), font=f); os.remove(p)
sheet.save(os.path.join(A, "previews", f"bossend_props_{ELEV}.png"))
