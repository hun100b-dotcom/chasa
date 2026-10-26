# 보스가 꿇은 동안 압박 예고음 (기획·사운드, 2026-10-26 KST)

> 근거:
> - `planning/combat/boss-final-moment-act1-2.md` §2 "꿇은 동안의 약한 압박"
> - `boss-final-moment-act3.md` §2
> - `b01-naru-final-check.md`
>
> 파일은 `Resources/Audio/Sfx/<id의 점을 밑줄로>.wav`(모두 1.05초)이다. `BossArena.cs`·`Act2BossArena.cs`는 코드팀 파일이라 붙일 자리만 제안한다.

## 1. 규칙 (모든 보스가 같다)

- 압박이 닿기 **정확히 1.0초 전에** 튼다.
- 소리는 1.0초 동안 점점 커지다가, 닿는 순간 **뚝 끊긴다**. 끊긴 바로 뒤에 압박 자체의 소리(파동·낙석·파도…)가 난다.
- 그래서 귀가 익히는 것은 하나다: **"차오르던 소리가 끊기고 압박이 지나가면, 그때 천도를 시작한다."** 압박 간격은 4~6초이고 천도 시전은 2초다. 끊긴 직후에 시작하면 다음 예고가 오기 전에 끝난다.
- 바탕 한 겹은 모든 보스가 같다. 낮게 차오르는 숨이고, 1초 동안 커지고 높아진다. 그 위의 빛깔만 보스마다 다르다. 그래서 처음 보는 보스여도 "아, 예고다"를 안다.
- 예고음은 모두 천도 먹먹 필터를 건너뛴다(`bypass_cast`). 시전 중에도 또렷하게 들린다. 시전을 늦게 시작했으면 "지금 끊어야 하나"를 판단할 수 있다.

## 2. 보스별

| 보스 | 꿇은 동안 압박 | 예고음 id | 틀 때 | 소리 |
|---|---|---|---|---|
| B-01 나루 영감 | 물 혼 두 물결(꿇는 순간 · 5초) | `sfx.boss.naru.kneel.warn` | **4.0초**(두 번째 물결 1초 전). 첫 물결은 꿇는 소리와 같이 와서 예고 없음 | 뱃전 아래 물이 보글보글 차오름 |
| B-03 서 의원 | 낙인 파동 4.0초마다 | `sfx.boss.seo.kneel.warn` | 파동마다 1.0초 전 | 쇠 낙인이 달궈지며 치이익 |
| B-06 이름 없는 장수 | 마지막 호령: 1초부터 4.5초마다 대형 | `sfx.boss.general.kneel.warn` | 대형마다 1.0초 전. 그림 예고(1.2초)보다 0.2초 늦게 시작 | 진고(큰 북)가 둥…둥.둥둥 빨라짐 |
| B-07 반장 칠성 | 낙석 4.5초마다(그림자 3곳) | `sfx.boss.chilseong.kneel.warn` | 그림자와 같이(1.0초 전) | 갱도 천장 나무가 끼이익 휘고 흙이 흘러내림 |
| B-08 장부꾼 염씨 | 숫자 4장 4.5초마다(지뢰는 남음) | `sfx.boss.yeom.kneel.warn` | 던지기 1.0초 전 | 장부 장이 촤르르 빨라짐 |
| B-09 망부석 아낙 | 파도 한 줄 4.5초마다 | `sfx.boss.mangbu.kneel.warn` | 파도 1.0초 전 | 바닷물이 쏴아 뒤로 빠지며 자갈이 끌려감 |
| B-10 만선호 선장 | 갑판 기울기 6초마다 | `sfx.boss.seonjang.kneel.warn` | 기울기 1.0초 전 | 배 밑창이 끄으응 신음하며 높아짐 |
| B-11 다리 밑 왕초 | 거적 던지기 4.5초마다 | `sfx.boss.wangcho.kneel.warn` | 던지기 1.0초 전. 그림 예고(0.8초)보다 0.2초 먼저 | 거적을 휘휘 돌리는 바람이 빨라짐 |

**예고음을 만들지 않은 보스**
- B-02 월화: 지금 있는 잔 파동(5.5초)을 그대로 쓴다. 열두째 칸이 늘 안전하므로 때를 맞출 필요가 적다.
- B-05 기수 대돌: 남은 번호 병사가 공격하는 방식이라 정해진 박자가 없다.
- B-12 흑월 2차: 일부러 압박이 없다(기획). 예고음도 없다.

싸움 중에 쓰는 기존 예고(`sfx.boss.chilseong.collapse.telegraph`, `sfx.boss.seonjang.rope.telegraph` 등)는 그대로 둔다. 꿇은 동안에는 위의 예고음을 **대신** 튼다. 그래야 "꿇은 동안의 박자"가 따로 귀에 남는다.

## 3. 붙일 자리 (제안)

```csharp
// 꿇은 동안 전용 Tick(Act2BossArena 의 Clear() 자리, BossArena 의 서 의원 분기) 안에서
// (왜) 예고를 압박 1.0초 전에 틀어야 "소리가 끊기면 천도"가 맞아떨어진다. 다음 압박 시각을 이미 알고 있으니 1초 앞에서 한 번
const float WarnLead = 1.0f;
if (!warned && kneelPressT <= WarnLead) { warned = true; Sfx.Play(KneelWarnId(def.Id), boss.Pos); }
if (kneelPressT <= 0f) { DoPressure(); kneelPressT = gap; warned = false; }

static string KneelWarnId(string id) => id switch {
    "B-01" => "sfx.boss.naru.kneel.warn",      "B-03" => "sfx.boss.seo.kneel.warn",
    "B-06" => "sfx.boss.general.kneel.warn",   "B-07" => "sfx.boss.chilseong.kneel.warn",
    "B-08" => "sfx.boss.yeom.kneel.warn",      "B-09" => "sfx.boss.mangbu.kneel.warn",
    "B-10" => "sfx.boss.seonjang.kneel.warn",  "B-11" => "sfx.boss.wangcho.kneel.warn",
    _ => null };
```

- 처결이 시작되면(천도 성공·파혼) 남은 예고를 멈춘다. 예고가 울리는 중에 끝났으면 0.1초에 걸쳐 꺼 준다.
- 장수는 꿇은 뒤 첫 대형이 1초에 온다. 그래서 첫 예고는 꿇는 순간(0초)에 울린다. 꿇는 소리와 겹쳐도 되도록 바탕 숨을 낮게 두었다.

## 4. 들어 보기

미리듣기 2쪽 맨 아래 `demo_kneel_warn`: 칠성이 꿇음 → 3.7초 예고 → 4.7초 낙석 → 4.8초 천도 시작 → 6.8초 천도 끝 → 8.2초 다음 예고 → 9.2초 낙석. 천도가 두 압박 사이에 들어가는 것을 들을 수 있다.
