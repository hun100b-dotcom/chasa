// =============================================================================
// GroundTerrain.cs — 새 땅 받는 쪽: 높낮이 지도(하이트맵) + 재질 섞기 지도(스플랫맵) → 청크별 땅 메쉬, 높이 묻기.
// 아트팀이 땅을 새로 만들면 tools/build_terrain_data.py 가 Resources/Terrain 에 넣고, 이 클래스가 알아서 읽는다.
// 파일이 없으면 Active=false 라서 옛 8m 타일 땅이 그대로 쓰인다(아무것도 바뀌지 않음). 형식 약속: docs/TERRAIN-FORMAT.md
// 규칙(보간·정규화)은 Core/TerrainField.cs, 여기는 파일 읽기·메쉬·재질만.
// 왜 .bytes? 유니티가 PNG 를 '읽을 수 있는 그림'으로 주지 않아서, 파일 그대로를 글자 덩어리(TextAsset)로 읽어 LoadImage 로 푼다.
// =============================================================================
using Chasa.Core;
using System.Collections.Generic;
using UnityEngine;

public static class GroundTerrain
{
    [System.Serializable] class Meta { public float size = 640f, height_min_m = 0f, height_max_m = 8f; public int height_res = 641, splat_res = 640; public float[] layer_tile_m; public float[] origin_m; public float size_x_m, size_z_m; }   // origin_m·size_x/z_m 는 2막 직사각 땅

    public static bool Active, Active2;   // Active2: 2막 땅(768×640m, 원점 (0,640))이 켜졌다
    // 붙은 땅들(2막 북쪽·3막 ⑤ 동쪽·⑥ 서쪽): 1막 땅(0~640)과 같은 셰이더에 원점·직사각 크기만 더해 받는다
    class Region { public Meta meta; public HeightField h; public SplatField s; public Material m; public float ox, oz, sx, sz; public bool Has(float x, float z) { return x >= ox && x < ox + sx && z >= oz && z < oz + sz; } }
    static readonly List<Region> extras = new List<Region>();
    static Region RegionAt(float x, float z) { for (int i = 0; i < extras.Count; i++) if (extras[i].Has(x, z)) return extras[i]; return null; }
    static HeightField height; static SplatField splat;
    static Material mat; static Meta meta;
    const float Step = 2f;   // 땅 메쉬 꼭짓점 간격(m). 128m 청크 = 64칸 = 4225 꼭짓점

    /// <summary>월드 (x,z) 의 땅 높이(m). 새 땅이 없으면 0 (옛 평지)</summary>
    public static float HeightAt(float x, float z) { var r = RegionAt(x, z); if (r != null) return r.h.At(x, z); return Active ? height.At(x, z) : 0f; }
    public static float SlopeAt(float x, float z) { var r = RegionAt(x, z); if (r != null) return r.h.Slope(x, z); return Active ? height.Slope(x, z) : 0f; }

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
            var ht = Decode(hb, true); if (ht == null) return;
            var px = ht.GetPixels32(); var r = new byte[px.Length]; var g = new byte[px.Length];
            for (int i = 0; i < px.Length; i++) { r[i] = px[i].r; g[i] = px[i].g; }
            height = HeightField.FromRG(ht.width, ht.height, meta.size, r, g, meta.height_min_m, meta.height_max_m);
            // (옛 CloseWaterGaps 는 뺐다: 아트가 칸과 무관한 연속 물길로 높이맵을 새로 고쳐서 둑을 따로 팔 필요가 없다)
            // 재질 섞기: 5개 층을 float 로 풀어 규칙 클래스에 넘긴다(걸어 다닐 때 재질 소리·미끄러움에 쓸 수 있게)
            var ta = Decode(sa, true); var tb = Decode(Resources.Load<TextAsset>("Terrain/splat_b"), true);
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
            extras.Clear(); Active2 = false;
            // 붙은 땅은 해당 때만 읽는다(1막은 아무것도 안 바뀐다). 색 곱은 아트 TERRAIN-ACT2/ACT3.md 층 뜻 표의 근사값 — PC 캡처로 아트 검수
            if (FieldRules.Act2) Active2 = InitExtra("Terrain2", new[] { new Color(1.2f, 0.7f, 0.5f), new Color(1.3f, 1.1f, 0.55f), new Color(0.9f, 0.9f, 0.95f), new Color(0.35f, 0.35f, 0.5f), new Color(1.3f, 1.05f, 0.6f) });   // 붉은 흙·마른 풀·바위·쇠찌꺼기·황토
            if (FieldRules.Act3)
            {
                InitExtra("Terrain3E", new[] { new Color(1.1f, 1.0f, 0.85f), new Color(0.8f, 1.0f, 0.75f), new Color(0.95f, 0.95f, 1.0f), new Color(1.9f, 1.9f, 1.8f), Color.white });   // ⑤ 갯마을: 마른 갯흙·갯풀·바위·소금 흰색
                InitExtra("Terrain3W", new[] { new Color(1.0f, 0.95f, 0.85f), new Color(0.9f, 0.95f, 0.85f), new Color(0.95f, 0.95f, 1.0f), new Color(1.15f, 0.95f, 0.75f), new Color(2.0f, 2.0f, 2.2f) });   // ⑥ 도성: 흙길·풀·성벽 돌·장터 마당·눈
            }
        }
        catch (System.Exception e) { Debug.LogWarning("새 땅을 읽지 못해 옛 땅을 쓴다: " + e.Message); Active = false; }
    }

    /// <summary>
    /// 붙은 땅 하나(Resources/<dir>): 직사각 땅 + origin 오프셋. 층 그림·잔무늬는 1막 것을 그대로 쓰고 색만 tints 로 곱한다.
    /// 성공하면 걸을 수 있는 땅(FieldRules.AddRegion)도 넓힌다. 실패하면 그 땅만 빠지고 나머지는 그대로다.
    /// </summary>
    static bool InitExtra(string dir, Color[] tints)
    {
        try
        {
            var mj = Resources.Load<TextAsset>(dir + "/terrain"); var hb = Resources.Load<TextAsset>(dir + "/heightmap"); var sa = Resources.Load<TextAsset>(dir + "/splat_a");
            if (mj == null || hb == null || sa == null) return false;
            var mt = JsonUtility.FromJson<Meta>(mj.text);
            float ox = mt.origin_m != null && mt.origin_m.Length >= 2 ? mt.origin_m[0] : 0f, oz = mt.origin_m != null && mt.origin_m.Length >= 2 ? mt.origin_m[1] : 640f;
            float sx = mt.size_x_m > 0f ? mt.size_x_m : mt.size, sz = mt.size_z_m > 0f ? mt.size_z_m : mt.size;
            var ht = Decode(hb, true); if (ht == null) return false;
            var px = ht.GetPixels32(); var r = new byte[px.Length]; var g = new byte[px.Length];
            for (int i = 0; i < px.Length; i++) { r[i] = px[i].r; g[i] = px[i].g; }
            var hf = HeightField.FromRGRect(ht.width, ht.height, sx, sz, ox, oz, r, g, mt.height_min_m, mt.height_max_m);
            var ta = Decode(sa, true); var tb = Decode(Resources.Load<TextAsset>(dir + "/splat_b"), true);
            if (ta == null) return false;
            var pa = ta.GetPixels32(); var pb = tb != null && tb.width == ta.width && tb.height == ta.height ? tb.GetPixels32() : null;
            var layers = new float[SplatField.Layers][];
            for (int l = 0; l < layers.Length; l++) layers[l] = new float[pa.Length];
            for (int i = 0; i < pa.Length; i++) { layers[0][i] = pa[i].r / 255f; layers[1][i] = pa[i].g / 255f; layers[2][i] = pa[i].b / 255f; layers[3][i] = pa[i].a / 255f; layers[4][i] = pb == null ? 0f : pb[i].r / 255f; }
            var sf = new SplatField(ta.width, ta.height, sx, sz, ox, oz, layers);
            var m = MakeMaterial(ta, tb, mt, new Vector4(ox, oz, sx, sz), tints);
            extras.Add(new Region { meta = mt, h = hf, s = sf, m = m, ox = ox, oz = oz, sx = sx, sz = sz });
            FieldRules.AddRegion(ox, oz, ox + sx, oz + sz);   // 걸을 수 있는 땅이 넓어진다
            return true;
        }
        catch (System.Exception e) { Debug.LogWarning(dir + " 땅을 읽지 못했다: " + e.Message); return false; }
    }

    /// <summary>PNG 를 읽는다. flipRows: 지도(높이·재질)는 약속이 '그림 첫 줄(위) = 남쪽(z 0)'인데 유니티는 그림 맨 아랫줄을 0번으로 읽어 남북이 뒤집힌다 → 줄 순서를 뒤집어 바로잡는다</summary>
    static Texture2D Decode(TextAsset ta, bool flipRows = false)
    {
        if (ta == null) return null;
        var t = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);   // 선형(색 보정 없이): 높이·비율 값이라서
        if (!t.LoadImage(ta.bytes)) return null;
        if (flipRows)
        {
            int w = t.width, h = t.height; var px = t.GetPixels32(); var fl = new Color32[px.Length];
            for (int y = 0; y < h; y++) System.Array.Copy(px, y * w, fl, (h - 1 - y) * w, w);
            t.SetPixels32(fl); t.Apply();
        }
        return t;
    }

    /// <summary>그 자리의 재질 비율(흙·풀·자갈·논·낙엽). 걸음 소리·미끄러움에 쓴다. 새 땅이 없으면 풀</summary>
    public static void LayerWeights(float x, float z, float[] o)
    {
        var rg = RegionAt(x, z); if (rg != null) { rg.s.Weights(x, z, o); return; }
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

    /// <summary>날씨의 구름 양(0~1)을 땅 셰이더에 알린다. 구름 그림이 없으면 아무 일도 없다</summary>
    public static void SetCloudCover(float amount)
    {
        if (mat == null || !mat.HasProperty("_CloudAmount")) return;
        if (!cloudTried)
        {
            cloudTried = true;
            var t = SpriteLib.Texture("sky/cloud_shadow");
            if (t != null) { t.wrapMode = TextureWrapMode.Repeat; mat.SetTexture("_CloudTex", t); cloudOk = true; }
        }
        mat.SetFloat("_CloudAmount", cloudOk ? amount * Balance.CLOUD_SHADOW_MULT : 0f);
    }
    static bool cloudTried, cloudOk;

    static Material waterMat, waterDeepMat;

    /// <summary>큰 강 조각(br_*)의 물면용 재질. deep=깊은 곳(어두운 그림). 그림·셰이더가 없으면 null(조각 모델 자체 재질을 그대로 쓴다)</summary>
    public static Material RiverWater(bool deep)
    {
        if (!deep) return WaterMaterial();
        if (waterDeepMat != null) return waterDeepMat;
        var ta = Resources.Load<TextAsset>("Terrain/water_albedo_deep");
        var shared = WaterMaterial();
        if (ta == null || shared == null) return shared;
        var t = Decode(ta); if (t == null) return shared;
        t.wrapMode = TextureWrapMode.Repeat;
        waterDeepMat = new Material(shared) { name = "WaterDeep" };
        waterDeepMat.SetTexture("_MainTex", t);
        return waterDeepMat;
    }
    const float WaterY = 0.18f;   // 아트가 정한 물 높이(m)

    /// <summary>물 재질. 물 그림이나 셰이더가 없으면 null(물을 그리지 않는다)</summary>
    static Material WaterMaterial()
    {
        if (waterMat != null) return waterMat;
        var ta = Resources.Load<TextAsset>("Terrain/water_albedo");
        var sh = Resources.Load<Shader>("Shaders/ChasaWater");
        if (ta == null || sh == null || !sh.isSupported) return null;
        var t = Decode(ta); if (t == null) return null;
        t.wrapMode = TextureWrapMode.Repeat;
        waterMat = new Material(sh);
        waterMat.SetTexture("_MainTex", t);
        waterMat.SetFloat("_TileM", 4f);
        waterMat.SetVector("_Flow", new Vector4(0f, -0.7f, 0f, 0f));   // 남쪽(-z)으로 0.7m/s
        return waterMat;
    }

    /// <summary>땅이 물높이보다 낮은 2m 칸에만 물 판을 깐다(강·개울 자리). 물 판은 없으면 만들지 않는다</summary>
    static void BuildWater(Transform parent, Vector3[] verts, int n, int vn)
    {
        var wm = WaterMaterial(); if (wm == null) return;
        var wv = new List<Vector3>(); var wt = new List<int>();
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                int a = j * vn + i, b = a + 1, c = a + vn, d = c + 1;
                if (verts[a].y >= WaterY && verts[b].y >= WaterY && verts[c].y >= WaterY && verts[d].y >= WaterY) continue;   // 네 꼭짓점이 다 물 위면 마른 땅
                int k = wv.Count;
                wv.Add(new Vector3(verts[a].x, WaterY, verts[a].z)); wv.Add(new Vector3(verts[b].x, WaterY, verts[b].z));
                wv.Add(new Vector3(verts[c].x, WaterY, verts[c].z)); wv.Add(new Vector3(verts[d].x, WaterY, verts[d].z));
                wt.Add(k); wt.Add(k + 2); wt.Add(k + 1); wt.Add(k + 1); wt.Add(k + 2); wt.Add(k + 3);
            }
        if (wv.Count == 0) return;
        var m = new Mesh { name = "Water" };
        m.SetVertices(wv); m.SetTriangles(wt, 0);
        var nr = new Vector3[wv.Count]; for (int i = 0; i < nr.Length; i++) nr[i] = Vector3.up; m.normals = nr;
        m.RecalculateBounds();
        var go = new GameObject("Water"); go.transform.SetParent(parent, false);
        go.AddComponent<MeshFilter>().sharedMesh = m;
        var mr = go.AddComponent<MeshRenderer>(); mr.sharedMaterial = wm;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; mr.receiveShadows = false;
    }

    static void BuildMaterial(Texture2D a, Texture2D b) { mat = MakeMaterial(a, b, meta, new Vector4(0f, 0f, meta.size, meta.size), null); }

    static Material MakeMaterial(Texture2D a, Texture2D b, Meta meta, Vector4 rect, Color[] tints)
    {
        var sh = Resources.Load<Shader>("Shaders/ChasaTerrainSplat");
        if (sh == null || !sh.isSupported) return U.Matte(tints != null ? new Color(0.45f, 0.30f, 0.22f) : new Color(0.34f, 0.46f, 0.26f));   // 셰이더가 안 되는 기기: 한 가지 색 땅(그래도 높낮이는 있다)
        var mat = new Material(sh);
        mat.SetVector("_SplatRect", rect);
        if (tints != null)   // 붙은 땅의 색 곱: 같은 타일 그림에 층마다 곱하는 근사값
            for (int i = 0; i < 5 && i < tints.Length; i++) mat.SetColor("_Tint" + i, tints[i]);
        a.wrapMode = TextureWrapMode.Clamp; a.filterMode = FilterMode.Bilinear; mat.SetTexture("_SplatA", a);
        if (b != null) { b.wrapMode = TextureWrapMode.Clamp; b.filterMode = FilterMode.Bilinear; mat.SetTexture("_SplatB", b); }
        mat.SetTexture("_T0", LayerTex("dirt", "tile_dirt_road_a")); mat.SetTexture("_T1", LayerTex("grass", "tile_grass_a"));
        mat.SetTexture("_T2", LayerTex("gravel", "tile_stepping_stones_a")); mat.SetTexture("_T3", LayerTex("paddy", "tile_paddy_a"));
        mat.SetTexture("_T4", LayerTex("leaf", "tile_grass_b"));
        var tm = meta.layer_tile_m != null && meta.layer_tile_m.Length >= 5 ? meta.layer_tile_m : new[] { 6f, 6f, 6f, 6f, 6f };
        mat.SetVector("_TileM", new Vector4(tm[0], tm[1], tm[2], tm[3])); mat.SetFloat("_TileM4", tm[4]);
        mat.SetFloat("_WorldSize", meta.size);
        // 잔무늬(가까이 볼 때 섞는 이랑·알갱이): 다섯 장이 다 있을 때만 켠다
        string[] dn = { "dirt", "grass", "gravel", "paddy", "leaf" }; int found = 0;
        for (int i = 0; i < 5; i++)
        {
            var ta = Resources.Load<TextAsset>("Terrain/detail_" + dn[i]);
            var t = ta != null ? Decode(ta) : null;
            if (t == null) continue;
            t.wrapMode = TextureWrapMode.Repeat; mat.SetTexture("_D" + i, t); found++;
        }
        mat.SetFloat("_DetailAmount", found == 5 ? 0.5f : 0f);   // 0.5 = 가까울 때 큰 타일과 반반
        return mat;
    }

    /// <summary>청크(cx,cz) 한 칸(128m)의 땅 메쉬를 만들어 parent 아래에 붙인다. 높이는 하이트맵에서</summary>
    public static System.Collections.IEnumerator BuildChunk(Transform parent, int cx, int cz)
    {
        if (!Active) yield break;
        float ccx = cx * FieldRules.ChunkSize + FieldRules.ChunkSize * 0.5f, ccz = cz * FieldRules.ChunkSize + FieldRules.ChunkSize * 0.5f;
        var rg = RegionAt(ccx, ccz);   // 이 청크가 붙은 땅(2막·3막) 위인가
        if (rg == null && !(ccx >= 0f && ccx < FieldRules.Size && ccz >= 0f && ccz < FieldRules.Size)) yield break;   // 어느 땅도 아닌 빈 칸(1막 동쪽 바깥·바다)은 만들지 않는다
        float cs = FieldRules.ChunkSize; int n = Mathf.RoundToInt(cs / Step), vn = n + 1;
        float x0 = cx * cs, z0 = cz * cs;
        var verts = new Vector3[vn * vn]; var uvs = new Vector2[vn * vn]; var tris = new int[n * n * 6];
        for (int j = 0; j < vn; j++)
        {
            for (int i = 0; i < vn; i++)
            {
                float x = x0 + i * Step, z = z0 + j * Step;
                verts[j * vn + i] = new Vector3(x, rg != null ? rg.h.At(x, z) : height.At(x, z), z);
                uvs[j * vn + i] = new Vector2(x / meta.size, z / meta.size);   // (셰이더는 월드 좌표를 쓴다. uv 는 쓰이지 않음)
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
        var mr = go.AddComponent<MeshRenderer>(); mr.sharedMaterial = rg != null ? rg.m : mat;
        mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;   // 땅이 자기 그림자를 만들 필요는 없다(가볍게)
        if (rg == null) BuildWater(parent, verts, n, vn);   // 강·개울 자리에 흐르는 물(붙은 땅은 아직 물 없음: ⑤ 바다는 tide_water 물판)
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
