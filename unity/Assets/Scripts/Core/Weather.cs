// =============================================================================
// Weather.cs — 날씨 규칙 (순수 C#, 테스트 가능). 기획서 8절 '날씨' (모두 임시값).
//
// 한 줄 요약: 날씨는 월드 시계의 새벽·저녁에만 구역마다 따로 굴려 바뀐다(밤 중간 25% 한 번 더).
// 효과는 '밤에만' 켜지고 낮에는 보기와 소리만 바뀐다. 역병 안개는 낮에 없다.
// 보스 마당은 날씨 고정(1호 비 / 2호 안개 / 3호 역병 안개). 이야기가 정한 날씨는 무작위보다 우선.
// =============================================================================
using System;

namespace Chasa.Core
{
    public enum Weather { Clear, Cloudy, Rain, Fog, Plague }

    /// <summary>한 날씨가 규칙에 주는 값. 맑음은 전부 기본값</summary>
    public struct WeatherEffect
    {
        public float GhostMult;      // 혼 나오는 수 배율
        public float StainMult;      // 원념 얼룩 지속 배율
        public bool HideKarma;       // 업 표시를 '?'로 가림(업은 그대로 쌓이고 그치면 드러난다)
        public float VisionM;        // 보이는 거리(m)
        public float CastHit;        // 천도 중 피격 확률
        public float NamedMult;      // 이름혼 출현 배율
        public float MoveSlow;       // 이동 둔화(0~)
        public float StandDrain;     // 서 있을 때 초당 체력 감소
    }

    public static class WeatherRules
    {
        public static readonly string[] Zones = { "솔고개", "보릿들", "물막이 골", "폐당집", "검은여울" };

        /// <summary>구역별 가중치 [맑음, 흐림, 비, 안개, 역병]. isNight=false(낮)면 역병 0, 맑음 ×2. plagueEased: 3호 보스를 처결한 뒤 검은여울 역병 35 → 5</summary>
        public static float[] Weights(string zone, bool isNight, bool plagueEased = false)
        {
            float[] w;
            if (zone != null && zone.Contains("물막이")) w = new float[] { 25, 20, 40, 15, 0 };
            else if (zone != null && zone.Contains("폐당집")) w = new float[] { 25, 25, 15, 35, 0 };
            else if (zone != null && zone.Contains("검은여울")) w = new float[] { 15, 20, 15, 15, plagueEased ? 5 : 35 };
            else w = new float[] { 40, 25, 20, 15, 0 };   // 솔고개·보릿들(그 밖의 구역도 기본)
            if (!isNight) { w[4] = 0; w[0] *= 2f; }
            return w;
        }

        /// <summary>가중치 굴림. r01 은 0~1 난수(테스트에서 값을 고정하려고 밖에서 받는다)</summary>
        public static Weather Roll(string zone, bool isNight, float r01, bool plagueEased = false)
        {
            var w = Weights(zone, isNight, plagueEased);
            float sum = 0; foreach (var x in w) sum += x;
            float t = Math.Max(0f, Math.Min(0.99999f, r01)) * sum, a = 0;
            for (int i = 0; i < w.Length; i++) { a += w[i]; if (t < a) return (Weather)i; }
            return Weather.Clear;
        }

        /// <summary>컷 날씨 이름("rain" 등) → 날씨. 모르는 이름·null 이면 null(무작위 그대로)</summary>
        public static Weather? Parse(string name)
        {
            switch ((name ?? "").ToLowerInvariant())
            {
                case "clear": return Weather.Clear; case "cloudy": return Weather.Cloudy; case "rain": return Weather.Rain;
                case "fog": return Weather.Fog; case "plague": return Weather.Plague; default: return null;
            }
        }

        /// <summary>보스 마당 고정 날씨. 보스가 아니면 null</summary>
        public static Weather? BossFixed(int bossId)
        {
            switch (bossId) { case 1: return Weather.Rain; case 2: return Weather.Fog; case 3: return Weather.Plague; default: return null; }
        }

        /// <summary>날씨가 규칙에 주는 값. night=false 면 낮이라 효과 없음(보기·소리만)</summary>
        public static WeatherEffect Effect(Weather w, bool night)
        {
            var e = new WeatherEffect { GhostMult = 1f, StainMult = 1f, VisionM = Balance.WEATHER_CLEAR_VISION_M, CastHit = Balance.WEATHER_CLEAR_CAST_HIT, NamedMult = 1f };
            if (!night) return e;
            switch (w)
            {
                case Weather.Cloudy: e.GhostMult = Balance.WEATHER_CLOUDY_GHOST_MULT; break;
                case Weather.Rain: e.StainMult = Balance.WEATHER_RAIN_STAIN_MULT; e.HideKarma = true; break;
                case Weather.Fog: e.VisionM = Balance.WEATHER_FOG_VISION_M; e.CastHit = Balance.WEATHER_FOG_CAST_HIT; e.NamedMult = Balance.WEATHER_FOG_NAMED_MULT; break;
                case Weather.Plague: e.MoveSlow = Balance.WEATHER_PLAGUE_MOVE_SLOW; e.StandDrain = Balance.WEATHER_PLAGUE_STAND_DRAIN; break;
            }
            return e;
        }

        /// <summary>이동 둔화 합치기: 날씨와 얼룩이 겹쳐도 상한(WEATHER_MOVE_SLOW_MAX)을 넘지 않는다</summary>
        public static float CombineSlow(float weatherSlow, float stainSlow)
        {
            return Math.Min(Balance.WEATHER_MOVE_SLOW_MAX, Math.Max(0f, weatherSlow) + Math.Max(0f, stainSlow));
        }
    }
}
