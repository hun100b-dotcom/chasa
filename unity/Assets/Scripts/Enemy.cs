// =============================================================================
// Enemy.cs — 적(캡슐/박스 샌드백) + 적 무리 관리 (Godot판 enemy.gd + enemy_manager.gd)
// AI는 "플레이어 쪽으로 걸어온다"가 전부. 이 단계의 목적은 때리는 맛이다.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class Enemy : MonoBehaviour
{
    public int damage = Balance.ENEMY_ATTACK_DAMAGE;   // 공격력 (보스는 더 아프다)
    public float tiltWeak;                              // 나루 영감: 휩쓸기 뒤 배가 기울어 무방비인 남은 시간(초)
    public bool loner;                                 // 외톨이 야영지의 혼(소리: amb.loner)
    public string label;                               // 이름혼·보스 이름표 (없으면 null)
    public float radius = Config.ENEMY_RADIUS;
    public float height = Config.ENEMY_HEIGHT;
    public Vector3 vel;            // 넉백 속도 (맞으면 크게, 마찰로 줄어듦)
    // 처결 상태는 엔진과 무관한 Core 의 Soul 이 가진다 (맺힘·무릎·천도 캐스팅·떠남). 여기는 몸과 화면만 맡는다.
    public Soul soul = new Soul(SoulKind.Fresh);
    public bool alive => soul.State == SoulState.Active;        // 싸우는 중
    public bool kneeling => soul.State == SoulState.Kneel;       // 처결 대기 중 (천도·파혼 선택 가능)
    public bool sending => soul.State == SoulState.Sending;      // 천도 캐스팅 받는 중
    public bool gone => soul.State == SoulState.Gone;            // 떠났거나 터짐
    // ---- 필드 혼 3유형(넋두리·잔넋·묻힌 혼). 규칙은 Core/SoulTypes.cs, 수치는 balance.json SOULTYPE_* ----
    public SoulType type = SoulType.Plain;
    WailAi wail; BuriedAi buried; GameObject teleLine;
    public List<Enemy> group; public bool leader;    // 잔넋 무리: 대장을 처결하면 나머지가 잠깐 혼란
    public static Vector3 LastPlayer;                // 마지막으로 본 플레이어 자리(원념 탄이 명중을 재는 데 쓴다)
    /// <summary>맞을 수 있나? 땅속에 묻힌 혼은 솟기 전·묻힌 동안 맞지도 집히지도 않는다</summary>
    public bool Targetable { get { return type != SoulType.Buried || buried == null || SoulTypeRules.Reachable(type, buried.Phase); } }

    /// <summary>유형을 정하고 등급과 곱한 수치를 입힌다(맺힘·피해·속도·공격 시계). 만든 직후 한 번 부른다</summary>
    public void SetType(SoulType t)
    {
        type = t;
        soul.MaedhimMax = SoulTypeRules.Maedhim(t, soul.Kind, soul.MaedhimMax); soul.Maedhim = soul.MaedhimMax;
        damage = SoulTypeRules.Damage(t, soul.Kind);
        speed *= SoulTypeRules.Speed(t, soul.Kind);
        if (t == SoulType.Mote)
        {
            atk.WindupTime = Balance.SOULTYPE_MOTE_WINDUP; atk.Interval = Balance.SOULTYPE_MOTE_INTERVAL; atk.Range = Balance.SOULTYPE_MOTE_RANGE; atk.Cooldown = atk.Interval;
            radius *= 0.55f; height *= 0.5f;   // 작은 혼
        }
        else if (t == SoulType.Wail) wail = new WailAi();
        else if (t == SoulType.Buried) buried = new BuriedAi();
        if (t != SoulType.Plain) soul.Trick = false;   // 속임수는 보통 혼만
    }

    public bool camp;                                            // 필드 군집 소속: 처결되면 사라진다(제자리 재등장 없음)
    public bool extra;                                           // 얼룩 3개로 소환된 추가 적 (한 번 처리하면 사라짐)
    public float stun;             // 남은 기절 시간
    public AttackClock atk = new AttackClock();   // 공격 시계(쿨다운·예비동작) — 규칙은 Core에 있다
    public System.Action onKneel;                  // 맺힘 0 이 되어 무릎 꿇는 순간 한 번 불린다 (장비 드롭 판정용)
    bool dropRolled;                               // 이 혼 한 명당 드롭은 한 번만 (대기 초과로 다시 일어섰다 쓰러져도 재굴림 없음)
    public System.Action onHitPlayer;             // 공격이 명중하면 불린다 (EnemyManager가 플레이어 피해로 연결)
    public bool pulled;            // 견인으로 끌려오는 중
    public bool respawnReady;

    float speed, flash, deathT, spawnT, pulledT;
    public static float BoundBonus;   // 묶인 자 패시브: 묶인 적이 받는 피해 +%
    public float boundT;               // 묶임 남은 시간(휘감기·쇠사슬 울)
    public float weaponSlowT, weaponSlowAmt;   // 요령방울 타격 둔화(남은 초·비율)
    public int ink; public float inkT; public bool nameWritten;   // 명부 붓 먹 표식 수·남은 초, 이름을 써 둔 혼(천도 시전 단축)
    public float slowMult = 1f;        // 이동 감소 배율(배웅길: 천도 직후 적이 느려진다)
    Material mat;
    float deathHold = Config.ENEMY_DEATH_HOLD, deathShrink = Config.ENEMY_DEATH_SHRINK;   // 천도·파혼 모델 동작이 있으면 그 길이만큼 몸을 유지(동작이 스스로 흩어지는 모양)
    /// <summary>맞은 동작: 1 약(Hit1)·2 중(Hit2)·3 강(Stagger). 무릎 꿇음·죽음·보스(전용 동작 없는 것)에는 안 쓴다. 동작이 없는 모델이면 아무 일 없음</summary>
    public void ReactHit(int kind)
    {
        if (spr == null || !alive || kneeling) return;
        spr.PlayReact(kind >= 3 ? ActorModel.Pose.Stagger : kind == 2 ? ActorModel.Pose.Hit2 : ActorModel.Pose.Hit);
    }
    /// <summary>처결로 떠날 때 모델 동작(천도=Tendo 0.8초·파혼=Pahon 0.3초)을 틀고 그 길이만큼 몸을 남긴다</summary>
    public void PlayFinishAnim(bool tendo)
    {
        if (spr == null) return;
        float len = spr.PlayReact(tendo ? ActorModel.Pose.Tendo : ActorModel.Pose.Pahon);
        if (len > 0f) { deathHold = len; deathShrink = 0.05f; }
    }
    ActorSprite spr;               // 아트팀 그림(없으면 색 도형으로 대신)
    Renderer bodyRenderer;
    Vector3 lastPlayerPos;         // 그림이 플레이어 쪽을 보게 하려고 기억
    Color baseColor;               // 평소 색 (예비동작 붉은 신호에서 되돌아올 색)
    public bool capsuleShape;
    string variant;                // 구역에 따른 모양 변형 이름표(첫 호출 때 한 번 정한다). "" = 기본

    public Vector3 Pos { get => transform.position; set => transform.position = value; }

    public static Enemy Create(bool capsule, Vector3 at, float scale = 1f)
    {
        var root = new GameObject(capsule ? "Enemy(capsule)" : "Enemy(box)");
        var e = root.AddComponent<Enemy>();
        e.capsuleShape = capsule;
        e.radius *= scale; e.height *= scale;   // 보스는 크게 (몸 크기와 충돌 크기를 같이 키운다)
        e.soul = new Soul(RandomKind()); RollTrick(e.soul);
        e.speed = Config.ENEMY_SPEED * (1f + Random.Range(-Config.ENEMY_SPEED_VARIANCE, Config.ENEMY_SPEED_VARIANCE));
        // 도형 두 종류로 "다른 적"처럼 보이게 (에셋 없이 구분하는 가장 싼 방법)
        var body = GameObject.CreatePrimitive(capsule ? PrimitiveType.Capsule : PrimitiveType.Cube);
        Destroy(body.GetComponent<Collider>());
        body.transform.SetParent(root.transform, false);
        if (capsule) body.transform.localScale = new Vector3(e.radius * 1.7f, e.height / 2f, e.radius * 1.7f); // 기본 캡슐: 지름1·키2
        else body.transform.localScale = new Vector3(e.radius * 1.9f, e.height, e.radius * 1.9f);
        body.transform.localPosition = new Vector3(0, e.height / 2f, 0); // 발바닥이 바닥에
        e.bodyRenderer = body.GetComponent<Renderer>();
        e.spr = ActorSprite.Create(root.transform, null, true);
        e.baseColor = KindColor(e.soul.Kind);
        e.mat = U.Flashable(e.baseColor);
        body.GetComponent<Renderer>().sharedMaterial = e.mat;
        root.transform.position = at;
        GroundSnap.Attach(root);   // 새 땅 높이 따라 서 있는다
        return e;
    }

    /// <summary>보통 혼(덩어리 제외) 중 일부는 무릎 꿇은 척하는 속임수 혼이다 (TRICK_SPAWN_CHANCE)</summary>
    static void RollTrick(Soul s)
    {
        if (s.Kind != SoulKind.Lump && Random.value < Balance.TRICK_SPAWN_CHANCE) s.Trick = true;
    }

    /// <summary>혼 종류를 무작위로. 덩어리는 드물게 (LUMP_SPAWN_CHANCE)</summary>
    static SoulKind RandomKind()
    {
        if (Random.value < Balance.LUMP_SPAWN_CHANCE + MoonEffects.LumpBonus) return SoulKind.Lump;   // 그믐엔 덩어리가 많다
        return (SoulKind)Random.Range(0, 3);
    }

    /// <summary>혼 종류별 색. 색은 아트팀 팔레트(ChasaPalette)에서만 가져온다: 갓 죽은=청백, 해 넘긴=금, 오래된=주황, 덩어리=보라</summary>
    /// <summary>구역 이름 → 혼 모양 변형 꼬리표. 검은여울=역병, 붉은재=병사, 쇳골=광부. 2막 이후 구역이 field.json 에 생기면 이름만 맞으면 바로 쓰인다</summary>
    static string VariantOf(string zone)
    {
        if (string.IsNullOrEmpty(zone)) return "";
        if (zone.Contains("검은여울")) return "_yeoksa";
        if (zone.Contains("붉은재")) return "_bungjae";
        if (zone.Contains("쇳골")) return "_soegol";
        return "";
    }

    public static Color KindColor(SoulKind k)
    {
        switch (k)
        {
            case SoulKind.Fresh: return ChasaPalette.SoulFresh;
            case SoulKind.Year: return ChasaPalette.SoulDay;
            case SoulKind.Old: return ChasaPalette.SoulOld;
            default: return ChasaPalette.SoulMass;
        }
    }

    public Vector3 HeadPosition => new Vector3(Pos.x, Pos.y + height + 0.3f, Pos.z);   // 땅 높이(Pos.y)를 더해야 언덕에서도 숫자·막대가 머리 위에 붙는다

    /// <summary>한 대 맞음. 맺힘이 깎이고, 0이 되면 죽는 게 아니라 무릎을 꿇는다(true)</summary>
    public float barT;   // 맺힘 막대를 보이는 남은 시간(맞았을 때 3초). 보스는 늘 보인다
    public static float FierceMult = 1f;   // JudgeSystem 이 장비 합계에서 매 프레임 채운다
    public bool TakeHit(int damage, Vector3 dir, float knockback, float stunTime)
    {
        barT = 3f;
        if (!alive || !Targetable) return false;
        if (FierceMult != 1f && (soul.Boss || soul.Fierce || elite || soul.Kind == SoulKind.Lump)) damage = Mathf.Max(1, Mathf.RoundToInt(damage * FierceMult));   // 거센 혼·덩어리·보스 피해 옵션(상한 +50%)
        if (boundT > 0f && BoundBonus > 0f) damage = Mathf.Max(1, Mathf.RoundToInt(damage * (1f + BoundBonus)));
        if (Time.time < cageUntil) damage = Mathf.Max(1, Mathf.RoundToInt(damage * Balance.CAGE_DAMAGE_MULT));   // 쇠사슬 울 안: 받는 피해 +50%
        if (damageTakenMult != 1f) damage = Mathf.Max(1, Mathf.RoundToInt(damage * damageTakenMult));   // 보스 전용: 약점 창 규칙
        flash = 1f;
        stun = Mathf.Max(stun, stunTime);
        pulled = false;                 // 끌려오던 중 맞으면 견인 취소
        atk.Interrupt();                // 맞으면 예비동작이 끊긴다 (때리는 쪽이 이득)
        // 무게 배율: 보스는 안 밀리고(0), 덩어리·사나운 적은 덜 밀린다
        float weight = soul.Boss ? Balance.WEIGHT_BOSS : soul.Kind == SoulKind.Lump ? Balance.WEIGHT_LUMP : soul.Fierce ? Balance.WEIGHT_FIERCE : 1f;
        vel = dir * knockback * weight * knockMult;          // '덮어쓰기': 연타해도 무한히 빨라지지 않는다
        if (soul.TakeHit(damage))
        {
            if (!dropRolled) { dropRolled = true; onKneel?.Invoke(); }
            vel *= 0.5f;                // 무릎 꿇으며 조금만 미끄러진다
            return true;
        }
        return false;
    }

    /// <summary>천도·파혼으로 떠남. 몸은 쪼그라들어 사라진다</summary>
    public void Finish()
    {
        soul.Finish();
        if (leader && group != null) foreach (var m in group) if (m != null && m != this && m.alive) { m.stun = Mathf.Max(m.stun, Balance.SOULTYPE_MOTE_RATTLE_S); m.flash = 1f; }   // 무리 대장이 떠나면 나머지가 혼란
        if (teleLine != null) teleLine.SetActive(false);
        deathT = 0f; respawnReady = false; vel = Vector3.zero;
    }

    public void StartPulled() { pulled = true; pulledT = 0f; vel = Vector3.zero; }

    public void Respawn(Vector3 at)
    {
        soul = new Soul(RandomKind()); RollTrick(soul); respawnReady = false; dropRolled = false;
        stun = 0f; pulled = false; flash = 0f; spawnT = 0f; vel = Vector3.zero;
        Pos = at;
        baseColor = KindColor(soul.Kind);
        mat.color = baseColor;
        atk = new AttackClock();
        ApplyVisual();
    }

    /// <summary>이름혼(박돌쇠): 무명 혼보다 맺힘이 크고, 머리 위에 이름이 뜬다</summary>
    public void MakeNamed(string name)
    {
        extra = true; label = name;
        soul = Soul.Named(name, SoulKind.Fresh, Balance.NAMED_MAEDHIM);
        baseColor = ChasaPalette.SoulFresh; mat.color = baseColor;
    }

    /// <summary>이름혼으로 만든다(박돌쇠 등): 이름표·고유 혼 상태. 나이에 맞는 색을 입는다</summary>
    public void MakeNamed(string name, SoulKind kind, float waitBonus, string labelText = null)
    {
        label = labelText ?? name;   // 머리 위 이름표는 label, 기억·장례 찾기는 soul.Name — 단서를 이름표가 미리 새지 않게 갈랐다
        soul = Soul.Named(name, kind, Balance.MAEDHIM_NORMAL);
        soul.WaitBonus = waitBonus;
        baseColor = KindColor(kind); mat.color = baseColor;
    }

    /// <summary>고리 배율을 입힌다: 맺힘·공격이 고리를 따라 오른다(힘을 상한 밖으로 뺀 화력과 짝, 기획 act1-enemy-check)</summary>
    public void ApplyRing(int ring)
    {
        if (soul == null || ring <= 1) return;
        soul.Ring = ring;
        soul.MaedhimMax = Mathf.Max(1, Mathf.RoundToInt(soul.MaedhimMax * RingLoot.MaedhimMult(ring))); soul.Maedhim = soul.MaedhimMax;
        damage = Mathf.Max(1, Mathf.RoundToInt(damage * RingLoot.DamageMult(ring)));
    }

    /// <summary>S1 보스 나루 영감: 크고 느리고 한 방이 아프다</summary>
    // 보스 목줄: 플레이어가 40m 보다 멀면 쫓지 않고 처음 자리로 돌아간다.
    // 왜? 넓은 필드에서 몇 분 지나면 보스가 마을까지 걸어와 체력바가 마을에 뜨는 일이 있었다(PC 봇 측정).
    const float BossLeashM = 40f;
    Vector3 bossHome; bool bossHomeSet;
    void ReturnHome(float dt)
    {
        if (!bossHomeSet) return;
        var d = bossHome - Pos; d.y = 0f;
        if (d.magnitude < 0.5f) return;
        Pos += d.normalized * speed * slowMult * dt;
    }
    public void MakeBoss(int id = 1)
    {
        bossHome = Pos; bossHomeSet = true;
        var def = Bosses.Get(id);
        extra = true; label = def.Name;
        soul = Soul.MakeBoss(id);
        damage = def.Damage;
        speed *= def.Speed;
        // 1호 보랏빛 / 2호 오방 천(붉은 자주) / 3호 약탕 갈색 — 3D 모델이 없을 때의 색 도형 대역
        baseColor = id == 2 ? new Color(0.72f, 0.25f, 0.38f) : id == 3 ? new Color(0.45f, 0.33f, 0.20f) : new Color(0.55f, 0.42f, 0.78f);
        mat.color = baseColor;
    }

    public bool elite;                      // 거센 혼(첫 강적): 맺힘 300, 패턴 셋, 이름 띠. EliteArena 가 움직임을 맡는다
    public string eliteAnim = "";           // 거센 혼 예고 동작 꼬리표("", "attack", "strike")
    public bool eliteMote;                  // 거센 혼이 부른 잔넋(천도하면 조용히 흩어지고, 파혼 폭발에 함께 터진다)
    public float knockMult = 1f;            // 맞았을 때 밀림 배율(거센 혼 0.5)

    /// <summary>거센 혼으로 만든다(처음 10분 M10). 보통 공격은 없고(사거리 0), 예고 있는 패턴만 쓴다</summary>
    public void MakeElite()
    {
        elite = true; extra = true; label = "거센 혼";
        soul = new Soul(SoulKind.Year) { MaedhimMax = Balance.ELITE_MAEDHIM, Maedhim = Balance.ELITE_MAEDHIM };
        damage = Balance.ELITE_SLAM_DMG;
        knockMult = Balance.ELITE_KNOCKBACK_MULT;
        speed *= 0.85f;
        atk.Range = 0f;   // 몸으로 때리지 않는다(패턴만)
        baseColor = new Color(0.62f, 0.12f, 0.12f); mat.color = baseColor;
    }

    /// <summary>거센 혼이 부른 잔넋: 맺힘 30, 공격 4, 주기 2.6초</summary>
    public void MakeEliteMote()
    {
        SetType(SoulType.Mote);
        eliteMote = true; extra = true;
        soul.MaedhimMax = Balance.ELITE_MOTE_MAEDHIM; soul.Maedhim = Balance.ELITE_MOTE_MAEDHIM;
        damage = Balance.ELITE_MOTE_DMG;
        atk.Interval = Balance.ELITE_MOTE_INTERVAL; atk.Cooldown = atk.Interval;
    }

    public float cageUntil;                 // 쇠사슬 울에 갇힌 시각(이 시각까지 받는 피해 +50%)
    public float damageTakenMult = 1f;     // 받는 피해 배율(서 의원: 약점이 닫혀 있으면 0.25)

    /// <summary>얼룩 3개가 겹쳐 소환된 사나운 적 (P-010, P-011)</summary>
    public void MakeFierce()
    {
        extra = true;
        soul = new Soul(SoulKind.Fresh, true);
        baseColor = new Color(0.48f, 0.06f, 0.11f);
        mat.color = baseColor;
    }

    float freezeT;                      // 맞은 순간 이 적만 멈추는 시간(국소 히트스톱)

    /// <summary>
    /// 이 적만 잠깐 멈춘다 — 전체 정지 대신 '맞은 놈만 굳는' 히트스톱. 다른 적과 플레이어는 계속 움직여 여러 마리를 칠 때 끊기지 않는다.
    /// 멈춘 동안 번쩍임(flash)이 유지되고, 풀리면 쌓인 넉백 속도로 날아간다.
    /// </summary>
    public void Freeze(float seconds) { freezeT = Mathf.Max(freezeT, seconds); }

    // ---- 공격 차례(토큰): 동시에 때리는 보통 혼 수를 제한해, 둘러싸여도 한꺼번에 맞아 쓰러지지 않게 한다(기획 10-25) ----
    public static bool IntroCalm;                                       // 첫 25초(첫 5분 안): 가만히 서 있어도 쓰러지지 않게 원거리 혼(넋두리·묻힌 혼)은 쏘지 않고 근접도 한 마리씩만(PC 유휴 1분 검증)
    public static int TokenMax = int.MaxValue;                          // JudgeSystem 이 매 프레임 정한다(첫 5분엔 2, 이후 3)
    static readonly HashSet<Enemy> tokenHolders = new HashSet<Enemy>();   // 지금 예고·공격 중인 혼들
    public static void ResetTokens() { tokenHolders.Clear(); }

    public void Tick(float dt, Vector3 playerPos)
    {
        if (gone || !alive) tokenHolders.Remove(this);
        lastPlayerPos = playerPos; LastPlayer = playerPos;
        if (barT > 0f) barT -= dt;
        if (boundT > 0f) boundT -= dt;
        if (gone) { TickDead(dt); return; }
        if (freezeT > 0f && alive) { freezeT -= dt; flash = 1f; ApplyVisual(); return; }
        if (!alive)
        {
            // 무릎 꿇음 / 천도 캐스팅 중: 가만히 미끄러지다 멈춘다. 대기 시간이 흐르다가 다 되면 다시 일어선다
            Pos += vel * dt;
            vel *= Mathf.Exp(-Config.ENEMY_KNOCKBACK_FRICTION * dt);
            soul.Tick(dt);
            // 속임수 혼: 가까이 선 채로 도화선이 다 타면 벌떡 일어나 곧바로 덮친다
            float pd = new Vector2(playerPos.x - Pos.x, playerPos.z - Pos.z).magnitude;
            if (soul.TickTrick(dt, pd)) { atk.ForceWindup(); Sfx.Play("sfx.enemy.telegraph"); flash = 1f; }
            if (alive) { stun = soul.Stun; flash = 1f; }
            ClampToArena(); ApplyVisual();
            return;
        }
        spawnT += dt;
        flash = Mathf.Max(0f, flash - dt / Config.ENEMY_FLASH_TIME);
        if (pulled) { atk.Interrupt(); TickPulled(dt, playerPos); }
        else
        {
            Pos += vel * dt;                                   // 넉백 이동
            vel *= Mathf.Exp(-Config.ENEMY_KNOCKBACK_FRICTION * dt); // 지수 감속 (프레임레이트 무관)
            stun -= dt;
            bool canAct = stun <= 0f;
            float dist = new Vector2(playerPos.x - Pos.x, playerPos.z - Pos.z).magnitude;
            if (type == SoulType.Wail) TickWail(dt, playerPos, canAct && !IntroCalm, dist);
            else if (type == SoulType.Buried) { if (!IntroCalm) TickBuried(dt, canAct, dist); }
            else
            {
            // 예비동작 중에는 멈춰 서서 '곧 때린다'는 신호를 준다 (피할 시간)
            bool gated = !soul.Boss && !extra;   // 보스·추가 혼은 차례 제한이 없다
            if (gated) atk.Blocked = !atk.Winding && !tokenHolders.Contains(this) && tokenHolders.Count >= TokenMax;
            else atk.Blocked = false;
            if (canAct && !atk.Winding)
            {
                if (atk.Blocked && dist < Balance.TOKEN_WAIT_RING_M)   // 차례를 기다리는 혼: 둘레를 천천히 돌며 기다린다(겹쳐 서서 한 덩어리가 되지 않게)
                {
                    var tg = new Vector3(-(playerPos.z - Pos.z), 0f, playerPos.x - Pos.x) / Mathf.Max(0.01f, dist);
                    Pos += tg * speed * slowMult * 0.35f * dt;
                }
                else if (soul.Boss && FieldRules.On && dist > BossLeashM) ReturnHome(dt);   // 보스는 마당 근처에서만 쫓는다
                else Chase(dt, playerPos);
            }
            bool wasWind = atk.Winding;
            if (atk.Tick(dt, dist, canAct)) { if (soul.Boss && soul.BossId == 1) { Sfx.Play("sfx.boss.naru.sweep"); tiltWeak = 1.5f; } onHitPlayer?.Invoke(); }   // 나루 영감: 휩쓸기 판정 순간
            if (gated) { if (atk.Winding) tokenHolders.Add(this); else tokenHolders.Remove(this); }
            if (atk.Winding && !wasWind) Sfx.Play(type == SoulType.Mote ? "sfx.enemy.mote.telegraph" : soul.Boss && soul.BossId == 1 ? "sfx.boss.naru.sweep.telegraph" : "sfx.enemy.telegraph");   // 예비동작이 막 시작: 숨 들이켜는 소리
            // 신호: 예비동작이 진행될수록 붉게 달아오른다
            mat.color = atk.Winding ? Color.Lerp(baseColor, new Color(1f, 0.25f, 0.2f), atk.WindupRatio)
                                    : baseColor;
            }
        }
        ClampToArena();
        ApplyVisual();
    }

    /// <summary>넋두리: 7~9m 를 지키며(가까우면 천천히 물러난다) 선딜(바닥에 궤적 예고선) 뒤 원념 탄을 던진다</summary>
    void TickWail(float dt, Vector3 playerPos, bool canAct, float dist)
    {
        var to = new Vector3(playerPos.x - Pos.x, 0f, playerPos.z - Pos.z);
        var dir = dist > 0.01f ? to / dist : Vector3.forward;
        if (canAct && !wail.Winding)
        {
            int m = WailAi.MoveDir(dist);
            if (m != 0) Pos += dir * (m > 0 ? speed : -speed * 0.6f) * slowMult * dt;   // 물러날 땐 느리게
        }
        bool wasWind = wail.Winding;
        bool fire = wail.Tick(dt, dist, canAct);
        if (wail.Winding && !wasWind) Sfx.Play("sfx.enemy.wail.telegraph");   // 사운드 PR #25: 신종 혼 예고음
        if (fire) Sfx.Play("sfx.enemy.wail.throw");
        if (fire) WonnyeomOrb.Spawn(Pos + Vector3.up * 1.0f, dir, this);
        UpdateTeleLine(dir, Mathf.Min(dist, Balance.SOULTYPE_WAIL_ORB_RANGE_M));
        mat.color = wail.Winding ? Color.Lerp(baseColor, new Color(0.7f, 0.3f, 0.9f), wail.WindupRatio) : baseColor;
    }

    void UpdateTeleLine(Vector3 dir, float len)
    {
        bool on = wail != null && wail.Winding && alive;
        if (teleLine == null)
        {
            if (!on) return;
            teleLine = GameObject.CreatePrimitive(PrimitiveType.Cube);
            Destroy(teleLine.GetComponent<Collider>());
            teleLine.GetComponent<Renderer>().sharedMaterial = U.Unlit(new Color(0.55f, 0.2f, 0.75f));
        }
        teleLine.SetActive(on);
        if (!on) return;
        teleLine.transform.position = Pos + dir * (len * 0.5f) + Vector3.up * 0.05f;
        teleLine.transform.rotation = Quaternion.LookRotation(dir, Vector3.up);
        teleLine.transform.localScale = new Vector3(0.12f + 0.25f * wail.WindupRatio, 0.02f, len);   // 선딜이 찰수록 굵어진다
    }

    void OnDestroy() { if (teleLine != null) Destroy(teleLine); }

    /// <summary>묻힌 혼: 땅속 → (4.5m 안) 갈라짐 예고 → 솟음 → 붙잡기(범위 2m) → 묻힘 → 6초 뒤 재매복. 이동 없음</summary>
    void TickBuried(float dt, bool canAct, float dist)
    {
        var ph = buried.Phase;
        if (!canAct && ph != BuriedPhase.Hidden) { /* 기절 중엔 단계가 멈춘다 */ }
        else if (buried.Tick(dt, dist) && SoulTypeRules.Reachable(type, buried.Phase) && BuriedAi.InStrike(dist)) { Sfx.Play("sfx.enemy.buried.burst"); onHitPlayer?.Invoke(); }
        if (buried.Phase == BuriedPhase.Windup && ph == BuriedPhase.Hidden) Sfx.Play("sfx.enemy.buried.telegraph");
        mat.color = buried.Phase == BuriedPhase.Windup ? Color.Lerp(baseColor, new Color(1f, 0.25f, 0.2f), buried.T / Balance.SOULTYPE_BURIED_WINDUP) : baseColor;
    }

    void Chase(float dt, Vector3 playerPos)
    {
        var d = new Vector2(playerPos.x - Pos.x, playerPos.z - Pos.z);
        float dist = d.magnitude;
        if (dist > Config.ENEMY_STOP_DISTANCE)
            Pos += new Vector3(d.x / dist, 0, d.y / dist) * speed * slowMult * dt;
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
        // 맵 경계 + 집·장승 같은 막힌 곳 밖으로 밀어낸다 (규칙은 Core 의 MapLayout)
        float x = Pos.x, z = Pos.z;
        Chasa.Core.MapLayout.PushOut(ref x, ref z, radius);
        Pos = new Vector3(x, Pos.y, z);
    }

    /// <summary>상태에 맞는 그림을 고른다. 그림이 있으면 색 도형은 숨긴다</summary>
    void UpdateSprite()
    {
        if (spr == null) return;
        string n;
        bool down = kneeling || sending;
        if (soul.Boss)
        {
            string b = soul.BossId == 2 ? "boss_b02" : soul.BossId == 3 ? "boss_b03" : soul.BossId >= 4 ? Bosses.Get(soul.BossId).Model : "boss_naru";
            n = "boss/" + b + (atk.Winding ? "_attack" : down && soul.BossId > 1 ? "_kneel" : "_idle");
        }
        else if (elite)   // 거센 혼: 예고 동작은 EliteArena 가 eliteAnim 으로 알려 준다(attack = 내려치기 준비, strike = 덮치기 준비)
            n = "enemies/soul_elite_day" + (down ? "_kneel" : eliteAnim.Length > 0 ? "_" + eliteAnim : "");
        else if (soul.Fierce) n = "enemies/soul_fierce";
        else if (type != SoulType.Plain)
        {
            // 유형 모델(아트): 이름 = soul_<유형>_<등급> + 동작 꼬리표. 묻힌 혼은 땅속(hidden)·갈라짐/솟음(strike)·묻힘(sink) 동작이 따로 있다
            string g = soul.Kind == SoulKind.Year ? "day" : soul.Kind == SoulKind.Old ? "old" : soul.Kind == SoulKind.Lump ? "lump" : "fresh";
            string t = type == SoulType.Wail ? "wail" : type == SoulType.Mote ? "mote" : "buried";
            n = "enemies/soul_" + t + "_" + g;
            if (down) n += "_kneel";
            else if (type == SoulType.Buried) n += buried.Phase == BuriedPhase.Hidden ? "_hidden" : buried.Phase == BuriedPhase.Windup ? "_attack" : buried.Phase == BuriedPhase.Sink ? "_dodge" : buried.Phase == BuriedPhase.Strike ? "_strike" : "";
            else if (type == SoulType.Wail && wail.Winding) n += "_attack";
            else if (type == SoulType.Mote && atk.Winding) n += "_attack";
        }
        else switch (soul.Kind)
        {
            case SoulKind.Year: n = down ? "enemies/soul_day_kneel" : "enemies/soul_day"; break;
            case SoulKind.Old: n = down ? "enemies/soul_old_kneel" : "enemies/soul_old"; break;
            case SoulKind.Lump: n = "enemies/soul_lump"; break;   // 덩어리는 무릎 꿇는 그림이 없다
            default: n = down ? "enemies/soul_fresh_kneel" : "enemies/soul_fresh"; break;
        }
        // 구역 변형(3D 모델이 있을 때만): 검은여울의 혼은 역병(푸른 멍울) 모양. 이름 뒤에 _yeoksa 를 붙이면 ActorModel 이 변형 모델을 고른다
        if (View3D.On && !soul.Boss && !soul.Fierce && type == SoulType.Plain)
        {
            if (variant == null) variant = VariantOf(FieldZones.NameAt(Pos.x, Pos.z));
            /* 숫자 혼(인 없음)은 구역 모양 대신 번호 목패 모양을 쓴다. B-08 천도 뒤엔 이름 쪽지가 달린 모양으로 바뀌므로
               구역 이름표처럼 한 번에 굳히지 않고 매번 본다(Numbered 표식은 맺힌 뒤에 붙을 수 있어서이기도 하다) */
            if (soul.Numbered) n += Soul.NumberedBlurred ? "_number_named" : "_number";
            else if (variant.Length > 0) n += variant;
        }
        var look = lastPlayerPos - Pos;
        // 예비동작이면 붉게, 맞은 순간이면 하얗게 번쩍 (색 도형의 flash 와 같은 신호)
        var tint = Color.Lerp(Color.white, new Color(1f, 0.4f, 0.35f), atk.Winding ? atk.WindupRatio : 0f);
        tint = Color.Lerp(tint, new Color(1f, 1f, 1f), flash);
        bool shown = spr.Show(n, look, tint);
        if (bodyRenderer != null) bodyRenderer.enabled = !shown;
    }

    void ApplyVisual()
    {
        UpdateSprite();
        mat.SetColor("_EmissionColor", Color.white * (flash * 0.9f));
        // 등장 팝인(0→1) 또는 죽은 뒤 쪼그라듦(1→0)
        float b = U.EaseOutQuad(Mathf.Clamp01(spawnT / Config.ENEMY_SPAWN_POP_TIME));
        if (gone) b = 1f - Mathf.Clamp01((deathT - deathHold) / deathShrink);
        float kneel = alive || gone ? 1f : (View3D.On ? 0.92f : 0.62f);   // 3D 인형은 무릎 꿇는 자세가 따로 있어 덜 찌그러뜨린다   // 무릎 꿇으면 키가 줄어든다(눈으로 '처결 대기'를 알아보게)
        // 맞은 순간: 옆으로 넓어지고 키가 줄어드는 찌그러짐 (무게감)
        float sx = 1f + Config.ENEMY_SQUASH * flash;
        float sy = 1f - Config.ENEMY_SQUASH * 0.8f * flash;
        transform.localScale = new Vector3(Mathf.Max(0.001f, b * sx), Mathf.Max(0.001f, b * sy * kneel), Mathf.Max(0.001f, b * sx));
    }

    /// <summary>마우스 광선이 몸통(세로 원기둥으로 근사)을 지나가나?</summary>
    public bool RayHitsBody(Ray ray)
    {
        if (!Targetable) return false;
        if (gone) return false;
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
    public float graceT;                        // 밤 시작 유예: 이 시간 동안 적은 공격 준비를 시작하지 않는다
    public bool holdFire;                       // 첫 입력 전(로딩 중)에는 공격하지 않는다
    public bool spawnPaused;                    // true 면 잡몹이 다시 일어서듯 새로 나오지 않는다 (보스 천도 보호)
    public System.Action<Enemy> onEnemyKneel;   // 어느 적이 무릎 꿇었나 (JudgeSystem 이 장비 드롭 굴림)
    public System.Action<Enemy> onPlayerHit;   // 어느 적의 공격이 명중했는지 (JudgeSystem/GameMain이 체력 처리)

    /// <summary>원념 얼룩 3개가 겹친 자리에서 사나운 적이 솟아난다</summary>
    public Enemy SpawnFierce(Vector3 at)
    {
        var e = Enemy.Create(true, at);
        e.MakeFierce();
        e.onHitPlayer = () => onPlayerHit?.Invoke(e);
        e.onKneel = () => onEnemyKneel?.Invoke(e);
        list.Add(e);
        return e;
    }

    public Enemy SpawnNamed(Vector3 at, string name)
    {
        var e = Enemy.Create(false, at);
        e.MakeNamed(name);
        e.onHitPlayer = () => onPlayerHit?.Invoke(e);
        e.onKneel = () => onEnemyKneel?.Invoke(e);
        list.Add(e);
        return e;
    }

    public Enemy SpawnBoss(Vector3 at, int id = 1)
    {
        var e = Enemy.Create(true, at, 1.6f);
        e.MakeBoss(id);
        e.onHitPlayer = () => onPlayerHit?.Invoke(e);
        e.onKneel = () => onEnemyKneel?.Invoke(e);
        list.Add(e);
        return e;
    }

    /// <summary>거센 혼(첫 강적): 보통 혼의 1.3배 크기</summary>
    public Enemy SpawnElite(Vector3 at)
    {
        var e = Enemy.Create(true, at, Balance.ELITE_SCALE);
        e.MakeElite(); e.camp = true;
        e.onHitPlayer = () => onPlayerHit?.Invoke(e);
        e.onKneel = () => onEnemyKneel?.Invoke(e);
        list.Add(e);
        return e;
    }

    /// <summary>거센 혼이 부르는 잔넋</summary>
    public Enemy SpawnEliteMote(Vector3 at)
    {
        var e = Enemy.Create(true, at);
        e.MakeEliteMote(); e.camp = true;
        e.onHitPlayer = () => onPlayerHit?.Invoke(e);
        e.onKneel = () => onEnemyKneel?.Invoke(e);
        list.Add(e);
        return e;
    }

    /// <summary>처결 대기 중인 혼 중 pos 에서 가장 가까운 것 (사거리 안)</summary>
    public Enemy NearestKneeling(Vector3 pos, float range, System.Func<Enemy, bool> accept = null)
    {
        Enemy best = null; float bestD = range;
        foreach (var e in list)
        {
            if (!e.kneeling) continue;
            if (accept != null && !accept(e)) continue;   // 조건에 안 맞는 혼은 건너뛴다(예: 천도 못 하는 덩어리)
            float d = new Vector2(e.Pos.x - pos.x, e.Pos.z - pos.z).magnitude;
            if (d <= bestD) { bestD = d; best = e; }
        }
        return best;
    }

    /// <summary>필드 군집의 혼 하나를 세운다 (처결되면 그냥 사라진다: Respawn 하지 않음)</summary>
    public Enemy SpawnCamp(Vector3 at, bool a, SoulType type = SoulType.Plain, int ring = 1)
    {
        var e = Enemy.Create(a, at);
        if (type != SoulType.Plain) e.SetType(type);
        e.ApplyRing(ring);   // 고리 배율(맺힘·공격)
        e.camp = true;
        e.onHitPlayer = () => onPlayerHit?.Invoke(e);
        e.onKneel = () => onEnemyKneel?.Invoke(e);
        list.Add(e);
        return e;
    }

    /// <summary>목록에서 빼고 화면 부품도 지운다</summary>
    public void Remove(Enemy e) { if (e == null) return; list.Remove(e); Object.Destroy(e.gameObject); }

    public void SpawnAll(Vector3 playerPos)
    {
        for (int i = 0; i < Config.ENEMY_COUNT; i++)
        {
            var e = Enemy.Create(i % 2 == 0, SpawnPoint(playerPos, (float)i / Config.ENEMY_COUNT * U.TAU + 0.4f));
            e.onHitPlayer = () => onPlayerHit?.Invoke(e);
        e.onKneel = () => onEnemyKneel?.Invoke(e);
            list.Add(e);
        }
    }

    Vector3 SpawnPoint(Vector3 c, float angle)
    {
        // 플레이어 둘레 고리 위에서 태어나되, 맵 밖이거나 집 안이면 밀려난다
        float x = c.x + Mathf.Cos(angle) * Config.ENEMY_SPAWN_DISTANCE, z = c.z + Mathf.Sin(angle) * Config.ENEMY_SPAWN_DISTANCE;
        MapLayout.PushOut(ref x, ref z, Config.ENEMY_RADIUS + 1f);
        return new Vector3(x, 0, z);
    }

    public void Tick(float dt, Vector3 playerPos, float playerRadius)
    {
        var toRemove = new List<Enemy>();
        graceT = Mathf.Max(0f, graceT - dt);
        bool hold = holdFire || graceT > 0f;
        foreach (var e in list)
        {
            if (hold && e.alive) { e.atk.Interrupt(); e.atk.Cooldown = Balance.ENEMY_ATTACK_INTERVAL; }   // 유예 중엔 공격 시계를 계속 되감는다
            e.Tick(dt, playerPos);
            if (e.gone && e.respawnReady)
            {
                if (e.camp) { toRemove.Add(e); continue; }   // 필드 군집의 혼은 처결되면 끝(다시 서는 건 군집 규칙이 정한다)
                if (spawnPaused && !e.extra) continue;   // 스폰 정지 중엔 대기
                if (e.extra) { toRemove.Add(e); continue; }   // 소환된 적은 한 번 처리하면 끝 (계속 늘어나지 않게)
                e.Respawn(SpawnPoint(playerPos, Random.value * U.TAU));
            }
        }
        foreach (var e in toRemove) { list.Remove(e); Object.Destroy(e.gameObject); }
        if (dt <= 0f) return; // 히트스톱 중엔 밀어내기도 멈춘다
        var alive = list.FindAll(x => !x.gone);   // 무릎 꿇은 혼도 몸은 있으니 서로 겹치지 않게 밀어낸다
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
            if (e.gone || !e.Targetable) continue;
            float d = new Vector2(e.Pos.x - ground.Value.x, e.Pos.z - ground.Value.z).magnitude;
            if (d <= bestD) { bestD = d; best = e; }
        }
        return best;
    }
}
