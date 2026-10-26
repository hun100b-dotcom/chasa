"""1막 폐당집 서낭당(⑤) 둘레 꾸미기 배치표. 실행: python3 place_act1_pyedang.py → assets3d/layouts/act1_pyedang.json
왜: 서낭당 건물(prop_seonangdang_pyedang, (574,552), 터 높이 z=2.0)은 코드가 field.json에 세우지만 둘레는 무덤 몇 기·고사목뿐이라 '쉼터'로 읽히지 않았다.
 다른 서낭당(마을 등)처럼 길손이 쌓은 돌탑·장승·금줄·넋불 등을 두르되, 폐당집답게 낡고 쓸쓸하게(상사화·이끼, 불은 약하게) 한다.
 터는 평평(z=2.0). 이미 있는 무덤·고사목과 1.6 m 이상 떨어뜨리고, 입구 마커(580,552)에서 보스 마당(580,521) 쪽 길(x 574~586)은 비워 둔다.
작성: 아트. 직접 고치지 말고 스크립트를 고친다."""
import os, json, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, "..", "..", "assets3d")
R = random.Random(5521); CX, CY, Z = 574.0, 552.0, 2.0
FIXED = [(566.7, 553.8), (575.3, 558.8), (580.1, 554.5), (570.2, 544.4), (571.9, 550.3), (572.3, 555.0), (CX, CY)]   # 이미 놓인 것(field.json 점검 결과)
F = {"prop_jangseung": "props", "prop_geumjul": "props", "prop_cairn": "props", "prop_soulfire_lantern": "props", "a1r_wayside_rest": "props", "cover_lily_red": "nature", "cover_moss_patch": "nature", "cover_wayside_cairn": "nature", "cover_stones_a": "nature", "nature_dead_a": "nature"}
placed = []
def ok(x, y, gap):
    if abs(x - 580) < 6 and y < 551: return False              # 입구에서 보스 마당으로 내려가는 길
    return all(math.hypot(x - a, y - b) >= gap for a, b in FIXED + [(p["x"], p["y"]) for p in placed])
def put(m, x, y, rot, note, gap=1.6, force=False):
    if force or ok(x, y, gap): placed.append({"prop": m, "file": f"assets3d/{F[m]}/{m}.glb", "x": round(x, 2), "y": round(y, 2), "rot": rot, "z": Z, "note": note}); return True
    return False
# 서낭당 앞마당 좌우 장승 한 쌍 + 금줄(문턱 표시)
put("prop_jangseung", CX - 3.2, CY - 3.0, 10, "폐당집 서낭당 앞 장승(왼)", force=True); put("prop_jangseung", CX + 3.2, CY - 3.0, -10, "폐당집 서낭당 앞 장승(오른)", force=True)
put("prop_geumjul", CX, CY - 3.0, 0, "폐당집 서낭당 금줄(낡음)", force=True)
# 넋불 둘: 서낭당 양옆 모서리(보랏빛 혼불이 이미 있어 두 개만, 약하게)
put("prop_soulfire_lantern", CX - 2.6, CY + 0.8, 0, "폐당집 서낭당 넋불(왼)"); put("prop_soulfire_lantern", CX + 2.6, CY + 0.8, 0, "폐당집 서낭당 넋불(오른)")
# 쉼터 표시(길손 쉼 자리, 서낭당 동쪽 입구 쪽)
put("a1r_wayside_rest", CX + 4.5, CY - 1.8, 0, "폐당집 서낭당 쉼 자리")
# 길손 돌탑 3, 큰 돌탑 2
for i, (dx, dy) in enumerate(((-4.2, 1.5), (-2.2, 4.5), (3.8, 3.2))): put("prop_cairn", CX + dx, CY + dy, R.uniform(0, 360), "폐당집 길손 돌탑" if i == 0 else "")
for dx, dy in ((-5.5, -1.0), (5.5, 1.6)): put("cover_wayside_cairn", CX + dx, CY + dy, R.uniform(0, 360), "")
# 상사화·이끼·돌: 무덤 곁과 둘레에 얇게
for n, c, rmin, rmax in (("cover_lily_red", 14, 2.5, 9.0), ("cover_moss_patch", 9, 2.0, 8.0), ("cover_stones_a", 8, 3.0, 9.0), ("nature_dead_a", 3, 5.0, 9.5)):
    got = 0
    for _ in range(c * 25):
        if got >= c: break
        a, r_ = R.uniform(0, 2 * math.pi), R.uniform(rmin, rmax)
        if put(n, CX + math.cos(a) * r_, CY + math.sin(a) * r_, R.uniform(0, 360), "", 1.6 if n.startswith("nature") else 1.2): got += 1
json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "place_act1_pyedang.py가 만든다. 직접 고치지 말고 스크립트를 고친다. 폐당집 터 z=2.0", "props": placed}, open(os.path.join(A, "layouts", "act1_pyedang.json"), "w"), ensure_ascii=False, indent=1)
print(len(placed), "개 → assets3d/layouts/act1_pyedang.json")
