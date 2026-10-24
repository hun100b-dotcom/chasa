# 임시 스프라이트 규격 (시연판 "하룻밤 한 판"용)
코드팀과 합의한 형식(2026-10-24). 원본 목록은 `assets/sprites/manifest.json`.

- 투명 PNG, 쿼터뷰 2:1. 타일 128×64, **PPU 128**(Unity Isometric 셀 1×0.5와 일치)
- 피벗은 파일별 pivotX/pivotY(0~1, 아래가 1). 캐릭터·소품은 발/바닥 중심
- Filter Bilinear, 밉맵 끔, 압축 None(임시 단계)
- 좌우는 한쪽만 그려 flipX. `tint:true` 파일은 흰색 원본 → Unity에서 색을 입힌다
- Sorting Layer는 코드팀이 폴더별 배정: Ground(tiles) < Stain < Props(props) < Actors(characters·enemies·boss) < Fx < Hud(hud)
- 다시 뽑기: `python3 tools/art/gen_sprites.py && node tools/art/render_sprites.cjs` (SVG 원본은 assets/sprites_src/)

| 폴더 | 내용 |
|---|---|
| characters | 주인공: idle, walk_a/b, swing(사슬 휘두름), cast(천도), hit |
| enemies | 혼 4종 서 있음 + 갓 죽은·해 넘긴·오래된 혼 무릎 꿇음(덩어리는 무릎 없음) |
| boss | 나루 영감 idle / attack(삿대 휩쓸기 예비동작) |
| tiles | 흙길·마당·풀·논두렁·돌길·징검다리 각 변형 a/b |
| props | 초가집·기와집·돌담·장독대·우물·서낭나무·돌무더기·장승·상여·평상·지게·솟대 |
| hud | 게이지 틀/채움, 처결 타이머 링, 천도·파혼 버튼, 넋·기억·엽전·업 아이콘, 시야 축소 비네트, 기억색 테두리, 밤 시간 바, 패널 |

이 그림은 **임시**다. 최종 에셋은 Higgsfield(MCP 연결 후) 단계에서 같은 파일 이름·피벗으로 교체한다.
