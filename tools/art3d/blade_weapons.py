"""날붙이 무기 2종: 환도(검)와 월도(도). 철삭·방망이 등 기존 5종과 같은 규약을 따른다.
규약: GLB, 1유닛=1m, 원점=쥐는 곳(손바닥 한가운데), 무기의 '긴 방향'이 블렌더 +Z(glTF에서는 +Y).
날(칼날)은 블렌더 +X 쪽이 '날 선 쪽', -X 쪽이 '등(칼등)'이다. 끝은 등 쪽(-X)으로 살짝 휘어 오른다(진짜 휜 칼과 같은 방향).
왜 직접 만드나: 칼날은 납작하고 휘어 있어 기존 원기둥 도구로는 그릴 수 없어서, 단면이 삼각형인 '날 전용 도구'(blade)를 따로 둔다.
IP: 환도·월도는 조선 시대 실제 병장기라 공유 자산이다(특정 작품의 무기 모양을 따르지 않았다)."""
import bpy, math
import bpy, bmesh
from lib3d import *
import lib3d


def blade(name, stations, material, edge_mat=None):
    """칼날 한 장. stations=[(z 높이, 반폭 w, 등 두께 t, 휨 x), ...] 아래→위. 마지막 점의 w=0이면 뾰족한 끝.
    단면은 삼각형: 날 선 쪽(+X)은 얇은 선, 등 쪽(-X)은 두께 t. 면이 적어 로우폴리를 지킨다."""
    bm = bmesh.new(); rows = []
    for z, w, t, cx in stations:
        if w <= 0:
            rows.append([bm.verts.new((cx, 0, z))]); continue
        rows.append([bm.verts.new((cx + w, 0, z)), bm.verts.new((cx - w, t, z)), bm.verts.new((cx - w, -t, z))])
    for a, b in zip(rows, rows[1:]):
        if len(a) == 3 and len(b) == 3:
            for k in range(3):
                k2 = (k + 1) % 3
                bm.faces.new([a[k], a[k2], b[k2], b[k]])
        elif len(a) == 3 and len(b) == 1:
            for k in range(3):
                bm.faces.new([a[k], a[(k + 1) % 3], b[0]])
    bm.faces.new(list(reversed(rows[0])))      # 아래 뚜껑(손잡이 쪽, 눈에 안 띔)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return lib3d._obj(name, bm, material)


def curve_x(t, bow):
    """날 길이 비율 t(0~1)에서 등 쪽(-X)으로 휜 양. 끝으로 갈수록 크게 휜다."""
    return -bow * t * t


def hwando():
    """환도: 허리에 차는 휜 외날 칼. 날 1.0m(휨 8cm, 반폭 4cm: 로우폴리 화면에서도 칼로 읽히게 실제보다 굵게), 고리 모양 날밑, 붉은 끈 감은 손잡이, 놋 머리, 늘어진 붉은 술(수술).
    쥐는 곳(원점)=손잡이 한가운데. 키 1.0m 안쪽."""
    p = []
    # 손잡이(자루): 나무 + 붉은 끈 감기 + 놋 머리
    p.append(cyl("grip", 0.027, 0.03, 0.2, (0, 0, -0.12), "wood_dark", 6))
    for i in range(5): p.append(cyl(f"wrap{i}", 0.032, 0.032, 0.012, (0, 0, -0.105 + i * 0.038), "red", 6))
    p.append(cyl("pommel", 0.036, 0.03, 0.035, (0, 0, -0.165), "gold", 6))
    p.append(sphere("ring_end", 0.02, (0, 0.0, -0.19), "gold", 5, 4))
    # 날밑(고리형): 납작한 원판 + 양옆 돌기. 환도의 둥근 날밑을 단순화
    p.append(cyl("guard", 0.06, 0.06, 0.014, (0, 0, 0.085), "gold", 8))
    p.append(cyl("habaki", 0.032, 0.026, 0.05, (0, 0, 0.1), "gold", 6))
    # 날: 0.15m부터 0.99m까지. 등 쪽으로 6cm 휨. 끝에서 4분의 1은 양날처럼 살짝 넓어졌다 좁아진다(조선 환도의 칼끝 모양)
    st = [(0.15, 0.03, 0.012, 0.0), (0.45, 0.04, 0.012, curve_x(0.3, 0.08)), (0.75, 0.042, 0.011, curve_x(0.6, 0.08)), (1.0, 0.038, 0.01, curve_x(0.85, 0.08)), (1.14, 0.0, 0.0, curve_x(1.0, 0.08))]
    p.append(blade("blade", st, "silver"))
    # 칼등을 따라 푸른빛 홈줄 한 줄(천도빛 아님, 그냥 강철 반사 느낌의 밝은 줄)
    p.append(box("fuller", (0.008, 0.004, 0.56), (-0.014, 0.0, 0.6), "chain"))
    # 늘어진 붉은 술(수술)
    for i, dx in enumerate((-0.012, 0.0, 0.012)):
        p.append(limb(f"tassel{i}", (dx, 0.03, -0.18), (dx * 2, 0.04, -0.34 - 0.02 * (i == 1)), 0.01, 0.006, "red", 4))
    return p


def wolgeom():
    """월도: 긴 자루 끝에 넓고 휜 외날 큰 칼날(언월도 계열의 조선 병장기). 자루 1.7m + 날 0.62m, 총길이 약 2.3m.
    쥐는 곳(원점)은 자루 아래쪽 3분의 1 지점이라 날은 위로 1.1m 떨어져 있어 묵직하게 휘둘리는 맛이 난다.
    날은 폭이 넓어(반폭 8cm) 한눈에 '창이 아니라 도'로 읽히고, 등에는 미늘 두 개와 붉은 술, 아래 끝에는 쇠 뒤끝이 달린다."""
    p = []
    # 자루: 나무 선반(가운데가 조금 굵음) + 쥐는 곳 천 감기 + 쇠 고리 두 개
    p.append(lathe("shaft", [(-0.62, 0.026), (0.0, 0.03), (0.6, 0.029), (1.1, 0.026)], 8, "wood"))
    p.append(cyl("gripwrap", 0.034, 0.034, 0.3, (0, 0, -0.18), "wood_dark", 8))
    for i in range(5): p.append(cyl(f"gw{i}", 0.036, 0.036, 0.012, (0, 0, -0.16 + i * 0.058), "red", 8))
    for zb in (0.35, 0.8): p.append(cyl(f"ring{int(zb*100)}", 0.034, 0.034, 0.022, (0, 0, zb), "iron", 8))
    p.append(lathe("butt", [(-0.62, 0.034), (-0.67, 0.03), (-0.78, 0.0)], 6, "iron"))      # 쇠 뒤끝(땅에 꽂는 부분)
    # 날 물림(놋 목)과 칼날 밑동
    p.append(lathe("socket", [(1.08, 0.03), (1.12, 0.05), (1.22, 0.05), (1.27, 0.032)], 8, "gold"))
    p.append(cyl("collar", 0.056, 0.056, 0.016, (0, 0, 1.17), "gold", 8))
    # 큰 날: 밑동에서 넓어졌다가 끝으로 갈수록 등 쪽(-X)으로 휘며 뾰족. 반폭 최대 8cm
    st = [(1.26, 0.03, 0.014, 0.0), (1.34, 0.06, 0.016, curve_x(0.12, 0.10)), (1.48, 0.08, 0.016, curve_x(0.38, 0.10)), (1.62, 0.075, 0.014, curve_x(0.65, 0.10)),
          (1.80, 0.05, 0.012, curve_x(0.9, 0.10)), (1.88, 0.0, 0.0, curve_x(1.0, 0.10))]
    p.append(blade("blade", st, "silver"))
    p.append(box("fuller", (0.012, 0.006, 0.4), (-0.03, 0.0, 1.5), "chain"))                 # 날 가운데 홈줄
    # 등의 미늘(톱니 모양 돌기) 두 개 — 월도의 상징적인 등 장식
    for i, zz in enumerate((1.42, 1.56)):
        p.append(limb(f"spine{i}", (-0.075, 0, zz), (-0.145, 0, zz + 0.045), 0.02, 0.0, "iron", 4))
    # 붉은 술 + 매듭
    p.append(sphere("knot", 0.03, (0.0, 0.0, 1.06), "red", 6, 4))
    for i, dx in enumerate((-0.03, 0.0, 0.03)):
        p += [limb(f"ts{i}", (dx, 0.0, 1.05), (dx * 2.2, 0.03, 0.86 - 0.05 * (i == 1)), 0.016, 0.01, "red", 4)]
    return p


W = [("weapon_hwando", "환도", hwando, "Hand.R", "검 계열. 빠른 4연타. 칼날 +X=날 선 쪽, 끝은 등 쪽(-X)으로 휨"),
     ("weapon_wolgeom", "월도", wolgeom, "Hand.R", "도 계열. 넓고 무거운 3연타. 쥐는 곳에서 날까지 1.1m")]

if __name__ == "__main__":
    import json, os
    OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
    rep = []
    for key, ko, fn, bone, note in W:
        reset(); o = join(key, fn()); lo, hi = bounds(o)
        rep.append({"name": key, "label": ko, "tris": tris(o), "length_m": round(hi.z - lo.z, 2), "z_range_m": [round(lo.z, 2), round(hi.z, 2)], "width_m": round(max(hi.x - lo.x, hi.y - lo.y), 2),
                    "socket": {"bone": bone, "position_in_bone_m": [0, 0, 0], "blade_axis_in_file": "+Y(glTF 위쪽)", "aim_blade_to": "캐릭터 앞(+Z glTF)", "rotate_deg_x": 90, "hero_hand_R_rest_pos_m": [-0.52, 0.87, 0.0]}, "note": note})
        export(o, os.path.join(OUT, "weapons", f"{key}.glb"))
    reset()
    for i, (key, ko, fn, bone, note) in enumerate(W):
        o = join(key, fn()); o.rotation_euler = (math.radians(90), 0, 0); o.location = ((i - 0.5) * 2.4, 0, 0.9)
    setup_render(8.0, (0, 0, 1.0), size=(900, 420), ground_size=14)
    render(os.path.join(OUT, "previews", "weapons_blades_50deg.png"))
    json.dump({"note": "원점=쥐는 곳. socket 참고", "weapons": rep}, open(os.path.join(OUT, "weapons", "_blade_weapons_manifest.json"), "w"), ensure_ascii=False, indent=1)
    for r in rep: print(r["name"], r["tris"], r["length_m"], r["width_m"])
