[UI 재료 키트 2차] 생성: tools/art/gen_ui_kit2.py(gen_sprites.py가 부름) → SVG는 assets/sprites_src/ui/, PNG는 assets/sprites/ui/, manifest.json에 크기·피벗·설명 기록. 전체 한눈에: assets/ui/ui_kit2_sheet.png
재료: 밤 남청 판 + 한지 + 먹 + 붉은 인(#B5473F, #E85C41은 주황으로 읽혀 안 씀). 금은 깊은 도술·귀한 것에만. 천도 청록(#5FE3C0)·파혼 주황(#E8683A)은 두 버튼에만.
- 시각 고리: ui_time_ring_frame(512²). 위=자시, 시계방향. 구간 호 각도(위=0°): 동틀녘 81~99°(붉음)·낮 99~225°(한지)·해질녘 225~243°(금)·밤 243~81°(남청). 해·달 표시(ui_marker_sun/moon)는 반지름 228px 위에서 돌린다. 가운데 투명(미니맵 자리).
- 막대: 생명 ui_bar_vital_frame(320×32, 9조각 좌우 16)+ui_bar_vital_fill/ghost(304×16, 홈은 x7~313·y7~25). 맺힘(적 머리 위) ui_bar_gyeol_frame(96×14)·_gold(보스)·_x2(덩어리 두 줄 96×28)+ui_bar_gyeol_fill/ghost(88×8, 홈 x4~92).
- 도술 4칸: ui_skill_slot(기본)·_hot(누름)·_ready(쓸 수 있게 됨, 겹쳐 페이드)·_cool(대기 덮개, Radial360)·ui_skill_key_tab(단축키 쪽지)·ui_skill_bar_plate(줄 바탕, 9조각 32)·ui_skill_pip_{bureum,jul,eolluk}(갈래 점).
- 도술 아이콘 15종(128², 액티브만): icon_skill_bureum_1~5=붙잡아 부르기·혼불 날리기·이름 비추기·배웅길·일곱 이름(깊은) / jul_1~5=휘감기·여럿 끌기·매듭 걸음·한 줄 꿰기·쇠사슬 울(깊은) / eolluk_1~5=터뜨리기·원념 두르기·얼룩 타기·깨진 이름 던지기·검은 갓의 그림자(깊은). 깊은 도술은 금 겹선. 갈래색: 부름 청록·줄 사슬 청백·얼룩 보라. 첫 칸 이름은 '초혼'이 아니라 '붙잡아 부르기'(초혼은 결말 A 전용). 패시브 12종은 아이콘 없음(글씨 목록).
- 버튼: ui_btn_cheondo(길게)·ui_btn_pahon(톡) + 각 _pressed(128²), ui_btn_hold_ring(144², 길게 누르기 홈 — 청록 채움은 코드가 Radial360).
- 명부 책: ui_book_spread(1024×640, 한지 안쪽 여백 약 40px, 가운데 오침 붉은 실) · ui_book_tab / ui_book_tab_active(64×168, 9조각 위아래 28, 오른쪽 끝이 표지에 닿음). 탭 글씨는 코드가 세로쓰기로.
유니티 재생·실제 화면 배치는 미확인(그림 확인만).
