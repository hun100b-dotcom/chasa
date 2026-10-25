// =============================================================================
// Sim.cs — 1막(첫 밤 셋 + 1호 보스 나루 영감) 자동 시뮬. 천도만 / 파혼만 / 섞기(상황 판단) / 섞기(반반)를 같은 조건에서 돌려
// 넋·기억·엽전·업·시간·위험(체력)을 비교한다. 한쪽이 항상 정답이 되는지 보려는 것.
// 규칙(보상·업·캐스팅 시간·수치)은 Core 를 그대로 쓰고, 전투는 단순 기대값 모델이다(아래 가정, 모두 임시):
//   - 한 번에 마주치는 주변 적 수 n(0~2), 혼 종류 비율, 죽이는 속도(초당 34), 맞을 확률(움직이며 0.30 / 천도 시전 중 0.75)
//   - 파혼 폭발은 주변 적에게 PAHON_DAMAGE 를 먼저 넣어 다음 처치를 빠르게 한다
//   - 회복: 4초 넘게 안 맞으면 초당 2, 회복약 2개(체력 35 이하에서 +40)
// =============================================================================
using System;
using System.Collections.Generic;
using Chasa.Core;

enum Strat { TendoOnly, PahonOnly, Adaptive, CoinFlip }

class RunResult
{
    public bool Died, DiedInNight; public int Tendo, Pahon, Neok, Memory, Coin, Karma, Rank; public double Seconds, Damage, RestSeconds; public int Rests; public bool BossTendo, BossFought; public int Clues;
    public double[] QuotaSeconds = new double[3];   // 밤마다 명부 몫(천도 NIGHT_QUOTA)을 채운 시각(못 채우면 NaN)
}

static class Sim
{
    const double BaseDps = 34.0, HitMove = 0.30, HitBoss = 0.12, HitBossAdds = 0.20, HitCast = 0.75, TravelAvg = 8.0, Approach = 0.6;
    const int Nights = 3;
    static WeaponDef Wd = WeaponDef.Chain;   // 이번 판에 든 무기
    // 무기별 전투 가정(WeaponTable 콤보 합/시간에서): 단일 목표 초당 피해 비율 r(철삭 1.0 기준)과 주변 적 한 마리당 추가 비율 g(범위·관통), 받는 피해 배율(붓은 멀리서 쏴 덜 맞음)
    static double WR(WeaponId w) { switch (w) { case WeaponId.Mace: return 0.91; case WeaponId.Bell: return 0.70; case WeaponId.Trident: return 0.78; case WeaponId.Brush: return 0.65; default: return 1.0; } }
    static double WG(WeaponId w) { switch (w) { case WeaponId.Mace: return 0.15; case WeaponId.Bell: return 0.80; case WeaponId.Trident: return 0.40; case WeaponId.Brush: return 0.0; default: return 0.20; } }
    static double WTake(WeaponId w) { return w == WeaponId.Brush ? 0.75 : 1.0; }
    static bool Growth = true;   // 성장(품계 힘 몰기·장비 손보기·얼룩 점수)을 전투에 직접 넣는다. --nogrowth 면 끈다(옛 시뮬)
    const double MainOptDmg = 0.055;   // 손보기 대상 주옵션을 피해 옵션 평균(기본 6% x 등급 0.5~1.1)으로 가정
    static readonly int[] EnhCost = { 30, 60, 100, 150, 220 };
    const double RestBelow = 45, ShrineWalk = 14.0;   // 체력이 이 밑이면 서낭당(왕복 약 14초)에서 쉰다

    static int Main(string[] args)
    {
        int runs = args.Length > 0 && !args[0].StartsWith("--") ? int.Parse(args[0]) : 4000;
        foreach (var a in args) if (a == "--nogrowth") Growth = false;
        if (Array.IndexOf(args, "--weapons") >= 0) return WeaponTable(runs);
        Console.WriteLine("1막 시뮬: 첫 밤 " + Nights + "개 + 1호 보스, 각 전략 " + runs + "판. 밤 " + Balance.NIGHT_DURATION + "초, 몫 " + Balance.NIGHT_QUOTA + ", 체력 " + Balance.PLAYER_MAX_HP);
        var results = new Dictionary<Strat, List<RunResult>>();
        foreach (Strat s in Enum.GetValues(typeof(Strat)))
        {
            var rng = new Random(12345);
            var list = new List<RunResult>();
            for (int i = 0; i < runs; i++) list.Add(Play(s, rng));
            results[s] = list;
        }
        string[] names = { "천도만", "파혼만", "섞기(상황 판단)", "섞기(반반)" };
        Console.WriteLine("\n| 전략 | 생존 | 천도 | 파혼 | 넋 | 기억 | 엽전 | 업(끝) | 품계 | 걸린 시간(분) | 맞은 피해 | 쉬러 간 횟수 | 몫 채운 밤 | 보스 천도 | 단서 |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
        int k = 0;
        foreach (Strat s in Enum.GetValues(typeof(Strat)))
        {
            var L = results[s];
            double surv = Avg(L, r => r.Died ? 0 : 1), quotaN = 0;
            foreach (var r in L) foreach (var q in r.QuotaSeconds) if (!double.IsNaN(q)) quotaN++;
            Console.WriteLine("| " + names[k++] + " | " + (surv * 100).ToString("0") + "% | " + Avg(L, r => r.Tendo).ToString("0.0") + " | " + Avg(L, r => r.Pahon).ToString("0.0") + " | " + Avg(L, r => r.Neok).ToString("0") +
                " | " + Avg(L, r => r.Memory).ToString("0.0") + " | " + Avg(L, r => r.Coin).ToString("0") + " | " + Avg(L, r => r.Karma).ToString("0.0") + " | " + Avg(L, r => r.Rank).ToString("0.0") +
                " | " + (Avg(L, r => r.Seconds) / 60).ToString("0.0") + " | " + Avg(L, r => r.Damage).ToString("0") + " | " + Avg(L, r => r.Rests).ToString("0.0") + " | " + (quotaN / (L.Count * Nights) * 100).ToString("0") + "% | " + (Avg(L, r => r.BossTendo ? 1 : 0) * 100).ToString("0") + "% | " + Avg(L, r => r.Clues).ToString("0.0") + " |");
        }
        // 가치 환산: 엽전 1개를 넋 w 로 볼 때의 분당 가치. 어느 w 에서도 한 전략이 늘 1등이면 '정답 고정'
        Console.WriteLine("\n분당 가치 = (넋 + 기억×4 + 엽전×w) ÷ 걸린 분.  w = 엽전 1개의 가치(넋 환산). 위험 = 맞은 피해 ÷ 분");
        Console.WriteLine("| w | " + string.Join(" | ", names) + " | 1등 |");
        Console.WriteLine("|---|---|---|---|---|---|");
        var passRows = new List<string>();
        foreach (double w in new[] { 0.5, 1.0, 1.15, 1.3, 1.45, 2.0 })
        {
            var vals = new List<double>(); int best = 0;
            foreach (Strat s in Enum.GetValues(typeof(Strat)))
            {
                var L = results[s]; double v = 0, mins = 0;
                foreach (var r in L) { v += r.Neok + 4.0 * r.Memory + w * r.Coin; mins += r.Seconds / 60; }
                vals.Add(v / Math.Max(1e-9, mins)); if (vals[vals.Count - 1] > vals[best]) best = vals.Count - 1;
            }
            Console.WriteLine("| " + w + " | " + string.Join(" | ", vals.ConvertAll(x => x.ToString("0.0"))) + " | " + names[best] + " |");
            // 기획 합격 기준: ① 섞기(상황 판단)가 1등 ② 천도만·파혼만 차이 20% 안 (③ 보스·④ 위험은 아래 표에서 따로)
            double hi = Math.Max(vals[0], vals[1]), lo = Math.Min(vals[0], vals[1]);
            passRows.Add("| " + w + " | " + (best == 2 ? "O" : "X") + " | " + (hi > 0 && (hi - lo) / hi <= 0.20 ? "O" : "X") + " | " + ((vals[0] - vals[1]) / hi * 100).ToString("0") + "% |");
        }
        Console.WriteLine("\n| w | ① 섞기 1등 | ② 천도·파혼 20% 안 | 천도-파혼 차이 |");
        Console.WriteLine("|---|---|---|---|");
        foreach (var row in passRows) Console.WriteLine(row);
        Console.WriteLine("| 밤에서 쓰러짐 | " + string.Join(" | ", ((Func<List<string>>)(() => { var o = new List<string>(); foreach (Strat s in Enum.GetValues(typeof(Strat))) o.Add((Avg(results[s], r => r.DiedInNight ? 1 : 0) * 100).ToString("0") + "%"); return o; }))()) + " | |");
        var qt = new List<string>();
        foreach (Strat s in Enum.GetValues(typeof(Strat))) { double sum = 0; int n = 0; foreach (var r in results[s]) foreach (var q in r.QuotaSeconds) if (!double.IsNaN(q)) { sum += q; n++; } qt.Add(n == 0 ? "-" : (sum / n).ToString("0") + "초"); }
        Console.WriteLine("| 몫(천도 3) 채우는 데 걸린 시간 | " + string.Join(" | ", qt) + " | |");
        var risk = new List<string>(); foreach (Strat s in Enum.GetValues(typeof(Strat))) { double d = 0, m = 0; foreach (var r in results[s]) { d += r.Damage; m += r.Seconds / 60; } risk.Add((d / m).ToString("0.0")); }
        Console.WriteLine("| 위험(분당 피해) | " + string.Join(" | ", risk) + " | |");
        // 결말 A(최종 눕히기) 조건: 기억 충분 + 업 < 60 은 다음 막에서 검토 — 여기서는 업·기억만 보고한다
        return 0;
    }

    /// <summary>무기 5계열을 각각 돌려 기획 기준 ①~④ 를 w=1.3 에서 판정한다</summary>
    static int WeaponTable(int runs)
    {
        const double w = 1.3;
        Console.WriteLine("무기별 판정 (w=" + w + ", 각 전략 " + runs + "판). 가치/분 = (넋+기억x4+엽전xw)/분");
        Console.WriteLine("| 무기 | 천도만 | 파혼만 | 섞기(상황) | 섞기(반반) | 1등 | ① 섞기1등 | ② 천도·파혼 20%안 | ③ 파혼만 생존·보스 | ④ 위험 천도만 최대 | 위험(천/파/섞) |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|---|");
        foreach (var wid in new[] { WeaponId.Chain, WeaponId.Mace, WeaponId.Bell, WeaponId.Trident, WeaponId.Brush })
        {
            Wd = WeaponDef.Get(wid);
            var v = new double[4]; var risk = new double[4]; double pahonSurv = 0, pahonBoss = 0; int k = 0;
            foreach (Strat s in Enum.GetValues(typeof(Strat)))
            {
                var rng = new Random(12345); var L = new List<RunResult>();
                for (int i = 0; i < runs; i++) L.Add(Play(s, rng));
                double val = 0, mins = 0, dmg = 0;
                foreach (var r in L) { val += r.Neok + 4.0 * r.Memory + w * r.Coin; mins += r.Seconds / 60; dmg += r.Damage; }
                v[k] = val / mins; risk[k] = dmg / mins;
                if (s == Strat.PahonOnly) { pahonSurv = Avg(L, r => r.Died ? 0 : 1); pahonBoss = Avg(L, r => r.BossFought ? 1 : 0); }
                k++;
            }
            int best = 0; for (int i = 1; i < 4; i++) if (v[i] > v[best]) best = i;
            string[] nm = { "천도만", "파혼만", "섞기(상황)", "섞기(반반)" };
            double hi = Math.Max(v[0], v[1]), lo = Math.Min(v[0], v[1]);
            bool c1 = best == 2, c2 = (hi - lo) / hi <= 0.20, c3 = pahonSurv >= 0.95 && pahonBoss >= 0.95, c4 = risk[0] >= risk[1] && risk[0] >= risk[2] && risk[0] >= risk[3];
            Console.WriteLine("| " + Wd.Name + " | " + v[0].ToString("0.0") + " | " + v[1].ToString("0.0") + " | " + v[2].ToString("0.0") + " | " + v[3].ToString("0.0") + " | " + nm[best] + " | " + (c1 ? "O" : "X") + " | " + (c2 ? "O" : "X") + " (" + ((v[0] - v[1]) / hi * 100).ToString("0") + "%) | " + (c3 ? "O" : "X") + "(생존" + (pahonSurv * 100).ToString("0") + "%)" + " | " + (c4 ? "O" : "X") + " | " + risk[0].ToString("0") + "/" + risk[1].ToString("0") + "/" + risk[2].ToString("0") + " |");
        }
        return 0;
    }

    static double Avg(List<RunResult> L, Func<RunResult, double> f) { double s = 0; foreach (var r in L) s += f(r); return s / L.Count; }

    static bool WantTendo(Strat s, Random rng, int others, double hp)
    {
        switch (s)
        {
            case Strat.TendoOnly: return true;
            case Strat.PahonOnly: return false;
            case Strat.Adaptive: return others <= 1 && hp > 30;   // 주변이 붐비거나 위험하면 파혼, 한가하면 천도
            default: return rng.NextDouble() < 0.5;
        }
    }

    static int Pick(Random rng, double[] w) { double x = rng.NextDouble(), a = 0; for (int i = 0; i < w.Length; i++) { a += w[i]; if (x < a) return i; } return w.Length - 1; }

    static RunResult Play(Strat s, Random rng)
    {
        var res = new RunResult(); var led = new Ledger(); var g = new GrowthState();
        double hp = led.MaxHp; int potions = Balance.FIRST_NIGHT_HEAL; double bonusPool = 0; bool namedTendoed = false;
        int enhSteps = 0, stainPts = 0, pahonCnt = 0; var slotLv = new int[3]; int spent = 0; double coinAcc = 0;
        // 지금 공격력: 품계가 오르면 능력치 5점을 전부 힘에(+1%/점), 손보기 한 단계 = 주옵션 +6%(=피해 약 +0.33%)
        Func<double> dps = () => !Growth ? BaseDps : BaseDps * (1 + GrowthStr(GrowthState.RankFor(led.Neok))) * (1 + Balance.ENHANCE_PCT * MainOptDmg * enhSteps);
        for (int night = 0; night < Nights && hp > 0; night++)
        {
            double t = 0, lastTendoAt = -99, sinceHit = 99; int sentTonight = 0; res.QuotaSeconds[night] = double.NaN;
            bool namedDone = false;
            while (t < Balance.NIGHT_DURATION && hp > 0)
            {
                // 다음 혼을 찾아간다(이동). 맞지 않은 시간만큼 회복
                double travel = TravelAvg * (0.5 + rng.NextDouble());
                t += travel; sinceHit += travel; hp = Math.Min(led.MaxHp, hp + Balance.REGEN_PER_SEC * Math.Max(0, sinceHit - Balance.REGEN_DELAY > 0 ? Math.Min(travel, sinceHit - Balance.REGEN_DELAY) : 0));
                if (t >= Balance.NIGHT_DURATION) break;
                // 혼 하나: 종류, 주변 적 수
                bool lump = rng.NextDouble() < Balance.LUMP_SPAWN_CHANCE;
                int kind = Pick(rng, new[] { 0.5, 0.3, 0.2 });   // 갓 죽은·해 넘긴·오래된
                int others = Pick(rng, new[] { 0.3, 0.4, 0.3 });
                bool named = !namedDone && night == Nights - 1 && sentTonight >= Balance.NIGHT_QUOTA - 1 && !lump;   // 몫의 마지막은 이름혼(곽 뱃꾼 대용)
                // 죽여서 무릎 꿇리기
                double maed = lump ? Balance.MAEDHIM_LUMP : Balance.MAEDHIM_NORMAL;
                double use = Math.Min(maed - 10, bonusPool); bonusPool -= use;
                if (Wd.Id == WeaponId.Mace)   // 땅울림(Q, 6초마다): 접근하며 한 번 — 목표 20 + 주변 적마다 20(다음 싸움에서 이미 깎인 몫으로 쌓임), 기절 0.8초 동안 안 맞음
                {
                    double q = Math.Min(maed - 10 - use, Balance.MACE_QUAKE_DAMAGE); use += q;
                    bonusPool += Balance.MACE_QUAKE_DAMAGE * others;
                }   // 앞선 파혼 폭발이 이미 깎아 둔 몫
                double kill = (maed - use) / (dps() * WR(Wd.Id) * (1 + WG(Wd.Id) * Math.Min(others, 2))) + 0.5;
                double take = (others + 1) * (kill / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * HitMove * WTake(Wd.Id);
                Hit(ref hp, ref sinceHit, ref res, take); t += kill; sinceHit = take > 0 ? 0 : sinceHit + kill;
                if (hp <= 0) break;
                hp = Heal(hp, ref potions);
                // 선택
                bool tendo = !lump && WantTendo(s, rng, others, hp);
                if (named && s == Strat.TendoOnly) tendo = true;
                if (tendo)
                {
                    bool chain = t - lastTendoAt <= Balance.TENDO_CHAIN_WINDOW + Wd.ChainWindowAddS;
                    double cast = CoreRules.CastTime(chain) * Wd.CastTimeMult;
                    double dmg = others * (cast / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * HitCast;
                    Hit(ref hp, ref sinceHit, ref res, dmg); t += cast + Approach; if (dmg > 0) sinceHit = 0;
                    if (hp <= 0) break;
                    { int nb = led.Neok; led.CompleteTendo(); led.Neok += (int)Math.Round((led.Neok - nb) * Wd.NeokPct); } res.Tendo++; sentTonight++; lastTendoAt = t;
                    if (named) { namedDone = true; namedTendoed = true; }
                    if (sentTonight == Balance.NIGHT_QUOTA) res.QuotaSeconds[night] = t;
                }
                else
                {
                    t += 0.25 + Approach; led.DoPahon(); res.Pahon++;
                    if (Growth)
                    {
                        pahonCnt++; if (pahonCnt % Balance.PAHON_STAIN_POINT_EVERY == 0) stainPts++;
                        coinAcc += Balance.PAHON_COIN * 0.2 * Math.Min(2, stainPts); int whole = (int)coinAcc; led.Coin += whole; coinAcc -= whole;   // 얼룩 점수 -> 노잣돈 2단계(+20%/단계)
                    }
                    bonusPool += others * Balance.PAHON_DAMAGE * Wd.PahonDamageMult * (Growth ? 1 + 0.1 * Math.Max(0, Math.Min(2, stainPts - 2)) : 1);   // 폭발이 이웃들을 먼저 깎아 둔다(남는 얼룩 점수는 큰 폭발로)
                    if (named) namedDone = true;
                }
                hp = Heal(hp, ref potions);
                if (hp < RestBelow) { double rest = ShrineWalk + (led.MaxHp - hp) / Balance.SHRINE_HEAL_PER_SEC; t += rest; res.RestSeconds += rest; res.Rests++; hp = led.MaxHp; sinceHit = 99; }   // 서낭당에 돌아가 쉰다(시간이 비용)
            }
            res.Seconds += t;
            // 낮: 단서(1호 보스). 지켜보기·만져 보기는 늘, 엿듣기는 업 30 미만일 때만, 밤 대체 단서는 이름혼을 천도했을 때만
            if (night == Nights - 1) { res.Clues = 2 + (Eavesdrop.Mode(led.Karma, true, true) != EavesMode.Closed ? 1 : 0) + (namedTendoed ? 1 : 0); }
            if (Growth)   // 낮: 가진 엽전으로 칸 셋을 값싼 단계부터 손본다
                while (true)
                {
                    int best = -1; for (int k = 0; k < 3; k++) if (slotLv[k] < Balance.ENHANCE_MAX && (best < 0 || slotLv[k] < slotLv[best])) best = k;
                    if (best < 0 || led.Coin - spent < EnhCost[slotLv[best]]) break;
                    spent += EnhCost[slotLv[best]]; slotLv[best]++; enhSteps++;
                }
            hp = led.MaxHp; potions = Math.Max(potions, Balance.FIRST_NIGHT_HEAL);   // 서낭당·낮에 회복
        }
        res.DiedInNight = hp <= 0;
        // 1호 보스
        if (hp > 0)
        {
            res.BossFought = true; bool canTendo = Math.Min(res.Clues, Balance.BOSS_CLUES_REQUIRED) >= Balance.BOSS_CLUES_REQUIRED;
            double kill = Balance.BOSS_S1_MAEDHIM / (dps() * WR(Wd.Id)) + 1.0, sinceHit = 99;
            double take = (kill / (Balance.ENEMY_ATTACK_INTERVAL / Balance.BOSS_S1_SPEED_MULT)) * Balance.BOSS_S1_DAMAGE * HitBoss + 2 * (kill / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * HitBossAdds;   // 보스는 예비동작이 길어 읽힌다   // 보스 + 올라오는 혼 2마리
            Hit(ref hp, ref sinceHit, ref res, take); res.Seconds += kill;
            if (hp > 0) hp = Heal(hp, ref potions);
            if (hp > 0)
            {
                bool tendo = canTendo && (s == Strat.TendoOnly || (s == Strat.Adaptive && hp > 40) || (s == Strat.CoinFlip && rng.NextDouble() < 0.5));
                if (tendo)
                {
                    double dmg = 2 * (Balance.BOSS_TENDO_CAST_TIME / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * HitCast;   // 시전 중 올라온 혼에 맞음
                    Hit(ref hp, ref sinceHit, ref res, dmg); res.Seconds += Balance.BOSS_TENDO_CAST_TIME;
                    if (hp > 0) { led.CompleteBossTendo(); res.BossTendo = true; }
                }
                else if (hp > 0) { res.Seconds += 0.5; led.DoPahon(true); }
            }
        }
        res.Died = hp <= 0; res.Neok = led.Neok; res.Memory = led.Memory; res.Coin = led.Coin; res.Karma = led.Karma; res.Rank = GrowthState.RankFor(led.Neok);
        return res;
    }

    static double GrowthStr(int rank) { return 0.05 * Math.Max(0, rank - 1); }   // 품계당 힘 5점 x 1%

    static void Hit(ref double hp, ref double sinceHit, ref RunResult res, double dmg) { hp -= dmg; res.Damage += dmg; }
    static double Heal(double hp, ref int potions) { if (hp > 0 && hp <= 35 && potions > 0) { potions--; return Math.Min(Balance.PLAYER_MAX_HP, hp + 40); } return hp; }
}
