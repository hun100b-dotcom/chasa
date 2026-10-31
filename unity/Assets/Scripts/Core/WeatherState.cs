// =============================================================================
// WeatherState.cs — 구역별 지금 날씨 + 굴리는 때 (순수 C#). 규칙표는 Weather.cs.
// 새벽 시작·저녁 시작에 네 구역(+기본)을 따로 굴리고, 밤 중간 지점을 지날 때 구역마다 25% 한 번 더 굴린다.
// 저녁이 시작될 때 굴린 밤 날씨는 곧 '예보'다(예보는 틀리지 않으니 밤 중간 재굴림은 예보를 바꾸지 못하게 하려면 호출 쪽에서 막는다 — 기획: 밤 중간 변경은 예보에 없는 변수).
// 서사가 정한 장면 날씨(Override)는 무작위보다 우선한다.
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public class WeatherState
    {
        readonly Dictionary<string, Weather> now = new Dictionary<string, Weather>();
        public Weather? Override;                 // 서사가 정한 장면 날씨(null 이면 무작위)
        public bool PlagueEased;                  // 3호 보스를 처결해 검은여울 역병 가중치가 35→5
        bool midDone;

        public Weather For(string zone)
        {
            if (Override.HasValue) return Override.Value;
            Weather w; return now.TryGetValue(Key(zone), out w) ? w : Weather.Clear;
        }

        static string Key(string zone)
        {
            foreach (var z in WeatherRules.Zones) if (zone != null && zone.Contains(z)) return z;
            return "솔고개";
        }

        /// <summary>새벽·저녁이 시작될 때 모든 구역을 굴린다. isNight: 저녁 시작이면 true(곧 밤)</summary>
        public void RollAll(bool isNight, Random rng)
        {
            foreach (var z in WeatherRules.Zones) now[z] = WeatherRules.Roll(z, isNight, (float)rng.NextDouble(), PlagueEased);
            midDone = false;
        }

        /// <summary>밤이 반쯤 지났을 때 한 번 호출. 구역마다 WEATHER_NIGHT_MID_REROLL 확률로 다시 굴린다. 바뀐 구역 수를 돌려준다</summary>
        public int MidNight(Random rng)
        {
            if (midDone) return 0; midDone = true; int n = 0;
            foreach (var z in WeatherRules.Zones)
                if (rng.NextDouble() < Balance.WEATHER_NIGHT_MID_REROLL)
                {
                    var w = WeatherRules.Roll(z, true, (float)rng.NextDouble(), PlagueEased);
                    if (w != now[z]) n++;
                    now[z] = w;
                }
            return n;
        }

        /// <summary>저장·예보용: 구역 이름 순서대로 날씨</summary>
        public Weather[] Snapshot() { var o = new Weather[WeatherRules.Zones.Length]; for (int i = 0; i < o.Length; i++) { Weather w; o[i] = now.TryGetValue(WeatherRules.Zones[i], out w) ? w : Weather.Clear; } return o; }
        public void Restore(Weather[] a) { for (int i = 0; i < a.Length && i < WeatherRules.Zones.Length; i++) now[WeatherRules.Zones[i]] = a[i]; }

        public static string Name(Weather w)
        {
            switch (w) { case Weather.Cloudy: return "흐림"; case Weather.Rain: return "비"; case Weather.Fog: return "안개"; case Weather.Plague: return "역병 안개"; default: return "맑음"; }
        }
    }
}
