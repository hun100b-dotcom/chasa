"""솔고개 마을 첫 맵 배치 시안 생성기.
- 입력: assets/sprites/ (타일·소품·캐릭터 PNG) + manifest.json(피벗)
- 출력: assets/maps/solgogae_village_layout.json (코드팀이 그대로 읽어 배치) + solgogae_village_preview.png (눈으로 확인)
좌표: 셀 (gx, gy), 쿼터뷰 2:1. 화면 x = (gx - gy) * 64, y = (gx + gy) * 32. 소품 anchor 는 차지하는 칸 묶음의 정중앙 셀.
왜 규칙으로 만드나: 마을 형태를 바꿔 보고 싶을 때(길 위치, 집 수) 숫자만 고쳐 다시 뽑으면 되게 하려고."""
import json, os
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SP = os.path.join(ROOT, "assets", "sprites")
man = {m["file"]: m for m in json.load(open(os.path.join(SP, "manifest.json")))["sprites"]}
N_X, N_Y = 18, 14

# ---- 바닥 ----
ground = [["grass"] * N_X for _ in range(N_Y)]
def fill(x0, y0, x1, y1, t):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if 0 <= x < N_X and 0 <= y < N_Y:
                ground[y][x] = t
fill(0, 5, N_X - 1, 6, "dirt_road")           # 마을 가로 큰길(서낭당 고개 → 물막이 골)
fill(8, 0, 9, N_Y - 1, "dirt_road")           # 세로 길(마을 위·아래)
fill(0, 0, 3, 3, "stone_path")                # 서낭당 고개: 안전지대 돌바닥
for (x0, y0, x1, y1) in [(3, 7, 6, 9), (10, 2, 13, 4), (11, 8, 14, 10), (4, 1, 7, 3)]:
    fill(x0, y0, x1, y1, "yard")              # 집 앞마당
fill(0, 11, 8, 13, "paddy")                   # 보릿들 논
fill(15, 6, 17, 13, "stepping_stones")        # 물막이 골 쪽 개울
ground[6][15] = ground[6][16] = ground[6][17] = "stepping_stones"   # 길이 개울을 징검다리로 건넌다

# ---- 소품: (이름, 왼쪽 위 칸 x, y, 가로칸, 세로칸) ----
props = [("seonang_tree", 1, 1, 2, 2), ("cairn", 3, 0, 1, 1), ("jangseung", 4, 4, 1, 1), ("jangseung", 7, 4, 1, 1),
         ("choga", 4, 7, 2, 2), ("jars", 3, 7, 1, 1), ("choga", 10, 2, 2, 2), ("giwa", 11, 8, 3, 2), ("well", 8, 7, 1, 1), ("sangyeo", 10, 6, 2, 1),
         ("stone_wall", 5, 4, 2, 1), ("pyeongsang", 12, 3, 2, 1), ("jigae", 13, 5, 1, 1), ("sotdae", 15, 4, 1, 1), ("jars", 14, 8, 1, 1)]
actors = [("characters/chasa_idle", 7.5, 9, "주인공 시작 위치(튜토리얼)"), ("enemies/soul_fresh_kneel", 6, 6, "무릎 꿇은 갓 죽은 혼"),
          ("enemies/soul_fresh", 12, 11, "튜토리얼 첫 이름혼(박돌쇠)"), ("enemies/soul_day", 6, 3, "해 넘긴 혼"),
          ("enemies/soul_old", 13, 12, "오래된 혼(위험 구역)")]

def scr(gx, gy):
    return ((gx - gy) * 64, (gx + gy) * 32)

layout = {"grid": {"w": N_X, "h": N_Y, "tile": "128x64", "ppu": 128},
          "ground": ground,
          "props": [{"sprite": f"props/prop_{n}", "x": x, "y": y, "w": w, "h": h, "anchor": [x + (w - 1) / 2, y + (h - 1) / 2]} for n, x, y, w, h in props],
          "actors": [{"sprite": a, "x": x, "y": y, "note": n} for a, x, y, n in actors],
          "zones": {"hub": [0, 0, 3, 3], "village": [3, 1, 14, 10], "field": [0, 11, 8, 13], "stream": [15, 6, 17, 13]},
          "note": "솔고개 마을 시안 v1. 서낭당 고개(돌바닥) 시작 → 큰길을 따라 마을 → 동쪽 징검다리로 물막이 골. 논은 보릿들."}
os.makedirs(os.path.join(ROOT, "assets", "maps"), exist_ok=True)
json.dump(layout, open(os.path.join(ROOT, "assets", "maps", "solgogae_village_layout.json"), "w"), ensure_ascii=False, indent=1)

# ---- 미리보기 합성 ----
PADX, PADY = 320, 320
Wd = (N_X + N_Y) * 64 + PADX
Hd = (N_X + N_Y) * 32 + PADY + 200
img = Image.new("RGBA", (Wd, Hd), (10, 16, 34, 255))
ox, oy = PADX // 2 + N_Y * 64, 260
def put(path, sx, sy):
    m = man[path + ".png"]
    im = Image.open(os.path.join(SP, path + ".png")).convert("RGBA")
    img.alpha_composite(im, (int(ox + sx - m["pivotX"] * m["w"]), int(oy + sy - m["pivotY"] * m["h"])))
variant = lambda x, y: "ab"[(x * 7 + y * 3) % 2]
for gy in range(N_Y):
    for gx in range(N_X):
        sx, sy = scr(gx, gy)
        put(f"tiles/tile_{ground[gy][gx]}_{variant(gx, gy)}", sx, sy)
objs = [(f"props/prop_{n}", x + (w - 1) / 2, y + (h - 1) / 2, 0) for n, x, y, w, h in props] + [(a, x, y, 1) for a, x, y, _ in actors]
for path, gx, gy, _ in sorted(objs, key=lambda o: o[1] + o[2]):
    sx, sy = scr(gx, gy)
    put(path, sx, sy)
# 밤 분위기: 남청 비네트 + 약한 어두움
shade = Image.new("RGBA", img.size, (10, 16, 40, 70))
img = Image.alpha_composite(img, shade)
img = img.convert("RGB")
img.thumbnail((2600, 2600))
img.save(os.path.join(ROOT, "assets", "maps", "solgogae_village_preview.png"))
print("map ok", img.size)
