// =============================================================================
// Ledger.cs — 플레이어의 '장부': 넋·기억·엽전·업과 천도 횟수 (순수 C#)
// 천도·파혼이 끝났을 때 무엇이 얼마나 바뀌는지를 한 곳에서 정한다.
// =============================================================================
namespace Chasa.Core
{
    public class Ledger
    {
        public int Neok;          // 넋 (천도 보상)
        public int Memory;        // 기억 조각 (천도 보상)
        public int Coin;          // 엽전 (파혼 보상)
        public int Karma;         // 업 (파혼하면 쌓이고, 천도 2회마다 1씩 줄어든다)
        public int TendoTotal;    // 지금까지 천도한 횟수 (업 감쇠 계산용)
        public int TendoStreak;   // 연속 천도 횟수

        /// <summary>천도 하나가 끝났을 때. 넋(업 단계 보상 배율 적용)·기억을 얻고 업이 N회마다 1 줄어든다</summary>
        public void CompleteTendo()
        {
            Neok += (int)System.Math.Round(Balance.TENDO_NEOK * CoreRules.RewardMult(Karma));
            Memory += Balance.TENDO_MEMORY;
            TendoStreak++;
            TendoTotal++;
            // 왜 감쇠? 업이 오르기만 하면 긴 게임 끝에서 모두가 '업 높음'이 되어 천도의 선택이 결말에 의미를 갖지 못한다
            if (TendoTotal % Balance.KARMA_DECAY_TENDO_INTERVAL == 0)
                Karma = System.Math.Max(0, Karma - 1);
        }

        /// <summary>파혼 하나가 끝났을 때. 엽전을 얻고 업이 쌓이며 연속 천도가 끊긴다</summary>
        public void DoPahon(bool boss = false)
        {
            Coin += Balance.PAHON_COIN;
            Karma += boss ? Balance.BOSS_PAHON_KARMA : Balance.PAHON_KARMA;
            TendoStreak = 0;
        }
    }
}
