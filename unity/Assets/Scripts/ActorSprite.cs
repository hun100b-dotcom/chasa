// =============================================================================
// ActorSprite.cs — 3D 월드 위에 서 있는 '그림 한 장' (빌보드).
// 빌보드 = 항상 카메라를 정면으로 바라보는 판. 쿼터뷰에서 캐릭터 그림이 납작해 보이지 않게 한다.
// 좌우: 그림은 한쪽만 그렸으므로 화면 기준 왼쪽을 볼 때는 flipX(좌우 뒤집기)로 처리한다(아트 규격 ⑤).
// =============================================================================
using UnityEngine;

public class ActorSprite : MonoBehaviour
{
    public Camera cam;
    SpriteRenderer sr;

    public static ActorSprite Create(Transform parent, Camera cam)
    {
        var go = new GameObject("Sprite");
        go.transform.SetParent(parent, false);
        var a = go.AddComponent<ActorSprite>();
        a.sr = go.AddComponent<SpriteRenderer>();
        a.cam = cam;   // null 이면 Camera.main 을 쓴다
        return a;
    }

    /// <summary>스프라이트를 바꾼다. 없으면(null) 숨기고 false — 부르는 쪽이 색 도형으로 대신한다</summary>
    public bool Show(string name, Vector3 facingDir, Color? tint = null)
    {
        var s = SpriteLib.Get(name);
        sr.enabled = s != null;
        if (s == null) return false;
        sr.sprite = s;
        sr.color = tint ?? Color.white;
        var c = Cam;
        if (c != null) sr.flipX = Vector3.Dot(facingDir, c.transform.right) < 0f;   // 보는 방향이 화면 왼쪽이면 뒤집는다
        return true;
    }

    Camera Cam { get { if (cam == null) cam = Camera.main; return cam; } }

    public void Hide() { sr.enabled = false; }

    void LateUpdate()
    {
        var c = Cam;
        if (c != null) transform.rotation = c.transform.rotation;   // 부모가 돌아도 항상 화면을 정면으로
    }
}
