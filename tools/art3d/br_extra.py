"""검은여울 지형 소품 보강 12종: 강변·물속·역병의 흔적.
왜 이렇게: 지금 검은여울은 여울·돌다리·나루터·버드나무·갈대·의원 집뿐이라 강변이 비어 보인다. 이 지역의 분위기(물이 검고, 역병이 돌아 사람이 떠난 강마을)를 말해 줄 소품을 더한다.
 강이 일하던 흔적(그물 말뚝·통발·빨래 돌판) + 사람이 급히 떠난 흔적(엎어진 배·버려진 수레·부러진 울타리·흰 천 줄) + 강이 가져온 것(떠내려온 통나무·이끼 낀 큰 돌) + 살아 있는 것(왜가리·마른 갈대 무더기·부표 등).
규약은 기존 br_* 키트와 같다(1유닛=1m, 원점=바닥 중심, 정면 -Y). 물에 닿는 소품(수레·부표·그물 말뚝)은 아랫부분이 물면(z=0.18) 아래로 묻혀도 되도록 바닥을 0에 둔다.
실행: python3 br_extra.py → assets3d/blackrapids/br_x_*.glb, _br_extra_report.json, previews/br_extra_50deg.png"""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d"); TAU = math.tau
MOSS, WET, CLOTH = "#4F6A58", "#3A3F44", "#D8D4C4"

def wrecked_boat():
    """엎어져 물가에 걸린 배: 뒤집힌 선체(곡선 갈빗대 드러남) + 부러진 삿대. 길이 4m."""
    p = [lathe("hull", [(0, 0.2), (0.3, 0.6), (0.55, 0.75), (0.7, 0.6), (0.78, 0.0)], 12, "#5A4634", scale=(2.6, 1.0, 1.0), loc=(0, 0, 0.0), skip=lambda i, k: False)]
    p += [box(f"rib{i}", (0.06, 1.2, 0.05), (-1.3 + i * 0.52, 0, 0.62 - 0.24 * abs(i - 2.5) * 0.35), "wood_dark", rot=(0, 0, 0)) for i in range(6)]
    p += [limb("pole", (1.6, -0.7, 0.05), (-0.6, -1.2, 0.35), 0.05, 0.04, "wood", 5), box("pole_broken", (0.5, 0.06, 0.06), (-1.0, -1.3, 0.1), "wood", rot=(0, 0, 0.3)), sphere("weed", 0.3, (-1.5, 0.3, 0.1), MOSS, 5, 3, (1.4, 1, 0.4))]
    return p

def net_posts():
    """그물 말뚝: 말뚝 셋 + 늘어진 마른 그물(성긴 격자) + 뜸 돌(부력 나무). 폭 3.6m, 높이 2m."""
    p = [limb(f"post{i}", (-1.8 + i * 1.8, 0, 0), (-1.8 + i * 1.8 + 0.05 * (i - 1), 0, 2.0 - 0.1 * i), 0.07, 0.05, "wood_dark", 5) for i in range(3)]
    for r in range(5):
        z = 1.8 - r * 0.28
        p.append(limb(f"h{r}", (-1.8, 0, z), (1.8, 0, z - 0.2 * math.sin(r)), 0.012, 0.012, "#8C8372", 3))
    for c in range(11): p.append(limb(f"v{c}", (-1.7 + c * 0.34, 0, 1.85), (-1.7 + c * 0.34, 0.02, 0.8 + 0.1 * (c % 3)), 0.01, 0.01, "#8C8372", 3))
    p += [sphere(f"float{i}", 0.05, (-1.5 + i * 0.75, 0, 1.55), "#B79B5E", 4, 3) for i in range(5)]
    return p

def driftwood():
    """떠내려온 통나무 더미: 뿌리 달린 큰 통나무 + 가지 + 쌓인 갈대 검불. 길이 3.8m, 높이 1m."""
    p = [cyl("trunk", 0.28, 0.2, 3.4, (0, 0, 0.28), "#5E5448", 8, rot=(0, math.pi / 2, 0.15)), sphere("rootball", 0.4, (1.7, 0, 0.4), "#4A4038", 6, 4, (1, 1.2, 0.9))]
    p += [limb(f"rt{i}", (1.7, 0, 0.4), (2.0 + 0.1 * i, (i - 1) * 0.45, 0.6 + 0.2 * i), 0.07, 0.02, "#4A4038", 4) for i in range(3)]
    p += [limb("branch", (-0.6, 0, 0.5), (-1.4, 0.7, 0.95), 0.06, 0.02, "#5E5448", 4), cyl("log2", 0.14, 0.12, 1.8, (-0.6, 0.55, 0.14), "#6B5E50", 7, rot=(0, math.pi / 2, -0.5))]
    p += [sphere(f"debris{i}", 0.2, (-1.0 + i * 0.5, -0.3 + (i % 2) * 0.2, 0.1), "#8A7A5A", 5, 3, (1.4, 1, 0.5)) for i in range(4)]
    return p

def mossy_boulder():
    """이끼 낀 큰 돌: 물에 닳아 둥근 돌 + 아래쪽 젖은 어두운 띠 + 윗면 이끼. 지름 2m, 높이 1.4m."""
    p = [sphere("rock", 1.0, (0, 0, 0.55), "#6F7276", 8, 6, (1.0, 0.85, 0.7)), sphere("rock2", 0.55, (0.9, -0.3, 0.3), "#5F6266", 6, 4, (1, 1, 0.7)), sphere("wet", 1.02, (0, 0, 0.2), WET, 8, 4, (1.0, 0.86, 0.3)), sphere("moss", 0.7, (-0.1, 0.1, 0.95), MOSS, 7, 4, (1.1, 0.9, 0.35))]
    return p

def drowned_cart():
    """반쯤 잠긴 수레: 바퀴 하나가 빠진 짐수레, 한쪽으로 기울고 끌채가 부러짐. 길이 3m."""
    p = [box("bed", (2.0, 1.1, 0.12), (0, 0, 0.55), "wood", rot=(0, 0.18, 0)), box("side_l", (2.0, 0.06, 0.4), (0, -0.55, 0.78), "wood_dark", rot=(0, 0.18, 0)), box("side_r", (2.0, 0.06, 0.4), (0, 0.55, 0.78), "wood_dark", rot=(0, 0.18, 0)), limb("shaft", (1.0, 0.3, 0.5), (2.2, 0.6, 0.15), 0.05, 0.04, "wood", 4)]
    p += [cyl("wheel", 0.42, 0.42, 0.08, (-0.6, -0.68, 0.42), "wood_dark", 10, rot=(math.pi / 2, 0, 0))] + [limb(f"spoke{i}", (-0.6, -0.72, 0.42), (-0.6 + 0.4 * math.cos(i * 1.05), -0.72, 0.42 + 0.4 * math.sin(i * 1.05)), 0.02, 0.02, "wood", 3) for i in range(6)]
    p += [box("sack", (0.5, 0.4, 0.3), (-0.2, 0.0, 0.8), "#8C8372", rot=(0, 0.2, 0.3)), sphere("weed", 0.35, (0.5, 0.7, 0.15), MOSS, 5, 3, (1.4, 1, 0.4))]
    return p

def fish_trap():
    """통발: 대나무 살로 엮은 긴 통 + 입구 깔때기 + 묶은 끈과 말뚝. 길이 1.4m."""
    p = [lathe("trap", [(0, 0.0), (0.12, 0.12), (0.5, 0.2), (0.9, 0.2), (1.3, 0.14)], 8, "#9A8450", rot=(0, math.pi / 2, 0), loc=(-0.6, 0, 0.22))]
    p += [limb("peg", (0.3, -0.4, 0), (0.3, -0.4, 0.8), 0.04, 0.03, "wood_dark", 4), limb("cord", (0.3, -0.4, 0.7), (0.1, 0, 0.35), 0.01, 0.01, "thatch", 3), cyl("funnel", 0.2, 0.08, 0.3, (-0.62, 0, 0.22), "#8A7440", 8, rot=(0, math.pi / 2, 0))]
    return p

def heron():
    """왜가리: 한쪽 다리로 서서 물을 보는 회색 새. 높이 1.1m. 쿼터뷰에서 작은 점이 아니라 길쭉한 흰 실루엣으로 읽힘."""
    p = [limb("leg", (0, 0, 0), (0.02, 0, 0.5), 0.015, 0.015, "#A89A6A", 3), sphere("body", 0.16, (0.0, 0, 0.62), "#B8BCC4", 7, 5, (0.8, 1.5, 1.0), (0.3, 0, 0))]
    p += [limb("neck", (0, -0.15, 0.7), (0.0, -0.22, 1.0), 0.03, 0.025, "#D8D8DC", 4), sphere("head", 0.04, (0, -0.24, 1.05), "#D8D8DC", 5, 4), limb("beak", (0, -0.27, 1.05), (0, -0.52, 1.0), 0.015, 0.004, "#D8B040", 3), limb("tail", (0, 0.18, 0.6), (0, 0.38, 0.5), 0.05, 0.01, "#8E929A", 3)]
    return p

def dead_reeds():
    """마른 갈대 무더기: 꺾인 줄기 서른 개, 이삭 끝이 고개 숙임. 반경 0.8m, 높이 1.8m. 역병 철이라 누렇게 시듦."""
    r = random.Random(8); p = []
    for i in range(28):
        a = r.uniform(0, TAU); d = r.uniform(0.05, 0.75); h = r.uniform(1.1, 1.8); lean = r.uniform(0.0, 0.5)
        x, y = math.cos(a) * d, math.sin(a) * d; p.append(limb(f"r{i}", (x, y, 0), (x + math.cos(a) * lean, y + math.sin(a) * lean, h), 0.02, 0.008, "#8A7A4A" if i % 3 else "#6B5E3A", 3))
        if i % 3 == 0: p.append(sphere(f"head{i}", 0.05, (x + math.cos(a) * (lean + 0.1), y + math.sin(a) * (lean + 0.1), h - 0.1), "#5E4E30", 4, 3, (0.6, 0.6, 1.8)))
    return p

def broken_fence():
    """부러진 물가 울타리: 말뚝 여섯 중 둘이 쓰러지고 가로대가 늘어짐. 길이 3m."""
    p = []
    for i in range(6):
        x = -1.5 + i * 0.6
        if i in (2, 3): p.append(limb(f"fallen{i}", (x, 0.1, 0.05), (x + 0.6, 0.5 + 0.1 * i, 0.08), 0.04, 0.04, "wood_dark", 4))
        else: p.append(limb(f"stake{i}", (x, 0, 0), (x + 0.03 * (i - 2), 0, 1.1 - 0.12 * (i % 2)), 0.05, 0.04, "wood_dark", 5))
    p += [limb("rail_a", (-1.5, 0, 0.8), (-0.4, 0, 0.7), 0.025, 0.025, "wood", 4), limb("rail_b", (0.9, 0, 0.55), (1.5, 0, 0.8), 0.025, 0.025, "wood", 4), limb("rail_c", (-0.4, 0, 0.7), (0.4, 0.4, 0.05), 0.025, 0.025, "wood", 4)]
    return p

def cloth_line():
    """물가 흰 천 줄: 말뚝 둘 사이에 바람에 쏠린 흰 천들(역병·상 때 거는 표시). 폭 3m, 높이 1.8m. 쿼터뷰에서 흰 점이 줄지어 보임."""
    p = [limb("pL", (-1.5, 0, 0), (-1.5, 0, 1.8), 0.05, 0.04, "wood_dark", 4), limb("pR", (1.5, 0, 0), (1.52, 0, 1.7), 0.05, 0.04, "wood_dark", 4)]
    pts = [(-1.5 + 3.0 * i / 6, 0, 1.75 - 0.15 * math.sin(math.pi * i / 6)) for i in range(7)]
    for i in range(6): p.append(limb(f"l{i}", pts[i], pts[i + 1], 0.012, 0.012, "thatch", 3))
    for i in range(1, 6): x, _, z = pts[i]; p.append(box(f"c{i}", (0.26, 0.02, 0.9 - 0.08 * (i % 3)), (x + 0.08, 0.03, z - 0.5 + 0.04 * (i % 3)), CLOTH, rot=(0, 0.2, 0.15)))
    return p

def washing_stone():
    """빨래 돌판: 비스듬한 넓은 돌 + 방망이 + 흰 옷이 든 대야(주인은 떠났다). 1.6m."""
    p = [box("slab", (1.4, 0.9, 0.18), (0, 0, 0.14), "#7A7C80", rot=(0.12, 0, 0.1)), box("slab_low", (0.6, 0.5, 0.12), (-0.9, 0.1, 0.06), "#6A6C70"), cyl("bat", 0.035, 0.035, 0.5, (0.2, -0.2, 0.28), "wood", 5, rot=(math.pi / 2, 0, 0.4))]
    p += [lathe("basin", [(0, 0.0), (0.04, 0.08), (0.22, 0.16), (0.3, 0.2)], 9, "#7A4A2E", loc=(0.7, 0.55, 0.0)), sphere("laundry", 0.2, (0.7, 0.55, 0.18), CLOTH, 6, 4, (1, 1, 0.55))]
    return p

def buoy_lamp():
    """부표 등: 물 위에 띄운 나무 통 + 짧은 장대 + 꺼진 종이 등. 나루터 길잡이였으나 불이 꺼졌다. 높이 1.4m."""
    p = [cyl("float", 0.3, 0.3, 0.3, (0, 0, 0.0), "wood_dark", 8), cyl("band", 0.31, 0.31, 0.04, (0, 0, 0.12), "#6A6C70", 8), limb("pole", (0, 0, 0.3), (0.02, 0, 1.2), 0.03, 0.025, "wood", 4), box("lamp", (0.26, 0.26, 0.34), (0.02, 0, 1.2), "#C9C0A8"), box("lamp_top", (0.34, 0.34, 0.05), (0.02, 0, 1.4), "wood_dark"), limb("anchor", (0, 0, 0.0), (0.3, 0.2, -0.4), 0.012, 0.012, "thatch", 3)]
    return p

def salt_ring():
    """역병 소금 선: 땅에 뿌린 소금 호(弧)와 재, 그 안에 놓인 깨진 사발. 반경 1.2m. 의원이 막으려던 흔적(물가 길목)."""
    from fx import annulus
    p = [annulus("salt", 1.0, 1.15, 0.015, 0.0, "#EDEDE6", 20, 0.4, 5.5), annulus("ash", 0.2, 0.7, 0.012, 0.0, "#6B6A66", 12), cyl("bowl", 0.14, 0.09, 0.08, (0.1, 0.05, 0.0), "#8B6A52", 7), box("chip", (0.1, 0.07, 0.02), (0.3, -0.1, 0.01), "#8B6A52", rot=(0, 0, 0.8))]
    return p

LIST = [("br_x_wrecked_boat", wrecked_boat, "엎어진 배"), ("br_x_net_posts", net_posts, "그물 말뚝"), ("br_x_driftwood", driftwood, "떠내려온 통나무"), ("br_x_mossy_boulder", mossy_boulder, "이끼 낀 큰 돌"), ("br_x_drowned_cart", drowned_cart, "잠긴 수레"), ("br_x_fish_trap", fish_trap, "통발"),
        ("br_x_heron", heron, "왜가리"), ("br_x_dead_reeds", dead_reeds, "마른 갈대 무더기"), ("br_x_broken_fence", broken_fence, "부러진 울타리"), ("br_x_cloth_line", cloth_line, "흰 천 줄"), ("br_x_washing_stone", washing_stone, "빨래 돌판"), ("br_x_buoy_lamp", buoy_lamp, "부표 등"), ("br_x_salt_ring", salt_ring, "소금 선")]

def run():
    rep = []
    for key, fn, nm in LIST:
        reset(); o = join(key, fn()); lo, hi = bounds(o); export(o, os.path.join(OUT, "blackrapids", key + ".glb"))
        rep.append({"name": key, "label": nm, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)})
    json.dump(rep, open(os.path.join(OUT, "blackrapids", "_br_extra_report.json"), "w"), ensure_ascii=False, indent=1)
    reset()
    for i, (key, fn, nm) in enumerate(LIST): o = join(f"p{i}", fn()); o.location = ((i % 5 - 2) * 4.2, 4.0 - (i // 5) * 4.0, 0)
    setup_render(24, (0, 0, 0.6), size=(2000, 1100), ground_size=50, night=False)
    bpy.context.scene.cycles.samples = 32; render(os.path.join(OUT, "previews", "br_extra_50deg.png"))
    return rep

if __name__ == "__main__":
    for r in run(): print(r["name"], r["tris"], r["size_m"], "min_z", r["min_z"])
