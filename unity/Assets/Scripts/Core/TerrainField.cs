// =============================================================================
// TerrainField.cs — 높낮이 지도(하이트맵)와 재질 섞기 지도(스플랫맵)의 규칙 (순수 C#, 유니티 없이 테스트됨)
// 아트팀이 새 땅을 만들어 주면 이 두 지도로 땅을 입힌다. 땅 위 모든 것(주인공·적·NPC·소품)이 HeightField.At(x,z) 로 높이를 묻는다.
// 좌표: 월드 x,z (미터). 지도는 0..Size 를 덮고, 칸 사이는 부드럽게 이어 읽는다(쌍선형 보간 = 네 칸을 거리 비율로 섞음).
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public enum GroundLayer { Dirt = 0, Grass = 1, Gravel = 2, Paddy = 3, Leaf = 4 }   // 흙 / 풀 / 자갈 / 논 / 낙엽

    public class HeightField
    {
        public readonly int W, H;
        public readonly float Size;              // 지도가 덮는 한 변(m). 직사각이면 동서 길이(SizeX)
        public readonly float SizeX, SizeZ, OriginX, OriginZ;   // 직사각 땅(2막: 768×640m, 남서 모서리 (0,640)). 정사각 1막은 SizeX=SizeZ=Size, 원점 0
        readonly float[] m;                      // 높이(m), 행 우선: m[z * W + x]

        public HeightField(int w, int h, float sizeM, float[] meters) : this(w, h, sizeM, sizeM, 0f, 0f, meters) { }

        public HeightField(int w, int h, float sizeXM, float sizeZM, float originX, float originZ, float[] meters)
        {
            if (w < 2 || h < 2 || meters == null || meters.Length != w * h) throw new ArgumentException("높이 지도 크기가 맞지 않다");
            W = w; H = h; Size = sizeXM; SizeX = sizeXM; SizeZ = sizeZM; OriginX = originX; OriginZ = originZ; m = meters;
        }

        /// <summary>직사각·원점이 있는 땅용 FromRG(2막)</summary>
        public static HeightField FromRGRect(int w, int h, float sizeXM, float sizeZM, float originX, float originZ, byte[] r, byte[] g, float minM, float maxM)
        {
            var f = new float[w * h];
            for (int i = 0; i < f.Length; i++) f[i] = minM + (r[i] * 256 + g[i]) / 65535f * (maxM - minM);
            return new HeightField(w, h, sizeXM, sizeZM, originX, originZ, f);
        }

        /// <summary>이 월드 점이 이 땅 지도 안인가</summary>
        public bool Covers(float x, float z) { return x >= OriginX && x <= OriginX + SizeX && z >= OriginZ && z <= OriginZ + SizeZ; }

        /// <summary>16비트 높이를 (큰 바이트 R, 작은 바이트 G)로 담은 그림에서 만든다. 0 → minM, 65535 → maxM</summary>
        public static HeightField FromRG(int w, int h, float sizeM, byte[] r, byte[] g, float minM, float maxM)
        {
            var f = new float[w * h];
            for (int i = 0; i < f.Length; i++) f[i] = minM + (r[i] * 256 + g[i]) / 65535f * (maxM - minM);
            return new HeightField(w, h, sizeM, f);
        }

        /// <summary>
        /// 물길 틈 메우기: 강 조각 칸 안쪽만 파여 있어 칸 사이에 1~2m 둑이 남는다. 같은 줄(가로·세로)에서
        /// 양쪽 maxGap 칸 안에 물보다 낮은 칸이 다 있고, 자기 높이가 rimMaxM 이하인 칸을 floorM 으로 낮춰 물길을 잇는다.
        /// (둑이 한쪽에만 물이 있으면 강둑이므로 건드리지 않는다)
        /// </summary>
        public int CloseWaterGaps(float waterM, float rimMaxM, int maxGap, float floorM)
        {
            var lower = new List<int>();
            for (int z = 0; z < H; z++)
                for (int x = 0; x < W; x++)
                {
                    float h = m[z * W + x]; if (h < waterM || h > rimMaxM) continue;
                    if ((LowWithin(x, z, -1, 0, waterM, maxGap) && LowWithin(x, z, 1, 0, waterM, maxGap)) ||
                        (LowWithin(x, z, 0, -1, waterM, maxGap) && LowWithin(x, z, 0, 1, waterM, maxGap))) lower.Add(z * W + x);
                }
            foreach (var i in lower) m[i] = floorM;   // 한꺼번에 낮춘다(낮추는 도중 판정이 바뀌지 않게)
            return lower.Count;
        }

        bool LowWithin(int x, int z, int dx, int dz, float waterM, int maxGap)
        {
            for (int k = 1; k <= maxGap; k++)
            {
                int xx = x + dx * k, zz = z + dz * k;
                if (xx < 0 || zz < 0 || xx >= W || zz >= H) return false;
                if (m[zz * W + xx] < waterM) return true;
            }
            return false;
        }

        public float Texel { get { return SizeX / (W - 1); } }   // 한 칸의 실제 길이(m)

        float Px(int ix, int iz) { return m[Math.Max(0, Math.Min(H - 1, iz)) * W + Math.Max(0, Math.Min(W - 1, ix))]; }

        /// <summary>월드 (x,z) 의 땅 높이(m). 지도 밖은 가장자리 값</summary>
        public float At(float x, float z)
        {
            float fx = (x - OriginX) / SizeX * (W - 1), fz = (z - OriginZ) / SizeZ * (H - 1);
            int ix = (int)Math.Floor(fx), iz = (int)Math.Floor(fz);
            float tx = fx - ix, tz = fz - iz;
            float a = Px(ix, iz), b = Px(ix + 1, iz), c = Px(ix, iz + 1), d = Px(ix + 1, iz + 1);
            return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz;
        }

        /// <summary>그 자리의 기울기(오르막 비율, 높이 변화 ÷ 거리). 가파른 곳을 걷지 못하게 하거나 미끄러운 재질을 고를 때</summary>
        public float Slope(float x, float z)
        {
            float e = Texel;
            float dx = (At(x + e, z) - At(x - e, z)) / (2 * e), dz = (At(x, z + e) - At(x, z - e)) / (2 * e);
            return (float)Math.Sqrt(dx * dx + dz * dz);
        }
    }

    public class SplatField
    {
        public const int Layers = 5;
        public readonly int W, H; public readonly float Size;
        public readonly float SizeX, SizeZ, OriginX, OriginZ;   // 높이 지도와 같은 약속(직사각·원점)
        readonly float[][] w;   // w[층][z*W+x] 0~1

        public SplatField(int wpx, int hpx, float sizeM, float[][] weights) : this(wpx, hpx, sizeM, sizeM, 0f, 0f, weights) { }

        public SplatField(int wpx, int hpx, float sizeXM, float sizeZM, float originX, float originZ, float[][] weights)
        {
            if (weights == null || weights.Length != Layers) throw new ArgumentException("재질 층은 5개");
            foreach (var l in weights) if (l == null || l.Length != wpx * hpx) throw new ArgumentException("재질 지도 크기가 맞지 않다");
            W = wpx; H = hpx; Size = sizeXM; SizeX = sizeXM; SizeZ = sizeZM; OriginX = originX; OriginZ = originZ; w = weights;
        }

        float Px(int l, int ix, int iz) { return w[l][Math.Max(0, Math.Min(H - 1, iz)) * W + Math.Max(0, Math.Min(W - 1, ix))]; }

        /// <summary>월드 (x,z) 의 층별 비율을 합이 1 이 되게 out[0..4] 에 담는다. 아무 층도 칠해지지 않은 자리는 풀 100%</summary>
        public void Weights(float x, float z, float[] o)
        {
            float fx = (x - OriginX) / SizeX * (W - 1), fz = (z - OriginZ) / SizeZ * (H - 1);
            int ix = (int)Math.Floor(fx), iz = (int)Math.Floor(fz);
            float tx = fx - ix, tz = fz - iz, sum = 0f;
            for (int l = 0; l < Layers; l++)
            {
                float v = (Px(l, ix, iz) * (1 - tx) + Px(l, ix + 1, iz) * tx) * (1 - tz) + (Px(l, ix, iz + 1) * (1 - tx) + Px(l, ix + 1, iz + 1) * tx) * tz;
                o[l] = v; sum += v;
            }
            if (sum < 1e-4f) { for (int l = 0; l < Layers; l++) o[l] = l == (int)GroundLayer.Grass ? 1f : 0f; return; }
            for (int l = 0; l < Layers; l++) o[l] /= sum;
        }
    }
}
