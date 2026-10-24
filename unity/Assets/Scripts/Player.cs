// =============================================================================
// Player.cs — 플레이어(차사). 이동 / 철삭 3타 콤보 / 견인. (Godot판 player.gd)
//
// 상태 머신(지금 뭘 하는지 하나만 기억): Free 대기·이동 / Attack 콤보 / Pull 견인
// 한 번에 한 상태만 → "공격하면서 견인" 같은 꼬임이 없다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class Player : MonoBehaviour
{
    public enum State { Free, Attack, Pull }

    class AttackRun
    {
        public int step; public ComboStep cfg; public string phase = "windup"; public float t;
        public float startAngle, totalSweep, prevAngle;
        public HashSet<Enemy> hit = new HashSet<Enemy>(); // 한 번 휘두를 때 한 번만 맞게
        public bool firstSample = true;
    }
    class PullRun { public string phase = "throw"; public float t; public Enemy target; public Vector3 aim, from; }

    public EnemyManager enemies;
    public HitFeel feel;
    public DamageNumbers numbers;
    public ChainVisual chain;

    public bool locked;               // 천도 캐스팅 중엔 움직이지도 휘두르지도 못한다 (무방비 = 위험)
    public float speedMult = 1f;      // 원념 얼룩 위면 0.8 (이동속도 -20%). JudgeSystem 이 매 프레임 넣어 준다
    public float facing;              // 바닥 평면 각도 (0 = +x)
    public State state = State.Free;
    Vector3? moveTarget;
    Enemy chaseTarget;
    int comboStep;
    float comboTimer;
    AttackRun atk;
    bool hasBuffered; Enemy buffered; Vector3? bufferedAim; // 후딜 중 눌러둔 다음 입력
    PullRun pullRun;
    float pullCooldown;
    float chainLag;

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
        return p;
    }

    // ===== 명령 (입력 쪽에서 호출) ================================================
    public void CommandMove(Vector3 point)
    {
        if (locked) return;
        moveTarget = new Vector3(Mathf.Clamp(point.x, -Config.ARENA_HALF_SIZE, Config.ARENA_HALF_SIZE), 0,
                                 Mathf.Clamp(point.z, -Config.ARENA_HALF_SIZE, Config.ARENA_HALF_SIZE));
        chaseTarget = null;
        hasBuffered = false; // 이동을 지시하면 눌러둔 다음 타는 취소
    }

    public void CommandAttack(Enemy e)
    {
        if (locked) return;
        if (state == State.Attack) { hasBuffered = true; buffered = e; bufferedAim = null; } // 다음 타 예약
        else if (state == State.Free) { chaseTarget = e; moveTarget = null; }
    }

    /// <summary>키보드(Space) 제자리 휘두르기: 달려가지 않고 그 자리에서 aim 방향으로 콤보</summary>
    public void CommandSwing(Vector3 aim)
    {
        if (locked) return;
        if (state == State.Attack) { hasBuffered = true; buffered = null; bufferedAim = aim; }
        else if (state == State.Free) { moveTarget = null; chaseTarget = null; StartAttack(null, comboTimer > 0f, aim); }
    }

    public void CommandPull(Enemy e, Vector3 aim)
    {
        if (locked) return;
        if (pullCooldown > 0f) return;
        bool canCancel = state == State.Attack && atk != null && atk.phase == "recover"; // 후딜은 견인으로 끊을 수 있다
        if (state != State.Free && !canCancel) return;
        StartPull(e, aim);
    }

    // ===== 매 프레임 (dt = 게임 세계 시간, 히트스톱 중엔 0) ==========================
    public void Tick(float dt)
    {
        pullCooldown = Mathf.Max(0f, pullCooldown - dt);
        switch (state)
        {
            case State.Free: if (!locked) TickFree(dt); break;
            case State.Attack: TickAttack(dt); break;
            case State.Pull: TickPull(dt); break;
        }
        transform.rotation = Quaternion.LookRotation(U.Dir(facing)); // 코(+z)가 facing 방향을 보게
        chain.trail.Tick(dt);
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

    void StepToward(Vector3 target, float dt)
    {
        var d = new Vector2(target.x - Pos.x, target.z - Pos.z);
        float dist = d.magnitude;
        if (dist < 1e-5f) return;
        float step = Mathf.Min(dist, Config.PLAYER_MOVE_SPEED * speedMult * dt);
        Pos += new Vector3(d.x / dist, 0, d.y / dist) * step;
        ClampToArena();
    }

    void ClampToArena()
    {
        float lim = Config.ARENA_HALF_SIZE - Config.PLAYER_RADIUS;
        Pos = new Vector3(Mathf.Clamp(Pos.x, -lim, lim), 0, Mathf.Clamp(Pos.z, -lim, lim));
    }

    Vector3 Hand => new Vector3(Pos.x, Config.PLAYER_HAND_HEIGHT, Pos.z);

    // ===== 철삭 3타 콤보 ===========================================================
    void StartAttack(Enemy target, bool continueCombo, Vector3? aim)
    {
        int step = continueCombo ? (comboStep % Config.COMBO.Length) + 1 : 1;
        comboStep = step;
        var cfg = Config.COMBO[step - 1];
        if (target != null && target.alive) facing = Mathf.Atan2(target.Pos.z - Pos.z, target.Pos.x - Pos.x);
        else if (aim.HasValue) facing = Mathf.Atan2(aim.Value.z - Pos.z, aim.Value.x - Pos.x);
        float start = facing - cfg.dir * cfg.startOffsetDeg * Mathf.Deg2Rad;
        state = State.Attack;
        atk = new AttackRun { step = step, cfg = cfg, startAngle = start, prevAngle = start, totalSweep = cfg.dir * cfg.sweepDeg * Mathf.Deg2Rad };
        hasBuffered = false;
        chain.gameObject.SetActive(true);
    }

    void TickAttack(float dt)
    {
        var a = atk; var cfg = a.cfg;
        a.t += dt;
        var hand = Hand;
        if (a.phase == "windup")
        {
            // 준비: 살짝 앞 → 뒤로 당기는 예비동작
            float p = Mathf.Clamp01(a.t / cfg.windup);
            float angle = a.startAngle + cfg.dir * 0.4f * (1f - U.EaseOutQuad(p));
            chainLag *= Mathf.Exp(-14f * dt);
            chain.SetShape(hand, angle, Mathf.Lerp(0.3f, 0.55f, p) * cfg.reach, hand.y + 0.25f * p, chainLag, 0.25f);
            a.prevAngle = a.startAngle;
            if (a.t >= cfg.windup) { a.phase = "swing"; a.t = 0f; }
            return;
        }
        if (a.phase == "swing")
        {
            float p = Mathf.Clamp01(a.t / cfg.swing);
            float angle = a.startAngle + a.totalSweep * U.EaseOutQuad(p);           // 확 휘두르고 끝에서 감속
            float radius = cfg.reach * (0.55f + 0.45f * U.EaseOutQuad(Mathf.Min(1f, p / 0.3f))); // 쭉 펴짐
            float headY = hand.y + 0.25f - 0.3f * p;
            if (dt > 0f)
            {
                float angVel = Mathf.Abs(angle - a.prevAngle) / dt;
                chainLag = Mathf.Lerp(chainLag, cfg.dir * Mathf.Min(angVel * 0.04f, 1.1f), 0.5f); // 빠를수록 많이 휨
                SweepHits(a, a.prevAngle, angle);
                RecordTrail(a, hand, a.prevAngle, angle, radius, headY);
                if (cfg.lunge > 0f) { Pos += U.Dir(facing) * (cfg.lunge / cfg.swing * dt); ClampToArena(); } // 앞으로 밀고 들어감
            }
            chain.SetShape(Hand, angle, radius, headY, chainLag, 0f);
            a.prevAngle = angle;
            if (a.t >= cfg.swing) { a.phase = "recover"; a.t = 0f; }
            return;
        }
        // recover: 후딜. 사슬을 거둬들인다
        float pr = Mathf.Clamp01(a.t / cfg.recover);
        float ang = a.startAngle + a.totalSweep + cfg.dir * 0.2f * U.EaseOutQuad(pr);
        chainLag *= Mathf.Exp(-10f * dt);
        chain.SetShape(hand, ang, cfg.reach * (1f - 0.85f * U.EaseInQuad(pr)), hand.y - 0.05f, chainLag, 0.4f * pr);
        if (a.t >= cfg.recover) FinishAttack();
    }

    void FinishAttack()
    {
        int finished = atk.step;
        atk = null;
        if (hasBuffered)
        {
            var next = buffered; var nextAim = bufferedAim;
            hasBuffered = false; bufferedAim = null;
            if (finished >= Config.COMBO.Length) comboStep = 0; // 3타 끝이면 다음은 1타
            StartAttack(next, true, nextAim);
            return;
        }
        state = State.Free;
        chain.gameObject.SetActive(false);
        if (finished >= Config.COMBO.Length) { comboStep = 0; comboTimer = 0f; }
        else comboTimer = Config.COMBO_RESET_TIME;
    }

    void SweepHits(AttackRun a, float prev, float cur)
    {
        foreach (var e in enemies.list)
        {
            if (!e.alive || a.hit.Contains(e)) continue;
            var d = new Vector2(e.Pos.x - Pos.x, e.Pos.z - Pos.z);
            float dist = d.magnitude;
            if (dist - e.radius > a.cfg.reach + Config.HIT_PADDING) continue; // 사슬이 안 닿음
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
        int dmg = Mathf.Max(1, Mathf.RoundToInt(cfg.damage * (1f + Random.Range(-Config.DAMAGE_VARIANCE, Config.DAMAGE_VARIANCE))));
        bool killed = e.TakeHit(dmg, dir, cfg.knockback, cfg.stun);
        feel.HitStop(cfg.hitStopFrames + (killed ? Config.FEEL_KILL_BONUS_FRAMES : 0));
        feel.AddShake(cfg.shake + (killed ? Config.FEEL_KILL_BONUS_SHAKE : 0f));
        numbers.Spawn(e.HeadPosition, dmg, a.step == Config.COMBO.Length ? "heavy" : "normal");
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
                if (dt > 0f && target.alive) { feel.HitStop(2); feel.AddShake(Config.PULL_ARRIVE_SHAKE); } // 도착 '쿵'
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
