// =============================================================================
// Growth.cs — 성장 뼈대 (순수 C#, 테스트 가능). 기획 6절: 품계(레벨)·능력치 4종·도술 세 갈래.
//
// 품계: 쌓인 넋으로 오르고 잃지 않는다(1~50). 품계가 오를 때 도술 점수 1점 + 능력치 5점, 보스를 천도하면 도술 점수 1점.
// 능력치: 힘·날램·몸·마음, 시작은 각 10. 점수는 자유롭게 나눠 쓴다.
// 도술: 부름(천도)·줄(싸움)·얼룩(파혼) 세 갈래. 갈래를 섞어도 되고, '깊은 도술'은 그 갈래에 10점 이상 넣어야 열린다.
//       패시브는 두 단계(+1/+2), 액티브는 한 번 배운다. 액티브 칸은 넷.
// 수치는 모두 임시값(기획서: 모든 숫자는 임시값). 효과를 게임에 연결하는 것은 다음 일 — 여기서는 '쓰는 규칙'만 지킨다.
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public enum Branch { Call, Chain, Stain }   // 부름 / 줄 / 얼룩

    public class SkillNode
    {
        public string Name; public Branch Branch; public bool Active, Deep; public string Desc;
        public int MaxLevel { get { return Active ? 1 : 2; } }
        public SkillNode(string name, Branch b, bool active, string desc, bool deep = false) { Name = name; Branch = b; Active = active; Desc = desc; Deep = deep; }
    }

    public static class SkillTree
    {
        public const int DeepNeeds = 10;     // 깊은 도술을 열려면 그 갈래에 넣어야 하는 점수
        public const int ActiveSlots = 4;    // 액티브 칸(PC 1~4)

        public static readonly SkillNode[] All =
        {
            // 부름 갈래 (천도 쪽)
            new SkillNode("붙잡아 부르기", Branch.Call, true, "6m 안 무릎 꿇은 혼 대기 +3초 · 혼 0.8초 멈칫 (12초)"),
            new SkillNode("혼불 날리기", Branch.Call, true, "혼불을 던진다 · 피해 8 × 그날 천도한 수+1 (최대 5)"),
            new SkillNode("이름 비추기", Branch.Call, true, "다음 천도 시전 −0.25초 (8초)"),
            new SkillNode("배웅길", Branch.Call, true, "천도 직후 3초 동안 적 이동 -30%"),
            new SkillNode("오래 부르기", Branch.Call, false, "연속 천도 창 +1/+2초"),
            new SkillNode("고마운 넋", Branch.Call, false, "천도 넋 +6/+12%"),
            new SkillNode("곁을 지킴", Branch.Call, false, "천도 중 받는 피해 −10/−20%"),
            new SkillNode("몫을 채움", Branch.Call, false, "그날 명부 몫을 채우면 이동 속도 +8%"),
            new SkillNode("일곱 이름", Branch.Call, true, "연속 천도 7회째 다음 천도는 하한 0.5초로 끝난다", true),
            // 줄 갈래 (싸움·제어)
            new SkillNode("휘감기", Branch.Chain, true, "4m 안 혼 1.5초 묶기 (8초)"),
            new SkillNode("여럿 끌기", Branch.Chain, true, "적 셋을 한꺼번에 끌어온다 (8초)"),
            new SkillNode("매듭 걸음", Branch.Chain, true, "사슬을 걸어 8m 돌진, 지나는 동안 피격 없음 (7초)"),
            new SkillNode("한 줄 꿰기", Branch.Chain, true, "무릎 꿇은 혼 둘을 한 줄로 묶어 함께 천도 또는 함께 파혼"),
            new SkillNode("단단한 손", Branch.Chain, false, "공격 속도 +8/+16%"),
            new SkillNode("긴 사슬", Branch.Chain, false, "무기 사거리 +0.4/+0.8m"),
            new SkillNode("묶인 자", Branch.Chain, false, "묶인 적이 받는 맺힘 피해 +30%"),
            new SkillNode("손에 익음", Branch.Chain, false, "지금 든 무기 계열의 특성 하나 강화"),
            new SkillNode("쇠사슬 울", Branch.Chain, true, "반경 5m 원 안의 적 3초 고정 (20초)", true),
            // 얼룩 갈래 (파혼 쪽)
            new SkillNode("터뜨리기", Branch.Stain, true, "가까운 얼룩 하나를 터뜨려 없앤다 · 2.5m 피해 30 · 업은 그대로 (9초)"),
            new SkillNode("원념 두르기", Branch.Stain, true, "5초 동안 업 단계만큼 공격 +5/10/15/20% (10초)"),
            new SkillNode("얼룩 타기", Branch.Stain, true, "6초간 얼룩 위에서 둔화 대신 이동 +15%"),
            new SkillNode("깨진 이름 던지기", Branch.Stain, true, "방금 파혼한 혼의 파편을 던져 원거리 피해 (8초마다)"),
            new SkillNode("큰 폭발", Branch.Stain, false, "파혼 반경 +0.2/+0.4m (합계 상한 안)"),
            new SkillNode("세찬 넉백", Branch.Stain, false, "파혼 넉백 +20/+40%"),
            new SkillNode("노잣돈", Branch.Stain, false, "파혼 엽전 +7/+14%"),
            new SkillNode("마른 얼룩", Branch.Stain, false, "얼룩 지속 -15/-30%"),
            new SkillNode("검은 갓의 그림자", Branch.Stain, true, "10초간 파혼 폭발이 주변 무릎 꿇은 혼까지 깨뜨린다. 깨진 혼마다 업 +1", true),
        };

        public static SkillNode Find(string name) { foreach (var s in All) if (s.Name == name) return s; return null; }
        public static string BranchName(Branch b) { return b == Branch.Call ? "부름" : b == Branch.Chain ? "줄" : "얼룩"; }
    }

    public class GrowthState
    {
        public const int MaxRank = 50;
        public const int StatPerRank = 7;      // 품계 한 번 오를 때 능력치 점수(기획 성장 곡선 10-25: 5→7. 품계가 느려져도 천도가 파혼에 안 밀리게)
        public const int StatBase = 10;        // 능력치 시작값
        public static readonly string[] StatNames = { "힘", "날램", "몸", "마음" };

        public int Rank = 1;
        public int TotalNeok;                              // 지금까지 쌓은 넋(잃지 않는다)
        public int SkillPointsEarned, SkillPointsSpent;
        public int StatPointsEarned;
        public int PahonCount, StainPointsEarned, StainPointsSpent;   // 파혼 횟수 / 얼룩 갈래 전용 도술 점수(파혼 15회마다 1)
        public readonly int[] Stats = { StatBase, StatBase, StatBase, StatBase };
        public readonly Dictionary<string, int> Learned = new Dictionary<string, int>();
        public readonly List<string> ActiveBar = new List<string>();   // 배운 액티브 중 칸에 올린 것(최대 4)

        /// <summary>시작 상태(기획): 옛 고정 도술 셋 = 각 갈래의 첫 액티브가 공짜로 배워져 1·2·3칸에 끼워져 있다</summary>
        public GrowthState()
        {
            foreach (var n in new[] { "붙잡아 부르기", "휘감기", "터뜨리기" }) { Learned[n] = 1; ActiveBar.Add(n); }
        }

        /// <summary>배운 액티브를 칸에 올리고 내린다(칸은 넷까지). 바뀌었으면 true</summary>
        public bool ToggleBar(string name)
        {
            var s = SkillTree.Find(name);
            if (s == null || !s.Active || LevelOf(name) < 1) return false;
            if (ActiveBar.Remove(name)) return true;
            if (ActiveBar.Count >= SkillTree.ActiveSlots) return false;
            ActiveBar.Add(name); return true;
        }

        /// <summary>그 품계에 닿기까지 필요한 누적 넋(기획 성장 곡선 10-25). 2품계 75, 10품계 6075, 20품계 27075, 40품계 114075, 50품계 180075. 밤 22분 기준 시즌 1 끝이 약 20품계</summary>
        public static int NeokForRank(int rank)
        {
            if (rank <= 1) return 0;
            return (int)Math.Round(75.0 * (rank - 1) * (rank - 1));
        }

        public static int RankFor(int totalNeok)
        {
            int r = 1;
            while (r < MaxRank && totalNeok >= NeokForRank(r + 1)) r++;
            return r;
        }

        /// <summary>넋을 얻었다. 품계가 오른 만큼(여러 단계도 가능)을 돌려준다. 오를 때마다 도술 점수 1·능력치 7점</summary>
        public int AddNeok(int amount)
        {
            if (amount <= 0) return 0;
            TotalNeok += amount;
            int newRank = RankFor(TotalNeok), ups = newRank - Rank;
            if (ups > 0) { Rank = newRank; SkillPointsEarned += ups; StatPointsEarned += ups * StatPerRank; }
            return Math.Max(0, ups);
        }

        /// <summary>보스를 천도하면 도술 점수 1</summary>
        public void AddBossPoint() { SkillPointsEarned++; }

        /// <summary>파혼 한 번. PAHON_STAIN_POINT_EVERY 번째마다 얼룩 갈래 전용 점수 1을 주고 true (파혼만 해도 성장 길이 열리게)</summary>
        public bool AddPahon()
        {
            PahonCount++;
            if (PahonCount % Balance.PAHON_STAIN_POINT_EVERY != 0) return false;
            StainPointsEarned++; return true;
        }

        public int StainPointsFree { get { return StainPointsEarned - StainPointsSpent; } }

        public int SkillPointsFree { get { return SkillPointsEarned - SkillPointsSpent; } }
        public int StatPointsFree { get { return StatPointsEarned - SpentStatPoints(); } }
        int SpentStatPoints() { int s = 0; foreach (var v in Stats) s += v - StatBase; return s; }

        /// <summary>능력치 한 점 올리기. 남은 점수가 없으면 false</summary>
        public bool AddStat(int index)
        {
            if (index < 0 || index >= Stats.Length || StatPointsFree <= 0) return false;
            Stats[index]++; return true;
        }

        /// <summary>그 갈래에 넣은 도술 점수(배운 단계의 합)</summary>
        public int BranchPoints(Branch b)
        {
            int n = 0;
            foreach (var kv in Learned) { var s = SkillTree.Find(kv.Key); if (s != null && s.Branch == b) n += kv.Value; }
            return n;
        }

        public int LevelOf(string name) { int l; return Learned.TryGetValue(name, out l) ? l : 0; }

        /// <summary>배울 수 있나 (점수·최고 단계·깊은 도술 조건)</summary>
        public bool CanLearn(string name)
        {
            var s = SkillTree.Find(name);
            if (s == null || LevelOf(name) >= s.MaxLevel) return false;
            if (SkillPointsFree <= 0 && !(s.Branch == Branch.Stain && StainPointsFree > 0)) return false;   // 얼룩 도술은 전용 점수로도 배운다
            if (s.Deep && BranchPoints(s.Branch) < SkillTree.DeepNeeds) return false;
            return true;
        }

        public bool Learn(string name)
        {
            if (!CanLearn(name)) return false;
            var s = SkillTree.Find(name);
            Learned[name] = LevelOf(name) + 1;
            if (s.Branch == Branch.Stain && StainPointsFree > 0) StainPointsSpent++; else SkillPointsSpent++;   // 전용 점수를 먼저 쓴다
            if (s.Active && ActiveBar.Count < SkillTree.ActiveSlots) ActiveBar.Add(name);   // 칸이 비어 있으면 바로 올린다
            return true;
        }
    }

    /// <summary>
    /// 성장(능력치 점수 + 배운 패시브)을 장비 합계(GearStats)에 얹는다. 상한(CAP_*)은 GearStats 가 그대로 지킨다.
    /// 이어진 것: 힘·날램·몸·마음, 패시브 12종(몫을 채움만 JudgeSystem 이 명부 조건으로 따로 처리). 아직 안 이은 것: 몫을 채움(명부 조건)·긴 사슬(사거리)·묶인 자·손에 익음·마른 얼룩, 액티브 전부.
    /// </summary>
    public static class GrowthEffects
    {
        public static void Apply(GrowthState g, GearStats s)
        {
            if (g == null) return;
            int str = g.Stats[0] - GrowthState.StatBase, agi = g.Stats[1] - GrowthState.StatBase,
                body = g.Stats[2] - GrowthState.StatBase, mind = g.Stats[3] - GrowthState.StatBase;
            s.DamagePct += str * Balance.GROWTH_DAMAGE_PER_STR;
            s.AttackSpeedPct += agi * Balance.GROWTH_ATKSPD_PER_AGI;
            s.MoveSpeedPct += agi * Balance.GROWTH_MOVE_PER_AGI;
            s.HpFlat += body * Balance.GROWTH_HP_PER_BODY;
            s.CastReducePct += mind * Balance.GROWTH_CAST_PER_MIND;
            s.TendoNeokPct += mind * Balance.GROWTH_NEOK_PER_MIND;
            // 패시브(단계 1/2): 도술 설명문의 수치 그대로
            s.ChainWindowAddS += 1f * g.LevelOf("오래 부르기");
            s.TendoNeokPct += 0.06f * g.LevelOf("고마운 넋");
            s.CastDamageReducePct += 0.10f * g.LevelOf("곁을 지킴");
            s.AttackSpeedPct += 0.08f * g.LevelOf("단단한 손");
            s.PahonRadiusM += 0.2f * g.LevelOf("큰 폭발");
            s.PahonKnockbackPct += 0.2f * g.LevelOf("세찬 넉백");
            s.PahonCoinPct += 0.07f * g.LevelOf("노잣돈");
            s.ReachAdd += 0.4f * g.LevelOf("긴 사슬");
            s.BoundBonus += 0.30f * g.LevelOf("묶인 자");
            s.StainShorten += 0.15f * g.LevelOf("마른 얼룩");
            s.DamagePct += 0.05f * g.LevelOf("손에 익음");   // 근사: '무기 계열 특성 하나 강화'가 정해지기 전까지 피해 +5%/+10%
        }
    }
}

namespace Chasa.Core
{
    /// <summary>액티브 도술의 재사용 대기(이름으로 찾는다). 수치는 balance.json 의 ACD_* / SKILL_*_COOLDOWN (임시값)</summary>
    public class ActiveCooldowns
    {
        readonly System.Collections.Generic.Dictionary<string, float> left = new System.Collections.Generic.Dictionary<string, float>();

        public static float Cooldown(string name)
        {
            switch (name)
            {
                case "붙잡아 부르기": return Balance.SKILL_HOLD_COOLDOWN;
                case "휘감기": return Balance.SKILL_BIND_COOLDOWN;
                case "터뜨리기": return Balance.SKILL_BURST_COOLDOWN;
                case "혼불 날리기": return Balance.ACD_SOULFIRE;
                case "이름 비추기": return Balance.ACD_NAMELIGHT;
                case "배웅길": return Balance.ACD_ESCORT;
                case "일곱 이름": return Balance.ACD_SEVEN;
                case "여럿 끌기": return Balance.ACD_MULTIPULL;
                case "매듭 걸음": return Balance.ACD_KNOTDASH;
                case "한 줄 꿰기": return Balance.ACD_TIE;
                case "쇠사슬 울": return Balance.ACD_CAGE;
                case "원념 두르기": return Balance.ACD_WRATH;
                case "얼룩 타기": return Balance.ACD_STAINRIDE;
                case "깨진 이름 던지기": return Balance.ACD_THROWNAME;
                case "검은 갓의 그림자": return Balance.ACD_SHADOW;
                default: return 10f;
            }
        }

        public float Left(string name) { float v; return left.TryGetValue(name, out v) ? v : 0f; }
        public bool Ready(string name) { return Left(name) <= 0f; }
        public float Ratio(string name) { float l = Left(name); return l <= 0f ? 0f : l / Cooldown(name); }
        public bool Start(string name) { if (!Ready(name)) return false; left[name] = Cooldown(name); return true; }

        public void Tick(float dt)
        {
            var keys = new System.Collections.Generic.List<string>(left.Keys);
            foreach (var k in keys) { float v = left[k] - dt; if (v <= 0f) left.Remove(k); else left[k] = v; }
        }
    }
}
