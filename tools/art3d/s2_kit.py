"""시즌 2 저승 ⑦~⑩ 키트(약 30종). 실행: python3 s2_kit.py [이름 ...]
규약은 act3_kit.py와 같다(원점=바닥 한가운데, 정면=-Y, 1단위=1m, 재질은 색만, 불빛은 발광 면 + Light_ 빈 오브젝트).
색 뼈대: 재 섞인 회색 돌(#6E6A64)·젖은 먹(#26242C)·종이 흰색(#E4E0D4, 혼불 청록과 겹치지 않게 따뜻한 흰)·낡은 마(#A89E84)·붉은 인주(#9A3A30)·혼불 청록(#7FD6C8, 발광 면은 불빛에만).
쿼터뷰 가림 규칙(기획): 보스 마당 안에는 높은 것을 두지 않는다. 서가는 s2_archive_shelf(2.4m, 마당 밖 벽쪽)와 s2_archive_shelf_low(반 높이 1.2m, 남쪽용) 둘. 큰 벼루 s2_big_inkstone 둘레 2m는 못 들어가는 칸이라 배치 쪽에서 막힘 반지름 3.2m로 잡는다.
출력: assets3d/s2/ (접두 s2_)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
ASH = "#6E6A64"; ASH_D = "#58554F"; INK = "#26242C"; PAPER = "#E4E0D4"; LINEN = "#A89E84"; LINEN_D = "#7C7460"; VERM = "#9A3A30"; SOUL = "#7FD6C8"; WOOD = "#5A4A3C"; WOOD_D = "#403428"; TILE = "#3A3A44"

def ferry_post():
    """나루 말뚝 높이 3.4m: 굵은 말뚝에 낡은 밧줄이 감기고 꼭대기에 줄 맨 앞을 알리는 매듭 헝겊. 칼금(수백 줄)이 새겨져 있다."""
    r = random.Random(1); p = [cyl("post", 0.22, 0.28, 3.4, (0, 0, 0), WOOD_D, 8), box("cap", (0.6, 0.6, 0.12), (0, 0, 3.4), INK)]
    p += [cyl(f"rope{i}", 0.27 - i * 0.003, 0.27 - i * 0.003, 0.05, (0, 0, 0.5 + i * 0.12), LINEN, 8) for i in range(12)]
    p += [box(f"cut{i}", (0.02, 0.01, r.uniform(0.15, 0.3)), (-0.2 + (i % 8) * 0.06, -0.27, 1.9 + (i // 8) * 0.35), PAPER) for i in range(24)]
    p += [box("rag", (0.35, 0.02, 0.6), (0.3, 0, 3.1), PAPER, rot=(0, 0.1, 0.12))]
    return p
def ferry_pier():
    """나루 널판 선착장 한 칸 4×3m: 나룻배가 닿는 널판. 먹물 얼룩. 말뚝은 물속으로 3m."""
    r = random.Random(2); p = [box(f"plank{i}", (3.0, 0.38, 0.07), (0, -1.5 + i * 0.32 + 0.16, 0.4 + r.uniform(0, .015)), LINEN_D if i % 3 else WOOD_D) for i in range(10)]
    p += [box(f"bear{i}", (4.0, 0.14, 0.12), (0, -1.2 + i * 1.2, 0.31), WOOD_D) for i in range(3)] + [cyl(f"pile{i}", 0.1, 0.12, 3.3, (-1.7 + (i % 2) * 3.4, -1.3 + (i // 2) * 1.3, -3.0), WOOD_D, 6) for i in range(6)]
    return p
def ferry_boat():
    """저승 나룻배 5×1.5m: 뱃머리가 높은 검은 배. 노는 먹으로 칠해져 있다. 뱃전에 흰 종이 등롱 하나(발광 아님)."""
    p = [sphere("hull", 1.0, (0, 0, 0.35), INK, 10, 5, (2.5, 0.75, 0.4)), sphere("hull_in", 0.9, (0, 0, 0.5), "#3A3640", 10, 4, (2.4, 0.65, 0.34)), box("prow", (0.14, 0.14, 0.7), (2.4, 0, 0.8), INK, rot=(0, 0.3, 0)),
         box("seat", (0.1, 1.2, 0.06), (0.4, 0, 0.55), WOOD), cyl("oar", 0.03, 0.03, 2.4, (-0.3, 0.2, 0.55), INK, 5, rot=(0, 1.2, 0.5)), sphere("lantern", 0.16, (-2.2, 0, 1.0), PAPER, 6, 4)]
    return p
def queue_stake():
    """줄 표지 말뚝 1.2m: 줄 선 혼이 서는 자리를 알리는 낮은 말뚝과 밧줄 한 칸(줄 따라 1.2m 간격으로 놓음)."""
    return [cyl("stake", 0.05, 0.06, 1.2, (0, 0, 0), WOOD_D, 5), box("rope", (1.2, 0.02, 0.02), (0.6, 0, 1.0), LINEN)]
def ferry_hut():
    """빈 나루 마을 집 3.6×3m: 문이 열린 낡은 초가. 지붕이 가라앉고 마당에 아무도 없다. 문 안은 먹처럼 어둡다."""
    r = random.Random(4); p = [box("base", (3.6, 3.0, 0.3), (0, 0, 0.15), ASH_D), box("wall", (3.2, 2.6, 1.6), (0, 0, 1.1), LINEN_D), prism("roof", 4.2, 3.6, 1.2, (0, 0, 1.9), "#8A7A58"), box("door", (0.9, 0.08, 1.3), (0, -1.32, 0.95), INK)]
    p += [box(f"thatch{i}", (r.uniform(0.3, 0.6), 0.5, 0.05), (r.uniform(-1.6, 1.6), r.uniform(-1.5, 0), 1.9 + r.uniform(0, .5)), "#6E6244", rot=(0.3, 0, r.uniform(-.4, .4))) for i in range(5)]
    return p
def ferry_inn_site():
    """나루 마을 주막 터: 기둥 넷만 남은 빈 주막 4×4m. 솥 하나와 평상. 나룻불 쉼터가 놓이는 곳."""
    p = [box("floor", (4.0, 4.0, 0.2), (0, 0, 0.1), ASH_D)] + [cyl(f"pil{i}", 0.12, 0.14, 2.4, (-1.7 + (i % 2) * 3.4, -1.7 + (i // 2) * 3.4, 0.2), WOOD_D, 6) for i in range(4)]
    p += [box("bench", (1.6, 0.6, 0.4), (0.4, 0.8, 0.4), WOOD), cyl("pot", 0.35, 0.3, 0.4, (-1.0, 0.8, 0.2), INK, 8), box("beam", (3.6, 0.15, 0.15), (0, -1.7, 2.5), WOOD_D)]
    return p
def reed_dust():
    """깨진 가루 걸린 은빛 갈대 한 무더기 1.4m: 줄기마다 흰 가루 조각이 걸려 반짝인다(F로 줍는 자리 표시, 발광은 약한 흰 조각 둘)."""
    r = random.Random(6); p = []
    for i in range(14): a = r.uniform(0, 6.28); d = r.uniform(0, 0.4); p.append(cyl(f"r{i}", 0.012, 0.02, r.uniform(1.0, 1.5), (math.cos(a) * d, math.sin(a) * d, 0), "#A8B0AC", 4, rot=(r.uniform(-.2, .2), r.uniform(-.2, .2), 0)))
    p += [box(f"dust{i}", (0.07, 0.01, 0.05), (r.uniform(-.3, .3), r.uniform(-.3, .3), r.uniform(0.7, 1.3)), "#F0EDE4", rot=(0.4, 0, r.uniform(0, 3))) for i in range(8)]
    return p
def ink_rock():
    """먹물 여울 바위 높이 1.6m: 먹물이 번져 검게 물든 바위. 밑동에 먹 얼룩."""
    r = random.Random(8); p = [sphere("r1", 1.0, (0, 0, 0.6), INK, 6, 4, (1.2, 1.0, 0.8)), sphere("r2", 0.6, (0.7, 0.3, 0.3), "#33303A", 5, 3, (1.1, 1, 0.7))]
    p += [box(f"s{i}", (r.uniform(.3, .6), r.uniform(.3, .6), 0.02), (r.uniform(-1.2, 1.2), r.uniform(-1.2, 1.2), 0.02), "#14121A") for i in range(4)]
    return p
def dam_wall():
    """물안개 둑 한 칸 4m, 높이 1.2m: 흙과 돌을 쌓은 낮은 둑. 위는 평평. 남쪽은 안개(코드)."""
    r = random.Random(9); p = [box("bank", (4.0, 1.8, 0.8), (0, 0, 0.4), ASH_D), box("top", (3.9, 1.5, 0.12), (0, 0, 0.86), ASH)]
    p += [sphere(f"st{i}", r.uniform(0.15, 0.3), (r.uniform(-1.8, 1.8), -0.9, 0.25), ASH, 5, 3) for i in range(6)]
    return p
def nabulbul():
    """나룻불 쉼터 받침 1.6m: 돌 받침 위 청록 혼불. 쉴 수 있는 자리 표시(불빛은 Light_)."""
    p = [cyl("base", 0.5, 0.6, 0.4, (0, 0, 0), ASH_D, 8), cyl("post", 0.12, 0.14, 1.0, (0, 0, 0.4), INK, 6), sphere("bowl", 0.3, (0, 0, 1.55), ASH, 7, 4, (1, 1, 0.5)), sphere("flame", 0.18, (0, 0, 1.75), mat(SOUL, 2.4), 6, 4, (1, 1, 1.4))]
    return p

# ── ⑧ 명부전 담장 밖 ──
def clerk_barrack():
    """서리 숙사 6×3.4m: 기와 얹은 긴 행랑. 문이 나란히 다섯. 기와는 먹빛."""
    p = [box("base", (6.2, 3.6, 0.35), (0, 0, 0.17), ASH_D), box("wall", (5.8, 3.2, 2.0), (0, 0, 1.35), PAPER), prism("roof", 7.0, 4.4, 1.5, (0, 0, 2.35), TILE)]
    p += [box(f"door{i}", (0.7, 0.08, 1.4), (-2.2 + i * 1.1, -1.62, 1.05), WOOD_D) for i in range(5)]
    return p
def clerk_kitchen():
    """숙사 부엌 3×3m: 낮은 기와집. 아궁이 굴뚝 하나."""
    return [box("base", (3.2, 3.2, 0.3), (0, 0, 0.15), ASH_D), box("wall", (2.8, 2.8, 1.7), (0, 0, 1.15), LINEN), prism("roof", 3.8, 3.8, 1.2, (0, 0, 2.0), TILE), cyl("chim", 0.2, 0.22, 1.0, (1.1, 0.9, 2.0), ASH, 6)]
def inkroom_house():
    """먹방 건물 5×4m: 벽이 먹빛으로 물든 방. 문간은 하나. 지붕은 낮고 어둡다."""
    p = [box("base", (5.2, 4.2, 0.35), (0, 0, 0.17), ASH_D), box("wall", (4.8, 3.8, 1.9), (0, 0, 1.3), "#4A4650"), prism("roof", 5.8, 4.8, 1.4, (0, 0, 2.25), "#2A2830"), box("door", (1.1, 0.08, 1.5), (0, -1.92, 1.1), INK)]
    p += [box(f"drip{i}", (0.12, 0.02, 0.7 + 0.2 * (i % 3)), (-2.0 + i * 0.7, -1.93, 2.0), INK) for i in range(6)]
    return p
def big_inkstone():
    """큰 벼루 지름 4m, 높이 0.9m: 먹방 가운데 돌 벼루. 안쪽 먹물 못. 둘레 2m는 못 들어가는 칸(막힘 반지름 3.2m는 배치표에서). 가장자리 턱 0.9m."""
    p = [cyl("body", 2.0, 2.1, 0.9, (0, 0, 0), ASH_D, 20), cyl("pool", 1.55, 1.55, 0.04, (0, 0, 0.88), INK, 20), cyl("rim", 2.0, 2.0, 0.08, (0, 0, 0.86), ASH, 20), box("stick", (0.3, 0.3, 0.9), (1.25, 0.9, 0.9), INK, rot=(0, 0.4, 0.3))]
    p += [lathe("pool_ring", [(0.9, 1.5), (0.92, 1.5)], 16, "#3A3642", caps=(True, True))] if False else []
    return p
def archive_shelf():
    """서가 4m, 높이 2.4m: 문서가 빼곡한 칸 다섯. 마당 밖 벽쪽에만 둔다."""
    r = random.Random(12); p = [box("back", (4.0, 0.1, 2.4), (0, 0.45, 1.2), WOOD_D)] + [box(f"side{i}", (0.1, 0.9, 2.4), (-2.0 + i * 1.0, 0, 1.2), WOOD) for i in range(5)] + [box(f"sh{i}", (4.0, 0.9, 0.06), (0, 0, 0.1 + i * 0.58), WOOD) for i in range(5)]
    p += [box(f"doc{i}_{j}", (r.uniform(0.3, 0.8), 0.5, 0.35), (-1.7 + j * 0.9, 0, 0.35 + i * 0.58), PAPER if (i + j) % 3 else LINEN) for i in range(4) for j in range(4)]
    return p
def archive_shelf_low():
    """서가 4m, 높이 1.2m(반 높이): 쿼터뷰 가림 방지용 남쪽 서가. 위가 열려 있고 문서 두 단."""
    r = random.Random(13); p = [box("back", (4.0, 0.1, 1.2), (0, 0.45, 0.6), WOOD_D)] + [box(f"side{i}", (0.1, 0.9, 1.2), (-2.0 + i * 1.0, 0, 0.6), WOOD) for i in range(5)] + [box(f"sh{i}", (4.0, 0.9, 0.06), (0, 0, 0.1 + i * 0.55), WOOD) for i in range(3)]
    p += [box(f"doc{i}_{j}", (r.uniform(0.3, 0.8), 0.5, 0.35), (-1.7 + j * 0.9, 0, 0.35 + i * 0.55), PAPER if (i + j) % 3 else LINEN) for i in range(2) for j in range(4)]
    return p
def archive_desk():
    """그의 책상 1.6×0.8m: 서리 B-15의 낡은 책상. 위에 펼친 장부와 말라붙은 붓."""
    return [box("top", (1.6, 0.8, 0.08), (0, 0, 0.75), WOOD), box("l1", (0.08, 0.7, 0.75), (-0.7, 0, 0), WOOD_D), box("l2", (0.08, 0.7, 0.75), (0.7, 0, 0), WOOD_D), box("book", (0.5, 0.35, 0.05), (-0.2, 0, 0.83), PAPER), cyl("brush", 0.015, 0.015, 0.3, (0.4, 0.1, 0.84), INK, 4, rot=(0, 1.5, 0.3))]
def ninth_slot():
    """아홉째 칸 4m: 먼지 없는 텅 빈 서가 한 칸(⑨로 가는 문). 바닥에 먼지 자국이 없다. 뒤 문틀이 은은히 보인다."""
    p = [box("back", (4.0, 0.1, 2.4), (0, 0.45, 1.2), "#2A2830")] + [box(f"side{i}", (0.1, 0.9, 2.4), (-2.0 + i * 4.0, 0, 1.2), WOOD) for i in range(2)] + [box(f"sh{i}", (4.0, 0.9, 0.06), (0, 0, 0.1 + i * 0.58), WOOD) for i in range(5)]
    p += [box("frame_l", (0.12, 0.2, 2.0), (-0.7, 0.4, 1.0), VERM), box("frame_r", (0.12, 0.2, 2.0), (0.7, 0.4, 1.0), VERM), box("frame_t", (1.5, 0.2, 0.12), (0, 0.4, 2.0), VERM)]
    return p
def number_board():
    """번호 판 1.0×1.6m: 숫자 마당에 선 혼의 번호를 적은 나무 판. 번호는 먹줄 여섯."""
    p = [cyl("pole", 0.05, 0.05, 1.8, (0, 0, 0), WOOD_D, 5), box("board", (0.9, 0.06, 1.0), (0, 0, 1.2), LINEN)]
    p += [box(f"n{i}", (0.6, 0.012, 0.05), (0, -0.04, 1.55 - i * 0.14), INK) for i in range(6)]
    return p
def yard_desk():
    """마당 책상 1.4×0.8m: 숫자 마당 가장자리의 책상. 번호 장부와 벼루."""
    return [box("top", (1.4, 0.8, 0.07), (0, 0, 0.72), WOOD), box("l1", (0.07, 0.7, 0.72), (-0.6, 0, 0), WOOD_D), box("l2", (0.07, 0.7, 0.72), (0.6, 0, 0), WOOD_D), box("book", (0.5, 0.35, 0.05), (-0.2, 0, 0.8), PAPER), cyl("ink", 0.1, 0.1, 0.05, (0.4, 0.1, 0.8), INK, 8)]
def myeongbu_wall():
    """명부전 담장 4m, 높이 3m: 먹빛 기와를 인 긴 담. 본당이 있는 북쪽(y 1040)을 막는다."""
    p = [box("wall", (4.0, 0.8, 2.4), (0, 0, 1.2), "#4A4650"), prism("cap", 4.2, 1.2, 0.5, (0, 0, 2.4), TILE)] + [box(f"bat{i}", (0.1, 0.84, 2.4), (-1.9 + i * 1.9, 0, 1.2), ASH_D) for i in range(3)]
    return p
def myeongbu_gate():
    """명부전 닫힌 본당 문 6×4.5m: 붉은 인주 문틀에 두 짝 문이 굳게 닫혀 있다. 문 앞에 돌계단 둘."""
    p = [box("pl", (0.5, 0.5, 4.0), (-2.6, 0, 2.0), VERM), box("pr", (0.5, 0.5, 4.0), (2.6, 0, 2.0), VERM), box("lintel", (6.2, 0.6, 0.5), (0, 0, 4.1), VERM), prism("roof", 7.4, 2.6, 1.3, (0, 0, 4.35), TILE)]
    p += [box("doorL", (2.3, 0.2, 3.6), (-1.3, 0.05, 1.9), "#3A2C26"), box("doorR", (2.3, 0.2, 3.6), (1.3, 0.05, 1.9), "#3A2C26"), box("lock", (0.4, 0.1, 0.4), (0, -0.1, 1.9), "iron"), box("step1", (3.4, 1.0, 0.2), (0, -1.0, 0.1), ASH), box("step2", (3.0, 0.8, 0.2), (0, -1.7, 0.1), ASH_D)]
    return p
# ── ⑨ 빈 관할 ──
def ninth_gate():
    """아홉째 문 6×7m: 문지기가 지키는 거대한 먹빛 문. 위에 인(도장)이 들어갈 네모 자리가 비어 있다. 종 하나가 처마에 달림."""
    p = [box("pl", (0.8, 0.8, 6.0), (-2.7, 0, 3.0), "#34303A"), box("pr", (0.8, 0.8, 6.0), (2.7, 0, 3.0), "#34303A"), box("lintel", (6.8, 0.9, 0.7), (0, 0, 6.2), "#34303A"), prism("roof", 8.2, 3.0, 1.5, (0, 0, 6.5), TILE)]
    p += [box("slot", (1.2, 0.1, 1.2), (0, -0.46, 5.4), "#14121A"), box("slot_frame", (1.4, 0.06, 1.4), (0, -0.44, 5.4), VERM), cyl("bell", 0.4, 0.5, 0.7, (2.0, -0.2, 6.3), "iron", 8), box("door_gap", (4.6, 0.2, 5.2), (0, 0.1, 2.6), "#14121A")]
    return p
def seal_market_stall():
    """도장 없는 장터 판 2.6×1.8m: 천막 아래 빈 판대. 판 위에 인(도장)이 없는 빈 받침만 늘어서 있다."""
    p = [box("table", (2.4, 1.2, 0.08), (0, 0, 0.85), WOOD), box("l1", (0.08, 1.0, 0.85), (-1.1, 0, 0), WOOD_D), box("l2", (0.08, 1.0, 0.85), (1.1, 0, 0), WOOD_D), prism("awning", 3.0, 2.2, 0.5, (0, 0, 2.0), "#B8AE92")]
    p += [cyl(f"pl{i}", 0.04, 0.04, 2.0, (-1.3 + (i % 2) * 2.6, -0.9 + (i // 2) * 1.8, 0), WOOD_D, 5) for i in range(4)] + [box(f"pad{i}", (0.2, 0.2, 0.04), (-0.9 + i * 0.45, 0, 0.91), VERM) for i in range(5)]
    return p
def seal_cave_rock_a():
    """인장 굴 바위 담 한 덩이 높이 5m: 굴을 둘러싸는 거친 바위. 쿼터뷰에서 안이 보이도록 위가 열려 있다."""
    r = random.Random(21); p = [sphere("a", 2.2, (0, 0, 2.0), ASH_D, 6, 4, (1.2, 0.9, 1.1)), sphere("b", 1.4, (1.6, 0.6, 1.0), ASH, 6, 4, (1, 1, 0.9)), sphere("c", 1.2, (-1.5, -0.4, 3.2), ASH, 6, 4)]
    p += [box(f"crack{i}", (0.05, 0.02, r.uniform(0.8, 1.6)), (r.uniform(-1.2, 1.2), -1.8, r.uniform(1, 3)), INK) for i in range(3)]
    return p
def seal_cave_rock_low():
    """인장 굴 남쪽 낮은 바위 담 높이 1.4m: 쿼터뷰 카메라가 가리지 않게 낮게 둔 바위 줄."""
    r = random.Random(22); return [sphere(f"s{i}", r.uniform(0.5, 0.8), (-1.5 + i * 1.0, r.uniform(-.1, .1), 0.4), ASH_D if i % 2 else ASH, 6, 4, (1.3, 1, 0.8)) for i in range(4)]
def seal_stone():
    """도장 돌 높이 1.0m: 인(도장)을 찍던 네모 돌. 윗면이 인주로 붉게 물들었고 인이 없다."""
    return [box("base", (0.8, 0.8, 0.7), (0, 0, 0.35), ASH), box("top", (0.7, 0.7, 0.06), (0, 0, 0.73), VERM), box("slot", (0.4, 0.4, 0.04), (0, 0, 0.76), "#3A1612")]
# ── ⑩ 열째 관할 ──
def first_hut():
    """처음 마을 집 3.4×2.8m: 돌과 흙으로 쌓은 아주 오래된 낮은 집. 지붕은 풀. 불빛 없음."""
    r = random.Random(31); p = [box("wall", (3.2, 2.6, 1.3), (0, 0, 0.65), "#7C7468"), prism("roof", 3.9, 3.3, 1.1, (0, 0, 1.3), "#6E6A44"), box("door", (0.7, 0.08, 1.0), (0, -1.32, 0.55), INK)]
    p += [sphere(f"st{i}", r.uniform(0.15, 0.25), (r.uniform(-1.5, 1.5), -1.4, 0.15), ASH, 5, 3) for i in range(4)]
    return p
def old_well():
    """처음 마을 우물 지름 2.2m, 높이 1.0m: 돌 우물. 검은 물이 가득 찼고 두레박은 없다. 우물터 B-19 자리."""
    return [cyl("wall", 1.1, 1.15, 1.0, (0, 0, 0), ASH, 12), cyl("water", 0.85, 0.85, 0.05, (0, 0, 0.9), INK, 12), cyl("rim", 1.1, 1.1, 0.1, (0, 0, 0.95), ASH_D, 12)]
def chain_grave():
    """사슬 무덤 봉분 2.4m: 둥근 봉분에 굵은 사슬이 감겨 말뚝에 묶여 있다(옛 차사들의 무덤)."""
    p = [sphere("mound", 1.2, (0, 0, 0.0), "#5A5648", 8, 4, (1.0, 1.0, 0.6)), cyl("stake", 0.1, 0.12, 1.4, (0, -1.0, 0), WOOD_D, 6)]
    p += [box(f"link{i}", (0.1, 0.03, 0.14), (math.cos(i * 0.52) * 1.0, math.sin(i * 0.52) * 1.0, 0.35 + 0.04 * (i % 2)), "iron", rot=(0, (i % 2) * 1.57, i * 0.52 + 1.57)) for i in range(12)]
    return p
def chain_stake():
    """사슬 무덤 맨 앞 말뚝 높이 1.8m: 굵은 쇠사슬이 말뚝에서 땅으로 늘어진다(만져 보기 자리)."""
    p = [cyl("post", 0.14, 0.16, 1.8, (0, 0, 0), WOOD_D, 6), box("cap", (0.4, 0.4, 0.08), (0, 0, 1.8), "iron")]
    p += [box(f"l{i}", (0.1, 0.03, 0.14), (0.1 * i * 0.6, -0.2, 1.5 - i * 0.12), "iron", rot=(0, (i % 2) * 1.57, 0)) for i in range(10)]
    return p
def big_dam_wall():
    """큰 물막이 벽 한 칸 6m, 높이 5m: 물막이 바닥을 둘러싼 거대한 돌벽. 위에서 물이 넘치다 멈춘 자국."""
    r = random.Random(41); p = [box("wall", (6.0, 2.4, 4.4), (0, 0, 2.2), ASH_D), box("cap", (6.2, 2.6, 0.5), (0, 0, 4.6), ASH)]
    p += [box(f"mark{i}", (0.2, 0.02, r.uniform(1.0, 2.5)), (-2.5 + i * 1.0, -1.21, 3.4), "#3A3642") for i in range(6)]
    return p
def dam_stone_step():
    """물막이 바닥으로 내려가는 돌계단 한 칸 4×2m, 낮은 쪽이 남쪽: 한 칸 0.3m씩 내려간다."""
    return [box(f"s{i}", (4.0, 0.5, 0.3), (0, -0.75 + i * 0.5, 0.15 - i * 0.0), ASH if i % 2 else ASH_D) for i in range(4)]
def first_lantern():
    """처음 마을 새벽 등 높이 2m: 작은 돌 받침 위 종이 등. 늘 같은 새벽빛이라 불은 약하게(청록)."""
    return [cyl("post", 0.08, 0.1, 1.5, (0, 0, 0), ASH_D, 5), box("lamp", (0.3, 0.3, 0.4), (0, 0, 1.5), mat(SOUL, 1.2))]
def old_charcoal_mark():
    """바닥 그을림 자국 지름 2m: 오래된 불 탄 자리(처음 마을 마당)."""
    return [cyl("burn", 1.0, 1.0, 0.02, (0, 0, 0.0), "#1E1C20", 12)]

KIT = [(f.__name__, f) for f in (ferry_post, ferry_pier, ferry_boat, queue_stake, ferry_hut, ferry_inn_site, reed_dust, ink_rock, dam_wall, nabulbul, clerk_barrack, clerk_kitchen, inkroom_house, big_inkstone,
        archive_shelf, archive_shelf_low, archive_desk, ninth_slot, number_board, yard_desk, myeongbu_wall, myeongbu_gate, ninth_gate, seal_market_stall, seal_cave_rock_a, seal_cave_rock_low, seal_stone,
        first_hut, old_well, chain_grave, chain_stake, big_dam_wall, dam_stone_step, first_lantern, old_charcoal_mark)]
LIGHTS = {"nabulbul": ("Light_nabulbul", (0, 0, 1.8), (0.5, 0.84, 0.78), 1.6, 8.0, True), "first_lantern": ("Light_first_lantern", (0, 0, 1.6), (0.5, 0.84, 0.78), 0.8, 5.0, False),
          "ninth_gate": ("Light_gate_slot", (0, -0.6, 5.4), (0.6, 0.2, 0.15), 0.6, 6.0, False)}
def build(name, fn):
    reset(); o = join("s2_" + name, fn()); lo, hi = bounds(o)
    if name in LIGHTS: n, pos, col, it, rg, fl = LIGHTS[name]; light_empty(o, n, pos, col, intensity=it, range_m=rg, flicker=fl)
    export(o, os.path.join(OUT, "s2", f"s2_{name}.glb"))
    return {"name": "s2_" + name, "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "min_z": round(lo.z, 3)}
if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "s2"), exist_ok=True)
    want = sys.argv[1:]; res = [build(k, f) for k, f in KIT if not want or k in want]
    if not want:
        json.dump(res, open(os.path.join(OUT, "s2", "_report_s2.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        for i, (k, f) in enumerate(KIT): o = join(k, f()); o.location = ((i % 7 - 3) * 10.0, -(i // 7) * 10.0, 0)
        setup_render(75, (0, -20.0, 1.5), elev=50, size=(1500, 900), ground_size=140); bpy.context.scene.cycles.samples = 24
        render(os.path.join(OUT, "previews", "s2_kit_50deg.png"))
    print(len(res), "종, 삼각형 최대", max(r["tris"] for r in res))
