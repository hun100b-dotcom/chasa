// =============================================================================
// FieldManager.cs — 5×5 넓은 필드(640m)를 걸어가는 대로 켜고 끈다. (규칙: Core/FieldRules, 데이터: Resources/Data/field.json)
//
// 어떻게 동작하나?
//   1) 시작할 때 field.json 을 읽어 모든 항목(땅 타일·나무·집 조각·소품)을 128m 청크(칸)별로 묶어 둔다.
//   2) 플레이어 둘레 3×3 청크만 세운다. 먼 청크는 지운다 (웹·폰에서 가볍게).
//   3) 한 번에 다 세우면 프레임이 멈칫하니 프레임마다 ItemsPerFrame 개씩 나눠 세운다(코루틴).
//   4) 충돌(막힌 곳)은 청크를 켤 때 그림보다 먼저 등록한다 → 안 보여도 부딪힌다(보이는데 통과하는 일은 없게).
//   5) 불빛 26개: 가까운 몇 개만 진짜 점광원으로 켠다(내장 렌더러는 점광원이 많으면 느리다).
// 좌표/회전 약속(아트팀): 유니티 (x, 높이, z) = (블렌더 x, z, y), 방향 yaw = -rot.
// 풀밭 칸은 표에 안 적혀 있다(5천 칸) → 청크를 켤 때 비어 있는 8m 칸을 풀 타일로 채운다.
// 높이: 이번 판은 땅을 모두 평평하게(고지 +2m 는 0 으로) 둔다. 고지 걷기는 2차(높이 규칙 필요).
// =============================================================================
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class FieldManager : MonoBehaviour
{
    [System.Serializable] public class Item { public string n; public float x, y, z; public int r, t; }
    [System.Serializable] public class Marker { public string kind, name; public float x, z; }
    [System.Serializable] public class Lamp { public float x, y, z, intensity, range; public string color; public int flicker; }
    [System.Serializable] class FieldFile { public float size, tile; public Item[] items; public Marker[] markers; public Lamp[] lights; }

    public Player player;
    const int ItemsPerFrame = 60;                 // 프레임당 세우는 개수(PC 측정으로 조정)

    FieldFile data;
    readonly Dictionary<int, List<Item>> byChunk = new Dictionary<int, List<Item>>();
    readonly Dictionary<int, GameObject> roots = new Dictionary<int, GameObject>();
    readonly Dictionary<int, Coroutine> loading = new Dictionary<int, Coroutine>();
    readonly Dictionary<int, List<Blocker>> blockers = new Dictionary<int, List<Blocker>>();
    readonly Dictionary<string, GameObject> prefabs = new Dictionary<string, GameObject>();
    readonly Dictionary<Material, Material> matCache = new Dictionary<Material, Material>();
    Light[] pool = new Light[6]; Lamp[] poolLamp = new Lamp[6];
    float lampScan;
    int curChunk = -1;

    public string Status { get { return "필드 청크 켜짐 " + roots.Count; } }

    /// <summary>시작 위치·이야기 자리를 마커에서 읽어 FieldRules 에 넣는다. GameMain 이 맨 먼저 부른다</summary>
    public static void ApplyMarkers()
    {
        var ta = Resources.Load<TextAsset>("Data/field");
        if (ta == null) return;
        var f = JsonUtility.FromJson<FieldFile>(ta.text);
        if (f == null || f.markers == null) return;
        foreach (var m in f.markers)
        {
            if (m.kind == "spawn") { FieldRules.StartX = m.x; FieldRules.StartZ = m.z; }
            else if (m.kind == "village") { FieldRules.VillageX = m.x; FieldRules.VillageZ = m.z; }
            else if (m.kind == "boss") { FieldRules.BossX = m.x; FieldRules.BossZ = m.z; }
        }
    }

    void Awake()
    {
        var ta = Resources.Load<TextAsset>("Data/field");
        if (ta == null) { Debug.LogWarning("field.json 이 없다: 필드를 세우지 못한다"); enabled = false; return; }
        data = JsonUtility.FromJson<FieldFile>(ta.text);
        // 표에 적힌 항목을 청크별로 묶는다. 풀밭 칸(적히지 않은 8m 칸)은 켤 때 채운다
        foreach (var it in data.items) Bucket(it);
        // 불빛 점광원 풀(진짜 Light 6개를 돌려 쓴다)
        for (int i = 0; i < pool.Length; i++)
        {
            var g = new GameObject("FieldLamp" + i);
            g.transform.SetParent(transform, false);
            var l = g.AddComponent<Light>(); l.type = LightType.Point; l.shadows = LightShadows.None; l.enabled = false;
            pool[i] = l;
        }
    }

    void Bucket(Item it)
    {
        int key = FieldRules.Key(FieldRules.ChunkIndex(it.x), FieldRules.ChunkIndex(it.z));
        List<Item> l; if (!byChunk.TryGetValue(key, out l)) byChunk[key] = l = new List<Item>();
        l.Add(it);
    }

    void Update()
    {
        if (player == null || data == null) return;
        int cx = FieldRules.ChunkIndex(player.Pos.x), cz = FieldRules.ChunkIndex(player.Pos.z);
        int key = FieldRules.Key(cx, cz);
        if (key != curChunk)
        {
            curChunk = key;
            for (int x = cx - 1; x <= cx + 1; x++)
                for (int z = cz - 1; z <= cz + 1; z++)
                    if (x >= 0 && z >= 0 && x < FieldRules.Chunks && z < FieldRules.Chunks) Open(x, z);
            var drop = new List<int>();
            foreach (var kv in roots) { int ox = kv.Key / 100, oz = kv.Key % 100; if (Mathf.Abs(ox - cx) > 1 || Mathf.Abs(oz - cz) > 1) drop.Add(kv.Key); }
            foreach (var k in drop) Close(k);
        }
        lampScan -= Time.unscaledDeltaTime;
        if (lampScan <= 0f) { lampScan = 0.4f; AssignLamps(); }
        // 불빛 깜빡임(횃불·등불)
        for (int i = 0; i < pool.Length; i++)
            if (pool[i].enabled && poolLamp[i] != null)
            {
                float f = poolLamp[i].flicker == 1 ? 0.85f + 0.15f * Mathf.PerlinNoise(Time.time * 7f, i * 3.1f) : 1f;
                pool[i].intensity = poolLamp[i].intensity * 1.6f * f;
            }
    }

    // ---- 청크 켜기 / 끄기 ------------------------------------------------------
    void Open(int cx, int cz)
    {
        int key = FieldRules.Key(cx, cz);
        if (roots.ContainsKey(key)) return;
        var root = new GameObject("Chunk_" + cx + "_" + cz);
        root.transform.SetParent(transform, false);
        roots[key] = root;
        // 충돌 먼저
        var bl = new List<Blocker>();
        List<Item> items; if (!byChunk.TryGetValue(key, out items)) items = new List<Item>();
        foreach (var it in items)
        {
            float r = FieldRules.BlockerRadius(it.n);
            if (r > 0f) bl.Add(new Blocker("stone", it.x, it.z, r));
        }
        blockers[key] = bl;
        MapLayout.ZoneBlockers.AddRange(bl);
        loading[key] = StartCoroutine(Build(cx, cz, key, root, items));
    }

    void Close(int key)
    {
        Coroutine c; if (loading.TryGetValue(key, out c)) { StopCoroutine(c); loading.Remove(key); }
        GameObject root; if (roots.TryGetValue(key, out root)) { if (root != null) Destroy(root); roots.Remove(key); }
        List<Blocker> bl; if (blockers.TryGetValue(key, out bl)) { foreach (var b in bl) MapLayout.ZoneBlockers.Remove(b); blockers.Remove(key); }
    }

    IEnumerator Build(int cx, int cz, int key, GameObject root, List<Item> items)
    {
        int n = 0;
        // 1) 풀밭: 표에 없는 8m 칸을 채운다 (이 청크 16×16 칸)
        float tile = data.tile > 0 ? data.tile : 8f;
        int per = Mathf.RoundToInt(FieldRules.ChunkSize / tile);
        var listed = new HashSet<int>();
        foreach (var it in items) if (it.t == 1) listed.Add(Mathf.FloorToInt(it.x / tile) * 1000 + Mathf.FloorToInt(it.z / tile));
        for (int ix = cx * per; ix < (cx + 1) * per; ix++)
            for (int iz = cz * per; iz < (cz + 1) * per; iz++)
            {
                if (listed.Contains(ix * 1000 + iz)) continue;
                if (root == null) yield break;
                Place(root.transform, "terrain_tile_grass", ix * tile + tile * 0.5f, 0f, iz * tile + tile * 0.5f, 0);
                if (++n % ItemsPerFrame == 0) yield return null;
            }
        // 2) 표에 적힌 항목(길·비탈·냇물·나무·집·소품)
        foreach (var it in items)
        {
            if (root == null) yield break;
            Place(root.transform, it.n, it.x, HeightOf(it), it.z, it.r);
            if (++n % ItemsPerFrame == 0) yield return null;
        }
        loading.Remove(key);
    }

    /// <summary>
    /// 놓을 높이. 땅 타일과 '고지(+2m) 위 소품'은 땅을 평평하게 두니 0 으로 내리고,
    /// 한옥 조각(기단 위 벽 0.5 · 지붕 2.9 · 용마루 4.5)은 아트팀이 정한 높이를 그대로 쓴다(안 그러면 지붕이 바닥에 깔림).
    /// </summary>
    static float HeightOf(Item it)
    {
        if (it.t == 1) return 0f;                              // 땅 타일(고지 포함) 평평
        if (it.n.StartsWith("hanok_")) return it.y;            // 집 조각은 쌓는 높이 그대로
        return it.y >= 1.5f ? it.y - 2f : it.y;                // 고지(+2m) 위 나무·돌은 평평해진 땅에 맞춰 내림
    }

    /// <summary>모델 하나를 세운다. 재질은 모델 안의 색을 따서 우리 무광 재질로(같은 색은 하나를 나눠 써서 GPU 가 묶어 그린다)</summary>
    void Place(Transform parent, string name, float x, float y, float z, int rot)
    {
        GameObject prefab;
        if (!prefabs.TryGetValue(name, out prefab)) { prefab = Resources.Load<GameObject>("Models/Field/" + name); prefabs[name] = prefab; }
        if (prefab == null) return;
        var inst = Instantiate(prefab, parent);
        inst.transform.SetPositionAndRotation(new Vector3(x, y, z), Quaternion.Euler(0f, -rot, 0f));   // 유니티 yaw = -rot (아트 약속)
        // 지붕·처마·용마루·굴뚝은 카메라와 주인공 사이를 가리면 비켜 준다(큰 기와집 지붕이 보스를 가리던 문제)
        if (name.StartsWith("hanok_") && (name.Contains("roof") || name.Contains("eave") || name.Contains("ridge") || name.Contains("chimney")))
        { var of = inst.AddComponent<OccluderFade>(); of.radius = 3.2f; of.centerHeight = 3.2f; }
        foreach (var r in inst.GetComponentsInChildren<Renderer>())
        {
            var src = r.sharedMaterials; var dst = new Material[src.Length];
            for (int i = 0; i < src.Length; i++)
            {
                if (name == "terrain_tile_grass" && src[i] != null) { dst[i] = GrassVariant(src[i], x, z); continue; }   // 넓은 풀밭이 한 색 평면으로 보이지 않게 칸마다 약간 다른 초록
                Material m;
                if (src[i] == null || !matCache.TryGetValue(src[i], out m))
                {
                    m = U.Matte(Props3D.MatColor(src[i])); m.enableInstancing = true;
                    if (src[i] != null) matCache[src[i]] = m;
                }
                dst[i] = m;
            }
            r.sharedMaterials = dst;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;   // 수백 개 그림자는 웹에서 무거워 일단 끈다(주인공·혼은 그림자 유지)
            r.receiveShadows = true;
        }
    }

    readonly Dictionary<long, Material> grassMats = new Dictionary<long, Material>();
    static readonly float[] GrassTint = { 0.86f, 0.96f, 1.06f, 1.16f };

    /// <summary>풀 타일의 색을 위치로 4가지 밝기 중 하나로(같은 위치는 늘 같은 색 — 이웃 칸과 살짝 다르게). 변형마다 재질을 하나만 만든다</summary>
    Material GrassVariant(Material src, float x, float z)
    {
        int h = (Mathf.FloorToInt(x / 8f) * 73856093) ^ (Mathf.FloorToInt(z / 8f) * 19349663);
        int v = (h & 0x7fffffff) % GrassTint.Length;
        long key = (long)src.GetInstanceID() * 8 + v;
        Material m;
        if (!grassMats.TryGetValue(key, out m))
        {
            var c = Props3D.MatColor(src); float t = GrassTint[v];
            m = U.Matte(new Color(Mathf.Clamp01(c.r * t * 0.95f), Mathf.Clamp01(c.g * t), Mathf.Clamp01(c.b * t * 0.9f), 1f)); m.enableInstancing = true;
            grassMats[key] = m;
        }
        return m;
    }

    // ---- 불빛 ------------------------------------------------------------------
    void AssignLamps()
    {
        if (data.lights == null) return;
        var p = player.Pos;
        var near = new List<Lamp>(data.lights);
        near.Sort((a, b) => ((a.x - p.x) * (a.x - p.x) + (a.z - p.z) * (a.z - p.z)).CompareTo((b.x - p.x) * (b.x - p.x) + (b.z - p.z) * (b.z - p.z)));
        for (int i = 0; i < pool.Length; i++)
        {
            if (i >= near.Count) { pool[i].enabled = false; poolLamp[i] = null; continue; }
            var l = near[i];
            float d2 = (l.x - p.x) * (l.x - p.x) + (l.z - p.z) * (l.z - p.z);
            if (d2 > 45f * 45f) { pool[i].enabled = false; poolLamp[i] = null; continue; }   // 45m 밖은 안 켠다
            Color c; if (!ColorUtility.TryParseHtmlString(l.color, out c)) c = new Color(1f, 0.7f, 0.4f);
            pool[i].transform.position = new Vector3(l.x, l.y + 1.0f, l.z);
            pool[i].color = c; pool[i].range = Mathf.Max(6f, l.range * 1.4f);
            pool[i].enabled = true; poolLamp[i] = l;
        }
    }
}
