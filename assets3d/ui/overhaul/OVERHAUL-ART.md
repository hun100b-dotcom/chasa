# 개편 아트 한 벌 (HUD · 맺힘 금 · 처결 표식 · 예고 장판) — 코드팀용

개편안 P0-2·3·5의 아트 몫. 목록·크기·기준점은 `_manifest.json`, 같은 파일이 `unity/Assets/Resources/Sprites/overhaul/`에도 있다(1배 + @2x, 큰 장판은 1배만).
재현: `python3 tools/art3d/overhaul_ui.py` · `overhaul_tele.py` · 확인판 `overhaul_tele_check.py`(→ assets3d/previews/overhaul_tele_check.png).

## hud/
- `plate_cluster`(9조각 24) 아래 한 덩어리 바탕. `vital_frame/fill/ghost` 체력(채움은 틀 안 4,4).
- 기술 칸 `slot_skill_ready/empty(점선)/cool` 80². **천도·파혼 칸 `slot_tendo_*`/`slot_pahon_*` 80², `_on/_off/_hot`** — 크기 같고 평균 밝기 차 0.05%(측정). 글자(E·R)는 코드.
- `dodge_pip_full/empty` 18² 피하기 점 2개.
## gyeol/ (숫자 대신 맺힘 금)
- 막대 위에 덮는 금: `gyeol_crack_stage1/2/3_L` — 남은 맺힘 66/33/10% 이하일 때 한 장만. 맞은 번쩍 `gyeol_flash_L`. 0이 되면 `gyeol_break_left/right_L`을 벌려 떨어뜨림.
- 맞은 자리 금 표식 `hit_crack_s/m/l/crit`(0.35초, 숫자 대체).
- 보스 맺힘 줄 `boss_gyeol_row_frame/fill/ghost/broken`(960×28, 2~3줄 쌓기, 한 줄 깨면 broken).
## mark/
- `mark_exec_pair`(▲+✕+빈 키캡 2개, 꼬리가 겨눈 혼을 가리킴) / `mark_exec_pahon_only`(덩어리). 연속 천도: `chain_seg`(바닥 1 m 가로 반복)·`chain_seg_weak`(0.2초 남음)·`chain_node`.
## tele/ (모든 적 공격 같은 문법, 1 m = 128 px)
- 모양별 `_border`(스케일 금지, 12 cm 한지 실선) · `_ghost`(0초부터 옅게) · `_fill`(0→1로 키워 안으로 차오름, 기준점은 manifest `pivot`).
- 원 r1.6/2.0/2.5/3.0/3.5 · 부채꼴 90° r2.2(기본 근접)·r1.6(잔넋) · 띠 6×1.6(덮치기) · 선 14×0.6(넋두리). 파혼 범위 `tele2_pahon_r3_0/r4_5`는 주황 점선+톱니, 채움 없음. `tele2_foot` 공격 준비 혼 발밑.
- 채움은 밝은 빗금/어두운 빗금 교대 + 한지 앞가장자리선 → 흑백·적록 색약 시뮬에서도 '찬 정도'가 읽힘(확인판). 판정 0.12초 전 테두리를 흰빛으로 한 번 번쩍(코드).

## 한계·남은 일
- Unity 실기 미확인(스케일·9조각·정렬). 처결 표식 꼬리 위치·키캡 글자 정렬은 코드팀이 한 번 맞춰 볼 것.
- 혼 피격 자세: 3D 동작 Hit1/Hit2/Stagger는 이미 전 혼·보스에 있음(HIT-REACT.md). 이번엔 새로 안 만들었고, "앞모습에서 보이는지" 측정·보강은 다음 스레드 몫.
- 기술 아이콘 다시 그리기, 보스 실루엣 읽기 점검은 개편안의 다른 아트 항목으로 남음.
