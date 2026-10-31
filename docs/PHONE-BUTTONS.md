# 폰 버튼 그림 (화면 명세 v1.8 §5) — 아트

위치: `Resources/Sprites/ui/phone/` (assets3d/ui/phone/ 에도), 전부 1배 + @2x. 크기는 1080p 기준 픽셀. 확인판(컬러·흑백) `_phone_buttons_check.png`.

| 파일 | 크기 | 쓰는 곳 |
|---|---|---|
| btn_tendo_136 / _pressed | 136 | 천도 ▲. 처결할 혼이 있을 때만 0.15초에 뜸. 누르고 있기 = 시전 |
| btn_tendo_ring_fill / _ring_track | 136 | 시전 진행 고리. track 위에 fill을 Image Filled Radial360(12시부터 시계방향)으로 채움. 연속 천도는 절반 찬 채 시작. 맞아서 끊기면 fill을 #E85C41로 한 번 틴트 |
| btn_pahon_136 / _pressed | 136 | 파혼 ✕. 톡 = 파혼, 삼지창이면 끌기 = 방향 조준 |
| btn_pahon_chain_ring | 152(✕ 136 위에 가운데 맞춰 겹침) | 업 30 연쇄 고리. 파혼 직후 1초 동안 Filled Radial360이 줄어듦. 대상 없으면 안 띄움 |
| mark_chain_target | 48 | 연쇄 대상(4 m 안 다음 꿇은 혼) 머리 위 표시 |
| btn_q_frame_104 + q_glyph_{pin,call,brush,chain,club} / btn_q_{pin,call,brush,chain,club}_104 | 104 / 64 | 무기 기술 Q(삼지창 꽂아 버티기·요령 불러 세우기·붓 이름 쓰기·철삭·육모방망이 손에 익음). 완성본이 있으니 틀+그림 합치기는 선택. 재사용 중은 코드가 어둡게 + 남은 초 |
| q_dot_on / q_dot_off | 16 | 붓 표식 먹점 ●●● (Q 위) |
| btn_f_frame_104, f_glyph_lamp, btn_f_lamp_104 | 104 | F 자리 등잔 버튼(밤·오늘 안 켬·둘레 대상 없을 때) |
| btn_f_hold_ring | 104 | F 길게 누르기 0.5초 진행 고리 |
| preview_line_6x2 | 768×256 | 삼지창 ✕ 끌기 직선 미리보기. 바닥에 눕힘, 1 m = 128 px, 앞(+x). 6 m × 2 m(가로 6 m 늘리면 스케일 1) |

규칙: 천도·파혼은 크기·밝기 비슷(정답 표시 금지). **흑백에서도 구별**: ▲ = 솟는 불꽃 + 매끈한 실선 고리, ✕ = 사방으로 벌어진 깨진 팔 + 점선 고리 + 바깥 톱니. 측정(글리프 겹침 IoU 0.14, 테두리 밝기 변화 매끈 ↔ 톱니 점선 큼)과 흑백 비교판으로 확인. 미리보기 선은 주황 점선(파혼 색)이라 위험 예고(빨강 실선)와 구분.
무기 5계열 Q 그림 모두 있음(철삭·삼지창·요령·붓·육모방망이).
한계: Unity 실기 미확인. 폰 실물 터치 확인(T7)은 코드·QA.
재현: `python3 tools/art3d/phone_buttons.py`
