#!/usr/bin/env python3
"""작업 지도 '개발 현황' 탭용 게시 폴더를 만든다.

왜: 지도(Artifact)는 외부 이미지를 못 불러오므로 그림을 페이지 파일로 같이 올려야 한다.
사용: python3 tools/build_dashboard_status.py [출력폴더(기본 /tmp/dash-out)]
 1) docs/status.json 을 읽는다(요약·병합 PR·화면 칸 목록).
 2) 칸 id 와 같은 이름의 docs/screenshots/<id>.jpg|png 가 있으면 '실제 화면'으로 채운다.
    없으면 칸의 fallback(저장소 렌더 그림)을 '렌더 미리보기'로, 그것도 없으면 '촬영 대기'.
 3) 그림은 가로 960 이하 JPEG 로 줄여 shots/ 에 넣고, 합친 status.json 을 쓴다.
 그다음 출력폴더의 파일을 지도 Artifact 에 publish_files 로 올린다(그림 바이트가 채팅을 거치지 않는다).
"""
import json, os, sys
from PIL import Image

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/dash-out"
os.makedirs(out + "/shots", exist_ok=True)
st = json.load(open(root + "/docs/status.json", encoding="utf8"))
st.pop("_설명", None)
# PC 가 올린 manifest(찍은 시각·커밋 등)가 있으면 칸 정보에 덧붙인다
mf = {}
mp = root + "/docs/screenshots/manifest.json"
if os.path.exists(mp):
    for s in json.load(open(mp, encoding="utf8")).get("shots", []):
        mf[os.path.splitext(s["file"])[0]] = s

def shrink(src, dst):
    im = Image.open(src).convert("RGB")
    if im.width > 960:
        im = im.resize((960, round(im.height * 960 / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=80, optimize=True)

def find_real(i):
    for ext in ("jpg", "jpeg", "png"):
        p = f"{root}/docs/screenshots/{i}.{ext}"
        if os.path.exists(p):
            return p

for s in st["slots"]:
    real = find_real(s["id"])
    fb = s.pop("fallback", None)
    if real:
        s["kind"] = "screen"; src = real
        m = mf.get(s["id"], {})
        for k in ("commit", "takenAt", "caption"):
            if m.get(k): s[k] = m[k]
    elif fb and os.path.exists(root + "/" + fb):
        s["kind"] = "render"; src = root + "/" + fb
    else:
        s["kind"] = "pending"; src = None
    if src:
        s["file"] = f"shots/{s['id']}.jpg"
        shrink(src, f"{out}/{s['file']}")
json.dump(st, open(out + "/status.json", "w", encoding="utf8"), ensure_ascii=False)
print("출력:", out, "| 실제", sum(s["kind"] == "screen" for s in st["slots"]),
      "렌더", sum(s["kind"] == "render" for s in st["slots"]),
      "대기", sum(s["kind"] == "pending" for s in st["slots"]))
