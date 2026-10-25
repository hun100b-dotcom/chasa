// =============================================================================
// HeroRing.cs — 주인공 발밑의 옅은 청록 고리 (아트 검수 P2: 검은 도포가 어두운 땅에 묻힌다)
// 왜 고리? 윤곽선을 따로 그리는 것보다 가볍고, 어두운 땅에서도 주인공 자리를 한눈에 알려 준다. 지름 2m·알파 25%.
// 그림 파일 없이 코드로 부드러운 고리 그림을 만든다(아트가 전용 고리 그림을 주면 Resources/Sprites/fx/hero_ring 으로 바꾼다).
// =============================================================================
using UnityEngine;

public class HeroRing : MonoBehaviour
{
    public Player player;
    Transform quad; Material mat;
    const float Diameter = 2.0f;

    void Start()
    {
        var tex = new Texture2D(64, 64, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
        for (int y = 0; y < 64; y++) for (int x = 0; x < 64; x++)
        {
            float d = Vector2.Distance(new Vector2(x, y), new Vector2(31.5f, 31.5f)) / 31.5f;   // 0 중심 ~ 1 가장자리
            float ring = Mathf.Clamp01(1f - Mathf.Abs(d - 0.86f) / 0.12f);   // 가장자리 안쪽의 가는 띠
            float glow = Mathf.Clamp01(1f - d) * 0.25f;                      // 안쪽은 아주 옅게
            tex.SetPixel(x, y, new Color(0.37f, 0.89f, 0.75f, Mathf.Clamp01(ring * 0.9f + glow) * (d <= 1f ? 1f : 0f)));
        }
        tex.Apply();
        var sh = Shader.Find("Sprites/Default");
        if (sh == null) { enabled = false; return; }
        mat = new Material(sh) { mainTexture = tex, color = new Color(1, 1, 1, 0.25f) };   // 전체 알파 25%
        var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
        Destroy(go.GetComponent<Collider>());
        go.name = "HeroRing"; go.GetComponent<Renderer>().sharedMaterial = mat;
        go.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        quad = go.transform; quad.SetParent(transform, false);
        quad.localScale = new Vector3(Diameter, Diameter, 1f); quad.rotation = Quaternion.Euler(90f, 0f, 0f);   // 바닥에 눕힘
    }

    void LateUpdate()
    {
        if (quad == null || player == null) return;
        quad.position = new Vector3(player.Pos.x, player.Pos.y + 0.06f, player.Pos.z);
        quad.gameObject.SetActive(ActorModel.HeroShadowOn);   // 낮엔 주인공이 산 사람에게 안 보인다 — 그때는 고리도 끈다
    }
}
