# 3막 키트 1차 — ⑤ 갯마을 (19종, 아트 2026-10-25)
생성: `python3 tools/art3d/act3_kit.py` · 미리보기 `assets3d/previews/act3_harbor_50deg.png` · 크기표 `_report_act3.json`
규약은 2막 키트와 같다(1 m, 원점=바닥 중앙, 정면 -Y, 색만, 불빛은 `Light_*` 빈 오브젝트).

| 묶음 | 모델 |
|---|---|
| 포구 | harbor_pier(선창 4×3), harbor_gauge_post(물때 눈금 말뚝), harbor_boat, harbor_net_frame, harbor_net_pile, harbor_jar, harbor_gaekju_house(객주 집), harbor_inn(주막), harbor_lamp_hut(등대지기 막, 등 14 m) |
| 소금밭 | salt_pan(염전 4×4, 이어 붙임), salt_pile, salt_warehouse, salt_dike |
| 곶 | cape_waiting_rock(7.4 m), cape_hutmyo(헛묘, 마흔둘은 배치에서 변형), cape_new_grave(S-086 새 무덤) |
| 여울 | shoal_wreck(B-10 갑판 7×3.6), shoal_rock(B10-D3), shoal_plank(천도 뒤 갯골 널판) |

메모: 소금 흰색은 따뜻한 #E6E2D6이라 청록 혼불과 구분된다. 썰물·밀물 높이와 배 흔들림은 코드가 움직인다. 다음: 땅(⑤), 큰 다리 분리 모델·⑥ 키트.

## 이름 규칙 모델 (코디 전달 2026-10-25)
| 모델 | 뜻 |
|---|---|
| `bridge_deck` | 큰 다리 상판·난간(8×6 m, 바닥에서 3.6 m). 재질은 **`M_bridge_deck` 하나뿐** → 플레이어가 다리 밑에 들면 이 재질 알파만 낮추면 된다 |
| `bridge_pier` | 다릿발·보·둔치 바닥. 불투명 유지. `bridge_deck`과 원점이 같다(다리 중앙 바닥) |
| `tide_water` | 썰물·밀물 물판 64×64 m(큰 강과 같은 물 재질). 코드가 높이를 25분 주기로 움직임 |
