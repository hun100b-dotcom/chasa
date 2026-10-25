// =============================================================================
// Cutscene.cs — 실시간 컷신의 '시간표 재생기' (순수 C#, 테스트 가능). 기획 7단계 첫 보스 연출.
//
// 컷신 = 시각(t)마다 붙는 단계(step)의 목록: 카메라를 어디로·얼마나 확대·대사 한 줄. 이 클래스는 시간만 흘리며
// "지금 카메라가 어디를 보나 / 어떤 대사가 떠 있나 / 끝났나"를 알려 준다. 화면(카메라 이동·글자 그리기)은 쓰는 쪽이 맡는다.
// 왜 코어에? 컷신이 순서 틀리거나 끝나지 않아 입력이 영영 잠기는 사고를 엔진 없이 시험으로 막으려고.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    [System.Serializable]
    public class CutStep
    {
        public float t;                          // 컷 시작부터 초
        public string cam, camTo;                // 카메라 모드(pan·push·pull·hold·cut·shake·return)와 바라볼 대상
        public float camTime, zoom, shake;       // 이동 시간, 확대 배율(0 이면 안 바꿈), 흔들림(0 이면 없음)
        public string text, style;               // 대사 글자와 모양(bubble·memory)
        public float lineDur;                    // 대사가 떠 있는 시간
        public string[] sfx;                     // 이 시각에 틀 효과음 id 들(서사 대본 sfx 칸)
        public string weather;                   // 장면 날씨: clear·cloudy·rain·fog·plague 로 고정(서사가 정하면 무작위보다 우선), auto 면 풀림
        public string cond;                      // 이 조건일 때만 적용(예: "B-01 천도함"). 비면 늘 적용 — 서사 장례 대본의 condition 칸
        public string ctl;                       // 조작 허용: none(잠금) / walk(걷기만) / restore(복귀). 비면 그대로 — 서사 대본의 control 칸
    }

    [System.Serializable]
    public class CutData
    {
        public string id;
        public float duration;
        public bool @lock, pause, skippable;     // 입력 잠금 / 적 멈춤 / 건너뛸 수 있나
        public CutStep[] steps;
    }

    public class CutPlayback
    {
        public readonly CutData Data;
        public float Time;
        public bool Done { get { return Time >= Data.duration; } }
        public string SceneWeather;              // 컷이 정한 날씨 이름(없으면 null). 컷이 끝나면 쓰지 않는다
        public string CamTarget = "player";      // 지금 카메라가 보는 곳
        public float CamZoom = 1f;               // 지금 확대 배율(1 = 평소)
        public float CamTime = 0.3f;             // 가장 최근 단계가 정한 이동 시간
        public float ShakeRequest;               // 이번 프레임에 새로 걸린 흔들림(쓴 쪽이 읽고 0 으로)
        public readonly Queue<string> SfxPending = new Queue<string>();   // 틀어야 할 효과음 대기줄(쓰는 쪽이 비운다)
        public bool Walk;                        // 지금 구간이 '걷기만 허용'인가(잠금 컷이어도 걸을 수 있다)
        public string LineText = "", LineStyle = "";
        float lineUntil;
        int next;                                 // 다음에 적용할 단계 번호

        public static System.Func<string, bool> Cond;   // 조건 글자를 판정하는 쪽(JudgeSystem 이 정한다). 없으면 조건 붙은 단계는 건너뜀
        public CutPlayback(CutData d) { Data = d; Apply(0f); }

        public bool LineVisible { get { return !string.IsNullOrEmpty(LineText) && Time < lineUntil; } }

        public void Tick(float dt)
        {
            if (Done) return;
            Time += dt;
            Apply(Time);
        }

        void Apply(float now)
        {
            while (next < Data.steps.Length && Data.steps[next].t <= now)
            {
                var s = Data.steps[next++];
                if (!string.IsNullOrEmpty(s.cond) && (Cond == null || !Cond(s.cond))) continue;   // 조건이 아니면 시간은 비워 둔 채 다음 박자로
                if (s.sfx != null) foreach (var id in s.sfx) if (!string.IsNullOrEmpty(id)) SfxPending.Enqueue(id);
                if (!string.IsNullOrEmpty(s.weather)) SceneWeather = s.weather == "auto" ? null : s.weather;
                if (s.ctl == "walk" || s.ctl == "restore") Walk = true; else if (s.ctl == "none") Walk = false;
                if (!string.IsNullOrEmpty(s.cam))
                {
                    if (s.cam == "return") { CamTarget = "player"; CamZoom = 1f; }
                    else if (!string.IsNullOrEmpty(s.camTo)) CamTarget = s.camTo;
                    if (s.zoom > 0f) CamZoom = s.zoom;
                    if (s.camTime > 0f) CamTime = s.camTime;
                    if (s.shake > 0f) ShakeRequest = System.Math.Max(ShakeRequest, s.shake);
                }
                if (!string.IsNullOrEmpty(s.text)) { LineText = s.text; LineStyle = s.style; lineUntil = s.t + s.lineDur; }
            }
        }

        /// <summary>건너뛰기: 끝까지 가서 남은 단계(마지막 카메라 복귀 포함)를 모두 적용한다. 보상·세계 변화는 다른 코드가 이미 처리</summary>
        public void Skip()
        {
            Time = Data.duration;
            Apply(Data.duration + 1f);
            SfxPending.Clear();                   // 건너뛰면 남은 효과음은 틀지 않는다
            Walk = false; LineText = "";          // 건너뛰면 대사도 지운다
            CamTarget = "player"; CamZoom = 1f;   // 항상 플레이어로 돌아온다(마지막 단계가 return 이 아니어도 안전)
        }
    }
}
