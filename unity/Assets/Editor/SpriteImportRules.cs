// =============================================================================
// SpriteImportRules.cs — 아트팀 PNG 를 불러올 때 쓰는 규칙 (에디터 전용, 자동 실행)
// 규격(SPRITE-SPEC): 필터 Bilinear(도트 아님)·밉맵 끔·압축 없음·투명 배경. 규칙을 파일마다 손으로 누르지 않게 자동화한다.
// =============================================================================
using UnityEditor;

public class SpriteImportRules : AssetPostprocessor
{
    void OnPreprocessTexture()
    {
        if (!assetPath.StartsWith("Assets/Resources/Sprites/")) return;
        var t = (TextureImporter)assetImporter;
        t.textureType = TextureImporterType.Default;      // 스프라이트는 코드에서 피벗을 정해 만든다(manifest 값)
        t.mipmapEnabled = false;
        t.filterMode = UnityEngine.FilterMode.Bilinear;
        t.textureCompression = TextureImporterCompression.Uncompressed;
        t.alphaIsTransparency = true;
        t.npotScale = TextureImporterNPOTScale.None;       // 2의 거듭제곱이 아니어도 늘리지 않는다
        t.isReadable = false;
        t.wrapMode = UnityEngine.TextureWrapMode.Clamp;
    }
}
