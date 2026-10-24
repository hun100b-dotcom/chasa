// =============================================================================
// MapLayout.cs — 솔고개 마을 지형의 '충돌 뼈대' (순수 C#). 집·장승 같은 막힌 곳을 원으로 적어 둔다.
// 원칙: 뼈대 지형은 손으로, 내부 배치(혼 위치)만 무작위 (Godot MapGen 과 같은 원칙).
// 왜 원(동그라미)? 쿼터뷰 액션에서 사각형 충돌보다 '미끄러지며 돌아가기'가 훨씬 자연스럽고 계산도 쉽다.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public struct Blocker
    {
        public float X, Z, R;
        public string Kind;   // "house" 집 / "post" 장승 / "fence" 돌무더기 — 화면에서 모양을 고르는 이름표
        public Blocker(string kind, float x, float z, float r) { Kind = kind; X = x; Z = z; R = r; }
    }

    public static class MapLayout
    {
        public const float HalfSize = 30f;          // 맵 한 변의 절반 (m). 60×60
        public static readonly Vector2f Shrine = new Vector2f(0f, 0f);   // 서낭당(출발·귀환점)

        /// <summary>솔고개 첫 밤 지형. 서낭당 중심에서 동쪽(+x)으로 길이 이어져 마을 어귀로 간다</summary>
        public static readonly List<Blocker> Blockers = BuildSolgogae();

        static List<Blocker> BuildSolgogae()
        {
            var b = new List<Blocker>();
            // 장승 한 쌍: 귀환 반경(SHRINE_RADIUS) 가장자리에 세워, 그 사이로 들어서면 귀환이 되게 한다 (서사 확정)
            b.Add(new Blocker("post", Balance.SHRINE_RADIUS, -1.6f, 0.4f));
            b.Add(new Blocker("post", Balance.SHRINE_RADIUS, 1.6f, 0.4f));
            // 마을 집들: 길(z≈0, +x 방향)을 비워 두고 위·아래로 늘어놓는다
            float[] xs = { 9f, 16f, 23f };
            foreach (float x in xs)
            {
                b.Add(new Blocker("house", x, -6.5f, 2.2f));
                b.Add(new Blocker("house", x + 1.5f, 6.5f, 2.2f));
            }
            // 서낭당 둘레 돌무더기 (길 반대편, 뒤쪽을 막아 '여기가 시작점'이라는 느낌)
            b.Add(new Blocker("fence", -5f, -3f, 0.9f));
            b.Add(new Blocker("fence", -5.5f, 0.5f, 0.9f));
            b.Add(new Blocker("fence", -5f, 4f, 0.9f));
            // 먼 쪽 서쪽·남북 외곽의 큰 바위
            b.Add(new Blocker("house", -16f, -12f, 3f));
            b.Add(new Blocker("house", -14f, 13f, 3f));
            return b;
        }

        /// <summary>
        /// 반지름 radius 인 몸이 (x,z) 에 있을 때 막힌 곳과 겹치면 바깥으로 밀어낸다. 맵 경계도 지킨다.
        /// 한 번에 가장 깊이 겹친 것부터 두 번 돌려 모서리에 끼는 일을 줄인다.
        /// </summary>
        public static void PushOut(ref float x, ref float z, float radius)
        {
            for (int pass = 0; pass < 2; pass++)
                foreach (var o in Blockers)
                {
                    float dx = x - o.X, dz = z - o.Z;
                    float min = o.R + radius;
                    float d2 = dx * dx + dz * dz;
                    if (d2 >= min * min) continue;
                    float d = (float)System.Math.Sqrt(d2);
                    if (d < 1e-4f) { dx = 1f; dz = 0f; d = 1f; }   // 정확히 중심이면 +x 로 밀어낸다
                    x = o.X + dx / d * min;
                    z = o.Z + dz / d * min;
                }
            float lim = HalfSize - radius;
            x = System.Math.Max(-lim, System.Math.Min(lim, x));
            z = System.Math.Max(-lim, System.Math.Min(lim, z));
        }

        /// <summary>점 (x,z) 가 막힌 곳 안인가 (혼이 집 안에서 태어나지 않게 검사용)</summary>
        public static bool IsBlocked(float x, float z, float radius)
        {
            foreach (var o in Blockers)
            {
                float dx = x - o.X, dz = z - o.Z, min = o.R + radius;
                if (dx * dx + dz * dz < min * min) return true;
            }
            return false;
        }
    }

    /// <summary>Core 는 UnityEngine 을 쓰지 않으므로 아주 작은 2차원 값 하나를 따로 둔다</summary>
    public struct Vector2f { public float X, Z; public Vector2f(float x, float z) { X = x; Z = z; } }
}
