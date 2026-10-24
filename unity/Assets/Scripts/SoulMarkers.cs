// =============================================================================
// SoulMarkers.cs — 무릎 꿇은 혼 발밑의 '시간 고리' (2단계 처결의 긴장).
//
// 왜 필요한가?
//   무릎 꿇은 혼은 정해진 시간 안에 천도(E)나 파혼(R)으로 처결해야 한다. 안 하면 맺힘 일부를 되찾아 다시 일어선다.
//   "얼마나 남았지?"를 머리 위 작은 막대로만 보면 혼 무리 속에서 놓치기 쉽다.
//   그래서 발밑에 고리를 그려, 시간이 줄수록 고리가 조금씩 닫히게 한다(색 = 혼 종류, 25% 아래에서 깜박임).
//   천도 캐스팅 중(Sending)에는 시간이 멈춘 것이므로 고리를 흰색으로 고정해 보여 준다.
// 구현: 혼마다 LineRenderer(선을 그리는 부품) 하나. 안 쓰는 건 꺼 둔다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class SoulMarkers
{
    const int Segments = 40;          // 고리를 이루는 선분 수 (많을수록 둥글다)
    const float Radius = 0.9f;        // 고리 반지름(미터). 혼 몸 크기보다 약간 크게
    const float BlinkBelow = 0.25f;   // 남은 시간 비율이 이 아래면 깜박인다

    readonly Dictionary<Enemy, LineRenderer> rings = new Dictionary<Enemy, LineRenderer>();
    readonly List<Enemy> dead = new List<Enemy>();
    readonly Transform root;
    Material mat;

    public SoulMarkers(Transform parent)
    {
        root = new GameObject("SoulMarkers").transform;
        root.SetParent(parent, false);
    }

    /// <summary>매 프레임 불러 준다. 무릎 꿇거나 천도 받는 혼에게만 고리를 보인다</summary>
    public void Refresh(List<Enemy> list)
    {
        foreach (var e in list)
        {
            if (e == null) continue;
            bool show = e.kneeling || e.sending;
            LineRenderer lr;
            if (!rings.TryGetValue(e, out lr))
            {
                if (!show) continue;                 // 필요해질 때 만든다(안 꿇은 혼은 부품 낭비 없음)
                lr = Make(e); rings[e] = lr;
            }
            lr.enabled = show;
            if (!show) continue;

            float ratio = Mathf.Clamp01(e.soul.WaitLeft / Mathf.Max(0.01f, e.soul.WaitTotal));
            Color c = e.sending ? Color.white : Enemy.KindColor(e.soul.Kind);
            // 천도 중엔 시간이 멈췄으므로 가득 찬 고리, 아니면 남은 비율만큼만 그린다
            float shown = e.sending ? 1f : ratio;
            if (e.soul.Fuse > 0.05f) c = Color.Lerp(c, new Color(1f, 0.15f, 0.1f), 0.85f);   // 속임수 혼 도화선: 붉게 달아오른다 = 곧 덮친다(파혼하거나 물러나라)
            if (!e.sending && ratio < BlinkBelow && Mathf.Repeat(Time.unscaledTime * 6f, 1f) < 0.5f) c.a = 0.25f;   // 급하다 = 깜박
            lr.startColor = c; lr.endColor = c;
            int n = Mathf.Max(2, Mathf.CeilToInt(Segments * shown) + 1);
            lr.positionCount = n;
            float y = e.Pos.y + 0.06f;               // 바닥에 파묻히지 않게 살짝 띄운다
            for (int i = 0; i < n; i++)
            {
                // 위쪽(+z)에서 시작해 시계 방향으로 줄어든다
                float a = Mathf.PI * 0.5f - (float)i / Segments * Mathf.PI * 2f;
                lr.SetPosition(i, new Vector3(e.Pos.x + Mathf.Cos(a) * Radius, y, e.Pos.z + Mathf.Sin(a) * Radius));
            }
        }
        // 사라진 혼의 고리 정리
        dead.Clear();
        foreach (var kv in rings) if (kv.Key == null) dead.Add(kv.Key);
        foreach (var k in dead) { if (rings[k] != null) Object.Destroy(rings[k].gameObject); rings.Remove(k); }
    }

    LineRenderer Make(Enemy e)
    {
        if (mat == null) mat = U.Unlit(Color.white);
        var go = new GameObject("Ring"); go.transform.SetParent(root, false);
        var lr = go.AddComponent<LineRenderer>();
        lr.useWorldSpace = true;                      // 혼이 움직여도 매 프레임 좌표를 다시 준다
        lr.widthMultiplier = 0.09f;
        lr.sharedMaterial = mat;
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        lr.receiveShadows = false;
        return lr;
    }
}
