// =============================================================================
// ZoneRules.cs — 필드 구역(마을·보릿들·검은여울…) 판정 (순수 C#, 테스트 가능).
// 안개처럼 구역마다 다른 분위기를 줄 때, '지금 서 있는 곳이 어느 구역인가'만 여기서 정한다.
// 구역이 겹치면 목록에서 먼저 나온 것이 이긴다(좁고 특별한 구역을 앞에 두면 된다).
// =============================================================================
namespace Chasa.Core
{
    public struct ZoneRect
    {
        public float X0, Z0, X1, Z1;
        public bool Contains(float x, float z) { return x >= X0 && x <= X1 && z >= Z0 && z <= Z1; }
    }

    public static class ZoneRules
    {
        /// <summary>(x,z)가 들어 있는 첫 구역 번호. 어느 구역도 아니면 -1</summary>
        public static int Find(ZoneRect[] zones, float x, float z)
        {
            for (int i = 0; i < zones.Length; i++) if (zones[i].Contains(x, z)) return i;
            return -1;
        }
    }
}
