// =============================================================================
// Dialogue.cs — NPC 대화 진행 규칙 (순수 C#, 테스트 가능). 대사 데이터(Resources/Data/dialogues.json)는 기획이 채운다.
// 규칙: F 로 말을 걸면 첫 줄이 뜨고, F 를 누를 때마다 다음 줄, 마지막 줄 뒤에 F 를 누르면 닫힌다. 한 번 끝낸 대화는 '들었음'으로 기록해
//       같은 사람에게 다시 말을 걸면 마지막 한 줄(되풀이 줄, repeat)만 말한다. 멀어지면(MaxDist) 저절로 닫힌다.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public sealed class TalkEntry
    {
        public string Npc;                 // 말 걸 대상의 이름(NpcWorld 의 표시 이름)
        public string[] Lines;             // 처음 말을 걸 때의 줄들
        public string Repeat;              // 이미 들은 뒤 다시 걸 때 한 줄(없으면 마지막 줄)
        public string GiveClue;            // 끝까지 들으면 얻는 단서 id(없으면 비움)
    }

    public sealed class DialogueState
    {
        public const float MaxDist = 4.5f;
        readonly Dictionary<string, TalkEntry> byNpc = new Dictionary<string, TalkEntry>();
        readonly HashSet<string> heard = new HashSet<string>();
        string[] lines; int idx; TalkEntry cur;

        public void Add(TalkEntry e) { if (e != null && !string.IsNullOrEmpty(e.Npc) && e.Lines != null && e.Lines.Length > 0) byNpc[e.Npc] = e; }
        public bool Has(string npc) { return npc != null && byNpc.ContainsKey(npc); }
        public int Count { get { return byNpc.Count; } }
        public bool Active { get { return cur != null; } }
        public string Speaker { get { return cur != null ? cur.Npc : null; } }
        public string Line { get { return cur != null && idx < lines.Length ? lines[idx] : null; } }
        public bool IsLast { get { return cur != null && idx >= lines.Length - 1; } }
        public bool Heard(string npc) { return heard.Contains(npc); }
        public IEnumerable<string> HeardIds { get { return heard; } }
        public void MarkHeard(string npc) { heard.Add(npc); }

        /// <summary>말을 건다. 대사가 없는 사람이면 false</summary>
        public bool Start(string npc)
        {
            TalkEntry e; if (!byNpc.TryGetValue(npc, out e)) return false;
            cur = e; idx = 0;
            lines = heard.Contains(npc) ? new[] { string.IsNullOrEmpty(e.Repeat) ? e.Lines[e.Lines.Length - 1] : e.Repeat } : e.Lines;
            return true;
        }

        /// <summary>F 한 번: 다음 줄. 마지막 줄 뒤면 닫고 그 대화의 단서 id(없으면 null)와 함께 true 를 돌려준다(끝났다는 뜻)</summary>
        public bool Advance(out string clue)
        {
            clue = null;
            if (cur == null) return false;
            if (idx < lines.Length - 1) { idx++; return false; }
            bool first = !heard.Contains(cur.Npc);
            heard.Add(cur.Npc);
            if (first && !string.IsNullOrEmpty(cur.GiveClue)) clue = cur.GiveClue;
            cur = null; lines = null; idx = 0;
            return true;
        }

        public void Close() { cur = null; lines = null; idx = 0; }
    }
}
