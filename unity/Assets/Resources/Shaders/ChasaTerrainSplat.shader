// =============================================================================
// ChasaTerrainSplat.shader — 땅 재질 섞기(스플랫맵) 셰이더 (내장 렌더 파이프라인, 표면 셰이더)
// 하는 일: 땅 한 장(메쉬)에 흙·풀·자갈·논·낙엽 5가지 타일 그림을 '재질 섞기 지도'의 비율대로 섞어 칠한다.
//   _SplatA (R=흙 G=풀 B=자갈 A=논), _SplatB (R=낙엽) : 월드 전체(_WorldSize m)를 덮는 지도. 비율은 합이 1이 되게 코드에서 맞춘다.
//   _T0.._T4 : 층별 타일 그림(이음매 없이 반복되는 것). _TileM0.._TileM4 : 타일 한 장이 덮는 실제 길이(m).
// 왜 월드 좌표로 칠하나? 청크(128m 조각)마다 메쉬가 나뉘어도 이음매 없이 같은 무늬가 이어지게.
// 지도가 하나도 칠하지 않은 자리(합 0)는 풀로 둔다. 조명은 Lambert(무광) — 프로젝트 전체가 무광 재질이다.
// =============================================================================
Shader "Chasa/TerrainSplat"
{
    Properties
    {
        _SplatA ("Splat A (흙/풀/자갈/논)", 2D) = "red" {}
        _SplatB ("Splat B (낙엽)", 2D) = "black" {}
        _T0 ("흙", 2D) = "white" {}
        _T1 ("풀", 2D) = "white" {}
        _T2 ("자갈", 2D) = "white" {}
        _T3 ("논", 2D) = "white" {}
        _T4 ("낙엽", 2D) = "white" {}
        _TileM ("타일 크기 m (흙,풀,자갈,논)", Vector) = (6, 6, 6, 6)
        _TileM4 ("낙엽 타일 크기 m", Float) = 6
        _WorldSize ("지도가 덮는 한 변 m", Float) = 640
        _SplatRect ("지도 원점 xz, 크기 xz (m) — 2막은 직사각·원점이 있다", Vector) = (0, 0, 640, 640)
        _Tint0 ("흙 색 곱", Color) = (1,1,1,1)
        _Tint1 ("풀 색 곱", Color) = (1,1,1,1)
        _Tint2 ("자갈 색 곱", Color) = (1,1,1,1)
        _Tint3 ("논 색 곱", Color) = (1,1,1,1)
        _Tint4 ("낙엽 색 곱", Color) = (1,1,1,1)
        _D0 ("잔무늬 흙", 2D) = "gray" {}
        _D1 ("잔무늬 풀", 2D) = "gray" {}
        _D2 ("잔무늬 자갈", 2D) = "gray" {}
        _D3 ("잔무늬 논", 2D) = "gray" {}
        _D4 ("잔무늬 낙엽", 2D) = "gray" {}
        _DetailTileM ("잔무늬 타일 m", Float) = 1.5
        _CloudTex ("구름 그림자 (흑백, 200m 반복)", 2D) = "white" {}
        _CloudAmount ("구름 그림자 세기 (0=끔)", Float) = 0
        _CloudScroll ("구름 흐름 속도 m/s xz", Vector) = (1.2, 0.4, 0, 0)
        _DetailAmount ("잔무늬 세기 (0=끔)", Float) = 0
        _DetailNear ("잔무늬 완전히 보이는 거리 m", Float) = 18
        _DetailFar ("잔무늬 사라지는 거리 m", Float) = 32
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "Queue" = "Geometry" }
        CGPROGRAM
        #pragma surface surf Lambert fullforwardshadows
        #pragma target 3.0

        // 텍스처 13장을 각자 샘플러로 읽으면 샘플러 16개 한도를 넘어(웹/GLES3 빌드 오류) 샘플러는 _T0 하나를 모두가 나눠 쓴다(텍스처 자체는 따로)
        #include "HLSLSupport.cginc"
        UNITY_DECLARE_TEX2D(_T0);
        UNITY_DECLARE_TEX2D_NOSAMPLER(_SplatA); UNITY_DECLARE_TEX2D_NOSAMPLER(_SplatB);
        UNITY_DECLARE_TEX2D_NOSAMPLER(_T1); UNITY_DECLARE_TEX2D_NOSAMPLER(_T2); UNITY_DECLARE_TEX2D_NOSAMPLER(_T3); UNITY_DECLARE_TEX2D_NOSAMPLER(_T4);
        #define S(tex, uv) UNITY_SAMPLE_TEX2D_SAMPLER(tex, _T0, uv)
        float4 _TileM;
        float _TileM4, _WorldSize; float4 _SplatRect; fixed4 _Tint0, _Tint1, _Tint2, _Tint3, _Tint4;   // 2막은 같은 타일 그림에 색을 곱해 붉은 흙·마른 풀·쇠찌꺼기로 바꾼다
        UNITY_DECLARE_TEX2D_NOSAMPLER(_D0); UNITY_DECLARE_TEX2D_NOSAMPLER(_D1); UNITY_DECLARE_TEX2D_NOSAMPLER(_D2); UNITY_DECLARE_TEX2D_NOSAMPLER(_D3); UNITY_DECLARE_TEX2D_NOSAMPLER(_D4);
        float _DetailTileM, _DetailAmount, _DetailNear, _DetailFar;
        UNITY_DECLARE_TEX2D_NOSAMPLER(_CloudTex); float _CloudAmount; float4 _CloudScroll;

        struct Input { float3 worldPos; };

        void surf (Input IN, inout SurfaceOutput o)
        {
            float2 wxz = IN.worldPos.xz;
            float2 suv = (wxz - _SplatRect.xy) / _SplatRect.zw;
            fixed4 a = S(_SplatA, suv);
            fixed4 b = S(_SplatB, suv);
            float sum = a.r + a.g + a.b + a.a + b.r;
            float4 wa = a; float wb = b.r;
            if (sum < 0.0001) { wa = float4(0, 1, 0, 0); wb = 0; sum = 1; }   // 아무것도 안 칠한 자리 = 풀
            wa /= sum; wb /= sum;
            fixed3 c = S(_T0, wxz / _TileM.x).rgb * _Tint0.rgb * wa.x
                     + S(_T1, wxz / _TileM.y).rgb * _Tint1.rgb * wa.y
                     + S(_T2, wxz / _TileM.z).rgb * _Tint2.rgb * wa.z
                     + S(_T3, wxz / _TileM.w).rgb * _Tint3.rgb * wa.w
                     + S(_T4, wxz / _TileM4).rgb * _Tint4.rgb * wb;
            // 가까울 때(약 18~32m)만 잔무늬(이랑·자갈 알갱이)를 섞는다. 멀리선 큰 타일만 보여 반복 무늬가 덜 티 난다
            if (_DetailAmount > 0.001)
            {
                float k = _DetailAmount * (1.0 - smoothstep(_DetailNear, _DetailFar, distance(IN.worldPos, _WorldSpaceCameraPos)));
                if (k > 0.001)
                {
                    float2 duv = wxz / _DetailTileM;
                    fixed3 d = S(_D0, duv).rgb * wa.x + S(_D1, duv).rgb * wa.y + S(_D2, duv).rgb * wa.z
                             + S(_D3, duv).rgb * wa.w + S(_D4, duv).rgb * wb;
                    c = lerp(c, d, k);   // 잔무늬 평균 명도가 층 그림과 비슷하다고 아트가 맞춰 줌 → 색을 섞어도 밝기가 안 튄다
                }
            }
            // 구름 그림자: 흑백 그림(흰=햇빛, 검=그림자)을 바람 방향으로 천천히 흘려 땅 색에 곱한다
            if (_CloudAmount > 0.001)
            {
                float cs = S(_CloudTex, (wxz + _CloudScroll.xy * _Time.y) / 200.0).r;
                c *= lerp(1.0, lerp(0.55, 1.0, cs), _CloudAmount);
            }
            o.Albedo = c;
        }
        ENDCG
    }
    FallBack "Diffuse"
}
