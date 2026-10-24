// =============================================================================
// TimedSprite.cs — 잠깐 서 있다 사라지는 그림 한 장(드롭 빛줄기 등). 위아래로 살짝 떠다니다 끝에서 투명해진다.
// =============================================================================
using UnityEngine;

public class TimedSprite : MonoBehaviour
{
    float t, life; Vector3 basePos; SpriteRenderer sr;

    public static void Spawn(string name, Vector3 at, float life)
    {
        var s = SpriteLib.Get(name);
        if (s == null) return;   // 그림이 없으면 조용히 건너뜀
        var a = ActorSprite.Create(null, null);
        a.Show(name, Vector3.right);
        var ts = a.gameObject.AddComponent<TimedSprite>();
        ts.life = life; ts.basePos = new Vector3(at.x, 0f, at.z) + Vector3.up * ActorSprite.Lift;
        ts.sr = a.GetComponent<SpriteRenderer>();
        a.transform.position = ts.basePos;
    }

    void Update()
    {
        t += Time.unscaledDeltaTime;
        if (t >= life) { Destroy(gameObject); return; }
        transform.position = basePos + Vector3.up * (0.15f * Mathf.Sin(t * 4f));   // 둥실
        float fade = Mathf.Clamp01((life - t) / 0.8f);
        sr.color = new Color(1f, 1f, 1f, fade);
    }
}
