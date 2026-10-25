# 2막 지역 키트 밑작업 (③ 붉은재 산성 아랫마을 · ④ 쇳골 광산)

지도·배치 자료가 오기 전에 만든 **조각 키트 29종**이다. 지도가 정해지면 이 조각을 그대로 놓는다. 폴더 `assets3d/act2/`, 이름 접두 `sanseong_` / `soegol_`. 다시 만들기: `python3 tools/art3d/act2_kit.py`.

- 규약은 다른 소품과 같다: 1단위=1m, 원점=바닥 한가운데, 정면=-Y(내보내면 +Z), 재질은 색만, 불빛은 발광 면 + `Light_*` 빈 오브젝트.
- 바위·봉분·쇠찌꺼기 더미는 아래쪽이 땅에 반쯤 묻히게 만들었다(그래서 min_z가 음수). 땅 위에 그대로 놓으면 된다.
- 설정 근거: 붉은재=산성 싸움터·큰 무덤(술잔 서른일곱)·화살골 바위틈 부러진 깃대·산성 쉼터(planning/combat/appendix-E), 쇳골=광산·갱도 지름길·광부(등불 모자+곡괭이)(planning/day/appendix-B·C). **지역 분위기는 서사 확인 전**이라 이름·모양은 바뀔 수 있다.

| 이름 | 무엇 | 삼각형 | 크기 m (가로·세로·높이) |
|---|---|---|---|
| sanseong_wall_straight | 성벽 한 칸 | 636 | 4.0×1.08×3.19 |
| sanseong_wall_ruin | 무너진 성벽 | 516 | 3.94×2.21×2.68 |
| sanseong_gate | 산성 문(홍예+문루) | 768 | 6.6×2.8×5.88 |
| sanseong_tower | 망루 | 630 | 4.2×4.2×8.29 |
| sanseong_palisade | 목책 | 384 | 3.16×0.43×2.46 |
| sanseong_banner_torn | 부러진 깃대·찢긴 붉은 깃 | 120 | 1.5×1.0×3.81 |
| sanseong_big_mound | 큰 무덤+술잔 37 | 784 | 5.2×7.54×2.6 |
| sanseong_arrow_field | 화살 꽂힌 땅 | 264 | 1.96×1.73×0.77 |
| sanseong_arrow_rock | 화살골 바위(깃대 조각 단서 자리) | 284 | 4.35×2.93×3.3 |
| sanseong_spear_rack | 창꽂이 | 164 | 1.81×2.26×2.75 |
| sanseong_tent | 군막 | 80 | 3.88×4.97×2.21 |
| sanseong_sul_vat | 술도가 술독 밭 | 474 | 2.63×1.81×1.32 |
| sanseong_stairs | 산길 돌계단 | 144 | 2.8×4.05×2.28 |
| sanseong_beacon | 봉수대(불빛) | 204 | 2.28×2.4×2.75 |
| soegol_mine_entrance | 갱도 입구(등불) | 524 | 8.84×6.21×6.08 |
| soegol_timber_frame | 갱목 문틀 | 88 | 2.4×0.29×2.33 |
| soegol_rail | 광차 레일 3m | 96 | 0.95×3.0×0.14 |
| soegol_cart | 광차 | 380 | 1.06×1.73×1.09 |
| soegol_ore_pile | 광석 더미 | 680 | 1.88×1.59×0.78 |
| soegol_slag_heap | 쇠찌꺼기 더미 | 872 | 3.99×2.98×2.28 |
| soegol_windlass | 도르래 틀 | 180 | 2.16×1.16×3.13 |
| soegol_miner_hut | 광부 움막(등불) | 116 | 3.4×2.96×2.25 |
| soegol_lantern_post | 광부 등불 기둥 | 64 | 0.89×0.5×2.6 |
| soegol_ore_basket | 광석 바구니+곡괭이 | 184 | 0.9×0.76×1.16 |
| soegol_wash_flume | 선광 물길 | 156 | 0.76×4.0×1.0 |
| soegol_smelter | 용광로(불빛) | 392 | 3.63×3.58×4.08 |
| soegol_ingot_stack | 쇳덩이 더미 | 132 | 1.65×0.2×0.36 |
| soegol_rope_fence | 갱 입구 밧줄 울타리 | 148 | 3.23×0.09×1.1 |
| soegol_scree | 붉은 자갈 비탈 | 408 | 3.15×2.84×0.34 |

불빛 마커: `Light_beacon`(봉수대), `Light_mine_lamp`(갱도 입구), `Light_soegol_post`(등불 기둥), `Light_smelter`(용광로, #FF9A4A), `Light_miner_hut`(움막). 색은 따뜻한 등불색 #FFB066(주황은 파혼 전용).

## 다음에 필요한 것 (지도가 오면)
- 땅 색: 붉은재=붉은 흙(#9A5A3E)·젖은 성돌, 쇳골=쇠찌꺼기(#2E2C30)·녹슨 광석·누런 흙(#A8864E). 땅 무늬 그림(detail 타일)·지형 청크는 지도 크기가 정해진 뒤에 만든다.
- 갱도 안 장면용 갱목 문틀을 이어 붙인 통로, 산성 쉼터(B-06) 모양, 산성 아랫마을 집(기존 한옥 키트 재사용 가능).
