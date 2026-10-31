using UnityEngine;

/// <summary>
/// 2막 구역별 환경음(사운드팀 PR #24 규칙). 구역 직사각형(act2_map.json)에 들어가면 그 구역의 반복 소리를 켜고,
/// 구역이 바뀌면 3초 동안 서로 교차시킨다(앞 소리는 줄고 새 소리는 커짐).
/// 왜 따로 만드나: 1막의 amb.field·날씨 소리와 겹쳐도 되도록 별도 음원(AudioSource)으로 돌리기 위해서다.
/// </summary>
public class ZoneAmbient : MonoBehaviour
{
    [System.Serializable] class Zone { public string code; public float[] rect_m; }
    [System.Serializable] class MapFile { public Zone[] zones; }
    Zone[] zones = new Zone[0];
    readonly System.Collections.Generic.Dictionary<string, AudioSource> src = new System.Collections.Generic.Dictionary<string, AudioSource>();
    System.Func<Vector3> playerPos;
    const float FADE_SEC = 3f;                              // 구역 바뀔 때 교차 시간(사운드팀 요청)
    static readonly Vector3 MineMouth = new Vector3(560f, 0f, 980f);   // 갱 입구: 광부촌에서도 가까우면 갱 바람을 더한다
    const float MineWindRange = 60f;

    public static ZoneAmbient Create(System.Func<Vector3> pos)
    {
        var z = new GameObject("ZoneAmbient").AddComponent<ZoneAmbient>(); z.playerPos = pos;
        var all = new System.Collections.Generic.List<Zone>();
        foreach (var nm in new[] { "Data/act2_map", "Data/act3_map" })   // 있는 지도만 읽는다
        {
            var ta = Resources.Load<TextAsset>(nm);
            if (ta != null) { var f = JsonUtility.FromJson<MapFile>(ta.text); if (f != null && f.zones != null) all.AddRange(f.zones); }
        }
        z.zones = all.ToArray();
        return z;
    }

    /// <summary>이 자리에서 켜야 할 소리 id 들(구역 밖이면 빈 목록 → 1막 소리만)</summary>
    public string[] Wanted(Vector3 p)
    {
        foreach (var z in zones)
        {
            if (z.rect_m == null || z.rect_m.Length < 4) continue;
            if (p.x < z.rect_m[0] || p.x > z.rect_m[2] || p.z < z.rect_m[1] || p.z > z.rect_m[3]) continue;
            switch (z.code)
            {
                case "Fortress": return new[] { "amb.fortress.flag" };
                case "ArrowValley": return new[] { "amb.arrowvalley" };
                case "Camp": return new[] { "amb.camp" };
                case "MinerTown":
                    return Vector3.Distance(new Vector3(p.x, 0f, p.z), MineMouth) < MineWindRange ? new[] { "amb.mine", "amb.mine.wind" } : new[] { "amb.mine" };
                case "MainShaft": case "Collapse": return new[] { "amb.mine.shaft" };
                // 3막(사운드 PR #26): 3막 지도(act3_map.json)가 오면 구역 직사각형이 있어야 켜진다. 썰물 겹침·밀물 신호는 물때 시계가 생긴 뒤 연결
                case "Harbor": return new[] { "amb.harbor" };
                case "SaltField": return new[] { "amb.saltfield" };
                case "WreckShoal": return new[] { "amb.wreckshoal" };
                case "Market": return new[] { "amb.capital.market" };
                case "BridgeUnder": case "Shacks": return new[] { "amb.bridge.under" };
                case "CityGate": return new[] { "amb.citygate" };
            }
            return new string[0];
        }
        // 광부촌 밖이어도 갱 입구 가까이면 바람이 들린다
        if (Vector3.Distance(new Vector3(p.x, 0f, p.z), MineMouth) < MineWindRange) return new[] { "amb.mine.wind" };
        return new string[0];
    }

    void Update()
    {
        if (playerPos == null) return;
        var want = RegionSoundscape.BedActive ? new string[0] : Wanted(playerPos());   // 새 바탕 소리가 있는 구역·시각이면 옛 구역 소리는 끈다(겹침 방지)
        foreach (var id in want) if (!src.ContainsKey(id)) src[id] = Sfx.MakeLoop(id);
        var dead = new System.Collections.Generic.List<string>();
        foreach (var kv in src)
        {
            bool on = System.Array.IndexOf(want, kv.Key) >= 0 && !Sfx.Muted;
            var s = kv.Value; if (s == null) { dead.Add(kv.Key); continue; }
            float target = on ? 0.7f * SaveStore.Settings.Sfx * Sfx.Duck : 0f;   // 믹스 기준표: 구역 환경음 0.7 + 더킹
            s.volume = Mathf.MoveTowards(s.volume, target, Time.unscaledDeltaTime / FADE_SEC * Mathf.Max(0.01f, SaveStore.Settings.Sfx));
            if (!on && s.volume <= 0f) { Destroy(s); dead.Add(kv.Key); }
        }
        foreach (var d in dead) src.Remove(d);
    }
}
