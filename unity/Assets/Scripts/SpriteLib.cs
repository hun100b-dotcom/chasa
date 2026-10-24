// =============================================================================
// SpriteLib.cs — 아트팀 PNG 를 이름으로 꺼내 주는 창고.
// Resources/Sprites/manifest.json 에 적힌 피벗(발 위치)·PPU(1m 당 픽셀 수)로 Sprite 를 런타임에 만든다.
// 왜 런타임? 파일마다 피벗을 에디터에서 손으로 맞추면 그림이 바뀔 때마다 또 해야 해서. manifest 가 원본이다.
// 그림이 없으면 null 을 돌려주고, 부르는 쪽은 색 도형(옛 임시 모습)으로 대신 그린다 — 그림이 없어도 게임은 돈다.
// =============================================================================
using System;
using System.Collections.Generic;
using UnityEngine;

public static class SpriteLib
{
    [Serializable] class Entry { public string file; public int w, h; public float pivotX, pivotY, ppu; public bool tint; }
    [Serializable] class Manifest { public float ppu; public Entry[] sprites; }

    static Dictionary<string, Entry> entries;
    static readonly Dictionary<string, Sprite> cache = new Dictionary<string, Sprite>();

    static void Load()
    {
        entries = new Dictionary<string, Entry>();
        var ta = Resources.Load<TextAsset>("Sprites/manifest");
        if (ta == null) return;
        var m = JsonUtility.FromJson<Manifest>(ta.text);
        if (m == null || m.sprites == null) return;
        foreach (var e in m.sprites) entries[e.file.Replace(".png", "")] = e;
    }

    /// <summary>스프라이트가 아닌 원본 텍스처가 필요할 때(지형 타일을 메쉬에 입힐 때). 없으면 null</summary>
    public static Texture2D Texture(string name) { return Resources.Load<Texture2D>("Sprites/" + name); }

    /// <summary>"characters/chasa_idle" 같은 이름으로 스프라이트를 얻는다. 없으면 null</summary>
    public static Sprite Get(string name)
    {
        if (entries == null) Load();
        Sprite s;
        if (cache.TryGetValue(name, out s)) return s;
        Entry e;
        var tex = Resources.Load<Texture2D>("Sprites/" + name);
        if (tex == null || !entries.TryGetValue(name, out e)) { cache[name] = null; return null; }
        s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(e.pivotX, 1f - e.pivotY)   // manifest 는 아래가 1(그림 좌표), 유니티 피벗은 아래가 0 이라 뒤집는다
            , e.ppu > 0 ? e.ppu : 128f);
        cache[name] = s;
        return s;
    }
}
