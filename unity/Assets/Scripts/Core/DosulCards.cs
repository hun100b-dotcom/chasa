// =============================================================================
// DosulCards.cs — 첫 도술 카드 다섯 번 (기획 combat/first-elite-and-dosul-cards.md §2, 처음 10분 M9)
// 도술 점수 처음 다섯 점은 '카드 세 장 중 하나'로 쓴다. 세 장은 늘 갈래 하나씩(부름·줄·얼룩), 놓는 자리는 섞는다.
// 왜 카드로: 트리 창에서 점수를 찍는 것보다 '손으로 고르는 순간'이 첫 선택의 재미를 준다. 여섯째 점부터는 도술 창이 열린다.
// 순수 C#(엔진 무관): 무엇을 보여 줄지만 정한다. 화면·입력은 UiRoot/JudgeSystem.
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public static class DosulCards
    {
        public const int Rounds = 5;                 // 카드로 쓰는 점수 수
        public static bool Open;                     // 카드가 떠 있나(화면이 세계를 멈추는 데 쓴다)
        public const int RerollCoin = 20;            // 다시 뽑기 엽전(첫 판은 없음)

        // 판별 후보 풀(②~④). 갈래마다 같은 판에서 하나를 무작위로 뽑는다
        static readonly string[][][] Pools =
        {
            null,   // ① 고정
            new[] { new[] { "고마운 넋", "곁을 지킴" }, new[] { "단단한 손", "긴 사슬" }, new[] { "노잣돈", "큰 폭발" } },
            new[] { new[] { "오래 부르기", "몫을 채움" }, new[] { "묶인 자", "손에 익음" }, new[] { "세찬 넉백", "마른 얼룩" } },
            new[] { new[] { "혼불 날리기", "이름 비추기" }, new[] { "매듭 걸음", "여럿 끌기" }, new[] { "원념 두르기", "얼룩 타기" } },
        };
        // 처음 다섯 판에 안 나오는 것: 깊은 도술(10점 필요), 한 줄 꿰기, 깨진 이름 던지기
        static bool Excluded(SkillNode n) { return n.Deep || n.Name == "한 줄 꿰기" || n.Name == "깨진 이름 던지기"; }

        /// <summary>round(0~4)번째 카드 세 장의 도술 이름. 갈래 하나씩이고 자리(왼·가운데·오른)는 섞여 있다. 배울 수 없는 건 뺀다(그 갈래가 비면 장수가 줄 수 있다)</summary>
        public static List<string> Offer(int round, GrowthState g, Func<float> rand, HashSet<string> seen = null)
        {
            var picks = new List<string>();
            var branches = new[] { Branch.Call, Branch.Chain, Branch.Stain };
            for (int b = 0; b < 3; b++)
            {
                string name = null;
                if (round == 0) name = new[] { "붙잡아 부르기", "휘감기", "터뜨리기" }[b];
                else
                {
                    var cand = new List<string>();
                    if (round <= 3) foreach (var n in Pools[round][b]) if (g.CanLearn(n)) cand.Add(n);
                    if (round == 2) foreach (var n in Pools[1][b]) if (g.LevelOf(n) == 1 && g.CanLearn(n)) cand.Add(n);   // ③은 가진 패시브를 한 단계 더(+1단계)도 나온다
                    if (cand.Count == 0)   // ⑤ 와 메우기: 이 갈래에서 안 나온 것 → 아무거나
                    {
                        foreach (var n in SkillTree.All)
                            if (n.Branch == branches[b] && !Excluded(n) && g.CanLearn(n.Name) && (seen == null || !seen.Contains(n.Name))) cand.Add(n.Name);
                        if (cand.Count == 0)
                            foreach (var n in SkillTree.All) if (n.Branch == branches[b] && !Excluded(n) && g.CanLearn(n.Name)) cand.Add(n.Name);
                    }
                    if (cand.Count > 0) name = cand[Math.Min(cand.Count - 1, (int)(rand() * cand.Count))];
                }
                if (name != null) picks.Add(name);
            }
            for (int i = picks.Count - 1; i > 0; i--)   // 자리 섞기(한쪽이 늘 왼쪽이면 추천처럼 보인다)
            { int j = Math.Min(i, (int)(rand() * (i + 1))); var t = picks[i]; picks[i] = picks[j]; picks[j] = t; }
            return picks;
        }

        /// <summary>카드 표시: 갈래 모양(색약 규칙: 모양으로 구분)</summary>
        public static string Mark(Branch b) { return b == Branch.Call ? "↑" : b == Branch.Chain ? "●" : "×"; }

        /// <summary>처음 다섯 판에 한해 얼룩 점수 3마다 도술 점수 1로 바꾼다(파혼만 하는 사람도 첫 성장이 오게). 바꾼 횟수를 돌려준다</summary>
        public static int ConvertStain(GrowthState g)
        {
            int n = 0;
            while (g.StainPointsFree >= 3) { g.StainPointsSpent += 3; g.SkillPointsEarned++; n++; }
            return n;
        }
    }
}
