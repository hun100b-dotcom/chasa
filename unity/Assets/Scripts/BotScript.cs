// =============================================================================
// BotScript.cs — 첫 세션 자동 플레이 테스트 (?bot=1). 사람이 없어도 "시작 → 오프닝 → 단서 모으기 → 밤 싸움 → 나루 영감 처결"을
// 끝까지 걸어 보고, 막히는 지점을 로그로 남긴다. PC 에서 숨김 창(headless)으로 돌려 콘솔 로그([BOT] …)를 읽는다.
//
// 주소 옵션: ?bot=1 &speed=6 (비어 있는 낮 시계를 빨리 돌리는 배속, 기본 6) &god=0 (체력이 줄게 하려면 0, 기본 1) &max=1800 (실제 초 한계)
// 막힘 신호: ① 컷이 길이보다 오래 안 끝남 ② 단서 자리에 다가갔는데 단서가 안 열림 ③ 목표 자리에 못 감(위치 변화 없음)
//           ④ 단서가 모자라 보스를 천도할 수 없음 ⑤ 60초(실제) 동안 아무 진척 없음(단서·처결·보스·시각 구간 모두 그대로)
// 막히면 목표 쪽으로 순간이동해 계속 가고(횟수를 센다), 끝나면 [BOT-REPORT] 한 줄 요약을 낸다.
// =============================================================================
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using Chasa.Core;

public class BotScript : MonoBehaviour
{
    public Player player; public EnemyManager enemies; public JudgeSystem judge;

    public static bool Wanted() { return (Application.absoluteURL ?? "").Contains("bot=1"); }
    static float Param(string key, float def)
    {
        string u = Application.absoluteURL ?? ""; int i = u.IndexOf(key + "=");
        if (i < 0) return def;
        i += key.Length + 1; int j = i; while (j < u.Length && (char.IsDigit(u[j]) || u[j] == '.')) j++;
        float v; return float.TryParse(u.Substring(i, j - i), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out v) ? v : def;
    }

    float t;                       // 실제 경과(초)
    float speed, maxReal; bool god;
    bool overLogged; int deaths; float fightSince = -1f, ignoreFightUntil;   // 결과 화면 처리 / 같은 싸움에 너무 오래 매이면 잠깐 무시
    string goalName = ""; Vector3 goalPos; bool hasGoal;
    float lastProgressT, lastMoveCheckT; Vector3 lastMovePos; float goalSince; int unstucks;
    int lastScore = -1; ClockPhase lastPhase = (ClockPhase)(-1); string lastCut = "";
    float cutStartT;
    bool reported, bossSeen, bossTold, noClueWarned; int bossFightT0;
    readonly List<KeyValuePair<Vector3, string>> pend = new List<KeyValuePair<Vector3, string>>();
    readonly HashSet<string> warnedClue = new HashSet<string>(); readonly Dictionary<string, float> clueNearT = new Dictionary<string, float>();
    readonly List<string> issues = new List<string>();
    float nextAttack, stageT; bool casting;
    // 길찾기: 아트의 여유 폭 지도(1m 칸)를 A* 로 따라가 바위·물에 걸리지 않게 한다(직선으로만 가면 순간이동이 필요했다)
    GridPath nav; List<float[]> route; int routeIdx; Vector3 routeGoal;

    void Start()
    {
        speed = Param("speed", 6f); maxReal = Param("max", 1800f); god = Param("god", 1f) > 0.5f;
        LoadNav();
        Log("시작 speed=" + speed + " god=" + god + " max=" + maxReal + "s");
    }

    /// <summary>여유 폭 지도를 읽는다. 없으면 길찾기 없이 직선(예전 방식)으로 간다</summary>
    void LoadNav()
    {
        var ta = Resources.Load<TextAsset>("Map/nav_clearance"); if (ta == null) return;
        var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (!tex.LoadImage(ta.bytes)) return;
        int w = tex.width, h = tex.height; var px = tex.GetPixels32(); var cells = new byte[w * h];
        for (int z = 0; z < h; z++) for (int x = 0; x < w; x++) cells[z * w + x] = px[z * w + x].r;   // GetPixels32 는 맨 아래 줄이 0 번이라, 그림 위쪽=북(z 큰 쪽)과 z 가 그대로 맞는다
        nav = new GridPath(cells, w, h);
    }

    void Log(string s) { Debug.Log("[BOT] t=" + t.ToString("0") + "s " + Stamp() + " " + s); }
    string Stamp() { var c = judge != null ? judge.clock : null; return c == null ? "" : "d" + c.Day + " " + c.Phase + " " + c.Minutes.ToString("0.0") + "분"; }
    void Issue(string s) { issues.Add("[" + t.ToString("0") + "s " + Stamp() + "] " + s); Log("문제: " + s); }

    int Score()
    {
        // 진척 점수: 단서 수 + 처결 수(넋·기억·엽전 합) + 보스 결과 + 시각 구간 바뀜 횟수 + 본 컷 수
        int clues = 0; foreach (var c in judge.clueBook.All) clues++;
        return clues * 1000 + judge.ledger.Neok + judge.ledger.Memory * 3 + judge.ledger.Coin + judge.BossOutcomeNow * 5000 + phaseChanges * 700 + cutsSeen * 400;
    }
    int phaseChanges, cutsSeen;

    void Update()
    {
        if (judge == null || judge.clock == null || reported) return;
        float dt = Time.unscaledDeltaTime; t += dt;
        judge.godMode = god;
        var clk = judge.clock;
        // ① 시각 구간·컷 감시
        if (clk.Phase != lastPhase) { if ((int)lastPhase >= 0) phaseChanges++; lastPhase = clk.Phase; Log("시각 구간 → " + clk.Phase + " 단서 " + ClueCount() + "/" + Balance.BOSS_CLUES_REQUIRED + " 넋 " + judge.ledger.Neok); noClueWarned = false; }
        if (judge.cuts.Active)
        {
            string id = judge.cuts.CurId;
            if (id != lastCut) { lastCut = id; cutStartT = t; cutsSeen++; Log("컷 시작 " + id); }
            if (t - cutStartT > judge.cuts.CurDuration + 10f && !warnedClue.Contains("cut" + id)) { warnedClue.Add("cut" + id); Issue("컷이 안 끝남: " + id + " (길이 " + judge.cuts.CurDuration + "초, 실제 " + (t - cutStartT).ToString("0") + "초 지남)"); }
            lastProgressT = t;   // 컷 중엔 막힘으로 세지 않는다(위 경고가 따로 있다)
            return;
        }
        else if (lastCut != "") { Log("컷 끝 " + lastCut + " (" + (t - cutStartT).ToString("0") + "초)"); lastCut = ""; }
        judge.StartPlaying();
        // 쓰러졌거나 동이 터서 결과 화면이 뜨면(god=0): 문제로 적고 다시 시작한다(예전엔 Space 를 안 눌러 28분을 멈춰 있었다)
        if (judge.NightOver) { if (!overLogged) { overLogged = true; deaths++; Issue("결과 화면(쓰러짐·동틈) #" + deaths + " — 다시 시작"); } if (judge.BotRestart()) { overLogged = false; hasGoal = false; lastProgressT = t; } return; }
        // ② 진척 감시
        int sc = Score();
        if (sc != lastScore) { lastScore = sc; lastProgressT = t; }
        if (t - lastProgressT > 60f) { Stuck(); lastProgressT = t; }
        if (deaths >= 5) { Finish("5번 쓰러져 중단"); return; }
        if (t > maxReal) { Finish("시간 초과(" + maxReal + "초)"); return; }
        if (judge.BossOutcomeNow != 0) { Finish(judge.BossOutcomeNow == 1 ? "보스 천도 성공" : "보스 파혼"); return; }
        // ③ 무엇을 할까
        bool night = clk.Phase == ClockPhase.Night || clk.Phase == ClockPhase.Dusk;
        clk.Speed = (night ? 1f : speed);   // 낮 대기는 빨리, 밤 싸움은 실제 속도
        if (judge.Casting) { player.CommandStop(); return; }   // 천도 시전 중엔 가만히
        var boss = FindBoss();
        if (boss != null && ClueCount() >= Balance.BOSS_CLUES_REQUIRED && TickBoss(boss)) return;
        if (ClueCount() >= Balance.BOSS_CLUES_REQUIRED && boss != null) { /* 보스로 */ }
        if (TickFight()) return;
        if (TickClues()) return;
        if (boss != null && ClueCount() >= Balance.BOSS_CLUES_REQUIRED) { GoTo(boss.Pos, "보스 나루 영감"); return; }
        if (!night && !noClueWarned) { noClueWarned = true; Log("할 일 없음: 켜진 단서 자리 " + (judge.npcs != null ? judge.npcs.ActiveSpots : -1) + "곳, 단서 " + ClueCount() + "/" + Balance.BOSS_CLUES_REQUIRED + " — 시계를 돌려 다음 구간을 기다린다"); }
        if (night && TickNamedWander()) return;
        // 아무것도 없으면 마을 어귀로 걸어가 기다린다
        GoTo(new Vector3(FieldRules.VillageX, 0f, FieldRules.VillageZ), "마을 대기");
    }

    int ClueCount() { int n = 0; foreach (var c in judge.clueBook.All) if (c.StartsWith("B01-")) n++; return n; }

    Enemy FindBoss()
    {
        foreach (var e in enemies.list) if (e != null && e.soul.Boss && e.soul.BossId == 1 && !e.gone) return e;
        return null;
    }

    /// <summary>보스: 가까이 가서 때리고, 무릎 꿇으면 천도(단서가 모자라면 파혼). 해야 할 일이 있었으면 true</summary>
    bool TickBoss(Enemy boss)
    {
        float d = Vector3.Distance(boss.Pos, player.Pos);
        if (!bossSeen) { bossSeen = true; Log("보스 나루 영감에게 간다. 단서 " + ClueCount()); }
        if (boss.kneeling)
        {
            if (judge.CanTendoNow(boss)) { if (d > Balance.JUDGE_RANGE * 0.8f) { player.CommandMove(boss.Pos); return true; } player.CommandStop(); judge.CommandTendo(); return true; }
            if (!bossTold) { bossTold = true; Issue("보스가 무릎 꿇었는데 천도할 수 없음(단서 " + ClueCount() + "/" + Balance.BOSS_CLUES_REQUIRED + " 또는 인 부족) → 파혼으로 마무리"); }
            if (d > 3f) { player.CommandMove(boss.Pos); return true; }
            player.CommandStop(); judge.CommandPahon(); return true;
        }
        if (d > 40f) { GoTo(boss.Pos, "보스"); return true; }
        if (Time.time >= nextAttack) { player.CommandAttack(boss); nextAttack = Time.time + 0.45f; }
        return true;
    }

    /// <summary>가까이(25m) 서 있는 혼은 때리고, 무릎 꿇은 혼은 천도한다. 했으면 true</summary>
    bool TickFight()
    {
        // 한 싸움에 25초 넘게 매이면(덩어리 혼 무리처럼 끝이 안 나는 곳) 20초는 싸움을 무시하고 목표로 간다(god 일 땐 맞아도 괜찮다)
        if (t < ignoreFightUntil) return false;
        Enemy near = null, kneel = null, lumpKneel = null; float nd = 25f, kd = 30f, ld = 6f;
        foreach (var e in enemies.list)
        {
            if (e == null || e.soul.Boss) continue;
            float d = Vector3.Distance(e.Pos, player.Pos);
            if (e.kneeling && judge.CanTendoNow(e) && d < kd) { kd = d; kneel = e; }
            else if (e.kneeling && e.alive && d < ld) { ld = d; lumpKneel = e; }   // 무릎 꿇었지만 천도 못 하는 혼(덩어리 등) → 파혼으로 치운다
            else if (e.alive && !e.kneeling && e.Targetable && d < nd) { nd = d; near = e; }
        }
        if (kneel == null && lumpKneel != null) { player.CommandStop(); judge.CommandPahon(); return true; }
        if (kneel == null && near == null) fightSince = -1f;
        else { if (fightSince < 0f) fightSince = t; if (t - fightSince > 25f) { Log("한 싸움 25초 넘음 → 20초 무시하고 목표로"); ignoreFightUntil = t + 20f; fightSince = -1f; return false; } }
        if (kneel != null)
        {
            if (kd > Balance.JUDGE_RANGE * 0.8f) { player.CommandMove(kneel.Pos); return true; }
            player.CommandStop(); if (!judge.Casting) judge.CommandTendo(); return true;
        }
        if (near != null) { if (Time.time >= nextAttack) { player.CommandAttack(near); nextAttack = Time.time + 0.45f; } return true; }
        return false;
    }

    /// <summary>켜진 단서 자리 중 가장 가까운 곳으로 간다. 닿았는데 단서가 안 열리면 문제로 적는다</summary>
    bool TickClues()
    {
        if (judge.npcs == null) return false;
        judge.npcs.PendingClues(pend);
        if (pend.Count == 0) return false;
        KeyValuePair<Vector3, string> best = pend[0]; float bd = 1e9f;
        foreach (var p in pend) { float d = Vector2.Distance(new Vector2(p.Key.x, p.Key.z), new Vector2(player.Pos.x, player.Pos.z)); if (d < bd) { bd = d; best = p; } }
        if (bd <= 3.0f)
        {
            // 단서 자리 반경(3.5m) 안인데 단서가 계속 안 열린다 → 업이 높아 귀가 닫혔거나 데이터 문제
            float since; if (!clueNearT.TryGetValue(best.Value, out since)) { since = t; clueNearT[best.Value] = t; }
            if (t - since > 6f && warnedClue.Add(best.Value)) Issue("단서가 안 열림: " + best.Value + " (업 " + judge.ledger.Karma + ", 이미 6초 곁에 서 있음)");
            return true;   // 곁에 서서 기다린다
        }
        GoTo(best.Key, "단서 " + best.Value);
        return true;
    }

    bool TickNamedWander()
    {
        if (judge.named == null) return false;
        var l = new List<KeyValuePair<Vector3, string>>(); judge.named.PendingPositions(l);
        KeyValuePair<Vector3, string>? best = null; float bd = 1e9f;
        foreach (var p in l) { float d = Vector2.Distance(new Vector2(p.Key.x, p.Key.z), new Vector2(player.Pos.x, player.Pos.z)); if (d < bd) { bd = d; best = p; } }
        if (best == null || bd < 4f) return false;
        GoTo(best.Value.Key, "이름혼 " + best.Value.Value); return true;
    }

    void GoTo(Vector3 pos, string name)
    {
        if (!hasGoal || goalName != name) { goalName = name; goalPos = pos; hasGoal = true; goalSince = t; lastMovePos = player.Pos; lastMoveCheckT = t; Log("목표 → " + name + " (" + Vector3.Distance(pos, player.Pos).ToString("0") + "m)"); }
        goalPos = pos;
        player.CommandMove(NextStep(pos));
        // 목표로 가는데 8초(실제) 동안 거의 안 움직이면 막힌 것: 순간이동으로 건너뛴다
        if (t - lastMoveCheckT > 8f)
        {
            if (Vector3.Distance(player.Pos, lastMovePos) < 1.0f) { Issue("이동이 막힘: 목표 '" + name + "' 까지 " + Vector3.Distance(pos, player.Pos).ToString("0") + "m, 위치 변화 없음 " + player.Pos.ToString("0") + " → 순간이동"); Warp(pos); }
            lastMovePos = player.Pos; lastMoveCheckT = t;
        }
        if (t - goalSince > 120f) { Issue("목표 '" + name + "' 에 120초 넘게 못 감 → 순간이동"); Warp(pos); goalSince = t; }
    }

    /// <summary>멀면(10m 넘게) 웨이포인트를 차례로 따라가고, 가까우면 목표로 곧장 간다</summary>
    Vector3 NextStep(Vector3 pos)
    {
        if (nav == null) return pos;
        var me = player.Pos; float dist = Vector2.Distance(new Vector2(me.x, me.z), new Vector2(pos.x, pos.z));
        if (dist < 10f) { route = null; return pos; }
        if (route == null || Vector2.Distance(new Vector2(routeGoal.x, routeGoal.z), new Vector2(pos.x, pos.z)) > 6f)
        {
            route = nav.Find(me.x, me.z, pos.x, pos.z, 1.0f); if (route == null) route = nav.Find(me.x, me.z, pos.x, pos.z, 0.5f);
            routeGoal = pos; routeIdx = 0;
            if (route == null) { Issue("길 못 찾음: " + me.ToString("0") + " → " + pos.ToString("0")); return pos; }
        }
        while (routeIdx < route.Count - 1 && Vector2.Distance(new Vector2(me.x, me.z), new Vector2(route[routeIdx][0], route[routeIdx][1])) < 2.5f) routeIdx++;
        if (routeIdx >= route.Count) return pos;
        var wp = route[routeIdx]; return new Vector3(wp[0], me.y, wp[1]);
    }

    void Warp(Vector3 pos)
    {
        unstucks++;
        var dir = (pos - player.Pos); dir.y = 0f; var to = dir.magnitude > 6f ? player.Pos + dir.normalized * Mathf.Max(6f, dir.magnitude - 2.5f) : pos;
        player.CommandStop(); player.Pos = new Vector3(to.x, player.Pos.y, to.z);
        if (judge.onTeleport != null) judge.onTeleport(player.Pos);
    }

    void Stuck()
    {
        var sb = new StringBuilder();
        sb.Append("60초 진척 없음 — 목표 '").Append(goalName).Append("' 위치 ").Append(player.Pos.ToString("0"));
        sb.Append(" 시각 ").Append(Stamp()).Append(" 단서 ").Append(ClueCount()).Append("/").Append(Balance.BOSS_CLUES_REQUIRED);
        sb.Append(" 켜진 자리 ").Append(judge.npcs != null ? judge.npcs.ActiveSpots : -1).Append(" 적 ").Append(enemies.list.Count);
        sb.Append(" 시전 ").Append(judge.Casting).Append(" 컷 ").Append(judge.cuts.Active);
        Issue(sb.ToString());
        if (hasGoal) Warp(goalPos);
    }

    void Finish(string why)
    {
        reported = true;
        var sb = new StringBuilder();
        sb.Append("{\"결과\":\"").Append(why).Append("\",\"실제초\":").Append(t.ToString("0")).Append(",\"게임\":\"").Append(Stamp()).Append("\"");
        sb.Append(",\"단서\":").Append(ClueCount()).Append(",\"넋\":").Append(judge.ledger.Neok).Append(",\"기억\":").Append(judge.ledger.Memory).Append(",\"업\":").Append(judge.ledger.Karma);
        sb.Append(",\"쓰러짐\":").Append(deaths).Append(",\"막힘순간이동\":").Append(unstucks).Append(",\"컷\":").Append(cutsSeen).Append(",\"문제\":[");
        for (int i = 0; i < issues.Count; i++) { if (i > 0) sb.Append(','); sb.Append('"').Append(issues[i].Replace("\"", "'")).Append('"'); }
        sb.Append("]}");
        Debug.Log("[BOT-REPORT] " + sb);
        Report = sb.ToString();
    }

    public static string Report = "";

    void OnGUI()
    {
        if (judge == null) return;
        GUI.color = new Color(1f, 1f, 1f, 0.85f);
        GUI.Label(new Rect(12, Screen.height - 46, 900, 40), "[BOT] " + (reported ? Report : goalName + "  단서 " + (judge.clueBook != null ? ClueCount() : 0) + "/" + Balance.BOSS_CLUES_REQUIRED + "  막힘 " + unstucks));
        GUI.color = Color.white;
    }
}
