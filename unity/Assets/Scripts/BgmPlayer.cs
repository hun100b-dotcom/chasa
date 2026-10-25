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

    public static BgmPlayer Create(JudgeSystem j)
    {
        var go = new GameObject("BgmPlayer");
        var b = go.AddComponent<BgmPlayer>(); b.judge = j; return b;
    }

    static AudioClip Load(string id) { return Resources.Load<AudioClip>("Audio/BGM/" + id); }

    void Start()
    {
        dayA = Load("bgm_solgogae_day_a"); dayBclip = Load("bgm_solgogae_day_b");
        night = Load("bgm_solgogae_night"); combat = Load("bgm_solgogae_combat"); finish = Load("bgm_solgogae_finish");   // 처결 전용 곡(오너 Gemini 「Bells of the Crossing」 첫 종소리 8.45초)
        loadedAny = dayA != null || night != null;
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
        int kneeling; float near = judge.NearestEnemyDist(out kneeling);
        bool started = judge.KneelEvents != lastKneel; lastKneel = judge.KneelEvents;
        dir.Update(dt, judge.clock.Daylight, near, started, kneeling > 0 || judge.Casting);

        // 틀어야 할 곡 정하기
        AudioClip want = null; string wantId = null; bool loop = true;
        switch (dir.Layer)
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
        if (wantId != curId) Switch(want, wantId, loop, nearEndFade: dir.Layer == BgmLayer.Explore && (curId == "day_a" || curId == "day_b") && (wantId == "day_a" || wantId == "day_b") ? 2f : dir.Fade);

        // 교차 진행
        fadeT = Mathf.Min(fadeLen, fadeT + dt);
        float k = fadeLen <= 0.001f ? 1f : fadeT / fadeLen;
        float mute = Sfx.Muted ? 0f : 1f;
        cur.volume = (cur.clip != null ? k : 0f) * mute;
        prev.volume = (1f - k) * mute;
        if (k >= 1f && prev.isPlaying) prev.Stop();
    }

    void Switch(AudioClip clip, string id, bool loop, float nearEndFade)
    {
        var t = prev; prev = cur; cur = t;       // 지금 곡은 사라져 가는 쪽으로, 새 곡이 지금 쪽으로
        curId = id; fadeLen = nearEndFade; fadeT = 0f;
        cur.Stop(); cur.clip = clip; cur.loop = loop; cur.time = 0f;
        if (clip != null) cur.Play();
    }

    void Silence()
    {
        if (cur != null && cur.isPlaying) { cur.Stop(); curId = null; }
        if (prev != null && prev.isPlaying) prev.Stop();
    }
}
