# 1막 손맛 이펙트 인계 (아트 → 코드)

작성: 아트 스레드, 2026-10-25. 근거: `planning/combat/feel/feel-balance-patch.json`(타격감 권장값), `hud-controls-spec.md` §3-2.

## 1. 새로 만든 그림 (`assets3d/fx/hit/`, 같은 파일을 `unity/Assets/Resources/Sprites/fx/hit/`에도 복사)
가로 띠 PNG, 프레임 256², 투명 배경, 글자 없음. **앞쪽 = 오른쪽(+X)**이라 코드가 때린 방향으로 돌린다. 색 규칙: 주황=파혼 전용 / 보라=원념(적) 전용 / 청백=천도.

| 파일 | 프레임 | 시간 | 언제 · 어디에 |
|---|---|---|---|
| `hit_chain`, `hit_chain_big` | 6 | 0.20 / 0.30초 | 철삭 보통 타 / 3타·견인 명중. 맞은 혼 몸 중심 위 0.3m |
| `hit_mace`, `hit_mace_big` | 6 | 0.20 / 0.30초 | 육모방망이 보통 타 / 3타 내려찍기(반경 3m라 `_big`을 크게) |
| `hit_bell`, `hit_bell_big` | 6 | 0.20 / 0.30초 | 요령방울 울림. 360° 무기라 맞은 혼마다 하나씩 |
| `hit_trident`, `hit_trident_big` | 6 | 0.20 / 0.30초 | 삼지창 찌르기. 관통이라 맞은 혼마다 |
| `hit_brush`, `hit_brush_big` | 6 | 0.20 / 0.30초 | 명부 붓 먹 튐 |
| `hit_flash` | 4 | 0.12초 | 모든 명중 위에 겹치는 흰 점광(적 몸 번쩍 0.09초와 같이) |
| `hit_player_vignette` | 1 | 0.15초 | 차사가 맞았을 때 화면 가장자리 붉은 번쩍(알파 1→0). 가운데는 비어 시야를 안 가린다 |
| `tendo_motes` | 8 | 0.8초 | 천도 완료 슬로모(0.35초) 때 시작, 위로 오르며 사라짐. **흔들림·번쩍 없음** |
| `pahon_ring` | 8 | 0.4초 | 파혼 폭발. 히트스톱 8프레임 동안 첫 프레임에 붙들었다가 풀리며 반경 끝(3.55m)까지 퍼짐 |
| `wait_pulse_fresh/day/old` | 4 | 0.5초 | 처결 대기 남은 2초부터 0.5초마다 맥박(고리 지름 1.8m 기준), 소리 예고와 같이 |

매니페스트 `_manifest_hit.json`, 미리보기 `assets3d/previews/hit_fx_sheet.png`(어두운 땅·밝은 땅), 전후 `hit_fx_before_after.png`.
원칙: **첫 두 프레임이 가장 밝고 크다**(히트스톱 3~6프레임 동안 멈춘 화면에 맞은 모습이 이미 보이게). 화면 흔들림이 작은 타에서 거의 없으므로(권장값 TRAUMA_COMBO1 0.18) 맞은 자리의 이 그림이 손맛을 맡는다.

## 2. 점검 결과: 권장값 대비 현재 코드 (코드 스레드 확인 요청)
`feel-balance-patch.json` 70개 중 `data/balance.json`에 **같은 값 36개 / 다른 값 1개 / 없는 값 33개**.
- 다른 값: `DODGE_DISTANCE` balance 4.0 ↔ 권장 3.2. 단 **구르기 4 m·0.3초·무적 0.2초는 hud-controls-spec §3-2 값이고 구르기 동작(`Roll` 19프레임 = 0.317초, Root 이동 4.0 m)이 이에 맞춰 만들어져 있다.** 3.2로 바꾸면 동작 이동표(`Roll.travel`)를 다시 구워야 하므로 기획이 어느 쪽이 정본인지 정해 주면 맞춘다.
- 없는 값(주요): `COMBO1~3_HITSTOP_FRAMES`, `HITSTOP_MULTI_ADD`, `HITSTOP_VICTIM_SHAKE`, `HITSTOP_ATTACKER_SHAKE`, `SHAKE_MODEL_TRAUMA`, `TRAUMA_*`, `KICK_*`, `KNOCKBACK_TIME`, `WEIGHT_NORMAL`, `WALL_SLAM_*`, `WINDUP_*`(빠른/무거운/보스/시야 밖/터치/번쩍 0.12초), `BUFFER_*`, `CANCEL_*`. 일부는 `Balance.cs`에 상수로 있을 수 있다(예: `HITSTOP_CAP_FRAMES`).
- `WeaponTable.cs` 무기별 히트스톱(프레임): 육모방망이 3/3/6, 요령방울 2/2/5, 삼지창 3/3/6, **명부 붓 1/1/4**. 권장은 1타 3·2타 3·3타 6이라 붓과 방울의 1·2타가 짧다. 붓은 투사체 무기라 1프레임이 의도일 수 있으니 기획 확인 필요.
- 무기 모션 길이는 표와 일치한다(육모방망이 선딜 0.16+휘두름 0.18+후딜 0.22 = 0.56초 ↔ 동작 35프레임 0.567초, 방울 0.517, 삼지창 0.5, 붓 0.433). 달리기는 발 미끄러짐 0.0 mm/프레임이라 손댈 곳이 없다.

## 3. 쓰는 법 (예시)
1. 명중 순간 `hit_<무기>` (3타·견인이면 `_big`)을 맞은 몸 위치에, 때린 방향으로 돌려 깐다. `hit_flash`를 같은 자리에 겹친다.
2. 파혼: 히트스톱 8프레임 동안 `pahon_ring` 첫 프레임 정지 → 풀리며 반경 3.55m까지 확대(0.4초). 화면 흔들림은 파혼에만 크게(TRAUMA_PAHON 0.65).
3. 천도 완료: 슬로모 0.35초(배율 0.5) 시작에 `tendo_motes` 재생. 번쩍 없음.
4. 처결 대기: 남은 2초부터 0.5초마다 `wait_pulse_<fresh|day|old>`.
5. 차사 피격: `hit_player_vignette` 0.15초.
