// =============================================================================
// ZoneManager.cs — 플레이어가 걸어가면 둘레 3×3 구역을 켜고, 멀어진 구역은 끈다. (규칙은 Core/World 의 ZoneStreamer)
//
// 왜 한꺼번에 안 세우나?
//   웹(WebGL)은 일꾼(쓰레드)이 없어서 구역 하나를 통째로 세우면 그 프레임이 멈칫한다(끊김).
//   그래서 땅은 한 번에 깔되(몇 ms) 소품은 프레임마다 N개(Balance.ZONE_LOAD_PROPS_PER_FRAME)씩 세운다.
//   이웃 구역을 미리 켜 두므로 플레이어는 로딩 화면을 보지 않는다.
// 충돌(막힌 곳)은 그림보다 먼저 등록한다 → 소품이 아직 안 보여도 부딪힌다(보이는데 통과하는 일은 있어도 그 반대는 없게).
// 마을(0번 구역)은 이야기 규칙이 붙어 있어서 항상 켜 둔다(끄지 않음).
// =============================================================================
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class ZoneManager : MonoBehaviour
{
    public Player player;

    readonly ZoneStreamer streamer = new ZoneStreamer();
    readonly Dictionary<ZoneDef, GameObject> roots = new Dictionary<ZoneDef, GameObject>();
    readonly Dictionary<ZoneDef, Coroutine> loading = new Dictionary<ZoneDef, Coroutine>();
    readonly List<ZoneDef> load = new List<ZoneDef>(), drop = new List<ZoneDef>();
    int propsBuilt;

    public ZoneDef Current { get { return streamer.Current; } }
    /// <summary>화면 구석 디버그용 한 줄</summary>
    public string Status { get { return "구역 " + (Current != null ? Current.Name : "-") + " / 켜짐 " + roots.Count + " / 소품 " + propsBuilt; } }

    void Update()
    {
        if (player == null) return;
        load.Clear(); drop.Clear();
        streamer.Update(player.Pos.x, player.Pos.z, load, drop);
        foreach (var z in load) Open(z);
        foreach (var z in drop) Close(z);
    }

    void Open(ZoneDef z)
    {
        if (z.Village) { roots[z] = null; return; }   // 마을은 BuildStage 가 이미 세웠다
        if (roots.ContainsKey(z)) return;
        MapLayout.ZoneBlockers.AddRange(z.Blockers);   // 충돌 먼저
        var root = MapView.BuildZoneGround(z, transform);
        roots[z] = root;
        loading[z] = StartCoroutine(BuildProps(z, root));
        Debug.Log("[Zone] 켬 " + z.Name + " (" + z.Id + ") / 켜짐 " + roots.Count);
    }

    IEnumerator BuildProps(ZoneDef z, GameObject root)
    {
        int n = 0;
        foreach (var p in z.Props)
        {
            if (root == null) yield break;   // 소품을 세우는 사이에 구역이 꺼졌다
            MapView.BuildZoneProp(root, p); propsBuilt++;
            if (++n % Balance.ZONE_LOAD_PROPS_PER_FRAME == 0) yield return null;
        }
        loading.Remove(z);
    }

    void Close(ZoneDef z)
    {
        if (z.Village) return;
        Coroutine c;
        if (loading.TryGetValue(z, out c)) { StopCoroutine(c); loading.Remove(z); }
        GameObject root;
        if (roots.TryGetValue(z, out root))
        {
            if (root != null) { propsBuilt -= Mathf.Min(propsBuilt, z.Props.Count); Destroy(root); }
            roots.Remove(z);
        }
        foreach (var b in z.Blockers) MapLayout.ZoneBlockers.Remove(b);
        Debug.Log("[Zone] 끔 " + z.Name + " (" + z.Id + ") / 켜짐 " + roots.Count);
    }
}
