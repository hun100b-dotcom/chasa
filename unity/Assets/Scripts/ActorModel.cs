// =============================================================================
// ActorModel.cs — 새 화면(?v=3d)의 '3D 대역 인형'. 도형을 이어 붙여 만든 사람형·혼 모양에 코드로 움직임을 준다.
//
// 대역(stand-in)이란? 최종 그림이 오기 전에 자리를 지키는 임시 모델. 카메라·조명·움직임을 먼저 맞추려고 쓴다.
// 왜 외부 3D 파일이 아니라 도형인가?
//   · 외부 모델은 가져오기(임포트) 작업과 라이선스 확인이 필요하다. 도형은 파일 없이 바로 빌드에 들어간다.
//   · 나중에 아트팀 3D 모델이 오면 'ModelSlot'(Resources/Models/<이름> 프리팹)에 넣으면 이 인형 대신 쓰이도록 자리를 만들어 뒀다.
// 움직임: 서기(숨쉬기) · 걷기(팔다리 흔들기) · 공격(팔 휘두르기) · 맞음(젖힘) · 천도 자세(팔 들기) · 무릎 꿇음 · 피하기(앞으로 숙임).
// ActorSprite 가 그림 이름(예: characters/chasa_swing)을 알려 주면 여기서 상태로 바꿔 쓴다 → 전투 코드는 그대로.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

public class ActorModel : MonoBehaviour
{
    public enum Pose { Idle, Walk, Attack, Hit, Cast, Kneel, Dodge }

    // 모양 설명서: 이름에서 골라 쓴다
    struct Spec
    {
        public string key; public float height; public Color body, accent; public bool legs, horns, blob, hat; public float glow;
    }

    GameObject modelRoot;                 // 실제 인형(자식). ActorSprite 와 따로 방향을 가진다
    Transform hips, torso, head, armL, armR, legL, legR;
    Renderer[] rends; Material[] mats; Color[] baseCol;
    string key;
    Pose pose = Pose.Idle; float poseT;
    float walkPhase, yaw, lastYawSet;
    Vector3 lastPos;
    float speed;                          // 이동 속도(m/s) — 걷기 판정에 쓴다
    bool hasGlow; float glowAmt;

    // ---- 모델 슬롯: Resources/Models/Hero 에 CC0 3D 모델(Kenney 캐릭터)이 있으면 도형 인형 대신 그것을 쓴다 ----
    GameObject hero;                         // 있으면 진짜 모델
    PlayableGraph graph; AnimationMixerPlayable mixer;
    readonly Dictionary<Pose, int> heroInput = new Dictionary<Pose, int>();
    readonly List<AnimationClip> heroClips = new List<AnimationClip>();
    AnimationClipPlayable[] heroPlayables;
    int heroCur = -1; float heroT;
    const string HeroPath = "Models/Hero/character-male-a";
    const float HeroScale = 2.7f;            // Kenney 미니 캐릭터는 키 0.67m → 1.8m 로

    // 동작 → 모델에 들어 있는 움직임 이름. 맞음(Hit) 전용 움직임이 없어 고개 젓기로 대신한다
    static string ClipFor(Pose p)
    {
        switch (p)
        {
            case Pose.Walk: return "walk";
            case Pose.Attack: return "attack-melee-right";
            case Pose.Hit: return "emote-no";
            case Pose.Cast: return "pick-up";
            case Pose.Kneel: return "crouch";
            case Pose.Dodge: return "sprint";
            default: return "idle";
        }
    }

    bool TryBuildHero()
    {
        var prefab = Resources.Load<GameObject>(HeroPath);
        if (prefab == null) return false;
        hero = Instantiate(prefab, modelRoot.transform);
        hero.transform.localPosition = Vector3.zero; hero.transform.localRotation = Quaternion.identity;
        hero.transform.localScale = Vector3.one * HeroScale;
        // 재질은 가져오지 않았으므로(색 팔레트는 코드에서) 색 지도(colormap) 한 장을 입힌 무광 재질을 만든다
        var tex = Resources.Load<Texture2D>("Models/Hero/colormap");
        var rl = new List<Material>();
        foreach (var r in hero.GetComponentsInChildren<Renderer>())
        {
            var m = U.Flashable(Color.white);
            if (tex != null) m.mainTexture = tex;
            r.sharedMaterial = m; rl.Add(m);
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On; r.receiveShadows = true;
        }
        mats = rl.ToArray(); baseCol = new Color[mats.Length]; for (int i = 0; i < baseCol.Length; i++) baseCol[i] = Color.white;
        hasGlow = false;
        // 움직임: 컨트롤러 없이 코드로 재생(Playables = 움직임 조각을 섞는 유니티 기능). 상태가 바뀌면 부드럽게 섞어 넘긴다
        var anim = hero.GetComponentInChildren<Animator>();
        if (anim == null) anim = hero.AddComponent<Animator>();
        var all = Resources.LoadAll<AnimationClip>(HeroPath);
        var byName = new Dictionary<string, AnimationClip>();
        foreach (var c in all) if (!c.name.StartsWith("__")) byName[c.name] = c;
        graph = PlayableGraph.Create("Hero");
        graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);   // 우리가 직접 시간을 흘린다(히트스톱과 무관하게 부드럽게)
        var output = AnimationPlayableOutput.Create(graph, "out", anim);
        var order = new[] { Pose.Idle, Pose.Walk, Pose.Attack, Pose.Hit, Pose.Cast, Pose.Kneel, Pose.Dodge };
        mixer = AnimationMixerPlayable.Create(graph, order.Length);
        heroPlayables = new AnimationClipPlayable[order.Length];
        for (int i = 0; i < order.Length; i++)
        {
            AnimationClip clip; if (!byName.TryGetValue(ClipFor(order[i]), out clip) && !byName.TryGetValue("idle", out clip)) continue;
            heroPlayables[i] = AnimationClipPlayable.Create(graph, clip);
            graph.Connect(heroPlayables[i], 0, mixer, i);
            mixer.SetInputWeight(i, i == 0 ? 1f : 0f);
            heroInput[order[i]] = i; heroClips.Add(clip);
        }
        if (heroInput.Count == 0) { graph.Destroy(); Destroy(hero); hero = null; return false; }
        output.SetSourcePlayable(mixer);
        graph.Play();
        heroCur = 0;
        return true;
    }

    void HeroUpdate(float dt, bool moving)
    {
        var want = pose == Pose.Idle && moving ? Pose.Walk : pose;
        if (want == Pose.Walk && !moving && pose == Pose.Walk) want = Pose.Idle;
        int idx; if (!heroInput.TryGetValue(want, out idx)) idx = 0;
        if (idx != heroCur) { heroCur = idx; heroT = 0f; }   // 새 동작은 처음부터
        heroT += dt;
        // 가중치를 부드럽게 옮긴다 (0.12초 안팎 크로스페이드)
        for (int i = 0; i < mixer.GetInputCount(); i++)
        {
            float w = mixer.GetInputWeight(i), target = i == idx ? 1f : 0f;
            mixer.SetInputWeight(i, Mathf.MoveTowards(w, target, dt / 0.12f));
            var pl = heroPlayables[i];
            if (!pl.IsValid()) continue;
            float len = pl.GetAnimationClip().length;
            // 반복 동작(서기·걷기·무릎 꿇음 자세)은 돌고, 한 번짜리(공격·맞음·천도)는 처음부터 한 번
            bool loop = i == heroInput[Pose.Idle] || i == heroInput[Pose.Walk] || i == heroInput[Pose.Kneel] || i == heroInput[Pose.Dodge];
            if (i == idx) pl.SetTime(loop ? heroT % Mathf.Max(0.01f, len) : Mathf.Min(heroT, len - 0.001f));
        }
        graph.Evaluate(0f);
        // 피하기·무릎 꿇음 때 몸 높이(미끄러짐 방지용 보정은 하지 않는다 — 대역이라 단순하게)
    }

    void OnDestroy() { if (graph.IsValid()) graph.Destroy(); }

    public static ActorModel Create(Transform parent)
    {
        var go = new GameObject("ActorModel");
        go.transform.SetParent(parent, false);
        return go.AddComponent<ActorModel>();
    }

    // ---- 이름 → 모양 -----------------------------------------------------------
    static Spec SpecFor(string name)
    {
        var s = new Spec { legs = true };
        if (name.Contains("chasa"))      // 동이 대역: 검은 도포, 붉은 띠, 갓
        { s.key = "dongi"; s.height = 1.8f; s.body = new Color(0.10f, 0.11f, 0.17f); s.accent = new Color(0.62f, 0.12f, 0.12f); s.hat = true; s.glow = 0f; }
        else if (name.Contains("boss"))  // 나루 영감: 크고 보랏빛, 뿔 없이 긴 도포
        { s.key = "boss"; s.height = 3.2f; s.body = new Color(0.40f, 0.30f, 0.60f); s.accent = new Color(0.8f, 0.7f, 1f); s.legs = false; s.glow = 0.5f; }
        else if (name.Contains("lump"))  // 덩어리: 뭉친 한 덩이
        { s.key = "lump"; s.height = 1.5f; s.body = new Color(0.30f, 0.14f, 0.16f); s.accent = new Color(0.8f, 0.25f, 0.2f); s.blob = true; s.legs = false; s.glow = 0.3f; }
        else if (name.Contains("fierce")) // 사나운 적: 붉고 뿔 달림
        { s.key = "fierce"; s.height = 2.0f; s.body = new Color(0.65f, 0.12f, 0.12f); s.accent = new Color(1f, 0.55f, 0.3f); s.horns = true; s.legs = false; s.glow = 0.6f; }
        else if (name.Contains("soul_old"))   // 오래된 혼: 잿빛 보라, 구부정, 작다
        { s.key = "old"; s.height = 1.5f; s.body = new Color(0.45f, 0.40f, 0.52f); s.accent = new Color(0.7f, 0.65f, 0.8f); s.legs = false; s.glow = 0.35f; }
        else if (name.Contains("soul_day"))   // 해 넘긴 혼: 누런빛, 보통
        { s.key = "year"; s.height = 1.75f; s.body = new Color(0.80f, 0.70f, 0.35f); s.accent = new Color(1f, 0.92f, 0.6f); s.legs = false; s.glow = 0.5f; }
        else                                   // 갓 죽은 혼: 맑은 청백, 크다
        { s.key = "fresh"; s.height = 1.95f; s.body = new Color(0.65f, 0.82f, 1f); s.accent = new Color(0.9f, 0.97f, 1f); s.legs = false; s.glow = 0.7f; }
        return s;
    }

    static Pose PoseFor(string name)
    {
        if (name.Contains("kneel")) return Pose.Kneel;
        if (name.Contains("dodge")) return Pose.Dodge;
        if (name.Contains("cast")) return Pose.Cast;
        if (name.Contains("hit")) return Pose.Hit;
        if (name.Contains("swing") || name.Contains("bang") || name.Contains("attack")) return Pose.Attack;
        if (name.Contains("walk")) return Pose.Walk;
        return Pose.Idle;
    }

    /// <summary>그림 이름·보는 방향·색조를 받아 인형을 갱신한다 (ActorSprite.Show 에서 부른다)</summary>
    public void Show(string name, Vector3 facing, Color tint)
    {
        var spec = SpecFor(name);
        if (key != spec.key) Build(spec);
        var p = PoseFor(name);
        if (p != pose) { pose = p; poseT = 0f; }
        facing.y = 0f;
        if (facing.sqrMagnitude > 1e-4f) yaw = Mathf.Atan2(facing.x, facing.z) * Mathf.Rad2Deg;   // 유니티: +z 가 앞(0도)
        // 색조: 예비동작 붉음·맞은 번쩍(흰색)을 재질에 반영
        for (int i = 0; i < mats.Length; i++)
        {
            mats[i].color = baseCol[i] * new Color(tint.r, tint.g, tint.b, 1f);
            if (hasGlow && hero == null) mats[i].SetColor("_EmissionColor", baseCol[i] * glowAmt + Color.white * Mathf.Max(0f, (tint.g + tint.b) * 0.5f - 0.7f) * 1.2f);
        }
    }

    // ---- 만들기 ------------------------------------------------------------------
    void Build(Spec sp)
    {
        key = sp.key;
        if (modelRoot != null) Destroy(modelRoot);
        modelRoot = new GameObject("Model_" + sp.key);
        modelRoot.transform.SetParent(transform, false);
        if (sp.key == "dongi" && TryBuildHero()) { modelRoot.transform.localRotation = Quaternion.Euler(0, yaw, 0); return; }   // 슬롯에 진짜 모델이 있으면 그걸 쓴다
        var rl = new System.Collections.Generic.List<Renderer>();
        var ml = new System.Collections.Generic.List<Material>();
        var cl = new System.Collections.Generic.List<Color>();
        float H = sp.height;
        hasGlow = sp.glow > 0f; glowAmt = sp.glow;

        Transform Part(string n, PrimitiveType t, Transform parent, Vector3 pos, Vector3 scale, Color c, Vector3? euler = null)
        {
            var g = GameObject.CreatePrimitive(t);
            Destroy(g.GetComponent<Collider>());
            g.name = n; g.transform.SetParent(parent, false);
            g.transform.localPosition = pos; g.transform.localScale = scale;
            if (euler.HasValue) g.transform.localEulerAngles = euler.Value;
            var r = g.GetComponent<Renderer>();
            var m = U.Flashable(c);   // 번쩍임·발광을 받을 수 있는 재질(빛은 그대로 받는다)
            r.sharedMaterial = m;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On; r.receiveShadows = true;
            rl.Add(r); ml.Add(m); cl.Add(c);
            return g.transform;
        }
        Transform Pivot(string n, Transform parent, Vector3 pos)
        {
            var g = new GameObject(n); g.transform.SetParent(parent, false); g.transform.localPosition = pos; return g.transform;
        }

        if (sp.blob)
        {
            // 덩어리: 찌그러진 구 + 박힌 작은 구들 (사람 모양이 아님 = 한눈에 구분)
            hips = Pivot("hips", modelRoot.transform, Vector3.zero); torso = Pivot("torso", hips, new Vector3(0, H * 0.5f, 0));
            Part("blob", PrimitiveType.Sphere, torso, Vector3.zero, new Vector3(H * 1.05f, H * 0.95f, H * 1.0f), sp.body);
            Part("b1", PrimitiveType.Sphere, torso, new Vector3(H * 0.35f, H * 0.25f, 0.1f), Vector3.one * H * 0.4f, sp.accent);
            Part("b2", PrimitiveType.Sphere, torso, new Vector3(-H * 0.3f, -H * 0.1f, 0.2f), Vector3.one * H * 0.33f, sp.accent * 0.8f);
            head = torso; armL = armR = legL = legR = null;
        }
        else
        {
            float legH = sp.legs ? H * 0.45f : 0f;
            hips = Pivot("hips", modelRoot.transform, new Vector3(0, legH, 0));
            torso = Pivot("torso", hips, Vector3.zero);
            float torsoH = H * (sp.legs ? 0.32f : 0.52f);
            // 몸통: 다리가 있으면 짧은 캡슐, 혼은 아래로 퍼지는 긴 몸(치맛자락처럼)
            if (sp.legs) Part("torso", PrimitiveType.Capsule, torso, new Vector3(0, torsoH * 0.5f, 0), new Vector3(H * 0.26f, torsoH * 0.62f, H * 0.18f), sp.body);
            else
            {
                Part("body", PrimitiveType.Capsule, torso, new Vector3(0, torsoH * 0.5f - legH * 0.0f + H * 0.18f, 0), new Vector3(H * 0.30f, torsoH * 0.62f + H * 0.12f, H * 0.24f), sp.body);
                Part("skirt", PrimitiveType.Cylinder, torso, new Vector3(0, H * 0.14f, 0), new Vector3(H * 0.34f, H * 0.14f, H * 0.28f), sp.body * 0.85f);
            }
            float neckY = (sp.legs ? torsoH : torsoH + H * 0.22f);
            if (sp.legs) Part("sash", PrimitiveType.Cylinder, torso, new Vector3(0, torsoH * 0.35f, 0), new Vector3(H * 0.27f, H * 0.018f, H * 0.19f), sp.accent);
            head = Pivot("head", torso, new Vector3(0, neckY, 0));
            Part("head", PrimitiveType.Sphere, head, new Vector3(0, H * 0.075f, 0), Vector3.one * H * 0.17f, sp.legs ? new Color(0.78f, 0.62f, 0.5f) : sp.accent);
            if (sp.hat)   // 갓: 넓은 챙 + 원통 (저승차사 실루엣)
            {
                Part("brim", PrimitiveType.Cylinder, head, new Vector3(0, H * 0.14f, 0), new Vector3(H * 0.34f, H * 0.008f, H * 0.34f), new Color(0.05f, 0.05f, 0.06f));
                Part("crown", PrimitiveType.Cylinder, head, new Vector3(0, H * 0.18f, 0), new Vector3(H * 0.15f, H * 0.04f, H * 0.15f), new Color(0.07f, 0.07f, 0.09f));
            }
            if (sp.horns)
            {
                Part("hornL", PrimitiveType.Capsule, head, new Vector3(-H * 0.07f, H * 0.17f, 0), new Vector3(H * 0.03f, H * 0.05f, H * 0.03f), sp.accent, new Vector3(0, 0, 25));
                Part("hornR", PrimitiveType.Capsule, head, new Vector3(H * 0.07f, H * 0.17f, 0), new Vector3(H * 0.03f, H * 0.05f, H * 0.03f), sp.accent, new Vector3(0, 0, -25));
            }
            float shY = sp.legs ? torsoH * 0.9f : torsoH + H * 0.1f;
            armL = Pivot("armL", torso, new Vector3(-H * 0.17f, shY, 0));
            armR = Pivot("armR", torso, new Vector3(H * 0.17f, shY, 0));
            Part("armL", PrimitiveType.Capsule, armL, new Vector3(0, -H * 0.14f, 0), new Vector3(H * 0.07f, H * 0.14f, H * 0.07f), sp.body * 1.1f);
            Part("armR", PrimitiveType.Capsule, armR, new Vector3(0, -H * 0.14f, 0), new Vector3(H * 0.07f, H * 0.14f, H * 0.07f), sp.body * 1.1f);
            if (sp.legs)
            {
                legL = Pivot("legL", hips, new Vector3(-H * 0.07f, 0, 0));
                legR = Pivot("legR", hips, new Vector3(H * 0.07f, 0, 0));
                Part("legL", PrimitiveType.Capsule, legL, new Vector3(0, -legH * 0.5f, 0), new Vector3(H * 0.09f, legH * 0.5f, H * 0.09f), new Color(0.07f, 0.07f, 0.10f));
                Part("legR", PrimitiveType.Capsule, legR, new Vector3(0, -legH * 0.5f, 0), new Vector3(H * 0.09f, legH * 0.5f, H * 0.09f), new Color(0.07f, 0.07f, 0.10f));
            }
            else legL = legR = null;
        }
        rends = rl.ToArray(); mats = ml.ToArray(); baseCol = cl.ToArray();
        modelRoot.transform.localRotation = Quaternion.Euler(0, yaw, 0);
    }

    // ---- 움직임 ------------------------------------------------------------------
    void LateUpdate()
    {
        if (modelRoot == null) return;
        float dt = Time.deltaTime;
        poseT += dt;
        // 이동 속도 = 위치 변화 (걷기 판정). 슬로모·히트스톱 중엔 dt 가 달라 값이 흔들릴 수 있어 부드럽게
        var p = transform.parent != null ? transform.parent.position : transform.position;
        float sp = dt > 0f ? new Vector2(p.x - lastPos.x, p.z - lastPos.z).magnitude / dt : 0f; lastPos = p;
        speed = Mathf.Lerp(speed, sp, 0.3f);
        // 방향: 목표 각도로 빠르게 돈다(순간 회전은 부자연스럽다)
        var cur = modelRoot.transform.localEulerAngles.y;
        modelRoot.transform.localRotation = Quaternion.Euler(0, Mathf.LerpAngle(cur, yaw, 1f - Mathf.Exp(-18f * dt)), 0);

        bool moving = speed > 0.6f && (pose == Pose.Idle || pose == Pose.Walk);
        if (hero != null) { HeroUpdate(dt, moving); return; }   // 진짜 모델은 자기 움직임으로
        if (moving) walkPhase += dt * Mathf.Clamp(speed * 1.1f, 4f, 13f);
        float swing = moving ? Mathf.Sin(walkPhase) : 0f;
        float t = Time.time;

        // 기본 자세로 되돌린 뒤 상태별로 덮는다
        Set(hips, new Vector3(0, hipsBase(), 0), Vector3.zero);
        Set(torso, Vector3.zero, Vector3.zero);
        Rot(head, Vector3.zero); Rot(armL, Vector3.zero); Rot(armR, Vector3.zero); Rot(legL, Vector3.zero); Rot(legR, Vector3.zero);

        float bob = Mathf.Sin(t * 2.2f + GetInstanceID()) * 0.02f;
        hips.localPosition += new Vector3(0, bob + (moving ? Mathf.Abs(swing) * 0.05f : 0f), 0);   // 숨쉬기/걸을 때 위아래

        switch (pose)
        {
            case Pose.Walk: case Pose.Idle:
                Rot(legL, new Vector3(swing * 38f, 0, 0)); Rot(legR, new Vector3(-swing * 38f, 0, 0));
                Rot(armL, new Vector3(-swing * 30f, 0, 0)); Rot(armR, new Vector3(swing * 30f, 0, 0));
                if (legL == null) Rot(torso, new Vector3(moving ? 8f : 0f, 0, Mathf.Sin(t * 1.7f + GetInstanceID()) * 3f));   // 혼은 떠다니며 살짝 기울어짐
                break;
            case Pose.Attack:
            {
                // 휘두르기: 팔을 뒤로 젖혔다가 앞으로 크게 (0.33초 주기), 몸통은 팔을 따라 비틈
                float k = Mathf.Repeat(poseT * 3f, 1f), a = Mathf.Lerp(-140f, 70f, k * k);
                Rot(armR, new Vector3(a, 0, 15f)); Rot(armL, new Vector3(-30f, 0, -10f));
                Rot(torso, new Vector3(0, Mathf.Lerp(-35f, 40f, k), 0));
                if (legL != null) { Rot(legL, new Vector3(25f, 0, 0)); Rot(legR, new Vector3(-30f, 0, 0)); }
                break;
            }
            case Pose.Hit:
                Rot(torso, new Vector3(-28f, 0, 6f)); Rot(armL, new Vector3(-50f, 0, -20f)); Rot(armR, new Vector3(-50f, 0, 20f));
                hips.localPosition += new Vector3(0, -0.05f, 0);
                break;
            case Pose.Cast:
                // 천도 자세: 두 팔을 위로 모으고 몸이 떠오르듯 흔들림
                Rot(armL, new Vector3(-155f, 0, -12f)); Rot(armR, new Vector3(-155f, 0, 12f));
                hips.localPosition += new Vector3(0, 0.08f + Mathf.Sin(t * 6f) * 0.03f, 0);
                Rot(torso, new Vector3(-6f, 0, 0));
                break;
            case Pose.Kneel:
                // 무릎 꿇음: 몸이 낮아지고 고개 숙임 (한눈에 '처결 대기'가 보이게)
                hips.localPosition += new Vector3(0, -hipsBase() * 0.42f, 0);
                Rot(torso, new Vector3(18f, 0, 0)); Rot(head, new Vector3(25f, 0, 0));
                Rot(armL, new Vector3(25f, 0, -8f)); Rot(armR, new Vector3(25f, 0, 8f));
                if (legL != null) { Rot(legL, new Vector3(-80f, 0, 0)); Rot(legR, new Vector3(-80f, 0, 0)); }
                break;
            case Pose.Dodge:
                Rot(torso, new Vector3(38f, 0, 0)); hips.localPosition += new Vector3(0, -0.18f, 0);
                Rot(armL, new Vector3(-60f, 0, -15f)); Rot(armR, new Vector3(-60f, 0, 15f));
                if (legL != null) { Rot(legL, new Vector3(-45f, 0, 0)); Rot(legR, new Vector3(35f, 0, 0)); }
                break;
        }
    }

    float hipsBase() { return hips != null && legL != null ? 0.45f * HeightOfKey() : (key == "lump" ? 0f : 0f); }
    float HeightOfKey() { switch (key) { case "dongi": return 1.8f; case "boss": return 3.2f; case "lump": return 1.5f; case "fierce": return 2.0f; case "old": return 1.5f; case "year": return 1.75f; default: return 1.95f; } }

    static void Set(Transform t, Vector3 pos, Vector3 euler) { if (t == null) return; t.localPosition = pos; t.localEulerAngles = euler; }
    static void Rot(Transform t, Vector3 euler) { if (t != null) t.localEulerAngles = euler; }
}
