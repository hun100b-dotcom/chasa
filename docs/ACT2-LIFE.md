# 2막 ③ 붉은재 아랫마을 · ④ 쇳골 광부촌 · 들판 생활 소품

원인: 2막 배치표(act2_layout.json 422개)에 아랫마을 집이 0채, 들판은 거의 빈 땅이었다.

## 새 소품 24종 (`tools/art3d/act2_life.py` → `assets3d/act2/a2*_*.glb`, 유니티 `Models/Field/`)
- **a2v_ 아랫마을(붉은 흙벽·돌 얹은 초가)**: `house_sul` 술도가 집 · `house_small` 초가 · `house_herb` 약초 집 · `stone_cutter` 석수 일터 · `persimmon_line` 곶감 줄 · `red_wall_low` 붉은 낮은 담
- **a2m_ 광부촌(널집·쇠찌꺼기·등불)**: `soup_house` 국밥집(Light) · `stable` 마구간 · `mule` 노새 · `owner_house` 광산 주인집(기와) · `coal_stack` 석탄 더미 · `dusty_clothes` 먼지 빨래줄 · `pick_rack` 곡괭이 걸이 · `water_barrel` 물통 · `lamp_string` 등 줄(Light)
- **a2f_ 들판**: `dry_grass` · `red_rock` · `thorn_bush` · `dead_tree` · `boundary_stone` · `persimmon_tree`(붉은재 표지) · `dry_plot` · `cairn_red` · `ore_vein_rock`(쇳골)

## 배치표 (`tools/art3d/place_act2_extra.py` → `assets3d/layouts/act2_extra.json` 650개, `act2_extra_report.json`)
- act2_layout.json **옆에 같이 읽는다**(별도 파일). 형식·좌표·z(땅 높이) 규칙은 같다. 길 3m·장소 중심 비움·겹침 검사·가파른 땅(2m 안 높이차 0.6~1.2 초과)·물 피하기를 지켰고, 못 놓은 것 0, 17개는 옮김(`walk_snap`).
- 마을: 술도가 집·이장 집·약초 집·벌초꾼 집을 지도 장소 점의 북쪽(+y)에 세워 문이 점을 봄 + 빈 집 터 5 + 담 44 + 곶감 줄 2 + 석수 일터.
- 광부촌: 국밥집·마구간+노새·주인집(505,986)·석탄 더미 7·빨래줄·곡괭이 걸이·물통·등 줄 4·움막 4 추가.
- 들판: 마른 풀 260, 붉은 바위 70, 가시덤불 70, 고사목 45, 경계 돌 22, 감나무 28(서쪽), 광맥 바위 30(동쪽), 돌탑 12, 마른 밭 5.
- 코드팀 할 일: `tools/build_field_data.py`가 act2_layout.json처럼 act2_extra.json도 합치기. 소품 수가 늘었으니 먼 것 컬링(LOD) 확인 부탁.

## 로딩 팁
`tools/art3d/loading_tips.py`는 이제 `assets3d/title/loading_tips.json`의 팁 문구(서사·기획이 고친 것)를 그대로 읽어 미리보기(`previews/loading_tips_sheet.jpg`)만 다시 뽑는다(문구를 덮어쓰지 않음).
