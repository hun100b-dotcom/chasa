"""한옥 조각 키트로 집 한 채를 세우는 '조립 설명서'(순수 파이썬, 블렌더 없이도 돈다).
왜 따로 두나: 마을 배치(solgogae_village.py)와 필드 배치(field_layout.py)가 같은 설명서를 쓰게 하려고.
좌표: 집 중심이 (0,0), 정면은 -Y(남쪽), 바닥 z=0. 조각 높이 규칙은 hanok_kit.py와 같다(기단 0 / 벽 0.5 / 지붕 2.9).
반환: [(조각이름, x, y, z, rot)] — 조각이름은 assets3d/hanok/hanok_<이름>.glb"""
import math
ZW, ZR = 0.5, 2.9

def _shift(lst, dy=-2.0): return [(k, x, y + dy, z, r) for k, x, y, z, r in lst]

def giwa8():
    """기와집 8×4m(우진각 지붕, 대청마루, 굴뚝)."""
    P = []
    for x in (-2, 2): P += [("gidan_straight", x, 0, 0, 0), ("gidan_straight", x, 4, 0, 0)]
    for s in (-1, 1): P.append(("gidan_straight", s * 4, 2, 0, 90))
    for x in (-4, 4):
        for y in (0, 4): P.append(("gidan_corner", x, y, 0, 0))
    P += [("wall_window", -2, 0, ZW, 0), ("door_double", 2, 0, ZW, 0), ("wall_plaster", -2, 4, ZW, 180), ("wall_plaster", 2, 4, ZW, 180), ("wall_plank", 4, 2, ZW, 90), ("wall_plaster", -4, 2, ZW, -90)]
    for x in (-4, 0, 4): P += [("pillar_round", x, 0, ZW, 0), ("pillar_round", x, 4, ZW, 0)]
    P += [("toenmaru_straight", -2, 0, 0, 0), ("toenmaru_straight", 2, 0, 0, 0), ("daetdol_step", 2, -1.3, 0, 0)]
    P += [("giwa_roof_straight", 0, 2, ZR, 0), ("giwa_roof_hip_end", 2, 2, ZR, 0), ("giwa_roof_hip_end", -2, 2, ZR, 180), ("giwa_ridge_end", 3.0, 2, ZR + 1.55, 0), ("chimney", 5.6, 4.3, 0, 0)]
    return _shift(P)

def choga4():
    """초가 4×4m(문 하나, 창 하나, 우진각 초가지붕)."""
    P = [("gidan_straight", 0, 0, 0, 0), ("gidan_straight", 0, 4, 0, 0)] + [("gidan_straight", s * 2, 2, 0, 90) for s in (-1, 1)]
    P += [("door_single", 0, 0, ZW, 0), ("wall_mud", 0, 4, ZW, 180), ("wall_window", 2, 2, ZW, 90), ("wall_mud", -2, 2, ZW, -90)]
    for sx in (-2, 2):
        for y in (0, 4): P.append(("pillar_square", sx, y, ZW, 0))
    P += [("choga_roof_hip_end", 0, 2, ZR, 0), ("choga_roof_hip_end", 0, 2, ZR, 180)]
    return _shift(P)

def choga8():
    """긴 초가 8×4m(방 둘: 문 둘). 지붕은 가운데 직선 + 양끝 우진각."""
    P = []
    for x in (-2, 2): P += [("gidan_straight", x, 0, 0, 0), ("gidan_straight", x, 4, 0, 0)]
    for s in (-1, 1): P.append(("gidan_straight", s * 4, 2, 0, 90))
    for x in (-4, 4):
        for y in (0, 4): P.append(("gidan_corner", x, y, 0, 0))
    P += [("door_single", -2, 0, ZW, 0), ("door_single", 2, 0, ZW, 0), ("wall_mud", -2, 4, ZW, 180), ("wall_window", 2, 4, ZW, 180), ("wall_mud", 4, 2, ZW, 90), ("wall_window", -4, 2, ZW, -90)]
    for x in (-4, 0, 4): P += [("pillar_square", x, 0, ZW, 0), ("pillar_square", x, 4, ZW, 0)]
    P += [("choga_roof_straight", 0, 2, ZR, 0), ("choga_roof_hip_end", 2, 2, ZR, 0), ("choga_roof_hip_end", -2, 2, ZR, 180), ("chimney", 5.6, 4.3, 0, 0)]
    return _shift(P)

def jeongja():
    """정자 4×4m: 기단 위 둥근 기둥 넷, 우진각 기와지붕, 벽 없음(앞에 댓돌). 사방이 트인 쉼터."""
    P = [("gidan_straight", 0, 0, 0, 0), ("gidan_straight", 0, 4, 0, 0)] + [("gidan_straight", s * 2, 2, 0, 90) for s in (-1, 1)]
    for sx in (-2, 2):
        for y in (0, 4): P.append(("pillar_round", sx, y, ZW, 0))
    P += [("giwa_roof_hip_end", 0, 2, ZR, 0), ("giwa_roof_hip_end", 0, 2, ZR, 180), ("daetdol_step", 0, -1.3, 0, 0)]
    return _shift(P)

def daejanggan():
    """대장간 4×4m: 초가 틀에서 앞(−Y)과 한쪽 옆을 터서 화덕 연기와 불빛이 바깥으로 나오게. 뒤·한쪽 벽만 흙벽, 굴뚝 하나."""
    P = [("gidan_straight", 0, 0, 0, 0), ("gidan_straight", 0, 4, 0, 0)] + [("gidan_straight", s * 2, 2, 0, 90) for s in (-1, 1)]
    P += [("wall_mud", 0, 4, ZW, 180), ("wall_mud", -2, 2, ZW, -90)]
    for sx in (-2, 2):
        for y in (0, 4): P.append(("pillar_square", sx, y, ZW, 0))
    P += [("choga_roof_hip_end", 0, 2, ZR, 0), ("choga_roof_hip_end", 0, 2, ZR, 180), ("chimney", -2.9, 4.3, 0, 0)]
    return _shift(P)

def donghun_burnt():
    """불탄 동헌 터 8×4m: 기단과 토막 난 벽 둘만 남고 지붕·기둥은 없다(기둥은 소품 '탄 기둥'을 따로 세운다). 앞 댓돌."""
    P = []
    for x in (-2, 2): P += [("gidan_straight", x, 0, 0, 0), ("gidan_straight", x, 4, 0, 0)]
    for s in (-1, 1): P.append(("gidan_straight", s * 4, 2, 0, 90))
    for x in (-4, 4):
        for y in (0, 4): P.append(("gidan_corner", x, y, 0, 0))
    P += [("wall_plaster", -2, 4, ZW, 180), ("wall_plank", 4, 2, ZW, 90), ("daetdol_step", 0, -1.3, 0, 0)]
    return _shift(P)

RECIPES = {"uiwon": giwa8, "giwa8": giwa8, "choga4": choga4, "choga8": choga8, "jeongja": jeongja, "daejanggan": daejanggan, "donghun_burnt": donghun_burnt}
FOOTPRINT = {"uiwon": (9, 5), "giwa8": (9, 5), "choga4": (5, 5), "choga8": (9, 5), "jeongja": (5, 5), "daejanggan": (5, 5), "donghun_burnt": (9, 5)}   # 겹침 검사용(가로, 세로, 기단 포함)

def place_building(kind, x, y, rot=0, gate=True):
    """집을 세계 좌표 (x,y), 방향 rot(반시계 도)로 옮긴 조각 목록을 돌려준다. 초가는 앞마당에 사립문을 단다."""
    parts = RECIPES[kind]()
    if gate and kind.startswith("choga"): parts.append(("saripmun", 0, -5.0, 0, 0))
    a = math.radians(rot); c, s = math.cos(a), math.sin(a)
    return [{"piece": f"hanok_{k}", "file": f"assets3d/hanok/hanok_{k}.glb", "x": round(x + px * c - py * s, 3), "y": round(y + px * s + py * c, 3), "z": z, "rot": (r + rot) % 360 if (r + rot) % 360 <= 180 else (r + rot) % 360 - 360}
            for k, px, py, z, r in parts]
