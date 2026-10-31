// =============================================================================
// FirstHitTimer.cs — '조작권을 받고 첫 타격이 맞기까지' 재는 시계 (순수 C#, 테스트 가능). 개편안 P2 "30초 안 첫 타격".
// 왜 필요한가? 손맛 게임은 첫 30초에 때리는 재미가 나와야 한다. 사람 눈대중이 아니라 숫자로 남기려고 잰다.
// 규칙: 컷신·낮 화면·창이 열린 동안엔 시계가 가지 않는다(플레이어가 아무것도 못 하는 시간이라 공정하게 뺀다).
//       첫 타격이 맞으면 그 시각을 한 번만 기록하고 멈춘다. 수치 기둥(천도·파혼 값)과 무관하다.
// =============================================================================
namespace Chasa.Core
{
    public class FirstHitTimer
    {
        public float Elapsed;        // 조작할 수 있었던 시간(초)
        public bool Hit;             // 첫 타격이 맞았나
        public float HitAt = -1f;    // 첫 타격이 맞은 때(조작 시간 기준, 초). 아직이면 -1

        /// <summary>매 프레임 부른다. canAct = 지금 플레이어가 조작할 수 있나(컷·낮 화면·창이 아님)</summary>
        public void Tick(float dt, bool canAct)
        {
            if (Hit || !canAct) return;
            Elapsed += dt;
        }

        /// <summary>내 타격이 적에게 맞았다. 처음 한 번만 기록하고, 기록했으면 true</summary>
        public bool OnHit()
        {
            if (Hit) return false;
            Hit = true; HitAt = Elapsed;
            return true;
        }

        /// <summary>목표(초) 안이었나. 아직 못 쳤으면 false</summary>
        public bool WithinGoal(float goalSec) { return Hit && HitAt <= goalSec; }
    }
}
