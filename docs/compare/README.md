# 옛 화면 vs 새 화면 비교 (2026-10-25, PC 녹화)

> 이 폴더가 왜 있는가: 오너가 새 3D 화면을 채택할지 영상으로 비교해 보고 정하기 위한 자료.
> 메인 작업 브랜치에는 영상을 넣지 않는다(저장소가 무거워지므로) → 이 브랜치에만 둔다.

## 녹화 조건
- 빌드: `claude/project-thread-ozfksa` @ `137baef` (동이 = Kenney CC0 캐릭터), Unity 6000.3.27f1 WebGL, 45.87MB(압축 전)
- 헤드리스 Chrome(창 없음) 1280×720, Playwright 녹화 → ffmpeg H.264, 25fps, 28초(페이지 로드 3초 뒤부터)
- 주소: 옛 `?demo=1` / 새 `?v=3d&demo=1&cam=a` (스크린샷 cam=b, cam=c 추가)
- `?demo=1` 자동 연출: 철삭 3타 → 천도 1회 → 피하기 (난수 고정, 입력 없음)

## 파일
| 파일 | 내용 |
|---|---|
| `compare-old-vs-new.mp4` | 왼쪽 OLD, 오른쪽 NEW(cam=a) 나란히 |
| `old-A.mp4` / `new-B-cam-a.mp4` | 각각 단독 |
| `new-cam-a.png` | 새 화면 cam=a, 3타 중 |
| `new-cam-a-casting.png` | 새 화면 cam=a, 천도 캐스팅 중(보랏빛) |
| `new-cam-b.png` / `new-cam-c.png` | 카메라 b·c 고정 시점 |

## 측정
| 화면 | 콘솔 오류 | 평균 프레임 | 최대 프레임 | 50ms 넘는 프레임 |
|---|---|---|---|---|
| 옛(A) | 0 | 6.1ms | 12.2ms | 0 |
| 새 cam=a(B) | 0 | 6.1ms | 24.2ms | 0 |
| 새 cam=b(C) | 0 | 6.1ms | 24.2ms | 0 |
| 새 cam=c(D) | 0 | 6.1ms | 12.2ms | 0 |
(헤드리스라 화면 갱신이 실제 모니터보다 빠르다. 절대값보다 '튐 없음'을 볼 것)

## 눈에 띈 점
- 동이(Kenney 캐릭터)가 색 지도(colormap)를 입고 바로 서서 움직인다(T자로 굳지 않음, 땅에 묻히지 않음).
- **cam=a 에서 서낭나무 잎(큰 어두운 덩어리)이 동이를 가린다** — 특히 천도 캐스팅 순간에 동이가 거의 안 보인다(`new-cam-a-casting.png`). cam=c 는 가림이 덜하다.
- 새 화면은 서낭당 주변만 보이고 옛 화면의 초가·장독·장승 배치가 아직 3D로 옮겨지지 않아 비어 보인다.

## 2026-10-25 04:30 KST — 0단계·1단계 빌드 (작업 브랜치 3ada00d + 34673f6)
- `stage0-default-hud.png` — 주소 옵션 없이 연 기본 화면: 새 HUD(왼쪽 위 장부 쪽지), 콘솔 오류 0
- `stage1-demo-cam-a.mp4` — ?demo=1&cam=a 30초 (원본 영상 4초 지점부터). 데모는 혼 1마리 3타→천도→피하기 후 멈춤
- `stage1-combo-hit.png` — 3타 콤보 중 사슬 휘두름 순간
- `stage1-toast-skillbar.png` — 천도 직후: '넋 +10 / 기억 +1' 알림이 왼쪽 가운데가 아니라 왼쪽 위에 겹쳐 뜸, 아래쪽 기술 줄 안 보임
- `village-art-props.png` — 아트팀 OBJ 소품(우물·상여·기와집·장승·돌담)
- `village-glb-choga-gray.png` — (임시 시험 빌드) 초가를 GLB 로 바꿔 끼운 화면: 색이 회색으로 나옴(재질 색 속성 이름 차이)

## 2026-10-25 05:55 KST — 1단계 수정 재확인 (작업 브랜치 d4aad92)
- `stage1b-demo-cam-a.mp4` — ?demo=1&cam=a 30초(원본 4초 지점부터). 혼 여러 마리를 돌며 때림, 천도는 1회(그 뒤 '대상이 없다' 반복)
- `stage1b-skillbar-toast.png` — 아래 가운데 기술 줄(무기 철삭 / E 천도 / R 파혼 / Q 끌어당김 / Space 피하기◆◆), 왼쪽 가운데 '넋 +10 / 기억 +1'
- `stage1b-glb-choga-color.png` — (임시 시험) GLB 초가: 흙벽·초가 색이 제대로 나옴(오른쪽 아래)

## 2026-10-25 06:10 KST — 새 주인공 GLB 연결 확인 (작업 브랜치 f8fdb65)
- `stage1c-demo-cam-a.mp4` — ?demo=1&cam=a 30초. 주인공=아트팀 GLB(검은 도포·갓). 이 빌드는 데모 중 천도 0회(끝까지 천도 0/3)
- `stage1c-hero-body.png` — 주인공 서 있는 모습(확대)
- `stage1c-combo-1-2-3.png` — 1·2·3타 순간(?debug N 키)
- `stage1c-tendo-cast.png` — 천도 시전 자세(팔을 들어 올림, ?debug K→E). 이 경로로는 천도 1/3 정상
- `stage1c-toast.png` — '넋 +10 / 기억 +1' 알림 상자(테두리 생겨 잘 보임)

## 2026-10-25 06:15 KST — 데모 천도 수정(6d3ba8e) + 주인공 GLB 교체(9a69de4)
- `stage1d-demo-cam-a.mp4` — 데모 수정판 30초. 끝 화면 천도 0/3(아직 천도 안 됨)
- `stage1d-tendo-cast.png` — ?debug 로 혼을 쓰러뜨린 뒤 E: 천도 시전 자세(팔 들어 올림), 끝나면 천도 1/3·넋 +10
- `stage1e-demo-cam-a.mp4` — 새 주인공 GLB(3타 차별화·붉은 띠·앞면 표식) 30초. 천도 0/3
- `stage1e-combo-1-2-3.png` — 1타(팔 벌림) / 2타(옆으로 휘두름) / 3타(앞으로 숙여 내려치기)
- `stage1e-front-back.png` — 왼쪽: 화면 위쪽(카메라 반대)으로 걸어간 뒤인데 앞면 장식(금 장식·붉은 띠 매듭)이 카메라를 봄 → 모델이 진행 방향 반대(180°)로 보임

## 2026-10-25 06:30 KST — 앞 방향 보정·데모 천도 안정화 (작업 브랜치 716d67a)
- `stage1f-demo-cam-a.mp4` — 30초. 끝 화면 천도 0/3 (데모 코드의 alive/kneeling 조건 충돌 — 보고 참고)
- `stage1f-facing-up-down-left-right.png` — 빈 땅에서 위·아래·왼쪽·오른쪽으로 걸은 뒤: 위=뒷모습, 왼쪽=갓 금장식 왼쪽, 오른쪽=앞면 장식이 보임 → 앞뒤 보정 정상
- `stage1f-tendo-cast.png` — ?debug 천도 시전(끝나면 천도 1/3, 넋 +10)
