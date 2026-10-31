import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import souls
import bpy
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
def load(name, loc, scale=1.0, rotz=0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, "fx", name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.location = loc; o.scale = (scale,) * 3
    return new
def scene(night, path):
    reset()
    for i, (k, kind) in enumerate((("fresh", "soul_fresh"), ("day", "soul_day"), ("old", "soul_old"))):
        for j, s in enumerate((1.0, 0.45)):
            x = (i - 1) * 4.0; y = (0.5 - j) * 4.0
            o = join(f"soul{i}{j}", souls()[k](0)); o.location = (x, y, 0)
            load(f"fx_wait_ring_{k}", (x, y, 0.02), s)
    setup_render(11, (0, 0, 0.3), size=(1500, 900), ground_size=30, night=night)
    bpy.context.scene.cycles.samples = 28; render(path)
if __name__ == "__main__":
    scene(False, "/tmp/wait_day2.png")
