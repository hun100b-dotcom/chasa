// =============================================================================
// GameMain.cs — 시작점. 무대(카메라·조명·바닥)를 세우고, 부품을 조립하고, 매 프레임 돌린다.
// (Godot판 main.gd 와 같은 구조)
//
// 왜 씬 편집기 대신 코드로 다 만드나?
//   AI가 텍스트 파일만 고쳐서 개발하기 위해서다. Unity 씬 파일은 사람이 편집기로 배치하는 게
//   기본이라 AI가 직접 다루기 어렵다. 그래서 씬은 비워 두고 게임이 켜질 때 코드로 전부 만든다.
// =============================================================================
using UnityEngine;
using Chasa.Core;

public class GameMain : MonoBehaviour
{
    readonly HitFeel feel = new HitFeel();
    Camera cam;
    Light sun;
    Player player;
    readonly EnemyManager enemies = new EnemyManager();
    DamageNumbers numbers;
    ClickMarker marker;
    JudgeSystem judge;
    Vector3 focus, offset;
    Vector3 camPrevPlayer, ahead;   // 카메라 앞쪽 보기용: 지난 프레임 플레이어 위치, 현재 앞쪽 치우침
    bool holdingMove;

    /// <summary>씬에 아무것도 없어도 게임이 켜지면 자동으로 이 오브젝트를 만든다</summary>
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot() => new GameObject("GameMain").AddComponent<GameMain>();

    void Start()
    {
        Application.targetFrameRate = 60;
        // 구역을 이어 붙인 넓은 필드: 설정값 또는 주소에 ?zones 가 있으면 켠다 (꺼져 있으면 마을 한 곳 = 기존 동작)
        World.Enabled = Balance.WORLD_ZONES || Application.absoluteURL.Contains("zones");
        var url = Application.absoluteURL;
        UiRoot.Enabled = Balance.UI_TOOLKIT || url.Contains("?ui") || url.Contains("&ui");   // 주소에 ?ui 가 있으면 UI Toolkit HUD ("build" 같은 글자에 걸리지 않게 ? 와 & 를 붙여 본다)
        GrowthData.Load();   // 기획팀 도술·옵션 JSON 덮어쓰기(있을 때만)
        BuildStage();
        enemies.SpawnAll(Vector3.zero);
        numbers = gameObject.AddComponent<DamageNumbers>();
        numbers.cam = cam;
        marker = ClickMarker.Create();
        player = Player.Create();
        player.enemies = enemies; player.feel = feel; player.numbers = numbers;
        player.chain = ChainVisual.Create();
        // 처결(천도·파혼): 규칙은 Core, 화면 연결은 JudgeSystem
        judge = gameObject.AddComponent<JudgeSystem>();
        judge.player = player; judge.enemies = enemies; judge.feel = feel; judge.numbers = numbers; judge.cam = cam;
        // 밤 분위기: 어둠 막 + 등불 (화면 위에 덮는 방식이라 그림 재질을 바꿀 필요가 없다)
        var atmo = gameObject.AddComponent<Atmosphere>();
        if (World.Enabled) { var zm = gameObject.AddComponent<ZoneManager>(); zm.player = player; }   // 걸어가면 둘레 구역을 켜고 끈다
        if (UiRoot.Enabled) judge.ui = gameObject.AddComponent<UiRoot>();   // 새 화면(UI Toolkit)
        Sfx.Create(judge);   // 효과음 재생기
        atmo.cam = cam; atmo.judge = judge; atmo.player = player; atmo.enemies = enemies;
    }

    // -------------------------------------------------------------------------
    // 게임 루프: realDt(진짜 시간)와 dt(게임 세계 시간, 히트스톱 중 0)를 나눈다
    //   → "세계는 멈췄는데 화면만 부르르 떨리는" 타격감 (세 엔진 모두 같은 원리)
    // -------------------------------------------------------------------------
    void Update()
    {
        if (Input.touchCount > 0) Ko.TouchUI = true;   // 실제로 터치가 들어오면 화면 버튼을 띄운다
        if (CharacterPanel.Open) { UpdateCamera(Time.unscaledDeltaTime); return; }   // 캐릭터 창이 열리면 세계 정지
        if (judge.InDay) { judge.Tick(0f, Mathf.Min(0.05f, Time.unscaledDeltaTime)); return; }   // 낮 화면: 세계는 멈추고 낮 화면만 흐른다
        if (!judge.NightOver) HandleInput();   // 결과 화면에서는 조작이 먹지 않는다(QA B4)
        float realDt = Mathf.Min(0.05f, Time.unscaledDeltaTime);
        bool frozen = feel.Tick(realDt);
        float dt = frozen ? 0f : realDt * feel.TimeScale;   // 히트스톱 중 0, 천도 완료 슬로모 중 절반
        player.Tick(dt);
        judge.Tick(dt, realDt);
        enemies.Tick(dt, player.Pos, Config.PLAYER_RADIUS);
        numbers.Tick(realDt);
        marker.Tick(realDt);
        UpdateCamera(realDt);
    }

    // ---- 무대 -----------------------------------------------------------------
    void BuildStage()
    {
        // 직교 카메라: 멀어도 작아지지 않음 = 원근감 없는 쿼터뷰
        cam = new GameObject("Camera").AddComponent<Camera>();
        cam.gameObject.tag = "MainCamera";   // 그림(빌보드)이 Camera.main 으로 카메라를 찾는다
        cam.orthographic = true;
        cam.orthographicSize = Config.CAMERA_VIEW_HEIGHT / 2f; // 유니티는 '세로 절반' 값을 받는다
        cam.nearClipPlane = 0.1f; cam.farClipPlane = 300f;
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = Config.Hex(0x14161c);
        float pitch = Config.CAMERA_PITCH_DEG * Mathf.Deg2Rad, yaw = Config.CAMERA_YAW_DEG * Mathf.Deg2Rad, dist = 60f;
        offset = new Vector3(Mathf.Cos(yaw) * Mathf.Cos(pitch), Mathf.Sin(pitch), Mathf.Sin(yaw) * Mathf.Cos(pitch)) * dist;

        // 조명: 은은한 전체 조명 + 그림자 만드는 햇빛 (밝기는 다른 판과 눈으로 맞춤)
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.45f, 0.45f, 0.45f);
        sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.intensity = 0.9f;
        sun.shadows = LightShadows.Soft;
        sun.transform.rotation = Quaternion.LookRotation(-new Vector3(14, 30, 8));
        QualitySettings.shadowDistance = 60f;

        // 바닥: 맵 경계(Core/MapLayout)에 맞춘 직사각형. 그림 타일이 깔리면 이 판은 뒤에 숨는다
        float sizeX = MapLayout.MaxX - MapLayout.MinX, sizeZ = MapLayout.MaxZ - MapLayout.MinZ;
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane); // 기본 판: 10 x 10
        Destroy(floor.GetComponent<Collider>());
        floor.transform.position = new Vector3(MapLayout.CenterX, 0f, MapLayout.CenterZ);
        floor.transform.localScale = new Vector3(sizeX / 10f, 1, sizeZ / 10f);
        floor.GetComponent<Renderer>().sharedMaterial = U.Matte(Config.Hex(0x2b303b));

        // 격자(2칸 간격) + 붉은 테두리 — 선 메쉬 하나로 (그림 지형이 있으면 꺼진다)
        var verts = new System.Collections.Generic.List<Vector3>();
        var cols = new System.Collections.Generic.List<Color>();
        float x0 = MapLayout.MinX, x1 = MapLayout.MaxX, z0 = MapLayout.MinZ, z1 = MapLayout.MaxZ;
        for (float x = Mathf.Ceil(x0 / 2f) * 2f; x <= x1 + 0.001f; x += 2f)
        {
            var c = Mathf.Abs(x) < 0.001f ? Config.Hex(0x4a5262) : Config.Hex(0x383e4b);
            verts.Add(new Vector3(x, 0.01f, z0)); verts.Add(new Vector3(x, 0.01f, z1));
            cols.Add(c); cols.Add(c);
        }
        for (float z = Mathf.Ceil(z0 / 2f) * 2f; z <= z1 + 0.001f; z += 2f)
        {
            var c = Mathf.Abs(z) < 0.001f ? Config.Hex(0x4a5262) : Config.Hex(0x383e4b);
            verts.Add(new Vector3(x0, 0.01f, z)); verts.Add(new Vector3(x1, 0.01f, z));
            cols.Add(c); cols.Add(c);
        }
        var corners = new[] { new Vector3(x0, 0.02f, z0), new Vector3(x1, 0.02f, z0), new Vector3(x1, 0.02f, z1), new Vector3(x0, 0.02f, z1) };
        for (int i = 0; i < 4; i++) { verts.Add(corners[i]); verts.Add(corners[(i + 1) % 4]); cols.Add(Config.Hex(0x9b3b3b)); cols.Add(Config.Hex(0x9b3b3b)); }
        var idx = new int[verts.Count];
        for (int i = 0; i < idx.Length; i++) idx[i] = i;
        var mesh = new Mesh();
        mesh.SetVertices(verts); mesh.SetColors(cols);
        mesh.SetIndices(idx, MeshTopology.Lines, 0);
        var lines = new GameObject("Grid");
        lines.AddComponent<MeshFilter>().sharedMesh = mesh;
        var lr = lines.AddComponent<MeshRenderer>();
        lr.sharedMaterial = U.VertexColor();
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;

        bool groundArt = MapView.Build(transform);   // 솔고개 마을(집·장승·길) — 막힌 곳 규칙은 Core/MapLayout
        if (groundArt) lines.SetActive(false);        // 그림 지형이 깔렸으면 임시 격자선은 끈다
    }

    void UpdateCamera(float dt)
    {
        float k = 1f - Mathf.Exp(-Config.CAMERA_FOLLOW_SMOOTHNESS * dt); // 프레임레이트와 무관한 부드러운 추적
        // 목표점 = 플레이어 + 걷는 방향 앞쪽(look-ahead). 멈추면 앞쪽 보기는 서서히 0으로 돌아온다
        var vel = (player.Pos - camPrevPlayer) / Mathf.Max(0.0001f, dt); camPrevPlayer = player.Pos;
        vel.y = 0f;
        var wantAhead = vel.sqrMagnitude > 0.25f ? vel.normalized * Balance.CAMERA_LOOKAHEAD_M : Vector3.zero;
        ahead = Vector3.Lerp(ahead, wantAhead, 1f - Mathf.Exp(-3f * dt));   // 천천히 따라가야 방향을 바꿀 때 화면이 휙 돌지 않는다
        var goal = new Vector3(player.Pos.x, 0, player.Pos.z) + ahead;
        // 데드존: 목표가 카메라 중심에서 이 반경 안이면 움직이지 않는다 (작은 흔들림에 화면이 같이 떨리지 않게)
        var d = goal - focus; d.y = 0f;
        if (d.magnitude > Balance.CAMERA_DEADZONE_M) goal = focus + d.normalized * (d.magnitude - Balance.CAMERA_DEADZONE_M);
        else goal = focus;
        focus = Vector3.Lerp(focus, goal, k);
        cam.transform.position = focus + offset;
        cam.transform.LookAt(focus);
        cam.transform.Rotate(0f, 0f, feel.GetShakeRoll(), Space.Self);   // 충격이 클 때만 화면이 살짝 기울었다 돌아온다
        var s = feel.GetShakeOffset(); // 화면 기준 오른쪽/위쪽으로 밀어 평행하게 떨림
        cam.transform.position += cam.transform.right * s.x + cam.transform.up * s.y;
        cam.transform.position += feel.Kick;   // 맞은 방향으로 툭 밀렸다 돌아오는 카메라
        // 줌: 타격 펀치(최대 6%) + 천도 캐스팅 중 서서히 다가감(최대 9%) — 화면 크기(orthographicSize)를 줄이면 다가간 것
        float zoomIn = feel.Zoom * 0.06f + judge.CastZoom * 0.09f;
        cam.orthographicSize = Config.CAMERA_VIEW_HEIGHT / 2f * (1f - zoomIn);
    }

    // ---- 입력: 마우스 = 이동·대상 / 키보드 = 기술 (PD 피드백 반영) --------------------
    void HandleInput()
    {
        Vector3 mouse = Input.mousePosition;
        if (Input.GetKeyDown(KeyCode.Q)) { if (player.loadout.Def.HasQuake) player.CommandQuake(); else if (player.loadout.Def.HasPull) SkillPull(mouse); }   // Q: 철삭=견인 / 육모방망이=땅울림 / 그 외 무기는 없음
        if (Input.GetKeyDown(KeyCode.Space)) SkillDodge(mouse); // Space: 피하기(구르기). 휘두르기는 마우스 클릭으로 충분하다(기획 타격감 분석)
        if (Input.GetMouseButtonDown(1) && player.loadout.Def.HasPull) SkillPull(mouse);   // 우클릭도 견인(철삭일 때)

        if (Input.GetMouseButtonDown(0) && !OverTouchButtons(mouse))
        {
            var ray = cam.ScreenPointToRay(mouse);
            var ground = Ground(ray);
            var e = enemies.Pick(ray, ground, Config.ENEMY_PICK_RADIUS);
            if (e != null) player.CommandAttack(e);
            else if (ground.HasValue) { player.CommandMove(ground.Value); marker.Show(ground.Value); holdingMove = true; }
        }
        if (Input.GetMouseButtonUp(0)) holdingMove = false;
        if (holdingMove && Input.GetMouseButton(0)) // 누른 채 움직이면 마우스를 따라 걷기
        {
            var g = Ground(cam.ScreenPointToRay(mouse));
            if (g.HasValue) player.CommandMove(g.Value);
        }
    }

    void SkillPull(Vector3 screen)
    {
        var ray = cam.ScreenPointToRay(screen);
        var g = Ground(ray);
        var e = enemies.Pick(ray, g, Config.PULL_PICK_RADIUS);
        player.CommandPull(e, g ?? player.Pos);
    }

    /// <summary>피하기: 마우스가 있는 쪽으로. 마우스 위치를 못 구하면 걷던 방향</summary>
    void SkillDodge(Vector3 screen)
    {
        var g = Ground(cam.ScreenPointToRay(screen));
        player.CommandDodge(g);
    }

    void SkillSwing(Vector3 screen)
    {
        var g = Ground(cam.ScreenPointToRay(screen));
        player.CommandSwing(g ?? player.Pos + U.Dir(player.facing));
    }

    static Vector3? Ground(Ray ray)
    {
        // 마우스 광선이 y=0 바닥과 만나는 점
        if (Mathf.Abs(ray.direction.y) < 1e-6f) return null;
        float t = -ray.origin.y / ray.direction.y;
        if (t < 0f) return null;
        return ray.origin + ray.direction * t;
    }

    // ---- 화면 글자 / 폰 버튼 (기본 글꼴에 한글이 없을 수 있어 영문) --------------------
    Rect PullBtn => new Rect(Screen.width - 260, Screen.height - 110, 110, 90);
    Rect DodgeBtn => new Rect(Screen.width - 136, Screen.height - 212, 110, 90);
    Rect SwingBtn => new Rect(Screen.width - 136, Screen.height - 110, 110, 90);

    bool OverTouchButtons(Vector3 mouse)
    {
        if (!Ko.TouchUI) return false;
        var p = new Vector2(mouse.x, Screen.height - mouse.y);
        return PullBtn.Contains(p) || SwingBtn.Contains(p) || DodgeBtn.Contains(p);
    }

    void OnGUI()
    {
        Ko.Apply(); // 한글 글꼴 적용(안 하면 한글이 네모로 깨짐)
        if (judge.InDay || CharacterPanel.Open || judge.NightOver) return;   // 낮 화면·캐릭터 창에서는 밤의 안내·버튼을 그리지 않는다
        var hint = new GUIStyle(GUI.skin.label) { fontSize = 14 };
        hint.normal.textColor = new Color(1, 1, 1, 0.55f);
        GUI.Label(new Rect(12, 8, 600, 24), "마우스: 이동·대상   Q: 끌어당김   Space: 피하기" + (Demo.Panel ? "   C: 캐릭터 창" : ""), hint);
        if (!Ko.TouchUI) return;
        var bs = new GUIStyle(GUI.skin.button) { fontSize = 20 };
        if (GUI.Button(PullBtn, "끌기", bs)) { var e = Nearest(); player.CommandPull(e, e != null ? e.Pos : player.Pos); }
        if (Balance.DODGE_ENABLED && GUI.Button(DodgeBtn, "피하기", bs)) player.CommandDodge(null);   // 폰: 걷던 방향으로
        if (GUI.Button(SwingBtn, "휘두르기", bs)) { var e = Nearest(); player.CommandSwing(e != null ? e.Pos : player.Pos + U.Dir(player.facing)); }
    }

    Enemy Nearest()
    {
        // 터치엔 커서가 없으니 가장 가까운 적을 자동 선택
        Enemy best = null; float bestD = Config.PULL_RANGE;
        foreach (var e in enemies.list)
        {
            if (!e.alive) continue;   // 견인은 싸우는 적만
            float d = Vector3.Distance(e.Pos, player.Pos);
            if (d <= bestD) { bestD = d; best = e; }
        }
        return best;
    }
}
