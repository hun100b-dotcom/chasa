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
    public static float LeftPx = -1f;   // 작은 지도 틀의 왼쪽 끝(화면 px). 소리·설정 버튼이 그 왼쪽에 놓인다(-1 이면 아직 모름)
    public static float BottomPx = 150f;   // 작은 지도 + 지역 이름 줄의 아래 끝(화면 px, 위가 0). UiRoot 가 시계 고리를 이 아래에 둔다

    const int Px = 320;                 // 바탕 그림 한 변(픽셀)
    const float WorldM = 640f;          // 필드 한 변(m)
    const float M2P = Px / WorldM;      // 1m 당 픽셀
    // 작은 지도가 보여 주는 반지름(m). 기획 표준 40m(지름 80m) 기본, + / - 키로 30·40·60m 3단계(기획 명세 v1.2). 바뀔 때 부드럽게 따라간다
    static readonly float[] RadiusSteps = { 30f, 40f, 60f };
    int radiusStep = 1; float MiniRadiusM = 40f;
    static Rect miniRect;   // 작은 지도 틀(GUI 좌표). 폰에서 탭하면 큰 지도가 열린다
    public static bool OverMini(Vector2 screenPos) { return miniRect.width > 0f && miniRect.Contains(new Vector2(screenPos.x, Screen.height - screenPos.y)); }
    Texture2D baseTex, white, dot, frameTex; bool ready;
    readonly Dictionary<string, Texture2D> icons = new Dictionary<string, Texture2D>();
    void LoadIcons() { foreach (var n in new[] { "me", "boss", "enemy", "elite", "seonang", "bridge", "ferry", "quest", "soul_lump", "soul_fresh", "soul_named", "npc" }) icons[n] = SpriteLib.Texture("ui/map_icon_" + n); icons["soul_wait"] = SpriteLib.Texture("icon_soul_wait"); icons["soulpath_off"] = SpriteLib.Texture("icon_soulpath_off"); }   // 처결 대기 혼(속 빈 청록 고리)·낮에 닫힌 넋길(아트 PR #47)
    // 아트 아이콘(64px 그림)을 화면 크기 sz 로 줄여 그린다. 없으면 false
    bool Icon(string n, Vector2 c, float sz)
    {
        Texture2D t; if (!icons.TryGetValue(n, out t) || t == null) return false;
        GUI.DrawTexture(new Rect(c.x - sz * 0.5f, c.y - sz * 0.5f, sz, sz), t); return true;
    }
    [Serializable] class Item { public string n; public float x, z; public int t; }
    [Serializable] class Mark { public string kind, name; public float x, z; }
    [Serializable] class FieldFile { public Item[] items; public Mark[] markers; }
    // 2·3막 지도 겹침(tools/build_map_overlay.py 가 act2_map·act3_map 에서 만든다). 아트 지도는 1막(0~640m)뿐이라 그 밖은 도형으로 그린다
    [Serializable] class OvRect { public int act; public float[] rect; }
    [Serializable] class OvZone { public int act; public string name, code; public float[] rect; }
    [Serializable] class OvRoad { public int act; public string name; public float[] pts; }
    [Serializable] class OvPt { public int act; public string name; public float x, z; }
    [Serializable] class OvFile { public float[] extent; public OvRect[] fills; public OvZone[] zones; public OvRoad[] roads; public OvPt[] shrines, bosses; }
    OvFile ov; float ex0 = 0f, ez0 = 0f, ew = WorldM, eh = WorldM;   // 큰 지도가 보여 줄 전체 범위(월드 m). 겹침 데이터가 없으면 1막 정사각
    static float bigX0, bigZ0;                                       // 큰 지도를 그리는 동안 월드 → 화면 변환에 쓰는 왼쪽 아래 월드 좌표
    void LoadOverlay()
    {
        var ta = Resources.Load<TextAsset>("Data/map_overlay"); if (ta == null) return;
        try { ov = JsonUtility.FromJson<OvFile>(ta.text); } catch { ov = null; }
        if (ov != null && ov.extent != null && ov.extent.Length >= 4) { ex0 = ov.extent[0]; ez0 = ov.extent[1]; ew = ov.extent[2] - ov.extent[0]; eh = ov.extent[3] - ov.extent[1]; }
    }
    readonly List<Mark> marks = new List<Mark>();
    readonly List<KeyValuePair<string, Rect>> zones = new List<KeyValuePair<string, Rect>>();
    GUIStyle label, small, title; float styleH;
    readonly List<KeyValuePair<Vector3, string>> tmp = new List<KeyValuePair<Vector3, string>>();

    void Start()
    {
        white = Texture2D.whiteTexture;
        LoadOverlay();
        dot = new Texture2D(32, 32, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear };   // 속이 찬 동그라미
        for (int y = 0; y < 32; y++) for (int x = 0; x < 32; x++) dot.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(16f - Vector2.Distance(new Vector2(x, y), new Vector2(15.5f, 15.5f)))));
        dot.Apply();
        StartCoroutine(Bake());
    }

    // ---- 바탕 그림 굽기(여러 프레임에 나눠서) ------------------------------------------
    IEnumerator Bake()
    {
        // 아트가 그린 필드 지도(2048², 북쪽 위, 3.2px/m)가 있으면 그것을 쓴다. 없으면 아래에서 직접 굽는다(대체 수단)
        var art = Resources.Load<TextAsset>("Map/map_field");
        if (art != null)
        {
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
            if (t.LoadImage(art.bytes, true)) { baseTex = t; ready = true; frameTex = SpriteLib.Texture("ui/minimap_frame_square_pc"); LoadIcons(); }
        }
        var ta0 = Resources.Load<TextAsset>("Data/field");
        if (ready)
        {
            FieldFile f0 = null; if (ta0 != null) { try { f0 = JsonUtility.FromJson<FieldFile>(ta0.text); } catch { } }
            zones.AddRange(FieldZones.Labels());
            if (f0 != null && f0.markers != null) marks.AddRange(f0.markers);
            yield break;
        }
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
        if (Input.GetKeyDown(KeyCode.M) && !CharacterPanel.Open && !SettingsPanel.Open) { BigOpen = !BigOpen; judge.guide.Complete("map"); }
        if (BigOpen && Input.GetKeyDown(KeyCode.Escape)) BigOpen = false;
        // + 는 가깝게(반지름 작게), - 는 넓게. 숫자패드 키도 받는다
        if (!BigOpen && (Input.GetKeyDown(KeyCode.Equals) || Input.GetKeyDown(KeyCode.KeypadPlus))) radiusStep = Mathf.Max(0, radiusStep - 1);
        if (!BigOpen && (Input.GetKeyDown(KeyCode.Minus) || Input.GetKeyDown(KeyCode.KeypadMinus))) radiusStep = Mathf.Min(RadiusSteps.Length - 1, radiusStep + 1);
        MiniRadiusM = Mathf.Lerp(MiniRadiusM, RadiusSteps[radiusStep], 1f - Mathf.Exp(-10f * Time.unscaledDeltaTime));
        // 폰: 작은 지도를 탭하면 큰 지도(M 과 같다)
        if (Ko.TouchUI && !BigOpen)
            for (int i = 0; i < Input.touchCount; i++)
            {
                var t = Input.GetTouch(i);
                if (t.phase == TouchPhase.Began && OverMini(t.position)) { BigOpen = true; judge.guide.Complete("map"); }
            }
        if (BigOpen && judge.cuts.Active) BigOpen = false;
    }

    // ---- 그리기 ------------------------------------------------------------------------
    void Styles()
    {
        if (label != null && Mathf.Approximately(styleH, Screen.height)) return;
        styleH = Screen.height;
        float fs = Mathf.Max(1f, Screen.height / 720f) * (Ko.TouchUI ? 1.25f : 1f);   // 화면이 커지면 글자도 커진다(1080p 에서 지역 이름 10px 로 작던 문제)
        label = new GUIStyle(GUI.skin.label) { fontSize = Mathf.RoundToInt(15 * fs), alignment = TextAnchor.MiddleCenter };
        small = new GUIStyle(label) { fontSize = Mathf.RoundToInt(14 * fs) };
        title = new GUIStyle(label) { fontSize = Mathf.RoundToInt(24 * fs) };
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

    // 2·3막 겹침: 땅 바탕·구역 틀·길·서낭당·보스 자리. toScr = 월드 → 화면. big 이면 한지 위에 맞는 짙은 색, 구역 이름도 쓴다
    void DrawOverlay(Func<float, float, Vector2> toScr, bool big)
    {
        if (ov == null) return;
        Color ground = big ? new Color(0.78f, 0.72f, 0.57f, 1f) : new Color(0.20f, 0.24f, 0.19f, 1f);
        if (ov.fills != null) foreach (var f in ov.fills)
        { var a = toScr(f.rect[0], f.rect[1]); var b = toScr(f.rect[2], f.rect[3]); Box(new Rect(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Abs(b.x - a.x), Mathf.Abs(b.y - a.y)), ground); }
        if (ov.zones != null) foreach (var z in ov.zones)
        {
            var a = toScr(z.rect[0], z.rect[1]); var b = toScr(z.rect[2], z.rect[3]);
            var rc = new Rect(Mathf.Min(a.x, b.x), Mathf.Min(a.y, b.y), Mathf.Abs(b.x - a.x), Mathf.Abs(b.y - a.y));
            Frame(rc, 1f, big ? new Color(0.2f, 0.1f, 0.05f, 0.35f) : new Color(1f, 1f, 1f, 0.12f));
            if (big) { GUI.color = new Color(0.15f, 0.07f, 0.03f, 0.9f); GUI.Label(new Rect(rc.center.x - 70, rc.center.y - 12, 140, 24), z.name, label); GUI.color = Color.white; }
        }
        Color road = big ? new Color(0.45f, 0.33f, 0.2f, 0.9f) : new Color(0.84f, 0.75f, 0.55f, 0.9f);
        if (ov.roads != null) foreach (var rd in ov.roads)
            for (int i = 0; i + 3 < rd.pts.Length; i += 2)
            {
                var a = toScr(rd.pts[i], rd.pts[i + 1]); var b = toScr(rd.pts[i + 2], rd.pts[i + 3]);
                var d = b - a; float len = d.magnitude; if (len < 0.5f) continue;
                var old = GUI.matrix; GUIUtility.RotateAroundPivot(Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg, a);
                Box(new Rect(a.x, a.y - 1.2f, len, 2.4f), road); GUI.matrix = old;
            }
        if (ov.shrines != null) foreach (var m in ov.shrines)
        { var v = toScr(m.x, m.z); if (!Icon("seonang", v, 17f)) { Box(new Rect(v.x - 5, v.y - 5, 10, 10), new Color(0.05f, 0.06f, 0.08f, 0.9f)); Box(new Rect(v.x - 3.5f, v.y - 3.5f, 7, 7), new Color(0.45f, 0.95f, 0.85f)); } }
        if (ov.bosses != null) foreach (var m in ov.bosses)
        { var v = toScr(m.x, m.z); if (!Icon("boss", v, big ? 16f : 14f)) { var o = GUI.color; GUI.color = new Color(0.95f, 0.15f, 0.12f); GUI.DrawTexture(new Rect(v.x - 6, v.y - 6, 12, 12), dot); GUI.color = o; } }
    }

    void DrawMini()
    {
        // 기획 표준: 1080p 에서 260px(화면 높이의 24%), 우상 여백 24px. 폰은 200px 급(높이의 30%, 읽히는 하한 110px)
        float size = Ko.TouchUI ? Mathf.Clamp(Screen.height * 0.30f, 110f, 200f) : Mathf.Clamp(Screen.height * 0.24f, 150f, 300f);
        float margin = Mathf.Max(10f, 24f * Screen.height / 1080f);
        var r = new Rect(Screen.width - size - margin, margin, size, size);
        miniRect = r;
        LeftPx = r.x - size * 20f / 260f - 8f;
        BottomPx = r.yMax + size * 20f / 260f + 14f;   // 시계 고리와 12px 이상 띄운다   // 지역 이름 줄까지 포함한 아래 끝(시계 고리가 그 밑에 놓인다)
        float scale = size / (MiniRadiusM * 2f);   // px/m
        float H = 0f;   // 북쪽 고정(기획·아트 명세). 카메라 방향 회전은 마름모가 틀 밖으로 삐져나와 폐지
        if (frameTex == null) Box(new Rect(r.x - 4, r.y - 4, r.width + 8, r.height + 8), new Color(0.05f, 0.06f, 0.09f, 0.92f));
        if (ready)
        {
            GUI.BeginClip(r);
            var cen = new Vector2(size * 0.5f, size * 0.5f);
            var old = GUI.matrix;
            float full = WorldM * scale;
            // 텍스처 좌표(0=남서) → 지도 위 위치: 내 자리가 중앙. IMGUI 의 위쪽은 북(+z)
            float ox = cen.x - player.Pos.x * scale, oy = cen.y - (WorldM - player.Pos.z) * scale;
            float pxw = player.Pos.x, pzw = player.Pos.z;
            DrawOverlay((wx, wz) => new Vector2(cen.x + (wx - pxw) * scale, cen.y - (wz - pzw) * scale), false);   // 2·3막 땅·길(1막은 아래 아트 지도가 덮는다)
            GUI.DrawTexture(new Rect(ox, oy, full, full), baseTex);
            GUI.matrix = old;
            // 표식(회전을 직접 계산해 그려서 글자·점이 돌아가지 않게)
            DrawMarkers(r, cen, scale, H, size * 0.5f, false);
            // 북쪽 표시
            var n = Rot(0f, 1f, H); GUI.Label(new Rect(cen.x + n.x * (size * 0.5f - 12f) - 10f, cen.y - n.y * (size * 0.5f - 12f) - 9f, 20, 18), "북", small);
            GUI.EndClip();
        }
        else GUI.Label(r, "지도를 그리는 중…", small);
        if (frameTex != null) { float e = size * 20f / 260f; GUI.DrawTexture(new Rect(r.x - e, r.y - e, size + e * 2f, size + e * 2f), frameTex); }   // 아트 틀(구멍 260, 캔버스 300)
        else { Frame(r, 2f, new Color(0.83f, 0.66f, 0.31f, 1f)); Frame(new Rect(r.x - 4, r.y - 4, r.width + 8, r.height + 8), 1.5f, new Color(0.45f, 0.1f, 0.1f, 1f)); }
        string zn = FieldZones.CurrentName; if (string.IsNullOrEmpty(zn)) zn = "들길";
        var band = new Rect(r.x, r.yMax - size * 0.11f, r.width, size * 0.11f);   // 지도 아래 안쪽 띠: 시각 고리에 가려지지 않는다
        Box(band, new Color(0.04f, 0.04f, 0.07f, 0.72f));
        GUI.color = new Color(1f, 0.93f, 0.75f, 1f); GUI.Label(band, zn, small); GUI.color = Color.white;
    }

    void DrawBig()
    {
        // 아트 큰 지도 틀(1536×864, 지도 창 1104×700 이 왼쪽 위 64,96 에 뚫림, 오른쪽 범례 칸 300×700 이 1196,96)을 화면 80% 로 띄운다
        var bf = SpriteLib.Texture("ui/map_bigmap_frame");
        Box(new Rect(0, 0, Screen.width, Screen.height), new Color(0, 0, 0, 0.7f));
        if (bf == null) { DrawBigPlain(); return; }
        float k = Mathf.Min(Screen.width * 0.8f / 1536f, Screen.height * 0.8f / 864f);
        var fr = new Rect((Screen.width - 1536f * k) * 0.5f, (Screen.height - 864f * k) * 0.5f, 1536f * k, 864f * k);
        var win = new Rect(fr.x + 64f * k, fr.y + 96f * k, 1104f * k, 700f * k);
        float scale = Mathf.Min(win.width / ew, win.height / eh);   // 1·2·3막 전체 범위가 창에 들어오는 배율
        var r = new Rect(win.x + (win.width - ew * scale) * 0.5f, win.y + (win.height - eh * scale) * 0.5f, ew * scale, eh * scale);
        bigX0 = ex0; bigZ0 = ez0;
        Box(win, new Color(0.953f, 0.906f, 0.827f, 1f));   // 지도 밖 빈자리는 한지 색(검은 막대 금지: 아트 검수)
        DrawOverlay((wx, wz) => new Vector2(r.x + (wx - bigX0) * scale, r.yMax - (wz - bigZ0) * scale), true);
        if (ready) GUI.DrawTexture(new Rect(r.x + (0f - ex0) * scale, r.yMax - (WorldM - ez0) * scale, WorldM * scale, WorldM * scale), baseTex);   // 아트 1막 지도는 0~640m 자리에
        foreach (var z in zones)
        {
            var c = new Vector2((z.Value.xMin + z.Value.xMax) * 0.5f, (z.Value.yMin + z.Value.yMax) * 0.5f);
            var sp = new Vector2(r.x + (c.x - ex0) * scale, r.yMax - (c.y - ez0) * scale);
            Frame(new Rect(r.x + (z.Value.xMin - ex0) * scale, r.yMax - (z.Value.yMax - ez0) * scale, z.Value.width * scale, z.Value.height * scale), 1f, new Color(0.2f, 0.1f, 0.05f, 0.35f));
            GUI.color = new Color(0.15f, 0.07f, 0.03f, 0.9f); GUI.Label(new Rect(sp.x - 70, sp.y - 12, 140, 24), z.Key, label); GUI.color = Color.white;
        }
        DrawMarkers(r, Vector2.zero, scale, 0f, 0f, true);
        GUI.DrawTexture(fr, bf);
        var lg = SpriteLib.Texture("ui/map_bigmap_legend"); if (lg != null) GUI.DrawTexture(new Rect(fr.x + 1196f * k, fr.y + 96f * k, 300f * k, 700f * k), lg);
        var tt = SpriteLib.Texture("ui/map_bigmap_title"); if (tt != null) GUI.DrawTexture(new Rect(fr.x + 618f * k, fr.y + 36f * k, 300f * k, 54f * k), tt);   // 현판(왼쪽 위 618,36 — 가운데에 오게 놓인다)
        else { GUI.color = new Color(0.95f, 0.82f, 0.45f, 1f); GUI.Label(new Rect(fr.x + 618f * k, fr.y + 36f * k, 300f * k, 54f * k), "필드 지도", title); GUI.color = Color.white; }
        GUI.Label(new Rect(fr.x, fr.y + 806f * k, fr.width, 40f * k), "M · Esc 닫기", label);   // 두루마리 안쪽 아래(도술 칸과 안 겹침)
    }

    void DrawBigPlain()
    {
        float aw = Screen.width - 80f, ah = Screen.height - 120f;
        float scale = Mathf.Min(aw / ew, ah / eh);
        var r = new Rect((Screen.width - ew * scale) * 0.5f, 60f, ew * scale, eh * scale);
        bigX0 = ex0; bigZ0 = ez0;
        Box(new Rect(r.x - 6, r.y - 6, r.width + 12, r.height + 12), new Color(0.10f, 0.09f, 0.08f, 1f));
        DrawOverlay((wx, wz) => new Vector2(r.x + (wx - bigX0) * scale, r.yMax - (wz - bigZ0) * scale), false);
        if (ready) GUI.DrawTexture(new Rect(r.x + (0f - ex0) * scale, r.yMax - (WorldM - ez0) * scale, WorldM * scale, WorldM * scale), baseTex);
        foreach (var z in zones)
        {
            var c = new Vector2((z.Value.xMin + z.Value.xMax) * 0.5f, (z.Value.yMin + z.Value.yMax) * 0.5f);
            var sp = new Vector2(r.x + (c.x - ex0) * scale, r.yMax - (c.y - ez0) * scale);
            Frame(new Rect(r.x + (z.Value.xMin - ex0) * scale, r.yMax - (z.Value.yMax - ez0) * scale, z.Value.width * scale, z.Value.height * scale), 1f, new Color(1, 1, 1, 0.18f));
            GUI.color = new Color(1f, 0.95f, 0.8f, 0.85f); GUI.Label(new Rect(sp.x - 70, sp.y - 12, 140, 24), z.Key, label); GUI.color = Color.white;
        }
        DrawMarkers(r, Vector2.zero, scale, 0f, 0f, true);
        Frame(r, 2f, new Color(0.83f, 0.66f, 0.31f, 1f));
        GUI.Label(new Rect(r.x, 14f, r.width, 36f), "필드 지도", title);
        GUI.Label(new Rect(r.x, r.yMax + 10f, r.width, 22f), "M · Esc 닫기", label);
    }

    // 큰 지도(big=true): 북쪽이 위, 화면 = r 안의 절대 좌표. 작은 지도: 중심(cen) 기준 회전 좌표, 지도 가장자리 밖 표식은 가장자리에 붙인다
    void DrawMarkers(Rect r, Vector2 cen, float scale, float H, float half, bool big)
    {
        Func<float, float, Vector2?> toScreen = (wx, wz) =>
        {
            if (big) return new Vector2(r.x + (wx - bigX0) * scale, r.yMax - (wz - bigZ0) * scale);
            var o = Rot(wx - player.Pos.x, wz - player.Pos.z, H) * scale;
            return new Vector2(cen.x + o.x, cen.y - o.y);
        };
        Action<float, float, Color, float, string> D = (wx, wz, col, sz, ic) =>
        {
            var p = toScreen(wx, wz); if (!p.HasValue) return;
            var v = p.Value; if (!big) { if (Mathf.Abs(v.x - cen.x) > half - 3f || Mathf.Abs(v.y - cen.y) > half - 3f) return; }
            if (ic != null && Icon(ic, v, sz * 1.6f)) return;   // 아트 아이콘은 먹 테두리 때문에 조금 키워야 같은 크기로 읽힌다
            var o = GUI.color; GUI.color = col; GUI.DrawTexture(new Rect(v.x - sz * 0.5f, v.y - sz * 0.5f, sz, sz), dot); GUI.color = o;
        };
        Action<Vector2, Color, float> D2 = (pt, col, sz) => { var o = GUI.color; GUI.color = col; GUI.DrawTexture(new Rect(pt.x - sz * 0.5f, pt.y - sz * 0.5f, sz, sz), dot); GUI.color = o; };
        float s = big ? 7f : 6f;
        // 서낭당·다리·나루터·의원집·마을(고정 표식): 작은 네모 + 글자(큰 지도)
        foreach (var m in marks)
        {
            Color col = m.kind == "seonang" ? new Color(0.45f, 0.95f, 0.85f) : m.kind == "village" ? new Color(1f, 0.85f, 0.4f) : m.kind == "doctor" ? new Color(0.5f, 0.9f, 0.5f) : new Color(0.85f, 0.85f, 0.95f);
            var p = toScreen(m.x, m.z); if (!p.HasValue) continue;
            var v = p.Value; if (!big && (Mathf.Abs(v.x - cen.x) > half - 4f || Mathf.Abs(v.y - cen.y) > half - 4f)) continue;
            string mi = m.kind == "seonang" ? (Sfx.NightNow ? "seonang" : "soulpath_off") :   /* 넋길(서낭당)은 낮에 닫혀 있다: 낮엔 닫힌 아이콘(명세 v1.5) */ m.kind == "bridge" ? "bridge" : m.kind == "ferry" ? "ferry" : (m.kind == "village" || m.kind == "doctor") ? "npc" : null;
            if (mi == null || !Icon(mi, v, 17f)) { Box(new Rect(v.x - 5, v.y - 5, 10, 10), new Color(0.05f, 0.06f, 0.08f, 0.9f)); Box(new Rect(v.x - 3.5f, v.y - 3.5f, 7, 7), col); }
            if (m.kind == "seonang" && judge.EnhanceReady) D2(v + new Vector2(7f, -7f), new Color(0.9f, 0.15f, 0.12f), big ? 8f : 7f);   // R2: 손볼 엽전이 모였다는 붉은 점
            if (big && (m.kind == "seonang" || m.kind == "village" || m.kind == "ferry" || m.kind == "doctor") && !ZoneHasName(m.name)) { var nm = m.name; int i = nm.IndexOf('('); if (i > 0) nm = nm.Substring(0, i); i = nm.IndexOf('·'); GUI.color = new Color(0.12f, 0.06f, 0.02f, 1f); GUI.Label(new Rect(v.x - 80, v.y + 6, 160, 20), nm, small); GUI.color = Color.white; /* 밝은 지도 위에서도 읽히게 짙은 글자 + 연한 그림자 */ }
        }
        // 보스(붉은 마름모) — 아직 안 나타났어도 자리를 표시한다
        for (int id = 1; id <= Bosses.Count; id++) { var bd = Bosses.Get(id); D(bd.X, bd.Z, new Color(0.95f, 0.15f, 0.12f), s + 6f, "boss"); }
        // R1: 아직 안 만난 이름혼 쪽 먹 점 하나(작은 지도 가장자리에 붙임). 하루 한 번 30초
        if (!big && judge.NamedGuide.HasValue)
        {
            var gp = toScreen(judge.NamedGuide.Value.x, judge.NamedGuide.Value.z);
            if (gp.HasValue)
            {
                var gv = gp.Value - cen; float m = Mathf.Max(Mathf.Abs(gv.x), Mathf.Abs(gv.y), 0.01f); float k = Mathf.Min(1f, (half - 8f) / m);
                var at = cen + gv * k; float pulse = 0.65f + 0.35f * Mathf.Sin(Time.unscaledTime * 4f);
                D2(at, new Color(0.07f, 0.06f, 0.08f, 0.95f), 12f); D2(at, new Color(0.7f, 0.95f, 0.9f, pulse), 6f);
            }
        }
        // 흩어진 노잣돈: 잿빛 작은 점(넋길·혼 점보다 작게)
        foreach (var np in judge.NojatShown) D(np.x, np.z, new Color(0.62f, 0.62f, 0.6f), 3.5f, null);
        // 켜진 단서 자리
        if (judge.npcs != null) { tmp.Clear(); judge.npcs.PendingClues(tmp); foreach (var c in tmp) D(c.Key.x, c.Key.z, new Color(1f, 0.85f, 0.2f), s + 2f, "quest"); }
        // 이름혼
        if (judge.named != null) { tmp.Clear(); judge.named.PendingPositions(tmp); foreach (var c in tmp) { if (judge.NamedMarkerHidden(c.Value, c.Key.x, c.Key.z)) continue; D(c.Key.x, c.Key.z, new Color(0.4f, 1f, 0.85f), s + 1f, "soul_named"); } }
        // 혼
        foreach (var e in judge.enemies.list)
        {
            if (e == null || e.gone) continue;
            if (e.soul.Boss) { D(e.Pos.x, e.Pos.z, new Color(1f, 0.3f, 0.25f), s + 6f, "boss"); continue; }
            Color col = e.kneeling ? new Color(1f, 0.85f, 0.35f) : e.soul.Kind == SoulKind.Lump ? new Color(0.7f, 0.4f, 0.95f) : new Color(0.95f, 0.3f, 0.3f);
            if (!e.Targetable) continue;   // 땅속 혼은 지도에도 안 보인다
            // 점 크기(명세 v1.5 §2): 적 8 · 정예 12 · 처결 대기 혼 10 · 덩어리 10. 폰은 ×1.2. 흙빛 지도의 보리 점·집 그림자와 섞이지 않게 키웠다
            float ps = Ko.TouchUI ? 1.2f : 1f;
            if (e.kneeling) D(e.Pos.x, e.Pos.z, col, 10f * ps, "soul_wait");
            else if (e.elite) D(e.Pos.x, e.Pos.z, col, 12f * ps, "elite");
            else if (e.soul.Kind == SoulKind.Lump) D(e.Pos.x, e.Pos.z, col, 10f * ps, "soul_lump");
            else D(e.Pos.x, e.Pos.z, col, 8f * ps, "enemy");
        }
        // 나: 흰 화살표(카메라 기준 방향)
        var me = toScreen(player.Pos.x, player.Pos.z).Value;
        float face = player.facing;   // 0=+x
        float fh = Mathf.Atan2(Mathf.Cos(face), Mathf.Sin(face));   // 북(+z)에서 시계 방향 각도
        float ang = (big ? fh : fh - H) * Mathf.Rad2Deg;
        var old = GUI.matrix; GUIUtility.RotateAroundPivot(ang, me);
        if (!Icon("me", me, 24f)) { GUI.color = Color.black; GUI.DrawTexture(new Rect(me.x - 7, me.y - 9, 14, 18), dot); GUI.color = Color.white; DrawArrow(me); }
        GUI.matrix = old;
    }

    bool ZoneHasName(string n)
    {
        if (string.IsNullOrEmpty(n)) return false;
        int i = n.IndexOf('('); if (i > 0) n = n.Substring(0, i).Trim();
        foreach (var z in zones) if (z.Key == n) return true;
        return false;
    }

    // 삼각형 화살표(위쪽이 앞): 작은 네모 여러 줄로 그린다(텍스처 없이)
    void DrawArrow(Vector2 c)
    {
        for (int i = 0; i < 9; i++) Box(new Rect(c.x - i * 0.55f, c.y - 8 + i * 1.7f, i * 1.1f + 1f, 1.8f), Color.white);
        Box(new Rect(c.x - 1.2f, c.y + 6f, 2.4f, 3f), Color.white);
    }
}
