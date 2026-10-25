// =============================================================================
// Act2Gate.cs — 2막 금줄(붉은재 고개 R2-1·쇳골 산길 R2-2)이 풀리는 날 (순수 C#, 테스트 가능). 서사 확정 10-25.
//
// 규칙: 두 금줄은 '흑월 1차 대결(② 무덤골)이 있었던 밤'의 다음 새벽에 함께 풀린다.
//  - 흑월 1차는 B-01~B-03을 모두 처결한 다음 첫 밤에 무덤골에 나타난다.
//  - 처결이 덜 됐어도 ② 검은여울에 처음 들어간 뒤 5번째 새벽이 지난 밤에는 나타난다(막히지 않게).
//  - 그 밤 무덤골에 안 갔어도 다음 새벽엔 풀린다.
//  - 풀리기 전에 금줄에 다가가면 한 줄 안내: "명부에 아직 이 관할이 없다".
// 날짜는 '하루 번호'(0부터). 하루 = 새벽→낮→해질녘→밤. 밤 n 의 다음 새벽 = 하루 n+1 의 시작.
// =============================================================================
using System;

namespace Chasa.Core
{
    public static class Act2Gate
    {
        public const string BlockedLine = "명부에 아직 이 관할이 없다";

        /// <summary>
        /// 금줄이 풀리는 하루 번호(그날 새벽부터 열림). 아직 알 수 없으면 int.MaxValue.
        /// allDoneDay: B-01~B-03 을 모두 처결한 하루 번호(밤에 처결했으면 그 밤이 속한 하루), 아직이면 -1.
        /// allDoneAtNight: 마지막 처결이 밤에 있었나(그러면 '다음 첫 밤'은 다음 날 밤).
        /// enterDay: ② 검은여울에 처음 들어간 하루 번호, 아직이면 -1.
        /// </summary>
        public static int OpenDay(int allDoneDay, bool allDoneAtNight, int enterDay)
        {
            int night = HeukwolNight(allDoneDay, allDoneAtNight, enterDay);
            return night == int.MaxValue ? int.MaxValue : night + 1;                         // 그 밤의 다음 새벽
        }

        /// <summary>흑월 1차가 나타나는 밤이 속한 하루 번호(없으면 int.MaxValue)</summary>
        public static int HeukwolNight(int allDoneDay, bool allDoneAtNight, int enterDay)
        {
            int night = int.MaxValue;
            if (allDoneDay >= 0) night = allDoneAtNight ? allDoneDay + 1 : allDoneDay;      // 처결 뒤 첫 밤
            if (enterDay >= 0) night = Math.Min(night, enterDay + 5);                        // 5번째 새벽이 지난 밤(= 들어간 날로부터 5일째 밤)
            return night;
        }

        public static bool IsOpen(int today, int allDoneDay, bool allDoneAtNight, int enterDay) { return today >= OpenDay(allDoneDay, allDoneAtNight, enterDay); }
    }
}
