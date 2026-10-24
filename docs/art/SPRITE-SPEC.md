# 임시 스프라이트 규격 (시연판 "하룻밤 한 판"용)
코드팀과 합의한 형식(2026-10-24). 원본 목록은 `assets/sprites/manifest.json`.

- 투명 PNG, 쿼터뷰 2:1. 타일 128×64, **PPU 128**(Unity Isometric 셀 1×0.5와 일치)
- 피벗은 파일별 pivotX/pivotY(0~1, 아래가 1). 캐릭터·소품은 발/바닥 중심
- Filter Bilinear, 밉맵 끔, 압축 None(임시 단계)
- 좌우는 한쪽만 그려 flipX. `tint:true` 파일은 흰색 원본 → Unity에서 색을 입힌다
- Sorting Layer는 코드팀이 폴더별 배정: Ground(tiles) < Stain < Props(props) < Actors(characters·enemies·boss) < Fx < Hud(hud)
- 다시 뽑기: `python3 tools/art/gen_sprites.py && node tools/art/render_sprites.cjs` (SVG 원본은 assets/sprites_src/)

| 폴더 | 내용 |
|---|---|
| characters | 주인공: idle, walk_a/b, swing(사슬 휘두름), cast(천도), hit |
| enemies | 혼 4종 서 있음 + 갓 죽은·해 넘긴·오래된 혼 무릎 꿇음(덩어리는 무릎 없음) |
| boss | 나루 영감 idle / attack(삿대 휩쓸기 예비동작) |
| tiles | 흙길·마당·풀·논두렁·돌길·징검다리 각 변형 a/b |
| props | 초가집·기와집·돌담·장독대·우물·서낭나무·돌무더기·장승·상여·평상·지게·솟대 |
| hud | 게이지 틀/채움, 처결 타이머 링, 천도·파혼 버튼, 넋·기억·엽전·업 아이콘, 시야 축소 비네트, 기억색 테두리, 밤 시간 바, 패널 |

이 그림은 **임시**다. 최종 에셋은 Higgsfield(MCP 연결 후) 단계에서 같은 파일 이름·피벗으로 교체한다.

## 추가분 (2026-10-24)
| 폴더 | 내용 |
|---|---|
| characters | 육모방망이 3동작 chasa_bang1(치켜들기)·bang2(내리침)·bang3(땅 찍기+충격파 고리) |
| fx | 도술 이펙트 3종 × 3프레임: fx_call_0~2(붙잡아 부르기 6m), fx_bind_0~2(휘감기 4m), fx_burst_0~2(터뜨리기 2.5m). 512×256 바닥 눕힌 타원, 피벗 중앙 |
| icons | 장비 아이콘 3칸(weapon·dopo·noriga) × 3등급(common·crafted·rare) + 이름 있는 물건 월화의 방울, 등급 테두리 frame_common(미색)·crafted(청록)·rare(금빛)·named(주홍) |

맵 배치 시안: `assets/maps/solgogae_village_layout.json`(코드팀이 읽어 배치) + `solgogae_village_preview.png`(확인용). 다시 뽑기: `python3 tools/art/compose_map.py`.

## 카메라 30° 기준 (2026-10-24, 코드팀 질문 대응)
- 타일 128×64px(2:1)은 "수평선 위 30° 내려다봄"일 때 정확히 맞는다. Unity: 카메라 Projection=Orthographic, 회전 X=30, Y=45. (X=45면 마름모가 약 1.4:1로 보여 타일과 어긋난다.)
- 타일 맞물림: Isometric Tilemap Cell Size (1, 0.5), 타일 PPU 128. 바닥 타일은 가장자리까지 꽉 채워 틈이 없게 그렸다(투명 모서리만 마름모 바깥).
- 30°는 앞 물체가 뒤를 더 가리므로 소품 높이 상한: 일반 소품 ≤ 2.5칸(약 160px), 성벽·약장 등 큰 것은 투명도 페이드(앞에 플레이어가 가려질 때 알파 0.5)를 코드팀이 적용.
- 캐릭터·소품은 이미 2:1 기준으로 그려져 있어 그림 수정은 필요 없다. 피벗 변환은 Unity pivotY = 1 − manifest.pivotY.
- 검은여울 지형 바닥색은 palette-tokens.json `검은여울_지형`. 혼 대비 검사 통과값만 사용.

## ② 검은여울 변형 (10종, gen_sprites3.py)
| 파일 | 설명 |
|---|---|
| enemies/soul_{fresh,day,old}_plague, ..._kneel_plague | 역병 사망자 혼. 기본 혼과 같은 크기·피벗, 석회 반점 + 지워진 이름 먹줄. 단계 색은 그대로라 처결 시간(10/7/4초) 판별 유지 |
| hud/gauge_frame_r2, panel_hanji_r2, timer_ring_bg_r2, night_bar_r2 | 지역 HUD 변형. 솔고개 것과 같은 크기·9-slice, 테두리만 석회색. 코드는 지역에 따라 Sprite만 교체 |
덩어리 혼은 지역 변형 없이 그대로 쓴다(보라 + 붉은 점선 고리의 판별성 우선).

## ③ 붉은재 · ④ 쇳골 변형 (gen_sprites3.py, 총 127종)
- enemies/soul_{fresh,day,old}[_kneel]_r3 : 번호 패 + 녹슨 화살(번호 병사). _r4 : 석탄 가루 + 목패(광부). 크기·피벗은 기본 혼과 동일.
- hud/{gauge_frame,panel_hanji,timer_ring_bg}_r3(녹슨 적동 #B0704F) / _r4(놋쇠 #B8A26A). 코드는 지역에 따라 Sprite만 교체.
- 타일·소품 실루엣: assets/concepts/P2-043 (도형 초안, 최종 타일 PNG는 시연판 이후 단계).

## 무기 3계열 (요령·삼지창·명부 붓) — 총 145종
- characters/chasa_{bell,tri,brush}{1,2,3}.png : 예비동작 → 타격 → 마무리 3프레임. 캔버스 320×300, 피벗은 육모방망이와 동일(발 기준). 좌우는 flipX.
- fx/fx_{bell,trident,brush}_{0,1,2}.png : 512×256, 중심 = 공격 기준점. 요령=소리 고리(반경 약 3m), 삼지창=전방 직선 관통, 붓=먹 한 획 부채꼴. 범위 수치는 제안(밸런스 확정 전).
- 성장 UI 시안: assets/ui/growth_*_{pc,phone}.svg (장비 7칸·도술 3갈래·능력·조합). 슬롯 7종과 능력치 목록은 제안, 기획 확정 후 수정.

## 장비 아이콘 (기획서 6절 기준으로 개정, 총 199종)
- 장비 7칸 = 무기(두 벌 바꿔 들기) · 갓 · 도포 · 띠 · 신 · 노리개 2. 철삭은 칸이 아니라 무기 계열. 흑립은 갓 칸의 외형.
- gear/gear_{w_cheolsak,w_bangmangi,w_yoryeong,w_samjichang,w_but,gat,dopo,tti,sin,norigae}_{common,crafted,rare,named,set}.png (96×96, 10종×5등급 = 50). 노리개 2칸은 같은 아이콘 계열을 공유.
- 등급(5): 흔한 common #F3E7D3 / 손본 crafted #4FA8A0 / 귀한 rare #D4A94E / 이름 있는 named #E85C41 / 한 벌 set #C9B0FF. 테두리 icons/frame_{common..named,set}.png.
- 세트 3종 외형(주인공 정면 변형): characters/chasa_set_{wolhwa,miner,heukwol}.png (월화 굿옷 / 광부 / 흑월). 세트 구성 부품 수는 기획 JSON 이후 확정.
- 능력치 4(힘·날램·몸·마음)와 품계 1~50은 UI 시안(assets/ui)에 반영. 도술 27개(3갈래×9)도 반영. 옵션 표·인 조합표 JSON이 오면 문구를 갱신한다.
- 이전 시안의 철삭·흑립·붉은 띠·미투리·인장 슬롯 아이콘(gear_cheolsak 등)은 폐기됨.
