// =============================================================================
// HitFeel.cs — 히트스톱(순간 정지) + 화면 흔들림 (Godot판 hit_feel.gd)
// =============================================================================
using UnityEngine;

public class HitFeel
{
    float hitStopTimer; // 남은 정지 시간(초)
    float shake;        // 흔들림 세기(0~1)

    /// <summary>여러 마리를 동시에 때려도 정지가 합쳐지지 않게, 가장 긴 것 하나만</summary>
    public void HitStop(int frames) => hitStopTimer = Mathf.Max(hitStopTimer, frames * Config.FEEL_FRAME_TIME);

    public void AddShake(float strength) => shake = Mathf.Clamp01(Mathf.Max(shake, strength));

    /// <summary>true = 지금 정지 중. 정지 중에도 흔들림은 줄어든다(멈춘 화면이 부르르 = 손맛 핵심)</summary>
    public bool Tick(float realDt)
    {
        shake = Mathf.Max(0f, shake - Config.FEEL_SHAKE_DECAY * realDt);
        if (hitStopTimer > 1e-4f) // 오차로 2프레임이 3프레임 되는 것 방지
        {
            hitStopTimer -= realDt;
            return true;
        }
        hitStopTimer = 0f;
        return false;
    }

    /// <summary>이번 프레임 카메라 흔들림 (화면 기준 좌우 x, 상하 y)</summary>
    public Vector2 GetShakeOffset()
    {
        if (shake <= 0f) return Vector2.zero;
        float amp = Config.FEEL_SHAKE_MAX_OFFSET * shake;
        float a = Random.value * U.TAU; // 매 프레임 무작위 방향 → '지잉~'
        return new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * amp;
    }
}
