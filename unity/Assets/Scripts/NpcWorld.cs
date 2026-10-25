// =============================================================================
// NpcWorld.cs — 필드의 산 사람(NPC)과 낮 시간표, 엿듣기·지켜보기·만져 보기로 단서 얻기 (기획 5단계, 1차).
//
// 데이터: Resources/Data/npc_flat.json (서사팀 data/npc_act1.json 을 tools/build_npc_data.py 가 납작하게 만든 것).
// 어떻게 동작하나?
//   1) 지금 시간대(동틀녘/낮/해질녘/밤)에 해당하는 일정 줄만 켠다. 대사나 단서가 있는 줄만 사람(또는 사물 표시)을 세운다.
//   2) 자리는 구역(Hub·Village…)의 중심점 둘레에 '장소 이름 해시'로 정해 둔다. 서사 데이터엔 좌표가 없어서의 임시 배치이고,
//      아트가 좌표를 주면 anchors 만 바꾸면 된다.
//   3) 플레이어가 NoticeRadius 안으로 다가가면 대사가 자막으로 뜨고(업이 높으면 반쪽/닫힘), 단서가 있으면 장부에 적힌다.
// 대사는 모두 산 사람끼리의 말이다(차사에게 하지 않음) — 그래서 '말을 걸지' 않고 곁에 서서 '듣는다'.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class NpcWorld
{
    [System.Serializable] class Row { public string npc, name, zone, place, verb, line, half, clue; public int region, unlock, time; }
    [System.Serializable] class ClueRow { public string boss, id, verb, zone, place, npc, what; public int time; }
    [System.Serializable] class PlaceRow { public string place; public float ox, oz, ax, az; public int abs; }
    [System.Serializable] class FileData { public Row[] entries; public ClueRow[] clues; public PlaceRow[] places; }

    class Spot
    {
        public Row row; public string clue, line, half, verb, label; public Vector3 pos; public GameObject view; public NpcActor actor; public bool isObject; public DwellTimer dwell = new DwellTimer();
    }

    const float NoticeRadius = 3.5f;     // 이 거리 안이면 듣는다
    const float SpawnRadius = 80f;       // 이 거리 안의 사람만 세운다(멀리는 부품 낭비)
    static readonly Dictionary<string, Vector2> Anchors = new Dictionary<string, Vector2>
    {
        { "Hub", new Vector2(188f, 36f) }, { "Village", new Vector2(196f, 62f) }, { "Field", new Vector2(160f, 180f) },
        { "Ravine", new Vector2(356f, 324f) }, { "Shrine", new Vector2(580f, 552f) },
        { "Market", new Vector2(36f, 388f) }, { "Yamen", new Vector2(36f, 330f) }, { "Plague", new Vector2(34f, 469f) },   // 검은여울(서쪽 둑): 3호 보스 단서 자리. 아트 확정 좌표
    };

    static readonly Dictionary<string, Vector2> placeAbs = new Dictionary<string, Vector2>();   // 아트가 확정한 필드 절대 좌표(동 +x · 북 +z). 있으면 이쪽이 우선
    static readonly Dictionary<string, Vector2> placeOffset = new Dictionary<string, Vector2>();   // 서사가 정한 장소별 위치(구역 중심 기준, 동 +x · 북 +z)
    readonly List<Spot> spots = new List<Spot>();        // 지금 시간대에 켜진 자리들
    readonly List<Spot> all = new List<Spot>();
    readonly ClueBook book;
    readonly Transform root;
    readonly System.Func<int> karma;
    readonly System.Func<int> nightNo;                   // 지금이 몇 번째 밤인가(NPC 등장 조건)
    int builtPhase = -1, builtNight = -1;
    HashSet<string> heard = new HashSet<string>();       // 오늘(이 시간대) 이미 들은 자리
    public System.Action onClue;                         // 단서를 처음 얻었을 때(안내용)
    public System.Func<bool> inCombat;                   // 10m 안에 깨어 있는 혼이 있으면 true: 듣는 진행이 멈춘다(기획 §2-3)
    public readonly HeardLog Log = new HeardLog();       // 들은 말 기록(명부 '들은 말' 탭용)
    public float DwellRatio;                             // 지금 듣는 중인 자리의 진행(0~1). 화면 고리용
    public Vector3 DwellPos;
    public string Subtitle; public float SubtitleT;      // JudgeSystem 이 화면에 그린다

    public NpcWorld(ClueBook book, System.Func<int> karma, System.Func<int> nightNo)
    {
        this.book = book; this.karma = karma; this.nightNo = nightNo;
        root = new GameObject("NpcWorld").transform;
        var ta = Resources.Load<TextAsset>("Data/npc_flat");
        if (ta == null) return;
        var f = JsonUtility.FromJson<FileData>(ta.text);
        placeOffset.Clear(); placeAbs.Clear();
        if (f.places != null) foreach (var pl in f.places) { placeOffset[pl.place] = new Vector2(pl.ox, pl.oz); if (pl.abs == 1) placeAbs[pl.place] = new Vector2(pl.ax, pl.az); }
        var npcClueIds = new HashSet<string>();
        foreach (var r in f.entries)
        {
            if (!Anchors.ContainsKey(r.zone)) continue;                       // 아직 땅이 없는 구역(장터거리 등)은 건너뜀
            if (string.IsNullOrEmpty(r.line) && string.IsNullOrEmpty(r.clue)) continue;   // 말도 단서도 없는 줄(집 안 등)
            all.Add(new Spot { row = r, clue = r.clue, line = r.line, half = r.half, verb = r.verb, label = r.name, pos = PosFor(r.zone, r.place) });
            if (!string.IsNullOrEmpty(r.clue)) npcClueIds.Add(r.clue);
        }
        // 사람 없이 사물에만 달린 단서(부러진 삿대 등): 낮에 만져 본다
        foreach (var c in f.clues)
            if (string.IsNullOrEmpty(c.npc) && c.verb != "밤 대체" && Anchors.ContainsKey(c.zone) && !npcClueIds.Contains(c.id))
                all.Add(new Spot { row = new Row { npc = "obj", name = c.place, zone = c.zone, place = c.place, time = c.time, unlock = 1, region = 1 }, clue = c.id, line = c.what, half = c.what, verb = c.verb, label = c.place, pos = PosFor(c.zone, c.place), isObject = true });
    }

    /// <summary>처결 결과로 바뀐 풍경 한 곳을 더한다(예: 보스를 천도하면 나루에 배가 묶여 있다). 다가서면 글이 뜬다. timeSlot: 0 동틀녘 1 낮 2 해질녘 3 밤</summary>
    public void AddScenery(Vector3 pos, string text, int timeSlot)
    {
        all.Add(new Spot { row = new Row { npc = "scn", name = "풍경", zone = "Ravine", place = text, time = timeSlot, unlock = 1, region = 1 }, clue = "", line = text, half = text, verb = "지켜보기", label = "풍경", pos = pos, isObject = true });
        builtPhase = -1;   // 켜진 자리를 다음 프레임에 다시 고른다
    }

    /// <summary>구역 중심에서 장소 이름으로 정한 방향·거리(6~16m)의 자리. 막힌 곳이면 밀려난다</summary>
    static Vector3 PosFor(string zone, string place)
    {
        Vector2 off;
        if (placeAbs.TryGetValue(place, out off))   // 아트 확정 좌표: 그대로(막힌 곳이면만 살짝 밀어낸다)
        {
            float ax = off.x, az = off.y;
            MapLayout.PushOut(ref ax, ref az, 0.6f);
            return new Vector3(ax, 0f, az);
        }
        if (placeOffset.TryGetValue(place, out off))   // 서사가 장소 위치를 정해 줬으면 그대로(아트 확정 전 임시 값)
        {
            var a0 = Anchors[zone]; float px = a0.x + off.x, pz = a0.y + off.y;
            MapLayout.PushOut(ref px, ref pz, 0.6f);
            return new Vector3(px, 0f, pz);
        }
        int h = 17; foreach (char ch in place) h = h * 31 + ch;
        float a = (h & 1023) / 1024f * Mathf.PI * 2f, d = 6f + ((h >> 10) & 255) / 255f * 10f;
        var an = Anchors[zone];
        float x = an.x + Mathf.Cos(a) * d, z = an.y + Mathf.Sin(a) * d;
        MapLayout.PushOut(ref x, ref z, 1.0f);
        return new Vector3(x, 0f, z);
    }

    public void Tick(float dt, Vector3 playerPos, ClockPhase phase)
    {
        SubtitleT = Mathf.Max(0f, SubtitleT - dt);
        int ph = (int)phase, night = nightNo();
        if (ph != builtPhase || night != builtNight) Rebuild(ph, night);
        bool dwelling = false;
        foreach (var s in spots)
        {
            float d = new Vector2(s.pos.x - playerPos.x, s.pos.z - playerPos.z).magnitude;
            if (s.view != null) s.view.SetActive(d < SpawnRadius);
            if (s.actor != null) { s.actor.hasLook = d < 12f; s.actor.lookAt = playerPos; s.actor.talking = d <= NoticeRadius + 1f; }   // 가까우면 돌아보고 말하는 동작
            // 엿듣기·지켜보기는 원 안에 머무르면 저절로(엿듣기 3m 6초, 업 10 이상 2m · 지켜보기 6m 15초). 그 밖(만져 보기·사물)은 예전처럼 가까이 오면
            bool eaves = Eavesdrop.IsEavesVerb(s.verb), watch = s.verb == "지켜보기";
            if (eaves || watch)
            {
                float rad = eaves ? (karma() >= 10 ? Balance.EAVESDROP_RADIUS_EAR : Balance.EAVESDROP_RADIUS) : Balance.WATCH_RADIUS;
                float need = eaves ? Balance.EAVESDROP_TIME : Balance.WATCH_TIME;
                bool done = s.dwell.Tick(dt, d <= rad, inCombat != null && inCombat(), need);
                if (d <= rad && s.dwell.Progress > 0f && !heard.Contains(HeardKey(s))) { DwellRatio = s.dwell.Ratio(need); DwellPos = s.pos; dwelling = true; }
                if (done) Notice(s);
            }
            else if (d <= NoticeRadius) Notice(s);
        }
        if (!dwelling) DwellRatio = 0f;
    }

    /// <summary>자동 플레이 테스트용: 지금 켜진 자리 중 아직 못 얻은 단서가 달린 곳의 좌표·이름을 모은다</summary>
    public void PendingClues(List<KeyValuePair<Vector3, string>> into)
    {
        into.Clear();
        foreach (var s in spots) if (!string.IsNullOrEmpty(s.clue) && !book.Has(s.clue)) into.Add(new KeyValuePair<Vector3, string>(s.pos, s.clue + " " + s.label + "@" + s.row.place));
    }

    /// <summary>자동 플레이 테스트용: 켜진 자리 수(단서 없는 것 포함)</summary>
    public int ActiveSpots { get { return spots.Count; } }

    /// <summary>시간대나 밤 수가 바뀌면 켜진 자리를 다시 고른다</summary>
    void Rebuild(int ph, int night)
    {
        builtPhase = ph; builtNight = night; heard.Clear();
        foreach (var s in spots) if (s.view != null) Object.Destroy(s.view);
        spots.Clear();
        foreach (var s in all)
        {
            // WorldClock 의 ClockPhase(Dawn0 Day1 Dusk2 Night3) 와 데이터의 time(0 새벽 1 낮 2 저녁 3 밤)이 같은 순서다
            // 첫 보스(B01) 단서는 첫날부터 모두 열려 있다(서사 확정: 첫 저녁~밤에 4개를 얻을 수 있게)
            bool firstBoss = !string.IsNullOrEmpty(s.clue) && s.clue.StartsWith("B01-");
            if (s.row.time != ph || (s.row.unlock > night && !firstBoss)) continue;
            s.view = MakeView(s);
            spots.Add(s);
        }
    }

    GameObject MakeView(Spot s)
    {
        // 사람이면 아트의 3D 모델(npc_N101 …)을 먼저 시도한다. 한 칸에 여럿(104·110·204)은 첫 모델(a)을 쓴다
        if (!s.isObject && s.row.npc != null && s.row.npc.Length > 2)
        {
            string id = s.row.npc.Replace("-", "");
            var actor = NpcActor.Create(root, "Models/Npc/npc_" + id, s.pos) ?? NpcActor.Create(root, "Models/Npc/npc_" + id + "a", s.pos);
            if (actor != null) { s.actor = actor; actor.gameObject.SetActive(false); return actor.gameObject; }
        }
        PrimitiveType shape = s.isObject ? PrimitiveType.Cube : PrimitiveType.Capsule;
        var g = GameObject.CreatePrimitive(shape);
        Object.Destroy(g.GetComponent<Collider>());
        g.transform.SetParent(root, false);
        g.transform.position = s.pos + Vector3.up * (s.isObject ? 0.3f : 0.9f);
        g.transform.localScale = s.isObject ? new Vector3(0.5f, 0.5f, 0.5f) : new Vector3(0.6f, 0.9f, 0.6f);
        // 산 사람은 따뜻한 한지색, 단서가 있는 자리는 은은한 보랏빛(기억의 단서 색)으로 눈에 띄게(임시 도형: 아트가 모델을 주면 교체)
        var col = !string.IsNullOrEmpty(s.clue) && !book.Has(s.clue) ? ChasaPalette.MemoryRim : new Color(0.85f, 0.78f, 0.62f);
        g.GetComponent<Renderer>().sharedMaterial = s.isObject ? U.Unlit(col) : U.Matte(col);
        g.SetActive(false);
        return g;
    }

    static string HeardKey(Spot s) { return s.row.npc + "|" + s.row.place + "|" + s.verb + "|" + s.clue; }

    void Notice(Spot s)
    {
        if (!heard.Add(HeardKey(s))) return;                                         // 이 시간대엔 한 번만
        bool bossClue = !string.IsNullOrEmpty(s.clue) && s.clue.StartsWith("B");
        var mode = Eavesdrop.Mode(karma(), Eavesdrop.IsEavesVerb(s.verb), bossClue);
        if (mode == EavesMode.Closed)
        {
            Say("…갑자기 춥네.");                                           // 귀가 닫혔다: 사람이 말을 접고 떠난다
            return;
        }
        string text = mode == EavesMode.Half && !string.IsNullOrEmpty(s.half) ? s.half : s.line;
        if (!string.IsNullOrEmpty(text)) { Say((s.isObject ? "" : s.label + ": ") + "「" + text + "」"); Log.Add(s.label, s.row.place, text, s.clue, s.row.time); }
        if (!string.IsNullOrEmpty(s.clue) && book.Add(s.clue))
        {
            Sfx.Play("sfx.clue");
            if (onClue != null) onClue();
            if (s.view != null && s.actor == null) s.view.GetComponent<Renderer>().sharedMaterial = U.Matte(new Color(0.85f, 0.78f, 0.62f));   // 얻었으니 보랏빛이 꺼진다(도형 대역일 때만)
        }
    }

    void Say(string t) { Subtitle = t; SubtitleT = 4f; }
}
