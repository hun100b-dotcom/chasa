# -*- coding: utf-8 -*-
# 2막 장례 대본 8개: ③ 붉은재 산성 아랫마을 4(S-049~052) + ④ 쇳골 광부촌 4(S-067~070).
# 근거: SCENARIO-ACT2 "③의 장례"·"④의 장례" 표(#2 멈춘 것 / #6 다시 움직이는 것).
# 틀(박자·시간·파혼·처결 못 함)은 1막과 똑같다 → funerals_act1.py의 함수를 그대로 가져다 쓴다.
#   왜: 장례마다 모양이 다르면 코드가 장례마다 따로 만들어야 한다. 바뀌는 것은 "사물 두 개"와 배경뿐이게 한다.
# ④ 광부촌 장례는 짧고 조용하다(다음 날 또 갱에 들어가야 하므로). 그래서 곡소리를 낮추고 구경꾼 대신 교대 광부가 잠깐 비켜 선다.
# 실행: python3 tools/funerals_act2.py → docs/narrative/funerals_act2.json
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import funerals_act1 as F   # st, SCENE, build를 빌려 쓴다(가져올 때 1막 파일은 다시 쓰지 않는다)
from funerals_act1 import st

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'narrative', 'funerals_act2.json')

# 2막 배경 두 곳을 1막 표에 더한다
F.SCENE[3] = {'morning': '아침의 산성 아랫마을. {house} 대문에 조등. 무너진 성벽이 마을 위로 보인다. 차사는 길 건너에 서 있다',
              'cap': '[바람] [먼 닭울음] [요령 한 번]', 'sfx': ['amb.field', 'cut.yoryeong.ring'], 'req': ['amb.rooster(먼 닭울음)'],
              'proc': '상여가 집을 나서 큰 무덤 쪽 산길로 오른다. 앞에 요령잡이, 뒤로 만장. 만장이 차사의 몸을 스친다. 아무도 차사를 피하지 않는다',
              'away': '행렬이 산길 굽이로 사라진 뒤', 'hush': '[정적]'}
F.SCENE[4] = {'morning': '아침의 광부촌. 판잣집 사이로 갱 입구가 보인다. {house} 문에 조등. 차사는 길가에 서 있다',
              'cap': '[먼 곡괭이 소리] [요령 한 번]', 'sfx': ['cut.yoryeong.ring'], 'req': ['amb.mine(먼 곡괭이·수레 소리)'],
              'proc': '상여가 판잣집 사이 좁은 길을 지난다. 갱에 들어가던 광부들이 등잔을 든 채 잠깐 비켜 서고, 행렬이 지나면 다시 갱으로 간다. 만장이 차사의 몸을 스친다',
              'away': '행렬이 광부촌 아랫길로 사라진 뒤', 'hush': '[먼 곡괭이 소리가 멎는다]'}
QUIET = ('[요령] [낮은 곡소리]', ['cut.yoryeong.ring'], ['vo.wail(낮게, 짧게)'])   # ④ 광부촌 행렬 소리

FUNERALS = [
 # ───── ③ 붉은재 산성 아랫마을 ─────
 {'id': 'FUN-S049', 'soul': 'S-049', 'region': 3, 'name': '술도가 노인 최씨 장례', 'house': '술도가',
  'stopped': '술도가 뒤뜰에 빈 술독이 줄지어 엎어져 있다. 서른일곱 개',
  'moving': st(25.0, '손녀가 큰 무덤 앞에 술을 붓는다. 잔을 세며 붓다가, 다 부은 뒤 한 잔을 더 붓는다(할아버지 몫)',
               cap='[술 따르는 소리]', req=['cut.pour.liquor(잔에 술 따르는 소리)'], cam={'mode': 'side_track', 'to': 'big_tomb'}, control='walk',
               note='깊은 박자 ②. 기억 색(탁주 흰빛). 잔 수를 화면에 글로 세지 않는다'),
  'pending_act': '손녀가 술독 하나를 열어 보고 도로 덮는다'},
 {'id': 'FUN-S050', 'soul': 'S-050', 'region': 3, 'name': '약초 아낙 분녀 장례', 'house': '분녀네',
  'stopped': '봉당에 마른 약초 바구니가 놓여 있다. 약초가 바스러졌다',
  'moving': st(25.0, '이웃 아낙이 화살골 바위틈에 가서 약초를 캔다. 녹슨 촉 박힌 바위를 손으로 한 번 짚고 나서 캔다',
               cap='[호미 소리]', req=['cut.hoe.dig(호미로 흙 파는 소리)'], cam={'mode': 'move', 'to': 'arrow_rock'}, control='walk',
               note='깊은 박자 ②. 기억 색(약초 녹빛)'),
  'pending_act': '이웃 아낙이 바구니를 들어 보다 내려놓는다'},
 {'id': 'FUN-S051', 'soul': 'S-051', 'region': 3, 'name': '석수 판돌 장례', 'house': '판돌네',
  'stopped': '산성 비탈에 반쯤 쌓다 만 성벽. 맨 위 돌 자리가 비었다. 정이 돌 틈에 꽂힌 채다',
  'moving': st(25.0, '제자가 마지막 성돌을 얹는다. 정으로 돌에 글자를 새긴다(스승의 이름, 화면에서는 읽히지 않는다)',
               cap='[정 소리]', req=['cut.chisel.tap(정으로 돌 새기는 소리)'], cam={'mode': 'low_move', 'to': 'wall_top'}, control='walk',
               note='깊은 박자 ②. 기억 색(화강 회색)'),
  'pending_act': '제자가 성벽 앞에 서서 돌을 들었다가 내려놓는다'},
 {'id': 'FUN-S052', 'soul': 'S-052', 'region': 3, 'name': '벌초꾼 만석 장례', 'house': '만석네',
  'stopped': '헛간 벽에 녹슨 낫이 걸려 있다',
  'moving': st(25.0, '아들이 큰 무덤 벌초를 한다. 아버지 낫을 숫돌에 갈아 쓴다',
               cap='[낫질 소리]', req=['cut.sickle.cut(풀 베는 낫질)'], cam={'mode': 'tilt_up', 'to': 'big_tomb'}, control='walk',
               note='깊은 박자 ②. 기억 색(풀 초록)'),
  'variant': st(31.0, '(기수 대돌을 천도한 뒤라면) 봉분에 새겨진 이름들 사이를 아들의 낫질이 조심스럽게 비켜 간다',
                control='walk', cond='B-05 천도함', note='SCENARIO-ACT2 ③의 장례 표'),
  'pending_act': '아들이 낫을 들고 헛간 문 앞에 섰다가 도로 건다'},
 # ───── ④ 쇳골 광부촌 (짧고 조용하다) ─────
 {'id': 'FUN-S067', 'soul': 'S-067', 'region': 4, 'name': '광부 순돌 장례', 'house': '순돌네', 'proc_sound': QUIET,
  'stopped': '목패 걸이에 순돌의 목패 하나가 아직 걸려 있다. 다른 고리들은 아침이라 비었다',
  'moving': st(25.0, '동료 광부가 걸이에서 순돌의 목패를 떼어 가족에게 건넨다. 가족은 목패를 품에 넣는다. 하루가 끝났다는 표시다',
               cap='[나무패 떼는 소리]', req=['cut.tag.unhook(고리에서 나무패 떼는 소리)'], cam={'mode': 'low_move', 'to': 'tag_board'}, control='walk',
               note='깊은 박자 ②. 기억 색(석탄 검정). ACT2 표의 "빈 고리"는 목패를 뗀 뒤의 모습으로 읽는다(떼기 전엔 걸려 있어야 뗄 수 있다)'),
  'pending_act': '목패가 걸린 그대로다. 교대 광부 하나가 그 목패를 보다 지나간다'},
 {'id': 'FUN-S068', 'soul': 'S-068', 'region': 4, 'name': '선탄장 아낙 복례 장례', 'house': '복례네', 'proc_sound': QUIET,
  'stopped': '선탄장 평상 위 한 자리가 비어 있다. 골라 놓다 만 석탄 무더기',
  'moving': st(25.0, '딸이 어머니 자리에 앉아 석탄을 고른다. 일을 마치고 손을 씻는다. 씻은 물이 검다. 딸이 그 물을 오래 본다',
               cap='[석탄 고르는 소리] [물소리]', req=['cut.coal.sort(평상에서 석탄 고르는 소리)'], cam={'mode': 'side_track', 'to': 'sorting_bench'}, control='walk',
               note='깊은 박자 ②. 기억 색(석탄 검정)'),
  'pending_act': '평상의 빈자리에 아무도 앉지 않는다'},
 {'id': 'FUN-S069', 'soul': 'S-069', 'region': 4, 'name': '국밥집 주인 장씨 장례', 'house': '국밥집', 'proc_sound': QUIET,
  'stopped': '국밥집 벽에 외상 장부가 걸려 있다. 줄마다 이름 대신 번호뿐이다',
  'moving': st(25.0, '아들이 외상 장부를 내려 번호 옆에 이름을 하나씩 적어 넣는다. 모르는 번호에서 붓이 멈췄다가, 지나가는 광부를 불러 세우는 몸짓을 한다',
               cap='[붓 소리]', req=['cut.brush.write(붓으로 종이에 쓰는 소리)'], cam={'mode': 'low_move', 'to': 'ledger_wall'}, control='walk',
               note='깊은 박자 ②. 기억 색(국물 주황). 부르는 말은 들리지 않는다(몸짓만). 장부 글씨는 읽히지 않게'),
  'pending_act': '아들이 솥 앞에 선다. 장부는 벽에 걸린 그대로다'},
 {'id': 'FUN-S070', 'soul': 'S-070', 'region': 4, 'name': '노새 몰이 갑돌 장례', 'house': '노새 마구간', 'proc_sound': QUIET,
  'stopped': '마구간 여물통이 비었다. 노새는 말뚝에 매인 채 서 있다',
  'moving': st(25.0, '풀려난 노새가 상여 뒤를 따라 갱 입구까지 간다. 입구 앞에서 멈춰 선다',
               cap='[노새 발굽 소리]', req=['cut.mule.hoof(노새 발굽 소리)'], cam={'mode': 'side_track', 'to': 'mule'}, control='walk',
               note='깊은 박자 ②. 기억 색(노새 갈색). 노새는 차사를 보지 않는다'),
  'pending_act': '노새가 말뚝에 매인 채 갱 쪽을 본다'},
]

# 기억 문장은 원본(soul_memories.json)에서 그대로 가져온다(손으로 옮겨 적다 틀리지 않게)
SRC = json.load(open(os.path.join(os.path.dirname(OUT), 'soul_memories.json'), encoding='utf-8'))
MEM = {s['id']: s['memory'] for s in SRC['souls']}
for f in FUNERALS:
    f['memory'] = MEM[f['soul']]

data = {
    '_설명': '2막 장례 8개(③ 산성 아랫마을 4 + ④ 쇳골 광부촌 4). tools/funerals_act2.py로 생성. 틀과 규칙은 funerals_act1.json과 같다. 서사 2026-10-25',
    'rules': {
        'same_as_act1': '대사 0, 천도 48초(두 박자만 깊게), 파혼 조등만, 처결 못 함 12초, 하루 한 번, condition 박자',
        'mine': '④ 광부촌 장례는 곡소리를 낮게, 구경꾼 대신 교대 광부가 잠깐 비켜 섰다가 갱으로 간다',
        'numbers': '서른일곱·번호를 화면 글로 세지 않는다(보스 단서와 겹침). 사물로만 보인다',
        'names': '2막 산 사람은 이름 없이 역할로(npc_act2.json)',
    },
    'funerals': [F.build(f) for f in FUNERALS],
}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(data['funerals']), 'funerals')
