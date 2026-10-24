// =============================================================================
// CharacterPanel.cs — 캐릭터 창(장비 / 도술 / 능력치) 최소 UI. C 키 또는 MENU 버튼으로 열고 닫는다.
// 열려 있는 동안 게임은 멈춘다(보면서 죽지 않게). 기획서 6절 화면 구성을 따르되 시연판은 글자·아이콘만.
// 기본 글꼴에 한글이 없어 영문 표기를 쓴다. 규칙·수치는 Core 가 계산한 값을 그대로 보여 주기만 한다.
// =============================================================================
using Chasa.Core;
using UnityEngine;

public class CharacterPanel : MonoBehaviour
{
    public static bool Open;                 // 열려 있으면 GameMain 이 세계 갱신을 멈춘다
    public JudgeSystem judge;
    public Texture2D white;
    int tab;                                 // 0 장비 1 도술 2 능력치
    static readonly string[] TabNames = { "장비", "도술", "능력치" };

    public void Toggle() { Open = !Open; }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.C)) Toggle();
        if (Open && Input.GetKeyDown(KeyCode.Escape)) Open = false;
    }

    void OnGUI()
    {
        Ko.Apply(); // 한글 글꼴 적용(안 하면 한글이 네모로 깨짐)
        if (!Open || judge == null || judge.player == null) return;
        var lo = judge.player.loadout;
        float w = Mathf.Min(Screen.width - 24f, 640f), h = Mathf.Min(Screen.height - 24f, 440f);
        var box = new Rect((Screen.width - w) / 2f, (Screen.height - h) / 2f, w, h);
        GUI.color = new Color(0.05f, 0.06f, 0.1f, 0.94f); GUI.DrawTexture(box, white); GUI.color = Color.white;

        var title = new GUIStyle(GUI.skin.label) { fontSize = 20, fontStyle = FontStyle.Bold };
        var body = new GUIStyle(GUI.skin.label) { fontSize = 16 };
        title.normal.textColor = ChasaPalette.Hanji; body.normal.textColor = ChasaPalette.Hanji;

        // 탭 막대
        for (int i = 0; i < 3; i++)
        {
            var r = new Rect(box.x + 12 + i * 120, box.y + 10, 112, 36);
            if (GUI.Button(r, TabNames[i] + (tab == i ? " *" : ""))) tab = i;
        }
        if (GUI.Button(new Rect(box.xMax - 100, box.y + 10, 88, 36), "닫기")) Open = false;

        float y = box.y + 60;
        var st = lo.stats;
        if (tab == 0) DrawEquip(box, y, lo, body, title);
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
                label += Ko.ItemName(it) + (it.Gradient ? "  [기울기]" : "");
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
            case Opt.CastReducePct: return "천도 시전 " + Pct(-o.Value);   // 단축이 +이므로 시간은 반대 부호로 보여 준다
            case Opt.PahonAreaPct: return "파혼 범위 " + Pct(o.Value);
            case Opt.PahonDamagePct: return "파혼 피해 " + Pct(o.Value);
            case Opt.HpFlat: return "체력 +" + (int)o.Value;
            case Opt.MoveSpeedPct: return "이동 " + Pct(o.Value);
            case Opt.CoinPct: return "엽전 " + Pct(o.Value);
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
}
