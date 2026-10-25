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
using Chasa.Core;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

public class ActorModel : MonoBehaviour
{
    public enum Pose { Idle, Walk, Attack, Hit, Cast, Kneel, Dodge, Attack2, Attack3, Pahon, Draw, Hit2, Stagger, Tendo, RunStart, RunStop, Judge, KneelHold }   // Judge: 무릎 꿇은 혼 앞에서 천도·파혼을 고르는 자세(갓 숙임·왼손 혼불)   // Attack2·3 은 모델 동작 전용(콤보 2·3타). 도형 대역은 Attack 하나를 쓴다

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
    Pose atkPose = Pose.Attack;           // 지금 공격이 쓸 모델 동작(1·2·3타)
    float heroSpeed = 1f;                 // 한 번짜리 동작(공격) 재생 속도 배율 — 타격 순간을 판정 시각에 맞추려고
    float walkPhase, yaw, lastYawSet, leanNow, bankNow;   // 몸 기울임(앞으로/옆으로, 도)
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
    ModelCatalog.ActorRow heroRow;           // models.json 의 이 배우 줄

    static string ClipName(ModelCatalog.ActorRow row, Pose p)
    {
        if (row.clips != null) foreach (var c in row.clips) if (c.pose == p.ToString()) return c.clip;
        return null;
    }

    bool TryBuildHero(string key)
    {
        heroRow = ModelCatalog.Actor(key);
        if (heroRow == null) return false;
        var prefab = Resources.Load<GameObject>(heroRow.path);
        if (prefab == null) return false;
        hero = Instantiate(prefab, modelRoot.transform);
        hero.transform.localPosition = Vector3.zero; hero.transform.localRotation = Quaternion.Euler(0f, heroRow.yaw, 0f);
        hero.transform.localScale = Vector3.one * heroRow.scale;
        // 모델 표의 hide: 그 이름으로 시작하는 노드를 끈다(같은 모델을 장면마다 다르게 쓰려고. 흑월 1차는 눈이 안 쌓인 모습)
        if (heroRow.hide != null && heroRow.hide.Length > 0)
            foreach (var t in hero.GetComponentsInChildren<Transform>(true))
                foreach (var h in heroRow.hide) if (t.name.StartsWith(h)) { t.gameObject.SetActive(false); break; }
        // 모델 표의 light: 머리 뼈에 약한 점광원을 달아 '붉게 빛나는 눈' 둘레가 어둠 속에서 번지게 한다(발광 재질만으론 주변이 안 밝아서)
        if (heroRow.light != null && heroRow.light.Length >= 4)
            foreach (var t in hero.GetComponentsInChildren<Transform>(true))
                if (t.name == "Head") { var lg = new GameObject("EyeGlow"); lg.transform.SetParent(t, false); lg.transform.localPosition = new Vector3(0f, 0.1f, 0.3f); var l = lg.AddComponent<Light>(); l.type = LightType.Point; l.color = new Color(heroRow.light[0], heroRow.light[1], heroRow.light[2]); l.intensity = heroRow.light[3]; l.range = 4f; l.shadows = LightShadows.None; break; }
        // 재질은 가져오지 않았으므로(색 팔레트는 코드에서) 색 지도(colormap) 한 장을 입힌 무광 재질을 만든다
        var tex = string.IsNullOrEmpty(heroRow.texture) ? null : Resources.Load<Texture2D>(heroRow.texture);
        var rl = new List<Material>(); var cl = new List<Color>();
        foreach (var r in hero.GetComponentsInChildren<Renderer>())
        {
            if (tex != null)
            {
                var m = U.Flashable(Color.white); m.mainTexture = tex;   // 색 지도 한 장 쓰는 모델(켄니)
                r.sharedMaterial = m; rl.Add(m); cl.Add(Color.white);
            }
            else
            {
                // 색 지도가 없는 모델(아트팀 GLB): 재질 칸마다 원래 색을 따서 번쩍 가능한 재질로 바꾼다
                var src = r.sharedMaterials; var dst = new Material[src.Length];
                for (int i = 0; i < src.Length; i++) { var c = Props3D.MatColor(src[i]); dst[i] = U.Flashable(c); rl.Add(dst[i]); cl.Add(c); }
                r.sharedMaterials = dst;
            }
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On; r.receiveShadows = true;
        }
        mats = rl.ToArray(); baseCol = cl.ToArray();
        hasGlow = false;
        // 움직임: 컨트롤러 없이 코드로 재생(Playables = 움직임 조각을 섞는 유니티 기능). 상태가 바뀌면 부드럽게 섞어 넘긴다
        var anim = hero.GetComponentInChildren<Animator>();
        if (anim == null) anim = hero.AddComponent<Animator>();
        var all = Resources.LoadAll<AnimationClip>(heroRow.path);
        var byName = new Dictionary<string, AnimationClip>();
        foreach (var c in all) if (!c.name.StartsWith("__")) byName[c.name] = c;
        clipsByName = byName; heroOrder = new[] { Pose.Idle, Pose.Walk, Pose.Attack, Pose.Hit, Pose.Cast, Pose.Kneel, Pose.Dodge, Pose.Attack2, Pose.Attack3, Pose.Pahon, Pose.Draw, Pose.Hit2, Pose.Stagger, Pose.Tendo, Pose.RunStart, Pose.RunStop, Pose.Judge, Pose.KneelHold };
        graph = PlayableGraph.Create("Hero");
        graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);   // 우리가 직접 시간을 흘린다(히트스톱과 무관하게 부드럽게)
        var output = AnimationPlayableOutput.Create(graph, "out", anim);
        var order = heroOrder;
        mixer = AnimationMixerPlayable.Create(graph, order.Length);
        heroPlayables = new AnimationClipPlayable[order.Length];
        for (int i = 0; i < order.Length; i++)
        {
            AnimationClip clip; var cn = ClipName(heroRow, order[i]);
            if (order[i] == Pose.KneelHold && (cn == null || !byName.ContainsKey(cn))) continue;   // 무릎 꿇고 기다리는 반복 동작은 있는 모델만(없으면 Kneel 마지막 장면 유지)
            if (cn == null && (order[i] == Pose.Attack2 || order[i] == Pose.Attack3)) cn = ClipName(heroRow, Pose.Attack);   // 2·3타 동작이 표에 없으면 1타 동작을 쓴다
            if ((cn == null || !byName.TryGetValue(cn, out clip)) && !byName.TryGetValue(ClipName(heroRow, Pose.Idle) ?? "idle", out clip)) continue;
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

    Dictionary<string, AnimationClip> clipsByName; Pose[] heroOrder;

    static string WeaponClipPrefix(WeaponId w)
    {
        switch (w) { case WeaponId.Mace: return "Mace"; case WeaponId.Bell: return "Bell"; case WeaponId.Trident: return "Trident"; case WeaponId.Brush: return "Brush"; default: return null; }
    }

    /// <summary>무기별 소매동작 규칙: 아트가 무기마다 만든 1·2·3타(Mace_Attack1…)와 천도(Mace_Tendo)가 있으면 그것으로 갈아 끼운다. 철삭은 기본 동작</summary>
    void RetargetWeaponClips()
    {
        if (hero == null || heroPlayables == null || clipsByName == null) return;
        string pre = WeaponClipPrefix(wantWeapon);
        for (int i = 0; i < heroOrder.Length; i++)
        {
            var po = heroOrder[i]; string want = null;
            if (po == Pose.Attack) want = pre != null ? pre + "_Attack1" : ClipName(heroRow, Pose.Attack);
            else if (po == Pose.Attack2) want = pre != null ? pre + "_Attack2" : (ClipName(heroRow, Pose.Attack2) ?? ClipName(heroRow, Pose.Attack));
            else if (po == Pose.Attack3) want = pre != null ? pre + "_Attack3" : (ClipName(heroRow, Pose.Attack3) ?? ClipName(heroRow, Pose.Attack));
            else if (po == Pose.Cast) want = pre != null ? pre + "_Tendo" : ClipName(heroRow, Pose.Cast);
            else if (po == Pose.Pahon) want = pre != null ? pre + "_Pahon" : "Pahon";   // 파혼 전용 동작(철삭은 기본 Pahon)
            else if (po == Pose.Draw) want = (pre ?? "Chain") + "_Draw";                 // 무기 바꿔 들기 동작
            else continue;
            AnimationClip clip;
            if (want == null || !clipsByName.TryGetValue(want, out clip)) continue;   // 전용 동작이 없으면 지금 것을 그대로
            if (!heroPlayables[i].IsValid() || heroPlayables[i].GetAnimationClip() == clip) continue;
            graph.Disconnect(mixer, i); heroPlayables[i].Destroy();
            heroPlayables[i] = AnimationClipPlayable.Create(graph, clip);
            graph.Connect(heroPlayables[i], 0, mixer, i);
            mixer.SetInputWeight(i, i == heroCur ? 1f : 0f);
        }
    }

    bool wasMoving, kneelHold; float startT, stopT, runTime;
    void HeroUpdate(float dt, bool moving)
    {
        var want = pose == Pose.Idle && moving ? Pose.Walk : pose;
        // 출발·정지 동작(아트 HERO-MOTION): 서 있다가 달리기 시작할 때 Run_Start 9프레임(0.15초), 달리다 멈출 때 Run_Stop 16프레임(0.27초). 주인공만(해당 동작이 있는 모델)
        if (pose == Pose.Idle || pose == Pose.Walk)
        {
            if (moving && !wasMoving && heroInput.ContainsKey(Pose.RunStart)) startT = 0.15f;
            if (!moving && wasMoving && heroInput.ContainsKey(Pose.RunStop) && runTime > 0.3f) stopT = 0.27f;
            runTime = moving ? runTime + dt : 0f;
        }
        else { startT = 0f; stopT = 0f; runTime = 0f; }
        wasMoving = moving;
        if (startT > 0f) { startT -= dt; if (!moving) startT = 0f; else want = Pose.RunStart; }
        else if (stopT > 0f) { stopT -= dt; if (moving) stopT = 0f; else want = Pose.RunStop; }
        // 무릎 꿇음(Kneel)이 끝나면 이어서 KneelHold 를 반복한다(아트: 자세가 이어지게 만들어 크로스페이드 불필요). 처결 입력이 오면 자세가 바뀌어 풀린다
        if (want != Pose.Kneel) kneelHold = false;
        else if (!kneelHold && heroInput.ContainsKey(Pose.KneelHold) && heroInput.ContainsKey(Pose.Kneel) && heroT >= heroPlayables[heroInput[Pose.Kneel]].GetAnimationClip().length) kneelHold = true;
        if (kneelHold) want = Pose.KneelHold;
        if (want == Pose.Attack) want = atkPose;   // 콤보 2·3타는 전용 동작
        if (want == Pose.Walk && !moving && pose == Pose.Walk) want = Pose.Idle;
        int idx; if (!heroInput.TryGetValue(want, out idx)) idx = 0;
        if (idx != heroCur) { heroCur = idx; heroT = 0f; heroSpeed = 1f; }   // 새 동작은 처음부터
        // 달리기(Run)는 5.5 m/s 에서 1.0배로 재생하면 발이 안 미끄러진다(아트 HERO-MOTION). 다른 속도면 속도 비율만큼 빠르거나 느리게
        heroT += dt * (want == Pose.Walk ? Mathf.Clamp(speed / Mathf.Max(0.1f, Balance.PLAYER_MOVE_SPEED), 0.4f, 1.5f) : 1f);
        // 가중치를 부드럽게 옮긴다 (0.12초 안팎 크로스페이드)
        for (int i = 0; i < mixer.GetInputCount(); i++)
        {
            float w = mixer.GetInputWeight(i), target = i == idx ? 1f : 0f;
            mixer.SetInputWeight(i, Mathf.MoveTowards(w, target, dt / 0.12f));
            var pl = heroPlayables[i];
            if (!pl.IsValid()) continue;
            float len = pl.GetAnimationClip().length;
            // 반복 동작(서기·걷기·무릎 꿇음 자세)은 돌고, 한 번짜리(공격·맞음·천도)는 처음부터 한 번
            bool loop = false;
            foreach (var kv in heroInput) if (kv.Value == i && heroRow.loop != null && System.Array.IndexOf(heroRow.loop, kv.Key.ToString()) >= 0) loop = true;
            if (i == idx) pl.SetTime(loop ? heroT % Mathf.Max(0.01f, len) : Mathf.Min(heroT * heroSpeed, len - 0.001f));
        }
        graph.Evaluate(0f);
        // 피하기·무릎 꿇음 때 몸 높이(미끄러짐 방지용 보정은 하지 않는다 — 대역이라 단순하게)
    }

    /// <summary>
    /// 공격을 새로 시작했다(1타·2타·3타 모두). 이름이 같아 자세가 안 바뀌면 동작이 다시 시작되지 않던 문제를 막고,
    /// 모델 동작의 '때리는 순간'(대략 클립의 45%)이 판정 시각(선딜 + 휘두름의 가운데)에 오도록 재생 속도를 맞춘다.
    /// 왜? 판정과 몸 동작이 따로 놀면 "사슬만 혼자 도는" 느낌이 난다(PC 영상 의견).
    /// </summary>
    Pose oneShot; float oneShotT;   // 파혼·무기 바꿈 같은 한 번짜리 동작이 도는 동안은 그림 이름이 자세를 덮어쓰지 않는다

    /// <summary>한 번짜리 몸 동작(파혼·무기 바꿔 들기). 클립 길이만큼 자세를 붙든다. 주인공 3D 모델이 아니면 무시</summary>
    /// <summary>한 번짜리 동작의 길이(초). 모델에 그 동작이 없으면 0</summary>
    public float ClipLength(Pose p)
    {
        int idx; if (hero == null || heroPlayables == null || !heroInput.TryGetValue(p, out idx) || !heroPlayables[idx].IsValid()) return 0f;
        return heroPlayables[idx].GetAnimationClip().length;
    }

    public void PlayOneShot(Pose p)
    {
        int idx; if (hero == null || heroPlayables == null || !heroInput.TryGetValue(p, out idx) || !heroPlayables[idx].IsValid()) return;
        oneShot = p; pose = p; poseT = 0f; heroT = 0f; heroSpeed = 1f;
        oneShotT = heroPlayables[idx].GetAnimationClip().length;
    }

    public void PlayAttack(float windup, float swing, int step = 1)
    {
        oneShotT = 0f;
        pose = Pose.Attack; poseT = 0f; heroT = 0f;
        atkPose = step >= 3 ? Pose.Attack3 : step == 2 ? Pose.Attack2 : Pose.Attack;
        int idx; if (!heroInput.TryGetValue(atkPose, out idx) || heroPlayables == null || !heroPlayables[idx].IsValid()) { heroSpeed = 1f; return; }
        float len = heroPlayables[idx].GetAnimationClip().length;
        heroSpeed = Mathf.Clamp(0.45f * len / Mathf.Max(0.05f, windup + swing * 0.5f), 0.5f, 6f);
    }

    // ---- 손에 든 무기(주인공 모델의 Hand.R 뼈에 붙인다). 아트 약속: 원점=쥐는 곳, 길이 방향 glTF +Y, 뼈 기준 X축 +90° 로 눕혀 앞을 향하게
    WeaponId wantWeapon = WeaponId.Chain; GameObject weaponGo; WeaponId shownWeapon = (WeaponId)(-1);

    static float SocketRotX(WeaponId w) { switch (w) { case WeaponId.Mace: return 40f; case WeaponId.Bell: return 20f; case WeaponId.Trident: return 30f; case WeaponId.Brush: return 55f; default: return 90f; } }

    static string WeaponFile(WeaponId w)
    {
        switch (w) { case WeaponId.Mace: return "weapon_bangmang"; case WeaponId.Bell: return "weapon_yoryeong"; case WeaponId.Trident: return "weapon_samjichang"; case WeaponId.Brush: return "weapon_myeongbu"; default: return "weapon_chain"; }
    }

    /// <summary>든 무기를 알린다. 주인공 3D 모델이 아닐 땐 아무 일도 없다(도형 대역은 무기 그림이 없다)</summary>
    public void SetWeapon(WeaponId w) { wantWeapon = w; ApplyWeapon(); }

    void ApplyWeapon()
    {
        if (hero == null || key != "dongi" || shownWeapon == wantWeapon) return;
        Transform hand = null;
        foreach (var t in hero.GetComponentsInChildren<Transform>()) if (t.name == "Hand.R") { hand = t; break; }
        if (hand == null) return;   // 뼈 이름이 다르면 붙이지 않는다(맨손)
        if (weaponGo != null) Destroy(weaponGo);
        shownWeapon = wantWeapon;
        var prefab = Resources.Load<GameObject>("Models/Weapon/" + WeaponFile(wantWeapon));
        if (prefab == null) return;
        weaponGo = Instantiate(prefab, hand);
        weaponGo.transform.localPosition = Vector3.zero;
        weaponGo.transform.localRotation = Quaternion.Euler(SocketRotX(wantWeapon), 0f, 0f);   // 무기마다 쥐는 각도가 다르다(아트 매니페스트 socket_rotate_deg_x)
        RetargetWeaponClips();
        weaponGo.transform.localScale = Vector3.one / Mathf.Max(0.01f, heroRow != null ? heroRow.scale : 1f);   // 몸 크기 배율이 무기까지 줄이지 않게
        foreach (var r in weaponGo.GetComponentsInChildren<Renderer>())
        {
            var src = r.sharedMaterials; var dst = new Material[src.Length];
            for (int i = 0; i < src.Length; i++) dst[i] = U.Matte(Props3D.MatColor(src[i]));
            r.sharedMaterials = dst; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
        }
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
        var s = SpecBase(name);
        foreach (var suf in new[] { "_yeoksa", "_bungjae", "_soegol" })
            if (name.Contains(suf) && ModelCatalog.Actor(s.key + suf) != null) { s.key += suf; break; }   // 변형 모델 줄이 있을 때만(없으면 기본 모양)
        return s;
    }

    /// <summary>그림 이름("boss/boss_b05_daedol2_attack")에서 모델 표의 키를 뽑는다. 동작 꼬리표를 뗀 이름이 표에 있어야 한다</summary>
    static string BossModelKey(string name)
    {
        int i = name.IndexOf("boss_b"); if (i < 0) return null;
        string b = name.Substring(i);
        foreach (var suf in new[] { "_attack", "_kneel", "_idle" }) if (b.EndsWith(suf)) { b = b.Substring(0, b.Length - suf.Length); break; }
        return ModelCatalog.Actor(b) != null ? b : null;
    }

    static Spec SpecBase(string name)
    {
        var s = new Spec { legs = true };
        if (name.Contains("chasa"))      // 동이 대역: 검은 도포, 붉은 띠, 갓
        { s.key = "dongi"; s.height = 1.8f; s.body = new Color(0.10f, 0.11f, 0.17f); s.accent = new Color(0.62f, 0.12f, 0.12f); s.hat = true; s.glow = 0f; }
        else if (name.Contains("boss_b02"))  // 월화: 오방색 쾌자의 늙은 무당(3D 모델이 없을 때의 도형 대역)
        { s.key = "boss_b02"; s.height = 2.4f; s.body = new Color(0.72f, 0.25f, 0.38f); s.accent = new Color(0.95f, 0.8f, 0.4f); s.legs = false; s.glow = 0.4f; }
        else if (name.Contains("boss_b03"))  // 서 의원: 약장을 진 마른 의원
        { s.key = "boss_b03"; s.height = 2.2f; s.body = new Color(0.45f, 0.33f, 0.20f); s.accent = new Color(0.4f, 0.9f, 0.85f); s.legs = false; s.glow = 0.3f; }
        else if (name.Contains("boss_b") && BossModelKey(name) != null)   // 2·3막 보스·흑월: 모델 표에 줄이 있는 이름이면 그 모델(없으면 아래 도형)
        { s.key = BossModelKey(name); s.height = 2.2f; s.body = new Color(0.30f, 0.25f, 0.35f); s.accent = new Color(0.9f, 0.3f, 0.3f); s.legs = false; s.glow = 0.4f; }
        else if (name.Contains("boss"))  // 나루 영감: 크고 보랏빛, 뿔 없이 긴 도포
        { s.key = "boss"; s.height = 3.2f; s.body = new Color(0.40f, 0.30f, 0.60f); s.accent = new Color(0.8f, 0.7f, 1f); s.legs = false; s.glow = 0.5f; }
        else if (name.Contains("soul_elite"))   // 거센 혼(첫 강적): 모델이 이미 1.3배(코드 배율 1.0). 키 = elite_<등급>
        {
            string gr = name.Contains("_lump") ? "lump" : name.Contains("_old") ? "old" : name.Contains("_fresh") ? "fresh" : "day";
            s.key = "elite_" + gr; s.height = 1.8f; s.legs = false; s.glow = 0.5f; s.body = new Color(0.62f, 0.12f, 0.12f); s.accent = new Color(0.95f, 0.8f, 0.4f);
        }
        else if (name.Contains("soul_wail") || name.Contains("soul_mote") || name.Contains("soul_buried"))   // 필드 혼 3유형: 키 = <유형>_<등급> (모델은 models.json, 없으면 이 도형 대역)
        {
            string ty = name.Contains("soul_wail") ? "wail" : name.Contains("soul_mote") ? "mote" : "buried";
            string gr = name.Contains("_lump") ? "lump" : name.Contains("_old") ? "old" : name.Contains("_day") ? "day" : "fresh";
            s.key = ty + "_" + gr; s.height = ty == "mote" ? 0.5f : ty == "buried" ? 1.6f : 1.8f; s.legs = false; s.glow = 0.5f;
            s.body = gr == "lump" ? new Color(0.30f, 0.14f, 0.30f) : gr == "old" ? new Color(0.43f, 0.33f, 0.27f) : gr == "day" ? new Color(0.80f, 0.70f, 0.35f) : new Color(0.65f, 0.82f, 1f);
            s.accent = ty == "wail" ? new Color(0.69f, 0.31f, 0.82f) : new Color(0.9f, 0.97f, 1f);
        }
        else if (name.Contains("lump"))  // 덩어리: 뭉친 한 덩이
        { s.key = "lump"; s.height = 1.5f; s.body = new Color(0.30f, 0.14f, 0.16f); s.accent = new Color(0.8f, 0.25f, 0.2f); s.blob = true; s.legs = false; s.glow = 0.3f; }
        else if (name.Contains("fierce")) // 사나운 적: 붉고 뿔 달림
        { s.key = "fierce"; s.height = 2.0f; s.body = new Color(0.65f, 0.12f, 0.12f); s.accent = new Color(1f, 0.55f, 0.3f); s.horns = true; s.legs = false; s.glow = 0.6f; }
        else if (name.Contains("soul_old"))   // 오래된 혼: 잿빛 보라, 구부정, 작다
        { s.key = "old"; s.height = 1.5f; s.body = new Color(0.43f, 0.33f, 0.27f); s.accent = new Color(0.7f, 0.65f, 0.8f); s.legs = false; s.glow = 0.35f; }
        else if (name.Contains("soul_day"))   // 해 넘긴 혼: 누런빛, 보통
        { s.key = "year"; s.height = 1.75f; s.body = new Color(0.80f, 0.70f, 0.35f); s.accent = new Color(1f, 0.92f, 0.6f); s.legs = false; s.glow = 0.5f; }
        else                                   // 갓 죽은 혼: 맑은 청백, 크다
        { s.key = "fresh"; s.height = 1.95f; s.body = new Color(0.65f, 0.82f, 1f); s.accent = new Color(0.9f, 0.97f, 1f); s.legs = false; s.glow = 0.7f; }
        return s;
    }

    static Pose PoseFor(string name)
    {
        if (name.Contains("judge")) return Pose.Judge;
        if (name.Contains("kneel")) return Pose.Kneel;
        if (name.Contains("dodge")) return Pose.Dodge;
        if (name.Contains("cast")) return Pose.Cast;
        if (name.Contains("hit")) return Pose.Hit;
        if (name.Contains("strike")) return Pose.Attack2;   // 묻힌 혼: 솟아서 붙잡는 동작(Attack 클립)
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
        if (oneShotT > 0f) { oneShotT -= Time.deltaTime; if (oneShotT <= 0f) { pose = Pose.Idle; poseT = 0f; } }   // 한 번짜리 동작 중엔 그림 이름을 따르지 않는다
        else if (p != pose) { pose = p; poseT = 0f; }
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
        if (TryBuildHero(sp.key)) { modelRoot.transform.localRotation = Quaternion.Euler(0, yaw, 0); shownWeapon = (WeaponId)(-1); ApplyWeapon(); return; }   // 슬롯에 진짜 모델이 있으면 그걸 쓴다
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
    /// <summary>낮의 차사는 산 사람에게 보이지 않는다 → 낮엔 주인공 그림자를 끈다(글 없이 전해지는 연출). JudgeSystem 이 매 프레임 정한다</summary>
    public static bool HeroShadowOn = true;
    bool shadowApplied = true;

    void LateUpdate()
    {
        if (modelRoot == null) return;
        if (hero != null && key == "dongi" && shadowApplied != HeroShadowOn)
        {
            shadowApplied = HeroShadowOn;
            var mode = HeroShadowOn ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.Off;
            foreach (var r in hero.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = mode;
            if (weaponGo != null) foreach (var r in weaponGo.GetComponentsInChildren<Renderer>()) r.shadowCastingMode = mode;
        }
        float dt = Time.deltaTime;
        poseT += dt;
        // 이동 속도 = 위치 변화 (걷기 판정). 슬로모·히트스톱 중엔 dt 가 달라 값이 흔들릴 수 있어 부드럽게
        var p = transform.parent != null ? transform.parent.position : transform.position;
        float sp = dt > 0f ? new Vector2(p.x - lastPos.x, p.z - lastPos.z).magnitude / dt : 0f; lastPos = p;
        speed = Mathf.Lerp(speed, sp, 0.3f);
        // 방향: 목표 각도로 빠르게 돈다(순간 회전은 부자연스럽다)
        // 회전은 최대 속도(MOVE_TURN_RADPS)로 제한해 순간 회전처럼 보이지 않게 하고, 걸을 때 몸을 앞으로 기울이며 급하게 틀 때 안쪽으로 살짝 눕힌다
        var curYaw = modelRoot.transform.localEulerAngles.y;
        float newYaw = Mathf.MoveTowardsAngle(curYaw, yaw, Balance.MOVE_TURN_RADPS * Mathf.Rad2Deg * dt);
        float yawRate = dt > 0f ? Mathf.DeltaAngle(curYaw, newYaw) / dt : 0f;                              // 도/초(왼쪽 +)
        bool walkingPose = pose == Pose.Idle || pose == Pose.Walk;
        float leanT = walkingPose ? Mathf.Clamp01(speed / Mathf.Max(0.1f, Config.PLAYER_MOVE_SPEED)) * Balance.MOVE_LEAN_DEG : 0f;
        float bankT = walkingPose ? -Mathf.Clamp(yawRate / (Balance.MOVE_TURN_RADPS * Mathf.Rad2Deg), -1f, 1f) * Balance.MOVE_BANK_DEG * Mathf.Clamp01(speed / 2f) : 0f;
        leanNow = Mathf.Lerp(leanNow, leanT, 1f - Mathf.Exp(-Balance.MOVE_LEAN_SMOOTH * dt));
        bankNow = Mathf.Lerp(bankNow, bankT, 1f - Mathf.Exp(-Balance.MOVE_LEAN_SMOOTH * dt));
        modelRoot.transform.localRotation = Quaternion.Euler(leanNow, newYaw, bankNow);

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
