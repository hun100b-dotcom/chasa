// =============================================================================
// DosulIcons.cs — 폰 버튼 그림 이름표 (아트 2차, 2026-10-31)
// 한글 기술 이름 → 그림 파일 이름 연결표. 코드는 "이름만" 읽어 그림을 붙이고, 그림이 없으면 옛 글자 버튼으로 돈다.
// 왜 Core 에 두나: 화면(유니티)과 무관한 순수 표라서 테스트로 "도술을 새로 추가했는데 그림 이름을 빠뜨림"을 바로 잡을 수 있다.
// 파일 위치: Resources/Sprites/overhaul/skill/<이름>@2x (도술) · overhaul/btn/<이름>@2x (Q·F 버튼)
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public static class DosulIcons
    {
        // 도술 15(액티브) → 그림 이름. 패시브는 그림이 없어 갈래 쪽지로 대신한다(BranchIcon)
        static readonly Dictionary<string, string> Skill = new Dictionary<string, string>
        {
            { "붙잡아 부르기", "call_grab" }, { "혼불 날리기", "call_wisp" }, { "이름 비추기", "call_light" }, { "배웅길", "call_path" }, { "일곱 이름", "call_seven" },
            { "휘감기", "chain_coil" }, { "여럿 끌기", "chain_haul" }, { "매듭 걸음", "chain_dash" }, { "한 줄 꿰기", "chain_thread" }, { "쇠사슬 울", "chain_fence" },
            { "터뜨리기", "stain_burst" }, { "원념 두르기", "stain_aura" }, { "얼룩 타기", "stain_ride" }, { "깨진 이름 던지기", "stain_shard" }, { "금 간 그림자", "stain_shadow" },
        };

        /// <summary>도술 이름 → 그림 이름. 모르는 이름이면 null(코드는 글자로 대신 그린다)</summary>
        public static string SkillIcon(string skillName)
        {
            string id; return skillName != null && Skill.TryGetValue(skillName, out id) ? id : null;
        }

        /// <summary>갈래 쪽지 그림 이름(패시브·표에 없는 도술의 대신)</summary>
        public static string BranchIcon(Branch b) { return b == Branch.Call ? "branch_call" : b == Branch.Chain ? "branch_chain" : "branch_stain"; }

        /// <summary>Q 버튼 글자(무기 기술 이름) → 그림 이름. 글자는 GameMain 의 qLabel 과 같다. 모르는 글자는 베기 그림</summary>
        public static string QIcon(string qLabel)
        {
            switch (qLabel)
            {
                case "끌기": return "q_chain";
                case "땅울림": return "q_mace";
                case "부르기": case "세우기": return "q_bell";   // PC 칸 글자(세우기)와 폰 글자(부르기)가 다르다
                case "꽂기": return "q_trident";
                case "이름": return "q_brush";
                default: return "q_slash";
            }
        }

        /// <summary>상호작용(F) 버튼 그림 이름</summary>
        public const string UseIcon = "use", UseIconHot = "use_hot";
    }
}
