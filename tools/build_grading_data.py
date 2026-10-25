#!/usr/bin/env python3
"""
build_grading_data.py — 아트팀 화면 분위기 값(assets3d/grading)을 유니티가 읽는 형태로 넣는다.
  · LUT 22장·천도 시야 그림 2장 → Resources/Grading/<이름>.bytes (PNG 이름만 .bytes 로: 가져오기 설정(sRGB·압축) 걱정 없이 코드가 선형으로 읽는다)
  · 값 표(시간대 경계·날씨 교차·키별 블룸·비네트·천도) → Resources/Data/grading.json (짧게 줄임)
사용: python3 tools/build_grading_data.py <assets3d 폴더>
"""
import json, os, shutil, sys

art = os.path.join(sys.argv[1], "grading")
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = os.path.join(root, "unity", "Assets", "Resources")
p = json.load(open(os.path.join(art, "grading_params.json"), encoding="utf-8"))
dst = os.path.join(res, "Grading"); os.makedirs(dst, exist_ok=True)
for f in sorted(os.listdir(art)):
    if f.endswith(".png"):
        shutil.copyfile(os.path.join(art, f), os.path.join(dst, f[:-4] + ".bytes"))
keys = []
for k, v in p["presets"].items():
    keys.append({"k": k, "bi": v["bloom"]["threshold"], "bt": v["bloom"]["intensity"], "bs": v["bloom"]["scatter"], "bc": v["bloom"]["tint"],
                 "vi": v["vignette"]["intensity"], "vs": v["vignette"]["smoothness"], "vc": v["vignette"]["color"]})
for k in keys:  # 이름 정리: threshold 는 bi 가 아니라 bth
    k["bth"] = k.pop("bi")
hm = p["hour_map"]
out = {"dawn": hm["dawn"], "day": hm["day"], "dusk": hm["dusk"], "night": hm["night"], "cross": hm["crossfade_hours"],
       "weatherBlend": p["weather_blend_s"], "vignetteMax": p["vignette_max_except_tendo"], "keys": keys, "tendo": p.get("tendo", {})}
json.dump(out, open(os.path.join(res, "Data", "grading.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("LUT·그림", len([f for f in os.listdir(dst) if f.endswith(".bytes")]), "키", len(keys))
