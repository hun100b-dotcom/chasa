// =============================================================================
// SeonangTexts.cs — 서낭당 5곳 문구(서사 seonang_texts.json → Resources/Data/seonang_flat.json).
// 처음 만져 볼 때 두 줄, 쉬고 난 뒤 한 줄(낮·밤이 다르고, 그 관할 보스를 처결한 뒤 첫 낮 쉬기엔 처결 방식에 따른 한 줄),
// 직전과 같은 줄은 피한다. 자리는 아트 서낭당 5곳 좌표와 가장 가까운 곳으로 가린다.
// =============================================================================
using UnityEngine;

public static class SeonangTexts
{
    [System.Serializable] public class Shrine { public string model, rest_halmi, tendo, pahon; public string[] first_touch, rest_day, rest_night; public int boss; }
    [System.Serializable] public class Overhear { public string id, cond, half; public float x, z; public bool wall; public string[] speakers, lines; }
    [System.Serializable] class FileData { public Shrine[] shrines; public string death_wake; public Overhear[] overhear; }

    // 서낭당 ①~⑤ 자리(field.json 의 구역별 서낭당과 같음) — shrines 배열 순서와 같다
    static readonly float[] Xs = { 188f, 160f, 356f, 108f, 580f }, Zs = { 36f, 180f, 324f, 452f, 552f };
    static FileData data;
    static bool loaded;

    static void Load()
    {
        if (loaded) return; loaded = true;
        var ta = Resources.Load<TextAsset>("Data/seonang_flat");
        if (ta != null) data = JsonUtility.FromJson<FileData>(ta.text);
    }

    public static Overhear[] Overhears { get { Load(); return data != null ? data.overhear : new Overhear[0]; } }
    public static string DeathWake { get { Load(); return data != null ? data.death_wake : null; } }

    /// <summary>이 자리에서 12 m 안의 서낭당 번호(0~4). 없으면 -1</summary>
    public static int IndexAt(Vector3 p)
    {
        Load(); if (data == null || data.shrines == null) return -1;
        int best = -1; float bd = 12f;
        for (int i = 0; i < Xs.Length && i < data.shrines.Length; i++) { float d = Vector2.Distance(new Vector2(p.x, p.z), new Vector2(Xs[i], Zs[i])); if (d < bd) { bd = d; best = i; } }
        return best;
    }

    public static Shrine Get(int i) { Load(); return data != null && i >= 0 && i < data.shrines.Length ? data.shrines[i] : null; }

    /// <summary>처음 만질 때의 두 줄("\n"으로 이음)</summary>
    public static string FirstTouch(int i) { var s = Get(i); return s == null || s.first_touch == null || s.first_touch.Length == 0 ? null : string.Join("\n", s.first_touch); }

    static int lastRest = -1;
    /// <summary>쉬고 난 뒤의 한 줄. bossAfter 가 "tendo"/"pahon"이면 그 관할 보스 처결 뒤 첫 쉬기용 줄을 쓴다</summary>
    public static string RestLine(int i, bool night, string bossAfter)
    {
        var s = Get(i); if (s == null) return null;
        if (bossAfter == "tendo" && !string.IsNullOrEmpty(s.tendo)) return s.tendo;
        if (bossAfter == "pahon" && !string.IsNullOrEmpty(s.pahon)) return s.pahon;
        var pool = night ? s.rest_night : s.rest_day; if (pool == null || pool.Length == 0) return null;
        int k = Random.Range(0, pool.Length); if (pool.Length > 1 && k == lastRest) k = (k + 1) % pool.Length;   // 직전과 다른 줄
        lastRest = k; return pool[k];
    }
}
