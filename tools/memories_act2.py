# 2막(③ 붉은재 · ④ 쇳골) 천도 '기억 조각' 데이터 생성기 — memories_act1.py와 같은 모양
# 다른 점: 월드 시계가 이어서 흐르므로 '나오는 밤(nights)' 칸은 넣지 않는다(밤 단위 폐지, 10-25).
# 왜 따로 만드나: soul_memories.json(원본, 혼 202·백 120)은 시즌 1~3 전체라 크다.
# 코드가 막 단위로 읽기 쉽게, 원본에서 2막 혼만 뽑아 옮긴다.
# 원본이 바뀌면 이 스크립트를 다시 돌린다(손으로 고치지 않는다 — 원본이 하나여야 어긋나지 않는다).
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'docs', 'narrative', 'soul_memories.json')
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'memories_act2.json')
d = json.load(open(SRC, encoding='utf-8'))

# 떠돈 시간 등급(혼의 나이). 보스는 원본 type이 'boss'라서 이야기 기준으로 따로 적는다.
AGE = {'fresh': '갓 죽은', 'year': '해 넘긴', 'old': '오래된'}
BOSS_AGE = {'B-05': 'old', 'B-06': 'old', 'B-07': 'year', 'B-08': 'year'}  # ③ 옛 난리(오래된) / ④ 몇 해 전 막장 붕괴(해 넘긴)

# 단서(F)가 메인 미스터리 "저승이 고장 났다"에 어떻게 닿는가
AXIS = {}
for f in ['F17', 'F20', 'F21', 'F22']: AXIS[f] = 'main'      # 저승 쪽 고장(번호로 불린 혼은 안 들림, 숫자 명부, 흑월의 발자취, 이름 새긴 물건)
for f in ['F16', 'F18', 'F19']: AXIS[f] = 'mirror'            # 이승도 사람을 숫자로 적었다(구덩이, 목패, 장부)

# 제사 집 지켜보기 덧붙임 한 줄(기획 부록 B-4, 서사 10-25).
# 낮에 그 집 제사를 지켜본 뒤 그 이름혼을 천도하면 기억 끝에 한 줄이 더 붙는다.
# 왜 이렇게 쓰나: 기억 조각 수(결말 150)에 세지 않는 "덤"이라, 새 F 단서나 보스 단서를 담으면 안 된다.
# 그래서 사건이 아니라 그 사람의 손버릇·식구·마지막 하루 같은 삶의 결만 쓴다(1인칭, 기억과 같은 목소리).
JESA_EXTRA = {
    'S-049': '누룩은 손녀한테 맡겼다. 그 애 손이 나보다 따뜻하다.',
    'S-050': '바구니는 늘 반만 채웠다. 남은 약초는 내년 몫이니까.',
    'S-051': '정은 제자한테 물려줬다. 돌결 읽는 눈은 아직 서툴러도.',
    'S-052': '낫은 해마다 정월에 갈았다. 아들놈이 그걸 봐 두었으면.',
    'S-067': '주먹밥엔 늘 짠지 한 쪽. 아내가 그것만은 안 빠뜨렸다.',
    'S-068': '딸 손톱은 하얬으면 했다. 그래서 평상엔 못 앉게 했지.',
    'S-069': '국물은 첫 갱 들기 전 새벽에 우렸다. 식으면 맛이 없으니까.',
    'S-070': '노새 이름은 먹보. 내 몫 보리까지 다 먹어 치웠다.',
    'S-071': '아들 놈 첫 품삯으로 짚신을 사 왔더라. 아까워서 못 신었다.',
}

rows = []
for s in d['souls']:
    if s.get('region') not in (3, 4) or s.get('type') == 'baek' or s.get('layer') == 'below':
        continue  # 2막 = 관할 ③④의 혼과 보스만(시즌 3 백 제외)
    t = BOSS_AGE.get(s['id'], s['type'])
    f = s.get('fact')
    rows.append({
        'id': s['id'], 'name': s['name'], 'region': s['region'], 'zone': s['zone'],
        'age': t, 'age_ko': AGE.get(t), 'boss': s['type'] == 'boss',
        'seal': s['seal'],              # clear 또렷 / faded 흐림(+0.25초) / missing 없음(+0.5초)
        'memory_id': s['memory_id'], 'memory': s['memory'], 'tint': s.get('tint'),
        'fact': f, 'fact_text': d['facts'].get(f) if f else None,
        'mystery': bool(f), 'mystery_axis': AXIS.get(f) if f else None,
        'decisive': s.get('weight') == 'decisive',  # ★ 전모 단서(보스 천도로만)
        'weight': s.get('weight'), 'funeral': s.get('funeral'),
        'jesa_extra': JESA_EXTRA.get(s['id']),  # 제사 집 지켜보기 덤(조각 수에 안 셈). 없으면 null
    })
rows.sort(key=lambda r: (r['region'], r['boss'], r['id']))
out = {
    '_설명': '2막(③ 붉은재 · ④ 쇳골) 천도 기억 조각. 원본 soul_memories.json에서 tools/memories_act2.py로 생성. 손으로 고치지 말 것.',
    'source_version': d.get('_version'),
    'rules': {
        'count': '천도 1회 = 기억 조각 1(결말 기준 150에 셈). 같은 혼은 한 번만',
        'mystery': 'mystery=true인 혼을 천도하면 그 fact가 추리판에 켜진다. decisive(★)는 보스 천도로만',
        'axis': {'main': '저승이 고장 났다(숫자 명부)', 'mirror': '이승도 사람을 숫자로 적었다'},
        'generic': '이름 없는 무작위 혼은 generic 줄에서 뽑는다(미스터리 없음, 한 판에 한 줄 한 번)',
        'jesa_extra': '낮에 그 집 제사를 지켜본 뒤 천도하면 기억 끝에 덧붙는 한 줄. 기억 조각 수에 세지 않는다. 장례 대상 이름혼만 있다',
        'pahon': '파혼하면 기억 조각 없음, 그 혼의 fact 출처 하나를 잃는다(추리판에 번진 먹 자국)'},
    'souls': rows,
    'generic': {k: v for k, v in d['generic_pool'].items() if not k.startswith('_')},
    'facts': {k: d['facts'][k] for k in ['F%d' % i for i in range(16, 23)]},
}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(rows), 'souls,', sum(r['mystery'] for r in rows), 'mystery')
