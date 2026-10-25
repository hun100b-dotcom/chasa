// =============================================================================
// NpcActor.cs — 마을 사람(산 NPC) 3D 모델 하나를 세우고 Idle/Talk 동작을 재생한다.
// 아트의 NPC 21개는 뼈 16개·동작 4개(Idle/Walk/Talk/Work)를 공유한다. 컨트롤러 파일 없이 코드로 재생(Playables).
// 사람이 가까이 오면 그쪽으로 몸을 돌리고 'Talk' 동작을 한다(엿듣는 중이라 말은 자막으로).
// 모델이 없으면 NpcWorld 가 도형으로 대신한다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

public class NpcActor : MonoBehaviour
{
    PlayableGraph graph; AnimationMixerPlayable mixer;
    AnimationClipPlayable[] clips = new AnimationClipPlayable[2];   // 0 Idle, 1 Talk
    float t, yaw;
    public bool talking;                 // 가까이 선 사람이 있으면 true (NpcWorld 가 넣는다)
    public Vector3 lookAt;               // 몸을 돌릴 곳(플레이어)
    public bool hasLook;
    float talkW;

    /// <summary>모델을 불러와 세운다. 못 불러오면 false (그때는 호출한 쪽이 도형을 쓴다)</summary>
    public static NpcActor Create(Transform parent, string resourcePath, Vector3 pos)
    {
        var prefab = Resources.Load<GameObject>(resourcePath);
        if (prefab == null) return null;
        var root = new GameObject("Npc_" + prefab.name);
        root.transform.SetParent(parent, false);
        root.transform.position = pos;
        GroundSnap.Attach(root);   // 새 땅 높이 따라 선다
        var a = root.AddComponent<NpcActor>();
        if (!a.Build(prefab, resourcePath)) { Destroy(root); return null; }
        return a;
    }

    bool Build(GameObject prefab, string path)
    {
        var model = Instantiate(prefab, transform);
        model.transform.localPosition = Vector3.zero;
        model.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);   // glTFast 가 앞면을 뒤집으므로 주인공과 같은 보정
        foreach (var r in model.GetComponentsInChildren<Renderer>())
        {
            var src = r.sharedMaterials; var dst = new Material[src.Length];
            for (int i = 0; i < src.Length; i++) dst[i] = U.Matte(Props3D.MatColor(src[i]));   // 재질 칸의 원래 색을 무광 재질로
            r.sharedMaterials = dst;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On; r.receiveShadows = true;
        }
        var anim = model.GetComponentInChildren<Animator>();
        if (anim == null) anim = model.AddComponent<Animator>();
        var byName = new Dictionary<string, AnimationClip>();
        foreach (var c in Resources.LoadAll<AnimationClip>(path)) if (!c.name.StartsWith("__")) byName[c.name] = c;
        AnimationClip idle, talk;
        if (!byName.TryGetValue("Idle", out idle)) return true;   // 동작이 없으면 가만히 선 모델로라도 둔다
        if (!byName.TryGetValue("Talk", out talk)) talk = idle;
        graph = PlayableGraph.Create("Npc");
        graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
        var output = AnimationPlayableOutput.Create(graph, "out", anim);
        mixer = AnimationMixerPlayable.Create(graph, 2);
        clips[0] = AnimationClipPlayable.Create(graph, idle); clips[1] = AnimationClipPlayable.Create(graph, talk);
        graph.Connect(clips[0], 0, mixer, 0); graph.Connect(clips[1], 0, mixer, 1);
        mixer.SetInputWeight(0, 1f); mixer.SetInputWeight(1, 0f);
        output.SetSourcePlayable(mixer);
        graph.Play();
        t = Random.value * 3f;   // 사람마다 동작 시작 시각을 달리해 모두 똑같이 움직이지 않게
        return true;
    }

    void Update()
    {
        // 가까운 플레이어 쪽으로 천천히 몸을 돌린다
        if (hasLook)
        {
            var d = lookAt - transform.position; d.y = 0f;
            if (d.sqrMagnitude > 0.01f) yaw = Mathf.MoveTowardsAngle(yaw, Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg, 180f * Time.deltaTime);
            transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        }
        if (!graph.IsValid()) return;
        t += Time.deltaTime;
        talkW = Mathf.MoveTowards(talkW, talking ? 1f : 0f, Time.deltaTime / 0.25f);
        mixer.SetInputWeight(0, 1f - talkW); mixer.SetInputWeight(1, talkW);
        for (int i = 0; i < 2; i++) clips[i].SetTime(t % Mathf.Max(0.01f, clips[i].GetAnimationClip().length));
        graph.Evaluate(0f);
    }

    void OnDestroy() { if (graph.IsValid()) graph.Destroy(); }
}
