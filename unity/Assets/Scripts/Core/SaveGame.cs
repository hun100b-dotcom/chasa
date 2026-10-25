// =============================================================================
// SaveGame.cs — 저장·불러오기 규칙과 설정값 (순수 C#, 유니티 없이 테스트됨)
// 왜 직접 만든 글자 형식? 유니티의 JSON 도구는 Core(엔진 없는 규칙 폴더)에서 못 쓰고, 저장 내용이 작아서
// "이름=값" 줄 묶음으로 충분하다. 잘못된/옛 저장이 와도 게임이 죽지 않게 읽기에 실패하면 null 을 돌려준다.
// 저장하는 것: 위치·시각(날 수와 분)·품계·넋·능력치·도술(명부)·장비·장부(넋·기억·엽전·광석·업)·단서·보스 결과.
// 저장하지 않는 것: 적·얼룩·컷신 진행(불러오면 그 자리에서 새로 시작 — 시연판의 약속).
// =============================================================================
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Chasa.Core
{
    public class SaveSnapshot
    {
        public const int CurrentVersion = 1;
        public int Version = CurrentVersion;
        public float X, Z;                       // 플레이어 위치(월드 m)
        public int ClockDay; public float ClockMinutes;
        public int Neok, Memory, Coin, Ore, Karma, TendoTotal, Hp;   // 장부(+ 체력)
        public int TotalNeok, SkillPointsEarned, SkillPointsSpent, StatPointsEarned, PahonCount, StainPointsEarned, StainPointsSpent;
        public int[] Stats = new int[4];
        public Dictionary<string, int> Learned = new Dictionary<string, int>();
        public List<string> ActiveBar = new List<string>();
        public ItemDef[] Gear = new ItemDef[3];
        public List<string> Clues = new List<string>();
        public int BossOutcome, NamedOutcome;     // 보스 결과(1 천도·2 파혼) / 이름혼 박돌쇠 결과
        public bool OpeningSeen, FuneralShown;    // 오프닝·장례 컷을 이미 봤나(불러오면 다시 틀지 않는다)
        public WeaponId Weapon = WeaponId.Chain, Other = WeaponId.Mace;   // 손에 든 / 등에 멘 무기
        public int[] WeatherNow;                  // 구역별 지금 날씨(Weather 순서, WeatherRules.Zones 순). null 이면 불러올 때 새로 굴린다
        public bool PlagueEased;                  // 3호 처결 뒤 역병 가중치 감소
    }

    public static class SaveGame
    {
        static string Clean(string s) { return (s ?? "").Replace('|', ' ').Replace(',', ' ').Replace(':', ' ').Replace('=', ' ').Replace('\n', ' ').Replace('\r', ' '); }
        static string F(float v) { return v.ToString("R", CultureInfo.InvariantCulture); }
        static float PF(string s) { return float.Parse(s, CultureInfo.InvariantCulture); }

        static string ItemText(ItemDef it)
        {
            if (it == null) return "-";
            var o = new StringBuilder();
            foreach (var op in it.Options) { if (o.Length > 0) o.Append(','); o.Append(op.Kind).Append(':').Append(F(op.Value)); }
            return (int)it.Rarity + "|" + Clean(it.Name) + "|" + (it.Named ? 1 : 0) + "|" + (it.Gradient ? 1 : 0) + "|" + Clean(it.TiltId) + "|" + it.Rerolls + "|" + it.Plus + "|" + it.Sockets + "|" + o;
        }

        static ItemDef ItemFrom(string text, Slot slot)
        {
            if (text == "-") return null;
            var p = text.Split('|');
            if (p.Length < 9) throw new FormatException("item");
            var it = new ItemDef { Slot = slot, Rarity = (Rarity)int.Parse(p[0]), Name = p[1], Named = p[2] == "1", Gradient = p[3] == "1", TiltId = p[4].Length == 0 ? null : p[4], Rerolls = int.Parse(p[5]), Plus = int.Parse(p[6]), Sockets = int.Parse(p[7]) };
            if (p[8].Length > 0)
                foreach (var pair in p[8].Split(','))
                {
                    var kv = pair.Split(':');
                    it.Options.Add(new OptionRoll((Opt)Enum.Parse(typeof(Opt), kv[0]), PF(kv[1])));
                }
            return it;
        }

        public static string Serialize(SaveSnapshot s)
        {
            var b = new StringBuilder();
            Action<string, object> w = (k, v) => b.Append(k).Append('=').Append(v).Append('\n');
            w("v", s.Version); w("x", F(s.X)); w("z", F(s.Z)); w("day", s.ClockDay); w("min", F(s.ClockMinutes));
            w("neok", s.Neok); w("memory", s.Memory); w("coin", s.Coin); w("ore", s.Ore); w("karma", s.Karma); w("tendo", s.TendoTotal); w("hp", s.Hp);
            w("totalneok", s.TotalNeok); w("skE", s.SkillPointsEarned); w("skS", s.SkillPointsSpent); w("stE", s.StatPointsEarned);
            w("pahon", s.PahonCount); w("stainE", s.StainPointsEarned); w("stainS", s.StainPointsSpent);
            w("stats", string.Join(",", s.Stats));
            var l = new List<string>(); foreach (var kv in s.Learned) l.Add(Clean(kv.Key) + ":" + kv.Value); w("learned", string.Join(",", l));
            var a = new List<string>(); foreach (var n in s.ActiveBar) a.Add(Clean(n)); w("bar", string.Join(",", a));
            for (int i = 0; i < s.Gear.Length; i++) w("gear" + i, ItemText(s.Gear[i]));
            var c = new List<string>(); foreach (var n in s.Clues) c.Add(Clean(n)); w("clues", string.Join(",", c));
            w("boss", s.BossOutcome); w("named", s.NamedOutcome); w("opening", s.OpeningSeen ? 1 : 0); w("funeral", s.FuneralShown ? 1 : 0); w("weapon", (int)s.Weapon); w("other", (int)s.Other);
            if (s.WeatherNow != null) w("wx", string.Join(",", s.WeatherNow)); w("plagueEased", s.PlagueEased ? 1 : 0);
            return b.ToString();
        }

        /// <summary>글자에서 읽는다. 형식이 틀리거나 버전이 더 새것이면 null (게임은 새로 시작)</summary>
        public static SaveSnapshot Deserialize(string text)
        {
            if (string.IsNullOrEmpty(text)) return null;
            try
            {
                var d = new Dictionary<string, string>();
                foreach (var line in text.Split('\n')) { int i = line.IndexOf('='); if (i > 0) d[line.Substring(0, i)] = line.Substring(i + 1); }
                if (!d.ContainsKey("v") || int.Parse(d["v"]) > SaveSnapshot.CurrentVersion) return null;
                Func<string, int> I = k => d.ContainsKey(k) ? int.Parse(d[k]) : 0;
                var s = new SaveSnapshot { X = PF(d["x"]), Z = PF(d["z"]), ClockDay = I("day"), ClockMinutes = PF(d["min"]),
                    Neok = I("neok"), Memory = I("memory"), Coin = I("coin"), Ore = I("ore"), Karma = I("karma"), TendoTotal = I("tendo"), Hp = I("hp"),
                    TotalNeok = I("totalneok"), SkillPointsEarned = I("skE"), SkillPointsSpent = I("skS"), StatPointsEarned = I("stE"),
                    PahonCount = I("pahon"), StainPointsEarned = I("stainE"), StainPointsSpent = I("stainS"), BossOutcome = I("boss"), NamedOutcome = I("named"), OpeningSeen = I("opening") == 1, FuneralShown = I("funeral") == 1, Weapon = (WeaponId)I("weapon"), Other = d.ContainsKey("other") ? (WeaponId)I("other") : WeaponId.Mace };
                var st = d.ContainsKey("stats") ? d["stats"].Split(',') : new string[0];
                for (int i = 0; i < s.Stats.Length; i++) s.Stats[i] = i < st.Length ? int.Parse(st[i]) : GrowthState.StatBase;
                if (d.ContainsKey("learned") && d["learned"].Length > 0)
                    foreach (var pair in d["learned"].Split(',')) { var kv = pair.Split(':'); if (SkillTree.Find(kv[0]) != null) s.Learned[kv[0]] = int.Parse(kv[1]); }   // 지워진 도술 이름은 건너뛴다(옛 저장 호환)
                if (d.ContainsKey("bar") && d["bar"].Length > 0) foreach (var n in d["bar"].Split(',')) if (SkillTree.Find(n) != null && s.Learned.ContainsKey(n)) s.ActiveBar.Add(n);
                for (int i = 0; i < s.Gear.Length; i++) s.Gear[i] = d.ContainsKey("gear" + i) ? ItemFrom(d["gear" + i], (Slot)i) : null;
                if (d.ContainsKey("clues") && d["clues"].Length > 0) s.Clues.AddRange(d["clues"].Split(','));
                s.PlagueEased = I("plagueEased") == 1;
                if (d.ContainsKey("wx") && d["wx"].Length > 0) { var wp = d["wx"].Split(','); s.WeatherNow = new int[wp.Length]; for (int i = 0; i < wp.Length; i++) s.WeatherNow[i] = Math.Max(0, Math.Min(4, int.Parse(wp[i]))); }
                return s;
            }
            catch (Exception) { return null; }
        }

        /// <summary>지금 게임 상태를 저장 묶음으로 (위치·시각은 부르는 쪽이 채운다)</summary>
        public static SaveSnapshot Capture(GrowthState g, Ledger l, Equipment eq, ClueBook clues)
        {
            var s = new SaveSnapshot
            {
                Neok = l.Neok, Memory = l.Memory, Coin = l.Coin, Ore = l.Ore, Karma = l.Karma, TendoTotal = l.TendoTotal, Hp = l.Hp,
                TotalNeok = g.TotalNeok, SkillPointsEarned = g.SkillPointsEarned, SkillPointsSpent = g.SkillPointsSpent, StatPointsEarned = g.StatPointsEarned,
                PahonCount = g.PahonCount, StainPointsEarned = g.StainPointsEarned, StainPointsSpent = g.StainPointsSpent
            };
            for (int i = 0; i < 4; i++) s.Stats[i] = g.Stats[i];
            foreach (var kv in g.Learned) s.Learned[kv.Key] = kv.Value;
            s.ActiveBar.AddRange(g.ActiveBar);
            for (int i = 0; i < 3; i++) s.Gear[i] = eq.Get((Slot)i);
            s.Clues.AddRange(clues.All);
            return s;
        }

        /// <summary>저장 묶음을 게임 상태에 되돌린다(위치·시각·무기는 부르는 쪽이 따로)</summary>
        public static void Apply(SaveSnapshot s, GrowthState g, Ledger l, Equipment eq, ClueBook clues)
        {
            l.Neok = s.Neok; l.Memory = s.Memory; l.Coin = s.Coin; l.Ore = s.Ore; l.Karma = s.Karma; l.TendoTotal = s.TendoTotal;
            g.TotalNeok = s.TotalNeok; g.Rank = GrowthState.RankFor(s.TotalNeok);
            g.SkillPointsEarned = s.SkillPointsEarned; g.SkillPointsSpent = s.SkillPointsSpent; g.StatPointsEarned = s.StatPointsEarned;
            g.PahonCount = s.PahonCount; g.StainPointsEarned = s.StainPointsEarned; g.StainPointsSpent = s.StainPointsSpent;
            for (int i = 0; i < 4; i++) g.Stats[i] = s.Stats[i];
            g.Learned.Clear(); foreach (var kv in s.Learned) g.Learned[kv.Key] = kv.Value;
            g.ActiveBar.Clear(); g.ActiveBar.AddRange(s.ActiveBar);
            for (int i = 0; i < 3; i++) eq.Put((Slot)i, s.Gear[i]);
            foreach (var c in s.Clues) clues.Add(c);
            // 체력은 최대 체력(장비·몸 능력치)을 다시 계산한 뒤 부르는 쪽이 맞춘다(l.Hp = min(s.Hp, MaxHp))
        }
    }

    /// <summary>설정값: 소리 크기(전체·배경음·효과음)와 화면 흔들림 세기. 저장 글자 한 줄로 오간다</summary>
    public class GameSettings
    {
        static float Pf(string t) { return float.Parse(t, CultureInfo.InvariantCulture); }
        public float Master = 1f, Bgm = 0.8f, Sfx = 1f, Shake = 1f;
        public static GameSettings Clamp(GameSettings s)
        {
            s.Master = Math.Max(0f, Math.Min(1f, s.Master)); s.Bgm = Math.Max(0f, Math.Min(1f, s.Bgm));
            s.Sfx = Math.Max(0f, Math.Min(1f, s.Sfx)); s.Shake = Math.Max(0f, Math.Min(1.5f, s.Shake));
            return s;
        }
        public string Serialize() { return string.Format(CultureInfo.InvariantCulture, "{0},{1},{2},{3}", Master, Bgm, Sfx, Shake); }
        public static GameSettings Parse(string text)
        {
            var s = new GameSettings();
            try
            {
                var p = (text ?? "").Split(',');
                if (p.Length == 4) { s.Master = Pf(p[0]); s.Bgm = Pf(p[1]); s.Sfx = Pf(p[2]); s.Shake = Pf(p[3]); }
            }
            catch (Exception) { s = new GameSettings(); }
            return Clamp(s);
        }
    }
}
