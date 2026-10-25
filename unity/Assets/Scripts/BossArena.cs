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
    class Tele { public Vector3 c; float r; public float t, warn; public bool square, fired; public GameObject view; public float R { get { return r; } set { r = value; } } }
    readonly List<Tele> teles = new List<Tele>();
    GameObject[] cups;                         // 월화: 잔 12개 / 서 의원: 5×5 칸 바닥(흐린 선)
    GameObject weakMark;                       // 서 의원: 약점이 열리면 머리 위에 켜지는 청록 표시
    readonly WeakWindow weak = new WeakWindow();
    float waveT = 2f;                          // 다음 파동까지(전투 시작 직후 잠깐 여유)
    bool waveHit; Tele lastOfWave;             // 이번 파동에서 맞았나 / 파동의 마지막 칸(끝났는지 보려고)
    bool built;

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
        if (!fight) { ClearTeles(); boss.damageTakenMult = 1f; if (weakMark != null) weakMark.SetActive(false); return; }

        float dt = Time.deltaTime;
        TickTeles(dt);
        if (def.Id == 3) TickWeak(dt);
        waveT -= dt;
        if (waveT <= 0f && (def.Id != 3 || !weak.Open) && lastOfWave == null)   // 이전 파동이 끝나야 다음 파동
            StartWave();
    }

    void StartWave()
    {
        waveHit = false;
        if (def.Id == 2)
        {
            float ratio = boss.soul.MaedhimMax > 0f ? boss.soul.Maedhim / boss.soul.MaedhimMax : 1f;
            var pick = TwelveStreets.Pick(() => Random.value, TwelveStreets.CupsPerWave(ratio));
            foreach (int i in pick) Add(CupPos(i), Balance.B02_CUP_RADIUS_M, Balance.B02_WARN_TIME, false);
            Sfx.Play("cut.yoryeong.ring");   // 요령(방울) 한 번
            waveT = Balance.B02_WAVE_GAP + Balance.B02_WARN_TIME;
        }
        else
        {
            int n = Balance.B03_GRID;
            var bad = NumberGrid.Pick(() => Random.value, n * n, Balance.B03_CELLS_PER_WAVE);
            for (int k = 0; k < bad.Length; k++) if (bad[k]) Add(CellPos(k / n, k % n), Balance.B03_CELL_M * 0.5f, Balance.B03_WARN_TIME, true);
            Sfx.Play("cut.floor.flash");
            waveT = Balance.B03_WARN_TIME + Balance.B03_WAVE_GAP;
        }
        lastOfWave = teles[teles.Count - 1];
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

    void TickTeles(float dt)
    {
        for (int i = teles.Count - 1; i >= 0; i--)
        {
            var t = teles[i]; t.t += dt;
            if (!t.fired && t.t >= t.warn)
            {
                t.fired = true;
                var d = judge.player.Pos - t.c;
                bool inside = t.square ? (Mathf.Abs(d.x) < t.R + 0.3f && Mathf.Abs(d.z) < t.R + 0.3f) : (new Vector2(d.x, d.z).magnitude < t.R + 0.4f);
                if (inside) { if (judge.BossAreaHit(boss)) waveHit = true; }
                if (t.view != null) Tint(t.view, new Color(1f, 0.55f, 0.25f, 1f));   // 터지는 순간 밝게
            }
            else if (!t.fired && t.view != null)
                Tint(t.view, Color.Lerp(new Color(0.35f, 0.05f, 0.05f, 0.3f), new Color(0.85f, 0.12f, 0.1f, 1f), t.t / t.warn));   // 예고: 점점 붉어진다
            if (t.t >= t.warn + 0.25f)
            {
                if (t == lastOfWave) { lastOfWave = null; if (def.Id == 3) weak.WaveResolved(waveHit); }   // 파동 하나 끝
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
        boss.damageTakenMult = weak.DamageMult;
        if (decor != null && decor.WeakLamp != null) decor.WeakLamp.enabled = weak.Open;   // 약장 맨 아래 서랍의 청록 불
        if (weakMark != null) { weakMark.SetActive(weak.Open); weakMark.transform.position = boss.HeadPosition + Vector3.up * 0.6f; }
    }
}
