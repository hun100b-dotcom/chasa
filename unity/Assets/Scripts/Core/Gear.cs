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
        public bool Projectile;                 // 휘두름 대신 날아가는 먹물(투사체)을 쏘는가 (명부 붓)
        public float CastTimeMult = 1f;         // 천도 시전 시간 배율(요령방울 등)
        public float NeokPct;                   // 천도 넋 +%(명부 붓)
        public float ChainWindowAddS;           // 연속 천도 창 +초(철삭)
        public string Taste = "";               // 명부에 보일 한 줄: 이 무기의 천도·파혼 맛
        public bool HasCall;                    // Q 불러 세우기(요령방울): 둘레 무릎 꿇은 혼의 처결 대기가 잠시 멈춘다
        public bool HasFence;                   // Q 꽂아 버티기(삼지창): 잠깐 일반 적이 못 들어오는 울타리
        public bool HasInkName;                 // Q 이름 쓰기(명부 붓): 표식 3개인 적의 이름을 미리 써 둔다(천도 시전 단축)
        public int MaxHits;                     // 한 번 휘두를 때 맞는 적 수 상한 (0 = 제한 없음, 삼지창 관통 3 등)

        public static readonly WeaponDef Chain = new WeaponDef { Id = WeaponId.Chain, Name = "철삭", HasQuake = false, HasPull = true, ChainWindowAddS = Balance.CHAIN_CHAIN_WINDOW_ADD, Taste = "고르다 · 끌기(Q) · 연속 천도가 길다" };
        public static readonly WeaponDef Mace = new WeaponDef
        {
            Id = WeaponId.Mace, Name = "육모방망이",
            PahonKnockbackMult = Balance.MACE_PAHON_KNOCKBACK_MULT,
            PahonDamageMult = Balance.MACE_PAHON_DAMAGE_MULT,
            HasQuake = true,
            Taste = "파혼에 멀리 날린다 · 땅울림(Q) · 가까이 한 방"
        };

        // 시연판 이후 무기 3계열 (기획서 6절 임시값). 콤보 숫자는 Unity 쪽 WeaponTable 에 있다.
        // 요령방울: 짧은 원 범위 — 여러 마리를 한꺼번에 흔든다
        public static readonly WeaponDef Bell = new WeaponDef { Id = WeaponId.Bell, Name = "요령방울", HasCall = true, CastTimeMult = Balance.BELL_CAST_MULT, PahonDamageMult = Balance.BELL_PAHON_DAMAGE_MULT, Taste = "천도가 빠르다 · 파혼은 약하다 · 둘레의 여럿을 흔든다" };
        // 삼지창: 가늘고 긴 찌르기 — 줄지은 적을 최대 3마리까지 꿰뚫는다
        public static readonly WeaponDef Trident = new WeaponDef { Id = WeaponId.Trident, Name = "삼지창", HasFence = true, MaxHits = 3, PahonKnockbackMult = Balance.TRIDENT_PAHON_KNOCKBACK_MULT, PahonDamageMult = Balance.TRIDENT_PAHON_DAMAGE_MULT, Taste = "파혼이 날카롭다 · 줄 선 셋을 꿰뚫는다" };
        // 명부 붓: 멀리서 한 마리 — 먹물 투사체(날아가는 것)를 쏜다. 사거리는 콤보 표의 reach
        public static readonly WeaponDef Brush = new WeaponDef { Id = WeaponId.Brush, Name = "명부 붓", HasInkName = true, MaxHits = 1, Projectile = true, NeokPct = Balance.BRUSH_NEOK_PCT, PahonDamageMult = Balance.BRUSH_PAHON_DAMAGE_MULT, Taste = "멀리서 쏜다 · 천도 넋 조금 더 · 표식" };

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
    public enum Slot { Weapon, Robe, Charm, Hat, Belt, Shoes }   // 무기 / 도포 / 노리개 / 갓 / 띠 / 신 (앞 셋은 옛 저장과 번호가 같다. 자리는 EquipPos 8개: 무기·노리개는 둘씩)
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
        PahonRadiusM,     // 파혼 반경 +m (이름 있는 물건·검은 술)
        // ---- 기울기 옵션 전용 (귀한 등급의 기울기 한 줄에서만 나온다)
        TendoNeokPct,     // 천도 넋 +%
        PahonCoinPct,     // 파혼 엽전 +% (음수 = 줄어듦)
        WaitAddS,         // 처결 대기 시간 +초 (음수 = 짧아짐)
        ChainWindowAddS,  // 연속 천도 창 +초
        PahonKnockbackPct,// 파혼 넉백 +%
        VisionShift,      // 천도 중 시야 비율 이동(음수 = 더 좁아짐)
        CastDamageReducePct,// 천도 시전 중 받는 피해 −%
        // ---- 기획 장비 점검(10-26)으로 더한 옵션: 맨 끝에 붙여 옛 저장(이름으로 저장)과 어긋나지 않게 한다
        DefensePct,       // 방어: 받는 피해 −% (도포·갓, 합계 상한 60%)
        SkillCdReduce,    // 도술 재사용 −% (갓, 상한 35%)
        WeaponCdReduce,   // 무기 기술 재사용 −% (무기·갓, 상한 40%)
        FiercePct         // 거센 혼·덩어리·보스 피해 +% (무기·노리개, 상한 50%)
    }

    /// <summary>
    /// 기울기 한 줄(플러스 한 쪽 + 마이너스 한 쪽). 기획 growth.json 의 tilts 와 같은 표.
    /// Demo=true 인 것만 기본 드롭에 나온다 (시연판은 피 묻은 매듭 하나). 나머지는 QA 검증 뒤 켠다.
    /// </summary>
    public class TiltDef
    {
        public string Id, Name;
        public bool Demo;
        public OptionRoll[] Options;
        public TiltDef(string id, string name, bool demo, params OptionRoll[] opts) { Id = id; Name = name; Demo = demo; Options = opts; }

        public static readonly TiltDef[] All =
        {
            new TiltDef("tilt_dmg_cast", "피 묻은 매듭", true,
                new OptionRoll(Opt.DamagePct, 0.20f), new OptionRoll(Opt.CastReducePct, -0.10f)),
            new TiltDef("tilt_neok_coin", "향 내음", false,
                new OptionRoll(Opt.TendoNeokPct, Balance.TILT_NEOK_PCT), new OptionRoll(Opt.PahonCoinPct, Balance.TILT_PAHON_COIN_PCT)),
            new TiltDef("tilt_radius_wait", "검은 술", false,
                new OptionRoll(Opt.PahonRadiusM, Balance.TILT_RADIUS_M), new OptionRoll(Opt.WaitAddS, Balance.TILT_WAIT_ADD)),
            new TiltDef("tilt_window_dmg", "젖은 소매", false,
                new OptionRoll(Opt.ChainWindowAddS, Balance.TILT_WINDOW_ADD), new OptionRoll(Opt.DamagePct, Balance.TILT_WINDOW_DMG_PCT)),
            new TiltDef("tilt_kb_vision", "깨진 거울", false,
                new OptionRoll(Opt.PahonKnockbackPct, Balance.TILT_KNOCKBACK_PCT), new OptionRoll(Opt.VisionShift, Balance.TILT_VISION_SHIFT)),
            new TiltDef("tilt_castdr_aspd", "상복 자락", false,
                new OptionRoll(Opt.CastDamageReducePct, Balance.TILT_CAST_DR_PCT), new OptionRoll(Opt.AttackSpeedPct, Balance.TILT_ASPD_PCT)),
        };

        public static TiltDef Find(string id) { foreach (var t in All) if (t.Id == id) return t; return null; }
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
        public string TiltId;                                // 어떤 기울기인가 (TiltDef.Id)
        public int Rerolls;                                  // 다시 굴린 횟수 (비용이 오른다)
        public int Plus;                                     // 장비 손보기 단계(0~ENHANCE_MAX). 첫 옵션(주옵션)이 단계마다 +6%
        public int Sockets;                                  // 뚫은 인 홈 수 (최대 SOCKET_MAX)
        public List<Seal> Seals = new List<Seal>();          // 홈에 박은 인(Sockets 개수를 넘지 않는다)
        public List<OptionRoll> Options = new List<OptionRoll>();

        /// <summary>서사 확정 이름 있는 물건 5개(보스 처결 보상 노리개). 효과는 이름으로 JudgeSystem 이 읽는다(왕초의 바가지·흑월의 붓은 구현, 나머지는 기획 효과 확정 대기)</summary>
        public static ItemDef BossKeepsake(int bossId)
        {
            string name = bossId == 1 ? "도한수의 뱃삯" : bossId == 8 ? "남은 장부" : bossId == 9 ? "아낙의 등잔" : bossId == 11 ? "왕초의 바가지" : bossId == 12 ? "흑월의 붓" : null;
            if (name == null) return null;
            return new ItemDef { Slot = Slot.Charm, Rarity = Rarity.Rare, Name = name, Named = true };
        }

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
        public float TendoNeokPct, PahonCoinPct, WaitAddS, ChainWindowAddS, PahonKnockbackPct, VisionShift, CastDamageReducePct;
        public float ReachAdd, BoundBonus, StainShorten;   // 도술 패시브: 무기 사거리 +m / 묶인 적 받는 피해 +% / 얼룩 지속 단축 비율
        public float StatDamagePct;   // 힘(능력치) 피해: 장비 상한 밖에서 따로 곱한다(기획 점검 B-1: 힘이 장비 상한을 다 먹지 않게)
        public float DefensePct, SkillCdReduce, WeaponCdReduce, FiercePct;   // 인 전용: 방어 / 도술 재사용 단축 / 무기 기술 재사용 단축 / 사나운 적 피해 (쓰는 쪽 연결은 순서대로)
        public int HpFlat;

        /// <summary>피해 배율 = (1 + 장비·인·패시브 합[상한 +40%, 마이너스는 −20%까지]) × (1 + 힘). 힘은 상한 밖</summary>
        public float DamageMult { get { return (1f + Math.Max(Math.Min(DamagePct, Balance.CAP_DAMAGE_PCT), -Balance.CAP_DAMAGE_MINUS_PCT)) * (1f + StatDamagePct); } }
        /// <summary>받는 피해 배율(방어 상한 60%)</summary>
        public float DefenseMult { get { return 1f - Math.Min(Math.Max(DefensePct, 0f), Balance.CAP_DEFENSE_PCT); } }
        public float SkillCdMult { get { return 1f - Math.Min(Math.Max(SkillCdReduce, 0f), Balance.CAP_SKILL_CD_PCT); } }
        public float WeaponCdMult { get { return 1f - Math.Min(Math.Max(WeaponCdReduce, 0f), Balance.CAP_WEAPON_CD_PCT); } }
        /// <summary>거센 혼·덩어리·보스에게 주는 피해 배율(상한 +50%)</summary>
        public float FierceMult { get { return 1f + Math.Min(Math.Max(FiercePct, 0f), Balance.CAP_FIERCE_PCT); } }
        public float AttackSpeedMult { get { return 1f + Math.Min(AttackSpeedPct, Balance.CAP_ATTACK_SPEED_PCT); } }
        /// <summary>천도 캐스팅 배율. 단축은 상한 -30%까지, 느려짐(음수)은 +30%까지(기울기 마이너스가 쌓여도 2.4초까지 안 간다)</summary>
        public float CastMult { get { return 1f - Math.Max(Math.Min(CastReducePct, Balance.CAP_CAST_REDUCE_PCT), -Balance.CAP_CAST_SLOW_PCT); } }
        public float PahonDamageMult { get { return 1f + Math.Min(PahonDamagePct, Balance.CAP_PAHON_DAMAGE_PCT); } }
        public float MoveSpeedMult { get { return 1f + Math.Min(MoveSpeedPct, Balance.CAP_MOVE_SPEED_PCT); } }
        public float CoinMult { get { return 1f + Math.Max(Math.Min(CoinPct, Balance.CAP_COIN_PCT), -Balance.CAP_COIN_MINUS_PCT); } }
        /// <summary>천도 넋 배율 (향 내음)</summary>
        public float TendoNeokMult { get { return Math.Max(0f, 1f + Math.Min(TendoNeokPct, Balance.CAP_TENDO_NEOK_PCT)); } }   // 합계 상한 +30%(기획 점검 B-7)
        /// <summary>파혼 엽전 배율 (향 내음의 마이너스). 장비 엽전 보너스(CoinMult)와 곱해진다</summary>
        public float PahonCoinMult { get { return Math.Max(1f - Balance.CAP_COIN_MINUS_PCT, 1f + PahonCoinPct); } }   // 마이너스는 −50%까지
        /// <summary>처결 대기 시간 보정(초). 최종 대기는 WAIT_FLOOR 밑으로 못 내려간다 — 쓰는 쪽에서 AdjustWait 로</summary>
        public float AdjustWait(float baseWait, bool lump)
        {
            if (lump || WaitAddS >= 0f) return baseWait + (lump ? 0f : WaitAddS);   // 덩어리 혼은 대기 단축 제외(기획)
            return Math.Max(Math.Min(baseWait, Balance.WAIT_FLOOR), baseWait + WaitAddS);
        }
        public float ChainWindow { get { return Math.Max(0f, Balance.TENDO_CHAIN_WINDOW + ChainWindowAddS); } }
        public float PahonKnockbackMult { get { return Math.Max(0f, 1f + PahonKnockbackPct); } }
        /// <summary>천도 중 시야 비율. 하한 VISION_RATIO_FLOOR 밑으로 안 좁아진다</summary>
        public float VisionRatio(float baseRatio) { return Math.Max(Math.Min(baseRatio, Balance.VISION_RATIO_FLOOR), baseRatio + VisionShift); }
        /// <summary>천도 시전 중 받는 피해 배율 (상한 −50%)</summary>
        public float CastDamageTakenMult { get { return 1f - Math.Min(Math.Max(CastDamageReducePct, 0f), 0.5f); } }
        /// <summary>
        /// 빌드가 천도 쪽(-1)인지 파혼 쪽(+1)인지. 캐릭터 창의 기울기 막대. 천도 점수 = 캐스팅 단축(상한 대비),
        /// 파혼 점수 = 파혼 피해·반경(상한 대비) 평균. 둘이 같으면 0.
        /// </summary>
        public float Tilt(float weaponPahonLean = 0f)
        {
            float tendo = Clamp(CastReducePct / Balance.CAP_CAST_REDUCE_PCT, -1f, 1f);
            float pahon = (Clamp(PahonDamagePct / Balance.CAP_PAHON_DAMAGE_PCT, 0f, 1f) + Clamp(PahonAreaPct / Balance.CAP_PAHON_AREA_PCT, 0f, 1f)) * 0.5f + weaponPahonLean;
            // 기울기 옵션: 천도 쪽(넋·연속 창·시전 중 방어)과 파혼 쪽(반경·넉백)을 각각 절반 점수까지 더한다
            tendo += 0.5f * (Clamp(TendoNeokPct / Balance.TILT_NEOK_PCT, 0f, 1f) + Clamp(ChainWindowAddS / Balance.TILT_WINDOW_ADD, 0f, 1f) + Clamp(CastDamageReducePct / Balance.TILT_CAST_DR_PCT, 0f, 1f)) / 3f;
            pahon += 0.5f * (Clamp(PahonRadiusM / Balance.TILT_RADIUS_M, 0f, 1f) + Clamp(PahonKnockbackPct / Balance.TILT_KNOCKBACK_PCT, 0f, 1f)) / 2f;
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

        /// <summary>이미 센 기울기 번호(같은 기울기는 하나만 센다 — 기획 점검 B-2)</summary>
        public readonly HashSet<string> TiltCounted = new HashSet<string>();

        public void Add(ItemDef it)
        {
            foreach (var sl in it.Seals) SealEffects.Apply(sl, this);   // 박힌 인의 효과
            // 같은 기울기(TiltId)가 둘 이상이면 첫 것만 센다. 기울기 줄은 이 물건 옵션 앞쪽 두 개(플러스·마이너스)
            bool skipTilt = it.Gradient && !string.IsNullOrEmpty(it.TiltId) && !TiltCounted.Add(it.TiltId);
            for (int oi = 0; oi < it.Options.Count; oi++)
            {
                if (skipTilt && oi < 2) continue;
                var o = it.Options[oi];
                if (oi == 0 && it.Plus > 0)   // 손보기: 주옵션만 단계마다 올린다(귀한 칸 하나를 키우는 길 = 파혼 쪽 성장)
                {
                    float m = 1f + Balance.ENHANCE_PCT * it.Plus;
                    o = new OptionRoll(o.Kind, o.Kind == Opt.HpFlat ? (float)Math.Round(o.Value * m) : o.Value * m);
                }
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
                    case Opt.TendoNeokPct: TendoNeokPct += o.Value; break;
                    case Opt.PahonCoinPct: PahonCoinPct += o.Value; break;
                    case Opt.WaitAddS: WaitAddS += o.Value; break;
                    case Opt.ChainWindowAddS: ChainWindowAddS += o.Value; break;
                    case Opt.PahonKnockbackPct: PahonKnockbackPct += o.Value; break;
                    case Opt.VisionShift: VisionShift += o.Value; break;
                    case Opt.CastDamageReducePct: CastDamageReducePct += o.Value; break;
                    case Opt.DefensePct: DefensePct += o.Value; break;
                    case Opt.SkillCdReduce: SkillCdReduce += o.Value; break;
                    case Opt.WeaponCdReduce: WeaponCdReduce += o.Value; break;
                    case Opt.FiercePct: FiercePct += o.Value; break;
                }
            }
        }
    }

    /// <summary>
    /// 장착 여덟 자리(EquipPos: 무기 2·갓·도포·띠·신·노리개 2). 같은 종류 물건은 열린 빈 자리에 먼저 끼고,
    /// 자리가 다 찼으면 가장 못한 자리의 것보다 나을 때만 바꿔 낀다. 갓·띠는 1막 보스 하나를 보낸 뒤, 신·노리개 둘째는 2막에 들어선 뒤에 열린다.
    /// 옛 코드(Get/Put/Remove(Slot))는 그 종류의 첫 자리(무기1·도포·노리개1)를 가리킨다 — 옛 저장과 화면이 그대로 돈다.
    /// </summary>
    public class Equipment
    {
        readonly ItemDef[] pos = new ItemDef[8];
        public bool FirstRingBossDone, Act2Entered;   // 열린 자리 판단(EquipLayout.IsOpen). JudgeSystem 이 진행에 맞춰 켠다

        /// <summary>물건 종류가 들어갈 수 있는 자리들(앞쪽이 첫 자리)</summary>
        public static EquipPos[] PositionsOf(Slot s)
        {
            switch (s)
            {
                case Slot.Weapon: return new[] { EquipPos.Weapon1, EquipPos.Weapon2 };
                case Slot.Robe: return new[] { EquipPos.Robe };
                case Slot.Charm: return new[] { EquipPos.Charm1, EquipPos.Charm2 };
                case Slot.Hat: return new[] { EquipPos.Hat };
                case Slot.Belt: return new[] { EquipPos.Belt };
                default: return new[] { EquipPos.Shoes };
            }
        }
        /// <summary>자리의 물건 종류</summary>
        public static Slot KindOf(EquipPos p)
        {
            switch (p)
            {
                case EquipPos.Weapon1: case EquipPos.Weapon2: return Slot.Weapon;
                case EquipPos.Hat: return Slot.Hat;
                case EquipPos.Robe: return Slot.Robe;
                case EquipPos.Belt: return Slot.Belt;
                case EquipPos.Shoes: return Slot.Shoes;
                default: return Slot.Charm;
            }
        }
        public bool IsOpen(EquipPos p) { return EquipLayout.IsOpen(p, FirstRingBossDone, Act2Entered); }
        /// <summary>지금 드롭에 나올 수 있는 물건 종류(열린 자리가 있는 종류)</summary>
        public Slot[] DropKinds()
        {
            var l = new List<Slot>();
            foreach (Slot k in new[] { Slot.Weapon, Slot.Robe, Slot.Charm, Slot.Hat, Slot.Belt, Slot.Shoes })
                foreach (var p in PositionsOf(k)) if (IsOpen(p)) { l.Add(k); break; }
            return l.ToArray();
        }

        public ItemDef GetAt(EquipPos p) { return pos[(int)p]; }
        public void PutAt(EquipPos p, ItemDef it) { pos[(int)p] = it; }
        public void RemoveAt(EquipPos p) { pos[(int)p] = null; }

        public ItemDef Get(Slot s) { return pos[(int)PositionsOf(s)[0]]; }

        public static int Score(ItemDef it)
        {
            if (it == null) return -1;
            int s = (int)it.Rarity * 100 + it.Options.Count * 10;
            if (it.Named) s += 1000;
            return s;
        }

        /// <summary>새 물건이 들어갈 자리를 골라 장착하고 true. 빈 열린 자리가 있으면 거기, 없으면 가장 못한 자리를 이길 때만 바꿔 낀다</summary>
        public bool TryEquip(ItemDef it)
        {
            EquipPos worst = EquipPos.Weapon1; int worstScore = int.MaxValue; bool any = false;
            foreach (var p in PositionsOf(it.Slot))
            {
                if (!IsOpen(p)) continue;
                var cur = pos[(int)p];
                if (cur == null) { pos[(int)p] = it; return true; }
                int sc = Score(cur); if (!any || sc < worstScore) { any = true; worst = p; worstScore = sc; }
            }
            if (!any || Score(it) <= worstScore) return false;
            pos[(int)worst] = it; return true;
        }

        /// <summary>저장 불러오기용: 비교 없이 그 종류의 첫 자리에 그대로 넣는다(null 이면 비움)</summary>
        public void Put(Slot s, ItemDef it) { pos[(int)PositionsOf(s)[0]] = it; }

        /// <summary>그 종류의 첫 자리를 비운다 (풀기·분해에 쓴다)</summary>
        public void Remove(Slot s) { pos[(int)PositionsOf(s)[0]] = null; }

        public GearStats Stats()
        {
            var st = new GearStats();
            for (int i = 0; i < pos.Length; i++) { if (i == (int)EquipPos.Weapon2) continue; if (pos[i] != null) st.Add(pos[i]); }   // 등에 멘 무기(둘째 자리)는 세지 않는다 — 손에 든 무기만(기획 점검 B-6)
            return st;
        }
    }

    /// <summary>
    /// 드롭 굴림. 맺힘 0 이 되는 순간 한 번, 처결 방식과 무관 (기획서 6-1 규칙 ②). 사나운 적은 귀한 확정 (규칙 ③).
    /// rand() 는 0~1 난수 — 테스트에서 값을 정해 줄 수 있게 함수로 받는다.
    /// </summary>
    public static class Loot
    {
        static readonly Slot[] SlotPool = { Slot.Weapon, Slot.Robe, Slot.Charm };   // 기본(옛 시연판) 물건 종류. 열린 자리가 늘면 Equipment.DropKinds 를 kindPool 로 넘긴다

        /// <summary>true 면 시연판 밖 기울기 5종도 드롭에 나온다 (QA 검증 뒤 켠다)</summary>
        public static bool AllTilts = false;   // 2막에 들어서면 JudgeSystem 이 켠다(기획 점검 B-2)

        /// <summary>기울기 한 줄 고르기. 후보가 하나뿐이면 난수를 쓰지 않는다(기존 드롭 결과가 그대로 유지되도록)</summary>
        static TiltDef PickTilt(Func<float> rand)
        {
            var list = new List<TiltDef>();
            foreach (var t in TiltDef.All) if (AllTilts || t.Demo) list.Add(t);
            return list.Count == 1 ? list[0] : list[(int)(rand() * list.Count) % list.Count];
        }

        public static ItemDef Roll(Func<float> rand, bool fierce) { return Roll(rand, fierce, 0, null); }

        /// <summary>ring 1~6 이면 고리별 등급 표(RingLoot), 0 이면 시연판 고정 확률. 난수를 쓰는 순서는 같다(기존 결과 유지)</summary>
        public static ItemDef Roll(Func<float> rand, bool fierce, int ring, Slot[] kindPool = null)
        {
            if (!fierce && rand() >= Balance.DROP_CHANCE) return null;
            Rarity r;
            float x = rand();
            if (ring > 0) r = fierce ? Rarity.Rare : RingLoot.RarityAt(ring, x);
            else if (fierce || x < Balance.DROP_RARITY_RARE) r = Rarity.Rare;
            else if (x < Balance.DROP_RARITY_RARE + Balance.DROP_RARITY_CRAFTED) r = Rarity.Crafted;
            else r = Rarity.Common;

            var kinds = kindPool != null && kindPool.Length > 0 ? kindPool : SlotPool;
            var it = new ItemDef { Slot = kinds[(int)(rand() * kinds.Length) % kinds.Length], Rarity = r };
            it.Name = r + " " + it.Slot;
            int n = r == Rarity.Common ? (rand() < 0.5f ? 0 : 1) : r == Rarity.Crafted ? 1 + (rand() < 0.5f ? 0 : 1) : 3;
            // 시연판 옵션 8종 중 고르기. 중복 없이 n 개.
            var pool = new List<Opt>(PoolFor(it.Slot));   // 칸마다 나오는 옵션이 다르다(기획 growth.json affixes.slots)
            if (r == Rarity.Rare)
            {
                // 귀한 등급: 기울기 옵션 1줄 = 맺힘 피해 +20% / 천도 캐스팅 +10%(느려짐) (기획 확정). 나머지 일반 옵션 2개
                var tilt = PickTilt(rand);
                it.Gradient = true; it.TiltId = tilt.Id;
                foreach (var o in tilt.Options) { it.Options.Add(o); pool.Remove(o.Kind); }
                n = 2;
            }
            for (int i = 0; i < n && pool.Count > 0; i++)
            {
                int k = (int)(rand() * pool.Count) % pool.Count;
                var kind = pool[k]; pool.RemoveAt(k);
                it.Options.Add(new OptionRoll(kind, RollValue(kind, r, rand)));
            }
            return it;
        }

        /// <summary>일반 옵션 하나를 새로 굴린다. exclude 에 든 종류는 피한다 (다시 굴리기·매듭 올리기용)</summary>
        public static OptionRoll RollOption(Func<float> rand, Rarity r, ICollection<Opt> exclude) { return RollOption(rand, r, exclude, Slot.Weapon); }

        /// <summary>칸(slot)에 나올 수 있는 옵션만 후보로 굴린다</summary>
        public static OptionRoll RollOption(Func<float> rand, Rarity r, ICollection<Opt> exclude, Slot slot)
        {
            var pool = new List<Opt>(PoolFor(slot));
            if (exclude != null) pool.RemoveAll(o => exclude.Contains(o));
            if (pool.Count == 0) pool.Add(Opt.HpFlat);
            var kind = pool[(int)(rand() * pool.Count) % pool.Count];
            return new OptionRoll(kind, RollValue(kind, r, rand));
        }

        /// <summary>칸별 옵션 후보(기획 growth.json affixes 의 slots). 갓=gat, 도포=dopo, 띠=tti, 신=sin, 노리개=norigae</summary>
        public static Opt[] PoolFor(Slot slot)
        {
            switch (slot)
            {
                case Slot.Weapon: return new[] { Opt.DamagePct, Opt.AttackSpeedPct, Opt.WeaponCdReduce, Opt.FiercePct, Opt.PahonDamagePct };
                case Slot.Charm: return new[] { Opt.DamagePct, Opt.AttackSpeedPct, Opt.FiercePct, Opt.TendoNeokPct, Opt.ChainWindowAddS, Opt.PahonRadiusM, Opt.PahonDamagePct, Opt.CoinPct, Opt.CastReducePct };
                case Slot.Hat: return new[] { Opt.WeaponCdReduce, Opt.SkillCdReduce, Opt.DefensePct, Opt.HpFlat, Opt.CastReducePct };
                case Slot.Robe: return new[] { Opt.HpFlat, Opt.DefensePct, Opt.CastDamageReducePct, Opt.PahonKnockbackPct };
                case Slot.Belt: return new[] { Opt.CastReducePct, Opt.ChainWindowAddS, Opt.CastDamageReducePct, Opt.WaitAddS, Opt.PahonRadiusM, Opt.PahonDamagePct, Opt.PahonKnockbackPct, Opt.HpFlat };
                default: return new[] { Opt.HpFlat, Opt.MoveSpeedPct };
            }
        }

        /// <summary>등급별 옵션 크기 배율 (흔한 0.5 / 손본 0.8 / 귀한 1.1)</summary>
        public static float TierFactor(Rarity r) { return r == Rarity.Common ? 0.5f : r == Rarity.Crafted ? 0.8f : 1.1f; }

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
        static float RollValue(Opt k, Rarity r, Func<float> rand)
        {
            // 기획 growth.json affixes 의 등급별 범위 안에서 굴린다(없는 옵션은 기본값 ± 20%)
            float lo, hi; Range(k, r, out lo, out hi);
            float v = lo + (hi - lo) * rand();
            return k == Opt.HpFlat ? (float)Math.Round(v) : v;
        }

        // 옵션별 [흔한, 손본, 귀한] 범위(% 는 소수로). 값은 growth.json affixes ranges 와 같다
        static readonly Dictionary<Opt, float[]> Ranges = new Dictionary<Opt, float[]>
        {
            { Opt.DamagePct,          new[] { .03f, .05f, .05f, .09f, .09f, .14f } },
            { Opt.AttackSpeedPct,     new[] { .02f, .03f, .03f, .06f, .06f, .09f } },
            { Opt.CastReducePct,      new[] { .02f, .03f, .03f, .05f, .05f, .08f } },
            { Opt.PahonDamagePct,     new[] { .04f, .06f, .06f, .10f, .10f, .16f } },
            { Opt.HpFlat,             new[] { 8f, 12f, 12f, 20f, 20f, 32f } },
            { Opt.MoveSpeedPct,       new[] { .02f, .03f, .03f, .05f, .05f, .08f } },
            { Opt.CoinPct,            new[] { .04f, .06f, .06f, .10f, .10f, .15f } },
            { Opt.PahonKnockbackPct,  new[] { .05f, .08f, .08f, .12f, .12f, .18f } },
            { Opt.PahonRadiusM,       new[] { .05f, .10f, .10f, .20f, .20f, .30f } },
            { Opt.TendoNeokPct,       new[] { .03f, .04f, .04f, .07f, .07f, .10f } },
            { Opt.ChainWindowAddS,    new[] { .2f, .3f, .3f, .6f, .6f, 1.0f } },
            { Opt.WaitAddS,           new[] { .2f, .3f, .3f, .5f, .5f, .8f } },
            { Opt.CastDamageReducePct,new[] { .03f, .05f, .05f, .08f, .08f, .12f } },
            { Opt.DefensePct,         new[] { .02f, .03f, .03f, .05f, .05f, .08f } },
            { Opt.SkillCdReduce,      new[] { .03f, .05f, .05f, .08f, .08f, .12f } },
            { Opt.WeaponCdReduce,     new[] { .04f, .06f, .06f, .10f, .10f, .15f } },
            { Opt.FiercePct,          new[] { .05f, .08f, .08f, .14f, .14f, .20f } },
        };
        static void Range(Opt k, Rarity r, out float lo, out float hi)
        {
            float[] a; int i = r == Rarity.Common ? 0 : r == Rarity.Crafted ? 2 : 4;
            if (Ranges.TryGetValue(k, out a)) { lo = a[i]; hi = a[i + 1]; return; }
            float b = GetBase(k) * TierFactor(r); lo = b * 0.8f; hi = b * 1.2f;   // 파혼 반경(면적) 등 표에 없는 것
        }
    }

    /// <summary>능력치 4종(힘·날램·몸·마음)은 시연판에서 표시 전용. 넋 30마다 1점</summary>
    public static class StatPoints
    {
        public static int Earned(int totalNeokGained) { return totalNeokGained / Balance.STAT_POINT_PER_NEOK; }
    }
}
