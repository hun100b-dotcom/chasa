// =============================================================================
// GrowthData.cs — 기획팀이 보내 줄 도술·옵션 JSON 을 읽어 코드 표의 값을 덮어쓴다.
// 파일: Assets/Resources/Data/growth_overrides.json (없으면 아무것도 안 바꾼다 — 코드 기본값으로 돈다)
// 형식(예시는 같은 폴더 파일):
//   { "skills":  [ { "id": "HoldCall", "name": "Hold Call", "cooldown": 12 } ],
//     "optionBase": [ { "kind": "DamagePct", "base": 0.06 } ] }
// id/kind 는 코드 이름(SkillId, Opt)을 쓴다. 모르는 이름은 건너뛰고 경고만 남긴다(한 줄 오타가 게임을 멈추지 않게).
// =============================================================================
using System;
using Chasa.Core;
using UnityEngine;

public static class GrowthData
{
    [Serializable] class SkillRow { public string id; public string name; public float cooldown; }
    [Serializable] class OptRow { public string kind; public float @base; }
    [Serializable] class File { public SkillRow[] skills; public OptRow[] optionBase; }

    static bool loaded;

    public static void Load()
    {
        if (loaded) return;
        loaded = true;
        var ta = Resources.Load<TextAsset>("Data/growth_overrides");
        if (ta == null) return;
        File f;
        try { f = JsonUtility.FromJson<File>(ta.text); }
        catch (Exception e) { Debug.LogWarning("growth_overrides.json 을 읽지 못했다: " + e.Message); return; }
        if (f == null) return;
        if (f.skills != null)
            foreach (var s in f.skills)
                if (!SkillDef.Override(s.id, s.name, s.cooldown)) Debug.LogWarning("알 수 없는 도술 id: " + s.id);
        if (f.optionBase != null)
            foreach (var o in f.optionBase)
                if (!Loot.SetBase(o.kind, o.@base)) Debug.LogWarning("알 수 없는 옵션 kind: " + o.kind);
    }
}
