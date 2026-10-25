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
    [System.Serializable] public class Item { public string n; public float x, y, z; public int r, t, k; }   // k: 바닥 채움 소품의 등급(2 = 풀·꽃, 45m 안에서만 그린다)
    [System.Serializable] public class Marker { public string kind, name; public float x, z; }
    [System.Serializable] public class Lamp { public float x, y, z, intensity, range; public string color; public int flicker; }
    [System.Serializable] class FieldFile { public float size, tile; public Item[] items; public Marker[] markers; public Lamp[] lights; }

    public Player player;
    CoverInstancer cover;   // 바닥 채움 소품(cover_*)은 오브젝트 없이 GPU 인스턴싱으로 그린다
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

    public string Status { get { return "필드 청크 켜짐 " + roots.Count + (cover != null ? " · 바닥 소품 " + cover.DrawnCount : ""); } }

    [System.Serializable] class ShrineRow { public string id, name; public float x, y; }
    [System.Serializable] class Act2File { public ShrineRow[] shrines; }

    /// <summary>2막 서낭당 SH2-1·SH2-2(처음부터 열림)를 넋길 정류장 목록 끝에 붙인다. SH2-3(산성 쉼터)은 'B-06 천도 뒤'라 해금 규칙이 생기면 추가</summary>
    static void AddAct2Shrines()
    {
        var ta = Resources.Load<TextAsset>("Data/act2_map"); if (ta == null) return;
        var f = JsonUtility.FromJson<Act2File>(ta.text); if (f == null || f.shrines == null) return;
        var pos = new System.Collections.Generic.List<float[]>(FieldRules.Shrines);
        var names = new System.Collections.Generic.List<string>(FieldRules.ShrineNames);
        foreach (var s in f.shrines) { if (s.id == "SH2-3") continue; pos.Add(new[] { s.x, s.y }); names.Add(s.name); }
        FieldRules.Shrines = pos.ToArray(); FieldRules.ShrineNames = names.ToArray();
    }

    /// <summary>시작 위치·이야기 자리를 마커에서 읽어 FieldRules 에 넣는다. GameMain 이 맨 먼저 부른다</summary>
    public static void ApplyMarkers()
    {
        var ta = Resources.Load<TextAsset>("Data/field");
        if (ta == null) return;
        var f = JsonUtility.FromJson<FieldFile>(ta.text);
        if (f == null || f.markers == null) return;
        // 넋길 정류장: 서낭당 마커 + 폐당집 입구를 남→북 순으로
        var stops = new System.Collections.Generic.List<Marker>();
        foreach (var m in f.markers) if (m.kind == "seonang" || m.kind == "ruin") stops.Add(m);
        stops.Sort((a, b) => a.z.CompareTo(b.z));
        FieldRules.Shrines = stops.ConvertAll(m => new[] { m.x, m.z }).ToArray();
        FieldRules.ShrineNames = stops.ConvertAll(m => m.name).ToArray();
        if (FieldRules.Act2) AddAct2Shrines();   // 2막 서낭당(붉은재·산신각)을 넋길 정류장 뒤에 잇는다
        foreach (var m in f.markers)
        {
            if (m.kind == "spawn") { FieldRules.StartX = m.x; FieldRules.StartZ = Mathf.Max(m.z, 56f); }   // 카메라가 -x,-z 쪽을 비스듬히 내려다봐서, 남쪽 끝(z<30)에 서면 화면 위쪽 절반이 맵 밖 맨바닥이다 → 마을 안쪽으로 물린다
            else if (m.kind == "village") { FieldRules.VillageX = m.x; FieldRules.VillageZ = m.z; }
            else if (m.kind == "boss") { FieldRules.BossX = m.x; FieldRules.BossZ = m.z; }
        }
    }

    void Awake()
    {
        var ta = Resources.Load<TextAsset>("Data/field");
        if (ta == null) { Debug.LogWarning("field.json 이 없다: 필드를 세우지 못한다"); enabled = false; return; }
        data = JsonUtility.FromJson<FieldFile>(ta.text);
        cover = gameObject.AddComponent<CoverInstancer>(); cover.player = player;
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
        int key = FieldRules.Key(FieldRules.RawChunk(it.x), FieldRules.RawChunk(it.z));   // 붙이지 않는다: 아직 안 열린 2막 항목이 1막 가장자리 청크로 섞이지 않게
        List<Item> l; if (!byChunk.TryGetValue(key, out l)) byChunk[key] = l = new List<Item>();
        l.Add(it);
    }

    void Update()
    {
        if (player == null || data == null) return;
        if (cover != null && cover.player == null) cover.player = player;   // GameMain 이 player 를 Awake 뒤에 넣어 준다
        int cx = FieldRules.ChunkX(player.Pos.x), cz = FieldRules.ChunkZ(player.Pos.z);
        int key = FieldRules.Key(cx, cz);
        if (key != curChunk)
        {
            curChunk = key;
            for (int x = cx - 1; x <= cx + 1; x++)
                for (int z = cz - 1; z <= cz + 1; z++)
                    if (x >= 0 && z >= 0 && x < FieldRules.ChunksX && z < FieldRules.ChunksZ) Open(x, z);
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
                pool[i].intensity = poolLamp[i].intensity * 1.6f * f * (1f - 0.9f * Chasa.Core.SkyState.Daylight);   // 낮엔 등불이 거의 안 보이게
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
            if (it.n.StartsWith("cover_")) { cover.Add(key, it); continue; }   // 바닥 채움 소품: 충돌 없음, 인스턴싱으로
            float r = FieldRules.BlockerRadius(it.n);
            if (r > 0f) bl.Add(new Blocker("stone", it.x, it.z, r));
        }
        blockers[key] = bl;
        MapLayout.ZoneBlockers.AddRange(bl);
        loading[key] = StartCoroutine(Build(cx, cz, key, root, items));
    }

    void Close(int key)
    {
        Coroutine c; if (loading.TryGetValue(key, out c)) { if (c != null) StopCoroutine(c); loading.Remove(key); }   // 바로 끝난 코루틴은 null 로 남을 수 있다(새 땅: 세울 것이 없는 청크) → null 이면 멈추지 않는다(PC 확인: NullReferenceException)
        if (cover != null) cover.Remove(key);
        GameObject root; if (roots.TryGetValue(key, out root)) { if (root != null) Destroy(root); roots.Remove(key); }
        List<Blocker> bl; if (blockers.TryGetValue(key, out bl)) { foreach (var b in bl) MapLayout.ZoneBlockers.Remove(b); blockers.Remove(key); }
    }

    IEnumerator Build(int cx, int cz, int key, GameObject root, List<Item> items)
    {
        int n = 0;
        yield return GroundTerrain.BuildChunk(root.transform, cx, cz);   // 새 땅(하이트맵·스플랫맵)이 있으면 이 청크의 땅 메쉬를 깐다. 없으면 아무것도 안 함
        // 1) 풀밭: 표에 없는 8m 칸을 채운다 (이 청크 16×16 칸)
        float tile = data.tile > 0 ? data.tile : 8f;
        int per = Mathf.RoundToInt(FieldRules.ChunkSize / tile);
        var listed = new HashSet<int>();
        foreach (var it in items) if (it.t == 1) listed.Add(Mathf.FloorToInt(it.x / tile) * 1000 + Mathf.FloorToInt(it.z / tile));
        for (int ix = cx * per; ix < (cx + 1) * per; ix++)
            for (int iz = cz * per; iz < (cz + 1) * per; iz++)
            {
                if (GroundTerrain.Active || listed.Contains(ix * 1000 + iz)) continue;   // 새 땅이면 풀 타일도 필요 없다
                if (root == null) yield break;
                Place(root.transform, "terrain_tile_grass", ix * tile + tile * 0.5f, 0f, iz * tile + tile * 0.5f, 0);
                if (++n % ItemsPerFrame == 0) yield return null;
            }
        // 2) 표에 적힌 항목(길·비탈·냇물·나무·집·소품)
        foreach (var it in items)
        {
            if (root == null) yield break;
            if (it.n.StartsWith("cover_")) continue;          // 바닥 채움 소품은 CoverInstancer 가 그린다
            if (GroundTerrain.Active && it.t == 1) continue;   // 옛 땅 타일은 새 땅 메쉬가 대신한다
            if (SkipDecor(it)) continue;                       // 폰: 작은 장식 일부를 건너뛴다
            float py = it.z >= FieldRules.Size ? it.y : HeightOf(it) + GroundTerrain.HeightAt(it.x, it.z);   // 2막(z 640 이상) 표의 높이(y)는 땅 높이까지 이미 더해 둔 절대값
            Place(root.transform, it.n, it.x, py, it.z, it.r);   // 소품·집은 땅 높이 위에 붙인다(옛 평지는 +0)
            if (++n % ItemsPerFrame == 0) yield return null;
        }
        loading.Remove(key);
    }

    /// <summary>화질이 낮을 때 충돌 없는 작은 장식(덤불·작은 바위·죽은 나무)을 자리 값으로 일정하게 건너뛴다(같은 자리는 늘 같은 결과)</summary>
    static bool SkipDecor(Item it)
    {
        float skip = QualityTier.DecorSkip; if (skip <= 0f) return false;
        if (!(it.n.StartsWith("nature_bush") || it.n == "terrain_rock_small" || it.n.StartsWith("nature_dead"))) return false;
        if (FieldRules.BlockerRadius(it.n) > 0f) return false;   // 충돌이 있는 건 그대로(안 보이는 벽이 생기면 안 된다)
        int h = (Mathf.FloorToInt(it.x * 7.31f) * 73856093) ^ (Mathf.FloorToInt(it.z * 5.17f) * 19349663);
        return ((h & 0x7fffffff) % 1000) / 1000f < skip;
    }

    const float TileThickness = 0.3f;   // 땅 타일 두께. 아트 표의 높이(z)는 '칸 아랫면' 기준이고 타일 윗면은 그보다 0.3 위다

    /// <summary>
    /// 놓을 높이. 걸어 다니는 바닥(주인공 발)을 높이 0 으로 삼으려고, 타일 윗면이 0 이 되게 타일과 'br_' 조각을 0.3 내린다.
    /// 그러면 소품(표 z = 칸 아랫면 기준 → 윗면 기준으로 +0.3, 전체를 −0.3 내리니 결국 z 그대로)이 땅에 묻히지 않는다.
    /// 아주 납작한 것(거적·웅덩이·디딤돌)은 타일 윗면과 겹쳐 깜박이지 않게 2cm 띄운다.
    /// 고지(+2m) 위 소품은 땅을 평평하게 두므로 2m 내린다. 한옥 조각은 아트가 정한 쌓는 높이 그대로(기단 위 벽 0.5 · 지붕 2.9 · 용마루 4.5).
    /// </summary>
    static float HeightOf(Item it)
    {
        if (it.t == 1) return -TileThickness;                              // 땅 타일(고지 포함) 평평
        if (it.n.StartsWith("br_")) return it.y - TileThickness;           // 다리·나루터·배 조각은 처음부터 칸 아랫면 기준 → 타일과 같이 내린다
        if (it.n.StartsWith("hanok_")) return it.y;
        float y = it.y >= 1.5f ? it.y - 2f : it.y;
        return y < 0.05f ? 0.02f : y;
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
                if (src[i] != null && src[i].name.Contains("water"))   // 큰 강 물면: 알파 블렌드 + 흐르는 물 재질(없으면 아래로 내려가 단색 재질)
                {
                    var wm = GroundTerrain.RiverWater(src[i].name.Contains("deep"));
                    if (wm != null) { dst[i] = wm; continue; }
                }
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
            if (i >= near.Count || i >= QualityTier.LampBudget) { pool[i].enabled = false; poolLamp[i] = null; continue; }   // 폰은 등불 점 광원을 적게
            var l = near[i];
            float d2 = (l.x - p.x) * (l.x - p.x) + (l.z - p.z) * (l.z - p.z);
            if (d2 > 45f * 45f) { pool[i].enabled = false; poolLamp[i] = null; continue; }   // 45m 밖은 안 켠다
            Color c; if (!ColorUtility.TryParseHtmlString(l.color, out c)) c = new Color(1f, 0.7f, 0.4f);
            pool[i].transform.position = new Vector3(l.x, l.y + 1.0f + GroundTerrain.HeightAt(l.x, l.z), l.z);
            pool[i].color = c; pool[i].range = Mathf.Max(6f, l.range * 1.4f);
            pool[i].enabled = true; poolLamp[i] = l;
        }
    }
}
