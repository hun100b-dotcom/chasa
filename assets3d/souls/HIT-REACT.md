# 맞는 쪽 손맛 동작 (혼 7종 · 보스 3종) — 코드팀용

대상: 혼 4등급(soul_<등급>, 지역 변형 12종 포함) + 3유형(wail·mote·buried ×4등급) / 보스 나루(boss_naru), 월화(b02), 서 의원(b03). 파편 이펙트 fx/fx_hon_shards.glb.
공통 동작 이름: **Hit1 · Hit2 · Stagger · Kneel · Tendo · Pahon** (혼과 보스 모두 같은 이름). 60fps.

## 약속
1. 위치는 코드 넉백이 담당(KNOCKBACK_TIME 0.2초). 동작은 눌림·젖힘만 그려서 이중으로 밀리지 않는다.
2. **0번 프레임 = 히트스톱에 멈춰 보일 '맞은 직후' 자세**(최대의 35~50%). 맞은 순간 이 클립을 처음부터 재생하고, 히트스톱 동안 정지하면 맞은 모양이 보인 채로 멈춘다.
3. 흰 번쩍(ENEMY_FLASH_TIME 0.09초)은 코드 재질 처리.

## 어느 타에 무엇을 (feel-balance-patch 값 기준 제안)
| 맞은 것 | 히트스톱 | 넉백 | 재생 |
|---|---|---|---|
| 철삭 1타 | 3f | 1.0 m | **Hit1** (10f, 최대 f2) |
| 2타 · 견인 | 3f · 4f | 1.3 m | **Hit2** (16f, 최대 f3, 되튐 f7) |
| 3타 · 파혼 명중(죽지 않은 적) | 6f · 8f | 3.5 m · 3.0 m | **Stagger** (30f, 최대 f4, 흔들림 f9·14·19·24) |
| 맺힘 0 | +2f(KILL_BONUS) | 1.5배(KILL_KNOCKBACK) | **Kneel** (36f), 쿵 f14(먼지·소리), 끝 자세 유지 |
| 천도 완료 | 슬로모 0.35초 | 없음 | **Tendo** 48f: 일어남 f10 → 밝아짐 f24 → 빛 알갱이 폭발 f36 → 숨김 f47 |
| 파혼으로 처치 | 8f | 없음 | **Pahon** 18f: 금 f5 → 터짐 f9(**fx_hon_shards Burst 시작**) → 숨김 f13 |

Hit 클립은 겹쳐 맞으면 다시 처음부터 재생(마지막 맞은 것 우선). 3마리 이상 한꺼번에 맞아도 각자 같은 클립.
Tendo/Pahon은 Kneel 끝 자세에서 이어지도록 만들었다(Kneel→Tendo/Pahon은 크로스페이드 없이 바로 재생해도 된다).

## 보스
- 나루: Hit1 10f / Hit2 18f / Stagger 36f / Kneel 60f(+KneelHold 120f 반복) / Tendo 210f(일어나 삿대를 눕히고 깊이 숙여 흩어짐, dissolve=210) / Pahon 120f. 배가 같이 출렁인다.
- 월화·서 의원: 기존 Kneel·Tendo·Pahon·Hurt는 그대로(긴 연출), Hit1 10f / Hit2 18f / Stagger 36f 추가.
- 보스는 무거우니 **넉백 0 권장**(Hit2/Stagger도 제자리). 기존 Hurt는 호환용으로 남김.

## 파편 fx_hon_shards.glb
주황(파혼 전용색) 조각 14개, 동작 Burst 40f 한 번(끝 f40 숨김). 혼 위치에 놓고 shatter 프레임에 재생. 큰 혼(lump) 1.3배·잔넋 0.6배 크기만 바꿔 쓰면 된다.

## 다시 만들기
python3 tools/art3d/soul_anim.py / soul_types.py / naru_anim.py / boss_b02_b03.py / fx_hon_shards.py. 동작 정의는 hit_react.py 한 곳.
