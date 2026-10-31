// =============================================================================
// CharacterView.cs — 명부(C) 화면의 UI Toolkit 판. 설정 화면과 같은 방식(UiRoot 의 Overlay 에 판을 얹고, 바뀔 때만 다시 만든다).
// 왜 옮기나: IMGUI(OnGUI)는 폰 해상도·글자 배율을 따로 계산해야 하고 한 프레임마다 전부 다시 그려 느리다. UI Toolkit 은
//   UiRoot 와 같은 1280×720(폰 960×540) 기준 크기를 같이 쓴다. 규칙·수치는 그대로 Core/Growth.cs 가 쥐고 있고, 여기서는 보여 주고 누르게만 한다.
// 옛 세 탭(장비·도술·능력치, DEMO_PANEL 이 켜졌을 때만)은 아직 IMGUI 가 그린다. 명부·들은 말 두 탭만 이 판이 맡는다.
// ?ui2=0 이면 이 판을 끄고 옛 IMGUI 로 돌아간다.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;
using UnityEngine.UIElements;

public partial class CharacterPanel
{
    VisualElement view; bool viewDirty = true; int builtTab = -1, builtLog = -1;
    static readonly bool Ui2 = !(Application.absoluteURL ?? "").Contains("ui2=0");
    static readonly Color VInk = new Color32(0x1E, 0x1A, 0x17, 255), VSeal = new Color32(0xB5, 0x47, 0x3F, 255), VPaper = new Color(0.953f, 0.906f, 0.827f);

    /// <summary>확인용 장면(?scene=…)이 명부를 그 탭으로 연다(6 도술 · 7 장비 · 3 기록)</summary>
    public void PreviewOpen(int t) { if (!Open) Toggle(); tab = t; viewDirty = true; }   // Toggle 이 기록 탭으로 되돌리므로 탭은 그 뒤에 정한다

    /// <summary>이 판이 지금 그리는 중인가(그렇다면 IMGUI 는 건너뛴다)</summary>
    bool UseView { get { return Ui2 && view != null && tab >= 3; } }

    static Label VTxt(VisualElement p, string text, int size, Color c, bool bold = false)
    {
        var l = new Label(text) { pickingMode = PickingMode.Ignore };
        l.style.color = c; l.style.fontSize = size; l.style.whiteSpace = WhiteSpace.Normal;
        if (bold) l.style.unityFontStyleAndWeight = FontStyle.Bold;
        var f = Ko.GetFont(); if (f != null) l.style.unityFontDefinition = FontDefinition.FromFont(f);
        p.Add(l); return l;
    }

    Label VBtn(VisualElement p, string text, System.Action click, Color c, int size = 13, bool bgOn = false)
    {
        var b = VTxt(p, text, size, c); b.pickingMode = PickingMode.Position;
        b.style.paddingLeft = 4; b.style.paddingRight = 4; b.style.paddingTop = 3; b.style.paddingBottom = 3; b.style.marginBottom = 2;
        if (bgOn) b.style.backgroundColor = new Color(VInk.r, VInk.g, VInk.b, 0.14f);
        b.RegisterCallback<ClickEvent>(e => { UiSfx.Click(text); click(); viewDirty = true; });   // 눌림 소리(닫기·취소는 되돌림 소리)
        b.RegisterCallback<PointerEnterEvent>(e => b.style.color = VSeal);
        b.RegisterCallback<PointerLeaveEvent>(e => b.style.color = c);
        return b;
    }

    void UpdateView()
    {
        if (!Ui2) return;
        if (view == null)
        {
            var ov = judge != null && judge.ui != null ? judge.ui.Overlay : null; if (ov == null) return;
            view = new VisualElement { name = "character-view" }; view.style.position = Position.Absolute; view.style.left = 0; view.style.right = 0; view.style.top = 0; view.style.bottom = 0;
            view.style.alignItems = Align.Center; view.style.justifyContent = Justify.Center; view.style.display = DisplayStyle.None;
            view.style.backgroundColor = new Color(0f, 0f, 0f, 0.5f);   // 뒤 화면을 어둡게(눌림이 뒤로 새지 않게 이 판이 받는다)
            ov.Add(view);
        }
        bool show = Open && tab >= 3 && judge != null && judge.player != null;
        view.style.display = show ? DisplayStyle.Flex : DisplayStyle.None;
        if (!show) { viewDirty = true; return; }
        int logN = judge.npcs != null && judge.npcs.Log != null ? judge.npcs.Log.Items.Count : 0;
        if (viewDirty || builtTab != tab || builtLog != logN) { viewDirty = false; builtTab = tab; builtLog = logN; BuildView(); }
    }

    void BuildView()
    {
        view.Clear();
        if (tab == 5 && !judge.SealsTabOpen) tab = 3;   // 닫힌 탭에 머물러 있으면 기록으로
        var book = SpriteLib.Texture("ui/ui_book_page");
        bool bm = book != null;   // 세로 책 한 권: 모든 탭이 같은 한지 바탕을 쓴다
        var box = new VisualElement(); box.style.width = Length.Percent(96); box.style.maxWidth = 620; box.style.height = Length.Percent(94); box.style.maxHeight = 660;   // 가로 펼침 → 세로 한 권(좁고 길게). 폰 세로 화면에도 맞는다
        if (bm)
        {
            // 세로 책 한 쪽 그림(ui_book_page): 가장자리 56px(표지·금테·한지 끝)는 그대로, 가운데만 늘리는 9조각으로 쓴다.
            // 왜: 폰 세로처럼 비율이 많이 달라도 오른쪽·아래 금테가 잘리거나 가늘어지지 않는다(예전엔 가로 펼침 그림을 잘라 써서 오른쪽 금테가 잘렸다)
            box.style.backgroundImage = new StyleBackground(book);
            box.style.unitySliceLeft = 56; box.style.unitySliceRight = 56; box.style.unitySliceTop = 56; box.style.unitySliceBottom = 56;
            box.style.paddingLeft = 52; box.style.paddingRight = 48;   // 왼쪽은 책등 그림자(약 50px)를 피하고, 오른쪽은 한지 끝 안쪽
            box.style.paddingTop = 44; box.style.paddingBottom = 40;
        }
        else { box.style.backgroundColor = new Color(0.05f, 0.06f, 0.1f, 0.94f); box.style.paddingLeft = 16; box.style.paddingRight = 16; box.style.paddingTop = 12; box.style.paddingBottom = 12; }
        Color txt = bm ? VInk : VPaper, hi = bm ? VSeal : VPaper;
        // 탭 줄
        var tabs = new VisualElement { pickingMode = PickingMode.Position }; tabs.style.flexDirection = FlexDirection.Row; tabs.style.justifyContent = Justify.SpaceBetween;
        var left = new VisualElement { pickingMode = PickingMode.Position }; left.style.flexDirection = FlexDirection.Row;
        // 탭 다섯: 기록 · 도술 · 장비 · 들은 말 · 인(인은 만들 수 있게 된 뒤에만). 번호는 옛 탭과 겹치지 않게 6·7 을 새로 썼다
        foreach (int ti0 in new[] { 3, 6, 7, 4, 5 })
        {
            int ti = ti0; if (ti == 5 && !judge.SealsTabOpen) continue;   // 인 탭은 인을 만들 수 있게 된 뒤에만 보인다(성장 단계 공개)
            var t = VBtn(left, TabNames[ti] + (tab == ti ? " *" : ""), () => { if (tab != ti) Sfx.Play("sfx.ui.tab"); tab = ti; }, tab == ti ? hi : txt, 16); t.style.marginRight = 12;
        }
        tabs.Add(left); VBtn(tabs, "닫기", () => Open = false, txt, 16);
        box.Add(tabs);
        var body = new ScrollView(ScrollViewMode.Vertical); body.style.flexGrow = 1; body.style.marginTop = 8;
        if (tab == 3) BuildBook(body, txt, hi, bm, 0); else if (tab == 6) BuildBook(body, txt, hi, bm, 1); else if (tab == 7) BuildEquip(body, txt, hi); else if (tab == 5) BuildSeals(body, txt, hi, bm); else BuildHeard(body, txt, bm);
        NoShrink(body.contentContainer); box.Add(body);   // 세로 책: 줄이 많아도 서로 겹쳐 눌리지 않고 스크롤로 넘치게(도술 탭 확인 장면에서 갈래가 겹쳐 보였다)
        view.Add(box);
    }

    void BuildHeard(VisualElement p, Color txt, bool bm)
    {
        var log = judge.npcs != null ? judge.npcs.Log : null;
        if (log == null || log.Items.Count == 0) { VTxt(p, "아직 들은 말이 없다. 산 사람 곁에 가만히 서 있으면 들린다", 16, txt); return; }
        for (int i = log.Items.Count - 1; i >= 0; i--)   // 최근 것이 위
        {
            var e = log.Items[i]; bool clue = !string.IsNullOrEmpty(e.Clue);
            var row = new VisualElement { pickingMode = PickingMode.Ignore }; row.style.marginBottom = 8;
            var head = new VisualElement { pickingMode = PickingMode.Ignore }; head.style.flexDirection = FlexDirection.Row;
            if (clue) VTxt(head, "● ", 16, new Color(0.85f, 0.62f, 0.1f));   // 단서가 있는 말은 금색 점
            VTxt(head, e.Who + "  (" + SlotNames[Mathf.Clamp(e.Slot, 0, 3)] + " · " + e.Place + ")", 16, txt, true);
            row.Add(head); VTxt(row, e.Text, 15, txt); p.Add(row);
        }
    }

    /// <summary>part 0 = 기록 탭(품계·능력치·무기), part 1 = 도술 탭(갈래 나무·도술 칸)</summary>
    void BuildBook(VisualElement p, Color txt, Color hi, bool bm, int part)
    {
        var g = judge.growth;
        if (part == 0) {
        // 1) 품계 줄과 진행 막대
        int next = g.Rank >= GrowthState.MaxRank ? g.JudgeTally : GrowthState.TallyForRank(g.Rank + 1), cur = GrowthState.TallyForRank(g.Rank);
        float frac = g.Rank >= GrowthState.MaxRank ? 1f : Mathf.Clamp01((g.JudgeTally - cur) / (float)Mathf.Max(1, next - cur));
        var r1 = new VisualElement { pickingMode = PickingMode.Ignore }; r1.style.flexDirection = FlexDirection.Row; r1.style.justifyContent = Justify.SpaceBetween;
        VTxt(r1, "품계 " + g.Rank + " · " + Ko.RankTitle(g.Rank) + "   명부의 일 " + g.JudgeTally + (g.Rank >= GrowthState.MaxRank ? "" : " / " + next), 18, hi, true);
        VTxt(r1, "도술 점수 " + g.SkillPointsFree + (g.StainPointsFree > 0 ? " (+얼룩 전용 " + g.StainPointsFree + ")" : "") + "   능력치 점수 " + g.StatPointsFree, 14, txt);
        p.Add(r1);
        var bar = new VisualElement { pickingMode = PickingMode.Ignore }; bar.style.height = 8; bar.style.marginTop = 4; bar.style.marginBottom = 10; bar.style.backgroundColor = new Color(VInk.r, VInk.g, VInk.b, 0.18f);
        var fill = new VisualElement { pickingMode = PickingMode.Ignore }; fill.style.height = Length.Percent(100); fill.style.width = Length.Percent(frac * 100f); fill.style.backgroundColor = bm ? VSeal : new Color(0.45f, 0.78f, 0.82f);
        bar.Add(fill); p.Add(bar);
        // 2) 능력치 4종(점수가 있으면 + 버튼)
        var r2 = new VisualElement { pickingMode = PickingMode.Position }; r2.style.flexDirection = FlexDirection.Row; r2.style.marginBottom = 10;
        for (int i = 0; i < GrowthState.StatNames.Length; i++)
        {
            int si = i; var cell = new VisualElement { pickingMode = PickingMode.Position }; cell.style.flexDirection = FlexDirection.Row; cell.style.width = Length.Percent(25);
            VTxt(cell, GrowthState.StatNames[i] + " " + g.Stats[i], 16, txt);
            if (g.StatPointsFree > 0) { var b = VBtn(cell, " + ", () => { g.AddStat(si); judge.RefreshGrowth(); }, hi, 18, true); b.style.marginLeft = 8; }
            r2.Add(cell);
        }
        p.Add(r2);
        }
        if (part == 1) {
        // 3) 도술 세 갈래(세 열). 설명은 아래 한 줄에 마우스를 올린 것을 보여 준다
        var desc = new Label(); desc.pickingMode = PickingMode.Ignore;
        string idle = "도술을 누르면 점수 1을 써서 배운다(배운 쓰는 도술은 누르면 칸에 올리고 내림). [쓰는] 눌러 쓰는 도술 · [늘] 늘 켜진 도술(2단계) *=깊은 도술(그 갈래 " + SkillTree.DeepNeeds + "점 이상)";
        bool treeOpen = judge.SkillTreeOpen;
        var cols = new VisualElement { pickingMode = PickingMode.Position }; cols.style.flexDirection = FlexDirection.Column;   // 세로 책: 세 갈래를 위에서 아래로
        for (int b = 0; b < 3; b++)
        {
            var br = (Branch)b; var col = new VisualElement { pickingMode = PickingMode.Position }; col.style.marginBottom = 10;
            VTxt(col, SkillTree.BranchName(br) + " 갈래  (" + g.BranchPoints(br) + "점)", 16, hi, true);
            foreach (var n in SkillTree.All)
            {
                if (n.Branch != br) continue;
                if (!treeOpen && g.LevelOf(n.Name) == 0) continue;   // 나무가 닫혀 있는 동안은 배운 도술만 보인다(성장 단계 공개)
                var node = n; int lv = g.LevelOf(n.Name); bool can = g.CanLearn(n.Name); bool locked = n.Deep && g.BranchPoints(br) < SkillTree.DeepNeeds;
                int barAt = n.Active ? g.ActiveBar.IndexOf(n.Name) : -1;
                string label = (n.Active ? (barAt >= 0 ? "[" + (barAt + 1) + "칸] " : "[쓰는] ") : "[늘] ") + (n.Deep ? "*" : "") + n.Name + "  " + lv + "/" + n.MaxLevel + (locked ? "  잠김" : "");
                var c = lv > 0 ? txt : new Color(txt.r, txt.g, txt.b, can ? 0.9f : 0.45f);
                // 도술 그림 자리: 그림이 있으면 [그림 24px][글자 칸]을 한 줄(가로 배치)로 묶어 줄 간격이 흐트러지지 않게 한다.
                // 그림이 없으면(null) 줄을 만들지 않고 옛 모양 그대로 글자만 갈래 열에 바로 붙인다(안전장치)
                VisualElement btParent = col;
                var ico = UiRoot.DosulArt(n.Name);
                if (ico != null)
                {
                    var row = new VisualElement { pickingMode = PickingMode.Ignore };
                    row.style.flexDirection = FlexDirection.Row; row.style.alignItems = Align.Center; row.style.minHeight = 26;
                    var img = new VisualElement { pickingMode = PickingMode.Ignore };
                    img.style.width = 24; img.style.height = 24; img.style.flexShrink = 0; img.style.marginRight = 4;   // 크기 고정: 줄어들어 찌그러지지 않게
                    img.style.backgroundImage = new StyleBackground(ico);
                    img.style.opacity = lv > 0 ? 1f : (can ? 0.8f : 0.4f);   // 안 배운 도술은 흐리게(글자 색과 같은 규칙)
                    row.Add(img); col.Add(row); btParent = row;
                }
                var bt = VBtn(btParent, label, () =>
                {
                    if (node.Active && g.LevelOf(node.Name) > 0) g.ToggleBar(node.Name);   // 배운 액티브는 칸에 올렸다 내렸다
                    else if (!treeOpen) { }                                                   // 나무가 닫혀 있으면 점수는 카드로만 쓴다
                    else { g.Learn(node.Name); judge.RefreshGrowth(); }                     // 배우면 패시브 효과가 바로 붙는다
                }, c, 13, barAt >= 0);
                bt.RegisterCallback<PointerEnterEvent>(e => { string fl = ItemTexts.Skill(node.Name); desc.text = node.Name + ": " + node.Desc + (fl.Length > 0 ? "\n" + fl : ""); });
                bt.RegisterCallback<PointerLeaveEvent>(e => desc.text = idle);
            }
            cols.Add(col);
        }
        p.Add(cols);
        if (!treeOpen)
        {
            // 닫힌 동안의 안내: 왜 안 보이는지, 언제 열리는지(막막함 대신 다음 목표를 준다)
            int picked = Mathf.Min(DosulCards.Rounds, g.SkillPointsSpent);
            VTxt(p, "도술 갈래 나무는 아직 접혀 있다. 도술 카드를 " + DosulCards.Rounds + "번 고르고 여섯째 점수를 얻으면 펼쳐진다 (지금 " + picked + "/" + DosulCards.Rounds + ")", 13, txt).style.marginTop = 6;
        }
        // 4) 설명 한 줄 + 액티브 칸 + 무기 두 자루
        desc.text = idle; desc.style.color = txt; desc.style.fontSize = 13; desc.style.whiteSpace = WhiteSpace.Normal; desc.style.marginTop = 8;
        var kf = Ko.GetFont(); if (kf != null) desc.style.unityFontDefinition = FontDefinition.FromFont(kf);
        p.Add(desc);
        string bar4 = ""; for (int i = 0; i < SkillTree.ActiveSlots; i++) bar4 += "[" + (i + 1) + ": " + (i < g.ActiveBar.Count ? g.ActiveBar[i] : "빈 칸") + "]  ";
        VTxt(p, "도술 칸  " + bar4, 13, txt).style.marginTop = 4;
        }
        if (part == 0) {
        var lo = judge.player.loadout;
        for (int row = 0; row < 2; row++)
        {
            bool hand = row == 0; var line = new VisualElement { pickingMode = PickingMode.Position }; line.style.flexDirection = FlexDirection.Row; line.style.flexWrap = Wrap.Wrap; line.style.alignItems = Align.Center;
            var tag = VTxt(line, hand ? "손에 든" : "등에 멘", 13, txt); tag.style.width = 60;
            for (int i = 0; i < Loadout.AllWeapons.Length; i++)
            {
                var wid = Loadout.AllWeapons[i]; bool held = (hand ? lo.weapon : lo.other) == wid;
                var wb = VBtn(line, (held ? "● " : "") + WeaponDef.Get(wid).Name, () => { if (hand) lo.SetHand(wid); else lo.SetBack(wid); }, txt, 13, held); wb.style.marginRight = 10;
            }
            p.Add(line);
        }
        VTxt(p, "지금 든 " + lo.Def.Name + " — " + lo.Def.Taste, 13, txt);
        }
    }

    /// <summary>장비 탭: 여덟 자리를 위에서 아래로. 닫힌 자리는 흐리게 '잠김 — 언제 열리는지'를 보여 앞으로 늘어날 것을 알린다(성장 단계 공개)</summary>
    void BuildEquip(VisualElement p, Color txt, Color hi)
    {
        var lo = judge.player.loadout;
        VTxt(p, "열린 자리 " + GrowthReveal.OpenEquipCount(lo.gear.FirstRingBossDone, lo.gear.Act2Entered) + " / " + Ko.PosOrder.Length, 16, hi, true).style.marginBottom = 8;
        foreach (var pos in Ko.PosOrder)
        {
            var it = lo.gear.GetAt(pos);
            var row = new VisualElement { pickingMode = PickingMode.Ignore }; row.style.marginBottom = 8;
            if (!lo.gear.IsOpen(pos))
            {
                var l = VTxt(row, Ko.PosName(pos) + ": 잠김 — " + GrowthReveal.EquipUnlockHint(pos), 15, txt); l.style.opacity = 0.5f;
            }
            else if (it == null) VTxt(row, Ko.PosName(pos) + ": (비어 있음)", 15, txt);
            else
            {
                VTxt(row, Ko.PosName(pos) + ": " + Ko.ItemName(it, Ko.FamilyOf(pos, lo)) + (it.Gradient ? "  [기울기 " + Ko.TiltName(it) + "]" : ""), 15, txt, true);
                string opts = ""; foreach (var o in it.Options) opts += OptText(o) + "   ";
                if (opts.Length > 0) VTxt(row, opts, 13, txt);
            }
            p.Add(row);
        }
    }

    /// <summary>스크롤 안 줄들이 칸이 모자라다고 찌그러져 겹치지 않게, 아래 모든 칸의 줄어듦을 끈다</summary>
    static void NoShrink(VisualElement e) { foreach (var c in e.Children()) { c.style.flexShrink = 0; NoShrink(c); } }
}
