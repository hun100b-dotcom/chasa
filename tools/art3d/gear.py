"""장비 외형 5등급 모델: 갓·도포·띠·신·노리개(무기는 따로). 실행: python3 gear.py [slot ...]
근거: planning/growth/section6.md 6-3(칸·등급 5단계: 흔한 미색 #F3E7D3 / 손본 청록 #4FA8A0 / 귀한 금빛 #D4A94E / 이름 있는 주홍 #E85C41 / 한 벌 혼불 #5FE3C0).
방식: 주인공(look_v2.hero2)과 같은 뼈대(characters.BONES)·같은 위치에 맞춘 '갈아끼우는 조각'. 조각마다 hero_chasa.glb처럼 뼈대를 달고(apply=False) 내보내므로
코드는 같은 뼈 이름으로 조각을 바꿔 끼우면 된다(기본 모양의 해당 부분은 숨긴다). 조각마다 등급이 올라갈수록 ① 재질이 좋아지고 ② 장식이 늘고 ③ 등급 색이 눈에 띄게 들어간다.
등급 색은 장르 관습이라 써도 되고(IP 안전선 2-3), 실루엣은 등급마다 다르게 해 색을 못 봐도 구분되게 했다(갓끈 길이, 띠 끝, 신 코, 노리개 모양).
'이름 있는' 등급은 보스마다 고유 물건이 따로 있다(월화의 방울 등): 여기서는 그 계열이 공유하는 '주홍 외형'만 만들고, 고유 물건은 나중에 이 위에 얹는다.
출력: assets3d/gear/gear_{slot}_t{1..5}.glb(노리개는 _R/_L 둘씩), _manifest_gear.json, previews/gear_tiers.png(등급별 전신 5체)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import BONES, rig
from look_v2 import grp, blend, ribbon
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
TIER = {1: ("흔한", "#F3E7D3"), 2: ("손본", "#4FA8A0"), 3: ("귀한", "#D4A94E"), 4: ("이름 있는", "#E85C41"), 5: ("한 벌", "#5FE3C0")}
def tc(t): return TIER[t][1]
def glow(t, e=1.8): return mat(tc(t), e)

# ───────── 갓(흑립) → Head ─────────
def gat(t):
    """갓: 챙·모자는 흑립 그대로(등급이 올라도 검다), 갓끈·구슬·띠·장식으로 등급을 보인다. t1 삼끈 / t2 청록 끈 구슬 / t3 금 끈·금 판·금테 / t4 주홍 긴 끈(패영 구슬 5)·깃 장식 / t5 혼불 발광 끈·구슬·정수리 불티."""
    hatc = ["#2A2A34", "#242630", "#1E1E2A", "#1A1A24", "#16161E"][t - 1]
    brim_r = [(1.662, 0.125), (1.664, 0.22), (1.668, 0.33), (1.676, 0.41), (1.69, 0.43), (1.682, 0.41), (1.664, 0.3), (1.668, 0.2), (1.672, 0.125)]
    parts = [lathe("hat_brim", brim_r, 18, hatc, scale=(1.0, 0.9, 1.0), fn=lambda i, k, th, z, r: (r, z - (0.008 * math.cos(2 * th) if r > 0.25 else 0.0))),
             lathe("hat_crown", [(1.675, 0.128), (1.74, 0.122), (1.84, 0.12), (1.93, 0.123), (1.945, 0.118), (1.947, 0.0)], 14, hatc, scale=(1.0, 0.95, 1.0))]
    if t == 1: band = cyl("hat_band", 0.129, 0.127, 0.025, (0, 0, 1.7), "#A8987A", 12); strapc = "#B8A888"; bead = None
    elif t == 2: band = cyl("hat_band", 0.129, 0.127, 0.035, (0, 0, 1.7), tc(2), 12); strapc = tc(2); bead = tc(2)
    elif t == 3: band = cyl("hat_band", 0.129, 0.127, 0.04, (0, 0, 1.7), "red", 12); strapc = "#7A2A2A"; bead = tc(3)
    elif t == 4: band = cyl("hat_band", 0.129, 0.127, 0.045, (0, 0, 1.7), tc(4), 12); strapc = tc(4); bead = tc(4)
    else: band = cyl("hat_band", 0.129, 0.127, 0.045, (0, 0, 1.7), glow(5), 12); strapc = glow(5); bead = glow(5, 2.2)
    parts.append(band)
    if t >= 3: parts.append(lathe("brim_edge", [(1.676, 0.405), (1.69, 0.43)], 18, tc(3) if t == 3 else (tc(4) if t == 4 else glow(5, 1.2)), scale=(1.0, 0.9, 1.0), caps=(False, False)))     # 챙 가장자리 금테
    if t >= 3: parts.append(box("hat_plate", (0.07, 0.02, 0.08), (0, -0.126, 1.755), tc(3) if t == 3 else (tc(4) if t == 4 else glow(5))))
    for sx in (1, -1):
        L = 5 if t >= 4 else 3
        pts = [(sx * 0.12, -0.04, 1.665), (sx * 0.105, -0.1, 1.54), (sx * 0.095, -0.14, 1.42), (sx * 0.075, -0.19, 1.28), (sx * 0.07, -0.205, 1.12)] + ([(sx * 0.07, -0.21, 0.98), (sx * 0.07, -0.215, 0.86)] if t >= 4 else [])
        parts += chain_pts("strap" + ("L" if sx > 0 else "R"), pts, 0.011 if t < 4 else 0.014, 0.009, strapc, 4)
        if bead: parts += [sphere(f"bead{sx}{i}", 0.02 + (0.004 if t >= 4 else 0), (sx * (0.105 - i * 0.012), -0.1 - i * 0.045, 1.54 - i * 0.14), bead, 5, 4) for i in range(L)]
    if t == 4:   # 이름 있는 갓: 뒤로 크게 휘어 올라가는 주홍 깃 둘 + 챙 끝에 늘어진 이름 쪽지 넷(멀리서도 '갓 뒤가 솟은' 실루엣)
        for sx in (1, -1): parts += ribbon(f"plume{sx}", [(sx * 0.07, 0.06, 1.8), (sx * 0.14, 0.16, 1.93), (sx * 0.16, 0.28, 2.04), (sx * 0.12, 0.38, 2.1)], 0.075, "#E85C41", 0.02)
        for i, (x, y) in enumerate(((0.36, -0.16), (-0.36, -0.16), (0.3, 0.26), (-0.3, 0.26))): parts += [limb(f"tagcord{i}", (x, y, 1.69), (x, y, 1.52), 0.008, 0.008, tc(4), 3), box(f"tag{i}", (0.07, 0.012, 0.13), (x, y, 1.45), "#E4E0D4")]
    if t == 5:   # 한 벌 갓: 정수리 위에 떠 있는 혼불 고리(◎) + 고리를 도는 혼불 여섯. 고리는 갓과 이어지지 않아 '떠 있는 빛'으로 읽힘
        from fx import annulus
        parts.append(annulus("halo_hat", 0.17, 0.215, 0.02, 2.2, glow(5, 2.8), 18)); parts.append(annulus("halo_hat2", 0.08, 0.1, 0.02, 2.2, glow(5, 2.8), 12))
        parts += [sphere(f"mote{i}", 0.018, (0.26 * math.cos(a), 0.26 * math.sin(a), 2.2 + 0.03 * math.sin(a * 2)), glow(5, 3.2), 4, 3) for i, a in enumerate([k * math.tau / 6 for k in range(6)])]
    return grp(parts, "Head")

# ───────── 도포 → Hips(자락) · Spine/Chest(몸통) · UpperArm(소매) ─────────
def dopo(t):
    """도포: t1 삼베 미색 베옷(안감 없음, 끝동 미색) / t2 쪽빛+청록 끝동·밑단 / t3 남색+금 세로 자수 셋·금 끝동 / t4 먹빛+주홍 안감이 트임으로 보임·이름 쪽지 셋(글자 없음) / t5 먹빛+혼불 발광 밑단 실·소매 끝 실·어깨 불티."""
    cloth = ["#8A8068", "#2F4560", "#2A3050", "#24242C", "#1E2028"][t - 1]; skirtc = ["#7C735E", "#26364C", "#222844", "#1C1C24", "#16181E"][t - 1]; trim = tc(t)
    R = [(0.05, 0.47), (0.14, 0.43), (0.32, 0.355), (0.55, 0.285), (0.78, 0.235), (0.97, 0.215)]
    def pleat(i, k, th, z, r): a = 0.11 * (1 - z / 1.1); zz = z + (0.03 * math.sin(3 * th + 0.6) + 0.015 * (1 if k % 2 else -1) if i == 0 else 0); return r * (1 + a * (1 if k % 2 else -1)), zz
    parts_h = [lathe("skirt", R, 14, skirtc, scale=(1.0, 0.86, 1.0), fn=pleat, skip=lambda i, k: i <= 2 and k == 10)]
    liningc = {1: skirtc, 2: "#1E2C40", 3: "#1C2038", 4: tc(4), 5: "#10141A"}[t]
    parts_h.append(lathe("lining", [(0.07, 0.40), (0.3, 0.33), (0.6, 0.25), (0.95, 0.2)], 14, liningc, scale=(1.0, 0.8, 1.0)))
    hemc = trim if t != 5 else glow(5, 1.6)
    parts_h.append(lathe("skirt_hem", [(0.035, 0.485), (0.1, 0.455)], 14, hemc, scale=(1.0, 0.86, 1.0), fn=pleat, caps=(False, False), skip=lambda i, k: k == 10))
    for sx in (1, -1): parts_h += ribbon(f"skirt_back{sx}", [(sx * 0.09, 0.2, 0.88), (sx * 0.12, 0.3, 0.5), (sx * 0.16, 0.38, 0.1)], 0.17, cloth, 0.022)
    if t == 3: parts_h += [box(f"embroid{i}", (0.02, 0.012, 0.5), (-0.16 + i * 0.16, -0.262, 0.5), tc(3), rot=(0.1, 0, 0)) for i in range(3)]      # 앞자락 금 세로 자수
    if t == 4: parts_h += [box(f"nametag{i}", (0.08, 0.012, 0.11), (-0.2 + i * 0.2, -0.265, 0.55 - 0.1 * (i % 2)), "#E4E0D4", rot=(0.1, 0, 0.1 * (i - 1))) for i in range(3)]     # 이름 쪽지(글자 없음)
    parts = grp(parts_h, "Hips")
    T = lathe("torso", [(0.93, 0.215), (1.08, 0.225), (1.22, 0.24), (1.34, 0.255), (1.41, 0.2), (1.46, 0.085)], 10, cloth, scale=(1.14, 0.78, 1.0)); blend(T, [(0.97, "Hips"), (1.15, "Spine"), (1.36, "Chest")]); parts.append(T)
    col = [lathe("collar_ring", [(1.4, 0.108), (1.47, 0.092)], 10, "#E4E0D4" if t < 3 else trim, scale=(1.0, 0.9, 1.0), caps=(False, False))]
    col += ribbon("lapL", [(0.07, -0.15, 1.44), (0.0, -0.205, 1.25), (-0.07, -0.222, 1.06)], 0.085, skirtc) + ribbon("lapL_edge", [(0.095, -0.158, 1.44), (0.02, -0.21, 1.25), (-0.045, -0.227, 1.06)], 0.018, trim, 0.016)
    col += ribbon("lapR", [(-0.07, -0.15, 1.44), (-0.01, -0.2, 1.25), (0.05, -0.218, 1.06)], 0.085, cloth) + ribbon("lapR_edge", [(-0.095, -0.158, 1.44), (-0.03, -0.205, 1.25), (0.025, -0.222, 1.06)], 0.016, trim, 0.016)
    if t == 5: col += [sphere(f"sparkle{i}", 0.014, (-0.12 + i * 0.12, -0.18, 1.47), glow(5, 3.0), 4, 3) for i in range(3)]      # 어깨 불티
    parts += grp(col, "Chest")
    extra = []
    if t == 4:   # 이름 있는: 어깨 망토(주홍 가장자리) + 가장자리에 늘어진 이름 쪽지 여덟 — 어깨선이 넓고 술이 달려 먼 실루엣이 둥글게 커진다
        extra.append(lathe("mantle", [(1.43, 0.2), (1.34, 0.33), (1.2, 0.37)], 12, "#24242C", scale=(1.14, 0.8, 1.0), caps=(False, False)))
        extra.append(lathe("mantle_edge", [(1.215, 0.372), (1.19, 0.378)], 12, tc(4), scale=(1.14, 0.8, 1.0), caps=(False, False)))
        extra += [box(f"mtag{i}", (0.06, 0.012, 0.15), (math.cos(i / 8 * math.tau) * 0.42, math.sin(i / 8 * math.tau) * 0.3, 1.1), "#E4E0D4", rot=(0, 0, i / 8 * math.tau + 1.57)) for i in range(8)]
    if t == 5:   # 한 벌: 등 뒤 혼불 후광(세운 겹 고리) + 어깨에서 바깥으로 흐르는 혼불 자락 둘 — 먹빛 몸에서 빛이 뻗는 실루엣
        from fx import annulus
        h1 = annulus("halo_back", 0.44, 0.5, 0.025, 0.0, glow(5, 2.4), 22); h1.rotation_euler = (math.pi / 2, 0, 0); h1.location = (0, 0.3, 1.5)
        h2 = annulus("halo_back2", 0.3, 0.33, 0.02, 0.0, glow(5, 2.4), 18); h2.rotation_euler = (math.pi / 2, 0, 0); h2.location = (0, 0.3, 1.5)
        extra += [h1, h2]
        for sx in (1, -1): extra += ribbon(f"flow{sx}", [(sx * 0.2, 0.17, 1.36), (sx * 0.38, 0.3, 1.12), (sx * 0.52, 0.42, 0.88), (sx * 0.6, 0.55, 0.7)], 0.11, glow(5, 1.5), 0.02)
    parts += grp(extra, "Chest")
    A = 0.5
    for sx, side in ((1, "L"), (-1, "R")):
        sh = (sx * 0.23, 0, 1.4); d = Vector((sx * math.sin(A), 0, -math.cos(A))); theta = math.pi - sx * A
        sr = [(0.0, 0.062), (0.1, 0.085), (0.26, 0.135), (0.44, 0.175), (0.57, 0.195), (0.595, 0.19)]
        def sl(i, k, th, z, r): return r * (1 + 0.09 * (z / 0.6) * (1 if k % 2 else -1)), z + (0.02 * math.sin(2 * th + 1) if i >= 4 else 0)
        cuffc = {1: "#F3E7D3", 2: trim, 3: trim, 4: trim, 5: glow(5, 1.5)}[t]
        arm = [lathe(f"sleeve_{side}", sr, 10, cloth, loc=sh, rot=(0, theta, 0), fn=sl),
               lathe(f"cuff_{side}", [(0.575, 0.2), (0.62, 0.198)], 10, cuffc, loc=sh, rot=(0, theta, 0), caps=(False, False), fn=lambda i, k, th, z, r: (r, z + (0.02 * math.sin(2 * th + 1)))),
               lathe(f"cuff_in_{side}", [(0.6, 0.17), (0.6, 0.0)], 10, "#14141C", loc=sh, rot=(0, theta, 0), caps=(False, False))]
        parts += grp(arm, f"UpperArm.{side}")
    return parts

# ───────── 띠 → Hips ─────────
def tti(t):
    """띠: t1 삼 끈(가늘고 끝이 짧다) / t2 청록 띠·짧은 끝 둘 / t3 붉은 띠에 금 테·금 매듭·긴 끝 / t4 주홍 넓은 띠·방울 매듭·가장 긴 끝 셋 / t5 혼불 발광 테·끝에 불티. 끝(늘어진 자락)의 수와 길이가 등급마다 달라 실루엣으로도 구분된다."""
    w = [0.07, 0.11, 0.15, 0.19, 0.19][t - 1]; main = ["#A8987A", tc(2), "#B83A32", tc(4), "#E85C41"][t - 1]
    sash = cyl("sash", 0.245, 0.245, w, (0, 0, 0.9 + (0.15 - w) / 2), main, 10); sash.scale = (1.0, 0.9, 1.0)
    knot = box("sash_knot", (0.13, 0.07, 0.12), (0.1, -0.265, 0.97), {1: "#8A7A5A", 2: tc(2), 3: tc(3), 4: tc(4), 5: glow(5)}[t])
    parts = [sash, knot]
    if t >= 3: parts.append(cyl("sash_edge_top", 0.249, 0.249, 0.015, (0, 0, 1.04), tc(3) if t == 3 else (tc(3) if t == 4 else glow(5, 1.6)), 10))
    L = [0.3, 0.46, 0.74, 0.86, 0.86][t - 1]
    parts += ribbon("tailA", [(0.09, -0.27, 0.94), (0.12, -0.31, 0.94 - L * 0.4), (0.17, -0.34, 0.94 - L * 0.75), (0.14, -0.38, 0.94 - L)], 0.075 if t > 1 else 0.04, main)
    if t >= 2: parts += ribbon("tailB", [(0.14, -0.27, 0.93), (0.22, -0.3, 0.93 - L * 0.3), (0.3, -0.31, 0.93 - L * 0.55)], 0.06, main)
    if t >= 4: parts += ribbon("tailC", [(0.04, -0.27, 0.93), (-0.02, -0.31, 0.93 - L * 0.4), (-0.06, -0.33, 0.93 - L * 0.65)], 0.06, main) + [sphere("bell", 0.035, (0.1, -0.3, 0.94), tc(3), 5, 4)]
    if t == 5: parts += [sphere(f"spark{i}", 0.013, (0.15 + 0.03 * i, -0.4, 0.2 + 0.1 * i), glow(5, 3.0), 4, 3) for i in range(3)]
    return grp(parts, "Hips")

# ───────── 신 → Foot.L/R ─────────
def sin_(t):
    """신: t1 짚신(납작, 끈 둘) / t2 청록 헝겊신 / t3 검은 가죽신+금 코 장식 / t4 주홍 코가 높이 올라간 신+뒤 술 / t5 혼불 발광 밑창 선. 코의 높이와 장식이 등급마다 다르다."""
    parts = []
    for sx, side in ((1, "L"), (-1, "R")):
        body = {1: "#B8A888", 2: "#2A3A4A", 3: "#1E1E26", 4: "#2A1E20", 5: "#14161C"}[t]; toe = {1: "#9A8A6A", 2: tc(2), 3: tc(3), 4: tc(4), 5: glow(5)}[t]; th = [0.04, 0.07, 0.075, 0.08, 0.08][t - 1]; lift = [0.2, 0.5, 0.5, 0.8, 0.7][t - 1]
        p = [box(f"shoe_{side}", (0.12, 0.2, th), (sx * 0.13, -0.06, th / 2), body), box(f"toe_{side}", (0.09, 0.09, 0.06), (sx * 0.13, -0.19, th + 0.005 + 0.012 * lift), toe if t != 5 else body, rot=(lift, 0, 0))]
        if t == 1: p += [box(f"strawcord{i}", (0.13, 0.015, 0.02), (sx * 0.13, -0.02 - i * 0.08, 0.045), "#8A7A5A") for i in range(2)]
        if t >= 2: p.append(box(f"trim_{side}", (0.125, 0.02, 0.02), (sx * 0.13, 0.03, th + 0.005), toe))
        if t == 4:   # 이름 있는: 코가 뿔처럼 위로 말려 오르고(실루엣), 발목에 이름 쪽지 둘, 뒤꿈치에서 주홍 술이 뒤로 길게 끌린다
            p += [limb(f"horn_toe_{side}", (sx * 0.13, -0.17, th), (sx * 0.13, -0.27, 0.2), 0.05, 0.008, tc(4), 5), box(f"heel_tuft_{side}", (0.03, 0.03, 0.07), (sx * 0.13, 0.05, 0.08), tc(4))]
            p += ribbon(f"heel_tail_{side}", [(sx * 0.13, 0.07, 0.07), (sx * 0.13, 0.17, 0.05), (sx * 0.14, 0.3, 0.1)], 0.04, tc(4))
            p += [box(f"ankle_tag{i}_{side}", (0.035, 0.01, 0.07), (sx * (0.13 + (i - 0.5) * 0.07), 0.0, 0.13), "#F3E7D3") for i in range(2)]
        if t == 5: p += [box(f"sole_glow_{side}", (0.125, 0.205, 0.012), (sx * 0.13, -0.06, 0.003), glow(5, 2.2))]
        if t == 5:   # 한 벌: 발목에 둘린 혼불 고리 + 뒤꿈치에서 흩날리는 혼불 자락(투명) — 신만 봐도 ◎ 계열
            from fx import annulus as _an
            ar = _an(f"ankle_ring_{side}", 0.075, 0.1, 0.012, 0.12, glow(5, 2.4), 12); ar.location = (sx * 0.13, -0.04, 0)
            p += [ar] + ribbon(f"wisp_{side}", [(sx * 0.13, 0.06, 0.1), (sx * 0.16, 0.2, 0.18), (sx * 0.12, 0.34, 0.3)], 0.05, mat_alpha("#5FE3C0", 0.45, 1.6))
        if t == 5 and side == "L":   # 발밑에 번지는 혼불 겹 고리(◎): 바닥에 평평히 깔려 쿼터뷰에서 발을 둘러 빛난다
            from fx import annulus
            p += [annulus("foot_ring", 0.42, 0.47, 0.012, 0.004, glow(5, 2.2), 20), annulus("foot_ring2", 0.3, 0.33, 0.012, 0.004, glow(5, 2.2), 16)]
            for q in p[-2:]: q.location = (-0.0, -0.05, 0)
        parts += grp(p, f"Foot.{side}")
    return parts

# ───────── 노리개 → Hips (오른쪽/왼쪽 허리) ─────────
def norigae(t, side="R"):
    """노리개: 허리띠에 매다는 장식. t1 매듭 하나+삼 술 / t2 옥 구슬 하나+청록 술 / t3 금 장식 판+옥+긴 금 술 / t4 방울(월화의 방울 계열)+주홍 술 둘 / t5 혼불 구슬(발광)+발광 술. _R=오른쪽 허리(-X), _L=왼쪽(+X)."""
    sx = -1 if side == "R" else 1; x0 = sx * 0.2; y0 = -0.22
    ink = {1: "#B8A888", 2: tc(2), 3: tc(3), 4: tc(4), 5: glow(5)}[t]
    parts = [box("orn_knot", (0.05, 0.03, 0.05), (x0, y0, 0.89), ink if t != 3 else tc(3))]
    if t == 1: parts += [sphere("bead", 0.03, (x0, y0, 0.83), "#A8987A", 5, 4)]
    if t == 2: parts += [sphere("jade", 0.045, (x0, y0, 0.82), mat("teal", 0.4), 6, 4)]
    if t == 3: parts += [box("plate", (0.07, 0.02, 0.09), (x0, y0, 0.82), tc(3)), sphere("jade", 0.03, (x0, y0 - 0.02, 0.82), mat("teal", 0.5), 5, 4)]
    if t == 4:   # 이름 있는: 방울 위에 세 뿔 관(빛줄기 꼭대기와 같은 말) + 방울 밑에 이름 쪽지가 매달린다
        parts += [sphere("bell", 0.06, (x0, y0, 0.8), tc(3), 7, 5), box("bell_slit", (0.05, 0.012, 0.01), (x0, y0 - 0.055, 0.79), "#6A4A1A")]
        parts += [limb(f"crown{k}", (x0, y0, 0.855), (x0 + (k - 1) * 0.035, y0, 0.855 + (0.075 if k == 1 else 0.05)), 0.014, 0.003, tc(4), 4) for k in range(3)]
        parts += [limb("tag_thread", (x0, y0, 0.74), (x0, y0, 0.69), 0.004, 0.004, "#F3E7D3", 3), box("name_tag", (0.04, 0.01, 0.08), (x0, y0, 0.65), "#F3E7D3")]
    if t == 5:   # 한 벌: 혼불 구슬을 두 겹 고리(◎)가 감싸고 불티 셋이 돈다 + 아래로 흐르는 투명 혼불 자락
        from fx import annulus as _an
        parts += [sphere("orb_core", 0.04, (x0, y0, 0.82), glow(5, 3.0), 6, 4), sphere("orb_shell", 0.07, (x0, y0, 0.82), mat_alpha("#5FE3C0", 0.3, 1.0), 7, 5)]
        for k, (ri, ro) in enumerate(((0.085, 0.1), (0.12, 0.13))):
            ar = _an(f"orb_ring{k}", ri, ro, 0.008, 0.0, glow(5, 2.2), 14); ar.location = (x0, y0, 0.82); ar.rotation_euler = (0.5 * (k + 1), 0, 0.4); parts.append(ar)
        parts += [sphere(f"orb_mote{k}", 0.012, (x0 + math.cos(k * 2.1) * 0.15, y0 + math.sin(k * 2.1) * 0.15, 0.82 + 0.04 * k), glow(5, 3.0), 4, 3) for k in range(3)]
        parts += ribbon("orb_wisp", [(x0, y0, 0.76), (x0 + 0.03 * sx, y0 - 0.02, 0.6), (x0 - 0.02 * sx, y0 - 0.04, 0.44)], 0.06, mat_alpha("#5FE3C0", 0.4, 1.4))
    tl = {1: 0.14, 2: 0.2, 3: 0.3, 4: 0.36, 5: 0.28}[t]; tw = 0.035 if t < 4 else 0.04
    parts += ribbon("tassel", [(x0, y0, 0.78), (x0 + 0.01 * sx, y0 - 0.01, 0.78 - tl * 0.5), (x0, y0 - 0.015, 0.78 - tl)], tw, ink)
    if t == 4: parts += ribbon("tassel2", [(x0 + 0.03 * sx, y0, 0.78), (x0 + 0.05 * sx, y0 - 0.01, 0.78 - tl * 0.7)], 0.03, tc(4))
    return grp(parts, "Hips")

SLOTS = {"gat": gat, "dopo": dopo, "tti": tti, "sin": sin_, "norigae": None}
def build_piece(slot, t, side=None):
    reset(); parts = norigae(t, side) if slot == "norigae" else SLOTS[slot](t)
    name = f"gear_{slot}_t{t}" + (f"_{side}" if side else "")
    o = join(name, parts); rig(o, BONES); lo, hi = bounds(o)
    export(o, os.path.join(OUT, "gear", name + ".glb"), apply=False)
    return {"name": name, "slot": slot, "tier": t, "tier_name": TIER[t][0], "tier_color": tc(t), "tris": tris(o), "size_m": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)], "bones": sorted({vg.name for vg in o.vertex_groups})}
def mannequin():
    """등급 미리보기용 마네킹: 얼굴·목·손만 있는 몸(장비 조각은 따로). 보기용일 뿐 내보내지 않는다."""
    p = [sphere("head", 0.125, (0, 0, 1.585), "face", 10, 7, (1, 0.95, 1.05)), cyl("neck", 0.07, 0.07, 0.1, (0, 0, 1.46), "face", 6)]
    for sx in (1, -1): p.append(sphere("hand", 0.055, (sx * 0.54, 0, 0.85), "face", 6, 4))
    return p
if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("--")]; os.makedirs(os.path.join(OUT, "gear"), exist_ok=True)
    rep = []
    for slot in SLOTS:
        if only and slot not in only: continue
        for t in range(1, 6):
            if slot == "norigae": rep += [build_piece(slot, t, "R"), build_piece(slot, t, "L")]
            else: rep.append(build_piece(slot, t))
    if not only:
        json.dump({"_설명": "장비 5등급 조각. 같은 뼈대 이름(characters.BONES)·주인공과 같은 자리라 뼈 이름으로 바꿔 끼운다. 기본 모양의 해당 부분(갓·도포·띠·신·노리개)을 숨긴 뒤 이 조각을 쓴다.", "tiers": {str(k): {"name": v[0], "color": v[1]} for k, v in TIER.items()}, "pieces": rep}, open(os.path.join(OUT, "gear", "_manifest_gear.json"), "w"), ensure_ascii=False, indent=1)
        reset()
        for t in range(1, 6):
            parts = mannequin() + gat(t) + dopo(t) + tti(t) + sin_(t) + norigae(t, "R") + norigae(t, "L")
            o = join(f"set{t}", parts); o.location = ((t - 3) * 1.4, 0, 0)
        setup_render(7.6, (0, 0, 0.95), elev=20, size=(1800, 700), ground_size=12); render(os.path.join(OUT, "previews", "gear_tiers.png"))
    print(len(rep), "조각")
