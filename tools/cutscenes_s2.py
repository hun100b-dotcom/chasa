# -*- coding: utf-8 -*-
# 시즌 2 「줄과 먹방」 실시간 컷신 대본 — 4막(⑦·⑧) · 5막(⑨·⑩).
#   여는 장면 C-14·C-14S, 줄 C-15, 보스 B-13~B-20(등장·처결 대기·천도 불가·천도·파혼·단계 컷),
#   장례 변주 세 틀(배웅·정서·잇기), 먹지기 C-16·C-17·C-18, 시즌 2 끝 C-20A·C-20B.
# 형식은 시즌 1(cutscenes_s1.json)과 같다. 같은 도우미(st·say·intro·kneel·noclue·tendo·pahon)를 쓴다.
# 원칙:
#   - 주인공 대사 0. 시즌 2 보스 대사는 B-19 한 줄 + C-20A 첫 차사 한 줄뿐(season2_outline rules.lines). 보스 말풍선은 보스당 3줄 이하(코디 10-25).
#   - ⑦~⑩엔 산 사람이 없다. 저승은 나를 "보지만" 아무도 말을 걸지 않는다 — 시선과 몸짓으로만.
#   - 쓰지 않는 것: 먹지기의 얼굴, 어미의 이름, 사공의 정체(시즌 4 고리), 흑월의 본명 글자(7막 F62), "초혼"·"동이"(결말 A 전용), 추위 말.
#   - 열 시왕·재판·형벌 장면 없음. 명부전 본당 문은 끝까지 닫혀 있다(IP 선).
#   - 카메라는 "구도(framing) · 움직임(mode) · 박자(t·time)"로 지시한다. 긴 컷은 박자마다 beat 이름.
# 실행: python3 tools/cutscenes_s2.py → docs/narrative/cutscenes_s2.json
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_map import promote
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'docs', 'narrative')
mem = {s['id']: s for s in json.load(open(os.path.join(D, 'soul_memories.json'), encoding='utf-8'))['souls']}
S2 = json.load(open(os.path.join(D, 'season2_outline.json'), encoding='utf-8'))
BC = S2['boss_clues']

def st(t, cam=None, act=None, line=None, ui=None, note=None, sfx=None, req=None, cond=None, beat=None, variant=None):
    s = {'t': t}
    if beat: s['beat'] = beat
    if cam: s['camera'] = cam
    if act: s['action'] = act
    if line: s['line'] = line
    if ui: s['ui'] = ui
    if sfx: s['sfx'] = sfx
    if req: s['sfx_request'] = req
    if cond: s['condition'] = cond
    if variant: s['variant'] = variant
    if note: s['note'] = note
    return s

def say(text, speaker, style='bubble', dur=2.0):
    return {'speaker': speaker, 'text': text, 'style': style, 'duration': dur}

def cid(bid, kind): return f"{bid.replace('-', '')}-{kind}"

def intro(bid, trigger, steps, dur):
    return {'id': cid(bid, 'INTRO'), 'branch': '등장', 'trigger': trigger, 'duration': dur, 'input_lock': True,
            'world': 'pause_enemies', 'skippable': True, 'steps': steps}

def kneel(bid, act, extra=None, tendo_ok=True):
    steps = [st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.25}, act=act, sfx=['sfx.kneel'])]
    if extra: steps.append(extra)
    steps += [st(0.4, ui={'kneel_timer': 7.0, 'seal_over_boss': 'clue>=3 ? steady : flicker'} if tendo_ok else {'kneel_timer': 7.0, 'tendo_disabled': True}),
              st(1.5, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3, 'zoom': 1.0})]
    return {'id': cid(bid, 'KNEEL'), 'branch': '처결 대기', 'trigger': '보스 맺힘 0', 'duration': 1.5, 'input_lock': False,
            'world': 'run', 'skippable': False, 'note': '처결 대기 7초와 동시에 흐른다. 입력을 막지 않는다. 대사 없음', 'steps': steps}

def noclue(bid, act):
    return {'id': cid(bid, 'NOCLUE'), 'branch': '처결 대기(천도 불가)', 'trigger': '단서 2개 이하에서 천도 입력', 'duration': 1.0,
            'input_lock': False, 'world': 'run', 'skippable': False,
            'steps': [st(0.0, act=act, ui={'toast': '이름이 들리지 않는다.', 'toast_time': 1.0}, sfx=['cut.seal.fade'],
                         note='안내일 뿐. 캐스팅은 시작되지 않고 대기 시간은 계속 흐른다')]}

def tendo(bid, beats, dur=7.5, first=None, fx='strokes_join_unreadable', note=None, extra_ui=None, mem_t=1.0):
    """시즌 2 보스의 이름은 화면에 글자로 나오지 않는다(획이 모이는 것만). 그래서 ledger_name은 늘 비운다."""
    b = BC[bid]
    head = [st(0.0, cam={'mode': 'hold', 'zoom': 1.3, 'vignette': 0.6, 'vignette_color': mem[bid].get('tint')},
               act=first or '명부가 펼쳐지고, 번졌던 획들이 서로를 찾아 모인다(읽히지 않게)',
               ui={'ledger_fx': fx}, sfx=['cut.ledger.open', 'cut.brush.stroke', 'cut.seal.set']),
            st(mem_t, line=say(mem[bid]['memory'], bid, 'memory', 3.6), sfx=['sfx.clue'], note=f"기억 M-{bid.replace('-', '')}(★{b['decisive']} 전모)")]
    ui = {'fact_on': b['decisive'], 'reward': {'memory': 'M-' + bid.replace('-', '')}, 'world_change': b['tendo']}
    if extra_ui: ui.update(extra_ui)
    last = st(dur, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui=ui)
    c = {'id': cid(bid, 'TENDO'), 'branch': '천도', 'trigger': '천도 캐스팅 2.0초 완료', 'duration': dur, 'input_lock': True,
         'world': 'pause_enemies', 'skippable': True, 'steps': head + beats + [last]}
    if note: c['note'] = note
    return c

def pahon(bid, beats, reward_item, dam=True):
    steps = [st(0.0, cam={'mode': 'shake', 'strength': 'big', 'time': 0.5}, act=beats[0], sfx=['sfx.pahon.burst']),
             st(0.3, ui={'ledger_fx': 'strokes_scatter'}, act='명부의 그 줄이 흩어진다', sfx=['cut.stroke.scatter'])]
    steps += [st(0.8 + 0.7 * i, act=a) for i, a in enumerate(beats[1:])]
    ui = {'reward': {'item': reward_item}, 'karma': '+3', 'karma_warning': '업 단계 경계를 넘으면 화면 경고', 'world_change': BC[bid]['pahon']}
    if dam: ui['dam_gauge'] = '+큼(이름 줍기 쪽지를 낚으면 절반)'
    steps.append(st(2.5, ui=ui, note='대사 없음'))
    return {'id': cid(bid, 'PAHON'), 'branch': '파혼', 'trigger': '처결 대기 중 파혼 입력', 'duration': 2.5, 'input_lock': False,
            'world': 'run', 'skippable': False,
            'note': '즉시. 폭발로 화면의 잡몹이 밀려나 안전. ⑦~⑩ 파혼은 이름 쪽지가 1.5초 떠오른다(사슬로 낚으면 물막이 눈금 절반)', 'steps': steps,
            'name_slip': {'window': 1.5, 'at': 0.3}}

def phase(id_, branch, trigger, dur, steps, note=None):
    c = {'id': id_, 'branch': branch, 'trigger': trigger, 'duration': dur, 'input_lock': False, 'world': 'run', 'skippable': False, 'steps': steps}
    if note: c['note'] = note
    return c

CUTS = []

# ═════════ 시즌 2 여는 장면 ═════════
C14 = {'id': 'C-14', 'branch': '시즌 2 여는 장면', 'trigger': 'C-13 끝(시즌 1 이어 하기) / C-14S 끝(새 시작)', 'duration': 60.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 시즌 1 마지막 새벽 직후. 꺼진 나룻불 쪽으로 강을 따라 내려간다. condition: B-01 천도/파혼(시즌 1 기록)',
 'steps': [
  st(0.0, beat='고개 너머', cam={'mode': 'fade_in', 'time': 2.0, 'framing': '솔고개 서낭당 등 뒤에서 강 하류 쪽을 멀리'}, act='서낭당 너머로 강이 보인다. 나룻불은 다 꺼져 있다', sfx=['amb.river.mist']),
  st(6.0, beat='내려감', cam={'mode': 'follow', 'to': 'player', 'time': 14.0, 'height': 'low', 'framing': '차사 등 뒤, 강을 오른쪽에'}, act='차사가 강을 따라 내려간다. 걸을수록 물빛이 먹처럼 검어진다',
     note='자동 걷기. 물빛을 20초에 걸쳐 푸른 잿빛 → 먹빛으로'),
  st(20.0, beat='나루', cond='B-01 천도(시즌 1)', cam={'mode': 'crane', 'dir': 'down', 'time': 4.0, 'framing': '물 위로 이어진 나룻배들을 위에서'},
     act='나루 영감이 저어 주던 나룻배가 다리처럼 이어져 있다. 차사가 그 위를 건넌다', req=['cut.hull.creak(나무배가 밟혀 삐걱)']),
  st(20.0, beat='나루', cond='B-01 파혼(시즌 1)', cam={'mode': 'crane', 'dir': 'down', 'time': 4.0, 'framing': '부서진 판자들을 위에서'},
     act='부서진 판자들이 물에 떠 있다. 차사가 판자를 하나씩 밟아 건넌다', sfx=['cut.boat.break'], note='깨진 소리를 아주 작게'),
  st(30.0, beat='안개', cam={'mode': 'hold', 'zoom': 0.9, 'framing': '물안개 벽, 화면 가득 흰빛'}, act='물안개가 앞을 가린다', sfx=['amb.weather.fog']),
  st(38.0, beat='줄', cam={'mode': 'pull', 'zoom': 0.7, 'time': 8.0, 'framing': '안개가 걷히며, 끝이 안 보이는 줄을 옆으로 길게'},
     act='안개가 걷히면 줄이 보인다. 강가를 따라 혼들이 줄지어 서 있다. 끝이 안 보인다', note='줄 선 혼들은 움직이지 않는다. 고개도 돌리지 않는다'),
  st(50.0, beat='배 한 척', cam={'mode': 'push', 'to': 'ferry', 'time': 4.0, 'zoom': 1.1, 'framing': '줄 맨 앞, 강 위에 작은 배 하나'}, act='줄 맨 앞, 강 위에 배가 한 척 떠 있다. 노 젓는 이 하나',
     req=['cut.oar.row(노 젓기, 멀리)'], note='사공 얼굴은 갓 그늘로'),
  st(58.0, ui={'note_card': '배가 멈춘 이유를 보여 주겠다. 줄을 봐라.', 'note_card_time': 4.0}, act='명부 여백 먹지기 쪽지'),
  st(60.0, cam={'mode': 'return', 'to': 'player', 'time': 1.0}, ui={'region_title': '삼도천 기슭'}, note='다음: C-15(빈 나루 마을 첫 진입 때)'),
 ]}
C14S = {'id': 'C-14S', 'branch': '시즌 2부터 시작하는 사람용 요약', 'trigger': '시즌 2 새 시작(시즌 1 기록 없음)', 'duration': 60.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 기본 상태 "A판 + 업 12"(MASTER §S 규칙 6). 네 장면을 15초씩. F9의 내용은 말하지 않는다(같은 색만)',
 'steps': [
  st(0.0, beat='서낭당', cam={'mode': 'fade_in', 'time': 1.5, 'framing': '서낭당, 당할미 등'}, act='솔고개 서낭당. 당할미가 새벽마다 사잣밥을 차린다', sfx=['cut.brass.tap']),
  st(15.0, beat='부르는 차사', cam={'mode': 'orbit', 'to': 'player', 'time': 10.0, 'zoom': 1.2}, act='차사가 흐린 혼 앞에서 명부를 편다. 획이 모이고 혼이 빛으로 오른다', sfx=['cut.ledger.open', 'cut.seal.set', 'cut.dissolve']),
  st(30.0, beat='흑월', cam={'mode': 'hold', 'framing': '성문 밖 눈밭, 흑월의 등'}, act='눈밭. 검은 갓의 차사가 혼불이 되어 강 쪽으로 떠간다. 그 불빛이 내 혼불과 같은 색으로 한 번 빛난다', sfx=['cut.dissolve']),
  st(45.0, beat='짚신', cam={'mode': 'close', 'to': 'straw_shoes', 'time': 2.0}, act='사잣밥 상 위 짚신 한 켤레', req=['cut.straw.set(짚신을 상에 놓는 소리)']),
  st(60.0, cam={'mode': 'fade_out', 'time': 1.0}, note='다음: C-14'),
 ]}
C15 = {'id': 'C-15', 'branch': '줄(걷기 가능)', 'trigger': '빈 나루 마을(Ferrytown) 첫 진입', 'duration': 90.0, 'input_lock': False,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0, 'walkable': True,
 'note': '대사 0. 플레이어가 줄 옆 길(R7-2)을 직접 걷는다. 카메라는 걷는 속도에 맞춰 줄을 훑는다. 시즌 1에서 천도한 이름혼은 줄에서 고개를 숙이고, 파혼한 혼의 자리는 번진 먹 자국. 시즌 1 기록이 없으면 기본 상태(천도 위주)로 채운다',
 'steps': [
  st(0.0, beat='줄 끝', cam={'mode': 'follow', 'to': 'player', 'height': 'low', 'zoom': 1.1, 'framing': '줄을 화면 왼쪽에 길게, 차사는 오른쪽 3분의 1'}, act='줄 끝에서 걷기 시작한다. 줄 선 혼들은 앞만 본다',
     ui={'hud': 'hidden', 'walk_hint': '줄 옆 길을 따라 걷기'}),
  st(10.0, beat='고개 숙임', act='시즌 1에서 천도한 이름혼 곁을 지날 때마다 그 혼이 나를 보고 고개를 숙인다(지나는 순서대로)',
     note='플레이 기록에서 뽑는다. 들고 있는 것은 시즌 1 장례의 물건 그대로(박돌쇠 집게, 윤 소사 흰 저고리, 나루 영감 노, 대돌 접은 깃발, 왕초 별명 목걸이 등). 이름은 화면에 쓰지 않는다'),
  st(10.0, beat='번진 먹', cond='시즌 1 파혼한 이름혼이 있을 때', act='파혼한 이름혼의 자리는 비어 있고, 바닥에 번진 먹 자국만 있다. 앞뒤 혼이 그 자리를 비켜 선다', note='카메라가 그 자리에서 0.5초 느려진다. 강조하지 않는다'),
  st(45.0, beat='흑월', cond='B-12 천도(시즌 1)', cam={'mode': 'hold', 'framing': '줄 뒤쪽, 갓을 벗고 선 흑월'}, act='줄 뒤쪽에 흑월이 갓을 벗고 서 있다. 나를 보면 손으로 하류(물안개 둑)를 한 번 가리킨다', note='말 없음. 얼굴은 그늘로'),
  st(45.0, beat='흑월', cond='B-12 파혼(시즌 1)', cam={'mode': 'hold', 'framing': '줄 뒤쪽, 빈자리'}, act='그 자리에 먹 자국과 쇠사슬로 긁힌 자국', sfx=['cut.stroke.scatter']),
  st(60.0, beat='당할미의 남편', cam={'mode': 'hold', 'framing': '줄 끝 근처, 강 쪽을 보는 혼'}, act='줄 끝 가까이 한 혼이 강이 아니라 이승 쪽(위쪽)을 보고 서 있다. 입술이 움직인다. 소리는 없다', note='S-048. 누군지 알려 주지 않는다(배웅에서 풀림)'),
  st(75.0, beat='맨 앞', cam={'mode': 'pan', 'to': 'boss', 'time': 4.0, 'zoom': 1.0, 'framing': '줄 맨 앞, 나루 말뚝을 붙든 노인의 손'}, act='줄 맨 앞. 나루 말뚝을 붙든 노인. 배가 오면 뒷사람에게 손짓한다', note='B-13 복선. 노인 쪽으로 더 걸으면 B13-INTRO'),
  st(90.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'hud': 'shown'}),
 ]}
CUTS += [C14, C14S, C15]

# ═════════ 장례 변주 세 틀(⑦ 배웅 · ⑧ 정서 · ⑩ 잇기) ═════════
# 혼마다 다른 글(멈춘 것·다시 움직이는 것)은 memories_act4·5의 rite에서 넣는다. 여기는 카메라·박자 틀만.
RITES = [
 {'id': 'RITE-BAEUNG', 'branch': '⑦ 배웅(장례 변주)', 'trigger': '새벽 틈 시작, 배가 나루 말뚝 앞에 닿은 2분 안(그 밤 천도한 ⑦ 혼 먼저, 없으면 배웅 대기의 시즌 1 이름혼)',
  'duration': 30.0, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True, 'lines': 0, 'data': 'memories_act4.json souls[].rite(kind=배웅) / 시즌 1 이름혼은 npc_act4 rules.season1_send_off',
  'steps': [
   st(0.0, beat='#1 나루', cam={'mode': 'fade_in', 'time': 1.0, 'framing': '나루 말뚝 앞, 배와 줄을 한 화면에'}, act='배가 닿아 있다. 줄 선 혼들이 그 혼에게 길을 내준다', req=['cut.hull.creak(배가 말뚝에 닿아 삐걱)']),
   st(5.0, beat='#2 멈춘 것', cam={'mode': 'close', 'to': 'rite_stopped', 'time': 1.5}, act='{stopped}'),
   st(12.0, beat='#6 다시 움직이는 것', cam={'mode': 'two_shot', 'a': 'rite_soul', 'b': 'queue', 'time': 2.0}, act='{moving}'),
   st(22.0, beat='#7 나룻불', cam={'mode': 'crane', 'dir': 'up', 'time': 4.0, 'framing': '강 하류, 꺼진 나룻불들'}, act='배가 떠난다. 강가 나룻불 하나가 켜진다', sfx=['cut.lantern.light']),
   st(30.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5})]},
 {'id': 'RITE-JEONGSEO', 'branch': '⑧ 정서(장례 변주)', 'trigger': '숫자 마당 혼을 천도한 다음 새벽 틈(마당 책상 서리 N-803)',
  'duration': 30.0, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True, 'lines': 0, 'data': 'memories_act4.json souls[].rite(kind=정서)',
  'steps': [
   st(0.0, beat='#1 마당', cam={'mode': 'fade_in', 'time': 1.0, 'framing': '숫자 마당 한쪽 책상, 번호순으로 선 혼들이 배경'}, act='서리가 책상에 명부를 펴고 붓에 먹을 묻힌다', sfx=['cut.ink.grind']),
   st(5.0, beat='#2 멈춘 것', cam={'mode': 'close', 'to': 'rite_stopped', 'time': 1.5}, act='{stopped}'),
   st(12.0, beat='#6 다시 적기', cam={'mode': 'push', 'to': 'ledger', 'time': 2.0, 'zoom': 1.5}, act='{moving}', sfx=['cut.brush.write'], note='적는 글씨는 읽히지 않게'),
   st(22.0, beat='#7 번호 패', cam={'mode': 'hold', 'framing': '마당 바닥'}, act='번호 패가 마당 바닥에 떨어진다', sfx=['cut.tag.unhook']),
   st(30.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5})]},
 {'id': 'RITE-JOIN', 'branch': '⑩ 잇기(장례 변주)', 'trigger': '이은 이름(조각 셋)을 천도할 때',
  'duration': 20.0, 'input_lock': True, 'world': 'pause_enemies', 'skippable': True, 'lines': 0, 'data': 'memories_act5.json join_rite / fragment',
  'steps': [
   st(0.0, beat='맞물림', cam={'mode': 'close', 'to': 'chain_tip', 'time': 1.0, 'zoom': 1.6}, act='사슬 끝에서 조각 셋이 맞물린다. 번진 획이 서로를 찾는다', req=['cut.names.glow(획이 맞물리며 빛나는 소리)']),
   st(6.0, beat='한 글자', act='획이 한 글자가 된다(읽히지 않게)', sfx=['cut.seal.set']),
   st(8.0, beat='한 줄', line={'speaker': 'fragment', 'text': '{fragment}', 'style': 'memory', 'duration': 3.0}, note='memories_act5 fragment 중 하나(한 판에 같은 줄 한 번)'),
   st(14.0, beat='사슬 무덤', cam={'mode': 'cut', 'to': 'chain_graves', 'framing': '녹슨 사슬들이 비석처럼, 낮게'}, act='사슬 무덤의 녹슨 사슬 하나가 조금 덜 녹슬어 보인다'),
   st(20.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5})]},
]
CUTS += RITES

# ═════════ 4막 ⑦ ═════════
CUTS += [
 intro('B-13', '나루 말뚝 앞 싸움 원에 처음 들어설 때(Ferrytown에 밤에 처음 들어간 다음 새벽 틈 이후의 밤)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '줄 맨 앞, 노인의 손과 말뚝을 크게'}, act='노인이 나루 말뚝을 붙들고 서 있다. 배가 들어온다', sfx=['amb.river.mist']),
  st(1.6, act='노인이 뒤를 돌아보며 손짓한다. 줄 선 혼 몇이 배에 오른다. 노인은 오르지 않는다', note='"먼저 가시오"는 손짓으로만. 글로 쓰지 않는다'),
  st(3.2, act='배가 떠난다. 노인이 말뚝에 칼금을 하나 더 긋는다', req=['cut.knife.notch(나무에 칼금 긋는 짧은 소리)']),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '줄의 맨 앞 노인', 'seal_icon': 'missing'}, note='전투: 손짓에 줄 선 혼들이 밀려온다(장애물 — 때리면 돌아선 혼이 된다)')], 4.5),
 phase('B13-BOAT', '맺힘 50% — 배가 닿는다', '맺힘 50%', 3.0, [
  st(0.0, cam={'mode': 'pull', 'zoom': 0.95, 'time': 0.4}, act='배가 말뚝 앞에 3초 닿는다. 노인이 손짓을 멈춘다', req=['cut.hull.creak(배가 말뚝에 닿아 삐걱)'], ui={'hint_icon': '천도 캐스팅으로 줄 선 혼의 등을 밀어 배에 태우기'}),
  st(3.0, act='배가 떠난다', note='태웠으면 노인 맺힘 −20%. 노인이 처음으로 남이 아닌 내가 누군가를 태우는 것을 본다(그의 손이 잠깐 멈춘다)')]),
 kneel('B-13', '노인이 말뚝을 놓지 않은 채 무릎 꿇는다. 다른 손은 아직 뒤를 향해 손짓하고 있다'),
 noclue('B-13', '노인 머리 위 명부 인 자리가 비어 있다가 꺼진다. 손짓은 멈추지 않는다'),
 tendo('B-13', [
  st(1.8, cam={'mode': 'track', 'to': 'queue', 'time': 3.0, 'zoom': 0.8, 'framing': '노인 어깨 너머로 줄 끝까지'}, act='노인이 마지막으로 뒤를 돌아본다 — 줄 끝까지'),
  st(5.0, cam={'mode': 'two_shot', 'a': 'boss', 'b': 'ferry', 'time': 1.0}, act='노인이 처음으로 배에 오른다. 구멍 닳은 엽전을 사공에게 건넨다', sfx=['cut.coins.few']),
  st(7.0, act='배가 떠난다. 그 뒤로 두 번째 배가 안개 속에서 나온다. 줄이 처음으로 한 칸 움직인다', req=['cut.oar.row(노 젓기 둘)'],
     note='두 번째 배 사공: 시즌 1 B-12 천도면 흑월(첫 사공과 서로 갓을 숙인다), 아니면 이름 없는 차사 혼')],
  dur=9.5),
 pahon('B-13', ['대폭발. 말뚝이 부러진다', '노인이 쥐고 있던 노잣돈 꾸러미가 터져 엽전이 강가에 쏟아진다', '줄 맨 앞이 빈다. 아무도 그 자리로 나서지 않는다'],
       '노잣돈 꾸러미(엽전 ×100) + 노인의 요령(이름 있는 물건)'),
]
CUTS[-1]['steps'].insert(3, st(0.8, sfx=['cut.coins.spill']))

# B-14 돌아선 혼들의 덩어리 — 선택 없는 유일한 보스
CUTS += [
 intro('B-14', '물안개 둑 싸움 원에 처음 들어설 때(Dam에 밤에 처음 들어간 다음 밤)', [
  st(0.0, cam={'mode': 'crane', 'dir': 'up', 'time': 2.0, 'zoom': 0.9, 'framing': '둑 위, 안개 벽을 등진 덩어리'}, act='둑 위에 혼 수백이 엉긴 덩어리. 표면에 얼굴들이 떠올랐다 가라앉는다', sfx=['amb.weather.fog']),
  st(2.0, cam={'mode': 'push', 'to': 'boss_face', 'time': 1.0, 'zoom': 1.3}, act='얼굴 몇이 오래 떠 있다',
     note='시즌 1에서 처결 대기를 넘겨 놓친 이름혼의 얼굴(플레이 기록). 없으면 모르는 얼굴만. 이름은 쓰지 않는다'),
  st(4.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '돌아선 혼들의 덩어리', 'seal_icon': 'missing'}, note='전투: 조각을 깨뜨리면 이름 쪽지가 1.5초 떠오른다(이름 줍기)')], 4.0),
 kneel('B-14', '덩어리가 둑에 주저앉는다. 표면의 얼굴들이 모두 나를 본다', tendo_ok=False),
 {'id': 'B14-PAHON', 'branch': '처결(파혼만)', 'trigger': '처결 대기 중 파혼 입력(7초가 지나도 자동으로)', 'duration': 6.0, 'input_lock': True,
  'world': 'pause_enemies', 'skippable': True, 'lines': 0, 'note': '선택이 없으니 업 +0. 주운 쪽지 수(n)에 따라 끝 박자가 달라진다',
  'steps': [
   st(0.0, cam={'mode': 'shake', 'strength': 'big', 'time': 0.6}, act='덩어리가 깨진다', sfx=['sfx.pahon.burst']),
   st(0.8, cam={'mode': 'crane', 'dir': 'up', 'time': 2.0, 'zoom': 0.8}, act='둑에 붙어 있던 이름 쪽지가 눈처럼 흩어진다', req=['cut.paper.ascend(종이가 바람에 흩날려 오름)']),
   st(3.0, cond='n>0', cam={'mode': 'cut', 'to': 'queue_end', 'framing': '줄 끝, 안개 앞'}, act='줄 끝에 희미한 혼이 하나씩 다시 선다 — 주운 쪽지 수만큼', sfx=['cut.seal.set']),
   st(3.0, cond='n==0', cam={'mode': 'cut', 'to': 'queue_end', 'framing': '줄 끝, 안개 앞'}, act='줄 끝은 그대로다. 아무도 서지 않는다'),
   st(5.0, act='둑 너머 안개가 걷혀 상류 명부전 길이 보인다'),
   st(6.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'karma': '+0', 'dam_gauge': '주운 쪽지에 따라 +큼~+작음', 'world_change': BC['B-14']['pahon']})]},
]

# ═════════ 4막 ⑧ ═════════
CUTS += [
 intro('B-15', '문서 창고 맨 안쪽 싸움 원에 처음 들어설 때', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '끝없는 서가 사이, 책상 하나'}, act='끝없는 서가. 손이 먹으로 검은 늙은 서리가 상소문 한 장에 무언가를 적는다', sfx=['cut.brush.write']),
  st(1.8, cam={'mode': 'push', 'to': 'boss_paper', 'time': 0.8, 'zoom': 1.5}, act='적은 줄이 먹에 번져 사라진다. 그가 다시 적는다. 다시 사라진다', note='글자는 읽히지 않게. 줄 하나가 지워지는 것만'),
  st(3.2, act='그가 번호 도장을 든다. 바닥이 번호 칸으로 나뉜다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '숫자를 처음 쓴 서리', 'seal_icon': 'faded'}, note='전투: 내가 천도한 혼 25마다 이름이 적힌 안전 칸 1')], 4.5),
 phase('B15-P30', '맺힘 30% — 상소문 원본', '맺힘 30%', 3.0, [
  st(0.0, cam={'mode': 'push', 'to': 'petition', 'time': 0.5, 'zoom': 1.3}, act='그가 상소문 원본을 펼친다. 끝 한 줄이 먹으로 덧칠돼 있다', ui={'hint_icon': '사슬로 먹을 튕겨 지워진 줄 드러내기(3초)'}),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3}, note='드러내면 그가 도장을 떨어뜨린다(웅크림)')]),
 kneel('B-15', '서리가 무릎 꿇는다. 손가락 자국 파인 도장이 손에서 미끄러진다'),
 noclue('B-15', '서리 머리 위 명부 인이 흐릿하게 떨리다 꺼진다. 그는 다시 그 줄을 적기 시작한다'),
 tendo('B-15', [
  st(1.8, cam={'mode': 'close', 'to': 'boss_mouth', 'time': 1.0}, act='그가 지워진 줄을 소리 없이 읽는다. 입 모양만', note='읽는 글을 자막으로 쓰지 않는다(기억 글이 이미 말했다)'),
  st(4.0, cam={'mode': 'cut', 'to': 'number_yard', 'framing': '숫자 마당을 높이서'}, act='숫자 마당. 번호순으로 선 혼들 머리 위에 번호 옆으로 이름 획이 하나씩 떠오른다', sfx=['cut.seal.set']),
  st(6.5, act='서리가 도장을 책상에 내려놓고 빛으로 흩어진다', sfx=['cut.dissolve'])], dur=8.0),
 pahon('B-15', ['대폭발. 서가가 무너진다', '상소문 원본이 먹물에 잠긴다', '번호 도장 하나가 바닥에 굴러 멈춘다'], '서리의 붓(파혼 시 일정 확률 업 +0)'),

 intro('B-16', '먹방 가운데 큰 벼루 앞에 처음 들어설 때', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.1, 'framing': '거대한 벼루, 팔이 먹에 잠긴 사람'}, act='거대한 벼루 앞. 팔이 먹에 잠긴 사람이 먹을 간다', sfx=['cut.ink.grind']),
  st(1.6, cam={'mode': 'orbit', 'to': 'boss', 'time': 2.0, 'zoom': 1.2}, act='벼루 둘레를 흐린 글줄들이 돈다 — 내가 모은 기억 한 줄들', note='플레이 기록에서 3~5줄. 읽힐 만큼만 또렷하게'),
  st(3.6, cam={'mode': 'close', 'to': 'boss_face', 'time': 0.6}, act='그의 눈가에 소금 자국. 갈면서 운다', note='우는 소리는 없다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '벼루지기', 'seal_icon': 'faded'}, note='전투: 기억 줄을 잡으면 그가 1초 멈춘다. 파혼이 많았으면 바닥에 먹물 웅덩이')], 4.5),
 kneel('B-16', '벼루가 멈춘다. 벼루지기가 먹 묻은 팔을 처음으로 든다'),
 noclue('B-16', '벼루지기 머리 위 명부 인이 흐릿하게 떨리다 꺼진다. 그는 다시 갈기 시작한다'),
 tendo('B-16', [
  st(1.8, act='그가 처음으로 갈기를 멈춘다. 붓을 들어 종이에 무언가를 쓰려다 — 쓰지 못한다', sfx=['cut.brush.stroke']),
  st(4.0, cam={'mode': 'close', 'to': 'boss_face', 'time': 1.0}, act='그가 웃는다', note='시 글자는 끝내 보이지 않는다'),
  st(5.5, cam={'mode': 'pull', 'zoom': 0.9, 'time': 1.0}, act='벼루 둘레를 돌던 기억 줄들이 한 줄씩 길어진다 — 원래 장면으로', note='도감 확장 연출. 실제 글은 ink_originals.json'),
  st(7.0, act='벼루지기가 빛으로 흩어진다', sfx=['cut.dissolve'])], dur=8.5, extra_ui={'collection_unlock': '도감: 먹으로 갈리기 전 원본(ink_originals.json)'}),
 pahon('B-16', ['대폭발. 벼루 하나가 갈라진다', '먹물이 바닥에 번진다. 기억 줄들이 먹에 잠긴다', '갈라진 벼루 조각이 굴러 멈춘다'], '벼루(넋 대량)'),
]

C16 = {'id': 'C-16', 'branch': '4막 끝 — 먹지기의 빈 책상', 'trigger': 'B-15·B-16 둘 다 처결한 다음 새벽 틈(먹방 가장 안쪽 작은 방)', 'duration': 70.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 주인 없는 방. 먹지기의 얼굴·이름은 나오지 않는다(시즌 4 고리). 쪽지 글은 1막부터 실제로 받은 것 그대로',
 'steps': [
  st(0.0, beat='문패 없는 방', cam={'mode': 'fade_in', 'time': 1.5, 'framing': '먹방 가장 안쪽, 문패 없는 작은 방 문'}, act='문패 없는 작은 방. 문이 조금 열려 있다', sfx=['amb.mine.wind'], note='먹방 바람 대신 쓸 소리는 사운드팀 몫'),
  st(6.0, beat='의자', cam={'mode': 'push', 'to': 'desk', 'time': 3.0, 'zoom': 1.2, 'framing': '책상과 살짝 빠진 의자'}, act='책상. 의자가 살짝 빠져 있다 — 방금 일어난 것처럼'),
  st(12.0, beat='쪽지 묶음', cam={'mode': 'close', 'to': 'note_bundle', 'time': 2.0}, act='쪽지 묶음 — 1막부터 명부 여백에서 읽은 쪽지들의 원본. 맨 위는 처음 받은 것',
     ui={'note_card': '불러도 안 들린다.', 'note_card_time': 3.0}, note='묶음 옆면으로 종이 두께가 갈수록 얇아졌다가(2막) 다시 두꺼워지는(3막) 것이 보이게'),
  st(22.0, beat='역병 명단', cam={'mode': 'track', 'to': 'plague_list', 'time': 4.0, 'framing': '누렇게 바랜 명단, 마지막 줄까지'}, act='누렇게 바랜 명단 사본. 마지막 줄이 비어 있다', note='F37. 글자는 읽히지 않게'),
  st(30.0, beat='한 획', cond='B-12 천도(시즌 1)', cam={'mode': 'close', 'to': 'plague_list_last', 'time': 1.5}, act='빈 마지막 줄에 아주 희미하게 붓 한 획', note='흑월의 붓(도감 수집품)과 같은 결'),
  st(36.0, beat='아홉째 권', cam={'mode': 'push', 'to': 'ninth_page', 'time': 2.0, 'zoom': 1.4}, act='책상 가운데 명부 아홉째 권의 한 장. 인이 찍혀야 할 자리가 비어 있다', note='F38'),
  st(46.0, beat='마지막 쪽지', cam={'mode': 'close', 'to': 'last_note', 'time': 2.0}, act='먹이 아직 마르지 않은 쪽지',
     ui={'note_card': '아홉째 인을 찾으러 간다. 네 쪽지는 여기 두고 간다. 이제 내 쪽지는 네가 읽어라.', 'note_card_time': 7.0}),
  st(58.0, beat='빈 서가', cam={'mode': 'cut', 'to': 'archive_ninth', 'framing': '문서 창고 아홉째 칸, 먼지 없는 빈 서가'}, act='문서 창고 아홉째 칸 빈 서가 뒤 문이 열려 있다', req=['cut.door.slide(오래된 나무 문이 밀려 열림)']),
  st(70.0, cam={'mode': 'fade_out', 'time': 1.0}, ui={'world_change': '⑨ 금줄이 풀린다(아홉째 칸 뒤 문)'}, note='이후 5막(⑨ 첫 진입)까지 쪽지가 오지 않는다 — 침묵이 연출'),
 ]}
CUTS += [C16]

# ═════════ 5막 ⑨ ═════════
C17 = {'id': 'C-17', 'branch': '먹지기를 만나다', 'trigger': '⑨ 보스 단서를 2개 모은 다음 밤, 도장 없는 장터 끝 바위 가까이', 'duration': 50.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 얼굴은 갓 아래 먹 그림자. 이후 ⑨에선 먹지기가 멀리 실시간으로 보인다(따라가면 단서 쪽 — 길잡이)',
 'steps': [
  st(0.0, beat='표시', cam={'mode': 'fade_in', 'time': 1.0, 'framing': '장터 끝 바위, 먹물 묻은 소매'}, act='먹물 묻은 소매의 사람이 바위에 붓으로 표시를 한다', sfx=['cut.brush.stroke', 'amb.weather.fog']),
  st(10.0, beat='봄', cam={'mode': 'two_shot', 'a': 'keeper', 'b': 'player', 'time': 2.0, 'framing': '둘 사이에 바위'}, act='그가 나를 본다. 오래 본다', note='10초 그대로. 카메라도 움직이지 않는다'),
  st(24.0, beat='종이 한 장', cam={'mode': 'close', 'to': 'rock', 'time': 1.5}, act='품에서 종이 한 장을 꺼내 바위 위에 놓는다', req=['cut.paper.set(종이를 돌 위에 놓는 소리)']),
  st(32.0, beat='떠남', cam={'mode': 'hold', 'framing': '안개 속으로 멀어지는 등'}, act='그가 안개 속으로 걸어간다'),
  st(40.0, beat='쪽지', ui={'note_card': '늦었다. 반갑다. 인은 굴에 있다. 나는 문지기한테 가 보겠다.', 'note_card_time': 6.0}, act='1막부터 받던 그 글씨'),
  st(50.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'map_mark': '먹지기 붓 표시 바위(⑨ 기억 지도에 처음으로 그려짐)'}),
 ]}
CUTS += [C17]
CUTS += [
 intro('B-17', '아홉째 문 앞 싸움 원에 처음 들어설 때(NinthGate에 처음 들어간 다음 밤)', [
  st(0.0, cam={'mode': 'crane', 'dir': 'up', 'from': 'low', 'to': 'boss', 'time': 1.6, 'zoom': 1.1, 'framing': '문지기를 아래에서, 문 위 인 자리까지'}, act='아홉째 문. 문 위 인 자리에 붉은 자국만. 문 앞에 거대한 문지기', sfx=['amb.weather.fog']),
  st(1.6, cam={'mode': 'close', 'to': 'boss_face', 'time': 0.8}, act='눈꺼풀이 철사로 꿰어 올려져 있다', note='공포가 아니라 슬프게 — 잠든 적 없는 사람의 얼굴(아트 메모)'),
  st(2.8, act='문지기가 종을 친다. 제 귀에 대고', sfx=['sfx.bell']),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '아홉째 문지기', 'seal_icon': 'missing'}, note='전투: 종 박자가 늘어지는 1.5초 동안 존다 — 때리지 말고 문을 빠져나가려는 혼을 천도해 들여보내라')], 4.5),
 kneel('B-17', '문지기가 무릎 꿇는다. 눈은 여전히 감기지 않는다'),
 noclue('B-17', '문지기 머리 위 명부 인 자리가 비어 있다가 꺼진다. 종이 한 번 울린다'),
 tendo('B-17', [
  st(1.8, cam={'mode': 'close', 'to': 'boss_face', 'time': 1.5}, act='문지기가 눈꺼풀의 철사를 푼다', req=['cut.wire.untie(가는 쇠줄 풀리는 소리)']),
  st(4.0, act='처음으로 눈을 감는다', note='3초 그대로. 소리 없음'),
  st(7.0, cam={'mode': 'pull', 'zoom': 0.8, 'time': 1.5}, act='문 둘레가 기억 지도로 그려진다. 문 옆 빈 초소에 등불이 켜진다(빈 관할 쉼터)', sfx=['cut.lantern.light']),
  st(8.5, act='문지기가 빛으로 흩어진다', sfx=['cut.dissolve'])], dur=10.0, first='명부 아홉째 권이 펼쳐진다. 인 자리는 비어 있다. 획만 모인다', fx='strokes_join_noseal'),
 pahon('B-17', ['대폭발. 종이 깨진다', '아홉째 문이 열린 채 흔들린다', '육모방망이가 문턱에 떨어진다'], '문지기의 육모방망이(⑨~⑩ 잠긴 상자를 부숨)'),

 intro('B-18', '인장 굴 싸움 원에 처음 들어설 때(SealCave에 처음 들어간 다음 밤)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '굴 벽 가득 이마 높이 붉은 자국'}, act='굴 벽에 이마 높이로 붉은 자국 수백. 그 앞에 인을 안은 혼', sfx=['amb.mine.shaft']),
  st(1.8, cam={'mode': 'close', 'to': 'boss', 'time': 0.8}, act='그가 인을 제 이마에 찍는다. 찍히지 않는다. 붉은 물만 흐른다', req=['cut.seal.thud(돌도장이 이마에 닿는 둔한 소리)']),
  st(3.2, act='또 찍는다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '인을 훔친 혼', 'seal_icon': 'missing'}, note='전투: 붉은 인 자국 장판 안에서는 잠깐 이름을 얻어 천도 −1초(나에게도)')], 4.5),
 phase('B18-GIFT', '맺힘 30% — 빈 나무 조각(숨은 선택)', '맺힘 30%, 시즌 1 B-11 천도로 받은 도감 "빈 나무 조각"이 있을 때만', 3.0, [
  st(0.0, cam={'mode': 'two_shot', 'a': 'player', 'b': 'boss', 'time': 0.5}, act='그가 다시 이마에 인을 찍으려다 실패한다. 3초 동안 손이 멈춘다', ui={'hint_icon': '빈 나무 조각 건네기(F)'}),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3}, note='건네면 B18-GIFT-TENDO로. 단서 수와 상관없이 천도 가능')]),
 {'id': 'B18-GIFT-TENDO', 'branch': '숨은 선택 — 빈 나무 조각', 'trigger': 'B18-GIFT 중 빈 나무 조각을 건넸을 때', 'duration': 8.0, 'input_lock': True,
  'world': 'pause_enemies', 'skippable': True, 'lines': 0,
  'note': '왕초가 새기려다 못 한 이름이 기억 연출로 새겨진다. 글자는 읽히지 않게. 그 뒤 처결 대기에서 단서와 상관없이 천도 가능',
  'steps': [
   st(0.0, cam={'mode': 'close', 'to': 'wood_piece', 'time': 1.0, 'zoom': 1.6}, act='빈 나무 조각을 받아 든다'),
   st(1.5, cam={'mode': 'hold', 'vignette': 0.5, 'vignette_color': mem['B-11'].get('tint')}, act='다리 밑 기둥, 숯을 든 왕초의 손이 보인다(기억 연출). 조각에 획이 새겨진다', sfx=['cut.chisel.tap'], note='시즌 1 ⑥ 다리 밑의 색'),
   st(4.5, act='그가 이마 대신 조각에 인을 찍는다 — 찍힌다', sfx=['cut.seal.set']),
   st(6.0, cam={'mode': 'close', 'to': 'boss_face', 'time': 1.0}, act='그가 조각을 가슴에 안는다'),
   st(8.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'tendo_unlocked': True, 'special_memory': 'M-B18 뒤에 한 장면이 더 붙는다(왕초의 손)'})]},
 kneel('B-18', '그가 무릎 꿇는다. 인을 놓지 않는다'),
 noclue('B-18', '그의 이마에 붉은 물만 번진다. 인은 찍히지 않는다'),
 tendo('B-18', [
  st(1.8, act='그가 인을 두 손으로 내민다'),
  st(4.0, act='먹지기가 굴 입구에 와 있다. 인을 받아 간다', note='얼굴은 그림자. 다음 C-18(천도판)'),
  st(6.0, act='그가 빛으로 흩어진다. 벽의 붉은 자국들이 하나씩 옅어진다', sfx=['cut.dissolve'])], dur=7.5, first='명부 아홉째 권이 펼쳐진다. 인 자리가 처음으로 차오른다', fx='strokes_join_seal_return'),
 pahon('B-18', ['대폭발. 인이 깨진다', '인의 조각들이 굴 바닥에 흩어진다', '벽의 붉은 자국은 그대로 남는다'], '인의 조각(최강 룬)'),
]
C18 = {'id': 'C-18', 'branch': '⑨ 끝 — 먹지기, 자기 이름을 적다(천도/파혼 갈래)', 'trigger': 'B18-TENDO 또는 B18-PAHON 끝', 'duration': 60.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. variant A = B-18 천도 / B = 파혼. 먹지기의 이름은 화면에 크게 나오지 않는다(카메라가 너무 멀다). 도감에만. 또렷함은 지금까지 천도한 혼 300 이상(qa 합의)',
 'steps': [
  st(0.0, beat='굴 앞', variant={'A': {'camera': {'mode': 'fade_in', 'time': 1.0, 'framing': '굴 앞, 먹지기의 두 손'}, 'action': '먹지기가 온전한 아홉째 인을 두 손으로 받는다'},
                                'B': {'camera': {'mode': 'fade_in', 'time': 1.0, 'framing': '굴 바닥, 먹지기의 소매'}, 'action': '먹지기가 인의 조각들을 하나씩 주워 소매에 넣는다'}}),
  st(12.0, beat='찍기', variant={'A': {'camera': {'mode': 'crane', 'dir': 'up', 'time': 8.0, 'framing': '빈 고을 전체를 높이서'}, 'action': '명부 아홉째 권에 인을 찍는다. 백 년치 이름들에 한꺼번에 붉은빛이 번진다. 빈 고을 집집마다 문패가 생긴다',
                                     'sfx': ['cut.seal.set']},
                               'B': {'camera': {'mode': 'close', 'to': 'ledger', 'time': 2.0}, 'action': '조각 하나로 이름 하나에 찍는다. 붉은빛이 하나 켜진다. 나머지는 어둡다', 'sfx': ['cut.seal.set']}}),
  st(28.0, beat='제 이름', cam={'mode': 'pull', 'zoom': 0.6, 'time': 4.0, 'framing': '아주 멀리, 명부 여백에 붓을 대는 먹지기'}, act='먹지기가 명부 여백에 처음으로 자기 이름을 적는다', sfx=['cut.brush.write'],
     ui={'collection': '먹지기 항목에 이름 기록(천도 300 이상이면 또렷, 아니면 번짐)'}, note='화면에선 읽히지 않는 거리. 이름 글은 이 파일에 없다(시즌 4 고리)'),
  st(40.0, beat='새벽', cond='A', cam={'mode': 'hold', 'framing': '빈 고을 위로 처음 드는 새벽빛'}, act='⑨에 처음으로 새벽이 온다. 안개가 걷힌다', req=['amb.dawn.birds(새벽 새 한두 마리)']),
  st(48.0, beat='쪽지', variant={'A': {'ui': {'note_card': '⑩으로 가라. 처음이 거기 있다. 나는 인을 돌려놓고 뒤따라가겠다.', 'note_card_time': 6.0}},
                                'B': {'ui': {'note_card': '⑩으로 가라. 나는 조각을 다 찍고 가겠다. 오래 걸릴 거다.', 'note_card_time': 6.0}}}),
  st(60.0, cam={'mode': 'fade_out', 'time': 1.0}, ui={'world_change': '⑩ 금줄(물막이 둑 남쪽 안개 벽)이 걷힌다. 안개 벽 앞 바위에 먹지기 붓 표시'}),
 ]}
CUTS += [C18]

# ═════════ 5막 ⑩ ═════════
CUTS += [
 intro('B-19', '처음 마을 우물터 싸움 원에 처음 들어설 때(WellYard에 밤에 처음 들어간 다음 새벽 틈 이후의 밤)', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '우물과 그 곁에 선 차사, 늘 같은 새벽빛'}, act='처음 마을 우물터. 실이 다 풀린 검은 갓. 사슬이 아니라 새끼줄을 쥔 차사가 우물 쪽을 본다', req=['amb.dawn.still(바람 없는 새벽, 아주 고요)']),
  st(1.8, cam={'mode': 'hold', 'framing': '우물 쪽으로 걸어가는 두 그림자'}, act='따뜻한 빛 하나(아이)와 그것을 끌어안은 그림자(어미)가 우물 쪽으로 간다', note='얼굴 없음. 어미의 이름은 어디에도 쓰지 않는다'),
  st(3.2, act='차사가 새끼줄을 든다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '첫 차사', 'seal_icon': 'missing'}, note='전투: 그림자를 먼저 파혼하면 쉬워지지만 그의 맺힘이 회복된다. 사슬로 붙잡아 3초 버티면 −12%')], 4.5),
 phase('B19-P30', '맺힘 30% — 한 줄', '맺힘 30%', 4.0, [
  st(0.0, cam={'mode': 'two_shot', 'a': 'player', 'b': 'boss', 'time': 0.6, 'zoom': 1.15}, act='첫 차사가 새끼줄을 늘어뜨리고 나를 본다'),
  st(0.8, line=say(BC['B-19']['line'], 'B-19', 'bubble', 2.8), note='시즌 2 보스 말풍선 1줄(첫 차사의 첫 대사)'),
  st(4.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3})],
  note='전투는 멈추지 않는다(적 공격만 0.8초 늦춤)'),
 kneel('B-19', '첫 차사가 무릎 꿇는다. 새끼줄을 놓지 않는다. 우물 쪽을 본다'),
 noclue('B-19', '첫 차사 머리 위 명부 인 자리가 비어 있다가 꺼진다. 우물 쪽에서 같은 새벽이 다시 시작된다'),
 tendo('B-19', [
  st(1.8, cam={'mode': 'hold', 'framing': '우물가, 빛과 그림자'}, act='아이의 빛이 우물을 지나간다. 그림자는 깨지지 않고 그 곁에 머문다 — 처음으로 깨뜨리지 않고 끝나는 새벽'),
  st(4.5, cam={'mode': 'cut', 'to': 'chain_graves', 'framing': '사슬 무덤을 낮게, 끝까지'}, act='사슬 무덤의 녹슨 사슬마다 이름 획이 돌아온다(읽히지 않게)', sfx=['cut.seal.set']),
  st(6.5, cond='B-12 천도(시즌 1)', cam={'mode': 'close', 'to': 'ledger_margin', 'time': 1.0}, act='명부 한 줄에 획이 돌아오는 연출만', ui={'collection_locked': '흑월 본명 칸(빈칸 테두리만, 7막 F62까지 잠금)'},
     note='글자를 띄우지 않는다(기획 10-25 채택)'),
  st(8.0, act='첫 차사가 새끼줄을 우물가 말뚝에 감아 두고 빛으로 흩어진다', sfx=['cut.dissolve'])], dur=9.5),
 pahon('B-19', ['대폭발. 새끼줄이 끊어진다', '우물가의 그림자가 가루로 흩어진다. 아이의 빛은 우물을 지나간다', '끊어진 새끼줄이 사슬처럼 땅에 떨어진다'], '첫 사슬(전설 무기, 새끼줄 모양)'),
]

B20 = [
 intro('B-20', '물막이 바닥에 처음 들어설 때(B-19 처결 다음 첫 밤, 또는 ⑩ 첫 진입 뒤 5번째 새벽이 지난 밤 강제)', [
  st(0.0, cam={'mode': 'crane', 'dir': 'up', 'from': 'riverbed', 'to': 'boss', 'time': 3.0, 'zoom': 0.7, 'framing': '강바닥에서 산처럼 솟는 덩어리, 위는 화면 밖'}, act='강바닥. 덩어리가 산처럼 솟는다', sfx=['amb.river.mist']),
  st(3.0, act='귀를 대지 않아도 이름이 들린다. 수천 개가 한꺼번에', req=['amb.names.many(수천 사람이 한꺼번에 낮게 부르는 소리 — 말은 안 들리게)'], note='S-044 기억과 같은 소리'),
  st(6.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'boss_bar': '큰 물막이', 'dam_gauge': 'show'}, note='크기 = 물막이 눈금 + 시즌 1 파혼 수')], 6.0),
 phase('B20-P2', '단계 2 — 내가 깨뜨린 것들', '단계 1 끝', 6.0, [
  st(0.0, cam={'mode': 'push', 'to': 'boss_surface', 'time': 1.0, 'zoom': 1.2}, act='덩어리 표면에 내가 파혼한 혼의 얼굴들이 떠오른다. 공격하지 않고 나를 본다', note='플레이 기록. 쪽지를 주웠으면 이름 획이 떠 있어 부를 수 있다. 벌이 아니라 거울'),
  st(6.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4})]),
 phase('B20-P3', '단계 3 — 첫 가루', '단계 2 끝', 6.0, [
  st(0.0, cam={'mode': 'push', 'to': 'boss_core', 'time': 1.5, 'zoom': 1.4, 'framing': '덩어리 가장 깊은 곳, 가장 오래된 조각 하나'}, act='덩어리 가장 깊은 곳이 열린다. 가장 오래된 조각 하나', ui={'hint_icon': '사슬로 붙잡아 버티기'}),
  st(6.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, note='이 조각은 부를 수 없다(어미의 이름 — 시즌 4 고리). 붙잡아 두는 동안 나머지 덩어리가 그 조각을 놓아준다')]),
 {'id': 'B20-KNEEL', 'branch': '처결 대기(풀어내기 / 파혼)', 'trigger': '보스 맺힘 0', 'duration': 1.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '천도 대신 풀어내기. 조건 R/S ≥ 0.6(R = 천도한 혼 + 주운 이름 쪽지 + 이은 이름, S = 물막이 크기). 모자라면 파혼만',
  'steps': [st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.1}, act='덩어리가 허물어지기 직전에 멈춘다', sfx=['sfx.kneel']),
            st(0.4, ui={'kneel_timer': 7.0, 'unravel_ready': 'R/S >= 0.6 ? steady : flicker'}),
            st(1.5, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3})]},
 {'id': 'B20-NOCLUE', 'branch': '처결 대기(풀어내기 불가)', 'trigger': 'R/S < 0.6에서 풀어내기 입력', 'duration': 1.0, 'input_lock': False, 'world': 'run', 'skippable': False,
  'steps': [st(0.0, ui={'toast': '부를 이름이 모자란다.', 'toast_time': 1.0}, sfx=['cut.seal.fade'], note='안내일 뿐. 대기 시간은 계속 흐른다')]},
]
CUTS += B20

C20A = {'id': 'C-20A', 'branch': '시즌 2 끝 — 풀어내기판', 'trigger': 'B-20 풀어내기 캐스팅 완료', 'duration': 100.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': '0~1',
 'note': '대사는 B-19를 천도했을 때만 1줄(첫 차사의 두 번째이자 마지막 대사). 파혼했으면 같은 말이 먹지기 쪽지로 온다',
 'steps': [
  st(0.0, beat='풀림', cam={'mode': 'hold', 'zoom': 1.0, 'vignette': 0.5, 'vignette_color': mem['B-20'].get('tint')}, act='덩어리가 이름 하나하나로 풀려 강물에 실린다', req=['cut.names.release(이름들이 하나씩 풀려 흩어지는 소리)']),
  st(4.0, beat='기억 줄', line=say(mem['B-20']['memory'], 'B-20', 'memory', 4.0), note='기억 M-B20(★F46 전모)'),
  st(10.0, beat='강이 흐른다', cam={'mode': 'crane', 'dir': 'up', 'time': 10.0, 'framing': '물막이 바닥에서 강 상류 쪽으로 길게'}, act='강이 흐른다. 물빛이 먹빛에서 맑아진다', req=['cut.river.flow(막혔던 물이 흐르기 시작)']),
  st(22.0, beat='줄이 움직인다', cam={'mode': 'cut', 'to': 'ferrytown', 'framing': '⑦ 빈 나루 마을, 줄을 옆으로 길게'}, act='⑦ 빈 나루 마을. 줄이 움직인다. 배가 늘어난다 — 두 척, 세 척, 그 이상'),
  st(32.0, beat='보낸 사람들', cam={'mode': 'track', 'to': 'boarding', 'time': 10.0, 'zoom': 1.1}, act='시즌 1에서 내가 보낸 사람들이 배에 오른다. 박돌쇠가 오르며 나를 돌아본다',
     note='플레이 기록. 박돌쇠를 파혼했으면 그 자리는 빈 채로 지나간다. 이름 글 없음'),
  st(44.0, beat='사공', cam={'mode': 'close', 'to': 'ferryman_mouth', 'time': 2.0}, act='사공이 노를 젓는다. 입술이 움직인다. 소리는 없다', req=['cut.oar.row(노 젓기)'], note='어미의 이름 — 글로도 소리로도 내지 않는다'),
  st(52.0, beat='저편', cam={'mode': 'follow', 'to': 'boats', 'time': 8.0, 'framing': '배들이 안개 속으로'}, act='배들이 강 한가운데를 지나 저편 안개 속으로 들어간다'),
  st(64.0, beat='돌아옴', cam={'mode': 'hold', 'framing': '같은 안개, 같은 자리'}, act='…배가 돌아온다. 저편에 닿지 못하고. 사람들이 탄 채로. 혼들이 어리둥절하게 서 있다', note='5초 그대로. 음악도 멈춘다'),
  st(76.0, beat='첫 차사', cond='B-19 천도', cam={'mode': 'two_shot', 'a': 'player', 'b': 'first_chasa', 'time': 1.5, 'framing': '줄 끝, 첫 차사와 나'},
     line=say('혼만으로는 못 건넌다. 백이 아직 물 밑에 있다.', 'B-19', 'bubble', 3.2), note='첫 차사의 두 번째이자 마지막 대사(F47)'),
  st(76.0, beat='첫 차사', cond='B-19 파혼', ui={'note_card': '혼만으로는 못 건넌다고 한다. 백이 아직 물 밑에 있다고.', 'note_card_time': 5.0}, act='명부 여백 먹지기 쪽지'),
  st(88.0, beat='끝', cam={'mode': 'fade_out', 'time': 3.0}, ui={'small_caption': '시즌 2 줄과 먹방 — 끝', 'fact_on': 'F46'}),
  st(100.0, act='크레딧 또는 시즌 3 대기 화면'),
 ]}
C20B = {'id': 'C-20B', 'branch': '시즌 2 끝 — 파혼판', 'trigger': 'B-20 처결 대기 중 파혼 입력', 'duration': 80.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 강은 뚫리지만 사납게. 시즌 3 고리(배가 돌아온다, 백이 물 밑에)는 풀어내기판과 같다',
 'steps': [
  st(0.0, beat='터짐', cam={'mode': 'shake', 'strength': 'big', 'time': 1.0}, act='덩어리가 터진다', sfx=['sfx.pahon.burst']),
  st(2.0, beat='사나운 강', cam={'mode': 'follow', 'to': 'current', 'time': 10.0, 'framing': '물살을 따라 하류로'}, act='강이 사납게 흐른다. 가루가 하류로 쓸려 간다', req=['cut.river.rush(거센 물살)'], note='다음 시즌 어딘가에 다시 쌓일 것 — 말하지 않는다'),
  st(16.0, beat='흩어진 줄', cam={'mode': 'cut', 'to': 'ferrytown', 'framing': '⑦ 빈 나루 마을, 흩어지는 줄'}, act='줄이 흩어진다. 물살에 놀란 혼들이 다시 떠도는 혼이 되어 기슭으로 번진다. 일부만 배에 오른다'),
  st(34.0, beat='저편', cam={'mode': 'follow', 'to': 'boats', 'time': 8.0}, act='배가 저편으로 간다'),
  st(46.0, beat='돌아옴', cam={'mode': 'hold', 'framing': '같은 안개'}, act='…돌아온다'),
  st(56.0, beat='쪽지', ui={'note_card': '강은 뚫렸다. 그런데 배가 닿지 않는다. 혼만으로는 못 건넌다고 한다. 백이 아직 물 밑에 있다고.', 'note_card_time': 7.0}, act='명부 여백 먹지기 쪽지'),
  st(68.0, beat='끝', cam={'mode': 'fade_out', 'time': 3.0}, ui={'small_caption': '시즌 2 줄과 먹방 — 끝', 'karma': '+3'}),
  st(80.0, act='크레딧 또는 시즌 3 대기 화면'),
 ]}
CUTS += [C20A, C20B]

for c in CUTS:
    c['steps'].sort(key=lambda x: x['t'])
    promote(c)

# ───── 자체 검사 ─────
ids = [c['id'] for c in CUTS]
assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
need = {x['id'] for x in S2['cutscenes']}
assert need <= set(ids), need - set(ids)
blob = json.dumps(CUTS, ensure_ascii=False)
for w in ('초혼', '동이', '춥', '추워', '한기', '으슬', '시왕', '염라', '재판', '형벌'):
    assert w not in blob, w
# 말풍선(bubble) 대사 수: B-19 한 줄 + C-20A 한 줄
bubbles = [(c['id'], s['line']['text']) for c in CUTS for s in c['steps'] if s.get('line', {}).get('style') == 'bubble']
assert len(bubbles) == 2, bubbles
# 컷 길이 안에서 끝나는지
for c in CUTS:
    assert all(s['t'] <= c['duration'] for s in c['steps']), c['id']

data = {
 '_설명': '시즌 2 「줄과 먹방」 실시간 컷신 대본(4막 ⑦⑧ · 5막 ⑨⑩). tools/cutscenes_s2.py로 생성. 형식은 cutscenes_s1.json과 같다. 서사 2026-10-25',
 'rules': {
  'protagonist_lines': 0,
  'lines': '시즌 2 보스 말풍선은 B-19 "그 이름을 못 찾았다. 그래서 깨뜨렸다. 너는 찾았나."(B19-P30)와 C-20A 첫 차사 "혼만으로는 못 건넌다. 백이 아직 물 밑에 있다."(B-19 천도 때만) 두 줄뿐. 기억 줄(memory)·쪽지(note_card)는 대사로 세지 않는다',
  'silence': '⑦~⑩엔 산 사람이 없다. 저승은 나를 보지만 아무도 말을 걸지 않는다 — 시선·몸짓·쪽지로만',
  'hidden': '먹지기 얼굴·이름 글, 어미의 이름, 사공의 정체, 흑월 본명 글자(7막 F62)는 화면에 쓰지 않는다',
  'ledger': '시즌 2 보스 천도는 명부 이름 글자를 보여 주지 않는다(획이 모이는 것만, ledger_fx). ⑨는 인이 없어 strokes_join_noseal, B-18 천도만 인이 돌아온다',
  'rite': 'RITE-BAEUNG·RITE-JEONGSEO·RITE-JOIN은 틀이다. {stopped}·{moving}·{fragment} 자리에 memories_act4·5의 글을 넣는다',
  'name_slip': '⑦~⑩ 파혼 컷(…-PAHON)의 name_slip: 0.3초에 이름 쪽지가 떠올라 1.5초 머문다. 사슬로 낚으면 물막이 눈금 절반',
  'time': 't는 컷 시작부터 초. duration 안에서 끝난다',
  'camera': 'cutscenes_s1.json rules.camera와 같다(pan·push·pull·hold·cut·shake·return·crane·track·follow·orbit·two_shot·close·fade_in/out)',
  'condition': 'condition이 붙은 박자는 그 조건일 때만. 같은 t에 조건이 다른 박자가 둘이면 맞는 하나만 쓴다',
  'variant': 'C-18의 variant.A/B = B-18 천도/파혼',
  'walkable': 'C-15는 걷기 가능 컷(input_lock false, walkable true). 카메라만 컷이 쥔다',
  'sfx': 'sfx = 있는 소리 id, sfx_request = 아직 없는 소리(사운드팀 요청). 생긴 소리는 sfx_map.promote가 옮긴다',
  'skippable': '길게 눌러 건너뛰기. 건너뛰어도 보상·단서·세계 변화는 그대로',
 },
 'cutscenes': CUTS,
}
json.dump(data, open(os.path.join(D, 'cutscenes_s2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
req = sorted({r for c in CUTS for s in c['steps'] for r in s.get('sfx_request', [])})
print(len(CUTS), 'cutscenes,', len(req), 'sfx requests')
