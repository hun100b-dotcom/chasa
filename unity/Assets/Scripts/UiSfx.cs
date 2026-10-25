// =============================================================================
// UiSfx.cs — 메뉴 버튼 소리. 눌렸을 때 sfx.ui.click, 닫기·취소·뒤로면 sfx.ui.back.
// 왜 따로 만들었나? 버튼이 패널마다 흩어져 있어서(GUI.Button 수십 곳) 한 곳에서 소리를 내게 묶으려고.
// =============================================================================
using UnityEngine;

public static class UiSfx
{
    /// <summary>글자에 따라 '되돌아가는' 버튼인가</summary>
    public static bool IsBack(string text) { return text != null && (text.Contains("닫기") || text.Contains("취소") || text.Contains("뒤로")); }
    public static void Click(string text) { Sfx.Play(IsBack(text) ? "sfx.ui.back" : "sfx.ui.click"); }

    /// <summary>GUI.Button 과 같고, 눌렸을 때 소리가 난다</summary>
    public static bool Btn(Rect r, string text) { bool p = GUI.Button(r, text); if (p) Click(text); return p; }
    public static bool Btn(Rect r, string text, GUIStyle st) { bool p = GUI.Button(r, text, st); if (p) Click(text); return p; }
}
