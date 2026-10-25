// =============================================================================
// LootDrop.cs — 바닥에 떨어진 장비 (기획 first-10min M4)
//  예전엔 드롭이 바로 몸에 끼워져 "글자 알림"뿐이었다. 이제 물건이 바닥에 떨어지고,
//  등급 색 빛줄기(흔한 미색 1.5m · 손본 청록 2.5m · 귀한 금빛 4m)와 이름표가 서며,
//  2m 안에 들어가면 자동으로 줍는다. 오래 두면(120초) 놓치지 않게 자동으로 주워 준다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class LootDrop : MonoBehaviour
{
    class Drop { public ItemDef item; public Vector3 pos; public float age; public Transform beam, orb; public SpriteRenderer beamSr, orbSr; public string label; public Color col; public string tier; public GameObject pillar; }
    readonly List<Drop> drops = new List<Drop>();
    Sprite dot;
    public System.Func<Vector3> PlayerPos;
    public System.Action<ItemDef, Vector3> OnPick;   // 줍는 순간(장착 판정은 게임 쪽이 한다)
    public const float PickRadius = 2f, MaxAge = 120f;

    Sprite Dot()
    {
        if (dot != null) return dot;
        const int n = 32; var tex = new Texture2D(n, n, TextureFormat.RGBA32, false); tex.filterMode = FilterMode.Bilinear;
        for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
        {
            float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(n / 2f, n / 2f)) / (n / 2f);
            tex.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01((1f - d) * 3f)));
        }
        tex.Apply();
        dot = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);
        return dot;
    }

    public static Color RarityColor(ItemDef it) { return it.Named || it.Rarity == Rarity.Rare ? new Color(1f, 0.82f, 0.35f) : it.Rarity == Rarity.Crafted ? new Color(0.4f, 0.9f, 0.85f) : new Color(0.9f, 0.88f, 0.78f); }
    static float BeamHeight(ItemDef it) { return it.Named || it.Rarity == Rarity.Rare ? 4f : it.Rarity == Rarity.Crafted ? 2.5f : 1.5f; }

    /// <summary>등급 → 아트 이름(흔한 common · 손본 refined · 귀한 rare · 이름 있는 named. 옛 차사 antique 는 장비 등급이 생기면)</summary>
    public static string TierOf(ItemDef it) { return it.Named ? "named" : it.Rarity == Rarity.Rare ? "rare" : it.Rarity == Rarity.Crafted ? "refined" : "common"; }

    public int Count { get { return drops.Count; } }

    public void Add(ItemDef it, Vector3 at, string label)
    {
        var d = new Drop { item = it, pos = new Vector3(at.x, at.y, at.z), label = label, col = RarityColor(it) };
        d.tier = TierOf(it);
        float h = BeamHeight(it);
        var prefab = Resources.Load<GameObject>("Models/Fx/fx_drop_" + d.tier);   // 아트의 3D 빛줄기(등급마다 꼭대기 모양이 다르다)
        if (prefab != null) { d.pillar = Instantiate(prefab, d.pos, Quaternion.identity, transform); }
        var beam = new GameObject("LootBeam"); beam.transform.SetParent(transform, false); beam.SetActive(d.pillar == null);
        d.beamSr = beam.AddComponent<SpriteRenderer>(); d.beamSr.sprite = Dot(); d.beamSr.sortingOrder = 40;
        d.beamSr.color = new Color(d.col.r, d.col.g, d.col.b, 0.55f);
        beam.transform.localScale = new Vector3(0.35f, h, 1f); d.beam = beam.transform;   // 가늘고 긴 빛줄기(1유닛=1m 동그라미를 늘임)
        var orb = new GameObject("LootOrb"); orb.transform.SetParent(transform, false);
        d.orbSr = orb.AddComponent<SpriteRenderer>(); d.orbSr.sprite = Dot(); d.orbSr.sortingOrder = 41; d.orbSr.color = d.col;
        orb.transform.localScale = Vector3.one * 0.5f; d.orb = orb.transform; orb.SetActive(d.pillar == null);
        drops.Add(d);
    }

    void Update()
    {
        var cam = Camera.main; var pp = PlayerPos != null ? PlayerPos() : Vector3.zero;
        for (int i = drops.Count - 1; i >= 0; i--)
        {
            var d = drops[i]; d.age += Time.deltaTime;
            float bob = 0.15f * Mathf.Sin(d.age * 3f);
            d.orb.position = d.pos + Vector3.up * (0.5f + bob);
            d.beam.position = d.pos + Vector3.up * (d.beam.localScale.y * 0.5f);
            if (cam != null) { d.orb.rotation = cam.transform.rotation; d.beam.rotation = cam.transform.rotation; }
            var flat = new Vector2(pp.x - d.pos.x, pp.z - d.pos.z).magnitude;
            if (flat <= PickRadius || d.age >= MaxAge)
            {
                var it = d.item; var at = d.pos;
                Destroy(d.beam.gameObject); Destroy(d.orb.gameObject); if (d.pillar != null) Destroy(d.pillar); drops.RemoveAt(i);
                if (OnPick != null) OnPick(it, at);
            }
        }
    }

    /// <summary>이름표: 빛줄기 위에 등급 색 글자(OnGUI). 큰 지도가 열리면 숨긴다</summary>
    GUIStyle st;
    void OnGUI()
    {
        if (drops.Count == 0 || MiniMap.BigOpen) return;
        var cam = Camera.main; if (cam == null) return;
        Ko.Apply();
        if (st == null) st = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold, fontSize = 16 };
        foreach (var d in drops)
        {
            var sp = cam.WorldToScreenPoint(d.pos + Vector3.up * (BeamHeight(d.item) + 0.3f));
            if (sp.z < 0f) continue;
            float k = Mathf.Clamp(Screen.height / 1080f, 0.6f, 1.4f) * 1.0f;   // 화면 크기에 맞춘 이름표 배율
            var plate = First10.Tex("drop_tag_" + d.tier); var mark = First10.Tex("tier_mark_" + d.tier);
            float w = 220f * k, h = 40f * k; var r = new Rect(sp.x - w * 0.5f, Screen.height - sp.y - h * 0.5f, w, h);
            if (plate != null) GUI.DrawTexture(r, plate);
            if (mark != null) GUI.DrawTexture(new Rect(r.x + 4f * k, r.y + 4f * k, 32f * k, 32f * k), mark);   // 왼쪽 28px 자리: 등급 모양(색 없이도 구분)
            var lr = new Rect(r.x + (plate != null ? 34f * k : 0f), r.y, r.width - (plate != null ? 38f * k : 0f), r.height);
            st.fontSize = Mathf.RoundToInt(16 * k);
            st.normal.textColor = Color.black; if (plate == null) GUI.Label(new Rect(lr.x + 1, lr.y + 1, lr.width, lr.height), d.label, st);
            st.normal.textColor = plate != null ? new Color(0.97f, 0.94f, 0.84f) : d.col;; GUI.Label(lr, d.label, st);   // 이름표 판은 짙은 남색 → 밝은 글자
        }
    }
}
