// =============================================================================
// ClickMarker.cs — 이동 클릭 지점에 나타났다 안쪽으로 모이는 링 (Godot판 click_marker.gd)
// =============================================================================
using UnityEngine;

public class ClickMarker : MonoBehaviour
{
    float age = float.PositiveInfinity;
    Mesh mesh;
    Color[] colors;

    public static ClickMarker Create()
    {
        var go = new GameObject("ClickMarker");
        var m = go.AddComponent<ClickMarker>();
        // 바닥에 눕힌 고리(안 반지름 0.3, 바깥 0.42) 메쉬를 직접 만든다
        const int seg = 28;
        var v = new Vector3[seg * 2];
        var tris = new int[seg * 6];
        for (int i = 0; i < seg; i++)
        {
            float a = i * U.TAU / seg;
            v[i * 2] = new Vector3(Mathf.Cos(a) * 0.3f, 0, Mathf.Sin(a) * 0.3f);
            v[i * 2 + 1] = new Vector3(Mathf.Cos(a) * 0.42f, 0, Mathf.Sin(a) * 0.42f);
            int n = (i + 1) % seg;
            tris[i * 6 + 0] = i * 2; tris[i * 6 + 1] = n * 2; tris[i * 6 + 2] = i * 2 + 1;
            tris[i * 6 + 3] = i * 2 + 1; tris[i * 6 + 4] = n * 2; tris[i * 6 + 5] = n * 2 + 1;
        }
        m.mesh = new Mesh { vertices = v, triangles = tris };
        m.colors = new Color[v.Length];
        go.AddComponent<MeshFilter>().sharedMesh = m.mesh;
        var r = go.AddComponent<MeshRenderer>();
        r.sharedMaterial = U.VertexColor();
        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        go.SetActive(false);
        return m;
    }

    public void Show(Vector3 p)
    {
        transform.position = new Vector3(p.x, 0.04f, p.z);
        age = 0f;
        gameObject.SetActive(true);
    }

    public void Tick(float dt)
    {
        if (!gameObject.activeSelf) return;
        age += dt;
        float t = age / Config.CLICK_MARKER_LIFETIME;
        if (t >= 1f) { gameObject.SetActive(false); return; }
        transform.localScale = Vector3.one * (1.6f - 0.9f * t); // 바깥에서 안쪽으로 모임
        var c = Config.CLICK_MARKER_COLOR; c.a = 1f - t;
        for (int i = 0; i < colors.Length; i++) colors[i] = c;
        mesh.colors = colors;
    }
}
