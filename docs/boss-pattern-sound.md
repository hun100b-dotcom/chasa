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
