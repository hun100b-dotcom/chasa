// =============================================================================
// Interactables.cs — 1막 F 상호작용 물건(줍기·만져 보기)을 세운다. 규칙: planning/data/interactables-act1.md, 배치: Resources/Data/interactables_act1.json
//  · 단서 물건 3: 만지면(2초 누르기) 단서. 업 10↑ 글자 반쪽, 업 30↑ "손이 미끄러진다"
//  · 유품 6: 밤에 6m 안에서만 보임. 만지면 그 혼 천도 시전 −KEEPSAKE_CAST_CUT초. 기억 조각은 안 줌
//  · 엽전 꾸러미 6: 한 번만 줍기(저장됨) · 쑥 8: 낮에만, 다음 날 다시 남
// 자리는 JudgeSystem.interactSpots 에 등록하고, 거리·우선순위·누르기 진행은 JudgeSystem.UpdateInteract 가 한다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class Interactables
{
    [System.Serializable] class Gives { public string clue; }
    [System.Serializable] class ClueRow { public string id, place, when, text, model; public float x, z; public Gives gives; }
    [System.Serializable] class KeepRow { public string id, soul, soul_name, name, text, model; public float x, z; }
    [System.Serializable] class CoinRow { public string id; public float x, z; public int coin; }
    [System.Serializable] class HerbRow { public string id; public float x, z; }
    [System.Serializable] class Rules { public string gone_text; }
    [System.Serializable] class FileData { public Rules keepsake_text_rules; public ClueRow[] clue_objects; public KeepRow[] keepsakes; public CoinRow[] coin_bundles; public HerbRow[] herbs; }

    class Node { public JudgeSystem.InteractSpot spot; public GameObject view, ashView; public string kind, id, extra; }
    readonly List<Node> nodes = new List<Node>();
    readonly JudgeSystem j;
    Transform root; string goneText = "이미 떠난 사람의 물건이다.";

    public readonly HashSet<string> Picked = new HashSet<string>();            // 주운 엽전·만진 유품(저장됨)
    public readonly Dictionary<string, int> HerbTaken = new Dictionary<string, int>();   // 쑥 id → 딴 날(저장됨)
    public int Herbs;                                                          // 가진 쑥(저장됨)
    public readonly HashSet<string> KeepsakeSouls = new HashSet<string>();     // 유품을 만진 혼의 이름: 천도 시전이 짧아진다

    public Interactables(JudgeSystem judge)
    {
        j = judge;
        var ta = Resources.Load<TextAsset>("Data/interactables_act1");
        if (ta == null) return;
        var f = JsonUtility.FromJson<FileData>(ta.text);
        if (f == null) return;
        root = new GameObject("Interactables").transform;
        if (f.keepsake_text_rules != null && !string.IsNullOrEmpty(f.keepsake_text_rules.gone_text)) goneText = f.keepsake_text_rules.gone_text;
        if (f.clue_objects != null) foreach (var c in f.clue_objects) AddClue(c);
        if (f.keepsakes != null) foreach (var k in f.keepsakes) AddKeep(k);
        if (f.coin_bundles != null) foreach (var c in f.coin_bundles) AddCoin(c);
        if (f.herbs != null) foreach (var h in f.herbs) AddHerb(h);
    }

    /// <summary>걸을 수 있는 가장 가까운 자리로 붙인다(막힌 곳에 놓였으면 밀려난다)</summary>
    static Vector3 Place(float x, float z) { MapLayout.PushOut(ref x, ref z, 0.8f); return new Vector3(x, 0f, z); }

    GameObject Pillar(Vector3 p, Color col, float h, float w)
    {
        var g = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        Object.Destroy(g.GetComponent<Collider>());
        g.transform.SetParent(root, false);
        g.transform.position = p + Vector3.up * (h * 0.5f);
        g.transform.localScale = new Vector3(w, h * 0.5f, w);
        g.GetComponent<Renderer>().sharedMaterial = U.Unlit(col);
        g.SetActive(false);
        return g;
    }

    /// <summary>아트 모델(Resources/Models/Interact 또는 Field)이 있으면 그것을, 없으면 빛기둥 도형 대역을 세운다</summary>
    GameObject Model(string name, Vector3 p, Color fallback, float h, float w)
    {
        GameObject prefab = null;
        if (!string.IsNullOrEmpty(name)) prefab = Resources.Load<GameObject>("Models/Interact/" + name) ?? Resources.Load<GameObject>("Models/Field/" + name);
        if (prefab == null) return Pillar(p, fallback, h, w);
        var g = Object.Instantiate(prefab, p, Quaternion.identity, root);
        foreach (var c in g.GetComponentsInChildren<Collider>()) Object.Destroy(c);   // 걸리지 않게
        g.SetActive(false);
        return g;
    }

    Node Add(string kind, string id, Vector3 pos, InteractKind kind0, GameObject view, string extra = null)
    {
        var n = new Node { kind = kind, id = id, view = view, extra = extra };
        n.spot = new JudgeSystem.InteractSpot { Kind = kind0, Pos = pos };
        nodes.Add(n); j.interactSpots.Add(n.spot);
        return n;
    }

    void AddClue(ClueRow c)
    {
        var pos = Place(c.x, c.z);
        var n = Add("clue", c.id, pos, InteractKind.Touch, Model(c.model, pos, ChasaPalette.MemoryRim, 1.1f, 0.35f), c.when);
        n.spot.OnUse = () =>
        {
            if (j.ledger.Karma >= Balance.CLUE_TOUCH_KARMA_LOCK) { j.Say("손이 미끄러진다"); return false; }   // 업이 높으면 물건이 식어 만질 수 없다(다음에 다시)
            string t = c.text ?? "";
            if (j.ledger.Karma >= 10 && t.Length > 2) t = t.Substring(0, t.Length / 2) + "…";   // 업 10↑: 글자가 반만 보인다(단서는 인정)
            j.Say(t);
            if (j.clueBook.Add(c.gives.clue)) { Sfx.Play("sfx.clue"); j.HintClue(); }
            return true;
        };
        n.spot.Active = () => !j.clueBook.Has(c.gives.clue) && j.clock != null && (c.when != "낮" || j.clock.Phase == ClockPhase.Day) && (c.id == "B01-D2" || j.clock.Day >= 1);
    }

    void AddKeep(KeepRow k)
    {
        var pos = Place(k.x, k.z);
        var n = Add("keep", k.id, pos, InteractKind.Touch, Model(k.model, pos, new Color(0.95f, 0.85f, 0.55f), 0.9f, 0.18f), k.soul_name);
        n.ashView = Model("prop_keep_ash", pos, new Color(0.35f, 0.33f, 0.32f), 0.1f, 0.9f);   // 파혼하면 이 자리에 재가 남는다(F 안내 없음)
        n.spot.OnUse = () =>
        {
            Picked.Add(k.id);
            if (j.named != null && j.named.IsDone(k.soul_name)) { j.Say(goneText); return true; }   // 효과 없음
            KeepsakeSouls.Add(k.soul_name);
            j.Say(string.IsNullOrEmpty(k.text) ? k.name + " — " + k.soul_name + "의 물건. 이름을 알았다" : k.name + " — " + k.text);
            return true;
        };
        // 밤에만, 6m 안에서만 보인다. 이미 처결된 혼의 물건은 사라진다(천도) — 파혼의 재는 아직 따로 그리지 않는다
        n.spot.Active = () => !Picked.Contains(k.id) && !Picked.Contains("ash:" + k.id) && j.clock != null && j.clock.Phase == ClockPhase.Night && !(j.named != null && j.named.IsDone(k.soul_name))
            && new Vector2(pos.x - j.player.Pos.x, pos.z - j.player.Pos.z).magnitude <= Balance.KEEPSAKE_SHOW_M;
    }

    void AddCoin(CoinRow c)
    {
        var pos = Place(c.x, c.z);
        var n = Add("coin", c.id, pos, InteractKind.Pickup, Model("prop_coin_bundle", pos, Color.white, 1.4f, 0.12f));
        n.spot.OnUse = () => { Picked.Add(c.id); j.ledger.Coin += c.coin > 0 ? c.coin : Balance.COIN_BUNDLE; Sfx.Play("sfx.clue"); j.Say("엽전 " + (c.coin > 0 ? c.coin : Balance.COIN_BUNDLE) + "닢을 주웠다"); return true; };
        n.spot.Active = () => !Picked.Contains(c.id);
    }

    void AddHerb(HerbRow h)
    {
        var pos = Place(h.x, h.z);
        var n = Add("herb", h.id, pos, InteractKind.Pickup, Model("prop_herb_mugwort", pos, new Color(0.55f, 0.85f, 0.4f), 1.0f, 0.12f));
        n.spot.OnUse = () => { HerbTaken[h.id] = j.clock.Day; Herbs++; j.Say("쑥을 뜯었다 (" + Herbs + ")"); return true; };
        n.spot.Active = () => j.clock != null && j.clock.Phase == ClockPhase.Day && !(HerbTaken.ContainsKey(h.id) && HerbTaken[h.id] >= j.clock.Day);   // 낮에만 · 따면 다음 날 낮에 다시
    }

    /// <summary>이름혼을 파혼했다: 그 혼의 유품 자리에 재가 남는다(천도하면 유품은 그냥 사라진다)</summary>
    public void OnPahon(string soulName)
    {
        if (soulName == null) return;
        foreach (var n in nodes) if (n.kind == "keep" && n.extra == soulName) Picked.Add("ash:" + n.id);
    }

    bool restBuilt;
    /// <summary>서낭당마다 쉬기 자리(돌 의자·약탕 화로·따뜻한 불빛)를 세운다. 서낭당 좌표가 정해진 뒤 한 번</summary>
    void BuildRestSpots()
    {
        restBuilt = true;
        if (FieldRules.Shrines == null || FieldRules.Shrines.Length == 0 || root == null) return;
        var prefab = Resources.Load<GameObject>("Models/Interact/prop_seonang_rest");
        if (prefab == null) return;
        // 칠복네 문 앞의 빈 개집(지켜보기 J-004 자리 곁, 아트 좌표 근사 — 기획이 좌표를 확정하면 교체)
        var dog = Resources.Load<GameObject>("Models/Interact/prop_gaejip_empty");
        if (dog != null) { float dx = 200.5f, dz = 61.0f; MapLayout.PushOut(ref dx, ref dz, 0.8f); var dg = Object.Instantiate(dog, new Vector3(dx, 0f, dz), Quaternion.identity, root); foreach (var c in dg.GetComponentsInChildren<Collider>()) Object.Destroy(c); }
        foreach (var s in FieldRules.Shrines)
        {
            var g = Object.Instantiate(prefab, new Vector3(s[0], 0f, s[1]), Quaternion.identity, root);
            foreach (var c in g.GetComponentsInChildren<Collider>()) Object.Destroy(c);
            var lt = g.transform.Find("Light_seonang_rest");
            if (lt != null && QualityTier.Current != QualityTier.Level.Low)
            {
                var l = lt.gameObject.AddComponent<Light>();
                l.type = LightType.Point; l.color = new Color(1f, 0.69f, 0.4f); l.range = 6.5f; l.intensity = 1.1f;
                lt.gameObject.AddComponent<RestFlicker>();
            }
        }
    }

    /// <summary>모닥불처럼 살짝 깜박이는 불빛</summary>
    class RestFlicker : MonoBehaviour
    {
        Light l; float seed;
        void Awake() { l = GetComponent<Light>(); seed = Random.value * 10f; }
        void Update() { if (l != null) l.intensity = 1.0f + 0.15f * Mathf.PerlinNoise(seed, Time.time * 3f); }
    }

    /// <summary>매 프레임: 켜진 자리만 빛기둥을 보이게(40m 안)</summary>
    public void Tick(Vector3 playerPos)
    {
        if (!restBuilt) BuildRestSpots();
        foreach (var n in nodes)
            if (n.ashView != null)
            {
                bool ash = Picked.Contains("ash:" + n.id) && new Vector2(n.spot.Pos.x - playerPos.x, n.spot.Pos.z - playerPos.z).magnitude < 40f;
                if (n.ashView.activeSelf != ash) n.ashView.SetActive(ash);
            }
        foreach (var n in nodes)
        {
            if (n.view == null) continue;
            bool on = n.spot.Active != null && n.spot.Active() && new Vector2(n.spot.Pos.x - playerPos.x, n.spot.Pos.z - playerPos.z).magnitude < 40f;
            if (n.view.activeSelf != on) n.view.SetActive(on);
            if (on && (n.kind == "clue" || n.kind == "keep"))
            {
                // 아트의 'Glow' 자식 메시: 유품은 밤 6m 안(Active 가 이미 보장), 단서는 12m 안에서만 켠다
                var gl = n.view.transform.Find("Glow");
                if (gl != null) gl.gameObject.SetActive(n.kind == "keep" || new Vector2(n.spot.Pos.x - playerPos.x, n.spot.Pos.z - playerPos.z).magnitude <= 12f);
            }
        }
    }

    /// <summary>12m 안 만져 볼 물건 위에 손 아이콘(단서는 금색, 그 밖은 흰색)</summary>
    public void DrawWorld(Camera cam, Vector3 playerPos, Texture2D white)
    {
        if (cam == null) return;
        var st = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontSize = 15, fontStyle = FontStyle.Bold };
        foreach (var n in nodes)
        {
            if (n.kind != "clue" && n.kind != "keep") continue;
            if (n.spot.Active == null || !n.spot.Active()) continue;
            if (new Vector2(n.spot.Pos.x - playerPos.x, n.spot.Pos.z - playerPos.z).magnitude > 12f) continue;
            var sp = cam.WorldToScreenPoint(n.spot.Pos + Vector3.up * 1.7f);
            if (sp.z < 0f) continue;
            float x = sp.x, y = Screen.height - sp.y;
            GUI.color = new Color(0.06f, 0.05f, 0.05f, 0.6f); GUI.DrawTexture(new Rect(x - 13, y - 13, 26, 26), white);
            GUI.color = n.kind == "clue" ? new Color(1f, 0.82f, 0.3f) : Color.white; GUI.Label(new Rect(x - 13, y - 13, 26, 26), "손", st);
            GUI.color = Color.white;
        }
    }

    // ---- 저장 ----
    public string PickedText() { return string.Join(",", Picked); }
    public string HerbTakenText() { var l = new List<string>(); foreach (var kv in HerbTaken) l.Add(kv.Key + ":" + kv.Value); return string.Join(",", l); }
    public void Restore(IEnumerable<string> picked, IEnumerable<string> herbTaken, int herbs)
    {
        Picked.Clear(); HerbTaken.Clear(); KeepsakeSouls.Clear(); Herbs = herbs;
        if (picked != null) foreach (var p in picked) if (p.Length > 0 && !p.StartsWith("jesa:") && !p.StartsWith("fp:") && !p.StartsWith("fd:") && !p.StartsWith("fday:")) Picked.Add(p);   // 제사·장례 기록은 JudgeSystem 이 따로 읽는다(옛 값이 새 값을 덮지 않게 거른다)
        if (herbTaken != null) foreach (var h in herbTaken) { var kv = h.Split(':'); int d; if (kv.Length == 2 && int.TryParse(kv[1], out d)) HerbTaken[kv[0]] = d; }
        foreach (var n in nodes) if (n.kind == "keep" && Picked.Contains(n.id) && n.extra != null) KeepsakeSouls.Add(n.extra);   // 만진 유품의 혼 이름을 되살린다
    }
}
