# 서낭당 5곳 외형 + 넋길 혼불 줄 입구

생성: `tools/art3d/seonang_set.py` → `assets3d/props/`, 미리보기 `assets3d/previews/seonang_set_50deg.png`(낮)·`seonang_set_night_50deg.png`(밤). 유니티 복사: `unity/Assets/Resources/Models/Field/`.

## 서낭당 (몸통 자리는 기존 prop_seonangdang와 같아 파일만 바꿔 끼우면 됨)
| 파일 | 구역 | 먼 실루엣 | 가까이 보이는 것 |
|---|---|---|---|
| `prop_seonangdang_solgogae` | ① 솔고개 마을 | 장승 한 쌍 + 금줄 | 제물상(떡·과일·켜진 촛불), 오방색 헝겊 다섯, 황토 마당 |
| `prop_seonangdang_boritdeul` | ② 보릿들 | 솟대 + 장승 하나 | 짚단 둘, 보리 이삭 단지, 노랑·연두 헝겊 |
| `prop_seonangdang_mulmagi` | ③ 물막이 골 어귀 | 높은 이끼 돌탑 + 기운 장승 | 물동이 둘, 소금 무더기, 젖은 마당, 푸른 헝겊 |
| `prop_seonangdang_geomeun` | ④ 검은여울 어귀 | 먹빛 장승 한 쌍 + 흰 재 원 | 가운데 끊긴 금줄, 당집 문에 엇댄 널, 소금 선, 꺼진 촛불, 잿빛 헝겊, 성긴 어두운 잎 |
| `prop_seonangdang_pyedang` | ⑤ 폐당집 어귀 | 잎 없는 고사목 + 쓰러진 장승 | 내려앉은 지붕, 깨진 그릇, 꺼진 향, 혼불 하나(Light_hon_fire) |

- ⑤는 레이아웃에 서낭당 마커가 없어 **아직 배치 안 됨**(폐당집 입구 마커 곁 자리는 코드·기획이 정해 주세요). ①~④는 `field_layout.py`가 이름으로 골라 `field_5x5.json`에 넣었다.
- 밤 불빛: ①은 `Light_seonang_a`(제물상 촛불), ⑤는 `Light_hon_fire`(보라). 나머지는 기존 횃대 불빛만.

## 넋길 입구 (둥근 문·돌 고리 금지, IP 점검)
- `prop_soulpath_gate` (밤, 혼불 켜짐, `Light_hon_gate`) / `prop_soulpath_gate_off` (낮, 불 꺼진 잿빛 한지 등). 말뚝 둘 + 늘어진 새끼줄 + 길이 다른 혼불 다섯, 폭 3.7 m·높이 2.2 m. 문이 아니라 줄이라 그냥 지나간다. 원점=길 한가운데 바닥, 입구는 -Y 쪽.
- `prop_soulpath_lamp` / `_off`: 길 따라 세우는 혼불 등(높이 1.2 m, 1.5~3 m 간격 권장).
- `field_layout.py`가 넋길 정류장 3곳(시작·중간·끝)에 gate를 놓았다. 낮/밤 교체는 코드가 `_off` 파일로 바꿔 끼운다.
