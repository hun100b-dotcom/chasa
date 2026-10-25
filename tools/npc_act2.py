# -*- coding: utf-8 -*-
# 2막(③ 붉은재 싸움터 · ④ 쇳골 광산) 산 사람 초안 생성기.
# 왜 따로 두나: 1막(npc_act1.json)은 시간표·단서까지 확정됐지만, 2막은 아직 지도가 없다.
# 그래서 지금은 "누가 사는가 + 지나가며 들리는 혼잣말(barks)"만 먼저 정하고,
# 시간표(schedule)·자리 좌표·단서 대사(line)는 2막 지도가 나오면 1막과 같은 모양으로 채운다.
# 실행: python3 tools/npc_act2.py  → docs/narrative/npc_act2.json
import json, os

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'narrative', 'npc_act2.json')

# barks 규칙(1막과 같음, 기획 npc-interaction-spec §1):
#  - 시간대마다 0~3줄, 12자 안팎. 산 사람의 혼잣말이고 단서가 아니다(기록하지 않음).
#  - 보스 단서와 겹치는 말 금지: 서른일곱·술 붓기·깃발 아저씨·"일곱"·장군 위패(③),
#    목패 七·열셋/열넷·반장·장부 앞장/뒷장·머릿수 보상(④).
#  - 추위 말 금지(지나가는 순간 한기는 당할미만, 다른 사람은 업이 높을 때만 — 코드가 따로 처리).
#  - 땅의 상처(사람을 번호로 부르는 광산)는 "공공연한 풍경"이라 한 줄 정도는 들려도 된다.
#    다만 보스의 숫자(13·14·7)는 피한다.
#  - 이름은 짓지 않고 역할로 부른다(소설 전용 이름과 겹치지 않게).
NPCS = [
 # ───── ③ 붉은재 싸움터 · 산성 아랫마을 ─────
 {"id":"N-301","name":"술도가 손녀","region":3,"zone":"Fortress","link_soul":"S-049",
  "role":"술도가 노인(S-049)의 손녀. 할아버지 장례 뒤 술도가를 잇는다",
  "barks":{"낮":["누룩 뒤집을 때네.","독이 또 샜나 봐."],"저녁":["불 줄여야지."]}},
 {"id":"N-302","name":"산성 마을 아이들","region":3,"zone":"Fortress","link_soul":None,
  "role":"산성 아랫마을 아이들. 놀이 노래는 보스 단서(B-05 엿듣기)라 barks에 넣지 않는다",
  "barks":{"낮":["성돌에 올라가지 마!","내가 먼저 봤어!","화살촉 주웠다!"],"저녁":["밥 먹으러 가자."]}},
 {"id":"N-303","name":"사당 노인","region":3,"zone":"Fortress","link_soul":None,
  "role":"마을 사당을 돌보는 노인. 아버지 이야기는 보스 단서(B-06 엿듣기) 대사로만",
  "barks":{"낮":["무릎이 쑤시는구먼.","에구, 거미줄 봐라."],"저녁":["사당 문 걸어야지."]}},
 {"id":"N-304","name":"약초 캐는 이웃","region":3,"zone":"ArrowValley","link_soul":"S-050",
  "role":"약초 아낙(S-050)의 이웃. 장례 뒤 그 바위틈에 약초를 캐러 간다",
  "barks":{"낮":["여기 삽주가 있네.","바위가 미끄럽구먼."]}},
 {"id":"N-305","name":"석수 제자","region":3,"zone":"Fortress","link_soul":"S-051",
  "role":"석수(S-051)의 제자. 반쯤 쌓다 만 성벽을 잇는다",
  "barks":{"낮":["정이 또 무뎌졌네.","돌결을 봐야 해."],"저녁":["오늘은 여기까지."]}},
 {"id":"N-306","name":"벌초꾼 아들","region":3,"zone":"BigTomb","link_soul":"S-052",
  "role":"벌초꾼(S-052)의 아들. 큰 무덤 풀을 벤다",
  "barks":{"낮":["풀이 금세 자라네.","낫 갈아 와야겠다."]}},
 # ───── ④ 쇳골 광산 ─────
 {"id":"N-401","name":"선탄장 아낙들","region":4,"zone":"Sorting","link_soul":None,
  "role":"석탄을 고르는 아낙들. 반장 이야기는 보스 단서(B-07 엿듣기) 대사로만",
  "barks":{"낮":["손톱이 또 새까맣네.","돌 섞였다, 골라내.","허리 좀 펴자."],"저녁":["손이나 씻고 가."]}},
 {"id":"N-402","name":"선탄장 아낙의 딸","region":4,"zone":"Sorting","link_soul":"S-068",
  "role":"선탄장 아낙(S-068)의 딸. 장례 뒤 어머니 자리에 앉는다",
  "barks":{"낮":["이건 버리는 거고…","엄마는 빨랐는데."]}},
 {"id":"N-403","name":"광부 과부","region":4,"zone":"MinerTown","link_soul":None,
  "role":"남편을 갱에서 잃은 과부. 보상 이야기는 보스 단서(B-08 엿듣기) 대사로만",
  "barks":{"낮":["빨래가 금세 까매져.","물 길어야지."],"저녁":["애들 불러들여야지."]}},
 {"id":"N-404","name":"교대 광부들","region":4,"zone":"MinerTown","link_soul":None,
  "role":"갱에 드나드는 광부들. 동료가 순돌(S-067)의 목패를 떼어 가족에게 건넨다",
  "barks":{"낮":["등잔 기름 챙겼나?","삼십 번, 늦었다!","허리 숙여, 천장 낮다."],"저녁":["오늘도 나왔구먼."],"밤":["갱 바람 소리 봐라."]}},
 {"id":"N-405","name":"국밥집 아들","region":4,"zone":"MinerTown","link_soul":"S-069",
  "role":"국밥집 주인(S-069)의 아들. 외상 장부 번호 옆에 이름을 적어 넣는다",
  "barks":{"낮":["국밥 두 그릇이오!","뚝배기 뜨거워요."],"저녁":["솥 씻어야지."]}},
 {"id":"N-406","name":"광산 주인","region":4,"zone":"MinerTown","link_soul":None,
  "role":"광산 주인. 주인집은 광부촌 위. 장부를 넘기는 모습은 보스 단서(B-08 지켜보기)라 barks와 섞지 않는다",
  "barks":{"낮":["캐낸 게 이것뿐이야?","일 안 하나!"]}},
]

# ───── 시간표(schedule): 기획 2막 지도(act2_map.json의 npc_schedules)의 자리 이름을 그대로 쓴다(10-25) ─────
# 왜 지도 파일을 읽나: 자리·좌표는 기획 몫이고 말·동사·단서는 서사 몫이다. 같은 내용을 두 번 적으면 어긋나므로
# 자리는 지도에서 가져오고, 단서 대사(line/line_half)는 boss_clues_act2.json에서 가져와 붙인다.
import re
MAP = '/mnt/project-files/planning/openworld/act2/act2_map.json'
BC = os.path.join(os.path.dirname(OUT), 'boss_clues_act2.json')
if os.path.exists(MAP) and os.path.exists(BC):
    amap = json.load(open(MAP, encoding='utf-8'))
    clues = {c['id']: c for b in json.load(open(BC, encoding='utf-8'))['boss_clues'].values() for c in b['clues']}
    places = amap['places']
    for n in NPCS:
        key = next((k for k in amap['npc_schedules'] if k.split(' ')[0] == n['id']), None)
        if not key:
            continue
        sched = []
        for t, rows in amap['npc_schedules'][key].items():
            for r in rows:
                e = {'time': t, 'zone': places.get(r['place'], {}).get('zone', n['zone']), 'place': r['place'],
                     'verb': r.get('verb'), 'clue': r.get('clue')}
                m = re.search(r'낮 (\d+)~(\d+)분', r.get('memo') or '')
                if m:  # 낮을 둘로 나눈 사람(사당 노인·교대 광부): 그 동작을 하는 분 범위
                    e['window_min'] = [int(m.group(1)), int(m.group(2))]
                c = clues.get(r.get('clue'))
                if c and c.get('line'):
                    e['line'], e['line_half'] = c['line'], c['line_half']
                if r.get('memo'):
                    e['note'] = r['memo']
                sched.append(e)
        n['schedule'] = sched
        times = {e['time'] for e in sched}
        n['barks'] = {t: v for t, v in n['barks'].items() if t in times}  # 서 있지 않는 시간대의 말은 뺀다
        n['unlock'] = '2막 금줄이 풀린 뒤(1막 무덤골 흑월 1차 목격 다음 새벽)'

data = {
 "_설명": "2막 산 사람(서사 10-25). schedule의 자리 이름·시간대는 기획 2막 지도(planning/openworld/act2/act2_map.json)와 같고, 좌표는 그 파일의 places에서 찾는다. 단서 대사는 boss_clues_act2.json과 같다. barks 형식과 뜻은 npc_act1.json과 같다. 장례에만 나오는 사람(광부의 며느리 등)은 funerals_act2.json에만 있다.",
 "_version": 1,
 "zones": {"Fortress":"무너진 산성(아랫마을)","ArrowValley":"화살골","Camp":"군막 터","BigTomb":"큰 무덤",
           "MinerTown":"광부촌","Sorting":"선탄장","MainShaft":"큰 갱도","Collapse":"무너진 막장"},
 "rules": {
  "barks": "시간대마다 0~3줄, 12자 안팎. 단서 아님, 기록 안 함. 보스 단서·F 단서·추위 말 금지",
  "speaker": "모든 말은 산 사람의 혼잣말이거나 산 사람끼리 하는 말이다. 차사에게 하지 않는다(당할미는 ①에만 있다)",
  "names": "2막 산 사람은 이름 없이 역할로 부른다"},
 "npcs": NPCS,
}
json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(NPCS), 'npcs')
