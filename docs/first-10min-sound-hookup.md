# 처음 10분 소리 연결표 (코드팀용) — 기획·사운드, 2026-10-26 새벽

> 근거: `planning/controls/first-10min-benchmark.md`(M1·M3·M4·M6·M7·M8·M9·M10), `planning/combat/first-elite-and-dosul-cards.md`.
> 파일은 모두 `Resources/Audio/Sfx/<id의 점을 밑줄로>.wav`, 목록은 `data/sfx_files.json`. 크기는 파일에 맞춰 두었으니 **재생 볼륨 1.0**.
> `bypass_cast_filter: true`인 것(거센 혼 예고·공격)은 천도 먹먹함 필터를 건너뛴다 — 지금 `Sfx.cs`가 이미 이 값을 읽는다.
> 지금 `Sfx.cs`에는 손대지 않았다. 아래는 어디서 `Sfx.Play("…")`를 부르면 되는지에 대한 제안이다.

## M6 첫 성장 — 품계 인 · 첫 손보기
| 때 | 소리 | 메모 |
|---|---|---|
| 품계가 오르는 연출 시작(명부에 인이 찍힘, 1.0초) | `sfx.rank.seal` | 인이 찍히는 '쿵'은 0.05초, 종은 0.18초에 있다. 화면이 어두워지는 동안 다른 효과음·BGM을 0.6배로 1초 낮추기 |
| (기존) 명부 창에서 품계를 볼 때 | `sfx.ui.rank.up` | 2.4초짜리 옛 소리. 승급 연출에는 `sfx.rank.seal`을 쓴다 |
| 손보기 성공(첫 번째부터) | `sfx.repair.first` | 품계 인과 같은 크기. 금빛 번쩍은 0.82초 |

## M3 처결 보상이 몸으로
| 때 | 소리 | 메모 |
|---|---|---|
| 천도: 혼불 하나가 가슴에 닿기 0.4초 전 | `sfx.reward.honbul` | 혼불이 셋이면 0.08초 간격으로 세 번, 높이 ±3% 무작위(`pitch 0.97~1.03`) |
| 파혼: 엽전이 튀는 순간 | `sfx.reward.coin.pop` | |
| 파혼: 0.6초 뒤 발밑으로 빨려 올 때 | `sfx.reward.coin.gather` | 혼불과 같은 길이·크기(처결 필터 — 둘 다 똑같이 기분 좋게) |
| 넋 막대·엽전 칸이 처음 나타날 때 한 번 | `sfx.reward.bar.open` | |

## M4 장비가 바닥에
| 때 | 소리 | 메모 |
|---|---|---|
| 장비가 떨어지는 순간 | `sfx.drop.land` + 등급 빛줄기 하나 | 둘을 같은 프레임에 |
| 흔한(미색) | `sfx.drop.beam.common` | 한 음. 일부러 작다 |
| 손본(청록) | `sfx.drop.beam.fine` | 두 음. 거센 혼 확정 드롭 |
| 귀한(금빛) | `sfx.drop.beam.rare` | 네 음 화음, 멀리서도 들림 |
| 이름 있는 물건 | `sfx.drop.beam.named` | 낮은 징 + 다섯 음 |
| 줍기(자동·F) | `sfx.pickup.gear` | |

등급이 오를수록 음이 하나씩 늘어난다 → 색을 못 봐도 귀로 구분된다(접근성).

## M9 도술 카드 세 장
| 때 | 소리 | 메모 |
|---|---|---|
| 카드 세 장이 아래에서 올라옴(0.25초) | `sfx.card.rise` | |
| 카드가 앞면으로 뒤집힘 | `sfx.card.flip` | 한 장씩, 0.06초 간격으로 세 번 |
| 카드 위에 올림 / 1·2·3 키로 강조 | `sfx.card.hover` | 아주 작게 |
| 고름 → 0.5초 날아가 박힘 | `sfx.card.pick` | **날기 시작할 때** 재생. 박히는 '꾹'이 0.48초에 있다 |
| 안 고른 두 장이 흩어짐 | `sfx.card.scatter` | |
| 엽전 20 · 다시 | `sfx.card.reroll` | |

## M10 거센 혼 (첫 판: EL-001 두레 좌상 오봉)
| 때 | 소리 | 메모 |
|---|---|---|
| 처음 보일 때(이름 띠 0.6초 펼침) | `sfx.elite.appear` | 같은 순간 BGM 전투층 한 단계 위로 |
| 내려치기 예고 1.2초 | `sfx.elite.slam.telegraph` | 첫 만남은 예고가 1.3배 → `pitch 0.77`로 늘여 재생하거나 그대로 두고 0.36초 늦게 시작 |
| 내려치기 맞는 순간 | `sfx.elite.slam` | 화면 흔들림과 같이 |
| 덮치기 예고 1.0초 | `sfx.elite.pounce.telegraph` | |
| 덮치기 돌진 | `sfx.elite.pounce` | 풀릴 때는 기존 `sfx.swing.*` |
| 부르기(맺힘 50%, 0.8초 울부짖음) | `sfx.elite.call` | 징이 들어 있다(서사 요청 `cut.jing`과 같은 결) |
| 잔넋이 하나씩 일어남 | `sfx.mote.spawn` | 0.15초 간격 셋 |
| 천도 뒤 징채 소품 자리 | (없음) | 소리 없이 둔다 — 징은 이미 울렸다 |
| 파혼할 때 | 기존 파혼 폭발 + `cut.jing.crack` | 폭발과 같은 프레임 |
| (컷·연출용) 들판에 퍼지는 큰 징 | `cut.jing` | 서사 요청. 뒤 구역 거센 혼에도 써도 됨 |

## M7·M8 싸움 끝
| 때 | 소리 | 메모 |
|---|---|---|
| 무리의 마지막 혼이 무릎 꿇는 순간(짧은 슬로) | `sfx.fight.end.slow` | 기존 `sfx.kneel`과 함께. 슬로 동안 다른 효과음에 낮은 쪽 통과 필터(1.5kHz)를 걸면 더 좋다 |
| 무리를 다 처결한 순간 | `sfx.fight.end.jing` | 같은 순간 전투 BGM 층을 2초에 걸쳐 내림 + 한 줄 정리 글 |

## M1 타이틀 화면
| 때 | 소리 | 메모 |
|---|---|---|
| 타이틀이 뜨는 동안 | 곡 `bgm_title`(반복 64초) + 환경음 `amb.title.fog`(반복) | 곡: 진짜 곡 `Audio/BGM/bgm_title` → 없으면 `Audio/BGM/Temp/bgm_title`(지금은 임시 대역). Gemini 지시문 63번 |
| 새로 시작 | `sfx.title.start` | 곡·환경음을 2초에 걸쳐 내리고 C-01로 |
| 이어하기 · 설정 · 끝내기 | `sfx.ui.confirm` / `sfx.ui.click` / `sfx.ui.back` | 기존 소리 |
| 버튼 위에 올림 | `sfx.card.hover` | 같은 종이 결 |

## 용량
새 소리 31개 + 타이틀 곡 1곡. 효과음은 모두 `core` 묶음(어디서나 쓰는 것)이라 첫 화면 내려받기에 들어간다. 다시 잰 값은 `docs/audio-budget.md`.
