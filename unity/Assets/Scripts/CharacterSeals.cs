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
            var nm = VTxt(row, Ko.PosName(pos) + ": " + Ko.ItemName(it) + (it.Sockets == 0 ? "  (홈 없음)" : ""), 15, txt); nm.style.marginRight = 8;
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
        // 4) 인 만들기: 서낭당 곁에서만
        var gap2 = new VisualElement { pickingMode = PickingMode.Ignore }; gap2.style.height = 8; p.Add(gap2);
        if (!atShrine) { VTxt(p, "인은 서낭당 곁에서 만든다", 14, txt); return; }
        VTxt(p, "인 만들기 — 버튼을 0.6초 누르고 있는다", 18, txt, true);
        foreach (var kind in CSeal.AllKinds(false))
        {
            var k = kind; var row = new VisualElement { pickingMode = PickingMode.Position }; row.style.flexDirection = FlexDirection.Row; row.style.flexWrap = Wrap.Wrap; row.style.alignItems = Align.Center;
            var nm = VTxt(row, SealEffects.Name(k) + " (" + ColorShort(k.A) + (k.Mono ? "" : "+" + ColorShort(k.B)) + ")", 15, txt); nm.style.width = 170;
            foreach (bool large in new[] { false, true })
            {
                var s2 = new CSeal(k.A, k.B, large); bool ok = lo.wallet.CanAfford(s2);
                string need = ok ? "" : " 모자람";
                string label = (large ? "큰 인 " : "작은 인 ") + (k.Mono ? ColorShort(k.A) + " " + s2.TotalCost : ColorShort(k.A) + " " + s2.CostOf(k.A) + " · " + ColorShort(k.B) + " " + s2.CostOf(k.B)) + need;
                var b = VTxt(row, label, 13, ok ? txt : new Color(txt.r, txt.g, txt.b, 0.45f)); b.pickingMode = PickingMode.Position; b.style.marginRight = 10; b.style.paddingLeft = 4; b.style.paddingRight = 4; b.style.paddingTop = 3; b.style.paddingBottom = 3;
                b.style.backgroundColor = new Color(VInk.r, VInk.g, VInk.b, ok ? 0.14f : 0.05f);
                string key = k.A + "-" + k.B + "-" + large; string baseText = label;
                if (ok) b.RegisterCallback<PointerDownEvent>(e => { holdKey = key; holdT = 0f; holdLabel = b; holdText = baseText; holdA = k.A; holdB = k.B; holdLarge = large; });
            }
            p.Add(row);
        }
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
        else Sfx.Play("sfx.ui.deny");
        viewDirty = true;
    }
    void ToastSeal(CSeal s) { judge.Say("인을 만들었다 — " + SealLabel(s)); }
}
