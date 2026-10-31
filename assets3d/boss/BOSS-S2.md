# 시즌 2 보스 8종 모델 (코드팀 전달용)
생성: `python3 tools/art3d/boss_s2.py` · 미리보기 `assets3d/previews/bosses_s2_50deg.png` · 클립표 `assets3d/boss/_s2_anim_manifest.json`
틀은 2·3막 보스와 같다: 뼈 9개(Root/Hips/Chest/Head/UpperArm.L·R/Hand.L·R/Prop), 클립 10개(Idle·Windup 40f·Attack 24f 명중 f6·Hit1·Hit2·Stagger·Kneel·KneelHold·Tendo·Pahon), 원점=바닥 한가운데, 정면 -Y, 60fps.
| 파일 | 보스 | 키(m) | 삼각형 | 약점이 보이는 곳 |
|---|---|---|---|---|
| boss_b13_old_man.glb | B-13 줄의 맨 앞 노인 | 1.85 | 916 | 오른손 나루 말뚝 토막, 허리 엽전 꿰미, 뒤(Prop)로 이어진 줄 밧줄 |
| boss_b14_mass.glb | B-14 돌아선 혼들의 덩어리 | 3.2 | 1,596 | 등 돌린 얼굴 14, 맴도는 이름 쪽지 10(Prop) — 주우면 굳음 |
| boss_b15_clerk.glb | B-15 숫자를 처음 쓴 서리 | 2.0 | 752 | 오른손 붓, 왼손 도장(인주 붉은 면), 등 뒤 숫자 두루마리 5(Prop) |
| boss_b16_inkkeeper.glb | B-16 벼루지기 | 2.15 | 710 | 등의 작은 벼루와 먹 방울(Prop) = 기억 조각 자리, 손에 먹 막대 |
| boss_b17_gatekeeper.glb | B-17 아홉째 문지기 | 2.7 | 812 | 눈 감음(졸음), 허리 종, 육모방망이, 등 문짝 조각·열쇠 꾸러미(Prop) |
| boss_b18_sealthief.glb | B-18 인을 훔친 혼 | 1.9 | 626 | 이마의 붉은 인 자국(발광, **이마 3초 약점**), 얼굴 없는 흰 가면, 맴도는 붉은 인 7(Prop) |
| boss_b19_first_chasa.glb | B-19 첫 차사 | 2.2 | 768 | 회백색 갓·도포, 깨진 갓 테, 눈 청록 발광, 오른손 끊긴 첫 사슬, 뒤 그림자 형상(Prop, 그림자 버티기) |
| boss_b20_great_dam.glb | B-20 큰 물막이 | 6.0 | 1,856 | 몸의 이름 조각 40, 비어 있는 큰 얼굴 자리, 둘레 이름 조각 소용돌이 24(Prop) — 부르기 |
- B-14·B-20은 덩어리 원형이라 사람 모양이 아니다(팔 둘만 있음). B-20은 마당 반경 22 m에 맞춰 폭 약 11 m.
- 발광 면: B-14 눈, B-16·B-13 눈 약하게, B-18 이마 인, B-19 눈, B-20 눈. 점 광원이 필요하면 B-18 이마 (0,-0.14,1.82), B-19 눈 (0,-0.13,2.05)에 붉은/청록 빛을 코드가 달면 된다.
- 천도·파혼 자세(Kneel/Tendo/Pahon)는 덩어리형도 같은 클립 이름으로 들어 있다(몸이 가라앉음).
