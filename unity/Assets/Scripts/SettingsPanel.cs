// =============================================================================
// SettingsPanel.cs — 설정 화면: 소리 크기(전체·배경음·효과음), 화면 흔들림 세기, 조작 키 보기, 저장·불러오기.
// O 키 / 화면 오른쪽 위 "설정" 버튼으로 열고, 열려 있는 동안 세계가 멈춘다(CharacterPanel 과 같은 방식).
// 값은 SaveStore.Settings 한 곳에 있고 Sfx·BgmPlayer·HitFeel 이 거기서 읽는다 → 바꾸면 바로 들린다.
// 슬라이더를 놓을 때(값이 바뀐 뒤 열기/닫기)에 브라우저 저장소에 저장한다.
// =============================================================================
using Chasa.Core;
using UnityEngine;
using UnityEngine.UIElements;

public class SettingsPanel : MonoBehaviour
{
    public static bool Open;
    public JudgeSystem judge;
    public Texture2D white;
    bool showKeys, dirty, confirmReset;
    string note = "";

    // 조작 키 보기(실제 입력 코드와 같은 키). 폰은 화면 버튼이 대신한다
    static readonly string[] Keys =
    {
        "이동        WASD / 방향키 / 땅을 클릭   (폰: 왼쪽 화면을 눌러 떠다니는 조이스틱)",
        "공격        마우스 왼쪽 클릭(적 쪽으로, 3타 콤보)   우클릭: 커서 방향 즉시 공격",
        "피하기      Space",
        "천도        E (무릎 꿇은 혼 가까이)       파혼   R",
        "도술 4칸    1 2 3 4                      Q  철삭=끌어당김 / 육모방망이=땅울림",
        "무기 바꾸기 Tab                           회복약  H     얼룩 지우기  X",
        "넋길        F (서낭당 곁, 밤)",
        "명부(캐릭터) C                            설정   O",
        "소리 켜고 끄기 N                          줌   마우스 휠",
        "지도 M (크게 보기)",
    };

    // ---- UI Toolkit 판(UiRoot 가 있을 때). 옛 IMGUI 판은 아래 OnGUI 에 그대로 남아 UiRoot 가 없을 때만 쓴다 ----
    VisualElement view; bool viewDirty = true;
    static readonly Color Paper = new Color(0.953f, 0.906f, 0.827f);

    Label Txt(VisualElement parent, string text, int size, bool bold = false)
    {
        var l = new Label(text) { pickingMode = PickingMode.Ignore };
        l.style.color = Paper; l.style.fontSize = size; l.style.whiteSpace = WhiteSpace.Normal;
        if (bold) l.style.unityFontStyleAndWeight = FontStyle.Bold;
        var f = Ko.GetFont(); if (f != null) l.style.unityFontDefinition = FontDefinition.FromFont(f);   // 한글 글꼴(없으면 네모)
        parent.Add(l); return l;
    }

    VisualElement Btn(VisualElement parent, string text, System.Action onClick, bool enabled = true, int w = 170)
    {
        var b = new Label(text); b.style.width = w; b.style.height = 36; b.style.unityTextAlign = TextAnchor.MiddleCenter; b.style.marginRight = 10; b.style.marginTop = 6;
        b.style.color = enabled ? new Color(0.1f, 0.09f, 0.08f) : new Color(0.1f, 0.09f, 0.08f, 0.45f); b.style.fontSize = 16;
        b.style.backgroundColor = enabled ? new Color(0.88f, 0.8f, 0.62f) : new Color(0.55f, 0.5f, 0.4f, 0.6f);
        b.style.borderTopLeftRadius = 5; b.style.borderTopRightRadius = 5; b.style.borderBottomLeftRadius = 5; b.style.borderBottomRightRadius = 5;
        var f = Ko.GetFont(); if (f != null) b.style.unityFontDefinition = FontDefinition.FromFont(f);
        if (enabled) b.RegisterCallback<ClickEvent>(e => { onClick(); viewDirty = true; });
        parent.Add(b); return b;
    }

    /// <summary>끌어서 바꾸는 슬라이더(기본 슬라이더는 빈 테마에서 안 보여 직접 만든다). 값이 바뀌면 dirty 표시</summary>
    void SliderRow(VisualElement parent, string label, float v, float max, System.Action<float> set)
    {
        var row = new VisualElement { pickingMode = PickingMode.Ignore }; row.style.flexDirection = FlexDirection.Row; row.style.alignItems = Align.Center; row.style.height = 36;
        var nm = Txt(row, label, 16); nm.style.width = 120;
        var track = new VisualElement(); track.style.flexGrow = 1; track.style.height = 10; track.style.backgroundColor = new Color(0f, 0f, 0f, 0.55f); track.style.marginLeft = 10; track.style.marginRight = 10;
        track.style.borderTopLeftRadius = 5; track.style.borderTopRightRadius = 5; track.style.borderBottomLeftRadius = 5; track.style.borderBottomRightRadius = 5;
        var fill = new VisualElement { pickingMode = PickingMode.Ignore }; fill.style.height = Length.Percent(100); fill.style.width = Length.Percent(v / max * 100f); fill.style.backgroundColor = new Color(0.45f, 0.78f, 0.82f);
        track.Add(fill); row.Add(track);
        var pct = Txt(row, Mathf.RoundToInt(v / max * 100f) + "%", 16); pct.style.width = 52;
        System.Action<float> apply = x =>
        {
            float f = Mathf.Clamp01(x / Mathf.Max(1f, track.resolvedStyle.width)); float nv = f * max;
            fill.style.width = Length.Percent(f * 100f); pct.text = Mathf.RoundToInt(f * 100f) + "%"; set(nv); dirty = true;
        };
        track.RegisterCallback<PointerDownEvent>(e => { track.CapturePointer(e.pointerId); apply(e.localPosition.x); });
        track.RegisterCallback<PointerMoveEvent>(e => { if (track.HasPointerCapture(e.pointerId)) apply(e.localPosition.x); });
        track.RegisterCallback<PointerUpEvent>(e => { if (track.HasPointerCapture(e.pointerId)) track.ReleasePointer(e.pointerId); });
        parent.Add(row);
    }

    void BuildView()
    {
        var s = SaveStore.Settings;
        view.Clear();
        var box = new VisualElement(); box.style.width = 640; box.style.paddingLeft = 24; box.style.paddingRight = 24; box.style.paddingTop = 16; box.style.paddingBottom = 20;
        box.style.backgroundColor = new Color(0.05f, 0.06f, 0.1f, 0.96f);
        box.style.borderTopLeftRadius = 8; box.style.borderTopRightRadius = 8; box.style.borderBottomLeftRadius = 8; box.style.borderBottomRightRadius = 8;
        var head = new VisualElement { pickingMode = PickingMode.Ignore }; head.style.flexDirection = FlexDirection.Row; head.style.justifyContent = Justify.SpaceBetween; head.style.alignItems = Align.Center;
        Txt(head, "설정", 24, true); Btn(head, "닫기", Close, true, 80);
        box.Add(head);
        var gap = new VisualElement { pickingMode = PickingMode.Ignore }; gap.style.height = 10; box.Add(gap);
        if (!showKeys)
        {
            SliderRow(box, "전체 소리", s.Master, 1f, v => { s.Master = v; AudioListener.volume = v; });
            SliderRow(box, "배경음", s.Bgm, 1f, v => s.Bgm = v);
            SliderRow(box, "효과음", s.Sfx, 1f, v => s.Sfx = v);
            SliderRow(box, "화면 흔들림", s.Shake, 1.5f, v => s.Shake = v);
            Txt(box, "흔들림 0 = 흔들리지 않음(멀미가 나면 줄이세요). 1 = 기본.", 13);
            var r1 = new VisualElement { pickingMode = PickingMode.Position }; r1.style.flexDirection = FlexDirection.Row; r1.style.marginTop = 10; box.Add(r1);
            bool field = judge.FieldMode;
            Btn(r1, "조작 키 보기", () => showKeys = true);
            Btn(r1, "지금 저장", () => note = judge.SaveGameNow() ? "저장했다" : "저장하지 못했다", field, 130);
            Btn(r1, "불러오기", () => { if (judge.LoadGameNow()) { note = "불러왔다"; Close(); } else note = "저장이 없거나 읽지 못했다"; }, field && SaveStore.Exists, 130);
            var r2 = new VisualElement { pickingMode = PickingMode.Position }; r2.style.flexDirection = FlexDirection.Row; r2.style.alignItems = Align.Center; box.Add(r2);
            if (!confirmReset) Btn(r2, "처음부터 (저장 지움)", () => confirmReset = true, true, 200);
            else
            {
                Txt(r2, "저장을 지우고 다시 켜면 새 게임. 정말?", 16).style.marginRight = 12;
                Btn(r2, "지움", () => { SaveStore.Delete(); note = "저장을 지웠다. 새로고침하면 처음부터"; confirmReset = false; }, true, 70);
                Btn(r2, "취소", () => confirmReset = false, true, 70);
            }
            Txt(box, note.Length > 0 ? note : "45초마다 안전할 때 자동 저장됩니다(필드에서).", 14).style.marginTop = 10;
        }
        else
        {
            foreach (var k in Keys) { var t = Txt(box, k, 14); t.style.marginBottom = 6; t.style.whiteSpace = WhiteSpace.NoWrap; }
            Btn(box, "뒤로", () => showKeys = false, true, 140);
        }
        view.Add(box);
    }

    // 실험 스위치: 주소에 ?ui2=1 이 있을 때만 UI Toolkit 설정 화면을 쓴다. 이유: 이 프로젝트는 옛 입력 방식(Input Manager)이라 UI Toolkit 버튼 클릭이
    // 브라우저에서 정말 오는지 아직 실제로 못 봤다. PC 가 확인하면 기본으로 바꾼다(그 전엔 옛 화면이 안전하다)
    static readonly bool Ui2 = (Application.absoluteURL ?? "").Contains("ui2=1");

    void UpdateView()
    {
        if (!Ui2) return;
        if (view == null)
        {
            var ov = judge != null && judge.ui != null ? judge.ui.Overlay : null; if (ov == null) return;
            view = new VisualElement { name = "settings-view" }; view.style.position = Position.Absolute; view.style.left = 0; view.style.right = 0; view.style.top = 0; view.style.bottom = 0;
            view.style.alignItems = Align.Center; view.style.justifyContent = Justify.Center; view.style.display = DisplayStyle.None;
            view.style.backgroundColor = new Color(0f, 0f, 0f, 0.45f);   // 뒤 화면을 어둡게(그리고 클릭이 뒤로 새지 않게 이 판이 눌림을 받는다)
            ov.Add(view);
        }
        bool show = Open; view.style.display = show ? DisplayStyle.Flex : DisplayStyle.None;
        if (show && viewDirty) { viewDirty = false; BuildView(); }
        if (!show) viewDirty = true;   // 다음에 열릴 때 처음부터 다시 만든다
    }

    /// <summary>UiRoot 가 있어 UI Toolkit 판을 쓰는가(IMGUI 판의 열린 화면을 건너뛴다)</summary>
    bool UseView { get { return judge != null && judge.ui != null && view != null; } }

    void Update()
    {
        UpdateView();
        if (Input.GetKeyDown(KeyCode.O) && !CharacterPanel.Open) Toggle();
        if (Open && Input.GetKeyDown(KeyCode.Escape)) Close();
    }

    public void Toggle() { if (Open) Close(); else { Open = true; showKeys = false; confirmReset = false; note = ""; } }

    void Close()
    {
        Open = false;
        if (dirty) { SaveStore.SaveSettings(); dirty = false; }   // 닫을 때 한 번만 저장(슬라이더를 끄는 동안 저장소를 두들기지 않게)
    }

    void OnGUI()
    {
        Ko.Apply();
        if (judge == null) return;
        var s = SaveStore.Settings;
        GUI.depth = -110;
        if (!Open)
        {
            // 닫혀 있을 땐 오른쪽 위 작은 버튼(소리 버튼 아래). 낮 화면·캐릭터 창·컷신 중엔 숨긴다
            if (judge.InDay || CharacterPanel.Open || judge.cuts.Active) return;
            bool t = Ko.TouchUI;
            if (GUI.Button(new Rect(Mathf.Min(Screen.width, MiniMap.LeftPx > 0f ? MiniMap.LeftPx : Screen.width) - (t ? 104 : 78), t ? 62 : 38, t ? 96 : 70, t ? 48 : 26), "설정")) Toggle();
            return;
        }
        if (UseView) return;   // 열린 화면은 UI Toolkit 판이 그린다
        float w = Mathf.Min(Screen.width - 24f, 640f), h = Mathf.Min(Screen.height - 24f, showKeys ? 470f : 460f);
        var box = new Rect((Screen.width - w) / 2f, (Screen.height - h) / 2f, w, h);
        GUI.color = new Color(0.05f, 0.06f, 0.1f, 0.96f); GUI.DrawTexture(box, white); GUI.color = Color.white;
        var title = new GUIStyle(GUI.skin.label) { fontSize = 22, fontStyle = FontStyle.Bold }; title.normal.textColor = ChasaPalette.Hanji;
        var body = new GUIStyle(GUI.skin.label) { fontSize = 16 }; body.normal.textColor = ChasaPalette.Hanji;
        var mono = new GUIStyle(body) { fontSize = 14 };
        float x = box.x + 20, y = box.y + 14;
        GUI.Label(new Rect(x, y, 300, 30), "설정", title);
        if (GUI.Button(new Rect(box.xMax - 100, y, 80, 32), "닫기")) Close();
        y += 46;
        if (!showKeys)
        {
            y = Slider(x, y, box.width - 40, "전체 소리", ref s.Master, 1f, body);
            y = Slider(x, y, box.width - 40, "배경음", ref s.Bgm, 1f, body);
            y = Slider(x, y, box.width - 40, "효과음", ref s.Sfx, 1f, body);
            y = Slider(x, y, box.width - 40, "화면 흔들림", ref s.Shake, 1.5f, body);
            GUI.Label(new Rect(x, y, box.width - 40, 22), "흔들림 0 = 흔들리지 않음(멀미가 나면 줄이세요). 1 = 기본.", new GUIStyle(mono) { fontSize = 13 });
            y += 34;
            if (GUI.Button(new Rect(x, y, 190, 40), "조작 키 보기")) showKeys = true;
            bool field = judge.FieldMode;
            GUI.enabled = field;
            if (GUI.Button(new Rect(x + 200, y, 130, 40), "지금 저장")) note = judge.SaveGameNow() ? "저장했다" : "저장하지 못했다";
            GUI.enabled = field && SaveStore.Exists;
            if (GUI.Button(new Rect(x + 340, y, 130, 40), "불러오기")) { if (judge.LoadGameNow()) { note = "불러왔다"; Close(); } else note = "저장이 없거나 읽지 못했다"; }
            GUI.enabled = true;
            y += 52;
            if (!confirmReset) { if (GUI.Button(new Rect(x, y, 190, 36), "처음부터 (저장 지움)")) confirmReset = true; }
            else
            {
                GUI.Label(new Rect(x, y, 300, 30), "저장을 지우고 다시 켜면 새 게임. 정말?", body);
                if (GUI.Button(new Rect(x + 320, y, 70, 32), "지움")) { SaveStore.Delete(); note = "저장을 지웠다. 새로고침하면 처음부터"; confirmReset = false; }
                if (GUI.Button(new Rect(x + 400, y, 70, 32), "취소")) confirmReset = false;
            }
            y += 44;
            GUI.Label(new Rect(x, y, box.width - 40, 26), note.Length > 0 ? note : "45초마다 안전할 때 자동 저장됩니다(필드에서).", mono);
        }
        else
        {
            foreach (var k in Keys) { GUI.Label(new Rect(x, y, box.width - 40, 26), k, mono); y += 30; }
            y += 6;
            if (GUI.Button(new Rect(x, y, 140, 38), "뒤로")) showKeys = false;
        }
    }

    /// <summary>제목 + 슬라이더 + 숫자 한 줄. 값이 바뀌면 저장할 거라고 표시(dirty)만 한다. 다음 y 를 돌려준다</summary>
    float Slider(float x, float y, float w, string label, ref float v, float max, GUIStyle body)
    {
        GUI.Label(new Rect(x, y, 140, 28), label, body);
        float nv = GUI.HorizontalSlider(new Rect(x + 150, y + 8, w - 150 - 70, 20), v, 0f, max);
        GUI.Label(new Rect(x + w - 60, y, 60, 28), Mathf.RoundToInt(nv / max * 100f) + "%", body);
        if (Mathf.Abs(nv - v) > 1e-4f) { v = nv; dirty = true; if (label == "전체 소리") AudioListener.volume = v; }   // 전체 소리는 바로 반영(나머지는 매 프레임 읽는다)
        return y + 38;
    }
}
