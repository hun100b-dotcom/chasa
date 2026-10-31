// =============================================================================
// ChainLink.cs — 연속 천도 사슬선 (개편 P0-2).
//
// 무엇을? 방금 보낸(천도) 혼 / 깨뜨린(파혼) 자리에서 "다음에 연속으로 보낼 혼"까지 바닥에 사슬 한 줄을 깐다.
// 왜? 연속 천도 창(방금 처결한 뒤 몇 초 안)이 열려 있다는 사실을 글자(연쇄!)가 아니라 장면으로 보여 주려고.
//   "저 혼까지 이어서 가면 0.8초에 끝난다"가 눈에 보이면, 창이 닫히기 전에 이동할지 말지가 선택이 된다.
// 규칙(수치)은 건드리지 않는다: 창 길이·0.8초 시전은 Balance 가 그대로 결정한다. 이 파일은 그림만 깐다.
// 그림이 없으면(Resources/Sprites/overhaul/mark) 아무것도 안 그린다 — 그림 없이도 게임은 돈다.
// =============================================================================
using UnityEngine;

public class ChainLink
{
    SpriteRenderer seg, nodeA, nodeB;
    Sprite segSprite, weakSprite;
    bool tried, ok;   // 그림 불러오기를 한 번만 시도한다

    const float SegHeightM = 40f / 128f;   // 사슬 조각 그림 높이(1 m = 128 px 규격)
    const float WeakLeftSec = 0.6f;        // 창이 이만큼 남으면 약한 사슬로 바꿔 끼운다(아트 메모는 0.2초지만, 창이 몇 초라 0.2초는 눈에 안 띈다)

    // 바닥에 눕힌 가로 반복 스프라이트. Tiled 는 FullRect 메시여야 해서 Sprite.Create 에 명시한다
    static Sprite Load(string name)
    {
        var t = SpriteLib.Texture("overhaul/mark/" + name);
        if (t == null) return null;
        return Sprite.Create(t, new Rect(0, 0, t.width, t.height), new Vector2(0f, 0.5f), 128f, 0, SpriteMeshType.FullRect);   // 피벗 왼쪽 가운데: 시작점에서 뻗어 나가게
    }

    SpriteRenderer MakeRenderer(string n, Sprite s, int order)
    {
        var r = new GameObject(n).AddComponent<SpriteRenderer>();
        r.sprite = s; r.sortingOrder = order; r.gameObject.SetActive(false);
        return r;
    }

    void Init()
    {
        tried = true;
        segSprite = Load("chain_seg"); weakSprite = Load("chain_seg_weak");
        var nodeTex = SpriteLib.Texture("overhaul/mark/chain_node");
        if (segSprite == null || nodeTex == null) return;
        var ns = Sprite.Create(nodeTex, new Rect(0, 0, nodeTex.width, nodeTex.height), new Vector2(0.5f, 0.5f), 128f);
        seg = MakeRenderer("ChainLinkSeg", segSprite, 28);
        seg.drawMode = SpriteDrawMode.Tiled; seg.tileMode = SpriteTileMode.Continuous;
        nodeA = MakeRenderer("ChainLinkNodeA", ns, 29); nodeB = MakeRenderer("ChainLinkNodeB", ns, 29);
        ok = true;
    }

    /// <summary>from → to 로 사슬을 깐다. 창이 거의 닫히면(left ≤ 0.6초) 약한 사슬로 바꾼다</summary>
    public void Show(Vector3 from, Vector3 to, float windowLeft)
    {
        if (!tried) Init();
        if (!ok) return;
        from.y = to.y = 0.05f + Mathf.Max(GroundTerrain.HeightAt(from.x, from.z), GroundTerrain.HeightAt(to.x, to.z));   // 땅 위에 살짝 띄워 파묻힘 방지
        var d = to - from; d.y = 0f;
        float len = d.magnitude;
        if (len < 0.3f) { Hide(); return; }
        seg.sprite = windowLeft <= WeakLeftSec && weakSprite != null ? weakSprite : segSprite;
        seg.size = new Vector2(len, SegHeightM);   // 가로로 len m 만큼 조각을 반복해 깐다
        float yaw = Mathf.Atan2(-d.z, d.x) * Mathf.Rad2Deg;   // 그림의 가로축이 from→to 를 향하도록 돌린다
        seg.transform.rotation = Quaternion.Euler(0f, yaw, 0f) * Quaternion.Euler(90f, 0f, 0f);   // 먼저 땅에 눕히고 방향을 돌린다
        seg.transform.position = from;
        nodeA.transform.position = from; nodeB.transform.position = to;
        nodeA.transform.rotation = nodeB.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
        float a = windowLeft <= WeakLeftSec ? 0.5f : 1f;
        nodeA.color = nodeB.color = new Color(1f, 1f, 1f, a);
        seg.gameObject.SetActive(true); nodeA.gameObject.SetActive(true); nodeB.gameObject.SetActive(true);
    }

    public void Hide()
    {
        if (!ok) return;
        seg.gameObject.SetActive(false); nodeA.gameObject.SetActive(false); nodeB.gameObject.SetActive(false);
    }

    public void Destroy()
    {
        if (!ok) return;
        Object.Destroy(seg.gameObject); Object.Destroy(nodeA.gameObject); Object.Destroy(nodeB.gameObject); ok = false;
    }
}
