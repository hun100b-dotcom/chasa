// =============================================================================
// GameMain.cs — 시작점. 무대(카메라·조명·바닥)를 세우고, 부품을 조립하고, 매 프레임 돌린다.
// (Godot판 main.gd 와 같은 구조)
//
// 왜 씬 편집기 대신 코드로 다 만드나?
//   AI가 텍스트 파일만 고쳐서 개발하기 위해서다. Unity 씬 파일은 사람이 편집기로 배치하는 게
//   기본이라 AI가 직접 다루기 어렵다. 그래서 씬은 비워 두고 게임이 켜질 때 코드로 전부 만든다.
// =============================================================================
using UnityEngine;

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
    bool holdingMove;
    bool touchUI;

    /// <summary>씬에 아무것도 없어도 게임이 켜지면 자동으로 이 오브젝트를 만든다</summary>
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot() => new GameObject("GameMain").AddComponent<GameMain>();

    void Start()
    {
        Application.targetFrameRate = 60;
        BuildStage();
        enemies.SpawnAll(Vector3.zero);
        numbers = gameObject.AddComponent<DamageNumbers>();
        numbers.cam = cam;
        marker = ClickMarker.Create();
        player = Player.Create();
        player.enemies = enemies; player.feel = feel; player.numbers = numbers;
        player.chain = ChainVisual.Create();
        touchUI = Input.touchSupported; // 폰이면 화면 기술 버튼을 띄운다
        // 처결(천도·파혼): 규칙은 Core, 화면 연결은 JudgeSystem
        judge = gameObject.AddComponent<JudgeSystem>();
        judge.player = player; judge.enemies = enemies; judge.feel = feel; judge.numbers = numbers; judge.cam = cam;
    }

    // -------------------------------------------------------------------------
    // 게임 루프: realDt(진짜 시간)와 dt(게임 세계 시간, 히트스톱 중 0)를 나눈다
    //   → "세계는 멈췄는데 화면만 부르르 떨리는" 타격감 (세 엔진 모두 같은 원리)
    // -------------------------------------------------------------------------
    void Update()
    {
        HandleInput();
        float realDt = Mathf.Min(0.05f, Time.unscaledDeltaTime);
        bool frozen = feel.Tick(realDt);
        float dt = frozen ? 0f : realDt;
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

        // 바닥
        float size = Config.ARENA_HALF_SIZE * 2f;
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane); // 기본 판: 10 x 10
        Destroy(floor.GetComponent<Collider>());
        floor.transform.localScale = new Vector3(size / 10f, 1, size / 10f);
        floor.GetComponent<Renderer>().sharedMaterial = U.Matte(Config.Hex(0x2b303b));

        // 격자(2칸 간격, 가운데 밝게) + 붉은 테두리 — 선 메쉬 하나로
        var verts = new System.Collections.Generic.List<Vector3>();
        var cols = new System.Collections.Generic.List<Color>();
        float h = Config.ARENA_HALF_SIZE;
        for (float x = -h; x <= h + 0.001f; x += 2f)
        {
            var c = Mathf.Abs(x) < 0.001f ? Config.Hex(0x4a5262) : Config.Hex(0x383e4b);
            verts.Add(new Vector3(x, 0.01f, -h)); verts.Add(new Vector3(x, 0.01f, h));
            verts.Add(new Vector3(-h, 0.01f, x)); verts.Add(new Vector3(h, 0.01f, x));
            for (int k = 0; k < 4; k++) cols.Add(c);
        }
        var corners = new[] { new Vector3(-h, 0.02f, -h), new Vector3(h, 0.02f, -h), new Vector3(h, 0.02f, h), new Vector3(-h, 0.02f, h) };
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
    }

    void UpdateCamera(float dt)
    {
        float k = 1f - Mathf.Exp(-Config.CAMERA_FOLLOW_SMOOTHNESS * dt); // 프레임레이트와 무관한 부드러운 추적
        focus = Vector3.Lerp(focus, new Vector3(player.Pos.x, 0, player.Pos.z), k);
        cam.transform.position = focus + offset;
        cam.transform.LookAt(focus);
        var s = feel.GetShakeOffset(); // 화면 기준 오른쪽/위쪽으로 밀어 평행하게 떨림
        cam.transform.position += cam.transform.right * s.x + cam.transform.up * s.y;
    }

    // ---- 입력: 마우스 = 이동·대상 / 키보드 = 기술 (PD 피드백 반영) --------------------
    void HandleInput()
    {
        Vector3 mouse = Input.mousePosition;
        if (Input.GetKeyDown(KeyCode.Q)) SkillPull(mouse);   // Q: 커서 근처 적 견인
        if (Input.GetKeyDown(KeyCode.Space)) SkillSwing(mouse); // Space: 제자리 휘두르기
        if (Input.GetMouseButtonDown(1)) SkillPull(mouse);   // 우클릭도 견인

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
    Rect SwingBtn => new Rect(Screen.width - 136, Screen.height - 110, 110, 90);

    bool OverTouchButtons(Vector3 mouse)
    {
        if (!touchUI) return false;
        var p = new Vector2(mouse.x, Screen.height - mouse.y);
        return PullBtn.Contains(p) || SwingBtn.Contains(p);
    }

    void OnGUI()
    {
        var hint = new GUIStyle(GUI.skin.label) { fontSize = 14 };
        hint.normal.textColor = new Color(1, 1, 1, 0.55f);
        GUI.Label(new Rect(12, 8, 600, 24), "Unity  |  Mouse: move / target   Q: pull   Space: swing", hint);
        if (!touchUI) return;
        var bs = new GUIStyle(GUI.skin.button) { fontSize = 20 };
        if (GUI.Button(PullBtn, "PULL", bs)) { var e = Nearest(); player.CommandPull(e, e != null ? e.Pos : player.Pos); }
        if (GUI.Button(SwingBtn, "SWING", bs)) { var e = Nearest(); player.CommandSwing(e != null ? e.Pos : player.Pos + U.Dir(player.facing)); }
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
