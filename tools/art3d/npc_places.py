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
 "물막이 골 주막 터": (414.0, 322.0, (404, 296), "골 위쪽(북쪽) 방앗간(399,340) 남동쪽 빈 터. 주막 건물 없음(터만)"),
 "물막이 골 갈대 속 부러진 삿대": (393.0, 289.0, (404, 288), "나루 서쪽 갈대밭"),
 "객사 앞 방": (31.0, 326.0, (36, 330), "탄 동헌 서쪽 객사 터. 소나무 곁이라 피해 옮김"),
 "역병막 어귀": (42.0, 452.0, (34, 469), "격리 움막 줄 동쪽 길목(약탕 화로 곁). 제안(0,-8)은 움막과 겹쳐 옮김"),
 "폐당집 굿상": (580, 531.5, (580, 535), "당집(580,535) 앞마루 남쪽. 폐당집 입구가 남쪽"),
}
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
               "note": "서사 제안(구역 중심 기준)을 필드 지도에 맞춰 확정한 값. needs_new는 아직 모델이 없는 건물·소품. 시장·동헌·역병막은 2막 구역이라 건물이 없고 터 좌표만 잡았다(필드 서쪽 둑, x 0~72).",
               "needs_new": ["정자(마을 어귀)", "대장간 건물(초가+모루+풀무)", "주막 건물(터만 있음)", "장터 약방·주막·엿판 자리 건물/좌판", "동헌 터(탄 서안·숯 기둥)·옥 돌담·옥문·객사"], "places": o}, open(os.path.join(A3, "layouts", "npc_places_act1.json"), "w"), ensure_ascii=False, indent=1)
    for k, v in o.items(): print(f"{k:16s} {v['zone']:8s} ({v['x']:6},{v['y']:6}) 가까운 {v['nearest_prop']['name']} {v['nearest_prop']['dist_m']}m {'*' if v['moved_from_proposal'] else ''}")
