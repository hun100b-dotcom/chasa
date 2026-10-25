# -*- coding: utf-8 -*-
# 시즌 3 "백의 밤" 장례 대본 — 백(장례를 못 치른 몸)을 눕힌 이튿날, 그 몸이 비로소 받는 장례.
# 근거: memories_s3.json(백 120의 장례 종류 funeral = reverse/carve/group/False/True),
#       season3_outline.json(world.day_clues · regions · boss_clues[].lay 의 "이튿날 낮/새벽 틈" 문장 · facts F48~F72),
#       npc_s3.json(after_lay — 보스 장례에 서는 산 사람), cutscenes_s3.json(RITE-REVERSE · LEDGER-REVERSE · THREAD-RISE · C-27A).
# 왜 시즌 1 장례와 다른가:
#   시즌 1 장례는 "혼을 보낸 다음 날 산 사람이 몸을 묻는" 장면이었다. 시즌 3의 백은 그 장례를 끝내 받지 못한 몸이다.
#   그래서 시즌 3 장례는 늘 "늦은 장례"다. 몸은 이미 없거나(물·흙 속) 너무 오래되었다. 산 사람은 몸 대신
#   ① 거꾸로 장례(①⑤ 물 밑의 몸): 물이 돌려준 물건 하나를 묻는다(F53)
#   ② 이름 새기기(②③④⑥ 땅 밑의 몸): 이미 묻힌 자리의 빈 돌 · 목패 · 팻말에 이름을 새긴다(F57 — 묻혔다고 누운 게 아니다)
#   ③ 새벽 틈(⑧⑨⑩ 산 사람이 없는 곳): 장례 대신 위층의 그 혼이 일을 놓고 줄에 서거나(⑧⑨), 꽂힌 사슬이 쓰러진다(⑩, F68)
#   ④ 함께 묻기: 무리(①의 열한 몸 · ⑤ 일곱 · ③ 큰 무덤 · ④ 막장)는 무리가 다 처결된 이튿날 한 번에. 보스 장례와 겹친다
# 화면 규칙(시즌 1과 같음): 대사 · 자막 · 내레이션 0. 산 사람은 차사를 보지 못한다. 대괄호 글은 소리 자막(청각 보조 설정에서만).
#   이름을 부르는 장면은 "입 모양만"(소리 없음). 글자(비석 · 팻말)는 읽히지 않을 만큼 작게 — 보스 장례 B-27(C-27A)만 예외.
# 쓰지 않는 것: 주인공 이름 · 그 의례 이름 · 추위 말(연출 글도), 먹지기의 얼굴 · 이름, 어미의 이름, 사공의 이름,
#   S-185 "열두째 빈자리"와 S-188 "여덟째"의 뜻(8막 전 설명 금지 — 카메라가 머물지 않는다).
# 실행: python3 tools/funerals_s3.py → docs/narrative/funerals_s3.json
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_map import promote  # 사운드팀이 이미 만든 소리는 요청(sfx_request) → 있는 소리(sfx)로 옮긴다

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'narrative', 'funerals_s3.json')
MEM = os.path.join(HERE, '..', 'docs', 'narrative', 'memories_s3.json')
OUTLINE = os.path.join(HERE, '..', 'docs', 'narrative', 'season3_outline.json')


def st(t, act, cap=None, sfx=None, req=None, cam=None, control=None, note=None, cond=None):
    """장면 한 박자(1막 funerals_act1.py와 같은 모양). sfx = 이미 있는 소리, req = 아직 없는 소리(요청)."""
    s = {'t': t, 'action': act}
    if cam: s['camera'] = cam
    if cap: s['caption'] = cap
    if sfx: s['sfx'] = sfx
    if req: s['sfx_request'] = req
    if control: s['control'] = control
    if note: s['note'] = note
    if cond: s['condition'] = cond   # 이 조건일 때만 이 박자를 쓴다(아니면 건너뜀)
    return s


# ───────────────── 관할별 아침(또는 새벽 틈) 풍경 ─────────────────
# 왜 관할마다 따로: 같은 틀을 120번 보면 장례가 "농사"가 된다. 첫 컷의 공기(소리 · 빛)만이라도 그 땅의 것으로.
REGION = {
 1: {'name': '솔고개', 'when': 'day',
     'place': {'DamBed': '아침의 보릿들 둑. 둑 아래, 밤에 물이 빠졌던 흙탕 자리가 아직 젖어 있다. 차사는 둑 위에 서 있다',
               'PoolBed': '아침의 물막이 골 나루. 물은 다시 찼고, 나루 말뚝만 젖은 채 드러나 있다. 차사는 나루 위 버드나무 곁에 서 있다'},
     'cap': '[바람] [먼 닭울음] [물 흐르는 소리]', 'sfx': ['amb.rooster'], 'req': ['amb.river.morning(아침 강물, 잔잔함)']},
 5: {'name': '갯마을', 'when': 'day',
     'place': {'WreckBed': '썰물 뒤 아침의 갯마을 포구. 갯벌에 물길 자국이 남아 있다. 차사는 그물 너는 마당 끝에 서 있다',
               'SeaCave': '썰물 뒤 아침의 망부석 곶. 곶 밑 바다굴 입구는 다시 물에 잠겼다. 차사는 곶 길에 서 있다'},
     'cap': '[파도] [갈매기]', 'sfx': ['amb.harbor'], 'req': []},
 3: {'name': '붉은재', 'when': 'day',
     'place': {'ArrowRoots': '아침의 화살골. 바위 뿌리 사이로 녹슨 촉이 박힌 자리가 보인다. 차사는 골짜기 입구에 서 있다',
               'TombPit': '아침의 큰 무덤 앞. 봉분 한쪽이 밤사이 조금 내려앉았다. 차사는 무덤 아래 길에 서 있다'},
     'cap': '[바람] [먼 까마귀]', 'sfx': ['amb.wind.gust'], 'req': ['amb.crow.far(먼 까마귀 한 번)']},
 4: {'name': '쇳골', 'when': 'day',
     'place': {'FloodedShaft': '아침의 쇳골 갱 입구. 갱 물이 빠졌던 자국이 입구 돌에 띠처럼 남았다. 차사는 목패 걸이 맞은편에 서 있다',
               'SealedFace': '아침의 쇳골 막장 입구. 쌓은 돌 틈으로 아무것도 새지 않는다. 차사는 레일 끝에 서 있다'},
     'cap': '[먼 곡괭이 소리] [수레 바퀴]', 'sfx': ['amb.mine'], 'req': []},
 2: {'name': '검은여울', 'when': 'day',
     'place': {'LimePit': '아침의 무덤골 역병 구덩이 터. 풀 사이에 이름 없는 빈 돌들이 줄지어 있다. 차사는 구덩이 가장자리에 서 있다',
               'ClinicFloor': '아침의 옛 역병막 터. 마루는 꺼졌고 약장 하나가 기울어 서 있다. 차사는 문간에 서 있다'},
     'cap': '[바람] [먼 장터 웅성거림]', 'sfx': ['amb.market'], 'req': []},
 6: {'name': '도성', 'when': 'day',
     'place': {'GatePit': '아침의 성문 밖 구덩이 무덤. 팻말 없는 흙무더기들. 차사는 성벽 그늘에 서 있다',
               'BridgeFound': '아침의 큰 다리 밑. 다리 기초 돌 사이로 물이 흐른다. 차사는 다리 그늘에 서 있다'},
     'cap': '[먼 장터 웅성거림] [물 흐르는 소리]', 'sfx': ['amb.market'], 'req': []},
 8: {'name': '명부전 담장 밖', 'when': 'dawn',
     'place': {'InkSilt': '새벽 틈의 먹방. 벼루들 위로 첫 빛이 비스듬히 든다. 갈던 손들이 아직 돈다. 차사는 문간에 서 있다',
               'QuarterCellar': '새벽 틈의 서리 숙사. 일하다 잠든 자세의 서리들, 그 사이로 첫 빛. 차사는 마루 끝에 서 있다'},
     'cap': '[먹 가는 소리] [새벽 바람]', 'sfx': ['cut.ink.grind'], 'req': ['amb.dawn.still(바람 없는 새벽)']},
 9: {'name': '빈 고을', 'when': 'dawn',
     'place': {'Ondol': '새벽 틈의 빈 고을 고샅. 집집 문간에 차려 둔 밥상. 차사는 고샅 어귀에 서 있다',
               'SealFloor': '새벽 틈의 인장 굴 입구. 굴 벽의 붉은 자국이 첫 빛에 바래 보인다. 차사는 굴 앞 마당에 서 있다'},
     'cap': '[새벽 바람] [먼 종 한 번]', 'sfx': [], 'req': ['amb.dawn.still(바람 없는 새벽)']},
 10: {'name': '열째 관할', 'when': 'dawn',
      'place': {'ChainRoots': '새벽 틈의 사슬 무덤. 꽂힌 사슬들이 첫 빛에 긴 그림자를 늘인다. 차사는 무덤 가장자리에 서 있다',
                'WellBottom': '새벽 틈의 처음 마을 첫 우물. 새끼줄이 우물 턱에 걸려 있다. 차사는 우물 곁에 서 있다'},
      'cap': '[새벽 바람] [사슬 스치는 소리]', 'sfx': ['cut.chain.drag'], 'req': []},
}
# ⑨는 시즌 2 B-18을 천도해 새벽이 왔을 때만 새벽 틈이 있다(world.day_clues). 아니면 같은 장면을 새벽 시각에 등불 빛으로.
NINE_NO_DAWN = '시즌 2 B-18을 천도하지 않아 ⑨에 새벽이 오지 않았다면, 같은 장면을 새벽 시각(새벽 2분)에 등불 빛으로 튼다. 첫 빛 대신 등잔 하나'


# ───────────────── 백마다 장면 재료 ─────────────────
# reverse(①⑤): (멈춘 것 = 물이 돌려준 물건, 다시 움직이는 것 = 묻는 장면, 소리 요청)
REVERSE = {
 'S-181': ('둑 아래 박다 만 말뚝 셋. 그 밑 흙탕에 지게 멜빵 하나가 떠밀려 와 있다',
           '마을 사내 둘이 멜빵을 펴서 둑 밑 흙에 반듯이 눕혀 묻는다. 둘 다 말이 없다. 흙을 다진 손바닥 자국이 남는다',
           ['cut.hoe.dig(호미로 흙 파는 소리)']),
 'S-182': ('덜 박힌 말뚝 하나가 기울어 있다. 그 곁에 메 자루 토막이 떠밀려 와 있다',
           '갑술 영감이 메를 들고 와 덜 박힌 말뚝을 마저 박는다. 세 번. 그다음 자루 토막을 말뚝 밑에 묻는다',
           ['cut.stake.drive(메로 말뚝 박는 둔한 소리, 세 번)']),
 'S-183': ('보리밭 둑길 끝, 물 빠진 자리에 빛바랜 댕기 하나가 걸려 있다',
           '분이 또래 처녀 셋이 댕기를 보리밭 가장자리에 묻는다. 하나가 묻은 자리 위에 보리 이삭 하나를 꽂는다',
           ['cut.hoe.dig(호미로 흙 파는 소리)']),
 'S-187': ('둑 옆 헛묘(옷만 묻은 무덤). 그 앞에 짚신 한 짝이 떠밀려 와 있다',
           '학수 어머니가 헛묘 곁에 짚신을 묻는다. 무덤을 내려다보며 입 모양으로 이름을 한 번 부른다. 소리는 없다. 이번엔 울지 않는다',
           ['cut.hoe.dig(호미로 흙 파는 소리)']),
 'S-188': ('둑 밑 흙탕에 보릿단 하나와 아이 손에 맞는 작은 낫이 떠밀려 와 있다',
           '아이들이 보릿단 끈을 풀어 이삭을 밭에 흩는다. 작은 낫은 둑 밑에 묻는다. 짐이 없어진 끈만 둑 위에 남는다',
           ['cut.sickle.cut(낫 소리, 아주 작게)'],
           ),
 'S-189': ('나루 말뚝에 반 토막 난 삿대가 걸려 있다',
           '갑술 영감이 삿대 토막을 나루터 버드나무 밑에 묻는다. 묻은 자리가 물 쪽을 향하게 흙을 비스듬히 다진다',
           ['cut.hoe.dig(호미로 흙 파는 소리)']),
 'S-190': ('소 가장자리 물 빠진 자리에 고무신 한 짝이 떠밀려 와 있다',
           '삼월이 딸이 품에 안고 자던 다른 한 짝을 가져온다. 두 짝을 나란히 놓고 묻는다',
           ['cut.hoe.dig(호미로 흙 파는 소리)']),
 'S-192': ('숯막의 숯가마가 식어 있다. 가마 앞에 숯 자루 끈 하나가 떠밀려 와 있다',
           '숯막 사람들이 끈을 가마 옆에 묻는다. 그다음 가마에 다시 불을 넣는다. 연기가 오른다',
           ['cut.kiln.light(숯가마에 불 넣는 소리)']),
 'S-193': ('갯벌 물길 자국 끝에 조개 캐는 호미 하나가 박혀 있다',
           '갯벌 아낙들이 호미를 곶 아래 헛묘 곁에 묻는다. 묻고 나서 하늘을 한 번 올려다보는 아낙이 있다',
           ['cut.hoe.dig(호미로 흙 파는 소리)']),
 'S-194': ('헛묘 위에 그물찌 하나가 얹혀 있다. 밤사이 바다가 갖다 놓았다',
           '복동 어머니가 헛묘를 열지 않고 그 곁에 그물찌를 묻는다. 묻은 자리 앞에서 입 모양으로 아들을 부른다. 이번엔 소리가 흩어질 물이 없다',
           ['cut.hoe.dig(호미로 흙 파는 소리)']),
 'S-195': ('바위 끝에 망사리가 걸려 있다. 몸보다 먼저 뭍으로 온 그것',
           '해녀들이 망사리를 곶 아래 묻는다. 묻고 나서 물가에 나란히 서서 숨비소리를 한 번씩 낸다',
           ['vo.sumbi(숨비소리, 휘파람 같은 긴 숨. 여럿이 한 번씩)']),
 'S-198': ('선창 끝에 노 손잡이 토막 하나가 떠밀려 와 있다',
           '뱃사람들이 노 손잡이를 묻고 뱃노래를 부른다. 메기는 소리 없이 받는 소리만. 메기던 사람이 없다',
           ['mus.boat.answer(뱃노래 받는 소리만, 가사 안 들리게)']),
 'S-199': ('모래 위에 부싯돌 하나가 놓여 있다',
           '포구 사람 하나가 부싯돌로 불을 쳐 등잔 하나를 켠다. 등잔을 헛묘 앞에 두고, 부싯돌은 그 곁에 묻는다',
           ['cut.flint.strike(부싯돌 치는 소리, 두 번)']),
 'S-203': ('망부석 바위 아래, 아이 손에 맞는 미역 바구니 하나가 걸려 있다',
           '포구 아이들이 바구니를 망부석 아래 묻는다. 한 아이가 바위 위를 올려다보며 손을 흔든다. 이번엔 물이 가리지 않는다',
           ['cut.hoe.dig(호미로 흙 파는 소리)']),
}

# carve(②③④⑥): (빈 것 = RITE-REVERSE 마지막 컷의 빈 돌 · 목패 · 팻말, 새기는 사람, 새기는 장면, 소리 요청)
CARVE = {
 # ② 검은여울 — 묘지기가 새긴다. 위 겹(몇 해 전 역병) 이름은 의원 약장 감초 밑 종이, 아래 겹(사십 년 전)은 서생 명단의 사본(F61)
 'S-241': ('구덩이 위 겹 줄의 빈 돌. 돌 위에 마른 약초 한 줌', '묘지기',
           '묘지기가 감초 냄새 밴 종이를 펴 놓고 이름을 새긴다. 역병막에서 살아 나온 아낙 하나가 다 새긴 돌 위에 손을 잠깐 얹는다', 'upper'),
 'S-242': ('빈 돌들이 줄지어 있다. 맨 끝 한 자리엔 돌이 없다', '묘지기',
           '묘지기가 새 돌 하나를 지고 와 맨 끝 빈자리에 놓는다. 그 돌에 이름을 새긴다. 줄이 끝까지 찬다', 'upper'),
 'S-243': ('아래 겹 가장자리, 이끼가 덮인 빈 돌', '묘지기',
           '묘지기가 이끼를 손으로 걷어 낸다. 누렇게 바랜 명단 사본을 보며 획이 많은 이름을 천천히 새긴다', 'lower'),
 'S-244': ('기운 약장 맨 아래 칸이 빠져 있다. 감초 냄새', '묘지기',
           '묘지기가 이름을 새기고, 약장 맨 아래 칸에서 감초 한 뿌리를 꺼내 돌 앞에 둔다', 'upper'),
 'S-245': ('무덤골 상엿집. 상여 멜빵 한 자리가 비어 있다', '묘지기와 상여꾼들',
           '상여꾼들이 빈 상여를 메고 와 돌 앞에 한 번 내려놓았다가 든다. 그가 마흔한 번째로 멘 쪽에 누운 셈이다. 묘지기가 이름을 새긴다', 'upper'),
 'S-246': ('구덩이 위 겹, 아주 작은 빈 돌', '묘지기',
           '묘지기가 작은 돌에 이름을 새긴다. 두 글자. 새기는 손이 다른 돌보다 느리다', 'upper'),
 'S-247': ('구덩이 가장자리에 석회 자루 하나가 놓인 채다', '묘지기',
           '묘지기가 석회 자루를 치우고 그 자리 돌에 이름을 새긴다. 관아 쪽 길에서 젊은 사령 하나가 멀리 서서 갓을 벗는다', 'upper'),
 'S-248': ('아래 겹 줄의 빈 돌. 명단 사본의 그 이름 획만 유난히 반듯하다', '묘지기',
           '묘지기가 명단 사본의 획을 그대로 따라 새긴다. 한 획 한 획. 다른 이름보다 오래 걸린다', 'lower'),
 'S-249': ('큰 빈 돌 곁에 아주 작은 돌이 하나 붙어 있다', '묘지기',
           '묘지기가 큰 돌에 이름을 새기고, 작은 돌을 큰 돌 품 쪽으로 바짝 붙여 놓는다', 'upper'),
 'S-250': ('아래 겹, 이름 칸이 없는 빈 돌', '묘지기',
           '묘지기가 명단 사본을 처음부터 끝까지 넘겨 본다. 찾지 못한다. 돌은 빈 채로 둔다 — 차사가 긋는 판(반쪽)이 기본', 'lower'),
 'S-251': ('아래 겹 줄의 빈 돌. 그 앞에 끈 떨어진 명단 주머니', '묘지기',
           '묘지기가 명단 사본에서 그 이름을 찾아 새긴다. 명단을 나른 사람의 이름이 명단 안에 있다', 'lower'),
 'S-252': ('옛 역병막 터 문지방이 반쯤 썩어 있다', '묘지기',
           '묘지기가 이름을 새긴 돌을 문 쪽이 아니라 안쪽을 향하게 세운다. 나가는 발소리를 듣던 자리에서 이번엔 안을 본다', 'upper'),
 # ③ 붉은재 화살골 — 사당 노인(N-303)과 석수 제자가 새긴다. 건너편 이름은 소매 속 수놓은 이름 그대로(F59)
 'S-221': ('바위 뿌리 밑 작은 빈 돌', '석수 제자',
           '석수 제자가 소매 속에서 나온 수놓은 이름을 보며 새긴다. 글씨가 이쪽 글씨와 다르다. 다르게 둔다', None),
 'S-225': ('바위 틈에 꽂힌 깃대 토막. 색이 바랬다', '석수 제자',
           '석수 제자가 이름을 새기고, 사당 노인이 깃대 토막을 돌 옆에 다시 꽂는다. 이쪽 깃대 곁에', None),
 'S-226': ('바위 뿌리 사이에 끊어진 활시위', '석수 제자',
           '석수 제자가 작은 돌에 이름을 새긴다. 끊어진 시위를 돌 밑에 묻는다', None),
 'S-228': ('바위 밑에 약초가 무성하다', '약초 캐는 이웃',
           '약초 캐는 이웃이 바위 밑 약초를 캐지 않고 둔다. 그 곁 돌에 정으로 이름을 새긴다. 서툰 글씨', None),
 # ④ 쇳골 — 광부들이 새 나무에 새긴다. 이름을 모르면 번호(반쪽 · 목패 번호). 시즌 1 B-08 천도면 전원 이름으로
 'S-231': ('갱 입구 버팀목 줄에 하나가 빠진 자리', '광부들',
           '광부들이 새 버팀목 하나를 깎아 그 자리에 세운다. 버팀목 옆면에 이름을 새긴다', None),
 'S-232': ('갱 입구 점호판. 한 줄이 비어 있다', '광부들',
           '광부 하나가 점호판 빈 줄에 이름을 새긴다. 다 새긴 뒤 다 같이 점호판을 한 번 본다. 대답은 하지 않는다', None),
 'S-233': ('목패 걸이 아래 걸상. 빈 고리가 흔들린다', '광부들',
           '광부들이 걸상 등받이에 문지기의 이름을 새긴다. 빈 고리 하나를 떼어 걸상 다리에 묶는다', None),
 'S-234': ('산 중턱 첫 굴 입구 바위', '광부들',
           '늙은 광부가 첫 굴 입구 바위에 이름을 새긴다. 다 새기고 굴 안쪽을 향해 고개를 한 번 숙인다', None),
 'S-235': ('갱 입구 산신 자리. 막걸리 잔이 말라 있다', '광부들',
           '광부들이 산신 자리 옆 돌에 이름을 새기고 막걸리를 붓는다. 산신 잔이 아니라 그 돌 앞에', None),
 'S-237': ('선탄장 석탄 고르던 판. 감독 자리가 비었다', '광부들',
           '선탄장 사람들이 판 모서리에 이름을 새긴다. 그 자리에 앉지는 않는다', None),
 'S-240': ('갱 입구 등불 기둥. 등불 하나 걸 고리가 비었다', '광부들',
           '광부 하나가 기둥에 이름을 새기고 빈 고리에 등불을 하나 건다. 낮인데도 켜 둔다', None),
 # ⑥ 도성 — 팻말. 아들 문지기(N-602) · 서적상 노인 · 움막촌 사람들 · 다리 밑 아이들. 별명도 이름이다(B-11 규칙)
 'S-253': ('팻말 없는 흙무더기 하나', '움막촌 사람',
           '움막촌 사람 하나가 팻말을 세운다. 세운 뒤 팻말 머리를 고향 쪽 길로 조금 돌려놓는다', None),
 'S-254': ('"일꾼 셋"이라고만 적힌 낡은 팻말 하나', '아들 문지기',
           '아들 문지기가 낡은 팻말 곁에 새 팻말 하나를 세운다. 셋 가운데 한 사람의 이름', None),
 'S-255': ('팻말 없는 흙무더기, 검은여울 쪽 길가', '움막촌 사람',
           '움막촌 사람이 팻말을 세운다. 검은여울에서 지워진 이름이 여기서 처음 나무에 쓰인다', None),
 'S-256': ('움막촌 쪽 흙무더기', '움막촌 사람들',
           '움막촌 사람들이 여럿 와서 팻말을 함께 세운다. 손이 많다. 그가 받은 아이들이 이제 어른이다', None),
 'S-257': ('구덩이 맨 위 흙무더기', '아들 문지기',
           '아들 문지기가 팻말을 세운다. 서적상 노인 가게의 새 붓으로 쓴 글씨', None),
 'S-258': ('다리 기초 돌. 정 자국들', '다리 고치는 석수들',
           '다리 고치는 석수들이 기초 돌 하나에 정으로 이름을 새긴다. 팻말 대신 돌. 정 자국 사이에', None),
 'S-260': ('흙무더기 위에 탈 끈 한 가닥', '장터 광대패',
           '장터 광대패가 팻말을 세우고 탈 하나를 팻말에 건다. 장구가 짧게 한 장단 울린다', None),
 'S-261': ('서생이 누운 자리에서 멀지 않은 흙무더기', '서적상 노인',
           '서적상 노인이 팻말을 쓴다. 세울 자리를 서생 쪽으로 한 걸음 옮긴다', None),
 'S-262': ('다리 밑 흙무더기 하나. 둘이 함께 누운 자리', '다리 밑 아이들',
           '다리 밑 아이들이 팻말 하나를 세운다. 별명이 둘 — 업은 사람과 업힌 아이. 아이들이 팻말 앞에 나란히 쪼그려 앉는다', None),
 'S-264': ('성문 밖 길가 흙무더기', '아들 문지기',
           '아들 문지기가 팻말을 세운다. 팻말 앞에 누가 놓고 간 보릿대 한 줌이 있다', None),
}
CARVE_SFX = {2: 'cut.chisel.tap(정으로 돌 새기는 소리)', 3: 'cut.chisel.tap(정으로 돌 새기는 소리)',
             4: 'cut.knife.carve(칼로 나무 새기는 소리)', 6: 'cut.brush.write(붓으로 팻말 쓰는 소리)'}
# 반쪽(F51): 새길 이름을 아는 산 사람이 없으면 차사가 사슬 끝으로 대신 긋는다 — 이름이 아니라 한 줄
HALF = {2: '빈 돌', 3: '빈 돌', 4: '새 나무', 6: '빈 팻말'}

# dawn(⑧⑨⑩): (그 자리의 일, 일을 놓는 장면, 혼이 이미 없을 때 남은 물건이 하는 일)
DAWN = {
 'S-265': ('붓을 쥔 채 엎드린 신참 서리', '신참 서리가 붓을 붓꽂이에 꽂는다. 일어나 줄 쪽으로 걸어 나간다', '붓꽂이에 꽂히지 않은 붓 하나가 첫 빛에 마른다'),
 'S-266': ('먹물에 팔을 담근 채 먹을 가는 일꾼', '일꾼이 갈던 먹을 벼루 위에 눕혀 놓는다. 팔을 먹물에서 꺼내 닦지 않고 나간다', '벼루 위의 먹이 처음으로 눕혀져 있다'),
 'S-267': ('벼루를 닦는 아이', '아이가 닦던 벼루를 엎어 물기를 뺀다. 걸레를 벼루 곁에 개어 두고 나간다', '엎어진 벼루 하나. 걸레가 개켜 있다'),
 'S-268': ('상소문을 베끼던 서리', '서리가 베끼던 종이를 덮는다. 지운 줄이 있던 자리를 손가락으로 한 번 짚고 나간다', '덮인 종이 한 장'),
 'S-269': ('붓을 든 채 오래 망설이는 자세의 서리. 옆자리는 비어 있다', '서리가 붓을 옆자리 쪽에 내려놓고 나간다. 옆자리는 화면 밖', '붓 하나가 옆자리 쪽을 향해 놓여 있다'),
 'S-270': ('아궁이 앞에 앉은 부엌 할미', '할미가 밥 한 그릇을 차려 마루 끝 차사 쪽에 놓는다. 아궁이 불을 끄지 않고 나간다', '마루 끝에 밥 한 그릇. 아궁이 불은 살아 있다'),
 'S-271': ('먹 덩이에 이름표를 붙이는 혼', '혼이 마지막 이름표 한 장을 꺼내 제 먹 덩이에 붙인다. 그리고 나간다', '이름표가 붙은 먹 덩이 하나'),
 'S-272': ('벼루 곁에서 입술을 움직이는 혼', '혼의 입술이 멈춘다. 벼루지기 쪽을 한 번 보고 나간다', '벼루 곁 빈자리에 먹 묻은 손자국'),
 'S-273': ('숨을 아끼며 먹을 가는 서리', '서리가 숨을 크게 한 번 쉰다. 먹을 놓고 나간다', '반쯤 간 먹 하나'),
 'S-274': ('서랍 열쇠를 쥔 창고지기', '창고지기가 열쇠를 자물쇠에 꽂아 둔 채 나간다', '자물쇠에 꽂힌 열쇠'),
 'S-275': ('손바닥을 오므린 서리', '서리가 손바닥을 펴 본다. 번진 먹을 씻지 않고 나간다', '책상 위 손바닥 자국 하나'),
 'S-276': ('인 찍는 소리를 세며 조는 서리', '멀리서 인 찍는 소리가 아홉 번 난다. 서리가 눈을 뜨고 나간다', '아홉째 문서함 앞 빈 걸상'),
 'S-277': ('아홉째 문 앞에 백 년 서 있던 늙은이', '늙은이가 처음으로 문 앞에 앉는다. 잠깐. 일어나 줄 쪽으로 간다', '문 앞 땅에 발 자국 둘이 깊게 패어 있다'),
 'S-278': ('아랫목 밥상 앞에 앉은 아이', '아이가 밥상 앞에서 일어난다. 문간에서 한 번 돌아보고 나간다', '아랫목 밥상 앞 방석 하나'),
 'S-279': ('문설주에 숯으로 적힌 이름들', '혼이 문설주의 이름들 옆을 손으로 쓸고 나간다', '문설주의 숯 이름들'),
 'S-280': ('장터 끝에서 짚신을 엮는 노인', '노인이 반만 엮인 짚신을 길가 짚신 줄 맨 끝에 놓는다. 마저 엮지 않는다. 일어나 간다', '짚신 줄 맨 끝에 반만 엮인 한 켤레'),
 'S-281': ('개울가에 앉은 혼', '혼이 개울물에 손을 씻는다. 일어나 간다', '개울 돌 위의 젖은 손자국'),
 'S-282': ('빈 나무 문패를 깎는 목수', '목수가 문패에 자기 이름을 새겨 제 집 문에 건다. 그리고 간다', '빈 문패 하나가 문에 걸려 있다'),
 'S-283': ('방울을 쥔 무당', '무당이 방울을 흔든다. 처음으로 소리가 난다. 한 번', '방울이 문고리에 걸려 있다. 바람 없이 한 번 울린다'),
 'S-284': ('종채를 쥔 채 조는 아이', '아이가 눈을 뜨고 종을 한 번 친다. 그리고 간다', '종채가 종 밑에 놓여 있다'),
 'S-285': ('인장 굴 입구를 서성이는 혼', '혼이 이마를 소매로 닦는다. 붉은 물이 조금 묻어난다. 굴을 등지고 간다', '굴 입구 땅의 맴돌던 발자국이 끝난다'),
 'S-286': ('굴 안쪽을 들여다보는 혼', '혼이 굴 안쪽을 한 번 더 보고 돌아선다', '굴 입구에 선 발자국 한 쌍'),
 'S-287': ('굴 벽 이마 높이 붉은 자국', '굴 벽의 붉은 자국 하나가 첫 빛에 바랜다. 그 자리의 혼이 굴을 나선다', '굴 벽 붉은 자국 하나가 바랜다'),
 'S-288': ('혼잣말하는 혼', '혼의 입술이 멈춘다. 마지막으로 제 이름을 입 모양으로 부르고 간다', '돌 위에 앉았던 자국'),
 # ⑩ 사슬 무덤(ChainRoots) — 사슬이 빠져 쓰러진다(F68). 혼이 이미 없어도 사슬은 쓰러진다
 'S-289': ('녹슨 사슬 하나가 꽂혀 있다', None, '사슬이 흙에서 빠져 쓰러진다. 쓰러진 자리 흙이 봉긋하게 내려앉는다. 무덤 하나가 끝난다'),
 'S-290': ('사슬 사이를 세며 다니는 혼', '혼이 세던 손가락을 하나 접는다. 쓰러진 사슬 수만큼. 그리고 간다', '사슬 하나가 쓰러져 있다'),
 'S-291': ('"백삼"이 새겨진 사슬', None, '사슬이 쓰러진다. 새김이 흙 쪽으로 엎어져 숫자가 보이지 않는다'),
 'S-292': ('사슬이 꽂히지 않은 무덤 가장자리 흙', None, '아무것도 꽂히지 않았던 흙에서 녹슨 사슬 끝이 조금 비어져 나왔다가 옆으로 눕는다'),
 'S-293': ('사슬 무덤 위에 갓 하나', None, '갓이 바람 없이 굴러 사슬 무덤 흙 위 머리 자리에 엎어진다'),
 'S-294': ('반짝이는 가루가 묻은 사슬', None, '사슬이 쓰러지며 손바닥만 한 은빛 가루가 흙에 스민다'),
 'S-295': ('사슬 없이 고리 한 마디만 꽂힌 자리', None, '고리 한 마디가 흙 속으로 가라앉는다'),
 'S-296': ('녹슬어 끊어진 사슬 토막', None, '끊어진 사슬 토막이 쓰러진다. 이 무덤에서 가장 오래된 것'),
 # ⑩ 첫 우물(WellBottom)
 'S-297': ('우물가에서 두레박 물을 맛보는 노파', '노파가 두레박 물을 한 모금 맛본다. 두레박을 우물 턱에 걸고 간다', '두레박이 우물 턱에 걸려 있다'),
 'S-298': ('우물 물에 비친 하늘', None, '우물 물이 잔잔해진다. 비치는 것은 하늘뿐이다'),
 'S-299': ('대패질하던 목수', '목수가 대패를 내려놓고 간다', '대패 하나'),
 'S-300': ('손바닥을 펴 내밀고 선 혼', '혼이 펴 있던 손을 처음으로 가볍게 오므린다. 그리고 간다', '우물가 땅에 펴진 손바닥 자국'),
}
DAWN_SFX = {'InkSilt': 'cut.tool.set(붓 · 먹 · 열쇠를 내려놓는 작은 소리)', 'QuarterCellar': 'cut.tool.set(붓 · 먹 · 열쇠를 내려놓는 작은 소리)',
            'Ondol': 'cut.footstep.leave(맨발 걸음이 멀어진다)', 'SealFloor': 'cut.footstep.leave(맨발 걸음이 멀어진다)',
            'ChainRoots': 'cut.chain.fall(사슬이 흙 위로 쓰러지는 소리)', 'WellBottom': 'cut.footstep.leave(맨발 걸음이 멀어진다)'}
DAWN_SPECIAL = {'S-283': 'cut.bell.shaman(무당 방울, 한 번)', 'S-284': 'cut.bell.small(작은 종, 한 번)', 'S-276': 'cut.seal.set.nine(멀리서 인 찍는 소리 아홉 번, 한 파일)',
                'S-297': 'cut.well.bucket(두레박 줄 소리)', 'S-298': 'cut.water.still(물이 잔잔해지는 소리)'}

# 무리(group) 장례 — 무리의 백이 다 처결된 이튿날 한 번에. 보스 장례와 겹치면 보스 장례가 이것이다
GROUP_OF = {'S-184': 'G-ELEVEN', 'S-185': 'G-ELEVEN', 'S-186': 'G-ELEVEN',
            'S-200': 'FUN-B22', 'S-201': 'FUN-B22', 'S-202': 'FUN-B22'}
for _sid in ('S-217', 'S-218', 'S-219', 'S-220', 'S-222', 'S-223', 'S-224', 'S-227'): GROUP_OF[_sid] = 'FUN-B24'
for _sid in ('S-229', 'S-230', 'S-236', 'S-238', 'S-239'): GROUP_OF[_sid] = 'FUN-B25'


# ───────────────── 틀 ─────────────────
def opening(r, zone, stopped, empty_note):
    R = REGION[r]
    return [
        st(0.0, R['place'][zone], cap=R['cap'], sfx=R['sfx'] or None, req=R['req'] or None,
           cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 5.0}, control='none'),
        st(5.0, stopped, cap='[정적]', cam={'mode': 'low_move', 'to': 'stopped_thing', 'time': 6.0}, control='none',
           note=empty_note),
    ]


def reverse_day(b):
    r, z = b['region'], b['zone']
    stopped, moving, req = REVERSE[b['id']][:3]
    steps = opening(r, z, stopped, '깊은 박자 ①: RITE-REVERSE 마지막 컷의 "빈 몸 자리"에 밤사이 물이 물건 하나를 돌려 놓았다(F53). 플레이어가 혼자 알아차리게')
    steps += [
        st(11.0, '사람들이 하나둘 모인다. 상여는 없다. 맨 앞 사람이 그 물건을 두 손으로 든다. 요령이 한 번 울린다. 아무도 차사를 피하지 않는다',
           cap='[요령 한 번] [발소리]', sfx=['cut.yoryeong.ring'], cam={'mode': 'quarter', 'height': 'low'}, control='walk',
           note='몸이 없는 늦은 장례. 곡소리 없음 — 너무 오래된 죽음이라 울음보다 일손이 먼저다'),
        st(19.0, moving, cap='[흙 덮는 소리]', req=req, cam={'mode': 'low_move', 'to': 'grave'}, control='walk',
           note=f'깊은 박자 ②. 기억 색({b["tint"]})이 화면 가장자리에 한 번 번졌다 사라진다'),
        st(30.0, '흙을 다 덮은 자리에 떼 한 장. 사람들이 흩어진다. 물가 쪽으로 먼 바람', cap='[바람]',
           cam={'mode': 'pull_out', 'to': 'grave', 'then': 'quarter'}, control='walk'),
        st(36.0, '페이드 없이 평소 낮 화면', control='restore'),
    ]
    return steps


def carve_day(b):
    r, z = b['region'], b['zone']
    empty, who, act, layer = CARVE[b['id']]
    steps = opening(r, z, empty, '깊은 박자 ①: RITE-REVERSE 마지막 컷의 "빈 것"(빈 돌 · 목패 · 팻말) 그 자리. 묻혔다고 누운 게 아니다(F57)')
    steps += [
        st(11.0, f'{who}이(가) 연장을 들고 온다. 그 자리 앞에 무릎을 꿇는다. 아무도 차사를 피하지 않는다',
           cap='[발소리]', cam={'mode': 'quarter', 'height': 'low'}, control='walk',
           note={'upper': '위 겹 이름 — 의원 약장 감초 밑 종이(F61)', 'lower': '아래 겹 이름 — 서생 명단의 사본(F61). 글씨체가 위 겹과 달라 보이게'}.get(layer)),
        st(19.0, act, cap='[새기는 소리]', req=[CARVE_SFX[r]], cam={'mode': 'close', 'to': 'carving', 'time': 1.5}, control='walk',
           note=f'깊은 박자 ②. 글자는 읽히지 않을 만큼 작게. 기억 색({b["tint"]})이 한 번 번졌다 사라진다'),
        st(30.0, '새긴 자리 앞에 물 한 사발. 사람이 연장을 챙겨 돌아간다', cap='[바람]',
           cam={'mode': 'pull_out', 'to': 'marker', 'then': 'quarter'}, control='walk'),
        st(36.0, '페이드 없이 평소 낮 화면', control='restore'),
    ]
    if r == 4:
        steps.insert(4, st(26.0, '(번호로 눕혔다면) 이름 대신 목패 번호가 새겨진다', cond='번호로 눕힘(이름 단서 없음, 시즌 1 B-08 천도 아님)',
                           control='walk', note='④ 반쪽 — 산 사람이 아는 것이 번호뿐이다(regions.4.special)'))
    return steps


def half_branch(b):
    """반쪽(F51): 이름을 아는 산 사람이 없을 때. 차사가 사슬 끝으로 대신 긋는다 — 이름이 아니라 한 줄."""
    r = b['region']
    return {'branch': '반쪽', 'duration': 14.0, 'skippable': True,
            'condition': '이름을 모른 채 눕힘(F66 — 차사가 이름 없이 불러 눕힘). 짝 혼 없음 · 낮 단서 없음',
            'steps': [
                st(0.0, f'{REGION[r]["place"][b["zone"]]}. {HALF[r]} 하나가 비어 있다. 아무도 오지 않는다', cap='[바람]',
                   cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 3.0}, control='walk'),
                st(4.0, f'{HALF[r]} 앞에 다가가면 상호작용(F) 표시가 뜬다', control='walk', note='안내 문구 없음. 표시만'),
                st(6.0, f'(F를 누르면) 차사가 사슬 끝으로 {HALF[r]}에 한 줄을 긋는다. 이름이 아니라 한 줄', req=['cut.chain.scratch(사슬 끝으로 돌 · 나무를 긋는 가는 소리)'],
                   cam={'mode': 'close', 'to': 'marker', 'time': 1.0}, control='none',
                   note='반쪽(F51). 누르지 않으면 아무 일도 없다(벌 없음). 지나가던 산 사람 하나가 그 줄을 보고 고개를 갸웃한다'),
                st(14.0, '조작 복귀', control='restore'),
            ]}


def dawn(b):
    r, z = b['region'], b['zone']
    place, leave, left = DAWN[b['id']]
    sfx = [DAWN_SFX[z]] + ([DAWN_SPECIAL[b['id']]] if b['id'] in DAWN_SPECIAL else [])
    steps = [st(0.0, REGION[r]['place'][z], cap=REGION[r]['cap'], sfx=REGION[r]['sfx'] or None, req=REGION[r]['req'] or None,
                cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 4.0}, control='none',
                note='⑦~⑩엔 산 사람이 없다. 장례 대신 새벽 틈에 그 자리의 일이 끝난다(F65 · F68)'),
             st(4.0, place, cap='[정적]', cam={'mode': 'low_move', 'to': 'stopped_thing', 'time': 5.0}, control='none',
                note='깊은 박자 ①: 어젯밤 아래층에서 본 몸의 자세와 같은 자세(위아래가 겹친다)')]
    if leave:
        steps += [st(10.0, leave, req=sfx, cam={'mode': 'side_track', 'to': 'soul'}, control='walk',
                     cond='그 혼이 아직 그 자리에 있음(시즌 2에서 처결 안 함)',
                     note=f'깊은 박자 ②. 그 혼은 ⑦ 줄로 간다. 기억 색({b["tint"]})이 한 번 번졌다 사라진다'),
                  st(10.0, left, req=sfx[1:] or None, cam={'mode': 'low_move', 'to': 'left_thing'}, control='walk',
                     cond='그 혼이 이미 없음(시즌 2에서 천도 — 이미 줄에 있다 / 파혼 — 주인 없는 백)',
                     note='깊은 박자 ② 대신. 남은 물건만 움직인다')]
    else:
        steps += [st(10.0, left, req=sfx, cam={'mode': 'low_move', 'to': 'chain'}, control='walk',
                     note=f'깊은 박자 ②. 무덤 하나가 끝난다(F68). 기억 색({b["tint"]})이 한 번 번졌다 사라진다')]
    steps += [st(17.0, '첫 빛이 조금 더 든다', cap='[새벽 바람]', control='walk'), st(20.0, '조작 복귀', control='restore')]
    return steps


def break_branch(b, scene):
    return {'branch': '깨뜨림', 'duration': 0.0, 'skippable': False,
            'steps': [st(0.0, scene, control='walk', note='트리거 없음. 장면 없음. 안내 문구 없음. 그 자리는 이 상태로 시즌 끝까지 남는다')]}


BREAK_SCENE = {
    'reverse': '그 자리에 물건은 오지 않는다. RITE-REVERSE 마지막 컷의 빈 몸 자리 그대로. 사람들은 지나간다',
    'carve': '빈 돌 · 목패 · 팻말은 비어 있는 그대로다. 산 사람이 그 앞을 지나간다',
    'dawn8': '그 일꾼은 계속 일한다. 새벽 틈에도 손이 멈추지 않는다',
    'dawn9': '그 혼은 그 자리에 그대로 있다. 새벽 틈이 지나간다',
    'dawn10': '사슬은 꽂힌 그대로다',
}


def short_of(steps, n_moving, is_day):
    """같은 날 같은 관할의 두 번째부터: 깊은 박자 ②만 남긴 10초 판(장례가 농사처럼 느껴지지 않게)."""
    mv = [dict(s) for s in steps if s['t'] == n_moving]
    for s in mv: s['t'] = 0.0
    return mv + [st(8.0, '사람들이 흩어진다' if is_day else '첫 빛이 조금 더 든다', control='walk'), st(10.0, '조작 복귀', control='restore')]


def build_baek(b):
    k, r = b['funeral'], b['region']
    base = {'id': 'FUN-' + b['id'], 'baek': b['id'], 'name': b['name'], 'region': r, 'zone': b['zone'],
            'kind': {'reverse': '거꾸로 장례(다시 재생)', 'carve': '이름 새기기', 'group': '함께 묻기', False: '장례 없음', True: '이미 장례 받음'}[k] if r < 8 or k != 'reverse' else '새벽 틈',
            'memory_link': b['memory']}
    if b['id'] == 'S-263':  # 까치 — 왕초(S-262)와 함께 눕혀야 하고 장례도 하나
        return dict(base, branches=[], see='FUN-S-262', note='왕초(S-262)와 함께 눕혀야 하고 장례도 하나 — 팻말 하나에 별명 둘')
    if k is True:
        return dict(base, branches=[], note='이미 장례를 받은 백(다리 밑 아이들이 별명으로 묻어 줌). 상호작용 없이 기억만 읽힌다. 무덤 위 녹슨 사슬(F63)')
    if k is False:
        if r == 7:
            return dict(base, branches=[], see='THREAD-RISE', note='⑦엔 산 사람이 없고 새벽 틈 명부도 이 몸을 가리키지 않는다. 눕히는 순간 THREAD-RISE(위 줄에서 발목 실이 풀려 올라감)가 곧 장례다')
        if b['id'] == 'S-191':
            return dict(base, branches=[], note='소 밑의 무명 백. 이름을 아는 산 사람이 없어 장례가 없다. 눕힐 때 차사가 대신 부른 것이 전부(반쪽, F51)')
        return dict(base, branches=[], note='바다가 물건도 돌려주지 않은 몸(⑤). 장례 장면 없음. 눕힌 다음 썰물 밤, 그 자리 모래가 평평하다(장면 밖 풍경)')
    if k == 'group':
        return dict(base, branches=[], see=GROUP_OF[b['id']], note='무리의 백이 다 처결된 이튿날 함께 묻는다. 깨뜨린 백은 이름은 새겨지되 그 줄에만 먹이 들지 않는다')
    when = REGION[r]['when']
    if when == 'day' and k == 'reverse':
        steps, kb, mv = reverse_day(b), 'reverse', 19.0
    elif when == 'day':
        steps, kb, mv = carve_day(b), 'carve', 19.0
    else:
        steps, kb, mv = dawn(b), f'dawn{r}', 10.0
    lay = {'branch': '눕힘', 'id': base['id'] + '-LAY', 'duration': 36.0 if when == 'day' else 20.0,
           'skippable': True, 'clock': 'running', 'steps': steps}
    if r == 9:
        lay['note'] = NINE_NO_DAWN
    short = {'branch': '눕힘(같은 날 둘째부터)', 'id': base['id'] + '-SHORT', 'duration': 10.0, 'skippable': True, 'clock': 'running',
             'steps': short_of(steps, mv, when == 'day')}
    branches = [lay, short, dict(break_branch(b, BREAK_SCENE[kb]), id=base['id'] + '-BREAK')]
    if k == 'carve':
        branches.append(dict(half_branch(b), id=base['id'] + '-HALF'))
    for br in branches:
        promote(br)
    out = dict(base, when='그 백을 눕힌 이튿날 ' + ('낮, 그 자리에 처음 다가갈 때' if when == 'day' else '새벽 틈, 그 자리에 처음 다가갈 때'),
               branches=branches)
    if b['id'] == 'S-262':
        out['also'] = 'S-263(까치) — 둘은 함께 눕혀야 하고 장례도 하나(팻말 하나에 별명 둘)'
    if b['id'] == 'S-250':
        out['default_branch'] = '반쪽'
    return out


# ───────────────── 무리 · 보스 장례 ─────────────────
def day_boss(fid, boss, r, zone, name, trig, steps, brk, dur=40.0, extra=None):
    out = {'id': fid, 'boss': boss, 'name': name, 'region': r, 'zone': zone, 'kind': '보스 장례',
           'when': trig,
           'branches': [{'branch': '눕힘', 'id': fid + '-LAY', 'duration': dur, 'skippable': True, 'clock': 'running', 'steps': steps},
                        {'branch': '깨뜨림', 'id': fid + '-BREAK', 'duration': 0.0, 'skippable': False,
                         'steps': [st(0.0, brk, control='walk', note='트리거 없음. 장면 없음. season3_outline boss_clues 깨뜨리기 문장 그대로')]}]}
    if extra: out.update(extra)
    for br in out['branches']: promote(br)
    return out


GROUPS = [
 {'id': 'G-ELEVEN', 'name': '열한 몸 장례', 'region': 1, 'zone': 'DamBed', 'kind': '함께 묻기',
  'members': ['S-184', 'S-185', 'S-186', '열한 몸 덩어리 백'],
  'when': '열한 몸(S-184 · S-185 · S-186과 덩어리 백)이 다 처결된 이튿날 낮, 보릿들 둑에 처음 다가갈 때',
  'branches': [{'branch': '눕힘', 'id': 'G-ELEVEN-LAY', 'duration': 40.0, 'skippable': True, 'clock': 'running', 'steps': [
      st(0.0, REGION[1]['place']['DamBed'], cap=REGION[1]['cap'], sfx=REGION[1]['sfx'], req=REGION[1]['req'],
         cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 5.0}, control='none'),
      st(5.0, '둑 위에 마을 사람들이 거의 다 나와 있다. 큰 돌 하나를 굴려 온다', cap='[돌 굴리는 소리] [발소리]',
         req=['cut.stone.roll(큰 돌을 굴리는 둔한 소리)'], cam={'mode': 'quarter', 'height': 'low'}, control='walk'),
      st(13.0, '돌을 둑 위에 세운다. 석수가 이름을 하나씩 새긴다. 한 이름이 끝날 때마다 사람들 가운데 누군가 입 모양으로 그 이름을 따라 부른다',
         cap='[정으로 돌 새기는 소리]', req=['cut.chisel.tap(정으로 돌 새기는 소리)'], cam={'mode': 'close', 'to': 'stone', 'time': 2.0}, control='walk',
         note='깊은 박자 ②. 열한 이름. 글자는 읽히지 않게. B-02(월화) 천도판이면 새기는 손이 빠르다 — 이름이 다 또렷이 남아 있었다'),
      st(27.0, '열한째 이름 뒤에 한 자리가 더 비어 있다. 석수는 손을 멈추지 않고 정을 거둔다',
         cam={'mode': 'pull_out', 'to': 'stone', 'time': 1.5}, control='walk',
         note='F52. 카메라가 이 빈칸에 머물지 않는다(당기면서 지나간다). 8막 전에는 설명하지 않는다. 결말 쪽 뜻은 endings_s1 정본'),
      st(33.0, '사람들이 돌 앞에 술 한 잔씩을 붓고 흩어진다. 둑 아래 물이 반짝인다', cap='[술 붓는 소리] [바람]', req=['cut.pour.liquor(잔에 술 붓는 소리)'], control='walk'),
      st(40.0, '페이드 없이 평소 낮 화면', control='restore')]},
     {'branch': '깨뜨린 몸이 섞임', 'id': 'G-ELEVEN-MIXED', 'duration': 0.0, 'skippable': False,
      'steps': [st(0.0, '같은 장면. 깨뜨린 몸의 이름도 새겨지지만 그 줄에만 먹이 들지 않는다', control='walk', note='LAY 장면 안의 차이(별도 장면 아님)')]}]},
]

for _g in GROUPS:
    for _br in _g['branches']: promote(_br)

BOSSES = [
 day_boss('FUN-B21', 'B-21', 1, 'PoolBed', '마지막 손님 장례 — 빈 엽전 끈',
          'B-21을 눕힌 이튿날 낮, 윤 소사네에 처음 다가갈 때', [
     st(0.0, '아침의 솔고개. 윤 소사네 마당, 제사상 위 위패가 둘', cap=REGION[1]['cap'], sfx=REGION[1]['sfx'], req=REGION[1]['req'],
        cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 5.0}, control='none'),
     st(5.0, '제사상 곁에 엽전이 다 빠진 빈 엽전 끈 하나. 밤사이 나루에서 건져 온 것', cap='[정적]', cam={'mode': 'low_move', 'to': 'coin_string', 'time': 6.0}, control='none',
        note='깊은 박자 ①. 엽전 자국이 사라진 손바닥(B-21 눕힘)과 짝'),
     st(12.0, '윤 소사네 아들(N-103)이 끈을 두 손으로 들고 나선다. 마을 사람 몇이 뒤를 따른다. 요령 한 번', cap='[요령 한 번] [발소리]',
        sfx=['cut.yoryeong.ring'], cam={'mode': 'quarter', 'height': 'low'}, control='walk'),
     st(20.0, '물막이 골 나루 위 언덕. 아들이 끈을 묻는다. 위패 앞에 처음으로 무덤이 생긴다', cap='[흙 덮는 소리]', req=['cut.hoe.dig(호미로 흙 파는 소리)'],
        cam={'mode': 'low_move', 'to': 'grave'}, control='walk', note='깊은 박자 ②. 시즌 1 S-002 장례에서 위패가 둘이 된 집. 이번엔 무덤이 하나'),
     st(30.0, '저편 하류 쪽을 아들이 한 번 바라본다. 아무것도 보이지 않는다', cond='시즌 1 S-002(윤 소사) 천도함', control='walk',
        note='윤 소사가 저편 기슭에서 손을 흔든 것은 밤의 일(B-21 눕힘 컷). 산 사람은 모른다'),
     st(36.0, '사람들이 흩어진다', cap='[바람]', control='walk'),
     st(40.0, '페이드 없이 평소 낮 화면', control='restore')],
   '윤 소사네 제사상에 위패 둘 그대로. 무덤은 생기지 않는다. (윤 소사를 천도했다면 그는 저편이 아니라 줄 끝에서 계속 기다린다 — 밤 장면 몫)'),
 day_boss('FUN-B22', 'B-22', 5, 'SeaCave', '줄에 묶인 일곱 장례 — 밧줄 토막',
          'B-22를 눕히고 무리(S-200 · 201 · 202 포함 일곱)가 다 처결된 이튿날 낮, 망부석 곶에 처음 다가갈 때', [
     st(0.0, REGION[5]['place']['SeaCave'], cap=REGION[5]['cap'], sfx=REGION[5]['sfx'], cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 5.0}, control='none'),
     st(5.0, '곶 아래 모래에 밧줄 토막 일곱이 나란히 떠밀려 와 있다. 매듭이 그대로다', cap='[파도]', cam={'mode': 'low_move', 'to': 'ropes', 'time': 6.0}, control='none',
        note='깊은 박자 ①. 줄을 끊지 않고 이름을 불러 눕혔기 때문에 매듭이 풀리지 않은 채'),
     st(12.0, '그물 깁는 아낙들(N-501)과 포구 사람들이 모여 밧줄 토막을 하나씩 든다. 몸이 있는 장례처럼 다 나온다', cap='[발소리] [요령 한 번]',
        sfx=['cut.yoryeong.ring'], cam={'mode': 'quarter', 'height': 'low'}, control='walk'),
     st(20.0, '한 무덤에 일곱 토막을 함께 묻는다. 매듭은 풀지 않는다', cap='[흙 덮는 소리]', req=['cut.hoe.dig(호미로 흙 파는 소리)'],
        cam={'mode': 'low_move', 'to': 'grave'}, control='walk', note='깊은 박자 ②. "여섯이 같이 있었다"(S-200) — 같이 묻는다'),
     st(30.0, '망부석 곶 바위가 처음으로 포구 쪽을 향해 있다. 아무도 그것을 말하지 않는다', cam={'mode': 'tilt_up', 'to': 'mangbuseok', 'time': 2.0}, control='walk',
        note='season3_outline B-22 눕힘 문장. 바위가 움직이는 장면이 아니라 이미 향해 있는 것을 본다'),
     st(36.0, '사람들이 흩어진다', cap='[파도]', control='walk'),
     st(40.0, '페이드 없이 평소 낮 화면', control='restore')],
   '곶 아래 모래엔 아무것도 오지 않는다. 망부석 곶 바위는 여전히 바다를 향한다'),
 day_boss('FUN-B24', 'B-24', 3, 'TombPit', '한 구덩이의 두 진 장례 — 두 면의 비석',
          'B-24를 눕히고 큰 무덤 무리(S-217~227의 함께 묻기 백)가 다 처결된 이튿날 낮, 큰 무덤 앞에 처음 다가갈 때', [
     st(0.0, REGION[3]['place']['TombPit'], cap=REGION[3]['cap'], sfx=REGION[3]['sfx'], req=REGION[3]['req'],
        cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 5.0}, control='none'),
     st(5.0, '봉분 앞 땅에 깃대 둘이 X자로 누운 자국. 밤의 그 자리', cap='[정적]', cam={'mode': 'low_move', 'to': 'flag_marks', 'time': 6.0}, control='none'),
     st(12.0, '사당 노인(N-303)이 앞장서고 마을 사람들이 비석 하나를 세운다', cap='[돌 세우는 소리] [발소리]', req=['cut.stone.roll(큰 돌을 굴리는 둔한 소리)'],
        cam={'mode': 'quarter', 'height': 'low'}, control='walk'),
     st(20.0, '비석 앞면에 서른일곱. 석수가 뒤로 돌아가 뒷면에 건너편 이름들을 새긴다. 글씨가 다르다', cap='[정으로 돌 새기는 소리]',
        req=['cut.chisel.tap(정으로 돌 새기는 소리)'], cam={'mode': 'orbit', 'to': 'stone', 'time': 4.0}, control='walk',
        note='깊은 박자 ②. 카메라가 비석을 한 바퀴 돈다(앞 → 뒤). 글자는 읽히지 않게. 깨뜨린 백의 이름 줄에만 먹이 들지 않는다'),
     st(30.0, '술도가 손녀가 잔을 두 줄로 붓는다. 앞줄과 뒷줄', cap='[술 붓는 소리]', req=['cut.pour.liquor(잔에 술 붓는 소리)'],
        cam={'mode': 'low_move', 'to': 'cups'}, control='walk', note='시즌 1에서 서른일곱 잔이던 그 자리. 이제 두 줄'),
     st(36.0, '사람들이 흩어진다', cap='[바람]', control='walk'),
     st(40.0, '페이드 없이 평소 낮 화면', control='restore')],
   '비석 자리는 비어 있다. 술도가 손녀는 여전히 서른일곱 잔만 붓는다'),
 day_boss('FUN-B25', 'B-25', 4, 'SealedFace', '맨 마지막에 나가는 몸 장례 — 목패를 떼는 날',
          'B-25를 눕히고 막장 무리(S-229 · 230 · 236 · 238 · 239)가 다 처결된 이튿날 낮, 갱 입구 목패 걸이에 처음 다가갈 때', [
     st(0.0, REGION[4]['place']['FloodedShaft'], cap=REGION[4]['cap'], sfx=REGION[4]['sfx'], cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 5.0}, control='none'),
     st(5.0, '목패 걸이에 목패 열넷이 걸린 채다. 들어간 사람의 목패는 나와야 떼어진다', cap='[목패 흔들리는 소리]', req=['cut.tag.sway(나무 목패가 서로 부딪는 소리)'],
        cam={'mode': 'low_move', 'to': 'tag_board', 'time': 6.0}, control='none', note='깊은 박자 ①. 시즌 1부터 걸려 있던 그 열넷'),
     st(12.0, '광부들이 한 사람씩 목패를 걸이에서 뗀다. 하루가 끝났다는 뜻. 맨 마지막 목패는 반장 몫', cap='[목패 떼는 소리]',
        req=['cut.tag.unhook(목패를 고리에서 떼는 소리)'], cam={'mode': 'quarter', 'height': 'low'}, control='walk'),
     st(22.0, '광부 과부의 딸(N-407)이 그중 하나를 받는다. 아버지 것. 뒤집어 본다 — 뒷면에 이름', cam={'mode': 'close', 'to': 'tag_back', 'time': 1.5}, control='walk',
        note='깊은 박자 ②. 뒷면 이름은 읽히지 않게. S-239(과부의 남편)를 깨뜨렸다면 그 목패 뒷면에만 먹이 들지 않았다'),
     st(30.0, '열넷째 목패는 걸이에 하나 남아 있다가, 마지막에 반장 몫과 함께 떼어진다', cond='S-209(열넷) 눕힘', control='walk',
        note='B25-D4 · "열넷"이 갱 물을 타고 간 몸(F60)'),
     st(34.0, '빈 걸이. 광부들이 갱 입구에 등을 돌리고 마을로 내려간다', cap='[발소리 멀어진다]', control='walk'),
     st(40.0, '페이드 없이 평소 낮 화면', control='restore')],
   '목패 열넷은 걸이에 그대로 걸려 있다'),
 day_boss('FUN-B26', 'B-26', 2, 'LimePit', '두 겹 구덩이 장례 — 다시 나붙은 명단',
          'B-26을 눕힌 이튿날 낮, 검은여울 동헌 앞 또는 무덤골에 처음 다가갈 때', [
     st(0.0, '아침의 검은여울 동헌 앞. 벽에 새 방이 나붙어 있다. 사람들이 모여 있다', cap='[웅성거림]', sfx=['amb.market'],
        cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 5.0}, control='none'),
     st(5.0, '진짜 명단. 노경수 어른 손주(N-205)가 손가락으로 한 줄의 글씨를 짚는다. 할아버지 글씨', cam={'mode': 'close', 'to': 'notice', 'time': 1.5}, control='none',
        note='깊은 박자 ①. 글자는 읽히지 않게. 짚는 손가락만'),
     st(12.0, '무덤골. 묘지기가 빈 돌들 앞에서 이름을 새기기 시작한다. 위 겹 돌 줄, 그리고 아래 겹 돌 줄', cap='[정으로 돌 새기는 소리]',
        req=['cut.chisel.tap(정으로 돌 새기는 소리)'], cam={'mode': 'quarter', 'height': 'low'}, control='walk',
        note='돌 마흔과 마흔. 이미 개별로 새겨진 돌(②의 이름 새기기 장례)은 그대로 두고 나머지를 새긴다'),
     st(22.0, '도성 움막촌 사람들이 성묘를 온다. 사십 년 전 검은여울에서 도망친 사람들의 후손. 돌 앞에 짚신 · 떡 한 조각', cap='[발소리]',
        cam={'mode': 'side_track', 'to': 'visitors'}, control='walk', note='깊은 박자 ②. ②와 ⑥이 서로를 채운다(regions.2.special)'),
     st(34.0, '묘지기가 정을 거둔다. 돌 줄 끝까지 이름이 찼다', cam={'mode': 'pull_out', 'to': 'stones'}, control='walk'),
     st(40.0, '페이드 없이 평소 낮 화면', control='restore')],
   '돌 마흔은 비어 있다. 동헌 앞에 새 방은 없다'),
]
BOSS_POINTERS = [
 {'id': 'FUN-B23', 'boss': 'B-23', 'branches': [], 'see': 'C-23A / C-23B', 'note': '장례 없음. 풀기 = 첫 배가 닿는 C-23A, 끊기 = C-23B. ⑦엔 산 사람이 없다'},
 {'id': 'FUN-B27', 'boss': 'B-27', 'branches': [], 'see': 'C-27A / C-27B', 'note': '이튿날 낮 팻말(아들 문지기 · 서적상 노인 가게의 새 붓)은 C-27A 7막 엔딩 안에 있다. 따로 만들지 않는다'},
 {'id': 'FUN-B31', 'boss': 'B-31', 'branches': [], 'see': 'C-31A / C-31B / C-31C', 'note': '결말 컷이 장례다. 대사는 endings_s1 정본(line_ref)'},
]


def dawn_boss(fid, boss, r, zone, name, trig, place, act1, act2, brk, n1=None, n2=None):
    steps = [st(0.0, REGION[r]['place'][zone], cap=REGION[r]['cap'], sfx=REGION[r]['sfx'] or None, req=REGION[r]['req'] or None,
                cam={'mode': 'quarter', 'then': 'slow_zoom_in', 'time': 4.0}, control='none'),
             st(4.0, place, cap='[정적]', cam={'mode': 'low_move', 'to': 'stopped_thing', 'time': 6.0}, control='none', note=n1),
             st(12.0, act1, cam={'mode': 'quarter', 'height': 'low'}, control='walk'),
             st(20.0, act2, cam={'mode': 'pull_out', 'time': 2.0}, control='walk', note=n2),
             st(28.0, '첫 빛이 조금 더 든다', cap='[새벽 바람]', control='walk'),
             st(30.0, '조작 복귀', control='restore')]
    return day_boss(fid, boss, r, zone, name, trig, steps, brk, dur=30.0,
                    extra={'note': NINE_NO_DAWN} if r == 9 else None)


BOSSES += [
 dawn_boss('FUN-B28', 'B-28', 8, 'InkSilt', '벼루 밑의 손 — 먹방이 쉬는 새벽', 'B-28을 눕힌 다음 새벽 틈, 먹방에 처음 다가갈 때',
           '벼루지기 자리가 비어 있다. 그 벼루 위 먹이 처음으로 말라 있다',
           '먹방 일꾼들(N-802)이 하나둘 손을 놓는다. 갈던 먹을 벼루에 눕혀 둔다. 서로 보지 않는다',
           '먹방 전체가 잠깐 멈춘다. 먹 가는 소리가 처음으로 끊긴다. 그다음 몇 사람은 다시 갈고, 몇 사람은 줄 쪽으로 나간다',
           '벼루지기는 계속 먹을 간다. 손은 반 줄에서 영영 멈춘 채(밤의 일). 먹방은 쉬지 않는다',
           n1='깊은 박자 ①. 벼루지기의 혼은 이미 줄에 섰다(B-28 눕힘 컷)', n2='깊은 박자 ②. 먹 가는 소리가 끊기는 1초가 핵심 — 사운드팀 확인'),
 dawn_boss('FUN-B29', 'B-29', 9, 'Ondol', '백 년의 사잣밥 — 치워진 밥상', 'B-29를 눕힌 다음 새벽 틈, 빈 고을 고샅에 처음 다가갈 때',
           '집집 문간에 늘 차려 있던 밥상이 처음으로 치워져 있다. 상 자리만 마루가 조금 밝다',
           '차사가 고샅을 지나는 동안 문간마다 같은 빈자리. 백 년 만에 아무도 밥을 짓지 않는다',
           '고샅 끝 할미 집 문간. 빈 상 위에 짚신 한 켤레만 놓여 있다 — 차사가 신은 것과 같은 결',
           '무너진 방에서 밥 짓는 연기가 계속 오른다 — 아무도 없는데',
           n1='깊은 박자 ①. F69', n2='깊은 박자 ②. D3(백한 켤레째)을 찾았다면 이 짚신은 없다 — 이미 차사 발에 있다'),
 dawn_boss('FUN-B30', 'B-30', 10, 'WellBottom', '첫 우물 — 노를 다시 집는 새벽', 'B-30을 눕힌 다음 새벽 틈, ⑦ 나루 또는 첫 우물에 처음 다가갈 때',
           '첫 우물 턱에 새끼줄이 없다. 우물 물이 잔잔하다',
           '삼도천 나루. 사공이 노를 다시 집는다. 이번엔 입술이 움직이지 않는다',
           '배가 줄 쪽으로 나아간다. 차사는 나루에 서서 본다',
           '사공은 계속 소리 없이 부르며 노를 젓는다. 첫 차사의 백은 우물가에 앉은 채',
           n1='깊은 박자 ①. 명부 첫 줄의 번진 먹은 이름이 되지 않았지만 더 번지지 않는다(B-30 눕힘 컷)',
           n2='깊은 박자 ②. 사공의 이름 · 얼굴 클로즈업 금지. 입술이 움직이지 않는 것만'),
]

# FUN-B28 소리(사운드 PR #36 7534a05): 첫 박자는 먹방 반복음, 20초 박자에 "먹 가는 소리가 1초 끊김" 전용 소리.
# 반복음을 끄는 때와 음악을 0으로 내리는 일은 사운드의 data/funeral_audio_s3.json에 있다
for _b in BOSSES:
    if _b['id'] == 'FUN-B28':
        _st = _b['branches'][0]['steps']
        _st[0]['sfx'] = ['cut.ink.grind.room']
        _s20 = [x for x in _st if x['t'] == 20.0][0]
        _s20['sfx'] = _s20.get('sfx', []) + ['cut.ink.grind.stop']


# ───────────────── 만들기 · 자체 검사 ─────────────────
mem = json.load(open(MEM, encoding='utf-8'))
baek = mem['baek']
rows = [build_baek(b) for b in baek]

# 검사 1: 장례 종류별 재료가 빠짐없이 있다
for b in baek:
    k, r = b['funeral'], b['region']
    if k == 'reverse' and r in (1, 5): assert b['id'] in REVERSE, b['id']
    if k == 'reverse' and r >= 8: assert b['id'] in DAWN, b['id']
    if k == 'carve' and b['id'] != 'S-263': assert b['id'] in CARVE, b['id']
    if k == 'group': assert b['id'] in GROUP_OF, b['id']

data = {
    '_설명': '시즌 3 장례 대본 — 백을 눕힌 이튿날(①~⑥ 낮 / ⑦~⑩ 새벽 틈). tools/funerals_s3.py로 생성. 손으로 고치지 말 것. 서사 2026-10-26',
    'rules': {
        'kinds': {'reverse': '①⑤ 거꾸로 장례가 앞으로 다시 재생 — 물이 돌려준 물건을 묻는다(F53). 36초',
                  'carve': '②③④⑥ 산 사람이 빈 돌 · 목패 · 팻말에 이름을 새긴다(F57). 36초. 이름을 모르면 반쪽 — 차사가 사슬 끝으로 한 줄(F51), 14초',
                  'dawn': '⑧⑨⑩ 산 사람이 없다 → 새벽 틈에 그 혼이 일을 놓고 줄에 선다(⑧⑨, F65) / 사슬이 쓰러진다(⑩, F68). 20초',
                  'group': '무리가 다 처결된 이튿날 한 번에(G-ELEVEN · 보스 장례 B-22 · B-24 · B-25)',
                  'none': '⑦ = THREAD-RISE가 곧 장례 / ⑤ 일부 = 바다가 아무것도 돌려주지 않음 / S-191 = 이름 아는 사람 없음'},
        'dialogue': '대사 · 자막 · 내레이션 0. 이름 부름은 입 모양만. 산 사람은 차사를 보지 못한다',
        'per_day': '(기획 확인 요청) 한 관할에서 하룻밤에 여럿을 눕혔으면, 이튿날 처음 다가간 한 곳만 전체 장면(36초 / 20초), 나머지는 10초 판(-SHORT, 깊은 박자 ②만). 시즌 1의 "하루 한 장례"는 백 120에선 너무 느려서',
        'missed': '그날 그 자리에 가지 않으면 장면은 지나간다. 다음 날부터 끝난 상태(무덤 · 새긴 이름 · 쓰러진 사슬)만 남는다',
        'break': '깨뜨린 백은 장례 없음(0초). 빈 것이 그대로 남는다. 무리 장례에선 이름은 새겨지되 그 줄에만 먹이 들지 않는다',
        'step_aside': '비켜선 백(STEP-ASIDE)도 눕힌 것으로 친다 — 같은 장례',
        'karma': '업 10 이상이면 산 사람의 개가 차사 쪽을 보고 짖는다(시즌 1과 같음). 장면은 그대로',
        'sfx': 'sfx = 있는 소리, sfx_request = 요청(사운드팀), caption = 소리 자막(청각 보조 설정에서만)',
        'never': '찬 기운 말 · 주인공 이름 · 그 의례 이름 없음. 먹지기 얼굴 · 이름, 어미 이름, 사공 이름 없음. S-185 열두째 빈자리 · S-188의 뜻은 8막 전 설명 금지',
    },
    'baek_funerals': rows,
    'group_funerals': GROUPS,
    'boss_funerals': BOSSES + BOSS_POINTERS,
}

# 검사 2: 금지어 · 대사 0 · 시간 범위
txt = json.dumps(data, ensure_ascii=False)
for w in ('초혼', '동이', '춥', '추워', '추위', '한기', '으슬', '차누', '시왕', '염라', '재판', '형벌', '李明', '이명'):
    assert w not in txt, w
assert "'line'" not in txt and '"line"' not in txt


def _check(cut):
    for br in cut.get('branches', []):
        for s in br['steps']:
            assert 0 <= s['t'] <= max(br['duration'], 0.0) or br['duration'] == 0.0, (cut['id'], br['id'] if 'id' in br else br['branch'], s['t'])


for c in rows + GROUPS + BOSSES:
    _check(c)
ids = [c['id'] for c in rows + GROUPS + BOSSES + BOSS_POINTERS]
assert len(ids) == len(set(ids)), 'id 중복'

if __name__ == '__main__':  # reverse_clues_s3.py가 이 파일의 재료(CARVE 등)를 가져다 쓴다. 가져갈 때는 파일을 쓰지 않는다
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    cnt = {}
    for r in rows:
        cnt[r['kind']] = cnt.get(r['kind'], 0) + 1
    print(len(rows), 'baek rows', cnt, '| groups', len(GROUPS), '| boss', len(BOSSES), '+ pointers', len(BOSS_POINTERS))
    req = sorted({x.split('(')[0] for c in rows + GROUPS + BOSSES for br in c.get('branches', []) for s in br['steps'] for x in s.get('sfx_request', [])})
    print('sound requests:', len(req), req)
