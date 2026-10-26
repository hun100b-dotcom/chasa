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
    class Tele { public Vector3 ropeEnd; public bool rope; public string fireSfx; public bool drain; public float drainT; public bool weak; public Shape shape; public Vector3 c; public Vector3 dir; public float r, len, wid, gap, gapAt, deg, t, warn; public bool fired, paper, mine; public GameObject view; }

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
        bool fight = !shoalClosed && dist < fightArea && (boss.alive || boss.kneeling || boss.sending) && !judge.cuts.Active && !judge.NightOver && !CharacterPanel.Open && !SettingsPanel.Open;
        if (!fight) { Clear(); return; }
        float dt = Time.deltaTime;
        soldiers.RemoveAll(s => s == null || !s.alive);
        if (brain != null) { brain.Maedhim = boss.soul.Maedhim; brain.MaedhimMax = boss.soul.MaedhimMax; brain.Soldiers = soldiers.Count; }
        else { brain3.Maedhim = boss.soul.Maedhim; brain3.MaedhimMax = boss.soul.MaedhimMax; }
        if (boss.kneeling || boss.sending) { KneelTick(dt); return; }   // 천도 시전 중에도 압박은 이어진다   // 처결 대기 중엔 평소 공격은 멈추고, 보스별 약한 압박 하나만 돈다
        kneelBegun = false;
        var mv = brain != null ? brain.Tick(dt) : brain3.Tick(dt);
        if (mv.Act != BossAct.None) Start(mv);
        TickTeles(dt);
        TickPoints();
        // B-06 약점: 일자진의 빈칸(안전 자리)에 서서 때리면 피해가 커진다(Balance.B06_GAP_DMG_MULT). 대형이 떠 있는 동안만
        if (brain != null && def.Id == 7) TickMiners(dt);
        if (brain3 != null) TickHelpers(dt);
        if (brain3 != null && def.Id == 10) { TickTilt(dt); TickRope(dt); }
        if (brain != null && def.Id == 6) boss.damageTakenMult = brain.DamageMultAt(PlayerInFormGap());
    }

    // ---- 꿇은 동안의 약한 압박(기획 boss-final-moment-act1-2·act3) ----
    // 왜: 압박이 없으면 천도 1.5초가 늘 안전해 천도로 쏠리고, 이미 나온 병사·혼이 계속 때리면 앞선 판에 따라 운으로 갈린다.
    //     그래서 보스가 꿇은 동안 4.5초마다 보스별 압박 하나만 보내고(천도는 때를 맞춰야 하고 파혼은 즉시), 평소 공격은 멈춘다.
    bool kneelBegun; float kneelT;
    void KneelTick(float dt)
    {
        var bp = new Vector3(boss.Pos.x, 0f, boss.Pos.z); var pp = new Vector3(judge.player.Pos.x, 0f, judge.player.Pos.z);
        var to = pp - bp; var dir = to.sqrMagnitude > 0.01f ? to.normalized : Vector3.forward;
        if (!kneelBegun)
        {
            kneelBegun = true;
            kneelT = def.Id == 6 ? 1.0f : Balance.KNEEL_PRESS_GAP;   // 장수는 꿇은 뒤 1초에 첫 대형, 나머지는 한 간격 뒤
            // 보스 곁의 혼 정리: 대돌(번호 병사 최대 2), 흑월 2차(남은 물 혼 모두), 아낙(물 혼 1)
            int keep = def.Id == 5 ? Balance.B05_KNEEL_KEEP_NUMBERED : def.Id == 9 ? 1 : def.Id == 12 ? 0 : -1;
            if (keep >= 0)
            {
                var list = def.Id == 5 ? soldiers : new List<Enemy>(helpers.Keys);
                for (int i = list.Count - 1; i >= keep; i--) if (list[i] != null && list[i].alive) { list[i].Finish(); }
                if (def.Id == 5) soldiers.Clear();
            }
            if (def.Id == 11) foreach (var kv in helpers) if (kv.Key != null && kv.Value == 3) kv.Key.passive = true;   // 왕초가 꿇으면 별명 혼들이 협공을 멈추고 앉는다
            // 평소 예고는 거두되, 염씨의 숫자 지뢰는 그대로 둔다
            for (int i = teles.Count - 1; i >= 0; i--) { if (def.Id == 8 && teles[i].mine) continue; if (teles[i].view != null) Destroy(teles[i].view); teles.RemoveAt(i); }
            DropPoints();
        }
        TickTeles(dt);
        if (brain3 != null && def.Id == 10) TickTilt(dt);   // 선장: 갑판 기울기는 꿇은 동안에도 돈다(미끄러지면 처결 거리를 벗어나 천도가 끊긴다)
        if (def.Id == 12 || def.Id == 1) return;   // 흑월 2차는 압박 없음
        kneelT -= dt;
        if (kneelT > 0f) return;
        kneelT = Balance.KNEEL_PRESS_GAP;
        switch (def.Id)
        {
            case 5: return;   // 대돌: 남은 번호 병사가 곧 압박이라 따로 안 보낸다
            case 6: Add(new Tele { shape = Shape.Ring, c = bp, r = Balance.B06_CIRCLE_START, len = 2.8f, warn = Balance.KNEEL_PRESS_WARN }); Sfx.Play("sfx.boss.general.command"); break;   // 빈칸은 장수 2.8m 안
            case 7: Start(new BossMove { Act = BossAct.RockFall, Warn = Balance.KNEEL_PRESS_WARN, Radius = Balance.B07_ROCK_RADIUS, Count = 3 }); break;   // 낙석 3곳, 하나는 내 발밑
            case 8: Start(new BossMove { Act = BossAct.NumberMines, Warn = Balance.KNEEL_PRESS_WARN, Count = 4, Param = Balance.B08_MINE_MULT }); break;   // 숫자 4장
            case 9: Start(new BossMove { Act = BossAct.WaveRows, Warn = Balance.KNEEL_PRESS_WARN, Count = 1, Radius = Balance.B09_WAVE_WIDTH, Param = Balance.B09_WAVE_STRIDE }); break;   // 파도 1줄
            case 11: Start(new BossMove { Act = BossAct.MatThrow, Warn = Balance.KNEEL_PRESS_WARN, Radius = Balance.B11_MAT_RADIUS }); break;   // 거적 던지기
        }
    }

    // ---- B-10 약점: 줄 끊기 직후 늘어진 밧줄 끝을 2초 동안 사슬로 끌면 선장이 넘어진다(멈칫 1.5초 + 맺힘 피해 ×1.5 2초) ----
    void SpawnRopeEnd(Vector3 at)
    {
        DropPoint(ref ropePt, ref ropeView);
        ropePt = MakePoint(at, new Color(0.75f, 0.6f, 0.35f, 1f), 0.55f, () =>
        {
            brain3.Stun = Mathf.Max(brain3.Stun, 1.5f); ropeWeakT = 2f;
            judge.PatternEvent("B-10.weak_rope", boss, true);   // 처음 넘어질 때만 말풍선 "…무겁다."
            DropPoint(ref ropePt, ref ropeView);
        }, out ropeView);
        ropeT = 2f; judge.Say("밧줄 끝 — 끌어당겨라", 2f);
    }
    void TickRope(float dt)
    {
        if (ropePt != null) { ropeT -= dt; if (ropeT <= 0f) DropPoint(ref ropePt, ref ropeView); }
        if (ropeWeakT > 0f) ropeWeakT -= dt;
        if (boss != null) boss.damageTakenMult = ropeWeakT > 0f ? 1.5f : 1f;
    }

    // ---- B-10 기운 갑판: 6초마다(맺힘 50% 뒤 4초) 갑판이 좌우로 기울어 1.5초 동안 1.5 m/s 로 미끄러진다 ----
    float tiltT = 3f, tiltSlide, tiltSide = 1f; bool stormSaid;
    void TickTilt(float dt)
    {
        if (boss == null || !(boss.alive || boss.kneeling || boss.sending)) return;
        float dist = new Vector2(judge.player.Pos.x - def.X, judge.player.Pos.z - def.Z).magnitude;
        if (dist > fightArea + 6f) return;   // 싸움터 근처에서만
        bool storm = brain3.Phase2;
        if (storm && !stormSaid) { stormSaid = true; judge.PatternEvent("B-10.storm", boss, true, 2); }   // 알림 한 줄과 말풍선이 같은 글이라 한 번에(서사 C10) // 전용 소리 없음 → 기울기 소리를 두 번 겹쳐 쓴다(서사)
        tiltT -= dt;
        if (tiltT <= 0f)
        {
            tiltT = storm ? 4f : 6f; tiltSlide = 1.5f; tiltSide = -tiltSide;
            judge.PatternEvent("B-10.tilt", boss, true, storm ? 2 : 1);
        }
        if (tiltSlide > 0f)
        {
            tiltSlide -= dt;
            var push = new Vector3(tiltSide, 0f, 0f) * 1.5f * dt;
            float px = judge.player.Pos.x + push.x, pz = judge.player.Pos.z + push.z;
            MapLayout.PushOut(ref px, ref pz, 0.5f);
            judge.player.Pos = new Vector3(px, judge.player.Pos.y, pz);
        }
    }

    // ---- 3막 보스 곁의 혼(약점): 1 물 혼(B-09) · 2 선원(B-10) · 3 별명 혼(B-11) · 4 물 혼(B-12) ----
    readonly Dictionary<Enemy, int> helpers = new Dictionary<Enemy, int>(); int weakWaves; float nickT; bool sailorsSpawned;
    void SpawnHelper(int kind, Vector3 at) { var h = judge.enemies.SpawnCamp(at, kind % 2 == 0); if (h != null) { helpers[h] = kind; if (kind == 2) h.passive = true; } }   // 선원(2)은 처음부터 공격하지 않는다 — 칠성 광부처럼 처결만 받는다(기획 B10_SAILORS_ATTACK false)
    Vector3 ArenaPoint(float radFrac)
    {
        float a = Random.value * 360f;
        return new Vector3(def.X, 0f, def.Z) + Quaternion.Euler(0f, a, 0f) * Vector3.forward * (fightArea * radFrac);
    }
    void TickHelpers(float dt)
    {
        var dead = new List<Enemy>(); foreach (var kv in helpers) if (kv.Key == null || !kv.Key.alive) dead.Add(kv.Key);
        foreach (var d in dead) helpers.Remove(d);
        if (def.Id == 10 && !sailorsSpawned)   // 난간에 선원 혼 일곱
        {
            sailorsSpawned = true;
            for (int i = 0; i < 7; i++) SpawnHelper(2, new Vector3(def.X, 0f, def.Z) + Quaternion.Euler(0f, 360f / 7f * i, 0f) * Vector3.forward * (fightArea * 0.7f));
            judge.Say("난간에 선원 혼이 매달려 있다");
        }
        if (def.Id == 11)   // 별명 부르기: 10초마다 두 혼이 그 이름으로 일어난다
        {
            nickT -= dt;
            if (nickT <= 0f) { nickT = 10f; SpawnHelper(3, ArenaPoint(0.6f)); SpawnHelper(3, ArenaPoint(0.6f)); judge.Say("왕초가 별명을 부른다"); Sfx.Play("sfx.boss.wangcho.rise"); }
        }
    }

    // ---- B-07 광부 혼: 막장 안쪽 둘레에 다섯씩 나타난다. 다 보내거나 깨면 6초 뒤 다시 한 무리 ----
    readonly List<Enemy> miners = new List<Enemy>(); float minerT;
    void TickMiners(float dt)
    {
        miners.RemoveAll(m => m == null || !m.alive);
        if (miners.Count > 0) return;
        minerT -= dt;
        if (minerT > 0f) return;
        minerT = Balance.B07_MINERS > 0 ? 6f : 1e9f;
        var c = new Vector3(def.X, 0f, def.Z);
        for (int i = 0; i < Balance.B07_MINERS; i++)
            miners.Add(judge.enemies.SpawnCamp(c + Quaternion.Euler(0f, 72f * i + 18f, 0f) * Vector3.forward * (brain.ArenaRadius > 1f ? brain.ArenaRadius * 0.6f : 8f), i % 2 == 0));
        judge.Say("광부 혼이 나타났다 — 출구로 보내라"); Sfx.Play("sfx.boss.chilsung.count");
    }

    /// <summary>플레이어가 지금 떠 있는 일자진 예고의 빈칸 안에 서 있나</summary>
    bool PlayerInFormGap()
    {
        var p = judge.player.Pos;
        foreach (var t in teles)
        {
            if (t.shape != Shape.Bar || t.gap <= 0f) continue;
            var d = new Vector3(p.x - t.c.x, 0f, p.z - t.c.z);
            float along = Vector3.Dot(d, t.dir), across = Vector3.Dot(d, Vector3.Cross(Vector3.up, t.dir));
            if (Mathf.Abs(across) <= t.wid * 0.5f + 0.3f && Mathf.Abs(along - t.gapAt) < t.gap * 0.5f) return true;
        }
        return false;
    }

    // ---- 약점 점(사슬로 낚아챌 자리): 옷(B-09)·횃불(B-12)·깃발(B-05) ----
    PullPoint clothPt, torchPt, flagPt, ropePt; GameObject clothView, torchView, flagView, ropeView; float ropeT, ropeWeakT;   // 선장 줄 끝(B-10)
    PullPoint MakePoint(Vector3 at, Color col, float size, System.Action onPull, out GameObject view, string model = null)
    {
        GameObject g = null;
        var prefab = model != null ? Resources.Load<GameObject>("Models/Boss/" + model) : null;   // 아트 소품(옷·횃불·군기). 없으면 색 구슬 대역
        if (prefab != null)
        {
            g = Instantiate(prefab, Flat(at.x, at.z), Quaternion.Euler(0f, 180f, 0f));   // glTFast 가 읽은 GLB 는 앞이 반대라 180(모델 표 yaw 와 같은 이유)
            foreach (var c in g.GetComponentsInChildren<Collider>()) Destroy(c);
            var lt = g.transform.Find("Light_grab_torch");   // 횃불: 빈 오브젝트 자리에 주황 점광원(아트 지정: 세기 1.6·범위 7m)
            if (lt != null && QualityTier.Current != QualityTier.Level.Low) { var l = lt.gameObject.AddComponent<Light>(); l.type = LightType.Point; l.color = new Color(1f, 0.6f, 0.25f); l.intensity = 1.6f; l.range = 7f; l.shadows = LightShadows.None; }
        }
        else
        {
            g = GameObject.CreatePrimitive(PrimitiveType.Sphere); Destroy(g.GetComponent<Collider>());
            g.transform.position = Flat(at.x, at.z) + Vector3.up * 1.2f; g.transform.localScale = Vector3.one * size;
            g.GetComponent<Renderer>().sharedMaterial = U.Unlit(col);
        }
        view = g;
        return PullPoints.Add(at, 2.5f, onPull);
    }
    void DropPoint(ref PullPoint p, ref GameObject v) { PullPoints.Remove(p); p = null; if (v != null) Destroy(v); v = null; }
    void DropPoints() { DropPoint(ref ropePt, ref ropeView); DropPoint(ref clothPt, ref clothView); DropPoint(ref torchPt, ref torchView); DropPoint(ref flagPt, ref flagView); }

    void Clear() { foreach (var t in teles) if (t.view != null) Destroy(t.view); teles.Clear(); DropPoints(); if (boss != null) boss.damageTakenMult = 1f; }
    void OnDestroy() { DropPoints(); if (judge != null) judge.OnJudged -= OnJudged; }

    /// <summary>처결 신호: B-05 에서 이름으로 불린 병사를 천도하면 대돌이 멈춘다(약점)</summary>
    void OnJudged(Enemy e, bool tendo)
    {
        int hk;
        if (brain3 != null && helpers.TryGetValue(e, out hk))
        {
            // 3막 보스 곁의 혼들: 천도하면 보스가 약해진다(약점). 파혼하면 아무 보상도 없다(기획)
            helpers.Remove(e);
            if (!tendo) return;
            float cut = 0f;
            if (hk == 1) { weakWaves++; judge.Say("물 혼을 보냈다 — 다음 파도가 약해진다"); }
            else if (hk == 2) { cut = 5f; judge.Say("선원을 보냈다 — 선장이 흔들린다"); }
            else if (hk == 3) { brain3.Stun = Mathf.Max(brain3.Stun, 1.5f); judge.Say("별명을 불렀다 — 왕초가 멈칫한다"); }
            else if (hk == 4) { cut = 3f; judge.Say("물 혼을 보냈다 — 맺힘이 풀린다"); }
            if (cut > 0f) boss.soul.Maedhim = Mathf.Max(1, boss.soul.Maedhim - Mathf.RoundToInt(boss.soul.MaedhimMax * cut / 100f));
            return;
        }
        if (brain != null && def != null && def.Id == 7 && miners.Contains(e))
        {
            // B-07 광부 혼: 천도 = 출구로 보냄(다섯마다 칠성이 멈춤), 파혼 = 보스 맺힘 +10% · 10초 광폭
            miners.Remove(e);
            if (tendo) { brain.OnMinerExit(); judge.Say("광부 " + brain.MinersOut + "명을 내보냈다"); if (brain.Stun > 0f) judge.Say("칠성이 멈칫한다"); }
            else { brain.OnMinerPahon(); boss.soul.Maedhim = Mathf.Min(boss.soul.MaedhimMax, (int)brain.Maedhim); judge.Say("광부를 깨뜨렸다 — 칠성이 날뛴다!"); Sfx.Play("sfx.boss.chilsung.rage"); }
            return;
        }
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
                judge.snatched.Add(12); if (brain3.OnTorchPulled()) judge.Say("물속 횃불을 건졌다 — 흑월이 멈춘다");
                DropPoint(ref torchPt, ref torchView);
            }, out torchView, "boss_grab_torch_b12");
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
                Sfx.Play("sfx.boss.daedol.call"); Sfx.PlayLater("sfx.boss.daedol.number", 0.6f); break;   // 이름을 잊어 번호로 부르는 소리
            case BossAct.FlagPlant:
                Add(new Tele { shape = Shape.Circle, c = bp + dir * 5f, r = m.Radius, warn = 20f, mine = false }, false);
                DropPoint(ref flagPt, ref flagView);
                flagPt = MakePoint(bp + dir * 5f, new Color(0.9f, 0.2f, 0.2f, 1f), 0.6f, () => { brain.OnFlagPulled(); judge.snatched.Add(5); judge.Say("깃발을 뽑았다 — 이 보스를 부르는 시간이 짧아진다"); DropPoint(ref flagPt, ref flagView); }, out flagView, "boss_grab_flag_b05");   // 견인으로 뽑으면 깃발 효과가 사라진다
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
                    Sfx.Play("sfx.boss.yeom.land"); Sfx.Play("sfx.boss.yeom.throw"); break;   // 숫자 지뢰를 날리는 순간
                }
            case BossAct.AbacusSweep: Add(new Tele { shape = Shape.Sector, c = bp, dir = dir, r = m.Radius, deg = m.Param, warn = m.Warn }); break;
            // ---- 3막(9~12): 예고 장판 ----
            case BossAct.WaveRows:   // B-09: 가로 띠 여러 줄이 차례로 밀려온다(줄 사이는 안전 띠)
                for (int i = 0; i < m.Count; i++)
                    Add(new Tele { weak = i == 0 && weakWaves > 0, shape = Shape.Bar, c = new Vector3(def.X, 0f, def.Z + (i - (m.Count - 1) * 0.5f) * m.Param), dir = Vector3.right, len = fightArea * 2f, wid = m.Radius, warn = m.Warn + i * Balance.B09_WAVE_STEP });
                if (weakWaves > 0) weakWaves--;
                if (helpers.Count < 3) SpawnHelper(1, ArenaPoint(0.5f));   // 파도마다 물 혼 하나가 실려 온다
                Sfx.Play("sfx.boss.mangbu.wave"); break;
            case BossAct.CallSea: Add(new Tele { shape = Shape.Circle, c = bp, r = m.Radius, warn = m.Warn }); Sfx.Play("sfx.boss.mangbu.call"); break;
            case BossAct.ClothThrow:   // 2초 안에 사슬로 낚아채면 맺힘 −15%(실패해도 진행). 옷은 보스 손 앞에 구슬로 보인다
                judge.Say("아낙이 남편의 옷을 바다에 던지려 한다 — 사슬로 낚아채라");
                Sfx.Play("sfx.boss.mangbu.cloth.throw");
                DropPoint(ref clothPt, ref clothView);
                clothPt = MakePoint(bp + dir * 1.5f, new Color(0.8f, 0.9f, 1f, 1f), 0.6f, () =>
                {
                    judge.snatched.Add(9); float cut = brain3.OnClothCaught(); boss.soul.Maedhim = Mathf.Max(1, (int)brain3.Maedhim);
                    if (cut > 0f) { judge.Say("옷을 낚아챘다 — 아낙이 흔들린다"); Sfx.Play("sfx.boss.mangbu.cloth.catch"); }
                    DropPoint(ref clothPt, ref clothView);
                }, out clothView, "boss_grab_clothes_b09");
                break;
            case BossAct.RopeCut: case BossAct.RopeCross:
                for (int i = 0; i < m.Count; i++)
                {
                    var dd = m.Count == 1 ? dir : Quaternion.Euler(0f, i == 0 ? 35f : -35f, 0f) * dir;   // 두 줄이면 X 자로 엇갈린다
                    var cc = m.Count == 1 ? bp + dd * (m.Param * 0.5f) : pp;
                    Add(new Tele { shape = Shape.Bar, c = cc, dir = dd, len = m.Param, wid = m.Radius, warn = m.Warn, fireSfx = "sfx.boss.seonjang.rope.cut", rope = true, ropeEnd = cc + dd * (m.Param * 0.5f) });   // 판정이 나갈 때 줄 끊는 소리
                }
                break;
            case BossAct.RopeWrap: Add(new Tele { shape = Shape.Circle, c = pp, r = m.Radius, warn = m.Warn }); break;
            case BossAct.MatThrow: Add(new Tele { shape = Shape.Circle, c = pp, r = m.Radius, warn = m.Warn }); Sfx.Play("sfx.boss.wangcho.call"); break;
            case BossAct.StaffSwing: Add(new Tele { shape = Shape.Sector, c = bp, dir = dir, r = m.Radius, deg = m.Param, warn = m.Warn }); break;
            case BossAct.MirrorPull: Add(new Tele { shape = Shape.Bar, c = bp + dir * (m.Param * 0.5f), dir = dir, len = m.Param, wid = m.Radius, warn = m.Warn }); Sfx.Play("sfx.boss.heukwol.line.draw"); break;
            case BossAct.HisPahon: Add(new Tele { shape = Shape.Circle, c = pp, r = m.Radius, warn = m.Warn }); break;
            case BossAct.NameLines:   // 위(북)에서부터 한 줄씩, 마지막 줄은 비워 둔다(안전 지대)
                for (int i = 0; i < m.Count - 1; i++)
                    Add(new Tele { shape = Shape.Bar, c = new Vector3(def.X, 0f, def.Z + fightArea - 3f - i * (m.Radius + 1.5f)), dir = Vector3.right, len = fightArea * 2f, wid = m.Radius, warn = m.Warn + i * 0.5f, drain = true });   // 줄이 그어진 뒤에도 6초 남아 위에 서 있으면 넋·체력이 샌다
                Sfx.Play("sfx.boss.heukwol.line.draw"); break;
            case BossAct.Flood:       // 물살: 가로 띠가 무작위 자리에서 차례로
                for (int i = 0; i < m.Count; i++)
                    Add(new Tele { shape = Shape.Bar, c = new Vector3(def.X, 0f, def.Z + (Random.value - 0.5f) * fightArea * 1.6f), dir = Vector3.right, len = fightArea * 2f, wid = m.Radius, warn = m.Warn + i * 0.6f });
                if (helpers.Count < 2) SpawnHelper(4, ArenaPoint(0.5f));   // 큰물에 떠밀려 온 물 혼(천도하면 맺힘 -3%)
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
                if (t.fireSfx != null) Sfx.Play(t.fireSfx);
                if (t.rope && def.Id == 10) SpawnRopeEnd(t.ropeEnd);
                bool inside = Inside(t, judge.player.Pos);
                if (inside && t.paper) { brain.OnNamePaperStepped(); boss.soul.Maedhim = Mathf.Max(1, (int)brain.Maedhim); }   // 이름 종이: 무해, 보스 맺힘 −2%
                else if (inside) { judge.BossAreaHit(boss, t.weak ? 0.5f : 1f); if (t.mine) Sfx.Play("sfx.boss.yeom.burst"); }   // 숫자 칸을 밟아 피해   // 약해진 파도는 피해 절반
                if (t.view != null) t.view.GetComponent<Renderer>().sharedMaterial.color = new Color(1f, 0.55f, 0.25f, 1f);
            }
            else if (!t.fired && t.view != null)
                t.view.GetComponent<Renderer>().sharedMaterial.color = Color.Lerp(new Color(0.35f, 0.05f, 0.05f, 1f), new Color(0.85f, 0.12f, 0.1f, 1f), t.t / t.warn);
            // 명단 줄(B-12): 그어진 뒤 6초 동안 줄 위에 서 있으면 매초 넋 -2 · 피해 8
            if (t.drain && t.fired)
            {
                t.drainT += dt;
                if (t.drainT >= 1f) { t.drainT -= 1f; if (Inside(t, judge.player.Pos)) { Sfx.Play("sfx.boss.heukwol.line.drain"); judge.ledger.Neok = Mathf.Max(0, judge.ledger.Neok - 2); judge.BossAreaHit(boss, 8f / Mathf.Max(1, boss.damage)); } }
            }
            if (t.t >= (t.drain ? t.warn + 6f : t.warn < 19f ? t.warn + 0.25f : t.warn)) { if (t.view != null) Destroy(t.view); teles.RemoveAt(i); }
        }
    }
}
