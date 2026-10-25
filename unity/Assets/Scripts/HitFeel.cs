// =============================================================================
// HitFeel.cs — 히트스톱(순간 정지) + 화면 흔들림 (Godot판 hit_feel.gd)
// =============================================================================
using UnityEngine;

public class HitFeel
{
    float hitStopTimer; // 남은 정지 시간(초)
    float shake;        // 충격값 trauma(0~1). 실제 흔들림은 이 값의 제곱 → 작은 타는 거의 안 흔들리고 큰 타만 확 흔들린다
    float slowT, slowScale = 1f;   // 천도 완료 슬로모: 남은 시간(초)과 속도 배율
    float noiseT;       // 흔들림 잡음 시계(초)
    float zoom;         // 줌 펀치(-1~1): + 이면 화면이 확 다가갔다 돌아오고, − 이면 멀어졌다 돌아온다
    Vector3 kick;       // 맞은 방향으로 카메라가 툭 밀렸다 돌아오는 정도(세계 좌표, m)

    /// <summary>타격 순간 화면이 다가가는 '쿵'. 세기 1 = 화면 크기 약 6%</summary>
    public void AddZoom(float strength) => zoom = Mathf.Clamp(zoom + strength, -1f, 1f);

    /// <summary>때린 방향으로 카메라를 밀어 준다(방향 있는 충격). 세계 좌표 방향 × 세기(m)</summary>
    public void AddKick(Vector3 worldDir, float meters) { kick += new Vector3(worldDir.x, 0, worldDir.z).normalized * meters; if (kick.magnitude > 0.9f) kick = kick.normalized * 0.9f; }

    /// <summary>시간이 느려진다(정지가 아니라 느림). 천도 완료처럼 '보내는' 순간에 쓴다</summary>
    public void SlowMo(float seconds, float scale) { slowT = Mathf.Max(slowT, seconds); slowScale = scale; }
    /// <summary>게임 세계 시간 배율 (슬로모 중 < 1)</summary>
    public float TimeScale => slowT > 0f ? slowScale : 1f;

    public float Zoom => zoom;
    public Vector3 Kick => kick;

    /// <summary>여러 마리를 동시에 때려도 정지가 합쳐지지 않게, 가장 긴 것 하나만</summary>
    public void HitStop(int frames) => hitStopTimer = Mathf.Max(hitStopTimer, Mathf.Min(frames, Balance.HITSTOP_CAP_FRAMES) * Config.FEEL_FRAME_TIME);   // 상한: 연속 정지로 게임이 끊겨 보이는 것 방지

    public void AddShake(float strength) => shake = Mathf.Clamp01(Mathf.Max(shake, strength));

    /// <summary>true = 지금 정지 중. 정지 중에도 흔들림은 줄어든다(멈춘 화면이 부르르 = 손맛 핵심)</summary>
    public bool Tick(float realDt)
    {
        shake = Mathf.Max(0f, shake - Config.FEEL_SHAKE_DECAY * realDt);
        noiseT += realDt;
        if (slowT > 0f) slowT = Mathf.Max(0f, slowT - realDt);   // 슬로모 시간은 진짜 시간으로 센다(안 그러면 두 배 오래 간다)
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

    /// <summary>실제 흔들림 세기 = 충격값². 폰은 작은 화면이라 줄인다</summary>
    float Amount() => shake * shake * (Ko.TouchUI ? Balance.SHAKE_MOBILE_MULT : 1f) * SaveStore.Settings.Shake;   // 설정의 화면 흔들림 세기(0이면 안 흔들림)

    /// <summary>
    /// 이번 프레임 카메라 흔들림 (화면 기준 좌우 x, 상하 y).
    /// 왜 펄린 노이즈? 매 프레임 완전 무작위면 '지글지글'거린다. 부드럽게 이어지는 잡음을 22Hz 로 훑으면 '묵직하게 흔들'린다.
    /// </summary>
    public Vector2 GetShakeOffset()
    {
        float amp = Config.FEEL_SHAKE_MAX_OFFSET * Amount();
        if (amp <= 0f) return Vector2.zero;
        float t = noiseT * Balance.SHAKE_NOISE_FREQ;
        return new Vector2(Mathf.PerlinNoise(t, 0.37f) * 2f - 1f, Mathf.PerlinNoise(t, 7.91f) * 2f - 1f) * amp;
    }

    /// <summary>화면 기울기(도). 위치 흔들림보다 덜 어지럽고 더 묵직하다</summary>
    public float GetShakeRoll()
    {
        float amp = Balance.SHAKE_MAX_ROLL_DEG * Amount();
        return amp <= 0f ? 0f : (Mathf.PerlinNoise(noiseT * Balance.SHAKE_NOISE_FREQ, 15.3f) * 2f - 1f) * amp;
    }
}
