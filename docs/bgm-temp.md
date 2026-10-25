# 임시 대역 BGM (기획·사운드, 2026-10-25)

오너가 아직 뽑지 않은 BGM 자리를 코드로 합성한 국악풍 반복곡으로 채웠다. 그래서 2막·3막에 들어가거나 시즌1 끝 컷이 와도 음악이 끊기지 않는다.

- 만드는 프로그램: `tools/bgm_temp_render.py`. 다시 돌려도 같은 파일이 나온다.
- 파일 위치: `unity/Assets/Resources/Audio/BGM/Temp/<id>.ogg` (21곡, 약 18MB)
- 목록: `data/bgm_temp.json` (곡 길이, 반복 여부, 측정 음량)

## 곡 목록

| 지역 | 낮 (day_a) | 밤 (night) | 전투 (combat) | 처결 (finish) |
|---|---|---|---|---|
| 붉은재 `bulgeunjae` | G 계면조 66, 중모리 장단, 피리 | 진양 장단, 아쟁 드론, 멀리서 나각 | 자진모리 108, 큰 북 | 징·북 한 번 + 대금 (6.9초) |
| 쇳골 `soegol` | C 계면조 80, 중중모리, 해금·거문고 | 진양 장단, 멀리서 쇠 소리 | 자진모리 120, 꽹과리 | 같은 틀 |
| 갯마을 `gaetmaeul` | A 계면조 70, 피리 + 해금 대답 | 징이 바퀴마다 울림 | 자진모리 112, 징 | 같은 틀 |
| 도성 `doseong` | F 평조 92, 굿거리, 단소·양금 | 가야금 드문드문 | 자진모리 132, 박 | 같은 틀 |

시즌1 끝 곡은 1회 재생용이고, 지시문 21~25의 구성을 따랐다.

| 곡 | 길이 | 구성 |
|---|---|---|
| `bgm_s1_heukwol` | 66초 | 진양에서 시작해 점점 빨라짐(60→100). 단계마다 징 세 번 |
| `bgm_s1_finale_a` | 126초 | 해금 혼자 되풀이 → 거문고·피리 → 60초에 뚝 멈춤 → 대금 한 음 |
| `bgm_s1_finale_b` | 96초 | 아쟁 한 음 위에 가야금 드문드문. 맺지 않고 멈춤 |
| `bgm_s1_dawn` | 101초 | A 평조. 대금과 가야금. 중간에 한 번 잦아듦 |
| `bgm_s1_credits` | 137초 | 중모리 70. 해금·대금이 번갈아 연주. 가운데 거문고, 끝에 요령 |

**음량.** 1막 진짜 곡과 똑같이 맞췄다. 탐색은 -20 LUFS, 전투·처결은 -16 LUFS다. 반복곡은 끝과 처음이 끊김 없이 이어지는지 검사했다.

## 진짜 곡으로 바꾸는 법 (코드 수정 없음)

오너 곡을 같은 이름으로 `Audio/BGM/` 에 넣으면 끝이다. 예를 들어 `Audio/BGM/bgm_soegol_day_a.ogg` 처럼 넣는다. 게임은 진짜 곡을 먼저 찾고, 없을 때만 `Temp/` 의 곡을 쓴다. 이름 규칙은 `data/bgm.json` 의 `naming` 에 있다.

## 코드팀 연결 제안 (BgmPlayer.cs, 코드팀 파일이라 제안만)

지금 BgmPlayer 는 솔고개 곡 5개만 고정으로 불러서, 지역이 바뀌어도 곡이 그대로다. 그래서 아래 세 가지를 바꾸면 된다.

**1) 진짜 곡 먼저, 없으면 임시 곡.** 컷이 지정하는 `play` 곡(시즌1 끝 곡)도 이 함수를 쓰므로 함께 해결된다.

```csharp
// 진짜 곡(BGM/)을 먼저 찾고, 없으면 임시 대역(BGM/Temp/)을 쓴다.
// 오너 곡을 같은 이름으로 넣기만 하면 자동으로 바뀐다.
static AudioClip Load(string id)
{
    return Resources.Load<AudioClip>("Audio/BGM/" + id) ?? Resources.Load<AudioClip>("Audio/BGM/Temp/" + id);
}
```

**2) 지역별로 다섯 곡을 다시 불러오기.**

```csharp
// 지역 번호 → 곡 이름 앞부분 (data/bgm.json naming.regions 와 같은 표)
static readonly string[] RegionKey = { "solgogae", "solgogae", "solgogae", "bulgeunjae", "soegol", "gaetmaeul", "doseong" };
string region;

void LoadRegion(string r)
{
    if (r == region) return;
    region = r;
    dayA = Load("bgm_" + r + "_day_a"); dayBclip = Load("bgm_" + r + "_day_b");   // day_b 는 없어도 된다(그러면 day_a 만 반복)
    night = Load("bgm_" + r + "_night"); combat = Load("bgm_" + r + "_combat"); finish = Load("bgm_" + r + "_finish");
    if (night == null) night = dayA;   // 밤 곡이 없으면 낮 곡으로
    curId = null;                        // 다음 프레임에 새 지역 곡으로 교차
    fadeLen = 4f;                        // 지역이 바뀔 때는 4초에 걸쳐 넘긴다(data/bgm.json region_crossfade_sec)
}
```

`Start()` 의 다섯 줄 Load 는 `LoadRegion("solgogae")` 한 줄로 바꾼다.

**3) 플레이어가 어느 지역에 있는지 알아내기.** 0.5초마다 한 번 확인하면 충분하다.

`act2_map.json` 의 `field.rect_m` 은 ③·④ 지역이다. ③과 ④는 구역(zones)의 `region` 값으로 가른다. `act3_map.json` 의 `fields["5"]`·`fields["6"]` 의 `rect_m` 은 ⑤·⑥ 지역이다. 어느 사각형에도 없으면 솔고개다.

```csharp
// 예시. 구역 사각형 안이면 그 구역의 region, 2막 필드 안의 길이면 가장 가까운 구역의 region
int RegionAt(Vector3 p) { /* act2_map.zones / act3_map.fields 사각형 검사 */ return 1; }

// Update() 맨 앞쪽
regionCheck -= Time.unscaledDeltaTime;
if (regionCheck <= 0f && judge.player != null)
{
    regionCheck = 0.5f;
    LoadRegion(RegionKey[Mathf.Clamp(RegionAt(judge.player.Pos), 0, RegionKey.Length - 1)]);
}
```

위의 `fadeLen = 4f` 가 Switch 의 교차 시간에 덮어쓰이지 않게 하려면, `Switch(...)` 를 부를 때 `curId == null` 이면 4초를 넘겨 주면 된다.

**함께 볼 것.** `Start()` 의 `loadedAny` 는 지금 솔고개 곡만 보고 정해진다. 지역 곡 기준으로 해도 결과는 같다. 임시 곡이 있으니 2막·3막에서도 항상 참이다.
