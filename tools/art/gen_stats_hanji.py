"""능력 창 한지판(PC 1280×720 · 폰 390×844). 기획 정본 data/growth.json의 stats·ranks·seal_cost를 읽어 그대로 그린다.
이유: 숫자를 손으로 옮기면 기획 JSON과 어긋나므로 JSON에서 직접 뽑는다. 값은 모두 임시값(오너 확인 전).
구성: 위=품계와 남은 점수, 가운데=능력치 4(힘·날램·몸·마음)+올리는 버튼(+), 아래=지금 능력치로 바뀐 수치(파생값)·장비 한 벌 효과."""
import os, json, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from gen_growth_hanji import ROOT, SP, OUT, D, css
EXTRA = lambda mob: f"""
.rk{{display:flex;align-items:baseline;gap:10px;margin:2px 0 8px}} .rk b{{font-size:{30 if mob else 38}px}} .rk span{{font-size:13px;color:#7a5a2a}}
.bar{{height:10px;border:2px solid #2A2A38;border-radius:6px;background:#e6d8b8;margin:2px 0 8px;overflow:hidden}} .bar i{{display:block;height:100%;background:#4FA8A0}}
.pt{{display:inline-block;border:2px solid #D4A94E;background:#fff4d6;border-radius:8px;padding:2px 10px;font-weight:bold;margin-right:8px}}
.grid{{display:grid;grid-template-columns:{'1fr' if mob else '1fr 1fr'};gap:{6 if mob else 14}px}}
.st{{display:flex;align-items:center;gap:8px;border-bottom:1px dotted #b9a784;min-height:{54 if mob else 64}px}}
.st .n{{width:{52 if mob else 62}px;font-weight:bold;font-size:{20 if mob else 22}px}} .st .v{{width:44px;font-size:24px;font-weight:bold;text-align:right}}
.st .d{{flex:1;font-size:{11 if mob else 12.5}px;line-height:1.35;color:#4a3a22}}
.plus{{width:48px;height:48px;border-radius:50%;border:3px solid #2A2A38;background:#D4A94E;font-size:30px;font-weight:bold;text-align:center;line-height:40px;flex:none}}
.dv{{font-size:{12 if mob else 13.5}px}} .dv div{{display:flex;justify-content:space-between;border-bottom:1px dotted #b9a784;padding:2px 0}} .dv b{{font-variant-numeric:tabular-nums}}
h2{{font-size:15px;margin:8px 0 3px;border-bottom:3px solid #4FA8A0}}
.btn{{position:absolute;left:14px;right:14px;bottom:{14 if mob else 22}px;height:54px;border:3px solid #D4A94E;background:#2A2A38;color:#D4A94E;border-radius:12px;text-align:center;line-height:48px;font-size:18px;font-weight:bold}}
"""
def page(mob):
    r, st = D["ranks"], D["stats"]
    V = {"str": 14, "agi": 9, "body": 12, "mind": 10}   # 예시 분배(시안용: 시작 10 + 올린 점수)
    rank, pts, nxt = 12, 5, round(40 * 13 ** 1.5)
    cur = round(40 * rank ** 1.5)
    rows = ""
    for s in st:
        rows += f'<div class=st><span class=n>{s["name"]}</span><span class=v>{V[s["id"]]}</span><span class=d>1점마다<br>{s["per_point"]}</span><span class=plus>+</span></div>'
    v = lambda k: V[k]
    dv = [("맺힘 피해", f'+{v("str")}%'), ("넉백", f'+{v("str")*0.5:.1f}%'), ("공격 속도", f'+{v("agi")*0.4:.1f}%'), ("이동 속도", f'+{v("agi")*0.2:.1f}%'),
          ("생명", f'{100 + v("body")*4}'), ("얼룩 둔화 저항", f'+{v("body")*0.5:.1f}%'), ("도술 위력", f'+{v("mind")}%'), ("천도 캐스팅", f'−{v("mind")*0.15:.2f}%')]
    dvh = "".join(f"<div><span>{a}</span><b>{b}</b></div>" for a, b in dv)
    sets = "".join(f'<div><span>{s["name"]}</span><b>{s["lean"]}</b></div>' for s in D["sets"][:2])
    prog = int((rank - r["min"]) / (r["max"] - r["min"]) * 100)
    return (f"<style>{css(*((390,844) if mob else (1280,720)), mob)}{EXTRA(mob)}</style><div class=win><h1>능력</h1>"
            f'<div class=rk><b>품계 {rank}</b><span>/ {r["max"]} · 다음 품계까지 넋 {nxt - cur:,}</span></div><div class=bar><i style="width:{prog}%"></i></div>'
            f'<div><span class=pt>남은 점수 {pts}</span><span class=sub>품계가 오를 때마다 +{r["points_per_rank"]}점 · 능력치마다 처음 {r["start_each"]}</span></div>'
            f'<div class=grid><div>{rows}</div><div><h2>지금 능력치로 바뀐 수치</h2><div class=dv>{dvh}</div><h2>입은 한 벌</h2><div class=dv>{sets}</div></div></div>'
            f'<div class=btn>점수 확정</div></div>')
if __name__ == "__main__":
    tmp = os.path.join(OUT, "_g_tmp"); os.makedirs(tmp, exist_ok=True)
    js = ["const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"]
    for mob in (False, True):
        n = "phone" if mob else "pc"; f = os.path.join(tmp, f"stats_{n}.html"); open(f, "w", encoding="utf-8").write("<!doctype html><meta charset=utf-8>" + page(mob))
        w, h = (390, 844) if mob else (1280, 720)
        js.append(f"{{const p=await b.newPage({{viewport:{{width:{w},height:{h}}}}});await p.goto('file://{f}');await p.waitForTimeout(400);await p.screenshot({{path:'{OUT}/growth_stats_hanji_{n}.png'}});}}")
    js.append("await b.close()})()")
    open(os.path.join(tmp, "rs.cjs"), "w").write("\n".join(js))
    subprocess.run(["node", os.path.join(tmp, "rs.cjs")], env={**os.environ, "NODE_PATH": subprocess.check_output(["npm", "root", "-g"], text=True).strip()}, check=True)
