// =============================================================================
// DayRun.cs — 낮 한 번의 규칙 (순수 C#, 기획서 부록 B)
// 낮은 '시간'이 아니라 해 그림자 눈금 3개로 잰다. 단서 동사(엿듣기·지켜보기·만져 보기)를 성공할 때마다 1눈금.
// 이동·장례 목격·서낭당 시설은 눈금을 쓰지 않는다. 눈금 3개로는 보스 단서 셋과 이름혼 찾기를 다 못 하니
// 낮에도 "보스를 쫓을까, 이름혼을 찾을까" 선택이 생긴다.
// 업이 높으면 산 사람이 귀를 닫는다: 10 반쪽 문장·원 좁아짐 / 30 보스 엿듣기 닫힘 / 60 마을 소문 전부 닫힘.
// 업이 내려가면 닫힌 단서도 다시 열린다 (매번 현재 업으로 판정하므로 따로 처리할 것이 없다).
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public enum ClueVerb { Eavesdrop, Watch, Touch }        // 엿듣기 / 지켜보기 / 만져 보기
    public enum SpotKind { BossClue, Rumor, NamedHouse }    // 보스 단서 / 보스와 상관없는 마을 소문 / 제사 집(이름혼 위치)
    public enum SpotAccess { Open, Done, Closed }           // 할 수 있음 / 이미 함 / 업 때문에 닫힘
    public enum DayPhase { Day, Dusk }                      // 낮 / 해 질 녘(밤으로 넘어감)

    /// <summary>낮 지도의 단서 자리 하나</summary>
    public class ClueSpot
    {
        public string Id;
        public ClueVerb Verb;
        public SpotKind Kind;
        public bool HumanSpeech;   // 사람 말이 들어간 단서인가 (업 10 이상이면 반쪽 문장이 된다)
        public bool Done;
    }

    /// <summary>동사 하나를 실제로 수행하는 중. 화면은 매 프레임 Tick 에 '자리까지의 거리'를 넘긴다</summary>
    public class ClueAction
    {
        public ClueSpot Spot;
        public float Need;       // 필요한 시간(초)
        public float Radius;     // 이 거리 안에 있어야 한다 (m)
        public float Progress;   // 모인 시간(초)
        public bool Half;        // 반쪽 문장으로 기록될 단서인가
        public bool Completed;

        /// <summary>
        /// dt 초가 흘렀고 자리까지 dist m. 엿듣기·지켜보기는 원 밖으로 나가면 처음부터(기획: 끊김).
        /// 만져 보기는 끊기지 않고 그동안만 멈춘다(기획: 낮은 안전하다). 다 모이면 true
        /// </summary>
        public bool Tick(float dt, float dist)
        {
            if (Completed) return true;
            if (dist > Radius) { if (Spot.Verb != ClueVerb.Touch) Progress = 0f; return false; }
            Progress += dt;
            if (Progress >= Need) { Completed = true; return true; }
            return false;
        }
    }

    public class DayRun
    {
        public int TicksLeft = Balance.DAY_TICKS;
        public DayPhase Phase = DayPhase.Day;
        public readonly List<ClueSpot> Spots = new List<ClueSpot>();
        public int BossClues;            // 오늘 얻은 보스 단서 수
        public int HalfClues;            // 그중 반쪽 문장인 것
        public bool NamedHouseWatched;   // 제사 집을 지켜봐서 이름혼 위치가 명부에 올랐다
        public bool FuneralAvailable;    // 어젯밤 이름혼을 천도해서 장례가 열렸다
        public float FuneralWatched;     // 본 시간(초)
        public bool FuneralDone;         // 끝까지 봤다 (두루마리에서 다시 볼 수 있음)
        public float EmptyDayTimer;      // 할 것이 없는 낮의 안내 표시 시간

        public DayRun(bool namedTendoLastNight) { FuneralAvailable = namedTendoLastNight; }

        /// <summary>현재 업에서 이 자리를 쓸 수 있나</summary>
        public SpotAccess Access(ClueSpot s, int karma)
        {
            if (s.Done) return SpotAccess.Done;
            if (s.Kind == SpotKind.Rumor && karma >= Balance.KARMA_EAR_ALL_CLOSED) return SpotAccess.Closed;      // 60+: 마을이 텅 빔
            if (s.Kind == SpotKind.BossClue && s.Verb == ClueVerb.Eavesdrop && karma >= Balance.KARMA_EAR_BOSS_CLOSED) return SpotAccess.Closed;   // 30+: 보스 엿듣기 닫힘
            return SpotAccess.Open;
        }

        /// <summary>엿듣기 원 반경. 업 10 이상이면 좁아진다</summary>
        public static float EarRadius(int karma)
        {
            return karma >= Balance.KARMA_EAR_HALF ? Balance.EAVESDROP_RADIUS_EAR : Balance.EAVESDROP_RADIUS;
        }

        /// <summary>눈금이 남아 있고 열려 있으면 동작을 시작한다. 아니면 null (눈금은 성공해야 줄어든다)</summary>
        public ClueAction Begin(ClueSpot s, int karma)
        {
            if (Phase != DayPhase.Day || TicksLeft <= 0 || Access(s, karma) != SpotAccess.Open) return null;
            var a = new ClueAction { Spot = s };
            switch (s.Verb)
            {
                case ClueVerb.Eavesdrop: a.Need = Balance.EAVESDROP_TIME; a.Radius = EarRadius(karma); break;
                case ClueVerb.Watch: a.Need = Balance.WATCH_TIME; a.Radius = Balance.WATCH_RADIUS; break;
                default: a.Need = Balance.TOUCH_TIME; a.Radius = Balance.TOUCH_RADIUS; break;
            }
            a.Half = s.HumanSpeech && karma >= Balance.KARMA_EAR_HALF;   // 업 10+: 사람 말이 든 단서는 반쪽 문장
            return a;
        }

        /// <summary>동작이 끝났을 때 한 번 부른다. 눈금 1을 쓰고 결과(보스 단서·제사 집)를 반영. 눈금이 다 닳으면 해 질 녘</summary>
        public void Complete(ClueAction a)
        {
            if (!a.Completed || a.Spot.Done || TicksLeft <= 0) return;
            a.Spot.Done = true;
            TicksLeft--;
            if (a.Spot.Kind == SpotKind.BossClue) { BossClues++; if (a.Half) HalfClues++; }
            else if (a.Spot.Kind == SpotKind.NamedHouse) NamedHouseWatched = true;
            if (TicksLeft <= 0) Phase = DayPhase.Dusk;
        }

        /// <summary>장례를 본다 (눈금 0). 70초를 다 채우면 true. 건너뛰어도 된다</summary>
        public bool WatchFuneral(float dt)
        {
            if (!FuneralAvailable || FuneralDone) return FuneralDone;
            FuneralWatched += dt;
            if (FuneralWatched >= Balance.FUNERAL_TIME) FuneralDone = true;
            return FuneralDone;
        }

        /// <summary>장례를 건너뛴다: 두루마리에 이름 한 줄만 남는다(다시 볼 수 없음). 열린 장례는 사라진다</summary>
        public void SkipFuneral() { FuneralAvailable = false; }

        /// <summary>해 넘기기: 눈금이 남아 있어도 해 질 녘으로. 건너뛴 눈금은 이야기로 대가를 치른다(단서가 모자람)</summary>
        public void SkipToDusk() { Phase = DayPhase.Dusk; }

        /// <summary>
        /// 할 것이 없는 낮인가: 지금 업에서 쓸 수 있는 단서 자리도, 볼 장례도 없다.
        /// 이때 화면은 "오늘 낮엔 들을 것이 없다"를 EMPTY_DAY_TIME 초 보여 주고 해 질 녘으로 넘어간다
        /// </summary>
        public bool NothingToDo(int karma)
        {
            if (FuneralAvailable && !FuneralDone) return false;
            foreach (var s in Spots) if (Access(s, karma) == SpotAccess.Open) return false;
            return true;
        }

        /// <summary>
        /// 보스 천도에 쓸 단서 수. 낮에 얻은 것 + 이미 가진 것(단서는 사라지지 않는다). 반쪽 문장도 1개로 센다
        /// </summary>
        public int TotalBossClues(int alreadyHave) { return alreadyHave + BossClues; }
    }
}
