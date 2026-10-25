# 3막 보스 모델 (아트 2026-10-25) — 1차: B-12 흑월
생성: `python3 tools/art3d/boss_act3.py [--sheets]` · 미리보기 `assets3d/previews/bosses_act3_50deg.png`, 동작 시트 `anim_boss_b12_heugwol_*.png` · 동작표 `_act3_anim_manifest.json`

| 파일 | 설명 |
|---|---|
| `boss_b12_heugwol.glb` | 흑월 차사 2.25 m(삼각형 1368). 주인공과 같은 실루엣(검은 갓·검은 도포·사슬)을 닮되 키가 크고 야위었다. 붉게 빛나는 눈, 갓에 초승달 장식, 오른손 끌리는 사슬, 왼손 명부(이름 자리가 먹으로 지워짐), 허공에 도는 찢긴 명부 쪽 일곱(Prop 뼈), 어깨·갓에 쌓인 눈 |

- 뼈 9개(Root/Hips/Chest/Head/UpperArm.L·R/Hand.L·R/Prop), 동작 10개(Idle/Windup 40f/Attack 24f(명중 f6)/Hit1/Hit2/Stagger/Kneel/KneelHold/Tendo/Pahon). 이름·길이는 1막·2막 보스와 같다 → 코드 연결 그대로.
- **1차(B-04, ① 무덤골)에도 같은 모델을 써 달라**(코디 요청). 눈 조각 노드 이름이 `snow_sh*`, `brim_snow`이니 1차에서 거슬리면 이 노드만 끄면 된다.
- 눈의 붉은 빛은 발광 재질만이다(Light 마커 없음). 필요하면 Head 뼈 (0,-0.14,1.87)에 붉은 점광원을 코드가 달 것.
- 다음: B-09 망부석 아낙, B-10 만선호 선장, B-11 다리 밑 왕초.
