// =============================================================================
// HitFeel.cs — 히트스톱(순간 정지) + 화면 흔들림 (Godot판 hit_feel.gd)
// =============================================================================
using UnityEngine;

public class HitFeel
{
    float hitStopTimer; // 남은 정지 시간(초)
    float shake;        // 흔들림 세기(0~1)
    float zoom;         // 줌 펀치(-1~1): + 이면 화면이 확 다가갔다 돌아오고, − 이면 멀어졌다 돌아온다
    Vector3 kick;       // 맞은 방향으로 카메라가 툭 밀렸다 돌아오는 정도(세계 좌표, m)

    /// <summary>타격 순간 화면이 다가가는 '쿵'. 세기 1 = 화면 크기 약 6%</summary>
    public void AddZoom(float strength) => zoom = Mathf.Clamp(zoom + strength, -1f, 1f);

    /// <summary>때린 방향으로 카메라를 밀어 준다(방향 있는 충격). 세계 좌표 방향 × 세기(m)</summary>
    public void AddKick(Vector3 worldDir, float meters) { kick += new Vector3(worldDir.x, 0, worldDir.z).normalized * meters; if (kick.magnitude > 0.9f) kick = kick.normalized * 0.9f; }

    public float Zoom => zoom;
    public Vector3 Kick => kick;

    /// <summary>여러 마리를 동시에 때려도 정지가 합쳐지지 않게, 가장 긴 것 하나만</summary>
    public void HitStop(int frames) => hitStopTimer = Mathf.Max(hitStopTimer, frames * Config.FEEL_FRAME_TIME);

    public void AddShake(float strength) => shake = Mathf.Clamp01(Mathf.Max(shake, strength));

    /// <summary>true = 지금 정지 중. 정지 중에도 흔들림은 줄어든다(멈춘 화면이 부르르 = 손맛 핵심)</summary>
    public bool Tick(float realDt)
    {
        shake = Mathf.Max(0f, shake - Config.FEEL_SHAKE_DECAY * realDt);
        zoom = Mathf.MoveTowards(zoom, 0f, 6f * realDt);   // 0.15초 안팎에 제자리
        kick *= Mathf.Exp(-12f * realDt);                  // 빠르게 되돌아온다(스프링 느낌)
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
