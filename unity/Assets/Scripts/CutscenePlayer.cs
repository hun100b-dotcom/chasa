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

    public bool Active { get { return cur != null && !cur.Done; } }
    /// <summary>입력을 막아야 하나 (잠금 컷 재생 중)</summary>
    public bool InputLocked { get { return Active && cur.Data.@lock; } }
    /// <summary>적을 멈춰야 하나</summary>
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
    }

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

    public void Tick(float dt)
    {
        if (!Active) return;
        cur.Tick(dt);
        // 길게 누르면 건너뛴다: Space·Esc·마우스·터치 중 무엇이든 1초
        if (cur.Data.skippable)
        {
            bool held = Input.GetKey(KeyCode.Space) || Input.GetKey(KeyCode.Escape) || Input.GetMouseButton(0) || Input.touchCount > 0;
            holdSkip = held ? holdSkip + dt : 0f;
            if (holdSkip >= 1f) { cur.Skip(); holdSkip = 0f; }
        }
    }
}
