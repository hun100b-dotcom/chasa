// =============================================================================
// HudState.cs — 화면 상단 장부(HUD)에 보일 '값 묶음'과 글자 만들기 (순수 C#, 테스트 가능).
//
// 왜 따로 두나? (docs/TECH-DESIGN-UI-FEEL.md U1)
//   예전엔 JudgeSystem 이 화면에 글자를 직접 그렸다(IMGUI). 값이 바뀌면 화면 코드도 같이 고쳐야 했고 검사할 수 없었다.
//   이제 JudgeSystem 은 이 묶음에 '값'만 채운다 → 화면(UI Toolkit/IMGUI 어느 쪽이든)은 이 묶음을 읽어 그린다.
//   글자 만드는 규칙(어떤 순서로 무슨 말을 보여 줄지)이 여기 있어서 유니티 없이 테스트된다.
// =============================================================================
using System.Text;

namespace Chasa.Core
{
    public sealed class HudState
    {
        // 장부
        public int Neok, Memory, Coin, Karma;
        public bool ChainBonus;                 // 연쇄 천도 창이 열려 있나
        // 몸
        public int Hp, MaxHp, Heal;
        // 밤
        public int SecondsLeft, Sent, Quota, Clues, CluesNeeded;
        public bool BossDone, QuotaDone, Warning;
        // 시각 고리(오른쪽 위 해시계): TimeOfDay 0~1 = 하루 중 위치(0=해질녘 시작, 0.5=한밤, 1=동틀녘), IsDawn=붉은 구간.
        // 지금은 밤 남은 시간에서 만들고, 3단계(월드 시계)가 오면 그 값으로 바꾼다
        public float TimeOfDay; public bool IsDawn;
        // 아래쪽 기술 줄
        public float DodgeCharges; public int DodgeMax;     // 피하기 충전(소수는 충전 중인 칸)
        public float PullCd;                                // 끌어당김 남은 시간(초, 0이면 쓸 수 있음)
        public string WeaponName = "";
        public readonly System.Collections.Generic.List<EdgeMark> Edges = new System.Collections.Generic.List<EdgeMark>();   // 화면 가장자리 경고(시야 밖 공격 예고)
        public readonly ToastStack Toasts = new ToastStack();   // 얻은 것 알림(왼쪽 가운데)

        public float HpRatio { get { return MaxHp <= 0 ? 0f : System.Math.Max(0f, System.Math.Min(1f, (float)Hp / MaxHp)); } }
        /// <summary>체력이 이 비율 아래면 위험 색으로 (화면이 쓴다)</summary>
        public bool HpLow { get { return HpRatio < 0.3f; } }

        /// <summary>1줄: 장부 (넋·기억·엽전·업)</summary>
        public string LedgerLine()
        {
            return "넋 " + Neok + "   기억 " + Memory + "   엽전 " + Coin + "   업 " + Karma + " (" + CoreRules.KarmaTier(Karma) + "단계)" + (ChainBonus ? "   연쇄!" : "");
        }

        /// <summary>2줄: 체력과 회복약</summary>
        public string VitalLine() { return "체력 " + Hp + " / " + MaxHp + "   회복약 " + Heal + " (H)"; }

        /// <summary>3줄: 밤 시계·몫·단서</summary>
        public string NightLine()
        {
            var sb = new StringBuilder();
            sb.Append("밤 ").Append(SecondsLeft).Append("초   천도 ").Append(Sent).Append('/').Append(Quota)
              .Append("   단서 ").Append(Clues).Append('/').Append(CluesNeeded);
            if (BossDone) sb.Append("   나루 영감 끝");
            if (QuotaDone) sb.Append("  (당집으로 돌아가라!)");
            if (Warning) sb.Append("   동이 튼다!");
            return sb.ToString();
        }

        /// <summary>안내 한 줄 (키 설명)</summary>
        public static string KeyHint() { return "E: 천도(넋을 보냄)   R: 파혼(넋을 깸)"; }
    }
}
