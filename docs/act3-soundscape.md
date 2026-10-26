# 3막 ⑤갯마을·⑥도성 주변 소리 (기획·사운드, 2026-10-26)

> 코드팀용 연결법. 배치는 `data/act3_soundscape.json`(2막 `act2_soundscape.json`과 같은 모양). 코드 파일은 고치지 않았다.

## 방향
- **⑤ 갯마을:** 바다가 늘 바닥에 깔린다. 사람 소리는 그물·노·소금 같은 손일 소리다. 밤엔 빈 배들만 부딪는다.
- **⑥ 도성:** 사람이 가장 많은 곳이다. 그래서 오히려 **이름이 안 들린다**(웅얼거림이 두껍고 뜻이 없다).
  저잣거리 → 다리 밑 → 움막촌 → 성문 밖으로 갈수록 사람 소리가 줄고 바람이 커진다(셈 안에서 셈 밖으로).
- 말뜻이 들리는 목소리는 넣지 않았다. 장사꾼 외침도 모음뿐이다.

## 새 소리 35개
| 겹 | id |
|---|---|
| 구역 바탕 6 | `amb.harbor.night` · `amb.waitingrock`(지금 비어 있던 망부석 곶) · `amb.saltfield.night` · `amb.market.night` · `amb.shacks`(움막촌이 다리 밑 소리를 같이 쓰던 것을 따로) · `amb.citygate.day` |
| 서낭당 3 | `amb.seonang.harbor`(SH3-1) · `amb.seonang.market`(SH3-2) · `amb.seonang.bridge`(SH3-3, B-11 뒤) |
| 자리·생활 15 | `amb.net.yard` · `amb.jumak.harbor` · `amb.lighthouse.lamp` · `amb.salt.rake` · `amb.salt.store` · `amb.net.mending` · `amb.cloth.fold` · `amb.rock.waves` · `amb.boat.repair` · `amb.ricecake` · `amb.market.stall` · `amb.bridge.stone` · `amb.jumak.citygate` · `amb.gate.bar` · `amb.gate.queue` |
| 가끔 11 | `sfx.gull.far` · `sfx.net.throw` · `sfx.oar.knock` · `sfx.salt.crack` · `sfx.wave.big` · `sfx.market.call` · `sfx.market.drum` · `sfx.market.scale` · `sfx.shacks.baby` · `sfx.gate.bang` · `sfx.snow.slide` |

2막 소리 중 `amb.well.village`(움막촌 우물)·`amb.lamp.room`(담 너머 밤 방)은 같이 쓴다.

## 엿듣기 자리 → 생활 소리
| 자리 | 때 | 소리 |
|---|---|---|
| R3-01 갯골댁 집 | 저녁 | 그물 깁기 `amb.net.mending` |
| R3-02 소금 창고 | 낮 | 가마니·삽 `amb.salt.store` |
| R3-03 덕보 집(담 너머) | 밤 | `amb.lamp.room` |
| R3-04 순덕 집 | 저녁 | 장롱·혼례 옷 `amb.cloth.fold` |
| R3-05 등대지기 막 | 새벽 | 큰 등잔 `amb.lighthouse.lamp` |
| R3-06 염전 둑 | 낮 | 소금 긁기 `amb.salt.rake` |
| R3-07 여울 북쪽 갯바위 | 낮 | 갯바위 파도 `amb.rock.waves` + 아주 작은 숨비소리 |
| R3-08 포구 어귀 | 낮 | 배 손보기 `amb.boat.repair` |
| R3-09 떡장수 좌판 | 낮 | 떡메·시루 `amb.ricecake` |
| R3-10 문지기 막(담 너머) | 밤 | `amb.lamp.room` |
| R3-11·R3-15 저잣거리 한가운데 | 낮·저녁 | 좌판 `amb.market.stall` (R3-15 땐 광대 장구 간격 절반) |
| R3-12 큰 다리 | 낮 | 돌다리 위 발소리·수레 `amb.bridge.stone` |
| R3-13 움막촌 우물 | 저녁 | `amb.well.village` |
| R3-14 성문 | 새벽 | 문 열리기를 기다리는 줄 `amb.gate.queue` |

## 붙이는 법
2막과 같다(`docs/act2-soundscape.md`).
1. `ZoneAmbient` switch는 그대로 두고, `beds`에 값이 있는 칸만 얹거나 바꾼다.
2. 움막촌(Shacks)은 지금 `amb.bridge.under`를 같이 쓰는데, 이것을 `amb.shacks`로 바꾼다.
3. 망부석 곶(WaitingRock)은 지금 소리가 없으니 `amb.waitingrock`을 새로 넣는다.
