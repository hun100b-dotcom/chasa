// =============================================================================
// ChasaWater.shader — 개울물 (내장 렌더 파이프라인, 표면 셰이더)
// 하는 일: 물 그림(알파=투명도)을 흐름 방향으로 흘리고, 한 겹을 더 느리게·다른 크기로 겹쳐 흐름이 살아 보이게 한다.
// 왜 노멀 맵을 안 쓰나? 땅 메시에 접선(표면 방향 기준축) 정보가 없어 웹 빌드에서 결이 틀어질 수 있어서, 우선 색 그림 두 겹으로만 만든다.
// 반사는 거칠기 0.06 에 맞춰 Blinn-Phong 반짝임을 약간 준다.
// =============================================================================
Shader "Chasa/Water"
{
    Properties
    {
        _MainTex ("물 그림 (RGBA)", 2D) = "white" {}
        _TileM ("타일 크기 m", Float) = 4
        _Flow ("흐름 방향 xz × 속도 m/s", Vector) = (0, -0.7, 0, 0)
        _Tint ("색 곱", Color) = (1, 1, 1, 1)
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent" }
        CGPROGRAM
        #pragma surface surf BlinnPhong alpha:fade
        #pragma target 3.0

        sampler2D _MainTex;
        float _TileM;
        float4 _Flow, _Tint;

        struct Input { float3 worldPos; };

        void surf (Input IN, inout SurfaceOutput o)
        {
            float2 uv = IN.worldPos.xz / _TileM;
            float2 f = _Flow.xy / _TileM;
            fixed4 a = tex2D(_MainTex, uv + f * _Time.y);                              // 앞 겹: 흐름 속도 그대로
            fixed4 b = tex2D(_MainTex, uv * 0.63 + float2(0.31, 0.17) + f * 0.55 * _Time.y);   // 뒷 겹: 더 크고 더 느리게
            fixed4 c = lerp(a, b, 0.4);
            o.Albedo = c.rgb * _Tint.rgb;
            o.Alpha = c.a * _Tint.a;
            o.Specular = 0.6; o.Gloss = 0.8;
        }
        ENDCG
    }
    FallBack "Transparent/Diffuse"
}
