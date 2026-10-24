// =============================================================================
// AttackClock.cs — 적 한 마리의 '공격 시계' (순수 C#, 화면과 무관)
// 쿨다운 → 예비동작(선딜) → 타격 순서로 돈다. 예비동작 동안 플레이어가 멀리 피하면 헛스윙이다.
// 왜 코어에 두나? "피할 수 있는 신호"가 손맛의 핵심이라, 엔진 없이 자동 테스트로 지키려고.
// =============================================================================
namespace Chasa.Core
{
    public class AttackClock
    {
        public float Cooldown = Balance.ENEMY_ATTACK_INTERVAL; // 다음 공격까지 남은 시간
        public float Windup;                                   // 예비동작 남은 시간 (0이면 준비 중 아님)
        public bool Winding => Windup > 0f;
        /// <summary>예비동작 진행도 0~1 (화면에서 적이 부풀거나 붉어지는 연출용)</summary>
        public float WindupRatio => Winding ? 1f - Windup / Balance.ENEMY_ATTACK_WINDUP : 0f;

        /// <summary>
        /// 한 프레임 진행. dist = 적과 플레이어 사이 거리, canAct = 적이 움직일 수 있는 상태(무릎 꿇음·기절이면 false).
        /// 반환: 이번 프레임에 '타격이 명중'했으면 true (플레이어가 피해를 입는다)
        /// </summary>
        public bool Tick(float dt, float dist, bool canAct)
        {
            if (!canAct) { Interrupt(); return false; }

            if (Winding)
            {
                Windup -= dt;
                if (Windup > 0f) return false;
                // 예비동작 끝: 사거리 + 회피 여유 안에 아직 있으면 명중, 아니면 피한 것
                Windup = 0f;
                Cooldown = Balance.ENEMY_ATTACK_INTERVAL;
                return dist <= Balance.ENEMY_ATTACK_RANGE + Balance.ENEMY_ATTACK_DODGE_MARGIN;
            }

            Cooldown -= dt;
            // 사거리 안에 들어와야 예비동작을 시작한다 (멀리서 헛되이 휘두르지 않게)
            if (Cooldown <= 0f && dist <= Balance.ENEMY_ATTACK_RANGE)
                Windup = Balance.ENEMY_ATTACK_WINDUP;
            return false;
        }

        /// <summary>맞아서 끊김: 예비동작이 취소되고 쿨다운이 처음부터 다시 돈다 (때리는 쪽이 이득이어야 손맛이 산다)</summary>
        public void Interrupt()
        {
            if (Windup > 0f) Cooldown = Balance.ENEMY_ATTACK_INTERVAL;
            Windup = 0f;
        }
    }
}
