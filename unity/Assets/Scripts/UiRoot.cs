// =============================================================================
// UiRoot.cs — UI Toolkit 으로 그린 HUD (단계 U0 토대 + U1 장부·체력).
//
// UI Toolkit 이란? 화면을 '상자(VisualElement)들의 나무'로 만들고 글자·색·배치를 스타일로 정하는 유니티 신형 화면 방식.
//   옛 방식(IMGUI)은 매 프레임 위치를 좌표로 계산해야 했지만, 여기선 "왼쪽 위에 세로로 쌓기"처럼 말로 정하면
//   해상도(폰/PC)가 달라도 자동으로 맞는다.
// 왜 코드로 만드나? 파일(UXML)을 에디터가 불러와야 하는 단계를 없애려고(에디터 없이 AI가 고치는 원칙).
//   나중에 UXML/USS 파일로 옮겨도 아래 이름(hud-root, ledger-note, vitals)은 기획 UI 밑그림의 이름 그대로다.
// 마우스는 가로채지 않는다(pickingMode Ignore): 게임 클릭이 그대로 먹어야 하니까.
// 켜는 법: 주소 끝 ?ui 또는 balance.json 의 UI_TOOLKIT=true. 꺼져 있으면 예전 IMGUI 가 그린다.
// =============================================================================
using UnityEngine;
using UnityEngine.UIElements;
using Chasa.Core;

public class UiRoot : MonoBehaviour
{
    public static bool Enabled;   // 시작 때 GameMain 이 정한다

    public readonly HudState Hud = new HudState();

    UIDocument doc;
    Label ledger, vital, night, hint, hpText;
    VisualElement hpFill, root;
    string lastLedger, lastVital, lastNight;

    static readonly Color PaperBg = new Color(0.05f, 0.05f, 0.09f, 0.62f);
    static readonly Color Ink = new Color(1f, 1f, 1f, 0.92f);

    void Start()
    {
        // 화면 설정(PanelSettings): 1280×720 기준으로 크기를 맞춘다. 파일 없이 코드로 만든다
        var ps = ScriptableObject.CreateInstance<PanelSettings>();
        ps.scaleMode = PanelScaleMode.ScaleWithScreenSize;
        ps.referenceResolution = new Vector2Int(1280, 720);
        ps.screenMatchMode = PanelScreenMatchMode.MatchWidthOrHeight;
        ps.match = 0.5f;
        ps.themeStyleSheet = ScriptableObject.CreateInstance<ThemeStyleSheet>();   // 빈 테마(기본 모양 없이 우리 스타일만 씀)
        ps.sortingOrder = 5;
        var go = new GameObject("UiRoot_Doc");
        go.transform.SetParent(transform, false);
        doc = go.AddComponent<UIDocument>();
        doc.panelSettings = ps;
        Build(doc.rootVisualElement);
    }

    void Build(VisualElement r)
    {
        root = new VisualElement { name = "hud-root", pickingMode = PickingMode.Ignore };
        root.style.position = Position.Absolute; root.style.left = 0; root.style.top = 0; root.style.right = 0; root.style.bottom = 0;
        r.Add(root);

        // 장부 쪽지(왼쪽 위, 세로로 쌓기): 장부 / 체력 / 밤
        var note = new VisualElement { name = "ledger-note", pickingMode = PickingMode.Ignore };
        note.style.position = Position.Absolute; note.style.left = 12; note.style.top = 32;
        note.style.backgroundColor = PaperBg;
        note.style.paddingLeft = 12; note.style.paddingRight = 14; note.style.paddingTop = 8; note.style.paddingBottom = 10;
        note.style.borderTopLeftRadius = 6; note.style.borderBottomLeftRadius = 6; note.style.borderTopRightRadius = 6; note.style.borderBottomRightRadius = 6;
        root.Add(note);
        ledger = Line(note, 18); vital = Line(note, 18);
        // 체력 막대(vitals): 바탕 + 채움. 낮아지면 붉게
        var bar = new VisualElement { name = "vitals", pickingMode = PickingMode.Ignore };
        bar.style.height = 8; bar.style.marginTop = 2; bar.style.marginBottom = 4;
        bar.style.backgroundColor = new Color(0, 0, 0, 0.55f);
        hpFill = new VisualElement { pickingMode = PickingMode.Ignore };
        hpFill.style.height = 8; hpFill.style.backgroundColor = new Color(0.72f, 0.82f, 0.95f);
        bar.Add(hpFill);
        note.Add(bar);
        night = Line(note, 18);
        hint = Line(note, 14); hint.text = HudState.KeyHint(); hint.style.opacity = 0.65f; hint.style.marginTop = 4;
    }

    Label Line(VisualElement parent, int size)
    {
        var l = new Label { pickingMode = PickingMode.Ignore };
        l.style.color = Ink; l.style.fontSize = size;
        l.style.whiteSpace = WhiteSpace.NoWrap;
        var f = Ko.GetFont();
        if (f != null) l.style.unityFontDefinition = FontDefinition.FromFont(f);   // 한글 글꼴(없으면 네모로 깨지므로 반드시)
        parent.Add(l);
        return l;
    }

    /// <summary>JudgeSystem 이 값을 채운 뒤 부른다. 글자가 바뀐 줄만 갱신한다(안 바뀌면 건드리지 않아 가볍다)</summary>
    public void Refresh(bool visible)
    {
        if (root == null) return;
        root.style.display = visible ? DisplayStyle.Flex : DisplayStyle.None;
        if (!visible) return;
        var a = Hud.LedgerLine(); if (a != lastLedger) { ledger.text = lastLedger = a; }
        var b = Hud.VitalLine(); if (b != lastVital) { vital.text = lastVital = b; }
        var c = Hud.NightLine(); if (c != lastNight) { night.text = lastNight = c; }
        hpFill.style.width = Length.Percent(Hud.HpRatio * 100f);
        hpFill.style.backgroundColor = Hud.HpLow ? new Color(0.9f, 0.3f, 0.3f) : new Color(0.72f, 0.82f, 0.95f);
    }
}
