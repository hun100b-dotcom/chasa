"""시즌 3 '백(魄, 몸)' 보스 B-21~B-31 (11종) 콘셉트 시트. 카드 틀은 gen_season1_bosses 공유.
시즌 3 규칙: 혼(빛)이 아니라 몸(흙·물·돌)이다 — 윤곽은 땅에서 솟은 덩어리처럼 두껍고, 반짝임은 없다.
거울 관계: B-24↔B-05·06, B-25↔B-07·08, B-26↔B-03, B-27↔B-12(흑월의 몸), B-31 = 주인공의 몸."""
import os, gen_season1_bosses as S
K, HANJI, RED, GOLD, CHEON, VIO, CHAIN = S.K, S.HANJI, S.RED, S.GOLD, S.CHEON, S.VIO, S.CHAIN
P = S.person
def blob(parts, extra=""): return ''.join(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{K}"/>' for x, y, rx, ry in parts) + extra
S.FIG.clear()
S.FIG.update({
 "B-21": lambda: P('', f'<path d="M-90,-10 Q0,-70 90,-10 L70,16 L-70,16Z" fill="{K}"/><path d="M-20,-50 L-14,-130 L14,-130 L22,-50Z" fill="{K}"/><ellipse cx="0" cy="-146" rx="18" ry="20" fill="{K}"/>', f'<path d="M-100,-40 Q-60,-80 -20,-60" stroke="{CHAIN}" stroke-width="3" fill="none" opacity=".6"/>'),
 "B-22": lambda: ''.join(f'<path d="M{x-12},0 L{x-8},-110 L{x+8},-110 L{x+12},0Z" fill="{K}"/><ellipse cx="{x}" cy="-124" rx="12" ry="14" fill="{K}"/>' for x in (-100,-66,-33,0,33,66,100)) + f'<path d="M-120,-70 Q0,-40 120,-70" stroke="{GOLD}" stroke-width="5" fill="none"/>',
 "B-23": lambda: blob([(0,-60,70,60),(-60,-20,40,30),(60,-20,40,30),(0,-120,40,30)], ''.join(f'<path d="M{x},{y} q20,-40 0,-80" stroke="{CHAIN}" stroke-width="3" fill="none"/>' for x, y in [(-40,-10),(0,0),(40,-10),(-70,-30),(70,-30)])),
 "B-24": lambda: ''.join(f'<circle cx="{x}" cy="{y}" r="16" fill="{K}"/>' for x, y in [(-100,-10),(-70,-30),(-40,-14),(-70,-60),(100,-10),(70,-30),(40,-14),(70,-60)]) + f'<path d="M0,-130 L0,0" stroke="{RED}" stroke-width="5" stroke-dasharray="8 6"/><ellipse cx="0" cy="8" rx="120" ry="30" fill="none" stroke="{K}" stroke-width="6"/>',
 "B-25": lambda: P(f'<path d="M-24,-166 Q0,-200 24,-166Z" fill="{K}"/>', f'<path d="M-34,0 L-26,-160 L26,-160 L34,0Z" fill="{K}"/>', f'<path d="M-120,-140 L-90,-200 L120,-200 L90,-140 L120,0 L-120,0Z" fill="none" stroke="{K}" stroke-width="10" stroke-dasharray="14 8"/><text x="0" y="-100" fill="{HANJI}" font-size="26" text-anchor="middle">七</text>'),
 "B-26": lambda: blob([(-50,-30,60,28),(50,-30,60,28),(-50,-70,50,22),(50,-70,50,22)], f'<path d="M-110,-20 L110,-20" stroke="{HANJI}" stroke-width="3" opacity=".6"/><path d="M0,-110 L0,10" stroke="{VIO}" stroke-width="4"/>'),
 "B-27": lambda: P(f'<ellipse cx="0" cy="-176" rx="48" ry="9" fill="{K}"/><rect x="-14" y="-206" width="28" height="30" fill="{K}"/>', f'<path d="M-40,0 L-26,-160 L26,-160 L40,0Z" fill="{K}" stroke="{RED}" stroke-width="3"/>', f'<path d="M-130,6 L130,6" stroke="{K}" stroke-width="5"/><text x="-150" y="-20" fill="{K}" font-size="22">明 月 日</text>'),
 "B-28": lambda: blob([(0,-10,120,26)], f'<path d="M-30,-30 Q0,-150 30,-30 L20,-30 Q0,-110 -20,-30Z" fill="{K}"/><path d="M-12,-100 q-10,-30 -30,-40 M12,-100 q10,-30 30,-40" stroke="{K}" stroke-width="8" fill="none"/><ellipse cx="0" cy="-8" rx="80" ry="14" fill="none" stroke="{VIO}" stroke-width="3"/>'),
 "B-29": lambda: P(f'<ellipse cx="0" cy="-130" rx="22" ry="24" fill="{K}"/>', f'<path d="M-50,0 L-40,-110 L40,-110 L50,0Z" fill="{K}"/>', f'<ellipse cx="80" cy="-14" rx="28" ry="12" fill="{K}"/><path d="M60,-20 L100,-20 L96,-44 L64,-44Z" fill="{HANJI}" opacity=".9"/><path d="M-90,-8 q-30,10 -10,24" stroke="{K}" stroke-width="8" fill="none"/>'),
 "B-30": lambda: blob([(0,-30,100,40),(0,-84,60,36)], f'<path d="M0,-200 L0,-110" stroke="{K}" stroke-width="7"/><path d="M-14,-110 Q0,-90 14,-110" stroke="{K}" stroke-width="7" fill="none"/><path d="M-100,-10 Q-60,16 0,10 Q60,16 100,-10" stroke="{CHAIN}" stroke-width="4" fill="none"/>'),
 "B-31": lambda: P(f'<ellipse cx="0" cy="-176" rx="48" ry="9" fill="{K}"/><rect x="-14" y="-206" width="28" height="30" fill="{K}"/><path d="M-12,-172 L-10,-150" stroke="{RED}" stroke-width="3"/>', f'<path d="M-36,0 L-24,-160 L24,-160 L36,0Z" fill="{K}" stroke="{CHEON}" stroke-width="3"/>', ''.join(f'<circle cx="{-96+i*32}" cy="-210" r="7" fill="{GOLD}"/>' for i in range(7)) + f'<ellipse cx="0" cy="6" rx="130" ry="34" fill="none" stroke="{CHAIN}" stroke-width="4" stroke-dasharray="10 6"/>'),
})
S.CARDS[:] = [
 ("B-21", "윤 영감의 백", "물형", "마지막 손님을 못 건넨 몸, 뒤집힌 배 밑에 박힘", "소 밑", "산 사람이 이름을 부르면 눕는다(F51). 소의 물살 장판"),
 ("B-22", "줄에 묶인 일곱", "무리형", "만선호 선원 일곱의 몸이 한 줄에 묶여 있다", "곶 밑 바다굴", "썰물에만 열림. 바다가 돌려준 물건 하나를 묻으면 눕는다(F53)"),
 ("B-23", "물 밑 매듭", "덩어리형", "수천 가닥 실이 엉킨 매듭, 사공의 배가 닿지 못한 까닭", "닻 여울", "실을 하나씩 풀어 길을 낸다(제안)"),
 ("B-24", "한 구덩이의 두 진", "무리형", "번호로 불린 진과 이름으로 불린 진이 한 구덩이에", "큰 무덤 속", "몸 60기 규모를 흙덩이 단위로 표현. 두 진의 빛깔을 가른다"),
 ("B-25", "반장 칠성의 백", "무리형", "맨 마지막에 나가는 몸, 막힌 막장 안쪽", "막힌 막장 안쪽", "막장의 열셋 몸이 출구로 걸어간다. 틈으로 새는 등불이 안내"),
 ("B-26", "두 겹 구덩이", "덩어리형", "역병 마흔과 마흔, 위 겹은 해서·아래 겹은 흘림", "석회 구덩이", "두 겹의 글씨체를 달리 그려 위·아래를 가른다(N-A7-4)"),
 ("B-27", "서생 이명의 백", "기록형", "흑월의 몸. 明에서 日이 지워지고 月만 남은 이름", "성문 밖 구덩이", "흙의 글씨: 바닥에 쓰인 이름마다 백이 일어난다. 처결 대기 10초"),
 ("B-28", "벼루 밑의 손", "기록형", "벼루지기가 잊은 시 한 줄 — 옛 짝이 외우고 있었다", "먹 앙금", "먹 앙금에서 손이 올라와 글자를 지운다"),
 ("B-29", "백 년의 사잣밥 할미", "기다림형", "오지 않는 차사를 위해 백 년 상을 차렸다", "아랫목", "차사가 사잣밥을 먹고 짚신을 신어야 눕는다(F69)"),
 ("B-30", "첫 우물 — 어미의 백", "물형", "새끼줄에 매달린 큰 몸. 이름보다 부름이 먼저", "첫 우물 밑", "우물 벽을 따라 내려가며 싸운다. 부름이 백을 눕힌다(F66)"),
 ("B-31", "나의 백", "차사형", "열한 사내와 함께 둑에 오른 열두째 — 나", "물막이 골 소", "사슬 반경 8m. 40명당 일곱의 빛 하나씩(−12%). 처결 대기 15초"),
]
if __name__ == "__main__":
    out = S.svg().replace("시즌 1 보스 콘셉트 시트 — B-02, B-04~B-12 (10종)", "시즌 3 보스(백) 콘셉트 시트 — B-21~B-31 (11종)").replace("B-01 나루 영감은 스프라이트로, B-03 서 의원은 P2-041 로 이미 있음. ", "시즌 3는 혼이 아니라 몸이라 반짝임 없이 두꺼운 흙·물 윤곽. ")
    open(os.path.join(S.OUT, "P2-046-season3-bosses.svg"), "w", encoding="utf-8").write(out); print("ok")
