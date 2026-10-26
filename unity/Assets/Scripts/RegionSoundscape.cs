// =============================================================================
// RegionSoundscape.cs — 2·3막 주변 소리(사운드팀 PR #44: data/act2_soundscape.json·act3_soundscape.json
// → tools/build_region_soundscape.py → Resources/Data/region_soundscape.json).
// 1막(Act1Soundscape)과 같은 세 겹에 엿듣기 자리 소리를 더했다:
//   바탕     구역 코드(act2/3_map.json 의 code)마다 [밤, 낮] 2D 반복음. 구역이 바뀌면 3초 교차. 값이 있는 때는 ZoneAmbient 의 옛 구역 소리를 끈다.
//   자리     서낭당·소품 자리의 3D 반복음(시각대 조건 when). 가까운 것만 켠다(음원 수를 아끼려고).
//   엿듣기   R2-01~15·R3-01~15: 그 자리가 열려 있고(시각대·장례·업) 가까울 때만 반복. 글이 뜨는 동안은 0.6배(글을 읽게).
//   흩뿌림   구역마다 한 번짜리 소리를 무작위 간격·좌우로. 천도 시전 중엔 멈춘다.
//   시각     갱 징(sfx.mine.gong): 새벽·저녁이 되는 순간 그 구역 안에 있으면 한 번.
// 1막과 따로 둔 까닭: 구역을 이름이 아니라 코드로 가르고, 엿듣기 자리의 열림을 NpcWorld 에 물어야 해서.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class RegionSoundscape : MonoBehaviour
{
    [System.Serializable] class Bed { public string code, night, day; }
    [System.Serializable] class Pt { public string id, when, unlock; public float x, z, min, max; }
    [System.Serializable] class Ov { public string spot, id; }
    [System.Serializable] class Spr { public string code, id, when; public float lo, hi; }
    [System.Serializable] class Prop { public string prop, id; public float min, max, gain; public int nearest; }
    [System.Serializable] class Timed { public string id; public string[] zones; }
    [System.Serializable] class FileData { public Bed[] beds; public Pt[] points; public Ov[] overhear; public Spr[] sprinkles; public Prop[] props; public Timed[] timed; }
    [System.Serializable] class MapZone { public string code; public float[] rect_m; }
    [System.Serializable] class MapFile { public MapZone[] zones; }

    class Loop { public AudioSource s; public bool want; public float gain = 1f; }
    struct W { public string id; public Vector3 pos; public float min, max, gain; }

    /// <summary>지금 이 구역에 새 바탕 소리가 있으면 true — ZoneAmbient 가 보고 옛 구역 소리를 끈다(둘이 겹쳐 시끄럽지 않게)</summary>
    public static bool BedActive;

    FileData d; MapZone[] zones = new MapZone[0];
    JudgeSystem judge; System.Func<Vector3> playerPos;
    readonly Dictionary<string, Loop> loops = new Dictionary<string, Loop>();
    readonly Dictionary<string, W> wantCache = new Dictionary<string, W>();
    readonly Dictionary<string, List<Vector2>> propPos = new Dictionary<string, List<Vector2>>();
    float scanT; int lastPhase = -1;
    const float Fade3D = 0.5f, FadeBed = 3f, OverhearRadius = 10f;

    public static RegionSoundscape Create(JudgeSystem j, System.Func<Vector3> pos)
    {
        var ta = Resources.Load<TextAsset>("Data/region_soundscape");
        if (ta == null) return null;
        var g = new GameObject("RegionSoundscape").AddComponent<RegionSoundscape>();
        g.d = JsonUtility.FromJson<FileData>(ta.text); g.judge = j; g.playerPos = pos;
        var all = new List<MapZone>();
        foreach (var nm in new[] { "Data/act2_map", "Data/act3_map" })
        {
            var t = Resources.Load<TextAsset>(nm); if (t == null) continue;
            var f = JsonUtility.FromJson<MapFile>(t.text); if (f != null && f.zones != null) all.AddRange(f.zones);
        }
        g.zones = all.ToArray();
        return g;
    }

    string CodeAt(Vector3 p)
    {
        foreach (var z in zones)
            if (z.rect_m != null && z.rect_m.Length >= 4 && p.x >= z.rect_m[0] && p.x <= z.rect_m[2] && p.z >= z.rect_m[1] && p.z <= z.rect_m[3]) return z.code;
        return "";
    }

    static bool Night { get { return Sfx.PhaseNow == 3; } }
    /// <summary>점 소리의 시각 조건: always · day(새벽~낮) · night · evening_night(저녁~밤)</summary>
    static bool WhenOk(string when)
    {
        int ph = Sfx.PhaseNow;
        switch (when) { case "day": return ph <= 1; case "night": return ph == 3; case "evening_night": return ph >= 2; default: return true; }
    }

    void Update()
    {
        if (d == null || playerPos == null || Sfx.Muted) { BedActive = false; FadeAll(); return; }
        var p = playerPos(); string code = CodeAt(p);
        foreach (var l in loops.Values) l.want = false;
        // 바탕: 지금 시각의 값이 있을 때만(없으면 ZoneAmbient 가 그대로 맡는다)
        BedActive = false;
        foreach (var b in d.beds)
        {
            if (b.code != code) continue;
            string id = Night ? b.night : b.day;
            if (string.IsNullOrEmpty(id)) continue;
            BedActive = true; Want("bed:" + id, id, false, Vector3.zero, 0f, 0f, 0.6f);
        }
        scanT -= Time.unscaledDeltaTime;
        if (scanT <= 0f) { scanT = 0.5f; Rescan(p); }
        foreach (var kv in wantCache) Want(kv.Key, kv.Value.id, true, kv.Value.pos, kv.Value.min, kv.Value.max, kv.Value.gain);
        ApplyVolumes();
        TickSprinkles(code);
        TickTimed(code);
    }

    void Rescan(Vector3 p)
    {
        wantCache.Clear();
        var pp = new Vector2(p.x, p.z);
        var placed = new List<KeyValuePair<string, Vector2>>();   // 같은 소리가 12 m 안에 두 번 켜지지 않게(우물 점과 R2-02 처럼)
        System.Func<string, Vector2, bool> dup = (id, v) => { foreach (var o in placed) if (o.Key == id && Vector2.Distance(o.Value, v) < 12f) return true; return false; };
        for (int i = 0; i < d.points.Length; i++)
        {
            var q = d.points[i];
            if (!WhenOk(q.when)) continue;
            if (!string.IsNullOrEmpty(q.unlock) && q.unlock.Contains("B-11") && (judge == null || !judge.BossTendoed(11))) continue;   // 다리 밑 서낭은 B-11 천도 뒤에야 생긴다
            var v = new Vector2(q.x, q.z);
            if (Vector2.Distance(pp, v) > q.max + 12f || dup(q.id, v)) continue;
            placed.Add(new KeyValuePair<string, Vector2>(q.id, v));
            wantCache["pt" + i] = new W { id = q.id, pos = new Vector3(q.x, 0f, q.z), min = q.min, max = q.max, gain = 1f };
        }
        // 엿듣기 자리: 열려 있고 가까울 때. 글이 뜨는 동안은 0.6배
        if (judge != null && judge.npcs != null && d.overhear != null)
            foreach (var o in d.overhear)
            {
                Vector3 sp; if (!judge.npcs.RumorOpen(o.spot, out sp)) continue;
                var v = new Vector2(sp.x, sp.z);
                if (Vector2.Distance(pp, v) > OverhearRadius + 12f || dup(o.id, v)) continue;
                placed.Add(new KeyValuePair<string, Vector2>(o.id, v));
                wantCache["ov:" + o.spot] = new W { id = o.id, pos = sp, min = 1.5f, max = OverhearRadius, gain = judge.npcs.SubtitleT > 0f ? 0.6f : 1f };
            }
        // 소품 소리(감나무 고목): 가까운 N개
        if (d.props != null)
            foreach (var pr in d.props)
            {
                List<Vector2> all;
                if (!propPos.TryGetValue(pr.prop, out all)) { all = FieldManager.PositionsOf(pr.prop); propPos[pr.prop] = all; }
                var near = new List<KeyValuePair<float, Vector2>>();
                foreach (var v in all) { float dd = Vector2.Distance(pp, v); if (dd <= pr.max + 12f) near.Add(new KeyValuePair<float, Vector2>(dd, v)); }
                near.Sort((a, b) => a.Key.CompareTo(b.Key));
                for (int i = 0; i < near.Count && i < Mathf.Max(1, pr.nearest); i++)
                    wantCache["pr:" + pr.prop + i] = new W { id = pr.id, pos = new Vector3(near[i].Value.x, 0f, near[i].Value.y), min = pr.min, max = pr.max, gain = pr.gain > 0f ? pr.gain : 1f };
            }
    }

    void Want(string key, string id, bool is3d, Vector3 pos, float min, float max, float gain)
    {
        Loop l;
        if (!loops.TryGetValue(key, out l))
        {
            var clip = Sfx.ClipFor(id); if (clip == null) return;   // 소리 파일이 아직 없으면 조용히 건너뛴다
            var go = new GameObject("snd_" + key); go.transform.SetParent(transform, false);
            var s = go.AddComponent<AudioSource>(); s.clip = clip; s.loop = true; s.volume = 0f; s.playOnAwake = false;
            if (is3d) { s.spatialBlend = 1f; s.rolloffMode = AudioRolloffMode.Logarithmic; s.minDistance = min; s.maxDistance = max; go.transform.position = pos; }
            s.time = Random.value * clip.length;   // 같은 소리 여러 개가 똑같이 겹치지 않게 시작 지점을 흩는다
            s.Play();
            l = new Loop { s = s }; loops[key] = l;
        }
        l.want = true; l.gain = gain;
    }

    void ApplyVolumes()
    {
        var dead = new List<string>();
        foreach (var kv in loops)
        {
            var l = kv.Value; if (l.s == null) { dead.Add(kv.Key); continue; }
            float target = l.want ? l.gain * SaveStore.Settings.Sfx * Sfx.Duck : 0f;
            l.s.volume = Mathf.MoveTowards(l.s.volume, target, Time.unscaledDeltaTime / (kv.Key.StartsWith("bed:") ? FadeBed : Fade3D));
            if (!l.want && l.s.volume <= 0f) { Destroy(l.s.gameObject); dead.Add(kv.Key); }
        }
        foreach (var k in dead) loops.Remove(k);
    }

    void FadeAll() { foreach (var l in loops.Values) l.want = false; ApplyVolumes(); }

    // ---- 흩뿌림 ----
    readonly Dictionary<string, float> sprT = new Dictionary<string, float>();
    string lastSpr;
    void TickSprinkles(string code)
    {
        if (judge == null || judge.Casting || d.sprinkles == null) return;   // 천도 시전 중엔 멈춘다
        foreach (var s in d.sprinkles)
        {
            if (s.code != code || !WhenOk(s.when)) continue;
            string key = s.code + s.id; float t;
            if (!sprT.TryGetValue(key, out t)) t = Time.unscaledTime + Random.Range(s.lo, s.hi);
            if (Time.unscaledTime >= t)
            {
                if (s.id != lastSpr) { Sfx.PlayLater(s.id, 0f, Random.Range(0.5f, 1f), Random.Range(-0.8f, 0.8f)); lastSpr = s.id; }   // 같은 소리가 연달아 두 번 나오지 않게(크기 0.5~1.0 은 높낮이로 갈음)
                t = Time.unscaledTime + Random.Range(s.lo, s.hi);
            }
            sprT[key] = t;
        }
    }

    /// <summary>새벽·저녁이 되는 순간, 그 구역 안이면 징을 한 번(교대 시각)</summary>
    void TickTimed(string code)
    {
        int ph = Sfx.PhaseNow;
        if (ph != lastPhase)
        {
            if (lastPhase >= 0 && (ph == 0 || ph == 2) && d.timed != null)
                foreach (var t in d.timed) if (System.Array.IndexOf(t.zones, code) >= 0) Sfx.PlayLater(t.id, Random.Range(0f, 3f));
            lastPhase = ph;
        }
    }
}
