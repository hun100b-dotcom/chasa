// =============================================================================
// DodgeRules.cs — 피하기(구르기)의 규칙 숫자 계산 (순수 C#, 테스트 가능). 값은 balance.json(DODGE_*).
// Player 는 이 함수를 불러 쓰기만 한다 → 무적 구간·충전·3타 후딜 제한을 유니티 없이 검사할 수 있다.
// =============================================================================
using System;

namespace Chasa.Core
{
    public static class DodgeRules
    {
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
