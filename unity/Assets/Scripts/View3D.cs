// =============================================================================
// View3D.cs — "새 화면(3D 느낌)"과 "옛 화면(2D 그림 + 직교 카메라)"을 가르는 스위치와 카메라 안.
//
// 왜 스위치인가? 오너가 두 화면을 나란히 비교 영상으로 보고 고르기로 했다(C안).
//   그래서 옛 화면은 그대로 두고, 주소 끝에 ?v=3d 를 붙였을 때만 새 화면을 켠다.
//   ?cam=a|b|c 로 카메라 3안을 고른다 (없으면 a).
// 용어: 원근 카메라(perspective) = 가까운 건 크게 먼 건 작게 보이는 카메라(사람 눈과 같음).
//       직교 카메라(orthographic) = 멀어도 크기가 같음(보드게임판 같은 옛 쿼터뷰).
//       FOV = 카메라가 보는 각도(좁을수록 망원경처럼 납작해짐).
// =============================================================================
using UnityEngine;

public static class View3D
{
    public static bool On;                 // 새 화면 켜짐
    public static CamVariant Cam;          // 고른 카메라 안

    public struct CamVariant
    {
        public string Id; public float PitchDeg, ViewHeight, Fov;
        public CamVariant(string id, float pitch, float viewH, float fov) { Id = id; PitchDeg = pitch; ViewHeight = viewH; Fov = fov; }
    }

    // 카메라 안: 내려다보는 각도 / 플레이어 위치에서 화면 세로가 보여 주는 높이(m) / 시야각
    //   A: 영상 속 쿼터뷰 액션 시점에 가장 가깝게(가깝고 깊게 내려다봄)  B: 조금 멀고 완만  C: 더 가깝고 더 가파름
    public static readonly CamVariant[] Variants =
    {
        new CamVariant("a", 50f, 11.5f, 35f),
        new CamVariant("b", 45f, 12.5f, 30f),
        new CamVariant("c", 55f, 10.5f, 40f),
    };

    /// <summary>시작할 때 한 번: 주소(URL)를 읽어 켜짐 여부와 카메라 안을 정한다</summary>
    public static void Init()
    {
        string url = (Application.absoluteURL ?? "").ToLowerInvariant();
        // 오너 결정(10-24): 3D 가 본 화면. 주소에 v=2d 가 있을 때만 옛 2D 화면(정리 대상), v=3d 는 명시적으로 3D
        On = url.Contains("v=2d") ? false : url.Contains("v=3d") ? true : Balance.VIEW_3D_DEFAULT;
        Cam = Variants[0];
        foreach (var v in Variants) if (url.Contains("cam=" + v.Id)) Cam = v;
    }

    /// <summary>원근 카메라에서 화면 세로가 H(m)가 되는 거리 = H / (2·tan(FOV/2))</summary>
    public static float Distance { get { return Cam.ViewHeight / (2f * Mathf.Tan(Cam.Fov * 0.5f * Mathf.Deg2Rad)); } }

    // 새 화면의 밤 색감 (안개와 배경이 같은 색이라 땅 끝의 '빈 남색 띠'가 안개 속으로 사라진다)
    public static readonly Color FogColor = new Color(0.05f, 0.06f, 0.11f);
}
