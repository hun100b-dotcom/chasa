// =============================================================================
// SaveStore.cs — 저장 글자와 설정을 브라우저/기기에 넣고 꺼내는 곳 (PlayerPrefs)
// 왜 PlayerPrefs? 유니티가 웹(WebGL)에서는 브라우저 저장소(IndexedDB)로, 폰·PC 에서는 파일·레지스트리로 알아서 보내 준다.
// 저장소가 막혀 있어도(사생활 보호 창 등) 게임은 돌아가야 해서 모든 읽기·쓰기를 try/catch 로 감싼다.
// =============================================================================
using Chasa.Core;
using UnityEngine;

public static class SaveStore
{
    const string SaveKey = "chasa.save.v1", SettingsKey = "chasa.settings.v1";

    public static bool Exists { get { try { return PlayerPrefs.HasKey(SaveKey); } catch { return false; } } }

    public static string Read() { try { return PlayerPrefs.GetString(SaveKey, ""); } catch { return ""; } }

    public static bool Write(string text)
    {
        try { PlayerPrefs.SetString(SaveKey, text); PlayerPrefs.Save(); return true; } catch { return false; }
    }

    /// <summary>"처음부터": 저장을 지운다(다음에 켜면 새 게임)</summary>
    public static void Delete() { try { PlayerPrefs.DeleteKey(SaveKey); PlayerPrefs.Save(); } catch { } }

    // ---- 설정: 한 번 읽어 두고 모두가 같은 값을 본다(소리·흔들림)
    static GameSettings settings;
    public static GameSettings Settings
    {
        get
        {
            if (settings == null) { string t = ""; try { t = PlayerPrefs.GetString(SettingsKey, ""); } catch { } settings = t.Length == 0 ? new GameSettings() : GameSettings.Parse(t); }
            return settings;
        }
    }

    public static void SaveSettings()
    {
        GameSettings.Clamp(Settings);
        try { PlayerPrefs.SetString(SettingsKey, Settings.Serialize()); PlayerPrefs.Save(); } catch { }
    }
}
