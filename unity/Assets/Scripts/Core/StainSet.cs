// =============================================================================
// StainSet.cs — 원념 얼룩 모음 (순수 C#, P-007~P-011)
// 파혼한 자리에 남는 얼룩. 3개가 겹치면 그 자리에서 사나운 적이 소환된다.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public class StainSet
    {
        class Stain { public float X, Z, Age, Scale = 1f; }
        readonly List<Stain> _items = new List<Stain>();

        public int Count { get { return _items.Count; } }

        /// <summary>화면에 그릴 때 쓰는 읽기 전용 목록 (x, z, 남은 시간 비율 0~1)</summary>
        public List<float[]> Snapshot()
        {
            var list = new List<float[]>();
            foreach (var it in _items)
                list.Add(new[] { it.X, it.Z, 1f - it.Age / Balance.STAIN_DURATION, it.Scale });
            return list;
        }

        /// <summary>
        /// 얼룩 하나 추가. 겹친 얼룩(중심 거리 < 반경×2)이 3개 이상이 되면 그것들을 지우고 가운데 지점을 돌려준다.
        /// 소환이 아니면 false.
        /// </summary>
        public bool Add(float x, float z, out float centerX, out float centerZ, float scale = 1f, bool allowSummon = true)
        {
            var s = new Stain { X = x, Z = z, Scale = scale };
            _items.Add(s);
            if (!allowSummon) { centerX = centerZ = 0f; return false; }   // 낮: 얼룩은 남지만 겹쳐도 사나운 적이 소환되지 않는다(FK3)
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

        /// <summary>(x,z) 둘레 r 안의 얼룩 수 — '원념 짙은 구역' 판정용</summary>
        public int CountWithin(float x, float z, float r)
        {
            int n = 0;
            foreach (var it in _items) { float dx = x - it.X, dz = z - it.Z; if (dx * dx + dz * dz <= r * r) n++; }
            return n;
        }

        /// <summary>얼룩이 물에 떠서 (cx,cz) 쪽으로 흘러간다(나루 영감 ② 큰물). maxDist 안의 얼룩만, 도착하면 멈춘다</summary>
        public void DriftToward(float cx, float cz, float speed, float dt, float maxDist, float stopR = 1.5f)
        {
            foreach (var it in _items)
            {
                float dx = cx - it.X, dz = cz - it.Z, d = (float)System.Math.Sqrt(dx * dx + dz * dz);
                if (d > maxDist || d < stopR) continue;   // 영감 4m 앞에서 멈춘다(기획 B01_DRIFT_STOP_R): 얼룩이 영감 발밑까지 몰리지 않게
                it.X += dx / d * speed * dt; it.Z += dz / d * speed * dt;
            }
        }

        /// <summary>얼룩 위에 서 있는가 (이동속도 -20%)</summary>
        public bool IsOnStain(float x, float z)
        {
            foreach (var it in _items)
            {
                float dx = x - it.X, dz = z - it.Z;
                if (System.Math.Sqrt(dx * dx + dz * dz) <= Balance.STAIN_RADIUS * it.Scale) return true;
            }
            return false;
        }

        /// <summary>시간이 흐른다. 지속 시간(15초)이 지난 얼룩은 사라진다</summary>
        public float DurationMult = 1f;   // 얼룩 지속 배율(마른 얼룩: 0.85/0.7). 작을수록 빨리 사라진다

        public void Tick(float dt)
        {
            dt /= System.Math.Max(0.1f, DurationMult);   // 지속이 짧아지는 것 = 나이가 더 빨리 든다
            for (int i = _items.Count - 1; i >= 0; i--)
            {
                _items[i].Age += dt;
                if (_items[i].Age >= Balance.STAIN_DURATION) _items.RemoveAt(i);
            }
        }

        /// <summary>
        /// (x,z) 에서 range 안의 가장 가까운 얼룩 하나를 지우고 그 중심을 돌려준다 (도술 '터뜨리기').
        /// 얼룩을 지우는 유일한 방법이며, 업은 건드리지 않는다. 없으면 false.
        /// </summary>
        public bool RemoveNearest(float x, float z, float range, out float outX, out float outZ)
        {
            Stain best = null; float bestD = range;
            foreach (var it in _items)
            {
                float d = (float)System.Math.Sqrt((it.X - x) * (it.X - x) + (it.Z - z) * (it.Z - z));
                if (d <= bestD) { bestD = d; best = it; }
            }
            outX = outZ = 0f;
            if (best == null) return false;
            outX = best.X; outZ = best.Z;
            _items.Remove(best);
            return true;
        }

        public void Clear() { _items.Clear(); }
    }
}
