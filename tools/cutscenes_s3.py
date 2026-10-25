# -*- coding: utf-8 -*-
# 시즌 3 「백의 밤」 실시간 컷신 대본 — 6막(① · ⑤ · ⑦) · 7막(③ · ④ · ② · ⑥) · 8막(⑧ · ⑨ · ⑩ · 물막이 골 소).
#   여는 장면 C-21 · C-21S, 막 컷(C-23A/B · C-24 · C-27A/B · C-28 · C-30), 결말 C-31A/B/C,
#   보스 B-21~B-31(등장 · 단계 · 처결 대기 · 눕히기 불가 · 눕히기 · 깨뜨리기), 아래층 공통 틀(물 빠짐 · 떠밀림 · 거꾸로 장례 · 거꾸로 명부 · 비켜섬 …).
# 형식은 시즌 1 · 2(cutscenes_s1.json · cutscenes_s2.json)와 같다. 같은 도우미 모양(st · intro · kneel …)을 쓴다.
# 왜 시즌 2와 도우미가 조금 다른가: 시즌 3의 두 동사는 천도/파혼이 아니라 눕히기/깨뜨리기다(백 = 장례를 못 치른 몸의 넋).
#   눕히기는 "실을 끊어 무릎 꿇린 뒤 이름을 불러 눕힘", 깨뜨리기는 "즉시 폭발, 그 사람의 혼이 줄에서 돌아섬"이라 연출이 다르다.
# 원칙:
#   - 주인공 대사 0(결말 A의 대답 한 줄만 — 글은 endings_s1이 정본이라 여기엔 참조만 둔다).
#   - 시즌 3 보스 · 막 컷신 대사 0줄. 백은 말하지 않는다. 입 모양은 대사가 아니다(자막 · 소리 없음).
#   - 결말 대사 3줄(A 2 · B 1)은 이 파일에 글로 쓰지 않는다 — line_ref로 endings_s1.json을 가리킨다.
#     왜: 주인공 이름 · 그 의례 이름 · 추위 말은 endings_s1에만 두는 규칙(check_s1이 검사)이라서.
#   - 쓰지 않는 것: 먹지기의 얼굴 · 이름, 어미의 이름, 사공의 이름, 추위 말(연출 글은 "언 땅"). 흑월 본명은 B-27에서 처음 글자로.
#   - 열 시왕 · 재판 · 형벌 장면 없음(IP 선). 명부전 본당 문은 끝까지 닫혀 있다.
#   - 밤 번호를 쓰지 않는다(월드 시계). "그 구역 아래층에 처음 내려간 다음 낮 / 새벽 틈" 식으로만.
# 실행: python3 tools/cutscenes_s3.py → docs/narrative/cutscenes_s3.json
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_map import promote
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'docs', 'narrative')
mem = {s['id']: s for s in json.load(open(os.path.join(D, 'soul_memories.json'), encoding='utf-8'))['souls']}
S3 = json.load(open(os.path.join(D, 'season3_outline.json'), encoding='utf-8'))
BC = S3['boss_clues']
END = json.load(open(os.path.join(D, 'endings_s1.json'), encoding='utf-8'))['final_endings']['endings']


def st(t, cam=None, act=None, line=None, ui=None, note=None, sfx=None, req=None, cond=None, beat=None, variant=None, line_ref=None):
    """컷의 한 박자. t = 컷 시작부터 초."""
    s = {'t': t}
    if beat: s['beat'] = beat
    if cam: s['camera'] = cam
    if act: s['action'] = act
    if line: s['line'] = line
    if line_ref: s['line_ref'] = line_ref   # 글은 다른 파일(정본)에 있다 — 코드가 거기서 읽는다
    if ui: s['ui'] = ui
    if sfx: s['sfx'] = sfx
    if req: s['sfx_request'] = req
    if cond: s['condition'] = cond
    if variant: s['variant'] = variant
    if note: s['note'] = note
    return s


def memline(bid, dur=3.6):
    """백의 기억 한 줄(몸의 감각). 대사가 아니라 기억 줄 — 15줄 상한에 세지 않는다."""
    return {'speaker': bid, 'text': mem[bid]['memory'], 'style': 'memory', 'duration': dur}


def ref(ending, i):
    """결말 대사 참조. 글은 endings_s1.json final_endings.endings.<A|B>.lines_list[i]에만 있다."""
    assert END[ending]['lines_list'][i]   # 정본에 그 줄이 실제로 있는지 확인
    return {'file': 'endings_s1.json', 'path': f'final_endings.endings.{ending}.lines_list[{i}]',
            'speaker': END[ending]['lines_list'][i]['speaker'], 'style': 'voice'}


def cid(bid, kind): return f"{bid.replace('-', '')}-{kind}"


def intro(bid, trigger, steps, dur):
    return {'id': cid(bid, 'INTRO'), 'branch': '등장', 'trigger': trigger, 'duration': dur, 'input_lock': True,
            'world': 'pause_enemies', 'skippable': True, 'lines': 0, 'steps': steps}


def kneel(bid, act, timer=7.0, ready='clue>=3 ? steady : flicker', extra=None):
    """처결 대기. 시즌 3은 이름 실 대신 '실 끊김' 표시: 원념의 실(검은 물줄기)이 끊기고 백이 무릎 꿇는다."""
    steps = [st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.25}, act=act, sfx=['sfx.kneel'],
                req=['cut.thread.snap(물줄기 같은 검은 실이 끊기는 낮은 소리)'])]
    if extra: steps.append(extra)
    steps += [st(0.4, ui={'kneel_timer': timer, 'lay_ready': ready}),
              st(1.5, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3, 'zoom': 1.0})]
    return {'id': cid(bid, 'KNEEL'), 'branch': '처결 대기', 'trigger': '보스 맺힘 0', 'duration': 1.5, 'input_lock': False,
            'world': 'run', 'skippable': False, 'note': f'처결 대기 {timer:g}초와 동시에 흐른다. 입력을 막지 않는다. 대사 없음', 'steps': steps}


def noclue(bid, act, toast='이름이 닿지 않는다.'):
    return {'id': cid(bid, 'NOCLUE'), 'branch': '처결 대기(눕히기 불가)', 'trigger': '단서 2개 이하에서 눕히기 입력', 'duration': 1.0,
            'input_lock': False, 'world': 'run', 'skippable': False,
            'steps': [st(0.0, act=act, ui={'toast': toast, 'toast_time': 1.0}, sfx=['cut.seal.fade'],
                         note='안내일 뿐. 캐스팅은 시작되지 않고 대기 시간은 계속 흐른다. 깨뜨리기는 언제나 된다')]}


def lay(bid, beats, dur=9.0, light='저편 기슭에 나룻불이 하나 켜진다', light_t=None, extra_ui=None, note=None, first=None):
    """눕히기 컷. 머리(실 끊김 → 이름 → 기억 줄) + 보스별 박자 + 저편 나룻불 + 보상."""
    b = BC[bid]
    head = [st(0.0, cam={'mode': 'hold', 'zoom': 1.3, 'vignette': 0.6, 'vignette_color': mem[bid].get('tint')},
               act=first or '명부가 펼쳐지고 이름 획이 모인다. 백의 손목에서 검은 실이 풀려 내려앉는다',
               ui={'ledger_fx': 'strokes_join_then_lay'}, sfx=['cut.ledger.open', 'cut.seal.set'],
               req=['sfx.laydown(몸이 젖은 흙에 천천히 눕는 낮은 소리)']),
            st(1.0, line=memline(bid), sfx=['sfx.clue'], note=f"기억 M-{bid.replace('-', '')}(★{b['decisive']} 전모)")]
    lt = light_t if light_t is not None else dur - 2.0
    tail = [st(lt, beat='저편 나룻불', cam={'mode': 'cut', 'to': 'far_shore', 'framing': '강 하류 끝, 안개 너머 저편 기슭'}, act=light, sfx=['cut.lantern.light'],
               note='시즌 3 진행 막대(far_lights). 1막에 꺼져 있던 그 불(F3)'),
            st(dur, cam={'mode': 'return', 'to': 'player', 'time': 0.5},
               ui=dict({'fact_on': b['decisive'], 'reward': {'memory': 'M-' + bid.replace('-', '')}, 'world_change': b['lay'], 'sent_count': '+1(보낸 사람 수)'}, **(extra_ui or {})))]
    c = {'id': cid(bid, 'LAY'), 'branch': '눕히기', 'trigger': '눕히기 캐스팅 2.0초 완료', 'duration': dur, 'input_lock': True,
         'world': 'pause_enemies', 'skippable': True, 'lines': 0, 'steps': head + beats + tail}
    if note: c['note'] = note
    return c


def brk(bid, beats, reward_item):
    """깨뜨리기 컷. 즉시 · 큰 폭발. 그 사람의 혼이 ⑦ 줄에서 돌아서는 장면을 짧게 끼운다(대가를 보여 줌, 벌이 아니라 결과)."""
    steps = [st(0.0, cam={'mode': 'shake', 'strength': 'big', 'time': 0.5}, act=beats[0], sfx=['sfx.pahon.burst'],
                req=['cut.bones.crumble(젖은 흙과 뼈가 함께 부서지는 둔한 소리)']),
             st(0.3, ui={'ledger_fx': 'strokes_scatter'}, act='명부의 그 줄이 흩어진다', sfx=['cut.stroke.scatter'])]
    steps += [st(0.8 + 0.7 * i, act=a) for i, a in enumerate(beats[1:])]
    n = len(beats) - 1
    steps.append(st(round(0.8 + 0.7 * n, 1), cam={'mode': 'cut', 'to': 'queue_above', 'time': 0.6, 'framing': '⑦ 줄, 한 혼의 등'},
                    act='위쪽 ⑦ 줄에서 그 혼이 강을 등지고 돌아선다', note='0.6초. 얼굴은 보이지 않는다'))
    end = round(0.8 + 0.7 * n + 1.0, 1)
    steps.append(st(end, ui={'reward': {'item': reward_item}, 'karma': '+3', 'karma_warning': '업 단계 경계를 넘으면 화면 경고',
                             'world_change': BC[bid]['break']}, note='대사 없음'))
    return {'id': cid(bid, 'BREAK'), 'branch': '깨뜨리기', 'trigger': '처결 대기 중 깨뜨리기 입력', 'duration': end, 'input_lock': False,
            'world': 'run', 'skippable': False, 'note': '즉시. 폭발로 화면의 잡몹이 밀려나 안전', 'steps': steps}


def phase(id_, branch, trigger, dur, steps, note=None):
    c = {'id': id_, 'branch': branch, 'trigger': trigger, 'duration': dur, 'input_lock': False, 'world': 'run', 'skippable': False, 'steps': steps}
    if note: c['note'] = note
    return c


CUTS = []

# ═════════ 시즌 3 여는 장면 ═════════
C21 = {'id': 'C-21', 'branch': '시즌 3 여는 장면', 'trigger': 'C-20A 또는 C-20B 끝(시즌 2 이어 하기) / C-21S 끝(새 시작)', 'duration': 70.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 시즌 2 끝 "배가 돌아온다" 바로 뒤. 줄 선 혼들 발목의 실을 따라 내려가 물 빠진 강바닥을 처음 본다. variant A = B-20 풀어내기 / B = 파혼',
 'steps': [
  st(0.0, beat='돌아온 배', cam={'mode': 'fade_in', 'time': 1.5, 'framing': '⑦ 나루, 돌아온 배에서 내리는 혼들'}, act='돌아온 배에서 혼들이 내린다. 다시 줄 끝에 선다', sfx=['amb.river.mist'],
     variant={'A': {'action': '돌아온 배에서 혼들이 내린다. 말없이 다시 줄 끝에 선다'},
              'B': {'action': '돌아온 배에서 혼들이 내린다. 몇은 줄로 가지 못하고 기슭을 떠돈다'}}),
  st(8.0, beat='발목', cam={'mode': 'tilt', 'dir': 'down', 'time': 4.0, 'framing': '줄 선 혼들의 발목, 물가'}, act='카메라가 처음으로 혼들의 발목까지 내려간다. 발목마다 검은 물줄기 같은 실이 한 가닥씩 물속으로 내려가 있다',
     note='실은 물빛보다 조금만 더 검게. 시즌 2 내내 있었지만 카메라가 거기까지 내려가지 않았다'),
  st(16.0, beat='물속으로', cam={'mode': 'follow', 'to': 'thread', 'time': 10.0, 'height': 'low', 'framing': '실 한 가닥을 따라 물속으로'}, act='실 한 가닥을 따라 물속으로 내려간다. 바닥이 보이지 않는다',
     req=['amb.underwater.low(물속의 먹먹한 낮은 울림)']),
  st(28.0, beat='저녁', cam={'mode': 'cut', 'to': 'soljae_pool', 'framing': '솔고개 물막이 골 나루, 해 질 녘'}, act='해 질 녘 솔고개 물막이 골. 강물이 두 분 동안 소리를 내며 빠진다(연출에선 압축)',
     sfx=['cut.water.recede'], note='시즌 3의 물 주기 첫 시연(world.water_cycle). 실은 상류로도 이어져 있다는 것을 장소 전환으로 보여 준다'),
  st(38.0, beat='누운 그림자', cam={'mode': 'crane', 'dir': 'down', 'time': 8.0, 'zoom': 0.8, 'framing': '물 빠진 둑 밑과 소 밑, 위에서'},
     act='물 빠진 바닥에 누운 그림자들이 드러난다. 흙탕에 몸들. 박다 만 말뚝 셋. 소 밑엔 뒤집힌 나룻배 한 척', note='몸은 그림자 실루엣으로만(아트: 공포가 아니라 슬프게)'),
  st(48.0, beat='열한 몸', cam={'mode': 'push', 'to': 'eleven', 'time': 3.0, 'zoom': 1.2, 'framing': '둑 밑 한가운데, 서로 팔을 엮은 몸들'},
     act='둑 밑 한가운데 서로 팔을 엮은 몸 열하나. 맨 끝 오른팔이 비어 있다', note='F52 복선. 설명하지 않는다. 카메라가 빈 팔에서 0.5초 느려질 뿐'),
  st(56.0, beat='사슬이 닿다', cam={'mode': 'close', 'to': 'chain_tip', 'time': 2.0, 'zoom': 1.6, 'framing': '차사의 사슬 끝과 젖은 바닥'},
     act='차사가 바닥으로 내려선다. 사슬 끝이 처음으로 바닥에 닿는다. 사슬이 조금 무거워진다', sfx=['cut.chain.drag'],
     note='시즌 3 내내 사슬은 바닥에 끌린다(사슬 끝이 어디로 이어지는지는 6막 끝 F56에서)'),
  st(62.0, ui={'note_card': '물이 빠지는 밤에만 내려갈 수 있다. 몸들은 아래에 있다. 동틀 무렵엔 올라와라.', 'note_card_time': 5.0}, act='명부 여백 먹지기 쪽지'),
  st(70.0, cam={'mode': 'return', 'to': 'player', 'time': 1.0}, ui={'region_title': '솔고개의 아래', 'hint_icon': '눕히기(E) · 깨뜨리기(R)'}, note='다음: 둑 밑(DamBed) 첫 백'),
 ]}
C21S = {'id': 'C-21S', 'branch': '시즌 3부터 시작하는 사람용 요약', 'trigger': '시즌 3 새 시작(시즌 1 · 2 기록 없음)', 'duration': 60.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 기본 상태 "시즌 1 A판 + 시즌 2 풀어내기판 + 업 12 + F9 있음 + 누적 천도 120"(season3_outline). 네 장면을 15초씩. F9의 내용은 말하지 않는다',
 'steps': [
  st(0.0, beat='서낭당', cam={'mode': 'fade_in', 'time': 1.5, 'framing': '서낭당, 당할미 등'}, act='솔고개 서낭당. 당할미가 새벽마다 사잣밥을 차린다. 짚신 한 켤레', sfx=['cut.straw.set']),
  st(15.0, beat='부르는 차사', cam={'mode': 'orbit', 'to': 'player', 'time': 10.0, 'zoom': 1.2}, act='차사가 흐린 혼 앞에서 명부를 편다. 획이 모이고 혼이 빛으로 오른다', sfx=['cut.ledger.open', 'cut.seal.set', 'cut.dissolve']),
  st(30.0, beat='줄과 배', cam={'mode': 'pull', 'zoom': 0.7, 'time': 8.0, 'framing': '끝없는 줄, 강 위 배들'}, act='삼도천 기슭 끝없는 줄. 배들이 저편으로 간다 — 그리고 돌아온다', sfx=['cut.oar.row']),
  st(45.0, beat='실', cam={'mode': 'tilt', 'dir': 'down', 'time': 4.0, 'framing': '혼의 발목에서 물속으로'}, act='혼의 발목에서 검은 실 한 가닥이 물속으로 내려간다'),
  st(60.0, cam={'mode': 'fade_out', 'time': 1.0}, note='다음: C-21의 28.0(저녁)부터'),
 ]}
CUTS += [C21, C21S]

# ═════════ 아래층 공통 틀 ═════════
# 왜 틀로 두나: 시즌 3 백 120명마다 컷을 따로 쓰면 코드와 문서가 터진다. 같은 모양은 한 번만 쓰고 {자리}에 memories_s3 글을 넣는다.
COMMON = [
 {'id': 'S3-DUSK', 'branch': '물 빠짐(아래층 열림)', 'trigger': '시즌 3, 해가 질 때마다(아래층이 있는 관할 위층에 있을 때)', 'duration': 4.0,
  'input_lock': False, 'world': 'run', 'skippable': False, 'lines': 0,
  'note': '걷기 중 흐르는 짧은 연출. 저녁 2분 동안 물이 빠지는 실제 시간은 월드 시계가 쥔다 — 이 컷은 시작 신호만',
  'steps': [st(0.0, cam={'mode': 'pull', 'zoom': 0.9, 'time': 1.0}, act='강 쪽에서 물 빠지는 소리. 내려가는 계단 금줄 앞에 물빛이 낮아진다', sfx=['cut.water.recede']),
            st(4.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'map_mark': '아래층 내려가는 계단(열림)'})]},
 {'id': 'S3-DAWN-WARN', 'branch': '새벽 경고', 'trigger': '아래층에 있을 때, 새벽 30초 전', 'duration': 2.0, 'input_lock': False, 'world': 'run', 'skippable': False, 'lines': 0,
  'note': '기획 10-25 확정(world.water_cycle). 화면 가장자리 물빛 + 물소리. 보스 싸움 중에도 똑같이',
  'steps': [st(0.0, ui={'screen_edge': 'water_glow', 'map_mark': '가장 가까운 계단'}, req=['cut.water.rise.far(멀리서 물이 차오르기 시작하는 소리)']),
            st(2.0, note='이후 30초는 그대로 플레이')]},
 {'id': 'S3-DAWN-PUSH', 'branch': '새벽 떠밀림', 'trigger': '새벽에 아래층에 남아 있을 때', 'duration': 3.0, 'input_lock': True, 'world': 'pause_enemies', 'skippable': False, 'lines': 0,
  'note': '죽지 않고 벌도 없다(기획 10-25, world.flood_loss). 보스 싸움 중이면 맺힘은 그 단계 시작 값으로 저장되어 다음 밤 그 단계부터(기획 10-25 제안, 서사 찬성 — B-23 · B-31 강제 개방 싸움도 같은 규칙인지는 기획 표가 정본)',
  'steps': [st(0.0, cam={'mode': 'shake', 'strength': 'small', 'time': 0.6}, act='물이 찬다. 차사가 물살에 떠밀려 가장 가까운 계단 위로 올라온다', req=['cut.water.rise(물이 빠르게 차오름)']),
            st(2.0, cam={'mode': 'cut', 'to': 'stairs_top', 'framing': '계단 위, 젖은 차사, 뒤로 물이 찬 아래층'}, act='계단 위. 아래층은 다시 물에 잠겨 있다'),
            st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4})]},
 {'id': 'RITE-REVERSE', 'branch': '거꾸로 장례(단서, ①~⑥ 위층 낮)', 'trigger': '그 백의 아래층에 처음 내려간 다음 낮, 위층 장례 자리 가까이', 'duration': 24.0,
  'input_lock': False, 'world': 'run', 'skippable': True, 'lines': 0, 'walkable': True,
  'data': 'memories_s3.json baek[] (funeral=reverse/carve/group) · season3_outline boss_clues[].clues(verb=거꾸로 장례)',
  'note': '대사 0. 산 사람은 차사를 보지 못한다. 장례가 끝에서 처음으로 거꾸로 감긴다. 마지막 컷은 늘 비어 있는 것(6막 = 빈 몸 자리, 7막 = 빈 비석 · 목패 · 팻말). 그 빈 것이 단서다',
  'steps': [
   st(0.0, beat='#7 끝', cam={'mode': 'fade_in', 'time': 0.8, 'framing': '장례 자리, 산 사람들이 흩어지는 뒷모습'}, act='{last}', ui={'film_fx': 'reverse'},
      req=['cut.rewind.soft(종이 넘기듯 거꾸로 감기는 부드러운 소리)'], note='화면 결은 시즌 1 장례와 같게, 움직임만 거꾸로'),
   st(8.0, beat='#4 가운데', cam={'mode': 'close', 'to': 'rite_center', 'time': 1.5}, act='{middle}'),
   st(16.0, beat='#1 빈 것', cam={'mode': 'push', 'to': 'empty_spot', 'time': 2.0, 'zoom': 1.4}, act='{empty}', note='6막: 빈 몸 자리 / 7막: 빈 비석 · 목패 · 팻말. 3초 그대로'),
   st(24.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'clue_found': '{clue_id}'})]},
 {'id': 'LEDGER-REVERSE', 'branch': '거꾸로 명부(단서, ⑦~⑩ 새벽 틈)', 'trigger': '그 백의 아래층에 처음 내려간 다음 새벽 틈, 명부 여백이 번진 자리 가까이', 'duration': 16.0,
  'input_lock': False, 'world': 'run', 'skippable': True, 'lines': 0, 'walkable': True,
  'note': '대사 0. ⑦~⑩엔 산 사람이 없어서 장례 대신 명부가 거꾸로 넘어간다. 마지막 장은 몸 칸이 빈 줄',
  'steps': [
   st(0.0, cam={'mode': 'push', 'to': 'ledger', 'time': 1.0, 'zoom': 1.4}, act='명부 장들이 뒤에서 앞으로 넘어간다', sfx=['cut.ledger.open'], req=['cut.rewind.soft(종이 넘기듯 거꾸로 감기는 부드러운 소리)']),
   st(6.0, act='{line_row}', note='이름 칸은 획만, 몸 칸이 비어 있는 줄에서 멈춘다'),
   st(12.0, cam={'mode': 'close', 'to': 'body_cell', 'time': 1.0}, act='몸 칸이 비어 있다'),
   st(16.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'clue_found': '{clue_id}'})]},
 {'id': 'BAEK-LAY', 'branch': '백 눕히기(보스 아닌 백)', 'trigger': '이름 백 처결 대기 중 눕히기 캐스팅 2.0초 완료', 'duration': 3.0,
  'input_lock': False, 'world': 'run', 'skippable': False, 'lines': 0,
  'note': '입력을 막지 않는다(직후 잡몹 2초 정지는 전투 규칙). 기억 줄은 화면 아래 한 줄로',
  'steps': [st(0.0, act='검은 실이 손목에서 풀려 내려앉는다. 백이 천천히 눕는다', sfx=['cut.seal.set'], req=['sfx.laydown(몸이 젖은 흙에 천천히 눕는 낮은 소리)']),
            st(0.6, line={'speaker': '{soul_id}', 'text': '{memory}', 'style': 'memory', 'duration': 2.4}),
            st(3.0, ui={'sent_count': '+1', 'far_light_pending': '+1(그 혼이 배에 오르면)'})]},
 {'id': 'BAEK-BREAK', 'branch': '백 깨뜨리기(보스 아닌 백)', 'trigger': '이름 백 처결 대기 중 깨뜨리기 입력', 'duration': 1.2,
  'input_lock': False, 'world': 'run', 'skippable': False, 'lines': 0,
  'steps': [st(0.0, cam={'mode': 'shake', 'strength': 'mid', 'time': 0.3}, act='백이 깨진다', sfx=['sfx.pahon.burst']),
            st(1.2, ui={'karma': '+1(덩어리는 몸당 +0.1, 덩어리 하나당 상한 +3)'})]},
 {'id': 'STEP-ASIDE', 'branch': '비켜서는 백(7 · 8막)', 'trigger': '시즌 1 · 2에서 그 사람의 혼을 천도했고, 그 백에 3m 안으로 다가갔을 때', 'duration': 4.0,
  'input_lock': False, 'world': 'run', 'skippable': False, 'lines': 0,
  'note': 'F58. 전투 없이 바로 눕힘으로 친다. 비켜선 자리는 아래층 지름길이 된다',
  'steps': [st(0.0, act='백이 스스로 일어나 한 걸음 비켜선다. 고개를 숙인다', req=['cut.soil.shift(젖은 흙에서 몸이 일어나는 소리)']),
            st(2.0, act='비켜선 자리에 흙길이 드러난다. 백이 그 옆에 눕는다', sfx=['cut.seal.set']),
            st(4.0, ui={'sent_count': '+1', 'map_mark': '아래층 지름길'})]},
 {'id': 'OWNERLESS', 'branch': '주인 없는 백 알림', 'trigger': '시즌 1 · 2에서 그 사람의 혼을 파혼했고, 그 백을 처음 볼 때', 'duration': 1.5,
  'input_lock': False, 'world': 'run', 'skippable': False, 'lines': 0,
  'note': '벌이 아니라 수고(world.ownerless). 낮 단서 1개(거꾸로 장례)를 먼저 찾으면 눕힐 수 있다',
  'steps': [st(0.0, act='백의 이마에 이름 실이 끊겨 있다', ui={'toast': '이 몸에는 이름이 닿아 있지 않다.', 'toast_time': 1.5})]},
 {'id': 'THREAD-RISE', 'branch': '위아래 짝(⑦)', 'trigger': '⑦ 줄 밑(LineBed)에서 백을 눕혔을 때', 'duration': 3.0,
  'input_lock': False, 'world': 'run', 'skippable': False, 'lines': 0,
  'note': '카메라가 잠깐 위를 올려다본다. 장례를 받은 사람의 백은 여기 없다(F54)',
  'steps': [st(0.0, cam={'mode': 'tilt', 'dir': 'up', 'time': 0.8, 'framing': '강바닥에서 수면 위 줄 선 혼들의 발바닥'}, act='바로 위 줄에서 그 혼의 발목 실이 풀려 말려 올라간다', req=['cut.thread.reel(실이 감겨 올라가는 가는 소리)']),
            st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.4})]},
 {'id': 'FAR-LIGHT-FIRST', 'branch': '저편 나룻불 처음', 'trigger': '시즌 3에서 처음으로 배가 저편에 닿은 다음 낮, 서낭당에 처음 들렀을 때', 'duration': 12.0,
  'input_lock': True, 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
  'note': '진행 막대 소개. 이후는 서낭당에서 보이는 불빛 개수로만(컷 없음). 1막에 꺼져 있던 그 불(F3)',
  'steps': [st(0.0, cam={'mode': 'hold', 'framing': '서낭당 나무 너머 먼 하류 하늘'}, act='서낭당 너머 아주 먼 하류, 낮인데도 불빛 하나가 보인다', sfx=['cut.lantern.light']),
            st(6.0, cond='당할미가 서낭당에 있을 때', act='당할미가 손을 멈추고 그 쪽을 본다. 아무 말도 하지 않는다'),
            st(12.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'far_lights': 'show'})]},
]
CUTS += COMMON

# ═════════ 6막 ① 솔고개의 아래 ═════════
CUTS += [
 intro('B-21', '소 밑(PoolBed) 뒤집힌 나룻배 앞 싸움 원에 처음 들어설 때', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '소 밑 바닥, 뒤집힌 나룻배와 뱃전을 붙든 손'}, act='물 빠진 소 밑. 뒤집힌 나룻배 뱃전을 한 몸이 두 손으로 붙들고 있다', sfx=['amb.river.mist']),
  st(1.6, cam={'mode': 'close', 'to': 'boss_hand', 'time': 0.8, 'zoom': 1.5}, act='손바닥에 엽전 다섯 닢 자국', note='시즌 1 B-01 나루 영감이 끝내 건네지 못한 열두째 손님. 이름은 쓰지 않는다'),
  st(3.0, act='배가 물살처럼 바닥을 쓸며 다가온다. 몸은 뱃전에서 손을 떼지 않는다', req=['cut.hull.scrape(뒤집힌 나무배가 바닥을 긁는 소리)']),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '마지막 손님', 'seal_icon': 'thread'}, note='전투: 백은 움직이지 않고 배가 쓸며 온다. 실이 물에 엉킨 손을 끌어올린다')], 4.5),
 phase('B21-FLOOD', '맺힘 50% — 물 차오름', '맺힘 50%', 3.0, [
  st(0.0, cam={'mode': 'pull', 'zoom': 0.9, 'time': 0.5}, act='소 밑에 물이 차오르기 시작한다. 허리까지 차면 배가 떠 실이 드러난다', req=['cut.water.rise(물이 빠르게 차오름)'],
     ui={'timer': 90.0, 'hint_icon': '배가 뜨면 드러난 실을 끊기'}),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3}, note='90초를 넘기면 그 밤은 끝(S3-DAWN-PUSH와 같은 떠밀림), 다음 밤 맺힘 50%부터(qa)')]),
 kneel('B-21', '배가 바닥에 가라앉는다. 몸이 뱃전을 붙든 채 무릎 꿇는다'),
 noclue('B-21', '몸의 손이 뱃전을 더 세게 쥔다. 이름 획이 모이다 흩어진다'),
 lay('B-21', [
  st(4.8, cam={'mode': 'close', 'to': 'boss_hand', 'time': 1.0, 'zoom': 1.5}, act='손바닥의 엽전 자국이 사라진다. 손가락이 하나씩 뱃전에서 풀린다'),
  st(6.5, cam={'mode': 'pull', 'zoom': 1.0, 'time': 1.0}, act='몸이 배 옆에 눕는다. 배도 바로 눕는다 — 처음으로 뒤집히지 않은 채로', req=['sfx.laydown(몸이 젖은 흙에 천천히 눕는 낮은 소리)']),
  st(9.0, cond='S-002 천도(시즌 1)', cam={'mode': 'close', 'to': 'far_shore_figure', 'time': 1.0}, act='저편 기슭, 불빛 옆에 흰 저고리의 사람이 손을 흔든다', note='윤 소사. 얼굴은 먼 거리로만'),
  st(9.0, cond='S-002 천도 아님', cam={'mode': 'close', 'to': 'far_shore', 'time': 1.0}, act='저편 기슭엔 불빛만 있다')], dur=11.0, light_t=8.0),
 brk('B-21', ['대폭발. 배가 판자로 부서져 떠오른다', '엽전이 바닥에 쏟아진다', '몸은 판자 사이로 가라앉는다'], '나룻배 판자(물 차오름 신호 +10초) + 엽전 ×30'),
]
CUTS[-1]['steps'].insert(3, st(0.8, sfx=['cut.coins.spill', 'cut.boat.break']))

# ═════════ 6막 ⑤ 갯마을의 아래 ═════════
CUTS += [
 intro('B-22', '곶 밑 바다굴(SeaCave) 바위 마당에 처음 들어설 때(썰물 밤에만 입구가 열린다)', [
  st(0.0, cam={'mode': 'crane', 'dir': 'down', 'time': 1.6, 'zoom': 1.0, 'framing': '바다굴 안쪽, 썰물에 드러난 바위 마당을 위에서'}, act='썰물에 드러난 바위 마당. 일곱 몸이 한 줄에 엮여 원을 돈다', sfx=['amb.sea.wind']),
  st(1.8, cam={'mode': 'close', 'to': 'rope', 'time': 0.8, 'zoom': 1.4}, act='줄 끝이 칼에 잘려 있다. 일곱은 그 줄을 놓지 않았다', note='시즌 1 B-10 만선호 선장이 끊은 그 줄'),
  st(3.2, act='하나가 넘어지자 여섯이 동시에 줄을 당겨 일으킨다', req=['cut.rope.taut(젖은 밧줄이 팽팽해지는 소리)']),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '줄에 묶인 일곱', 'seal_icon': 'thread'}, note='전투: 일곱이 원을 돌며 줄을 휘두른다(걸리면 끌려감)')], 4.5),
 phase('B22-SEVEN', '맺힘 60% — 하나씩', '맺힘 60%', 2.5, [
  st(0.0, cam={'mode': 'pull', 'zoom': 0.9, 'time': 0.4}, act='일곱이 원을 멈추고 등을 맞댄다', ui={'timer': 15.0, 'hint_icon': '15초 안에 일곱 모두 무릎 꿇리기'}),
  st(2.5, cam={'mode': 'return', 'to': 'player', 'time': 0.3}, note='하나를 쓰러뜨리면 여섯이 끌어 일으킨다(qa 15초)')]),
 kneel('B-22', '일곱이 함께 무릎 꿇는다. 줄은 그대로 엮여 있다'),
 noclue('B-22', '일곱의 줄이 팽팽해진다. 이름 획이 모이다 흩어진다'),
 lay('B-22', [
  st(4.8, beat='일곱 이름', cam={'mode': 'track', 'to': 'seven', 'time': 3.0, 'zoom': 1.1, 'framing': '무릎 꿇은 일곱을 차례로'}, act='줄을 끊지 않는다. 일곱의 이름 획이 하나씩 차례로 모인다(읽히지 않게)', sfx=['cut.seal.set'],
     note='시즌 1 B-09 망부석 아낙을 천도했으면 돌석(S-090)의 획이 처음부터 또렷'),
  st(8.0, act='일곱이 줄에 엮인 채 나란히 눕는다', req=['sfx.laydown(몸이 젖은 흙에 천천히 눕는 낮은 소리)']),
  st(11.0, cond='B-09 천도(시즌 1)', cam={'mode': 'close', 'to': 'far_shore_figure', 'time': 1.0}, act='저편 기슭, 바위 같던 아낙 옆에 사내 하나가 와 선다', note='망부석 아낙과 돌석. 먼 거리')],
  dur=13.0, light_t=10.0, light='저편 기슭에 나룻불이 일곱 켜진다'),
 brk('B-22', ['대폭발. 줄이 끊어지며 일곱이 흩어진다', '끊긴 밧줄 토막이 썰물에 쓸려 간다'], '선원의 밧줄(사슬 사거리 +0.8m)'),
]

# ═════════ 6막 ⑦ 삼도천의 아래 — B-23 물 밑 매듭(조건형) ═════════
CUTS += [
 intro('B-23', '닻 여울(KnotDeep)에 처음 들어설 때(B-22 처결 다음 첫 밤, 또는 ⑦ 아래 첫 진입 뒤 5번째 새벽이 지난 밤 강제)', [
  st(0.0, cam={'mode': 'crane', 'dir': 'up', 'from': 'riverbed', 'to': 'boss', 'time': 2.0, 'zoom': 0.8, 'framing': '무릎 깊이 여울, 실 수천 가닥이 엉킨 매듭'}, act='물이 빠져도 무릎까지 차는 여울. 실 수천 가닥이 엉킨 매듭', sfx=['amb.river.mist']),
  st(2.2, cam={'mode': 'tilt', 'dir': 'up', 'time': 1.0, 'framing': '매듭 위 수면, 배 밑바닥'}, act='수면 위로 배 밑바닥 하나가 지나간다. 매듭에 걸려 멈칫하다 돌아간다', req=['cut.hull.creak(배가 걸려 삐걱)']),
  st(4.0, cam={'mode': 'close', 'to': 'thread_tags', 'time': 0.8}, act='실 끝마다 작은 이름표. 아는 이름은 희미하게 빛난다', note='아는 이름 = 천도 · 눕히기 기록. 글자는 읽히지 않게(빛으로만)'),
  st(5.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '물 밑 매듭', 'seal_icon': 'thread', 'untie_ready': 'laid_this_act>=20 || sent_total>=300 ? steady : flicker'},
     note='전투 1: 아는 이름 실은 낚아 풀기(1초), 모르는 이름은 끊으면 빠르지만 그 혼이 돌아선다')], 5.5),
 phase('B23-TIGHTEN', '맺힘 50% — 조이기', '맺힘 50%', 2.5, [
  st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.2}, act='매듭이 조인다. 바깥쪽 실이 밝아진다', ui={'hint_icon': '밝은 바깥 실부터'}),
  st(2.5, cam={'mode': 'return', 'to': 'player', 'time': 0.3})]),
 phase('B23-BOAT', '맺힘 20% — 사공의 배', '맺힘 20%', 3.0, [
  st(0.0, cam={'mode': 'tilt', 'dir': 'up', 'time': 0.6, 'framing': '매듭 위에 걸려 기운 배'}, act='사공의 배가 매듭 위에 걸려 기운다. 노 젓는 이가 노를 멈춘다', ui={'hint_icon': '배를 받치고 버티기(시즌 2 B-19에서 배운 버티기)'},
     note='사공 얼굴은 갓 그늘로. 이름 없음'),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3}, note='버티면 매듭 중심이 드러난다')]),
 {'id': 'B23-KNEEL', 'branch': '처결 대기(풀기 / 끊기)', 'trigger': '보스 맺힘 0', 'duration': 1.5, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '단서 대신 조건: 이번 막에서 눕힌 백 20 이상 또는 시즌 1 · 2 누적 천도 300 이상(qa). 모자라면 끊기만. 진행은 막지 않는다',
  'steps': [st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.4, 'zoom': 1.1}, act='매듭이 조인 채 멈춘다. 중심에 가장 오래된 실 한 가닥이 보인다', sfx=['sfx.kneel']),
            st(0.4, ui={'kneel_timer': 7.0, 'untie_ready': 'laid_this_act>=20 || sent_total>=300 ? steady : flicker'}),
            st(1.5, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3})]},
 {'id': 'B23-NOCOND', 'branch': '처결 대기(풀기 불가)', 'trigger': '조건 미달에서 풀기 입력', 'duration': 1.0, 'input_lock': False, 'world': 'run', 'skippable': False,
  'steps': [st(0.0, ui={'toast': '풀어 줄 이름이 모자란다.', 'toast_time': 1.0}, sfx=['cut.seal.fade'], note='안내일 뿐. 끊기는 된다')]},
]

C23A = {'id': 'C-23A', 'branch': '6막 끝 — 첫 배가 닿는다(풀기판)', 'trigger': 'B-23 풀기 캐스팅 완료', 'duration': 90.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 백 년 만에 처음으로 배가 저편에 닿는다. 당할미 6막 끝 비트(season3_outline.halmi). 먹지기 쪽지(keeper)',
 'steps': [
  st(0.0, beat='풀림', cam={'mode': 'hold', 'zoom': 1.0, 'vignette': 0.5, 'vignette_color': mem['B-23'].get('tint')}, act='매듭이 실 한 가닥씩 풀려 위로 올라간다', req=['cut.thread.reel(실이 감겨 올라가는 가는 소리)']),
  st(4.0, beat='기억 줄', line=memline('B-23', 4.0), note='기억 M-B23(★F55 전모)'),
  st(10.0, beat='줄이 움직인다', cam={'mode': 'crane', 'dir': 'up', 'time': 8.0, 'framing': '강바닥에서 수면 위 줄 전체로'}, act='위쪽 줄 전체가 한꺼번에 움직인다. 발목의 실들이 말려 올라간다'),
  st(22.0, beat='배', cam={'mode': 'follow', 'to': 'ferry', 'time': 14.0, 'framing': '사공의 배를 뒤에서, 강 한가운데를 지나'}, act='사공의 배가 강 한가운데를 지난다. 돌아오지 않는다', sfx=['cut.oar.row']),
  st(38.0, beat='닿다', cam={'mode': 'hold', 'framing': '저편 기슭, 배 머리가 모래에 닿는 순간'}, act='배 머리가 저편 모래에 닿는다. 혼들이 내린다. 불빛이 줄지어 켜진다',
     req=['cut.hull.beach(나무배가 모래에 올라앉는 소리)'], note='3초 그대로. 음악도 멈춘다'),
  st(46.0, beat='내가 보낸 사람들', cam={'mode': 'track', 'to': 'disembark', 'time': 8.0, 'zoom': 1.1}, act='이번 막에서 눕힌 사람들의 혼이 배에서 내린다',
     note='플레이 기록. 윤 영감(B-21 눕혔으면)이 맨 앞. 이름 글 없음'),
  st(56.0, beat='당할미', cam={'mode': 'cut', 'to': 'shrine_dawn', 'framing': '솔고개 서낭당, 새벽, 아궁이 연기'}, act='솔고개. 새벽밥을 짓던 당할미가 고개를 든다. 먼 하늘 아래 불빛들', sfx=['amb.dawn.birds']),
  st(64.0, beat='짚신', cam={'mode': 'close', 'to': 'straw_shoes', 'time': 1.5}, act='사잣밥 상 위 짚신. 당할미는 그날 짚신을 고쳐 놓지 않는다', note='halmi 6막 끝. 이유는 말하지 않는다'),
  st(72.0, beat='쪽지', ui={'note_card': S3['keeper']['beats'][0].split('"')[1], 'note_card_time': 8.0}, act='명부 여백 먹지기 쪽지'),
  st(84.0, cam={'mode': 'fade_out', 'time': 2.0}, ui={'fact_on': 'F56', 'small_caption': '6막 — 끝', 'world_change': BC['B-23']['lay']}),
  st(90.0, note='다음: C-24'),
 ]}
_k6 = S3['keeper']['beats'][0]
C23B = {'id': 'C-23B', 'branch': '6막 끝 — 첫 배가 닿는다(끊기판)', 'trigger': 'B-23 처결 대기 중 끊기 입력', 'duration': 90.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 배는 닿지만 끊긴 실의 혼들은 기슭을 떠돈다. F56은 이 판에서도 얻는다(진행 막힘 없음)',
 'steps': [
  st(0.0, beat='끊김', cam={'mode': 'shake', 'strength': 'big', 'time': 1.0}, act='매듭이 끊어진다. 실 토막들이 사방으로 흩어진다', sfx=['sfx.pahon.burst'], req=['cut.thread.snap(물줄기 같은 검은 실이 끊기는 낮은 소리)']),
  st(6.0, beat='흩어진 혼', cam={'mode': 'crane', 'dir': 'up', 'time': 8.0, 'framing': '수면 위 기슭'}, act='줄에서 혼 몇이 떨어져 나와 기슭을 떠돈다. 발목의 실 끝이 잘려 있다'),
  st(18.0, beat='배', cam={'mode': 'follow', 'to': 'ferry', 'time': 14.0}, act='사공의 배가 강 한가운데를 지난다', sfx=['cut.oar.row']),
  st(36.0, beat='닿다', cam={'mode': 'hold', 'framing': '저편 기슭'}, act='배가 저편에 닿는다. 불빛이 켜진다 — 군데군데 비어 있다', req=['cut.hull.beach(나무배가 모래에 올라앉는 소리)']),
  st(50.0, beat='당할미', cam={'mode': 'cut', 'to': 'shrine_dawn', 'framing': '솔고개 서낭당, 새벽'}, act='솔고개. 당할미가 먼 불빛을 본다. 그날 짚신을 고쳐 놓지 않는다', sfx=['amb.dawn.birds']),
  st(62.0, beat='쪽지', ui={'note_card': _k6.split('"')[1] + ' ' + _k6.split('"')[3], 'note_card_time': 10.0}, act='명부 여백 먹지기 쪽지(끊기판 한 줄 더)'),
  st(80.0, cam={'mode': 'fade_out', 'time': 2.0}, ui={'fact_on': 'F56', 'small_caption': '6막 — 끝', 'karma': '+3', 'world_change': BC['B-23']['break']}),
  st(90.0, note='다음: C-24'),
 ]}
CUTS += [C23A, C23B]

# ═════════ 7막 여는 장면 ═════════
C24 = {'id': 'C-24', 'branch': '7막 여는 장면', 'trigger': 'C-23A 또는 C-23B 끝', 'duration': 60.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 큰 무덤 단면. 묻혔다고 누운 것이 아니다(F57). 기수 대돌(B-05)의 시즌 1 천도 여부로 두 판 — 비켜섬(F58)을 처음 보여 준다',
 'steps': [
  st(0.0, beat='붉은재', cam={'mode': 'fade_in', 'time': 1.5, 'framing': '붉은재 큰 무덤, 해 질 녘'}, act='붉은재 산성 아래 큰 무덤. 해가 진다', req=['amb.wind.dry(마른 들바람)']),
  st(8.0, beat='단면', cam={'mode': 'cut', 'to': 'tomb_section', 'time': 10.0, 'framing': '봉분을 칼로 자른 듯한 옆 단면, 천천히 아래로'}, act='봉분 안쪽. 흙과 뼈의 겹. 몸들이 누워 있지 않다 — 앉거나, 서거나, 서로를 붙든 채',
     note='F57. 실루엣으로만. 갑주 색과 깃발 색이 흙 속에선 같다'),
  st(24.0, beat='번호', cam={'mode': 'hold', 'framing': '단면 한가운데'}, act='흙이 낮게 울린다. 몸들이 번호 소리에 맞춰 조금씩 대형을 바꾼다', req=['cut.earth.drum(땅속에서 울리는 낮은 북 같은 진동)'],
     note='번호 호령은 소리 없이 진동으로만. 시즌 1 B-06(이름 없는 장수)'),
  st(36.0, beat='기수', cond='B-05 천도(시즌 1)', cam={'mode': 'push', 'to': 'standard_bearer', 'time': 2.0, 'zoom': 1.3}, act='깃대를 쥔 몸 하나가 일어나 한 걸음 비켜선다. 그 자리에 흙길이 드러난다', req=['cut.soil.shift(젖은 흙에서 몸이 일어나는 소리)'],
     note='F58. "이름이 먼저 가면 몸이 따라간다"를 말없이'),
  st(36.0, beat='기수', cond='B-05 파혼(시즌 1)', cam={'mode': 'push', 'to': 'standard_bearer', 'time': 2.0, 'zoom': 1.3}, act='깃대를 쥔 몸 하나. 이마의 이름 실이 끊겨 있다. 움직이지 않는다'),
  st(48.0, beat='내려가는 길', cam={'mode': 'pull', 'zoom': 0.8, 'time': 4.0, 'framing': '봉분 옆, 아래로 내려가는 굴 입구'}, act='물이 빠진 해자 바닥에 봉분 안으로 드는 굴 입구가 열린다', sfx=['cut.water.recede']),
  st(60.0, cam={'mode': 'return', 'to': 'player', 'time': 1.0}, ui={'region_title': '붉은재의 아래', 'fact_on': 'F57'}),
 ]}
CUTS += [C24]

# ═════════ 7막 ③ 붉은재의 아래 ═════════
CUTS += [
 intro('B-24', '봉분 한가운데 빈 굴(TombPit)에 처음 들어설 때', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.0, 'framing': '둘로 갈라진 바닥, 양쪽에 선 두 진'}, act='봉분 한가운데 빈 굴. 바닥이 둘로 갈라졌다. 양쪽에 진을 친 몸들'),
  st(1.6, cam={'mode': 'two_shot', 'a': 'bearer_this', 'b': 'bearer_that', 'time': 1.0}, act='앞뒤에 두 기수. 깃발 색이 흙에 덮여 같다'),
  st(3.0, cond='B-06 천도 아님(시즌 1)', act='흙이 번호 소리로 울린다. 이쪽 진이 대형을 바꾼다', req=['cut.earth.drum(땅속에서 울리는 낮은 북 같은 진동)']),
  st(3.0, cond='B-06 천도(시즌 1)', act='호령이 없다. 이쪽 진이 어디로 갈지 몰라 흩어진다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '한 구덩이의 두 진', 'seal_icon': 'thread'}, note='전투: 양쪽이 서로 돌진, 나는 가운데')], 4.5),
 phase('B24-MASS', '맺힘 50% — 한 덩어리', '맺힘 50%', 3.0, [
  st(0.0, cam={'mode': 'pull', 'zoom': 0.85, 'time': 0.5}, act='두 진이 한 덩어리로 엉긴다', ui={'hint_icon': '아는 이름을 부르면 한 몸씩 떨어진다'}),
  st(1.0, cond='B-05 천도(시즌 1)', act='이쪽 서른일곱이 스스로 덩어리에서 빠져나와 비켜선다. 건너편만 남는다', note='F58'),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3})]),
 kneel('B-24', '두 기수가 깃대를 쥔 채 무릎 꿇는다. 마주 본다'),
 noclue('B-24', '두 진이 다시 서로를 향해 돌아선다. 이름 획이 모이다 흩어진다'),
 lay('B-24', [
  st(4.8, beat='깃대', cam={'mode': 'crane', 'dir': 'up', 'time': 1.5, 'framing': '두 깃대를 위에서'}, act='두 기수가 동시에 깃대를 내려놓는다. 깃대 둘이 X자로 땅에 눕는다', req=['cut.pole.lay(나무 깃대가 흙에 눕는 둔한 소리)']),
  st(7.0, beat='소매', cam={'mode': 'close', 'to': 'sleeve', 'time': 1.0, 'zoom': 1.6}, act='건너편 기수의 소매 안쪽이 뒤집힌다. 수놓은 실 획(읽히지 않게)', note='F59. 어머니가 수놓은 이름'),
  st(9.0, act='두 진이 한 몸씩 눕는다. 누운 뒤엔 어느 편인지 알 수 없다')], dur=12.0, light_t=10.0, light='저편 기슭에 나룻불이 여러 개 켜진다(눕힌 몸 ÷ 10, 올림)'),
 brk('B-24', ['대폭발. 봉분이 무너진다', '두 진이 흩어진다', '깃대 조각이 굴러 멈춘다'], '두 편의 깃대 조각(잡몹 1.5초 겁먹음)'),
]

# ═════════ 7막 ④ 쇳골의 아래 ═════════
CUTS += [
 intro('B-25', '막힌 막장 안쪽(SealedFace)에 처음 들어설 때', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '쌓인 돌, 틈으로 가늘게 새는 바깥 등불'}, act='막장 안쪽. 쌓인 돌 틈으로 바깥 등불이 가늘게 샌다', sfx=['amb.mine.shaft']),
  st(1.6, act='손들이 쌓인 돌을 판다. 쉬지 않는다', sfx=['cut.hoe.dig'], note='곡괭이가 아니라 맨손 — 소리는 작게'),
  st(3.0, cam={'mode': 'close', 'to': 'boss_mouth', 'time': 0.8}, act='한 몸이 파지 않고 서서 손가락으로 센다. 입술이 움직인다', note='칠성. 입 모양 "열둘." — 자막 · 소리 없음, 대사 수에 세지 않는다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '맨 마지막에 나가는 몸', 'seal_icon': 'thread'}, note='전투: 백들은 공격하지 않고 흙이 무너져 온다')], 4.5),
 phase('B25-PROP', '맺힘 50% — 버팀목', '맺힘 50%', 3.0, [
  st(0.0, cam={'mode': 'pull', 'zoom': 0.9, 'time': 0.4}, act='천장이 내려앉기 시작한다. 버팀목 셋', ui={'hint_icon': '버팀목 곁에서 버티는 동안만 칠성에게 닿는다'}),
  st(1.0, cond='S-073 천도(시즌 1)', act='버팀목 하나가 처음부터 단단하다', note='갱도 목수'),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3})]),
 kneel('B-25', '칠성이 세다 멈춘다. 입 모양 "열둘." 손가락 하나가 남는다'),
 noclue('B-25', '칠성이 처음부터 다시 센다'),
 lay('B-25', [
  st(4.8, beat='마저 세기', cam={'mode': 'close', 'to': 'boss_mouth', 'time': 1.0}, act='칠성이 마저 센다. 입 모양 "열셋. 그리고 —"', note='자막 · 소리 없음'),
  st(7.0, beat='대답', cond='S-209 눕힘', act='아래 물길 쪽에서 아주 작게 무언가 대답한다', req=['vo.far.reply(아주 먼 물길에서 오는 짧은 대답 — 말은 안 들리게)'], note='"열넷". 소리만, 글 없음'),
  st(9.0, act='열둘이 차례로 눕는다. 칠성이 맨 마지막에 눕는다', req=['sfx.laydown(몸이 젖은 흙에 천천히 눕는 낮은 소리)'])],
  dur=13.0, light_t=11.0, light='저편 기슭에 나룻불이 열셋 켜진다(S-209까지 눕혔으면 열넷)'),
 brk('B-25', ['대폭발. 막장이 무너진다', '열셋이 다시 흙에 묻힌다'], '광맥 한 줄(재료 3배)'),
]

# ═════════ 7막 ② 검은여울의 아래 ═════════
CUTS += [
 intro('B-26', '석회 구덩이(LimePit)에 처음 들어설 때', [
  st(0.0, cam={'mode': 'crane', 'dir': 'down', 'time': 1.6, 'zoom': 1.0, 'framing': '흰 가루 위 발자국, 구덩이를 위에서'}, act='석회 구덩이. 흰 가루에 내 발자국이 남는다. 위 겹에 몸 마흔', req=['cut.lime.step(마른 가루를 밟는 소리)']),
  st(1.8, cam={'mode': 'close', 'to': 'lime_band', 'time': 0.8}, act='발밑에 흰 석회 띠. 그 아래에도 몸들이 있다'),
  st(3.2, act='잿빛 안개가 번진다', sfx=['amb.weather.fog']),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '두 겹 구덩이', 'seal_icon': 'thread'}, note='전투: 아는 이름마다 한 몸씩 떨어진다. 잿빛 안개 이동 −20%')], 4.5),
 phase('B26-SPLIT', '맺힘 50% — 석회 띠가 갈라진다', '맺힘 50%', 3.0, [
  st(0.0, cam={'mode': 'shake', 'strength': 'mid', 'time': 0.4}, act='석회 띠가 갈라져 아래 겹으로 떨어진다. 아래 겹이 위 겹을 끌어당긴다', req=['cut.lime.crack(굳은 석회가 갈라지는 소리)']),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3}, note='위아래 둘 다의 이름이 있어야 깔끔(B-27 단서와 서로 채움)')]),
 kneel('B-26', '아무것도 쓰지 않은 돌 마흔이 흙에서 떠오른다'),
 noclue('B-26', '빈 돌들이 다시 가라앉는다'),
 lay('B-26', [
  st(4.8, beat='두 글씨', cam={'mode': 'track', 'to': 'stones', 'time': 3.0, 'zoom': 1.2, 'framing': '돌 마흔을 차례로'}, act='돌마다 이름이 새겨진다 — 위 겹은 의원의 글씨, 아래 겹은 서생의 글씨', sfx=['cut.stone.carve'],
     note='두 글씨체가 달라 보이는 것이 핵심(어려우면 해서/흘림). 글자는 읽히지 않을 거리'),
  st(8.5, act='위 겹과 아래 겹이 석회 띠를 사이에 두고 나란히 눕는다')], dur=11.0, light_t=9.0, light='저편 기슭에 나룻불이 여덟 켜진다'),
 brk('B-26', ['대폭발. 석회 띠가 터져 하얗게 흩어진다', '빈 돌 마흔이 그대로 남는다'], '석회 주머니(폭발 뒤 2초 잡몹 이동 −30%)'),
]

# ═════════ 7막 ⑥ 도성의 아래 — B-27 흑월의 몸 ═════════
_ink = '李明'
CUTS += [
 intro('B-27', '성문 밖 구덩이 가장 오래된 겹(GatePit)에 처음 들어설 때', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '바닥이 온통 글씨인 구덩이, 붓을 쥔 몸'}, act='구덩이 바닥이 온통 글씨다. 언 손 하나가 흙에 이름을 쓴다', sfx=['cut.brush.write']),
  st(1.6, cam={'mode': 'close', 'to': 'soil_text', 'time': 0.8}, act='쓰인 이름마다 그 사람의 몸이 흙에서 일어난다'),
  st(1.6, cond='B-26 눕힘', cam={'mode': 'close', 'to': 'soil_text', 'time': 0.8}, act='쓰인 이름마다 몸이 일어나 — 내게 오지 않고 서생 곁에 무릎 꿇는다', note='인사하러 온 것'),
  st(3.2, cam={'mode': 'close', 'to': 'last_row', 'time': 0.8}, act='마흔을 다 쓴 손이 마지막 한 줄 앞에서 멈춘다. 처음으로 돌아간다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '마지막 줄', 'seal_icon': 'thread'}, note='시즌 1 흑월(B-12)을 파혼했으면 흙의 글씨가 반쯤 번져 있다(주인 없는 백)')], 4.5),
 phase('B27-GATE', '맺힘 50% — 성문이 닫힌다', '맺힘 50%', 3.0, [
  st(0.0, cam={'mode': 'pull', 'zoom': 0.8, 'time': 0.6, 'framing': '성문 그림자가 무대를 덮어 오는 것을 위에서'}, act='성문이 닫히는 소리. 성문 그림자가 무대를 덮어 온다. 그림자 밖은 언 땅',
     req=['cut.gate.close(큰 나무 성문이 닫히는 소리)'], ui={'timer': 120.0, 'arena_shrink': '100%→50%'}),
  st(1.5, cond='시즌 1 ⑥ 장례에서 문지기 아들이 성문을 늦게 닫는 장면을 봤을 때', act='그림자가 느리게 온다', note='×0.6(qa)'),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3})]),
 kneel('B-27', '서생이 무릎 꿇는다. 마지막 줄 앞에서 붓끝이 떨린다', timer=10.0),
 noclue('B-27', '손이 다시 첫 줄로 돌아간다'),
 lay('B-27', [
  st(4.8, beat='마지막 줄', cam={'mode': 'close', 'to': 'last_row', 'time': 1.5, 'zoom': 1.6}, cond='B-12 천도(시즌 1)', act='서생의 손이 마지막 줄에 처음으로 자기 이름을 쓴다', sfx=['cut.brush.write'],
     ui={'ledger_name': _ink, 'ledger_name_note': '이 게임에서 처음으로 흑월의 본명이 글자로 뜬다(F62). 明의 日과 月이 함께 또렷'}),
  st(8.0, beat='사슬', cam={'mode': 'close', 'to': 'boss_wrist', 'time': 1.0}, act='손목에서 사슬이 풀려 흙 위로 둥글게 떨어진다', req=['cut.chain.fall(사슬이 흙 위로 감기며 떨어지는 소리)'], note='F63 — 7막 엔딩 C-27A에서 뜻이 열린다'),
  st(10.0, act='서생이 붓을 내려놓고 눕는다'),
  st(4.8, cond='B-12 파혼(시즌 1)', act='손이 마지막 줄에 이름을 쓰지만 번져 읽을 수 없다', ui={'ledger_name': None}, note='주인 없는 백 판. 팻말에는 "서생"만')],
  dur=13.0, light_t=11.0, extra_ui={'collection': '도감 "서생의 명단"'}),
 brk('B-27', ['대폭발. 흙의 글씨가 먹물처럼 번져 사라진다', '사슬이 흙 속으로 끌려 들어간다'], '번진 먹 한 덩이(폭발 반경 +0.5m)'),
]
# 시즌 2에서 그가 두 번째 배 사공이었다면(B-12 천도 · B-13 천도): 노를 내려놓고 배에서 내린다
CUTS[-1]['steps'].insert(-1, st(round(CUTS[-1]['duration'] - 0.5, 1), cond='B-12 천도 · B-13 천도(시즌 1 · 2)', act='⑦ 강 위, 두 번째 배의 사공이 노를 내려놓고 배에서 내린다'))

C27A = {'id': 'C-27A', 'branch': '7막 끝 — 사슬이 풀리는 것을 본다(눕히기판)', 'trigger': 'B-27 눕히기 끝(B-26도 처결된 뒤. 아니면 B-26 처결 끝)', 'duration': 90.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 차사의 사슬은 묻히지 못한 자기 몸에 묶여 있다(F63). 내 사슬 끝을 따라가면 물막이 골 소의 횃불(F64). 당할미 7막 끝 비트',
 'steps': [
  st(0.0, beat='팻말', cam={'mode': 'fade_in', 'time': 1.0, 'framing': '성문 밖, 이튿날 낮, 새 팻말'}, act='이튿날 낮. 문지기의 아들이 팻말 하나를 세운다. 서적상 노인 가게의 새 붓으로 쓴 두 글자', ui={'sign_text': _ink},
     sfx=['amb.wind.gust'], note='팻말의 글자는 읽히게. B-27 눕히기 판에서만'),
  st(12.0, beat='둥근 사슬', cam={'mode': 'close', 'to': 'chain_coil', 'time': 2.0}, act='팻말 앞 흙 위에 녹슨 사슬이 둥글게 놓여 있다'),
  st(20.0, beat='내 사슬', cam={'mode': 'close', 'to': 'player_wrist', 'time': 2.0, 'zoom': 1.6}, act='차사가 자기 손목을 본다. 사슬이 팽팽하다. 어딘가로 당겨진다',
     req=['cut.chain.taut(사슬이 팽팽하게 당겨지는 소리)']),
  st(28.0, beat='따라가다', cam={'mode': 'follow', 'to': 'chain_line', 'time': 18.0, 'height': 'low', 'framing': '사슬이 땅을 기어 강을 거슬러 솔고개 쪽으로'},
     act='사슬 줄이 땅을 기어 강을 거슬러 올라간다. 고개를 넘는다. 물막이 골', note='카메라만 간다. 차사는 그 자리'),
  st(48.0, beat='물속의 불', cam={'mode': 'crane', 'dir': 'down', 'time': 8.0, 'framing': '물막이 골 소, 수면 아래 깊이'}, act='물이 빠져도 마르지 않는 소. 가장 깊은 곳에 불빛 하나. 물속인데 꺼지지 않는다', req=['amb.underwater.low(물속의 먹먹한 낮은 울림)'],
     note='F64. 횃불을 쥔 손까지는 보여 주지 않는다(B-31에서)'),
  st(60.0, beat='당할미', cam={'mode': 'cut', 'to': 'shrine_day', 'framing': '서낭당, 짚신을 고치는 손'}, act='서낭당. 짚신을 고치던 당할미의 손이 멈춘다. 물막이 골 쪽을 오래 본다', note='halmi 7막 끝. S-192가 본 그 불빛'),
  st(72.0, beat='쪽지', ui={'note_card': S3['keeper']['beats'][1].split('"')[1], 'note_card_time': 8.0}, act='명부 여백 먹지기 쪽지'),
  st(84.0, cam={'mode': 'fade_out', 'time': 2.0}, ui={'fact_on': ['F63', 'F64'], 'small_caption': '7막 — 끝'}),
  st(90.0, note='다음: C-28'),
 ]}
_k7 = S3['keeper']['beats'][1]
C27B = {'id': 'C-27B', 'branch': '7막 끝 — 사슬이 풀리는 것을 본다(깨뜨리기판 · 시즌 1 흑월 파혼판)', 'trigger': 'B-27 깨뜨리기 끝, 또는 시즌 1 B-12 파혼인 채 B-27 눕히기 끝', 'duration': 90.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 팻말엔 "서생"만(또는 팻말 없음). F63 · F64는 이 판에서도 얻는다 — 다른 차사의 백(S-204, 6막)에서 본 것과 내 사슬로',
 'steps': [
  st(0.0, beat='빈 자리', cam={'mode': 'fade_in', 'time': 1.0, 'framing': '성문 밖, 이튿날 낮'}, act='이튿날 낮. 성문 밖은 그대로다',
     variant={'break': {'action': '팻말 없는 흙. 흙 속으로 끌려 들어간 사슬 끝이 조금 비어져 나와 있다'},
              'ownerless': {'action': '문지기의 아들이 팻말을 세운다. 두 글자 — "서생"', 'ui': {'sign_text': '서생'}}}),
  st(20.0, beat='내 사슬', cam={'mode': 'close', 'to': 'player_wrist', 'time': 2.0, 'zoom': 1.6}, act='차사가 자기 손목을 본다. 사슬이 팽팽하다', req=['cut.chain.taut(사슬이 팽팽하게 당겨지는 소리)']),
  st(28.0, beat='따라가다', cam={'mode': 'follow', 'to': 'chain_line', 'time': 18.0, 'height': 'low'}, act='사슬 줄이 강을 거슬러 솔고개 물막이 골로'),
  st(48.0, beat='물속의 불', cam={'mode': 'crane', 'dir': 'down', 'time': 8.0}, act='소 가장 깊은 곳, 꺼지지 않는 불빛 하나', req=['amb.underwater.low(물속의 먹먹한 낮은 울림)']),
  st(60.0, beat='당할미', cam={'mode': 'cut', 'to': 'shrine_day'}, act='당할미가 짚신을 고치다 멈추고 물막이 골 쪽을 본다'),
  st(72.0, beat='쪽지', ui={'note_card': _k7.split('"')[3], 'note_card_time': 6.0}, act='명부 여백 먹지기 쪽지'),
  st(84.0, cam={'mode': 'fade_out', 'time': 2.0}, ui={'fact_on': ['F63', 'F64'], 'small_caption': '7막 — 끝'}),
  st(90.0, note='다음: C-28'),
 ]}
CUTS += [C27A, C27B]

# ═════════ 8막 여는 장면 ═════════
C28 = {'id': 'C-28', 'branch': '8막 여는 장면', 'trigger': 'C-27A 또는 C-27B 끝', 'duration': 60.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 물막이 골 소로 가는 길은 이승 쪽이 아니라 저승 쪽(⑧ → ⑨ → ⑩ → 같은 물, F70 복선). 저승 일꾼도 묻히지 못한 몸을 가진 혼(F65)',
 'steps': [
  st(0.0, beat='가리킴', cam={'mode': 'close', 'to': 'player_wrist', 'time': 2.0, 'framing': '손목, 사슬이 당기는 방향'}, act='솔고개로 가야 할 사슬이 이상하게 하류 — 저승 쪽을 가리킨다'),
  st(8.0, beat='담장', cam={'mode': 'pull', 'zoom': 0.7, 'time': 6.0, 'framing': '명부전 담장 밖, 벼루들'}, act='명부전 담장 밖. 물이 빠지자 벼루들 밑에 검은 앙금이 드러난다', sfx=['cut.water.recede', 'cut.ink.grind']),
  st(22.0, beat='신참 서리', cam={'mode': 'two_shot', 'a': 'young_clerk', 'b': 'silt', 'time': 2.0, 'framing': '앙금 가장자리, 내려다보는 신참 서리'},
     act='신참 서리 하나가 일을 멈추고 앙금 속을 내려다본다. 거기 자기 몸이 누워 있다', note='S-128. 얼굴은 놀람이 아니라 오래 잊은 것을 본 표정'),
  st(36.0, beat='손을 놓다', act='서리가 들고 있던 장부를 앙금 가장자리에 내려놓는다. 다시 집지 않는다', req=['cut.book.set(묶은 장부를 젖은 돌에 내려놓는 소리)']),
  st(46.0, beat='일꾼들', cam={'mode': 'crane', 'dir': 'up', 'time': 6.0}, act='먹을 나르던 일꾼들이 하나둘 고개를 든다. 아무도 말하지 않는다'),
  st(60.0, cam={'mode': 'return', 'to': 'player', 'time': 1.0}, ui={'region_title': '명부전 담장 밖의 아래', 'fact_on': 'F65'}),
 ]}
CUTS += [C28]

# ═════════ 8막 ⑧ ═════════
CUTS += [
 intro('B-28', '먹 앙금 한가운데(InkSilt)에 처음 들어설 때', [
  st(0.0, cam={'mode': 'tilt', 'dir': 'up', 'time': 1.6, 'framing': '앙금 바닥에서 올려다본 벼루 바닥, 천장처럼 돈다'}, act='머리 위 벼루 바닥이 천장처럼 돈다. 위에서 혼이 먹을 간다', sfx=['cut.ink.grind']),
  st(1.8, cam={'mode': 'close', 'to': 'boss_hand', 'time': 0.8, 'zoom': 1.5}, act='앙금에서 붓 모양으로 굳은 손이 솟는다. 무언가를 쓰다 반 줄에서 멈춘다', sfx=['cut.brush.stroke']),
  st(3.2, act='다시 쓴다. 다시 반 줄에서 멈춘다'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '벼루 밑의 손', 'seal_icon': 'thread'}, note='전투: 먹물 비 장판, 앙금에서 손이 솟는다(이동 −15%)')], 4.5),
 phase('B28-DUST', '맺힘 50% — 가루의 늪', '맺힘 50%', 3.0, [
  st(0.0, cam={'mode': 'pull', 'zoom': 0.85, 'time': 0.5}, act='앙금 위로 가루가 떠오른다 — 내가 이 게임에서 깨뜨린 혼들의 가루', note='플레이 기록. 파혼 수만큼 둔화 웅덩이(최대 8). 천도 · 눕히기가 많으면 맑은 물길. 벌이 아니라 거울'),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3})]),
 kneel('B-28', '손이 반 줄 끝에서 멈춘 채 앙금에 내려앉는다'),
 noclue('B-28', '손이 다시 처음부터 쓴다'),
 lay('B-28', [
  st(4.8, beat='나머지 반 줄', cam={'mode': 'close', 'to': 'boss_hand', 'time': 1.5, 'zoom': 1.6}, act='손이 나머지 반 줄을 쓴다', sfx=['cut.brush.write'],
     ui={'poem_card': BC['B-28']['lay'].split('「')[1].split('」')[0], 'poem_card_time': 6.0, 'poem_rule': 'S-272를 안 눕혔으면 첫 줄만(도감에서 나중에 채움)'},
     note='시 글은 season3_outline B-28 lay가 정본. B-16 원본 마지막 줄 "내 먹 냄새를 모르겠다"에 대한 답(ink_link)'),
  st(10.0, beat='위층', cam={'mode': 'tilt', 'dir': 'up', 'time': 1.0}, act='위에서 벼루가 멈춘다. 벼루지기의 혼이 갈기를 멈추고 줄 쪽으로 걸어간다')],
  dur=14.0, light_t=12.0, extra_ui={'collection': '도감 "벼루지기의 시"'}),
 brk('B-28', ['대폭발. 앙금이 터져 먹물이 솟는다', '손이 반 줄에서 굳는다'], '진한 먹 한 통(캐스팅 중 피격 시 안 끊김 1회/밤)'),
]

# ═════════ 8막 ⑨ ═════════
CUTS += [
 intro('B-29', '빈 고을 맨 끝 집 방 안(Ondol)에 처음 들어설 때', [
  st(0.0, cam={'mode': 'pan', 'from': 'player', 'to': 'boss', 'time': 1.4, 'zoom': 1.15, 'framing': '반쯤 내려앉은 구들, 아랫목에 누운 할미, 머리맡 밥상'}, act='맨 끝 집 방. 구들이 반쯤 내려앉았다. 머리맡에 사잣밥 세 그릇, 짚신 세 켤레, 엽전 세 닢',
     req=['amb.ondol.fire(아궁이 불 타는 작은 소리)']),
  st(1.8, act='밥이 식는다. 할미의 손이 밥상을 새로 차린다', sfx=['cut.straw.set']),
  st(3.2, cam={'mode': 'pull', 'zoom': 0.9, 'time': 0.8}, act='집집에서 온 몸들이 방문을 지킨다 — 할머니 차례가 먼저라고'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '백 년의 사잣밥', 'seal_icon': 'thread', 'hint_icon': '밥상 앞에 3초 서기(맺힘 회복 15초 멈춤)'},
     note='밥상 앞에 서 있기 = 사잣밥을 먹음. 당할미 서낭당 밥상과 똑같은 상(결말 C의 거울)')], 4.5),
 phase('B29-FLOOR', '맺힘 50% — 무너지는 구들', '맺힘 50%', 2.5, [
  st(0.0, cam={'mode': 'shake', 'strength': 'mid', 'time': 0.4}, act='구들이 무너진다. 아궁이 불이 올라온다', ui={'hint_icon': '뜨거운 칸 피하기'}),
  st(2.5, cam={'mode': 'return', 'to': 'player', 'time': 0.3})]),
 kneel('B-29', '할미가 짚신 한 켤레를 내민다'),
 noclue('B-29', '할미가 짚신을 거두고 밥상을 새로 차린다'),
 lay('B-29', [
  st(4.8, beat='짚신', cam={'mode': 'close', 'to': 'player_feet', 'time': 1.0}, act='차사가 짚신을 신는다', req=['cut.straw.tie(짚신 끈을 매는 소리)'],
     note='B29-D3(백한 켤레째)를 찾았다면 할미가 마지막 켤레를 마저 엮어 내민다'),
  st(7.0, beat='손을 떼다', cam={'mode': 'close', 'to': 'boss_hand', 'time': 1.0}, act='할미가 처음으로 밥상에서 손을 뗀다. 눕는다'),
  st(9.5, beat='집집', cam={'mode': 'crane', 'dir': 'up', 'time': 2.0, 'framing': '빈 고을 지붕들을 위에서'}, act='집집의 몸들이 차례로 눕는다')],
  dur=14.0, light_t=12.0),
 brk('B-29', ['대폭발. 밥상이 엎어진다', '방이 무너진다'], '사잣밥 엽전 세 닢(물 차오름 떠밀림 1회 무효)'),
]

# ═════════ 8막 ⑩ ═════════
CUTS += [
 intro('B-30', '첫 우물 밑(WellBottom)에 처음 들어설 때', [
  st(0.0, cam={'mode': 'crane', 'dir': 'down', 'time': 1.6, 'zoom': 1.0, 'framing': '우물 밑 원형 무대, 벽을 따라 오르내리는 물'}, act='첫 우물 밑. 벽을 따라 물이 오르내린다', sfx=['amb.river.mist']),
  st(1.8, cam={'mode': 'close', 'to': 'boss_hand', 'time': 0.8, 'zoom': 1.5}, act='바닥에 몸 하나. 작은 신발 한 짝을 쥐고 있다', note='어미. 얼굴 · 이름 없음'),
  st(3.2, cam={'mode': 'tilt', 'dir': 'up', 'time': 1.0}, act='위에서 새끼줄 한 가닥이 늘어져 있다. 누군가 아주 오래 당겨 온 줄', note='우물 위 첫 차사(S-045)의 몸'),
  st(4.5, cam={'mode': 'return', 'to': 'player', 'time': 0.4}, ui={'boss_bar': '첫 우물', 'seal_icon': 'none'}, note='전투: 파도형 장판(오름 3 · 내림 5초). 우물 밑 몸들이 어미를 지킨다')], 4.5),
 phase('B30-ROPE', '맺힘 50% — 새끼줄', '맺힘 50%', 3.0, [
  st(0.0, cam={'mode': 'two_shot', 'a': 'player', 'b': 'rope', 'time': 0.5}, act='새끼줄이 팽팽해진다', ui={'hint_icon': '물이 내려가는 5초 안에 줄을 함께 붙잡고 3초 버티기 ×3'}),
  st(3.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3}, note='줄을 끊으면 즉시 끝나지만 깨뜨리기 판')]),
 phase('B30-OAR', '맺힘 20% — 노 젓는 이', '맺힘 20%', 4.0, [
  st(0.0, cam={'mode': 'tilt', 'dir': 'up', 'time': 1.0, 'framing': '우물 입구, 노를 기대 두는 손'}, act='마지막 사공이 노를 우물가에 기대 두고 줄을 타고 내려온다', sfx=['cut.oar.row'], note='얼굴은 갓 그늘로. 이름 없음'),
  st(4.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3}, note='이후 사공은 싸우지 않고 어미 곁에 선다')]),
 kneel('B-30', '어미가 신발을 쥔 채 무릎 꿇는다'),
 noclue('B-30', '어미가 신발을 더 꼭 쥔다'),
 lay('B-30', [
  st(4.8, beat='입 모양', cam={'mode': 'close', 'to': 'ferryman_mouth', 'time': 1.5}, act='사공이 입술을 움직인다. 소리도 자막도 없다',
     note='입 모양은 "어머니"(애니메이션 참고용 — 화면에 글 · 소리 없음, 대사 수에 세지 않는다)'),
  st(8.0, beat='신발', cam={'mode': 'close', 'to': 'boss_hand', 'time': 1.0}, act='어미가 작은 신발을 놓고 눕는다'),
  st(10.5, beat='첫 줄', cam={'mode': 'cut', 'to': 'ledger_first', 'framing': '명부 맨 첫 장 맨 첫 줄, 까맣게 번진 자리'}, act='명부 첫 줄의 번진 먹이 이름이 되지 않는다. 그러나 더 번지지 않고 멈춘다'),
  st(13.0, beat='새끼줄', act='새끼줄이 우물에 떨어진다', req=['cut.rope.fall(새끼줄이 물에 떨어지는 소리)'])],
  dur=17.0, light_t=15.0, light='저편 기슭에 나룻불이 둘 켜진다(어미 · 첫 차사)', first='명부가 펼쳐진다. 이름 칸은 비어 있다. 획이 모이지 않는다'),
 brk('B-30', ['대폭발. 새끼줄이 끊어진다', '우물이 무너진다', '사공이 소리 없이 부르며 노를 집는다'], '첫 우물의 두레박줄(사슬 당기기 속도 +20%)'),
]
# 이름 없는 눕히기: 첫 박자의 명부 연출을 '이름 칸이 빈 채 멈춤'으로 바꾼다
for c in CUTS:
    if c['id'] == 'B30-LAY':
        c['note'] = '눕히기 — 이름 없이. 차사가 부르는 대신 사공이 부른다(F66 — 결말 B의 원리). 어미의 이름은 어디에도 쓰지 않는다'
        c['steps'][0]['ui'] = {'ledger_fx': 'no_name_hold'}

C30 = {'id': 'C-30', 'branch': '⑩ 끝 — 처음과 끝은 같은 물', 'trigger': 'B30-LAY 또는 B30-BREAK 끝', 'duration': 40.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': True, 'lines': 0,
 'note': '대사 0. 첫 우물 밑 물길이 솔고개 물막이 골 소로 이어진다(F70). 최종 무대가 1막의 그 나루',
 'steps': [
  st(0.0, beat='물길', cam={'mode': 'follow', 'to': 'water_channel', 'time': 14.0, 'height': 'low', 'framing': '우물 밑 바닥의 좁은 물길을 따라'}, act='우물 밑 바닥, 좁은 물길이 열린다. 물이 흐른다 — 하류가 아니라 위로', req=['amb.underwater.low(물속의 먹먹한 낮은 울림)']),
  st(16.0, beat='같은 물', cam={'mode': 'cut', 'to': 'soljae_pool', 'framing': '솔고개 물막이 골 나루, 1막 첫 장면과 같은 구도'}, act='솔고개 물막이 골 나루. 1막 첫 장면과 같은 자리', sfx=['amb.river.mist'],
     note='C-01 구도를 그대로 다시 쓴다'),
  st(26.0, beat='불', cam={'mode': 'crane', 'dir': 'down', 'time': 8.0, 'framing': '소 수면 아래, 가장 깊은 곳'}, act='소 가장 깊은 곳 불빛이 조금 밝아진다. 내 사슬이 그쪽으로 당겨진다', req=['cut.chain.taut(사슬이 팽팽하게 당겨지는 소리)']),
  st(40.0, cam={'mode': 'fade_out', 'time': 1.5}, ui={'fact_on': 'F70', 'map_mark': '물막이 골 소(PoolDeep) — 다음 밤 열림'}),
 ]}
CUTS += [C30]

# ═════════ 마지막 — B-31 나의 백 ═════════
CUTS += [
 intro('B-31', '물막이 골 소 가장 깊은 곳(PoolDeep)에 처음 들어설 때(C-30 다음 첫 밤, 또는 ⑩ 아래 첫 진입 뒤 5번째 새벽이 지난 밤 강제)', [
  st(0.0, cam={'mode': 'crane', 'dir': 'down', 'time': 2.0, 'zoom': 0.9, 'framing': '물이 빠져도 마르지 않는 소, 물속에서 타는 횃불'}, act='물이 끝내 빠지지 않는 소. 물속에서 횃불 하나가 탄다', req=['amb.underwater.low(물속의 먹먹한 낮은 울림)']),
  st(2.2, cam={'mode': 'push', 'to': 'boss', 'time': 1.2, 'zoom': 1.2, 'framing': '젊은이, 한 손에 횃불, 다른 손은 앞으로'}, act='젊은이. 한 손에 횃불, 다른 손은 앞으로 뻗어 있다 — 아직 누구를 건지려는 손', note='얼굴은 횃불 그늘로. 차사와 닮았는지는 보여 주지 않는다'),
  st(4.0, cam={'mode': 'close', 'to': 'boss_wrist', 'time': 1.0, 'zoom': 1.6}, act='그 손목에 내 사슬 끝이 감겨 있다', sfx=['cut.chain.wrap']),
  st(6.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5}, ui={'boss_bar': '나의 백', 'seal_icon': 'thread', 'chain_tether': 8.0}, note='전투 1: 이동 반경이 사슬 길이 8.0m로 묶인다. 백이 움직이면 나도 끌려간다')], 6.0),
 phase('B31-EIGHTH', '단계 2 — 여덟째', '맺힘 60%', 4.0, [
  st(0.0, cond='S-188 눕힘 아님', cam={'mode': 'push', 'to': 'small_body', 'time': 1.0, 'zoom': 1.3}, act='실에 감긴 작은 몸 하나가 떠오른다. 등에 보릿단', ui={'hint_icon': '작은 몸을 먼저 눕히기'}),
  st(0.0, cond='S-188 눕힘', cam={'mode': 'push', 'to': 'barley', 'time': 1.0, 'zoom': 1.3}, act='보릿단 하나만 떠 있다. 저편 쪽 불 하나가 깜빡인다', note='이미 건너간 아이(F71). 짧게 끝남'),
  st(4.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3})]),
 phase('B31-SEVEN', '단계 3 — 일곱', '맺힘 30%', 5.0, [
  st(0.0, cam={'mode': 'crane', 'dir': 'up', 'time': 1.5, 'framing': '수면에서 내려오는 빛들'}, act='백이 나를 밀어낸다. 그 밤 건져진 일곱의 빛이 수면에서 내려와 사슬을 붙잡는다',
     ui={'helpers': 'min(7, max(1, sent_total // 40))'}, note='내가 보낸 사람 40명당 하나(1~7). 둑에서 건져진 사내(S-120/S-264)는 반드시 그중 하나'),
  st(5.0, cam={'mode': 'return', 'to': 'player', 'time': 0.3})]),
 {'id': 'B31-KNEEL', 'branch': '처결 대기(눕히기 / 깨뜨리기)', 'trigger': '보스 맺힘 0', 'duration': 3.0, 'input_lock': False, 'world': 'run', 'skippable': False,
  'note': '처결 대기 15초. 눕히기 가능 = 기억 조각 150 이상 + 업 60 미만. 미달이면 깨뜨리기만 → 결말 C. 백은 무릎 꿇지 않는다',
  'steps': [st(0.0, cam={'mode': 'push', 'to': 'boss', 'time': 0.8, 'zoom': 1.2}, act='백이 무릎 꿇지 않고 선다. 횃불을 내 쪽으로 내민다', sfx=['sfx.kneel']),
            st(0.8, line=memline('B-31', 3.6), note='기억 M-B31(★F72는 결말에서). 처결 대기 중 한 번'),
            st(1.0, ui={'kneel_timer': 15.0, 'lay_ready': 'memory>=150 && karma<60 ? steady : flicker'}),
            st(3.0, cam={'mode': 'return', 'to': 'player_and_boss', 'time': 0.3})]},
 {'id': 'B31-NOCOND', 'branch': '처결 대기(눕히기 불가)', 'trigger': '조건 미달에서 눕히기 입력', 'duration': 1.0, 'input_lock': False, 'world': 'run', 'skippable': False,
  'steps': [st(0.0, ui={'toast': '손이 닿지 않는다.', 'toast_time': 1.0}, sfx=['cut.seal.fade'], note='안내일 뿐. 깨뜨리기만 된다(결말 C)')]},
]

# ═════════ 결말 ═════════
# 장면 · 대사의 정본은 endings_s1.json final_endings. 여기는 그 장면을 카메라 · 박자 · 조건으로 푼 실행 대본이다.
# 대사 글은 line_ref로만 가리킨다(이 파일에 주인공 이름 · 의례 이름 · 추위 말이 들어가지 않게).
C31A = {'id': 'C-31A', 'branch': '결말 A — 이름을 부르다', 'trigger': 'B-31 눕히기 캐스팅 완료 + F9(시즌 1 B-12 천도)', 'duration': 240.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': False, 'lines': 2, 'canon': 'endings_s1.json final_endings.endings.A',
 'note': '대사 2줄(당할미 · 차사, line_ref). 처음 또렷하게 들리는 사람 목소리. 건너뛰기 불가(한 번은 끝까지 — 다시 볼 땐 도감에서 건너뛰기 가능). 끝에 선택: 건너간다 / 남는다',
 'steps': [
  st(0.0, beat='횃불', cam={'mode': 'two_shot', 'a': 'player', 'b': 'boss', 'time': 2.0, 'zoom': 1.2}, act='차사가 횃불을 받는다', sfx=['cut.torch.sink'], note='받는 순간 횃불이 꺼진다(물에 잠기는 소리)'),
  st(6.0, act='백이 뻗었던 손을 거둔다. 눕는다', req=['sfx.laydown(몸이 젖은 흙에 천천히 눕는 낮은 소리)']),
  st(14.0, beat='새벽', cam={'mode': 'crane', 'dir': 'up', 'time': 10.0, 'framing': '소에서 수면 위, 솔고개 새벽'}, act='새벽. 물이 찬다. 차사가 처음으로 흩어지지 않는다', sfx=['amb.dawn.birds'],
     note='시즌 1부터 새벽마다 흩어지던 몸(새벽 귀환)이 처음으로 그대로'),
  st(30.0, beat='상여', cam={'mode': 'follow', 'to': 'bier', 'time': 20.0, 'framing': '고갯길을 내려오는 상여, 낮'}, act='낮. 몸이 있는 상여가 고개를 내려간다. 메는 사람들은 내가 보낸 사람들의 가족',
     sfx=['mus.sangyeo.far'], note='플레이 기록에서 고름(천도 · 눕히기한 혼의 가족 NPC). 얼굴은 보이되 이름 글 없음'),
  st(30.0, beat='상여', cond='B-02 천도(시즌 1)', act='앞줄에 열한 사내의 아들들이 선다'),
  st(52.0, beat='열두째 자리', cam={'mode': 'crane', 'dir': 'down', 'time': 6.0, 'framing': '둑, 팔을 엮은 열한 무덤 옆 빈자리'}, act='둑. 열한 몸이 누운 줄의 열두째 자리에 상여가 내려선다. 사잣밥 한 그릇', ui={'fact_on': 'F72'}),
  st(70.0, beat='지붕', cam={'mode': 'cut', 'to': 'shrine_roof', 'time': 3.0, 'framing': '서낭당 지붕, 아래에서 올려다봄'}, act='당할미가 서낭당 지붕에 올라 아들의 저고리를 흔든다',
     req=['cut.cloth.wave(무명 저고리가 바람에 크게 흔들림)'], note='장례 첫 의례. 의례 이름은 화면에 쓰지 않는다(endings_s1 chohon 규칙)'),
  st(78.0, beat='부름', line_ref=ref('A', 0), note='게임에서 처음 또렷하게 들리는 사람 목소리. 자막은 정본 그대로. 세 번 부를 때마다 카메라가 한 칸씩 차사 쪽으로'),
  st(90.0, beat='따뜻함', cam={'mode': 'hold', 'framing': '고개, 바람이 지나가는 풀'}, act='찬 기운이 아니라 따뜻한 기운이 고개를 지나간다', note='찬 기운 규칙의 마지막 뒤집기(endings_s1 warmth)'),
  st(100.0, beat='대답', cam={'mode': 'close', 'to': 'player', 'time': 2.0, 'zoom': 1.4}, line_ref=ref('A', 1), note='차사가 이 게임에서 하는 유일한 말'),
  st(116.0, beat='명부', cam={'mode': 'cut', 'to': 'ledger_last', 'time': 3.0, 'framing': '해 질 녘, 명부 맨 끝 줄'}, act='해 질 녘. 명부 맨 끝 줄에 내 이름이 또렷하다',
     ui={'ledger_name_ref': {'file': 'endings_s1.json', 'fact': 'F73'}, 'fact_on': 'F73'}, note='이름 글자는 endings_s1 · soul_memories에서 읽는다(이 파일엔 없음)'),
  st(116.0, beat='명부', cond='B-18 천도(시즌 2)', act='그 줄에 온전한 인이 찍힌다', sfx=['cut.seal.set']),
  st(116.0, beat='명부', cond='B-18 파혼(시즌 2)', act='그 줄에 조각 인이 찍힌다. 가장자리가 깨져 있다', sfx=['cut.seal.set']),
  st(128.0, beat='쪽지', ui={'note_card': S3['keeper']['beats'][-1].split('"')[1], 'note_card_time': 5.0}, act='명부 여백 먹지기 쪽지'),
  st(140.0, beat='사슬', cam={'mode': 'close', 'to': 'player_wrist', 'time': 2.0, 'zoom': 1.6}, act='사슬이 손목에서 떨어진다', req=['cut.chain.fall(사슬이 흙 위로 감기며 떨어지는 소리)'], note='F63의 회수'),
  st(152.0, beat='선택', cam={'mode': 'hold', 'framing': '나루, 배 한 척과 사슬 하나'}, ui={'choice': ['건너간다', '남는다']}, note='입력 대기 동안 컷 시간은 멈춘다'),
  st(160.0, beat='건너간다', variant={'cross': {'camera': {'mode': 'follow', 'to': 'ferry', 'time': 30.0}, 'action': '배에 오른다. 줄 맨 끝에 서 있던 사람(S-048)이 함께 오른다'},
                                      'stay': {'camera': {'mode': 'close', 'to': 'chain', 'time': 2.0}, 'action': '차사가 떨어진 사슬을 스스로 집어 든다'}},
     note='S-048을 천도하지 않았다면 건너간다 판에선 줄 끝 빈자리에 그가 매일 부르던 입 모양만'),
  st(195.0, beat='저편', cond='건너간다 + B-12 천도(시즌 1)', cam={'mode': 'hold', 'framing': '저편 기슭'}, act='저편 기슭에 흑월이 서 있다. 그 곁에 붉은 갓끈의 사람(S-028 천도 시)'),
  st(195.0, beat='남는다', cond='남는다', cam={'mode': 'pull', 'zoom': 0.7, 'time': 8.0}, act='검은 갓의 차사가 나루에 남는다. 사슬은 이제 스스로 고른 것'),
  st(225.0, cam={'mode': 'fade_out', 'time': 4.0}, ui={'small_caption': '결말 A — 이름을 부르다'}),
  st(240.0, act='크레딧. 건너간다 → 새 회차는 새 차사 / 남는다 → 시즌 4로 그대로'),
 ]}
C31B = {'id': 'C-31B', 'branch': '결말 B — 번진 명부', 'trigger': 'B-31 눕히기 캐스팅 완료, F9 없음', 'duration': 180.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': False, 'lines': 1, 'canon': 'endings_s1.json final_endings.endings.B',
 'note': '대사 1줄(당할미, line_ref). 지붕에 오르지 않는다. 사슬은 풀리지 않고 가벼워진다. A로 가는 길은 시즌 1 다시 하기로 B-12 천도(F9) — 화면에서 가르치지 않는다',
 'steps': [
  st(0.0, beat='횃불', cam={'mode': 'two_shot', 'a': 'player', 'b': 'boss', 'time': 2.0, 'zoom': 1.2}, act='차사가 횃불을 받는다. 꺼진다. 백이 눕는다', sfx=['cut.torch.sink']),
  st(14.0, beat='새벽', cam={'mode': 'crane', 'dir': 'up', 'time': 10.0}, act='새벽. 차사가 흩어지지 않는다', sfx=['amb.dawn.birds']),
  st(30.0, beat='이름 없는 상여', cam={'mode': 'follow', 'to': 'bier', 'time': 20.0}, act='낮. 상여가 고개를 내려간다. 명정이 비어 있다', sfx=['mus.sangyeo.far'], note='명정(이름 쓰는 깃발)의 빈 천을 한 번 크게'),
  st(54.0, beat='열두째 자리', cam={'mode': 'crane', 'dir': 'down', 'time': 6.0}, act='둑의 열두째 자리에 몸이 묻힌다', ui={'fact_on': 'F72'}, note='B판에선 "누군가의 자리"로만 읽힌다(F9 없음)'),
  st(70.0, beat='무덤 앞', cam={'mode': 'hold', 'framing': '새 무덤 앞에 오래 선 당할미의 등'}, act='당할미가 무덤 앞에 오래 선다. 입술만 움직인다', note='지붕에 오르지 않는다. 그의 얼굴을 살피며 맞다/아니다를 가리는 장면 금지'),
  st(96.0, beat='한 줄', line_ref=ref('B', 0), note='결말 B의 한 줄. 이름이 없어도 부름으로 눕는다(F66)의 이승 쪽 메아리'),
  st(110.0, beat='명부', cam={'mode': 'cut', 'to': 'ledger_last', 'time': 3.0}, act='명부 맨 끝 내 자리는 번진 채다'),
  st(122.0, beat='쪽지', ui={'note_card': S3['keeper']['beats'][-1].split('"')[3], 'note_card_time': 6.0}, act='명부 여백 먹지기 쪽지'),
  st(136.0, beat='사슬', cam={'mode': 'close', 'to': 'player_wrist', 'time': 2.0}, act='사슬은 풀리지 않는다. 조금 가벼워진다', ui={'chain_weight': '-'}),
  st(165.0, cam={'mode': 'fade_out', 'time': 4.0}, ui={'small_caption': '결말 B — 번진 명부'}),
  st(180.0, act='계속 플레이(사슬이 가벼워진 채)'),
 ]}
C31C = {'id': 'C-31C', 'branch': '결말 C — 다음 검은 갓', 'trigger': 'B-31 깨뜨리기, 또는 업 60 이상 · 기억 조각 150 미만으로 처결 대기가 끝남', 'duration': 120.0, 'input_lock': True,
 'world': 'pause_enemies', 'skippable': False, 'lines': 0, 'canon': 'endings_s1.json final_endings.endings.C',
 'note': '대사 0. 벌이 아니라 거울 — 다음 회차 1막 멀리 혼 셋을 깨뜨리는 검은 갓이 나였다',
 'steps': [
  st(0.0, beat='깨짐', cam={'mode': 'shake', 'strength': 'big', 'time': 1.0}, act='나의 백이 깨진다. 횃불이 물속에서 흩어진다', sfx=['sfx.pahon.burst', 'cut.torch.sink']),
  st(10.0, beat='물', cam={'mode': 'hold', 'framing': '소 수면'}, act='소에 물이 찬다. 다시는 빠지지 않는다'),
  st(24.0, beat='빈자리', cam={'mode': 'crane', 'dir': 'down', 'time': 6.0, 'framing': '둑, 열한 무덤 옆 빈자리'}, act='둑의 열두째 자리는 영영 비어 있다'),
  st(40.0, beat='쪽지', ui={'note_card': S3['keeper']['beats'][-1].split('"')[5], 'note_card_time': 6.0}, act='명부 여백 먹지기 쪽지'),
  st(54.0, beat='짚신', cam={'mode': 'close', 'to': 'straw_shoes', 'time': 3.0, 'framing': '서낭당 사잣밥 상, 짚신을 고치는 손'}, act='당할미가 짚신을 고쳐 놓는다. 다음 날도, 그다음 날도',
     sfx=['cut.straw.set'], note='B-29 백 년 사잣밥 할미와 같은 손길(F69의 거울). 컷을 세 번 이어 붙여 날이 바뀌는 것만'),
  st(80.0, beat='사슬', cam={'mode': 'close', 'to': 'player_wrist', 'time': 2.0}, act='사슬의 끝이 내 손목으로 되돌아와 감긴다', sfx=['cut.chain.wrap'], note='사슬이 나 자신에게 묶인다'),
  st(96.0, beat='멀리', cam={'mode': 'pull', 'zoom': 0.5, 'time': 8.0, 'framing': '1막 첫 들판을 아주 멀리'}, act='아주 먼 들판에서 검은 갓 하나가 혼 셋을 깨뜨린다', note='다음 회차 1막의 그 장면과 같은 구도(거울). 설명하지 않는다'),
  st(110.0, cam={'mode': 'fade_out', 'time': 4.0}, ui={'small_caption': '결말 C — 다음 검은 갓'}),
  st(120.0, act='계속 플레이(사슬이 나 자신에게 묶인 채)'),
 ]}
CUTS += [C31A, C31B, C31C]

# 8막 내내 아침마다 — 당할미 사잣밥(⑨ B-29와 같은 밥상). 첫날 아침 한 번만 컷, 이후는 월드 그대로
CUTS.append({'id': 'S3-HALMI-TABLE', 'branch': '8막 아침 — 서낭당 사잣밥', 'trigger': '8막(C-28 뒤) 첫날 아침, 솔고개 서낭당 근처를 지날 때', 'duration': 10.0,
 'input_lock': False, 'world': 'run', 'skippable': True, 'lines': 0, 'walkable': True,
 'note': '대사 0. 같은 밥상이 ⑨ B-29에 나온다 — 그때 플레이어가 알아보게만. 결말 C의 거울',
 'steps': [st(0.0, cam={'mode': 'hold', 'framing': '서낭당 사잣밥 상, 밥 세 그릇 · 짚신 · 엽전'}, act='당할미가 사잣밥을 차린다. 밥 세 그릇, 짚신, 엽전', sfx=['cut.straw.set']),
           st(10.0, cam={'mode': 'return', 'to': 'player', 'time': 0.5})]})

# 쓰지 않는 None sfx 정리(조건부 표현에서 생긴 빈 칸)
for c in CUTS:
    for s in c['steps']:
        if 'sfx' in s and s['sfx'] is None: del s['sfx']
    c['steps'].sort(key=lambda x: x['t'])
    promote(c)

# ───── 자체 검사 ─────
ids = [c['id'] for c in CUTS]
assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
need = set()
for x in S3['cutscenes']:   # "C-23A/B" · "C-31A" 같은 표기를 낱개 id로 푼다
    base, *rest = x['id'].split('/')
    need.add(base)
    for r in rest: need.add(base[:-1] + r)
assert need <= set(ids), need - set(ids)
for b in BC:   # 보스마다 등장 · 처결 대기 컷이 있어야 한다
    assert cid(b, 'INTRO') in ids and cid(b, 'KNEEL') in ids, b
blob = json.dumps(CUTS, ensure_ascii=False)
for w in ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌'):
    assert w not in blob, w
# 말풍선(bubble) 대사는 시즌 3에 0줄. 결말 대사는 line_ref 3개(A 2 · B 1)
bubbles = [(c['id'], s['line']['text']) for c in CUTS for s in c['steps'] if s.get('line', {}).get('style') == 'bubble']
assert not bubbles, bubbles
refs = [(c['id'], s['line_ref']['path']) for c in CUTS for s in c['steps'] if 'line_ref' in s]
assert len(refs) == 3 and {r[0] for r in refs} == {'C-31A', 'C-31B'}, refs
# 컷 길이 안에서 끝나는지
for c in CUTS:
    assert all(s['t'] <= c['duration'] for s in c['steps']), c['id']
# 흑월 본명은 B-27 · C-27A에서만
for c in CUTS:
    if _ink in json.dumps(c, ensure_ascii=False):
        assert c['id'] in ('B27-LAY', 'C-27A'), c['id']

data = {
 '_설명': '시즌 3 「백의 밤」 실시간 컷신 대본(6막 ①⑤⑦ · 7막 ③④②⑥ · 8막 ⑧⑨⑩ · 물막이 골 소 · 결말 A/B/C). tools/cutscenes_s3.py로 생성. 형식은 cutscenes_s1 · s2와 같다. 서사 2026-10-25',
 'rules': {
  'protagonist_lines': '0(결말 A의 대답 한 줄만 — line_ref)',
  'lines': '시즌 3 보스 · 막 컷신 대사 0줄. 결말 대사는 A 2줄(당할미 · 차사) · B 1줄(당할미)뿐이고 글은 endings_s1.json에만 있다 — 이 파일은 line_ref(file · path)로 가리킨다. 기억 줄(memory) · 쪽지(note_card) · 입 모양은 대사로 세지 않는다',
  'line_ref': 'line_ref = {file, path, speaker, style:"voice"}. 코드는 path의 text를 읽어 목소리 + 자막으로 띄운다. 결말 A의 이름 글자(F73)도 ledger_name_ref로 같은 파일에서 읽는다',
  'verbs': '눕히기(LAY) = 천도의 백 버전, 캐스팅 2.0초. 깨뜨리기(BREAK) = 파혼의 백 버전, 즉시. B-23은 풀기 / 끊기(C-23A / C-23B가 처결 컷), B-31은 결말 컷(C-31A/B/C)이 처결 컷',
  'silence': '백은 말하지 않는다. 입 모양(칠성의 셈, 사공의 부름)은 자막 · 소리 없이 애니메이션으로만',
  'hidden': '먹지기 얼굴 · 이름 글, 어미의 이름, 사공의 이름은 화면에 쓰지 않는다. 흑월 본명은 B27-LAY에서 처음 글자로(C-27A 팻말까지)',
  'water': '아래층 물 주기는 S3-DUSK(물 빠짐) · S3-DAWN-WARN(새벽 30초 전) · S3-DAWN-PUSH(떠밀림, 벌 없음). ⑤ SeaCave는 거기에 시즌 1 ⑤의 50분 물때가 겹친다(썰물 밤에만 입구)',
  'rite': 'RITE-REVERSE(①~⑥ 낮) · LEDGER-REVERSE(⑦~⑩ 새벽 틈)는 틀이다. {last} · {middle} · {empty} · {line_row} · {clue_id} 자리에 season3_outline 단서 글과 memories_s3 글을 넣는다',
  'time': 't는 컷 시작부터 초. duration 안에서 끝난다. 결말 A의 선택(152초)에서는 입력을 기다리는 동안 시간이 멈춘다',
  'camera': 'cutscenes_s1.json rules.camera와 같다(+ tilt: 위아래로 고개 들기/숙이기)',
  'condition': 'condition이 붙은 박자는 그 조건일 때만. 같은 t에 조건이 다른 박자가 둘이면 맞는 하나만 쓴다',
  'variant': 'C-21 A/B = B-20 풀어내기/파혼 · C-27B break/ownerless · C-31A cross/stay',
  'sfx': 'sfx = 있는 소리 id, sfx_request = 아직 없는 소리(사운드팀 요청). 생긴 소리는 sfx_map.promote가 옮긴다',
  'skippable': '길게 눌러 건너뛰기. 건너뛰어도 보상 · 단서 · 세계 변화는 그대로. 결말 C-31A/B/C는 처음 한 번은 건너뛸 수 없다',
 },
 'cutscenes': CUTS,
}
json.dump(data, open(os.path.join(D, 'cutscenes_s3.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
req = sorted({r for c in CUTS for s in c['steps'] for r in s.get('sfx_request', [])})
print(len(CUTS), 'cutscenes,', len(req), 'sfx requests')
