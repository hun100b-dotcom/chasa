// =============================================================================
// CoreRules.cs — 엔진과 무관한 '규칙 계산' 모음 (순수 C#, UnityEngine 을 쓰지 않는다)
//
// 왜 따로 두나? 화면(Unity)과 규칙(숫자 계산)이 섞이면 테스트하려고 게임을 켜야 한다.
// 규칙만 이 폴더에 두면 Unity 를 화면 없이 돌려(batchmode) 자동 검사할 수 있다.
// 모든 숫자는 Balance.cs(= data/balance.json 에서 자동 생성)에서만 가져온다.
// =============================================================================
using System;

namespace Chasa.Core
{
    public static class CoreRules
    {
        /// <summary>업 단계. 0 = K-001(0~9), 1 = K-002, 2 = K-003, 3 = K-004</summary>
        public static int KarmaTier(int karma)
        {
            if (karma >= Balance.KARMA_TIER_3) return 3;
            if (karma >= Balance.KARMA_TIER_2) return 2;
            if (karma >= Balance.KARMA_TIER_1) return 1;
            return 0;
        }

        /// <summary>보상 배율. K-003(30+)부터 -10%</summary>
        public static float RewardMult(int karma)
        {
            return KarmaTier(karma) >= 2 ? 1.0f - Balance.KARMA_REWARD_PENALTY : 1.0f;
        }

        /// <summary>
        /// 천도 캐스팅 시간. 연속이면 짧고, 보정(+/-초)을 받아도 CAST_MIN_TIME 아래로는 내려가지 않는다.
        /// 왜 하한? 보정이 겹쳐 0초에 가까워지면 천도가 항상 정답이 되고 연쇄 악용이 생긴다.
        /// </summary>
        public static float CastTime(bool chained, float bonus = 0f)
        {
            float t = (chained ? Balance.TENDO_CHAIN_CAST_TIME : Balance.TENDO_CAST_TIME) + bonus;
            return Math.Max(Balance.CAST_MIN_TIME, t);
        }

        /// <summary>장비의 캐스팅 배율(CastMult)까지 반영한 천도 시간. 배율을 곱한 뒤에도 하한은 지킨다</summary>
        public static float CastTimeScaled(bool chained, float mult, float bonus = 0f)
        {
            float t = (chained ? Balance.TENDO_CHAIN_CAST_TIME : Balance.TENDO_CAST_TIME) * mult + bonus;
            return Math.Max(Balance.CAST_MIN_TIME, t);
        }

        /// <summary>결말 A(최종 눕히기) 가능한가: 기억 충분 + 업이 낮아야 한다</summary>
        public static bool EndingAOpen(int memory, int karma)
        {
            return memory >= Balance.ENDING_A_MEMORY_MIN && karma < Balance.ENDING_A_KARMA_MAX;
        }

        /// <summary>B-20 풀어내기 가능: 기억한 이름 수 R 이 물막이 크기 S 의 일정 비율 이상</summary>
        public static bool ReleaseOk(float remembered, float damSize)
        {
            if (damSize <= 0f) return true;
            return remembered / damSize >= Balance.RELEASE_RATIO_MIN;
        }

        /// <summary>B-23 풀기 가능: 이번 막 눕힌 백 수 또는 누적 천도 수가 기준 이상</summary>
        public static bool B23ReleaseOk(int baekLaid, int totalTendo)
        {
            return baekLaid >= Balance.B23_RELEASE_BAEK_MIN || totalTendo >= Balance.B23_RELEASE_TENDO_MIN;
        }

        /// <summary>B-31 일곱의 빛 개수: 보낸 사람 수 / 40, 최소 1 최대 7</summary>
        public static int B31LightCount(int sentPeople)
        {
            int n = sentPeople / Balance.B31_LIGHT_PER_SENT;
            return Math.Min(Balance.B31_LIGHT_MAX, Math.Max(1, n));
        }

        /// <summary>덩어리 백 파혼 업: 몸당 0.1, 덩어리 하나당 상한 3 (몸당 +1이면 40몸에 업 +40이 된다)</summary>
        public static float LumpPahonKarma(int bodies)
        {
            return Math.Min(Balance.LUMP_PAHON_KARMA_CAP, bodies * Balance.LUMP_PAHON_KARMA_PER_BODY);
        }

        /// <summary>이동 둔화 여러 개가 겹칠 때: 곱하지 않고 합산하되 상한(35%)을 둔다. 반환값 = 속도 배율</summary>
        public static float StackedSpeedMult(params float[] slows)
        {
            float sum = 0f;
            foreach (var s in slows) sum += s;
            return 1.0f - Math.Min(sum, Balance.SLOW_STACK_MAX);
        }

        /// <summary>보상 장비 면적 증가율: 반경 r 이 add 만큼 늘면 면적은 ((r+add)/r)^2 - 1</summary>
        public static float AreaGain(float radius, float add)
        {
            float k = (radius + add) / radius;
            return k * k - 1.0f;
        }
    }
}
