"""3막 보스 본체: B-12 흑월 차사(1차 등장에도 같이 씀) 먼저, 이어서 B-09 망부석 아낙, B-10 만선호 선장, B-11 다리 밑 왕초. 실행: python3 boss_act3.py [이름 ...] [--sheets]
근거: docs/narrative/SCENARIO-ACT3.md §보스, planning/openworld/act3/act3_map.json(싸움터). 틀은 boss_act2.py 와 같다(뼈 9개, 클립 10개, 이름·길이 동일 → 코드 연결 같음).
흑월은 '또 하나의 차사': 주인공과 같은 실루엣(검은 갓·검은 도포·사슬)을 일부러 닮되 키가 크고 야위었다. 눈은 붉게 빛나고, 갓에 초승달 장식, 한 손에 명부(이름이 지워진 장), 다른 손에 끌리는 사슬, 허공에 찢긴 명부 쪽 일곱이 돈다.
눈 쌓인 어깨는 B-12 싸움터(성문 밖 눈밭) 분위기다. 1차(B-04, ① 무덤골)에도 같은 모델을 쓴다: 눈 조각(snow*)은 Prop이 아니라 몸에 붙어 있으니 1차에서 거슬리면 코드가 노드 이름 snow* 만 끄면 된다."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(__file__))
from lib3d import *
from characters import to_group, rig
import anim
import boss_act2 as B2
from boss_act2 import P, bones_for, arm_pair, OUT
BLK, BLK2, BONE, RED = "#1E1E26", "#2E2E3A", "#E8DDA8", "#B02A2A"

SPEC12 = dict(h=2.25, hip=0.95, sh=1.65, neck=1.8, sw=0.4, hand=1.1, hx=0.5, hy=-0.3, prop=1.0)
def b12():
    """흑월 차사 2.25m: 야윈 키 큰 검은 차사. 끌리는 긴 도포 자락, 어깨에 쌓인 눈, 붉은 눈, 갓에 초승달. 오른손 사슬, 왼손 명부."""
    r = random.Random(112); p = P(); s = SPEC12
    p["Hips"] += [lathe("skirt", [(0.05, 0.4), (0.4, 0.36), (0.75, 0.3), (0.95, 0.24)], 10, BLK, fn=lambda i, k, th, z, rr: (rr * (1 + 0.1 * (1 if k % 2 else -1) * (1 - i / 3.0)), z + (0.05 * (k % 3) if i == 0 else 0))),
                  box("shoeL", (0.14, 0.3, 0.1), (0.13, -0.1, 0.05), "hat"), box("shoeR", (0.14, 0.3, 0.1), (-0.13, -0.1, 0.05), "hat")]
    p["Hips"] += [box(f"tatter{i}", (0.1, 0.02, r.uniform(0.3, 0.55)), (-0.35 + i * 0.12, -0.34, 0.3), BLK2, rot=(0.08, 0, r.uniform(-.1, .1))) for i in range(7)]       # 해진 자락
    p["Chest"] += [lathe("torso", [(0.95, 0.26), (1.15, 0.27), (1.4, 0.28), (1.58, 0.22), (1.66, 0.1)], 9, BLK, scale=(1.1, 0.8, 1.0)), box("sash", (0.52, 0.42, 0.09), (0, 0, 1.0), RED), box("collar", (0.24, 0.2, 0.05), (0, -0.06, 1.66), BONE)]
    for sx in (1, -1): p["Chest"].append(sphere(f"snow_sh{sx}", 0.17, (sx * 0.4, 0, 1.68), "#E8EAEE", 6, 4, (1.3, 1, 0.45)))      # 어깨에 쌓인 눈
    for i in range(10):   # 몸에 감긴 사슬: 나선 고리
        a = i / 10 * math.tau * 1.5; z = 1.1 + i * 0.045
        p["Chest"].append(box(f"wrap{i}", (0.1, 0.05, 0.05), (math.cos(a) * 0.29, math.sin(a) * 0.22, z), "iron", rot=(0, 0, a + math.pi / 2)))
    p["Head"] += [sphere("head", 0.14, (0, 0, 1.84), "#C9C2B6", 8, 6, (1, 0.95, 1.12)), cyl("gat_brim", 0.52, 0.52, 0.03, (0, 0, 1.97), "hat", 14), cyl("gat_crown", 0.17, 0.13, 0.32, (0, 0, 1.97), "hat", 9),
                  cyl("moon_disc", 0.07, 0.07, 0.02, (0, -0.14, 2.14), "#E8E6D8", 10, rot=(math.pi / 2, 0, 0)), cyl("moon_cut", 0.06, 0.06, 0.024, (0.03, -0.14, 2.15), "hat", 10, rot=(math.pi / 2, 0, 0)),     # 초승달 장식
                  box("eyeL", (0.05, 0.02, 0.03), (0.06, -0.14, 1.87), mat("#FF4040", 1.4)), box("eyeR", (0.05, 0.02, 0.03), (-0.06, -0.14, 1.87), mat("#FF4040", 1.4)), box("brim_snow", (0.5, 0.2, 0.025), (0, 0.18, 2.0), "#E8EAEE", rot=(0.1, 0, 0)), box("gat_strap", (0.02, 0.02, 0.4), (0.13, -0.08, 1.76), RED)]
    arm_pair(p, s, BLK, "#E8E6D8", 0.085, 0.07, "#C9C2B6")
    # 오른손 사슬: 손목에서 땅으로 늘어진 고리 열여덟(번갈아 돌려 고리 모양), 끝은 바닥에 끌린다
    hx, hy = -s["hx"], s["hy"]
    for i in range(18):
        t = i / 17; z = s["hand"] - 0.05 - t * 1.0; y = hy - 0.05 - 0.35 * math.sin(t * math.pi * 0.9) * 0.6 - t * 0.15
        p["Hand.R"].append(box(f"link{i}", (0.07, 0.025, 0.1), (hx, y, max(z, 0.04)), "iron", rot=(0, (i % 2) * 1.5708, 0)))
    p["Hand.R"].append(sphere("chain_end", 0.09, (hx, hy - 0.5, 0.06), "iron", 5, 4))
    # 왼손 명부: 열린 장. 이름이 있어야 할 자리가 먹으로 지워져 있다
    bx, by, bz = s["hx"] * 0.55, hy - 0.22, s["hand"] + 0.2
    p["Hand.L"] += [box("ledger_cover", (0.5, 0.06, 0.38), (bx, by, bz), "#2A2420", rot=(0.2, 0, 0)), box("ledger_pages", (0.46, 0.05, 0.34), (bx, by - 0.01, bz), BONE, rot=(0.2, 0, 0))]
    p["Hand.L"] += [box(f"blot{i}", (0.3 - 0.03 * i, 0.003, 0.025), (bx, by - 0.045, bz + 0.12 - i * 0.05), "ink", rot=(0.2, 0, 0)) for i in range(5)]
    for i in range(7):    # 찢긴 명부 쪽 일곱: 허공을 천천히 돈다
        a = i / 7 * math.tau; rr = 1.0 + 0.1 * (i % 2)
        p["Prop"].append(box(f"page{i}", (0.22, 0.004, 0.3), (math.cos(a) * rr, math.sin(a) * rr, 0.6 + (i % 4) * 0.35), BONE, rot=(0.3 * math.sin(a * 2), 0.2, a)))
    return p

BOSS3 = [("boss_b12_heugwol", b12, SPEC12)]
B2.SIG["boss_b12_heugwol"] = dict(wind=dict(R=-150, L=-100, lean=-14, tw=-16, nod=-8), atk=dict(R=-25, L=-60, lean=28, tw=16, nod=12), kneel_drop=-0.5)   # 사슬을 높이 들었다 명부와 함께 앞으로 내림

if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    res = [B2.build(*b, sheets="--sheets" in sys.argv) for b in BOSS3 if not only or b[0] in only]
    for r in res: print(r["name"], r["tris"], r["size_m"], r["verify"]["joints"], len(r["verify"]["animations"]))
    json.dump({"fps": anim.FPS, "bosses": res}, open(os.path.join(OUT, "boss", "_act3_anim_manifest.json"), "w"), ensure_ascii=False, indent=1)
    reset()
    for i, (name, fn, spec) in enumerate(BOSS3):
        p = fn(); parts = []
        for bone, objs in p.items(): parts += to_group(objs, bone)
        o = join(name, parts); o.location = ((i - (len(BOSS3) - 1) / 2) * 4.6, 0, 0)
    setup_render(8, (0, 0, 1.2), size=(900, 620), ground_size=30); render(os.path.join(OUT, "previews", "bosses_act3_50deg.png"))
