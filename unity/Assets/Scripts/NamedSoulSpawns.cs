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
    [System.Serializable] class Row { public string name; public float x, z, wait; public int age; public bool ledger; }
    [System.Serializable] class FileData { public Row[] souls; }
    class Entry { public Row row; public Enemy live; public bool done; }

    const float SpawnDist = 60f, ReleaseDist = 150f;
    readonly List<Entry> entries = new List<Entry>();
    readonly EnemyManager enemies;

    public NamedSoulSpawns(EnemyManager enemies)
    {
        this.enemies = enemies;
        var ta = Resources.Load<TextAsset>("Data/named_souls");
        if (ta == null) return;
        var f = JsonUtility.FromJson<FileData>(ta.text);
        if (f != null && f.souls != null) foreach (var r in f.souls) entries.Add(new Entry { row = r });
    }

    /// <summary>daylight: 하늘 밝기(0=밤). 밤에만 혼이 보인다</summary>
    public void Tick(Vector3 playerPos, float daylight)
    {
        bool night = daylight < 0.35f;
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
            float d = new Vector2(e.row.x - playerPos.x, e.row.z - playerPos.z).magnitude;
            if (d > SpawnDist) continue;
            float x = e.row.x, z = e.row.z;
            MapLayout.PushOut(ref x, ref z, Config.ENEMY_RADIUS + 1f);
            var en = enemies.SpawnCamp(new Vector3(x, 0f, z), true);
            en.MakeNamed(e.row.name, (SoulKind)Mathf.Clamp(e.row.age, 0, 2), e.row.wait);
            en.extra = false;
            e.live = en;
        }
    }
}
