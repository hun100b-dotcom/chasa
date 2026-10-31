// ChasaGrade.shader — 화면 후처리 한 장: 색보정표(LUT) 섞기 + 블룸 더하기 + 비네트 + 천도 시야 축소(먹 번짐·단청 문양·청록 글로우·붉은 위험 호·보라 성공 테두리).
// 패스 0: 밝은 곳만 뽑아 작게 / 1: 가로 흐림 / 2: 세로 흐림 / 3: 최종 합성. 값은 모두 GradingFx.cs 가 매 프레임 넣는다(아트 값표: Data/grading.json).
Shader "Chasa/Grade"
{
    Properties { _MainTex ("화면", 2D) = "white" {} }
    CGINCLUDE
    #include "UnityCG.cginc"
    sampler2D _MainTex; float4 _MainTex_TexelSize;
    sampler2D _Bloom, _L0, _L1, _L2, _L3, _LT, _Noise, _Pattern;
    float4 _W;                       // LUT 4장의 섞는 비율(합 1)
    float _BloomThr, _BloomInt, _BloomScatter; float4 _BloomTint;
    float4 _VigColor; float _VigInt, _VigSmooth;
    float _TendoLut;                 // 천도 LUT 섞는 비율(0~0.6)
    float _TendoK, _Radius, _Aspect, _PatA, _SuccessA; float4 _Center;   // xy = 시야 중심(uv), 천도 중에만 의미 있음
    float4 _G0, _G1;                 // 청록 글로우: xy 위치(uv), z 반지름(키 단위), w 세기
    float4 _D0, _D1, _D2, _D3;       // 붉은 위험 호: x 방향(라디안), y 불투명도, z 반폭(라디안)
    float2 _NoiseScroll; float2 _ScreenPx;
    float4 _GradeCS, _GradeTint;     // 검수용 보정 후보(?grade=b·c): x 대비, y 채도, z 밝기 보탬. tint 는 색 곱. 기본(1,1,0)·(1,1,1)은 아무 일도 안 한다

    // 32×32×32 LUT 가 1024×32 가로 띠: 칸=파랑, 칸 안 가로=빨강, 위쪽=초록 큰 값
    float3 Lut(sampler2D lut, float3 c)
    {
        c = saturate(c);
        float b = c.b * 31.0; float b0 = floor(b); float b1 = min(b0 + 1.0, 31.0); float f = b - b0;
        float y = (c.g * 31.0 + 0.5) / 32.0;
        float2 u0 = float2((b0 * 32.0 + c.r * 31.0 + 0.5) / 1024.0, y);
        float2 u1 = float2((b1 * 32.0 + c.r * 31.0 + 0.5) / 1024.0, y);
        return lerp(tex2D(lut, u0).rgb, tex2D(lut, u1).rgb, f);
    }

    fixed4 fragBright (v2f_img i) : SV_Target
    {
        float3 c = tex2D(_MainTex, i.uv).rgb;
        float l = max(c.r, max(c.g, c.b));
        float k = saturate((l - _BloomThr) / max(0.05, 1.0 - _BloomThr + 0.15));   // 문턱 위의 밝은 곳만(부드럽게)
        return fixed4(c * k * _BloomTint.rgb, 1);
    }
    fixed4 Blur (float2 uv, float2 dir)
    {
        float2 o = dir * _MainTex_TexelSize.xy * (1.0 + _BloomScatter * 2.0);
        float3 s = tex2D(_MainTex, uv).rgb * 0.227;
        s += (tex2D(_MainTex, uv + o * 1.38).rgb + tex2D(_MainTex, uv - o * 1.38).rgb) * 0.316;
        s += (tex2D(_MainTex, uv + o * 3.23).rgb + tex2D(_MainTex, uv - o * 3.23).rgb) * 0.070;
        return fixed4(s, 1);
    }
    fixed4 fragBlurH (v2f_img i) : SV_Target { return Blur(i.uv, float2(1, 0)); }
    fixed4 fragBlurV (v2f_img i) : SV_Target { return Blur(i.uv, float2(0, 1)); }

    float AngDiff(float a, float b) { float d = abs(a - b); return min(d, 6.2831853 - d); }
    float3 Danger(float4 d, float ang, float edge)
    {
        if (d.y <= 0.001) return 0;
        float arc = smoothstep(d.z, d.z * 0.55, AngDiff(ang, d.x));
        return float3(0.91, 0.36, 0.255) * arc * d.y * edge;   // #E85C41
    }

    fixed4 fragFinal (v2f_img i) : SV_Target
    {
        float2 uv = i.uv;
        float3 c = tex2D(_MainTex, uv).rgb;
        c += tex2D(_Bloom, uv).rgb * _BloomInt;                       // 블룸
        float3 g = 0;                                                  // LUT 섞기(0이 아닌 것만 읽는다)
        if (_W.x > 0.001) g += Lut(_L0, c) * _W.x;
        if (_W.y > 0.001) g += Lut(_L1, c) * _W.y;
        if (_W.z > 0.001) g += Lut(_L2, c) * _W.z;
        if (_W.w > 0.001) g += Lut(_L3, c) * _W.w;
        if (_W.x + _W.y + _W.z + _W.w < 0.001) g = c;
        if (_TendoLut > 0.001) g = lerp(g, Lut(_LT, g), _TendoLut);    // 천도 중 색(채도↓·청록 하이라이트)
        // 검수용 보정 후보: 대비 → 채도 → 색 곱 → 밝기 보탬 (기본값이면 그대로)
        g = (g - 0.5) * _GradeCS.x + 0.5;
        float gl = dot(g, float3(0.299, 0.587, 0.114));
        g = lerp(float3(gl, gl, gl), g, _GradeCS.y);
        g = saturate(g * _GradeTint.rgb + _GradeCS.z);
        // 평소 비네트(남청, 순검정 금지)
        float2 q = (uv - 0.5) * float2(_Aspect, 1.0); float dq = length(q) / (0.5 * sqrt(_Aspect * _Aspect + 1.0));
        float vt = saturate((dq - (1.0 - _VigSmooth) * 0.55) / max(0.001, _VigSmooth * 0.8));
        g = lerp(g, _VigColor.rgb, saturate(_VigInt * vt * vt));
        // 천도 시야 축소
        if (_TendoK > 0.001)
        {
            float2 p = (uv - _Center.xy) * float2(_Aspect, 1.0);
            float rd = 0.5 * sqrt(_Aspect * _Aspect + 1.0);               // 화면 대각선의 절반
            float d = length(p) / (rd * _Radius);
            float n = tex2D(_Noise, uv + _NoiseScroll).r;
            float dd = d + (n - 0.5) * 0.14;
            float a = smoothstep(1.0 - 0.12, 1.0 + 0.12, dd) * 0.94;      // 먹 번짐 가장자리
            g = lerp(g, float3(0.059, 0.09, 0.161), a);                    // #0F1729
            float ang = atan2(p.y, p.x);
            float pv = saturate((dd - (1.0 - 0.12 * 1.8)) / (0.12 * 1.8));
            float4 pat = tex2D(_Pattern, float2(frac(ang / 6.2831853 * 2.0), pv));   // 단청 문양 띠
            g = lerp(g, pat.rgb, pat.a * _PatA * saturate((a - 0.2) * 4.0));
            // 청록 글로우: 차사·대상 혼 두 곳
            float2 gp0 = (uv - _G0.xy) * float2(_Aspect, 1.0); float2 gp1 = (uv - _G1.xy) * float2(_Aspect, 1.0);
            float gl = _G0.w * exp(-pow(length(gp0) / max(0.001, _G0.z), 2.0)) + _G1.w * exp(-pow(length(gp1) / max(0.001, _G1.z), 2.0));
            g += float3(0.373, 0.89, 0.753) * gl * 0.35 * _TendoK;           // #5FE3C0
            float edge = smoothstep(0.7, 1.0, dd);
            g += Danger(_D0, ang, edge) + Danger(_D1, ang, edge) + Danger(_D2, ang, edge) + Danger(_D3, ang, edge);
        }
        // 성공 순간 보라 테두리 18px (파혼에는 없다)
        if (_SuccessA > 0.001)
        {
            float2 px = min(uv, 1.0 - uv) * _ScreenPx;
            float m = min(px.x, px.y);
            g = lerp(g, float3(0.788, 0.69, 1.0), saturate(1.0 - m / 18.0) * _SuccessA);   // #C9B0FF
        }
        return fixed4(g, 1);
    }
    ENDCG
    SubShader
    {
        Cull Off ZWrite Off ZTest Always
        Pass
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment fragBright
            #pragma target 3.0
            ENDCG
        }
        Pass
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment fragBlurH
            #pragma target 3.0
            ENDCG
        }
        Pass
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment fragBlurV
            #pragma target 3.0
            ENDCG
        }
        Pass
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment fragFinal
            #pragma target 3.0
            ENDCG
        }
    }
    Fallback Off
}
