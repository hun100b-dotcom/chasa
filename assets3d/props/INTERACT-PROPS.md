# F 상호작용 물건·서낭당 쉬기 자리 모델 + 혼 유형 바닥 예고 그림 (아트 → 코드팀)

기준: planning/data/interactables-act1.md · interactables_act1.json (모델 이름은 그 JSON의 `model` 값과 같다). 만든 도구: `tools/art3d/interactables.py`, `soul_fx_sprites.py`. 미리보기: `assets3d/previews/interactables_50deg.png`, `soul_fx_sprites.png`.

## 1. 모델 (assets3d/props/, 원점=바닥 가운데, 1유닛=1m, 삼각형 100~1,042)
| 모델 | 쓰임 | 크기(m) | 비고 |
|---|---|---|---|
| prop_keep_tongs | K-001 박돌쇠 식은 집게 | 0.7×0.4×0.3 | 돌판 위 쇠집게, 끝에 푸른 서리 |
| prop_keep_bowl | K-002 윤 소사 덮은 밥그릇 | 0.6×0.6×0.4 | 소반 위 뚜껑 덮은 그릇 + 다 탄 초 |
| prop_keep_steamer | K-003 연이 식은 떡시루 | 0.7×0.7×0.75 | 베보자기 덮은 시루, 세 돌 위 |
| prop_keep_lamp | K-006 장 둑지기 꺼진 둑 등잔 | 0.7×0.2×1.3 | 장대 끝 찢어진 종이 등 |
| prop_keep_oar | K-010 곽 뱃꾼 부러진 노 손잡이 | 0.5×0.4×1.2 | 갯벌에 꽂힌 노, 쪼개진 끝 |
| prop_keep_bundle | K-011 막례 젖은 비단 보따리 | 0.8×0.8×0.7 | 남색 보따리 + 물웅덩이 |
| prop_keep_ash | 파혼 뒤 재 | 0.9×0.9×0.1 | 유품 자리에 그대로 갈아 끼움(F 안내 없음) |
| prop_gut_table | B02-D3 폐당집 굿상(단서) | 1.5×0.8×0.85 | 잔 11개 서 있고 열두째 하나만 엎어짐 |
| prop_burnt_docbox | B03-D3 탄 문서함(단서) | 0.9×0.6×0.8 | 뚜껑 열린 그을린 함, 반듯한 한 줄이 그어진 종이 |
| prop_broken_pole | B01-D2 부러진 삿대(단서) | 기존 모델 그대로 | |
| prop_coin_bundle | 엽전 꾸러미 | 0.3×0.3×0.2 | 엽전 9닢 + 짚끈 매듭 |
| prop_herb_mugwort | 쑥 | 0.4×0.4×0.45 | 은빛 초록 잎 포기 |
| prop_seonang_rest | 서낭당 쉬기 자리(F 3m 원) | 지름 5.7 | 돌 두른 마당, 돌 의자 2 + 짚방석, 약탕관 화로, 소원 헝겊 말뚝 3. 광원 빈 오브젝트 `Light_seonang_rest`(따뜻한 #FFB066, 범위 6.5m, 깜박임) |
| fx/fx_pickup_pillar_{white,green,gold,violet} | 줍기 빛기둥 | 높이 2m | 엽전=white, 쑥=green, 장비=등급색(gold 등급 예시·코드가 재질색 변경 가능), violet=예비 |

## 2. 빛 표시(`Glow` 자식 메시)
- 유품 6개 + 단서 물건 2개에는 자식 메시 **`Glow`**(반투명 발광 판+빛 덩이)가 붙어 있다. 유품=보라 #C9B0FF, 단서=금 #D4A94E.
- 코드가 켜고 끄면 된다: 유품은 밤 + 6m 안(규칙 `KEEPSAKE_SHOW_M`)에서만 `Glow` 켜기, 단서는 12m 안에서. 낮엔 모델만. 거리로 알파를 줄이면 더 자연스럽다.
- 파혼 뒤: 모델을 `prop_keep_ash` 로 교체, `Glow` 없음.

## 3. 혼 유형 바닥 예고·충격 그림 (Resources/Sprites/fx/, 같은 파일이 assets3d/fx/sprites/ 에도)
| 파일 | 크기 | 쓰임 |
|---|---|---|
| tele_throw_line.png | 64×512 | 넋두리 던지기 예고. 폭 1m·길이 8m 로 늘려 깐다(아래=던지는 혼). 점선이 위로 흐려짐 + 끝 화살촉. 선딜 0.7s 동안 |
| tele_crack.png | 256² | 묻힌 혼 솟기 예고. 지름 4m(범위 2m). 선딜 0.73s 동안 보라 틈빛이 점점 밝아지게 알파를 올린다 |
| fx_dust_ring.png | 1024×256 | 솟을 때·묻을 때 흙먼지 고리 4프레임(프레임당 0.075s) |
| fx_wonnyeom_hit.png | 1024×256 | 원념 탄 적중 파문 4프레임(0.25s) |
| mote_leader_mark.png | 64² | 대장 잔넋 머리 위 표식(0.35m). 대장을 천도하면 나머지 2초 혼란 규칙의 힌트 |
색은 원념 보라 #B04FD0. 주황 안 씀. 유니티 안 외관은 미검증.
