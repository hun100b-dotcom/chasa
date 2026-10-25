"""컷신 소품: B-02 월화(굿판·열두 잔·방울·부러진 부채·굿상·처마 등)와 B-03 서 의원(약장·붉은 인·번호 칸 바닥·씻은 붓·약봉지).
근거: 서사팀 cutscenes_b02/b03.json(커밋 3syw2s). 실행: python3 cutscene_props.py [이름 ...]
규약: 1단위=1m, 원점=바닥 한가운데(걸어두는 것은 아래 설명), 정면=-Y, 재질은 색만(빛나는 것은 발광).
여러 조각이 따로 움직여야 하는 소품은 GLB 안에 이름 붙은 노드로 나눈다(예: Drawer_BL 서랍만 밀려 나옴, Cup_12 엎어진 잔, Cell_r_c 칸 하나가 깜빡).
주황은 파혼 전용이라 쓰지 않고 붉은 인·붉은 칸은 포도주색 쪽 붉음(#B5473F)을 쓴다."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
RED = "#A33A3A"; CUP = "#E8E1D0"

def cup_parts(prefix="cup", flipped=False, at=(0, 0, 0), rot_z=0.0):
    """제기 잔: 낮은 굽 + 넓게 벌어진 사발. 높이 0.2m, 지름 0.34m. flipped면 엎어서 입이 바닥에 닿게 한다."""
    x, y, z = at
    if not flipped:
        return [cyl(f"{prefix}_foot", 0.08, 0.06, 0.07, (x, y, z), CUP, 8), cyl(f"{prefix}_bowl", 0.07, 0.17, 0.13, (x, y, z + 0.07), CUP, 10), cyl(f"{prefix}_rim", 0.17, 0.17, 0.015, (x, y, z + 0.19), "gold", 10)]
    # 엎은 잔: 입(지름 0.34)이 바닥, 굽이 위
    return [cyl(f"{prefix}_rim", 0.17, 0.17, 0.015, (x, y, z), "gold", 10), cyl(f"{prefix}_bowl", 0.17, 0.07, 0.13, (x, y, z + 0.015), CUP, 10), cyl(f"{prefix}_foot", 0.06, 0.08, 0.07, (x, y, z + 0.145), CUP, 8)]

def gut_floor():
    """둥근 굿판: 지름 12m 흙바닥 위 돌 테두리, 가장자리 반지름 5m에 열두 잔(시계 방향, 첫째=북쪽 12시, 열두째=11시 방향이 엎어짐). 높이 0.16m."""
    base = [cyl("floor", 6.05, 6.05, 0.16, (0, 0, 0), "dead", 24)]
    base += [box(f"rim{i}", (1.7, 0.34, 0.24), (6.2 * math.cos(i / 24 * math.tau), 6.2 * math.sin(i / 24 * math.tau), 0.12), "stone", rot=(0, 0, i / 24 * math.tau + math.pi / 2)) for i in range(24)]
    base += [cyl("center_ring", 1.4, 1.4, 0.02, (0, 0, 0.165), "stone_dark", 16)]
    parts = [("Floor", base)]
    for i in range(12):
        a = math.radians(90 - i * 30); x, y = 5.0 * math.cos(a), 5.0 * math.sin(a)
        base_obj = [cyl(f"ped{i}", 0.3, 0.26, 0.1, (x, y, 0.16), "stone_dark", 8)]
        parts.append((f"Pedestal_{i + 1:02d}", base_obj))
        parts.append((f"Cup_{i + 1:02d}", cup_parts(f"c{i}", flipped=(i == 11), at=(x, y, 0.26))))
    return {"parts": parts}

def gut_slots():
    """굿판 열두 칸의 '붉게 열리는 바닥' 자국: 잔 안쪽(반지름 4.1m)에 놓인 지름 1.5m 붉은 원판 12개. 코드가 칸별로 켜고 끈다(노드 Slot_01~12). 높이 0.02m, 굿판 바닥(윗면 0.16) 위에 얹는다."""
    parts = []
    for i in range(12):
        a = math.radians(90 - i * 30); x, y = 4.1 * math.cos(a), 4.1 * math.sin(a)
        parts.append((f"Slot_{i + 1:02d}", [cyl(f"s{i}", 0.75, 0.75, 0.02, (x, y, 0.17), mat(RED, 0.9), 12)]))
    return {"parts": parts}

def gut_cup(): return {"parts": [("Cup", cup_parts("cup"))]}
def gut_cup_flipped(): return {"parts": [("Cup", cup_parts("cup", flipped=True))]}

def gutsang():
    """굿상: 나무 상 1.6×0.9m 위에 접시 다섯(오방색 받침), 쌀 고깔, 과일, 촛대 둘(Light_gutsang). 앞가장자리에 오방 천 다섯 장. 높이 0.95m."""
    p = [box("top", (1.6, 0.9, 0.06), (0, 0, 0.72), "wood"), box("legL", (0.08, 0.7, 0.7), (-0.7, 0, 0.35), "wood_dark"), box("legR", (0.08, 0.7, 0.7), (0.7, 0, 0.35), "wood_dark")]
    cols = ["#3E64B0", "#E8C15A", "hanji", RED, "#2A2A38"]
    p += [cyl(f"plate{i}", 0.13, 0.13, 0.03, (-0.6 + i * 0.3, -0.2, 0.75), cols[i], 8) for i in range(5)]
    p += [cyl("rice", 0.15, 0.0, 0.2, (0.0, 0.15, 0.75), "hanji", 8)] + [sphere(f"fruit{i}", 0.06, (-0.5 + i * 0.12, 0.2, 0.82), "#B5473F" if i % 2 else "#E8C15A", 5, 4) for i in range(5)]
    for sx in (-1, 1): p += [cyl(f"candle{sx}", 0.03, 0.03, 0.22, (sx * 0.65, 0.25, 0.75), "hanji", 6), cyl(f"holder{sx}", 0.07, 0.04, 0.08, (sx * 0.65, 0.25, 0.75), "gold", 6), sphere(f"flame{sx}", 0.03, (sx * 0.65, 0.25, 0.99), mat("#FFD27A", 2.0), 4, 3, (1, 1, 1.6))]
    p += [box(f"cloth{i}", (0.2, 0.02, 0.5), (-0.64 + i * 0.32, -0.46, 0.45), cols[i]) for i in range(5)]
    return {"parts": [("Table", p)], "lights": [("Light_gutsang", (0, 0.25, 1.05), "#FFB066", 0.9, 8.0, True)]}

def bangul():
    """방울(칠성방울): 손잡이에 놋쇠 방울 여덟 개가 가지에 달림. 원점=손잡이 맨 아래(쥐는 자리). 높이 0.45m. 굴러 나갈 땐 코드가 눕혀 쓴다."""
    p = [cyl("handle", 0.022, 0.018, 0.2, (0, 0, 0), "wood_dark", 6), cyl("hub", 0.045, 0.045, 0.04, (0, 0, 0.2), "gold", 8)]
    for i in range(8):
        a = i / 8 * math.tau; x, y = 0.1 * math.cos(a), 0.1 * math.sin(a)
        p += [box(f"arm{i}", (0.1, 0.012, 0.012), (x / 2, y / 2, 0.22), "gold", rot=(0, 0, a)), sphere(f"bell{i}", 0.04, (x, y, 0.2), "gold", 6, 4), box(f"cord{i}", (0.01, 0.01, 0.06), (x, y, 0.27), RED)]
    return {"parts": [("Bell", p)]}

def salpuchae_broken():
    """살 부러진 오방 부채: 손잡이 아래 원점, 살 9개(길이 0.34m)가 오방색. 5번째·6번째 살은 빠졌고 3번째는 꺾여 짧다. 높이 0.5m, 폭 0.55m, XZ 면에 펼쳐짐(정면 -Y)."""
    cols = ["#3E64B0", "#E8C15A", "hanji", RED, "#2A2A38"]; p = [cyl("handle", 0.02, 0.016, 0.16, (0, 0, 0), "wood_dark", 6)]
    for i in range(9):
        if i in (5, 6): continue
        a = math.radians(-64 + i * 16); ln = 0.17 if i == 3 else 0.36
        p.append(box(f"rib{i}", (0.07, 0.012, ln), (math.sin(a) * ln / 2, 0, 0.16 + math.cos(a) * ln / 2), cols[i % 5], rot=(0, a, 0)))
    p.append(box("snapped", (0.02, 0.012, 0.16), (0.2, 0, 0.1), "wood_dark", rot=(0, 1.2, 0)))
    return {"parts": [("Fan", p)]}

def obang_scraps():
    """오방 천 조각 흩날림용: 오방색+붉은 천 조각 12장(0.28×0.45m)이 폭 2m 안에 흩어져 누움. 코드가 개별로 띄운다(노드 Scrap_01~12). 높이 0.05m."""
    cols = ["#3E64B0", "#E8C15A", "hanji", RED, "#2A2A38", RED]; parts = []
    for i in range(12):
        a = i * 2.4; r = 0.2 + 0.075 * i
        parts.append((f"Scrap_{i + 1:02d}", [box(f"sc{i}", (0.28, 0.45, 0.012), (r * math.cos(a), r * math.sin(a), 0.01 + 0.004 * i), cols[i % 6], rot=(0.15 * (i % 3 - 1), 0.1, a * 0.7))]))
    return {"parts": parts}

def _lift(parts, dz):
    for _, objs in parts:
        for o in objs: o.location.z += dz
    return parts

def eave_lamp():
    """처마 등(폐당집 두 번째 쉼터): 기둥 곁 벽에 거는 부속. 원점=벽판 아래가 아니라 등롱 맨 아래(전체가 바닥 0 위로 오게 올림). 코드는 이 소품을 기둥 높이 2.0m쯤에 붙이면 벽판이 2.57m까지 오른다. 벽판 높이 0.5m, 팔 끝에 사각 종이 등롱이 매달림. 노드 Lamp_frame(틀), Lamp_glow(켜짐 발광 — 코드가 재질을 바꿔 끄고 켬). Light_eave_lamp 1개. 전체 높이 1.07m."""
    frame = [box("plate", (0.3, 0.06, 0.5), (0, 0, 0.25), "wood_dark"), box("arm", (0.06, 0.6, 0.06), (0, -0.3, 0.45), "wood_dark"), box("chain", (0.015, 0.015, 0.35), (0, -0.6, 0.275), "iron"),
             box("capTop", (0.3, 0.3, 0.04), (0, -0.6, 0.075), "wood_dark"), box("capBot", (0.3, 0.3, 0.04), (0, -0.6, -0.55), "wood_dark")]
    frame += [box(f"post{i}", (0.025, 0.025, 0.58), (0.14 * (1 if i % 2 else -1), -0.6 + 0.14 * (1 if i // 2 else -1), -0.24), "wood_dark") for i in range(4)]
    glow = [box("paper", (0.26, 0.26, 0.55), (0, -0.6, -0.24), mat("#FFD27A", 1.6))]
    return {"parts": _lift([("Lamp_frame", frame), ("Lamp_glow", glow)], 0.57), "lights": [("Light_eave_lamp", (0, -0.6, 0.33), "#FFC878", 1.0, 9.0, True)]}

def post_lamp():
    """주막 기둥 등(B-03 끝 장면): 둥근 나무 기둥 2.8m, 윗부분에 걸린 등롱. 노드 Pillar, Lamp_frame, Lamp_glow. Light_post_lamp(따뜻한 노랑, 범위 10m)."""
    pil = [cyl("pillar", 0.16, 0.14, 2.8, (0, 0, 0), "pillar", 8), box("base", (0.5, 0.5, 0.12), (0, 0, 0.06), "stone"), box("bracket", (0.06, 0.5, 0.06), (0, -0.25, 2.4), "wood_dark")]
    frame = [box("cap", (0.3, 0.3, 0.04), (0, -0.5, 2.3), "wood_dark"), box("capB", (0.3, 0.3, 0.04), (0, -0.5, 1.78), "wood_dark")] + [box(f"p{i}", (0.025, 0.025, 0.52), (0.13 * (1 if i % 2 else -1), -0.5 + 0.13 * (1 if i // 2 else -1), 2.04), "wood_dark") for i in range(4)]
    return {"parts": [("Pillar", pil), ("Lamp_frame", frame), ("Lamp_glow", [box("paper", (0.24, 0.24, 0.5), (0, -0.5, 2.04), mat("#FFD27A", 1.6))])], "lights": [("Light_post_lamp", (0, -0.5, 2.04), "#FFC878", 1.0, 10.0, True)]}

def yakjang():
    """등짐 약장(석 단 두 칸 = 서랍 6개): 폭 0.62·깊이 0.34·높이 0.86m, 붉은 어깨끈 한 쌍. 원점=바닥 한가운데(등에 질 때는 코드가 등 뼈에 붙임).
    노드: Body(몸통·나머지 서랍·끈) / Drawer_BL(맨 아랫단 왼쪽 서랍 — 앞(-Y)으로 0.12m 밀렸다 들어감, 원점=서랍 앞면 가운데 아래) / Drawer_BL_glow(약점 표시 얇은 발광판, 코드가 켬)."""
    W, D, H = 0.62, 0.34, 0.86; body = [box("back", (W, 0.03, H), (0, D / 2 - 0.015, H / 2 + 0.05), "wood_dark"), box("sideL", (0.03, D, H), (-W / 2 + 0.015, 0, H / 2 + 0.05), "wood_dark"), box("sideR", (0.03, D, H), (W / 2 - 0.015, 0, H / 2 + 0.05), "wood_dark"),
                                       box("top", (W, D, 0.03), (0, 0, H + 0.035), "wood_dark"), box("bottom", (W, D, 0.03), (0, 0, 0.065), "wood_dark"), box("mid", (0.03, D, H), (0, 0, H / 2 + 0.05), "wood_dark")]
    dh = (H - 0.06) / 3
    for r in range(3):
        for c in range(2):
            if r == 0 and c == 0: continue          # 맨 아랫단 왼쪽(캐릭터 기준 +X)은 따로 노드
            x = (1 if c == 0 else -1) * (W / 4 - 0.005)
            body += [box(f"dr{r}{c}", (W / 2 - 0.04, 0.03, dh - 0.03), (x, -D / 2 + 0.015, 0.09 + dh * (r + 0.5)), "wood"), box(f"knob{r}{c}", (0.04, 0.03, 0.04), (x, -D / 2 - 0.01, 0.09 + dh * (r + 0.5)), "gold")]
    body += [box("strapL", (0.05, 0.4, 0.05), (0.2, D / 2 + 0.2, 0.78), RED), box("strapR", (0.05, 0.4, 0.05), (-0.2, D / 2 + 0.2, 0.78), RED), box("bandMid", (W + 0.04, 0.04, 0.05), (0, 0, 0.5), RED)]
    dx = W / 4 - 0.005; dz = 0.09 + dh * 0.5
    drawer = [box("front", (W / 2 - 0.04, 0.03, dh - 0.03), (0, 0, 0), "wood"), box("knob", (0.04, 0.03, 0.04), (0, -0.025, 0), "gold"), box("box", (W / 2 - 0.08, D - 0.06, dh - 0.08), (0, 0.17, 0), "wood_dark")]
    for o in drawer: o.location += Vector((dx, -D / 2 + 0.015, dz))
    glow = [box("glow", (W / 2 - 0.02, 0.01, dh - 0.01), (dx, -D / 2 - 0.012, dz), mat("#6FD6C0", 1.5))]
    return {"parts": [("Body", body), ("Drawer_BL", drawer), ("Drawer_BL_glow", glow)]}

def tanggeon():
    """탕건(의원 모자): 두 단 무늬 있는 검은 말총 모자. 지름 0.24·높이 0.2m, 원점=머리 닿는 아래. 기운 모양은 코드가 7~10도 기울여 쓴다."""
    return {"parts": [("Hat", [cyl("band", 0.12, 0.12, 0.05, (0, 0, 0), "hat", 10), cyl("low", 0.115, 0.1, 0.09, (0, 0, 0.05), "hat", 10), cyl("up", 0.075, 0.06, 0.08, (0, 0, 0.14), "iron", 8), cyl("tie", 0.125, 0.125, 0.012, (0, 0, 0.025), "#5A4630", 10)])]}

def brush_dry():
    """희게 마른 붓: 대 자루 0.2m와 하얗게 굳은 붓털. 원점=자루 아래, 눕혀서 서랍 감초 위에 놓는다."""
    return {"parts": [("Brush", [cyl("shaft", 0.011, 0.009, 0.2, (0, 0, 0), "bamboo", 6), cyl("ferrule", 0.013, 0.013, 0.03, (0, 0, 0.2), "gold", 6), cyl("hair", 0.012, 0.0, 0.07, (0, 0, 0.23), "hanji", 6)])]}

def gamcho_pile():
    """감초 더미: 갈색 뿌리토막 18개와 마른 풀잎. 폭 0.4m 높이 0.12m. 약장 서랍·바닥에 쏟아진 모양에 쓴다."""
    rng = [(math.cos(i * 2.1) * 0.12 * (1 + i % 3 * 0.35), math.sin(i * 2.1) * 0.1 * (1 + i % 2 * 0.4)) for i in range(18)]
    p = [box(f"root{i}", (0.16, 0.025, 0.025), (x, y, 0.02 + 0.006 * i), "#8A6B4A" if i % 3 else "#A88A5A", rot=(0, 0.2 * (i % 4 - 1.5), i * 0.9)) for i, (x, y) in enumerate(rng)]
    return {"parts": [("Pile", p)]}

def potion_bottle():
    """회복약 병: 배불뚝이 병에 붉은 마개, 병 속은 연한 연두빛(약탕과 같은 계열) 발광. 높이 0.2m, 지름 0.12m. 다섯 병은 코드가 복제해 굴린다."""
    return {"parts": [("Bottle", [sphere("body", 0.07, (0, 0, 0.07), "jar", 8, 5, (1, 1, 0.95)), cyl("neck", 0.03, 0.025, 0.07, (0, 0, 0.13), "jar", 6), cyl("cork", 0.032, 0.032, 0.04, (0, 0, 0.2), RED, 6), sphere("liquid", 0.055, (0, 0, 0.065), mat("#8BD6A0", 0.9), 7, 4, (1, 1, 0.9))])]}

def yakbongji():
    """약봉지 묶음: 한지 봉지 세 개를 붉은 끈으로 묶음. 0.14×0.1×0.12m. 파혼 장면에 흩날리는 것을 복제해 쓴다."""
    p = [box(f"pk{i}", (0.13, 0.09, 0.045), (0.005 * i, 0, 0.0225 + 0.046 * i), "hanji", rot=(0, 0, 0.18 * i)) for i in range(3)] + [box("string", (0.02, 0.1, 0.14), (0, 0, 0.07), RED), box("tag", (0.04, 0.012, 0.05), (0.04, -0.06, 0.1), "yellow_cloth")]
    return {"parts": [("Packets", p)]}

def seal_red():
    """붉은 인(명부 이름 옆 도장 자국): 한 변 0.9m 정사각, 두께 0.03m, 붉은 발광(포도주색). 안쪽에 어두운 '井' 모양 새김. XY 면에 눕혀 만들었으니 머리 위에 세울 땐 코드가 X 90°로 세운다(정면=위)."""
    p = [box("plate", (0.9, 0.9, 0.03), (0, 0, 0.015), mat(RED, 0.8))]
    p += [box(f"cutH{i}", (0.7, 0.06, 0.012), (0, -0.14 + i * 0.28, 0.034), "ink") for i in range(2)] + [box(f"cutV{i}", (0.06, 0.7, 0.012), (-0.14 + i * 0.28, 0, 0.034), "ink") for i in range(2)]
    return {"parts": [("Seal", p)]}

def seal_empty():
    """빈 인 자리(흐릿한 틀): 한 변 0.9m 얇은 테두리 네 변, 어두운 붉은 약한 발광. 붉은 인이 '앉기' 전·떨리다 꺼질 때 쓴다(seal_red와 같은 크기·방향)."""
    c = mat("#6E3A3A", 0.5)
    return {"parts": [("Frame", [box("t", (0.9, 0.06, 0.012), (0, 0.42, 0.006), c), box("b", (0.9, 0.06, 0.012), (0, -0.42, 0.006), c), box("l", (0.06, 0.9, 0.012), (-0.42, 0, 0.006), c), box("r", (0.06, 0.9, 0.012), (0.42, 0, 0.006), c)])]}

def ledger_open():
    """펼친 명부(저승 장부): 흰 쪽 둘이 살짝 들린 책, 어두운 표지, 이름 줄 6줄 + 오른쪽 맨 아랫줄 끝에 인 자리. 폭 1.1·깊이 0.8m, 높이 0.1m. 공중에 띄워 쓴다."""
    p = [box("cover", (1.14, 0.84, 0.03), (0, 0, 0.015), "ink"), box("pageL", (0.52, 0.76, 0.03), (-0.28, 0, 0.05), "hanji", rot=(0, -0.06, 0)), box("pageR", (0.52, 0.76, 0.03), (0.28, 0, 0.05), "hanji", rot=(0, 0.06, 0)), box("spine", (0.06, 0.8, 0.05), (0, 0, 0.04), "wood_dark")]
    p += [box(f"line{i}", (0.34, 0.025, 0.006), (0.28 + (0.05 if i % 2 else 0), 0.28 - i * 0.1, 0.075), "ink") for i in range(6)] + [box(f"lineL{i}", (0.34, 0.02, 0.006), (-0.28, 0.28 - i * 0.12, 0.075), "#5A4630") for i in range(5)]
    p += [box("sealSpot", (0.1, 0.1, 0.008), (0.43, -0.3, 0.075), mat("#6E3A3A", 0.5))]
    return {"parts": [("Ledger", p)]}

def number_grid():
    """번호 부르기 칸 바닥(서 의원 마당): 5줄×5칸, 칸 하나 1.8m, 전체 9.5m. 노드 Lines(흐린 선)와 Cell_r_c(r=0 남쪽 줄~4 북쪽 줄, c=0 서쪽~4 동쪽) 25개. 칸은 붉은 발광판(높이 0.02m)이라 코드가 평소 숨기고 하나씩 깜빡인다."""
    S = 1.9; o = -2 * S; lines = []
    for i in range(6): lines += [box(f"h{i}", (5 * S, 0.06, 0.012), (0, o - S / 2 + i * S, 0.006), mat("#7A6A5A", 0.25)), box(f"v{i}", (0.06, 5 * S, 0.012), (o - S / 2 + i * S, 0, 0.006), mat("#7A6A5A", 0.25))]
    parts = [("Lines", lines)]
    for r in range(5):
        for c in range(5): parts.append((f"Cell_{r}_{c}", [box(f"cl{r}{c}", (S - 0.18, S - 0.18, 0.02), (o + c * S, o + r * S, 0.012), mat(RED, 0.9))]))
    return {"parts": parts}

KIT = [("gut_floor", gut_floor, "굿판(열두 잔 포함)"), ("gut_slots", gut_slots, "굿판 붉은 열림 12칸"), ("gut_cup", gut_cup, "제기 잔"), ("gut_cup_flipped", gut_cup_flipped, "엎어진 잔"), ("gutsang", gutsang, "굿상"), ("bangul", bangul, "방울"),
       ("salpuchae_broken", salpuchae_broken, "살 부러진 부채"), ("obang_scraps", obang_scraps, "오방 천 조각"), ("eave_lamp", eave_lamp, "처마 등"), ("post_lamp", post_lamp, "주막 기둥 등"), ("yakjang", yakjang, "등짐 약장"), ("tanggeon", tanggeon, "탕건"),
       ("brush_dry", brush_dry, "마른 붓"), ("gamcho_pile", gamcho_pile, "감초 더미"), ("potion_bottle", potion_bottle, "회복약 병"), ("yakbongji", yakbongji, "약봉지"), ("seal_red", seal_red, "붉은 인"), ("seal_empty", seal_empty, "빈 인 자리"),
       ("ledger_open", ledger_open, "펼친 명부"), ("number_grid", number_grid, "번호 부르기 칸 바닥")]

def assemble(key, fn):
    """조각 목록 → 노드 이름이 붙은 오브젝트들(루트 빈 오브젝트 아래). 조각이 하나뿐이면 단일 메시."""
    d = fn(); parts = d["parts"]
    if len(parts) == 1:
        o = join(f"prop_{key}", parts[0][1]); root = o
    else:
        root = bpy.data.objects.new(f"prop_{key}", None); bpy.context.collection.objects.link(root)
        for nm, objs in parts:
            o = join(nm, objs); o.parent = root
    for n, pos, col, it, rg, fl in d.get("lights", []): light_empty(root, n, pos, col, intensity=it, range_m=rg, flicker=fl)
    return root, parts

def stats(root):
    ms = [root] if root.type == "MESH" else [c for c in root.children_recursive if c.type == "MESH"]
    pts = [m.matrix_world @ Vector(c) for m in ms for c in m.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return {"tris": sum(tris(m) for m in ms), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3), "nodes": [m.name for m in ms] if len(ms) > 1 else []}

def build(key, fn):
    reset(); root, parts = assemble(key, fn); st = stats(root)
    export(root, os.path.join(OUT, "props", f"prop_{key}.glb"))
    return {"name": f"prop_{key}", **st}

if __name__ == "__main__":
    want = sys.argv[1:]; res = [build(k, f) for k, f, n in KIT if not want or k in want]
    for r in res: print(r["name"], r["tris"], r["size_m"], "min_z", r["min_z"], len(r["nodes"]), "노드")
    if not want:
        json.dump(res, open(os.path.join(OUT, "props", "_report_cutscene.json"), "w"), ensure_ascii=False, indent=1)
        # 점검 사진: 큰 것(굿판·칸 바닥)은 따로, 작은 것은 한 장에 모아
        small = [(k, f) for k, f, n in KIT if k not in ("gut_floor", "gut_slots", "number_grid", "post_lamp", "yakjang")]
        for name, items, ortho, sz in (("cutscene_props_small", small, 7.2, (1400, 800)), ("cutscene_props_big", [("yakjang", yakjang), ("post_lamp", post_lamp), ("gutsang", gutsang)], 6.0, (1200, 600))):
            reset()
            for i, (k, f) in enumerate(items):
                root, _ = assemble(k, f); root.location = ((i % 6 - 2.5) * 1.0 if name.endswith("small") else (i - 1) * 2.0, -(i // 6) * 1.1 if name.endswith("small") else 0, 0)
            setup_render(ortho, (0, -0.4 if name.endswith("small") else 0, 0.5), elev=35, size=sz, ground_size=30); bpy.context.scene.cycles.samples = 24; render(os.path.join(OUT, "previews", name + ".png"))
        reset(); r1, _ = assemble("gut_floor", gut_floor); r2, _ = assemble("gut_slots", gut_slots)
        for c in r2.children: c.location.z += 0.0
        setup_render(14.5, (0, 0, 0), elev=50, size=(1100, 800), ground_size=40); bpy.context.scene.cycles.samples = 24; render(os.path.join(OUT, "previews", "cutscene_gut_floor.png"))
        reset(); assemble("number_grid", number_grid); setup_render(12, (0, 0, 0), elev=50, size=(900, 700), ground_size=30); bpy.context.scene.cycles.samples = 24; render(os.path.join(OUT, "previews", "cutscene_number_grid.png"))
