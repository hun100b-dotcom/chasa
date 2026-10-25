# unity/CLAUDE.md — Unity 폴더 작업 규칙 (이 폴더 파일을 열 때만 자동 로드됨)

> 왜 따로 두는가: 루트 CLAUDE.md는 모든 팀이 읽는다. Unity 전용 규칙을 거기 넣으면 서사·아트 팀의 컨텍스트(비용)만 늘어난다.

- 정확한 에디터 버전은 `ProjectSettings/ProjectVersion.txt` (현재 6000.3.27f1). "Unity 6"라고만 부르지 않는다.
- 검증 절차·하드 규칙 전문은 스킬 `unity-batch`. 요약: `.unity .prefab .asset .meta` 텍스트 직접 편집 금지, 씬/프리팹은 `Assets/Editor` 스크립트로.
- 어셈블리: `Chasa.Core`(순수 규칙) ← `Chasa.Tests`(EditMode). 새 규칙 = Core + 테스트 먼저.
- 숫자는 `Balance`(← `../data/balance.json`) 한 곳. 색은 `ChasaPalette`(아트팀 소유)에서만.
- "완료" = 컴파일 0에러 + `node ../tools/unity-test.mjs` 통과 + (빌드 영향 시) `--build-webgl` 통과 + 실제 화면 확인.
- 커밋 금지: `Library/ Temp/ Obj/ Build/ Logs/ UserSettings/ *.csproj *.sln`. 새로 생긴 `.meta`는 스크립트와 함께 커밋.
- 모든 코드에 한국어 주석("왜" 중심, 전문용어는 괄호 풀이).
