# -*- coding: utf-8 -*-
# 1막 장례 대본 8개: ① 솔고개 4(S-002 윤 소사, S-003 연이, S-004 칠복, S-005 허 훈장) + ② 검은여울 장터 4(S-019 판쇠, S-020 최씨, S-021 끝순, S-029 덕수).
# 박돌쇠(S-001)는 기본형이라 first_session_scripts.json에 따로 있다.
# 근거: FUNERAL-SEQUENCE §1(발생 규칙)·§2(연출 원칙)·§4-1·4-2(변주표), 소설 1부 3~6장(같은 장례를 소설이 먼저 썼다), 기본형은 first_session_scripts.json의 박돌쇠 장례.
# 왜 기본형보다 짧은가: 7박자 전부는 첫 장례(박돌쇠)에만 쓴다. 이후 장례는
#   "멈춘 사물"과 "다시 움직이는 사물" 두 박자만 깊게 보여 주고 나머지는 짧게 지나간다(소설 집필 스킬 §8과 같은 규칙).
#   그래서 길이가 70초 → 약 48초다. 같은 장면을 네 번 다 보게 하면 장례가 "농사"처럼 느껴지기 때문이다.
# ① 솔고개: 작은 산골 마을. 요령잡이는 갑술 영감, 행렬은 다리를 건너 고개 너머로.
# ② 장터: 행렬이 길고 구경꾼이 많다. 차사는 사람 사이를 지나가고, 사람들은 그를 피하지 않고 지나간다. 행렬은 읍성 문 밖으로.
# 대사·자막·내레이션 0. 화면에 글로 뜻을 쓰지 않는다. 대괄호 글은 소리 자막(caption, 청각 보조 설정에서만 보임).
# 실행: python3 tools/funerals_act1.py → docs/narrative/funerals_act1.json
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_map import promote  # 사운드팀이 만든 소리는 요청 → 있는 소리로 옮긴다

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'funerals_act1.json')

def st(t, act, cap=None, sfx=None, req=None, cam=None, control=None, note=None, cond=None):
    """장면 한 박자. sfx = 사운드팀에 이미 있는 소리 id, req = 아직 없는 소리(요청)."""
    s = {'t': t, 'action': act}
    if cam: s['camera'] = cam
    if cap: s['caption'] = cap
    if sfx: s['sfx'] = sfx
    if req: s['sfx_request'] = req
    if control: s['control'] = control
    if note: s['note'] = note
    if cond: s['condition'] = cond   # 이 조건일 때만 이 박자를 쓴다(아니면 건너뜀)
    return s

# 네 장례가 함께 쓰는 앞뒤 박자(장터 아침 → 상여가 장터를 지남 → 사잣밥 → 복귀)
SCENE = {
 1: {'morning': '아침의 솔고개 마을. {house} 대문에 조등. 차사는 길 건너에 서 있다', 'cap': '[바람] [먼 닭울음] [요령 한 번]',
     'sfx': ['amb.field', 'cut.yoryeong.ring'], 'req': ['amb.rooster(먼 닭울음)'],
     'proc': '상여가 집을 나선다. 앞에 요령잡이 갑술 영감, 상여꾼 여덟, 뒤로 만장. 만장이 차사의 몸을 스친다. 아무도 차사를 피하지 않는다',
     'away': '행렬이 다리를 건너 고개 너머로 사라진 뒤', 'hush': '[정적]'},
 2: {'morning': '장날 아침의 장터. {house} 대문에 조등. 차사는 장꾼들 사이에 서 있다', 'cap': '[장터 웅성거림] [요령 한 번]',
     'sfx': ['cut.yoryeong.ring'], 'req': ['amb.market(장터 웅성거림, 말이 알아들리지 않게)'],
     'proc': '상여가 대문을 나서 장터 한가운데를 지난다. 구경꾼이 길 양쪽에 늘어선다. 만장이 차사의 몸을 스친다. 아무도 차사를 피하지 않는다',
     'away': '행렬이 읍성 문 밖으로 사라진 뒤', 'hush': '[장터 소리가 멀어진다]'},
}

def opening(region, house, stopped):
    sc = SCENE[region]
    return [
        st(0.0, sc['morning'].format(house=house),
           cap=sc['cap'], sfx=sc['sfx'], req=sc['req'],
           cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 5.0}, control='none'),
        st(5.0, stopped, cap=sc['hush'], cam={'mode': 'low_move', 'to': 'stopped_thing', 'time': 7.0}, control='none',
           note='깊은 박자 ①: 어젯밤 기억 속 사물이 멈춰 있다. 플레이어가 혼자 알아차리게 한다'),
    ]

def procession(region, override=None):
    return st(12.0, override or SCENE[region]['proc'],
              cap='[요령] [곡소리] [멀리 웅얼거리는 상여소리]', sfx=['cut.yoryeong.ring'],
              req=['vo.wail(곡소리, 말 없음)', 'mus.sangyeo.far(가사가 안 들리는 먼 상여소리)'],
              cam={'mode': 'quarter', 'height': 'low'}, control='walk',
              note='업 10 미만이면 개 한 마리가 차사가 선 쪽을 잠깐 보다 만다(모호하게). 업 10 이상이면 짖고 달아난다')

def closing(region):
    return [
        st(38.0, SCENE[region]['away'] + ', 그 집 대문 밖 사잣밥: 밥 세 그릇, 짚신 세 켤레, 엽전 몇 닢. 차사가 그 앞에 잠깐 선다(자동)',
           cap='[바람] [멀리서 요령 마지막 한 번]', sfx=['cut.yoryeong.ring', 'cut.coins.few'],
           cam={'mode': 'pull_out', 'to': 'gate', 'then': 'quarter'}, control='none', note='집을 수 없다. 수치 변화 없음'),
        st(46.0, '페이드 없이 평소 낮 화면', control='restore'),
    ]

def pahon(region, house):
    around = '마을은 여느 날처럼 조용하다' if region == 1 else '장터는 여느 날처럼 붐빈다'
    return {'branch': '파혼', 'duration': 0.0, 'skippable': False,
            'steps': [st(0.0, f'{house} 대문에 조등만 걸려 있다. 문은 닫혀 있다. {around}. 다가가도, 오래 서 있어도 아무 일도 일어나지 않는다',
                         control='walk', note='트리거 없음. 조등 소품 하나만. 사잣밥도 없다. 안내 문구 없음')]}

def pending(region, house, act):
    return {'branch': '처결 못 함', 'duration': 12.0, 'skippable': True,
            'note': '대사 없음(박돌쇠 아내의 한 줄은 첫 장례만의 예외). 그날 저녁 명부 맨 아래 줄에 같은 종류로 다시 적히고, 먹지기 쪽지 "어제 이름을 오늘 또 적었다."가 붙는다(이미 붙은 날이면 쪽지는 생략)',
            'steps': [st(0.0, f'{house}. 상은 아직 차려지지 않았다. ' + act, cap='[바람]' if region == 1 else '[장터 웅성거림]', control='walk'),
                      st(12.0, '조작 복귀', control='restore')]}

FUNERALS = [
 # ───── ① 솔고개 (소설 1부 3·4·5·6장과 같은 장례) ─────
 {'id': 'FUN-S002', 'soul': 'S-002', 'region': 1, 'name': '윤 소사 장례', 'house': '윤 소사네',
  'memory': '제삿밥을 차려 놓고 기다렸다. 영감은 그해도, 이듬해도 오지 않았다.',
  'stopped': '마당 제사상에 위패가 하나 놓여 있다(영감). 메 그릇은 뚜껑이 덮인 채 식었다',
  'proc': '상여가 집을 나선다. 앞에 요령잡이 갑술 영감. 맏상주(아들)는 오동나무 지팡이를 짚었다(어머니 상). 만장이 차사의 몸을 스친다. 아무도 차사를 피하지 않는다',
  'moving': st(25.0, '하관을 마치고 돌아온 아들이 새 위패를 두 손으로 받쳐 들고 와 제사상의 영감 위패 곁에 나란히 놓는다. 위패가 둘이 된다. 상 위 숟가락 하나가 틀어져 있는데 고치지 않는다',
               cap='[나무 내려놓는 소리]', cam={'mode': 'low_move', 'to': 'jesa_table'}, control='walk',
               note='깊은 박자 ②. 기억 색(촛불 노랑)이 한 번 번졌다 사라진다. 소설 5장(반혼)과 같은 장면'),
  'variant': st(31.0, '(나루 영감을 천도한 뒤라면) 상 위의 엽전 다섯 닢이 치워져 있다. 그 자리만 상보가 조금 밝다',
                control='walk', cond='B-01 천도함', note='FUNERAL-SEQUENCE §4-1: 뱃삯 약속이 끝났다. B01-D1 단서 자리이므로 단서를 이미 얻은 뒤에만 바뀐다'),
  'pending_act': '아들이 마당 제사상 앞에 혼자 서서 메 그릇 뚜껑을 열었다가 도로 덮는다'},
 {'id': 'FUN-S003', 'soul': 'S-003', 'region': 1, 'name': '연이 장례', 'house': '연이네 떡집',
  'memory': '상여가 너무 자주 나가. 올봄에만 일곱 번이야. 떡을 찌다가 손을 멈췄다.',
  'stopped': '부뚜막 위 떡시루가 식어 있다. 시루 밑 떡이 덜 익었다',
  'moving': st(25.0, '상여가 떠난 뒤 이웃 아낙들(곱단네·간난이)이 연이네 부엌에서 떡을 다시 찐다. 김이 오른다. 아낙 하나가 떡 소쿠리를 이고 상여꾼들 쪽으로 나른다',
               cap='[시루에 김 오르는 소리]', req=['cut.steam.rise(시루 김 오르는 소리)'], cam={'mode': 'move', 'to': 'kitchen'}, control='walk',
               note='깊은 박자 ②. 기억 색(쌀김 흰빛)이 한 번 번졌다 사라진다. 상여는 마을에 하나라 같은 상여를 쓴다(소설 3장)'),
  'pending_act': '부엌 문이 열려 있다. 곱단네가 들여다보다 시루에 손을 대지 않고 돌아선다'},
 {'id': 'FUN-S004', 'soul': 'S-004', 'region': 1, 'name': '칠복 장례', 'house': '기와집',
  'sajabap': '멍석 없이 짚 한 줌, 밥 한 그릇, 짚신 한 켤레(엽전 없음, 소설 6장)',
  'memory': '밤에 둑 쪽에서 쇠사슬 끄는 소리가 났다. 개들이 일제히 엎드려 울었다.',
  'stopped': '기와집 담 모퉁이에 짚으로 엮은 빈 개집. 개는 없다',
  'proc_sound': ('[놋그릇 두드리는 소리] [발소리]', [], ['cut.brass.tap(놋그릇을 숟가락으로 두드림)']),
  'away': '들것이 둑길 끝으로 사라진 뒤',
  'proc': '상여 대신 머슴방 문짝을 들것으로 쓴다. 사람 넷이 멘다. 앞사람이 놋그릇을 숟가락으로 두드린다. 들것은 둑길로 간다. 아무도 차사를 피하지 않는다',
  'moving': st(25.0, '누렁 개 한 마리가 어디선가 나타나 들것 뒤를 따라간다. 사람들이 쫓아도 물러서지 않는다. 행렬과 함께 둑길 끝으로 사라진다',
               cap='[개 발소리] [놋그릇 두드리는 소리]', req=['cut.brass.tap(놋그릇을 숟가락으로 두드림)'], cam={'mode': 'side_track', 'to': 'dog'}, control='walk',
               note='깊은 박자 ②. 기억 색(짚 누렁)이 한 번 번졌다 사라진다. 소설 6장과 같은 장례(문짝 들것, 사람 넷, 놋그릇, 둑길). 이 개는 차사를 보지 않는다'),
  'pending_act': '빈 개집 앞에 개밥 그릇이 엎어져 있다. 아무도 치우지 않는다'},
 {'id': 'FUN-S005', 'soul': 'S-005', 'region': 1, 'name': '허 훈장 장례', 'house': '서당',
  'memory': '명부라는 게 있다면 이름은 먹으로 쓰겠지. 그 먹은 무엇을 갈아 만들까.',
  'stopped': '서당 서안 위 벼루가 말라 있다. 붓걸이 넷 가운데 한 자리가 비었다',
  'moving': st(25.0, '상여가 떠난 뒤 서당 아이들이 벼루에 물을 붓고 먹을 간다. 저마다 제 이름을 써 본다. 큰 아이가 훈장 이름을 써서 노제 상에 돌로 눌러 둔다',
               cap='[먹 가는 소리]', req=['cut.ink.grind(벼루에 먹 가는 소리)'], cam={'mode': 'low_move', 'to': 'school_desk'}, control='walk',
               note='깊은 박자 ②. 기억 색(먹빛 청회)이 한 번 번졌다 사라진다. 명부의 먹(F5)과 겹치는 유일한 장면이지만 단서는 아니다. 종이 글씨는 읽히지 않게. 소설 4장과 같은 장면'),
  'pending_act': '서당 문이 닫혀 있다. 아이 둘이 문 앞에서 기웃거리다 돌아간다'},
 # ───── ② 검은여울 장터 ─────
 {'id': 'FUN-S019', 'soul': 'S-019', 'name': '엿장수 판쇠 장례', 'house': '판쇠의 엿방',
  'memory': '가위 장단을 치면 아이들이 몰려왔지. 이번엔 아무도 오지 않는다.',
  'stopped': '엿판 위에 큰 가위가 벌어진 채 놓여 있다. 엿은 굳어 금이 갔다',
  'moving': st(25.0, '상여 뒤를 장터 아이들(꼭지·차돌이)이 따라간다. 가위 대신 손뼉으로 장단을 흉내 낸다. 박자가 자꾸 어긋나도 그치지 않는다',
               cap='[아이들 손뼉 장단]', req=['cut.kids.clap(아이들 손뼉 장단, 박자 어긋남)'],
               cam={'mode': 'side_track', 'to': 'children'}, control='walk',
               note='깊은 박자 ②: "아무도 오지 않는다"던 사람 뒤로 아이들이 온다. 기억 색(엿 호박색)이 화면 가장자리에 한 번 번졌다 사라진다'),
  'pending_act': '아이들이 엿방 앞을 기웃거리다 닫힌 문을 보고 흩어진다'},
 {'id': 'FUN-S020', 'soul': 'S-020', 'name': '포목전 최씨 장례', 'house': '포목전',
  'memory': '외상 장부의 이름을 다 지우고 왔다. 받을 생각은 처음부터 없었다.',
  'stopped': '포목전 안쪽 화로에 재만 남아 있다. 장부를 태운 자리다. 선반의 무명 필들은 그대로 쌓여 있다',
  'moving': st(25.0, '상여가 떠난 뒤 장터 사람들이 하나씩 포목전 문 앞에 와서 무명 한 필씩 내려놓고 간다. 서로 말을 나누지 않는다. 문 앞에 무명이 쌓인다',
               cap='[천 내려놓는 소리]', sfx=['cut.cloth.flutter'], cam={'mode': 'fixed', 'to': 'shop_door'}, control='walk',
               note='깊은 박자 ②: 지운 외상을 갚을 길이 없어 천으로 갚는다. 기억 색(쪽물 남색)이 한 번 번졌다 사라진다'),
  'pending_act': '포목전 문은 열려 있는데 아무도 들어가지 않는다. 지나가던 아낙이 문 앞에서 걸음을 늦췄다가 그냥 간다'},
 {'id': 'FUN-S021', 'soul': 'S-021', 'name': '주모 끝순 장례', 'house': '주막',
  'memory': '역병 돈다고 떠든 사람은 곤장을 맞았지. 그래서 다들 고뿔이라고만 했어.',
  'stopped': '주막 평상 위에 막걸리 사발들이 모두 엎어져 있다. 기둥에 "고뿔 조심" 종이가 붙어 있다',
  'moving': st(25.0, '상여가 떠난 뒤 딸 섭섭이가 주막 기둥의 "고뿔 조심" 종이를 떼어 낸다. 접지 않고 화로에 넣는다. 사발 하나를 바로 세운다',
               cap='[종이 뜯는 소리]', req=['cut.paper.tear(기둥에서 종이 떼는 소리)'],
               cam={'mode': 'low_move', 'to': 'pillar'}, control='walk',
               note='깊은 박자 ②. 기억 색(탁주 흰빛)이 한 번 번졌다 사라진다. 기둥 글씨는 소품이라 대사 0 원칙에 걸리지 않는다'),
  'variant': st(31.0, '(서 의원을 천도한 뒤라면) 떼어 낸 자리에 역병으로 죽은 이들의 이름을 적은 방(榜)이 붙어 있다. 섭섭이가 그 앞에 잠깐 선다',
                cap='[바람에 종이 떨리는 소리]', control='walk', cond='B-03 천도함',
                note='FUNERAL-SEQUENCE §4-2. 이름은 읽히지 않을 만큼 작게(글자를 화면 주제로 쓰지 않는다)'),
  'pending_act': '주막은 문을 열었는데 평상의 사발은 엎어진 그대로다. 섭섭이가 사발 하나를 세우려다 도로 엎는다'},
 {'id': 'FUN-S029', 'soul': 'S-029', 'name': '북잡이 덕수 장례', 'house': '덕수네',
  'memory': '장날 북을 쳤다. 요즘은 북을 쳐도 사람이 덜 모인다.',
  'stopped': '장터 한복판 기둥에 북이 걸려 있다. 북채 하나가 북 테에 걸쳐진 채다. 아무도 치지 않는다',
  'moving': st(25.0, '상여가 장터를 지나자 장사꾼들이 하던 일을 하나씩 멈추고 길가로 나와 선다. 저울을 내려놓고, 국자를 걸어 두고. 북 없이도 길 양쪽이 사람으로 찬다',
               cap='[장터 소리가 한 집씩 멎는다]', req=['amb.market(장터 웅성거림이 한 집씩 멎는 버전)'],
               cam={'mode': 'tilt_up', 'to': 'crowd_wide'}, control='walk',
               note='깊은 박자 ②: "북을 쳐도 사람이 덜 모인다"던 장터에 사람이 모인다. 기억 색(소가죽 갈색)이 한 번 번졌다 사라진다'),
  'pending_act': '북은 걸린 그대로다. 장꾼 하나가 북채를 집어 들었다가 치지 않고 도로 걸어 둔다'},
]

def build(f):
    r = f.get('region', 2)
    proc = procession(r, f.get('proc'))
    if f.get('proc_sound'):  # 상여가 아닌 행렬(칠복의 문짝 들것)은 소리도 다르다
        proc['caption'], proc['sfx'], proc['sfx_request'] = f['proc_sound']
        if not proc['sfx']: del proc['sfx']
    tendo_steps = opening(r, f['house'], f['stopped']) + [proc, f['moving']]
    if f.get('variant'):
        tendo_steps.append(f['variant'])
    tendo_steps += closing(r)
    if f.get('sajabap'):  # 집안 형편에 따라 사잣밥이 다르다(소설과 같게)
        tendo_steps[-2]['action'] = tendo_steps[-2]['action'].replace('밥 세 그릇, 짚신 세 켤레, 엽전 몇 닢', f['sajabap'])
        tendo_steps[-2]['caption'], tendo_steps[-2]['sfx'] = '[바람] [멀리서 놋그릇 한 번]', []
        del tendo_steps[-2]['sfx']
    if f.get('away'):
        tendo_steps[-2]['action'] = tendo_steps[-2]['action'].replace(SCENE[r]['away'], f['away'])
    out = {
        'id': f['id'], 'soul': f['soul'], 'name': f['name'], 'region': r,
        'when': '그 혼을 처결한 다음 낮, 그 집 앞에 처음 다가갈 때',
        'memory_link': f['memory'],
        'branches': [
            {'branch': '천도', 'id': f['id'] + '-TENDO', 'duration': 48.0, 'skippable': True, 'clock': 'running', 'reward': None, 'steps': tendo_steps},
            dict(pahon(r, f['house']), id=f['id'] + '-PAHON'),
            dict(pending(r, f['house'], f['pending_act']), id=f['id'] + '-PENDING'),
        ]}
    for b in out['branches']:
        promote(b)
    return out

data = {
    '_설명': '1막 장례 8개(① 솔고개 4 + ② 검은여울 장터 4). tools/funerals_act1.py로 생성. 서사 2026-10-25. 기본형(박돌쇠)은 first_session_scripts.json',
    'rules': {
        'dialogue': '대사·자막·내레이션 0. 처결 못 함 갈래도 대사 없음(박돌쇠 아내 한 줄은 첫 장례만의 예외)',
        'length': '천도 48초. 7박자 전부는 첫 장례에만, 여기서는 멈춘 사물(t=5)과 다시 움직이는 사물(t=25) 두 박자만 깊게',
        'one_per_day': '하루에 장례 한 번. 하룻밤에 장례 대상 둘 이상 천도했으면 먼저 천도한 혼만, 나머지 집은 조등만(FUNERAL-SEQUENCE §1)',
        'cold': '산 사람이 춥다고 하거나 몸을 움츠리는 연출 없음(지나가는 차사의 한기는 당할미만 느낀다)',
        'condition': 'condition이 붙은 박자는 그 조건일 때만 쓰고, 아니면 건너뛴다(시간은 비워 둔 채 다음 박자로)',
        'sfx': 'sfx = 사운드팀에 있는 소리 id, sfx_request = 아직 없는 소리(요청), caption = 소리 자막(청각 보조 설정에서만)',
        'names': '갑술 영감(N-105), 윤 소사네 아들(N-103), 꼭지·차돌이(N-204), 섭섭이(N-203)는 npc_act1.json과 같은 사람. 서당 아이들·이웃 아낙은 이름 없이',
    },
    'funerals': [build(f) for f in FUNERALS],
}
if __name__ == '__main__':  # 2막 생성기(funerals_act2.py)가 이 파일의 틀을 가져다 쓴다. 가져갈 때는 파일을 쓰지 않는다
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(data['funerals']), 'funerals')
