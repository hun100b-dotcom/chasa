// =============================================================================
// EdgeWarn.cs — 화면 가장자리 경고 계산 (순수 C#, 테스트 가능).
//
// 왜 필요한가? (2단계 처결의 긴장)
//   천도를 외는 동안 시야가 좁아진다(원 모양으로 어두워짐). 그 바깥에서 적이 덮쳐 와도 안 보이면
//   "억울하게 맞았다"가 된다. 그래서 '예비동작을 시작한 적'이 시야 밖에 있으면
//   시야 가장자리에 빨간 표시를 띄워 방향을 알려 준다 → 천도하다 맞는 건 내 선택의 결과가 된다.
// 좌표: 화면 픽셀, 원점은 왼쪽 위(UI 좌표). 화면 가운데에서 적 쪽으로 쏜 선을 따라 표시 위치를 잡는다.
// =============================================================================
using System;

namespace Chasa.Core
{
    public static class EdgeWarn
    {
        /// <summary>
        /// 적(sx,sy)이 '보이는 범위' 밖이면 true 와 함께 표시 위치(ex,ey)를 낸다.
        /// 보이는 범위 = 화면 사각형(여백 margin 안쪽)과 시야 원(반지름 visionRadius) 중 더 좁은 쪽.
        /// visionRadius 가 0 이하이면 시야 원은 쓰지 않는다(평소엔 화면 밖일 때만 경고).
        /// </summary>
        public static bool Compute(float sx, float sy, float w, float h, float margin, float visionRadius,
                                   out float ex, out float ey)
        {
            float cx = w * 0.5f, cy = h * 0.5f;
            float dx = sx - cx, dy = sy - cy;
            float dist = (float)Math.Sqrt(dx * dx + dy * dy);
            ex = cx; ey = cy;
            if (dist < 0.001f) return false;                       // 정확히 가운데: 항상 보임
            float ux = dx / dist, uy = dy / dist;

            // 사각형 안쪽 경계까지의 거리: 가로·세로 중 먼저 닿는 쪽
            float halfW = Math.Max(1f, cx - margin), halfH = Math.Max(1f, cy - margin);
            float tx = Math.Abs(ux) < 1e-5f ? float.MaxValue : halfW / Math.Abs(ux);
            float ty = Math.Abs(uy) < 1e-5f ? float.MaxValue : halfH / Math.Abs(uy);
            float limit = Math.Min(tx, ty);
            if (visionRadius > 0f) limit = Math.Min(limit, Math.Max(margin, visionRadius - margin));

            if (dist <= limit) return false;                       // 보이는 범위 안 → 표시 불필요
            ex = cx + ux * limit; ey = cy + uy * limit;
            return true;
        }

        /// <summary>시야 원 반지름(픽셀). 평소 diag*0.625 → 천도 중 비율만큼 좁아진다. p = 0(평소)~1(캐스팅)</summary>
        public static float VisionRadius(float diag, float ratio, float p)
        {
            float r0 = diag * 0.625f;
            return p <= 0.001f ? 0f : r0 + (r0 * ratio - r0) * Math.Min(1f, p);
        }
    }

    /// <summary>화면 가장자리에 띄울 경고 하나 (위치는 화면 비율 0~1, 왼쪽 위 기준)</summary>
    public struct EdgeMark { public float Nx, Ny; }
}
