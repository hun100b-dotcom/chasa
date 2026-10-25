// =============================================================================
// Boss.cs — 보스 목록과 보스전 바닥 무늬 규칙 (순수 C#, 테스트 가능). 기획 부록 E·서사 보스 컷신 근거.
//   1호 나루 영감(물막이 골)  2호 월화(폐당집 굿판)  3호 서 의원(역병막 마당)
// 화면(붉은 예고 바닥 그리기·피해 주기)은 BossArena(Unity)가 맡고, 여기서는 "어느 칸이 터지나, 약점이 열렸나"만 정한다.
// 수치는 모두 data/balance.json (B02_*, B03_*, BOSS_S2_*). 자리 좌표는 아트가 확정한 장소(npc_places_act1)에서 가져온 임시값.
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public class BossDef
    {
        public int Id;                        // 1·2·3
        public string Name, Cut, CluePrefix;  // 이름 / 컷신 접두어("B02") / 단서 접두어("B02-")
        public float X, Z;                    // 자리(필드 절대 좌표, 동 +x · 북 +z)
        public float Maedhim;                 // 맺힘(체력)
        public float Speed;                   // 이동 속도 배율(1호 기준 0.6)
        public int Damage;                    // 몸으로 부딪는 한 방
        public string Model;                  // 그림/모델 이름(3D 표 키)
    }

    public static class Bosses
    {
        public static BossDef Get(int id)
        {
            switch (id)
            {
                case 2: return new BossDef { Id = 2, Name = "월화", Cut = "B02", CluePrefix = "B02-", X = 580f, Z = 521f, Maedhim = Balance.BOSS_S2_MAEDHIM, Speed = 0.5f, Damage = 22, Model = "boss_b02" };
                case 3: return new BossDef { Id = 3, Name = "서 의원", Cut = "B03", CluePrefix = "B03-", X = 46f, Z = 453f, Maedhim = Balance.B03_BOSS_MAEDHIM, Speed = 0.15f, Damage = 24, Model = "boss_b03" };
                // 2막 보스(기획 act2_map boss_arenas 좌표 · 맺힘 임시값은 balance B05~B08). 전투 규칙은 Core/Act2Boss.cs
                // 4호 흑월 차사 1차(1막 끝, ② 무덤골 임시 자리): 처결이 없다. 맺힘 50%에서 사슬을 거두고 물러난다(JudgeSystem.TickHeukwol)
                case 4: return new BossDef { Id = 4, Name = "흑월", Cut = "B04", CluePrefix = "B04-", X = 110f, Z = 585f, Maedhim = Balance.B04_MAEDHIM, Speed = 0.5f, Damage = (int)Balance.B04_DAMAGE, Model = "boss_b12_heugwol_b04" };
                case 5: return new BossDef { Id = 5, Name = "기수 대돌", Cut = "B05", CluePrefix = "B05-", X = 125f, Z = 1018f, Maedhim = Balance.B05_MAEDHIM, Speed = 0.5f, Damage = Balance.B05_DAMAGE, Model = "boss_b05_daedol2" };
                case 6: return new BossDef { Id = 6, Name = "이름 없는 장수", Cut = "B06", CluePrefix = "B06-", X = 245f, Z = 1138f, Maedhim = Balance.B06_MAEDHIM, Speed = 0.4f, Damage = Balance.B06_DAMAGE, Model = "boss_b06_jangsu" };
                case 7: return new BossDef { Id = 7, Name = "갱도 반장 칠성", Cut = "B07", CluePrefix = "B07-", X = 705f, Z = 1192f, Maedhim = Balance.B07_MAEDHIM, Speed = 0.5f, Damage = Balance.B07_DAMAGE, Model = "boss_b07_chilseong" };
                case 8: return new BossDef { Id = 8, Name = "장부꾼 염씨", Cut = "B08", CluePrefix = "B08-", X = 505f, Z = 952f, Maedhim = Balance.B08_MAEDHIM, Speed = 0.3f, Damage = Balance.B08_DAMAGE, Model = "boss_b08_yeom" };
                default: return new BossDef { Id = 1, Name = "나루 영감", Cut = "B01", CluePrefix = "B01-", X = FieldRules.BossX, Z = FieldRules.BossZ, Maedhim = Balance.BOSS_S1_MAEDHIM, Speed = Balance.BOSS_S1_SPEED_MULT, Damage = Balance.BOSS_S1_DAMAGE, Model = "boss_naru" };
            }
        }
        public const int Count = 3;
    }

    /// <summary>월화 '열두 거리': 잔 열두 개 중 몇 개의 앞 바닥이 열리나. 엎어진 열두째(11번) 잔은 절대 열리지 않는다(늘 안전한 자리)</summary>
    public static class TwelveStreets
    {
        public const int SafeCup = 11;
        public static List<int> Pick(Func<float> rand, int n)
        {
            var pool = new List<int>();
            for (int i = 0; i < Balance.B02_CUPS; i++) if (i != SafeCup) pool.Add(i);
            var res = new List<int>();
            while (res.Count < n && pool.Count > 0)
            {
                int k = Math.Min(pool.Count - 1, (int)(rand() * pool.Count));
                res.Add(pool[k]); pool.RemoveAt(k);
            }
            return res;
        }
        /// <summary>맺힘이 절반 이하면 2국면: 한 번에 더 많이 열린다</summary>
        public static int CupsPerWave(float maedhimRatio) { return maedhimRatio <= 0.5f ? Balance.B02_CUPS_PER_WAVE_P2 : Balance.B02_CUPS_PER_WAVE; }
    }

    /// <summary>서 의원 '번호 부르기': 5×5 칸 중 일부가 터진다. 안전 칸은 늘 칸 수−터지는 수 이상 남는다</summary>
    public static class NumberGrid
    {
        public static bool[] Pick(Func<float> rand, int cells, int bad)
        {
            var res = new bool[cells];
            var idx = new List<int>(); for (int i = 0; i < cells; i++) idx.Add(i);
            for (int n = 0; n < bad && idx.Count > 0; n++)
            {
                int k = Math.Min(idx.Count - 1, (int)(rand() * idx.Count));
                res[idx[k]] = true; idx.RemoveAt(k);
            }
            return res;
        }
    }

    /// <summary>서 의원 약점 창: 파동을 연달아 피하면 약장 서랍이 열린다. 열린 동안만 제대로 아프다</summary>
    public class WeakWindow
    {
        public int Streak;                 // 연속으로 안 맞은 파동 수
        public float OpenLeft;             // 열려 있는 남은 시간(초)
        public bool Open { get { return OpenLeft > 0f; } }

        /// <summary>파동 하나가 끝났다. 맞았으면 연속이 끊긴다. 열려 있는 동안엔 세지 않는다</summary>
        public void WaveResolved(bool playerHit)
        {
            if (Open) return;
            if (playerHit) { Streak = 0; return; }
            if (++Streak >= Balance.B03_WEAK_STREAK) { Streak = 0; OpenLeft = Balance.B03_WEAK_TIME; }
        }
        public void Tick(float dt) { if (OpenLeft > 0f) OpenLeft = Math.Max(0f, OpenLeft - dt); }
        public float DamageMult { get { return Open ? Balance.B03_WEAK_DMG_MULT : Balance.B03_CLOSED_DMG_MULT; } }
    }
}
