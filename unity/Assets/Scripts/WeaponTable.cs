// =============================================================================
// WeaponTable.cs — 무기별 콤보 '모션 값' 표 (Unity 쪽). 처결에 관한 성격은 Core/Gear.cs 의 WeaponDef.
// 왜 둘로 나눴나? 화면 값(각도·시간)은 손맛을 보며 자주 바뀌고, 처결 성격(넉백·피해 배율)은 밸런스 값이라서.
// 새 무기는 WeaponId 에 추가하고 여기 한 줄을 더하면 된다.
// =============================================================================
using Chasa.Core;

public static class WeaponTable
{
    // 육모방망이: 초당 피해 지수 ≈ 철삭의 91%(기획 90, QA 시뮬로 16/18/34로 맞춤) · 근접(3.2m) · 느리고 한 방이 크다 · 3타째는 반경 3m 내려찍기, 기절 1.2초 (기획서 6-2, 임시값)
    public static readonly ComboStep[] Mace =
    {
        new ComboStep { name = "1 swing", damage = 16, reach = 3.2f, sweepDeg = 110f, startOffsetDeg = 55f, dir = 1,
            windup = 0.16f, swing = 0.18f, recover = 0.22f, hitStopFrames = 3, shake = 0.5f, knockback = 12f, stun = 0.4f, lunge = 0.7f },
        new ComboStep { name = "2 swing", damage = 18, reach = 3.2f, sweepDeg = 110f, startOffsetDeg = 55f, dir = -1,
            windup = 0.16f, swing = 0.18f, recover = 0.22f, hitStopFrames = 3, shake = 0.55f, knockback = 13f, stun = 0.45f, lunge = 0.7f },
        new ComboStep { name = "3 slam", damage = 34, reach = 3.0f, sweepDeg = 360f, startOffsetDeg = 35f, dir = 1,
            windup = 0.28f, swing = 0.22f, recover = 0.45f, hitStopFrames = 6, shake = 1.0f, knockback = 18f, stun = 1.2f, lunge = 0f },
    };

    public static ComboStep[] Steps(WeaponId id) { return id == WeaponId.Mace ? Mace : Config.COMBO; }
}
