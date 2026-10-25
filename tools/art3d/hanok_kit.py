"""한옥 조각 키트 25종 + 조립 시험. 실행: python3 hanok_kit.py
조각 규약: 길이 방향=X, 4m 한 칸(모듈). 벽면 중심선=y 0, 정면(바깥)=-Y, 원점=조각 바닥 한가운데.
쌓는 순서(z): 기단 0~0.5 → 벽·기둥·문 0.5~2.9(높이 2.4) → 지붕 2.9 위. 벽 정면이 +X를 보려면 z축으로 +90도, -X는 -90도, +Y는 180도.
"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from lib3d import _obj
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
H = 2.4   # 벽 높이
def beam(w, z, t=0.12): return box("beam", (w, 0.2, t), (0, 0, z), "wood_dark")
def lattice(cx, cz, w, h, y=0.0, bars=4):   # 문살(격자)
    p = [box("frame_t", (w, 0.1, 0.06), (cx, y, cz + h / 2), "wood_dark"), box("frame_b", (w, 0.1, 0.06), (cx, y, cz - h / 2), "wood_dark")]
    for i in range(bars + 1):
        x = cx - w / 2 + w * i / bars
        p.append(box(f"bar{i}", (0.04, 0.08, h), (x, y, cz), "wood_dark"))
    p.append(box("paper", (w, 0.03, h), (cx, y + 0.02, cz), "hanji"))
    return p

def hip(name, span, length, h, material, ridge=0.4):
    """우진각(네 면) 지붕의 끝 조각. x=0 단면은 직선 지붕과 같은 삼각형, x=length에서 끝난다."""
    bm = bmesh.new(); s = span / 2
    A, B, C, D = (bm.verts.new(p) for p in [(0, -s, 0), (length, -s, 0), (length, s, 0), (0, s, 0)])
    R1, R2 = bm.verts.new((0, 0, h)), bm.verts.new((ridge, 0, h))
    for f in [(A, B, R2), (A, R2, R1), (C, D, R1), (C, R1, R2), (B, C, R2), (A, D, C, B)]:
        bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, material)

def K():
    k = {}
    # --- 기단
    k["gidan_straight"] = ("기단 직선", [box("g", (4, 0.9, 0.5), (0, 0, 0.25), "stone")], "4m 직선")
    k["gidan_corner"] = ("기단 모서리", [box("g", (0.9, 0.9, 0.5), (0, 0, 0.25), "stone_dark")], "모서리 한 칸")
    # --- 기둥
    k["pillar_round"] = ("둥근 기둥(주춧돌)", [cyl("base", 0.2, 0.17, 0.16, (0, 0, 0), "stone", 8), cyl("shaft", 0.11, 0.1, H - 0.1, (0, 0, 0.1), "pillar", 8)], "벽 사이 이음 기둥")
    k["pillar_square"] = ("네모 기둥", [box("shaft", (0.2, 0.2, H), (0, 0, H / 2), "wood_dark"), box("cap", (0.3, 0.3, 0.1), (0, 0, H - 0.05), "wood_dark")], "서민집 기둥")
    # --- 벽(4m 한 칸)
    def wall(mat):
        return [box("panel", (4, 0.16, H - 0.2), (0, 0, H / 2), mat), beam(4, 0.06), beam(4, H - 0.06)]
    k["wall_plaster"] = ("회벽", wall("hanji"), "흰 회벽")
    k["wall_mud"] = ("흙벽", wall("mud"), "초가의 흙벽")
    k["wall_plank"] = ("판벽", [box(f"pl{i}", (0.38, 0.14, H - 0.2), (-1.8 + i * 0.4, 0, H / 2), "wood" if i % 2 else "wood_dark") for i in range(10)] + [beam(4, 0.06), beam(4, H - 0.06)], "나무판 벽")
    ww = [box("low", (4, 0.16, 0.9), (0, 0, 0.45), "hanji"), box("up", (4, 0.16, 0.5), (0, 0, H - 0.25), "hanji"),
          box("sideL", (1.3, 0.16, 1.0), (-1.35, 0, 1.4), "hanji"), box("sideR", (1.3, 0.16, 1.0), (1.35, 0, 1.4), "hanji"), beam(4, 0.06), beam(4, H - 0.06)] + lattice(0, 1.4, 1.4, 1.0, y=-0.02, bars=5)
    k["wall_window"] = ("창 있는 벽", ww, "가운데 격자창")
    # --- 문(4m 한 칸에 들어감)
    d1 = [box("sideL", (1.4, 0.16, H - 0.2), (-1.3, 0, H / 2), "hanji"), box("sideR", (1.4, 0.16, H - 0.2), (1.3, 0, H / 2), "hanji"), box("top", (1.2, 0.16, 0.35), (0, 0, H - 0.18), "hanji"),
          box("panel", (1.1, 0.09, 1.85), (0, -0.04, 0.95), "wood_dark"), box("knob", (0.07, 0.04, 0.07), (0.38, -0.1, 0.95), "gold"), beam(4, 0.06), beam(4, H - 0.06)]
    k["door_single"] = ("외짝 여닫이문", d1, "마루로 나가는 문")
    d2 = [box("sideL", (0.45, 0.16, H - 0.2), (-1.78, 0, H / 2), "hanji"), box("sideR", (0.45, 0.16, H - 0.2), (1.78, 0, H / 2), "hanji"), box("top", (3.1, 0.16, 0.3), (0, 0, H - 0.17), "hanji"),
          beam(4, 0.06), beam(4, H - 0.06)] + lattice(-0.78, 1.0, 1.52, 1.8, y=-0.02, bars=4) + lattice(0.78, 1.0, 1.52, 1.8, y=0.04, bars=4)
    k["door_double"] = ("쌍미닫이문", d2, "안방 앞 격자 문")
    gate = [box("postL", (0.4, 0.4, 3.0), (-1.6, 0, 1.5), "pillar"), box("postR", (0.4, 0.4, 3.0), (1.6, 0, 1.5), "pillar"),
            box("leafL", (1.35, 0.14, 2.3), (-0.72, 0, 1.2), "wood_dark"), box("leafR", (1.35, 0.14, 2.3), (0.72, 0, 1.2), "wood_dark"),
            box("lintel", (3.6, 0.3, 0.3), (0, 0, 2.7), "wood_dark"), prism("cap", 4.4, 1.8, 0.7, (0, 0, 2.85), "tile"),
            box("ringL", (0.1, 0.04, 0.1), (-0.2, -0.1, 1.2), "gold"), box("ringR", (0.1, 0.04, 0.1), (0.2, -0.1, 1.2), "gold")]
    k["gate_main"] = ("대문(솟을 지붕 포함)", gate, "높이 약 3.5m")
    sa = [box("postL", (0.12, 0.12, 1.5), (-0.9, 0, 0.75), "wood"), box("postR", (0.12, 0.12, 1.5), (0.9, 0, 0.75), "wood"),
          box("door", (1.7, 0.06, 1.1), (0, 0, 0.7), "thatch")] + [box(f"twig{i}", (0.03, 0.08, 1.1), (-0.8 + i * 0.2, -0.02, 0.7), "wood") for i in range(9)]
    k["saripmun"] = ("사립문", sa, "초가 울타리 문, 폭 2m")
    # --- 툇마루·댓돌
    tm = [box("floor", (4, 1.2, 0.1), (0, -0.7, 0.5), "wood")] + [box(f"plank{i}", (4, 0.02, 0.02), (0, -0.35 - i * 0.28, 0.56), "wood_dark") for i in range(4)] + [box(f"leg{i}", (0.14, 0.14, 0.45), (-1.9 + i * 1.267, -1.2, 0.225), "wood_dark") for i in range(4)]
    k["toenmaru_straight"] = ("툇마루 직선", tm, "벽 앞에 붙이는 4m 마루, 윗면 높이 0.55m")
    k["toenmaru_corner"] = ("툇마루 모서리", [box("floor", (1.2, 1.2, 0.1), (0, -0.6, 0.5), "wood"), box("leg", (0.14, 0.14, 0.45), (0.5, -1.1, 0.225), "wood_dark")], "모서리 한 칸")
    k["daetdol_step"] = ("댓돌(계단)", [box("s1", (1.4, 0.5, 0.2), (0, -0.25, 0.1), "stone"), box("s2", (1.2, 0.5, 0.2), (0, -0.7, 0.1), "stone_dark")], "문 앞 돌계단")
    k["chimney"] = ("굴뚝", [box("stack", (0.7, 0.7, 1.8), (0, 0, 0.9), "stone_dark"), box("clay", (0.55, 0.55, 0.5), (0, 0, 2.05), "mud"), prism("cap", 0.9, 0.9, 0.3, (0, 0, 2.3), "tile")], "뒷벽 곁 굴뚝")
    # --- 기와 지붕(맞배·우진각)
    k["giwa_roof_straight"] = ("기와 지붕 직선", [prism("roof", 4, 6.4, 1.6, (0, 0, 0), "tile"), box("ridge", (4, 0.34, 0.24), (0, 0, 1.64), "tile")], "4m 용마루, 폭 6.4m")
    k["giwa_roof_gable_end"] = ("기와 박공(맞배 끝)", [prism("cap", 0.6, 6.6, 1.65, (0.3, 0, 0), "tile"), prism("gable", 0.12, 5.4, 1.3, (0.05, 0, 0), "hanji"), box("ridge", (0.6, 0.34, 0.24), (0.3, 0, 1.68), "tile")], "직선 지붕 끝에 붙임, 0.6m")
    parts = [hip("hip", 6.4, 3.2, 1.6, "tile")]
    k["giwa_roof_hip_end"] = ("기와 우진각 끝", parts, "직선 지붕 끝, x=0에서 이어 붙임, 길이 3.2m")
    k["giwa_ridge_end"] = ("용마루 끝장식(치미)", [box("a", (0.5, 0.35, 0.5), (0, 0, 0.25), "tile"), box("b", (0.3, 0.3, 0.3), (0, 0, 0.65), "gold")], "용마루 양 끝")
    k["giwa_eave_flare"] = ("처마 끝 막새줄", [box(f"m{i}", (0.18, 0.3, 0.16), (-1.8 + i * 0.4, 0, 0.08), "tile") for i in range(10)] + [box("rim", (4, 0.12, 0.1), (0, 0.1, 0.05), "gold")], "처마 아래 가장자리 4m")
    # --- 초가 지붕
    k["choga_roof_straight"] = ("초가 지붕 직선", [prism("roof", 4, 5.6, 1.7, (0, 0, 0), "thatch"), cyl("roll", 0.2, 0.2, 4, (-2, 0, 1.72), "thatch", 6, rot=(0, math.pi / 2, 0))], "4m 짚지붕, 폭 5.6m")
    k["choga_roof_gable_end"] = ("초가 박공(끝)", [prism("cap", 0.6, 5.8, 1.72, (0.3, 0, 0), "thatch"), prism("gable", 0.12, 4.6, 1.2, (0.05, 0, 0), "mud")], "직선 지붕 끝, 0.6m")
    k["choga_roof_hip_end"] = ("초가 우진각 끝", [hip("hip", 5.6, 2.8, 1.7, "thatch")], "두 개를 맞대면 정사각 지붕, 길이 2.8m")
    k["choga_ridge_cap"] = ("용마루 새끼줄 얹기", [cyl("roll", 0.24, 0.24, 4, (-2, 0, 0.24), "wood", 6, rot=(0, math.pi / 2, 0))] + [box(f"tie{i}", (0.08, 0.6, 0.1), (-1.6 + i * 1.07, 0, 0.26), "wood_dark", rot=(0, 0, 0.6)) for i in range(4)], "용마루 덮개(새끼줄 엇질러 묶음)")
    return k

def build_piece(key):
    before = set(bpy.context.scene.objects)
    label, parts, note = K()[key]
    keep = set(parts)
    for o in list(set(bpy.context.scene.objects) - before - keep): bpy.data.objects.remove(o)   # 다른 조각은 지운다
    return join(f"hanok_{key}", parts), label, note

def export_all():
    rep = []; man = []
    for key in K():
        reset(); o, label, note = build_piece(key)
        lo, hi = bounds(o)
        r = {"name": f"hanok_{key}", "label": label, "note": note, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}
        export(o, os.path.join(OUT, "hanok", f"hanok_{key}.glb")); rep.append(r)
    json.dump({"grid_m": 4, "wall_height_m": H, "stack_z": {"gidan": 0, "wall": 0.5, "roof": 2.9}, "front": "-Y(내보내면 +Z)", "pieces": rep}, open(os.path.join(OUT, "hanok", "_kit_manifest.json"), "w"), ensure_ascii=False, indent=1)
    return rep

def place(key, x, y, z=0, rot=0):
    o, _, _ = build_piece(key); o.location = (x, y, z); o.rotation_euler = (0, 0, math.radians(rot)); return o

def demo():
    """조립 시험: 기와집(8×4m, 우진각 지붕)과 초가(4×4m)를 조각만으로 세운다."""
    reset()
    z0, zw, zr = 0, 0.5, 2.9
    # 기와집: 앞면 y=0, 뒷면 y=4, 옆면 x=±4. 중심 (0,0)에서 x -4..4
    for x in (-2, 2):
        place("gidan_straight", x, 0, 0); place("gidan_straight", x, 4, 0)
    for s in (-1, 1): place("gidan_straight", s * 4, 2, 0, 90)
    for x in (-4, 4):
        for y in (0, 4): place("gidan_corner", x, y, 0)
    place("wall_window", -2, 0, zw); place("door_double", 2, 0, zw)
    place("wall_plaster", -2, 4, zw, 180); place("wall_plaster", 2, 4, zw, 180)
    place("wall_plank", 4, 2, zw, 90); place("wall_plaster", -4, 2, zw, -90)
    for x in (-4, 0, 4):
        place("pillar_round", x, 0, zw); place("pillar_round", x, 4, zw)
    place("toenmaru_straight", -2, 0, 0); place("toenmaru_straight", 2, 0, 0); place("daetdol_step", 2, -1.3, 0)
    place("giwa_roof_straight", 0, 2, zr); place("giwa_roof_hip_end", 2, 2, zr); place("giwa_roof_hip_end", -2, 2, zr, 180)
    place("giwa_ridge_end", 3.0, 2, zr + 1.55)
    place("chimney", 5.6, 4.3, 0)
    # 초가: 오른쪽에 12m 떨어진 곳(x=14)
    cx = 14
    place("gidan_straight", cx, 0, 0); place("gidan_straight", cx, 4, 0)
    for s in (-1, 1): place("gidan_straight", cx + s * 2, 2, 0, 90)
    place("door_single", cx, 0, zw); place("wall_mud", cx, 4, zw, 180); place("wall_window", cx + 2, 2, zw, 90); place("wall_mud", cx - 2, 2, zw, -90)
    for sx in (-2, 2):
        for y in (0, 4): place("pillar_square", cx + sx, y, zw)
    place("choga_roof_hip_end", cx, 2, zr, 0); place("choga_roof_hip_end", cx, 2, zr, 180)
    place("saripmun", cx, -5, 0)
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    setup_render(26, (7, 1.5, 1.5), size=(1280, 720), ground_size=60)
    render(os.path.join(OUT, "previews", "hanok_kit_assembled_50deg.png"))
    return len(objs)

if __name__ == "__main__":
    rep = export_all()
    print(len(rep), "조각, 최대 삼각형", max(r["tris"] for r in rep), "최소 z", min(r["min_z"] for r in rep))
    print("조립 시험 조각 수:", demo())
