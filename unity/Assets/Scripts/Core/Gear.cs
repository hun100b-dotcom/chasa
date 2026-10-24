// =============================================================================
// Gear.cs — 무기·도술·장비의 '데이터 정의'와 능력치 계산 (순수 C#)
// 왜 데이터로? 차사는 사슬 하나만 쓰는 게임이 아니다. 무기·스킬·장비를 코드가 아니라 표(정의)로 두어야
// 새 무기를 '정의 한 줄'로 추가하고, 밸런스 값은 balance.json 한 곳에서 고칠 수 있다.
// (나중에 Unity 에디터의 ScriptableObject(값을 파일로 끼워 넣는 데이터 상자)로 옮겨도 이 정의가 그대로 쓰인다.)
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    // ---------------------------------------------------------------- 무기
    public enum WeaponId { Chain, Mace, Bell, Trident, Brush }   // 철삭 / 육모방망이 / 요령방울 / 삼지창 / 명부 붓

    /// <summary>무기 하나의 처결 쪽 성격. 콤보 모션(화면 값)은 Unity 쪽 표에서 같은 Id 로 찾는다</summary>
    public class WeaponDef
    {
        public WeaponId Id;
        public string Name;
        public float PahonKnockbackMult = 1f;   // 파혼 넉백 배율
        public float PahonDamageMult = 1f;      // 파혼 피해 배율
        public bool HasQuake;                   // 이 무기의 Q 기술이 땅울림인가
        public bool HasPull;                    // 이 무기의 Q 기술이 철삭 견인인가 (사슬만)
        public int MaxHits;                     // 한 번 휘두를 때 맞는 적 수 상한 (0 = 제한 없음, 삼지창 관통 3 등)

        public static readonly WeaponDef Chain = new WeaponDef { Id = WeaponId.Chain, Name = "철삭", HasQuake = false, HasPull = true };
        public static readonly WeaponDef Mace = new WeaponDef
        {
            Id = WeaponId.Mace, Name = "육모방망이",
            PahonKnockbackMult = Balance.MACE_PAHON_KNOCKBACK_MULT,
            PahonDamageMult = Balance.MACE_PAHON_DAMAGE_MULT,
            HasQuake = true
        };

        // 시연판 이후 무기 3계열 (기획서 6절 임시값). 콤보 숫자는 Unity 쪽 WeaponTable 에 있다.
        // 요령방울: 짧은 원 범위 — 여러 마리를 한꺼번에 흔든다
        public static readonly WeaponDef Bell = new WeaponDef { Id = WeaponId.Bell, Name = "요령방울" };
        // 삼지창: 가늘고 긴 찌르기 — 줄지은 적을 최대 3마리까지 꿰뚫는다
        public static readonly WeaponDef Trident = new WeaponDef { Id = WeaponId.Trident, Name = "삼지창", MaxHits = 3 };
        // 명부 붓: 멀리서 한 마리 — 투사체(날아가는 것)가 생기기 전까지는 좁고 긴 휘두름으로 대신한다
        public static readonly WeaponDef Brush = new WeaponDef { Id = WeaponId.Brush, Name = "명부 붓", MaxHits = 1 };

        public static WeaponDef Get(WeaponId id)
        {
            switch (id)
            {
                case WeaponId.Mace: return Mace;
                case WeaponId.Bell: return Bell;
                case WeaponId.Trident: return Trident;
                case WeaponId.Brush: return Brush;
                default: return Chain;
            }
        }
    }

    // ---------------------------------------------------------------- 도술(스킬)
    public enum SkillId { HoldCall, Bind, StainBurst }   // 붙잡아 부르기 / 휘감기 / 터뜨리기

    public class SkillDef
    {
        public SkillId Id;
        public string Name;
        public float Cooldown;

        /// <summary>기획팀 JSON 이 이름·재사용 시간을 덮어쓸 때 (GrowthData 로더가 부른다). 모르는 id 면 false</summary>
        public static bool Override(string id, string name, float cooldown)
        {
            foreach (var s in All)
                if (s.Id.ToString() == id)
                {
                    if (!string.IsNullOrEmpty(name)) s.Name = name;
                    if (cooldown > 0f) s.Cooldown = cooldown;
                    return true;
                }
            return false;
        }

        public static readonly SkillDef[] All =
        {
            new SkillDef { Id = SkillId.HoldCall, Name = "붙잡아 부르기", Cooldown = Balance.SKILL_HOLD_COOLDOWN },
            new SkillDef { Id = SkillId.Bind, Name = "휘감기", Cooldown = Balance.SKILL_BIND_COOLDOWN },
            new SkillDef { Id = SkillId.StainBurst, Name = "터뜨리기", Cooldown = Balance.SKILL_BURST_COOLDOWN },
        };
    }

    /// <summary>도술 세 칸의 재사용 대기. 쓰면 쿨다운이 돌고, 0이 되면 다시 쓸 수 있다</summary>
    public class SkillBar
    {
        public readonly float[] Left = new float[3];

        public bool Ready(int slot) { return Left[slot] <= 0f; }
        public float Ratio(int slot) { return Left[slot] <= 0f ? 0f : Left[slot] / SkillDef.All[slot].Cooldown; }

        /// <param name="cooldownMult">1 - (마음 능력치 등으로 줄어든 비율). 기본 1</param>
        public bool TryUse(int slot, float cooldownMult = 1f)
        {
            if (!Ready(slot)) return false;
            Left[slot] = SkillDef.All[slot].Cooldown * cooldownMult;
            return true;
        }

        public void Tick(float dt)
        {
            for (int i = 0; i < Left.Length; i++) Left[i] = Math.Max(0f, Left[i] - dt);
        }
    }

    // ---------------------------------------------------------------- 장비
    public enum Slot { Weapon, Robe, Charm }                 // 무기 / 도포 / 노리개
    public enum Rarity { Common, Crafted, Rare }             // 흔한 / 손본 / 귀한
    public enum Opt
    {
        DamagePct,        // 맺힘 피해 +%
        AttackSpeedPct,   // 공격 속도 +%
        CastReducePct,    // 천도 캐스팅 -% (양수 = 빨라짐, 음수 = 느려짐)
        PahonAreaPct,     // 파혼 반경 면적 +%
        PahonDamagePct,   // 파혼 피해 +%
        HpFlat,           // 생명 +
        MoveSpeedPct,     // 이동 속도 +%
        CoinPct,          // 엽전 +%
        PahonRadiusM      // 파혼 반경 +m (이름 있는 물건 전용)
    }

    public struct OptionRoll
    {
        public Opt Kind; public float Value;
        public OptionRoll(Opt k, float v) { Kind = k; Value = v; }
    }

    public class ItemDef
    {
        public Slot Slot;
        public Rarity Rarity;
        public string Name;
        public bool Named;                                   // 이름 있는 물건(월화의 방울)
        public bool Gradient;                                // 기울기 옵션 포함 (귀한 등급에만)
        public List<OptionRoll> Options = new List<OptionRoll>();

        /// <summary>시연판의 이름 있는 물건: 파혼 반경 +m (노리개)</summary>
        public static ItemDef MoonflowerBell()
        {
            var it = new ItemDef { Slot = Slot.Charm, Rarity = Rarity.Rare, Name = "월화 방울", Named = true };
            it.Options.Add(new OptionRoll(Opt.PahonRadiusM, Balance.MOONFLOWER_BELL_PAHON_RADIUS));
            return it;
        }
    }

    /// <summary>능력치 합계. 옵션 합계는 상한을 넘지 못한다 — 어느 한쪽이 정답이 되지 않게 (기획서 6-3)</summary>
    public class GearStats
    {
        public float DamagePct, AttackSpeedPct, CastReducePct, PahonAreaPct, PahonDamagePct, MoveSpeedPct, CoinPct, PahonRadiusM;
        public int HpFlat;

        public float DamageMult { get { return 1f + Math.Min(DamagePct, Balance.CAP_DAMAGE_PCT); } }
        public float AttackSpeedMult { get { return 1f + Math.Min(AttackSpeedPct, Balance.CAP_ATTACK_SPEED_PCT); } }
        /// <summary>천도 캐스팅 배율. 단축은 상한 -30%까지, 느려짐(음수)은 제한 없음</summary>
        public float CastMult { get { return 1f - Math.Min(CastReducePct, Balance.CAP_CAST_REDUCE_PCT); } }
        public float PahonDamageMult { get { return 1f + Math.Min(PahonDamagePct, Balance.CAP_PAHON_DAMAGE_PCT); } }
        public float MoveSpeedMult { get { return 1f + Math.Min(MoveSpeedPct, Balance.CAP_MOVE_SPEED_PCT); } }
        public float CoinMult { get { return 1f + Math.Min(CoinPct, Balance.CAP_COIN_PCT); } }
        /// <summary>
        /// 빌드가 천도 쪽(-1)인지 파혼 쪽(+1)인지. 캐릭터 창의 기울기 막대. 천도 점수 = 캐스팅 단축(상한 대비),
        /// 파혼 점수 = 파혼 피해·반경(상한 대비) 평균. 둘이 같으면 0.
        /// </summary>
        public float Tilt(float weaponPahonLean = 0f)
        {
            float tendo = Clamp(CastReducePct / Balance.CAP_CAST_REDUCE_PCT, -1f, 1f);
            float pahon = (Clamp(PahonDamagePct / Balance.CAP_PAHON_DAMAGE_PCT, 0f, 1f) + Clamp(PahonAreaPct / Balance.CAP_PAHON_AREA_PCT, 0f, 1f)) * 0.5f + weaponPahonLean;
            return Clamp(pahon - tendo, -1f, 1f);
        }

        static float Clamp(float v, float lo, float hi) { return Math.Max(lo, Math.Min(hi, v)); }

        public int MaxHp { get { return Balance.PLAYER_MAX_HP + HpFlat; } }

        /// <summary>
        /// 파혼 반경(m). 면적 +x% 는 반경 sqrt(1+x) 배. 상한(면적 +40%)은 면적 기준이고 +m(이름 있는 물건)도 합쳐 같은 상한을 지킨다.
        /// </summary>
        public float PahonRadius(float baseRadius)
        {
            float areaMult = 1f + Math.Min(PahonAreaPct, Balance.CAP_PAHON_AREA_PCT);
            float r = baseRadius * (float)Math.Sqrt(areaMult) + PahonRadiusM;
            float cap = baseRadius * (float)Math.Sqrt(1f + Balance.CAP_PAHON_AREA_PCT);
            return Math.Min(r, cap);
        }

        public void Add(ItemDef it)
        {
            foreach (var o in it.Options)
                switch (o.Kind)
                {
                    case Opt.DamagePct: DamagePct += o.Value; break;
                    case Opt.AttackSpeedPct: AttackSpeedPct += o.Value; break;
                    case Opt.CastReducePct: CastReducePct += o.Value; break;
                    case Opt.PahonAreaPct: PahonAreaPct += o.Value; break;
                    case Opt.PahonDamagePct: PahonDamagePct += o.Value; break;
                    case Opt.HpFlat: HpFlat += (int)o.Value; break;
                    case Opt.MoveSpeedPct: MoveSpeedPct += o.Value; break;
                    case Opt.CoinPct: CoinPct += o.Value; break;
                    case Opt.PahonRadiusM: PahonRadiusM += o.Value; break;
                }
        }
    }

    /// <summary>장착 세 칸. 같은 칸의 새 물건이 더 귀하면(같으면 옵션 점수가 높으면) 바꿔 낀다</summary>
    public class Equipment
    {
        readonly ItemDef[] slots = new ItemDef[3];
        public ItemDef Get(Slot s) { return slots[(int)s]; }

        public static int Score(ItemDef it)
        {
            if (it == null) return -1;
            int s = (int)it.Rarity * 100 + it.Options.Count * 10;
            if (it.Named) s += 1000;
            return s;
        }

        /// <summary>새 물건이 지금 것보다 나으면 장착하고 true. (시연판은 자동 비교 — 버리는 쪽은 사라진다)</summary>
        public bool TryEquip(ItemDef it)
        {
            if (Score(it) <= Score(slots[(int)it.Slot])) return false;
            slots[(int)it.Slot] = it;
            return true;
        }

        public GearStats Stats()
        {
            var st = new GearStats();
            foreach (var it in slots) if (it != null) st.Add(it);
            return st;
        }
    }

    /// <summary>
    /// 드롭 굴림. 맺힘 0 이 되는 순간 한 번, 처결 방식과 무관 (기획서 6-1 규칙 ②). 사나운 적은 귀한 확정 (규칙 ③).
    /// rand() 는 0~1 난수 — 테스트에서 값을 정해 줄 수 있게 함수로 받는다.
    /// </summary>
    public static class Loot
    {
        static readonly Slot[] SlotPool = { Slot.Weapon, Slot.Robe, Slot.Charm };

        public static ItemDef Roll(Func<float> rand, bool fierce)
        {
            if (!fierce && rand() >= Balance.DROP_CHANCE) return null;
            Rarity r;
            float x = rand();
            if (fierce || x < Balance.DROP_RARITY_RARE) r = Rarity.Rare;
            else if (x < Balance.DROP_RARITY_RARE + Balance.DROP_RARITY_CRAFTED) r = Rarity.Crafted;
            else r = Rarity.Common;

            var it = new ItemDef { Slot = SlotPool[(int)(rand() * 3f) % 3], Rarity = r };
            it.Name = r + " " + it.Slot;
            int n = r == Rarity.Common ? (rand() < 0.5f ? 0 : 1) : r == Rarity.Crafted ? 1 + (rand() < 0.5f ? 0 : 1) : 3;
            // 시연판 옵션 8종 중 고르기. 중복 없이 n 개.
            var pool = new List<Opt> { Opt.DamagePct, Opt.AttackSpeedPct, Opt.CastReducePct, Opt.PahonAreaPct, Opt.PahonDamagePct, Opt.HpFlat, Opt.MoveSpeedPct, Opt.CoinPct };
            if (r == Rarity.Rare)
            {
                // 귀한 등급: 기울기 옵션 1줄 = 맺힘 피해 +20% / 천도 캐스팅 +10%(느려짐) (기획 확정). 나머지 일반 옵션 2개
                it.Gradient = true;
                it.Options.Add(new OptionRoll(Opt.DamagePct, 0.20f));
                it.Options.Add(new OptionRoll(Opt.CastReducePct, -0.10f));
                pool.Remove(Opt.DamagePct); pool.Remove(Opt.CastReducePct);
                n = 2;
            }
            for (int i = 0; i < n && pool.Count > 0; i++)
            {
                int k = (int)(rand() * pool.Count) % pool.Count;
                var kind = pool[k]; pool.RemoveAt(k);
                it.Options.Add(new OptionRoll(kind, RollValue(kind, r)));
            }
            return it;
        }

        // 옵션 기본값(등급 1.0 배 기준). 기획팀 JSON 이 SetBase 로 덮어쓸 수 있다
        static readonly Dictionary<Opt, float> BaseValue = new Dictionary<Opt, float>
        {
            { Opt.DamagePct, 0.06f }, { Opt.AttackSpeedPct, 0.04f }, { Opt.CastReducePct, 0.05f }, { Opt.PahonAreaPct, 0.08f },
            { Opt.PahonDamagePct, 0.08f }, { Opt.HpFlat, 10f }, { Opt.MoveSpeedPct, 0.04f }, { Opt.CoinPct, 0.08f }
        };

        public static bool SetBase(string kind, float value)
        {
            Opt k;
            if (!Enum.TryParse(kind, out k) || !BaseValue.ContainsKey(k)) return false;
            BaseValue[k] = value;
            return true;
        }

        public static float GetBase(Opt k) { float v; return BaseValue.TryGetValue(k, out v) ? v : 0f; }

        /// <summary>옵션 하나의 값. 등급이 높을수록 크다 (임시값)</summary>
        static float RollValue(Opt k, Rarity r)
        {
            float t = r == Rarity.Common ? 0.5f : r == Rarity.Crafted ? 0.8f : 1.1f;
            float v = GetBase(k) * t;
            return k == Opt.HpFlat ? (float)Math.Round(v) : v;
        }
    }

    /// <summary>능력치 4종(힘·날램·몸·마음)은 시연판에서 표시 전용. 넋 30마다 1점</summary>
    public static class StatPoints
    {
        public static int Earned(int totalNeokGained) { return totalNeokGained / Balance.STAT_POINT_PER_NEOK; }
    }
}
