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

## btn/ (폰 버튼 그림 — PR #56 의 임시 원 버튼 대체, 2026-10-31)
재현: `python3 tools/art3d/overhaul_icons.py` · 확인판 `assets3d/previews/overhaul_icons_check.png`(글자는 확인판에선 깨져 보임, 게임에선 코드가 얹음). 코드는 `TouchControls.Art("이름")`이 `Resources/Sprites/overhaul/btn/<이름>@2x`를 읽고, 없으면 옛 원으로 그린다.
- 물약: `potion_on`(한지 고리·호리병·붉은 인 물약) / `potion_off`(점선 빈 병) / `potion_hot`(눌림, 사방 8px) / `potion_count`(남은 수 글자판).
- 메뉴: `menu_badge`(책 쪽지 56², 초상 오른쪽 아래에 걸침) · `menu_badge_hot`. 눌림 판정은 그대로 초상 위 눈에 안 보이는 원.
- 공격 `atk`(160², 붉은 인 고리·사선 벤 자국 셋·사슬 고리) · `atk_hot`(180²) / 피하기 `dodge`(104², 남청 고리·바람 선). 그림은 위 78%, 아래 22%는 코드가 "공격"·"피하기" 글자.
- 기술 칸 `skill_ring_ready`(금 고리)·`skill_ring_cool`(대기) 104². 도술 아이콘 그림은 아직 없음 → 지금은 기술 이름 글자.
- `swap_hint` 무기 바꾸기 단서 화살표(64×40).
- 색 약속: 천도 청록·파혼 주황은 그 두 칸 전용. 물약은 한지 고리 + 붉은 인(체력과 같은 계열). 모양으로도 구분(호리병 / 벤 자국 / 바람).
- 남음: 도술 아이콘 본체, Q 버튼 무기별 그림(기존 `assets3d/ui/phone/btn_q_*`가 있으나 Resources 에 안 옮겨짐 → 코드팀과 결정), 상호작용 버튼. Unity 실기 미확인.

## skill/ · Q·F 버튼 (PR #57 에서 남은 것, 2026-10-31)
재현: `python3 tools/art3d/overhaul_icons2.py` · 확인판 `assets3d/previews/overhaul_icons2_check.png`. 이름 연결표는 코드 `Core/DosulIcons.cs`(테스트가 "액티브 도술 15개 모두 그림 이름 있음·겹침 없음"을 지킨다).
- 도술 `skill/`(64², 기술 칸 고리 안쪽에 얹음): 부름 `call_grab·wisp·light·path·seven` / 줄 `chain_coil·haul·dash·thread·fence` / 얼룩 `stain_burst·aura·ride·shard·shadow`. 패시브·그림 없는 도술은 `branch_call/chain/stain` 쪽지로 대신.
- 갈래 구분(색약): 금 + ↑삼각 / 은청 + ●점 / 먹자주 + ×. 천도 청록·파혼 주황은 쓰지 않음.
- Q 버튼 `btn/q_chain(끌기)·q_mace(땅울림)·q_bell(부르기)·q_trident(꽂기)·q_brush(이름)·q_slash(베기)` 104². 금 고리 + 무기 도상, 아래 22% 는 코드가 글자(재사용 중엔 남은 초).
- 상호작용 `btn/use`·`use_hot`: 한지 고리 + 손바닥. 옛 `assets3d/ui/phone/btn_f_*` 는 청록 고리(천도 색과 같음)라 대체.
- Unity 실기 미확인: 도술 그림 크기(고리 안 64/104), Q 아래 글자 겹침, F 글자(긴 대상 이름) 길이.
