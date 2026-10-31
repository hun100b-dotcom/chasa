// =============================================================================
// ToastStack.cs — "얻은 것 알림"(왼쪽 가운데에 잠깐 떴다 사라지는 쪽지들)의 규칙 (순수 C#, 테스트 가능).
//
// 왜 따로 두나? 규칙(2초 뒤 사라짐, 같은 글은 합치기, 최대 5줄)을 화면 코드와 분리해 유니티 없이 검사하려고.
// 합치기란? "넋 +1" 이 연달아 뜨면 줄이 쌓이지 않고 "넋 +1 ×3" 처럼 한 줄로 묶어 화면이 어지럽지 않게 한다.
// =============================================================================
using System.Collections.Generic;

namespace Chasa.Core
{
    public sealed class ToastStack
    {
        public sealed class Toast { public string Text; public int Count = 1; public float Age; }

        public const float Life = 2f;      // 한 쪽지가 보이는 시간(초)
        public const int MaxLines = 5;     // 동시에 보이는 최대 줄 수

        public readonly List<Toast> Items = new List<Toast>();

        /// <summary>쪽지를 더한다. 같은 글이 이미 떠 있으면 횟수만 올리고 시간을 새로 센다</summary>
        public void Add(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            foreach (var t in Items)
                if (t.Text == text) { t.Count++; t.Age = 0f; return; }
            Items.Add(new Toast { Text = text });
            if (Items.Count > MaxLines) Items.RemoveAt(0);   // 너무 많으면 가장 오래된 것부터 치운다
        }

        public void Tick(float dt)
        {
            for (int i = Items.Count - 1; i >= 0; i--)
            {
                Items[i].Age += dt;
                if (Items[i].Age >= Life) Items.RemoveAt(i);
            }
        }

        /// <summary>화면에 쓸 글: 합쳐진 것은 "글 ×N"</summary>
        public static string Line(Toast t) { return t.Count > 1 ? t.Text + " ×" + t.Count : t.Text; }
    }
}
