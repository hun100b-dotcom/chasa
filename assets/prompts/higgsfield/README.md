# Higgsfield 프롬프트 팩 (파일명 1:1)

`PROMPT-PACK.json` 의 `items[].file` = `assets/sprites/` 의 임시 그림 파일명과 같다.
최종 그림은 같은 이름으로 `assets/final/<file>` 에 저장한다 (코드 쪽 교체 시 이름 변경 없음).

## 규칙 (art-prompt-gate)
1. 작품명·작가명 0개. `node tools/ip-scan.mjs assets/prompts/higgsfield` 통과 후에만 생성.
2. 색은 HEX로 명시. 주인공 고정 5요소(흑립·검은 도포·붉은 띠·철삭·혼불), negative에 낫·해골·기모노·후드.
3. 한 번에 한 변수만 바꾼다 (`change_only` 칸 참고).
4. 처음 승인된 chasa_idle 이 기준 시트. 이후 모든 생성은 이를 reference 로 붙인다.
5. 생성 후 아래 로그에 프롬프트·날짜·모델·시드를 남긴다.

## 로그 (생성할 때마다 한 줄 추가)
| 파일 | 날짜 | 모델 | 시드 | 채택 | 비고 |
|---|---|---|---|---|---|

## 상태
Higgsfield MCP 연결 전까지 보류 (P1-032). 연결되면 이 팩 순서대로 생성.
