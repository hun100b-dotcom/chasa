차사 로우폴리 3D (직접 만든 소품, Blender 스크립트로 생성)
- 소품 10종: props/prop_*.glb  (초가·기와집·돌담·장독대·솟대·금줄·서낭당·상여·우물·장승)
- 주인공: characters/hero_chasa.glb (컨셉 B, 뼈대 16개, 삼각형 약 600). 화면에는 '동이' 이름 노출 금지.
- 혼 4종: souls/soul_{fresh,day,old,lump}.glb (하늘빛/노랑/녹슨 적갈색/보라)
- 솔고개 마을 배치표: layouts/solgogae_village.json, 미리보기 previews/
규약: GLB, 1유닛=1m, 원점=바닥 한가운데, 정면 +Z, 위 +Y, 재질=베이스컬러만(텍스처 없음, 혼은 빛나는 색 포함).
다시 만들기: pip install bpy==5.1.0 → cd tools/art3d && python3 props.py && python3 characters.py && python3 solgogae.py
라이선스: 전부 직접 제작(저작권 문제 없음). 외부 에셋 없음.
