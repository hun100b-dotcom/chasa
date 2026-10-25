// =============================================================================
// SoulRoadTexts.cs — 넋길 추가 도착점의 이름과 '처음 닿을 때 한 줄'(서사 field_extra_texts.json → Data/soulroad_extra.json).
// 왜 따로? 문구는 서사팀이 고치므로 코드에 박지 않고 데이터 파일에서 읽는다. 파일이 없으면 옛 이름("○○의 마당 어귀")으로 돌아간다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public static class SoulRoadTexts
{
    [System.Serializable] class Row { public int id; public string name, arrive; }
    [System.Serializable] class FileData { public Row[] stops; }
    static Dictionary<int, Row> rows;

    /// <summary>보스 번호(1~3, 5~12…)로 도착점 이름과 첫 도착 한 줄을 찾는다. 없으면 fallback 이름·null</summary>
    public static void Find(int bossId, out string name, out string arrive, string fallback)
    {
        if (rows == null)
        {
            rows = new Dictionary<int, Row>();
            var ta = Resources.Load<TextAsset>("Data/soulroad_extra");
            var f = ta == null ? null : JsonUtility.FromJson<FileData>(ta.text);
            if (f != null && f.stops != null) foreach (var r in f.stops) rows[r.id] = r;
        }
        Row row;
        if (rows.TryGetValue(bossId, out row)) { name = row.name; arrive = row.arrive; }
        else { name = fallback; arrive = null; }
    }
}
