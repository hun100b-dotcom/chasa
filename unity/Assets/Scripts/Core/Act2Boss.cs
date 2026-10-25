// =============================================================================
// Act2Boss.cs — 2막 보스 4종(B-05 기수 대돌 · B-06 이름 없는 장수 · B-07 갱도 반장 칠성 · B-08 장부꾼 염씨)의
// "언제 어떤 공격을 하나" 상태머신 뼈대 (순수 C#, 테스트 가능). 기획 act2-souls §4(부록 E 사양) 근거.
// 수치는 모두 data/balance.json 의 B05_~B08_* (임시값 — 기획 확정값이 오면 json 만 고친다).
// 화면(예고 바닥 그리기·피해 주기·병사 소환)은 이 뼈대를 읽는 쪽이 맡고, 여기서는 "다음 행동이 무엇인가"만 정한다.
// 왜 이렇게: 1~3호는 BossArena 안에 화면 코드와 섞여 있어 시험이 어렵다. 2막은 규칙을 먼저 분리해 두고 화면을 붙인다.
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public enum BossAct
    {
        None,
        // B-05
        CallNames, FlagPlant, FlagSwing, PoleCharge,
        // B-06
        LineForm, CraneForm, CircleForm,
        // B-07
        PickSwing, RockFall,
        // B-08
        NumberMines, AbacusSweep, LedgerFlip,
        // B-09 망부석 아낙 · B-10 만선호 선장 · B-11 다리 밑 왕초 · B-12 흑월 2차 (3막, Core/Act3Boss.cs)
        WaveRows, CallSea, ClothThrow,
        RopeCut, RopeWrap, RopeCross,
        MatThrow, StaffSwing,
        MirrorPull, HisPahon, NameLines, Flood
    }

    /// <summary>보스가 지금 하려는 행동 하나. Warn 초 뒤에 터진다(예고 동안 화면이 붉은 무늬를 그린다)</summary>
    public struct BossMove
    {
        public BossAct Act;
        public float Warn;      // 예고 시간(초)
        public float Radius;    // 반경(m, 해당 없으면 0)
        public int Count;       // 개수(낙석·병사·지뢰 등)
        public float Param;     // 행동별 보조값(진법 폭, 원진 시작 반경 등)
        public bool Fast;       // B-06 50% 이후 '빠른 호령'(대형 둘 연속)
    }

    public class Act2Brain
    {
        public readonly int BossId;
        readonly Func<float> rand;
        public float Maedhim, MaedhimMax;        // 현재/최대 맺힘(화면 쪽이 갱신해 주고, 여기서는 비율만 읽는다)
        public float Stun;                       // 이 시간 동안 아무것도 안 한다(약점 보상으로 멈춤)
        public float Frenzy;                     // B-07 광폭 남은 시간
        public bool Phase2 { get { return MaedhimMax > 0f && Maedhim / MaedhimMax <= 0.5f; } }
        float cdA, cdB, cdC;                     // 패턴별 다음까지 남은 시간
        float numT;                              // B-05 번호 비율이 오르는 시계
        int formIdx;                             // B-06 진법 순번
        int queued;                              // B-06 빠른 호령: 이어서 한 번 더
        public int NumberSharePct;               // B-05 지금 번호 병사 비율(%)
        public bool FlagPlanted;                 // B-05 깃발 꽂힘(50% 뒤 한 번, 견인으로 뽑으면 false)
        public int MinersOut, PapersStepped;     // B-07 나간 광부 수 / B-08 밟은 이름 종이 수
        public int Soldiers;                     // B-05 지금 살아 있는 소환 병사 수(화면 쪽이 갱신)
        public float ArenaRadius;                // B-07 막장 반경(14→10으로 좁아진다)

        public Act2Brain(int bossId, Func<float> rand)
        {
            BossId = bossId; this.rand = rand;
            switch (bossId)
            {
                case 5: MaedhimMax = Balance.B05_MAEDHIM; NumberSharePct = (int)Balance.B05_NUM_START_PCT; cdA = Balance.B05_CALL_INTERVAL; cdB = Balance.B05_SWING_GAP; cdC = Balance.B05_CHARGE_GAP; break;
                case 6: MaedhimMax = Balance.B06_MAEDHIM; cdA = Balance.B06_FORM_GAP; break;
                case 7: MaedhimMax = Balance.B07_MAEDHIM; cdA = Balance.B07_PICK_GAP; cdB = Balance.B07_ROCK_GAP; ArenaRadius = Balance.B07_ARENA_START; break;
                case 8: MaedhimMax = Balance.B08_MAEDHIM; cdA = Balance.B08_MINE_GAP; cdB = Balance.B08_SWEEP_GAP; cdC = Balance.B08_LEDGER_GAP; break;
                default: throw new ArgumentException("2막 보스 번호는 5~8");
            }
            Maedhim = MaedhimMax;
        }

        public int Damage { get { return BossId == 5 ? Balance.B05_DAMAGE : BossId == 6 ? Balance.B06_DAMAGE : BossId == 7 ? Balance.B07_DAMAGE : Balance.B08_DAMAGE; } }
        /// <summary>B-07 광폭이면 간격이 짧아진다(임시 ×0.6)</summary>
        float Rate { get { return Frenzy > 0f ? 0.6f : 1f; } }

        // ---- 약점·보상 신호 (화면 쪽이 일이 일어날 때 부른다) -----------------------------------
        /// <summary>B-05: 이름으로 불린 병사를 천도했다 → 보스가 멈춘다</summary>
        public void OnCalledSoulTendo() { if (BossId == 5) Stun = Math.Max(Stun, Balance.B05_CALLED_STUN); }
        /// <summary>B-05: 깃발을 견인으로 뽑았다</summary>
        public void OnFlagPulled() { FlagPlanted = false; }
        /// <summary>B-07: 광부 혼 하나가 출구로 나갔다. 다섯이 모일 때마다 멈춘다</summary>
        public void OnMinerExit() { if (BossId != 7) return; if (++MinersOut % Balance.B07_MINERS == 0) Stun = Math.Max(Stun, Balance.B07_MINER_STUN); }
        /// <summary>B-07: 광부를 파혼했다 → 보스 맺힘이 늘고(반환값 = 늘어난 양) 10초 광폭</summary>
        public float OnMinerPahon() { if (BossId != 7) return 0f; Frenzy = Balance.B07_FRENZY_SEC; float add = MaedhimMax * Balance.B07_PAHON_LUMP_PCT / 100f; Maedhim = Math.Min(MaedhimMax, Maedhim + add); return add; }
        /// <summary>B-08: 이름 종이를 밟았다. 맺힘 −2%(반환값 = 줄어든 양), 세 장째면 웅크린다</summary>
        public float OnNamePaperStepped()
        {
            if (BossId != 8) return 0f;
            float cut = MaedhimMax * -Balance.B08_NAME_SHARE_PCT / 100f; Maedhim = Math.Max(1f, Maedhim - cut);
            if (++PapersStepped % Balance.B08_PAPERS_FOR_CROUCH == 0) Stun = Math.Max(Stun, Balance.B08_CROUCH_SEC);
            return cut;
        }
        /// <summary>B-06: 때린 자리가 대형의 빈 자리면 피해가 커진다</summary>
        public float DamageMultAt(bool inGap) { return BossId == 6 && inGap ? Balance.B06_GAP_DMG_MULT : 1f; }

        /// <summary>한 틱. 새 행동이 있으면 돌려주고(없으면 Act=None), 한 틱에 하나만 낸다</summary>
        public BossMove Tick(float dt)
        {
            if (Frenzy > 0f) Frenzy = Math.Max(0f, Frenzy - dt);
            if (Stun > 0f) { Stun = Math.Max(0f, Stun - dt); return default(BossMove); }
            if (BossId == 5) { numT += dt; while (numT >= Balance.B05_NUM_STEP_SEC) { numT -= Balance.B05_NUM_STEP_SEC; NumberSharePct = Math.Min((int)Balance.B05_NUM_CAP_PCT, NumberSharePct + (int)Balance.B05_NUM_STEP_PCT); } }
            if (BossId == 7) ArenaRadius = Balance.B07_ARENA_START + (Balance.B07_ARENA_END - Balance.B07_ARENA_START) * (float)Math.Min(1.0, 1.0 - Maedhim / MaedhimMax);   // 맺힘이 줄수록 막장이 좁아진다
            cdA -= dt; cdB -= dt; cdC -= dt;
            switch (BossId)
            {
                case 5: return Tick5();
                case 6: return Tick6();
                case 7: return Tick7();
                default: return Tick8();
            }
        }

        BossMove Tick5()
        {
            if (Phase2 && !flagDone) { flagDone = true; FlagPlanted = true; return new BossMove { Act = BossAct.FlagPlant, Radius = Balance.B05_FLAG_RADIUS, Param = Balance.B05_FLAG_ATK_PCT }; }
            if (cdA <= 0f)
            {
                cdA = Balance.B05_CALL_INTERVAL;
                int room = Math.Max(0, Balance.B05_SOLDIER_CAP - Soldiers);   // 보스 자리 상한 4를 넘지 않는다
                int n = Math.Min(Balance.B05_CALL_COUNT, room);
                if (n > 0) return new BossMove { Act = BossAct.CallNames, Count = n, Param = NumberSharePct };
            }
            if (cdB <= 0f) { cdB = Balance.B05_SWING_GAP; return new BossMove { Act = BossAct.FlagSwing, Warn = Balance.B05_SWING_WARN, Radius = Balance.B05_SWING_RADIUS }; }
            if (cdC <= 0f) { cdC = Balance.B05_CHARGE_GAP; return new BossMove { Act = BossAct.PoleCharge, Warn = Balance.B05_CHARGE_WARN, Param = Balance.B05_CHARGE_DIST }; }
            return default(BossMove);
        }
        bool flagDone;

        BossMove Tick6()
        {
            if (queued > 0 && cdB <= 0f) { queued--; return Form(true); }   // 빠른 호령의 두 번째 대형
            if (cdA > 0f) return default(BossMove);
            cdA = Balance.B06_FORM_GAP;
            var m = Form(Phase2);
            if (Phase2) { queued = 1; cdB = m.Warn + 0.3f; }
            return m;
        }
        BossMove Form(bool fast)
        {
            float warn = fast ? Balance.B06_FAST_WARN : Balance.B06_WARN;
            switch (formIdx++ % 3)
            {
                case 0: return new BossMove { Act = BossAct.LineForm, Warn = warn, Param = Balance.B06_LINE_WIDTH, Radius = Balance.B06_LINE_GAP, Fast = fast };
                case 1: return new BossMove { Act = BossAct.CraneForm, Warn = warn, Radius = Balance.B06_CRANE_RADIUS, Fast = fast };
                default: return new BossMove { Act = BossAct.CircleForm, Warn = warn, Radius = Balance.B06_CIRCLE_START, Param = Balance.B06_CIRCLE_END, Fast = fast };
            }
        }

        BossMove Tick7()
        {
            if (cdA <= 0f) { cdA = Balance.B07_PICK_GAP * Rate; return new BossMove { Act = BossAct.PickSwing, Warn = Balance.B07_PICK_WARN, Radius = Balance.B07_PICK_RADIUS }; }
            if (cdB <= 0f) { cdB = Balance.B07_ROCK_GAP * Rate; return new BossMove { Act = BossAct.RockFall, Warn = Balance.B07_ROCK_WARN, Radius = Balance.B07_ROCK_RADIUS, Count = Phase2 ? Balance.B07_ROCK_COUNT_P2 : Balance.B07_ROCK_COUNT }; }
            return default(BossMove);
        }

        BossMove Tick8()
        {
            if (cdA <= 0f) { cdA = Balance.B08_MINE_GAP; return new BossMove { Act = BossAct.NumberMines, Warn = 1.0f, Count = Balance.B08_MINES, Param = Balance.B08_MINE_MULT }; }
            if (cdB <= 0f) { cdB = Balance.B08_SWEEP_GAP; return new BossMove { Act = BossAct.AbacusSweep, Warn = Balance.B08_SWEEP_WARN, Radius = Balance.B08_SWEEP_RADIUS, Param = Balance.B08_SWEEP_ANGLE }; }
            if (Phase2 && cdC <= 0f) { cdC = Balance.B08_LEDGER_GAP; return new BossMove { Act = BossAct.LedgerFlip, Warn = Balance.B08_LEDGER_WARN }; }
            return default(BossMove);
        }

        /// <summary>B-08 숫자 지뢰: 네 칸 중 한 칸은 이름 종이(무해). 어느 칸인지 뽑아 돌려준다</summary>
        public int PickNamePaper() { return Math.Min(Balance.B08_MINES - 1, (int)(rand() * Balance.B08_MINES)); }
    }
}
