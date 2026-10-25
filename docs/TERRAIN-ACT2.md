# 2막 지형 데이터 (코드팀 전달용)

생성: `python3 tools/art3d/terrain_act2.py` → `assets3d/terrain_act2/`
미리보기: `assets3d/previews/act2_terrain_map.png` (구역 상자·길·보스 원·서낭당 점)

## 1막과 다른 점
| 항목 | 1막 | 2막 |
|---|---|---|
| 땅 크기 | 640×640 m 정사각 | **768(동서)×640(남북) m 직사각** |
| 원점(남서 모서리) | (0,0) | **origin_m = [0, 640]** (1막 바로 북쪽에 이어 붙음) |
| 높이맵 칸 수 | 641×641 | **769(x)×641(z)** |
| 높이 범위 | — | -1 ~ 14 m |

`terrain.json`에 `origin_m`, `size_x_m`, `size_z_m`, `height_res_x`, `height_res_z`가 들어 있다.
월드 좌표 = 땅 안 좌표 + origin_m. 1막 땅은 그대로 두고 **두 번째 땅(Terrain)을 origin 위치에 하나 더** 놓으면 된다.
행 0 = 남쪽(1막과 같은 규칙).

## 땅 색 층 뜻 (2막용)
같은 파일 이름을 쓰되 뜻이 다르다. 코드는 2막일 때 아래 색을 입히면 된다.
| 파일/채널 | 1막 뜻 | 2막 뜻 |
|---|---|---|
| splat_a R (dirt) | 흙길 | **붉은 흙** (#9A5A3E) |
| splat_a G (grass) | 풀 | **마른 풀** |
| splat_a B (gravel) | 자갈 | **바위** |
| splat_a A (paddy) | 논 | **슬래그·석탄가루** (#2E2C30) |
| splat_b R (leaf) | 낙엽 | **황토** (#A8864E) |
| splat_b G/B | 물거품/젖음 | 쇳골 물막이 근처 젖음(B)만 사용 |

## 확인한 것
- 서낭당·보스 마당 바닥 기울기 ≈ 0 (평평하게 눌러 둠).
- 남쪽 입구 두 곳 (105,640)·(440,640)은 1막 땅 높이(0.3 m)로 이어지게 맞춤.
- 산성 터는 고원(9 m), 쇳골 광산 구역은 계단식 단, 갱도 골은 협곡으로 팠다.

## 부탁
1. 직사각 Terrain 지원 (`size_x_m` ≠ `size_z_m`) 과 origin 오프셋.
2. 2막 splat 색표를 위 표로 바꿔 입히기 (1막 색표 그대로 쓰면 초록 논이 생김).

## 2막 배치표 (act2_layout.json)
- 만드는 법: `python3 tools/art3d/place_act2.py` → `assets3d/layouts/act2_layout.json`(422개), `act2_walk_report.json`(점검 결과).
- 형식은 1막 `act1_extra.json`과 같다(`prop, file, x, y, rot, z`). 차이: **z가 0이 아니다**(terrain_act2 높이를 읽어 바닥을 붙였다). rot = 위에서 볼 때 반시계(Unity yaw = -rot).
- 갱도 골(R2-9)은 `soegol_gol_module`(바닥, 지붕 없음)을 길 따라 이어 붙이고 양옆에 `soegol_canyon_wall`을 세웠다.
- 길 가운데 3 m, 장소·서낭당·보스 마당 중심은 비웠다. 막힌 21곳은 열린 땅으로 옮기고 `walk_snap`(원래 좌표)을 남겼다. 겹침 0, 못 놓은 것 0.
- `by_design:true` 는 일부러 길 위에 둔 것(금줄·산성 문·갱 입구·단서 바위·깃대 조각).
- 코드팀 할 일: `tools/build_field_data.py`가 이 파일도 합치게 하기(1막 act1_extra 블록과 같은 방식, 좌표에 오프셋 불필요 — 이미 필드 절대 좌표).
