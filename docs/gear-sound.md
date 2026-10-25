# 장비 장착 · 손보기 소리 — 등급별 (기획·사운드, 2026-10-26)

> 코드팀용 연결법. 코드 파일은 고치지 않았다. 아래는 제안이다.

## 왜 이렇게 나눴나
- **장착 = 몸 + 머리 두 겹.** "무엇을 걸쳤나"(쇠·천·노리개)와 "얼마나 귀한가"(등급)를 따로 만들어 같은 순간에 같이 튼다.
  파일 8개로 15가지 조합이 나온다. 무기를 끼든 갓을 끼든 같은 등급이면 같은 '머리'가 들려서, 귀가 등급을 배운다.
- **흔한 것은 일부러 수수하게.** 모든 장착이 반짝이면 귀한 것이 안 귀하다. 흔한 등급 머리는 낮은 '툭' 하나뿐이다.
- **손보기(강화)는 망치 횟수와 쇠 무게가 등급을 말한다.** 흔한 1번 → 손본 2번 → 귀한 3번(더 무겁게) → 이름 있는 3번(아주 무겁게 + 담금질 치이익 + 징).
  +1→+5 단계는 같은 파일을 높이만 조금씩 올려 튼다. 파일이 늘지 않고, 오를수록 '올라간다'고 들린다.
- 등급 빛깔·순서는 `data/growth.json` rarities 와 같다: 흔한(미색) · 손본(청록) · 귀한(금빛) · 이름 있는(주홍) · 한 벌(옥빛).

## 소리 목록 (17개)
| 때 | id | 소리 |
|---|---|---|
| 장착 몸: 무기 | `sfx.equip.body.metal` | 쇠고리 철컥 + 가죽 끼익 |
| 장착 몸: 갓·도포·띠·신 | `sfx.equip.body.cloth` | 천이 훅 + 끈 사락 + 매듭 톡 |
| 장착 몸: 노리개 | `sfx.equip.body.trinket` | 술 사르르 + 옥 딸깍 |
| 장착 머리: 흔한 | `sfx.equip.tier.common` | 낮은 툭(아주 작게) |
| 장착 머리: 손본 | `sfx.equip.tier.crafted` | 맑은 한 음 |
| 장착 머리: 귀한 | `sfx.equip.tier.rare` | 두 음 화음 + 쉬이— |
| 장착 머리: 이름 있는 | `sfx.equip.tier.named` | 낮은 징 + 물건이 숨 + 세 음 |
| 장착 머리: 한 벌 | `sfx.equip.tier.set` | 옥 편경 두 음 맥놀이 |
| 한 벌 완성 | `sfx.equip.set.complete` | 다섯 음이 쌓여 한 화음 |
| 장비 풀기 | `sfx.equip.remove` | 매듭 풂 + 내려놓는 툭 |
| 손보기: 흔한 | `sfx.enhance.common` | 탕! 1번 |
| 손보기: 손본 | `sfx.enhance.crafted` | 탕! 탕! + 한 음 |
| 손보기: 귀한 | `sfx.enhance.rare` | 무거운 탕 3번 + 금빛 세 음 |
| 손보기: 이름 있는 | `sfx.enhance.named` | 아주 무거운 탕 3번 + 담금질 + 징 |
| 손보기: 한 벌 | `sfx.enhance.set` | 탕 2번 + 옥 두 음 |
| +5 닿음 | `sfx.enhance.max` | 쇠가 길게 노래 + 화덕 불 확 |
| 엽전 모자람 | `sfx.enhance.fail` | 빈 꾸러미 짤랑 + 나무 똑 |

`sfx.repair.first`(첫 손보기)는 그대로 둔다. 처음 10분 M6의 "처음 손봤다" 한 번에만 쓰고, 그 뒤는 위 등급 소리로.

## 붙이는 법 (제안)
1. **등급 → 이름** 한 줄 도우미. 지금 코드의 `Rarity { Common, Crafted, Rare }` + `Named` 기준:
   `string Tier(ItemDef it) => it.Named ? "named" : it.Set ? "set" : it.Rarity == Rarity.Rare ? "rare" : it.Rarity == Rarity.Crafted ? "crafted" : "common";`
   (`Set` 이 아직 없으면 그 부분은 빼도 된다)
2. **몸 이름:** 무기 → `metal`, 노리개 → `trinket`, 나머지(갓·도포·띠·신) → `cloth`.
3. **장착할 때** (`JudgeSystem` 줍기 뒤 `lo.Equip(it)` 이 true 일 때, 그리고 캐릭터 창에서 끼울 때):
   `Sfx.Play("sfx.equip.body." + Body(it)); Sfx.PlayLater("sfx.equip.tier." + Tier(it), 0.06f);`
   못 끼고 줍기만 했으면 지금처럼 `sfx.pickup.gear` 만.
   한 벌 효과가 이번에 켜졌으면 `Sfx.PlayLater("sfx.equip.set.complete", 0.25f);`
4. **풀 때** (`DayScreen` 장비 풀기): `Sfx.Play("sfx.equip.remove");`
5. **손보기 성공** (`DayScreen` 190줄, 지금 `sfx.repair.first`):
   - 처음 한 번만 `sfx.repair.first`, 그 뒤엔
   - `cur.Plus == Balance.ENHANCE_MAX` 이면 `Sfx.Play("sfx.enhance.max")`
   - 아니면 `Sfx.PlayLater("sfx.enhance." + Tier(cur), 0f, 1f + 0.03f * (cur.Plus - 1));` (+1은 원래 높이, +4는 9% 높게)
6. **엽전 모자람** (같은 버튼에서 `Enhance` 가 false): `Sfx.Play("sfx.enhance.fail");`

## 확인 방법
- 미리듣기 페이지 "장비 등급" 칸의 시연 두 개: 등급 다섯을 차례로 장착 / 귀한 무기를 +1→+5 손보기.
- 게임에서: 흔한 장비 장착이 '거의 안 들린다'고 느껴야 맞다. 이름 있는 물건을 꼈을 때만 고개가 돌아가야 한다.
