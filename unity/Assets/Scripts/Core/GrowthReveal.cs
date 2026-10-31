// =============================================================================
// GrowthReveal.cs — 성장 단계 공개 (개편안 P2-2). 순수 C#(엔진 무관), 무엇이 '지금 보이는가'만 정한다.
// 왜: 무기 5계열·장비 7칸·도술 3갈래·품계 50·인 15종이 1막 첫 화면부터 전부 보이면 처음 하는 사람이 어디부터 볼지 모른다.
//   "시스템은 하나씩 열린다" 법칙(개편안 법칙 6)에 따라, 쓸 수 있게 된 순간에 화면에도 나타나게 한다.
// 여기서 바꾸는 것은 '보이는 것'뿐이다. 점수 규칙·드롭·제작 문(Loadout.CraftLockReason)·3대 기둥 수치는 건드리지 않는다.
// 모든 단계 수치(5번·6번째 점수 등)는 임시값이고 DosulCards.Rounds 하나에서 따라온다.
// =============================================================================
namespace Chasa.Core
{
    public static class GrowthReveal
    {
        /// <summary>
        /// 도술 갈래 나무(27개 전체 목록)를 펼칠 때인가.
        /// 본 게임(카드 방식)에서는 처음 다섯 점을 카드 세 장 중 하나로 쓰고(DosulCards), 여섯째 점수를 얻은 뒤에야 나무가 열린다.
        /// 카드 방식이 아닌 시연판(옛 동작)은 처음부터 열려 있다.
        /// </summary>
        public static bool SkillTreeOpen(GrowthState g, bool cardsMode, int cardPicks)
        {
            if (!cardsMode) return true;
            return cardPicks >= DosulCards.Rounds && g.SkillPointsEarned > DosulCards.Rounds;
        }

        /// <summary>
        /// 명부의 '인' 탭을 보여 줄 때인가. 인 만들기 문(Loadout.CraftLockReason)과 같은 때 — 작은 인은 1막 첫 보스를 보낸 뒤, 큰 인은 2막에 들어선 뒤.
        /// 이미 만들어 둔 인이 있으면(옛 저장) 언제나 보인다.
        /// </summary>
        public static bool SealsTabOpen(bool firstRingBossDone, bool act2Entered, int sealBagCount)
        {
            return firstRingBossDone || act2Entered || sealBagCount > 0;
        }

        /// <summary>열린 장비 자리 수(전체 8자리: 무기 2·갓·도포·띠·신·노리개 2). 처음엔 무기 둘·도포·노리개 1 = 4자리</summary>
        public static int OpenEquipCount(bool firstRingBossDone, bool act2Entered)
        {
            int n = 0;
            foreach (EquipPos p in System.Enum.GetValues(typeof(EquipPos))) if (EquipLayout.IsOpen(p, firstRingBossDone, act2Entered)) n++;
            return n;
        }
    }
}
