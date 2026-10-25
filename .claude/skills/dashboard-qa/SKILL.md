---
name: dashboard-qa
description: 작업 지도·대시보드·전자책 같은 오너용 웹 페이지를 게시하기 전 검수할 때 쓴다. 폰/PC 스크린샷, 글씨 크기·대비, 렉(긴 작업) 측정, 가로 스크롤 검사.
---

# dashboard-qa — 오너용 화면 게시 전 검수 (대시보드·소설 전자책)

> 오너는 **폰**으로 본다. 과거 지적: 허접함, 흐림, 작은 글씨, 렉, 진행도 안 보임. 같은 지적을 되풀이하지 않도록 **게시 전 기계 검사**를 한다.

## 합격선 (전부 통과해야 보고)
| 항목 | 기준 | 측정 |
|---|---|---|
| 글씨 크기 | 본문 ≥ 16px, 보조 ≥ 14px (한글) | 계산된 스타일 전수 조사 |
| 대비 | 일반 글씨 ≥ 4.5:1 | 글자색·배경색 계산 |
| 가로 스크롤 | 390px 폭에서 없음 | `scrollWidth <= innerWidth` |
| 선명도 | 레티나(DPR 2) 스크린샷에서 흐림 없음, 캔버스 해상도 = 화면 × DPR | 눈으로 + 코드 확인 |
| 렉 | 스크롤/탭 전환 중 50ms 초과 긴 작업 0건 | PerformanceObserver `longtask` |
| 진행도 | 한눈에 전체 % 와 현재 단계 | 눈으로 |
| 콘솔 | 에러 0건 | 콘솔 수집 |
| 다크모드 | 어두운 배경에서도 위 기준 통과 | 두 모드 모두 |

## 절차
1. Playwright로 열기(클라우드에 설치돼 있음, 재설치 금지): 뷰포트 390×844(DPR 2)와 1366×768 스크린샷 각각.
2. 아래 스니펫으로 글씨/가로 스크롤/긴 작업을 수집한다.
```js
// 페이지 안에서 실행: 작은 글씨·가로 스크롤 검사
const small=[...document.querySelectorAll('body *')].filter(e=>e.childNodes.length&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())&&parseFloat(getComputedStyle(e).fontSize)<14).length;
({small, hscroll: document.documentElement.scrollWidth>innerWidth});
```
3. 끌기·확대 캔버스 지도 같은 **직접 구현 제스처는 쓰지 않는다**(렉·흐림의 원인). 브라우저 기본 스크롤 + CSS 사용.
4. 결과 표(항목/기준/측정값/통과)를 아트팀에 보내 시각 검수를 받은 뒤에만 오너에게 보고한다.
5. 글꼴은 페이지에 직접 포함(Pretendard → 실패 시 Noto Sans KR). 시스템 글꼴 의존 금지.
