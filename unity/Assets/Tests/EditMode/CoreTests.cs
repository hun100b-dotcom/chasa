// =============================================================================
// CoreTests.cs — 핵심 규칙 자동 검사 (Godot 스모크 테스트의 규칙 부분을 옮긴 것)
// 실행: Unity -batchmode -nographics -projectPath unity -runTests -testPlatform EditMode -testResults 결과.xml
// 숫자는 Balance.cs(= data/balance.json)에서만 읽는다. 값이 바뀌어도 '관계'가 깨지지 않는지 본다.
// =============================================================================
using Chasa.Core;
using NUnit.Framework;

public class CoreTests
{
    // ---------- 업 단계 [14-2] ----------
    [Test]
    public void KarmaTiers_Boundaries()
    {
        Assert.AreEqual(0, CoreRules.KarmaTier(9));    // K-001
        Assert.AreEqual(1, CoreRules.KarmaTier(10));   // K-002
        Assert.AreEqual(1, CoreRules.KarmaTier(29));
        Assert.AreEqual(2, CoreRules.KarmaTier(30));   // K-003
        Assert.AreEqual(3, CoreRules.KarmaTier(60));   // K-004
    }

    [Test]
    public void RewardMult_PenaltyFromTier2()
    {
        Assert.AreEqual(1.0f, CoreRules.RewardMult(9));
        Assert.AreEqual(1.0f, CoreRules.RewardMult(29));
        Assert.AreEqual(0.9f, CoreRules.RewardMult(30), 1e-4f);
    }

    // ---------- 천도 / 파혼 장부 ----------
    [Test]
    public void Tendo_GivesNeokAndMemory_ChainsStreak()
    {
        var l = new Ledger();
        l.CompleteTendo();
        Assert.AreEqual(Balance.TENDO_NEOK, l.Neok);
        Assert.AreEqual(Balance.TENDO_MEMORY, l.Memory);
        Assert.AreEqual(1, l.TendoStreak);
    }

    [Test]
    public void Pahon_GivesCoinAndKarma_BreaksStreak()
    {
        var l = new Ledger { TendoStreak = 3 };
        l.DoPahon();
        Assert.AreEqual(Balance.PAHON_COIN, l.Coin);
        Assert.AreEqual(Balance.PAHON_KARMA, l.Karma);
        Assert.AreEqual(0, l.TendoStreak);
    }

    [Test]
    public void BossPahon_KarmaIsThree()
    {
        var l = new Ledger();
        l.DoPahon(boss: true);
        Assert.AreEqual(Balance.BOSS_PAHON_KARMA, l.Karma);
        Assert.AreEqual(3, l.Karma);
    }

    [Test]
    public void KarmaDecay_EveryTwoTendo_FloorZero()
    {
        var l = new Ledger { Karma = 5 };
        l.CompleteTendo();
        Assert.AreEqual(5, l.Karma, "천도 1회: 업 그대로");
        l.CompleteTendo();
        Assert.AreEqual(4, l.Karma, "천도 2회: 업 -1");
        var z = new Ledger { Karma = 0 };
        z.CompleteTendo(); z.CompleteTendo();
        Assert.AreEqual(0, z.Karma, "업은 0 아래로 내려가지 않음");
    }

    [Test]
    public void Tendo_NeokReducedAtKarmaTier2()
    {
        var l = new Ledger { Karma = 30 };
        l.CompleteTendo();
        Assert.AreEqual((int)System.Math.Round(Balance.TENDO_NEOK * 0.9f), l.Neok);
    }

    // ---------- 캐스팅 시간 ----------
    [Test]
    public void CastTime_NormalAndChain()
    {
        Assert.AreEqual(Balance.TENDO_CAST_TIME, CoreRules.CastTime(false), 1e-4f);
        Assert.AreEqual(Balance.TENDO_CHAIN_CAST_TIME, CoreRules.CastTime(true), 1e-4f);
        Assert.Less(CoreRules.CastTime(true), CoreRules.CastTime(false));
    }

    [Test]
    public void CastTime_NeverBelowFloor_EvenWithStackedBonuses()
    {
        // 물 혼 + 눕히기 단축 + 인 자국을 전부 겹쳐도 하한에서 멈춘다
        float stacked = Balance.WATER_SOUL_CAST_BONUS + Balance.BAEK_KNOWN_CAST_BONUS + Balance.B18_STAMP_CAST_BONUS;
        Assert.AreEqual(Balance.CAST_MIN_TIME, CoreRules.CastTime(true, stacked), 1e-4f);
        Assert.AreEqual(Balance.CAST_MIN_TIME, CoreRules.CastTime(false, stacked), 1e-4f);
    }

    [Test]
    public void CastTime_WaterSoulAboveFloor_AndBossLongerThanNormal()
    {
        Assert.GreaterOrEqual(Balance.TENDO_CAST_TIME + Balance.WATER_SOUL_CAST_BONUS, Balance.CAST_MIN_TIME);
        Assert.Greater(Balance.BOSS_TENDO_CAST_TIME, Balance.TENDO_CAST_TIME);
        Assert.Less(Balance.BOSS_TENDO_CAST_TIME, 2.5f);
    }

    // ---------- 혼 상태머신 ----------
    [Test]
    public void Soul_HitsReduceMaedhim_NotKilled_ThenKneel()
    {
        var s = new Soul(SoulKind.Fresh);
        Assert.IsTrue(s.Alive);
        Assert.IsFalse(s.TakeHit(10));
        Assert.AreEqual(Balance.MAEDHIM_NORMAL - 10, s.Maedhim);
        Assert.IsTrue(s.TakeHit(Balance.MAEDHIM_NORMAL));   // 0이 됨
        Assert.AreEqual(SoulState.Kneel, s.State);
        Assert.AreEqual(Balance.WAIT_FRESH, s.WaitLeft, 1e-4f);
    }

    [Test]
    public void Soul_WaitTimeByKind()
    {
        foreach (var pair in new[] {
            (SoulKind.Fresh, Balance.WAIT_FRESH), (SoulKind.Year, Balance.WAIT_YEAR),
            (SoulKind.Old, Balance.WAIT_OLD), (SoulKind.Lump, Balance.WAIT_LUMP) })
        {
            var s = new Soul(pair.Item1);
            s.TakeHit(10000);
            Assert.AreEqual(pair.Item2, s.WaitLeft, 1e-4f, pair.Item1.ToString());
        }
        Assert.Greater(Balance.WAIT_FRESH, Balance.WAIT_YEAR);
        Assert.Greater(Balance.WAIT_YEAR, Balance.WAIT_OLD);   // 오래 떠돌수록 선택할 시간이 줄어든다
    }

    [Test]
    public void Soul_Lump_CannotTendo_OnlyPahon()
    {
        var s = new Soul(SoulKind.Lump);
        Assert.AreEqual(Balance.MAEDHIM_LUMP, s.Maedhim);
        s.TakeHit(10000);
        Assert.IsFalse(s.CanTendo);
        Assert.IsFalse(s.BeginSending());
        Assert.IsTrue(s.TryPahon());
        Assert.AreEqual(SoulState.Gone, s.State);
    }

    [Test]
    public void Soul_SendingStopsTimer_CancelResumes()
    {
        var s = new Soul(SoulKind.Year);
        s.TakeHit(10000);
        s.Tick(2f);
        float left = s.WaitLeft;
        Assert.IsTrue(s.BeginSending());
        s.Tick(100f);                           // 캐스팅 중엔 타이머 정지
        Assert.AreEqual(left, s.WaitLeft, 1e-4f);
        s.CancelSending();
        Assert.AreEqual(SoulState.Kneel, s.State);
        Assert.AreEqual(left, s.WaitLeft, 1e-4f, "남은 시간 그대로");
    }

    [Test]
    public void Soul_WaitTimeout_StandsUpWithHalfMaedhim()
    {
        var s = new Soul(SoulKind.Old);
        s.TakeHit(10000);
        s.Tick(Balance.WAIT_OLD + 0.1f);
        Assert.AreEqual(SoulState.Active, s.State);
        Assert.AreEqual((int)(s.MaedhimMax * Balance.WAIT_TIMEOUT_RECOVER), s.Maedhim);
    }

    [Test]
    public void Soul_NoDoubleJudgement()
    {
        var s = new Soul(SoulKind.Fresh);
        Assert.IsFalse(s.TryPahon(), "무릎 안 꿇은 혼은 처결 불가");
        s.TakeHit(10000);
        Assert.IsTrue(s.TryPahon());
        Assert.IsFalse(s.TryPahon(), "같은 혼을 두 번 처결할 수 없다");
        Assert.IsFalse(s.BeginSending());
    }

    [Test]
    public void Soul_Fierce_HasMoreMaedhim()
    {
        var s = new Soul(SoulKind.Fresh, fierce: true);
        Assert.AreEqual((int)(Balance.MAEDHIM_NORMAL * Balance.FIERCE_MULT), s.MaedhimMax);
    }

    // ---------- 원념 얼룩 ----------
    [Test]
    public void Stain_ThreeOverlapping_SummonsAtCentroid()
    {
        var st = new StainSet();
        float cx, cz;
        Assert.IsFalse(st.Add(0, 0, out cx, out cz));
        Assert.IsFalse(st.Add(1, 0, out cx, out cz));
        Assert.IsTrue(st.Add(0, 1, out cx, out cz));
        Assert.AreEqual(1f / 3f, cx, 1e-4f);
        Assert.AreEqual(1f / 3f, cz, 1e-4f);
        Assert.AreEqual(0, st.Count, "소환되면 얼룩은 사라진다");
    }

    [Test]
    public void Stain_FarApart_NoSummon_AndExpires()
    {
        var st = new StainSet();
        float cx, cz;
        st.Add(0, 0, out cx, out cz); st.Add(20, 0, out cx, out cz); st.Add(0, 20, out cx, out cz);
        Assert.AreEqual(3, st.Count);
        Assert.IsTrue(st.IsOnStain(0.5f, 0f));
        Assert.IsFalse(st.IsOnStain(10f, 10f));
        st.Tick(Balance.STAIN_DURATION + 0.1f);
        Assert.AreEqual(0, st.Count);
    }

    // ---------- 3막~8막 채택값 ----------
    [Test]
    public void Act3_to_8_AdoptedValues_AreConsistent()
    {
        // 장비 보상 면적 증가는 공통 상한(+40%) 이하
        Assert.LessOrEqual(CoreRules.AreaGain(3.0f, Balance.REWARD_INK_RADIUS_BONUS), Balance.REWARD_AREA_GAIN_MAX);
        Assert.LessOrEqual(CoreRules.AreaGain(5.6f, Balance.B22_ROPE_REACH_BONUS), Balance.REWARD_AREA_GAIN_MAX);
        // 버티기 성공 이득 > 파혼 회복 (쉬운 길이 성립하려면 회복이 더 작아야 한다)
        Assert.Less(Balance.B19_PAHON_HEAL, Balance.B19_HOLD_BOSS_CUT);
        // 덩어리 파혼 업 상한은 보스 파혼 업 이하
        Assert.LessOrEqual(Balance.LUMP_PAHON_KARMA_CAP, (float)Balance.BOSS_PAHON_KARMA);
        // 파도 내림 구간은 버티기 3초가 들어갈 만큼 길어야 한다
        Assert.GreaterOrEqual(Balance.B30_WAVE_PERIOD - Balance.B30_WAVE_RISE_TIME, 4.0f);
        // 시즌 3 시작 기본 천도는 B-23 기준보다 낮다 (기본값만으론 자동 통과 안 됨)
        Assert.Less(Balance.SEASON3_START_TENDO, Balance.B23_RELEASE_TENDO_MIN);
    }

    [Test]
    public void LumpPahonKarma_CappedAtThree()
    {
        Assert.AreEqual(1.0f, CoreRules.LumpPahonKarma(10), 1e-4f);
        Assert.AreEqual(3.0f, CoreRules.LumpPahonKarma(40), 1e-4f, "40몸이라도 업 +3까지만");
        Assert.AreEqual(3.0f, CoreRules.LumpPahonKarma(60), 1e-4f);
    }

    [Test]
    public void SlowStack_CappedAt35Percent()
    {
        Assert.AreEqual(0.80f, CoreRules.StackedSpeedMult(Balance.STAIN_SLOW), 1e-4f);
        Assert.AreEqual(0.65f, CoreRules.StackedSpeedMult(Balance.INK_SILT_SLOW, Balance.STAIN_SLOW, Balance.FOG_SLOW), 1e-4f);
    }

    [Test]
    public void B31Lights_ScaleWithSentPeople()
    {
        Assert.AreEqual(1, CoreRules.B31LightCount(0), "최소 1 (둑의 사내)");
        Assert.AreEqual(3, CoreRules.B31LightCount(120));
        Assert.AreEqual(7, CoreRules.B31LightCount(5000), "최대 7");
    }

    [Test]
    public void B23Release_BaekOrTendo()
    {
        Assert.IsTrue(CoreRules.B23ReleaseOk(Balance.B23_RELEASE_BAEK_MIN, 0));
        Assert.IsTrue(CoreRules.B23ReleaseOk(0, Balance.B23_RELEASE_TENDO_MIN));
        Assert.IsFalse(CoreRules.B23ReleaseOk(Balance.B23_RELEASE_BAEK_MIN - 1, Balance.B23_RELEASE_TENDO_MIN - 1));
    }

    [Test]
    public void B20Release_RatioBoundary()
    {
        // 서사 합의 표: 천도 위주 R/S 12.6 → 풀어내기, 방치형 0.37 → 파혼만
        Assert.IsTrue(CoreRules.ReleaseOk(880f, 70f));
        Assert.IsTrue(CoreRules.ReleaseOk(500f, 485f));
        Assert.IsFalse(CoreRules.ReleaseOk(230f, 625f));
        Assert.IsFalse(CoreRules.ReleaseOk(30f, 1040f));
    }

    [Test]
    public void EndingA_NeedsMemoryAndLowKarma()
    {
        Assert.IsTrue(CoreRules.EndingAOpen(Balance.ENDING_A_MEMORY_MIN, Balance.ENDING_A_KARMA_MAX - 1));
        Assert.IsFalse(CoreRules.EndingAOpen(Balance.ENDING_A_MEMORY_MIN - 1, 0), "기억 부족");
        Assert.IsFalse(CoreRules.EndingAOpen(Balance.ENDING_A_MEMORY_MIN, Balance.ENDING_A_KARMA_MAX), "업 초과");
    }

    [Test]
    public void EndingA_OpenForBalancedPlay_WithKarmaDecay()
    {
        // 균형형: 천도 500회, 파혼 300회(보스 2번 +3씩) → 업 감쇠가 있어야 A가 열린다
        var l = new Ledger();
        for (int i = 0; i < 300; i++) l.DoPahon();
        l.Karma += 2 * (Balance.BOSS_PAHON_KARMA - Balance.PAHON_KARMA);
        for (int i = 0; i < 500; i++) l.CompleteTendo();
        Assert.Less(l.Karma, Balance.ENDING_A_KARMA_MAX, "업 " + l.Karma);
        Assert.IsTrue(CoreRules.EndingAOpen(l.Memory, l.Karma));
    }

    [Test]
    public void EndingA_ClosedForPahonHeavy()
    {
        var l = new Ledger();
        for (int i = 0; i < 600; i++) l.DoPahon();
        for (int i = 0; i < 200; i++) l.CompleteTendo();
        Assert.GreaterOrEqual(l.Karma, Balance.ENDING_A_KARMA_MAX, "파혼 위주는 C로 간다");
    }

    // ---- M1: 적 공격 시계와 체력 ----
    [Test]
    public void Attack_HitsIfPlayerStaysClose()
    {
        var a = new AttackClock();
        bool hit = false;
        for (int i = 0; i < 600 && !hit; i++) hit = a.Tick(0.016f, 1.0f, true);
        Assert.IsTrue(hit, "가만히 있으면 맞는다");
    }

    [Test]
    public void Attack_MissesIfPlayerDodgesDuringWindup()
    {
        var a = new AttackClock();
        // 예비동작이 시작될 때까지 가까이 있다가, 시작되면 멀리 피한다
        while (!a.Winding) a.Tick(0.016f, 1.0f, true);
        bool hit = false;
        for (int i = 0; i < 100; i++) hit |= a.Tick(0.016f, 5.0f, true);
        Assert.IsFalse(hit, "예비동작 중 멀리 피하면 헛스윙");
        Assert.IsFalse(a.Winding);
    }

    [Test]
    public void Attack_InterruptResetsCooldown()
    {
        var a = new AttackClock();
        while (!a.Winding) a.Tick(0.016f, 1.0f, true);
        a.Interrupt();
        Assert.IsFalse(a.Winding);
        Assert.AreEqual(Balance.ENEMY_ATTACK_INTERVAL, a.Cooldown, 0.001f);
    }

    [Test]
    public void Attack_NoWindupWhenFarOrKneeling()
    {
        var a = new AttackClock();
        for (int i = 0; i < 600; i++) a.Tick(0.016f, 10f, true);
        Assert.IsFalse(a.Winding, "사거리 밖에서는 시작하지 않는다");
        a = new AttackClock();
        for (int i = 0; i < 600; i++) Assert.IsFalse(a.Tick(0.016f, 1f, false));
    }

    [Test]
    public void Ledger_HpClampsAtZero()
    {
        var l = new Ledger();
        Assert.AreEqual(Balance.PLAYER_MAX_HP, l.Hp);
        for (int i = 0; i < 20; i++) l.TakeDamage(Balance.ENEMY_ATTACK_DAMAGE);
        Assert.AreEqual(0, l.Hp);
        Assert.IsTrue(l.Dead);
        l.ResetHp();
        Assert.IsFalse(l.Dead);
    }

    // ---- M2: 하룻밤 한 판 ----
    [Test]
    public void Night_ReturnInTime_KeepsEverything()
    {
        var n = new NightRun();
        for (int i = 0; i < Balance.NIGHT_QUOTA + 2; i++) n.RecordTendo(10);
        n.Tick(Balance.NIGHT_DURATION - 1f);
        Assert.IsTrue(n.TryReturn(1f));
        Assert.AreEqual((Balance.NIGHT_QUOTA + 2) * 10, n.FinalNeok);
        Assert.AreEqual(0, n.LostNeok);
    }

    [Test]
    public void Night_Dawn_LosesOnlyExtra()
    {
        var n = new NightRun();
        for (int i = 0; i < Balance.NIGHT_QUOTA + 2; i++) n.RecordTendo(10);
        n.Tick(Balance.NIGHT_DURATION + 1f);
        Assert.AreEqual(NightPhase.Dawn, n.Phase);
        Assert.AreEqual(Balance.NIGHT_QUOTA * 10, n.FinalNeok, "명부 몫은 보존");
        Assert.AreEqual(20, n.LostNeok, "추가 수확분만 잃는다");
        Assert.IsFalse(n.TryReturn(0f), "동이 튼 뒤엔 귀환 불가");
    }

    [Test]
    public void Night_TooFarFromShrine_CannotReturn()
    {
        var n = new NightRun();
        Assert.IsFalse(n.TryReturn(Balance.SHRINE_RADIUS + 1f));
        Assert.IsFalse(n.Over);
        n.Tick(Balance.NIGHT_DURATION - Balance.NIGHT_WARN_TIME + 1f);
        Assert.IsTrue(n.Warning);
    }
}
