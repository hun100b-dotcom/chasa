// =============================================================================
// DamageNumbers.cs — 튀어오르는 데미지 숫자 (Godot판 damage_numbers.gd)
// 글꼴·UI 에셋 없이 Unity 기본 화면 글자(OnGUI)로 그린다. 프로토타입에는 이게 가장 가볍다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class DamageNumbers : MonoBehaviour
{
    class Item { public string text; public Vector2 pos, vel; public float age, size; public Color color; public string crack; }   // crack 이 있으면 숫자 대신 금 그림

    public Camera cam;
    readonly List<Item> items = new List<Item>();
    GUIStyle style;

    public void Spawn(Vector3 worldPos, int value, string kind)
    {
        if (value <= 0) return;   // 0 피해는 숫자를 띄우지 않는다(노란 0 이 떠 보이던 것: 아트 검수)
        Vector3 sp = cam.WorldToScreenPoint(worldPos);
        bool reward = kind == "neok" || kind == "coin";
        if (!reward && !SaveStore.Settings.ShowNumbers)
        {
            // 개편 P0-5: 맞은 숫자는 기본으로 끄고 '맺힘 금' 표식 한 장을 0.35초 띄운다(설정에서 숫자를 켤 수 있다)
            if (sp.z < 0f) return;
            string c = kind == "heavy" ? "hit_crack_l" : value >= 20 ? "hit_crack_m" : "hit_crack_s";
            if (SpriteLib.Texture("overhaul/gyeol/" + c) == null) return;   // 그림이 없으면 아무것도 띄우지 않는다
            while (items.Count >= Balance.DMG_NUM_MAX) items.RemoveAt(0);
            items.Add(new Item { crack = c, pos = new Vector2(sp.x, Screen.height - sp.y) });
            return;
        }
        sp.x += Random.Range(-Balance.DMG_NUM_SCATTER_PX, Balance.DMG_NUM_SCATTER_PX);   // 같은 자리 숫자가 좌우로 흩어져 겹쳐 읽기 어렵던 것 방지
        while (items.Count >= Balance.DMG_NUM_MAX) items.RemoveAt(0);   // 한 화면 최대 개수: 가장 오래된 것부터 지운다
        items.Add(new Item
        {
            text = kind == "neok" || kind == "coin" ? "+" + value : value.ToString(),   // 보상 숫자는 + 를 붙인다
            pos = new Vector2(sp.x, Screen.height - sp.y), // 화면 글자는 위가 0 → y 뒤집기
            vel = new Vector2(Random.Range(-Config.NUMBER_SPREAD_SPEED, Config.NUMBER_SPREAD_SPEED),
                              -Random.Range(Config.NUMBER_POP_SPEED_MIN, Config.NUMBER_POP_SPEED_MAX)),
            size = kind == "neok" || kind == "coin" ? 22f : Mathf.Min(Config.NUMBER_FONT_MAX, Config.NUMBER_FONT_BASE + value * Config.NUMBER_FONT_PER_DAMAGE),
            color = kind == "neok" ? new Color(0.45f, 0.95f, 0.9f) : kind == "coin" ? new Color(1f, 0.72f, 0.28f) : kind == "heavy" ? Config.NUMBER_COLOR_HEAVY : kind == "pull" ? Config.NUMBER_COLOR_PULL : Config.NUMBER_COLOR_NORMAL,
        });
    }

    public int Count => items.Count;
    const float CrackLife = 0.35f;   // 맞은 자리 금 표식 수명(아트 명세 OVERHAUL-ART)

    /// <summary>dt = 진짜 시간 (히트스톱 중에도 숫자는 흐른다)</summary>
    public void Tick(float dt)
    {
        for (int i = items.Count - 1; i >= 0; i--)
        {
            var n = items[i];
            n.age += dt;
            if (n.crack != null) { if (n.age >= CrackLife) items.RemoveAt(i); continue; }   // 금 표식은 제자리에서 0.35초 뒤 사라진다
            if (n.age >= Config.NUMBER_LIFETIME) { items.RemoveAt(i); continue; }
            n.vel.y += Config.NUMBER_GRAVITY * dt; // 중력: 솟았다 떨어짐
            n.pos += n.vel * dt;
        }
    }

    void OnGUI()
    {
        if (MiniMap.BigOpen) return;   // 큰 지도가 열리면 맞은 숫자가 지도 위를 가리지 않게 숨긴다
        Ko.Apply(); // 한글 글꼴 적용(안 하면 한글이 네모로 깨짐)
        if (style == null)
        {
            style = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
        }
        foreach (var n in items)
        {
            if (n.crack != null)
            {
                var tex = SpriteLib.Texture("overhaul/gyeol/" + n.crack);
                if (tex != null)
                {
                    float k = 1f + 0.25f * (n.age / CrackLife);   // 살짝 퍼지며 옅어진다
                    GUI.color = new Color(1f, 1f, 1f, 1f - n.age / CrackLife);
                    GUI.DrawTexture(new Rect(n.pos.x - tex.width * k * 0.5f, n.pos.y - tex.height * k * 0.5f, tex.width * k, tex.height * k), tex);
                    GUI.color = Color.white;
                }
                continue;
            }
            float pop = Mathf.Max(0f, 1f - n.age / Config.NUMBER_POP_TIME);
            float scale = 1f + (Config.NUMBER_POP_SCALE - 1f) * pop; // 처음 크게 → 정상
            float remain = Config.NUMBER_LIFETIME - n.age;
            float alpha = remain < Config.NUMBER_FADE_TIME ? remain / Config.NUMBER_FADE_TIME : 1f;
            style.fontSize = Mathf.RoundToInt(n.size * scale);
            var r = new Rect(n.pos.x - 100, n.pos.y - 50, 200, 100);
            // 검은 테두리: 상하좌우로 2픽셀씩 밀어 검은 글자를 먼저 그린다 (어떤 바닥에서도 읽히게)
            style.normal.textColor = new Color(0, 0, 0, alpha);
            foreach (var o in new[] { new Vector2(-2, -2), new Vector2(2, -2), new Vector2(-2, 2), new Vector2(2, 2) })
                GUI.Label(new Rect(r.x + o.x, r.y + o.y, r.width, r.height), n.text, style);
            var c = n.color; c.a = alpha;
            style.normal.textColor = c;
            GUI.Label(r, n.text, style);
        }
    }
}
