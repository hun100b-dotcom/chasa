# 서사 → 코드팀 넘김 (2026-10-26) — 우선순위 순

> 오늘 서사가 낸 코드 할 일을 한곳에 모았다. 근거 문서: `FIRST10-TEXT-PASS2.md`(K) · `S1-DATA-AUDIT.md`(C) · `S1-MYSTERY-PACING.md` §5(M) · `S1-BOSS-ENDINGS-CHECK.md` · `S1-FINALE-PATHS-CHECK.md`.
> 줄 번호는 10-26 기준 `main` 계열 코드. 밀렸으면 "지금 글자"로 찾는다.
> 서사는 `.cs`를 고치지 않았다. 데이터(JSON)는 서사 브랜치에 이미 고쳐 두었다 → 0번만 하면 된다.

---

## 0. 먼저 — 고쳐 둔 데이터 파일 가져오기 (PR #50 병합 전에도 가능)
서사 브랜치 `claude/project-thread-3syw2s`에서 아래 파일만 그대로 덮어쓴다. 코드는 안 바뀐다.
```
git fetch origin claude/project-thread-3syw2s
git checkout origin/claude/project-thread-3syw2s -- unity/Assets/Resources/Data/memory_flat.json unity/Assets/Resources/Data/npc_flat.json unity/Assets/Resources/Data/overhear_flat.json unity/Assets/Resources/Data/item_texts.json unity/Assets/Resources/Data/pattern_texts.json unity/Assets/Resources/Data/cutscenes_s1.json unity/Assets/Resources/Sprites/first10/loading_tips.json unity/Assets/Resources/Data/tutorial_hints.json
```
| 파일 | 왜 |
|---|---|
| `memory_flat.json` | **3막 기억 40개가 통째로 빠져 있었다**(3막 혼·B-09~B-12 천도해도 기억 없음, F23~F30 안 켜짐). 그리고 B-01 이름이 "나루 영감(뱃사공 도씨)"라 코드의 "나루 영감"과 안 맞아 **나루 영감 기억·★F4가 안 나왔다** → 둘 다 고침 |
| `npc_flat.json` | 1막 엿듣기 옛 복사본(업 대체 단서가 넷째 밤에 열리던 옛 규칙, 3막 단서 중복) |
| `overhear_flat.json` | R2-09 시간 0 → 1 |
| `item_texts.json` | 도술 설명 10개 옛 글, 「검은 갓의 그림자」 → 「금 간 그림자」, 새 키 3개 |
| `pattern_texts.json` | 보스 패턴 소리 이름 |
| `cutscenes_s1.json` | 파혼 마지막 장면 5개, `B12-RISE` 새 컷, C-12A 한 줄 |
| `first10/loading_tips.json` | 검은여울 두 줄 최신판, "10초 안에 처결" 숫자 뺌, 처음 하는 사람 눈으로 6줄 다듬음 |
| `tutorial_hints.json` | 처음 5분 안내 8개 다듬음. C 안내 "명부 보기" → "기록 보기"(명세상 C = 인물 창 기록 탭). 키·순서·시간 그대로 |

---

## 1순위 — 지금 화면에 틀린 글이 뜬다

### 1-1. 보통 사람이 추위를 느낌 (세계 이치 위반 — 그의 한기는 당할미만 느낀다)
`NpcWorld.cs:313`
```
지금:  Say("…갑자기 춥네.", s.isObject ? null : s.label);
바꿈:  Say("…그만 들어가세.", s.isObject ? null : s.label);
```
(주석 `Core/ClueBook.cs:6`의 '갑자기 춥네'도 '그만 들어가세'로)

### 1-2. 도술 이름 「검은 갓의 그림자」 → 「금 간 그림자」 ('검은 갓'은 나루 기억의 결정 낱말이라 미리 새면 안 됨)
| 자리 | 지금 | 바꿈 |
|---|---|---|
| `Core/Growth.cs:61` | `new SkillNode("검은 갓의 그림자", ...` | `new SkillNode("금 간 그림자", ...` |
| `Core/Growth.cs:246` | `case "검은 갓의 그림자":` | `case "금 간 그림자":` |
| `JudgeSystem.cs:850` | `case "검은 갓의 그림자":` | `case "금 간 그림자":` |
| 주석 `JudgeSystem.cs:269 · 690`, `Core/Balance.cs:455 · 473` | 검은 갓의 그림자 | 금 간 그림자 |
> 저장 데이터에 옛 이름이 들어 있으면 불러올 때 옛 이름 → 새 이름으로 바꿔 읽는다(`item_texts.json`에 `old_name` 칸이 있다).

### 1-3. 화면에 '동이'(주인공 이름과 겹침) → '날이 밝다'
| 자리 | 지금 | 바꿈 |
|---|---|---|
| `Core/HudState.cs:90` | `"   동이 튼다!"` | `"   날이 밝는다!"` |
| `JudgeSystem.cs:1668` | `"동이 터 무릎 꿇은 혼이 흩어졌다"` | `"날이 밝아 무릎 꿇은 혼이 흩어졌다"` |
| `JudgeSystem.cs:1669` | `"파루 — 동이 튼다"` | `"파루 — 날이 밝는다"` |
| `JudgeSystem.cs:2216` | `"   동이 튼다!"` | `"   날이 밝는다!"` |
| `JudgeSystem.cs:2224` | `"동이 트고 말았다"` | `"날이 밝고 말았다"` |

### 1-4. 첫 죽음 줄 (K1)
`JudgeSystem.cs:1093`
```
지금:  deaths == 1 ? "아직 보낼 이름이 남았다" : ...
바꿈:  deaths == 1 ? "아직 명부에 이름이 남았다" : ...
```

### 1-5. 조사 "을(를)" (T4) — 첫 이름혼부터 보인다
`JudgeSystem.cs:250` `Say(e.label + "을(를) 깨뜨렸다");` · `JudgeSystem.cs:464` `Say(castTarget.label + "을(를) 보냈다");`
```csharp
// 받침이 있으면 "을", 없으면 "를" (한글이 아니면 "을")
static string Eul(string w) { if (string.IsNullOrEmpty(w)) return "을"; char c = w[w.Length - 1]; return (c >= 0xAC00 && c <= 0xD7A3 && (c - 0xAC00) % 28 == 0) ? "를" : "을"; }
// Say(e.label + Eul(e.label) + " 깨뜨렸다");   Say(castTarget.label + Eul(castTarget.label) + " 보냈다");
```

### 1-6. '명부 밖' 안내가 이름혼에게 뜸
`JudgeSystem.cs:1903` — `offledger` 안내("명부 밖 혼 — 기억 없이 넋·엽전만")가 `NamedSoulSpawns.OffLedger`(윤 소사·연이 같은 **장례 대상 이름혼**) 곁에서 뜬다. 이 혼들은 천도하면 기억도 장례도 있다 → 안내가 거짓말이 된다. 조건을 **이름 없는 명부 밖 혼**(`e2.soul.Name == null`)으로 바꾼다(기획 first-5-minutes 4:00 "처음 명부 밖 혼을 처결하면"과 같음).

### 1-7. 품계 알림 (T1)
`JudgeSystem.cs:317` `"품계 " + growth.Rank + "품 — 능력치 +" + ...` → 이 토스트를 지우거나 `"품계 " + growth.Rank + " · 능력치 점수 +" + StatPerRank`로. "2품"은 높은 벼슬로 읽힌다(품계 2 = 종9품).

---

## 2순위 — 추리가 이어지게 (기획 자리 정하기와 같이)

### 2-1. 이름표(label)와 기억 열쇠(name) 나누기 (M5)
- `named_souls*.json` 줄에 `label` 칸을 더한다. 머리 위 이름표·처결 카드에는 `label`, `MemoryLines`(기억 찾기)에는 `name`.
- 지금 `Enemy.MakeNamed(name, ...)`은 name 하나를 둘 다에 쓴다 → `MakeNamed(name, label, kind, wait)`.
- 표: `docs/narrative/soul_labels_s1.json`(107혼, 바뀐 것 7). 예: `"검은 갓의 옛 혼"` → 이름표 `"남의 이름표"`, `"둑에서 건져진 사내"` → `"건져진 사내"`.

### 2-2. 안 세워진 미스터리 혼 63명 세우기 (M1 — 기획이 좌표)
- 지금 세우는 이름혼은 첫 세션·장례 대상 31명뿐. 63명 목록(구역 포함)은 `S1-MYSTERY-PACING.md` §5-3.
- 코드는 `NamedSoulSpawns`가 표만 늘리면 그대로 세운다. 좌표가 오면 `tools/build_named_souls.py`의 PLACES에 넣고 다시 빌드. **1막 22명 먼저.**

### 2-3. S-018 「당할미의 꿈」 이벤트 (M2)
- 추리판 켜진 단서 8개 이상 → 동트기 직전 서낭당, 당할미가 조는 동안 1.5초 "듣기"(천도처럼, 전투 없음). 기억 줄 `"시신이 없으니 상여도 못 메었다. 그래서 이 나무 밑에서 매일 이름을 부른다."` → F8 켜짐. 데이터: `docs/narrative/soul_memories.json` S-018.

### 2-4. 흐린 칸 (M3 — 기획 확인 뒤)
- F2: F4·F8·F28 중 둘이 켜지면 흐리게 켜짐(기획 채택 10-25). F6(제안): F5와 F12가 둘 다 켜지면 흐리게. 흐린 칸도 개수 1로 센다.

### 2-5. 파혼한 이름혼 기록 칸
- 기록(C) 화면의 그 칸: 이름표(label) 아래 `먹이 번져 읽을 수 없다`. 기억·단서 없음.

---

## 3순위 — 연출

### 3-1. 흑월 처결 대기 끝 (B12-RISE)
- B-12가 처결 대기 7초를 다 흘리면(`Soul.TimedOut`) `cuts.Play("B12-RISE")`(1.5초, 대사 0, `cutscenes_s1.json`에 있음).
- 다시 맺힘 0이 되어 `B12-KNEEL`이 또 나오면 t=2.8 말풍선 `"이번엔 내가 기억하마. 불러 보아라."`는 건너뛴다(한 번만).

### 3-2. 선장 폭풍 말풍선 중복 (C10)
`Act2BossArena.cs:88` `judge.Say("폭풍 — 갑판이 더 자주 기운다!", 2f); judge.BossBubble(boss, "붙들어라… 다 붙들어.");` → `judge.PatternEvent("B-10.storm", boss, true, 2);` 한 줄로(같은 글이 두 번 뜰 수 있음).

### 3-3. 보스 꿇은 동안 한마디 연결
- 데이터는 있음, 코드 연결 안 됨: `docs/narrative/boss_kneel_lines.json`(`kneel` 시즌 1, `when`·`count` 규칙). `JudgeSystem.BossBubble`로 띄운다. 보스당 말풍선 3줄 상한은 데이터에서 이미 맞춤.

### 3-4. 파혼 자국 (아트와 같이)
- 파혼 컷 마지막 클로즈업 물건 5개(B-05 깃대 조각 · B-07 닳은 목패 · B-08 장부 뒷장 귀퉁이 · B-10 밧줄 감긴 닻 · B-11 빈 나무 조각)와 낮 풍경 4개(B-05·B-06·B-07·B-10). 글은 `boss_clues_act2/3.json` 각 보스 `pahon` 칸. `S1-BOSS-ENDINGS-CHECK.md` §3.

### 3-5. ▲ · ✕ 글꼴 (K3)
- `NotoSansKR-Subset.ttf`에 ▲ · ✕가 없다. 지금처럼 ↑ · ×를 쓰거나 서브셋에 두 글자를 더한다.
