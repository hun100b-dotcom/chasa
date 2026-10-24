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
    VisualElement hpFill, root, toastBox, skillBar;
    readonly System.Collections.Generic.List<VisualElement> edgePool = new System.Collections.Generic.List<VisualElement>();   // 화면 가장자리 경고 표시 재사용 묶음
    Label dodgeLabel, pullLabel, weaponLabel; VisualElement[] pips = new VisualElement[0];
    string lastToasts;
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
        // 빈 테마라 기본 '화면 가득 채우기'가 없다 → 바닥(r) 높이가 0 이 돼 아래·퍼센트 위치가 어긋났다. 직접 화면 전체로 편다
        r.style.position = Position.Absolute; r.style.left = 0; r.style.top = 0; r.style.right = 0; r.style.bottom = 0;
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
        BuildToasts(); BuildSkillBar();
        hint = Line(note, 14); hint.text = HudState.KeyHint(); hint.style.opacity = 0.65f; hint.style.marginTop = 4;
    }

    static void Panel(VisualElement v)
    {
        v.style.backgroundColor = new Color(0.10f, 0.11f, 0.18f, 0.78f);   // 어두운 밤 화면에서도 구분되게 조금 밝고 진하게
        var edge = new Color(1f, 1f, 1f, 0.22f);
        v.style.borderTopWidth = 1; v.style.borderBottomWidth = 1; v.style.borderLeftWidth = 1; v.style.borderRightWidth = 1;
        v.style.borderTopColor = edge; v.style.borderBottomColor = edge; v.style.borderLeftColor = edge; v.style.borderRightColor = edge;
        v.style.paddingLeft = 10; v.style.paddingRight = 10; v.style.paddingTop = 6; v.style.paddingBottom = 6;
        v.style.borderTopLeftRadius = 6; v.style.borderBottomLeftRadius = 6; v.style.borderTopRightRadius = 6; v.style.borderBottomRightRadius = 6;
    }

    /// <summary>얻은 것 알림: 왼쪽 가운데 (장부 쪽지와 겹치지 않게 화면 세로 중앙)</summary>
    void BuildToasts()
    {
        toastBox = new VisualElement { name = "toasts", pickingMode = PickingMode.Ignore };
        toastBox.style.position = Position.Absolute; toastBox.style.left = 12; toastBox.style.top = Length.Percent(42);
        root.Add(toastBox);
    }

    /// <summary>아래쪽 기술 줄: 가운데 아래에 무기 / E 천도 / R 파혼 / Q 끌어당김 / 피하기 충전 칸</summary>
    void BuildSkillBar()
    {
        skillBar = new VisualElement { name = "skillbar", pickingMode = PickingMode.Ignore };
        skillBar.style.position = Position.Absolute; skillBar.style.left = 0; skillBar.style.right = 0; skillBar.style.bottom = 14;
        skillBar.style.flexDirection = FlexDirection.Row; skillBar.style.justifyContent = Justify.Center;
        root.Add(skillBar);
        weaponLabel = Slot("무기"); Slot("E 천도"); Slot("R 파혼"); pullLabel = Slot("Q 끌어당김");
        // 피하기: 글자 + 충전 칸(켜진 칸 = 지금 쓸 수 있는 횟수)
        var d = new VisualElement { pickingMode = PickingMode.Ignore }; Panel(d);
        d.style.flexDirection = FlexDirection.Row; d.style.alignItems = Align.Center; d.style.marginLeft = 6;
        dodgeLabel = Line(d, 16); dodgeLabel.text = "Space 피하기 ";
        pips = new VisualElement[Mathf.Max(1, Balance.DODGE_CHARGES)];
        for (int i = 0; i < pips.Length; i++)
        {
            var p = new VisualElement { pickingMode = PickingMode.Ignore };
            p.style.width = 12; p.style.height = 12; p.style.marginLeft = 4; p.style.rotate = new Rotate(45f);
            d.Add(p); pips[i] = p;
        }
        skillBar.Add(d);
    }

    Label Slot(string text)
    {
        var s = new VisualElement { pickingMode = PickingMode.Ignore }; Panel(s); s.style.marginLeft = 6;
        var l = Line(s, 16); l.text = text; skillBar.Add(s);
        return l;
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
        RefreshSkillBar(); RefreshToasts(); RefreshEdges();
        hpFill.style.width = Length.Percent(Hud.HpRatio * 100f);
        hpFill.style.backgroundColor = Hud.HpLow ? new Color(0.9f, 0.3f, 0.3f) : new Color(0.72f, 0.82f, 0.95f);
    }

    void RefreshSkillBar()
    {
        weaponLabel.text = "무기 " + Hud.WeaponName;
        pullLabel.text = Hud.PullCd > 0.05f ? "Q 끌어당김 " + Mathf.CeilToInt(Hud.PullCd) + "s" : "Q 끌어당김";
        pullLabel.style.opacity = Hud.PullCd > 0.05f ? 0.5f : 1f;
        for (int i = 0; i < pips.Length; i++)
        {
            float fill = Mathf.Clamp01(Hud.DodgeCharges - i);   // 충전 중인 칸은 흐리게 차오른다
            pips[i].style.backgroundColor = Color.Lerp(new Color(1, 1, 1, 0.15f), new Color(0.72f, 0.9f, 1f, 1f), fill);
        }
    }

    /// <summary>알림 줄이 바뀐 때만 다시 만든다(나이에 따라 서서히 투명해짐)</summary>
    void RefreshToasts()
    {
        var sb = new System.Text.StringBuilder();
        foreach (var t in Hud.Toasts.Items) sb.Append(ToastStack.Line(t)).Append('|');
        string key = sb.ToString();
        if (key != lastToasts)
        {
            lastToasts = key; toastBox.Clear();
            foreach (var t in Hud.Toasts.Items) { var v = new VisualElement { pickingMode = PickingMode.Ignore }; Panel(v); v.style.marginBottom = 3; Line(v, 18).text = ToastStack.Line(t); toastBox.Add(v); }
        }
        for (int i = 0; i < Hud.Toasts.Items.Count && i < toastBox.childCount; i++)
            toastBox[i].style.opacity = Mathf.Clamp01((ToastStack.Life - Hud.Toasts.Items[i].Age) / 0.5f);   // 마지막 0.5초에 사라짐
    }

    /// <summary>
    /// 가장자리 경고: 시야 밖에서 공격을 준비하는 적의 방향에 붉은 마름모를 띄운다.
    /// 위치는 화면 비율(%)이라 해상도·UI 배율이 달라도 맞는다. 표시는 미리 만들어 둔 것을 재사용(매 프레임 새로 만들면 느려진다).
    /// </summary>
    void RefreshEdges()
    {
        int n = Hud.Edges.Count;
        while (edgePool.Count < n)
        {
            var v = new VisualElement { pickingMode = PickingMode.Ignore };
            v.style.position = Position.Absolute; v.style.width = 26; v.style.height = 26;
            v.style.marginLeft = -13; v.style.marginTop = -13;           // 가운데 기준으로 놓는다
            v.style.rotate = new Rotate(45f);
            v.style.backgroundColor = new Color(0.95f, 0.18f, 0.15f, 0.9f);
            root.Add(v); edgePool.Add(v);
        }
        float pulse = 0.65f + 0.35f * Mathf.Sin(Time.unscaledTime * 14f);   // 빠르게 깜박여 눈에 띄게
        for (int i = 0; i < edgePool.Count; i++)
        {
            var v = edgePool[i];
            if (i >= n) { v.style.display = DisplayStyle.None; continue; }
            v.style.display = DisplayStyle.Flex;
            v.style.left = Length.Percent(Hud.Edges[i].Nx * 100f);
            v.style.top = Length.Percent(Hud.Edges[i].Ny * 100f);
            v.style.opacity = pulse;
        }
    }
}
