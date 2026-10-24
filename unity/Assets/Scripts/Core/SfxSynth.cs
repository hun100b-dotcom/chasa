// =============================================================================
// SfxSynth.cs — 임시 효과음을 "코드로 계산해서" 만든다 (녹음 파일 없이).
// 레시피 원본: 기획팀 planning/sound/sfx_synth.json (층·주파수·엔벨로프·크기). 값 조율은 그쪽 표를 따른다.
//
// 왜 Core(엔진 무관)에 두나?
//   소리는 결국 "숫자 배열"(PCM: 1초에 수만 개의 파형 높이값)이다. 유니티 없이도 만들 수 있어서
//   자동 검사(길이·최대 크기)를 클라우드에서 돌릴 수 있다. 유니티 쪽(Sfx.cs)은 이 배열을 재생만 한다.
//
// 용어: dBFS = 디지털 소리의 최대치(0)를 기준으로 얼마나 작은가(−9 = 꽤 큰 편, −24 = 아주 작게).
//       엔벨로프(envelope) = 소리가 커졌다 작아지는 모양(시작 attack, 사라짐 decay).
// =============================================================================
using System;
using System.Collections.Generic;

namespace Chasa.Core
{
    public static class SfxSynth
    {
        public const int Rate = 22050;   // 1초에 22050개 값 (효과음엔 충분하고 가볍다)

        enum Kind { Noise, Tone }
        enum Filt { None, Low, High, Band }

        /// <summary>소리 한 겹. Noise = 숨·타격 질감, Tone = 음높이 있는 소리</summary>
        struct Layer
        {
            public Kind kind; public Filt filt; public float f0, f1, q, mix;
            public float[] harm;                 // 여러 음을 동시에(쇠붙이 배음, 두 음 방울 등)
            public float attack, decay;          // ms. decay 0 = 계속 이어짐(루프용)
            public float trem;                   // 떨림(방울이 울리는 느낌) Hz
            public float lfoGain;                // 천천히 커졌다 작아지는(바람 숨결) Hz
        }

        struct Recipe { public float gainDb, lenMs; public bool loop, bypassCast; public List<Layer> layers; }

        static Layer Noise(Filt f, float c0, float c1, float q, float a, float d, float mix, float lfo = 0f)
        { return new Layer { kind = Kind.Noise, filt = f, f0 = c0, f1 = c1, q = q, attack = a, decay = d, mix = mix, lfoGain = lfo }; }
        static Layer Tone(float f0, float f1, float a, float d, float mix, float trem = 0f)
        { return new Layer { kind = Kind.Tone, f0 = f0, f1 = f1, attack = a, decay = d, mix = mix, trem = trem }; }
        static Layer Chord(float[] harm, float a, float d, float mix, float trem = 0f)
        { return new Layer { kind = Kind.Tone, harm = harm, attack = a, decay = d, mix = mix, trem = trem }; }

        static Recipe R(float gain, float len, params Layer[] ls)
        { return new Recipe { gainDb = gain, lenMs = len, layers = new List<Layer>(ls) }; }

        public static readonly string[] Ids =
        {
            "sfx.hit.chain", "sfx.hit.heavy", "sfx.enemy.telegraph", "sfx.kneel",
            "sfx.tendo.cast", "sfx.tendo.done", "sfx.pahon.burst", "amb.field",
            "sfx.player.hurt", "sfx.clue", "sfx.dodge",
        };

        /// <summary>id 로 레시피를 찾는다 (없으면 null)</summary>
        static bool TryRecipe(string id, out Recipe r)
        {
            switch (id)
            {
                case "sfx.hit.chain":   // 철컥 + 둔탁한 살
                    r = R(-9, 120,
                        Noise(Filt.Band, 2500, 2500, 2f, 1, 40, 0.6f),
                        Tone(180, 90, 1, 80, 0.8f),
                        Chord(new[] { 1240f, 1870f, 2630f }, 1, 120, 0.25f));   // 정수배가 아닌 배음 = 쇠붙이 소리
                    return true;
                case "sfx.hit.heavy":   // 낮고 무거운 쿵 (맨 앞 딱 소리가 있어야 또렷)
                    r = R(-6, 200,
                        Tone(90, 45, 2, 160, 1.0f),
                        Noise(Filt.Low, 600, 600, 0.7f, 1, 90, 0.7f),
                        Noise(Filt.Band, 1800, 1800, 1.5f, 1, 25, 0.3f));
                    return true;
                case "sfx.enemy.telegraph":   // 숨 들이켜는 상승음 = 곧 온다 (천도 먹먹 필터를 건너뛴다)
                    r = R(-10, 300,
                        Noise(Filt.Band, 500, 2200, 3f, 220, 80, 0.8f),
                        Tone(300, 420, 200, 100, 0.2f));
                    r.bypassCast = true; return true;
                case "sfx.kneel":   // 하강음 + 요령(방울) 한 번 = 고를 때다
                    r = R(-8, 600,
                        Tone(440, 220, 5, 300, 0.6f),
                        Chord(new[] { 2100f, 3150f }, 2, 600, 0.35f, 9f));
                    return true;
                case "sfx.tendo.cast":   // 낮은 드론, 점점 올라감 (이어 붙여 반복 재생)
                    r = R(-12, 1500,
                        Tone(110, 123, 150, 0, 0.7f, 4f),
                        Tone(165, 185, 150, 0, 0.4f, 4f));
                    r.loop = true; return true;
                case "sfx.tendo.done":   // 맑은 방울 두 음 + 숨 내쉼
                    r = R(-7, 900,
                        Chord(new[] { 880f, 1320f }, 3, 900, 0.6f),
                        Noise(Filt.High, 800, 6000, 0.7f, 40, 300, 0.25f));
                    return true;
                case "sfx.pahon.burst":   // 저음 폭발 + 깨지는 고음, 반음 부딪힘(찜찜함)
                    r = R(-4, 400,
                        Noise(Filt.Low, 3000, 200, 0.7f, 2, 350, 1.0f),
                        Tone(55, 55, 3, 250, 0.9f),
                        Chord(new[] { 1661f, 1760f }, 1, 180, 0.2f));
                    return true;
                case "amb.field":   // 느리게 숨 쉬는 바람 + 풀벌레 (8초 반복)
                    r = R(-24, 8000,
                        Noise(Filt.Low, 400, 400, 0.7f, 0, 0, 0.8f, 0.12f));
                    r.loop = true; r.layers.Add(new Layer { kind = Kind.Tone, f0 = 4200, f1 = 4200, mix = 0.15f, attack = -1 });   // attack<0 = 풀벌레 표시
                    return true;
                case "sfx.player.hurt":
                    r = R(-9, 120,
                        Tone(70, 50, 1, 120, 1.0f),
                        Noise(Filt.Low, 1200, 1200, 0.7f, 1, 50, 0.4f));
                    return true;
                case "sfx.dodge":   // 쉭 — 바람을 가르는 짧은 상승·하강
                    r = R(-12, 260,
                        Noise(Filt.Band, 400, 1800, 1.2f, 30, 220, 0.9f),
                        Tone(220, 150, 20, 200, 0.15f));
                    return true;
                case "sfx.clue":   // 대금 같은 숨 섞인 한 음
                    r = R(-11, 450,
                        Tone(660, 660, 60, 380, 0.7f, 5f),
                        Noise(Filt.Band, 660, 660, 4f, 60, 380, 0.2f));
                    return true;
            }
            r = default(Recipe); return false;
        }

        /// <summary>레시피대로 소리 샘플(−1~1)을 계산한다. 같은 id 는 항상 같은 소리(고정 난수)</summary>
        public static float[] Render(string id)
        {
            Recipe r;
            if (!TryRecipe(id, out r)) return null;
            int n = (int)(r.lenMs * 0.001f * Rate);
            var buf = new float[n];
            var rng = new Random(id.GetHashCode() & 0x7fffffff ^ 12345);
            foreach (var L in r.layers) AddLayer(buf, L, rng, r.loop);
            // 가장 큰 값이 gainDb 가 되도록 크기를 맞춘다 (dBFS → 배율: 10^(dB/20))
            float peak = 0f;
            for (int i = 0; i < n; i++) peak = Math.Max(peak, Math.Abs(buf[i]));
            if (peak > 1e-6f)
            {
                float k = (float)Math.Pow(10.0, r.gainDb / 20.0) / peak;
                for (int i = 0; i < n; i++) buf[i] *= k;
            }
            if (r.loop) FadeEdges(buf, 0.01f);   // 반복 이음매의 '틱' 소리 방지
            return buf;
        }

        /// <summary>샘플 배열의 최대 크기(dBFS). 검사용</summary>
        public static float PeakDb(float[] buf)
        {
            float p = 0f; foreach (var v in buf) p = Math.Max(p, Math.Abs(v));
            return p <= 1e-9f ? -200f : 20f * (float)Math.Log10(p);
        }

        static void FadeEdges(float[] b, float sec)
        {
            int m = Math.Min((int)(sec * Rate), b.Length / 2);
            for (int i = 0; i < m; i++) { float g = (float)i / m; b[i] *= g; b[b.Length - 1 - i] *= g; }
        }

        static void AddLayer(float[] buf, Layer L, Random rng, bool loop)
        {
            int n = buf.Length;
            if (L.attack < 0f) { AddCrickets(buf, L, rng); return; }
            double phase = 0, phase2 = 0;
            // 쌍이차 필터(biquad): 소리의 높은 쪽/낮은 쪽을 깎아 질감을 만든다
            float z1 = 0, z2 = 0, b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0;
            float lfoPh = (float)rng.NextDouble() * 6.28f;
            for (int i = 0; i < n; i++)
            {
                float t = (float)i / n;                          // 0~1 진행률
                float ms = i * 1000f / Rate;
                // 엔벨로프: attack 동안 올라가고, 이후 decay 동안 줄어든다. decay 0 이면 계속 유지
                float env = L.attack > 0f ? Math.Min(1f, ms / L.attack) : 1f;
                if (L.decay > 0f) { float d = 1f - Math.Max(0f, ms - L.attack) / L.decay; env *= d <= 0f ? 0f : d * d; }
                if (env <= 0f) continue;
                float s;
                if (L.kind == Kind.Noise)
                {
                    float x = (float)(rng.NextDouble() * 2.0 - 1.0);
                    if (L.filt != Filt.None)
                    {
                        if ((i & 15) == 0) Coeffs(L.filt, L.f0 + (L.f1 - L.f0) * t, L.q, out b0, out b1, out b2, out a1, out a2);
                        float y = b0 * x + z1; z1 = b1 * x - a1 * y + z2; z2 = b2 * x - a2 * y; x = y;
                    }
                    s = x * 2.5f;   // 필터가 소리를 깎으니 보충
                    if (L.lfoGain > 0f) s *= 0.55f + 0.45f * (float)Math.Sin(lfoPh + 6.2832f * L.lfoGain * i / Rate);
                }
                else
                {
                    if (L.harm != null)
                    {
                        s = 0f;
                        for (int h = 0; h < L.harm.Length; h++) s += (float)Math.Sin(6.2832 * L.harm[h] * i / Rate) / L.harm.Length;
                    }
                    else
                    {
                        float f = L.f0 + (L.f1 - L.f0) * t;
                        phase += 6.2832 * f / Rate; s = (float)Math.Sin(phase);
                        phase2 = phase;
                    }
                    if (L.trem > 0f) s *= 0.7f + 0.3f * (float)Math.Sin(6.2832 * L.trem * i / Rate);
                }
                buf[i] += s * env * L.mix;
            }
        }

        /// <summary>풀벌레: 짧은 3연 삑 소리를 무작위 간격으로 (고정 난수라 매번 같다)</summary>
        static void AddCrickets(float[] buf, Layer L, Random rng)
        {
            int pos = (int)(0.5f * Rate);
            while (pos < buf.Length - Rate / 5)
            {
                for (int p = 0; p < 3; p++)
                {
                    int len = (int)(0.018f * Rate), st = pos + p * (int)(0.045f * Rate);
                    for (int i = 0; i < len && st + i < buf.Length; i++)
                    {
                        float e = 1f - (float)i / len;
                        buf[st + i] += (float)Math.Sin(6.2832 * L.f0 * i / Rate) * e * L.mix * 0.2f;
                    }
                }
                pos += (int)((0.7f + (float)rng.NextDouble() * 0.9f) * Rate);   // 0.7~1.6초 간격
            }
        }

        /// <summary>RBJ 쌍이차 필터 계수 (표준 공식) — 반응이 날카롭지 않게 q 를 조절</summary>
        static void Coeffs(Filt f, float fc, float q, out float b0, out float b1, out float b2, out float a1, out float a2)
        {
            fc = Math.Max(40f, Math.Min(fc, Rate * 0.45f));
            double w = 6.2832 * fc / Rate, cw = Math.Cos(w), al = Math.Sin(w) / (2.0 * Math.Max(0.1f, q));
            double a0 = 1 + al, B0, B1, B2;
            switch (f)
            {
                case Filt.Low:  B0 = (1 - cw) / 2; B1 = 1 - cw; B2 = (1 - cw) / 2; break;
                case Filt.High: B0 = (1 + cw) / 2; B1 = -(1 + cw); B2 = (1 + cw) / 2; break;
                default:        B0 = al; B1 = 0; B2 = -al; break;
            }
            b0 = (float)(B0 / a0); b1 = (float)(B1 / a0); b2 = (float)(B2 / a0);
            a1 = (float)(-2 * cw / a0); a2 = (float)((1 - al) / a0);
        }
    }
}
