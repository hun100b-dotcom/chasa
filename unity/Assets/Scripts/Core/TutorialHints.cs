// =============================================================================
// TutorialHints.cs — 처음 한 번만 뜨는 안내 문구 틀 (순수 C#, 테스트 가능). 기획 8단계 '첫 30분'의 뼈대.
//
// 왜 틀만? 안내가 언제·무슨 말로 나올지(박자표)는 서사·기획이 하루 40분 시계 기준으로 다시 정하는 중이다.
// 그래서 여기서는 '사건(Event) → 문구, 한 번만' 규칙만 만든다. 문구와 사건 목록은 나중에 데이터로 바꿔 끼우기 쉽다.
// 터치(폰)와 키보드는 같은 사건에 다른 문구를 보여 준다(키보드엔 키 이름, 폰엔 버튼 이름).
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public enum HintEvent { FirstMove, FirstKneel, FirstHurt, FirstEdgeWarn, FirstNightfall, FirstClue }

    public class TutorialHints
    {
        readonly HashSet<HintEvent> shown = new HashSet<HintEvent>();
        public bool Enabled = true;

        /// <summary>사건이 처음이면 문구를, 아니면 null. touch=true 면 폰용 문구</summary>
        public string On(HintEvent e, bool touch)
        {
            if (!Enabled || !shown.Add(e)) return null;
            switch (e)
            {
                case HintEvent.FirstMove: return touch ? "왼쪽 아래를 눌러 걷고, 혼을 눌러 사슬을 날린다" : "WASD 또는 마우스 클릭으로 걷고, 혼을 눌러 사슬을 날린다 (휠: 확대·축소)";
                case HintEvent.FirstKneel: return touch ? "혼이 무릎 꿇었다 — 천도(보냄) 또는 파혼(깨뜨림) 버튼" : "혼이 무릎 꿇었다 — E 천도(보냄) / R 파혼(깨뜨림). 발밑 고리가 줄어들기 전에";
                case HintEvent.FirstHurt: return touch ? "붉게 달아오르면 곧 때린다 — 피하기 버튼" : "혼이 붉게 달아오르면 곧 때린다 — Space 로 피하기";
                case HintEvent.FirstEdgeWarn: return "화면 가장자리 붉은 표시 = 시야 밖에서 덮쳐 오는 혼의 방향";
                case HintEvent.FirstNightfall: return "밤이 되면 혼이 일어선다 — 서낭당 곁에서 F(넋길)로 멀리 이동";
                case HintEvent.FirstClue: return "산 사람 곁에 서서 말을 엿들으면 단서가 된다 (보스는 단서 3개가 있어야 천도)";
                default: return null;
            }
        }

        public bool Seen(HintEvent e) { return shown.Contains(e); }
    }
}
