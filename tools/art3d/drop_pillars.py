"""장비 드롭 빛줄기 5종(M4): 바닥에 떨어진 장비 위로 서는 등급색 빛줄기. 높이 1.5/1.5/2.5/4/4 m.
왜 이렇게: 기획 명세는 높이 3단계(1.5/2.5/4 m)다. 색만으로 등급을 가르면 색약인 사람이 못 읽으므로 **꼭대기에 떠 있는 모양**도 등급마다 다르다.
 흔한 미색=동그라미 · 손본 청록=마름모 · 귀한 금빛=네 갈래 별 · 옛 차사 먹빛 남색=속 빈 도장 네모 · 이름 있는 주홍=세 뿔 관.
구조(기존 fx_pickup_pillar_* 와 같은 규칙): 반투명 빔 하나 + 속 발광 심 + 바닥 빛 고리 + 꼭대기 모양. 꼭대기 모양은 카메라(앞=-Y)를 보게 세워 둠. 원점=바닥 가운데.
실행: python3 drop_pillars.py → assets3d/fx/fx_drop_{common,refined,rare,antique,named}.glb, assets3d/fx/_drop_pillars.json, assets3d/previews/drop_pillars_50deg.png"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from interactables import disc

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
TIERS = [("common", "흔한", "#F3E7D3", 1.5), ("refined", "손본", "#4FA8A0", 1.5), ("rare", "귀한", "#D4A94E", 2.5), ("antique", "옛 차사", "#4A66C4", 4.0), ("named", "이름 있는", "#E85C41", 4.0)]

def top_mark(i, z, col):
    """꼭대기 모양(XZ 면에 세움, 앞을 보게 얇게). z=모양 중심 높이."""
    m = mat(col, 2.2); t = 0.045; p = []
    if i == 0: p.append(sphere("mark", 0.17, (0, 0, z), m, 12, 6, (1, 0.25, 1)))
    elif i == 1: p.append(box("mark", (0.26, t, 0.26), (0, 0, z), m, rot=(0, math.pi / 4, 0)))
    elif i == 2:
        p += [box("starV", (0.09, t, 0.46), (0, 0, z), m), box("starH", (0.46, t, 0.09), (0, 0, z), m), box("starD", (0.2, t, 0.2), (0, 0, z), m, rot=(0, math.pi / 4, 0))]
    elif i == 3:
        s, w = 0.34, 0.075
        p += [box("sqT", (s, t, w), (0, 0, z + s / 2 - w / 2), m), box("sqB", (s, t, w), (0, 0, z - s / 2 + w / 2), m), box("sqL", (w, t, s), (-s / 2 + w / 2, 0, z), m), box("sqR", (w, t, s), (s / 2 - w / 2, 0, z), m)]
    else:
        p += [box("crBase", (0.44, t, 0.08), (0, 0, z - 0.14), m)] + [cyl(f"crS{k}", 0.075, 0.0, h, (x, 0, z - 0.12), m, 4) for k, (x, h) in enumerate(((-0.16, 0.26), (0, 0.38), (0.16, 0.26)))]
    return p

def pillar(i):
    key, nm, col, h = TIERS[i]
    p = [cyl("beam", 0.16, 0.05, h, (0, 0, 0.02), mat_alpha(col, 0.26, 1.6), 8), cyl("beam_core", 0.05, 0.02, h - 0.1, (0, 0, 0.02), mat_alpha(col, 0.5, 2.4), 6), disc("ring", 0.32, 0.0, col, 0.015, 14, 0.6, 1.8)]
    return p + top_mark(i, h + 0.3, col)

def run():
    rep = []
    for i, (key, nm, col, h) in enumerate(TIERS):
        reset(); o = join(f"fx_drop_{key}", pillar(i)); lo, hi = bounds(o)
        export(o, os.path.join(OUT, "fx", f"fx_drop_{key}.glb"))
        rep.append({"name": f"fx_drop_{key}", "tier": nm, "color": col, "beam_height_m": h, "top_shape": ["동그라미", "마름모", "네 갈래 별", "속 빈 도장 네모", "세 뿔 관"][i], "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
    json.dump(rep, open(os.path.join(OUT, "fx", "_drop_pillars.json"), "w"), ensure_ascii=False, indent=1)
    reset()
    for i in range(5): o = join(f"p{i}", pillar(i)); o.location = ((i - 2) * 1.7, 0, 0)
    setup_render(9.0, (0, 0, 2.0), elev=38, size=(1500, 800), ground_size=30, night=True)
    bpy.context.scene.cycles.samples = 40; render(os.path.join(OUT, "previews", "drop_pillars_50deg.png"))
    return rep

if __name__ == "__main__":
    for r in run(): print(r["name"], r["beam_height_m"], r["top_shape"], r["tris"], r["size_m"])
