// =============================================================================
// World.cs — 넓은 필드를 '구역(Zone)' 바둑판으로 나누는 규칙 (순수 C#, 유니티 없이 테스트됨).
// 기획 확정(10-24): 구역 한 칸 = 128×128m, 플레이어 둘레 3×3 구역을 켜 둔다.
//
// 왜 구역으로 쪼개나? (docs/TECH-DESIGN-OPEN-WORLD.md)
//   월드가 커져도 "가까운 구역만" 그리고 계산하면 웹·폰에서도 가볍다. 먼 곳은 메모리에서 내린다.
//
// 좌표 규칙: 구역 (Zx, Zz)는 월드 x 방향으로 Zx칸, z 방향으로 Zz칸째. 구역 (0,0)은 솔고개 마을이 있는 곳이고
//   그 왼쪽 위 모서리가 월드 기준점이다. 구역끼리는 변이 딱 맞닿는다(틈·겹침 없음).
// 켜짐 여부는 World.Enabled 로 정한다(꺼져 있으면 마을 한 곳만 — 기존 동작 그대로).
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    /// <summary>구역 안의 소품 하나 (월드 좌표). 마을은 아트 배치표(MapData)를 쓰고, 나머지 구역은 이것을 쓴다</summary>
    public struct ZoneProp
    {
        public string Sprite; public float X, Z; public int W, H;
        public ZoneProp(string s, float x, float z, int w, int h) { Sprite = s; X = x; Z = z; W = w; H = h; }
    }

    public sealed class ZoneDef
    {
        public string Id, Name;
        public int Zx, Zz;
        public int Danger;                                  // 위험도 1~5 (소리·BGM 장단이 따라간다)
        public bool Village;                                // true 면 모양은 MapData(아트 배치표)에서 온다
        public string[] Ground;                             // 땅 글자 줄 (마을은 null)
        public readonly List<ZoneProp> Props = new List<ZoneProp>();
        public readonly List<Blocker> Blockers = new List<Blocker>();
        public float MinX, MaxX, MinZ, MaxZ;                // 이 구역이 차지하는 월드 직사각형
        public bool Contains(float x, float z) { return x >= MinX && x < MaxX && z >= MinZ && z < MaxZ; }
        public bool Near(float x, float z, float m) { return x >= MinX - m && x < MaxX + m && z >= MinZ - m && z < MaxZ + m; }
    }

    public static class World
    {
        /// <summary>true 면 구역을 이어 붙인 넓은 필드. 시작 때 GameMain 이 정한다(Balance.WORLD_ZONES 또는 주소 ?zones)</summary>
        public static bool Enabled;

        public static float ZoneSize { get { return Balance.ZONE_SIZE_M; } }
        public static float BaseX { get { return MapLayout.VillageMinX; } }
        public static float BaseZ { get { return MapLayout.VillageMinZ; } }

        // 임시 구역 이름·위험도 (기획이 지역표를 주면 이 표만 바꾼다). 마을에서 멀수록 위험
        static readonly string[] Names = { "솔고개 마을", "보릿들", "물막이 골", "폐당집 어귀" };
        static readonly int[] Dangers = { 1, 2, 2, 3 };

        // (주의: 정적 필드는 적힌 순서대로 만들어진다. 이름표 표가 Zones 보다 먼저 와야 한다)
        public static readonly List<ZoneDef> Zones = Build();
        static readonly Dictionary<long, ZoneDef> byCell = Index();

        // 이름표 번호: (0,0)=마을, (1,0)=보릿들, (0,1)=물막이 골, (1,1)=폐당집 어귀
        static int NameIndex(int zx, int zz) { return zx == 0 && zz == 0 ? 0 : zx == 1 && zz == 0 ? 1 : zx == 0 && zz == 1 ? 2 : 3; }

        static long Key(int zx, int zz) { return ((long)zx << 32) ^ (uint)zz; }

        static List<ZoneDef> Build()
        {
            var list = new List<ZoneDef>();
            for (int zx = 0; zx < 2; zx++)
                for (int zz = 0; zz < 2; zz++)
                {
                    var z = new ZoneDef { Id = "z" + zx + "_" + zz, Name = Names[NameIndex(zx, zz)], Zx = zx, Zz = zz };
                    z.Danger = Dangers[NameIndex(zx, zz)];
                    z.Village = zx == 0 && zz == 0;
                    z.MinX = BaseX + zx * ZoneSize; z.MaxX = z.MinX + ZoneSize;
                    z.MinZ = BaseZ + zz * ZoneSize; z.MaxZ = z.MinZ + ZoneSize;
                    if (!z.Village) Generate(z);
                    list.Add(z);
                }
            return list;
        }

        static Dictionary<long, ZoneDef> Index()
        {
            var d = new Dictionary<long, ZoneDef>();
            foreach (var z in Zones) d[Key(z.Zx, z.Zz)] = z;
            return d;
        }

        /// <summary>월드 전체 경계 (정의된 구역의 바깥 모서리)</summary>
        public static float MinX { get { float m = float.MaxValue; foreach (var z in Zones) m = Math.Min(m, z.MinX); return m; } }
        public static float MaxX { get { float m = float.MinValue; foreach (var z in Zones) m = Math.Max(m, z.MaxX); return m; } }
        public static float MinZ { get { float m = float.MaxValue; foreach (var z in Zones) m = Math.Min(m, z.MinZ); return m; } }
        public static float MaxZ { get { float m = float.MinValue; foreach (var z in Zones) m = Math.Max(m, z.MaxZ); return m; } }

        public static ZoneDef Get(int zx, int zz) { ZoneDef z; return byCell.TryGetValue(Key(zx, zz), out z) ? z : null; }

        /// <summary>월드 점이 속한 구역 (없으면 null)</summary>
        public static ZoneDef At(float x, float z)
        {
            int zx = (int)Math.Floor((x - BaseX) / ZoneSize), zz = (int)Math.Floor((z - BaseZ) / ZoneSize);
            return Get(zx, zz);
        }

        /// <summary>
        /// 임시 들판: 구역 번호로 씨앗을 정해 항상 같은 모양을 만든다(재현 가능). 십자 흙길 + 풀밭 + 흩어진 소품.
        /// 소품은 구역 가장자리에서 6m 안쪽에만 놓아 이웃 구역과 겹치지 않게 한다. (기획이 진짜 지도를 주면 data/zones 파일로 교체)
        /// </summary>
        static void Generate(ZoneDef z)
        {
            float S = Balance.MAP_CELL_SIZE;
            int cells = (int)(ZoneSize / S);
            var rows = new string[cells];
            for (int gy = 0; gy < cells; gy++)
            {
                var chars = new char[cells];
                for (int gx = 0; gx < cells; gx++)
                {
                    bool road = Math.Abs(gy - cells / 2) <= 1 || Math.Abs(gx - cells / 2) <= 1;   // 가운데 십자길
                    chars[gx] = road ? 'D' : 'G';
                }
                rows[gy] = new string(chars);
            }
            z.Ground = rows;
            var rng = new Random(z.Zx * 1009 + z.Zz * 9176 + 7);
            string[] kinds = { "props/prop_jangseung", "props/prop_cairn", "props/prop_jars", "props/prop_stone_wall" };
            float cx = (z.MinX + z.MaxX) * 0.5f, cz = (z.MinZ + z.MaxZ) * 0.5f;
            int tries = 0;
            while (z.Props.Count < 36 && tries++ < 400)
            {
                float x = z.MinX + 6f + (float)rng.NextDouble() * (ZoneSize - 12f);
                float zz = z.MinZ + 6f + (float)rng.NextDouble() * (ZoneSize - 12f);
                if (Math.Abs(x - cx) < 5f || Math.Abs(zz - cz) < 5f) continue;   // 길 위에는 놓지 않는다
                string k = kinds[rng.Next(kinds.Length)];
                int w = k.EndsWith("stone_wall") ? 2 : 1;
                z.Props.Add(new ZoneProp(k, x, zz, w, 1));
                string kind; float r;
                if (k.EndsWith("jangseung")) { kind = "post"; r = 0.4f; }
                else if (w > 1) { kind = "stone"; r = 0.4f * S * 0.5f * w; }
                else { kind = "stone"; r = 0.3f * S; }
                z.Blockers.Add(new Blocker(kind, x, zz, r));
            }
        }
    }

    /// <summary>
    /// 플레이어 위치에 따라 어느 구역을 켜고 끌지 정한다. 유니티는 모른다(켜고 끄는 일은 ZoneManager 가 한다).
    /// 히스테리시스(여유): 경계 선을 막 넘었다고 바로 '현재 구역'을 바꾸지 않고, 경계에서 일정 거리 넘어갔을 때만 바꾼다.
    ///   → 경계선 위를 왔다 갔다 해도 구역이 켜졌다 꺼졌다 하지 않는다.
    /// </summary>
    public sealed class ZoneStreamer
    {
        public ZoneDef Current { get; private set; }
        readonly HashSet<ZoneDef> active = new HashSet<ZoneDef>();
        public IEnumerable<ZoneDef> Active { get { return active; } }
        public int ActiveCount { get { return active.Count; } }
        public bool IsActive(ZoneDef z) { return active.Contains(z); }

        /// <summary>위치를 알려 주면 새로 켤 구역(load)·끌 구역(unload)을 채워 준다</summary>
        public void Update(float x, float z, List<ZoneDef> load, List<ZoneDef> unload)
        {
            if (Current == null || !Current.Near(x, z, Balance.ZONE_HYSTERESIS_M))
            {
                var at = World.At(x, z);
                if (at != null) Current = at;
            }
            if (Current == null) return;
            // 원하는 켜짐 집합: 현재 구역과 그 둘레 8칸 중 실제로 있는 것
            var want = new HashSet<ZoneDef>();
            for (int dx = -1; dx <= 1; dx++)
                for (int dz = -1; dz <= 1; dz++)
                {
                    var n = World.Get(Current.Zx + dx, Current.Zz + dz);
                    if (n != null) want.Add(n);
                }
            foreach (var w in want) if (active.Add(w)) load.Add(w);
            var drop = new List<ZoneDef>();
            foreach (var a in active) if (!want.Contains(a)) drop.Add(a);
            foreach (var d in drop) { active.Remove(d); unload.Add(d); }
        }
    }
}
