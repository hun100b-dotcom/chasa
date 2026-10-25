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

[마을 v2·필드 배치표]
- layouts/solgogae_village.json: 집 7채를 한옥 조각 키트로 재조립(buildings[].pieces = 세계 좌표 조각 144개). 나머지 소품은 props[].
- layouts/field_5x5.json: 5×5칸(640m) 땅 배치표. tiles(80×80 중 풀밭 아닌 칸)·props(자연물 523)·markers(서낭당·굴·물막이·폐당집·보스·넋길)·zones. 마을 배치표는 필드 (196,60)에 놓는다.
  동선: 마을 → 동쪽 보릿들(밭 칸) → 북쪽 물막이 골(개울 + 양쪽 벼랑 +2m) → 동북 폐당집 터(+2m 고지, 남쪽 비탈 한 칸이 입구).
  비탈 모서리 rot는 추정값(QA에서 어긋나면 ±90 보정). 굴 입구는 서쪽 벼랑 비탈 한 칸이 길로 바뀐 자리.
- 생성: tools/art3d/kit_buildings.py(집 설명서) → solgogae.py(마을) / field_layout.py(필드, 파이썬만으로 실행)

[애니메이션 v1 — 60fps, 뼈대(스킨)+동작을 GLB에 함께 담음]
정정: 이전 hero_chasa.glb·boss_naru.glb는 내보낼 때 뼈대가 빠져 정지 모델이었다(아마추어를 선택하지 않은 탓). 지금은 tools/art3d/anim.py의 export_rig()가 아마추어와 메시를 함께 내보내고 verify()가 파일을 다시 열어 스킨·관절·동작 수를 센다.
- characters/hero_chasa.glb: 관절 16, 동작 9 = Idle(96f 반복) Walk(36f 반복) Attack(1타 22f, 명중 f10=45%) Attack2(22f) Attack3(회전 50f, 명중 f14~28) Dodge(19f, 무적 f2~15) Hit(18f) Cast(천도 60f, 버티기 f14~46) Pahon(25f, 터짐 f8). 상세 _hero_anim_manifest.json
- souls/soul_*.glb 16종: 관절 2(Root, Body), 동작 4 = Float(90f 반복) Windup(33f=0.55초, 번쩍 f21) Attack(18f, 명중 f5) Kneel(36f, 끝 자세 유지)
- boss/boss_naru.glb: 관절 8, 동작 3 = Idle(96f 반복) Windup(66f) Swing(42f, 명중 f8)
회전·이동은 제자리(루트 모션 없음). 이동거리(피하기 3.2m 등)는 코드가 맡는다. 철삭 사슬은 영웅 오른손의 감긴 사슬 모델만 있고 늘어나는 사슬은 코드 이펙트.

[무기 5종] weapons/weapon_{chain,bangmang,yoryeong,samjichang,myeongbu}.glb (110~436삼각형). 원점=쥐는 곳, 긴 방향=glTF +Y. 소켓은 weapons/_weapons_manifest.json(Hand.R 머리 위치에 원점, X축 +90°로 눕혀 앞을 향하게). 생성: tools/art3d/weapons.py

[처결 이펙트 메시 9종] fx/fx_{tendo_pillar,tendo_ring,pahon_shards_a/b/c,stain_decal,wait_ring_fresh/day/old}.glb (22~272삼각형, 발광 재질만, 투명·애니메이션은 코드). 생성: tools/art3d/fx.py

[2막 검은여울 키트 11종] blackrapids/br_{rapids,deep,shore,stone_bridge,ferry_dock,willow_a,willow_b,reed_field,herb_rack,med_sign,jars}.glb (48~412삼각형). 타일 8×8m, 물 윗면 z0.18/풀 윗면 z0.3. 나루터에 Light_ferry_dock. 의원 집=한옥 키트 'uiwon'(=기와집 8×4m)+약초 건조대·깃대·항아리. 생성: tools/art3d/blackrapids.py

[필드 5×5 v2: 검은여울 이어 붙임] layouts/field_5x5.json에 추가: 서쪽 칸(x 72~96m)에 남북 강(br_shore/br_rapids/br_deep, 물 폭 16m, y 272~640m), 돌다리 2토막(필드 (80,452),(88,452)), 나루터(92.4,548), 의원 집(52,468, buildings 조각 목록), 버드나무·갈대밭, 마을 길에서 갈라진 '검은여울 가는 길'. tiles의 'br_*'는 assets3d/blackrapids/, structures[]는 모델 직접 배치, props의 'br_*'도 blackrapids. file_dirs 참고.

[주인공 사슬 주먹 분리] characters/hero_chasa.glb(몸통만, 사슬 없음, 스킨 1·뼈 16·동작 9) + characters/hero_chain_wrap.glb(사슬 감긴 주먹 7.5KB, 코일 6+고리 4). 붙이는 법: hero_chain_wrap을 Hand.R 뼈의 자식으로 위치(0,0,0). 무기 장착 중이면 weapon_chain.glb로 대체 가능. 생성: tools/art3d/characters.py(chain_wrap), hero_anim.py

[밤 장면 렌더] previews/scene_*.png — tools/art3d/field_scene.py가 field_5x5.json+마을 배치표를 실제 3D로 조립(달빛 해 1.3, 등롱 점광, 50° 직교 카메라). 고친 것: 바닥 상자와 타일 윗면이 같은 높이라 길 옆이 검게 깨짐 → 바닥 상자를 0.28로 낮춤. 월드 안개(볼륨)는 장면 전체를 검게 먹어 끄고 후처리 안개로 대체.

[필드 조립에서 찾아 고친 이음새 7건] ①바닥 상자와 타일 윗면이 같은 높이라 길 옆이 검게 깨짐(조립기 바닥을 맨 밑으로) ②풀 칸을 안 깔아 물(0.18)이 풀 바닥(0.3)에 묻힘(빈 칸에 풀 타일 깔기) ③보릿들이 논 타일 → terrain_tile_barley 신설(180삼각형) ④개울이 논 격자 → terrain_tile_stream 신설(서쪽 칸 rot 0, 동쪽 칸 rot 180) ⑤다리 앞 길 4m 끊김 → br_road_pad(12삼각형) 신설, 필드 (74,452)·(94,452) ⑥서낭당 4곳이 마커뿐 → prop_seonangdang+횃대 2개씩 structures에 추가 ⑦불빛 목록 없음 → layouts/field_5x5_lights.json(26개).
유니티 주의: 타일 사이 머리카락 틈이 보이면 풀 타일을 3% 크게(xy만) 깔고 높이를 3~6mm 낮춰 아래에 겹쳐 놓으면 사라진다(field_scene.py 참고). 같은 높이 면끼리 겹치면 깨진다.
[렌더 컷] previews/scene_{gate,village,barley,bridge,naru,tendo}_final.jpg(후처리: 위쪽 푸른 안개+비네팅, tools/art3d/scene_post.py). 갤러리 같은 링크 갱신.

[오래된 혼 색 변경 #A5472E → #665659] 채도를 낮춘 먼지색 자주갈색, 발광 0.5→0.2. 이유: 따뜻한 등불 아래서 붉은 주황으로 읽혀 파혼 주황(#E8683A)과 혼동. 혼 16종·처결 대기 고리(old)·보스 조각 재생성. 확인 렌더: previews/soul_old_check.png(주황 등불 아래 오래된·해 넘긴·갓 죽은 혼 + 파혼 주황 구슬 나란히).

[주인공 개선(코드팀 요청 3건)] ①공격 3타를 확연히 다르게: Attack=왼발 내딛고 몸통 크게 비틀어 횡베기, Attack2=오른발 내딛고 반대 방향, Attack3=두 팔 머리 위로 들었다 내려찍는 오버헤드(회전 제거). 명중 프레임 유지(Attack/Attack2 hit f10, Attack3 hit_start 14~28). ②붉은 띠를 굵게(높이 0.16) + 앞으로 폭0.16·길이0.7 끝 두 가닥 + 금 매듭. ③앞면 표식: 갓 앞 금 장식판+붉은 술, 가슴 금 매듭. 미리보기 previews/anim_hero_*.png 재생성.

[재질 조각 분리 자동화] 뼈대 있는 GLB(주인공·혼 16·나루 영감)는 내보낸 뒤 tools/glb_split_prims.py(코드팀 도구)를 자동 통과(tools/art3d/anim.py split_prims). 조각마다 메시가 따로라 유니티 glTFast가 읽는다. 보스 b02~b14 등 다른 뼈대 파일은 아직 미적용.

[코드팀 요청 3건 반영] ①숲·덤불·바위 보강: props 625→1205개(북서 숲 260·서쪽 숲 130·보릿들 둘레 130·마을~보릿들 길가 60 추가; 청크(1,1) 206·(1,2) 155·(0,1) 136개). ②나룻배 br_ferry_boat.glb(212삼각형, 길이 약 6.1m 남북, 이물=-Y, 장대·선미 등불 Light_ferry_boat, 바닥 z=0.1이라 z=0에 놓으면 물에 8cm 잠김). structures: 나루터 곁 (84.6,553), 보스 자리 곁 (410,303). 참고: 보스 boss_naru.glb 안에도 배가 따로 있다. 불빛 목록 28개. ③비탈 기준 방향을 terrain/_tiles_manifest.json의 orientation_notes에 명시(slope_straight는 북이 높음, corner_out은 북동 꼭짓점만 높음, corner_in은 남서 꼭짓점만 낮음; rot는 반시계).

[숲 군집 2차] props 1205→6208개. 6~12그루 한 덩어리(그루당 약 30㎡), 덩어리 사이 빈 풀밭. 빽빽한 곳: 물막이 골·폐당집 둘레(간격 15~16m), 보릿들 바깥 띠(18m). 빈 청크(1,3)=189·(1,4)=180·(2,4)=123·(3,4)=387로 채움. 부담되면 field_layout.py의 cluster_grid skip 값을 올리거나 step을 키워 성기게 다시 뽑는다. 보스 자리 빈 배는 보스 바로 옆 (410.5,288)로 옮김(마커 boss는 (404,288) 그대로).

[생활감 소품 15종 + 배치] props/prop_{haystack,fence,cart,firewood,scarecrow,wonduumak,signpost,grave,cairn,millstone,sacks,cow,stepstones,log_pile,campfire}.glb (74~324삼각형, 원점=바닥 한가운데, 정면 -Y). campfire에 Light_campfire. 생성: tools/art3d/life_props.py, 미리보기 previews/life_props_15.png. 배치(field_layout.py): 마을 집마다 뒷마당(장작·볏가리·자루·울타리·소), 광장 모닥불, 수레·맷돌·디딤돌, 보릿들 밭마다 허수아비·원두막·볏가리·소, 갈림길 이정표 6, 무덤 5무리(폐당집·보릿들 서쪽 언덕·검은여울), 서낭당 돌탑, 숲 통나무·야영 불, 나루터 모닥불. props 6433, 불빛 34개.

[2차: 촌락·방앗간·LOD·인스턴싱·구역표] ①보릿들 한가운데 마을(초가 4채+우물·장독·모닥불·소), 마을 서·동 변두리 초가 군(3채씩), 개울가 방앗간 prop_mill.glb(572삼각형, 물레방아 +X=개울 쪽, 좌표 (399.3,340)). 해당 자리의 숲·덤불은 치움. props 6441, structures 34. ②LOD: assets3d/lod/<이름>_lod1.glb(면 40%)·_lod2.glb(색 덩어리 12면 이하) 57모델 + _lod_manifest.json(거리 규칙: LOD0~40m, LOD1~90m, LOD2~160m, 160m 밖 숨김, 키 1.5m 이하 소품은 70m 밖 숨김). 생성: tools/art3d/lod.py. ③인스턴싱 목록: layouts/field_5x5_instances.json(모델별·청크 128m별 위치). ④구역표: layouts/field_5x5_zones.json(구역 분위기·밀도·적 테마 + enemy_camps 후보 20곳). 생성: tools/art3d/field_export.py.
