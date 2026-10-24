// =============================================================================
// MapView.cs — 솔고개 마을을 '보이게' 만든다. 모양 데이터는 Core/MapData(아트 배치표), 충돌은 Core/MapLayout.
// 그림(PNG)이 있으면 그림으로, 없으면 색 도형으로 대신 그린다 — 그림이 없어도 게임은 돈다.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public static class MapView
{
    // 그림이 없을 때 쓰는 임시 색(아트 팀 팔레트에 땅·집 색이 없어 고른 값)
    static readonly Color VillageGround = new Color(0.20f, 0.23f, 0.20f);
    static readonly Color HouseWall = new Color(0.30f, 0.26f, 0.23f);
    static readonly Color HouseRoof = new Color(0.12f, 0.12f, 0.15f);

    // MapData.Ground 의 글자 → 타일 그림 이름
    static string TileName(char c)
    {
        switch (c)
        {
            case 'S': return "stone_path";
            case 'D': return "dirt_road";
            case 'Y': return "yard";
            case 'P': return "paddy";
            case 'T': return "stepping_stones";
            default: return "grass";
        }
    }

    /// <summary>마을을 세운다. 그림 지형 타일을 깔았으면 true (그러면 호출한 쪽이 임시 격자선을 끈다)</summary>
    public static bool Build(Transform parent)
    {
        var root = new GameObject("Solgogae");
        root.transform.SetParent(parent, false);

        bool tiles = BuildGroundTiles(root, MapData.Ground, MapLayout.VillageMinX, MapLayout.VillageMinZ);
        if (!tiles)
        {
            // 그림이 없을 때: 서낭당 마당만 색 원으로 (귀환 반경 안쪽을 조금 밝게)
            var yard = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            Object.Destroy(yard.GetComponent<Collider>());
            yard.name = "ShrineYard"; yard.transform.SetParent(root.transform, false);
            yard.transform.position = new Vector3(0, 0.011f, 0);
            yard.transform.localScale = new Vector3(Balance.SHRINE_RADIUS * 2.4f, 0.01f, Balance.SHRINE_RADIUS * 2.4f);
            yard.GetComponent<Renderer>().sharedMaterial = U.Matte(VillageGround);
        }

        // 소품: 배치표의 그림 소품. 서낭나무는 출발점(원점) 바로 뒤쪽(카메라에서 먼 쪽)에 세워 주인공을 가리지 않게 한다
        foreach (var p in MapData.Props)
        {
            float x = MapLayout.WorldX(p.Ay), z = MapLayout.WorldZ(p.Ax);
            if (p.Sprite.EndsWith("seonang_tree")) { x = -2.2f; z = -1.0f; }
            // 그림 폭은 배치표 칸 수 × 칸 길이 × 1.4(등각 화면에서 1m 칸의 폭) 정도로 맞춘다
            float widthM = p.W * Balance.MAP_CELL_SIZE * 1.1f + 0.8f;
            if (p.Sprite.EndsWith("seonang_tree")) widthM = 5.5f;
            if (!SpriteProp(root, p.Sprite, new Vector3(x, 0, z), widthM))
                FallbackShape(root, p.Sprite, x, z, widthM);
        }
        return tiles;
    }

    /// <summary>
    /// 땅 위에 눕힌 네모(쿼드)에 타일 그림을 입힌다. 쿼터뷰(요 45°, 기울기 30°)로 보면 네모가 정확히 2:1 마름모가 되고,
    /// 아트의 마름모 그림은 '그 모습 그대로' 그려져 있어서 마름모의 네 꼭짓점을 네모의 네 모서리에 붙이면(UV) 딱 맞는다.
    /// 화면 위쪽 꼭짓점 = 먼 모서리(-x,-z), 오른쪽 = (-x,+z), 아래 = (+x,+z), 왼쪽 = (+x,-z).
    /// 같은 종류·무늬는 메쉬 하나로 묶어 그린다.
    /// </summary>
    /// <summary>땅 그림(타일)이 전부 있는가. 하나라도 없으면 반쪽짜리 땅을 막으려고 통째로 포기한다</summary>
    public static bool GroundArtAvailable()
    {
        foreach (var k in new[] { "grass", "dirt_road", "stone_path", "paddy", "yard", "stepping_stones" })
            if (SpriteLib.Texture("tiles/tile_" + k + "_a") == null) return false;
        return true;
    }

    static bool BuildGroundTiles(GameObject root, string[] ground, float originX, float originZ, int rowFrom = 0, int rowTo = -1)
    {
        if (!GroundArtAvailable()) return false;
        if (rowTo < 0 || rowTo > ground.Length) rowTo = ground.Length;   // 기본: 전체 줄

        var verts = new Dictionary<string, List<Vector3>>();
        var uvs = new Dictionary<string, List<Vector2>>();
        var tris = new Dictionary<string, List<int>>();
        float h = Balance.MAP_CELL_SIZE * 0.5f;
        const float y = 0.004f;   // 바닥판 바로 위 (임시 격자·마당 원보다는 아래)
        for (int gy = rowFrom; gy < rowTo; gy++)
            for (int gx = 0; gx < ground[gy].Length; gx++)
            {
                // 칸 중심. (마을은 originX = 마을 모서리라 예전 WorldX(gy+0.5)와 같은 값이다)
                float cx = originX + (gy + 0.5f) * Balance.MAP_CELL_SIZE, cz = originZ + (gx + 0.5f) * Balance.MAP_CELL_SIZE;
                string key = TileName(ground[gy][gx]) + (((gx * 7 + gy * 13) % 3 == 0) ? "_b" : "_a");   // 무늬를 흩뿌려 반복이 티 나지 않게
                if (!verts.ContainsKey(key)) { verts[key] = new List<Vector3>(); uvs[key] = new List<Vector2>(); tris[key] = new List<int>(); }
                int b = verts[key].Count;
                verts[key].Add(new Vector3(cx - h, y, cz - h)); uvs[key].Add(new Vector2(0.5f, 1f));   // 위
                verts[key].Add(new Vector3(cx - h, y, cz + h)); uvs[key].Add(new Vector2(1f, 0.5f));   // 오른쪽
                verts[key].Add(new Vector3(cx + h, y, cz + h)); uvs[key].Add(new Vector2(0.5f, 0f));   // 아래
                verts[key].Add(new Vector3(cx + h, y, cz - h)); uvs[key].Add(new Vector2(0f, 0.5f));   // 왼쪽
                // 위에서 볼 때 시계 방향 = 앞면이 위를 향한다 (유니티 규칙)
                tris[key].AddRange(new[] { b, b + 1, b + 2, b, b + 2, b + 3 });
            }
        foreach (var key in verts.Keys)
        {
            var tex = SpriteLib.Texture("tiles/tile_" + key) ?? SpriteLib.Texture("tiles/tile_" + key.Replace("_b", "_a"));
            var mesh = new Mesh();
            mesh.SetVertices(verts[key]); mesh.SetUVs(0, uvs[key]); mesh.SetTriangles(tris[key], 0);
            mesh.RecalculateNormals(); mesh.RecalculateBounds();
            var go = new GameObject("Tiles_" + key + "_" + rowFrom);
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

    /// <summary>
    /// 마을이 아닌 구역의 땅을 한 번에 깐다(타일 종류별 메시 하나씩). 소품은 BuildZoneProp 으로 프레임마다 조금씩 세운다.
    /// 그림 타일이 없으면 구역 크기의 단색 판 하나로 대신한다.
    /// </summary>
    public static GameObject BuildZoneGround(ZoneDef z, Transform parent)
    {
        var root = new GameObject("Zone_" + z.Id);
        root.transform.SetParent(parent, false);
        if (!GroundArtAvailable())
        {
            var floor = GameObject.CreatePrimitive(PrimitiveType.Cube);
            Object.Destroy(floor.GetComponent<Collider>());
            floor.name = "ZoneFloor"; floor.transform.SetParent(root.transform, false);
            floor.transform.position = new Vector3((z.MinX + z.MaxX) * 0.5f, -0.02f, (z.MinZ + z.MaxZ) * 0.5f);
            floor.transform.localScale = new Vector3(z.MaxX - z.MinX, 0.04f, z.MaxZ - z.MinZ);
            floor.GetComponent<Renderer>().sharedMaterial = U.Matte(VillageGround);
        }
        return root;
    }

    /// <summary>구역 땅의 일부(rowFrom 줄 ~ rowTo 줄)를 깐다. 한 프레임에 조금씩 부르려고 나눴다(경계에서 프레임이 튀는 것 방지)</summary>
    public static void BuildZoneGroundRows(ZoneDef z, GameObject root, int rowFrom, int rowTo)
    {
        BuildGroundTiles(root, z.Ground, z.MinX, z.MinZ, rowFrom, rowTo);
    }

    /// <summary>구역 소품 하나를 세운다 (그림이 없으면 색 도형)</summary>
    public static void BuildZoneProp(GameObject root, ZoneProp p)
    {
        float widthM = p.W * Balance.MAP_CELL_SIZE * 1.1f + 0.8f;
        if (!SpriteProp(root, p.Sprite, new Vector3(p.X, 0, p.Z), widthM)) FallbackShape(root, p.Sprite, p.X, p.Z, widthM);
    }

    /// <summary>그림 소품을 세운다. 그림이 있으면 true. widthM = 그려질 폭(m)</summary>
    static bool SpriteProp(GameObject root, string name, Vector3 pos, float widthM)
    {
        var s = SpriteLib.Get(name);
        if (s == null) return false;
        var a = ActorSprite.Create(root.transform, null);
        a.transform.position = pos + Vector3.up * ActorSprite.Lift;
        a.Show(name, Vector3.right);
        float natural = s.rect.width / s.pixelsPerUnit;               // 그림 원래 폭(m)
        a.transform.localScale = Vector3.one * (widthM / Mathf.Max(0.1f, natural));
        return true;
    }

    /// <summary>그림이 없을 때 소품 자리를 색 도형으로 대신 보여 준다 (충돌과 모양이 어긋나지 않게)</summary>
    static void FallbackShape(GameObject root, string sprite, float x, float z, float widthM)
    {
        if (sprite.EndsWith("seonang_tree"))
        {
            Prim(PrimitiveType.Cylinder, root, "Tree", new Vector3(x, 1.4f, z), new Vector3(0.7f, 1.4f, 0.7f), new Color(0.25f, 0.18f, 0.12f));
            Prim(PrimitiveType.Sphere, root, "Leaves", new Vector3(x, 3.4f, z), new Vector3(3.4f, 2.4f, 3.4f), new Color(0.18f, 0.30f, 0.22f));
        }
        else if (sprite.EndsWith("choga") || sprite.EndsWith("giwa"))
        {
            Prim(PrimitiveType.Cube, root, "House", new Vector3(x, 1.1f, z), new Vector3(widthM * 0.7f, 2.2f, widthM * 0.7f), HouseWall);
            Prim(PrimitiveType.Cube, root, "Roof", new Vector3(x, 2.45f, z), new Vector3(widthM * 0.9f, 0.5f, widthM * 0.9f), HouseRoof);
        }
        else if (sprite.EndsWith("jangseung"))
        {
            Prim(PrimitiveType.Cube, root, "Post", new Vector3(x, 1.2f, z), new Vector3(0.6f, 2.4f, 0.6f), new Color(0.35f, 0.24f, 0.15f));
            Prim(PrimitiveType.Cube, root, "PostHead", new Vector3(x, 2.6f, z), new Vector3(0.8f, 0.7f, 0.8f), ChasaPalette.ChasaRed);
        }
        else Prim(PrimitiveType.Sphere, root, "Stones", new Vector3(x, 0.4f, z), new Vector3(0.9f, 0.8f, 0.9f), new Color(0.42f, 0.42f, 0.44f));
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
}
