// =============================================================================
// JudgeScenePreview.cs — 확인용 장면 (?scene=…). 사람 눈으로 봐야 하는 상황을 자동 플레이로는 만들기 어려워서, 주소 한 줄로 바로 띄운다.
// 원칙: 게임 규칙·수치·저장은 바꾸지 않는다. 이미 있는 공개 동작(적 세우기·맺힘 깎기·도술 배우기)을 '불러 쓰기만' 한다.
//       주소에 scene= 이 없으면 아무 일도 하지 않는다(일반 플레이에 영향 0). 새 게임(?new=1)과 같이 쓰면 저장에 안 섞인다.
//
//   ?new=1&scene=twoKneel   꿇은 혼 둘 — 겨눈 쪽 굵은 고리·▼ 표식·▲✕가 같은 혼을 겨누는지 (폰은 조이스틱/탭으로 바꿔 보기)
//   ?new=1&scene=bossCrack  보스 맺힘 줄 깨짐 — 3초 뒤 첫 줄(66%)이 깨지고 카메라 당김, 6초 뒤 둘째 줄(33%)
//   ?new=1&scene=dodge      피하기 ◆ 충전이 한 칸 가득 + 한 칸 차오르는 중에 멈춰 있음(폰 버튼 위 표시)
//   ?new=1&scene=tabScroll  도술 점수·배운 도술을 잔뜩 채우고 명부 도술 탭(세로 스크롤)을 연다
//   ?new=1&scene=oldSave    옛 저장처럼 이미 열린 상태로 시작 — 시작 때 '열렸다' 알림이 한꺼번에 뜨면 안 된다
//   ?new=1&scene=reveal     시작 5초 뒤에 도술 나무·인 탭이 새로 열린다 — 알림 두 줄이 한 번씩 뜨는지
// =============================================================================
using Chasa.Core;
using UnityEngine;

public partial class JudgeSystem
{
    string sceneName; bool sceneChecked, sceneDone, scene2; float sceneT;

    static string SceneFromUrl()
    {
        var u = (Application.absoluteURL ?? "").ToLowerInvariant();
        int i = u.IndexOf("scene="); if (i < 0) return null;
        i += 6; int j = i; while (j < u.Length && char.IsLetterOrDigit(u[j])) j++;
        return u.Substring(i, j - i);
    }

    /// <summary>매 프레임(Tick 맨 앞). 장면 이름이 없으면 곧바로 돌아간다</summary>
    void TickScenePreview(float realDt)
    {
        if (!sceneChecked) { sceneChecked = true; sceneName = SceneFromUrl(); }
        if (string.IsNullOrEmpty(sceneName) || player == null) return;
        // 성장 상태 바꾸기는 첫 TickReveal 전에 끝나야 해서 컷이 끝나길 기다리지 않는다
        if (sceneName == "oldsave" && !sceneDone) { sceneDone = true; PreviewUnlockAll(); return; }
        if (sceneName == "dodge") { player.PreviewSetDodge(Balance.DODGE_CHARGES >= 2 ? 1.4f : 0.4f); return; }
        bool ready = (clock == null || openingStarted) && !cuts.Active && !inDay && ui != null;
        if (!ready) return;
        sceneT += realDt;
        var at = player.Pos;
        switch (sceneName)
        {
            case "twokneel":
                if (sceneDone || sceneT < 1f) return;
                sceneDone = true;
                foreach (var off in new[] { new Vector3(4f, 0f, 2.5f), new Vector3(4.5f, 0f, -2.5f) })
                {
                    var e = enemies.SpawnCamp(at + off, false);
                    e.TakeHit(99999, Vector3.right, 0f, 0f);   // 진짜 타격 경로 — 무릎 꿇음·드롭 굴림이 평소처럼 돈다
                }
                Say("확인 장면: 꿇은 혼 둘 (▼가 겨눈 쪽)", 4f);
                break;
            case "bosscrack":
                if (!sceneDone && sceneT >= 1f)
                {
                    sceneDone = true;
                    bossPrev = enemies.SpawnBoss(at + new Vector3(0f, 0f, 9f), 1);
                    bossPrev.soul.Maedhim = Mathf.RoundToInt(bossPrev.soul.MaedhimMax * 0.68f);   // 첫 줄 경계(66%) 바로 위
                    Say("확인 장면: 보스 맺힘 줄 깨짐 (3초·6초 뒤)", 4f);
                }
                if (bossPrev != null && sceneT >= 3f && !scene2) { scene2 = true; BossCrackTo(0.60f); }
                if (bossPrev != null && sceneT >= 6f && scene2 && bossStep == 1) { bossStep = 2; BossCrackTo(0.30f); }
                break;
            case "tabscroll":
                if (sceneDone) return;
                sceneDone = true; PreviewUnlockAll(); panel.PreviewOpen(6);
                break;
            case "reveal":
                if (sceneDone || sceneT < 5f) return;
                sceneDone = true; PreviewUnlockAll();
                break;
        }
    }

    Enemy bossPrev; int bossStep = 1;
    /// <summary>보스 맺힘을 비율 아래로 한 번에 깎는다(진짜 타격 경로 → 줄 깨짐·카메라 당김이 평소처럼 돈다)</summary>
    void BossCrackTo(float ratio)
    {
        int want = Mathf.RoundToInt(bossPrev.soul.MaedhimMax * ratio), dmg = bossPrev.soul.Maedhim - want;
        if (dmg > 0) bossPrev.TakeHit(dmg, Vector3.back, 0f, 0f);
    }

    /// <summary>1막 보스·2막 진입·도술 카드 끝·도술 점수 넉넉히 — 옛 저장을 불러온 것과 같은 모습</summary>
    void PreviewUnlockAll()
    {
        lo.gear.FirstRingBossDone = true; lo.gear.Act2Entered = true;
        cardPicks = DosulCards.Rounds;
        growth.SkillPointsEarned = 40;
        foreach (var n in SkillTree.All) { for (int k = 0; k < n.MaxLevel && growth.CanLearn(n.Name); k++) growth.Learn(n.Name); }
        RefreshGrowth();
    }
}
