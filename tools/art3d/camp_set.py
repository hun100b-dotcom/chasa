"""외톨이 야영지 소품 10종 + 솔고개 첫 10분 길 풍성하게 소품 8종.
왜 이렇게:
 ① 외톨이 야영지(기획: 20곳 중 7곳, 무리에서 떨어져 혼 하나가 혼자 무릎 꿇은 자리)는 '누가 여기서 혼자 지냈다'가 소품만으로 읽혀야 한다.
   그래서 꺼진 모닥불 자국·거적 잠자리·낡은 봇짐·식은 솥·벗어 둔 짚신·기댄 지팡이처럼 **한 사람이 쓰던 흔적**만 놓고, 무리 야영지의 횃불·깃발·무기는 일부러 뺐다.
   다 쓸쓸한 색(바랜 갈색·잿빛)이고, 불은 꺼져 있다(밤에도 빛 없음). 혼이 무릎 꿇는 자리는 모닥불 자국 앞(-Y 3m)이다.
 ② 솔고개 길(시작 위치 → 마을 → 우물 → 보릿들 둑길)은 처음 10분에 모두가 지나는 곳이라 '사람이 사는 느낌'을 줄 생활 소품을 더한다:
   빨랫줄·물지게·고추 멍석·닭장·호박 넝쿨 울타리·메주 시렁·지게·장작 가림. 이미 있는 평상·장독대·우물·허수아비·장작더미와 겹치지 않는 것만 만들었다.
원점=바닥 가운데, 정면=-Y. 1칸=1 m. 실행: python3 camp_set.py → assets3d/props/prop_camp_*.glb, prop_life_*.glb, _report_camp_set.json, camp_layouts.json, previews/camp_set_50deg.png"""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from interactables import disc

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); TAU = math.tau
STRAW, STRAW_D, CLOTH_OLD, ASH, CHAR = "#B79B5E", "#8E7640", "#8C8372", "#8A8680", "#2E2926"

def straw_mat(w, d, x=0, y=0, rot=0, thick=0.04):
    """거적: 짚을 엮은 납작한 깔개. 가로 줄 결 + 끝 술."""
    p = [box("mat", (w, d, thick), (x, y, thick / 2), STRAW, (0, 0, rot))]
    for k in range(5): p.append(box(f"weave{k}", (w * 0.96, 0.03, thick * 0.4), (x + math.sin(rot) * (-(d / 2) + d * (k + 0.5) / 5) * -1, y + math.cos(rot) * (-(d / 2) + d * (k + 0.5) / 5), thick + 0.005), STRAW_D, (0, 0, rot)))
    return p

# ── ① 외톨이 야영지 ──────────────────────────────────────────────────────────────────────────────
def camp_fire_scar():
    """꺼진 모닥불 자국: 그을린 맨땅 원 + 돌 둘레(몇 개 빠짐) + 타다 만 장작 셋 + 재. 반경 0.9m. 불빛 없음."""
    r = random.Random(11); p = [disc("scorch", 0.85, 0.0, "#4A423C", 0.02, 14), disc("ash", 0.5, 0.02, ASH, 0.02, 12)]
    for i in range(9):
        if i in (3, 7): continue
        a = i / 9 * TAU; rr = 0.12 + r.random() * 0.05
        p.append(sphere(f"ring{i}", rr, (math.cos(a) * 0.78, math.sin(a) * 0.78, 0.07), "stone_dark" if i % 2 else "stone", 6, 4, (1.2, 1, 0.65), (0, 0, r.random() * TAU)))
    for i, (a, L) in enumerate(((0.3, 0.7), (2.3, 0.6), (4.4, 0.55))):
        p.append(limb(f"log{i}", (math.cos(a) * 0.35, math.sin(a) * 0.35, 0.05), (-math.cos(a) * 0.1, -math.sin(a) * 0.1, 0.13), 0.06, 0.05, CHAR, 5))
    p.append(sphere("cinder", 0.05, (0.0, 0.0, 0.05), "#5A4A44", 4, 3))
    return p

def camp_mat():
    """거적 잠자리: 거적 한 장 + 말아 벤 짚 베개 + 접힌 헌 이불 자락. 1.8×0.9m."""
    p = straw_mat(1.8, 0.9, 0, 0, 0.0)
    p += [cyl("pillow", 0.1, 0.1, 0.4, (-0.7, 0, 0.14), STRAW_D, 7, rot=(math.pi / 2, 0, 0)), box("blanket", (0.7, 0.8, 0.06), (0.35, 0.02, 0.07), CLOTH_OLD, (0, 0, 0.05)), box("blanket_fold", (0.2, 0.8, 0.09), (0.0, 0.02, 0.08), "#7A7262", (0, 0, 0.05))]
    return p

def camp_bundle():
    """낡은 봇짐: 헝겊 보따리 + 매듭 + 풀린 끈 + 삐져나온 헌 신발 한 짝. 높이 0.5m."""
    p = [sphere("bag", 0.28, (0, 0, 0.22), CLOTH_OLD, 8, 5, (1.1, 0.9, 0.85)), box("knot", (0.14, 0.14, 0.1), (0, 0, 0.5), "#6F675A", (0, 0, 0.4)),
         limb("tail1", (0.04, 0, 0.5), (0.25, 0.1, 0.38), 0.025, 0.02, "#6F675A", 4), limb("tail2", (-0.04, 0, 0.5), (-0.2, -0.1, 0.36), 0.025, 0.02, "#6F675A", 4),
         box("strap", (0.58, 0.05, 0.05), (0, -0.2, 0.25), "thatch", (0.0, 0.0, 0.0)), box("patch", (0.18, 0.02, 0.16), (0.12, -0.25, 0.3), "#6E5A3C")]
    return p

def camp_lean_to():
    """거적 가리개: 막대 둘에 거적을 비스듬히 걸친 한 사람용 비가림. 폭 1.8·깊이 1.3·높이 1.3m."""
    p = [limb("pole_l", (-0.8, 0.5, 0), (-0.78, 0.5, 1.3), 0.05, 0.04, "wood_dark", 5), limb("pole_r", (0.8, 0.5, 0), (0.78, 0.5, 1.3), 0.05, 0.04, "wood_dark", 5), limb("ridge", (-0.8, 0.5, 1.28), (0.8, 0.5, 1.28), 0.04, 0.04, "wood", 5),
         box("sheet", (1.8, 1.4, 0.05), (0, -0.15, 0.7), STRAW, (0.9, 0, 0)), box("sheet_edge", (1.8, 0.05, 0.1), (0, -0.78, 0.13), STRAW_D)]
    for k in range(4): p.append(limb(f"fray{k}", (-0.6 + k * 0.4, -0.76, 0.13), (-0.6 + k * 0.4, -0.84, 0.0), 0.02, 0.01, STRAW_D, 3))
    return p

def camp_pot():
    """식은 솥: 삼발이 위의 검은 솥 + 벗겨진 뚜껑 + 나무 국자. 높이 0.55m."""
    p = [lathe("pot", [(0, 0.0), (0.04, 0.16), (0.22, 0.26), (0.3, 0.12), (0.26, 0.0)], 9, "#2E2A2A", loc=(0, 0, 0.3), fn=None)]
    for i in range(3):
        a = i / 3 * TAU + 0.4; p.append(limb(f"leg{i}", (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.0), (math.cos(a) * 0.1, math.sin(a) * 0.1, 0.34), 0.03, 0.025, "#3A3A44", 4))
    p += [cyl("lid", 0.22, 0.2, 0.04, (0.45, -0.1, 0.0), "#2E2A2A", 8, rot=(0.15, 0, 0)), limb("ladle", (0.25, 0.1, 0.62), (0.55, 0.25, 0.1), 0.02, 0.02, "wood", 4), cyl("ladle_cup", 0.06, 0.05, 0.05, (0.56, 0.26, 0.05), "wood", 6)]
    return p

def camp_shoes():
    """벗어 둔 짚신 한 켤레(짝이 어긋나 놓임) + 쓰러진 바가지. 폭 0.5m."""
    p = []
    for k, (x, y, rot) in enumerate(((-0.12, 0, 0.1), (0.14, 0.12, -0.5))):
        p += [box(f"sole{k}", (0.12, 0.32, 0.03), (x, y, 0.015), STRAW, (0, 0, rot)), box(f"strap{k}", (0.1, 0.05, 0.05), (x, y + 0.06 * math.cos(rot), 0.05), STRAW_D, (0, 0, rot))]
    p += [sphere("gourd", 0.12, (0.4, -0.2, 0.08), "#CDB77A", 6, 4, (1, 1, 0.55), (0.4, 0, 0)), cyl("gourd_cut", 0.1, 0.1, 0.02, (0.4, -0.12, 0.1), "#3A3026", 6, rot=(1.1, 0, 0))]
    return p

def camp_staff():
    """기대 둔 지팡이: 굽은 막대 + 손때 묻은 손잡이 마디 + 흙 묻은 돌 하나(괴임). 높이 1.4m."""
    return [limb("staff", (0, 0, 0.0), (0.35, 0, 1.38), 0.035, 0.03, "wood", 5), sphere("knob", 0.05, (0.35, 0, 1.4), "wood_dark", 5, 3), limb("crook", (0.35, 0, 1.38), (0.45, 0, 1.3), 0.03, 0.03, "wood", 4), sphere("prop_stone", 0.14, (0.1, 0.0, 0.1), "stone_dark", 6, 4, (1, 1, 0.8))]

def camp_log_seat():
    """앉던 통나무: 누운 통나무 + 닳은 윗면 + 쪼갠 장작 두어 개. 길이 1.4m."""
    p = [cyl("log", 0.22, 0.22, 1.4, (0.7, 0, 0.22), "bark", 8, rot=(0, math.pi / 2, 0)), box("worn", (0.7, 0.3, 0.02), (0, 0, 0.44), "wood"), cyl("ring_end", 0.2, 0.2, 0.02, (1.4, 0, 0.22), "#A88B60", 8, rot=(0, math.pi / 2, 0))]
    p += [box(f"split{k}", (0.5, 0.08, 0.08), (0.3 + k * 0.3, -0.45 - k * 0.05, 0.05), "wood", (0, 0, 0.2 * k)) for k in range(3)]
    return p

def camp_trace():
    """남은 흔적 묶음: 먹은 자리(뼈 없는 열매씨·곡식 낟알·마른 나물 껍질) + 뭉친 헝겊 조각. 반경 0.5m. 이름 없는 누군가 자주 앉던 자리."""
    r = random.Random(5); p = [disc("stain", 0.45, 0.0, "#5A4D3C", 0.01, 10, 0.5)]
    for k in range(10): p.append(sphere(f"seed{k}", 0.03, (r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), 0.03), "#6B4A2E" if k % 2 else "#C9B764", 4, 3))
    p += [box("rag", (0.22, 0.16, 0.03), (0.2, 0.25, 0.02), CLOTH_OLD, (0, 0, 0.7)), cyl("bowl_broken", 0.12, 0.08, 0.07, (-0.2, 0.2, 0.0), "#8B6A52", 7), box("bowl_chip", (0.1, 0.07, 0.02), (-0.05, 0.3, 0.015), "#8B6A52", (0, 0, 0.8))]
    return p

def camp_pole_cloth():
    """매단 헌 헝겊 말뚝: 말뚝 하나에 낡은 천 둘이 늘어짐(누군가에게 보이라고 달았던 표시). 높이 1.6m."""
    return [limb("stake", (0, 0, 0), (0.02, 0, 1.6), 0.045, 0.035, "wood_dark", 5), box("cloth_a", (0.12, 0.02, 0.5), (0.1, 0, 1.3), CLOTH_OLD, (0, 0.1, 0.1)), box("cloth_b", (0.1, 0.02, 0.38), (-0.07, 0, 1.2), "#7A7262", (0, -0.1, 0.0)), cyl("base", 0.12, 0.1, 0.1, (0, 0, 0), "stone_dark", 6)]

# ── ② 솔고개 길 소품 ──────────────────────────────────────────────────────────────────────────────
def life_clothesline():
    """빨랫줄: 기둥 둘에 줄을 늘이고 흰 빨래·누른 빨래를 널었다. 폭 3.4m, 높이 1.9m."""
    p = [limb("postL", (-1.7, 0, 0), (-1.72, 0, 1.9), 0.06, 0.05, "wood", 5), limb("postR", (1.7, 0, 0), (1.72, 0, 1.9), 0.06, 0.05, "wood", 5)]
    pts = [(-1.7 + 3.4 * i / 8, 0, 1.78 - 0.18 * math.sin(math.pi * i / 8)) for i in range(9)]
    for i in range(8): p.append(limb(f"line{i}", pts[i], pts[i + 1], 0.015, 0.015, "thatch", 3))
    for i, (c, w, h) in enumerate((("hanji", 0.5, 0.9), ("#D9CBA0", 0.45, 0.6), ("#8FA3B8", 0.4, 0.75), ("hanji", 0.55, 1.0))):
        x, _, z = pts[1 + i * 2]; p.append(box(f"cloth{i}", (w, 0.03, h), (x, 0, z - h / 2 - 0.03), c, (0.0, 0.03 * (i - 1), 0)))
    return p

def life_water_yoke():
    """물지게: 어깨 장대 + 양쪽 물동이를 세워 기대 둔 모양. 높이 1.5m."""
    p = [limb("yoke", (-0.7, 0, 1.25), (0.7, 0, 1.25), 0.04, 0.04, "wood", 5), limb("rope_l", (-0.6, 0, 1.25), (-0.6, 0, 0.5), 0.012, 0.012, "thatch", 3), limb("rope_r", (0.6, 0, 1.25), (0.6, 0, 0.5), 0.012, 0.012, "thatch", 3),
         limb("lean", (0, 0, 1.25), (0, 0.5, 0.0), 0.03, 0.03, "wood_dark", 4)]
    for x in (-0.6, 0.6): p += [lathe(f"pail{x}", [(0, 0.0), (0.05, 0.2), (0.18, 0.28), (0.22, 0.42)], 8, "jar", loc=(x, 0, 0.0)), cyl(f"pwater{x}", 0.19, 0.19, 0.02, (x, 0, 0.4), "water", 8)]
    return p

def life_chili_mat():
    """고추 멍석: 짚 멍석 위에 붉은 고추를 펴 말린다. 1.8×1.2m. 붉은색은 고추(파혼 주황과 구분되는 짙은 붉은색)."""
    p = straw_mat(1.8, 1.2, 0, 0, 0.0, 0.05); r = random.Random(2)
    for k in range(34): p.append(limb(f"chili{k}", (r.uniform(-0.8, 0.8), r.uniform(-0.5, 0.5), 0.06), (r.uniform(-0.8, 0.8), r.uniform(-0.5, 0.5), 0.06), 0.02, 0.012, "#A8322A", 3)) if False else p.append(box(f"chili{k}", (0.16, 0.035, 0.03), (r.uniform(-0.8, 0.8), r.uniform(-0.5, 0.5), 0.07), "#A8322A", (0, 0, r.uniform(0, 3.1))))
    return p

def life_chicken_coop():
    """닭장: 짚 지붕 얹은 작은 나무 우리 + 닭 둘(둥근 몸). 폭 1.3m, 높이 0.9m."""
    p = [box("floor", (1.3, 0.9, 0.08), (0, 0, 0.34), "wood_dark"), box("wall_b", (1.3, 0.05, 0.5), (0, 0.42, 0.65), "wood"), box("wall_l", (0.05, 0.9, 0.5), (-0.62, 0, 0.65), "wood"), box("wall_r", (0.05, 0.9, 0.5), (0.62, 0, 0.65), "wood"),
         prism("roof", 1.5, 1.1, 0.35, (0, 0, 0.88), "thatch")]
    for x in (-0.6, 0.6): p += [limb(f"leg_f{x}", (x, -0.4, 0), (x, -0.4, 0.34), 0.04, 0.04, "wood_dark", 4), limb(f"leg_b{x}", (x, 0.4, 0), (x, 0.4, 0.34), 0.04, 0.04, "wood_dark", 4)]
    for k in range(5): p.append(box(f"bar{k}", (0.03, 0.03, 0.46), (-0.5 + k * 0.25, -0.43, 0.65), "wood"))
    for k, (x, c) in enumerate(((-0.3, "#E8E0CC"), (0.25, "#A8663A"))): p += [sphere(f"hen{k}", 0.15, (x, 0.0, 0.52), c, 6, 4, (1, 1.2, 0.9)), sphere(f"hen_h{k}", 0.06, (x, -0.17, 0.62), c, 5, 3), box(f"comb{k}", (0.02, 0.05, 0.04), (x, -0.18, 0.68), "#B03A2E")]
    return p

def life_pumpkin_fence():
    """호박 넝쿨 울타리: 나무 울 + 넝쿨 + 누런 호박 셋(풀밭 쪽). 길이 2.4m, 높이 1.2m."""
    p = [box("rail_a", (2.4, 0.05, 0.05), (0, 0, 0.45), "wood"), box("rail_b", (2.4, 0.05, 0.05), (0, 0, 0.95), "wood")]
    for i in range(7): p.append(limb(f"stake{i}", (-1.2 + i * 0.4, 0, 0), (-1.2 + i * 0.4, 0, 1.15 - (i % 2) * 0.1), 0.04, 0.03, "wood_dark", 4))
    r = random.Random(4)
    for i in range(12): p.append(sphere(f"leaf{i}", 0.13, (-1.1 + i * 0.2, r.uniform(-0.05, 0.1), 0.5 + r.uniform(0, 0.55)), "leaf" if i % 2 else "#4F7A3B", 5, 3, (1, 0.4, 0.9)))
    for i, x in enumerate((-0.6, 0.35, 0.95)): p += [sphere(f"pumpkin{i}", 0.2, (x, -0.35, 0.18), "#C98A2E", 7, 5, (1, 1, 0.75)), limb(f"stem{i}", (x, -0.35, 0.3), (x, -0.35, 0.38), 0.02, 0.015, "wood", 3)]
    return p

def life_meju_rack():
    """메주 시렁: 처마 아래 쓰는 가로대에 새끼로 묶은 메주 여섯 덩이를 매단 틀. 폭 2m, 높이 1.8m."""
    p = [limb("postL", (-1.0, 0, 0), (-1.0, 0, 1.8), 0.05, 0.05, "wood", 5), limb("postR", (1.0, 0, 0), (1.0, 0, 1.8), 0.05, 0.05, "wood", 5), limb("bar", (-1.05, 0, 1.75), (1.05, 0, 1.75), 0.04, 0.04, "wood", 5)]
    for i in range(6):
        x = -0.8 + i * 0.32; p += [limb(f"cord{i}", (x, 0, 1.75), (x, 0, 1.4), 0.012, 0.012, "thatch", 3), box(f"meju{i}", (0.2, 0.2, 0.28), (x, 0, 1.25), "#A07A44", (0, 0.05 * (i % 3), 0.2 * i))]
    return p

def life_jige():
    """기대 세운 지게 + 땔나무 한 짐. 높이 1.6m. A자 지게 틀 + 얹은 장작 단."""
    p = [limb("legL", (-0.28, 0.1, 0), (-0.2, -0.1, 1.5), 0.04, 0.04, "wood_dark", 5), limb("legR", (0.28, 0.1, 0), (0.2, -0.1, 1.5), 0.04, 0.04, "wood_dark", 5)]
    for z in (0.35, 0.75, 1.15): p.append(limb(f"rung{z}", (-0.26 + z * 0.05, 0.05, z), (0.26 - z * 0.05, 0.05, z), 0.03, 0.03, "wood", 4))
    p += [limb("bundle_bar", (-0.3, 0.2, 0.5), (0.3, 0.2, 0.5), 0.02, 0.02, "wood", 3)]
    for k in range(7): p.append(limb(f"fw{k}", (-0.2 + k * 0.07, 0.25, 0.5), (-0.28 + k * 0.09, 0.2, 1.7), 0.035, 0.03, "wood" if k % 2 else "#7A5A38", 4))
    p.append(box("tie", (0.5, 0.05, 0.05), (0, 0.24, 1.1), "thatch"))
    return p

def life_straw_cover():
    """땔감 짚 가림: 장작 더미 위에 짚을 덮고 돌로 누른 모양. 1.5×0.9×0.7m."""
    p = [box("logs", (1.3, 0.7, 0.45), (0, 0, 0.22), "bark"), prism("cover", 1.6, 1.0, 0.4, (0, 0, 0.42), "thatch")]
    p += [sphere(f"weight{k}", 0.1, (-0.5 + k * 0.5, 0, 0.78), "stone", 5, 3, (1, 1, 0.7)) for k in range(3)]
    return p

CAMP = [("camp_fire_scar", camp_fire_scar, "꺼진 모닥불 자국"), ("camp_mat", camp_mat, "거적 잠자리"), ("camp_bundle", camp_bundle, "낡은 봇짐"), ("camp_lean_to", camp_lean_to, "거적 가리개"), ("camp_pot", camp_pot, "식은 솥"),
        ("camp_shoes", camp_shoes, "벗어 둔 짚신+바가지"), ("camp_staff", camp_staff, "기댄 지팡이"), ("camp_log_seat", camp_log_seat, "앉던 통나무"), ("camp_trace", camp_trace, "먹은 흔적"), ("camp_pole_cloth", camp_pole_cloth, "헝겊 말뚝")]
LIFE = [("life_clothesline", life_clothesline, "빨랫줄"), ("life_water_yoke", life_water_yoke, "물지게"), ("life_chili_mat", life_chili_mat, "고추 멍석"), ("life_chicken_coop", life_chicken_coop, "닭장"),
        ("life_pumpkin_fence", life_pumpkin_fence, "호박 넝쿨 울타리"), ("life_meju_rack", life_meju_rack, "메주 시렁"), ("life_jige", life_jige, "지게+땔나무"), ("life_straw_cover", life_straw_cover, "짚 덮은 장작")]

# 외톨이 야영지 놓는 법(혼 무릎 자리 = 원점, 단위 m, -Y가 앞). 변형 셋을 돌려 쓰면 일곱 곳이 같아 보이지 않는다.
LAYOUTS = {"note": "kneel_soul = 떨어져 앉은 혼이 무릎 꿇는 자리(원점). 소품 좌표는 그 자리 기준 상대값. 무리 야영지(적 군집)와 12m 이상 떨어뜨린다. 소품에는 불빛이 없다(꺼진 자리).",
 "variants": [
  {"name": "A_바위 곁", "items": [["camp_fire_scar", 0, 3.0, 0], ["camp_mat", -3.2, 2.2, 0.3], ["camp_bundle", -2.2, 3.0, 0.5], ["camp_staff", 1.6, 2.4, 0], ["camp_shoes", -1.2, 1.2, 0.4], ["camp_log_seat", 1.4, 3.8, 3.3], ["camp_trace", 0.6, 1.8, 0]]},
  {"name": "B_거적 가리개", "items": [["camp_lean_to", -2.6, 3.6, 0], ["camp_mat", -2.6, 2.6, 0], ["camp_fire_scar", 0.8, 3.2, 0], ["camp_pot", 0.4, 4.4, 0], ["camp_bundle", -3.9, 3.0, 1.2], ["camp_pole_cloth", 3.0, 2.0, 0], ["camp_shoes", -1.5, 1.4, 0.2]]},
  {"name": "C_떠난 자리", "items": [["camp_fire_scar", 0, 3.2, 0], ["camp_pole_cloth", 2.4, 3.8, 0], ["camp_pot", -1.6, 3.9, 0], ["camp_log_seat", -1.0, 1.8, 0.2], ["camp_staff", 2.2, 1.6, 0], ["camp_trace", -0.4, 2.2, 0], ["camp_bundle", 1.2, 4.2, 2.0]]}]}

def run():
    rep = []; os.makedirs(os.path.join(OUT, "props"), exist_ok=True)
    for key, fn, nm in CAMP + LIFE:
        reset(); o = join(f"prop_{key}", fn()); lo, hi = bounds(o)
        export(o, os.path.join(OUT, "props", f"prop_{key}.glb"))
        rep.append({"name": f"prop_{key}", "label": nm, "group": "야영지" if key.startswith("camp") else "솔고개 길", "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
    json.dump(rep, open(os.path.join(OUT, "props", "_report_camp_set.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(LAYOUTS, open(os.path.join(OUT, "layouts", "camp_layouts.json"), "w"), ensure_ascii=False, indent=1)
    for night, fname in ((False, "camp_set_50deg.png"), (True, "camp_set_night_50deg.png")):
        reset()
        for i, (key, fn, nm) in enumerate(CAMP): o = join(f"c{i}", fn()); o.location = ((i % 5 - 2) * 3.4, 3.4 - (i // 5) * 3.2, 0)
        for i, (key, fn, nm) in enumerate(LIFE): o = join(f"l{i}", fn()); o.location = ((i % 4 - 1.5) * 4.0, -4.6 - (i // 4) * 3.4, 0)
        setup_render(24, (0, -2.6, 0.6), size=(2000, 1200), ground_size=50, night=night)
        bpy.context.scene.cycles.samples = 36; render(os.path.join(OUT, "previews", fname))
    return rep

if __name__ == "__main__":
    for r in run(): print(r["name"], r["tris"], r["size_m"], "min_z", r["min_z"])
