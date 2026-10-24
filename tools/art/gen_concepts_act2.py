"""③ 붉은재 싸움터 · ④ 쇳골 광산 타일·소품 실루엣 시트 생성기 (도형 초안).
근거: SCENARIO-ACT2 §1·§2. 실제 전쟁·사고를 특정하는 도상(깃발 문장·국가색)은 쓰지 않는다.
색: palette-tokens.json + 이 지역 보조색(녹슨 철 #6B4A3A, 석탄 #1C1C22, 흙 #5B4D3E)은 혼 대비 3:1 이상만 바닥에 쓴다."""
import os
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "concepts")
BG, HANJI, TEAL, GOLD, RED = "#0F1729", "#F3E7D3", "#4FA8A0", "#D4A94E", "#E85C41"
K = "#000"

def dia(c, extra=""):
    return f'<path d="M0,-32 L64,0 L0,32 L-64,0 Z" fill="{c}" stroke="{BG}"/>{extra}'
def line(d, c, w=3): return f'<path d="{d}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" fill="none"/>'

ZONES = {
 "③ 붉은재 싸움터 (산성 · 화살골 · 군막 터 · 큰 무덤)": (
  [("성돌 바닥", "#4A4F5E", line("M-40,0 L-10,-14 M8,10 L40,-2", "#3A3E4A", 4)),
   ("화살골 자갈", "#5B4D3E", line("M-30,6 l4,-6 M0,-8 l5,-5 M22,8 l5,-5", "#8A7A62", 3)),
   ("군막 터 흙", "#4F4436", line("M-44,0 L44,0 M0,-22 L0,22", "#3E352A", 2)),
   ("큰 무덤 풀", "#2F4535", line("M-30,6 l4,-10 M-6,-6 l4,-10 M20,8 l4,-10", "#5E7A4C", 2)),
   ("무너진 성돌", "#3E4250", line("M-26,-8 L-4,-18 L10,-6 L-8,8 Z", "#2B2E38", 3)),
   ("녹슨 화살 박힌 땅", "#4F4436", line("M-10,8 L10,-12 M10,-12 l-5,0 M10,-12 l0,5", "#6B4A3A", 3))],
  [("무너진 성벽", "wall"), ("깃대 꽂힘", "flag"), ("녹슨 화살 다발", "arrows"), ("찢어진 군막", "tent"),
   ("진법도 널판", "board"), ("비석 없는 봉분", "mound"), ("술독 서른일곱", "jars"), ("부러진 수레", "cart"),
   ("목패 말뚝", "post"), ("횃불대", "torch")]),
 "⑤ 갯마을 (포구 · 소금밭 · 망부석 곶 · 난파 여울)": (
  [("선창 널판", "#5B4D3E", line("M-44,-4 L-14,-18 M-30,6 L10,-12 M-6,18 L40,-4", "#42362A", 3)),
   ("갯벌", "#3E4A52", line("M-30,4 q10,-8 20,0 t20,0", "#2E3A44", 3)),
   ("소금밭 칸", "#8E98A0", line("M-40,0 L0,-20 L40,0 L0,20 Z", "#6C7680", 3)),
   ("바위 곶", "#4A4F5E", line("M-26,-8 L-4,-18 L10,-6 L-8,8 Z", "#2B2E38", 3)),
   ("헛묘 풀", "#2F4535", line("M-30,6 l4,-10 M-6,-6 l4,-10 M20,8 l4,-10", "#5E7A4C", 2)),
   ("여울 물", "#1D2C47", line("M-40,0 q10,-8 20,0 t20,0 t20,0", "#4FA8A0", 2))],
  [("빈 배 (묶임)", "boat"), ("그물 걸이", "net"), ("소금 더미", "pile"), ("객주 집", "stable"), ("망부석 바위", "stone_f"),
   ("헛묘 (옷만 묻힘)", "mound"), ("부서진 돛대", "mast"), ("암초", "rubble"), ("등대 장대", "torch"), ("줄 말뚝", "post")]),
 "⑥ 도성 (저잣거리 · 큰 다리 밑 · 움막촌 · 성문 밖)": (
  [("저잣 박석", "#4A4F5E", line("M-32,-8 L0,-24 L32,-8 L0,8 Z", "#2B2E38", 2)),
   ("다리 밑 모래", "#5B4D3E", line("M-30,6 l4,-6 M0,-8 l5,-5 M22,8 l5,-5", "#8A7A62", 3)),
   ("판잣집 바닥", "#4F4436", line("M-44,-4 L-14,-18 M-30,6 L10,-12", "#3E352A", 3)),
   ("성문 앞 돌", "#3E4250", line("M-40,0 L40,0 M0,-20 L0,20", "#2B2E38", 3)),
   ("구덩이 흙", "#2E2E38", line("M-24,-4 L-4,-14 L16,-4 L-4,6 Z", "#14141C", 3)),
   ("등불 번짐 바닥", "#5A5A63", line("M-20,0 q20,-20 40,0", "#E8C98A", 3))],
  [("좌판 천막", "tent"), ("등롱 줄", "torch"), ("돌다리 기둥", "post"), ("거적 움막", "stable"), ("판잣집", "tags"),
   ("닫힌 성문", "gate"), ("팻말 없는 구덩이", "mound"), ("성벽 조각", "wall"), ("솟대", "torch"), ("수레", "cart")]),
 "④ 쇳골 광산 (광부촌 · 선탄장 · 큰 갱도 · 무너진 막장)": (
  [("판자 바닥", "#5B4D3E", line("M-44,-4 L-14,-18 M-30,6 L10,-12 M-6,18 L40,-4", "#42362A", 3)),
   ("석탄 가루 땅", "#2E2E38", line("M-30,4 l6,-4 M8,-10 l6,-4 M20,10 l6,-4", "#4A4A58", 3)),
   ("갱도 레일", "#3C3C48", line("M-48,2 L30,-26 M-30,16 L48,-12", "#6B4A3A", 4)),
   ("버팀목 바닥", "#4F4436", line("M-52,0 L0,-26 M-26,13 L26,-13", "#2E2418", 5)),
   ("무너진 돌무더기", "#4A4F5E", line("M-26,-6 L-8,-18 L10,-8 L0,8 L-20,6 Z", "#2B2E38", 3)),
   ("분필 숫자 칸", "#3C3C48", line("M-24,-4 L-4,-14 L16,-4 L-4,6 Z", "#F3E7D3", 2))],
  [("갱도 입구 틀", "gate"), ("목패 걸이 판", "tags"), ("석탄 고르는 평상", "bench"), ("석탄 수레", "cart"),
   ("광석 더미", "pile"), ("버팀목 기둥", "post"), ("등불 걸이", "torch"), ("외상 장부 벽", "board"),
   ("막장 막힌 돌", "rubble"), ("빈 노새 마구간", "stable")]),
}
SH = {
 "wall": '<path d="M-66,0 L-66,-70 L-40,-60 L-34,-90 L-10,-70 L12,-80 L30,-56 L66,-62 L66,0 L0,30Z"/>',
 "flag": '<rect x="-3" y="-120" width="6" height="120"/><path d="M3,-118 L70,-104 L54,-88 L72,-72 L3,-70Z"/>',
 "arrows": '<path d="M-20,0 L-24,-80 M-4,0 L-4,-90 M14,0 L18,-84 M30,0 L36,-70" stroke="#000" stroke-width="5"/>',
 "tent": '<path d="M-70,0 L-10,-90 L0,-70 L14,-96 L70,0 L0,26Z"/>',
 "board": '<rect x="-40" y="-90" width="80" height="62"/><rect x="-6" y="-28" width="12" height="28"/>',
 "mound": '<path d="M-70,0 Q-60,-66 0,-70 Q60,-66 70,0 L0,34Z"/>',
 "jars": ''.join(f'<ellipse cx="{x}" cy="{y}" rx="16" ry="22"/>' for x, y in [(-40,-20),(-10,-26),(22,-20),(50,-22),(-24,-2),(8,-4),(38,-2)]),
 "cart": '<path d="M-50,-30 L50,-44 L56,-10 L-44,0Z"/><circle cx="-26" cy="4" r="16"/><circle cx="34" cy="-4" r="16"/><path d="M50,-44 L90,-50" stroke="#000" stroke-width="5"/>',
 "post": '<rect x="-6" y="-100" width="12" height="100"/><rect x="-24" y="-90" width="48" height="10"/><rect x="-12" y="-70" width="10" height="16"/><rect x="4" y="-62" width="10" height="16"/>',
 "torch": '<rect x="-3" y="-96" width="6" height="96"/><path d="M-12,-96 Q0,-130 12,-96Z"/><ellipse cx="0" cy="2" rx="16" ry="6"/>',
 "boat": '<path d="M-70,-20 L70,-20 L52,16 L-52,16 Z"/><rect x="-3" y="-90" width="6" height="70"/><path d="M3,-88 L40,-30 L3,-30Z"/>',
 "net": '<path d="M-60,0 L-60,-90 M60,0 L60,-90 M-60,-90 L60,-90" stroke="#000" stroke-width="6"/><path d="M-60,-70 L60,-30 M-60,-30 L60,-70 M-20,-90 L-20,-20 M20,-90 L20,-20" stroke="#000" stroke-width="3"/>',
 "stone_f": '<path d="M-50,0 L-40,-40 L-24,-70 L-16,-110 Q0,-130 16,-110 L24,-70 L44,-30 L56,0 L0,26Z"/>',
 "mast": '<rect x="-4" y="-120" width="8" height="120" transform="rotate(12)"/><path d="M4,-110 L50,-80 L8,-70Z" transform="rotate(12)"/>',
 "gate": '<path d="M-60,0 L-60,-100 L60,-100 L60,0 L40,0 L40,-80 L-40,-80 L-40,0Z"/>',
 "tags": '<rect x="-50" y="-90" width="100" height="70"/>' + ''.join(f'<rect x="{-42+i*16}" y="-14" width="10" height="16"/>' for i in range(6)),
 "bench": '<path d="M-60,-30 L60,-30 L60,-18 L-60,-18Z M-52,-18 L-52,0 M52,-18 L52,0 M-4,-18 L-4,0" stroke="#000" stroke-width="8"/>',
 "pile": '<path d="M-60,0 L-30,-40 L-8,-24 L12,-60 L40,-30 L64,0 L0,30Z"/>',
 "rubble": '<path d="M-60,0 L-40,-60 L-10,-40 L10,-80 L40,-50 L64,0 L0,30Z"/>',
 "stable": '<path d="M-70,0 L-70,-60 L0,-90 L70,-60 L70,0 L0,30Z"/><rect x="-14" y="-40" width="28" height="40" fill="#F3E7D3"/>',
}
def sheet():
    W = 1260
    rows = []
    y = 100
    o = [f'<text x="24" y="38" fill="{HANJI}" font-size="22" font-weight="bold">③~⑥ 붉은재·쇳골·갯마을·도성 타일·소품 실루엣 시트 (쿼터뷰 2:1, 도형 초안)</text>',
         f'<text x="24" y="60" fill="{TEAL}" font-size="12">검정으로 칠해도 읽히는지가 합격선. 실제 전쟁·사고를 특정하는 도상 없음. 작품명 참조 없음.</text>']
    for zone, (tiles, props) in ZONES.items():
        o.append(f'<text x="24" y="{y}" fill="{GOLD}" font-size="16" font-weight="bold">{zone}</text>')
        for i, (n, c, ex) in enumerate(tiles):
            cx, cy = 110 + i * 200, y + 70
            o.append(f'<g transform="translate({cx},{cy})">{dia(c, ex)}</g><text x="{cx}" y="{cy+58}" fill="{HANJI}" font-size="13" text-anchor="middle" font-weight="bold">{n}</text>')
        y += 170
        for i, (n, k) in enumerate(props):
            cx, cy = 130 + (i % 5) * 245, y + 120 + (i // 5) * 190
            o.append(f'<rect x="{cx-110}" y="{cy-110}" width="220" height="150" rx="10" fill="{HANJI}" opacity=".9"/><g transform="translate({cx},{cy})" fill="{K}">{SH[k]}</g><text x="{cx}" y="{cy+58}" fill="{HANJI}" font-size="13" text-anchor="middle" font-weight="bold">{n}</text>')
        y += 420
    H = y - 130
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="sans-serif"><rect width="{W}" height="{H}" fill="{BG}"/>' + "".join(o) + '</svg>'
if __name__ == "__main__":
    open(os.path.join(OUT, "P2-043-redash-ironbone-tiles-props.svg"), "w", encoding="utf-8").write(sheet()); print("ok")
