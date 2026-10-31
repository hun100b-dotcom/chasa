// =============================================================================
// Shrine.cs — 서낭당 시설의 규칙 (순수 C#, 기획서 부록 B-5)
// 원칙: 넋은 천도로(도술·품계), 엽전은 파혼으로(장비). 엽전으로는 기억·단서·넋을 살 수 없다 — 그래서
// 이 파일의 어떤 함수도 Neok·Memory 를 건드리지 않는다. 시설은 눈금을 쓰지 않고, 낮과 해 질 녘에 쓴다.
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public enum ShopItem { HealPotion, DawnCharm, CleanseCharm }   // 회복약 / 새벽 부적 / 씻김 부적

    /// <summary>한 밤 동안 들고 있는 소모품. 밤이 끝나면 새로 시작한다</summary>
    public class Pack
    {
        public int Heal, Dawn, Cleanse;
    }

    public static class Shrine
    {
        // ---- 공물상 -------------------------------------------------------------------
        public static int Price(ShopItem it)
        {
            return it == ShopItem.HealPotion ? Balance.SHOP_HEAL_PRICE : it == ShopItem.DawnCharm ? Balance.SHOP_DAWN_PRICE : Balance.SHOP_CLEANSE_PRICE;
        }

        static int Limit(ShopItem it) { return it == ShopItem.HealPotion ? Balance.SHOP_HEAL_MAX : 1; }

        static int Have(Pack p, ShopItem it) { return it == ShopItem.HealPotion ? p.Heal : it == ShopItem.DawnCharm ? p.Dawn : p.Cleanse; }

        /// <summary>엽전이 되고 한 밤 한도 안이면 사서 true</summary>
        public static bool Buy(ShopItem it, Ledger l, Pack p)
        {
            if (l.Coin < Price(it) || Have(p, it) >= Limit(it)) return false;
            l.Coin -= Price(it);
            if (it == ShopItem.HealPotion) p.Heal++; else if (it == ShopItem.DawnCharm) p.Dawn++; else p.Cleanse++;
            return true;
        }

        /// <summary>회복약을 마신다: 최대 생명의 SHOP_HEAL_RATIO 만큼 회복. 없으면 false</summary>
        public static bool UseHeal(Ledger l, Pack p)
        {
            if (p.Heal <= 0 || l.Dead) return false;
            p.Heal--;
            l.Hp = Math.Min(l.MaxHp, l.Hp + (int)Math.Round(l.MaxHp * Balance.SHOP_HEAL_RATIO));
            return true;
        }

        // ---- 손보기 -------------------------------------------------------------------
        /// <summary>다시 굴리기 비용: 20에서 시작해 같은 물건에 할 때마다 +20, 최대 200</summary>
        public static int RerollCost(int timesAlready)
        {
            return Math.Min(Balance.REROLL_MAX, Balance.REROLL_BASE + Balance.REROLL_STEP * timesAlready);
        }

        /// <summary>기울기 옵션과 이름 있는 물건은 다시 굴릴 수 없다</summary>
        public static bool CanReroll(ItemDef it) { return it != null && !it.Gradient && !it.Named && it.Options.Count > 0; }

        /// <summary>옵션 하나(index 번째)를 다른 종류의 새 옵션으로 굴린다. 엽전이 모자라거나 못 굴리는 물건이면 false</summary>
        public static bool Reroll(ItemDef it, int index, Ledger l, Func<float> rand)
        {
            if (!CanReroll(it) || index < 0 || index >= it.Options.Count) return false;
            int cost = RerollCost(it.Rerolls);
            if (l.Coin < cost) return false;
            var keep = new List<Opt>();
            for (int i = 0; i < it.Options.Count; i++) keep.Add(it.Options[i].Kind);   // 이미 있는 종류는 피한다(중복 방지)
            l.Coin -= cost;
            it.Options[index] = Loot.RollOption(rand, it.Rarity, keep, it.Slot);
            it.Rerolls++;
            return true;
        }

        /// <summary>매듭 올리기: 흔한→손본(엽전 60+광석 3), 손본→귀한(180+10). 귀한 위·이름 있는 물건은 못 올린다</summary>
        public static bool CanUpgrade(ItemDef it) { return it != null && !it.Named && it.Rarity != Rarity.Rare; }

        public static bool Upgrade(ItemDef it, Ledger l, Func<float> rand)
        {
            if (!CanUpgrade(it)) return false;
            bool toRare = it.Rarity == Rarity.Crafted;
            int coin = toRare ? Balance.UPGRADE_COIN_2 : Balance.UPGRADE_COIN_1;
            int ore = toRare ? Balance.UPGRADE_ORE_2 : Balance.UPGRADE_ORE_1;
            if (l.Coin < coin || l.Ore < ore) return false;
            l.Coin -= coin; l.Ore -= ore;
            var next = toRare ? Rarity.Rare : Rarity.Crafted;
            float scale = Loot.TierFactor(next) / Loot.TierFactor(it.Rarity);   // 범위가 새 등급 것으로 바뀐다
            var keep = new List<Opt>();
            for (int i = 0; i < it.Options.Count; i++)
            {
                var o = it.Options[i]; keep.Add(o.Kind);
                var v = o.Value * scale;
                it.Options[i] = new OptionRoll(o.Kind, o.Kind == Opt.HpFlat ? (float)Math.Round(v) : v);
            }
            it.Rarity = next;
            it.Options.Add(Loot.RollOption(rand, next, keep, it.Slot));   // 옵션 칸이 하나 늘어난다
            return true;
        }

        /// <summary>풀기(분해): 비용 0, 광석을 얻고 장비는 사라진다. 이름 있는 물건은 풀 수 없다</summary>
        public static int OreFor(Rarity r)
        {
            return r == Rarity.Rare ? Balance.DISMANTLE_ORE_RARE : r == Rarity.Crafted ? Balance.DISMANTLE_ORE_CRAFTED : Balance.DISMANTLE_ORE_COMMON;
        }

        public static bool Dismantle(ItemDef it, Ledger l)
        {
            if (it == null || it.Named) return false;
            l.Ore += OreFor(it.Rarity);
            return true;   // 호출한 쪽이 장비 칸에서 지운다
        }

        /// <summary>장비 손보기 비용: 지금 단계(0~4)에서 다음 단계로. 240/480/800/1200/1760 (1막 균형 10-31: 옛 30/60/100/150/220의 8배. 일곱 칸 모두 5단계면 약 31,000 ≈ 시즌 1 엽전 수입의 4분의 3)</summary>
        public static int EnhanceCost(int plusNow)
        {
            int[] c = { Balance.ENHANCE_COST_1, Balance.ENHANCE_COST_2, Balance.ENHANCE_COST_3, Balance.ENHANCE_COST_4, Balance.ENHANCE_COST_5 };
            return c[Math.Max(0, Math.Min(c.Length - 1, plusNow))];
        }

        /// <summary>이름 있는 물건도 손볼 수 있다(옵션을 바꾸는 게 아니라 키우는 것). 최대 단계 전이면 true</summary>
        public static bool CanEnhance(ItemDef it) { return it != null && it.Options.Count > 0 && it.Plus < Balance.ENHANCE_MAX; }

        /// <summary>손보기 한 단계: 엽전만 쓴다(넋·기억은 건드리지 않는다 — 천도=넋, 파혼=엽전 구분)</summary>
        public static bool Enhance(ItemDef it, Ledger l)
        {
            if (!CanEnhance(it)) return false;
            int cost = EnhanceCost(it.Plus);
            if (l.Coin < cost) return false;
            l.Coin -= cost; it.Plus++;
            return true;
        }

        /// <summary>홈 뚫기: 첫째 80, 둘째 240, 최대 2</summary>
        public static bool Socket(ItemDef it, Ledger l)
        {
            if (it == null || it.Sockets >= Balance.SOCKET_MAX) return false;
            int cost = it.Sockets == 0 ? Balance.SOCKET_COST_1 : Balance.SOCKET_COST_2;
            if (l.Coin < cost) return false;
            l.Coin -= cost; it.Sockets++;
            return true;
        }
    }
}
