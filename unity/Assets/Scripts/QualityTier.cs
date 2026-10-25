// =============================================================================
// QualityTier.cs — 기기에 맞춰 화질 단계(낮음·보통·높음)를 고른다. 폰은 낮음, 태블릿은 보통, PC 는 높음.
// 왜 필요한가? 웹 게임을 폰 브라우저에서 열면 그림자·점 광원·풀 수가 그대로라 발열과 끊김이 심하다. 눈에 덜 띄는 것부터 줄인다.
// 단계를 손으로 고르려면 주소 뒤에 ?q=low / ?q=mid / ?q=high 를 붙인다.
// 줄이는 것: 그림자(끄기/딱딱하게/부드럽게) · 점 광원 수 · 길가 등불 수 · 작은 장식(덤불·작은 바위·죽은 나무) 개수 · 목표 프레임
// (화면 해상도는 웹 페이지 틀(index.html)이 devicePixelRatio 로 정한다 — 같은 ?q 값을 읽는다)
// =============================================================================
using UnityEngine;

public static class QualityTier
{
    public enum Level { Low, Mid, High }

    static bool decided; static Level level = Level.High;

    public static Level Current { get { Decide(); return level; } }
    public static bool IsLow { get { return Current == Level.Low; } }

    /// <summary>길가 등불 점 광원 최대 수(풀은 6개)</summary>
    public static int LampBudget { get { switch (Current) { case Level.Low: return 2; case Level.Mid: return 4; default: return 6; } } }

    /// <summary>작은 장식을 이 확률로 건너뛴다(충돌 없는 덤불·작은 바위·죽은 나무만)</summary>
    public static float DecorSkip { get { switch (Current) { case Level.Low: return 0.5f; case Level.Mid: return 0.25f; default: return 0f; } } }

    static void Decide()
    {
        if (decided) return;
        decided = true;
        string u = (Application.absoluteURL ?? "").ToLowerInvariant();
        if (u.Contains("q=low")) { level = Level.Low; return; }
        if (u.Contains("q=mid")) { level = Level.Mid; return; }
        if (u.Contains("q=high")) { level = Level.High; return; }
        // 자동: 터치 기기이면서 짧은 변이 작으면 폰(낮음), 크면 태블릿(보통). PC 크롬은 touchSupported 가 true 일 수 있어 화면 크기·dpi 도 본다
        bool touch = Input.touchSupported;
        int shortSide = Mathf.Min(Screen.width, Screen.height);
        bool smallScreen = shortSide < 1200;   // 폰 가로 화면의 짧은 변(보통 1000 안팎 이하, 장치 픽셀 기준)
        if (Application.isMobilePlatform) level = shortSide < 1200 ? Level.Low : Level.Mid;
        else if (touch && smallScreen && Screen.dpi > 200f) level = Level.Low;
        else if (touch && Screen.dpi > 200f) level = Level.Mid;
        else level = Level.High;
    }

    /// <summary>해(햇빛)와 품질 설정에 단계를 적용한다. 게임을 세울 때 한 번 부른다</summary>
    public static void Apply(Light sun)
    {
        switch (Current)
        {
            case Level.Low:
                if (sun != null) sun.shadows = LightShadows.None;       // 그림자는 폰에서 가장 비싼 것
                QualitySettings.shadowDistance = 0f; QualitySettings.pixelLightCount = 3; Application.targetFrameRate = 30; break;
            case Level.Mid:
                if (sun != null) { sun.shadows = LightShadows.Hard; sun.shadowStrength = 0.8f; }
                QualitySettings.shadowDistance = 25f; QualitySettings.pixelLightCount = 5; Application.targetFrameRate = 45; break;
            default: break;   // 높음: 기존 값 그대로(NightLights 가 40m·8개로 맞춘다)
        }
    }
}
