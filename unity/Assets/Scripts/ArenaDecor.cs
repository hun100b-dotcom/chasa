// =============================================================================
// ArenaDecor.cs — 보스 싸움터 3곳(나루터·폐당집 굿판·역병막 마당)의 '꾸밈': 바닥 무늬 한 장 + 소품 + 조명.
//   아트팀이 만든 배치표(Data/boss_arenas.json, tools/build_arena_data.py 가 만든다)를 읽어 그대로 세운다.
//   판정은 하지 않는다(판정은 BossArena·JudgeSystem). 그림과 판정이 같은 규칙(CupPos·CellPos)으로 맞춰져 있다.
//   가까이 가야(120m) 만들어서 멀리서는 비용이 없다. 보스가 처결되면 조명·바닥 무늬는 끄고 소품은 남긴다.
// =============================================================================
using System;
using System.Collections.Generic;
using UnityEngine;

public class ArenaDecor : MonoBehaviour
{
    [Serializable] class PropRow { public string n; public float x, z; public int r, c; }
    [Serializable] class LightRow { public float x, z, h, i, range; public string col; public bool flicker, weak; }
    [Serializable] class ArenaRow { public int id; public float x, z, decalSize; public string decal; public bool waterLevel; public PropRow[] props; public LightRow[] lights; }
    [Serializable] class Table { public ArenaRow[] arenas; }

    static Table table;
    public static Light WeakLight;   // 서 의원 약장 맨 아래 서랍(약점)의 청록 불. 약점이 열릴 때만 BossArena 가 켠다

    JudgeSystem judge; Enemy boss; int id; ArenaRow row;
    bool built; GameObject root; GameObject decal;
    readonly List<Light> lights = new List<Light>(); readonly List<float> baseI = new List<float>(); readonly List<bool> flick = new List<bool>(); readonly List<bool> weakFlag = new List<bool>();
    Light weak;

    public Light WeakLamp { get { return weak; } }

    public static ArenaDecor Make(JudgeSystem j, Enemy b, int bossId)
    {
        if (table == null)
        {
            var ta = Resources.Load<TextAsset>("Data/boss_arenas");
            table = ta != null ? JsonUtility.FromJson<Table>(ta.text) : new Table { arenas = new ArenaRow[0] };
        }
        ArenaRow r = null;
        foreach (var a in table.arenas) if (a.id == bossId) r = a;
        if (r == null) return null;
        var d = new GameObject("ArenaDecor" + bossId).AddComponent<ArenaDecor>();
        d.judge = j; d.boss = b; d.id = bossId; d.row = r;
        return d;
    }

    // 싸움터 안(전투 거리)에 있는지: 조명을 켜는 기준
    bool InFight(float dist) { return boss != null && boss.alive && dist < 24f; }

    void Update()
    {
        if (judge == null || row == null) return;
        float dist = new Vector2(judge.player.Pos.x - row.x, judge.player.Pos.z - row.z).magnitude;
        if (!built && dist < 120f) Build();
        if (!built) return;
        bool gone = boss != null && !boss.alive;
        if (decal != null) decal.SetActive(!gone && dist < 70f);
        bool on = InFight(dist);
        if (gone && weak != null) weak.enabled = false;
        for (int i = 0; i < lights.Count; i++)
        {
            var l = lights[i];
            if (weakFlag[i]) continue;   // 약점 불은 BossArena 가 켜고 끈다
            l.enabled = on;
            if (on && flick[i]) l.intensity = baseI[i] * (0.85f + 0.3f * Mathf.PerlinNoise(Time.time * 7f, i * 3.1f));
        }
    }

    void Build()
    {
        built = true;
        root = new GameObject("ArenaDecorRoot"); root.transform.SetParent(transform, false);
        foreach (var p in row.props)
        {
            var prefab = Resources.Load<GameObject>("Models/Field/" + p.n);
            if (prefab == null) continue;
            float y = GroundTerrain.HeightAt(p.x, p.z);
            var inst = Instantiate(prefab, root.transform);
            inst.transform.SetPositionAndRotation(new Vector3(p.x, y, p.z), Quaternion.Euler(0f, -p.r, 0f));   // 유니티 yaw = -rot (아트 약속)
            foreach (var r in inst.GetComponentsInChildren<Renderer>())
            {
                var src = r.sharedMaterials; var dst = new Material[src.Length];
                for (int k = 0; k < src.Length; k++) dst[k] = U.Matte(Props3D.MatColor(src[k]));
                r.sharedMaterials = dst;
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
        }
        // 바닥 무늬: 정사각 그림(위=북·오른쪽=동). 땅(물이면 물면) 위 0.04m 에 눕힌다. 한가운데가 보스 자리
        var tex = SpriteLib.Texture("boss/" + row.decal);
        if (tex != null)
        {
            decal = new GameObject("Decal"); decal.transform.SetParent(root.transform, false);
            float gy = row.waterLevel ? 0.05f : GroundTerrain.HeightAt(row.x, row.z) + 0.04f;
            decal.transform.position = new Vector3(row.x, gy, row.z);
            decal.transform.rotation = Quaternion.Euler(90f, 0f, 0f);   // 스프라이트를 눕힘: 위쪽이 북(+z)
            var sr = decal.AddComponent<SpriteRenderer>();
            sr.sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), tex.width / row.decalSize);
            sr.sortingOrder = -5;
        }
        foreach (var lr in row.lights)
        {
            var go = new GameObject("ArenaLight"); go.transform.SetParent(root.transform, false);
            go.transform.position = new Vector3(lr.x, GroundTerrain.HeightAt(lr.x, lr.z) + lr.h, lr.z);
            var l = go.AddComponent<Light>(); l.type = LightType.Point; l.shadows = LightShadows.None;
            Color c; if (!ColorUtility.TryParseHtmlString(lr.col, out c)) c = Color.white;
            l.color = c; l.intensity = lr.i; l.range = lr.range; l.enabled = false;
            lights.Add(l); baseI.Add(lr.i); flick.Add(lr.flicker); weakFlag.Add(lr.weak);
            if (lr.weak) weak = l;
        }
    }
}
