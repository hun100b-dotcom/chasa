# 보스 파혼 결말 소품 9종 (아트)

근거: `docs/narrative/S1-BOSS-ENDINGS-CHECK.md` §3. 만든 곳 `tools/art3d/bossend_props.py`(재생성 `python3 bossend_props.py`), 확인 `bossend_check.py [고도°]` → `assets3d/previews/bossend_props.png`(50°)·`bossend_props_22.png`(22°).
규약: 1 unit = 1 m, 원점 = 바닥 중앙, 정면 −Y, 발광 전용 재질, 주황(#E8683A)은 쓰지 않음(파혼 전용 색).
파일: `assets3d/props/prop_*.glb` = `unity/Assets/Resources/Models/Props/prop_*.glb`(같은 파일).

## 클로즈업 5종(손에 든 물건 확대 연출용)
| 모델 | 보스 | 크기 m(가로×깊이×높이) | 삼각형 |
|---|---|---|---|
| prop_closeup_flagpole | B-05 깃대 조각 | 1.2×0.27×0.13 | 478 |
| prop_closeup_mokpae | B-07 닳은 목패 | 0.22×0.05×0.44 | 224 |
| prop_closeup_ledger_back | B-08 타다 남은 장부 뒷장 | 0.35×0.36×0.01 | 1236 |
| prop_closeup_rope7 | B-10 매듭 일곱 밧줄(한끝은 칼로 벤 매끈한 비스듬한 단면) | 1.59×0.34×0.1 | 1176 |
| prop_closeup_blank_tag | B-11 새기지 않은 나무 조각(아랫부분 진흙에 반쯤 묻힘) | 0.53×0.12×0.37 | 284 |

## 파혼 뒤 낮 흔적 4종(필드 배치용)
| 모델 | 보스 | 크기 m | 삼각형 |
|---|---|---|---|
| prop_trace_banner_up | B-05 성벽에 걸려 반쯤 찢긴 군기(내릴 사람 없음) | 2.0×1.05×3.99 | 264 |
| prop_trace_armor_empty | B-06 빈 갑옷 | 1.4×0.58×2.2 | 500 |
| prop_trace_mokpae_gap | B-07 목패 한 칸 빈 자리(`act2_kit.soegol_mokpae_board`에서 6번 패·표식 뺌) | 2.7×0.7×2.11 | 536 |
| prop_trace_anchor_rope | B-10 밧줄 감긴 닻 드러남 | 3.86×2.23×1.64 | 456 |

## 쓰는 법(코드팀)
- 클로즈업: 파혼 연출 때 카메라 앞 0.6~1 m에 띄워 천천히 돌림(모델은 정면 −Y 기준 보기 좋게 눕힘).
- 흔적: 해당 보스 자리에서 보스가 사라진 뒤 같은 좌표에 낮 배치(`field.json` 항목으로 넣거나 파혼 결말 플래그가 켜졌을 때만 생성).
- 아직 Unity에서 확인 안 함. 위치 좌표는 보스 방 중심 기준으로 코드팀이 정함.
