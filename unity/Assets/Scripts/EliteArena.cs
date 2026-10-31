// =============================================================================
// EliteArena.cs — 거센 혼(첫 강적)의 행동 (기획 combat/first-elite-and-dosul-cards.md)
// 패턴 셋을 4초 간격으로 번갈아 쓴다(첫 패턴은 늘 내려치기): 내려치기(원) · 덮치기(띠 + 붙잡힘) · 맺힘 50% 에서 한 번 부르기(잔넋 셋).
// 예고는 접근성 규칙: 밝은 테두리 + 안쪽에서 차오르는 붉은 채움. 맞으면 피해(BossAreaHit)로 넘긴다.
// 수치는 전부 Balance.ELITE_* (balance.json). 왜 따로 만드나: 보스 틀(Act2BossArena)은 두뇌(Core)·약점·고리가 얽혀 있어 가벼운 강적엔 무겁다.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class EliteArena : MonoBehaviour
{
    public static bool Met;   // 이번 판에 한 번이라도 만났나(첫 만남에만 예고 1.3배)

    class Tele { public bool bar; public Vector3 c, dir; public float r, len, wid, t, warn, mult; public bool fired, pounce, art; public GameObject border, back, fill; }

    JudgeSystem judge; Enemy e;
    readonly List<Tele> teles = new List<Tele>();
    readonly List<Enemy> motes = new List<Enemy>();
    float gapT = 1.5f, callT = -1f; int patternIdx; bool called, first = true, engaged;

    public static EliteArena Make(JudgeSystem j, Enemy elite)
    {
        var a = new GameObject("EliteArena").AddComponent<EliteArena>();
        a.judge = j; a.e = elite;
        j.OnJudged += a.OnJudged;
        return a;
    }

    void OnDestroy() { if (judge != null) judge.OnJudged -= OnJudged; ClearTeles(); }

    /// <summary>거센 혼이 처결되면 잔넋은 천도든 파혼이든 정리된다(파혼 보상은 JudgeSystem 이 계산)</summary>
    void OnJudged(Enemy who, bool tendo)
    {
        if (who != e && !tendo) { TryInterruptByPahon(who); return; }   // 다른 혼의 파혼 → 반격 규칙
        if (who != e) return;
        if (tendo) foreach (var m in motes) if (m != null && !m.gone) { m.Finish(); }   // 천도: 잔넋도 조용히 흩어진다(보상 없음)
    }

    /// <summary>
    /// 파혼 반격(개편안 P1-2, 오너 결정 5): 거센 혼이 기를 모으는 중에 곁의 처결 대기 혼을 파혼하면, 그 충격이 공격을 끊는다.
    /// 왜: 천도가 늘 정답이던 판에 '지금은 파혼이 맞다'는 순간을 만든다. 천도하면 기억을 얻지만 공격을 맞을 각오를 해야 한다.
    /// 폭발 반경·피해·업 대가는 그대로(3대 기둥 수치 변경 없음). 이미 터진 공격(fired)은 못 끊는다.
    /// </summary>
    void TryInterruptByPahon(Enemy who)
    {
        if (who == null || e == null || !e.alive || who.soul.Boss) return;
        bool charging = false; foreach (var t in teles) if (!t.fired) { charging = true; break; }
        float dist = new Vector2(who.Pos.x - e.Pos.x, who.Pos.z - e.Pos.z).magnitude;
        if (!CoreRules.PahonInterruptsCharge(charging, dist, judge.PahonRadiusOf(who), e.radius)) return;
        ClearTeles(); e.eliteAnim = ""; gapT = Balance.ELITE_PATTERN_GAP;   // 예고를 지우고 다음 패턴까지 평소 간격만큼 쉰다
        e.atk.Interrupt();
        judge.feel.AddShake(0.35f); Sfx.Play("cut.jing.crack");
        judge.Say("파혼의 충격이 거센 혼의 공격을 끊었다");
    }

    void Update()
    {
        if (judge == null || e == null) { Destroy(gameObject); return; }
        if (e.gone) { ClearTeles(); if (ring != null) Destroy(ring.gameObject); Destroy(gameObject, 0.1f); return; }
        TickRing();
        { string an = ""; foreach (var tl in teles) if (!tl.fired) { an = tl.pounce ? "strike" : "attack"; break; } e.eliteAnim = an; }
        float dist = new Vector2(judge.player.Pos.x - e.Pos.x, judge.player.Pos.z - e.Pos.z).magnitude;
        bool fight = e.alive && dist < 30f && !judge.cuts.Active && !judge.NightOver && !CharacterPanel.Open && !SettingsPanel.Open;
        if (!fight) { if (!e.alive) ClearTeles(); return; }
        if (!engaged) { engaged = true; Met = true; Sfx.Play("sfx.elite.appear"); }
        float dt = Time.deltaTime;
        motes.RemoveAll(m => m == null || m.gone);
        TickTeles(dt);
        // 부르기: 맺힘 50% 에서 한 번(0.8초 울부짖음 뒤 잔넋 셋)
        if (!called && e.soul.Maedhim <= e.soul.MaedhimMax * Balance.ELITE_CALL_AT) { called = true; callT = 0.8f; Sfx.Play("sfx.elite.call"); judge.feel.AddShake(0.25f); judge.Say("거센 혼이 울부짖는다"); }
        if (callT >= 0f) { callT -= dt; if (callT < 0f) CallMotes(); }
        if (teles.Count > 0 || callT >= 0f) return;
        gapT -= dt;
        if (gapT > 0f) return;
        gapT = Balance.ELITE_PATTERN_GAP;
        if (patternIdx++ % 2 == 0) Slam(); else Pounce();
    }

    // 머리 위 붉은 가시 고리(눕혀 놓은 그림 4프레임 8fps): 한눈에 '센 놈'
    SpriteRenderer ring; Sprite[] ringFrames;
    void TickRing()
    {
        if (ringFrames == null) ringFrames = First10.Strip("elite_ring", 4, 128f);
        if (ringFrames == null) return;
        if (ring == null) { var g = new GameObject("EliteRing"); ring = g.AddComponent<SpriteRenderer>(); ring.sortingOrder = 45; }
        ring.gameObject.SetActive(e.alive || e.kneeling);
        ring.sprite = ringFrames[(int)(Time.time * 8f) % ringFrames.Length];
        ring.transform.position = e.HeadPosition + Vector3.up * 0.3f;
        ring.transform.rotation = Quaternion.LookRotation(Vector3.down, Vector3.forward);
    }

    float Warn(float basic) { float w = first ? basic * 1.3f : basic; first = false; return w; }   // 첫 패턴(첫 만남)만 예고 1.3배
    Vector3 Flat(Vector3 p) { return new Vector3(p.x, 0.03f + GroundTerrain.HeightAt(p.x, p.z), p.z); }

    void Slam()
    {
        var t = new Tele { c = new Vector3(e.Pos.x, 0f, e.Pos.z), r = Balance.ELITE_SLAM_R, warn = Warn(Balance.ELITE_SLAM_TELE), mult = 1f };
        e.atk.Interrupt(); Show(t); teles.Add(t); Sfx.Play("sfx.elite.slam.telegraph");
    }

    void Pounce()
    {
        var d = new Vector3(judge.player.Pos.x - e.Pos.x, 0f, judge.player.Pos.z - e.Pos.z);
        var dir = d.sqrMagnitude > 0.01f ? d.normalized : Vector3.forward;
        var from = new Vector3(e.Pos.x, 0f, e.Pos.z);
        var t = new Tele { bar = true, c = from + dir * (Balance.ELITE_POUNCE_LEN * 0.5f), dir = dir, len = Balance.ELITE_POUNCE_LEN, wid = Balance.ELITE_POUNCE_W, warn = Warn(Balance.ELITE_POUNCE_TELE), mult = (float)Balance.ELITE_POUNCE_DMG / Mathf.Max(1, Balance.ELITE_SLAM_DMG), pounce = true };
        Show(t); teles.Add(t); Sfx.Play("sfx.elite.pounce.telegraph");
    }

    void CallMotes()
    {
        for (int i = 0; i < Balance.ELITE_MOTES; i++)
        {
            var at = e.Pos + Quaternion.Euler(0f, 360f / Balance.ELITE_MOTES * i + 30f, 0f) * Vector3.forward * 3.2f;   // 주변 4m 안
            var m = judge.enemies.SpawnEliteMote(at); motes.Add(m); Sfx.Play("sfx.mote.spawn");
        }
        judge.Say("잔넋이 몰려온다");
    }

    // ---- 예고 그림: 밝은 테두리 + 어두운 바탕 + 안쪽에서 차오르는 붉은 채움 ----
    GameObject Disc(Vector3 at, float r, Color c, float lift)
    {
        var g = GameObject.CreatePrimitive(PrimitiveType.Cylinder); Destroy(g.GetComponent<Collider>());
        g.transform.localScale = new Vector3(r * 2f, 0.02f, r * 2f); g.transform.position = Flat(at) + Vector3.up * lift;
        g.GetComponent<Renderer>().sharedMaterial = U.Unlit(c); return g;
    }
    GameObject Slab(Vector3 at, Vector3 dir, float len, float wid, Color c, float lift)
    {
        var g = GameObject.CreatePrimitive(PrimitiveType.Cube); Destroy(g.GetComponent<Collider>());
        g.transform.localScale = new Vector3(wid, 0.02f, len); g.transform.rotation = Quaternion.LookRotation(dir, Vector3.up); g.transform.position = Flat(at) + Vector3.up * lift;
        g.GetComponent<Renderer>().sharedMaterial = U.Unlit(c); return g;
    }
    static readonly Color Edge = new Color(1f, 0.93f, 0.72f, 1f), Back = new Color(0.26f, 0.03f, 0.04f, 1f), Fill = new Color(0.9f, 0.14f, 0.1f, 1f);
    // 아트 장판(그림이 있으면): 테두리는 늘 보이고, 채움은 가운데서(원)·시작에서(띠) 차오른다. 접근성: 밝은 테두리 + 35% 채움
    GameObject Flat(string name, Vector3 at, Vector3 dir, float ppu, int order)
    {
        var sp = First10.Whole(name, ppu); var g = new GameObject("EliteTele_" + name);
        var sr = g.AddComponent<SpriteRenderer>(); sr.sprite = sp; sr.sortingOrder = order;
        g.transform.position = Flat(at) + Vector3.up * 0.04f; g.transform.rotation = Quaternion.LookRotation(Vector3.down, dir);   // 땅에 눕히고 그림의 위쪽이 dir 을 향하게
        return g;
    }
    void Show(Tele t)
    {
        if (First10.Tex(t.bar ? "tele_band_border" : "tele_circle_border") != null)
        {
            var dir = t.bar ? t.dir : Vector3.forward;
            if (t.bar) { t.border = Flat("tele_band_border", t.c, dir, 256f / Balance.ELITE_POUNCE_W, 30); t.fill = Flat("tele_band_fill_red", t.c, dir, 256f / Balance.ELITE_POUNCE_W, 31); }
            else { t.border = Flat("tele_circle_border", t.c, dir, 512f / (t.r * 2f), 30); t.fill = Flat("tele_circle_fill_red", t.c, dir, 512f / (t.r * 2f), 31); }
            t.art = true; t.fill.transform.localScale = new Vector3(1f, 0.01f, 1f);
            return;
        }
        if (t.bar)
        {
            t.border = Slab(t.c, t.dir, t.len, t.wid, Edge, 0f);
            t.back = Slab(t.c, t.dir, t.len - 0.2f, t.wid - 0.2f, Back, 0.01f);
            t.fill = Slab(t.c - t.dir * (t.len * 0.5f), t.dir, 0.01f, t.wid - 0.3f, Fill, 0.02f);   // 시작에서 끝으로 차오른다
        }
        else
        {
            t.border = Disc(t.c, t.r, Edge, 0f); t.back = Disc(t.c, t.r - 0.12f, Back, 0.01f); t.fill = Disc(t.c, 0.05f, Fill, 0.02f);
        }
    }
    void Grow(Tele t)
    {
        float k = Mathf.Clamp01(t.t / t.warn);
        if (t.art)
        {
            if (t.bar)
            {
                t.fill.transform.localScale = new Vector3(1f, Mathf.Max(0.01f, k), 1f);
                t.fill.transform.position = Flat(t.c - t.dir * (t.len * 0.5f) + t.dir * (t.len * k * 0.5f)) + Vector3.up * 0.045f;   // 시작에서 끝으로 차오른다
            }
            else t.fill.transform.localScale = new Vector3(Mathf.Max(0.01f, k), Mathf.Max(0.01f, k), 1f);   // 가운데서 퍼진다
            return;
        }
        if (t.bar)
        {
            float l = Mathf.Max(0.01f, (t.len - 0.2f) * k);
            t.fill.transform.localScale = new Vector3(t.wid - 0.3f, 0.02f, l);
            t.fill.transform.position = Flat(t.c - t.dir * (t.len * 0.5f - 0.1f - l * 0.5f)) + Vector3.up * 0.02f;
        }
        else { float r = Mathf.Max(0.05f, (t.r - 0.12f) * k); t.fill.transform.localScale = new Vector3(r * 2f, 0.02f, r * 2f); }
    }

    bool Inside(Tele t, Vector3 p)
    {
        var d = new Vector3(p.x - t.c.x, 0f, p.z - t.c.z);
        if (!t.bar) return d.magnitude < t.r + 0.4f;
        float along = Vector3.Dot(d, t.dir), across = Vector3.Dot(d, Vector3.Cross(Vector3.up, t.dir));
        return Mathf.Abs(across) <= t.wid * 0.5f + 0.3f && Mathf.Abs(along) <= t.len * 0.5f;
    }

    void TickTeles(float dt)
    {
        for (int i = teles.Count - 1; i >= 0; i--)
        {
            var t = teles[i]; t.t += dt;
            if (!t.fired)
            {
                Grow(t);
                if (t.t >= t.warn)
                {
                    t.fired = true;
                    if (t.pounce) e.Pos = new Vector3(t.c.x + t.dir.x * t.len * 0.5f, e.Pos.y, t.c.z + t.dir.z * t.len * 0.5f) - t.dir * 1.2f;   // 덮치기: 띠 끝까지 달려든다
                    judge.feel.AddShake(0.3f); Sfx.Play(t.pounce ? "sfx.elite.pounce" : "sfx.elite.slam");
                    if (Inside(t, judge.player.Pos) && judge.BossAreaHit(e, t.mult) && t.pounce) judge.player.actLock = Mathf.Max(judge.player.actLock, Balance.ELITE_POUNCE_HOLD);   // 맞으면 1초 붙잡힘
                    if (!t.art) t.fill.GetComponent<Renderer>().sharedMaterial.color = new Color(1f, 0.55f, 0.25f, 1f);
                }
            }
            if (t.t >= t.warn + 0.25f) { Kill(t); teles.RemoveAt(i); }
        }
    }

    static void Kill(Tele t) { if (t.border != null) Destroy(t.border); if (t.back != null) Destroy(t.back); if (t.fill != null) Destroy(t.fill); }
    void ClearTeles() { foreach (var t in teles) Kill(t); teles.Clear(); }
}
