// =============================================================================
// SoulTypes.cs — 필드 혼 3유형(넋두리·잔넋·묻힌 혼)의 규칙. 엔진 없는 순수 C# (테스트 가능). 수치는 모두 balance.json(SOULTYPE_*, 임시).
//   혼 4등급(갓/한나절/묵은/뭉친)은 '색·세기', 유형은 '몸·행동'. 유형 × 등급이 한 마리를 이룬다.
//   넋두리 wail  : 멀리서 원념을 던진다. 7~9m 거리를 지키고 가까우면 물러난다.
//   잔넋  mote   : 작은 무리. 약하고 빠르고 따끔. 대장을 처결하면 나머지가 2초 혼란.
//   묻힌 혼 buried: 평소 땅속. 4.5m 안에 들면 땅이 갈라지고(예고) 솟아 붙잡는다. 공격 뒤 묻혀 6초 뒤 다시 매복.
// =============================================================================
using System;

namespace Chasa.Core
{
    public enum SoulType { Plain, Wail, Mote, Buried }

    public static class SoulTypeRules
    {
        /// <summary>구역 이름 → (잔넋%, 넋두리%, 묻힌 혼%). 나머지는 보통 혼. 기획서 부록 F-1b 의 구역별 비율(임시)</summary>
        static void Ratios(string zone, out float mote, out float wail, out float buried)
        {
            mote = wail = buried = 0f;
            if (zone == null) return;
            if (zone.Contains("솔고개")) { mote = Balance.SOULTYPE_SOLGOGAE_MOTE_PCT; wail = Balance.SOULTYPE_SOLGOGAE_WAIL_PCT; buried = Balance.SOULTYPE_SOLGOGAE_BURIED_PCT; }
            else if (zone.Contains("보릿들")) { mote = Balance.SOULTYPE_BORIT_MOTE_PCT; wail = Balance.SOULTYPE_BORIT_WAIL_PCT; buried = Balance.SOULTYPE_BORIT_BURIED_PCT; }
            else if (zone.Contains("물막이 골")) { mote = Balance.SOULTYPE_MULMAGI_MOTE_PCT; wail = Balance.SOULTYPE_MULMAGI_WAIL_PCT; buried = Balance.SOULTYPE_MULMAGI_BURIED_PCT; }
            else if (zone.Contains("폐당집")) { mote = Balance.SOULTYPE_PYEDANG_MOTE_PCT; wail = Balance.SOULTYPE_PYEDANG_WAIL_PCT; buried = Balance.SOULTYPE_PYEDANG_BURIED_PCT; }
            else if (zone.Contains("검은여울")) { mote = Balance.SOULTYPE_RAPIDS_MOTE_PCT; wail = Balance.SOULTYPE_RAPIDS_WAIL_PCT; buried = Balance.SOULTYPE_RAPIDS_BURIED_PCT; }
        }

        /// <summary>구역과 난수(0~1)로 군집 유형을 정한다(군집 하나가 한 유형: 잔넋은 무리, 나머지는 섞이지 않게)</summary>
        public static SoulType Pick(string zone, float roll)
        {
            float m, w, b; Ratios(zone, out m, out w, out b);
            float r = roll * 100f;
            if (r < m) return SoulType.Mote;
            if (r < m + w) return SoulType.Wail;
            if (r < m + w + b) return SoulType.Buried;
            return SoulType.Plain;
        }

        public static float TypeHp(SoulType t) { return t == SoulType.Wail ? Balance.SOULTYPE_WAIL_HP : t == SoulType.Mote ? Balance.SOULTYPE_MOTE_HP : 1f; }

        /// <summary>등급 배율: 한나절 ×1.15, 묵은 맺힘 ×1.6, 갓·뭉친 1</summary>
        public static float GradeHp(SoulKind k) { return k == SoulKind.Year ? Balance.SOULGRADE_YEAR_MULT : k == SoulKind.Old ? Balance.SOULGRADE_OLD_HP : 1f; }
        public static float GradeSpeed(SoulKind k) { return k == SoulKind.Old ? Balance.SOULGRADE_OLD_SPEED : 1f; }
        public static float GradeDamage(SoulKind k) { return k == SoulKind.Year ? Balance.SOULGRADE_YEAR_MULT : k == SoulKind.Lump ? Balance.SOULGRADE_LUMP_DAMAGE : 1f; }

        /// <summary>유형의 기본 피해(보통 혼은 ENEMY_ATTACK_DAMAGE) × 등급</summary>
        public static int Damage(SoulType t, SoulKind k)
        {
            float b = t == SoulType.Wail ? Balance.SOULTYPE_WAIL_DAMAGE : t == SoulType.Mote ? Balance.SOULTYPE_MOTE_DAMAGE : t == SoulType.Buried ? Balance.SOULTYPE_BURIED_DAMAGE : Balance.ENEMY_ATTACK_DAMAGE;
            return Math.Max(1, (int)Math.Round(b * GradeDamage(k)));
        }

        public static int Maedhim(SoulType t, SoulKind k, int baseMaedhim)
        {
            return Math.Max(1, (int)Math.Round(baseMaedhim * TypeHp(t) * GradeHp(k)));
        }

        public static float Speed(SoulType t, SoulKind k) { return (t == SoulType.Mote ? Balance.SOULTYPE_MOTE_SPEED : 1f) * GradeSpeed(k); }

        /// <summary>천도할 수 있는 몸인가? 묻힌 혼은 솟아 있는 동안만 맞고 처결할 수 있다(땅속이면 불가)</summary>
        public static bool Reachable(SoulType t, BuriedPhase ph) { return t != SoulType.Buried || ph == BuriedPhase.Up || ph == BuriedPhase.Strike; }
    }

    // ---- 넋두리: 거리 지키기 + 던지기 -----------------------------------------
    public class WailAi
    {
        public float Cooldown = Balance.SOULTYPE_WAIL_INTERVAL * 0.5f;   // 처음엔 절반만 기다리고 던진다
        public float Windup;                                              // 선딜 남은 시간(0=준비 중 아님)
        public bool Winding { get { return Windup > 0f; } }
        public float WindupRatio { get { return Winding ? 1f - Windup / Balance.SOULTYPE_WAIL_WINDUP : 0f; } }

        /// <summary>이동 방향: +1 다가온다, -1 물러난다, 0 서 있는다. 가까우면 천천히 물러나고, 너무 멀면 다가온다</summary>
        public static int MoveDir(float dist)
        {
            if (dist < Balance.SOULTYPE_WAIL_KEEP_MIN_M) return -1;
            if (dist > Balance.SOULTYPE_WAIL_KEEP_MAX_M) return 1;
            return 0;
        }

        /// <summary>한 프레임. 선딜이 끝나는 순간 true(탄을 쏜다). 시야 밖이면 준비하지 않는다</summary>
        public bool Tick(float dt, float dist, bool canAct)
        {
            if (!canAct) { Interrupt(); return false; }
            if (Winding)
            {
                Windup -= dt;
                if (Windup > 0f) return false;
                Windup = 0f; Cooldown = Balance.SOULTYPE_WAIL_INTERVAL;
                return true;
            }
            Cooldown -= dt;
            if (Cooldown <= 0f && dist <= Balance.SOULTYPE_WAIL_SIGHT_M) Windup = Balance.SOULTYPE_WAIL_WINDUP;
            return false;
        }

        /// <summary>맞으면 선딜이 끊기고 간격이 처음부터(때리는 쪽이 이득)</summary>
        public void Interrupt() { if (Windup > 0f) Cooldown = Balance.SOULTYPE_WAIL_INTERVAL; Windup = 0f; }
    }

    // ---- 묻힌 혼: 매복 상태머신 -------------------------------------------------
    public enum BuriedPhase { Hidden, Windup, Up, Strike, Sink }

    public class BuriedAi
    {
        public BuriedPhase Phase = BuriedPhase.Hidden;
        public float T;                      // 현재 단계에서 흐른 시간
        float rebury;                        // 다시 매복 가능해질 때까지 남은 시간
        const float SinkS = 0.5f;            // 묻히는 동작 길이(아트 Sink 30f)
        const float UpHoldS = 0.4f;          // 솟은 뒤 공격 전까지 잠깐(맞설 틈)

        /// <summary>한 프레임. 솟구침이 끝나 공격이 닿는 순간 true(범위 안이면 피해). dist=플레이어와의 거리</summary>
        public bool Tick(float dt, float dist)
        {
            T += dt;
            switch (Phase)
            {
                case BuriedPhase.Hidden:
                    rebury -= dt;
                    if (rebury <= 0f && dist <= Balance.SOULTYPE_BURIED_TRIGGER_M) { Phase = BuriedPhase.Windup; T = 0f; }
                    break;
                case BuriedPhase.Windup:   // 땅이 갈라지는 예고. 이 동안은 아직 맞지 않는다(회피 창)
                    if (T >= Balance.SOULTYPE_BURIED_WINDUP) { Phase = BuriedPhase.Up; T = 0f; }
                    break;
                case BuriedPhase.Up:       // 솟아 있다: 때리고 처결할 수 있다
                    if (T >= UpHoldS) { Phase = BuriedPhase.Strike; T = 0f; return true; }
                    break;
                case BuriedPhase.Strike:
                    if (T >= Balance.SOULTYPE_BURIED_STRIKE_S) { Phase = BuriedPhase.Sink; T = 0f; }
                    break;
                case BuriedPhase.Sink:
                    if (T >= SinkS) { Phase = BuriedPhase.Hidden; T = 0f; rebury = Balance.SOULTYPE_BURIED_REBURY_S; }
                    break;
            }
            return false;
        }

        /// <summary>범위 판정: 솟은 자리 반지름 + 몸 여유 안에 있나</summary>
        public static bool InStrike(float dist) { return dist <= Balance.SOULTYPE_BURIED_RADIUS_M + 0.3f; }
    }
}
