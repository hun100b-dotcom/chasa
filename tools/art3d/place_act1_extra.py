"""1막 추가 소품 배치(기획 요청 2026-10-25): 칠복네 빈 개집(190.5,75.0), 마른 벼루(202.5,70.5), 장터 북틀(38,390).
왜 따로 파일인가: field_5x5.json·solgogae_village.json은 생성기(field_layout.py·solgogae.py)가 다시 쓰므로, 손으로 더한 배치가 사라지지 않게 별도 파일 `layouts/act1_extra.json`에 둔다.
build_field_data.py와 walkcheck.py가 이 파일을 함께 읽는다. 기획이 준 자리가 막혔으면(담·집·나무 가까이) 열린 땅(여유폭 1.2m 이상)으로 6m 안에서 옮기고 walk_snap에 원래 좌표를 남긴다.
실행: python3 tools/art3d/place_act1_extra.py"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import walkcheck as W
from walk_fix import snap
WANT = [("prop_gaejip_empty", 190.5, 75.0, 270, "칠복네 기와집(house_06) 마당 서쪽 담 모퉁이 빈 개집 — 입구 동쪽, 밥그릇 (191.6,75.0). 기획 확정 2026-10-25 (J-004 제사 자리 (191.5,76.5) 옆)"),
        ("prop_dry_inkstone", 202.5, 70.5, 0, "마른 벼루(서당) — 유품 K-005 자리"),
        ("prop_market_drum_frame", 38.0, 390.0, 180, "장터 북틀(덕수) — 장례 대본 소품")]
def main():
    bl = W.load()
    G = W.Grid(bl, 0, 0, 260, 420, 0.5)   # 마을(200,60)과 장터(38,390)를 모두 덮는 격자(0.5m)
    props = []
    for name, x, y, rot, note in WANT:
        nx, ny = snap(G, x, y, want=1.2, rad=6.0)
        p = {"prop": name, "file": f"assets3d/props/{name}.glb", "x": round(nx, 2), "y": round(ny, 2), "rot": rot, "z": 0.0, "note": note}
        if (nx, ny) != (x, y): p["walk_snap"] = {"from": [x, y], "to": [round(nx, 2), round(ny, 2)]}
        props.append(p); print(name, (x, y), "→", (round(nx, 2), round(ny, 2)))
    json.dump({"units": "m", "axes": "x=동, y=북(필드 절대)", "note": "place_act1_extra.py가 만든다. 직접 고치지 말고 스크립트의 WANT를 고친다", "props": props}, open(os.path.join(W.LAY, "act1_extra.json"), "w"), ensure_ascii=False, indent=1)
if __name__ == "__main__": main()
