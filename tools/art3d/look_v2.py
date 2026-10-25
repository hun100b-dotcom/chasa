"""외형 2차 다듬기: 주인공(동이)·혼 4종. 뼈대 이름과 위치는 characters.BONES 그대로라서 hero_anim.py·soul_anim.py의 동작이 그대로 맞는다.
왜 다시 만드나: 직접 평가에서 최종 외형이 3/10이었다. 원통 몇 개를 이은 모양이라 실루엣이 둔하고, 갓·도포에 주름이 없고, 혼은 매끈한 덩어리라 '혼'다운 맛이 없었다.
 - 도포: 선반으로 깎은 몸체에 고리마다 주름(번갈아 들락날락)과 삐뚤빼뚤한 밑단, 앞 트임과 안감.
 - 소매: 어깨는 좁고 끝동 쪽으로 퍼지며 끝에 한지 끝동. 갓: 챙이 얇게 위로 들리고 갓끈과 구슬이 가슴까지 늘어진다.
 - 혼: 반투명 겉껍질(알파) + 불투명 발광 핵 + 꼬리 가닥. 겉껍질 하나만 투명이라 유니티 투명 정렬 부담이 작다.
좌표 규약은 lib3d와 같다(Z 위, 앞 -Y, 캐릭터 왼쪽 +X)."""
import math, random
from lib3d import *

def grp(objs, bone):
    """조각 전체를 뼈 하나에 100% 묶는다."""
    for o in objs:
        vg = o.vertex_groups.new(name=bone); vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
    return objs

def blend(o, knots):
    """높이에 따라 뼈 사이 가중치를 섞는다. knots=[(z, 뼈), ...] 아래→위. 사이에 있는 점은 두 뼈에 나눠 묶어 허리가 꺾일 때 천이 자연스럽게 휜다."""
    gs = {}
    for _, b in knots:
        if b not in gs: gs[b] = o.vertex_groups.new(name=b)
    for v in o.data.vertices:
        z = v.co.z
        if z <= knots[0][0]: gs[knots[0][1]].add([v.index], 1.0, "REPLACE"); continue
        if z >= knots[-1][0]: gs[knots[-1][1]].add([v.index], 1.0, "REPLACE"); continue
        for (z0, b0), (z1, b1) in zip(knots, knots[1:]):
            if z0 <= z <= z1:
                t = (z - z0) / (z1 - z0)
                if b0 == b1: gs[b0].add([v.index], 1.0, "REPLACE")
                else: gs[b0].add([v.index], 1 - t, "REPLACE"); gs[b1].add([v.index], t, "REPLACE")
                break
    return o

def ribbon(name, pts, w, material, th=0.014):
    """점들을 따라 이어진 납작한 띠(고름·옷깃·세조대). 마디마다 상자 하나."""
    out = []
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1]); d = b - a
        q = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
        out.append(box(f"{name}{i}", (w, th, d.length * 1.04), tuple((a + b) / 2), material, rot=tuple(q)))
    return out

# ─────────────────────────────── 주인공 ───────────────────────────────
def hero2():
    A = 0.5
    parts = []
    # 1) 도포 자락: 14각 선반 + 번갈아 들락거리는 주름 + 삐뚤빼뚤한 밑단 + 앞 한 칸 트임(안감이 비침)
    R = [(0.05, 0.47), (0.14, 0.43), (0.32, 0.355), (0.55, 0.285), (0.78, 0.235), (0.97, 0.215)]
    def pleat(i, k, th, z, r):
        a = 0.11 * (1 - z / 1.1)
        zz = z + (0.03 * math.sin(3 * th + 0.6) + 0.015 * (1 if k % 2 else -1) if i == 0 else 0)
        return r * (1 + a * (1 if k % 2 else -1)), zz
    skirt = lathe("skirt", R, 14, "ink", scale=(1.0, 0.86, 1.0), fn=pleat, skip=lambda i, k: i <= 2 and k == 10)
    lining = lathe("lining", [(0.07, 0.40), (0.3, 0.33), (0.6, 0.25), (0.95, 0.2)], 14, "#353C5C", scale=(1.0, 0.8, 1.0))
    parts += grp([skirt, lining], "Hips")
    # 2) 허리띠(붉은 띠)와 늘어진 끝, 매듭, 노리개
    sash = [cyl("sash", 0.245, 0.245, 0.15, (0, 0, 0.9), "red", 10, ), box("sash_knot", (0.13, 0.07, 0.12), (0.1, -0.265, 0.97), "gold")]
    sash[0].scale = (1.0, 0.9, 1.0)
    tails = ribbon("tailA", [(0.09, -0.27, 0.94), (0.12, -0.31, 0.7), (0.17, -0.34, 0.46), (0.14, -0.38, 0.22)], 0.075, "red") + \
            ribbon("tailB", [(0.14, -0.27, 0.93), (0.22, -0.3, 0.72), (0.3, -0.31, 0.52)], 0.06, "red")
    ornament = [sphere("jade", 0.04, (-0.2, -0.22, 0.82), mat("teal", 0.4), 6, 4), box("orn_knot", (0.05, 0.03, 0.05), (-0.2, -0.22, 0.89), "gold")] + \
               ribbon("orn_tassel", [(-0.2, -0.22, 0.78), (-0.21, -0.23, 0.66), (-0.2, -0.235, 0.56)], 0.035, "red")
    parts += grp(sash + tails + ornament, "Hips")
    # 3) 몸통: 어깨가 넓고 허리가 잘록. 허리~가슴 사이 가중치를 섞어 허리를 숙일 때 천이 늘어난다
    T = lathe("torso", [(0.93, 0.215), (1.08, 0.225), (1.22, 0.24), (1.34, 0.255), (1.41, 0.2), (1.46, 0.085)], 10, "cloth", scale=(1.14, 0.78, 1.0))
    blend(T, [(0.97, "Hips"), (1.15, "Spine"), (1.36, "Chest")]); parts.append(T)
    # 4) 옷깃: 서 있는 동정(흰 띠) + 교차하는 두 깃 + 가슴 매듭
    collar = [lathe("collar_ring", [(1.4, 0.108), (1.47, 0.092)], 10, "hanji", scale=(1.0, 0.9, 1.0), caps=(False, False))]
    collar += ribbon("lapL", [(0.07, -0.15, 1.44), (0.0, -0.205, 1.25), (-0.07, -0.222, 1.06)], 0.085, "robe") + ribbon("lapL_edge", [(0.095, -0.158, 1.44), (0.02, -0.21, 1.25), (-0.045, -0.227, 1.06)], 0.018, "hanji", 0.016)
    collar += ribbon("lapR", [(-0.07, -0.15, 1.44), (-0.01, -0.2, 1.25), (0.05, -0.218, 1.06)], 0.085, "cloth") + ribbon("lapR_edge", [(-0.095, -0.158, 1.44), (-0.03, -0.205, 1.25), (0.025, -0.222, 1.06)], 0.016, "hanji", 0.016)
    collar += [box("chest_knot", (0.08, 0.04, 0.08), (-0.02, -0.235, 1.1), "gold")] + ribbon("goreum", [(-0.02, -0.235, 1.09), (-0.03, -0.24, 0.98), (-0.05, -0.245, 0.88)], 0.03, "red")
    parts += grp(collar, "Chest")
    parts += grp([cyl("neck", 0.07, 0.07, 0.1, (0, 0, 1.46), "face", 6)], "Neck")
    # 5) 머리·갓: 얼굴은 어둠. 눈 두 줄만 천도색으로 희미하게(뒤집어 끌 수 있다). 챙은 얇고 가장자리가 들린다
    head = [sphere("head", 0.125, (0, 0, 1.585), "face", 10, 7, (1, 0.95, 1.05)),
            box("eyeL", (0.045, 0.014, 0.012), (0.05, -0.115, 1.6), mat("cheondo", 1.6), rot=(0, 0, 0.12)), box("eyeR", (0.045, 0.014, 0.012), (-0.05, -0.115, 1.6), mat("cheondo", 1.6), rot=(0, 0, -0.12))]
    brim_r = [(1.662, 0.125), (1.664, 0.2), (1.668, 0.3), (1.688, 0.385), (1.702, 0.385), (1.69, 0.3), (1.704, 0.2), (1.708, 0.125)]
    brim = lathe("hat_brim", brim_r, 16, "hat", fn=lambda i, k, th, z, r: (r, z - (0.014 * math.cos(2 * th) if r > 0.25 else 0.0)))
    crown = lathe("hat_crown", [(1.69, 0.125), (1.74, 0.122), (1.82, 0.113), (1.9, 0.106), (1.93, 0.085), (1.935, 0.0)], 12, "hat", scale=(1.0, 0.95, 1.0))
    band = cyl("hat_band", 0.129, 0.127, 0.035, (0, 0, 1.7), "red", 12)
    plate = box("hat_plate", (0.07, 0.02, 0.08), (0, -0.126, 1.755), "gold")
    head += [brim, crown, band, plate]
    for sx in (1, -1):   # 갓끈: 챙 밑에서 턱 옆을 지나 가슴까지, 구슬 셋
        pts = [(sx * 0.12, -0.04, 1.665), (sx * 0.105, -0.1, 1.54), (sx * 0.095, -0.14, 1.42), (sx * 0.075, -0.19, 1.28), (sx * 0.07, -0.205, 1.12)]
        head += chain_pts("strap" + ("L" if sx > 0 else "R"), pts, 0.011, 0.009, "red", 4)
        head += [sphere(f"bead{sx}{i}", 0.02, (sx * (0.105 - i * 0.012), -0.1 - i * 0.045, 1.54 - i * 0.12), "gold", 5, 4) for i in range(3)]
    parts += grp(head, "Head")
    # 6) 소매: 어깨 좁고 끝동에서 크게 퍼짐. 끝에 한지 끝동. 손은 어둠
    for sx, side in ((1, "L"), (-1, "R")):
        sh = (sx * 0.23, 0, 1.4); d = Vector((sx * math.sin(A), 0, -math.cos(A))); theta = math.pi - sx * A
        sr = [(0.0, 0.062), (0.1, 0.085), (0.26, 0.135), (0.44, 0.175), (0.57, 0.195), (0.595, 0.19)]
        def sl(i, k, th, z, r): return r * (1 + 0.09 * (z / 0.6) * (1 if k % 2 else -1)), z + (0.02 * math.sin(2 * th + 1) if i >= 4 else 0)
        arm = [lathe(f"sleeve_{side}", sr, 10, "cloth", loc=sh, rot=(0, theta, 0), fn=sl),
               lathe(f"cuff_{side}", [(0.575, 0.2), (0.62, 0.198)], 10, "hanji", loc=sh, rot=(0, theta, 0), caps=(False, False), fn=lambda i, k, th, z, r: (r, z + (0.02 * math.sin(2 * th + 1)))),
               lathe(f"cuff_in_{side}", [(0.6, 0.17), (0.6, 0.0)], 10, "face", loc=sh, rot=(0, theta, 0), caps=(False, False))]
        parts += grp(arm, f"UpperArm.{side}")
        hand = Vector(sh) + d * 0.63
        hp = [sphere(f"hand_{side}", 0.055, tuple(hand), "face", 6, 4)]
        if side == "L":   # 왼손 곁 혼불: 단단한 핵 + 반투명 겉 + 작은 불티
            c = (hand.x + 0.2, hand.y - 0.08, hand.z + 0.18)
            hp += [sphere("orb_core", 0.055, c, mat("cheondo", 3.0), 7, 5), sphere("orb_shell", 0.1, c, mat_alpha("cheondo", 0.32, 1.0), 8, 6)]
            hp += [sphere(f"mote{i}", 0.014, (c[0] + 0.12 * math.cos(a), c[1] + 0.05 * i - 0.06, c[2] + 0.13 * math.sin(a)), mat("cheondo", 3.0), 4, 3) for i, a in enumerate((0.6, 2.4, 4.3))]
        parts += grp(hp, f"Hand.{side}")
    # 7) 신: 코가 살짝 올라간 모양
    for sx, side in ((1, "L"), (-1, "R")):
        parts += grp([box(f"shoe_{side}", (0.12, 0.2, 0.07), (sx * 0.13, -0.06, 0.035), "hat"), box(f"toe_{side}", (0.09, 0.09, 0.06), (sx * 0.13, -0.19, 0.075), "hat", rot=(0.5, 0, 0))], f"Foot.{side}")
    return parts

# ─────────────────────────────── 혼 4종 ───────────────────────────────
def souls2():
    def eyes(z, y, dx=0.07, w=0.05, h=0.075, ox=0, m="face", slit=0.0):
        """눈 한 쌍. 납작한 타원. slit이 있으면 화난 눈처럼 바깥쪽이 올라가게 기울인다."""
        return [sphere("eyeL", 1, (ox + dx, y, z), m, 7, 5, (w / 2, 0.012, h / 2), rot=(0, 0, 0)) if not slit else box("eyeL", (w, 0.016, h * 0.4), (ox + dx, y, z), m, rot=(0, -slit, 0)),
                sphere("eyeR", 1, (ox - dx, y, z), m, 7, 5, (w / 2, 0.012, h / 2), rot=(0, 0, 0)) if not slit else box("eyeR", (w, 0.016, h * 0.4), (ox - dx, y, z), m, rot=(0, slit, 0))]
    def tail(o, base, end, r0, m, k=0.0, name="tail", n=4):
        """꼬리 가닥: base에서 end로 곡선으로 가늘어진다. k는 옆으로 휘는 정도."""
        bx, by, bz = base; ex, ey, ez = end
        pts = [(o + bx + (ex - bx) * t + k * math.sin(math.pi * t), by + (ey - by) * t, bz + (ez - bz) * t - 0.02 * t) for t in [i / n for i in range(n + 1)]]
        return chain_pts(name, pts, r0, 0.005, m, 5)

    def fresh(o=0):   # 갓 죽은 혼: 하늘빛 불꽃 방울, 위로 휘는 불꽃 끝, 아래로 말리는 꼬리 두 가닥
        sh = mat_alpha("soul_fresh", 0.55, 0.7); core = mat("soul_fresh", 3.2); sol = mat("soul_fresh", 1.0)
        body = lathe("body", [(0.30, 0.0), (0.33, 0.12), (0.43, 0.23), (0.58, 0.27), (0.73, 0.22), (0.88, 0.14), (1.0, 0.07)], 10, sh, scale=(1.0, 0.92, 1.0), loc=(o, 0, 0), caps=(False, False))
        p = [body, sphere("core", 0.16, (o, 0.01, 0.6), core, 8, 6, (1, 1, 1.25)), sphere("core2", 0.07, (o, 0.0, 0.88), core, 6, 4, (1, 1, 1.4))]
        p += chain_pts("flame", [(o, 0, 0.96), (o + 0.025, 0, 1.08), (o - 0.03, 0, 1.2), (o + 0.02, 0, 1.33)], 0.075, 0.004, sol, 5)
        p += tail(o, (0.0, 0.04, 0.34), (0.2, 0.16, 0.05), 0.1, sol, 0.04, "tailA") + tail(o, (0.0, 0.04, 0.34), (-0.17, 0.12, 0.07), 0.085, sol, -0.04, "tailB")
        p += eyes(0.63, -0.246, dx=0.075, w=0.05, h=0.075, ox=o) + [box("mouth", (0.03, 0.012, 0.02), (o, -0.248, 0.545), "face")]
        return p

    def day(o=0):     # 해 넘긴 혼: 키 큰 도포 자락 혼. 앞으로 처진 소매, 헝클어진 머리카락, 해진 밑단 가닥
        sh = mat_alpha("soul_day", 0.62, 0.55); core = mat("soul_day", 3.0); sol = mat("soul_day", 0.9); hair = mat("#7A5A1C", 0.0)
        r = random.Random(4)
        body = lathe("body", [(0.3, 0.19), (0.46, 0.25), (0.78, 0.245), (0.98, 0.19), (1.06, 0.13)], 10, sh, scale=(1.0, 0.86, 1.0), loc=(o, 0, 0),
                     fn=lambda i, k, th, z, rr: (rr * (1 + 0.05 * (1 if k % 2 else -1) * (1 if i < 3 else 0)), z))
        p = [body, sphere("head", 0.2, (o, 0, 1.17), sh, 9, 6), sphere("core", 0.13, (o, 0.0, 0.78), core, 7, 5, (1, 1, 1.5))]
        for i in range(7):   # 해진 밑단 가닥: 길이가 제각각
            a = i / 7 * math.tau + 0.2; ln = r.uniform(0.18, 0.34)
            p += chain_pts(f"rag{i}", [(o + math.cos(a) * 0.19, math.sin(a) * 0.16, 0.34), (o + math.cos(a) * 0.22, math.sin(a) * 0.19, 0.34 - ln * 0.5), (o + math.cos(a) * 0.25 + r.uniform(-.03, .03), math.sin(a) * 0.21, 0.34 - ln)], 0.07, 0.006, sol, 5)
        for sx in (-1, 1):   # 처진 소매 + 앞으로 내민 손, 헝클어진 머리카락
            p += [limb(f"sleeve{sx}", (o + sx * 0.22, -0.02, 0.98), (o + sx * 0.38, -0.2, 0.5), 0.065, 0.1, sol, 6), sphere(f"hand{sx}", 0.065, (o + sx * 0.41, -0.22, 0.44), sol, 6, 4)]
            p += chain_pts(f"hair{sx}", [(o + sx * 0.12, 0.1, 1.3), (o + sx * 0.2, 0.14, 1.1), (o + sx * 0.23, 0.16, 0.9), (o + sx * 0.2, 0.17, 0.76)], 0.04, 0.006, hair, 5)
        p += chain_pts("hairBack", [(o, 0.15, 1.3), (o + 0.03, 0.22, 1.1), (o + 0.0, 0.26, 0.85)], 0.06, 0.008, hair, 5)
        p += eyes(1.19, -0.195, dx=0.075, w=0.05, h=0.08, ox=o) + [sphere("mouth", 1, (o, -0.2, 1.08), "face", 6, 4, (0.025, 0.012, 0.035))]
        return p

    def old(o=0):     # 오래된 혼: 구부정한 덩어리. 들쭉날쭉한 뿔, 갈라진 틈으로 붉게 비치는 속불, 화난 눈, 질질 끌리는 꼬리
        r = random.Random(11)
        sh = mat_alpha("soul_old", 0.86, 0.25); core = mat("berry", 2.6); sol = mat("soul_old", 0.25); glow = mat("#FFE9A8", 3.0); crack = mat("berry", 3.2)
        body = lathe("body", [(0.2, 0.3), (0.42, 0.42), (0.66, 0.39), (0.9, 0.24), (1.0, 0.0)], 9, sh, scale=(1.1, 1.0, 0.92), loc=(o, 0.05, 0), fn=lambda i, k, th, z, rr: (rr * (1 + r.uniform(-0.06, 0.06) * (1 if i not in (0, 4) else 0)), z))
        p = [body, sphere("core", 0.2, (o, 0.05, 0.6), core, 7, 5, (1, 1, 1.1))]
        for i in range(8):   # 뿔: 길이·기울기가 제각각
            a = i / 8 * math.tau + r.uniform(-0.2, 0.2); ln = r.uniform(0.2, 0.46)
            bx, by = o + math.cos(a) * 0.2, 0.05 + math.sin(a) * 0.18
            p.append(limb(f"horn{i}", (bx, by, 0.88), (bx + math.cos(a) * ln * 0.45, by + math.sin(a) * ln * 0.4 + r.uniform(-.05, .05), 0.88 + ln), 0.07, 0.0, sol, 5))
        for i in range(6):   # 질질 끌리는 꼬리 가닥
            a = i / 6 * math.tau; ln = r.uniform(0.22, 0.4)
            p += chain_pts(f"drip{i}", [(o + math.cos(a) * 0.3, 0.12 + math.sin(a) * 0.26, 0.3), (o + math.cos(a) * 0.36, 0.2 + math.sin(a) * 0.3, 0.15), (o + math.cos(a) * 0.4, 0.3 + math.sin(a) * 0.34, 0.0)], 0.08, 0.006, sol, 5)
        for i, (x, z, a) in enumerate([(-0.18, 0.55, 0.3), (0.2, 0.46, -0.25), (0.05, 0.3, 0.1), (-0.3, 0.38, -0.5)]):   # 갈라진 틈(속불이 비침)
            p.append(box(f"crack{i}", (0.03, 0.02, r.uniform(0.14, 0.24)), (o + x, 0.05 - 0.325 - 0.0, z), crack, rot=(0, a, 0)))
        p += eyes(0.77, -0.345, dx=0.11, w=0.1, h=0.1, ox=o, m=glow, slit=0.4) + [box("maw", (0.2, 0.014, 0.035), (o, -0.335, 0.6), "face")]
        return p

    def lump(o=0):    # 덩어리: 겹친 구름 같은 혼. 속의 보랏빛 핵, 군데군데 떠오른 얼굴, 말려 올라가는 가닥
        sh = mat_alpha("soul_lump", 0.66, 0.5); core = mat("soul_lump", 3.0); sol = mat("soul_lump", 0.9)
        p = []
        for i, (x, y, z, r) in enumerate([(-0.32, 0, 0.57, 0.42), (0.3, 0.05, 0.67, 0.48), (0, -0.05, 0.42, 0.42), (-0.02, 0.1, 1.07, 0.34), (0.1, -0.1, 0.77, 0.3)]):
            p.append(sphere(f"blob{i}", r, (o + x, y, z), sh, 9, 6))
        p += [sphere("core", 0.3, (o, 0.0, 0.7), core, 8, 6), sphere("core2", 0.14, (o - 0.3, -0.05, 0.6), core, 6, 4), sphere("core3", 0.12, (o + 0.32, 0.0, 0.8), core, 6, 4)]
        for i, a in enumerate((0.5, 2.4, 4.4)):
            p += chain_pts(f"curl{i}", [(o + math.cos(a) * 0.5, math.sin(a) * 0.4, 0.2), (o + math.cos(a) * 0.62, math.sin(a) * 0.5, 0.1), (o + math.cos(a) * 0.7, math.sin(a) * 0.58, 0.28), (o + math.cos(a) * 0.62, math.sin(a) * 0.5, 0.42)], 0.09, 0.01, sol, 5)
        p += eyes(0.63, -0.418, dx=0.075, w=0.055, h=0.085, ox=o - 0.32) + eyes(0.74, -0.43, dx=0.085, w=0.06, h=0.095, ox=o + 0.3) + eyes(1.12, -0.23, dx=0.06, w=0.04, h=0.06, ox=o - 0.02)
        return p
    return {"fresh": fresh, "day": day, "old": old, "lump": lump}


# ─────────────────────────────── 마을 사람 얼굴 ───────────────────────────────
def shade(hexc, t, to="#5A3A2C"):
    """색을 어두운 갈색 쪽으로 t만큼 섞는다(코·주름 그림자 색)."""
    a, b = PAL.get(hexc, hexc).lstrip("#"), to.lstrip("#")
    return "#" + "".join(f"{round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t):02X}" for i in (0, 2, 4))

def npc_face(K_, add, s, hc, hr, hy):
    """눈 두 점 대신 단순한 얼굴: 흰자+눈동자, 눈썹, 코, 입, 귀, (여자·아이) 볼, (노인) 주름.
    머리는 위아래로 살짝 긴 타원(scale 1,0.97,1.08)이라 표면 앞 y를 식으로 구해 조각을 살짝 묻어 붙인다.
    성별·나이로 눈썹과 입 모양을 달리해, 조각 몇 개만으로 표정이 갈리게 한다."""
    sk = s["skin"]; sexf = s["sex"] == "f"; child = s.get("child", False); old = s.get("hunch", False) or bool(s.get("beard")) or s["skin"] == "old_skin"
    hair = s["haircol"]; brow_c = s.get("beard") or hair
    def front(x, z):   # 얼굴 표면의 앞쪽 y
        v = 1 - (x / hr) ** 2 - ((z - hc[2]) / (hr * 1.08)) ** 2
        return hy - 0.97 * hr * math.sqrt(max(v, 0.05))
    ez = hc[2] + 0.018 * (1 if not child else -0.5); ex = 0.05 * (1.08 if child else 1.0)
    dark = "#14141A"; tone = shade(sk, 0.28); lip = "#A04848" if sexf or child else "#7A3A3A"
    parts = []
    big = 1.25 if child else 1.0          # 아이는 눈이 크고 낮게
    for sx in (1, -1):
        y = front(sx * ex, ez)
        parts.append(K_.box("eyeW", (0.034 * big, 0.012, 0.024 * big), (sx * ex, y + 0.001, ez), "hanji"))
        parts.append(K_.box("eyeP", (0.017 * big, 0.012, 0.022 * big), (sx * (ex - 0.004), y - 0.006, ez - 0.001), dark))
        tilt = (0.18 if not sexf else -0.12) * (-1 if old else 1)
        parts.append(K_.box("brow", (0.05 * (0.8 if child else 1.0), 0.012, 0.012 if sexf or child else 0.017), (sx * ex, front(sx * ex, ez + 0.04) - 0.002, ez + 0.036 + (0.004 if child else 0)), brow_c, rot=(0, sx * tilt, 0)))
        parts.append(K_.box("ear", (0.016, 0.026, 0.045), (sx * (hr - 0.004), hy + 0.0, hc[2] + 0.0), sk))
        if sexf or child:
            parts.append(K_.box("cheek", (0.034, 0.01, 0.022), (sx * 0.075, front(sx * 0.075, hc[2] - 0.03) + 0.0, hc[2] - 0.03), "#D9928A"))
        if old:
            parts.append(K_.box("wrinkle", (0.04, 0.008, 0.005), (sx * ex, front(sx * ex, ez - 0.026) - 0.002, ez - 0.026), tone, rot=(0, sx * -0.15, 0)))
    parts.append(K_.box("nose", (0.024, 0.026, 0.036), (0, front(0, hc[2] - 0.012) - 0.01, hc[2] - 0.012), tone))
    mz = hc[2] - 0.06
    if sexf or child:
        parts.append(K_.box("mouth", (0.032, 0.01, 0.012), (0, front(0, mz) - 0.001, mz), lip))
    else:
        parts.append(K_.box("mouth", (0.044, 0.01, 0.01), (0, front(0, mz) - 0.001, mz), lip, rot=(0, 0, 0.0)))
        parts.append(K_.box("mouthL", (0.012, 0.01, 0.01), (0.026, front(0.026, mz) - 0.001, mz + (0.004 if not old else -0.006)), lip))
        parts.append(K_.box("mouthR", (0.012, 0.01, 0.01), (-0.026, front(-0.026, mz) - 0.001, mz + (0.004 if not old else -0.006)), lip))
    if old: parts.append(K_.box("forehead", (0.07, 0.008, 0.005), (0, front(0, ez + 0.085) - 0.002, ez + 0.085), tone))
    add("Head", *parts)


# ─────────────────────────────── 철삭 ───────────────────────────────
def link_ring(name, c, ang, m, L=0.085, Wd=0.05, t=0.014):
    """사슬 고리 하나(운동장 모양 고리, 상자 6개). 긴 쪽이 Z. ang=0이면 XZ 면, ang=pi/2이면 YZ 면(번갈아 끼우면 서로 직각으로 맞물려 보인다)."""
    s, cz = math.sin(ang), math.cos(ang)
    def at(u, w): return (c[0] + u * cz, c[1] + u * s, c[2] + w)   # 고리 면 안의 좌표(u 가로, w 세로)를 세계로
    hl = L / 2; side = L - Wd * 0.8
    o = [box(f"{name}s{i}", (t, t, side), at(sx * (Wd / 2 - t / 2), 0), m, rot=(0, 0, ang)) for i, sx in enumerate((1, -1))]
    for j, sz in enumerate((1, -1)):
        for i, sx in enumerate((1, -1)):
            o.append(box(f"{name}e{j}{i}", (Wd * 0.46, t, t), at(sx * Wd * 0.19, sz * (hl - t * 0.9 - Wd * 0.1 * (1 if i == 0 else 1))), m, rot=(0, -sx * sz * 0.55, 0) if ang == 0 else (0, 0, ang) if False else (0, -sx * sz * 0.55, ang)))
    return o

def chain2():
    """철삭 2차: 가죽 감은 손잡이 + 놋 마개와 붉은 매듭 술 + 쇠 받침 + 맞물린 사슬 고리 + 천도빛 띠를 두른 철추.
    원점=쥐는 곳, 길이 방향 +Z. 사슬은 살짝 휘어 늘어지는 곡선(뻣뻣한 일직선 탈피)."""
    cm = mat("chain", 0.5); p = []
    p += [cyl("grip", 0.034, 0.034, 0.3, (0, 0, -0.15), "wood_dark", 8)]
    for i in range(5): p.append(cyl(f"wrap{i}", 0.039, 0.039, 0.022, (0, 0, -0.13 - i * 0.045 + 0.04), "hanji", 8))
    p += [sphere("pommel", 0.05, (0, 0, -0.19), "gold", 7, 5), cyl("capB", 0.045, 0.045, 0.025, (0, 0, -0.165), "gold", 8)]
    p += ribbon("tassel", [(0.0, 0.0, -0.22), (0.02, 0.01, -0.34), (0.015, 0.0, -0.38)], 0.035, "red") + ribbon("tassel2", [(0.0, 0.0, -0.22), (-0.025, 0.012, -0.32), (-0.02, 0.0, -0.34)], 0.03, "red")
    p += [cyl("guard", 0.055, 0.08, 0.07, (0, 0, 0.15), "iron", 8), cyl("guard2", 0.08, 0.08, 0.018, (0, 0, 0.22), "iron", 8), cyl("socket", 0.03, 0.03, 0.04, (0, 0, 0.238), "gold", 8)]
    n = 8
    for i in range(n):   # 곡선으로 늘어진 사슬 고리
        t = i / (n - 1); z = 0.3 + i * 0.065
        p += link_ring(f"lk{i}", (0.035 * math.sin(math.pi * t), 0, z), 0 if i % 2 == 0 else math.pi / 2, cm)
    zt = 0.3 + n * 0.065
    p += [sphere("weight", 0.075, (0.0, 0, zt + 0.07), "iron", 7, 5, (1, 1, 1.1)), cyl("bolt", 0.03, 0.03, 0.05, (0, 0, zt - 0.02), "iron", 6),
          cyl("band", 0.078, 0.078, 0.02, (0, 0, zt + 0.07), mat("cheondo", 2.0), 8)]
    for i in range(4):
        a = i * math.pi / 2 + 0.4
        p.append(limb(f"stud{i}", (math.cos(a) * 0.06, math.sin(a) * 0.06, zt + 0.09), (math.cos(a) * 0.12, math.sin(a) * 0.12, zt + 0.1), 0.02, 0.0, "iron", 4))
    p.append(cyl("spike", 0.05, 0.0, 0.19, (0, 0, zt + 0.14), "iron", 6))
    return p

def chain_wrap2():
    """주인공 오른손에 감긴 사슬(손 위치가 원점): 고리 6개로 팔찌처럼 감고, 고리 4개가 늘어진다."""
    cm = mat("chain", 0.5); p = []
    for i in range(6):
        a = i / 6 * math.tau
        p += link_ring(f"w{i}", (math.cos(a) * 0.1, math.sin(a) * 0.1, 0.02), a + math.pi / 2 if False else 0, cm, 0.06, 0.04, 0.012)
    for i in range(4):
        p += link_ring(f"d{i}", (-0.05, -0.04, -0.1 - i * 0.07), 0 if i % 2 == 0 else math.pi / 2, cm, 0.08, 0.045, 0.013)
    return p
