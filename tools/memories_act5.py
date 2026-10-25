# -*- coding: utf-8 -*-
# 5막(⑨ 빈 관할 · ⑩ 열째 관할) 천도 '기억 조각' 데이터 생성기 — memories_act1.py·act4.py와 같은 틀.
# 원본이 바뀌면 이 스크립트를 다시 돌린다(손으로 고치지 않는다 — 원본이 하나여야 어긋나지 않는다).
# 5막에서 더한 것:
#   - ⑨ 기억 지도(map_mark): 인이 없는 땅이라 미니맵이 빈 종이다. 혼을 천도하면 그 혼의 기억이 주변 지형을 그린다.
#     그래서 혼마다 "무엇이 그려지는가" 한 줄을 둔다(기억과 같은 장면에서 뽑는다 — 새 사실을 더하지 않는다).
#   - ⑨ 먹지기가 주워 둔 이름 쪽지(keeper_notes): 이름 줍기를 놓친 사람의 따라잡기. 18장(qa 제안), 구역당 4~5장.
#   - ⑩ 이름 조각(fragment): 이름 없는 조각 셋을 사슬로 이어 한 이름을 만들면 천도할 수 있다. 그때 뜨는 한 줄과 장례 변주 '잇기'.
# 실행: python3 tools/memories_act5.py → docs/narrative/memories_act5.json
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'docs', 'narrative', 'soul_memories.json')
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'memories_act5.json')
d = json.load(open(SRC, encoding='utf-8'))

REGIONS = (9, 10)
AGE = {'fresh': '갓 죽은', 'year': '해 넘긴', 'old': '오래된'}

AXIS = {}
for f in ['F38', 'F39', 'F40', 'F41', 'F46', 'F47']: AXIS[f] = 'main'     # 인을 잃은 땅·풀어내기·백
for f in ['F42', 'F43', 'F44']: AXIS[f] = 'origin'                         # 고장의 처음(첫 파혼)
for f in ['F45']: AXIS[f] = 'ferryman'                                     # 마지막 사공

# 구역이 언제 열리나(밤 번호 대신). 금줄 규칙: 정해진 조건, 못 채우면 바로 앞 지역 첫 진입 뒤 7번째 새벽(기획 10-25).
OPENS = {
    'BlankTown': '⑨ 금줄이 풀린 뒤(4막 끝 C-16 — 문서 창고 아홉째 칸 뒤 문 / ⑧ 첫 진입 뒤 7번째 새벽)',
    'NinthGate': '⑨ 금줄이 풀린 뒤', 'SeallessMarket': '⑨ 금줄이 풀린 뒤', 'SealCave': '⑨ 금줄이 풀린 뒤',
    'FirstVillage': '⑩ 금줄이 풀린 뒤(B-18 처결 — 천도면 먹지기가 인을 돌려놓고, 파혼이면 먹지기가 길을 대신 연다 / ⑨ 첫 진입 뒤 7번째 새벽)',
    'ChainGraves': '⑩ 금줄이 풀린 뒤', 'WellYard': '⑩ 금줄이 풀린 뒤',
    'BigDam': '⑩ 금줄이 풀린 뒤(싸움은 B-19 처결 다음 첫 밤, 또는 ⑩ 첫 진입 뒤 5번째 새벽이 지난 밤 강제)',
}

# ⑨ 기억 지도: 천도하면 그 혼 둘레(반경은 기획 몫)에 그려지는 것. 기억 글에 이미 있는 것만 그린다.
# 왜 한 줄씩 정하나: "보낸 혼이 곧 길"(S-158)을 손으로 느끼게 하려면 지도 조각이 그 사람의 기억처럼 보여야 한다.
MAP_MARK = {
    'S-145': '아홉째 문 앞 돌바닥과, 누가 뛰어간 발자국 하나',
    'S-146': '연기 오르는 부엌 한 채(문패 자리는 빈 채로)',
    'S-147': '장터 좌판 한 줄',
    'S-148': '고샅길 끝, 누군가를 기다리던 자리',
    'S-149': '인장 굴 입구까지 가는 길',
    'S-150': '문 옆 교대 초소(비어 있다)',
    'S-151': '마을 한가운데 서로 부르던 마당',
    'S-152': '장터 끝 짚신 엮는 자리와 짚신 더미',
    'S-153': '빈 고을 개울가',
    'S-154': '장터 뒷골목',
    'S-155': '목수 집과 빈 나무 문패가 걸린 집들',
    'S-156': '종이 걸린 문루',
    'S-157': '인장 굴 안쪽, 누가 오래 누워 있던 자리',
    'S-158': '아무것도 그려지지 않는다 — 대신 그가 걸어온 발자국만(보낸 혼이 없는 차사라서)',
    'S-159': '굿하다 만 자리(빈 상)',
    'S-160': '먹 묻은 표시 바위들을 잇는 길(먹지기의 흔적 쪽으로)',
    'S-161': '굴로 가는 지름길(다리 밑 아이들이 쓰던 샛길처럼)',
    'S-162': '서낭나무와 빈 종이들',
    'B-17': '아홉째 문 둘레 전부 + 빈 관할 쉼터(동트기 안전 지점)',
    'B-18': '⑨ 전체(인 회복 — 지도가 한꺼번에 그려진다)',
}

# 먹지기가 주워 둔 이름 쪽지(⑨). 하나 = '주운 이름 쪽지' 1장(풀어내기 R과 ⑩ 이름 조각에 모두 쓰임).
# 겉글은 둘 중 하나: 4막에서 이름 줍기를 하나도 안 했으면 "이건 내가 대신 주웠다", 했으면 같은 자리에 쪽지 대신 "너도 주웠구나"(보상 중복 없음).
KEEPER_NOTES = {
    'BlankTown': ['먹 묻은 발자국 끝(빈 집 문턱)', '서낭나무 아래', '개울가 넓은 돌', '목수 집 대들보', '우물 뚜껑 위'],
    'NinthGate': ['문 옆 붓 표시 바위', '교대 초소 처마', '종 아래', '문 앞 돌바닥 틈'],
    'SeallessMarket': ['장터 끝 바위', '짚신 더미 속', '빈 좌판 밑', '굿상 아래', '뒷골목 담 틈'],
    'SealCave': ['굴 입구 거적 옆', '굴 중간 붓 표시', '붉은 자국 벽 아래', '굴 안쪽 돌베개'],
}
KEEPER_TEXT = {'missed': '이건 내가 대신 주웠다', 'had': '너도 주웠구나'}

# ⑩ 이은 이름(이름 조각 셋)의 한 줄. 미스터리 없음, 1인칭, 이름·F 단서·보스 단서 말 금지(어미·우물·새끼줄·신발).
# 왜 따로 두나: 조각은 이름이 깨진 혼이라 원본에 사람별 기억이 없다. 이으면 짧게 '그 사람의 결' 한 줄만 돌아온다.
FRAGMENT = [
    '누가 내 이름을 반쯤 불렀다. 나머지는 내가 불렀다.',
    '흩어질 때 소리가 났다. 이어질 때도 났다.',
    '나는 세 군데에 있었다. 이제 한 군데다.',
    '아침밥 냄새. 그거 하나 남았었다.',
    '부르는 사람 목소리가 낯익다.',
    '이름 첫 글자는 늘 먼저 돌아온다더라.',
    '깨진 데가 아프지는 않다. 비어 있었을 뿐이다.',
    '손을 잡아 준 게 누군지 몰라도 고맙다.',
]
JOIN_RITE = {
    'kind': '잇기', 'dur': '약 20초, 대사 0줄',
    'stopped': '사슬 끝에 모인 조각 셋(번진 획)',
    'moving': '번진 획이 서로를 찾아 맞물려 한 글자가 된다. 이은 이름의 한 줄(fragment)이 짧게 보인다',
    'last': '사슬 무덤에 꽂힌 녹슨 사슬 하나가 조금 덜 녹슬어 보인다',
}

rows = []
for s in d['souls']:
    if s.get('region') not in REGIONS or s.get('type') == 'baek' or s.get('layer') == 'below':
        continue  # 5막 = ⑨⑩ 혼과 보스. 물 밑 백은 시즌 3
    f = s.get('fact')
    rows.append({
        'id': s['id'], 'name': s['name'], 'region': s['region'], 'zone': s['zone'],
        'opens': OPENS.get(s['zone']),
        'age': 'old', 'age_ko': AGE['old'], 'boss': s['type'] == 'boss',
        'seal': s['seal'],
        'memory_id': s['memory_id'], 'memory': s['memory'], 'tint': s.get('tint'),
        'fact': f, 'fact_text': d['facts'].get(f) if f else None,
        'mystery': bool(f), 'mystery_axis': AXIS.get(f) if f else None,
        'decisive': s.get('weight') == 'decisive',
        'weight': s.get('weight'), 'funeral': s.get('funeral'),
        'map_mark': MAP_MARK.get(s['id']) if s['region'] == 9 else None,   # ⑨ 기억 지도에 그려지는 것
    })
rows.sort(key=lambda r: (r['region'], r['boss'], r['id']))
ids9 = {r['id'] for r in rows if r['region'] == 9}
assert ids9 == set(MAP_MARK), ids9 ^ set(MAP_MARK)     # ⑨ 혼은 빠짐없이 지도 조각이 있어야 한다
assert sum(len(v) for v in KEEPER_NOTES.values()) == 18
for x in FRAGMENT: assert not any(w in x for w in ('어미', '우물', '새끼줄', '신발', '춥', '추워', '한기')), x

out = {
    '_설명': '5막(⑨ 빈 관할 · ⑩ 열째 관할) 천도 기억 조각. 원본 soul_memories.json에서 tools/memories_act5.py로 생성. 손으로 고치지 말 것.',
    'source_version': d.get('_version'),
    'rules': {
        'count': '천도 1회 = 기억 조각 1(결말 기준 150에 셈). 같은 혼은 한 번만. 이은 이름(⑩)도 천도 1회로 센다',
        'mystery': 'mystery=true인 혼을 천도하면 그 fact가 추리판에 켜진다. decisive(★)는 보스 천도로만',
        'axis': {'main': '인을 잃은 땅·풀어내기·백', 'origin': '고장의 처음(첫 파혼)', 'ferryman': '마지막 사공'},
        'region9_light': '(기획 10-25) ⑨ 안에서만 새벽·낮·저녁 빛이 짙은 안개+낮은 밝기. 새벽이 와도 혼이 흩어지지 않고 낮엔 밤 밀도의 50%. 서낭당 반경 12m에만 새벽빛(쉼 자리). B-18 천도 뒤 ⑨에 처음으로 새벽이 온다',
        'region9_clues': '⑨는 새벽 틈이 없다. 보스 단서는 "먹지기의 흔적" 둘레에서 언제나(엿듣기 = 인 없는 혼들의 혼잣말)',
        'memory_map': '⑨ 미니맵은 빈 종이. 천도하면 그 혼의 map_mark가 둘레에 그려진다. 파혼한 자리는 끝까지 빈 종이. 무작위 혼은 둘레 길만 조금',
        'keeper_notes': '먹지기가 주워 둔 이름 쪽지 18장(구역당 4~5). 먹지기 흔적(발자국·표시 바위·쪽지 조각) 근처를 만지면 나온다. 1장 = 주운 이름 쪽지 1장. 겉글은 keeper_text',
        'fragment': '⑩ 이름 조각: 조각 하나는 천도할 수 없다. 같은 색 조각 셋을 사슬로 이으면 한 이름이 되어 천도 가능. 4막에서 주운 쪽지·⑨ 먹지기 쪽지는 조각 하나로 센다. 그냥 파혼하면 빠르지만 물막이 눈금이 오른다',
        'rite': '⑩ 장례 변주 "잇기"(join_rite). 이은 이름을 천도할 때마다. ⑨는 장례 변주 대신 기억 지도',
        'dam': '⑦~⑩에서 파혼하면 물막이 눈금이 오른다(F32). B-20 풀어내기 조건 R/S ≥ 0.6(qa 합의)',
        'pahon': '파혼하면 기억 조각 없음, 그 혼의 fact 출처 하나를 잃는다(추리판에 번진 먹 자국)'},
    'souls': rows,
    'keeper_notes': KEEPER_NOTES, 'keeper_text': KEEPER_TEXT,
    'fragment': FRAGMENT, 'join_rite': JOIN_RITE,
    'generic': {k: v for k, v in d['generic_pool'].items() if not k.startswith('_')},
    'facts': {k: d['facts'][k] for k in sorted({r['fact'] for r in rows if r['fact']}, key=lambda x: int(x[1:]))},
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(rows), 'souls,', sum(r['mystery'] for r in rows), 'mystery,', len(MAP_MARK), 'map marks, 18 keeper notes,', len(FRAGMENT), 'fragment lines')
