// =============================================================================
// U.cs — 작은 수학 도구 + 재질 만들기 (Godot판 util.gd 와 같은 동작)
// =============================================================================
using UnityEngine;

public static class U
{
    public const float TAU = Mathf.PI * 2f;

    public static float EaseOutQuad(float t) => 1f - (1f - t) * (1f - t); // 확 뻗고 끝에서 감속
    public static float EaseInQuad(float t) => t * t;                    // 천천히 시작해 빨라짐

    /// <summary>각도를 -π ~ +π 로 정리</summary>
    public static float WrapPi(float a)
    {
        a = (a + Mathf.PI) % TAU;
        if (a < 0f) a += TAU;
        return a - Mathf.PI;
    }

    /// <summary>a 에서 b 로 가까운 쪽으로 최대 maxStep 만큼 돈다</summary>
    public static float TurnToward(float a, float b, float maxStep)
    {
        float diff = WrapPi(b - a);
        if (Mathf.Abs(diff) <= maxStep) return b;
        return a + Mathf.Sign(diff) * maxStep;
    }

    /// <summary>
    /// 사슬 끝이 prev→cur 각도로 훑는 동안 target 각도의 적을 스쳤나?
    /// 프레임 사이 구간 전체를 검사해야 "보이는 사슬이 스치는 순간"에 맞는다.
    /// </summary>
    public static bool SweptThrough(float prev, float cur, float target, float halfWidth)
    {
        float delta = cur - prev;
        if (delta == 0f) return false;
        float s = Mathf.Sign(delta);
        float from = prev - s * halfWidth;
        float len = Mathf.Abs(delta) + halfWidth * 2f;
        float d = (target - from) * s;
        d = ((d % TAU) + TAU) % TAU;
        return d <= len;
    }

    /// <summary>바닥 평면(x,z) 각도 → 방향 벡터</summary>
    public static Vector3 Dir(float angle) => new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle));

    // ---- 재질 ----------------------------------------------------------------
    // 셰이더는 빌드에 꼭 포함되도록 BuildScript 가 Resources/Mats 에 재질 파일로 미리 만들어 둔다.
    // 여기서는 그 재질을 복사해 색만 바꿔 쓴다. (Shader.Find 만 쓰면 웹 빌드에서 셰이더가 빠질 수 있다)
    static Material Base(string name)
    {
        var m = Resources.Load<Material>("Mats/" + name);
        return m != null ? new Material(m) : new Material(Shader.Find("Standard"));
    }

    /// <summary>무광 재질 (조명 받음)</summary>
    public static Material Matte(Color c)
    {
        var m = Base("Matte");
        m.color = c;
        return m;
    }

    /// <summary>맞으면 하얗게 번쩍일 수 있는 무광 재질 (적 전용)</summary>
    public static Material Flashable(Color c)
    {
        var m = Base("Flash");
        m.color = c;
        m.SetColor("_EmissionColor", Color.black);
        return m;
    }

    /// <summary>조명 영향 없이 색 그대로 (사슬처럼 빛나는 물체)</summary>
    public static Material Unlit(Color c)
    {
        var m = Base("Unlit");
        m.color = c;
        return m;
    }

    /// <summary>정점 색 + 투명 (격자선, 클릭 링)</summary>
    public static Material VertexColor() => Base("VertexColor");

    /// <summary>정점 색 + 더하기 합성 (빛처럼 겹칠수록 밝아짐 — 사슬 잔상)</summary>
    public static Material Additive() => Base("Additive");
}
