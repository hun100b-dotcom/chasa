// =============================================================================
// AudioImportRules.cs — 소리 파일을 불러올 때 웹 빌드용 압축 규칙을 건다 (에디터 전용, 자동 실행)
// 왜? 효과음이 WAV 원본(17MB)이라 빌드 용량(.data)의 큰 몫을 차지한다. 웹(WebGL)용으로만 Vorbis 압축 + 효과음은 한 채널(모노)로 줄이면
// 귀로는 거의 같고 용량은 1/5 안팎이 된다. 원본 WAV 는 그대로 두므로 다시 되돌릴 수 있다.
// =============================================================================
using UnityEditor;
using UnityEngine;

public class AudioImportRules : AssetPostprocessor
{
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
        a.SetOverrideSampleSettings("WebGL", s);
        a.preloadAudioData = !bgm;   // 음악은 처음 틀 때 불러온다(시작이 빨라진다)
    }
}
