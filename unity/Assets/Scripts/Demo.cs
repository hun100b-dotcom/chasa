using Chasa.Core;

/// <summary>
/// 시연판 기능 켜고 끄기. 값의 원본은 balance.json 의 DEMO_*. 코드는 남기고 끄기만 한다(격차 분석 결과: 처음 5분은 철삭 + 천도/파혼 선택에 집중).
/// 왜 상수를 바로 안 쓰고 속성으로 감싸나? 상수 false 를 if 에 쓰면 '도달 못 하는 코드' 경고가 수십 개 생기기 때문.
/// </summary>
public static class Demo
{
    public static bool Weapons { get { return Balance.DEMO_WEAPONS; } }   // Tab 무기 교체
    public static bool Skills { get { return Balance.DEMO_SKILLS; } }     // 도술 1/2/3
    public static bool Gear { get { return Balance.DEMO_GEAR; } }         // 장비 드롭·장착
    public static bool Day { get { return Balance.DEMO_DAY; } }           // 낮 화면·서낭당
    public static bool Panel { get { return Balance.DEMO_PANEL; } }       // C 캐릭터 창
}
