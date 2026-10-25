// =============================================================================
// GearSfx.cs — 장비 장착·손보기 소리(사운드팀 docs/gear-sound.md).
// 왜 두 겹인가: "무엇을 걸쳤나"(몸: 쇠·천·노리개)와 "얼마나 귀한가"(머리: 등급)를 따로 만들어 같이 튼다.
//   파일 8개로 15가지 조합이 나오고, 같은 등급이면 무엇을 끼든 같은 머리가 들려서 귀가 등급을 배운다.
// =============================================================================
using Chasa.Core;

public static class GearSfx
{
    /// <summary>등급 이름(소리 id 끝말). 이름 있는 > 귀한 > 손본 > 흔한</summary>
    public static string Tier(ItemDef it) { return it.Named ? "named" : it.Rarity == Rarity.Rare ? "rare" : it.Rarity == Rarity.Crafted ? "crafted" : "common"; }

    /// <summary>장착: 몸 소리 + (0.06초 뒤) 등급 소리</summary>
    public static void Equip(ItemDef it)
    {
        if (it == null) return;
        string body = it.Slot == Slot.Weapon ? "metal" : it.Slot == Slot.Charm ? "trinket" : "cloth";
        Sfx.Play("sfx.equip.body." + body);
        Sfx.PlayLater("sfx.equip.tier." + Tier(it), 0.06f);
    }

    /// <summary>손보기 성공: 첫 번째는 '처음 손봤다' 소리, 그 뒤는 등급 소리를 단계마다 조금씩 높여서(+0.03×(단계−1)). +5 에 닿으면 노래 소리</summary>
    public static void Enhance(ItemDef it, bool first)
    {
        if (first) { Sfx.Play("sfx.repair.first"); return; }
        if (it.Plus >= Balance.ENHANCE_MAX) { Sfx.Play("sfx.enhance.max"); return; }
        Sfx.PlayLater("sfx.enhance." + Tier(it), 0f, 1f + 0.03f * (it.Plus - 1), 0f);
    }

    public static void Remove() { Sfx.Play("sfx.equip.remove"); }   // 매듭 풂 + 내려놓는 툭(등급 무관)

    public static void EnhanceFail() { Sfx.Play("sfx.enhance.fail"); }
}
