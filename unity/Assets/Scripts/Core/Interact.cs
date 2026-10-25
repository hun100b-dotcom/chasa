// =============================================================================
// Interact.cs — F키 상호작용 대상 고르기 (순수 C#, 테스트 가능). 기획 npc-interaction-spec §2.
// 산 사람에게는 쓰지 않는다(엿듣기·지켜보기는 머무르면 저절로). F 대상은 줍기·만져 보기·넋길·쉬기 넷.
// 우선순위: ① 거리가 가장 가까운 것 ② 거리 차이가 0.5m 안이면 줍기 > 만져 보기 > 넋길 > 쉬기.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public enum InteractKind { None = -1, Pickup = 0, Touch = 1, SoulPath = 2, Rest = 3 }   // 숫자가 작을수록 동률일 때 우선

    public struct InteractCand { public InteractKind Kind; public float Dist; public int Id; }

    public static class Interact
    {
        public const float TieM = 0.5f;           // 이 안의 거리 차이는 동률로 본다
        public const float PickupRange = 2.0f, SoulPathRange = 3.0f, RestRange = 3.0f;   // 만져 보기는 Balance.TOUCH_RADIUS

        public static float Range(InteractKind k)
        {
            switch (k)
            {
                case InteractKind.Pickup: return PickupRange;
                case InteractKind.Touch: return Balance.TOUCH_RADIUS;
                case InteractKind.SoulPath: return SoulPathRange;
                case InteractKind.Rest: return RestRange;
            }
            return 0f;
        }

        /// <summary>버튼·안내 글자(폰 버튼도 같은 글자)</summary>
        public static string Label(InteractKind k)
        {
            switch (k)
            {
                case InteractKind.Pickup: return "줍기";
                case InteractKind.Touch: return "만져 보기";
                case InteractKind.SoulPath: return "넋길";
                case InteractKind.Rest: return "쉬기";
            }
            return "";
        }

        /// <summary>범위 안 후보 중 하나를 고른다. 없으면 인덱스 -1</summary>
        public static int Pick(IList<InteractCand> cands)
        {
            int best = -1;
            for (int i = 0; i < cands.Count; i++)
            {
                var c = cands[i];
                if (c.Kind == InteractKind.None || c.Dist > Range(c.Kind)) continue;
                if (best < 0) { best = i; continue; }
                var b = cands[best];
                if (c.Dist < b.Dist - TieM) best = i;
                else if (c.Dist <= b.Dist + TieM && (int)c.Kind < (int)b.Kind) best = i;
                else if (c.Dist <= b.Dist + TieM && c.Kind == b.Kind && c.Dist < b.Dist) best = i;
            }
            return best;
        }
    }
}
