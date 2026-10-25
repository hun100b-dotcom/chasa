// =============================================================================
// GroundTerrain.cs — 새 땅 받는 쪽: 높낮이 지도(하이트맵) + 재질 섞기 지도(스플랫맵) → 청크별 땅 메쉬, 높이 묻기.
// 아트팀이 땅을 새로 만들면 tools/build_terrain_data.py 가 Resources/Terrain 에 넣고, 이 클래스가 알아서 읽는다.
// 파일이 없으면 Active=false 라서 옛 8m 타일 땅이 그대로 쓰인다(아무것도 바뀌지 않음). 형식 약속: docs/TERRAIN-FORMAT.md
// 규칙(보간·정규화)은 Core/TerrainField.cs, 여기는 파일 읽기·메쉬·재질만.
// 왜 .bytes? 유니티가 PNG 를 '읽을 수 있는 그림'으로 주지 않아서, 파일 그대로를 글자 덩어리(TextAsset)로 읽어 LoadImage 로 푼다.
// =============================================================================
using Chasa.Core;
using UnityEngine;

public static class GroundTerrain
{
    [System.Serializable] class Meta { public float size = 640f, height_min_m = 0f, height_max_m = 8f; public int height_res = 641, splat_res = 640; public float[] layer_tile_m; }

    public static bool Active;
    static HeightField height; static SplatField splat;
    static Material mat; static Meta meta;
    const float Step = 2f;   // 땅 메쉬 꼭짓점 간격(m). 128m 청크 = 64칸 = 4225 꼭짓점

    /// <summary>월드 (x,z) 의 땅 높이(m). 새 땅이 없으면 0 (옛 평지)</summary>
    public static float HeightAt(float x, float z) { return Active ? height.At(x, z) : 0f; }
    public static float SlopeAt(float x, float z) { return Active ? height.Slope(x, z) : 0f; }

    public static void Init()
    {
        Active = false;
        try
        {
            var mj = Resources.Load<TextAsset>("Terrain/terrain");
            var hb = Resources.Load<TextAsset>("Terrain/heightmap");
            var sa = Resources.Load<TextAsset>("Terrain/splat_a");
            if (mj == null || hb == null || sa == null) return;   // 아직 아트 산출물이 없다
            meta = JsonUtility.FromJson<Meta>(mj.text);
            var ht = Decode(hb); if (ht == null) return;
            var px = ht.GetPixels32(); var r = new byte[px.Length]; var g = new byte[px.Length];
            for (int i = 0; i < px.Length; i++) { r[i] = px[i].r; g[i] = px[i].g; }
            height = HeightField.FromRG(ht.width, ht.height, meta.size, r, g, meta.height_min_m, meta.height_max_m);
            // 재질 섞기: 5개 층을 float 로 풀어 규칙 클래스에 넘긴다(걸어 다닐 때 재질 소리·미끄러움에 쓸 수 있게)
            var ta = Decode(sa); var tb = Decode(Resources.Load<TextAsset>("Terrain/splat_b"));
            if (ta != null)
            {
                var pa = ta.GetPixels32(); var pb = tb != null && tb.width == ta.width && tb.height == ta.height ? tb.GetPixels32() : null;
                var layers = new float[SplatField.Layers][];
                for (int l = 0; l < layers.Length; l++) layers[l] = new float[pa.Length];
                for (int i = 0; i < pa.Length; i++) { layers[0][i] = pa[i].r / 255f; layers[1][i] = pa[i].g / 255f; layers[2][i] = pa[i].b / 255f; layers[3][i] = pa[i].a / 255f; layers[4][i] = pb == null ? 0f : pb[i].r / 255f; }
                splat = new SplatField(ta.width, ta.height, meta.size, layers);
                BuildMaterial(ta, tb);
            }
            Active = true;
        }
        catch (System.Exception e) { Debug.LogWarning("새 땅을 읽지 못해 옛 땅을 쓴다: " + e.Message); Active = false; }
    }

    static Texture2D Decode(TextAsset ta)
    {
        if (ta == null) return null;
        var t = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);   // 선형(색 보정 없이): 높이·비율 값이라서
        return t.LoadImage(ta.bytes) ? t : null;
    }

    /// <summary>그 자리의 재질 비율(흙·풀·자갈·논·낙엽). 걸음 소리·미끄러움에 쓴다. 새 땅이 없으면 풀</summary>
    public static void LayerWeights(float x, float z, float[] o)
    {
        if (Active && splat != null) { splat.Weights(x, z, o); return; }
        for (int i = 0; i < o.Length; i++) o[i] = i == (int)GroundLayer.Grass ? 1f : 0f;
    }

    static Texture2D LayerTex(string layer, string fallbackTile)
    {
        var ta = Resources.Load<TextAsset>("Terrain/layer_" + layer);   // 아트가 이음매 없는 전용 타일을 주면 그것을, 아니면 옛 타일 그림을 대신 쓴다
        Texture2D t = ta != null ? Decode(ta) : null;
        if (t == null) t = SpriteLib.Texture("tiles/" + fallbackTile);
        if (t != null) t.wrapMode = TextureWrapMode.Repeat;
        return t;
    }

    static void BuildMaterial(Texture2D a, Texture2D b)
    {
        var sh = Resources.Load<Shader>("Shaders/ChasaTerrainSplat");
        if (sh == null || !sh.isSupported) { mat = U.Matte(new Color(0.34f, 0.46f, 0.26f)); return; }   // 셰이더가 안 되는 기기: 한 가지 풀색 땅(그래도 높낮이는 있다)
        mat = new Material(sh);
        a.wrapMode = TextureWrapMode.Clamp; a.filterMode = FilterMode.Bilinear; mat.SetTexture("_SplatA", a);
        if (b != null) { b.wrapMode = TextureWrapMode.Clamp; b.filterMode = FilterMode.Bilinear; mat.SetTexture("_SplatB", b); }
        mat.SetTexture("_T0", LayerTex("dirt", "tile_dirt_road_a")); mat.SetTexture("_T1", LayerTex("grass", "tile_grass_a"));
        mat.SetTexture("_T2", LayerTex("gravel", "tile_stepping_stones_a")); mat.SetTexture("_T3", LayerTex("paddy", "tile_paddy_a"));
        mat.SetTexture("_T4", LayerTex("leaf", "tile_grass_b"));
        var tm = meta.layer_tile_m != null && meta.layer_tile_m.Length >= 5 ? meta.layer_tile_m : new[] { 6f, 6f, 6f, 6f, 6f };
        mat.SetVector("_TileM", new Vector4(tm[0], tm[1], tm[2], tm[3])); mat.SetFloat("_TileM4", tm[4]);
        mat.SetFloat("_WorldSize", meta.size);
    }

    /// <summary>청크(cx,cz) 한 칸(128m)의 땅 메쉬를 만들어 parent 아래에 붙인다. 높이는 하이트맵에서</summary>
    public static System.Collections.IEnumerator BuildChunk(Transform parent, int cx, int cz)
    {
        if (!Active) yield break;
        float cs = FieldRules.ChunkSize; int n = Mathf.RoundToInt(cs / Step), vn = n + 1;
        float x0 = cx * cs, z0 = cz * cs;
        var verts = new Vector3[vn * vn]; var uvs = new Vector2[vn * vn]; var tris = new int[n * n * 6];
        for (int j = 0; j < vn; j++)
        {
            for (int i = 0; i < vn; i++)
            {
                float x = x0 + i * Step, z = z0 + j * Step;
                verts[j * vn + i] = new Vector3(x, height.At(x, z), z);
                uvs[j * vn + i] = new Vector2(x / meta.size, z / meta.size);
            }
            if (j % 24 == 23) yield return null;   // 한 프레임에 몰아 만들면 걸음이 뚝 끊긴다 → 여러 프레임에 나눠 만든다
        }
        int t = 0;
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                int a = j * vn + i, b = a + 1, c = a + vn, d = c + 1;
                tris[t++] = a; tris[t++] = c; tris[t++] = b;   // 위(+y)가 앞면이 되는 순서
                tris[t++] = b; tris[t++] = c; tris[t++] = d;
            }
        yield return null;   // 정점 계산과 메시 조립(법선 계산 포함)을 서로 다른 프레임에
        if (parent == null) yield break;   // 그 사이 청크가 꺼졌으면 만들지 않는다
        var mesh = new Mesh { name = "Ground_" + cx + "_" + cz };
        mesh.vertices = verts; mesh.uv = uvs; mesh.triangles = tris;
        mesh.RecalculateNormals(); mesh.RecalculateBounds();
        var go = new GameObject("Ground");
        go.transform.SetParent(parent, false);
        go.AddComponent<MeshFilter>().sharedMesh = mesh;
        var mr = go.AddComponent<MeshRenderer>(); mr.sharedMaterial = mat;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;   // 땅이 자기 그림자를 만들 필요는 없다(가볍게)
    }
}

/// <summary>땅 높이를 따라 발을 붙이는 부품: 새 땅이 켜져 있을 때만 붙는다(주인공·적·NPC). offset 은 땅 위로 띄울 높이</summary>
public class GroundSnap : MonoBehaviour
{
    public float offset;
    public static void Attach(GameObject go, float offset = 0f)
    {
        if (!GroundTerrain.Active || go.GetComponent<GroundSnap>() != null) return;
        go.AddComponent<GroundSnap>().offset = offset;
    }

    void LateUpdate()
    {
        var p = transform.position;
        float y = offset + GroundTerrain.HeightAt(p.x, p.z);
        if (Mathf.Abs(p.y - y) > 0.001f) transform.position = new Vector3(p.x, y, p.z);
    }
}
