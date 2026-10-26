"""무기 기본 특성 '맞은 혼 표식' 3종(삼지창 고정·요령 둔화·붓 표식). 코드가 혼 발밑 원점(0,0,0)에 얹는다(키 약 1.3 m 기준, 거센 혼은 ×1.3 배율).
왜 이 모양인가
- 처결 대기 고리(바닥의 둥근 톱니 고리, 청록·노랑·갈색)와 헷갈리면 안 된다 → 셋 다 **둥글지 않고 위로 서는 모양**(기울어진 창, 어깨 멍에, 머리 위 획). 바닥에 고리·원판을 깔지 않는다.
- 24 m 폰(주인공 4 mm, 혼 몸 2.7 mm)에서도 읽혀야 한다 → 가장 얇은 부분도 굵게(자루 0.07 m), **먹빛 바깥 테두리**를 한 겹 더 두른다(어떤 바닥색에서도 모양이 선다). 주황은 파혼 전용이라 쓰지 않는다.
- 셋이 서로 갈리게: ① 고정 = 땅에 박힌 기울어진 창(긴 대각선 + 붉은 술) ② 둔화 = 어깨에 얹은 멍에와 놋쇠 방울 둘(옆으로 긴 가로선) ③ 붓 표식 = 머리 위 먹 획 1~3개(쌓이는 개수가 곧 표식 개수).
파일: fx_mark_pin(1초 고정) · fx_mark_slow(25% 둔화) · fx_mark_ink_1/2/3(표식 1~3개, 3개째는 '이름 쓰기' 준비 = 획 위에 금빛 점).
규약: 1유닛=1m, 원점=혼 발밑, 정면(카메라 쪽)=-Y. 발광 재질만(투명 없음). 실행: python3 fx_marks.py"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); UNITY = os.path.join(OUT, "..", "unity", "Assets", "Resources", "Models", "Fx")
INK = "#14141F"; CREAM = "#F3E7D3"; STEEL = "#DCE6F2"; BRASS = "#8E6B2E"; RED = "#C43428"; WOOD = "#8A6A44"; GOLD = "#FFD873"
EDGE = "#1A1410"      # 바깥 먹 테두리(미니맵 아이콘 테두리와 같은 색)

BACK = Vector((0.0, 0.05, -0.06))   # 테두리 사본을 카메라에서 먼 쪽(뒤·아래)으로 살짝 밀어 둔다 → 제 색 모양 둘레에 먹 테두리만 삐져나옴
def behind(parts):
    """테두리 사본을 뒤로 민다. 뒤집은 껍질(뒷면 컬링)에 기대지 않는 이유: GLB 재질이 엔진마다 컬링 설정이 달라 테두리가 몸을 덮어 버릴 수 있다."""
    for o in parts: o.location = o.location + BACK
    return parts
def layered(build):
    """같은 모양을 두 번 짓는다: 먼저 먹색으로 살짝 부풀려 뒤로 민 테두리 → 그 위에 제 색. build(g, edge): g는 부풀리는 양(m)."""
    return behind(build(0.035, True)) + build(0.0, False)

def pin(g, edge):
    """고정: 삼지창 머리를 땅에 박은 기울어진 창. 가로대에서 세 갈래가 아래로(땅 속으로) 박히고, 자루가 뒤쪽으로 15° 기울어 1.9 m까지 솟는다. 붉은 술이 자루 끝에서 흔들림."""
    m = lambda c, e=0.6: mat(EDGE if edge else c, 0.0 if edge else e)
    p = []; lean = math.radians(15); top = (0.0, 0.25 + 1.55 * math.sin(lean), 0.35 + 1.55 * math.cos(lean)); base = (0.0, 0.25, 0.35)
    p.append(limb("shaft", base, top, 0.07 + g, 0.06 + g, m(WOOD, 0.1), 6))
    p.append(box("guard", (0.62 + 2 * g, 0.12 + 2 * g, 0.1 + 2 * g), (0, 0.25, 0.37), m(STEEL), rot=(0, 0, 0)))
    for i, x in enumerate((-0.26, 0, 0.26)):
        p.append(cyl(f"tine{i}", 0.06 + g, 0.0, 0.42 + g, (x, 0.25, 0.33), m(STEEL), 5, rot=(math.pi, 0, 0)))   # 가로대에서 아래로 뾰족(끝이 땅 -0.09까지 박힘)
    p.append(limb("tassel", (top[0], top[1], top[2] - 0.05), (top[0] + 0.12, top[1] + 0.05, top[2] - 0.45), 0.09 + g, 0.04 + g, m(RED), 5))
    p.append(sphere("knob", 0.09 + g, top, m(STEEL), 6, 4))
    return p

def slow(g, edge):
    """둔화: 어깨에 얹은 멍에(가로 1.2 m, 가운데가 살짝 처짐) 양끝에 놋쇠 방울이 무겁게 늘어짐. 방울이 땅을 향해 늘어져 '짓눌림'으로 읽힌다."""
    m = lambda c, e=0.6: mat(EDGE if edge else c, 0.0 if edge else e)
    p = []; z0 = 1.02
    p.append(limb("yokeL", (-0.62, -0.05, z0 + 0.04), (0, -0.05, z0 - 0.04), 0.07 + g, 0.07 + g, m(WOOD, 0.2), 6)); p.append(limb("yokeR", (0, -0.05, z0 - 0.04), (0.62, -0.05, z0 + 0.04), 0.07 + g, 0.07 + g, m(WOOD, 0.2), 6))
    for sx in (-1, 1):
        x = sx * 0.58
        p.append(limb(f"cord{sx}", (x, -0.05, z0 + 0.04), (x, -0.05, z0 - 0.12), 0.03 + g, 0.03 + g, m(WOOD, 0.1), 4))
        p.append(cyl(f"bell{sx}", 0.24 + g, 0.11 + g, 0.36 + g, (x, -0.05, z0 - 0.5), m(BRASS, 0.7), 9))   # 아래가 넓은 종 모양(위 0.11 → 아래 0.24)
        p.append(sphere(f"clap{sx}", 0.06 + g, (x, -0.05, z0 - 0.52), m(WOOD, 0.1), 5, 3))
    return p

def ink(n, ready):
    """붓 표식: 머리 위 먹 획 n개(왼쪽에서 오른쪽, 길이가 조금씩 다름). 획 판은 카메라 쪽으로 38° 눕혀 위에서 봐도 납작하지 않다. 바깥은 한지색 테두리(검은 먹이 어두운 바닥에서도 보이게).
    ready(=3개)면 획 위에 금빛 점 하나('이름 쓰기' 준비)."""
    a = math.radians(38); sy, cz = math.sin(a), math.cos(a)
    def W(x, z): return (x, 1.95 * 0.0 + z * sy - 0.0, 1.55 + z * cz)       # 판 좌표(x,z) → 세계
    def build(g, edge):
        m = lambda c, e: mat(CREAM if edge else c, 0.9 if edge else e)
        p = []; spacing = 0.34
        for i in range(n):
            x = (i - (n - 1) / 2) * spacing; L = 0.58 + 0.1 * (i % 2); lean = 0.12 * (1 if i % 2 == 0 else -1)
            p.append(limb(f"stroke{i}", W(x - lean, -L / 2), W(x + lean, L / 2), 0.1 + g, 0.055 + g, m(INK, 0.0), 6))
            p.append(sphere(f"dot{i}", 0.11 + g, W(x - lean, -L / 2), m(INK, 0.0), 6, 4))
        if ready and not edge: p.append(sphere("gold", 0.09, W(0, 0.55), m(GOLD, 1.6), 6, 4))
        return p
    return behind(build(0.04, True)) + build(0.0, False)

MARKS = [("fx_mark_pin", lambda: layered(pin), "삼지창 고정(1초). 땅에 박힌 기울어진 창, 붉은 술"), ("fx_mark_slow", lambda: layered(slow), "요령 둔화(25%). 어깨 멍에 + 놋쇠 방울 둘"),
         ("fx_mark_ink_1", lambda: ink(1, False), "붓 표식 1개"), ("fx_mark_ink_2", lambda: ink(2, False), "붓 표식 2개"), ("fx_mark_ink_3", lambda: ink(3, True), "붓 표식 3개(이름 쓰기 준비, 금빛 점)")]

def run():
    rep = []
    for key, fn, note in MARKS:
        reset(); o = join(key, fn()); lo, hi = bounds(o); export(o, os.path.join(OUT, "fx", key + ".glb"))
        if os.path.isdir(UNITY): export(o, os.path.join(UNITY, key + ".glb"))
        rep.append({"name": key, "note": note, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "z_range": [round(lo.z, 2), round(hi.z, 2)]})
    json.dump(rep, open(os.path.join(OUT, "fx", "_fx_marks.json"), "w"), ensure_ascii=False, indent=1)
    return rep
if __name__ == "__main__":
    for r in run(): print(r)
