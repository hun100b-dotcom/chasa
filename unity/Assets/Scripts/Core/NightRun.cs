// =============================================================================
// NightRun.cs — '하룻밤 한 판'의 뼈대 (순수 C#). 해 질 무렵 출발 → 밤 전투 → 동트기 전 서낭당 귀환.
// 핵심 규칙(기둥 3): 못 돌아오면 '추가 수확분'만 잃고, 명부 몫과 성장은 보존된다.
//   - 명부 몫 = NIGHT_QUOTA 만큼의 천도. 그 위로 천도한 만큼이 '추가 수확분'.
// 왜 코어에? 한 판의 승패 규칙이 화면 코드에 섞이면 시험도 어렵고 나중에 값을 고치기도 힘들다.
// =============================================================================
namespace Chasa.Core
{
    public enum NightPhase { Night, Returned, Dawn }   // 밤 진행 중 / 제때 귀환(성공) / 동이 터 버림(실패)

    public class NightRun
    {
        public float TimeLeft = Balance.NIGHT_DURATION;
        public NightPhase Phase = NightPhase.Night;
        public int Sent;           // 이번 밤에 천도한 혼 수
        public int KeptNeok;       // 명부 몫으로 확정된 넋(실패해도 보존)
        public int ExtraNeok;      // 추가 수확분 넋(실패하면 잃음)

        public int KeptCoin;       // 명부 몫을 채우기 전에 번 엽전(실패해도 보존)
        public int ExtraCoin;      // 몫을 채운 뒤에 번 엽전 = 명부 밖 엽전(동이 트면 흩어짐)
        public int Clues;          // 주운 낮 단서 수 (보스 천도 조건)
        public bool NamedSpawned;  // 이름혼(박돌쇠)이 이미 나왔나
        public bool BossDone;      // 보스를 처결했나

        public void PickClue() { if (Clues < Balance.BOSS_CLUES_REQUIRED) Clues++; }

        /// <summary>
        /// 이름혼은 명부 맨 아래 줄이라 몫의 '마지막 하나'로 나온다: 무명 혼을 몫-1 마리 보낸 뒤 한 번만 (서사 확정)
        /// 반환이 true 면 지금 이름혼을 내보내라.
        /// </summary>
        public bool TakeNamedSpawn()
        {
            if (Over || NamedSpawned || Sent < Balance.NIGHT_QUOTA - 1) return false;
            NamedSpawned = true;
            return true;
        }

        /// <summary>파혼으로 번 엽전을 쌓는다. 몫(천도 NIGHT_QUOTA 개)을 채우기 전 것은 몫, 이후 것은 명부 밖(추가 수확분)</summary>
        public void RecordCoin(int coin)
        {
            if (Over) return;
            if (QuotaDone) ExtraCoin += coin; else KeptCoin += coin;
        }

        /// <summary>보스 처결 보상은 몫이 아니라 '추가 수확분'이다 (동이 트면 잃는다 — 어디까지 갈 것인가의 위험)</summary>
        public void RecordBoss(int neokGained)
        {
            if (Over) return;
            BossDone = true;
            ExtraNeok += neokGained;
        }

        public bool Over => Phase != NightPhase.Night;
        public bool QuotaDone => Sent >= Balance.NIGHT_QUOTA;
        public bool Warning => !Over && TimeLeft <= Balance.NIGHT_WARN_TIME;
        /// <summary>밤이 얼마나 지났나 0(해 질 무렵)~1(동트기). 하늘 색 보간용</summary>
        public float Progress => 1f - TimeLeft / Balance.NIGHT_DURATION;

        /// <summary>천도 하나가 끝났을 때 얻은 넋을 몫/추가 수확분 중 어디에 쌓을지 정한다</summary>
        public void RecordTendo(int neokGained)
        {
            if (Over) return;
            Sent++;
            if (Sent <= Balance.NIGHT_QUOTA) KeptNeok += neokGained; else ExtraNeok += neokGained;
        }

        public void Tick(float dt)
        {
            if (Over) return;
            TimeLeft -= dt;
            if (TimeLeft <= 0f) { TimeLeft = 0f; Phase = NightPhase.Dawn; }
        }

        /// <summary>서낭당 반경 안에서 귀환을 시도. 밤이 끝나지 않았을 때만 성공</summary>
        public bool TryReturn(float distToShrine)
        {
            if (Over || distToShrine > Balance.SHRINE_RADIUS) return false;
            Phase = NightPhase.Returned;
            return true;
        }

        /// <summary>결과로 확정되는 넋: 성공이면 전부, 실패(동이 틈)면 명부 몫만</summary>
        public int FinalNeok => Phase == NightPhase.Returned ? KeptNeok + ExtraNeok : KeptNeok;
        public int FinalCoin => Phase == NightPhase.Returned ? KeptCoin + ExtraCoin : KeptCoin;
        public int LostCoin => Phase == NightPhase.Dawn ? ExtraCoin : 0;
        public int LostNeok => Phase == NightPhase.Dawn ? ExtraNeok : 0;
    }
}
