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
            if (clock.Phase == ClockPhase.Dawn) state.RollAll(false, rng);
            else if (clock.Phase == ClockPhase.Dusk)
            {
                state.RollAll(true, rng); midDone = false;   // 저녁이 시작될 때 굴린 밤 날씨 = 예보(틀리지 않는다)
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

    float lightNow = 1f, fogNow = 1f;
    void Apply()
    {
        // 갑자기 바뀌지 않게 서서히(약 1.5초) 따라간다
        float k = 1f - Mathf.Exp(-1.5f * Time.unscaledDeltaTime * 2f);
        lightNow = Mathf.Lerp(lightNow, LightMult(Current), k); fogNow = Mathf.Lerp(fogNow, FogMult(Current), k);
        SkyState.LightMult = lightNow; SkyState.FogMult = fogNow;
        Sfx.SetWeatherAmbient(Current);
    }
}
