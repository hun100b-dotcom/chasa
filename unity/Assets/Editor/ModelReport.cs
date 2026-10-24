// =============================================================================
// ModelReport.cs — 들여온 3D 모델의 정보를 로그로 찍는 검사용 도구 (창 없이 배치모드로 실행).
//
// 실행: Unity.exe -batchmode -nographics -quit -projectPath unity -executeMethod ModelReport.Run -logFile <로그>
// 찍는 것: 애니메이션 클립 이름, 모델 키(높이, m), 발이 원점(y=0)에 있는지, 위쪽이 +y 인지
// =============================================================================
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class ModelReport
{
    public static void Run()
    {
        foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { "Assets/Resources/Models" }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (go == null) continue;
            var inst = Object.Instantiate(go);
            var rs = inst.GetComponentsInChildren<Renderer>();
            Bounds b = rs.Length > 0 ? rs[0].bounds : new Bounds();
            foreach (var r in rs) b.Encapsulate(r.bounds);
            var clips = AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>()
                .Where(c => !c.name.StartsWith("__preview__")).Select(c => c.name + "(" + c.length.ToString("0.00") + "s)").ToArray();
            Debug.Log("[ModelReport] " + path +
                      " | size(m) " + b.size.x.ToString("0.00") + "x" + b.size.y.ToString("0.00") + "x" + b.size.z.ToString("0.00") +
                      " | minY " + b.min.y.ToString("0.000") + " maxY " + b.max.y.ToString("0.000") +
                      " | root up " + inst.transform.up +
                      " | clips " + clips.Length + ": " + string.Join(", ", clips));
            Object.DestroyImmediate(inst);
        }
    }
}
