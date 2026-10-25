"""처결 이펙트 메시. 발광 재질(emission)만 쓰고 투명은 쓰지 않는다(GLB 기본 재질로 안정적으로 읽히게). 투명·깜빡임·크기 변화는 코드가 맡는다.
규약: 원점=땅 중심. 1유닛=1m. 
- fx_tendo_pillar: 천도 빛기둥(속이 빈 육각 기둥 + 위로 갈수록 가늘어짐, 높이 6m, 반지름 0.7m)
- fx_tendo_ring: 천도 고리(바닥에 놓는 둥근 고리, 반지름 1.2m, 이음 8토막)
- fx_pahon_shards_a/b/c: 파혼 폭발 파편 세 가지 모양(각 12개 조각이 퍼진 모습, 반지름 약 1.5m. 코드는 조각별로 날려도 되고 통째로 키워도 됨)
- fx_stain_decal: 원념 얼룩 바닥 데칼(납작한 얼룩 모양, 반지름 1.5m, 두께 2cm, 코드에서 반경만큼 크기 조절)
- fx_wait_ring_fresh/day/old: 처결 대기 고리 3색(갓 죽은 혼 하늘 / 해 넘긴 혼 노랑 / 오래된 혼 적갈색), 반지름 0.9m, 눈금 12개(한 메시로 합쳐 있음. 남은 시간 표시는 고리 전체 크기·투명도로. 눈금별 제어가 필요하면 말해 주세요)"""
import sys, os, math, json, random
import bpy, bmesh
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from lib3d import _obj
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")

def annulus(name, r_in, r_out, h, z, material, segs=16, a0=0.0, a1=math.tau):
    """납작한 고리(또는 호). 위아래 면과 안팎 옆면을 직접 만든다."""
    bm = bmesh.new(); n = segs
    pts = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    V = lambda r, a, zz: bm.verts.new((math.cos(a) * r, math.sin(a) * r, zz))
    top_o = [V(r_out, a, z + h) for a in pts]; top_i = [V(r_in, a, z + h) for a in pts]; bo = [V(r_out, a, z) for a in pts]; bi = [V(r_in, a, z) for a in pts]
    for i in range(n):
        bm.faces.new((top_i[i], top_o[i], top_o[i + 1], top_i[i + 1])); bm.faces.new((bo[i + 1], bo[i], bi[i], bi[i + 1]))
        bm.faces.new((top_o[i], bo[i], bo[i + 1], top_o[i + 1])); bm.faces.new((bi[i], top_i[i], top_i[i + 1], bi[i + 1]))
    if abs((a1 - a0) - math.tau) > 1e-6:
        bm.faces.new((top_i[0], bi[0], bo[0], top_o[0])); bm.faces.new((top_o[n], bo[n], bi[n], top_i[n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, material)

def pillar():
    m = mat("cheondo", 1.6)
    return [cyl("beam", 0.7, 0.35, 6.0, (0, 0, 0), m, 6), cyl("core", 0.3, 0.12, 6.0, (0, 0, 0), mat("chain", 2.2), 6), annulus("base", 0.7, 1.0, 0.04, 0.0, m, 12)]

def ring_tendo():
    m = mat("cheondo", 1.6)
    return [annulus(f"seg{i}", 1.0, 1.25, 0.05, 0.0, m, 3, i * math.tau / 8 + 0.06, (i + 1) * math.tau / 8 - 0.06) for i in range(8)]

def shards(seed):
    rnd = random.Random(seed); p = []
    cols = [mat("red", 1.0), mat("gold", 0.8), "ink"]
    for i in range(12):
        a = rnd.uniform(0, math.tau); r = rnd.uniform(0.5, 1.5); z = rnd.uniform(0.1, 1.2); s = rnd.uniform(0.12, 0.3)
        p.append(cyl(f"shard{i}", s * 0.5, 0.0, s * 2.2, (math.cos(a) * r, math.sin(a) * r, z), cols[i % 3], 4, rot=(rnd.uniform(0, 3), rnd.uniform(0, 3), a)))
    return p

def decal():
    rnd = random.Random(3); bm = bmesh.new(); n = 11; c = bm.verts.new((0, 0, 0.02)); ring = []
    for i in range(n):
        a = i / n * math.tau; r = 1.5 * rnd.uniform(0.62, 1.0); ring.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0.02)))
    for i in range(n): bm.faces.new((c, ring[i], ring[(i + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    base = _obj("stain", bm, mat("soul_lump", 0.0))
    # 안쪽 핏빛 얼룩 한 겹(더 작게)
    bm2 = bmesh.new(); c2 = bm2.verts.new((0, 0, 0.03)); r2 = []
    for i in range(n):
        a = i / n * math.tau; r = 0.8 * rnd.uniform(0.6, 1.0); r2.append(bm2.verts.new((math.cos(a) * r, math.sin(a) * r, 0.03)))
    for i in range(n): bm2.faces.new((c2, r2[i], r2[(i + 1) % n]))
    bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
    return [base, _obj("stain_core", bm2, mat("night", 0.0))]

def wait_ring(color):
    """처결 대기 고리. 50° 카메라 점검(밝은 낮 풀밭·어두운 밤)에서 오래된 혼(갈회색) 고리가 풀색과 밝기가 비슷해 약했다 → 고리 바로 밑에 어두운 먹 받침(발광 없음)을 깔아 어떤 땅에서도 윤곽이 서게 했다."""
    # 줌이 24m까지 멀어지면(폰 기준 고리 두께 0.28mm로 실선처럼 얇아짐) 띠를 0.08→0.17m, 눈금을 2배 크게, 먹 받침도 따라 넓힌다. 바깥 지름(2.12)은 그대로라 코드 배율 그대로 쓴다.
    m = mat(color, 1.2); p = [annulus("rim_ink", 0.68, 0.98, 0.01, -0.005, mat("ink", 0.0), 16), annulus("rim", 0.74, 0.91, 0.04, 0.0, m, 16)]
    for i in range(12):
        a = i / 12 * math.tau
        p.append(box(f"tick_ink{i:02d}", (0.16, 0.26, 0.012), (math.cos(a) * 0.93, math.sin(a) * 0.93, 0.004), mat("ink", 0.0), rot=(0, 0, a - math.pi / 2)))
        p.append(box(f"tick{i:02d}", (0.09, 0.2, 0.05), (math.cos(a) * 0.93, math.sin(a) * 0.93, 0.02), m, rot=(0, 0, a - math.pi / 2)))
    return p

FX = [("fx_tendo_pillar", pillar), ("fx_tendo_ring", ring_tendo), ("fx_pahon_shards_a", lambda: shards(1)), ("fx_pahon_shards_b", lambda: shards(2)), ("fx_pahon_shards_c", lambda: shards(3)), ("fx_stain_decal", decal),
      ("fx_wait_ring_fresh", lambda: wait_ring("soul_fresh")), ("fx_wait_ring_day", lambda: wait_ring("soul_day")), ("fx_wait_ring_old", lambda: wait_ring("soul_old"))]

if __name__ == "__main__":
    rep = []
    for key, fn in FX:
        reset(); o = join(key, fn()); lo, hi = bounds(o)
        rep.append({"name": key, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
        export(o, os.path.join(OUT, "fx", f"{key}.glb"))
    reset()
    for i, (key, fn) in enumerate(FX):
        o = join(key, fn()); o.location = ((i % 5 - 2) * 3.4, -(i // 5) * 3.4 + 1.5, 0)
    setup_render(17, (0, -1.2, 2.0), size=(1300, 560), ground_size=30, night=True)
    render(os.path.join(OUT, "previews", "fx_9_50deg.png"))
    json.dump(rep, open(os.path.join(OUT, "fx", "_fx_manifest.json"), "w"), ensure_ascii=False, indent=1)
    for r in rep: print(r["name"], r["tris"], r["size_m"])
