// =============================================================================
// SettingsPanel.cs — 설정 화면: 소리 크기(전체·배경음·효과음), 화면 흔들림 세기, 조작 키 보기, 저장·불러오기.
// O 키 / 화면 오른쪽 위 "설정" 버튼으로 열고, 열려 있는 동안 세계가 멈춘다(CharacterPanel 과 같은 방식).
// 값은 SaveStore.Settings 한 곳에 있고 Sfx·BgmPlayer·HitFeel 이 거기서 읽는다 → 바꾸면 바로 들린다.
// 슬라이더를 놓을 때(값이 바뀐 뒤 열기/닫기)에 브라우저 저장소에 저장한다.
// =============================================================================
using Chasa.Core;
using UnityEngine;

public class SettingsPanel : MonoBehaviour
{
    public static bool Open;
    public JudgeSystem judge;
    public Texture2D white;
    bool showKeys, dirty, confirmReset;
    string note = "";

    // 조작 키 보기(실제 입력 코드와 같은 키). 폰은 화면 버튼이 대신한다
    static readonly string[] Keys =
    {
        "이동        WASD / 방향키 / 땅을 클릭   (폰: 왼쪽 화면을 눌러 떠다니는 조이스틱)",
        "공격        마우스 왼쪽 클릭(적 쪽으로, 3타 콤보)",
        "피하기      Space",
        "천도        E (무릎 꿇은 혼 가까이)       파혼   R",
        "도술 4칸    1 2 3 4                      Q  철삭=끌어당김(우클릭도) / 육모방망이=땅울림",
        "무기 바꾸기 Tab                           회복약  H     얼룩 지우기  X",
        "넋길        F (서낭당 곁, 밤)",
        "명부(캐릭터) C                            설정   O",
        "소리 켜고 끄기 M                          줌   마우스 휠",
    };

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.O) && !CharacterPanel.Open) Toggle();
        if (Open && Input.GetKeyDown(KeyCode.Escape)) Close();
    }

    public void Toggle() { if (Open) Close(); else { Open = true; showKeys = false; confirmReset = false; note = ""; } }

    void Close()
    {
        Open = false;
        if (dirty) { SaveStore.SaveSettings(); dirty = false; }   // 닫을 때 한 번만 저장(슬라이더를 끄는 동안 저장소를 두들기지 않게)
    }

    void OnGUI()
    {
        Ko.Apply();
        if (judge == null) return;
        var s = SaveStore.Settings;
        GUI.depth = -110;
        if (!Open)
        {
            // 닫혀 있을 땐 오른쪽 위 작은 버튼(소리 버튼 아래). 낮 화면·캐릭터 창·컷신 중엔 숨긴다
            if (judge.InDay || CharacterPanel.Open || judge.cuts.Active) return;
            bool t = Ko.TouchUI;
            if (GUI.Button(new Rect(Mathf.Min(Screen.width, MiniMap.LeftPx > 0f ? MiniMap.LeftPx : Screen.width) - (t ? 104 : 78), t ? 62 : 38, t ? 96 : 70, t ? 48 : 26), "설정")) Toggle();
            return;
        }
        float w = Mathf.Min(Screen.width - 24f, 640f), h = Mathf.Min(Screen.height - 24f, showKeys ? 470f : 460f);
        var box = new Rect((Screen.width - w) / 2f, (Screen.height - h) / 2f, w, h);
        GUI.color = new Color(0.05f, 0.06f, 0.1f, 0.96f); GUI.DrawTexture(box, white); GUI.color = Color.white;
        var title = new GUIStyle(GUI.skin.label) { fontSize = 22, fontStyle = FontStyle.Bold }; title.normal.textColor = ChasaPalette.Hanji;
        var body = new GUIStyle(GUI.skin.label) { fontSize = 16 }; body.normal.textColor = ChasaPalette.Hanji;
        var mono = new GUIStyle(body) { fontSize = 14 };
        float x = box.x + 20, y = box.y + 14;
        GUI.Label(new Rect(x, y, 300, 30), "설정", title);
        if (GUI.Button(new Rect(box.xMax - 100, y, 80, 32), "닫기")) Close();
        y += 46;
        if (!showKeys)
        {
            y = Slider(x, y, box.width - 40, "전체 소리", ref s.Master, 1f, body);
            y = Slider(x, y, box.width - 40, "배경음", ref s.Bgm, 1f, body);
            y = Slider(x, y, box.width - 40, "효과음", ref s.Sfx, 1f, body);
            y = Slider(x, y, box.width - 40, "화면 흔들림", ref s.Shake, 1.5f, body);
            GUI.Label(new Rect(x, y, box.width - 40, 22), "흔들림 0 = 흔들리지 않음(멀미가 나면 줄이세요). 1 = 기본.", new GUIStyle(mono) { fontSize = 13 });
            y += 34;
            if (GUI.Button(new Rect(x, y, 190, 40), "조작 키 보기")) showKeys = true;
            bool field = judge.FieldMode;
            GUI.enabled = field;
            if (GUI.Button(new Rect(x + 200, y, 130, 40), "지금 저장")) note = judge.SaveGameNow() ? "저장했다" : "저장하지 못했다";
            GUI.enabled = field && SaveStore.Exists;
            if (GUI.Button(new Rect(x + 340, y, 130, 40), "불러오기")) { if (judge.LoadGameNow()) { note = "불러왔다"; Close(); } else note = "저장이 없거나 읽지 못했다"; }
            GUI.enabled = true;
            y += 52;
            if (!confirmReset) { if (GUI.Button(new Rect(x, y, 190, 36), "처음부터 (저장 지움)")) confirmReset = true; }
            else
            {
                GUI.Label(new Rect(x, y, 300, 30), "저장을 지우고 다시 켜면 새 게임. 정말?", body);
                if (GUI.Button(new Rect(x + 320, y, 70, 32), "지움")) { SaveStore.Delete(); note = "저장을 지웠다. 새로고침하면 처음부터"; confirmReset = false; }
                if (GUI.Button(new Rect(x + 400, y, 70, 32), "취소")) confirmReset = false;
            }
            y += 44;
            GUI.Label(new Rect(x, y, box.width - 40, 26), note.Length > 0 ? note : "45초마다 안전할 때 자동 저장됩니다(필드에서).", mono);
        }
        else
        {
            foreach (var k in Keys) { GUI.Label(new Rect(x, y, box.width - 40, 26), k, mono); y += 30; }
            y += 6;
            if (GUI.Button(new Rect(x, y, 140, 38), "뒤로")) showKeys = false;
        }
    }

    /// <summary>제목 + 슬라이더 + 숫자 한 줄. 값이 바뀌면 저장할 거라고 표시(dirty)만 한다. 다음 y 를 돌려준다</summary>
    float Slider(float x, float y, float w, string label, ref float v, float max, GUIStyle body)
    {
        GUI.Label(new Rect(x, y, 140, 28), label, body);
        float nv = GUI.HorizontalSlider(new Rect(x + 150, y + 8, w - 150 - 70, 20), v, 0f, max);
        GUI.Label(new Rect(x + w - 60, y, 60, 28), Mathf.RoundToInt(nv / max * 100f) + "%", body);
        if (Mathf.Abs(nv - v) > 1e-4f) { v = nv; dirty = true; if (label == "전체 소리") AudioListener.volume = v; }   // 전체 소리는 바로 반영(나머지는 매 프레임 읽는다)
        return y + 38;
    }
}
