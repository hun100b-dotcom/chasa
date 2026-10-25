// =============================================================================
// BgmDirector.cs — BGM 층 고르기 규칙 (순수 C#, 테스트 가능). 소리를 내는 건 BgmPlayer(Unity)가 맡고,
// 여기서는 "지금 어느 층을 틀어야 하나, 몇 초에 걸쳐 넘기나"만 정한다. 기준표는 data/bgm.json (기획·사운드).
//   탐색(낮/밤) ↔ 전투: 적이 8m 안이면 전투, 다 멀어지고 4초 지나면 탐색으로
//   처결: 적이 무릎 꿇는 순간 짧은 곡 1회 → 천도·파혼이 끝날 때까지 BGM 쉼 → 2초에 걸쳐 탐색 복귀
// =============================================================================
using System;

namespace Chasa.Core
{
    public enum BgmLayer { Explore, Combat, Finish, Silent }

    public class BgmDirector
    {
        public const float CombatRange = 8f;        // 적이 이 안이면 전투 층
        public const float CombatExitDelay = 4f;    // 전투가 끝난 뒤 기다리는 시간
        public const float FinishClipSec = 6.9f;    // 처결 임시 곡 길이(이 뒤로는 무음)
        public const float DayToNightSec = 8f, ExploreToCombatSec = 1f, CombatToExploreSec = 3f, ToFinishSec = 0.3f, FinishToExploreSec = 2f;
        // 낮밤 경계에 히스테리시스(문턱 두 개): 해 질 녘에 곡이 깜빡이며 왔다 갔다 하지 않게
        const float NightBelow = 0.30f, DayAbove = 0.40f;

        public BgmLayer Layer = BgmLayer.Explore;
        public bool Night;                          // 탐색 층에서 밤 곡을 쓰나
        public float Fade = 2f;                     // 직전 전환에 쓸 교차 시간(초)
        float combatQuiet, finishT;                 // 마지막 적 이후 흐른 시간 / 처결 곡 재생 시간

        /// <summary>한 프레임 갱신. nearestEnemy: 가장 가까운 살아 있는 적 거리(없으면 큰 수)</summary>
        public void Update(float dt, float daylight, float nearestEnemy, bool kneelStarted, bool kneelBusy)
        {
            // 낮밤(탐색 층 안에서만 의미가 있지만 항상 갱신해 둔다)
            bool wasNight = Night;
            if (Night && daylight > DayAbove) Night = false;
            else if (!Night && daylight < NightBelow) Night = true;
            bool nightFlip = Night != wasNight;

            // 처결: 무릎 꿇는 순간 1회. 곡이 끝나면 천도·파혼이 끝날 때까지 무음
            if (kneelStarted && Layer != BgmLayer.Finish && Layer != BgmLayer.Silent) { Set(BgmLayer.Finish, ToFinishSec); finishT = 0f; return; }
            if (Layer == BgmLayer.Finish)
            {
                finishT += dt;
                if (finishT >= FinishClipSec) Layer = BgmLayer.Silent;
            }
            if (Layer == BgmLayer.Silent || Layer == BgmLayer.Finish)
            {
                // 곡이 끝났고(또는 곡 도중에라도) 처결이 끝났으면 탐색으로
                if (!kneelBusy && finishT >= FinishClipSec) { Set(BgmLayer.Explore, FinishToExploreSec); combatQuiet = CombatExitDelay; }
                return;
            }

            // 전투 ↔ 탐색
            if (nearestEnemy <= CombatRange) combatQuiet = 0f; else combatQuiet += dt;
            if (Layer == BgmLayer.Explore && nearestEnemy <= CombatRange) Set(BgmLayer.Combat, ExploreToCombatSec);
            else if (Layer == BgmLayer.Combat && combatQuiet >= CombatExitDelay) Set(BgmLayer.Explore, CombatToExploreSec);
            else if (nightFlip && Layer == BgmLayer.Explore) Fade = DayToNightSec;   // 낮↔밤은 8초 교차
        }

        void Set(BgmLayer l, float fade) { Layer = l; Fade = fade; }
    }
}
