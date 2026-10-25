// =============================================================================
// DodgeRules.cs — 피하기(구르기)의 규칙 숫자 계산 (순수 C#, 테스트 가능). 값은 balance.json(DODGE_*).
// Player 는 이 함수를 불러 쓰기만 한다 → 무적 구간·충전·3타 후딜 제한을 유니티 없이 검사할 수 있다.
// =============================================================================
using System;

namespace Chasa.Core
{
    public static class DodgeRules
    {
        /// <summary>
        /// 구르기 클립(Roll 19프레임)의 프레임별 속도(m/s, 아트 _hero_anim_manifest.json Roll.travel.speed_mps_per_frame).
        /// 5.5 에서 시작해 15.2 를 유지하다 5.5 로 끝난다 — 달리기 속도로 시작·끝나서 앞뒤가 이어진다(옛 EaseOut 은 25 m/s 로 튀고 0 으로 멈췄다).
        /// </summary>
        static readonly float[] RollSpeed = { 5.5f, 8.021f, 12.703f, 15.224f, 15.224f, 15.224f, 15.224f, 15.224f, 15.224f, 15.224f, 15.224f, 15.224f, 15.224f, 15.224f, 15.224f, 13.705f, 10.362f, 7.019f, 5.5f };
        static float[] rollCum;

        /// <summary>구르기 t01(0~1 시간)까지 간 거리의 비율(0~1). 속도표를 쌓아 합이 1 이 되게 늘렸다 → 총 거리는 dodgeDistance 그대로</summary>
        public static float RollFraction(float t01)
        {
            if (rollCum == null)
            {
                rollCum = new float[RollSpeed.Length + 1];
                for (int i = 0; i < RollSpeed.Length; i++) rollCum[i + 1] = rollCum[i] + RollSpeed[i];
            }
            float x = Math.Max(0f, Math.Min(1f, t01)) * RollSpeed.Length;
            int f = Math.Min(RollSpeed.Length - 1, (int)x);
            return (rollCum[f] + (x - f) * RollSpeed[f]) / rollCum[RollSpeed.Length];
        }

        /// <summary>피하기 시작 t초 뒤, 맞아도 피해가 없는 무적 구간인가</summary>
        public static bool Invulnerable(float t) { return t >= Balance.DODGE_IFRAME_START && t <= Balance.DODGE_IFRAME_END; }

        /// <summary>충전 회복: 한 번 충전에 DODGE_RECHARGE 초. 최대 DODGE_CHARGES</summary>
        public static float Recharge(float charges, float dt)
        { return Math.Min(Balance.DODGE_CHARGES, charges + dt / Balance.DODGE_RECHARGE); }

        /// <summary>마지막 타(3타) 후딜의 앞쪽 절반은 피할 수 없다(마무리의 대가). progress 0~1 = 후딜 진행률</summary>
        public static bool RecoverAllowsDodge(bool lastStep, float progress)
        { return !(lastStep && progress < Balance.COMBO3_RECOVER_DODGE_LOCK); }

        /// <summary>공격 후딜 진행률(0~1)이 기준을 넘으면 이동 입력으로 끝동작을 끊을 수 있다 (왜: 때린 뒤 굳어 있는 느낌을 줄인다)</summary>
        public static bool CanCancelRecoverToMove(float progress) { return progress >= Balance.MOVE_CANCEL_RECOVER; }

        /// <summary>피하기 중, 공격·처결로 끊을 수 있는 시점인가</summary>
        public static bool CanCancelToAction(float t) { return t >= Balance.DODGE_CANCEL_TO_ATTACK; }
    }
}
