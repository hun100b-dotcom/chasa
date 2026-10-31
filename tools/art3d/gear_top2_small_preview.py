"""신·노리개 상위 두 등급 점검판: 귀한(t3)·이름 있는(t4)·한 벌(t5)을 발끝·허리만 크게 뽑아 나란히 본다(앞·옆, 그리고 검은 실루엣 줄).
왜: 전신 점검판(gear_top2.png)에서는 신·노리개가 너무 작아 모양 차이가 보이지 않는다.
실행: python3 gear_top2_small_preview.py → assets3d/previews/gear_top2_small.png, gear_top2_small_silhouette.png"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import gear as G
from npc_silhouette import black_everything
OUT = G.OUT

def scene(tiers, part, yaw, path, sil=False):
    reset()
    for i, t in enumerate(tiers):
        parts = (G.sin_(t) if part == "feet" else G.tti(t) + G.norigae(t, "R") + G.norigae(t, "L"))
        o = join(f"set{t}", parts); o.location = ((i - (len(tiers) - 1) / 2) * 1.0, 0, 0); o.rotation_euler = (0, 0, yaw)
    z = 0.12 if part == "feet" else 0.75
    setup_render(2.6, (0, 0, z), elev=30, size=(1500, 440), ground_size=8)
    if sil: black_everything()
    bpy.context.scene.cycles.samples = 28; render(path)

if __name__ == "__main__":
    from PIL import Image
    tmp = []
    for part in ("feet", "waist"):
        for k, yaw in enumerate((0, math.pi / 2)):
            p = os.path.join(OUT, "previews", f"_ts_{part}{k}.png"); scene((3, 4, 5), part, yaw, p); tmp.append(p)
    ims = [Image.open(p).convert("RGB") for p in tmp]; W = Image.new("RGB", (ims[0].width, ims[0].height * len(ims)))
    for i, im in enumerate(ims): W.paste(im, (0, im.height * i))
    W.save(os.path.join(OUT, "previews", "gear_top2_small.png")); [os.remove(p) for p in tmp]
    tmp = []
    for part in ("feet", "waist"):
        p = os.path.join(OUT, "previews", f"_tss_{part}.png"); scene((3, 4, 5), part, 0, p, True); tmp.append(p)
    ims = [Image.open(p).convert("RGB") for p in tmp]; W = Image.new("RGB", (ims[0].width, ims[0].height * 2))
    for i, im in enumerate(ims): W.paste(im, (0, im.height * i))
    W.save(os.path.join(OUT, "previews", "gear_top2_small_silhouette.png")); [os.remove(p) for p in tmp]
