"""필드 전체(640m)의 불빛 위치 목록을 뽑는다 → assets3d/layouts/field_5x5_lights.json
왜: 코드팀이 유니티에서 점광원을 한 번에 깔 수 있게. 블렌더 조립기(field_scene.py)가 실제로 놓은 등롱·횃대·혼불·나루터 불을 그대로 쓴다."""
import sys, os, json
sys.argv = ["x"]
import field_scene as F
F.reset(); F.lib.t.clear(); F.lib.lights.clear(); F.placed_lights.clear()
F.build((0, 0, 640, 640))
out = os.path.join(F.A3, "layouts", "field_5x5_lights.json")
json.dump({"units": "m", "axes": "x=동, y=북, z=위(블렌더 좌표. 유니티는 (x, z, y))", "note": "field_scene.py가 조립하며 놓은 점광원. intensity 1.0 = 블렌더 900W 기준 보통 밝기", "lights": F.placed_lights}, open(out, "w"), ensure_ascii=False, indent=1)
print(len(F.placed_lights), "개 →", out)
