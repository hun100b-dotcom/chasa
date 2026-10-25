// =============================================================================
// BuildScript.cs — 편집기 화면 없이 명령어 한 줄로 웹 빌드를 만든다.
//
// 실행 (PC 터미널):
//   Unity.exe -batchmode -quit -projectPath <이 폴더> -executeMethod BuildScript.BuildWebGL -logFile -
//
// 하는 일
//   1) 재질 파일 5개를 Resources/Mats 에 만든다 → 웹 빌드에 셰이더가 빠지지 않게 '사용 중'으로 표시하는 효과
//   2) 빈 씬 하나를 만든다 (게임은 GameMain.cs 가 켜질 때 코드로 다 만든다)
//   3) 웹(WebGL)으로 빌드한다. 압축은 끄고(서버 설정 없이 Vercel에 그대로 올리려고) Vercel이 대신 압축한다.
// =============================================================================
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class BuildScript
{
    const string MatDir = "Assets/Resources/Mats";
    const string ScenePath = "Assets/Scenes/Main.unity";

    [MenuItem("Chasa/Build WebGL")]
    public static void BuildWebGL()
    {
        PrepareAssets();
        PlayerSettings.productName = "Chasa Unity";
        PlayerSettings.companyName = "Chasa";
        PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Disabled;
        PlayerSettings.WebGL.dataCaching = true;
        PlayerSettings.runInBackground = true;
        PlayerSettings.WebGL.template = "PROJECT:Chasa";   // 폰 대응 페이지 틀(전체 화면 캔버스·해상도 제한·가로 안내) — Assets/WebGLTemplates/Chasa
        // 엔진 코드 줄이기(stripping)를 끈다. 켜 두면 웹 빌드가 실제로 쓰는 엔진 기능(충돌체·GUI 등)까지 지워
        // 콘솔 오류가 수만 개 나고 화면 버튼 배경이 사라졌다(2026-10-24 PC 검증). 크기가 조금 늘어도 안전이 먼저다.
        PlayerSettings.stripEngineCode = false;
        var opts = new BuildPlayerOptions
        {
            scenes = new[] { ScenePath },
            locationPathName = "Build/web",
            target = BuildTarget.WebGL,
            options = BuildOptions.None,
        };
        var report = BuildPipeline.BuildPlayer(opts);
        Debug.Log("[Chasa] 빌드 결과: " + report.summary.result + " / 크기 " + report.summary.totalSize + " bytes");
        if (report.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded) EditorApplication.Exit(1);
    }

    public static void PrepareAssets()
    {
        Directory.CreateDirectory(MatDir);
        Directory.CreateDirectory("Assets/Scenes");

        Save("Matte", Shader.Find("Standard"), m => { m.SetFloat("_Glossiness", 0f); m.SetFloat("_Metallic", 0f); });
        Save("Flash", Shader.Find("Standard"), m =>
        {
            // 적이 맞을 때 하얗게 번쩍이는 데 쓰는 '발광' 기능을 켜 둔다 (빌드에서 이 기능이 빠지지 않게)
            m.SetFloat("_Glossiness", 0f); m.SetFloat("_Metallic", 0f);
            m.EnableKeyword("_EMISSION");
            m.SetColor("_EmissionColor", Color.black);
            m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
        });
        Save("Unlit", Shader.Find("Unlit/Color"), null);
        Save("VertexColor", Shader.Find("Sprites/Default"), null);
        Save("Additive", Shader.Find("Legacy Shaders/Particles/Additive") ?? Shader.Find("Sprites/Default"), null);
        AssetDatabase.SaveAssets();

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        EditorSceneManager.SaveScene(scene, ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
    }

    static void Save(string name, Shader shader, System.Action<Material> setup)
    {
        if (shader == null) { Debug.LogError("[Chasa] 셰이더 없음: " + name); return; }
        string path = $"{MatDir}/{name}.mat";
        AssetDatabase.DeleteAsset(path);
        var m = new Material(shader);
        setup?.Invoke(m);
        AssetDatabase.CreateAsset(m, path);
    }
}
