// =============================================================================
// ClockSky.cs — 세계 시계(WorldClock)에 맞춰 하늘·햇빛·안개를 바꾼다 (화면 전용).
//
// 왜 숫자 시계가 아니라 하늘색인가? (기획 3단계) 시간을 '읽게' 하지 않고 '느끼게' 하려는 것.
// 해질녘엔 해가 낮고 주황이 돌고, 밤엔 푸른 달빛, 동틀녘엔 다시 붉다 → 종소리와 함께 하루의 흐름이 몸으로 들어온다.
// 한 가지 값(Daylight 0~1)만 보간하고, 붉은 기운은 '낮도 밤도 아닌 중간'에서 가장 세게 낸다.
// =============================================================================
using UnityEngine;
using Chasa.Core;

/// <summary>아트팀 하늘 키프레임(Resources/Data/sky_clock.json): 게임 시(0~24)별 빛·그늘·안개 색. 키 사이는 smoothstep(부드러운 S자) 보간</summary>
public static class SkyKeys
{
    [System.Serializable] public class Key { public float hour, light_intensity, fog_density_mult; public string light_color, ambient_color, fog_color; }
    [System.Serializable] class Root { public Key[] keyframes; }
    static Key[] keys; static bool tried;
    public struct Sample { public Color light, ambient, fog; public float intensity, fogMult; }

    static Color Hex(string h) { Color c; return ColorUtility.TryParseHtmlString(h, out c) ? c : Color.gray; }

    /// <summary>세계 시계의 분 → 게임 시. 빛이 있는 구간(동틀녘~해질녘)을 5.5~18.5시에, 밤을 18.5~29.5시(=다음 날 5.5시)에 맞춘다</summary>
    public static float HourOf(WorldClock clock)
    {
        float m = clock.Minutes % WorldClock.DayLength;
        float light = Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + Balance.CLOCK_DUSK_MIN;
        float h = m < light ? Mathf.Lerp(5.5f, 18.5f, m / light) : Mathf.Lerp(18.5f, 29.5f, (m - light) / Mathf.Max(0.01f, WorldClock.DayLength - light));
        return h % 24f;
    }

    /// <summary>키프레임을 못 읽었으면 false(그러면 부르는 쪽이 예전 계산을 쓴다)</summary>
    public static bool TryEvaluate(float hour, out Sample o)
    {
        o = default(Sample);
        if (!tried)
        {
            tried = true;
            var ta = Resources.Load<TextAsset>("Data/sky_clock");
            if (ta != null) { try { keys = JsonUtility.FromJson<Root>(ta.text).keyframes; } catch (System.Exception) { keys = null; } }
        }
        if (keys == null || keys.Length < 2) return false;
        // hour 를 감싸고 있는 두 키 찾기(24시 → 0시로 이어진다)
        Key a = keys[keys.Length - 1], b = keys[0]; float ha = a.hour - 24f, hb = b.hour;
        for (int i = 0; i < keys.Length; i++)
        {
            if (keys[i].hour <= hour) { a = keys[i]; ha = a.hour; b = keys[(i + 1) % keys.Length]; hb = i + 1 < keys.Length ? b.hour : b.hour + 24f; }
        }
        float t = Mathf.Clamp01((hour - ha) / Mathf.Max(0.001f, hb - ha)); t = t * t * (3f - 2f * t);
        o.light = Color.Lerp(Hex(a.light_color), Hex(b.light_color), t);
        o.ambient = Color.Lerp(Hex(a.ambient_color), Hex(b.ambient_color), t);
        o.fog = Color.Lerp(Hex(a.fog_color), Hex(b.fog_color), t);
        o.intensity = Mathf.Lerp(a.light_intensity, b.light_intensity, t);
        o.fogMult = Mathf.Lerp(a.fog_density_mult, b.fog_density_mult, t);
        return true;
    }
}

public static class ClockSky
{
    static readonly Color SunNight = new Color(0.55f, 0.65f, 1f), SunDay = new Color(1f, 0.96f, 0.86f), SunRed = new Color(1f, 0.55f, 0.35f);
    static readonly Color AmbNight = new Color(0.20f, 0.23f, 0.34f), AmbDay = new Color(0.55f, 0.56f, 0.58f);
    static readonly Color FogDay = new Color(0.60f, 0.66f, 0.72f);

    public static void Apply(Light sun, Camera cam, WorldClock clock, Vector3 playerPos, float dt)
    {
        FieldZones.Tick(playerPos, dt);   // 구역별 밤 안개(색·짙기)를 서서히 갈아 끼운다
        float dl = clock.Daylight;
        SkyState.Daylight = dl;
        float red = 1f - Mathf.Abs(dl * 2f - 1f);   // 낮밤 중간에서 1, 한낮·한밤에서 0
        if (sun != null)
        {
            sun.intensity = Mathf.Lerp(0.55f, 1.15f, dl);
            var c = Color.Lerp(SunNight, SunDay, dl);
            sun.color = Color.Lerp(c, SunRed, red * 0.55f);
            // 해가 하늘을 가로지른다: 낮 동안 동→서로 그림자가 돌고, 높이는 정오에 가장 높다. 밤엔 달이 고정
            float lightSpan = Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + Balance.CLOCK_DUSK_MIN;
            if (clock.Minutes < lightSpan)
            {
                float t = Mathf.Clamp01(clock.Minutes / lightSpan);
                sun.transform.rotation = Quaternion.Euler(Mathf.Lerp(18f, 62f, Mathf.Sin(t * Mathf.PI)), Mathf.Lerp(-80f, 80f, t), 0f);
            }
            else sun.transform.rotation = Quaternion.Euler(52f, -35f, 0f);
        }
        SkyKeys.Sample ks; bool keyed = SkyKeys.TryEvaluate(SkyKeys.HourOf(clock), out ks);
        if (keyed)
        {
            // 아트 키프레임이 있으면 빛·그늘 색을 그것으로(해 방향·높이는 위 계산 그대로). 보름밤 ×1.25, 초승밤 ×0.8
            float moon = dl < 0.5f ? (clock.FullMoon ? 1.25f : clock.NewMoon ? 0.8f : 1f) : 1f;
            if (sun != null) { sun.color = ks.light; sun.intensity = ks.intensity * moon * SkyState.LightMult; }
            RenderSettings.ambientLight = ks.ambient;
        }
        else RenderSettings.ambientLight = Color.Lerp(AmbNight, AmbDay, dl);
        var fog = Color.Lerp(FieldZones.NightFog, Color.Lerp(FogDay, new Color(0.85f, 0.55f, 0.45f), red * 0.5f), dl > 0.001f ? Mathf.Clamp01(dl * 1.2f) : 0f);
        if (keyed) fog = Color.Lerp(FieldZones.NightFog, ks.fog, dl > 0.001f ? Mathf.Clamp01(dl * 1.2f) : 0f);   // 낮 안개는 아트 색, 밤엔 구역별 안개 그대로
        RenderSettings.fogColor = fog;
        RenderSettings.fogDensity = Mathf.Lerp(FieldZones.NightDensity, 0.007f, dl) * SkyState.FogMult * Balance.FOG_DENSITY_MULT;   // 낮엔 구역과 상관없이 옅게. 날씨가 안개를 더 짙게
        if (cam != null) cam.backgroundColor = fog;
    }
}
