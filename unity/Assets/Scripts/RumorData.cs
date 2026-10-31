// =============================================================================
// RumorData.cs — 2·3막 소문 엿듣기 30자리(서사 overhear_act2/3 → Data/overhear_flat.json)를 NpcWorld 에 심는다.
// 땅이 열린 막(FieldRules.Act2/Act3)의 자리만 심는다. 좌표는 act2/3 지도 절대 좌표(동 +x · 북 +z).
// =============================================================================
using Chasa.Core;
using UnityEngine;

public static class RumorData
{
    [System.Serializable] class Row { public string id, place, half, echo; public int act, time; public float x, z; public string[] speakers, lines; }
    [System.Serializable] class FileData { public Row[] spots; }

    public static void Load(NpcWorld npcs)
    {
        var ta = Resources.Load<TextAsset>("Data/overhear_flat"); if (ta == null || npcs == null) return;
        var f = JsonUtility.FromJson<FileData>(ta.text); if (f == null || f.spots == null) return;
        foreach (var r in f.spots)
        {
            if ((r.act == 2 && !FieldRules.Act2) || (r.act == 3 && !FieldRules.Act3)) continue;
            float x = r.x, z = r.z; MapLayout.PushOut(ref x, ref z, 0.6f);
            npcs.AddRumor(r.id, r.place, new Vector3(x, 0f, z), r.speakers, r.lines, r.half, r.time, r.echo);
        }
    }
}
