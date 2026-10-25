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
        /// <summary>필드 혼 고리 배율(기획 act1-enemy-check, 시뮬 Sim.cs 와 같은 표). 고리 1~6</summary>
        static readonly float[] RingMaedhim = { 1f, 1.2f, 1.4f, 1.7f, 2.0f, 2.3f, 2.6f, 2.9f }, RingDamage = { 1f, 1.15f, 1.3f, 1.5f, 1.7f, 1.9f, 2.1f, 2.3f }, RingReward = { 1f, 1.25f, 1.5f, 1.75f, 2.0f, 2.3f, 2.6f, 2.9f };
        static int Ix(int ring) { return System.Math.Max(0, System.Math.Min(7, ring - 1)); }
        public static float MaedhimMult(int ring) { return RingMaedhim[Ix(ring)]; }
        public static float DamageMult(int ring) { return RingDamage[Ix(ring)]; }
        /// <summary>넋 보상 배율</summary>
        public static float RewardMult(int ring) { return RingReward[Ix(ring)]; }
        /// <summary>엽전 보상 배율: 보상 배율 증가분의 RING_COIN_SHARE(60%)만</summary>
        public static float CoinMult(int ring) { return 1f + (RingReward[Ix(ring)] - 1f) * Balance.RING_COIN_SHARE; }

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
        /// <summary>저장 글자(예: S01). Key 와 같다</summary>
        public string Text { get { return Key; } }
        /// <summary>저장 글자에서 되살린다. 형식이 틀리면 null</summary>
        public static Seal Parse(string t)
        {
            if (t == null || t.Length != 3 || (t[0] != 'S' && t[0] != 'L') || t[1] < '0' || t[1] > '4' || t[2] < '0' || t[2] > '4') return null;
            return new Seal((SoulColor)(t[1] - '0'), (SoulColor)(t[2] - '0'), t[0] == 'L');
        }
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

    /// <summary>인 15종의 이름과 효과(기획 A-4). 큰 인은 효과 2배. 값은 임시(기획 수치표 확정 시 갱신)</summary>
    public static class SealEffects
    {
        public static string Name(Seal s)
        {
            string n = Key(s);
            string name = n == "00" ? "날랜 인" : n == "33" ? "센 인" : n == "11" ? "굳은 인" : n == "44" ? "쇠 인" : n == "22" ? "깊은 인"
                : n == "03" ? "서두름 인" : n == "01" ? "길 인" : n == "04" ? "바람 인" : n == "02" ? "물길 인" : n == "13" ? "불씨 인"
                : n == "34" ? "칼끝 인" : n == "23" ? "그을음 인" : n == "14" ? "버팀 인" : n == "12" ? "무덤 인" : "찬 인";
            return (s.Large ? "큰 " : "") + name;
        }
        static string Key(Seal s) { return (int)s.A + "" + (int)s.B; }
        /// <summary>효과 한 줄 설명</summary>
        public static string Describe(Seal s)
        {
            string n = Key(s); int m = s.Large ? 2 : 1;
            switch (n)
            {
                case "00": return "공격 속도 +" + 6 * m + "%";
                case "33": return "맺힘 피해 +" + 8 * m + "%";
                case "11": return "생명 +" + 30 * m;
                case "44": return "방어 +" + 6 * m + "%";
                case "22": return "도술 재사용 -" + 8 * m + "%";
                case "03": return "연속 천도 창 +" + m + "초 · 천도 넋 +" + 4 * m + "%";
                case "01": return "이동 속도 +" + 5 * m + "%";
                case "04": return "무기 기술 재사용 -" + 10 * m + "%";
                case "02": return "천도 시전 -" + 6 * m + "% · 천도 넋 +" + 4 * m + "%";
                case "13": return "파혼 피해 +" + 15 * m + "% · 파혼 엽전 +" + 2 * m + "%";
                case "34": return "사나운 적·덩어리 피해 +" + 12 * m + "%";
                case "23": return "얼룩 지속 -" + 20 * m + "% · 파혼 엽전 +" + 3 * m + "%";
                case "14": return "천도 중 받는 피해 -" + 15 * m + "% · 천도 넋 +" + 4 * m + "%";
                case "12": return "처결 대기 시간 +" + m + "초";
                default: return "파혼 넉백 +" + 30 * m + "% · 파혼 엽전 +" + 3.5f * m + "%";
            }
        }
        public static void Apply(Seal s, GearStats g)
        {
            float m = s.Large ? 2f : 1f;
            switch (Key(s))
            {
                case "00": g.AttackSpeedPct += 0.06f * m; break;
                case "33": g.DamagePct += 0.08f * m; break;
                case "11": g.HpFlat += (int)(30 * m); break;
                case "44": g.DefensePct += 0.06f * m; break;
                case "22": g.SkillCdReduce += 0.08f * m; break;
                case "03": g.ChainWindowAddS += 1f * m; g.TendoNeokPct += 0.04f * m; break;   // 기울기 인은 덧줄(기획 인 점검 4): 천도 셋 합 11.2% · 파혼 셋 합 11.0%
                case "01": g.MoveSpeedPct += 0.05f * m; break;
                case "04": g.WeaponCdReduce += 0.10f * m; break;
                case "02": g.CastReducePct += 0.06f * m; g.TendoNeokPct += 0.04f * m; break;
                case "13": g.PahonDamagePct += 0.15f * m; g.PahonCoinPct += 0.02f * m; break;
                case "34": g.FiercePct += 0.12f * m; break;
                case "23": g.StainShorten += 0.20f * m; g.PahonCoinPct += 0.03f * m; break;
                case "14": g.CastDamageReducePct += 0.15f * m; g.TendoNeokPct += 0.04f * m; break;
                case "12": g.WaitAddS += 1f * m; break;
                default: g.PahonKnockbackPct += 0.30f * m; g.PahonCoinPct += 0.035f * m; break;
            }
        }
        /// <summary>인을 장비 홈에 끼운다(홈이 비어 있고 그 자리가 인을 받을 수 있을 때)</summary>
        public static bool Insert(ItemDef it, EquipPos pos, Seal s)
        {
            if (it == null || s == null || !EquipLayout.CanHoldSeal(pos) || it.Seals.Count >= it.Sockets) return false;
            it.Seals.Add(s); return true;
        }
    }

    /// <summary>구역 이름 → 그 구역 혼의 넋 빛깔(기획 A-4: 죽은 자리·까닭). 모르는 구역은 청(산·고개)</summary>
    public static class SoulColors
    {
        public static SoulColor ForZone(string zone)
        {
            string z = zone ?? "";
            if (z.Contains("붉은재") || z.Contains("검은여울") || z.Contains("역병")) return SoulColor.Red;      // 싸움·불·역병
            if (z.Contains("보릿들") || z.Contains("쇳골") || z.Contains("갱")) return SoulColor.Yellow;          // 밭·흙·광산
            if (z.Contains("물막이") || z.Contains("갯마을") || z.Contains("삼도천") || z.Contains("강")) return SoulColor.Black;   // 물
            if (z.Contains("동헌") || z.Contains("도성") || z.Contains("명부")) return SoulColor.White;          // 쇠·관아·명부
            return SoulColor.Blue;                                                                              // 솔고개·폐당집 등 산·숲·고개
        }
        public static string KoName(SoulColor c)
        {
            switch (c) { case SoulColor.Blue: return "푸른 넋"; case SoulColor.Red: return "붉은 넋"; case SoulColor.Yellow: return "누런 넋"; case SoulColor.White: return "흰 넋"; default: return "검은 넋"; }
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
