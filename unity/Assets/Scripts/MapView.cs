// =============================================================================
// MapView.cs — 솔고개 마을을 '보이게' 만든다. 충돌 규칙은 Core/MapLayout, 여기는 색 도형으로 모양만.
// 아트팀 그림(PNG)이 오면(M5) 이 도형들을 스프라이트로 바꾼다. 그래서 만드는 코드를 한곳에 모아 둔다.
// =============================================================================
using Chasa.Core;
using UnityEngine;

public static class MapView
{
    // 임시 색(아트 팀 팔레트에 땅·집 색이 없어 고른 값). 그림이 들어오면 사라진다.
    static readonly Color RoadColor = new Color(0.36f, 0.31f, 0.25f);    // 흙길
    static readonly Color VillageGround = new Color(0.20f, 0.23f, 0.20f); // 마을 바닥
    static readonly Color HouseWall = new Color(0.30f, 0.26f, 0.23f);
    static readonly Color HouseRoof = new Color(0.12f, 0.12f, 0.15f);

    /// <summary>마을을 세운다. 그림 지형 타일을 깔았으면 true (그러면 호출한 쪽이 임시 격자선을 끈다)</summary>
    public static bool Build(Transform parent)
    {
        var root = new GameObject("Solgogae");
        root.transform.SetParent(parent, false);

        // 지형: 아트팀 타일 그림이 있으면 그것을 깔고, 없으면 색 판(흙길·마당)으로 대신한다
        bool tiles = BuildGroundTiles(root);
        if (!tiles)
        {
            // 흙길: 서낭당에서 동쪽 마을 어귀까지 (z=0 따라 납작한 판)
            Flat(root, "Road", new Vector3(14f, 0.012f, 0f), new Vector3(30f, 0.01f, 3.2f), RoadColor);
            // 서낭당 마당: 귀환 반경 안쪽을 조금 밝게
            var yard = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            Object.Destroy(yard.GetComponent<Collider>());
            yard.name = "ShrineYard"; yard.transform.SetParent(root.transform, false);
            yard.transform.position = new Vector3(0, 0.011f, 0);
            yard.transform.localScale = new Vector3(Balance.SHRINE_RADIUS * 2.4f, 0.01f, Balance.SHRINE_RADIUS * 2.4f);
            yard.GetComponent<Renderer>().sharedMaterial = U.Matte(VillageGround);
        }

        // 서낭나무: 몸통(충돌 없음 — 출발점이 막히면 안 되어서)과 둥근 잎
        if (!SpriteProp(root, "props/prop_seonang_tree", new Vector3(-3.2f, 0, 0), 5.5f))
        {
            Prim(PrimitiveType.Cylinder, root, "ShrineTree", new Vector3(0, 1.4f, 0), new Vector3(0.7f, 1.4f, 0.7f), new Color(0.25f, 0.18f, 0.12f));
            Prim(PrimitiveType.Sphere, root, "ShrineLeaves", new Vector3(0, 3.4f, 0), new Vector3(3.4f, 2.4f, 3.4f), new Color(0.18f, 0.30f, 0.22f));
        }

        foreach (var b in MapLayout.Blockers)
        {
            switch (b.Kind)
            {
                case "house":
                    if (SpriteProp(root, (b.X > 0 && ((int)b.X) % 2 == 0) ? "props/prop_giwa" : "props/prop_choga", new Vector3(b.X, 0, b.Z), b.R * 2.8f)) break;
                    Prim(PrimitiveType.Cube, root, "House", new Vector3(b.X, 1.1f, b.Z), new Vector3(b.R * 1.7f, 2.2f, b.R * 1.7f), HouseWall);
                    Prim(PrimitiveType.Cube, root, "Roof", new Vector3(b.X, 2.45f, b.Z), new Vector3(b.R * 2.3f, 0.5f, b.R * 2.3f), HouseRoof);
                    break;
                case "post":
                    if (SpriteProp(root, "props/prop_jangseung", new Vector3(b.X, 0, b.Z), 1.6f)) break;
   // 장승: 길쭉한 나무 기둥 + 붉은 머리 (ChasaRed 로 눈에 띄게)
                    Prim(PrimitiveType.Cube, root, "Post", new Vector3(b.X, 1.2f, b.Z), new Vector3(b.R * 1.6f, 2.4f, b.R * 1.6f), new Color(0.35f, 0.24f, 0.15f));
                    Prim(PrimitiveType.Cube, root, "PostHead", new Vector3(b.X, 2.6f, b.Z), new Vector3(b.R * 2.2f, 0.7f, b.R * 2.2f), ChasaPalette.ChasaRed);
                    break;
                default:       // 돌무더기
                    if (SpriteProp(root, "props/prop_cairn", new Vector3(b.X, 0, b.Z), b.R * 2.4f)) break;
                    Prim(PrimitiveType.Sphere, root, "Stones", new Vector3(b.X, b.R * 0.5f, b.Z), new Vector3(b.R * 2f, b.R, b.R * 2f), new Color(0.42f, 0.42f, 0.44f));
                    break;
            }
        }
        return tiles;
    }


    /// <summary>
    /// 땅 위에 눕힌 네모(쿼드)에 타일 그림을 입힌다. 쿼터뷰(요 45°, 기울기 30°)로 보면 1m 네모가 정확히 2:1 마름모가 되고,
    /// 아트의 마름모 그림은 '그 모습 그대로' 그려져 있어서 마름모의 네 꼭짓점을 네모의 네 모서리에 붙이면(UV) 딱 맞는다.
    /// 화면 위쪽 꼭짓점 = 먼 모서리(-x,-z), 오른쪽 = (-x,+z), 아래 = (+x,+z), 왼쪽 = (+x,-z).
    /// 같은 종류는 메쉬 하나로 묶어 그린다(3600칸이라도 12개 정도의 메쉬).
    /// </summary>
    static bool BuildGroundTiles(GameObject root)
    {
        string[] kinds = { "grass", "dirt_road", "stone_path", "paddy" };
        // 필요한 그림이 하나라도 없으면 통째로 포기한다(반쪽짜리 땅을 막기 위해)
        foreach (var k in kinds) if (SpriteLib.Texture("tiles/tile_" + k + "_a") == null) return false;

        int n = (int)(MapLayout.HalfSize * 2f);
        // 종류별(×a/b 두 무늬) 메쉬 재료
        var verts = new System.Collections.Generic.Dictionary<string, System.Collections.Generic.List<Vector3>>();
        var uvs = new System.Collections.Generic.Dictionary<string, System.Collections.Generic.List<Vector2>>();
        var tris = new System.Collections.Generic.Dictionary<string, System.Collections.Generic.List<int>>();
        float h = 0.5f;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
            {
                float cx = i + 0.5f - MapLayout.HalfSize, cz = j + 0.5f - MapLayout.HalfSize;
                string kind = TileKind(cx, cz);
                string key = kind + (((i * 7 + j * 13) % 3 == 0) ? "_b" : "_a");   // 무늬를 흩뿌려 반복이 티 나지 않게
                if (!verts.ContainsKey(key)) { verts[key] = new System.Collections.Generic.List<Vector3>(); uvs[key] = new System.Collections.Generic.List<Vector2>(); tris[key] = new System.Collections.Generic.List<int>(); }
                int b = verts[key].Count;
                const float y = 0.004f;   // 바닥판 바로 위 (임시 격자·마당 원보다는 아래)
                verts[key].Add(new Vector3(cx - h, y, cz - h)); uvs[key].Add(new Vector2(0.5f, 1f));   // 위
                verts[key].Add(new Vector3(cx - h, y, cz + h)); uvs[key].Add(new Vector2(1f, 0.5f));   // 오른쪽
                verts[key].Add(new Vector3(cx + h, y, cz + h)); uvs[key].Add(new Vector2(0.5f, 0f));   // 아래
                verts[key].Add(new Vector3(cx + h, y, cz - h)); uvs[key].Add(new Vector2(0f, 0.5f));   // 왼쪽
                // 위에서 볼 때 앞면이 위를 향하도록 감는 순서 (유니티는 시계 방향이 앞면)
                tris[key].AddRange(new[] { b, b + 1, b + 2, b, b + 2, b + 3 });
            }
        foreach (var key in verts.Keys)
        {
            var tex = SpriteLib.Texture("tiles/tile_" + key);
            if (tex == null) tex = SpriteLib.Texture("tiles/tile_" + key.Replace("_b", "_a"));
            var mesh = new Mesh();
            mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
            mesh.SetVertices(verts[key]); mesh.SetUVs(0, uvs[key]); mesh.SetTriangles(tris[key], 0);
            mesh.RecalculateNormals(); mesh.RecalculateBounds();
            var go = new GameObject("Tiles_" + key);
            go.transform.SetParent(root.transform, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            var mat = U.Matte(Color.white);
            mat.mainTexture = tex;
            mr.sharedMaterial = mat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
        }
        return true;
    }

    /// <summary>칸 중심 (x,z) 가 어떤 땅인가: 서낭당 돌바닥 → 동쪽 큰길(흙길) → 서쪽 논(보릿들 암시) → 나머지 풀</summary>
    static string TileKind(float x, float z)
    {
        if (x * x + z * z <= (Balance.SHRINE_RADIUS + 1.5f) * (Balance.SHRINE_RADIUS + 1.5f)) return "stone_path";
        if (x > 0f && System.Math.Abs(z) <= 1.6f) return "dirt_road";
        if (x < -18f) return "paddy";
        return "grass";
    }

    /// <summary>그림 소품을 세운다. 그림이 있으면 true (그러면 색 도형은 만들지 않는다). width = 그려질 폭(m)</summary>
    static bool SpriteProp(GameObject root, string name, Vector3 pos, float widthM)
    {
        var s = SpriteLib.Get(name);
        if (s == null) return false;
        var a = ActorSprite.Create(root.transform, null);
        a.transform.position = pos;
        a.Show(name, Vector3.right);
        float natural = s.rect.width / s.pixelsPerUnit;               // 그림 원래 폭(m)
        a.transform.localScale = Vector3.one * (widthM / Mathf.Max(0.1f, natural));
        return true;
    }

    static GameObject Prim(PrimitiveType t, GameObject parent, string name, Vector3 pos, Vector3 scale, Color c)
    {
        var g = GameObject.CreatePrimitive(t);
        Object.Destroy(g.GetComponent<Collider>());   // 충돌은 Core 가 계산한다. 물리 엔진을 쓰지 않으니 끈다
        g.name = name; g.transform.SetParent(parent.transform, false);
        g.transform.position = pos; g.transform.localScale = scale;
        g.GetComponent<Renderer>().sharedMaterial = U.Matte(c);
        return g;
    }

    static void Flat(GameObject parent, string name, Vector3 pos, Vector3 scale, Color c) => Prim(PrimitiveType.Cube, parent, name, pos, scale, c);
}
