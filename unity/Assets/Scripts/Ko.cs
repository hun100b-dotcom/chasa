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
    static Font font;
    static bool loaded;

    /// <summary>OnGUI 맨 앞에서 부른다. GUI 기본 스킨(skin = 화면 글꼴 묶음)의 글꼴을 한글 글꼴로 바꾼다</summary>
    public static void Apply()
    {
        if (!loaded) { loaded = true; font = Resources.Load<Font>("Fonts/NotoSansKR-Subset"); }
        if (font != null && GUI.skin.font != font) GUI.skin.font = font;
    }

    /// <summary>장비 칸 이름</summary>
    public static string SlotName(Slot s)
    {
        return s == Slot.Weapon ? "무기" : s == Slot.Robe ? "도포" : "노리개";
    }

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
