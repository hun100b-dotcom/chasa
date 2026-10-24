// 자동 생성 파일 — tools/gen_map.py 로 만든다. 손으로 고치지 않는다.
// 원본: data/maps/solgogae_village_layout.json (아트팀 마을 배치표 v1)
namespace Chasa.Core
{
    public struct PropDef
    {
        public string Sprite; public float Ax, Ay; public int W, H;
        public PropDef(string s, float ax, float ay, int w, int h) { Sprite = s; Ax = ax; Ay = ay; W = w; H = h; }
    }

    public static class MapData
    {
        public const int Cols = 18;   // 가로 칸 수 (gx)
        public const int Rows = 14;   // 세로 칸 수 (gy)
        // 땅 종류: S 돌바닥, G 풀, D 흙길, Y 마당, P 논, T 징검다리. 줄 = gy, 글자 = gx
        public static readonly string[] Ground =
        {
            "SSSSGGGGDDGGGGGGGG",
            "SSSSYYYYDDGGGGGGGG",
            "SSSSYYYYDDYYYYGGGG",
            "SSSSYYYYDDYYYYGGGG",
            "GGGGGGGGDDYYYYGGGG",
            "DDDDDDDDDDDDDDDDDD",
            "DDDDDDDDDDDDDDDTTT",
            "GGGYYYYGDDGGGGGTTT",
            "GGGYYYYGDDGYYYYTTT",
            "GGGYYYYGDDGYYYYTTT",
            "GGGGGGGGDDGYYYYTTT",
            "PPPPPPPPPDGGGGGTTT",
            "PPPPPPPPPDGGGGGTTT",
            "PPPPPPPPPDGGGGGTTT",
        };

        public static readonly PropDef[] Props =
        {
            new PropDef("props/prop_seonang_tree", 1.5f, 1.5f, 2, 2),
            new PropDef("props/prop_cairn", 3.0f, 0.0f, 1, 1),
            new PropDef("props/prop_jangseung", 4.0f, 4.0f, 1, 1),
            new PropDef("props/prop_jangseung", 7.0f, 4.0f, 1, 1),
            new PropDef("props/prop_choga", 4.5f, 7.5f, 2, 2),
            new PropDef("props/prop_jars", 3.0f, 7.0f, 1, 1),
            new PropDef("props/prop_choga", 10.5f, 2.5f, 2, 2),
            new PropDef("props/prop_giwa", 12.0f, 8.5f, 3, 2),
            new PropDef("props/prop_well", 8.0f, 7.0f, 1, 1),
            new PropDef("props/prop_sangyeo", 10.5f, 6.0f, 2, 1),
            new PropDef("props/prop_stone_wall", 5.5f, 4.0f, 2, 1),
            new PropDef("props/prop_pyeongsang", 12.5f, 3.0f, 2, 1),
            new PropDef("props/prop_jigae", 13.0f, 5.0f, 1, 1),
            new PropDef("props/prop_sotdae", 15.0f, 4.0f, 1, 1),
            new PropDef("props/prop_jars", 14.0f, 8.0f, 1, 1),
        };
    }
}
