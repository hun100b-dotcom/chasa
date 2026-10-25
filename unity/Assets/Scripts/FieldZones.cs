// =============================================================================
// FieldZones.cs — 구역별 안개(분위기). 아트 구역표(field_camps.json 의 zones)에서 색·짙기를 읽고,
// 플레이어가 구역을 넘나들 때 급히 바뀌지 않게 부드럽게 섞는다 (검은여울 독안개 → 마을 푸른 안개 …).
// ClockSky 가 이 값을 '밤의 안개'로 쓰고 낮에는 하늘 밝기에 따라 걷어낸다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public static class FieldZones
{
    [System.Serializable] class ZoneRow { public string name, fog; public float x0, z0, x1, z1, density; }
    [System.Serializable] class FileData { public ZoneRow[] zones; }

    static ZoneRect[] rects = new ZoneRect[0];
    static Color[] colors = new Color[0];
    static float[] densities = new float[0];
    static bool loaded;
    public static string CurrentName = "";                              // 지금 구역 이름(알림·시각 고리 자막용)
    public static Color NightFog = new Color(0.20f, 0.24f, 0.37f);      // 부드럽게 섞인 지금 안개 색 (기본 #33405F)
    public static float NightDensity = 0.006f;

    static void Load()
    {
        loaded = true;
        var ta = Resources.Load<TextAsset>("Data/field_camps");
        if (ta == null) return;
        var f = JsonUtility.FromJson<FileData>(ta.text);
        if (f == null || f.zones == null) return;
        var rs = new List<ZoneRect>(); var cs = new List<Color>(); var ds = new List<float>();
        foreach (var z in f.zones)
        {
            Color c; if (!ColorUtility.TryParseHtmlString(z.fog, out c)) c = NightFog;
            rs.Add(new ZoneRect { X0 = z.x0, Z0 = z.z0, X1 = z.x1, Z1 = z.z1 }); cs.Add(c); ds.Add(z.density);
        }
        rects = rs.ToArray(); colors = cs.ToArray(); densities = ds.ToArray();
        names = f.zones;
    }
    static ZoneRow[] names;

    /// <summary>플레이어 자리에 맞춰 안개 값을 한 걸음 섞는다 (구역을 넘어도 약 1.5초에 걸쳐 서서히 바뀐다)</summary>
    public static void Tick(Vector3 playerPos, float dt)
    {
        if (!loaded) Load();
        int i = ZoneRules.Find(rects, playerPos.x, playerPos.z);
        Color tc = new Color(0.20f, 0.24f, 0.37f); float td = 0.006f;   // 어느 구역도 아니면 기본(#33405F, 0.006)
        CurrentName = "";
        if (i >= 0) { tc = colors[i]; td = densities[i]; CurrentName = names[i].name; }
        float k = 1f - Mathf.Exp(-2f * dt);
        NightFog = Color.Lerp(NightFog, tc, k);
        NightDensity = Mathf.Lerp(NightDensity, td, k);
    }
}
