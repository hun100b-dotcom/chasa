#!/usr/bin/env python3
"""
soul_labels_s1.py — 시즌 1 이름혼의 '머리 위 이름표'와 파혼 뒤 기록 칸 글을 정한다(서사 2026-10-26).

왜 따로 두나: 기억 표(memories_act1~3.json)의 name 은 서사가 혼을 부르는 이름이라, 몇은 천도하기 전에
보이면 단서를 미리 새게 한다("검은 갓의 옛 혼" → F29, "둑에서 건져진 사내" → F28). 게임은 이름(name)으로
기억을 찾으므로 name 은 그대로 두고, 화면에 띄우는 이름표(label)만 따로 준다.

사용: python3 tools/soul_labels_s1.py → docs/narrative/soul_labels_s1.json
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 이름표를 바꾸는 혼: (새 이름표, 까닭). 나머지는 name 그대로
OVERRIDE = {
    'S-012': ('무명 혼', "'사슬'이 F7(이름 잃은 혼이 사슬을 받는다)을 미리 말함"),
    'S-028': ('정혼한 처녀', "'서생'이 F11(흑월은 서생이었다)을 미리 말함"),
    'S-066': ('산성의 목소리', "8자로 길고, '서른일곱'은 보스 숫자라 단서 물건·대사에만 쓴다"),
    'S-098': ('썰물의 혼', "'물 밑'이 F30(물 밑에 누운 것은 우리 몸)을 미리 말함"),
    'S-102': ('남의 이름표', "'검은 갓'이 F29(사슬 받은 차사가 나 하나가 아니다)를 미리 말함. 기억의 '이름표엔 남의 글씨'에서 땀"),
    'S-118': ('다리 밑 거지', "'차사'가 F29를 미리 말함"),
    'S-120': ('건져진 사내', "8자로 길고 '둑'이 F28·F9 곁 낱말(그의 감각에 둑을 두지 않는 규율)"),
}
RULES = {
    'label': '머리 위 이름표 = label. 혼이 처음 보일 때부터 뜬다. 무적 혼은 별명을 듣기 전엔 이름표 대신 「별명 모름」(field_nicknames_act3 rule.show), 들은 뒤 별명. 별명이 없는 무적 혼(nickname null)은 B-11 천도 뒤 label',
    'name': '기억을 찾는 열쇠(MemoryLines는 이름으로 찾는다). 천도한 뒤 기록(C) 칸 제목은 name — 기억을 본 뒤에야 서사 이름이 드러난다',
    'tendo': '천도 뒤 남는 한 줄 = memories의 memory(+ 제사 지켜봤으면 jesa_extra). 모두 있음',
    'pahon': '파혼 뒤: 그 자리엔 아무것도 남지 않는다(장례 대상만 대문 조등). 기록(C)의 그 칸은 label 아래 「먹이 번져 읽을 수 없다」 한 줄(ink_originals smudged와 같은 글). 기억 조각·단서 없음',
    'length': '이름표는 공백 빼고 7자 이하(맺힘 막대 80 px 위)',
}
out_souls = []
for a in (1, 2, 3):
    for s in json.load(open(os.path.join(ROOT, 'docs', 'narrative', 'memories_act%d.json' % a), encoding='utf-8'))['souls']:
        if s.get('boss'):
            continue
        lab, why = OVERRIDE.get(s['id'], (s['name'], None))
        assert len(lab.replace(' ', '')) <= 7, (s['id'], lab)
        row = {'id': s['id'], 'name': s['name'], 'label': lab}
        if why: row['why'] = why
        if s.get('mujeok'): row['mujeok'] = True; row['nickname'] = s.get('nickname')
        out_souls.append(row)
json.dump({'_설명': '시즌 1 이름혼 이름표(label)와 파혼 뒤 기록 칸 규칙. tools/soul_labels_s1.py로 생성. 서사 2026-10-26',
           'rules': RULES, 'souls': out_souls},
          open(os.path.join(ROOT, 'docs', 'narrative', 'soul_labels_s1.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out_souls), 'souls,', sum(1 for r in out_souls if r['label'] != r['name']), 'relabeled')
