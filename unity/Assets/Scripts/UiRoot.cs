// =============================================================================
// UiRoot.cs — UI Toolkit 으로 그린 HUD (단계 U0 토대 + U1 장부·체력).
//
// UI Toolkit 이란? 화면을 '상자(VisualElement)들의 나무'로 만들고 글자·색·배치를 스타일로 정하는 유니티 신형 화면 방식.
//   옛 방식(IMGUI)은 매 프레임 위치를 좌표로 계산해야 했지만, 여기선 "왼쪽 위에 세로로 쌓기"처럼 말로 정하면
//   해상도(폰/PC)가 달라도 자동으로 맞는다.
// 왜 코드로 만드나? 파일(UXML)을 에디터가 불러와야 하는 단계를 없애려고(에디터 없이 AI가 고치는 원칙).
//   나중에 UXML/USS 파일로 옮겨도 아래 이름(hud-root, ledger-note, vitals)은 기획 UI 밑그림의 이름 그대로다.
// 마우스는 가로채지 않는다(pickingMode Ignore): 게임 클릭이 그대로 먹어야 하니까.
// 켜는 법: 주소 끝 ?ui 또는 balance.json 의 UI_TOOLKIT=true. 꺼져 있으면 예전 IMGUI 가 그린다.
// =============================================================================
using UnityEngine;
using UnityEngine.UIElements;
using Chasa.Core;

public class UiRoot : MonoBehaviour
{
    public static bool Enabled;   // 시작 때 GameMain 이 정한다

    public readonly HudState Hud = new HudState();

    UIDocument doc;
    /// <summary>화면 전체를 덮는 바닥 요소(설정 창 같은 큰 창이 여기에 붙는다). 아직 안 만들어졌으면 null</summary>
    public VisualElement Overlay { get { return doc != null ? doc.rootVisualElement : null; } }
    Label ledger, vital, night, hint, hpText;
    VisualElement hpFill, root, toastBox, skillBar;
    readonly System.Collections.Generic.List<VisualElement> edgePool = new System.Collections.Generic.List<VisualElement>();   // 화면 가장자리 경고 표시 재사용 묶음
    Label dodgeLabel, pullLabel, weaponLabel; VisualElement[] pips = new VisualElement[0];
    VisualElement ringBox, ringMarker, note;   // 시각 고리: 바탕 원 / 해·달 표시
    string lastToasts;
    VisualElement vitalClip, vitalFillImg, slotBar; VisualElement[] slotBox = new VisualElement[0], slotIcon = new VisualElement[0], slotCool = new VisualElement[0]; Label[] slotKey = new Label[0], slotSec = new Label[0];
    bool artRing;   // 아트 시각 고리 틀이 있나(없으면 옛 눈금 고리로 대신 그린다)
    float ringSize = 84f;   // 시각 고리 지름(px, 1280×720 기준). 아트 틀이 있으면 키운다
    string lastLedger, lastVital, lastNight;
    float hpFullW = 304f;   // 체력 채움의 전체 폭(틀 안 홈 길이)
    static float U(float specPx) { return specPx * (Ko.TouchUI ? 0.5f : 2f / 3f); }   // 명세 px(1080p) → 패널 단위(1280×720 기준)

    static readonly Color PaperBg = new Color(0.05f, 0.05f, 0.09f, 0.62f);
    static readonly Color Ink = new Color(1f, 1f, 1f, 0.92f);

    void Start()
    {
        // 화면 설정(PanelSettings): 1280×720 기준으로 크기를 맞춘다. 파일 없이 코드로 만든다
        var ps = ScriptableObject.CreateInstance<PanelSettings>();
        ps.scaleMode = PanelScaleMode.ScaleWithScreenSize;
        ps.referenceResolution = Ko.TouchUI ? new Vector2Int(960, 540) : new Vector2Int(1280, 720);   // 폰은 기준을 작게 잡아 HUD 를 1.33배 크게(기획: 폰 글자 ×1.25 이상)
        ps.screenMatchMode = PanelScreenMatchMode.MatchWidthOrHeight;
        ps.match = 0.5f;
        ps.themeStyleSheet = ScriptableObject.CreateInstance<ThemeStyleSheet>();   // 빈 테마(기본 모양 없이 우리 스타일만 씀)
        ps.sortingOrder = 5;
        var go = new GameObject("UiRoot_Doc");
        go.transform.SetParent(transform, false);
        doc = go.AddComponent<UIDocument>();
        doc.panelSettings = ps;
        Build(doc.rootVisualElement);
    }

    void Build(VisualElement r)
    {
        // 빈 테마라 기본 '화면 가득 채우기'가 없다 → 바닥(r) 높이가 0 이 돼 아래·퍼센트 위치가 어긋났다. 직접 화면 전체로 편다
        r.style.position = Position.Absolute; r.style.left = 0; r.style.top = 0; r.style.right = 0; r.style.bottom = 0;
        root = new VisualElement { name = "hud-root", pickingMode = PickingMode.Ignore };
        root.style.position = Position.Absolute; root.style.left = 0; root.style.top = 0; root.style.right = 0; root.style.bottom = 0;
        r.Add(root);

        // 좌상(기획 표준): 초상 + 체력 막대, 그 아래 장부 글자. 기준 해상도가 1280×720 이라 명세 px(1080p)에 U=2/3 를 곱한다
        note = new VisualElement { name = "ledger-note", pickingMode = PickingMode.Ignore };
        note.style.position = Position.Absolute; note.style.left = U(24); note.style.top = U(24);
        root.Add(note);
        var head = new VisualElement { pickingMode = PickingMode.Ignore }; head.style.flexDirection = FlexDirection.Row; note.Add(head);
        bool artHud = UiTex("hud_hp_frame") != null && UiTex("hud_portrait_frame") != null;
        if (artHud)
        {
            var pf = new VisualElement { pickingMode = PickingMode.Ignore }; pf.style.width = U(88); pf.style.height = U(88);
            var pc = Img("hud_portrait_chasa", U(72), U(72)); pc.style.position = Position.Absolute; pc.style.left = U(8); pc.style.top = U(8);
            var pr = Img("hud_portrait_frame", U(88), U(88)); pr.style.position = Position.Absolute; pr.style.left = 0; pr.style.top = 0;
            pf.Add(pc); pf.Add(pr); head.Add(pf);
            var col = new VisualElement { pickingMode = PickingMode.Ignore }; col.style.marginLeft = U(8); col.style.justifyContent = Justify.Center; head.Add(col);
            // 개편 P0-3: 새 한 벌(overhaul/hud/vital_*: 틀 320×24, 채움 312×16 이 (4,4))이 있으면 그것으로, 없으면 옛 그림으로
            bool newVital = OTex("hud/vital_frame") != null && OTex("hud/vital_fill") != null && OTex("hud/vital_ghost") != null;
            float vfw = newVital ? 312f : 280f, vfh = newVital ? 16f : 18f;
            var bar = newVital ? OImg("hud/vital_frame", U(320), U(24)) : Img("hud_hp_frame", U(288), U(26)); bar.name = "vitals";
            hpFullW = U(vfw);
            var ghost = newVital ? OImg("hud/vital_ghost", hpFullW, U(vfh)) : Img("hud_hp_fill_loss", hpFullW, U(vfh)); ghost.style.position = Position.Absolute; ghost.style.left = U(4); ghost.style.top = U(4);
            vitalClip = new VisualElement { pickingMode = PickingMode.Ignore };
            vitalClip.style.position = Position.Absolute; vitalClip.style.left = U(4); vitalClip.style.top = U(4); vitalClip.style.height = U(vfh); vitalClip.style.width = hpFullW; vitalClip.style.overflow = Overflow.Hidden;
            vitalFillImg = newVital ? OImg("hud/vital_fill", hpFullW, U(vfh)) : Img("hud_hp_fill", hpFullW, U(vfh));
            vitalClip.Add(vitalFillImg); bar.Add(ghost); bar.Add(vitalClip);
            col.Add(bar);
            vital = Line(col, 15); vital.style.marginTop = 4;
            hpFill = null;
        }
        else
        {
            vital = Line(head, 18);
            var bar = new VisualElement { name = "vitals", pickingMode = PickingMode.Ignore };
            bar.style.height = 8; bar.style.width = 200; bar.style.backgroundColor = new Color(0, 0, 0, 0.55f);
            hpFill = new VisualElement { pickingMode = PickingMode.Ignore };
            hpFill.style.height = 8; hpFill.style.backgroundColor = new Color(0.72f, 0.82f, 0.95f);
            bar.Add(hpFill); note.Add(bar);
        }
        // 장부·밤 글자: 배경 위에서도 읽히게 짙은 반투명 판 위에 둔다
        var texts = new VisualElement { pickingMode = PickingMode.Ignore }; texts.style.marginTop = 6; Panel(texts); note.Add(texts);
        ledger = Line(texts, 15); night = Line(texts, 15);
        BuildGuide(); BuildBossArea(); BuildCards(); BuildToasts(); BuildStamp(); BuildDosulCards(); BuildSkillBar(); BuildSlots(); BuildTimeRing();
    }

    // ---- 아트팀 UI 그림(Resources/Sprites/ui). 없으면 null 이라 부르는 쪽이 옛 색 도형으로 대신 그린다(그림 없이도 돈다)
    static Texture2D UiTex(string n) { return SpriteLib.Texture("ui/" + n); }
    // 개편 아트 한 벌(Resources/Sprites/overhaul/...). 없으면 null
    static Texture2D OTex(string n) { return SpriteLib.Texture("overhaul/" + n); }
    static void SetOImg(VisualElement v, string n) { var t = OTex(n); if (t != null) v.style.backgroundImage = Background.FromTexture2D(t); }
    static VisualElement OImg(string n, float w, float h) { var v = new VisualElement { pickingMode = PickingMode.Ignore }; v.style.width = w; v.style.height = h; SetOImg(v, n); return v; }
    /// <summary>틀 안쪽 (4,4) 에 놓는 잘림 상자: 폭을 줄이면 안의 그림이 찌그러지지 않고 잘려 보인다</summary>
    static VisualElement OClip(float w, float h)
    {
        var v = new VisualElement { pickingMode = PickingMode.Ignore };
        v.style.position = Position.Absolute; v.style.left = U(4); v.style.top = U(4); v.style.width = w; v.style.height = h; v.style.overflow = Overflow.Hidden;
        return v;
    }
    // 보스 맺힘 줄(개편): 채움 상자·잔상 상자·깨진 줄·금 10장
    VisualElement bossFillClip, bossGhostClip, bossBroken; VisualElement[] bossCrack; float bossGhostRatio = 1f; int bossCrackStage = -1;
    /// <summary>남은 맺힘 비율 → 금 단계(0 없음 / 1: 66% 이하 / 2: 33% 이하 / 3: 10% 이하). 개편안 §4 의 기준 그대로</summary>
    public static int CrackStage(float ratio) { return CoreRules.GyeolCrackStage(ratio); }

    static void SetImg(VisualElement v, string n) { var t = UiTex(n); if (t != null) v.style.backgroundImage = Background.FromTexture2D(t); }
    static VisualElement Img(string n, float w, float h)
    {
        var v = new VisualElement { pickingMode = PickingMode.Ignore };
        v.style.width = w; v.style.height = h; SetImg(v, n); return v;
    }

    // ---- 개편 도술 그림(Resources/Sprites/overhaul/skill, btn). 기술 칸·도술 카드가 같은 그림을 쓴다 ----
    // 왜 캐시: 기술 칸은 매 프레임 그림을 물어보는데 Resources.Load 를 매번 부르면 낭비다. 없는 그림(null)도 기억해 둔다.
    static readonly System.Collections.Generic.Dictionary<string, Texture2D> artCache = new System.Collections.Generic.Dictionary<string, Texture2D>();
    static Texture2D OArt(string folder, string id)
    {
        if (id == null) return null;
        string key = folder + "/" + id; Texture2D t;
        if (artCache.TryGetValue(key, out t)) return t;
        t = OTex(key + "@2x"); if (t == null) t = OTex(key);   // 폰 화면처럼 촘촘해서 @2x 우선
        artCache[key] = t; return t;
    }
    /// <summary>도술 이름 → 개편 도술 그림. 표에 없으면(패시브 등) 갈래 쪽지, 그것도 없으면 null(부르는 쪽이 옛 그림·글자로 대신)</summary>
    public static Texture2D DosulArt(string skillName)
    {
        var t = OArt("skill", DosulIcons.SkillIcon(skillName)); if (t != null) return t;
        var n = SkillTree.Find(skillName);
        return n != null ? OArt("skill", DosulIcons.BranchIcon(n.Branch)) : null;
    }

    /// <summary>도술 이름 → 아이콘 이름. 갈래별 액티브 순서(부름 청록·줄 사슬·얼룩 보라)가 아트 파일 번호 1~5와 같다</summary>
    public static string SkillIcon(string name)
    {
        var node = SkillTree.Find(name); if (node == null) return null;
        int n = 0;
        foreach (var k in SkillTree.All) { if (k.Branch != node.Branch || !k.Active) continue; n++; if (k.Name == name) break; }
        string br = node.Branch == Branch.Call ? "bureum" : node.Branch == Branch.Chain ? "jul" : "eolluk";
        return "icon_skill_" + br + "_" + n;
    }

    static void Panel(VisualElement v)
    {
        v.style.backgroundColor = new Color(0.10f, 0.11f, 0.18f, 0.78f);   // 어두운 밤 화면에서도 구분되게 조금 밝고 진하게
        var edge = new Color(1f, 1f, 1f, 0.22f);
        v.style.borderTopWidth = 1; v.style.borderBottomWidth = 1; v.style.borderLeftWidth = 1; v.style.borderRightWidth = 1;
        v.style.borderTopColor = edge; v.style.borderBottomColor = edge; v.style.borderLeftColor = edge; v.style.borderRightColor = edge;
        v.style.paddingLeft = 10; v.style.paddingRight = 10; v.style.paddingTop = 6; v.style.paddingBottom = 6;
        v.style.borderTopLeftRadius = 6; v.style.borderBottomLeftRadius = 6; v.style.borderTopRightRadius = 6; v.style.borderBottomRightRadius = 6;
    }

    /// <summary>얻은 것 알림: 왼쪽 가운데 (장부 쪽지와 겹치지 않게 화면 세로 중앙)</summary>
    void BuildToasts()
    {
        toastBox = new VisualElement { name = "toasts", pickingMode = PickingMode.Ignore };
        toastBox.style.position = Position.Absolute; toastBox.style.left = U(24); toastBox.style.bottom = U(140); toastBox.style.flexDirection = FlexDirection.Column;
        root.Add(toastBox);
    }

    // ---- 품계 승급 인: 명부 종이 위에 붉은 品 인이 쾅 찍힌다(처음 10분 M6). 그림이 없으면 붉은 글자로 대신 ----
    VisualElement stampBox, stampPaper, stampInk; Label stampTitle, stampSub, stampPlaque;
    void BuildStamp()
    {
        stampBox = new VisualElement { name = "stamp", pickingMode = PickingMode.Ignore };
        stampBox.style.position = Position.Absolute; stampBox.style.left = 0; stampBox.style.right = 0; stampBox.style.top = Length.Percent(24);
        stampBox.style.alignItems = Align.Center; stampBox.style.display = DisplayStyle.None;
        float k = Ko.TouchUI ? 0.55f : 0.75f;   // 640x400 그림을 패널 단위로 줄인다
        stampPaper = new VisualElement { pickingMode = PickingMode.Ignore }; stampPaper.style.width = 640 * k; stampPaper.style.height = 400 * k;
        var paper = First10.Whole("rank_paper");
        if (paper != null) stampPaper.style.backgroundImage = new StyleBackground(paper);
        stampBox.Add(stampPaper);
        stampPlaque = Line(stampPaper, 26); stampPlaque.style.position = Position.Absolute; stampPlaque.style.left = 60 * k; stampPlaque.style.top = 64 * k;
        stampPlaque.style.width = 520 * k; stampPlaque.style.height = 56 * k; stampPlaque.style.unityTextAlign = TextAnchor.MiddleCenter;
        stampPlaque.style.color = new Color(0.12f, 0.08f, 0.07f); stampPlaque.style.unityFontStyleAndWeight = FontStyle.Bold;
        stampInk = new VisualElement { pickingMode = PickingMode.Ignore }; stampInk.style.position = Position.Absolute;
        stampInk.style.width = 256 * k; stampInk.style.height = 256 * k; stampInk.style.left = (640 - 256) * 0.5f * k; stampInk.style.top = 160 * k;
        stampPaper.Add(stampInk);
        // 그림이 없을 때 대신하는 글자
        stampTitle = Line(stampBox, 56); stampTitle.style.color = new Color(0.86f, 0.12f, 0.1f); stampTitle.style.unityFontStyleAndWeight = FontStyle.Bold;
        stampSub = Line(stampBox, 28); stampSub.style.color = new Color(0.95f, 0.85f, 0.6f);
        root.Add(stampBox);
    }
    void RefreshStamp()
    {
        if (stampBox == null) return;
        bool on = Hud.StampAge >= 0f;
        stampBox.style.display = on ? DisplayStyle.Flex : DisplayStyle.None;
        if (!on) return;
        float a = Hud.StampAge;
        var frames = First10.Strip("rank_stamp", 12);
        bool art = First10.Tex("rank_paper") != null && frames != null;
        stampPaper.style.display = art ? DisplayStyle.Flex : DisplayStyle.None;
        stampTitle.style.display = stampSub.style.display = art ? DisplayStyle.None : DisplayStyle.Flex;
        if (art)
        {
            stampPlaque.text = Hud.StampSub + "  ·  " + Hud.StampTitle;
            int f = Mathf.Min(11, (int)(a * 12f));   // 12프레임 12fps = 1초. 프레임 4(0.33초)가 찍히는 순간
            stampInk.style.backgroundImage = new StyleBackground(frames[f]);
            stampInk.style.display = a >= 0.08f ? DisplayStyle.Flex : DisplayStyle.None;
        }
        else
        {
            stampTitle.text = Hud.StampTitle; stampSub.text = Hud.StampSub;
            stampBox.style.scale = new Scale(Vector2.one * Mathf.Lerp(1.7f, 1f, Mathf.Clamp01(a / 0.15f)));
        }
        stampBox.style.opacity = Mathf.Clamp01((Balance.RANKUP_STAMP_SEC - a) / 0.25f);   // 마지막 0.25초에 사라짐
    }

    // ---- 첫 도술 카드: 한지 빛깔 카드 세 장 중 하나를 고른다(처음 10분 M9). 추천·별점 없음, 같은 크기 ----
    VisualElement cardsBox, cardsRow, rerollBtn; Label cardsTitle, rerollLabel; string lastCards;
    VisualElement[] cardEl = new VisualElement[3], cardBadge = new VisualElement[3], cardArt = new VisualElement[3], cardIcon = new VisualElement[3]; Label[] cardMark = new Label[3], cardName = new Label[3], cardDesc = new Label[3], cardKey = new Label[3];
    void BuildDosulCards()
    {
        cardsBox = new VisualElement { name = "dosul-cards", pickingMode = PickingMode.Position };   // 화면 전체를 덮어 뒤 클릭을 막는다
        cardsBox.style.position = Position.Absolute; cardsBox.style.left = 0; cardsBox.style.right = 0; cardsBox.style.top = 0; cardsBox.style.bottom = 0;
        cardsBox.style.backgroundColor = new Color(0f, 0f, 0f, 0.62f); cardsBox.style.alignItems = Align.Center; cardsBox.style.justifyContent = Justify.Center;
        cardsBox.style.display = DisplayStyle.None;
        cardsTitle = Line(cardsBox, 26); cardsTitle.style.marginBottom = 18;
        cardsRow = new VisualElement { pickingMode = PickingMode.Ignore }; cardsRow.style.flexDirection = FlexDirection.Row; cardsBox.Add(cardsRow);
        for (int i = 0; i < 3; i++)
        {
            int idx = i;
            var c = new VisualElement { pickingMode = PickingMode.Position };
            c.RegisterCallback<PointerEnterEvent>(e => Sfx.Play("sfx.card.hover"));   // 카드에 올리면 종이 스치는 소리
            float k = Ko.TouchUI ? 0.6f : 0.78f;   // 명세 320x440 카드를 패널 단위로 줄인다
            float w = 320f * k, h = 440f * k;
            c.style.width = w; c.style.height = h; c.style.marginLeft = 10; c.style.marginRight = 10;
            var frame = First10.Whole("skill_card_frame");
            bool art = frame != null;
            if (art) c.style.backgroundImage = new StyleBackground(frame);   // 한지 틀(배지·삽화 창·이름 띠 자리가 정해져 있다)
            else
            {
                c.style.backgroundColor = new Color(0.90f, 0.86f, 0.74f, 0.97f);   // 한지
                var edge = new Color(0.10f, 0.08f, 0.07f, 1f);
                c.style.borderTopWidth = 4; c.style.borderBottomWidth = 4; c.style.borderLeftWidth = 4; c.style.borderRightWidth = 4;
                c.style.borderTopColor = edge; c.style.borderBottomColor = edge; c.style.borderLeftColor = edge; c.style.borderRightColor = edge;
            }
            Color ink = new Color(0.12f, 0.09f, 0.08f);
            // 배지(지름 84, 중심 160,44): 갈래 큰 표시 80². 그림이 없으면 글자 기호
            cardBadge[i] = new VisualElement { pickingMode = PickingMode.Ignore }; cardBadge[i].style.position = Position.Absolute;
            cardBadge[i].style.left = (160 - 40) * k; cardBadge[i].style.top = (44 - 40) * k; cardBadge[i].style.width = 80 * k; cardBadge[i].style.height = 80 * k; c.Add(cardBadge[i]);
            cardMark[i] = Line(c, 54); cardMark[i].style.color = ink; cardMark[i].style.position = Position.Absolute; cardMark[i].style.left = 0; cardMark[i].style.width = w; cardMark[i].style.top = 2 * k; cardMark[i].style.unityTextAlign = TextAnchor.MiddleCenter;
            // 삽화 창(16,66, 288x130)
            cardArt[i] = new VisualElement { pickingMode = PickingMode.Ignore }; cardArt[i].style.position = Position.Absolute;
            cardArt[i].style.left = 16 * k; cardArt[i].style.top = 66 * k; cardArt[i].style.width = 288 * k; cardArt[i].style.height = 130 * k; c.Add(cardArt[i]);
            // 삽화 창 한가운데: 이 도술 자신의 그림(갈래 그림 위에 얹는다). 창 높이 130 에 맞춰 정사각 112
            cardIcon[i] = new VisualElement { pickingMode = PickingMode.Ignore }; cardIcon[i].style.position = Position.Absolute;
            cardIcon[i].style.left = (288 - 112) / 2f * k; cardIcon[i].style.top = (130 - 112) / 2f * k; cardIcon[i].style.width = 112 * k; cardIcon[i].style.height = 112 * k;
            cardIcon[i].style.display = DisplayStyle.None; cardArt[i].Add(cardIcon[i]);
            // 이름 띠(16,208, 288x44)
            cardName[i] = Line(c, 22); cardName[i].style.color = ink; cardName[i].style.position = Position.Absolute; cardName[i].style.left = 16 * k; cardName[i].style.top = 208 * k;
            cardName[i].style.width = 288 * k; cardName[i].style.height = 44 * k; cardName[i].style.unityTextAlign = TextAnchor.MiddleCenter; cardName[i].style.unityFontStyleAndWeight = FontStyle.Bold;
            // 효과 글(y 262~362)
            cardDesc[i] = Line(c, 15); cardDesc[i].style.color = new Color(0.2f, 0.17f, 0.14f); cardDesc[i].style.whiteSpace = WhiteSpace.Normal; cardDesc[i].style.position = Position.Absolute;
            cardDesc[i].style.left = 24 * k; cardDesc[i].style.top = 262 * k; cardDesc[i].style.width = 272 * k; cardDesc[i].style.height = 100 * k; cardDesc[i].style.unityTextAlign = TextAnchor.UpperCenter;
            cardKey[i] = Line(c, 16); cardKey[i].style.color = new Color(0.4f, 0.1f, 0.08f); cardKey[i].style.position = Position.Absolute; cardKey[i].style.bottom = 8; cardKey[i].style.left = 0; cardKey[i].style.width = w; cardKey[i].style.unityTextAlign = TextAnchor.MiddleCenter; cardKey[i].text = (i + 1).ToString();
            c.RegisterCallback<ClickEvent>(ev => { if (Hud.CardPick != null) Hud.CardPick(idx); });
            cardEl[i] = c; cardsRow.Add(c);
        }
        rerollBtn = new VisualElement { pickingMode = PickingMode.Position }; Panel(rerollBtn); rerollBtn.style.marginTop = 18;
        rerollLabel = Line(rerollBtn, 18); rerollBtn.RegisterCallback<ClickEvent>(ev => { if (Hud.CardRerollNow != null) Hud.CardRerollNow(); });
        cardsBox.Add(rerollBtn);
        root.Add(cardsBox);
    }
    void RefreshDosulCards()
    {
        if (cardsBox == null) return;
        bool on = Hud.CardNames != null;
        cardsBox.style.display = on ? DisplayStyle.Flex : DisplayStyle.None;
        if (!on) { lastCards = null; return; }
        string key = string.Join("|", Hud.CardNames) + Hud.CardReroll;
        if (key == lastCards) return;
        lastCards = key;
        cardsTitle.text = Hud.CardRound == 0 ? "첫 도술 — 하나를 고른다" : "도술 — 하나를 고른다";
        for (int i = 0; i < 3; i++)
        {
            bool has = i < Hud.CardNames.Length;
            cardEl[i].style.display = has ? DisplayStyle.Flex : DisplayStyle.None;
            if (!has) continue;
            cardName[i].text = Hud.CardNames[i]; cardDesc[i].text = Hud.CardDescs[i];
            string br = Hud.CardMarks[i] == "↑" ? "bureum" : Hud.CardMarks[i] == "●" ? "jul" : "eolluk";   // 갈래 → 그림 이름
            var big = First10.Whole("branch_" + br + "_big"); var artImg = First10.Whole("skill_card_art_" + br);
            cardBadge[i].style.backgroundImage = big != null ? new StyleBackground(big) : new StyleBackground();
            cardArt[i].style.backgroundImage = artImg != null ? new StyleBackground(artImg) : new StyleBackground();
            cardMark[i].text = big != null ? "" : Hud.CardMarks[i];   // 그림이 없을 때만 글자 기호
            var ico = DosulArt(Hud.CardNames[i]);   // 도술 그림이 없으면 칸을 숨겨 옛 카드 모양 그대로
            cardIcon[i].style.display = ico != null ? DisplayStyle.Flex : DisplayStyle.None;
            cardIcon[i].style.backgroundImage = ico != null ? new StyleBackground(ico) : new StyleBackground();
        }
        rerollBtn.style.display = string.IsNullOrEmpty(Hud.CardReroll) ? DisplayStyle.None : DisplayStyle.Flex;
        rerollLabel.text = Hud.CardReroll ?? "";
    }

    /// <summary>아래쪽 기술 줄: 가운데 아래에 무기 / E 천도 / R 파혼 / Q 끌기 / 피하기 충전 칸</summary>
    void BuildSkillBar()
    {
        skillBar = new VisualElement { name = "skillbar", pickingMode = PickingMode.Ignore };
        skillBar.style.position = Position.Absolute; skillBar.style.left = 0; skillBar.style.right = 0; skillBar.style.bottom = 14;
        skillBar.style.flexDirection = FlexDirection.Row; skillBar.style.justifyContent = Justify.Center;
        root.Add(skillBar);
        weaponLabel = Slot("무기"); Slot("E 천도"); Slot("R 파혼"); pullLabel = Slot("Q 끌기");
        // 피하기: 글자 + 충전 칸(켜진 칸 = 지금 쓸 수 있는 횟수)
        var d = new VisualElement { pickingMode = PickingMode.Ignore }; Panel(d);
        d.style.flexDirection = FlexDirection.Row; d.style.alignItems = Align.Center; d.style.marginLeft = 6;
        dodgeLabel = Line(d, 16); dodgeLabel.text = "Space 피하기";
        pips = new VisualElement[Mathf.Max(1, Balance.DODGE_CHARGES)];
        for (int i = 0; i < pips.Length; i++)
        {
            var p = new VisualElement { pickingMode = PickingMode.Ignore };
            p.style.width = 12; p.style.height = 12; p.style.marginLeft = 4; p.style.rotate = new Rotate(45f);
            d.Add(p); pips[i] = p;
        }
        skillBar.Add(d);
    }

    // ---- 처음 5분 안내 띠: 하단 중앙, 스킬바 위. 키 그림 + 글자 22px, 행동하면 초록 체크 ----
    VisualElement guideBox, guideKeyBox; Label guideKey, guideText, guideTick; string lastGuide;
    // ---- 보스 체력바(위 가운데) · 지역 진입 알림 --------------------------------------
    VisualElement bossBox, bossFill, areaBox, questBox, expBox, expFill, castBox, castFill; Label expLabel, sayLabel, subSfx, subCutMem, subMemLine, subNpc, subNpcName, interactLabel; VisualElement subNpcBand, interactBar; Label questTitle, questBody; string lastQuest; Label bossName, areaLabel, areaSub;
    void BuildBossArea()
    {
        bossBox = new VisualElement { name = "boss", pickingMode = PickingMode.Ignore };
        bossBox.style.position = Position.Absolute; bossBox.style.left = 0; bossBox.style.right = 0; bossBox.style.top = U(64);
        bossBox.style.alignItems = Align.Center; bossBox.style.display = DisplayStyle.None;
        questBox = new VisualElement { name = "quest", pickingMode = PickingMode.Ignore };   // 퀘스트 추적: 우상(명세 §1), 시계 고리 아래
        questBox.style.position = Position.Absolute; questBox.style.width = U(300); questBox.style.right = U(24); questBox.style.top = U(330);   // 우상: 미니맵·시계 고리 아래(실제 높이는 매 프레임 맞춘다) questBox.style.display = DisplayStyle.None;
        Panel(questBox); questTitle = Line(questBox, 16); questTitle.style.color = new Color(0.9f, 0.78f, 0.45f); questBody = Line(questBox, 15); questBody.style.whiteSpace = WhiteSpace.Normal;
        root.Add(questBox);
        expBox = new VisualElement { name = "exp", pickingMode = PickingMode.Ignore };   // 경험치(품계) 막대: 화면 맨 아래 가는 띠
        expBox.style.position = Position.Absolute; expBox.style.left = 0; expBox.style.right = 0; expBox.style.bottom = 0; expBox.style.height = U(10); expBox.style.display = DisplayStyle.None;
        expBox.style.backgroundColor = new Color(0f, 0f, 0f, 0.5f);
        expFill = new VisualElement { pickingMode = PickingMode.Ignore }; expFill.style.height = Length.Percent(100); expFill.style.backgroundColor = new Color(0.17f, 0.14f, 0.13f);   // 먹빛 막대(「명부의 일」). 끝의 붉은 인은 아래 expCap. 청록·주황은 쓰지 않는다(명세 first-5-minutes v2)
        { var cap = new VisualElement { pickingMode = PickingMode.Ignore }; cap.style.position = Position.Absolute; cap.style.right = 0; cap.style.top = 0; cap.style.bottom = 0; cap.style.width = U(4); cap.style.backgroundColor = new Color(0.66f, 0.12f, 0.12f); expFill.Add(cap); }   // 막대 끝의 붉은 인
        expBox.Add(expFill); root.Add(expBox);
        expLabel = Line(root, 13); expLabel.style.position = Position.Absolute; expLabel.style.left = U(24); expLabel.style.bottom = U(14); expLabel.style.color = new Color(0.8f, 0.9f, 0.9f); expLabel.style.display = DisplayStyle.None;
        // 천도 시전 막대: 화면 높이 72% 자리(스킬바·처결 카드 위, 도술 칸을 가리지 않게)
        castBox = new VisualElement { name = "cast", pickingMode = PickingMode.Ignore };
        castBox.style.position = Position.Absolute; castBox.style.left = Length.Percent(50); castBox.style.top = Length.Percent(72);
        castBox.style.width = U(300); castBox.style.height = U(16); castBox.style.marginLeft = -U(150); castBox.style.display = DisplayStyle.None;
        castBox.style.backgroundColor = new Color(0f, 0f, 0f, 0.7f);
        castFill = new VisualElement { pickingMode = PickingMode.Ignore }; castFill.style.height = Length.Percent(100); castFill.style.backgroundColor = ChasaPalette.CheondoGlow;
        castBox.Add(castFill); root.Add(castBox);
        // 짧은 한마디(예전 IMGUI 화면 가운데 글): 시전이 끊겼다·쓰러졌다 같은 알림
        sayLabel = Line(root, 24); sayLabel.style.position = Position.Absolute; sayLabel.style.left = 0; sayLabel.style.right = 0; sayLabel.style.top = Length.Percent(28);
        sayLabel.style.unityTextAlign = TextAnchor.MiddleCenter; sayLabel.style.color = Color.white; sayLabel.style.display = DisplayStyle.None;
        // 자막 넷: 소리 자막(아래 가운데, 흐린 흰), 컷신 기억 줄(보랏빛 기울임), 천도 뒤 기억 한 줄(위쪽 보랏빛), 산 사람 대사(한지색 글자 + 먹색 띠)
        subSfx = SubLine(root, 18, new Color(0.85f, 0.85f, 0.85f, 0.85f), false); subSfx.style.bottom = U(150);
        subCutMem = SubLine(root, 22, new Color(0.79f, 0.69f, 1f), true); subCutMem.style.bottom = U(230);
        subMemLine = SubLine(root, 22, new Color(0.79f, 0.69f, 1f), true); subMemLine.style.top = Length.Percent(18);
        // F 안내: 하단 중앙 "[F] 줍기". 만져 보기는 아래 막대가 2초 동안 찬다
        interactLabel = Line(root, 18); interactLabel.style.position = Position.Absolute; interactLabel.style.left = Length.Percent(50); interactLabel.style.width = U(300); interactLabel.style.marginLeft = -U(150);
        interactLabel.style.bottom = U(150); interactLabel.style.unityTextAlign = TextAnchor.MiddleCenter; interactLabel.style.color = new Color(0.953f, 0.906f, 0.827f);
        interactLabel.style.backgroundColor = new Color(0.06f, 0.05f, 0.05f, 0.6f); interactLabel.style.display = DisplayStyle.None;
        interactBar = new VisualElement { pickingMode = PickingMode.Ignore }; interactBar.style.height = U(5); interactBar.style.backgroundColor = new Color(1f, 0.82f, 0.3f); interactBar.style.alignSelf = Align.FlexStart; interactLabel.Add(interactBar);
        // 들은 말 창(기획 npc-interaction-spec §3): 하단 중앙, 이름 탭 + '(들린 말)' + 본문. 선택지 없음, 게임은 멈추지 않는다
        subNpcBand = new VisualElement { pickingMode = PickingMode.Ignore };
        subNpcBand.style.position = Position.Absolute; subNpcBand.style.left = Length.Percent(50); subNpcBand.style.width = U(1152); subNpcBand.style.marginLeft = -U(576); subNpcBand.style.bottom = U(190);
        subNpcBand.style.alignItems = Align.Center; subNpcBand.style.backgroundColor = new Color(0.06f, 0.05f, 0.05f, 0.7f); subNpcBand.style.display = DisplayStyle.None;
        subNpcBand.style.paddingTop = U(10); subNpcBand.style.paddingBottom = U(16);
        subNpcName = Line(subNpcBand, 17); subNpcName.style.color = new Color(1f, 0.82f, 0.3f); subNpcName.style.unityFontStyleAndWeight = FontStyle.Bold;
        var hear = Line(subNpcBand, 11); hear.text = "(들린 말)"; hear.style.color = new Color(0.6f, 0.58f, 0.55f);
        subNpc = Line(subNpcBand, 20); subNpc.style.color = new Color(0.953f, 0.906f, 0.827f); subNpc.style.whiteSpace = WhiteSpace.Normal; subNpc.style.unityTextAlign = TextAnchor.MiddleCenter;
        subNpc.style.paddingTop = U(6); subNpc.style.paddingLeft = U(40); subNpc.style.paddingRight = U(40); root.Add(subNpcBand);
        bossName = Line(bossBox, 24); bossName.style.color = new Color(0.95f, 0.9f, 0.8f); bossName.style.marginBottom = U(6);
        var frame = new VisualElement { pickingMode = PickingMode.Ignore };   // 틀: 어두운 판에 붉은 채움
        frame.style.width = U(960); frame.style.height = U(20); frame.style.backgroundColor = new Color(0.05f, 0.04f, 0.05f, 0.85f);
        frame.style.borderTopWidth = 2; frame.style.borderBottomWidth = 2; frame.style.borderLeftWidth = 2; frame.style.borderRightWidth = 2;
        var bc = new Color(0.78f, 0.66f, 0.45f); frame.style.borderTopColor = bc; frame.style.borderBottomColor = bc; frame.style.borderLeftColor = bc; frame.style.borderRightColor = bc;
        bossFill = new VisualElement { pickingMode = PickingMode.Ignore }; bossFill.style.height = Length.Percent(100); bossFill.style.backgroundColor = new Color(0.72f, 0.16f, 0.14f);
        frame.Add(bossFill);
        // 개편 P0-2(보스 맺힘 금): 아트 틀·채움·금 그림이 다 있으면 그림으로 바꾼다. 없으면 위의 색 막대가 그대로 돈다(그림 없이도 돈다)
        if (OTex("gyeol/boss_gyeol_row_frame") != null && OTex("gyeol/boss_gyeol_row_fill") != null && OTex("gyeol/gyeol_crack_stage1_L") != null)
        {
            frame.Clear(); bossFill = null;
            frame.style.backgroundColor = Color.clear;
            frame.style.borderTopWidth = 0; frame.style.borderBottomWidth = 0; frame.style.borderLeftWidth = 0; frame.style.borderRightWidth = 0;
            frame.style.width = U(960); frame.style.height = U(28);
            SetOImg(frame, "gyeol/boss_gyeol_row_frame");
            // 줄어든 자리 잔상(한지색): 채움보다 천천히 따라 내려온다 → 방금 얼마나 깎였는지 보인다
            bossGhostClip = OClip(U(952), U(20)); bossGhostClip.Add(OImg("gyeol/boss_gyeol_row_ghost", U(952), U(20))); frame.Add(bossGhostClip);
            bossFillClip = OClip(U(952), U(20)); bossFillClip.Add(OImg("gyeol/boss_gyeol_row_fill", U(952), U(20))); frame.Add(bossFillClip);
            // 맺힘 0(무릎 꿇음): 채움 대신 금 간 빈 줄
            bossBroken = OImg("gyeol/boss_gyeol_row_broken", U(952), U(20)); bossBroken.style.position = Position.Absolute; bossBroken.style.left = U(4); bossBroken.style.top = U(4); bossBroken.style.display = DisplayStyle.None; frame.Add(bossBroken);
            // 금: 아트는 96×22(일반 혼 막대 크기)라서 960×28 막대에는 10장을 이어 붙여 덮는다(가로는 그대로 96, 세로만 막대 높이에 맞춤)
            bossCrack = new VisualElement[10];
            for (int i = 0; i < bossCrack.Length; i++)
            {
                var c = new VisualElement { pickingMode = PickingMode.Ignore };
                c.style.position = Position.Absolute; c.style.left = U(96) * i; c.style.top = 0; c.style.width = U(96); c.style.height = U(28);
                c.style.display = DisplayStyle.None; frame.Add(c); bossCrack[i] = c;
            }
        }
        bossBox.Add(frame); root.Add(bossBox);
        areaBox = new VisualElement { name = "area", pickingMode = PickingMode.Ignore };
        areaBox.style.position = Position.Absolute; areaBox.style.left = 0; areaBox.style.right = 0; areaBox.style.top = U(180);
        areaBox.style.alignItems = Align.Center; areaBox.style.display = DisplayStyle.None;
        areaLabel = Line(areaBox, 40); areaLabel.style.color = new Color(0.96f, 0.92f, 0.82f);
        areaLabel.style.backgroundColor = new Color(0f, 0f, 0f, 0.45f); areaLabel.style.paddingLeft = U(40); areaLabel.style.paddingRight = U(40); areaLabel.style.paddingTop = U(8); areaLabel.style.paddingBottom = U(8);
        areaSub = Line(areaBox, 20); areaSub.style.color = new Color(0.85f, 0.8f, 0.7f); areaSub.style.marginTop = U(6);   // 아래 부제: 시각
        areaBox.Add(areaLabel); areaBox.Add(areaSub); root.Add(areaBox);
    }
    Label SubLine(VisualElement parent, int size, Color c, bool italic)
    {
        var l = Line(parent, size); l.style.position = Position.Absolute; l.style.left = Length.Percent(15); l.style.right = Length.Percent(15);
        l.style.whiteSpace = WhiteSpace.Normal; l.style.unityTextAlign = TextAnchor.MiddleCenter; l.style.color = c; l.style.display = DisplayStyle.None;
        if (italic) l.style.unityFontStyleAndWeight = FontStyle.Italic;
        return l;
    }
    static void ShowSub(Label l, string text, float alpha)
    {
        bool on = text != null && alpha > 0.01f; l.style.display = on ? DisplayStyle.Flex : DisplayStyle.None;
        if (on) { l.text = text; l.style.opacity = alpha; }
    }
    void RefreshBossArea()
    {
        if (bossBox == null) return;
        expBox.style.display = Hud.ShowExp ? DisplayStyle.Flex : DisplayStyle.None; expLabel.style.display = Hud.ShowExp ? DisplayStyle.Flex : DisplayStyle.None;
        if (Hud.ShowExp) { expFill.style.width = Length.Percent(Mathf.Clamp01(Hud.ExpRatio) * 100f); expLabel.text = "명부의 일  " + Hud.Rank + "품"; }
        ShowSub(subSfx, Hud.SubSfx, 1f); ShowSub(subCutMem, Hud.SubCutMemory, 1f); ShowSub(subMemLine, Hud.SubMemLine, Hud.SubMemLineAlpha);
        bool hasIx = !string.IsNullOrEmpty(Hud.InteractLabel) && !Ko.TouchUI;   // 폰은 버튼 글자가 대신한다
        interactLabel.style.display = hasIx ? DisplayStyle.Flex : DisplayStyle.None;
        if (hasIx) { interactLabel.text = "[F] " + Hud.InteractLabel; interactBar.style.width = Length.Percent(100f * Hud.InteractRatio); interactBar.style.display = Hud.InteractRatio > 0f ? DisplayStyle.Flex : DisplayStyle.None; }
        bool npcSub = Hud.SubNpc != null && Hud.SubNpcAlpha > 0.01f; subNpcBand.style.display = npcSub ? DisplayStyle.Flex : DisplayStyle.None;
        if (npcSub) { subNpc.text = Hud.SubNpc; subNpcBand.style.opacity = Hud.SubNpcAlpha; bool hasName = !string.IsNullOrEmpty(Hud.SubNpcName); subNpcName.text = hasName ? Hud.SubNpcName : ""; subNpcName.style.display = hasName ? DisplayStyle.Flex : DisplayStyle.None; }
        bool casting = Hud.CastRatio >= 0f; castBox.style.display = casting ? DisplayStyle.Flex : DisplayStyle.None;
        if (casting) castFill.style.width = Length.Percent(Mathf.Clamp01(Hud.CastRatio) * 100f);
        bool say = Hud.SayText != null; sayLabel.style.display = say ? DisplayStyle.Flex : DisplayStyle.None; if (say) sayLabel.text = Hud.SayText;
        bool quest = Hud.QuestTitle != null; questBox.style.display = quest ? DisplayStyle.Flex : DisplayStyle.None;
        if (quest) { string qk = Hud.QuestTitle + "|" + string.Join("|", Hud.QuestLines ?? new string[0]); if (qk != lastQuest) { lastQuest = qk; questTitle.text = Hud.QuestTitle; questBody.text = string.Join("\n", Hud.QuestLines ?? new string[0]); } }
        bool boss = Hud.BossName != null; bossBox.style.display = boss ? DisplayStyle.Flex : DisplayStyle.None;
        if (boss) { bossName.text = Hud.BossName + (Hud.BossKneel ? "  — 무릎 꿇음" : ""); RefreshBossBar(); }
        bool area = Hud.AreaText != null && Hud.AreaAlpha > 0.01f; areaBox.style.display = area ? DisplayStyle.Flex : DisplayStyle.None;
        if (area) { areaLabel.text = Hud.AreaText; areaSub.text = Hud.ClockLabel ?? ""; areaBox.style.opacity = Hud.AreaAlpha; }
    }

    /// <summary>보스 맺힘 줄 갱신. 숫자 대신 '금'이 간다: 66%·33%·10% 이하에서 한 단계씩 금이 늘고, 0 이면 금 간 빈 줄이 된다</summary>
    void RefreshBossBar()
    {
        float r = Mathf.Clamp01(Hud.BossRatio);
        if (bossFillClip == null) { bossFill.style.width = Length.Percent(r * 100f); return; }   // 그림이 없으면 옛 색 막대
        bossFillClip.style.width = U(952) * r;
        // 잔상: 줄어들면 천천히(초당 40%) 따라 내려온다. 채워지면 즉시 맞춘다
        bossGhostRatio = r >= bossGhostRatio ? r : Mathf.Max(r, bossGhostRatio - 0.4f * Time.unscaledDeltaTime);
        bossGhostClip.style.width = U(952) * bossGhostRatio;
        bool broken = r <= 0f;
        bossFillClip.style.display = broken ? DisplayStyle.None : DisplayStyle.Flex;
        bossBroken.style.display = broken ? DisplayStyle.Flex : DisplayStyle.None;
        int st = broken ? 0 : CrackStage(r);   // 깨진 줄은 자기 그림에 금이 이미 있어 덧그리지 않는다
        if (st != bossCrackStage)
        {
            bossCrackStage = st;
            var t = st > 0 ? OTex("gyeol/gyeol_crack_stage" + st + "_L") : null;
            foreach (var c in bossCrack)
            {
                c.style.display = t != null ? DisplayStyle.Flex : DisplayStyle.None;
                if (t != null) c.style.backgroundImage = Background.FromTexture2D(t);
            }
        }
    }

    void BuildGuide()
    {
        guideBox = new VisualElement { name = "guide", pickingMode = PickingMode.Ignore };
        guideBox.style.position = Position.Absolute; guideBox.style.left = 0; guideBox.style.right = 0; guideBox.style.bottom = U(190);
        guideBox.style.alignItems = Align.Center; guideBox.style.display = DisplayStyle.None;
        var band = new VisualElement { pickingMode = PickingMode.Ignore };
        band.style.flexDirection = FlexDirection.Row; band.style.alignItems = Align.Center; band.style.height = U(56);
        band.style.paddingLeft = U(20); band.style.paddingRight = U(24); band.style.backgroundColor = new Color(0.04f, 0.035f, 0.03f, 0.85f);   // 낮에도 묻히지 않게 먹판을 진하게(아트 hint_plate 9칸 슬라이스는 UI Toolkit 슬라이스 속성이 필요해 다음에)
        band.style.borderTopLeftRadius = 6; band.style.borderTopRightRadius = 6; band.style.borderBottomLeftRadius = 6; band.style.borderBottomRightRadius = 6;
        var plate = UiTex("hint_plate");   // 아트 안내 글판(64×32, 9칸: 모서리 20,14,20,14 는 늘이지 않고 가운데만 늘인다)
        if (plate != null)
        {
            band.style.backgroundImage = Background.FromTexture2D(plate); band.style.backgroundColor = Color.clear;
            band.style.unitySliceLeft = 20; band.style.unitySliceRight = 20; band.style.unitySliceTop = 14; band.style.unitySliceBottom = 14;
            band.style.paddingLeft = U(28); band.style.paddingRight = U(32);
        }
        guideKeyBox = new VisualElement { pickingMode = PickingMode.Ignore };   // 키 그림: 둥근 밝은 판 + 글자
        guideKeyBox.style.height = U(40); guideKeyBox.style.minWidth = U(40); guideKeyBox.style.marginRight = U(14); guideKeyBox.style.paddingLeft = U(10); guideKeyBox.style.paddingRight = U(10);
        guideKeyBox.style.backgroundColor = new Color(0.92f, 0.9f, 0.82f, 1f); guideKeyBox.style.justifyContent = Justify.Center;
        guideKeyBox.style.borderTopLeftRadius = 6; guideKeyBox.style.borderTopRightRadius = 6; guideKeyBox.style.borderBottomLeftRadius = 6; guideKeyBox.style.borderBottomRightRadius = 6;
        guideKey = Line(guideKeyBox, 16); guideKey.style.color = new Color(0.1f, 0.09f, 0.08f); guideKey.style.unityTextAlign = TextAnchor.MiddleCenter;
        guideText = Line(band, 22);
        guideTick = Line(band, 22); guideTick.text = "  확인"; guideTick.style.color = new Color(0.45f, 0.95f, 0.55f); guideTick.style.display = DisplayStyle.None;
        band.Insert(0, guideKeyBox); guideBox.Add(band); root.Add(guideBox);
    }
    void RefreshGuide()
    {
        if (guideBox == null) return;
        bool show = Hud.GuideText != null;
        guideBox.style.display = show ? DisplayStyle.Flex : DisplayStyle.None;
        if (!show) { lastGuide = null; return; }
        if (lastGuide != Hud.GuideText) { lastGuide = Hud.GuideText; guideText.text = Hud.GuideText; guideBox.style.opacity = 0f; guideFade = 0f; }   // 새 안내는 0.25초 페이드 인
        guideFade = Mathf.MoveTowards(guideFade, 1f, Time.unscaledDeltaTime / 0.25f);
        bool hasKey = !string.IsNullOrEmpty(Hud.GuideKey);
        guideKeyBox.style.display = hasKey ? DisplayStyle.Flex : DisplayStyle.None; if (hasKey) guideKey.text = Hud.GuideKey;
        guideTick.style.display = Hud.GuideCheck ? DisplayStyle.Flex : DisplayStyle.None;
        float blink = Hud.GuideRemind ? 0.5f + 0.5f * Mathf.Abs(Mathf.Sin(Time.unscaledTime * 8f)) : 1f;   // 20초 안 하면 깜빡
        guideBox.style.opacity = guideFade * blink;
    }
    float guideFade;

    // ---- 첫 처결 카드: 스킬바 위 가운데에 같은 크기·같은 밝기의 카드 둘(천도·파혼). 정답을 말하지 않는다 ----
    VisualElement cardRow;
    void BuildCards()
    {
        cardRow = new VisualElement { name = "judge-cards", pickingMode = PickingMode.Ignore };
        cardRow.style.position = Position.Absolute; cardRow.style.left = 0; cardRow.style.right = 0; cardRow.style.bottom = U(150);
        cardRow.style.flexDirection = FlexDirection.Row; cardRow.style.justifyContent = Justify.Center; cardRow.style.display = DisplayStyle.None;
        cardRow.Add(Card("E", "천도", "보내기", new Color(0.12f, 0.45f, 0.45f, 0.92f), "↑", false));
        cardRow.Add(Card("R", "파혼", "깨뜨리기", new Color(0.62f, 0.25f, 0.12f, 0.92f), "×", true));
        root.Add(cardRow);
    }
    /// <summary>mark: 색 말고 모양으로도 구분(↑ 천도 = 오르는 불꽃·실선·둥근 모서리 / × 파혼 = 깨진 조각·두꺼운 각진 테두리). 색약 대응(명세 §9-2)</summary>
    VisualElement rimIcon;   // 천도 카드의 금테(이름혼일 때만 보임)
    VisualElement Card(string key, string name, string sub, Color bg, string mark, bool jagged)
    {
        var c = new VisualElement { pickingMode = PickingMode.Ignore };
        c.style.width = U(280); c.style.height = U(96); c.style.marginLeft = U(10); c.style.marginRight = U(10);
        c.style.backgroundColor = bg; c.style.justifyContent = Justify.Center; c.style.alignItems = Align.Center;
        var edge = new Color(0.95f, 0.85f, 0.55f, 0.9f);
        float bw = jagged ? 5f : 2f; c.style.borderTopWidth = bw; c.style.borderBottomWidth = bw; c.style.borderLeftWidth = bw; c.style.borderRightWidth = bw;
        c.style.borderTopColor = edge; c.style.borderBottomColor = edge; c.style.borderLeftColor = edge; c.style.borderRightColor = edge;
        float rad = jagged ? 0f : 14f; c.style.borderTopLeftRadius = rad; c.style.borderTopRightRadius = rad; c.style.borderBottomLeftRadius = rad; c.style.borderBottomRightRadius = rad;
        // 아트 처결 카드(PR #47, 280×96): 틀·보상 그림이 이미 그려져 있다. 키는 칸(98,14, 36×24)에, 글자는 오른쪽(144~)에 얹는다.
        // 천도는 실선·둥근 모서리, 파혼은 점선·톱니라 색 없이도 갈린다(명세 §9-2). 두 카드의 평균 밝기를 맞춰 뒀으니 색을 더 입히지 않는다
        var cardArt = First10.Whole(jagged ? "exec_card_pahon" : "exec_card_tendo");
        if (cardArt != null)
        {
            c.style.backgroundColor = Color.clear; c.style.backgroundImage = new StyleBackground(cardArt);
            c.style.borderTopWidth = 0; c.style.borderBottomWidth = 0; c.style.borderLeftWidth = 0; c.style.borderRightWidth = 0;
            c.style.justifyContent = Justify.FlexStart; c.style.alignItems = Align.FlexStart;
            var k = Line(c, 18); k.text = key; k.style.position = Position.Absolute; k.style.left = U(98); k.style.top = U(14); k.style.width = U(36); k.style.height = U(24); k.style.unityTextAlign = TextAnchor.MiddleCenter; k.style.color = new Color(0.1f, 0.08f, 0.06f);
            var nt = Line(c, 24); nt.text = name; nt.style.position = Position.Absolute; nt.style.left = U(144); nt.style.top = U(12);
            var ns = Line(c, 18); ns.text = sub; ns.style.position = Position.Absolute; ns.style.left = U(144); ns.style.top = U(48);
            if (!jagged)
            {
                rimIcon = new VisualElement { pickingMode = PickingMode.Ignore }; var rim0 = First10.Whole("reward_gold_rim");
                if (rim0 != null) { rimIcon.style.backgroundImage = new StyleBackground(rim0); rimIcon.style.position = Position.Absolute; rimIcon.style.left = U(12); rimIcon.style.top = U(20); rimIcon.style.width = U(56); rimIcon.style.height = U(56); rimIcon.style.display = DisplayStyle.None; c.Add(rimIcon); }
            }
            return c;
        }
        var t = Line(c, 24); t.text = mark + " [" + key + "] " + name; t.style.unityTextAlign = TextAnchor.MiddleCenter;
        var s2 = Line(c, 18); s2.text = sub; s2.style.unityTextAlign = TextAnchor.MiddleCenter;
        // 고르기 전에 보상이 보인다(M5): 천도=혼불+기억, 파혼=엽전+얼룩. 같은 크기·밝기. 이름혼이면 기억 아이콘에 금테
        var icon = First10.Whole(jagged ? "reward_pahon" : "reward_tendo");
        if (icon != null)
        {
            var iv = new VisualElement { pickingMode = PickingMode.Ignore }; iv.style.position = Position.Absolute; iv.style.left = U(12); iv.style.top = U(20);
            iv.style.width = U(56); iv.style.height = U(56); iv.style.backgroundImage = new StyleBackground(icon); c.Add(iv);
            if (!jagged) { rimIcon = new VisualElement { pickingMode = PickingMode.Ignore }; var rim = First10.Whole("reward_gold_rim"); if (rim != null) rimIcon.style.backgroundImage = new StyleBackground(rim); rimIcon.style.width = U(56); rimIcon.style.height = U(56); rimIcon.style.display = DisplayStyle.None; iv.Add(rimIcon); }
        }
        return c;
    }

    // ---- 스킬바 8칸(기획 표준 v1.1): [Q 견인][1][2][3][4][E 천도][R 파혼][H 회복약], 칸 64px·간격 8px·아래 40px ------------
    const int BarN = 8;
    bool newSlots; VisualElement[] bHot = new VisualElement[BarN]; string[] bBg = new string[BarN];   // 개편 칸 그림을 썼나 / 천도·파혼 겉 빛 / 칸마다 지금 깔린 바탕 이름(바뀔 때만 갈아 끼운다)
    VisualElement[] bSlot = new VisualElement[BarN], bIcon = new VisualElement[BarN], bShade = new VisualElement[BarN]; Label[] bKey = new Label[BarN], bTxt = new Label[BarN], bSec = new Label[BarN];
    VisualElement[] bPips = new VisualElement[0]; float pullMax = 1f; VisualElement bPipRow; Label bWeapon;
    static readonly string[] BarKeys = { "Q", "1", "2", "3", "4", "E", "R", "H" };
    static readonly string[] BarNames = { "끌기", "", "", "", "", "↑천도", "×파혼", "약" };

    void BuildSlots()
    {
        if (UiTex("hud_slot_normal") == null) return;   // 그림 없으면 옛 기술 줄(skillBar)만 쓴다
        slotBar = new VisualElement { name = "skill-slots", pickingMode = PickingMode.Ignore };
        slotBar.style.position = Position.Absolute; slotBar.style.left = 0; slotBar.style.right = 0; slotBar.style.bottom = U(40 - 4);
        slotBar.style.alignItems = Align.Center;
        root.Add(slotBar);
        // 회피 충전 점(스킬바 바로 위 가운데) + 무기 이름
        bPipRow = new VisualElement { pickingMode = PickingMode.Ignore }; bPipRow.style.flexDirection = FlexDirection.Row; bPipRow.style.alignItems = Align.Center; bPipRow.style.marginBottom = U(6);
        bWeapon = Line(bPipRow, 14); bWeapon.style.marginRight = 10;
        bPips = new VisualElement[Mathf.Max(1, Balance.DODGE_CHARGES)];
        for (int i = 0; i < bPips.Length; i++) { var p = Img("hud_dodge_pip_empty", U(14), U(14)); p.style.marginLeft = 3; p.style.marginRight = 3; bPipRow.Add(p); bPips[i] = p; }
        var sp = Line(bPipRow, 14); sp.text = "Space 피하기"; sp.style.marginLeft = 8; sp.style.opacity = 0.8f;
        slotBar.Add(bPipRow);
        var row = new VisualElement { pickingMode = PickingMode.Ignore }; row.style.flexDirection = FlexDirection.Row; slotBar.Add(row);
        // 개편 P0-3: 기술·천도·파혼 칸이 한 덩어리 먹판(plate_cluster, 9조각 24) 위에 놓인다. 칸 크기는 전부 80²(천도·파혼도 같다 = 한쪽이 기본값처럼 안 보이게)
        newSlots = OTex("hud/slot_skill_ready") != null && OTex("hud/slot_skill_empty") != null && OTex("hud/slot_skill_cool") != null
                && OTex("hud/slot_tendo_on") != null && OTex("hud/slot_tendo_off") != null && OTex("hud/slot_pahon_on") != null && OTex("hud/slot_pahon_off") != null;
        if (newSlots && OTex("hud/plate_cluster") != null)
        {
            row.style.backgroundImage = Background.FromTexture2D(OTex("hud/plate_cluster"));
            row.style.unitySliceLeft = 24; row.style.unitySliceRight = 24; row.style.unitySliceTop = 24; row.style.unitySliceBottom = 24;
            row.style.paddingLeft = U(14); row.style.paddingRight = U(14); row.style.paddingTop = U(10); row.style.paddingBottom = U(10);
        }
        float slotW = newSlots ? 80f : 72f, icoOff = 8f, icoW = newSlots ? 64f : 56f;
        for (int i = 0; i < BarN; i++)
        {
            var b = newSlots ? OImg("hud/slot_skill_ready", U(slotW), U(slotW)) : Img("hud_slot_normal", U(72), U(72)); b.style.marginLeft = U(4); b.style.marginRight = U(4);   // 옛 그림은 그림자 4px 포함 72 → 칸 64 + 간격 8
            var ic = new VisualElement { pickingMode = PickingMode.Ignore }; ic.style.position = Position.Absolute; ic.style.left = U(icoOff); ic.style.top = U(icoOff); ic.style.width = U(icoW); ic.style.height = U(icoW);
            var shade = new VisualElement { pickingMode = PickingMode.Ignore };   // 쿨타임 어둠 판: 아래에서부터 남은 비율만큼 덮는다
            shade.style.position = Position.Absolute; shade.style.left = U(4); shade.style.right = U(8); shade.style.bottom = U(8); shade.style.height = 0; shade.style.backgroundColor = new Color(0f, 0f, 0.03f, 0.62f);
            var key = Line(b, 14); key.text = BarKeys[i]; key.style.position = Position.Absolute; key.style.left = U(8); key.style.top = U(4);
            var txt = Line(b, 17); txt.text = BarNames[i]; txt.style.position = Position.Absolute; txt.style.left = 0; txt.style.right = U(4); txt.style.top = U(24); txt.style.unityTextAlign = TextAnchor.MiddleCenter;
            var sec = Line(b, 20); sec.style.position = Position.Absolute; sec.style.left = 0; sec.style.right = U(4); sec.style.top = U(22); sec.style.unityTextAlign = TextAnchor.MiddleCenter;
            b.Insert(0, ic); b.Insert(1, shade);
            if (newSlots && (i == 5 || i == 6))   // 천도·파혼 칸은 누르는 순간 겉으로 8px 번지는 빛(_hot 96²)을 가진다. 평소엔 숨김
            {
                var hot = OImg(i == 5 ? "hud/slot_tendo_hot" : "hud/slot_pahon_hot", U(96), U(96)); hot.style.position = Position.Absolute; hot.style.left = -U(8); hot.style.top = -U(8); hot.style.display = DisplayStyle.None;
                b.Insert(0, hot); bHot[i] = hot;
            }
            row.Add(b); bSlot[i] = b; bIcon[i] = ic; bShade[i] = shade; bKey[i] = key; bTxt[i] = txt; bSec[i] = sec;
        }
    }

    /// <summary>칸 바탕 그림 갈아 끼우기(같으면 건드리지 않는다)</summary>
    void SetBg(int i, string name)
    {
        if (bBg[i] == name) return;
        bBg[i] = name; SetOImg(bSlot[i], "hud/" + name);
    }

    void SetSlot(int i, bool enabled, float cd, float sec, Texture2D t)
    {
        bIcon[i].style.backgroundImage = t != null ? new StyleBackground(Background.FromTexture2D(t)) : new StyleBackground(StyleKeyword.None);
        bTxt[i].style.display = t == null ? DisplayStyle.Flex : DisplayStyle.None;   // 그림이 없는 칸(천도·파혼·약, 그림 없는 도술)은 글자로
        bSlot[i].style.opacity = enabled ? 1f : 0.4f;
        bShade[i].style.height = cd > 0f ? U(56) * Mathf.Clamp01(cd) : 0f;
        bSec[i].text = sec > 0.05f ? Mathf.CeilToInt(sec).ToString() : "";
    }

    /// <summary>옛 아트팀 도술 그림(ui/icon_skill_*). 개편 그림이 없을 때만 쓰는 안전장치</summary>
    static Texture2D OldSkillArt(string name) { string id = SkillIcon(name); return id != null ? UiTex(id) : null; }

    void RefreshSlots()
    {
        if (slotBar == null) return;
        slotBar.style.display = Ko.TouchUI ? DisplayStyle.None : DisplayStyle.Flex;   // 폰은 터치 버튼이 맡는다
        if (Ko.TouchUI) return;
        pullMax = Mathf.Max(pullMax, Hud.PullCd);
        SetSlot(0, true, Hud.PullCd > 0.05f ? Hud.PullCd / pullMax : 0f, Hud.PullCd, newSlots ? OArt("btn", DosulIcons.QIcon(Hud.QName)) : null);   // Q 칸: 무기별 그림(없으면 옛 글자)
        if (!string.IsNullOrEmpty(Hud.QName)) bTxt[0].text = Hud.QName;   // 무기마다 Q 이름이 다르다(끌기·땅울림·세우기·꽂기·이름)
        for (int i = 0; i < 4; i++)
        {
            var sv = Hud.Slots[i]; bool has = sv.Name != null;
            SetSlot(1 + i, has, has ? sv.Cd : 0f, has ? sv.CdSec : 0f, has ? (DosulArt(sv.Name) ?? OldSkillArt(sv.Name)) : null);   // 개편 그림 → 옛 그림 → 글자 순
            bTxt[1 + i].text = "";
        }
        SetSlot(5, true, 0f, 0f, null); SetSlot(6, true, 0f, 0f, null);
        SetSlot(7, Hud.Heal > 0, 0f, 0f, null); bTxt[7].text = "약 " + Hud.Heal;
        if (newSlots)
        {
            // 칸 바탕: 기술은 쓸 수 있음/빈 칸(점선)/재사용 대기, 천도·파혼은 켜짐/꺼짐(처결할 혼이 없을 때). 꺼진 칸도 자리·크기는 그대로
            SetBg(0, Hud.PullCd > 0.05f ? "slot_skill_cool" : "slot_skill_ready");
            for (int i = 0; i < 4; i++) { var sv = Hud.Slots[i]; SetBg(1 + i, sv.Name == null ? "slot_skill_empty" : sv.Cd > 0f ? "slot_skill_cool" : "slot_skill_ready"); bSlot[1 + i].style.opacity = 1f; }
            bSlot[0].style.opacity = 1f;
            SetBg(5, Hud.TendoReady || Hud.CastRatio >= 0f ? "slot_tendo_on" : "slot_tendo_off"); bSlot[5].style.opacity = 1f;
            SetBg(6, Hud.PahonReady ? "slot_pahon_on" : "slot_pahon_off"); bSlot[6].style.opacity = 1f;
            SetBg(7, Hud.Heal > 0 ? "slot_skill_ready" : "slot_skill_empty"); bSlot[7].style.opacity = 1f;
            bHot[5].style.display = Hud.CastRatio >= 0f ? DisplayStyle.Flex : DisplayStyle.None;   // 천도 시전 중 겉 빛
            bTxt[5].text = ""; bTxt[6].text = "";   // 천도·파혼 칸의 모양(▲·✕)은 그림이 말한다. E·R 글자는 왼쪽 위 키 글자
        }
        bWeapon.text = "무기 " + Hud.WeaponName + " (Tab)";
        for (int i = 0; i < bPips.Length; i++) SetImg(bPips[i], Hud.DodgeCharges - i >= 0.999f ? "hud_dodge_pip_full" : "hud_dodge_pip_empty");
    }

    Label Slot(string text)
    {
        var s = new VisualElement { pickingMode = PickingMode.Ignore }; Panel(s); s.style.marginLeft = 6;
        var l = Line(s, 16); l.text = text; skillBar.Add(s);
        return l;
    }

    Label Line(VisualElement parent, int size)
    {
        var l = new Label { pickingMode = PickingMode.Ignore };
        l.style.color = Ink; l.style.fontSize = size;
        l.style.whiteSpace = WhiteSpace.NoWrap;
        var f = Ko.GetFont();
        if (f != null) l.style.unityFontDefinition = FontDefinition.FromFont(f);   // 한글 글꼴(없으면 네모로 깨지므로 반드시)
        parent.Add(l);
        return l;
    }

    /// <summary>JudgeSystem 이 값을 채운 뒤 부른다. 글자가 바뀐 줄만 갱신한다(안 바뀌면 건드리지 않아 가볍다)</summary>
    public void Refresh(bool visible)
    {
        if (root == null) return;
        root.style.display = visible && !MiniMap.BigOpen ? DisplayStyle.Flex : DisplayStyle.None;   // 큰 지도가 열리면 HUD 는 숨긴다(비쳐 보임 방지)
        if (!visible) return;
        var a = Hud.LedgerLine(); if (a != lastLedger) { ledger.text = lastLedger = a; }
        var b = Hud.VitalLine(); if (b != lastVital) { vital.text = lastVital = b; }
        // 개편 P0-1: 좌상단 '밤 N초 · 천도 · 단서' 상태 줄은 지운다(시각은 미니맵 둘레 시계가, 흐름은 퀘스트 추적이 맡는다)
        night.style.display = DisplayStyle.None;
        // 시계 고리는 미니맵 바로 아래(화면 px → 패널 단위로 환산: 패널은 1280×720 기준, 가로·세로 비율을 절반씩 섞는다)
        float refW = Ko.TouchUI ? 960f : 1280f, refH = Ko.TouchUI ? 540f : 720f; float pscale = Mathf.Sqrt((Screen.width / refW) * (Screen.height / refH));
        if (questBox != null) questBox.style.top = MiniMap.BottomPx / Mathf.Max(0.1f, pscale) + ringSize + U(16);   // 명세: 지역명(시계 고리) 아래 16px
        if (questBox != null && Ko.TouchUI)
        {
            // 폰: 미니맵이 화면 높이에 비해 커서 퀘스트 칸이 천도·도술 버튼 자리까지 밀려 내려온다(PC 확인 2026-10-31).
            // 버튼이 없는 왼쪽, 물약 버튼 아래로 옮긴다(가로 폰에서 330 은 물약 버튼과 겹쳐 440)
            float sPx = Screen.height / 1080f / Mathf.Max(0.1f, pscale);
            questBox.style.right = StyleKeyword.Auto; questBox.style.left = 24f * sPx; questBox.style.top = 440f * sPx;
        }
        if (ringBox != null) { ringBox.style.top = MiniMap.BottomPx / Mathf.Max(0.1f, pscale) + 4f; ringBox.style.right = Mathf.Max(10f, 24f * Screen.height / 1080f) / Mathf.Max(0.1f, pscale); }
        skillBar.style.display = Ko.TouchUI || slotBar != null ? DisplayStyle.None : DisplayStyle.Flex;   // 폰: 키 안내줄(E 천도·R 파혼)은 버튼과 겹치고 키보드가 없어 항상 숨김. PC: 새 8칸 스킬바가 있으면 숨기고, 그림이 없을 때만 옛 줄로 돌아감
        RefreshGuide(); RefreshBossArea();
        if (rimIcon != null) rimIcon.style.display = Hud.JudgeNamed ? DisplayStyle.Flex : DisplayStyle.None;
        if (cardRow != null) cardRow.style.display = DisplayStyle.None;   // 개편 P0-1·2: 화면 아래 큰 처결 카드는 지운다. 선택은 혼 머리 위 ▲E ✕R 표식(JudgeSystem.DrawExecMark)이 보여 준다
        RefreshSkillBar(); RefreshSlots(); RefreshToasts(); RefreshStamp(); RefreshDosulCards(); RefreshEdges(); RefreshTimeRing(); RefreshPeace();
        if (hpFill != null)
        {
            hpFill.style.width = Length.Percent(Hud.HpRatio * 100f);
            hpFill.style.backgroundColor = Hud.HpLow ? new Color(0.9f, 0.3f, 0.3f) : new Color(0.72f, 0.82f, 0.95f);
        }
        else if (vitalClip != null)
        {
            vitalClip.style.width = hpFullW * Hud.HpRatio;   // 틀 안 홈 길이에 맞춰 자른다(그림이 찌그러지지 않게)
            vitalFillImg.style.unityBackgroundImageTintColor = Hud.HpLow ? new Color(1f, 0.45f, 0.4f) : Color.white;   // 위험하면 붉게
        }
    }

    void RefreshSkillBar()
    {
        weaponLabel.text = "무기 " + Hud.WeaponName;
        pullLabel.text = Hud.PullCd > 0.05f ? "Q 끌기 " + Mathf.CeilToInt(Hud.PullCd) + "s" : "Q 끌기";
        pullLabel.style.opacity = Hud.PullCd > 0.05f ? 0.5f : 1f;
        for (int i = 0; i < pips.Length; i++)
        {
            float fill = Mathf.Clamp01(Hud.DodgeCharges - i);   // 충전 중인 칸은 흐리게 차오른다
            pips[i].style.backgroundColor = Color.Lerp(new Color(1, 1, 1, 0.15f), new Color(0.72f, 0.9f, 1f, 1f), fill);
        }
    }

    /// <summary>알림 줄이 바뀐 때만 다시 만든다(나이에 따라 서서히 투명해짐)</summary>
    void RefreshToasts()
    {
        var sb = new System.Text.StringBuilder();
        foreach (var t in Hud.Toasts.Items) sb.Append(ToastStack.Line(t)).Append('|');
        string key = sb.ToString();
        if (key != lastToasts)
        {
            lastToasts = key; toastBox.Clear();
            foreach (var t in Hud.Toasts.Items) { var v = new VisualElement { pickingMode = PickingMode.Ignore }; Panel(v); v.style.marginBottom = 3; Line(v, 18).text = ToastStack.Line(t); toastBox.Add(v); }
        }
        for (int i = 0; i < Hud.Toasts.Items.Count && i < toastBox.childCount; i++)
            toastBox[i].style.opacity = Mathf.Clamp01((ToastStack.Life - Hud.Toasts.Items[i].Age) / 0.5f);   // 마지막 0.5초에 사라짐
    }

    /// <summary>
    /// 가장자리 경고: 시야 밖에서 공격을 준비하는 적의 방향에 붉은 마름모를 띄운다.
    /// 위치는 화면 비율(%)이라 해상도·UI 배율이 달라도 맞는다. 표시는 미리 만들어 둔 것을 재사용(매 프레임 새로 만들면 느려진다).
    /// </summary>
    void RefreshEdges()
    {
        int n = Hud.Edges.Count;
        while (edgePool.Count < n)
        {
            var v = new VisualElement { pickingMode = PickingMode.Ignore };
            v.style.position = Position.Absolute; v.style.width = 26; v.style.height = 26;
            v.style.marginLeft = -13; v.style.marginTop = -13;           // 가운데 기준으로 놓는다
            v.style.rotate = new Rotate(45f);
            v.style.backgroundColor = new Color(0.95f, 0.18f, 0.15f, 0.9f);
            root.Add(v); edgePool.Add(v);
        }
        float pulse = 0.65f + 0.35f * Mathf.Sin(Time.unscaledTime * 14f);   // 빠르게 깜박여 눈에 띄게
        for (int i = 0; i < edgePool.Count; i++)
        {
            var v = edgePool[i];
            if (i >= n) { v.style.display = DisplayStyle.None; continue; }
            v.style.display = DisplayStyle.Flex;
            v.style.left = Length.Percent(Hud.Edges[i].Nx * 100f);
            v.style.top = Length.Percent(Hud.Edges[i].Ny * 100f);
            v.style.opacity = pulse;
        }
    }


    /// <summary>
    /// 시각 고리(기획 UI 밑그림): 12지시 해시계처럼 둘레에 눈금 12개, 해·달 표시가 둘레를 돈다. 동틀녘엔 붉게.
    /// 숫자 대신 '모양'으로 시간을 읽게 하려는 것(마을 평화 시간엔 이것만 보인다). 유니티 구버전에도 되도록 회전한 작은 막대로 눈금을 만든다.
    /// </summary>
    void BuildTimeRing()
    {
        ringBox = new VisualElement { name = "time-ring", pickingMode = PickingMode.Ignore };
        ringBox.style.position = Position.Absolute; ringBox.style.right = 14; ringBox.style.top = 64;
        artRing = UiTex("ui_time_ring_frame") != null;
        if (artRing) ringSize = 120f;   // 아트 틀은 구간 호가 그려져 있어 조금 크게 둔다
        ringBox.style.width = ringSize; ringBox.style.height = ringSize;
        ringBox.style.backgroundColor = PaperBg;
        float rad = ringSize / 2f;
        if (artRing)
        {
            // 아트 틀(동틀녘 붉음·낮 한지·해질녘 금·밤 남청 호가 이미 그려짐): 바탕·테두리·눈금 대신 그림 한 장 + 해·달 표시
            ringBox.style.backgroundColor = Color.clear; SetImg(ringBox, "ui_time_ring_frame");
            ringMarker = new VisualElement { pickingMode = PickingMode.Ignore };
            ringMarker.style.position = Position.Absolute; ringMarker.style.width = 22; ringMarker.style.height = 22;
            ringBox.Add(ringMarker); root.Add(ringBox);
            return;
        }
        ringBox.style.borderTopLeftRadius = rad; ringBox.style.borderTopRightRadius = rad; ringBox.style.borderBottomLeftRadius = rad; ringBox.style.borderBottomRightRadius = rad;
        var edge = new Color(1f, 1f, 1f, 0.3f);
        ringBox.style.borderTopWidth = 2; ringBox.style.borderBottomWidth = 2; ringBox.style.borderLeftWidth = 2; ringBox.style.borderRightWidth = 2;
        ringBox.style.borderTopColor = edge; ringBox.style.borderBottomColor = edge; ringBox.style.borderLeftColor = edge; ringBox.style.borderRightColor = edge;
        for (int i = 0; i < 12; i++)
        {
            float a = i * 30f * Mathf.Deg2Rad;
            bool top = i == 0;   // 꼭대기(한밤) 눈금만 굵고 길게
            var t = new VisualElement { pickingMode = PickingMode.Ignore };
            float w = top ? 4f : 2f, h = top ? 12f : 7f, r = rad - 2f - h / 2f - 2f;
            t.style.position = Position.Absolute; t.style.width = w; t.style.height = h;
            t.style.left = rad - 2f + Mathf.Sin(a) * r - w / 2f; t.style.top = rad - 2f - Mathf.Cos(a) * r - h / 2f;   // -2 는 테두리 두께
            t.style.rotate = new Rotate(i * 30f);
            t.style.backgroundColor = new Color(1f, 1f, 1f, top ? 0.8f : 0.4f);
            ringBox.Add(t);
        }
        ringMarker = new VisualElement { pickingMode = PickingMode.Ignore };
        ringMarker.style.position = Position.Absolute; ringMarker.style.width = 14; ringMarker.style.height = 14;
        ringMarker.style.borderTopLeftRadius = 7; ringMarker.style.borderTopRightRadius = 7; ringMarker.style.borderBottomLeftRadius = 7; ringMarker.style.borderBottomRightRadius = 7;
        ringBox.Add(ringMarker);
        root.Add(ringBox);
    }

    static readonly string[] MoonTex = { "moon_crescent", "moon_first_quarter", "moon_full", "moon_last_quarter" };

    void RefreshTimeRing()
    {
        float deg;
        if (Hud.ClockLabel != null)
        {
            // 흐르는 하루: 한밤(밤의 가운데)이 꼭대기, 시계 방향으로 돈다
            float midnight = (Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + Balance.CLOCK_DUSK_MIN + Balance.CLOCK_NIGHT_MIN * 0.5f) / WorldClock.DayLength;
            deg = Mathf.Repeat(Hud.TimeOfDay - midnight, 1f) * 360f;
        }
        else deg = Mathf.Lerp(-120f, 120f, Mathf.Clamp01(Hud.TimeOfDay));   // 옛 한 판: 해질녘 왼쪽 아래 → 동틀녘 오른쪽 아래
        if (artRing)
        {
            // 아트 틀: 해·달 표시는 틀 반지름 228/512 위를 돈다. 낮엔 해, 밤엔 달 그림(동틀녘엔 붉게 물들임)
            float aa = deg * Mathf.Deg2Rad, c = ringSize / 2f, rr = ringSize * 228f / 512f, ms = Hud.ClockLabel != null && Hud.Daylight < 0.5f && Hud.FullMoon ? 28f : 22f;
            ringMarker.style.width = ms; ringMarker.style.height = ms;
            ringMarker.style.left = c + Mathf.Sin(aa) * rr - ms / 2f; ringMarker.style.top = c - Mathf.Cos(aa) * rr - ms / 2f;
            bool sun = Hud.ClockLabel != null ? Hud.Daylight >= 0.5f : Hud.TimeOfDay < 0.0f;
            var mt = sun ? UiTex("ui_marker_sun") : (UiTex(MoonTex[Mathf.Clamp(Hud.MoonPhase, 0, 3)]) ?? UiTex("ui_marker_moon"));   // 밤엔 그날의 달 모양
            if (mt != null) ringMarker.style.backgroundImage = Background.FromTexture2D(mt);
            ringMarker.style.unityBackgroundImageTintColor = Hud.IsDawn ? new Color(1f, 0.55f, 0.5f) : Color.white;
            return;
        }
        float a = deg * Mathf.Deg2Rad, rad = ringSize / 2f, r = rad - 2f - 16f;
        float msz = Hud.ClockLabel != null && Hud.Daylight < 0.5f && Hud.FullMoon ? 20f : 14f;   // 보름달 밤엔 표시가 커진다
        ringMarker.style.width = msz; ringMarker.style.height = msz;
        ringMarker.style.left = rad - 2f + Mathf.Sin(a) * r - msz / 2f;   // 크기가 달라도 중심이 어긋나지 않게
        ringMarker.style.top = rad - 2f - Mathf.Cos(a) * r - msz / 2f;
        ringMarker.style.backgroundColor = Hud.IsDawn ? new Color(0.95f, 0.3f, 0.25f)
            : Hud.ClockLabel != null ? Color.Lerp(new Color(0.8f, 0.88f, 1f), new Color(1f, 0.85f, 0.45f), Hud.Daylight)   // 밤 달 청백 → 낮 해 금색
            : Color.Lerp(new Color(1f, 0.85f, 0.5f), new Color(0.8f, 0.88f, 1f), Mathf.Clamp01(Hud.TimeOfDay * 2f));
   // 노을 금색 → 달 청백
    }

    /// <summary>평화로운 낮: 장부·기술 줄을 서서히 걷어 시각 고리와 풍경만 남긴다(적이 가까워지면 곧바로 돌아온다)</summary>
    float peace = 1f;
    void RefreshPeace()
    {
        // 기획 표준: 체력·스킬바·미니맵은 처음부터 항상 보인다(예전의 '평화로운 낮 숨김'은 폐지)
        note.style.opacity = 1f; note.style.display = DisplayStyle.Flex;
        if (slotBar != null) slotBar.style.opacity = 1f;
    }
}
