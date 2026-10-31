// =============================================================================
// First10.cs — 아트의 '처음 10분 그림' 묶음(Resources/Sprites/first10/)을 이름으로 꺼내 주는 창고.
// 왜 따로: 이 그림들은 manifest 에 없는 화면용(UI) 그림이라 피벗이 필요 없고, 가로 띠(프레임 여러 장)는 칸을 잘라 써야 한다.
// 그림이 없으면 null 을 돌려주고, 부르는 쪽이 코드 도형으로 대신한다(그림이 없어도 게임은 돈다).
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public static class First10
{
    static readonly Dictionary<string, Texture2D> tex = new Dictionary<string, Texture2D>();
    static readonly Dictionary<string, Sprite[]> strips = new Dictionary<string, Sprite[]>();

    public static Texture2D Tex(string name)
    {
        Texture2D t;
        if (tex.TryGetValue(name, out t)) return t;
        t = Resources.Load<Texture2D>("Sprites/first10/" + name);
        tex[name] = t; return t;
    }

    /// <summary>가로 띠를 frames 칸으로 잘라 스프라이트 배열로. ppu = 1m 당 픽셀(월드에 그릴 때 크기를 정한다)</summary>
    public static Sprite[] Strip(string name, int frames, float ppu = 100f)
    {
        string key = name + "|" + frames + "|" + ppu;
        Sprite[] s;
        if (strips.TryGetValue(key, out s)) return s;
        var t = Tex(name);
        if (t == null || frames < 1) { strips[key] = null; return null; }
        s = new Sprite[frames]; int w = t.width / frames;
        for (int i = 0; i < frames; i++) s[i] = Sprite.Create(t, new Rect(i * w, 0, w, t.height), new Vector2(0.5f, 0.5f), ppu);
        strips[key] = s; return s;
    }

    public static Sprite Whole(string name, float ppu = 100f)
    {
        var a = Strip(name, 1, ppu); return a != null ? a[0] : null;
    }
}
