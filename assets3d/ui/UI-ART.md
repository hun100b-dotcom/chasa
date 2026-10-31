# UI 그림 세트 (아트 → 코드팀) — 표준 명세(hud-controls-spec.md v1) 기준

한지·먹 + 단청 금 + 남청 먹판. 규칙: 게임 화면 위에 얹히는 것(막대·칸·버튼)은 **남청 먹판(85%)+금 테두리**, 글을 읽는 곳(대화·퀘스트·알림·지역바)만 **한지**. 주황은 파혼 전용이라 UI에서도 안 씀.
모든 PNG는 1배(명세 px 그대로) + `@2x`(2배) 두 벌. 글자는 그림에 안 넣음(코드가 14~24px, 1px 외곽선). 만든 도구: `tools/art3d/{minimap,map_ui,hud_art,hud_mock,ui_lib}.py`. 목록·크기·9칸 늘이기 값은 `assets3d/ui/ui_manifest.json`. 확인용 시안: `assets3d/previews/hud_mock_{desktop,boss_dialog,phone}.jpg`, `ui_bigmap_mock.jpg`.

## 1. 미니맵 (명세 §2)
| 파일(assets3d/ui/map/) | 내용 |
|---|---|
| `map_field.png` 2048² | 필드 전체(640m) 위에서 본 한지·먹 지도. **북쪽 위, 3.2px/m.** 반경 40m(지름 80m) = 정확히 256px → 미니맵 256 텍스처와 1:1. 30m는 확대·60m는 축소해서 자름. 길(황토)·물(청 먹)·숲(소나무·느티·마른 나무)·보리밭(황금 줄)·비탈(해칭)·집(기와 먹회색/초가 황토)·다리·무덤·바위를 구분. 글자 없음 |
| `map_field_1024.png` | 큰 지도 축소판 |
| `map_labels.png` | 구역 이름 붓글씨(투명). 큰 지도에서만 켬 |
| `map_unexplored.png` | 안 가 본 곳을 덮는 빈 한지. 플레이어가 지난 자리(반경 38m, 가장자리 12m 번짐)를 알파 0으로 지우면 지도가 드러남 |
| `map_meta.json` | 좌표 규칙: `px = x*3.2`, `py = (640 - y)*3.2` (유니티 UV: u=x/640, v=y/640). 구역·표식(서낭당·나루터·굴 등) 좌표 |
| `minimap_frame_round_pc.png` 300² | 둥근 틀. **구멍 지름 260, 투명.** 금 띠+눈금+북쪽 붉은 도장(北). 뒤에 지도를 깔고 `minimap_mask_260.png`(흰 원)로 지도를 둥글게 자름 |
| `minimap_frame_round_phone.png` 240² (+mask_200) | 폰용(구멍 200) |
| `minimap_frame_square_pc.png` | 모서리 둥근 사각 대안(구멍 260) |
| `minimap_icons_atlas.png` + `minimap_icons.json` + `icons/icon_*.png` | 아이콘 19종(64px 칸): me·enemy·elite·boss·soul_fresh/day/old/lump·soul_named·npc·quest·quest_arrow·seonang·exit·cave·bridge·ferry·herb·soulpath. 명세 크기(me 14·enemy 6·elite 8·boss 16·npc 6·서낭당 14)로 줄여 씀. 짙은 먹 테두리가 있어 작게 줄여도 읽힘 |
| `bigmap_frame.png` 1536×864 | 큰 지도 틀(화면 80%). **지도 창 1104×700이 투명하게 뚫림**(왼쪽 위 64,96). 오른쪽 범례 칸(1196,96, 300×700), 위 현판 자리(618,36). `bigmap_title.png`(지도 붓글씨)·`bigmap_legend.png`(범례 카드) 포함 |
| `btn_zoom_in/out`, `btn_close` (hud/) | 큰 지도 버튼 56px |

**명세와 다르게 한 곳(이유 있음)**: ① 정예 적: 명세는 주황 점 → **붉은 점+둘레 가시**(주황=파혼 전용, 색약도 모양으로 구분). ② 보스: 해골 → **붉은 도장 魁**(해골은 아트 금지 목록: 저승사자 클리셰). ③ 일반 적은 붉은 점 그대로. 명세대로 바꾸길 원하면 말해 주세요. 4등급 혼은 색 달리한 물방울(오래된 혼은 갈회색 #6E5446 계열).
구현 팁: ① 미니맵은 UI Toolkit `background-image`=map_field + `-unity-background-image-tint`/UV 사각형(플레이어 좌표 중심 80m)으로 그리면 렌더텍스처 없이 가능. ② 북쪽 고정이므로 지도는 회전하지 않고 `icon_me`만 돌린다. ③ 범위 밖 퀘스트는 `icon_quest_arrow`를 원 테두리에 붙이고 방향으로 회전.

## 2. HUD 조각 (assets3d/ui/hud/, 명세 §1)
| 요소 | 파일 | 크기·사용법 |
|---|---|---|
| 초상 | `portrait_frame` | 88×88, 가운데 72×72 뚫림(초상은 아래에 깔기). 24,24 |
| 체력 | `hp_frame`(288×26) + `hp_fill`(280×18) + `hp_fill_loss`(잔상) | 채움을 틀 안쪽(+4,+4)에 깔고 가로로 잘라 줄임 |
| 기력(도력) | `mp_frame`(288×20) + `mp_fill`(280×12) | 〃 |
| 경험치 | `exp_frame`(774×12) + `exp_fill`(768×6) | 하단 중앙 아래 16px |
| 보스 체력 | `boss_hp_frame`(970×30)+`boss_hp_fill`(960×20)+`boss_hp_loss`+`boss_phase_ticks` | 상단 중앙 위 64px, 이름 24px는 바 위 |
| 스킬 칸 | `slot_normal/ready/selected/disabled`(72×72, 칸 64+그림자) + `slot_cooldown_shade` + `keycap_small`(18×18) | 8칸 간격 8. ready=청록 테두리, 쿨타임은 어둠 판을 시계방향으로 잘라 + 가운데 남은 초 20px |
| 회피 점 | `dodge_pip_full/empty` 12×12 | 스킬바 위 8px |
| 버프 | `buff_frame`, `debuff_frame` 32×32 | 붉은 테두리 = 디버프 |
| 지역명·시각 | `region_time_bar` 260×28 (9칸 12) + `time/time_{sun,dusk,moon,dawn}`(20px) | 미니맵 아래 8px. 낮 7~16·저녁놀 16~19.5·밤 19.5~4.5·새벽 4.5~7(색보정과 같은 구간) |
| 퀘스트·알림·패널 바탕 | `panel_hanji_small`(9칸 16), `panel_hanji`(9칸 24), `quest_title_bar` | 늘려 쓰는 한지 카드 |
| 알림 로그 | `log_row_bg` 420×28 | 오른쪽으로 사라지는 먹 |
| 대화창 | `dialog_box`(9칸 28 → 1152×220), `dialog_name_tab`(9칸, 높이 44), `dialog_next_arrow`, `choice_normal/selected`(9칸 12, 줄 44) | 선택된 줄=붉은 테두리 |
| 지역 진입 알림 | `region_streak` 1000×160(뒤 먹 번짐) + `region_divider` 640×16 | 지역명 40px |
| 키 아이콘 | `key_small` 32×32, `key_wide` 56×32 | `[F] 말 걸기` 앞에 |
| 폰 조작 | `joystick_base` 240, `joystick_knob` 96, `btn_attack` 160, `btn_dodge/interact/skill_blank` 104 | 명세 §5 위치. 손가락 판정은 1.2배 넓게(코드) |
| 커서 | `cursor/cursor_default/attack/talk` 32×32 | 눌리는 점: default(2,2) attack(24,6) talk(8,28) |
9칸 늘이기 값은 manifest 의 `nine_slice_px`. 시안에서 늘린 모습: `hud_mock_*.jpg`.

## 3. 2차 추가(10-25): 도술 아이콘·초상·데미지 숫자
- **도술 아이콘 15종** `hud/skill/icon_{bureum,eolluk,jul}_{1..5}.png` — 기존 128px 아이콘의 옛 틀을 걷어 내고 칸 안쪽 **56×56**(칸 왼쪽 위에서 +4,+4)에 맞춰 둥글게 잘라 1배/@2x(112)로 다시 냄. 5번은 궁극기 → `slot_ultimate`(금빛 테두리 칸)와 함께 쓸 것.
- **차사 초상** `hud/portrait_chasa.png` 72×72(@2x 144): 3D 모델 정면 가슴 위 렌더(밤 색보정). `portrait_frame` 구멍 아래에 깐다. 큰 판 `portrait_chasa_large.png`(288) — 명부(C) 화면용.
- **데미지 숫자 그림 글꼴** `hud/damage/dmg_{normal,crit,taken,heal}.png` + `damage_font.json`: 숫자 0~9와 `, . + - !` 를 가로로 이어 붙인 띠(각 글자 x·폭은 JSON). 일반 28px(흰색)·치명 40px(노랑, 주황 아님)·받은 피해 30px(붉음)·회복 28px(청록). 글자 한 장씩 잘라 이어 붙이고 0.6초 동안 위로 0.8m 뜨며 흐려지게. 한글 낱말 `word_miss`(빗나감)·`word_dodge`(회피). 동적 글자용 TTF는 `assets3d/ui/fonts/BlackHanSans-Regular.ttf`(SIL OFL, 라이선스 같이 둠).

## 4. 확인
- 미니맵 지도는 필드 전체가 한 장이라 2048² 3MB. 모바일 메모리가 걱정이면 1024판(`map_field_1024.png`)을 쓰고 확대 때만 큰 판.
- Unity에서 보인 모습은 미확인. 틀의 구멍(투명)·9칸 늘이기 값이 기대와 다르면 알려 주세요.
- 아직 없음: 버프 아이콘(디버프 종류가 정해지면), 무기별 스킬 아이콘(무기 5계열 도술은 15종 그대로 쓰는지 기획 확인 필요).
