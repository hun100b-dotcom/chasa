# CLAUDE.md — 차사(Chasa) 프로젝트 지침서

> 작게 유지한다. 문서가 코드보다 무거워지면 안 된다.

## 오너
**종훈님은 코딩 지식이 없는 비전공자**다. 터미널·깃·배포는 직접 실행하고,
오너에게는 "링크 하나 눌러서 해보기" 이상을 요구하지 않는다.
문제를 발견하면 숨기지 않고 보고한다.

## 프로젝트
**차사(Chasa)** — 저승차사 소재 한국 설화 쿼터뷰 액션 RPG. 사슬(철삭)로 싸운다.
GitHub: `hun100b-dotcom/chasa` (Public, 기본 브랜치 `main`)

## 기술 스택
Vite + TypeScript + Three.js (정적 빌드, 서버·환경변수 없음)

## 지금의 핵심 원칙 (단계 0)
1. **손맛 우선.** 목표는 "때리는 손맛이 재밌는가"를 확인하는 것 하나.
2. **에셋 없음.** 그림·소리·모델 없이 색깔 도형만 쓴다. 에셋은 손맛이 검증된 뒤에.
3. **숫자의 원본은 `data/balance.json`** (엔진 무관). 고친 뒤 `python3 tools/sync_balance.py`로 Godot·Unity에 반영, `--check`로 어긋남 검사. (옛 웹판은 `src/config.ts`)
    감으로 잡는 값은 코드에 흩뿌리지 않는다.
   오너가 "히트스톱 더", "흔들림 줄여"라고 하면 config.ts 맨 위 "빠른 찾기표"로 값을 집는다.
4. 적 AI·UI·메뉴·사운드는 이 단계에서 일부러 안 만든다.

## 작업 규칙
- **시작 전:** `git pull` 후 `git status`, `git log -3`로 최신인지 확인.
- **끝낼 때:** `docs/progress.md` 맨 아래에 항목 추가 → 커밋 → `main`에 push.
- **모든 코드에 한국어 주석.** "무엇을"보다 "왜"를 적는다. 전문 용어는 괄호로 풀어 쓴다.
- 확인은 실제로 돌려서 한다: `npm run build`(에러 없어야 함) + 브라우저에서 조작해 보기.

## 명령어
```
npm install      # 처음 한 번
npm run dev      # http://localhost:5173
npm run build    # 타입 검사 + 빌드
```

## 폴더
`src/config.ts` 조절판 · `player.ts` 이동·콤보·견인 · `enemy.ts` 적 · `chain.ts` 사슬/잔상 ·
`effects.ts` 히트스톱·흔들림·숫자 · `stage.ts` 카메라/바닥 · `input.ts` 입력 · `main.ts` 루프.
상세는 README.md.
