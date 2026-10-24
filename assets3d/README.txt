차사 로우폴리 3D (직접 만든 소품, Blender 스크립트로 생성)
- 소품 10종: props/prop_*.glb  (초가·기와집·돌담·장독대·솟대·금줄·서낭당·상여·우물·장승)
- 주인공: characters/hero_chasa.glb (컨셉 B, 뼈대 16개, 삼각형 약 600). 화면에는 '동이' 이름 노출 금지.
- 혼 4종: souls/soul_{fresh,day,old,lump}.glb (하늘빛/노랑/녹슨 적갈색/보라)
- 솔고개 마을 배치표: layouts/solgogae_village.json, 미리보기 previews/
규약: GLB, 1유닛=1m, 원점=바닥 한가운데, 정면 +Z, 위 +Y, 재질=베이스컬러만(텍스처 없음, 혼은 빛나는 색 포함).
다시 만들기: pip install bpy==5.1.0 → cd tools/art3d && python3 props.py && python3 characters.py && python3 solgogae.py
라이선스: 전부 직접 제작(저작권 문제 없음). 외부 에셋 없음.

[추가 2026-10-24]
- hanok/ : 한옥 조각 25종(4m 한 칸 규격), _kit_manifest.json(쌓는 높이: 기단 0, 벽 0.5, 지붕 2.9). 조립 시험 previews/hanok_kit_assembled_50deg.png
- terrain/ : 지형 타일 18종(한 칸 8m, 128m 땅 칸에 16×16), _tiles_manifest.json. 시험판 previews/terrain_tiles_demo_50deg.png
- boss/ : 나루 영감(boss_naru.glb, boss_naru_attack.glb 예비동작), 뼈대 8개
- 주인공은 더 날씬하게, 흑립은 작게 고침(삼각형 616, 키 흑립 포함 1.94m)
다시 만들기: tools/art3d 에서 hanok_kit.py, terrain_tiles.py, boss_naru.py

[자연물·밤 소품] nature/ 17종(소나무3·느티나무2·대나무2·갈대2·억새2·덤불3·마른나무3), night/ 5종(석등·등롱 받침·등롱 기둥·횃대·혼불 받침).
- night/*.glb 안의 Light_* 빈 오브젝트 = 불빛 위치. extras: light_type, color, intensity, range_m, flicker(1=깜빡임).
- 나무 뿌리·쓰러진 나무는 최대 7cm 땅속으로 박힘(의도: 땅에 자연스럽게 묻힘).

[보스 6원형] boss/boss_b02_wolhwa·b03_seo·b05_daedol·b09_mangbu·b04_heugwol·b14_lump.glb (+ 1호 boss_naru).
- 뼈대 7개 공통: Root/Hips/Chest/Head/UpperArm.L/UpperArm.R/Prop(깃발·장부·사슬 고리 등 무기/상징물). 키 1.94~2.8m(깃발 포함 대돌 3.4m).
- ⑥ 흑월은 영웅과 같은 실루엣(검은 도포·붉은 사슬). 재질 이름만 바꿔 다른 차사형 보스로 재활용 가능.

[혼 지역 변형 12종] souls/soul_{fresh,day,old,lump}_{yeoksa,bungjae,soegol}.glb — 검은여울 역병(푸른 멍울)·붉은재 번호 병사(전립+번호표)·쇳골 광부(등불 모자+곡괭이).
기본 4종과 같은 실루엣·같은 크기, 색과 부착물만 다름. 최대 432삼각형. 생성: tools/art3d/soul_variants.py
