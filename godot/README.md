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
