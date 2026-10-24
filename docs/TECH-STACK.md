# P1-003 기술 스택 결정서 (Unity 기준, 1차)

> 엔진·버전 관리·빌드 파이프라인·데이터 저장을 한 장으로. 엔진은 오너가 **Unity**로 확정(2026-10-24).
> 🔴 = 아직 확정 못 한 곳(근거 부족) · ✅ = 근거 있는 결정.

## 1. 엔진
| 항목 | 결정 |
|---|---|
| 엔진 | ✅ **Unity 6 LTS** (정확한 버전은 PC 설치 시 공식 아카이브에서 확인해 이 표에 기록 🔴) |
| 언어 | ✅ C# (시험판 `unity/Assets/Scripts`가 Godot판과 같은 구조·숫자로 이미 있음. 컴파일은 PC 설치 뒤 검증) |
| 렌더 | 🔴 시험판은 Built-in(가장 단순). **본편은 URP 권장**(Unity 6 표준, 모바일 최적화, 시야 축소·번짐 같은 화면 효과에 포스트 프로세싱 필요). 팔레트 작업(P1-031) 전에 확정 |
| 입력 | ✅ Unity **Input System** 패키지 + 입력 추상화 계층(P1-016): PC 마우스/키보드와 모바일 터치를 같은 "명령"으로 |
| 플랫폼 | ✅ PC(Windows) + 모바일(Android 먼저, iOS는 맥·Xcode 필요) + 웹(Unity Web, 비교용 배포) |

## 2. 버전 관리
- ✅ **Git + GitHub** (`hun100b-dotcom/chasa`).
- ✅ Unity 설정: Asset Serialization = **Force Text**, Meta Files = Visible → AI가 장면·프리팹을 텍스트(YAML)로 읽고 고칠 수 있고, 충돌도 줄어듦.
- ✅ 큰 파일(텍스처·모델·오디오)은 **Git LFS**. `Library/`, `Temp/`, `Build/`는 올리지 않음(.gitignore).
- ✅ 숫자는 `Config.cs` 한 파일에 COMBAT-SPEC ID와 1:1 (Godot판 `config.gd`와 같은 규칙).

## 3. 빌드·테스트 파이프라인
| 단계 | 방법 | 상태 |
|---|---|---|
| 로컬 빌드 | `Unity -batchmode -quit -executeMethod BuildScript.BuildWebGL` (이미 작성, `unity/Assets/Editor/BuildScript.cs`) | ✅ 작성됨, 설치 뒤 실행 검증 |
| 자동 테스트 | Unity Test Framework(EditMode/PlayMode)를 batchmode로. Godot `smoke_test.gd` 49개 검사를 같은 내용으로 이식 | 🔴 이식 필요 |
| 웹 배포 | 빌드 결과를 Vercel에 올림(오너 승인 문구 필요한 점은 그대로) | ✅ 경로 있음 |
| CI(자동 빌드) | GitHub Actions + game-ci 계열. Unity 라이선스를 CI에서 활성화하는 방법은 Personal 기준 별도 확인 필요 | 🔴 미확인 |
| 모바일 | Android: PC에서 가능. iOS: 맥 빌더(클라우드 맥 러너) 필요 | 🔴 Phase 2 |

## 4. 데이터 저장
| 데이터 | 결정 |
|---|---|
| 혼 기억 DB (이름혼 18·보스 2·단서 F1~F9, 서사팀이 만든 `docs/narrative/soul_memories.json`) | ✅ **JSON이 원본(편집용)**, 빌드 때 Unity ScriptableObject로 가져와 게임이 읽음. 서사팀은 JSON만 고치면 됨 |
| 게임 수치 | ✅ `Config.cs` (ID 1:1). 밸런스 시뮬(`tools/*.py`)은 같은 값을 읽도록 맞춤 🔴 |
| 세이브(진행 저장) | 🔴 Phase 2. 1차는 로컬 JSON 파일. 클라우드 세이브는 백로그 |
| 에셋(그림·소리) | `assets/` 폴더 규칙(하네스 룰 3), 프롬프트 기록 `assets/**/README.md` |

## 5. Godot판의 역할
Godot 시험판(`godot/`)은 **규칙·수치 검증 기준**으로 보존한다: 핵심 루프(처결 대기·천도·파혼·얼룩), 업 단계, 맵 생성기, 검사 49개. Unity판은 이를 같은 숫자로 이식하고, 이식 후 같은 검사를 통과해야 "동등"으로 본다.

## 6. 열린 질문 / 다음
1. Unity 설치·라이선스 인증 완료 후: 버전 번호 기록, `unity/` 컴파일·빌드 검증.
2. 렌더 파이프라인(URP) 확정 → P1-031 팔레트 토큰.
3. 입력 추상화 설계 → P1-016 (이제 엔진이 정해져 진행 가능).
4. CI 라이선스 방식 확인.
