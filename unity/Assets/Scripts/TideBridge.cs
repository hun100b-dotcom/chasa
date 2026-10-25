// =============================================================================
// TideBridge.cs — 3막 소품 동작 두 가지(아트 ACT3-KIT-PLAN §2).
//  1) TideWater: 이름이 tide_water 로 시작하는 물판을 썰물·밀물(Core/Tide)에 맞춰 오르내린다.
//  2) BridgeDeckFade: 플레이어가 '큰 다리 밑'(BridgeUnder 사각형)에 들어가면 bridge_deck 소품(상판·난간)을 숨긴다.
//     왜 숨김? 쿼터뷰 카메라가 다리 위쪽에서 내려다봐서, 다리 밑에 선 주인공이 상판에 가려 안 보인다. 알파(반투명) 전환은
//     재질을 따로 만들어야 해서, 먼저 가장 단순하고 확실한 '숨기기'로 한다(아트가 deck 전용 반투명 재질을 주면 교체).
// 소품은 FieldManager.Place 가 만들 때 Register 로 등록한다(청크가 꺼지면 사라지므로 죽은 것은 알아서 걸러낸다).
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

/// <summary>물판 하나. 놓인 높이가 간조(썰물)이고, 만조 때 rise 만큼 올라온다</summary>
public class TideWater : MonoBehaviour
{
    public static float WorldMinutes;   // JudgeSystem 이 매 프레임 알려 준다(하루 수 × 40 + 하루 안의 분)
    public float rise = 1.1f;           // 간조(놓인 높이, 아트 기준 -0.5)에서 만조(+0.6)까지 올라가는 높이(m)
    float lowY; bool init;
    const float CoastRise = 1.5f;       // 해안 띠 물판은 -7.5(썰물)↔-6.0(밀물) = 1.5m 오르내린다(아트 terrain.json)

    void LateUpdate()
    {
        if (!init) { lowY = transform.position.y; init = true; if (lowY < -5f) rise = CoastRise; }   // 아트 약속: 배치표의 높이가 썰물(간조) 높이. 해안 띠(깊이 -5m 아래)는 오르내림 폭이 달라 따로
        var p = transform.position;
        p.y = lowY + Tide.Level(WorldMinutes) * rise;
        transform.position = p;
    }
}

public class BridgeDeckFade : MonoBehaviour
{
    public Transform player;
    static readonly List<Renderer> decks = new List<Renderer>();
    readonly List<float[]> rects = new List<float[]>();   // [x0, z0, x1, z1]
    bool hidden;

    [System.Serializable] class ZoneRow { public string code; public float[] rect_m; }
    [System.Serializable] class MapFile { public ZoneRow[] zones; }

    /// <summary>FieldManager.Place 가 호출: 이름에 따라 조각에 동작을 붙인다</summary>
    public static void Register(string name, GameObject inst)
    {
        if (name.StartsWith("tide_water")) inst.AddComponent<TideWater>();
        else if (name.StartsWith("bridge_deck")) decks.AddRange(inst.GetComponentsInChildren<Renderer>());
    }

    void Start()
    {
        var ta = Resources.Load<TextAsset>("Data/act3_map"); if (ta == null) return;
        var f = JsonUtility.FromJson<MapFile>(ta.text); if (f == null || f.zones == null) return;
        foreach (var z in f.zones) if (z.code == "BridgeUnder" && z.rect_m != null && z.rect_m.Length >= 4) rects.Add(z.rect_m);
    }

    void Update()
    {
        if (player == null || rects.Count == 0) return;
        var p = player.position; bool under = false;
        foreach (var r in rects) if (p.x >= r[0] && p.x <= r[2] && p.z >= r[1] && p.z <= r[3]) { under = true; break; }
        // 밑에 있는 동안은 매 프레임 숨김을 다시 적용한다(밑에서 새 청크의 상판이 켜져도 숨겨지도록). 벗어난 첫 프레임에 한 번 다시 보이게 한다
        if (under || hidden) { decks.RemoveAll(d => d == null); foreach (var d in decks) d.enabled = !under; }
        hidden = under;
    }
}
