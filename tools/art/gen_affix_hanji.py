"""옵션·기울기 화면 한지판(PC·폰). 기획 정본 data/growth.json의 affixes·tilts·rarities를 읽어 그대로 그린다(값은 임시값).
구성: 장비 상세 카드(등급 테두리·옵션 줄과 굴림 위치 막대·기울기 +/−·홈·기억 한 줄) + 기울기 도감(6종, 천도/파혼 기울기 표시).
이유: '귀한' 장비만 기울기가 붙는 규칙과 +·−가 한눈에 읽히는지, 폰에서도 눌러 볼 수 있는지 확인하는 시안."""
import os, json, sys, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from gen_growth_hanji import ROOT, SP, OUT, D, css
EX = lambda mob: f"""
.card{{border:3px solid #D4A94E;border-radius:12px;background:#fbf3df;padding:{8 if mob else 12}px {10 if mob else 14}px;box-shadow:0 0 0 3px #fbf3df,0 0 0 5px #D4A94E55}}
.hd{{display:flex;align-items:center;gap:10px}} .ic{{width:{50 if mob else 62}px;height:{50 if mob else 62}px;border:3px solid #D4A94E;border-radius:10px;background:#0F1729;display:flex;align-items:center;justify-content:center}}
.ic i{{width:0;height:0;border-left:11px solid transparent;border-right:11px solid transparent;border-bottom:26px solid #D4A94E}}
.nm{{font-size:{19 if mob else 22}px;font-weight:bold}} .rar{{font-size:12px;color:#a9811f;font-weight:bold}}
.op{{margin-top:6px;border-bottom:1px dotted #b9a784;padding:3px 0}} .op .t{{display:flex;justify-content:space-between;font-size:{13 if mob else 14.5}px}} .op b{{font-variant-numeric:tabular-nums}}
.rg{{position:relative;height:7px;border:1.5px solid #2A2A38;border-radius:4px;background:#e6d8b8;margin-top:3px}} .rg i{{position:absolute;top:-4px;width:4px;height:13px;background:#E85C41;border-radius:2px}}
.rgt{{font-size:10.5px;color:#7a5a2a;display:flex;justify-content:space-between}}
.tl{{margin-top:8px;border:2px solid #2A2A38;border-radius:8px;padding:6px 8px;background:#f1e6cb}} .tl .n{{font-weight:bold;font-size:14px}}
.pl{{color:#1f7a72;font-size:13px;font-weight:bold}} .mi{{color:#c0422b;font-size:13px;font-weight:bold}}
.chip{{display:inline-block;font-size:11px;padding:0 6px;border-radius:9px;color:#fff;margin-left:6px;vertical-align:middle}}
.sock{{display:flex;gap:6px;margin-top:8px;align-items:center;font-size:12px}} .sock b{{width:26px;height:26px;border-radius:50%;border:2.5px dashed #2A2A38;display:block}}
.mem{{margin-top:8px;font-size:{12 if mob else 13}px;color:#4a3a22;font-style:italic;line-height:1.45}}
.row{{display:flex;gap:16px;{'flex-direction:column;gap:8px' if mob else ''}}} .row>div{{flex:1}}
h2{{font-size:15px;margin:2px 0 5px;border-bottom:3px solid #E85C41}}
.tb{{border-bottom:1px dotted #b9a784;padding:{3 if mob else 5}px 0;font-size:{12 if mob else 13.5}px;line-height:1.35}}
.btn{{position:absolute;left:14px;right:14px;bottom:{14 if mob else 22}px;height:{52 if mob else 54}px;border:3px solid #D4A94E;background:#2A2A38;color:#D4A94E;border-radius:12px;text-align:center;line-height:46px;font-size:18px;font-weight:bold}}
"""
def page(mob):
    R = {r["id"]: r for r in D["rarities"]}; AF = {a["id"]: a for a in D["affixes"]}; rare = R["rare"]
    picks = [("tendo_cast", 0.62), ("skill_cd", 0.30), ("life", 0.85)]   # 귀한 갓에 붙을 수 있는 옵션 3개(굴림 위치는 시안용)
    ops = ""
    for k, pos in picks:
        a = AF[k]; lo, hi = a["ranges"]["rare"]; v = lo + (hi - lo) * pos; sign = "−" if "−" in a["name"] else "+"
        base = a["name"].replace(" +%", "").replace(" −%", "").replace(" +", "").replace(" −", "")
        unit = "%" if "%" in a["name"] else ""
        ops += f'<div class=op><div class=t><span>{base}</span><b>{sign}{v:.0f}{unit}</b></div><div class=rg><i style="left:{pos*100:.0f}%"></i></div><div class=rgt><span>{lo}{unit}</span><span>한도 {a["cap"]}</span><span>{hi}{unit}</span></div></div>'
    T = D["tilts"]; LEAN = {"천도": D["schools"]["burum"]["color"], "파혼": D["schools"]["eolruk"]["color"]}
    t0 = [t for t in T if t["id"] == "tilt_radius_wait"][0]
    tilt = f'<div class=tl><div class=n>기울기 · {t0["name"]}<span class=chip style="background:{LEAN[t0["lean"]]}">{t0["lean"]}</span></div><div class=pl>＋ {t0["plus"]}</div><div class=mi>－ {t0["minus"]}</div></div>'
    card = (f'<div class=card><div class=hd><div class=ic><i></i></div><div><div class=nm>검은 갓</div><div class=rar>{rare["name"]} · 갓 · 옵션 {rare["affixes"]}줄 + 기울기</div></div></div>{ops}{tilt}'
            f'<div class=sock>홈<b></b><b></b><span style="color:#7a5a2a">서낭당에서 인을 끼운다</span></div><div class=mem>갓끈 끝에 매단 검은 술이 흔들릴 때마다 누군가 이름을 부르다 만 소리가 났다.</div></div>')
    tlist = "".join(f'<div class=tb><b>{t["name"]}</b><span class=chip style="background:{LEAN[t["lean"]]}">{t["lean"]}</span><br><span class=pl>＋ {t["plus"]}</span><br><span class=mi>－ {t["minus"]}</span></div>' for t in (T[:3] if mob else T))
    side = f'<h2>기울기 도감 · 귀한 장비에만 붙음</h2>{tlist}'
    body = f'<div class=row><div>{card}</div><div>{side}</div></div>'
    return (f"<style>{css(*((390,844) if mob else (1280,720)), mob)}{EX(mob)}</style><div class=win><h1>장비 정보</h1><div class=sub>옵션 줄은 한도 안에서 굴림 · 굴림 위치는 붉은 막대 · 숫자는 임시값</div>{body}<div class=btn>착용하기</div></div>")
if __name__ == "__main__":
    tmp = os.path.join(OUT, "_g_tmp"); os.makedirs(tmp, exist_ok=True)
    js = ["const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"]
    for mob in (False, True):
        n = "phone" if mob else "pc"; f = os.path.join(tmp, f"aff_{n}.html"); open(f, "w", encoding="utf-8").write("<!doctype html><meta charset=utf-8>" + page(mob))
        w, h = (390, 844) if mob else (1280, 720)
        js.append(f"{{const p=await b.newPage({{viewport:{{width:{w},height:{h}}}}});await p.goto('file://{f}');await p.waitForTimeout(400);await p.screenshot({{path:'{OUT}/growth_affix_hanji_{n}.png'}});}}")
    js.append("await b.close()})()")
    open(os.path.join(tmp, "ra.cjs"), "w").write("\n".join(js))
    subprocess.run(["node", os.path.join(tmp, "ra.cjs")], env={**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()}, check=True)
