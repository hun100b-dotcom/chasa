// =============================================================================
// PullPoints.cs — '사슬로 낚아챌 수 있는 자리'(보스 약점). 적이 아니라 땅 위의 한 점이라 Player 의 견인이 적을 못 찾아도
// 이 점을 겨누면 사슬이 거기까지 날아가 닿고, 닿는 순간 onPull 이 불린다.
// 예) B-09 아낙이 던지려는 남편의 옷(2초 창), B-12 큰물 속 횃불, B-05 땅에 꽂힌 깃발.
// 왜 따로? 견인은 원래 'Enemy 를 끌어오는' 기능이라 적 아닌 대상을 받을 자리가 없었다. 점 하나를 등록해 두면 되게 해서
// 보스마다 코드를 Player 에 심지 않는다. 마우스는 점 근처를, 터치(커서 없음)는 점이 있으면 보스 대신 그 점을 잡는다.
// =============================================================================
using System;
using System.Collections.Generic;
using UnityEngine;

public class PullPoint
{
    public Vector3 pos;
    public float radius = 2.5f;      // 이 안을 겨누면 잡는다(m)
    public Action onPull;            // 사슬이 닿았을 때
    public bool active = true;
}

public static class PullPoints
{
    static readonly List<PullPoint> list = new List<PullPoint>();

    public static PullPoint Add(Vector3 pos, float radius, Action onPull)
    {
        var p = new PullPoint { pos = pos, radius = radius, onPull = onPull }; list.Add(p); return p;
    }
    public static void Remove(PullPoint p) { if (p != null) { p.active = false; list.Remove(p); } }
    public static void Clear() { list.Clear(); }

    /// <summary>
    /// 겨눈 자리(aim)·잡힌 적(targetPos, 없으면 null)·플레이어(from) 로 잡을 점을 고른다. range 밖이면 못 잡는다.
    /// 규칙: aim 이 점 반경 안이거나, 겨눈 적이 점 바로 옆(보스가 손에 든 물건)이면 그 점이 우선한다.
    /// </summary>
    public static PullPoint Pick(Vector3 aim, Vector3? targetPos, Vector3 from, float range)
    {
        PullPoint best = null; float bd = float.MaxValue;
        foreach (var p in list)
        {
            if (!p.active || Flat(p.pos, from) > range) continue;
            float da = Flat(p.pos, aim);
            bool touch = Flat(aim, from) < 0.3f;   // 터치는 커서가 없어 aim 이 플레이어 자리 → 사거리 안 점은 다 겨눈 것으로 본다
            bool aimed = touch || da <= p.radius + 1f || (targetPos.HasValue && Flat(p.pos, targetPos.Value) <= p.radius + 1.5f);
            if (aimed && da < bd) { bd = da; best = p; }
        }
        return best;
    }
    static float Flat(Vector3 a, Vector3 b) { float dx = a.x - b.x, dz = a.z - b.z; return Mathf.Sqrt(dx * dx + dz * dz); }
}
