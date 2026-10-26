// =============================================================================
// BossArena.cs — 2호 월화·3호 서 의원의 '바닥 무늬' 전투. 1호(나루 영감)는 몸으로 싸우고, 2·3호는 바닥을 붉게 물들인다.
//   월화 '열두 거리': 굿판 가장자리 잔 12개 중 몇 개 앞 바닥이 1초 예고 뒤 열린다. 엎어진 열두째 잔 자리는 늘 안전. 맺힘 50% 이하면 더 많이.
//   서 의원 '번호 부르기': 5×5 칸 중 16칸이 0.8초 예고 뒤 터진다. 파동을 3번 연달아 피하면 약장 서랍이 열려 3초간 제대로 아프다.
// 어느 칸이 터지나·약점이 열렸나는 Core/Boss.cs 가 정한다. 여기서는 그리고, 맞았는지 재고, 피해를 JudgeSystem 에 넘기기만 한다.
// 모양은 색 도형(에셋 없음). 자리·시간 수치는 모두 balance.json.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class BossArena : MonoBehaviour
{
    JudgeSystem judge; Enemy boss; BossDef def;
    class Tele { public Vector3 c; float r; public float t, warn; public bool square, fired, sector; public float ang;   // sector: 월화 부채꼴(ang=굿판 중심에서 잔 방향, 라디안)
        public GameObject view; public float R { get { return r; } set { r = value; } } }
    readonly List<Tele> teles = new List<Tele>();
    GameObject[] cups;                         // 월화: 잔 12개 / 서 의원: 5×5 칸 바닥(흐린 선)
    GameObject weakMark;                       // 서 의원: 약점이 열리면 머리 위에 켜지는 청록 표시
    readonly WeakWindow weak = new WeakWindow();
    float waveT = 2f;                          // 다음 파동까지(전투 시작 직후 잠깐 여유)
    bool waveBurstSnd, frenzySnd; int seoStreak;   // 파동마다 터짐 소리 1번 / 월화 몰아침 소리 1번 / 서 의원 연속 피함
    bool waveHit; Tele lastOfWave;             // 이번 파동에서 맞았나 / 파동의 마지막 칸(끝났는지 보려고)
    bool built, wasKneel;   // wasKneel: 꿇은 압박 타이머를 한 번만 맞추려고

    ArenaDecor decor;
    public void Init(JudgeSystem j, Enemy b, BossDef d) { judge = j; boss = b; def = d; decor = ArenaDecor.Make(j, b, d.Id); }

    static GameObject Flat(PrimitiveType t, Color col, Vector3 pos, Vector3 scale)
    {
        var g = GameObject.CreatePrimitive(t);
        Destroy(g.GetComponent<Collider>());
        g.GetComponent<Renderer>().sharedMaterial = U.Unlit(col);
        g.transform.position = pos; g.transform.localScale = scale;
        return g;
    }

    Vector3 CupPos(int i)
    {
        float a = i * Mathf.PI * 2f / Balance.B02_CUPS;
        float x = def.X + Mathf.Cos(a) * Balance.B02_RING_RADIUS_M, z = def.Z + Mathf.Sin(a) * Balance.B02_RING_RADIUS_M;
        return new Vector3(x, 0.03f + GroundTerrain.HeightAt(x, z), z);   // 새 땅이 있으면 땅 높이 위에 깐다(비탈이 가파르면 한쪽이 묻힐 수 있어 보스 터는 평평하게 부탁)
    }
    Vector3 CellPos(int i, int j)
    {
        int n = Balance.B03_GRID; float m = Balance.B03_CELL_M;
        float x = def.X + (i - (n - 1) * 0.5f) * m, z = def.Z + (j - (n - 1) * 0.5f) * m;
        return new Vector3(x, 0.03f + GroundTerrain.HeightAt(x, z), z);
    }

    void Build()
    {
        built = true;
        // 잔·칸 그림은 ArenaDecor(아트 소품·바닥 무늬)가 맡는다. 여기서는 서 의원 약점 표시만 만든다
        if (def.Id == 3)
        {
            weakMark = Flat(PrimitiveType.Sphere, new Color(0.25f, 0.9f, 0.85f), Vector3.zero, Vector3.one * 0.5f);
            weakMark.SetActive(false);
        }
    }

    void SetCupsActive(bool on) { if (cups != null) foreach (var c in cups) if (c != null) c.SetActive(on); }

    void ClearTeles() { foreach (var t in teles) if (t.view != null) Destroy(t.view); teles.Clear(); lastOfWave = null; }

    void Update()
    {
        if (judge == null || boss == null || def == null) return;
        // 보스가 처결되어 사라지면 바닥도 거둔다
        if (boss.soul.State == SoulState.Gone) { ClearTeles(); SetCupsActive(false); if (weakMark != null) weakMark.SetActive(false); return; }
        float dist = new Vector2(judge.player.Pos.x - def.X, judge.player.Pos.z - def.Z).magnitude;
        if (!built && dist < 60f) Build();
        if (!built) return;
        SetCupsActive(dist < 60f);
        bool fight = dist < 16f && boss.alive && !judge.cuts.Active && !judge.NightOver && !CharacterPanel.Open && !SettingsPanel.Open;
        // 꿇은 동안의 압박(기획 boss-final-moment-act1-2): 서 의원은 꿇어도 4초마다 12칸 파동을 보낸다
        // 왜: 압박이 없으면 천도(1.5초 시전)가 늘 안전해 파혼 쪽으로 쏠리지 않고 천도로 쏠린다. 시전 중에도 계속 돈다
        bool kneelFight = def.Id == 3 && (boss.kneeling || boss.sending) && dist < 16f && !judge.cuts.Active && !judge.NightOver && !CharacterPanel.Open && !SettingsPanel.Open;
        if (kneelFight)
        {
            if (!wasKneel) { wasKneel = true; waveT = Balance.B03_KNEEL_WAVE_GAP; }   // 꿇는 순간 첫 파동까지 4초
            boss.damageTakenMult = 1f; if (weakMark != null) weakMark.SetActive(false);
            TickTeles(Time.deltaTime);
            waveT -= Time.deltaTime;
            if (waveT <= 0f && lastOfWave == null) StartWave(true);
            return;
        }
        wasKneel = false;
        if (!fight) { ClearTeles(); boss.damageTakenMult = 1f; if (weakMark != null) weakMark.SetActive(false); return; }

        float dt = Time.deltaTime;
        TickTeles(dt);
        if (def.Id == 3) TickWeak(dt);
        waveT -= dt;
        if (waveT <= 0f && (def.Id != 3 || !weak.Open) && lastOfWave == null)   // 이전 파동이 끝나야 다음 파동
            StartWave();
    }

    void StartWave(bool kneel = false)
    {
        waveHit = false; waveBurstSnd = false;
        if (def.Id == 2)
        {
            float ratio = boss.soul.MaedhimMax > 0f ? boss.soul.Maedhim / boss.soul.MaedhimMax : 1f;
            if (!frenzySnd && ratio <= 0.5f) { frenzySnd = true; Sfx.Play("sfx.boss.wolhwa.frenzy"); }   // 맺힘이 처음 절반 아래로
            var pick = TwelveStreets.Pick(() => Random.value, TwelveStreets.CupsPerWave(ratio));
            // 월화 '열두 거리': 굿판 한가운데에서 그 잔 쪽으로 30° 부채꼴이 열린다(잔 방향 = 30i°, 아트 예고 그림과 같은 모양)
            foreach (int i in pick) AddSector(i * Mathf.PI * 2f / Balance.B02_CUPS, Balance.B02_WARN_TIME);
            Sfx.Play("sfx.boss.wolhwa.warn");   // 월화 예고음(컷신용 요령 소리 대신 전투용)
            waveT = Balance.B02_WAVE_GAP + Balance.B02_WARN_TIME;
        }
        else
        {
            int n = Balance.B03_GRID;
            var bad = NumberGrid.Pick(() => Random.value, n * n, kneel ? Balance.B03_KNEEL_CELLS : Balance.B03_CELLS_PER_WAVE);   // 꿇은 동안은 12칸(평소 16)
            for (int k = 0; k < bad.Length; k++) if (bad[k]) Add(CellPos(k / n, k % n), Balance.B03_CELL_M * 0.5f, Balance.B03_WARN_TIME, true);
            Sfx.Play("cut.floor.flash");
            waveT = kneel ? Balance.B03_KNEEL_WAVE_GAP : Balance.B03_WARN_TIME + Balance.B03_WAVE_GAP;
        }
        lastOfWave = teles[teles.Count - 1];
    }

    void AddSector(float ang, float warn)
    {
        float R = Balance.B02_SECTOR_R_M;
        var c = new Vector3(def.X, 0.03f + GroundTerrain.HeightAt(def.X, def.Z), def.Z);
        var t = new Tele { c = c, t = 0f, warn = warn, sector = true, ang = ang }; t.R = R;
        var tex = SpriteLib.Texture("boss/tele_sector30");
        if (tex != null)
        {
            var g = new GameObject("Tele"); g.transform.position = c + Vector3.up * 0.03f;
            // 그림은 꼭짓점이 한가운데, 오른쪽(+x)으로 펼쳐진다. 눕힌 뒤 위에서 볼 때 ang 만큼 돌린다(유니티 y축은 반대 방향이라 음수)
            g.transform.rotation = Quaternion.Euler(0f, -ang * Mathf.Rad2Deg, 0f) * Quaternion.Euler(90f, 0f, 0f);
            var sr = g.AddComponent<SpriteRenderer>();
            sr.sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width / (R * 2f));   // 그림 반폭 = 반지름
            sr.color = new Color(0.35f, 0.05f, 0.05f, 0.3f); sr.sortingOrder = -4;
            t.view = g;
        }
        teles.Add(t);
    }

    void Add(Vector3 c, float r, float warn, bool square)
    {
        var t = new Tele { c = c, t = 0f, warn = warn, square = square };
        t.R = r;
        t.view = TeleView(c, r, square);
        teles.Add(t);
    }

    // 예고 장판: 아트의 흰색+알파 그림(칸=tele_cell, 원=tele_circle)을 눕히고 색은 코드가 입힌다. 판정 크기와 그림 크기가 같다
    static GameObject TeleView(Vector3 c, float r, bool square)
    {
        var tex = SpriteLib.Texture("boss/" + (square ? "tele_cell" : "tele_circle"));
        if (tex == null) return Flat(square ? PrimitiveType.Cube : PrimitiveType.Cylinder, new Color(0.55f, 0.08f, 0.08f), c, new Vector3(r * 2f, 0.03f, r * 2f));
        var g = new GameObject("Tele"); g.transform.position = c + Vector3.up * 0.03f; g.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
        var sr = g.AddComponent<SpriteRenderer>();
        sr.sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width / (r * 2f));   // 그림 전체 폭 = 판정 지름
        sr.color = new Color(0.35f, 0.05f, 0.05f, 0.3f); sr.sortingOrder = -4;
        return g;
    }
    static void Tint(GameObject g, Color col)
    {
        var sr = g.GetComponent<SpriteRenderer>();
        if (sr != null) sr.color = col; else g.GetComponent<Renderer>().sharedMaterial.color = col;
    }

    // 부채꼴 판정: 굿판 중심에서 거리 < 반지름이고, 방향 차이가 부채꼴 반각(15°) 이내. 중심 바로 곁은 방향이 불안정해 늘 맞는 걸로 본다
    static bool InSector(Vector3 d, Tele t)
    {
        float dist = new Vector2(d.x, d.z).magnitude;
        if (dist > t.R + 0.4f) return false;
        if (dist < 0.5f) return true;
        float diff = Mathf.Abs(Mathf.DeltaAngle(Mathf.Atan2(d.z, d.x) * Mathf.Rad2Deg, t.ang * Mathf.Rad2Deg));
        return diff <= Balance.B02_SECTOR_DEG * 0.5f + 2f;   // +2°: 경계에 걸친 몸 크기
    }

    void TickTeles(float dt)
    {
        for (int i = teles.Count - 1; i >= 0; i--)
        {
            var t = teles[i]; t.t += dt;
            if (!t.fired && t.t >= t.warn)
            {
                t.fired = true;
                if (!waveBurstSnd) { waveBurstSnd = true; Sfx.Play(def.Id == 2 ? "sfx.boss.wolhwa.burst" : "sfx.boss.seo.burst"); }   // 파동마다 한 번
                var d = judge.player.Pos - t.c;
                bool inside = t.sector ? InSector(d, t) : t.square ? (Mathf.Abs(d.x) < t.R + 0.3f && Mathf.Abs(d.z) < t.R + 0.3f) : (new Vector2(d.x, d.z).magnitude < t.R + 0.4f);
                if (inside) { if (judge.BossAreaHit(boss)) waveHit = true; }
                if (t.view != null) Tint(t.view, new Color(1f, 0.55f, 0.25f, 1f));   // 터지는 순간 밝게
            }
            else if (!t.fired && t.view != null)
                Tint(t.view, Color.Lerp(new Color(0.35f, 0.05f, 0.05f, 0.3f), new Color(0.85f, 0.12f, 0.1f, 1f), t.t / t.warn));   // 예고: 점점 붉어진다
            if (t.t >= t.warn + 0.25f)
            {
                if (t == lastOfWave) { lastOfWave = null; if (def.Id == 3) { weak.WaveResolved(waveHit); seoStreak = waveHit ? 0 : seoStreak + 1; if (seoStreak == 1 || seoStreak == 2) Sfx.Play("sfx.boss.seo.streak"); } }   // 3번째 피함은 약장 서랍 소리가 맡는다   // 파동 하나 끝
                if (t.view != null) Destroy(t.view);
                teles.RemoveAt(i);
            }
        }
    }

    void TickWeak(float dt)
    {
        bool wasOpen = weak.Open;
        weak.Tick(dt);
        if (!wasOpen && weak.Open) Sfx.Play("cut.drawer");   // 약장 서랍이 밀려 나온다
        if (wasOpen && !weak.Open) Sfx.Play("sfx.boss.seo.weak.close");   // 약점 3초가 끝났다
        boss.damageTakenMult = weak.DamageMult;
        if (decor != null && decor.WeakLamp != null) decor.WeakLamp.enabled = weak.Open;   // 약장 맨 아래 서랍의 청록 불
        if (weakMark != null) { weakMark.SetActive(weak.Open); weakMark.transform.position = boss.HeadPosition + Vector3.up * 0.6f; }
    }
}
