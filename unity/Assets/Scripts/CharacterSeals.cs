// =============================================================================
// CharacterSeals.cs — 인물 창의 "인" 탭 (기획 hud-controls-spec §8): 넋 지갑 · 인 박기/빼기 · 인 만들기.
// 규칙은 전부 Core(SoulWallet·Seal·SealEffects)가 쥐고, 여기는 보여 주고 누르게만 한다.
//  - 박기·빼기: 싸움 밖(10m 안에 깨어 있는 혼이 없을 때)이면 어디서나. 빼면 인은 가방으로 돌아온다(잃지 않음)
//  - 만들기: 서낭당 곁에서만. 버튼을 0.6초 누르고 있어야 만들어진다(잘못 누름 방지, 확인 창 없음)
// 지금은 글자 버튼 위주의 첫 판이다(칸 아이콘·끌어다 놓기·툴팁은 아트 인 그림 연결 때 얹는다).
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;
using UnityEngine.UIElements;
using CSeal = Chasa.Core.Seal;   // CharacterPanel 에 Seal(붉은 인 색)이라는 이름이 이미 있어 별명을 쓴다

public partial class CharacterPanel
{
    int selBagSeal = -1;                       // 가방에서 고른 인(없으면 -1)
    string holdKey; float holdT; Label holdLabel; string holdText;   // 만들기 누르고 있기
    readonly string[] colorMark = { "나무", "흙", "물", "불", "쇠" };   // 색만으로 구분하지 않게 모양 이름도 함께(청·황·흑·적·백 순서 = SoulColor)

    static string ColorShort(SoulColor c) { switch (c) { case SoulColor.Blue: return "청"; case SoulColor.Yellow: return "황"; case SoulColor.Black: return "흑"; case SoulColor.Red: return "적"; default: return "백"; } }
    static string SealLabel(CSeal s) { return SealEffects.Name(s) + " (" + ColorShort(s.A) + (s.Mono ? "" : "+" + ColorShort(s.B)) + ")"; }

    /// <summary>10m 안에 깨어 있는 혼이 있으면 박기·빼기가 잠긴다(서낭당 쉬기와 같은 거리)</summary>
    bool SealLocked()
    {
        var p = judge.player.Pos; float r2 = Balance.SHRINE_REST_BLOCK_M * Balance.SHRINE_REST_BLOCK_M;
        foreach (var x in judge.enemies.list) if (x.alive && (x.Pos - p).sqrMagnitude < r2) return true;
        return false;
    }

    void AfterSealChange(Loadout lo) { lo.Refresh(); judge.ledger.SetMaxHp(lo.stats.MaxHp); Sfx.Play("sfx.ui.confirm"); }

    void BuildSeals(VisualElement p, Color txt, Color hi, bool bm)
    {
        var lo = judge.player.loadout;
        bool locked = SealLocked(), atShrine = judge.AtShrine;
        // 1) 넋 지갑: 품계용 넋과 따로 센다(천도한 혼 구역의 빛깔로 쌓임)
        VTxt(p, "넋 지갑", 18, txt, true);
        var wr = new VisualElement { pickingMode = PickingMode.Ignore }; wr.style.flexDirection = FlexDirection.Row; wr.style.flexWrap = Wrap.Wrap; wr.style.marginBottom = 8;
        for (int i = 0; i < 5; i++) { var c = (SoulColor)i; var l = VTxt(wr, ColorShort(c) + "(" + colorMark[i] + ") " + lo.wallet.Get(c), 16, txt); l.style.marginRight = 16; }
        p.Add(wr);
        // 2) 장비 홈: 박힌 인을 누르면 가방으로, 빈 홈을 누르면 고른 인이 박힌다
        VTxt(p, "장비 홈" + (locked ? "  (싸움이 끝나면 바꿀 수 있다)" : ""), 18, txt, true);
        bool anyItem = false;
        foreach (var pos in Ko.PosOrder)
        {
            var it = lo.gear.GetAt(pos);
            if (it == null || !EquipLayout.CanHoldSeal(pos)) continue;
            anyItem = true;
            var row = new VisualElement { pickingMode = PickingMode.Position }; row.style.flexDirection = FlexDirection.Row; row.style.flexWrap = Wrap.Wrap; row.style.alignItems = Align.Center;
            var nm = VTxt(row, Ko.PosName(pos) + ": " + Ko.ItemName(it, Ko.FamilyOf(pos, lo)) + (it.Sockets == 0 ? "  (홈 없음)" : ""), 15, txt); nm.style.marginRight = 8;
            var itc = it; var posc = pos;
            for (int si = 0; si < it.Sockets; si++)
            {
                int sIdx = si;
                if (si < it.Seals.Count)
                {
                    var sl = it.Seals[si];
                    VBtn(row, "[" + SealLabel(sl) + " · " + SealEffects.Describe(sl) + "]", () =>
                    {
                        if (locked) { Sfx.Play("sfx.ui.deny"); return; }
                        itc.Seals.RemoveAt(sIdx); lo.sealBag.Add(sl); AfterSealChange(lo);   // 빼도 인은 잃지 않는다
                    }, txt, 14, true);
                }
                else
                {
                    VBtn(row, selBagSeal >= 0 && !locked ? "[빈 홈 — 여기에 박기]" : "[빈 홈]", () =>
                    {
                        if (locked || selBagSeal < 0 || selBagSeal >= lo.sealBag.Count) { Sfx.Play("sfx.ui.deny"); return; }
                        if (lo.InsertSeal(posc, selBagSeal)) { selBagSeal = -1; AfterSealChange(lo); }
                    }, hi, 14, true);
                }
            }
            p.Add(row);
        }
        if (!anyItem) VTxt(p, "인 홈이 있는 장비가 아직 없다 (손본 장비 1홈 · 귀한 장비 2홈)", 14, txt);
        // 3) 인 가방
        var gap = new VisualElement { pickingMode = PickingMode.Ignore }; gap.style.height = 8; p.Add(gap);
        VTxt(p, "인 가방" + (lo.sealBag.Count > 0 ? "  (고르고 빈 홈을 누른다)" : ""), 18, txt, true);
        if (lo.sealBag.Count == 0) VTxt(p, "만들어 둔 인이 없다", 14, txt);
        for (int i = 0; i < lo.sealBag.Count; i++)
        {
            int bi = i; var sl = lo.sealBag[i];
            VBtn(p, (selBagSeal == i ? "▶ " : "") + (sl.Large ? "큰 " : "") + SealLabel(sl) + " · " + SealEffects.Describe(sl), () => selBagSeal = selBagSeal == bi ? -1 : bi, selBagSeal == i ? hi : txt, 14, selBagSeal == i);
        }
        if (selBagSeal >= 0 && selBagSeal < lo.sealBag.Count)
        {
            // 고른 인의 세계관 문장(서사): 기능 문구 아래 흐린 글씨
            string fl = ItemTexts.Seal(SealEffects.Name(lo.sealBag[selBagSeal]));
            if (fl.Length > 0) VTxt(p, fl, 13, new Color(txt.r, txt.g, txt.b, 0.6f));
        }
        // 4) 인 조합표: 오방색(다섯 빛깔) 두 개를 짝지어 15종. 서낭당 밖에서도 볼 수 있고, 만들기는 서낭당 곁에서만 된다
        var gap2 = new VisualElement { pickingMode = PickingMode.Ignore }; gap2.style.height = 8; p.Add(gap2);
        BuildSealMatrix(p, lo, txt, hi, atShrine);
    }

    int selKind = -1;   // 조합표에서 고른 칸(0~14, 없으면 -1). 15종 = 빛깔 A<=B 쌍을 순서대로 센 번호

    /// <summary>
    /// 인 조합표(5x5 삼각형) + 고른 인의 설명/만들기.
    /// 왜 표인가? 15종을 글자 줄로 늘어놓으면 "어느 빛깔 둘이 무슨 인이 되는지"가 한눈에 안 들어온다.
    /// 행·열이 빛깔이라 짝이 곧 칸이고, 지금 넋으로 만들 수 있는 칸은 ● 표시로(색만 믿지 않게) 보여 준다.
    /// </summary>
    void BuildSealMatrix(VisualElement p, Loadout lo, Color txt, Color hi, bool atShrine)
    {
        var kinds = CSeal.AllKinds(false);   // 15종(작은 인 기준). 번호 = 줄 순서
        int canMake = 0; foreach (var k0 in kinds) if (lo.wallet.CanAfford(k0)) canMake++;
        VTxt(p, "인 조합표 — 칸을 누르면 설명이 나온다" + (atShrine ? "" : "  (만들기는 서낭당 곁에서)"), 18, txt, true);
        VTxt(p, "● 지금 넋으로 만들 수 있다 (" + canMake + "/15)   ○ 넋이 모자란다", 13, new Color(txt.r, txt.g, txt.b, 0.7f));
        // 5x5 표: 위 삼각형만(A<=B). 행=A, 열=B. 아래쪽은 같은 인이라 비운다
        var grid = new VisualElement { pickingMode = PickingMode.Ignore }; grid.style.marginTop = 4; grid.style.marginBottom = 6;
        var head = new VisualElement { pickingMode = PickingMode.Ignore }; head.style.flexDirection = FlexDirection.Row;
        var corner = VTxt(head, "", 13, txt); corner.style.width = Length.Percent(12);
        for (int j = 0; j < 5; j++) { var h = VTxt(head, ColorShort((SoulColor)j) + "(" + colorMark[j] + ")", 13, txt, true); h.style.width = Length.Percent(17.6f); h.style.unityTextAlign = TextAnchor.MiddleCenter; }
        grid.Add(head);
        int idx = 0;
        for (int i = 0; i < 5; i++)
        {
            var row = new VisualElement { pickingMode = PickingMode.Position }; row.style.flexDirection = FlexDirection.Row; row.style.alignItems = Align.Center;
            var rh = VTxt(row, ColorShort((SoulColor)i) + "(" + colorMark[i] + ")", 13, txt, true); rh.style.width = Length.Percent(12);
            for (int j = 0; j < 5; j++)
            {
                if (j < i) { var blank = VTxt(row, "", 13, txt); blank.style.width = Length.Percent(17.6f); continue; }
                int my = idx++; var sk = kinds[my]; bool ok = lo.wallet.CanAfford(sk);
                string nm = SealEffects.Name(sk).Replace(" 인", "");   // 칸이 좁아 "인" 글자는 뺀다
                var cell = VTxt(row, (ok ? "● " : "○ ") + nm, 13, ok ? txt : new Color(txt.r, txt.g, txt.b, 0.5f));
                cell.pickingMode = PickingMode.Position; cell.style.width = Length.Percent(17.6f); cell.style.unityTextAlign = TextAnchor.MiddleCenter;
                cell.style.paddingTop = 6; cell.style.paddingBottom = 6;   // 손가락으로 누를 칸 높이를 넉넉히(폰)
                cell.style.backgroundColor = new Color(VInk.r, VInk.g, VInk.b, selKind == my ? 0.30f : (ok ? 0.12f : 0.05f));
                if (selKind == my) cell.style.borderBottomWidth = cell.style.borderTopWidth = cell.style.borderLeftWidth = cell.style.borderRightWidth = 2;   // 고른 칸은 테두리로도 표시
                cell.style.borderBottomColor = cell.style.borderTopColor = cell.style.borderLeftColor = cell.style.borderRightColor = hi;
                int pick = my; cell.RegisterCallback<ClickEvent>(e => { selKind = selKind == pick ? -1 : pick; Sfx.Play("sfx.ui.tab"); viewDirty = true; });
            }
            grid.Add(row);
        }
        p.Add(grid);
        // 고른 인의 설명과 만들기(작은 인 / 큰 인)
        if (selKind < 0 || selKind >= kinds.Count) { VTxt(p, "칸을 눌러 효과와 드는 넋을 본다", 14, txt); return; }
        var k = kinds[selKind];
        VTxt(p, SealLabel(k) + " — " + SealEffects.Describe(k) + " (큰 인은 효과 2배)", 15, txt, true);
        string fl = ItemTexts.Seal(SealEffects.Name(k)); if (fl.Length > 0) VTxt(p, fl, 13, new Color(txt.r, txt.g, txt.b, 0.6f));
        if (!atShrine) { VTxt(p, "인은 서낭당 곁에서 만든다 — 버튼을 0.6초 누르고 있는다", 14, txt); }
        var brow = new VisualElement { pickingMode = PickingMode.Position }; brow.style.flexDirection = FlexDirection.Row; brow.style.flexWrap = Wrap.Wrap;
        foreach (bool large in new[] { false, true })
        {
            var s2 = new CSeal(k.A, k.B, large); bool ok = lo.wallet.CanAfford(s2);
            string cost = k.Mono ? ColorShort(k.A) + " " + s2.TotalCost : ColorShort(k.A) + " " + s2.CostOf(k.A) + " · " + ColorShort(k.B) + " " + s2.CostOf(k.B);
            string label = (large ? "큰 인 " : "작은 인 ") + cost + (ok ? "" : " 모자람");
            bool live = ok && atShrine;   // 만들 수 있는 때: 넋이 있고 서낭당 곁일 때
            var b = VTxt(brow, label, 14, live ? txt : new Color(txt.r, txt.g, txt.b, 0.45f)); b.pickingMode = PickingMode.Position; b.style.marginRight = 10; b.style.paddingLeft = 6; b.style.paddingRight = 6; b.style.paddingTop = 8; b.style.paddingBottom = 8;
            b.style.backgroundColor = new Color(VInk.r, VInk.g, VInk.b, live ? 0.18f : 0.05f);
            string key = k.A + "-" + k.B + "-" + large; string baseText = label; var ka = k.A; var kb = k.B; bool lg = large;
            if (live) b.RegisterCallback<PointerDownEvent>(e => { holdKey = key; holdT = 0f; holdLabel = b; holdText = baseText; holdA = ka; holdB = kb; holdLarge = lg; });
        }
        p.Add(brow);
    }

    SoulColor holdA, holdB; bool holdLarge;
    /// <summary>만들기 누르고 있기: 손을 떼면 취소, 0.6초가 차면 만든다(매 프레임 부른다)</summary>
    void TickSealHold()
    {
        if (holdKey == null) return;
        bool down = Input.GetMouseButton(0) || Input.touchCount > 0;
        if (!down || !Open || tab != 5) { if (holdLabel != null) holdLabel.text = holdText; holdKey = null; return; }
        holdT += Time.unscaledDeltaTime;
        if (holdLabel != null) holdLabel.text = "만드는 중 " + Mathf.RoundToInt(Mathf.Clamp01(holdT / Balance.SEAL_CRAFT_HOLD_S) * 100f) + "%";
        if (holdT < Balance.SEAL_CRAFT_HOLD_S) return;
        holdKey = null; holdLabel = null;
        var lo = judge.player.loadout;
        if (lo.CraftSeal(holdA, holdB, holdLarge)) { Sfx.Play("sfx.ui.confirm"); selBagSeal = lo.sealBag.Count - 1; ToastSeal(lo.sealBag[lo.sealBag.Count - 1]); }
        else { Sfx.Play("sfx.ui.deny"); var lockMsg = lo.CraftLockReason(holdLarge); if (lockMsg != null) judge.Say(lockMsg); }
        viewDirty = true;
    }
    void ToastSeal(CSeal s) { judge.Say("인을 만들었다 — " + SealLabel(s)); }
}
