// =============================================================================
// TouchControls.cs — 폰(터치) 조작 버튼 (기획 hud-controls-spec §5). 옛 사각 버튼 3개(110×90)를 대신한다.
//
// 배치(1080p 기준 px, 화면 높이에 비례해 줄인다):
//   공격 버튼 — 우하, 오른쪽·아래 여백 64, 지름 160. 누르고 있으면 연속 공격, 가까운 적(6m)을 자동 조준
//   도술 4개 — 공격 버튼 둘레 부채꼴(9시→12시), 중심에서 235px, 지름 104. 탭=발동
//   피하기 — 공격 버튼에서 (-345,+61), 지름 104
//   무기 기술 Q — (-83,-335), 지름 104. 무기마다 하나뿐인 기술(끌기·땅울림·불러 세우기·꽂아 버티기·이름 쓰기). 개편 P1-5: 예전 '끌기' 버튼을 이 자리로 합쳤다
//   천도 ▲(-241,-268)·파혼 ✕(-350,-114) — 지름 136, 처결할 혼이 있을 때만(그리기는 JudgeSystem). 위치는 아래 상수 한 곳에서만 정한다
//   상호작용(넋길·등잔 등) — (+64,-466), 대상이 있을 때만(급하지 않은 일이라 멀리)
//   물약 — 왼쪽 위 초상 아래 (150,260), 지름 96, 남은 수 표시. 급할 때 왼손 엄지(개편 P1-5)
//   메뉴 — 왼쪽 위 초상을 톡(눈에 안 보이는 판정 + 초상 오른쪽 아래 책 쪽지 그림 overhaul/btn/menu_badge, 초상은 UiRoot). 무기 바꾸기 — 공격 버튼을 위로 끌어올리기(따로 버튼 없음, 엄지 자리가 모자라서)
// 왜 Input.touches 로 직접 판정하나? 조이스틱을 잡은 채 다른 손가락으로 공격을 눌러야 해서(멀티터치),
//   한 손가락만 다루는 GUI.Button 으로는 안 된다. 그리기만 OnGUI 에 맡긴다.
// 모든 버튼은 눈에 보이는 크기보다 1.2배 넓게, 최소 96px(9mm) 로 눌린다.
// =============================================================================
using System;
using Chasa.Core;
using UnityEngine;

public class TouchControls : MonoBehaviour
{
    public static bool UseHeld;   // 상호작용 버튼을 누르고 있나(만져 보기는 2초 누르기)
    public static bool Active;   // 이 조작이 켜져 있나(옛 IMGUI 도술 줄·넋길 버튼을 숨기는 데 쓴다)
    static TouchControls inst;
    public static Rect[] JudgeRects;   // 천도·파혼 버튼(GUI 좌표). 보일 때만 채워지며, 조이스틱·이동 클릭보다 먼저 눌린다

    // 개편 P1-5(폰 조작 명세 §5): 공격 버튼 중심에서의 거리(1080p 기준 px, 오른쪽이 +x, 아래가 +y). 엄지가 자주 누르는 순서대로 가깝게 둔다
    public static readonly Vector2 DodgeOff = new Vector2(-345f, 61f);
    public static readonly Vector2 QOff = new Vector2(-83f, -335f);
    public static readonly Vector2 TendoOff = new Vector2(-241f, -268f);   // ▲ — 위쪽
    public static readonly Vector2 PahonOff = new Vector2(-350f, -114f);   // ✕ — 아래(회피 쪽). 둘은 크기·밝기가 같다(정답 표시 금지)
    public static readonly Vector2 UseOff = new Vector2(64f, -466f);
    public const float JudgeDiameter = 136f;                               // 처결 둘의 지름(1080p 기준)
    public const float SkillRadius = 235f;                                 // 도술 부채꼴 반지름

    /// <summary>버튼 배율. 세로로 세운 폰은 화면 높이 기준이면 왼쪽 버튼(파혼·피하기)이 화면 밖으로 나간다(PC 확인 2026-10-31).
    /// 공격 중심 기준 왼쪽으로 약 590(1080p 기준 px)이 가로에 들어오도록 가로 폭으로도 제한한다</summary>
    public static float Scale()
    {
        var sa = Screen.safeArea; float w = sa.width > 0f ? sa.width : Screen.width;
        return Mathf.Min(Screen.height / 1080f, w / 590f);
    }

    /// <summary>공격 버튼 중심(GUI 좌표, 위가 0). 노치·제스처 줄을 피해 Screen.safeArea 안쪽 기준. JudgeSystem 의 처결 버튼도 이 점에서 잰다</summary>
    public static Vector2 AttackCenter()
    {
        float s = Scale();
        var sa = Screen.safeArea;
        float rightEdge = sa.width > 0f ? sa.xMax : Screen.width, bottomEdge = sa.width > 0f ? Screen.height - sa.yMin : Screen.height;
        return new Vector2(rightEdge - (64f + 80f) * s, bottomEdge - (64f + 80f) * s);
    }

    public Func<Vector3?> nearestEnemyPos;           // 6m 안 가장 가까운 적 위치(없으면 null)
    public Action onAttackHold, onDodge, onPull, onInteract, onQ;
    public Func<string> qLabel;                      // 무기 기술(Q) 버튼 글자(무기마다 다름)
    public Func<float> qLeft;                        // 무기 기술 남은 대기(초). 0 = 쓸 수 있음
    public Action<int> onSkill;
    public Func<int, string> skillLabel;             // 도술 i 의 이름(없으면 null)
    public Func<int, float> skillLeft;               // 도술 i 의 남은 대기(초). 0 = 쓸 수 있음
    public Func<bool> canInteract, hasPull; public Func<string> interactLabel;
    public Action onHeal, onMenu, onSwap;            // 물약 · 초상 탭(메뉴) · 공격 버튼 끌어올리기(무기 바꾸기)
    public Func<int> potionCount;                    // 남은 회복약 수
    public Func<bool> canSwap;                       // 무기 바꾸기를 쓸 수 있나(안 되면 안내 글자도 없다)
    public Func<float> dodgeCharges;                 // 피하기 충전(2.0 = 가득, 소수 = 충전 중인 칸). 없으면 점을 안 그린다
    public Func<int> dodgeMax;                       // 피하기 최대 충전 수
    public Func<bool> suspended;                     // 낮 화면·창이 떠 있어 폰 버튼을 접어야 하나

    struct Btn { public string id; public Vector2 center; public float r, visual; public string text; public Color color; public bool hidden; }   // hidden = 눌림 판정만 있고 그리지 않는다(초상 탭)   // 좌표는 GUI 좌표(위가 0)
    readonly System.Collections.Generic.List<Btn> btns = new System.Collections.Generic.List<Btn>();
    Texture2D disc, ring;
    bool attackHeld; readonly bool[] prevDown = new bool[16];
    int swapFinger = -1; float swapStartY; bool swapDone;   // 공격 버튼에서 시작한 손가락(무기 바꾸기 끌어올리기 판정용)
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

    // 개편 P1-5: 왼쪽 위 기준 자리(1080p). 초상 가운데는 UiRoot 의 초상(지름 약 132)과 맞춘다
    public static readonly Vector2 PotionPos = new Vector2(150f, 260f);
    public static readonly Vector2 MenuPos = new Vector2(66f, 66f);

    void Layout()
    {
        btns.Clear();
        if (suspended != null && suspended()) return;   // 낮 화면 등이 떠 있으면 버튼이 없다 → 눌러도 아무 일도 안 일어난다
        float s = Scale();
        var sa = Screen.safeArea;
        float left = sa.width > 0f ? sa.xMin : 0f, top = sa.width > 0f ? Screen.height - sa.yMax : 0f;   // 노치·상태줄을 피한 왼쪽 위
        var tl = new Vector2(left, top);
        Add("menu", tl + MenuPos * s, 132f * s, "", Color.clear, s, true);
        int pots = potionCount != null ? potionCount() : 0;
        Add("potion", tl + PotionPos * s, 96f * s, "약 " + pots, pots > 0 ? new Color(0.20f, 0.50f, 0.28f) : new Color(0.25f, 0.28f, 0.27f), s);
        Vector2 ac = AttackCenter();   // 공격 버튼 중심
        Add("atk", ac, 160f * s, "공격", new Color(0.62f, 0.22f, 0.18f), s);
        for (int i = 0; i < 4; i++)
        {
            float ang = (180f - 30f * i) * Mathf.Deg2Rad;   // 9시 → 12시
            Add("sk" + i, ac + new Vector2(Mathf.Cos(ang), -Mathf.Sin(ang)) * SkillRadius * s, 104f * s, "", new Color(0.12f, 0.45f, 0.45f), s);   // 버튼 사이 간격 16px 이상(명세 §9-4)
        }
        Add("dodge", ac + DodgeOff * s, 104f * s, "피하기", new Color(0.30f, 0.34f, 0.46f), s);
        Add("q", ac + QOff * s, 104f * s, qLabel != null ? qLabel() : "기술", new Color(0.55f, 0.42f, 0.16f), s);   // 무기 기술은 늘 있다(없는 무기는 베기)
        if (canInteract != null && canInteract()) Add("use", ac + UseOff * s, 104f * s, interactLabel != null ? interactLabel() : "상호작용", new Color(0.85f, 0.78f, 0.62f), s);
    }

    void Add(string id, Vector2 c, float diameter, string text, Color col, float s, bool hidden = false)
    {
        float vis = diameter * 0.5f;
        btns.Add(new Btn { id = id, center = c, visual = vis, r = Mathf.Max(vis * 1.2f, 48f * s * 2f / 2f), text = text, color = col, hidden = hidden });   // 눌림 반지름: 1.2배, 최소 지름 96px
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
            // 판정끼리 겹치면 중심이 더 가까운 버튼이 이긴다(명세 §9-4)
            int best = -1; float bestD = float.MaxValue;
            for (int i = 0; i < btns.Count; i++)
            {
                float d = (p - btns[i].center).magnitude;
                if (d > btns[i].r || d >= bestD) continue;
                best = i; bestD = d;
            }
            if (best >= 0) { down[best] = true; if (btns[best].id == "atk") atk = true; if (btns[best].id == "use") UseHeld = true; }
        }
        // 공격 버튼을 위로 끌어올리면 무기 바꾸기(명세 §5: 따로 버튼 없이 공격 버튼 위쪽 테두리). 끈 손가락은 그동안 연속 공격이 아니다
        if (canSwap != null && canSwap() && onSwap != null && btns.Count > 0)
        {
            var atkBtn = btns.Find(b => b.id == "atk");
            for (int t = 0; t < Input.touchCount; t++)
            {
                var tc = Input.GetTouch(t);
                var p = new Vector2(tc.position.x, Screen.height - tc.position.y);
                if (tc.phase == TouchPhase.Began) { swapFinger = (p - atkBtn.center).magnitude <= atkBtn.r ? tc.fingerId : swapFinger == tc.fingerId ? -1 : swapFinger; swapStartY = p.y; swapDone = false; }
                else if (tc.fingerId == swapFinger && !swapDone && tc.phase == TouchPhase.Moved && swapStartY - p.y > 70f * Scale())
                {
                    swapDone = true; onSwap();   // 위로(화면 y 는 위가 작다) 70px(1080p 기준) 이상
                }
                if (tc.fingerId == swapFinger && (tc.phase == TouchPhase.Ended || tc.phase == TouchPhase.Canceled)) { swapFinger = -1; swapDone = false; }
            }
            if (swapDone) atk = false;   // 바꾼 뒤 손을 뗄 때까지 연속 공격으로 새지 않는다
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
                else if (id == "q") { if (onQ != null) onQ(); }
                else if (id == "use") { if (onInteract != null) onInteract(); }
                else if (id == "potion") { if (onHeal != null) onHeal(); }
                else if (id == "menu") { if (onMenu != null) onMenu(); }
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
        for (int bi = 0; bi < btns.Count; bi++)
        {
            var b = btns[bi];
            if (b.hidden)
            {
                // 초상 탭(메뉴): 눌림 판정은 눈에 안 보이지만, 초상 오른쪽 아래에 '책' 쪽지를 붙여 눌러도 된다는 단서를 준다
                if (b.id == "menu") DrawMenuBadge(b, bi < prevDown.Length && prevDown[bi]);
                continue;
            }
            string text = b.text; float left = 0f; bool dim = false;
            if (b.id == "potion") dim = potionCount == null || potionCount() <= 0;   // 약이 없으면 어둡게(눌러도 '회복약이 없다' 안내만)
            if (b.id.StartsWith("sk"))
            {
                int i = int.Parse(b.id.Substring(2)); string nm = skillLabel != null ? skillLabel(i) : null;
                if (nm == null) continue;   // 비어 있는 칸은 그리지 않는다
                text = nm; left = skillLeft != null ? skillLeft(i) : 0f; dim = left > 0f;
            }
            if (b.id == "q") { left = qLeft != null ? qLeft() : 0f; dim = left > 0f; }   // 재사용 중엔 어둡게 + 남은 초
            bool pressed = b.id == "atk" && attackHeld;
            bool touched = bi < prevDown.Length && prevDown[bi];   // 지금 눌려 있나(겉 빛용)
            var rect = new Rect(b.center.x - b.visual, b.center.y - b.visual, b.visual * 2f, b.visual * 2f);

            // --- 개편 그림이 있으면 그것으로 (potion / atk / dodge / 기술 칸 고리). 없으면 아래 옛 임시 원
            Texture2D baseArt = null; float hotGrow = 1f; Texture2D hotArt = null; bool artLabelBelow = false;
            if (b.id == "potion") { baseArt = Art(dim ? "potion_off" : "potion_on"); hotArt = dim ? null : Art("potion_hot"); hotGrow = 112f / 96f; }
            else if (b.id == "atk") { baseArt = Art("atk"); hotArt = Art("atk_hot"); hotGrow = 180f / 160f; artLabelBelow = true; }
            else if (b.id == "dodge") { baseArt = Art("dodge"); artLabelBelow = true; }
            else if (b.id.StartsWith("sk")) { baseArt = Art(dim ? "skill_ring_cool" : "skill_ring_ready"); }
            else if (b.id == "q") { baseArt = Art(DosulIcons.QIcon(text)); artLabelBelow = true; }                                       // 무기별 Q 그림(없으면 옛 원)
            else if (b.id == "use") { baseArt = Art(DosulIcons.UseIcon); hotArt = Art(DosulIcons.UseIconHot); hotGrow = 120f / 104f; artLabelBelow = true; }   // 상호작용(F) 손 그림
            if (baseArt != null)
            {
                if ((pressed || touched) && hotArt != null) DrawArt(hotArt, rect, hotGrow, 1f);
                else DrawArt(baseArt, rect, 1f, 1f);
                if (dim && b.id != "potion") { GUI.color = new Color(0f, 0f, 0f, 0.25f); GUI.DrawTexture(rect, disc); GUI.color = Color.white; }   // 재사용 대기 어둡게(그림 위 얇은 막)
                label.fontSize = Mathf.Max(12, Mathf.RoundToInt(b.visual * (b.id == "atk" ? 0.27f : 0.28f)));
                if (b.id == "potion")
                {
                    // 남은 수: 오른쪽 아래에 걸친 알약 글자판(40×28 은 96 지름 기준)
                    var chip = Art("potion_count"); float k = b.visual * 2f / 96f;
                    var cr = new Rect(rect.center.x + 12f * k, rect.center.y + 16f * k, 40f * k, 28f * k);
                    if (chip != null) { GUI.color = new Color(1f, 1f, 1f, dim ? 0.6f : 1f); GUI.DrawTexture(cr, chip); GUI.color = Color.white; }
                    label.fontSize = Mathf.Max(12, Mathf.RoundToInt(20f * k));
                    GUI.Label(cr, (potionCount != null ? potionCount() : 0).ToString(), label);
                }
                else if (b.id.StartsWith("sk"))
                {
                    // 기술 칸: 고리 안쪽 64/104 자리에 도술 그림. 그림이 없는 도술(패시브 등)은 갈래 쪽지, 그것도 없으면 옛처럼 이름 글자.
                    // 재사용 중이면 그림을 어둡게 한 위에 남은 초를 얹는다
                    var ic = SkillArt(text);
                    if (ic != null)
                    {
                        float inner = rect.width * 64f / 104f;
                        DrawArt(ic, new Rect(rect.center.x - inner / 2f, rect.center.y - inner / 2f, inner, inner), 1f, dim ? 0.45f : 1f);
                        if (left > 0f) GUI.Label(rect, Mathf.CeilToInt(left).ToString(), label);
                    }
                    else GUI.Label(rect, left > 0f ? Mathf.CeilToInt(left).ToString() : text, label);
                }
                else if (artLabelBelow)
                {
                    // 그림은 위쪽 78% 에 모았고 글자("공격"·"피하기")는 아래 22% 에 — 색약·처음 쓰는 사람도 글자로 읽는다(접근성 결정)
                    var lr = new Rect(rect.x, rect.y + rect.height * 0.70f, rect.width, rect.height * 0.24f);
                    label.fontSize = Mathf.Max(11, Mathf.RoundToInt(b.visual * 0.24f));
                    GUI.Label(lr, b.id == "q" && left > 0f ? Mathf.CeilToInt(left).ToString() : text, label);   // Q 는 재사용 중 남은 초
                }
            }
            else
            {
                GUI.color = new Color(b.color.r, b.color.g, b.color.b, (dim ? 0.35f : 0.62f) + (pressed ? 0.25f : 0f));
                GUI.DrawTexture(rect, disc);
                GUI.color = new Color(1f, 1f, 1f, dim ? 0.35f : 0.8f);
                GUI.DrawTexture(rect, ring);
                GUI.color = Color.white;
                label.fontSize = Mathf.Max(12, Mathf.RoundToInt(b.visual * (b.id == "atk" ? 0.36f : 0.28f)));
                GUI.Label(rect, left > 0f ? Mathf.CeilToInt(left).ToString() : text, label);
            }
            if (b.id == "dodge") DrawDodgePips(rect, b.visual);   // 피하기 충전 ◆ 표시(폰에는 키보드 줄의 충전 점이 없다)
            if (b.id == "atk" && canSwap != null && canSwap())   // 끌어올리기 단서: 공격 버튼 바로 위에 작은 안내(숨은 동작이라 한 번은 보여야 한다)
            {
                // 겹친 위쪽 화살표 그림(없으면 글자만) + "무기" 글자
                var sw = Art("swap_hint"); float sy = rect.y - b.visual * 0.50f;
                if (sw != null) { GUI.color = new Color(1f, 1f, 1f, 0.8f); GUI.DrawTexture(new Rect(rect.center.x - b.visual * 0.2f, sy, b.visual * 0.4f, b.visual * 0.25f), sw); GUI.color = Color.white; }
                label.fontSize = Mathf.Max(11, Mathf.RoundToInt(b.visual * 0.17f));
                GUI.color = new Color(1f, 1f, 1f, 0.7f);
                GUI.Label(new Rect(rect.x, rect.y - b.visual * (sw != null ? 0.26f : 0.38f), rect.width, b.visual * 0.34f), sw != null ? "무기" : "↑ 무기", label);
                GUI.color = Color.white;
            }
        }
    }

    /// <summary>피하기 버튼 위쪽에 충전 ◆ 를 한 줄로 그린다. 찬 칸은 밝은 하늘색, 비면 어두운 회색, 충전 중인 칸은 차오른 만큼만 밝다.
    /// 왜 글자 '◆' 가 아니라 도형인가: 폰 기본 글꼴에 ◆ 가 없으면 네모(깨짐)로 나온다. 흰 사각형을 45도 돌려 마름모를 만들면 글꼴과 무관하다(PC 충전 막대와 같은 방침)</summary>
    void DrawDodgePips(Rect btn, float visual)
    {
        if (dodgeCharges == null || dodgeMax == null) return;
        int n = Mathf.Max(0, dodgeMax()); if (n == 0) return;
        float ch = dodgeCharges(), size = visual * 0.22f, gap = size * 0.55f;   // 마름모 한 변(회전 전)과 간격
        float total = n * size * 1.414f + (n - 1) * gap;                       // 회전하면 대각선(약 1.414배)만큼 차지한다
        float x0 = btn.center.x - total / 2f, cy = btn.y - size * 0.4f;         // 버튼 윗선 바로 위
        var old = GUI.matrix;
        for (int i = 0; i < n; i++)
        {
            float fill = Mathf.Clamp01(ch - i);
            float cx = x0 + size * 0.707f + i * (size * 1.414f + gap);
            var r = new Rect(cx - size / 2f, cy - size / 2f, size, size);
            GUI.matrix = old; GUIUtility.RotateAroundPivot(45f, new Vector2(cx, cy));
            GUI.color = new Color(0f, 0f, 0f, 0.6f); GUI.DrawTexture(new Rect(r.x - 2f, r.y - 2f, size + 4f, size + 4f), Texture2D.whiteTexture);   // 바탕 테두리(어두운 배경에서도 보이게)
            GUI.color = Color.Lerp(new Color(0.35f, 0.38f, 0.45f, 0.9f), new Color(0.75f, 0.88f, 1f, 1f), fill);   // 충전 정도에 따라 어두운 회색 → 밝은 하늘색
            GUI.DrawTexture(r, Texture2D.whiteTexture);
        }
        GUI.matrix = old; GUI.color = Color.white;   // 다른 버튼 그림이 돌아가거나 물들지 않게 원상 복구
    }

    /// <summary>메뉴 쪽지: 초상(지름 132) 오른쪽 아래 모서리에 56px 책 그림. 그림이 없으면 아무것도 안 그린다(옛 모습 = 초상만)</summary>
    void DrawMenuBadge(Btn b, bool touched)
    {
        var t = Art("menu_badge"); if (t == null) return;
        float s = Scale(), d = 56f * s;
        var c = b.center + new Vector2(0.72f, 0.72f) * (b.visual - 8f * s);   // 초상 둘레 오른쪽 아래(45도)에 걸친다
        var rect = new Rect(c.x - d / 2f, c.y - d / 2f, d, d);
        var hot = touched ? Art("menu_badge_hot") : null;
        if (hot != null) DrawArt(hot, rect, (56f + 12f) / 56f, 1f); else DrawArt(t, rect, 1f, 0.95f);
    }

    // 개편 아트(Resources/Sprites/overhaul/btn). 그림이 없으면 null → 아래 OnGUI 가 옛 임시 원으로 대신 그린다(그림 없이도 게임은 돈다).
    // 왜 @2x 를 쓰나: 폰 화면은 촘촘해서 1배 그림을 늘리면 번진다. 이름만 바꾸면 붙게 한 곳에 모은다.
    readonly System.Collections.Generic.Dictionary<string, Texture2D> artCache = new System.Collections.Generic.Dictionary<string, Texture2D>();
    Texture2D Art(string name, string folder = "btn")
    {
        Texture2D t; string key = folder + "/" + name;
        if (artCache.TryGetValue(key, out t)) return t;
        t = SpriteLib.Texture("overhaul/" + key + "@2x"); if (t == null) t = SpriteLib.Texture("overhaul/" + key);
        artCache[key] = t; return t;   // null 도 기억해 두어 매 프레임 찾지 않는다
    }

    /// <summary>도술 이름 → 도술 그림. 표에 없으면(패시브 등) 그 도술의 갈래 쪽지, 그것도 없으면 null</summary>
    Texture2D SkillArt(string skillName)
    {
        string id = DosulIcons.SkillIcon(skillName); Texture2D t = id != null ? Art(id, "skill") : null;
        if (t != null) return t;
        var n = SkillTree.Find(skillName);
        return n != null ? Art(DosulIcons.BranchIcon(n.Branch), "skill") : null;
    }

    /// <summary>그림을 원 버튼 자리에 그린다. grow = 겉 빛 그림처럼 원보다 커진 비율(예 96→112 면 1.1667)</summary>
    static void DrawArt(Texture2D t, Rect rect, float grow, float alpha)
    {
        var r = new Rect(rect.center.x - rect.width * grow * 0.5f, rect.center.y - rect.height * grow * 0.5f, rect.width * grow, rect.height * grow);
        GUI.color = new Color(1f, 1f, 1f, alpha); GUI.DrawTexture(r, t, ScaleMode.StretchToFill, true); GUI.color = Color.white;
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
