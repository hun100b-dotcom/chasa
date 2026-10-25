// =============================================================================
// Act3Boss.cs — 3막 보스 4종(B-09 망부석 아낙 · B-10 만선호 선장 · B-11 다리 밑 왕초 · B-12 흑월 2차)의
// "언제 어떤 공격을 하나" 상태머신 (순수 C#, 테스트 가능). 기획 부록 E(시즌 1 보스 12종 전투 사양) 근거.
// 수치는 모두 data/balance.json 의 B09_~B12_* (임시값 — 기획 확정값이 오면 json 만 고친다).
// 2막 Act2Brain 과 같은 틀: 이 클래스는 '다음 행동이 무엇인가'만 정하고, 예고 바닥 그리기·피해는 화면 쪽(Act2BossArena)이 맡는다.
// 이번 판에 넣지 않은 것(다음 일): 물 혼이 실린 파도·선원 혼·별명 혼 같은 '혼이 얽힌' 약점 연결, 명단 줄의 초당 넋 감소,
//   큰물의 밀어내기/둔화, 보스 간 숨은 연결(B-10 먼저 천도 → B-09 50% 남편 혼). 지금은 예고 장판과 단계 전환까지다.
// =============================================================================
using System;

namespace Chasa.Core
{
    public class Act3Brain
    {
        public readonly int BossId;
        readonly Func<float> rand;
        public float Maedhim, MaedhimMax;
        public float Stun;                    // 이 시간 동안 아무것도 안 한다(약점 보상으로 멈춤)
        public float ClothWindow;             // B-09: 옷 낚아채기 창이 열려 있는 남은 시간(0 이면 닫힘)
        public bool ClothDone;                // B-09: 옷 던지기 장면이 이미 있었나(1회)
        public bool TorchDone;                // B-12: 큰물 횃불 약점을 이미 썼나(1회)
        float cdA, cdB, cdC;
        bool stage2Said;
        int lineSeq;

        public Act3Brain(int bossId, Func<float> rand)
        {
            BossId = bossId; this.rand = rand;
            switch (bossId)
            {
                case 9: MaedhimMax = Balance.B09_MAEDHIM; cdA = Balance.B09_WAVE_GAP; cdB = Balance.B09_CALL_GAP; break;
                case 10: MaedhimMax = Balance.B10_MAEDHIM; cdA = Balance.B10_ROPE_GAP; cdB = Balance.B10_WRAP_GAP; break;
                case 11: MaedhimMax = Balance.B11_MAEDHIM; cdA = Balance.B11_MAT_GAP; cdB = Balance.B11_STAFF_GAP; break;
                case 12: MaedhimMax = Balance.B12_MAEDHIM; cdA = Balance.B12_PULL_GAP; cdB = Balance.B12_PAHON_GAP; cdC = Balance.B12_LINES_GAP; break;
                default: throw new ArgumentException("3막 보스 번호는 9~12");
            }
            Maedhim = MaedhimMax;
        }

        public int Damage { get { return BossId == 9 ? Balance.B09_DAMAGE : BossId == 10 ? Balance.B10_DAMAGE : BossId == 11 ? Balance.B11_DAMAGE : Balance.B12_DAMAGE; } }
        public float Ratio { get { return MaedhimMax > 0f ? Maedhim / MaedhimMax : 0f; } }
        public bool Phase2 { get { return Ratio <= 0.5f; } }   // B-09·10·11 의 50% 이후
        /// <summary>B-12 단계: 1(100→70%) · 2(70→40%, 명단) · 3(40→15%, 큰물) · 4(15% 이하, 사슬을 내려놓음 = 공격 없음)</summary>
        public int Stage12 { get { float r = Ratio; return r > 0.7f ? 1 : r > 0.4f ? 2 : r > 0.15f ? 3 : 4; } }

        // ---- 약점·보상 신호 (화면 쪽이 일이 일어날 때 부른다) -----------------------------------
        /// <summary>B-09: 옷 던지기 창 안에 사슬로 낚아챘다 → 맺힘 −15%(반환값 = 줄어든 양)</summary>
        public float OnClothCaught()
        {
            if (BossId != 9 || ClothWindow <= 0f) return 0f;
            ClothWindow = 0f; float cut = MaedhimMax * Balance.B09_CLOTH_CUT_PCT / 100f; Maedhim = Math.Max(1f, Maedhim - cut); return cut;
        }
        /// <summary>B-12: 큰물 단계에서 물속 횃불을 사슬로 건졌다 → 3초 멈춘다(1회)</summary>
        public bool OnTorchPulled()
        {
            if (BossId != 12 || TorchDone || Stage12 != 3) return false;
            TorchDone = true; Stun = Math.Max(Stun, Balance.B12_TORCH_STUN); return true;
        }

        /// <summary>한 틱. 새 행동이 있으면 돌려주고(없으면 Act=None), 한 틱에 하나만 낸다</summary>
        public BossMove Tick(float dt)
        {
            if (ClothWindow > 0f) ClothWindow = Math.Max(0f, ClothWindow - dt);
            if (Stun > 0f) { Stun = Math.Max(0f, Stun - dt); return default(BossMove); }
            cdA -= dt; cdB -= dt; cdC -= dt;
            switch (BossId)
            {
                case 9: return Tick9();
                case 10: return Tick10();
                case 11: return Tick11();
                default: return Tick12();
            }
        }

        BossMove Tick9()
        {
            if (Phase2 && !ClothDone)   // 50%: 남편의 옷을 던지려 한다. 창(2초) 동안 다른 공격은 쉰다
            {
                ClothDone = true; ClothWindow = Balance.B09_CLOTH_WINDOW;
                return new BossMove { Act = BossAct.ClothThrow, Warn = Balance.B09_CLOTH_WINDOW };
            }
            if (ClothWindow > 0f) return default(BossMove);
            if (cdA <= 0f) { cdA = Balance.B09_WAVE_GAP; return new BossMove { Act = BossAct.WaveRows, Warn = Balance.B09_WAVE_WARN, Count = Balance.B09_WAVE_ROWS, Radius = Balance.B09_WAVE_WIDTH, Param = Balance.B09_WAVE_STRIDE }; }
            if (cdB <= 0f) { cdB = Balance.B09_CALL_GAP; return new BossMove { Act = BossAct.CallSea, Warn = Balance.B09_CALL_WARN, Radius = Balance.B09_CALL_RADIUS }; }
            return default(BossMove);
        }

        BossMove Tick10()
        {
            if (cdA <= 0f)
            {
                cdA = Balance.B10_ROPE_GAP;
                if (Phase2) return new BossMove { Act = BossAct.RopeCross, Warn = Balance.B10_CROSS_WARN, Param = Balance.B10_ROPE_LEN, Radius = Balance.B10_ROPE_WID, Count = 2 };   // 50% 폭풍: 두 줄 엇갈림
                return new BossMove { Act = BossAct.RopeCut, Warn = Balance.B10_ROPE_WARN, Param = Balance.B10_ROPE_LEN, Radius = Balance.B10_ROPE_WID, Count = 1 };
            }
            if (cdB <= 0f) { cdB = Balance.B10_WRAP_GAP; return new BossMove { Act = BossAct.RopeWrap, Warn = Balance.B10_WRAP_WARN, Radius = Balance.B10_WRAP_RADIUS }; }
            return default(BossMove);
        }

        BossMove Tick11()
        {
            if (cdA <= 0f) { cdA = Balance.B11_MAT_GAP; return new BossMove { Act = BossAct.MatThrow, Warn = Balance.B11_MAT_WARN, Radius = Balance.B11_MAT_RADIUS }; }
            if (cdB <= 0f) { cdB = Balance.B11_STAFF_GAP; return new BossMove { Act = BossAct.StaffSwing, Warn = Balance.B11_STAFF_WARN, Radius = Balance.B11_STAFF_RADIUS, Param = Balance.B11_STAFF_ANGLE }; }
            return default(BossMove);
        }

        BossMove Tick12()
        {
            int st = Stage12;
            if (st == 4) return default(BossMove);   // 사슬을 내려놓고 선다: 더는 공격하지 않는다
            if (cdA <= 0f && st <= 2) { cdA = Balance.B12_PULL_GAP; return new BossMove { Act = BossAct.MirrorPull, Warn = Balance.B12_PULL_WARN, Param = Balance.B12_PULL_LEN, Radius = Balance.B12_PULL_WID }; }
            if (cdB <= 0f && st == 1) { cdB = Balance.B12_PAHON_GAP; return new BossMove { Act = BossAct.HisPahon, Warn = Balance.B12_PAHON_WARN, Radius = Balance.B12_PAHON_RADIUS }; }
            if (cdC <= 0f && st == 2) { cdC = Balance.B12_LINES_GAP; return new BossMove { Act = BossAct.NameLines, Warn = Balance.B12_LINES_WARN, Count = Balance.B12_LINES_ROWS, Radius = Balance.B12_LINES_WID, Param = ++lineSeq }; }
            if (cdA <= 0f && st == 3) { cdA = Balance.B12_FLOOD_GAP; return new BossMove { Act = BossAct.Flood, Warn = Balance.B12_FLOOD_WARN, Radius = Balance.B12_FLOOD_WID, Count = 3 }; }
            return default(BossMove);
        }
    }
}
