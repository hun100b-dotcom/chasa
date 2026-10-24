"""시즌 1 보스 12종 중 시트가 없던 10종(B-02,04~12)의 실루엣 콘셉트 시트 생성기.
이미 있는 것: B-01 나루 영감(스프라이트), B-03 서 의원(P2-041).
원형 7종 색 규칙은 BOSS-ARCHETYPES.md. 한 장에 10장의 카드: 실루엣 + 한 줄 한 + 전투 신호.
작품명 참조 없음. 수치는 시나리오 문서 기준이며 확정은 QA."""
import os
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "concepts")
BG, INK, HANJI, TEAL, RED, GOLD, CHEON, VIO, CHAIN = "#0F1729", "#2A2A38", "#F3E7D3", "#4FA8A0", "#E85C41", "#D4A94E", "#5FE3C0", "#C9B0FF", "#BFE8FF"
K = "#14141C"  # 실루엣 먹빛(배경 카드 위에서 읽히도록 한지 바탕 카드 사용)

def person(hat, body, extra=""):
    return f'<ellipse cx="0" cy="2" rx="46" ry="12" fill="#000" opacity=".25"/>{body}{hat}{extra}'

FIG = {
 # B-02 월화: 굿 옷 + 큰 소매 + 살 부러진 부채 + 엎어진 잔
 "B-02": lambda: person('<path d="M-22,-170 L0,-205 L22,-170 Z" fill="%s"/>'%K,
     f'<path d="M-40,0 L-26,-160 L26,-160 L40,0 Q0,12 -40,0Z" fill="{K}"/><path d="M-26,-140 L-84,-90 L-70,-60 L-30,-100 Z M26,-140 L80,-110 L90,-80 L30,-100Z" fill="{K}"/>',
     f'<path d="M80,-110 L100,-170 M80,-110 L124,-150 M80,-110 L140,-120" stroke="{K}" stroke-width="4"/><path d="M-70,-52 L-52,-52 L-56,-34 L-66,-34 Z" fill="{RED}"/>'),
 # B-04/12 흑월: 갓 + 긴 도포 + 사슬 (차사 거울상, 붉은 테두리)
 "B-04": lambda: person(f'<ellipse cx="0" cy="-176" rx="48" ry="9" fill="{K}"/><rect x="-14" y="-206" width="28" height="30" fill="{K}"/><path d="M-12,-172 L-10,-150" stroke="{RED}" stroke-width="3"/>',
     f'<path d="M-36,0 L-24,-160 L24,-160 L36,0 Q0,10 -36,0Z" fill="{K}" stroke="{RED}" stroke-width="3"/>',
     f'<path d="M30,-120 Q80,-130 90,-70" stroke="{CHAIN}" stroke-width="4" fill="none"/>'),
 "B-12": lambda: person(f'<ellipse cx="0" cy="-176" rx="52" ry="10" fill="{K}"/><rect x="-14" y="-210" width="28" height="34" fill="{K}"/><path d="M-12,-172 L-10,-146" stroke="{RED}" stroke-width="3"/>',
     f'<path d="M-40,0 L-26,-160 L26,-160 L40,0 Q0,10 -40,0Z" fill="{K}" stroke="{RED}" stroke-width="3"/><circle cx="0" cy="-110" r="14" fill="{VIO}" opacity=".9"/>',
     f'<path d="M30,-130 Q120,-150 126,-60 M-30,-130 Q-120,-150 -126,-60" stroke="{CHAIN}" stroke-width="4" fill="none"/>'),
 # B-05 기수 대돌: 찢어진 깃발
 "B-05": lambda: person(f'<path d="M-18,-168 Q0,-196 18,-168Z" fill="{K}"/>',
     f'<path d="M-30,0 L-22,-160 L22,-160 L30,0Z" fill="{K}"/>',
     f'<rect x="38" y="-230" width="6" height="232" fill="{K}"/><path d="M44,-228 L120,-214 L104,-196 L122,-180 L96,-172 L44,-176Z" fill="{K}"/><path d="M60,-212 l14,0 M60,-200 l18,0" stroke="#F3E7D3" stroke-width="2"/>'),
 # B-06 장수: 넓은 갑주 + 번호 패
 "B-06": lambda: person(f'<path d="M-24,-180 L0,-214 L24,-180Z" fill="{K}"/>',
     f'<path d="M-56,0 L-60,-150 L-30,-168 L30,-168 L60,-150 L56,0Z" fill="{K}"/><path d="M-60,-150 L-90,-110 M60,-150 L90,-110" stroke="{K}" stroke-width="16"/>',
     ''.join(f'<rect x="{-40+i*28}" y="-130" width="20" height="28" fill="{HANJI}" opacity=".85"/>' for i in range(3))+f'<path d="M-100,-100 L-104,-210" stroke="{K}" stroke-width="6"/>'),
 # B-07 칠성: 갱도 반장, 곡괭이 + 등불
 "B-07": lambda: person(f'<path d="M-24,-166 Q0,-200 24,-166Z" fill="{K}"/>',
     f'<path d="M-34,0 L-26,-160 L26,-160 L34,0Z" fill="{K}"/>',
     f'<path d="M30,-130 L90,-210 M70,-222 L114,-196" stroke="{K}" stroke-width="8"/><rect x="-70" y="-120" width="22" height="30" fill="{K}"/><circle cx="-59" cy="-105" r="26" fill="{GOLD}" opacity=".25"/><text x="0" y="-100" fill="{HANJI}" font-size="26" text-anchor="middle">七</text>'),
 # B-08 염씨: 앉은 장부꾼 + 큰 장부
 "B-08": lambda: person(f'<ellipse cx="0" cy="-130" rx="22" ry="24" fill="{K}"/>',
     f'<path d="M-50,0 L-44,-112 L44,-112 L50,0 Z" fill="{K}"/>',
     f'<path d="M-96,-40 L0,-70 L96,-40 L96,-4 L0,-34 L-96,-4Z" fill="{K}" stroke="{HANJI}" stroke-width="2"/><text x="-40" y="-176" fill="{K}" font-size="22">十四 三 九</text><path d="M54,-120 L90,-170" stroke="{K}" stroke-width="5"/>'),
 # B-09 망부석 아낙: 바위와 붙은 몸 + 옷 한 벌
 "B-09": lambda: person('',
     f'<path d="M-70,0 Q-76,-70 -30,-96 Q0,-110 30,-96 Q70,-70 70,0Z" fill="{K}"/><path d="M-18,-90 L-14,-170 L18,-170 L14,-90Z" fill="{K}"/><ellipse cx="0" cy="-184" rx="20" ry="22" fill="{K}"/>',
     f'<path d="M-60,-30 q15,-14 30,0 t30,0 t30,0 t30,0" stroke="{CHAIN}" stroke-width="4" fill="none"/><path d="M14,-130 L50,-120 L44,-70 L12,-80Z" fill="{HANJI}" opacity=".8"/>'),
 # B-10 선장: 기운 갑판 + 밧줄 + 패랭이
 "B-10": lambda: f'<g transform="rotate(-8)"><rect x="-110" y="0" width="220" height="14" fill="{K}"/></g>' + person(f'<path d="M-30,-170 L30,-170 L24,-182 L-24,-182Z" fill="{K}"/>',
     f'<path d="M-30,0 L-22,-165 L22,-165 L30,0Z" fill="{K}"/>',
     f'<path d="M26,-120 Q90,-150 110,-60 L120,-30" stroke="{K}" stroke-width="5" fill="none"/>'),
 # B-11 왕초: 누더기 + 별명 목걸이
 "B-11": lambda: person(f'<ellipse cx="0" cy="-172" rx="22" ry="24" fill="{K}"/>',
     f'<path d="M-50,0 L-34,-150 L34,-150 L50,0 L30,-12 L10,2 L-10,-12 L-30,2Z" fill="{K}"/>',
     ''.join(f'<rect x="{-24+i*12}" y="{-146+abs(i-2)*-6+10}" width="8" height="16" fill="{HANJI}"/>' for i in range(5))),
}
CARDS = [
 ("B-02","월화","의식형","끝내지 못한 열두 거리 굿, 엎어진 열두째 잔","폐당집","열두 잔 순서대로 장판이 열린다. 엎어진 잔 칸만 안전(제안)"),
 ("B-04","흑월 차사 · 1차","차사형","처결 없음. 맺힘 50%에서 사슬을 내려놓고 한마디","무덤골","천도와 파혼을 둘 다 쓴다. 그가 깨뜨린 폭발이 내 얼룩을 키운다"),
 ("B-05","기수 대돌","무리형","동료 서른일곱 이름을 외우다 하나씩 잊는다","붉은재 산성","이름 잊은 자리는 번호 병사로 바뀌어 더 사나움(맺힘 +30%)"),
 ("B-06","이름 없는 장수","무리형","부하를 번호로 불러 진을 짰다","붉은재 군막","호령 번호에 맞춰 대형이 바뀐다. 호령을 읽으면 빈틈"),
 ("B-07","갱도 반장 칠성","무리형","열셋을 내보내고 자기 번호를 세지 않았다","쇳골 막장","광부 혼을 파혼하면 숫자가 틀려 광폭. 이 전투만 잡몹 파혼이 손해"),
 ("B-08","장부꾼 염씨","기록형","죽음을 '손실 열넷'으로 적고 뒷장에 이름을 적었다","쇳골 주인집","숫자 지뢰. 이름이 적힌 종이는 밟아도 무해, 맺힘을 더 깎는다"),
 ("B-09","망부석 아낙","기다림형","돌아오지 않는 배를 기다리다 바다에 들었다","곶 끝","줄지어 오는 파도 장판. 물 혼 천도로 파도 한 줄이 약해진다"),
 ("B-10","만선호 선장","무리형","배를 버리고 혼자 살아 돌아왔다","난파 여울","썰물 밤에만 열림. 기운 갑판, 줄 끊기 직선 장판"),
 ("B-11","다리 밑 왕초","무리형","떠돌이들의 이름을 지어 부른 유일한 사람","도성 다리 밑","별명을 부르면 혼이 일어나 협공. 낮에 들은 별명 혼은 돌아선다"),
 ("B-12","흑월 차사 · 2차","차사형","그 밤 구하지 못한 젊은이(=나)","성문 밖","사슬 양손. 천도 시 F9(내 정체). 기억 보라 테두리가 시야 가장자리에 번진다"),
]
def svg():
    cw, ch, cols = 400, 470, 3
    rows = (len(CARDS) + cols - 1) // cols
    W, H = cols * cw + 40, rows * ch + 110
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="sans-serif"><rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="20" y="38" fill="{HANJI}" font-size="22" font-weight="bold">시즌 1 보스 콘셉트 시트 — B-02, B-04~B-12 (10종)</text>',
         f'<text x="20" y="62" fill="{TEAL}" font-size="12">B-01 나루 영감은 스프라이트로, B-03 서 의원은 P2-041 로 이미 있음. 도형 초안·실루엣 합격선 = 검정으로 칠해도 구별. 작품명 참조 없음.</text>']
    for i, (bid, name, arche, han, place, fight) in enumerate(CARDS):
        x, y = 20 + (i % cols) * cw, 90 + (i // cols) * ch
        o.append(f'<rect x="{x}" y="{y}" width="{cw-16}" height="{ch-16}" rx="12" fill="#16213E" stroke="{TEAL}" stroke-opacity=".4"/>')
        o.append(f'<rect x="{x+12}" y="{y+52}" width="{cw-40}" height="252" rx="8" fill="{HANJI}" opacity=".92"/>')
        o.append(f'<text x="{x+16}" y="{y+30}" fill="{GOLD}" font-size="16" font-weight="bold">{bid} {name}</text><text x="{x+cw-32}" y="{y+30}" fill="{TEAL}" font-size="12" text-anchor="end">{arche} · {place}</text>')
        o.append(f'<g transform="translate({x+(cw-16)/2},{y+285})">{FIG[bid]()}</g>')
        # 길이 제한 줄바꿈
        def wrap(s, n):
            return [s[k:k+n] for k in range(0, len(s), n)]
        yy = y + 330
        o.append(f'<text x="{x+16}" y="{yy}" fill="{GOLD}" font-size="12" font-weight="bold">한(恨)</text>')
        for L in wrap(han, 24): yy += 18; o.append(f'<text x="{x+16}" y="{yy}" fill="{HANJI}" font-size="13">{L}</text>')
        yy += 26; o.append(f'<text x="{x+16}" y="{yy}" fill="{RED}" font-size="12" font-weight="bold">전투 신호</text>')
        for L in wrap(fight, 24): yy += 18; o.append(f'<text x="{x+16}" y="{yy}" fill="{HANJI}" font-size="13">{L}</text>')
    o.append('</svg>')
    return "".join(o)
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "P2-042-season1-bosses.svg"), "w", encoding="utf-8").write(svg()); print("ok")
