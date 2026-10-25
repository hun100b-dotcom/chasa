// =============================================================================
// FieldRules.cs — 5×5 넓은 필드(640m)의 규칙 (순수 C#, 유니티 없이 테스트됨).
//
// 필드란? 아트팀이 블렌더로 조립한 이어진 땅(솔고개 마을 · 보릿들 · 물막이 골 · 검은여울 · 폐당집).
//   128m 칸(청크 = 한 덩어리)을 5×5로 이어 640m. 걸어가면 둘레 3×3 칸만 켜고 먼 칸은 끈다(웹·폰이 가볍게).
// 이 파일이 정하는 것: 청크 번호 계산 / 소품별 충돌 크기 / 이야기 자리(단서·이름혼·보스)·시작 위치.
//   (그림은 FieldManager 가, 데이터는 Resources/Data/field.json 이 가진다)
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public static class FieldRules
    {
        /// <summary>필드 모드 켜짐 (주소 ?field 또는 설정). 시작 때 GameMain 이 정한다</summary>
        public static bool On;

        public const float Size = 640f;        // 필드 한 변(m)
        public const float ChunkSize = 128f;   // 청크 한 변(m) — 기획 확정값(구역 한 칸)
        public const int Chunks = 5;           // 한 변의 청크 수

        // 이야기 자리 (아트 마커에서 받는다. 못 받았을 때를 대비한 기본값 = 마커 값과 같음)
        public static float StartX = 196f, StartZ = 30f;           // 시작 위치(마을 남쪽 입구)
        public static float VillageX = 196f, VillageZ = 60f;       // 마을 원점
        public static float BossX = 404f, BossZ = 288f;            // 1호 보스 자리(개울 위 나룻배)

        /// <summary>넋길로 이어진 서낭당 자리들(남→북 순서)과 이름. 마커에서 채운다</summary>
        public static float[][] Shrines = new float[0][];
        public static string[] ShrineNames = new string[0];

        /// <summary>단서 세 곳: 마을 안 큰길과 마당 근처 (마을 원점 기준 옮김)</summary>
        public static float[][] CluePoints()
        {
            return new[]
            {
                new[] { VillageX - 7f, VillageZ - 10f },
                new[] { VillageX + 9f, VillageZ + 2f },
                new[] { VillageX - 5f, VillageZ + 14f },
            };
        }
        public static float NamedX { get { return VillageX + 6f; } }   // 첫 이름혼 자리
        public static float NamedZ { get { return VillageZ - 16f; } }

        /// <summary>월드 좌표 → 청크 번호 (0~4). 필드 밖은 가장자리로 붙인다</summary>
        public static int ChunkIndex(float v)
        {
            int i = (int)Math.Floor(v / ChunkSize);
            return Math.Max(0, Math.Min(Chunks - 1, i));
        }

        /// <summary>청크 (cx, cz)를 하나의 정수 키로</summary>
        public static int Key(int cx, int cz) { return cx * 100 + cz; }

        /// <summary>
        /// 모델 이름으로 충돌(막힘) 반지름을 정한다. 0 이면 지나갈 수 있다(덤불·갈대·길·금줄 등).
        /// 왜 원(동그라미)? 기존 충돌 규칙(MapLayout)이 원이라 그대로 붙인다.
        /// </summary>
        public static float BlockerRadius(string name)
        {
            if (name == null) return 0f;
            if (name == "br_deep") return 4.6f;                                   // 깊은 물: 8m 칸을 거의 다 막는다
            if (name.StartsWith("terrain_tile_") || name.StartsWith("br_")) { if (name == "br_willow_a" || name == "br_willow_b") return 0.7f; if (name == "br_herb_rack") return 1.2f; if (name == "br_jars") return 0.6f; if (name == "br_med_sign") return 0.3f; return 0f; }
            if (name.StartsWith("hanok_"))
            {
                // 집은 조각을 맞춰 지었다: 기단·벽·기둥만 막고 문·지붕·처마·굴뚝은 통과(문은 드나드는 곳)
                if (name.Contains("gidan") || name.Contains("wall") || name.Contains("pillar")) return 1.1f;
                return 0f;
            }
            if (name.StartsWith("nature_"))
            {
                if (name.Contains("pine") || name.Contains("zelkova") || name.Contains("dead")) return 0.6f;
                if (name.Contains("bamboo")) return 0.5f;
                return 0f;                                                          // 덤불·억새·갈대는 헤치고 간다
            }
            if (name == "terrain_rock_small") return 0.7f;
            if (name == "terrain_rock_medium") return 1.3f;
            if (name == "terrain_rock_cluster") return 2.0f;
            if (name.StartsWith("terrain_bush")) return 0f;
            switch (name)
            {
                case "prop_seonangdang": return 2.2f;
                case "prop_dolddam": return 1.0f;
                case "prop_jangdok": return 0.7f;
                case "prop_jangseung": return 0.4f;
                case "prop_umul": return 1.3f;
                case "prop_sangyeo": return 1.5f;
                case "prop_sotdae": return 0.3f;
                case "prop_choga": case "prop_giwa": return 2.5f;
                case "night_torch_stand": return 0.3f;
                case "prop_gaejip_empty": return 0.6f;       // 아트 walkcheck 에 맞춤(개집)
                case "prop_market_drum_frame": return 0.5f;  // 북틀. 벼루(prop_dry_inkstone)는 0
            }
            return 0f;
        }

        /// <summary>월드 점이 필드 안인가</summary>
        public static bool Inside(float x, float z) { return x >= 0f && x <= Size && z >= 0f && z <= Size; }
    }
}
