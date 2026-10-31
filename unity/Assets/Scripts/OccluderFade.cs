// =============================================================================
// OccluderFade.cs — 카메라와 주인공 사이를 가리는 큰 물체(서낭나무 잎 등)를 투명하게 비켜 준다.
//
// 왜 필요한가? 원근 카메라로 내려다보면 키 큰 나무 잎이 주인공 머리 위를 덮어 버린다
//   (PC 비교영상에서 천도 시전 중 주인공이 거의 안 보였음). 쿼터뷰 액션 시점의 기본 처방은 "가리면 치운다".
// 어떻게? 카메라 정면 선(= 주인공을 보는 선) 위에서 잎 덩이의 중심이 가까우면, 잎을 그림에서만 빼고
//   (ShadowsOnly = 모습은 숨기되 그림자는 그대로) 줄기와 그림자는 남겨 나무가 사라진 느낌이 안 나게 한다.
//   (반투명 재질은 새 머티리얼 파일이 필요해서 지금은 '숨김'으로 대체. 나중에 Fade 재질로 교체 가능)
// =============================================================================
using UnityEngine;

public class OccluderFade : MonoBehaviour
{
    public float radius = 2.4f;      // 이 거리 안에 카메라 선이 지나가면 가린 것으로 본다(m)
    public float centerHeight = 3.8f;   // 가림 판정에 쓰는 중심 높이(m). 서낭나무 잎 3.8, 지붕 조각은 약 3.2
    Renderer[] rs;
    bool hidden;

    void Awake() { rs = GetComponentsInChildren<Renderer>(); }

    void LateUpdate()
    {
        var cam = Camera.main; if (cam == null || rs == null) return;
        // 카메라에서 정면으로 뻗은 선과 이 물체 중심 사이 거리 (주인공은 화면 중앙 근처에 있으므로 정면선으로 근사)
        Vector3 o = cam.transform.position, d = cam.transform.forward;
        Vector3 c = transform.position + Vector3.up * centerHeight;          // 가리는 덩이의 중심 높이
        float along = Vector3.Dot(c - o, d);
        float dist = (c - (o + d * along)).magnitude;
        // 카메라와 초점 사이에 있고(along < 초점 거리 + 여유) 선에 가까우면 가림
        bool block = along > 0f && along < View3D.Distance + 2f && dist < radius;
        // 깜빡임 방지: 숨길 땐 radius, 다시 보일 땐 조금 더 멀어져야(여유 0.6m)
        if (hidden) block = along > 0f && along < View3D.Distance + 2f && dist < radius + 0.6f;
        if (block == hidden) return;
        hidden = block;
        foreach (var r in rs)
        {
            if (r.name.StartsWith("Trunk") || r.name == "Rope") continue;   // 줄기·금줄은 항상 보임
            r.shadowCastingMode = hidden ? UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly
                                         : UnityEngine.Rendering.ShadowCastingMode.On;
            r.forceRenderingOff = hidden;                                    // 그림에서만 끄기
        }
    }
}
