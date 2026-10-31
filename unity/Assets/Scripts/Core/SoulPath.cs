// =============================================================================
// SoulPath.cs — 넋길(밤에만 쓰는 서낭당 사이 즉시 이동) 규칙 (순수 C#, 테스트 가능).
//
// 왜 밤에만? (기획 4단계) 낮엔 걸어서 풍경을 보게 하고, 밤엔 넋길을 타고 멀리 가 혼을 처결한다.
// 그러면 "멀리 갔다가 동틀녘 전에 돌아오는" 긴장이 남는다(귀환 강제는 없지만 낮엔 걸어야 하니까).
// 서낭당 곁(UseRadius 안)에서만 탈 수 있고, 누르면 목록의 다음 서낭당으로 간다(끝이면 처음으로).
// =============================================================================
using System;

namespace Chasa.Core
{
    public static class SoulPath
    {
        public const float UseRadius = 6f;          // 서낭당에서 이 거리 안이어야 탈 수 있다
        public const float NightDaylight = 0.15f;   // 하늘 밝기가 이보다 낮으면 '밤'으로 본다

        public static bool Available(float daylight) { return daylight < NightDaylight; }

        /// <summary>(x,z) 곁의 서낭당 번호. 없으면 -1</summary>
        public static int NearIndex(float x, float z, float[][] shrines)
        {
            int best = -1; float bd = UseRadius * UseRadius;
            for (int i = 0; i < shrines.Length; i++)
            {
                float dx = shrines[i][0] - x, dz = shrines[i][1] - z, d = dx * dx + dz * dz;
                if (d <= bd) { bd = d; best = i; }
            }
            return best;
        }

        /// <summary>다음 서낭당 번호 (끝이면 처음으로)</summary>
        public static int Next(int index, int count) { return count <= 0 ? -1 : (index + 1) % count; }
    }
}
