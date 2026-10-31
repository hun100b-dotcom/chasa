// =============================================================================
// FxMesh.cs — 처결(천도·파혼) 이펙트 3D 모델(GLB) 연결.
// 아트팀 모델 9종: 천도 빛기둥·고리, 파혼 파편 3종, 얼룩 장판, 대기 고리 3종.
// 모델을 불러와 조명 없는 단색 재질(U.Unlit)로 바꿔 입히고, 커졌다 사라지는 움직임만 코드로 준다.
// 모델이 없으면 조용히 건너뛴다(기존 효과가 그대로 보인다).
// =============================================================================
using UnityEngine;

public class FxMesh : MonoBehaviour
{
    float life, t, startScale, endScale, rise;
    Vector3 baseScale;

    /// <summary>모델 한 개를 불러 tint 색의 단색으로 바꿔 놓는다. 없으면 null</summary>
    public static GameObject Spawn(string file, Vector3 pos, float size, Color? tint = null, Transform parent = null)
    {
        var prefab = Resources.Load<GameObject>("Models/Fx/" + file);
        if (prefab == null) return null;
        var go = Instantiate(prefab, parent);
        go.name = file;
        go.transform.position = pos;
        go.transform.localScale = Vector3.one * size;
        foreach (var r in go.GetComponentsInChildren<Renderer>())
        {
            var src = r.sharedMaterials; var dst = new Material[src.Length];
            for (int i = 0; i < src.Length; i++)
                dst[i] = U.Unlit(tint ?? Props3D.MatColor(src[i]));   // 색을 안 정하면 모델 원래 색
            r.sharedMaterials = dst;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;   // 빛 이펙트는 그림자를 안 드리운다
            r.receiveShadows = false;
        }
        return go;
    }

    /// <summary>한 번 터지고 사라지는 효과. 커지는 배율(from→to)과 위로 뜨는 거리(rise)를 준다</summary>
    public static void Burst(string file, Vector3 pos, float size, float seconds, float from, float to, float rise = 0f, Color? tint = null, float yaw = 0f)
    {
        var go = Spawn(file, pos, size, tint);
        if (go == null) return;
        go.transform.rotation = Quaternion.Euler(0, yaw, 0);
        var fx = go.AddComponent<FxMesh>();
        fx.life = seconds; fx.startScale = from; fx.endScale = to; fx.rise = rise; fx.baseScale = go.transform.localScale;
        fx.Tick(0f);
    }

    void Update() { Tick(Time.deltaTime); }

    void Tick(float dt)
    {
        t += dt;
        float k = Mathf.Clamp01(t / Mathf.Max(0.01f, life));
        // 처음엔 빨리 커지고(ease-out: 끝에서 느려짐) 뒤로 갈수록 작아져 사라진다
        float grow = 1f - (1f - k) * (1f - k);
        float s = Mathf.Lerp(startScale, endScale, grow) * (k < 0.6f ? 1f : Mathf.Lerp(1f, 0f, (k - 0.6f) / 0.4f));
        transform.localScale = baseScale * Mathf.Max(0.001f, s);
        transform.position += Vector3.up * (rise * dt / Mathf.Max(0.01f, life));
        if (k >= 1f) Destroy(gameObject);
    }
}
