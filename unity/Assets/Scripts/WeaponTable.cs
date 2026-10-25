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

    // 요령방울: 10/10/20 에서 12/12/24 로 올림(10-25 시뮬: 단일 목표 약 70%여야 파혼만으로 1호 보스를 눕힘). 적 3마리 이상일 때 총 피해가 큼. 360° 원 범위, 짧고 빠르다 (임시값)
    public static readonly ComboStep[] Bell =
    {
        new ComboStep { name = "1 ring", damage = 12, reach = 2.6f, sweepDeg = 360f, startOffsetDeg = 30f, dir = 1,
            windup = 0.12f, swing = 0.2f, recover = 0.2f, hitStopFrames = 3, shake = 0.35f, knockback = 9f, stun = 0.3f, lunge = 0f },
        new ComboStep { name = "2 ring", damage = 12, reach = 2.6f, sweepDeg = 360f, startOffsetDeg = 30f, dir = -1,
            windup = 0.12f, swing = 0.2f, recover = 0.2f, hitStopFrames = 3, shake = 0.35f, knockback = 9f, stun = 0.3f, lunge = 0f },
        new ComboStep { name = "3 toll", damage = 24, reach = 3.0f, sweepDeg = 360f, startOffsetDeg = 30f, dir = 1,
            windup = 0.22f, swing = 0.24f, recover = 0.4f, hitStopFrames = 6, shake = 0.8f, knockback = 14f, stun = 0.9f, lunge = 0f },
    };

    // 삼지창: 기획 13/14/24, 관통 3 (WeaponDef.MaxHits). 좁고 긴 찌르기
    public static readonly ComboStep[] Trident =
    {
        new ComboStep { name = "1 thrust", damage = 13, reach = 4.4f, sweepDeg = 24f, startOffsetDeg = 12f, dir = -1,
            windup = 0.16f, swing = 0.12f, recover = 0.22f, hitStopFrames = 3, shake = 0.45f, knockback = 11f, stun = 0.35f, lunge = 1.0f },
        new ComboStep { name = "2 thrust", damage = 14, reach = 4.4f, sweepDeg = 24f, startOffsetDeg = 12f, dir = -1,
            windup = 0.16f, swing = 0.12f, recover = 0.22f, hitStopFrames = 3, shake = 0.5f, knockback = 12f, stun = 0.4f, lunge = 1.0f },
        new ComboStep { name = "3 skewer", damage = 24, reach = 4.8f, sweepDeg = 24f, startOffsetDeg = 12f, dir = -1,
            windup = 0.26f, swing = 0.14f, recover = 0.42f, hitStopFrames = 6, shake = 0.9f, knockback = 17f, stun = 0.9f, lunge = 1.4f },
    };

    // 명부 붓: 기획 10/10/18, 투사체. 지금은 좁고 긴 휘두름으로 대신(실제 투사체는 다음 단계)
    public static readonly ComboStep[] Brush =
    {
        new ComboStep { name = "1 stroke", damage = 10, reach = 6.0f, sweepDeg = 14f, startOffsetDeg = 7f, dir = 1,
            windup = 0.14f, swing = 0.1f, recover = 0.2f, hitStopFrames = 1, shake = 0.25f, knockback = 6f, stun = 0.25f, lunge = 0f },
        new ComboStep { name = "2 stroke", damage = 10, reach = 6.0f, sweepDeg = 14f, startOffsetDeg = 7f, dir = -1,
            windup = 0.14f, swing = 0.1f, recover = 0.2f, hitStopFrames = 1, shake = 0.25f, knockback = 6f, stun = 0.25f, lunge = 0f },
        new ComboStep { name = "3 seal", damage = 18, reach = 6.5f, sweepDeg = 14f, startOffsetDeg = 7f, dir = 1,
            windup = 0.24f, swing = 0.12f, recover = 0.38f, hitStopFrames = 4, shake = 0.6f, knockback = 10f, stun = 0.7f, lunge = 0f },
    };

    public static ComboStep[] Steps(WeaponId id)
    {
        switch (id)
        {
            case WeaponId.Mace: return Mace;
            case WeaponId.Bell: return Bell;
            case WeaponId.Trident: return Trident;
            case WeaponId.Brush: return Brush;
            default: return Config.COMBO;
        }
    }
}
