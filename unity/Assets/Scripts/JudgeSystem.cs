// =============================================================================
// JudgeSystem.cs — 처결(천도·파혼) 화면 연결. 규칙은 Core 가 정하고, 여기는 '보이게·듣게' 만 한다.
//
//   E 키 / SEND 버튼  = 천도: 1.5초(연속 0.8초) 캐스팅. 동안 움직일 수 없고 시야가 좁아지며 기억의 색으로 물든다.
//   R 키 / SHATTER 버튼 = 파혼: 즉시. 주변을 밀쳐 내지만 업이 쌓이고 원념 얼룩이 남는다 (3개 겹치면 사나운 적).
//   대상 = 사거리 안에서 가장 가까운 '무릎 꿇은' 혼. 덩어리는 천도 불가.
//
// 왜 규칙과 화면을 나눴나? Core 는 Unity 를 켜지 않고도 자동 검사(EditMode 테스트)가 돌아간다.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class JudgeSystem : MonoBehaviour
{
    public Player player;
    public EnemyManager enemies;
    public HitFeel feel;
    public DamageNumbers numbers;
    public LootDrop loot;     // 바닥에 떨어진 장비(빛줄기·이름표·자동 줍기)
    public RewardFx reward;   // 처결 보상 흡수 연출(혼불·엽전)
    public Camera cam;

    CharacterPanel panel;
    Loadout lo => player.loadout;                // 든 무기·도술·장비 (Player 가 소유)
    public readonly Ledger ledger = new Ledger();
    public readonly GrowthState growth = new GrowthState();   // 품계·능력치·도술 점수(잃지 않는 성장). 명부 책 탭이 보여 준다
    public NightRun night = new NightRun();   // 하룻밤 한 판의 뼈대(시간·몫·귀환) — 규칙은 Core
    GameObject shrineView;                      // 서낭당 표시(바닥 원)
    readonly StainSet stains = new StainSet();
    readonly List<GameObject> stainViews = new List<GameObject>();

    Enemy castTarget;
    bool settled;                        // 밤 결과를 장부에 이미 반영했나
    float enemySpawnPause;               // 보스 천도 직후 잡몹 스폰 정지 남은 시간
    readonly List<Vector3> cluePos = new List<Vector3>();   // 아직 안 주운 단서 위치
    readonly List<GameObject> clueViews = new List<GameObject>();
    float castT, castTotal, chainLeft;
    /// <summary>약점 점(깃발·옷·횃불)을 낚아챈 보스 번호. 그 보스는 천도 시전 -0.5초(하한 0.5), 파혼 엽전 x1.2 (기획 감사 보강)</summary>
    public readonly System.Collections.Generic.HashSet<int> snatched = new System.Collections.Generic.HashSet<int>();
    public float CastZoom { get { return visionP; } }   // 카메라가 캐스팅 중 다가가는 정도(0~1)
    float visionP;                       // 0(평소) ~ 1(캐스팅 중): 시야 축소·기억색 정도. 0.2초에 걸쳐 부드럽게 변한다
    string toast = ""; float toastT;     // 화면 안내 글자(영문: 기본 글꼴에 한글이 없다)
    Texture2D white, vignette;
    public bool godMode;                        // ?debug 검증용: 체력이 줄지 않는다
    float vignetteT;                       // 차사가 맞았을 때 화면 가장자리 붉은 번쩍 남은 시간(0.15초, 아트 hit_player_vignette)
    Color flashColor; float flashA;        // 화면 전체 번쩍임(파혼=붉음, 천도=흰 보라). 점점 사라진다
    float sinceHit = 99f;                // 마지막으로 맞은 뒤 지난 시간(초) — 체력 회복 시작 판단
    bool played;                         // 첫 입력이 있었나 (그 전엔 적이 공격하지 않는다: 로딩 중 죽는 것 방지)
    public bool NightOver { get { return night.Over; } }
    bool debugKeys;
    public UiRoot ui;   // 있으면 장부·체력 글자는 UI Toolkit 이 그린다(IMGUI 는 그 줄을 건너뜀)
    float overT;   // 결과 화면이 뜬 지 얼마나 됐나(초)
    DayScreen dayScreen;                 // 낮 화면과 낮에 쌓이는 것(단서·소모품)
    bool inDay;                          // 지금 낮 화면인가
    public bool InDay { get { return inDay; } }
    bool namedTendoed;                   // 이번 밤 이름혼을 천도했나 (다음 낮에 장례가 열린다)

    void Start()
    {
        StripFx.HoldWhen = () => feel != null && feel.InHitStop;   // 히트스톱 동안 타격 그림도 첫 프레임에 붙든다
        LoadFuneralIndex(); CutPlayback.Cond = FuneralCond;   // 1막 장례 색인과 장례 컷의 조건 판정
        // 서낭당: 출발점이자 귀환점. 납작한 노란 원으로 '돌아갈 곳'을 보여 준다
        shrineView = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        Destroy(shrineView.GetComponent<Collider>());
        shrineView.GetComponent<Renderer>().sharedMaterial = U.Matte(ChasaPalette.CheondoGlow);
        shrineView.transform.position = new Vector3(0, 0.015f, 0);
        shrineView.transform.localScale = new Vector3(Balance.SHRINE_RADIUS * 2f, 0.01f, Balance.SHRINE_RADIUS * 2f);
        panel = gameObject.AddComponent<CharacterPanel>();   // C 키 캐릭터 창(장비·도술·능력치)
        panel.judge = this;
        if (FieldRules.On) { cardsMode = true; growth.Learned.Clear(); growth.ActiveBar.Clear(); }   // 본 게임: 도술은 카드로 하나씩 얻는다(처음 10분 M9). 저장을 불러오면 그 기록이 덮어쓴다
        lo.growth = growth;   // 성장(능력치·패시브)이 전투 수치 합계에 얹히도록 연결
        RefreshGrowth();
        enemies.onPlayerHit = OnPlayerHit;
        player.onDodgeCancelCast = () => { if (Casting) { castTarget.soul.CancelSending(); EndCast(); Say("천도를 멈추고 피했다"); } };   // 천도 중 피하기: 캐스팅만 취소, 혼은 무릎 꿇은 채 대기
        enemies.onEnemyKneel = OnEnemyKneel;
        dayScreen = new DayScreen(ledger, lo);
        SetupNight();   // 적 공격이 명중하면 체력 처리로 연결
        debugKeys = Application.isEditor || Application.absoluteURL.Contains("debug");
        white = new Texture2D(1, 1); white.SetPixel(0, 0, Color.white); white.Apply();
        panel.white = white;
        // 가운데는 투명, 가장자리로 갈수록 진해지는 둥근 가림막 (시야가 좁아지는 연출)
        const int n = 128;
        vignette = new Texture2D(n, n, TextureFormat.RGBA32, false);
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float r = new Vector2((x + 0.5f) / n - 0.5f, (y + 0.5f) / n - 0.5f).magnitude * 2f;   // 0 중심 ~ 1 가장자리
                vignette.SetPixel(x, y, new Color(1, 1, 1, Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.45f, 1f, r))));
            }
        vignette.Apply();
        vignette.wrapMode = TextureWrapMode.Clamp;
    }

    public bool Casting => castTarget != null;
    public Enemy CastTarget => castTarget;          // 화면 후처리(천도 시야 축소)가 대상 자리·보스 여부를 본다
    public float TendoSuccessAt = -99f;             // 마지막 천도 성공 시각(Time.time). 파혼에는 안 찍는다 — 성공 테두리용
    public int BossOutcomeNow => bossOutcome;   // 자동 플레이 테스트(BotScript)가 보는 값: 0 아직 · 1 천도 · 2 파혼
    public int KneelEvents;   // 무릎 꿇은 횟수 누계(BGM 용)
    public bool FieldMode { get { return clock != null; } }   // 필드(흐르는 하루)에서만 BGM 을 쓴다

    /// <summary>첫 입력이 있었던 것으로 친다(자동 연출·검증용). 이 전엔 적이 공격하지 않는다</summary>
    public void StartPlaying() { if (!played) { played = true; enemies.graceT = Balance.NIGHT_GRACE; } }

    // ===== 명령 ====================================================================
    /// <summary>이 보스의 낮 단서 수. 1호는 밤 장부(night.Clues), 2·3호는 단서장에서 그 보스 접두어("B02-")로 센다(최대 필요 수까지)</summary>
    int CluesFor(Soul s)
    {
        if (!s.Boss || s.BossId <= 1) return night.Clues;
        return Mathf.Min(Balance.BOSS_CLUES_REQUIRED, clueBook.Count(Bosses.Get(s.BossId).CluePrefix));
    }

    /// <summary>보스별 컷 이름: 예) B02-KNEEL</summary>
    static string BossCut(Soul s, string kind) { return Bosses.Get(Mathf.Max(1, s.BossId)).Cut + "-" + kind; }

    /// <summary>플레이어에게 가장 가까운 살아 있는 보스(컷신 카메라·말풍선이 따라간다)</summary>
    public Enemy NearestBoss()
    {
        Enemy best = null; float bd = float.MaxValue;
        foreach (var x in enemies.list)
        {
            if (!x.soul.Boss) continue;
            float d = (x.Pos - player.Pos).sqrMagnitude;
            if (d < bd) { bd = d; best = x; }
        }
        return best;
    }

    public void CommandTendo()
    {
        if (Casting || !player.CanActNow()) return;
        // 천도는 보낼 수 있는 혼 중 가장 가까운 것을 고른다 — 곁에 덩어리(천도 불가)가 있어도 막히지 않게(QA)
        var e = enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE, x => x.soul.CanTendoWith(CluesFor(x.soul)));
        if (e == null) e = enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE);   // 없으면 가장 가까운 혼으로 이유를 안내
        if (e == null) { Say("대상이 없다"); return; }
        if (!e.soul.CanTendo) { Say("보낼 수 없는 혼이다. 파혼만 된다"); return; }
        if (e.soul.Boss && !e.soul.CanTendoWith(CluesFor(e.soul))) cuts.Play(BossCut(e.soul, "NOCLUE"));   // 명부 인이 흐려졌다 꺼진다
        if (!e.soul.CanTendoWith(CluesFor(e.soul))) { Say("단서 " + Balance.BOSS_CLUES_REQUIRED + "개가 필요하다 (" + CluesFor(e.soul) + "). 파혼만 된다"); return; }
        if (!e.soul.BeginSending()) return;
        player.ConsumeAct();   // 후딜·피하기를 끊고 천도 시작
        castTarget = e;
        castT = 0f;
        castTotal = e.soul.Boss ? Mathf.Max(0.5f, Balance.BOSS_TENDO_CAST_TIME - (snatched.Contains(e.soul.BossId) ? 0.5f : 0f)) : CoreRules.CastTimeScaled(chainLeft > 0f, lo.stats.CastMult) * lo.Def.CastTimeMult;   // 요령방울은 천도가 빠르다   // 연속 천도면 0.8초, 보스는 2.0초
        if (!e.soul.Boss)
        {
            if (interactables != null && e.label != null && interactables.KeepsakeSouls.Contains(e.label)) castTotal = Mathf.Max(Balance.CAST_MIN_TIME, castTotal - Balance.KEEPSAKE_CAST_CUT);   // 유품을 만져 둔 혼
            if (nameLightArmed) { castTotal = Mathf.Max(Balance.CAST_MIN_TIME, castTotal - Balance.AC_NAMELIGHT_SEC); nameLightArmed = false; }   // 이름 비추기
            if (sevenLeft > 0) { castTotal = Balance.CAST_MIN_TIME; sevenLeft--; }                                                          // 일곱 이름: 하한까지
        }
        player.locked = true;
        player.facing = Mathf.Atan2(e.Pos.z - player.Pos.z, e.Pos.x - player.Pos.x);
    }

    /// <summary>이 혼을 지금 천도할 수 있나(덩어리·단서 부족이면 아니오). 데모가 대상을 고를 때 쓴다</summary>
    public bool CanTendoNow(Enemy e) { return e != null && e.soul.CanTendo && e.soul.CanTendoWith(CluesFor(e.soul)); }

    public void CommandPahon()
    {
        if (Casting || !player.CanActNow()) return;
        var e = enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE);
        if (e == null) { Say("대상이 없다"); return; }
        if (!e.soul.TryPahon()) return;
        player.ConsumeAct();   // 후딜·피하기를 끊고 파혼
        DoPahon(e);
        player.actLock = Balance.PAHON_RECOVER;   // 파혼 끝동작 0.25초
        player.PlayPahonAnim();
    }

    /// <summary>혼 하나를 처결했다(두 번째 값: true=천도, false=파혼). 보스 약점(B-05 불린 병사 천도 등)이 듣는다</summary>
    public System.Action<Enemy, bool> OnJudged;

    void DoPahon(Enemy e)
    {
        var at = e.Pos;
        LastJudgeSlow(e);
        if (OnJudged != null) OnJudged(e, false);
        lastPahonAt = Time.time;   // 깨진 이름 던지기가 '방금 파혼'을 알아본다
        if (e.soul.Name == "박돌쇠") pahonOrTendo = 2;
        if (interactables != null) interactables.OnPahon(e.soul.Name);   // 이름혼의 유품은 재가 된다
        if (e.soul.Name != null && funeralCut.ContainsKey(e.soul.Name)) { funeralPending[e.soul.Name] = 2; funeralBorn[e.soul.Name] = clock != null && clock.Phase == ClockPhase.Day ? clock.Day : -1; }   // 파혼: 조등만(장면 없음)
        if (!e.soul.Boss && e.soul.Name == null) introPlainDone++;
        e.PlayFinishAnim(false);   // 파혼 동작(터짐)
        e.Finish();
        int coinBefore = ledger.Coin;
        ledger.DoPahon(e.soul.Boss);
        TieProgress(e, 2);
        if (growth.AddPahon()) ui?.Hud.Toasts.Add("얼룩 도술 점수 +1");   // 파혼 15회마다: 파혼 길에도 도술 성장이 열린다
        // 엽전 장비 보너스(엽전 +%)와 향 내음의 마이너스(파혼 엽전 −50%)를 곱해 반영 (음수면 깎인다)
        float baseCoin = e.soul.Boss ? Balance.BOSS_PAHON_COIN : e.elite ? Balance.PAHON_COIN * Balance.ELITE_PAHON_COIN_MULT : Balance.PAHON_COIN;   // 거센 혼: 엽전 x3
        float snatchMult = e.soul.Boss && snatched.Contains(e.soul.BossId) ? 1.2f : 1f;   // 낚아챈 보스는 파혼 엽전 x1.2
        float coinX = baseCoin * lo.stats.CoinMult * lo.stats.PahonCoinMult * snatchMult - baseCoin + coinFrac;   // 소수점을 모아 반영(작은 보너스도 평균에는 들어간다)
        int coinAdd = Mathf.FloorToInt(coinX); coinFrac = coinX - coinAdd; ledger.Coin += coinAdd;
        if (e.soul.Name == "박돌쇠") { ledger.Coin += Balance.NAMED_FIRST_PAHON_COIN; }   // 첫 이름혼 파혼: 엽전이 커서 첫 손보기가 바로 열린다(처음 10분 M6)
        night.RecordCoin(ledger.Coin - coinBefore);   // 몫 달성 전/후로 나눠 쌓는다
        if (reward != null) reward.Pahon(at, 3 + (ledger.Coin - coinBefore) / 8);   // 엽전이 튀었다가 발밑으로 빨려 든다
        if (numbers != null) numbers.Spawn(at + Vector3.up * 1.7f, ledger.Coin - coinBefore, "coin");
        // 잔넋 대장 파혼 연쇄(기획 F-1b): 4m 안 같은 무리 잔넋이 함께 깨진다. 엽전은 마리당 ×0.6, 업은 마리당 +0.5 (파혼이 늘 1등이 되지 않게)
        if (e.type == SoulType.Mote && e.leader && e.group != null)
        {
            int chained = 0;
            foreach (var m in new List<Enemy>(e.group))
            {
                if (m == null || m == e || !m.alive || m.soul.Boss) continue;
                if (new Vector2(m.Pos.x - at.x, m.Pos.z - at.z).magnitude > Balance.MOTE_CHAIN_PAHON_M) continue;
                m.PlayFinishAnim(false); m.Finish(); chained++;
                int c = Mathf.RoundToInt(Balance.PAHON_COIN * Balance.MOTE_CHAIN_COIN_MULT * lo.stats.CoinMult * lo.stats.PahonCoinMult);
                ledger.Coin += c; night.RecordCoin(c); ledger.AddKarma(Balance.MOTE_CHAIN_KARMA);
            }
            if (chained > 0) Say("잔넋 " + chained + "마리가 함께 깨졌다");
        }
        if (e.soul.Boss)
        {
            if (e.soul.BossId == 3) weather.state.PlagueEased = true;   // 3호 처결: 검은여울 역병 안개 35→5
            if (e.soul.BossId <= 1) { night.BossDone = true; bossOutcome = 2; }
            MarkBossDone(e.soul.BossId);
            Say(e.label + "을(를) 깨뜨렸다");
            cuts.Play(BossCut(e.soul, "PAHON")); feel.AddShake(1f);   // 6m 대폭발, 판자가 흩어진다
            // 보스 파혼 보상: 이름 있는 물건 (즉시 강해진다 vs 천도의 기억/넋) — 기획서 6-1
            if (e.soul.BossId <= 1 && Demo.Gear && lo.Equip(ItemDef.MoonflowerBell())) { lo.lastDrop = "이름 있는 장비: 월화 방울 (파혼 반경 +)"; lo.lastDropT = 6f; }
        }
        // 폭발: 반경 안 싸우는 적에게 피해 + 바깥으로 넉백. 거리(2.5m)를 속도로 바꾸려면 마찰을 곱한다
        float kb = Balance.PAHON_KNOCKBACK_DIST * Config.ENEMY_KNOCKBACK_FRICTION * lo.Def.PahonKnockbackMult * lo.stats.PahonKnockbackMult;   // 육모방망이는 더 멀리 날린다
        float radius = e.elite ? Balance.ELITE_PAHON_RADIUS : lo.stats.PahonRadius(Balance.PAHON_RADIUS);   // 거센 혼 파혼: 반경 4.5m   // 업 쪽 장비: 파혼 반경 (상한 안)
        if (e.elite)   // 거센 혼 파혼 폭발은 부른 잔넋까지 터뜨린다(마리당 엽전 +2)
            foreach (var o in new List<Enemy>(enemies.list))
            {
                if (o == null || !o.eliteMote || o.gone) continue;
                if (new Vector2(o.Pos.x - at.x, o.Pos.z - at.z).magnitude > radius + o.radius) continue;
                o.PlayFinishAnim(false); o.Finish(); ledger.Coin += Balance.ELITE_MOTE_COIN; night.RecordCoin(Balance.ELITE_MOTE_COIN);
            }
        int pahonDmg = Mathf.RoundToInt(Balance.PAHON_DAMAGE * lo.Def.PahonDamageMult * lo.stats.PahonDamageMult);
        if (shadowT > 0f)   // 검은 갓의 그림자: 폭발이 주변 무릎 꿇은 혼까지 깨뜨린다(깨진 혼마다 업 +1 — DoPahon 이 쌓는다)
            foreach (var o in new List<Enemy>(enemies.list))
            {
                if (o == e || !o.kneeling || o.soul.Boss) continue;
                if (new Vector2(o.Pos.x - at.x, o.Pos.z - at.z).magnitude > radius + o.radius) continue;
                o.soul.TryPahon(); o.Finish(); ledger.DoPahon(false); numbers.Spawn(o.HeadPosition, 0, "heavy");
                int sc = Mathf.RoundToInt(Balance.PAHON_COIN * lo.stats.CoinMult * lo.stats.PahonCoinMult); ledger.Coin += sc; night.RecordCoin(sc);   // 함께 깨진 혼도 엽전을 낸다(균형 2차)
            }
        foreach (var o in enemies.list)
        {
            if (o == e || !o.alive) continue;
            var d = new Vector3(o.Pos.x - at.x, 0, o.Pos.z - at.z);
            if (d.magnitude > radius + o.radius) continue;
            var dir = d.magnitude > 0.01f ? d.normalized : Vector3.right;
            o.TakeHit(pahonDmg, dir, kb, 0.3f);
            numbers.Spawn(o.HeadPosition, pahonDmg, "heavy");
        }
        // 파편 모델: 3종 중 하나를 무작위 방향으로 터뜨린다 (반경에 맞춰 크기)
        FxMesh.Burst("fx_pahon_shards_" + "abc"[Random.Range(0, 3)], new Vector3(at.x, at.y + 0.05f, at.z), radius / 1.25f, 0.55f, 0.5f, 1.15f, 0.4f, null, Random.Range(0f, 360f));
        feel.HitStop(Balance.PAHON_HITSTOP_FRAMES);
        StripFx.Flat("pahon_ring", 8, 0.4f, at, radius * 2f, new Color(1f, 1f, 1f, 0.9f));   // 파혼 고리(아트): 반경 끝까지 퍼진다
        Sfx.Play("sfx.pahon.burst." + Sfx.WeaponTag(lo.weapon));
        feel.AddShake(Balance.PAHON_SHAKE);
        feel.AddZoom(1f);                       // 파혼: 확 다가가는 쿵
        flashColor = new Color(0.55f, 0.05f, 0.08f); flashA = 0.55f;   // 붉은 번쩍임(깨뜨림)
        // 원념 얼룩: 3개가 겹치면 그 자리에서 사나운 적이 솟는다
        float cx, cz;
        if (stains.Add(at.x, at.z, out cx, out cz))
        {
            enemies.SpawnFierce(new Vector3(cx, 0, cz));
            Say("사나운 혼이 깨어났다!");
        }
    }

    /// <summary>품계가 올랐다: 화면 가운데에 붉은 품계 인이 1초 찍힌다(처음 10분 M6). 글자 알림은 그대로 곁들인다</summary>
    void OnRankUp()
    {
        Sfx.Play("sfx.ui.rank.up");
        if (ui == null) return;
        ui.Hud.Toasts.Add("품계 " + growth.Rank + "품 — 도술 점수 +1, 능력치 +" + GrowthState.StatPerRank);
        ui.Hud.StampTitle = "품계 " + growth.Rank; ui.Hud.StampSub = Ko.RankTitle(growth.Rank); ui.Hud.StampAge = 0f;
        flashColor = new Color(0.05f, 0.02f, 0.02f); flashA = 0.35f;   // 화면이 살짝 어두워진다
        cardDelay = Mathf.Max(cardDelay, 1.6f);   // 인이 찍히는 걸 본 뒤에 도술 카드가 뜬다
    }

    // ---- 첫 도술 카드(처음 10분 M9): 점수가 생기고 싸움이 잠잠하면 카드 세 장이 뜬다. 1·2·3 또는 클릭, 다시 뽑기 R ----
    bool cardsMode, cardPicksLoaded, cardRerolled; int cardPicks; float cardDelay; List<string> cardList;
    readonly HashSet<string> cardSeen = new HashSet<string>();
    void TickCards(float dt)
    {
        if (ui == null || DosulCards.Open) return;
        if (ui.Hud.CardPick == null) { ui.Hud.CardPick = PickCard; ui.Hud.CardRerollNow = RerollCards; }
        if (!cardsMode || cardPicks >= DosulCards.Rounds) return;
        DosulCards.ConvertStain(growth);   // 얼룩 점수 3마다 도술 점수 1(처음 다섯 판만)
        if (growth.SkillPointsFree <= 0) return;
        if (Casting || cuts.Active || inDay || night.Over || ledger.Dead || CharacterPanel.Open || SettingsPanel.Open || FightLeft(null) > 0) return;
        if (cardDelay > 0f) { cardDelay -= dt; return; }
        cardRerolled = false; OfferCards();
    }
    void OfferCards()
    {
        cardList = DosulCards.Offer(cardPicks, growth, () => Random.value, cardSeen);
        if (cardList.Count == 0) { cardPicks = DosulCards.Rounds; return; }   // 고를 게 없으면 카드는 끝(도술 창으로)
        var h = ui.Hud; int n = cardList.Count;
        h.CardNames = new string[n]; h.CardMarks = new string[n]; h.CardDescs = new string[n]; h.CardRound = cardPicks;
        for (int i = 0; i < n; i++)
        {
            var nd = SkillTree.Find(cardList[i]);
            h.CardNames[i] = nd.Name + (growth.LevelOf(nd.Name) > 0 ? " +1" : "");
            h.CardMarks[i] = DosulCards.Mark(nd.Branch);
            h.CardDescs[i] = SkillTree.BranchName(nd.Branch) + " · " + (nd.Active ? "액티브" : "패시브") + "\n" + nd.Desc;
        }
        h.CardReroll = cardPicks == 0 || cardRerolled ? null : "엽전 " + DosulCards.RerollCoin + " · 다시 뽑기 (R)" + (ledger.Coin < DosulCards.RerollCoin ? " — 엽전이 모자라다" : "");
        DosulCards.Open = true; Sfx.Play("sfx.ui.tab");
    }
    /// <summary>카드를 골랐다(1~3번 칸). 고른 도술을 배우고 카드는 닫힌다</summary>
    public void PickCard(int i)
    {
        if (!DosulCards.Open || cardList == null || i < 0 || i >= cardList.Count) return;
        string name = cardList[i];
        foreach (var n in cardList) cardSeen.Add(n);
        growth.Learn(name); cardPicks++;
        RefreshGrowth();
        ui.Hud.CardNames = null; DosulCards.Open = false; cardDelay = 0.8f;
        Sfx.Play("sfx.ui.confirm"); ui.Hud.Toasts.Add("도술 — " + name);
    }
    public void RerollCards()
    {
        if (!DosulCards.Open || cardPicks == 0 || cardRerolled) return;
        if (ledger.Coin < DosulCards.RerollCoin) { Sfx.Play("sfx.ui.deny"); return; }
        ledger.Coin -= DosulCards.RerollCoin; cardRerolled = true;
        ui.Hud.CardNames = null; OfferCards();
    }
    /// <summary>카드가 떠 있는 동안 세계는 멈춘다. 키 입력만 GameMain 이 여기로 넘긴다</summary>
    public void CardInput()
    {
        if (Input.GetKeyDown(KeyCode.Alpha1)) PickCard(0); else if (Input.GetKeyDown(KeyCode.Alpha2)) PickCard(1); else if (Input.GetKeyDown(KeyCode.Alpha3)) PickCard(2);
        else if (Input.GetKeyDown(KeyCode.R)) RerollCards();
    }

    // ---- 거센 혼(첫 강적, 처음 10분 M10): 박돌쇠 처결 뒤 이름혼 자리에서 60m 멀어지거나 7분이 되면 보릿들 둑길 들머리에 한 번 ----
    bool eliteSpawned; float runT;
    static readonly Vector3 EliteSpot = new Vector3(212f, 0f, 125f);   // 보릿들 둑길 들머리(임시 좌표: 아트 마커가 오면 교체)
    void TickEliteSpawn(float dt)
    {
        runT += dt;
        if (eliteSpawned || !FieldRules.On || pahonOrTendo == 0 || introFrozen) return;
        float away = new Vector2(player.Pos.x - MapLayout.NamedX, player.Pos.z - MapLayout.NamedZ).magnitude;
        if (away < Balance.ELITE_FIRST_AWAY && runT < Balance.ELITE_FIRST_SEC) return;
        if (new Vector2(player.Pos.x - EliteSpot.x, player.Pos.z - EliteSpot.z).magnitude < 30f) return;   // 코앞에서 갑자기 서지 않게
        eliteSpawned = true;
        var el = enemies.SpawnElite(EliteSpot);
        EliteArena.Make(this, el);
    }

    // ---- 싸움 끝 신호(처음 10분 M7·M8) ----
    bool fightOn; int fJudged, fStartNeok, fStartCoin, fStartMem;
    /// <summary>플레이어 둘레 18m 안에 아직 처결이 남은 혼(보스 제외)이 몇인가. except 는 방금 처결하는 혼</summary>
    int FightLeft(Enemy except)
    {
        int n = 0;
        foreach (var o in enemies.list)
        {
            if (o == null || o == except || o.soul.Boss || !o.Targetable) continue;
            if (!(o.alive || o.kneeling || o.sending)) continue;
            if (new Vector2(o.Pos.x - player.Pos.x, o.Pos.z - player.Pos.z).magnitude > 18f) continue;
            n++;
        }
        return n;
    }
    /// <summary>싸움이 시작되면 장부를 적어 두고, 다 끝나면 한 줄로 정리해 보여 준다</summary>
    void TickFight()
    {
        int left = FightLeft(null);
        if (!fightOn && left > 0 && enemies.list.Exists(o => o.alive && !o.soul.Boss && new Vector2(o.Pos.x - player.Pos.x, o.Pos.z - player.Pos.z).magnitude < 12f && o.soul.State == SoulState.Active))
        { fightOn = true; fJudged = 0; fStartNeok = ledger.Neok; fStartCoin = ledger.Coin; fStartMem = ledger.Memory; }
        if (fightOn && left == 0 && !Casting)
        {
            fightOn = false;
            int dn = ledger.Neok - fStartNeok, dc = ledger.Coin - fStartCoin, dm = ledger.Memory - fStartMem;
            if (dn > 0 || dc > 0 || dm > 0) { Sfx.Play("sfx.fight.end"); Say("정리 — 넋 +" + dn + " · 엽전 +" + dc + " · 기억 " + dm); }   // 징 한 번(소리는 사운드팀 파일이 오면 난다)
        }
    }
    /// <summary>방금 처결로 싸움의 마지막 혼이 끝났나? 그렇다면 0.25초 절반 속도로 느리게(천도·파혼 똑같이)</summary>
    void LastJudgeSlow(Enemy e)
    {
        if (!fightOn) return;
        fJudged++;   // 혼 하나뿐인 작은 싸움엔 느려짐을 쓰지 않는다(둘 이상일 때만)
        if (fJudged >= 2 && FightLeft(e) == 0) feel.SlowMo(Balance.FIGHT_END_SLOW_SEC, Balance.FIGHT_END_SLOW_SCALE);
    }

    int gainedExtra;   // 한 줄 꿰기로 덤으로 간 혼이 준 넋(알림용)
    /// <summary>천도로 얻은 넋을 그 혼이 있던 구역의 빛깔 주머니에도 쌓는다(인 만들기 재료). 품계용 넋과는 별개로 쓴다</summary>
    void CreditSoulColor(Vector3 at, int amount)
    {
        if (amount <= 0) return;
        var c = SoulColors.ForZone(FieldZones.NameAt(at.x, at.z));
        lo.wallet.Add(c, amount);
        ui?.Hud.Toasts.Add(SoulColors.KoName(c) + " +" + amount);
    }

    void FinishTendo()
    {
        var tp = castTarget.Pos;   // Finish 뒤엔 혼이 사라질 수 있어 자리를 미리 적어 둔다
        FxMesh.Burst("fx_tendo_pillar", tp, 0.8f, 0.9f, 0.6f, 1f, 1.5f, new Color(0.85f, 0.8f, 1f, 0.7f));   // 크기 −20%·알파 −30%(아트 검수: 화면 1/3을 흰 덩어리로 덮음)
        FxMesh.Burst("fx_tendo_ring", new Vector3(tp.x, tp.y + 0.06f, tp.z), 0.85f, 0.8f, 0.5f, 1.6f, 0f, new Color(0.85f, 0.8f, 1f, 0.7f));
        TendoSuccessAt = Time.time;
        if (castTarget.soul.Name != null && funeralCut.ContainsKey(castTarget.soul.Name)) { funeralPending[castTarget.soul.Name] = 1; funeralBorn[castTarget.soul.Name] = clock != null && clock.Phase == ClockPhase.Day ? clock.Day : -1; }   // 천도: 다음 낮 그 집 장례
        weather.ClearPlague(tp);   // 역병 안개: 천도한 자리 반경 4m 가 15초 걷힌다
        LastJudgeSlow(castTarget);
        castTarget.PlayFinishAnim(true);   // 천도 동작(일어남→빛 알갱이→숨김)
        castTarget.Finish();
        tendoToday++;                                                    // 혼불 발 수
        if (escortArmed) { escortT = Balance.AC_ESCORT_SEC; escortArmed = false; }   // 배웅길: 천도 직후 적이 느려진다
        if (!castTarget.soul.Boss && growth.ActiveBar.Contains("일곱 이름") && ++sevenCount >= 7) { sevenCount = 0; sevenLeft = 2; Say("일곱 이름 — 다음 천도 둘이 빨라진다"); }
        TieProgress(castTarget, 1);                                      // 한 줄 꿰기: 묶은 둘 중 하나는 천도·하나는 파혼하면 둘 다 보상 +5%
        if (castTarget.soul.Boss)
        {
            if (castTarget.soul.BossId == 3) weather.state.PlagueEased = true;   // 3호 처결: 검은여울 역병 안개 35→5
            int g = ledger.CompleteBossTendo();
            growth.AddBossPoint();                  // 보스 천도 = 도술 점수 1
            ui?.Hud.Toasts.Add("도술 점수 +1");
            CreditSoulColor(castTarget.Pos, g); night.RecordBoss(g);                    // 보스 보상은 '추가 수확분' — 동이 트면 잃는다
            enemySpawnPause = Balance.BOSS_CAST_ADD_PAUSE;
            Say(castTarget.label + "을(를) 보냈다"); if (castTarget.soul.BossId <= 1) bossOutcome = 1;
            MarkBossDone(castTarget.soul.BossId);
            if (cuts.Play(BossCut(castTarget.soul, "TENDO"))) { player.CommandStop(); enemies.graceT = Mathf.Max(enemies.graceT, 7f); }   // 7초 컷: 입력 잠김·적 멈춤
        }
        else
        {
            int before = ledger.Neok;
            ledger.CompleteTendo();
            ledger.Neok += Mathf.RoundToInt((ledger.Neok - before) * (lo.stats.TendoNeokMult - 1f + lo.Def.NeokPct));   // 향 내음: 천도 넋 보너스
            // 묻힌 혼은 넋 ×1.25, 넋두리는 기억 조각 +1 (기획 F-1b)
            if (castTarget.type == SoulType.Buried) ledger.Neok += Mathf.RoundToInt((ledger.Neok - before) * (Balance.BURIED_TENDO_NEOK_MULT - 1f));
            if (castTarget.type == SoulType.Wail) ledger.Memory += Balance.WAIL_TENDO_MEMORY;
            if (castTarget.soul.Name == "박돌쇠") { int bonus = (ledger.Neok - before) * (Balance.NAMED_FIRST_NEOK_MULT - 1); ledger.Neok += bonus; }   // 첫 이름혼은 넋이 크다: 5분 안에 첫 품계(처음 10분 M6)
            if (castTarget.elite)   // 거센 혼 천도: 넋 x3 + 기억 한 줄(두레 좌상 오봉). 잔넋은 EliteArena 가 조용히 흩는다
            {
                ledger.Neok += (ledger.Neok - before) * (Balance.ELITE_TENDO_NEOK_MULT - 1);
                memLine = "징을 치면 들판이 다 모였다. 아무도 오지 않아서, 더 세게 쳤다."; memLineT = 7f; ledger.Memory += 1;
                Say("두레 좌상 오봉");
            }
            int gained = ledger.Neok - before;
            if (reward != null) reward.Tendo(tp, 1 + gained / 30);   // 혼불이 날아와 가슴에 든다
            if (numbers != null) numbers.Spawn(tp + Vector3.up * 1.7f, gained, "neok");
            if (growth.AddNeok(gained) > 0) OnRankUp();   // 품계 상승: 인이 찍히는 연출
            CreditSoulColor(tp, gained); night.RecordTendo(ledger.Neok - before);   // 몫인지 추가 수확분인지 나눠 쌓는다
            if (OnJudged != null) OnJudged(castTarget, true);
            if (castTarget.soul.Name == "박돌쇠") pahonOrTendo = 1;
            if (castTarget.soul.Name == null) introPlainDone++;
            if (castTarget.soul.Name != null) namedTendoed = true;   // 이름혼을 보냈다 → 다음 낮 장례
            if (night.TakeNamedSpawn() && clock == null) SpawnNamedSoul();   // 몫의 마지막 하나는 이름혼 박돌쇠
        }
        // 기억 한 줄: 천도해야만 보이는 이야기(파혼엔 없다). 이름혼의 기억은 추리판 사실도 켠다
        if (castTarget.soul.Name == "곽 뱃꾼" && clueBook.Add("B01-D4")) Say("단서 — 곽 뱃꾼의 기억");   // 밤 대체 단서(서사 확정): 천도해야만 얻는다
        string fact; var ml = memories.Collect(castTarget.soul, out fact);
        if (ml != null) { memLine = ml; memLineT = 5f; if (fact != null && Demo.DebugUi) ui?.Hud.Toasts.Add("추리판 " + fact + " 켜짐"); }
        chainLeft = lo.stats.ChainWindow + lo.Def.ChainWindowAddS;   // 젖은 소매가 있으면 창이 길다
        feel.AddShake(0.15f);
        Sfx.Play("sfx.tendo.done." + Sfx.WeaponTag(lo.weapon));
        feel.SlowMo(Balance.TENDO_COMPLETE_SLOWMO, Balance.TENDO_COMPLETE_SLOWMO_SCALE);   // 멈춤이 아니라 느림 = 보냄
        feel.AddZoom(-0.7f);                    // 천도 완료: 숨을 내쉬듯 화면이 살짝 멀어졌다 돌아온다
        flashColor = new Color(0.85f, 0.8f, 1f); flashA = 0.5f;        // 흰 보랏빛 번쩍임(보냄)
        StripFx.Billboard("tendo_motes", 8, 0.8f, tp + Vector3.up * 1.2f, Vector3.zero, 2.4f);   // 천도 알갱이(아트): 위로 오르며 사라진다. 흔들림·번쩍은 더하지 않는다
        EndCast();
    }

    void EndCast()
    {
        castTarget = null;
        castT = 0f;
        player.locked = false;
    }

    // ===== M4.5: 장비 드롭·도술 ========================================================
    /// <summary>맺힘 0 → 장비 드롭 판정 1회(처결 방식과 무관). 사나운 적은 귀한 확정</summary>
    /// <summary>명부에서 점수를 쓴 뒤: 전투 수치 합계를 다시 계산하고 최대 체력도 맞춘다</summary>
    public void RefreshGrowth()
    {
        lo.Refresh(); ledger.SetMaxHp(lo.stats.MaxHp);
        Enemy.BoundBonus = lo.stats.BoundBonus;                          // 묶인 자
        stains.DurationMult = 1f - lo.stats.StainShorten;                // 마른 얼룩
    }

    void OnEnemyKneel(Enemy e)
    {
        KneelEvents++;   // BGM 재생기가 '무릎 꿇는 순간'을 알아채는 번호표
        Sfx.Play("sfx.kneel");   // 무릎 꿇는 소리 = '지금 고를 때'
        if (!e.soul.Boss && !firstKneelDone && FieldRules.On)
        {
            // 첫 처결: 안내 글 대신 화면 하단에 큰 카드 둘(천도·파혼 같은 크기·밝기). 시간 제한 없음(이 혼만 대기가 멈춘다)
            firstKneelDone = true; firstCardSoul = e; e.soul.Frozen = true; hints.On(HintEvent.FirstKneel, false);
        }
        else Hint(HintEvent.FirstKneel);
        if (e.soul.Boss) cuts.Play(BossCut(e.soul, "KNEEL"));   // 영감: "아직… 못 건넸소."
        // 검은 술: 무릎 꿇은 혼의 대기 시간이 짧아진다 (덩어리는 제외, 최소 WAIT_FLOOR)
        if (!e.soul.Boss && e.soul.State == SoulState.Kneel)
        {
            e.soul.WaitTotal = lo.stats.AdjustWait(e.soul.WaitTotal, e.soul.Kind == SoulKind.Lump);
            e.soul.WaitLeft = e.soul.WaitTotal;
        }
        if (e.elite && !e.soul.Boss) { e.soul.WaitTotal = lo.stats.AdjustWait(Balance.ELITE_JUDGE_WAIT, false); e.soul.WaitLeft = e.soul.WaitTotal; }   // 거센 혼의 처결 대기는 7초
        if (!Demo.Gear) return;   // 시연판 기본 구성: 장비 드롭 없음
        ItemDef it;
        if (!firstGearGiven && ++kneelCount >= 2 && FieldRules.On)
        {
            // 첫 장비는 확정(처음 10분 M4): 두 번째로 무릎 꿇은 혼이 흔한 노리개를 떨군다. 처결 방식과 무관
            var seq = new Queue<float>(new[] { 0f, 0.99f, 0.5f });   // 드롭 통과 → 흔한 등급 → 첫 칸
            it = Loot.Roll(() => seq.Count > 0 ? seq.Dequeue() : 0.9f, false, 0, new[] { Slot.Charm });
        }
        else if (e.elite)
        {
            // 거센 혼은 손본 장비 확정(처결과 무관): 드롭 통과 → 손본 등급 구간 → 칸은 무작위
            var sq = new Queue<float>(new[] { 0f, Balance.DROP_RARITY_RARE + Balance.DROP_RARITY_CRAFTED * 0.5f });
            it = Loot.Roll(() => sq.Count > 0 ? sq.Dequeue() : Random.value, false, 0, lo.gear.DropKinds());
        }
        else if (e.eliteMote) it = null;   // 부른 잔넋은 장비를 주지 않는다
        else it = Loot.Roll(() => Random.value, e.soul.Fierce, FieldRules.On ? RingLoot.RingAt(e.Pos.x, e.Pos.z, FieldZones.NameAt(e.Pos.x, e.Pos.z) == "검은여울") : 0, lo.gear.DropKinds());   // 필드에선 위치로 고리를 정해 등급 표를 쓴다
        if (it == null) return;
        firstGearGiven = true;
        string nm = Ko.ItemName(it, Ko.FamilyOf(it.Slot, it.Slot == Slot.Weapon ? (WeaponId?)lo.weapon : null));
        if (loot != null) loot.Add(it, e.Pos, nm);   // 바닥에 떨어진다: 가까이 가면 줍는다
        else PickLoot(it, e.Pos);
    }
    bool firstGearGiven; int kneelCount;

    /// <summary>바닥 장비를 주웠다: 지금 것보다 낫거나 빈 칸이면 끼고, 아니면 가방(알림)만. 줍는 자리에 빛줄기를 한 번 더 남긴다</summary>
    public void PickLoot(ItemDef it, Vector3 at)
    {
        string txt = Loadout.Describe(it);
        if (lo.Equip(it))
        {
            ledger.SetMaxHp(lo.stats.MaxHp);
            lo.lastDrop = "주워서 찼다: " + txt;
        }
        else lo.lastDrop = "주웠다(지금 것이 낫다): " + txt;
        lo.lastDropT = 5f;
        Sfx.Play("sfx.ui.confirm");
        TimedSprite.Spawn("fx/loot_" + (it.Named ? "named" : it.Rarity == Rarity.Rare ? "rare" : it.Rarity == Rarity.Crafted ? "crafted" : "common"), at, 1.5f);   // 줍는 순간의 빛
    }

    // ===== 액티브 도술: 1~4키는 명부(성장)에서 칸에 올린 액티브. 처음엔 붙잡아 부르기·휘감기·터뜨리기가 끼워져 있다 =====
    bool SkillsOn { get { return Demo.Skills || FieldRules.On; } }   // 시연판은 꺼 두고, 필드(본 게임)에서는 켠다

    /// <summary>그 칸의 액티브 이름(비었으면 null)</summary>
    public string ActiveNameAt(int slot) { return slot >= 0 && slot < growth.ActiveBar.Count ? growth.ActiveBar[slot] : null; }

    // 도술이 남기는 짧은 상태들
    bool nameLightArmed, escortArmed; int sevenLeft;   // sevenLeft: 일곱 이름이 남긴 '하한 천도' 횟수(쓰면 2)
    int sevenCount;                                    // 일곱 이름: 센 천도 수(파혼이 끼어도 안 지워진다)
    float coinFrac;                                    // 파혼 엽전 배수의 소수점 누적(엽전 7에 +5% 가 반올림으로 0이 되지 않게)
    Enemy tiedA, tiedB; int tiedKinds;                 // 한 줄 꿰기: 묶은 둘과 지금까지 한 일(1 천도·2 파혼)
    //          // 다음 천도에 걸리는 것(이름 비추기·배웅길·일곱 이름)
    float escortT, wrathT, rideT, shadowT;                  // 배웅길 느림·원념 두르기·얼룩 타기·검은 갓의 그림자 남은 시간
    float lastPahonAt = -99f;                               // 마지막 파혼 시각(깨진 이름 던지기)
    int tendoToday;                                         // 오늘 천도한 혼 수(혼불 발 수)
    ClockPhase lastPhase;
    public readonly WeatherRuntime weather = new WeatherRuntime();   // 날씨 굴림·효과(밤에만)·소리
    float lastQuotaMove;

    void TickActives(float dt)
    {
        if (clock != null && clock.Phase == ClockPhase.Dawn && lastPhase != ClockPhase.Dawn) tendoToday = 0;   // 새 하루
        if (clock != null) lastPhase = clock.Phase;
        bool dirty = false;
        if (wrathT > 0f) { wrathT -= dt; if (wrathT <= 0f) { lo.buffDamage = 0f; dirty = true; } }
        if (rideT > 0f) { rideT -= dt; if (rideT <= 0f) { lo.buffMove = 0f; dirty = true; } }
        if (shadowT > 0f) shadowT -= dt;
        // 몫을 채움: 그날 명부 몫(천도 NIGHT_QUOTA)을 채우면 이동 속도 +8%/+16% (필드에는 밤 장부가 없어 몫 채움을 night 로 본다)
        float quotaMove = growth.LevelOf("몫을 채움") > 0 && night.QuotaDone ? 0.08f * growth.LevelOf("몫을 채움") : 0f;
        if (!Mathf.Approximately(quotaMove, lastQuotaMove)) { lastQuotaMove = quotaMove; dirty = true; }
        lo.buffMovePassive = quotaMove;
        if (dirty) lo.Refresh();
        float slow = escortT > 0f ? 1f - Balance.AC_ESCORT_SLOW : 1f;
        if (escortT > 0f) escortT -= dt;
        foreach (var e in enemies.list) e.slowMult = e.soul.Boss ? 1f : slow;   // 보스는 느려지지 않는다
    }

    /// <summary>도술 1~4키. 효과가 없었으면(대상 없음 등) 재사용 대기를 쓰지 않는다</summary>
    public void UseSkill(int slot)
    {
        if (!SkillsOn || night.Over || ledger.Dead || Casting || player.locked) return;
        string name = ActiveNameAt(slot);
        if (name == null || !lo.active.Ready(name)) return;
        if (CastActive(name)) lo.active.Start(name);
    }

    List<Enemy> AliveNear(Vector3 at, float range, bool includeBoss)
    {
        var list = new List<Enemy>();
        foreach (var e in enemies.list)
            if (e.alive && (includeBoss || !e.soul.Boss) && new Vector2(e.Pos.x - at.x, e.Pos.z - at.z).magnitude <= range + e.radius) list.Add(e);
        list.Sort((x, y) => (x.Pos - at).sqrMagnitude.CompareTo((y.Pos - at).sqrMagnitude));
        return list;
    }

    bool CastActive(string name)
    {
        switch (name)
        {
            case "붙잡아 부르기": // 무릎 꿇은 혼 대기 +3초, 서 있는 적 0.8초 멈칫
            {
                int n = 0;
                foreach (var e in enemies.list)
                {
                    if (new Vector2(e.Pos.x - player.Pos.x, e.Pos.z - player.Pos.z).magnitude > Balance.SKILL_HOLD_RADIUS) continue;
                    if (e.kneeling) { e.soul.WaitLeft += Balance.SKILL_HOLD_WAIT_BONUS; e.soul.WaitTotal += Balance.SKILL_HOLD_WAIT_BONUS; n++; }
                    else if (e.alive) { e.stun = Mathf.Max(e.stun, Balance.SKILL_HOLD_STUN); e.atk.Interrupt(); n++; }
                }
                if (n == 0) { Say("반경 안에 아무도 없다"); return false; }
                GroundFx.Play(player.Pos, Balance.SKILL_HOLD_RADIUS, "fx/fx_call_", 3, 0.7f);
                Say(name); return true;
            }
            case "휘감기": // 반경 4m 서 있는 적 1.5초 묶기
            {
                int n = 0;
                foreach (var e in enemies.list)
                {
                    if (!e.alive || new Vector2(e.Pos.x - player.Pos.x, e.Pos.z - player.Pos.z).magnitude > Balance.SKILL_BIND_RADIUS + e.radius) continue;
                    e.stun = Mathf.Max(e.stun, Balance.SKILL_BIND_STUN); e.boundT = Balance.SKILL_BIND_STUN; e.atk.Interrupt(); e.vel = Vector3.zero; n++;
                }
                if (n == 0) { Say("반경 안에 아무도 없다"); return false; }
                GroundFx.Play(player.Pos, Balance.SKILL_BIND_RADIUS, "fx/fx_bind_", 3, 0.6f);
                Say(name); return true;
            }
            case "터뜨리기": // 가까운 얼룩 하나를 터뜨려 지운다(업 그대로), 반경 2.5m 맺힘 40
            {
                float sx, sz;
                if (!stains.RemoveNearest(player.Pos.x, player.Pos.z, Balance.SKILL_BURST_FIND_RANGE, out sx, out sz)) { Say("터뜨릴 얼룩이 없다"); return false; }
                foreach (var e in enemies.list)
                {
                    if (!e.alive) continue;
                    var d = new Vector3(e.Pos.x - sx, 0, e.Pos.z - sz);
                    if (d.magnitude > Balance.SKILL_BURST_RADIUS + e.radius) continue;
                    int dmg = Mathf.RoundToInt(Balance.SKILL_BURST_DAMAGE * lo.stats.DamageMult);
                    e.TakeHit(dmg, d.magnitude > 0.01f ? d.normalized : Vector3.right, 10f, 0.3f);
                    numbers.Spawn(e.HeadPosition, dmg, "heavy");
                }
                feel.AddShake(0.5f); feel.HitStop(3);
                GroundFx.Play(new Vector3(sx, 0, sz), Balance.SKILL_BURST_RADIUS, "fx/fx_burst_", 3, 0.5f);
                Say(name); return true;
            }
            case "혼불 날리기": // 혼불 1 + 오늘 천도한 혼 수(최대 5발): 가까운 적부터 한 발씩
            {
                var near = AliveNear(player.Pos, Balance.AC_SOULFIRE_RANGE, true);
                if (near.Count == 0) { Say("혼불이 닿을 적이 없다"); return false; }
                int shots = Mathf.Min(Balance.AC_SOULFIRE_MAX, 1 + tendoToday);
                for (int i = 0; i < shots; i++)
                {
                    var e = near[i % near.Count];
                    int dmg = Mathf.RoundToInt(Balance.AC_SOULFIRE_DMG * lo.stats.DamageMult);
                    e.TakeHit(dmg, (e.Pos - player.Pos).normalized, 4f, 0.15f);
                    numbers.Spawn(e.HeadPosition, dmg, "normal");
                }
                Say("혼불 날리기 x" + shots); return true;
            }
            case "이름 비추기": nameLightArmed = true; Say("다음 천도가 빨라진다"); return true;
            case "배웅길": escortArmed = true; Say("다음 천도 뒤 적이 느려진다"); return true;
            case "일곱 이름": Say("일곱 이름 " + sevenCount + "/7 (천도 7번마다 다음 둘이 빨라진다)"); return false;   // 세는 도술: 눌러 쓰는 게 아니라 칸에 넣어 두면 켜진다
            case "여럿 끌기": // 가까운 일반 적 셋을 한꺼번에 끌어온다
            {
                var near = AliveNear(player.Pos, Balance.AC_MULTIPULL_RANGE, false);
                if (near.Count == 0) { Say("끌어올 적이 없다"); return false; }
                for (int i = 0; i < Mathf.Min(Balance.AC_MULTIPULL_N, near.Count); i++) near[i].StartPulled();
                Say(name); return true;
            }
            case "매듭 걸음": // 8m 돌진, 지나는 동안 피격 없음
                if (!player.CommandKnotDash(Balance.AC_DASH_DIST, null)) { Say("지금은 걸을 수 없다"); return false; }
                return true;
            case "한 줄 꿰기": // 무릎 꿇은 혼 둘을 한 줄로 묶어, 첫째를 천도하면 둘째도 함께 간다
            {
                var ks = new List<Enemy>();
                foreach (var e in enemies.list)
                    if (e.kneeling && !e.soul.Boss && e.soul.CanTendo && new Vector2(e.Pos.x - player.Pos.x, e.Pos.z - player.Pos.z).magnitude <= Balance.AC_TIE_RANGE) ks.Add(e);
                if (ks.Count < 2) { Say("무릎 꿇은 혼 둘이 필요하다"); return false; }
                ks.Sort((x, y) => (x.Pos - player.Pos).sqrMagnitude.CompareTo((y.Pos - player.Pos).sqrMagnitude));
                tiedA = ks[0]; tiedB = ks[1]; tiedKinds = 0; Say("두 혼을 한 줄로 꿰었다 — 하나는 천도, 하나는 파혼"); return true;
            }
            case "쇠사슬 울": // 반경 5m 적 3초 고정(보스 제외)
            {
                var near = AliveNear(player.Pos, Balance.AC_CAGE_RADIUS, false);
                if (near.Count == 0) { Say("반경 안에 아무도 없다"); return false; }
                foreach (var e in near) { e.stun = Mathf.Max(e.stun, Balance.AC_CAGE_STUN); e.boundT = Balance.AC_CAGE_STUN; e.cageUntil = Time.time + Balance.AC_CAGE_STUN; e.atk.Interrupt(); e.vel = Vector3.zero; }
                GroundFx.Play(player.Pos, Balance.AC_CAGE_RADIUS, "fx/fx_bind_", 3, 0.8f);
                Say(name); return true;
            }
            case "원념 두르기": // 업 단계에 따라 공격력 +5/10/15/20%
            {
                int tier = 1 + Mathf.Min(3, ledger.Karma / 10);
                lo.buffDamage = 0.05f * tier; wrathT = Balance.AC_WRATH_SEC; lo.Refresh();
                Say("원념 두르기 +" + (5 * tier) + "%"); return true;
            }
            case "얼룩 타기": lo.buffMove = Balance.AC_STAINRIDE_MOVE; rideT = Balance.AC_STAINRIDE_SEC; lo.Refresh(); Say(name); return true;
            case "깨진 이름 던지기": // 방금 파혼한 혼의 파편을 던진다(근사: 최근 파혼 뒤 일정 시간 안)
            {
                if (Time.time - lastPahonAt > Balance.AC_THROWNAME_WINDOW) { Say("방금 파혼한 혼이 없다"); return false; }
                var near = AliveNear(player.Pos, Balance.AC_SOULFIRE_RANGE, true);
                if (near.Count == 0) { Say("던질 대상이 없다"); return false; }
                int dmg = Mathf.RoundToInt(Balance.AC_THROWNAME_DMG * lo.stats.DamageMult);
                near[0].TakeHit(dmg, (near[0].Pos - player.Pos).normalized, 6f, 0.2f);
                numbers.Spawn(near[0].HeadPosition, dmg, "heavy");
                lastPahonAt = -99f;
                ledger.AddKarma(1);   // 대가: 던진 혼은 업이 1 더 쌓인다(파혼 +1과 합쳐 +2). 엽전은 그대로
                Say(name + " (업 +1 더)"); return true;
            }
            case "검은 갓의 그림자": shadowT = Balance.AC_SHADOW_SEC; Say("파혼 폭발이 무릎 꿇은 혼까지 깨뜨린다"); return true;
        }
        return false;
    }

    // ===== M4: 이름혼·보스·단서 ======================================================
    void SpawnNamedSoul()
    {
        // 플레이어 앞쪽 7m 에서 나타난다 (길 위, 집 밖)
        var at = new Vector3(MapLayout.NamedX, 0, MapLayout.NamedZ);   // 아트 배치표가 정한 자리
        enemies.SpawnNamed(at, "박돌쇠");
        Say("명부에 오른 이름이 나타났다");
    }

    /// <summary>한 판 시작: 마을 어귀에 보스, 마을 곳곳에 단서 3개</summary>
    void SetupNight()
    {
        var naru = enemies.SpawnBoss(new Vector3(MapLayout.BossX, 0, MapLayout.BossZ));
        if (FieldRules.On) ArenaDecor.Make(this, naru, 1);   // 나루터 꾸밈(말뚝·물때 표식·바닥 무늬·달빛)
        if (FieldRules.On)   // 필드: 2호 월화(폐당집 굿판)·3호 서 의원(검은여울 역병막 마당). 가까이 가면 바닥 무늬(BossArena)가 깨어난다
            for (int bid = 2; bid <= Bosses.Count; bid++)
            {
                var bd = Bosses.Get(bid);
                var be = enemies.SpawnBoss(new Vector3(bd.X, 0, bd.Z), bid);
                var arena = new GameObject("BossArena" + bid).AddComponent<BossArena>(); arena.Init(this, be, bd);
            }
        if (FieldRules.On && Act2BossArena.Enabled)   // 2막 보스 넷(?act2=1 검사용): 2막 땅이 깔리면 기본으로 켠다
            for (int bid = 5; bid <= 8; bid++)
            {
                var bd = Bosses.Get(bid);
                var be = enemies.SpawnBoss(new Vector3(bd.X, 0, bd.Z), bid);
                var arena = new GameObject("Act2BossArena" + bid).AddComponent<Act2BossArena>(); arena.Init(this, be, bd);
            }
        if (FieldRules.On && FieldRules.Act3)   // 3막 보스 넷: 땅이 깔려 있으면 선다(금줄이 열리기 전엔 닿을 수 없다)
            for (int bid = 9; bid <= 12; bid++)
            {
                var bd = Bosses.Get(bid);
                var be = enemies.SpawnBoss(new Vector3(bd.X, 0, bd.Z), bid);
                var arena = new GameObject("Act3BossArena" + bid).AddComponent<Act2BossArena>(); arena.Init(this, be, bd);
            }
        cluePos.Clear();
        foreach (var v in clueViews) Destroy(v);
        clueViews.Clear();
        foreach (var cp in FieldRules.On ? new float[0][] : MapLayout.CluePoints())   // 필드에선 단서를 산 사람에게서 얻는다(NpcWorld)
        {
            var p = new Vector3(cp[0], 0, cp[1]);
            cluePos.Add(p);
            var g = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            Destroy(g.GetComponent<Collider>());
            g.transform.position = p + Vector3.up * 0.8f;
            g.transform.localScale = Vector3.one * 0.6f;
            g.GetComponent<Renderer>().sharedMaterial = U.Unlit(ChasaPalette.MemoryRim);   // 보랏빛 구슬 = 기억의 단서
            clueViews.Add(g);
        }
    }

    // ===== 1막 끝: 흑월 1차 → 2막 금줄 해금 (서사 확정 10-25, 규칙은 Core/Act2Gate) =====
    // 1막 보스 셋(나루 영감·월화·서 의원)을 모두 처결한 다음 첫 밤(또는 ② 검은여울에 처음 들어간 뒤 5일째 밤) 무덤골에 흑월이 나타난다.
    // 처결은 없다: 맺힘 50% 에서 사슬을 거두고 "너는 아직 모른다." 한 마디를 남기고 물러난다. 그 밤의 다음 새벽에 두 금줄이 함께 풀린다(싸우지 않았어도).
    readonly HashSet<int> bossDoneIds = new HashSet<int>();   // 처결한 1막 보스 번호(1~3)
    int allDoneDay = -1; bool allDoneAtNight; int enterDay = -1; int act2DoneDay = -1; bool gate3Announced;   // act2DoneDay: 2막 보스 넷을 모두 처결한 하루(3막 금줄은 그 다음 새벽에 풀린다)
    bool heukwolSpawned, heukwolRetreated, gateAnnounced, heukwolWarned; Enemy heukwol; float gateToastT;
    void MarkBossDone(int id)
    {
        if (id < 1 || id > 12 || id == 4 || clock == null || !bossDoneIds.Add(id)) return;
        if (id <= 2 && !lo.gear.FirstRingBossDone) { lo.gear.FirstRingBossDone = true; lo.lastDrop = "새 장비 자리가 열렸다: 갓 · 띠"; lo.lastDropT = 6f; }   // 1막 보스 처결 뒤 갓·띠 자리(기획 성장 표)
        if (id <= 3 && bossDoneIds.Contains(1) && bossDoneIds.Contains(2) && bossDoneIds.Contains(3) && allDoneDay < 0) { allDoneDay = clock.Day; allDoneAtNight = clock.Phase == ClockPhase.Night; }
        if (id >= 5 && bossDoneIds.Contains(5) && bossDoneIds.Contains(6) && bossDoneIds.Contains(7) && bossDoneIds.Contains(8) && act2DoneDay < 0) act2DoneDay = clock.Day;   // 2막 마지막 일
    }
    void TickHeukwol()
    {
        if (!FieldRules.On || !FieldRules.Act2 || clock == null) return;
        if (allDoneDay < 0 && (Application.absoluteURL ?? "").Contains("hk=")) { bossDoneIds.Add(1); bossDoneIds.Add(2); bossDoneIds.Add(3); allDoneDay = clock.Day; allDoneAtNight = clock.Phase == ClockPhase.Night; }   // 검사용 ?hk=1: 1막 보스 셋을 이미 처결한 것으로 친다(흑월 1차를 바로 본다)
        if (!lo.gear.Act2Entered && FieldRules.Act2Open && player.Pos.z > FieldRules.Size + 4f) { lo.gear.Act2Entered = true; lo.lastDrop = "새 장비 자리가 열렸다: 신 · 노리개 2"; lo.lastDropT = 6f; }   // 2막 땅에 첫 발 — 신·노리개 둘째 자리
        if (enterDay < 0 && FieldZones.CurrentName == "검은여울") enterDay = clock.Day;   // ② 검은여울 첫 진입(5일 안전장치의 기준)
        int hn = Act2Gate.HeukwolNight(allDoneDay, allDoneAtNight, enterDay);
        bool open = FieldRules.Act2Open || clock.Day >= Act2Gate.OpenDay(allDoneDay, allDoneAtNight, enterDay);
        if (open && !FieldRules.Act2Open) { FieldRules.Act2Open = true; }
        if (open && !gateAnnounced && hn != int.MaxValue) { gateAnnounced = true; Say("두 금줄이 풀렸다 — 붉은재 고개길 · 쇳골 산길"); }
        // 3막 금줄 셋(강둑길·큰길·갱도 출구): 2막 마지막 일 다음 새벽에 함께 풀린다(서사·기획 act3_map unlock)
        if (!FieldRules.Act3Open && FieldRules.Act3 && act2DoneDay >= 0 && clock.Day >= act2DoneDay + 1) FieldRules.Act3Open = true;
        if (FieldRules.Act3Open && !gate3Announced && act2DoneDay >= 0) { gate3Announced = true; Say("세 금줄이 풀렸다 — 강둑길 · 큰길 · 갱도 출구"); }
        if (FieldRules.Act3 && !FieldRules.Act3Open && gateToastT <= 0f && ((player.Pos.x < 4f && player.Pos.z < FieldRules.Size) || (player.Pos.x > 764f && player.Pos.z > FieldRules.Size))) { gateToastT = 8f; Say(Act2Gate.BlockedLine); }
        // 금줄 앞: 열리기 전에는 한 줄 안내
        gateToastT -= Time.deltaTime;
        if (!open && player.Pos.z > FieldRules.Size - 4f && player.Pos.x < 768f && gateToastT <= 0f) { gateToastT = 8f; Say(Act2Gate.BlockedLine); }
        // 예고: 흑월이 나타날 날 해질녘 서낭당 당할미의 한 줄(서사 B-04 낮 단서의 혼잣말 — 단서로 세지 않는다)
        if (hn != int.MaxValue && clock.Day == hn && !heukwolWarned && clock.Phase == ClockPhase.Dusk) { heukwolWarned = true; Say("당할미: “예전 차사님은 갓끈이 붉었는데…”"); }
        // 등장: 그 밤이 되면 무덤골에
        if (hn != int.MaxValue && clock.Day == hn && !heukwolSpawned && clock.Phase == ClockPhase.Night)
        {
            heukwolSpawned = true;
            var bd = Bosses.Get(4);
            heukwol = enemies.SpawnBoss(new Vector3(bd.X, 0, bd.Z), 4);
            Say("고개 위에 갓끈 검은 차사가 서 있다");
            if ((Application.absoluteURL ?? "").Contains("hk=2")) heukwol.soul.Maedhim = (int)(heukwol.soul.MaedhimMax * 0.52f);   // 검사용 ?hk=2: 맺힘 52% 로 시작 → 몇 대만 쳐도 절반을 넘어 물러나는 장면(너는 아직 모른다·새벽 금줄 해제)이 나온다
        }
        if (heukwol != null)
        {
            if (heukwol.soul.MaedhimMax > 0 && heukwol.soul.Maedhim <= heukwol.soul.MaedhimMax * 0.5f)   // 맺힘 50% — 물러난다
            {
                Say("흑월 — “너는 아직 모른다.”");
                RemoveEnemy(heukwol); heukwol = null; heukwolRetreated = true;
            }
            else if (clock.Phase == ClockPhase.Dawn && clock.Day > hn) { RemoveEnemy(heukwol); heukwol = null; heukwolRetreated = true; }   // 싸우지 않았으면 새벽에 사라진다
        }
    }
    void RemoveEnemy(Enemy e) { if (e == null) return; enemies.list.Remove(e); Destroy(e.gameObject); }

    /// <summary>한 줄 꿰기: 묶은 둘 중 하나를 천도하고 다른 하나를 파혼하면 둘 다 보상 +5%(소수점 누적). 같은 종류만 하면 아무 일도 없다</summary>
    void TieProgress(Enemy who, int kind)
    {
        if (tiedA == null || (who != tiedA && who != tiedB)) return;
        tiedKinds |= kind;
        if (tiedKinds != 3) return;
        tiedA = tiedB = null; tiedKinds = 0;
        coinFrac += Balance.PAHON_COIN * 0.05f;
        neokFrac += Balance.TENDO_NEOK * 0.05f;
        int n = Mathf.FloorToInt(neokFrac); neokFrac -= n; if (n > 0) { ledger.Neok += n; growth.AddNeok(n); }
        Say("한 줄 꿰기 보상");
    }
    float neokFrac;

    // ---- 처결 대기 긴장음: 남은 시간 비율에 맞춰 똑딱 간격이 1.0초 → 0.15초로 줄어든다(사운드팀 표) ----
    float waitTickT, waitPulseT; Enemy waitFor; bool waitFinalDone;
    void TickWaitTick(float dt)
    {
        Enemy e = enemies.NearestKneeling(player.Pos, 14f);
        if (e != waitFor) { waitFor = e; waitFinalDone = false; waitTickT = 0.3f; }   // 새 대기 혼이 생기면 처음부터
        if (e == null || Casting || introFrozen) return;   // 천도 시전 중엔 멈춤, 첫 혼(튜토리얼)엔 틀지 않는다
        var s = e.soul;
        if (s.WaitTotal <= 0f) return;
        // 처결 대기 맥박(아트 wait_pulse_*): 남은 2초부터 0.5초마다 발밑 고리가 한 번씩 뛴다. 소리 예고와 같이 보이게
        if (s.WaitLeft <= 2f)
        {
            waitPulseT -= dt;
            if (waitPulseT <= 0f)
            {
                waitPulseT = 0.5f;
                StripFx.Flat(s.Kind == SoulKind.Fresh ? "wait_pulse_fresh" : s.Kind == SoulKind.Year ? "wait_pulse_day" : "wait_pulse_old", 4, 0.5f, e.Pos, 2.2f);
            }
        }
        else waitPulseT = 0f;
        if (!waitFinalDone && s.WaitLeft <= 1.5f) { waitFinalDone = true; Sfx.Play("sfx.wait.final"); }   // 마지막 1.5초 경고
        waitTickT -= dt;
        if (waitTickT > 0f) return;
        float ratio = Mathf.Clamp01(s.WaitLeft / s.WaitTotal);
        waitTickT = Mathf.Lerp(0.15f, 1.0f, ratio);
        // 나이가 많은 혼일수록 낮고 무거운 똑딱
        Sfx.Play(s.Kind == SoulKind.Fresh ? "sfx.wait.tick.fresh" : s.Kind == SoulKind.Year ? "sfx.wait.tick.year" : "sfx.wait.tick.old");
    }

    void TickClues()
    {
        for (int i = cluePos.Count - 1; i >= 0; i--)
        {
            var p = cluePos[i];
            if (new Vector2(player.Pos.x - p.x, player.Pos.z - p.z).magnitude > Balance.CLUE_PICK_RADIUS) continue;
            night.PickClue();
            Destroy(clueViews[i]); clueViews.RemoveAt(i); cluePos.RemoveAt(i);
            Sfx.Play("sfx.clue");
            Say("단서 " + night.Clues + "/" + Balance.BOSS_CLUES_REQUIRED);
        }
    }

    // ===== M1: 맞음·체력·쓰러짐 ======================================================
    /// <summary>적 공격이 명중했을 때. 무적 시간이면 무시. 천도 캐스팅 중이면 끊긴다 (무방비의 대가)</summary>
    /// <summary>보스 바닥 무늬(BossArena)에 맞았을 때. 피하기 무적이면 false(안 맞음)</summary>
    float areaMult = 1f;   // 이번 보스 장판 한 번의 피해 배율(약해진 파도 = 0.5)
    public bool BossAreaHit(Enemy by, float mult = 1f)
    {
        if (ledger.Dead || night.Over) return false;
        float hp = ledger.Hp; areaMult = mult; OnPlayerHit(by); areaMult = 1f;
        return ledger.Hp < hp || godMode;
    }

    void OnPlayerHit(Enemy by)
    {
        if (ledger.Dead || night.Over || !player.Hurt()) return;
        // 상복 자락: 천도 시전 중에 맞으면 피해가 줄어든다
        int incoming = Casting ? Mathf.Max(1, Mathf.RoundToInt(by.damage * lo.stats.CastDamageTakenMult * weather.Fx.CastHit / Balance.WEATHER_CLEAR_CAST_HIT)) : by.damage;   // 안개: 천도 중 맞는 피해 ×(0.85/0.75)
        if (areaMult != 1f) incoming = Mathf.Max(1, Mathf.RoundToInt(incoming * areaMult));
        // 첫 5분(시계 정지 중)은 배우는 시간: 보스가 아닌 혼의 피해를 절반으로(처음 1분을 못 버티고 쓰러지던 것 방지)
        if (introFrozen && !by.soul.Boss) incoming = Mathf.Max(1, Mathf.RoundToInt(incoming * Balance.INTRO_DAMAGE_MULT));
        sinceHit = 0f;
        Hint(HintEvent.FirstHurt);
        guide.Complete("dodge");   // 맞아도 피하기 안내는 닫힌다(기획)
        Sfx.Play("sfx.player.hurt");
        int dealt = godMode ? 0 : ledger.TakeDamage(incoming);
        numbers.Spawn(player.Pos + Vector3.up * 2f, dealt, "heavy");
        feel.AddShake(Balance.TRAUMA_PLAYER_HIT);
        vignetteT = 0.15f;
        feel.HitStop(3);
        if (Casting)
        {
            castTarget.soul.CancelSending();   // 혼은 무릎 꿇은 상태로 돌아간다(대기 시간은 그대로 흐름)
            EndCast();
            Say("시전이 끊겼다!");
        }
        if (ledger.Dead) { Say("쓰러졌다"); night.Tick(night.TimeLeft + 1f); }   // 쓰러짐 = 동트기와 같은 실패(추가 수확분 상실)
    }

    /// <summary>쓰러진 뒤 한 판을 처음부터. 체력·적·얼룩을 되돌리고 장부(수확)는 결과 화면(M5)에서 다룬다</summary>
    void RestartNight()
    {
        night = new NightRun(); settled = false; ResetRound(); sinceHit = 99f;
        toastT = 0f; played = true; enemies.graceT = Balance.NIGHT_GRACE;   // 지난 밤 안내 지우기(QA B3), 새 밤 유예(QA B1)
        night.Clues = dayScreen.BossCluesHave;   // 낮에 얻은 단서는 사라지지 않고 밤으로 이어진다
        if (dayScreen.Pack.Dawn > 0) { dayScreen.Pack.Dawn--; night.WarnTime += Balance.SHOP_DAWN_EARLY; }   // 새벽 부적: 경고가 일찍
    }

    /// <summary>자동 플레이 봇 전용: 결과 화면이면 Space 대신 다시 시작. 했으면 true</summary>
    public bool BotRestart() { if (!night.Over || overT <= 1.2f) return false; RestartNight(); return true; }

    /// <summary>결과 화면에서 낮으로. 어젯밤 이름혼을 천도했으면 장례가 열린다</summary>
    void StartDay()
    {
        inDay = true;
        dayScreen.Begin(namedTendoed);
        namedTendoed = false;
    }

    void ResetRound()
    {
        ledger.ResetHp();
        stains.Clear();
        player.Pos = Vector3.zero;
        foreach (var e in enemies.list) if (!e.extra) e.Respawn(Vector3.zero + new Vector3(8f + Random.value * 4f, 0, 8f + Random.value * 4f));
        var extras = enemies.list.FindAll(x => x.extra);
        foreach (var e in extras) { enemies.list.Remove(e); Destroy(e.gameObject); }
        enemySpawnPause = 0f;
        SetupNight();
    }

    public void Say(string s) { toast = s; toastT = 1.5f; }

    // ===== 매 프레임 ===============================================================
    public void Tick(float dt, float realDt)
    {
        toastT -= realDt;   // 안내 글자는 창이 열려 있어도 사라진다(QA B3)
        if (CharacterPanel.Open || SettingsPanel.Open) return;   // 캐릭터 창·설정이 열려 있으면 세계가 멈춘다
        if (inDay)
        {
            dayScreen.Tick(realDt);
            if (dayScreen.WantsNight) { inDay = false; RestartNight(); }   // 해 넘기기 → 새 밤
            return;
        }
        if (!played && (Input.anyKeyDown || Input.GetMouseButtonDown(0) || Input.touchCount > 0)) { played = true; enemies.graceT = Balance.NIGHT_GRACE; }
        enemies.holdFire = !played;
        UpdateInteract(dt);
        player.judgeStance = !Casting && enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE) != null;   // 무릎 꿇은 혼 앞: 주인공 Judge 자세
        if (!night.Over) HandleKeys();   // 결과 화면에서는 무기 교체·공격 키가 먹지 않는다(QA B4)
        if (!night.Over) overT = 0f;
        if (night.Over)
        {
            // 한 번만 정산: 동이 터서 끝났으면 흩어진 추가 수확분(넋)을 장부에서 뺀다. 몫과 성장(기억·품계)은 그대로.
            if (!settled) { settled = true; dayScreen.BossCluesHave = Mathf.Max(dayScreen.BossCluesHave, night.Clues);   // 밤에 주운 단서도 남는다
                ledger.Neok = Mathf.Max(0, ledger.Neok - night.LostNeok); ledger.Coin = Mathf.Max(0, ledger.Coin - night.LostCoin); }
            // 결과 화면: Space(또는 버튼)로 다시 시작. 단, 결과가 뜬 뒤 1.2초 동안은 Space 를 무시한다 —
            // Space 가 '피하기'이기도 해서, 쓰러지는 순간 연타하던 피하기가 곧바로 다시 시작으로 이어지는 것을 막는다(QA)
            overT += realDt;
            if (overT > 1.2f && Input.GetKeyDown(KeyCode.Space)) RestartNight();
            if (Demo.Day && Input.GetKeyDown(KeyCode.D)) StartDay();
            return;
        }
        TickCutscenes(dt);
        if (clock == null) night.Tick(dt);     // 옛 방식: 밤 타이머. 필드에선 시한이 없다(시계가 흐를 뿐)
        else TickClock(dt);
        TickClues();
        TickAutoSave(realDt);
        if (camps != null) { camps.GhostMult = weather.Fx.GhostMult; camps.Tick(dt, player.Pos); }   // 필드: 가까운 군집만 세운다
        enemySpawnPause = Mathf.Max(0f, enemySpawnPause - dt);
        TickActives(dt);   // 도술이 남기는 짧은 상태(버프·느림·타이머)
        enemies.spawnPaused = enemySpawnPause > 0f || (Casting && castTarget.soul.Boss);   // 보스 천도 중·직후엔 잡몹이 새로 나오지 않는다
        // 귀환: 서낭당 위에 서면 즉시. 단 출발 직후(몫을 하나도 못 채움)에는 자동 귀환하지 않는다 — 밤을 시작도 못 하고 끝나는 것 방지
        float toShrine = new Vector2(player.Pos.x, player.Pos.z).magnitude;
        if (clock == null && night.QuotaDone && night.TryReturn(toShrine)) Say("귀환했다!");   // 필드엔 강제 귀환이 없다
        chainLeft = Mathf.Max(0f, chainLeft - dt);
        Sfx.NightNow = clock != null && clock.Phase == ClockPhase.Night;
        if (clock != null) TideWater.WorldMinutes = Tide.TotalMinutes(clock.Day, clock.Minutes);   // 썰물·밀물 시계
        weather.state.Override = WeatherRules.Parse(cuts.SceneWeather);   // 서사 컷이 정한 날씨가 무작위보다 우선
        float wxSlow; int wxDrain;
        weather.Tick(clock, player.Pos, enemies, dt, godMode, out wxSlow, out wxDrain, t => ui?.Hud.Toasts.Add(t));
        stains.Tick(dt * weather.Fx.StainMult);   // 비 오는 밤: 얼룩이 절반만 오래간다
        if (wxDrain > 0 && !ledger.Dead) { ledger.TakeDamage(wxDrain); if (ledger.Dead) { Say("쓰러졌다"); night.Tick(night.TimeLeft + 1f); } }   // 역병 안개: 서 있으면 체력이 준다
        flashA = Mathf.Max(0f, flashA - realDt * 2.2f);
        vignetteT = Mathf.Max(0f, vignetteT - realDt);
        sinceHit += dt;
        ledger.Regen(dt, toShrine <= Balance.SHRINE_RADIUS, sinceHit);   // 서낭당 안: 빠른 회복 / 밖: 맞지 않으면 천천히
        player.speedMult = 1f - WeatherRules.CombineSlow(wxSlow, stains.IsOnStain(player.Pos.x, player.Pos.z) ? Balance.STAIN_SLOW : 0f);   // 얼룩 위 -20%, 역병 안개 -20%, 겹쳐도 최대 -30%

        if (Casting)
        {
            if (castTarget.soul.State != SoulState.Sending) EndCast();   // 혼이 사라졌다
            else
            {
                castT += dt;
                if (castT >= castTotal) FinishTendo();
            }
        }
        // 시야 연출: 캐스팅 중 1 쪽으로, 아니면 0 쪽으로 TENDO_VISION_BLEND(0.2초) 동안 이동
        float target = Casting ? 1f : 0f;
        visionP = Mathf.MoveTowards(visionP, target, realDt / Mathf.Max(0.01f, Balance.TENDO_VISION_BLEND));
        UpdateStainViews();
    }

    /// <summary>컷신을 흘리고, 보스 구역 첫 진입이면 등장 컷을 건다. 잠금·적 멈춤을 반영한다</summary>
    int bossOutcome;             // 나루 영감 처결 결과: 1 천도 · 2 파혼 (낮 풍경이 바뀐다)
    bool sceneryAdded;
    bool openingStarted;
    int pahonOrTendo;            // 박돌쇠 처결 결과: 0 안 함 · 1 천도 · 2 파혼
    bool funeralShown;
    public int PahonOrTendo { get { return pahonOrTendo; } }   // 박돌쇠 결과: 1 천도 · 2 파혼 · 0 아직
    // 1막 장례(서사 funerals_act1): 처결한 혼의 집 앞에 다음 낮 처음 다가갈 때 하루 한 번. 혼 이름 → 컷 이름 색인
    [System.Serializable] class FunIdx { public string soul, id; }
    [System.Serializable] class FunFile { public FunIdx[] funerals; }
    readonly Dictionary<string, string> funeralCut = new Dictionary<string, string>();
    readonly Dictionary<string, int> funeralPending = new Dictionary<string, int>();   // 혼 → 결과(1 천도 · 2 파혼)
    readonly HashSet<string> funeralDone = new HashSet<string>();
    readonly Dictionary<string, int> funeralBorn = new Dictionary<string, int>();   // 혼 → 처결한 날(낮에 처결했으면 그 낮이 끝나도 다음 낮까지 남기려고)
    int funeralDay = -1;                                  // 장례를 본 날(하루 한 번)
    public Vector3 FuneralPos = new Vector3(214f, 0f, 62f);   // 지금 장례가 열린 마당(카메라 'funeral' 대상)
    // 기획 funeral_targets_act1.json: 혼마다 대문(gate)·멈춘 것·다시 움직이는 것·노제·사라지는 자리 좌표
    [System.Serializable] class FPt { public float[] xy; }
    [System.Serializable] class FTarget { public string name; public float[] gate; public FPt stop_object, restart_object, noje, exit; }
    [System.Serializable] class FTargetFile { public FTarget[] funerals; }
    readonly Dictionary<string, FTarget> funeralTargets = new Dictionary<string, FTarget>();
    bool dogHome;                                         // 칠복 장례 다음 새벽부터 누렁이가 개집(191,75)으로 돌아와 머문다
    /// <summary>누렁이 동선(기획 kennel_S004): 처결 전 둑 어귀(250,100)·밤엔 칠복 혼 자리 근처 / 장례 날 (205,86)에서 나타나 행렬을 따라 (236,98)로 사라짐 / 다음 새벽부터 개집 / 파혼·처결 못 함이면 둑 어귀 그대로</summary>
    void DogTick()
    {
        bool done = funeralDone.Contains("칠복");
        Vector3 p = Vector3.zero; bool show = true;
        if (dogHome) p = new Vector3(191f, 0f, 75f);
        else if (cuts.Active && cuts.CurId == "FUN-S004_TENDO") { float k = Mathf.Clamp01((cuts.CurTime - 25f) / 20f); show = cuts.CurTime >= 25f; p = Vector3.Lerp(new Vector3(205f, 0f, 86f), new Vector3(236f, 0f, 98f), k); }
        else if (done) show = false;   // 장례가 끝난 날: 사라진 채로 다음 새벽을 기다린다
        else if (clock != null && clock.Phase == ClockPhase.Night && !funeralPending.ContainsKey("칠복") && !funeralNoneShown.Contains("칠복")) p = new Vector3(204f, 0f, 87.5f);
        else p = new Vector3(250f, 0f, 100f);
        interactables.SetDog(show, show ? p : Vector3.zero);
    }
    bool parkUnjudged;                                    // 박돌쇠 '처결 못 함' 확정(대기 초과·동틀녘·첫 5분 10분 안전장치)
    string funeralNow;                                    // 지금 열린 장례의 혼 이름(카메라 좌표 종류를 고르는 데 쓴다)
    readonly HashSet<string> funeralNoneShown = new HashSet<string>();   // '처결 못 함' 장면을 이미 본 혼(한 혼에 한 번)
    ClockPhase lastFunPhase = ClockPhase.Night;
    static Vector3 V(float[] xy) { return xy != null && xy.Length >= 2 ? new Vector3(xy[0], 0f, xy[1]) : Vector3.zero; }
    /// <summary>장례 카메라 좌표: kind = stop · restart · gate · noje · exit. 혼 데이터가 없으면 지금 마당</summary>
    public Vector3 FuneralPoint(string kind)
    {
        FTarget t;
        if (funeralNow == null || !funeralTargets.TryGetValue(funeralNow, out t)) return FuneralPos;
        switch (kind)
        {
            case "stop": return t.stop_object != null ? V(t.stop_object.xy) : FuneralPos;
            case "restart": return t.restart_object != null ? V(t.restart_object.xy) : FuneralPos;
            case "noje": return t.noje != null ? V(t.noje.xy) : FuneralPos;
            case "exit": return t.exit != null ? V(t.exit.xy) : FuneralPos;
            default: return V(t.gate);
        }
    }
    /// <summary>처결 대기까지 갔다가 E·R 을 못 받고 흩어졌다(대기 초과·동틀녘): 장례 대상이면 다음 낮 '처결 못 함'(한 혼에 한 번)</summary>
    void MarkUnjudged(Enemy e)
    {
        string n = e.soul.Name;
        if (n == "박돌쇠" && pahonOrTendo == 0) parkUnjudged = true;   // 박돌쇠는 첫 세션 장면(FUNERAL_NONE)이 따로 있어 표시만 한다
        if (n == null || !funeralCut.ContainsKey(n) || funeralDone.Contains(n) || funeralNoneShown.Contains(n) || funeralPending.ContainsKey(n)) return;
        funeralPending[n] = 3; funeralBorn[n] = clock != null && clock.Phase == ClockPhase.Day ? clock.Day : -1;
    }
    public bool FuneralDoneHas(string soul) { return funeralDone.Contains(soul); }
    void LoadFuneralIndex()
    {
        var ta = Resources.Load<TextAsset>("Data/funerals_index"); if (ta == null) return;
        var f = JsonUtility.FromJson<FunFile>(ta.text); if (f == null || f.funerals == null) return;
        foreach (var x in f.funerals) funeralCut[x.soul] = x.id;
        var tt = Resources.Load<TextAsset>("Data/funeral_targets_act1");
        if (tt != null) { var tf = JsonUtility.FromJson<FTargetFile>(tt.text); if (tf != null && tf.funerals != null) foreach (var x in tf.funerals) funeralTargets[x.name] = x; }
        if (FieldRules.Act2)   // 2막 장례 좌표는 기획 act2_map.json 의 funerals(이름·대문·멈춘 것·다시 움직이는 것·노제·사라지는 자리)
        {
            var t2 = Resources.Load<TextAsset>("Data/act2_map");
            if (t2 != null) { var f2 = JsonUtility.FromJson<FTargetFile>(t2.text); if (f2 != null && f2.funerals != null) foreach (var x in f2.funerals) funeralTargets[x.name] = x; }
        }
        if (FieldRules.Act3)   // 3막 장례 좌표는 기획 act3_map.json 의 funerals(모양이 2막과 같다)
        {
            var t3 = Resources.Load<TextAsset>("Data/act3_map");
            if (t3 != null) { var f3 = JsonUtility.FromJson<FTargetFile>(t3.text); if (f3 != null && f3.funerals != null) foreach (var x in f3.funerals) funeralTargets[x.name] = x; }
        }
    }
    /// <summary>장례 컷의 조건 글자(서사 condition). 지금은 1호 결과만 안다(3호 결과는 아직 따로 세지 않아 false)</summary>
    bool FuneralCond(string c) { return c == "B-01 천도함" ? bossOutcome == 1 : false; }
    /// <summary>제사를 지켜보기 전에는 장례 대상 이름혼의 지도 표식을 숨긴다(기획: 지켜보면 그 혼의 오늘 밤 자리가 명부에 표시된다). 윤 소사·연이는 첫 세션 흐름이라 처음부터 보인다</summary>
    public bool NamedMarkerHidden(string name) { return name != null && name != "윤 소사" && name != "연이" && funeralCut.ContainsKey(name) && (npcs == null || !npcs.JesaSeen.Contains(name)) && (npcs == null || npcs.HasHome(name)); }   // 제사 자리 데이터가 없는 이름혼(2막)은 숨기지 않는다
    public const float FuneralX = 214f, FuneralZ = 62f;   // 박돌쇠 대장간 문 앞(아트 확정: 이름혼 자리 215.6, 62.2)
    // ===== 저장·불러오기 (규칙은 Core/SaveGame.cs, 저장소는 SaveStore) ==================
    bool loadChecked; float autoSaveT = 30f;
    public string SaveNote = "";   // 설정 화면에 보일 마지막 저장·불러오기 결과 글자

    /// <summary>지금 상태를 저장한다. 필드에서만(옛 한 판 모드엔 저장할 세계가 없다). 성공하면 true</summary>
    public bool SaveGameNow()
    {
        if (clock == null || ledger.Dead) return false;
        var s = SaveGame.Capture(growth, ledger, lo.gear, clueBook);
        System.Array.Copy(lo.wallet.Amount, s.Wallet, 5);   // 빛깔별 넋 주머니
        foreach (var sl in lo.sealBag) s.SealBag.Add(sl.Text);
        s.X = player.Pos.x; s.Z = player.Pos.z; s.ClockDay = clock.Day; s.ClockMinutes = clock.Minutes;
        s.BossOutcome = bossOutcome; s.NamedOutcome = pahonOrTendo; s.OpeningSeen = openingStarted; s.FuneralShown = funeralShown; s.Weapon = lo.weapon; s.Other = lo.other;
        s.WeatherNow = weather.Snapshot(); s.PlagueEased = weather.state.PlagueEased;
        s.Picked.Add("cp:" + cardPicks);   // 도술 카드 몇 번 골랐나
        if (npcs != null) foreach (var js in npcs.JesaSeen) s.Picked.Add("jesa:" + js);   // 제사를 지켜본 혼
        foreach (var kv in funeralPending) s.Picked.Add("fp:" + kv.Key + ":" + kv.Value); foreach (var fd in funeralDone) s.Picked.Add("fd:" + fd); s.Picked.Add("fday:" + funeralDay); if (parkUnjudged) s.Picked.Add("pu:1"); foreach (var bi in bossDoneIds) s.Picked.Add("bd:" + bi); if (act2DoneDay >= 0) s.Picked.Add("a2d:" + act2DoneDay); if (allDoneDay >= 0) s.Picked.Add("ad:" + allDoneDay + ":" + (allDoneAtNight ? 1 : 0)); if (enterDay >= 0) s.Picked.Add("ed:" + enterDay); if (heukwolSpawned) s.Picked.Add("hks:1"); if (gateAnnounced) s.Picked.Add("ga:1"); if (dogHome) s.Picked.Add("dh:1"); foreach (var ns in funeralNoneShown) s.Picked.Add("fn:" + ns); foreach (var kv in funeralBorn) s.Picked.Add("fb:" + kv.Key + ":" + kv.Value);   // 장례 진행
        if (interactables != null) { s.Picked.AddRange(interactables.Picked); foreach (var kv in interactables.HerbTaken) s.HerbTaken.Add(kv.Key + ":" + kv.Value); s.Herbs = interactables.Herbs; }
        return SaveStore.Write(SaveGame.Serialize(s));
    }

    /// <summary>저장된 것을 불러온다. 없거나 깨졌으면 false(게임은 그대로 계속). 적·얼룩은 새로 시작</summary>
    public bool LoadGameNow()
    {
        if (clock == null) return false;
        var s = SaveGame.Deserialize(SaveStore.Read());
        if (s == null) return false;
        if (Casting) EndCast();
        SaveGame.Apply(s, growth, ledger, lo.gear, clueBook);
        System.Array.Copy(s.Wallet, lo.wallet.Amount, 5);
        lo.sealBag.Clear(); foreach (var t in s.SealBag) { var sl = Seal.Parse(t); if (sl != null) lo.sealBag.Add(sl); }
        lo.Refresh();
        lo.weapon = s.Weapon; lo.other = s.Other == s.Weapon ? (s.Weapon == WeaponId.Chain ? WeaponId.Mace : WeaponId.Chain) : s.Other;
        RefreshGrowth();
        ledger.Hp = Mathf.Clamp(s.Hp, 1, ledger.MaxHp);
        clock.Set(s.ClockDay, s.ClockMinutes);
        funeralPending.Clear(); funeralDone.Clear(); funeralNoneShown.Clear(); funeralBorn.Clear(); parkUnjudged = false; dogHome = false; funeralDay = -1;
        bossDoneIds.Clear(); allDoneDay = -1; allDoneAtNight = false; enterDay = -1; act2DoneDay = -1; gate3Announced = false; heukwolSpawned = false; heukwolRetreated = false; gateAnnounced = false; heukwolWarned = false; heukwol = null;
        cardPicks = 0; cardPicksLoaded = false;
        foreach (var pk in s.Picked)
        {
            if (pk.StartsWith("cp:")) { int.TryParse(pk.Substring(3), out cardPicks); cardPicksLoaded = true; }
            else if (pk.StartsWith("fd:")) funeralDone.Add(pk.Substring(3));
            else if (pk == "pu:1") parkUnjudged = true;
            else if (pk == "dh:1") dogHome = true;
            else if (pk.StartsWith("bd:")) { int bi; if (int.TryParse(pk.Substring(3), out bi)) bossDoneIds.Add(bi); }
            else if (pk.StartsWith("ad:")) { var q = pk.Split(':'); int d0; if (q.Length == 3 && int.TryParse(q[1], out d0)) { allDoneDay = d0; allDoneAtNight = q[2] == "1"; } }
            else if (pk.StartsWith("ed:")) int.TryParse(pk.Substring(3), out enterDay);
            else if (pk.StartsWith("a2d:")) int.TryParse(pk.Substring(4), out act2DoneDay);
            else if (pk == "hks:1") { heukwolSpawned = true; heukwolRetreated = true; heukwolWarned = true; }   // 이미 나타났던 밤: 다시 나오지 않는다
            else if (pk == "ga:1") gateAnnounced = true;
            else if (pk.StartsWith("fn:")) funeralNoneShown.Add(pk.Substring(3));
            else if (pk.StartsWith("fb:")) { int c = pk.LastIndexOf(':'); int o; if (c > 3 && int.TryParse(pk.Substring(c + 1), out o)) funeralBorn[pk.Substring(3, c - 3)] = o; }
            else if (pk.StartsWith("fday:")) int.TryParse(pk.Substring(5), out funeralDay);
            else if (pk.StartsWith("fp:")) { int c = pk.LastIndexOf(':'); int o; if (c > 3 && int.TryParse(pk.Substring(c + 1), out o)) funeralPending[pk.Substring(3, c - 3)] = o; }
        }
        if (!cardPicksLoaded && growth.Learned.Count > 0) cardPicks = DosulCards.Rounds;   // 카드 이전의 옛 저장: 이미 도술이 있으니 카드는 건너뛴다
        DosulCards.Open = false; if (ui != null) ui.Hud.CardNames = null;
        if (npcs != null) { npcs.JesaSeen.Clear(); foreach (var pk in s.Picked) if (pk.StartsWith("jesa:")) npcs.JesaSeen.Add(pk.Substring(5)); }
        if (interactables != null) { interactables.Restore(s.Picked, s.HerbTaken, s.Herbs); foreach (var sp in interactSpots) sp.Done = false; }   // 주운 것은 Active 가 id 로 걸러 준다
        weather.Restore(s.WeatherNow, s.PlagueEased, clock);   // 날씨도 그대로(불러오자마자 다시 굴리지 않는다)
        bossOutcome = s.BossOutcome; pahonOrTendo = s.NamedOutcome; openingStarted = true; funeralShown = s.FuneralShown; sceneryAdded = false;
        player.CommandStop(); player.Pos = new Vector3(s.X, 0f, s.Z);
        if (onTeleport != null) onTeleport(player.Pos);   // 카메라가 날아오지 않고 곧바로 따라가게
        sinceHit = 99f;
        return true;
    }

    /// <summary>처음 한 번: 저장이 있으면 이어서 시작(주소에 new 가 있으면 무시). 오프닝 컷보다 먼저</summary>
    void TryAutoLoad()
    {
        string u = (Application.absoluteURL ?? "").ToLowerInvariant();
        if (u.Contains("new=1") || u.Contains("?new") || u.Contains("&new")) return;
        if (SaveStore.Exists && LoadGameNow()) Say("이어서 시작했다");
    }

    /// <summary>45초마다 안전할 때(적·시전·컷 없음) 자동 저장</summary>
    void TickAutoSave(float realDt)
    {
        autoSaveT -= realDt;
        if (autoSaveT > 0f) return;
        autoSaveT = 45f;
        if (clock == null || !played || Casting || cuts.Active || ledger.Dead || AnyEnemyNear(20f)) return;
        if (SaveGameNow()) Sfx.Play("sfx.ui.save.auto");
    }

    void TickCutscenes(float dt)
    {
        if (!loadChecked && FieldRules.On && clock != null) { loadChecked = true; TryAutoLoad(); }
        // 오프닝(검은 화면 → 서낭당 고개에서 깨어남): 게임을 처음 켠 필드에서 한 번
        if (!openingStarted && FieldRules.On && clock != null)
        {
            openingStarted = true;
            player.CommandStop();
            cuts.Play("OPENING", true);
        }
        // 나루 풍경: 보스를 처결한 뒤의 낮에 물막이 골 나루 곁에 결과가 보인다 (천도: 배가 묶임·순임이 줄배 / 파혼: 판자 조각과 검은 물)
        if (npcs != null && bossOutcome != 0 && !sceneryAdded && clock != null && clock.Phase == ClockPhase.Day)
        {
            sceneryAdded = true;
            var at = new Vector3(FieldRules.BossX - 4f, 0f, FieldRules.BossZ);
            npcs.AddScenery(at, bossOutcome == 1 ? "나룻배가 묶여 있다. 순임이 줄배를 맨다." : "판자 조각이 떠 있다. 물이 검다.", 1);
        }
        // 박돌쇠 장례: 처결한 다음 낮, 그 집(대장간) 앞에 처음 다가갈 때 한 번(서사 확정). 천도 70초 / 처결 못 함 20초 / 파혼은 조등만(아무 일 없음, 컷 없음)
        if (clock != null && clock.Phase == ClockPhase.Day && !funeralShown && openingStarted && !cuts.Active)
        {
            if (pahonOrTendo == 2 || (pahonOrTendo == 0 && !parkUnjudged)) funeralShown = pahonOrTendo == 2;   // 파혼: 일어나는 일이 없다. 처결 못 함(대기 초과·동틀녘·10분 안전장치)이 아니면 "아직"이라 장면 없음
            else if (new Vector2(player.Pos.x - FuneralX, player.Pos.z - FuneralZ).magnitude < 14f)
            {
                funeralShown = true; funeralDay = clock.Day; FuneralPos = new Vector3(FuneralX, 0f, FuneralZ);
                cuts.Play(pahonOrTendo == 1 ? "FUNERAL_TENDO" : "FUNERAL_NONE");
            }
        }
        // 1막 장례(기획 funeral-rules-act1): 다음 낮 14분 안에 그 집 대문 20m 안으로 처음 들어갈 때 시작, 못 보고 낮이 지나면 사라짐. 하루 한 번.
        // 천도(1)=장례 장면 · 파혼(2)=조등만 · 처결 못 함(3)=20초 장면(한 혼에 한 번)
        if (clock != null && clock.Phase != lastFunPhase)
        {
            if (lastFunPhase == ClockPhase.Day && funeralPending.Count > 0)   // 낮이 끝났다: 그 낮에 열린 것은 못 본 장례로 사라진다(낮에 처결한 것은 다음 낮까지 남는다)
            {
                int missed = 0; foreach (var k in new List<string>(funeralPending.Keys)) { int born; if (!funeralBorn.TryGetValue(k, out born) || born != clock.Day) { funeralPending.Remove(k); funeralBorn.Remove(k); if (funeralPending.ContainsKey(k) == false) missed++; } }
                if (missed > 0) Say("보지 못한 장례");
            }
            lastFunPhase = clock.Phase;
        }
        if (clock != null && clock.Phase == ClockPhase.Day && openingStarted && !cuts.Active && funeralPending.Count > 0 && funeralDay != clock.Day)
        {
            string fire = null; int fireKind = 0;
            foreach (var kv in funeralPending)
            {
                FTarget ft;
                if (kv.Value == 2 || funeralDone.Contains(kv.Key)) { if (fire == null) { fire = kv.Key; fireKind = 2; } continue; }   // 조등만: 장면 없이 정리
                if (kv.Value == 3 && funeralNoneShown.Contains(kv.Key)) { if (fire == null) { fire = kv.Key; fireKind = 2; } continue; }   // 두 번째부터는 빗장만
                if (funeralTargets.TryGetValue(kv.Key, out ft) && new Vector2(player.Pos.x - ft.gate[0], player.Pos.z - ft.gate[1]).magnitude < 20f) { fire = kv.Key; fireKind = kv.Value; break; }
            }
            if (fire != null)
            {
                funeralPending.Remove(fire); funeralBorn.Remove(fire);
                if (fireKind != 2)
                {
                    funeralDay = clock.Day; funeralNow = fire; FuneralPos = FuneralPoint("gate");
                    if (fireKind == 1) funeralDone.Add(fire); else funeralNoneShown.Add(fire);
                    cuts.Play(funeralCut[fire] + (fireKind == 1 ? "_TENDO" : "_NONE"));
                }
            }
        }
        if (FieldRules.On)
            foreach (var b in new List<Enemy>(enemies.list))   // 복사본을 돈다: 안에서 혼을 새로 세우면(SpawnCamp) 원본 목록이 바뀌어 'Collection was modified' 오류가 났다
            {
                if (!b.soul.Boss || b.soul.BossId < 1 || bossIntroDone.Contains(b.soul.BossId)) continue;
                if (new Vector2(b.Pos.x - player.Pos.x, b.Pos.z - player.Pos.z).magnitude >= 40f) continue;
                bossIntroDone.Add(b.soul.BossId);
                if (cuts.Play(BossCut(b.soul, "INTRO"), true))
                {
                    player.CommandStop();
                    // 1호: 물에 빠진 혼 2마리가 뱃전을 잡고 올라온다 (대본). 2·3호는 바닥 무늬가 시작된다
                    if (b.soul.BossId == 1) for (int i = 0; i < 2; i++) enemies.SpawnCamp(b.Pos + new Vector3(i == 0 ? -3f : 3f, 0f, -2.5f), i == 0);
                }
            }
        cuts.Tick(dt);
        if (cuts.PauseEnemies) enemies.graceT = Mathf.Max(enemies.graceT, 0.5f);   // 컷 동안 적 공격 시계를 계속 되감는다
        float sh = cuts.TakeShake(); if (sh > 0f) feel.AddShake(sh);
    }

    /// <summary>지금 넋길을 탈 수 있나 (필드·밤·서낭당 곁·행동 가능). 서낭당 번호를 돌려준다(없으면 -1)</summary>
    /// <summary>폰 '상호작용' 버튼을 보일 때인가(서낭당 곁 밤)</summary>
    public bool CanSoulPathNow { get { return SoulPathStop() >= 0; } }
    public bool CanInteractNow { get { return Target != InteractKind.None; } }
    /// <summary>도술 칸 i 의 남은 재사용 대기(초). 이름이 없으면 0</summary>
    public float SkillLeft(int slot) { string n = ActiveNameAt(slot); return n == null ? 0f : lo.active.Left(n); }

    int SoulPathStop()
    {
        if (clock == null || Casting || !player.CanActNow() || !SoulPath.Available(clock.Daylight)) return -1;
        return SoulPath.NearIndex(player.Pos.x, player.Pos.z, FieldRules.Shrines);
    }

    // ---- F 상호작용(기획 npc-interaction-spec §2): 줍기 2m · 만져 보기 1.5m(2초 누르기) · 넋길 3m · 쉬기 3m ----
    /// <summary>줍기·만져 보기 자리(Interactables 가 채운다). OnUse 가 true 를 돌려주면 다 쓴 것(Done)</summary>
    public class InteractSpot { public InteractKind Kind; public Vector3 Pos; public System.Func<bool> OnUse; public System.Func<bool> Active; public bool Done; }
    public readonly List<InteractSpot> interactSpots = new List<InteractSpot>();
    public Interactables interactables;                    // 1막 물건 배치(필드에서만)
    public InteractKind Target = InteractKind.None;       // 지금 F 가 향하는 대상(안내·폰 버튼 글자가 이것을 따른다)
    public string TargetLabel = "";                        // 안내·폰 버튼 글자(넋길 곁이면 '꾹 눌러 쉬기'도 붙는다)
    public float HoldRatio;                                // 누르고 있는 진행(0~1): 만져 보기·쉬기
    public bool RestBlocked;                               // 쉬려는데 10m 안에 깨어 있는 혼이 있다
    InteractSpot targetSpot;
    float holdT, lastHold; bool prevF, heldConsumed;
    readonly List<InteractCand> candBuf = new List<InteractCand>();

    /// <summary>서낭당 곁(귀환 반경 + 여유 2m)인가 — 인 만들기가 열리는 자리</summary>
    public bool AtShrine { get { float d; ShrineNear(out d); return d <= Balance.SHRINE_RADIUS + 2f; } }
    void ShrineNear(out float dist) { dist = float.MaxValue; foreach (var sh in FieldRules.Shrines) { float d = Mathf.Sqrt((sh[0] - player.Pos.x) * (sh[0] - player.Pos.x) + (sh[1] - player.Pos.z) * (sh[1] - player.Pos.z)); if (d < dist) dist = d; } }

    /// <summary>매 프레임: 후보를 모아 대상 하나를 고르고, F 누름·누르고 있기(만져 보기·쉬기)를 처리한다</summary>
    void UpdateInteract(float dt)
    {
        candBuf.Clear(); targetSpot = null;
        float sd = float.MaxValue; bool canSoulPath = false;
        if (clock != null && !Casting && player.CanActNow())
        {
            for (int i = 0; i < interactSpots.Count; i++)
            {
                var sp = interactSpots[i]; if (sp.Done || (sp.Active != null && !sp.Active())) continue;
                candBuf.Add(new InteractCand { Kind = sp.Kind, Id = i, Dist = Mathf.Sqrt((sp.Pos.x - player.Pos.x) * (sp.Pos.x - player.Pos.x) + (sp.Pos.z - player.Pos.z) * (sp.Pos.z - player.Pos.z)) });
            }
            ShrineNear(out sd);
            canSoulPath = SoulPathStop() >= 0;
            if (canSoulPath) candBuf.Add(new InteractCand { Kind = InteractKind.SoulPath, Id = -1, Dist = sd });
            candBuf.Add(new InteractCand { Kind = InteractKind.Rest, Id = -1, Dist = sd });
        }
        int pick = Interact.Pick(candBuf);
        Target = pick < 0 ? InteractKind.None : candBuf[pick].Kind;
        if (pick >= 0 && candBuf[pick].Id >= 0) targetSpot = interactSpots[candBuf[pick].Id];

        // 쉬기 막힘: 10m 안에 깨어 있는 혼
        RestBlocked = false;
        if (Target == InteractKind.Rest || Target == InteractKind.SoulPath)
            foreach (var x in enemies.list) if (x.alive && (x.Pos - player.Pos).sqrMagnitude < Balance.SHRINE_REST_BLOCK_M * Balance.SHRINE_REST_BLOCK_M) { RestBlocked = true; break; }
        bool nightBoth = Target == InteractKind.SoulPath;   // 밤 서낭당: 톡 = 넋길, 꾹 = 쉬기
        TargetLabel = Target == InteractKind.None ? "" : nightBoth ? (RestBlocked ? "넋길 (혼이 가까이 있다)" : "넋길 · 길게 눌러 쉬기")
            : Target == InteractKind.Rest && RestBlocked ? "혼이 가까이 있다" : Interact.Label(Target);

        // F 상태: 키보드 또는 폰 버튼. 한 번 쓴 뒤에는 뗄 때까지 새 대상으로 이어지지 않는다
        bool fHeld = Input.GetKey(KeyCode.F) || TouchControls.UseHeld;
        if (!fHeld) heldConsumed = false;
        bool down = fHeld && !prevF, up = !fHeld && prevF; prevF = fHeld;
        if (fHeld && !heldConsumed) holdT += dt; else { if (up) lastHold = holdT; holdT = 0f; }
        if (sinceHit < 0.1f) holdT = 0f;   // 맞으면 앉기·만지기가 끊긴다
        HoldRatio = 0f;
        switch (Target)
        {
            case InteractKind.Pickup:
                if (down && targetSpot != null) UseSpot(targetSpot);
                break;
            case InteractKind.Touch:
                HoldRatio = Mathf.Clamp01(holdT / Balance.TOUCH_TIME);
                if (holdT >= Balance.TOUCH_TIME && targetSpot != null) { holdT = 0f; heldConsumed = true; UseSpot(targetSpot); }
                break;
            case InteractKind.SoulPath:
            case InteractKind.Rest:
                if (nightBoth && up && lastHold < 0.35f) CommandSoulPath();
                if (!RestBlocked && holdT > 0.35f)
                {
                    HoldRatio = Mathf.Clamp01(holdT / Balance.SHRINE_REST_TIME);
                    if (holdT >= Balance.SHRINE_REST_TIME) { holdT = 0f; heldConsumed = true; ShrineRest(); }
                }
                break;
            case InteractKind.None:
                if (down && npcs != null) npcs.DismissSubtitle();
                break;
        }
    }

    void UseSpot(InteractSpot sp) { if (sp.OnUse == null || sp.OnUse()) sp.Done = true; }

    /// <summary>서낭당에서 앉아 쉰다(기획 interactables-act1 §3). 시간은 넘기지 않는다</summary>
    void ShrineRest()
    {
        ledger.Hp = ledger.MaxHp; player.RefillDodge();
        int made = 0;
        if (interactables != null)
        {
            made = Mathf.Min(interactables.Herbs / Balance.HERB_PER_POTION, Mathf.Max(0, Shop_Max - dayScreen.Pack.Heal));   // 쑥 3개 → 회복약 1개(한도까지)
            dayScreen.Pack.Heal += made; interactables.Herbs -= made * Balance.HERB_PER_POTION;
        }
        CharacterPanel.Open = true;   // 성장 창(도술·능력치 점수 찍기)
        SaveGameNow();
        Say(made > 0 ? "서낭당에 이름을 걸어 두었다 — 쑥을 달여 회복약 " + made + "개" : "서낭당에 이름을 걸어 두었다");
        if (weather != null) { forecastNote = weather.PeekNext(clock); forecastT = 12f; }   // 다음 시간대 날씨 예보
    }
    const int Shop_Max = Balance.SHOP_HEAL_MAX;
    string forecastNote; float forecastT;   // 쉬고 난 뒤 시간 고리 곁에 잠시 띄우는 예보

    /// <summary>금줄이 닫힌 땅의 서낭당인가(2막 z≥640 · 3막 x≥768 또는 x&lt;0)</summary>
    static bool ShrineLocked(float[] s) { return (s[1] >= FieldRules.Size && s[0] >= 0f && s[0] < 768f && !FieldRules.Act2Open) || ((s[0] >= 768f || s[0] < 0f) && !FieldRules.Act3Open); }

    /// <summary>넋길: 다음 서낭당으로 즉시 이동</summary>
    public void CommandSoulPath()
    {
        int at = SoulPathStop();
        if (at < 0) return;
        int to = SoulPath.Next(at, FieldRules.Shrines.Length);
        // 2막 금줄이 닫혀 있으면 2막 서낭당(z 640 이상)은 건너뛰고 1막 처음으로 돌아간다
        for (int guard = 0; guard < FieldRules.Shrines.Length && ShrineLocked(FieldRules.Shrines[to]); guard++) to = SoulPath.Next(to, FieldRules.Shrines.Length);
        var s = FieldRules.Shrines[to];
        var dest = new Vector3(s[0], 0f, s[1] - 3f);   // 서낭당 바로 앞(남쪽)에 선다
        player.CommandStop(); player.Pos = dest;
        if (onTeleport != null) onTeleport(dest);
        Sfx.Play("sfx.tendo.done");
        Say("넋길 — " + FieldRules.ShrineNames[to]);
    }

    /// <summary>세계 시계를 흘리고, 단계가 바뀌면 종을 울리고 알린다</summary>
    void TickClock(float dt)
    {
        // 처음 5분: 박돌쇠를 처결할 때까지(최대 10분) 시계를 멈춘다 — 시간 압박 없이 배우게(기획 first-5-minutes)
        { var nb = NearestBoss(); float want = nb != null && Vector3.Distance(nb.Pos, player.Pos) < 24f ? 0.5f : 1f; ClockSky.ArenaFog = Mathf.MoveTowards(ClockSky.ArenaFog, want, dt * 0.5f); }   // 마당에 들어서면 2초에 걸쳐 안개가 반으로
        Enemy.IntroCalm = FieldRules.On && introFrozen && introT < 25f;
        Enemy.TokenMax = FieldRules.On ? (Enemy.IntroCalm ? 1 : introFrozen ? Balance.ATTACK_TOKENS_INTRO : Balance.ATTACK_TOKENS) : int.MaxValue;   // 동시에 때리는 혼 수 제한
        FieldCamps.EarlyMaxAlive = introFrozen ? 5 : int.MaxValue;   // 첫 5분엔 혼 8~10마리까지만
        if (introFrozen && !cuts.Active && !inDay) introT += dt;
        if (introFrozen && (pahonOrTendo != 0 || introT >= 600f)) { if (pahonOrTendo == 0) parkUnjudged = true; introFrozen = false; ui?.Hud.Toasts.Add("밤이 깊어 간다"); }
        if (!cuts.PauseClock && !introFrozen) clock.Tick(dt);   // 오프닝 컷 동안·첫 5분엔 시계가 멈춘다
        MoonEffects.Set(clock.FullMoon, clock.NewMoon);
        ActorModel.HeroShadowOn = clock.Phase != ClockPhase.Day;   // 낮엔 주인공 그림자 없음(산 사람에게 안 보이는 차사)
        if (interactables != null) DogTick();
        if (npcs != null) npcs.Tick(dt, player.Pos, clock.Phase);
        if (interactables != null) interactables.Tick(player.Pos);
        if (named != null) { named.AppearMult = weather.Fx.NamedMult; named.Tick(player.Pos, clock.Daylight); }
        night.Clues = Mathf.Min(Balance.BOSS_CLUES_REQUIRED, clueBook.Count("B01-"));   // 1막 첫 보스(나루 영감)의 낮 단서 수 = 보스 천도 조건
        // 처결 대기가 끝까지 지나 일어선 혼 = '처결 못 함'(장례 대상이면 다음 낮 장례로). 읽고 바로 지워 한 번만 센다
        foreach (var e in enemies.list) if (e.soul.TimedOut) { e.soul.TimedOut = false; Sfx.Play("sfx.wait.expire"); MarkUnjudged(e); }
        TickWaitTick(dt);
        TickFight();
        TickEliteSpawn(dt);
        TickCards(dt);
        TickHeukwol();
        var ph = clock.Consume();
        if (ph.HasValue)
        {
            Sfx.Play("sfx.bell");
            if (ph.Value == ClockPhase.Night) Hint(HintEvent.FirstNightfall);
            string n = WorldClock.PhaseName(ph.Value);
            if (ph.Value == ClockPhase.Dawn && funeralDone.Contains("칠복") && funeralDay >= 0) dogHome = true;
            if (ph.Value == ClockPhase.Dawn)
                foreach (var e in enemies.list) if (e.kneeling) { MarkUnjudged(e); e.soul.Finish(); Say("동이 터 무릎 꿇은 혼이 흩어졌다"); }   // 동틀녘: 대기 중 혼은 잃는 것 없이 흩어질 뿐(벌칙 없음)
            Say(ph.Value == ClockPhase.Dusk ? "인정 — 해가 진다" : ph.Value == ClockPhase.Dawn ? "파루 — 동이 튼다" : n + "이 되었다");
        }
        // 검사용: ] 로 배속 순환(1→10→60→1)
        if (debugKeys && Input.GetKeyDown(KeyCode.RightBracket)) clock.Speed = clock.Speed < 5f ? 10f : clock.Speed < 30f ? 60f : 1f;
    }

    /// <summary>H: 회복약 마시기(봇도 부른다)</summary>
    public void CommandHeal() { if (Shrine.UseHeal(ledger, dayScreen.Pack)) Say("회복약을 마셨다"); }

    void HandleKeys()
    {
        if (Input.GetKeyDown(KeyCode.E)) CommandTendo();
        // F(줍기·만져 보기·넋길·쉬기)는 UpdateInteract 가 누름·누르고 있기를 함께 처리한다
        if (Input.GetKeyDown(KeyCode.Alpha1)) UseSkill(0);
        if (Input.GetKeyDown(KeyCode.Alpha2)) UseSkill(1);
        if (Input.GetKeyDown(KeyCode.Alpha3)) UseSkill(2);
        if (Input.GetKeyDown(KeyCode.Alpha4)) UseSkill(3);
        if (Input.GetKeyDown(KeyCode.Tab)) player.CommandSwap();
        // 공물상에서 산 소모품: H = 회복약, X = 밟고 선 얼룩 지우기(씻김 부적)
        if (Input.GetKeyDown(KeyCode.H)) CommandHeal();
        if (Input.GetKeyDown(KeyCode.X) && dayScreen.Pack.Cleanse > 0)
        {
            float sx, sz;
            if (stains.RemoveNearest(player.Pos.x, player.Pos.z, Balance.STAIN_RADIUS, out sx, out sz)) { dayScreen.Pack.Cleanse--; Say("얼룩을 씻었다"); }
            else Say("지울 얼룩이 없다");
        }
        if (Input.GetKeyDown(KeyCode.R)) CommandPahon();
        // 검사용(?debug): 7/8/9 로 등에 멘 무기를 요령방울/삼지창/붓으로 바꿔 Tab 으로 꺼내 본다
        if (debugKeys)
        {
            if (Input.GetKeyDown(KeyCode.G)) godMode = !godMode;   // 검증용 불사
            if (Input.GetKeyDown(KeyCode.J)) player.Pos = new Vector3(MapLayout.BossX - 3f, 0, MapLayout.BossZ);   // 검증용: 보스 곁으로
            if (Input.GetKeyDown(KeyCode.N))   // 검증용: 가장 가까운 산 적을 바로 공격(클릭 타이밍 없이 콤보·피하기 검사)
            {
                Enemy best = null; float bd = 99f;
                foreach (var e in enemies.list) { if (!e.alive) continue; float d = Vector3.Distance(e.Pos, player.Pos); if (d < bd) { bd = d; best = e; } }
                if (best != null) player.CommandAttack(best);
            }
            if (Input.GetKeyDown(KeyCode.Alpha7)) lo.other = WeaponId.Bell;
            if (Input.GetKeyDown(KeyCode.Alpha8)) lo.other = WeaponId.Trident;
            if (Input.GetKeyDown(KeyCode.Alpha9)) lo.other = WeaponId.Brush;
        }
        // 검사용: 주소 끝에 ?debug 를 붙여 연 경우에만 K 키로 가장 가까운 적을 바로 무릎 꿇린다
        // (자동 화면 확인에서 '무릎 꿇은 혼' 장면을 안정적으로 만들기 위해. 일반 플레이엔 영향 없음)
        if (debugKeys && Input.GetKeyDown(KeyCode.K))
        {
            Enemy best = null; float bestD = 99f;
            foreach (var e in enemies.list)
            {
                if (!e.alive) continue;
                float d = Vector3.Distance(e.Pos, player.Pos);
                if (d < bestD) { bestD = d; best = e; }
            }
            if (best != null)
            {
                best.Pos = player.Pos + new Vector3(1.8f, 0, 0);   // 사거리 안으로
                best.TakeHit(100000, Vector3.right, 0f, 0f);
            }
        }
    }

    void UpdateStainViews()
    {
        var snap = stains.Snapshot();
        bool glb = Resources.Load<GameObject>("Models/Fx/fx_stain_decal") != null;   // 얼룩 장판 모델이 있으면 최우선
        bool art = !glb && SpriteLib.Texture("fx/stain_0") != null;   // 없으면 아트 그림, 그것도 없으면 색 원기둥
        while (stainViews.Count < snap.Count)
        {
            GameObject go;
            if (glb) go = FxMesh.Spawn("fx_stain_decal", Vector3.zero, 1f, ChasaPalette.WonnyeomStain);
            else if (art) go = GroundFx.Persistent(Vector3.zero, Balance.STAIN_RADIUS, "fx/stain_0");
            else
            {
                // 납작한 원기둥으로 웅덩이를 만든다. 색은 아트팀 팔레트의 '원념 얼룩'
                go = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                Destroy(go.GetComponent<Collider>());
                go.GetComponent<Renderer>().sharedMaterial = U.Matte(ChasaPalette.WonnyeomStain);
            }
            stainViews.Add(go);
        }
        while (stainViews.Count > snap.Count) { Destroy(stainViews[stainViews.Count - 1]); stainViews.RemoveAt(stainViews.Count - 1); }
        for (int i = 0; i < snap.Count; i++)
        {
            float life = snap[i][2];
            float fade = Mathf.Clamp01(life * Balance.STAIN_DURATION / 2f);   // 마지막 2초 동안 줄어들며 사라진다(언제 없어지는지 보이게)
            if (glb)
            {
                // 모델 얼룩(지름 약 2.2m)을 STAIN_RADIUS 에 맞추고, 마지막 2초에 줄어든다
                float d = Balance.STAIN_RADIUS * 2f / 2.2f * fade;
                stainViews[i].transform.position = new Vector3(snap[i][0], 0.02f + i * 0.002f + GroundTerrain.HeightAt(snap[i][0], snap[i][1]), snap[i][1]);
                stainViews[i].transform.localScale = new Vector3(d, d, d);
            }
            else if (art)
            {
                // 그림 얼룩은 같은 크기에서 점점 작아진다 (그림 쿼드의 기본 크기는 반경 STAIN_RADIUS 기준)
                stainViews[i].transform.position = new Vector3(snap[i][0], 0.02f + i * 0.002f + GroundTerrain.HeightAt(snap[i][0], snap[i][1]), snap[i][1]);
                stainViews[i].transform.localScale = new Vector3(fade, 1f, fade);
            }
            else
            {
                float d = Balance.STAIN_RADIUS * 2f * fade;
                stainViews[i].transform.position = new Vector3(snap[i][0], 0.02f + i * 0.002f + GroundTerrain.HeightAt(snap[i][0], snap[i][1]), snap[i][1]);
                stainViews[i].transform.localScale = new Vector3(d, 0.01f, d);
            }
        }
    }

    /// <summary>장비 한 칸의 아이콘과 등급 테두리. 비어 있으면 칸만 어둡게</summary>
    void DrawGearIcon(Slot s, Rect r)
    {
        var it = lo.gear.Get(s);
        GUI.color = new Color(0, 0, 0, 0.45f); GUI.DrawTexture(r, white); GUI.color = Color.white;
        if (it == null) return;
        string rar = it.Named ? "named" : it.Rarity == Rarity.Rare ? "rare" : it.Rarity == Rarity.Crafted ? "crafted" : "common";
        string icon = Ko.IconName(s, rar, it.Named);
        var tex = SpriteLib.Texture("icons/" + icon);
        var frame = SpriteLib.Texture("icons/frame_" + rar);
        if (tex != null) GUI.DrawTexture(r, tex);
        if (frame != null) GUI.DrawTexture(r, frame);
    }

    string GearName(Slot s)
    {
        var it = lo.gear.Get(s);
        return it == null ? "-" : Ko.ItemName(it, Ko.FamilyOf(s, s == Slot.Weapon ? (WeaponId?)lo.weapon : null)) + "/" + it.Options.Count;
    }

    // ===== 화면 ====================================================================
    /// <summary>화면에 보일 값을 모아(HudState) 새 화면(UI Toolkit)에 넘긴다</summary>
    public System.Action<Vector3> onTeleport;   // 넋길로 순간이동했을 때 카메라가 따라가게 GameMain 이 받는다
    public readonly MemoryLines memories = new MemoryLines();   // 천도 기억 한 줄
    public string memLine; public float memLineT;              // 지금 화면에 띄울 기억 줄(보랏빛 자막)
    public readonly TutorialHints hints = new TutorialHints();   // 처음 한 번만 뜨는 안내
    public void HintClue() { Hint(HintEvent.FirstClue); }

    // ---- 처음 5분 안내 대기줄(기획 first-5-minutes.md): 행동을 하면 닫히고, 한 번에 하나만 뜬다 ----
    public readonly GuideQueue guide = new GuideQueue();
    [System.Serializable] class GuideFile { public GuideRow[] steps; }
    [System.Serializable] class GuideRow { public string id, pc, touch, key; public bool timed; public float dur; }
    const string GuidePref = "chasa.guide.done"; int guideSaved;   // 본 안내 목록(브라우저 저장소)
    public bool introFrozen; float introT;                // 첫 5분 시계 정지(GameMain 이 필드 시작 때 켠다)
    bool revNeok, revMemory, revCoin, revKarma;           // 장부 항목이 한 번이라도 열렸나
    bool firstTeleDone;                                   // 첫 예고 특례를 이미 썼나
    Enemy firstCardSoul;                                  // 처결 카드를 띄우는 첫 무릎 혼(이 혼만 대기 시간이 멈춘다)
    bool firstKneelDone;
    bool guideLoaded; Vector3 walkFrom; bool walkFromSet; float guideClock;
    void LoadGuide()
    {
        guideLoaded = true;
        var ta = Resources.Load<TextAsset>("Data/tutorial_hints"); if (ta == null) return;
        GuideFile f = null; try { f = JsonUtility.FromJson<GuideFile>(ta.text); } catch { }
        if (f == null || f.steps == null) return;
        foreach (var r in f.steps) guide.Define(new GuideStep { Id = r.id, Pc = r.pc, Touch = r.touch, Key = r.key, Timed = r.timed, Dur = r.dur > 0f ? r.dur : 3f });
        var u = (Application.absoluteURL ?? "").ToLowerInvariant();
        if (u.Contains("guide=off")) guide.Enabled = false;   // 숙련자: 안내 끄기
        if (u.Contains("guide=reset")) { try { PlayerPrefs.DeleteKey(GuidePref); } catch { } }   // 검수용: 본 안내 기록 지우기
        try { foreach (var id in PlayerPrefs.GetString(GuidePref, "").Split(',')) if (id.Length > 0) guide.MarkDone(id); } catch { }   // 이어하기: 본 안내는 다시 안 뜬다
    }

    /// <summary>안내를 띄울 상황을 보고 요청하고, 화면 값(HudState)을 채운다. 컷신·낮 화면·창이 열려 있으면 쉰다</summary>
    // ---- 보스 체력바·지역 진입 알림 값 채우기 ----
    string lastArea; float areaT = -1f; int introPlainDone;   // 첫 5분 퀘스트: 이름 없는 혼을 처결한 수
    void FillBossArea(HudState h)
    {
        h.BossName = null;
        h.CastRatio = Casting ? Mathf.Clamp01(castT / Mathf.Max(0.01f, castTotal)) : -1f;   // 시전 막대·짧은 한마디는 UiRoot 가 그린다(예전 IMGUI 는 ui 가 없을 때만)
        h.SayText = toastT > 0f ? toast : null;
        // 고정 자막 넷도 UiRoot 가 그린다(말풍선만 월드 좌표라 IMGUI 에 남는다)
        h.SubSfx = cuts.LineVisible && cuts.LineStyle == "sfx" ? cuts.LineText : null;
        h.SubCutMemory = cuts.LineVisible && cuts.LineStyle == "memory" ? "“" + cuts.LineText + "”" : null;
        if (memLineT > 0f) memLineT -= Time.unscaledDeltaTime;
        h.SubMemLine = memLineT > 0f ? "“" + memLine + "”" : null; h.SubMemLineAlpha = Mathf.Clamp01(memLineT / 0.8f);
        h.SubNpc = npcs != null && npcs.SubtitleT > 0f ? npcs.Subtitle : null; h.SubNpcName = npcs != null ? npcs.SubtitleName : null;
        // 무릎 꿇은 혼이 3m 안이면 F 안내를 숨긴다(그 순간엔 E·R 이 주인공, 기획 §2-2). F 를 눌러도 동작은 한다
        bool kneelNear = enemies.NearestKneeling(player.Pos, 3f) != null;
        h.InteractLabel = Target != InteractKind.None && !kneelNear ? TargetLabel : null;
        h.InteractRatio = HoldRatio; h.SubNpcAlpha = npcs != null ? Mathf.Clamp01(npcs.SubtitleT / 0.6f) : 0f;
        // 경험치(품계) 막대: 처음 넋을 얻은 뒤에만(하나씩 열기)
        h.ShowExp = revNeok && FieldRules.On; h.Rank = growth.Rank;
        { int lo0 = GrowthState.NeokForRank(growth.Rank), hi0 = GrowthState.NeokForRank(growth.Rank + 1); h.ExpRatio = hi0 <= lo0 ? 1f : (float)(growth.TotalNeok - lo0) / (hi0 - lo0); }
        // 첫 5분 퀘스트 추적(기획): 명부 — 이름 없는 혼 n/2, 박돌쇠 n/1. 시계가 풀리면(첫 처결 끝) 사라진다
        if (introFrozen && FieldRules.On) { h.QuestTitle = "명부"; h.QuestLines = new[] { "이름 없는 혼 " + Mathf.Min(2, introPlainDone) + "/2", "박돌쇠 " + (pahonOrTendo != 0 ? 1 : 0) + "/1" }; }
        else { h.QuestTitle = null; h.QuestLines = null; }
        foreach (var e in enemies.list)
        {
            if (e == null || !(e.soul.Boss || e.elite) || !e.alive && !e.kneeling) continue;   // 거센 혼도 이름 띠(맺힘 막대)가 뜬다
            if (new Vector2(e.Pos.x - player.Pos.x, e.Pos.z - player.Pos.z).magnitude > 45f) continue;   // 가까이 가야 막대가 뜬다
            h.BossName = e.label; h.BossKneel = e.kneeling; h.BossRatio = e.soul.MaedhimMax <= 0 ? 0f : (float)e.soul.Maedhim / e.soul.MaedhimMax;
            break;
        }
        string zn = FieldRules.On ? FieldZones.CurrentName : null;
        if (!string.IsNullOrEmpty(zn) && zn != lastArea) { lastArea = zn; areaT = 0f; }   // 구역이 바뀌면 4초 알림
        if (areaT >= 0f && !cuts.Active) { areaT += Time.unscaledDeltaTime; if (areaT > 3.5f) areaT = -1f; }   // 나타남 0.5 + 유지 2 + 사라짐 1
        h.AreaText = areaT >= 0f ? lastArea : null;
        h.AreaAlpha = areaT < 0f ? 0f : Mathf.Min(areaT / 0.5f, (3.5f - areaT) / 1f, 1f);
    }

    void GuideTick(HudState h)
    {
        if (!guideLoaded) LoadGuide();
        bool quiet = inDay || night.Over || cuts.Active || CharacterPanel.Open || SettingsPanel.Open || MiniMap.BigOpen;
        if (!quiet)
        {
            guideClock += Time.deltaTime;
            if (!walkFromSet) { walkFrom = player.Pos; walkFromSet = true; guide.Request("walk"); }
            if (!guide.IsDone("walk") && (player.Pos - walkFrom).magnitude >= 3f) guide.Complete("walk");
            if (guide.IsDone("walk"))
            {
                guide.Request("map");
                bool near = false, winding = false, far = false;
                foreach (var e in enemies.list)
                {
                    if (e == null || !e.alive || e.gone || e.soul.Boss) continue;
                    float d = Vector3.Distance(e.Pos, player.Pos);
                    if (d < 12f) near = true;
                    if (d < 10f && e.atk != null && e.atk.Winding)
                    {
                        winding = true;
                        if (!firstTeleDone)   // 첫 혼의 첫 공격 예고: 1.5배 길게 + 화면 0.5초 30% 느리게(이번 한 번만)
                        {
                            firstTeleDone = true; e.atk.WindupTime *= 1.5f; e.atk.Windup = e.atk.WindupTime; feel.SlowMo(0.5f, 0.3f);
                        }
                    }
                    if (d > 10f && d < 20f) far = true;
                }
                if (near) guide.Request("hit");
                if (winding) guide.Request("dodge");
                if (far && guide.IsDone("hit")) guide.Request("pull");
                if (guideClock > 90f && guide.IsDone("hit")) guide.Request("zoom");
                // 첫 5분 보충 안내 넷(기획): 처음 한 번만, 한 번에 하나씩(대기줄이 순서를 지킨다)
                if (introPlainDone >= 1) guide.Request("codex");                                          // 첫 처결 뒤: [C] 명부
                if (player.speedMult < 0.95f && stains.IsOnStain(player.Pos.x, player.Pos.z)) guide.Request("stain");   // 얼룩에 처음 들어가 느려질 때
                if (Casting) guide.Request("castdef");                                                    // 천도 시전 중: 무방비
                foreach (var e2 in enemies.list)                                                          // 명부 밖 이름혼이 무릎 꿇었을 때
                    if (e2 != null && e2.kneeling && e2.soul.Name != null && NamedSoulSpawns.OffLedger.Contains(e2.soul.Name) && Vector3.Distance(e2.Pos, player.Pos) < 12f) { guide.Request("offledger"); break; }
            }
            guide.Tick(Time.deltaTime);
            int nDone = 0; foreach (var _ in guide.DoneIds) nDone++;
            if (nDone != guideSaved) { guideSaved = nDone; try { PlayerPrefs.SetString(GuidePref, string.Join(",", new List<string>(guide.DoneIds).ToArray())); PlayerPrefs.Save(); } catch { } }
        }
        if (firstCardSoul != null && (!firstCardSoul.kneeling || firstCardSoul.gone)) { firstCardSoul.soul.Frozen = false; firstCardSoul = null; }   // 처결했으면 카드를 접고 대기 시간을 되돌린다
        h.JudgeCard = firstCardSoul != null && !quiet;
        var cur = guide.Current;
        h.GuideText = quiet || cur == null || h.JudgeCard ? null : guide.TextFor(Ko.TouchUI);
        h.GuideKey = cur != null && !Ko.TouchUI ? cur.Key : null;
        h.GuideCheck = guide.Checking; h.GuideRemind = guide.Reminding;
    }
    void Hint(HintEvent e) { var t = hints.On(e, Ko.TouchUI); if (t != null) ui?.Hud.Toasts.Add(t); }
    public readonly CutscenePlayer cuts = new CutscenePlayer();   // 나루 영감 실시간 컷신
    readonly HashSet<int> bossIntroDone = new HashSet<int>();   // 등장 컷을 본 보스 번호
    public NamedSoulSpawns named;               // 첫 세션 이름혼들
    public NpcWorld npcs;                       // 필드의 산 사람(엿듣기·지켜보기)
    public readonly ClueBook clueBook = new ClueBook();
    public WorldClock clock;   // 필드 모드의 흐르는 하루 (없으면 옛 '하룻밤 한 판')
    public FieldCamps camps;   // 필드 모드에서만 있다
    Vector3? moveRef;      // 처음 선 자리(걷기 안내 판단용)
    SoulMarkers soulMarkers;
    void LateUpdate()
    {
        if (!inDay)
        {
            if (soulMarkers == null) soulMarkers = new SoulMarkers(null);
            soulMarkers.Refresh(enemies.list);          // 발밑 시간 고리
        }
        else if (soulMarkers != null) soulMarkers.Refresh(new List<Enemy>());   // 낮에는 모두 끈다
        if (ui == null) return;
        var h = ui.Hud;
        FillEdges(h);
        GuideTick(h);
        FillBossArea(h);
        if (clock != null)
        {
            h.Peaceful = clock.Daylight > 0.6f && !Casting && !AnyEnemyNear(25f);
            h.TimeOfDay = clock.DayFraction; h.IsDawn = clock.Reddish; h.Daylight = clock.Daylight; h.FullMoon = clock.FullMoon; h.NewMoon = clock.NewMoon; h.MoonPhase = clock.MoonPhase;
            h.ClockLabel = WorldClock.PhaseName(clock.Phase) + (clock.FullMoon ? " · 보름달" : clock.NewMoon ? " · 그믐" : "") + (clock.Speed > 1.5f ? "  x" + (int)clock.Speed : "") + (introFrozen ? "  · 시간 멈춤" : "");
            if (forecastT > 0f) { forecastT -= Time.unscaledDeltaTime; h.ClockLabel += "\n" + forecastNote; }   // 서낭당 예보
        }
        else { h.Peaceful = false; h.TimeOfDay = Mathf.Clamp01(1f - night.TimeLeft / Mathf.Max(1f, Balance.NIGHT_DURATION)); h.IsDawn = night.Warning; h.Daylight = 0f; h.ClockLabel = null; }
        h.Neok = ledger.Neok; h.Memory = ledger.Memory; h.Coin = ledger.Coin; h.Karma = ledger.Karma; h.KarmaHidden = weather.Fx.HideKarma; h.ChainBonus = chainLeft > 0f;
        if (FieldRules.On)   // HUD 하나씩 열기: 처음 얻을 때 숫자가 나타난다(업은 10에 처음 닿을 때)
        {
            revNeok |= ledger.Neok > 0; revMemory |= ledger.Memory > 0; revCoin |= ledger.Coin > 0; revKarma |= ledger.Karma >= 10;
            h.ShowNeok = revNeok; h.ShowMemory = revMemory; h.ShowCoin = revCoin; h.ShowKarma = revKarma;
        }
        h.Hp = ledger.Hp; h.MaxHp = ledger.MaxHp; h.Heal = dayScreen.Pack.Heal;
        h.SecondsLeft = Mathf.CeilToInt(night.TimeLeft); h.Sent = night.Sent; h.Quota = Balance.NIGHT_QUOTA;
        h.Clues = night.Clues; h.CluesNeeded = Balance.BOSS_CLUES_REQUIRED;
        h.BossDone = night.BossDone; h.QuotaDone = night.QuotaDone; h.Warning = night.Warning;
        h.DodgeCharges = player.DodgeCharges; h.DodgeMax = Balance.DODGE_CHARGES; h.PullCd = player.PullCooldown; h.WeaponName = lo.Def.Name;
        for (int si = 0; si < h.Slots.Length; si++)   // 도술 4칸 표시값(HUD 가 그림으로 그린다)
        {
            string sn = ActiveNameAt(si); var sv = h.Slots[si];
            sv.Name = sn; sv.Cd = sn == null ? 0f : lo.active.Ratio(sn); sv.CdSec = sn == null ? 0f : lo.active.Left(sn);
        }
        // 얻은 것 알림: 장부 값이 늘어난 만큼 쪽지를 띄운다(같은 글은 합쳐진다). 낮 화면을 넘어온 첫 프레임엔 띄우지 않는다
        if (toastReady)
        {
            if (ledger.Neok > pNeok) h.Toasts.Add("넋 +" + (ledger.Neok - pNeok));
            if (ledger.Memory > pMemory) h.Toasts.Add("기억 +" + (ledger.Memory - pMemory));
            if (ledger.Coin > pCoin) h.Toasts.Add("엽전 +" + (ledger.Coin - pCoin));
            if (ledger.Karma > pKarma && !weather.Fx.HideKarma) h.Toasts.Add("업 +" + (ledger.Karma - pKarma));   // 비 오는 밤엔 업이 오른 것도 가린다
            if (lo.lastDropT > 0f && lo.lastDrop != pDrop) h.Toasts.Add(lo.lastDrop);
        }
        pNeok = ledger.Neok; pMemory = ledger.Memory; pCoin = ledger.Coin; pKarma = ledger.Karma; pDrop = lo.lastDrop; toastReady = true;
        h.Toasts.Tick(Time.unscaledDeltaTime);
        if (h.StampAge >= 0f) { h.StampAge += Time.unscaledDeltaTime; if (h.StampAge > Balance.RANKUP_STAMP_SEC) h.StampAge = -1f; }
        ui.Refresh(!inDay && !night.Over && !CharacterPanel.Open && !SettingsPanel.Open);
    }
    int pNeok, pMemory, pCoin, pKarma; string pDrop; bool toastReady;

    /// <summary>화면 가장자리 경고: 공격 준비 중인 적이 화면 밖이거나(천도 중이면) 좁아진 시야 밖이면 방향 표시를 띄운다</summary>
    void FillEdges(HudState h)
    {
        h.Edges.Clear();
        if (moveRef == null) { moveRef = player.Pos; Hint(HintEvent.FirstMove); }   // 시작하자마자 걷기·공격 안내 한 번
        var cam = Camera.main; if (cam == null || inDay || night.Over) return;
        float w = Screen.width, hh = Screen.height;
        float diag = Mathf.Sqrt(w * w + hh * hh);
        float vr = EdgeWarn.VisionRadius(diag, lo.stats.VisionRatio(Balance.TENDO_VISION_RATIO), visionP);
        foreach (var e in enemies.list)
        {
            if (!e.alive || !e.atk.Winding) continue;      // 예비동작 중인 적만 (평소 모든 적에 띄우면 어지럽다)
            var sp = cam.WorldToScreenPoint(e.HeadPosition);
            if (sp.z < 0f) { sp.x = w - sp.x; sp.y = hh - sp.y; }   // 카메라 뒤쪽이면 반대편으로 뒤집어 방향만 맞춘다
            float ex, ey;
            if (EdgeWarn.Compute(sp.x, hh - sp.y, w, hh, 48f, vr, out ex, out ey))   // 화면 y 는 위로 갈수록 커서 UI 좌표로 뒤집는다
            { h.Edges.Add(new EdgeMark { Nx = ex / w, Ny = ey / hh }); Hint(HintEvent.FirstEdgeWarn); }
        }
    }

    /// <summary>싸울 수 있는 혼이나 처결 대기 혼이 이 거리 안에 있나 (평화로운 낮 판정)</summary>
    /// <summary>BGM 용: 가장 가까운 살아 있는 적 거리와, 무릎 꿇은 채 처결을 기다리는 적 수</summary>
    public float NearestEnemyDist(out int kneeling)
    {
        float best = float.MaxValue; kneeling = 0;
        foreach (var e in enemies.list)
        {
            if (e.gone) continue;
            float d = (e.Pos - player.Pos).magnitude; if (d < best) best = d;
            if (e.kneeling) kneeling++;
        }
        return best;
    }

    bool AnyEnemyNear(float range)
    {
        float r2 = range * range;
        foreach (var e in enemies.list)
            if (!e.gone && (e.Pos - player.Pos).sqrMagnitude < r2) return true;
        return false;
    }

    /// <summary>맥락 버튼: 지금 천도/파혼이 가능한 무릎 꿇은 혼이 가까이 있나 (폰 버튼을 그때만 켠다)</summary>
    bool AnyKneelNearby(out bool canTendo)
    {
        canTendo = false; bool any = false;
        foreach (var e in enemies.list)
        {
            if (!e.kneeling) continue;
            if ((e.Pos - player.Pos).sqrMagnitude > 7f * 7f) continue;
            any = true;
            if (CanTendoNow(e)) canTendo = true;
        }
        return any;
    }

    void OnGUI()
    {
        Ko.Apply(); // 한글 글꼴 적용(안 하면 한글이 네모로 깨짐)
        if (white == null) return;
        if (CharacterPanel.Open || SettingsPanel.Open || MiniMap.BigOpen) return;   // 큰 지도가 열리면 월드 이름표·막대도 숨긴다(아트 검수)
        // 캐릭터 창·설정이 열리면 밤 화면 글자·버튼은 그리지 않는다(QA B2)
        if (inDay) { dayScreen.OnGUI(white); return; }   // 낮 화면이 모든 것을 덮는다
        weather.DrawOverlay(player.Pos);   // 비 줄기(HUD 보다 아래)
        if (npcs != null) npcs.DrawWorld(Camera.main, player.Pos, white);
        if (interactables != null) interactables.DrawWorld(Camera.main, player.Pos, white);   // 귀·눈 아이콘, 진행, 지나가는 혼잣말
        // (0) 화면 번쩍임: 천도/파혼 순간의 색
        if (vignetteT > 0f) { var vg = SpriteLib.Texture("fx/hit/hit_player_vignette"); if (vg != null) { GUI.color = new Color(1f, 1f, 1f, vignetteT / 0.15f * (SaveStore.Settings.ReduceFlash ? 0.5f : 1f)); GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), vg, ScaleMode.StretchToFill); GUI.color = Color.white; } }
        if (flashA > 0.001f) { GUI.color = new Color(flashColor.r, flashColor.g, flashColor.b, flashA * (SaveStore.Settings.ReduceFlash ? 0.3f : 1f)); GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), white); GUI.color = Color.white; }
        // (1) 시야 축소 + 기억의 색 (천도 캐스팅 중)
        if (visionP > 0.001f)
        {
            var tint = ChasaPalette.MemoryRim;
            float diag = Mathf.Sqrt(Screen.width * Screen.width + Screen.height * Screen.height);
            float size = Mathf.Lerp(diag * 1.25f, diag * 1.25f * lo.stats.VisionRatio(Balance.TENDO_VISION_RATIO), visionP);   // 반경 60%로
            var r = new Rect((Screen.width - size) / 2f, (Screen.height - size) / 2f, size, size);
            GUI.color = new Color(tint.r * 0.35f, tint.g * 0.25f, tint.b * 0.5f, 0.95f * visionP);
            GUI.DrawTexture(r, vignette);
            // 가림막 바깥 모서리는 같은 색으로 채운다
            GUI.DrawTexture(new Rect(0, 0, Screen.width, r.y), white);
            GUI.DrawTexture(new Rect(0, r.yMax, Screen.width, Screen.height - r.yMax), white);
            GUI.DrawTexture(new Rect(0, r.y, r.x, r.height), white);
            GUI.DrawTexture(new Rect(r.xMax, r.y, Screen.width - r.xMax, r.height), white);
            GUI.color = Color.white;
        }
        // (1-2) 이름표: 이름혼·보스 머리 위 (기본 글꼴에 한글이 없어 영문 표기: 나루 영감=Old Ferryman)
        if (cam != null)
        {
            var nameStyle = new GUIStyle(GUI.skin.label) { fontSize = 16, alignment = TextAnchor.MiddleCenter };
            nameStyle.normal.textColor = Color.white;
            foreach (var e in enemies.list)
            {
                if (e.label == null || e.gone) continue;
                var sp = cam.WorldToScreenPoint(e.HeadPosition + Vector3.up * 0.9f);
                GUI.Label(new Rect(sp.x - 80, Screen.height - sp.y - 12, 160, 24), e.soul.Boss ? (e.label ?? "나루 영감") : e.label, nameStyle);
            }
        }
        // (2) 머리 위 '맺힘' 막대 = 남은 맺힘(체력 대신 깎이는 수치). 처결 대기 시간은 발밑 고리(SoulMarkers)가 맡는다.
        //     보스·이름혼·맞아서 깎인 혼에게만 보인다(전부 띄우면 화면이 막대 숲이 된다). 덩어리는 두 줄(= 두 배 질기다는 표시)
        if (cam != null)
        {
            foreach (var e in enemies.list)
            {
                if (!e.alive) continue;
                var so = e.soul;
                bool named = so.Boss || e.label != null;
                if (!so.Boss && e.barT <= 0f) continue;   // 명세: 보스는 늘, 나머지는 맞았을 때 3초만(머리 위 막대 숲 방지)
                var sp = cam.WorldToScreenPoint(e.HeadPosition - Vector3.up * 0.15f);
                if (sp.z < 0f) continue;
                float ratio = Mathf.Clamp01((float)so.Maedhim / Mathf.Max(1, so.MaedhimMax));
                int rows = so.Kind == SoulKind.Lump ? 2 : 1;
                float wBar = named ? 72f : 56f;
                // 아트 맺힘 막대(틀 96x14 / 보스 금테 / 덩어리 두 줄 96x28 + 홈 88x8): 있으면 그림으로, 없으면 아래 색 막대
                var gFrame = SpriteLib.Texture("ui/" + (rows == 2 ? "ui_bar_gyeol_frame_x2" : so.Boss ? "ui_bar_gyeol_frame_gold" : "ui_bar_gyeol_frame"));
                var gFill = SpriteLib.Texture("ui/ui_bar_gyeol_fill"); var gGhost = SpriteLib.Texture("ui/ui_bar_gyeol_ghost");
                if (gFrame != null && gFill != null && gGhost != null)
                {
                    float k = (named ? 80f : 64f) / 96f, fw = 96f * k, fh = gFrame.height * k;
                    var fr = new Rect(sp.x - fw * 0.5f, Screen.height - sp.y - fh * 0.5f, fw, fh);
                    GUI.DrawTexture(fr, gFrame);
                    for (int r2 = 0; r2 < rows; r2++)
                    {
                        float rr = rows == 1 ? ratio : Mathf.Clamp01(ratio * 2f - (rows - 1 - r2));
                        var slot = new Rect(fr.x + 4f * k, fr.y + (rows == 1 ? 3f : 4f + r2 * 12f) * k, 88f * k, 8f * k);
                        GUI.DrawTexture(slot, gGhost);
                        GUI.DrawTextureWithTexCoords(new Rect(slot.x, slot.y, slot.width * rr, slot.height), gFill, new Rect(0f, 0f, rr, 1f));   // 비율만큼만 잘라 그린다(찌그러지지 않게)
                    }
                    continue;
                }
                for (int r = 0; r < rows; r++)
                {
                    // 두 줄이면 위 줄이 먼저 닳는다: 전체 비율을 줄마다 절반씩 나눠 채운다
                    float rowRatio = rows == 1 ? ratio : Mathf.Clamp01(ratio * 2f - (rows - 1 - r));
                    var bg = new Rect(sp.x - wBar * 0.5f, Screen.height - sp.y - 4 + r * 9, wBar, 8);
                    GUI.color = new Color(0, 0, 0, 0.7f); GUI.DrawTexture(bg, white);
                    GUI.color = new Color(0.85f, 0.3f, 0.3f);
                    GUI.DrawTexture(new Rect(bg.x + 1, bg.y + 1, (wBar - 2) * rowRatio, 6), white);
                }
                GUI.color = Color.white;
            }
        }
        // (2.2) 오프닝 검은 화면
        if (cuts.OpeningBlack > 0.01f) { GUI.color = new Color(0, 0, 0, cuts.OpeningBlack); GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), white); GUI.color = Color.white; }
        // (2.3) 컷신 대사: 말풍선은 보스 머리 위, 기억 줄은 화면 아래 가운데(보랏빛). 건너뛰기 진행 막대
        if (cuts.LineVisible && cam != null)
        {
            var cs = new GUIStyle(GUI.skin.label) { fontSize = Ko.TouchUI ? 26 : 22, alignment = TextAnchor.MiddleCenter, wordWrap = true };
            if (ui != null && (cuts.LineStyle == "sfx" || cuts.LineStyle == "memory")) { }   // UiRoot 가 그린다
            else if (cuts.LineStyle == "sfx")
            {
                // 소리 자막: 화면 아래 가운데, 흐린 흰 글씨 대괄호(대사가 아니다 — 서사: 소리가 들어오면 접근성 설정에서만 켠다)
                cs.fontSize = Ko.TouchUI ? 22 : 18; cs.normal.textColor = new Color(0.85f, 0.85f, 0.85f, 0.85f);
                GUI.Label(new Rect(Screen.width * 0.15f, Screen.height - 150, Screen.width * 0.7f, 40), cuts.LineText, cs);
            }
            else if (cuts.LineStyle == "memory")
            {
                cs.normal.textColor = new Color(0.79f, 0.69f, 1f, 1f); cs.fontStyle = FontStyle.Italic;
                GUI.Label(new Rect(Screen.width * 0.15f, Screen.height - 230, Screen.width * 0.7f, 100), "“" + cuts.LineText + "”", cs);
            }
            else
            {
                var bs = NearestBoss();
                var sp = bs != null ? cam.WorldToScreenPoint(bs.HeadPosition + Vector3.up * 1.2f) : new Vector3(Screen.width * 0.5f, Screen.height * 0.6f, 1f);
                var r = new Rect(sp.x - 150, Screen.height - sp.y - 30, 300, 60);
                GUI.color = new Color(0.95f, 0.92f, 0.82f, 0.92f); GUI.DrawTexture(r, white);
                cs.normal.textColor = new Color(0.12f, 0.1f, 0.08f); GUI.color = Color.white;
                GUI.Label(r, cuts.LineText, cs);
            }
        }
        if (cuts.SkipProgress > 0.02f)
        {
            GUI.color = new Color(0, 0, 0, 0.6f); GUI.DrawTexture(new Rect(Screen.width * 0.5f - 80, Screen.height - 24, 160, 8), white);
            GUI.color = Color.white; GUI.DrawTexture(new Rect(Screen.width * 0.5f - 79, Screen.height - 23, 158 * cuts.SkipProgress, 6), white);
        }
        // (2.4) 기억 한 줄: 천도 직후 화면 가운데 위, 기억 색(보랏빛)
        if (memLineT > 0f && ui == null)
        {
            memLineT -= Time.unscaledDeltaTime;
            var ms = new GUIStyle(GUI.skin.label) { fontSize = Ko.TouchUI ? 26 : 22, alignment = TextAnchor.MiddleCenter, wordWrap = true, fontStyle = FontStyle.Italic };
            float a = Mathf.Clamp01(memLineT / 0.8f);
            ms.normal.textColor = new Color(0.79f, 0.69f, 1f, a);
            GUI.Label(new Rect(Screen.width * 0.15f, Screen.height * 0.18f, Screen.width * 0.7f, 90), "“" + memLine + "”", ms);
        }
        // (2.5) 산 사람 대사 자막(엿듣기): 화면 아래 가운데
        if (npcs != null && npcs.SubtitleT > 0f && ui == null)
        {
            var st = new GUIStyle(GUI.skin.label) { fontSize = Mathf.RoundToInt((Ko.TouchUI ? 26 : 22) * Mathf.Max(1f, Screen.height / 720f)), alignment = TextAnchor.MiddleCenter, wordWrap = true };
            st.normal.textColor = new Color(0.953f, 0.906f, 0.827f, Mathf.Clamp01(npcs.SubtitleT / 0.6f));   // 한지색 글자
            var r = new Rect(Screen.width * 0.15f, Screen.height - Mathf.Max(190f, Screen.height * 0.24f), Screen.width * 0.7f, Mathf.Max(60f, Screen.height * 0.085f));
            GUI.color = new Color(0.06f, 0.05f, 0.05f, 0.55f * Mathf.Clamp01(npcs.SubtitleT / 0.6f));   // 먹색 반투명 띠 GUI.DrawTexture(r, white); GUI.color = Color.white;
            GUI.Label(r, npcs.Subtitle, st);
        }
        // (3) 장부(넋·기억·엽전·업)와 안내
        var small = new GUIStyle(GUI.skin.label) { fontSize = 16 };
        small.normal.textColor = new Color(1, 1, 1, 0.9f);
        if (ui == null)
        {
            GUI.Label(new Rect(12, 30, 700, 24),
                "넋 " + ledger.Neok + "   기억 " + ledger.Memory + "   엽전 " + ledger.Coin +
                "   업 " + (weather.Fx.HideKarma ? "?" : ledger.Karma + " (" + CoreRules.KarmaTier(ledger.Karma) + "단계)") +
                (chainLeft > 0f ? "   연쇄!" : ""), small);
            GUI.Label(new Rect(12, 74, 700, 24), "체력 " + ledger.Hp + " / " + ledger.MaxHp + "   회복약 " + dayScreen.Pack.Heal + " (H)" +
                (Demo.Weapons ? "   무기 " + lo.Def.Name + " (Tab)" + (lo.Def.HasQuake ? "  Q 땅울림" + (lo.quakeCd > 0f ? " " + Mathf.CeilToInt(lo.quakeCd) + "s" : "") : "") : "") +
                (Demo.Gear ? "   능력치 점수 " + StatPoints.Earned(ledger.Neok) : ""), small);
        }
        // 시연판 기본 구성에서는 도술·장비 표시를 숨긴다 (기능은 DEMO_* 로 켜면 그대로 나온다)
        if (SkillsOn && ui == null)   // 새 HUD 가 하단 스킬바에 그리면 중복·겹침이라 건너뜀
        {
            string sk = "";
            for (int i = 0; i < SkillTree.ActiveSlots; i++)
            {
                string an = ActiveNameAt(i); if (an == null) continue;
                sk += (i + 1) + ":" + an + (lo.active.Ready(an) ? "" : "(" + Mathf.CeilToInt(lo.active.Left(an)) + "s)") + "   ";
            }
            GUI.Label(new Rect(12, 122, 800, 24), sk, small);   // 96줄(밤·천도·단서)과 겹치지 않게 아래로(PC 검증 지적)
        }
        if (Demo.Gear)
        {
            GUI.Label(new Rect(12, 148, 900, 24), "장비  무기:" + GearName(Slot.Weapon) + "  도포:" + GearName(Slot.Robe) + "  노리개:" + GearName(Slot.Charm), small);
            if (lo.lastDropT > 0f) GUI.Label(new Rect(12, 170, 900, 24), lo.lastDrop, small);
            // 장비 아이콘 세 칸 (그림이 있을 때만): 등급 테두리 + 칸별 아이콘
            for (int si = 0; si < 3; si++) DrawGearIcon((Slot)si, new Rect(12 + si * 56, 198, 52, 52));
        }
        if (ui == null) GUI.Label(new Rect(12, 52, 700, 24), "E: 천도(넋을 보냄)   R: 파혼(넋을 깸)", small);
        if (ui == null)
        {
            GUI.Label(new Rect(12, 96, 700, 24),
                "밤 " + Mathf.CeilToInt(night.TimeLeft) + "초   천도 " + night.Sent + "/" + Balance.NIGHT_QUOTA +
                "   단서 " + night.Clues + "/" + Balance.BOSS_CLUES_REQUIRED + (night.BossDone ? "   나루 영감 끝" : "") + (night.QuotaDone ? "  (당집으로 돌아가라!)" : "") + (night.Warning ? "   동이 튼다!" : ""), small);
        }
        if (night.Over)
        {
            GUI.color = new Color(0, 0, 0, 0.75f); GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), white); GUI.color = Color.white;
            var h = new GUIStyle(GUI.skin.label) { fontSize = 34, alignment = TextAnchor.MiddleCenter }; h.normal.textColor = Color.white;
            var m = new GUIStyle(h) { fontSize = 22 };
            bool ok = night.Phase == NightPhase.Returned;
            GUI.Label(new Rect(0, Screen.height * 0.25f, Screen.width, 50), ok ? "밤을 넘겼다" : "동이 트고 말았다", h);
            GUI.Label(new Rect(0, Screen.height * 0.25f + 60, Screen.width, 190),
                "천도 " + night.Sent + "   지킨 넋 " + night.FinalNeok + (night.LostNeok > 0 ? "   잃은 넋 " + night.LostNeok : "") + (night.LostCoin > 0 ? "   잃은 엽전 " + night.LostCoin : "") +
                "\n엽전 " + ledger.Coin + "   업 " + ledger.Karma + "   기억 " + ledger.Memory +
                "\n나루 영감 " + (night.BossDone ? "끝" : "-") + "   단서 " + night.Clues + "/" + Balance.BOSS_CLUES_REQUIRED +
                "   장비 무기:" + GearName(Slot.Weapon) + " 도포:" + GearName(Slot.Robe) + " 노리개:" + GearName(Slot.Charm) +
                (night.Phase == NightPhase.Returned ? "" : "\n(몫만큼은 지켰고, 그 너머의 수확은 흩어졌다)"), m);
            if (Demo.Day)
            {
                if (GUI.Button(new Rect(Screen.width / 2f - 200, Screen.height * 0.25f + 260, 190, 70), "낮으로 (D)")) StartDay();
                if (GUI.Button(new Rect(Screen.width / 2f + 10, Screen.height * 0.25f + 260, 190, 70), "다시 (Space)")) RestartNight();
            }
            else if (GUI.Button(new Rect(Screen.width / 2f - 90, Screen.height * 0.25f + 260, 180, 70), "다시 (Space)")) RestartNight();
            return;
        }
        if (Casting && ui == null)
        {
            var bar = new Rect(Screen.width / 2f - 80, Screen.height * 0.72f, 160, 12);   // 스킬바·처결 카드 위(도술 칸을 가리지 않게)
            GUI.color = new Color(0, 0, 0, 0.7f); GUI.DrawTexture(bar, white);
            GUI.color = ChasaPalette.CheondoGlow;
            GUI.DrawTexture(new Rect(bar.x + 1, bar.y + 1, 158f * Mathf.Clamp01(castT / castTotal), 10), white);
            GUI.color = Color.white;
        }
        if (Balance.DODGE_ENABLED && ui == null)   // 새 HUD 가 아래쪽 기술 줄에 그리면 중복이라 예전 칸은 숨긴다
        {
            // 피하기 충전 표시: 작은 막대 2개(채워지는 중이면 부분만 찬다). 글자 없이 도형이라 글꼴 걱정이 없다
            for (int i = 0; i < Balance.DODGE_CHARGES; i++)
            {
                float fill = Mathf.Clamp01(player.DodgeCharges - i);
                var r = new Rect(Screen.width / 2f - 34 + i * 36, Screen.height - 66, 32, 8);
                GUI.color = new Color(0, 0, 0, 0.6f); GUI.DrawTexture(r, white);
                GUI.color = fill >= 1f ? new Color(0.75f, 0.85f, 1f) : new Color(0.45f, 0.5f, 0.6f);
                GUI.DrawTexture(new Rect(r.x + 1, r.y + 1, 30f * fill, 6), white);
                GUI.color = Color.white;
            }
        }
        if (toastT > 0f && ui == null)
        {
            var big = new GUIStyle(GUI.skin.label) { fontSize = 22, alignment = TextAnchor.MiddleCenter };
            big.normal.textColor = Color.white;
            GUI.Label(new Rect(0, Screen.height * 0.28f, Screen.width, 40), toast, big);
        }
        // (4) 터치 버튼 (폰에는 키보드가 없다)
        if (Ko.TouchUI)
        {
            var bs = new GUIStyle(GUI.skin.button) { fontSize = 20 };
            var sbs = new GUIStyle(bs) { fontSize = 13, wordWrap = true };   // 도술 이름이 길어 작은 글씨로
            // 천도·파혼은 '무릎 꿇은 혼이 가까이 있을 때만' 켜진다(평소엔 흐리고 눌러도 안 됨 → 전투 중 오터치 방지)
            bool nearKneel = AnyKneelNearby(out bool nearTendo);
            bool wasEnabled = GUI.enabled;
            GUI.enabled = wasEnabled && nearTendo;
            // 아트 버튼 그림(천도 청록·파혼 주황)이 있으면 그림 위에 투명 버튼을 얹는다. 없으면 옛 글자 버튼
            var artBs = new GUIStyle(bs);
            artBs.normal.background = null; artBs.hover.background = null; artBs.active.background = null; artBs.focused.background = null;
            artBs.normal.textColor = Color.white; artBs.fontSize = 18; artBs.alignment = TextAnchor.LowerCenter;
            // 폰 천도·파혼(기획 §5): 하단 가운데 지름 120px 둘을 같은 크기로 나란히(중심에서 ±110px, 아래 64px). 무릎 꿇은 혼이 가까울 때만 나타난다
            float bs1 = Screen.height / 1080f, bd = 120f * bs1;
            var rT = new Rect(Screen.width * 0.5f - 110f * bs1 - bd * 0.5f, Screen.height - 64f * bs1 - bd, bd, bd);
            var rP = new Rect(Screen.width * 0.5f + 110f * bs1 - bd * 0.5f, Screen.height - 64f * bs1 - bd, bd, bd);
            bool showJudge = nearKneel || nearTendo || Casting;
            TouchControls.JudgeRects = showJudge ? new[] { rT, rP } : null;   // 조이스틱보다 먼저 눌리게 GameMain 에 알린다
            if (showJudge)
            {
            bool artT = DrawArt(rT, TouchHeld(rT) && nearTendo ? "ui_btn_cheondo_pressed" : "ui_btn_cheondo", nearTendo);
            if (GUI.Button(rT, "천도", artT ? artBs : bs)) CommandTendo();
            if (Casting && artT)   // 길게 누르기 고리: 천도 시전이 진행될수록 버튼 둘레 고리가 진해지며 커진다(원형 채움은 못 써서 투명도+크기로 대신)
            {
                float cp = Mathf.Clamp01(castT / Mathf.Max(0.01f, castTotal)), rs2 = bd * (0.9f + 0.2f * cp);
                DrawArt(new Rect(rT.center.x - rs2 * 0.5f, rT.center.y - rs2 * 0.5f, rs2, rs2), "ui_btn_hold_ring", true, 0.35f + 0.65f * cp);
            }
            GUI.enabled = wasEnabled && nearKneel;
            bool artP = DrawArt(rP, TouchHeld(rP) && nearKneel ? "ui_btn_pahon_pressed" : "ui_btn_pahon", nearKneel);
            if (GUI.Button(rP, "파혼", artP ? artBs : bs)) CommandPahon();
            GUI.enabled = wasEnabled;
            }
            if (!TouchControls.Active && SoulPathStop() >= 0 && GUI.Button(new Rect(292, Screen.height - 110, 110, 90), "넋길", bs)) CommandSoulPath();   // 서낭당 곁 밤에만 나타난다
            // 도술 세 칸과 무기 바꾸기 (위쪽 줄) — 시연판 기본 구성에서는 숨김
            if (SkillsOn && !TouchControls.Active)   // 폰 도술은 새 부채꼴 버튼(TouchControls)이 맡는다
                for (int i = 0; i < SkillTree.ActiveSlots; i++)
                {
                    string an = ActiveNameAt(i); if (an == null) continue;
                    bool rdy = lo.active.Ready(an);
                    var rs = new Rect(24 + i * 94, Screen.height - 206, 86, 80);
                    // 아트 도술 칸: 틀 + 갈래 아이콘 + 대기 덮개 위에 투명 버튼. 그림이 없으면 옛 글자 버튼
                    bool artS = DrawArt(rs, "ui_skill_slot", true);
                    if (artS)
                    {
                        DrawArt(new Rect(rs.x + 14, rs.y + 8, 58, 58), SpriteLib.Texture("ui/" + UiRoot.SkillIcon(an)) != null ? UiRoot.SkillIcon(an) : "ui_skill_slot", true);
                        if (!rdy) DrawArt(rs, "ui_skill_slot_cool", true, 0.4f + 0.6f * lo.active.Ratio(an));
                        var kb = new GUIStyle(sbs); kb.normal.background = null; kb.hover.background = null; kb.active.background = null; kb.normal.textColor = Color.white; kb.alignment = TextAnchor.UpperLeft;
                        if (GUI.Button(rs, (i + 1) + (rdy ? "" : "   " + Mathf.CeilToInt(lo.active.Left(an))), kb)) UseSkill(i);
                    }
                    else if (GUI.Button(rs, (i + 1) + "\n" + an + (rdy ? "" : "\n" + Mathf.CeilToInt(lo.active.Left(an)) + "s"), sbs)) UseSkill(i);
                }
            if (Demo.Weapons && GUI.Button(new Rect(24 + 4 * 94, Screen.height - 206, 86, 80), "교체", bs)) player.CommandSwap();
            if ((Demo.Panel || FieldRules.On) && GUI.Button(new Rect(24 + 5 * 94, Screen.height - 206, 86, 80), "메뉴", bs)) panel.Toggle();
            if (Demo.Weapons && lo.Def.HasQuake && GUI.Button(new Rect(24 + 6 * 94, Screen.height - 206, 86, 80), "땅울림", bs)) player.CommandQuake();
        }
    }

    /// <summary>Resources/Sprites/ui 그림을 IMGUI 위에 그린다(화면 비율 유지). 그림이 없으면 false — 부르는 쪽이 옛 버튼으로 대신한다</summary>
    static bool DrawArt(Rect r, string name, bool on, float alpha = 1f)
    {
        var t = SpriteLib.Texture("ui/" + name); if (t == null) return false;
        var c = GUI.color; GUI.color = new Color(1f, 1f, 1f, (on ? 1f : 0.45f) * alpha);   // 눌러도 안 되는 버튼은 흐리게
        GUI.DrawTexture(r, t, ScaleMode.ScaleToFit); GUI.color = c;
        return true;
    }

    /// <summary>지금 이 영역을 누르고 있나(눌림 그림으로 바꾸려고)</summary>
    static bool TouchHeld(Rect r)
    {
        var e = Event.current; if (e == null) return false;
        if (Input.touchCount > 0) { for (int i = 0; i < Input.touchCount; i++) { var tp = Input.GetTouch(i).position; if (r.Contains(new Vector2(tp.x, Screen.height - tp.y))) return true; } return false; }
        return Input.GetMouseButton(0) && r.Contains(new Vector2(Input.mousePosition.x, Screen.height - Input.mousePosition.y));
    }
}
