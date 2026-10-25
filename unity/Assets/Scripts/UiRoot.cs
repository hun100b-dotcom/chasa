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
    VisualElement ringBox, ringMarker, note;   // 시각 고리: 바탕 원 / 해·달 표시
    string lastToasts;
    VisualElement vitalClip, vitalFillImg, slotBar; VisualElement[] slotBox = new VisualElement[0], slotIcon = new VisualElement[0], slotCool = new VisualElement[0]; Label[] slotKey = new Label[0], slotSec = new Label[0];
    bool artRing;   // 아트 시각 고리 틀이 있나(없으면 옛 눈금 고리로 대신 그린다)
    float ringSize = 84f;   // 시각 고리 지름(px, 1280×720 기준). 아트 틀이 있으면 키운다
    string lastLedger, lastVital, lastNight;
    float hpFullW = 304f;   // 체력 채움의 전체 폭(틀 안 홈 길이)
    static float U(float specPx) { return specPx * (Ko.TouchUI ? 0.5f : 2f / 3f); }   // 명세 px(1080p) → 패널 단위(1280×720 기준)

    static readonly Color PaperBg = new Color(0.05f, 0.05f, 0.09f, 0.62f);
    static readonly Color Ink = new Color(1f, 1f, 1f, 0.92f);

    void Start()
    {
        // 화면 설정(PanelSettings): 1280×720 기준으로 크기를 맞춘다. 파일 없이 코드로 만든다
        var ps = ScriptableObject.CreateInstance<PanelSettings>();
        ps.scaleMode = PanelScaleMode.ScaleWithScreenSize;
        ps.referenceResolution = Ko.TouchUI ? new Vector2Int(960, 540) : new Vector2Int(1280, 720);   // 폰은 기준을 작게 잡아 HUD 를 1.33배 크게(기획: 폰 글자 ×1.25 이상)
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

        // 좌상(기획 표준): 초상 + 체력 막대, 그 아래 장부 글자. 기준 해상도가 1280×720 이라 명세 px(1080p)에 U=2/3 를 곱한다
        note = new VisualElement { name = "ledger-note", pickingMode = PickingMode.Ignore };
        note.style.position = Position.Absolute; note.style.left = U(24); note.style.top = U(24);
        root.Add(note);
        var head = new VisualElement { pickingMode = PickingMode.Ignore }; head.style.flexDirection = FlexDirection.Row; note.Add(head);
        bool artHud = UiTex("hud_hp_frame") != null && UiTex("hud_portrait_frame") != null;
        if (artHud)
        {
            var pf = new VisualElement { pickingMode = PickingMode.Ignore }; pf.style.width = U(88); pf.style.height = U(88);
            var pc = Img("hud_portrait_chasa", U(72), U(72)); pc.style.position = Position.Absolute; pc.style.left = U(8); pc.style.top = U(8);
            var pr = Img("hud_portrait_frame", U(88), U(88)); pr.style.position = Position.Absolute; pr.style.left = 0; pr.style.top = 0;
            pf.Add(pc); pf.Add(pr); head.Add(pf);
            var col = new VisualElement { pickingMode = PickingMode.Ignore }; col.style.marginLeft = U(8); col.style.justifyContent = Justify.Center; head.Add(col);
            var bar = Img("hud_hp_frame", U(288), U(26)); bar.name = "vitals";
            hpFullW = U(280);
            var ghost = Img("hud_hp_fill_loss", hpFullW, U(18)); ghost.style.position = Position.Absolute; ghost.style.left = U(4); ghost.style.top = U(4);
            vitalClip = new VisualElement { pickingMode = PickingMode.Ignore };
            vitalClip.style.position = Position.Absolute; vitalClip.style.left = U(4); vitalClip.style.top = U(4); vitalClip.style.height = U(18); vitalClip.style.width = hpFullW; vitalClip.style.overflow = Overflow.Hidden;
            vitalFillImg = Img("hud_hp_fill", hpFullW, U(18));
            vitalClip.Add(vitalFillImg); bar.Add(ghost); bar.Add(vitalClip);
            col.Add(bar);
            vital = Line(col, 15); vital.style.marginTop = 4;
            hpFill = null;
        }
        else
        {
            vital = Line(head, 18);
            var bar = new VisualElement { name = "vitals", pickingMode = PickingMode.Ignore };
            bar.style.height = 8; bar.style.width = 200; bar.style.backgroundColor = new Color(0, 0, 0, 0.55f);
            hpFill = new VisualElement { pickingMode = PickingMode.Ignore };
            hpFill.style.height = 8; hpFill.style.backgroundColor = new Color(0.72f, 0.82f, 0.95f);
            bar.Add(hpFill); note.Add(bar);
        }
        // 장부·밤 글자: 배경 위에서도 읽히게 짙은 반투명 판 위에 둔다
        var texts = new VisualElement { pickingMode = PickingMode.Ignore }; texts.style.marginTop = 6; Panel(texts); note.Add(texts);
        ledger = Line(texts, 15); night = Line(texts, 15);
        BuildToasts(); BuildSkillBar(); BuildSlots(); BuildTimeRing();
    }

    // ---- 아트팀 UI 그림(Resources/Sprites/ui). 없으면 null 이라 부르는 쪽이 옛 색 도형으로 대신 그린다(그림 없이도 돈다)
    static Texture2D UiTex(string n) { return SpriteLib.Texture("ui/" + n); }
    static void SetImg(VisualElement v, string n) { var t = UiTex(n); if (t != null) v.style.backgroundImage = Background.FromTexture2D(t); }
    static VisualElement Img(string n, float w, float h)
    {
        var v = new VisualElement { pickingMode = PickingMode.Ignore };
        v.style.width = w; v.style.height = h; SetImg(v, n); return v;
    }

    /// <summary>도술 이름 → 아이콘 이름. 갈래별 액티브 순서(부름 청록·줄 사슬·얼룩 보라)가 아트 파일 번호 1~5와 같다</summary>
    public static string SkillIcon(string name)
    {
        var node = SkillTree.Find(name); if (node == null) return null;
        int n = 0;
        foreach (var k in SkillTree.All) { if (k.Branch != node.Branch || !k.Active) continue; n++; if (k.Name == name) break; }
        string br = node.Branch == Branch.Call ? "bureum" : node.Branch == Branch.Chain ? "jul" : "eolluk";
        return "icon_skill_" + br + "_" + n;
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
        toastBox.style.position = Position.Absolute; toastBox.style.left = U(24); toastBox.style.bottom = U(140); toastBox.style.flexDirection = FlexDirection.Column;
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

    // ---- 스킬바 8칸(기획 표준 v1.1): [Q 견인][1][2][3][4][E 천도][R 파혼][H 회복약], 칸 64px·간격 8px·아래 40px ------------
    const int BarN = 8;
    VisualElement[] bSlot = new VisualElement[BarN], bIcon = new VisualElement[BarN], bShade = new VisualElement[BarN]; Label[] bKey = new Label[BarN], bTxt = new Label[BarN], bSec = new Label[BarN];
    VisualElement[] bPips = new VisualElement[0]; float pullMax = 1f; VisualElement bPipRow; Label bWeapon;
    static readonly string[] BarKeys = { "Q", "1", "2", "3", "4", "E", "R", "H" };
    static readonly string[] BarNames = { "견인", "", "", "", "", "천도", "파혼", "약" };

    void BuildSlots()
    {
        if (UiTex("hud_slot_normal") == null) return;   // 그림 없으면 옛 기술 줄(skillBar)만 쓴다
        slotBar = new VisualElement { name = "skill-slots", pickingMode = PickingMode.Ignore };
        slotBar.style.position = Position.Absolute; slotBar.style.left = 0; slotBar.style.right = 0; slotBar.style.bottom = U(40 - 4);
        slotBar.style.alignItems = Align.Center;
        root.Add(slotBar);
        // 회피 충전 점(스킬바 바로 위 가운데) + 무기 이름
        bPipRow = new VisualElement { pickingMode = PickingMode.Ignore }; bPipRow.style.flexDirection = FlexDirection.Row; bPipRow.style.alignItems = Align.Center; bPipRow.style.marginBottom = U(6);
        bWeapon = Line(bPipRow, 14); bWeapon.style.marginRight = 10;
        bPips = new VisualElement[Mathf.Max(1, Balance.DODGE_CHARGES)];
        for (int i = 0; i < bPips.Length; i++) { var p = Img("hud_dodge_pip_empty", U(14), U(14)); p.style.marginLeft = 3; p.style.marginRight = 3; bPipRow.Add(p); bPips[i] = p; }
        var sp = Line(bPipRow, 14); sp.text = "Space 피하기"; sp.style.marginLeft = 8; sp.style.opacity = 0.8f;
        slotBar.Add(bPipRow);
        var row = new VisualElement { pickingMode = PickingMode.Ignore }; row.style.flexDirection = FlexDirection.Row; slotBar.Add(row);
        for (int i = 0; i < BarN; i++)
        {
            var b = Img("hud_slot_normal", U(72), U(72)); b.style.marginLeft = U(4); b.style.marginRight = U(4);   // 그림자 4px 포함 72 → 칸 64 + 간격 8
            var ic = new VisualElement { pickingMode = PickingMode.Ignore }; ic.style.position = Position.Absolute; ic.style.left = U(8); ic.style.top = U(8); ic.style.width = U(56); ic.style.height = U(56);
            var shade = new VisualElement { pickingMode = PickingMode.Ignore };   // 쿨타임 어둠 판: 아래에서부터 남은 비율만큼 덮는다
            shade.style.position = Position.Absolute; shade.style.left = U(4); shade.style.right = U(8); shade.style.bottom = U(8); shade.style.height = 0; shade.style.backgroundColor = new Color(0f, 0f, 0.03f, 0.62f);
            var key = Line(b, 14); key.text = BarKeys[i]; key.style.position = Position.Absolute; key.style.left = U(8); key.style.top = U(4);
            var txt = Line(b, 17); txt.text = BarNames[i]; txt.style.position = Position.Absolute; txt.style.left = 0; txt.style.right = U(4); txt.style.top = U(24); txt.style.unityTextAlign = TextAnchor.MiddleCenter;
            var sec = Line(b, 20); sec.style.position = Position.Absolute; sec.style.left = 0; sec.style.right = U(4); sec.style.top = U(22); sec.style.unityTextAlign = TextAnchor.MiddleCenter;
            b.Insert(0, ic); b.Insert(1, shade);
            row.Add(b); bSlot[i] = b; bIcon[i] = ic; bShade[i] = shade; bKey[i] = key; bTxt[i] = txt; bSec[i] = sec;
        }
    }

    void SetSlot(int i, bool enabled, float cd, float sec, string iconName)
    {
        var t = iconName != null ? UiTex(iconName) : null;
        bIcon[i].style.backgroundImage = t != null ? new StyleBackground(Background.FromTexture2D(t)) : new StyleBackground(StyleKeyword.None);
        bTxt[i].style.display = t == null ? DisplayStyle.Flex : DisplayStyle.None;   // 아이콘이 없는 칸(견인·천도·파혼·약)은 글자로
        bSlot[i].style.opacity = enabled ? 1f : 0.4f;
        bShade[i].style.height = cd > 0f ? U(56) * Mathf.Clamp01(cd) : 0f;
        bSec[i].text = sec > 0.05f ? Mathf.CeilToInt(sec).ToString() : "";
    }

    void RefreshSlots()
    {
        if (slotBar == null) return;
        slotBar.style.display = Ko.TouchUI ? DisplayStyle.None : DisplayStyle.Flex;   // 폰은 터치 버튼이 맡는다
        if (Ko.TouchUI) return;
        pullMax = Mathf.Max(pullMax, Hud.PullCd);
        SetSlot(0, true, Hud.PullCd > 0.05f ? Hud.PullCd / pullMax : 0f, Hud.PullCd, null);
        for (int i = 0; i < 4; i++)
        {
            var sv = Hud.Slots[i]; bool has = sv.Name != null;
            SetSlot(1 + i, has, has ? sv.Cd : 0f, has ? sv.CdSec : 0f, has ? SkillIcon(sv.Name) : null);
            bTxt[1 + i].text = "";
        }
        SetSlot(5, true, 0f, 0f, null); SetSlot(6, true, 0f, 0f, null);
        SetSlot(7, Hud.Heal > 0, 0f, 0f, null); bTxt[7].text = "약 " + Hud.Heal;
        bWeapon.text = "무기 " + Hud.WeaponName + " (Tab)";
        for (int i = 0; i < bPips.Length; i++) SetImg(bPips[i], Hud.DodgeCharges - i >= 0.999f ? "hud_dodge_pip_full" : "hud_dodge_pip_empty");
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
        // 시계 고리는 미니맵 바로 아래(화면 px → 패널 단위로 환산: 패널은 1280×720 기준, 가로·세로 비율을 절반씩 섞는다)
        float refW = Ko.TouchUI ? 960f : 1280f, refH = Ko.TouchUI ? 540f : 720f; float pscale = Mathf.Sqrt((Screen.width / refW) * (Screen.height / refH));
        if (ringBox != null) { ringBox.style.top = MiniMap.BottomPx / Mathf.Max(0.1f, pscale) + 4f; ringBox.style.right = Mathf.Max(10f, 24f * Screen.height / 1080f) / Mathf.Max(0.1f, pscale); }
        skillBar.style.display = slotBar != null && !Ko.TouchUI ? DisplayStyle.None : DisplayStyle.Flex;   // 새 8칸 스킬바가 있으면 옛 줄은 폰에서만
        RefreshSkillBar(); RefreshSlots(); RefreshToasts(); RefreshEdges(); RefreshTimeRing(); RefreshPeace();
        if (hpFill != null)
        {
            hpFill.style.width = Length.Percent(Hud.HpRatio * 100f);
            hpFill.style.backgroundColor = Hud.HpLow ? new Color(0.9f, 0.3f, 0.3f) : new Color(0.72f, 0.82f, 0.95f);
        }
        else if (vitalClip != null)
        {
            vitalClip.style.width = hpFullW * Hud.HpRatio;   // 틀 안 홈 길이에 맞춰 자른다(그림이 찌그러지지 않게)
            vitalFillImg.style.unityBackgroundImageTintColor = Hud.HpLow ? new Color(1f, 0.45f, 0.4f) : Color.white;   // 위험하면 붉게
        }
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


    /// <summary>
    /// 시각 고리(기획 UI 밑그림): 12지시 해시계처럼 둘레에 눈금 12개, 해·달 표시가 둘레를 돈다. 동틀녘엔 붉게.
    /// 숫자 대신 '모양'으로 시간을 읽게 하려는 것(마을 평화 시간엔 이것만 보인다). 유니티 구버전에도 되도록 회전한 작은 막대로 눈금을 만든다.
    /// </summary>
    void BuildTimeRing()
    {
        ringBox = new VisualElement { name = "time-ring", pickingMode = PickingMode.Ignore };
        ringBox.style.position = Position.Absolute; ringBox.style.right = 14; ringBox.style.top = 64;
        artRing = UiTex("ui_time_ring_frame") != null;
        if (artRing) ringSize = 120f;   // 아트 틀은 구간 호가 그려져 있어 조금 크게 둔다
        ringBox.style.width = ringSize; ringBox.style.height = ringSize;
        ringBox.style.backgroundColor = PaperBg;
        float rad = ringSize / 2f;
        if (artRing)
        {
            // 아트 틀(동틀녘 붉음·낮 한지·해질녘 금·밤 남청 호가 이미 그려짐): 바탕·테두리·눈금 대신 그림 한 장 + 해·달 표시
            ringBox.style.backgroundColor = Color.clear; SetImg(ringBox, "ui_time_ring_frame");
            ringMarker = new VisualElement { pickingMode = PickingMode.Ignore };
            ringMarker.style.position = Position.Absolute; ringMarker.style.width = 22; ringMarker.style.height = 22;
            ringBox.Add(ringMarker); root.Add(ringBox);
            return;
        }
        ringBox.style.borderTopLeftRadius = rad; ringBox.style.borderTopRightRadius = rad; ringBox.style.borderBottomLeftRadius = rad; ringBox.style.borderBottomRightRadius = rad;
        var edge = new Color(1f, 1f, 1f, 0.3f);
        ringBox.style.borderTopWidth = 2; ringBox.style.borderBottomWidth = 2; ringBox.style.borderLeftWidth = 2; ringBox.style.borderRightWidth = 2;
        ringBox.style.borderTopColor = edge; ringBox.style.borderBottomColor = edge; ringBox.style.borderLeftColor = edge; ringBox.style.borderRightColor = edge;
        for (int i = 0; i < 12; i++)
        {
            float a = i * 30f * Mathf.Deg2Rad;
            bool top = i == 0;   // 꼭대기(한밤) 눈금만 굵고 길게
            var t = new VisualElement { pickingMode = PickingMode.Ignore };
            float w = top ? 4f : 2f, h = top ? 12f : 7f, r = rad - 2f - h / 2f - 2f;
            t.style.position = Position.Absolute; t.style.width = w; t.style.height = h;
            t.style.left = rad - 2f + Mathf.Sin(a) * r - w / 2f; t.style.top = rad - 2f - Mathf.Cos(a) * r - h / 2f;   // -2 는 테두리 두께
            t.style.rotate = new Rotate(i * 30f);
            t.style.backgroundColor = new Color(1f, 1f, 1f, top ? 0.8f : 0.4f);
            ringBox.Add(t);
        }
        ringMarker = new VisualElement { pickingMode = PickingMode.Ignore };
        ringMarker.style.position = Position.Absolute; ringMarker.style.width = 14; ringMarker.style.height = 14;
        ringMarker.style.borderTopLeftRadius = 7; ringMarker.style.borderTopRightRadius = 7; ringMarker.style.borderBottomLeftRadius = 7; ringMarker.style.borderBottomRightRadius = 7;
        ringBox.Add(ringMarker);
        root.Add(ringBox);
    }

    static readonly string[] MoonTex = { "moon_crescent", "moon_first_quarter", "moon_full", "moon_last_quarter" };

    void RefreshTimeRing()
    {
        float deg;
        if (Hud.ClockLabel != null)
        {
            // 흐르는 하루: 한밤(밤의 가운데)이 꼭대기, 시계 방향으로 돈다
            float midnight = (Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + Balance.CLOCK_DUSK_MIN + Balance.CLOCK_NIGHT_MIN * 0.5f) / WorldClock.DayLength;
            deg = Mathf.Repeat(Hud.TimeOfDay - midnight, 1f) * 360f;
        }
        else deg = Mathf.Lerp(-120f, 120f, Mathf.Clamp01(Hud.TimeOfDay));   // 옛 한 판: 해질녘 왼쪽 아래 → 동틀녘 오른쪽 아래
        if (artRing)
        {
            // 아트 틀: 해·달 표시는 틀 반지름 228/512 위를 돈다. 낮엔 해, 밤엔 달 그림(동틀녘엔 붉게 물들임)
            float aa = deg * Mathf.Deg2Rad, c = ringSize / 2f, rr = ringSize * 228f / 512f, ms = Hud.ClockLabel != null && Hud.Daylight < 0.5f && Hud.FullMoon ? 28f : 22f;
            ringMarker.style.width = ms; ringMarker.style.height = ms;
            ringMarker.style.left = c + Mathf.Sin(aa) * rr - ms / 2f; ringMarker.style.top = c - Mathf.Cos(aa) * rr - ms / 2f;
            bool sun = Hud.ClockLabel != null ? Hud.Daylight >= 0.5f : Hud.TimeOfDay < 0.0f;
            var mt = sun ? UiTex("ui_marker_sun") : (UiTex(MoonTex[Mathf.Clamp(Hud.MoonPhase, 0, 3)]) ?? UiTex("ui_marker_moon"));   // 밤엔 그날의 달 모양
            if (mt != null) ringMarker.style.backgroundImage = Background.FromTexture2D(mt);
            ringMarker.style.unityBackgroundImageTintColor = Hud.IsDawn ? new Color(1f, 0.55f, 0.5f) : Color.white;
            return;
        }
        float a = deg * Mathf.Deg2Rad, rad = ringSize / 2f, r = rad - 2f - 16f;
        float msz = Hud.ClockLabel != null && Hud.Daylight < 0.5f && Hud.FullMoon ? 20f : 14f;   // 보름달 밤엔 표시가 커진다
        ringMarker.style.width = msz; ringMarker.style.height = msz;
        ringMarker.style.left = rad - 2f + Mathf.Sin(a) * r - msz / 2f;   // 크기가 달라도 중심이 어긋나지 않게
        ringMarker.style.top = rad - 2f - Mathf.Cos(a) * r - msz / 2f;
        ringMarker.style.backgroundColor = Hud.IsDawn ? new Color(0.95f, 0.3f, 0.25f)
            : Hud.ClockLabel != null ? Color.Lerp(new Color(0.8f, 0.88f, 1f), new Color(1f, 0.85f, 0.45f), Hud.Daylight)   // 밤 달 청백 → 낮 해 금색
            : Color.Lerp(new Color(1f, 0.85f, 0.5f), new Color(0.8f, 0.88f, 1f), Mathf.Clamp01(Hud.TimeOfDay * 2f));
   // 노을 금색 → 달 청백
    }

    /// <summary>평화로운 낮: 장부·기술 줄을 서서히 걷어 시각 고리와 풍경만 남긴다(적이 가까워지면 곧바로 돌아온다)</summary>
    float peace = 1f;
    void RefreshPeace()
    {
        // 기획 표준: 체력·스킬바·미니맵은 처음부터 항상 보인다(예전의 '평화로운 낮 숨김'은 폐지)
        note.style.opacity = 1f; note.style.display = DisplayStyle.Flex;
        if (slotBar != null) slotBar.style.opacity = 1f;
    }
}
