// =============================================================================
// Atmosphere.cs — 밤의 어둠과 등불. "어두운 밤에 불빛이 번지는" 분위기를 만든다.
//
// 왜 유니티 조명(Light)을 안 쓰나?
//   이 게임의 그림(스프라이트)은 빛을 받지 않는 재질(Sprites/Default)이라 Light 를 켜도 안 변한다.
//   재질을 바꾸려면 PC 에디터 작업이 필요하다. 그래서 "화면 위에 반투명 어둠 막"을 덮고,
//   불빛이 있는 자리만 막을 얇게 만드는 방식으로 같은 효과를 낸다. (파일만 고쳐서 개발하는 원칙)
//
// 어떻게 그리나?
//   1) 화면을 아주 작은 격자(80×45칸)로 본다. 칸마다 "얼마나 어두운가(알파)"를 계산해 작은 그림 한 장에 담는다.
//   2) 그 그림을 화면 전체로 늘려 그린다. 늘릴 때 부드럽게 번지므로(쌍선형 보간) 빛이 자연스럽게 퍼진다.
//   3) 불빛마다 타원 모양(쿼터뷰라 세로로 납작)으로 어둠을 걷어 낸다.
// =============================================================================
using UnityEngine;
using Chasa.Core;

public class Atmosphere : MonoBehaviour
{
    public Camera cam;
    public JudgeSystem judge;
    public Player player;
    public EnemyManager enemies;

    const int W = 80, H = 45;                 // 어둠 격자 크기(작을수록 가볍고 번짐이 부드럽다)
    const float BASE_DARK = 0.58f;            // 빛이 없는 곳의 어둠 (0=밝음, 1=칠흑)
    static readonly Color32 DARK_TINT = new Color32(10, 14, 38, 255);   // 어둠의 색: 푸른 남색(차가운 밤)

    // 불빛 하나: 월드 위치, 반지름(화면 세로 대비 비율), 세기, 깜빡임 정도
    struct Lamp { public Vector3 pos; public float radius, power, flicker; }

    Texture2D mask;
    Color32[] px;
    Lamp[] fixedLamps;                         // 마을 등불(움직이지 않음)
    float t;
    bool on = true;

    void Start()
    {
        mask = new Texture2D(W, H, TextureFormat.RGBA32, false);
        mask.filterMode = FilterMode.Bilinear;   // 칸 사이를 부드럽게 이어 빛이 번지게 한다
        mask.wrapMode = TextureWrapMode.Clamp;
        px = new Color32[W * H];
        BuildFixedLamps();
    }

    /// <summary>마을 소품에서 등불 자리를 뽑는다: 초가·기와집은 창가 등불, 장승·서낭나무는 약한 불빛</summary>
    void BuildFixedLamps()
    {
        var list = new System.Collections.Generic.List<Lamp>();
        foreach (var p in MapData.Props)
        {
            // 칸 좌표 → 월드 좌표 (Blocker 만들 때와 같은 규칙)
            var pos = new Vector3(MapLayout.WorldX(p.Ay), 1.2f, MapLayout.WorldZ(p.Ax));
            if (p.Sprite.EndsWith("choga") || p.Sprite.EndsWith("giwa"))
                list.Add(new Lamp { pos = pos, radius = 0.16f, power = 0.85f, flicker = 0.12f });
            else if (p.Sprite.EndsWith("jangseung"))
                list.Add(new Lamp { pos = pos, radius = 0.10f, power = 0.55f, flicker = 0.08f });
            else if (p.Sprite.EndsWith("seonang_tree"))
                // 서낭나무 = 출발점의 성소: 크고 따뜻하고 천천히 숨 쉬듯 깜빡인다
                list.Add(new Lamp { pos = pos, radius = 0.30f, power = 1.0f, flicker = 0.18f });
            else if (p.Sprite.EndsWith("well") || p.Sprite.EndsWith("sotdae"))
                list.Add(new Lamp { pos = pos, radius = 0.09f, power = 0.4f, flicker = 0.05f });
        }
        fixedLamps = list.ToArray();
    }

    void Update() { t += Time.unscaledDeltaTime; if (Input.GetKeyDown(KeyCode.L)) on = !on; }   // L 키: 어둠 켜기/끄기(비교용)

    void OnGUI()
    {
        if (!on || cam == null || mask == null) return;
        if (Event.current.type != EventType.Repaint) return;
        if (judge != null && (judge.InDay || CharacterPanel.Open || SettingsPanel.Open)) return;
        GUI.depth = 50;   // 숫자·HUD(작은 depth)보다 뒤, 월드보다 앞

        float cast = judge != null ? judge.CastZoom : 0f;   // 천도 캐스팅 중 0→1 (시야가 좁아지는 정도)
        Fill(cast);
        mask.SetPixels32(px);
        mask.Apply(false);
        GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), mask, ScaleMode.StretchToFill);
    }

    /// <summary>격자 칸마다 어둠 알파를 계산한다</summary>
    void Fill(float cast)
    {
        // 어둠 알파 배열(0~1). 처음엔 전부 BASE_DARK, 불빛마다 깎는다.
        for (int i = 0; i < px.Length; i++) px[i] = new Color32(DARK_TINT.r, DARK_TINT.g, DARK_TINT.b, 0);
        float[] a = alpha ?? (alpha = new float[W * H]);
        // 천도 캐스팅 중엔 주변이 더 어두워진다 = 집중하는 느낌 (시야 축소와 짝)
        float dark = Mathf.Lerp(BASE_DARK, 0.74f, cast);
        for (int i = 0; i < a.Length; i++) a[i] = dark;

        foreach (var l in fixedLamps)
            Carve(a, l.pos, l.radius, l.power * (1f + l.flicker * Mathf.Sin(t * 5f + l.pos.x * 3.1f) * 0.5f
                                                   + l.flicker * 0.5f * Mathf.Sin(t * 11.3f + l.pos.z)), 0f);

        if (player != null)
        {
            // 플레이어 등불: 평소 넓고 따뜻함, 캐스팅 중엔 좁아지며 보랏빛 느낌(색은 아래에서 따로)
            float r = Mathf.Lerp(0.26f, 0.15f, cast);
            Carve(a, player.Pos + Vector3.up * 0.8f, r, 0.95f, 0f);
        }

        if (enemies != null)
            foreach (var e in enemies.list)
            {
                if (e == null) continue;
                if (e.soul.Boss) Carve(a, e.Pos + Vector3.up * 1.2f, 0.20f, 0.7f, 0f);   // 보스는 자기 빛을 두른다
                else if (e.soul.State == SoulState.Kneel || e.soul.State == SoulState.Sending)
                    Carve(a, e.Pos + Vector3.up * 0.8f, 0.10f, 0.6f, 0f);               // 무릎 꿇은 넋은 푸른 불빛
            }

        // 알파를 색 격자에 옮긴다. 캐스팅 중엔 어둠이 보랏빛으로 기운다
        byte tr = (byte)Mathf.Lerp(DARK_TINT.r, 40, cast), tb = (byte)Mathf.Lerp(DARK_TINT.b, 70, cast);
        for (int i = 0; i < px.Length; i++)
            px[i] = new Color32(tr, DARK_TINT.g, tb, (byte)(Mathf.Clamp01(a[i]) * 255f));
    }
    float[] alpha;

    /// <summary>월드의 한 점에 불빛을 놓아 주변 어둠을 걷어 낸다 (타원 감쇠 (1-d²)²)</summary>
    void Carve(float[] a, Vector3 world, float radius, float power, float unused)
    {
        Vector3 sp = cam.WorldToViewportPoint(world);   // 0~1 화면 좌표
        if (sp.z <= 0f) return;
        float cx = sp.x * W, cy = sp.y * H;
        float rx = radius * H * 1.0f * (16f / 9f) * 0.5f + 1f;   // 가로 반지름(칸)
        float ry = radius * H * 0.62f + 1f;                       // 세로는 납작하게(쿼터뷰 바닥 느낌)
        int x0 = Mathf.Max(0, (int)(cx - rx)), x1 = Mathf.Min(W - 1, (int)(cx + rx));
        int y0 = Mathf.Max(0, (int)(cy - ry)), y1 = Mathf.Min(H - 1, (int)(cy + ry));
        for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++)
            {
                float dx = (x - cx) / rx, dy = (y - cy) / ry;
                float d2 = dx * dx + dy * dy;
                if (d2 >= 1f) continue;
                float f = (1f - d2); f *= f;               // 중심이 가장 밝고 가장자리는 서서히 사라진다
                int i = (H - 1 - y) * W + x;               // 텍스처는 위가 0줄이 아니라 아래가 0줄: 뒤집어 넣는다
                // 이미 밝은 곳(다른 불빛)과 겹치면 더 밝아지되 0 밑으론 안 간다
                a[i] = Mathf.Max(0f, a[i] - f * power * BASE_DARK);
            }
    }
}
