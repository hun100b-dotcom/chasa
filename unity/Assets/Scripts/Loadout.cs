// =============================================================================
// Loadout.cs — 플레이어가 지금 들고 낀 것: 든 무기, 도술 쿨다운, 장비. (규칙은 Core/Gear.cs)
// 왜 한 곳에? Player·JudgeSystem·화면 글자가 모두 같은 장비 합계를 읽어야 서로 값이 어긋나지 않는다.
// =============================================================================
using Chasa.Core;

public class Loadout
{
    public WeaponId weapon = WeaponId.Chain;
    public WeaponId other = WeaponId.Mace;                  // 등에 멘 다른 한 자루 (Tab 으로 맞바꿈, 기획: 2자루 교체)
    public float swapLeft;                                  // 바꿔 들기 남은 시간(이동·공격 불가)
    public float quakeCd;                                   // 땅울림 재사용 남은 시간
    public readonly SkillBar skills = new SkillBar();           // (옛 고정 도술 3칸 — 새 도술 트리로 대체되어 active 가 쓰인다)
    public readonly ActiveCooldowns active = new ActiveCooldowns();   // 새 도술 트리 액티브의 재사용 대기(이름으로)
    public float buffDamage, buffMove;                       // 도술이 잠깐 얹는 피해·이동 +%(원념 두르기·얼룩 타기). 바꾼 뒤 Refresh 로 반영
    public readonly Equipment gear = new Equipment();
    public GearStats stats = new GearStats();               // 장비 합계 + 성장(능력치·패시브). 장착·성장이 바뀔 때만 다시 계산
    public GrowthState growth;                              // 성장 상태(JudgeSystem 이 넣어 준다). 있으면 합계에 얹는다
    public string lastDrop = "";                            // 가장 최근 드롭 안내 글자
    public float lastDropT;

    public WeaponDef Def { get { return WeaponDef.Get(weapon); } }

    public void Tick(float dt)
    {
        swapLeft = System.Math.Max(0f, swapLeft - dt);
        quakeCd = System.Math.Max(0f, quakeCd - dt);
        lastDropT -= dt;
        skills.Tick(dt);
        active.Tick(dt);
    }

    /// <summary>새 물건을 비교해 장착. 장착했으면 합계를 다시 계산하고 true</summary>
    public bool Equip(ItemDef it)
    {
        if (!gear.TryEquip(it)) return false;
        Refresh();
        return true;
    }

    /// <summary>손보기로 장비가 바뀐 뒤 합계를 다시 계산한다</summary>
    public void Refresh() { stats = gear.Stats(); GrowthEffects.Apply(growth, stats); stats.DamagePct += buffDamage; stats.MoveSpeedPct += buffMove; }   // 장비 합계 위에 성장 효과를 얹는다

    public static string Describe(ItemDef it)
    {
        return Ko.Describe(it);
    }
}
