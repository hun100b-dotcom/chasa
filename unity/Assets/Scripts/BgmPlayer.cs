// =============================================================================
// BgmPlayer.cs — BGM 재생기. 어느 층을 틀지는 Core/BgmDirector 가 정하고, 여기서는 곡을 불러와
// 두 개의 재생기(AudioSource)로 교차(크로스페이드)해 틀기만 한다. 층 배정표는 data/bgm.json.
//   - 곡은 Resources/Audio/BGM/<id>.ogg. 파일 음량을 미리 맞춰 뒀으니 볼륨은 1.0 기준
//   - 낮 a·b 는 번갈아(한 곡이 끝나기 2초 전 다른 곡으로 교차)
//   - 필드(흐르는 하루)에서만 켠다. 옛 '하룻밤 한 판'은 기존 소리 그대로
//   - 소리 끔(M 키)을 따른다
// =============================================================================
using Chasa.Core;
using UnityEngine;

public class BgmPlayer : MonoBehaviour
{
    public JudgeSystem judge;
    readonly BgmDirector dir = new BgmDirector();
    AudioSource cur, prev;               // 지금 곡 / 사라져 가는 곡
    float fadeLen = 2f, fadeT = 2f;      // 교차 길이 / 흐른 시간
    string curId;                        // 지금 트는 곡 이름
    int lastKneel;
    bool dayB;                           // 다음 낮 곡이 b 인가
    bool loadedAny;
    AudioClip dayA, dayBclip, night, combat, finish;

    // ---- 컷신 소리 대본의 음악 명령(CutscenePlayer 가 보낸다) ----
    // duck: 음악을 to 배율로 줄임 / silence: 0 / resume: 원래대로(강제 층·곡도 해제) / layer: 전투·처결 층으로 강제 / play: 지정 곡(없으면 fallback)
    static float mixTarget = 1f, mixRate = 1f, mixNow = 1f;
    static string forceLayer, playId, playFallback;
    public static void Command(string op, string id, float to, float fade, string fallback)
    {
        mixRate = 1f / Mathf.Max(0.05f, fade);
        switch (op)
        {
            case "duck": mixTarget = Mathf.Clamp01(to); break;
            case "silence": mixTarget = 0f; break;
            case "resume": mixTarget = 1f; forceLayer = null; playId = null; break;
            case "layer": forceLayer = id; mixTarget = 1f; break;
            case "play": playId = id; playFallback = fallback; mixTarget = 1f; break;
        }
    }

    public static BgmPlayer Create(JudgeSystem j)
    {
        var go = new GameObject("BgmPlayer");
        var b = go.AddComponent<BgmPlayer>(); b.judge = j; return b;
    }

    // 진짜 곡(BGM/)을 먼저 찾고, 없으면 임시 대역(BGM/Temp/)을 쓴다 → 오너 곡을 같은 이름으로 넣기만 하면 자동으로 바뀐다
    static AudioClip Load(string id) { return Resources.Load<AudioClip>("Audio/BGM/" + id) ?? Resources.Load<AudioClip>("Audio/BGM/Temp/" + id); }

    // ---- 지역별 곡: 지역이 바뀌면 그 지역의 다섯 곡(낮·밤·전투·처결)을 다시 불러와 4초에 걸쳐 넘긴다 ----
    string region; float regionCheck; bool regionFade;
    /// <summary>
    /// 월드 좌표 → 곡 이름 앞부분. ⑤ 갯마을(x≥768)·⑥ 도성(x&lt;0)·2막 ③ 붉은재(서쪽)·④ 쇳골(동쪽)·그 밖은 솔고개.
    /// 왜 좌표 경계? 지역 사각형을 JSON 에서 다시 읽는 것보다 단순하고, 지역 경계는 땅 사각형(FieldRules)과 같은 선이라 어긋나지 않는다.
    /// </summary>
    public static string RegionKeyAt(float x, float z)
    {
        if (x >= FieldRules.Size + 128f) return "gaetmaeul";
        if (x < 0f) return "doseong";
        if (z >= FieldRules.Size) return x < 360f ? "bulgeunjae" : "soegol";
        return "solgogae";
    }
    void LoadRegion(string r)
    {
        if (r == region) return;
        bool first = region == null; region = r;
        dayA = Load("bgm_" + r + "_day_a"); dayBclip = Load("bgm_" + r + "_day_b");   // day_b 는 없어도 된다(그러면 day_a 만 반복)
        night = Load("bgm_" + r + "_night"); combat = Load("bgm_" + r + "_combat"); finish = Load("bgm_" + r + "_finish");
        if (night == null) night = dayA;   // 밤 곡이 없으면 낮 곡으로
        loadedAny = dayA != null || night != null;
        if (!first) { curId = null; regionFade = true; }   // 다음 프레임에 새 지역 곡으로 교차(첫 불러오기는 그냥 시작)
    }

    void Start()
    {
        LoadRegion("solgogae");   // 시작은 솔고개(처결 전용 곡은 오너 Gemini 「Bells of the Crossing」 첫 종소리 8.45초)
        cur = NewSource(); prev = NewSource();
        if (loadedAny) Sfx.StopAmbient();   // 진짜 BGM 이 있으면 임시 배경음은 끈다
        if (judge != null) lastKneel = judge.KneelEvents;
    }

    AudioSource NewSource()
    {
        var s = gameObject.AddComponent<AudioSource>();
        s.playOnAwake = false; s.spatialBlend = 0f; s.volume = 0f; s.bypassListenerEffects = false;
        return s;
    }

    void Update()
    {
        if (!loadedAny || judge == null || !judge.FieldMode || judge.InDay) { Silence(); return; }
        float dt = Time.unscaledDeltaTime;   // 슬로모션 중에도 음악은 같은 속도로
        regionCheck -= dt;
        if (regionCheck <= 0f && judge.player != null) { regionCheck = 0.5f; LoadRegion(RegionKeyAt(judge.player.Pos.x, judge.player.Pos.z)); }   // 0.5초마다 지역을 본다
        Sfx.TickDuck(judge.cuts.Active || judge.Casting || CharacterPanel.Open, dt);   // 컷신·천도 시전·명부 열림 때 배경을 줄인다
        int kneeling; float near = judge.NearestEnemyDist(out kneeling);
        bool started = judge.KneelEvents != lastKneel; lastKneel = judge.KneelEvents;
        dir.Update(dt, judge.clock.Daylight, near, started, kneeling > 0 || judge.Casting);
        mixNow = Mathf.MoveTowards(mixNow, mixTarget, dt * mixRate);

        // 틀어야 할 곡 정하기
        AudioClip want = null; string wantId = null; bool loop = true;
        var layer = forceLayer == "combat" ? BgmLayer.Combat : forceLayer == "finish" ? BgmLayer.Finish : dir.Layer;   // 컷이 층을 강제하면 그것을 따른다
        switch (layer)
        {
            case BgmLayer.Combat: want = combat; wantId = "combat"; break;
            case BgmLayer.Finish: want = finish; wantId = "finish"; loop = false; break;
            case BgmLayer.Silent: break;
            default:
                if (dir.Night) { want = night; wantId = "night"; }
                else
                {
                    // 낮: 지금 낮 곡을 그대로 두고, 끝나기 2초 전이면 다른 곡으로 넘긴다
                    bool onDay = curId == "day_a" || curId == "day_b";
                    bool nearEnd = onDay && cur.clip != null && cur.clip.length - cur.time < 2f;
                    if (nearEnd && dayA != null && dayBclip != null) dayB = curId == "day_a";
                    else if (onDay) dayB = curId == "day_b";
                    want = dayB && dayBclip != null ? dayBclip : dayA; wantId = dayB && dayBclip != null ? "day_b" : "day_a";
                    if (nearEnd) fadeLen = 2f;
                }
                break;
        }
        if (playId != null)   // 컷이 지정한 곡(시즌1 끝 곡 등). 파일이 없으면 fallback(silence 면 조용히)
        {
            var pc = Load(playId);
            if (pc != null) { want = pc; wantId = "cut:" + playId; loop = playId.Contains("heukwol") || playId.Contains("bigdam"); }   // 컷이 지정한 곡은 한 번만 틀지만, 결전 곡(흑월·B-20 보스전)은 싸움이 끝날 때까지 반복
            else if (playFallback == "silence") { want = null; wantId = "cut-none"; }
        }
        if (wantId != curId && regionFade) { regionFade = false; Switch(want, wantId, loop, 4f); }   // 지역이 바뀔 때는 4초에 걸쳐 넘긴다
        else if (wantId != curId) Switch(want, wantId, loop, nearEndFade: dir.Layer == BgmLayer.Explore && (curId == "day_a" || curId == "day_b") && (wantId == "day_a" || wantId == "day_b") ? 2f : dir.Fade);

        // 교차 진행
        fadeT = Mathf.Min(fadeLen, fadeT + dt);
        float k = fadeLen <= 0.001f ? 1f : fadeT / fadeLen;
        float mute = Sfx.Muted ? 0f : SaveStore.Settings.Bgm;   // 설정의 배경음 크기(음소거면 0)
        // 믹스 기준표: 탐험 0.5 / 전투·처결 0.45 를 곱해 타격음을 덮지 않게 한다(1막 BGM 이 -16~-20 LUFS 로 큼)
        float layerMix = dir.Layer == BgmLayer.Combat || dir.Layer == BgmLayer.Finish ? 0.45f : 0.5f;
        mute *= layerMix * Sfx.Duck * mixNow;
        cur.volume = (cur.clip != null ? k : 0f) * mute;
        prev.volume = (1f - k) * mute;
        if (k >= 1f && prev.isPlaying) prev.Stop();
    }

    void Switch(AudioClip clip, string id, bool loop, float nearEndFade)
    {
        var t = prev; prev = cur; cur = t;       // 지금 곡은 사라져 가는 쪽으로, 새 곡이 지금 쪽으로
        curId = id; fadeLen = nearEndFade; fadeT = 0f;
        cur.Stop(); cur.clip = clip; cur.loop = loop;
        if (clip != null) { cur.time = 0f; cur.Play(); }   // 클립이 없을 때 time 을 건드리면 유니티가 경고를 낸다
    }

    void Silence()
    {
        if (cur != null && cur.isPlaying) { cur.Stop(); curId = null; }
        if (prev != null && prev.isPlaying) prev.Stop();
    }
}
