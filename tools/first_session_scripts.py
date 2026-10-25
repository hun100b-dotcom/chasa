# 첫 세션 대본 두 가지: ① 오프닝 컷신 C-01(20초) ② 박돌쇠(S-001) 장례 3갈래
# 근거: SCENARIO-ACT1 프롤로그 1단계, FUNERAL-SEQUENCE §1~§3(기본형 = 박돌쇠).
# 중요한 원칙: 둘 다 "대사·자막·내레이션 0"이다(FUNERAL-SEQUENCE §2-1). 그래서 이 파일의 글자는
#   대부분 'sfx' 칸(소리 자막 — 소리가 아직 없는 지금 단계에서 무슨 소리가 나는지 알려 주는 대괄호 글)이다.
#   sfx 자막은 소리가 들어오면 꺼지는 것이 기본이고, 접근성 설정(청각 보조)에서만 다시 켠다.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_map import apply as sfx_apply, promote as sfx_promote  # 효과음 이름표 붙이기 / 생긴 소리로 옮기기
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'first_session_scripts.json')

def st(t, cam=None, act=None, sfx=None, line=None, control=None, note=None):
    s = {'t': t}
    if cam: s['camera'] = cam
    if act: s['action'] = act
    if sfx: s['sfx'] = sfx
    if line: s['line'] = line
    if control: s['control'] = control
    if note: s['note'] = note
    return s

opening = {
 'id': 'C-01', 'name': '오프닝 — 물', 'duration': 20.0, 'input_lock': True, 'clock': 'paused', 'skippable': False,
 'note': '처음 한 번만. 건너뛸 수 없다(20초). 누구의 기억인지 알려 주지 않는다 — 결말(B-31 나의 백, 물막이 골 소)에서 같은 물로 돌아온다',
 'lines': [],
 'steps': [
  st(0.0, cam={'mode': 'black'}, sfx='[물소리]', note='검은 화면. 3초 동안 소리 자막만'),
  st(3.0, cam={'mode': 'fade_in', 'time': 1.5, 'framing': '둑 위에서 내려다봄, 아주 어둡게'}, act='횃불 하나가 둑 아래로 내려간다. 횃불을 든 사람은 보이지 않는다(불빛만)', sfx='[빗소리]'),
  st(7.0, act='불빛이 물가에 닿는다. 물이 불어 있다. 불빛이 잠시 멈췄다가, 물로 들어간다'),
  st(10.0, cam={'mode': 'follow', 'to': 'torch', 'time': 2.0}, act='횃불이 물에 잠긴다. 불이 꺼지기 전 물속이 주황으로 한 번 밝아진다', sfx='[물에 잠기는 소리]'),
  st(13.0, cam={'mode': 'black', 'time': 0.5}, act='어둠', sfx='[물소리가 멀어진다]'),
  st(15.0, cam={'mode': 'close', 'framing': '손 하나(얼굴 없음)'}, act='어둠 속에서 쇠사슬이 손목에 한 바퀴, 두 바퀴 감긴다', sfx='[쇠사슬 소리]'),
  st(18.0, cam={'mode': 'fade_out', 'time': 1.0}, act='사슬이 조여지는 순간 컷'),
  st(19.0, cam={'mode': 'black'}, sfx='[바람 소리]', note='다음: 서낭당 고개에서 깨어남(first_session.json 0:20). 시계가 흐르기 시작한다'),
 ]}

funeral = {
 'id': 'FUN-S001', 'soul': 'S-001', 'name': '박돌쇠 장례(기본형)', 'when': '박돌쇠를 처결한 다음 낮, 그 집(대장간) 앞에 처음 다가갈 때',
 'rule': '하루에 장례 한 번. 첫 이름혼 박돌쇠가 우선(FUNERAL-SEQUENCE §1)',
 'branches': [
  {'branch': '천도', 'id': 'FUN-S001-TENDO', 'duration': 70.0, 'skippable': True, 'clock': 'running', 'reward': None,
   'note': '대사·자막·내레이션 0. 상여소리는 가사가 들리지 않게 웅얼거림. 사람들은 차사를 피하지 않고 지나간다(충돌 없음)',
   'lines': [],
   'steps': [
    st(0.0, cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 6.0}, act='아침의 솔고개 마을. 대장간 문이 닫혀 있고 대문에 조등. 차사는 길 건너', sfx='[바람] [먼 닭울음]', control='none'),
    st(6.0, cam={'mode': 'low_move', 'to': 'forge_inside', 'time': 8.0}, act='불 꺼진 화로, 식은 쇳덩이, 풀무 손잡이에 걸린 낡은 수건', sfx='[요령 소리 한 번]', control='none', note='어젯밤 기억 "풀무질을 멈추자 쇳물이 식었다"의 멈춘 것'),
    st(14.0, cam={'mode': 'quarter', 'height': 'low'}, act='상여가 집을 나선다. 앞에 요령잡이(갑술 영감), 상여꾼 여덟, 뒤로 만장. 아내가 상여 끝을 붙잡고 따라 나온다', sfx='[요령] [곡소리] [멀리 웅얼거리는 상여소리]', control='walk', note='만장이 차사의 몸을 스치고 지나간다'),
    st(26.0, cam={'mode': 'side_track', 'to': 'procession'}, act='마을 어귀 장승 앞(금줄 밑) 노제. 맏아들 용득이 술잔을 올린다. 막내딸 금순은 울지 않고 아버지 짚신을 품에 안고 있다', sfx='[곡소리가 커졌다가 잦아든다]', control='walk', note='아무도 고개를 돌리지 않는다. 업 10 미만이면 마을 개 한 마리가 한쪽 귀를 세워 차사가 선 쪽을 잠깐 보다 만다(정말 보았는지는 모호하게). 업 10 이상이면 개가 짖고 달아난다'),
    st(40.0, cam={'mode': 'tilt_up', 'to': 'sky'}, act='행렬이 고개 너머로 사라진다. 만장 끝자락 하나가 뜯겨 차사 발밑에 떨어진다', sfx='[상여소리가 멀어진다]', control='walk', note='고개에 투명한 경계(따라갈 수 없다)'),
    st(52.0, cam={'mode': 'move', 'to': 'forge_inside'}, act='먼저 돌아온 용득이 화로에 불을 붙인다. 서툴게 풀무를 밟는다. 불이 오른다. 화면 가장자리에 쇳물 주황이 한 번 번졌다 사라진다', sfx='[풀무 소리] [불꽃 튀는 소리]', control='none'),
    st(62.0, cam={'mode': 'pull_out', 'to': 'gate', 'then': 'quarter'}, act='대문 밖 사잣밥: 밥 세 그릇, 짚신 세 켤레, 엽전 몇 닢. 차사가 그 앞에 잠깐 선다(자동)', sfx='[바람] [멀리서 요령 마지막 한 번]', control='none', note='집을 수 없다. 수치 변화 없음'),
    st(70.0, act='페이드 없이 평소 낮 화면', control='restore'),
   ]},
  {'branch': '파혼', 'id': 'FUN-S001-PAHON', 'duration': 0.0, 'skippable': False, 'clock': 'running', 'reward': None,
   'note': '장면이 없다는 것 자체가 장면. 안내 문구도 띄우지 않는다',
   'lines': [],
   'steps': [
    st(0.0, act='대장간 대문에 조등만 걸려 있다. 문은 닫혀 있다. 다가가도, 오래 서 있어도 아무 일도 일어나지 않는다', control='walk', note='트리거 없음. 조등 소품 하나만 둔다. 사잣밥도 없다'),
   ]},
  {'branch': '처결 못 함', 'id': 'FUN-S001-PENDING', 'duration': 20.0, 'skippable': True, 'clock': 'running', 'reward': None,
   'note': '대기 시간 초과·귀환 실패 등으로 박돌쇠를 처결하지 못했을 때. 장례가 아니므로 대사 0 원칙의 예외로 한 줄만 둔다',
   'lines': [{'speaker': '박돌쇠 아내', 'text': '……여기는 어째 이리 차누.', 'style': 'bubble', 'duration': 2.0}],
   'steps': [
    st(0.0, cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 4.0}, act='같은 마당. 상은 아직 차려지지 않았다. 대장간 문에 빗장', sfx='[바람]', control='walk'),
    st(4.0, act='아내가 대장간 문 앞에 서서 문을 두드리려다 손을 내린다'),
    st(8.0, act='아내가 남편이 서 있던 대장간 문 앞에서 제 팔을 감싼다', line={'speaker': '박돌쇠 아내', 'text': '……여기는 어째 이리 차누.', 'style': 'bubble', 'duration': 2.0}, note='차사 위치와 상관없이 늘 나온다. 찬 기운은 차사가 아니라 아직 보내지 못한 남편 혼이 머물던 자리에 남은 것(서사 10-25 기준: 지나가는 차사의 한기는 당할미만 느낀다). 소설 1장과 같은 대사'),
    st(12.0, act='아내가 부엌으로 들어간다. 마당이 비고, 빗장 지른 문만 남는다', sfx='[개가 한 번 낑낑대는 소리]'),
    st(20.0, act='조작 복귀', control='restore', note='이날 저녁 명부 맨 아래 줄에 박돌쇠가 같은 종류(갓 죽은 혼)로 다시 적히고, 먹지기 쪽지 "어제 이름을 오늘 또 적었다."가 붙는다'),
   ]},
 ]}

sfx_apply(opening)
sfx_promote(opening)
for b in funeral['branches']:
    b['id_backup'] = b['id']
    sfx_apply(b)
    sfx_promote(b)
    del b['id_backup']

data = {'_설명': '첫 세션 대본 — 오프닝 C-01(20초) + 박돌쇠 장례 3갈래. tools/first_session_scripts.py로 생성. 서사 확정 2026-10-25.',
        'rules': {'dialogue': '오프닝과 장례(천도)는 대사·자막·내레이션 0. 화면에 글로 주제를 쓰지 않는다',
                  'sfx': 'sfx = 재생할 효과음 id(사운드팀 data/sfx_files.json). sfx_request = 아직 없는 소리(사운드팀 요청). caption = 소리 자막 글(접근성 설정에서만 표시)',
                  'control': 'none = 조작 없음 / walk = 걷기만 / restore = 조작 복귀',
                  'names': '맏아들 용득, 막내딸 금순, 요령잡이 갑술 영감(소설 1부와 같음)'},
        'opening': opening, 'funeral': funeral}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
