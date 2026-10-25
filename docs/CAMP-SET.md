# 외톨이 야영지 소품 10종 + 솔고개 길 생활 소품 8종

생성: `tools/art3d/camp_set.py` → `assets3d/props/prop_camp_*.glb`, `prop_life_*.glb`, 놓는 법 `assets3d/layouts/camp_layouts.json`, 미리보기 `assets3d/previews/camp_set_50deg.png`(낮)·`camp_set_night_50deg.png`(밤). 유니티 복사: `unity/Assets/Resources/Models/Field/`. 원점=바닥 가운데, 정면 -Y.

## 외톨이 야영지 (기획: 20곳 중 7곳, 떨어져 앉은 혼 하나가 무릎 꿇는 자리)
원칙: **한 사람이 쓰던 흔적**만(무리 야영지의 횃불·깃발·무기는 뺌), 바랜 갈색·잿빛, **불빛 없음**(꺼진 자리).
`camp_fire_scar`(꺼진 모닥불 자국, 반경 0.9m) · `camp_mat`(거적 잠자리+짚 베개+헌 이불) · `camp_bundle`(낡은 봇짐) · `camp_lean_to`(거적 가리개 1.8×1.4m) · `camp_pot`(식은 솥+국자) · `camp_shoes`(벗어 둔 짚신+쓰러진 바가지) · `camp_staff`(기댄 지팡이) · `camp_log_seat`(앉던 통나무+쪼갠 장작) · `camp_trace`(먹은 흔적: 씨·낟알·깨진 사발) · `camp_pole_cloth`(헌 헝겊 말뚝)

`camp_layouts.json`에 세 가지 놓는 법(A 바위 곁 / B 거적 가리개 / C 떠난 자리). **혼이 무릎 꿇는 자리 = 원점**, 모닥불 자국은 그 앞(-Y 3m쯤). 일곱 곳에 세 변형을 돌려 쓰면 같아 보이지 않는다. 무리 야영지와 12m 이상 떼어 둔다.

## 솔고개 길 생활 소품 (처음 10분 동선: 시작 위치 → 마을 → 우물 → 보릿들 둑길)
기존 평상·장독대·우물·허수아비·장작더미와 겹치지 않는 것만:
`life_clothesline`(빨랫줄) · `life_water_yoke`(물지게) · `life_chili_mat`(고추 멍석, 짙은 붉은색이라 파혼 주황과 구분) · `life_chicken_coop`(닭장+닭 둘) · `life_pumpkin_fence`(호박 넝쿨 울타리) · `life_meju_rack`(메주 시렁) · `life_jige`(지게+땔나무) · `life_straw_cover`(짚 덮은 장작)
권장: 마을 안 집 곁마다 1~2개(빨랫줄·닭장·메주 시렁은 초가 앞, 고추 멍석은 마당, 호박 울타리는 길가 울타리 대신), 우물가에 물지게, 둑길 입구에 지게+짚 덮은 장작. 배치 좌표는 코드·기획이 `act1_life.json`에 얹는다(아트 쪽 자동 배치는 아직 안 했음).
