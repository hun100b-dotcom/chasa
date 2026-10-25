// =============================================================================
// RewardFx.cs — 처결 보상이 '몸으로 들어오는' 연출 (기획 first-10min M3)
//  천도: 혼불 1~3개가 떠올랐다가 곡선으로 날아와 가슴에 흡수된다.
//  파혼: 엽전 3~5닢이 튀어 올랐다가 바닥에 떨어지고, 잠시 뒤 발밑으로 빨려 든다.
//  왜 이렇게: 보상이 글자 알림뿐이면 "얻었다"는 느낌이 약하다. 눈에 보이는 물건이 몸으로 들어와야 한다.
//  두 쪽의 총 길이(0.85초)와 알갱이 크기를 똑같이 맞춘다 — 어느 쪽이 정답처럼 보이면 안 된다(처결 필터).
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class RewardFx : MonoBehaviour
{
    const float TOTAL = 0.85f;      // 천도·파혼 공통 총 길이(초)
    const float SIZE = 0.3f;        // 알갱이 크기(m) — 두 쪽 같게

    class P
    {
        public Transform tr; public SpriteRenderer sr;
        public Vector3 start, apex;      // 시작 / (천도) 떠오르는 자리 · (파혼) 떨어지는 자리
        public float age, delay; public bool coin; public float spin; public bool first, burst; public Sprite[] frames; public float fps;
    }
    readonly List<P> list = new List<P>();
    Sprite dot;
    public System.Func<Vector3> Target;   // 흡수될 자리(플레이어 위치)

    Sprite Dot()
    {
        if (dot != null) return dot;
        const int n = 32; var tex = new Texture2D(n, n, TextureFormat.RGBA32, false); tex.filterMode = FilterMode.Bilinear;
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(n / 2f, n / 2f)) / (n / 2f);
            tex.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01((1f - d) * 3f)));   // 가장자리가 부드러운 동그라미
        }
        tex.Apply();
        dot = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);   // 1유닛 = 32픽셀 → 지름 1m
        return dot;
    }

    /// <summary>천도 보상: 혼불 1~3개. amount 가 클수록 개수가 많다</summary>
    public void Tendo(Vector3 at, int count)
    {
        first = true;
        for (int i = 0; i < Mathf.Clamp(count, 1, 3); i++)
            Add(at + Vector3.up * 0.8f, at + new Vector3(Random.Range(-0.7f, 0.7f), 1.9f + 0.3f * i, Random.Range(-0.7f, 0.7f)), false, i * 0.06f);
    }

    /// <summary>파혼 보상: 엽전 3~5닢</summary>
    public void Pahon(Vector3 at, int count)
    {
        first = true;
        for (int i = 0; i < Mathf.Clamp(count, 3, 5); i++)
            Add(at + Vector3.up * 0.8f, at + new Vector3(Random.Range(-1.4f, 1.4f), 0.1f, Random.Range(-1.4f, 1.4f)), true, i * 0.04f);
    }

    void Add(Vector3 start, Vector3 apex, bool coin, float delay)
    {
        var go = new GameObject(coin ? "RewardCoin" : "RewardMote"); go.transform.SetParent(transform, false);
        var sr = go.AddComponent<SpriteRenderer>();
        var art = First10.Strip(coin ? "absorb_coin_spin" : "absorb_hon_fly", coin ? 6 : 4, 48f / SIZE);   // 아트 그림(48px = 0.3m). 없으면 색 동그라미
        if (art != null) { sr.sprite = art[0]; sr.color = Color.white; go.transform.localScale = Vector3.one; }
        else
        {
            sr.sprite = Dot();
            sr.color = coin ? new Color(1f, 0.72f, 0.28f, 1f) : new Color(0.45f, 0.95f, 0.9f, 1f);   // 엽전 주황 / 혼불 청록(기획 값)
            go.transform.localScale = Vector3.one * SIZE;
        }
        sr.sortingOrder = 50; go.transform.position = start;
        list.Add(new P { tr = go.transform, sr = sr, start = start, apex = apex, coin = coin, delay = delay, frames = art, fps = 12f, first = first });
        first = false;
    }
    bool first;

    /// <summary>흡수되는 순간의 번쩍임(혼불은 가슴에 불티가 모이고, 엽전은 발밑에 파편이 튄다). 128px 6프레임 0.3초</summary>
    void Burst(Vector3 at, bool coin)
    {
        var art = First10.Strip(coin ? "absorb_coin_burst" : "absorb_hon_burst", 6, 128f / 0.9f); if (art == null) return;
        var go = new GameObject("RewardBurst"); go.transform.SetParent(transform, false);
        var sr = go.AddComponent<SpriteRenderer>(); sr.sprite = art[0]; sr.sortingOrder = 51; go.transform.position = at;
        list.Add(new P { tr = go.transform, sr = sr, burst = true, frames = art, fps = 20f });
    }

    void Update()
    {
        var cam = Camera.main; var tgt = Target != null ? Target() : Vector3.zero;
        for (int i = list.Count - 1; i >= 0; i--)
        {
            var p = list[i]; p.age += Time.deltaTime;
            float t = p.age - p.delay;
            if (t < 0f) { p.sr.enabled = false; continue; }
            p.sr.enabled = true;
            if (p.burst)   // 번쩍임: 제자리에서 프레임만 넘기고 끝나면 사라진다
            {
                int bf = (int)(t * p.fps);
                if (bf >= p.frames.Length) { Destroy(p.tr.gameObject); list.RemoveAt(i); continue; }
                p.sr.sprite = p.frames[bf]; if (cam != null) p.tr.rotation = cam.transform.rotation; continue;
            }
            if (t >= TOTAL)
            {
                if (p.first) Burst(p.coin ? tgt + Vector3.up * 0.15f : tgt + Vector3.up * 1.2f, p.coin);   // 한 무리에 한 번
                Destroy(p.tr.gameObject); list.RemoveAt(i); continue;
            }
            if (p.frames != null) p.sr.sprite = p.frames[(int)(t * p.fps) % p.frames.Length];   // 깜빡·도는 프레임
            Vector3 pos;
            if (p.coin)
            {
                if (t < 0.6f)   // 튀어 올랐다가 떨어진다(포물선)
                {
                    float u = t / 0.6f;
                    pos = Vector3.Lerp(p.start, p.apex, u); pos.y = Mathf.Lerp(p.start.y, p.apex.y, u) + 1.4f * 4f * u * (1f - u);
                }
                else { float u = (t - 0.6f) / (TOTAL - 0.6f); pos = Vector3.Lerp(p.apex, tgt + Vector3.up * 0.1f, u * u); }   // 발밑으로 빨려 든다
            }
            else
            {
                if (t < 0.35f) pos = Vector3.Lerp(p.start, p.apex, 1f - (1f - t / 0.35f) * (1f - t / 0.35f));   // 떠오른다
                else
                {
                    float u = (t - 0.35f) / (TOTAL - 0.35f); var chest = tgt + Vector3.up * 1.2f;
                    var mid = (p.apex + chest) * 0.5f + Vector3.up * 0.6f;   // 곡선: 위로 부푼 중간점
                    pos = Vector3.Lerp(Vector3.Lerp(p.apex, mid, u), Vector3.Lerp(mid, chest, u), u);
                }
            }
            p.tr.position = pos;
            if (cam != null) p.tr.rotation = cam.transform.rotation;   // 늘 화면을 본다
            float fade = Mathf.Clamp01((TOTAL - t) / 0.12f);
            var c = p.sr.color; c.a = fade; p.sr.color = c;
        }
    }
}
