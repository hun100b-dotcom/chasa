# HARNESS.md — 팀별 하네스 지도 (2026-10-24 점검판)

> **이 파일이 왜 존재하는가**
> 팀이 6개로 늘면서 "누가 어떤 파일을 소유하는지 / 어떤 도구로 검증하는지 / 어디에 결과를 모으는지"가
> 사람 머릿속과 채팅에만 있었다. 그러면 같은 파일을 동시에 고치거나, 숫자가 팀마다 달라진다
> (실제 사례: 업 감쇠 후 기억 기준 150 vs "약 100개" 불일치). 이 파일이 그 지도다.
> 내부 문서이므로 오너에게 보여주지 않는다(보고는 채팅·대시보드).

## 1. 팀 지도

| 팀 | 모델 | 소유 파일(여기만 고친다) | 쓰는 서브에이전트 | 쓰는 스킬 | 검증 습관(끝났다고 말하기 전) |
|---|---|---|---|---|---|
| 코드·QA | Sonnet | `unity/`, `data/balance.json`, `tools/`, `docs/BALANCE-*`, `docs/TIMER-*`, `docs/TECH-STACK.md` | code-system-lead, qa-balance-lead, unity-build-verifier | unity-batch, balance-sim | 컴파일 0에러 → EditMode 테스트 통과 → WebGL 빌드 → 브라우저에서 눈으로 확인 |
| 아트 | Sonnet | `docs/art/`, `assets/` | visual-art-lead, ip-safety-auditor | art-prompt-gate | 프롬프트에 작품명 0건(ip-scan) → 팔레트 토큰만 사용 → 이미지로 보고 |
| 서사 | **Opus** | `docs/narrative/` | opus-narrative-lead, continuity-checker(Sonnet) | lore-continuity | 쓰기는 Opus, 검사는 Sonnet 서브에이전트로 → 잠금 결정과 충돌 0건 |
| 기획 | **Opus** | `planning/`, 기획서 아티팩트 | (기획 전용 없음) | lore-continuity(숫자 대조만) | 기획서 숫자 ↔ `LOCKED-DECISIONS.md` 대조 |
| 소설 | **Opus** | 소설 원고·전자책 | continuity-checker | chasa-novel(claude.ai 스킬), lore-continuity | 장마다 자동 점검기 + 잠금 결정 대조 |
| 대시보드 | Sonnet | `dashboard/`, 작업 지도 아티팩트 | (없음) | dashboard-qa | 390px·1366px 스크린샷 + 대비 4.5:1 + 렉 측정 → 아트팀 검수 → 보고 |
| 하네스 | Sonnet | `.claude/`, `docs/harness/`, `CLAUDE.md` §9 | ip-safety-auditor | (전부) | 키트 변경 시 각 팀에 메시지로 통지 |

모델 규칙(변경 금지): 기본 Sonnet / 창작 판단만 Opus / Fable은 이유+예상 소진량 보고 후 오너 승인.

## 2. 같은 파일 동시 수정 금지 — 소유권 원칙
- 위 표의 "소유 파일"은 해당 팀만 고친다. 남의 파일을 고쳐야 하면 **그 팀 스레드에 메시지**로 요청한다.
- 공용 파일(`CLAUDE.md`, `TASKS.md`, `DEVELOPMENT-LOG.md`)은 **줄 추가만**, 기존 줄 수정은 담당(코드·QA)이 한다.
- `docs/harness/LOCKED-DECISIONS.md`: 숫자·이름이 확정되면 **먼저 여기에 적고** 각 문서가 따라온다(역순 금지).
- 색 값은 아트팀만 바꾼다(`ChasaPalette.cs` ← `docs/art/palette-tokens.json`).

## 3. 브랜치·동기화 (현재 가장 큰 구조적 위험)
- SSOT는 PC `C:\Users\hun10\Github\chasa`. 그런데 클라우드 팀들은 각자 `claude/project-thread-*` 브랜치에 쓰고 있어
  **PC 쪽에 서사·아트·QC 문서가 아직 없다**(점검 시점 기준). 방치하면 팀마다 다른 진실이 생긴다.
- 원칙: ① 팀 브랜치는 자기 소유 폴더만 건드린다(충돌 없음) ② 코드·QA 팀이 PC에서 주기적으로
  `git fetch` → 소유 폴더 단위로 가져와 통합한다(`git checkout origin/<브랜치> -- docs/narrative` 식) ③ 통합 후 `TASKS.md` 갱신.
- main 직접 push 금지·force 금지는 유지.

## 4. 오너 보고 형식
채팅 본문에 `[담당 팀]`으로 시작, 표 + 핵심 3줄. `.md` 파일·터미널 작업·승인 요청을 오너에게 시키지 않는다.

## 5. 키트 목록 (이 점검에서 설치)
- 스킬: `.claude/skills/{unity-batch, balance-sim, lore-continuity, art-prompt-gate, dashboard-qa}`
- 서브에이전트: `unity-build-verifier`, `continuity-checker`, `ip-safety-auditor` (모두 Sonnet, 읽기 중심)
- 도구: `node tools/ip-scan.mjs`(작품명 금지어 검사), `node tools/unity-test.mjs`(배치모드 테스트·빌드 + 요약)
- 중첩 CLAUDE.md: `unity/CLAUDE.md`, `dashboard/CLAUDE.md` (해당 폴더 작업 때만 자동 로드 → 평소 컨텍스트 절약)
