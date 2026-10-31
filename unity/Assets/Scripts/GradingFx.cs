// =============================================================================
// GradingFx.cs — 화면 분위기 후처리(카메라에 붙는다). 아트 값표(Data/grading.json)와 LUT 22장(Resources/Grading)을 쓴다.
//   · 색보정(LUT): 시각 구간(새벽·낮·저녁놀·밤, 경계 앞뒤 0.5게임시 smoothstep 교차) × 날씨(맑음·흐림·비·안개·역병, 바뀔 때 1.5초 교차)
//   · 블룸·비네트: 같은 키의 값을 같은 비율로 섞는다. 비네트 세기는 0.45 를 못 넘긴다(가장자리 적이 안 보이면 안 됨)
//   · 천도 시야 축소: 시전 중 0.25초에 조이고 끝나면 0.15초에 푼다. 가장자리는 남청 먹 번짐 + 단청 문양, 시야 밖 적 방향은 붉은 호(2.5Hz), 성공하면 보라 테두리 0.3초(파혼 없음)
// UI 는 카메라 후처리 뒤에 그려지는 화면 위 UI(IMGUI·UI Toolkit)라 번지지 않는다.
// 끄기: 주소 뒤에 ?grade=off / 방향 점검: ?grade=neutral(색이 안 변해야 정상). 폰(낮음)은 블룸을 끈다.
// =============================================================================
using System;
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class GradingFx : MonoBehaviour
{
    public JudgeSystem judge;

    [Serializable] class Key { public string k; public float bth, bt, bs, vi, vs; public string bc, vc; }
    [Serializable] class Root { public float[] dawn, day, dusk, night; public float cross, weatherBlend, vignetteMax; public Key[] keys; }

    static readonly string[] Times = { "dawn", "day", "dusk", "night" };
    static readonly string[] Wx = { "clear", "cloudy", "rain", "fog", "plague" };   // Weather 열거 순서(맑음·흐림·비·안개·역병)와 같다
    Root data; readonly Dictionary<string, Key> keys = new Dictionary<string, Key>();
    readonly Dictionary<string, Texture2D> luts = new Dictionary<string, Texture2D>();
    Texture2D lutTendo, noise, pattern;
    Vector4 gradeCS = new Vector4(1f, 1f, 0f, 0f), gradeTint = Vector4.one;   // ?grade=b·c 후보(a 는 기본)
    Material mat; bool ok, neutral; Texture2D lutNeutral;

    Weather wxNow = Weather.Clear, wxPrev = Weather.Clear; float wxT = 99f;
    float tendoT; Vector2 center = new Vector2(0.5f, 0.5f); Vector2 gPlayer, gTarget; bool bossCast; float lastSuccessSeen = -99f;
    int bloomLevel;   // 0 끔 · 1 보통(1/4 해상도) · 2 높음(1/2 해상도 + 한 번 더 흐림)

    static Texture2D Load(string name)
    {
        var ta = Resources.Load<TextAsset>("Grading/" + name); if (ta == null) return null;
        var t = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);   // 선형(sRGB 아님): LUT 값은 그대로 읽어야 한다
        t.wrapMode = TextureWrapMode.Clamp; t.filterMode = FilterMode.Bilinear;
        return t.LoadImage(ta.bytes, false) ? t : null;
    }

    void Start()
    {
        string u = (Application.absoluteURL ?? "").ToLowerInvariant();
        if (u.Contains("grade=off")) return;
        neutral = u.Contains("grade=neutral");
        // 낮이 희뿌연 문제의 색보정 후보. b: 대비·채도를 조금 올리고 안개 낀 밝기를 눌러 줌 / c: b 보다 강하게 + 따뜻한 쪽
        if (u.Contains("grade=b")) { gradeCS = new Vector4(1.12f, 1.15f, -0.03f, 0f); }
        else if (u.Contains("grade=c")) { gradeCS = new Vector4(1.22f, 1.28f, -0.05f, 0f); gradeTint = new Vector4(1.04f, 1.0f, 0.95f, 1f); }
        var sh = Resources.Load<Shader>("Shaders/ChasaGrade");
        var ta = Resources.Load<TextAsset>("Data/grading");
        if (sh == null || !sh.isSupported || ta == null) return;
        try { data = JsonUtility.FromJson<Root>(ta.text); } catch { return; }
        if (data == null || data.keys == null) return;
        foreach (var k in data.keys) keys[k.k] = k;
        foreach (var t in Times) foreach (var w in Wx) { var tx = Load("lut_" + t + "_" + w); if (tx != null) luts[t + "_" + w] = tx; }
        lutTendo = Load("lut_tendo"); noise = Load("vision_noise"); pattern = Load("vision_pattern"); lutNeutral = Load("lut_neutral");
        if (noise != null) noise.wrapMode = TextureWrapMode.Repeat;
        if (pattern != null) pattern.wrapMode = TextureWrapMode.Repeat;
        if (luts.Count < 20 || lutTendo == null || noise == null || pattern == null) return;
        mat = new Material(sh) { hideFlags = HideFlags.HideAndDontSave };
        bloomLevel = QualityTier.Current == QualityTier.Level.Low ? 0 : QualityTier.Current == QualityTier.Level.Mid ? 1 : 2;
        ok = true;
    }

    static float Smooth(float t) { t = Mathf.Clamp01(t); return t * t * (3f - 2f * t); }
    static float EaseOutCubic(float t) { t = 1f - Mathf.Clamp01(t); return 1f - t * t * t; }
    static Color Hex(string h) { Color c; return ColorUtility.TryParseHtmlString(h, out c) ? c : Color.white; }

    /// <summary>게임 시 → 시간대 가중치 4개(dawn·day·dusk·night). 구간 경계 앞뒤 cross/2 시간은 smoothstep 으로 두 구간을 섞는다</summary>
    void TimeWeights(float h, float[] w)
    {
        if (h < data.dawn[0]) h += 24f;   // 밤은 19.5~28.5(=다음 날 4.5시) → h 는 [4.5, 28.5)
        float[] starts = { data.dawn[0], data.day[0], data.dusk[0], data.night[0] };
        Array.Clear(w, 0, 4);
        int cur = 0; for (int i = 0; i < 4; i++) if (h >= starts[i]) cur = i;
        w[cur] = 1f;
        float half = data.cross * 0.5f;
        // 경계 4곳(새벽→낮, 낮→저녁놀, 저녁놀→밤, 밤→새벽[=4.5+24]): 앞뒤 half 시간 안이면 두 구간을 섞는다
        float[] bounds = { starts[1], starts[2], starts[3], starts[0] + 24f };
        int[] before = { 0, 1, 2, 3 }, after = { 1, 2, 3, 0 };
        for (int k = 0; k < 4; k++)
            foreach (float hh in new[] { h, h + 24f })
                if (Mathf.Abs(hh - bounds[k]) < half)
                {
                    float t = Smooth((hh - (bounds[k] - half)) / data.cross);
                    Array.Clear(w, 0, 4); w[before[k]] = 1f - t; w[after[k]] = t; return;
                }
    }

    // 이번 프레임 값(OnRenderImage 에서 쓴다)
    readonly Texture2D[] useLut = new Texture2D[4]; Vector4 W; float bThr, bInt, bScat, vInt, vSm; Color bTint, vCol;
    float tendoK, radius, patA, successA; Vector4 g0, g1, d0, d1, d2, d3; Vector2 noiseScroll;
    readonly float[] tw = new float[4];

    void Update()
    {
        if (!ok || judge == null) return;
        float dt = Time.unscaledDeltaTime;
        float hour = judge.clock != null ? SkyKeys.HourOf(judge.clock) : 12f;
        TimeWeights(hour, tw);
        // 날씨: 바뀌면 1.5초 교차
        var wNow = judge.weather != null ? judge.weather.Current : Weather.Clear;
        if (wNow != wxNow) { wxPrev = wxNow; wxNow = wNow; wxT = 0f; }
        wxT += dt; float wf = Smooth(wxT / Mathf.Max(0.01f, data.weatherBlend));
        // LUT·값 섞기: (시간대 ≤2) × (날씨 ≤2) = 최대 4개
        int n = 0; W = Vector4.zero; bThr = bInt = bScat = vInt = vSm = 0f; bTint = Color.black; vCol = Color.black;
        for (int ti = 0; ti < 4; ti++)
        {
            if (tw[ti] <= 0.001f) continue;
            for (int wi = 0; wi < 2; wi++)
            {
                var wx = wi == 0 ? wxPrev : wxNow; float wwt = wi == 0 ? 1f - wf : wf; if (wxPrev == wxNow && wi == 0) continue; if (wxPrev == wxNow) wwt = 1f;
                float wt = tw[ti] * wwt; if (wt <= 0.001f || n >= 4) continue;
                string kk = Times[ti] + "_" + Wx[(int)wx];
                Key kd; Texture2D lt; if (!keys.TryGetValue(kk, out kd) || !luts.TryGetValue(kk, out lt)) continue;
                useLut[n] = lt; W[n] = wt; n++;
                bThr += kd.bth * wt; bInt += kd.bt * wt; bScat += kd.bs * wt; vInt += kd.vi * wt; vSm += kd.vs * wt;
                bTint += Hex(kd.bc) * wt; vCol += Hex(kd.vc) * wt;
            }
        }
        float sum = W.x + W.y + W.z + W.w;
        if (sum > 0.001f) { W /= sum; bThr /= sum; bInt /= sum; bScat /= sum; vInt /= sum; vSm /= sum; bTint /= sum; vCol /= sum; }
        for (int i = n; i < 4; i++) useLut[i] = useLut[0] != null ? useLut[0] : lutNeutral;
        vInt = Mathf.Min(vInt, data.vignetteMax);   // 비네트 0.45 초과 금지
        // 천도 시야 축소: 조임 0.25s(easeOutCubic) / 풀림 0.15s(easeInQuad)
        bool casting = judge.Casting && !judge.cuts.Active;
        tendoT = Mathf.Clamp01(tendoT + (casting ? dt / 0.25f : -dt / 0.15f));
        tendoK = casting ? EaseOutCubic(tendoT) : tendoT * tendoT;
        var cm = cam();
        if (casting && cm != null && judge.CastTarget != null)
        {
            var pv = cm.WorldToViewportPoint(judge.player.Pos); var tv = cm.WorldToViewportPoint(judge.CastTarget.Pos);
            gPlayer = new Vector2(pv.x, pv.y); gTarget = new Vector2(tv.x, tv.y);
            center = Vector2.Lerp(center, Vector2.Lerp(gPlayer, gTarget, 0.5f), 0.6f);
            bossCast = judge.CastTarget.soul.Boss;
        }
        float minR = Mathf.Min(Screen.width, Screen.height) < 600 ? 0.55f : 0.6f;
        radius = Mathf.Lerp(2.2f, minR, tendoK);
        patA = bossCast ? 0.24f : 0.14f;
        vInt *= 1f - tendoK;                                    // 천도 중엔 기본 비네트를 끈다(겹치면 가장자리가 죽는다)
        bInt *= 1f + 0.25f * tendoK; bTint = Color.Lerp(bTint, Hex("#5FE3C0"), 0.5f * tendoK);
        noiseScroll = new Vector2(0.012f, -0.008f) * Time.unscaledTime;
        // 글로우·위험 호
        g0 = g1 = d0 = d1 = d2 = d3 = Vector4.zero;
        if (tendoK > 0.01f && cm != null)
        {
            float asp = (float)Screen.width / Mathf.Max(1, Screen.height);
            g0 = new Vector4(gPlayer.x, gPlayer.y, GlowR(cm, judge.player.Pos, 2.4f, asp), 0.55f);
            if (judge.CastTarget != null) g1 = new Vector4(gTarget.x, gTarget.y, GlowR(cm, judge.CastTarget.Pos, 1.6f, asp), 0.55f);
            float rd = 0.5f * Mathf.Sqrt(asp * asp + 1f), limit = rd * radius;
            float pulse = Mathf.Lerp(0.15f, 0.55f, 0.5f + 0.5f * Mathf.Sin(Time.unscaledTime * 2.5f * 2f * Mathf.PI));   // 2.5Hz
            var arcs = new Vector4[4]; int na = 0;
            foreach (var e in judge.enemies.list)
            {
                if (na >= 4) break;
                if (e == null || !e.alive || e == judge.CastTarget || !e.Targetable) continue;
                if (Vector3.Distance(e.Pos, judge.player.Pos) > 14f) continue;
                var v = cm.WorldToViewportPoint(e.Pos); if (v.z < 0f) continue;
                var p = new Vector2((v.x - center.x) * asp, v.y - center.y);
                if (p.magnitude <= limit) continue;   // 시야 안이면 보이니까 호가 필요 없다
                arcs[na++] = new Vector4(Mathf.Atan2(p.y, p.x), pulse * tendoK, 28f * Mathf.Deg2Rad * 0.5f, 0f);
            }
            d0 = arcs[0]; d1 = arcs[1]; d2 = arcs[2]; d3 = arcs[3];
        }
        // 성공 테두리: 천도 성공 0.3초(파혼은 TendoSuccessAt 를 안 찍는다)
        successA = Mathf.Clamp01(1f - (Time.time - judge.TendoSuccessAt) / 0.3f);
    }

    static float GlowR(Camera cm, Vector3 p, float meters, float asp)
    {
        var a = cm.WorldToViewportPoint(p); var b = cm.WorldToViewportPoint(p + cm.transform.right * meters);
        return new Vector2((b.x - a.x) * asp, b.y - a.y).magnitude;
    }
    Camera camCache; Camera cam() { if (camCache == null) camCache = GetComponent<Camera>(); return camCache; }

    void OnRenderImage(RenderTexture src, RenderTexture dst)
    {
        if (!ok || judge == null) { Graphics.Blit(src, dst); return; }
        int w = src.width, h = src.height;
        // 블룸(보통·높음만): 밝은 곳만 뽑아 작게 → 가로·세로로 흐려 최종 합성에서 더한다
        RenderTexture b1 = null, b2 = null;
        bool bloom = bloomLevel > 0 && bInt > 0.001f;
        if (bloom)
        {
            int div = bloomLevel == 2 ? 2 : 4;
            b1 = RenderTexture.GetTemporary(Mathf.Max(8, w / div), Mathf.Max(8, h / div), 0, src.format);
            b2 = RenderTexture.GetTemporary(b1.width, b1.height, 0, src.format);
            mat.SetFloat("_BloomThr", bThr * 0.75f);   // 아트 문턱은 HDR 기준 값 → 일반(LDR) 화면에서는 낮춰 읽는다(유니티에서 튜닝)
            mat.SetColor("_BloomTint", bTint); mat.SetFloat("_BloomScatter", bScat);
            Graphics.Blit(src, b1, mat, 0);
            Graphics.Blit(b1, b2, mat, 1); Graphics.Blit(b2, b1, mat, 2);
            if (bloomLevel == 2) { Graphics.Blit(b1, b2, mat, 1); Graphics.Blit(b2, b1, mat, 2); }
            mat.SetTexture("_Bloom", b1);
        }
        else mat.SetTexture("_Bloom", Texture2D.blackTexture);
        mat.SetFloat("_BloomInt", bloom ? bInt : 0f);
        if (neutral && lutNeutral != null) { for (int i = 0; i < 4; i++) useLut[i] = lutNeutral; mat.SetVector("_W", new Vector4(1, 0, 0, 0)); }
        else mat.SetVector("_W", W);
        mat.SetTexture("_L0", useLut[0]); mat.SetTexture("_L1", useLut[1]); mat.SetTexture("_L2", useLut[2]); mat.SetTexture("_L3", useLut[3]);
        mat.SetTexture("_LT", lutTendo); mat.SetTexture("_Noise", noise); mat.SetTexture("_Pattern", pattern);
        mat.SetVector("_GradeCS", gradeCS); mat.SetVector("_GradeTint", gradeTint);
        mat.SetColor("_VigColor", vCol); mat.SetFloat("_VigInt", vInt); mat.SetFloat("_VigSmooth", vSm);
        mat.SetFloat("_TendoLut", 0.6f * tendoK);
        mat.SetFloat("_TendoK", tendoK); mat.SetFloat("_Radius", radius); mat.SetFloat("_Aspect", (float)w / Mathf.Max(1, h)); mat.SetFloat("_PatA", patA);
        mat.SetFloat("_SuccessA", successA); mat.SetVector("_Center", new Vector4(center.x, center.y, 0, 0));
        mat.SetVector("_G0", g0); mat.SetVector("_G1", g1); mat.SetVector("_D0", d0); mat.SetVector("_D1", d1); mat.SetVector("_D2", d2); mat.SetVector("_D3", d3);
        mat.SetVector("_NoiseScroll", noiseScroll); mat.SetVector("_ScreenPx", new Vector4(w, h, 0, 0));
        Graphics.Blit(src, dst, mat, 3);
        if (b1 != null) RenderTexture.ReleaseTemporary(b1);
        if (b2 != null) RenderTexture.ReleaseTemporary(b2);
    }
}
