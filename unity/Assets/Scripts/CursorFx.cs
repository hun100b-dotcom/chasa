// =============================================================================
// CursorFx.cs — 마우스 커서 모양 (기획 명세 §3-3). 적 위에 올리면 칼 모양, 평소엔 기본 화살표.
// 왜 코드로 그리나? 에셋 없이도 '지금 누르면 때린다'가 보이게 하려고. 32×32 그림을 한 번 만들어 쓴다(흰 칼날 + 어두운 2px 외곽선).
// WebGL 에서는 Cursor.SetCursor 가 그림 커서를 지원한다(CursorMode.Auto).
// =============================================================================
using UnityEngine;

public static class CursorFx
{
    public enum Kind { Default, Attack }
    static Texture2D attack; static Kind current = Kind.Default;

    public static void Set(Kind k)
    {
        if (k == current) return;
        current = k;
        if (k == Kind.Default) { Cursor.SetCursor(null, Vector2.zero, CursorMode.Auto); return; }
        if (attack == null) attack = MakeSword();
        Cursor.SetCursor(attack, new Vector2(3f, 3f), CursorMode.Auto);   // 칼끝이 클릭 지점
    }

    static Texture2D MakeSword()
    {
        const int N = 32;
        var t = new Texture2D(N, N, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
        var clear = new Color(0, 0, 0, 0); for (int y = 0; y < N; y++) for (int x = 0; x < N; x++) t.SetPixel(x, y, clear);
        // 칼끝(왼쪽 위)에서 오른쪽 아래로 뻗는 대각선. 텍스처 y 는 아래가 0 이라 화면 위쪽 = 큰 y
        for (int i = 0; i < 22; i++)
        {
            int x = 3 + i, y = N - 1 - (3 + i);
            for (int dx = -2; dx <= 2; dx++) for (int dy = -2; dy <= 2; dy++)   // 어두운 외곽선(2px)
                if (x + dx >= 0 && x + dx < N && y + dy >= 0 && y + dy < N) t.SetPixel(x + dx, y + dy, new Color(0.08f, 0.06f, 0.07f, 0.95f));
        }
        for (int i = 0; i < 22; i++) { t.SetPixel(3 + i, N - 1 - (3 + i), Color.white); t.SetPixel(4 + i, N - 1 - (3 + i), i < 16 ? new Color(0.85f, 0.88f, 0.95f) : new Color(0.7f, 0.25f, 0.2f)); }   // 날(흰) + 자루(붉은)
        t.Apply(); return t;
    }
}
