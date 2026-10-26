// =============================================================================
// NamedSoulSpawns.cs — 첫 세션의 이름혼(박돌쇠·윤 소사·연이·장 둑지기·곽 뱃꾼·방물장수 막례)을 정해진 자리에 세운다.
// 서사 첫 세션 흐름의 '갈림'이 되는 혼들이다. 이름이 있어 천도하면 그 혼의 기억(MemoryLines)이 나오고, 인이 흐릴수록 처결 대기가 길다.
//
// 규칙: 밤에, 플레이어가 가까이(60m) 오면 선다 / 멀어지면(150m) 걷히고 다시 오면 또 선다 / 처결(천도·파혼)되면 다시는 안 선다.
// 자리는 임시(tools/build_named_souls.py 의 PLACES). 확정되면 그 표만 바꾸면 된다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class NamedSoulSpawns
{
    [System.Serializable] class Row { public string name, label; public float x, z, wait; public int age, after_boss; public bool ledger, water, mujeok; }   // name=기억 찾는 열쇠, label=머리 위 이름표(단서를 미리 안 새게 따로), after_boss=보스 N마리 처결 뒤에 나타남, water=썰물 때만 보이는 갯벌 자리
    [System.Serializable] class Group { public string id; public float x, z, trigger; public int n; public bool frozen; }
    [System.Serializable] class FileData { public Row[] souls; public Group[] groups; }
    readonly List<Group> groups = new List<Group>();
    readonly HashSet<string> groupDone = new HashSet<string>();
    class Entry { public Row row; public Enemy live; public bool done; }

    /// <summary>명부에 없는 이름혼(처결해도 넋·엽전만 얻는다)의 이름 모음 — 첫 5분 안내가 쓴다</summary>
    public static readonly HashSet<string> OffLedger = new HashSet<string>();
    const float SpawnDist = 60f, ReleaseDist = 150f;
    readonly List<Entry> entries = new List<Entry>();
    readonly EnemyManager enemies;

    public NamedSoulSpawns(EnemyManager enemies)
    {
        this.enemies = enemies;
        var ta = Resources.Load<TextAsset>("Data/named_souls");
        if (ta == null) return;
        var f = JsonUtility.FromJson<FileData>(ta.text);
        if (f != null && f.souls != null) foreach (var r in f.souls) { entries.Add(new Entry { row = r }); if (!r.ledger) OffLedger.Add(r.name); }
        if (f != null && f.groups != null) groups.AddRange(f.groups);
        if (FieldRules.Act2)   // 2막 장례 대상 이름혼 9명(tools/build_named_souls_act2.py)
        {
            var t2 = Resources.Load<TextAsset>("Data/named_souls_act2");
            var f2 = t2 != null ? JsonUtility.FromJson<FileData>(t2.text) : null;
            if (f2 != null && f2.souls != null) foreach (var r in f2.souls) { entries.Add(new Entry { row = r }); OffLedger.Add(r.name); }
        }
        if (FieldRules.Act3)   // 3막 장례 대상 이름혼 10명(tools/build_named_souls_act3.py)
        {
            var t3 = Resources.Load<TextAsset>("Data/named_souls_act3");
            var f3 = t3 != null ? JsonUtility.FromJson<FileData>(t3.text) : null;
            if (f3 != null && f3.souls != null) foreach (var r in f3.souls) { entries.Add(new Entry { row = r }); OffLedger.Add(r.name); }
        }
    }

    /// <summary>daylight: 하늘 밝기(0=밤). 밤에만 혼이 보인다</summary>
    /// <summary>자동 플레이 테스트용: 아직 처결 안 된 이름혼의 자리</summary>
    /// <summary>이 이름의 혼이 이미 처결(천도·파혼)되었나</summary>
    public bool IsDone(string name) { foreach (var e in entries) if (e.row.name == name) return e.done || (e.live != null && e.live.gone); return false; }

    public void PendingPositions(List<KeyValuePair<Vector3, string>> into)
    {
        into.Clear();
        foreach (var e in entries) if (!e.done) into.Add(new KeyValuePair<Vector3, string>(new Vector3(e.row.x, 0f, e.row.z), e.row.name));
    }

    public System.Func<int> BossesDone;   // 1막 보스를 몇 마리 처결했나(김 영감 같은 '보스 둘 뒤에 나타남' 조건용). 안 걸어 두면 늘 0
    public System.Func<bool> IsEbb;       // 지금 썰물인가(갯벌 자리 water 혼용). 안 걸어 두면 늘 보임
    public float AppearMult = 1f;   // 안개 +50%: 나타나는 거리 배율

    public void Tick(Vector3 playerPos, float daylight)
    {
        bool night = daylight < 0.35f;
        if (night) foreach (var g in groups) TickGroup(g, playerPos);
        foreach (var e in entries)
        {
            if (e.done) continue;
            if (e.live != null)
            {
                if (e.live.gone) { e.done = true; e.live = null; continue; }   // 처결됨(천도·파혼) → 다시는 안 나온다
                float dd = new Vector2(e.row.x - playerPos.x, e.row.z - playerPos.z).magnitude;
                if (dd >= ReleaseDist) { enemies.Remove(e.live); e.live = null; }   // 멀어지면 걷어낸다(처결 전이라 다시 선다)
                continue;
            }
            if (!night) continue;
            if (e.row.after_boss > 0 && (BossesDone == null ? 0 : BossesDone()) < e.row.after_boss) continue;   // M6: 보스를 충분히 처결한 뒤에야 선다
            if (e.row.water && IsEbb != null && !IsEbb()) continue;   // M7: 갯벌 혼은 썰물 때만 보인다
            float d = new Vector2(e.row.x - playerPos.x, e.row.z - playerPos.z).magnitude;
            if (d > SpawnDist * AppearMult) continue;   // 안개 낀 밤: 이름혼이 더 멀리서부터 나타난다(+50%)
            float x = e.row.x, z = e.row.z;
            MapLayout.PushOut(ref x, ref z, Config.ENEMY_RADIUS + 1f);
            var en = enemies.SpawnCamp(new Vector3(x, 0f, z), true);
            en.MakeNamed(e.row.name, (SoulKind)Mathf.Clamp(e.row.age, 0, 2), e.row.wait, string.IsNullOrEmpty(e.row.label) ? null : e.row.label);   // M5: 이름표(label)와 기억 키(name) 분리
            en.extra = false;
            e.live = en;
        }
    }

    /// <summary>갈림: 처음 가까이 오면 한 번 세운다. frozen 이면 처결 대기가 멈춘 채 무릎 꿇는다(첫 고르기 연습). 둘 이상이면 플레이어를 둘러싼다</summary>
    void TickGroup(Group g, Vector3 playerPos)
    {
        if (groupDone.Contains(g.id)) return;
        if (new Vector2(g.x - playerPos.x, g.z - playerPos.z).magnitude > g.trigger) return;
        groupDone.Add(g.id);
        for (int i = 0; i < g.n; i++)
        {
            float a = g.n == 1 ? 0f : i / (float)g.n * Mathf.PI * 2f + 0.4f, r = g.n == 1 ? 0f : 5f;
            float x = (g.n == 1 ? g.x : playerPos.x) + Mathf.Cos(a) * r, z = (g.n == 1 ? g.z : playerPos.z) + Mathf.Sin(a) * r;
            MapLayout.PushOut(ref x, ref z, Config.ENEMY_RADIUS + 1f);
            var en = enemies.SpawnCamp(new Vector3(x, 0f, z), true);
            if (g.frozen) { en.soul.Frozen = true; en.soul.Kind = SoulKind.Fresh; }   // 정확히 한 마리 연습용: 시간이 멈춘 처결
        }
    }
}
