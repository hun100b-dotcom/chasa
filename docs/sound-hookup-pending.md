# 아직 안 붙은 소리 3건 — 코드팀과 맞출 붙이는 법 (기획·사운드, 2026-10-26)

> 코드 브랜치(ozfksa, 2026-10-26 KST 06시경) 기준. 사운드팀은 코드 파일을 고치지 않는다. 아래 그대로 붙이면 된다.
> 소리 파일은 모두 이미 있다(`unity/Assets/Resources/Audio/Sfx`).

## 1. 한 벌 완성음 `sfx.equip.set.complete`
**지금:** `Loadout.Equip` → `GearSfx.Equip(it)`는 몸 + 등급 소리만 낸다. 한 벌 판정은 `JudgeSystem` 1605줄 근처 외형 코드에만 있다(갓·도포·띠·신 넷이 모두 이름 있는 물건).

**붙이는 법:**
1. 한 벌 판정을 한 곳으로 모은다(외형 코드도 같이 쓰게):
   ```csharp
   // Loadout.cs — 한 벌 = 갓·도포·띠·신 넷이 모두 이름 있는 물건(외형 5단계와 같은 규칙)
   public bool FullSet()
   {
       foreach (var p in new[] { EquipPos.Hat, EquipPos.Robe, EquipPos.Belt, EquipPos.Shoes })
       { var g = gear.GetAt(p); if (g == null || !g.Named) return false; }
       return true;
   }
   ```
2. `Loadout.Equip`에서 끼기 전·후를 비교해 **새로 갖춰졌을 때만** 한 번:
   ```csharp
   bool wasSet = FullSet();
   if (!gear.TryEquip(it)) return false;
   Refresh();
   GearSfx.Equip(it);
   if (!wasSet && FullSet()) Sfx.PlayLater("sfx.equip.set.complete", 0.25f);   // 한 벌이 막 갖춰짐(등급 소리 끝난 뒤)
   ```
3. (선택) 한 벌 등급 머리 `sfx.equip.tier.set`은 코드에 '한 벌' 등급이 따로 생길 때 `GearSfx.Tier`에 `"set"`을 더한다. 지금은 안 써도 된다.

## 2. 장비 풀기음 `sfx.equip.remove`
**지금:** `DayScreen` 198줄 `lo.gear.RemoveAt(...)` 뒤에 소리 없음.

**붙이는 법:**
```csharp
// GearSfx.cs
public static void Remove() { Sfx.Play("sfx.equip.remove"); }   // 매듭 풂 + 내려놓는 툭(등급 무관)
```
```csharp
// DayScreen.cs 198줄: msg = "장비를 풀었다"; 바로 앞에
GearSfx.Remove();
```
캐릭터 창(`CharacterPanel`)에서 풀기가 생기면 거기서도 같은 한 줄.

## 3. 물안개 저역 통과 (검은여울 `prop_mist_bank`·`prop_mist_pillar`)
**지금:** `Act1Soundscape`가 `inside_lowpass_hz`를 읽기만 하고 쓰지 않는다.
**바라는 것:** 물안개 반경(4 m) 안에 있는 동안 **주변 소리만** 먹먹하게(2.5 kHz). 전투·UI 소리(`Sfx` 본체)는 그대로 둔다.
그래서 `Sfx`의 master 필터(천도 시전용)는 건드리지 않고, 주변 소리 음원마다 필터를 하나씩 단다.

**붙이는 법 (`Act1Soundscape.cs`):**
```csharp
float mistHz = 0f;          // 0 = 안개 밖. 안이면 그 소품의 inside_lowpass_hz
float lpNow = 22000f;       // 지금 필터 위치(부드럽게 옮긴다)

// Rescan(p) 맨 앞에서 mistHz = 0f; 로 비우고, 소품 고르는 루프(picked 계산 뒤)에:
if (pr.inside_lowpass_hz > 0f && picked.Count > 0 && Vector2.Distance(pp, picked[0]) <= pr.max)
    mistHz = pr.inside_lowpass_hz;

// Want(...)에서 새 음원을 만들 때 (s.Play() 앞):
go.AddComponent<AudioLowPassFilter>().cutoffFrequency = 22000f;

// ApplyVolumes() 맨 앞:
lpNow = Mathf.MoveTowards(lpNow, mistHz > 0f ? mistHz : 22000f, Time.unscaledDeltaTime * 20000f);   // 1초쯤 걸려 먹먹해진다
// 그리고 루프 안에서 각 음원마다 (안개 소리 자신은 제외):
var lp = l.s.GetComponent<AudioLowPassFilter>();
if (lp != null) lp.cutoffFrequency = l.s.clip != null && l.s.clip.name == "amb_mist_bank" ? 22000f : lpNow;
```
- 흩뿌림(한 번짜리, `Sfx.PlayLater`)은 `Sfx` 본체 소리라 이 필터를 안 탄다. 괜찮다(멀리서 나는 소리라 안개 속에서도 들려도 된다).
- 확인: 검은여울 물안개 덩이(예: 96,470)에 들어가면 1초쯤 걸려 여울물·병자 등 소리가 먹먹해지고, 나오면 돌아와야 한다.
