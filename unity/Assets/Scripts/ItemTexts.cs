// =============================================================================
// ItemTexts.cs — 서사가 쓴 아이템 설명글(세계관 문장): 인 15종·인의 조각·도술 27개. 파일: Resources/Data/item_texts.json (원본 docs/narrative/item_texts.json)
// 화면 순서(서사 규칙): 이름 → 기능 문구(기획 표) → 빈 줄 → 세계관 문장(흐린 글씨). 이 클래스는 세계관 문장만 돌려준다.
// 파일이 없거나 이름이 없으면 빈 글자(화면은 그냥 그 줄을 안 그린다).
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public static class ItemTexts
{
    [System.Serializable] class Row { public string name; public string[] text; }
    [System.Serializable] class Data { public Row[] seals; public Row[] skills; }

    static Dictionary<string, string> seals, skills;

    static Dictionary<string, string> Index(Row[] rows)
    {
        var d = new Dictionary<string, string>();
        if (rows != null) foreach (var r in rows) if (r != null && r.name != null && r.text != null) d[r.name] = string.Join("\n", r.text);
        return d;
    }

    static void Load()
    {
        if (seals != null) return;
        seals = new Dictionary<string, string>(); skills = new Dictionary<string, string>();
        var ta = Resources.Load<TextAsset>("Data/item_texts");
        if (ta == null) return;
        var d = JsonUtility.FromJson<Data>(ta.text);
        if (d == null) return;
        seals = Index(d.seals); skills = Index(d.skills);
    }

    /// <summary>인 이름(큰 인이면 "큰 " 앞말은 떼고)의 세계관 문장. 없으면 빈 글자</summary>
    public static string Seal(string sealName)
    {
        Load(); string v; if (sealName != null && sealName.StartsWith("큰 ")) sealName = sealName.Substring(2);
        return sealName != null && seals.TryGetValue(sealName, out v) ? v : "";
    }
    public static string Skill(string skillName) { Load(); string v; return skillName != null && skills.TryGetValue(skillName, out v) ? v : ""; }
}
