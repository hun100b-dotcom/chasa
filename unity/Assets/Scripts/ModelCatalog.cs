// =============================================================================
// ModelCatalog.cs — Resources/Data/models.json 을 읽어 "어떤 3D 모델을 어디에 쓸지"를 알려 주는 표.
//
// 왜 JSON 인가? 오너가 승인한 무료 3D 에셋이나 아트팀 모델이 올 때마다 코드를 고치지 않으려고.
//   모델 파일을 Resources/Models 에 넣고 이 표에 한 줄 적으면 바뀐다. 표에 없으면 코드로 만든 도형 대역이 대신 선다.
// =============================================================================
using System;
using System.Collections.Generic;
using UnityEngine;

public static class ModelCatalog
{
    [Serializable] public class ClipRow { public string pose; public string clip; }
    [Serializable] public class ActorRow
    {
        public string key, path, texture; public float scale = 1f, yaw;   // yaw: 앞 방향 보정(도). glTFast 는 GLB 의 앞(+Z)을 유니티에서 뒤집어 읽어서 GLB 모델은 180
        public ClipRow[] clips; public string[] loop;
    }
    [Serializable] public class PropRow { public string sprite, path, texture; public float scale = 1f, yaw; }
    [Serializable] class File { public ActorRow[] actors; public PropRow[] props; }

    static readonly Dictionary<string, ActorRow> actors = new Dictionary<string, ActorRow>();
    static readonly List<PropRow> props = new List<PropRow>();
    static bool loaded;

    static void Load()
    {
        if (loaded) return;
        loaded = true;
        var ta = Resources.Load<TextAsset>("Data/models");
        if (ta == null) return;
        try
        {
            var f = JsonUtility.FromJson<File>(ta.text);
            if (f == null) return;
            if (f.actors != null) foreach (var a in f.actors) actors[a.key] = a;
            if (f.props != null) props.AddRange(f.props);
        }
        catch (Exception e) { Debug.LogWarning("models.json 을 읽지 못했다: " + e.Message); }   // 오타 하나가 게임을 멈추지 않게
    }

    public static ActorRow Actor(string key) { Load(); ActorRow a; return actors.TryGetValue(key, out a) ? a : null; }

    /// <summary>소품 그림 이름(예: props/prop_jars)에 맞는 모델 줄 (없으면 null)</summary>
    public static PropRow Prop(string sprite)
    {
        Load();
        foreach (var p in props) if (sprite.EndsWith(p.sprite)) return p;
        return null;
    }
}
