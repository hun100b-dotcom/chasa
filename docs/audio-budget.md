# 소리 용량 예산 (웹·폰) — tools/audio_budget.py 가 만든 보고서

효과음 368개 · 곡 47개(임시 대역 포함)를 실제로 변환해 잰 값이다. 다시 재려면 `python3 tools/audio_budget.py`.

## 한눈에

| | 원본(저장소) | 지금 설정으로 구우면(품질 100%) | 권장 설정 — 웹(AAC) | 권장 설정 — 폰 앱(Vorbis) |
|---|---|---|---|---|
| 효과음 | 161MB(wav) | 약 40MB | **12.0MB** | **9.1MB** |
| 음악 | 44MB(ogg) | 약 119MB | **33.3MB** | **33.4MB** |
| 합계 | | 약 159MB | **45.2MB** | **42.4MB** |

## 막별 묶음(처음엔 공통+1막만)

| 묶음 | 효과음 | 곡 | 웹 내려받기(AAC) | 웹 메모리 어림 |
|---|---|---|---|---|
| 공통(처음 화면에서 바로) | 97 | 0 | 1.7MB | 21MB |
| 1막 솔고개 | 49 | 5 | 5.9MB | 29MB |
| 2막 붉은재·쇳골 | 25 | 8 | 5.6MB | 14MB |
| 3막 갯마을·도성(시즌1 끝 포함) | 50 | 13 | 11.5MB | 35MB |
| 시즌2 저승 ⑦~⑩(4·5막) | 39 | 4 | 5.1MB | 14MB |
| 6막 물 밑(시즌3 공통 장치 포함) | 41 | 6 | 4.6MB | 22MB |
| 7막 흙 밑 | 36 | 4 | 3.5MB | 15MB |
| 8막 먹 밑(결말 포함) | 31 | 7 | 7.3MB | 17MB |

**첫 화면에서 받는 소리 = 공통 + 1막 = 약 7.6MB** (지금은 전부 약 159MB를 한 번에).

메모리 어림: 짧은 소리는 브라우저가 풀어서(48kHz, 4바이트) 들고 있고, 반복 환경음·긴 소리·음악은 압축한 채로 든다고 보고 셌다. 한 묶음을 다 불렀을 때의 최대치다.

## 검사 결과

- **클리핑(찢어짐):** 샘플 최고점이 0dB에 닿은 파일 0개. 트루 피크(샘플 사이 최고점)가 −1dB를 넘는 파일 1개: `bgm_solgogae_finish` -0.79dB. 압축하면 넘칠 수 있어 −1dB 아래로 맞출 것(진짜 곡이면 다시 내보내기).
- **음량 편차:** 같은 묶음(카테고리) 안에서 '최대 순간 음량'이 가운데 값보다 6dB 넘게 다른 것. 일부러 그런 것(처결 대기 틱은 작게, 품계 오름은 크게)은 그대로 둔다.

| 묶음 | 개수 | 가운데 값 | 튀는 것 |
|---|---|---|---|
| UI | 12 | -35 LUFS | `sfx.ui.click` -8, `sfx.ui.tab` -7, `sfx.ui.heard.clue` +8, `sfx.ui.rank.up` +14, `sfx.ui.save.auto` -19 |
| 날씨 | 1 | -25 LUFS | — |
| 날씨 반복 | 8 | -38 LUFS | `amb.weather.rain.heavy` +7 |
| 발소리 | 24 | -39 LUFS | — |
| 백의 밤 | 10 | -24 LUFS | — |
| 백의 밤 반복 | 23 | -36 LUFS | `amb.water.rising` +7 |
| 보스 | 80 | -23 LUFS | `sfx.boss.seo.streak` -8, `sfx.boss.seo.weak.close` -9, `sfx.boss.chilseong.count` -8, `sfx.boss.mother.shoe` -6 |
| 보스 반복 | 7 | -29 LUFS | — |
| 세계 | 7 | -23 LUFS | `sfx.bell` +7, `sfx.dog.whine` -7, `amb.market.hush` -15 |
| 세계 반복 | 15 | -36 LUFS | — |
| 저승 | 10 | -24 LUFS | `sfx.clerk.hush` -8, `sfx.map.draw` -6 |
| 저승 반복 | 17 | -36 LUFS | — |
| 전투 | 23 | -27 LUFS | — |
| 처결 | 18 | -17 LUFS | `sfx.wait.tick.fresh` -21, `sfx.wait.tick.year` -16, `sfx.wait.tick.old` -14, `sfx.wait.final` -7 |
| 처결 반복 | 1 | -21 LUFS | — |
| 컷신 | 100 | -26 LUFS | `cut.boat.break` +9, `cut.yoryeong.ring` +8, `cut.cloth.flutter` -7, `cut.drawer` -7, `cut.kids.clap` -6, `cut.ink.grind` -7, `cut.shovel.dig` -6, `cut.lamp.snuff` -8, `cut.kids.steps` -10, `cut.war.drum` +7, `cut.paper.set` -7 |
| 컷신 반복 | 9 | -37 LUFS | `mus.sangyeo.far` +8, `cut.river.rush` +13 |
| 탐색 | 2 | -32 LUFS | `sfx.clue` +13, `sfx.footstep` -13 |
| 탐색 반복 | 1 | -37 LUFS | — |

- **음악 음량:** 탐색 −20 · 전투/처결 −16 LUFS 목표에서 1dB 넘게 벗어난 곡 0개.
