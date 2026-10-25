---
name: unity-batch
description: Unity 프로젝트(unity/)를 에디터 창 없이 컴파일 검사·EditMode 테스트·WebGL 빌드할 때 쓴다. 코드 작업이 "돌아간다"고 보고하기 전 검증 절차, .meta/씬 파일 규칙, 흔한 실패 원인 포함.
---

# unity-batch — Unity 배치모드 검증 절차 (코드·QA 팀)

> 왜 필요한가: 오너는 Unity를 직접 열어주지 못한다. 코드팀이 **창 없이(batchmode)** 스스로 컴파일·테스트·빌드를
> 돌려 "돌아가는 것을 봤다"를 증명해야 한다(CLAUDE.md §6).

## 0. 사전 확인 (1분)
1. `unity/ProjectSettings/ProjectVersion.txt` 의 정확한 버전 확인(현재 6000.3.27f1).
2. `unity/Temp/UnityLockfile` 이 있으면 **에디터/다른 배치가 이 프로젝트를 열고 있는 것** → 기다리거나 끝날 때까지 새로 실행하지 않는다
   (한 프로젝트는 한 번에 한 Unity만 연다).
3. 다른 팀이 같은 `unity/` 파일을 수정 중인지 `git status` 로 확인.

## 1. 한 줄 실행 (권장 — 요약까지 해줌)
```
node tools/unity-test.mjs                 # EditMode 테스트
node tools/unity-test.mjs --build-webgl   # WebGL 빌드 (BuildScript.BuildWebGL)
node tools/unity-test.mjs --parse 결과.xml # 이미 있는 결과 XML만 요약
```
종료코드: 0 통과 / 2 테스트 실패 / 1 그 외 오류(컴파일 에러·라이선스·잠금 등).

## 2. 직접 실행할 때 (Windows)
- 에디터: `C:\Users\hun10\Unity\Editor\6000.3.27f1\Editor\Unity.exe`
- 테스트: `-batchmode -nographics -projectPath <unity> -runTests -testPlatform EditMode -testResults <xml> -logFile <log>`
  - **`-runTests` 와 `-quit` 는 같이 쓰지 않는다**(테스트가 끝나기 전에 종료될 수 있음).
  - PlayMode 테스트는 `-nographics` 불가(렌더링 필요). 로직은 순수 C#(`Chasa.Core`)로 빼서 EditMode로 검증한다.
- 메서드 실행/빌드: `-batchmode -quit -projectPath <unity> -executeMethod BuildScript.BuildWebGL -logFile <log>`
- 로그는 반드시 파일로 받고, **에러 줄(`error CS`, `Exception`)만 grep** 해서 보고한다(전체 로그를 채팅에 붙이지 않는다).

## 3. 하드 규칙 (어기면 프로젝트가 깨진다)
1. `.unity` `.prefab` `.asset` `.meta` 는 **텍스트로 직접 편집하지 않는다.** 씬/프리팹 변경은 Editor 스크립트(`Assets/Editor/`)로 한다.
   임시 생성 스크립트는 `Assets/Editor/Temp/` 에 두고 작업 끝에 지운다.
2. 새 `.cs`/`.asmdef` 를 만들면 Unity가 `.meta` 를 만든다 → 배치 실행 후 생긴 `.meta` 를 **스크립트와 함께 커밋**.
3. `Library/ Temp/ Obj/ Build/ Logs/ UserSettings/ *.csproj *.sln` 는 커밋 금지(.gitignore).
4. 어셈블리 경계: `Chasa.Core`(순수 규칙, Unity 의존 최소) ← `Chasa.Tests`(EditMode). 새 규칙은 Core에 + 테스트 먼저.
5. 숫자는 `Balance`(← `data/balance.json`)에서만. 코드에 숫자 박지 않는다.
6. 입력은 New Input System 기준 설계(입력 추상화 계층 P1-016), 레거시 `Input` 직접 호출 금지(예외: 시험판 한정, 주석으로 표시).
7. MonoBehaviour: 컴포넌트 참조는 `Awake`에서 캐시, `Update`에서 `GetComponent`/`Find`/LINQ/문자열 연결 금지(GC·성능), 이벤트는 `OnDestroy`에서 해제,
   `UnityEngine.Object` null 검사에 `?.` 금지.
8. 모바일 목표: 쿼터뷰 다수 적 → 오브젝트 풀링, 드로우콜·GC 의식. 성능 수치는 추측 말고 프로파일러/로그 수치로.

## 4. 실패 원인 빠른 표
| 증상 | 원인 | 조치 |
|---|---|---|
| 종료코드 1, 로그에 `error CS` | 컴파일 에러 | 에러 줄만 뽑아 수정 후 재실행 |
| `Licensing`/`entitlement` 문구 | 라이선스 미활성 | 에디터 로그인 필요 → 코드팀이 상태만 보고(오너에게 클릭 요구 금지, 보류 처리) |
| `another Unity instance is running` | 프로젝트 잠금 | 실행 중인 Unity 종료 대기 |
| 테스트 0개 실행 | asmdef 참조/`UNITY_INCLUDE_TESTS` | `Chasa.Tests.asmdef` 확인 |
| 결과 XML 없음 | 크래시/타임아웃 | 로그 꼬리 50줄 확인, `-playerHeartbeatTimeout` 조정 |

## 5. 선택: Editor 연결형 도구 (필요해질 때만)
- **MCP for Unity**(CoplayDev, MIT): 에디터를 켜 둔 채 씬/프리팹/에셋을 MCP로 조작. Unity 2021.3~6.x, Python 3.10+(uv).
  설치: Package Manager → Add from git URL `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.0.0`.
  씬 배치·프리팹 작업이 늘어나는 시점(UI/스킬트리/맵 제작)에 코드팀이 PC에서 직접 설치·검증한다.
- **Unity 공식 에이전트 플러그인**: `claude plugin marketplace add Unity-Technologies/unity-agent-plugin` →
  `claude plugin install unity@unity-agent-plugin` (Unity 6+, UI/URP/WebGL 최적화 스킬 포함).
