// =============================================================================
// StainSet.cs — 원념 얼룩 모음 (순수 C#, P-007~P-011)
// 파혼한 자리에 남는 얼룩. 3개가 겹치면 그 자리에서 사나운 적이 소환된다.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public class StainSet
    {
        class Stain { public float X, Z, Age; }
        readonly List<Stain> _items = new List<Stain>();

        public int Count { get { return _items.Count; } }

        /// <summary>
        /// 얼룩 하나 추가. 겹친 얼룩(중심 거리 < 반경×2)이 3개 이상이 되면 그것들을 지우고 가운데 지점을 돌려준다.
        /// 소환이 아니면 false.
        /// </summary>
        public bool Add(float x, float z, out float centerX, out float centerZ)
        {
            var s = new Stain { X = x, Z = z };
            _items.Add(s);
            float limit = Balance.STAIN_RADIUS * 2f;
            var group = new List<Stain>();
            foreach (var it in _items)
            {
                float dx = it.X - s.X, dz = it.Z - s.Z;
                if (System.Math.Sqrt(dx * dx + dz * dz) < limit) group.Add(it);
            }
            centerX = centerZ = 0f;
            if (group.Count < Balance.STAIN_SUMMON_COUNT) return false;
            foreach (var it in group) { centerX += it.X; centerZ += it.Z; _items.Remove(it); }
            centerX /= group.Count;
            centerZ /= group.Count;
            return true;
        }

        /// <summary>얼룩 위에 서 있는가 (이동속도 -20%)</summary>
        public bool IsOnStain(float x, float z)
        {
            foreach (var it in _items)
            {
                float dx = x - it.X, dz = z - it.Z;
                if (System.Math.Sqrt(dx * dx + dz * dz) <= Balance.STAIN_RADIUS) return true;
            }
            return false;
        }

        /// <summary>시간이 흐른다. 지속 시간(15초)이 지난 얼룩은 사라진다</summary>
        public void Tick(float dt)
        {
            for (int i = _items.Count - 1; i >= 0; i--)
            {
                _items[i].Age += dt;
                if (_items[i].Age >= Balance.STAIN_DURATION) _items.RemoveAt(i);
            }
        }

        public void Clear() { _items.Clear(); }
    }
}
