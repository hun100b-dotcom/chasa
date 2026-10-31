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
    public bool Died, DiedInNight; public int Vanished; public int Tendo, Pahon, Neok, Memory, Coin, Karma, Rank; public double Seconds, Damage, RestSeconds; public int Rests; public bool BossTendo, BossFought; public int Clues;
    public double[] QuotaSeconds = new double[3];   // 밤마다 명부 몫(천도 NIGHT_QUOTA)을 채운 시각(못 채우면 NaN)
}

static class Sim
{
    static readonly double HitScale = Env("HIT_SCALE", 1.0);   // 신참 민감도 검사용: 맞을 확률을 이 배수만큼 키운다(기본 1)
    static readonly double BaseDps = 34.0, HitMove = 0.30 * HitScale, HitBoss = 0.12 * HitScale, HitBossAdds = 0.20 * HitScale, HitCast = Math.Min(1.0, 0.75 * HitScale), TravelAvg = 8.0, Approach = 0.6;
    const int Nights = 3;
    static WeaponDef Wd = WeaponDef.Chain;   // 이번 판에 든 무기
    // 무기별 전투 가정(WeaponTable 콤보 합/시간에서): 단일 목표 초당 피해 비율 r(철삭 1.0 기준)과 주변 적 한 마리당 추가 비율 g(범위·관통), 받는 피해 배율(붓은 멀리서 쏴 덜 맞음)
    static double WR(WeaponId w) { switch (w) { case WeaponId.Mace: return 0.91; case WeaponId.Bell: return 0.70; case WeaponId.Trident: return 0.78; case WeaponId.Brush: return 0.65; default: return 1.0; } }
    static double WG(WeaponId w) { switch (w) { case WeaponId.Mace: return 0.15; case WeaponId.Bell: return 0.80; case WeaponId.Trident: return 0.40; case WeaponId.Brush: return 0.0; default: return 0.20; } }
    static double WTake(WeaponId w) { return w == WeaponId.Brush ? 0.75 : 1.0; }
    // 날씨(기획서 8절). null = 날씨 무시(옛 시뮬). Fixed = 밤 세 개를 같은 날씨로, Mixed = 솔고개 가중치로 밤마다(+밤 중간 25% 다시) 굴림
    static Weather? WxFixed = null; static bool WxMixed = false; static double PTendo = 0.5;
    static WeatherEffect Fx = WeatherRules.Effect(Weather.Clear, true);
    // 혼 유형 보상은 환경변수가 아니라 게임과 같은 Balance 상수를 읽는다(시뮬과 실제가 어긋나지 않게)
    static readonly double MOTE_COIN = Balance.MOTE_CHAIN_COIN_MULT, MOTE_KARMA = Balance.MOTE_CHAIN_KARMA, BURIED_NEOK = Balance.BURIED_TENDO_NEOK_MULT; static readonly int WAIL_MEM = Balance.WAIL_TENDO_MEMORY;
    static double MixMote = 0, MixWail = 0, MixBuried = 0;   // 혼 3유형 비율(%) — 0 이면 옛 시뮬(보통 혼만). --types 표가 구역별로 채운다
    // 2막(기획 10-25, act2-souls.md): --act2 표가 구역별로 채운다. 기본값은 1막 그대로
    static bool Act2 = false; static double A2Maed = 1, A2Dmg = 1, A2Reward = 1, A2Lump = -1, A2NumPct = 0, A2OrePct = 0; static int A2StartNeok = 0, A2StartEnh = 0;
    static int A2BossMaed = 960, A2BossDmg = 22;
    static double A2CoinMult = Env("A2_COIN", 0.75), A2NumNeok = Env("A2_NUMNEOK", 1.3);   // 기획 10-25 확정안: 고리 보상 중 엽전은 넋 몫의 75%만, 숫자 혼 천도 넋 x1.3 (코드팀: Balance 상수로 옮길 것)
    static bool A2B08 = false;
    // 3막(기획 10-25, act3-souls.md): 물 혼(⑤ 시신 없음: 천도 캐스팅 -0.5초, 하한 0.5초 / 밀물 20초 안에 못 붙잡으면 사라짐)·무적 혼(⑥ 별명을 못 들었으면 천도 불가)
    // 시즌 2(기획 season2-souls-draft): 1 돌아선 혼(⑦ 천도 넋 x0.6·기억+1) / 2 잠긴 숫자 혼(⑧ 이름 되찾은 비율만 천도, 캐스팅+0.5·넋x1.3) / 3 이름 조각(⑩ 셋을 이어야 천도, 넋 x2.4, 파혼은 셋 다)
    static double S2TurnPct = 0, S2LockPct = 0, S2FragPct = 0, S2Rest = Env("S2_REST", 0.5), S2FragMult = Env("S2_FRAG", 2.7), S2TurnMult = Env("S2_TURN", 0.85);
    static double A3WaterPct = 0, A3MujeokPct = 0, A3Heard = Env("A3_HEARD", 0.6), A3TideP = Env("A3_TIDE", 0.3), A3TideWin = 20;   // B-08 천도 뒤: ④ 숫자 혼이 이름을 되찾음(인 없음 → 흐림, 캐스팅 +0.5 → +0.25)
    static double Env(string k, double d) { var v = Environment.GetEnvironmentVariable(k); return v == null ? d : double.Parse(v, System.Globalization.CultureInfo.InvariantCulture); }
    const int OreCoinValue = 5;   // 광석 1개를 엽전 몇 닢 값으로 칠지(시뮬 가치 계산용 가정: 매듭 올리기 3광석 ≈ 손보기 1단계 일부)
    static bool Growth = true;   // 성장(품계 힘 몰기·장비 손보기·얼룩 점수)을 전투에 직접 넣는다. --nogrowth 면 끈다(옛 시뮬)
    const double MainOptDmg = 0.055;   // 손보기 대상 주옵션을 피해 옵션 평균(기본 6% x 등급 0.5~1.1)으로 가정
    static readonly int[] EnhCost = { 30, 60, 100, 150, 220 };
    const double RestBelow = 45, ShrineWalk = 14.0;   // 체력이 이 밑이면 서낭당(왕복 약 14초)에서 쉰다

    static int Main(string[] args)
    {
        int runs = args.Length > 0 && !args[0].StartsWith("--") ? int.Parse(args[0]) : 4000;
        foreach (var a in args) if (a == "--nogrowth") Growth = false;
        if (Array.IndexOf(args, "--weapons") >= 0) return WeaponTable(runs);
        if (Array.IndexOf(args, "--weather") >= 0) return WeatherTable(runs);
        if (Array.IndexOf(args, "--types") >= 0) return TypesTable(runs);
        if (Array.IndexOf(args, "--act2") >= 0) return Act2Table(runs, args);
        if (Array.IndexOf(args, "--act3") >= 0) return Act3Table(runs, args);
        if (Array.IndexOf(args, "--s2") >= 0) return S2Table(runs, args);
        if (Array.IndexOf(args, "--curve") >= 0) return CurveTable(runs, args);
        if (Array.IndexOf(args, "--act1") >= 0) return Act1Table(runs, args);
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

    /// <summary>밤 하나의 날씨 효과를 정한다(고정이면 그 날씨, 섞기면 솔고개 밤 가중치로 굴림, 아니면 맑음)</summary>
    static WeatherEffect NightFx(Random rng)
    {
        if (WxFixed.HasValue) return WeatherRules.Effect(WxFixed.Value, true);
        if (WxMixed) return WeatherRules.Effect(WeatherRules.Roll("솔고개", true, (float)rng.NextDouble()), true);
        return WeatherRules.Effect(Weather.Clear, true);
    }

    static double ValuePerMin(List<RunResult> L, double w) { double v = 0, m = 0; foreach (var r in L) { v += r.Neok + 4.0 * r.Memory + w * r.Coin; m += r.Seconds / 60; } return v / Math.Max(1e-9, m); }
    static double RiskPerMin(List<RunResult> L) { double d = 0, m = 0; foreach (var r in L) { d += r.Damage; m += r.Seconds / 60; } return d / Math.Max(1e-9, m); }
    static List<RunResult> RunMany(Strat s, int runs) { var rng = new Random(12345); var L = new List<RunResult>(); for (int i = 0; i < runs; i++) L.Add(Play(s, rng)); return L; }

    /// <summary>날씨별 판정표: 기획서 8절 합격 기준 ①~③ (w=1.3)</summary>
    static int WeatherTable(int runs)
    {
        const double w = 1.3;
        Console.WriteLine("날씨 시뮬 (철삭, w=" + w + ", 각 전략 " + runs + "판). 밤 세 개를 같은 날씨로 고정해 돌린다. 가치/분 = (넋+기억x4+엽전xw)/분");
        Console.WriteLine("| 날씨 | 천도만 | 파혼만 | 섞기(상황) | 섞기(반반) | 1등 | 천도-파혼 차이 | 최적 천도 비율 | 생존(천/파/섞) | 위험(천/파/섞) |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|");
        string[] wn = { "맑음", "흐림", "비", "안개", "역병 안개" }; var best = new double[5]; var gap = new double[5];
        string[] nm = { "천도만", "파혼만", "섞기(상황)", "섞기(반반)" };
        for (int wi = 0; wi < 5; wi++)
        {
            WxFixed = (Weather)wi; WxMixed = false; Fx = WeatherRules.Effect(WxFixed.Value, true);
            var v = new double[4]; var risk = new double[3]; var surv = new double[3]; int k = 0;
            foreach (Strat st in Enum.GetValues(typeof(Strat)))
            {
                PTendo = 0.5; var L = RunMany(st, runs); v[k] = ValuePerMin(L, w);
                if (k < 3) { risk[k] = RiskPerMin(L); surv[k] = Avg(L, r => r.Died ? 0 : 1); }
                k++;
            }
            int b = 0; for (int i = 1; i < 4; i++) if (v[i] > v[b]) b = i;
            double hi = Math.Max(v[0], v[1]), lo = Math.Min(v[0], v[1]); gap[wi] = (hi - lo) / hi;
            // 최적 천도 비율: 섞기 전략에서 천도를 고르는 확률 p 를 0~1 로 훑어 가치/분이 가장 큰 p
            double bp = 0, bv = -1;
            for (double p = 0; p <= 1.0001; p += 0.1) { PTendo = p; var L = RunMany(Strat.CoinFlip, runs); double vv = ValuePerMin(L, w); if (vv > bv) { bv = vv; bp = p; } }
            best[wi] = bp; PTendo = 0.5;
            Console.WriteLine("| " + wn[wi] + " | " + v[0].ToString("0.0") + " | " + v[1].ToString("0.0") + " | " + v[2].ToString("0.0") + " | " + v[3].ToString("0.0") + " | " + nm[b] + " | " + ((v[0] - v[1]) / hi * 100).ToString("0") + "% | " + (bp * 100).ToString("0") + "% | " + (surv[0] * 100).ToString("0") + "/" + (surv[1] * 100).ToString("0") + "/" + (surv[2] * 100).ToString("0") + "% | " + risk[0].ToString("0") + "/" + risk[1].ToString("0") + "/" + risk[2].ToString("0") + " |");
        }
        bool c1 = true; foreach (var g in gap) if (g > 0.25) c1 = false;
        double diff = Math.Abs(best[2] - best[3]) * 100;
        Console.WriteLine("\n① 날씨별로 순수 전략 간 차이 25% 이내: " + (c1 ? "O" : "X") + " (최대 " + (Max(gap) * 100).ToString("0") + "%)");
        Console.WriteLine("② 최적 천도 비율 비 vs 안개 차이 10%p 이상: " + (diff >= 10 ? "O" : "X") + " (비 " + (best[2] * 100).ToString("0") + "% / 안개 " + (best[3] * 100).ToString("0") + "% → " + diff.ToString("0") + "%p)");
        // ③ 날씨를 섞은 1막 전체에서 4-4절 기준 ①~④
        WxFixed = null; WxMixed = true; var vm = new double[4]; var rm = new double[4]; double psurv = 0, pboss = 0; int q = 0;
        foreach (Strat st in Enum.GetValues(typeof(Strat)))
        {
            PTendo = 0.5; var L = RunMany(st, runs); vm[q] = ValuePerMin(L, w); rm[q] = RiskPerMin(L);
            if (st == Strat.PahonOnly) { psurv = Avg(L, r => r.Died ? 0 : 1); pboss = Avg(L, r => r.BossFought ? 1 : 0); }
            q++;
        }
        int bm = 0; for (int i = 1; i < 4; i++) if (vm[i] > vm[bm]) bm = i;
        double mh = Math.Max(vm[0], vm[1]), ml = Math.Min(vm[0], vm[1]);
        Console.WriteLine("\n③ 날씨 섞은 1막(밤마다 솔고개 가중치, 밤 중간 25% 재굴림):");
        Console.WriteLine("| 천도만 | 파혼만 | 섞기(상황) | 섞기(반반) | 1등 | ① 섞기 1등 | ② 천도·파혼 20% 안 | ③ 파혼만 생존·보스 | ④ 위험 천도만 최대 |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|");
        Console.WriteLine("| " + vm[0].ToString("0.0") + " | " + vm[1].ToString("0.0") + " | " + vm[2].ToString("0.0") + " | " + vm[3].ToString("0.0") + " | " + nm[bm] + " | " + (bm == 2 ? "O" : "X") + " | " + ((mh - ml) / mh <= 0.20 ? "O" : "X") + " (" + ((vm[0] - vm[1]) / mh * 100).ToString("0") + "%) | " + (psurv >= 0.95 && pboss >= 0.95 ? "O" : "X") + "(생존" + (psurv * 100).ToString("0") + "%) | " + (rm[0] >= rm[1] && rm[0] >= rm[2] && rm[0] >= rm[3] ? "O" : "X") + " |");
        return 0;
    }
    /// <summary>혼 3유형 판정표(기획서 부록 F-1b): 구역별 순수 전략·최적 천도 비율, 잔넋 구역 vs 묻힌 혼 구역 비교, 1막 전체 ①~④</summary>
    static int TypesTable(int runs)
    {
        const double w = 1.3;
        var zones = new (string n, double m, double wl, double b)[] {
            ("솔고개", Balance.SOULTYPE_SOLGOGAE_MOTE_PCT, Balance.SOULTYPE_SOLGOGAE_WAIL_PCT, Balance.SOULTYPE_SOLGOGAE_BURIED_PCT),
            ("보릿들", Balance.SOULTYPE_BORIT_MOTE_PCT, Balance.SOULTYPE_BORIT_WAIL_PCT, Balance.SOULTYPE_BORIT_BURIED_PCT),
            ("물막이 골", Balance.SOULTYPE_MULMAGI_MOTE_PCT, Balance.SOULTYPE_MULMAGI_WAIL_PCT, Balance.SOULTYPE_MULMAGI_BURIED_PCT),
            ("폐당집", Balance.SOULTYPE_PYEDANG_MOTE_PCT, Balance.SOULTYPE_PYEDANG_WAIL_PCT, Balance.SOULTYPE_PYEDANG_BURIED_PCT),
            ("검은여울", Balance.SOULTYPE_RAPIDS_MOTE_PCT, Balance.SOULTYPE_RAPIDS_WAIL_PCT, Balance.SOULTYPE_RAPIDS_BURIED_PCT),
            ("(유형 없음·옛 시뮬)", 0, 0, 0) };
        Console.WriteLine("혼 3유형 시뮬 (철삭, w=" + w + ", 각 전략 " + runs + "판). 가치/분 = (넋+기억x4+엽전xw)/분. 비율은 잔넋/넋두리/묻힌 혼(%), 나머지 보통");
        Console.WriteLine("| 구역 | 비율 | 천도만 | 파혼만 | 섞기(상황) | 섞기(반반) | 1등 | 천도-파혼 차이 | 최적 천도 비율 | 생존(천/파/섞) | 위험(천/파/섞) |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|---|");
        string[] nm = { "천도만", "파혼만", "섞기(상황)", "섞기(반반)" };
        var bestP = new double[zones.Length];
        for (int zi = 0; zi < zones.Length; zi++)
        {
            MixMote = zones[zi].m; MixWail = zones[zi].wl; MixBuried = zones[zi].b;
            var v = new double[4]; var risk = new double[3]; var surv = new double[3]; int k = 0;
            foreach (Strat st in Enum.GetValues(typeof(Strat)))
            {
                PTendo = 0.5; var L = RunMany(st, runs); v[k] = ValuePerMin(L, w);
                if (k < 3) { risk[k] = RiskPerMin(L); surv[k] = Avg(L, r => r.Died ? 0 : 1); }
                k++;
            }
            int b = 0; for (int i = 1; i < 4; i++) if (v[i] > v[b]) b = i;
            double hi = Math.Max(v[0], v[1]);
            double bp = 0, bv = -1;
            for (double p = 0; p <= 1.0001; p += 0.1) { PTendo = p; var L = RunMany(Strat.CoinFlip, runs); double vv = ValuePerMin(L, w); if (vv > bv) { bv = vv; bp = p; } }
            bestP[zi] = bp; PTendo = 0.5;
            Console.WriteLine("| " + zones[zi].n + " | " + zones[zi].m + "/" + zones[zi].wl + "/" + zones[zi].b + " | " + v[0].ToString("0.0") + " | " + v[1].ToString("0.0") + " | " + v[2].ToString("0.0") + " | " + v[3].ToString("0.0") + " | " + nm[b] + " | " + ((v[0] - v[1]) / hi * 100).ToString("0") + "% | " + (bp * 100).ToString("0") + "% | " + surv[0].ToString("0.00") + "/" + surv[1].ToString("0.00") + "/" + surv[2].ToString("0.00") + " | " + risk[0].ToString("0.0") + "/" + risk[1].ToString("0.0") + "/" + risk[2].ToString("0.0") + " |");
        }
        double d = Math.Abs(bestP[0] - bestP[4]) * 100;
        Console.WriteLine("\n① 잔넋 많은 구역(솔고개) vs 묻힌 혼 많은 구역(검은여울) 최적 천도 비율 15%p 이상 차이: " + (d >= 15 ? "O" : "X") + " (솔고개 " + (bestP[0] * 100).ToString("0") + "% / 검은여울 " + (bestP[4] * 100).ToString("0") + "% → " + d.ToString("0") + "%p)");
        // ② 1막 전체: 다섯 구역 평균 비율로 4-4절 기준 ①~④
        MixMote = 0; MixWail = 0; MixBuried = 0; for (int zi = 0; zi < 5; zi++) { MixMote += zones[zi].m / 5; MixWail += zones[zi].wl / 5; MixBuried += zones[zi].b / 5; }
        var vm = new double[4]; var rm = new double[4]; double psurv = 0, pboss = 0; int q = 0;
        foreach (Strat st in Enum.GetValues(typeof(Strat)))
        {
            PTendo = 0.5; var L = RunMany(st, runs); vm[q] = ValuePerMin(L, w); rm[q] = RiskPerMin(L);
            if (st == Strat.PahonOnly) { psurv = Avg(L, r => r.Died ? 0 : 1); pboss = Avg(L, r => r.BossFought ? 1 : 0); }
            q++;
        }
        int bm = 0; for (int i = 1; i < 4; i++) if (vm[i] > vm[bm]) bm = i;
        double mh = Math.Max(vm[0], vm[1]), ml = Math.Min(vm[0], vm[1]);
        Console.WriteLine("\n② 1막 전체(다섯 구역 평균 비율: 잔넋 " + MixMote.ToString("0") + "/넋두리 " + MixWail.ToString("0") + "/묻힌 혼 " + MixBuried.ToString("0") + "%):");
        Console.WriteLine("| 천도만 | 파혼만 | 섞기(상황) | 섞기(반반) | 1등 | ① 섞기 1등 | ② 천도·파혼 20% 안 | ③ 파혼만 생존·보스 | ④ 위험 천도만 최대 |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|");
        Console.WriteLine("| " + vm[0].ToString("0.0") + " | " + vm[1].ToString("0.0") + " | " + vm[2].ToString("0.0") + " | " + vm[3].ToString("0.0") + " | " + nm[bm] + " | " + (bm == 2 ? "O" : "X") + " | " + ((mh - ml) / mh <= 0.20 ? "O" : "X") + " (" + ((vm[0] - vm[1]) / mh * 100).ToString("0") + "%) | " + (psurv >= 0.95 && pboss >= 0.95 ? "O" : "X") + " (생존 " + psurv.ToString("0.00") + ", 보스 " + pboss.ToString("0.00") + ") | " + (rm[0] >= rm[1] && rm[0] >= rm[2] && rm[0] >= rm[3] ? "O" : "X") + " |");
        MixMote = MixWail = MixBuried = 0;
        return 0;
    }

    /// <summary>2막 구역별 표(기획 act2-souls.md): 구역마다 혼 비율·고리 배율로 세 밤 + 2막 보스(맺힘 960). 시작은 1막을 마친 차사(품계·손보기)</summary>
    static int Act2Table(int runs, string[] args)
    {
        const double w = 1.3;
        int ai = Array.IndexOf(args, "--rank"); int rank = ai >= 0 ? int.Parse(args[ai + 1]) : 10;
        int ei = Array.IndexOf(args, "--enh"); int enh = ei >= 0 ? int.Parse(args[ei + 1]) : 6;
        Act2 = true; A2StartNeok = NeokOf(rank); A2StartEnh = enh;
        // 이름, 잔넋, 넋두리, 묻힌 혼, 숫자 혼 %, 고리, 광석
        var zones = new (string n, double m, double wl, double b, double num, int ring, bool ore)[] {
            ("산성 아랫마을", 10, 15, 0, 10, 3, false), ("무너진 산성", 35, 10, 5, 30, 3, false), ("화살골", 30, 25, 5, 45, 3, false),
            ("군막 터", 40, 10, 0, 60, 4, false), ("큰 무덤", 10, 10, 45, 50, 4, false),
            ("광부촌", 10, 20, 0, 20, 3, true), ("선탄장", 15, 30, 0, 15, 3, true), ("큰 갱도", 20, 25, 15, 40, 4, true), ("무너진 막장", 10, 15, 30, 70, 4, true) };
        Console.WriteLine("2막 구역 시뮬 (철삭, w=" + w + ", 각 전략 " + runs + "판, 시작 품계 " + rank + "·손보기 " + enh + "단계). 가치/분 = (넋+기억x4+엽전xw)/분");
        Console.WriteLine("| 구역 | 고리 | 잔넋/넋두리/묻힌/숫자 | 천도만 | 파혼만 | 섞기(상황) | 섞기(반반) | 1등 | 천도-파혼 차이 | 생존(천/파/섞) | 위험(천/파/섞) |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|---|");
        string[] nm = { "천도만", "파혼만", "섞기(상황)", "섞기(반반)" };
        var all = new Dictionary<Strat, double>(); var allSurv = new Dictionary<Strat, double>(); foreach (Strat st in Enum.GetValues(typeof(Strat))) { all[st] = 0; allSurv[st] = 0; }
        foreach (var z in zones)
        {
            MixMote = z.m; MixWail = z.wl; MixBuried = z.b; A2NumPct = z.num; A2OrePct = z.ore ? 0.25 : 0;
            A2Maed = (z.ring == 3 ? 1.4 : 1.7) / (1 + Env("GEAR_DMG", 0.10)); A2Dmg = (z.ring == 3 ? 1.3 : 1.5) * (1 - Env("GEAR_DEF", 0.05));  A2B08 = z.ore && Env("A2_B08", 0) > 0; A2Reward = z.ring == 3 ? 1.5 : 1.75; A2Lump = z.ring == 3 ? 0.15 : 0.20;
            A2BossMaed = z.ring == 3 ? 960 : 1120; A2BossDmg = z.ring == 3 ? 22 : 24;
            var v = new double[4]; var surv = new double[4]; var risk = new double[4]; int k = 0;
            foreach (Strat st in Enum.GetValues(typeof(Strat)))
            {
                var L = RunMany(st, runs); double val = 0, min = 0, dmg = 0, sv = 0;
                foreach (var r in L) { val += r.Neok - A2StartNeok + r.Memory * 4 + r.Coin * w; min += r.Seconds / 60; dmg += r.Damage; sv += r.Died ? 0 : 1; }
                v[k] = val / min; surv[k] = sv / L.Count; risk[k] = dmg / min; all[st] += v[k] / zones.Length; allSurv[st] += surv[k] / zones.Length; k++;
            }
            int b = 0; for (int i = 1; i < 4; i++) if (v[i] > v[b]) b = i; double hi = Max(v);
            Console.WriteLine("| " + z.n + " | " + z.ring + " | " + z.m + "/" + z.wl + "/" + z.b + "/" + z.num + " | " + v[0].ToString("0.0") + " | " + v[1].ToString("0.0") + " | " + v[2].ToString("0.0") + " | " + v[3].ToString("0.0") + " | " + nm[b] + " | " + ((v[0] - v[1]) / hi * 100).ToString("0") + "% | " + surv[0].ToString("0.00") + "/" + surv[1].ToString("0.00") + "/" + surv[2].ToString("0.00") + " | " + risk[0].ToString("0.0") + "/" + risk[1].ToString("0.0") + "/" + risk[2].ToString("0.0") + " |");
        }
        var a = new List<double>(); foreach (Strat st in Enum.GetValues(typeof(Strat))) a.Add(all[st]);
        Console.WriteLine("\n2막 평균: 천도만 " + a[0].ToString("0.0") + " / 파혼만 " + a[1].ToString("0.0") + " / 섞기(상황) " + a[2].ToString("0.0") + " / 섞기(반반) " + a[3].ToString("0.0") +
            " · 생존 천/파/섞 " + allSurv[Strat.TendoOnly].ToString("0.00") + "/" + allSurv[Strat.PahonOnly].ToString("0.00") + "/" + allSurv[Strat.Adaptive].ToString("0.00"));
        double mh = Math.Max(Math.Max(a[0], a[1]), Math.Max(a[2], a[3])), ml = Math.Min(Math.Min(a[0], a[1]), Math.Min(a[2], a[3]));
        Console.WriteLine("기준: ① 섞기(상황) 1등 " + (a[2] >= mh ? "O" : "X") + " ② 네 전략 차이 20% 이내 " + ((mh - ml) / mh <= 0.20 ? "O" : "X") + " (" + ((mh - ml) / mh * 100).ToString("0") + "%) ③ 섞기 생존 0.95 이상 " + (allSurv[Strat.Adaptive] >= 0.95 ? "O" : "X"));
        Act2 = false; A2Maed = A2Dmg = A2Reward = 1; A2Lump = -1; A2NumPct = A2OrePct = 0; MixMote = MixWail = MixBuried = 0;
        return 0;
    }

    /// <summary>3막 구역별 표(기획 act3-souls.md): 고리 5·6, 물 혼(⑤)·무적 혼(⑥). 시작은 2막을 마친 차사</summary>
    static int Act3Table(int runs, string[] args)
    {
        const double w = 1.3;
        int ai = Array.IndexOf(args, "--rank"); int rank = ai >= 0 ? int.Parse(args[ai + 1]) : 15;
        int ei = Array.IndexOf(args, "--enh"); int enh = ei >= 0 ? int.Parse(args[ei + 1]) : 9;
        Act2 = true; A2StartNeok = NeokOf(rank); A2StartEnh = enh;
        double r5m = Env("R5_MAED", 2.0), r6m = Env("R6_MAED", 2.3), r5d = Env("R5_DMG", 1.7), r6d = Env("R6_DMG", 1.9), r5n = Env("R5_NEOK", 2.0), r6n = Env("R6_NEOK", 2.3);
        // 이름, 잔넋, 넋두리, 묻힌 혼, 숫자 %, 물 혼 %, 무적 %, 고리
        var zones = new (string n, double m, double wl, double b, double num, double wa, double mj, int ring)[] {
            ("포구", 10, 20, 0, 10, 30, 0, 5), ("소금밭", 25, 15, 0, 15, 20, 0, 5), ("망부석 곶", 10, 15, 10, 10, 50, 0, 6), ("난파 여울", 20, 20, 0, 20, 70, 0, 6),
            ("저잣거리", 30, 15, 0, 15, 0, 30, 5), ("움막촌", 15, 20, 10, 10, 0, 50, 5), ("큰 다리 밑", 25, 20, 0, 10, 0, 60, 6), ("성문 밖", 10, 15, 40, 30, 0, 30, 6) };
        Console.WriteLine("3막 구역 시뮬 (철삭, w=" + w + ", 각 전략 " + runs + "판, 시작 품계 " + rank + "·손보기 " + enh + ", 별명 들은 비율 " + A3Heard + ", 밀물 창 확률 " + A3TideP + ")");
        Console.WriteLine("| 구역 | 고리 | 잔넋/넋두리/묻힌/숫자/물/무적 | 천도만 | 파혼만 | 섞기(상황) | 섞기(반반) | 1등 | 천도-파혼 | 생존(천/파/섞) | 사라짐/밤 |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|---|");
        string[] nm = { "천도만", "파혼만", "섞기(상황)", "섞기(반반)" };
        var all = new Dictionary<Strat, double>(); var allSurv = new Dictionary<Strat, double>(); foreach (Strat st in Enum.GetValues(typeof(Strat))) { all[st] = 0; allSurv[st] = 0; }
        foreach (var z in zones)
        {
            MixMote = z.m; MixWail = z.wl; MixBuried = z.b; A2NumPct = z.num; A2OrePct = 0; A3WaterPct = z.wa; A3MujeokPct = z.mj;
            A2Maed = (z.ring == 5 ? r5m : r6m) / (1 + Env("GEAR_DMG", 0.22)); A2Dmg = (z.ring == 5 ? r5d : r6d) * (1 - Env("GEAR_DEF", 0.10));  A2B08 = true; A2Reward = z.ring == 5 ? r5n : r6n; A2Lump = z.ring == 5 ? 0.22 : 0.25;
            A2BossMaed = z.ring == 5 ? 1280 : 1440; A2BossDmg = z.ring == 5 ? 26 : 28;
            var v = new double[4]; var surv = new double[4]; double van = 0; int k = 0;
            foreach (Strat st in Enum.GetValues(typeof(Strat)))
            {
                var L = RunMany(st, runs); double val = 0, min = 0, sv = 0, vn = 0;
                foreach (var r in L) { val += r.Neok - A2StartNeok + r.Memory * 4 + r.Coin * w; min += r.Seconds / 60; sv += r.Died ? 0 : 1; vn += r.Vanished; }
                v[k] = val / min; surv[k] = sv / L.Count; if (st == Strat.Adaptive) van = vn / L.Count / Nights; all[st] += v[k] / zones.Length; allSurv[st] += surv[k] / zones.Length; k++;
            }
            int b = 0; for (int i = 1; i < 4; i++) if (v[i] > v[b]) b = i; double hi = Max(v);
            Console.WriteLine("| " + z.n + " | " + z.ring + " | " + z.m + "/" + z.wl + "/" + z.b + "/" + z.num + "/" + z.wa + "/" + z.mj + " | " + v[0].ToString("0.0") + " | " + v[1].ToString("0.0") + " | " + v[2].ToString("0.0") + " | " + v[3].ToString("0.0") + " | " + nm[b] + " | " + ((v[0] - v[1]) / hi * 100).ToString("0") + "% | " + surv[0].ToString("0.00") + "/" + surv[1].ToString("0.00") + "/" + surv[2].ToString("0.00") + " | " + van.ToString("0.0") + " |");
        }
        var a = new List<double>(); foreach (Strat st in Enum.GetValues(typeof(Strat))) a.Add(all[st]);
        Console.WriteLine("\n3막 평균: 천도만 " + a[0].ToString("0.0") + " / 파혼만 " + a[1].ToString("0.0") + " / 섞기(상황) " + a[2].ToString("0.0") + " / 섞기(반반) " + a[3].ToString("0.0") +
            " · 생존 천/파/섞 " + allSurv[Strat.TendoOnly].ToString("0.00") + "/" + allSurv[Strat.PahonOnly].ToString("0.00") + "/" + allSurv[Strat.Adaptive].ToString("0.00"));
        double mh = Math.Max(Math.Max(a[0], a[1]), Math.Max(a[2], a[3])), ml = Math.Min(Math.Min(a[0], a[1]), Math.Min(a[2], a[3]));
        Console.WriteLine("기준(2막과 같음): 지배 답 없음 = 네 전략 차이 5% 이내 " + ((mh - ml) / mh <= 0.05 ? "O" : "X") + " (" + ((mh - ml) / mh * 100).ToString("0") + "%) · 섞기 생존 0.95 이상 " + (allSurv[Strat.Adaptive] >= 0.95 ? "O" : "X"));
        Act2 = false; A2Maed = A2Dmg = A2Reward = 1; A2Lump = -1; A2NumPct = A2OrePct = 0; A3WaterPct = A3MujeokPct = 0; A2B08 = false; MixMote = MixWail = MixBuried = 0;
        return 0;
    }

    /// <summary>시즌 2(⑦~⑩) 구역 표(기획 season2-souls-draft.md). 고리 7·8</summary>
    static int S2Table(int runs, string[] args)
    {
        const double w = 1.3;
        int ai = Array.IndexOf(args, "--rank"); int rank = ai >= 0 ? int.Parse(args[ai + 1]) : 20;
        int ei = Array.IndexOf(args, "--enh"); int enh = ei >= 0 ? int.Parse(args[ei + 1]) : 12;
        Act2 = true; A2StartNeok = NeokOf(rank); A2StartEnh = enh;
        // 이름, 잔넋, 넋두리(+사슬 혼), 묻힌, 숫자(인 없음)%, 돌아선%, 잠긴 숫자%, 조각%, 고리, 덩어리
        var zones = new (string n, double m, double wl, double b, double num, double tu, double lk, double fr, int ring, double lump)[] {
            ("⑦ 갈대늪", 20, 20, 0, 0, 40, 0, 0, 7, 0.25), ("⑦ 빈 나루 마을", 10, 15, 0, 0, 60, 0, 0, 7, 0.25), ("⑦ 먹물 여울", 25, 25, 0, 0, 30, 0, 0, 7, 0.25), ("⑦ 물안개 둑", 15, 15, 10, 0, 50, 0, 0, 7, 0.25),
            ("⑧ 서리 숙사", 20, 20, 0, 0, 0, 20, 0, 7, 0.25), ("⑧ 먹방", 15, 30, 0, 0, 0, 20, 0, 7, 0.25), ("⑧ 문서 창고", 10, 20, 20, 0, 0, 30, 0, 7, 0.25), ("⑧ 숫자 마당", 10, 10, 0, 0, 0, 80, 0, 7, 0.25),
            ("⑨ 빈 고을", 10, 20, 10, 50, 0, 0, 0, 8, 0.28), ("⑨ 아홉째 문", 10, 15, 0, 60, 0, 0, 0, 8, 0.28), ("⑨ 도장 없는 장터", 30, 15, 0, 40, 0, 0, 0, 8, 0.28), ("⑨ 인장 굴", 5, 20, 30, 50, 0, 0, 0, 8, 0.28),
            ("⑩ 처음 마을", 5, 20, 0, 0, 0, 0, 65, 8, 0.28), ("⑩ 사슬 무덤", 5, 45, 0, 0, 0, 0, 45, 8, 0.28), ("⑩ 우물터", 0, 20, 0, 0, 0, 0, 70, 8, 0.28), ("⑩ 물막이 바닥", 10, 10, 0, 0, 0, 0, 60, 8, 0.40) };
        double r7m = Env("R7_MAED", 2.6), r8m = Env("R8_MAED", 2.9), r7d = Env("R7_DMG", 2.1), r8d = Env("R8_DMG", 2.3), r7n = Env("R7_NEOK", 2.6), r8n = Env("R8_NEOK", 2.9);
        Console.WriteLine("시즌 2 구역 시뮬 (철삭, w=" + w + ", 각 전략 " + runs + "판, 시작 품계 " + rank + "·손보기 " + enh + ", 숫자 마당 이름 되찾은 비율 " + S2Rest + ", 엽전 몫 " + A2CoinMult + ")");
        Console.WriteLine("| 구역 | 고리 | 잔넋/넋두리/묻힌/인없음/돌아선/잠긴/조각 | 천도만 | 파혼만 | 섞기(상황) | 섞기(반반) | 1등 | 천도-파혼 | 생존(천/파/섞) |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|");
        string[] nm = { "천도만", "파혼만", "섞기(상황)", "섞기(반반)" };
        var all = new Dictionary<Strat, double>(); var allSurv = new Dictionary<Strat, double>(); foreach (Strat st in Enum.GetValues(typeof(Strat))) { all[st] = 0; allSurv[st] = 0; }
        foreach (var z in zones)
        {
            MixMote = z.m; MixWail = z.wl; MixBuried = z.b; A2NumPct = z.num; A2OrePct = 0; A3WaterPct = A3MujeokPct = 0; S2TurnPct = z.tu; S2LockPct = z.lk; S2FragPct = z.fr; A2B08 = false;
            A2Maed = (z.ring == 7 ? r7m : r8m) / (1 + Env("GEAR_DMG", 0.36)); A2Dmg = (z.ring == 7 ? r7d : r8d) * (1 - Env("GEAR_DEF", 0.18));  A2Reward = z.ring == 7 ? r7n : r8n; A2Lump = z.lump;
            A2BossMaed = z.ring == 7 ? 1600 : 1760; A2BossDmg = z.ring == 7 ? 30 : 32;
            A2NumNeok = z.num > 0 ? Env("S2_SEALLESS_NEOK", 1.15) : Env("A2_NUMNEOK", 1.3);   // ⑨ 인 없는 혼은 숫자 혼보다 낮게
            var v = new double[4]; var surv = new double[4]; int k = 0;
            foreach (Strat st in Enum.GetValues(typeof(Strat)))
            {
                var L = RunMany(st, runs); double val = 0, min = 0, sv = 0;
                foreach (var r in L) { val += r.Neok - A2StartNeok + r.Memory * 4 + r.Coin * w; min += r.Seconds / 60; sv += r.Died ? 0 : 1; }
                v[k] = val / min; surv[k] = sv / L.Count; all[st] += v[k] / zones.Length; allSurv[st] += surv[k] / zones.Length; k++;
            }
            int b = 0; for (int i = 1; i < 4; i++) if (v[i] > v[b]) b = i; double hi = Max(v);
            Console.WriteLine("| " + z.n + " | " + z.ring + " | " + z.m + "/" + z.wl + "/" + z.b + "/" + z.num + "/" + z.tu + "/" + z.lk + "/" + z.fr + " | " + v[0].ToString("0.0") + " | " + v[1].ToString("0.0") + " | " + v[2].ToString("0.0") + " | " + v[3].ToString("0.0") + " | " + nm[b] + " | " + ((v[0] - v[1]) / hi * 100).ToString("0") + "% | " + surv[0].ToString("0.00") + "/" + surv[1].ToString("0.00") + "/" + surv[2].ToString("0.00") + " |");
        }
        var a = new List<double>(); foreach (Strat st in Enum.GetValues(typeof(Strat))) a.Add(all[st]);
        Console.WriteLine("\n시즌 2 평균: 천도만 " + a[0].ToString("0.0") + " / 파혼만 " + a[1].ToString("0.0") + " / 섞기(상황) " + a[2].ToString("0.0") + " / 섞기(반반) " + a[3].ToString("0.0") +
            " · 생존 천/파/섞 " + allSurv[Strat.TendoOnly].ToString("0.00") + "/" + allSurv[Strat.PahonOnly].ToString("0.00") + "/" + allSurv[Strat.Adaptive].ToString("0.00"));
        double mh = Math.Max(Math.Max(a[0], a[1]), Math.Max(a[2], a[3])), ml = Math.Min(Math.Min(a[0], a[1]), Math.Min(a[2], a[3]));
        Console.WriteLine("기준: 네 전략 차이 5% 이내 " + ((mh - ml) / mh <= 0.05 ? "O" : "X") + " (" + ((mh - ml) / mh * 100).ToString("0") + "%) · 섞기 생존 0.95 이상 " + (allSurv[Strat.Adaptive] >= 0.95 ? "O" : "X"));
        A2NumNeok = Env("A2_NUMNEOK", 1.3);
        Act2 = false; A2Maed = A2Dmg = A2Reward = 1; A2Lump = -1; A2NumPct = A2OrePct = 0; S2TurnPct = S2LockPct = S2FragPct = 0; MixMote = MixWail = MixBuried = 0;
        return 0;
    }

    /// <summary>시즌 1 성장 곡선(기획 10-25): 하루씩 넘기며 넋을 쌓고, 그날 고리의 혼을 그날 품계로 상대한다. 막 경계에서 체감이 끊기는지 본다</summary>
    static int CurveTable(int runs, string[] args)
    {
        double eff = Env("CURVE_EFF", 0.8), nightMin = 22;
        // 고리: 매딤, 피해, 보상, 덩어리
        var ring = new Dictionary<int, double[]> { {1, new[]{1.0,1.0,1.0,0.05}}, {2, new[]{1.2,Env("R2_DMG",1.15),1.25,0.10}}, {3, new[]{1.4,1.3,1.5,0.15}}, {4, new[]{1.7,1.5,1.75,0.20}}, {5, new[]{2.0,1.7,2.0,0.22}}, {6, new[]{2.3,1.9,2.3,0.25}} };
        // 막, 날수, 앞 고리, 뒤 고리, 막 시작 손보기, 막 끝 손보기, 보스 천도 넋(보스당)
        var acts = new (string n, int days, int r1, int r2, int e0, int e1, int bossN, int bossNeok, double g0, double g1, double f0, double f1)[] {
            ("1막", (int)Env("D1", 12), 1, 2, 0, 6, 4, 50, 0, 0.10, 0, 0.05), ("2막", (int)Env("D2", 14), 3, 4, 6, 9, 4, 75, 0.10, 0.22, 0.05, 0.10), ("3막", (int)Env("D3", 14), 5, 6, 9, 12, 4, 100, 0.22, 0.36, 0.10, 0.18) };
        bool gear = Env("CURVE_GEAR", 1) > 0;   // 장비 옵션·인(맺힘 피해 %, 방어 %)을 막 안에서 고르게 올린다(드롭 표 목표값)
        MixMote = 20; MixWail = 15; MixBuried = 10; A2NumPct = 0; A2OrePct = 0; A3WaterPct = A3MujeokPct = 0;
        double neok = 0; int bossDone = 0;
        Console.WriteLine("시즌 1 성장 곡선 (섞기(상황), 하루 밤 " + nightMin + "분 x 효율 " + eff + ", 하루마다 " + runs + "판)");
        Console.WriteLine("| 막 | 날 | 고리 | 품계(시작) | 손보기 | 분당 넋 | 분당 처결 | 분당 피해 | 생존 | 그날 넋 |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|");
        var summary = new List<string>();
        foreach (var a in acts)
        {
            for (int d = 0; d < a.days; d++)
            {
                int rg = d < a.days / 2 ? a.r1 : a.r2; var R = ring[rg];
                int enh = a.e0 + (int)Math.Round((a.e1 - a.e0) * (double)d / Math.Max(1, a.days - 1));
                double fr = (double)d / Math.Max(1, a.days - 1), gd = gear ? a.g0 + (a.g1 - a.g0) * fr : 0, gf = gear ? a.f0 + (a.f1 - a.f0) * fr : 0;
                Act2 = true; A2StartNeok = (int)neok; A2StartEnh = enh; A2Maed = R[0] / (1 + gd); A2Dmg = R[1] * (1 - gf); A2Reward = R[2]; A2Lump = R[3]; A2B08 = false;
                A2BossMaed = (int)(800 * (1 + 0.25 * (rg - 1)) / 1.25 * 1.25); A2BossDmg = 18 + 2 * rg;
                int rank = RankOf((int)neok);
                var L = RunMany(Strat.Adaptive, runs); double gain = 0, min = 0, dmg = 0, sv = 0, cnt = 0;
                foreach (var r in L) { gain += r.Neok - A2StartNeok; min += r.Seconds / 60; dmg += r.Damage; sv += r.Died ? 0 : 1; cnt += r.Tendo + r.Pahon; }
                double npm = gain / min, spm = cnt / min, dpm = dmg / min, day = npm * nightMin * eff;
                neok += day;
                if (d == a.days / 2 - 1 || d == a.days - 1) { neok += 2 * a.bossNeok; bossDone += 2; }   // 고리마다 보스 둘 처결(천도 가정)
                if (d == 0 || d == a.days / 2 - 1 || d == a.days / 2 || d == a.days - 1)
                    Console.WriteLine("| " + a.n + " | " + (d + 1) + " | " + rg + " | " + rank + " | " + enh + " | " + npm.ToString("0.0") + " | " + spm.ToString("0.00") + " | " + dpm.ToString("0.0") + " | " + (sv / L.Count).ToString("0.00") + " | " + day.ToString("0") + " |");
                if (d == 0) summary.Add(a.n + " 시작 품계 " + rank + " 분당 처결 " + spm.ToString("0.00") + " 분당 피해 " + dpm.ToString("0.0"));
                if (d == a.days - 1) summary.Add(a.n + " 끝 품계 " + RankOf((int)neok) + " 분당 처결 " + spm.ToString("0.00") + " 분당 피해 " + dpm.ToString("0.0"));
            }
        }
        Console.WriteLine();
        foreach (var x in summary) Console.WriteLine(x);
        Console.WriteLine("시즌 1 끝 넋 " + neok.ToString("0") + " → 품계 " + RankOf((int)neok) + ", 도술 점수 " + (RankOf((int)neok) - 1 + bossDone) + "(품계−1 + 보스 천도 " + bossDone + ")");
        Act2 = false; A2Maed = A2Dmg = A2Reward = 1; A2Lump = -1; MixMote = MixWail = MixBuried = 0;
        return 0;
    }


    /// <summary>
    /// 1막 균형 점검(--act1): 12일을 이어서 돌린다. 게임의 실제 규칙을 쓴다 —
    /// 품계는 처결 셈(GrowthState.RankFor, 혼 하나 = 10 x 고리 보상 배율), 힘 품계당 +7%, 엽전으로 손보기(칸 셋 x 5단계),
    /// 장비는 실제 Loot.Roll + Equipment.TryEquip 로 굴린다(드롭 35%, 고리별 등급 표). 날마다 품계·장비·손보기가 다음 날 싸움에 들어간다.
    /// 한계: 보스는 맺힘 ÷ 초당 피해 모델이라 실제 3~4분보다 훨씬 짧게 나온다(약점 창·꿇은 동안 기다림 같은 연출 시간이 없음) → 보스는 PC 봇 몫.
    /// </summary>
    static int Act1Table(int runs, string[] args)
    {
        double eff = Env("CURVE_EFF", 0.8), nightMin = Env("NIGHT_MIN", 22);
        int days = (int)Env("D1", 12), ringSwitch = (int)Env("RING2_DAY", 7);   // 7일째부터 검은여울(고리 2)
        Environment.SetEnvironmentVariable("RANK_STR", Env("RANK_STR", 0.07).ToString(System.Globalization.CultureInfo.InvariantCulture));
        A2CoinMult = Env("A2_COIN", Balance.RING_COIN_SHARE);
        var ring = new Dictionary<int, double[]> { {1, new[]{1.0,1.0,1.0,0.05}}, {2, new[]{1.2,1.15,1.25,0.10}} };
        MixMote = 20; MixWail = 15; MixBuried = 10; A2NumPct = 0; A2OrePct = 0; A3WaterPct = A3MujeokPct = 0;
        int gearSeeds = (int)Env("GEAR_SEEDS", 400);
        // 1차: 장비 없이 하루 처결 수를 어림 → 장비 궤적 → 2차에서 장비를 넣어 다시 잰다
        double[] kills = new double[days]; for (int d = 0; d < days; d++) kills[d] = Env("KILLS0", 85);
        double[] gDmg = new double[days + 1], gDef = new double[days + 1], gDrops = new double[days], gRareDrops = new double[days];
        double tally = 0; int enh = 0; int[] slotLv = new int[5]; int spent = 0; double coinPool = 0;
        var rows = new List<string>();
        for (int pass = 0; pass < 3; pass++)
        {
            GearTrajectory(days, ringSwitch, kills, gearSeeds, gDmg, gDef, gDrops, gRareDrops);
            tally = 0; enh = 0; slotLv = new int[5]; spent = 0; coinPool = 0; rows.Clear();
            double potCoin = 0;
            for (int d = 0; d < days; d++)
            {
                int rg = d + 1 < ringSwitch ? 1 : 2; var R = ring[rg];
                int rank = GrowthState.RankFor((int)tally);
                ForceRank = rank; Act2 = true; A2StartNeok = 0; A2StartEnh = enh; A2B08 = false;
                A2Maed = R[0] / (1 + Math.Min(gDmg[d], Balance.CAP_DAMAGE_PCT)); A2Dmg = R[1] * (1 - Math.Min(gDef[d], Balance.CAP_DEFENSE_PCT)); A2Reward = R[2]; A2Lump = R[3];
                A2BossMaed = (int)Balance.BOSS_S1_MAEDHIM; A2BossDmg = (int)Balance.BOSS_S1_DAMAGE;
                PotionsUsed = 0; var L = RunMany(Strat.Adaptive, runs);
                double min = 0, cnt = 0, dmg = 0, sv = 0, coin = 0; foreach (var r in L) { min += r.Seconds / 60; cnt += r.Tendo + r.Pahon; dmg += r.Damage; sv += r.Died ? 0 : 1; coin += r.Coin; }
                double spm = cnt / min, dpm = dmg / min, cpm = coin / min, potPerNight = (double)PotionsUsed / (L.Count * Nights);
                double dayKills = spm * nightMin * eff, dayCoin = cpm * nightMin * eff, dayTally = dayKills * Balance.TENDO_NEOK * R[2];
                kills[d] = dayKills;
                // 낮: 쓴 회복약 값을 먼저 빼고(밤마다 쓴 만큼 15엽전, 처음 두 개는 당할미가 줌), 남은 엽전으로 손보기
                double potBuy = Math.Max(0, potPerNight - Balance.FIRST_NIGHT_HEAL) * Balance.SHOP_HEAL_PRICE; potCoin += potBuy;
                coinPool += dayCoin - potBuy;
                int enhBefore = enh;
                while (true)
                {
                    int nSlots = d + 1 >= ringSwitch ? 5 : 3, best = -1; for (int k = 0; k < nSlots; k++) if (slotLv[k] < Balance.ENHANCE_MAX && (best < 0 || slotLv[k] < slotLv[best])) best = k;
                    int cost = best < 0 ? 0 : EnhCostAt(slotLv[best]);
                    if (best < 0 || coinPool < cost) break;
                    coinPool -= cost; slotLv[best]++; enh++;
                }
                rows.Add("| " + (d + 1) + " | " + rg + " | " + rank + " | " + ((int)tally) + " | " + dayKills.ToString("0") + " | " + spm.ToString("0.00") + " | " + dpm.ToString("0.0") + " | " + (sv / L.Count).ToString("0.00") + " | " + dayCoin.ToString("0") + " | " + potPerNight.ToString("0.0") + " | " + enh + " (+" + (enh - enhBefore) + ") | " + coinPool.ToString("0") + " | " + (gDmg[d] * 100).ToString("0.0") + "% | " + (gDef[d] * 100).ToString("0.0") + "% | " + gDrops[d].ToString("0.0") + " |");
                tally += dayTally;
                if (d + 1 == ringSwitch - 1 || d + 1 == days) tally += 2 * (Balance.TENDO_NEOK * 5) * 1.0;   // 고리마다 보스 둘(보스 천도 넋 50, 처결 셈도 같은 값)
            }
        }
        Console.WriteLine("1막 균형(--act1): 섞기(상황), 하루 밤 " + nightMin + "분 x 효율 " + eff + ", 하루 " + runs + "판 x 밤 3. 힘 품계당 +" + (Env("RANK_STR", 0.07) * 100) + "%, 엽전 몫 " + A2CoinMult + ", 장비 시드 " + gearSeeds);
        Console.WriteLine("| 날 | 고리 | 품계(시작) | 처결 셈(시작) | 하루 처결 | 분당 처결 | 분당 피해 | 생존 | 하루 엽전 | 밤당 약 마심 | 손보기 단계 | 남은 엽전 | 장비 피해 | 장비 방어 | 하루 드롭 |");
        Console.WriteLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
        foreach (var r in rows) Console.WriteLine(r);
        Console.WriteLine("1막 끝 처결 셈 " + ((int)tally) + " → 품계 " + GrowthState.RankFor((int)tally) + ", 손보기 " + enh + "단계");
        ForceRank = 0; Act2 = false; A2Maed = A2Dmg = A2Reward = 1; A2Lump = -1; MixMote = MixWail = MixBuried = 0;
        return 0;
    }

    static double DropOverride = Env("DROP", Balance.DROP_CHANCE);
    static int EnhCostAt(int lv) { int[] c = { Balance.ENHANCE_COST_1, Balance.ENHANCE_COST_2, Balance.ENHANCE_COST_3, Balance.ENHANCE_COST_4, Balance.ENHANCE_COST_5 }; return (int)Math.Round(c[Math.Min(lv, 4)] * Env("ENH_K", 1)); }

    /// <summary>실제 드롭 규칙(Loot.Roll)과 자리 규칙(Equipment.TryEquip)으로 12일 동안의 장비 피해·방어 평균을 구한다. d일째 "시작" 값이 [d]</summary>
    static void GearTrajectory(int days, int ringSwitch, double[] kills, int seeds, double[] dmgOut, double[] defOut, double[] dropsOut, double[] rareOut)
    {
        var dsum = new double[days + 1]; var fsum = new double[days + 1]; Array.Clear(dropsOut, 0, dropsOut.Length); Array.Clear(rareOut, 0, rareOut.Length);
        for (int sd = 0; sd < seeds; sd++)
        {
            var rng = new Random(7000 + sd); Func<float> rnd = () => (float)rng.NextDouble();
            var eq = new Equipment();
            for (int d = 0; d < days; d++)
            {
                var st = eq.Stats(); dsum[d] += st.DamagePct; fsum[d] += st.DefensePct;
                int ringNo = d + 1 < ringSwitch ? 1 : 2; eq.FirstRingBossDone = d + 1 >= ringSwitch;
                int n = (int)Math.Round(kills[d]); int got = 0, rare = 0;
                for (int i = 0; i < n; i++) { if (rng.NextDouble() >= DropOverride) continue; bool first = true; Func<float> rnd2 = () => { if (first) { first = false; return 0f; } return rnd(); }; var it = Loot.Roll(rnd2, false, ringNo, eq.DropKinds()); if (it == null) continue; got++; if (it.Rarity == Rarity.Rare) rare++; eq.TryEquip(it); }
                dropsOut[d] += (double)got / seeds; rareOut[d] += (double)rare / seeds;
            }
            var s2 = eq.Stats(); dsum[days] += s2.DamagePct; fsum[days] += s2.DefensePct;
        }
        for (int d = 0; d <= days; d++) { dmgOut[d] = dsum[d] / seeds; defOut[d] = fsum[d] / seeds; }
    }

    static double Max(double[] a) { double m = a[0]; foreach (var x in a) if (x > m) m = x; return m; }

    static double Avg(List<RunResult> L, Func<RunResult, double> f) { double s = 0; foreach (var r in L) s += f(r); return s / L.Count; }

    static bool WantTendo(Strat s, Random rng, int others, double hp, int ty = 0)
    {
        switch (s)
        {
            case Strat.TendoOnly: return true;
            case Strat.PahonOnly: return false;
            case Strat.Adaptive: if (Act2) { if (ty == 2) return false; if (ty == 1) return hp > 30; if (ty == 3) return others <= 1 && hp > 35; return others <= 1 && hp > 30; }   // 2막: 잔넋 무리는 연쇄 파혼, 숫자 혼은 others+1 로 들어온다
                if (ty == 2) return others == 0 && hp > 50; if (ty == 1) return hp > 30; if (ty == 3) return others == 0 && hp > 40; return others <= 1 && hp > 30;   // 주변이 붐비거나 위험하면 파혼, 한가하면 천도
            default: return rng.NextDouble() < PTendo;
        }
    }

    static int Pick(Random rng, double[] w) { double x = rng.NextDouble(), a = 0; for (int i = 0; i < w.Length; i++) { a += w[i]; if (x < a) return i; } return w.Length - 1; }

    static RunResult Play(Strat s, Random rng)
    {
        var res = new RunResult(); var led = new Ledger(); var g = new GrowthState();
        double hp = led.MaxHp; int potions = Balance.FIRST_NIGHT_HEAL; double bonusPool = 0; bool namedTendoed = false;
        int enhSteps = 0, stainPts = 0, pahonCnt = 0; var slotLv = new int[3]; int spent = 0; double coinAcc = 0;
        if (Act2) { led.Neok = A2StartNeok; enhSteps = A2StartEnh; for (int k = 0; k < A2StartEnh; k++) slotLv[k % 3]++; spent = 0; }   // 1막을 마친 차사로 시작
        // 지금 공격력: 품계가 오르면 능력치 5점을 전부 힘에(+1%/점), 손보기 한 단계 = 주옵션 +6%(=피해 약 +0.33%)
        Func<double> dps = () => !Growth ? BaseDps : BaseDps * (1 + GrowthStr(ForceRank > 0 ? ForceRank : RankOf(led.Neok))) * (1 + Balance.ENHANCE_PCT * MainOptDmg * enhSteps);
        for (int night = 0; night < Nights && hp > 0; night++)
        {
            double t = 0, lastTendoAt = -99, sinceHit = 99; int sentTonight = 0; res.QuotaSeconds[night] = double.NaN;
            double fogClearUntil = -1; bool midRolled = false;
            Fx = NightFx(rng);
            bool namedDone = false; int tideLeft = 0; double tideDeadline = 0;
            while (t < Balance.NIGHT_DURATION && hp > 0)
            {
                // 다음 혼을 찾아간다(이동). 맞지 않은 시간만큼 회복
                if (WxMixed && !midRolled && t >= Balance.NIGHT_DURATION / 2) { midRolled = true; if (rng.NextDouble() < Balance.WEATHER_NIGHT_MID_REROLL) Fx = NightFx(rng); }   // 밤 중간 25% 한 번 더
                double travel = TravelAvg * (0.5 + rng.NextDouble()) / Fx.GhostMult;
                if (tideLeft > 0) travel = 1.0;   // 밀물 무리: 바로 옆에 떠 있다   // 혼이 더 많이 나오면 다음 혼이 가깝다
                if (Fx.VisionM < Balance.WEATHER_CLEAR_VISION_M) travel *= Math.Sqrt(Balance.WEATHER_CLEAR_VISION_M / Fx.VisionM);   // 안개: 혼 찾기 느려짐(가정: 시야 비의 제곱근)
                bool clearNow = t < fogClearUntil;
                if (Fx.MoveSlow > 0 && !clearNow) travel /= 1 - Fx.MoveSlow;   // 역병 안개: 이동 -20%
                t += travel; sinceHit += travel; hp = Math.Min(led.MaxHp, hp + Balance.REGEN_PER_SEC * Math.Max(0, sinceHit - Balance.REGEN_DELAY > 0 ? Math.Min(travel, sinceHit - Balance.REGEN_DELAY) : 0));
                if (t >= Balance.NIGHT_DURATION) break;
                // 혼 하나: 종류, 주변 적 수
                bool lump = rng.NextDouble() < (A2Lump >= 0 ? A2Lump : Balance.LUMP_SPAWN_CHANCE);
                int kind = Pick(rng, new[] { 0.5, 0.3, 0.2 });   // 갓 죽은·해 넘긴·오래된
                int others = Pick(rng, new[] { 0.3, 0.4, 0.3 });
                bool named = !namedDone && night == Nights - 1 && sentTonight >= Balance.NIGHT_QUOTA - 1 && !lump;   // 몫의 마지막은 이름혼(곽 뱃꾼 대용)
                // 죽여서 무릎 꿇리기
                double maed = (lump ? Balance.MAEDHIM_LUMP : Balance.MAEDHIM_NORMAL) * A2Maed;
                bool num = Act2 && !lump && !named && rng.NextDouble() * 100 < A2NumPct;   // 숫자 혼(인 없음): 천도 캐스팅 +0.5초
                int s2k = 0; if (Act2 && !lump && !named) { double q2 = rng.NextDouble() * 100; s2k = q2 < S2TurnPct ? 1 : q2 < S2TurnPct + S2LockPct ? 2 : q2 < S2TurnPct + S2LockPct + S2FragPct ? 3 : 0; }
                if (s2k == 2) num = true;
                if (s2k == 3) maed *= 1.5;   // 조각 셋(각 절반 맺힘)을 모두 꿇린다
                bool water = Act2 && !lump && !named && (tideLeft > 0 || rng.NextDouble() * 100 < A3WaterPct);      // 3막 ⑤ 물 혼(밀물 무리 중이면 물 혼)
                bool mujeok = Act2 && !lump && !named && !water && rng.NextDouble() * 100 < A3MujeokPct;   // 3막 ⑥ 무적 혼
                bool tideOn = tideLeft > 0;
                if (water && !tideOn && rng.NextDouble() < A3TideP) { tideOn = true; tideLeft = 2 + rng.Next(3); tideDeadline = t + A3TideWin; }   // 밀물 신호: 물 혼 2~4마리가 한꺼번에 떠밀려 가기 시작, 20초 창
                if (tideOn) tideLeft--;
                double use = Math.Min(maed - 10, bonusPool); bonusPool -= use;
                if (Wd.Id == WeaponId.Mace)   // 땅울림(Q, 6초마다): 접근하며 한 번 — 목표 20 + 주변 적마다 20(다음 싸움에서 이미 깎인 몫으로 쌓임), 기절 0.8초 동안 안 맞음
                {
                    double q = Math.Min(maed - 10 - use, Balance.MACE_QUAKE_DAMAGE); use += q;
                    bonusPool += Balance.MACE_QUAKE_DAMAGE * others;
                }   // 앞선 파혼 폭발이 이미 깎아 둔 몫
                // 혼 3유형(기획서 부록 F-1b, 임시): 0 보통 / 1 넋두리 / 2 잔넋 무리 / 3 묻힌 혼
                int ty = 0, moteN = 0;
                if (!lump && !named && (MixMote + MixWail + MixBuried) > 0) { double rr = rng.NextDouble() * 100; ty = rr < MixMote ? 2 : rr < MixMote + MixWail ? 1 : rr < MixMote + MixWail + MixBuried ? 3 : 0; }
                if (ty == 2) moteN = 3 + rng.Next(3);
                if (s2k != 0) { ty = 0; moteN = 0; }
                if (ty == 1) maed *= Balance.SOULTYPE_WAIL_HP;
                double groupHp = ty == 2 ? moteN * Balance.SOULTYPE_MOTE_HP * maed : maed;   // 잔넋 무리는 맺힘 합
                double crowd = others + (ty == 2 ? moteN - 1 : 0);                          // 사슬 휘두르기가 한꺼번에 맞히는 주변 수
                double kill = (groupHp - use) / (dps() * WR(Wd.Id) * (1 + WG(Wd.Id) * Math.Min(crowd, 2))) + 0.5;
                if (ty == 1) kill += 1.0;   // 거리를 지키는 혼을 쫓아가거나 견인으로 끌어와야 한다
                double take = (others + 1) * (kill / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * HitMove * WTake(Wd.Id);
                if (ty == 1) take = ((kill / Balance.SOULTYPE_WAIL_INTERVAL) * Balance.SOULTYPE_WAIL_DAMAGE * HitMove * 0.85 + others * (kill / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * HitMove) * WTake(Wd.Id);   // 탄은 직선이라 읽기 쉽다(0.85)
                else if (ty == 2) take = (moteN * (kill / Balance.SOULTYPE_MOTE_INTERVAL) * Balance.SOULTYPE_MOTE_DAMAGE * HitMove + others * (kill / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * HitMove) * WTake(Wd.Id);
                else if (ty == 3) take = ((kill / (Balance.SOULTYPE_BURIED_REBURY_S + 2)) * Balance.SOULTYPE_BURIED_DAMAGE * 0.5 + others * (kill / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * HitMove) * WTake(Wd.Id);   // 매복 한 번에 반쯤 맞는다
                take *= A2Dmg; Hit(ref hp, ref sinceHit, ref res, take); t += kill; sinceHit = take > 0 ? 0 : sinceHit + kill;
                if (hp <= 0) break;
                hp = Heal(hp, ref potions);
                // 선택
                if (tideOn && t + kill > tideDeadline) { t += Math.Max(0, tideDeadline - t); res.Vanished++; continue; }   // 깎는 사이 물 밑으로 사라졌다(넋 0·기억 0, 시간만 씀)
                bool tendo = !lump && WantTendo(s, rng, others + (num ? 1 : 0) - (water ? 1 : 0), hp, ty);   // 숫자 혼은 시전이 길어 한 마리 더 붐비는 것처럼, 물 혼은 짧아 한 마리 덜
                if (mujeok && rng.NextDouble() >= A3Heard) tendo = false;
                if (s2k == 2 && rng.NextDouble() >= S2Rest) tendo = false;   // 이름을 못 되찾은 숫자 마당 혼은 파혼만
                if (s2k == 3 && tendo) kill += 2.0;   // 조각 셋을 견인으로 모아 잇는 시간   // 별명을 못 들은 무적 혼은 파혼만
                if (named && s == Strat.TendoOnly) tendo = true;
                if (tendo)
                {
                    bool chain = t - lastTendoAt <= Balance.TENDO_CHAIN_WINDOW + Wd.ChainWindowAddS;
                    double cast = CoreRules.CastTime(chain) * Wd.CastTimeMult + (num ? (A2B08 ? Balance.SEAL_FADED_CAST_BONUS : Balance.SEAL_MISSING_CAST_BONUS) : 0);
                    if (water) cast = Math.Max(0.5, cast - 0.5);
                    if (tideOn && t + cast > tideDeadline) { t = Math.Max(t, tideDeadline); res.Vanished++; continue; }   // 외는 도중 물에 쓸려 감
                    double dmg = others * (cast / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * Fx.CastHit;
                    if (ty == 1) dmg += (cast / Balance.SOULTYPE_WAIL_INTERVAL) * Balance.SOULTYPE_WAIL_DAMAGE * Fx.CastHit * 0.5;   // 외는 동안 멀리서 던진다
                    else if (ty == 2) dmg += (moteN - 1) * Math.Max(0, cast - Balance.SOULTYPE_MOTE_RATTLE_S) / Balance.SOULTYPE_MOTE_INTERVAL * Balance.SOULTYPE_MOTE_DAMAGE * Fx.CastHit;   // 대장이 떠나면 2초 혼란
                    else if (ty == 3) dmg += (cast / (Balance.SOULTYPE_BURIED_REBURY_S + 2)) * Balance.SOULTYPE_BURIED_DAMAGE * Fx.CastHit;   // 옆 무덤이 솟아 시전을 끊을 위험
                    if (Fx.StandDrain > 0 && !(t < fogClearUntil)) dmg += Fx.StandDrain * cast;   // 역병 안개: 서서 외는 동안 초당 1
                    dmg *= A2Dmg; Hit(ref hp, ref sinceHit, ref res, dmg); t += cast + Approach; if (dmg > 0) sinceHit = 0;
                    if (hp <= 0) break;
                    { int nb = led.Neok; led.CompleteTendo(); led.Neok += (int)Math.Round((led.Neok - nb) * Wd.NeokPct); if (ty == 2) { for (int f = 1; f < moteN; f++) { t += CoreRules.CastTime(true) * Wd.CastTimeMult; led.Neok += (int)Math.Round((led.Neok - nb) * 0.4); } } if (ty == 1) led.Memory += WAIL_MEM; if (ty == 3) led.Neok += (int)Math.Round((led.Neok - nb) * (BURIED_NEOK - 1)); if (Act2) led.Neok = nb + (int)Math.Round((led.Neok - nb) * A2Reward * (num ? A2NumNeok : 1) * (s2k == 1 ? S2TurnMult : s2k == 3 ? S2FragMult : 1)); if (s2k == 1) led.Memory += 1; }
                    res.Tendo++; sentTonight++; lastTendoAt = t; fogClearUntil = t + Balance.WEATHER_PLAGUE_CLEAR_SEC;   // 천도 자리 안개 15초 걷힘
                    if (named) { namedDone = true; namedTendoed = true; }
                    if (sentTonight == Balance.NIGHT_QUOTA) res.QuotaSeconds[night] = t;
                }
                else
                {
                    int cb = led.Coin; t += 0.25 + Approach; led.DoPahon(); res.Pahon++;
                    if (ty == 2) led.Coin += (int)Math.Round((double)Balance.PAHON_COIN * MOTE_COIN * (moteN - 1)); led.Karma += (int)Math.Round(MOTE_KARMA * (moteN - 1));   // 대장 파혼이 4m 안 잔넋을 함께 파혼(엽전은 마리마다)
                    if (Growth)
                    {
                        pahonCnt++; if (pahonCnt % Balance.PAHON_STAIN_POINT_EVERY == 0) stainPts++;
                        coinAcc += Balance.PAHON_COIN * 0.2 * Math.Min(2, stainPts); int whole = (int)coinAcc; led.Coin += whole; coinAcc -= whole;   // 얼룩 점수 -> 노잣돈 2단계(+20%/단계)
                    }
                    bonusPool += others * Balance.PAHON_DAMAGE * Wd.PahonDamageMult * (Growth ? 1 + 0.1 * Math.Max(0, Math.Min(2, stainPts - 2)) : 1);   // 폭발이 이웃들을 먼저 깎아 둔다(남는 얼룩 점수는 큰 폭발로)
                    if (named) namedDone = true;
                    if (s2k == 3) { led.Coin += 2 * Balance.PAHON_COIN; t += 0.5; res.Pahon += 2; }   // 조각 셋을 따로 깨뜨린다
                    if (Act2) { led.Coin = cb + (int)Math.Round((led.Coin - cb) * (1 + (A2Reward - 1) * A2CoinMult)); if (rng.NextDouble() < A2OrePct) { led.Ore++; led.Coin += OreCoinValue; } }   // ④ 파혼 25% 광석 1(가치는 엽전으로 환산)
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
            double kill = (Act2 ? A2BossMaed : Balance.BOSS_S1_MAEDHIM) / (dps() * WR(Wd.Id)) + 1.0, sinceHit = 99;
            double take = (kill / (Balance.ENEMY_ATTACK_INTERVAL / Balance.BOSS_S1_SPEED_MULT)) * (Act2 ? A2BossDmg : Balance.BOSS_S1_DAMAGE) * HitBoss + 2 * (kill / Balance.ENEMY_ATTACK_INTERVAL) * Balance.ENEMY_ATTACK_DAMAGE * A2Dmg * HitBossAdds;   // 보스는 예비동작이 길어 읽힌다   // 보스 + 올라오는 혼 2마리
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
        res.Died = hp <= 0; res.Neok = led.Neok; res.Memory = led.Memory; res.Coin = led.Coin; res.Karma = led.Karma; res.Rank = RankOf(led.Neok);
        return res;
    }

    // 품계 곡선(기획 10-25 성장 점검): 넋 = A x (품계-1)^P. 옛 값 A40·P1.5는 22분 밤에서 2막 중간에 50품계가 되어 버려 A75·P2로 바꾼다
    static double RankA = Env("RANK_A", 75), RankP = Env("RANK_P", 2.0);
    static int NeokOf(int rank) { return (int)Math.Ceiling(RankA * Math.Pow(Math.Max(0, rank - 1), RankP)); }
    static int RankOf(int neok) { int r = 1; while (r < 50 && neok >= NeokOf(r + 1)) r++; return r; }
    static double GrowthStr(int rank) { return Env("RANK_STR", 0.05) * Math.Max(0, rank - 1); }   // 품계당 힘 5점 x 1%

    static void Hit(ref double hp, ref double sinceHit, ref RunResult res, double dmg) { hp -= dmg; res.Damage += dmg; }
    static int ForceRank = 0, PotionsUsed = 0;   // --act1 표 전용: 처결 셈으로 정한 품계를 강제로 쓰고, 회복약을 몇 번 마셨는지 센다
    static double Heal(double hp, ref int potions) { if (hp > 0 && hp <= 35 && potions > 0) { potions--; PotionsUsed++; return Math.Min(Balance.PLAYER_MAX_HP, hp + 40); } return hp; }
}
