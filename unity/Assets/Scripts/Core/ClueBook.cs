// =============================================================================
// ClueBook.cs — 낮 단서 장부와 '엿듣기' 규칙 (순수 C#, 테스트 가능). 기획 5단계 '산 사람과 낮 시간표'.
//
// 보스는 단서 BOSS_CLUES_REQUIRED(3)개 이상이어야 천도할 수 있다. 단서는 산 사람을 지켜보고·엿듣고·만져 보아 얻는다.
// 업(카르마)이 쌓이면 귀가 닫힌다(서사 확정): 업 10 → 엿듣기 대사가 반쪽 문장(그래도 단서는 인정)
//                                                업 30 → 보스 엿듣기 단서가 닫힘(사람이 '갑자기 춥네' 하고 떠남)
//                                                업 60 → 마을 소문(단서 없는 엿듣기)까지 모두 닫힘
// 지켜보기·만져 보기는 업의 영향을 받지 않는다(귀가 아니라 눈·손이라서).
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public enum EavesMode { Full, Half, Closed }

    public static class Eavesdrop
    {
        /// <summary>엿듣기 한 번의 결과 모드. isEaves=false(지켜보기·만져 보기)면 항상 Full</summary>
        public static EavesMode Mode(int karma, bool isEaves, bool isBossClue)
        {
            if (!isEaves) return EavesMode.Full;
            if (karma >= 60) return EavesMode.Closed;
            if (karma >= 30 && isBossClue) return EavesMode.Closed;
            if (karma >= 10) return EavesMode.Half;
            return EavesMode.Full;
        }

        public static bool IsEavesVerb(string verb) { return verb == "엿듣기"; }
    }

    public class ClueBook
    {
        readonly HashSet<string> ids = new HashSet<string>();

        /// <summary>저장용: 지금까지 얻은 단서 이름 전부</summary>
        public IEnumerable<string> All { get { return ids; } }

        public bool Has(string id) { return ids.Contains(id); }

        /// <summary>새 단서면 true (이미 있으면 false)</summary>
        public bool Add(string id) { return !string.IsNullOrEmpty(id) && ids.Add(id); }

        /// <summary>접두어(보스 번호, 예 "B01-")로 시작하는 단서 개수</summary>
        public int Count(string prefix)
        {
            int n = 0;
            foreach (var i in ids) if (i.StartsWith(prefix)) n++;
            return n;
        }
    }
}
