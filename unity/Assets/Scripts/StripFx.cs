// =============================================================================
// StripFx.cs — 가로로 이어 붙인 '띠 그림'(여러 프레임이 한 장)을 차례로 보여 주고 사라지는 효과.
// 아트의 손맛 이펙트(hit_*, pahon_ring, tendo_motes)가 이 형식이다. 프레임은 정사각이고 '앞쪽 = 오른쪽(+X)'.
// 왜 메시를 직접 쓰나: 기본 스프라이트 셰이더는 UV 이동·배율(_MainTex_ST)을 안 따라서, 프레임마다 UV 를 직접 바꾼다.
//  - 세우기(billboard): 카메라를 보게 세우고, 때린 방향이 화면에서 오른쪽을 향하도록 돌린다(타격 그림)
//  - 눕히기(flat): 땅에 눕힌다(파혼 고리 등 바닥 효과)
// 그림 파일이 없으면 조용히 건너뛴다(아직 안 들어온 그림이 게임을 멈추지 않게).
// =============================================================================
using UnityEngine;

public class StripFx : MonoBehaviour
{
    int frames; float life, t, fade;
    Mesh mesh; Color tint = Color.white;
    static Material baseMat;
    public static System.Func<bool> HoldWhen;   // true 인 동안 그림 시간을 멈춘다(히트스톱). 게임 쪽이 정해 준다
    static readonly System.Collections.Generic.Dictionary<string, Texture2D> cache = new System.Collections.Generic.Dictionary<string, Texture2D>();

    static Texture2D Tex(string name)
    {
        Texture2D t;
        if (cache.TryGetValue(name, out t)) return t;
        t = SpriteLib.Texture("fx/hit/" + name);
        cache[name] = t;
        return t;
    }

    /// <summary>카메라를 보는 효과. dirWorld 는 '앞쪽'이 향할 월드 방향(없으면 Vector3.zero), size 는 한 변(m)</summary>
    public static void Billboard(string name, int frames, float life, Vector3 pos, Vector3 dirWorld, float size, Color? tint = null)
    {
        var cam = Camera.main; if (cam == null) return;
        var fx = Make(name, frames, life, pos, size, tint); if (fx == null) return;
        float roll = 0f;
        if (dirWorld.sqrMagnitude > 1e-4f)
        {
            // 월드 방향을 화면 방향으로 바꿔 그 각도만큼 그림을 돌린다
            Vector2 a = cam.WorldToScreenPoint(pos), b = cam.WorldToScreenPoint(pos + dirWorld.normalized);
            var d = b - a; if (d.sqrMagnitude > 1e-4f) roll = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
        }
        fx.transform.rotation = Quaternion.LookRotation(cam.transform.forward, cam.transform.up) * Quaternion.Euler(0f, 0f, roll);
    }

    /// <summary>땅에 눕힌 효과(파혼 고리). size 는 한 변(m)</summary>
    public static void Flat(string name, int frames, float life, Vector3 pos, float size, Color? tint = null)
    {
        var fx = Make(name, frames, life, new Vector3(pos.x, pos.y + 0.04f, pos.z), size, tint); if (fx == null) return;
        fx.transform.rotation = Quaternion.Euler(90f, 0f, 0f);   // 앞면(-Z 법선)이 위를 보게 눕힌다
    }

    static StripFx Make(string name, int frames, float life, Vector3 pos, float size, Color? tint)
    {
        var tex = Tex(name); if (tex == null) return null;
        var go = new GameObject("StripFx_" + name);
        go.transform.position = pos;
        float h = size * 0.5f;
        var mesh = new Mesh();
        mesh.SetVertices(new[] { new Vector3(-h, -h, 0), new Vector3(-h, h, 0), new Vector3(h, h, 0), new Vector3(h, -h, 0) });
        mesh.SetUVs(0, new Vector2[4]);
        mesh.SetTriangles(new[] { 0, 1, 2, 0, 2, 3 }, 0);
        mesh.bounds = new Bounds(Vector3.zero, new Vector3(size, size, size));
        go.AddComponent<MeshFilter>().sharedMesh = mesh;
        var mr = go.AddComponent<MeshRenderer>();
        if (baseMat == null)
        {
            // 스프라이트 기본 재질을 빌려 쓴다(셰이더를 이름으로 찾지 않아 웹 빌드에서도 빠지지 않는다)
            var tmp = new GameObject("tmp"); var sr = tmp.AddComponent<SpriteRenderer>();
            baseMat = sr.sharedMaterial; Destroy(tmp);
        }
        mr.sharedMaterial = baseMat;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; mr.receiveShadows = false;
        var pb = new MaterialPropertyBlock(); pb.SetTexture("_MainTex", tex); pb.SetColor("_Color", tint ?? Color.white); mr.SetPropertyBlock(pb);
        var fx = go.AddComponent<StripFx>();
        fx.frames = Mathf.Max(1, frames); fx.life = Mathf.Max(0.05f, life); fx.mesh = mesh; fx.tint = tint ?? Color.white;
        fx.SetFrame(0);
        return fx;
    }

    void SetFrame(int f)
    {
        float u0 = (float)f / frames, u1 = (float)(f + 1) / frames;
        // 꼭짓점 순서: 왼아래·왼위·오른위·오른아래
        mesh.SetUVs(0, new[] { new Vector2(u0, 0), new Vector2(u0, 1), new Vector2(u1, 1), new Vector2(u1, 0) });
    }

    void Update()
    {
        if (HoldWhen != null && HoldWhen()) return;
        t += Time.deltaTime;   // 히트스톱으로 시간이 멈추면(Time.timeScale) 그림도 멈춘다 — 맞은 모습이 붙들려 보이게 하려는 것
        if (t >= life) { Destroy(mesh); Destroy(gameObject); return; }
        SetFrame(Mathf.Min(frames - 1, (int)(t / life * frames)));
    }
}
