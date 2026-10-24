// =============================================================================
// DamageNumbers.cs — 튀어오르는 데미지 숫자 (Godot판 damage_numbers.gd)
// 글꼴·UI 에셋 없이 Unity 기본 화면 글자(OnGUI)로 그린다. 프로토타입에는 이게 가장 가볍다.
// =============================================================================
using System.Collections.Generic;
using UnityEngine;

public class DamageNumbers : MonoBehaviour
{
    class Item { public string text; public Vector2 pos, vel; public float age, size; public Color color; }

    public Camera cam;
    readonly List<Item> items = new List<Item>();
    GUIStyle style;

    public void Spawn(Vector3 worldPos, int value, string kind)
    {
        Vector3 sp = cam.WorldToScreenPoint(worldPos);
        items.Add(new Item
        {
            text = value.ToString(),
            pos = new Vector2(sp.x, Screen.height - sp.y), // 화면 글자는 위가 0 → y 뒤집기
            vel = new Vector2(Random.Range(-Config.NUMBER_SPREAD_SPEED, Config.NUMBER_SPREAD_SPEED),
                              -Random.Range(Config.NUMBER_POP_SPEED_MIN, Config.NUMBER_POP_SPEED_MAX)),
            size = Mathf.Min(Config.NUMBER_FONT_MAX, Config.NUMBER_FONT_BASE + value * Config.NUMBER_FONT_PER_DAMAGE),
            color = kind == "heavy" ? Config.NUMBER_COLOR_HEAVY : kind == "pull" ? Config.NUMBER_COLOR_PULL : Config.NUMBER_COLOR_NORMAL,
        });
    }

    public int Count => items.Count;

    /// <summary>dt = 진짜 시간 (히트스톱 중에도 숫자는 흐른다)</summary>
    public void Tick(float dt)
    {
        for (int i = items.Count - 1; i >= 0; i--)
        {
            var n = items[i];
            n.age += dt;
            if (n.age >= Config.NUMBER_LIFETIME) { items.RemoveAt(i); continue; }
            n.vel.y += Config.NUMBER_GRAVITY * dt; // 중력: 솟았다 떨어짐
            n.pos += n.vel * dt;
        }
    }

    void OnGUI()
    {
        if (style == null)
        {
            style = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold };
        }
        foreach (var n in items)
        {
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
