// =============================================================================
// Loadout.cs — 플레이어가 지금 들고 낀 것: 든 무기, 도술 쿨다운, 장비. (규칙은 Core/Gear.cs)
// 왜 한 곳에? Player·JudgeSystem·화면 글자가 모두 같은 장비 합계를 읽어야 서로 값이 어긋나지 않는다.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;

public class Loadout
{
    public WeaponId weapon = WeaponId.Chain;
    public WeaponId other = WeaponId.Mace;                  // 등에 멘 다른 한 자루 (Tab 으로 맞바꿈, 기획: 2자루 교체)
    public float swapLeft;                                  // 바꿔 들기 남은 시간(이동·공격 불가)
    public float quakeCd;                                   // 땅울림 재사용 남은 시간
    public readonly SkillBar skills = new SkillBar();           // (옛 고정 도술 3칸 — 새 도술 트리로 대체되어 active 가 쓰인다)
    public readonly ActiveCooldowns active = new ActiveCooldowns();   // 새 도술 트리 액티브의 재사용 대기(이름으로)
    public float buffDamage, buffMove, buffMovePassive;                       // 도술이 잠깐 얹는 피해·이동 +%(원념 두르기·얼룩 타기). 바꾼 뒤 Refresh 로 반영
    public readonly Equipment gear = new Equipment();
    public readonly List<Seal> sealBag = new List<Seal>();   // 만들어 둔(아직 안 박은) 인
    public readonly SoulWallet wallet = new SoulWallet();   // 빛깔별 넋 주머니(인 만들기 재료). 천도한 혼의 구역 빛깔로 쌓인다
    public GearStats stats = new GearStats();               // 장비 합계 + 성장(능력치·패시브). 장착·성장이 바뀔 때만 다시 계산
    public GrowthState growth;                              // 성장 상태(JudgeSystem 이 넣어 준다). 있으면 합계에 얹는다
    public string lastDrop = "";                            // 가장 최근 드롭 안내 글자
    public float lastDropT;

    public static readonly WeaponId[] AllWeapons = { WeaponId.Chain, WeaponId.Mace, WeaponId.Bell, WeaponId.Trident, WeaponId.Brush };   // 5계열 모두 고를 수 있다

    /// <summary>손에 들 무기를 고른다. 등에 멘 것과 같으면 둘을 맞바꾼다(같은 무기 두 자루는 안 됨)</summary>
    public void SetHand(WeaponId w) { if (w == weapon) return; if (w == other) other = weapon; weapon = w; swapLeft = 0f; }

    /// <summary>등에 멜 무기를 고른다. 손에 든 것과 같으면 둘을 맞바꾼다</summary>
    public void SetBack(WeaponId w) { if (w == other) return; if (w == weapon) weapon = other; other = w; }

    public WeaponDef Def { get { return WeaponDef.Get(weapon); } }

    public void Tick(float dt)
    {
        swapLeft = System.Math.Max(0f, swapLeft - dt);
        quakeCd = System.Math.Max(0f, quakeCd - dt / stats.WeaponCdMult);   // 무기 기술 재사용 단축 옵션(상한 40%)
        lastDropT -= dt;
        skills.Tick(dt / stats.SkillCdMult);   // 도술 재사용 단축(상한 35%): 시간을 더 빨리 흘려 보낸다
        active.Tick(dt / stats.SkillCdMult);
    }

    /// <summary>새 물건을 비교해 장착. 장착했으면 합계를 다시 계산하고 true</summary>
    public bool Equip(ItemDef it)
    {
        bool wasSet = FullSet();
        if (!gear.TryEquip(it)) return false;
        Refresh();
        GearSfx.Equip(it);
        if (!wasSet && FullSet()) Sfx.PlayLater("sfx.equip.set.complete", 0.25f);   // 한 벌이 막 갖춰졌다(등급 소리가 끝난 뒤)   // 장착 소리: 몸(쇠·천·노리개) + 머리(등급)를 0.06초 어긋나게
        return true;
    }

    /// <summary>한 벌 = 갓·도포·띠·신 넷이 모두 이름 있는 물건(외형 5단계와 같은 규칙)</summary>
    public bool FullSet()
    {
        foreach (var p in new[] { EquipPos.Hat, EquipPos.Robe, EquipPos.Belt, EquipPos.Shoes })
        { var g = gear.GetAt(p); if (g == null || !g.Named) return false; }
        return true;
    }

    /// <summary>손보기로 장비가 바뀐 뒤 합계를 다시 계산한다</summary>
    /// <summary>인 만들기: 넋 주머니에서 깎고 가방에 담는다. 넋이 모자라면 false (아무것도 깎지 않는다)</summary>
    /// <summary>인 만들기 문(기획 인 점검 2): 작은 인은 1막 첫 보스를 보낸 뒤, 큰 인은 2막에 들어선 뒤. 열려 있으면 null, 잠겼으면 알림 글</summary>
    public string CraftLockReason(bool large)
    {
        bool open = large ? gear.Act2Entered : gear.FirstRingBossDone;
        return open ? null : "아직 명부에 이 인이 없다";
    }

    public bool CraftSeal(SoulColor a, SoulColor b, bool large)
    {
        if (CraftLockReason(large) != null) return false;
        var s = wallet.Craft(a, b, large);
        if (s == null) return false;
        sealBag.Add(s); return true;
    }

    /// <summary>가방의 인 하나를 그 자리 장비 홈에 끼운다. 성공하면 합계를 다시 계산한다</summary>
    public bool InsertSeal(EquipPos pos, int bagIndex)
    {
        if (bagIndex < 0 || bagIndex >= sealBag.Count) return false;
        if (!SealEffects.Insert(gear.GetAt(pos), pos, sealBag[bagIndex])) return false;
        sealBag.RemoveAt(bagIndex); Refresh(); return true;
    }

    public void Refresh() { stats = gear.Stats(); GrowthEffects.Apply(growth, stats); stats.DamagePct += buffDamage; stats.MoveSpeedPct += buffMove + buffMovePassive; }   // 장비 합계 위에 성장 효과를 얹는다

    public static string Describe(ItemDef it)
    {
        return Ko.Describe(it);
    }
}
