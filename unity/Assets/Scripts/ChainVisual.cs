// =============================================================================
// ChainVisual.cs — 철삭(쇠사슬) 모습 + 휘두른 자리의 빛 잔상 (Godot판 chain_visual.gd)
// 판정은 Player.cs, 여기는 그림만.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class ChainVisual : MonoBehaviour
{
    public SwingTrail trail;
    readonly List<Transform> links = new List<Transform>();
    Transform head;
    readonly Vector3[] points = new Vector3[Config.CHAIN_SEGMENTS + 1];
    float spin;

    public static ChainVisual Create()
    {
        var go = new GameObject("Chain");
        var cv = go.AddComponent<ChainVisual>();
        var linkMat = U.Unlit(Config.CHAIN_LINK_COLOR);
        for (int i = 0; i < Config.CHAIN_SEGMENTS; i++)
        {
            // 마디 = 납작한 박스. 길이(z)는 1로 두고 마디 간격만큼 늘린다
            var link = Prim(PrimitiveType.Cube, linkMat, go.transform);
            cv.links.Add(link);
        }
        cv.head = Prim(PrimitiveType.Cube, U.Unlit(Config.CHAIN_HEAD_COLOR), go.transform);
        cv.head.localScale = Vector3.one * 0.42f;
        cv.trail = SwingTrail.Create();
        go.SetActive(false);
        return cv;
    }

    static Transform Prim(PrimitiveType t, Material m, Transform parent)
    {
        var p = GameObject.CreatePrimitive(t);
        Object.Destroy(p.GetComponent<Collider>()); // 판정은 직접 계산하므로 물리 충돌체는 필요 없다
        var r = p.GetComponent<Renderer>();
        r.sharedMaterial = m;
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        p.transform.SetParent(parent, false);
        return p.transform;
    }

    /// <summary>
    /// 손(hand) 기준 극좌표로 사슬 끝을 받는다.
    /// lag = 사슬 몸통이 끝보다 뒤처지는 각도(채찍 휘어짐 → 속도감) / sag = 중력 처짐
    /// </summary>
    public void SetShape(Vector3 hand, float angle, float radius, float headY, float lag, float sag)
    {
        int n = Config.CHAIN_SEGMENTS;
        for (int i = 0; i <= n; i++)
        {
            float t = (float)i / n; // 0 = 손, 1 = 끝
            float a = angle - lag * Mathf.Pow(1f - t, 1.5f); // 손 쪽일수록 많이 뒤처짐
            float r = radius * t;
            points[i] = new Vector3(hand.x + Mathf.Cos(a) * r,
                                    hand.y + (headY - hand.y) * t - sag * Mathf.Sin(Mathf.PI * t),
                                    hand.z + Mathf.Sin(a) * r);
        }
        for (int i = 0; i < n; i++)
        {
            Vector3 p = points[i], q = points[i + 1];
            Vector3 d = q - p;
            float len = d.magnitude;
            var link = links[i];
            if (len < 1e-4f) { link.gameObject.SetActive(false); continue; }
            link.gameObject.SetActive(true);
            link.position = (p + q) * 0.5f;
            link.rotation = Quaternion.LookRotation(d) * Quaternion.Euler(0, 0, i % 2 == 0 ? 0 : 90); // 번갈아 눕혀 고리 느낌
            link.localScale = new Vector3(0.2f, 0.07f, Mathf.Max(0.01f, len * 0.92f));
        }
        head.position = points[n];
        spin += 0.35f;
        head.rotation = Quaternion.Euler(spin * Mathf.Rad2Deg, spin * 0.7f * Mathf.Rad2Deg, 0);
    }
}

// -----------------------------------------------------------------------------
// 궤적 잔상: "사슬 안쪽 점"과 "사슬 끝 점"을 기록해 띠로 잇고, 오래된 부분일수록 투명하게.
// -----------------------------------------------------------------------------
public class SwingTrail : MonoBehaviour
{
    struct Sample { public Vector3 inner, outer; public float age; public bool start; }

    readonly List<Sample> samples = new List<Sample>();
    Mesh mesh;
    readonly List<Vector3> verts = new List<Vector3>();
    readonly List<Color> cols = new List<Color>();
    readonly List<int> tris = new List<int>();

    public static SwingTrail Create()
    {
        var go = new GameObject("SwingTrail");
        var t = go.AddComponent<SwingTrail>();
        t.mesh = new Mesh();
        t.mesh.MarkDynamic(); // 매 프레임 모양이 바뀐다고 알려 성능을 챙긴다
        go.AddComponent<MeshFilter>().sharedMesh = t.mesh;
        var r = go.AddComponent<MeshRenderer>();
        r.sharedMaterial = U.Additive();
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        return t;
    }

    public void Add(Vector3 inner, Vector3 outer, bool start)
    {
        samples.Add(new Sample { inner = inner, outer = outer, age = 0f, start = start });
        if (samples.Count > Config.TRAIL_MAX_SAMPLES) samples.RemoveAt(0);
    }

    float AlphaOf(Sample s) => Config.TRAIL_ALPHA * Mathf.Pow(1f - s.age / Config.TRAIL_LIFETIME, Config.TRAIL_FADE_POWER);

    public void Tick(float dt)
    {
        for (int i = 0; i < samples.Count; i++) { var s = samples[i]; s.age += dt; samples[i] = s; }
        while (samples.Count > 0 && samples[0].age >= Config.TRAIL_LIFETIME) samples.RemoveAt(0);

        verts.Clear(); cols.Clear(); tris.Clear();
        for (int i = 1; i < samples.Count; i++)
        {
            Sample a = samples[i - 1], b = samples[i];
            if (b.start) continue; // 새 휘두르기의 첫 점은 이전 것과 잇지 않는다
            float aa = AlphaOf(a), ab = AlphaOf(b);
            // 안쪽은 옅게(×0.15), 바깥(사슬 끝 궤적)은 진하게 → 칼날 같은 빛줄기
            Put(a.inner, Config.TRAIL_COLOR_INNER, aa * 0.15f); Put(a.outer, Config.TRAIL_COLOR_OUTER, aa); Put(b.outer, Config.TRAIL_COLOR_OUTER, ab);
            Put(a.inner, Config.TRAIL_COLOR_INNER, aa * 0.15f); Put(b.outer, Config.TRAIL_COLOR_OUTER, ab); Put(b.inner, Config.TRAIL_COLOR_INNER, ab * 0.15f);
        }
        mesh.Clear();
        mesh.SetVertices(verts);
        mesh.SetColors(cols);
        mesh.SetTriangles(tris, 0);
        mesh.bounds = new Bounds(Vector3.zero, Vector3.one * 200f); // 화면 밖 판정으로 사라지지 않게 넉넉히
    }

    void Put(Vector3 p, Color c, float alpha)
    {
        tris.Add(verts.Count);
        verts.Add(p);
        cols.Add(new Color(c.r, c.g, c.b, alpha));
    }
}
