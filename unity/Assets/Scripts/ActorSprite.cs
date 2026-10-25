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
    ActorModel model;                  // 새 화면(?v=3d)에서는 그림 대신 3D 대역 인형을 쓴다
    public const float Lift = 0.16f;   // 발 아래 9% 가 땅 아래로 내려가 깊이 검사에 잘리는 것을 막는 높이(m)

    public static ActorSprite Create(Transform parent, Camera cam, bool actor = false)
    {
        var go = new GameObject("Sprite");
        go.transform.SetParent(parent, false);
        var a = go.AddComponent<ActorSprite>();
        a.sr = go.AddComponent<SpriteRenderer>();
        a.cam = cam;   // null 이면 Camera.main 을 쓴다
        if (View3D.On && actor) a.model = ActorModel.Create(parent);   // 인형은 그림판과 달리 카메라를 향해 돌지 않아서 부모 밑에 따로 둔다
        go.transform.localPosition = Vector3.up * Lift;   // 그림 판 아랫부분이 땅 속으로 잘리지 않게 살짝 띄운다
        return a;
    }

    /// <summary>손에 든 무기 모델을 바꾼다(주인공 3D 모델에서만 보임)</summary>
    public void SetWeapon(Chasa.Core.WeaponId w) { if (model != null) model.SetWeapon(w); }

    /// <summary>공격 시작을 3D 인형에 알린다(동작을 처음부터, 판정 시각에 맞춰 재생). 2D 그림 쪽은 할 일 없음</summary>
    public void PlayPahon() { if (model != null) model.PlayOneShot(ActorModel.Pose.Pahon); }
    /// <summary>맞은 동작(Hit1·Hit2·Stagger)·천도(Tendo)·파혼(Pahon) 한 번짜리. 모델이 없으면 0(할 일 없음), 있으면 클립 길이(초)</summary>
    public float PlayReact(ActorModel.Pose p) { if (model == null) return 0f; float len = model.ClipLength(p); if (len > 0f) model.PlayOneShot(p); return len; }
    public void PlayDraw() { if (model != null) model.PlayOneShot(ActorModel.Pose.Draw); }
    public void PlayAttack(float windup, float swing, int step = 1) { if (model != null) model.PlayAttack(windup, swing, step); }

    /// <summary>스프라이트를 바꾼다. 없으면(null) 숨기고 false — 부르는 쪽이 색 도형으로 대신한다</summary>
    public bool Show(string name, Vector3 facingDir, Color? tint = null)
    {
        if (model != null)
        {
            sr.enabled = false;
            model.Show(name, facingDir, tint ?? Color.white);
            return true;   // 부르는 쪽이 색 도형을 숨기도록 '그림이 있다'고 알린다
        }
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

    public void Hide() { sr.enabled = false; if (model != null) model.gameObject.SetActive(false); }

    void LateUpdate()
    {
        var c = Cam;
        if (c != null && model == null) transform.rotation = c.transform.rotation;   // 부모가 돌아도 항상 화면을 정면으로
    }
}
