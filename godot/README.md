# 차사 단계 0 — Godot판 (엔진 손맛 비교용)

Three.js판(`src/`)을 **숫자 그대로** Godot 4.7로 옮긴 비교용 시험판. 엔진만 바꿨을 때 손맛이 어떻게 달라지는지 보기 위해 만들었다.

| Three.js판 | Godot판 |
|---|---|
| `src/config.ts` | `config.gd` (같은 값, 이름은 `CAMERA.PITCH_DEG` → `CAMERA_PITCH_DEG`) |
| `main.ts` + `stage.ts` + `input.ts` | `main.gd` |
| `player.ts` | `player.gd` |
| `enemy.ts` | `enemy.gd` + `enemy_manager.gd` |
| `chain.ts` | `chain_visual.gd` |
| `effects.ts` | `hit_feel.gd` + `damage_numbers.gd` + `click_marker.gd` |
| (Godot판에만) | `stain_field.gd` — 파혼 뒤 남는 원념 얼룩 |

## 명령어 (Godot 4.7.2)
```
godot --headless --import                                  # 처음 한 번 (클래스 등록)
godot --headless -s res://tests/smoke_test.gd              # 자동 검사 (이동·콤보·히트스톱·견인·20초 안정성)
godot --headless --export-release "Web" build/web/index.html  # 웹 빌드 (템플릿 web_nothreads_release.zip 필요)
```
화면은 전부 코드로 만든다(`main.tscn`은 빈 껍데기). 에디터를 열지 않고도 AI가 수정·검증할 수 있게 하기 위해서다.

## Three.js판과 다른 점 (의도한 것만)
- 왼쪽 위 조작 안내 한 줄(영문 — 기본 글꼴에 한글이 없음).
- 조명 세기는 눈으로 비슷하게 맞춤(엔진마다 빛 계산식이 달라 같은 숫자를 넣으면 밝기가 달라진다).
- 적 클릭 판정: 물리 엔진 대신 "광선–원기둥 거리"로 계산(결과는 같음).

## 핵심 루프 (2026-10-24 추가, COMBAT-SPEC 1-1~1-4)
Three.js판에는 없다. 수치는 전부 `config.gd` 11번 칸(스펙 ID 그대로).

| 조작 (PC) | 폰 | 하는 일 |
|---|---|---|
| 좌클릭 바닥 / 적 | 탭 | 이동 / 콤보 |
| Q · 우클릭 | PULL 버튼 | 견인 |
| Space | SWING 버튼 | 제자리 휘두르기 |
| 무릎 꿇은 혼을 **길게 누름** · E | SEND 버튼 | 천도 (1.5초, 5초 안에 이어 하면 0.8초) |
| 무릎 꿇은 혼을 **짧게 클릭** · R | SHATTER 버튼 | 파혼 (즉시 폭발, 얼룩 남음) |

- 적: 2초마다 공격(예비동작 0.4초 동안 빨갛게 부풀면 피할 수 있음), 맞으면 12.
- 맺힘 0 → 무릎 꿇고 처결 대기. 머리 위 막대 색 = 혼 종류(하늘 갓 죽은 10초 / 노랑 해 넘긴 7초 / 주황 오래된 4초 / 보라 덩어리 = 천도 불가).
- 천도 중엔 시야가 60%로 좁아지고 가장자리가 '생전 기억' 색으로 물든다. 맞으면 끊긴다.
- 파혼 얼룩: 밟으면 -20% 속도, 3개 겹치면 사나운 적(+50%) 소환.
- **임시 해석(스펙 공백):** W-005 대기 시간 초과 → 맺힘 50%로 다시 일어남 / T-008 캐스팅 중 피격 → 중단 / K-004 미구현 / 플레이어 체력 100.
