// =============================================================================
// FieldCamps.cs — 필드 적 군집을 플레이어 가까이에서만 세우고 멀어지면 걷어낸다.
// 규칙(거리·재등장 시간)은 Core/CampRules. 자리표는 Resources/Data/field_camps.json
// (아트 구역표에서 tools/build_field_data.py 가 구운 것). 옛 '플레이어 둘레 무한 재등장'은 필드에선 쓰지 않는다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class FieldCamps
{
    [System.Serializable] class CampRow { public float x, z, r; public int n; public string zone, theme; }
    [System.Serializable] class CampFile { public CampRow[] camps; }

    class Camp
    {
        public CampRow row; public bool spawned; public float cooldown;
        public readonly List<Enemy> members = new List<Enemy>();
    }

    readonly List<Camp> camps = new List<Camp>();
    readonly EnemyManager enemies;

    public int Count => camps.Count;
    public float GhostMult = 1f;   // 흐린 밤 +15%: 군집이 설 때 혼 수에 곱한다

    // 서낭당 자리(아트 배치표의 prop_seonangdang 5곳, x·z 쌍)
    static readonly float[] Shrines = { 108f, 452f, 188f, 36f, 160f, 180f, 356f, 324f, 186f, 39f };

    public FieldCamps(EnemyManager enemies)
    {
        this.enemies = enemies;
        var ta = Resources.Load<TextAsset>("Data/field_camps");
        if (ta == null) return;
        var f = JsonUtility.FromJson<CampFile>(ta.text);
        if (f == null || f.camps == null) return;
        // 서낭당 둘레 60m 는 비우고(쉬는 자리), 보스 마당 둘레 30m 는 치우거나 절반으로 줄인다(코디 결정). 아트 구역표 자체는 건드리지 않고 여기서 보정한다
        var bosses = new List<float>();
        for (int b = 1; b <= Bosses.Count; b++) { var bd = Bosses.Get(b); bosses.Add(bd.X); bosses.Add(bd.Z); }
        foreach (var r in f.camps)
        {
            float x = r.x, z = r.z; int n = r.n;
            if (!CampRules.Adjust(ref x, ref z, r.r, ref n, Shrines, bosses.ToArray())) continue;
            r.x = x; r.z = z; r.n = n;
            camps.Add(new Camp { row = r });
        }
    }

    public void Tick(float dt, Vector3 playerPos)
    {
        foreach (var c in camps)
        {
            c.cooldown = Mathf.Max(0f, c.cooldown - dt);
            float dist = new Vector2(c.row.x - playerPos.x, c.row.z - playerPos.z).magnitude;
            if (CampRules.ShouldSpawn(c.spawned, dist, c.cooldown)) Spawn(c);
            else if (c.spawned)
            {
                c.members.RemoveAll(e => e == null || !enemies.list.Contains(e));   // 처결돼 목록에서 빠진 혼은 정리
                if (c.members.Count == 0) { c.spawned = false; c.cooldown = CampRules.RespawnDelay; }   // 다 처결 → 재등장 대기
                else if (CampRules.ShouldRelease(true, dist)) Release(c);
            }
        }
    }

    void Spawn(Camp c)
    {
        c.spawned = true;
        int count = CampRules.CountFor(c.row.n, SkyState.Daylight);   // 낮엔 적게
        if (GhostMult > 1.001f)   // 날씨로 늘어나는 몫은 확률로 올려서(기댓값이 맞게) 작은 군집도 평균 +15% 가 된다
        {
            float exact = count * GhostMult; int whole = Mathf.FloorToInt(exact);
            count = whole + (Random.value < exact - whole ? 1 : 0);
        }
        for (int i = 0; i < count; i++)
        {
            // 군집 반지름 안 무작위 자리. 집·소품 안이면 밀려난다
            float a = Random.value * Mathf.PI * 2f, rr = Mathf.Sqrt(Random.value) * c.row.r;
            float x = c.row.x + Mathf.Cos(a) * rr, z = c.row.z + Mathf.Sin(a) * rr;
            MapLayout.PushOut(ref x, ref z, Config.ENEMY_RADIUS + 1f);
            var e = enemies.SpawnCamp(new Vector3(x, 0f, z), i % 2 == 0);
            c.members.Add(e);
        }
    }

    /// <summary>멀어졌을 때: 아직 싸우는 혼은 걷어내고, 군집은 다음에 가까이 가면 새로 선다(무릎 꿇은 혼도 함께 사라짐)</summary>
    void Release(Camp c)
    {
        foreach (var e in c.members) enemies.Remove(e);
        c.members.Clear();
        c.spawned = false;
    }
}
