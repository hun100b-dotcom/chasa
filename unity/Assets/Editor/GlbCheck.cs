// =============================================================================
// GlbCheck.cs — Resources/Models/Art 의 3D 모델(GLB·OBJ)이 제대로 읽히는지 로그로 찍는 검사 도구.
//
// 왜 있는가: 창 없는 배치모드에서는 눈으로 볼 수 없으니, 모델을 Resources.Load 로 실제로 읽어 보고
//   (1) 읽혔는지 (2) 재질의 셰이더 이름(분홍색 = 셰이더 없음 사고를 미리 잡기) (3) 뼈대(SkinnedMeshRenderer·Animator)
//   (4) 크기를 글로 남긴다.
// 실행: Unity.exe -batchmode -nographics -quit -projectPath unity -executeMethod GlbCheck.Run -logFile <로그>
// =============================================================================
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class GlbCheck
{
    public static void Run()
    {
        foreach (var guid in AssetDatabase.FindAssets("", new[] { "Assets/Resources/Models/Art" }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            if (!(path.EndsWith(".glb") || path.EndsWith(".obj"))) continue;
            // Resources 기준 이름(확장자 없이)으로 게임과 똑같이 읽어 본다
            string res = path.Substring("Assets/Resources/".Length);
            res = res.Substring(0, res.LastIndexOf('.'));
            var go = Resources.Load<GameObject>(res);
            if (go == null) { Debug.Log("[GlbCheck] " + path + " | Resources.Load 실패(null) | importer " + AssetImporter.GetAtPath(path)?.GetType().Name); continue; }
            var inst = Object.Instantiate(go);
            var rs = inst.GetComponentsInChildren<Renderer>();
            Bounds b = rs.Length > 0 ? rs[0].bounds : new Bounds();
            foreach (var r in rs) b.Encapsulate(r.bounds);
            var shaders = rs.SelectMany(r => r.sharedMaterials).Where(m => m != null)
                .Select(m => m.shader == null ? "null" : m.shader.name + (m.shader.isSupported ? "" : "(미지원)")).Distinct().ToArray();
            int skinned = inst.GetComponentsInChildren<SkinnedMeshRenderer>().Length;
            int bones = inst.GetComponentsInChildren<SkinnedMeshRenderer>().Sum(s => s.bones.Length);
            bool animator = inst.GetComponentInChildren<Animator>() != null || inst.GetComponentInChildren<Animation>() != null;
            Debug.Log("[GlbCheck] " + path + " | importer " + AssetImporter.GetAtPath(path)?.GetType().Name +
                      " | size(m) " + b.size.x.ToString("0.00") + "x" + b.size.y.ToString("0.00") + "x" + b.size.z.ToString("0.00") +
                      " | minY " + b.min.y.ToString("0.00") + " | renderers " + rs.Length + " skinned " + skinned + " bones " + bones +
                      " | animator " + animator + " | shaders " + string.Join(", ", shaders));
            // 재질마다 색이 어느 속성 이름에 들어 있는지(Props3D 가 색을 꺼낼 수 있는지) 찍는다
            foreach (var m in rs.SelectMany(r => r.sharedMaterials).Where(m => m != null).Take(3))
            {
                var found = new[] { "_BaseColorFactor", "_BaseColor", "_Color", "baseColorFactor" }
                    .Where(n => m.HasProperty(n)).Select(n => n + "=" + m.GetColor(n)).ToArray();
                Debug.Log("[GlbCheck]   재질 " + m.name + " | " + (found.Length > 0 ? string.Join(" ", found) : "색 속성 없음"));
            }
            Object.DestroyImmediate(inst);
        }
    }
}
