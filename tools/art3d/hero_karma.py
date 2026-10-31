"""업 칸(10·30·60)이 오를 때 주인공이 조금씩 흑월을 닮아 가는 덧붙임 모델 9벌.
왜 덧붙임인가: 주인공 몸·뼈·동작은 하나도 건드리지 않는다. 업 칸이 바뀌면 코드가 아래 파일을 켜고 끌 뿐이라 옛 동작·장비와 충돌이 없다.
방향(기획): 벌이 아니라 "다른 길". 그래서 ① 때 묻은 얼룩이 아니라 '붓으로 번진 먹'(젖은 먹 = 보라빛 테두리가 살짝 도는 짙은 먹색) ② 갓·도포 끝·바닥에만 ③ 천도색 눈과 붉은 허리띠는 그대로 남긴다(차사는 차사).
흑월을 닮은 점(B-04/B-12): 검은 도포 · 몸을 감은 사슬 고리 셋 · 갓 위로 퍼지는 먹. 세 칸은 쌓인다(파일 하나가 그 칸의 전부, 높은 칸이 낮은 칸을 포함).
  10 「그늘」: 갓 챙·도포 밑단 끝에 먹 방울, 발밑에 먹 웅덩이.
  30 「흑월의 걸음」: + 갓에서 피어오르는 먹 가닥 둘(바람에 날리는 갓끈처럼), 갓 챙에 먹 띠가 번져 넓어짐, 허리에 사슬 고리 하나, 웅덩이가 번지며 먹 튀김 점.
  60 「검은 갓」: + 갓 전체를 덮는 검은 덧갓(조금 더 높고 넓음), 먹 가닥 넷(더 길게), 사슬 고리 셋, 눈 위 붉은 눈초리 선, 웅덩이가 크고 도포 자락을 타고 오름.
24 m 폰에서 읽히려면 얇은 방울은 소용없다 → 눈에 보이는 건 ① 바닥 웅덩이(주인공보다 넓게) ② 갓 위 먹 가닥(실루엣을 키 +0.6 m) ③ 붉은 사슬 고리(색 대비) 셋이다. 방울·덧갓·눈초리는 가까이 볼 때 보태는 것.
파일·붙이는 곳: hero_karma_head_{10,30,60}.glb = 원점이 머리 중심(0,0,1.6) → Head 뼈에 그대로 붙임 / hero_karma_body_{10,30,60}.glb = 원점 발밑 → 주인공 뿌리에 붙임 / hero_karma_floor_{10,30,60}.glb = 원점 발밑, 바닥에 눕힌 것 → 회전은 따라가지 않게(월드 yaw 0) 발밑 따라다니기.
규약: 1유닛=1m, 정면=-Y, 발광 없는 불투명 재질만(웅덩이 번짐 투명도는 코드). 실행: python3 hero_karma.py → assets3d/characters/ + unity Models/Hero/ + assets3d/characters/_hero_karma.json"""
import sys, os, math, json, random, shutil
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d", "characters"); UNITY = os.path.join(OUT, "..", "..", "unity", "Assets", "Resources", "Models", "Hero")
INKB = "#0B0912"       # 젖은 먹
RIM = "#3F3656"        # 먹이 빛을 받는 보라 테두리(어두운 바닥·도포 위에서도 먹이 '번졌다'고 읽히는 얇은 선)
DEEP = "#05040A"       # 검은 덧갓
RED = "#E85C41"; IRON = "#3A3A44"; DARK_RED = "#C43428"
HEAD_Z = 1.6

def drop(name, x, y, z, ln, r, m):
    """매달린 먹 방울: 위가 굵고 아래로 뾰족(위에서 아래로 흐르는 먹)."""
    return limb(name, (x, y, z), (x, y, z - ln), r, 0.004, m, 5)

def pool(R, seed, tend, tend_len):
    """바닥 먹 웅덩이: 납작한 타원 여러 개를 겹쳐 울퉁불퉁하게 + 가장자리 보라 테두리 + 바깥으로 뻗는 가닥. 높이 0.02 m(바닥 위로 살짝)."""
    rnd = random.Random(seed); out = []; mi = mat(INKB); mr = mat(RIM)
    for k in range(9):
        a = rnd.random() * math.tau; d = R * 0.45 * rnd.random(); rr = R * (0.62 + 0.3 * rnd.random())
        out.append(sphere(f"pool{k}", rr, (math.cos(a) * d, math.sin(a) * d, 0.0), mi, 10, 3, scale=(1, 1, 0.045)))
        out.append(sphere(f"poolr{k}", rr + 0.035, (math.cos(a) * d, math.sin(a) * d, -0.012), mr, 10, 3, scale=(1, 1, 0.04)))
    for k in range(tend):      # 가닥(다리) 대신 붓 튀김: 웅덩이 둘레에 흩어진 먹 점(큰 것 → 작은 것). 뻗는 다리처럼 보이면 괴물 같아서 점으로만 번지게 한다
        a = k / max(1, tend) * math.tau + rnd.random() * 0.6; rr = R * 1.0 + tend_len * (0.3 + 0.7 * rnd.random()); sz = 0.11 - 0.07 * (rr - R) / max(0.1, tend_len)
        out.append(sphere(f"fleck{k}", max(0.03, sz), (math.cos(a) * rr, math.sin(a) * rr, 0.0), mi, 8, 3, scale=(1, 1, 0.05)))
    return out

def wisps(n, ln, seed):
    """갓에서 한쪽(바람 방향 +X 뒤쪽)으로 날리는 먹 가닥: 갓끈이 바람에 날리듯 위로 오르다 옆으로 휘며 가늘어진다. 곧추선 뿔·가시는 괴물처럼 읽혀 쓰지 않는다. 밑동 0.05 m."""
    rnd = random.Random(seed); out = []; mi = mat(INKB); mr = mat(RIM)
    for k in range(n):
        a = math.radians(200 + 60 * k / max(1, n - 1) - 30 + rnd.random() * 20); r0 = 0.34; h0 = 0.10; L = ln * (0.8 + 0.4 * rnd.random()); sgn = 1
        pts = [(math.cos(a) * r0 + 0.38 * t * t * L, math.sin(a) * r0 * 0.9 + 0.10 * math.sin(t * 5 + k * 2), h0 + L * 0.62 * t - 0.15 * t * t * L) for t in (0, 0.2, 0.45, 0.72, 1.0)]
        out += chain_pts(f"wisp{k}", pts, 0.05, 0.006, mi, 5)
        out += chain_pts(f"wispr{k}", [(x, y, z + 0.012) for x, y, z in pts], 0.056, 0.01, mr, 5)
    return out

def chain_ring(z, r, name):
    """허리·가슴을 감은 사슬 고리 하나: 쇠 고리 + 둘레에 붉은 고리쇠(색 대비로 24 m에서도 읽힘). 흑월의 사슬 고리와 같은 모양."""
    out = [cyl(name, r, r, 0.06, (0, 0, z - 0.03), mat(IRON), 14)]; n = 8
    for k in range(n):
        a = k / n * math.tau; out.append(box(f"{name}_l{k}", (0.1, 0.045, 0.1), (math.cos(a) * (r + 0.01), math.sin(a) * (r + 0.01), z), mat(DARK_RED if k % 2 else RED), rot=(0, 0, a + math.pi / 2)))
    return out

def head_parts(tier):
    """원점=머리 중심. 좌표는 영웅 좌표에서 HEAD_Z를 뺀 값으로 짓는다."""
    mi = mat(INKB); mr = mat(RIM); out = []; rnd = random.Random(10)
    # 갓 챙 가장자리 먹 방울: 챙 반지름 0.43(영웅은 y 0.9 눌림)·높이 1.69
    n = 8 if tier == 10 else 12
    for k in range(n):
        a = k / n * math.tau + 0.2; x = math.cos(a) * 0.405; y = math.sin(a) * 0.405 * 0.9
        out.append(drop(f"bdrop{k}", x, y, 1.675 - HEAD_Z, 0.09 + 0.1 * rnd.random() + (0.04 if tier > 10 else 0), 0.032, mi))
    if tier >= 30:
        # 넓어진 챙: 챙 가장자리를 둘러싼 얇은 먹 띠(반지름 0.43→0.50, 가장자리는 완만한 물결) — 가시 없이 '번진' 느낌
        out.append(lathe("brim_ink", [(1.675 - HEAD_Z, 0.38), (1.683 - HEAD_Z, 0.46), (1.676 - HEAD_Z, 0.5), (1.668 - HEAD_Z, 0.46), (1.668 - HEAD_Z, 0.38)], 20, mi, scale=(1.0, 0.9, 1.0), fn=lambda i, k, th, z, r: (r * (1 + (0.035 * math.sin(5 * th + 1) if r > 0.45 else 0)), z), caps=(False, False)))
        out += wisps(2 if tier == 30 else 4, 0.55 if tier == 30 else 0.8, 30)
    if tier >= 60:
        # 검은 덧갓: 챙·모자를 한 겹 더 씌운 순흑 껍질(영웅 갓은 #14141F, 이건 #05040A). 약간 더 높고 넓음.
        brim = lathe("cap_brim", [(1.668, 0.0), (1.672, 0.24), (1.683, 0.39), (1.698, 0.455), (1.704, 0.47), (1.694, 0.455), (1.672, 0.33), (1.675, 0.0)], 18, mat(DEEP), scale=(1.0, 0.9, 1.0), loc=(0, 0, -HEAD_Z))
        crown = lathe("cap_crown", [(1.68, 0.135), (1.75, 0.13), (1.86, 0.128), (1.975, 0.13), (1.99, 0.124), (1.992, 0.0)], 14, mat(DEEP), scale=(1.0, 0.95, 1.0), loc=(0, 0, -HEAD_Z))
        out += [brim, crown]
        # 눈초리: 천도색 눈(영웅 모델)은 그대로 두고 눈 위에 붉은 짧은 선만(차사의 눈은 지우지 않는다)
        for sx in (1, -1):
            out.append(box(f"eyeliner{sx}", (0.075, 0.012, 0.012), (0.055 * sx, -0.119, 1.628 - HEAD_Z), mat(RED, 1.0), rot=(0, 0, 0.18 * sx)))
    return out

def body_parts(tier):
    """원점=발밑. 도포 밑단(반지름 약 0.215·z 0~0.3)에 먹 혀(아래로 갈수록 가는 방울 혀)가 둘러 있다. 30은 사슬 1, 60은 3."""
    mi = mat(INKB); mr = mat(RIM); out = []; rnd = random.Random(20)
    n = 14 if tier == 10 else 18; top = 0.30 if tier == 10 else (0.38 if tier == 30 else 0.55)
    for k in range(n):
        a = k / n * math.tau + 0.1; r = 0.235 + 0.02 * math.sin(a * 3); ln = top * (0.55 + 0.45 * rnd.random())
        out.append(limb(f"hem{k}", (math.cos(a) * r, math.sin(a) * r * 0.86, 0.04 + ln), (math.cos(a) * (r + 0.02), math.sin(a) * (r + 0.02) * 0.86, 0.01), 0.055, 0.012, mi, 5))
        out.append(limb(f"hemr{k}", (math.cos(a) * (r + 0.03), math.sin(a) * (r + 0.03) * 0.86, 0.04 + ln * 0.9), (math.cos(a) * (r + 0.05), math.sin(a) * (r + 0.05) * 0.86, 0.015), 0.012, 0.006, mr, 4))
    if tier >= 30: out += chain_ring(0.62, 0.34, "chain0")
    if tier >= 60: out += chain_ring(1.0, 0.31, "chain1") + chain_ring(1.3, 0.31, "chain2")
    return out

def floor_parts(tier):
    return pool(0.7, 1, 0, 0) if tier == 10 else (pool(0.95, 2, 7, 0.45) if tier == 30 else pool(1.2, 3, 14, 0.6))

def build_all():
    info = {}
    for tier in (10, 30, 60):
        for kind, fn in (("head", head_parts), ("body", body_parts), ("floor", floor_parts)):
            reset(); parts = fn(tier); o = join(f"hero_karma_{kind}_{tier}", parts); p = os.path.join(OUT, f"hero_karma_{kind}_{tier}.glb"); export(o, p)
            lo, hi = bounds(o); info[f"{kind}_{tier}"] = {"tris": tris(o), "bounds_min": [round(v, 2) for v in lo], "bounds_max": [round(v, 2) for v in hi]}
            os.makedirs(UNITY, exist_ok=True); shutil.copy(p, os.path.join(UNITY, os.path.basename(p)))
    json.dump(info, open(os.path.join(OUT, "_hero_karma.json"), "w"), ensure_ascii=False, indent=1); return info

if __name__ == "__main__":
    for k, v in build_all().items(): print(k, v)
