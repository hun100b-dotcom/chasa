// =============================================================================
// DemoScript.cs — 비교 영상용 자동 연출 (?demo=1). 사람이 조작하지 않아도 같은 장면이 매번 똑같이 흐른다.
//
// 왜 필요한가? 오너가 "지금 화면"과 "새 화면"을 같은 장면으로 나란히 보고 고르기로 했다.
//   손으로 조작하면 장면이 매번 달라서 비교가 안 된다. 그래서 난수 씨앗을 고정하고(Random.InitState)
//   같은 순서로 입력을 넣는다:  ① 가장 가까운 혼에게 달려가 철삭 3타 → ② 무릎 꿇으면 천도 1회 → ③ 피하기 한 번.
// 체력은 줄지 않게(godMode) 두어 영상 도중에 쓰러지지 않는다.
// =============================================================================
using UnityEngine;

public class DemoScript : MonoBehaviour
{
    public Player player;
    public EnemyManager enemies;
    public JudgeSystem judge;

    float t, nextAttack;
    int stage;            // 0 달려가 때리기 · 1 천도 · 2 피하기 · 3 다음 혼이 있으면 0으로(반복)
    float stageT, walkT;

    public static bool Wanted()
    {
        return (Application.absoluteURL ?? "").Contains("demo=1");
    }

    Enemy Nearest()
    {
        Enemy best = null; float bd = 999f;
        foreach (var e in enemies.list)
        {
            if (e == null || !e.alive || e.kneeling || e.soul.Boss) continue;   // 무릎 꿇은 혼은 천도 몫이라 때리지 않는다
            float d = Vector3.Distance(e.Pos, player.Pos);
            if (d < bd) { bd = d; best = e; }
        }
        return best;
    }

    void Update()
    {
        float dt = Time.unscaledDeltaTime;
        t += dt; stageT += dt;
        judge.godMode = true;
        if (judge.cuts.Active) { t = Mathf.Min(t, 1.5f); return; }   // 오프닝 컷(어두운 화면) 동안은 조작하지 않는다 → 컷이 끝나야 연출 시작
        if (t < 1.5f) return;             // 처음 1.5초는 화면만 보여 준다(밤 분위기)
        judge.StartPlaying();             // 첫 입력으로 친다(적이 움직이기 시작)
        switch (stage)
        {
            case 0:
            {
                var e = Nearest();
                if (e == null) { stage = 1; stageT = 0f; break; }
                // 0.45초마다 다시 명령 → 달려가서 1타, 2타, 3타가 이어진다(입력 버퍼)
                if (t >= nextAttack) { player.CommandAttack(e); nextAttack = t + 0.45f; }
                foreach (var k in enemies.list) if (k != null && k.kneeling && judge.CanTendoNow(k) && Vector3.Distance(k.Pos, player.Pos) < 6f) { stage = 1; stageT = 0f; walkT = 0f; break; }   // 가까이 무릎 꿇은 혼이 있을 때만 천도로(멀리 있는 혼을 쫓다 일어서는 일 방지)
                if (stageT > 14f) { stage = 1; stageT = 0f; }   // 안전장치: 너무 오래 걸리면 다음으로
                break;
            }
            case 1:
            {
                // 무릎 꿇은 혼이 천도 범위 밖이면 먼저 걸어간다(전엔 범위 밖이라 '대상이 없다'만 반복했다)
                Enemy k = null; float kd = 999f;
                foreach (var e in enemies.list)
                {
                    if (e == null || !e.kneeling || !judge.CanTendoNow(e)) continue;   // (무릎 꿇은 혼은 alive 가 아니다 — alive 는 '싸우는 중'만)   // 덩어리·보스처럼 천도 못 하는 혼은 거른다
                    float d = Vector3.Distance(e.Pos, player.Pos);
                    if (d < kd) { kd = d; k = e; }
                }
                if (k == null) { stage = 2; stageT = 0f; break; }
                if (kd > Balance.JUDGE_RANGE * 0.8f)
                {
                    walkT += dt; stageT = 0f;
                    if (walkT > 2.5f) { stage = 0; stageT = 0f; break; }   // 못 다가가면 포기하고 다시 때리기
                    player.CommandMove(k.Pos); break;
                }
                player.CommandStop();   // 쫓기던 대상·예약 공격을 끊어야 천도가 시작된다(안 끊으면 계속 때리며 천도가 거절됨)
                if (stageT > 0.35f && !judge.Casting && stageT < 3f) judge.CommandTendo();
                if (stageT > 3.2f && !judge.Casting) { stage = 2; stageT = 0f; }   // 시전이 끝난 뒤에 피하기로(시전 도중 피해서 취소되는 장면 방지)
                break;
            }
            case 2:
                if (stageT > 0.6f) { player.CommandDodge(player.Pos + new Vector3(-3f, 0, 3f)); stage = 3; stageT = 0f; }
                break;
            case 3:
                // 다음 혼이 남아 있으면 처음부터 다시(영상 30초 동안 여러 마리를 상대하게)
                if (stageT > 0.8f) { stage = Nearest() != null ? 0 : 1; stageT = 0f; walkT = 0f; }   // 서 있는 혼이 있으면 때리기, 모두 무릎 꿇었으면 천도부터
                break;
        }
    }
}
