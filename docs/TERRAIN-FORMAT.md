# 새 땅 형식 약속 (코드·QA ↔ 아트)

아트가 땅을 새로 깔 때 이 형식으로 주면 코드가 그대로 받는다. 파일이 없으면 옛 8m 타일 땅이 계속 쓰인다.
받는 쪽: `GroundTerrain.cs`(파일·메쉬), `Core/TerrainField.cs`(규칙·테스트), `Resources/Shaders/ChasaTerrainSplat.shader`.

## 폴더 (아트가 `assets3d/terrain/` 에 둔다)
| 파일 | 내용 |
|---|---|
| `terrain.json` | 아래 표 |
| `heightmap.png` | **높낮이 지도.** 16비트를 두 바이트로: R = 큰 바이트, G = 작은 바이트, B 무시, 알파 255. 높이(m) = height_min_m + (R·256+G)/65535 × (height_max_m − height_min_m). 크기 = height_res × height_res (권장 641, 1m 간격) |
| `splat_a.png` | **재질 섞기 지도 A.** R=흙, G=풀, B=자갈, A=논. 크기 splat_res × splat_res (권장 640). 값 0~255 = 비율(합이 꼭 1일 필요 없음, 코드가 합 1로 맞춤. 전부 0이면 풀) |
| `splat_b.png` | 지도 B(선택): R=낙엽. splat_a 와 같은 크기. 없으면 낙엽 0 |
| `layer_dirt/grass/gravel/paddy/leaf.png` | 층별 **이음매 없이 반복되는** 타일 그림(선택, 권장 512²). 없으면 옛 `tiles/tile_*` 그림을 대신 씀(낙엽은 풀 B) |

`terrain.json`
```json
{ "size": 640, "height_res": 641, "splat_res": 640,
  "height_min_m": 0.0, "height_max_m": 8.0,
  "layer_tile_m": [6, 6, 6, 6, 6] }
```
- `size`: 지도가 덮는 한 변(m). 월드 좌표 (x,z) = (0..size) — 블렌더 x, y 가 유니티 x, z (소품 약속과 같음). 지도의 위쪽 줄(행 0)이 z=0.
- `layer_tile_m`: 타일 한 장이 덮는 실제 길이(흙·풀·자갈·논·낙엽 순).
- 시작 지점·서낭당·길목은 급경사 없이 평평하게(기울기 0.3 이하 권장). 주인공은 땅 높이를 따라 걷고, 막힌 곳 판정은 평면(2D)이라 비탈이 길을 막지 못한다.

## 넣는 법 (코드·QA)
```
python3 tools/build_terrain_data.py assets3d/terrain
```
`unity/Assets/Resources/Terrain/*.bytes` 로 복사된다(크기 검사 포함). 시험용: `python3 tools/build_terrain_data.py --demo /tmp/demo_terrain` 로 만든 뒤 위 명령으로 넣으면 완만한 언덕·흙길·논·자갈·낙엽 땅이 나온다.

## 땅 위에 붙는 것
주인공·적·NPC(`GroundSnap`), 필드 소품·집(`FieldManager`, 청크 만들 때 높이 더함), 카메라 초점. 아직 안 붙인 것: 불빛(26개) 높이, 얼룩·그림자 원판, 보스 구역 붉은 바닥 타일(BossArena), 소리(재질별 발소리는 `GroundTerrain.LayerWeights` 로 물을 수 있음).
