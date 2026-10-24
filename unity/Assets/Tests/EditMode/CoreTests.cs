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
        Assert.Greater(WeaponDef.Mace.PahonDamageMult, WeaponDef.Chain.PahonDamageMult);
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
        Assert.AreEqual(Balance.BOSS_S1_NEOK, night.LostNeok, "보스 보상은 흩어진다");
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
    public void 손보기_다시굴리기_비용은_20씩_오르고_200이_상한_기울기와_이름물건은_불가()
    {
        Assert.AreEqual(20, Shrine.RerollCost(0));
        Assert.AreEqual(40, Shrine.RerollCost(1));
        Assert.AreEqual(200, Shrine.RerollCost(9));
        Assert.AreEqual(200, Shrine.RerollCost(30));
        var rnd = new System.Random(3);
        var it = new ItemDef { Slot = Slot.Robe, Rarity = Rarity.Crafted };
        it.Options.Add(new OptionRoll(Opt.DamagePct, 0.05f)); it.Options.Add(new OptionRoll(Opt.HpFlat, 8f));
        var l = new Ledger { Coin = 100 };
        Assert.IsTrue(Shrine.Reroll(it, 0, l, () => (float)rnd.NextDouble()));
        Assert.AreEqual(80, l.Coin); Assert.AreEqual(1, it.Rerolls);
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
        h.Warning = true; StringAssert.Contains("동이 튼다", h.NightLine());
    }
}
