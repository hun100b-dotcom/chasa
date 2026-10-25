// =============================================================================
// Player.cs — 플레이어(차사). 이동 / 철삭 3타 콤보 / 견인. (Godot판 player.gd)
//
// 상태 머신(지금 뭘 하는지 하나만 기억): Free 대기·이동 / Attack 콤보 / Pull 견인
// 한 번에 한 상태만 → "공격하면서 견인" 같은 꼬임이 없다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class Player : MonoBehaviour
{
    public enum State { Free, Attack, Pull, Dodge }

    class AttackRun
    {
        public int step; public ComboStep cfg; public string phase = "windup"; public float t;
        public float startAngle, totalSweep, prevAngle;
        public HashSet<Enemy> hit = new HashSet<Enemy>(); // 한 번 휘두를 때 한 번만 맞게
        public bool firstSample = true;
        public bool trailDone;                             // 큰 원호 잔상을 맞는 순간 한꺼번에 그렸는가(그 뒤 기록 중단)
        public bool fired;                                 // 붓: 먹물을 이미 쐈는가
    }
    /// <summary>명부 붓이 쏘는 먹물. 앞으로 날다가 처음 닿는 적 한 마리를 맞히고 사라진다(사거리 = 콤보 reach)</summary>
    class InkBolt
    {
        public GameObject go; public Vector3 dir; public float left; public ComboStep cfg; public int step;
    }
    readonly List<InkBolt> bolts = new List<InkBolt>();
    const float BOLT_SPEED = 22f;     // 먹물 속도(m/s). 6m 를 약 0.27초에 — 피하기 어려운 대신 사거리가 짧다 (임시값)
    const float BOLT_RADIUS = 0.35f;  // 먹물 크기: 적 몸 반경에 더해 닿음을 판정

    class PullRun { public string phase = "throw"; public float t; public Enemy target; public Vector3 aim, from; }

    public EnemyManager enemies;
    public HitFeel feel;
    public DamageNumbers numbers;
    public ChainVisual chain;

    ActorSprite spr;                   // 아트팀 그림(없으면 파란 캡슐로 대신)
    Renderer[] bodyShapes;
    Vector3 lastPos; float walkT;      // 걷는 그림 두 장을 번갈아 보여 주려고
    public Loadout loadout = new Loadout();   // 든 무기·도술 쿨다운·장비 (JudgeSystem 이 장비 드롭을 넣어 준다)
    ComboStep[] Steps => WeaponTable.Steps(loadout.weapon);   // 지금 든 무기의 콤보 표
    public float actLock;   // 파혼 끝동작 잠금(초). 이 동안은 이동·공격 불가
    bool Busy => locked || loadout.swapLeft > 0f || actLock > 0f;             // 천도 캐스팅 중이거나 무기를 바꿔 드는 중
    public bool locked;               // 천도 캐스팅 중엔 움직이지도 휘두르지도 못한다 (무방비 = 위험)
    public float speedMult = 1f;      // 원념 얼룩 위면 0.8 (이동속도 -20%). JudgeSystem 이 매 프레임 넣어 준다
    public float invulnT;             // 맞은 직후 무적 시간(연속 피해 방지). 0이면 맞을 수 있다
    public float facing;              // 바닥 평면 각도 (0 = +x)
    public State state = State.Free;
    Vector3? moveTarget;
    Enemy chaseTarget;
    int comboStep;
    float comboTimer;
    AttackRun atk;
    bool hasBuffered; Enemy buffered; Vector3? bufferedAim; // 눌러둔 다음 입력(공격). 후딜 직전 0.2초부터만 저장되고 0.15초 지나면 버려진다
    float bufferAge;                                         // 저장된 공격 입력의 나이(초)
    bool hasDodgeBuffer; Vector3? dodgeBufferAim; float dodgeBufferAge;   // 눌러둔 피하기(우선순위 최고)
    PullRun pullRun;
    float pullCooldown;
    float chainLag;
    // ---- 피하기(구르기) ----
    float dodgeT; Vector3 dodgeDir;                 // 피하는 중 경과 시간, 방향
    float dodgeCharges = Balance.DODGE_CHARGES;     // 남은 충전(소수 가능: 충전되는 중)
    public System.Action onHitLanded;               // 내 타격이 적에게 맞을 때마다(안내가 첫 타를 알아챈다)
    public System.Action onDodgeCancelCast;         // 천도 캐스팅 중 피하면 JudgeSystem 이 캐스팅만 취소한다
    public bool judgeStance;                        // 무릎 꿇은 혼 앞에서 고르는 중: 서 있으면 Idle→Judge 자세(JudgeSystem 이 매 프레임 정한다)
    public float DodgeCharges => dodgeCharges;
    public void RefillDodge() { dodgeCharges = Balance.DODGE_CHARGES; }   // 서낭당 쉬기: 피하기 충전 가득
    public float PullCooldown => pullCooldown;
    public bool Dodging => state == State.Dodge;

    public Vector3 Pos { get => transform.position; set => transform.position = value; }

    public static Player Create()
    {
        var go = new GameObject("Player");
        var p = go.AddComponent<Player>();
        // 몸: 파란 캡슐 + 노란 코(어느 쪽을 보는지 보이게). 코는 로컬 +z(유니티의 '앞')
        var body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        Destroy(body.GetComponent<Collider>());
        body.transform.SetParent(go.transform, false);
        body.transform.localScale = new Vector3(Config.PLAYER_RADIUS * 1.8f, (0.8f + Config.PLAYER_RADIUS * 1.8f) / 2f, Config.PLAYER_RADIUS * 1.8f);
        body.transform.localPosition = new Vector3(0, 0.9f, 0);
        body.GetComponent<Renderer>().sharedMaterial = U.Matte(Config.Hex(0x3b82f6));
        var nose = GameObject.CreatePrimitive(PrimitiveType.Cube);
        Destroy(nose.GetComponent<Collider>());
        nose.transform.SetParent(go.transform, false);
        nose.transform.localScale = new Vector3(0.25f, 0.25f, 0.4f);
        nose.transform.localPosition = new Vector3(0, 1.35f, Config.PLAYER_RADIUS * 0.9f);
        nose.GetComponent<Renderer>().sharedMaterial = U.Matte(Config.Hex(0xffe066));
        p.bodyShapes = new[] { body.GetComponent<Renderer>(), nose.GetComponent<Renderer>() };
        p.spr = ActorSprite.Create(go.transform, null, true);
        p.spr.transform.localPosition = Vector3.zero;
        return p;
    }

    /// <summary>지금 하는 일에 맞는 그림: 휘두름(철삭/방망이)·시전·피격·걷기·서 있기</summary>
    void UpdateSprite(float dt)
    {
        if (spr == null) return;
        float moved = new Vector2(Pos.x - lastPos.x, Pos.z - lastPos.z).magnitude;
        lastPos = Pos;
        if (moved > 0.001f) walkT += dt; else walkT = 0f;
        string n = "characters/chasa_idle";
        bool mace = loadout.weapon == WeaponId.Mace;
        if (state == State.Dodge) n = View3D.On ? "characters/chasa_dodge" : "characters/chasa_walk_a";       // 피하는 중(전용 그림이 오기 전엔 걷는 그림)
        else if (invulnT > 0.35f) n = "characters/chasa_hit";                 // 막 맞음
        else if (locked) n = "characters/chasa_cast";                    // 천도 시전
        else if (state == State.Attack && atk != null) n = mace ? "characters/chasa_bang" + Mathf.Clamp(atk.step, 1, 3) : "characters/chasa_swing";
        else if (judgeStance && View3D.On && moved <= 0.001f) n = "characters/chasa_judge";   // 처결 고르는 자세(모델 동작 Judge)
        else if (moved > 0.001f) n = ((int)(walkT * 6f) % 2 == 0) ? "characters/chasa_walk_a" : "characters/chasa_walk_b";
        bool shown = spr.Show(n, U.Dir(facing));
        spr.SetWeapon(loadout.weapon);   // 손에 든 무기 모델(바꿔 들면 다른 모델로)
        foreach (var r in bodyShapes) r.enabled = !shown;
    }

    // ===== 피하기 ==================================================================
    /// <summary>
    /// 지금 처결(천도·파혼) 같은 행동을 시작할 수 있나? (상태를 바꾸지 않는다)
    /// 자유 상태 / 피하기 중 0.22초 지남 / 공격 후딜(끊기 창 = 후딜 시작부터)이면 가능.
    /// </summary>
    public bool CanActNow()
    {
        if (state == State.Free) return true;
        if (state == State.Dodge) return DodgeRules.CanCancelToAction(dodgeT);
        if (state == State.Attack && atk != null) return atk.phase == "recover";
        return false;
    }

    /// <summary>실제로 행동을 시작할 때 부른다: 피하기·공격 후딜을 끝내고 자유 상태로 만든다</summary>
    public bool ConsumeAct()
    {
        if (!CanActNow()) return false;
        if (state == State.Dodge) state = State.Free;
        else if (state == State.Attack)
        {
            int finished = atk.step; atk = null; state = State.Free; hasBuffered = false; bufferedAim = null; hasDodgeBuffer = false;
            chain.gameObject.SetActive(false);
            if (finished >= Steps.Length) { comboStep = 0; comboTimer = 0f; } else comboTimer = Config.COMBO_RESET_TIME;
        }
        return true;
    }

    /// <summary>폰은 터치 지연 때문에 버퍼 창과 유효 시간이 조금 길다</summary>
    float BufWindow => Balance.BUFFER_WINDOW + (Ko.TouchUI ? Balance.BUFFER_TOUCH_ADD : 0f);
    float BufLife => Balance.BUFFER_LIFETIME + (Ko.TouchUI ? Balance.BUFFER_TOUCH_ADD : 0f);

    /// <summary>
    /// 공격 중 들어온 입력을 저장해도 되는가: 휘두르는 끝(후딜 직전 BUFFER_WINDOW 초)부터, 후딜 중에는 언제든.
    /// 왜? 예전엔 선딜 때 누른 입력도 기억해서 '내가 안 누른 타'가 나가는 느낌이 났다.
    /// </summary>
    bool CanBufferNow()
    {
        if (atk == null) return false;
        if (atk.phase == "recover") return true;
        if (atk.phase == "swing") return (atk.cfg.swing - atk.t) <= BufWindow;
        return false;
    }

    /// <summary>지금 피할 수 있나? (규칙: 휘두르는 중은 불가, 3타 후딜 앞 절반 불가, 견인 중 불가)</summary>
    bool CanDodgeNow()
    {
        if (!Balance.DODGE_ENABLED || dodgeCharges < 1f) return false;
        if (state == State.Pull) return false;
        if (state == State.Dodge) return DodgeRules.CanCancelToAction(dodgeT);   // 연속 피하기
        if (locked) return Balance.DODGE_CANCELS_TENDO;                               // 천도 중: 캐스팅을 포기하고 피한다
        if (state == State.Attack && atk != null)
        {
            if (atk.phase == "swing") return false;                                   // 휘두르면 책임진다
            if (atk.phase == "recover" && !DodgeRules.RecoverAllowsDodge(atk.step >= Steps.Length, atk.t / atk.cfg.recover)) return false;
        }
        return true;
    }

    /// <summary>피하기. aim = 가고 싶은 쪽 바닥 점(없으면 걷던 방향, 그것도 없으면 바라보던 방향)</summary>
    public bool CommandDodge(Vector3? aim)
    {
        if (!CanDodgeNow())
        {
            // 지금은 못 피하지만 곧 가능해지는 때(휘두르는 끝·3타 후딜 앞)라면 눌러둔다 — 우선순위 최고
            if (state == State.Attack && atk != null && dodgeCharges >= 1f && Balance.DODGE_ENABLED && CanBufferNow()) { hasDodgeBuffer = true; dodgeBufferAim = aim; dodgeBufferAge = 0f; }
            return false;
        }
        if (locked) { onDodgeCancelCast?.Invoke(); locked = false; }
        Vector3 dir;
        if (aim.HasValue) dir = new Vector3(aim.Value.x - Pos.x, 0, aim.Value.z - Pos.z);
        else if (moveTarget.HasValue) dir = new Vector3(moveTarget.Value.x - Pos.x, 0, moveTarget.Value.z - Pos.z);
        else dir = U.Dir(facing);
        if (dir.sqrMagnitude < 1e-4f) dir = U.Dir(facing);
        dodgeDir = dir.normalized;
        facing = Mathf.Atan2(dodgeDir.z, dodgeDir.x);
        dodgeCharges -= 1f; dodgeT = 0f; dodgeDistance = Balance.DODGE_DISTANCE;
        state = State.Dodge;
        moveTarget = null; chaseTarget = null; hasBuffered = false; bufferedAim = null; atk = null;
        chain.gameObject.SetActive(false);
        Sfx.Play("sfx.dodge");
        return true;
    }

    float dodgeDistance = Balance.DODGE_DISTANCE;   // 이번 피하기가 가는 거리(매듭 걸음은 더 멀다)

    /// <summary>매듭 걸음: 사슬을 걸어 바라보는(또는 가고 싶은) 쪽으로 dist 만큼 돌진. 피하기와 같은 무적 구간을 쓰고 피하기 충전은 쓰지 않는다</summary>
    public bool CommandKnotDash(float dist, Vector3? aim)
    {
        if (Busy || state == State.Pull || state == State.Dodge) return false;
        if (locked) return false;
        Vector3 dir = aim.HasValue ? new Vector3(aim.Value.x - Pos.x, 0, aim.Value.z - Pos.z) : moveTarget.HasValue ? new Vector3(moveTarget.Value.x - Pos.x, 0, moveTarget.Value.z - Pos.z) : U.Dir(facing);
        if (dir.sqrMagnitude < 1e-4f) dir = U.Dir(facing);
        dodgeDir = dir.normalized; facing = Mathf.Atan2(dodgeDir.z, dodgeDir.x);
        dodgeT = 0f; dodgeDistance = dist; state = State.Dodge;
        moveTarget = null; chaseTarget = null; hasBuffered = false; bufferedAim = null; atk = null;
        chain.gameObject.SetActive(false);
        Sfx.Play("sfx.dodge");
        return true;
    }

    void TickDodge(float dt)
    {
        if (dt <= 0f) return;
        // 처음 빠르고 끝에서 감속(EaseOut): 순간 이동처럼 튀지 않고 '미끄러져 피하는' 느낌
        float t0 = dodgeT, t1 = Mathf.Min(Balance.DODGE_TIME, dodgeT + dt);
        float p0 = 1f - Mathf.Pow(1f - t0 / Balance.DODGE_TIME, 2f), p1 = 1f - Mathf.Pow(1f - t1 / Balance.DODGE_TIME, 2f);
        Pos += dodgeDir * (dodgeDistance * (p1 - p0));
        ClampToArena();
        dodgeT += dt;
        if (dodgeT >= Balance.DODGE_TIME) { state = State.Free; comboTimer = Mathf.Max(comboTimer, 0f); }
    }

    // ===== 명령 (입력 쪽에서 호출) ================================================
    public void CommandMove(Vector3 point)
    {
        if (Busy) return;
        if (state == State.Dodge && !CanActNow()) return;
        if (state == State.Dodge) ConsumeAct();
        // 공격 후딜이 60% 지났으면 이동으로 끝동작을 끊는다(손맛: 때리고 바로 움직일 수 있게)
        else if (state == State.Attack && atk != null && atk.phase == "recover" && DodgeRules.CanCancelRecoverToMove(atk.t / atk.cfg.recover)) ConsumeAct();
        float tx = point.x, tz = point.z;
        MapLayout.ClampPoint(ref tx, ref tz);   // 맵 밖을 눌러도 맵 안쪽 끝으로
        moveTarget = new Vector3(tx, 0, tz);
        chaseTarget = null;
        hasBuffered = false; // 이동을 지시하면 눌러둔 다음 타는 취소
    }

    /// <summary>쫓기·이동·예약된 공격을 모두 끊는다(데모·연출이 '이제 그만 때리고 천도해' 할 때)</summary>
    public void CommandStop() { chaseTarget = null; moveTarget = null; hasBuffered = false; bufferedAim = null; }

    public void CommandAttack(Enemy e)
    {
        if (Busy) return;
        if (state == State.Dodge) ConsumeAct();   // 끊을 수 있는 시점이면 피하기를 끝내고 아래로
        if (state == State.Attack) { if (CanBufferNow()) { hasBuffered = true; buffered = e; bufferedAim = null; bufferAge = 0f; } } // 다음 타 예약(새 입력이 이전 저장을 덮어쓴다)
        else if (state == State.Free) { chaseTarget = e; moveTarget = null; }
    }

    /// <summary>키보드(Space) 제자리 휘두르기: 달려가지 않고 그 자리에서 aim 방향으로 콤보</summary>
    public void CommandSwing(Vector3 aim)
    {
        if (Busy) return;
        if (state == State.Dodge) ConsumeAct();
        if (state == State.Attack) { if (CanBufferNow()) { hasBuffered = true; buffered = null; bufferedAim = aim; bufferAge = 0f; } }
        else if (state == State.Free) { moveTarget = null; chaseTarget = null; StartAttack(null, comboTimer > 0f, aim); }
    }

    /// <summary>Tab: 무기를 바꿔 든다(0.5초 동안 이동·공격 불가). 자유 상태에서만</summary>
    public void CommandSwap()
    {
        if (!Demo.Weapons || Busy || state != State.Free) return;   // 시연판 기본 구성은 철삭 하나
        var next = loadout.other; loadout.other = loadout.weapon; loadout.weapon = next;   // 든 것과 멘 것을 맞바꾼다
        loadout.swapLeft = Balance.WEAPON_SWAP_TIME;
        spr?.SetWeapon(loadout.weapon); spr?.PlayDraw();   // 새 무기 모델로 바꾸고 꺼내 드는 동작
        comboStep = 0; comboTimer = 0f; moveTarget = null; chaseTarget = null;
    }

    /// <summary>
    /// 육모방망이 Q '땅울림': 반경 안에 서 있는 적에게 맺힘 피해 + 기절.
    /// 기절은 서 있는 적에게만 걸리고, 무릎 꿇은 혼의 처결 대기 시간과는 무관하다 (기획 확정).
    /// 무릎 꿇은 혼은 맞지 않는다 — 처결을 기다리는 혼을 부수면 안 되니까.
    /// </summary>
    /// <summary>파혼 몸 동작(JudgeSystem 이 파혼을 터뜨릴 때 부른다)</summary>
    public void PlayPahonAnim() { spr?.PlayPahon(); }

    public bool CommandQuake()
    {
        if (Busy || state != State.Free || !loadout.Def.HasQuake || loadout.quakeCd > 0f) return false;
        loadout.quakeCd = Balance.MACE_QUAKE_COOLDOWN;
        moveTarget = null; chaseTarget = null;
        foreach (var e in enemies.list)
        {
            if (!e.alive) continue;
            var d = new Vector3(e.Pos.x - Pos.x, 0, e.Pos.z - Pos.z);
            if (d.magnitude > Balance.MACE_QUAKE_RADIUS + e.radius) continue;
            var dir = d.magnitude > 0.01f ? d.normalized : Vector3.right;
            int dmg = Mathf.RoundToInt(Balance.MACE_QUAKE_DAMAGE * loadout.stats.DamageMult);
            e.TakeHit(dmg, dir, 0f, Balance.MACE_QUAKE_STUN);
            numbers.Spawn(e.HeadPosition, dmg, "heavy");
        }
        feel.HitStop(4);
        feel.AddShake(0.8f);
        return true;
    }

    public void CommandPull(Enemy e, Vector3 aim)
    {
        if (Busy) return;
        if (pullCooldown > 0f) return;
        bool canCancel = state == State.Attack && atk != null && atk.phase == "recover"; // 후딜은 견인으로 끊을 수 있다
        if (state != State.Free && !canCancel) return;
        StartPull(e, aim);
    }

    // ===== 매 프레임 (dt = 게임 세계 시간, 히트스톱 중엔 0) ==========================
    /// <summary>
    /// 적에게 맞음. 휘두르던 중이면 끊긴다(콤보 처음부터). 견인(Pull)은 끊기지 않는다 — 끌고 오는 선택이 위험하지만 보상받게.
    /// 무적 시간 안이면 false(피해 없음).
    /// </summary>
    public bool Hurt()
    {
        if (invulnT > 0f) return false;
        // 피하기 무적 구간(시작 직후~끝): 맞지 않는다. 이 짧은 창을 맞추는 것이 피하기의 보상
        if (state == State.Dodge && DodgeRules.Invulnerable(dodgeT)) return false;
        invulnT = Balance.PLAYER_HIT_INVULN;
        bool wasAttacking = state == State.Attack;
        if (state == State.Attack)
        {
            // 공격 중단: 대기 예약·콤보를 지우고 자유 상태로 (여기서 EndAttack 대신 직접 정리해야 후딜 로직이 안 돈다)
            hasBuffered = false; bufferedAim = null;
            comboStep = 0; comboTimer = 0f;
            state = State.Free;
            chain.gameObject.SetActive(false);
        }
        // 걷는 중에 맞았다면 클릭 이동 목표를 지우지 않는다: 클릭은 한 번만 명령을 넣어서, 지우면 맞을 때마다 중간에 멈춰 섰다(PC 실측)
        if (wasAttacking) { moveTarget = null; chaseTarget = null; }
        return true;
    }

    public void Tick(float dt)
    {
        invulnT = Mathf.Max(0f, invulnT - dt);
        actLock = Mathf.Max(0f, actLock - dt);
        dodgeCharges = DodgeRules.Recharge(dodgeCharges, dt);   // 한 번 충전 1.1초
        loadout.Tick(dt);
        pullCooldown = Mathf.Max(0f, pullCooldown - dt);
        switch (state)
        {
            case State.Free: if (!Busy) TickFree(dt); break;
            case State.Attack: TickAttack(dt); break;
            case State.Pull: TickPull(dt); break;
            case State.Dodge: TickDodge(dt); break;
        }
        transform.rotation = Quaternion.LookRotation(U.Dir(facing)); // 코(+z)가 facing 방향을 보게
        UpdateSprite(dt);
        chain.trail.Tick(dt);
        TickBolts(dt);
    }

    /// <summary>먹물 한 방 발사: 휘두름이 시작되는 순간 손에서 정면으로</summary>
    void FireBolt(AttackRun a)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        Destroy(go.GetComponent<Collider>());
        go.transform.localScale = Vector3.one * BOLT_RADIUS * 2f;
        go.transform.position = Hand + U.Dir(facing) * 0.6f;
        go.GetComponent<Renderer>().sharedMaterial = U.Unlit(Config.Hex(0x1a1a2e));   // 먹색
        bolts.Add(new InkBolt { go = go, dir = U.Dir(facing), left = (a.cfg.reach + loadout.stats.ReachAdd), cfg = a.cfg, step = a.step });
    }

    void TickBolts(float dt)
    {
        for (int i = bolts.Count - 1; i >= 0; i--)
        {
            var b = bolts[i];
            float move = Mathf.Min(BOLT_SPEED * dt, b.left);
            b.go.transform.position += b.dir * move;
            b.left -= move;
            bool done = b.left <= 0f;
            var p = b.go.transform.position;
            foreach (var e in enemies.list)
            {
                if (!e.alive) continue;
                var d = new Vector2(e.Pos.x - p.x, e.Pos.z - p.z);
                if (d.magnitude > e.radius + BOLT_RADIUS) continue;
                var n = d.magnitude > 0.01f ? d.normalized : new Vector2(b.dir.x, b.dir.z);
                HitEnemy(e, new AttackRun { step = b.step, cfg = b.cfg }, n.x, n.y);
                done = true; break;   // 처음 닿은 한 마리만 (MaxHits 1)
            }
            if (done) { Destroy(b.go); bolts.RemoveAt(i); }
        }
    }

    void TickFree(float dt)
    {
        comboTimer = Mathf.Max(0f, comboTimer - dt);
        if (dt <= 0f) return;
        if (chaseTarget != null)
        {
            var e = chaseTarget;
            if (!e.alive) chaseTarget = null;
            else
            {
                var d = new Vector2(e.Pos.x - Pos.x, e.Pos.z - Pos.z);
                facing = U.TurnToward(facing, Mathf.Atan2(d.y, d.x), Config.PLAYER_TURN_SPEED * dt);
                if (d.magnitude - e.radius <= Config.ATTACK_START_RANGE) { chaseTarget = null; StartAttack(e, comboTimer > 0f, null); }
                else StepToward(e.Pos, dt);
                return;
            }
        }
        if (moveTarget.HasValue)
        {
            var mt = moveTarget.Value;
            var d = new Vector2(mt.x - Pos.x, mt.z - Pos.z);
            if (d.magnitude <= Config.PLAYER_ARRIVE_DISTANCE) moveTarget = null;
            else
            {
                facing = U.TurnToward(facing, Mathf.Atan2(d.y, d.x), Config.PLAYER_TURN_SPEED * dt);
                StepToward(mt, dt);
            }
        }
    }

    float walkSpeed, lastStepTime = -10f;   // 지금 걷는 속도와 마지막으로 걸은 시각(가속·감속용)

    void StepToward(Vector3 target, float dt)
    {
        var d = new Vector2(target.x - Pos.x, target.z - Pos.z);
        float dist = d.magnitude;
        if (dist < 1e-5f) return;
        float full = Config.PLAYER_MOVE_SPEED * speedMult * loadout.stats.MoveSpeedMult;
        // 오너 피드백 '움직임이 부자연스럽다' 대응: 출발 때 서서히 빨라지고(가속), 도착 직전엔 미리 줄인다(감속).
        // 멈췄다가 다시 걷기 시작하면(마지막 걸음이 0.1초 넘게 전이면) 속도를 처음부터 올린다
        if (Time.time - lastStepTime > 0.1f) walkSpeed = full * Balance.MOVE_START_FRAC;
        lastStepTime = Time.time;
        float cap = Mathf.Max(full * Balance.MOVE_START_FRAC, dist / Mathf.Max(0.01f, Balance.MOVE_BRAKE_TIME));   // 도착이 가까울수록 허용 속도가 낮아진다
        walkSpeed = Mathf.MoveTowards(walkSpeed, Mathf.Min(full, cap), Balance.MOVE_ACCEL * dt);
        float step = Mathf.Min(dist, walkSpeed * dt);
        var dir3 = new Vector3(d.x / dist, 0, d.y / dist);
        // 경사: 앞으로 1m 지점과 지금 자리의 땅 높이 차로 기울기를 잰다. 오르막이 가파를수록 느려지고, 너무 가파르면 못 오른다(내리막은 그대로)
        if (GroundTerrain.Active && step > 1e-5f)
        {
            float rise = GroundTerrain.HeightAt(Pos.x + dir3.x, Pos.z + dir3.z) - GroundTerrain.HeightAt(Pos.x, Pos.z);
            if (rise > Balance.MOVE_SLOPE_SLOW)
                step *= Mathf.Clamp01(1f - (rise - Balance.MOVE_SLOPE_SLOW) / Mathf.Max(0.01f, Balance.MOVE_SLOPE_BLOCK - Balance.MOVE_SLOPE_SLOW));
        }
        Pos += dir3 * step;
        Footstep(step);
        ClampToArena();
    }

    float strideLeft;   // 다음 발소리까지 남은 걸음 거리
    /// <summary>걸은 거리를 모아 한 걸음(FOOTSTEP_STRIDE_M)마다 땅 재질에 맞는 발소리를 낸다</summary>
    void Footstep(float moved)
    {
        if (moved <= 0f) return;
        strideLeft -= moved;
        if (strideLeft > 0f) return;
        strideLeft = Balance.FOOTSTEP_STRIDE_M;
        var w = footW ?? (footW = new float[5]);
        GroundTerrain.LayerWeights(Pos.x, Pos.z, w);
        Sfx.PlayStep(w, GroundTerrain.Active && GroundTerrain.HeightAt(Pos.x, Pos.z) < 0.18f);
    }
    float[] footW;

    void ClampToArena()
    {
        // 맵 경계 + 막힌 곳(집·장승)에서 미끄러지듯 밀려난다
        float x = Pos.x, z = Pos.z;
        Chasa.Core.MapLayout.PushOut(ref x, ref z, Config.PLAYER_RADIUS);
        Pos = new Vector3(x, Pos.y, z);   // 높이는 땅 붙이기(GroundSnap)가 맡으니 건드리지 않는다
    }

    Vector3 Hand => new Vector3(Pos.x, Config.PLAYER_HAND_HEIGHT, Pos.z);

    // ===== 철삭 3타 콤보 ===========================================================
    void StartAttack(Enemy target, bool continueCombo, Vector3? aim)
    {
        int step = continueCombo ? (comboStep % Steps.Length) + 1 : 1;
        comboStep = step;
        var cfg = Steps[step - 1];
        if (target != null && target.alive) facing = Mathf.Atan2(target.Pos.z - Pos.z, target.Pos.x - Pos.x);
        else if (aim.HasValue) facing = Mathf.Atan2(aim.Value.z - Pos.z, aim.Value.x - Pos.x);
        float start = facing - cfg.dir * cfg.startOffsetDeg * Mathf.Deg2Rad;
        state = State.Attack;
        atk = new AttackRun { step = step, cfg = cfg, startAngle = start, prevAngle = start, totalSweep = cfg.dir * cfg.sweepDeg * Mathf.Deg2Rad };
        hasBuffered = false;
        if (spr != null) spr.PlayAttack(cfg.windup / loadout.stats.AttackSpeedMult, cfg.swing / loadout.stats.AttackSpeedMult, step);   // 3D 동작을 이 타에 맞춰 처음부터
        chain.gameObject.SetActive(!loadout.Def.Projectile);   // 붓은 사슬 그림을 쓰지 않는다
    }

    void TickAttack(float dt)
    {
        var a = atk; var cfg = a.cfg;
        bufferAge += dt; dodgeBufferAge += dt;
        a.t += dt * loadout.stats.AttackSpeedMult;   // 장비의 공격 속도 보너스: 시간이 더 빨리 흐르는 셈
        var hand = Hand;
        if (a.phase == "windup")
        {
            // 준비: 살짝 앞 → 뒤로 당기는 예비동작
            float p = Mathf.Clamp01(a.t / cfg.windup);
            float angle = a.startAngle + cfg.dir * 0.4f * (1f - U.EaseOutQuad(p));
            chainLag *= Mathf.Exp(-14f * dt);
            chain.SetShape(hand, angle, Mathf.Lerp(0.3f, 0.55f, p) * (cfg.reach + loadout.stats.ReachAdd), hand.y + 0.25f * p, chainLag, 0.25f);
            a.prevAngle = a.startAngle;
            if (a.t >= cfg.windup) { a.phase = "swing"; a.t = 0f; Sfx.Play("sfx.swing." + Sfx.WeaponTag(loadout.weapon)); }   // 예비→휘두름 순간에 휘두르는 소리
            return;
        }
        if (a.phase == "swing")
        {
            float p = Mathf.Clamp01(a.t / cfg.swing);
            float angle = a.startAngle + a.totalSweep * U.EaseOutQuad(p);           // 확 휘두르고 끝에서 감속
            float radius = (cfg.reach + loadout.stats.ReachAdd) * (0.55f + 0.45f * U.EaseOutQuad(Mathf.Min(1f, p / 0.3f))); // 쭉 펴짐
            float headY = hand.y + 0.25f - 0.3f * p;
            if (dt > 0f)
            {
                float angVel = Mathf.Abs(angle - a.prevAngle) / dt;
                chainLag = Mathf.Lerp(chainLag, cfg.dir * Mathf.Min(angVel * 0.04f, 1.1f), 0.5f); // 빠를수록 많이 휨
                if (loadout.Def.Projectile) { if (!a.fired) { a.fired = true; FireBolt(a); } }   // 붓: 투사체
                else SweepHits(a, a.prevAngle, angle);
                if (!a.trailDone)
                {
                    RecordTrail(a, hand, a.prevAngle, angle, radius, headY);
                    // 길게 휘두르는 타(3타): 맞는 순간 남은 원호를 한꺼번에 그려 '맞은 프레임에 잔상이 같이 뜨게' 한다
                    // (원래는 휘두름이 끝나는 0.3초 뒤까지 천천히 자라 숫자보다 늦게 보였다 — PC 영상 의견)
                    if (cfg.swing >= 0.2f && a.hit.Count > 0)
                    {
                        RecordTrail(a, hand, angle, a.startAngle + a.totalSweep, (cfg.reach + loadout.stats.ReachAdd), headY);
                        a.trailDone = true;
                    }
                }
                if (cfg.lunge > 0f) { Pos += U.Dir(facing) * (cfg.lunge / cfg.swing * dt); ClampToArena(); } // 앞으로 밀고 들어감
            }
            chain.SetShape(Hand, angle, radius, headY, chainLag, 0f);
            a.prevAngle = angle;
            if (a.t >= cfg.swing) { a.phase = "recover"; a.t = 0f; }
            return;
        }
        // recover: 후딜. 사슬을 거둬들인다
        // 끊기 창: 후딜이 시작되면 저장된 입력을 바로 실행한다(우선순위: 피하기 > 공격). 0.15초 지난 입력은 버린다
        if (hasDodgeBuffer && dodgeBufferAge > BufLife) hasDodgeBuffer = false;
        if (hasBuffered && bufferAge > BufLife) { hasBuffered = false; bufferedAim = null; }
        if (hasDodgeBuffer && CanDodgeNow()) { hasDodgeBuffer = false; var da = dodgeBufferAim; CommandDodge(da); return; }
        if (hasBuffered) { FinishAttack(); return; }   // 후딜을 건너뛰고 다음 타로
        float pr = Mathf.Clamp01(a.t / cfg.recover);
        float ang = a.startAngle + a.totalSweep + cfg.dir * 0.2f * U.EaseOutQuad(pr);
        chainLag *= Mathf.Exp(-10f * dt);
        chain.SetShape(hand, ang, (cfg.reach + loadout.stats.ReachAdd) * (1f - 0.85f * U.EaseInQuad(pr)), hand.y - 0.05f, chainLag, 0.4f * pr);
        if (a.t >= cfg.recover) FinishAttack();
    }

    void FinishAttack()
    {
        int finished = atk.step;
        atk = null; hasDodgeBuffer = false;
        if (hasBuffered)
        {
            var next = buffered; var nextAim = bufferedAim;
            hasBuffered = false; bufferedAim = null;
            if (finished >= Steps.Length) comboStep = 0; // 3타 끝이면 다음은 1타
            StartAttack(next, true, nextAim);
            return;
        }
        state = State.Free;
        chain.gameObject.SetActive(false);
        if (finished >= Steps.Length) { comboStep = 0; comboTimer = 0f; }
        else comboTimer = Config.COMBO_RESET_TIME;
    }

    /// <summary>가까운 적부터 차례로 — 상한이 있는 무기가 먼 적보다 가까운 적을 먼저 맞히도록</summary>
    IEnumerable<Enemy> SweepOrder()
    {
        var sorted = new List<Enemy>(enemies.list);
        sorted.Sort((x, y) => (x.Pos - Pos).sqrMagnitude.CompareTo((y.Pos - Pos).sqrMagnitude));
        return sorted;
    }

    void SweepHits(AttackRun a, float prev, float cur)
    {
        int cap = loadout.Def.MaxHits;   // 관통 상한 (0 = 제한 없음)
        foreach (var e in SweepOrder())
        {
            if (cap > 0 && a.hit.Count >= cap) break;   // 삼지창은 3마리, 붓은 1마리에서 멈춘다
            if (!e.alive || a.hit.Contains(e)) continue;
            var d = new Vector2(e.Pos.x - Pos.x, e.Pos.z - Pos.z);
            float dist = d.magnitude;
            if (dist - e.radius > (a.cfg.reach + loadout.stats.ReachAdd) + Config.HIT_PADDING) continue; // 사슬이 안 닿음
            float half = Mathf.Asin(Mathf.Clamp01((e.radius + Config.HIT_PADDING) / Mathf.Max(dist, 0.01f)));
            if (!U.SweptThrough(prev, cur, Mathf.Atan2(d.y, d.x), half)) continue;
            a.hit.Add(e);
            var n = dist > 0f ? d / dist : d;
            HitEnemy(e, a, n.x, n.y);
        }
    }

    void HitEnemy(Enemy e, AttackRun a, float rx, float rz)
    {
        var cfg = a.cfg;
        float mix = Config.FEEL_KNOCKBACK_TANGENT_MIX * cfg.dir; // 바깥 + 휘두른 방향(접선) → 쓸려 날아감
        var dir = new Vector3(rx - rz * mix, 0, rz + rx * mix).normalized;
        int dmg = Mathf.Max(1, Mathf.RoundToInt(cfg.damage * loadout.stats.DamageMult * (1f + Random.Range(-Config.DAMAGE_VARIANCE, Config.DAMAGE_VARIANCE))));
        bool killed = e.TakeHit(dmg, dir, cfg.knockback, cfg.stun);
        onHitLanded?.Invoke();
        if (!killed) e.ReactHit(a.step);   // 맞은 동작: 1타 약·2타 중·3타 강(아트 맞는 동작)
        // 손맛 5요소: 맞은 놈만 굳기(국소 히트스톱) · 처치/마지막 타격만 전체 정지 · 흔들림 · 줌 펀치 · 맞은 방향 카메라 밀림
        bool last = a.step == Steps.Length;
        Sfx.Play(Sfx.HitKey(loadout.weapon, killed || last));   // 타격음은 히트스톱과 같은 순간에(무기마다 다른 소리)
        if (killed || last) feel.HitStop(cfg.hitStopFrames + (killed ? Config.FEEL_KILL_BONUS_FRAMES : 0));
        else e.Freeze(cfg.hitStopFrames * Config.FEEL_FRAME_TIME * 1.5f);   // 일반 타격은 국소 정지(조금 더 길게 — 전체 정지보다 덜 거슬리니까)
        feel.AddShake(cfg.shake + (killed ? Config.FEEL_KILL_BONUS_SHAKE : 0f));
        feel.AddZoom(killed ? 0.9f : last ? 0.6f : 0.25f + 0.35f * cfg.shake);
        feel.AddKick(dir, killed ? 0.35f : 0.12f + 0.12f * cfg.shake);
        numbers.Spawn(e.HeadPosition, dmg, a.step == Steps.Length ? "heavy" : "normal");
    }

    void RecordTrail(AttackRun a, Vector3 hand, float prev, float cur, float radius, float y)
    {
        for (int i = 1; i <= Config.TRAIL_SUBSTEPS; i++)
        {
            float ang = Mathf.Lerp(prev, cur, (float)i / Config.TRAIL_SUBSTEPS);
            var dir = U.Dir(ang);
            var outer = new Vector3(hand.x, y, hand.z) + dir * radius;
            var inner = new Vector3(hand.x, y, hand.z) + dir * (radius * Config.TRAIL_INNER_RATIO);
            chain.trail.Add(inner, outer, a.firstSample);
            a.firstSample = false;
        }
    }

    // ===== 견인 ===================================================================
    void StartPull(Enemy e, Vector3 aim)
    {
        atk = null; hasBuffered = false; moveTarget = null; chaseTarget = null; comboTimer = 0f; comboStep = 0;
        var target = e != null && e.alive ? e : null;
        var goal = target != null ? target.Pos : aim;
        var d = new Vector2(goal.x - Pos.x, goal.z - Pos.z);
        float dist = d.magnitude;
        if (target != null && dist > Config.PULL_RANGE) target = null; // 사거리 밖 → 허공(빗나감)
        facing = Mathf.Atan2(d.y, d.x);
        float reach = Mathf.Min(dist, Config.PULL_RANGE);
        state = State.Pull;
        pullRun = new PullRun { target = target, aim = Hand + U.Dir(facing) * reach };
        chain.gameObject.SetActive(true);
    }

    void TickPull(float dt)
    {
        var r = pullRun; var hand = Hand;
        r.t += dt;
        var target = r.target;
        if (r.phase == "throw")
        {
            var goal = target != null ? new Vector3(target.Pos.x, Config.PLAYER_HAND_HEIGHT, target.Pos.z) : r.aim;
            float p = U.EaseOutQuad(Mathf.Clamp01(r.t / Config.PULL_THROW_TIME));
            StraightChain(hand, Vector3.Lerp(hand, goal, p), 0.2f * (1f - p));
            if (r.t >= Config.PULL_THROW_TIME)
            {
                if (target != null) { HitPull(target); r.phase = "drag"; }
                else { r.from = goal; r.phase = "retract"; }
                r.t = 0f;
            }
            return;
        }
        if (r.phase == "drag")
        {
            var head = new Vector3(target.Pos.x, Config.PLAYER_HAND_HEIGHT, target.Pos.z);
            StraightChain(hand, head, 0f);
            facing = Mathf.Atan2(target.Pos.z - Pos.z, target.Pos.x - Pos.x);
            if (!target.pulled)
            {
                if (dt > 0f && target.alive) { feel.HitStop(2); feel.AddShake(Config.PULL_ARRIVE_SHAKE); Sfx.Play("sfx.hit.heavy"); } // 도착 '쿵'
                r.from = head; r.phase = "retract"; r.t = 0f;
            }
            return;
        }
        float p2 = U.EaseInQuad(Mathf.Clamp01(r.t / Config.PULL_RETRACT_TIME));
        StraightChain(hand, Vector3.Lerp(r.from, hand, p2), 0.1f);
        if (r.t >= Config.PULL_RETRACT_TIME)
        {
            state = State.Free; pullRun = null; pullCooldown = Config.PULL_COOLDOWN;
            chain.gameObject.SetActive(false);
        }
    }

    void HitPull(Enemy e)
    {
        var dir = new Vector3(Pos.x - e.Pos.x, 0, Pos.z - e.Pos.z).normalized;
        int dmg = Mathf.Max(1, Mathf.RoundToInt(Config.PULL_DAMAGE * (1f + Random.Range(-Config.DAMAGE_VARIANCE, Config.DAMAGE_VARIANCE))));
        bool killed = e.TakeHit(dmg, dir, 0f, Config.PULL_STUN);
        feel.HitStop(Config.PULL_HITSTOP_FRAMES + (killed ? Config.FEEL_KILL_BONUS_FRAMES : 0));
        feel.AddShake(Config.PULL_SHAKE);
        numbers.Spawn(e.HeadPosition, dmg, "pull");
        if (!killed) e.StartPulled();
    }

    void StraightChain(Vector3 hand, Vector3 head, float sag)
    {
        var d = new Vector2(head.x - hand.x, head.z - hand.z);
        chain.SetShape(hand, Mathf.Atan2(d.y, d.x), d.magnitude, head.y, 0f, sag);
    }
}
