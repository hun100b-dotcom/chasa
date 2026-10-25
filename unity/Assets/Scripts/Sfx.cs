// =============================================================================
// Sfx.cs — 효과음 재생기. 소리 만들기는 Core/SfxSynth, 여기서는 "언제·어떻게 틀지"만 맡는다.
//
// 규칙(기획 sound-direction.md):
//   1) 같은 소리 동시 최대 4개 (넘으면 가장 오래된 것을 끊는다) — 다수전에서 귀가 안 터지게
//   2) 타격음은 매번 음높이 ±6%, 크기 ±1.5dB 무작위 — 같은 소리 반복 피로 줄이기
//   3) 천도 캐스팅 중엔 세상이 먹먹해진다: 전체 소리에 저역 통과 필터(높은 소리 깎기) 20kHz→1.2kHz.
//      단, 적 예고음은 필터를 건너뛴다 (위험은 들려야 하니까)
//   4) 소리 켜기/끄기 (M 키 또는 화면 왼쪽 위 버튼). 선택은 저장된다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class Sfx : MonoBehaviour
{
    public static Sfx I;
    public JudgeSystem judge;

    const int VOICES = 10;                        // 동시에 낼 수 있는 소리 칸 수
    readonly Dictionary<string, AudioClip> clips = new Dictionary<string, AudioClip>();
    readonly Dictionary<string, List<AudioSource>> playing = new Dictionary<string, List<AudioSource>>();
    AudioSource[] voices;
    AudioSource castLoop, ambLoop;
    AudioLowPassFilter master;                    // 전체 먹먹함 필터(카메라의 귀에 붙인다)
    float cutoff = 20000f;
    bool muted, ambOff;                           // ambOff: BGM 이 들어오면 임시 들판 소리(amb.field)는 끈다
    const string PREF = "chasa_muted";

    public static Sfx Create(JudgeSystem j)
    {
        var go = new GameObject("Sfx");
        var s = go.AddComponent<Sfx>(); s.judge = j; return s;
    }

    void Awake() { I = this; }

    public static bool Muted { get { return I != null && I.muted; } }
    /// <summary>진짜 BGM 이 켜졌으니 임시 배경음(amb.field + 드론)을 끈다</summary>
    public static void StopAmbient() { if (I != null) { I.ambOff = true; if (I.ambLoop != null) I.ambLoop.Stop(); } }

    void Start()
    {
        try { muted = PlayerPrefs.GetInt(PREF, 0) == 1; } catch { }   // 저장소가 막혀 있어도 게임은 돌아가야 한다
        // 이 게임엔 귀(AudioListener)가 아직 없다 → 카메라에 달아 준다. 필터도 같은 곳에 둔다.
        var cam = Camera.main;
        if (cam != null)
        {
            if (cam.GetComponent<AudioListener>() == null) cam.gameObject.AddComponent<AudioListener>();
            master = cam.gameObject.AddComponent<AudioLowPassFilter>();
            master.cutoffFrequency = 20000f;
        }
        voices = new AudioSource[VOICES];
        for (int i = 0; i < VOICES; i++) { voices[i] = gameObject.AddComponent<AudioSource>(); voices[i].playOnAwake = false; }
        castLoop = gameObject.AddComponent<AudioSource>(); castLoop.loop = true; castLoop.playOnAwake = false;
        ambLoop = gameObject.AddComponent<AudioSource>(); ambLoop.loop = true; ambLoop.playOnAwake = false;
        // 소리 만들기는 시작할 때 한 번만 (몇십 ms). 이후엔 재생만 한다
        foreach (var id in SfxSynth.Ids) Clip(id);
        var amb = Clip("amb.field"); if (amb != null) { ambLoop.clip = amb; ambLoop.volume = SaveStore.Settings.Sfx; }
        ApplyMute();
        AudioListener.volume = SaveStore.Settings.Master;   // 설정의 전체 소리 크기
    }

    AudioClip Clip(string id)
    {
        AudioClip c;
        if (clips.TryGetValue(id, out c)) return c;
        // 사운드팀이 만든 WAV 파일이 있으면 그것을 먼저 쓴다(Resources/Audio/Sfx/<id의 . 을 _ 로>). 없을 때만 코드로 합성한다.
        // 반복 소리(cast·amb)는 파일 자체에 이음매 처리가 돼 있고, 음량도 맞춰져 있어 재생 볼륨은 1.0 그대로
        c = Resources.Load<AudioClip>("Audio/Sfx/" + id.Replace('.', '_'));
        if (c != null) { clips[id] = c; return c; }
        var data = SfxSynth.Render(id);
        if (data == null) { clips[id] = null; return null; }
        c = AudioClip.Create(id, data.Length, 1, SfxSynth.Rate, false);
        c.SetData(data, 0);
        clips[id] = c; return c;
    }

    /// <summary>구역 환경음용 반복 음원 하나를 만든다(소리 0으로 시작, 호출한 쪽이 서서히 키운다). 소리 파일이 없으면 null 대신 빈 음원</summary>
    public static AudioSource MakeLoop(string id)
    {
        var host = I != null ? I.gameObject : new GameObject("SfxLoop");
        var s = host.AddComponent<AudioSource>(); s.loop = true; s.playOnAwake = false; s.volume = 0f;
        var c = I != null ? I.Clip(id) : null;
        if (c != null) { s.clip = c; s.Play(); }
        return s;
    }

    /// <summary>효과음 한 번 재생. 아직 준비 전이거나 꺼져 있으면 조용히 무시</summary>
    /// <summary>무기 이름표(chain/mace/bell/trident/brush) — 소리 id 뒤에 붙인다</summary>
    public static string WeaponTag(WeaponId w) { return w.ToString().ToLowerInvariant(); }
    /// <summary>무기별 타격음 id. 철삭은 기존 소리를 그대로 쓴다(사운드팀 표)</summary>
    public static string HitKey(WeaponId w, bool heavy)
    {
        if (w == WeaponId.Chain) return heavy ? "sfx.hit.heavy" : "sfx.hit.chain";
        return "sfx.hit." + WeaponTag(w) + (heavy ? ".heavy" : "");
    }
    public static void Play(string id) { if (I != null) I.PlayInternal(id); }

    AudioSource wxLoop; Weather wxNow = Weather.Clear; string wxId;
    /// <summary>날씨 소리: 비=amb.weather.rain, 흐림=바람, 안개·역병 안개=fog_night. 맑음은 끈다. 바뀌면 서서히(0.5초) 갈아 끼운다</summary>
    /// <summary>더킹(ducking, 중요한 소리 때 배경을 잠깐 줄이기): 1=그대로, 0.5=절반. 컷신·천도 시전·명부 열림 때 BGM·환경음에 곱한다. 예고음·타격음은 줄이지 않는다</summary>
    public static float Duck = 1f;
    public static void TickDuck(bool on, float dt) { Duck = Mathf.MoveTowards(Duck, on ? 0.5f : 1f, dt / (on ? 0.4f : 1.2f) * 0.5f); }   // 줄일 땐 0.4초, 돌아올 땐 1.2초(갑자기 커지지 않게)
    public static bool NightNow;   // 지금이 밤인가(JudgeSystem 이 시계를 보고 매 프레임 알려 준다 — 날씨 소리 고르기용)
    public static void SetWeatherAmbient(Weather w) { if (I != null) I.SetWeatherInternal(w); }

    void SetWeatherInternal(Weather w)
    {
        if (wxLoop == null) { wxLoop = gameObject.AddComponent<AudioSource>(); wxLoop.loop = true; wxLoop.playOnAwake = false; wxLoop.volume = 0f; }
        // 날씨 소리는 낮·밤과 안개·역병을 구분한다(사운드팀 표). 큰비(1호 보스 날)는 보스 날 신호가 생기면 추가
        string id = w == Weather.Rain ? "amb.weather.rain"
            : w == Weather.Cloudy ? (NightNow ? "amb.weather.cloudy.night" : "amb.weather.wind")
            : w == Weather.Fog ? (NightNow ? "amb.weather.fog_night" : "amb.weather.fog")
            : w == Weather.Plague ? "amb.weather.plague" : null;
        float target = id == null || muted ? 0f : 0.6f * SaveStore.Settings.Sfx * Duck;   // 믹스 기준표: 날씨 0.6
        if (id != null && id != wxId) { var c = Clip(id); if (c != null) { wxLoop.clip = c; wxId = id; if (!wxLoop.isPlaying) wxLoop.Play(); } }
        wxLoop.volume = Mathf.MoveTowards(wxLoop.volume, target, Time.unscaledDeltaTime * 2f);
        if (id == null && wxLoop.volume <= 0f && wxLoop.isPlaying) { wxLoop.Stop(); wxId = null; }
    }

    static readonly string[] StepMat = { "dirt", "grass", "gravel", "paddy", "leaves" };   // 땅 층 순서(흙·풀·자갈·논·낙엽)와 같다
    int lastStepN;

    /// <summary>발소리 한 번. 가장 많이 밟은 땅 재질(젖은 땅·물이면 water)의 4개 중 직전과 다른 하나를 고른다. 재질 차이·크기는 사운드팀 파일에 맞춰져 있다</summary>
    public static void PlayStep(float[] w, bool wet) { if (I != null) I.PlayStepInternal(w, wet); }

    void PlayStepInternal(float[] w, bool wet)
    {
        if (muted || voices == null) return;
        int top = 1; float best = -1f;   // 비율을 못 읽으면 풀
        for (int i = 0; i < StepMat.Length && i < w.Length; i++) if (w[i] > best) { best = w[i]; top = i; }
        string mat = wet ? "water" : StepMat[top];
        int n; do { n = Random.Range(1, 5); } while (n == lastStepN);   // 같은 소리가 연달아 나오면 기계 같다
        lastStepN = n;
        var c = Clip("sfx.step." + mat + "." + n); if (c == null) return;
        AudioSource s = null;
        foreach (var x in voices) if (!x.isPlaying) { s = x; break; }
        if (s == null) return;   // 발소리는 빈 칸이 없으면 그냥 건너뛴다(다른 소리를 뺏지 않는다)
        s.clip = c; s.pitch = 1f + Random.Range(-0.04f, 0.04f); s.volume = 0.45f * SaveStore.Settings.Sfx; s.bypassListenerEffects = false;
        s.Play();
    }

    void PlayInternal(string id)
    {
        if (muted || voices == null) return;
        var c = Clip(id); if (c == null) return;
        // 같은 id 동시 4개 제한
        List<AudioSource> list;
        if (!playing.TryGetValue(id, out list)) playing[id] = list = new List<AudioSource>();
        list.RemoveAll(s => s == null || !s.isPlaying);
        if (list.Count >= 4) { list[0].Stop(); list.RemoveAt(0); }
        // 쉬는 칸 찾기. 없으면 가장 오래 울린 칸을 뺏는다
        AudioSource v = null;
        foreach (var s in voices) if (!s.isPlaying) { v = s; break; }
        if (v == null) { v = voices[0]; foreach (var s in voices) if (s.time > v.time) v = s; }
        v.clip = c;
        bool hit = id.StartsWith("sfx.hit") || id == "sfx.player.hurt";
        v.pitch = hit ? 1f + Random.Range(-0.06f, 0.06f) : 1f;
        v.volume = (hit ? Mathf.Pow(10f, Random.Range(-1.5f, 1.5f) / 20f) : 1f) * SaveStore.Settings.Sfx;   // 설정의 효과음 크기
        v.bypassListenerEffects = id == "sfx.enemy.telegraph";   // 예고음은 먹먹 필터를 건너뛴다
        v.Play();
        list.Add(v);
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.N)) ToggleMute();   // 소리 끄기는 N (M 은 지도)
        if (judge == null) return;
        // 천도 캐스팅: 먹먹 필터 + 낮은 드론. CastZoom(0~1)이 올라갈수록 소리가 깎인다
        float cast = judge.CastZoom;
        float target = Mathf.Lerp(20000f, 1200f, cast);
        cutoff = Mathf.Lerp(cutoff, target, 1f - Mathf.Exp(-14f * Time.unscaledDeltaTime));   // 0.25초 안팎으로 따라간다
        if (master != null) master.cutoffFrequency = Mathf.Clamp(cutoff, 1000f, 22000f);
        if (castLoop != null)
        {
            if (judge.Casting && !muted)
            {
                if (castLoop.clip == null) castLoop.clip = Clip("sfx.tendo.cast");
                if (!castLoop.isPlaying) castLoop.Play();
                castLoop.pitch = 1f + 0.12f * cast;   // 점점 올라간다
                castLoop.volume = Mathf.Min(SaveStore.Settings.Sfx, castLoop.volume + Time.unscaledDeltaTime * 6f);
            }
            else if (castLoop.isPlaying)
            {
                castLoop.volume -= Time.unscaledDeltaTime * 6f;   // 0.17초에 걸쳐 사라진다
                if (castLoop.volume <= 0f) { castLoop.Stop(); castLoop.volume = 0f; }
            }
        }
    }

    void ToggleMute()
    {
        muted = !muted;
        try { PlayerPrefs.SetInt(PREF, muted ? 1 : 0); PlayerPrefs.Save(); } catch { }
        ApplyMute();
    }

    void ApplyMute()
    {
        if (muted) { foreach (var v in voices) v.Stop(); castLoop.Stop(); ambLoop.Stop(); }
        else if (!ambOff && ambLoop.clip != null && !ambLoop.isPlaying) ambLoop.Play();
    }

    /// <summary>화면 왼쪽 위의 작은 소리 켜기/끄기 버튼 (폰에서도 눌러야 하니까)</summary>
    void OnGUI()
    {
        if (judge != null && (judge.InDay || CharacterPanel.Open)) return;
        Ko.Apply();
        GUI.depth = -50;
        var st = new GUIStyle(GUI.skin.button) { fontSize = Ko.TouchUI ? 22 : 14 };
        if (GUI.Button(new Rect(Mathf.Min(Screen.width, MiniMap.LeftPx > 0f ? MiniMap.LeftPx : Screen.width) - (Ko.TouchUI ? 104 : 78), 8, Ko.TouchUI ? 96 : 70, Ko.TouchUI ? 48 : 26), muted ? "소리 끔" : "소리 켬", st)) ToggleMute();
    }
}
