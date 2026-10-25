using UnityEngine;
using Chasa.Core;

/// <summary>
/// 화면에 보이는 한글 글꼴과 공용 낱말.
/// 왜 따로 두나: 글꼴 설정이 화면마다 흩어지면 한 곳만 빠져도 글자가 네모(□)로 깨진다.
/// 글꼴은 Noto Sans KR(OFL 라이선스: 상업 이용 무료)에서 KS X 1001 한글 2350자 + 영숫자·기호만 잘라
/// 용량을 0.4MB로 줄였다(WebGL은 용량이 곧 로딩 시간).
/// </summary>
public static class Ko
{
    /// <summary>화면을 실제로 터치했을 때만 true — Chrome 은 PC 에서도 touchSupported 가 true 라서 터치 입력이 한 번 들어와야 버튼을 띄운다</summary>
    public static bool TouchUI;
    static Font font;
    static bool loaded;

    /// <summary>OnGUI 맨 앞에서 부른다. GUI 기본 스킨(skin = 화면 글꼴 묶음)의 글꼴을 한글 글꼴로 바꾼다</summary>
    public static void Apply()
    {
        if (!loaded) { loaded = true; font = Resources.Load<Font>("Fonts/NotoSansKR-Subset"); }
        if (font != null && GUI.skin.font != font) GUI.skin.font = font;
    }

    /// <summary>한글 글꼴(UI Toolkit 글자도 같은 글꼴을 쓰도록 꺼내 준다)</summary>
    public static Font GetFont()
    {
        if (!loaded) { loaded = true; font = Resources.Load<Font>("Fonts/NotoSansKR-Subset"); }
        return font;
    }

    /// <summary>장비 칸 이름</summary>
    public static string SlotName(Slot s)
    {
        switch (s)
        {
            case Slot.Weapon: return "무기";
            case Slot.Robe: return "도포";
            case Slot.Hat: return "갓";
            case Slot.Belt: return "띠";
            case Slot.Shoes: return "신";
            default: return "노리개";
        }
    }

    /// <summary>장비 자리 이름. 같은 종류가 둘인 자리(무기·노리개)는 1·2 를 붙여 구분한다</summary>
    public static string PosName(EquipPos p)
    {
        switch (p)
        {
            case EquipPos.Weapon1: return "무기 1";
            case EquipPos.Weapon2: return "무기 2";
            case EquipPos.Charm1: return "노리개 1";
            case EquipPos.Charm2: return "노리개 2";
            default: return SlotName(Equipment.KindOf(p));
        }
    }

    /// <summary>자리 화면에 보여 줄 순서(무기·갓·도포·띠·신·노리개)</summary>
    public static readonly EquipPos[] PosOrder = { EquipPos.Weapon1, EquipPos.Weapon2, EquipPos.Hat, EquipPos.Robe, EquipPos.Belt, EquipPos.Shoes, EquipPos.Charm1, EquipPos.Charm2 };

    /// <summary>아이콘 파일 이름에 쓰는 종류 글자(새 종류는 그림이 아직 없어 노리개 그림을 빌린다)</summary>
    public static string IconName(Slot s, string rar, bool named)
    {
        if (s == Slot.Hat) return "equip_gat";   // 갓·띠·신은 등급 구분 없는 그림 한 장(아트 PR #33)
        if (s == Slot.Belt) return "equip_tti";
        if (s == Slot.Shoes) return "equip_sin";
        return named ? "icon_named_wolhwa_bell" : "icon_" + IconKind(s) + "_" + rar;
    }
    public static string IconKind(Slot s) { return s == Slot.Weapon ? "weapon" : s == Slot.Robe ? "dopo" : "noriga"; }

    /// <summary>장비 등급 이름 (Common/Crafted/Rare = 흔한/손본/귀한)</summary>
    public static string RarityName(Rarity r)
    {
        return r == Rarity.Rare ? "귀한" : r == Rarity.Crafted ? "손본" : "흔한";
    }

    /// <summary>장비 한 줄 이름. 이름 있는 장비는 그 이름, 아니면 등급 이름</summary>
    public static string ItemName(ItemDef it)
    {
        return it.Named ? it.Name : RarityName(it.Rarity);
    }

    /// <summary>기울기 이름 (피 묻은 매듭·향 내음 …). 모르면 빈 글자</summary>
    public static string TiltName(ItemDef it)
    {
        var t = it.TiltId == null ? null : TiltDef.Find(it.TiltId);
        return t == null ? "" : t.Name;
    }

    /// <summary>드롭 알림용 한 줄 설명</summary>
    public static string Describe(ItemDef it)
    {
        return RarityName(it.Rarity) + " " + SlotName(it.Slot) + (it.Named ? " [" + it.Name + "]" : "") +
               " (옵션 " + it.Options.Count + (it.Gradient ? ", 기울기" : "") + ")";
    }
}
