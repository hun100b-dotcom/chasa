// =============================================================================
// GuideQueue.cs — '처음 5분' 안내 대기줄 (순수 C#, 테스트 가능). 기획 first-5-minutes.md 의 원칙 다섯을 그대로 코드로 옮긴 것.
//
// 규칙(왜 이렇게?):
//   1) 한 번에 안내 하나 — 앞 안내가 닫힌 뒤 1초가 지나야 다음이 뜬다(화면이 글로 가득 차지 않게).
//   2) "해 보면 닫힌다" — 시간이 지나서 사라지지 않고, 플레이어가 그 행동을 하면 초록 체크 0.4초 뒤 닫힌다. (예외: 시간제 안내는 Dur 초 뒤)
//   3) 20초 동안 안 하면 한 번 깜빡여 다시 알린다(Remind). 이미 한 행동이면 안내 자체를 띄우지 않는다.
//   4) 끄기(Enabled=false)와 '이미 봄' 목록(Done)을 저장해 이어하기에서 다시 안 뜨게 할 수 있다.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public sealed class GuideStep
    {
        public string Id, Pc, Touch, Key;   // Key = 키 그림에 쓸 글자(예: "Space"). 폰은 비운다
        public bool Timed; public float Dur = 3f;   // Timed: 행동과 상관없이 Dur 초 뒤 닫힘(지도·줌 같은 '선택' 안내)
    }

    public sealed class GuideQueue
    {
        public bool Enabled = true;
        public const float Gap = 1f, CheckTime = 0.4f, RemindAfter = 20f;
        readonly Dictionary<string, GuideStep> defs = new Dictionary<string, GuideStep>();
        readonly HashSet<string> done = new HashSet<string>();
        readonly List<string> queue = new List<string>();
        float age, gap, checkT;

        public GuideStep Current { get; private set; }
        /// <summary>초록 체크를 보이는 중(행동을 한 뒤 0.4초)</summary>
        public bool Checking { get { return Current != null && checkT > 0f; } }
        /// <summary>20초 넘게 행동이 없을 때 20초 간격으로 0.8초 동안 true — 화면이 안내를 깜빡인다</summary>
        public bool Reminding { get { return Current != null && !Current.Timed && checkT <= 0f && age >= RemindAfter && (age - RemindAfter) % RemindAfter < 0.8f; } }

        public void Define(GuideStep s) { defs[s.Id] = s; }
        public bool Has(string id) { return defs.ContainsKey(id); }
        public bool IsDone(string id) { return done.Contains(id); }
        public IEnumerable<string> DoneIds { get { return done; } }
        public void MarkDone(string id) { done.Add(id); }   // 저장 파일에서 불러올 때

        /// <summary>안내를 띄울 상황이 되었다. 이미 한 행동이거나 이미 줄 서 있으면 무시</summary>
        public void Request(string id)
        {
            if (!Enabled || !defs.ContainsKey(id) || done.Contains(id) || queue.Contains(id) || (Current != null && Current.Id == id)) return;
            queue.Add(id);
        }

        /// <summary>플레이어가 그 행동을 했다. 지금 떠 있으면 체크 후 닫고, 줄 서 있으면 빼며, 앞으로도 안 띄운다</summary>
        public void Complete(string id)
        {
            if (done.Contains(id) && (Current == null || Current.Id != id)) { queue.Remove(id); return; }
            done.Add(id); queue.Remove(id);
            if (Current != null && Current.Id == id && checkT <= 0f) checkT = CheckTime;
        }

        public void Tick(float dt)
        {
            if (!Enabled) { Current = null; queue.Clear(); return; }
            if (Current == null)
            {
                if (gap > 0f) gap -= dt;
                if (gap <= 0f && queue.Count > 0) { Current = defs[queue[0]]; queue.RemoveAt(0); age = 0f; checkT = 0f; }
                return;
            }
            age += dt;
            if (checkT > 0f) { checkT -= dt; if (checkT <= 0f) { Current = null; gap = Gap; } return; }
            if (Current.Timed && age >= Current.Dur) { done.Add(Current.Id); Current = null; gap = Gap; }
        }

        public string TextFor(bool touch) { return Current == null ? null : (touch && !string.IsNullOrEmpty(Current.Touch) ? Current.Touch : Current.Pc); }
    }
}
