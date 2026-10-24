// =============================================================================
// Soul.cs — 혼(적)의 처결 상태머신 (순수 C#). docs/TIMER-STATE-MACHINE.md 와 같은 규칙.
//
//   Active --맺힘0--> Kneel --천도 시작--> Sending --캐스팅 완료--> Gone
//                      |  ^                   |
//                      |  +--- 피격 중단 ------+
//                      +--파혼(즉시)-----------------------------> Gone
//                      +--대기 초과--> Active (맺힘 50%)
// 규칙: 상태는 이 클래스의 함수로만 바꾼다(밖에서 State 를 직접 바꾸지 않는다).
// =============================================================================
namespace Chasa.Core
{
    public enum SoulState { Active, Kneel, Sending, Gone }
    public enum SoulKind { Fresh, Year, Old, Lump }   // 갓 죽은 / 해 넘긴 / 오래된 / 덩어리

    public class Soul
    {
        public SoulState State = SoulState.Active;
        public SoulKind Kind;
        public int Maedhim;          // 맺힘 (체력 대신 깎이는 수치)
        public int MaedhimMax;
        public float WaitLeft;       // 처결 대기 남은 시간
        public float WaitTotal;
        public float Stun;           // 남은 경직 시간
        public bool Fierce;          // 얼룩 3개로 소환된 사나운 적
        public bool Boss;            // 보스 여부 (천도에 단서 3개 필요, 보상이 큼)
        public string Name;          // 이름혼/보스의 이름 (무명 혼은 null)

        public Soul(SoulKind kind, bool fierce = false)
        {
            Kind = kind;
            Fierce = fierce;
            MaedhimMax = kind == SoulKind.Lump ? Balance.MAEDHIM_LUMP : Balance.MAEDHIM_NORMAL;
            if (fierce) MaedhimMax = (int)(MaedhimMax * Balance.FIERCE_MULT);
            Maedhim = MaedhimMax;
        }

        /// <summary>이름이 있는 혼(박돌쇠 등). 맺힘은 따로 정한다</summary>
        public static Soul Named(string name, SoulKind kind, int maedhim)
        {
            var s = new Soul(kind) { Name = name, MaedhimMax = maedhim, Maedhim = maedhim };
            return s;
        }

        /// <summary>시연판 S1 보스 나루 영감. 대기·맺힘은 Balance 의 보스 값</summary>
        public static Soul MakeBossS1()
        {
            return new Soul(SoulKind.Old) { Name = "나루 영감", Boss = true, MaedhimMax = Balance.BOSS_S1_MAEDHIM, Maedhim = Balance.BOSS_S1_MAEDHIM };
        }

        public bool Alive { get { return State == SoulState.Active; } }
        public bool Kneeling { get { return State == SoulState.Kneel; } }
        /// <summary>덩어리는 천도 불가 → 파혼만 (W-004)</summary>
        public bool CanTendo { get { return Kind != SoulKind.Lump; } }
        /// <summary>천도 가능 여부(단서 반영). 보스는 낮 단서가 BOSS_CLUES_REQUIRED 개 이상이어야 한다 (N-005, B-1 확정)</summary>
        public bool CanTendoWith(int clues) { return CanTendo && (!Boss || clues >= Balance.BOSS_CLUES_REQUIRED); }

        public float WaitTimeForKind()
        {
            if (Boss) return Balance.BOSS_S1_WAIT;
            switch (Kind)
            {
                case SoulKind.Fresh: return Balance.WAIT_FRESH;
                case SoulKind.Year: return Balance.WAIT_YEAR;
                case SoulKind.Old: return Balance.WAIT_OLD;
                default: return Balance.WAIT_LUMP;
            }
        }

        /// <summary>맞아서 맺힘이 깎인다. 이번 타격으로 0이 되면 true (= 무릎 꿇음. 죽는 게 아니다)</summary>
        public bool TakeHit(int damage)
        {
            if (State != SoulState.Active) return false;   // 무릎 꿇은 혼은 더 못 때린다
            Maedhim -= damage;
            if (Maedhim <= 0)
            {
                Maedhim = 0;
                State = SoulState.Kneel;
                WaitTotal = WaitTimeForKind();
                WaitLeft = WaitTotal;
                return true;
            }
            return false;
        }

        /// <summary>천도 캐스팅 시작: 대기 타이머가 멈춘다. 무릎 꿇은 혼만 가능</summary>
        public bool BeginSending()
        {
            if (State != SoulState.Kneel || !CanTendo) return false;
            State = SoulState.Sending;
            return true;
        }

        /// <summary>캐스팅이 끊겼다 → 다시 대기 (남은 시간은 그대로)</summary>
        public void CancelSending()
        {
            if (State == SoulState.Sending) State = SoulState.Kneel;
        }

        /// <summary>천도 완료 또는 파혼으로 떠남</summary>
        public void Finish()
        {
            State = SoulState.Gone;
        }

        /// <summary>파혼: 무릎 꿇은 혼만 즉시 터뜨릴 수 있다</summary>
        public bool TryPahon()
        {
            if (State != SoulState.Kneel) return false;
            Finish();
            return true;
        }

        /// <summary>시간이 흐른다. 대기가 끝나면 맺힘 일부를 되찾고 다시 일어선다 (W-005 임시 해석)</summary>
        public void Tick(float dt)
        {
            if (State != SoulState.Kneel) return;
            WaitLeft -= dt;
            if (WaitLeft <= 0f)
            {
                State = SoulState.Active;
                Maedhim = System.Math.Max(1, (int)(MaedhimMax * Balance.WAIT_TIMEOUT_RECOVER));
                Stun = 0.4f;
            }
        }
    }
}
