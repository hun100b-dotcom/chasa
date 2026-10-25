"""1막·2막 마을 사람 자리 38곳을 필드 좌표로 확정한다 → assets3d/layouts/npc_places_act1.json (+ 지도 그림).
왜: 서사팀 npc_act1.json의 places는 '구역 중심 기준 미터'(동쪽 +x, 북쪽 +y) 제안값이다. 실제 필드(640m)의 길·집·우물과 맞추려면 구역마다 닻 좌표(anchor)를 정하고,
집·길과 겹치지 않게 옮겨야 한다. 모든 좌표는 필드 절대 m(x=동, y=북). 유니티는 (x, 높이, y)."""
import os, json, math
A3 = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
L = json.load(open(os.path.join(A3, "layouts", "field_5x5.json")))
NP = json.load(open("/tmp/claude-0/n/npc_act1.json"))["places"]
V0 = (196, 60); WELL = (V0[0] + 4.2, V0[1] - 5.5)    # 마을 원점과 우물
ANCHOR = {"Hub": (188, 36), "Village": WELL, "Field": (290, 116), "Ravine": (404, 296), "Shrine": (580, 535), "Market": (36, 388), "Yamen": (36, 330), "Plague": (34, 469)}
# 이름 → (x, y, 바라보는 곳(x,y), 메모). 지정 안 한 곳은 제안 오프셋을 닻에 더한 값을 그대로 쓴다.
OV = {
 "서낭당 돌무더기 곁": (191.0, 33.4, (188, 36), "서낭나무 남동쪽 돌무더기, 장승 안쪽"),
 "서낭당 고개 고갯마루": (196, 25.5, (196, 36), "서사 제안은 '장승 밖 북쪽'인데 필드에서 장승 밖은 남쪽(시작점 쪽)이라 남쪽 입구 밖으로 옮김. 검은여울 가는 길은 마을 북쪽 갈림에서 서쪽으로 나간다"),
 "우물가": (198.6, 53.2, WELL, "우물 남서쪽 1.8m. 우물 자체(4.2,-5.5)가 마을 중심"),
 "윤 소사네 제사상": (191.2, 58.0, (187.5, 57), "서쪽 긴 초가(house_01, 187.5,57) 동쪽 마당"),
 "윤 소사네 마당 제사상": (191.2, 58.0, (187.5, 57), "서쪽 긴 초가 동쪽 마당"),
 "윤 소사네 마당": (191.4, 59.4, (187.5, 57), "제사상 곁"),
 "마을 어귀 정자": (190.8, 43.6, (188, 36), "마을에 정자가 없어 새 소품 필요. 제안(6,-6)은 동쪽 초가와 겹쳐 서낭당 쪽 어귀로 옮김"),
 "정자": (190.8, 43.6, (188, 36), "위와 같은 자리"),
 "박돌쇠네 대장간": (219.0, 62.0, (212, 62), "제안(10,6)은 동쪽 초가와 겹침. 동쪽 돌담 밖 외딴 터로. 대장간 건물 필요(초가+모루+풀무)"),
 "대장간": (219.0, 62.0, (212, 62), "위와 같은 자리"),
 "당할미 집": (190.8, 47.0, (188, 36), "남서쪽 끝 초가(house_00, 187.5,47) 문 앞. 서낭당 쪽"),
 "도씨네 집": (190.8, 67.0, (187.5, 67), "서쪽 초가(house_02, 187.5,67) 문 앞. 강 쪽 끝 집"),
 "보릿들 둑": (290, 113.2, (290, 120), "보릿들 남쪽 큰 길(y 116) 북쪽 풀둑"),
 "물막이 골 나루 계단": (399.0, 291.5, (404, 288), "보스1 자리(404,288) 서쪽 옛 나루 계단"),
 "물막이 골 줄배": (397.0, 286.0, (410.5, 288), "나룻배(410.5,288) 서쪽 줄 매는 말뚝 곁"),
 "물막이 골 주막 터": (417.4, 321.0, (404, 296), "주막 앞마당(주막 건물 (419.8,330), 문 남쪽). 개울 동쪽 둑 위"),
 "물막이 골 갈대 속 부러진 삿대": (393.0, 289.0, (404, 288), "나루 서쪽 갈대밭"),
 "객사 앞 방": (31.0, 326.0, (36, 330), "탄 동헌 서쪽 객사 터. 소나무 곁이라 피해 옮김"),
 "역병막 어귀": (42.0, 452.0, (34, 469), "격리 움막 줄 동쪽 길목(약탕 화로 곁). 제안(0,-8)은 움막과 겹쳐 옮김"),
 "폐당집 굿상": (580, 531.5, (580, 535), "당집(580,535) 앞마루 남쪽. 폐당집 입구가 남쪽"),
}
# 첫 세션 이름혼 6명(first_session.json): 명부 몫 또는 명부 밖으로 나오는 이름 있는 혼의 자리
SOULS = {
 "S-001 박돌쇠": (215.6, 62.2, (219, 62), "fresh", "갈림 셋: 빗장 지른 대장간 문 앞. 대장간(219,62)이 서쪽 문이라 문 앞은 x 약 216"),
 "S-002 윤 소사": (190.4, 60.8, (187.5, 57), "fresh", "마을 안(명부 밖). 윤 소사네 마당 제사상(191.2,58) 곁. 방금 천도했다면 제사상 앞에 잠깐 서 있다 흩어짐"),
 "S-003 연이": (202.0, 56.6, (200.2, 54.5), "fresh", "마을 안(명부 밖). 우물(200.2,54.5) 동쪽 길, 동쪽 초가 문 앞"),
 "S-006 장 둑지기": (302.0, 112.6, (290, 116), "year", "보릿들 둑 갈림 둘 자리(290,113)에서 동쪽 12m, 길 북쪽 풀둑. 해 넘긴 혼"),
 "S-010 곽 뱃꾼": (381.5, 293.5, (404, 288), "year", "물막이 골: 큰 길에서 나루로 가는 중간(나루까지 약 23m). 해 넘긴 혼, 명부 몫"),
 "S-011 방물장수 막례": (397.8, 304.0, (404, 296), "year", "보스 진입 직전 나루 북서쪽 풀밭(명부 밖, 인 없음)"),
}
def souls(pts):
    out = {}
    for name, (x, y, face, age, memo) in SOULS.items():
        near = min((math.hypot(x - px, y - py), k) for px, py, k in pts)
        out[name] = {"x": x, "y": y, "face_deg": round(math.degrees(math.atan2(face[1] - y, face[0] - x)) % 360), "age": age, "memo": memo, "nearest_prop": {"name": near[1], "dist_m": round(near[0], 1)}}
    return out

def build():
    out = {}; props = L["props"]; st = L["structures"]
    pts = [(p["x"], p["y"], p["prop"]) for p in props] + [(s["x"], s["y"], s.get("piece") or s.get("id")) for s in st]
    for name, v in NP.items():
        z = v["zone"]; ax, ay = ANCHOR[z]
        if name in OV: x, y, face, memo = OV[name]; moved = True
        else: x, y = ax + v["offset_m"][0], ay + v["offset_m"][1]; face = (ax, ay); memo = ""; moved = False
        near = sorted((math.hypot(x - px, y - py), k) for px, py, k in pts)[:1]
        d = {"zone": z, "x": round(x, 1), "y": round(y, 1), "face_deg": round(math.degrees(math.atan2(face[1] - y, face[0] - x)) % 360), "from_narrative_offset_m": v["offset_m"], "moved_from_proposal": moved, "memo": memo or v.get("hint", ""),
             "nearest_prop": {"name": near[0][1], "dist_m": round(near[0][0], 1)}}
        out[name] = d
    return out
if __name__ == "__main__":
    o = build()
    json.dump({"units": "m", "axes": "x=동, y=북(필드 절대). 유니티는 (x, 높이, y)", "face_deg": "0=동쪽, 90=북쪽(반시계). 그 자리 NPC가 바라볼 방향", "anchors": {k: list(v) for k, v in ANCHOR.items()},
               "note": "서사 제안(구역 중심 기준)을 필드 지도에 맞춰 확정한 값. needs_new는 아직 모델이 없는 건물·소품. 시장·동헌 터에는 이후 건물을 지었다(역병막은 터 좌표만)(필드 서쪽 둑, x 0~72).",
               "needs_new": [], "built_buildings": "정자·대장간·물막이 골 주막·장터 약방·장터 주막·동헌 터·옥·객사 7곳은 지음(README 참고)", "named_souls_first_session": souls([(p["x"], p["y"], p["prop"]) for p in L["props"]] + [(q["x"], q["y"], q.get("piece") or q.get("id")) for q in L["structures"]]), "places": o}, open(os.path.join(A3, "layouts", "npc_places_act1.json"), "w"), ensure_ascii=False, indent=1)
    for k, v in json.load(open(os.path.join(A3, "layouts", "npc_places_act1.json")))["named_souls_first_session"].items(): print("혼", k, v["x"], v["y"], v["nearest_prop"])
    for k, v in o.items(): print(f"{k:16s} {v['zone']:8s} ({v['x']:6},{v['y']:6}) 가까운 {v['nearest_prop']['name']} {v['nearest_prop']['dist_m']}m {'*' if v['moved_from_proposal'] else ''}")
