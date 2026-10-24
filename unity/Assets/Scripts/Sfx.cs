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
    bool muted;
    const string PREF = "chasa_muted";

    public static Sfx Create(JudgeSystem j)
    {
        var go = new GameObject("Sfx");
        var s = go.AddComponent<Sfx>(); s.judge = j; return s;
    }

    void Awake() { I = this; }

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
        var amb = Clip("amb.field"); if (amb != null) { ambLoop.clip = amb; ambLoop.volume = 1f; }
        ApplyMute();
    }

    AudioClip Clip(string id)
    {
        AudioClip c;
        if (clips.TryGetValue(id, out c)) return c;
        var data = SfxSynth.Render(id);
        if (data == null) { clips[id] = null; return null; }
        c = AudioClip.Create(id, data.Length, 1, SfxSynth.Rate, false);
        c.SetData(data, 0);
        clips[id] = c; return c;
    }

    /// <summary>효과음 한 번 재생. 아직 준비 전이거나 꺼져 있으면 조용히 무시</summary>
    public static void Play(string id) { if (I != null) I.PlayInternal(id); }

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
        v.volume = hit ? Mathf.Pow(10f, Random.Range(-1.5f, 1.5f) / 20f) : 1f;
        v.bypassListenerEffects = id == "sfx.enemy.telegraph";   // 예고음은 먹먹 필터를 건너뛴다
        v.Play();
        list.Add(v);
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.M)) ToggleMute();
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
                castLoop.volume = Mathf.Min(1f, castLoop.volume + Time.unscaledDeltaTime * 6f);
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
        else if (ambLoop.clip != null && !ambLoop.isPlaying) ambLoop.Play();
    }

    /// <summary>화면 왼쪽 위의 작은 소리 켜기/끄기 버튼 (폰에서도 눌러야 하니까)</summary>
    void OnGUI()
    {
        if (judge != null && (judge.InDay || CharacterPanel.Open)) return;
        Ko.Apply();
        GUI.depth = -50;
        var st = new GUIStyle(GUI.skin.button) { fontSize = Ko.TouchUI ? 22 : 14 };
        if (GUI.Button(new Rect(Screen.width - (Ko.TouchUI ? 104 : 78), 8, Ko.TouchUI ? 96 : 70, Ko.TouchUI ? 48 : 26), muted ? "소리 끔" : "소리 켬", st)) ToggleMute();
    }
}
