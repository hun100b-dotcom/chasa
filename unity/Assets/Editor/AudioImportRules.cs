// =============================================================================
// AudioImportRules.cs — 소리 파일을 불러올 때 웹 빌드용 압축 규칙을 건다 (에디터 전용, 자동 실행)
// 왜? 효과음이 WAV 원본(17MB)이라 빌드 용량(.data)의 큰 몫을 차지한다. 웹(WebGL)용으로만 Vorbis 압축 + 효과음은 한 채널(모노)로 줄이면
// 귀로는 거의 같고 용량은 1/5 안팎이 된다. 원본 WAV 는 그대로 두므로 다시 되돌릴 수 있다.
// =============================================================================
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

public class AudioImportRules : AssetPostprocessor
{
    // data/audio_packs.json(기획·사운드)의 소리 종류표: 소리마다 sfx_short / sfx_lowband / amb_loop / long_oneshot 중 하나.
    // 종류별로 표본율(11kHz 위가 없는 소리는 22050Hz)과 품질을 달리해 내려받는 크기를 줄인다. 표에 없는 소리는 아래 기본값을 쓴다.
    static Dictionary<string, string> kindOf;
    static readonly Dictionary<string, KeyValuePair<float, uint>> KindRule = new Dictionary<string, KeyValuePair<float, uint>>   // 품질(0~1), 표본율(0 = 최적)
    {
        { "sfx_short", new KeyValuePair<float, uint>(0.4f, 44100) }, { "sfx_lowband", new KeyValuePair<float, uint>(0.3f, 22050) },
        { "amb_loop", new KeyValuePair<float, uint>(0.3f, 22050) }, { "long_oneshot", new KeyValuePair<float, uint>(0.3f, 44100) },
    };

    static string KindFor(string assetPath)
    {
        if (kindOf == null)
        {
            kindOf = new Dictionary<string, string>();
            try
            {
                var path = Path.GetFullPath(Path.Combine(Application.dataPath, "../../data/audio_packs.json"));
                if (File.Exists(path))
                {
                    // 'kind_of' 한 덩어리만 정규식 없이 간단히 읽는다(JsonUtility 는 사전을 못 읽는다): "키": "종류" 줄을 훑는다
                    string text = File.ReadAllText(path); int at = text.IndexOf("\"kind_of\"");
                    if (at >= 0)
                    {
                        int end = text.IndexOf('}', at);
                        foreach (var m in System.Text.RegularExpressions.Regex.Matches(text.Substring(at, end - at), "\"([^\"]+)\"\\s*:\\s*\"([a-z_]+)\""))
                        {
                            var g = ((System.Text.RegularExpressions.Match)m).Groups; if (g[1].Value != "kind_of") kindOf[g[1].Value.Replace('.', '_')] = g[2].Value;
                        }
                    }
                }
            }
            catch (System.Exception e) { Debug.LogWarning("audio_packs.json 읽기 실패 — 기본 설정을 쓴다: " + e.Message); }
        }
        string k; return kindOf.TryGetValue(Path.GetFileNameWithoutExtension(assetPath), out k) ? k : null;
    }

    void OnPreprocessAudio()
    {
        if (!assetPath.StartsWith("Assets/Resources/Audio/")) return;
        var a = (AudioImporter)assetImporter;
        bool bgm = assetPath.StartsWith("Assets/Resources/Audio/BGM/");
        a.forceToMono = !bgm;   // 효과음·환경음은 모노(위치음이 없는 게임이라 차이가 안 난다). 음악은 스테레오 유지
        var s = a.GetOverrideSampleSettings("WebGL");
        s.loadType = AudioClipLoadType.CompressedInMemory;
        s.compressionFormat = AudioCompressionFormat.Vorbis;
        s.quality = bgm ? 0.4f : 0.45f;
        s.sampleRateSetting = AudioSampleRateSetting.OptimizeSampleRate;
        string kind = bgm ? null : KindFor(assetPath);
        if (kind != null && KindRule.ContainsKey(kind))
        {
            // 종류별 품질·표본율(22050Hz 로 낮춰도 되는 소리는 내려받기만 줄고 메모리는 같다 — 웹은 브라우저가 48kHz 로 푼다)
            var r = KindRule[kind]; s.quality = r.Key;
            if (r.Value > 0) { s.sampleRateSetting = AudioSampleRateSetting.OverrideSampleRate; s.sampleRateOverride = r.Value; }
        }
        // 음악은 처음 틀 때 불러온다(시작이 빨라진다). Unity 6.3 부터 미리 불러오기는 플랫폼별 SampleSettings 안의 값이다
        // (AudioImporter.preloadAudioData 는 없어진 값이라 쓰면 컴파일 에러 — PC 확인)
        s.preloadAudioData = !bgm;
        a.SetOverrideSampleSettings("WebGL", s);
    }
}
