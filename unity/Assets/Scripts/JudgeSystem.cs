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
    float visionP;                       // 0(평소) ~ 1(캐스팅 중): 시야 축소·기억색 정도. 0.2초에 걸쳐 부드럽게 변한다
    string toast = ""; float toastT;     // 화면 안내 글자(영문: 기본 글꼴에 한글이 없다)
    Texture2D white, vignette;
    bool touchUI;
    bool debugKeys;

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
        enemies.onEnemyKneel = OnEnemyKneel;
        SetupNight();   // 적 공격이 명중하면 체력 처리로 연결
        touchUI = Input.touchSupported;
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

    // ===== 명령 ====================================================================
    public void CommandTendo()
    {
        if (Casting || player.state != Player.State.Free) return;
        var e = enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE);
        if (e == null) { Say("NO TARGET"); return; }
        if (!e.soul.CanTendo) { Say("CAN'T SEND - SHATTER ONLY"); return; }
        if (!e.soul.CanTendoWith(night.Clues)) { Say("NEED " + Balance.BOSS_CLUES_REQUIRED + " CLUES (" + night.Clues + ") - SHATTER ONLY"); return; }
        if (!e.soul.BeginSending()) return;
        castTarget = e;
        castT = 0f;
        castTotal = e.soul.Boss ? Balance.BOSS_TENDO_CAST_TIME : CoreRules.CastTimeScaled(chainLeft > 0f, lo.stats.CastMult);   // 연속 천도면 0.8초, 보스는 2.0초
        player.locked = true;
        player.facing = Mathf.Atan2(e.Pos.z - player.Pos.z, e.Pos.x - player.Pos.x);
    }

    public void CommandPahon()
    {
        if (Casting || player.state != Player.State.Free) return;
        var e = enemies.NearestKneeling(player.Pos, Balance.JUDGE_RANGE);
        if (e == null) { Say("NO TARGET"); return; }
        if (!e.soul.TryPahon()) return;
        DoPahon(e);
    }

    void DoPahon(Enemy e)
    {
        var at = e.Pos;
        e.Finish();
        int coinBefore = ledger.Coin;
        ledger.DoPahon(e.soul.Boss);
        ledger.Coin += Mathf.RoundToInt((e.soul.Boss ? Balance.BOSS_PAHON_COIN : Balance.PAHON_COIN) * (lo.stats.CoinMult - 1f));   // 엽전 장비 보너스
        night.RecordCoin(ledger.Coin - coinBefore);   // 몫 달성 전/후로 나눠 쌓는다
        if (e.soul.Boss)
        {
            night.BossDone = true; Say("BOSS SHATTERED");
            // 보스 파혼 보상: 이름 있는 물건 (즉시 강해진다 vs 천도의 기억/넋) — 기획서 6-1
            if (lo.Equip(ItemDef.MoonflowerBell())) { lo.lastDrop = "NAMED: Moonflower Bell (pahon radius +)"; lo.lastDropT = 6f; }
        }
        // 폭발: 반경 안 싸우는 적에게 피해 + 바깥으로 넉백. 거리(2.5m)를 속도로 바꾸려면 마찰을 곱한다
        float kb = Balance.PAHON_KNOCKBACK_DIST * Config.ENEMY_KNOCKBACK_FRICTION * lo.Def.PahonKnockbackMult;   // 육모방망이는 더 멀리 날린다
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
        feel.AddShake(Balance.PAHON_SHAKE);
        // 원념 얼룩: 3개가 겹치면 그 자리에서 사나운 적이 솟는다
        float cx, cz;
        if (stains.Add(at.x, at.z, out cx, out cz))
        {
            enemies.SpawnFierce(new Vector3(cx, 0, cz));
            Say("FIERCE SOUL!");
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
            Say("BOSS SENT!");
        }
        else
        {
            int before = ledger.Neok;
            ledger.CompleteTendo();
            night.RecordTendo(ledger.Neok - before);   // 몫인지 추가 수확분인지 나눠 쌓는다
            if (night.TakeNamedSpawn()) SpawnNamedSoul();   // 몫의 마지막 하나는 이름혼 박돌쇠
        }
        chainLeft = Balance.TENDO_CHAIN_WINDOW;
        feel.AddShake(0.15f);
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
        var it = Loot.Roll(() => Random.value, e.soul.Fierce);
        if (it == null) return;
        string txt = Loadout.Describe(it);
        if (lo.Equip(it))
        {
            ledger.SetMaxHp(lo.stats.MaxHp);
            lo.lastDrop = "DROP+EQUIP: " + txt;
        }
        else lo.lastDrop = "DROP (worse, left): " + txt;
        lo.lastDropT = 5f;
        TimedSprite.Spawn("fx/loot_" + (it.Named ? "named" : it.Rarity == Rarity.Rare ? "rare" : it.Rarity == Rarity.Crafted ? "crafted" : "common"), e.Pos, 3f);   // 드롭 빛줄기
    }

    /// <summary>도술 1·2·3. 쿨다운 중이거나 무릎 꿇은 혼이 없는 등 효과가 없으면 쿨다운을 쓰지 않는다</summary>
    public void UseSkill(int slot)
    {
        if (night.Over || ledger.Dead || Casting || !lo.skills.Ready(slot)) return;
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
                if (n == 0) { Say("NOTHING IN RANGE"); return; }
                GroundFx.Play(player.Pos, Balance.SKILL_HOLD_RADIUS, "fx/fx_call_", 3, 0.7f);
                Say("HOLD CALL");
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
                if (n == 0) { Say("NOTHING IN RANGE"); return; }
                GroundFx.Play(player.Pos, Balance.SKILL_BIND_RADIUS, "fx/fx_bind_", 3, 0.6f);
                Say("BIND");
                break;
            }
            default: // 터뜨리기: 가까운 얼룩 하나를 터뜨려 지운다(업 그대로), 반경 2.5m 맺힘 40
            {
                float sx, sz;
                if (!stains.RemoveNearest(player.Pos.x, player.Pos.z, Balance.SKILL_BURST_FIND_RANGE, out sx, out sz)) { Say("NO STAIN"); return; }
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
                Say("BURST");
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
        enemies.SpawnNamed(at, "Bak Dolsoe");
        Say("A NAME ON THE LIST...");
    }

    /// <summary>한 판 시작: 마을 어귀에 보스, 마을 곳곳에 단서 3개</summary>
    void SetupNight()
    {
        enemies.SpawnBoss(new Vector3(MapLayout.BossX, 0, MapLayout.BossZ));
        cluePos.Clear();
        foreach (var v in clueViews) Destroy(v);
        clueViews.Clear();
        foreach (var cell in MapLayout.ClueCells)
        {
            var p = new Vector3(MapLayout.WorldX(cell[1]), 0, MapLayout.WorldZ(cell[0]));
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
            Say("CLUE " + night.Clues + "/" + Balance.BOSS_CLUES_REQUIRED);
        }
    }

    // ===== M1: 맞음·체력·쓰러짐 ======================================================
    /// <summary>적 공격이 명중했을 때. 무적 시간이면 무시. 천도 캐스팅 중이면 끊긴다 (무방비의 대가)</summary>
    void OnPlayerHit(Enemy by)
    {
        if (ledger.Dead || night.Over || !player.Hurt()) return;
        int dealt = ledger.TakeDamage(by.damage);
        numbers.Spawn(player.Pos + Vector3.up * 2f, dealt, "heavy");
        feel.AddShake(0.35f);
        feel.HitStop(3);
        if (Casting)
        {
            castTarget.soul.CancelSending();   // 혼은 무릎 꿇은 상태로 돌아간다(대기 시간은 그대로 흐름)
            EndCast();
            Say("INTERRUPTED!");
        }
        if (ledger.Dead) { Say("FALLEN"); night.Tick(night.TimeLeft + 1f); }   // 쓰러짐 = 동트기와 같은 실패(추가 수확분 상실)
    }

    /// <summary>쓰러진 뒤 한 판을 처음부터. 체력·적·얼룩을 되돌리고 장부(수확)는 결과 화면(M5)에서 다룬다</summary>
    void RestartNight() { night = new NightRun(); settled = false; ResetRound(); }

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
        if (CharacterPanel.Open) return;   // 캐릭터 창이 열려 있으면 세계가 멈춘다
        HandleKeys();
        if (night.Over)
        {
            // 한 번만 정산: 동이 터서 끝났으면 흩어진 추가 수확분(넋)을 장부에서 뺀다. 몫과 성장(기억·품계)은 그대로.
            if (!settled) { settled = true; ledger.Neok = Mathf.Max(0, ledger.Neok - night.LostNeok); ledger.Coin = Mathf.Max(0, ledger.Coin - night.LostCoin); }
            // 결과 화면: 아무 때나 R/E 가 아닌 Space(또는 터치 버튼)로 다시 시작
            if (Input.GetKeyDown(KeyCode.Space)) RestartNight();
            return;
        }
        night.Tick(dt);
        TickClues();
        enemySpawnPause = Mathf.Max(0f, enemySpawnPause - dt);
        enemies.spawnPaused = enemySpawnPause > 0f || (Casting && castTarget.soul.Boss);   // 보스 천도 중·직후엔 잡몹이 새로 나오지 않는다
        // 귀환: 서낭당 위에 서면 즉시. 단 출발 직후(몫을 하나도 못 채움)에는 자동 귀환하지 않는다 — 밤을 시작도 못 하고 끝나는 것 방지
        float toShrine = new Vector2(player.Pos.x, player.Pos.z).magnitude;
        if (night.QuotaDone && night.TryReturn(toShrine)) Say("RETURNED!");
        chainLeft = Mathf.Max(0f, chainLeft - dt);
        toastT -= realDt;
        stains.Tick(dt);
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
        if (Input.GetKeyDown(KeyCode.R)) CommandPahon();
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
        return it == null ? "-" : (it.Named ? it.Name : it.Rarity.ToString()) + "/" + it.Options.Count;
    }

    // ===== 화면 ====================================================================
    void OnGUI()
    {
        if (white == null) return;
        // (1) 시야 축소 + 기억의 색 (천도 캐스팅 중)
        if (visionP > 0.001f)
        {
            var tint = ChasaPalette.MemoryRim;
            float diag = Mathf.Sqrt(Screen.width * Screen.width + Screen.height * Screen.height);
            float size = Mathf.Lerp(diag * 1.25f, diag * 1.25f * Balance.TENDO_VISION_RATIO, visionP);   // 반경 60%로
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
                GUI.Label(new Rect(sp.x - 80, Screen.height - sp.y - 12, 160, 24), e.soul.Boss ? "Old Ferryman" : e.label, nameStyle);
            }
        }
        // (2) 무릎 꿇은 혼 머리 위 막대 = 처결 대기 남은 시간 (색 = 혼 종류)
        if (cam != null)
        {
            foreach (var e in enemies.list)
            {
                if (!e.kneeling && !e.sending) continue;
                var sp = cam.WorldToScreenPoint(e.HeadPosition + Vector3.up * 0.3f);
                float ratio = Mathf.Clamp01(e.soul.WaitLeft / Mathf.Max(0.01f, e.soul.WaitTotal));
                var bg = new Rect(sp.x - 28, Screen.height - sp.y - 4, 56, 8);
                GUI.color = new Color(0, 0, 0, 0.7f); GUI.DrawTexture(bg, white);
                GUI.color = Enemy.KindColor(e.soul.Kind);
                GUI.DrawTexture(new Rect(bg.x + 1, bg.y + 1, 54 * ratio, 6), white);
                GUI.color = Color.white;
            }
        }
        // (3) 장부(넋·기억·엽전·업)와 안내
        var small = new GUIStyle(GUI.skin.label) { fontSize = 16 };
        small.normal.textColor = new Color(1, 1, 1, 0.9f);
        GUI.Label(new Rect(12, 30, 700, 24),
            "NEOK " + ledger.Neok + "   MEMORY " + ledger.Memory + "   COIN " + ledger.Coin +
            "   KARMA " + ledger.Karma + " (tier " + CoreRules.KarmaTier(ledger.Karma) + ")" +
            (chainLeft > 0f ? "   CHAIN!" : ""), small);
        GUI.Label(new Rect(12, 74, 700, 24), "HP " + ledger.Hp + " / " + ledger.MaxHp + "   WEAPON " + lo.Def.Name + " (Tab)" +
            (lo.Def.HasQuake ? "  Q quake" + (lo.quakeCd > 0f ? " " + Mathf.CeilToInt(lo.quakeCd) + "s" : "") : "") + "   STAT PTS " + StatPoints.Earned(ledger.Neok), small);
        string sk = "";
        for (int i = 0; i < 3; i++)
            sk += (i + 1) + ":" + SkillDef.All[i].Name + (lo.skills.Ready(i) ? "" : "(" + Mathf.CeilToInt(lo.skills.Left[i]) + "s)") + "   ";
        GUI.Label(new Rect(12, 118, 800, 24), sk, small);
        GUI.Label(new Rect(12, 140, 900, 24), "GEAR  W:" + GearName(Slot.Weapon) + "  R:" + GearName(Slot.Robe) + "  C:" + GearName(Slot.Charm), small);
        if (lo.lastDropT > 0f) GUI.Label(new Rect(12, 162, 900, 24), lo.lastDrop, small);
        // 장비 아이콘 세 칸 (그림이 있을 때만): 등급 테두리 + 칸별 아이콘
        for (int si = 0; si < 3; si++) DrawGearIcon((Slot)si, new Rect(12 + si * 56, 190, 52, 52));
        GUI.Label(new Rect(12, 52, 700, 24), "E: send (cheondo)   R: shatter (pahon)", small);
        GUI.Label(new Rect(12, 96, 700, 24),
            "NIGHT " + Mathf.CeilToInt(night.TimeLeft) + "s   SENT " + night.Sent + "/" + Balance.NIGHT_QUOTA +
            "   CLUES " + night.Clues + "/" + Balance.BOSS_CLUES_REQUIRED + (night.BossDone ? "   BOSS DONE" : "") + (night.QuotaDone ? "  (go back to the shrine!)" : "") + (night.Warning ? "   DAWN IS COMING!" : ""), small);
        if (night.Over)
        {
            GUI.color = new Color(0, 0, 0, 0.75f); GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), white); GUI.color = Color.white;
            var h = new GUIStyle(GUI.skin.label) { fontSize = 34, alignment = TextAnchor.MiddleCenter }; h.normal.textColor = Color.white;
            var m = new GUIStyle(h) { fontSize = 22 };
            bool ok = night.Phase == NightPhase.Returned;
            GUI.Label(new Rect(0, Screen.height * 0.25f, Screen.width, 50), ok ? "NIGHT COMPLETE" : "DAWN BROKE", h);
            GUI.Label(new Rect(0, Screen.height * 0.25f + 60, Screen.width, 190),
                "SENT " + night.Sent + "   NEOK KEPT " + night.FinalNeok + (night.LostNeok > 0 ? "   LOST " + night.LostNeok : "") + (night.LostCoin > 0 ? "   COIN LOST " + night.LostCoin : "") +
                "\nCOIN " + ledger.Coin + "   KARMA " + ledger.Karma + "   MEMORY " + ledger.Memory +
                "\nBOSS " + (night.BossDone ? "DONE" : "-") + "   CLUES " + night.Clues + "/" + Balance.BOSS_CLUES_REQUIRED +
                "   GEAR W:" + GearName(Slot.Weapon) + " R:" + GearName(Slot.Robe) + " C:" + GearName(Slot.Charm) +
                (night.Phase == NightPhase.Returned ? "" : "\n(the quota's share is kept; extra harvest scattered)"), m);
            if (GUI.Button(new Rect(Screen.width / 2f - 90, Screen.height * 0.25f + 260, 180, 70), "AGAIN (Space)")) RestartNight();
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
        if (toastT > 0f)
        {
            var big = new GUIStyle(GUI.skin.label) { fontSize = 22, alignment = TextAnchor.MiddleCenter };
            big.normal.textColor = Color.white;
            GUI.Label(new Rect(0, Screen.height * 0.28f, Screen.width, 40), toast, big);
        }
        // (4) 터치 버튼 (폰에는 키보드가 없다)
        if (touchUI)
        {
            var bs = new GUIStyle(GUI.skin.button) { fontSize = 20 };
            if (GUI.Button(new Rect(24, Screen.height - 110, 110, 90), "SEND", bs)) CommandTendo();
            if (GUI.Button(new Rect(148, Screen.height - 110, 130, 90), "SHATTER", bs)) CommandPahon();
            // 도술 세 칸과 무기 바꾸기 (위쪽 줄)
            for (int i = 0; i < 3; i++)
                if (GUI.Button(new Rect(24 + i * 94, Screen.height - 206, 86, 80), (i + 1) + "\n" + SkillDef.All[i].Name, bs)) UseSkill(i);
            if (GUI.Button(new Rect(24 + 3 * 94, Screen.height - 206, 86, 80), "SWAP", bs)) player.CommandSwap();
            if (GUI.Button(new Rect(24 + 5 * 94, Screen.height - 206, 86, 80), "MENU", bs)) panel.Toggle();
            if (lo.Def.HasQuake && GUI.Button(new Rect(24 + 4 * 94, Screen.height - 206, 86, 80), "QUAKE", bs)) player.CommandQuake();
        }
    }
}
