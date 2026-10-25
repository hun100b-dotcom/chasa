// =============================================================================
// CutscenePlayer.cs — 실시간 컷신을 화면에 연결한다 (카메라 이동·확대·대사·입력 잠금·건너뛰기).
// 시간표 규칙은 Core/Cutscene(CutPlayback). 대본은 Resources/Data/cutscenes_b01.json (서사 원본 → tools/build_cutscene_data.py).
// 컷신은 '게임을 멈추는 영상'이 아니라 같은 세계 위에서 카메라만 연출하는 방식이다(손맛·몰입이 끊기지 않게).
// 잠금 컷은 입력을 막고 적을 멈추며, 길게(1초) 누르면 건너뛴다. 건너뛰어도 보상·세계 변화는 이미 코드가 처리해 그대로다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class CutscenePlayer
{
    [System.Serializable] class FileData { public CutData[] cuts; }

    readonly Dictionary<string, CutData> byId = new Dictionary<string, CutData>();
    readonly HashSet<string> playedOnce = new HashSet<string>();
    CutPlayback cur;
    float holdSkip;                          // 건너뛰기 버튼을 누르고 있는 시간

    public string CurId { get { return cur != null ? cur.Data.id : ""; } }          // 자동 플레이 테스트가 본다
    public float CurDuration { get { return cur != null ? cur.Data.duration : 0f; } }
    public bool Active { get { return cur != null && !cur.Done; } }
    /// <summary>입력을 막아야 하나 (잠금 컷 재생 중)</summary>
    public bool InputLocked { get { return Active && cur.Data.@lock && !cur.Walk; } }   // 서사 control=walk 구간은 잠금이 풀려 걸을 수 있다
    /// <summary>적을 멈춰야 하나</summary>
    /// <summary>시계를 세워야 하나 (오프닝 컷 20초 동안만 월드 시계가 멈춘다 — 서사 확정)</summary>
    public bool PauseClock { get { return Active && cur.Data.id == "OPENING"; } }
    /// <summary>오프닝의 검은 화면 가림 정도 0~1 (처음 8초는 완전히 검고, 그 뒤 10초에 걸쳐 걷힌다)</summary>
    public float OpeningBlack
    {
        get
        {
            if (!PauseClock) return 0f;
            float t = cur.Time;   // 서사 오프닝 C-01 시간표: 0~3 검정 / 3~4.5 아주 어둡게 밝아짐 / 10~13 물에 잠김 / 13~15 어둠 / 15~18 손목 / 18~19 컷 / 이후 검정
            if (t < 3f) return 1f;
            if (t < 4.5f) return Mathf.Lerp(1f, 0.55f, (t - 3f) / 1.5f);
            if (t < 10f) return 0.55f;
            if (t < 13f) return Mathf.Lerp(0.55f, 0.8f, (t - 10f) / 3f);
            if (t < 13.5f) return Mathf.Lerp(0.8f, 1f, (t - 13f) / 0.5f);
            if (t < 15f) return 1f;
            if (t < 18f) return 0.88f;
            return 1f;
        }
    }
    /// <summary>지금 컷이 정한 장면 날씨(소문자 영문 이름). 컷이 없거나 정하지 않았으면 null</summary>
    public string SceneWeather { get { return Active ? cur.SceneWeather : null; } }
    public bool PauseEnemies { get { return Active && cur.Data.pause; } }
    public string CamTarget { get { return Active ? cur.CamTarget : "player"; } }
    public float CamZoom { get { return Active ? cur.CamZoom : 1f; } }
    public float CamTime { get { return cur != null ? cur.CamTime : 0.3f; } }
    public float SkipProgress { get { return Active && cur.Data.skippable ? Mathf.Clamp01(holdSkip / 1f) : 0f; } }
    public bool LineVisible { get { return Active && cur.LineVisible; } }
    public string LineText { get { return cur != null ? cur.LineText : ""; } }
    public string LineStyle { get { return cur != null ? cur.LineStyle : ""; } }
    /// <summary>이번 프레임 새 흔들림 요청(읽으면 지워진다)</summary>
    public float TakeShake() { if (cur == null) return 0f; float s = cur.ShakeRequest; cur.ShakeRequest = 0f; return s; }

    public CutscenePlayer()
    {
        var ta = Resources.Load<TextAsset>("Data/cutscenes_b01");
        if (ta == null) return;
        var f = JsonUtility.FromJson<FileData>(ta.text);
        if (f != null && f.cuts != null) foreach (var c in f.cuts) byId[c.id] = c;
        // 서사 첫 세션 대본(오프닝·장례): 있으면 코드 속 임시 장면보다 우선(Add 는 이미 있는 id 를 건드리지 않는다)
        var fs = Resources.Load<TextAsset>("Data/cutscenes_first_session");
        if (fs != null) { var f2 = JsonUtility.FromJson<FileData>(fs.text); if (f2 != null && f2.cuts != null) foreach (var c in f2.cuts) byId[c.id] = c; }
        AddBuiltIn();
    }

    /// <summary>
    /// 서사 대본 파일에는 없는 장면(첫 세션 오프닝·박돌쇠 장례)을 코드로 만든다. 서사 첫 세션 흐름의 장면 길이를 그대로 따랐고,
    /// 글자는 장면 설명 이상으로 지어내지 않았다(대사는 서사팀 몫). 대본이 오면 데이터 파일 쪽 같은 id 가 이 값을 덮어쓴다.
    /// </summary>
    void AddBuiltIn()
    {
        Add(new CutData { id = "OPENING", duration = 20f, @lock = true, pause = true, skippable = true, steps = new[] {
            new CutStep { t = 0f, cam = "hold", camTo = "player", zoom = 1.35f, camTime = 1f },
            new CutStep { t = 16f, cam = "return", camTime = 1.5f } } });
        Add(new CutData { id = "FUNERAL_TENDO", duration = 70f, @lock = true, skippable = true, steps = new[] {
            new CutStep { t = 0f, cam = "pan", camTo = "funeral", camTime = 2f, zoom = 1.2f, text = "박돌쇠의 장례", style = "bubble", lineDur = 4f },
            new CutStep { t = 66f, cam = "return", camTime = 2f } } });
        Add(new CutData { id = "FUNERAL_NONE", duration = 20f, @lock = false, skippable = true, steps = new[] {
            new CutStep { t = 0f, cam = "pan", camTo = "funeral", camTime = 1.5f, text = "상이 아직 없다", style = "bubble", lineDur = 4f },
            new CutStep { t = 18f, cam = "return", camTime = 1.5f } } });
    }
    void Add(CutData d) { if (!byId.ContainsKey(d.id)) byId[d.id] = d; }


    /// <summary>컷 재생 시작. once 면 한 번만(이미 봤으면 false). 이미 다른 잠금 컷 중이면 시작하지 않는다</summary>
    public bool Play(string id, bool once = false)
    {
        CutData d;
        if (!byId.TryGetValue(id, out d)) return false;
        if (once && !playedOnce.Add(id)) return false;
        if (InputLocked && !d.@lock) return false;     // 잠금 컷 중엔 가벼운 컷(대사 하나)이 끼어들지 않는다
        cur = new CutPlayback(d); holdSkip = 0f;
        return true;
    }

    void DrainSfx() { if (cur != null) while (cur.SfxPending.Count > 0) Sfx.Play(cur.SfxPending.Dequeue()); }   // 서사 대본의 효과음을 그 시각에 튼다

    public void Tick(float dt)
    {
        DrainSfx();   // 방금 시작한 컷의 0초 소리·직전 프레임에 끝난 컷의 마지막 소리
        if (!Active) return;
        cur.Tick(dt);
        DrainSfx();
        // 길게 누르면 건너뛴다: Space·Esc·마우스·터치 중 무엇이든 1초
        if (cur.Data.skippable)
        {
            bool held = Input.GetKey(KeyCode.Space) || Input.GetKey(KeyCode.Escape) || Input.GetMouseButton(0) || Input.touchCount > 0;
            holdSkip = held ? holdSkip + dt : 0f;
            if (holdSkip >= 1f) { cur.Skip(); holdSkip = 0f; }
        }
    }
}
