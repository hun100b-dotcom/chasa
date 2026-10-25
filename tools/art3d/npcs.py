"""1막 마을 사람(NPC) 17명 → 21개 GLB (뼈대+동작 포함). 실행: python3 npcs.py [--sheets] [id ...]
왜 이렇게: 서사팀 npc_act1.json에는 생김새 칸이 없다. 그래서 '한복 몸통 틀 몇 가지(남/여/노인/아이)'에 색과 소품만 바꿔 끼우는 방식으로 만든다.
 - 뼈대는 주인공과 같은 16개 이름(Root~Foot.R). 팔이 아래로 내려온 자세라서 주인공의 걷기 키를 그대로 쓴다.
 - 동작 4개(60fps): Idle(숨쉬기) / Walk(걷기) / Talk(말하며 손짓) / Work(망치질·일하는 손짓).
 - 치마·도포처럼 다리를 덮는 옷은 걸음 폭을 줄여(0.55배) 다리가 옷을 뚫고 나오는 걸 줄인다.
 - 단위 m, 원점=발바닥 한가운데, 정면 -Y(블렌더)=+Z(glTF), 캐릭터 왼쪽=+X. 화면에 주인공 이름은 쓰지 않는다.
 - 주황은 파혼 전용이라 옷 색에 쓰지 않는다(붉은 계열은 포도주색 쪽으로)."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import rig, to_group
import anim, hero_anim
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
DARK = "#1A1A22"

# ── 몸 크기 배율 도우미: 모든 길이에 k를 곱해 같은 틀로 아이·어른을 만든다 ─────────────────────────
class K:
    def __init__(s, k): s.k = k
    def v(s, t): return tuple(a * s.k for a in t)
    def box(s, n, size, loc, m, rot=(0, 0, 0)): return box(n, s.v(size), s.v(loc), m, rot)
    def cyl(s, n, r1, r2, h, base, m, segs=8, rot=(0, 0, 0)): return cyl(n, r1 * s.k, r2 * s.k, h * s.k, s.v(base), m, segs, rot)
    def sph(s, n, r, c, m, segs=7, rings=5, scale=(1, 1, 1), rot=(0, 0, 0)): return sphere(n, r * s.k, s.v(c), m, segs, rings, scale, rot)

A_ARM = 0.12   # 팔이 몸에서 벌어진 각도(라디안): 거의 내려온 자세
def npc_bones(k, wide=1.0):
    """주인공 BONES와 이름·구조 같고 팔만 아래로 내려온 모양. 키 배율 k."""
    sx = 0.25 * wide; ex = sx + 0.42 * math.sin(A_ARM); ez = 1.4 - 0.42 * math.cos(A_ARM)
    B = [("Root", None, (0, 0, 0), (0, 0, 0.12)), ("Hips", "Root", (0, 0, 0.95), (0, 0, 1.05)), ("Spine", "Hips", (0, 0, 1.05), (0, 0, 1.25)),
         ("Chest", "Spine", (0, 0, 1.25), (0, 0, 1.45)), ("Neck", "Chest", (0, 0, 1.45), (0, 0, 1.52)), ("Head", "Neck", (0, 0, 1.52), (0, 0, 1.95)),
         ("UpperArm.L", "Chest", (sx, 0, 1.4), (ex, 0, ez)), ("Hand.L", "UpperArm.L", (ex, 0, ez), (ex + 0.01, 0, ez - 0.1)),
         ("UpperArm.R", "Chest", (-sx, 0, 1.4), (-ex, 0, ez)), ("Hand.R", "UpperArm.R", (-ex, 0, ez), (-ex - 0.01, 0, ez - 0.1)),
         ("UpperLeg.L", "Hips", (0.13, 0, 0.95), (0.13, 0, 0.5)), ("LowerLeg.L", "UpperLeg.L", (0.13, 0, 0.5), (0.13, 0, 0.09)), ("Foot.L", "LowerLeg.L", (0.13, 0, 0.09), (0.13, -0.2, 0.02)),
         ("UpperLeg.R", "Hips", (-0.13, 0, 0.95), (-0.13, 0, 0.5)), ("LowerLeg.R", "UpperLeg.R", (-0.13, 0, 0.5), (-0.13, 0, 0.09)), ("Foot.R", "LowerLeg.R", (-0.13, 0, 0.09), (-0.13, -0.2, 0.02))]
    return [(n, p, tuple(a * k for a in h), tuple(a * k for a in t)) for n, p, h, t in B]

def ring_xz(K_, name, c, r, n, size, m, y=0.0):
    """XZ 면에 놓인 고리(밧줄 감은 모양): 작은 상자 n개를 원 둘레에 접선 방향으로 놓는다."""
    out = []
    for i in range(n):
        t = i / n * math.tau
        out.append(K_.box(f"{name}{i}", size, (c[0] + r * math.cos(t), c[1] + y, c[2] + r * math.sin(t)), m, rot=(0, -t - math.pi / 2, 0)))
    return out

# ── 소품(손·허리·등에 끼우는 것). 함수(K_, H, add)가 뼈 이름별로 add 한다. H=손 위치(L/R, 키 배율 전 좌표) ─────────
def pr_cane(K_, H, add):
    x, y, z = H["R"]; add("Hand.R", K_.cyl("cane", 0.028, 0.022, 1.1, (x, y - 0.03, 0.0), "wood", 5), K_.sph("caneTop", 0.04, (x, y - 0.03, 1.1), "wood", 5, 4))

def pr_fan_broken(K_, H, add):
    """부러진 부채: 오방색 살 7개 중 하나는 빠지고 하나는 꺾여 짧다(당할미)."""
    x, y, z = H["R"]; cols = ["#3E64B0", "#E8C15A", "hanji", "#B5473F", "#2A2A38"]; parts = []
    for i, a in enumerate((-0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9)):
        if i == 4: continue                      # 빠진 살
        ln = 0.14 if i == 2 else 0.3             # 꺾여 짧아진 살
        parts.append(K_.box(f"rib{i}", (0.035, 0.012, ln), (x + math.sin(a) * ln / 2, y - 0.1, z + 0.02 + math.cos(a) * ln / 2), cols[i % 5], rot=(0, a, 0)))
    add("Hand.R", *parts)

def pr_cross_cloth(K_, H, add):
    """오방색 천을 어깨에서 허리로 가로질러 맨 무녀 차림."""
    add("Chest", *[K_.box(f"sash{i}", (0.035, 0.03, 0.58), (-0.06 + i * 0.035, -0.205, 1.18), c, rot=(0, 0.62, 0)) for i, c in enumerate(["#3E64B0", "#E8C15A", "hanji", "#B5473F", "#2A2A38"])])

def pr_rope_coil(K_, H, add):
    """줄배 줄: 왼손에 걸린 밧줄 타래와 늘어진 끝."""
    x, y, z = H["L"]; add("Hand.L", *ring_xz(K_, "coil", (x, y - 0.08, z - 0.12), 0.15, 10, (0.09, 0.05, 0.05), "thatch"), *ring_xz(K_, "coil2", (x, y - 0.08, z - 0.12), 0.11, 8, (0.08, 0.05, 0.05), "thatch", y=0.04),
                          *[K_.box(f"tail{i}", (0.04, 0.04, 0.07), (x + 0.02 * i, y - 0.08, z - 0.3 - i * 0.07), "thatch") for i in range(4)])

def pr_bell(K_, H, add):
    """요령(상여 앞에서 흔드는 손종): 손잡이와 종."""
    x, y, z = H["R"]; add("Hand.R", K_.cyl("handle", 0.016, 0.016, 0.16, (x, y - 0.06, z - 0.04), "wood", 5), K_.cyl("bell", 0.085, 0.04, 0.13, (x, y - 0.06, z + 0.11), "gold", 7), K_.sph("clapper", 0.02, (x, y - 0.06, z + 0.1), "iron", 4, 3))

def pr_jar_on_head(K_, H, add):
    """물동이 이고 선 모습: 똬리 위 옹기."""
    add("Head", K_.cyl("ring", 0.12, 0.12, 0.05, (0, 0, 1.70), "thatch", 8), K_.sph("jar", 0.2, (0, 0, 1.95), "jar", 8, 5, (1, 1, 1.08)), K_.cyl("jarNeck", 0.1, 0.07, 0.1, (0, 0, 2.12), "jar", 8), K_.cyl("jarRim", 0.09, 0.09, 0.03, (0, 0, 2.21), "wood_dark", 8))

def pr_bucket(K_, H, add):
    """우물 두레박: 왼손에 든 나무 물통."""
    x, y, z = H["L"]; add("Hand.L", K_.cyl("bucket", 0.12, 0.15, 0.2, (x, y - 0.02, z - 0.28), "wood", 8), K_.cyl("hoop", 0.155, 0.155, 0.03, (x, y - 0.02, z - 0.2), "iron", 8), K_.box("bail", (0.28, 0.02, 0.02), (x, y - 0.02, z - 0.02), "thatch"))

def pr_smith(K_, H, add):
    """대장장이: 가죽 앞치마, 쇠망치, 얼굴 검댕."""
    x, y, z = H["R"]
    add("Chest", K_.box("apron", (0.38, 0.03, 0.62), (0, -0.235, 1.05), "slope_side"), K_.box("apronStrap", (0.04, 0.03, 0.3), (0, -0.2, 1.42), "slope_side"))
    add("Hand.R", K_.cyl("hamHandle", 0.028, 0.028, 0.5, (x, y - 0.05, z - 0.2), "wood", 5), K_.box("hamHead", (0.26, 0.1, 0.1), (x, y - 0.05, z + 0.32), "iron"))
    add("Head", K_.box("soot", (0.06, 0.012, 0.035), (0.055, -0.128, 1.54), "#2E2A2A"))

def pr_jige(K_, H, add):
    """등짐장수 지게: 두 다리와 가로대, 짐 보따리 둘, 어깨끈."""
    add("Chest", K_.cyl("jigeL", 0.03, 0.03, 1.0, (0.13, 0.34, 0.5), "wood", 5, rot=(0.12, 0, 0)), K_.cyl("jigeR", 0.03, 0.03, 1.0, (-0.13, 0.34, 0.5), "wood", 5, rot=(0.12, 0, 0)),
        K_.box("jigeBar", (0.36, 0.04, 0.04), (0, 0.4, 1.0), "wood"), K_.box("bundleA", (0.5, 0.3, 0.42), (0, 0.5, 1.28), "#8A7448"), K_.box("bundleB", (0.36, 0.26, 0.3), (0, 0.5, 1.64), "#6B5E50"),
        K_.box("bundleBand", (0.52, 0.32, 0.04), (0, 0.5, 1.28), "#B5473F"), K_.box("strapL", (0.05, 0.4, 0.05), (0.14, 0.17, 1.38), "thatch"), K_.box("strapR", (0.05, 0.4, 0.05), (-0.14, 0.17, 1.38), "thatch"))

def pr_bundle(K_, H, add):
    """봇짐: 등에 진 보자기 짐과 가슴 앞 매듭, 지팡이."""
    add("Chest", K_.box("bundle", (0.38, 0.24, 0.38), (0, 0.3, 1.2), "#3E64B0"), K_.box("knot", (0.07, 0.05, 0.07), (0.02, -0.215, 1.3), "#3E64B0"), K_.box("diag", (0.05, 0.03, 0.62), (0.0, -0.205, 1.16), "#3E64B0", rot=(0, 0.55, 0)))
    pr_cane(K_, H, add)

def pr_medicine(K_, H, add):
    """약방 딸: 왼손에 약봉지 세 개, 허리에 약주머니."""
    x, y, z = H["L"]
    add("Hand.L", *[K_.box(f"packet{i}", (0.13, 0.1, 0.045), (x, y - 0.07, z + 0.02 + i * 0.05), "hanji", rot=(0, 0.2 * i, 0)) for i in range(3)], K_.box("string", (0.03, 0.11, 0.16), (x, y - 0.07, z + 0.07), "#B5473F"))
    add("Hips", K_.box("pouch", (0.12, 0.07, 0.17), (0.23, -0.1, 0.92), "yellow_cloth"), K_.box("pouchCord", (0.02, 0.02, 0.1), (0.23, -0.1, 1.03), "#B5473F"), K_.box("sprig", (0.05, 0.02, 0.14), (0.27, -0.1, 1.05), "leaf", rot=(0, 0.3, 0)))

def pr_tray(K_, H, add):
    """주막 쟁반(소반): 오른손으로 받친 상에 사발 둘과 주전자."""
    x, y, z = H["R"]
    add("Hand.R", K_.cyl("tray", 0.22, 0.22, 0.03, (x - 0.02, y - 0.22, z + 0.05), "wood", 10), K_.cyl("bowlA", 0.05, 0.075, 0.06, (x + 0.06, y - 0.2, z + 0.08), "hanji", 7), K_.cyl("bowlB", 0.05, 0.075, 0.06, (x - 0.1, y - 0.28, z + 0.08), "hanji", 7), K_.cyl("jug", 0.06, 0.045, 0.15, (x - 0.06, y - 0.15, z + 0.08), "jar", 7))

def pr_candy_stick(K_, H, add):
    x, y, z = H["R"]; add("Hand.R", K_.cyl("stick", 0.012, 0.012, 0.4, (x, y - 0.04, z - 0.1), "wood", 4), K_.sph("candy", 0.05, (x, y - 0.04, z + 0.32), "yellow_cloth", 6, 4))

def pr_candy_tray(K_, H, add):
    """엿판: 목에 끈을 걸어 배 앞에 멘 납작한 판과 엿 조각."""
    add("Chest", K_.box("tray", (0.36, 0.28, 0.06), (0, -0.3, 0.9), "wood"), K_.box("rim", (0.38, 0.3, 0.03), (0, -0.3, 0.945), "wood_dark"), *[K_.box(f"cand{i}", (0.07, 0.07, 0.04), (-0.12 + 0.08 * (i % 4), -0.34 + 0.1 * (i // 4), 0.98), "yellow_cloth") for i in range(8)],
        K_.box("strapL", (0.03, 0.03, 0.62), (0.11, -0.16, 1.2), "thatch", rot=(-0.28, 0, 0)), K_.box("strapR", (0.03, 0.03, 0.62), (-0.11, -0.16, 1.2), "thatch", rot=(-0.28, 0, 0)))

def pr_book(K_, H, add):
    x, y, z = H["L"]; add("Hand.L", K_.box("book", (0.18, 0.045, 0.25), (x, y - 0.08, z + 0.02), "#2F4A7A"), K_.box("pages", (0.16, 0.047, 0.23), (x + 0.01, y - 0.08, z + 0.02), "hanji"), K_.box("spine", (0.02, 0.05, 0.25), (x - 0.09, y - 0.08, z + 0.02), "#B5473F"))

def pr_keys(K_, H, add):
    """옥지기 열쇠: 허리 고리에 걸린 큰 열쇠 뭉치."""
    add("Hips", *ring_xz(K_, "kring", (0.2, -0.17, 0.9), 0.06, 8, (0.035, 0.015, 0.015), "iron"), *[K_.box(f"key{i}", (0.025, 0.015, 0.14), (0.2 + (i - 1.5) * 0.03, -0.17, 0.74), "iron", rot=(0, 0.1 * (i - 1.5), 0)) for i in range(4)],
        *[K_.box(f"keyHead{i}", (0.05, 0.018, 0.04), (0.2 + (i - 1.5) * 0.03, -0.17, 0.67), "gold") for i in range(4)])

def pr_gonjang(K_, H, add):
    """사령: 곤장(납작한 날이 달린 긴 몽둥이)과 허리의 붉은 오라줄."""
    x, y, z = H["R"]
    add("Hand.R", K_.cyl("shaft", 0.028, 0.025, 1.25, (x, y - 0.03, 0.3), "wood", 5), K_.box("blade", (0.13, 0.035, 0.5), (x, y - 0.03, 0.22), "wood"), K_.box("band", (0.07, 0.07, 0.05), (x, y - 0.03, 1.1), "#B5473F"))
    add("Hips", *ring_xz(K_, "rope", (-0.2, -0.14, 0.88), 0.09, 8, (0.06, 0.03, 0.03), "#B5473F"))

def pr_scar(K_, H, add):
    """덕만: 왼 눈썹(캐릭터 왼쪽=+X) 위의 흉터와 손에 쥔 고삐."""
    add("Head", K_.box("scar", (0.07, 0.014, 0.014), (0.06, -0.133, 1.645), "#A04A52", rot=(0, 0.6, 0)))
    x, y, z = H["R"]; add("Hand.R", *ring_xz(K_, "halter", (x, y - 0.06, z - 0.08), 0.1, 8, (0.06, 0.04, 0.04), "thatch"))

def pr_incense(K_, H, add):
    """제사: 오른손에 향로, 연기 한 줄기."""
    x, y, z = H["R"]; add("Hand.R", K_.cyl("censer", 0.06, 0.09, 0.09, (x, y - 0.1, z - 0.03), "sagat", 8), K_.cyl("lid", 0.07, 0.025, 0.06, (x, y - 0.1, z + 0.06), "sagat", 8), K_.sph("smoke", 0.04, (x, y - 0.1, z + 0.17), "#D8D0C0", 5, 3, (1, 1, 1.6)))

PROPS = {f.__name__[3:]: f for f in (pr_cane, pr_fan_broken, pr_cross_cloth, pr_rope_coil, pr_bell, pr_jar_on_head, pr_bucket, pr_smith, pr_jige, pr_bundle, pr_medicine, pr_tray, pr_candy_stick, pr_candy_tray, pr_book, pr_keys, pr_gonjang, pr_scar, pr_incense)}

# ── 몸통 틀 ────────────────────────────────────────────────────────────────────────
def build_body(s):
    """spec(dict) → (뼈 이름 → 조각 리스트). sex m=바지저고리 / f=치마저고리, robe=도포·두루마기(긴 겉옷)."""
    K_ = K(s["k"]); P = {}
    def add(b, *objs): P.setdefault(b, []).extend(objs)
    sex = s["sex"]; sk = s["skin"]; w = s.get("wide", 1.0); top = s["top"]; bot = s["bottom"]; child = s.get("child", False); hr = 0.13 * (1.25 if child else 1.0)
    hunch = s.get("hunch", False); hy = -0.07 if hunch else 0.0
    cover = False                       # 다리를 덮는 옷인가
    if sex == "f":
        hem = s.get("hem", 0.16)
        add("Hips", K_.cyl("chima", 0.42 if hem < 0.3 else 0.3, 0.17, 1.0 - hem, (0, 0, hem), bot, 10))
        if hem < 0.3:
            cover = True
            for sx, side in ((1, "L"), (-1, "R")): add(f"Foot.{side}", K_.box("sock", (0.1, 0.24, 0.07), (sx * 0.11, -0.08, 0.035), "hanji"))
        else:                            # 일하는 아가씨: 무릎 위 짧은 치마 + 바지
            for sx, side in ((1, "L"), (-1, "R")):
                add(f"UpperLeg.{side}", K_.cyl("thigh", 0.09, 0.1, 0.47, (sx * 0.13, 0, 0.5), s.get("pants", "hanji"), 6))
                add(f"LowerLeg.{side}", K_.cyl("shin", 0.055, 0.085, 0.4, (sx * 0.13, 0, 0.1), s.get("pants", "hanji"), 6))
                add(f"Foot.{side}", K_.box("shoe", (0.12, 0.27, 0.08), (sx * 0.13, -0.06, 0.04), "reed"))
    else:
        for sx, side in ((1, "L"), (-1, "R")):
            if s.get("robe"):
                cover = True; add(f"Foot.{side}", K_.box("shoe", (0.13, 0.27, 0.08), (sx * 0.13, -0.06, 0.04), "hat"))
            else:
                add(f"UpperLeg.{side}", K_.cyl("thigh", 0.09, 0.11 * w, 0.47, (sx * 0.13, 0, 0.5), bot, 6))
                add(f"LowerLeg.{side}", K_.cyl("shin", 0.06, 0.09, 0.4, (sx * 0.13, 0, 0.1), bot, 6), K_.cyl("wrap", 0.068, 0.068, 0.13, (sx * 0.13, 0, 0.1), s.get("wrap", "hanji"), 6))
                add(f"Foot.{side}", K_.box("shoe", (0.13, 0.27, 0.08), (sx * 0.13, -0.06, 0.04), "reed"))
        if s.get("robe"): add("Hips", K_.cyl("robe", 0.33 * w, 0.21 * w, 0.88, (0, 0, 0.1), s["robe"], 9))
        else: add("Hips", K_.cyl("waist", 0.21 * w, 0.2 * w, 0.14, (0, 0, 0.88), bot, 8))
    sash = s.get("sash")
    if sex == "m" and sash:
        add("Hips", K_.cyl("belt", 0.215 * w, 0.215 * w, 0.07, (0, 0, 0.99), sash, 8), K_.box("beltTail", (0.07, 0.03, 0.3), (0.08, -0.22, 0.86), sash, rot=(0, 0.1, 0)))
    # 윗옷
    if sex == "f":
        add("Chest", K_.cyl("jeogori", 0.2, 0.17, 0.34, (0, 0, 1.12), top, 8), K_.box("goreum", (0.045, 0.02, 0.5), (0.04, -0.19, 1.2), s.get("ribbon", "#B5473F")), K_.box("goreum2", (0.045, 0.02, 0.42), (0.1, -0.19, 1.2), s.get("ribbon", "#B5473F"), rot=(0, -0.1, 0)))
    else:
        add("Chest", K_.cyl("jeogori", 0.215 * w, 0.185 * w, 0.46, (0, 0, 1.0), top, 8))
    # 깃(동정): 가슴 가운데 틈이 검게 비면 보기 싫어서, 안쪽에 속저고리(흰 판)를 한 겹 깔고 깃은 짧게
    add("Chest", K_.box("inner", (0.1, 0.03, 0.2), (0, -0.19 * w, 1.36), "hanji"), K_.box("collarL", (0.06, 0.03, 0.2), (0.06, -0.2 * w, 1.37), "hanji", rot=(0, 0.45, 0)), K_.box("collarR", (0.06, 0.03, 0.2), (-0.06, -0.2 * w, 1.37), "hanji", rot=(0, -0.45, 0)))
    if hunch: add("Chest", K_.sph("hump", 0.16, (0, 0.1, 1.33), top, 6, 4, (1.0, 0.8, 0.85)))
    add("Neck", K_.cyl("neck", 0.07, 0.07, 0.1, (0, hy * 0.5, 1.46), sk, 6))
    # 팔(소매 + 손)
    H = {}
    for sx, side in ((1, "L"), (-1, "R")):
        sh = (sx * 0.25 * w, 0, 1.4); d = (sx * math.sin(A_ARM), 0, -math.cos(A_ARM)); theta = math.pi - sx * A_ARM
        slen = 0.2 if s.get("rolled") else 0.42
        add(f"UpperArm.{side}", K_.cyl("sleeve", 0.075, 0.062 if not s.get("rolled") else 0.07, slen, sh, top, 7, rot=(0, theta, 0)))
        if s.get("rolled"):
            b2 = tuple(sh[i] + d[i] * slen for i in range(3))
            add(f"UpperArm.{side}", K_.cyl("forearm", 0.065, 0.05, 0.26, b2, sk, 6, rot=(0, theta, 0)))
        hp = tuple(sh[i] + d[i] * 0.46 for i in range(3)); H[side] = hp
        add(f"Hand.{side}", K_.sph("hand", 0.055, hp, sk, 5, 4))
    # 머리
    hc = (0, hy, 1.58 - (0.02 if child else 0))
    add("Head", K_.sph("head", hr, hc, sk, 10, 7, (1, 0.97, 1.08)))
    from look_v2 import npc_face
    npc_face(K_, add, s, hc, hr, hy)   # 눈 두 점 → 흰자·눈동자·눈썹·코·입·귀·볼·주름(look_v2.py)
    hs = s.get("hair", "topknot"); hc_col = s["haircol"]
    if hs != "none": add("Head", K_.sph("hairCap", hr * 1.05, (0, hy + 0.025, hc[2] + 0.04), hc_col, 7, 4, (1, 1, 0.8)))
    if hs == "topknot": add("Head", K_.sph("knot", 0.055, (0, hy + 0.02, hc[2] + 0.17), hc_col, 5, 4), K_.box("pin", (0.01, 0.01, 0.1), (0, hy + 0.02, hc[2] + 0.14), "gold"))
    if hs == "bun": add("Head", K_.sph("bun", 0.065, (0, hy + 0.15, hc[2] - 0.03), hc_col, 6, 4), K_.box("binyeo", (0.22, 0.015, 0.015), (0, hy + 0.17, hc[2] - 0.03), "gold"))
    if hs == "braid": add("Head", K_.box("braid", (0.065, 0.06, 0.4), (0, hy + 0.2, hc[2] - 0.3), hc_col), K_.box("daenggi", (0.075, 0.065, 0.1), (0, hy + 0.2, hc[2] - 0.52), s.get("daenggi", "#B5473F")))
    if hs == "tuft": add("Head", K_.sph("tuft", 0.04, (0, hy + 0.0, hc[2] + 0.15), hc_col, 5, 3))
    if s.get("beard"): add("Head", K_.sph("beard", 0.1, (0, hy - 0.06, hc[2] - 0.13), s["beard"], 6, 4, (0.85, 0.7, 1.1)), K_.box("brow", (0.18, 0.02, 0.025), (0, hy - hr + 0.0, hc[2] + 0.045), s["beard"]))
    # 모자·수건
    ht = s.get("hat")
    if ht: typ, col = ht
    if ht and typ == "gat": add("Head", K_.cyl("brim", 0.32, 0.32, 0.02, (0, 0, 1.69), col, 12), K_.cyl("crown", 0.13, 0.1, 0.22, (0, 0, 1.7), col, 10), K_.box("strapL", (0.015, 0.015, 0.2), (0.1, -0.1, 1.55), "#B5473F"), K_.box("strapR", (0.015, 0.015, 0.2), (-0.1, -0.1, 1.55), "#B5473F"))
    if ht and typ == "paeraengi": add("Head", K_.cyl("brim", 0.3, 0.3, 0.025, (0, 0, 1.69), col, 10), K_.cyl("crown", 0.115, 0.095, 0.11, (0, 0, 1.7), col, 8), K_.box("string", (0.15, 0.015, 0.015), (0, -0.12, 1.6), "thatch"))
    if ht and typ == "jeollip": add("Head", K_.cyl("brim", 0.21, 0.175, 0.03, (0, 0, 1.69), "hat", 10), K_.cyl("crown", 0.125, 0.1, 0.14, (0, 0, 1.7), "hat", 8), K_.cyl("band", 0.13, 0.13, 0.03, (0, 0, 1.71), col, 8), K_.cyl("knob", 0.03, 0.03, 0.07, (0, 0, 1.84), col, 6), K_.box("plume", (0.025, 0.025, 0.26), (0.07, 0, 1.97), col, rot=(0, 0.35, 0)))
    if ht and typ == "headcloth": add("Head", K_.cyl("cloth", hr * 1.07, hr * 1.07, 0.06, (0, hy, hc[2] + 0.05), col, 8), K_.box("knot", (0.07, 0.05, 0.08), (0, hy + 0.15, hc[2] + 0.07), col), K_.box("tail", (0.04, 0.02, 0.18), (0.04, hy + 0.17, hc[2] - 0.04), col, rot=(0, 0.2, 0)))
    if ht and typ == "bokgeon": add("Head", K_.sph("hood", hr * 1.1, (0, hy + 0.02, hc[2] + 0.05), col, 7, 4, (1.0, 1.05, 0.85)), K_.box("flap", (0.22, 0.03, 0.22), (0, hy + 0.14, hc[2] - 0.08), col), K_.box("peak", (0.1, 0.1, 0.06), (0, hy + 0.0, hc[2] + 0.22), col))
    for p in s.get("props", ()): PROPS[p](K_, H, add)
    return P, cover

def make(s):
    """한 명을 만들어 (메시, 뼈대, 삼각형 수)로 돌려준다."""
    P, cover = build_body(s); objs = []
    for b, ps in P.items(): objs += to_group(list(ps), b)
    o = join(f"npc_{s['id']}", objs); arm = rig(o, npc_bones(s["k"], s.get("wide", 1.0)))
    return o, arm, cover

# ── 동작 ─────────────────────────────────────────────────────────────────────────
def damp(keys, f):
    """다리 동작 폭을 f배로 줄인다(치마·도포용)."""
    out = []
    for fr, spec in keys:
        d = {}
        for b, v in spec.items():
            v = dict(v)
            if b.split(".")[0] in ("UpperLeg", "LowerLeg", "Foot") and "r" in v: v["r"] = tuple(a * f for a in v["r"])
            d[b] = v
        out.append((fr, d))
    return out

def talk_keys():
    def p(arm, hand, head, chest, hrz=0): return {"UpperArm.R": {"r": (arm, 0, 0)}, "Hand.R": {"r": (hand, 0, 0)}, "Head": {"r": (head, 0, hrz)}, "Chest": {"r": (0, 0, chest)}}
    return [(0, p(-8, 0, 0, 0)), (15, p(-55, -30, 4, 2, 5)), (30, p(-35, -15, -2, 0, 0)), (48, p(-60, -35, 5, -2, -5)), (66, p(-30, -10, -1, 0, 0)), (84, p(-50, -25, 4, 2, 4)), (100, p(-8, 0, 0, 0)), (120, p(-8, 0, 0, 0))]

def work_keys():
    up = {"UpperArm.R": {"r": (-95, 0, 0)}, "Hand.R": {"r": (-20, 0, 0)}, "UpperArm.L": {"r": (-35, 0, 0)}, "Chest": {"r": (-3, 0, 0)}, "Head": {"r": (3, 0, 0)}}
    dn = {"UpperArm.R": {"r": (-40, 0, 0)}, "Hand.R": {"r": (-5, 0, 0)}, "UpperArm.L": {"r": (-35, 0, 0)}, "Chest": {"r": (8, 0, 0)}, "Head": {"r": (8, 0, 0)}}
    return [(0, up), (8, dn), (12, dn), (30, up), (36, up)]

def clips(cover):
    f = 0.55 if cover else 1.0
    return {"Idle": (hero_anim.idle_keys(), "LINEAR", True, {}), "Walk": (damp(hero_anim.walk_keys(), f), "LINEAR", True, {"step": [9, 27]}),
            "Talk": (talk_keys(), "LINEAR", True, {}), "Work": (work_keys(), "LINEAR", True, {"hit": 8})}

# ── 17명(21개) 명세 ───────────────────────────────────────────────────────────────
HAIR = "#14141F"; WHITE = "#D8D0C0"; GREY = "#8E8A84"
def N(id, name, tmpl, **kw): return dict(id=id, name=name, tmpl=tmpl, **kw)
SPECS = [
 N("N101", "당할미", "노인 여자(무녀)", sex="f", k=0.93, skin="old_skin", top="hanji", bottom="#3E5A8A", haircol=WHITE, hair="bun", hunch=True, props=["fan_broken", "cross_cloth"], note="서낭당 무녀. 오방색 천과 부러진 부채"),
 N("N102", "순임", "처녀(일하는 차림)", sex="f", k=0.9, skin="#C49A78", top="#C8B68A", bottom="#7C6A55", hem=0.52, pants="#6E7B5B", haircol=HAIR, hair="braid", daenggi="#B5473F", props=["rope_coil"], note="나루 영감 손녀. 줄배 줄 타래"),
 N("N103", "윤 소사네 아들", "청년(도포)", sex="m", k=0.98, skin="skin", top="hanji", bottom="hanji", robe="#E8E1D0", sash="#586080", haircol=HAIR, hair="topknot", hat=("gat", "hat"), props=["incense"], note="제사 지내는 아들. 흰 도포·갓·향로"),
 N("N104a", "복남", "사내아이", sex="m", k=0.75, child=True, skin="skin", top="#5C7FB0", bottom="#7C6A55", sash="#B5473F", haircol=HAIR, hair="topknot", props=["candy_stick"], note="노래놀이 아이 1"),
 N("N104b", "언년이", "계집아이", sex="f", k=0.7, child=True, skin="skin", top="#E8C15A", bottom="#B5473F", ribbon="hanji", haircol=HAIR, hair="braid", daenggi="#3E64B0", note="노래놀이 아이 2"),
 N("N104c", "삼돌이", "어린 사내아이", sex="m", k=0.6, child=True, skin="skin", top="#8C9A78", bottom="#6B5E50", haircol=HAIR, hair="tuft", note="노래놀이 아이 3(가장 어림)"),
 N("N105", "갑술 영감", "노인 남자(삼베)", sex="m", k=0.95, skin="old_skin", top="#D9D2BE", bottom="#D9D2BE", robe="#D9D2BE", haircol=WHITE, hair="none", beard=WHITE, hunch=True, hat=("headcloth", "#F3E7D3"), props=["bell"], note="상여 선소리꾼. 삼베옷·흰 수염·요령"),
 N("N106", "곱단네", "아낙(중년)", sex="f", k=0.95, skin="#C49A78", top="#E8E1D0", bottom="#6B8E6A", haircol=HAIR, hair="bun", props=["jar_on_head"], note="우물가 아낙. 물동이"),
 N("N107", "간난이", "아낙(젊음)", sex="f", k=0.93, skin="skin", top="#E6B8B0", bottom="#4F6FA8", ribbon="hanji", haircol=HAIR, hair="bun", props=["bucket"], note="우물가 아낙. 두레박"),
 N("N108", "덕만", "청년(소장수 아들)", sex="m", k=1.0, skin="#C49A78", top="#9A9A8C", bottom="#4A4A52", sash="#7A5C45", haircol=HAIR, hair="topknot", hat=("headcloth", "#3E64B0"), props=["scar"], note="왼 눈썹 흉터(+X쪽)와 고삐"),
 N("N109", "용득", "대장장이(건장)", sex="m", k=1.0, wide=1.15, skin="#C49A78", top="#7C6A55", bottom="#3A3A44", sash="#2A2A38", rolled=True, haircol=HAIR, hair="topknot", hat=("headcloth", "#3E64B0"), props=["smith"], note="가죽 앞치마·망치·검댕"),
 N("N110a", "등짐장수(득보)", "등짐장수", sex="m", k=1.0, skin="#C49A78", top="#8A6B4A", bottom="#5A4630", sash="#B5473F", haircol=HAIR, hair="topknot", hat=("paeraengi", "#B4A66A"), props=["jige"], note="지게와 보따리 둘, 패랭이"),
 N("N110b", "등짐장수(동무)", "등짐장수", sex="m", k=0.97, skin="#C49A78", top="#6E7B5B", bottom="#4A4A52", sash="#E8C15A", haircol=HAIR, hair="topknot", hat=("paeraengi", "#8A7448"), props=["bundle"], note="봇짐과 지팡이, 패랭이"),
 N("N201", "득보", "등짐장수", same_as="N110a", sex="m", k=1.0, skin="#C49A78", top="#8A6B4A", bottom="#5A4630", sash="#B5473F", haircol=HAIR, hair="topknot", hat=("paeraengi", "#B4A66A"), props=["jige"], note="N-110 등짐장수(득보)와 같은 사람·같은 모양"),
 N("N202", "은실", "처녀(약방)", sex="f", k=0.93, skin="skin", top="#9CC9A0", bottom="#E8E1D0", ribbon="#E85C41" if False else "#B5473F", haircol=HAIR, hair="braid", daenggi="#E8C15A", props=["medicine"], note="약봉지와 약주머니"),
 N("N203", "섭섭이", "처녀(주막)", sex="f", k=0.93, skin="skin", top="#D9788A", bottom="#3E64B0", ribbon="hanji", haircol=HAIR, hair="braid", daenggi="#B5473F", props=["tray"], note="주막 쟁반(사발·주전자)"),
 N("N204a", "꼭지", "사내아이(장터)", sex="m", k=0.72, child=True, skin="#C49A78", top="#C8A24A", bottom="#6B5E50", sash="#586080", haircol=HAIR, hair="topknot", props=["candy_stick"], note="엿 막대"),
 N("N204b", "차돌이", "사내아이(장터)", sex="m", k=0.7, child=True, skin="#C49A78", top="#7E8DAE", bottom="#5A4630", haircol=HAIR, hair="short", props=["candy_tray"], note="목에 건 엿판"),
 N("N205", "노경수 손주", "도령(아이)", sex="m", k=0.7, child=True, skin="skin", top="#6F5BA8", bottom="#3A3F52", sash="#E8C15A", haircol=HAIR, hair="none", hat=("bokgeon", "hat"), props=["book"], note="아전 집 도령. 복건과 책"),
 N("N206", "옥지기", "관아 하인(옥)", sex="m", k=1.0, wide=1.08, skin="#C49A78", top="#3A3F52", bottom="#2A2A38", sash="#5A4630", haircol=HAIR, hair="topknot", hat=("headcloth", "#2A2A38"), props=["keys"], note="허리 열쇠 뭉치, 어두운 옷"),
 N("N207", "사령", "관아 사령(군복)", sex="m", k=1.02, skin="skin", top="#8E2F3A", bottom="#3A3F52", sash="#3E64B0", haircol=HAIR, hair="topknot", hat=("jeollip", "#B5473F"), props=["gonjang"], note="붉은 군복·전립·곤장"),
]

def build_one(s, export=True):
    reset(); anim.setup_scene()
    o, arm, cover = make(s); lo, hi = bounds(o); man = []
    for name, (keys, interp, loop, ev) in clips(cover).items():
        info = anim.clip(arm, name, keys, interp); info.update({"loop": loop, "events": ev}); man.append(info)
    path = os.path.join(OUT, "npcs", f"npc_{s['id']}.glb")
    if export: anim.export_rig(arm, path)
    return {"id": s["id"], "name": s["name"], "file": f"assets3d/npcs/npc_{s['id']}.glb", "template": s["tmpl"], "height_m": round(hi.z, 2), "tris": tris(o), "props": s.get("props", []), "note": s["note"],
            **({"same_as": s["same_as"]} if s.get("same_as") else {}), "clips": man, "verify": anim.verify(path) if export else None}

def sheets():
    """17명 전원 나란히(정면, 약간 위에서) 한 장 + 걷기 연속 사진 몇 장."""
    from PIL import Image
    rows = [SPECS[0:7], SPECS[7:14], SPECS[14:21]]; imgs = []
    for ri, row in enumerate(rows):
        reset(); anim.setup_scene()
        for i, s in enumerate(row):
            o, arm, cover = make(s); o.parent.location = (i * 1.35, 0, 0)
        setup_render(9.6, (1.35 * 3, 0, 0.95), elev=28, size=(1500, 480), ground_size=30)
        p = os.path.join(OUT, "previews", f"npc_row{ri}.png"); bpy.context.scene.cycles.samples = 24; render(p); imgs.append(Image.open(p).convert("RGB"))
    W = Image.new("RGB", (1500, 480 * 3))
    for i, im in enumerate(imgs): W.paste(im, (0, 480 * i))
    W.save(os.path.join(OUT, "previews", "npc_act1_all.png"))
    for ri in range(3): os.remove(os.path.join(OUT, "previews", f"npc_row{ri}.png"))
    # 걷기·말하기 점검: 치마(당할미 계열 N107)와 바지(N109 대장장이) 두 명
    for sid, clipn, fr in (("N107", "Walk", [0, 9, 18, 27, 35]), ("N109", "Work", [0, 4, 8, 12, 20, 30]), ("N106", "Talk", [0, 15, 30, 48, 84])):
        s = [x for x in SPECS if x["id"] == sid][0]; reset(); anim.setup_scene(); o, arm, cover = make(s)
        for name, (keys, interp, loop, ev) in clips(cover).items(): anim.clip(arm, name, keys, interp)
        setup_render(3.0, (0, 0, 1.0), size=(220, 280), ground_size=10)
        print(anim.sheet(arm, clipn, fr, os.path.join(OUT, "previews", f"anim_npc_{sid}_{clipn}")))

if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--sheets" in sys.argv: sheets()
    else:
        res = []
        for s in SPECS:
            if want and s["id"] not in want: continue
            r = build_one(s); res.append(r); print(r["id"], r["name"], "키", r["height_m"], "삼각형", r["tris"], r["verify"]["joints"], "뼈", r["verify"]["animations"])
        if not want: json.dump({"fps": anim.FPS, "note": "화면에 주인공 이름은 쓰지 않는다. 같은 틀(뼈 16개·동작 4개)이라 유니티에서 한 컨트롤러를 공유할 수 있다.", "npcs": res}, open(os.path.join(OUT, "npcs", "_npc_manifest.json"), "w"), ensure_ascii=False, indent=1)
