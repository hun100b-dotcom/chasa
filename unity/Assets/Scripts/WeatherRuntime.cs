// =============================================================================
// WeatherRuntime.cs — 날씨를 게임에 켜는 얇은 연결부 (규칙은 Core/Weather.cs·WeatherState.cs).
// 하는 일: ① 새벽·저녁 시작과 밤 중간에 날씨를 굴리고 저녁엔 예보를 알린다 ② 플레이어가 선 구역(보스 마당이면 고정 날씨)의
// 날씨 효과를 매 프레임 계산해 JudgeSystem 이 가져다 쓰게 한다 ③ 안개·빛 세기와 날씨 소리를 켠다.
// 효과(이동·피해·얼룩)는 밤에만, 낮엔 보기와 소리만 바뀐다.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class WeatherRuntime
{
    public readonly WeatherState state = new WeatherState();
    readonly System.Random rng = new System.Random();
    public Weather Current { get; private set; }
    public WeatherEffect Fx { get; private set; } = WeatherRules.Effect(Weather.Clear, true);
    bool started, midDone; ClockPhase lastPhase;
    float clearT; Vector3 clearAt; float drainAcc;     // 역병 안개가 걷힌 자리와 남은 시간
    Vector3 lastPos;

    /// <summary>저장에서 불러올 때: 날씨를 그대로 되돌리고(새로 굴리지 않는다) 지금 시계 구간에서 이어 간다</summary>
    public void Restore(int[] now, bool eased, WorldClock clock)
    {
        state.PlagueEased = eased;
        if (now != null) { var a = new Weather[now.Length]; for (int i = 0; i < a.Length; i++) a[i] = (Weather)now[i]; state.Restore(a); started = true; if (clock != null) { lastPhase = clock.Phase; midDone = clock.Phase == ClockPhase.Night && clock.Minutes >= Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + Balance.CLOCK_DUSK_MIN + Balance.CLOCK_NIGHT_MIN * 0.5f; } }
        else started = false;   // 옛 저장: 새로 굴린다
    }

    public int[] Snapshot() { var sn = state.Snapshot(); var o = new int[sn.Length]; for (int i = 0; i < o.Length; i++) o[i] = (int)sn[i]; return o; }

    /// <summary>천도가 끝난 자리: 역병 안개가 반경 4m 에서 15초 걷힌다</summary>
    public void ClearPlague(Vector3 at) { clearAt = at; clearT = Balance.WEATHER_PLAGUE_CLEAR_SEC; }

    /// <summary>플레이어가 걷힌 자리 안에 있나(역병 효과를 건너뛴다)</summary>
    public bool PlagueCleared(Vector3 p) { return clearT > 0f && new Vector2(p.x - clearAt.x, p.z - clearAt.z).magnitude <= Balance.WEATHER_PLAGUE_CLEAR_R; }

    /// <summary>매 프레임. 이동 둔화(날씨분)와 서 있을 때 줄어드는 체력(이번 프레임 정수 피해)을 돌려준다</summary>
    public void Tick(WorldClock clock, Vector3 playerPos, EnemyManager enemies, float dt, bool godMode, out float weatherSlow, out int standDamage, System.Action<string> toast)
    {
        weatherSlow = 0f; standDamage = 0;
        if (clock == null) return;
        bool night = clock.Phase == ClockPhase.Night;
        if (!started) { started = true; state.RollAll(night, rng); lastPhase = clock.Phase; }
        if (clock.Phase != lastPhase)
        {
            if (clock.Phase == ClockPhase.Dawn) { if (pending != null && pendingFor == ClockPhase.Dawn) state.Restore(pending); else state.RollAll(false, rng); pending = null; }
            else if (clock.Phase == ClockPhase.Dusk)
            {
                if (pending != null && pendingFor == ClockPhase.Dusk) state.Restore(pending); else state.RollAll(true, rng);
                pending = null; midDone = false;   // 저녁이 시작될 때 굴린 밤 날씨 = 예보(틀리지 않는다)
                if (toast != null) toast("오늘 밤 날씨 — " + Forecast());
            }
            lastPhase = clock.Phase;
        }
        float nightStart = Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + Balance.CLOCK_DUSK_MIN;
        if (night && !midDone && clock.Minutes >= nightStart + Balance.CLOCK_NIGHT_MIN * 0.5f) { midDone = true; state.MidNight(rng); }
        // 보스 마당: 보스 곁(30m)에서는 날씨가 보스 날씨로 고정
        Weather? fixedW = null;
        if (enemies != null)
            foreach (var e in enemies.list)
            {
                if (e == null || !e.soul.Boss || e.soul.BossId < 1 || e.gone) continue;
                if (new Vector2(e.Pos.x - playerPos.x, e.Pos.z - playerPos.z).magnitude < 30f) { fixedW = WeatherRules.BossFixed(e.soul.BossId); break; }
            }
        Current = fixedW ?? state.For(FieldZones.NameAt(playerPos.x, playerPos.z));
        Fx = WeatherRules.Effect(Current, night);
        clearT = Mathf.Max(0f, clearT - dt);
        bool cleared = PlagueCleared(playerPos);
        if (!cleared) weatherSlow = Fx.MoveSlow;
        // 서 있을 때만(이번 프레임 거의 안 움직임) 초당 StandDrain 만큼 체력이 준다
        bool standing = (playerPos - lastPos).magnitude < 0.002f * Mathf.Max(1f, dt * 60f); lastPos = playerPos;
        if (Fx.StandDrain > 0f && !cleared && standing && !godMode)
        {
            drainAcc += Fx.StandDrain * dt;
            if (drainAcc >= 1f) { standDamage = (int)drainAcc; drainAcc -= standDamage; }
        }
        else drainAcc = Mathf.Max(0f, drainAcc - dt);
        Apply();
    }

    Weather[] pending; ClockPhase pendingFor;   // 서낭당에서 미리 본 다음 시간대 날씨(그 시간대가 오면 그대로 쓴다 — 예보는 틀리지 않는다)

    /// <summary>서낭당 쉬기의 예보: 다음 시간대의 구역별 날씨 한 줄. 날씨는 새벽·저녁에만 새로 굴려지므로 그때가 다음이면 미리 굴려 두고, 아니면 지금 날씨가 이어진다</summary>
    public string PeekNext(WorldClock clock)
    {
        if (clock == null) return "";
        ClockPhase next = (ClockPhase)(((int)clock.Phase + 1) % 4);
        if (next == ClockPhase.Dawn || next == ClockPhase.Dusk)
        {
            if (pending == null || pendingFor != next)
            {
                var keep = state.Snapshot();
                state.RollAll(next == ClockPhase.Dusk, rng);   // 저녁에 굴리는 것은 '밤 날씨'
                pending = state.Snapshot(); pendingFor = next;
                state.Restore(keep);                           // 지금 날씨는 그대로
            }
            var keep2 = state.Snapshot(); state.Restore(pending);
            string t = Forecast(); state.Restore(keep2); return WorldClock.PhaseName(next) + " 날씨 — " + t;
        }
        return WorldClock.PhaseName(next) + " 날씨 — " + Forecast();
    }

    /// <summary>저녁 예보 한 줄: 구역별 밤 날씨(맑음은 줄인다)</summary>
    public string Forecast()
    {
        var snap = state.Snapshot(); var parts = new List<string>();
        for (int i = 0; i < snap.Length; i++) parts.Add(WeatherRules.Zones[i] + " " + WeatherState.Name(snap[i]));
        return string.Join(" · ", parts);
    }

    // 날씨 미리 정한 보기(sky_clock.json 의 weather_presets): 빛 배율, 안개 배율
    static float LightMult(Weather w) { switch (w) { case Weather.Cloudy: return 0.8f; case Weather.Rain: return 0.55f; case Weather.Fog: return 0.7f; case Weather.Plague: return 0.6f; default: return 1f; } }
    static float FogMult(Weather w) { switch (w) { case Weather.Cloudy: return 1.2f; case Weather.Rain: return 1.6f; case Weather.Fog: return 3.0f; case Weather.Plague: return 2.5f; default: return 1f; } }

    // ---- 비 줄기 화면 덮개: 멀리·가까이 두 겹을 아래로 흘린다(sky_clock.json 의 rain_layers 값)
    float rainA; Texture2D rainFar, rainNear; bool rainTried;

    /// <summary>JudgeSystem.OnGUI 가 HUD 보다 먼저 부른다. 비가 아니면 서서히 걷힌다</summary>
    public void DrawOverlay(Vector3 playerPos)
    {
        float ftarget = (Current == Weather.Fog || Current == Weather.Plague) ? 1f : 0f;
        fogA = Mathf.MoveTowards(fogA, ftarget, Time.unscaledDeltaTime * 0.5f);   // 안개 층은 더 천천히(2초)
        float target = Current == Weather.Rain ? 1f : 0f;
        rainA = Mathf.MoveTowards(rainA, target, Time.unscaledDeltaTime * 0.7f);   // 약 1.4초에 걸쳐 시작·그침
        if (Event.current.type != EventType.Repaint) return;
        DrawFog();
        if (rainA <= 0.01f) return;
        if (!rainTried)
        {
            rainTried = true;
            rainFar = SpriteLib.Texture("sky/rain_streaks_far"); rainNear = SpriteLib.Texture("sky/rain_streaks_near");
            if (rainFar != null) rainFar.wrapMode = TextureWrapMode.Repeat;
            if (rainNear != null) rainNear.wrapMode = TextureWrapMode.Repeat;
        }
        float t = Time.unscaledTime;
        DrawRainLayer(rainFar, 0.05f, -1.3f, 640f, 0.22f * rainA, t);   // 아트 검수 10-25: 비 줄기가 굵고 밝아 줄무늬였다 → 알파 절반
        DrawRainLayer(rainNear, 0.12f, -2.4f, 460f, 0.3f * rainA, t);
        DrawSplashes(playerPos, t);
    }

    // ---- 안개 층: fog_noise 두 겹을 서로 다른 방향으로 천천히 흘린다(sky_clock.json fog_layers). 역병 안개는 푸르스름한 회녹색
    float fogA; Texture2D fogTex; bool fogTried;
    void DrawFog()
    {
        if (fogA <= 0.01f) return;
        if (!fogTried) { fogTried = true; fogTex = SpriteLib.Texture("sky/fog_noise"); if (fogTex != null) fogTex.wrapMode = TextureWrapMode.Repeat; }
        if (fogTex == null) return;
        var tint = Current == Weather.Plague ? new Color(0.45f, 0.55f, 0.50f) : new Color(0.80f, 0.85f, 0.88f);
        float t = Time.unscaledTime, w = Screen.width / 900f, h = Screen.height / 900f;
        GUI.color = new Color(tint.r, tint.g, tint.b, 0.20f * fogA);
        GUI.DrawTextureWithTexCoords(new Rect(0, 0, Screen.width, Screen.height), fogTex, new Rect(t * 0.01f, t * 0.004f, w, h));
        GUI.color = new Color(tint.r, tint.g, tint.b, 0.14f * fogA);
        GUI.DrawTextureWithTexCoords(new Rect(0, 0, Screen.width, Screen.height), fogTex, new Rect(-t * 0.006f, t * 0.007f, w * 1.6f, h * 1.6f));
        GUI.color = Color.white;
    }

    // ---- 비 튀김: 플레이어 둘레 땅 위 무작위 점에서 8프레임 물방울이 초당 14프레임으로 퍼진다(rain_splash_sheet 768x96)
    struct Splash { public Vector3 at; public float t0; }
    readonly Splash[] splashes = new Splash[18]; Texture2D splashTex; bool splashTried;
    void DrawSplashes(Vector3 center, float now)
    {
        if (!splashTried) { splashTried = true; splashTex = SpriteLib.Texture("sky/rain_splash_sheet"); }
        var cam = Camera.main; if (splashTex == null || cam == null) return;
        for (int i = 0; i < splashes.Length; i++)
        {
            var sp = splashes[i]; float age = now - sp.t0;
            if (age > 8f / 14f || sp.t0 == 0f)   // 한 번 퍼지고 나면 다른 점에서 다시(시작 시각을 흩어 놓아 한꺼번에 터지지 않게)
            {
                float a = Random.value * Mathf.PI * 2f, r = Mathf.Sqrt(Random.value) * 11f;
                sp.at = new Vector3(center.x + Mathf.Cos(a) * r, 0f, center.z + Mathf.Sin(a) * r);
                sp.at.y = GroundTerrain.HeightAt(sp.at.x, sp.at.z) + 0.05f;   // 땅 높이 바로 위
                sp.t0 = now + Random.value * 0.5f; splashes[i] = sp; continue;
            }
            if (age < 0f) continue;
            int frame = Mathf.Clamp((int)(age * 14f), 0, 7);
            var sc = cam.WorldToScreenPoint(sp.at); if (sc.z <= 0f) continue;
            float size = 64f;
            GUI.color = new Color(1f, 1f, 1f, 0.85f * rainA);
            GUI.DrawTextureWithTexCoords(new Rect(sc.x - size * 0.5f, Screen.height - sc.y - size * 0.5f, size, size), splashTex, new Rect(frame / 8f, 0f, 1f / 8f, 1f));
        }
        GUI.color = Color.white;
    }

    static void DrawRainLayer(Texture2D tex, float su, float sv, float tilePx, float alpha, float t)
    {
        if (tex == null) return;
        float w = Screen.width / tilePx, h = Screen.height / tilePx;
        GUI.color = new Color(1f, 1f, 1f, alpha);
        // 텍스처 v 는 아래가 0 이라 +방향으로 흘리면 줄기가 아래로 떨어져 보인다(그림 좌표계 차이를 부호로 맞춤)
        GUI.DrawTextureWithTexCoords(new Rect(0, 0, Screen.width, Screen.height), tex, new Rect(t * su, -t * sv, w, h));
        GUI.color = Color.white;
    }

    static float CloudCover(Weather w) { switch (w) { case Weather.Cloudy: return 0.7f; case Weather.Rain: return 0.95f; case Weather.Fog: return 0.4f; case Weather.Plague: return 0.5f; default: return 0.25f; } }   // sky_clock.json cloud_cover
    float lightNow = 1f, fogNow = 1f, cloudNow = 0.25f;
    void Apply()
    {
        // 갑자기 바뀌지 않게 서서히(약 1.5초) 따라간다
        float k = 1f - Mathf.Exp(-1.5f * Time.unscaledDeltaTime * 2f);
        lightNow = Mathf.Lerp(lightNow, LightMult(Current), k); fogNow = Mathf.Lerp(fogNow, FogMult(Current), k);
        SkyState.LightMult = lightNow; SkyState.FogMult = fogNow;
        Sfx.SetWeatherAmbient(Current);
        cloudNow = Mathf.Lerp(cloudNow, CloudCover(Current), k);
        GroundTerrain.SetCloudCover(cloudNow);   // 구름 그림자(땅에 곱해 흘린다)
    }
}
