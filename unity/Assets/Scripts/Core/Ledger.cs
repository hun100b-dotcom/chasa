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
        public int Ore;           // 광석 (장비를 풀면 얻고, 매듭 올리기에 쓴다)
        public int Karma;         // 업 (파혼하면 쌓이고, 천도 2회마다 1씩 줄어든다)
        public int TendoTotal;    // 지금까지 천도한 횟수 (업 감쇠 계산용)
        public int TendoStreak;   // 연속 천도 횟수
        public int MaxHp = Balance.PLAYER_MAX_HP;   // 최대 체력 (장비 생명 옵션으로 늘어난다)
        public int Hp = Balance.PLAYER_MAX_HP; // 플레이어 체력
        public bool Dead => Hp <= 0;

        /// <summary>피해를 입는다. 체력은 0 밑으로 내려가지 않는다. 반환: 실제로 깎인 양</summary>
        public int TakeDamage(int amount)
        {
            int before = Hp;
            Hp = System.Math.Max(0, Hp - System.Math.Max(0, amount));
            return before - Hp;
        }

        /// <summary>
        /// 체력 회복 한 걸음. 서낭당 안이면 언제나 빠르게(안전한 쉼터), 밖이면 마지막으로 맞고 REGEN_DELAY 초가 지난 뒤에 천천히.
        /// 왜? 처음 하는 사람이 480초 동안 체력이 한 번도 안 차면 보스에 닿기 전에 죽는다 (QA M6).
        /// 반환: 실제로 오른 체력(소수는 버리지 않고 쌓는다)
        /// </summary>
        public int Regen(float dt, bool inShrine, float sinceHit)
        {
            if (Dead || Hp >= MaxHp) { regenAcc = 0f; return 0; }
            float rate = inShrine ? Balance.SHRINE_HEAL_PER_SEC : (sinceHit >= Balance.REGEN_DELAY ? Balance.REGEN_PER_SEC : 0f);
            regenAcc += rate * dt;
            int whole = (int)regenAcc;
            if (whole <= 0) return 0;
            regenAcc -= whole;
            int before = Hp;
            Hp = System.Math.Min(MaxHp, Hp + whole);
            return Hp - before;
        }
        float regenAcc;   // 아직 정수가 안 된 회복량

        /// <summary>한 판을 다시 시작할 때 체력만 되돌린다 (넋·기억 같은 장부는 결과 화면에서 따로 다룬다)</summary>
        public void ResetHp() { Hp = MaxHp; }

        /// <summary>최대 체력이 바뀌면 늘어난 만큼만 현재 체력도 올린다(줄어들면 최대치까지만)</summary>
        public void SetMaxHp(int max)
        {
            if (max == MaxHp) return;
            Hp = System.Math.Min(max, Hp + System.Math.Max(0, max - MaxHp));
            MaxHp = max;
        }

        /// <summary>천도 하나가 끝났을 때. 넋(업 단계 보상 배율 적용)·기억을 얻고 업이 N회마다 1 줄어든다</summary>
        public void CompleteTendo()
        {
            Neok += (int)System.Math.Round(Balance.TENDO_NEOK * CoreRules.RewardMult(Karma));
            Memory += Balance.TENDO_MEMORY;
            TendoStreak++;
            CountForDecay();
        }

        /// <summary>
        /// 업 감쇠 횟수 세기: 천도와 눕히기(시즌 3 '천도의 백 버전')를 같이 세어 2회마다 업 −1 (LOCKED-DECISIONS).
        /// 왜 감쇠? 업이 오르기만 하면 긴 게임 끝에서 모두가 '업 높음'이 되어 천도의 선택이 결말에 의미를 갖지 못한다
        /// </summary>
        void CountForDecay()
        {
            TendoTotal++;
            if (TendoTotal % Balance.KARMA_DECAY_TENDO_INTERVAL == 0)
                Karma = System.Math.Max(0, Karma - 1);
        }

        /// <summary>
        /// 눕히기 하나가 끝났을 때 (시즌 3 백 보스, 시연판에는 없음). 보상은 보스별로 달라 여기서 다루지 않고,
        /// 천도와 같은 횟수로 세어 업만 줄인다. 연속 천도 창에도 이어진다.
        /// </summary>
        public void CompleteLay()
        {
            TendoStreak++;
            CountForDecay();
        }

        /// <summary>보스 천도: 큰 넋과 기억을 얻는다. 업 감쇠 횟수에는 일반 천도와 똑같이 센다</summary>
        public int CompleteBossTendo()
        {
            int gain = (int)System.Math.Round(Balance.BOSS_S1_NEOK * CoreRules.RewardMult(Karma));
            Neok += gain;
            Memory += Balance.BOSS_S1_MEMORY;
            TendoStreak++;
            CountForDecay();
            return gain;
        }

        /// <summary>파혼 하나가 끝났을 때. 엽전을 얻고 업이 쌓이며 연속 천도가 끊긴다</summary>
        public void DoPahon(bool boss = false)
        {
            Coin += boss ? Balance.BOSS_PAHON_COIN : Balance.PAHON_COIN;
            Karma += boss ? Balance.BOSS_PAHON_KARMA : Balance.PAHON_KARMA;
            TendoStreak = 0;
        }
    }
}
