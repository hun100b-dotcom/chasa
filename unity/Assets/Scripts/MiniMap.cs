// =============================================================================
// MiniMap.cs — 필드 지도. 오른쪽 위 '작은 지도'(내 둘레 70m, 카메라 방향이 위) + M 키 '큰 지도'(필드 전체, 북쪽이 위).
//   바탕 그림은 게임을 시작할 때 땅 데이터(높이·재질·물)와 배치표(길·집·서낭당)에서 한 번 그려 둔다(2m = 1픽셀, 320×320).
//   표시: 지형 음영·물·길·집, 서낭당·다리·나루터·의원집·마을 표식, 혼(싸우는 혼=붉은 점·무릎 꿇은 혼=금색·덩어리=보라), 보스(붉은 마름모),
//        켜진 단서 자리(금색 느낌표), 이름혼(청록), 내 자리와 방향(흰 화살표), 구역 이름.
//   그리는 방법은 IMGUI(OnGUI). 판정·게임 규칙은 건드리지 않는다.
// =============================================================================
using System;
using System.Collections;
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class MiniMap : MonoBehaviour
{
    public JudgeSystem judge; public Player player; public Camera cam;
    public static bool BigOpen;
    public static float BottomPx = 150f;   // 작은 지도 + 지역 이름 줄의 아래 끝(화면 px, 위가 0). UiRoot 가 시계 고리를 이 아래에 둔다

    const int Px = 320;                 // 바탕 그림 한 변(픽셀)
    const float WorldM = 640f;          // 필드 한 변(m)
    const float M2P = Px / WorldM;      // 1m 당 픽셀
    const float MiniRadiusM = 40f;      // 작은 지도가 보여 주는 반지름(m). 기획 표준 반경 40m(지름 80m)
    Texture2D baseTex, white, dot; bool ready;
    [Serializable] class Item { public string n; public float x, z; public int t; }
    [Serializable] class Mark { public string kind, name; public float x, z; }
    [Serializable] class FieldFile { public Item[] items; public Mark[] markers; }
    readonly List<Mark> marks = new List<Mark>();
    readonly List<KeyValuePair<string, Rect>> zones = new List<KeyValuePair<string, Rect>>();
    GUIStyle label, small, title;
    readonly List<KeyValuePair<Vector3, string>> tmp = new List<KeyValuePair<Vector3, string>>();

    void Start()
    {
        white = Texture2D.whiteTexture;
        dot = new Texture2D(32, 32, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear };   // 속이 찬 동그라미
        for (int y = 0; y < 32; y++) for (int x = 0; x < 32; x++) dot.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(16f - Vector2.Distance(new Vector2(x, y), new Vector2(15.5f, 15.5f)))));
        dot.Apply();
        StartCoroutine(Bake());
    }

    // ---- 바탕 그림 굽기(여러 프레임에 나눠서) ------------------------------------------
    IEnumerator Bake()
    {
        var ta = Resources.Load<TextAsset>("Data/field");
        FieldFile f = null; if (ta != null) { try { f = JsonUtility.FromJson<FieldFile>(ta.text); } catch { } }
        zones.AddRange(FieldZones.Labels());
        if (f != null && f.markers != null) marks.AddRange(f.markers);
        var px = new Color32[Px * Px];
        var w = new float[SplatField.Layers];
        // 층 색(흙·풀·자갈·논·낙엽): 지도 읽기 좋게 채도 낮춘 먹빛 팔레트
        Color[] lc = { new Color(0.55f, 0.45f, 0.32f), new Color(0.30f, 0.38f, 0.28f), new Color(0.52f, 0.52f, 0.50f), new Color(0.50f, 0.50f, 0.30f), new Color(0.42f, 0.30f, 0.22f) };
        int rowsPerFrame = 40;
        for (int y = 0; y < Px; y++)
        {
            for (int x = 0; x < Px; x++)
            {
                float wx = (x + 0.5f) / M2P, wz = (y + 0.5f) / M2P;
                float h = GroundTerrain.HeightAt(wx, wz);
                Color c;
                if (!GroundTerrain.Active) c = new Color(0.30f, 0.38f, 0.28f);
                else
                {
                    GroundTerrain.LayerWeights(wx, wz, w);
                    c = Color.black; float sum = 0f;
                    for (int l = 0; l < w.Length; l++) { c += lc[Mathf.Min(l, lc.Length - 1)] * w[l]; sum += w[l]; }
                    c = sum > 0.001f ? c / sum : lc[1];
                    // 음영: 북서쪽에서 비추는 것처럼 높이 차이로 입체감
                    float hx = GroundTerrain.HeightAt(wx + 2f, wz) - GroundTerrain.HeightAt(wx - 2f, wz), hz = GroundTerrain.HeightAt(wx, wz + 2f) - GroundTerrain.HeightAt(wx, wz - 2f);
                    float shade = Mathf.Clamp(1f + (hx - hz) * 0.35f, 0.6f, 1.4f);
                    c *= shade;
                    if (h < 0.18f) c = Color.Lerp(new Color(0.17f, 0.30f, 0.45f), new Color(0.10f, 0.18f, 0.32f), Mathf.Clamp01((0.18f - h) / 0.5f));   // 물: 깊을수록 짙게
                    else if (h < 0.3f) c = Color.Lerp(c, new Color(0.45f, 0.5f, 0.5f), 0.35f);   // 물가
                }
                c.a = 1f; px[y * Px + x] = c;
            }
            if (y % rowsPerFrame == rowsPerFrame - 1) yield return null;
        }
        // 길·집·다리 덮기
        if (f != null && f.items != null)
            foreach (var it in f.items)
            {
                if (it.n.StartsWith("terrain_tile_road")) Fill(px, it.x, it.z, 8f, 8f, new Color32(214, 190, 140, 255));
                else if (it.n.StartsWith("hanok_gidan")) Fill(px, it.x, it.z, 4f, 4f, new Color32(70, 52, 44, 255));
                else if (it.n.StartsWith("hanok_choga_roof") || it.n.StartsWith("hanok_giwa_roof")) Fill(px, it.x, it.z, 6f, 6f, new Color32(96, 70, 56, 255));
                else if (it.n == "br_stone_bridge") Fill(px, it.x, it.z, 8f, 6f, new Color32(190, 180, 160, 255));
            }
        baseTex = new Texture2D(Px, Px, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
        baseTex.SetPixels32(px); baseTex.Apply();
        ready = true;
    }

    static void Fill(Color32[] px, float wx, float wz, float w, float h, Color32 c)
    {
        int x0 = Mathf.Max(0, Mathf.FloorToInt((wx - w * 0.5f) * M2P)), x1 = Mathf.Min(Px - 1, Mathf.CeilToInt((wx + w * 0.5f) * M2P));
        int y0 = Mathf.Max(0, Mathf.FloorToInt((wz - h * 0.5f) * M2P)), y1 = Mathf.Min(Px - 1, Mathf.CeilToInt((wz + h * 0.5f) * M2P));
        for (int y = y0; y <= y1; y++) for (int x = x0; x <= x1; x++) px[y * Px + x] = c;
    }

    // ---- 입력 ------------------------------------------------------------------------
    void Update()
    {
        if (judge == null || judge.InDay || judge.NightOver) return;
        if (Input.GetKeyDown(KeyCode.M) && !CharacterPanel.Open && !SettingsPanel.Open) BigOpen = !BigOpen;
        if (BigOpen && Input.GetKeyDown(KeyCode.Escape)) BigOpen = false;
        if (BigOpen && judge.cuts.Active) BigOpen = false;
    }

    // ---- 그리기 ------------------------------------------------------------------------
    void Styles()
    {
        if (label != null) return;
        label = new GUIStyle(GUI.skin.label) { fontSize = 13, alignment = TextAnchor.MiddleCenter };
        small = new GUIStyle(label) { fontSize = 11 };
        title = new GUIStyle(label) { fontSize = 22 };
    }

    static void Box(Rect r, Color c) { var o = GUI.color; GUI.color = c; GUI.DrawTexture(r, Texture2D.whiteTexture); GUI.color = o; }
    static void Frame(Rect r, float t, Color c) { Box(new Rect(r.x, r.y, r.width, t), c); Box(new Rect(r.x, r.yMax - t, r.width, t), c); Box(new Rect(r.x, r.y, t, r.height), c); Box(new Rect(r.xMax - t, r.y, t, r.height), c); }

    void OnGUI()
    {
        if (judge == null || player == null || cam == null || judge.InDay || judge.NightOver || CharacterPanel.Open || SettingsPanel.Open) return;
        if (judge.cuts.Active && !BigOpen) return;
        Ko.Apply(); Styles();
        if (BigOpen) DrawBig(); else DrawMini();
    }

    float CamHeading() { var f = cam.transform.forward; f.y = 0f; if (f.sqrMagnitude < 1e-4f) return 0f; return Mathf.Atan2(f.x, f.z); }

    // 월드 오프셋 → 작은 지도 화면 오프셋(카메라 방향이 위): 반시계로 heading 만큼 돌린다
    static Vector2 Rot(float dx, float dz, float heading) { float c = Mathf.Cos(heading), s = Mathf.Sin(heading); return new Vector2(dx * c - dz * s, dx * s + dz * c); }

    void DrawMini()
    {
        // 기획 표준: 1080p 에서 260px(화면 높이의 24%), 우상 여백 24px. 폰은 200px 급(높이의 30%, 읽히는 하한 110px)
        float size = Ko.TouchUI ? Mathf.Clamp(Screen.height * 0.30f, 110f, 200f) : Mathf.Clamp(Screen.height * 0.24f, 150f, 300f);
        float margin = Mathf.Max(10f, 24f * Screen.height / 1080f);
        var r = new Rect(Screen.width - size - margin, margin, size, size);
        BottomPx = r.yMax + 4f + 28f;   // 지역 이름 줄까지 포함한 아래 끝(시계 고리가 그 밑에 놓인다)
        float scale = size / (MiniRadiusM * 2f);   // px/m
        float H = CamHeading();
        Box(new Rect(r.x - 4, r.y - 4, r.width + 8, r.height + 8), new Color(0.05f, 0.06f, 0.09f, 0.92f));
        if (ready)
        {
            GUI.BeginClip(r);
            var cen = new Vector2(size * 0.5f, size * 0.5f);
            var old = GUI.matrix;
            GUIUtility.RotateAroundPivot(-H * Mathf.Rad2Deg, cen);   // 카메라 앞이 위로 오게 지도를 반시계로 돌린다
            float full = WorldM * scale;
            // 텍스처 좌표(0=남서) → 지도 위 위치: 내 자리가 중앙. IMGUI 의 위쪽은 북(+z)
            float ox = cen.x - player.Pos.x * scale, oy = cen.y - (WorldM - player.Pos.z) * scale;
            GUI.DrawTexture(new Rect(ox, oy, full, full), baseTex);
            GUI.matrix = old;
            // 표식(회전을 직접 계산해 그려서 글자·점이 돌아가지 않게)
            DrawMarkers(r, cen, scale, H, size * 0.5f, false);
            // 북쪽 표시
            var n = Rot(0f, 1f, H); GUI.Label(new Rect(cen.x + n.x * (size * 0.5f - 12f) - 10f, cen.y - n.y * (size * 0.5f - 12f) - 9f, 20, 18), "북", small);
            GUI.EndClip();
        }
        else GUI.Label(r, "지도를 그리는 중…", small);
        Frame(r, 2f, new Color(0.83f, 0.66f, 0.31f, 1f));   // 단청 금빛 테두리
        Frame(new Rect(r.x - 4, r.y - 4, r.width + 8, r.height + 8), 1.5f, new Color(0.45f, 0.1f, 0.1f, 1f));
        string zn = FieldZones.CurrentName; if (string.IsNullOrEmpty(zn)) zn = "들길";
        GUI.Label(new Rect(r.x, r.yMax + 6f, r.width, 20f), zn + "   (M 큰 지도)", small);
    }

    void DrawBig()
    {
        float size = Mathf.Min(Screen.width - 80f, Screen.height - 120f);
        var r = new Rect((Screen.width - size) * 0.5f, 60f, size, size);
        Box(new Rect(0, 0, Screen.width, Screen.height), new Color(0, 0, 0, 0.7f));
        Box(new Rect(r.x - 6, r.y - 6, r.width + 12, r.height + 12), new Color(0.10f, 0.09f, 0.08f, 1f));
        float scale = size / WorldM;
        if (ready) GUI.DrawTexture(r, baseTex);
        // 구역 이름
        foreach (var z in zones)
        {
            var c = new Vector2((z.Value.xMin + z.Value.xMax) * 0.5f, (z.Value.yMin + z.Value.yMax) * 0.5f);
            var sp = new Vector2(r.x + c.x * scale, r.yMax - c.y * scale);
            Frame(new Rect(r.x + z.Value.xMin * scale, r.yMax - z.Value.yMax * scale, z.Value.width * scale, z.Value.height * scale), 1f, new Color(1, 1, 1, 0.18f));
            GUI.color = new Color(1f, 0.95f, 0.8f, 0.85f); GUI.Label(new Rect(sp.x - 70, sp.y - 12, 140, 24), z.Key, label); GUI.color = Color.white;
        }
        DrawMarkers(r, Vector2.zero, scale, 0f, 0f, true);
        Frame(r, 2f, new Color(0.83f, 0.66f, 0.31f, 1f));
        GUI.Label(new Rect(r.x, 14f, r.width, 36f), "필드 지도", title);
        GUI.Label(new Rect(r.x, r.yMax + 10f, r.width, 22f), "● 혼   붉은 네모 보스   ! 단서   흰 화살표 나   M·Esc 닫기", label);
    }

    // 큰 지도(big=true): 북쪽이 위, 화면 = r 안의 절대 좌표. 작은 지도: 중심(cen) 기준 회전 좌표, 지도 가장자리 밖 표식은 가장자리에 붙인다
    void DrawMarkers(Rect r, Vector2 cen, float scale, float H, float half, bool big)
    {
        Func<float, float, Vector2?> toScreen = (wx, wz) =>
        {
            if (big) return new Vector2(r.x + wx * scale, r.yMax - wz * scale);
            var o = Rot(wx - player.Pos.x, wz - player.Pos.z, H) * scale;
            return new Vector2(cen.x + o.x, cen.y - o.y);
        };
        Action<float, float, Color, float> D = (wx, wz, col, sz) =>
        {
            var p = toScreen(wx, wz); if (!p.HasValue) return;
            var v = p.Value; if (!big) { if (Mathf.Abs(v.x - cen.x) > half - 3f || Mathf.Abs(v.y - cen.y) > half - 3f) return; }
            var o = GUI.color; GUI.color = col; GUI.DrawTexture(new Rect(v.x - sz * 0.5f, v.y - sz * 0.5f, sz, sz), dot); GUI.color = o;
        };
        float s = big ? 7f : 6f;
        // 서낭당·다리·나루터·의원집·마을(고정 표식): 작은 네모 + 글자(큰 지도)
        foreach (var m in marks)
        {
            Color col = m.kind == "seonang" ? new Color(0.45f, 0.95f, 0.85f) : m.kind == "village" ? new Color(1f, 0.85f, 0.4f) : m.kind == "doctor" ? new Color(0.5f, 0.9f, 0.5f) : new Color(0.85f, 0.85f, 0.95f);
            var p = toScreen(m.x, m.z); if (!p.HasValue) continue;
            var v = p.Value; if (!big && (Mathf.Abs(v.x - cen.x) > half - 4f || Mathf.Abs(v.y - cen.y) > half - 4f)) continue;
            Box(new Rect(v.x - 5, v.y - 5, 10, 10), new Color(0.05f, 0.05f, 0.08f, 0.9f)); Box(new Rect(v.x - 3.5f, v.y - 3.5f, 7, 7), col);
            if (big) { var nm = m.name; int i = nm.IndexOf('('); if (i > 0) nm = nm.Substring(0, i); i = nm.IndexOf('·'); GUI.color = new Color(1, 1, 1, 0.9f); GUI.Label(new Rect(v.x - 80, v.y + 6, 160, 20), nm, small); GUI.color = Color.white; }
        }
        // 보스(붉은 마름모) — 아직 안 나타났어도 자리를 표시한다
        for (int id = 1; id <= Bosses.Count; id++) { var bd = Bosses.Get(id); D(bd.X, bd.Z, new Color(0.95f, 0.15f, 0.12f), s + 6f); }
        // 켜진 단서 자리
        if (judge.npcs != null) { tmp.Clear(); judge.npcs.PendingClues(tmp); foreach (var c in tmp) D(c.Key.x, c.Key.z, new Color(1f, 0.85f, 0.2f), s + 2f); }
        // 이름혼
        if (judge.named != null) { tmp.Clear(); judge.named.PendingPositions(tmp); foreach (var c in tmp) D(c.Key.x, c.Key.z, new Color(0.4f, 1f, 0.85f), s + 1f); }
        // 혼
        foreach (var e in judge.enemies.list)
        {
            if (e == null || e.gone) continue;
            if (e.soul.Boss) { D(e.Pos.x, e.Pos.z, new Color(1f, 0.3f, 0.25f), s + 6f); continue; }
            Color col = e.kneeling ? new Color(1f, 0.85f, 0.35f) : e.soul.Kind == SoulKind.Lump ? new Color(0.7f, 0.4f, 0.95f) : new Color(0.95f, 0.3f, 0.3f);
            if (!e.Targetable) continue;   // 땅속 혼은 지도에도 안 보인다
            D(e.Pos.x, e.Pos.z, col, s - 1f);
        }
        // 나: 흰 화살표(카메라 기준 방향)
        var me = toScreen(player.Pos.x, player.Pos.z).Value;
        float face = player.facing;   // 0=+x
        float fh = Mathf.Atan2(Mathf.Cos(face), Mathf.Sin(face));   // 북(+z)에서 시계 방향 각도
        float ang = (big ? fh : fh - H) * Mathf.Rad2Deg;
        var old = GUI.matrix; GUIUtility.RotateAroundPivot(ang, me);
        GUI.color = Color.black; GUI.DrawTexture(new Rect(me.x - 7, me.y - 9, 14, 18), dot); GUI.color = Color.white;
        DrawArrow(me); GUI.matrix = old;
    }

    // 삼각형 화살표(위쪽이 앞): 작은 네모 여러 줄로 그린다(텍스처 없이)
    void DrawArrow(Vector2 c)
    {
        for (int i = 0; i < 9; i++) Box(new Rect(c.x - i * 0.55f, c.y - 8 + i * 1.7f, i * 1.1f + 1f, 1.8f), Color.white);
        Box(new Rect(c.x - 1.2f, c.y + 6f, 2.4f, 3f), Color.white);
    }
}
