// =============================================================================
// DayScreen.cs — 낮 한 번의 최소 화면 (시연판용, IMGUI). 규칙은 Core/DayRun.cs·Shrine.cs.
// 왜 지도 없이 목록인가: 기획서 B-1 "낮에는 혼이 없어 걸어갈 필요가 없다 — 열린 구역을 골라 바로 간다".
// 그래서 낮 지도는 '고를 수 있는 자리 목록'으로 시작한다. 엿듣기 원·지켜보기 거리 같은 '그 자리에 서 있기'는
// 버튼을 누르고 있는 동안(자리를 벗어나면 버튼을 눌러 중단)으로 바꿨다. 낮 마을 지도 그림은 아트가 오면 얹는다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class DayScreen
{
    readonly Ledger ledger;
    readonly Loadout lo;

    public DayRun Run;                         // 지금 낮
    public readonly Pack Pack = new Pack();    // 한 밤 소모품
    public int BossCluesHave;                  // 지금까지 모은 보스 단서(단서는 사라지지 않는다)
    readonly HashSet<string> doneIds = new HashSet<string>();   // 이미 한 단서 자리(다음 낮에도 다시 못 얻음)
    ClueAction action;                         // 하는 중인 동사
    bool shrineOpen;
    int selSlot;                               // 손보기에서 고른 장비 칸
    string msg = "";
    public bool WantsNight;                    // 해 넘기기를 눌렀다 → JudgeSystem 이 밤을 시작
    bool funeralOn;                            // 장례를 지켜보는 중 (눈금 0, 시간이 흐른다)
    float emptyT;                              // 할 것 없는 낮 안내 남은 시간

    public DayScreen(Ledger l, Loadout loadout) { ledger = l; lo = loadout; }

    /// <summary>새 낮을 시작. namedTendoLastNight = 어젯밤 이름혼을 천도했나(장례가 열림)</summary>
    public void Begin(bool namedTendoLastNight)
    {
        Run = new DayRun(namedTendoLastNight);
        action = null; funeralOn = false; shrineOpen = false; WantsNight = false; msg = ""; emptyT = 0f;
        Pack.Heal = Mathf.Min(Pack.Heal, Balance.SHOP_HEAL_MAX);
        // 솔고개 마을의 낮 단서 자리 (기획 B-2: 동사 셋이 하나씩 다르다. 제사 집·강가·서낭당 고개에 흩어져 있다)
        Add("listen", "제사 집 담장 밑 엿듣기", ClueVerb.Eavesdrop, SpotKind.BossClue, true);
        Add("ferry", "강가 나루터 지켜보기", ClueVerb.Watch, SpotKind.BossClue, false);
        Add("relic", "서낭당 고개 유품 만져 보기", ClueVerb.Touch, SpotKind.BossClue, false);
        Add("house", "제사 지내는 집 지켜보기 (이름혼)", ClueVerb.Watch, SpotKind.NamedHouse, false);
        Add("rumor", "우물가 마을 소문 엿듣기", ClueVerb.Eavesdrop, SpotKind.Rumor, true);
    }

    void Add(string id, string name, ClueVerb v, SpotKind k, bool human)
    {
        Run.Spots.Add(new ClueSpot { Id = id, Verb = v, Kind = k, HumanSpeech = human, Done = doneIds.Contains(id) });
        names[id] = name;
    }
    readonly Dictionary<string, string> names = new Dictionary<string, string>();

    static string VerbName(ClueVerb v) { return v == ClueVerb.Eavesdrop ? "엿듣기" : v == ClueVerb.Watch ? "지켜보기" : "만져 보기"; }

    public void Tick(float dt)
    {
        if (Run == null) return;
        if (action != null)
        {
            // 한 자리에 머무는 동작: 화면 시뮬레이션이라 '자리까지의 거리'는 항상 0(= 서 있는 중)
            if (action.Tick(dt, 0f))
            {
                Run.Complete(action);
                doneIds.Add(action.Spot.Id);
                if (action.Spot.Kind == SpotKind.BossClue)
                    BossCluesHave = Mathf.Min(Balance.BOSS_CLUES_REQUIRED, BossCluesHave + 1);
                msg = action.Spot.Kind == SpotKind.NamedHouse ? "이름혼의 자리가 명부에 올랐다" :
                      action.Half ? "반쪽 문장만 들렸다 (업이 귀를 닫고 있다)" : "단서를 얻었다";
                action = null;
            }
        }
        if (funeralOn && action == null)
        {
            if (Run.WatchFuneral(dt)) { funeralOn = false; msg = "장례를 끝까지 보았다"; }
        }
        // 할 것이 없는 낮은 저절로 짧아진다
        if (action == null && !funeralOn && Run.Phase == DayPhase.Day && Run.NothingToDo(ledger.Karma))
        {
            if (emptyT <= 0f) emptyT = Balance.EMPTY_DAY_TIME;
            emptyT -= dt;
            if (emptyT <= 0f) WantsNight = true;
        }
        else emptyT = 0f;
    }

    public bool NamedHouseWatched { get { return Run != null && Run.NamedHouseWatched; } }

    public void OnGUI(Texture2D white)
    {
        if (Run == null) return;
        GUI.color = new Color(0.08f, 0.07f, 0.06f, 0.96f); GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), white); GUI.color = Color.white;
        var h = new GUIStyle(GUI.skin.label) { fontSize = 30, alignment = TextAnchor.MiddleCenter };
        var body = new GUIStyle(GUI.skin.label) { fontSize = 18, wordWrap = true };
        var btn = new GUIStyle(GUI.skin.button) { fontSize = 18, alignment = TextAnchor.MiddleLeft };
        float w = Mathf.Min(Screen.width - 24f, 760f), x = (Screen.width - w) / 2f, y = 14f;

        string sun = "";
        for (int i = 0; i < Balance.DAY_TICKS; i++) sun += i < Run.TicksLeft ? "● " : "○ ";
        GUI.Label(new Rect(x, y, w, 44), (Run.Phase == DayPhase.Day ? "낮" : "해 질 녘") + "   해 그림자 " + sun, h); y += 50;
        GUI.Label(new Rect(x, y, w, 26), "엽전 " + ledger.Coin + "   광석 " + ledger.Ore + "   업 " + ledger.Karma + "   보스 단서 " + BossCluesHave + "/" + Balance.BOSS_CLUES_REQUIRED + "   " + KarmaNote(), body); y += 30;
        if (msg != "") { GUI.Label(new Rect(x, y, w, 26), msg, body); }
        y += 30;

        if (shrineOpen) { DrawShrine(x, y, w, body, btn); return; }

        // 하는 중인 동사: 진행 막대 + 자리를 벗어나기
        if (action != null)
        {
            GUI.Label(new Rect(x, y, w, 26), VerbName(action.Spot.Verb) + ": " + names[action.Spot.Id], body); y += 30;
            GUI.color = new Color(0, 0, 0, 0.7f); GUI.DrawTexture(new Rect(x, y, w, 16), white);
            GUI.color = ChasaPalette.MemoryRim; GUI.DrawTexture(new Rect(x + 1, y + 1, (w - 2) * Mathf.Clamp01(action.Progress / action.Need), 14), white); GUI.color = Color.white; y += 28;
            if (GUI.Button(new Rect(x, y, 260, 44), action.Spot.Verb == ClueVerb.Touch ? "손을 뗀다 (멈춤)" : "자리를 벗어난다 (처음부터)", btn))
                action = null;   // 중단: 엿듣기·지켜보기는 처음부터, 만져 보기는 눈금을 쓰지 않은 채 멈춘다
            return;
        }

        // 장례 (눈금 0, 건너뛸 수 있음)
        if (Run.FuneralAvailable && !Run.FuneralDone)
        {
            string f = funeralOn ? "장례를 지켜보는 중 " + Mathf.CeilToInt(Balance.FUNERAL_TIME - Run.FuneralWatched) + "초 (누르면 멈춤)" : "어젯밤 천도한 이의 장례를 본다 (70초, 눈금 0)";
            if (GUI.Button(new Rect(x, y, w - 120, 44), f, btn)) funeralOn = !funeralOn;
            if (GUI.Button(new Rect(x + w - 110, y, 110, 44), "건너뛰기", btn)) { Run.SkipFuneral(); funeralOn = false; }
            y += 52;
        }
        else if (Run.FuneralDone) { GUI.Label(new Rect(x, y, w, 26), "장례를 끝까지 보았다. 두루마리에 남는다.", body); y += 32; }

        // 열린 구역 목록 (낮에는 걸어갈 필요 없이 바로 간다)
        if (Run.Phase == DayPhase.Day)
        {
            foreach (var s in Run.Spots)
            {
                var acc = Run.Access(s, ledger.Karma);
                string tag = acc == SpotAccess.Done ? " (끝)" : acc == SpotAccess.Closed ? " (귀가 닫혔다)" : "";
                bool can = acc == SpotAccess.Open && Run.TicksLeft > 0;
                GUI.enabled = can;
                if (GUI.Button(new Rect(x, y, w, 44), VerbName(s.Verb) + " · " + names[s.Id] + tag, btn))
                { action = Run.Begin(s, ledger.Karma); msg = ""; }
                GUI.enabled = true; y += 50;
            }
            if (emptyT > 0f) { GUI.Label(new Rect(x, y, w, 26), "오늘 낮엔 들을 것이 없다.", body); y += 32; }
        }
        else { GUI.Label(new Rect(x, y, w, 26), "해가 기울었다. 서낭당에서 채비를 하고 밤으로 간다.", body); y += 32; }

        if (GUI.Button(new Rect(x, y + 6, 220, 52), "서낭당 (공물상·손보기)", btn)) { shrineOpen = true; msg = ""; }
        if (GUI.Button(new Rect(x + w - 220, y + 6, 220, 52), "해 넘기기 → 밤", btn)) WantsNight = true;
    }

    /// <summary>업이 귀를 닫은 정도를 한 줄로</summary>
    string KarmaNote()
    {
        int k = ledger.Karma;
        return k >= Balance.KARMA_EAR_ALL_CLOSED ? "문이 모두 닫혔다" : k >= Balance.KARMA_EAR_BOSS_CLOSED ? "길에 사람이 줄었다" : k >= Balance.KARMA_EAR_HALF ? "개가 짖고 사람들이 움츠린다" : "";
    }

    // ---- 서낭당 창 -----------------------------------------------------------------------
    void DrawShrine(float x, float y, float w, GUIStyle body, GUIStyle btn)
    {
        GUI.Label(new Rect(x, y, w, 26), "서낭당 — 당할미의 공물상", body); y += 30;
        // 공물상
        string[] names3 = { "회복약", "새벽 부적", "씻김 부적" };
        int[] have = { Pack.Heal, Pack.Dawn, Pack.Cleanse };
        for (int i = 0; i < 3; i++)
        {
            var it = (ShopItem)i;
            if (GUI.Button(new Rect(x, y, w, 40), names3[i] + "  엽전 " + Shrine.Price(it) + "   (지님 " + have[i] + ")" + ShopHelp(it), btn))
                msg = Shrine.Buy(it, ledger, Pack) ? names3[i] + "을 샀다" : "엽전이 모자라거나 더 지닐 수 없다";
            y += 44;
        }
        y += 8;
        // 손보기: 장비 칸 고르기
        GUI.Label(new Rect(x, y, w, 26), "손보기 — 고를 장비", body); y += 30;
        for (int s = 0; s < 3; s++)
        {
            var it = lo.gear.Get((Slot)s);
            string label = Ko.SlotName((Slot)s) + ": " + (it == null ? "(비어 있음)" : Ko.ItemName(it) + " 옵션 " + it.Options.Count + " 홈 " + it.Sockets + "/" + Balance.SOCKET_MAX);
            GUI.enabled = it != null;
            if (GUI.Button(new Rect(x + s * (w / 3f), y, w / 3f - 4, 40), (selSlot == s ? "▶ " : "") + label, btn)) selSlot = s;
            GUI.enabled = true;
        }
        y += 48;
        var cur = lo.gear.Get((Slot)selSlot);
        if (cur != null)
        {
            GUI.enabled = Shrine.CanReroll(cur);
            if (GUI.Button(new Rect(x, y, w / 2f - 4, 40), "다시 굴리기 (옵션 1번)  엽전 " + Shrine.RerollCost(cur.Rerolls), btn))
            { msg = Shrine.Reroll(cur, 0, ledger, () => Random.value) ? "옵션을 다시 굴렸다" : "굴릴 수 없다"; lo.Refresh(); ledger.SetMaxHp(lo.stats.MaxHp); }
            GUI.enabled = Shrine.CanUpgrade(cur);
            if (GUI.Button(new Rect(x + w / 2f, y, w / 2f, 40), "매듭 올리기  " + UpgradeCost(cur), btn))
            { msg = Shrine.Upgrade(cur, ledger, () => Random.value) ? "등급이 올랐다" : "엽전이나 광석이 모자라다"; lo.Refresh(); ledger.SetMaxHp(lo.stats.MaxHp); }
            GUI.enabled = true; y += 44;
            if (GUI.Button(new Rect(x, y, w / 2f - 4, 40), "풀기(광석 " + Shrine.OreFor(cur.Rarity) + ")", btn) && Shrine.Dismantle(cur, ledger))
            { lo.gear.Remove((Slot)selSlot); lo.Refresh(); ledger.SetMaxHp(lo.stats.MaxHp); msg = "장비를 풀었다"; }
            GUI.enabled = cur.Sockets < Balance.SOCKET_MAX && ledger.Coin >= (cur.Sockets == 0 ? Balance.SOCKET_COST_1 : Balance.SOCKET_COST_2);
            if (GUI.Button(new Rect(x + w / 2f, y, w / 2f, 40), "홈 뚫기  엽전 " + (cur.Sockets == 0 ? Balance.SOCKET_COST_1 : Balance.SOCKET_COST_2), btn))
                msg = Shrine.Socket(cur, ledger) ? "인 홈을 뚫었다" : "엽전이 모자라다";
            GUI.enabled = true; y += 48;
        }
        if (GUI.Button(new Rect(x, y, 160, 44), "돌아가기", btn)) { shrineOpen = false; msg = ""; }
    }

    static string ShopHelp(ShopItem it)
    {
        return it == ShopItem.HealPotion ? " — 생명 40% 회복 (H)" : it == ShopItem.DawnCharm ? " — 그 밤 동트기 경고가 30초 일찍" : " — 밟은 얼룩 하나 지움 (X)";
    }

    static string UpgradeCost(ItemDef it)
    {
        return it.Rarity == Rarity.Crafted ? "엽전 " + Balance.UPGRADE_COIN_2 + " 광석 " + Balance.UPGRADE_ORE_2 : "엽전 " + Balance.UPGRADE_COIN_1 + " 광석 " + Balance.UPGRADE_ORE_1;
    }
}
