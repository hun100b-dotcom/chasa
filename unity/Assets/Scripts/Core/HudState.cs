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
        public int Neok, Memory, Coin, Karma; public bool KarmaHidden;   // KarmaHidden: 비 오는 밤엔 업 표시가 ?로 가려진다(업은 그대로 쌓인다)
        public bool ShowNeok = true, ShowMemory = true, ShowCoin = true, ShowKarma = true;   // 처음 얻을 때 열리는 항목(필드 모드)
        public bool ChainBonus;                 // 연쇄 천도 창이 열려 있나
        // 몸
        public int Hp, MaxHp, Heal;
        // 밤
        public int SecondsLeft, Sent, Quota, Clues, CluesNeeded;
        public bool BossDone, QuotaDone, Warning;
        // 시각 고리(오른쪽 위 해시계): TimeOfDay 0~1 = 하루 중 위치(0=해질녘 시작, 0.5=한밤, 1=동틀녘), IsDawn=붉은 구간.
        // 지금은 밤 남은 시간에서 만들고, 3단계(월드 시계)가 오면 그 값으로 바꾼다
        public float TimeOfDay; public bool IsDawn;
        public float Daylight; public bool FullMoon, NewMoon; public int MoonPhase;   // MoonPhase: 0 초승·그믐 / 1 상현 / 2 보름 / 3 하현 —    // 하늘 밝기(0~1)와 달 (시각 고리가 해/달 모양을 고름)
        public bool Peaceful;                                    // 평화로운 낮(주변에 적 없음): 시각 고리만 남기고 나머지 화면을 걷는다
        public string ClockLabel;                                // 필드 모드의 시간대 글자('해질녘 · 보름달'). null 이면 옛 밤 타이머 글자
        // 아래쪽 기술 줄
        public float DodgeCharges; public int DodgeMax;     // 피하기 충전(소수는 충전 중인 칸)
        public float PullCd;                                // 끌어당김 남은 시간(초, 0이면 쓸 수 있음)
        public string WeaponName = "";
        /// <summary>도술 4칸(이름 없으면 빈 칸). Cd = 남은 비율 0~1, CdSec = 남은 초</summary>
        public sealed class SkillSlotView { public string Name; public float Cd, CdSec; }
        public readonly SkillSlotView[] Slots = { new SkillSlotView(), new SkillSlotView(), new SkillSlotView(), new SkillSlotView() };
        public readonly System.Collections.Generic.List<EdgeMark> Edges = new System.Collections.Generic.List<EdgeMark>();   // 화면 가장자리 경고(시야 밖 공격 예고)
        // 처음 5분 안내(화면 하단 중앙 띠). GuideText 가 null 이면 안 보인다
        public string GuideText, GuideKey; public bool GuideCheck, GuideRemind;
        public string BossName; public float BossRatio; public bool BossKneel;   // 보스 체력(맺힘) 막대: 이름이 null 이면 안 보인다
        public string QuestTitle; public string[] QuestLines;                      // 퀘스트 추적(왼쪽, 장부 아래). 제목이 null 이면 안 보인다
        // 화면에 고정된 자막 넷(UiRoot): 소리 자막·컷신 기억 줄·천도 뒤 기억 한 줄·산 사람 대사. 글이 null 이면 안 보인다. Alpha 0~1
        public string SubSfx, SubCutMemory, SubMemLine, SubNpc; public float SubMemLineAlpha = 1f, SubNpcAlpha = 1f;
        public float CastRatio = -1f;                                            // 천도 시전 막대 0~1 (-1 이면 안 보임)
        public string SayText;                                                   // 화면 가운데 위쪽 짧은 한마디(시전이 끊겼다 등). null 이면 안 보임
        public bool ShowExp; public float ExpRatio; public int Rank;                // 경험치(품계) 막대: 처음 넋을 얻은 뒤에 열린다
        public string AreaText; public float AreaAlpha;                          // 지역 진입 알림(화면 위 가운데 큰 글씨, 알파 0~1)
        public bool JudgeCard;                                   // 첫 처결 카드(천도·파혼 두 장)를 하단에 띄운다
        public readonly ToastStack Toasts = new ToastStack();   // 얻은 것 알림(왼쪽 가운데)

        public float HpRatio { get { return MaxHp <= 0 ? 0f : System.Math.Max(0f, System.Math.Min(1f, (float)Hp / MaxHp)); } }
        /// <summary>체력이 이 비율 아래면 위험 색으로 (화면이 쓴다)</summary>
        public bool HpLow { get { return HpRatio < 0.3f; } }

        /// <summary>1줄: 장부 (넋·기억·엽전·업)</summary>
        public string LedgerLine()
        {
            // 하나씩 열기(기획): 처음 얻기 전엔 숨긴다. 기본값은 모두 보임(옛 화면·테스트용)
            var sb = new StringBuilder();
            if (ShowNeok) sb.Append("넋 ").Append(Neok).Append("   ");
            if (ShowMemory) sb.Append("기억 ").Append(Memory).Append("   ");
            if (ShowCoin) sb.Append("엽전 ").Append(Coin).Append("   ");
            if (ShowKarma) sb.Append("업 ").Append(KarmaHidden ? "?" : Karma + " (" + CoreRules.KarmaTier(Karma) + "단계)");
            if (ChainBonus) sb.Append("   연쇄!");
            return sb.ToString().TrimEnd();
        }

        /// <summary>2줄: 체력과 회복약</summary>
        public string VitalLine() { return "체력 " + Hp + " / " + MaxHp + "   회복약 " + Heal + " (H)"; }

        /// <summary>3줄: 밤 시계·몫·단서</summary>
        public string NightLine()
        {
            var sb = new StringBuilder();
            if (ClockLabel != null)
            {
                // 흐르는 하루: 남은 초 대신 시간대. 명부 몫(천도 수)과 단서만 남긴다
                sb.Append(ClockLabel).Append("   천도 ").Append(Sent).Append('/').Append(Quota).Append("   단서 ").Append(Clues).Append('/').Append(CluesNeeded);
                if (BossDone) sb.Append("   나루 영감 끝");
                return sb.ToString();
            }
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
