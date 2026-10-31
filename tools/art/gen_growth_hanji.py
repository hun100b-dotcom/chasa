"""도술·조합 화면 한지판. 기획 정본 data/growth.json(도술 27, 인 15, 넋 5색)을 읽어 그대로 그린다.
이유: 숫자·이름을 손으로 옮기면 어긋나므로 JSON에서 직접 뽑는다."""
import os, json, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SP = os.path.join(ROOT, "assets", "sprites"); OUT = os.path.join(ROOT, "assets", "ui")
D = json.load(open(os.path.join(ROOT, "data", "growth.json"), encoding="utf-8"))
def css(W, H, mob):
    return f"""*{{box-sizing:border-box;margin:0}}body{{width:{W}px;height:{H}px;background:radial-gradient(circle at 50% 20%,#1D2C52,#0F1729);font-family:'Noto Serif KR','Noto Sans KR',serif;color:#2A2A38;overflow:hidden}}
.win{{position:absolute;inset:{4 if mob else 24}px;border:48px solid transparent;border-image:url(file://{SP}/ui/ui_hanji_panel.png) 48 fill/{18 if mob else 30}px stretch;padding:{4 if mob else 10}px}}
h1{{font-size:{20 if mob else 24}px}} .sub{{font-size:12px;color:#7a5a2a;margin-bottom:6px}}
.cols{{display:flex;gap:14px;{'flex-direction:column;gap:6px' if mob else ''}}} .col{{flex:1}}
.sch{{font-weight:bold;font-size:15px;padding-bottom:2px;border-bottom:3px solid var(--c);margin-bottom:5px}}
.sk{{display:flex;align-items:center;gap:6px;font-size:{11 if mob else 13}px;height:{19 if mob else 28}px;border-bottom:1px dotted #b9a784}}
.sk i{{font-style:normal;font-size:10px;padding:0 4px;border:1px solid #2A2A38;border-radius:3px}} .sk .d{{margin-left:auto;font-size:10px;color:#E85C41}}
.seal{{position:absolute;right:{18 if mob else 70}px;top:{18 if mob else 52}px;width:28px}}
.sealg{{display:grid;grid-template-columns:repeat({3 if mob else 5},1fr);gap:5px}}
.sg{{border:20px solid transparent;border-image:url(file://{SP}/ui/ui_ink_border_thin.png) 28 fill/8px stretch;font-size:{10 if mob else 12}px;line-height:1.3;padding:0 2px;min-height:{50 if mob else 62}px}}
.nk{{display:flex;gap:8px;margin:6px 0}} .nk b{{width:{26 if mob else 34}px;height:{26 if mob else 34}px;border-radius:50%;border:2px solid #2A2A38;display:block}}
"""
def skills(mob):
    cols = ""
    for k, sc in D["schools"].items():
        rows = "".join(f'<div class=sk><i>{"능" if s["kind"]=="active" else "상"}</i>{s["name"]}<span class=d>{"체험" if s.get("demo") else ""}</span></div>' for s in D["skills"] if s["school"] == k)
        cols += f'<div class=col style="--c:{sc["color"]}"><div class=sch>{sc["name"]} · {sc["lean"]}</div>{rows}</div>'
    return f"<style>{css(*((390,844) if mob else (1280,720)), mob)}</style><div class=win><h1>도술</h1><div class=sub>3갈래 × 9 = 27 · 능=쓰는 도술 / 상=늘 켜진 도술 · 붉은 글자=시연판에 들어감</div><div class=cols>{cols}</div><img class=seal src=file://{SP}/ui/ui_seal_select.png></div>"
def combine(mob):
    nk = "".join(f'<b style="background:{n["hex"]}" title="{n["name"]}"></b>' for n in D["neok_colors"])
    sg = "".join(f'<div class=sg><b>{s["name"]}</b><br>{s["effect"]}</div>' for s in D["seals"][:15 if not mob else 9])
    return f"<style>{css(*((390,844) if mob else (1280,720)), mob)}</style><div class=win><h1>조합</h1><div class=sub>넋 오방색 5색 — 같은 색 둘이면 같은 인, 다른 색이면 섞인 인</div><div class=nk>{nk}</div><div class=sealg>{sg}</div></div>"
if __name__ == "__main__":
    tmp = os.path.join(OUT, "_g_tmp"); os.makedirs(tmp, exist_ok=True)
    js = ["const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"]
    for nm, fn in [("skilltree", skills), ("combine", combine)]:
        for mob in (False, True):
            n = "phone" if mob else "pc"; f = os.path.join(tmp, f"{nm}_{n}.html"); open(f, "w", encoding="utf-8").write("<!doctype html><meta charset=utf-8>" + fn(mob))
            w, h = (390, 844) if mob else (1280, 720)
            js.append(f"{{const p=await b.newPage({{viewport:{{width:{w},height:{h}}}}});await p.goto('file://{f}');await p.waitForTimeout(400);await p.screenshot({{path:'{OUT}/growth_{nm}_hanji_{n}.png'}});}}")
    js.append("await b.close()})()")
    open(os.path.join(tmp, "r.cjs"), "w").write("\n".join(js))
    subprocess.run(["node", os.path.join(tmp, "r.cjs")], env={**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()}, check=True)
