// =============================================================================
// Props3D.cs — 새 화면(?v=3d)의 3D 소품 대역: 초가·기와집·돌담·장독·나무·장승·우물 등을 도형으로 세운다.
// 왜 도형인가? 외부 3D 파일을 들이려면 가져오기·라이선스 작업이 필요하다. 도형은 파일 없이 바로 빌드에 들어가고
//   (조명·그림자를 그대로 받는다) 아트팀 모델이 오면 같은 자리(좌표·충돌 반지름)에 바꿔 끼우면 된다.
// 크기는 충돌(Core/MapLayout)과 맞춘다: 집은 widthM 정도의 발자국, 장승은 반지름 0.4m.
// =============================================================================
using UnityEngine;

public static class Props3D
{
    static readonly Color Wall = new Color(0.34f, 0.28f, 0.22f);
    static readonly Color Thatch = new Color(0.30f, 0.26f, 0.15f);     // 초가 지붕(짚색)
    static readonly Color Tile = new Color(0.13f, 0.14f, 0.18f);       // 기와
    static readonly Color Wood = new Color(0.30f, 0.20f, 0.12f);
    static readonly Color Stone = new Color(0.40f, 0.40f, 0.42f);
    static readonly Color Leaf = new Color(0.12f, 0.24f, 0.17f);

    static GameObject Prim(PrimitiveType t, Transform parent, string name, Vector3 pos, Vector3 scale, Color c, Vector3? euler = null)
    {
        var g = GameObject.CreatePrimitive(t);
        Object.Destroy(g.GetComponent<Collider>());   // 충돌은 Core 가 계산한다
        g.name = name; g.transform.SetParent(parent, false);
        g.transform.localPosition = pos; g.transform.localScale = scale;
        if (euler.HasValue) g.transform.localEulerAngles = euler.Value;
        g.GetComponent<Renderer>().sharedMaterial = U.Matte(c);
        return g;
    }

    /// <summary>네 면이 모이는 뾰족 지붕 메시(밑면 w×d, 높이 h). 면마다 꼭짓점을 따로 둬서 각진 그림자가 선명하다</summary>
    static GameObject Roof(Transform parent, Vector3 pos, float w, float d, float h, float overhang, Color c)
    {
        float hw = w * 0.5f + overhang, hd = d * 0.5f + overhang;
        var a = new Vector3(-hw, 0, -hd); var b = new Vector3(hw, 0, -hd); var cc = new Vector3(hw, 0, hd); var dd = new Vector3(-hw, 0, hd);
        var top = new Vector3(0, h, 0);
        var verts = new[] { a, top, b, b, top, cc, cc, top, dd, dd, top, a };   // 시계 방향 = 바깥이 앞면
        var tris = new[] { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 };
        var m = new Mesh { vertices = verts, triangles = tris };
        m.RecalculateNormals(); m.RecalculateBounds();
        var g = new GameObject("Roof"); g.transform.SetParent(parent, false); g.transform.localPosition = pos;
        g.AddComponent<MeshFilter>().sharedMesh = m;
        var r = g.AddComponent<MeshRenderer>(); r.sharedMaterial = U.Matte(c);
        return g;
    }

    /// <summary>소품 하나를 (x,z) 에 세운다. sprite = 배치표 그림 이름, widthM = 발자국 폭(m)</summary>
    public static void Build(GameObject rootGo, string sprite, float x, float z, float widthM)
    {
        var g = new GameObject("P3D_" + sprite.Substring(sprite.LastIndexOf('/') + 1));
        g.transform.SetParent(rootGo.transform, false);
        g.transform.position = new Vector3(x, 0, z);
        g.transform.rotation = Quaternion.Euler(0, 45f, 0);   // 쿼터뷰와 같은 방향으로 놓아 정면이 화면 아래쪽을 본다
        var t = g.transform;
        float w = widthM;

        // 모델 슬롯: models.json 의 props 줄에 이 소품이 있으면 그 모델을 세운다 (없으면 아래 도형 대역)
        var row = ModelCatalog.Prop(sprite);
        if (row != null)
        {
            var prefab = Resources.Load<GameObject>(row.path);
            if (prefab != null)
            {
                var inst = Object.Instantiate(prefab, t);
                inst.transform.localPosition = Vector3.zero; inst.transform.localScale = Vector3.one * row.scale;
                var tex = string.IsNullOrEmpty(row.texture) ? null : Resources.Load<Texture2D>(row.texture);
                foreach (var r in inst.GetComponentsInChildren<Renderer>())
                {
                    var m = U.Matte(Color.white); if (tex != null) m.mainTexture = tex;
                    r.sharedMaterial = m;
                }
                return;
            }
        }

        if (sprite.EndsWith("seonang_tree"))
        {
            // 서낭나무: 굵은 줄기 + 겹친 잎덩이 + 금줄(붉은 띠)
            Prim(PrimitiveType.Cylinder, t, "Trunk", new Vector3(0, 1.8f, 0), new Vector3(0.9f, 1.8f, 0.9f), new Color(0.22f, 0.16f, 0.11f));
            Prim(PrimitiveType.Sphere, t, "Crown1", new Vector3(0, 4.3f, 0), new Vector3(4.2f, 3.0f, 4.2f), Leaf);
            Prim(PrimitiveType.Sphere, t, "Crown2", new Vector3(1.2f, 3.6f, 0.8f), new Vector3(2.8f, 2.2f, 2.8f), Leaf * 1.15f);
            Prim(PrimitiveType.Sphere, t, "Crown3", new Vector3(-1.1f, 3.9f, -0.7f), new Vector3(2.6f, 2.1f, 2.6f), Leaf * 0.9f);
            Prim(PrimitiveType.Cylinder, t, "Rope", new Vector3(0, 1.3f, 0), new Vector3(1.02f, 0.06f, 1.02f), new Color(0.65f, 0.12f, 0.12f));
        }
        else if (sprite.EndsWith("choga") || sprite.EndsWith("giwa"))
        {
            bool giwa = sprite.EndsWith("giwa");
            float bw = w * 0.78f, bd = w * (giwa ? 0.6f : 0.7f), wh = giwa ? 2.4f : 1.9f;
            Prim(PrimitiveType.Cube, t, "Wall", new Vector3(0, wh * 0.5f, 0), new Vector3(bw, wh, bd), giwa ? new Color(0.62f, 0.58f, 0.5f) : Wall);
            Prim(PrimitiveType.Cube, t, "Base", new Vector3(0, 0.15f, 0), new Vector3(bw + 0.3f, 0.3f, bd + 0.3f), Stone);
            Prim(PrimitiveType.Cube, t, "Door", new Vector3(0, 0.95f, -bd * 0.5f - 0.02f), new Vector3(bw * 0.28f, 1.5f, 0.06f), new Color(0.78f, 0.7f, 0.55f));
            Roof(t, new Vector3(0, wh, 0), bw, bd, giwa ? 1.5f : 1.9f, 0.55f, giwa ? Tile : Thatch);
        }
        else if (sprite.EndsWith("jangseung"))
        {
            // 장승: 굵은 기둥 + 사람 얼굴 모양 윗부분(눈·코)
            Prim(PrimitiveType.Cylinder, t, "Post", new Vector3(0, 1.4f, 0), new Vector3(0.5f, 1.4f, 0.5f), Wood);
            Prim(PrimitiveType.Cube, t, "Face", new Vector3(0, 2.7f, 0), new Vector3(0.75f, 0.8f, 0.6f), new Color(0.38f, 0.26f, 0.16f));
            Prim(PrimitiveType.Cube, t, "EyeL", new Vector3(-0.17f, 2.82f, -0.31f), new Vector3(0.14f, 0.1f, 0.04f), new Color(0.05f, 0.04f, 0.04f));
            Prim(PrimitiveType.Cube, t, "EyeR", new Vector3(0.17f, 2.82f, -0.31f), new Vector3(0.14f, 0.1f, 0.04f), new Color(0.05f, 0.04f, 0.04f));
            Prim(PrimitiveType.Cube, t, "Hat", new Vector3(0, 3.18f, 0), new Vector3(0.9f, 0.16f, 0.7f), ChasaPalette.ChasaRed);
        }
        else if (sprite.EndsWith("jars"))
        {
            for (int i = 0; i < 3; i++)
            {
                float ox = (i - 1) * 0.55f, s = i == 1 ? 1.15f : 0.9f;
                Prim(PrimitiveType.Sphere, t, "Jar", new Vector3(ox, 0.5f * s, i == 1 ? 0.25f : -0.1f), new Vector3(0.8f * s, 0.95f * s, 0.8f * s), new Color(0.32f, 0.22f, 0.15f));
                Prim(PrimitiveType.Cylinder, t, "Neck", new Vector3(ox, 1.0f * s, i == 1 ? 0.25f : -0.1f), new Vector3(0.38f * s, 0.07f * s, 0.38f * s), new Color(0.26f, 0.18f, 0.12f));
            }
        }
        else if (sprite.EndsWith("well"))
        {
            Prim(PrimitiveType.Cylinder, t, "Ring", new Vector3(0, 0.4f, 0), new Vector3(1.5f, 0.4f, 1.5f), Stone);
            Prim(PrimitiveType.Cylinder, t, "Water", new Vector3(0, 0.72f, 0), new Vector3(1.1f, 0.02f, 1.1f), new Color(0.04f, 0.07f, 0.12f));
            Prim(PrimitiveType.Cube, t, "PostL", new Vector3(-0.8f, 1.3f, 0), new Vector3(0.12f, 1.8f, 0.12f), Wood);
            Prim(PrimitiveType.Cube, t, "PostR", new Vector3(0.8f, 1.3f, 0), new Vector3(0.12f, 1.8f, 0.12f), Wood);
            Prim(PrimitiveType.Cube, t, "Beam", new Vector3(0, 2.2f, 0), new Vector3(1.8f, 0.12f, 0.12f), Wood);
        }
        else if (sprite.EndsWith("stone_wall"))
        {
            int n = Mathf.Max(3, Mathf.RoundToInt(w / 0.55f));
            for (int i = 0; i < n; i++)
            {
                float ox = (i - (n - 1) * 0.5f) * 0.55f;
                Prim(PrimitiveType.Cube, t, "S", new Vector3(ox, 0.35f + (i % 2) * 0.05f, (i % 3 - 1) * 0.04f), new Vector3(0.6f, 0.7f + (i % 2) * 0.1f, 0.5f), Stone * (0.85f + 0.1f * (i % 3)));
            }
        }
        else if (sprite.EndsWith("sangyeo"))
        {
            Prim(PrimitiveType.Cube, t, "Bed", new Vector3(0, 0.8f, 0), new Vector3(w * 0.8f, 0.2f, 1.1f), Wood);
            Prim(PrimitiveType.Cube, t, "Box", new Vector3(0, 1.3f, 0), new Vector3(w * 0.6f, 0.8f, 0.8f), new Color(0.55f, 0.22f, 0.2f));
            Roof(t, new Vector3(0, 1.7f, 0), w * 0.6f, 0.8f, 0.7f, 0.25f, Tile);
            Prim(PrimitiveType.Cylinder, t, "PoleL", new Vector3(0, 0.6f, -0.6f), new Vector3(0.1f, w * 0.5f, 0.1f), Wood, new Vector3(0, 0, 90));
            Prim(PrimitiveType.Cylinder, t, "PoleR", new Vector3(0, 0.6f, 0.6f), new Vector3(0.1f, w * 0.5f, 0.1f), Wood, new Vector3(0, 0, 90));
        }
        else if (sprite.EndsWith("pyeongsang"))
        {
            Prim(PrimitiveType.Cube, t, "Top", new Vector3(0, 0.55f, 0), new Vector3(w * 0.85f, 0.14f, 1.3f), new Color(0.40f, 0.30f, 0.20f));
            for (int i = 0; i < 4; i++) Prim(PrimitiveType.Cube, t, "Leg", new Vector3((i % 2 - 0.5f) * w * 0.75f, 0.27f, (i / 2 - 0.5f) * 1.0f), new Vector3(0.12f, 0.55f, 0.12f), Wood);
        }
        else if (sprite.EndsWith("jigae"))
        {
            Prim(PrimitiveType.Cube, t, "FrameL", new Vector3(-0.3f, 0.7f, 0), new Vector3(0.08f, 1.5f, 0.08f), Wood, new Vector3(0, 0, 12));
            Prim(PrimitiveType.Cube, t, "FrameR", new Vector3(0.3f, 0.7f, 0), new Vector3(0.08f, 1.5f, 0.08f), Wood, new Vector3(0, 0, -12));
            Prim(PrimitiveType.Cube, t, "Rack", new Vector3(0, 0.55f, 0), new Vector3(0.7f, 0.5f, 0.45f), new Color(0.35f, 0.26f, 0.16f));
        }
        else if (sprite.EndsWith("sotdae"))
        {
            Prim(PrimitiveType.Cylinder, t, "Pole", new Vector3(0, 2.0f, 0), new Vector3(0.14f, 2.0f, 0.14f), Wood);
            Prim(PrimitiveType.Sphere, t, "Bird", new Vector3(0, 4.15f, 0), new Vector3(0.45f, 0.4f, 0.55f), new Color(0.12f, 0.12f, 0.14f));
        }
        else if (sprite.EndsWith("cairn"))
        {
            Prim(PrimitiveType.Sphere, t, "S1", new Vector3(0, 0.3f, 0), new Vector3(1.0f, 0.6f, 0.9f), Stone);
            Prim(PrimitiveType.Sphere, t, "S2", new Vector3(0.05f, 0.75f, 0), new Vector3(0.7f, 0.5f, 0.65f), Stone * 1.1f);
            Prim(PrimitiveType.Sphere, t, "S3", new Vector3(-0.03f, 1.1f, 0), new Vector3(0.4f, 0.35f, 0.4f), Stone * 0.9f);
        }
        else Prim(PrimitiveType.Sphere, t, "Stones", new Vector3(0, 0.4f, 0), new Vector3(0.9f, 0.8f, 0.9f), Stone);

        // 지붕 있는 큰 물체는 그림자를 만들고 받는다 (프리미티브 기본값). 소품은 정적이라 움직이지 않는다.
        g.isStatic = false;
    }
}
