// =============================================================================
// Enemy.cs — 적(캡슐/박스 샌드백) + 적 무리 관리 (Godot판 enemy.gd + enemy_manager.gd)
// AI는 "플레이어 쪽으로 걸어온다"가 전부. 이 단계의 목적은 때리는 맛이다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class Enemy : MonoBehaviour
{
    public float radius = Config.ENEMY_RADIUS;
    public float height = Config.ENEMY_HEIGHT;
    public Vector3 vel;            // 넉백 속도 (맞으면 크게, 마찰로 줄어듦)
    public int hp = Config.ENEMY_MAX_HP;
    public bool alive = true;
    public float stun;             // 남은 기절 시간
    public bool pulled;            // 견인으로 끌려오는 중
    public bool respawnReady;

    float speed, flash, deathT, spawnT, pulledT;
    Material mat;

    public Vector3 Pos { get => transform.position; set => transform.position = value; }

    public static Enemy Create(bool capsule, Vector3 at)
    {
        var root = new GameObject(capsule ? "Enemy(capsule)" : "Enemy(box)");
        var e = root.AddComponent<Enemy>();
        e.speed = Config.ENEMY_SPEED * (1f + Random.Range(-Config.ENEMY_SPEED_VARIANCE, Config.ENEMY_SPEED_VARIANCE));
        // 도형 두 종류로 "다른 적"처럼 보이게 (에셋 없이 구분하는 가장 싼 방법)
        var body = GameObject.CreatePrimitive(capsule ? PrimitiveType.Capsule : PrimitiveType.Cube);
        Destroy(body.GetComponent<Collider>());
        body.transform.SetParent(root.transform, false);
        if (capsule) body.transform.localScale = new Vector3(e.radius * 1.7f, e.height / 2f, e.radius * 1.7f); // 기본 캡슐: 지름1·키2
        else body.transform.localScale = new Vector3(e.radius * 1.9f, e.height, e.radius * 1.9f);
        body.transform.localPosition = new Vector3(0, e.height / 2f, 0); // 발바닥이 바닥에
        e.mat = U.Flashable(capsule ? Config.Hex(0xd9534f) : Config.Hex(0xc2692f));
        body.GetComponent<Renderer>().sharedMaterial = e.mat;
        root.transform.position = at;
        return e;
    }

    public Vector3 HeadPosition => new Vector3(Pos.x, height + 0.3f, Pos.z);

    /// <summary>한 대 맞음. 이번 타격으로 죽으면 true</summary>
    public bool TakeHit(int damage, Vector3 dir, float knockback, float stunTime)
    {
        hp -= damage;
        flash = 1f;
        stun = Mathf.Max(stun, stunTime);
        pulled = false;                 // 끌려오던 중 맞으면 견인 취소
        vel = dir * knockback;          // '덮어쓰기': 연타해도 무한히 빨라지지 않는다
        if (hp <= 0)
        {
            alive = false; deathT = 0f; respawnReady = false;
            vel *= Config.ENEMY_KILL_KNOCKBACK_MULT;
            return true;
        }
        return false;
    }

    public void StartPulled() { pulled = true; pulledT = 0f; vel = Vector3.zero; }

    public void Respawn(Vector3 at)
    {
        hp = Config.ENEMY_MAX_HP; alive = true; respawnReady = false;
        stun = 0f; pulled = false; flash = 0f; spawnT = 0f; vel = Vector3.zero;
        Pos = at;
        ApplyVisual();
    }

    public void Tick(float dt, Vector3 playerPos)
    {
        if (!alive) { TickDead(dt); return; }
        spawnT += dt;
        flash = Mathf.Max(0f, flash - dt / Config.ENEMY_FLASH_TIME);
        if (pulled) TickPulled(dt, playerPos);
        else
        {
            Pos += vel * dt;                                   // 넉백 이동
            vel *= Mathf.Exp(-Config.ENEMY_KNOCKBACK_FRICTION * dt); // 지수 감속 (프레임레이트 무관)
            stun -= dt;
            if (stun <= 0f) Chase(dt, playerPos);
        }
        ClampToArena();
        ApplyVisual();
    }

    void Chase(float dt, Vector3 playerPos)
    {
        var d = new Vector2(playerPos.x - Pos.x, playerPos.z - Pos.z);
        float dist = d.magnitude;
        if (dist > Config.ENEMY_STOP_DISTANCE)
            Pos += new Vector3(d.x / dist, 0, d.y / dist) * speed * dt;
    }

    void TickPulled(float dt, Vector3 playerPos)
    {
        pulledT += dt;
        var d = new Vector2(playerPos.x - Pos.x, playerPos.z - Pos.z);
        float dist = d.magnitude;
        float step = Config.PULL_DRAG_SPEED * dt;
        if (dist - step <= Config.PULL_STOP_DISTANCE || pulledT > 1f)
        {
            // 도착! 멈추고 멍해진다 (도착 연출은 Player 가 pulled 꺼짐을 보고 처리)
            float keep = Config.PULL_STOP_DISTANCE;
            if (dist > keep) Pos = new Vector3(playerPos.x - d.x / dist * keep, Pos.y, playerPos.z - d.y / dist * keep);
            pulled = false; stun = Config.PULL_STUN; flash = 1f;
            return;
        }
        Pos += new Vector3(d.x / dist, 0, d.y / dist) * step;
    }

    void TickDead(float dt)
    {
        // 죽은 뒤: 마지막 넉백으로 날아가다 → 쪼그라들어 사라짐 → 부활 대기
        deathT += dt;
        flash = Mathf.Max(0f, flash - dt / Config.ENEMY_FLASH_TIME);
        Pos += vel * dt;
        vel *= Mathf.Exp(-Config.ENEMY_KNOCKBACK_FRICTION * dt);
        ClampToArena();
        ApplyVisual();
        if (deathT >= Config.ENEMY_RESPAWN_DELAY) respawnReady = true;
    }

    void ClampToArena()
    {
        float lim = Config.ARENA_HALF_SIZE - radius;
        Pos = new Vector3(Mathf.Clamp(Pos.x, -lim, lim), Pos.y, Mathf.Clamp(Pos.z, -lim, lim));
    }

    void ApplyVisual()
    {
        mat.SetColor("_EmissionColor", Color.white * (flash * 0.9f));
        // 등장 팝인(0→1) 또는 죽은 뒤 쪼그라듦(1→0)
        float b = U.EaseOutQuad(Mathf.Clamp01(spawnT / Config.ENEMY_SPAWN_POP_TIME));
        if (!alive) b = 1f - Mathf.Clamp01((deathT - Config.ENEMY_DEATH_HOLD) / Config.ENEMY_DEATH_SHRINK);
        // 맞은 순간: 옆으로 넓어지고 키가 줄어드는 찌그러짐 (무게감)
        float sx = 1f + Config.ENEMY_SQUASH * flash;
        float sy = 1f - Config.ENEMY_SQUASH * 0.8f * flash;
        transform.localScale = new Vector3(Mathf.Max(0.001f, b * sx), Mathf.Max(0.001f, b * sy), Mathf.Max(0.001f, b * sx));
    }

    /// <summary>마우스 광선이 몸통(세로 원기둥으로 근사)을 지나가나?</summary>
    public bool RayHitsBody(Ray ray)
    {
        if (!alive) return false;
        var center = Pos + new Vector3(0, height / 2f, 0);
        float t = Vector3.Dot(center - ray.origin, ray.direction);
        var closest = ray.origin + ray.direction * t;
        if (Mathf.Abs(closest.y - center.y) > height / 2f + 0.2f) return false;
        return new Vector2(closest.x - center.x, closest.z - center.z).magnitude <= radius * 1.1f;
    }
}

public class EnemyManager
{
    public readonly List<Enemy> list = new List<Enemy>();

    public void SpawnAll(Vector3 playerPos)
    {
        for (int i = 0; i < Config.ENEMY_COUNT; i++)
            list.Add(Enemy.Create(i % 2 == 0, SpawnPoint(playerPos, (float)i / Config.ENEMY_COUNT * U.TAU + 0.4f)));
    }

    Vector3 SpawnPoint(Vector3 c, float angle)
    {
        float lim = Config.ARENA_HALF_SIZE - 1f;
        return new Vector3(Mathf.Clamp(c.x + Mathf.Cos(angle) * Config.ENEMY_SPAWN_DISTANCE, -lim, lim), 0,
                           Mathf.Clamp(c.z + Mathf.Sin(angle) * Config.ENEMY_SPAWN_DISTANCE, -lim, lim));
    }

    public void Tick(float dt, Vector3 playerPos, float playerRadius)
    {
        foreach (var e in list)
        {
            e.Tick(dt, playerPos);
            if (!e.alive && e.respawnReady) e.Respawn(SpawnPoint(playerPos, Random.value * U.TAU));
        }
        if (dt <= 0f) return; // 히트스톱 중엔 밀어내기도 멈춘다
        var alive = list.FindAll(x => x.alive);
        for (int i = 0; i < alive.Count; i++)
        {
            var a = alive[i];
            for (int j = i + 1; j < alive.Count; j++)
            {
                var b = alive[j];
                if (a.pulled || b.pulled) continue;
                Separate(a, b.Pos, a.radius + b.radius, 0.5f, b);
            }
            if (!a.pulled) Separate(a, playerPos, a.radius + playerRadius, 1f, null);
        }
    }

    static void Separate(Enemy a, Vector3 other, float minDist, float share, Enemy b)
    {
        var d = new Vector2(a.Pos.x - other.x, a.Pos.z - other.z);
        float dist = d.magnitude;
        if (dist >= minDist || dist < 1e-5f) return;
        float push = (minDist - dist) * share;
        var n = new Vector3(d.x / dist, 0, d.y / dist);
        a.Pos += n * push;
        if (b != null) b.Pos -= n * push;
    }

    /// <summary>1순위: 광선이 몸에 닿음 / 2순위: 바닥 클릭 지점 근처 가장 가까운 적 (조작 관대함)</summary>
    public Enemy Pick(Ray ray, Vector3? ground, float nearRadius)
    {
        foreach (var e in list) if (e.RayHitsBody(ray)) return e;
        if (ground == null) return null;
        Enemy best = null; float bestD = nearRadius;
        foreach (var e in list)
        {
            if (!e.alive) continue;
            float d = new Vector2(e.Pos.x - ground.Value.x, e.Pos.z - ground.Value.z).magnitude;
            if (d <= bestD) { bestD = d; best = e; }
        }
        return best;
    }
}
