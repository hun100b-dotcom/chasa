// =============================================================================
// Act2BossArena.cs — 2막 보스 4종(B-05~B-08)의 '화면' 쪽: Core/Act2Boss.cs 의 Act2Brain 이 정한 행동을
// 붉은 예고 바닥(원·부채꼴·긴 막대)으로 그리고, 터지는 순간 플레이어가 안에 있으면 피해를 넘긴다.
// 지금은 뼈대: 수치는 임시값(balance B05~B08), 모양은 색 도형, 병사 소환·약점 신호(천도·파혼 연결)는 1차 연결만 했다.
// 왜 꺼 두나: 2막 땅·길이 아직 안 깔려 보스가 허공에 서게 된다. 주소에 ?act2=1 이 있을 때만 세운다(검사용).
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class Act2BossArena : MonoBehaviour
{
    public static bool Enabled { get { return FieldRules.Act2; } }   // 2막 땅이 깔려 있으면 보스 넷도 선다(금줄이 닫혀 있는 동안은 닿을 수 없다)

    enum Shape { Circle, Sector, Bar, Ring }
    class Tele { public Shape shape; public Vector3 c; public Vector3 dir; public float r, len, wid, gap, gapAt, deg, t, warn; public bool fired, paper, mine; public GameObject view; }

    JudgeSystem judge; Enemy boss; BossDef def; Act2Brain brain;
    readonly List<Tele> teles = new List<Tele>();
    readonly List<Enemy> soldiers = new List<Enemy>();
    float fightArea = 16f;

    public void Init(JudgeSystem j, Enemy b, BossDef d)
    {
        judge = j; boss = b; def = d;
        brain = new Act2Brain(d.Id, () => Random.value);
        if (d.Id == 7) fightArea = Balance.B07_ARENA_START + 2f;
    }

    Vector3 Flat(float x, float z) { return new Vector3(x, 0.03f + GroundTerrain.HeightAt(x, z), z); }

    void Update()
    {
        if (judge == null || boss == null || brain == null) return;
        if (boss.soul.State == SoulState.Gone) { Clear(); return; }
        float dist = new Vector2(judge.player.Pos.x - def.X, judge.player.Pos.z - def.Z).magnitude;
        bool fight = dist < fightArea && boss.alive && !judge.cuts.Active && !judge.NightOver && !CharacterPanel.Open && !SettingsPanel.Open;
        if (!fight) { Clear(); return; }
        float dt = Time.deltaTime;
        brain.Maedhim = boss.soul.Maedhim; brain.MaedhimMax = boss.soul.MaedhimMax;
        soldiers.RemoveAll(s => s == null || !s.alive);
        brain.Soldiers = soldiers.Count;
        if (boss.kneeling) { Clear(); return; }   // 처결 대기 중엔 공격하지 않는다
        var mv = brain.Tick(dt);
        if (mv.Act != BossAct.None) Start(mv);
        TickTeles(dt);
    }

    void Clear() { foreach (var t in teles) if (t.view != null) Destroy(t.view); teles.Clear(); }

    // ---- 행동 → 예고 바닥 -----------------------------------------------------
    void Start(BossMove m)
    {
        var bp = new Vector3(boss.Pos.x, 0f, boss.Pos.z); var pp = new Vector3(judge.player.Pos.x, 0f, judge.player.Pos.z);
        var to = pp - bp; var dir = to.sqrMagnitude > 0.01f ? to.normalized : Vector3.forward;
        switch (m.Act)
        {
            case BossAct.CallNames:
                for (int i = 0; i < m.Count; i++)   // 소환 병사: 보스 둘레(상한은 Act2Brain 이 지킨다). 번호 비율(m.Param)은 아직 화면에 안 쓴다
                    soldiers.Add(judge.enemies.SpawnCamp(bp + Quaternion.Euler(0f, 120f * i + 40f, 0f) * Vector3.forward * 3.5f, i % 2 == 0));
                Sfx.Play("sfx.boss.daedol.call"); break;
            case BossAct.FlagPlant: Add(new Tele { shape = Shape.Circle, c = bp + dir * 5f, r = m.Radius, warn = 20f, mine = false }, false); break;   // 깃발 반경(병사 공격 +20%는 다음 일). 피해 없이 표식만
            case BossAct.FlagSwing: Add(new Tele { shape = Shape.Circle, c = bp, r = m.Radius, warn = m.Warn }); break;
            case BossAct.PoleCharge: Add(new Tele { shape = Shape.Bar, c = bp + dir * (m.Param * 0.5f), dir = dir, len = m.Param, wid = 2f, warn = m.Warn }); break;
            case BossAct.LineForm:
                { var side = new Vector3(-dir.z, 0f, dir.x); Add(new Tele { shape = Shape.Bar, c = pp + dir * 1f, dir = side, len = m.Param, wid = 3f, gap = m.Radius, gapAt = (Random.value - 0.5f) * (m.Param - m.Radius), warn = m.Warn }); Sfx.Play("sfx.boss.general.command"); break; }
            case BossAct.CraneForm: Add(new Tele { shape = Shape.Sector, c = bp, dir = dir, r = m.Radius, deg = 120f, warn = m.Warn }); Sfx.Play("sfx.boss.general.command"); break;
            case BossAct.CircleForm: Add(new Tele { shape = Shape.Ring, c = pp, r = m.Radius, len = m.Param, warn = m.Warn }); Sfx.Play("sfx.boss.general.command"); break;   // 바깥 반경~안쪽 반경 사이가 위험, 한가운데가 안전(임시 해석)
            case BossAct.PickSwing: Add(new Tele { shape = Shape.Circle, c = bp + dir * 1.5f, r = m.Radius, warn = m.Warn }); break;
            case BossAct.RockFall:
                for (int i = 0; i < m.Count; i++)
                {
                    var o = i == 0 ? pp : bp + Quaternion.Euler(0f, Random.value * 360f, 0f) * Vector3.forward * Random.value * brain.ArenaRadius;   // 하나는 늘 플레이어 발밑(피하게 만든다)
                    Add(new Tele { shape = Shape.Circle, c = o, r = m.Radius, warn = m.Warn });
                }
                break;
            case BossAct.NumberMines:
                {
                    int paper = brain.PickNamePaper();
                    for (int i = 0; i < m.Count; i++)
                        Add(new Tele { shape = Shape.Circle, c = bp + Quaternion.Euler(0f, 360f / m.Count * i + Random.value * 40f, 0f) * Vector3.forward * (4f + Random.value * 4f), r = 1.2f, warn = m.Warn, paper = i == paper, mine = true });
                    Sfx.Play("sfx.boss.yeom.land"); break;
                }
            case BossAct.AbacusSweep: Add(new Tele { shape = Shape.Sector, c = bp, dir = dir, r = m.Radius, deg = m.Param, warn = m.Warn }); break;
            case BossAct.LedgerFlip: Sfx.Play("sfx.boss.yeom.backpage"); judge.Say("장부가 넘어간다"); break;   // 이름 종이 위만 안전한 연출은 다음 일
        }
    }

    void Add(Tele t, bool damaging = true)
    {
        t.t = 0f; if (!damaging) t.fired = true;   // 표식만(피해 없음)
        t.view = View(t); teles.Add(t);
    }

    GameObject View(Tele t)
    {
        GameObject g;
        switch (t.shape)
        {
            case Shape.Bar: g = GameObject.CreatePrimitive(PrimitiveType.Cube); g.transform.localScale = new Vector3(t.wid, 0.03f, t.len); g.transform.rotation = Quaternion.LookRotation(t.dir, Vector3.up); break;
            case Shape.Sector: g = GameObject.CreatePrimitive(PrimitiveType.Cylinder); g.transform.localScale = new Vector3(t.r * 2f, 0.03f, t.r * 2f); break;   // 부채꼴은 원판으로 대신 그린다(임시: 판정만 부채꼴)
            default: g = GameObject.CreatePrimitive(PrimitiveType.Cylinder); g.transform.localScale = new Vector3(t.r * 2f, 0.03f, t.r * 2f); break;
        }
        Destroy(g.GetComponent<Collider>());
        g.transform.position = Flat(t.c.x, t.c.z);
        g.GetComponent<Renderer>().sharedMaterial = U.Unlit(t.paper ? new Color(0.9f, 0.9f, 0.8f, 1f) : new Color(0.35f, 0.05f, 0.05f, 1f));
        return g;
    }

    bool Inside(Tele t, Vector3 p)
    {
        var d = new Vector3(p.x - t.c.x, 0f, p.z - t.c.z);
        switch (t.shape)
        {
            case Shape.Circle: return d.magnitude < t.r + 0.4f;
            case Shape.Ring: { float m = d.magnitude; return m < t.r + 0.4f && m > t.len; }
            case Shape.Sector:
                { float m = d.magnitude; if (m > t.r + 0.4f) return false; if (m < 0.5f) return true; return Vector3.Angle(t.dir, d) <= t.deg * 0.5f + 2f; }
            default:   // Bar: dir 방향이 긴 쪽. 빈칸(gap)은 긴 쪽 gapAt 중심의 구멍
            {
                float along = Vector3.Dot(d, t.dir), across = Vector3.Dot(d, Vector3.Cross(Vector3.up, t.dir));
                if (Mathf.Abs(across) > t.wid * 0.5f + 0.3f) return false;
                if (Mathf.Abs(along) > t.len * 0.5f) return false;
                if (t.gap > 0f && Mathf.Abs(along - t.gapAt) < t.gap * 0.5f) return false;
                return true;
            }
        }
    }

    void TickTeles(float dt)
    {
        for (int i = teles.Count - 1; i >= 0; i--)
        {
            var t = teles[i]; t.t += dt;
            if (!t.fired && t.t >= t.warn)
            {
                t.fired = true;
                bool inside = Inside(t, judge.player.Pos);
                if (inside && t.paper) { brain.OnNamePaperStepped(); boss.soul.Maedhim = Mathf.Max(1, (int)brain.Maedhim); }   // 이름 종이: 무해, 보스 맺힘 −2%
                else if (inside) judge.BossAreaHit(boss);
                if (t.view != null) t.view.GetComponent<Renderer>().sharedMaterial.color = new Color(1f, 0.55f, 0.25f, 1f);
            }
            else if (!t.fired && t.view != null)
                t.view.GetComponent<Renderer>().sharedMaterial.color = Color.Lerp(new Color(0.35f, 0.05f, 0.05f, 1f), new Color(0.85f, 0.12f, 0.1f, 1f), t.t / t.warn);
            if (t.t >= (t.warn < 19f ? t.warn + 0.25f : t.warn)) { if (t.view != null) Destroy(t.view); teles.RemoveAt(i); }
        }
    }
}
