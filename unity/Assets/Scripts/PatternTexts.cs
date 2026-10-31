// =============================================================================
// PatternTexts.cs — 보스 패턴 말풍선·경고 글과 원념 짙은 구역 경고 글(서사 boss_pattern_texts.json → Data/pattern_texts.json).
// 글은 서사팀이 고치므로 데이터에서 읽는다. key 는 "B-01.bigwater" 처럼 보스.이벤트.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public static class PatternTexts
{
    [System.Serializable] class Ev { public string key, bubble, warn, sfx; }
    [System.Serializable] class FileData { public Ev[] events; public string enter, enter_sub, leave, karma_high; }
    static FileData d; static bool loaded;
    static readonly HashSet<string> shown = new HashSet<string>();   // '처음 한 번만' 글자를 띄웠는지

    static void Load()
    {
        if (loaded) return; loaded = true;
        var ta = Resources.Load<TextAsset>("Data/pattern_texts");
        if (ta != null) d = JsonUtility.FromJson<FileData>(ta.text);
    }

    public static string Enter { get { Load(); return d != null ? d.enter : "원념이 짙다 — 혼이 몰려든다!"; } }
    public static string EnterSub { get { Load(); return d != null ? d.enter_sub : "천도는 더 위험하다"; } }
    public static string Leave { get { Load(); return d != null ? d.leave : "원념이 옅어졌다"; } }
    public static string KarmaHigh { get { Load(); return d != null ? d.karma_high : "원념이 짙다 — 발밑이 끈적하다!"; } }

    /// <summary>패턴 이벤트의 경고 글·말풍선·소리를 꺼낸다. once 면 같은 key 는 세션에서 글자를 한 번만(소리는 호출한 쪽이 매번)</summary>
    public static bool Get(string key, bool once, out string warn, out string bubble, out string sfx)
    {
        Load(); warn = bubble = sfx = null;
        if (d == null || d.events == null) return false;
        foreach (var e in d.events)
        {
            if (e.key != key) continue;
            sfx = string.IsNullOrEmpty(e.sfx) ? null : e.sfx;
            if (once && !shown.Add(key)) return true;   // 글자는 이미 보여 줬다(소리만 쓰게 warn·bubble 은 null)
            warn = string.IsNullOrEmpty(e.warn) ? null : e.warn; bubble = string.IsNullOrEmpty(e.bubble) ? null : e.bubble;
            return true;
        }
        return false;
    }
}
