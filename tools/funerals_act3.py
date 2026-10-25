# -*- coding: utf-8 -*-
# 3막 장례 대본 10개: ⑤ 갯마을 포구 5(S-085~089) + ⑥ 도성 아랫마을 5(S-103~107).
# 근거: SCENARIO-ACT3 "⑤의 장례"·"⑥의 장례" 표(#2 멈춘 것 / #6 다시 움직이는 것), 기획 3막 지도(act3_map.json funerals).
# 틀(박자·시간·파혼·처결 못 함)은 1·2막과 똑같다 → funerals_act1.py의 함수를 그대로 빌려 쓴다.
# 3막에서 다른 점:
#   ⑤ 갯마을 = 몸이 있는 장례는 귀하다. 그래서 포구 사람들이 다 나온다. 조등 연기가 하늘이 아니라 바다 쪽으로 흐른다.
#   ⑥ 도성 = 상주가 없다. 이웃이 상주가 된다. 무적 혼(S-104·105·106)의 장례는 B-11(왕초) 천도 다음 낮부터 열리고,
#            B-11을 파혼하면 열리지 않는다(기획 funeral_rules_act3). 장례를 치른 무덤에만 다음 새벽부터 팻말이 선다(기획 확정).
# 실행: python3 tools/funerals_act3.py → docs/narrative/funerals_act3.json
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import funerals_act1 as F
from funerals_act1 import st

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'narrative', 'funerals_act3.json')

F.SCENE[5] = {'morning': '아침의 갯마을 포구. {house} 앞에 조등. 빈 배들이 선창에 묶여 흔들린다. 차사는 그물 너는 마당 끝에 서 있다',
              'cap': '[파도] [갈매기] [요령 한 번]', 'sfx': ['cut.yoryeong.ring'], 'req': ['amb.harbor(파도·갈매기·배 삐걱임)'],
              'proc': '상여가 집을 나선다. 몸이 있는 장례는 귀해서 포구 사람들이 다 나와 뒤를 따른다. 만장이 차사의 몸을 스친다. 아무도 차사를 피하지 않는다',
              'away': '포구 어귀에서 노제를 지낸 행렬이 곶 길로 올라가 사라진 뒤. 조등 연기가 하늘이 아니라 바다 쪽으로 흐른다',
              'hush': '[파도 소리만]'}
F.SCENE[6] = {'morning': '아침의 도성 아랫마을. {house} 앞에 조등. 상주 자리에 이웃들이 서 있다. 차사는 길가에 서 있다',
              'cap': '[먼 장터 웅성거림] [요령 한 번]', 'sfx': ['cut.yoryeong.ring'], 'req': ['amb.market(장터 웅성거림, 말이 알아들리지 않게)'],
              'proc': '상여가 나선다. 상주가 없어 이웃들이 상여를 멘다. 만장 대신 헝겊 조각을 단 장대 몇 개. 장대가 차사의 몸을 스친다. 아무도 차사를 피하지 않는다',
              'away': '저잣거리 한가운데에서 노제를 지낸 행렬이 큰길을 따라 성문 밖으로 나간 뒤',
              'hush': '[장터 소리가 멀어진다]'}

FUNERALS = [
 # ───── ⑤ 갯마을 포구 ─────
 {'id': 'FUN-S085', 'soul': 'S-085', 'region': 5, 'name': '갯골댁 장례', 'house': '갯골댁 집',
  'stopped': '마당에 그물이 펼쳐져 있다. 그물코 하나가 비어 있다',
  'moving': st(25.0, '며느리가 그 그물코를 깁는다. 다 깁고 나서 그물을 바다 쪽으로 한 번 턴다',
               cap='[그물 터는 소리]', req=['cut.net.shake(그물 터는 소리)'], cam={'mode': 'low_move', 'to': 'net'}, control='walk',
               note='깊은 박자 ②. 기억 색(그물 삼베빛)'),
  'pending_line': ('갯골댁 며느리', '어머님 날은 아직이래요. 그물은 펴 둘게요.'),
  'pending_act': '며느리가 그물 앞에 앉았다가 바늘을 그물에 꽂아 두고 일어난다'},
 {'id': 'FUN-S086', 'soul': 'S-086', 'region': 5, 'name': '헛묘지기 영감 장례', 'house': '헛묘지기 집',
  'stopped': '곶 아래 헛묘 곁에 삽 한 자루가 꽂혀 있다',
  'moving': st(25.0, '손자가 삽을 든다. 옷만 묻은 무덤들 옆에, 처음으로 몸이 든 무덤 하나를 짓는다',
               cap='[삽질 소리]', req=['cut.shovel.dig(삽으로 흙 퍼는 소리)'], cam={'mode': 'side_track', 'to': 'new_grave'}, control='walk',
               note='깊은 박자 ②. 기억 색(젖은 흙빛). 헛묘 수를 화면 글로 세지 않는다(보스 단서 B09-D1과 겹침)'),
  'away': '포구 어귀에서 노제를 지낸 행렬이 곶 길을 올라 헛묘 옆 새 무덤에서 멈춘 뒤. 조등 연기가 바다 쪽으로 흐른다',
  'pending_line': ('헛묘지기 손자', '할아버지 날을 못 받았대. 삽은 그대로 둬.'),
  'pending_act': '손자가 삽 앞에 섰다가 손을 대지 않고 돌아선다'},
 {'id': 'FUN-S087', 'soul': 'S-087', 'region': 5, 'name': '소금장수 덕보 장례', 'house': '덕보 집',
  'stopped': '소금 창고 앞에 반쯤 진 소금 지게가 내려져 있다',
  'moving': st(25.0, '이웃 염부가 지게를 대신 진다. 바닷가에 이르러 소금 한 줌을 바다에 뿌린다',
               cap='[소금 흩는 소리] [파도]', req=['cut.salt.scatter(소금 한 줌 흩는 소리)'], cam={'mode': 'side_track', 'to': 'shore'}, control='walk',
               note='깊은 박자 ②. 기억 색(소금 흰빛). 누구 몫인지는 글로 쓰지 않는다(기억 "형은 바다에 있다"를 본 사람만 안다)'),
  'pending_line': ('이웃 염부', '덕보 지게는 아직 못 지겠네.'),
  'pending_act': '지게가 내려진 그대로다. 이웃 염부가 멜빵을 한 번 만져 보고 간다'},
 {'id': 'FUN-S088', 'soul': 'S-088', 'region': 5, 'name': '순덕 장례', 'house': '순덕 집',
  'stopped': '방 안에 혼례 저고리가 개어져 있다',
  'proc': '상여가 집을 나선다. 상여 위에 혼례 저고리가 덮여 있다(어머니가 덮었다). 포구 사람들이 다 나와 뒤를 따른다. 만장이 차사의 몸을 스친다',
  'moving': st(25.0, '노제 자리에서 포구로 배 한 척이 들어온다. 그 집 배는 아니다. 그래도 사람들이 다 같이 손을 흔든다',
               cap='[노 젓는 소리] [파도]', req=['cut.oar.row(노 젓는 소리)'], cam={'mode': 'tilt_up', 'to': 'harbor_mouth'}, control='walk',
               note='깊은 박자 ②. 기억 색(저고리 다홍). 배 이름·깃발을 보이지 않는다(만선호와 헷갈리지 않게)'),
  'pending_line': ('순덕 어머니', '저고리는 다시 개어 둬야지.'),
  'pending_act': '어머니가 저고리를 펼쳤다가 도로 갠다'},
 {'id': 'FUN-S089', 'soul': 'S-089', 'region': 5, 'name': '등대지기 장례', 'house': '등대지기 막',
  'stopped': '등대지기 막 창가에 등잔이 아직 타고 있다. 아침이다',
  'moving': st(25.0, '딸이 등잔을 끈다. 아침이니까',
               cap='[심지 끄는 소리]', req=['cut.lamp.snuff(등잔 심지 끄는 소리)'], cam={'mode': 'low_move', 'to': 'lamp'}, control='walk',
               note='깊은 박자 ②. 기억 색(등잔 노란빛)'),
  'variant': st(31.0, '(망부석 아낙을 천도한 뒤라면) 해 질 녘 한 컷: 딸이 등잔을 다시 켜 곶 끝 높은 자리에 건다. 포구 등대가 된다',
                control='walk', cond='B-09 천도함', note='SCENARIO-ACT3 ⑤의 장례 표. 화면을 저녁빛으로 잠깐 바꾼 한 컷(시계는 그대로)'),
  'pending_line': ('등대지기 딸', '아버지 등잔은 아직 못 끄겠어.'),
  'pending_act': '낮인데 창가 등잔이 그대로 타고 있다. 딸이 그 앞을 지나간다'},
 # ───── ⑥ 도성 아랫마을 (상주가 없다 — 이웃이 상주) ─────
 {'id': 'FUN-S103', 'soul': 'S-103', 'region': 6, 'name': '떡장수 할미 장례', 'house': '떡장수 좌판',
  'stopped': '좌판 위에 빈 떡판이 놓여 있다',
  'proc': '다리 밑 아이들이 상여를 멘다. 넷이서 멨다. 만장 대신 헝겊 장대 몇 개가 차사의 몸을 스친다. 아무도 차사를 피하지 않는다',
  'moving': st(25.0, '상여가 너무 무거워 아이들이 비틀거린다. 다리 밑에서 아이들이 더 달려와 넷이 여덟이 된다. 발을 맞춘다',
               cap='[아이들 발소리]', req=['cut.kids.steps(아이들 맨발 발소리)'], cam={'mode': 'side_track', 'to': 'procession'}, control='walk',
               note='깊은 박자 ②. 기억 색(콩고물 노란빛)'),
  'variant': st(31.0, '(다리 밑 왕초를 천도한 뒤라면) 아이들이 서로를 보며 입 모양으로 별명을 부르고 발을 맞춘다(소리 없음)',
                control='walk', cond='B-11 천도함', note='대사 0 원칙 — 입 모양만. 어느 별명인지 글로 쓰지 않는다'),
  'pending_line': ('다리 밑 아이들', '떡장수 할매, 아직 날을 못 받았대.'),
  'pending_act': '아이 하나가 빈 떡판 앞에 쪼그려 앉았다가 일어난다'},
 {'id': 'FUN-S104', 'soul': 'S-104', 'region': 6, 'name': '짐꾼 곰 장례', 'house': '짐꾼 지게 자리', 'mujeok': True,
  'stopped': '저잣거리 기둥에 빈 지게가 기대 서 있다',
  'proc': '상여 대신 지게다. 저잣거리 상인들이 지게에 그의 짚신을 얹어 메고 장터를 한 바퀴 돈다. 지게가 차사의 몸을 스친다',
  'proc_sound': ('[요령] [장터가 조용해진다]', ['cut.yoryeong.ring'], ['amb.market.hush(웅성거림이 잦아드는 장터)']),
  'moving': st(25.0, '한 바퀴를 다 돈 상인들이 지게를 장터 어귀에 세운다. 상인 하나가 지게 위 짚신을 가지런히 고쳐 놓는다',
               cam={'mode': 'low_move', 'to': 'jige'}, control='walk', note='깊은 박자 ②. 기억 색(지게 나무빛)'),
  'away': '장터를 한 바퀴 돈 행렬이 큰길을 따라 성문 밖으로 나간 뒤',
  'pending_line': ('저잣거리 상인', '그 지게는 그냥 둬. 아직 날이 안 났대.'),
  'pending_act': '지게가 기둥에 기댄 그대로다. 상인 하나가 그 옆에 짐을 내려놓았다가 도로 든다'},
 {'id': 'FUN-S105', 'soul': 'S-105', 'region': 6, 'name': '움막촌 어미 장례', 'house': '움막촌 어미 판잣집', 'mujeok': True,
  'stopped': '판잣집 문턱에 아이 배냇저고리가 개어져 있다',
  'moving': st(25.0, '이웃 아낙이 배냇저고리 안쪽에 실로 아이 이름을 바느질한다. 관아 대신 옷에 적는 호적이다',
               cap='[바늘 소리]', req=['cut.needle.sew(천에 바늘 꿰는 소리)'], cam={'mode': 'low_move', 'to': 'baby_jacket'}, control='walk',
               note='깊은 박자 ②. 기억 색(배냇저고리 흰빛). 수놓은 글자는 읽히지 않게'),
  'away': '움막촌 우물가에서 노제를 지낸 행렬이 성벽 밑 비탈을 따라 성문 밖으로 나간 뒤',
  'pending_line': ('움막촌 이웃 아낙', '저 애 어미 날은 아직이래.'),
  'pending_act': '이웃 아낙이 아이를 업고 판잣집 문턱 앞을 서성인다'},
 {'id': 'FUN-S106', 'soul': 'S-106', 'region': 6, 'name': '쥐똥이 장례', 'house': '쥐똥이 거적', 'mujeok': True,
  'stopped': '다리 밑에 거적 한 장이 덮인 채다',
  'proc': '다리 밑 아이들이 작은 상여를 멘다. 헝겊 장대 하나가 차사의 몸을 스친다. 아무도 차사를 피하지 않는다',
  'moving': st(25.0, '아이들이 거적을 걷는다. 다리 기둥의 별명 목록 가운데 하나 옆에 숯으로 꽃 하나를 그린다',
               cap='[숯 긋는 소리]', req=['cut.charcoal.draw(숯으로 돌에 긋는 소리)'], cam={'mode': 'tilt_up', 'to': 'bridge_pillar'}, control='walk',
               note='깊은 박자 ②. 기억 색(숯 검정). 꽃은 "쥐똥이" 옆. 맨 아래 빈칸(B11-D1 단서)은 건드리지 않는다'),
  'away': '다리 밑에서 노제를 지낸 행렬이 큰길로 올라 성문 밖으로 나간 뒤',
  'pending_line': ('다리 밑 아이들', '그 거적 걷지 마. 아직이래.'),
  'pending_act': '거적이 덮인 그대로다. 아이들이 그 둘레를 비켜 앉는다'},
 {'id': 'FUN-S107', 'soul': 'S-107', 'region': 6, 'name': '성문 문지기 장례', 'house': '문지기 막',
  'stopped': '문지기 막 벽에 아버지가 쓰던 빗장 막대가 기대 서 있다',
  'moving': st(25.0, '해 질 녘 한 컷: 아들 문지기가 성문을 닫다가 빗장을 쥔 채 잠깐 멈춘다. 문을 조금 늦게 닫는다. 그 틈으로 밖에서 누가 뛰어 들어온다',
               cap='[성문 삐걱임] [뛰어오는 발소리]', req=['cut.gate.creak(큰 나무 성문 삐걱임)'], cam={'mode': 'move', 'to': 'city_gate'}, control='walk',
               note='깊은 박자 ②. 기억 색(빗장 쇠빛). 화면을 저녁빛으로 잠깐 바꾼 한 컷(시계는 그대로). 뛰어 들어온 사람의 얼굴은 보이지 않는다'),
  'pending_line': ('아들 문지기', '아버지 날은 아직이오. 문은 내가 닫소.'),
  'pending_act': '아들 문지기가 빗장 막대를 집었다가 도로 벽에 기대 놓는다'},
]

SRC = json.load(open(os.path.join(os.path.dirname(OUT), 'soul_memories.json'), encoding='utf-8'))
MEM = {s['id']: s['memory'] for s in SRC['souls']}
AROUND = {5: '포구는 여느 날처럼 그물을 넌다', 6: '저잣거리는 여느 날처럼 붐빈다'}
PEND_CAP = {5: '[파도]', 6: '[먼 장터 웅성거림]'}

out = []
for f in FUNERALS:
    f['memory'] = MEM[f['soul']]
    b = F.build(f)
    r = f['region']
    for br in b['branches']:   # 1막 함수가 ①②만 아는 부분(파혼 주변 풍경·처결 못 함 첫 소리)을 3막 것으로 바꾼다
        if br['branch'] == '파혼':
            br['steps'][0]['action'] = br['steps'][0]['action'].replace('장터는 여느 날처럼 붐빈다', AROUND[r])
        if br['branch'] == '처결 못 함':
            br['steps'][0]['caption'] = PEND_CAP[r]
    if f.get('mujeok'):
        b['mujeok'] = True
        b['opens'] = 'B-11(다리 밑 왕초) 천도 다음 낮부터, 하루 하나씩. B-11을 파혼하면 이 장례는 열리지 않는다(천도한 넋·기억은 그대로)'
    out.append(b)

data = {
    '_설명': '3막 장례 10개(⑤ 갯마을 5 + ⑥ 도성 아랫마을 5). tools/funerals_act3.py로 생성. 틀과 규칙은 funerals_act1.json과 같다. 서사 2026-10-25',
    'rules': {
        'same_as_act1': '천도·파혼 대사 0, 천도 48초(두 박자만 깊게), 파혼 조등만, 처결 못 함 20초·산 사람 한 줄·혼마다 한 번, 하루 한 번, condition 박자',
        'harbor': '⑤ 몸이 있는 장례는 귀해서 포구 사람들이 다 나온다. 조등 연기는 바다 쪽으로 흐른다(대사 없이 보이는 이 마을의 상처)',
        'city': '⑥ 상주가 없어 이웃이 상주. 만장 대신 헝겊 장대. 장례를 치른 무덤에만 다음 새벽부터 팻말이 선다(장면 밖 풍경. 자리: act3_map.json, 구덩이 무덤 남쪽 줄 다섯 자리)',
        'mujeok': 'mujeok=true 장례는 B-11 천도 다음 낮부터 열린다. B-11 파혼이면 열리지 않는다(기획 funeral_rules_act3와 같음)',
        'one_cut_jump': 'S-089 variant·S-107 moving의 "해 질 녘 한 컷"은 화면 빛만 저녁으로 바꾼 짧은 컷이다. 월드 시계는 흐르지 않게 연출만',
        'numbers': '헛묘 수·별명을 화면 글로 세거나 읽히게 하지 않는다(보스 단서와 겹침)',
        'cold': '추위 말·몸 움츠림 없음',
        'names': '3막 산 사람은 이름 없이 역할로(npc_act3.json)',
        'positions': '노제·나감 자리는 기획 act3_map.json funerals. S-105 노제 움막촌 우물, S-106 노제 다리 밑(기획 반영 10-25)',
    },
    'funerals': out,
}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out), 'funerals')
