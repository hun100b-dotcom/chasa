// =============================================================================
// CharacterPanel.cs — 캐릭터 창(장비 / 도술 / 능력치) 최소 UI. C 키 또는 MENU 버튼으로 열고 닫는다.
// 열려 있는 동안 게임은 멈춘다(보면서 죽지 않게). 기획서 6절 화면 구성을 따르되 시연판은 글자·아이콘만.
// 기본 글꼴에 한글이 없어 영문 표기를 쓴다. 규칙·수치는 Core 가 계산한 값을 그대로 보여 주기만 한다.
// =============================================================================
using Chasa.Core;
using UnityEngine;

public partial class CharacterPanel : MonoBehaviour
{
    public static bool Open;                 // 열려 있으면 GameMain 이 세계 갱신을 멈춘다
    public JudgeSystem judge;
    public Texture2D white;
    int tab = 3;                             // 0 장비 1 도술 2 능력치 3 명부(책). 기본은 명부
    static readonly string[] TabNames = { "장비", "도술", "능력치", "명부", "들은 말" };
    string hoverDesc = "";
    // 명부 책 색(코디 결정 10-25): 글자는 먹색, 강조는 붉은 인. 책 그림(한지 바탕)이 있을 때만 쓴다
    static readonly Color Ink = new Color32(0x1E, 0x1A, 0x17, 255), Seal = new Color32(0xB5, 0x47, 0x3F, 255);
    bool bookMode; GUIStyle bookBtn;                   // 명부에서 마우스를 올린 도술의 설명

    // 명부 탭은 시연판 설정과 무관하게 항상 열린다. 옛 세 탭(장비·도술·능력치)은 DEMO_PANEL 이 켜졌을 때만 보인다
    public void Toggle() { Open = !Open; Sfx.Play(Open ? "sfx.ui.ledger.open" : "sfx.ui.ledger.close"); if (Open && !Demo.Panel) tab = 3; }

    void Update()
    {
        UpdateView();
        if (Input.GetKeyDown(KeyCode.C)) Toggle();   // Demo.Panel 이 꺼져 있으면 Toggle 이 무시한다
        if (Open && Input.GetKeyDown(KeyCode.Escape)) Open = false;
    }

    void OnGUI()
    {
        Ko.Apply(); // 한글 글꼴 적용(안 하면 한글이 네모로 깨짐)
        if (!Open || judge == null || judge.player == null || UseView) return;   // 명부·들은 말 탭은 UI Toolkit 판(CharacterView)이 그린다
        GUI.depth = -100;   // 가장 위에 그린다(낮을수록 위) — 밤 화면 글자와 겹치지 않게(QA B2)
        var lo = judge.player.loadout;
        // 명부는 도술 27칸을 세 줄로 늘어놓아야 해서 더 크게 쓴다
        float w = Mathf.Min(Screen.width - 24f, tab == 3 ? 940f : 640f), h = Mathf.Min(Screen.height - 24f, tab == 3 ? 600f : 440f);
        var box = new Rect((Screen.width - w) / 2f, (Screen.height - h) / 2f, w, h);
        var bookTex = tab == 3 ? SpriteLib.Texture("ui/ui_book_spread") : null;
        bookMode = bookTex != null;
        if (bookMode) GUI.DrawTexture(box, bookTex, ScaleMode.StretchToFill);   // 펼친 책(한지·가운데 붉은 실)
        else { GUI.color = new Color(0.05f, 0.06f, 0.1f, 0.94f); GUI.DrawTexture(box, white); GUI.color = Color.white; }

        var title = new GUIStyle(GUI.skin.label) { fontSize = 20, fontStyle = FontStyle.Bold };
        var body = new GUIStyle(GUI.skin.label) { fontSize = 16 };
        title.normal.textColor = bookMode ? Seal : ChasaPalette.Hanji; body.normal.textColor = bookMode ? Ink : ChasaPalette.Hanji;
        if (bookMode)
        {
            // 책 안 버튼: 바탕 없이 먹색 글자, 올리면 붉은 인 색. (기본 버튼은 어두운 회색 바탕이라 한지 위에서 튄다)
            bookBtn = new GUIStyle(GUI.skin.button) { fontSize = 13, alignment = TextAnchor.MiddleLeft };
            bookBtn.normal.background = null; bookBtn.hover.background = null; bookBtn.active.background = null; bookBtn.focused.background = null;
            bookBtn.normal.textColor = Ink; bookBtn.hover.textColor = Seal; bookBtn.active.textColor = Seal; bookBtn.focused.textColor = Ink;
        }

        // 탭 막대
        int slot0 = 0;   // 보이는 탭 칸 번호(옛 탭이 숨겨져도 간격이 벌어지지 않게)
        for (int i = 0; i < 5; i++)
        {
            if (i < 3 && !Demo.Panel) continue;
            var r = new Rect(box.x + 12 + slot0++ * 120, box.y + 10, 112, 36);
            if (GUI.Button(r, TabNames[i] + (tab == i ? " *" : ""))) tab = i;
        }
        if (GUI.Button(new Rect(box.xMax - 100, box.y + 6, 88, 30), "닫기")) Open = false;

        float y = box.y + 60;
        var st = lo.stats;
        if (tab == 3 && bookMode) DrawBook(new Rect(box.x + 44, box.y + 40, box.width - 88, box.height - 80), box.y + 52, body, title);   // 한지 안쪽 여백(약 40px)을 피해 그린다
        else if (tab == 3) DrawBook(box, y, body, title);
        else if (tab == 4) DrawHeard(box, y, body, title);
        else if (tab == 0) DrawEquip(box, y, lo, body, title);
        else if (tab == 1) DrawSkills(box, y, lo, body, title);
        else DrawStats(box, y, lo, st, body, title);
    }

    void DrawEquip(Rect box, float y, Loadout lo, GUIStyle body, GUIStyle title)
    {
        GUI.Label(new Rect(box.x + 16, y, 500, 28), "손에 든 무기: " + lo.Def.Name + "  (Tab으로 교체)", title);
        y += 36;
        for (int s = 0; s < 3; s++)
        {
            var slot = (Slot)s;
            var it = lo.gear.Get(slot);
            var icon = new Rect(box.x + 16, y, 64, 64);
            GUI.color = new Color(0, 0, 0, 0.4f); GUI.DrawTexture(icon, white); GUI.color = Color.white;
            string label = Ko.SlotName(slot) + ": ";
            if (it == null) label += "(비어 있음)";
            else
            {
                DrawIcon(slot, it, icon);
                label += Ko.ItemName(it) + (it.Gradient ? "  [기울기: " + Ko.TiltName(it) + "]" : "");
            }
            GUI.Label(new Rect(box.x + 92, y, box.width - 110, 24), label, body);
            if (it != null)
            {
                string opts = "";
                foreach (var o in it.Options) opts += OptText(o) + "   ";
                GUI.Label(new Rect(box.x + 92, y + 24, box.width - 110, 40), opts, body);
            }
            y += 76;
        }
    }

    static string OptText(OptionRoll o)
    {
        switch (o.Kind)
        {
            case Opt.DamagePct: return "피해 " + Pct(o.Value);
            case Opt.AttackSpeedPct: return "공격 속도 " + Pct(o.Value);
            case Opt.CastReducePct: return "천도 시전 시간 " + Pct(-o.Value);   // 단축이 +이므로 시간은 반대 부호로 보여 준다
            case Opt.PahonAreaPct: return "파혼 범위 " + Pct(o.Value);
            case Opt.PahonDamagePct: return "파혼 피해 " + Pct(o.Value);
            case Opt.HpFlat: return "체력 +" + (int)o.Value;
            case Opt.MoveSpeedPct: return "이동 " + Pct(o.Value);
            case Opt.CoinPct: return "엽전 " + Pct(o.Value);
            case Opt.TendoNeokPct: return "천도 넋 " + Pct(o.Value);
            case Opt.PahonCoinPct: return "파혼 엽전 " + Pct(o.Value);
            case Opt.WaitAddS: return "처결 대기 " + (o.Value >= 0 ? "+" : "") + o.Value.ToString("0.0") + "초";
            case Opt.ChainWindowAddS: return "연속 천도 창 " + (o.Value >= 0 ? "+" : "") + o.Value.ToString("0.0") + "초";
            case Opt.PahonKnockbackPct: return "파혼 넉백 " + Pct(o.Value);
            case Opt.VisionShift: return "천도 중 시야 " + (o.Value >= 0 ? "+" : "") + Mathf.RoundToInt(o.Value * 100f) + "%p";
            case Opt.CastDamageReducePct: return "시전 중 받는 피해 " + Pct(-o.Value);
            default: return "파혼 반경 +" + o.Value.ToString("0.0") + "m";
        }
    }

    static string Pct(float v) { return (v >= 0 ? "+" : "") + Mathf.RoundToInt(v * 100f) + "%"; }

    void DrawIcon(Slot s, ItemDef it, Rect r)
    {
        string rar = it.Named ? "named" : it.Rarity == Rarity.Rare ? "rare" : it.Rarity == Rarity.Crafted ? "crafted" : "common";
        string icon = it.Named ? "icon_named_wolhwa_bell" : "icon_" + (s == Slot.Weapon ? "weapon" : s == Slot.Robe ? "dopo" : "noriga") + "_" + rar;
        var tex = SpriteLib.Texture("icons/" + icon); var fr = SpriteLib.Texture("icons/frame_" + rar);
        if (tex != null) GUI.DrawTexture(r, tex);
        if (fr != null) GUI.DrawTexture(r, fr);
    }

    static readonly string[] SlotNames = { "새벽", "낮", "저녁", "밤" };
    Vector2 heardScroll;

    /// <summary>들은 말 탭: 엿듣고 지켜본 말을 시간대·자리와 함께 보여 준다. 단서가 있으면 금색 점(기획 §3-2)</summary>
    void DrawHeard(Rect box, float y, GUIStyle body, GUIStyle title)
    {
        var log = judge.npcs != null ? judge.npcs.Log : null;
        if (log == null || log.Items.Count == 0) { GUI.Label(new Rect(box.x + 16, y, box.width - 32, 60), "아직 들은 말이 없다. 산 사람 곁에 가만히 서 있으면 들린다.", body); return; }
        var view = new Rect(box.x + 12, y, box.width - 24, box.height - (y - box.y) - 12);
        var content = new Rect(0, 0, view.width - 24, log.Items.Count * 62f);
        heardScroll = GUI.BeginScrollView(view, heardScroll, content);
        for (int i = 0; i < log.Items.Count; i++)
        {
            var e = log.Items[log.Items.Count - 1 - i];   // 최근 것이 위
            bool clue = !string.IsNullOrEmpty(e.Clue);
            if (clue) { GUI.color = new Color(1f, 0.82f, 0.3f); GUI.Label(new Rect(0, i * 62f, 20, 24), "●", body); GUI.color = Color.white; }
            GUI.Label(new Rect(22, i * 62f, content.width - 22, 24), e.Who + "  (" + SlotNames[Mathf.Clamp(e.Slot, 0, 3)] + " · " + e.Place + ")", title);
            GUI.Label(new Rect(22, i * 62f + 24, content.width - 22, 36), e.Text, body);
        }
        GUI.EndScrollView();
    }

    void DrawSkills(Rect box, float y, Loadout lo, GUIStyle body, GUIStyle title)
    {
        string[] desc =
        {
            "반경 " + Balance.SKILL_HOLD_RADIUS + "m: 무릎 꿇은 넋의 대기 +" + Balance.SKILL_HOLD_WAIT_BONUS + "초, 적은 " + Balance.SKILL_HOLD_STUN + "초 움찔",
            "반경 " + Balance.SKILL_BIND_RADIUS + "m: 적을 " + Balance.SKILL_BIND_STUN + "초 동안 묶는다",
            "가장 가까운 얼룩을 터뜨린다: 반경 " + Balance.SKILL_BURST_RADIUS + "m, 피해 " + Balance.SKILL_BURST_DAMAGE + ", 업은 그대로",
        };
        for (int i = 0; i < 3; i++)
        {
            var d = SkillDef.All[i];
            GUI.Label(new Rect(box.x + 16, y, box.width - 32, 26), "[" + (i + 1) + "] " + d.Name + "   재사용 " + d.Cooldown + "초" +
                (lo.skills.Ready(i) ? "   준비됨" : "   " + Mathf.CeilToInt(lo.skills.Left[i]) + "초 남음"), title);
            GUI.Label(new Rect(box.x + 40, y + 28, box.width - 56, 28), desc[i], body);
            y += 72;
        }
        if (lo.Def.HasQuake)
            GUI.Label(new Rect(box.x + 16, y, box.width - 32, 26), "[Q] 땅울림 (육모방망이)  반경 " + Balance.MACE_QUAKE_RADIUS + "m, 기절 " + Balance.MACE_QUAKE_STUN + "초, 재사용 " + Balance.MACE_QUAKE_COOLDOWN + "초", body);
    }

    void DrawStats(Rect box, float y, Loadout lo, GearStats st, GUIStyle body, GUIStyle title)
    {
        // 기울기 막대: 왼쪽 천도(SEND) ↔ 오른쪽 파혼(SHATTER)
        float tilt = st.Tilt(lo.Def.PahonDamageMult > 1f ? 0.25f : 0f);
        GUI.Label(new Rect(box.x + 16, y, 260, 24), "기울기", title);
        var bar = new Rect(box.x + 16, y + 28, box.width - 32, 14);
        GUI.color = new Color(0, 0, 0, 0.6f); GUI.DrawTexture(bar, white);
        GUI.color = ChasaPalette.CheondoGlow; GUI.DrawTexture(new Rect(bar.x, bar.y, bar.width * 0.5f, bar.height), white);
        GUI.color = ChasaPalette.PahonBurst; GUI.DrawTexture(new Rect(bar.x + bar.width * 0.5f, bar.y, bar.width * 0.5f, bar.height), white);
        GUI.color = Color.white; GUI.DrawTexture(new Rect(bar.x + bar.width * (0.5f + tilt * 0.5f) - 3, bar.y - 3, 6, bar.height + 6), white);
        GUI.Label(new Rect(bar.x, bar.y + 16, 200, 22), "천도", body);
        GUI.Label(new Rect(bar.xMax - 80, bar.y + 16, 80, 22), "파혼", body);
        y += 70;
        // 능력치 4종(시연판: 표시 전용). 넋 30마다 1점
        int pts = StatPoints.Earned(judge.ledger.Neok);
        GUI.Label(new Rect(box.x + 16, y, box.width - 32, 24), "힘 10   민첩 10   몸 10   정신 10      얻은 점수: " + pts + " (쓰기: 나중에)", body);
        y += 30;
        string d1 = "피해 x" + st.DamageMult.ToString("0.00") + "   공격 속도 x" + st.AttackSpeedMult.ToString("0.00") + "   이동 x" + st.MoveSpeedMult.ToString("0.00") + "   최대 체력 " + st.MaxHp;
        string d2 = "천도 시전 x" + st.CastMult.ToString("0.00") + " (최소 " + Balance.CAST_MIN_TIME + "초)   파혼 피해 x" + (lo.Def.PahonDamageMult * st.PahonDamageMult).ToString("0.00") +
                    "   반경 " + st.PahonRadius(Balance.PAHON_RADIUS).ToString("0.0") + "m   엽전 x" + st.CoinMult.ToString("0.00");
        GUI.Label(new Rect(box.x + 16, y, box.width - 32, 24), d1, body);
        GUI.Label(new Rect(box.x + 16, y + 26, box.width - 32, 24), d2, body);
    }

    // ===== 명부(책) 탭: 품계·능력치 점수 나누기·도술 세 갈래·장비 칸 ====================
    // 규칙은 Core/Growth.cs 가 쥐고 있고, 여기서는 보여 주고 버튼을 누르게만 한다(효과를 게임에 잇는 것은 다음 일).
    static readonly string[] SlotLabels = { "무기", "도포", "노리개", "갓", "신", "띠", "부적" };   // 7칸(임시 이름 — 기획서 확정 전)
    static readonly bool[] SlotLive = { true, true, true, false, false, false, false };           // 지금 실제로 쓰는 칸

    void DrawBook(Rect box, float y, GUIStyle body, GUIStyle title)
    {
        var g = judge.growth;
        var small = new GUIStyle(body) { fontSize = 14 };
        // 1) 품계 줄: 다음 품계까지 얼마나 남았는지 막대로
        int next = g.Rank >= GrowthState.MaxRank ? g.TotalNeok : GrowthState.NeokForRank(g.Rank + 1);
        int cur = GrowthState.NeokForRank(g.Rank);
        float frac = g.Rank >= GrowthState.MaxRank ? 1f : Mathf.Clamp01((g.TotalNeok - cur) / (float)Mathf.Max(1, next - cur));
        GUI.Label(new Rect(box.x + 16, y, 420, 28), "품계 " + g.Rank + "품   넋 " + g.TotalNeok + (g.Rank >= GrowthState.MaxRank ? "" : " / " + next), title);
        GUI.Label(new Rect(box.x + 460, y + 2, box.width - 480, 24), "도술 점수 " + g.SkillPointsFree + (g.StainPointsFree > 0 ? " (+얼룩 전용 " + g.StainPointsFree + ")" : "") + "   능력치 점수 " + g.StatPointsFree, body);
        var bar = new Rect(box.x + 16, y + 30, box.width - 32, 8);
        GUI.color = bookMode ? new Color(Ink.r, Ink.g, Ink.b, 0.18f) : new Color(0, 0, 0, 0.6f); GUI.DrawTexture(bar, white);
        GUI.color = bookMode ? Seal : ChasaPalette.CheondoGlow; GUI.DrawTexture(new Rect(bar.x, bar.y, bar.width * frac, bar.height), white);
        GUI.color = Color.white;
        y += 50;

        // 2) 능력치 4종: 점수가 남아 있으면 + 버튼
        for (int i = 0; i < GrowthState.StatNames.Length; i++)
        {
            float x = box.x + 16 + i * 220;
            GUI.Label(new Rect(x, y, 150, 26), GrowthState.StatNames[i] + " " + g.Stats[i], body);
            if (g.StatPointsFree > 0 && GUI.Button(new Rect(x + 120, y, 36, 28), "+", bookMode ? bookBtn : GUI.skin.button)) { g.AddStat(i); judge.RefreshGrowth(); }   // 점수를 쓰면 전투 수치를 다시 계산
        }
        y += 40;

        // 3) 도술 세 갈래(세 줄). 눌러서 배운다. 깊은 도술은 그 갈래 10점 전까지 잠김
        float colW = (box.width - 32 - 24) / 3f;
        hoverDesc = "";
        for (int b = 0; b < 3; b++)
        {
            var br = (Branch)b;
            float x = box.x + 16 + b * (colW + 12), yy = y;
            GUI.Label(new Rect(x, yy, colW, 24), SkillTree.BranchName(br) + " 갈래  (" + g.BranchPoints(br) + "점)", title);
            yy += 28;
            foreach (var n in SkillTree.All)
            {
                if (n.Branch != br) continue;
                int lv = g.LevelOf(n.Name);
                bool can = g.CanLearn(n.Name);
                bool locked = n.Deep && g.BranchPoints(br) < SkillTree.DeepNeeds;
                int barAt = n.Active ? g.ActiveBar.IndexOf(n.Name) : -1;
                string label = (n.Active ? (barAt >= 0 ? "[" + (barAt + 1) + "칸] " : "[기] ") : "[패] ") + (n.Deep ? "*" : "") + n.Name + "  " + lv + "/" + n.MaxLevel + (locked ? "  잠김" : "");
                var r = new Rect(x, yy, colW, 26);
                GUI.color = lv > 0 ? Color.white : (can ? new Color(1f, 1f, 1f, 0.9f) : new Color(1f, 1f, 1f, 0.45f));
                if (GUI.Button(r, label, bookMode ? bookBtn : GUI.skin.button))
                {
                    if (n.Active && lv > 0) g.ToggleBar(n.Name);   // 배운 액티브는 누르면 칸에 올렸다 내렸다
                    else { g.Learn(n.Name); judge.RefreshGrowth(); }
                }   // 배우면 패시브 효과가 바로 붙는다
                GUI.color = Color.white;
                if (r.Contains(Event.current.mousePosition)) hoverDesc = n.Name + ": " + n.Desc;
                yy += 28;
            }
        }
        y += 28 + 9 * 28 + 6;

        // 4) 설명 한 줄 + 액티브 칸 + 장비 칸
        GUI.Label(new Rect(box.x + 16, y, box.width - 32, 24), hoverDesc.Length > 0 ? hoverDesc : "도술을 누르면 점수 1을 써서 배운다(배운 액티브는 누르면 칸에 올리고 내림). [기]=액티브 [패]=패시브(2단계) *=깊은 도술(그 갈래 " + SkillTree.DeepNeeds + "점 이상)", small);
        y += 26;
        string bar4 = "";
        for (int i = 0; i < SkillTree.ActiveSlots; i++) bar4 += "[" + (i + 1) + ": " + (i < g.ActiveBar.Count ? g.ActiveBar[i] : "빈 칸") + "]  ";
        GUI.Label(new Rect(box.x + 16, y, box.width - 32, 24), "액티브 칸  " + bar4, small);
        y += 26;
        // 무기 2자루: 손에 든 것 / 등에 멘 것(Tab 으로 바꿔 듦). 다섯 계열 모두 고를 수 있다
        var lo = judge.player.loadout;
        var bst = bookMode ? bookBtn : GUI.skin.button;
        for (int row = 0; row < 2; row++)
        {
            bool hand = row == 0;
            GUI.Label(new Rect(box.x + 16, y, 70, 26), hand ? "손에 든" : "등에 멘", small);
            for (int i = 0; i < Loadout.AllWeapons.Length; i++)
            {
                var wid = Loadout.AllWeapons[i];
                bool held = (hand ? lo.weapon : lo.other) == wid;
                var wr = new Rect(box.x + 90 + i * 128, y, 124, 26);
                if (GUI.Button(wr, (held ? "● " : "") + WeaponDef.Get(wid).Name, bst)) { if (hand) lo.SetHand(wid); else lo.SetBack(wid); }
            }
            y += 28;
        }
        GUI.Label(new Rect(box.x + 16, y, box.width - 32, 24), "지금 든 " + lo.Def.Name + " — " + lo.Def.Taste, small);
    }
}
