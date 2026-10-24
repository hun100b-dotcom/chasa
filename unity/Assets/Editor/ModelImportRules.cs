// =============================================================================
// ModelImportRules.cs — Resources/Models 아래 3D 모델(FBX)을 들여올 때 설정을 자동으로 맞춘다.
//
// 왜 필요한가
//   .meta 파일을 손으로 고치면 프로젝트가 깨지기 쉽다(하네스 규칙). 그래서 "이 폴더에 들어온 모델은
//   이렇게 들여온다"는 규칙을 코드로 둔다. 새 모델을 넣어도 사람이 설정 창을 열 필요가 없다.
//
// 정한 값 (코디네이터 지시 2026-10-25)
//   - 애니메이션 종류: Generic (사람형 전용 Humanoid 가 아닌, 뼈대 그대로 쓰는 일반 방식)
//   - 머티리얼(재질): 들여오지 않음(None). 색·재질은 우리 팔레트로 코드에서 입힌다.
// =============================================================================
using UnityEditor;

public class ModelImportRules : AssetPostprocessor
{
    const string ModelsDir = "Assets/Resources/Models/";

    void OnPreprocessModel()
    {
        if (!assetPath.StartsWith(ModelsDir)) return;
        // 아트팀 소품(Models/Art)은 예외: 모델 안 재질 색(MTL)을 Props3D 가 꺼내 쓰므로
        // 재질을 들여와야 한다. 유니티 기본 설정(Scale Factor 1, 재질 생성 기본) 그대로 둔다.
        if (assetPath.StartsWith(ModelsDir + "Art/")) return;
        var mi = (ModelImporter)assetImporter;
        mi.animationType = ModelImporterAnimationType.Generic;
        mi.materialImportMode = ModelImporterMaterialImportMode.None;
        // 소품(Props)에는 움직임이 없으므로 애니메이션을 아예 들여오지 않아 용량을 줄인다
        mi.importAnimation = assetPath.Contains("/Hero/");
    }
}
