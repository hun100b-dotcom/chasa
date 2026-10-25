// =============================================================================
// Act1Soundscape.cs — 1막 주변 소리(사운드팀 data/act1_soundscape.json → Resources/Data/act1_soundscape.json).
// "어디를 걸어도 같은 소리"를 없애려고 세 겹을 깐다:
//   바탕   구역마다 밤 반복음 하나(2D). 구역이 바뀌면 3초 교차.
//   자리   서낭당·넋길 입구·소품(모닥불·고목·허수아비·개울)·외톨이 혼 곁의 3D 반복음. 소품은 가까운 N개만 켠다(음원 수를 아끼려고).
//   흩뿌림 부엉이·먼 개 같은 한 번짜리를 구역마다 무작위 간격·좌우로. 반복음의 이음매가 안 들리게 하는 역할. 천도 시전 중엔 멈춘다.
// ZoneAmbient(2·3막)와 따로 둔 까닭: 1막 소리는 낮밤·소품 위치를 보는 규칙이 다르다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class Act1Soundscape : MonoBehaviour
{
    [System.Serializable] class Bed { public string zone, id; }
    [System.Serializable] class Pt { public string id, when, note; public float x, z, min, max; }
    [System.Serializable] class Prop { public string prop, id, when, group; public float min, max, every_m, day_gain, inside_lowpass_hz; public int nearest; }
    [System.Serializable] class LonerRow { public string loop, notice; public float min, max, notice_m; }
    [System.Serializable] class Spr { public string zone, id; public float lo, hi; public bool night; }
    [System.Serializable] class Line { public string id; public float x1, z1, x2, z2, min, max; public bool night_only; }
    [System.Serializable] class FileData { public Bed[] beds; public Pt[] points; public Prop[] props; public LonerRow loner; public Spr[] sprinkles; public Bed[] beds_day; public Line[] lines; }

    class Loop { public AudioSource s; public bool want; public float gain = 1f; }

    FileData d;
    JudgeSystem judge; System.Func<Vector3> playerPos;
    readonly Dictionary<string, Loop> loops = new Dictionary<string, Loop>();
    readonly Dictionary<string, List<Vector2>> propPos = new Dictionary<string, List<Vector2>>();
    readonly HashSet<Enemy> noticed = new HashSet<Enemy>();
    float scanT;
    const float Fade3D = 0.5f, FadeBed = 3f;

    public static Act1Soundscape Create(JudgeSystem j, System.Func<Vector3> pos)
    {
        var ta = Resources.Load<TextAsset>("Data/act1_soundscape");
        if (ta == null) return null;
        var g = new GameObject("Act1Soundscape").AddComponent<Act1Soundscape>();
        g.d = JsonUtility.FromJson<FileData>(ta.text); g.judge = j; g.playerPos = pos;
        return g;
    }

    bool Night { get { return Sfx.NightNow; } }

    void Update()
    {
        if (d == null || playerPos == null || Sfx.Muted) { FadeAll(0f); return; }
        var p = playerPos();
        foreach (var l in loops.Values) l.want = false;
        // 바탕: 밤에만. 구역 이름이 표에 있을 때
        if (Night) foreach (var b in d.beds) { if (b.zone == FieldZones.CurrentName) Want("bed:" + b.id, b.id, false, Vector3.zero, 0f, 0f, 0.6f); }
        else if (d.beds_day != null) foreach (var b in d.beds_day) if (b.zone == FieldZones.CurrentName) Want("bed:" + b.id, b.id, false, Vector3.zero, 0f, 0f, 0.6f);   // 낮 바탕은 표에 있는 구역만(없으면 옛 amb.field)
        // 물줄기 같은 긴 소리: 선분 위에서 나와 가장 가까운 점 하나를 소리 자리로 삼는다(매 프레임 옮겨 끊김이 없다)
        if (d.lines != null) foreach (var ln in d.lines)
        {
            if (ln.night_only && !Night) continue;
            var a = new Vector2(ln.x1, ln.z1); var ab = new Vector2(ln.x2, ln.z2) - a;
            float t = Mathf.Clamp01(Vector2.Dot(new Vector2(p.x, p.z) - a, ab) / Mathf.Max(0.01f, ab.sqrMagnitude));
            var q = a + ab * t;
            if (Vector2.Distance(new Vector2(p.x, p.z), q) > ln.max + 12f) continue;
            Want("line:" + ln.id, ln.id, true, new Vector3(q.x, 0f, q.y), ln.min, ln.max, 1f);
        }
        // 자리 + 소품 + 외톨이: 반 초마다 후보를 다시 고른다(소품 수천 개를 매 프레임 돌지 않으려고)
        scanT -= Time.unscaledDeltaTime;
        if (scanT <= 0f) { scanT = 0.5f; Rescan(p); }
        foreach (var kv in wantCache) Want(kv.Key, kv.Value.id, true, kv.Value.pos, kv.Value.min, kv.Value.max, kv.Value.gain);
        ApplyVolumes();
        TickSprinkles();
    }

    struct W { public string id; public Vector3 pos; public float min, max, gain; }
    readonly Dictionary<string, W> wantCache = new Dictionary<string, W>();

    void Rescan(Vector3 p)
    {
        wantCache.Clear();
        var pp = new Vector2(p.x, p.z);
        // 서낭당·넋길 입구·대장간 화덕
        for (int i = 0; i < d.points.Length; i++)
        {
            var q = d.points[i];
            if (q.when == "night" && !Night) continue;
            if (Vector2.Distance(pp, new Vector2(q.x, q.z)) > q.max + 12f) continue;   // 들릴 일 없는 먼 소리는 음원을 만들지 않는다
            wantCache["pt" + i] = new W { id = q.id, pos = new Vector3(q.x, 0f, q.z), min = q.min, max = q.max, gain = 1f };
        }
        // 소품 점 소리: 소품마다 가까운 N개만(개울은 12 m 간격으로 솎는다)
        var doneGroups = new HashSet<string>();
        foreach (var pr in d.props)
        {
            if (pr.when == "night" && !Night) continue;                                       // 병자 등 같은 밤 전용 소품
            string gkey = string.IsNullOrEmpty(pr.group) ? pr.prop : "g:" + pr.group;
            if (!string.IsNullOrEmpty(pr.group) && !doneGroups.Add(pr.group)) continue;      // 같은 묶음(버드나무 a·b 등)은 합쳐서 한 번만 고른다
            List<Vector2> all;
            if (!propPos.TryGetValue(gkey, out all))
            {
                all = new List<Vector2>();
                foreach (var o2 in d.props) if (o2 == pr || (!string.IsNullOrEmpty(pr.group) && o2.group == pr.group)) all.AddRange(FieldManager.PositionsOf(o2.prop));
                propPos[gkey] = all;
            }
            var near = new List<KeyValuePair<float, Vector2>>();
            foreach (var v in all) { float dd = Vector2.Distance(pp, v); if (dd <= pr.max + 12f) near.Add(new KeyValuePair<float, Vector2>(dd, v)); }
            near.Sort((a, b) => a.Key.CompareTo(b.Key));
            var picked = new List<Vector2>();
            foreach (var kv in near)
            {
                if (picked.Count >= Mathf.Max(1, pr.nearest)) break;
                bool tooClose = false;
                if (pr.every_m > 0f) foreach (var o in picked) if (Vector2.Distance(o, kv.Value) < pr.every_m) { tooClose = true; break; }
                if (!tooClose) picked.Add(kv.Value);
            }
            for (int i = 0; i < picked.Count; i++) wantCache["pr:" + gkey + i] = new W { id = pr.id, pos = new Vector3(picked[i].x, 0f, picked[i].y), min = pr.min, max = pr.max, gain = !Night && pr.day_gain > 0f ? pr.day_gain : 1f };
        }
        // 외톨이 혼: 무릎 꿇고 있는 동안 곁에서 들린다. 근처에서 싸우는 중이면 0.5배, 8 m 안에 처음 들어오면 고개 드는 소리 한 번
        if (judge != null && judge.enemies != null && d.loner != null && !string.IsNullOrEmpty(d.loner.loop))
        {
            int n = 0;
            foreach (var e in judge.enemies.list)
            {
                if (e == null || !e.loner || !e.alive || e.gone || !e.kneeling) continue;
                float dd = Vector2.Distance(pp, new Vector2(e.Pos.x, e.Pos.z));
                if (dd > d.loner.max + 12f) continue;
                bool fighting = false;
                foreach (var o in judge.enemies.list) if (o != null && o.alive && !o.kneeling && !o.loner && Vector2.Distance(new Vector2(o.Pos.x, o.Pos.z), new Vector2(e.Pos.x, e.Pos.z)) < 14f) { fighting = true; break; }
                wantCache["loner" + (n++)] = new W { id = d.loner.loop, pos = e.Pos, min = d.loner.min, max = d.loner.max, gain = fighting ? 0.5f : 1f };
                if (dd <= d.loner.notice_m && noticed.Add(e)) Sfx.Play(d.loner.notice);
            }
        }
    }

    void Want(string key, string id, bool is3d, Vector3 pos, float min, float max, float gain)
    {
        Loop l;
        if (!loops.TryGetValue(key, out l))
        {
            var clip = Sfx.ClipFor(id); if (clip == null) return;   // 파일이 없으면 조용히 건너뛴다
            var go = new GameObject("snd_" + key); go.transform.SetParent(transform, false);
            var s = go.AddComponent<AudioSource>(); s.clip = clip; s.loop = true; s.volume = 0f; s.playOnAwake = false;
            if (is3d) { s.spatialBlend = 1f; s.rolloffMode = AudioRolloffMode.Logarithmic; s.minDistance = min; s.maxDistance = max; go.transform.position = pos; }
            s.time = Random.value * clip.length;   // 같은 소리 여러 개가 똑같이 겹쳐 울리지 않게 시작 지점을 흩는다
            s.Play();
            l = new Loop { s = s }; loops[key] = l;
        }
        else if (is3d && l.s != null) l.s.transform.position = pos;   // 움직이는 혼 곁이면 따라간다
        l.want = true; l.gain = gain;
    }

    void ApplyVolumes()
    {
        var dead = new List<string>();
        foreach (var kv in loops)
        {
            var l = kv.Value; if (l.s == null) { dead.Add(kv.Key); continue; }
            bool bed = kv.Key.StartsWith("bed:");
            float target = l.want ? l.gain * SaveStore.Settings.Sfx * Sfx.Duck : 0f;
            l.s.volume = Mathf.MoveTowards(l.s.volume, target, Time.unscaledDeltaTime / (bed ? FadeBed : Fade3D));
            if (!l.want && l.s.volume <= 0f) { Destroy(l.s.gameObject); dead.Add(kv.Key); }
        }
        foreach (var k in dead) loops.Remove(k);
    }

    void FadeAll(float v) { foreach (var l in loops.Values) l.want = false; ApplyVolumes(); }

    /// <summary>여울이 앓는 소리는 업 30 이상이면 간격이 절반(원념 고인 물이라는 암시)</summary>
    float Gap(string id) { return id == "sfx.geomeun.groan" && judge != null && judge.ledger != null && judge.ledger.Karma >= 30 ? 0.5f : 1f; }

    // ---- 흩뿌림 ----
    readonly Dictionary<string, float> sprT = new Dictionary<string, float>();
    string lastSpr;
    void TickSprinkles()
    {
        if (judge == null || judge.Casting) return;   // 천도 시전 중엔 멈춘다
        foreach (var s in d.sprinkles)
        {
            if (s.zone != FieldZones.CurrentName || (s.night && !Night)) continue;
            string key = s.zone + s.id;
            float t;
            if (!sprT.TryGetValue(key, out t)) t = Time.unscaledTime + Random.Range(s.lo, s.hi) * Gap(s.id);
            if (Time.unscaledTime >= t)
            {
                if (s.id != lastSpr) { Sfx.PlayLater(s.id, 0f, 1f, Random.Range(-0.8f, 0.8f)); lastSpr = s.id; }   // 같은 소리가 연달아 두 번 나오지 않게
                t = Time.unscaledTime + Random.Range(s.lo, s.hi) * Gap(s.id);
            }
            sprT[key] = t;
        }
    }
}
