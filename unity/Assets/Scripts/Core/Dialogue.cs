// =============================================================================
// Dialogue.cs — '들은 말' 규칙 (순수 C#, 테스트 가능). 기획 명세 npc-interaction-spec.md v1.
// 세계관상 산 사람은 차사를 못 본다 → '말 걸기'는 없다. 원 안에 머무르면 저절로 듣는다(엿듣기·지켜보기).
//  - DwellTimer: 원 안에 있는 시간을 모은다. 나가면 멈추고, GraceSec(3초) 안에 돌아오면 이어서 쌓는다. 그보다 오래 비우면 처음부터.
//  - HeardLog: 들은 말 기록(명부 '들은 말' 탭용). 같은 자리·같은 말은 한 번만 쌓는다.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public sealed class DwellTimer
    {
        public const float GraceSec = 3f;      // 원을 나가도 이 시간 안에 돌아오면 진행 유지
        public float Progress;                 // 지금까지 모은 초
        float away;                            // 원 밖에 머문 초

        /// <summary>한 프레임. inside=원 안, paused=전투 중이라 멈춤. 필요한 시간(need)을 채우면 true (한 번 채우면 다음 호출부터 다시 0에서 시작)</summary>
        public bool Tick(float dt, bool inside, bool paused, float need)
        {
            if (paused) return false;
            if (inside) { away = 0f; Progress += dt; if (Progress >= need) { Progress = 0f; return true; } }
            else { away += dt; if (away > GraceSec) Progress = 0f; }
            return false;
        }

        public float Ratio(float need) { return need <= 0f ? 0f : (Progress >= need ? 1f : Progress / need); }
    }

    public sealed class HeardEntry { public string Who, Place, Text, Clue; public int Slot; }

    public sealed class HeardLog
    {
        public readonly List<HeardEntry> Items = new List<HeardEntry>();
        readonly HashSet<string> keys = new HashSet<string>();

        /// <summary>기록을 더한다. 이미 있으면 false</summary>
        public bool Add(string who, string place, string text, string clue, int slot)
        {
            if (!keys.Add(who + "|" + place + "|" + slot + "|" + text)) return false;
            Items.Add(new HeardEntry { Who = who, Place = place, Text = text, Clue = clue, Slot = slot });
            return true;
        }
    }
}
