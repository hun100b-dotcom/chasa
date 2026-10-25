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
    public static int EarlyMaxAlive = int.MaxValue;   // 처음 5분(시계 정지 중)엔 살아 있는 혼을 이 수까지만(시작 지점에 28마리가 줄 맞춰 서던 것 방지: 아트 검수)
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
        int alive = 0; foreach (var e0 in enemies.list) if (e0 != null && e0.alive) alive++;
        if (alive >= EarlyMaxAlive) { c.cooldown = 3f; return; }   // 지금은 더 못 세운다(조금 뒤 다시 시도)
        c.spawned = true;
        int count = CampRules.CountFor(c.row.n, SkyState.Daylight);   // 낮엔 적게
        int ring = RingOf(c.row.zone);
        float dens = Balance.CAMP_DENSITY_MULT * (ring == 1 ? Balance.CAMP_DENSITY_RING1 : ring == 2 ? Balance.CAMP_DENSITY_RING2 : Balance.CAMP_DENSITY_RING3);   // 구역 고리별 밀도(난이도 조정)
        if (dens < 0.999f) count = Mathf.Max(1, Mathf.RoundToInt(count * dens));
        if (NearNamed(c.row.x, c.row.z)) count = Mathf.Max(1, Mathf.Min(Balance.NAMED_NEAR_CAP, Mathf.RoundToInt(count * 0.5f)));   // 이름혼 자리 둘레는 한산하게(이름혼 처결 때 둘러싸이지 않게)
        if (GhostMult > 1.001f)   // 날씨로 늘어나는 몫은 확률로 올려서(기댓값이 맞게) 작은 군집도 평균 +15% 가 된다
        {
            float exact = count * GhostMult; int whole = Mathf.FloorToInt(exact);
            count = whole + (Random.value < exact - whole ? 1 : 0);
        }
        if (EarlyMaxAlive != int.MaxValue) count = Mathf.Min(count, Mathf.Max(1, EarlyMaxAlive - alive));
        for (int i = 0; i < count; i++)   // i 는 '자리 수': 잔넋 무리는 2자리를 차지한다
        {
            // 군집 반지름 안 무작위 자리. 집·소품 안이면 밀려난다
            float a = Random.value * Mathf.PI * 2f, rr = Mathf.Sqrt(Random.value) * c.row.r;
            float x = c.row.x + Mathf.Cos(a) * rr, z = c.row.z + Mathf.Sin(a) * rr;
            MapLayout.PushOut(ref x, ref z, Config.ENEMY_RADIUS + 1f);
            // 혼 3유형(구역별 비율, 임시): 넋두리는 한 구역에 동시 WAIL_MAX_ZONE 마리까지(넘으면 보통 혼), 잔넋은 3~5마리 무리로 나온다
            var type = SoulTypeRules.Pick(c.row.zone, Random.value);
            if (type == SoulType.Wail && AliveWails(c.row.zone) >= Balance.SOULTYPE_WAIL_MAX_ZONE) type = SoulType.Plain;
            if (type == SoulType.Mote)
            {
                i++;   // 잔넋 무리는 군집 2자리(기획 F-1b)
                int n = ring == 1 ? Random.Range(Balance.MOTE_GROUP_MIN_RING1, Balance.MOTE_GROUP_MAX_RING1 + 1) : Random.Range(3, 6); var grp = new List<Enemy>();
                for (int k = 0; k < n; k++)
                {
                    float ma = Random.value * Mathf.PI * 2f, mr = Random.value * 2.5f;
                    float mx = x + Mathf.Cos(ma) * mr, mz = z + Mathf.Sin(ma) * mr;
                    MapLayout.PushOut(ref mx, ref mz, Config.ENEMY_RADIUS + 0.5f);
                    var m = enemies.SpawnCamp(new Vector3(mx, 0f, mz), true, SoulType.Mote);
                    m.group = grp; m.leader = k == 0; grp.Add(m); c.members.Add(m);
                }
                continue;
            }
            var e = enemies.SpawnCamp(new Vector3(x, 0f, z), i % 2 == 0, type);
            c.members.Add(e);
        }
    }

    /// <summary>구역 이름 → 고리(1 솔고개·보릿들 / 2 물막이 골·폐당집 / 3 검은여울)</summary>
    static int RingOf(string zone)
    {
        if (zone == "검은여울") return 3;
        if (zone == "물막이 골" || zone == "폐당집") return 2;
        return 1;
    }

    // 이름혼 자리(Data/named_souls.json). 그 둘레 군집은 한산하게 한다
    [System.Serializable] class NamedRow { public float x, z; }
    [System.Serializable] class NamedFile { public NamedRow[] souls; }
    List<Vector2> namedPos;
    bool NearNamed(float x, float z)
    {
        if (namedPos == null)
        {
            namedPos = new List<Vector2>();
            var ta = Resources.Load<TextAsset>("Data/named_souls");
            var nf = ta != null ? JsonUtility.FromJson<NamedFile>(ta.text) : null;
            if (nf != null && nf.souls != null) foreach (var r in nf.souls) namedPos.Add(new Vector2(r.x, r.z));
        }
        foreach (var p in namedPos) if ((p - new Vector2(x, z)).magnitude <= Balance.NAMED_NEAR_M) return true;
        return false;
    }

    /// <summary>같은 구역에서 지금 살아 있는 넋두리 수(동시 원거리 한도 계산)</summary>
    int AliveWails(string zone)
    {
        int n = 0;
        foreach (var c in camps) if (c.row.zone == zone) foreach (var m in c.members) if (m != null && !m.gone && m.type == SoulType.Wail) n++;
        return n;
    }

    /// <summary>멀어졌을 때: 아직 싸우는 혼은 걷어내고, 군집은 다음에 가까이 가면 새로 선다(무릎 꿇은 혼도 함께 사라짐)</summary>
    void Release(Camp c)
    {
        foreach (var e in c.members) enemies.Remove(e);
        c.members.Clear();
        c.spawned = false;
    }
}
