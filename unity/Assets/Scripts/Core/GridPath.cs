// =============================================================================
// GridPath.cs — 격자 길찾기(A*, 순수 C#, 테스트 가능). 봇이 장애물에 걸려 순간이동하지 않고 '여유 폭이 있는 길'로 걷게 한다.
//
// 입력: 아트가 만든 여유 폭 지도(nav_clearance_1m.png). 한 칸 = 1m, 값/20 = 그 칸의 여유 폭(m). 0 이면 막힘.
// 왜 A*? 직선으로만 가면 바위·물·절벽에 걸린다. A*(에이스타, 목적지까지 가장 싼 길을 찾는 방법)는 막힌 칸을 돌아 가는 길을 준다.
// 결과는 '꺾는 점(웨이포인트)' 목록 — 눈에 보이는 직선 구간은 합쳐서 점 수를 줄인다.
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public sealed class GridPath
    {
        readonly byte[] cell; readonly int w, h;   // cell[z*w+x] = 여유 폭×20 (0 = 막힘)
        public GridPath(byte[] cells, int width, int height) { cell = cells; w = width; h = height; }

        public int Width { get { return w; } }
        public int Height { get { return h; } }

        /// <summary>그 칸의 여유 폭(m). 지도 밖은 0</summary>
        public float Clearance(int x, int z) { return (x < 0 || z < 0 || x >= w || z >= h) ? 0f : cell[z * w + x] / 20f; }

        /// <summary>minClear 이상인 칸 중 (x,z)에서 가장 가까운 칸. 없으면 false</summary>
        public bool Nearest(float x, float z, float minClear, out int nx, out int nz)
        {
            int cx = (int)Math.Round(x), cz = (int)Math.Round(z); nx = cx; nz = cz;
            if (Clearance(cx, cz) >= minClear) return true;
            for (int r = 1; r <= 40; r++)
            {
                float best = float.MaxValue; bool found = false;
                for (int dz = -r; dz <= r; dz++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        if (Math.Max(Math.Abs(dx), Math.Abs(dz)) != r) continue;   // 이번 고리(바깥 테두리)만 본다
                        if (Clearance(cx + dx, cz + dz) < minClear) continue;
                        float d = dx * dx + dz * dz;
                        if (d < best) { best = d; nx = cx + dx; nz = cz + dz; found = true; }
                    }
                if (found) return true;
            }
            return false;
        }

        /// <summary>시작→끝 웨이포인트(좌표 m, 시작점 제외, 끝 포함). 길이 없으면 null.
        /// 여유 폭이 minClear 이상인 칸만 지난다(폭이 넓은 길일수록 싸게 쳐서 가운데로 걷게 한다).</summary>
        public List<float[]> Find(float sx, float sz, float gx, float gz, float minClear)
        {
            int s0x, s0z, g0x, g0z;
            if (!Nearest(sx, sz, minClear, out s0x, out s0z) || !Nearest(gx, gz, minClear, out g0x, out g0z)) return null;
            int start = s0z * w + s0x, goal = g0z * w + g0x;
            var g = new float[w * h]; var from = new int[w * h]; var closed = new bool[w * h];
            for (int i = 0; i < g.Length; i++) { g[i] = float.MaxValue; from[i] = -1; }
            var open = new SortedSet<KeyValuePair<float, int>>(new Cmp());
            g[start] = 0f; open.Add(new KeyValuePair<float, int>(H(s0x, s0z, g0x, g0z), start));
            while (open.Count > 0)
            {
                var top = open.Min; open.Remove(top); int cur = top.Value;
                if (cur == goal) break;
                if (closed[cur]) continue; closed[cur] = true;
                int cx = cur % w, cz = cur / w;
                for (int dz = -1; dz <= 1; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        if (dx == 0 && dz == 0) continue;
                        int nx = cx + dx, nz = cz + dz;
                        float c = Clearance(nx, nz); if (c < minClear) continue;
                        // 대각선으로 모서리를 베고 지나가지 않게: 옆 두 칸도 열려 있어야 한다
                        if (dx != 0 && dz != 0 && (Clearance(cx + dx, cz) < minClear || Clearance(cx, cz + dz) < minClear)) continue;
                        int ni = nz * w + nx; if (closed[ni]) continue;
                        float step = (dx != 0 && dz != 0 ? 1.4142f : 1f) * (c < 3f ? 1.6f : 1f);   // 좁은 칸은 조금 비싸게
                        float ng = g[cur] + step;
                        if (ng < g[ni]) { g[ni] = ng; from[ni] = cur; open.Add(new KeyValuePair<float, int>(ng + H(nx, nz, g0x, g0z), ni)); }
                    }
            }
            if (from[goal] < 0 && goal != start) return null;
            var cells = new List<int>(); for (int c = goal; c >= 0; c = from[c]) { cells.Add(c); if (c == start) break; }
            cells.Reverse();
            // 눈에 보이는 직선 구간은 합친다(끝점 위주로 남김)
            var pts = new List<float[]>(); int a = 0;
            while (a < cells.Count - 1)
            {
                int b = cells.Count - 1;
                while (b > a + 1 && !Clear(cells[a], cells[b], minClear)) b--;
                pts.Add(new float[] { cells[b] % w, cells[b] / w }); a = b;
            }
            if (pts.Count == 0) pts.Add(new float[] { g0x, g0z });
            return pts;
        }

        static float H(int x, int z, int gx, int gz) { float dx = x - gx, dz = z - gz; return (float)Math.Sqrt(dx * dx + dz * dz); }

        /// <summary>두 칸 사이 직선이 모두 열려 있는가</summary>
        bool Clear(int a, int b, float minClear)
        {
            int ax = a % w, az = a / w, bx = b % w, bz = b / w;
            int n = Math.Max(Math.Abs(bx - ax), Math.Abs(bz - az));
            for (int i = 1; i < n; i++) { float t = (float)i / n; if (Clearance((int)Math.Round(ax + (bx - ax) * t), (int)Math.Round(az + (bz - az) * t)) < minClear) return false; }
            return true;
        }

        sealed class Cmp : IComparer<KeyValuePair<float, int>>
        {
            public int Compare(KeyValuePair<float, int> x, KeyValuePair<float, int> y) { int c = x.Key.CompareTo(y.Key); return c != 0 ? c : x.Value.CompareTo(y.Value); }
        }
    }
}
