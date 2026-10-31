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
    public enum HintEvent { FirstMove, FirstKneel, FirstHurt, FirstEdgeWarn, FirstNightfall, FirstClue, FirstEliteCharge }

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
                case HintEvent.FirstMove: return touch ? "왼쪽 화면을 끌어 걷기 · 공격 버튼으로 때리기" : "왼쪽 버튼을 누르고 있으면 걷는다 · 혼을 눌러 때리기";
                case HintEvent.FirstKneel: return touch ? "혼이 무릎 꿇었다 — 천도(오래 누르기)·파혼(톡)" : "혼이 무릎 꿇었다 — E 천도(보내기) · R 파혼(깨뜨리기). 고리가 닫히기 전에";
                case HintEvent.FirstHurt: return touch ? "붉게 차오르면 곧 때린다 — 피하기 버튼" : "붉게 차오르면 곧 때린다 — Space 피하기";
                case HintEvent.FirstEdgeWarn: return "화면 가장자리 화살표 = 보이지 않는 혼이 오는 쪽";
                case HintEvent.FirstNightfall: return "밤에는 서낭당에서 F 넋길로 멀리 간다";
                case HintEvent.FirstClue: return "산 사람 곁에 가만히 서 있으면 말이 들린다 · 보스는 단서 3개로 천도";
                // 개편 P1-4(처음 10분 7분): 거센 혼을 처음 만났을 때 '파혼이 지금 정답'인 순간을 한 줄로 알려 준다. 강제 장치 없이 글 한 줄뿐
                case HintEvent.FirstEliteCharge: return touch ? "기를 모으는 중 곁의 꿇은 혼을 파혼하면 공격이 끊긴다" : "기를 모으는 중 곁의 꿇은 혼을 R 파혼하면 공격이 끊긴다";
                default: return null;
            }
        }

        public bool Seen(HintEvent e) { return shown.Contains(e); }
    }
}
