# 컷신 스텝에 효과음 이름표(사운드팀 data/sfx_files.json의 id)를 붙이는 표.
# 왜 따로 두나: 대본 생성기 넷(B01·B02·B03·첫 세션)이 같은 규칙으로 붙이게 하려고.
# 키 = (컷 id, 스텝 시각 t). 값 = (있는 소리 id 목록, 아직 없는 소리 요청 목록)
SFX = {
 # B-01 나루 영감
 ('B01-INTRO', 0.0): (['amb.river.mist'], []),
 ('B01-INTRO', 1.2): (['cut.water.pole'], []),
 ('B01-INTRO', 3.0): (['cut.water.hands'], []),
 ('B01-KNEEL', 0.0): (['sfx.kneel', 'cut.water.drop'], []),
 ('B01-NOCLUE', 0.0): (['cut.seal.fade'], []),
 ('B01-TENDO', 0.0): (['cut.ledger.open', 'cut.brush.stroke', 'cut.seal.set'], []),
 ('B01-TENDO', 1.0): (['sfx.clue'], []),
 ('B01-TENDO', 1.5): (['cut.coins.few'], []),
 ('B01-TENDO', 5.5): (['cut.lantern.light'], []),
 ('B01-PAHON', 0.0): (['sfx.pahon.burst', 'cut.boat.break'], []),
 ('B01-PAHON', 0.3): (['cut.stroke.scatter'], []),
 ('B01-PAHON', 0.8): (['cut.coins.spill'], []),
 # B-02 월화
 ('B02-INTRO', 2.0): (['cut.yoryeong.ring'], []),
 ('B02-KNEEL', 0.0): (['sfx.kneel', 'cut.bell.roll'], []),
 ('B02-NOCLUE', 0.0): (['cut.seal.fade'], []),
 ('B02-TENDO', 0.0): (['cut.ledger.open', 'cut.brush.stroke', 'cut.seal.set'], []),
 ('B02-TENDO', 1.0): (['sfx.clue'], []),
 ('B02-TENDO', 1.5): (['cut.cups.set'], []),
 ('B02-TENDO', 4.5): (['cut.cloth.flutter', 'cut.dissolve'], []),
 ('B02-TENDO', 6.0): (['cut.lantern.light'], []),
 ('B02-PAHON', 0.0): (['sfx.pahon.burst', 'cut.cups.topple'], []),
 ('B02-PAHON', 0.3): (['cut.stroke.scatter'], []),
 ('B02-PAHON', 0.8): (['cut.cloth.flutter', 'cut.bell.roll'], []),
 # B-03 서 의원
 ('B03-INTRO', 2.0): (['cut.drawer'], ['cut.cough(마른기침)']),
 ('B03-INTRO', 2.6): (['cut.floor.flash'], []),
 ('B03-KNEEL', 0.0): (['sfx.kneel'], []),
 ('B03-NOCLUE', 0.0): (['cut.seal.fade'], []),
 ('B03-TENDO', 0.0): (['cut.ledger.open', 'cut.seal.set'], []),
 ('B03-TENDO', 1.0): (['sfx.clue'], []),
 ('B03-TENDO', 1.5): (['cut.drawer'], []),
 ('B03-TENDO', 3.5): (['cut.ledger.open'], []),
 ('B03-TENDO', 5.0): (['cut.dissolve'], []),
 ('B03-TENDO', 6.5): (['cut.lantern.light'], []),
 ('B03-PAHON', 0.0): (['sfx.pahon.burst', 'cut.boat.break'], []),
 ('B03-PAHON', 0.3): (['cut.stroke.scatter'], []),
 ('B03-PAHON', 0.8): (['cut.bottles.roll'], []),
 # 오프닝 C-01
 ('C-01', 0.0): (['amb.river.mist'], []),
 ('C-01', 3.0): ([], ['amb.rain(빗소리)']),
 ('C-01', 10.0): ([], ['cut.torch.sink(횃불이 물에 잠김: 치익 + 꼬르륵)']),
 ('C-01', 13.0): (['amb.river.mist'], []),
 ('C-01', 15.0): ([], ['cut.chain.wrap(쇠사슬이 손목에 감김)']),
 ('C-01', 19.0): (['amb.field'], []),
 # 박돌쇠 장례
 ('FUN-S001-TENDO', 0.0): (['amb.field'], ['amb.rooster(먼 닭울음)']),
 ('FUN-S001-TENDO', 6.0): (['cut.yoryeong.ring'], []),
 ('FUN-S001-TENDO', 14.0): (['cut.yoryeong.ring'], ['vo.wail(곡소리, 말 없음)', 'mus.sangyeo.far(가사가 안 들리는 먼 상여소리)']),
 ('FUN-S001-TENDO', 26.0): ([], ['vo.wail(곡소리, 커졌다 잦아듦)']),
 ('FUN-S001-TENDO', 40.0): ([], ['mus.sangyeo.far(멀어짐)']),
 ('FUN-S001-TENDO', 52.0): ([], ['cut.bellows(풀무 + 불꽃 튐)']),
 ('FUN-S001-TENDO', 62.0): (['amb.field', 'cut.yoryeong.ring'], []),
 ('FUN-S001-PENDING', 0.0): (['amb.field'], []),
 ('FUN-S001-PENDING', 12.0): ([], ['sfx.dog.whine(개 낑낑)']),
}

def apply(cut):
    """컷 하나의 steps에 sfx(있는 소리)와 sfx_request(사운드팀에 요청할 소리)를 붙인다."""
    for s in cut.get('steps', []):
        have, need = SFX.get((cut['id'], s['t']), ([], []))
        if 'sfx' in s and isinstance(s['sfx'], str):
            s['caption'] = s.pop('sfx')   # 예전 소리 자막 글은 caption으로 옮긴다
        if have: s['sfx'] = have
        if need: s['sfx_request'] = need
    return cut
