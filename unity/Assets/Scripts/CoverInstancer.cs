// =============================================================================
// CoverInstancer.cs — 필드 바닥 채움 소품(풀·꽃·보리 이랑·돌·강변 소품, 약 2.7만 개)을 'GPU 인스턴싱'으로 그린다.
//
// 왜 따로 만드나? 일반 소품은 하나마다 게임 오브젝트(GameObject, 화면의 물건 하나)를 만들지만, 2.7만 개를 그렇게 만들면
//   웹·폰이 멈춘다. 여기서는 오브젝트를 만들지 않고, '같은 모델은 위치만 다르게 한 번에 그려 달라'(DrawMeshInstanced)고 GPU 에 맡긴다.
// 거리 컬링(culling, 멀리 있는 것은 아예 안 그리기): 플레이어 둘레 tier 1(보리 줄·돌·강변 소품)은 70m, tier 2(풀·꽃)는 45m.
//   0.25초마다 한 번만 '지금 보일 것'을 다시 고르고, 그 사이엔 같은 목록을 그린다.
// 충돌 없음, 그림자 없음(아트 안내). 높이는 땅 높이표(GroundTerrain.HeightAt) 위에 얹는다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class CoverInstancer : MonoBehaviour
{
    public Player player;
    public static float Tier1Range = 48f, Tier2Range = 30f;   // 이 거리 밖은 안 그린다(m)

    struct Inst { public Vector3 pos; public Matrix4x4 world; public bool tier2; }
    class Part { public Mesh mesh; public int sub; public Material mat; public Matrix4x4 local; }
    class Group { public Part[] parts; public List<Matrix4x4[]>[] bufs; public int count; }

    readonly Dictionary<string, Part[]> partCache = new Dictionary<string, Part[]>();
    readonly Dictionary<Material, Material> matCache = new Dictionary<Material, Material>();
    readonly Dictionary<int, Dictionary<string, List<Inst>>> chunks = new Dictionary<int, Dictionary<string, List<Inst>>>();   // 청크 → 모델 이름 → 놓을 자리들
    float rescan; Vector3 lastScan = new Vector3(1e9f, 0f, 1e9f);

    /// <summary>청크가 켜질 때 그 청크의 바닥 채움 소품을 등록한다(오브젝트는 안 만든다)</summary>
    public void Add(int key, FieldManager.Item it)
    {
        Dictionary<string, List<Inst>> d; if (!chunks.TryGetValue(key, out d)) chunks[key] = d = new Dictionary<string, List<Inst>>();
        List<Inst> l; if (!d.TryGetValue(it.n, out l)) d[it.n] = l = new List<Inst>();
        float y = it.y + GroundTerrain.HeightAt(it.x, it.z);
        var pos = new Vector3(it.x, y, it.z);
        l.Add(new Inst { pos = pos, world = Matrix4x4.TRS(pos, Quaternion.Euler(0f, -it.r, 0f), Test ? Vector3.one * 3f : Vector3.one), tier2 = it.k >= 2 });   // 유니티 yaw = -rot (아트 약속)
    }

    public void Remove(int key) { chunks.Remove(key); rescan = 0f; lastScan = new Vector3(1e9f, 0f, 1e9f); }

    Part[] PartsOf(string name)
    {
        Part[] ps; if (partCache.TryGetValue(name, out ps)) return ps;
        var prefab = Resources.Load<GameObject>("Models/Field/" + name);
        var list = new List<Part>();
        if (prefab != null)
            foreach (var mf in prefab.GetComponentsInChildren<MeshFilter>())
            {
                var r = mf.GetComponent<Renderer>(); if (r == null || mf.sharedMesh == null) continue;
                var mats = r.sharedMaterials;
                for (int s = 0; s < mf.sharedMesh.subMeshCount; s++)
                {
                    var src = s < mats.Length ? mats[s] : null; Material m;
                    if (src == null || !matCache.TryGetValue(src, out m))
                    {
                        m = U.Matte(Test ? new Color(1f, 0.1f, 0.8f) : Props3D.MatColor(src)); m.enableInstancing = true;   // 같은 색은 한 재질을 나눠 쓴다
                        if (src != null) matCache[src] = m;
                    }
                    list.Add(new Part { mesh = mf.sharedMesh, sub = s, mat = m, local = prefab.transform.worldToLocalMatrix * mf.transform.localToWorldMatrix });
                }
            }
        ps = list.ToArray(); partCache[name] = ps; return ps;
    }

    // 검사용 주소 ?covertest=1: 바닥 소품을 3배 크게 + 분홍색으로 그린다(그려지는데 눈에 안 띄는 건지, 아예 안 그려지는 건지 가르려고)
    static readonly bool Test = (Application.absoluteURL ?? "").Contains("covertest=1");
    public int DrawnCount { get { int n = 0; foreach (var g in groups.Values) n += g.count; return n; } }   // 지금 그리는 개수(검사용)
    const int Batch = 1023;   // DrawMeshInstanced 한 번에 그릴 수 있는 최대 개수
    void Update()
    {
        if (player == null || chunks.Count == 0) return;
        rescan -= Time.unscaledDeltaTime;
        var p = player.Pos;
        if (rescan <= 0f || (p - lastScan).sqrMagnitude > 4f) { rescan = 0.25f; lastScan = p; Rescan(p); }
        foreach (var g in groups.Values)
        {
            if (g.count == 0) continue;
            for (int i = 0; i < g.parts.Length; i++)
            {
                var part = g.parts[i];
                for (int b = 0, off = 0; off < g.count; b++, off += Batch)
                    Graphics.DrawMeshInstanced(part.mesh, part.sub, part.mat, g.bufs[i][b], Mathf.Min(Batch, g.count - off), null, UnityEngine.Rendering.ShadowCastingMode.Off, true);
            }
        }
    }

    readonly Dictionary<string, Group> groups = new Dictionary<string, Group>();   // 모델별 그릴 목록(배열을 다시 쓰려고 계속 들고 있는다: 쓰레기(GC) 줄이기)

    /// <summary>플레이어 둘레의 보일 것만 골라, 모델별·부품별 행렬 배열을 다시 채운다(배열은 재사용)</summary>
    void Rescan(Vector3 p)
    {
        float q = QualityTier.DecorSkip > 0f ? 0.7f : 1f;   // 낮은 화질은 거리를 줄인다
        float r1 = Tier1Range * q, r2 = Tier2Range * q; float r1s = r1 * r1, r2s = r2 * r2;
        foreach (var g in groups.Values) g.count = 0;
        foreach (var cd in chunks.Values)
            foreach (var kv in cd)
            {
                Group g = null;
                foreach (var it in kv.Value)
                {
                    float dx = it.pos.x - p.x, dz = it.pos.z - p.z, d2 = dx * dx + dz * dz;
                    if (d2 > (it.tier2 ? r2s : r1s)) continue;
                    if (g == null && !groups.TryGetValue(kv.Key, out g))
                    {
                        var parts = PartsOf(kv.Key); if (parts.Length == 0) break;
                        groups[kv.Key] = g = new Group { parts = parts, bufs = new List<Matrix4x4[]>[parts.Length] };
                        for (int i = 0; i < parts.Length; i++) g.bufs[i] = new List<Matrix4x4[]>();
                    }
                    int k = g.count++, b = k / Batch, o = k % Batch;
                    for (int i = 0; i < g.parts.Length; i++)
                    {
                        while (g.bufs[i].Count <= b) g.bufs[i].Add(new Matrix4x4[Batch]);
                        g.bufs[i][b][o] = it.world * g.parts[i].local;   // 놓일 자리 × 부품의 모델 안 위치
                    }
                }
            }
    }
}
