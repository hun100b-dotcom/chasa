# 1호 보스 나루 영감(B-01) 실시간 컷신 대본 생성기
# 왜 JSON인가: 코드팀이 타임라인(시간 순서대로 카메라·동작·자막을 재생하는 장치)으로 그대로 읽게 하려고.
# 원칙: 짧게(전투 흐름을 끊지 않게), 주인공 대사 0줄, 설명하지 않고 보여 준다(WORLD-BIBLE §6 대사 톤).
import json, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'narrative', 'cutscenes_b01.json')

def st(t, cam=None, act=None, line=None, ui=None, note=None):
    s = {'t': t}
    if cam: s['camera'] = cam
    if act: s['action'] = act
    if line: s['line'] = line
    if ui: s['ui'] = ui
    if note: s['note'] = note
    return s

def say(text, speaker='B-01', style='bubble', dur=2.0):
    # bubble = 인물 머리 위 말풍선 자막 / caption = 화면 아래 자막 / memory = 기억 한 줄(시야 가장자리 기억 색)
    return {'speaker': speaker, 'text': text, 'style': style, 'duration': dur}

cutscenes = [
 {'id': 'B01-INTRO', 'branch': '등장', 'trigger': '물막이 골 옛 나루터 보스 구역에 처음 들어설 때(한 번만)',
  'duration': 4.5, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True,
  'steps': [
   st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss_boat', 'time': 1.2, 'zoom': 1.15}, act='물안개가 깔린다. 무너진 징검다리 옆, 반쯤 가라앉은 나룻배'),
   st(1.2, act='삿갓 쓴 영감이 부러진 삿대로 물을 짚는다. 허리에 엽전 꾸러미 자국만 남은 빈 끈'),
   st(1.6, line=say('배 떠나오.', dur=1.4)),
   st(3.0, act='영감이 강물을 내려다본다. 물에서 손 둘이 올라와 뱃전을 잡는다(물에 빠진 혼 2마리 등장)', line=say('…한 사람만 더.', dur=1.5)),
   st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '나루 영감', 'seal_icon': 'faded'}, note='전투 ① 물안개 시작')]},

 {'id': 'B01-KNEEL', 'branch': '처결 대기', 'trigger': '보스 맺힘 0',
  'duration': 1.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '처결 대기 7초는 이 컷과 동시에 흐른다. 입력을 막지 않는다(물에 빠진 혼은 계속 올라온다)',
  'steps': [
   st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.25}, act='영감이 배 위에서 무릎 꿇는다. 삿대가 손에서 미끄러져 물에 뜬다'),
   st(0.3, act='영감이 강 건너 쪽으로 고개를 돌린다', line=say('아직… 못 건넸소.', dur=1.6)),
   st(0.4, ui={'kneel_timer': 7.0, 'seal_over_boss': 'clue>=3 ? steady : flicker'}),
   st(1.5, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3, 'zoom': 1.0})]},

 {'id': 'B01-NOCLUE', 'branch': '처결 대기(천도 불가)', 'trigger': '단서 2개 이하에서 천도 입력',
  'duration': 1.0, 'input_lock': False, 'world': 'run', 'skippable': False,
  'steps': [
   st(0.0, act='영감 머리 위 명부 인이 흐릿하게 떨리다 꺼진다', ui={'toast': '이름이 들리지 않는다.', 'toast_time': 1.0}, note='실패 연출이 아니라 안내(BOSS-01 §6). 캐스팅은 시작되지 않는다. 대기 시간은 계속 흐른다')]},

 {'id': 'B01-TENDO', 'branch': '천도', 'trigger': '천도 캐스팅 2.0초 완료',
  'duration': 7.0, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True,
  'note': '캐스팅(2.0초, 시야 60%, 시작 후 2초 잡몹 스폰 정지)은 전투 안에서 일어난다. 이 컷은 캐스팅이 끝난 뒤부터. 잡몹은 남은 것도 물안개 속으로 가라앉아 사라진다',
  'steps': [
   st(0.0, cam={'mode': 'hold', 'zoom': 1.3, 'vignette': 0.6, 'vignette_color': '나룻불 주황'}, act='명부가 펼쳐지고 붓 획이 이어진다. 흐렸던 인이 또렷해진다', ui={'ledger_name': '도한수', 'ledger_fx': 'strokes_join'}),
   st(1.0, line=say('나루에 검은 갓이 서 있었다. 물에서 건져 낸 혼을 하나씩 깨뜨리고 있었다. 울면서.', speaker='B-01', style='memory', dur=3.0), note='기억 M-B01(★F4 전모). 시야 가장자리에 기억 색'),
   st(1.5, act='영감이 삿대를 물에서 건져 노 자리에 내려놓는다. 빈 허리끈에 엽전 다섯 닢이 다시 매달린다(D-1의 엽전)'),
   st(3.5, cam={'mode': 'pull', 'zoom': 0.9, 'time': 1.5, 'vignette': 0.0}, act='배가 물 위로 떠오른다. 물안개가 걷힌다. 배가 강 건너로 천천히 간다'),
   st(4.5, act='배 위의 영감이 이쪽을 한 번 돌아본다. 삿갓을 조금 숙인다', line=None, note='대사 없음. 고개 숙임이 인사다'),
   st(5.5, cam={'mode': 'cut', 'to': 'far_sky_over_hub', 'time': 0.0, 'hold': 1.0}, act='먼 하늘. 서낭당 쪽 저편에 나룻불 하나가 켜진다'),
   st(6.5, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'fact_on': 'F4', 'reward': {'neok': 5, 'memory': 'M-B01'}, 'world_change': '물막이 골 나루 열림 — 귀환 −17.5%'})]},

 {'id': 'B01-PAHON', 'branch': '파혼', 'trigger': '처결 대기 중 파혼 입력',
  'duration': 2.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '즉시 일어난다. 반경 6m 대폭발로 화면의 잡몹이 날아가므로 입력을 막지 않아도 안전',
  'steps': [
   st(0.0, cam={'mode': 'shake', 'strength': 'big', 'time': 0.5}, act='반경 6m 대폭발. 배가 터져 판자가 흩어진다'),
   st(0.3, ui={'ledger_name': '도한수', 'ledger_fx': 'strokes_scatter'}, act='명부의 "도한수" 획이 하나씩 흩어진다. 마지막 획까지'),
   st(0.8, act='엽전이 물 위로 쏟아진다(엽전 ×30). 빈 허리끈 하나가 떠내려간다'),
   st(1.5, act='물 위의 얼룩이 천천히 하류로 번진다(큰 얼룩 지대)', note='대사 없음. 소리도 없이 물소리만'),
   st(2.5, ui={'reward': {'coin': 30}, 'karma': '+3', 'karma_warning': '업 단계 경계를 넘으면 화면 경고', 'world_change': '물막이 골 큰 얼룩 지대(덩어리 +10%p)'})]},
]

data = {
 '_설명': '1호 보스 나루 영감(B-01) 실시간 컷신 4갈래 + 천도 불가 안내. tools/cutscenes_b01.py로 생성. 근거: BOSS-01-NARU.md, soul_memories.json B-01. 서사 확정 2026-10-25.',
 'boss': {'id': 'B-01', 'name': '나루 영감', 'ledger_name': '도한수', 'zone': 'Ravine', 'tint': '나룻불 주황'},
 'rules': {
  'protagonist_lines': 0,
  'lines_total': '영감 대사 3줄(등장 2 · 처결 대기 1) + 천도 때 기억 한 줄. 파혼에는 대사가 없다',
  'time': 't는 컷 시작부터 초. duration 안에서 끝난다',
  'camera': 'pan(옮기기)·push(다가가기)·pull(물러나기)·hold(멈춤)·cut(장면 바꾸기)·shake(흔들기)·return(플레이어로 돌아오기). zoom 1.0 = 평소 쿼터뷰 거리',
  'world': 'pause_enemies = 적 멈춤(입력 잠금 컷만) / run = 전투 계속',
  'line_style': 'bubble 말풍선 · memory 기억 줄(시야 가장자리 기억 색, 화면 아래 가운데) · 소리는 아직 없음',
  'skippable': '길게 눌러 건너뛰기. 건너뛰어도 보상·단서·세계 변화는 그대로'},
 'cutscenes': cutscenes}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(cutscenes), 'cutscenes')
