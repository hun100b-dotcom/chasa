// =============================================================================
// MemoryLines.cs — 천도하면 보이는 '기억 한 줄' (기획 6단계 성장 루프의 이야기 쪽).
//
// 천도 1회 = 기억 조각 1개(같은 혼은 한 번만 센다). 이름이 있는 혼은 서사팀이 쓴 그 혼의 기억을, 이름 없는 혼은
// 나이(갓 죽은·해 넘긴·오래된)별 공용 줄에서 무작위로 보여 준다. 파혼하면 기억은 없다(이야기를 못 봄 — 선택의 대가).
// 데이터: Resources/Data/memory_flat.json (tools/build_memory_data.py 가 서사 원본에서 만든다).
// =============================================================================
using System.Collections.Generic;
using UnityEngine;
using Chasa.Core;

public class MemoryLines
{
    [System.Serializable] class SoulRow { public string name, memory, tint, fact, jesa; public bool mystery, decisive, boss; }
    [System.Serializable] class FileData { public string[] fresh, year, old; public SoulRow[] souls; }

    readonly Dictionary<string, SoulRow> byName = new Dictionary<string, SoulRow>();
    readonly HashSet<string> counted = new HashSet<string>();   // 이미 기억을 본 이름혼(한 번만)
    FileData data;
    public System.Func<string, bool> jesaSeen;                  // 그 혼 집의 제사를 낮에 지켜봤나(JudgeSystem 이 판정)
    public int Fragments;                                       // 모은 기억 조각 수

    public MemoryLines()
    {
        var ta = Resources.Load<TextAsset>("Data/memory_flat");
        if (ta == null) return;
        data = JsonUtility.FromJson<FileData>(ta.text);
        if (data != null && data.souls != null) foreach (var s in data.souls) byName[s.name] = s;
    }

    /// <summary>천도 끝난 혼의 기억 한 줄을 돌려준다. 이미 본 이름혼이거나 데이터가 없으면 null (조각도 안 센다)</summary>
    public string Collect(Soul soul, out string fact)
    {
        fact = null;
        if (!string.IsNullOrEmpty(soul.LonerMemory)) { Fragments++; return soul.LonerMemory; }   // 외톨이 혼: 서사 표의 기억 한 줄(혼자 앉은 까닭)
        if (data == null) return null;
        SoulRow row;
        if (soul.Name != null && byName.TryGetValue(soul.Name, out row))
        {
            if (!counted.Add(soul.Name)) return null;
            Fragments++;
            if (row.mystery && !string.IsNullOrEmpty(row.fact)) fact = row.fact;   // 추리판에 켜질 사실 번호
            // 제사를 지켜본 뒤 천도하면 기억 끝에 한 줄 덧붙는다(기억 조각 수에는 세지 않는다)
            if (!string.IsNullOrEmpty(row.jesa) && jesaSeen != null && jesaSeen(soul.Name)) return row.memory + "\n" + row.jesa;
            return row.memory;
        }
        string[] pool = soul.Kind == SoulKind.Year ? data.year : soul.Kind == SoulKind.Old ? data.old : data.fresh;
        if (pool == null || pool.Length == 0) return null;
        Fragments++;
        return pool[Random.Range(0, pool.Length)];
    }
}
