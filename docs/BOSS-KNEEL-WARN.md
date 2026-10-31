# 보스 꿇음 압박 바닥 경고 점검 (아트)

폰 24 m·처결 대기 고리 겹침·천도 먹 가장자리 아래에서도 "어디가 위험한지" 읽히게 하는 경고 그림 세트. 확인 그림: `assets3d/previews/boss_warn_check.png`(위 PC, 아래 폰 크기 ×0.41).

## 점검 결과
- 기존 경고(원·띠·칸·부채꼴·직선)는 테두리가 5.9 cm → 폰 24 m에서 0.26 mm라 고리·먹에 묻힘. **새 `_L` 테두리 12 cm(+먹선)로 0.54 mm**, 3장면 모두 먹 가장자리 걸친 곳까지 읽힘.
- 기존에 없던 것: 안전 칸·띠, 낙석 그림자, 갑판 화살, 물 혼 자리, 거적 무늬. 전부 새로 제작.
- 주의: 빨강 35% 채움이 대기 고리를 덮으면 고리가 흐려짐 → **고리를 채움 위에 그릴 것**(테두리는 맨 위).

## 압박 ↔ 그림 (`Sprites/boss_warn/`, 1 m = 128 px, 코드는 월드 크기÷그림 크기로 스케일)
| 압박 | 그림 |
|---|---|
| B-03 낙인 파동 12칸(+안전 1칸) | warn_cell_border_L + warn_cell_fill_red, 안전 칸은 warn_safe_cell |
| B-06 호령 대형(틈 칸) | 위와 같음, 틈 칸 = warn_safe_cell |
| B-07 낙석 3곳 | warn_rock_border_L + warn_rock_fill, 내 발밑 하나는 warn_rock_border_you_L |
| B-09 파도 줄(안전 띠) | warn_band_border_L + warn_band_fill_red, 안전 구간 warn_safe_band |
| B-11 거적(r 3 m, 0.8초) | warn_circle_border_L + warn_mat_fill (scale 6/5) |
| B-10 갑판 기울기 | warn_deck_arrow_border_L + warn_deck_arrow_fill (미끄러지는 방향으로 회전, 화살 한 겹씩 켜기) |
| B-01 물 혼 두 번 | warn_spawn (배 양옆 3 m) |
| B-08 염씨 숫자 4장 | 기존 칸/원 재사용(_L) |

규칙: 위험 = 한지색 **실선** + 빨강 #E85C41 35%, 안전 = 한지색 **점선** + 옥색 38%(색 못 봐도 구분). 주황 채움 없음. 채움은 코드가 바깥→안으로 차오르게 마스크. 예고 ≈1.0초.
재현: `python3 tools/art3d/boss_kneel_warn.py`, 점검 `python3 tools/art3d/boss_warn_check.py`.
재측정(옥색 38%): 안전 칸은 24 m 폰에서 선명. 안전 띠는 빨강 채움 위에 겹쳐 놓으면 점선 테두리만 남아 약함 → **안전 구간을 빨강 채움 뒤가 아니라 위에 그릴 것**. Unity 실기 미확인.
