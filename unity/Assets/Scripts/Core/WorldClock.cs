// =============================================================================
// WorldClock.cs — 흐르는 하루 (순수 C#, 테스트 가능). 기획 3단계 '흐르는 낮밤'.
//
// 하루 = 40분: 동틀녘 2 → 낮 14 → 해질녘 2 → 밤 22 (길이는 Balance 의 CLOCK_*). 넘기기·시한·강제 귀환 없음. 시계는 그냥 흐른다.
// 숫자 시계 대신 하늘색·해 그림자·종소리로 알린다 → 이 클래스는 '하늘 밝기(Daylight)'와 '단계가 바뀌는 순간' 을 내 준다.
// 달: 하루가 쌓일 때마다 7일 주기로 돈다. 보름(가운데 날)엔 혼이 강하고 기억이 길게, 그믐(첫날)엔 덩어리가 많다(효과는 쓰는 쪽이 정함).
// =============================================================================
using System;

namespace Chasa.Core
{
    public enum ClockPhase { Dawn, Day, Dusk, Night }

    public class WorldClock
    {
        public float Speed = 1f;                 // 배속(검사용 10배속 등). 1 이 실제 속도
        public int Day;                          // 지난 하루 수
        public float Minutes = Balance.CLOCK_START_MIN;   // 하루 안의 분 (0 ~ 하루 길이)
        public ClockPhase Phase { get; private set; }
        /// <summary>단계가 막 바뀐 프레임에 새 단계가 들어 있다(종소리·알림용). 쓴 쪽이 Consume 으로 비운다</summary>
        public ClockPhase? Changed;

        public static float DayLength { get { return Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + Balance.CLOCK_DUSK_MIN + Balance.CLOCK_NIGHT_MIN; } }

        public WorldClock() { Phase = PhaseAt(Minutes); }
        /// <summary>시작 시각(하루 안의 분)을 정해 만든다 (검사·저장 불러오기용)</summary>
        public WorldClock(float startMinutes) { Minutes = startMinutes; Phase = PhaseAt(Minutes); }

        /// <summary>하루 안의 분 → 단계 (동틀녘이 0분에서 시작)</summary>
        public static ClockPhase PhaseAt(float minutes)
        {
            float m = Wrap(minutes);
            if (m < Balance.CLOCK_DAWN_MIN) return ClockPhase.Dawn;
            m -= Balance.CLOCK_DAWN_MIN;
            if (m < Balance.CLOCK_DAY_MIN) return ClockPhase.Day;
            m -= Balance.CLOCK_DAY_MIN;
            if (m < Balance.CLOCK_DUSK_MIN) return ClockPhase.Dusk;
            return ClockPhase.Night;
        }

        static float Wrap(float minutes)
        {
            float len = DayLength;
            float m = minutes % len;
            return m < 0f ? m + len : m;
        }

        /// <summary>
        /// 하늘 밝기 0(한밤)~1(한낮). 동틀녘엔 0→1 로 올라가고 해질녘엔 1→0 으로 내려간다. 부드럽게(SmoothStep) 변해 눈에 갑작스럽지 않다.
        /// </summary>
        public static float DaylightAt(float minutes)
        {
            float m = Wrap(minutes);
            float dawn = Balance.CLOCK_DAWN_MIN, day = Balance.CLOCK_DAY_MIN, dusk = Balance.CLOCK_DUSK_MIN;
            if (m < dawn) return Smooth(m / dawn);
            m -= dawn;
            if (m < day) return 1f;
            m -= day;
            if (m < dusk) return 1f - Smooth(m / dusk);
            return 0f;
        }
        static float Smooth(float t) { t = Math.Max(0f, Math.Min(1f, t)); return t * t * (3f - 2f * t); }

        public float Daylight { get { return DaylightAt(Minutes); } }
        /// <summary>하루 중 위치 0~1 (시각 고리용)</summary>
        public float DayFraction { get { return Wrap(Minutes) / DayLength; } }
        /// <summary>해질녘·동틀녘처럼 하늘이 붉은 구간인가</summary>
        public bool Reddish { get { return Phase == ClockPhase.Dawn || Phase == ClockPhase.Dusk; } }

        /// <summary>달의 날 0 ~ MOON_DAYS-1. 0 = 그믐, 가운데 = 보름</summary>
        public int MoonDay { get { return ((Day % (int)Balance.MOON_DAYS) + (int)Balance.MOON_DAYS) % (int)Balance.MOON_DAYS; } }
        public bool FullMoon { get { return MoonDay == (int)Balance.MOON_DAYS / 2; } }
        public bool NewMoon { get { return MoonDay == 0; } }

        /// <summary>실제 초(dt)만큼 시계를 흘린다. 하루가 넘으면 Day 가 오른다</summary>
        public void Tick(float dt)
        {
            Minutes += dt * Speed / 60f;
            float len = DayLength;
            while (Minutes >= len) { Minutes -= len; Day++; }
            var p = PhaseAt(Minutes);
            if (p != Phase) { Phase = p; Changed = p; }
        }

        public ClockPhase? Consume() { var c = Changed; Changed = null; return c; }

        public static string PhaseName(ClockPhase p)
        {
            switch (p) { case ClockPhase.Dawn: return "동틀녘"; case ClockPhase.Day: return "낮"; case ClockPhase.Dusk: return "해질녘"; default: return "밤"; }
        }
    }

    /// <summary>지금 하늘 밝기(0~1)를 여러 곳(등불·햇빛)이 같이 읽는 공유값. 시계가 없는 모드에선 0(밤)으로 둔다</summary>
    public static class SkyState { public static float Daylight; }
}
