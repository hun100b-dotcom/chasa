// =============================================================================
// TitleScreen.cs — 타이틀 화면 (기획 first-10min M1)
// 켜자마자: 밤 서낭당 그림 + 느리게 흐르는 안개 + 메뉴(이어하기 · 새로 시작 · 설정 · 끝내기). 누르면 본 게임이 시작된다.
// 왜: 바로 게임이 시작되면 "게임을 켰다"는 느낌이 없다. 이어하기가 있어야 저장을 믿고 나갈 수 있다.
// 열려 있는 동안 세계는 멈춘다(GameMain 이 Open 을 보고 돌려보낸다). 검수·자동 시험용 주소 옵션이 있으면 건너뛴다.
// 그림: Resources/Sprites/title/title_screen(1920x1080, 로고 포함) · first10/menu_btn_* · title_fog_a/b
// =============================================================================
using UnityEngine;

public class TitleScreen : MonoBehaviour
{
    public static bool Open;
    float t;
    GUIStyle label;

    /// <summary>타이틀을 보일지: 필드 본 게임이고, 검수·시험용 주소 옵션이 없을 때</summary>
    public static bool Wanted(bool fieldOn)
    {
        if (!fieldOn) return false;
        var u = (Application.absoluteURL ?? "").ToLowerInvariant();
        if (u.Contains("notitle")) return false;
        foreach (var k in new[] { "time=", "pos=", "hk=", "debug=", "bot", "demo", "act2=1", "act3=1", "clock=", "cam=" }) if (u.Contains(k)) return false;
        return true;
    }

    void Start() { Open = true; }

    void Update() { if (Open) t += Time.unscaledDeltaTime; }

    void Begin(bool fresh)
    {
        if (fresh) SaveStore.Delete();   // 새로 시작: 옛 저장을 지운다(이어하기 칸은 저장이 있을 때만 있다)
        Open = false; Destroy(this);
        Sfx.Play("sfx.ui.confirm");
    }

    void OnGUI()
    {
        if (!Open) return;
        Ko.Apply();
        GUI.depth = 10;   // 설정 창(깊이 0)이 타이틀 위에 그려지게 뒤로 둔다
        if (SettingsPanel.Open && Event.current.type != EventType.Repaint) return;   // 설정이 열려 있으면 뒤 메뉴가 클릭을 가져가지 않게
        float W = Screen.width, H = Screen.height, k = Mathf.Clamp(H / 1080f, 0.6f, 1.6f);
        var bg = SpriteLib.Texture("title/title_screen");
        if (bg != null) GUI.DrawTexture(new Rect(0, 0, W, H), bg, ScaleMode.ScaleAndCrop);
        else { var old = GUI.color; GUI.color = new Color(0.05f, 0.06f, 0.12f); GUI.DrawTexture(new Rect(0, 0, W, H), Texture2D.whiteTexture); GUI.color = old; }
        // 안개 띠 둘: 가장 느린 층 8px/초, 빠른 층 14px/초(1080p 기준). 이음매 없는 그림이라 좌우로 이어 붙인다
        DrawFog("first10/title_fog_a", 8f, 0.55f, H * 0.58f, k); DrawFog("first10/title_fog_b", 14f, 0.45f, H * 0.66f, k);
        if (label == null) label = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
        // 메뉴: 오른쪽 아래. 버튼 360x64
        bool hasSave = SaveStore.Exists;
        var items = new System.Collections.Generic.List<string>();
        if (hasSave) items.Add("이어하기"); items.Add("새로 시작"); items.Add("설정");
#if !UNITY_WEBGL
        items.Add("끝내기");
#endif
        float bw = 360f * k, bh = 64f * k, gap = 14f * k, x = W - bw - 90f * k, y = H - (bh + gap) * items.Count - 70f * k;
        var normal = First10.Tex("menu_btn_normal"); var hover = First10.Tex("menu_btn_hover");
        for (int i = 0; i < items.Count; i++)
        {
            var r = new Rect(x, y + i * (bh + gap), bw, bh);
            bool over = r.Contains(Event.current.mousePosition);
            var tex = over && hover != null ? hover : normal;
            if (tex != null) GUI.DrawTexture(r, tex);
            else { var old = GUI.color; GUI.color = over ? new Color(0.45f, 0.18f, 0.12f) : new Color(0.14f, 0.1f, 0.12f); GUI.DrawTexture(r, Texture2D.whiteTexture); GUI.color = old; }
            label.fontSize = Mathf.RoundToInt(20 * k); label.normal.textColor = new Color(0.97f, 0.93f, 0.82f);
            GUI.Label(r, items[i], label);
            if (Event.current.type == EventType.MouseDown && r.Contains(Event.current.mousePosition)) { Event.current.Use(); Pick(items[i]); }
        }
        // 키보드: Enter = 이어하기(없으면 새로 시작)
        if (Event.current.type == EventType.KeyDown && (Event.current.keyCode == KeyCode.Return || Event.current.keyCode == KeyCode.KeypadEnter)) { Event.current.Use(); Pick(hasSave ? "이어하기" : "새로 시작"); }
        // 처음 0.6초는 부드럽게 밝아진다
        if (t < 0.6f) { var old = GUI.color; GUI.color = new Color(0, 0, 0, 1f - t / 0.6f); GUI.DrawTexture(new Rect(0, 0, W, H), Texture2D.whiteTexture); GUI.color = old; }
    }

    void Pick(string name)
    {
        if (name == "이어하기") Begin(false);
        else if (name == "새로 시작") Begin(true);
        else if (name == "설정") { var s = FindObjectOfType<SettingsPanel>(); if (s != null) s.Toggle(); }
        else Application.Quit();
    }

    void DrawFog(string name, float speed, float alpha, float y, float k)
    {
        var tex = First10.Tex(name); if (tex == null) return;
        float h = 512f * k * 0.7f, w = 2048f * k * 0.7f, off = (t * speed * k) % w;
        var old = GUI.color; GUI.color = new Color(1f, 1f, 1f, alpha);
        for (float x = -off; x < Screen.width; x += w) GUI.DrawTexture(new Rect(x, y, w, h), tex);
        GUI.color = old;
    }
}
