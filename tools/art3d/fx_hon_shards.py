"""파혼으로 깨지는 혼의 파편 이펙트 fx_hon_shards.glb. 주황(파혼 전용색 #E8683A) 날카로운 조각 14개가 몸 한가운데(높이 0.55m)에서 사방으로 튀어 떨어지며 작아져 사라진다.
뼈 Shard0~13 (조각 하나에 뼈 하나, 뼈 머리 = 조각 중심이라 제자리에서 구른다). 동작 Burst 40f(0.67초) 한 번 재생, 이벤트 gone=40(전부 사라짐 → 오브젝트 숨김).
모델 원점 = 혼이 깨지는 바닥 지점. 코드는 파혼 명중 프레임(shatter)에 이 오브젝트를 혼 위치에 놓고 Burst를 재생한다. 혼이 큰 덩어리(lump)면 1.3배, 잔넋(mote)이면 0.6배로 크기만 바꿔 쓴다."""
import sys, os, math, random, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import rig, to_group
import anim
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
N = 14

def build():
    r = random.Random(77); parts = []; bones = [("Root", None, (0, 0, 0), (0, 0, 0.1))]; meta = []
    for i in range(N):
        a = i / N * math.tau + r.uniform(-0.2, 0.2); rad = r.uniform(0.04, 0.12); c = (math.cos(a) * rad, math.sin(a) * rad, 0.55 + r.uniform(-0.2, 0.25))
        w = r.uniform(0.07, 0.13); h = r.uniform(0.12, 0.22)
        sh = pyramid(f"shard{i}", w, w * 0.6, h, (c[0], c[1], c[2] - h / 2), mat("#E8683A", 2.6), rot=(r.uniform(0, 3), r.uniform(0, 3), r.uniform(0, 3)))
        parts += to_group([sh], f"Shard{i}"); bones.append((f"Shard{i}", "Root", c, (c[0], c[1], c[2] + 0.1)))
        sp = r.uniform(1.6, 3.4); up = r.uniform(1.6, 3.8)
        meta.append({"v": (math.cos(a) * sp, math.sin(a) * sp, up), "spin": (r.uniform(-900, 900), r.uniform(-900, 900), r.uniform(-900, 900)), "c": c})
    return parts, bones, meta

def clip(meta):
    keys = []; G = 9.8
    for f in range(0, 41, 2):
        t = f / 60; spec = {}
        for i, m in enumerate(meta):
            x, y, z = m["v"][0] * t, m["v"][1] * t, m["v"][2] * t - 0.5 * G * t * t
            z = max(z, -m["c"][2] + 0.03)                  # 바닥(높이 0)에 닿으면 멈춘다
            k = 1.0 if f < 28 else max(0.02, 1 - (f - 28) / 12)    # 끝 12프레임에 작아져 사라짐
            spec[f"Shard{i}"] = {"l": (x, y, z), "r": tuple(s * t for s in m["spin"]), "s": (k, k, k)}
        keys.append((f, spec))
    return keys

if __name__ == "__main__":
    reset(); anim.setup_scene(); parts, bones, meta = build(); o = join("fx_hon_shards", parts); arm = rig(o, bones)
    i = anim.clip(arm, "Burst", clip(meta), "LINEAR"); i.update({"loop": False, "events": {"gone": 40}})
    if "--sheets" in sys.argv:
        setup_render(3.4, (0, 0, 0.7), size=(200, 260), ground_size=8); anim.sheet(arm, "Burst", [0, 6, 14, 24, 34, 40], os.path.join(OUT, "previews", "anim_fx_hon_shards_Burst"), ortho=3.4, center=(0, 0, 0.7), cell=(200, 260))
    p = os.path.join(OUT, "fx", "fx_hon_shards.glb"); anim.export_rig(arm, p); v = anim.verify(p); print(v)
    json.dump({"fps": anim.FPS, "clip": i, "verify": v}, open(os.path.join(OUT, "fx", "_fx_hon_shards_manifest.json"), "w"), ensure_ascii=False, indent=1)
