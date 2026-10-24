// =============================================================================
// GroundFx.cs — 땅에 깔리는 효과 그림(도술 범위 등). 3장짜리 그림을 차례로 보여 주다 사라진다.
// 땅 위에 눕힌 네모에 입히는 방식(MapView 타일과 같은 원리)이라 땅 속으로 잘리지 않는다.
// 아트의 타원 그림은 '반경 R 의 원'을 쿼터뷰로 본 모습이라, 네모 한 변을 R×√2 로 잡으면 타원 가장자리가 반경 R 에 닿는다.
// =============================================================================
using UnityEngine;

public class GroundFx : MonoBehaviour
{
    string prefix; int frames; float life, t;
    MeshRenderer mr;
    MaterialPropertyBlock block;
    static Material baseMat;

    /// <summary>center 에서 반경 radius(m) 의 효과를 duration 초 동안. prefix = "fx/fx_call_" 처럼 끝 번호 앞까지</summary>
    public static void Play(Vector3 center, float radius, string prefix, int frames, float duration)
    {
        if (SpriteLib.Texture(prefix + "0") == null) return;   // 그림이 없으면 조용히 건너뜀
        var go = new GameObject("GroundFx");
        go.transform.position = new Vector3(center.x, 0.03f, center.z);   // 타일(0.004)·임시 마당(0.011) 위
        float h = radius * 1.4142f * 0.5f;
        var mesh = new Mesh();
        mesh.SetVertices(new[] { new Vector3(-h, 0, -h), new Vector3(-h, 0, h), new Vector3(h, 0, h), new Vector3(h, 0, -h) });
        mesh.SetUVs(0, new[] { new Vector2(0.5f, 1f), new Vector2(1f, 0.5f), new Vector2(0.5f, 0f), new Vector2(0f, 0.5f) });   // MapView 타일과 같은 모서리 대응
        mesh.SetTriangles(new[] { 0, 1, 2, 0, 2, 3 }, 0);
        mesh.RecalculateBounds();
        go.AddComponent<MeshFilter>().sharedMesh = mesh;
        var fx = go.AddComponent<GroundFx>();
        fx.mr = go.AddComponent<MeshRenderer>();
        if (baseMat == null)
        {
            // 스프라이트 기본 재질(투명 합성)을 빌려 쓴다: 셰이더를 이름으로 찾지 않아 웹 빌드에서도 빠지지 않는다
            var tmp = new GameObject("tmp"); var sr = tmp.AddComponent<SpriteRenderer>();
            baseMat = sr.sharedMaterial; Destroy(tmp);
        }
        fx.mr.sharedMaterial = baseMat;
        fx.mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        fx.mr.receiveShadows = false;
        fx.block = new MaterialPropertyBlock();
        fx.prefix = prefix; fx.frames = frames; fx.life = duration;
        fx.Apply(0, 1f);
    }

    void Apply(int frame, float alpha)
    {
        var tex = SpriteLib.Texture(prefix + frame);
        if (tex == null) return;
        block.SetTexture("_MainTex", tex);
        block.SetColor("_Color", new Color(1f, 1f, 1f, alpha));
        mr.SetPropertyBlock(block);
    }

    void Update()
    {
        t += Time.unscaledDeltaTime;
        if (t >= life) { Destroy(gameObject); return; }
        int f = Mathf.Min(frames - 1, (int)(t / life * frames));
        float fade = Mathf.Clamp01((life - t) / (life * 0.4f));   // 끝 40% 동안 투명해지며 사라진다
        Apply(f, fade);
    }
}
