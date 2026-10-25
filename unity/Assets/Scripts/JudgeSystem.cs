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
    public Camera cam;

    CharacterPanel panel;
    Loadout lo => player.loadout;                // 든 무기·도술·장비 (Player 가 소유)
    public readonly Ledger ledger = new Ledger();
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
    public float CastZoom { get { return visionP; } }   // 카메라가 캐스팅 중 다가가는 정도(0~1)
    float visionP;                       // 0(평소) ~ 1(캐스팅 중): 시야 축소·기억색 정도. 0.2초에 걸쳐 부드럽게 변한다
    string toast = ""; float toastT;     // 화면 안내 글자(영문: 기본 글꼴에 한글이 없다)
    Texture2D white, vignette;
    public bool godMode;                        // ?debug 검증용: 체력이 줄지 않는다
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
        // 서낭당: 출발점이자 귀환점. 납작한 노란 원으로 '돌아갈 곳'을 보여 준다
        shrineView = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        Destroy(shrineView.GetComponent<Collider>());
        shrineView.GetComponent<Renderer>().sharedMaterial = U.Matte(ChasaPalette.CheondoGlow);
        shrineView.transform.position = new Vector3(0, 0.015f, 0);
        shrineView.transform.localScale = new Vector3(Balance.SHRINE_RADIUS * 2f, 0.01f, Balance.SHRINE_RADIUS * 2f);
        panel = gameObject.AddComponent<CharacterPanel>();   // C 키 캐릭터 창(장비·도술·능력치)
        panel.judge = this;
        enemies.onPlayerHit = OnPlayerHit;
        player.onDodgeCancelCast = () => { if (Casting) { castTarget.soul.CancelSending(); EndCast(); Say("천도를 거두고 피했다"); } };   // 천도 중 피하기: 캐스팅만 취소, 혼은 무릎 꿇은 채 대기
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

    /// <summary>첫 입력이 있었던 것으로 친다(자동 연출·검증용). 이 전엔 적이 공격하지 않는다</summary>
    public void StartPlaying() { if (!played) { played = true; enemies.graceT = Balance.NIGHT_GRACE; } }

    // ===== 명령 ====================================================================
    public void CommandTendo()
    {
        if (Casting || !player.CanActNow()) return;
        // 천도는 보낼 수 있는 혼 중 가장 가까운 것을 고른다 — 곁에 덩어리(천도 불가)가 있어도 막히지 않게(QA)
        var e = enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE, x => x.soul.CanTendoWith(night.Clues));
        if (e == null) e = enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE);   // 없으면 가장 가까운 혼으로 이유를 안내
        if (e == null) { Say("대상이 없다"); return; }
        if (!e.soul.CanTendo) { Say("보낼 수 없는 넋 - 파혼만 가능"); return; }
        if (!e.soul.CanTendoWith(night.Clues)) { Say("단서 " + Balance.BOSS_CLUES_REQUIRED + "개가 필요하다 (" + night.Clues + ") - 파혼만 가능"); return; }
        if (!e.soul.BeginSending()) return;
        player.ConsumeAct();   // 후딜·피하기를 끊고 천도 시작
        castTarget = e;
        castT = 0f;
        castTotal = e.soul.Boss ? Balance.BOSS_TENDO_CAST_TIME : CoreRules.CastTimeScaled(chainLeft > 0f, lo.stats.CastMult);   // 연속 천도면 0.8초, 보스는 2.0초
        player.locked = true;
        player.facing = Mathf.Atan2(e.Pos.z - player.Pos.z, e.Pos.x - player.Pos.x);
    }

    /// <summary>이 혼을 지금 천도할 수 있나(덩어리·단서 부족이면 아니오). 데모가 대상을 고를 때 쓴다</summary>
    public bool CanTendoNow(Enemy e) { return e != null && e.soul.CanTendo && e.soul.CanTendoWith(night.Clues); }

    public void CommandPahon()
    {
        if (Casting || !player.CanActNow()) return;
        var e = enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE);
        if (e == null) { Say("대상이 없다"); return; }
        if (!e.soul.TryPahon()) return;
        player.ConsumeAct();   // 후딜·피하기를 끊고 파혼
        DoPahon(e);
        player.actLock = Balance.PAHON_RECOVER;   // 파혼 끝동작 0.25초
    }

    void DoPahon(Enemy e)
    {
        var at = e.Pos;
        e.Finish();
        int coinBefore = ledger.Coin;
        ledger.DoPahon(e.soul.Boss);
        // 엽전 장비 보너스(엽전 +%)와 향 내음의 마이너스(파혼 엽전 −50%)를 곱해 반영 (음수면 깎인다)
        float baseCoin = e.soul.Boss ? Balance.BOSS_PAHON_COIN : Balance.PAHON_COIN;
        ledger.Coin += Mathf.RoundToInt(baseCoin * lo.stats.CoinMult * lo.stats.PahonCoinMult - baseCoin);
        night.RecordCoin(ledger.Coin - coinBefore);   // 몫 달성 전/후로 나눠 쌓는다
        if (e.soul.Boss)
        {
            night.BossDone = true; Say("나루 영감을 깨뜨렸다");
            // 보스 파혼 보상: 이름 있는 물건 (즉시 강해진다 vs 천도의 기억/넋) — 기획서 6-1
            if (Demo.Gear && lo.Equip(ItemDef.MoonflowerBell())) { lo.lastDrop = "이름 있는 장비: 월화 방울 (파혼 반경 +)"; lo.lastDropT = 6f; }
        }
        // 폭발: 반경 안 싸우는 적에게 피해 + 바깥으로 넉백. 거리(2.5m)를 속도로 바꾸려면 마찰을 곱한다
        float kb = Balance.PAHON_KNOCKBACK_DIST * Config.ENEMY_KNOCKBACK_FRICTION * lo.Def.PahonKnockbackMult * lo.stats.PahonKnockbackMult;   // 육모방망이는 더 멀리 날린다
        float radius = lo.stats.PahonRadius(Balance.PAHON_RADIUS);   // 업 쪽 장비: 파혼 반경 (상한 안)
        int pahonDmg = Mathf.RoundToInt(Balance.PAHON_DAMAGE * lo.Def.PahonDamageMult * lo.stats.PahonDamageMult);
        foreach (var o in enemies.list)
        {
            if (o == e || !o.alive) continue;
            var d = new Vector3(o.Pos.x - at.x, 0, o.Pos.z - at.z);
            if (d.magnitude > radius + o.radius) continue;
            var dir = d.magnitude > 0.01f ? d.normalized : Vector3.right;
            o.TakeHit(pahonDmg, dir, kb, 0.3f);
            numbers.Spawn(o.HeadPosition, pahonDmg, "heavy");
        }
        feel.HitStop(Balance.PAHON_HITSTOP_FRAMES);
        Sfx.Play("sfx.pahon.burst");
        feel.AddShake(Balance.PAHON_SHAKE);
        feel.AddZoom(1f);                       // 파혼: 확 다가가는 쿵
        flashColor = new Color(0.55f, 0.05f, 0.08f); flashA = 0.55f;   // 붉은 번쩍임(깨뜨림)
        // 원념 얼룩: 3개가 겹치면 그 자리에서 사나운 적이 솟는다
        float cx, cz;
        if (stains.Add(at.x, at.z, out cx, out cz))
        {
            enemies.SpawnFierce(new Vector3(cx, 0, cz));
            Say("사나운 넋이 깨어났다!");
        }
    }

    void FinishTendo()
    {
        castTarget.Finish();
        if (castTarget.soul.Boss)
        {
            int g = ledger.CompleteBossTendo();
            night.RecordBoss(g);                    // 보스 보상은 '추가 수확분' — 동이 트면 잃는다
            enemySpawnPause = Balance.BOSS_CAST_ADD_PAUSE;
            Say("나루 영감을 천도했다!");
        }
        else
        {
            int before = ledger.Neok;
            ledger.CompleteTendo();
            ledger.Neok += Mathf.RoundToInt((ledger.Neok - before) * (lo.stats.TendoNeokMult - 1f));   // 향 내음: 천도 넋 보너스
            night.RecordTendo(ledger.Neok - before);   // 몫인지 추가 수확분인지 나눠 쌓는다
            if (castTarget.soul.Name != null) namedTendoed = true;   // 이름혼을 보냈다 → 다음 낮 장례
            if (night.TakeNamedSpawn()) SpawnNamedSoul();   // 몫의 마지막 하나는 이름혼 박돌쇠
        }
        chainLeft = lo.stats.ChainWindow;   // 젖은 소매가 있으면 창이 길다
        feel.AddShake(0.15f);
        Sfx.Play("sfx.tendo.done");
        feel.SlowMo(Balance.TENDO_COMPLETE_SLOWMO, Balance.TENDO_COMPLETE_SLOWMO_SCALE);   // 멈춤이 아니라 느림 = 보냄
        feel.AddZoom(-0.7f);                    // 천도 완료: 숨을 내쉬듯 화면이 살짝 멀어졌다 돌아온다
        flashColor = new Color(0.85f, 0.8f, 1f); flashA = 0.5f;        // 흰 보랏빛 번쩍임(보냄)
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
    void OnEnemyKneel(Enemy e)
    {
        Sfx.Play("sfx.kneel");   // 무릎 꿇는 소리 = '지금 고를 때'
        // 검은 술: 무릎 꿇은 혼의 대기 시간이 짧아진다 (덩어리는 제외, 최소 WAIT_FLOOR)
        if (!e.soul.Boss && e.soul.State == SoulState.Kneel)
        {
            e.soul.WaitTotal = lo.stats.AdjustWait(e.soul.WaitTotal, e.soul.Kind == SoulKind.Lump);
            e.soul.WaitLeft = e.soul.WaitTotal;
        }
        if (!Demo.Gear) return;   // 시연판 기본 구성: 장비 드롭 없음
        var it = Loot.Roll(() => Random.value, e.soul.Fierce);
        if (it == null) return;
        string txt = Loadout.Describe(it);
        if (lo.Equip(it))
        {
            ledger.SetMaxHp(lo.stats.MaxHp);
            lo.lastDrop = "획득·장착: " + txt;
        }
        else lo.lastDrop = "획득(더 나쁨, 두고 감): " + txt;
        lo.lastDropT = 5f;
        TimedSprite.Spawn("fx/loot_" + (it.Named ? "named" : it.Rarity == Rarity.Rare ? "rare" : it.Rarity == Rarity.Crafted ? "crafted" : "common"), e.Pos, 3f);   // 드롭 빛줄기
    }

    /// <summary>도술 1·2·3. 쿨다운 중이거나 무릎 꿇은 혼이 없는 등 효과가 없으면 쿨다운을 쓰지 않는다</summary>
    public void UseSkill(int slot)
    {
        if (!Demo.Skills || night.Over || ledger.Dead || Casting || !lo.skills.Ready(slot)) return;
        switch (slot)
        {
            case 0: // 붙잡아 부르기: 무릎 꿇은 혼 대기 +3초, 서 있는 적 0.8초 멈칫
            {
                int n = 0;
                foreach (var e in enemies.list)
                {
                    if (new Vector2(e.Pos.x - player.Pos.x, e.Pos.z - player.Pos.z).magnitude > Balance.SKILL_HOLD_RADIUS) continue;
                    if (e.kneeling) { e.soul.WaitLeft += Balance.SKILL_HOLD_WAIT_BONUS; e.soul.WaitTotal += Balance.SKILL_HOLD_WAIT_BONUS; n++; }
                    else if (e.alive) { e.stun = Mathf.Max(e.stun, Balance.SKILL_HOLD_STUN); e.atk.Interrupt(); n++; }
                }
                if (n == 0) { Say("범위 안에 아무도 없다"); return; }
                GroundFx.Play(player.Pos, Balance.SKILL_HOLD_RADIUS, "fx/fx_call_", 3, 0.7f);
                Say("붙잡아 부르기");
                break;
            }
            case 1: // 휘감기: 반경 4m 서 있는 적 1.5초 묶기
            {
                int n = 0;
                foreach (var e in enemies.list)
                {
                    if (!e.alive || new Vector2(e.Pos.x - player.Pos.x, e.Pos.z - player.Pos.z).magnitude > Balance.SKILL_BIND_RADIUS + e.radius) continue;
                    e.stun = Mathf.Max(e.stun, Balance.SKILL_BIND_STUN); e.atk.Interrupt(); e.vel = Vector3.zero; n++;
                }
                if (n == 0) { Say("범위 안에 아무도 없다"); return; }
                GroundFx.Play(player.Pos, Balance.SKILL_BIND_RADIUS, "fx/fx_bind_", 3, 0.6f);
                Say("휘감기");
                break;
            }
            default: // 터뜨리기: 가까운 얼룩 하나를 터뜨려 지운다(업 그대로), 반경 2.5m 맺힘 40
            {
                float sx, sz;
                if (!stains.RemoveNearest(player.Pos.x, player.Pos.z, Balance.SKILL_BURST_FIND_RANGE, out sx, out sz)) { Say("터뜨릴 얼룩이 없다"); return; }
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
                Say("터뜨리기");
                break;
            }
        }
        lo.skills.TryUse(slot);   // 효과가 있었을 때만 쿨다운을 쓴다
    }

    // ===== M4: 이름혼·보스·단서 ======================================================
    void SpawnNamedSoul()
    {
        // 플레이어 앞쪽 7m 에서 나타난다 (길 위, 집 밖)
        var at = new Vector3(MapLayout.NamedX, 0, MapLayout.NamedZ);   // 아트 배치표가 정한 자리
        enemies.SpawnNamed(at, "박돌쇠");
        Say("명부에 오른 이름이 나타났다...");
    }

    /// <summary>한 판 시작: 마을 어귀에 보스, 마을 곳곳에 단서 3개</summary>
    void SetupNight()
    {
        enemies.SpawnBoss(new Vector3(MapLayout.BossX, 0, MapLayout.BossZ));
        cluePos.Clear();
        foreach (var v in clueViews) Destroy(v);
        clueViews.Clear();
        foreach (var cp in MapLayout.CluePoints())
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
    void OnPlayerHit(Enemy by)
    {
        if (ledger.Dead || night.Over || !player.Hurt()) return;
        // 상복 자락: 천도 시전 중에 맞으면 피해가 줄어든다
        int incoming = Casting ? Mathf.Max(1, Mathf.RoundToInt(by.damage * lo.stats.CastDamageTakenMult)) : by.damage;
        sinceHit = 0f;
        Sfx.Play("sfx.player.hurt");
        int dealt = godMode ? 0 : ledger.TakeDamage(incoming);
        numbers.Spawn(player.Pos + Vector3.up * 2f, dealt, "heavy");
        feel.AddShake(Balance.TRAUMA_PLAYER_HIT);
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

    void Say(string s) { toast = s; toastT = 1.5f; }

    // ===== 매 프레임 ===============================================================
    public void Tick(float dt, float realDt)
    {
        toastT -= realDt;   // 안내 글자는 창이 열려 있어도 사라진다(QA B3)
        if (CharacterPanel.Open) return;   // 캐릭터 창이 열려 있으면 세계가 멈춘다
        if (inDay)
        {
            dayScreen.Tick(realDt);
            if (dayScreen.WantsNight) { inDay = false; RestartNight(); }   // 해 넘기기 → 새 밤
            return;
        }
        if (!played && (Input.anyKeyDown || Input.GetMouseButtonDown(0) || Input.touchCount > 0)) { played = true; enemies.graceT = Balance.NIGHT_GRACE; }
        enemies.holdFire = !played;
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
        night.Tick(dt);
        TickClues();
        enemySpawnPause = Mathf.Max(0f, enemySpawnPause - dt);
        enemies.spawnPaused = enemySpawnPause > 0f || (Casting && castTarget.soul.Boss);   // 보스 천도 중·직후엔 잡몹이 새로 나오지 않는다
        // 귀환: 서낭당 위에 서면 즉시. 단 출발 직후(몫을 하나도 못 채움)에는 자동 귀환하지 않는다 — 밤을 시작도 못 하고 끝나는 것 방지
        float toShrine = new Vector2(player.Pos.x, player.Pos.z).magnitude;
        if (night.QuotaDone && night.TryReturn(toShrine)) Say("귀환했다!");
        chainLeft = Mathf.Max(0f, chainLeft - dt);
        stains.Tick(dt);
        flashA = Mathf.Max(0f, flashA - realDt * 2.2f);
        sinceHit += dt;
        ledger.Regen(dt, toShrine <= Balance.SHRINE_RADIUS, sinceHit);   // 서낭당 안: 빠른 회복 / 밖: 맞지 않으면 천천히
        player.speedMult = stains.IsOnStain(player.Pos.x, player.Pos.z) ? 1f - Balance.STAIN_SLOW : 1f;   // 얼룩 위: -20%

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

    void HandleKeys()
    {
        if (Input.GetKeyDown(KeyCode.E)) CommandTendo();
        if (Input.GetKeyDown(KeyCode.Alpha1)) UseSkill(0);
        if (Input.GetKeyDown(KeyCode.Alpha2)) UseSkill(1);
        if (Input.GetKeyDown(KeyCode.Alpha3)) UseSkill(2);
        if (Input.GetKeyDown(KeyCode.Tab)) player.CommandSwap();
        // 공물상에서 산 소모품: H = 회복약, X = 밟고 선 얼룩 지우기(씻김 부적)
        if (Input.GetKeyDown(KeyCode.H) && Shrine.UseHeal(ledger, dayScreen.Pack)) Say("회복약을 마셨다");
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
        bool art = SpriteLib.Texture("fx/stain_0") != null;   // 아트 얼룩 그림이 있으면 그것으로, 없으면 색 원기둥으로
        while (stainViews.Count < snap.Count)
        {
            GameObject go;
            if (art) go = GroundFx.Persistent(Vector3.zero, Balance.STAIN_RADIUS, "fx/stain_0");
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
            if (art)
            {
                // 그림 얼룩은 같은 크기에서 점점 작아진다 (그림 쿼드의 기본 크기는 반경 STAIN_RADIUS 기준)
                stainViews[i].transform.position = new Vector3(snap[i][0], 0.02f + i * 0.002f, snap[i][1]);
                stainViews[i].transform.localScale = new Vector3(fade, 1f, fade);
            }
            else
            {
                float d = Balance.STAIN_RADIUS * 2f * fade;
                stainViews[i].transform.position = new Vector3(snap[i][0], 0.02f + i * 0.002f, snap[i][1]);
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
        string icon = it.Named ? "icon_named_wolhwa_bell" : "icon_" + (s == Slot.Weapon ? "weapon" : s == Slot.Robe ? "dopo" : "noriga") + "_" + rar;
        var tex = SpriteLib.Texture("icons/" + icon);
        var frame = SpriteLib.Texture("icons/frame_" + rar);
        if (tex != null) GUI.DrawTexture(r, tex);
        if (frame != null) GUI.DrawTexture(r, frame);
    }

    string GearName(Slot s)
    {
        var it = lo.gear.Get(s);
        return it == null ? "-" : Ko.ItemName(it) + "/" + it.Options.Count;
    }

    // ===== 화면 ====================================================================
    /// <summary>화면에 보일 값을 모아(HudState) 새 화면(UI Toolkit)에 넘긴다</summary>
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
        h.TimeOfDay = Mathf.Clamp01(1f - night.TimeLeft / Mathf.Max(1f, Balance.NIGHT_DURATION)); h.IsDawn = night.Warning;
        h.Neok = ledger.Neok; h.Memory = ledger.Memory; h.Coin = ledger.Coin; h.Karma = ledger.Karma; h.ChainBonus = chainLeft > 0f;
        h.Hp = ledger.Hp; h.MaxHp = ledger.MaxHp; h.Heal = dayScreen.Pack.Heal;
        h.SecondsLeft = Mathf.CeilToInt(night.TimeLeft); h.Sent = night.Sent; h.Quota = Balance.NIGHT_QUOTA;
        h.Clues = night.Clues; h.CluesNeeded = Balance.BOSS_CLUES_REQUIRED;
        h.BossDone = night.BossDone; h.QuotaDone = night.QuotaDone; h.Warning = night.Warning;
        h.DodgeCharges = player.DodgeCharges; h.DodgeMax = Balance.DODGE_CHARGES; h.PullCd = player.PullCooldown; h.WeaponName = lo.Def.Name;
        // 얻은 것 알림: 장부 값이 늘어난 만큼 쪽지를 띄운다(같은 글은 합쳐진다). 낮 화면을 넘어온 첫 프레임엔 띄우지 않는다
        if (toastReady)
        {
            if (ledger.Neok > pNeok) h.Toasts.Add("넋 +" + (ledger.Neok - pNeok));
            if (ledger.Memory > pMemory) h.Toasts.Add("기억 +" + (ledger.Memory - pMemory));
            if (ledger.Coin > pCoin) h.Toasts.Add("엽전 +" + (ledger.Coin - pCoin));
            if (ledger.Karma > pKarma) h.Toasts.Add("업 +" + (ledger.Karma - pKarma));
            if (lo.lastDropT > 0f && lo.lastDrop != pDrop) h.Toasts.Add(lo.lastDrop);
        }
        pNeok = ledger.Neok; pMemory = ledger.Memory; pCoin = ledger.Coin; pKarma = ledger.Karma; pDrop = lo.lastDrop; toastReady = true;
        h.Toasts.Tick(Time.unscaledDeltaTime);
        ui.Refresh(!inDay && !night.Over && !CharacterPanel.Open);
    }
    int pNeok, pMemory, pCoin, pKarma; string pDrop; bool toastReady;

    /// <summary>화면 가장자리 경고: 공격 준비 중인 적이 화면 밖이거나(천도 중이면) 좁아진 시야 밖이면 방향 표시를 띄운다</summary>
    void FillEdges(HudState h)
    {
        h.Edges.Clear();
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
                h.Edges.Add(new EdgeMark { Nx = ex / w, Ny = ey / hh });
        }
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
        if (CharacterPanel.Open) return;   // 캐릭터 창이 열리면 밤 화면 글자·버튼은 그리지 않는다(QA B2)
        if (inDay) { dayScreen.OnGUI(white); return; }   // 낮 화면이 모든 것을 덮는다
        // (0) 화면 번쩍임: 천도/파혼 순간의 색
        if (flashA > 0.001f) { GUI.color = new Color(flashColor.r, flashColor.g, flashColor.b, flashA); GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), white); GUI.color = Color.white; }
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
                GUI.Label(new Rect(sp.x - 80, Screen.height - sp.y - 12, 160, 24), e.soul.Boss ? "나루 영감" : e.label, nameStyle);
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
                if (!named && so.Maedhim >= so.MaedhimMax) continue;
                var sp = cam.WorldToScreenPoint(e.HeadPosition + Vector3.up * 0.3f);
                if (sp.z < 0f) continue;
                float ratio = Mathf.Clamp01((float)so.Maedhim / Mathf.Max(1, so.MaedhimMax));
                int rows = so.Kind == SoulKind.Lump ? 2 : 1;
                float wBar = named ? 72f : 56f;
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
        // (3) 장부(넋·기억·엽전·업)와 안내
        var small = new GUIStyle(GUI.skin.label) { fontSize = 16 };
        small.normal.textColor = new Color(1, 1, 1, 0.9f);
        if (ui == null)
        {
            GUI.Label(new Rect(12, 30, 700, 24),
                "넋 " + ledger.Neok + "   기억 " + ledger.Memory + "   엽전 " + ledger.Coin +
                "   업 " + ledger.Karma + " (" + CoreRules.KarmaTier(ledger.Karma) + "단계)" +
                (chainLeft > 0f ? "   연쇄!" : ""), small);
            GUI.Label(new Rect(12, 74, 700, 24), "체력 " + ledger.Hp + " / " + ledger.MaxHp + "   회복약 " + dayScreen.Pack.Heal + " (H)" +
                (Demo.Weapons ? "   무기 " + lo.Def.Name + " (Tab)" + (lo.Def.HasQuake ? "  Q 땅울림" + (lo.quakeCd > 0f ? " " + Mathf.CeilToInt(lo.quakeCd) + "s" : "") : "") : "") +
                (Demo.Gear ? "   능력치 점수 " + StatPoints.Earned(ledger.Neok) : ""), small);
        }
        // 시연판 기본 구성에서는 도술·장비 표시를 숨긴다 (기능은 DEMO_* 로 켜면 그대로 나온다)
        if (Demo.Skills)
        {
            string sk = "";
            for (int i = 0; i < 3; i++)
                sk += (i + 1) + ":" + SkillDef.All[i].Name + (lo.skills.Ready(i) ? "" : "(" + Mathf.CeilToInt(lo.skills.Left[i]) + "s)") + "   ";
            GUI.Label(new Rect(12, 118, 800, 24), sk, small);
        }
        if (Demo.Gear)
        {
            GUI.Label(new Rect(12, 140, 900, 24), "장비  무기:" + GearName(Slot.Weapon) + "  도포:" + GearName(Slot.Robe) + "  노리개:" + GearName(Slot.Charm), small);
            if (lo.lastDropT > 0f) GUI.Label(new Rect(12, 162, 900, 24), lo.lastDrop, small);
            // 장비 아이콘 세 칸 (그림이 있을 때만): 등급 테두리 + 칸별 아이콘
            for (int si = 0; si < 3; si++) DrawGearIcon((Slot)si, new Rect(12 + si * 56, 190, 52, 52));
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
        if (Casting)
        {
            var bar = new Rect(Screen.width / 2f - 80, Screen.height - 90, 160, 12);
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
        if (toastT > 0f)
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
            if (GUI.Button(new Rect(24, Screen.height - 110, 110, 90), "천도", bs)) CommandTendo();
            GUI.enabled = wasEnabled && nearKneel;
            if (GUI.Button(new Rect(148, Screen.height - 110, 130, 90), "파혼", bs)) CommandPahon();
            GUI.enabled = wasEnabled;
            // 도술 세 칸과 무기 바꾸기 (위쪽 줄) — 시연판 기본 구성에서는 숨김
            if (Demo.Skills)
                for (int i = 0; i < 3; i++)
                    if (GUI.Button(new Rect(24 + i * 94, Screen.height - 206, 86, 80), (i + 1) + "\n" + SkillDef.All[i].Name, sbs)) UseSkill(i);
            if (Demo.Weapons && GUI.Button(new Rect(24 + 3 * 94, Screen.height - 206, 86, 80), "교체", bs)) player.CommandSwap();
            if (Demo.Panel && GUI.Button(new Rect(24 + 5 * 94, Screen.height - 206, 86, 80), "메뉴", bs)) panel.Toggle();
            if (Demo.Weapons && lo.Def.HasQuake && GUI.Button(new Rect(24 + 4 * 94, Screen.height - 206, 86, 80), "땅울림", bs)) player.CommandQuake();
        }
    }
}
