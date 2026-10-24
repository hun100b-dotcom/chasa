// 차사 색 토큰 (아트팀 원본: docs/art/palette-tokens.json)
// (이미 Scripts 폴더에 복사됨. 색은 여기서만 가져다 쓴다.)
// 왜 한 곳에 모으나: 색을 코드 여기저기에 직접 적으면 나중에 팔레트가 바뀔 때 다 찾아 고쳐야 한다.
// 값 변경은 아트팀만 한다(변경 시 palette-tokens.json과 이 파일을 함께 갱신).
using UnityEngine;

public static class ChasaPalette
{
    // "#RRGGBB" 문자열을 Unity 색으로 바꾸는 도우미 (sRGB 값 그대로 사용)
    static Color Hex(string h)
    {
        ColorUtility.TryParseHtmlString(h, out var c);
        return c;
    }

    /// <summary>환경 / 밤_남청_기본</summary>
    public static readonly Color NightIndigo = Hex("#16213E");
    /// <summary>환경 / 밤_심연</summary>
    public static readonly Color NightDeep = Hex("#0F1729");
    /// <summary>환경 / 이승_환경광_청록</summary>
    public static readonly Color AmbientTeal = Hex("#4FA8A0");
    /// <summary>환경 / 한지_바탕</summary>
    public static readonly Color Hanji = Hex("#F3E7D3");
    /// <summary>차사 / 차사_붉은띠</summary>
    public static readonly Color ChasaRed = Hex("#E85C41");
    /// <summary>차사 / 단청_금</summary>
    public static readonly Color DanchungGold = Hex("#D4A94E");
    /// <summary>차사 / 도포_먹</summary>
    public static readonly Color DopoInk = Hex("#2A2A38");
    /// <summary>차사 / 철삭_빛</summary>
    public static readonly Color ChainGlow = Hex("#BFE8FF");
    /// <summary>천도 / 천도_발광_청록</summary>
    public static readonly Color CheondoGlow = Hex("#5FE3C0");
    /// <summary>천도 / 기억_테두리_보라</summary>
    public static readonly Color MemoryRim = Hex("#C9B0FF");
    /// <summary>혼_단계 / 갓_죽은_혼</summary>
    public static readonly Color SoulFresh = Hex("#BFE8FF");
    /// <summary>혼_단계 / 해_넘긴_혼</summary>
    public static readonly Color SoulDay = Hex("#FFCC55");
    /// <summary>혼_단계 / 오래된_혼 — 녹슨 적갈색. 주황(#E8683A)은 파혼 전용이라 겹치지 않게 바꿈(기획 총정리 ④, 2026-10-25)</summary>
    public static readonly Color SoulOld = Hex("#A8472E");
    /// <summary>혼_단계 / 덩어리</summary>
    public static readonly Color SoulMass = Hex("#9A5CFF");
    /// <summary>파혼 / 파혼_폭발</summary>
    public static readonly Color PahonBurst = Hex("#E8683A");
    /// <summary>파혼 / 원념_얼룩</summary>
    public static readonly Color WonnyeomStain = Hex("#7B4FD6");
}
