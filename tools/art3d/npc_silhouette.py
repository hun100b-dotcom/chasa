"""마을 사람 실루엣 점검판: 색을 다 지우고 검은 그림자만 남겨 '멀리서 봤을 때 나이·직업이 읽히는가'를 본다.
왜 이렇게: 쿼터뷰 카메라에서는 얼굴·색보다 머리 위 모양(갓·수건·물동이), 어깨선, 밑단 폭, 키가 먼저 보인다.
실행: python3 npc_silhouette.py out.png [id ...]   (id를 안 주면 마을 17명 21모델 전부)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
import anim
import npcs

def black_everything():
    """모든 메시를 검정 빛 재질로 바꾸고 바닥은 지운다(실루엣만 남기기)."""
    m = bpy.data.materials.new("sil"); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.02, 0.02, 0.03, 1); em.inputs[1].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs[0])
    for ob in list(bpy.context.scene.objects):
        if ob.name == "ground": bpy.data.objects.remove(ob, do_unlink=True)
        elif ob.type == "MESH": ob.data.materials.clear(); ob.data.materials.append(m)
    w = bpy.context.scene.world; w.node_tree.nodes["Background"].inputs[0].default_value = (0.93, 0.92, 0.88, 1)
    bpy.context.scene.view_settings.view_transform = "Standard"

def sheet(specs, path, per_row=7, cell=150):
    from PIL import Image
    rows = [specs[i:i + per_row] for i in range(0, len(specs), per_row)]; imgs = []
    for ri, row in enumerate(rows):
        reset(); anim.setup_scene()
        for i, s in enumerate(row):
            o, arm, cover = npcs.make(s); o.parent.location = (i * 1.35, 0, 0)
        setup_render(9.6 * len(row) / 7 if len(row) < 7 else 9.6, (1.35 * (len(row) - 1) / 2, 0, 0.95), elev=50, size=(cell * per_row, int(cell * 1.45)), ground_size=30)
        black_everything()
        p = path + f".row{ri}.png"; bpy.context.scene.cycles.samples = 8; render(p); imgs.append(Image.open(p).convert("RGB")); os.remove(p)
    W = Image.new("RGB", (imgs[0].width, imgs[0].height * len(imgs)), (237, 235, 224))
    for i, im in enumerate(imgs): W.paste(im, (0, im.height * i))
    W.save(path)

if __name__ == "__main__":
    out = sys.argv[1]; want = [a for a in sys.argv[2:]]
    specs = [s for s in npcs.SPECS if not want or s["id"] in want]
    sheet(specs, out)
