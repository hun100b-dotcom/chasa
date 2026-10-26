# 보스 새 패턴·숫자 혼 소리 + 1막 보스 BGM 길이 점검 (기획·사운드, 2026-10-26 KST)

> 이 문서는 "어디서 무슨 소리를 틀지"만 정한다. 코드(JudgeSystem·BossArena·BgmPlayer)와
> 서사 파일(pattern_texts.json)은 기획·사운드가 직접 고치지 않는다 → 아래 표대로 각 팀이 반영.

## 1. 점검 결과 한눈에

| 자리 | 지금 | 문제 | 고침 |
|---|---|---|---|
| B-01 나루 `bigwater`(큰물 시작) | sfx.boss.naru.bigwater | 이 소리는 원래 "얼룩 셋이 모여 물기둥" 소리 | → **sfx.boss.naru.flood** (강이 불어 바닥을 삼키는 3초) |
| B-01 `flood`(큰물 중 4초마다 밀기) | sfx.boss.naru.flood (3초) | 3초짜리가 4초마다 겹쳐 울림 | → **sfx.boss.naru.current** (새, 1.2초 물살 밀기) |
| B-01 `stain_merge`(얼룩 합침) | 없음 | 소리 없음 | → **sfx.boss.naru.bigwater** (원래 이 자리 소리) |
| B-01 큰물 동안 바닥 | 없음 | 큰물 내내 조용 | → **amb.boss.naru.highwater** (새, 반복, 큰물 끝나면 1초 페이드) |
| B-01 `weak_tilt`(약점: 기울어짐) | 없음 | 약점 열려도 알 수 없음 | → **sfx.boss.naru.weak** (새, 매번) |
| B-10 선장 `storm`(폭풍 2단계) | 없음 | tilt 를 두 번 틀어 대신함 | → **sfx.boss.seonjang.storm** (새) + **amb.boss.seonjang.storm** (새, 2단계 내내 반복). tilt 의 sfxTimes 는 1로 |
| B-10 줄 끝 생김(SpawnRopeEnd) | 없음 | 줄이 떨어진 걸 모름 | → **sfx.boss.seonjang.rope.slack** (새) |
| B-10 `weak_rope`(줄 끌기 성공) | 없음 | 가장 큰 순간이 조용 | → **sfx.boss.seonjang.rope.pull** (새) 먼저, 0.35초 뒤 **sfx.boss.seonjang.fall** (새, 선장 넘어짐) |
| 약점 열린 동안 맞힐 때(damageTakenMult > 1) | 평소 타격음만 | 약점 친 손맛이 같음 | 평소 타격음 위에 **sfx.boss.weak.hit** (새) 한 겹 더 |
| 숫자 혼 무릎 꿇음 | 평소 무릎음만 | 숫자 혼만의 표시 없음 | 평소 무릎음 위에 **sfx.soul.numbered.mark** (새) |
| 숫자 혼 기다림 틱(JudgeSystem 1015줄 근처) | fresh/year/old 중 하나 | 숫자 혼 구분 없음 | Soul.Numbered 면 **sfx.wait.tick.numbered** (새, 주판알 딸깍) |
| 숫자 혼 천도 | 평소 천도음만 | — | 평소 천도음 끝에 **sfx.soul.numbered.release** (새, 3초 장부 덮임) |
| 파혼 "남은 장부" 엽전 보너스 | 평소 엽전음 | 보너스인 줄 모름 | 엽전음 0.2초 뒤 **sfx.pahon.ledger** (새) |

새 소리 13개는 `tools/sfx_render.py` 맨 아래 블록, 파일은 `unity/Assets/Resources/Audio/Sfx/`.
`data/sfx_files.json` 에도 올라가 있어 이름으로 바로 부를 수 있다.

## 2. 서사팀에 부탁 (pattern_texts.json 의 sfx 칸만)

```
B-01.bigwater    sfx: sfx.boss.naru.flood
B-01.flood       sfx: sfx.boss.naru.current
B-01.stain_merge sfx: sfx.boss.naru.bigwater
B-01.weak_tilt   sfx: sfx.boss.naru.weak
B-10.storm       sfx: sfx.boss.seonjang.storm
B-10.weak_rope   sfx: sfx.boss.seonjang.rope.pull
```

## 3. 코드팀에 부탁 (붙일 자리)

```csharp
// (1) 나루 큰물 바닥: 큰물 시작에 반복 소리를 켜고, 끝나면 1초에 걸쳐 끈다
//     (왜) 큰물 동안 "물이 차 있다"는 걸 눈 말고 귀로도 알게
Sfx.Loop("amb.boss.naru.highwater", on: bigWaterActive, fade: 1f);

// (2) 선장 폭풍 2단계: 폭풍 시작에 한 번 + 2단계 끝날 때까지 반복
Sfx.Loop("amb.boss.seonjang.storm", on: phase2, fade: 1.5f);

// (3) 줄 끝이 바닥에 떨어질 때(SpawnRopeEnd 안)
Sfx.Play("sfx.boss.seonjang.rope.slack", ropeEndPos);

// (4) 줄 끌기 성공: 끄는 소리 → 0.35초 뒤 선장 넘어지는 소리
Sfx.Play("sfx.boss.seonjang.rope.pull", player.Pos);
Sfx.PlayDelayed("sfx.boss.seonjang.fall", boss.Pos, 0.35f);

// (5) 약점 열린 동안 맞힘: 평소 타격음은 그대로 두고 한 겹 더
if (boss.damageTakenMult > 1f) Sfx.Play("sfx.boss.weak.hit", hitPos);

// (6) 숫자 혼
if (soul.Numbered) Sfx.Play("sfx.soul.numbered.mark", pos);          // 무릎 꿇을 때(평소 무릎음 다음)
string tick = soul.Numbered ? "sfx.wait.tick.numbered" : 기존틱;      // 기다림 틱 고르는 곳
if (soul.Numbered) Sfx.Play("sfx.soul.numbered.release", pos);       // 천도 끝날 때

// (7) 파혼 남은 장부 보너스
if (ledgerBonus > 0) Sfx.PlayDelayed("sfx.pahon.ledger", pos, 0.2f);
```

`Sfx.Loop`·`Sfx.PlayDelayed` 가 없으면 지금 쓰는 방식(AudioSource 하나 붙여 켜고 끄기, 코루틴)으로 같은 뜻만 맞추면 된다.

## 4. 1막 보스 BGM 길이 점검

| | 값 |
|---|---|
| 보스 맺힘 | 1200/1000 → **800** (BOSS_S1_MAEDHIM·BOSS_S2_MAEDHIM, 10-25) |
| 예상 싸움 길이 | 약 **3.3~4분** (1200일 때 5~6분, 목표 3~4분 = act1-enemy-check.md) |
| 지금 보스전 곡 | 필드 전투 곡 `bgm_solgogae_combat` **41.85초** 반복 |
| 지금 되풀이 횟수 | **4~6번** → 같은 41초가 귀에 걸린다. 필드 잡몹 싸움과 소리도 똑같다 |

**결론: 길이가 안 맞는다. 보스 전용 곡을 만들었다.**

- `bgm_solgogae_boss.ogg` — **142.65초** 반복. 오너가 만든 「Storm on the High Ridge」 전체(23.45~166.10초)를
  잘라 이음매를 맞춤(-16 LUFS, 전투 곡과 같은 크기). 조용히 시작 → 차오름 → 절정 → 한 번 숨 → 다시 몰아침 순서라
  1단계 동안 "점점 거세지는" 흐름이 저절로 생긴다.
- 2단계(맺힘 50% 이하 = 나루 큰물·선장 폭풍 즈음)에는 **같은 노래의 절정 부분**인 지금 전투 곡으로 3초 교차.
- 이러면 싸움 3.5분 = 보스 곡 약 1~1.5바퀴 + 절정 곡 2~3바퀴. 되풀이가 귀에 덜 걸린다.
- `data/bgm.json` 의 `layers.boss` 에 규칙을 적어 두었다. 크레딧은 `data/audio_credits.json` 에 추가.

코드팀 붙일 자리(BgmPlayer, 제안):

```csharp
// 보스와 싸우는 중이면 보스 곡, 보스 맺힘이 절반 이하면 절정(전투) 곡
// (왜) 800 맺힘 보스전 3~4분 동안 41초 곡이 4~6번 되풀이되지 않게
case BgmLayer.Combat:
    var b = judge.NearestBoss();
    bool bossFight = b != null && (b.Pos - judge.player.Pos).sqrMagnitude < 30f * 30f;
    bool p2 = bossFight && b.soul.Maedhim <= b.soul.MaedhimMax * 0.5f;
    if (bossFight && !p2 && boss != null) { want = boss; wantId = "boss"; }   // boss = Load("bgm_" + r + "_boss")
    else { want = combat; wantId = "combat"; }
    break;
// boss ↔ combat 로 넘어갈 때만 교차 시간을 3초로 (지금 기본 1초는 너무 급함)
```

보스 곡이 없는 지역은 `boss == null` 이라 지금처럼 전투 곡이 나온다 → 다른 막은 고장 나지 않는다.

### 다른 막도 같은 문제

2막·3막 보스도 지역 전투 곡(임시 대역 44초)을 되풀이한다. 진짜 곡이 오면 같은 방식(전체 곡 → `bgm_<지역>_boss`,
절정 → `_combat`)으로 자르면 된다. 1막처럼 긴 원곡이 있으면 새로 만들 필요 없이 자르기만 하면 됨.

## 5. 나중에 진짜 보스 곡을 따로 만들고 싶을 때 (Gemini 지시문 63, 선택)

> 지금 자른 곡으로도 충분하다. 아래는 1막 보스 6명을 더 구별하고 싶을 때만.

```
A tense Korean traditional battle piece for a boss fight on a misty pine ridge at night.
Fast jajinmori rhythm on janggu and a deep buk drum, a bowed ajaeng droning low,
piri carrying a sharp urgent melody. Starts restrained, builds for about two minutes,
breathes once with only drum and ajaeng, then surges again even harder.
No vocals, no Western drum kit, no synth. Around 3 minutes, steady tempo so it can loop.
```

(ip_scan.py 로 검사: 다른 작품·작곡가 이름 없음.)

## 6. 2·3막 보스와 흑월 2차 BGM 길이 점검 (10-26 추가)

| 보스 | 맺힘 | 목표 싸움 | 지금 곡 | 되풀이 | 고침 |
|---|---|---|---|---|---|
| B-05·B-06 (③ 붉은재) | 960·1120 | 3~4분 | `bgm_bulgeunjae_combat` 44.4초 | 4~6번 | `bgm_bulgeunjae_boss` 150초 → 2단계 `_boss_p2` 90.5초 |
| B-07·B-08 (④ 쇳골) | 1120·960 | 3~4분 | `bgm_soegol_combat` 44초 | 4~6번 | `bgm_soegol_boss` 149초 → `_boss_p2` 89.5초 |
| B-09·B-10 (⑤ 갯마을) | 1280·1440 | 3~4 · **4~5분** | `bgm_gaetmaeul_combat` 45초 | 4~7번 | `bgm_gaetmaeul_boss` 151초 → `_boss_p2` 89.5초 |
| B-11 (⑥ 도성) | 1280 | 3~4분 | `bgm_doseong_combat` 43.6초 | 4~6번 | `bgm_doseong_boss` 150초 → `_boss_p2` 90.4초 |
| **B-12 흑월 2차** (⑥ 성문 밖) | 1800 | **6~8분** | 컷이 `bgm_s1_heukwol` 66초를 지정 | 아래 '고장' 참고 | `bgm_s1_heukwol_fight` 180초(1·2단계) → 큰물 `bgm_s1_heukwol_flood` 120초 |

- 바꾼 뒤에는 1단계 곡이 1바퀴 이하, 2단계 곡이 1~2바퀴만 돈다. 흑월 2차 6~8분은 싸움 곡 약 1.3바퀴, 큰물 곡 1~2바퀴.
- 1단계 곡은 "조용히 시작 → 차오름 → 절정 → 한 번 숨 → 다시 몰아침" 흐름이다. 2단계는 처음부터 거세게 가고, 앞뒤 절반의 가락이 다르다.
- 모두 **임시 대역**(코드 합성, `tools/bgm_temp_render.py`, -16 LUFS)이다. 진짜 곡을 `Audio/BGM/<같은 이름>.ogg`로 넣으면 그것이 먼저 쓰인다.
- 규칙 정리: `data/bgm.json`의 `layers.boss.by_region`, `heukwol_2`.

### 흑월 2차에서 찾은 고장 2개 (코드팀)

1. **결전 곡이 싸움 중에 꺼진다.**
   - B12-INTRO가 8.0초에 `play bgm_s1_heukwol`을 보낸다.
   - 그런데 컷이 끝나면 `CutscenePlayer`가 `resume`을 보내고, `BgmPlayer`의 `resume`은 `playId = null`로 지정 곡을 지운다.
   - 그래서 싸움이 시작되면 ⑥ 지역 전투 곡으로 돌아간다. B12-P2의 `resume`도 같은 일을 한다.
   - 시즌2 B-20 `bigdam`도 같은 구조라 같은 고장이 있다.
2. **옛 `bgm_s1_heukwol`은 1회용 곡이다.**
   - 이 곡은 60에서 100으로 빨라지다가 끝 3초에서 닫힌다.
   - 반복하면 66초마다 소리가 끊기고 느린 처음으로 돌아간다.
   - 그래서 컷 지시를 반복용 `_fight`·`_flood`로 바꿨다(`tools/cutscene_audio_s1.py` → `data/cutscene_audio_s1.json`).
   - 이 바뀐 지시가 실제 컷 표에 들어가려면 `build_cutscenes_s1.py`를 한 번 다시 돌려야 한다.

```csharp
// BgmPlayer.Command — 결전 곡은 컷이 끝나도 남기고, 'end' 가 올 때만 내린다
// (왜) 컷 끝마다 오는 resume 이 결전 곡을 지워 흑월·물막이 바닥 싸움 내내 지역 전투 곡이 나오던 것을 막는다
static bool FightLoop(string id) => id != null && (id.Contains("heukwol") || id.Contains("bigdam") || id.Contains("knot") || id.Contains("imyeong") || id.Contains("mybaek"));
case "resume": mixTarget = 1f; forceLayer = null; if (!FightLoop(playId)) playId = null; break;
case "end":    playId = null; forceLayer = null; mixTarget = Mathf.Clamp01(to); break;   // B12-KNEEL 0.0초가 보낸다(0.3배로 줄이며 내림)
// 반복 판단도 같은 함수로: loop = FightLoop(playId);
```

- `end`를 모르는 지금 코드는 이 명령을 그냥 넘긴다. 그래서 먼저 데이터만 들어가도 고장 나지 않는다.
- 시즌2·3 결전 곡(`bigdam`·`knot`·`imyeong`·`mybaek`)의 길이 점검은 그 막을 구현할 때 같은 방식으로 하겠다.

## 7. 처음 10분 화면 요소(아트 PR #47) UI 소리 점검

| 화면 요소 | 지금 소리 | 판단 | 고침 |
|---|---|---|---|
| 첫 처결 카드 두 장(1:20, `exec_card_tendo`·`pahon`) | 없음(무릎 소리만) | 화면 아래에 큰 카드가 뜨는데 조용해서, 뜬 줄 모를 수 있다 | **sfx.exec.card.open**(새): 한지 두 장이 같은 크기로 스윽·스윽. 무릎 소리 0.25초 뒤. 천도·파혼 어느 쪽으로도 기울지 않게 같은 높이로 냈다 |
| 카드 고름(E·R·탭) | 천도 시전 / 파혼 소리 | 맞음 | 그대로. 폰에서 카드에 손가락을 올릴 때는 `sfx.card.hover` 재사용 |
| 일반 혼 머리 위 맺힘 막대 | 타격음 | 맞음. 막대가 줄 때마다 소리를 내면 너무 시끄럽다 | 그대로 |
| 덩어리 두 줄 막대(`bind_world_frame2`) | 없음 | 첫 줄이 다 깎여도 "아직 한 줄 남았다"를 귀로 알 수 없다 | **sfx.bind.row.break**(새): 새끼줄 한 가닥이 툭 끊김 + 낮은 둥. 첫 줄이 0이 될 때 한 번 |
| 미니맵 대기 혼 고리(`icon_soul_wait`) | 무릎 소리 + 대기 똑딱 | 맞음. 지도 아이콘은 일부러 소리를 내지 않는다(겹치면 시끄러움) | 그대로 |
| 넋길 낮→밤(`icon_soulpath_off` → 열림) | 없음(1막). 2·3막은 저녁 징 | 1막에서는 넋길이 열린 줄 모른다 | **sfx.soulpath.light**(새): 혼불 다섯이 하나씩 후—. 해 질 때 서낭당 40m 안에서만 3D로 한 번 |
| 넋길 안내 `[F]`(`prompt_soulpath`) | 없음 | 맞음. 안내가 뜰 때는 조용한 편이 낫다 | 낮에 F를 누르면 아무 일이 없으니 `sfx.ui.deny`를 제안 |
| 넋길을 탐(`CommandSoulPath`) | **`sfx.tendo.done`** | **틀림.** 천도 끝 소리라 "처결했다"로 들린다 | **sfx.soulpath.travel**(새): 혼불 줄 따라 쑥 빨려 감 → 새끼줄 삐걱 |
| 처결 고리 먹 받침 | — | 그림만 바뀜 | 소리 없음 |

```csharp
// JudgeSystem — (1) 첫 처결 카드: 카드를 띄우는 곳에서
Sfx.PlayDelayed("sfx.exec.card.open", 0.25f);                 // 2D, 무릎 소리 다음
// (2) 덩어리 첫 줄이 0이 되는 순간(줄이 바뀌는 판단 바로 뒤)
Sfx.Play("sfx.bind.row.break", enemy.Pos);
// (3) CommandSoulPath: Sfx.Play("sfx.tendo.done") → 바꿈
Sfx.Play("sfx.soulpath.travel");
// (4) 넋길이 열리는 순간(낮→밤, FieldManager 가 넋길 모델을 _off → 켜짐으로 바꾸는 곳)
if (가장 가까운 서낭당까지 < 40f) Sfx.Play("sfx.soulpath.light", 서낭당위치);
// (5) 낮에 서낭당 곁에서 F: SoulPathStop() < 0 이고 서낭당 곁이면
Sfx.Play("sfx.ui.deny");
```
