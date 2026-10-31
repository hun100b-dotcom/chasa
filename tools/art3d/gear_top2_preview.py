"""상위 두 등급(이름 있는·한 벌) 차별화 점검판: 귀한(t3)과 나란히, 앞·옆·뒤 세 방향 + 실루엣(검은 그림자) 줄.
실행: python3 gear_top2_preview.py → assets3d/previews/gear_top2.png, gear_top2_silhouette.png"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import gear as G
from npc_silhouette import black_everything
OUT = G.OUT

def scene(tiers, yaw, path, sil=False):
    reset()
    for i, t in enumerate(tiers):
        parts = G.mannequin() + G.gat(t) + G.dopo(t) + G.tti(t) + G.sin_(t) + G.norigae(t, "R") + G.norigae(t, "L")
        o = join(f"set{t}", parts); o.location = ((i - (len(tiers) - 1) / 2) * 1.6, 0, 0); o.rotation_euler = (0, 0, yaw)
    setup_render(6.4, (0, 0, 1.05), elev=30, size=(1500, 640), ground_size=14)
    if sil: black_everything()
    bpy.context.scene.cycles.samples = 28; render(path)

if __name__ == "__main__":
    from PIL import Image
    tmp = []
    for k, yaw in enumerate((0, math.pi / 2, math.pi)):
        p = os.path.join(OUT, "previews", f"_t2_{k}.png"); scene((3, 4, 5), yaw, p); tmp.append(p)
    ims = [Image.open(p).convert("RGB") for p in tmp]; W = Image.new("RGB", (ims[0].width, ims[0].height * 3))
    for i, im in enumerate(ims): W.paste(im, (0, im.height * i))
    W.save(os.path.join(OUT, "previews", "gear_top2.png")); [os.remove(p) for p in tmp]
    p = os.path.join(OUT, "previews", "_t2s.png"); scene((3, 4, 5), 0, p, True); Image.open(p).convert("RGB").save(os.path.join(OUT, "previews", "gear_top2_silhouette.png")); os.remove(p)
