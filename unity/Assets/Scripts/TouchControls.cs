// =============================================================================
// TouchControls.cs — 폰(터치) 조작 버튼 (기획 hud-controls-spec §5). 옛 사각 버튼 3개(110×90)를 대신한다.
//
// 배치(1080p 기준 px, 화면 높이에 비례해 줄인다):
//   공격 버튼 — 우하, 오른쪽·아래 여백 64, 지름 160. 누르고 있으면 연속 공격, 가까운 적(6m)을 자동 조준
//   도술 4개 — 공격 버튼 둘레 부채꼴(9시→12시), 중심에서 230px, 지름 104. 탭=발동
//   피하기 — 공격 버튼 왼쪽 아래, 지름 104 / 끌기(견인) — 왼쪽 위 / 상호작용(넋길) — 공격 버튼 위, 대상이 있을 때만
// 왜 Input.touches 로 직접 판정하나? 조이스틱을 잡은 채 다른 손가락으로 공격을 눌러야 해서(멀티터치),
//   한 손가락만 다루는 GUI.Button 으로는 안 된다. 그리기만 OnGUI 에 맡긴다.
// 모든 버튼은 눈에 보이는 크기보다 1.2배 넓게, 최소 96px(9mm) 로 눌린다.
// =============================================================================
using System;
using UnityEngine;

public class TouchControls : MonoBehaviour
{
    public static bool UseHeld;   // 상호작용 버튼을 누르고 있나(만져 보기는 2초 누르기)
    public static bool Active;   // 이 조작이 켜져 있나(옛 IMGUI 도술 줄·넋길 버튼을 숨기는 데 쓴다)
    static TouchControls inst;
    public static Rect[] JudgeRects;   // 천도·파혼 버튼(GUI 좌표). 보일 때만 채워지며, 조이스틱·이동 클릭보다 먼저 눌린다

    public Func<Vector3?> nearestEnemyPos;           // 6m 안 가장 가까운 적 위치(없으면 null)
    public Action onAttackHold, onDodge, onPull, onInteract;
    public Action<int> onSkill;
    public Func<int, string> skillLabel;             // 도술 i 의 이름(없으면 null)
    public Func<int, float> skillLeft;               // 도술 i 의 남은 대기(초). 0 = 쓸 수 있음
    public Func<bool> canInteract, hasPull; public Func<string> interactLabel;

    struct Btn { public string id; public Vector2 center; public float r, visual; public string text; public Color color; }   // 좌표는 GUI 좌표(위가 0)
    readonly System.Collections.Generic.List<Btn> btns = new System.Collections.Generic.List<Btn>();
    Texture2D disc, ring;
    bool attackHeld; readonly bool[] prevDown = new bool[16];
    GUIStyle label;

    void Awake() { inst = this; }
    void OnDestroy() { if (inst == this) inst = null; Active = false; }

    /// <summary>이 화면 좌표(아래가 0)가 터치 버튼 위인가 — '눌러서 이동'과 겹치지 않게 GameMain 이 묻는다</summary>
    public static bool Over(Vector2 screenPos)
    {
        if (inst == null || !Active) return false;
        var p = new Vector2(screenPos.x, Screen.height - screenPos.y);
        if (JudgeRects != null) foreach (var jr in JudgeRects) if (jr.Contains(p)) return true;
        foreach (var b in inst.btns) if ((p - b.center).magnitude <= b.r) return true;
        return false;
    }

    void Layout()
    {
        btns.Clear();
        float s = Screen.height / 1080f;
        Vector2 ac = new Vector2(Screen.width - (64f + 80f) * s, Screen.height - (64f + 80f) * s);   // 공격 버튼 중심
        Add("atk", ac, 160f * s, "공격", new Color(0.62f, 0.22f, 0.18f), s);
        for (int i = 0; i < 4; i++)
        {
            float ang = (180f - 30f * i) * Mathf.Deg2Rad;   // 9시 → 12시
            Add("sk" + i, ac + new Vector2(Mathf.Cos(ang), -Mathf.Sin(ang)) * 230f * s, 104f * s, "", new Color(0.12f, 0.45f, 0.45f), s);
        }
        Add("dodge", ac + new Vector2(-136f * s, 63f * s), 104f * s, "피하기", new Color(0.30f, 0.34f, 0.46f), s);
        if (hasPull != null && hasPull()) { float a = 135f * Mathf.Deg2Rad; Add("pull", ac + new Vector2(Mathf.Cos(a), -Mathf.Sin(a)) * 130f * s, 104f * s, "끌기", new Color(0.55f, 0.42f, 0.16f), s); }
        if (canInteract != null && canInteract()) Add("use", ac + new Vector2(0f, -140f * s), 104f * s, interactLabel != null ? interactLabel() : "상호작용", new Color(0.85f, 0.78f, 0.62f), s);
    }

    void Add(string id, Vector2 c, float diameter, string text, Color col, float s)
    {
        float vis = diameter * 0.5f;
        btns.Add(new Btn { id = id, center = c, visual = vis, r = Mathf.Max(vis * 1.2f, 48f * s * 2f / 2f), text = text, color = col });   // 눌림 반지름: 1.2배, 최소 지름 96px
    }

    void Update()
    {
        Active = Ko.TouchUI;
        if (!Active) return;
        Layout();
        bool atk = false; UseHeld = false; var down = new bool[btns.Count];
        for (int t = 0; t < Input.touchCount; t++)
        {
            var tc = Input.GetTouch(t);
            if (tc.phase == TouchPhase.Ended || tc.phase == TouchPhase.Canceled) continue;
            var p = new Vector2(tc.position.x, Screen.height - tc.position.y);
            for (int i = 0; i < btns.Count; i++)
            {
                if ((p - btns[i].center).magnitude > btns[i].r) continue;
                down[i] = true; if (btns[i].id == "atk") atk = true; if (btns[i].id == "use") UseHeld = true;
                break;
            }
        }
        attackHeld = atk;
        if (atk && onAttackHold != null) onAttackHold();   // 누르고 있는 동안 계속(콤보 예약이 알아서 이어 준다)
        for (int i = 0; i < btns.Count && i < prevDown.Length; i++)
        {
            bool edge = down[i] && !prevDown[i];   // 새로 눌린 순간만(탭)
            if (edge)
            {
                string id = btns[i].id;
                if (id.StartsWith("sk")) { if (onSkill != null) onSkill(int.Parse(id.Substring(2))); }
                else if (id == "dodge") { if (onDodge != null) onDodge(); }
                else if (id == "pull") { if (onPull != null) onPull(); }
                else if (id == "use") { if (onInteract != null) onInteract(); }
            }
        }
        for (int i = 0; i < prevDown.Length; i++) prevDown[i] = i < down.Length && down[i];
    }

    void OnGUI()
    {
        if (!Active || btns.Count == 0 || Event.current.type != EventType.Repaint) return;
        Ko.Apply();
        if (disc == null) MakeTex();
        if (label == null) { label = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold }; label.normal.textColor = Color.white; }
        foreach (var b in btns)
        {
            string text = b.text; float left = 0f; bool dim = false;
            if (b.id.StartsWith("sk"))
            {
                int i = int.Parse(b.id.Substring(2)); string nm = skillLabel != null ? skillLabel(i) : null;
                if (nm == null) continue;   // 비어 있는 칸은 그리지 않는다
                text = nm; left = skillLeft != null ? skillLeft(i) : 0f; dim = left > 0f;
            }
            bool pressed = b.id == "atk" && attackHeld;
            var rect = new Rect(b.center.x - b.visual, b.center.y - b.visual, b.visual * 2f, b.visual * 2f);
            GUI.color = new Color(b.color.r, b.color.g, b.color.b, (dim ? 0.35f : 0.62f) + (pressed ? 0.25f : 0f));
            GUI.DrawTexture(rect, disc);
            GUI.color = new Color(1f, 1f, 1f, dim ? 0.35f : 0.8f);
            GUI.DrawTexture(rect, ring);
            GUI.color = Color.white;
            label.fontSize = Mathf.Max(12, Mathf.RoundToInt(b.visual * (b.id == "atk" ? 0.36f : 0.28f)));
            GUI.Label(rect, left > 0f ? Mathf.CeilToInt(left).ToString() : text, label);
        }
    }

    void MakeTex()
    {
        const int N = 128; disc = new Texture2D(N, N, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear }; ring = new Texture2D(N, N, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear };
        for (int y = 0; y < N; y++) for (int x = 0; x < N; x++)
        {
            float d = Vector2.Distance(new Vector2(x, y), new Vector2(N / 2f - 0.5f, N / 2f - 0.5f));
            disc.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(N / 2f - d)));
            ring.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(N / 2f - d) * Mathf.Clamp01(d - (N / 2f - 5f))));   // 가장자리 얇은 테두리
        }
        disc.Apply(); ring.Apply();
    }
}
