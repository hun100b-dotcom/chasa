"""장비창 시안(한지·먹·인 재료 버전). 파란 상자 시안을 대체한다.
이유: 기획팀 UI 재질 언어(한지 창/먹 테두리/붉은 인/등급 테두리)를 실제 키트 PNG로 조립해,
키트가 9조각 늘림(border-image)으로 제대로 늘어나는지도 함께 검증한다.
HTML 한 장을 만들고 Playwright로 PC(1280×720)/폰(390×844) 캡처한다."""
import os, sys, subprocess, textwrap
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SP = os.path.join(ROOT, "assets", "sprites")
OUT = os.path.join(ROOT, "assets", "ui")
SLOTS = [("무기", "weapon", 3), ("갓", "gat", 2), ("도포", "dopo", 4), ("띠", "tti", 1), ("신", "shoe", 2), ("노리개", "noriga", 3), ("노리개", "noriga", 5)]
def icon(cat, g):
    # 등급 번호 → 아이콘 파일 접미사 (없으면 빈 칸)
    m = {1: "common", 2: "crafted", 3: "rare", 4: "named"}
    p = f"icons/icon_{cat}_{m.get(g,'')}.png"
    return f'<img class="ic" src="file://{SP}/{p}" onerror="this.style.display=\'none\'">' if os.path.exists(os.path.join(SP, p)) else ""
def page(mob):
    W, H = (390, 844) if mob else (1280, 720)
    ss = 52 if mob else 76
    slots = "".join(f'<div class="slot" style="background-image:url(file://{SP}/ui/ui_grade_{g}.png)">{icon(c,g)}<span class="nm">{n}</span>{"<img class=seal src=file://"+SP+"/ui/ui_seal_select.png>" if i==0 else ""}{"<img class=seal src=file://"+SP+"/ui/ui_seal_new.png>" if i==3 else ""}</div>' for i, (n, c, g) in enumerate(SLOTS))
    bag = "".join(f'<div class="slot s2" style="background-image:url(file://{SP}/ui/ui_grade_{[1,2,3,1,0,4,0,2][i%8]}.png)">{"<img class=strike src=file://"+SP+"/ui/ui_strike_pahon.png>" if i==5 else ""}</div>' if i%8 not in (4,6) else '<div class="slot s2 empty"></div>' for i in range(18 if mob else 24))
    return f"""<!doctype html><meta charset=utf-8><style>
*{{box-sizing:border-box;margin:0}}body{{width:{W}px;height:{H}px;background:radial-gradient(circle at 50% 20%,#1D2C52,#0F1729);font-family:'Noto Serif KR','Noto Sans KR',serif;color:#2A2A38;overflow:hidden}}
.win{{position:absolute;inset:{4 if mob else 24}px;border:48px solid transparent;border-image:url(file://{SP}/ui/ui_hanji_panel.png) 48 fill/{18 if mob else 30}px stretch;padding:{4 if mob else 14}px}}
h1{{font-size:{20 if mob else 26}px;letter-spacing:2px}} .sub{{font-size:12px;color:#7a5a2a}}
.grid{{display:flex;gap:{8 if mob else 24}px;margin-top:10px;{'flex-direction:column;gap:22px' if mob else ''}}}
.equip{{display:grid;grid-template-columns:repeat({4 if mob else 4},{ss}px);gap:{8 if mob else 14}px;align-content:start}}
.slot{{width:{ss}px;height:{ss}px;background-size:100% 100%;position:relative;display:flex;align-items:center;justify-content:center}}
.slot.s2{{width:{44 if mob else 62}px;height:{44 if mob else 62}px}} .slot.empty{{opacity:.35;background:none;border:1px dashed #2A2A38}}
.ic{{width:70%;height:70%;object-fit:contain}} .nm{{position:absolute;bottom:-15px;font-size:11px;width:100%;text-align:center}}
.seal{{position:absolute;top:-6px;right:-6px;width:20px}} .strike{{position:absolute;left:0;top:45%;width:100%}}
.bag{{display:grid;grid-template-columns:repeat({6 if mob else 6},auto);gap:6px;margin-top:6px;justify-content:start}}
.info{{border:28px solid transparent;border-image:url(file://{SP}/ui/ui_ink_border_double.png) 28 fill/10px stretch;padding:4px 8px;margin-top:10px;font-size:{12 if mob else 15}px;line-height:1.5}}
.btn{{position:absolute;{'left:24px;right:24px;bottom:22px;height:52px' if mob else 'right:60px;bottom:50px;width:220px;height:52px'};border:28px solid transparent;border-image:url(file://{SP}/ui/ui_ink_border_thin.png) 28 fill/14px stretch;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:17px;color:#E85C41;background:transparent}}
.plate{{{'display:none!important;' if mob else ''}position:absolute;{'right:20px;top:20px;width:30px' if mob else 'right:60px;top:60px;width:56px'};height:{110 if mob else 200}px;background:url(file://{SP}/ui/ui_nameplate_v.png) 0 0/100% 100%;writing-mode:vertical-rl;color:#F3E7D3;font-size:{13 if mob else 18}px;display:flex;align-items:center;justify-content:center;padding-top:6px}}
</style><div class=win><h1>장비</h1><div class=sub>무기(두 벌) · 갓 · 도포 · 띠 · 신 · 노리개 2 — 붉은 인: 고른 것 / 새것</div>
<div class=grid><div class=equip>{slots}</div><div><b>가방 18/30</b><div class=bag>{bag}</div>
<div class=info><b style="color:#E85C41">월화의 방울</b> (이름 있는)<br>파혼 반경 +1m · 천도 캐스팅 +0.2초<br><i style="color:#7a5a2a">'열두째 잔이 엎어진 뒤로, 이 방울은 소리를 내지 않는다.'</i></div></div></div>
<div class=plate>월화의 방울</div><div class=btn>착용하기</div></div>"""
if __name__ == "__main__":
    tmp = os.path.join(OUT, "_equip_tmp"); os.makedirs(tmp, exist_ok=True)
    js = ["const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"]
    for mob in (False, True):
        n = "phone" if mob else "pc"; f = os.path.join(tmp, n + ".html"); open(f, "w", encoding="utf-8").write(page(mob))
        w, h = (390, 844) if mob else (1280, 720)
        js.append(f"{{const p=await b.newPage({{viewport:{{width:{w},height:{h}}}}});await p.goto('file://{f}');await p.waitForTimeout(500);await p.screenshot({{path:'{OUT}/growth_equip_hanji_{n}.png'}});}}")
    js.append("await b.close()})()")
    open(os.path.join(tmp, "r.cjs"), "w").write("\n".join(js))
    subprocess.run(["node", os.path.join(tmp, "r.cjs")], env={**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()}, check=True)
