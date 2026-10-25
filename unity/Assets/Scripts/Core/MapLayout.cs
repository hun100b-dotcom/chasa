// =============================================================================
// MapLayout.cs — 솔고개 마을의 '충돌 뼈대'와 좌표 규칙 (순수 C#). 모양 데이터는 MapData.cs (아트 배치표에서 자동 생성).
// 원칙: 뼈대 지형은 손(아트 배치표)으로, 내부 배치(혼 위치)만 무작위 (Godot MapGen 과 같은 원칙).
// 왜 원(동그라미) 충돌? 쿼터뷰 액션에서 사각형보다 '미끄러지며 돌아가기'가 자연스럽고 계산도 쉽다.
//
// 좌표: 배치표 칸 (gx 가로, gy 세로) → 월드 (x, z).  x = (gy - 1.5) * S,  z = (gx - 1.5) * S  (S = 한 칸 길이 m)
//   왜 이 식? 카메라가 요 45° 로 보면 화면 오른쪽 ∝ (-x + z), 아래쪽 ∝ (x + z) 인데,
//   아트의 등각 화면 좌표는 오른쪽 ∝ (gx - gy), 아래쪽 ∝ (gx + gy) 라서 이 식이면 그림이 그대로 맞물린다.
//   (1.5, 1.5) 칸 = 서낭나무 중심을 월드 원점(0,0)에 둔다.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public struct Blocker
    {
        public float X, Z, R;
        public string Kind;   // "house" 집 / "post" 장승 / "stone" 작은 소품 — 화면 대체 모양을 고르는 이름표
        public Blocker(string kind, float x, float z, float r) { Kind = kind; X = x; Z = z; R = r; }
    }

    public static class MapLayout
    {
        static float S { get { return Balance.MAP_CELL_SIZE; } }

        // 마을 한 곳만의 경계 (구역 0번 = 마을의 기준 모서리이기도 하다)
        public static float VillageMinX { get { return (0f - 1.5f) * S; } }
        public static float VillageMaxX { get { return (MapData.Rows - 1.5f) * S; } }
        public static float VillageMinZ { get { return (0f - 1.5f) * S; } }
        public static float VillageMaxZ { get { return (MapData.Cols - 1.5f) * S; } }

        /// <summary>맵 경계 (월드). 구역 기능이 꺼져 있으면 마을 한 곳(기존 동작), 켜져 있으면 이어 붙인 구역 전체</summary>
        public static float MinX { get { return FieldRules.On ? FieldRules.MinX : World.Enabled ? World.MinX : VillageMinX; } }
        public static float MaxX { get { return FieldRules.On ? FieldRules.WorldX : World.Enabled ? World.MaxX : VillageMaxX; } }
        public static float MinZ { get { return FieldRules.On ? FieldRules.MinZ : World.Enabled ? World.MinZ : VillageMinZ; } }
        public static float MaxZ { get { return FieldRules.On ? FieldRules.WorldZ : World.Enabled ? World.MaxZ : VillageMaxZ; } }

        public static float CenterX { get { return (MinX + MaxX) * 0.5f; } }
        public static float CenterZ { get { return (MinZ + MaxZ) * 0.5f; } }

        /// <summary>배치표 칸 좌표(소수 가능) → 월드 x</summary>
        public static float WorldX(float gy) { return (gy - 1.5f) * S; }
        public static float WorldZ(float gx) { return (gx - 1.5f) * S; }

        // 이야기 자리 (칸 좌표로 정한다 — 아트 배치표의 메모를 따름)
        public static float BossX { get { return FieldRules.On ? FieldRules.BossX : WorldX(10.5f); } }   // 징검다리 쪽 동쪽 끝 '나루'
        public static float BossZ { get { return FieldRules.On ? FieldRules.BossZ : WorldZ(16f); } }
        public static float NamedX { get { return FieldRules.On ? FieldRules.NamedX : WorldX(11f); } }    // 튜토리얼 첫 이름혼(박돌쇠) 자리
        public static float NamedZ { get { return FieldRules.On ? FieldRules.NamedZ : WorldZ(12f); } }
        /// <summary>낮 단서 세 곳(칸 좌표). 큰길과 마당에 놓아 걸어가며 줍게 한다</summary>
        public static readonly float[][] ClueCells = { new[] { 6f, 5.4f }, new[] { 13.5f, 3.2f }, new[] { 5.2f, 8.6f } };

        /// <summary>단서 자리(월드 x, z). 필드 모드면 필드 마을 안, 아니면 옛 배치표 칸에서 계산</summary>
        public static float[][] CluePoints()
        {
            if (FieldRules.On) return FieldRules.CluePoints();
            var r = new float[ClueCells.Length][];
            for (int i = 0; i < r.Length; i++) r[i] = new[] { WorldX(ClueCells[i][1]), WorldZ(ClueCells[i][0]) };
            return r;
        }

        /// <summary>솔고개 첫 밤 막힌 곳 목록: 아트 배치표의 소품에서 자동으로 만든다</summary>
        public static readonly List<Blocker> Blockers = BuildFromProps();
        /// <summary>불러온 다른 구역들의 막힌 곳 (ZoneManager 가 구역을 켜고 끌 때 넣고 뺀다)</summary>
        public static readonly List<Blocker> ZoneBlockers = new List<Blocker>();

        static List<Blocker> BuildFromProps()
        {
            var b = new List<Blocker>();
            foreach (var p in MapData.Props)
            {
                if (p.Sprite.EndsWith("seonang_tree")) continue;   // 서낭나무는 출발점이라 막지 않는다 (화면에서만 뒤쪽에 그린다)
                float x = WorldX(p.Ay), z = WorldZ(p.Ax);
                string kind; float r;
                if (p.Sprite.EndsWith("choga") || p.Sprite.EndsWith("giwa")) { kind = "house"; r = 0.4f * S * (p.W > p.H ? p.W : p.H) * 0.9f; }
                else if (p.Sprite.EndsWith("jangseung")) { kind = "post"; r = 0.4f; }
                else if (p.W > 1 || p.H > 1) { kind = "stone"; r = 0.4f * S * 0.5f * (p.W > p.H ? p.W : p.H); }   // 담·평상·상여: 긴 소품
                else { kind = "stone"; r = 0.3f * S; }
                b.Add(new Blocker(kind, x, z, r));
            }
            return b;
        }

        /// <summary>
        /// 반지름 radius 인 몸이 (x,z) 에 있을 때 막힌 곳과 겹치면 바깥으로 밀어낸다. 맵 경계도 지킨다.
        /// 두 번 돌려 모서리에 끼는 일을 줄인다.
        /// </summary>
        public static void PushOut(ref float x, ref float z, float radius)
        {
            for (int pass = 0; pass < 2; pass++)
                for (int bi = 0; bi < Blockers.Count + ZoneBlockers.Count; bi++)
                {
                    var o = bi < Blockers.Count ? Blockers[bi] : ZoneBlockers[bi - Blockers.Count];
                    float dx = x - o.X, dz = z - o.Z;
                    float min = o.R + radius;
                    float d2 = dx * dx + dz * dz;
                    if (d2 >= min * min) continue;
                    float d = (float)System.Math.Sqrt(d2);
                    if (d < 1e-4f) { dx = 1f; dz = 0f; d = 1f; }   // 정확히 중심이면 +x 로 밀어낸다
                    x = o.X + dx / d * min;
                    z = o.Z + dz / d * min;
                }
            x = System.Math.Max(MinX + radius, System.Math.Min(MaxX - radius, x));
            z = System.Math.Max(MinZ + radius, System.Math.Min(MaxZ - radius, z));
            ClampL(ref x, ref z, radius);
        }

        static void ClampL(ref float x, ref float z, float radius)
        {
            if (FieldRules.On && (FieldRules.Act2 || FieldRules.Act3)) FieldRules.ClampWalk(ref x, ref z, radius);   // 땅이 여러 사각형이면 사각형 밖 빈 구석으로 못 나가게 가장 가까운 땅 안으로 당긴다
        }

        /// <summary>
        /// 주인공 전용 금줄: 2막(금줄 둘)·3막(금줄 셋)이 아직 닫혀 있으면 그 땅 안으로 못 들어간다. 혼·NPC·보스는 그 땅에 서 있어야 하니 일반 PushOut 은 그대로 둔다.
        /// 왜 따로? 맵 경계를 줄이면 닫힌 땅에 세운 사람과 보스가 모두 경계선으로 끌려 나온다.
        /// </summary>
        public static void PlayerClamp(ref float x, ref float z, float radius)
        {
            if (FieldRules.On && (FieldRules.Act2 || FieldRules.Act3) && (!FieldRules.Act2Open || !FieldRules.Act3Open)) FieldRules.ClampWalk(ref x, ref z, radius, true);
        }

        /// <summary>점 하나를 맵 안으로만 가둔다 (이동 목표점 등, 막힌 곳은 따지지 않음)</summary>
        public static void ClampPoint(ref float x, ref float z)
        {
            x = System.Math.Max(MinX, System.Math.Min(MaxX, x));
            z = System.Math.Max(MinZ, System.Math.Min(MaxZ, z));
            ClampL(ref x, ref z, 0f);
        }

        /// <summary>점 (x,z) 가 막힌 곳 안인가 (혼이 집 안에서 태어나지 않게 검사용)</summary>
        public static bool IsBlocked(float x, float z, float radius)
        {
            foreach (var o in Blockers)
            {
                float dx = x - o.X, dz = z - o.Z, min = o.R + radius;
                if (dx * dx + dz * dz < min * min) return true;
            }
            foreach (var o in ZoneBlockers)
            {
                float dx = x - o.X, dz = z - o.Z, min = o.R + radius;
                if (dx * dx + dz * dz < min * min) return true;
            }
            return false;
        }

        /// <summary>
        /// 출발점(0,0)에서 목표까지 몸(radius)이 지나갈 수 있는가 — 칸 격자 길찾기(막힌 칸 제외). 맵이 막혀 보스에 못 가는 일을 자동으로 잡는다.
        /// </summary>
        public static bool Reachable(float tx, float tz, float radius, float step = 0.5f)
        {
            int nx = (int)((MaxX - MinX) / step) + 1, nz = (int)((MaxZ - MinZ) / step) + 1;
            var seen = new bool[nx, nz];
            var q = new Queue<int>();
            int sx = (int)((0f - MinX) / step), sz = (int)((0f - MinZ) / step);
            int gx = (int)((tx - MinX) / step), gz = (int)((tz - MinZ) / step);
            q.Enqueue(sx * nz + sz); seen[sx, sz] = true;
            int[] dxs = { 1, -1, 0, 0 }, dzs = { 0, 0, 1, -1 };
            while (q.Count > 0)
            {
                int c = q.Dequeue(); int cx = c / nz, cz = c % nz;
                if (System.Math.Abs(cx - gx) <= 1 && System.Math.Abs(cz - gz) <= 1) return true;
                for (int k = 0; k < 4; k++)
                {
                    int ax = cx + dxs[k], az = cz + dzs[k];
                    if (ax < 0 || az < 0 || ax >= nx || az >= nz || seen[ax, az]) continue;
                    float wx = MinX + ax * step, wz = MinZ + az * step;
                    if (IsBlocked(wx, wz, radius)) continue;
                    seen[ax, az] = true; q.Enqueue(ax * nz + az);
                }
            }
            return false;
        }
    }
}
