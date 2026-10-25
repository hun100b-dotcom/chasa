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

[3차: 구역 개성·랜드마크 14종] props/prop_{ruined_shrine,tomb_old,mangjang,soulfire_lantern,plague_rope,quarantine_hut,herb_pot,foul_pool,sick_mats,plague_banner,big_rock,old_tree,small_shrine,pass_cairn}.glb (60~526삼각형; 불빛 Light_: ruined_shrine 보라, soulfire_lantern 푸른 혼불, herb_pot 연두, small_shrine 등불). 생성: tools/art3d/zone_props.py. 배치: 폐당집 터 위 숲 걷어 내고 무너진 당집+무덤 20+만장 4+혼불 석등 길, 검은여울 의원 집 둘레 약탕·병자·격리 움막, 길목 금줄 3, 독기 웅덩이 9, 역병 깃발 9, 병자 거적 5, 길 따라 72m마다 랜드마크 19곳(field_5x5.json landmarks).
[소품 높이 기준] 땅 타일 두께 0.3. props[].z는 칸 아랫면 기준, props[].gz=z+0.3이 땅 윗면(소품을 놓는 높이). 최상위 tile_thickness_m·z_note 참고. instances.json은 [x,y,rot,z,gz].

[역병 분위기 2차] props/prop_{mist_bank,mist_pillar,sick_lantern}.glb (252·180·70삼각형). mist_bank=낮게 깔린 회청록 독안개 덩이(폭 7m·높이 0.9m, 약한 자체발광), mist_pillar=솟는 독기 기둥(3m, Light_mist_pillar 연한 청록), sick_lantern=병든 초록 등롱(2.2m, Light_sick_lantern 탁한 연두 #8FE0A8·세기 1.0·범위 9m·깜빡임). 배치: 검은여울 다리목·의원 둘레·강 양쪽 둑에 안개 덩이 45개, 웅덩이·약탕 곁 기둥 6개, 길·다리목에 초록 등불 14개(layouts 불빛 목록 35→66개). 안개 색 값은 layouts/field_5x5_zones.json 각 구역의 "fog"(color·density·start_m·end_m): 검은여울 #46564F(짙게 14~90m), 폐당집 #3A3357, 기본 #33405F. 유니티는 RenderSettings.fog를 구역에 따라 바꾸면 된다(투명 재질을 안 쓰는 대신 안개 덩이를 소품으로 깔았다). LOD도 74모델로 갱신.
[1막 마을 사람 17명] npcs/npc_{N101,N102,N103,N104a,N104b,N104c,N105,N106,N107,N108,N109,N110a,N110b,N201,N202,N203,N204a,N204b,N205,N206,N207}.glb (21개, 삼각형 420~830, 파일 110~155KB) + npcs/_npc_manifest.json(키·소품·동작 목록). 서사 npc_act1.json에 외형 칸이 없어 역할 설명으로 정함: 한복 몸통 틀(남 바지저고리/여 치마저고리/도포·두루마기/노인 굽은 등/아이는 같은 틀을 0.6~0.75배)에 색·머리·모자·소품만 바꿨다. 뼈대는 주인공과 같은 16개 이름(팔만 내려온 자세), 동작 4개(60fps): Idle 96f·Walk 36f·Talk 120f·Work 36f(event hit=8f, 망치질). 치마·도포는 걸음 폭 0.55배. 규약: 원점=발바닥, 정면 -Y(블렌더)=+Z(glTF), 캐릭터 왼쪽=+X. N-201 득보는 N-110a와 같은 사람이라 같은 모양(N201 파일은 N110a 복사본 취급 가능). N-101 당할미는 모델로만 존재(대사 없음). 키: 몸 1.2~1.9m, 소품 포함 최대 2.14m(곱단네 물동이·사령 전립 깃). 새 사람은 tools/art3d/npcs.py 맨 아래 SPECS에 한 줄 추가.

[컷신 소품 20종: B-02 월화·B-03 서 의원] props/prop_{gut_floor,gut_slots,gut_cup,gut_cup_flipped,gutsang,bangul,salpuchae_broken,obang_scraps,eave_lamp,post_lamp,yakjang,tanggeon,brush_dry,gamcho_pile,potion_bottle,yakbongji,seal_red,seal_empty,ledger_open,number_grid}.glb (48~1976삼각형, tools/art3d/cutscene_props.py, 보고서 props/_report_cutscene.json). 서사 cutscenes_b02/b03.json의 장면 지문에서 뽑았다. 여러 조각이 따로 움직이는 것은 GLB 안 노드 이름으로 나눔:
 - gut_floor: 지름 12.4m 굿판, 노드 Floor / Pedestal_01~12 / Cup_01~12(열두째 Cup_12만 엎어짐. 첫째=북쪽 12시, 시계 방향, 반지름 5m). gut_slots: '붉게 열리는 바닥' 원판 Slot_01~12(반지름 4.1m, 평소 숨기고 칸별로 켠다). 열두째 잔을 세우는 컷은 코드가 Cup_12를 gut_cup 위치로 바꿔 세우거나 gut_cup_flipped↔gut_cup을 교체.
 - yakjang(등짐 약장 0.62×0.34×0.86m): Body / Drawer_BL(맨 아랫단 왼쪽=캐릭터 기준 +X 서랍, 앞 -Y로 0.12m 밀려 나옴) / Drawer_BL_glow(약점 표시 발광판). 붉은 어깨끈 포함.
 - eave_lamp(폐당집 처마 등)·post_lamp(주막 기둥 등): Lamp_frame + Lamp_glow(켜짐 발광 — 코드가 재질을 바꿔 끄고 켬) + Light_ 빈 오브젝트 1개. 켜질 때 광원과 발광을 같이 켠다.
 - number_grid: 5×5 칸 1.9m, 전체 9.56m. Lines(흐린 선) + Cell_r_c(r=0 남쪽~4 북쪽, c=0 서쪽~4 동쪽) 25개, 칸은 붉은 발광판이라 코드가 평소 숨기고 하나씩 깜빡임.
 - obang_scraps: Scrap_01~12, 오방+붉은 천 조각(코드가 개별로 띄움). seal_red/seal_empty: 0.9m 정사각 붉은 인과 빈 인 자리(XY 면에 눕혀 만듦 — 머리 위에 세우려면 X축 90°). ledger_open: 펼친 명부. bangul(칠성방울 8개, 원점=손잡이 아래)·salpuchae_broken(살 9개 중 둘 빠지고 하나 꺾임)·gutsang(굿상, Light_gutsang)·gut_cup(+엎어진 것)·tanggeon·brush_dry·gamcho_pile·potion_bottle·yakbongji.
 색: 붉은 인·붉은 칸은 포도주색 #A33A3A(주황은 파혼 전용이라 안 씀), 켜진 등은 노랑 #FFD27A(주황 아님).
[마을 사람 자리 38곳] layouts/npc_places_act1.json: 서사 npc_act1.json places 38곳을 필드 절대 좌표(x=동,y=북 m)로 확정. 각 자리마다 x·y·face_deg(0=동,90=북)·가까운 소품·옮긴 이유. 구역 닻: 서낭당 고개(188,36), 마을=우물(200.2,54.5), 보릿들 둑(290,116), 물막이 골 나루(404,296), 폐당집(580,535), 장터(36,388)·동헌 터(36,330)·역병막(34,469)(2막 구역은 건물 없이 서쪽 둑에 터만 잡음). 새 모델이 필요한 곳: 정자·대장간·주막·장터 약방/좌판·동헌 터·옥·객사.

[보스 본체 B-02 월화·B-03 서 의원: 모델+동작] boss/boss_b02_wolhwa.glb(약 1250삼각형, 뼈 9) / boss/boss_b03_seo.glb(약 780삼각형, 뼈 11) + boss/_b02_b03_anim_manifest.json(동작별 프레임 수·event). tools/art3d/boss_b02_b03.py. 6원형 뼈 규칙(Root·Hips·Chest·Head·UpperArm.L/R·Prop)에 Hand.L/R을 더했고 서 의원만 Case(약장)·Drawer(서랍)를 더했다. 재질 조각별로 메시가 나뉘어(split_prims) 있고 스킨 1개.
 월화(2.04m): 오방 쾌자, 왼손 방울(칠성방울), 오른손 살 부러진 부채, 허공에 도는 요령 고리(Prop, 굿판 둥지 고리는 Root). 동작 10개: Idle(96f 반복)·Intro(216f: 등 돌린 채 서 있다 방울 36f, 고개 132f)·Open(잔이 열린다 예비 60f, hit 66f)·Whip(붉은 천 휘감기 예비 42f, hit 46f)·Phase2(거꾸로 굿, 반 바퀴씩 회전 120f)·Kneel(90f, bell_drop 8f)+KneelHold(120f 반복)·Tendo(390f: 일어서 90f→잔 세움 150f→내밂 210f→부채 눕힘 300f→흩어짐 390f)·Pahon(150f, blast 6f)·Hurt(20f).
 서 의원(2.0m): 기운 탕건, 등짐 약장(Case, 서랍면이 뒤 +Y), 맨 아랫단 왼쪽 서랍 Drawer(청록 약점판 dGlow가 같은 뼈에 붙은 발광 재질 — 코드가 켜고 끈다), 몸 앞 장부(Prop, 작게 줄여 몸이 보이게). 동작 11개: Idle·Intro(기침 42f, 서랍 밀림 42f·들어감 66f)·Call(번호 부르기 예비 48f, hit 52f)·Stamp(붉은 도장 찍기 예비 42f, hit 46f)·Phase2(명단 줄이기, 장부 넘김 18f)·Cough(약점 노출 180f: 반 바퀴 돌아 등의 약장을 보이고 서랍이 열림 30f~165f)·Kneel(90f, case_down 30f)+KneelHold·Tendo(390f: 서랍 열림 90f·붓 140f·닫음 170f·탕건 300f·돌아봄 330f·흩어짐 390f)·Pahon(150f, burst 6f 서랍이 튀어나옴)·Hurt.
 보스 기술 이름과 클립: 잔이 열린다=Open, 붉은 천 휘감기=Whip, 번호 낙인=Call, 붉은 도장 찍기=Stamp. 눈으로 본 접촉판 점검만 했고 유니티 재생은 미확인. 이전 6원형 파일(뼈 7, 동작 없음)은 이 두 보스에 한해 대체됐다.
[첫 세션 이름혼 6명 자리] layouts/npc_places_act1.json 의 named_souls_first_session: S-001 박돌쇠(215.6,62.2 대장간 문 앞)·S-002 윤 소사(190.4,60.8)·S-003 연이(202.0,56.6)·S-006 장 둑지기(302.0,112.6)·S-010 곽 뱃꾼(381.5,293.5)·S-011 방물장수 막례(397.8,304.0). 각 face_deg·나이대·메모 포함.
[마을 건물 7곳: 정자·대장간·주막·장터 약방·동헌 터·옥·객사] 한옥 조각 키트(tools/art3d/kit_buildings.py)로 지어 확정 좌표에 넣었다. 새 레시피 3종 jeongja(사방이 트인 정자)·daejanggan(앞이 트인 대장간)·donghun_burnt(불탄 동헌 뼈대) + 기존 choga8·giwa8. 좌표(x=동,y=북, rot 0=정면 남쪽, +90=동쪽, -90=서쪽): 정자 (192,43.6,0)=서낭당 고개 서낭나무 곁 / 대장간 (224,62,-90)=마을 동쪽, 문 앞이 박돌쇠 자리 / 주막(계곡) (419.8,330,0)=물막이 골 개울 동쪽 둑(처음 (414,328)은 개울 위라 옮김) / 장터 약방 (25,391,90)+주막 (47,391,-90)=장터 좌우 / 동헌 터 (36,330,0) 불탄 뼈대 / 객사 (25.5,326,90) / 옥 = 담 prop_prison_wall (36,345)+문 prop_prison_gate (36,339.5)로 둘러싼 원. 장터 약방 곁에 약초 말림대 br_herb_rack·약방 간판 br_med_sign·항아리 br_jars. 주변 숲은 치우고(field_layout.py SITE_CLEAR), 장터·동헌 터로 가는 서쪽 둑길을 EXTRA_ROADS로 추가했다.
[마을 소품 13종] props/prop_{anvil,trough,tool_rack,forge,pyeongsang,post_lamp,jangdok,market_stall,candy_stand,burnt_desk,burnt_cabinet,ash_heap,charred_pillar,prison_wall,prison_gate}.glb 중 town_props.py가 만든 것(보고서 props/_report_town.json, 미리보기 previews/town_props.png). 불빛 Light_: forge 주황 #FF9A4A(대장간 화덕, 세기 1.4·범위 10m), prison_gate 따뜻한 등 #FFC878, burnt_cabinet 약한 흰빛. 배치 목록은 field_layout.py SITE_PROPS(모루·구유·연장걸이·평상 5·장독·좌판 3·엿판·수레·재 더미 3·그을린 기둥 6 등). 밤 장면 확인용 previews/scene_{market,donghun,smithy,jeongja,jumak}_final.jpg.
 주의: 화덕 불빛은 처마에 가려 위에서 보면 약하다 — 유니티에서 Light_forge 세기를 올려도 된다. 시장 길 끝에 오래전부터 있던 어두운 팔각 땅(road_end 칸)이 남아 있다. 유니티 재생은 아직 눈으로만(렌더) 확인. layouts·LOD(102모델)·instances(props 6295)·lights는 다시 뽑았다.
[땅 전면 교체(오너 지시 "타일 변경 시급: 요소만 때려박지 말고 실제처럼, 맞는 타일 다 깔기")] 8m 타일 조각 깔기를 버리고 '이어진 지형 + 월드 좌표로 구운 땅 그림'으로 바꿨다. 생성: tools/art3d/terrain_ground.py(인자 없으면 25청크 전부, 약 5분). 색·높이 값은 맨 위 상수·팔레트 C에 모음.
  ① terrain/chunk_{0..4}_{0..4}.glb — 청크 128m, 원점=청크 남서 모서리(x=동,y=북,z=위; GLB는 +Y 위). 2m 격자 메시(삼각형 8192) + 알베도·노멀 JPEG(8픽셀/m, 가장자리 6픽셀 여유) + 개울 물면(알파). br_* 칸(검은여울 강 조각)은 구멍으로 두고 그 칸엔 br_ 조각이 따로 놓인다.
  ② terrain/terrain_height_2m.png(16비트, 321×321, 2m 간격, 행 0=남쪽, 높이(m)=값/65535×8−1) + _terrain_manifest.json — 소품 높이용 표. tools/art3d/terrain_apply.py가 소품 6262개의 gz를 이 표로 다시 계산해 field_5x5.json에 넣는다(field_5x5.json "ground" 키 참고). 순서: field_layout.py → terrain_apply.py → field_export.py → field_lights.py.
  ③ 땅 종류: 흙길(바퀴 자국 두 줄·가운데 풀 줄·길섶 짙은 풀 번짐·자갈), 건물 둘레 다짐 마당(불규칙 가장자리), 풀(색 얼룩·마른 풀·클로버·들꽃 점), 보리밭(이랑 7줄/칸 + 둑 논두렁 + 밭 가장자리 풀), 개울(자갈 바닥·젖은 흙·자갈 둑), 숲 바닥(솔잎·낙엽·이끼, 나무 밀도에서 계산), 마른 나무 밑 재, 바위 부스러기, 무덤 둘레 맨흙, 비탈 맨흙·절벽돌, 구역 색조(검은여울 병든 회녹·폐당집 마른 자주). 높낮이: 평지에 ±0.17m 완만한 굴곡(건물·마을·길 둘레는 평탄, 개울·강 둘레 억제).
  ④ 한계: 메시는 2m 격자라 이랑·바퀴 자국은 그림(+노멀)로만 있다. 텍셀 밀도 8픽셀/m는 50° 가까이 보기엔 낮으니 유니티에서 디테일 텍스처를 곱하면 좋다.
  ⑤ 유니티 지형 자료(코드팀 docs/TERRAIN-FORMAT.md 형식): terrain/terrain.json·heightmap.png(641², 1m, R·G 16비트, 높이 −1~8m)·splat_a.png(R흙·G풀·B자갈·A논, 640²)·splat_b.png(R낙엽)·layer_{dirt,grass,gravel,paddy,leaf}.png(이음매 없는 512², 6m). 같은 규칙(terrain_ground.chunk_maps masks=True)에서 뽑는다: tools/art3d/terrain_unity.py. 행 0=y 0(남쪽). 강 조각 칸 안쪽은 −0.1m로 낮춤. 청크 GLB와 이 자료는 같은 땅이라 둘 중 하나만 써도 된다.
  ⑥ field_scene.py(밤 장면 조립)는 청크 GLB를 깔고 br_ 조각만 옛 모델로 놓는다. 옛 타일 목록은 field_5x5.json tiles에 호환용으로 남아 있다.
[모델 2차 다듬기(오너 지시 "퀄리티 업"; 직접 평가 3/10)] tools/art3d/look_v2.py. 주인공(선반 깎은 도포 주름·앞 트임·안감·소매 단·갓끈과 구슬·허리띠·천도빛 구슬), 혼 4종(갓 죽은=반투명 눈물 모양 껍질+속 불꽃, 해 넘긴=소매 늘어진 도포 혼불, 오래된=뿔·금·불씨 눈, 뭉친=구름 속 얼굴), 마을 사람 21명 얼굴(눈 흰자·눈동자·눈썹·코·입·귀·볼·주름), 무기 5종 전부. 뼈 이름·동작은 그대로. 반투명 재질은 mat_alpha(glTF alphaMode BLEND). 전후 사진 previews/q_{before,after}_{hero,souls,souls_night,faces,weapons}.png. 옛 모양은 characters.hero_v1·souls_v1, weapons.*_v1에 보존.
  무기(원점=쥐는 곳, 긴 방향 +Z): 철삭(가죽 감은 손잡이·놋 마개·붉은 술·맞물린 사슬 고리·천도빛 띠 철추 1098삼각형 1.53m) / 육모방망이(여섯 모 깎은 몸·쇠테 셋+못·한지 감은 손잡이·금패 낙인·붉은 손목끈 756삼각형 1.21m) / 요령방울(종 모양 놋 방울 셋·휘어 내린 가지·연꽃 봉오리 꼭대기 천도빛 구슬·한지 술 1154삼각형 0.84m) / 삼지창(매듭 감은 자루·놋 장식 목·잎 모양 가운데 날+천도빛 홈·미늘 달린 바깥 두 갈래·붉은 술과 부적 744삼각형 2.44m) / 명부 붓(마디 진 붓대·놋 물림쇠·갈라진 먹 붓털+붉은 끝·천도빛 구슬 매듭·두루마리 쪽지+도장 572삼각형 1.56m). 소켓·방향 규약은 그대로(weapons/_weapons_manifest.json).
[땅 한계 해결: 디테일·개울물·낮 장면] ①디테일: terrain/detail_{grass,dirt,gravel,paddy,leaf}.png(색)·detail_*_n.png(노멀, OpenGL), 512², 1.5m 반복·이음매 없음(약 340픽셀/m). 층 색에 곱하거나 가까울 때(~25m) 섞는다. 생성 tools/art3d/terrain_detail.py(detail_tiles) → terrain_unity.py가 저장. ②개울물: terrain/water_albedo.png(RGBA, 알파=투명도)·water_normal.png, 256², 4m 반복. 흐름=남북(terrain.json water.flow_dir_xy [0,-1], 0.7m/s). 청크 GLB의 물면에도 같은 그림이 내장(알파 블렌드, 거칠기 0.06). 물가 거품은 땅 알베도에 구웠고 splat_b.png G채널(거품)·B채널(젖은 땅)로도 줌. ③낮 장면: FS_DAY=1 python3 field_scene.py <컷...> → scene_<컷>_day.png, scene_post.py <컷>_day → previews/scene_*_day_final.jpg(마을·보릿들·방앗간·개울·폐당집·역병·한가운데 마을·다리 8컷). 개울 가까이 컷 scene_stream_*.
[큰 강 물 + 하늘·날씨 재료] ①blackrapids/br_{rapids,deep,shore}.glb: 단색 물 상자 → 바닥(자갈 흙 상자 0.12m)+흐르는 물면 판(z0.18, 알파 블렌드, 개울과 같은 물 그림). 큰 강은 terrain/water_albedo_deep.png(더 어둡고 덜 비침), 노멀 water_normal.png. 줄무늬는 타일의 서→동(+X)으로 눕고 타일 rot를 따라 돈다. 흰 거품 줄·바위는 그대로. lib3d.mat_water/water_plane, join()이 UV를 보존하도록 고침. ②하늘·날씨: assets3d/sky/ — sky_clock.json(하루 40분=게임 24시 키프레임: 하늘 꼭대기·중간·지평선색, 빛 색·세기, 그늘색, 안개색·짙기, 별·달 보임 + 날씨 5종 프리셋 clear/cloudy/rain/fog/plague_mist + 달 주기·구름 바람), sky_gradient_{clear,overcast,fog}.png(480×128, 가로=하루 3분/픽셀), cloud_{cumulus,cirrus,storm}.png(1024² RGBA 반복)+cloud_shadow.png(512² 흑백 반복), moon_{crescent,first_quarter,full,last_quarter}.png+moon_halo.png(256²), sun_disc.png, stars.png(1024² 반복)+stars_twinkle.png, rain_streaks_{far,near}.png(512² 반복)+rain_splash_sheet.png(8프레임×96px), fog_noise.png(512² 반복)+mist_puffs.png(4종). 생성 tools/art3d/sky_weather.py, 미리보기 tools/art3d/sky_sheet.py → previews/sky_sheet_{a,b}.jpg. 50° 시점은 지평선이 안 보이므로 하늘은 빛·안개·구름 그림자·화면 가장자리·밤 달별 연출에 쓰인다.

== 무기별 동작 (hero_weapon_anim.py → hero_chasa.glb) ==
hero_chasa.glb 동작 34개(60fps). 기존 9개(Idle·Walk·Attack/2/3=철삭·Dodge·Hit·Cast·Pahon)는 그대로, 새로 25개:
  <무기>_Attack1/2/3 (Mace·Bell·Trident·Brush), <무기>_Draw (Chain 포함 5개, 30f=0.5초), <무기>_Tendo (60f), <무기>_Pahon (25f)
  철삭 3타·천도·파혼은 기존 Attack/Attack2/Attack3/Cast/Pahon.
시간은 WeaponTable.cs의 windup/swing/recover(초)를 60fps로 바꿔 맞춤. 이벤트(프레임)는 _hero_anim_manifest.json의 각 clip.events:
  공격 hit(또는 3타 hit_start/hit_end·impact), windup_end, swing_end / Draw swap_hide 9·swap_show 13 / Tendo hold_start 14·hold_end 46·finish_start 46·finish_peak 52 / Pahon hit 8·recover_dodge_from 10.
소켓(중요): 무기마다 손에 쥐는 각도가 다르다. 무기 모델을 Hand.R 뼈에 붙일 때 X축 회전 socket_rotate_deg_x = Chain 90 · Mace 40 · Bell 20 · Trident 30 · Brush 55 (매니페스트 clip.socket_rotate_deg_x에도 있음). 철삭 외 무기를 90°로 붙이면 동작이 어긋난다.
확인 그림: assets3d/previews/anim_hero_<클립>.png, 요약 anim_hero_weapons_overview.jpg

== 보스 싸움터 3곳 (tools/art3d/boss_arenas.py → layouts/boss_arenas.json) ==
나루 영감 B01 (404,288 물 위) · 월화 B02 (580,521 폐당집 굿판) · 서 의원 B03 (46,453 역병막 마당). 좌표는 코드팀 Boss.cs, 시간·모양은 balance.json·기획 부록 E.
  바닥 무늬(정사각 RGBA, 위=북·오른쪽=동·한가운데=보스 자리): assets3d/boss/arena_b01_floor.png(44m, 물 위 반경 18m 바깥 경계 + 반경 11m '큰물' 경계) / arena_b02_floor.png(24m, 굿판 반경 9.6m·잔 열두 자리 r=7m 한자 번호·오방색 띠·열두째는 청록 테두리) / arena_b03_floor.png(14m, 5×5 번호 칸 2m 한자 一~二十五).
    땅 위 quad로 깔고 0.04m 띄운다. 칸 번호는 코드 CellPos(i=동 +, j=북 +)·CupPos(30i°, 반경 7m)와 같은 규칙이라 코드 판정 칸과 그림이 어긋나지 않는다.
  예고 장판 그림 6장(흰색+알파, 코드가 색을 입힘): assets3d/boss/tele_circle·tele_sector120·tele_sector30·tele_line·tele_cell·tele_band.png. 가장자리 선명(1.0)·안쪽 옅음(0.3).
  소품 새 16종: prop_mooring_post·flood_marker·broken_pole(나루), prop_arena_cup·arena_cup_down·arena_gutsang·obangki_{blue,red,yellow,white,black}·brazier(굿판), prop_medicine_chest_big·name_board_row·corner_stone·brand_rack(역병막). 불빛은 Light_ 빈 오브젝트.
  배치표 layouts/boss_arenas.json: 싸움터별 중심·땅 높이·바닥 무늬 규격·소품 위치·조명·예고 장판 규격(패턴별 그림·크기·예고 시간).
  싸움터 둘레는 field_layout.py의 ARENA_CLEAR로 나무·바위를 비웠다(필드 JSON 재생성, 33개 제거).
  확인 그림: previews/scene_arena{1,2,3}_final.jpg(밤), scene_arena{1,2,3}t_final.jpg(패턴 예고 켠 장면).

== 큰 강 높이맵 이어 파기 (terrain_unity.py river) ==
원인: 옛 높이맵은 br_* 칸(8m)마다 '안쪽'만 −0.1로 낮추고 칸 둘레 2m는 그대로 둬서, 강이 칸마다 둑이 남은 3×46개 웅덩이 격자가 됐다(전/후 그림: previews/river_beforeafter.jpg).
고침: 칸과 무관한 연속 물길로 판다(river_field). 단면 = 한가운데 −0.30 → 물가로 얕아져 −0.10 → 물가선(물면 0.18보다 살짝 아래) → 둑 0.30. 물가선은 길이 방향 ±0.5m 구불거리고 남쪽 끝(y=272)은 둥글게 닫힘, 북쪽은 지도 끝까지.
  heightmap.png·splat_a/b.png(강바닥·둑=자갈, 물가선=거품·젖은 땅)·terrain.json(river 항목: 축·물 범위·바닥 깊이)을 새로 냈고, 연속 물판 terrain/river_water.glb(x 76~92, y 272~640, z 0.18, 4m 반복 uv)를 추가했다.
  br_* 조각 모델은 물판·바닥 상자가 칸마다 나뉘어 있어 격자처럼 보이니, 지형 + river_water.glb만 쓰길 권장(돌다리·나루터 같은 구조물은 그대로).

== 첫인상: 로고·타이틀·로딩·아이콘 (tools/art3d/title_assets.py → assets3d/title/) ==
  logo_chasa.png(밤 화면용 한지색+그림자, 투명 배경) · logo_chasa_ink.png(밝은 바탕용 먹색) · seal_chasa.png(붉은 인 '差使') — 나눔 붓글씨(OFL)로 쓴 '차사'에 마른 붓 질감을 입히고 직접 그린 도장을 얹었다. 상표성 문구·기존 작품 자원 없음.
  favicon.svg / favicon.ico(16·32·48·64·256) / favicon_{16,32,48,64,192,512}.png / apple-touch-icon.png(180) — 붉은 도장 위 '差' 한 글자.
  title_screen.png(1920×1080, 로고 합성) · title_bg.png(로고 없음 → 코드가 로고·버튼을 올릴 때) — 밤 서낭당 앞에 선 차사(3D 렌더, field_scene.py의 title 샷).
  loading_1_solgogae.jpg · loading_2_mulmagi.jpg · loading_3_pyedang.jpg(1920×1080) — 구역별 밤 장면, 아래쪽 25%는 막대 자리라 어둡게. loading_bar_frame.png(1024×64) / loading_bar_fill.png(1024×40, 붉은 붓줄)은 왼쪽부터 잘라 보여 주면 막대가 된다.
  title_manifest.json: 로고·막대 권장 위치.
