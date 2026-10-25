# 소리 호출 교차 점검 — 기획·사운드, 2026-10-26 03:00 KST

> 코드 브랜치 `claude/project-thread-ozfksa`(커밋 e19e5dd)를 이 저장소의 소리 목록(`data/sfx_files.json`, 440개)과 맞대어 보았다.
> 다시 돌리기: `python3 tools/sound_call_check.py <코드 브랜치 폴더>` → `data/sound_call_check.json`.
> 코드(.cs) 문자열, `Resources/Data/*.json`(컷신 `sfx`·`audio` 명령 포함), 조합 호출(무기 5종·발소리·장비 등급)을 모두 셌다.

## 한눈에
| | 개수 |
|---|---|
| 만든 소리 | 440 |
| 코드·자료가 부르는 소리 | 250 |
| **불리는데 파일 없는 id** | **0** (곡도 15곡 모두 있음) |
| 만들었지만 안 불리는 소리 | 190 — 아래 |

부르는 쪽에서 빠진 것은 없다. 남은 일은 모두 "만들어 둔 소리를 아직 부르지 않음"이다.

## 만들었지만 안 불리는 소리 — 시즌1 범위(우선, 30개)
### 보스 전투음 (12) — 패턴은 있는데 소리만 안 붙은 것
| 보스 | 소리 | 붙일 자리 |
|---|---|---|
| B-01 나루 | `sfx.boss.naru.rise` | 강물에서 혼 2마리가 올라올 때마다 |
| | `sfx.boss.naru.flood` | ② 맺힘 50%, 바닥이 18m→11m로 좁아지기 시작 |
| | `sfx.boss.naru.bigwater` | ② 얼룩 3개가 모여 큰물귀신이 될 때 |
| B-05 대돌 | `sfx.boss.daedol.number` | 이름을 잊어 번호로 부를 때(맺힘 +30% 병사) |
| B-07 칠성 | `sfx.boss.chilsung.count` | 광부 혼을 한 명씩 내보낼 때 |
| | `sfx.boss.chilsung.rage` | 광부 혼을 파혼해 숫자가 틀렸을 때 |
| B-08 염 | `sfx.boss.yeom.throw` | 숫자 지뢰를 날리는 순간 |
| | `sfx.boss.yeom.burst` | 숫자 칸을 밟아 피해를 입을 때 |
| B-10 선장 | `sfx.boss.seonjang.tilt` | 갑판이 좌우로 기울기 시작할 때마다 |
| | `sfx.boss.seonjang.rope.cut` | 직선 장판 판정이 나갈 때 |
| B-11 왕초 | `sfx.boss.wangcho.rise` | 별명이 불린 무적 혼이 일어나 협공할 때 |
| B-12 흑월 | `sfx.boss.heukwol.line.drain` | ② 줄 위에 있는 동안 반복, 벗어나면 0.2초에 끔 |

### 세계·처음 10분·UI (17)
| 소리 | 붙일 자리 | 메모 |
|---|---|---|
| `sfx.tide.flood` · `amb.tide.ebb` | ⑤ 밀물 신호 / 썰물 때 바닥(`Tide.cs`) | 3막 |
| `sfx.clock.toll` | 월드 시계 큰 시각(동틀 녘 등) | |
| `sfx.danger.enter` | 원념 짙은 구역에 들어설 때 | |
| `amb.weather.rain_light` | 비가 오기 시작·그칠 때 | 지금은 비 = `amb.weather.rain`만 |
| `sfx.ui.click` · `sfx.ui.back` | 버튼·탭 / 취소·창 닫기 | 메뉴·설정·가방 전부 |
| `sfx.card.hover` | 도술 카드에 올림 · 1·2·3 강조 | 카드 나머지 소리는 이미 불림 |
| `sfx.repair.first` | 손보기 성공 | M6 |
| `sfx.reward.bar.open` | 넋 막대·엽전 칸이 처음 나타날 때 | M3 |
| `amb.title.fog` | 타이틀 화면 배경 | 타이틀 곡 `bgm_title`은 이미 불림 |
| `cut.jing` | EL-001 거센 혼 부르기·연출 | `sfx.elite.call`에 같은 징이 들어 있어 급하지 않음 |
| `cut.cough` | B03 등장 컷 "의원이 기침" | 컷신 대본(`cutscenes_s1`/`b01`)의 sfx 칸에 없음 → 서사 대본 쪽 |
| `sfx.ui.rank.up` | (옛) 품계 오름 2.4초 | 승급 연출은 `sfx.rank.seal`로 바뀜 → **안 써도 됨** |
| `sfx.footstep` | (옛) 한 가지 발소리 | 재질별 `sfx.step.*`로 바뀜 → **안 써도 됨** |

(`amb.crow.far`·`amb.river.morning`은 묶음표상 공통이지만 시즌3 장례 소리라 아래 시즌3에 센다. `cut.bones.crumble`도 시즌3.)

## 그 밖(160개) — 아직 들어올 때가 아닌 것
| 묶음 | 개수 | 왜 안 불리나 |
|---|---|---|
| 방금 넘긴 천도 위험·파혼·업·얼룩 | 21 | 이 소리가 든 커밋(c1acd4e, 2a9f680)이 아직 코드 브랜치에 안 들어감. 연결법 `docs/cast-danger-sound.md`, `docs/pahon-karma-sound.md` |
| 시즌2 저승 ⑦~⑩ | 13 | 구역 환경음 9개(`amb.styx.*`·`amb.archive` 등)는 `ZoneAmbient`에 ⑦~⑩ 구역 이름이 아직 없음. 장치음 4개(`sfx.dam.gauge.up`·`sfx.name.slip.catch`·`sfx.clerk.hush` 등)는 장치가 생길 때 |
| 시즌3(6·7·8막) | 126 | `cutscenes_s3`·`funerals_s3`와 소리 대본(`cutscene_audio_s3`·`funeral_audio_s3`)이 아직 `Resources/Data`에 없음. 시즌3 보스·아래층 환경음도 시즌3 코드와 함께 |

## 같이 본 것
- 시즌1·2 컷신 소리 대본은 `cutscenes_s1`(audio 명령 78개)·`cutscenes_s2`(104개)에 잘 녹아 있다.
- 장례 컷(`cutscenes_funerals`)에는 audio 명령이 0개다. 시즌1·2 소리 대본에는 장례가 따로 없어서 맞다. 대본의 sfx 칸만 쓴다.
- 코드가 합성(`SfxSynth`)으로만 내고 파일이 없는 소리: 0개.
