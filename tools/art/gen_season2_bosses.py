"""시즌 2 보스 B-13~B-20 (8종) 콘셉트 시트. 카드 틀은 gen_season1_bosses 와 같다. 한(恨)·이득은 SCENARIO-MASTER §5 기준."""
import os, gen_season1_bosses as S
K, HANJI, RED, GOLD, CHEON, VIO, CHAIN = S.K, S.HANJI, S.RED, S.GOLD, S.CHEON, S.VIO, S.CHAIN
P = S.person
S.FIG.clear()
S.FIG.update({
 "B-13": lambda: P(f'<ellipse cx="0" cy="-160" rx="20" ry="22" fill="{K}"/>', f'<path d="M-34,0 L-26,-140 L26,-140 L34,0Z" fill="{K}"/>', ''.join(f'<ellipse cx="{-90+i*40}" cy="-60" rx="12" ry="40" fill="{CHAIN}" opacity=".5"/>' for i in range(5) if i != 2)),
 "B-14": lambda: ''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{K}"/>' for x, y, r in [(-30,-40,40),(30,-36,38),(0,-90,34),(0,-10,36),(-60,-6,22),(62,-6,22)]) + f'<ellipse cx="0" cy="0" rx="100" ry="30" fill="none" stroke="{RED}" stroke-width="4" stroke-dasharray="9 7"/>',
 "B-15": lambda: P(f'<path d="M-24,-150 L24,-150 L18,-172 L-18,-172Z" fill="{K}"/>', f'<path d="M-30,0 L-22,-146 L22,-146 L30,0Z" fill="{K}"/>', f'<path d="M30,-110 L80,-170" stroke="{K}" stroke-width="6"/><path d="M76,-176 L90,-200 L96,-172Z" fill="{K}"/><text x="-70" y="-110" fill="{K}" font-size="30">0 1 2</text>'),
 "B-16": lambda: P(f'<ellipse cx="0" cy="-130" rx="20" ry="22" fill="{K}"/>', f'<path d="M-40,0 L-34,-110 L34,-110 L40,0Z" fill="{K}"/>', f'<rect x="-100" y="-50" width="200" height="50" rx="8" fill="{K}"/><ellipse cx="0" cy="-48" rx="80" ry="12" fill="#2A2A38" stroke="{VIO}" stroke-width="3"/>'),
 "B-17": lambda: P(f'<path d="M-24,-190 L0,-214 L24,-190Z" fill="{K}"/>', f'<path d="M-44,0 L-36,-180 L36,-180 L44,0Z" fill="{K}"/>', f'<rect x="64" y="-190" width="8" height="190" fill="{K}"/><path d="M60,-190 L76,-210 L80,-190Z" fill="{K}"/>'),
 "B-18": lambda: P(f'<ellipse cx="0" cy="-166" rx="20" ry="22" fill="{K}"/>', f'<path d="M-30,0 L-22,-146 L22,-146 L30,0Z" fill="{K}" stroke="{CHAIN}" stroke-width="2" stroke-dasharray="6 4"/>', f'<rect x="-14" y="-196" width="28" height="12" fill="{RED}"/><path d="M-30,-100 L-70,-60 M30,-100 L70,-60" stroke="{K}" stroke-width="12"/>'),
 "B-19": lambda: P(f'<ellipse cx="0" cy="-176" rx="30" ry="9" fill="{K}"/><rect x="-10" y="-198" width="20" height="24" fill="{K}"/>', f'<path d="M-30,0 L-20,-160 L20,-160 L30,0Z" fill="{K}" stroke="{RED}" stroke-width="3"/>', f'<path d="M24,-110 Q70,-120 78,-60" stroke="{CHAIN}" stroke-width="3" fill="none"/><rect x="-6" y="-200" width="0" height="0"/>'),
 "B-20": lambda: ''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{K}"/>' for x, y, r in [(-60,-50,56),(60,-50,56),(0,-110,52),(0,-20,50),(-110,-10,32),(110,-10,32),(-40,-150,28),(40,-150,28)]) + f'<ellipse cx="0" cy="8" rx="150" ry="40" fill="none" stroke="{VIO}" stroke-width="5"/><circle cx="-20" cy="-110" r="7" fill="{HANJI}"/><circle cx="20" cy="-110" r="7" fill="{HANJI}"/>',
})
S.CARDS[:] = [
 ("B-13", "줄의 맨 앞 노인", "기다림형", "남을 먼저 태우다 백 년째 맨 앞에 서 있다", "삼도천 나루", "뒤에 선 혼 줄이 장판 방향을 알려 준다. 줄 혼을 건드리면 손해(제안)"),
 ("B-14", "돌아선 혼들의 덩어리", "덩어리형", "기다리다 돌아선 혼 수백이 엉겼다(천도 불가)", "삼도천 나루", "붉은 점선 고리 안은 항상 위험. 파혼만 가능"),
 ("B-15", "숫자를 처음 쓴 서리", "기록형", "먹을 아끼려고 이름 대신 숫자를 상소했다", "저승 관아", "바닥 번호 칸 분류. 숫자 마당의 혼이 번호순으로 줄 선다"),
 ("B-16", "벼루지기", "기록형", "천도된 기억을 갈아 먹을 만들며 전부 봐야 했다", "먹방", "벼루에서 먹물이 번진다. 기억색 보라 장판이 시야를 가린다"),
 ("B-17", "아홉째 문지기", "기다림형", "문을 지키다 잠든 사이 인을 도둑맞았다", "명부전 담장", "문이 열리는 박자에 맞춰 돌진을 피한다. 깃대 휘두르기"),
 ("B-18", "인을 훔친 혼", "기록형", "이름이 없어 자기 이마에 인을 찍으려 했다 — 나와 같은 처지", "인장 굴", "붉은 인 자국 장판. 인장 벽의 이마 높이 자국이 점등한다"),
 ("B-19", "첫 차사", "차사형", "처음으로 혼을 깨뜨렸다. 그 이름을 기억하지 못했다", "우물터", "플레이어 거울상 패턴. 철삭을 마주 휘두른다"),
 ("B-20", "큰 물막이", "덩어리형", "모든 관할에서 깨진 이름이 흘러와 고인 덩어리", "물막이 바닥", "풀어내기 / 파혼으로 결말이 갈린다. 가장 큰 실루엣"),
]
if __name__ == "__main__":
    S.OUT = S.OUT
    open(os.path.join(S.OUT, "P2-045-season2-bosses.svg"), "w", encoding="utf-8").write(S.svg().replace("시즌 1 보스 콘셉트 시트 — B-02, B-04~B-12 (10종)", "시즌 2 보스 콘셉트 시트 — B-13~B-20 (8종)").replace("B-01 나루 영감은 스프라이트로, B-03 서 의원은 P2-041 로 이미 있음. ", "")); print("ok")
