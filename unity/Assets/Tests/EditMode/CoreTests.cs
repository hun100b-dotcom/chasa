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
    public void Ledger_KarmaStopsAtMax()
    {
        // 업 상한 99: 파혼을 아무리 해도 99에서 멈춘다(넘친 몫은 버림)
        var l = new Ledger();
        l.Karma = 98;
        l.DoPahon(false, 0);
        l.DoPahon(false, 0);
        l.AddKarma(50f);
        Assert.AreEqual(Balance.KARMA_MAX, l.Karma);
    }

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
        for (int i = 0; i < 600; i++) l.DoPahon();   // 업은 99에서 멈춘다(상한)
        for (int i = 0; i < 60; i++) l.CompleteTendo();
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

    // ---- M3: 솔고개 지형 (아트 배치표 기반) ----
    [Test]
    public void Map_PushOutMovesBodyOutOfHouse()
    {
        var h = MapLayout.Blockers.Find(b => b.Kind == "house");
        float x = h.X, z = h.Z + 0.1f;   // 집 한가운데
        MapLayout.PushOut(ref x, ref z, 0.5f);
        float d = (float)System.Math.Sqrt((x - h.X) * (x - h.X) + (z - h.Z) * (z - h.Z));
        Assert.GreaterOrEqual(d, h.R + 0.5f - 0.01f);
    }

    [Test]
    public void Map_BoundaryClamped()
    {
        float x = 999f, z = -999f;
        MapLayout.PushOut(ref x, ref z, 0.5f);
        Assert.AreEqual(MapLayout.MaxX - 0.5f, x, 0.001f);
        Assert.AreEqual(MapLayout.MinZ + 0.5f, z, 0.001f);
    }

    [Test]
    public void Map_StartIsFree_AndStoryPlacesReachable()
    {
        Assert.IsFalse(MapLayout.IsBlocked(0f, 0f, 0.5f), "출발점이 막히면 안 된다");
        Assert.IsFalse(MapLayout.IsBlocked(MapLayout.BossX, MapLayout.BossZ, 1.0f), "보스 자리가 막힘");
        Assert.IsFalse(MapLayout.IsBlocked(MapLayout.NamedX, MapLayout.NamedZ, 0.6f), "이름혼 자리가 막힘");
        Assert.IsTrue(MapLayout.Reachable(MapLayout.BossX, MapLayout.BossZ, 0.6f), "보스까지 길이 없다");
        Assert.IsTrue(MapLayout.Reachable(MapLayout.NamedX, MapLayout.NamedZ, 0.6f), "이름혼 자리까지 길이 없다");
        foreach (var c in MapLayout.ClueCells)
        {
            float x = MapLayout.WorldX(c[1]), z = MapLayout.WorldZ(c[0]);
            Assert.IsFalse(MapLayout.IsBlocked(x, z, 0.6f), "단서 자리가 막힘 " + c[0] + "," + c[1]);
            Assert.IsTrue(MapLayout.Reachable(x, z, 0.6f), "단서까지 길이 없다 " + c[0] + "," + c[1]);
        }
    }

    [Test]
    public void Map_DataMatchesGrid()
    {
        Assert.AreEqual(MapData.Rows, MapData.Ground.Length);
        foreach (var row in MapData.Ground) Assert.AreEqual(MapData.Cols, row.Length);
        Assert.Greater(MapLayout.Blockers.Count, 5);
    }

    // ---- M4: 이름혼·보스·단서 ----
    [Test]
    public void Boss_TendoNeedsThreeClues()
    {
        var b = Soul.MakeBossS1();
        Assert.IsFalse(b.CanTendoWith(2), "단서 2개 이하면 천도 불가 — 파혼만");
        Assert.IsTrue(b.CanTendoWith(Balance.BOSS_CLUES_REQUIRED));
        Assert.IsTrue(new Soul(SoulKind.Fresh).CanTendoWith(0), "일반 혼은 단서와 무관");
    }

    [Test]
    public void Boss_Act2And3Rewards_ScaleWithRing()
    {
        // 기획 표: 고리 1.5/1.75/2.0/2.25 → 넋 60/70/80/90, 엽전 36/42/48/54. 1막 보스는 60/30 그대로
        Assert.AreEqual(60, Bosses.NeokFor(5)); Assert.AreEqual(70, Bosses.NeokFor(6)); Assert.AreEqual(80, Bosses.NeokFor(9)); Assert.AreEqual(90, Bosses.NeokFor(12));
        Assert.AreEqual(36, Bosses.CoinFor(8)); Assert.AreEqual(42, Bosses.CoinFor(7)); Assert.AreEqual(48, Bosses.CoinFor(11)); Assert.AreEqual(54, Bosses.CoinFor(10));
        Assert.AreEqual(50, Bosses.NeokFor(2)); Assert.AreEqual(Balance.BOSS_PAHON_COIN, Bosses.CoinFor(3));
        var l = new Ledger(); l.DoPahon(true, 12); Assert.AreEqual(54, l.Coin);
    }

    [Test]
    public void Boss_RewardsAreBigger_AndPahonPaysMoreCoin()
    {
        var l = new Ledger();
        int g = l.CompleteBossTendo();
        Assert.Greater(g, Balance.TENDO_NEOK * 3);
        var l2 = new Ledger(); l2.DoPahon(true);
        Assert.Greater(l2.Coin, Balance.PAHON_COIN * 3, "보스 파혼은 천도 쏠림을 막을 만큼 후하다");
        Assert.AreEqual(Balance.BOSS_PAHON_KARMA, l2.Karma);
    }

    [Test]
    public void Named_SpawnsOnceAsLastOfQuota()
    {
        var n = new NightRun();
        Assert.IsFalse(n.TakeNamedSpawn());
        for (int i = 0; i < Balance.NIGHT_QUOTA - 1; i++) n.RecordTendo(10);
        Assert.IsTrue(n.TakeNamedSpawn());
        Assert.IsFalse(n.TakeNamedSpawn(), "한 번만");
    }

    [Test]
    public void BossNeok_IsExtra_LostAtDawn()
    {
        var n = new NightRun();
        for (int i = 0; i < Balance.NIGHT_QUOTA; i++) n.RecordTendo(10);
        n.RecordBoss(60);
        n.Tick(Balance.NIGHT_DURATION + 1f);
        Assert.AreEqual(Balance.NIGHT_QUOTA * 10, n.FinalNeok);
        Assert.AreEqual(60, n.LostNeok);
    }

    [Test]
    public void Clues_CapAtRequired()
    {
        var n = new NightRun();
        for (int i = 0; i < 10; i++) n.PickClue();
        Assert.AreEqual(Balance.BOSS_CLUES_REQUIRED, n.Clues);
    }

    // ---- M4.5: 무기·도술·장비 ----
    [Test]
    public void Weapon_MaceLeansPahon()
    {
        Assert.GreaterOrEqual(WeaponDef.Mace.PahonDamageMult, 0.9f);   // 10-25 시뮬로 1.2→0.9 (땅울림 포함 판정). 방망이의 파혼 맛은 넉백 배율이 맡는다
        Assert.Greater(WeaponDef.Mace.PahonKnockbackMult, WeaponDef.Chain.PahonKnockbackMult);
        Assert.AreEqual(WeaponDef.Mace, WeaponDef.Get(WeaponId.Mace));
        // 무기 3계열 추가: 정의가 서로 구별되고, Q 기술·관통 상한이 기획대로인지
        Assert.AreEqual(WeaponDef.Bell, WeaponDef.Get(WeaponId.Bell));
        Assert.AreEqual(WeaponDef.Trident, WeaponDef.Get(WeaponId.Trident));
        Assert.AreEqual(WeaponDef.Brush, WeaponDef.Get(WeaponId.Brush));
        Assert.IsTrue(WeaponDef.Chain.HasPull);                       // 견인은 사슬만
        Assert.IsFalse(WeaponDef.Mace.HasPull || WeaponDef.Bell.HasPull || WeaponDef.Trident.HasPull || WeaponDef.Brush.HasPull);
        Assert.AreEqual(3, WeaponDef.Trident.MaxHits);                // 삼지창 관통 3
        Assert.AreEqual(1, WeaponDef.Brush.MaxHits);                  // 붓은 한 마리
        Assert.IsTrue(WeaponDef.Brush.Projectile);                    // 붓만 투사체
        Assert.IsFalse(WeaponDef.Chain.Projectile || WeaponDef.Mace.Projectile || WeaponDef.Bell.Projectile || WeaponDef.Trident.Projectile);
        Assert.AreEqual(0, WeaponDef.Bell.MaxHits);                   // 요령은 원 범위(제한 없음)
    }

    [Test]
    public void SkillBar_CooldownCycle()
    {
        var b = new SkillBar();
        Assert.IsTrue(b.TryUse(0));
        Assert.IsFalse(b.TryUse(0), "쿨다운 중엔 못 쓴다");
        b.Tick(SkillDef.All[0].Cooldown + 0.01f);
        Assert.IsTrue(b.Ready(0));
        Assert.IsTrue(b.TryUse(1), "다른 칸은 독립");
    }

    [Test]
    public void Gear_CapsHold()
    {
        var it = new ItemDef { Slot = Slot.Weapon, Rarity = Rarity.Rare };
        it.Options.Add(new OptionRoll(Opt.DamagePct, 0.9f));
        it.Options.Add(new OptionRoll(Opt.CastReducePct, 0.9f));
        it.Options.Add(new OptionRoll(Opt.PahonAreaPct, 0.9f));
        var st = new GearStats(); st.Add(it);
        Assert.AreEqual(1f + Balance.CAP_DAMAGE_PCT, st.DamageMult, 0.001f);
        Assert.AreEqual(1f - Balance.CAP_CAST_REDUCE_PCT, st.CastMult, 0.001f);
        Assert.LessOrEqual(st.PahonRadius(2.5f), 2.5f * (float)System.Math.Sqrt(1f + Balance.CAP_PAHON_AREA_PCT) + 0.001f);
    }

    [Test]
    public void Gear_CastMinFloorRespected()
    {
        // 장비가 캐스팅을 최대로 줄여도 하한 0.5초 아래로 못 간다
        var st = new GearStats { CastReducePct = 5f };
        Assert.AreEqual(1f - Balance.CAP_CAST_REDUCE_PCT, st.CastMult, 0.001f, "단축은 상한에서 멈춘다");
        float t = CoreRules.CastTimeScaled(true, 0.01f);
        Assert.GreaterOrEqual(t, Balance.CAST_MIN_TIME);
    }

    [Test]
    public void Loot_FierceAlwaysRare_WithGradient()
    {
        var rnd = new System.Random(1);
        for (int i = 0; i < 50; i++)
        {
            var it = Loot.Roll(() => (float)rnd.NextDouble(), true);
            Assert.IsNotNull(it);
            Assert.AreEqual(Rarity.Rare, it.Rarity);
            Assert.IsTrue(it.Gradient);
            Assert.IsTrue(it.Options.Exists(o => o.Kind == Opt.CastReducePct && o.Value < 0f), "기울기: 천도 느려짐 줄이 있다");
        }
    }

    [Test]
    public void Loot_DropRateRoughlyMatches()
    {
        var rnd = new System.Random(7);
        int drops = 0;
        for (int i = 0; i < 4000; i++) if (Loot.Roll(() => (float)rnd.NextDouble(), false) != null) drops++;
        Assert.AreEqual(Balance.DROP_CHANCE, drops / 4000f, 0.04f);
    }

    [Test]
    public void Equipment_BetterReplacesWorse_NamedBeatsRare()
    {
        var eq = new Equipment();
        var common = new ItemDef { Slot = Slot.Charm, Rarity = Rarity.Common };
        Assert.IsTrue(eq.TryEquip(common));
        Assert.IsFalse(eq.TryEquip(common), "같은 물건은 교체하지 않는다");
        Assert.IsTrue(eq.TryEquip(ItemDef.MoonflowerBell()));
        var st = eq.Stats();
        Assert.AreEqual(Balance.MOONFLOWER_BELL_PAHON_RADIUS, st.PahonRadiusM, 0.001f);
    }

    [Test]
    public void Stain_RemoveNearest_RemovesOnlyOneWithoutKarma()
    {
        var st = new StainSet(); float cx, cz;
        st.Add(0f, 0f, out cx, out cz); st.Add(10f, 0f, out cx, out cz);
        float ox, oz;
        Assert.IsTrue(st.RemoveNearest(1f, 0f, 3f, out ox, out oz));
        Assert.AreEqual(0f, ox, 0.001f);
        Assert.AreEqual(1, st.Count);
        Assert.IsFalse(st.RemoveNearest(1f, 0f, 3f, out ox, out oz), "범위 밖은 못 지운다");
    }

    [Test]
    public void Ledger_MaxHpGrowsRaisesHp()
    {
        var l = new Ledger();
        l.TakeDamage(30);
        l.SetMaxHp(Balance.PLAYER_MAX_HP + 20);
        Assert.AreEqual(Balance.PLAYER_MAX_HP - 30 + 20, l.Hp);
        l.ResetHp();
        Assert.AreEqual(Balance.PLAYER_MAX_HP + 20, l.Hp);
    }

    // ---- M6: 한 판 통합 시나리오 (화면 없이 규칙만으로 처음부터 끝까지) ----
    [Test]
    public void FullNight_Scenario_ReturnsWithBossAndGear()
    {
        var ledger = new Ledger(); var night = new NightRun(); var eq = new Equipment();
        var rnd = new System.Random(3);
        // 무명 혼 몫-1마리 천도 → 이름혼 등장 → 이름혼 천도(몫 완성)
        for (int i = 0; i < Balance.NIGHT_QUOTA - 1; i++)
        {
            var s = new Soul(SoulKind.Fresh);
            Assert.IsTrue(s.TakeHit(1000));
            Assert.IsTrue(s.BeginSending());
            int before = ledger.Neok; ledger.CompleteTendo(); night.RecordTendo(ledger.Neok - before); s.Finish();
            var it = Loot.Roll(() => (float)rnd.NextDouble(), false); if (it != null) eq.TryEquip(it);
        }
        Assert.IsTrue(night.TakeNamedSpawn());
        var named = Soul.Named("Bak Dolsoe", SoulKind.Fresh, Balance.NAMED_MAEDHIM);
        Assert.IsTrue(named.TakeHit(1000)); Assert.IsTrue(named.BeginSending());
        int b2 = ledger.Neok; ledger.CompleteTendo(); night.RecordTendo(ledger.Neok - b2); named.Finish();
        Assert.IsTrue(night.QuotaDone);
        // 보스: 단서 없이는 천도 불가 → 단서 3개 후 천도
        var boss = Soul.MakeBossS1();
        Assert.IsTrue(boss.TakeHit(Balance.BOSS_S1_MAEDHIM));
        Assert.IsFalse(boss.CanTendoWith(night.Clues));
        for (int i = 0; i < 3; i++) night.PickClue();
        Assert.IsTrue(boss.CanTendoWith(night.Clues));
        Assert.IsTrue(boss.BeginSending());
        night.RecordBoss(ledger.CompleteBossTendo()); boss.Finish();
        // 귀환
        night.Tick(Balance.NIGHT_DURATION * 0.6f);
        Assert.IsTrue(night.TryReturn(1f));
        Assert.AreEqual(NightPhase.Returned, night.Phase);
        Assert.AreEqual(0, night.LostNeok);
        Assert.AreEqual(night.KeptNeok + night.ExtraNeok, night.FinalNeok);
        Assert.Greater(night.ExtraNeok, 0, "보스 보상이 추가 수확분으로 남는다");
    }

    [Test]
    public void FullNight_Scenario_DawnLosesBossReward()
    {
        var ledger = new Ledger(); var night = new NightRun();
        for (int i = 0; i < Balance.NIGHT_QUOTA; i++) { int b = ledger.Neok; ledger.CompleteTendo(); night.RecordTendo(ledger.Neok - b); }
        for (int i = 0; i < 3; i++) night.PickClue();
        night.RecordBoss(ledger.CompleteBossTendo());
        night.Tick(Balance.NIGHT_DURATION + 1f);
        Assert.AreEqual(NightPhase.Dawn, night.Phase);
        Assert.AreEqual(night.KeptNeok, night.FinalNeok, "몫은 보존");
        Assert.AreEqual(Bosses.NeokFor(1), night.LostNeok, "보스 보상은 흩어진다");
        Assert.Greater(ledger.Neok, night.FinalNeok, "장부엔 쌓였지만 확정 수확은 줄어든다(결과 화면 표시 기준)");
    }

    [Test]
    public void Night_CoinAfterQuotaScatters_AtDawn()
    {
        var n = new NightRun();
        n.RecordCoin(5);                                   // 몫 전: 보존
        for (int i = 0; i < Balance.NIGHT_QUOTA; i++) n.RecordTendo(10);
        n.RecordCoin(5); n.RecordCoin(30);                 // 몫 뒤: 명부 밖
        n.Tick(Balance.NIGHT_DURATION + 1f);
        Assert.AreEqual(5, n.FinalCoin);
        Assert.AreEqual(35, n.LostCoin);
        var n2 = new NightRun();
        for (int i = 0; i < Balance.NIGHT_QUOTA; i++) n2.RecordTendo(10);
        n2.RecordCoin(35);
        Assert.IsTrue(n2.TryReturn(0f));
        Assert.AreEqual(35, n2.FinalCoin);
        Assert.AreEqual(0, n2.LostCoin);
    }

    [Test]
    public void Gear_TiltBarLeansWithBuild()
    {
        Assert.AreEqual(0f, new GearStats().Tilt(), 0.001f);
        Assert.Less(new GearStats { CastReducePct = 0.3f }.Tilt(), -0.9f, "천도 빌드는 왼쪽(-)");
        Assert.Greater(new GearStats { PahonDamagePct = 0.5f, PahonAreaPct = 0.4f }.Tilt(), 0.9f, "파혼 빌드는 오른쪽(+)");
    }

    [Test]
    public void Data_OverridesApply()
    {
        string oldName = SkillDef.All[1].Name; float oldCd = SkillDef.All[1].Cooldown;
        Assert.IsTrue(SkillDef.Override("Bind", "Tie Up", 7f));
        Assert.AreEqual("Tie Up", SkillDef.All[1].Name);
        Assert.AreEqual(7f, SkillDef.All[1].Cooldown);
        Assert.IsFalse(SkillDef.Override("NoSuch", "x", 1f));
        SkillDef.Override("Bind", oldName, oldCd);   // 다른 테스트에 영향이 없게 되돌린다
        float oldBase = Loot.GetBase(Opt.DamagePct);
        Assert.IsTrue(Loot.SetBase("DamagePct", 0.1f));
        Assert.AreEqual(0.1f, Loot.GetBase(Opt.DamagePct));
        Assert.IsFalse(Loot.SetBase("PahonRadiusM", 1f), "이름 있는 물건 전용 옵션은 굴림 값이 아니다");
        Loot.SetBase("DamagePct", oldBase);
    }

    // ---- 기울기 옵션 6종 (기획 growth.json tilts) ------------------------------------------
    static GearStats StatsOf(string tiltId)
    {
        var it = new ItemDef { Slot = Slot.Charm, Rarity = Rarity.Rare, Gradient = true, TiltId = tiltId };
        it.Options.AddRange(TiltDef.Find(tiltId).Options);
        var st = new GearStats(); st.Add(it); return st;
    }

    [Test]
    public void 기울기_향내음_넋은_늘고_파혼엽전은_절반()
    {
        var st = StatsOf("tilt_neok_coin");
        Assert.AreEqual(1.25f, st.TendoNeokMult, 1e-4f);
        Assert.AreEqual(0.5f, st.PahonCoinMult, 1e-4f);
        Assert.Less(st.Tilt(), 0f, "천도 쪽 기울기");
    }

    [Test]
    public void 기울기_검은술_반경은_늘고_대기는_짧아지되_덩어리와_하한은_지킨다()
    {
        var st = StatsOf("tilt_radius_wait");
        Assert.AreEqual(3.3f, st.PahonRadius(3.0f), 1e-3f);
        Assert.AreEqual(4.5f, st.AdjustWait(5.0f, false), 1e-4f);
        Assert.AreEqual(5.0f, st.AdjustWait(5.0f, true), 1e-4f, "덩어리는 대기 단축 제외");
        Assert.AreEqual(Balance.WAIT_FLOOR, st.AdjustWait(0.8f, false), 1e-4f, "하한 아래로 못 내려간다");
        Assert.Greater(st.Tilt(), 0f, "파혼 쪽 기울기");
    }

    [Test]
    public void 기울기_젖은소매_연속창은_길고_피해는_줄어든다()
    {
        var st = StatsOf("tilt_window_dmg");
        Assert.AreEqual(Balance.TENDO_CHAIN_WINDOW + 1.5f, st.ChainWindow, 1e-4f);
        Assert.AreEqual(0.9f, st.DamageMult, 1e-4f);
    }

    [Test]
    public void 기울기_깨진거울_넉백은_늘고_시야는_하한까지만_좁아진다()
    {
        var st = StatsOf("tilt_kb_vision");
        Assert.AreEqual(1.3f, st.PahonKnockbackMult, 1e-4f);
        Assert.AreEqual(0.55f, st.VisionRatio(0.6f), 1e-4f);
        var two = new GearStats(); two.VisionShift = -0.2f;
        Assert.AreEqual(Balance.VISION_RATIO_FLOOR, two.VisionRatio(0.6f), 1e-4f, "여러 개 껴도 하한");
    }

    [Test]
    public void 기울기_상복자락_시전중_피해는_줄고_공격속도는_느려진다()
    {
        var st = StatsOf("tilt_castdr_aspd");
        Assert.AreEqual(0.8f, st.CastDamageTakenMult, 1e-4f);
        Assert.AreEqual(0.92f, st.AttackSpeedMult, 1e-4f);
    }

    [Test]
    public void 기울기_기본_드롭은_시연판_하나만_AllTilts면_여섯종이_나온다()
    {
        var rnd = new System.Random(7);
        for (int i = 0; i < 50; i++)
        {
            var it = Loot.Roll(() => (float)rnd.NextDouble(), true);   // 사나운 적 = 귀한 확정
            Assert.AreEqual("tilt_dmg_cast", it.TiltId);
        }
        Loot.AllTilts = true;
        try
        {
            var seen = new System.Collections.Generic.HashSet<string>();
            for (int i = 0; i < 300; i++) seen.Add(Loot.Roll(() => (float)rnd.NextDouble(), true).TiltId);
            Assert.AreEqual(6, seen.Count);
        }
        finally { Loot.AllTilts = false; }
    }

    // ---- 낮 (기획서 부록 B) ----------------------------------------------------------------
    static DayRun NewDay()
    {
        var d = new DayRun(false);
        d.Spots.Add(new ClueSpot { Id = "listen", Verb = ClueVerb.Eavesdrop, Kind = SpotKind.BossClue, HumanSpeech = true });
        d.Spots.Add(new ClueSpot { Id = "watch", Verb = ClueVerb.Watch, Kind = SpotKind.BossClue, HumanSpeech = false });
        d.Spots.Add(new ClueSpot { Id = "touch", Verb = ClueVerb.Touch, Kind = SpotKind.BossClue });
        d.Spots.Add(new ClueSpot { Id = "house", Verb = ClueVerb.Watch, Kind = SpotKind.NamedHouse });
        d.Spots.Add(new ClueSpot { Id = "rumor", Verb = ClueVerb.Eavesdrop, Kind = SpotKind.Rumor, HumanSpeech = true });
        return d;
    }

    static bool Finish(DayRun d, ClueSpot s, int karma)
    {
        var a = d.Begin(s, karma);
        if (a == null) return false;
        Assert.IsTrue(a.Tick(a.Need + 0.01f, 0f));
        d.Complete(a);
        return true;
    }

    [Test]
    public void 낮_눈금은_세개_동사_성공마다_하나씩_줄고_다_쓰면_해질녘()
    {
        var d = NewDay();
        Assert.AreEqual(3, d.TicksLeft);
        Finish(d, d.Spots[0], 0); Assert.AreEqual(2, d.TicksLeft);
        Finish(d, d.Spots[1], 0); Assert.AreEqual(1, d.TicksLeft);
        Assert.AreEqual(DayPhase.Day, d.Phase);
        Finish(d, d.Spots[2], 0); Assert.AreEqual(0, d.TicksLeft);
        Assert.AreEqual(DayPhase.Dusk, d.Phase);
        Assert.AreEqual(3, d.BossClues);
        Assert.IsNull(d.Begin(d.Spots[3], 0), "눈금이 없으면 제사 집을 못 본다");
    }

    [Test]
    public void 낮_엿듣기는_원밖으로_나가면_처음부터_눈금도_안_줄어든다()
    {
        var d = NewDay();
        var a = d.Begin(d.Spots[0], 0);
        a.Tick(4f, 1f);
        Assert.AreEqual(4f, a.Progress, 1e-4f);
        a.Tick(0.1f, Balance.EAVESDROP_RADIUS + 0.5f);          // 원 밖
        Assert.AreEqual(0f, a.Progress, 1e-4f, "끊기면 처음부터");
        Assert.IsFalse(a.Tick(5.9f, 1f), "6초 못 채움");
        Assert.AreEqual(3, d.TicksLeft, "성공 전에는 눈금이 줄지 않는다");
    }

    [Test]
    public void 낮_만져보기는_끊기지_않고_멈출_뿐()
    {
        var d = NewDay();
        var a = d.Begin(d.Spots[2], 0);
        a.Tick(1f, 0.5f);
        a.Tick(1f, 99f);   // 멀어져도
        Assert.AreEqual(1f, a.Progress, 1e-4f);
    }

    [Test]
    public void 낮_업이_귀를_닫는다_10반쪽_30보스엿듣기닫힘_60소문닫힘_내려가면_다시_열림()
    {
        var d = NewDay();
        Assert.AreEqual(3.0f, DayRun.EarRadius(0));
        Assert.AreEqual(2.0f, DayRun.EarRadius(10), "업 10: 원이 2m로");
        Assert.IsTrue(d.Begin(d.Spots[0], 10).Half, "업 10: 사람 말 단서는 반쪽");
        Assert.IsFalse(d.Begin(d.Spots[1], 10).Half, "사람 말이 없는 지켜보기는 그대로");
        Assert.AreEqual(SpotAccess.Closed, d.Access(d.Spots[0], 30), "업 30: 보스 엿듣기 닫힘");
        Assert.AreEqual(SpotAccess.Open, d.Access(d.Spots[4], 30), "업 30: 마을 소문은 아직");
        Assert.AreEqual(SpotAccess.Open, d.Access(d.Spots[1], 30), "보스 지켜보기는 열림");
        Assert.AreEqual(SpotAccess.Closed, d.Access(d.Spots[4], 60), "업 60: 소문도 닫힘");
        Assert.AreEqual(SpotAccess.Open, d.Access(d.Spots[0], 28), "업이 내려가면 다시 열림");
    }

    [Test]
    public void 낮_반쪽_단서도_한개로_세고_보스천도는_세개부터()
    {
        var d = NewDay();
        Finish(d, d.Spots[0], 10);
        Assert.AreEqual(1, d.BossClues); Assert.AreEqual(1, d.HalfClues);
        Assert.AreEqual(3, d.TotalBossClues(2));
    }

    [Test]
    public void 낮_제사집을_지켜보면_이름혼이_명부에_오르지만_보스단서는_늘지_않는다()
    {
        var d = NewDay();
        Finish(d, d.Spots[3], 0);
        Assert.IsTrue(d.NamedHouseWatched);
        Assert.AreEqual(0, d.BossClues);
        Assert.AreEqual(2, d.TicksLeft, "눈금은 같이 쓴다 — 보스냐 이름혼이냐");
    }

    [Test]
    public void 낮_장례는_눈금0_70초_건너뛸수있고_할것없는_낮은_짧아진다()
    {
        var d = new DayRun(true);
        Assert.IsFalse(d.NothingToDo(0), "장례가 있으면 할 것이 있다");
        Assert.IsFalse(d.WatchFuneral(69f));
        Assert.IsTrue(d.WatchFuneral(1f));
        Assert.AreEqual(3, d.TicksLeft, "장례는 눈금을 쓰지 않는다");
        Assert.IsTrue(d.NothingToDo(0), "열린 자리도 남은 장례도 없다");
        var d2 = new DayRun(true); d2.SkipFuneral();
        Assert.IsTrue(d2.NothingToDo(0));
        var d3 = NewDay(); foreach (var sp in d3.Spots) sp.Done = true;
        Assert.IsTrue(d3.NothingToDo(0));
    }

    [Test]
    public void 낮_업_60이면_소문과_보스엿듣기가_닫혀_할것이_줄어든다()
    {
        var d = new DayRun(false);
        d.Spots.Add(new ClueSpot { Id = "a", Verb = ClueVerb.Eavesdrop, Kind = SpotKind.Rumor });
        d.Spots.Add(new ClueSpot { Id = "b", Verb = ClueVerb.Eavesdrop, Kind = SpotKind.BossClue });
        Assert.IsFalse(d.NothingToDo(0));
        Assert.IsTrue(d.NothingToDo(60));
    }

    [Test]
    public void 낮_해넘기기는_눈금이_남아도_해질녘()
    {
        var d = NewDay(); d.SkipToDusk();
        Assert.AreEqual(DayPhase.Dusk, d.Phase);
        Assert.IsNull(d.Begin(d.Spots[0], 0));
    }

    // ---- 서낭당 시설 -------------------------------------------------------------------------
    [Test]
    public void 공물상_가격과_한밤_한도_회복약()
    {
        var l = new Ledger { Coin = 15 * 5 + 14 }; var p = new Pack();
        for (int i = 0; i < 5; i++) Assert.IsTrue(Shrine.Buy(ShopItem.HealPotion, l, p));
        Assert.IsFalse(Shrine.Buy(ShopItem.HealPotion, l, p), "한 밤 5개까지");
        Assert.AreEqual(14, l.Coin);
        l.Coin = 100;
        Assert.IsTrue(Shrine.Buy(ShopItem.DawnCharm, l, p)); Assert.AreEqual(60, l.Coin);
        Assert.IsFalse(Shrine.Buy(ShopItem.DawnCharm, l, p), "새벽 부적은 한 밤 1장");
        Assert.IsTrue(Shrine.Buy(ShopItem.CleanseCharm, l, p)); Assert.AreEqual(30, l.Coin);
    }

    [Test]
    public void 공물상_회복약은_생명_40퍼센트_엽전으로_넋은_못_산다()
    {
        var l = new Ledger { Coin = 15 }; var p = new Pack();
        Shrine.Buy(ShopItem.HealPotion, l, p);
        l.Hp = 10;
        Assert.IsTrue(Shrine.UseHeal(l, p));
        Assert.AreEqual(10 + (int)System.Math.Round(l.MaxHp * 0.4f), l.Hp);
        int neok = l.Neok, mem = l.Memory;
        Shrine.Buy(ShopItem.HealPotion, l, p);
        Assert.AreEqual(neok, l.Neok); Assert.AreEqual(mem, l.Memory);
    }

    [Test]
    public void 손보기_다시굴리기_비용은_40에서_20씩_오르고_200이_상한_기울기와_이름물건은_불가()
    {
        Assert.AreEqual(40, Shrine.RerollCost(0));
        Assert.AreEqual(60, Shrine.RerollCost(1));
        Assert.AreEqual(200, Shrine.RerollCost(9));
        Assert.AreEqual(200, Shrine.RerollCost(30));
        var rnd = new System.Random(3);
        var it = new ItemDef { Slot = Slot.Robe, Rarity = Rarity.Crafted };
        it.Options.Add(new OptionRoll(Opt.DamagePct, 0.05f)); it.Options.Add(new OptionRoll(Opt.HpFlat, 8f));
        var l = new Ledger { Coin = 100 };
        Assert.IsTrue(Shrine.Reroll(it, 0, l, () => (float)rnd.NextDouble()));
        Assert.AreEqual(60, l.Coin); Assert.AreEqual(1, it.Rerolls);
        Assert.AreNotEqual(Opt.DamagePct, it.Options[0].Kind, "다른 종류로 굴러야 한다");
        Assert.AreEqual(Opt.HpFlat, it.Options[1].Kind, "다른 옵션은 그대로");
        Assert.AreEqual(2, new System.Collections.Generic.HashSet<Opt> { it.Options[0].Kind, it.Options[1].Kind }.Count, "옵션 종류 중복 없음");
        Assert.IsFalse(Shrine.CanReroll(new ItemDef { Gradient = true, Options = { new OptionRoll(Opt.DamagePct, 0.2f) } }));
        Assert.IsFalse(Shrine.CanReroll(ItemDef.MoonflowerBell()));
        l.Coin = 10;
        Assert.IsFalse(Shrine.Reroll(it, 0, l, () => 0.5f), "엽전이 모자라면 안 된다");
    }

    [Test]
    public void 손보기_매듭올리기_비용과_옵션칸_늘어남_귀한위는_불가()
    {
        var rnd = new System.Random(5);
        var it = new ItemDef { Slot = Slot.Weapon, Rarity = Rarity.Common };
        it.Options.Add(new OptionRoll(Opt.DamagePct, 0.03f));
        var l = new Ledger { Coin = 60 + 180, Ore = 3 + 10 };
        Assert.IsTrue(Shrine.Upgrade(it, l, () => (float)rnd.NextDouble()));
        Assert.AreEqual(Rarity.Crafted, it.Rarity); Assert.AreEqual(2, it.Options.Count);
        Assert.AreEqual(0.03f * 0.8f / 0.5f, it.Options[0].Value, 1e-5f, "범위가 새 등급 것으로");
        Assert.AreEqual(180, l.Coin); Assert.AreEqual(10, l.Ore);
        Assert.IsTrue(Shrine.Upgrade(it, l, () => (float)rnd.NextDouble()));
        Assert.AreEqual(Rarity.Rare, it.Rarity); Assert.AreEqual(3, it.Options.Count);
        Assert.AreEqual(0, l.Coin); Assert.AreEqual(0, l.Ore);
        Assert.IsFalse(Shrine.CanUpgrade(it), "귀한 위로는 못 올린다");
        Assert.IsFalse(Shrine.CanUpgrade(ItemDef.MoonflowerBell()));
        var poor = new Ledger { Coin = 59, Ore = 3 };
        Assert.IsFalse(Shrine.Upgrade(new ItemDef { Rarity = Rarity.Common }, poor, () => 0.1f));
    }

    [Test]
    public void 손보기_풀기는_공짜_광석_1_3_8_홈뚫기_80_240_최대2()
    {
        var l = new Ledger();
        Assert.IsTrue(Shrine.Dismantle(new ItemDef { Rarity = Rarity.Common }, l)); Assert.AreEqual(1, l.Ore);
        Assert.IsTrue(Shrine.Dismantle(new ItemDef { Rarity = Rarity.Crafted }, l)); Assert.AreEqual(4, l.Ore);
        Assert.IsTrue(Shrine.Dismantle(new ItemDef { Rarity = Rarity.Rare }, l)); Assert.AreEqual(12, l.Ore);
        Assert.IsFalse(Shrine.Dismantle(ItemDef.MoonflowerBell(), l), "이름 있는 물건은 못 푼다");
        var it = new ItemDef { Rarity = Rarity.Common };
        l.Coin = 80 + 240 + 1000;
        Assert.IsTrue(Shrine.Socket(it, l)); Assert.AreEqual(1000 + 240, l.Coin);
        Assert.IsTrue(Shrine.Socket(it, l)); Assert.AreEqual(1000, l.Coin);
        Assert.IsFalse(Shrine.Socket(it, l), "최대 2개");
    }

    [Test]
    public void 업_감쇠는_천도와_눕히기를_같이_세어_2회마다_1()
    {
        var l = new Ledger { Karma = 5 };
        l.CompleteTendo();                    // 1회: 변화 없음
        Assert.AreEqual(5, l.Karma);
        l.CompleteLay();                      // 2회째(눕히기): -1
        Assert.AreEqual(4, l.Karma);
        l.CompleteLay(); l.CompleteTendo();   // 4회째: -1
        Assert.AreEqual(3, l.Karma);
        Assert.AreEqual(4, l.TendoTotal);
    }

    [Test]
    public void 체력_회복_서낭당은_빠르고_밖은_맞고_4초_뒤_천천히()
    {
        var l = new Ledger(); l.Hp = 50;
        Assert.AreEqual(0, l.Regen(1f, false, 1f), "맞은 직후 밖에서는 회복 없음");
        Assert.AreEqual(50, l.Hp);
        l.Regen(1f, false, Balance.REGEN_DELAY);
        Assert.AreEqual(52, l.Hp, "밖에서 초당 2");
        l.Regen(1f, true, 0f);
        Assert.AreEqual(64, l.Hp, "서낭당 안은 맞은 직후에도 초당 12");
        for (int i = 0; i < 100; i++) l.Regen(1f, true, 0f);
        Assert.AreEqual(l.MaxHp, l.Hp, "최대 체력을 넘지 않는다");
        var dead = new Ledger { Hp = 0 };
        Assert.AreEqual(0, dead.Regen(5f, true, 99f), "쓰러진 뒤에는 회복 없음");
    }

    [Test]
    public void 첫밤_적_수는_3_공격_10_주기_2_6_체력_100_회복약_2()
    {
        Assert.AreEqual(3, Balance.ENEMY_COUNT);
        Assert.AreEqual(10, Balance.ENEMY_ATTACK_DAMAGE);
        Assert.AreEqual(2.6f, Balance.ENEMY_ATTACK_INTERVAL, 1e-4f);
        Assert.AreEqual(2, Balance.FIRST_NIGHT_HEAL);
    }

    // ---------- 임시 효과음 합성 ----------
    [Test]
    public void 효과음_모든_id가_만들어지고_최대_크기가_마이너스1dB_이하()
    {
        foreach (var id in SfxSynth.Ids)
        {
            var b = SfxSynth.Render(id);
            Assert.IsNotNull(b, id);
            Assert.Greater(b.Length, SfxSynth.Rate / 50, id + " 너무 짧음");
            Assert.LessOrEqual(SfxSynth.PeakDb(b), -1f, id + " 소리가 너무 큼(찢어짐)");
            Assert.Greater(SfxSynth.PeakDb(b), -40f, id + " 소리가 거의 안 남");
        }
    }

    [Test]
    public void 효과음_같은_id는_항상_같은_소리()
    {
        var a = SfxSynth.Render("sfx.hit.chain"); var b = SfxSynth.Render("sfx.hit.chain");
        CollectionAssert.AreEqual(a, b);
    }

    // ---------- 구역(Zone) 바둑판 ----------
    [Test]
    public void 구역_마을은_0번_구역_안에_들어가고_구역은_틈과_겹침이_없다()
    {
        var v = World.Get(0, 0);
        Assert.IsTrue(v.Village);
        Assert.GreaterOrEqual(MapLayout.VillageMinX, v.MinX); Assert.LessOrEqual(MapLayout.VillageMaxX, v.MaxX);
        Assert.GreaterOrEqual(MapLayout.VillageMinZ, v.MinZ); Assert.LessOrEqual(MapLayout.VillageMaxZ, v.MaxZ);
        // 이웃 구역은 변이 정확히 맞닿는다
        Assert.AreEqual(World.Get(0, 0).MaxX, World.Get(1, 0).MinX, 1e-3f);
        Assert.AreEqual(World.Get(0, 0).MaxZ, World.Get(0, 1).MinZ, 1e-3f);
        Assert.AreEqual(World.ZoneSize, v.MaxX - v.MinX, 1e-3f);
    }

    [Test]
    public void 구역_소품은_자기_구역_안에만_있고_길_위가_아니다()
    {
        foreach (var z in World.Zones)
        {
            Assert.AreEqual(z.Props.Count, z.Blockers.Count, z.Id);
            foreach (var p in z.Props)
            {
                Assert.IsTrue(z.Contains(p.X, p.Z), z.Id + " 소품이 구역 밖");
                Assert.IsTrue(World.At(p.X, p.Z) == z);
            }
        }
        // 같은 구역은 항상 같은 모양(재현 가능)
        Assert.AreEqual(World.Get(1, 1).Props[0].X, World.Get(1, 1).Props[0].X);
    }

    [Test]
    public void 구역_켜짐은_둘레_3x3이고_경계에서_깜빡이지_않는다()
    {
        var st = new ZoneStreamer(); var load = new System.Collections.Generic.List<ZoneDef>(); var drop = new System.Collections.Generic.List<ZoneDef>();
        st.Update(0f, 0f, load, drop);   // 마을 한가운데
        Assert.AreEqual(World.Get(0, 0), st.Current);
        Assert.AreEqual(4, st.ActiveCount, "마을은 모서리 구역이라 이웃 3개와 합쳐 4개만 켜진다");
        // 경계 x = Get(1,0).MinX 부근을 오가도 현재 구역이 바뀌지 않는다(히스테리시스)
        float edge = World.Get(1, 0).MinX; load.Clear(); drop.Clear();
        st.Update(edge + 1f, 10f, load, drop); st.Update(edge - 1f, 10f, load, drop); st.Update(edge + 2f, 10f, load, drop);
        Assert.AreEqual(World.Get(0, 0), st.Current, "경계를 막 넘은 것만으로는 바뀌지 않음");
        Assert.AreEqual(0, load.Count + drop.Count);
        // 충분히 넘어가면 바뀐다
        st.Update(edge + Balance.ZONE_HYSTERESIS_M + 2f, 10f, load, drop);
        Assert.AreEqual(World.Get(1, 0), st.Current);
    }

    [Test]
    public void 구역_켜면_경계가_넓어지고_꺼면_마을만()
    {
        float oldMax = MapLayout.MaxX;
        try
        {
            World.Enabled = true;
            Assert.AreEqual(World.MaxX, MapLayout.MaxX);
            Assert.Greater(MapLayout.MaxX, oldMax + 50f);
            // 다른 구역 소품도 막힌 곳이다
            var p = World.Get(1, 1).Blockers[0];
            MapLayout.ZoneBlockers.AddRange(World.Get(1, 1).Blockers);
            Assert.IsTrue(MapLayout.IsBlocked(p.X, p.Z, 0.3f));
            float x = p.X, z = p.Z; MapLayout.PushOut(ref x, ref z, 0.3f);
            Assert.IsFalse(MapLayout.IsBlocked(x, z, 0.3f - 0.01f));
        }
        finally { MapLayout.ZoneBlockers.Clear(); World.Enabled = false; }
        Assert.AreEqual(oldMax, MapLayout.MaxX, "꺼 두면 기존 마을 경계 그대로");
    }

    // ---------- 피하기 ----------
    [Test]
    public void 피하기_무적은_0_03초부터_0_25초까지만()
    {
        Assert.IsFalse(DodgeRules.Invulnerable(0f));
        Assert.IsTrue(DodgeRules.Invulnerable(0.1f));
        Assert.IsFalse(DodgeRules.Invulnerable(0.3f));
        Assert.Less(Balance.DODGE_IFRAME_END, Balance.DODGE_TIME, "무적이 피하기보다 길면 안 됨");
    }

    [Test]
    public void 후딜_60퍼센트_뒤에는_이동으로_끊을_수_있다()
    {
        Assert.IsFalse(DodgeRules.CanCancelRecoverToMove(0.5f));
        Assert.IsTrue(DodgeRules.CanCancelRecoverToMove(0.6f));
        Assert.Less(Balance.PAHON_RECOVER, Balance.DODGE_TIME + 0.2f, "파혼 끝동작이 너무 길면 안 됨");
    }

    // ---------- 5×5 필드 ----------
    [Test]
    public void 필드_청크_번호는_128m마다_바뀌고_가장자리로_붙는다()
    {
        Assert.AreEqual(0, FieldRules.ChunkIndex(0f));
        Assert.AreEqual(0, FieldRules.ChunkIndex(127.9f));
        Assert.AreEqual(1, FieldRules.ChunkIndex(128f));
        Assert.AreEqual(4, FieldRules.ChunkIndex(639f));
        Assert.AreEqual(4, FieldRules.ChunkIndex(900f), "필드 밖은 가장자리 청크");
        Assert.AreEqual(0, FieldRules.ChunkIndex(-5f));
    }

    [Test]
    public void 필드_충돌은_나무_바위_벽만_막고_덤불_길은_통과()
    {
        Assert.Greater(FieldRules.BlockerRadius("nature_pine_a"), 0f);
        Assert.Greater(FieldRules.BlockerRadius("terrain_rock_cluster"), FieldRules.BlockerRadius("terrain_rock_small"));
        Assert.Greater(FieldRules.BlockerRadius("hanok_wall_mud"), 0f);
        Assert.AreEqual(0f, FieldRules.BlockerRadius("hanok_door_single"), "문은 드나드는 곳");
        Assert.AreEqual(0f, FieldRules.BlockerRadius("nature_bush_a"));
        Assert.AreEqual(0f, FieldRules.BlockerRadius("terrain_tile_road_straight"));
        Assert.Greater(FieldRules.BlockerRadius("br_deep"), 4f, "깊은 물은 못 건넌다");
    }

    // ---------- 얻은 것 알림 ----------
    [Test]
    public void 알림은_같은_글을_합치고_2초_뒤_사라진다()
    {
        var t = new ToastStack();
        t.Add("넋 +1"); t.Add("넋 +1"); t.Add("엽전 +5");
        Assert.AreEqual(2, t.Items.Count);
        Assert.AreEqual("넋 +1 ×2", ToastStack.Line(t.Items[0]));
        t.Tick(1.5f); Assert.AreEqual(2, t.Items.Count);
        t.Tick(0.6f); Assert.AreEqual(0, t.Items.Count);
    }

    [Test]
    public void 알림은_최대_5줄이다()
    {
        var t = new ToastStack();
        for (int i = 0; i < 8; i++) t.Add("글" + i);
        Assert.AreEqual(ToastStack.MaxLines, t.Items.Count);
        Assert.AreEqual("글3", t.Items[0].Text);
    }

    [Test]
    public void 피하기_충전은_1_1초에_한_번_최대_2()
    {
        float c = 0f;
        c = DodgeRules.Recharge(c, Balance.DODGE_RECHARGE);
        Assert.AreEqual(1f, c, 1e-4f);
        c = DodgeRules.Recharge(c, 100f);
        Assert.AreEqual((float)Balance.DODGE_CHARGES, c, 1e-4f);
    }

    [Test]
    public void 피하기_3타_후딜_앞쪽은_못_피하고_1타는_바로_가능()
    {
        Assert.IsFalse(DodgeRules.RecoverAllowsDodge(true, 0.2f));
        Assert.IsTrue(DodgeRules.RecoverAllowsDodge(true, 0.6f));
        Assert.IsTrue(DodgeRules.RecoverAllowsDodge(false, 0f));
        Assert.IsFalse(DodgeRules.CanCancelToAction(0.1f));
        Assert.IsTrue(DodgeRules.CanCancelToAction(0.25f));
    }

    // ---------- HUD 값 묶음 ----------
    [Test]
    public void HUD_글자는_값에서_만들어지고_체력_비율은_0에서_1_사이()
    {
        var h = new HudState { Neok = 5, Memory = 2, Coin = 7, Karma = 12, Hp = 30, MaxHp = 100, Heal = 2, SecondsLeft = 300, Sent = 1, Quota = 3, Clues = 1, CluesNeeded = 3 };
        StringAssert.Contains("넋 5", h.LedgerLine());
        StringAssert.Contains("업 12 (1단계)", h.LedgerLine());
        StringAssert.Contains("체력 30 / 100", h.VitalLine());
        StringAssert.Contains("천도 1/3", h.NightLine());
        Assert.AreEqual(0.3f, h.HpRatio, 1e-4f);
        h.Hp = -5; Assert.AreEqual(0f, h.HpRatio);
        h.Hp = 999; Assert.AreEqual(1f, h.HpRatio);
        h.Hp = 10; Assert.IsTrue(h.HpLow);
        h.Warning = true; StringAssert.Contains("날이 밝는다", h.NightLine());
    }

    [Test]
    public void 퀘스트_줄은_천도_몫과_단서_수를_보여_주고_넘쳐도_분자는_멈춘다()
    {
        var q = HudState.QuestLinesFor(1, 3, 2, 3, false);
        CollectionAssert.AreEqual(new[] { "천도 1/3", "단서 2/3" }, q);
        q = HudState.QuestLinesFor(5, 3, 9, 3, true);   // 몫·단서가 넘쳐도 n/N 의 n 은 N 까지
        CollectionAssert.AreEqual(new[] { "천도 3/3 채움", "단서 3/3", "나루 영감 끝" }, q);
    }

    [Test]
    public void 파혼_반격은_기를_모으는_중이고_폭발_반경_안일_때만_끊는다()
    {
        Assert.IsTrue(CoreRules.PahonInterruptsCharge(true, 2.5f, Balance.PAHON_RADIUS, 0.5f));    // 반경 안 + 모으는 중 → 끊김
        Assert.IsTrue(CoreRules.PahonInterruptsCharge(true, 3.4f, Balance.PAHON_RADIUS, 0.5f));    // 몸 반경만큼 걸쳐도 끊김
        Assert.IsFalse(CoreRules.PahonInterruptsCharge(true, 3.6f, Balance.PAHON_RADIUS, 0.5f));   // 밖이면 못 끊음
        Assert.IsFalse(CoreRules.PahonInterruptsCharge(false, 1f, Balance.PAHON_RADIUS, 0.5f));    // 모으는 중이 아니면(이미 터짐/쉬는 중) 해당 없음
    }

    [Test]
    public void 처결_대상은_조이스틱을_안_밀면_가장_가까운_혼이다()
    {
        var xs = new[] { 2f, -1f }; var zs = new[] { 0f, 0.5f };
        Assert.AreEqual(1, CoreRules.PickKneelIndex(0f, 0f, 0f, 0f, xs, zs));         // 방향 없음 → 더 가까운 1번
        Assert.AreEqual(1, CoreRules.PickKneelIndex(0f, 0f, 0.1f, 0f, xs, zs));       // 데드존(KNEEL_AIM_MIN) 아래로 살짝 밀기 → 그대로 가장 가까운 혼
        Assert.AreEqual(-1, CoreRules.PickKneelIndex(0f, 0f, 1f, 0f, new float[0], new float[0]));   // 후보가 없으면 -1
    }

    [Test]
    public void 처결_대상은_조이스틱_방향_60도_안에서_가장_가까운_혼이다()
    {
        var xs = new[] { 2f, -1f, 2.5f }; var zs = new[] { 0f, 0.5f, 1.0f };
        Assert.AreEqual(0, CoreRules.PickKneelIndex(0f, 0f, 1f, 0f, xs, zs));          // 오른쪽으로 밀면 오른쪽 혼 중 가까운 0번(더 가까운 1번은 반대편)
        Assert.AreEqual(1, CoreRules.PickKneelIndex(0f, 0f, -1f, 0f, xs, zs));         // 왼쪽으로 밀면 1번
        Assert.AreEqual(1, CoreRules.PickKneelIndex(0f, 0f, 0f, 1f, new[] { 2f, -1f }, new[] { 0f, 0.5f }));   // 위로 밀었는데 60도 안에 혼이 없으면 가장 가까운 혼으로(대상이 사라지지 않는다)
    }

    [Test]
    public void 보스_등장_카메라_세기는_처음과_끝에서_0이고_가운데서_1이다()
    {
        Assert.AreEqual(0f, CoreRules.RevealWeight(0f, 2f), 1e-5f);
        Assert.AreEqual(0f, CoreRules.RevealWeight(2f, 2f), 1e-5f);
        Assert.AreEqual(1f, CoreRules.RevealWeight(1f, 2f), 1e-5f);
        Assert.Greater(CoreRules.RevealWeight(0.25f, 2f), 0f);
        Assert.Less(CoreRules.RevealWeight(0.25f, 2f), 1f);                            // 앞 25%는 오르는 중
        Assert.AreEqual(CoreRules.RevealWeight(0.3f, 2f), CoreRules.RevealWeight(1.7f, 2f), 1e-5f);   // 올라갈 때와 내려올 때가 대칭
    }

    [Test]
    public void 맺힘_줄_수는_66퍼와_33퍼에서_한_줄씩_줄어든다()
    {
        Assert.AreEqual(3, CoreRules.LinesLeft(900, 900, 3));   // 가득
        Assert.AreEqual(3, CoreRules.LinesLeft(601, 900, 3));   // 아직 첫 줄 안 깨짐
        Assert.AreEqual(2, CoreRules.LinesLeft(600, 900, 3));   // 첫 줄 깨짐
        Assert.AreEqual(2, CoreRules.LinesLeft(301, 900, 3));
        Assert.AreEqual(1, CoreRules.LinesLeft(300, 900, 3));   // 둘째 줄 깨짐
        Assert.AreEqual(1, CoreRules.LinesLeft(1, 900, 3));     // 1 이라도 남으면 마지막 줄
        Assert.AreEqual(0, CoreRules.LinesLeft(0, 900, 3));     // 끝(무릎)
        Assert.AreEqual(1, CoreRules.LinesLeft(50, 100, 1));    // 한 줄짜리는 늘 1
    }

    [Test]
    public void 보스는_줄이_깨질_때마다_알리고_마지막_줄은_무릎으로만_센다()
    {
        var b = Soul.MakeBoss(1);                       // 맺힘 800, 3줄
        Assert.AreEqual(3, b.LinesLeft);
        Assert.IsFalse(b.TakeHit(100));                 // 700: 아직 첫 줄(>533)
        Assert.AreEqual(0, b.TakeLineBreaks());
        Assert.IsFalse(b.TakeHit(200));                 // 500: 첫 줄 깨짐
        Assert.AreEqual(2, b.LinesLeft);
        Assert.AreEqual(1, b.TakeLineBreaks());
        Assert.AreEqual(0, b.TakeLineBreaks());         // 읽으면 비워진다
        Assert.IsFalse(b.TakeHit(450));                 // 50: 둘째 줄 깨짐(마지막 줄만 남음)
        Assert.AreEqual(1, b.LinesLeft);
        Assert.AreEqual(1, b.TakeLineBreaks());
        Assert.IsTrue(b.TakeHit(50));                   // 0: 무릎. 줄 깨짐으로는 세지 않는다
        Assert.AreEqual(0, b.TakeLineBreaks());
        Assert.AreEqual(Balance.BOSS_S1_MAEDHIM, b.MaedhimMax);   // 총 맺힘은 그대로 — 줄은 마디일 뿐
    }

    [Test]
    public void 보스가_아닌_혼은_한_줄이라_줄_깨짐이_없다()
    {
        var s = new Soul(SoulKind.Fresh);
        Assert.AreEqual(1, s.LinesLeft);
        s.TakeHit(s.MaedhimMax - 1);
        Assert.AreEqual(0, s.TakeLineBreaks());
    }

    [Test]
    public void 첫_타격_시계는_조작할_수_있는_시간만_세고_한_번만_기록한다()
    {
        var t = new FirstHitTimer();
        t.Tick(5f, false);                              // 컷신 중: 안 센다
        t.Tick(12f, true);
        Assert.AreEqual(12f, t.Elapsed, 1e-5f);
        Assert.IsFalse(t.Hit);
        Assert.IsTrue(t.OnHit());
        Assert.AreEqual(12f, t.HitAt, 1e-5f);
        t.Tick(20f, true);                              // 기록 뒤엔 멈춘다
        Assert.IsFalse(t.OnHit());                      // 두 번째 타격은 기록하지 않는다
        Assert.AreEqual(12f, t.HitAt, 1e-5f);
        Assert.IsTrue(t.WithinGoal(Balance.FIRST_HIT_GOAL_SEC));
        var late = new FirstHitTimer(); late.Tick(31f, true); late.OnHit();
        Assert.IsFalse(late.WithinGoal(Balance.FIRST_HIT_GOAL_SEC));   // 31초는 초과
        Assert.IsFalse(new FirstHitTimer().WithinGoal(30f));           // 아직 못 쳤으면 통과 아님
    }

    // ---------- 화면 가장자리 경고 (2단계) ----------
    [Test]
    public void EdgeWarn_InsideView_NoMark()
    {
        float ex, ey;
        Assert.IsFalse(EdgeWarn.Compute(960 + 100, 540 + 50, 1920, 1080, 40, 0f, out ex, out ey));   // 화면 안, 시야 원 없음
    }

    [Test]
    public void EdgeWarn_OffScreen_MarkOnEdge()
    {
        float ex, ey;
        Assert.IsTrue(EdgeWarn.Compute(3000, 540, 1920, 1080, 40, 0f, out ex, out ey));            // 오른쪽 화면 밖
        Assert.AreEqual(1920 - 40, ex, 0.01f);                                                      // 오른쪽 안쪽 경계
        Assert.AreEqual(540, ey, 0.01f);
    }

    [Test]
    public void EdgeWarn_InsideScreenButOutsideVision_Marks()
    {
        float ex, ey;
        float r = EdgeWarn.VisionRadius(2203f, 0.6f, 1f);                                           // 캐스팅 중 좁아진 시야
        Assert.Greater(r, 0f);
        Assert.IsTrue(EdgeWarn.Compute(960 + 850, 540, 1920, 1080, 40, r, out ex, out ey));        // 화면 안이지만 시야 밖
        Assert.AreEqual(960 + (r - 40), ex, 0.5f);                                                  // 시야 원 가장자리에 붙음
        Assert.IsFalse(EdgeWarn.Compute(960 + 100, 540, 1920, 1080, 40, r, out ex, out ey));       // 시야 안은 표시 없음
    }

    [Test]
    public void EdgeWarn_VisionRadius_ZeroWhenNotCasting()
    {
        Assert.AreEqual(0f, EdgeWarn.VisionRadius(2203f, 0.6f, 0f));
        Assert.Less(EdgeWarn.VisionRadius(2203f, 0.6f, 1f), EdgeWarn.VisionRadius(2203f, 0.6f, 0.01f) + 1f);
    }

    // ---------- 속임수 혼 (2단계) ----------
    static Soul KneelingTrick()
    {
        var so = new Soul(SoulKind.Fresh) { Trick = true };
        so.TakeHit(so.MaedhimMax);   // 맺힘을 모두 깎아 무릎 꿇림
        return so;
    }

    [Test]
    public void Trick_FarAway_NeverSprings()
    {
        var so = KneelingTrick();
        for (int i = 0; i < 100; i++) Assert.IsFalse(so.TickTrick(0.1f, Balance.TRICK_TRIGGER_DIST + 1f));
        Assert.AreEqual(SoulState.Kneel, so.State);
    }

    [Test]
    public void Trick_Near_SpringsAfterFuse()
    {
        var so = KneelingTrick();
        float t = 0f; bool sprang = false;
        while (t < Balance.TRICK_FUSE + 0.5f && !sprang) { sprang = so.TickTrick(0.05f, 1f); t += 0.05f; }
        Assert.IsTrue(sprang);
        Assert.AreEqual(SoulState.Active, so.State);
        Assert.Greater(so.Maedhim, 0);
        Assert.IsFalse(so.Trick);   // 한 번만 속인다
    }

    [Test]
    public void Trick_PahonBeforeFuse_IsSafe()
    {
        var so = KneelingTrick();
        so.TickTrick(Balance.TRICK_FUSE * 0.5f, 1f);   // 도화선이 절반만 탐
        Assert.IsTrue(so.TryPahon());                   // 파혼은 즉시라 걸리지 않는다
        Assert.AreEqual(SoulState.Gone, so.State);
    }

    [Test]
    public void Trick_FuseCoolsWhenPlayerLeaves()
    {
        var so = KneelingTrick();
        so.TickTrick(Balance.TRICK_FUSE * 0.6f, 1f);
        so.TickTrick(10f, Balance.TRICK_TRIGGER_DIST + 5f);
        Assert.AreEqual(0f, so.Fuse, 1e-5f);
    }

    [Test]
    public void Trick_SpringsEvenWhileSending()
    {
        var so = KneelingTrick();
        Assert.IsTrue(so.BeginSending());
        bool sprang = false;
        for (int i = 0; i < 40 && !sprang; i++) sprang = so.TickTrick(0.05f, 1f);
        Assert.IsTrue(sprang);   // 천도하다 걸림 → 캐스팅은 끊기고 혼은 일어선다
        Assert.AreEqual(SoulState.Active, so.State);
    }

    [Test]
    public void AttackClock_ForceWindup_StartsImmediately()
    {
        var a = new AttackClock();
        a.ForceWindup();
        Assert.IsTrue(a.Winding);
    }

    // ---------- 필드 적 군집 ----------
    [Test]
    public void Camp_SpawnsOnlyWhenNearAndReady()
    {
        Assert.IsTrue(CampRules.ShouldSpawn(false, CampRules.ActivateDist - 1f, 0f));
        Assert.IsFalse(CampRules.ShouldSpawn(false, CampRules.ActivateDist + 1f, 0f));   // 멀면 안 선다
        Assert.IsFalse(CampRules.ShouldSpawn(false, 10f, 5f));                           // 재등장 대기 중
        Assert.IsFalse(CampRules.ShouldSpawn(true, 10f, 0f));                            // 이미 서 있음
    }

    [Test]
    public void Camp_ReleaseHasHysteresis()
    {
        Assert.Greater(CampRules.ReleaseDist, CampRules.ActivateDist);                   // 경계에서 깜박이지 않게 끄는 거리가 더 크다
        Assert.IsFalse(CampRules.ShouldRelease(true, CampRules.ActivateDist + 10f));
        Assert.IsTrue(CampRules.ShouldRelease(true, CampRules.ReleaseDist + 1f));
        Assert.IsFalse(CampRules.ShouldRelease(false, 999f));
    }

    // ---------- 흐르는 하루 (3단계) ----------
    [Test]
    public void Clock_DayIsFortyMinutes()
    {
        Assert.AreEqual(40f, WorldClock.DayLength, 1e-4f);
    }

    [Test]
    public void Clock_PhasesInOrder()
    {
        Assert.AreEqual(ClockPhase.Dawn, WorldClock.PhaseAt(0.5f));
        Assert.AreEqual(ClockPhase.Day, WorldClock.PhaseAt(Balance.CLOCK_DAWN_MIN + 1f));
        Assert.AreEqual(ClockPhase.Dusk, WorldClock.PhaseAt(Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + 0.5f));
        Assert.AreEqual(ClockPhase.Night, WorldClock.PhaseAt(30f));
    }

    [Test]
    public void Clock_DaylightRisesAtDawnAndFallsAtDusk()
    {
        Assert.AreEqual(0f, WorldClock.DaylightAt(30f), 1e-4f);                          // 한밤
        Assert.AreEqual(1f, WorldClock.DaylightAt(10f), 1e-4f);                          // 한낮
        Assert.Greater(WorldClock.DaylightAt(1.5f), WorldClock.DaylightAt(0.5f));        // 동틀녘엔 올라감
        Assert.Greater(WorldClock.DaylightAt(16.5f), WorldClock.DaylightAt(17.5f));      // 해질녘엔 내려감
    }

    [Test]
    public void Clock_FullDayWrapsAndCountsDays()
    {
        var c = new WorldClock(0f);
        c.Tick(WorldClock.DayLength * 60f + 1f);
        Assert.AreEqual(1, c.Day);
        Assert.Less(c.Minutes, 1f);
    }

    [Test]
    public void Clock_ReportsPhaseChangeOnce()
    {
        var c = new WorldClock(Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN - 0.01f);
        c.Tick(0.01f * 60f - 0.0001f); Assert.IsNull(c.Consume());                       // 아직 낮
        c.Tick(1f);
        Assert.AreEqual(ClockPhase.Dusk, c.Consume());                                       // 해질녘 종
        Assert.IsNull(c.Consume());                                                        // 한 번만
    }

    [Test]
    public void Clock_MoonCycleIsSevenDays()
    {
        var c = new WorldClock();
        Assert.IsTrue(c.NewMoon);
        c.Day = (int)Balance.MOON_DAYS / 2; Assert.IsTrue(c.FullMoon);
        c.Day = (int)Balance.MOON_DAYS; Assert.IsTrue(c.NewMoon);                          // 한 바퀴 돌면 다시 그믐
    }

    [Test]
    public void Clock_TenTimesSpeedRunsADayInFourMinutes()
    {
        var c = new WorldClock(0f) { Speed = 10f };
        for (int i = 0; i < 240 * 20; i++) c.Tick(0.05f);                                  // 실제 240초 = 4분
        Assert.AreEqual(1, c.Day);
    }

    [Test]
    public void Camp_FewerEnemiesByDay()
    {
        Assert.AreEqual(8, CampRules.CountFor(8, 0f));                                     // 밤엔 그대로
        Assert.Less(CampRules.CountFor(8, 1f), 8);                                         // 한낮엔 줄어든다
        Assert.GreaterOrEqual(CampRules.CountFor(1, 1f), 1);                               // 최소 1명
    }

    [Test]
    public void Moon_FullStrongerAndNewMoreLumps()
    {
        MoonEffects.Set(true, false);
        var strong = new Soul(SoulKind.Fresh);
        MoonEffects.Set(false, false);
        var normal = new Soul(SoulKind.Fresh);
        Assert.Greater(strong.MaedhimMax, normal.MaedhimMax);                              // 보름은 혼이 질기다
        MoonEffects.Set(false, true);
        Assert.Greater(MoonEffects.LumpBonus, 0f);                                         // 그믐은 덩어리 가산
        MoonEffects.Set(false, false);                                                     // 다른 시험에 영향 없게 되돌림
        Assert.AreEqual(1f, MoonEffects.MaedhimMult);
    }

    // ---------- 넋길 (4단계) ----------
    [Test]
    public void SoulPath_NightOnly_AndNextWraps()
    {
        Assert.IsTrue(SoulPath.Available(0f));
        Assert.IsFalse(SoulPath.Available(1f));                     // 낮엔 못 탄다
        Assert.AreEqual(1, SoulPath.Next(0, 3));
        Assert.AreEqual(0, SoulPath.Next(2, 3));                    // 끝이면 처음으로
    }

    [Test]
    public void SoulPath_NearIndexPicksClosestWithinRadius()
    {
        var sh = new[] { new[] { 0f, 0f }, new[] { 100f, 0f } };
        Assert.AreEqual(0, SoulPath.NearIndex(2f, 1f, sh));
        Assert.AreEqual(1, SoulPath.NearIndex(98f, 0f, sh));
        Assert.AreEqual(-1, SoulPath.NearIndex(50f, 0f, sh));       // 어느 서낭당 곁도 아님
    }

    // ---------- 엿듣기·단서 (5단계) ----------
    [Test]
    public void Eavesdrop_KarmaClosesEars()
    {
        Assert.AreEqual(EavesMode.Full, Eavesdrop.Mode(9, true, true));
        Assert.AreEqual(EavesMode.Half, Eavesdrop.Mode(10, true, false));
        Assert.AreEqual(EavesMode.Half, Eavesdrop.Mode(29, true, true));
        Assert.AreEqual(EavesMode.Closed, Eavesdrop.Mode(30, true, true));    // 보스 엿듣기 닫힘
        Assert.AreEqual(EavesMode.Half, Eavesdrop.Mode(30, true, false));     // 일반 소문은 아직 반쪽
        Assert.AreEqual(EavesMode.Closed, Eavesdrop.Mode(60, true, false));   // 소문까지 닫힘
    }

    [Test]
    public void Eavesdrop_WatchingAndTouchingIgnoreKarma()
    {
        Assert.AreEqual(EavesMode.Full, Eavesdrop.Mode(99, false, true));
    }

    [Test]
    public void ClueBook_CountsPerBossAndNoDuplicates()
    {
        var b = new ClueBook();
        Assert.IsTrue(b.Add("B01-D1"));
        Assert.IsFalse(b.Add("B01-D1"));
        b.Add("B01-D2"); b.Add("B02-D1");
        Assert.AreEqual(2, b.Count("B01-"));
        Assert.AreEqual(1, b.Count("B02-"));
    }

    // ---------- 컷신 재생기 (7단계) ----------
    static CutData TestCut()
    {
        return new CutData
        {
            id = "T", duration = 3f, skippable = true, @lock = true,
            steps = new[]
            {
                new CutStep { t = 0f, cam = "pan", camTo = "boss", camTime = 1f, zoom = 1.2f },
                new CutStep { t = 1f, text = "배 떠나오.", style = "bubble", lineDur = 1f },
                new CutStep { t = 2.9f, cam = "return" },
            }
        };
    }

    [Test]
    public void Cutscene_StepsApplyInOrderAndEnd()
    {
        var p = new CutPlayback(TestCut());
        Assert.AreEqual("boss", p.CamTarget); Assert.AreEqual(1.2f, p.CamZoom, 1e-4f);   // t=0 단계는 시작하자마자
        Assert.IsFalse(p.LineVisible);
        p.Tick(1.1f);
        Assert.IsTrue(p.LineVisible); Assert.AreEqual("배 떠나오.", p.LineText);
        p.Tick(1.0f);
        Assert.IsFalse(p.LineVisible);                                                    // 대사 시간이 지나면 사라짐
        p.Tick(1.0f);
        Assert.IsTrue(p.Done); Assert.AreEqual("player", p.CamTarget);                    // 끝: 플레이어로 복귀
    }

    [Test]
    public void Cutscene_SkipAlwaysReturnsToPlayer()
    {
        var p = new CutPlayback(TestCut());
        p.Tick(0.5f);
        p.Skip();
        Assert.IsTrue(p.Done); Assert.AreEqual("player", p.CamTarget); Assert.AreEqual(1f, p.CamZoom, 1e-4f);
        Assert.IsFalse(p.LineVisible);
    }

    [Test]
    public void Cutscene_ShakeRequestedOnce()
    {
        var c = new CutData { id = "S", duration = 1f, steps = new[] { new CutStep { t = 0.2f, cam = "shake", shake = 1f } } };
        var p = new CutPlayback(c);
        p.Tick(0.3f); Assert.AreEqual(1f, p.ShakeRequest, 1e-4f);
        p.ShakeRequest = 0f; p.Tick(0.3f); Assert.AreEqual(0f, p.ShakeRequest);
    }

    // ---------- 안내 문구 틀 (8단계) ----------
    [Test]
    public void Hints_ShowOnlyOnce_AndTouchDiffers()
    {
        var h = new TutorialHints();
        var key = h.On(HintEvent.FirstKneel, false);
        Assert.IsNotNull(key);
        Assert.IsNull(h.On(HintEvent.FirstKneel, false));                      // 두 번째는 없음
        var t2 = new TutorialHints().On(HintEvent.FirstKneel, true);
        Assert.AreNotEqual(key, t2);                                           // 폰은 버튼 이름으로
    }

    [Test]
    public void Hints_EliteChargeTeachesPahonInterrupt_OnceOnly()
    {
        var h = new TutorialHints();
        var pc = h.On(HintEvent.FirstEliteCharge, false);
        StringAssert.Contains("파혼", pc);                                      // 파혼 반격을 알려 준다
        Assert.IsNull(h.On(HintEvent.FirstEliteCharge, false));                // 한 번만
        StringAssert.DoesNotContain("R", new TutorialHints().On(HintEvent.FirstEliteCharge, true));   // 폰 문구에는 키보드 글자가 없다
    }

    [Test]
    public void Hints_DisabledShowsNothing()
    {
        var h = new TutorialHints { Enabled = false };
        Assert.IsNull(h.On(HintEvent.FirstMove, false));
    }

    // ---------- 구역 판정 ----------
    [Test]
    public void Zones_FirstMatchWinsAndOutsideIsMinusOne()
    {
        var z = new[] { new ZoneRect { X0 = 0, Z0 = 0, X1 = 10, Z1 = 10 }, new ZoneRect { X0 = 5, Z0 = 5, X1 = 20, Z1 = 20 } };
        Assert.AreEqual(0, ZoneRules.Find(z, 7, 7));      // 겹치면 앞의 구역
        Assert.AreEqual(1, ZoneRules.Find(z, 15, 15));
        Assert.AreEqual(-1, ZoneRules.Find(z, 50, 50));
    }

    // ---------- 이름혼 인(seal) ----------
    [Test]
    public void Soul_FadedSealLengthensWait()
    {
        var clear = Soul.Named("A", SoulKind.Fresh, 1); clear.TakeHit(5);
        var faded = Soul.Named("B", SoulKind.Fresh, 1); faded.WaitBonus = 0.25f; faded.TakeHit(5);
        Assert.AreEqual(clear.WaitTotal + 0.25f, faded.WaitTotal, 1e-4f);
    }

    // ---------- 성장: 품계·능력치·도술 ----------
    [Test]
    public void Growth_RankCurveIncreasesAndCapsAt50()
    {
        Assert.AreEqual(1, GrowthState.RankFor(0));
        Assert.AreEqual(2, GrowthState.RankFor(GrowthState.NeokForRank(2)));
        Assert.AreEqual(1, GrowthState.RankFor(GrowthState.NeokForRank(2) - 1));
        Assert.AreEqual(50, GrowthState.RankFor(99999999));                            // 상한
        for (int r = 2; r <= 50; r++) Assert.Greater(GrowthState.NeokForRank(r), GrowthState.NeokForRank(r - 1));
        Assert.AreEqual(75, GrowthState.TallyForRank(2)); Assert.AreEqual(180 * 4, GrowthState.TallyForRank(3)); Assert.AreEqual(180 * 361, GrowthState.TallyForRank(20));   // 품계 2 만 75(첫 성장 보장), 3 부터 180×(품계−1)²
    }

    [Test]
    public void Growth_RankUpGivesSkillAndStatPoints()
    {
        var g = new GrowthState();
        Assert.AreEqual(0, g.AddNeok(99999)); Assert.AreEqual(1, g.Rank);                // 쌓인 넋(천도 재화)으로는 품계가 오르지 않는다
        int ups = g.AddJudge(GrowthState.TallyForRank(4));                              // 처결 셈으로 한 번에 3단계
        Assert.AreEqual(3, ups); Assert.AreEqual(4, g.Rank);
        Assert.AreEqual(3, g.SkillPointsFree); Assert.AreEqual(3 * GrowthState.StatPerRank, g.StatPointsFree);   // 품계 하나마다 도술 점수 1·능력치 7
        g.AddBossPoint(); Assert.AreEqual(4, g.SkillPointsFree);                       // 보스 천도 +1
    }

    [Test]
    public void Growth_StatsStartTenAndSpendPoints()
    {
        var g = new GrowthState();
        Assert.IsFalse(g.AddStat(0));                                                    // 점수 없이는 못 올림
        g.AddJudge(GrowthState.TallyForRank(2));
        Assert.IsTrue(g.AddStat(0)); Assert.AreEqual(11, g.Stats[0]); Assert.AreEqual(GrowthState.StatPerRank - 1, g.StatPointsFree);
    }

    [Test]
    public void Growth_DeepSkillNeedsTenInBranch()
    {
        var g = new GrowthState { SkillPointsEarned = 30 }; g.Learned.Clear(); g.ActiveBar.Clear();   // 시작 도술 셋을 비우고 규칙만 본다
        Assert.IsFalse(g.CanLearn("일곱 이름"));                                        // 부름 갈래 점수 0
        foreach (var n in new[] { "붙잡아 부르기", "혼불 날리기", "이름 비추기", "배웅길" }) Assert.IsTrue(g.Learn(n));   // 액티브 4 (점수 4)
        foreach (var n in new[] { "오래 부르기", "고마운 넋", "곁을 지킴" }) { Assert.IsTrue(g.Learn(n)); Assert.IsTrue(g.Learn(n)); }   // 패시브 3×2 (점수 6) → 합 10
        Assert.IsTrue(g.CanLearn("일곱 이름"));                                          // 10점 이상이라 열림
    }

    [Test]
    public void Growth_PassiveMaxTwoLevelsActiveOnce_AndBarHoldsFour()
    {
        var g = new GrowthState { SkillPointsEarned = 40 }; g.Learned.Clear(); g.ActiveBar.Clear();
        for (int i = 0; i < 5; i++) Assert.IsTrue(g.Learn("휘감기")); Assert.IsFalse(g.Learn("휘감기"));   // 액티브는 다섯 단계
        for (int i = 0; i < 3; i++) Assert.IsTrue(g.Learn("단단한 손")); Assert.IsFalse(g.Learn("단단한 손"));   // 패시브는 세 단계
        foreach (var n in new[] { "여럿 끌기", "매듭 걸음", "한 줄 꿰기", "터뜨리기" }) g.Learn(n);
        Assert.AreEqual(SkillTree.ActiveSlots, g.ActiveBar.Count);                       // 칸은 넷까지
    }

    // ---- BGM 층 고르기 (기획·사운드 bgm.json) ----
    [Test] public void Bgm_CombatEntersAt8mAndExitsAfter4s()
        {
            var d = new BgmDirector();
            d.Update(0.1f, 1f, 20f, false, false); Assert.AreEqual(BgmLayer.Explore, d.Layer);
            d.Update(0.1f, 1f, 7.9f, false, false); Assert.AreEqual(BgmLayer.Combat, d.Layer); Assert.AreEqual(1f, d.Fade);
            d.Update(3.9f, 1f, 30f, false, false); Assert.AreEqual(BgmLayer.Combat, d.Layer);   // 4초 전엔 그대로
            d.Update(0.2f, 1f, 30f, false, false); Assert.AreEqual(BgmLayer.Explore, d.Layer); Assert.AreEqual(3f, d.Fade);
        }
    [Test] public void Bgm_NightFlipUsesHysteresisAnd8sFade()
        {
            var d = new BgmDirector();
            d.Update(0.1f, 0.35f, 99f, false, false); Assert.IsFalse(d.Night);   // 문턱 사이: 바뀌지 않는다
            d.Update(0.1f, 0.2f, 99f, false, false); Assert.IsTrue(d.Night); Assert.AreEqual(8f, d.Fade);
            d.Update(0.1f, 0.35f, 99f, false, false); Assert.IsTrue(d.Night);
            d.Update(0.1f, 0.5f, 99f, false, false); Assert.IsFalse(d.Night);
        }
    [Test] public void Bgm_KneelPlaysOnceThenSilenceUntilDone()
        {
            var d = new BgmDirector();
            d.Update(0.1f, 1f, 3f, true, true); Assert.AreEqual(BgmLayer.Finish, d.Layer); Assert.AreEqual(0.3f, d.Fade);
            d.Update(3f, 1f, 3f, false, true); Assert.AreEqual(BgmLayer.Finish, d.Layer);
            d.Update(4f, 1f, 3f, false, true); Assert.AreEqual(BgmLayer.Silent, d.Layer);   // 곡 끝 → 무음
            d.Update(5f, 1f, 3f, false, true); Assert.AreEqual(BgmLayer.Silent, d.Layer);   // 아직 처결 중
            d.Update(0.1f, 1f, 3f, false, false); Assert.AreEqual(BgmLayer.Explore, d.Layer); Assert.AreEqual(2f, d.Fade);
        }

    // ---- 서사 control 칸: walk 구간은 잠금 컷이어도 걸을 수 있다 ----
    [Test] public void Cutscene_WalkStepUnlocksMovement()
    {
        var cp = new CutPlayback(new CutData { id = "F", duration = 30f, @lock = true, steps = new[] {
            new CutStep { t = 0f, ctl = "none" }, new CutStep { t = 14f, ctl = "walk" }, new CutStep { t = 52f, ctl = "none" } } });
        Assert.IsFalse(cp.Walk);
        cp.Tick(15f); Assert.IsTrue(cp.Walk);
        cp.Skip(); Assert.IsFalse(cp.Walk);   // 건너뛰면 잠금 상태로 정리된다(컷이 끝나며 조작은 어차피 돌아온다)
    }

    // ---- 성장이 전투 수치에 얹힌다 ----
    [Test] public void GrowthEffects_StatsAndPassivesAddToGear()
    {
        var g = new GrowthState { StatPointsEarned = 20, SkillPointsEarned = 10 };
        for (int i = 0; i < 10; i++) g.AddStat(0);                                       // 힘 +10
        for (int i = 0; i < 4; i++) g.AddStat(2);                                        // 몸 +4
        g.Learn("고마운 넋"); g.Learn("고마운 넋"); g.Learn("노잣돈");
        var s = new GearStats();
        GrowthEffects.Apply(g, s);
        Assert.AreEqual(0.10f, s.StatDamagePct, 0.0001f);                                // 힘 10점 × 1% (장비 상한 밖)
        Assert.AreEqual(16, s.HpFlat);                                                   // 몸 4점 × 4
        Assert.AreEqual(0.08f, s.TendoNeokPct, 0.0001f);                                 // 고마운 넋 2단계 = +8% (3단계 4/8/12)
        Assert.AreEqual(0.05f, s.PahonCoinPct, 0.0001f);                                 // 노잣돈 1단계 +5%
        GrowthEffects.Apply(null, s);                                                    // 성장이 없어도 안전
    }

    [Test] public void GearCheck_StrengthIsOutsideCapAndMinusesAreCapped()
    {
        var s = new GearStats { DamagePct = 0.9f, StatDamagePct = 0.4f };
        Assert.AreEqual(1.4f * 1.4f, s.DamageMult, 0.0001f);                              // 장비 상한 +40% 에 힘 +40% 가 따로 곱해진다
        var m = new GearStats { CastReducePct = -0.9f, DamagePct = -0.9f, CoinPct = -0.9f, PahonCoinPct = -0.9f };
        Assert.AreEqual(1.3f, m.CastMult, 0.0001f);                                       // 느려짐 +30% 까지
        Assert.AreEqual(0.8f, m.DamageMult, 0.0001f);                                     // 피해 −20% 까지
        Assert.AreEqual(0.5f, m.CoinMult, 0.0001f);
        Assert.AreEqual(0.5f, m.PahonCoinMult, 0.0001f);
        Assert.AreEqual(1.3f, new GearStats { TendoNeokPct = 2f }.TendoNeokMult, 0.0001f); // 천도 넋 합계 상한 +30%
        Assert.AreEqual(0.4f, new GearStats { DefensePct = 2f }.DefenseMult, 0.0001f);     // 방어 상한 60%
    }

    [Test] public void GearCheck_SameTiltCountsOnceAndBackWeaponIgnored()
    {
        var eq = new Equipment { FirstRingBossDone = true, Act2Entered = true };
        var a = new ItemDef { Slot = Slot.Charm, Rarity = Rarity.Rare, Gradient = true, TiltId = "tilt_dmg_cast" };
        a.Options.Add(new OptionRoll(Opt.DamagePct, 0.2f)); a.Options.Add(new OptionRoll(Opt.CastReducePct, -0.1f));
        var b = new ItemDef { Slot = Slot.Hat, Rarity = Rarity.Rare, Gradient = true, TiltId = "tilt_dmg_cast" };
        b.Options.Add(new OptionRoll(Opt.DamagePct, 0.2f)); b.Options.Add(new OptionRoll(Opt.CastReducePct, -0.1f));
        eq.PutAt(EquipPos.Charm1, a); eq.PutAt(EquipPos.Hat, b);
        var st = eq.Stats();
        Assert.AreEqual(0.2f, st.DamagePct, 0.0001f);                                      // 같은 기울기는 하나만
        var w = new ItemDef { Slot = Slot.Weapon, Rarity = Rarity.Common }; w.Options.Add(new OptionRoll(Opt.DamagePct, 0.05f));
        eq.PutAt(EquipPos.Weapon2, w);
        Assert.AreEqual(0.2f, eq.Stats().DamagePct, 0.0001f);                              // 등에 멘 무기는 안 센다
    }

    [Test] public void GearCheck_OptionsFollowSlotAndRarityRange()
    {
        var rng = new System.Random(3);
        for (int i = 0; i < 400; i++)
        {
            var it = Loot.Roll(() => (float)rng.NextDouble(), true, 0, new[] { Slot.Shoes });
            foreach (var o in it.Options.GetRange(2, it.Options.Count - 2))                 // 앞 두 줄은 기울기
            {
                CollectionAssert.Contains(Loot.PoolFor(Slot.Shoes), o.Kind);                   // 신은 생명·이동만
                if (o.Kind == Opt.MoveSpeedPct) Assert.That(o.Value, Is.InRange(0.044f, 0.064f)); // 귀한 이동 +4.5~6.3%(기획 B: 피해 줄과 같은 비율로 줄임)
            }
        }
    }

    [Test] public void RingMultipliers_MatchSimTable()
    {
        Assert.AreEqual(1.2f, RingLoot.MaedhimMult(2), 0.0001f); Assert.AreEqual(1.15f, RingLoot.DamageMult(2), 0.0001f); Assert.AreEqual(1.25f, RingLoot.RewardMult(2), 0.0001f);
        Assert.AreEqual(1.15f, RingLoot.CoinMult(2), 0.0001f);   // 엽전은 증가분 0.25 의 60% = +0.15
        Assert.AreEqual(1f, RingLoot.MaedhimMult(1), 0.0001f); Assert.AreEqual(2.3f, RingLoot.RewardMult(6), 0.0001f);
    }

    // ---- 보스 목록·바닥 무늬 ----
    [Test] public void Bosses_TableAndTwelveStreetsNeverOpensSafeCup()
    {
        Assert.AreEqual("월화", Bosses.Get(2).Name); Assert.AreEqual("B03", Bosses.Get(3).Cut); Assert.AreEqual("나루 영감", Bosses.Get(1).Name);
        var rng = new System.Random(7);
        for (int t = 0; t < 500; t++)
        {
            var cups = TwelveStreets.Pick(() => (float)rng.NextDouble(), 5);
            Assert.AreEqual(5, cups.Count); Assert.IsFalse(cups.Contains(TwelveStreets.SafeCup));
            Assert.AreEqual(5, new System.Collections.Generic.HashSet<int>(cups).Count);   // 겹치지 않는다
        }
        Assert.AreEqual(Balance.B02_CUPS_PER_WAVE_P2, TwelveStreets.CupsPerWave(0.4f));
        Assert.AreEqual(Balance.B02_CUPS_PER_WAVE, TwelveStreets.CupsPerWave(0.9f));
    }
    [Test] public void NumberGridAndWeakWindow()
    {
        var rng = new System.Random(3);
        var g = NumberGrid.Pick(() => (float)rng.NextDouble(), 25, Balance.B03_CELLS_PER_WAVE);
        int bad = 0; foreach (var b in g) if (b) bad++;
        Assert.AreEqual(Balance.B03_CELLS_PER_WAVE, bad);
        var w = new WeakWindow();
        w.WaveResolved(false); w.WaveResolved(false); w.WaveResolved(true); Assert.AreEqual(0, w.Streak);   // 맞으면 끊김
        for (int i = 0; i < Balance.B03_WEAK_STREAK; i++) w.WaveResolved(false);
        Assert.IsTrue(w.Open); Assert.AreEqual(Balance.B03_WEAK_DMG_MULT, w.DamageMult);
        w.Tick(Balance.B03_WEAK_TIME + 0.1f); Assert.IsFalse(w.Open); Assert.AreEqual(Balance.B03_CLOSED_DMG_MULT, w.DamageMult);
    }

    [Test] public void CupWeak_OpensForThreeSecondsMaxThreeTimesWithCooldown()
    {
        var w = new CupWeak();
        Assert.IsTrue(w.CanGrab); Assert.AreEqual(1f, w.DamageMult);          // 처음엔 잡을 수 있고 피해는 평소
        Assert.IsTrue(w.Grab()); Assert.IsTrue(w.Open); Assert.AreEqual(Balance.B02_WEAK_DMG_MULT, w.DamageMult);
        Assert.IsFalse(w.Grab());                                              // 열려 있는 동안 또 잡아도 소용없다
        w.Tick(Balance.B02_WEAK_TIME + 0.01f); Assert.IsFalse(w.Open); Assert.AreEqual(1f, w.DamageMult);
        Assert.IsFalse(w.CanGrab);                                             // 닫힌 직후엔 식는 중
        w.Tick(Balance.B02_WEAK_COOLDOWN + 0.01f); Assert.IsTrue(w.CanGrab);
        for (int i = 1; i < Balance.B02_WEAK_MAX; i++) { Assert.IsTrue(w.Grab()); w.Tick(Balance.B02_WEAK_TIME + 0.01f); w.Tick(Balance.B02_WEAK_COOLDOWN + 0.01f); }
        Assert.AreEqual(Balance.B02_WEAK_MAX, w.Uses);
        Assert.IsFalse(w.CanGrab); Assert.IsFalse(w.Grab());                   // 한 전투에 최대 횟수까지만
    }

    [Test] public void Growth_StartingKitAndBarToggleAndCooldowns()
    {
        var g = new GrowthState();
        CollectionAssert.AreEqual(new[] { "붙잡아 부르기", "휘감기", "터뜨리기" }, g.ActiveBar);   // 처음엔 옛 도술 셋이 끼워져 있다
        Assert.AreEqual(0, g.SkillPointsSpent);                                               // 점수는 쓰지 않았다
        g.SkillPointsEarned = 1; Assert.IsTrue(g.Learn("혼불 날리기")); Assert.AreEqual(4, g.ActiveBar.Count);
        g.SkillPointsEarned = 2; g.Learn("이름 비추기"); Assert.AreEqual(4, g.ActiveBar.Count);   // 칸이 차 있으면 올라가지 않는다
        Assert.IsFalse(g.ToggleBar("이름 비추기"));                                           // 칸이 가득
        Assert.IsTrue(g.ToggleBar("휘감기")); Assert.IsTrue(g.ToggleBar("이름 비추기"));      // 내리고 올리기
        Assert.IsFalse(g.ToggleBar("오래 부르기"));                                           // 패시브는 칸에 안 올린다
        var cd = new ActiveCooldowns();
        Assert.IsTrue(cd.Start("혼불 날리기")); Assert.IsFalse(cd.Ready("혼불 날리기"));
        cd.Tick(Balance.ACD_SOULFIRE + 0.1f); Assert.IsTrue(cd.Ready("혼불 날리기"));
    }

    [Test]
    public void Enhance_CostsAndRaisesMainOption()
    {
        var it = new ItemDef { Slot = Slot.Weapon, Rarity = Rarity.Common, Name = "시험" };
        it.Options.Add(new OptionRoll(Opt.DamagePct, 0.10f));
        // 값은 Balance 에서 읽는다(1막 균형 10-31: 비용을 8배로 올렸다. 숫자를 박아 두면 조정할 때마다 시험이 깨진다)
        int total = Balance.ENHANCE_COST_1 + Balance.ENHANCE_COST_2 + Balance.ENHANCE_COST_3 + Balance.ENHANCE_COST_4 + Balance.ENHANCE_COST_5;
        var l = new Ledger { Coin = total + 100 };
        float before = GearStatsOf(it).DamagePct;
        int spent = 0;
        for (int i = 0; i < 5; i++) { Assert.IsTrue(Shrine.Enhance(it, l)); }
        spent = total + 100 - l.Coin;
        Assert.AreEqual(total, spent, "한 칸 5단계 = 다섯 단계 비용의 합");
        Assert.IsFalse(Shrine.Enhance(it, l), "최대 +5");
        Assert.AreEqual(before * (1f + Balance.ENHANCE_PCT * 5), GearStatsOf(it).DamagePct, 0.0001f, "주옵션 단계마다 +ENHANCE_PCT");
        Assert.AreEqual(0, l.Neok, "넋은 건드리지 않는다");
    }

    static GearStats GearStatsOf(ItemDef it) { var st = new GearStats(); st.Add(it); return st; }

    [Test]
    public void JudgeTally_PahonAndTendoEarnSkillPointsAtSameThresholds()
    {
        var g = new GrowthState(); var h = new GrowthState();
        for (int i = 0; i < 100; i++) { g.AddJudge(50); h.AddJudge(50); }               // 파혼만·천도만 같은 양을 셈에 더하면 같은 점수
        Assert.AreEqual(g.SkillPointsEarned, h.SkillPointsEarned);
        Assert.Greater(g.SkillPointsEarned, 0);
        for (int i = 0; i < 1000; i++) Assert.IsFalse(g.AddPahon());                      // 파혼 15번마다 얼룩 점수는 사라졌다
        Assert.AreEqual(0, g.StainPointsFree);
    }

    [Test]
    public void Save_RoundTrip_KeepsGrowthLedgerGearAndClues()
    {
        var g = new GrowthState(); var l = new Ledger { Neok = 120, Memory = 7, Coin = 333, Ore = 4, Karma = 9, TendoTotal = 12, Hp = 77 };
        g.AddNeok(400); g.AddPahon(); g.Learn("휘감기");
        var eq = new Equipment(); var it = new ItemDef { Slot = Slot.Weapon, Rarity = Rarity.Rare, Name = "시험 사슬", Plus = 3, Sockets = 1, Rerolls = 2 };
        it.Options.Add(new OptionRoll(Opt.DamagePct, 0.0625f)); it.Options.Add(new OptionRoll(Opt.HpFlat, 11f)); eq.Put(Slot.Weapon, it);
        var cb = new ClueBook(); cb.Add("B01-D1"); cb.Add("B02-D3");
        var snap = SaveGame.Capture(g, l, eq, cb); snap.X = 12.5f; snap.Z = -3.25f; snap.ClockDay = 4; snap.ClockMinutes = 123.5f; snap.BossOutcome = 2;
        var back = SaveGame.Deserialize(SaveGame.Serialize(snap));
        Assert.NotNull(back);
        Assert.AreEqual(12.5f, back.X); Assert.AreEqual(-3.25f, back.Z); Assert.AreEqual(4, back.ClockDay); Assert.AreEqual(123.5f, back.ClockMinutes); Assert.AreEqual(2, back.BossOutcome);
        var g2 = new GrowthState(); var l2 = new Ledger(); var eq2 = new Equipment(); var cb2 = new ClueBook();
        SaveGame.Apply(back, g2, l2, eq2, cb2);
        Assert.AreEqual(g.Rank, g2.Rank); Assert.AreEqual(g.TotalNeok, g2.TotalNeok); Assert.AreEqual(1, g2.LevelOf("휘감기"));
        Assert.AreEqual(g.PahonCount, g2.PahonCount); Assert.AreEqual(g.SkillPointsFree, g2.SkillPointsFree);
        Assert.AreEqual(333, l2.Coin); Assert.AreEqual(9, l2.Karma); Assert.AreEqual(12, l2.TendoTotal);
        var it2 = eq2.Get(Slot.Weapon);
        Assert.AreEqual("시험 사슬", it2.Name); Assert.AreEqual(3, it2.Plus); Assert.AreEqual(2, it2.Options.Count); Assert.AreEqual(0.0625f, it2.Options[0].Value);
        Assert.IsTrue(cb2.Has("B01-D1") && cb2.Has("B02-D3"));
    }

    [Test]
    public void Save_BadOrNewerText_ReturnsNull_NotCrash()
    {
        Assert.IsNull(SaveGame.Deserialize(null)); Assert.IsNull(SaveGame.Deserialize("쓰레기")); Assert.IsNull(SaveGame.Deserialize("v=99\nx=1\nz=1\nmin=1\n"));
        Assert.IsNull(SaveGame.Deserialize("v=1\nx=abc\nz=1\nmin=1\n"));
    }

    [Test]
    public void Settings_ParseClampsAndFallsBack()
    {
        var s = GameSettings.Parse("5,-1,0.5,9"); Assert.AreEqual(1f, s.Master); Assert.AreEqual(0f, s.Bgm); Assert.AreEqual(0.5f, s.Sfx); Assert.AreEqual(1.5f, s.Shake);
        var d = GameSettings.Parse("깨짐"); Assert.AreEqual(1f, d.Master); Assert.AreEqual(1f, d.Shake);
        var r = GameSettings.Parse(new GameSettings { Master = 0.3f, Bgm = 0.4f, Sfx = 0.5f, Shake = 0.6f }.Serialize()); Assert.AreEqual(0.6f, r.Shake, 0.0001f);
    }

    [Test]
    public void WorldClock_Set_MovesPhaseWithoutAlert()
    {
        var c = new WorldClock(); c.Set(3, WorldClock.DayLength - 1f);
        Assert.AreEqual(3, c.Day); Assert.AreEqual(ClockPhase.Night, c.Phase); Assert.IsNull(c.Changed);
    }

    [Test]
    public void Height_BilinearAndEdgeClamp()
    {
        // 2x2 지도(한 변 10m): 네 모서리 높이 0, 2, 4, 6
        var h = new HeightField(2, 2, 10f, new float[] { 0f, 2f, 4f, 6f });
        Assert.AreEqual(0f, h.At(0, 0), 1e-4f); Assert.AreEqual(2f, h.At(10, 0), 1e-4f); Assert.AreEqual(6f, h.At(10, 10), 1e-4f);
        Assert.AreEqual(3f, h.At(5, 5), 1e-4f, "가운데는 네 모서리 평균");
        Assert.AreEqual(6f, h.At(99, 99), 1e-4f, "지도 밖은 가장자리 값");
        Assert.AreEqual(0f, h.At(-5, -5), 1e-4f);
        Assert.Greater(h.Slope(5, 5), 0.1f);
    }

    [Test]
    public void Height_FromRG_DecodesSixteenBit()
    {
        var h = HeightField.FromRG(2, 2, 10f, new byte[] { 0, 255, 128, 0 }, new byte[] { 0, 255, 0, 0 }, 0f, 10f);
        Assert.AreEqual(0f, h.At(0, 0), 1e-4f); Assert.AreEqual(10f, h.At(10, 0), 1e-4f);
        Assert.AreEqual(128f * 256f / 65535f * 10f, h.At(0, 10), 1e-3f);
    }

    [Test]
    public void Splat_WeightsSumToOne_EmptyIsGrass()
    {
        var layers = new float[SplatField.Layers][];
        for (int l = 0; l < layers.Length; l++) layers[l] = new float[4];
        layers[(int)GroundLayer.Dirt] = new float[] { 1f, 1f, 0f, 0f };   // 위쪽 줄만 흙
        var s = new SplatField(2, 2, 10f, layers); var o = new float[SplatField.Layers];
        s.Weights(0, 0, o); Assert.AreEqual(1f, o[(int)GroundLayer.Dirt], 1e-4f);
        s.Weights(5, 5, o); Assert.AreEqual(1f, o[(int)GroundLayer.Dirt], 1e-4f, "위쪽만 칠해졌어도 합을 1로 맞춘다");
        s.Weights(5, 10, o); Assert.AreEqual(1f, o[(int)GroundLayer.Grass], 1e-4f, "아무 층도 안 칠한 자리는 풀 100%");
    }

    [Test]
    public void Weather_WeightsAndRoll()
    {
        var day = WeatherRules.Weights("검은여울", false); Assert.AreEqual(0f, day[4], "낮엔 역병 안개가 없다"); Assert.AreEqual(30f, day[0], "낮엔 맑음 ×2");
        Assert.AreEqual(35f, WeatherRules.Weights("검은여울", true)[4]); Assert.AreEqual(5f, WeatherRules.Weights("검은여울", true, true)[4], "3호 처결 뒤 35→5");
        Assert.AreEqual(Weather.Clear, WeatherRules.Roll("솔고개", true, 0.0f)); Assert.AreEqual(Weather.Fog, WeatherRules.Roll("솔고개", true, 0.99f));
        Assert.AreEqual(Weather.Rain, WeatherRules.Roll("물막이 골", true, 0.5f), "물막이 골: 25/20/40/15 중 0.5(=50/100)는 비 구간(45~85)");
        Assert.AreEqual(Weather.Rain, WeatherRules.BossFixed(1).Value); Assert.AreEqual(Weather.Plague, WeatherRules.BossFixed(3).Value); Assert.IsNull(WeatherRules.BossFixed(0));
    }

    [Test]
    public void Weather_EffectsOnlyAtNight_AndSlowCap()
    {
        Assert.AreEqual(1f, WeatherRules.Effect(Weather.Cloudy, false).GhostMult, "낮엔 효과 없음");
        Assert.AreEqual(Balance.WEATHER_CLOUDY_GHOST_MULT, WeatherRules.Effect(Weather.Cloudy, true).GhostMult);
        var fog = WeatherRules.Effect(Weather.Fog, true); Assert.AreEqual(Balance.WEATHER_FOG_VISION_M, fog.VisionM); Assert.Greater(fog.CastHit, Balance.WEATHER_CLEAR_CAST_HIT);
        Assert.IsTrue(WeatherRules.Effect(Weather.Rain, true).HideKarma);
        Assert.AreEqual(Balance.WEATHER_MOVE_SLOW_MAX, WeatherRules.CombineSlow(0.2f, 0.2f), 1e-5f, "겹쳐도 최대 -30%");
    }

    [Test]
    public void WeatherState_RollsPerZone_OverrideWins()
    {
        var ws = new WeatherState(); var rng = new System.Random(3);
        ws.RollAll(false, rng);
        Assert.AreNotEqual(Weather.Plague, ws.For("검은여울"), "낮엔 역병 안개 없음");
        ws.RollAll(true, rng); var snap = ws.Snapshot(); Assert.AreEqual(5, snap.Length);
        ws.Override = Weather.Rain; Assert.AreEqual(Weather.Rain, ws.For("폐당집"), "서사 지정이 우선"); ws.Override = null;
        ws.MidNight(rng); Assert.AreEqual(0, ws.MidNight(rng), "밤 중간은 밤마다 한 번만");
        Assert.AreEqual("역병 안개", WeatherState.Name(Weather.Plague));
    }

    [Test]
    public void HeightField_CloseWaterGaps_FillsThinRimOnly()
    {
        // 한 줄 높이: 물(-0.1) 물 둑(0.4) 물 | 땅(1.0) 물 | 강둑 한쪽만 물(-0.1) 평지(0.3) 평지(0.3) 평지(0.3)
        var h = new float[] { -0.1f, 0.4f, -0.1f, 1.0f, -0.1f, 0.3f, 0.3f, 0.3f, 0.3f };
        var f = new HeightField(9, 2, 8f, new float[18]);
        var row = new float[18]; for (int i = 0; i < 9; i++) { row[i] = h[i]; row[9 + i] = 5f; }   // 둘째 줄은 높은 벽(세로 판정이 틈을 만들지 않게)
        f = new HeightField(9, 2, 8f, row);
        int n = f.CloseWaterGaps(0.18f, 0.8f, 3, -0.1f);
        Assert.AreEqual(1, n, "둑(0.4) 하나만 낮춘다");
        Assert.AreEqual(-0.1f, f.At(1f, 0f), 1e-3f); Assert.AreEqual(1.0f, f.At(3f, 0f), 1e-3f, "rimMax 넘는 땅은 그대로"); Assert.AreEqual(0.3f, f.At(5f, 0f), 1e-3f, "한쪽만 물이면 강둑");
    }

    [Test]
    public void Save_PickedHerbs_RoundTrip()
    {
        var snap = new SaveSnapshot { Herbs = 4 };
        snap.Picked.Add("C-01"); snap.Picked.Add("K-001"); snap.HerbTaken.Add("H-02:3");
        var back = SaveGame.Deserialize(SaveGame.Serialize(snap));
        CollectionAssert.AreEqual(new[] { "C-01", "K-001" }, back.Picked); CollectionAssert.AreEqual(new[] { "H-02:3" }, back.HerbTaken); Assert.AreEqual(4, back.Herbs);
        var old = SaveGame.Deserialize(SaveGame.Serialize(new SaveSnapshot()));
        Assert.AreEqual(0, old.Picked.Count); Assert.AreEqual(0, old.Herbs);
    }

    [Test]
    public void Weather_SaveRoundTrip_AndParse()
    {
        var snap = new SaveSnapshot { WeatherNow = new[] { 0, 2, 3, 4, 1 }, PlagueEased = true };
        var back = SaveGame.Deserialize(SaveGame.Serialize(snap));
        CollectionAssert.AreEqual(new[] { 0, 2, 3, 4, 1 }, back.WeatherNow); Assert.IsTrue(back.PlagueEased);
        Assert.IsNull(SaveGame.Deserialize(SaveGame.Serialize(new SaveSnapshot())).WeatherNow, "옛 저장·날씨 없음은 null");
        Assert.AreEqual(Weather.Fog, WeatherRules.Parse("FOG").Value); Assert.IsNull(WeatherRules.Parse("auto"));
    }

    [Test]
    public void MoonPhase_FollowsCycle()
    {
        var c = new WorldClock(0f);
        var seen = new System.Collections.Generic.List<int>();
        for (int d = 0; d < (int)Balance.MOON_DAYS; d++) { c.Set(d, 0f); seen.Add(c.MoonPhase); }
        Assert.AreEqual(0, seen[0], "그믐=초승 모양"); Assert.AreEqual(2, seen[(int)Balance.MOON_DAYS / 2], "가운데 날 보름");
        Assert.IsTrue(seen.Contains(1) && seen.Contains(3), "상현·하현이 모두 나온다");
    }

    [Test]
    public void CampRules_Adjust_PushesFromShrineAndThinsBossYard()
    {
        var sh = new float[] { 100f, 100f }; var boss = new float[] { 500f, 500f };
        float x = 130f, z = 100f; int n = 6;   // 서낭당에서 30m → 밀려나 60m 밖
        Assert.IsTrue(CampRules.Adjust(ref x, ref z, 8f, ref n, sh, boss));
        Assert.GreaterOrEqual(new UnityEngineFreeVec(x - 100f, z - 100f).Len, CampRules.ShrineSafeM);
        Assert.AreEqual(6, n);
        x = 505f; z = 500f; n = 9;             // 보스 마당 한가운데 → 제거
        Assert.IsFalse(CampRules.Adjust(ref x, ref z, 8f, ref n, sh, boss));
        x = 525f; z = 500f; n = 9;             // 25m, 반지름 8 → 가장자리 띠: 절반
        Assert.IsTrue(CampRules.Adjust(ref x, ref z, 8f, ref n, sh, boss));
        Assert.AreEqual(4, n);
    }
    [Test]
    public void SoulTypes_PickByZone_FollowsRatios()
    {
        Assert.AreEqual(SoulType.Plain, SoulTypeRules.Pick(null, 0.1f));
        Assert.AreEqual(SoulType.Mote, SoulTypeRules.Pick("솔고개 마을", 0.10f));      // 35% 잔넋
        Assert.AreEqual(SoulType.Wail, SoulTypeRules.Pick("솔고개 마을", 0.40f));      // 35~50% 넋두리
        Assert.AreEqual(SoulType.Plain, SoulTypeRules.Pick("솔고개 마을", 0.80f));     // 묻힌 혼 0%, 나머지 보통
        Assert.AreEqual(SoulType.Wail, SoulTypeRules.Pick("검은여울", 0.15f));          // 잔넋 10% → 넋두리 10~35%
        Assert.AreEqual(SoulType.Buried, SoulTypeRules.Pick("검은여울", 0.50f));        // 묻힌 혼 35~70%
        Assert.AreEqual(SoulType.Mote, SoulTypeRules.Pick("검은여울", 0.05f));
        Assert.AreEqual(SoulType.Plain, SoulTypeRules.Pick("검은여울", 0.95f));
        Assert.AreEqual(SoulType.Plain, SoulTypeRules.Pick("알 수 없는 곳", 0.01f));
    }

    [Test]
    public void SoulTypes_Stats_ScaleByTypeAndGrade()
    {
        Assert.AreEqual((int)System.Math.Round(Balance.MAEDHIM_NORMAL * Balance.SOULTYPE_MOTE_HP), SoulTypeRules.Maedhim(SoulType.Mote, SoulKind.Fresh, Balance.MAEDHIM_NORMAL));
        Assert.AreEqual(System.Math.Round(Balance.SOULTYPE_WAIL_DAMAGE * Balance.SOULGRADE_LUMP_DAMAGE), SoulTypeRules.Damage(SoulType.Wail, SoulKind.Lump));
        Assert.Less(SoulTypeRules.Speed(SoulType.Plain, SoulKind.Old), 1f, "묵은 혼은 느리다");
        Assert.Greater(SoulTypeRules.Speed(SoulType.Mote, SoulKind.Fresh), 1f, "잔넋은 빠르다");
        Assert.IsFalse(SoulTypeRules.Reachable(SoulType.Buried, BuriedPhase.Hidden));
        Assert.IsFalse(SoulTypeRules.Reachable(SoulType.Buried, BuriedPhase.Windup), "예고 중엔 아직 못 때린다(회피 창)");
        Assert.IsTrue(SoulTypeRules.Reachable(SoulType.Buried, BuriedPhase.Up));
        Assert.IsTrue(SoulTypeRules.Reachable(SoulType.Wail, BuriedPhase.Hidden), "다른 유형은 늘 닿는다");
    }

    [Test]
    public void WailAi_KeepsDistanceAndThrowsAfterWindup()
    {
        Assert.AreEqual(-1, WailAi.MoveDir(3f)); Assert.AreEqual(0, WailAi.MoveDir(8f)); Assert.AreEqual(1, WailAi.MoveDir(12f));
        var w = new WailAi(); bool fired = false; float t = 0f;
        while (t < 10f && !fired) { fired = w.Tick(0.05f, 8f, true); t += 0.05f; }
        Assert.IsTrue(fired, "시야 안이면 결국 던진다");
        Assert.AreEqual(Balance.SOULTYPE_WAIL_INTERVAL * 0.5f + Balance.SOULTYPE_WAIL_WINDUP, t, 0.15f);
        var far = new WailAi(); for (int i = 0; i < 400; i++) Assert.IsFalse(far.Tick(0.05f, Balance.SOULTYPE_WAIL_SIGHT_M + 5f, true), "시야 밖이면 던지지 않는다");
        var hit = new WailAi(); hit.Windup = 0.3f; hit.Interrupt(); Assert.IsFalse(hit.Winding, "맞으면 선딜이 끊긴다");
    }

    [Test]
    public void BuriedAi_AmbushCycle()
    {
        var b = new BuriedAi();
        Assert.IsFalse(b.Tick(0.1f, 20f)); Assert.AreEqual(BuriedPhase.Hidden, b.Phase, "멀면 숨어 있다");
        b.Tick(0.1f, 3f); Assert.AreEqual(BuriedPhase.Windup, b.Phase, "4.5m 안이면 예고");
        bool strike = false; float t = 0f;
        while (t < 3f && !strike) { strike = b.Tick(0.02f, 1f); t += 0.02f; }
        Assert.IsTrue(strike, "예고 → 솟음 → 붙잡기");
        Assert.AreEqual(Balance.SOULTYPE_BURIED_WINDUP + 0.4f, t, 0.1f);
        while (b.Phase != BuriedPhase.Hidden && t < 6f) { b.Tick(0.02f, 1f); t += 0.02f; }
        Assert.AreEqual(BuriedPhase.Hidden, b.Phase, "공격 뒤 묻힌다");
        for (int i = 0; i < 100; i++) b.Tick(0.02f, 1f); Assert.AreEqual(BuriedPhase.Hidden, b.Phase, "6초 지나기 전엔 재매복하지 않는다");
        bool again = false; for (int i = 0; i < 400; i++) { b.Tick(0.02f, 1f); if (b.Phase != BuriedPhase.Hidden) again = true; } Assert.IsTrue(again, "6초 뒤 다시 매복");
        Assert.IsTrue(BuriedAi.InStrike(1.5f)); Assert.IsFalse(BuriedAi.InStrike(3.5f));
    }

    [Test]
    public void GuideQueue_OneAtATime_ClosesOnAction_RemindsAfter20s()
    {
        var g = new GuideQueue();
        g.Define(new GuideStep { Id = "walk", Pc = "걷기" }); g.Define(new GuideStep { Id = "hit", Pc = "때리기" });
        g.Define(new GuideStep { Id = "map", Pc = "지도", Timed = true, Dur = 3f });
        g.Request("walk"); g.Request("hit"); g.Request("walk");
        g.Tick(0.1f); Assert.AreEqual("walk", g.Current.Id, "먼저 요청한 안내가 먼저 뜬다(한 번에 하나)");
        g.Tick(5f); Assert.AreEqual("walk", g.Current.Id, "시간이 지나도 행동하기 전엔 안 닫힌다");
        g.Tick(15.5f); Assert.IsTrue(g.Reminding, "20초 넘게 안 하면 다시 알린다");
        g.Complete("walk"); Assert.IsTrue(g.Checking, "행동하면 체크");
        g.Tick(0.5f); Assert.IsNull(g.Current, "체크 0.4초 뒤 닫힘");
        g.Tick(0.5f); Assert.IsNull(g.Current, "닫힌 뒤 1초가 지나야 다음 안내");
        g.Tick(0.6f); Assert.AreEqual("hit", g.Current.Id);
        g.Complete("hit"); g.Tick(0.5f); g.Tick(1.1f);
        g.Request("walk"); g.Tick(0.1f); Assert.IsNull(g.Current, "이미 한 행동은 다시 안 띄운다");
        g.Request("map"); g.Tick(0.1f); Assert.AreEqual("map", g.Current.Id);
        g.Tick(3.1f); Assert.IsNull(g.Current, "시간제 안내는 시간이 지나면 닫힌다");
    }

    [Test]
    public void GridPath_GoesAroundWall_AndNullWhenSealed()
    {
        // 20×20 열린 땅(폭 5m) 가운데에 세로 벽(x=10, z 0~17)을 세우면 위쪽 틈(z 18~19)으로 돌아가야 한다
        var c = new byte[400]; for (int i = 0; i < 400; i++) c[i] = 100;
        for (int z = 0; z < 18; z++) c[z * 20 + 10] = 0;
        var gp = new GridPath(c, 20, 20);
        var path = gp.Find(2, 2, 17, 2, 1f);
        Assert.IsNotNull(path); Assert.Greater(path.Count, 1, "벽을 돌아가려면 꺾는 점이 있어야 한다");
        float maxZ = 0; foreach (var p in path) maxZ = System.Math.Max(maxZ, p[1]);
        Assert.GreaterOrEqual(maxZ, 18f, "틈(z>=18)을 지나야 한다");
        Assert.AreEqual(17f, path[path.Count - 1][0], 0.01f);
        // 틈까지 막으면 길이 없다
        c[18 * 20 + 10] = 0; c[19 * 20 + 10] = 0;
        Assert.IsNull(new GridPath(c, 20, 20).Find(2, 2, 17, 2, 1f));
    }

    [Test]
    public void Dwell_FillsAfterNeed_GraceKeeps_LongAwayResets()
    {
        var t = new DwellTimer();
        Assert.IsFalse(t.Tick(3f, true, false, 6f));
        Assert.IsFalse(t.Tick(2f, false, false, 6f));          // 2초 나갔다 옴: 유지
        Assert.IsFalse(t.Tick(2f, true, false, 6f));           // 합 5초
        Assert.IsTrue(t.Tick(1.5f, true, false, 6f));          // 6.5 >= 6 완료
        Assert.AreEqual(0f, t.Progress);
        t.Tick(4f, true, false, 6f); t.Tick(3.5f, false, false, 6f);   // 3초 넘게 비움
        Assert.AreEqual(0f, t.Progress);
        t.Tick(5f, true, true, 6f);                            // 전투 중: 쌓지 않음
        Assert.AreEqual(0f, t.Progress);
    }

    [Test]
    public void HeardLog_DedupesSameLine()
    {
        var l = new HeardLog();
        Assert.IsTrue(l.Add("순임", "서낭당", "말", "B01-D3", 2));
        Assert.IsFalse(l.Add("순임", "서낭당", "말", "B01-D3", 2));
        Assert.AreEqual(1, l.Items.Count);
    }

    [Test]
    public void Interact_Pick_NearestThenKindOrder()
    {
        var l = new System.Collections.Generic.List<InteractCand>
        {
            new InteractCand { Kind = InteractKind.Rest, Dist = 1.0f },
            new InteractCand { Kind = InteractKind.SoulPath, Dist = 1.2f },
            new InteractCand { Kind = InteractKind.Pickup, Dist = 1.4f },
        };
        Assert.AreEqual(2, Interact.Pick(l), "0.5m 안 동률 → 줍기가 먼저");
        l[2] = new InteractCand { Kind = InteractKind.Pickup, Dist = 1.9f };
        Assert.AreEqual(1, Interact.Pick(l), "줍기가 0.5m 넘게 멀면 넋길(쉬기와 동률 → 넋길 우선)");
        l[0] = new InteractCand { Kind = InteractKind.Rest, Dist = 0.3f };
        Assert.AreEqual(0, Interact.Pick(l), "쉬기가 0.5m 넘게 가까우면 쉬기");
        Assert.AreEqual(-1, Interact.Pick(new System.Collections.Generic.List<InteractCand> { new InteractCand { Kind = InteractKind.Touch, Dist = 2f } }), "만져 보기는 1.5m 밖이면 없음");
    }


    // ---- 2막 보스 4종 상태머신 뼈대 ----
    static System.Collections.Generic.List<BossMove> RunBrain(Act2Brain b, float sec, float dt = 0.1f)
    {
        var l = new System.Collections.Generic.List<BossMove>();
        for (float t = 0f; t < sec; t += dt) { var m = b.Tick(dt); if (m.Act != BossAct.None) l.Add(m); }
        return l;
    }

    [Test]
    public void Act2Boss_B05_CallsNames_CapAndNumberShare()
    {
        var b = new Act2Brain(5, () => 0.5f);
        var l = RunBrain(b, 9f);
        Assert.IsTrue(l.Exists(m => m.Act == BossAct.CallNames && m.Count == 2), "8초마다 병사 2");
        b.Soldiers = 3;
        var l2 = RunBrain(b, 8.5f);
        Assert.IsTrue(l2.Exists(m => m.Act == BossAct.CallNames && m.Count == 1), "상한 4 → 남는 자리 1만");
        b.Soldiers = 4;
        Assert.IsFalse(RunBrain(b, 8.5f).Exists(m => m.Act == BossAct.CallNames), "자리가 없으면 안 부른다");
        RunBrain(b, 200f);
        Assert.AreEqual(70, b.NumberSharePct, "번호 비율 상한 70%");
        b.Stun = 0f; b.OnCalledSoulTendo(); Assert.AreEqual(2f, b.Stun, 1e-4f, "불린 병사 천도 → 2초 멈춤");
        Assert.AreEqual(BossAct.None, b.Tick(0.1f).Act);
    }

    [Test]
    public void Act2Boss_B05_FlagPlantOnceAtHalf()
    {
        var b = new Act2Brain(5, () => 0.5f);
        b.Maedhim = b.MaedhimMax * 0.4f;
        var l = RunBrain(b, 30f);
        Assert.AreEqual(1, l.FindAll(m => m.Act == BossAct.FlagPlant).Count, "50% 이하에서 깃발 꽂기 한 번");
        Assert.IsTrue(b.FlagPlanted); b.OnFlagPulled(); Assert.IsFalse(b.FlagPlanted);
    }

    [Test]
    public void Act2Boss_B06_FormationsCycle_FastDoubles()
    {
        var b = new Act2Brain(6, () => 0.5f);
        var l = RunBrain(b, 40f);
        Assert.AreEqual(BossAct.LineForm, l[0].Act); Assert.AreEqual(BossAct.CraneForm, l[1].Act); Assert.AreEqual(BossAct.CircleForm, l[2].Act);
        Assert.AreEqual(1.2f, l[0].Warn, 1e-4f);
        b.Maedhim = b.MaedhimMax * 0.4f;
        var f = RunBrain(b, 8f);
        Assert.GreaterOrEqual(f.Count, 2, "50% 뒤 대형 둘 연속"); Assert.IsTrue(f[0].Fast); Assert.AreEqual(0.9f, f[0].Warn, 1e-4f);
        Assert.AreEqual(1.5f, b.DamageMultAt(true), 1e-4f); Assert.AreEqual(1f, b.DamageMultAt(false), 1e-4f);
    }

    [Test]
    public void Act2Boss_B07_MinersStunPahonFrenzyArenaShrinks()
    {
        var b = new Act2Brain(7, () => 0.5f);
        for (int i = 0; i < 4; i++) b.OnMinerExit();
        Assert.AreEqual(0f, b.Stun, 1e-4f); b.OnMinerExit(); Assert.AreEqual(2.5f, b.Stun, 1e-4f, "다섯째 광부가 나가면 2.5초 멈춤");
        b.Maedhim = b.MaedhimMax * 0.5f; float before = b.Maedhim; float add = b.OnMinerPahon();
        Assert.AreEqual(before + add, b.Maedhim, 1e-3f); Assert.AreEqual(b.MaedhimMax * 0.1f, add, 1e-3f); Assert.AreEqual(10f, b.Frenzy, 1e-4f);
        b.Stun = 0f; b.Tick(0.1f); Assert.Less(b.ArenaRadius, 14f); Assert.GreaterOrEqual(b.ArenaRadius, 10f);
        b.Maedhim = b.MaedhimMax * 0.4f; b.Frenzy = 0f; b.Stun = 0f;
        var l = RunBrain(b, 20f);
        Assert.IsTrue(l.Exists(m => m.Act == BossAct.RockFall && m.Count == 5), "50% 뒤 낙석 5");
    }

    [Test]
    public void Act2Boss_B08_MinesPapersCrouch()
    {
        var b = new Act2Brain(8, () => 0.99f);
        var l = RunBrain(b, 20f);
        Assert.IsTrue(l.Exists(m => m.Act == BossAct.NumberMines && m.Count == 4 && m.Param == 4f));
        Assert.IsTrue(l.Exists(m => m.Act == BossAct.AbacusSweep));
        Assert.IsFalse(l.Exists(m => m.Act == BossAct.LedgerFlip), "장부 넘기기는 50% 뒤부터");
        Assert.AreEqual(3, b.PickNamePaper(), "종이 칸은 0~3 안");
        float hp = b.Maedhim; b.OnNamePaperStepped(); b.OnNamePaperStepped();
        Assert.AreEqual(0f, b.Stun, 1e-4f); b.OnNamePaperStepped(); Assert.AreEqual(3f, b.Stun, 1e-4f, "세 장째 3초 웅크림");
        Assert.Less(b.Maedhim, hp);
    }


    [Test]
    public void HeightField_RectOrigin_ReadsWorldCoords()
    {
        // 2막 땅: 768×640m, 남서 모서리 (0,640). 가로 3칸·세로 3칸짜리 작은 지도로 확인
        var m = new float[] { 0, 1, 2, 10, 11, 12, 20, 21, 22 };   // 행(z) 0이 남쪽
        var h = new HeightField(3, 3, 4f, 4f, 100f, 640f, m);
        Assert.AreEqual(0f, h.At(100f, 640f), 1e-4f);
        Assert.AreEqual(2f, h.At(104f, 640f), 1e-4f);
        Assert.AreEqual(20f, h.At(100f, 644f), 1e-4f);
        Assert.AreEqual(11f, h.At(102f, 642f), 1e-4f, "한가운데");
        Assert.IsTrue(h.Covers(102f, 642f)); Assert.IsFalse(h.Covers(99f, 642f)); Assert.IsFalse(h.Covers(102f, 600f));
    }

    [Test]
    public void FieldRules_Extend_ChunkGrid()
    {
        try
        {
            FieldRules.ResetRegions();
            Assert.AreEqual(5, FieldRules.ChunksX); Assert.AreEqual(5, FieldRules.ChunksZ);
            FieldRules.AddRegion(0f, 640f, 768f, 1280f);
            Assert.AreEqual(6, FieldRules.ChunksX); Assert.AreEqual(10, FieldRules.ChunksZ);
            Assert.AreEqual(9, FieldRules.ChunkZ(1279f)); Assert.AreEqual(5, FieldRules.ChunkX(767f)); Assert.AreEqual(9, FieldRules.ChunkZ(5000f));
            Assert.AreEqual(5, FieldRules.RawChunk(640f), "붙이지 않은 번호");
            Assert.IsTrue(FieldRules.Inside(700f, 1200f));
        }
        finally { FieldRules.ResetRegions(); }
    }

    [Test]
    public void Tide_Cycle_And_FiveDayTable()
    {
        // 0분 = 만조에서 썰물 시작, 25분 = 간조, 50분 = 다시 만조
        Assert.AreEqual(1f, Tide.Level(0f), 0.001f);
        Assert.AreEqual(0f, Tide.Level(25f), 0.001f);
        Assert.AreEqual(1f, Tide.Level(50f), 0.001f);
        Assert.IsTrue(Tide.IsEbb(24.9f)); Assert.IsFalse(Tide.IsEbb(25.1f));
        // 기획 act3_map.json 5일 표: 밤 썰물 분 7·17·20·10·0 (오차 0.5분), 썰물 밤은 2·3·4일차
        float[] want = { 7f, 17f, 20f, 10f, 0f };
        for (int d = 0; d < 5; d++) Assert.AreEqual(want[d], Tide.EbbMinutesInNight(d), 0.6f, "day " + (d + 1));
        Assert.IsFalse(Tide.IsEbbNight(0)); Assert.IsTrue(Tide.IsEbbNight(1)); Assert.IsTrue(Tide.IsEbbNight(3)); Assert.IsFalse(Tide.IsEbbNight(4));
        float dx, dz; Tide.SmokeDir(5, out dx, out dz); Assert.AreEqual(1f, dx); Assert.AreEqual(0f, dz);
    }

    [Test]
    public void Act2Gate_OpensDawnAfterBlackMoonNight()
    {
        Assert.AreEqual(int.MaxValue, Act2Gate.OpenDay(-1, false, -1));              // 아무 조건도 없으면 안 풀린다
        Assert.AreEqual(4, Act2Gate.OpenDay(3, false, -1));                           // 3일째 낮에 셋 처결 → 그 밤 흑월 → 4일째 새벽
        Assert.AreEqual(5, Act2Gate.OpenDay(3, true, -1));                            // 3일째 밤에 처결 → 다음 밤 → 5일째 새벽
        Assert.AreEqual(7, Act2Gate.OpenDay(-1, false, 1));                           // 처결 못 해도 들어간 1일째 + 5 = 6일째 밤 → 7일째 새벽
        Assert.AreEqual(4, Act2Gate.OpenDay(3, false, 1));                            // 둘 다면 더 빠른 쪽
        Assert.IsFalse(Act2Gate.IsOpen(3, 3, false, -1)); Assert.IsTrue(Act2Gate.IsOpen(4, 3, false, -1));
    }

    [Test]
    public void CutPlayback_AudioCommands_QueueAtBeat_AndClearOnSkip()
    {
        var d = new CutData { id = "T", duration = 5f, steps = new[] {
            new CutStep { t = 0f, audio = new[] { "music:duck::0.3:1" } },
            new CutStep { t = 2f, audio = new[] { "loop:amb.snow.wind:0.5" } } } };
        var p = new CutPlayback(d);
        Assert.AreEqual(1, p.AudioPending.Count); Assert.AreEqual("music:duck::0.3:1", p.AudioPending.Dequeue());
        p.Tick(2.5f); Assert.AreEqual("loop:amb.snow.wind:0.5", p.AudioPending.Dequeue());
        var q = new CutPlayback(d); q.Skip(); Assert.AreEqual(0, q.AudioPending.Count);   // 건너뛰면 소리 명령은 버린다
    }

    [Test]
    public void FieldRules_Regions_WalkClamp_AndPlayerGates()
    {
        bool a2 = FieldRules.Act2, a3 = FieldRules.Act3, o2 = FieldRules.Act2Open, o3 = FieldRules.Act3Open, on0 = FieldRules.On;
        try
        {
            FieldRules.On = true; FieldRules.ResetRegions();
            FieldRules.AddRegion(0f, 640f, 768f, 1280f);       // 2막(북)
            FieldRules.AddRegion(768f, 0f, 1280f, 1024f);      // ⑤ 갯마을(동)
            FieldRules.AddRegion(-640f, 0f, 0f, 640f);         // ⑥ 도성(서)
            FieldRules.Act2 = true; FieldRules.Act3 = true;
            Assert.AreEqual(-640f, FieldRules.MinX); Assert.AreEqual(1280f, FieldRules.WorldX); Assert.AreEqual(1280f, FieldRules.WorldZ);
            Assert.IsTrue(FieldRules.Walkable(100f, 900f)); Assert.IsTrue(FieldRules.Walkable(-300f, 300f)); Assert.IsTrue(FieldRules.Walkable(1000f, 500f));
            Assert.IsFalse(FieldRules.Walkable(700f, 300f));   // 1막 동쪽 바깥 빈 구석(x 640~768, z<640)
            Assert.AreEqual(FieldRules.Key(-5, 3), FieldRules.Key(-5, 3)); Assert.AreEqual(-5, FieldRules.KeyX(FieldRules.Key(-5, 3))); Assert.AreEqual(3, FieldRules.KeyZ(FieldRules.Key(-5, 3)));
            // 해안 띠 청크(cz=-1)도 키가 겹치지 않고 왕복된다
            Assert.AreEqual(-1, FieldRules.KeyZ(FieldRules.Key(2, -1))); Assert.AreEqual(2, FieldRules.KeyX(FieldRules.Key(2, -1)));
            Assert.AreNotEqual(FieldRules.Key(2, -1), FieldRules.Key(1, 4));
            Assert.IsTrue(FieldRules.ChunkHasLand(-5, 0)); Assert.IsFalse(FieldRules.ChunkHasLand(5, 2));   // (640~768, 256~384)는 빈 땅
            // 빈 구석으로 걸어 들어가면 가장 가까운 땅으로 당겨진다
            float x = 700f, z = 300f; FieldRules.ClampWalk(ref x, ref z, 0.5f); Assert.IsTrue(FieldRules.Walkable(x, z, 0.4f));
            // 금줄: 닫혀 있으면 주인공만 못 들어간다
            FieldRules.Act2Open = false; FieldRules.Act3Open = false;
            x = 100f; z = 700f; MapLayout.PlayerClamp(ref x, ref z, 0.5f); Assert.AreEqual(639.5f, z, 0.001f);
            x = -300f; z = 300f; MapLayout.PlayerClamp(ref x, ref z, 0.5f); Assert.AreEqual(-0f, x, 0.6f);
            FieldRules.Act2Open = true; FieldRules.Act3Open = true;
            x = 100f; z = 700f; MapLayout.PlayerClamp(ref x, ref z, 0.5f); Assert.AreEqual(700f, z, 0.001f);
            Assert.AreEqual(4, Act2Gate.OpenDay(3, false, -1));
            Assert.AreEqual(3, Act2Gate.HeukwolNight(3, false, -1));
        }
        finally { FieldRules.ResetRegions(); FieldRules.Act2 = a2; FieldRules.Act3 = a3; FieldRules.Act2Open = o2; FieldRules.Act3Open = o3; FieldRules.On = on0; }
    }

    // ---- 3막 보스(B-09~B-12) 행동 규칙 ----
    static System.Collections.Generic.List<BossMove> RunBrain3(Act3Brain b, float sec, float dt = 0.1f)
    {
        var l = new System.Collections.Generic.List<BossMove>();
        for (float t = 0f; t < sec; t += dt) { var m = b.Tick(dt); if (m.Act != BossAct.None) l.Add(m); }
        return l;
    }

    [Test]
    public void Act3Brain_B09_파도와_바다부르기_그리고_50퍼센트_옷던지기는_한번만()
    {
        var b = new Act3Brain(9, () => 0.5f);
        var early = RunBrain3(b, 20f);
        Assert.IsTrue(early.Exists(m => m.Act == BossAct.WaveRows && m.Count == Balance.B09_WAVE_ROWS));
        Assert.IsTrue(early.Exists(m => m.Act == BossAct.CallSea));
        Assert.IsFalse(early.Exists(m => m.Act == BossAct.ClothThrow));
        b.Maedhim = b.MaedhimMax * 0.5f;
        var late = RunBrain3(b, 0.2f);                       // 50% 가 되자마자 옷 던지기 장면이 나온다
        Assert.AreEqual(1, late.FindAll(m => m.Act == BossAct.ClothThrow).Count);
        float cut = b.OnClothCaught();                       // 창(2초)이 아직 열려 있으니 낚아채기 성공 → 맺힘이 준다
        Assert.AreEqual(b.MaedhimMax * Balance.B09_CLOTH_CUT_PCT / 100f, cut, 0.01f);
        Assert.AreEqual(0, RunBrain3(b, 20f).FindAll(m => m.Act == BossAct.ClothThrow).Count);   // 한 번뿐
    }

    [Test]
    public void Act3Brain_B09_창이_닫힌_뒤_낚아채기는_효과없다()
    {
        var b = new Act3Brain(9, () => 0.5f); b.Maedhim = b.MaedhimMax * 0.4f;
        RunBrain3(b, 10f);
        float before = b.Maedhim;
        Assert.AreEqual(0f, b.OnClothCaught()); Assert.AreEqual(before, b.Maedhim);
    }

    [Test]
    public void Act3Brain_B10_50퍼센트_뒤엔_줄끊기가_두줄이다()
    {
        var b = new Act3Brain(10, () => 0.5f);
        Assert.IsTrue(RunBrain3(b, 20f).Exists(m => m.Act == BossAct.RopeCut && m.Count == 1));
        b.Maedhim = b.MaedhimMax * 0.4f;
        var late = RunBrain3(b, 20f);
        Assert.IsTrue(late.Exists(m => m.Act == BossAct.RopeCross && m.Count == 2));
        Assert.IsFalse(late.Exists(m => m.Act == BossAct.RopeCut));
    }

    [Test]
    public void Act3Brain_B12_단계마다_다른_공격_마지막은_공격없음_횃불은_큰물에서만_한번()
    {
        var b = new Act3Brain(12, () => 0.5f);
        Assert.AreEqual(1, b.Stage12);
        var s1 = RunBrain3(b, 30f);
        Assert.IsTrue(s1.Exists(m => m.Act == BossAct.MirrorPull)); Assert.IsTrue(s1.Exists(m => m.Act == BossAct.HisPahon));
        Assert.IsFalse(b.OnTorchPulled());                  // 큰물 단계가 아니면 횃불은 효과 없다
        b.Maedhim = b.MaedhimMax * 0.6f; Assert.AreEqual(2, b.Stage12);
        var s2 = RunBrain3(b, 30f);
        Assert.IsTrue(s2.Exists(m => m.Act == BossAct.NameLines && m.Count == Balance.B12_LINES_ROWS));
        Assert.IsFalse(s2.Exists(m => m.Act == BossAct.HisPahon));
        b.Maedhim = b.MaedhimMax * 0.3f; Assert.AreEqual(3, b.Stage12);
        Assert.IsTrue(b.OnTorchPulled()); Assert.IsFalse(b.OnTorchPulled());   // 1회만
        Assert.AreEqual(Balance.B12_TORCH_STUN, b.Stun, 0.001f);
        RunBrain3(b, Balance.B12_TORCH_STUN + 0.5f);
        Assert.IsTrue(RunBrain3(b, 30f).Exists(m => m.Act == BossAct.Flood));
        b.Maedhim = b.MaedhimMax * 0.1f; Assert.AreEqual(4, b.Stage12);
        Assert.AreEqual(0, RunBrain3(b, 30f).Count);        // 사슬을 내려놓고 선다
    }

    [Test]
    public void Act3Brain_번호_범위_밖은_예외()
    {
        Assert.Throws<System.ArgumentException>(() => new Act3Brain(8, () => 0f));
        Assert.AreEqual(9, Bosses.Get(9).Id); Assert.AreEqual(12, Bosses.Get(12).Id);
    }

    // ---- 장비 7칸·고리 드롭·인 (Core/GearPlan.cs) ----
    [Test]
    public void EquipLayout_열리는_때와_인_홈()
    {
        Assert.IsTrue(EquipLayout.IsOpen(EquipPos.Weapon2, false, false)); Assert.IsTrue(EquipLayout.IsOpen(EquipPos.Robe, false, false)); Assert.IsTrue(EquipLayout.IsOpen(EquipPos.Charm1, false, false));
        Assert.IsFalse(EquipLayout.IsOpen(EquipPos.Hat, false, false)); Assert.IsFalse(EquipLayout.IsOpen(EquipPos.Belt, false, false));
        Assert.IsTrue(EquipLayout.IsOpen(EquipPos.Hat, true, false)); Assert.IsTrue(EquipLayout.IsOpen(EquipPos.Belt, true, false));
        Assert.IsFalse(EquipLayout.IsOpen(EquipPos.Shoes, true, false)); Assert.IsFalse(EquipLayout.IsOpen(EquipPos.Charm2, true, false));
        Assert.IsTrue(EquipLayout.IsOpen(EquipPos.Shoes, true, true)); Assert.IsTrue(EquipLayout.IsOpen(EquipPos.Charm2, false, true));
        Assert.AreEqual(0, EquipLayout.SealSlots(EquipPos.Robe, Rarity.Common, false));
        Assert.AreEqual(1, EquipLayout.SealSlots(EquipPos.Hat, Rarity.Crafted, false));
        Assert.AreEqual(2, EquipLayout.SealSlots(EquipPos.Weapon1, Rarity.Rare, false));
        Assert.AreEqual(2, EquipLayout.SealSlots(EquipPos.Weapon2, Rarity.Common, true));      // 이름 있는 물건은 귀한과 같다
        Assert.AreEqual(0, EquipLayout.SealSlots(EquipPos.Belt, Rarity.Rare, false));          // 띠·신·노리개는 홈 없음
        Assert.AreEqual(0, EquipLayout.SealSlots(EquipPos.Charm1, Rarity.Rare, true));
    }

    [Test]
    public void RingLoot_고리별_확률의_합은_1이고_고리가_오를수록_귀한_쪽이_넓다()
    {
        float prevRare = -1f;
        for (int ring = 1; ring <= 6; ring++)
        {
            float sum = RingLoot.Chance(ring, Rarity.Common) + RingLoot.Chance(ring, Rarity.Crafted) + RingLoot.Chance(ring, Rarity.Rare);
            Assert.AreEqual(1f, sum, 0.001f);
            Assert.Greater(RingLoot.Chance(ring, Rarity.Rare), prevRare); prevRare = RingLoot.Chance(ring, Rarity.Rare);
        }
        Assert.AreEqual(RingLoot.Chance(1, Rarity.Rare), RingLoot.Chance(0, Rarity.Rare), 0.0001f);   // 범위 밖은 가장자리로
        Assert.AreEqual(RingLoot.Chance(6, Rarity.Rare), RingLoot.Chance(9, Rarity.Rare), 0.0001f);
        Assert.AreEqual(Rarity.Rare, RingLoot.RarityAt(6, 0.2f));      // 고리 6 은 귀한 25%
        Assert.AreEqual(Rarity.Crafted, RingLoot.RarityAt(6, 0.3f));
        Assert.AreEqual(Rarity.Common, RingLoot.RarityAt(6, 0.9f));
        Assert.AreEqual(Rarity.Common, RingLoot.RarityAt(1, 0.5f));    // 고리 1 은 귀한 2%·손본 18%
    }

    [Test]
    public void RingLoot_위치로_고리를_정한다()
    {
        Assert.AreEqual(1, RingLoot.RingAt(200f, 100f, false)); Assert.AreEqual(2, RingLoot.RingAt(300f, 500f, true));
        Assert.AreEqual(3, RingLoot.RingAt(100f, 900f, false)); Assert.AreEqual(3, RingLoot.RingAt(600f, 1000f, false));   // 2막은 구역 단위라 군집·혼의 ring 을 쓴다(기획 act2-field-camps). 기본은 3
        Assert.AreEqual(5, RingLoot.RingAt(1000f, 400f, false)); Assert.AreEqual(6, RingLoot.RingAt(-300f, 300f, false));
    }

    [Test]
    public void Loot_고리를_주면_고리표를_쓰고_안_주면_시연판_확률을_쓴다()
    {
        int rare6 = 0, rare0 = 0, n = 4000; var rng = new System.Random(7);
        for (int i = 0; i < n; i++) { var it = Loot.Roll(() => (float)rng.NextDouble(), false, 6); if (it != null && it.Rarity == Rarity.Rare) rare6++; }
        rng = new System.Random(7);
        for (int i = 0; i < n; i++) { var it = Loot.Roll(() => (float)rng.NextDouble(), false, 0); if (it != null && it.Rarity == Rarity.Rare) rare0++; }
        Assert.Greater(rare6, rare0 * 2);                               // 고리 6(25%)이 시연판(8%)보다 훨씬 자주 귀한 것을 준다
        Assert.IsTrue(Loot.Roll(() => 0f, true, 3).Rarity == Rarity.Rare);   // 사나운 적은 어느 고리든 귀한 확정
        var seq = new[] { 0f, 0.5f, 0.1f, 0.2f, 0.3f, 0.4f, 0.5f, 0.6f };
        int k = 0; var a1 = Loot.Roll(() => seq[k++ % seq.Length], false);
        k = 0; var a2 = Loot.Roll(() => seq[k++ % seq.Length], false, 0);
        Assert.AreEqual(a1.Rarity, a2.Rarity); Assert.AreEqual(a1.Options.Count, a2.Options.Count);   // 기존 호출은 결과가 그대로
    }

    [Test]
    public void Seal_열다섯_종과_비용()
    {
        Assert.AreEqual(15, Seal.AllKinds(false).Count);
        var mono = new Seal(SoulColor.Red, SoulColor.Red, false); var pair = new Seal(SoulColor.Yellow, SoulColor.Blue, false);
        Assert.AreEqual(Balance.SEAL_SMALL_NEOK, mono.CostOf(SoulColor.Red)); Assert.AreEqual(0, mono.CostOf(SoulColor.Blue));
        Assert.AreEqual(Balance.SEAL_SMALL_NEOK / 2, pair.CostOf(SoulColor.Blue)); Assert.AreEqual(Balance.SEAL_SMALL_NEOK / 2, pair.CostOf(SoulColor.Yellow));
        Assert.AreEqual(new Seal(SoulColor.Blue, SoulColor.Yellow, false).Key, pair.Key);   // 순서가 달라도 같은 인
        Assert.AreEqual(Balance.SEAL_LARGE_NEOK / 2, new Seal(SoulColor.Black, SoulColor.White, true).CostOf(SoulColor.White));
    }

    [Test]
    public void SoulWallet_모자라면_만들지_못하고_아무것도_깎지_않는다()
    {
        var w = new SoulWallet(); w.Add(SoulColor.Blue, 150); w.Add(SoulColor.Yellow, 149);
        Assert.IsNull(w.Craft(SoulColor.Blue, SoulColor.Yellow, false));
        Assert.AreEqual(150, w.Get(SoulColor.Blue)); Assert.AreEqual(149, w.Get(SoulColor.Yellow));
        w.Add(SoulColor.Yellow, 1);
        var s = w.Craft(SoulColor.Yellow, SoulColor.Blue, false);
        Assert.IsNotNull(s); Assert.AreEqual(0, w.Get(SoulColor.Blue)); Assert.AreEqual(0, w.Get(SoulColor.Yellow));
        Assert.IsNull(w.Craft(SoulColor.Red, SoulColor.Red, true));   // 큰 인은 900
    }

    [Test]
    public void SealSet_홈_수를_넘겨_박지_못한다()
    {
        var set = new SealSet(EquipLayout.SealSlots(EquipPos.Hat, Rarity.Crafted, false));   // 손본 갓 = 홈 1
        var s = new Seal(SoulColor.Blue, SoulColor.Blue, false);
        Assert.IsTrue(set.Insert(s)); Assert.IsFalse(set.Insert(s));
        Assert.IsTrue(set.Remove(0)); Assert.IsTrue(set.Insert(s)); Assert.IsFalse(set.Insert(null));
        Assert.IsFalse(new SealSet(0).Insert(s));   // 흔한 등급은 홈이 없다
    }

    static ItemDef 시험물건(Slot k, Rarity r) { return new ItemDef { Slot = k, Rarity = r, Name = "시험" }; }

    [Test]
    public void Equipment_무기_노리개는_둘째_자리까지_채우고_갓은_해금_전엔_못_낀다()
    {
        var eq = new Equipment();
        Assert.IsTrue(eq.TryEquip(시험물건(Slot.Weapon, Rarity.Common))); Assert.IsTrue(eq.TryEquip(시험물건(Slot.Weapon, Rarity.Common)));
        Assert.IsNotNull(eq.GetAt(EquipPos.Weapon1)); Assert.IsNotNull(eq.GetAt(EquipPos.Weapon2));
        Assert.IsFalse(eq.TryEquip(시험물건(Slot.Hat, Rarity.Rare)), "1막 보스 전엔 갓 자리가 닫혀 있다");
        eq.FirstRingBossDone = true; Assert.IsTrue(eq.TryEquip(시험물건(Slot.Hat, Rarity.Common)));
        Assert.IsTrue(eq.TryEquip(시험물건(Slot.Charm, Rarity.Common))); Assert.IsFalse(eq.TryEquip(시험물건(Slot.Charm, Rarity.Common)), "노리개 둘째 자리는 2막 진입 뒤");
        eq.Act2Entered = true; Assert.IsTrue(eq.TryEquip(시험물건(Slot.Charm, Rarity.Common)));
        // 가득 찬 뒤에는 더 나은 것만 가장 못한 자리를 대신한다
        Assert.IsFalse(eq.TryEquip(시험물건(Slot.Weapon, Rarity.Common))); Assert.IsTrue(eq.TryEquip(시험물건(Slot.Weapon, Rarity.Rare)));
    }

    [Test]
    public void Equipment_DropKinds_열린_종류만()
    {
        var eq = new Equipment();
        Assert.AreEqual(3, eq.DropKinds().Length);
        eq.FirstRingBossDone = true; Assert.AreEqual(5, eq.DropKinds().Length);
        eq.Act2Entered = true; Assert.AreEqual(6, eq.DropKinds().Length);
    }

    [Test]
    public void GrowthReveal_도술_나무는_카드_다섯_번과_여섯째_점수_뒤에_열린다()
    {
        var g = new GrowthState();
        Assert.IsTrue(GrowthReveal.SkillTreeOpen(g, false, 0), "카드 방식이 아니면(시연판) 처음부터 열림");
        Assert.IsFalse(GrowthReveal.SkillTreeOpen(g, true, 0), "카드 방식: 처음엔 닫힘");
        g.SkillPointsEarned = DosulCards.Rounds;
        Assert.IsFalse(GrowthReveal.SkillTreeOpen(g, true, DosulCards.Rounds), "점수 다섯 개를 카드로 다 써도 아직 닫힘");
        g.SkillPointsEarned = DosulCards.Rounds + 1;
        Assert.IsFalse(GrowthReveal.SkillTreeOpen(g, true, DosulCards.Rounds - 1), "카드가 남아 있으면 여섯째 점수가 먼저 와도 닫힘");
        Assert.IsTrue(GrowthReveal.SkillTreeOpen(g, true, DosulCards.Rounds), "카드 끝 + 여섯째 점수 = 열림");
    }

    [Test]
    public void GrowthReveal_인_탭과_장비_자리_수()
    {
        Assert.IsFalse(GrowthReveal.SealsTabOpen(false, false, 0));
        Assert.IsTrue(GrowthReveal.SealsTabOpen(true, false, 0));
        Assert.IsTrue(GrowthReveal.SealsTabOpen(false, true, 0));
        Assert.IsTrue(GrowthReveal.SealsTabOpen(false, false, 1), "만들어 둔 인이 있으면(옛 저장) 보인다");
        Assert.AreEqual(4, GrowthReveal.OpenEquipCount(false, false));
        Assert.AreEqual(6, GrowthReveal.OpenEquipCount(true, false));
        Assert.AreEqual(8, GrowthReveal.OpenEquipCount(true, true));
        // 닫힌 자리마다 안내가 있고, 처음부터 열린 자리는 비어 있다
        foreach (EquipPos ep in System.Enum.GetValues(typeof(EquipPos)))
            Assert.AreEqual(!EquipLayout.IsOpen(ep, false, false), GrowthReveal.EquipUnlockHint(ep).Length > 0, ep.ToString());
    }

    [Test]
    public void SaveGame_장비_8자리_왕복과_옛_3칸_저장_옮겨담기()
    {
        var g = new GrowthState(); var l = new Ledger(); var eq = new Equipment(); var cb = new ClueBook();
        eq.FirstRingBossDone = true; eq.Act2Entered = true;
        eq.PutAt(EquipPos.Hat, 시험물건(Slot.Hat, Rarity.Rare)); eq.PutAt(EquipPos.Charm2, 시험물건(Slot.Charm, Rarity.Crafted));
        var back = SaveGame.Deserialize(SaveGame.Serialize(SaveGame.Capture(g, l, eq, cb)));
        var eq2 = new Equipment(); SaveGame.Apply(back, new GrowthState(), new Ledger(), eq2, new ClueBook());
        Assert.AreEqual(Rarity.Rare, eq2.GetAt(EquipPos.Hat).Rarity); Assert.AreEqual(Slot.Charm, eq2.GetAt(EquipPos.Charm2).Slot);
        Assert.IsTrue(eq2.FirstRingBossDone && eq2.Act2Entered);
        // 옛 저장: gear0(무기)·gear1(도포)·gear2(노리개) 만 있다
        var txt = "v=1\nx=1\nz=1\nmin=1\ngear0=1|옛 사슬|0|0||0|0|0|\ngear1=-\ngear2=2|옛 노리개|0|0||0|0|0|\n";
        var old = SaveGame.Deserialize(txt); Assert.IsNotNull(old);
        var eq3 = new Equipment(); SaveGame.Apply(old, new GrowthState(), new Ledger(), eq3, new ClueBook());
        Assert.AreEqual("옛 사슬", eq3.GetAt(EquipPos.Weapon1).Name); Assert.IsNull(eq3.GetAt(EquipPos.Robe)); Assert.AreEqual("옛 노리개", eq3.GetAt(EquipPos.Charm1).Name);
    }

    [Test]
    public void SoulColors_구역별_빛깔과_저장_왕복()
    {
        Assert.AreEqual(SoulColor.Blue, SoulColors.ForZone("솔고개 마을")); Assert.AreEqual(SoulColor.Yellow, SoulColors.ForZone("보릿들"));
        Assert.AreEqual(SoulColor.Black, SoulColors.ForZone("물막이 골")); Assert.AreEqual(SoulColor.Red, SoulColors.ForZone("검은여울"));
        Assert.AreEqual(SoulColor.White, SoulColors.ForZone("도성")); Assert.AreEqual(SoulColor.Blue, SoulColors.ForZone(null));
        var snap = SaveGame.Capture(new GrowthState(), new Ledger(), new Equipment(), new ClueBook()); snap.Wallet[2] = 77; snap.Wallet[3] = 5;
        var back = SaveGame.Deserialize(SaveGame.Serialize(snap));
        Assert.AreEqual(77, back.Wallet[2]); Assert.AreEqual(5, back.Wallet[3]); Assert.AreEqual(0, back.Wallet[0]);
    }

    [Test]
    public void 인_효과는_장비_합계에_더해지고_큰_인은_2배_홈을_넘지_못한다()
    {
        var it = new ItemDef { Slot = Slot.Weapon, Rarity = Rarity.Crafted, Name = "시험", Sockets = 1 };
        Assert.IsTrue(SealEffects.Insert(it, EquipPos.Weapon1, new Seal(SoulColor.Blue, SoulColor.Blue, false)));
        Assert.IsFalse(SealEffects.Insert(it, EquipPos.Weapon1, new Seal(SoulColor.Red, SoulColor.Red, false)), "홈 하나뿐");
        Assert.IsFalse(SealEffects.Insert(new ItemDef { Sockets = 2 }, EquipPos.Belt, new Seal(SoulColor.Red, SoulColor.Red, false)), "띠는 인 홈이 없다");
        var st = new GearStats(); st.Add(it); Assert.AreEqual(0.06f, st.AttackSpeedPct, 1e-5f);
        var big = new GearStats(); SealEffects.Apply(new Seal(SoulColor.Yellow, SoulColor.Yellow, true), big); Assert.AreEqual(60, big.HpFlat);
        Assert.AreEqual("서두름 인", SealEffects.Name(new Seal(SoulColor.Red, SoulColor.Blue, false)));
        Assert.AreEqual(15, Seal.AllKinds(false).Count);
        var names = new System.Collections.Generic.HashSet<string>(); foreach (var k in Seal.AllKinds(false)) names.Add(SealEffects.Name(k));
        Assert.AreEqual(15, names.Count, "인 이름 15종이 겹치지 않는다");
    }

    [Test]
    public void 인_가방과_박힌_인은_저장_왕복()
    {
        var eq = new Equipment(); var it = new ItemDef { Slot = Slot.Weapon, Rarity = Rarity.Rare, Name = "시험", Sockets = 2 };
        it.Seals.Add(new Seal(SoulColor.Black, SoulColor.Red, true)); eq.PutAt(EquipPos.Weapon1, it);
        var snap = SaveGame.Capture(new GrowthState(), new Ledger(), eq, new ClueBook()); snap.SealBag.Add(new Seal(SoulColor.Blue, SoulColor.White, false).Text);
        var back = SaveGame.Deserialize(SaveGame.Serialize(snap));
        Assert.AreEqual(1, back.Gear[0].Seals.Count); Assert.IsTrue(back.Gear[0].Seals[0].Large); Assert.AreEqual(SoulColor.Black, back.Gear[0].Seals[0].A);
        Assert.AreEqual(1, back.SealBag.Count); Assert.IsNull(Seal.Parse("X99"));
    }

    [Test]
    public void GameSettings_클릭이동과_숫자보이기는_기본_꺼짐이고_저장_왕복한다()
    {
        var d = new GameSettings(); Assert.IsFalse(d.ClickMove); Assert.IsFalse(d.ShowNumbers);   // 개편 P0-4·5 기본값
        var on = GameSettings.Parse(new GameSettings { ClickMove = true, ShowNumbers = true }.Serialize());
        Assert.IsTrue(on.ClickMove); Assert.IsTrue(on.ShowNumbers);
        var old = GameSettings.Parse("1,0.8,1,1,1"); Assert.IsTrue(old.ReduceFlash); Assert.IsFalse(old.ClickMove, "옛 5칸 저장은 새 칸이 꺼짐");
    }

    [Test]
    public void GameSettings_번쩍임_줄이기_저장_왕복과_옛_4칸_호환()
    {
        var on = GameSettings.Parse(new GameSettings { ReduceFlash = true }.Serialize()); Assert.IsTrue(on.ReduceFlash);
        Assert.IsFalse(GameSettings.Parse("1,0.8,1,1").ReduceFlash, "옛 저장(4칸)은 꺼짐");
    }

    [Test]
    public void 도술카드_첫판은_고정_세장_갈래하나씩()
    {
        var g = new GrowthState(); g.Learned.Clear(); g.ActiveBar.Clear();
        var o = DosulCards.Offer(0, g, () => 0.3f);
        CollectionAssert.AreEquivalent(new[] { "붙잡아 부르기", "휘감기", "터뜨리기" }, o);
    }

    [Test]
    public void 도술카드_둘째판부터_갈래마다_하나_배울수있는것만()
    {
        var g = new GrowthState(); g.Learned.Clear(); g.ActiveBar.Clear(); g.SkillPointsEarned = 5;
        var rnd = new System.Random(7);
        for (int round = 1; round < DosulCards.Rounds; round++)
        {
            var o = DosulCards.Offer(round, g, () => (float)rnd.NextDouble());
            Assert.AreEqual(3, o.Count, "판 " + round);
            var br = new System.Collections.Generic.HashSet<Branch>();
            foreach (var n in o) { Assert.IsTrue(g.CanLearn(n), n); var nd = SkillTree.Find(n); Assert.IsFalse(nd.Deep); br.Add(nd.Branch); }
            Assert.AreEqual(3, br.Count, "갈래 하나씩");
            Assert.IsTrue(g.Learn(o[0]));
        }
    }

    [Test]
    public void 도술카드_얼룩점수3마다_도술점수1()
    {
        var g = new GrowthState(); g.StainPointsEarned = 7;
        Assert.AreEqual(2, DosulCards.ConvertStain(g));
        Assert.AreEqual(2, g.SkillPointsEarned); Assert.AreEqual(1, g.StainPointsFree);
    }

    [Test]
    public void Mujeok_LockedUntilB11_AndEbbRemain()
    {
        var s = new Soul(SoulKind.Fresh) { Mujeok = true };
        Soul.MujeokLocked = true; Assert.IsFalse(s.CanTendo);    // B-11 천도 전: 무적 혼은 파혼만
        Soul.MujeokLocked = false; Assert.IsTrue(s.CanTendo);    // 뒤: 모두 천도 가능
        Assert.IsTrue(new Soul(SoulKind.Fresh).CanTendo);        // 표식 없는 혼은 상관없음
        Assert.AreEqual(25f, Tide.EbbRemainMin(0f), 0.01f);      // 썰물이 막 시작
        Assert.AreEqual(0.5f, Tide.EbbRemainMin(24.5f), 0.01f);  // 밀물 30초 전
        Assert.AreEqual(0f, Tide.EbbRemainMin(30f), 0.01f);      // 밀물 중
    }

    [Test]
    public void RollFraction_FollowsClipSpeedTable()
    {
        Assert.AreEqual(0f, DodgeRules.RollFraction(0f), 1e-5f);
        Assert.AreEqual(1f, DodgeRules.RollFraction(1f), 1e-5f);            // 합이 1 → 총 거리는 dodgeDistance 그대로
        float prev = 0f; for (int i = 1; i <= 20; i++) { float f = DodgeRules.RollFraction(i / 20f); Assert.GreaterOrEqual(f, prev); prev = f; }
        // 처음 한 프레임 구간의 속도는 달리기 속도(5.5)에서 시작: 옛 EaseOut 의 25 m/s 로 튀지 않는다(4 m, 0.32초 기준 초속 = 비율 변화 × 4 / 0.0168초)
        float v0 = (DodgeRules.RollFraction(1f / 19f) - DodgeRules.RollFraction(0f)) * 4f / (0.32f / 19f);
        Assert.Less(v0, 7f);
        float vEnd = (DodgeRules.RollFraction(1f) - DodgeRules.RollFraction(18f / 19f)) * 4f / (0.32f / 19f);
        Assert.Greater(vEnd, 4f); Assert.Less(vEnd, 7f);                      // 끝도 달리기 속도로 이어진다(0 으로 멈추지 않는다)
    }

    [Test]
    public void GyeolCrackStage_단계경계()
    {
        Assert.AreEqual(0, CoreRules.GyeolCrackStage(1f));
        Assert.AreEqual(0, CoreRules.GyeolCrackStage(0.67f));
        Assert.AreEqual(1, CoreRules.GyeolCrackStage(0.66f));   // 66% 이하부터 1단계
        Assert.AreEqual(1, CoreRules.GyeolCrackStage(0.34f));
        Assert.AreEqual(2, CoreRules.GyeolCrackStage(0.33f));
        Assert.AreEqual(2, CoreRules.GyeolCrackStage(0.11f));
        Assert.AreEqual(3, CoreRules.GyeolCrackStage(0.10f));
        Assert.AreEqual(3, CoreRules.GyeolCrackStage(0f));
    }

    [Test]
    public void DosulIcons_액티브도술은모두그림이름이있고_이름이겹치지않는다()
    {
        // 도술을 새로 추가하고 그림 이름을 빠뜨리면 폰 기술 칸이 글자로만 나온다 → 여기서 바로 잡는다
        var seen = new System.Collections.Generic.HashSet<string>();
        foreach (var n in SkillTree.All)
        {
            if (!n.Active) continue;
            string id = DosulIcons.SkillIcon(n.Name);
            Assert.IsNotNull(id, n.Name + " 그림 이름 없음");
            Assert.IsTrue(seen.Add(id), n.Name + " 그림 이름 겹침: " + id);
            string prefix = n.Branch == Branch.Call ? "call_" : n.Branch == Branch.Chain ? "chain_" : "stain_";
            Assert.IsTrue(id.StartsWith(prefix), n.Name + " 갈래와 그림 이름 접두어가 다름");
        }
        Assert.IsNull(DosulIcons.SkillIcon("없는도술"));
        Assert.IsNull(DosulIcons.SkillIcon(null));
        Assert.AreEqual("q_chain", DosulIcons.QIcon("끌기"));
        Assert.AreEqual("q_bell", DosulIcons.QIcon("세우기"));   // PC 칸 글자(세우기)도 요령방울 그림
        Assert.AreEqual("q_slash", DosulIcons.QIcon("베기"));
        Assert.AreEqual("q_slash", DosulIcons.QIcon("모르는글자"));
    }

    struct UnityEngineFreeVec { public float X, Z; public UnityEngineFreeVec(float x, float z) { X = x; Z = z; } public float Len { get { return (float)System.Math.Sqrt(X * X + Z * Z); } } }
}
