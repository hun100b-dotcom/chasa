// =============================================================================
// GearPlan.cs — 장비 7칸·등급·인(印) 시스템의 규칙 뼈대 (순수 C#, 테스트 가능). 기획서 6-3·6-6, 성장 곡선 점검(10-25) 근거.
// 지금 화면(DayScreen·CharacterPanel)과 저장은 옛 3칸(무기·도포·노리개)이라, 여기는 '규칙만' 먼저 둔다:
//   · EquipLayout  — 8자리(무기 2·갓·도포·띠·신·노리개 2)와 열리는 때, 칸별 인 홈 수
//   · RingLoot     — 고리(1~6)별 드롭 등급 확률. 고리는 위치로 정한다
//   · SoulColor/SoulWallet/Seal — 오방색 넋을 모아 작은 인(300)·큰 인(900)을 만든다. 인 15종 = 한 빛깔 5 + 두 빛깔 조합 10
// 왜 옛 코드를 안 바꾸나: 화면·저장이 3칸에 묶여 있어 한 번에 바꾸면 되돌릴 수 없는 저장 호환 문제가 생긴다.
//   규칙이 테스트로 굳은 뒤에 화면·저장을 새 자리로 옮긴다(다음 일).
// 수치 원본은 data/balance.json (RING*_DROP_*_PCT, SEAL_*).
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    /// <summary>장비 자리 8개. (기획서는 '칸 일곱'이라 부르지만 무기·노리개가 둘씩이라 자리는 여덟이다)</summary>
    public enum EquipPos { Weapon1, Weapon2, Hat, Robe, Belt, Shoes, Charm1, Charm2 }

    public static class EquipLayout
    {
        /// <summary>
        /// 그 자리가 열렸나. 시작: 무기 둘·도포·노리개 1. 1막 보스 B-01·B-02 중 하나 처결 뒤: 갓·띠. 2막 진입: 신·노리개 2.
        /// </summary>
        public static bool IsOpen(EquipPos p, bool firstRingBossDone, bool act2Entered)
        {
            switch (p)
            {
                case EquipPos.Hat: case EquipPos.Belt: return firstRingBossDone || act2Entered;
                case EquipPos.Shoes: case EquipPos.Charm2: return act2Entered;
                default: return true;
            }
        }

        /// <summary>인 홈을 가질 수 있는 자리인가(무기·갓·도포만. 띠·신·노리개는 없다)</summary>
        public static bool CanHoldSeal(EquipPos p) { return p == EquipPos.Weapon1 || p == EquipPos.Weapon2 || p == EquipPos.Hat || p == EquipPos.Robe; }

        /// <summary>자리와 등급으로 본 인 홈 수: 흔한 0 · 손본 1 · 귀한 2 (이름 있는 물건은 귀한과 같다)</summary>
        public static int SealSlots(EquipPos p, Rarity r, bool named)
        {
            if (!CanHoldSeal(p)) return 0;
            if (named || r == Rarity.Rare) return Balance.SEAL_SLOTS_RARE;
            return r == Rarity.Crafted ? Balance.SEAL_SLOTS_CRAFTED : 0;
        }
    }

    public static class RingLoot
    {
        /// <summary>그 고리에서 이 등급이 나올 확률(0~1). 고리는 1~6, 범위 밖은 가장자리로 붙인다</summary>
        public static float Chance(int ring, Rarity r)
        {
            switch (Math.Max(1, Math.Min(6, ring)))
            {
                case 1: return Pct(r, Balance.RING1_DROP_COMMON_PCT, Balance.RING1_DROP_CRAFTED_PCT, Balance.RING1_DROP_RARE_PCT);
                case 2: return Pct(r, Balance.RING2_DROP_COMMON_PCT, Balance.RING2_DROP_CRAFTED_PCT, Balance.RING2_DROP_RARE_PCT);
                case 3: return Pct(r, Balance.RING3_DROP_COMMON_PCT, Balance.RING3_DROP_CRAFTED_PCT, Balance.RING3_DROP_RARE_PCT);
                case 4: return Pct(r, Balance.RING4_DROP_COMMON_PCT, Balance.RING4_DROP_CRAFTED_PCT, Balance.RING4_DROP_RARE_PCT);
                case 5: return Pct(r, Balance.RING5_DROP_COMMON_PCT, Balance.RING5_DROP_CRAFTED_PCT, Balance.RING5_DROP_RARE_PCT);
                default: return Pct(r, Balance.RING6_DROP_COMMON_PCT, Balance.RING6_DROP_CRAFTED_PCT, Balance.RING6_DROP_RARE_PCT);
            }
        }
        static float Pct(Rarity r, float common, float crafted, float rare) { return (r == Rarity.Common ? common : r == Rarity.Crafted ? crafted : rare) / 100f; }

        /// <summary>난수 x(0~1)로 등급을 고른다: 귀한부터 위에서 자른다(고리가 올라갈수록 귀한 쪽 띠가 넓어진다)</summary>
        public static Rarity RarityAt(int ring, float x)
        {
            float rare = Chance(ring, Rarity.Rare), crafted = Chance(ring, Rarity.Crafted);
            return x < rare ? Rarity.Rare : x < rare + crafted ? Rarity.Crafted : Rarity.Common;
        }

        /// <summary>
        /// 위치로 본 고리. ① 솔고개·보릿들·물막이 골·폐당집=1, ② 검은여울=2, ③ 붉은재=3, ④ 쇳골=4, ⑤ 갯마을=5, ⑥ 도성=6.
        /// 2막 ③④는 x 360 을 경계로 가른다(BgmPlayer.RegionKeyAt 과 같은 선). blackRiver: 지금 있는 구역이 검은여울인가.
        /// </summary>
        public static int RingAt(float x, float z, bool blackRiver)
        {
            if (x >= FieldRules.Size + 128f) return 5;
            if (x < 0f) return 6;
            if (z >= FieldRules.Size) return x < 360f ? 3 : 4;
            return blackRiver ? 2 : 1;
        }
    }

    /// <summary>넋 오방색: 청 · 황 · 흑 · 적 · 백</summary>
    public enum SoulColor { Blue, Yellow, Black, Red, White }

    /// <summary>
    /// 인 하나. 빛깔 두 개(같을 수도 있다)와 크기. 인 15종 = 한 빛깔 5 + 두 빛깔 조합 10 (순서 무관).
    /// </summary>
    public class Seal
    {
        public SoulColor A, B;       // A &lt;= B 로 정리해 둔다(순서가 달라도 같은 인)
        public bool Large;
        public Seal(SoulColor a, SoulColor b, bool large)
        {
            if ((int)a <= (int)b) { A = a; B = b; } else { A = b; B = a; }
            Large = large;
        }
        public bool Mono { get { return A == B; } }
        public string Key { get { return (Large ? "L" : "S") + (int)A + (int)B; } }
        /// <summary>만드는 데 드는 넋 합계(작은 300·큰 900)</summary>
        public int TotalCost { get { return Large ? Balance.SEAL_LARGE_NEOK : Balance.SEAL_SMALL_NEOK; } }
        /// <summary>그 빛깔에서 드는 넋: 두 빛깔이면 반반, 한 빛깔이면 전부</summary>
        public int CostOf(SoulColor c) { return Mono ? (c == A ? TotalCost : 0) : (c == A || c == B ? TotalCost / 2 : 0); }

        /// <summary>인 종류 전부(15종 × 크기)</summary>
        public static List<Seal> AllKinds(bool large)
        {
            var l = new List<Seal>();
            for (int a = 0; a < 5; a++) for (int b = a; b < 5; b++) l.Add(new Seal((SoulColor)a, (SoulColor)b, large));
            return l;
        }
    }

    /// <summary>빛깔별 넋 주머니. 그 구역 혼을 천도해야 그 빛깔이 쌓인다(어느 구역 혼을 보낼지가 빌드 선택)</summary>
    public class SoulWallet
    {
        public readonly int[] Amount = new int[5];
        public int Get(SoulColor c) { return Amount[(int)c]; }
        public void Add(SoulColor c, int n) { if (n > 0) Amount[(int)c] += n; }
        public bool CanAfford(Seal s) { for (int i = 0; i < 5; i++) if (Amount[i] < s.CostOf((SoulColor)i)) return false; return true; }
        /// <summary>인을 만든다. 모자라면 null (아무것도 깎지 않는다)</summary>
        public Seal Craft(SoulColor a, SoulColor b, bool large)
        {
            var s = new Seal(a, b, large);
            if (!CanAfford(s)) return null;
            for (int i = 0; i < 5; i++) Amount[i] -= s.CostOf((SoulColor)i);
            return s;
        }
    }

    /// <summary>장비 하나에 박힌 인들. 홈 수를 넘겨 박을 수 없다</summary>
    public class SealSet
    {
        public readonly List<Seal> Placed = new List<Seal>();
        public int Capacity;
        public SealSet(int capacity) { Capacity = capacity; }
        public bool Insert(Seal s) { if (s == null || Placed.Count >= Capacity) return false; Placed.Add(s); return true; }
        public bool Remove(int index) { if (index < 0 || index >= Placed.Count) return false; Placed.RemoveAt(index); return true; }
    }
}
