# 차사 단계 0 — Unity판 (엔진 손맛 비교용)

Godot판(`godot/`)과 **같은 숫자·같은 조작**(흔들림 절반, 마우스 이동·대상 / Q 견인 / Space 제자리 휘두르기)으로 만든 비교용 시험판.
씬은 비어 있고, 게임이 켜지면 `GameMain.cs`가 코드로 전부 만든다(AI가 편집기 없이 고칠 수 있게).

| Godot판 | Unity판 |
|---|---|
| `config.gd` | `Assets/Scripts/Config.cs` |
| `main.gd` | `GameMain.cs` |
| `player.gd` | `Player.cs` |
| `enemy.gd` + `enemy_manager.gd` | `Enemy.cs` |
| `chain_visual.gd` | `ChainVisual.cs` |
| `hit_feel.gd` / `damage_numbers.gd` / `click_marker.gd` | `HitFeel.cs` / `DamageNumbers.cs` / `ClickMarker.cs` |

## 웹 빌드 (편집기 화면 없이)
```
Unity.exe -batchmode -quit -projectPath unity -executeMethod BuildScript.BuildWebGL -logFile -
```
결과물: `unity/Build/web/` (압축 끔 — Vercel이 자동 압축).
