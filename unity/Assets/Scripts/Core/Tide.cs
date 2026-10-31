// =============================================================================
// Tide.cs — 3막 ⑤ 갯마을 썰물·밀물 (순수 C#, 테스트 가능). 기획 act3_map.json 의 tide.
//
// 주기 50분 = 썰물 25분 + 밀물 25분. 월드 시계 0분(1일차 새벽 시작)에 썰물이 시작된다.
// 하루가 40분이라 주기와 어긋나서, 5일마다 같은 무늬로 돈다(5밤 중 3밤이 '썰물 밤').
//   왜 코사인? 물이 갑자기 빠지고 차면 어색해서, 높을 때·낮을 때는 천천히 머물고 가운데에서 빠르게 움직이게 한다.
// =============================================================================
using System;

namespace Chasa.Core
{
    public static class Tide
    {
        public const float CycleMin = 50f, EbbMin = 25f;

        /// <summary>시작부터 흐른 전체 분(하루 수 × 하루 길이 + 하루 안의 분)</summary>
        public static float TotalMinutes(int day, float minutes) { return day * WorldClock.DayLength + minutes; }

        static float InCycle(float totalMin) { float m = totalMin % CycleMin; return m < 0f ? m + CycleMin : m; }

        /// <summary>물 높이 0(가장 낮은 썰물)~1(가장 높은 밀물). 0분=만조에서 시작해 25분에 간조</summary>
        public static float Level(float totalMin) { return 0.5f + 0.5f * (float)Math.Cos(2.0 * Math.PI * InCycle(totalMin) / CycleMin); }

        /// <summary>썰물이 끝나기까지 남은 분(밀물이면 0). 필드 군집이 '밀물 30초 전부터 새로 맺히지 않기'에 쓴다</summary>
        public static float EbbRemainMin(float totalMin) { float m = InCycle(totalMin); return m < EbbMin ? EbbMin - m : 0f; }

        /// <summary>지금 썰물 구간인가(주기의 앞 25분)</summary>
        public static bool IsEbb(float totalMin) { return InCycle(totalMin) < EbbMin; }

        /// <summary>그날 밤(시작 분~끝 분) 중 썰물인 분 수. 8분 이상이면 '썰물 밤'(B-10 싸움이 열린다)</summary>
        public static float EbbMinutesInNight(int day)
        {
            float nightStart = WorldClock.DayLength - Balance.CLOCK_NIGHT_MIN, nightEnd = WorldClock.DayLength;
            float a = TotalMinutes(day, nightStart), b = TotalMinutes(day, nightEnd), sum = 0f;
            for (float t = a; t < b; t += 0.25f) if (IsEbb(t)) sum += 0.25f;
            return sum;
        }
        public static bool IsEbbNight(int day) { return EbbMinutesInNight(day) >= 8f; }

        /// <summary>장례 연기가 흐르는 방향(x, z): ⑤ 갯마을(region 5)은 바다 쪽인 동쪽(+x), 그 밖은 방향 없음(0,0)</summary>
        public static void SmokeDir(int region, out float dx, out float dz) { dx = region == 5 ? 1f : 0f; dz = 0f; }
    }
}
