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

        /// <summary>지금 군집을 세워야 하나?</summary>
        public static bool ShouldSpawn(bool spawned, float dist, float cooldownLeft)
        {
            return !spawned && dist <= ActivateDist && cooldownLeft <= 0f;
        }

        /// <summary>지금 군집을 걷어내야 하나?</summary>
        public static bool ShouldRelease(bool spawned, float dist)
        {
            return spawned && dist >= ReleaseDist;
        }
    }
}
