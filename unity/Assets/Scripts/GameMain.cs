// =============================================================================
// GameMain.cs — 시작점. 무대(카메라·조명·바닥)를 세우고, 부품을 조립하고, 매 프레임 돌린다.
// (Godot판 main.gd 와 같은 구조)
//
// 왜 씬 편집기 대신 코드로 다 만드나?
//   AI가 텍스트 파일만 고쳐서 개발하기 위해서다. Unity 씬 파일은 사람이 편집기로 배치하는 게
//   기본이라 AI가 직접 다루기 어렵다. 그래서 씬은 비워 두고 게임이 켜질 때 코드로 전부 만든다.
// =============================================================================
using System.Linq;
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
    float camYaw, camPitch, camDist;   // 기본 카메라 각도·거리(줌에 따라 각도를 바꿀 때의 기준)
    Vector3 camPrevPlayer, ahead;   // 카메라 앞쪽 보기용: 지난 프레임 플레이어 위치, 현재 앞쪽 치우침
    bool holdingMove;

    /// <summary>씬에 아무것도 없어도 게임이 켜지면 자동으로 이 오브젝트를 만든다</summary>
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot() => new GameObject("GameMain").AddComponent<GameMain>();

    void Start()
    {
        Application.targetFrameRate = 60;
        // 구역을 이어 붙인 넓은 필드: 설정값 또는 주소에 ?zones 가 있으면 켠다 (꺼져 있으면 마을 한 곳 = 기존 동작)
        if (DemoScript.Wanted()) Random.InitState(7);   // 비교 영상용: 같은 장면이 매번 똑같이(난수 씨앗 고정)
        View3D.Init();   // 주소의 ?v=3d / ?cam=a|b|c 를 읽는다
        // 5×5 넓은 필드(아트팀 조립): 이제 기본값. 옛 솔고개 한 구역으로 돌아가려면 주소에 ?field=0 (오너 지시로 옛 코드는 지우지 않고 남겨 둠)
        // 켜지면 옛 구역 시험판(?zones)은 쓰지 않는다
        var fieldUrl = (Application.absoluteURL ?? "").ToLowerInvariant();
        FieldRules.On = !(fieldUrl.Contains("field=0") || fieldUrl.Contains("field=off"));
        if (FieldRules.On) { FieldManager.ApplyMarkers(); MapLayout.Blockers.Clear(); }   // 마을 옛 충돌표는 비우고 필드 소품 충돌을 쓴다
        World.Enabled = !FieldRules.On && (Balance.WORLD_ZONES || Application.absoluteURL.Contains("zones"));
        var url = Application.absoluteURL;
        UiRoot.Enabled = Balance.UI_TOOLKIT || url.Contains("?ui") || url.Contains("&ui");   // 주소에 ?ui 가 있으면 UI Toolkit HUD ("build" 같은 글자에 걸리지 않게 ? 와 & 를 붙여 본다)
        GrowthData.Load();   // 기획팀 도술·옵션 JSON 덮어쓰기(있을 때만)
        if (FieldRules.On) GroundTerrain.Init();   // 아트의 새 땅(Resources/Terrain)이 있으면 읽는다. 없으면 옛 타일 땅
        BuildStage();
        var startPos = FieldRules.On ? new Vector3(FieldRules.StartX, 0f, FieldRules.StartZ) : Vector3.zero;
        if (FieldRules.On) startPos = CaptureStart(startPos);   // 검수용 주소 ?boss=naru|wolhwa|seo · ?pos=x,z 로 시작 자리를 옮긴다
        if (FieldRules.On) focus = startPos;   // 카메라가 원점에서 날아오지 않게 시작 위치에서 시작
        if (!FieldRules.On) enemies.SpawnAll(startPos);   // 필드에선 군집(FieldCamps)이 가까이 갈 때 세운다
        numbers = gameObject.AddComponent<DamageNumbers>();
        numbers.cam = cam;
        marker = ClickMarker.Create();
        player = Player.Create();
        player.Pos = startPos;
        GroundSnap.Attach(player.gameObject);   // 새 땅이 있으면 높이를 따라 걷는다
        player.enemies = enemies; player.feel = feel; player.numbers = numbers;
        player.chain = ChainVisual.Create();
        // 처결(천도·파혼): 규칙은 Core, 화면 연결은 JudgeSystem
        judge = gameObject.AddComponent<JudgeSystem>();
        if (FieldRules.On)
        {
            judge.camps = new FieldCamps(enemies);
            judge.named = new NamedSoulSpawns(enemies);
            judge.clock = new WorldClock();
            judge.clock.Minutes = WorldClock.DayLength - Balance.CLOCK_NIGHT_MIN + 3f;   // 첫 5분: 밤이 막 깊어진 때(밤 9시 무렵)에서 시작해 박돌쇠 처결까지 멈춘다
            judge.introFrozen = true;
            judge.npcs = new NpcWorld(judge.clueBook, () => judge.ledger.Karma, () => judge.clock.Day + 1);
            judge.npcs.onClue = () => judge.HintClue();
            judge.interactables = new Interactables(judge);   // 1막 줍기·만져 보기 물건
            // 10m 안에 싸우는 혼이 있으면 엿듣기·지켜보기 진행이 멈춘다(기획 npc-interaction-spec §2-3)
            judge.npcs.enemyWithin = r =>
            {
                foreach (var x in judge.enemies.list) if (x.alive && (x.Pos - judge.player.Pos).sqrMagnitude < r * r) return true;
                return false;
            };
            judge.npcs.inCombat = () =>
            {
                foreach (var x in judge.enemies.list) if (x.alive && (x.Pos - judge.player.Pos).sqrMagnitude < 100f) return true;
                return false;
            };
            judge.onTeleport = p => focus = p;   // 넋길로 옮겨 가면 카메라도 곧바로 따라간다(날아가지 않게)
            var cu = (Application.absoluteURL ?? "").ToLowerInvariant();
            // 검수용 안개 배율: ?fog=off 는 안개 끔, ?fog=0.5 처럼 숫자면 그 배율
            { int fi = cu.IndexOf("fog="); if (fi >= 0) { string fv = cu.Substring(fi + 4); int amp = fv.IndexOf('&'); if (amp >= 0) fv = fv.Substring(0, amp); float fs; ClockSky.FogScale = fv == "off" ? 0f : (float.TryParse(fv, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out fs) ? fs : 1f); } }
            // 검수용 시각 고정: ?time=day|dusk|night|dawn 이면 그 시간대 한가운데에서 시작하고 첫 5분 시계 정지를 푼다(아트·PC 캡처용)
            foreach (var tn in new[] { "dawn", "day", "dusk", "night" })
                if (cu.Contains("time=" + tn))
                {
                    float st = tn == "dawn" ? 1f : tn == "day" ? Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN * 0.5f : tn == "dusk" ? Balance.CLOCK_DAWN_MIN + Balance.CLOCK_DAY_MIN + Balance.CLOCK_DUSK_MIN * 0.5f : WorldClock.DayLength - Balance.CLOCK_NIGHT_MIN + 8f;
                    judge.clock.Minutes = st; judge.introFrozen = false;
                }
            int ci = cu.IndexOf("clock=");
            float sp; if (ci >= 0 && float.TryParse(new string(cu.Substring(ci + 6).TakeWhile(char.IsDigit).ToArray()), out sp) && sp > 0f) judge.clock.Speed = sp;   // 주소 ?clock=10 이면 10배속(한 바퀴 검사용)
        }
        player.onHitLanded = () => judge.guide.Complete("hit");   // 첫 타가 맞으면 '때리기' 안내가 닫힌다
        judge.player = player; judge.enemies = enemies; judge.feel = feel; judge.numbers = numbers; judge.cam = cam;
        if (View3D.On)
        {
            // 새 화면: 진짜 조명(등불·혼불·달빛). 화면 위 어둠 막은 필요 없다
            var nl = gameObject.AddComponent<NightLights>();
            nl.player = player; nl.judge = judge; nl.enemies = enemies;
        }
        else
        {
            // 옛 화면 밤 분위기: 어둠 막 + 등불 (화면 위에 덮는 방식이라 그림 재질을 바꿀 필요가 없다)
            var atmo = gameObject.AddComponent<Atmosphere>();
            atmo.cam = cam; atmo.judge = judge; atmo.player = player; atmo.enemies = enemies;
        }
        if (View3D.On) { var hr = gameObject.AddComponent<HeroRing>(); hr.player = player; }   // 주인공 발밑 청록 고리(어두운 땅에서 안 묻히게)
        WireTouchControls();
        if (FieldRules.On) { var mm = gameObject.AddComponent<MiniMap>(); mm.judge = judge; mm.player = player; mm.cam = cam; }   // 필드 지도(오른쪽 위 작은 지도 + M 큰 지도)
        { var gfx = cam.gameObject.AddComponent<GradingFx>(); gfx.judge = judge; }   // 화면 분위기 후처리(색보정·블룸·비네트·천도 시야 축소). 카메라에 붙어야 OnRenderImage 가 불린다
        if (FieldRules.On) { var fm = gameObject.AddComponent<FieldManager>(); fm.player = player; }   // 걸어가면 둘레 청크를 켜고 끈다
        if (World.Enabled) { var zm = gameObject.AddComponent<ZoneManager>(); zm.player = player; }   // 걸어가면 둘레 구역을 켜고 끈다
        if (UiRoot.Enabled) judge.ui = gameObject.AddComponent<UiRoot>();   // 새 화면(UI Toolkit)
        var settingsPanel = gameObject.AddComponent<SettingsPanel>(); settingsPanel.judge = judge; settingsPanel.white = Texture2D.whiteTexture;   // 설정 화면(O)
        Sfx.Create(judge);   // 효과음 재생기
        BgmPlayer.Create(judge);   // BGM 재생기(층 교차). 필드에서만 소리를 낸다
        if (BotScript.Wanted()) { var bs = gameObject.AddComponent<BotScript>(); bs.player = player; bs.enemies = enemies; bs.judge = judge; }   // ?bot=1 첫 세션 자동 플레이 테스트
        else if (DemoScript.Wanted()) { var ds = gameObject.AddComponent<DemoScript>(); ds.player = player; ds.enemies = enemies; ds.judge = judge; }   // ?demo=1 자동 연출
    }

    // -------------------------------------------------------------------------
    // 게임 루프: realDt(진짜 시간)와 dt(게임 세계 시간, 히트스톱 중 0)를 나눈다
    //   → "세계는 멈췄는데 화면만 부르르 떨리는" 타격감 (세 엔진 모두 같은 원리)
    // -------------------------------------------------------------------------
    void Update()
    {
        if (Input.touchCount > 0) Ko.TouchUI = true;   // 실제로 터치가 들어오면 화면 버튼을 띄운다
        if (CharacterPanel.Open || SettingsPanel.Open || MiniMap.BigOpen) { UpdateCamera(Time.unscaledDeltaTime); return; }   // 캐릭터 창이 열리면 세계 정지
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
        cam.nearClipPlane = 0.1f; cam.farClipPlane = 300f;
        cam.clearFlags = CameraClearFlags.SolidColor;
        float pitch, yaw = Config.CAMERA_YAW_DEG * Mathf.Deg2Rad, dist;
        if (View3D.On)
        {
            // 새 화면: 원근 카메라. 가까이서 깊게 내려다봐서 캐릭터가 크게 보이고 입체감이 난다
            cam.orthographic = false;
            cam.fieldOfView = View3D.Cam.Fov;
            cam.backgroundColor = View3D.FogColor;
            pitch = View3D.Cam.PitchDeg * Mathf.Deg2Rad; dist = View3D.Distance;
        }
        else
        {
            cam.orthographic = true;
            cam.orthographicSize = Config.CAMERA_VIEW_HEIGHT / 2f; // 유니티는 '세로 절반' 값을 받는다
            cam.backgroundColor = Config.Hex(0x14161c);
            pitch = Config.CAMERA_PITCH_DEG * Mathf.Deg2Rad; dist = 60f;
        }
        offset = new Vector3(Mathf.Cos(yaw) * Mathf.Cos(pitch), Mathf.Sin(pitch), Mathf.Sin(yaw) * Mathf.Cos(pitch)) * dist;
        camYaw = yaw; camPitch = pitch; camDist = dist;
        if (View3D.On) { SetZoomStep(1); wheel = wheelTarget; }   // 시작은 기본 거리(16 m)에서

        // 조명: 은은한 전체 조명 + 그림자 만드는 햇빛 (밝기는 다른 판과 눈으로 맞춤)
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.45f, 0.45f, 0.45f);
        sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.intensity = 0.9f;
        sun.shadows = LightShadows.Soft;
        sun.transform.rotation = Quaternion.LookRotation(-new Vector3(14, 30, 8));
        QualitySettings.shadowDistance = 60f;
        if (View3D.On) NightLights.SetupAtmosphere(sun);   // 새 화면: 달빛·푸른 환경광·안개

        // 바닥: 맵 경계(Core/MapLayout)에 맞춘 직사각형. 그림 타일이 깔리면 이 판은 뒤에 숨는다
        float sizeX = MapLayout.MaxX - MapLayout.MinX, sizeZ = MapLayout.MaxZ - MapLayout.MinZ;
        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane); // 기본 판: 10 x 10
        Destroy(floor.GetComponent<Collider>());
        floor.transform.position = new Vector3(MapLayout.CenterX, 0f, MapLayout.CenterZ);
        floor.transform.localScale = new Vector3(sizeX / 10f, 1, sizeZ / 10f);
        floor.GetComponent<Renderer>().sharedMaterial = U.Matte(FieldRules.On ? new Color(0.17f, 0.24f, 0.15f) : Config.Hex(0x2b303b));   // 필드: 풀색 밑판(타일 사이 틈이 보여도 어둡지 않게)

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

        bool groundArt = FieldRules.On || MapView.Build(transform);   // 필드 모드는 FieldManager 가 땅을 세운다   // 솔고개 마을(집·장승·길) — 막힌 곳 규칙은 Core/MapLayout
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
        var goal = new Vector3(player.Pos.x, player.Pos.y, player.Pos.z) + ahead;   // 높이는 발 높이(새 땅 오르막에서 카메라도 같이 오른다)
        // 컷신 중엔 카메라가 대본이 가리키는 곳으로 간다(보스·나룻배·서낭당 쪽 하늘 …). 끝나면 플레이어로 돌아온다
        if (judge.cuts.Active)
        {
            goal = CutTarget(judge.cuts.CamTarget);
            focus = Vector3.Lerp(focus, goal, 1f - Mathf.Exp(-3f / Mathf.Max(0.15f, judge.cuts.CamTime) * dt));
            goal = focus;
        }
        // 데드존: 목표가 카메라 중심에서 이 반경 안이면 움직이지 않는다 (작은 흔들림에 화면이 같이 떨리지 않게)
        var d = goal - focus; d.y = 0f;
        if (d.magnitude > Balance.CAMERA_DEADZONE_M) goal = focus + d.normalized * (d.magnitude - Balance.CAMERA_DEADZONE_M);
        else goal = focus;
        focus = Vector3.Lerp(focus, goal, k);
        // 줌(타격 펀치·천도 캐스팅)은 직교에선 화면 크기, 원근에선 카메라 거리로 만든다
        wheelCut = Mathf.Lerp(wheelCut, judge.cuts.CamZoom, 1f - Mathf.Exp(-4f * dt));   // 컷신 확대 배율도 부드럽게
        float zoomIn = feel.Zoom * 0.06f + judge.CastZoom * 0.09f + (1f - 1f / Mathf.Max(0.3f, wheelCut));   // 배율 1.25 → 20% 다가감
        wheel = Mathf.Lerp(wheel, wheelTarget, 1f - Mathf.Exp(-Balance.CAMERA_WHEEL_SMOOTH * Time.unscaledDeltaTime));   // 휠 줌은 부드럽게 따라간다
        if (judge.clock != null) ClockSky.Apply(sun, cam, judge.clock, player.Pos, dt);   // 하늘·햇빛이 시계를 따른다
        // 줌하면 카메라 각도도 함께 바뀐다: 확대(wheel<1)하면 눕고(몰입), 축소하면 일어선다(지도처럼). 기준 각도는 wheel=1
        Vector3 off = offset;
        if (View3D.On)
        {
            // 각도는 거리 따라 46°(가깝게) ~ 52°(기본) ~ 58°(멀리)로 부드럽게 이어진다 (기획 표준)
            float curD = camDist * wheel;
            float pd = curD <= Balance.CAMERA_DIST_MID
                ? Mathf.Lerp(Balance.CAMERA_PITCH_NEAR, Balance.CAMERA_PITCH_MID, Mathf.InverseLerp(Balance.CAMERA_DIST_NEAR, Balance.CAMERA_DIST_MID, curD))
                : Mathf.Lerp(Balance.CAMERA_PITCH_MID, Balance.CAMERA_PITCH_FAR, Mathf.InverseLerp(Balance.CAMERA_DIST_MID, Balance.CAMERA_DIST_FAR, curD));
            float p = pd * Mathf.Deg2Rad;
            off = new Vector3(Mathf.Cos(camYaw) * Mathf.Cos(p), Mathf.Sin(p), Mathf.Sin(camYaw) * Mathf.Cos(p)) * camDist;
        }
        cam.transform.position = focus + (View3D.On ? off * ((1f - zoomIn) * wheel) : offset);
        cam.transform.LookAt(View3D.On ? focus + Vector3.up * 0.9f : focus);   // 3D 에선 발밑이 아니라 가슴께를 본다
        cam.transform.Rotate(0f, 0f, feel.GetShakeRoll(), Space.Self);   // 충격이 클 때만 화면이 살짝 기울었다 돌아온다
        var s = feel.GetShakeOffset(); // 화면 기준 오른쪽/위쪽으로 밀어 평행하게 떨림
        cam.transform.position += cam.transform.right * s.x + cam.transform.up * s.y;
        cam.transform.position += feel.Kick;   // 맞은 방향으로 툭 밀렸다 돌아오는 카메라
        // 줌: 타격 펀치(최대 6%) + 천도 캐스팅 중 서서히 다가감(최대 9%) — 화면 크기(orthographicSize)를 줄이면 다가간 것
        if (!View3D.On) cam.orthographicSize = Config.CAMERA_VIEW_HEIGHT / 2f * (1f - zoomIn) * wheel;
    }

    // ---- 입력: 마우스 = 이동·대상 / 키보드 = 기술 (PD 피드백 반영) --------------------
    float wheelCut = 1f;                                              // 컷신이 정한 확대 배율(부드럽게 따라감)
    Vector3 CutTarget(string name)
    {
        var boss = judge.NearestBoss();   // 지금 가장 가까운 보스(1·2·3호)
        var bp = boss != null ? new Vector3(boss.Pos.x, 0f, boss.Pos.z) : new Vector3(MapLayout.BossX, 0f, MapLayout.BossZ);
        var pp = new Vector3(player.Pos.x, 0f, player.Pos.z);
        switch (name)
        {
            case "boss": case "boss_boat": return bp;
            case "player_and_boss": return (bp + pp) * 0.5f;
            case "funeral": return new Vector3(JudgeSystem.FuneralX, 0f, JudgeSystem.FuneralZ);   // 박돌쇠 집(대장간) 문 앞 마당(아트 확정 좌표)
            case "forge": return new Vector3(218f, 0f, 62f);              // 대장간 안(건물 모델이 없어 터 좌표만)
            case "far_sky_over_hub": return new Vector3(188f, 0f, 60f);   // 서낭당 쪽 먼 하늘
            default: return pp;
        }
    }
    float wheel = 1f, wheelTarget = 1f;   // 카메라 거리 배율(작을수록 확대). 휠·핀치로 바뀐다
    float pinchPrev;                      // 두 손가락 사이 이전 거리(폰 확대·축소)
    bool kbMove;                          // 지금 WASD 로 걷는 중인가

    /// <summary>휠·핀치로 3단계(가깝게/기본/멀리) 줌. 단계 거리는 balance.json 의 CAMERA_DIST_* (기획 표준: 11/16/20 m)</summary>
    int zoomStep = 1;   // 0=가깝게 1=기본 2=멀리
    float StepDist(int i) { return i <= 0 ? Balance.CAMERA_DIST_NEAR : i == 1 ? Balance.CAMERA_DIST_MID : Balance.CAMERA_DIST_FAR; }
    void SetZoomStep(int i) { if (i != zoomStep && judge != null) judge.guide.Complete("zoom"); zoomStep = Mathf.Clamp(i, 0, 2); wheelTarget = StepDist(zoomStep) / Mathf.Max(0.1f, camDist); }   // 배율 = 목표 거리 / 기준 거리
    void HandleZoom()
    {
        // 휠 한 칸 = 한 단계(앞으로 굴리면 가깝게). 연속 값이 아니라 단계라서 '딱 3번'만 멈춘다
        float scroll = Input.mouseScrollDelta.y;
        if (Mathf.Abs(scroll) > 0.01f) SetZoomStep(zoomStep - (scroll > 0f ? 1 : -1));
        if (Input.touchCount == 2)
        {
            float dist = Vector2.Distance(Input.GetTouch(0).position, Input.GetTouch(1).position);
            // 손가락을 12% 이상 벌리면 한 단계 가깝게, 오므리면 한 단계 멀리. 한 번 바꾸면 기준을 새로 잡아 연속으로 바뀌지 않게 한다
            if (pinchPrev > 0f)
            {
                float ratio = dist / pinchPrev;
                if (ratio > 1.12f) { SetZoomStep(zoomStep - 1); pinchPrev = dist; }
                else if (ratio < 0.88f) { SetZoomStep(zoomStep + 1); pinchPrev = dist; }
            }
            else pinchPrev = dist;
        }
        else pinchPrev = 0f;
    }

    /// <summary>WASD·방향키: 카메라 기준 위/아래/좌/우로 걷는다. 클릭 이동과 함께 쓸 수 있다</summary>
    // ---- 폰: 떠다니는 조이스틱 ----------------------------------------------------
    // 왼쪽 영역을 누르면 그 자리에 조이스틱이 생기고, 끌면 끈 방향으로 걷는다(카메라 기준 위=앞). 떼면 멈추고 사라진다.
    // 오른쪽·아래 버튼 영역은 건드리지 않는다. 터치가 마우스처럼도 들어와 '눌러서 이동'과 겹치므로 영역 안은 OverTouchButtons 가 막는다.
    bool joyActive; int joyFinger = -1; Vector2 joyOrigin, joyPos, joyAxes;   // 화면 좌표(아래가 0)
    Texture2D joyTex;

    bool InJoyZone(Vector2 screenPos)
    {
        if (!Ko.TouchUI) return false;
        if (TouchControls.Over(screenPos)) return false;   // 버튼 판정이 조이스틱보다 먼저(기획 §5)
        float py = Screen.height - screenPos.y;   // GUI 좌표(위가 0)
        return screenPos.x < Screen.width * Balance.JOY_ZONE_WIDTH_FRAC && py > 60f && py < Screen.height - 215f;   // 아래쪽은 천도·파혼·도술 버튼 줄
    }

    void UpdateJoystick()
    {
        if (Input.touchCount == 0) { joyActive = false; joyFinger = -1; joyAxes = Vector2.zero; return; }
        if (!joyActive)
        {
            foreach (var t in Input.touches)
                if (t.phase == TouchPhase.Began && InJoyZone(t.position)) { joyActive = true; joyFinger = t.fingerId; joyOrigin = joyPos = t.position; break; }
            if (!joyActive) return;
        }
        bool found = false;
        foreach (var t in Input.touches)
        {
            if (t.fingerId != joyFinger) continue;
            found = true;
            if (t.phase == TouchPhase.Ended || t.phase == TouchPhase.Canceled) { joyActive = false; joyFinger = -1; joyAxes = Vector2.zero; return; }
            var v = t.position - joyOrigin;
            if (v.magnitude > Balance.JOY_RADIUS_PX) v = v.normalized * Balance.JOY_RADIUS_PX;   // 손잡이는 반지름 안에서만
            joyPos = joyOrigin + v;
            joyAxes = v.magnitude < Balance.JOY_DEADZONE_PX ? Vector2.zero : v / Balance.JOY_RADIUS_PX;
        }
        if (!found) { joyActive = false; joyFinger = -1; joyAxes = Vector2.zero; }
    }

    void DrawJoystick()
    {
        if (!joyActive) return;
        if (joyTex == null)
        {
            joyTex = new Texture2D(64, 64) { filterMode = FilterMode.Bilinear };   // 속이 찬 동그라미(알파 가장자리)
            for (int y = 0; y < 64; y++) for (int x = 0; x < 64; x++) { float d = Vector2.Distance(new Vector2(x, y), new Vector2(31.5f, 31.5f)); joyTex.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(32f - d))); }
            joyTex.Apply();
        }
        float R = Balance.JOY_RADIUS_PX;
        var o = new Vector2(joyOrigin.x, Screen.height - joyOrigin.y); var p = new Vector2(joyPos.x, Screen.height - joyPos.y);
        GUI.color = new Color(1, 1, 1, 0.18f); GUI.DrawTexture(new Rect(o.x - R, o.y - R, R * 2, R * 2), joyTex);
        GUI.color = new Color(1, 1, 1, 0.45f); GUI.DrawTexture(new Rect(p.x - 32, p.y - 32, 64, 64), joyTex);
        GUI.color = Color.white;
    }

    /// <summary>
    /// 아트·PC 캡처용 시작 자리: ?boss=naru|wolhwa|seo 면 그 보스 마당 남쪽 10m(보스가 정면에 보이게)에서, ?pos=x,z 면 그 좌표에서 시작한다.
    /// 마당 꾸밈은 120m 안에서 단계적으로 켜지므로 시작 직후엔 안 보일 수 있다 — 8초 뒤에 찍을 것.
    /// </summary>
    static Vector3 CaptureStart(Vector3 def)
    {
        var u = (Application.absoluteURL ?? "").ToLowerInvariant();
        int bi = u.IndexOf("boss=");
        if (bi >= 0)
        {
            string v = new string(u.Substring(bi + 5).TakeWhile(char.IsLetterOrDigit).ToArray());
            int id = v == "naru" || v == "1" ? 1 : v == "wolhwa" || v == "2" ? 2 : v == "seo" || v == "3" ? 3 : 0;
            if (id > 0) { var bd = Bosses.Get(id); return new Vector3(bd.X, 0f, bd.Z - 10f); }
        }
        int pi = u.IndexOf("pos=");
        if (pi >= 0)
        {
            var parts = new string(u.Substring(pi + 4).TakeWhile(c => char.IsDigit(c) || c == ',' || c == '.' || c == '-').ToArray()).Split(',');
            float x, z;
            if (parts.Length == 2 && float.TryParse(parts[0], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out x) && float.TryParse(parts[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out z)) return new Vector3(x, 0f, z);
        }
        return def;
    }

    void HandleKeyboardMove()
    {
        UpdateJoystick();
        float x = (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow) ? 1f : 0f) - (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow) ? 1f : 0f);
        float z = (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow) ? 1f : 0f) - (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow) ? 1f : 0f);
        if (joyActive) { x = joyAxes.x; z = joyAxes.y; }   // 폰 조이스틱이 눌려 있으면 그 값을 쓴다
        if (Mathf.Abs(x) < 0.01f && Mathf.Abs(z) < 0.01f)
        {
            if (kbMove) { kbMove = false; player.CommandStop(); }   // 키를 떼면 멈춘다(클릭 이동 중이었다면 건드리지 않음)
            return;
        }
        // 카메라가 바라보는 방향(바닥에 눌러 편 것)이 '위'
        var f = cam.transform.forward; f.y = 0f; f = f.sqrMagnitude < 1e-4f ? Vector3.forward : f.normalized;
        var r = new Vector3(f.z, 0f, -f.x);
        var dir = (f * z + r * x).normalized;
        kbMove = true;
        player.CommandMove(player.Pos + dir * 2.5f);   // 목표를 계속 앞에 두어, 도착 감속 없이 이어 걷게 한다
    }

    void HandleInput()
    {
        HandleZoom();
        if (judge.cuts.InputLocked) { kbMove = false; return; }   // 잠금 컷신 중엔 입력이 먹지 않는다
        HandleKeyboardMove();
        Vector3 mouse = Input.mousePosition;
        if (!Ko.TouchUI)   // 적 위에 커서를 올리면 칼 모양(손이 '누르면 때린다'를 미리 안다). 클릭 판정은 1.3배 넓게
        {
            var hray = cam.ScreenPointToRay(mouse);
            bool over = !MiniMap.BigOpen && !CharacterPanel.Open && !SettingsPanel.Open && enemies.Pick(hray, Ground(hray), Config.ENEMY_PICK_RADIUS * 1.3f) != null;
            CursorFx.Set(over ? CursorFx.Kind.Attack : CursorFx.Kind.Default);
        }
        if (Input.GetKeyDown(KeyCode.Q)) { if (player.loadout.Def.HasQuake) player.CommandQuake(); else if (player.loadout.Def.HasPull) SkillPull(mouse); }   // Q: 철삭=견인 / 육모방망이=땅울림 / 그 외 무기는 없음
        if (Input.GetKeyDown(KeyCode.Space)) SkillDodge(mouse); // Space: 피하기(구르기). 휘두르기는 마우스 클릭으로 충분하다(기획 타격감 분석)
        if (Input.GetMouseButtonDown(1) && !OverTouchButtons(mouse)) SkillSwing(mouse);   // 우클릭: 커서 방향으로 그 자리에서 즉시 공격(명세 v1.2). 견인은 Q 만

        if (Input.GetMouseButtonDown(0) && !OverTouchButtons(mouse))
        {
            var ray = cam.ScreenPointToRay(mouse);
            var ground = Ground(ray);
            var e = enemies.Pick(ray, ground, Config.ENEMY_PICK_RADIUS * 1.3f);   // 클릭 판정 1.3배(명세 §3-3)
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
        judge.guide.Complete("pull");
        var ray = cam.ScreenPointToRay(screen);
        var g = Ground(ray);
        var e = enemies.Pick(ray, g, Config.PULL_PICK_RADIUS);
        player.CommandPull(e, g ?? player.Pos);
    }

    /// <summary>피하기: 마우스가 있는 쪽으로. 마우스 위치를 못 구하면 걷던 방향</summary>
    void SkillDodge(Vector3 screen)
    {
        judge.guide.Complete("dodge");
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
    bool OverTouchButtons(Vector3 mouse)
    {
        if (!Ko.TouchUI) return false;
        if (InJoyZone(mouse) || joyActive) return true;   // 조이스틱 영역은 '눌러서 이동'이 아니다
        return TouchControls.Over(mouse) || MiniMap.OverMini(mouse);   // 공격·도술·피하기 같은 새 터치 버튼(TouchControls)
    }

    void OnGUI()
    {
        Ko.Apply(); // 한글 글꼴 적용(안 하면 한글이 네모로 깨짐)
        if (judge.InDay || CharacterPanel.Open || SettingsPanel.Open || judge.NightOver) return;   // 낮 화면·캐릭터 창에서는 밤의 안내·버튼을 그리지 않는다
        // 상시 조작 안내 줄은 지웠다(기획 표준). 안내는 처음 해당 행동이 필요할 때 하나씩 띄운다(TutorialHints)
        if (!Ko.TouchUI) return;
        DrawJoystick();
    }

    /// <summary>폰 조작 버튼(TouchControls)에 동작을 연결한다. 키보드·마우스와 같은 함수를 부르므로 규칙이 갈라지지 않는다</summary>
    void WireTouchControls()
    {
        var tc = gameObject.AddComponent<TouchControls>();
        tc.hasPull = () => player.loadout.Def.HasPull;
        tc.canInteract = () => judge.CanInteractNow;
        tc.interactLabel = () => judge.TargetLabel;
        tc.skillLabel = i => judge.ActiveNameAt(i);
        tc.skillLeft = i => judge.SkillLeft(i);
        tc.onSkill = i => judge.UseSkill(i);
        tc.onDodge = () => { judge.guide.Complete("dodge"); player.CommandDodge(null); };   // 걷던 방향으로(가운데면 앞쪽)
        tc.onPull = () => { judge.guide.Complete("pull"); var e = Nearest(); player.CommandPull(e, e != null ? e.Pos : player.Pos); };
        tc.onAttackHold = () =>   // 누르고 있으면 6m 안 가장 가까운 적을 자동 조준해 연속 공격
        {
            Enemy best = null; float bd = 6f;
            foreach (var e in enemies.list) { if (!e.alive || !e.Targetable) continue; float d = Vector3.Distance(e.Pos, player.Pos); if (d <= bd) { bd = d; best = e; } }
            if (best != null) player.CommandAttack(best); else player.CommandSwing(player.Pos + U.Dir(player.facing));
        };
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
