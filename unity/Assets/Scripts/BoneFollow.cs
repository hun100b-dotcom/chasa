// =============================================================================
// BoneFollow.cs — 뼈대 없는 정지 조각(장비 외형)이 뼈를 따라 움직이게 한다.
// 원리: 붙이는 순간의 뼈 위치(처음 자세)를 기억한다 → 매 프레임 "뼈가 처음 자세에서 얼마나 움직였나"를 조각의 처음 자리에 곱한다.
// 왜 부모를 뼈로 바꾸지 않나? 조각은 주인공과 같은 좌표(처음 자세)로 만들어져 있어서, 뼈의 자식으로 넣으면 한 번 옮겨 맞추는 계산이 더 필요하다.
// =============================================================================
using UnityEngine;

public class BoneFollow : MonoBehaviour
{
    Transform bone; Matrix4x4 restInv, rest;

    public void Setup(Transform b)
    {
        bone = b;
        restInv = b.worldToLocalMatrix;              // 처음 자세의 뼈 → 월드 변환의 역
        rest = transform.localToWorldMatrix;         // 조각의 처음 월드 자리
    }

    void LateUpdate()
    {
        if (bone == null) return;
        var m = bone.localToWorldMatrix * restInv * rest;
        transform.SetPositionAndRotation(m.GetColumn(3), Quaternion.LookRotation(m.GetColumn(2), m.GetColumn(1)));
    }
}
