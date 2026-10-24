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

    public static void Build(Transform parent)
    {
        var root = new GameObject("Solgogae");
        root.transform.SetParent(parent, false);

        // 흙길: 서낭당에서 동쪽 마을 어귀까지 (z=0 따라 납작한 판)
        Flat(root, "Road", new Vector3(14f, 0.012f, 0f), new Vector3(30f, 0.01f, 3.2f), RoadColor);
        // 서낭당 마당: 귀환 반경 안쪽을 조금 밝게
        var yard = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        Object.Destroy(yard.GetComponent<Collider>());
        yard.name = "ShrineYard"; yard.transform.SetParent(root.transform, false);
        yard.transform.position = new Vector3(0, 0.011f, 0);
        yard.transform.localScale = new Vector3(Balance.SHRINE_RADIUS * 2.4f, 0.01f, Balance.SHRINE_RADIUS * 2.4f);
        yard.GetComponent<Renderer>().sharedMaterial = U.Matte(VillageGround);

        // 서낭나무: 몸통(충돌 없음 — 출발점이 막히면 안 되어서)과 둥근 잎
        Prim(PrimitiveType.Cylinder, root, "ShrineTree", new Vector3(0, 1.4f, 0), new Vector3(0.7f, 1.4f, 0.7f), new Color(0.25f, 0.18f, 0.12f));
        Prim(PrimitiveType.Sphere, root, "ShrineLeaves", new Vector3(0, 3.4f, 0), new Vector3(3.4f, 2.4f, 3.4f), new Color(0.18f, 0.30f, 0.22f));

        foreach (var b in MapLayout.Blockers)
        {
            switch (b.Kind)
            {
                case "house":
                    Prim(PrimitiveType.Cube, root, "House", new Vector3(b.X, 1.1f, b.Z), new Vector3(b.R * 1.7f, 2.2f, b.R * 1.7f), HouseWall);
                    Prim(PrimitiveType.Cube, root, "Roof", new Vector3(b.X, 2.45f, b.Z), new Vector3(b.R * 2.3f, 0.5f, b.R * 2.3f), HouseRoof);
                    break;
                case "post":   // 장승: 길쭉한 나무 기둥 + 붉은 머리 (ChasaRed 로 눈에 띄게)
                    Prim(PrimitiveType.Cube, root, "Post", new Vector3(b.X, 1.2f, b.Z), new Vector3(b.R * 1.6f, 2.4f, b.R * 1.6f), new Color(0.35f, 0.24f, 0.15f));
                    Prim(PrimitiveType.Cube, root, "PostHead", new Vector3(b.X, 2.6f, b.Z), new Vector3(b.R * 2.2f, 0.7f, b.R * 2.2f), ChasaPalette.ChasaRed);
                    break;
                default:       // 돌무더기
                    Prim(PrimitiveType.Sphere, root, "Stones", new Vector3(b.X, b.R * 0.5f, b.Z), new Vector3(b.R * 2f, b.R, b.R * 2f), new Color(0.42f, 0.42f, 0.44f));
                    break;
            }
        }
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
