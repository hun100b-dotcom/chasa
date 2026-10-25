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

    JudgeSystem judge; Enemy boss; BossDef def; Act2Brain brain; Act3Brain brain3;   // 2막(5~8)은 brain, 3막(9~12)은 brain3 — 같은 화면 코드가 둘을 다 그린다
    readonly List<Tele> teles = new List<Tele>();
    readonly List<Enemy> soldiers = new List<Enemy>();
    float fightArea = 16f, closedToast;

    public void Init(JudgeSystem j, Enemy b, BossDef d)
    {
        judge = j; boss = b; def = d;
        judge.OnJudged += OnJudged;
        if (d.Id >= 9) brain3 = new Act3Brain(d.Id, () => Random.value); else brain = new Act2Brain(d.Id, () => Random.value);
        if (d.Id == 9) fightArea = 15f; else if (d.Id == 10 || d.Id == 11) fightArea = 14f; else if (d.Id == 12) fightArea = 18f;   // 기획 act3_map boss_arenas 반경
        if (d.Id == 7) fightArea = Balance.B07_ARENA_START + 2f;
    }

    Vector3 Flat(float x, float z) { return new Vector3(x, 0.03f + GroundTerrain.HeightAt(x, z), z); }

    void Update()
    {
        if (judge == null || boss == null || (brain == null && brain3 == null)) return;
        if (boss.soul.State == SoulState.Gone) { Clear(); return; }
        float dist = new Vector2(judge.player.Pos.x - def.X, judge.player.Pos.z - def.Z).magnitude;
        // B-10 난파 여울은 썰물 밤에만 열린다(밀물 밤엔 물에 잠김): 닫혀 있으면 싸움이 시작되지 않고 입구에서 한 줄 안내
        bool shoalClosed = def.Id == 10 && judge.clock != null && !(judge.clock.Phase == ClockPhase.Night && Tide.IsEbbNight(judge.clock.Day));
        closedToast -= Time.deltaTime;
        if (shoalClosed && dist < fightArea + 10f && closedToast <= 0f) { closedToast = 8f; judge.Say("물이 들었다"); }
        bool fight = !shoalClosed && dist < fightArea && boss.alive && !judge.cuts.Active && !judge.NightOver && !CharacterPanel.Open && !SettingsPanel.Open;
        if (!fight) { Clear(); return; }
        float dt = Time.deltaTime;
        soldiers.RemoveAll(s => s == null || !s.alive);
        if (brain != null) { brain.Maedhim = boss.soul.Maedhim; brain.MaedhimMax = boss.soul.MaedhimMax; brain.Soldiers = soldiers.Count; }
        else { brain3.Maedhim = boss.soul.Maedhim; brain3.MaedhimMax = boss.soul.MaedhimMax; }
        if (boss.kneeling) { Clear(); return; }   // 처결 대기 중엔 공격하지 않는다
        var mv = brain != null ? brain.Tick(dt) : brain3.Tick(dt);
        if (mv.Act != BossAct.None) Start(mv);
        TickTeles(dt);
        TickPoints();
    }

    // ---- 약점 점(사슬로 낚아챌 자리): 옷(B-09)·횃불(B-12)·깃발(B-05) ----
    PullPoint clothPt, torchPt, flagPt; GameObject clothView, torchView, flagView;
    PullPoint MakePoint(Vector3 at, Color col, float size, System.Action onPull, out GameObject view)
    {
        var g = GameObject.CreatePrimitive(PrimitiveType.Sphere); Destroy(g.GetComponent<Collider>());
        g.transform.position = Flat(at.x, at.z) + Vector3.up * 1.2f; g.transform.localScale = Vector3.one * size;
        g.GetComponent<Renderer>().sharedMaterial = U.Unlit(col); view = g;   // 눈에 띄는 색 구슬(임시: 아트가 옷·횃불 모델을 주면 교체)
        return PullPoints.Add(at, 2.5f, onPull);
    }
    void DropPoint(ref PullPoint p, ref GameObject v) { PullPoints.Remove(p); p = null; if (v != null) Destroy(v); v = null; }
    void DropPoints() { DropPoint(ref clothPt, ref clothView); DropPoint(ref torchPt, ref torchView); DropPoint(ref flagPt, ref flagView); }

    void Clear() { foreach (var t in teles) if (t.view != null) Destroy(t.view); teles.Clear(); DropPoints(); }
    void OnDestroy() { DropPoints(); if (judge != null) judge.OnJudged -= OnJudged; }

    /// <summary>처결 신호: B-05 에서 이름으로 불린 병사를 천도하면 대돌이 멈춘다(약점)</summary>
    void OnJudged(Enemy e, bool tendo)
    {
        if (brain == null || def == null || def.Id != 5 || !tendo || !soldiers.Contains(e)) return;
        brain.OnCalledSoulTendo(); judge.Say("불린 병사를 보냈다 — 대돌이 주춤한다");
    }

    /// <summary>약점 점의 시간 관리: B-09 옷은 창(2초)이 닫히면 사라지고, B-12 횃불은 큰물 단계에 한 번만 나타난다</summary>
    void TickPoints()
    {
        if (brain3 == null) return;
        if (clothPt != null && brain3.ClothWindow <= 0f) DropPoint(ref clothPt, ref clothView);
        if (brain3.BossId == 12 && brain3.Stage12 == 3 && !brain3.TorchDone && torchPt == null)
        {
            var at = new Vector3(def.X + (Random.value - 0.5f) * fightArea, 0f, def.Z + (Random.value - 0.5f) * fightArea);   // 물속 어딘가
            torchPt = MakePoint(at, new Color(1f, 0.6f, 0.2f, 1f), 0.7f, () =>
            {
                if (brain3.OnTorchPulled()) judge.Say("물속 횃불을 건졌다 — 흑월이 멈춘다");
                DropPoint(ref torchPt, ref torchView);
            }, out torchView);
            judge.Say("물속에 횃불이 하나 떠 있다");
        }
        if (brain3.Stage12 != 3 && torchPt != null) DropPoint(ref torchPt, ref torchView);
    }

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
            case BossAct.FlagPlant:
                Add(new Tele { shape = Shape.Circle, c = bp + dir * 5f, r = m.Radius, warn = 20f, mine = false }, false);
                DropPoint(ref flagPt, ref flagView);
                flagPt = MakePoint(bp + dir * 5f, new Color(0.9f, 0.2f, 0.2f, 1f), 0.6f, () => { brain.OnFlagPulled(); judge.Say("깃발을 뽑았다"); DropPoint(ref flagPt, ref flagView); }, out flagView);   // 견인으로 뽑으면 깃발 효과가 사라진다
                break;   // 깃발 반경(병사 공격 +20%는 다음 일). 피해 없이 표식만
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
            // ---- 3막(9~12): 예고 장판 ----
            case BossAct.WaveRows:   // B-09: 가로 띠 여러 줄이 차례로 밀려온다(줄 사이는 안전 띠)
                for (int i = 0; i < m.Count; i++)
                    Add(new Tele { shape = Shape.Bar, c = new Vector3(def.X, 0f, def.Z + (i - (m.Count - 1) * 0.5f) * m.Param), dir = Vector3.right, len = fightArea * 2f, wid = m.Radius, warn = m.Warn + i * Balance.B09_WAVE_STEP });
                Sfx.Play("sfx.boss.mangbu.wave"); break;
            case BossAct.CallSea: Add(new Tele { shape = Shape.Circle, c = bp, r = m.Radius, warn = m.Warn }); Sfx.Play("sfx.boss.mangbu.call"); break;
            case BossAct.ClothThrow:   // 2초 안에 사슬로 낚아채면 맺힘 −15%(실패해도 진행). 옷은 보스 손 앞에 구슬로 보인다
                judge.Say("아낙이 남편의 옷을 바다에 던지려 한다 — 사슬로 낚아채라");
                Sfx.Play("sfx.boss.mangbu.cloth.throw");
                DropPoint(ref clothPt, ref clothView);
                clothPt = MakePoint(bp + dir * 1.5f, new Color(0.8f, 0.9f, 1f, 1f), 0.6f, () =>
                {
                    float cut = brain3.OnClothCaught(); boss.soul.Maedhim = Mathf.Max(1, (int)brain3.Maedhim);
                    if (cut > 0f) { judge.Say("옷을 낚아챘다 — 아낙이 흔들린다"); Sfx.Play("sfx.boss.mangbu.cloth.catch"); }
                    DropPoint(ref clothPt, ref clothView);
                }, out clothView);
                break;
            case BossAct.RopeCut: case BossAct.RopeCross:
                for (int i = 0; i < m.Count; i++)
                {
                    var dd = m.Count == 1 ? dir : Quaternion.Euler(0f, i == 0 ? 35f : -35f, 0f) * dir;   // 두 줄이면 X 자로 엇갈린다
                    var cc = m.Count == 1 ? bp + dd * (m.Param * 0.5f) : pp;
                    Add(new Tele { shape = Shape.Bar, c = cc, dir = dd, len = m.Param, wid = m.Radius, warn = m.Warn });
                }
                break;
            case BossAct.RopeWrap: Add(new Tele { shape = Shape.Circle, c = pp, r = m.Radius, warn = m.Warn }); break;
            case BossAct.MatThrow: Add(new Tele { shape = Shape.Circle, c = pp, r = m.Radius, warn = m.Warn }); Sfx.Play("sfx.boss.wangcho.call"); break;
            case BossAct.StaffSwing: Add(new Tele { shape = Shape.Sector, c = bp, dir = dir, r = m.Radius, deg = m.Param, warn = m.Warn }); break;
            case BossAct.MirrorPull: Add(new Tele { shape = Shape.Bar, c = bp + dir * (m.Param * 0.5f), dir = dir, len = m.Param, wid = m.Radius, warn = m.Warn }); Sfx.Play("sfx.boss.heukwol.line.draw"); break;
            case BossAct.HisPahon: Add(new Tele { shape = Shape.Circle, c = pp, r = m.Radius, warn = m.Warn }); break;
            case BossAct.NameLines:   // 위(북)에서부터 한 줄씩, 마지막 줄은 비워 둔다(안전 지대)
                for (int i = 0; i < m.Count - 1; i++)
                    Add(new Tele { shape = Shape.Bar, c = new Vector3(def.X, 0f, def.Z + fightArea - 3f - i * (m.Radius + 1.5f)), dir = Vector3.right, len = fightArea * 2f, wid = m.Radius, warn = m.Warn + i * 0.5f });
                Sfx.Play("sfx.boss.heukwol.line.draw"); break;
            case BossAct.Flood:       // 물살: 가로 띠가 무작위 자리에서 차례로
                for (int i = 0; i < m.Count; i++)
                    Add(new Tele { shape = Shape.Bar, c = new Vector3(def.X, 0f, def.Z + (Random.value - 0.5f) * fightArea * 1.6f), dir = Vector3.right, len = fightArea * 2f, wid = m.Radius, warn = m.Warn + i * 0.6f });
                Sfx.Play("sfx.boss.heukwol.flood"); break;
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
