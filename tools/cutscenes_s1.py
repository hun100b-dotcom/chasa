# -*- coding: utf-8 -*-
# 시즌 1 실시간 컷신 대본 — 2막 보스 넷(B-05~08), 3막 보스 셋(B-09~11), 흑월 2차(B-12) 결전 컷,
#   시즌 1 끝 C-12A(천도) · C-12B(파혼) · 공통 새벽 C-13.
# 형식은 1막(cutscenes_b01·b02·b03.json)과 같다: 등장 · 처결 대기 · 천도 불가 안내 · 천도 · 파혼.
# 원칙(1막과 같음):
#   - 주인공 대사 0. 2·3막 보스는 말하지 않는다(SCENARIO-ACT2·3 대사 집계 — 3막은 흑월 1줄만). 예외는 B-07의 마지막 셈 한 마디.
#   - 설명하지 않고 보여 준다. 숫자·별명·F9 내용은 화면 글로 쓰지 않는다.
#   - 카메라는 "구도(framing) · 움직임(mode) · 박자(t·time)" 세 가지로 지시한다. 긴 컷(C-12A/B·C-13)은 박자마다 beat 이름을 단다.
# 실행: python3 tools/cutscenes_s1.py → docs/narrative/cutscenes_s1.json
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_map import promote
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'docs', 'narrative')
mem = {s['id']: s for s in json.load(open(os.path.join(D, 'soul_memories.json'), encoding='utf-8'))['souls']}
BC = {}
for f in ('boss_clues_act2.json', 'boss_clues_act3.json'):
    BC.update(json.load(open(os.path.join(D, f), encoding='utf-8'))['boss_clues'])

def st(t, cam=None, act=None, line=None, ui=None, note=None, sfx=None, req=None, cond=None, beat=None, variant=None):
    s = {'t': t}
    if beat: s['beat'] = beat
    if cam: s['camera'] = cam
    if act: s['action'] = act
    if line: s['line'] = line
    if ui: s['ui'] = ui
    if sfx: s['sfx'] = sfx
    if req: s['sfx_request'] = req
    if cond: s['condition'] = cond      # 이 조건일 때만 이 박자를 쓴다(아니면 건너뜀)
    if variant: s['variant'] = variant  # A판/B판에 따라 다른 카메라·동작
    if note: s['note'] = note
    return s

def say(text, speaker, style='bubble', dur=2.0):
    return {'speaker': speaker, 'text': text, 'style': style, 'duration': dur}

def intro(bid, trigger, steps, dur):
    return {'id': f"{bid.replace('-', '')}-INTRO", 'branch': '등장', 'trigger': trigger, 'duration': dur, 'input_lock': True,
            'world': 'pause_enemies', 'skippable': True, 'steps': steps}

def kneel(bid, act, extra=None):
    steps = [st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.25}, act=act, sfx=['sfx.kneel'])]
    if extra: steps.append(extra)
    steps += [st(0.4, ui={'kneel_timer': 7.0, 'seal_over_boss': 'clue>=3 ? steady : flicker'}),
              st(1.5, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3, 'zoom': 1.0})]
    return {'id': f"{bid.replace('-', '')}-KNEEL", 'branch': '처결 대기', 'trigger': '보스 맺힘 0', 'duration': 1.5, 'input_lock': False,
            'world': 'run', 'skippable': False, 'note': '처결 대기 7초와 동시에 흐른다. 입력을 막지 않는다. 대사 없음', 'steps': steps}

def noclue(bid, act):
    return {'id': f"{bid.replace('-', '')}-NOCLUE", 'branch': '처결 대기(천도 불가)', 'trigger': '단서 2개 이하에서 천도 입력', 'duration': 1.0,
            'input_lock': False, 'world': 'run', 'skippable': False,
            'steps': [st(0.0, act=act, ui={'toast': '이름이 들리지 않는다.', 'toast_time': 1.0}, sfx=['cut.seal.fade'],
                         note='안내일 뿐. 캐스팅은 시작되지 않고 대기 시간은 계속 흐른다')]}

def tendo(bid, ledger, beats, reward, dur=7.5, note=None, first=None, mem_t=1.0):
    b = BC[bid]
    head = [st(0.0, cam={'mode': 'hold', 'zoom': 1.3, 'vignette': 0.6, 'vignette_color': mem[bid].get('tint')},
               act=first or '명부가 펼쳐지고 흐렸던 인이 또렷해진다',
               ui={'ledger_name': ledger, 'ledger_fx': 'strokes_join' if ledger else 'seal_only'},
               sfx=['cut.ledger.open', 'cut.brush.stroke', 'cut.seal.set'],
               note=None if ledger else '명부 그 줄엔 이름이 없다. 인만 앉는다(이름은 끝내 모른다)'),
            st(mem_t, line=say(mem[bid]['memory'], bid, 'memory', 3.4), sfx=['sfx.clue'], note=f"기억 M-{bid.replace('-', '')}(★{b['decisive']} 전모)")]
    last = st(dur, cam={'mode': 'return', 'to': 'player', 'time': 0.5},
              ui=dict({'fact_on': b['decisive'], 'reward': {'memory': 'M-' + bid.replace('-', '')}, 'world_change': b['tendo']}, **(reward or {})))
    c = {'id': f"{bid.replace('-', '')}-TENDO", 'branch': '천도', 'trigger': '천도 캐스팅 2.0초 완료', 'duration': dur, 'input_lock': True,
         'world': 'pause_enemies', 'skippable': True, 'steps': head + beats + [last]}
    if note: c['note'] = note
    return c

def pahon(bid, ledger, beats, reward_item):
    steps = [st(0.0, cam={'mode': 'shake', 'strength': 'big', 'time': 0.5}, act=beats[0], sfx=['sfx.pahon.burst']),
             st(0.3, ui={'ledger_name': ledger, 'ledger_fx': 'strokes_scatter'} if ledger else {'ledger_fx': 'seal_shatter'},
                act='명부의 그 줄이 흩어진다', sfx=['cut.stroke.scatter'])]
    steps += [st(0.8 + 0.7 * i, act=a) for i, a in enumerate(beats[1:])]
    steps.append(st(2.5, ui={'reward': {'item': reward_item}, 'karma': '+3', 'karma_warning': '업 단계 경계를 넘으면 화면 경고',
                             'world_change': BC[bid]['pahon']}, note='대사 없음'))
    return {'id': f"{bid.replace('-', '')}-PAHON", 'branch': '파혼', 'trigger': '처결 대기 중 파혼 입력', 'duration': 2.5, 'input_lock': False,
            'world': 'run', 'skippable': False, 'note': '즉시. 폭발로 화면의 잡몹이 밀려나 안전', 'steps': steps}

CUTS = []

# ═════════ 2막 ═════════
# B-05 기수 대돌 — 무너진 산성 깃대 터
CUTS += [
 intro('B-05', '무너진 산성 깃대 터에 처음 들어설 때(한 번만)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '깃대를 화면 위쪽 3분의 1에'}, act='무너진 성벽 위, 부러진 깃대. 찢어진 깃발을 쥔 손이 깃대를 놓지 않는다', sfx=['amb.field']),
  st(1.4, cam={'mode': 'push', 'to': 'flagpole', 'time': 0.8, 'zoom': 1.3}, act='깃대에 칼금으로 새긴 이름들. 반은 지워졌다', note='글자는 읽히지 않게'),
  st(2.4, cam={'mode': 'pull', 'zoom': 1.1, 'time': 0.6}, act='대돌이 입을 연다. 소리는 들리지 않는다. 그가 입을 열 때마다 땅에서 병사 혼이 하나씩 일어난다', req=['cut.soldier.rise(갑옷 혼이 땅에서 일어나는 소리)']),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '기수 대돌', 'seal_icon': 'faded'}, note='전투: 이름을 잊은 자리는 번호로 부른다(번호 혼이 더 사납다)')], 4.5),
 kneel('B-05', '대돌이 깃대를 땅에 꽂고 무릎 꿇는다. 입술은 계속 움직인다 — 아직 세고 있다'),
 noclue('B-05', '대돌 머리 위 명부 인이 흐릿하게 떨리다 꺼진다. 깃발만 펄럭인다'),
 tendo('B-05', '대돌', [
  st(1.5, act='대돌이 일어나 깃대를 똑바로 세운다. 칼금 이름들에 하나씩 빛이 든다. 지워졌던 자리까지', sfx=['cut.cloth.flutter']),
  st(3.5, cam={'mode': 'cut', 'to': 'big_tomb', 'time': 0.0, 'framing': '봉분을 낮게, 하늘을 크게'}, act='큰 무덤 봉분에 이름들이 새겨진다. 빛이 위에서 아래로 한 줄씩', req=['cut.stone.carve(돌에 글이 새겨지는 낮은 소리)'], note='글자는 읽히지 않게. 수를 세지 않는다'),
  st(5.5, cam={'mode': 'crane', 'dir': 'up', 'time': 1.5}, act='대돌이 깃발과 함께 빛으로 흩어져 봉분 위로 오른다', sfx=['cut.dissolve'])],
  None),
 pahon('B-05', '대돌', ['대폭발. 깃대가 부러져 날아간다', '병사 혼들을 부르던 입 모양이 한꺼번에 멈춘다. 일어났던 혼들이 그대로 주저앉는다', '찢어진 군기 한 폭이 성벽 위에 걸려 펄럭인다'],
       '찢어진 군기(들고 있으면 주변 잡몹 1초 겁먹음)'),
]

# B-06 이름 없는 장수 — 군막 터
CUTS += [
 intro('B-06', '군막 터에 처음 들어설 때(한 번만)', [
  st(0.0, cam={'mode': 'crane', 'dir': 'down', 'from': 'high', 'to': 'boss', 'time': 1.6, 'zoom': 1.1, 'framing': '내려다보는 진법도 — 병사 혼들이 바둑돌처럼'}, act='군막 터 바닥에 찢어진 진법도. 그 위에 병사 혼들이 줄 맞춰 서 있다. 등에 숫자 패'),
  st(1.6, act='한가운데 투구를 깊이 쓴 장수. 얼굴이 보이지 않는다. 북이 한 번 울리자 병사 혼들이 대형을 바꾼다', req=['cut.war.drum(큰 북 한 번)']),
  st(3.0, act='북이 두 번. 대형이 또 바뀐다', note='호령은 말이 아니라 북. 대사 없음'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '이름 없는 장수', 'seal_icon': 'missing'}, note='전투: 북(호령)을 들으면 대형의 빈틈이 보인다')], 4.5),
 kneel('B-06', '장수가 갑주 무릎을 꿇는다. 병사 혼들의 대형이 흩어져 제자리에 선다. 북채가 땅에 떨어진다'),
 noclue('B-06', '장수 머리 위 명부 인 자리가 비어 있다가 꺼진다'),
 tendo('B-06', None, [
  st(1.5, act='장수가 투구를 벗는다(얼굴은 그늘로). 병사 혼 하나하나 앞으로 가서 얼굴을 본다'),
  st(3.0, cam={'mode': 'track', 'to': 'boss', 'time': 2.0, 'zoom': 1.2, 'framing': '장수 어깨 너머로 병사 얼굴'}, act='그가 지나간 병사의 등에서 숫자 패가 떨어진다. 패가 떨어진 혼은 고개를 든다', req=['cut.tag.drop(나무패 떨어지는 소리)']),
  st(5.5, act='병사 혼들이 먼저 흩어져 오른다. 장수는 맨 마지막에 오른다', sfx=['cut.dissolve'])],
  None, first='명부가 펼쳐진다. 그 줄엔 이름이 없다. 인만 천천히 앉는다'),
 pahon('B-06', None, ['대폭발. 진법도가 불티로 찢어진다', '병사 혼들이 숫자 패를 단 채 흩어진다', '빈 갑주 한 벌이 군막 터에 선 채로 남는다'], '장수의 갑주(방어 장비)'),
]

# B-07 갱도 반장 칠성 — 무너진 막장
CUTS += [
 intro('B-07', '무너진 막장에 처음 들어설 때(한 번만)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.2, 'framing': '낮은 천장, 등잔 하나가 유일한 빛'}, act='무너진 막장. 등잔 하나. 광부 혼들이 줄지어 출구 쪽으로 걸어간다', sfx=['amb.mine']),
  st(1.4, act='줄 끝에 선 반장이 손가락을 하나씩 접으며 센다. 입 모양만', note='숫자를 화면 글로 쓰지 않는다'),
  st(3.0, act='반장의 손가락이 멈춘다. 다시 처음부터 접는다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '갱도 반장 칠성', 'seal_icon': 'faded'}, note='전투: 광부 혼을 파혼하면 셈이 틀려 반장이 맺힘을 회복한다')], 4.5),
 kneel('B-07', '반장이 무릎 꿇는다. 접은 손가락을 펴지 못한다. 등잔이 흔들린다'),
 noclue('B-07', '반장 머리 위 명부 인이 흐릿하게 떨리다 꺼진다. 등잔불만 깜빡인다'),
 tendo('B-07', '칠성', [
  st(0.4, cam={'mode': 'push', 'to': 'boss_hand', 'time': 0.6, 'zoom': 1.5}, act='반장이 마지막 손가락을 접어 제 가슴에 댄다'),
  st(1.0, line=say('…열셋. 그리고 — 칠성.', 'B-07', 'bubble', 2.0), note='2막 보스가 하는 유일한 말(SCENARIO-ACT2 B-07). 원안은 캐스팅 중이나, 캐스팅은 시야 60% 전투 안이라 대사가 묻힌다 → 천도 컷 첫머리로 옮김'),
  st(5.0, cam={'mode': 'cut', 'to': 'shortcut_mouth', 'time': 0.0, 'framing': '갱도 끝에 빛 한 점'}, act='막장 옆 막혔던 갱도 끝이 열린다. 바람이 들어온다. 바다 냄새 — 화면 가장자리 물빛이 한 번 스친다', req=['amb.sea.wind(먼 바닷바람)']),
  st(6.8, act='반장이 맨 마지막으로 출구를 나서며 빛으로 흩어진다', sfx=['cut.dissolve'])],
  None, dur=8.0, mem_t=3.2),
 pahon('B-07', '칠성', ['대폭발. 천장 돌이 쏟아진다', '출구로 걷던 광부 혼들이 멈춰 선다. 셈이 끊겼다', '무너진 돌 사이로 광석 무더기가 드러난다'], '광석 대량(제작 재료)'),
]

# B-08 장부꾼 염씨 — 광산 주인집
CUTS += [
 intro('B-08', '광산 주인집(광부촌 위)에 처음 들어설 때(한 번만)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '마루 위 장부 상, 등 뒤로 광부촌 지붕들'}, act='주인집 마루. 장부를 펴 든 사내가 앉아 있다. 붓을 쥔 손이 쉬지 않는다', sfx=['cut.brush.write']),
  st(1.6, act='장부에서 숫자 적힌 종이가 한 장씩 뜯겨 마당으로 날아가 바닥에 박힌다', sfx=['cut.paper.tear']),
  st(3.2, act='뒷장 한 장이 펄럭이다 도로 접힌다', note='뒷장 글씨는 보이지 않는다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '장부꾼 염씨', 'seal_icon': 'faded'}, note='전투: 숫자 종이는 밟으면 피해, 이름 적힌 뒷장은 무해')], 4.5),
 kneel('B-08', '염씨가 장부를 품에 안고 무릎 꿇는다. 앞장은 접고 뒷장을 가슴 쪽으로'),
 noclue('B-08', '염씨 머리 위 명부 인이 흐릿하게 떨리다 꺼진다. 장부는 닫힌 채'),
 tendo('B-08', '염씨', [
  st(1.5, cam={'mode': 'push', 'to': 'ledger_book', 'time': 0.8, 'zoom': 1.5, 'framing': '장부를 위에서'}, act='장부 뒷장이 처음으로 넘어간다. 빼곡한 이름들(읽히지 않게)', sfx=['cut.ledger.open']),
  st(3.0, cam={'mode': 'crane', 'dir': 'up', 'time': 1.2}, act='앞장의 숫자들이 종이에서 떨어져 나와 위로, 하늘로 빨려 올라간다', note='"위로" = 저승 관아(F20). 말하지 않는다'),
  st(4.6, act='뒷장 이름들은 남는다. 염씨가 장부를 덮어 마루에 놓고 빛으로 흩어진다', sfx=['cut.dissolve'])],
  None,
  note='먹지기 쪽지 "숫자를 어디서 배웠나 했더니. 아래 장부를 베꼈구나."는 이날 밤 명부 여백에 붙는다(컷 밖)'),
 pahon('B-08', '염씨', ['대폭발. 장부가 불붙는다', '앞장도 뒷장도 함께 탄다. 재가 마당에 내린다', '불탄 장부함에서 엽전이 쏟아진다'], '장부의 금(엽전 ×80)'),
]

# ═════════ 3막 ═════════
# B-09 망부석 아낙 — 망부석 곶 끝
CUTS += [
 intro('B-09', '망부석 곶 끝에 처음 들어설 때(한 번만)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.6, 'zoom': 1.1, 'framing': '아낙의 등 너머로 바다, 수평선을 화면 가운데'}, act='곶 끝. 사람 모양 바위에 반쯤 붙은 몸. 젖은 저고리. 손에 남자 옷 한 벌', req=['amb.harbor(파도·갈매기·배 삐걱임)']),
  st(1.6, act='아낙은 돌아보지 않는다. 바다만 본다'),
  st(2.8, cam={'mode': 'hold', 'zoom': 1.05}, act='먼 바다에서 파도가 줄지어 일어난다. 파도마다 물 혼 하나씩', req=['cut.wave.row(줄지어 밀려오는 파도)']),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '망부석 아낙', 'seal_icon': 'faded'}, note='전투: 파도 장판·물보라. 물 혼을 천도하면 파도 한 줄 약해짐')], 4.5),
 kneel('B-09', '아낙이 무릎 꿇는다. 옷은 놓지 않는다. 여전히 바다를 본다'),
 noclue('B-09', '아낙 머리 위 명부 인이 흐릿하게 떨리다 꺼진다. 파도 소리만'),
 tendo('B-09', None, [
  st(1.5, cam={'mode': 'orbit', 'around': 'boss', 'deg': 120, 'time': 2.0, 'zoom': 1.3}, act='아낙이 처음으로 바다에서 고개를 돌린다', note='카메라가 아낙을 돌아 그녀 얼굴 쪽 — 바다를 등진 구도로 바뀐다'),
  st(3.5, cond='B-10 천도함', cam={'mode': 'two_shot', 'a': 'boss', 'b': 'husband_soul', 'time': 0.5}, act='곁에 만선호 갑판꾼의 혼이 서 있다(전투 중 파도를 막아 섰던 그). 둘이 처음 마주 본다. 대사 없음'),
  st(5.0, act='아낙이 남자 옷을 놓는다. 옷이 바람에 실려 곶 아래 헛묘 쪽으로 날아간다', sfx=['cut.cloth.flutter']),
  st(6.2, act='아낙이(조건이면 둘이 함께) 빛으로 흩어진다. 망부석 바위만 남는다', sfx=['cut.dissolve'])],
  None, dur=8.0, first='명부가 펼쳐진다. 그 줄엔 택호(집 이름)만 흐릿하다. 인이 앉는다'),
 pahon('B-09', None, ['대폭발. 파도가 한꺼번에 무너진다', '남자 옷이 찢겨 바다로 흩어진다', '망부석 바위에 금이 한 줄 간다'], '등잔 기름(천도 중 시야 축소 무효 3회)'),
]

# B-10 만선호 선장 — 난파 여울(썰물 밤)
CUTS += [
 intro('B-10', '썰물 밤, 난파 여울 갑판에 처음 오를 때(한 번만)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '기운 갑판을 수평선과 비스듬히'}, act='드러난 여울 바닥, 반쯤 가라앉은 배. 갑판이 기울어 있다', req=['cut.hull.creak(배 몸체 삐걱임)']),
  st(1.4, act='난간에 선원 혼 일곱이 매달려 있다', note='수를 화면 글로 세지 않는다'),
  st(2.6, act='젖은 패랭이를 쓴 선장이 끊긴 밧줄 끝을 휘두른다. 갑판이 반대로 기운다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '만선호 선장', 'seal_icon': 'faded'}, note='전투: 줄 끊기 장판. 선원 혼 천도 −5%씩, 파혼하면 배가 가벼워짐(쉬워짐)')], 4.5),
 kneel('B-10', '선장이 기운 갑판에 무릎 꿇는다. 끊긴 밧줄 끝을 두 손에 쥐고'),
 noclue('B-10', '선장 머리 위 명부 인이 흐릿하게 떨리다 꺼진다. 갑판이 삐걱인다'),
 tendo('B-10', None, [
  st(1.5, cam={'mode': 'push', 'to': 'boss_face', 'time': 0.8, 'zoom': 1.6, 'framing': '입 아래 반만'}, act='선장이 이름을 부른다. 소리 없이 입 모양만. 한 번, 또 한 번 — 일곱 번', note='대사 0. 입 모양만. 이름 글자 없음'),
  st(4.0, cam={'mode': 'pull', 'zoom': 1.1, 'time': 1.0}, act='부를 때마다 손에 쥔 밧줄의 매듭이 하나씩 풀린다. 남아 있던 선원 혼이 난간에서 손을 놓고 빛으로 오른다', req=['cut.rope.untie(젖은 매듭 풀리는 소리)']),
  st(6.0, act='선장이 패랭이를 벗어 갑판에 놓고 흩어진다', sfx=['cut.dissolve']),
  st(7.0, cam={'mode': 'cut', 'to': 'shoal_path', 'time': 0.0}, act='여울 바닥에 젖은 돌길이 이어져 보인다(지름길)')],
  None, dur=8.5),
 pahon('B-10', None, ['대폭발. 갑판이 두 동강 난다', '난간의 선원 혼들이 물로 떨어져 사라진다', '부서진 배에서 닻 하나가 여울 바닥에 박힌다'], '선장의 닻(끌어당기기 강화 철삭)'),
]

# B-11 다리 밑 왕초 — 큰 다리 밑
CUTS += [
 intro('B-11', '큰 다리 밑에 처음 들어설 때(한 번만)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '다리 상판을 화면 위에 잘라 두고 둔치를 크게'}, act='다리 밑 둔치. 거적 움막들. 누더기 위에 기운 도포, 목에 나무 조각 목걸이', note='다리 상판은 반투명(기획 메모)'),
  st(1.4, act='왕초가 입을 연다. 소리는 없다. 거적 사이에서 혼 하나가 일어나 그를 돌아본다'),
  st(2.6, act='또 한 번. 다른 혼이 일어난다', req=['cut.soul.rise(혼이 일어나는 낮은 숨소리)']),
  st(3.6, cond='낮에 별명을 엿들은 무적 혼이 있음', act='그 혼들 중 몇은 일어나지 않고 플레이어 쪽을 돌아본다', note='전투 규칙 예고(대사 없음)'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '다리 밑 왕초', 'seal_icon': 'missing'})], 4.5),
 kneel('B-11', '왕초가 무릎 꿇는다. 목걸이를 한 손으로 움켜쥔다'),
 noclue('B-11', '왕초 머리 위 명부 인 자리가 비어 있다가 꺼진다'),
 tendo('B-11', '왕초', [
  st(1.5, cam={'mode': 'push', 'to': 'necklace', 'time': 1.0, 'zoom': 1.6}, act='목걸이의 나무 조각이 하나씩 빛난다. 차례로, 끝까지'),
  st(3.5, act='마지막 조각에는 아무것도 새겨져 있지 않다. 그 조각만 빛나지 않는다', note='글자는 읽히지 않게'),
  st(4.5, cam={'mode': 'pull', 'zoom': 1.1, 'time': 0.8}, act='명부 그 줄에 "왕초"가 적혀 있다. 아이들이 부르던 그 말이 이름이 되었다', ui={'ledger_fx': 'nickname_becomes_name'}, note='F26 회수. 명부 글자 "왕초"는 보여도 된다(이 컷의 핵심)'),
  st(6.0, act='거적 사이 혼들이 일어나 그를 둘러싼다. 함께 흩어진다', sfx=['cut.dissolve'])],
  {'clue_fill': 'B12-D4'}, dur=8.0, note='숨은 연결: B-12 단서 ④가 이 컷 끝에서 조용히 채워진다(토스트 없음, 추리판에만)'),
 pahon('B-11', '왕초', ['대폭발. 거적 움막들이 날아간다', '목걸이 줄이 끊겨 나무 조각이 둔치에 흩어진다', '엽전 꾸러미가 구른다'], '떠돌이들의 엽전 꾸러미(엽전 ×60)'),
 {'id': 'B11-AFTER', 'branch': '흑월 목격 ⑥-b', 'trigger': 'B-11 천도 다음 밤, 다리 밑에 처음 갈 때(한 번만)', 'duration': 6.0, 'input_lock': True,
  'world': 'pause_enemies', 'skippable': True, 'note': 'SCENARIO-ACT3 §5 ⑥-b. 대사 0',
  'steps': [
   st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'bridge_pillar', 'time': 1.2, 'zoom': 1.2}, act='다리 기둥 별명 목록 맨 아래 빈칸 앞에 흑월이 서 있다'),
   st(2.0, act='흑월이 돌아본다. 도망치지 않는다. 고개를 한 번 숙인다'),
   st(4.0, act='흑월이 다리 그늘로 걸어 들어가 사라진다', sfx=['cut.dissolve']),
   st(6.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'note_card': '별명이라도 좋다. 나는 그걸 적겠다. 먹이 모자라도.'}, note='먹지기 쪽지(B-11 천도 시). 파혼했으면 이 컷은 없고 쪽지만 "적을 것이 없다."')]},
]

# ═════════ B-12 흑월 2차 — 성문 밖 눈밭 ═════════
B12 = [
 {'id': 'B12-INTRO', 'branch': '등장', 'trigger': '결전이 열린 밤, 성문 밖 눈밭에 들어설 때', 'duration': 8.0, 'input_lock': True,
  'world': 'pause_enemies', 'skippable': True, 'note': '대사 0. 1차(B-04)의 "너는 아직 모른다."와 짝이 되는 말은 맨 끝(4단계)에만',
  'steps': [
   st(0.0, beat='눈밭', cam={'mode': 'crane', 'dir': 'down', 'from': 'high', 'to': 'arena', 'time': 2.5, 'zoom': 1.0, 'framing': '닫힌 성문을 화면 왼쪽 위, 눈밭을 크게'}, act='닫힌 성문. 성문 밖 눈밭에 팻말 없는 구덩이 무덤들. 그 사이를 혼 열둘이 떠돈다', req=['amb.snow.wind(눈밭 바람)']),
   st(2.5, beat='등', cam={'mode': 'push', 'to': 'boss', 'time': 1.5, 'zoom': 1.2, 'framing': '흑월의 등, 늘어뜨린 사슬 끝이 눈에 닿음'}, act='검은 갓의 차사가 등을 보이고 서 있다. 사슬 끝이 눈에 줄을 남긴다'),
   st(4.5, beat='돌아봄', act='흑월이 돌아본다. 갓 그늘에 얼굴이 없다', sfx=['cut.chain.wrap']),
   st(6.0, act='흑월이 사슬을 감아 쥔다. 떠돌던 혼 하나에 먼저 손을 뻗는다 — 천도하는 손짓', note='1단계 "두 차사": 그도 천도를 한다(가로채기)'),
   st(8.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'boss_bar': '흑월 차사', 'seal_icon': 'missing'})]},
 {'id': 'B12-P2', 'branch': '단계 2 명단', 'trigger': '맺힘 70%', 'duration': 2.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'steps': [
   st(0.0, cam={'mode': 'crane', 'dir': 'up', 'time': 0.8, 'zoom': 0.85, 'framing': '눈밭을 위에서 — 명단처럼'}, act='흑월이 사슬 끝으로 눈밭에 가로줄을 긋는다. 위에서부터 한 줄씩', req=['cut.chain.drag(사슬이 눈을 긁는 소리)']),
   st(1.5, act='맨 아래 한 줄은 긋지 않고 비워 둔다', note='그 칸만 안전 지대(S-117 "아직 안 죽은 사람 자리")'),
   st(2.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4})]},
 {'id': 'B12-P3', 'branch': '단계 3 큰물', 'trigger': '맺힘 40%', 'duration': 3.0, 'input_lock': False, 'world': 'run', 'skippable': False,
  'steps': [
   st(0.0, cam={'mode': 'hold', 'zoom': 0.95}, act='눈이 비로 바뀐다. 성문 밖이 물에 잠기기 시작한다', sfx=['amb.rain']),
   st(1.0, cam={'mode': 'push', 'to': 'floating_torch', 'time': 0.6, 'zoom': 1.2}, act='불어나는 물 어딘가에 횃불 하나가 떠 있다', note='오프닝 C-01의 횃불과 같은 불빛'),
   st(2.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, act='물 혼들이 떠밀려 온다. 흑월이 보이는 대로 깨뜨리기 시작한다', note='내가 먼저 천도하면 그의 맺힘 −3%씩')]},
 {'id': 'B12-KNEEL', 'branch': '단계 4 사슬을 내려놓다(처결 대기)', 'trigger': '맺힘 15%', 'duration': 6.0, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '흑월은 무릎 꿇지 않고 선다. 처결 대기 7초는 대사가 끝난 뒤부터 센다. 이 게임에서 흑월의 마지막 대사',
  'steps': [
   st(0.0, cam={'mode': 'pull', 'zoom': 1.0, 'time': 1.2}, act='물이 빠진다. 새벽빛이 눈밭에 든다', req=['cut.water.recede(물 빠지는 소리)']),
   st(1.5, cam={'mode': 'two_shot', 'a': 'player', 'b': 'boss', 'time': 0.8, 'zoom': 1.15, 'framing': '둘을 같은 높이로, 사이에 사슬'}, act='흑월이 사슬을 눈밭에 내려놓는다. 더 공격하지 않는다', sfx=['cut.chain.wrap']),
   st(2.8, line=say('이번엔 내가 기억하마. 불러 보아라.', 'B-12', 'bubble', 2.8)),
   st(5.6, ui={'kneel_timer': 7.0, 'seal_over_boss': 'clue>=3 ? steady : flicker'}),
   st(6.0, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3})]},
 noclue('B-12', '흑월 머리 위 명부 인 자리가 비어 있다. 흑월은 기다린다'),
]
CUTS += B12

# ═════════ 시즌 1 끝 ═════════
C12A = {'id': 'C-12A', 'branch': '천도(시즌 1 끝 A판)', 'trigger': 'B-12 천도 캐스팅 2.0초 완료', 'duration': 90.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 얼굴은 끝까지 보이지 않는다. F9는 글로 쓰지 않고 "같은 구도"와 "같은 색"으로만 알린다. 오프닝 C-01(20초)의 장면을 그대로 되짚는 컷이 셋 있다(match_cut)',
 'steps': [
  st(0.0, beat='캐스팅 끝', cam={'mode': 'hold', 'zoom': 1.4, 'vignette': 0.7, 'vignette_color': mem['B-12'].get('tint')}, act='눈밭 위 흑월. 사슬이 눈 위에 놓여 있다', sfx=['sfx.clue']),
  st(2.0, beat='기억 속으로', cam={'mode': 'fade_out', 'time': 1.5}, act='화면 가장자리부터 비가 번져 들어온다', sfx=['amb.rain']),
  st(4.0, beat='큰물 밤', cam={'mode': 'crane', 'dir': 'down', 'from': 'sky', 'to': 'dike', 'time': 6.0, 'framing': '둑 위에서 내려다봄, 아주 어둡게'}, act='큰물 밤. 비. 불어난 물. 둑 위에 횃불 하나',
     note='match_cut ① C-01 t=3.0과 같은 구도. 기억 장면은 실시간 3D + 탱화풍 색(기획 확정)'),
  st(10.0, beat='일곱', cam={'mode': 'track', 'to': 'torch_bearer', 'time': 16.0, 'zoom': 1.1, 'framing': '둑을 옆으로, 사람은 실루엣'},
     act='횃불을 진 젊은이가 물로 들어가 사람을 끌어올린다. 둑에 눕힌다. 다시 들어간다. 또 하나. 또 하나', req=['cut.splash.pull(물에서 사람을 끌어올리는 소리)'],
     note='약 2초에 한 사람, 일곱. 수를 글로 세지 않는다. 일곱째(S-120)는 다른 이들보다 조금 오래 비춘다'),
  st(26.0, beat='여덟째', cam={'mode': 'hold', 'framing': '둑 위에서 물 쪽, 젊은이 등'}, act='젊은이가 둑에 서서 물을 본다. 물 한가운데 무언가 떠내려간다(보릿단 하나). 젊은이가 다시 들어간다',
     note='여덟째는 보여 주지 않는다(시즌 3 몫). 보릿단만'),
  st(32.0, beat='잠김', cam={'mode': 'follow', 'to': 'torch', 'time': 3.0}, act='횃불이 물에 잠긴다. 꺼지기 전 물속이 주황으로 한 번 밝아진다', sfx=['cut.torch.sink'],
     note='match_cut ② C-01 t=10.0과 같은 연출'),
  st(38.0, beat='늦음', cam={'mode': 'cut', 'to': 'shore_low', 'framing': '물가 낮게, 검은 갓의 등'}, act='검은 갓의 차사가 물에서 젊은이를 끌어낸다. 젊은이는 움직이지 않는다', note='젊은이 얼굴은 물풀·그늘로 가린다'),
  st(46.0, beat='빈 획', cam={'mode': 'push', 'to': 'ledger', 'time': 2.0, 'zoom': 1.6, 'framing': '명부를 위에서, 한 줄만'}, act='차사가 명부를 편다. 한 줄 — 이름 자리에 획이 없다. 먹이 번진 자국뿐', sfx=['cut.ledger.open'],
     note='이름 글자를 보여 주지 않는다(이름은 결말 A에서만)'),
  st(54.0, beat='사슬', cam={'mode': 'close', 'framing': '손 하나(얼굴 없음)'}, act='차사가 사슬을 꺼내 젊은이의 손목에 감는다. 한 바퀴, 두 바퀴', sfx=['cut.chain.wrap'],
     note='match_cut ③ C-01 t=15.0과 같은 구도·같은 손. 플레이어가 여기서 알아차리게 한다'),
  st(60.0, beat='기억 한 줄', line=say(mem['B-12']['memory'], 'B-12', 'memory', 5.0), note='기억 M-B12(★F9). 그림이 먼저, 글은 뒤에 — 확인으로만'),
  st(66.0, beat='같은 색', cam={'mode': 'cut', 'to': 'arena', 'framing': '눈밭, 나와 흑월'}, act='눈밭으로 돌아온다. 화면 가장자리 기억 색이 천천히 내 혼불 색으로 바뀐다',
     ui={'vignette_to': 'player_soul_color', 'fact_on': 'F9', 'board_center': '나'}, note='추리판 가운데 빈칸에 "나". 이름 칸은 비어 있다'),
  st(74.0, beat='떠남', cam={'mode': 'crane', 'dir': 'up', 'time': 6.0, 'framing': '흑월 혼불과 강 하류를 한 화면에'}, act='흑월이 흩어지지 않는다. 혼불이 되어 삼도천 쪽으로 천천히 떠간다', sfx=['cut.dissolve'],
     note='시즌 2 ⑦ 줄에서 다시 만난다'),
  st(82.0, beat='붓', cam={'mode': 'push', 'to': 'snow_brush', 'time': 2.0, 'zoom': 1.5}, act='사슬은 남지 않았다. 눈밭에 붓 한 자루가 남아 있다', req=['cut.snow.settle(눈 위에 가벼운 것이 놓이는 소리)']),
  st(90.0, cam={'mode': 'fade_out', 'time': 1.0}, ui={'reward': {'memory': 'M-B12', 'item': '흑월의 붓(이름 있는 노리개 · 시즌 2로 가져감)'}}, note='다음: C-13(A판)'),
 ]}
C12B = {'id': 'C-12B', 'branch': '파혼(시즌 1 끝 B판)', 'trigger': 'B-12 처결 대기 중 파혼 입력', 'duration': 60.0,
 'input_lock': True, 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 무엇을 잃었는지 말하지 않는다. 같은 색이 한 번 스치고 꺼지는 것만',
 'steps': [
  st(0.0, beat='폭발', cam={'mode': 'shake', 'strength': 'big', 'time': 0.8}, act='즉시 폭발', sfx=['sfx.pahon.burst']),
  st(1.0, beat='먹', cam={'mode': 'crane', 'dir': 'up', 'time': 7.0, 'zoom': 0.8, 'framing': '눈밭 위에서, 번지는 검은 자국'}, act='흑월의 혼이 먹물처럼 흩어져 눈밭에 번진다. 번진 자국이 명단의 줄들을 덮는다', sfx=['cut.stroke.scatter']),
  st(8.0, beat='철삭', cam={'mode': 'push', 'to': 'dropped_chain', 'time': 1.5, 'zoom': 1.3}, act='눈 위에 흑월의 철삭이 떨어진다', sfx=['cut.chain.wrap']),
  st(12.0, beat='스침', cam={'mode': 'close', 'to': 'player_soul', 'time': 2.0, 'framing': '내 혼불을 크게'}, act='흩어지는 조각 하나가 내 혼불 옆을 스친다. 아주 잠깐, 같은 색으로 빛났다가 꺼진다',
     note='뜻을 알려 주지 않는다. 슬로 0.5배 2초'),
  st(20.0, beat='빈 눈밭', cam={'mode': 'hold', 'zoom': 0.9, 'framing': '닫힌 성문과 눈밭, 아무도 없음'}, act='혼 열둘이 떠돌던 자리가 비었다. 눈만 내린다', req=['amb.snow.wind(눈밭 바람)']),
  st(35.0, beat='추리판', ui={'board_view': True, 'board_center': 'smudged'}, act='추리판 가운데 빈칸이 번진 채 남는다', note='F9 영영 없음(시즌 1 다시 하기로만)'),
  st(50.0, beat='복귀', cam={'mode': 'return', 'to': 'player', 'time': 1.0}, ui={'reward': {'item': '흑월의 철삭(전설 무기)'}, 'karma': '+3'}),
  st(60.0, cam={'mode': 'fade_out', 'time': 1.0}, note='다음: C-13(B판)'),
 ]}
C13 = {'id': 'C-13', 'branch': '시즌 1 마지막 새벽(공통, A/B 갈래)', 'trigger': 'C-12A 또는 C-12B 끝', 'duration': 80.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 당할미는 A판에서도 나를 보지 못한다. 초혼 없음(초혼은 게임 결말 A 전용). variant 키가 A/B 차이',
 'steps': [
  st(0.0, beat='동트기 전', cam={'mode': 'fade_in', 'time': 2.0, 'framing': '서낭당 고개, 푸른 새벽빛, 서낭나무를 화면 오른쪽'}, act='솔고개 서낭당. 동트기 직전', req=['amb.dawn.birds(새벽 새 한두 마리)']),
  st(4.0, beat='사잣밥', cam={'mode': 'track', 'to': 'dang_halmi', 'time': 10.0, 'height': 'low', 'framing': '당할미 손과 상을 낮게'},
     act='당할미가 서낭나무 아래 사잣밥을 차린다. 밥 세 그릇, 짚신 한 켤레, 엽전 셋', sfx=['cut.brass.tap', 'cut.coins.few'], note='1막부터 매 새벽 보던 바로 그 상'),
  st(16.0, beat='선 자리', variant={'A': {'camera': {'mode': 'two_shot', 'a': 'dang_halmi', 'b': 'player', 'time': 2.0, 'framing': '둘을 나란히, 같은 높이'},
                                         'action': '차사가 상 앞이 아니라 당할미 곁으로 걸어가 선다(자동 걷기)'},
                                   'B': {'camera': {'mode': 'hold', 'framing': '상 너머로 차사, 당할미는 화면 끝'},
                                         'action': '차사가 상 앞에 선다. 늘 그랬듯'}}),
  st(24.0, beat='짚신', variant={'A': {'camera': {'mode': 'close', 'to': 'straw_shoes', 'time': 1.5}, 'action': '당할미가 짚신 한 켤레를 조금 고쳐 놓는다. 차사의 발과 같은 크기다',
                                       'note': '발 크기는 화면으로만(차사 발과 짚신을 한 화면에). 글 없음'},
                                 'B': {'camera': {'mode': 'close', 'to': 'straw_shoes', 'time': 1.5}, 'action': '짚신은 그냥 놓여 있다'}}),
  st(34.0, beat='바람', cam={'mode': 'hold', 'framing': '당할미 옆얼굴, 시선은 화면 밖'}, act='바람이 분다. 서낭나무 천 조각이 흔들린다. 당할미가 고개를 든다. 아무 말도 하지 않는다',
     req=['amb.wind.gust(바람 한 줄기)'], note='추위 규칙: 지나가는 차사의 한기를 느끼는 사람은 당할미뿐 — 고개를 드는 것으로만. 카메라를 보지 않는다'),
  st(44.0, beat='나룻불', cam={'mode': 'crane', 'dir': 'up', 'time': 4.0, 'to': 'river_far', 'framing': '고개 너머 강 하류를 멀리'}, act='멀리 강 하류, 삼도천 나룻불들. 하나가 꺼진다. 둘. 그리고 한꺼번에 전부',
     note='시즌 2 고리. 소리는 빼고 바람만'),
  st(58.0, beat='쪽지', ui={'note_card': '배가 멈췄다. 이제 아래로 와라.', 'note_card_time': 6.0}, act='명부 여백 먹지기 쪽지'),
  st(68.0, beat='끝', cam={'mode': 'fade_out', 'time': 3.0}, ui={'small_caption': '시즌 1 이름을 부르는 자 — 끝'}, note='작은 글씨, 화면 아래'),
  st(80.0, act='크레딧 또는 시즌 2 대기 화면'),
 ]}
CUTS += [C12A, C12B, C13]

for c in CUTS:
    c['steps'].sort(key=lambda x: x['t'])   # 박자를 시간 순서로(같은 시각은 적은 순서 유지)
    promote(c)

data = {
 '_설명': '시즌 1 실시간 컷신 대본 — 2막 B-05~08, 3막 B-09~11, 흑월 2차 B-12 결전 컷, 시즌 1 끝 C-12A·C-12B·C-13. tools/cutscenes_s1.py로 생성. 1막 cutscenes_b01~b03.json과 같은 형식. 서사 2026-10-25',
 'rules': {
  'protagonist_lines': 0,
  'lines': '2·3막 보스는 말하지 않는다. 예외 둘: B-07 "…열셋. 그리고 — 칠성."(2막), B-12 "이번엔 내가 기억하마. 불러 보아라."(3막). 기억 줄(memory)은 대사로 세지 않는다',
  'time': 't는 컷 시작부터 초. duration 안에서 끝난다',
  'camera': 'pan(옮기기)·push(다가가기)·pull(물러나기)·hold(멈춤)·cut(장면 바꾸기)·shake(흔들기)·return(플레이어로) + 긴 컷용: crane(위아래로 올리고 내리기)·track(옆으로 따라가기)·follow(대상 따라가기)·orbit(대상 둘레를 돌기)·two_shot(둘을 한 화면에)·close(아주 가까이)·fade_in/fade_out. zoom 1.0 = 평소 쿼터뷰 거리. framing = 구도 메모',
  'beat': '긴 컷(B-12·C-12A/B·C-13)은 박자마다 beat 이름. 편집할 때 박자 단위로 늘이고 줄인다',
  'match_cut': 'C-12A의 match_cut ①②③은 오프닝 C-01(first_session_scripts.json)의 t=3.0·10.0·15.0과 같은 구도·같은 연출로 맞춘다. F9는 이 겹침으로만 알린다',
  'condition': 'condition이 붙은 박자는 그 조건일 때만. 아니면 건너뛴다',
  'variant': 'C-13의 variant.A/B는 시즌 1 끝 A판/B판에 따라 그 박자의 카메라·동작을 바꾼다',
  'world': 'pause_enemies = 적 멈춤(입력 잠금 컷만) / run = 전투 계속',
  'face': '횃불 젊은이·흑월·장수의 얼굴은 보이지 않는다(그늘·갓·물풀)',
  'sfx': 'sfx = 있는 소리 id, sfx_request = 아직 없는 소리(사운드팀 요청). 생긴 소리는 sfx_map.promote가 옮긴다',
  'skippable': '길게 눌러 건너뛰기. 건너뛰어도 보상·단서·세계 변화는 그대로',
 },
 'cutscenes': CUTS,
}
json.dump(data, open(os.path.join(D, 'cutscenes_s1.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(CUTS), 'cutscenes')
