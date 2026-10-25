# 검은여울 지형 소품 보강 13종 (`tools/art3d/br_extra.py`)
출력 `assets3d/blackrapids/br_x_*.glb`, 미리보기 `assets3d/previews/br_extra_50deg.png`. 규약은 기존 br_* 키트와 같음(원점=바닥 중심, 정면 -Y). 물에 닿는 것은 바닥을 0에 둠(물면 z=0.18 아래로 묻혀도 됨).
- 강이 일하던 흔적: `br_x_net_posts`(그물 말뚝) · `br_x_fish_trap`(통발) · `br_x_washing_stone`(빨래 돌판+흰 옷 대야)
- 사람이 급히 떠난 흔적: `br_x_wrecked_boat`(엎어진 배) · `br_x_drowned_cart`(잠긴 수레) · `br_x_broken_fence`(부러진 울타리) · `br_x_cloth_line`(흰 천 줄) · `br_x_salt_ring`(소금 선+재, 의원이 막으려던 흔적)
- 강이 가져온 것: `br_x_driftwood`(떠내려온 통나무) · `br_x_mossy_boulder`(이끼 낀 큰 돌)
- 살아 있는 것·길잡이: `br_x_heron`(왜가리) · `br_x_dead_reeds`(마른 갈대 무더기, 누렇게 시듦) · `br_x_buoy_lamp`(꺼진 부표 등, 닻줄은 물밑이라 min_z −0.4)
권장 놓기: 수레·부표·그물 말뚝·왜가리는 물가(물 타일 곁 0~2m), 엎어진 배는 나루터에서 먼 모래톱, 소금 선은 의원 집·격리 막 길목, 흰 천 줄은 무덤·격리 막 곁, 이끼 돌·통나무는 여울 가운데 얕은 곳. 배치 좌표는 아직 안 넣음(코드·기획이 정하면 맞춤).
