// =============================================================================
// NightLights.cs — 새 화면(?v=3d)의 '진짜 조명'. 달빛(약한 푸른 햇빛) + 어둠 속 등불 웅덩이 + 안개.
//
// 옛 화면은 그림이 빛을 안 받아서 화면 위에 어둠 막을 덮었지만(Atmosphere), 3D 물체는 유니티 조명을 그대로 받는다.
// 그래서 여기서는 진짜 Light 를 놓는다:
//   · 달빛: 방향 광원 하나(캐릭터 그림자를 만든다. 약하고 푸르게)
//   · 플레이어 등불: 따뜻한 점 광원이 따라다닌다. 천도 캐스팅 중엔 보랏빛으로 좁아진다
//   · 마을 등불: 초가·기와집·장승·서낭나무 자리의 점 광원(불꽃처럼 깜빡임)
//   · 혼불: 무릎 꿇은 혼 · 보스 · 사나운 적 몸에서 푸른/붉은 빛
//   · 안개: 먼 곳을 같은 남색으로 가려 땅 끝의 '빈 띠'가 안 보이게
// 점 광원은 그림자를 만들지 않는다(웹에서 점 광원 그림자는 비싸다). 그림자는 달빛 하나만.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class NightLights : MonoBehaviour
{
    public Player player;
    public JudgeSystem judge;
    public EnemyManager enemies;

    Light lantern;                                   // 플레이어 등불
    readonly List<Light> lamps = new List<Light>();  // 마을 등불
    readonly List<float> lampBase = new List<float>(), lampSeed = new List<float>();
    readonly Dictionary<Enemy, Light> glow = new Dictionary<Enemy, Light>();   // 적마다 하나(필요할 때만 켬)
    float t;

    static readonly Color Warm = new Color(1f, 0.72f, 0.42f);
    static readonly Color Violet = new Color(0.62f, 0.45f, 1f);
    static readonly Color Soul = new Color(0.45f, 0.7f, 1f);

    /// <summary>무대 전체 분위기(달빛·환경광·안개). GameMain 이 BuildStage 에서 부른다</summary>
    public static void SetupAtmosphere(Light sun)
    {
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.20f, 0.23f, 0.34f);   // 완전한 어둠이 아니라 푸른 기운이 남게
        sun.color = new Color(0.55f, 0.65f, 1f);
        sun.intensity = 0.55f;
        sun.shadows = LightShadows.Soft;
        sun.shadowStrength = 0.85f;
        sun.transform.rotation = Quaternion.Euler(52f, -35f, 0f);   // 달이 위쪽 뒤에서 비춘다
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.ExponentialSquared;
        RenderSettings.fogColor = View3D.FogColor;
        RenderSettings.fogDensity = 0.016f;
        QualitySettings.shadowDistance = 40f;
        QualitySettings.pixelLightCount = 8;   // 한 물체에 닿는 점 광원 최대 수(기본 4는 등불이 많으면 부족)
        QualityTier.Apply(sun);   // 폰·태블릿이면 그림자·광원·프레임을 낮춘다
    }

    void Start()
    {
        var go = new GameObject("PlayerLantern");
        go.transform.SetParent(transform, false);
        lantern = go.AddComponent<Light>();
        lantern.type = LightType.Point; lantern.color = Warm; lantern.range = 12f; lantern.intensity = 2.0f;
        lantern.shadows = LightShadows.None;
        // 마을 소품에서 등불 자리를 뽑는다 (Atmosphere 와 같은 규칙: 집은 창가, 장승은 약하게, 서낭나무는 크게)
        foreach (var p in FieldRules.On ? new PropDef[0] : MapData.Props)   // 필드 모드는 불빛을 FieldManager 가 따로 켠다
        {
            var pos = new Vector3(MapLayout.WorldX(p.Ay), 2.0f, MapLayout.WorldZ(p.Ax));
            if (p.Sprite.EndsWith("seonang_tree")) { pos = new Vector3(-2.2f, 2.6f, -1.0f); AddLamp(pos, 14f, 2.2f); }
            else if (p.Sprite.EndsWith("choga") || p.Sprite.EndsWith("giwa")) AddLamp(pos + Vector3.up * -0.3f, 9f, 1.8f);
            else if (p.Sprite.EndsWith("jangseung")) AddLamp(pos + Vector3.up * 0.8f, 6f, 1.2f);
            else if (p.Sprite.EndsWith("well") || p.Sprite.EndsWith("sotdae")) AddLamp(pos + Vector3.up * -0.6f, 5f, 0.9f);
        }
    }

    void AddLamp(Vector3 pos, float range, float intensity)
    {
        var go = new GameObject("Lamp");
        go.transform.SetParent(transform, false);
        go.transform.position = pos;
        var l = go.AddComponent<Light>();
        l.type = LightType.Point; l.color = Warm; l.range = range; l.intensity = intensity; l.shadows = LightShadows.None;
        lamps.Add(l); lampBase.Add(intensity); lampSeed.Add(Random.value * 10f);
    }

    void Update()
    {
        t += Time.unscaledDeltaTime;
        if (player != null && lantern != null)
        {
            // 천도 캐스팅 중(0→1): 등불이 보랏빛으로 변하고 좁아진다 = 시야가 줄어드는 느낌과 짝
            float cast = judge != null ? judge.CastZoom : 0f;
            lantern.transform.position = player.Pos + Vector3.up * 2.6f;
            lantern.color = Color.Lerp(Warm, Violet, cast);
            lantern.range = Mathf.Lerp(12f, 7f, cast);
            lantern.intensity = Mathf.Lerp(2.0f, 1.4f, cast) * (1f - 0.8f * Chasa.Core.SkyState.Daylight);
        }
        // 불꽃 깜빡임: 느린 숨결 + 빠른 떨림을 섞는다
        for (int i = 0; i < lamps.Count; i++)
            lamps[i].intensity = lampBase[i] * (1f - 0.9f * Chasa.Core.SkyState.Daylight) * (1f + 0.10f * Mathf.Sin(t * 4.1f + lampSeed[i]) + 0.06f * Mathf.Sin(t * 11.7f + lampSeed[i] * 2f));
        // 혼불
        if (enemies != null)
            foreach (var e in enemies.list)
            {
                if (e == null) continue;
                Light l;
                bool want = e.soul.Boss || e.soul.Fierce || e.kneeling || e.sending;
                if (!glow.TryGetValue(e, out l))
                {
                    if (!want) continue;
                    var go = new GameObject("SoulGlow"); go.transform.SetParent(e.transform, false); go.transform.localPosition = Vector3.up * 1.0f;
                    l = go.AddComponent<Light>(); l.type = LightType.Point; l.shadows = LightShadows.None;
                    glow[e] = l;
                }
                l.enabled = want && !e.gone;
                if (!l.enabled) continue;
                l.color = e.soul.Fierce ? new Color(1f, 0.3f, 0.25f) : e.soul.Boss ? Violet : Soul;
                l.range = e.soul.Boss ? 8f : 5f;
                l.intensity = (e.soul.Boss ? 1.6f : 1.1f) * (0.9f + 0.1f * Mathf.Sin(t * 6f + e.GetInstanceID()));
            }
    }
}
