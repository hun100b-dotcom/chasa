# 아트 디렉션 준비물 (2026-10-24) — 도형 제작 중단 후 방향 결정용

작성: 아트팀. 금액·요금은 전부 **추정 또는 제3자 글 인용**이며 견적·공식 요금표로 확인 전에는 확정값이 아니다.

## 1. Higgsfield 첫 시험 세트 (주인공 기준 시트 1장 · 혼 1종 · 솔고개 타일 1장)

### 1-1. 순서와 기준 이미지 전략
1. **주인공 후보 뽑기**: 아래 프롬프트 A를 해상도 최대(1024 이상)로 8~12장 생성. 한 번에 한 변수만 바꾼다(포즈 고정, 시드만 변경).
2. 합격 기준을 통과한 1장을 **기준 시트(레퍼런스)** 로 확정하고 `assets/final/characters/chasa_idle_ref.png` 로 저장. 이후 모든 주인공 생성은 이 이미지를 레퍼런스로 붙인다.
3. **혼 1종**: 프롬프트 B, 주인공 기준 시트를 *스타일 레퍼런스*로 붙여 화풍을 맞춘다(구도는 고정하지 않음). 4~6장.
4. **타일 1장**: 프롬프트 C. AI는 정확한 마름모를 못 만들 때가 많으므로 우리 기존 `tile_grass_a.png`(128×64)를 *구조 레퍼런스*로 붙이고, 그래도 안 되면 결과를 마름모 마스크로 잘라 쓴다(후처리 허용).
5. 각 결과는 `assets/prompts/higgsfield/README.md` 로그 표에 프롬프트·날짜·모델·시드·채택 여부를 남긴다.

### 1-2. 명령문 (art-prompt-gate·IP 검사 통과본, PROMPT-PACK.json 과 동일)
**A. 주인공 (characters/chasa_idle)**
```
front view of a Korean afterlife escort in a tall black horsehair hat (heukrip) with a wide flat brim, long black overcoat (dopo) with wide sleeves, a red sash #E85C41 at the waist, a chain (cheolsak) in pale blue #BFE8FF, and a small floating teal soul-flame #5FE3C0 near the shoulder, standing relaxed, chain hanging from the right hand. Korean folk dark-fantasy game art, painterly gothic with traditional dancheong accent colors, quarter-view 45 degree 2:1 isometric camera, low-key lighting, desaturated navy ambient light #16213E, deep shadow #0F1729, teal rim light #4FA8A0, warm hanji paper texture #F3E7D3, soft contact shadow, clean readable silhouette that still reads when filled solid black. isolated on a flat solid #00FF00 chroma-key background, no ground, no text.
NEGATIVE: scythe, skull face, kimono, hooded robe, pixel art, photorealistic, text, watermark, logo, extra limbs, cropped, busy background, anime style
```
**B. 혼 (enemies/soul_fresh)**
```
a freshly dead soul, almost a living person, clear outline and readable sad face, pale-blue hanbok-like clothes #BFE8FF, translucent glow. [위 공통 스타일 문장 동일] isolated on a flat solid #00FF00 chroma-key background, no ground, no text.
NEGATIVE: (A와 동일)
```
**C. 타일 (tiles/tile_grass_a)**
```
a single seamless isometric diamond ground tile, 2:1 ratio: dark green night grass with short blades, top-down lighting, no objects, edges tileable. [위 공통 스타일 문장 동일] flat solid #00FF00 outside the diamond.
```
시험 때 바꿔 볼 것: 해상도는 1024로 뽑고 128/256으로 줄인다. 타일 프롬프트의 "no ground"는 모순이므로 제거했다(팩 원문에는 남아 있어 수정 필요).

### 1-3. 합격 기준 (모두 통과해야 채택)
| 항목 | 기준 | 확인 방법 |
|---|---|---|
| 투명 배경 | #00FF00 키를 제거했을 때 가장자리에 초록 번짐 없음 | 어두운 배경(#16213E)에 올려 눈으로 확인 |
| 고정 5요소 | 흑립·검은 도포·붉은 띠·철삭·혼불이 전부 보임. 낫·해골·기모노·후드 없음 | 체크리스트 |
| 일관성 | 같은 기준 시트로 4장 뽑아 4장 모두 의상·색 구성이 같음(얼굴 세부는 허용) | 나란히 비교 |
| 읽힘 | 검게 칠해도 모자 챙, 소매, 사슬로 주인공임이 구별됨 | 실루엣 변환 |
| 크기 | 최종 256×256(주인공)/192×256(혼)/128×64(타일), 발 기준 위치 고정(피벗 표 SPRITE-SPEC) | 규격 스크립트 |
| 타일 | 2×2로 이어 붙였을 때 이음매가 눈에 띄지 않음, 마름모 꼭짓점이 정확 | 타일 이음 테스트 |
| 팔레트 | 주요 색이 팔레트 토큰과 크게 어긋나지 않음, 혼은 바닥 대비 3:1 | 대비 검사 |
| 법적 | IP 검사 통과 + 서비스 약관상 상업 이용 가능한 요금제인지 확인 | 약관 확인(미확인) |

### 1-4. 사전 확인 필요
- Higgsfield 요금(제3자 글 기준, 미확인): 무료 일 10크레딧, Starter 월 $15·200크레딧, Plus $34·1,000, Ultra $84·3,000. 공식 표는 higgsfield.ai/pricing. **생성물의 상업 이용 가능 범위는 확인하지 못했다.**
- 한계: 주인공을 여러 포즈·프레임에 일관되게 이어 가는 일, 투명 배경, 타일 이음은 실제로 해 보기 전에는 되는지 모른다. 이 시험이 그것을 확인하는 용도다.

## 2. 외주 의뢰서 초안

**프로젝트**: 차사(Chasa) — 저승차사가 사슬로 싸우는 한국 설화 소재 쿼터뷰(2:1 등각) 다크 판타지 액션 RPG. Unity 6, PC·모바일.

**1단계 범위(시연판, 제안)**
| 구분 | 수량 | 비고 |
|---|---|---|
| 주인공 | 기준 시트 1 + 포즈 8 | 정면 1방향, 좌우 반전 사용. 걷기 4프레임 이상 권장 |
| 혼 | 4단계 × (서기·무릎) | 갓 죽은/해 넘긴/오래된/덩어리 |
| 보스 | 1체(나루 영감) | 대기·공격 예비동작 |
| 타일 | 6종 × 변형 2 | 128×64 |
| 소품 | 13종 | 초가·기와집·서낭나무 등 |
| HUD·아이콘 | 35 + 장비 아이콘 50 | 후순위 가능 |

**기술 규격**: PNG 투명 배경, 텍스처 PPU 128, 타일 128×64, 캐릭터 256 캔버스(발 기준 피벗은 SPRITE-SPEC.md), 파일명은 `assets/sprites/manifest.json`과 동일, 원본(PSD/CLIP 등 레이어) 함께 납품.

**스타일 가이드**: 한국 민화·단청 포인트의 painterly gothic. 저채도 남청 환경(#16213E)에 청록 림 라이트(#4FA8A0), 오방색 포인트는 소량. 주인공 고정 5요소: 흑립·검은 도포·붉은 띠(#E85C41)·철삭(#BFE8FF)·혼불(#5FE3C0). 검게 칠해도 실루엣으로 구별. 팔레트 토큰: docs/art/palette-tokens.json. 현재 임시 그림은 `assets/sprites/`(참고용, 품질 기준 아님).

**금지**: 일본식 사신 도상(낫·해골·기모노·후드), 특정 기존 작품의 캐릭터·세계관 모방(금지 목록은 tools/ip-scan.mjs), 생성형 AI 산출물의 무단 사용(사용 시 사전 고지·합의).

**권리**: 저작재산권 양도 또는 독점 이용 허락, 2차 가공 허용, 포트폴리오 공개는 출시 후. **납품물이 공개 저장소에 올라가지 않도록** 비공개 저장소를 쓴다.

**일정·지급**: 시안 3안(콘셉트) → 확정 후 본작업 → 수정 2회. 마일스톤별 분할 지급(착수 30 / 시안 확정 30 / 납품 40, 제안).

**예상 견적 범위(추정, 견적 필수)**: 개인 작가 기준 주인공 기준 시트 + 포즈 수십만~수백만 원, 혼 4단계와 보스 1체 수백만 원대, 타일·소품 수백만 원대, 전체 1단계 합계 수백만~천만 원대 이상(범위가 매우 큼). 애니메이션 프레임과 HUD를 포함하면 늘어난다. 최소 3곳에서 견적을 받을 것.
**섭외처 후보**: 국내 재능 마켓(크몽 등), ArtStation, 인디게임 커뮤니티. 제작 전에 포트폴리오로 한국 설화·어두운 톤 경험을 확인.

## 3. 에셋 스토어 후보 조사

**확인한 것(페이지 직접 열람)**
| 후보 | 가격 | 메모 |
|---|---|---|
| [2D Isometric Fantasy Heroes Sprites ×9 Animations](https://assetstore.unity.com/packages/2d/characters/2d-isometric-fantasy-heroes-sprites-x-9-animations-84772) | $10 | 등각 판타지 영웅. 크기 1.0GB. 설명·미리보기가 없어 화풍은 직접 확인 필요. 서양 판타지일 가능성이 높아 한국 설화 톤과 어긋날 수 있음 |
| [Dark Fantasy 2D Game Pack (UI·HUD·타일·캐릭터·VFX)](https://assetstore.unity.com/packages/2d/gui/icons/dark-fantasy-2d-game-pack-ui-hud-tiles-characters-vfx-126098) | $19.99 | UI·HUD·VFX 보강용 후보. 2022년 버전, 평가 수 부족, 쿼터뷰 여부 불명 |
| itch.io [Isometric Character](https://otsoga.itch.io/isometric-character), [Isometric Character Prototype](https://dark-kahon.itch.io/isometric-character-prototype-asset-pack) | 페이지 미확인 | 프로토타입용 후보 |

**솔직한 한계**: 검색으로 확인한 범위에서 "쿼터뷰 + 한국 설화 + 다크 판타지"가 맞는 패키지는 찾지 못했다. 에셋은 타일·UI·이펙트 같은 범용품 보강에 쓰고, 주인공·혼·보스는 우리 고유 디자인이어야 하므로 대체하기 어렵다. 이 조사는 일부 페이지만 본 것이라 전수 조사가 아니다.

**라이선스(Unity 에셋 스토어 FAQ 확인)**
- 상업 게임에 포함해 판매 가능. 단 좌석 수만큼 라이선스(Single Entity는 개인·소규모, 사람 수 기준).
- **에셋은 게임에 내장된 형태로만 배포 가능하고, 사용자가 따로 추출·다운로드할 수 있으면 안 된다.** 우리 저장소 `hun100b-dotcom/chasa`는 **Public**이므로 구입한 에셋 원본을 커밋하면 위반 소지가 있다. 에셋은 비공개 저장소나 gitignore 처리해야 한다. (외주 납품물도 같다)
- 수정은 SDK가 아닌 에셋이면 가능. EULA에는 AI 관련 규정이 없어, AI 학습·가공 용도는 판매자 문의 필요.
- 다른 에셋 판매자(itch.io 등)는 개별 라이선스가 다르므로 상업 이용·수정·재배포 항목을 구입 전에 읽는다.

**IP 금지선**: 팩 이름·미리보기가 특정 인기 작품을 노골적으로 따라 한 것은 제외. 사신 소재 팩은 낫·해골·후드 도상이 많아 우리 금지 도상(일본식 사신)과 충돌하므로 원본 그대로는 불가. 구입 전 스크린샷을 아트팀이 확인한다.

## 4. 아트팀 추천
1. 이번 주 안에 Higgsfield 시험 세트를 돌려 합격 기준 통과 여부를 본다(비용 최소).
2. 결과가 좋으면 AI 중심 + 주인공·보스만 외주 다듬기, 나쁘면 외주 중심으로 간다.
3. 어느 쪽이든 파일명·규격·팔레트·맵 데이터는 지금 것을 그대로 쓴다.
