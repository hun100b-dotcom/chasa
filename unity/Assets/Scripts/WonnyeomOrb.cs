// =============================================================================
// WonnyeomOrb.cs — 넋두리가 던지는 원념 탄. 직선으로 날아가 플레이어에 닿으면 던진 혼의 피해로 맞춘다. 최대 사거리에서 사라진다.
//   회피(구르기 무적)·피해 계산은 던진 혼의 onHitPlayer 가 기존 경로(JudgeSystem)로 처리한다. 모양은 아트 fx_wonnyeom_orb.glb(없으면 보랏빛 구).
//   (사슬로 쳐내기는 아직 없음 — 후속)
// =============================================================================
using UnityEngine;

public class WonnyeomOrb : MonoBehaviour
{
    Enemy owner; Vector3 dir; float left;
    const float HitRadius = 0.85f;

    public static WonnyeomOrb Spawn(Vector3 at, Vector3 dir, Enemy owner)
    {
        var g = new GameObject("WonnyeomOrb");
        g.transform.position = at;
        var o = g.AddComponent<WonnyeomOrb>();
        o.owner = owner; o.dir = new Vector3(dir.x, 0f, dir.z).normalized; o.left = Balance.SOULTYPE_WAIL_ORB_RANGE_M;
        var col = new Color(0.69f, 0.31f, 0.82f);   // #B04FD0 원념 보라(주황은 파혼 전용)
        var prefab = Resources.Load<GameObject>("Models/Fx/fx_wonnyeom_orb");
        if (prefab != null)
        {
            var m = Instantiate(prefab, g.transform); m.transform.localPosition = Vector3.zero;
            foreach (var r in m.GetComponentsInChildren<Renderer>()) { r.sharedMaterial = U.Unlit(col); r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; }
        }
        else
        {
            var s = GameObject.CreatePrimitive(PrimitiveType.Sphere); Destroy(s.GetComponent<Collider>());
            s.transform.SetParent(g.transform, false); s.transform.localScale = Vector3.one * 0.5f; s.GetComponent<Renderer>().sharedMaterial = U.Unlit(col);
        }
        return o;
    }

    void Update()
    {
        float step = Balance.SOULTYPE_WAIL_ORB_SPEED * Time.deltaTime;
        transform.position += dir * step; left -= step;
        var p = Enemy.LastPlayer; var d = new Vector2(p.x - transform.position.x, p.z - transform.position.z);
        if (d.magnitude <= HitRadius)
        {
            if (owner != null) owner.onHitPlayer?.Invoke();
            Destroy(gameObject); return;
        }
        if (left <= 0f) Destroy(gameObject);
    }
}
