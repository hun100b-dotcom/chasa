// =============================================================================
// CampRules.cs — 필드 적 군집(야영지)이 언제 나타나고 사라지는지의 규칙 (순수 C#, 테스트 가능).
//
// 왜 필요한가? 필드는 640m 한 변. 적 수십~백 마리를 처음부터 다 세우면 화면 부품(오브젝트)이 너무 많아 느려진다.
// 그래서 플레이어가 가까워지면(ActivateDist) 그 군집만 세우고, 멀어지면(ReleaseDist) 걷어낸다.
// 군집을 모두 처결한 뒤엔 RespawnDelay 가 지나야 다시 나타난다(같은 자리를 계속 쓸어 담는 것 방지).
// 켜는 거리보다 끄는 거리를 더 크게 둔 건, 경계에서 왔다 갔다 할 때 깜박깜박 생겼다 사라지지 않게 하려는 '여유 구간'.
// =============================================================================
namespace Chasa.Core
{
    public static class CampRules
    {
        public const float ActivateDist = 85f;    // 이 거리 안으로 들어오면 군집이 나타난다
        public const float ReleaseDist = 150f;    // 이 거리 밖으로 나가면 남은 적을 걷어낸다
        public const float RespawnDelay = 120f;   // 다 처결한 뒤 다시 나타나기까지(초)
        public const float ShrineSafeM = 60f;     // 서낭당(쉬는 자리) 둘레엔 군집이 서지 않는다(코디 결정 10-25)
        public const float BossYardM = 30f;       // 보스 마당 둘레: 안쪽은 군집 제거, 바깥 띠는 절반(보스전 주인공은 보스)
        public const float BossYardCoreM = 18f;

        /// <summary>군집 자리를 보정한다. 서낭당 60m 안이면 바깥으로 밀어내고, 보스 마당에선 가운데면 없애고(false) 가장자리면 수를 절반으로.
        /// shrines/bosses 는 {x,z} 쌍의 평평한 배열. 군집 중심이 서낭당 둘레 60m 밖이 될 때까지 최대 4번 민다</summary>
        public static bool Adjust(ref float x, ref float z, float r, ref int n, float[] shrines, float[] bosses)
        {
            for (int pass = 0; pass < 4; pass++)
            {
                bool moved = false;
                for (int i = 0; i + 1 < shrines.Length; i += 2)
                {
                    float dx = x - shrines[i], dz = z - shrines[i + 1], d = (float)System.Math.Sqrt(dx * dx + dz * dz);
                    if (d >= ShrineSafeM) continue;
                    if (d < 0.01f) { dx = 1f; dz = 0f; d = 1f; }
                    x = shrines[i] + dx / d * (ShrineSafeM + 2f); z = shrines[i + 1] + dz / d * (ShrineSafeM + 2f); moved = true;
                }
                if (!moved) break;
            }
            for (int i = 0; i + 1 < bosses.Length; i += 2)
            {
                float dx = x - bosses[i], dz = z - bosses[i + 1], d = (float)System.Math.Sqrt(dx * dx + dz * dz);
                if (d <= BossYardCoreM) return false;
                if (d - r < BossYardM) n = System.Math.Max(2, n / 2);
            }
            return true;
        }

        /// <summary>지금 군집을 세워야 하나?</summary>
        public static bool ShouldSpawn(bool spawned, float dist, float cooldownLeft)
        {
            return !spawned && dist <= ActivateDist && cooldownLeft <= 0f;
        }

        /// <summary>낮이 밝을수록 군집 인원이 줄어든다 (밤 1.0 → 한낮 DAY_CAMP_MIN_FRAC). 최소 1명</summary>
        public static int CountFor(int baseCount, float daylight)
        {
            float f = 1f - (1f - Balance.DAY_CAMP_MIN_FRAC) * System.Math.Max(0f, System.Math.Min(1f, daylight));
            return System.Math.Max(1, (int)System.Math.Round(baseCount * f));
        }

        /// <summary>지금 군집을 걷어내야 하나?</summary>
        public static bool ShouldRelease(bool spawned, float dist)
        {
            return spawned && dist >= ReleaseDist;
        }
    }
}
