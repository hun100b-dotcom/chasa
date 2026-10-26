# 1막 보스 B-02 월화 · B-03 서 의원 실시간 컷신 대본 생성기
# 형식은 cutscenes_b01.json(나루 영감)과 같다: 등장 · 처결 대기 · 천도 불가 안내 · 천도 · 파혼.
# 원칙: 짧게, 주인공 대사 0줄, 설명하지 않고 보여 준다. 보스 대사는 3줄 이하.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_map import apply as sfx_apply  # 효과음 이름표 붙이기
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'docs', 'narrative')
mem = {s['id']: s for s in json.load(open(os.path.join(D, 'soul_memories.json'), encoding='utf-8'))['souls']}

def st(t, cam=None, act=None, line=None, ui=None, note=None):
    s = {'t': t}
    if cam: s['camera'] = cam
    if act: s['action'] = act
    if line: s['line'] = line
    if ui: s['ui'] = ui
    if note: s['note'] = note
    return s

def say(text, speaker, style='bubble', dur=2.0):
    return {'speaker': speaker, 'text': text, 'style': style, 'duration': dur}

RULES = {
 'protagonist_lines': 0,
 'time': 't는 컷 시작부터 초. duration 안에서 끝난다',
 'camera': 'pan·push·pull·hold·cut·shake·return. zoom 1.0 = 평소 쿼터뷰 거리',
 'world': 'pause_enemies = 적 멈춤(입력 잠금 컷만) / run = 전투 계속',
 'line_style': 'bubble 말풍선 · memory 기억 줄(시야 가장자리 기억 색)', 'sfx': 'sfx = 그 스텝 시각에 재생할 효과음 id(사운드팀 data/sfx_files.json, 루프는 amb.*). sfx_request = 아직 없는 소리(사운드팀 요청)',
 'skippable': '길게 눌러 건너뛰기. 건너뛰어도 보상·단서·세계 변화는 그대로',
 'format': 'cutscenes_b01.json과 같은 형식'}

def noclue(bid, what):
    return {'id': f'{bid}-NOCLUE', 'branch': '처결 대기(천도 불가)', 'trigger': '단서 2개 이하에서 천도 입력',
            'duration': 1.0, 'input_lock': False, 'world': 'run', 'skippable': False,
            'steps': [st(0.0, act=what, ui={'toast': '이름이 들리지 않는다', 'toast_time': 1.0}, note='안내일 뿐. 캐스팅은 시작되지 않고 대기 시간은 계속 흐른다')]}

# ───────── B-02 월화 (① 폐당집 굿판) ─────────
W = 'B-02'
b02 = [
 {'id': 'B02-INTRO', 'branch': '등장', 'trigger': '폐당집 굿판에 처음 들어설 때(한 번만)', 'duration': 5.0, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True,
  'steps': [
   st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15}, act='둥근 굿판. 가장자리에 잔 열두 개가 둘러 놓여 있다. 열두째 잔만 엎어져 있다'),
   st(1.4, act='굿상 앞, 오방색 쾌자를 입은 늙은 무당이 등을 보이고 서 있다. 한 손에 살 부러진 부채, 한 손에 방울'),
   st(2.0, act='방울이 한 번 울린다. 첫째 잔 앞 바닥이 붉게 열린다', line=say('첫째 거리부터 다시 하자.', W, dur=1.6)),
   st(3.6, act='월화가 엎어진 열두째 잔 쪽으로 고개를 돌리다 멈춘다', line=say('…열두째는 누구 몫이었더라.', W, dur=1.4)),
   st(5.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '월화', 'seal_icon': 'faded'}, note='전투 ① 열두 거리 시작. 엎어진 열두째 잔 칸은 늘 안전')]},
 {'id': 'B02-KNEEL', 'branch': '처결 대기', 'trigger': '보스 맺힘 0', 'duration': 1.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '처결 대기 7초와 동시에 흐른다. 입력을 막지 않는다',
  'steps': [
   st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.25}, act='월화가 굿판 한가운데 주저앉는다. 방울이 손에서 굴러 나간다. 부채는 놓지 않는다'),
   st(0.3, line=say('잔이… 하나 모자라.', W, dur=1.5)),
   st(0.4, ui={'kneel_timer': 7.0, 'seal_over_boss': 'clue>=3 ? steady : flicker'}),
   st(1.5, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3, 'zoom': 1.0})]},
 noclue('B02', '월화 머리 위 명부 인이 흐릿하게 떨리다 꺼진다. 방울 소리 없이'),
 {'id': 'B02-TENDO', 'branch': '천도', 'trigger': '천도 캐스팅 2.0초 완료', 'duration': 7.5, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True,
  'note': '남은 잡몹은 굿판 바깥 어둠으로 물러나 사라진다',
  'steps': [
   st(0.0, cam={'mode': 'hold', 'zoom': 1.3, 'vignette': 0.6, 'vignette_color': mem[W]['tint']}, act='명부가 펼쳐지고 흐렸던 인이 또렷해진다', ui={'ledger_name': '월화', 'ledger_fx': 'strokes_join'}),
   st(1.0, line=say(mem[W]['memory'], W, 'memory', 3.4), note='기억 M-B02(★F12 전모). 시야 가장자리에 기억 색'),
   st(1.5, act='월화가 일어나 엎어진 열두째 잔을 두 손으로 세운다. 잔 열두 개가 모두 바로 놓인다'),
   st(3.0, act='월화가 바로 선 열두째 잔 위에 손을 한 번 얹었다가 거둔다. 플레이어 쪽은 끝내 보지 않는다', note='대사 없음. 10-26 서사: 잔을 플레이어 쪽으로 내미는 손짓은 1막에서 F9를 너무 가리켜 뺌(소설 13장과 맞춤 — 월화는 끝까지 그를 보지 않는다). 카메라는 그녀와 잔만'),
   st(4.5, cam={'mode': 'pull', 'zoom': 0.9, 'time': 1.5, 'vignette': 0.0}, act='월화가 부채를 접어 열두째 잔 곁에 놓고, 오방 천 빛으로 흩어진다'),
   st(6.0, act='폐당집 처마 밑에 등 하나가 켜진다(두 번째 쉼터)'),
   st(7.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'fact_on': 'F12', 'reward': {'neok': 50, 'memory': 'M-B02'}, 'world_change': '폐당집 두 번째 쉼터 · 쉼터 둘레 40 m 혼은 처결 대기 +2초(굿을 끝낸 자리)', 'item_spawn': '옥이의 신칼(굿상 머리)'})]},
 {'id': 'B02-PAHON', 'branch': '파혼', 'trigger': '처결 대기 중 파혼 입력', 'duration': 2.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '즉시. 폭발로 화면의 잡몹이 밀려나 안전',
  'steps': [
   st(0.0, cam={'mode': 'shake', 'strength': 'big', 'time': 0.5}, act='대폭발. 굿판의 잔 열두 개가 한꺼번에 엎어진다'),
   st(0.3, ui={'ledger_name': '월화', 'ledger_fx': 'strokes_scatter'}, act='명부의 "월화" 획이 흩어진다'),
   st(0.8, act='붉은 천과 오방 천 조각이 흩날린다. 방울 하나만 굿판 위로 굴러 와 멈춘다(월화의 방울)'),
   st(1.5, act='굿판 바닥에 얼룩이 둥지처럼 번진다', note='대사 없음'),
   st(2.5, ui={'reward': {'coin': 30, 'item': '월화의 방울(파혼 반경 +0.5m, 얼룩 위 천도 −0.3초)'}, 'karma': '+3', 'karma_warning': '업 단계 경계를 넘으면 화면 경고', 'world_change': '폐당집 얼룩 둥지', 'next_day': '얼룩 둥지에서 밤마다 거센 혼 하나', 'closeup': '굴러온 방울(마지막 0.5초)', 'item_spawn': '옥이의 신칼(굿상 머리)'})]},
]

# ───────── B-03 서 의원 (② 역병막) ─────────
S = 'B-03'
b03 = [
 {'id': 'B03-INTRO', 'branch': '등장', 'trigger': '역병막 의원 움막 앞 마당에 처음 들어설 때(한 번만)', 'duration': 5.0, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True,
  'steps': [
   st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15}, act='거적 움막 두 줄 끝, 널판 움막 앞 마당. 바닥에 다섯 줄 다섯 칸의 흐린 선'),
   st(1.4, act='기운 탕건을 쓴 마른 의원. 등에 작은 약장(석 단 두 칸)을 붉은 띠로 졌다. 손끝이 먹과 약물로 갈색'),
   st(2.0, act='의원이 기침한다. 약장 맨 아랫단 왼쪽 서랍이 조금 밀려 나왔다가 들어간다', note='약점 예고(낙인 세 번 피하면 이 서랍이 빛난다)'),
   st(2.6, act='바닥 칸 하나가 붉게 깜빡인다', line=say('번호만 불러라. 이름은 적지 마라.', S, dur=1.8), note='사또의 명을 되풀이하는 말'),
   st(5.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '서 의원', 'seal_icon': 'missing'}, note='전투 ① 번호 부르기 시작. 명부에 이름은 또렷하고 인 자리만 비어 있다')]},
 {'id': 'B03-KNEEL', 'branch': '처결 대기', 'trigger': '보스 맺힘 0', 'duration': 1.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '처결 대기 7초와 동시에 흐른다. 입력을 막지 않는다',
  'steps': [
   st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.25}, act='의원이 약장을 내려놓고 무릎 꿇는다. 손바닥을 들여다본다'),
   st(0.3, line=say('다 지웠소. 하나도… 못 지웠소.', S, dur=1.6)),
   st(0.4, ui={'kneel_timer': 7.0, 'seal_over_boss': 'clue>=3 ? steady : flicker'}),
   st(1.5, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3, 'zoom': 1.0})]},
 noclue('B03', '의원 머리 위 명부의 빈 인 자리가 떨리다 그대로 빈다'),
 {'id': 'B03-TENDO', 'branch': '천도', 'trigger': '천도 캐스팅 2.0초 완료', 'duration': 7.5, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True,
  'note': '남은 잡몹(역병막 혼)은 거적 움막 안으로 돌아가 눕는다',
  'steps': [
   st(0.0, cam={'mode': 'hold', 'zoom': 1.3, 'vignette': 0.6, 'vignette_color': mem[S]['tint']}, act='명부의 "서인보" 줄, 비어 있던 인 자리에 붉은 인이 천천히 앉는다', ui={'ledger_name': '서인보', 'ledger_fx': 'seal_appear'}),
   st(1.0, line=say(mem[S]['memory'], S, 'memory', 3.2), note='기억 M-B03(★F10 전모)'),
   st(1.5, act='의원이 약장 맨 아랫단 서랍을 연다. 감초 위에 희게 마른 붓 한 자루를 가만히 뉜다(씻은 붓)'),
   st(3.5, cam={'mode': 'pull', 'zoom': 0.9, 'time': 1.0, 'vignette': 0.0}, act='명부가 저절로 넘어간다. 검은여울 장마다 인 빈 줄들에 흐린 인이 배어 나온다', ui={'ledger_fx': 'region2_seal_missing_to_faded'}),
   st(5.0, act='의원이 탕건을 고쳐 쓰고, 거적 움막 줄을 한 번 돌아본 뒤 약탕 빛으로 흩어진다', note='대사 없음'),
   st(6.5, cam={'mode': 'cut', 'to': 'market_square', 'time': 0.0, 'hold': 0.6}, act='먼 장터 쪽, 주막 기둥에 등 하나'),
   st(7.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'fact_on': 'F10', 'reward': {'neok': 50, 'memory': 'M-B03'}, 'world_change': '검은여울 이름혼 인 없음 → 흐림(+0.5 → +0.25초) · 검은여울 이름혼 천도 넋 ×1.15 · 장터 장례 장면 추가', 'item_spawn': '씻은 붓(약장 맨 아랫단)'})]},
 {'id': 'B03-PAHON', 'branch': '파혼', 'trigger': '처결 대기 중 파혼 입력', 'duration': 2.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '즉시. 폭발로 화면의 잡몹이 밀려나 안전',
  'steps': [
   st(0.0, cam={'mode': 'shake', 'strength': 'big', 'time': 0.5}, act='대폭발. 약장이 터진다. 약봉지와 감초 조각이 흩날린다'),
   st(0.3, ui={'ledger_name': '서인보', 'ledger_fx': 'strokes_scatter'}, act='명부의 "서인보" 획이 흩어진다. 인 자리는 끝내 비어 있다'),
   st(0.8, act='회복약 다섯 병이 마당에 구른다. 희게 마른 붓 한 자루가 감초 더미 위에 떨어진다'),
   st(1.5, act='번호 칸 바닥의 붉은 선만 잠깐 남았다가 꺼진다', note='대사 없음'),
   st(2.5, ui={'reward': {'coin': 30, 'potion': 5}, 'karma': '+3', 'karma_warning': '업 단계 경계를 넘으면 화면 경고', 'world_change': '검은여울 이름혼은 끝까지 인 없음', 'next_day': '역병막 터에 깨진 약장. 둘레에 쑥 줍기 3이 날마다 난다', 'closeup': '흩어진 약재 위의 씻은 붓(마지막 0.5초)', 'item_spawn': '씻은 붓(약장 터진 자리)'})]},
]

b02 = [sfx_apply(c) for c in b02]
b03 = [sfx_apply(c) for c in b03]

for bid, name, ledger, zone, tint, cuts, lines in [
    ('B-02', '월화', '월화', 'Shrine', mem['B-02']['tint'], b02, '월화 대사 3줄(등장 2 · 처결 대기 1) + 천도 기억 한 줄'),
    ('B-03', '서 의원', '서인보', 'Plague', mem['B-03']['tint'], b03, '의원 대사 2줄(등장 1 · 처결 대기 1) + 천도 기억 한 줄')]:
    data = {'_설명': f'{bid} {name} 실시간 컷신 4갈래 + 천도 불가 안내. tools/cutscenes_act1.py로 생성. 근거: SCENARIO-ACT1 §6, 기획 부록 E, soul_memories.json. 서사 확정 2026-10-25.',
            'boss': {'id': bid, 'name': name, 'ledger_name': ledger, 'zone': zone, 'tint': tint},
            'rules': dict(RULES, lines_total=lines + '. 파혼에는 대사가 없다'), 'cutscenes': cuts}
    fn = os.path.join(D, f'cutscenes_{bid.lower().replace("-", "")}.json')
    json.dump(data, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(fn, len(cuts))
