# 2막 ③붉은재·④쇳골 주변 소리 (기획·사운드, 2026-10-26)

> 코드팀용 연결법. 코드 파일은 고치지 않았다. 배치는 `data/act2_soundscape.json`에 있다.

## 무엇이 달라지나
지금 2막은 구역마다 반복 소리 하나뿐이고(ZoneAmbient), 아랫마을·큰 무덤·선탄장은 비어 있다.
1막처럼 **바탕 → 자리 점 소리 → 가끔 섞기** 세 겹으로 채우고, **엿듣기 자리 15곳**에 그 장면의 생활 소리를 붙인다.

- **③ 아랫마을**은 산 사람이 가장 많은 곳이다. 낮엔 빨래 방망이, 도끼, 닭, 술독, 석수의 정 소리가 겹친다. 밤엔 불이 꺼지고 담 너머 기침만 남는다.
- **④ 광부촌**은 쇠·돌·석탄 소리다. 사람 목소리는 늘 멀고 흐리다(번호로 불리는 마을).
- 말뜻이 들리는 목소리는 넣지 않았다. 엿듣기 말은 글자로 나온다.

## 새 소리 37개
| 겹 | id |
|---|---|
| 구역 바탕 6 | `amb.fv.day` · `amb.fv.night`(아랫마을) · `amb.bigtomb` · `amb.sorting.day` · `amb.sorting.night` · `amb.collapse` |
| 서낭당 2 | `amb.seonang.bulgeunjae`(SH2-1) · `amb.seonang.sanshin`(SH2-2) |
| 자리 점 8 | `amb.sooldoga` · `amb.stonemason`(낮) · `amb.village.shrine` · `amb.well.village` · `amb.mokpae.board` · `amb.shaft.timber` · `amb.gukbap` · `amb.mule.stable` |
| 엿듣기 생활 8 | `amb.laundry` · `amb.whetstone` · `amb.lamp.room` · `amb.herb.dig` · `amb.woodcutter` · `amb.peddler` · `amb.grave.tending` · `amb.shift.change` |
| 가끔 13 | `sfx.fv.jar.lid` · `sfx.fv.rooster.near` · `sfx.fortress.stone` · `sfx.fortress.count`(밤, 드묾) · `sfx.arrow.rattle` · `sfx.hawk.far` · `sfx.camp.pole` · `sfx.tomb.cup`(밤) · `sfx.mine.pick.far` · `sfx.mine.cart.far` · `sfx.mine.gong`(교대 시각) · `sfx.mine.rockfall` · `sfx.sorting.basket` |

## 엿듣기 자리 → 생활 소리
| 자리 | 때 | 소리 |
|---|---|---|
| R2-01 아랫마을 마당 | 낮 | 빨래 방망이 `amb.laundry` |
| R2-02 아랫마을 우물 | 저녁 | 두레박 `amb.well.village` |
| R2-03 벌초꾼 집(담 너머) | 저녁 | 낫 가는 쓱싹 `amb.whetstone` |
| R2-04 화살골 어귀 | 낮 | 호미로 약초 캐기 `amb.herb.dig` |
| R2-05 산성 문 | 낮 | 도끼질 `amb.woodcutter` |
| R2-06 이장 집(담 너머) | 밤 | 등잔·명단 종이 `amb.lamp.room` |
| R2-07 남쪽 어귀 | 낮 | 지게 진 장꾼 `amb.peddler` |
| R2-08 작은 무덤 떼 | 낮 | 풀 뜯고 비질 `amb.grave.tending` |
| R2-09 광부촌 어귀 | 새벽 | 교대 광부 발소리·등잔 `amb.shift.change` |
| R2-10 국밥집 | 저녁 | 가마솥·숟가락 `amb.gukbap` |
| R2-11 노새 마구간 | 낮 | 발굽·푸르르 `amb.mule.stable` |
| R2-12 광부촌 우물가 | 저녁 | 우물 + 빨래 |
| R2-13 갱 입구 · R2-15 갱도 골 버팀목 | 낮 | 버팀목 끄응 `amb.shaft.timber` |
| R2-14 순돌 집(담 너머) | 밤 | `amb.lamp.room` |

규칙은 이렇다. 자리가 열려 있고 그 시각일 때만 반경 10m 안에서 반복한다. 엿듣기 문구가 뜨는 동안은 0.6배로 낮춘다. 장례나 업으로 자리가 닫히면 소리도 끈다.

## 붙이는 법 (제안)
1. `ZoneAmbient`가 지금 2막 소리를 고르는 `switch`는 그대로 둔다. `beds`에 값이 있는 구역(아랫마을·큰 무덤·선탄장·무너진 막장)만 바꿔 끼운다. 무너진 막장은 지금의 `amb.mine.shaft` 대신 `amb.collapse`를 쓴다.
2. `points`·`sprinkles`는 1막(`act1_soundscape.json`) 붙이는 코드를 그대로 쓴다. 같은 모양이고, 좌표의 `z`는 act2_map 의 `y`이다.
3. `overhear`는 엿듣기 자리를 그리는 코드(귀 아이콘)가 이미 자리마다 열림을 알고 있으니, 그 자리에 3D 소리 하나를 붙이면 된다.
4. 같은 id가 가까이 두 번 켜지면(R2-02와 우물 점처럼) 하나만 켠다.

## 확인 방법
- 미리듣기 2 페이지의 시연 두 개: 아랫마을 낮 한 바퀴, 광부촌 저녁→갱도.
- 게임에서: 아랫마을 낮은 1막 솔고개 마을보다 바쁘게, 광부촌은 사람 소리가 늘 멀게 들려야 맞다.
