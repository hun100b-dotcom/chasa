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
        /// <summary>보스 맺힘 금 단계(개편안 §4): 남은 맺힘 66% 이하 1단계, 33% 이하 2단계, 10% 이하 3단계, 그 위는 0(금 없음). 화면 전용 규칙이라 수치 기둥과 무관</summary>
        public static int GyeolCrackStage(float ratio) { return ratio <= 0.10f ? 3 : ratio <= 0.33f ? 2 : ratio <= 0.66f ? 1 : 0; }

        /// <summary>남은 맺힘 줄 수(개편 P2): 맺힘을 lines 개 줄로 나눠 올림으로 센다. 가득이면 lines, 1 이라도 남으면 1, 0 이면 0.
        /// 예) 최대 900 · 3줄: 900→3, 600→2, 601→3(아직 첫 줄 안 깨짐), 300→1. 줄 경계는 66%·33% 로 화면의 금 단계와 같다</summary>
        public static int LinesLeft(int maedhim, int max, int lines)
        {
            if (max <= 0 || lines <= 1) return maedhim > 0 ? 1 : 0;
            if (maedhim <= 0) return 0;
            if (maedhim >= max) return lines;
            return (int)System.Math.Ceiling((double)maedhim * lines / max - 1e-9);
        }

        /// <summary>파혼 반격(개편안 P1-2): 거센 혼이 기를 모으는 중에, 그 혼이 파혼 폭발 반경 안에 들면 공격이 끊긴다.
        /// 왜 규칙으로 떼나: '파혼이 지금은 정답'인 순간을 화면 코드가 아니라 테스트로 지키려는 것. 반경·피해 수치는 건드리지 않는다.
        /// <paramref name="blastToTarget"/> 폭발 중심에서 거센 혼까지 거리, <paramref name="radius"/> 폭발 반경, <paramref name="targetRadius"/> 거센 혼 몸 반경</summary>
        public static bool PahonInterruptsCharge(bool charging, float blastToTarget, float radius, float targetRadius)
        {
            return charging && blastToTarget <= radius + targetRadius;
        }

        /// <summary>
        /// 폰 처결 대상 고르기(개편안 P1-5, 명세 §5-1): 꿇은 혼이 여럿일 때 어느 혼을 겨눌지.
        /// 조이스틱을 밀고 있으면 '그 방향 60도 안에서 가장 가까운 혼', 아니면(또는 그 방향에 없으면) 그냥 가장 가까운 혼.
        /// 왜 규칙으로 떼나: 천도와 파혼이 둘 다 '같은 혼'을 겨누므로 대상 고르기가 흔들리면 선택이 정답 입력이 된다 — 화면 없이 테스트로 지키려는 것.
        /// <paramref name="px"/>,<paramref name="pz"/> 내 자리, <paramref name="aimX"/>,<paramref name="aimZ"/> 조이스틱 방향(월드 바닥 좌표, 길이 0~1),
        /// <paramref name="xs"/>,<paramref name="zs"/> 후보 혼 자리. 반환 = 후보 번호, 후보가 없으면 -1
        /// </summary>
        public static int PickKneelIndex(float px, float pz, float aimX, float aimZ, float[] xs, float[] zs)
        {
            if (xs == null || xs.Length == 0) return -1;
            float aimLen = (float)Math.Sqrt(aimX * aimX + aimZ * aimZ);
            bool aimed = aimLen >= Balance.KNEEL_AIM_MIN;
            int bestAim = -1, bestAny = -1; float dAim = float.MaxValue, dAny = float.MaxValue;
            for (int i = 0; i < xs.Length; i++)
            {
                float dx = xs[i] - px, dz = zs[i] - pz;
                float d = (float)Math.Sqrt(dx * dx + dz * dz);
                if (d < dAny) { dAny = d; bestAny = i; }
                if (!aimed || d < 1e-4f) continue;
                float cos = (dx * aimX + dz * aimZ) / (d * aimLen);   // 방향이 얼마나 같은가(1 = 정확히 그 쪽)
                if (cos >= Balance.KNEEL_AIM_COS && d < dAim) { dAim = d; bestAim = i; }
            }
            return bestAim >= 0 ? bestAim : bestAny;
        }

        /// <summary>
        /// 보스 등장 카메라의 세기(0~1). 개편안 P1-3 '보스 등장 2초 카메라'.
        /// 전체 길이의 앞 25%는 보스 쪽으로 서서히 움직이고, 가운데 50%는 머물고, 뒤 25%는 플레이어로 돌아온다. 처음·끝은 0 이라 화면이 튀지 않는다
        /// </summary>
        public static float RevealWeight(float elapsed, float total)
        {
            if (total <= 0f || elapsed <= 0f || elapsed >= total) return 0f;
            float u = elapsed / total;
            float w = u < 0.25f ? u / 0.25f : u > 0.75f ? (1f - u) / 0.25f : 1f;
            return w * w * (3f - 2f * w);   // 부드러운 곡선(smoothstep): 시작과 끝에서 속도가 0
        }

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
