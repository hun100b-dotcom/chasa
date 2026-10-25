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

    public FieldCamps(EnemyManager enemies)
    {
        this.enemies = enemies;
        var ta = Resources.Load<TextAsset>("Data/field_camps");
        if (ta == null) return;
        var f = JsonUtility.FromJson<CampFile>(ta.text);
        if (f == null || f.camps == null) return;
        foreach (var r in f.camps) camps.Add(new Camp { row = r });
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
        for (int i = 0; i < c.row.n; i++)
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
