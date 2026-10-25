// =============================================================================
// ClockSky.cs — 세계 시계(WorldClock)에 맞춰 하늘·햇빛·안개를 바꾼다 (화면 전용).
//
// 왜 숫자 시계가 아니라 하늘색인가? (기획 3단계) 시간을 '읽게' 하지 않고 '느끼게' 하려는 것.
// 해질녘엔 해가 낮고 주황이 돌고, 밤엔 푸른 달빛, 동틀녘엔 다시 붉다 → 종소리와 함께 하루의 흐름이 몸으로 들어온다.
// 한 가지 값(Daylight 0~1)만 보간하고, 붉은 기운은 '낮도 밤도 아닌 중간'에서 가장 세게 낸다.
// =============================================================================
using UnityEngine;
using Chasa.Core;

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
        RenderSettings.ambientLight = Color.Lerp(AmbNight, AmbDay, dl);
        var fog = Color.Lerp(FieldZones.NightFog, Color.Lerp(FogDay, new Color(0.85f, 0.55f, 0.45f), red * 0.5f), dl > 0.001f ? Mathf.Clamp01(dl * 1.2f) : 0f);
        RenderSettings.fogColor = fog;
        RenderSettings.fogDensity = Mathf.Lerp(FieldZones.NightDensity, 0.007f, dl);   // 낮엔 구역과 상관없이 옅게
        if (cam != null) cam.backgroundColor = fog;
    }
}
