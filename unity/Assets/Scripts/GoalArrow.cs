// =============================================================================
// GoalArrow.cs — 목표 화살표 (기획 first-10min M12)
// 명부에 오른 이름혼(미니맵의 청록 점)이 화면 밖이면, 그쪽 가장자리에 금색 작은 화살표와 거리(m)를 띄운다.
// 왜: 미니맵을 볼 줄 모르는 사람도 '어디로 가야 하나'를 화면 가장자리에서 바로 안다. 화면 안이면 안 보인다.
// =============================================================================
using System.Collections.Generic;
using Chasa.Core;
using UnityEngine;

public class GoalArrow : MonoBehaviour
{
    public JudgeSystem judge;
    readonly List<KeyValuePair<Vector3, string>> tmp = new List<KeyValuePair<Vector3, string>>();
    GUIStyle st;

    void OnGUI()
    {
        if (judge == null || judge.named == null || judge.InDay || judge.NightOver || MiniMap.BigOpen || CharacterPanel.Open || SettingsPanel.Open || DosulCards.Open) return;
        var cam = Camera.main; if (cam == null) return;
        tmp.Clear(); judge.named.PendingPositions(tmp);
        Vector3 best = default(Vector3); float bd = float.MaxValue; bool has = false;
        foreach (var c in tmp)
        {
            if (judge.NamedMarkerHidden(c.Value)) continue;
            float d = new Vector2(c.Key.x - judge.player.Pos.x, c.Key.z - judge.player.Pos.z).magnitude;
            if (d < bd) { bd = d; best = c.Key; has = true; }
        }
        if (!has || bd < 6f) return;
        var sp = cam.WorldToScreenPoint(new Vector3(best.x, 1f, best.z));
        float margin = 48f;
        bool onScreen = sp.z > 0f && sp.x > margin && sp.x < Screen.width - margin && sp.y > margin && sp.y < Screen.height - margin;
        if (onScreen) return;
        // 화면 가운데에서 목표 쪽 방향을 가장자리(여백 margin)까지 늘린다. 카메라 뒤(z<0)면 방향을 뒤집는다
        var cen = new Vector2(Screen.width * 0.5f, Screen.height * 0.5f); var dir = new Vector2(sp.x, sp.y) - cen; if (sp.z < 0f) dir = -dir;
        if (dir.sqrMagnitude < 1f) dir = Vector2.up; dir.Normalize();
        float tx = dir.x != 0f ? (Screen.width * 0.5f - margin) / Mathf.Abs(dir.x) : float.MaxValue, ty = dir.y != 0f ? (Screen.height * 0.5f - margin) / Mathf.Abs(dir.y) : float.MaxValue;
        var pos = cen + dir * Mathf.Min(tx, ty);
        float k = Mathf.Clamp(Screen.height / 1080f, 0.7f, 1.4f);
        var arrow = First10.Tex("goal_arrow"); var plate = First10.Tex("goal_dist_plate");
        float ang = -Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;   // 그림은 오른쪽을 향한다. 화면 y 는 아래가 +라 부호를 뒤집는다
        var m = GUI.matrix;
        GUIUtility.RotateAroundPivot(ang, new Vector2(pos.x, Screen.height - pos.y));
        var ar = new Rect(pos.x - 12f * k, Screen.height - pos.y - 12f * k, 24f * k, 24f * k);
        if (arrow != null) GUI.DrawTexture(ar, arrow);
        else { var old = GUI.color; GUI.color = new Color(1f, 0.82f, 0.3f); GUI.DrawTexture(ar, Texture2D.whiteTexture); GUI.color = old; }
        GUI.matrix = m;
        // 거리 글자: 화살표 안쪽(가운데 쪽)에
        var tp = pos - dir * 30f * k;
        var pr = new Rect(tp.x - 32f * k, Screen.height - tp.y - 11f * k, 64f * k, 22f * k);
        if (plate != null) GUI.DrawTexture(pr, plate);
        Ko.Apply();
        if (st == null) st = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
        st.fontSize = Mathf.RoundToInt(13 * k); st.normal.textColor = new Color(1f, 0.9f, 0.55f);
        GUI.Label(pr, Mathf.RoundToInt(bd) + " m", st);
    }
}
