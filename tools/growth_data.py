# -*- coding: utf-8 -*-
"""
growth_data.py — 차사 성장 시스템(무기·도술·장비·넋/인) 데이터의 '원본'.

왜 이 파일이 있나?
  기획서(사람이 읽는 문서)와 코드팀·아트팀이 쓰는 데이터 표(JSON)가 서로 어긋나면
  "문서엔 12초, 게임엔 10초" 같은 사고가 난다. 그래서 숫자는 여기 한 곳에만 적고,
  이 스크립트를 돌려서 JSON(data/growth.json)과 기획서용 표(마크다운)를 함께 뽑는다.

쓰는 법 (터미널):
  python3 tools/growth_data.py            # data/growth.json 과 planning/growth/appendix.md 를 새로 만든다

주의:
  - 모든 숫자는 '임시값'이다. QA 시뮬로 확정되면 LOCKED-DECISIONS 를 먼저 고치고 여기를 따라 고친다.
  - 기억 조각을 늘리는 효과는 어떤 항목에도 넣지 않는다(기둥 2: 기억은 이야기다).
  - 천도 캐스팅은 무슨 보정을 받아도 0.5초(CAST_MIN_TIME)보다 짧아지지 않는다.
"""
import json
import os
import sys

VERSION = "growth-v1 (2026-10-24, 임시값, 오너 확인 전)"

# ---------------------------------------------------------------------------
# 1. 도술 27개 (갈래 3 × 9)
#    kind: active(액티브, 칸에 끼워 쓰는 기술) / passive(패시브, 늘 켜져 있는 효과) / deep(깊은 도술, 갈래에 10점 넣어야 열림)
#    max_rank: 최대 단계. 단계마다 도술 점수 1점이 든다.
#    cd: 재사용 대기시간(초) = base + per_rank × (단계-1)
#    values: 단계 1 값과 단계당 변화량. 표 만들 때 '1단계 → 최대단계' 로 보여 준다.
# ---------------------------------------------------------------------------
SCHOOLS = {
    "burum": {"name": "부름", "lean": "천도", "color": "#5FE3C0", "desc": "이름을 불러 보내는 힘. 천도를 돕는다"},
    "jul":   {"name": "줄",   "lean": "중립", "color": "#D4A94E", "desc": "사슬과 매듭으로 묶는 힘. 싸움과 제어"},
    "eolruk": {"name": "얼룩", "lean": "파혼", "color": "#E85C41", "desc": "원념을 다루는 힘. 쓸수록 흑월을 닮아 간다"},
}

def V(base, per_rank=0.0, unit=""):
    """단계별 값 하나. base = 1단계 값, per_rank = 단계가 오를 때마다 더하는 값."""
    return {"base": base, "per_rank": per_rank, "unit": unit}

SKILLS = [
    # ---------------- 부름 갈래 (천도 쪽) ----------------
    dict(id="burum_hold", name="붙잡아 부르기", school="burum", kind="active", max_rank=5,
         cd=V(12, -0.5, "초"), use_cost="없음",
         values={"radius": V(6, 0, "m"), "wait_bonus": V(3, 0.25, "초"), "enemy_stagger": V(0.8, 0, "초")},
         effect="반경 6m 안 무릎 꿇은 혼의 처결 대기 시간을 늘리고, 서 있는 적을 잠깐 멈칫하게 한다. 같은 혼에는 한 번만 걸린다",
         tendo="고민할 시간을 사 준다. 천도할 혼을 고를 여유가 생긴다",
         pahon="늘린 시간 안에 파혼해도 된다. 선택지를 늘릴 뿐 방향을 정하지 않는다",
         demo=True),
    dict(id="burum_wisp", name="혼불 날리기", school="burum", kind="active", max_rank=5,
         cd=V(5, -0.25, "초"), use_cost="혼불 1개(던지면 4초 뒤 돌아옴)",
         values={"damage": V(12, 2, "맺힘"), "wisp_max": V(3, 0.5, "개")},
         effect="따르는 혼불을 던져 맺힘 피해. 혼불 수 = 그날 밤 천도한 혼 수(최대 3→5)",
         tendo="천도할수록 강해지는 공격. 천도가 곧 화력이 된다",
         pahon="파혼하면 혼불 하나가 놀라 3초 동안 흩어진다(못 던짐)",
         demo=False),
    dict(id="burum_namelight", name="이름 비추기", school="burum", kind="active", max_rank=5,
         cd=V(8, -0.5, "초"), use_cost="없음",
         values={"cast_cut": V(0.4, 0.05, "초"), "duration": V(10, 0, "초")},
         effect="혼 하나(서 있는 적도 됨)의 이름을 미리 비춘다. 10초 안에 그 혼을 천도하면 캐스팅이 짧아진다(하한 0.5초)",
         tendo="오래된 혼(대기 4초)도 안전하게 보낼 수 있다",
         pahon="비춘 혼을 파혼하면 효과가 사라지고, 명부의 그 이름이 흐려지는 연출이 나온다(수치 변화 없음)",
         demo=False),
    dict(id="burum_path", name="배웅길", school="burum", kind="active", max_rank=5,
         cd=V(15, -1, "초"), use_cost="없음",
         values={"charges": V(3, 0, "회"), "slow": V(0.30, 0, "비율"), "duration": V(3, 0.5, "초"), "radius": V(3, 0, "m")},
         effect="켜 두면 다음 천도 3회 동안, 천도가 끝난 자리에 길이 생겨 반경 3m 적 이동이 30% 느려진다",
         tendo="천도 직후의 빈틈(시야가 돌아오는 순간)을 지켜 준다",
         pahon="파혼에는 걸리지 않는다. 켜 둔 채 파혼하면 횟수만 남는다",
         demo=False),
    dict(id="burum_longcall", name="오래 부르기", school="burum", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"chain_window": V(0.7, 0.65, "초")},
         effect="연속 천도로 인정되는 시간(기본 5초)이 늘어난다", tendo="연속 천도(0.8초)를 잇기 쉬워진다", pahon="없음", demo=False),
    dict(id="burum_neok", name="고마운 넋", school="burum", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"neok_bonus": V(0.07, 0.065, "비율")},
         effect="천도로 받는 넋이 늘어난다(기억 조각은 늘지 않음)", tendo="품계·인이 빨라진다", pahon="없음", demo=False),
    dict(id="burum_guard", name="곁을 지킴", school="burum", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"cast_dr": V(0.07, 0.065, "비율")},
         effect="천도 캐스팅 중 받는 피해가 줄어든다", tendo="맞아서 캐스팅이 끊길 위험이 준다(피격 시 중단 규칙은 그대로)", pahon="없음", demo=False),
    dict(id="burum_quota", name="몫을 채움", school="burum", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"move_bonus": V(0.04, 0.02, "비율")},
         effect="그날 밤 명부 몫(천도만 셈)을 채우면 그 밤 동안 이동 속도가 오른다", tendo="몫을 먼저 채우고 멀리 가는 전략", pahon="파혼은 몫에 안 들어간다", demo=False),
    dict(id="burum_seven", name="일곱 이름", school="burum", kind="deep", max_rank=1,
         cd=None, use_cost="없음", values={"chain_count": V(7, 0, "회")},
         effect="연속 천도 7회째 다음 천도 1회는 하한 0.5초로 끝난다. 시야 축소는 그대로",
         tendo="천도만으로 몰려오는 적을 버티는 빌드의 완성", pahon="파혼 한 번이면 연속이 끊긴다", demo=False),

    # ---------------- 줄 갈래 (중립: 싸움·제어) ----------------
    dict(id="jul_coil", name="휘감기", school="jul", kind="active", max_rank=5,
         cd=V(10, -0.5, "초"), use_cost="없음",
         values={"radius": V(4, 0, "m"), "bind": V(1.5, 0.1, "초")},
         effect="반경 4m 서 있는 적을 사슬로 묶어 못 움직이게 한다(보스는 묶는 시간 1/3)",
         tendo="천도 캐스팅 전에 주변을 묶어 두면 안전하게 보낼 수 있다",
         pahon="묶인 적은 파혼 폭발 피해는 받지만 넉백되지 않는다. 묶고 터뜨릴지, 터뜨려서 밀어낼지 고른다",
         demo=True),
    dict(id="jul_multipull", name="여럿 끌기", school="jul", kind="active", max_rank=5,
         cd=V(8, -0.4, "초"), use_cost="없음",
         values={"targets": V(3, 0.5, "명"), "range": V(10, 0, "m")},
         effect="10m 안 적 셋(→다섯)을 한꺼번에 끌어온다. 무릎 꿇은 혼은 끌지 않는다",
         tendo="흩어진 적을 모아 한 번에 정리한 뒤 천도할 틈을 만든다",
         pahon="적을 한곳에 모으면 파혼 폭발 한 번의 값어치가 커진다",
         demo=False),
    dict(id="jul_knotstep", name="매듭 걸음", school="jul", kind="active", max_rank=5,
         cd=V(7, -0.4, "초"), use_cost="없음",
         values={"distance": V(8, 0, "m"), "iframe": V(0.3, 0.02, "초")},
         effect="사슬을 걸어 8m를 달려 나간다. 달리는 동안 맞지 않는다",
         tendo="천도 캐스팅 중에 쓰면 캐스팅이 취소된다(혼의 대기 시간은 남은 만큼 이어짐)",
         pahon="포위에서 빠져나와 파혼 없이 버티는 선택지가 생긴다",
         demo=False),
    dict(id="jul_thread", name="한 줄 꿰기", school="jul", kind="active", max_rank=5,
         cd=V(20, -1, "초"), use_cost="없음",
         values={"range": V(5, 0, "m"), "pair_cast": V(2.4, -0.1, "초"), "pair_blast_mult": V(1.6, 0, "배")},
         effect="무릎 꿇은 혼 둘을 한 줄로 묶는다. 함께 천도(2.4초, 시야 축소 한 번, 넋·기억 둘 다) 또는 함께 파혼(폭발 피해 1.6배, 업 +2, 얼룩 2개가 한 자리). 덩어리는 못 꿴다",
         tendo="두 혼을 한 번의 위험으로 보낸다",
         pahon="한 자리에 얼룩이 2개 겹친다. 세 번째 얼룩이면 사나운 적이 나온다",
         demo=False),
    dict(id="jul_firmhand", name="단단한 손", school="jul", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"attack_speed": V(0.04, 0.03, "비율")},
         effect="공격 속도가 오른다", tendo="무릎 꿇리는 속도가 빨라져 처결 상황이 자주 온다", pahon="같음", demo=False),
    dict(id="jul_longchain", name="긴 사슬", school="jul", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"reach": V(0.3, 0.25, "m")},
         effect="모든 무기의 사거리가 늘어난다", tendo="거리를 두고 싸워 천도 자리를 지키기 쉽다", pahon="없음", demo=False),
    dict(id="jul_bound", name="묶인 자", school="jul", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"bound_damage": V(0.06, 0.045, "비율")},
         effect="묶이거나 고정된 적이 받는 맺힘 피해가 늘어난다", tendo="휘감기·삼지창과 짝", pahon="휘감기 후 파혼 폭발과 짝", demo=False),
    dict(id="jul_familiar", name="손에 익음", school="jul", kind="passive", max_rank=3,
         cd=None, use_cost="없음",
         values={"chain_pull_cd": V(0.10, 0.10, "비율"), "mace_stun": V(0.1, 0.1, "초"), "bell_slow": V(0.05, 0.05, "비율"),
                 "spear_pin": V(0.2, 0.2, "초"), "brush_mark": V(2, 2, "초")},
         effect="지금 든 무기의 특성 하나가 강해진다: 철삭 견인 재사용 −10/20/30% · 육모방망이 기절 +0.1/0.2/0.3초 · 요령 둔화 +5/10/15%p · 삼지창 고정 +0.2/0.4/0.6초 · 명부 붓 표식 지속 +2/4/6초",
         tendo="무기 성향을 더 진하게 만든다", pahon="무기 성향을 더 진하게 만든다", demo=False),
    dict(id="jul_cage", name="쇠사슬 울", school="jul", kind="deep", max_rank=1,
         cd=V(40, 0, "초"), use_cost="없음", values={"radius": V(5, 0, "m"), "hold": V(3, 0, "초"), "boss_hold": V(1, 0, "초")},
         effect="반경 5m 원 안의 서 있는 적을 3초 동안 고정한다(보스 1초)",
         tendo="울 안에서는 천도를 안전하게 할 수 있다", pahon="갇힌 적은 넉백 없이 폭발 피해만 받는다", demo=False),

    # ---------------- 얼룩 갈래 (파혼 쪽) ----------------
    dict(id="eol_burst", name="터뜨리기", school="eolruk", kind="active", max_rank=5,
         cd=V(9, -0.5, "초"), use_cost="얼룩 1개",
         values={"find_range": V(8, 0, "m"), "radius": V(2.5, 0, "m"), "damage": V(40, 6, "맺힘")},
         effect="8m 안 가장 가까운 원념 얼룩 하나를 터뜨려 없앤다. 반경 2.5m 맺힘 피해. 얼룩을 지우는 유일한 방법이며 업은 그대로다",
         tendo="얼룩을 지워 천도할 자리를 만들고, 세 번째 얼룩(사나운 적 소환)을 막는다",
         pahon="파혼의 뒤처리이자 두 번째 폭발. 파혼을 더 자주 하게 만든다",
         demo=True),
    dict(id="eol_grudge", name="원념 두르기", school="eolruk", kind="active", max_rank=5,
         cd=V(18, -1, "초"), use_cost="쓰는 동안 천도 캐스팅 +0.3초",
         values={"duration": V(6, 0, "초"), "atk_per_tier": V(0.05, 0.005, "비율/업 단계")},
         effect="6초 동안 업 단계(0~3)에 따라 공격력이 오른다(단계당 +5%→+7%). 업 벌칙은 그대로다",
         tendo="쓰는 동안 원념이 이름 부르는 목소리를 가려 천도가 느려진다",
         pahon="업이 높을수록 세진다. 업을 쌓고 싶은 유혹",
         demo=False),
    dict(id="eol_ride", name="얼룩 타기", school="eolruk", kind="active", max_rank=5,
         cd=V(14, -0.75, "초"), use_cost="없음",
         values={"duration": V(6, 0.5, "초"), "move_bonus": V(0.15, 0, "비율")},
         effect="잠깐 동안 얼룩 위에서 느려지는 대신 빨라진다",
         tendo="없음", pahon="얼룩 투성이 바닥을 무기로 쓴다. 대신 얼룩을 지우지는 않는다", demo=False),
    dict(id="eol_shard", name="깨진 이름 던지기", school="eolruk", kind="active", max_rank=5,
         cd=V(4, 0, "초"), use_cost="그 파혼의 엽전 0",
         values={"window": V(5, 0, "초"), "damage": V(30, 5, "맺힘"), "range": V(12, 0, "m")},
         effect="파혼 뒤 5초 안에 쓸 수 있다. 깨진 혼의 파편을 12m 날려 일직선 적을 관통한다",
         tendo="없음", pahon="파혼 한 번을 원거리 공격 한 번으로 바꾼다. 엽전을 포기하는 대가", demo=False),
    dict(id="eol_bigblast", name="큰 폭발", school="eolruk", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"pahon_radius": V(0.15, 0.125, "m")},
         effect="파혼 폭발 반경이 늘어난다(업 묶음 합계 상한 안)", tendo="없음", pahon="포위 탈출이 쉬워진다", demo=False),
    dict(id="eol_push", name="세찬 넉백", school="eolruk", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"pahon_knockback": V(0.15, 0.125, "비율")},
         effect="파혼 넉백 거리가 늘어난다", tendo="없음", pahon="밀어낸 뒤 천도할 틈을 만드는 '파혼으로 천도 돕기'", demo=False),
    dict(id="eol_coin", name="노잣돈", school="eolruk", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"coin_bonus": V(0.15, 0.125, "비율")},
         effect="파혼으로 얻는 엽전이 늘어난다", tendo="없음", pahon="장비 손보기 재화가 빨리 쌓인다", demo=False),
    dict(id="eol_dry", name="마른 얼룩", school="eolruk", kind="passive", max_rank=3,
         cd=None, use_cost="없음", values={"stain_duration_cut": V(0.10, 0.10, "비율")},
         effect="얼룩 지속 시간이 줄어든다(얼룩이 안 생기지는 않는다)", tendo="얼룩이 빨리 마르면 천도 자리가 빨리 생긴다", pahon="파혼의 바닥 대가가 줄어든다", demo=False),
    dict(id="eol_shadow", name="검은 갓의 그림자", school="eolruk", kind="deep", max_rank=1,
         cd=V(90, 0, "초"), use_cost="깨진 혼마다 업 +1, 얼룩 +1",
         values={"duration": V(10, 0, "초")},
         effect="10초 동안 파혼 폭발이 반경 안의 다른 무릎 꿇은 혼까지 함께 깨뜨린다(연쇄 파혼)",
         tendo="쓰는 동안 갓끈이 검게 바래는 연출. 결말 C(다음 검은 갓)의 거울",
         pahon="가장 강한 파혼 빌드의 완성. 대신 그 혼들의 이야기는 영영 없다", demo=False),
]

ACTIVE_SLOTS = {"count": 4, "unlock_rank": [1, 5, 12, 20], "keys_pc": ["1", "2", "3", "4"], "mobile": "기술 버튼 4"}
SKILL_POINTS = {"per_rank_up": 1, "per_boss_tendo": 1, "deep_unlock_school_points": 10,
                "note": "품계 2~50에서 49점 + 보스 천도 최대 30점 = 79점. 세 갈래를 다 채우려면 99점이라 다 배울 수 없다(빌드 선택이 생김)"}

# ---------------------------------------------------------------------------
# 2. 무기 다섯. 콤보 3타는 코드의 ComboStep 모양(damage·reach·sweepDeg·windup·swing·recover·knockback·stun)과 같다.
#    철삭·육모방망이는 이미 구현된 값(src/config.ts COMBO, unity WeaponTable.Mace)을 그대로 옮겼다.
#    index = 초당 맺힘 피해 / 철삭(36.1) × 100. 표 만들 때 자동으로 계산한다.
# ---------------------------------------------------------------------------
def step(name, damage, reach, sweep, windup, swing, recover, knockback, stun, extra=None):
    d = dict(name=name, damage=damage, reach=reach, sweepDeg=sweep, windup=windup, swing=swing,
             recover=recover, knockback=knockback, stun=stun)
    if extra:
        d.update(extra)
    return d

WEAPONS = [
    dict(id="chain", name="철삭", family="사슬", lean="기준", target_index=100, implemented=True,
         combo=[step("1 횡베기", 12, 4.6, 150, 0.09, 0.15, 0.13, 9, 0.28),
                step("2 역횡베기", 14, 4.6, 150, 0.08, 0.15, 0.13, 10, 0.3),
                step("3 회전 후려치기", 30, 5.6, 360, 0.16, 0.30, 0.36, 24, 0.65)],
         special=dict(name="견인", key="Q·우클릭", cd=0.5, values={"range": 13, "damage": 8, "stun": 0.8},
                      desc="13m 밖 적 하나를 사슬로 끌어온다"),
         judge=dict(tendo="무릎 꿇은 혼을 사슬로 묶어 끌고 다닐 수 있다(이동 −30%, 대기 시간은 그대로 흐름)",
                    pahon="기준(반경 3m, 피해 35, 넉백 2.5m)"),
         named=["흑월의 철삭(B-12)", "선장의 닻(B-10)", "첫 사슬(5막)"]),
    dict(id="mace", name="육모방망이", family="둔기", lean="파혼 쪽", target_index=90, implemented=True,
         combo=[step("1 내려치기", 16, 3.2, 110, 0.16, 0.18, 0.22, 12, 0.4),
                step("2 되치기", 18, 3.2, 110, 0.16, 0.18, 0.22, 13, 0.45),
                step("3 내려찍기", 34, 3.0, 360, 0.28, 0.22, 0.45, 18, 1.2)],
         special=dict(name="땅울림", key="Q·우클릭", cd=6, values={"radius": 4, "damage": 20, "stun": 0.8},
                      desc="땅을 내리쳐 반경 4m 적에게 맺힘 피해와 기절"),
         judge=dict(tendo="효과 없음. 여럿을 한꺼번에 무릎 꿇려 대기 시간이 동시에 흐른다(다 천도 못 함)",
                    pahon="파혼 넉백 +50%, 파혼 피해 +20%"),
         named=["문지기의 육모방망이(B-17)"]),
    dict(id="bell", name="요령", family="방울", lean="천도 쪽", target_index=70, implemented=False,
         combo=[step("1 울림", 10, 4.0, 360, 0.12, 0.12, 0.18, 4, 0.0, {"slow": 0.25, "slow_time": 1.0}),
                step("2 울림", 10, 4.0, 360, 0.12, 0.12, 0.18, 4, 0.0, {"slow": 0.25, "slow_time": 1.0}),
                step("3 큰 울림", 20, 4.5, 360, 0.20, 0.20, 0.35, 8, 0.3, {"slow": 0.25, "slow_time": 1.5})],
         special=dict(name="불러 세우기", key="Q·우클릭", cd=10, values={"radius": 6, "freeze": 3},
                      desc="반경 6m 무릎 꿇은 혼들의 처결 대기 시간이 3초 동안 멈춘다"),
         judge=dict(tendo="천도 캐스팅 −10%", pahon="파혼 폭발 피해 −30%. 포위되면 약해서 파혼에 기대게 된다"),
         named=["노인의 요령(B-13)"]),
    dict(id="spear", name="삼지창", family="장병", lean="자리 싸움", target_index=95, implemented=False,
         combo=[step("1 찌르기", 13, 5.0, 20, 0.10, 0.12, 0.16, 6, 0.2, {"pierce": 3}),
                step("2 찌르기", 14, 5.0, 20, 0.10, 0.12, 0.16, 6, 0.2, {"pierce": 3}),
                step("3 꿰찌르기", 24, 6.0, 20, 0.18, 0.20, 0.34, 0, 1.0, {"pierce": 3, "pin": 1.0})],
         special=dict(name="꽂아 버티기", key="Q·우클릭", cd=14, values={"radius": 2.5, "duration": 4},
                      desc="창을 땅에 꽂아 4초 동안 반경 2.5m 안으로 일반 적이 못 들어온다"),
         judge=dict(tendo="천도 캐스팅을 지키는 울타리(울타리 안에서 천도)",
                    pahon="파혼 폭발이 원 대신 앞쪽 6m 직선으로 나가고, 얼룩도 앞에 떨어진다(발밑이 깨끗)"),
         named=["찢어진 군기(B-05)", "두 편의 깃대 조각(7막)"]),
    dict(id="brush", name="명부 붓", family="원거리", lean="둘 다", target_index=75, implemented=False,
         combo=[step("1 먹 획", 10, 12.0, 0, 0.10, 0.10, 0.18, 3, 0.0, {"projectile": True, "mark": 1}),
                step("2 먹 획", 10, 12.0, 0, 0.10, 0.10, 0.18, 3, 0.0, {"projectile": True, "mark": 1}),
                step("3 큰 획", 18, 12.0, 0, 0.20, 0.15, 0.30, 6, 0.2, {"projectile": True, "pierce": 99, "mark": 1})],
         special=dict(name="이름 쓰기", key="Q·우클릭", cd=6, values={"mark_need": 3, "cast_cut": 0.4, "mark_time": 8},
                      desc="먹 표식 3개가 쌓인 적의 이름을 미리 써 둔다. 그 혼은 무릎 꿇으면 천도 캐스팅 −0.4초"),
         judge=dict(tendo="이름을 써 둔 혼은 천도 캐스팅 −0.4초(하한 0.5초)",
                    pahon="표식 있는 혼을 파혼하면 먹이 튀어 주변 4m 적에게 표식 +1"),
         named=["서리의 붓(B-15)"]),
]
WEAPON_SWAP = {"time": 0.5, "pc": "Tab", "mobile": "무기 바꾸기 버튼", "slots": 2}

def combo_dps(combo):
    """3타 한 바퀴 동안의 초당 맺힘 피해. 콤보 이음 대기(0.6초)는 빼고 순수 동작 시간만 쓴다(QA 시뮬과 같은 방식)."""
    dmg = sum(s["damage"] for s in combo)
    t = sum(s["windup"] + s["swing"] + s["recover"] for s in combo)
    return dmg / t

# ---------------------------------------------------------------------------
# 3. 장비: 칸·등급·옵션 풀·기울기 옵션·한 벌·이름 있는 물건(시즌 1)
#    옵션 값은 등급별 굴림 범위 [최소, 최대]. 흔한 0~1개, 손본 1~2개, 귀한 3~4개.
# ---------------------------------------------------------------------------
SLOTS = [
    dict(id="weapon", name="무기", count=2, sockets="0~2", main="손"),
    dict(id="gat", name="갓", count=1, sockets="0~2", main="혼·도술"),
    dict(id="dopo", name="도포", count=1, sockets="0~2", main="몸"),
    dict(id="tti", name="띠", count=1, sockets="없음", main="혼·업"),
    dict(id="sin", name="신", count=1, sockets="없음", main="몸(이동)"),
    dict(id="norigae", name="노리개", count=2, sockets="없음", main="특수"),
]
RARITIES = [
    dict(id="common", name="흔한", color="#F3E7D3", affixes="0~1", tilt=False, source="잡몹, 상자"),
    dict(id="crafted", name="손본", color="#4FA8A0", affixes="1~2", tilt=False, source="잡몹, 사나운 적"),
    dict(id="rare", name="귀한", color="#D4A94E", affixes="3~4", tilt=True, source="사나운 적(확정), 덩어리, 먼 구역"),
    dict(id="named", name="이름 있는", color="#E85C41", affixes="고유 1 + 2", tilt=False, source="보스 파혼, 먼 구역 숨은 자리"),
    dict(id="set", name="한 벌", color="#5FE3C0", affixes="한 벌 효과 + 1", tilt=False, source="관할별 정해진 자리"),
]
DROP = {"chance_on_maedhim_zero": 0.35, "rare": 0.08, "crafted": 0.30, "fierce_enemy": "귀한 확정(예비안: 70% 이상)",
        "note": "드롭 판정은 맺힘 0 때 1회, 천도·파혼과 무관"}

def A(id, group, name, slots, ranges, cap, demo=False, note=""):
    """옵션 하나. ranges = {등급id: [최소, 최대]}"""
    return dict(id=id, group=group, name=name, slots=slots, ranges=ranges, cap=cap, demo=demo, note=note)

ALL = ["weapon", "gat", "dopo", "tti", "sin", "norigae"]
AFFIXES = [
    # 손 (싸움)
    A("dmg_pct", "손", "맺힘 피해 +%", ["weapon", "norigae"], {"common": [3, 5], "crafted": [5, 9], "rare": [9, 14]}, "합계 +40%", demo=True),
    A("aspd_pct", "손", "공격 속도 +%", ["weapon", "norigae"], {"common": [2, 3], "crafted": [3, 6], "rare": [6, 9]}, "합계 +25%", demo=True),
    A("special_cd", "손", "무기 기술 재사용 −%", ["weapon", "gat"], {"common": [4, 6], "crafted": [6, 10], "rare": [10, 15]}, "합계 −40%"),
    A("fierce_dmg", "손", "사나운 적·덩어리 피해 +%", ["weapon", "norigae"], {"common": [5, 8], "crafted": [8, 14], "rare": [14, 20]}, "합계 +50%"),
    A("reach", "손", "무기 사거리 +m", ["weapon"], {"common": [0.1, 0.2], "crafted": [0.2, 0.3], "rare": [0.3, 0.5]}, "합계 +1.2m"),
    A("stun_time", "손", "기절·묶기 시간 +%", ["weapon", "tti"], {"common": [5, 8], "crafted": [8, 12], "rare": [12, 18]}, "합계 +40%"),
    A("skill_power", "손", "도술 위력 +%", ["gat", "norigae"], {"common": [3, 5], "crafted": [5, 9], "rare": [9, 14]}, "합계 +50%"),
    A("skill_cd", "손", "도술 재사용 −%", ["gat"], {"common": [3, 5], "crafted": [5, 8], "rare": [8, 12]}, "합계 −35%"),
    # 몸 (버티기)
    A("life", "몸", "생명 +", ["dopo", "gat", "sin", "tti"], {"common": [8, 12], "crafted": [12, 20], "rare": [20, 32]}, "없음"),
    A("armor_pct", "몸", "방어(받는 피해 −%)", ["dopo", "gat"], {"common": [2, 3], "crafted": [3, 5], "rare": [5, 8]}, "합계 60%"),
    A("move_pct", "몸", "이동 속도 +%", ["sin"], {"common": [2, 3], "crafted": [3, 5], "rare": [5, 8]}, "합계 +20%"),
    A("slow_resist", "몸", "둔화 저항(얼룩 포함) +%", ["sin", "dopo"], {"common": [5, 8], "crafted": [8, 12], "rare": [12, 18]}, "합계 50%"),
    A("stagger_cut", "몸", "피격 경직 −%", ["dopo"], {"common": [5, 8], "crafted": [8, 12], "rare": [12, 18]}, "합계 −50%"),
    A("return_time", "몸", "동트기 전 귀환 경고 +초", ["sin"], {"common": [3, 5], "crafted": [5, 8], "rare": [8, 12]}, "합계 +20초"),
    # 혼 (천도 쪽)
    A("tendo_cast", "혼", "천도 캐스팅 −%", ["tti", "gat", "norigae"], {"common": [2, 3], "crafted": [3, 5], "rare": [5, 8]}, "합계 −30%, 하한 0.5초", demo=True),
    A("chain_window", "혼", "연속 천도 창 +초", ["tti", "norigae"], {"common": [0.2, 0.3], "crafted": [0.3, 0.6], "rare": [0.6, 1.0]}, "합계 +3초"),
    A("tendo_neok", "혼", "천도 넋 +%", ["norigae"], {"common": [3, 4], "crafted": [4, 7], "rare": [7, 10]}, "합계 +30%"),
    A("cast_dr", "혼", "천도 중 받는 피해 −%", ["dopo", "tti"], {"common": [3, 5], "crafted": [5, 8], "rare": [8, 12]}, "합계 −40%"),
    A("wait_time", "혼", "처결 대기 시간 +초", ["tti"], {"common": [0.2, 0.3], "crafted": [0.3, 0.5], "rare": [0.5, 0.8]}, "합계 +2초(덩어리 제외)"),
    A("tendo_vision", "혼", "천도 중 최저 시야 +%p", ["gat"], {"common": [1, 1], "crafted": [1, 2], "rare": [2, 4]}, "최대 70%까지"),
    # 업 (파혼 쪽)
    A("pahon_radius", "업", "파혼 반경 +m", ["tti", "norigae"], {"common": [0.05, 0.1], "crafted": [0.1, 0.2], "rare": [0.2, 0.3]}, "면적 +40%(약 3.55m)", demo=True),
    A("pahon_dmg", "업", "파혼 피해 +%", ["weapon", "tti", "norigae"], {"common": [4, 6], "crafted": [6, 10], "rare": [10, 16]}, "합계 +50%"),
    A("pahon_kb", "업", "파혼 넉백 +%", ["tti", "dopo"], {"common": [5, 8], "crafted": [8, 12], "rare": [12, 18]}, "합계 +60%"),
    A("coin_pct", "업", "파혼 엽전 +%", ["norigae"], {"common": [4, 6], "crafted": [6, 10], "rare": [10, 15]}, "합계 +50%"),
    A("stain_cut", "업", "얼룩 지속 −%", ["sin", "tti"], {"common": [3, 5], "crafted": [5, 8], "rare": [8, 12]}, "합계 −30%"),
    A("stain_slow_cut", "업", "얼룩 둔화 −%p", ["sin"], {"common": [2, 3], "crafted": [3, 5], "rare": [5, 8]}, "합계 −15%p"),
]
TILTS = [
    dict(id="tilt_dmg_cast", name="피 묻은 매듭", plus="맺힘 피해 +20%", minus="천도 캐스팅 +10%(느려짐)", lean="파혼", demo=True, qa="검증 통과(경계 변화 없음)"),
    dict(id="tilt_neok_coin", name="향 내음", plus="천도 넋 +25%", minus="파혼 엽전 −50%", lean="천도", demo=False, qa="다음 단계 검증"),
    dict(id="tilt_radius_wait", name="검은 술", desc="갓끈 끝의 장식 끈", plus="파혼 반경 +0.3m", minus="처결 대기 시간 −0.5초(덩어리 외)", lean="파혼", demo=False, qa="미검증"),
    dict(id="tilt_window_dmg", name="젖은 소매", plus="연속 천도 창 +1.5초", minus="맺힘 피해 −10%", lean="천도", demo=False, qa="미검증"),
    dict(id="tilt_kb_vision", name="깨진 거울", plus="파혼 넉백 +30%", minus="천도 중 최저 시야 −5%p(55%)", lean="파혼", demo=False, qa="미검증 — 시야 하한 55% 허용 여부"),
    dict(id="tilt_castdr_aspd", name="상복 자락", plus="천도 중 받는 피해 −20%", minus="공격 속도 −8%", lean="천도", demo=False, qa="미검증"),
]
FORBIDDEN_AFFIXES = ["업이 안 쌓임(예외: 서리의 붓, 확률 25% 이하)", "얼룩이 안 생김", "기억 조각 증가", "천도 시야 축소 제거",
                     "덩어리 천도 가능", "자동 처결", "천도 캐스팅 0.5초 미만"]

SETS = [
    dict(id="set_baeung", name="배웅 한 벌", lean="천도", pieces=["갓", "띠", "신", "노리개"],
         bonus={"2": "연속 천도 창 +2초", "3": "천도를 끝낼 때마다 2초 동안 이동 +10%",
                "4": "연속 천도 중 혼불이 주변 2m 적을 밀어내 캐스팅을 지킨다(4초마다 1번)"}),
    dict(id="set_kkaejin", name="깨진 인 한 벌", lean="파혼", pieces=["무기", "도포", "띠", "노리개"],
         bonus={"2": "파혼 피해 +30%", "3": "파혼 직후 3초 동안 받는 피해 −15%",
                "4": "원념 얼룩 위에 서 있으면 공격력 +15%(3개째 얼룩 소환 위험은 그대로)"}),
    dict(id="set_sangdu", name="상두 한 벌", lean="번갈아", pieces=["갓", "도포", "신", "노리개"],
         bonus={"2": "천도 뒤 4초간 다음 파혼 반경 +0.5m, 파혼 뒤 4초간 다음 천도 캐스팅 −0.3초",
                "3": "번갈아 할 때마다 생명 3% 회복",
                "4": "천도와 파혼을 번갈아 4번 하면 혼불 하나가 3초 동안 함께 싸운다"}),
]

# 시즌 1(1~3막, B-01~B-12) 이름 있는 물건.
#   status: canon(서사 문서에 이미 있음) / proposal(기획 제안, 서사 확인 대기)
NAMED_S1 = [
    dict(id="named_wolhwa_bell", name="월화의 방울", slot="노리개", boss="B-02 월화 (폐당집) 파혼", status="canon",
         unique="파혼 폭발 반경 +1m (업 상한을 넘으므로 QA 확인 전 +0.5m)", memory_from="B-02",
         memory="열두째 잔은 당집 아이 몫이었다. 이름을 부르려는데 물이 들어왔다."),
    dict(id="named_torn_banner", name="찢어진 군기", slot="무기(삼지창)", boss="B-05 기수 대돌 (산성) 파혼", status="canon",
         unique="들고 있으면 주변 잡몹이 1초 겁먹는다(8초마다)", memory_from="B-05",
         memory="서른일곱. 매일 밤 불렀다. 오늘은 서른하나까지밖에 생각나지 않는다."),
    dict(id="named_general_armor", name="장수의 갑주", slot="도포", boss="B-06 이름 없는 장수 (군막 터) 파혼", status="canon",
         unique="방어 +10%, 대신 무기 바꿔 들기 +0.3초(무겁다)", memory_from="B-06",
         memory="번호를 부르면 앞만 보았다. 그래서 번호로 불렀다. 그래서 다 죽었다."),
    dict(id="named_captain_anchor", name="선장의 닻", slot="무기(철삭)", boss="B-10 만선호 선장 (난파 여울) 파혼", status="canon",
         unique="견인이 무거워진다: 끌어온 적 기절 +0.5초, 견인 재사용 +1초", memory_from="B-10",
         memory="줄을 끊자 배가 가벼워졌다. 나 혼자 남았다."),
    dict(id="named_heukwol_chain", name="흑월의 철삭", slot="무기(철삭)", boss="B-12 흑월 2차 (성문 밖) 파혼", status="canon",
         unique="전설 무기. 견인한 적이 무릎 꿇으면 대기 시간 +2초. 대신 F9(나의 정체)는 영영 없다", memory_from="B-12",
         memory="횃불을 진 젊은이가 물에 뛰어들었다. 숨이 끊기기 전에 이름을 불러 주지 못했다."),
    # 아래는 기획 제안: 이미 서사에 나오는 물건(단서·소품)을 '먼 구역 숨은 자리'에서 줍는 이름 있는 물건으로 쓰자는 안
    dict(id="named_naru_pole", name="칼금 새긴 삿대", slot="무기(삼지창)", boss="① 물막이 골 먼 여울 갈대 속 (B-01 처결 뒤)", status="after_boss",
         unique="찌르기 사거리 +1m, 물 위(얕은 여울)에서 이동 둔화 없음", memory_from="B-01",
         desc="열두 번째 금은 반만 새겨져 있다. (B-01 낮 단서 D-2와 같은 물건이라 처결 전에는 나오지 않는다)",
         memory="나루에 검은 갓이 서 있었다. 물에서 건져 낸 혼을 하나씩 깨뜨리고 있었다. 울면서."),
    dict(id="named_seo_brush", name="씻은 붓", slot="무기(명부 붓)", boss="② 역병막 약장 맨 아래 칸 (B-03 처결 뒤)", status="after_boss",
         unique="인이 흐린 이름의 천도 가산 +0.25초를 없앤다", memory_from="B-03",
         memory="이름을 지울 때마다 붓을 씻었다. 물이 검어질수록, 지운 이름은 내 손에 남았다."),
    # 살 부러진 부채(당할미의 물건, B-02 낮 단서)는 서사 판정으로 교체: 차사는 산 사람의 물건을 가져갈 수 없다
    dict(id="named_ok_sinkal", name="옥이의 신칼", slot="노리개", boss="① 폐당집 굿상 머리 (B-02 처결 뒤)", status="after_boss",
         unique="붙잡아 부르기 반경 +1.5m", memory_from="S-014 옥이(신딸)",
         memory="(기억 한 줄은 서사팀 S-014 데이터를 따른다)"),
    dict(id="named_chilseong_tag", name="열넷 목패", slot="노리개", boss="④ 무너진 막장 입구 (B-07 처결 뒤)", status="after_boss",
         unique="숫자 혼(인 없음) 천도 캐스팅 가산 +0.5초 → +0.25초", memory_from="B-07",
         memory="하나, 둘… 열셋. 다 나갔다. 하나가 모자란다."),
    dict(id="named_lamp_oil", name="등잔 기름", slot="소모품(이름 있는 물건 아님)", boss="B-09 망부석 아낙 파혼", status="canon",
         unique="천도 중 시야 축소 무효 3회(일회용). 기둥 1 예외라 소모품으로만 둔다", memory_from="B-09",
         memory="그이 몸은 아직 저 아래 있어요. 나는 혼만 데리고 가요."),
]
NON_ITEM_REWARDS_S1 = "B-01 엽전 ×30 · B-03 회복약 대량 · B-07 광석 대량(제작 재료) · B-08 엽전 ×80 · B-11 엽전 ×60 · B-04 처결 없음"

# ---------------------------------------------------------------------------
# 4. 넋 다섯 빛깔과 인 15종
# ---------------------------------------------------------------------------
NEOK_COLORS = [
    dict(id="blue", name="푸른 넋", obang="청(나무·동)", hex="#4FA8A0", death="산·숲·고개", zones="솔고개 마을, 폐당집", lean="빠름"),
    dict(id="red", name="붉은 넋", obang="적(불·남)", hex="#E85C41", death="싸움·불·역병", zones="붉은재, 검은여울 역병막", lean="셈(피해)"),
    dict(id="yellow", name="누런 넋", obang="황(흙·가운데)", hex="#D4A94E", death="밭·흙·광산", zones="보릿들, 쇳골", lean="버팀(생명)"),
    dict(id="white", name="흰 넋", obang="백(쇠·서)", hex="#F3E7D3", death="쇠·관아·명부", zones="동헌 터, 도성, 명부전", lean="굳음(방어)"),
    dict(id="black", name="검은 넋", obang="흑(물·북)", hex="#16213E", death="물", zones="물막이 골, 갯마을, 삼도천, 시즌 3 물 밑", lean="깊음(도술)"),
]
SEAL_COST = {"small": 40, "large": 120, "large_mult": 2.0, "where": "서낭당", "sockets": "무기·갓·도포 홈 0~2"}
SEALS = [
    ("blue", "blue", "날랜 인", "공격 속도 +6%", "중립"),
    ("red", "red", "센 인", "맺힘 피해 +8%", "중립"),
    ("yellow", "yellow", "굳은 인", "생명 +30", "중립"),
    ("white", "white", "쇠 인", "방어 +6%", "중립"),
    ("black", "black", "깊은 인", "도술 재사용 −8%", "중립"),
    ("blue", "red", "서두름 인", "연속 천도 창 +1초", "천도"),
    ("blue", "yellow", "길 인", "이동 속도 +5%", "중립"),
    ("blue", "white", "바람 인", "무기 기술 재사용 −10%", "중립"),
    ("blue", "black", "물길 인", "천도 캐스팅 −6%", "천도"),
    ("red", "yellow", "불씨 인", "파혼 피해 +15%", "파혼"),
    ("red", "white", "칼끝 인", "사나운 적·덩어리 피해 +12%", "중립"),
    ("red", "black", "그을음 인", "얼룩 지속 −20%", "파혼"),
    ("yellow", "white", "버팀 인", "천도 중 받는 피해 −15%", "천도"),
    ("yellow", "black", "무덤 인", "처결 대기 시간 +1초", "둘 다"),
    ("white", "black", "찬 인", "파혼 넉백 +30%", "파혼"),
]
SPECIAL_SEAL = dict(name="인의 조각", source="5막 보스 파혼 보상", note="만들 수 없는 가장 센 인. 효과는 서사 5막 확정안을 따른다")

STATS = [
    dict(id="str", name="힘", per_point="맺힘 피해 +1%, 넉백 +0.5%"),
    dict(id="agi", name="날램", per_point="공격 속도 +0.4%, 이동 속도 +0.2%"),
    dict(id="body", name="몸", per_point="생명 +4(기본 100), 얼룩 둔화 저항 +0.5%"),
    dict(id="mind", name="마음", per_point="도술 위력 +1%, 도술 재사용 −0.3%, 천도 캐스팅 −0.15%"),
]
RANKS = {"min": 1, "max": 50, "cost_formula": "40 × 품계^1.5 넋 (QA 1차)", "points_per_rank": 5, "start_each": 10}


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------
def at_rank(v, r):
    return round(v["base"] + v["per_rank"] * (r - 1), 3)

def fmt(x):
    if isinstance(x, float):
        s = ("%.3f" % x).rstrip("0").rstrip(".")
        return s
    return str(x)

def skill_rows():
    out = []
    for s in SKILLS:
        r = s["max_rank"]
        cd = "—" if not s["cd"] else (fmt(at_rank(s["cd"], 1)) + "초" + ("" if r == 1 or s["cd"]["per_rank"] == 0 else " → " + fmt(at_rank(s["cd"], r)) + "초"))
        vals = []
        for k, v in s["values"].items():
            a, b = at_rank(v, 1), at_rank(v, r)
            unit = v["unit"]
            if unit.startswith("비율"):
                a, b, unit = round(a * 100, 1), round(b * 100, 1), "%" + unit[2:]
            vals.append(fmt(a) + (unit if unit else "") + ("" if a == b else "→" + fmt(b) + (unit if unit else "")))
        out.append((s, cd, ", ".join(vals)))
    return out

def build_json():
    dps0 = combo_dps(WEAPONS[0]["combo"])
    weapons = []
    for w in WEAPONS:
        d = dict(w)
        d["dps"] = round(combo_dps(w["combo"]), 1)
        d["index"] = round(combo_dps(w["combo"]) / dps0 * 100, 1)
        weapons.append(d)
    return {
        "_설명": "차사 성장 시스템 데이터. tools/growth_data.py 가 만든다. 직접 고치지 말고 그 파일을 고친 뒤 다시 돌린다. 모든 수치 임시값.",
        "_version": VERSION,
        "schools": SCHOOLS, "skills": SKILLS, "active_slots": ACTIVE_SLOTS, "skill_points": SKILL_POINTS,
        "weapons": weapons, "weapon_swap": WEAPON_SWAP,
        "slots": SLOTS, "rarities": RARITIES, "drop": DROP, "affixes": AFFIXES, "tilts": TILTS,
        "forbidden_affixes": FORBIDDEN_AFFIXES, "sets": SETS, "named_season1": NAMED_S1,
        "non_item_rewards_season1": NON_ITEM_REWARDS_S1,
        "neok_colors": NEOK_COLORS, "seal_cost": SEAL_COST,
        "seals": [dict(a=a, b=b, name=n, effect=e, lean=l) for a, b, n, e, l in SEALS],
        "special_seal": SPECIAL_SEAL, "stats": STATS, "ranks": RANKS,
    }

def md_part(part):
    """기획서 부록에 넣을 마크다운. part = 1~4"""
    L = []
    if part == 1:
        L.append("### A-1. 도술 27개 상세")
        L.append("")
        L.append("단계마다 도술 점수 1점이 든다. 액티브는 5단계, 패시브는 3단계, 깊은 도술은 1단계이고 그 갈래에 10점 이상 넣어야 열린다. 점수는 품계가 오를 때 1점, 보스를 천도할 때 1점(최대 79점)이고, 세 갈래를 다 채우려면 99점이라 다 배울 수 없다. 액티브 칸은 넷이며 품계 1·5·12·20에 하나씩 열린다. 값은 1단계 → 최대 단계로 적었다.")
        for sk, sch in SCHOOLS.items():
            L.append("")
            L.append("**%s 갈래 (%s 쪽).** %s." % (sch["name"], sch["lean"], sch["desc"]))
            L.append("")
            L.append("| 도술 | 재사용 · 사용 대가 | 효과와 값 | 천도와의 관계 | 파혼과의 관계 |")
            L.append("|---|---|---|---|---|")
            for s, cd, vals in skill_rows():
                if s["school"] != sk:
                    continue
                kind = {"active": "액티브", "passive": "패시브", "deep": "깊은 도술"}[s["kind"]]
                name = "%s (%s %d단계)" % (s["name"], kind, s["max_rank"])
                L.append("| %s | %s · %s | %s (%s) | %s | %s |" % (name, cd, s["use_cost"], s["effect"], vals, s["tendo"], s["pahon"]))
    elif part == 2:
        dps0 = combo_dps(WEAPONS[0]["combo"])
        L.append("### A-2. 무기 다섯의 콤보와 특수 동작")
        L.append("")
        L.append("콤보 값은 코드의 콤보 표 모양(피해·사거리·각도·선딜·휘두름·후딜·넉백·기절)과 같다. 철삭과 육모방망이는 이미 들어간 값이고, 요령·삼지창·명부 붓은 새 임시값이다. 지수는 초당 맺힘 피해를 철삭과 견준 값이다. 무기는 두 자루를 차고 Tab(모바일 버튼)으로 0.5초 만에 바꿔 든다.")
        for w in WEAPONS:
            d = combo_dps(w["combo"])
            L.append("")
            L.append("**%s (%s, %s).** 초당 맺힘 %.1f, 지수 %d (목표 %d)%s." % (
                w["name"], w["family"], w["lean"], d, round(d / dps0 * 100), w["target_index"], "" if w["implemented"] else ", 새 임시값"))
            L.append("")
            L.append("| 타 | 피해 | 사거리·각도 | 선딜·휘두름·후딜 | 넉백·기절 | 특수 |")
            L.append("|---|---|---|---|---|---|")
            for s in w["combo"]:
                extra = []
                if s.get("slow"): extra.append("둔화 %d%% %s초" % (s["slow"] * 100, fmt(s["slow_time"])))
                if s.get("pierce"): extra.append("관통 %s" % ("전부" if s["pierce"] >= 99 else str(s["pierce"]) + "명"))
                if s.get("pin"): extra.append("고정 %s초" % fmt(s["pin"]))
                if s.get("projectile"): extra.append("투사체")
                if s.get("mark"): extra.append("먹 표식 +1")
                ang = "직선" if s["sweepDeg"] <= 20 else ("원" if s["sweepDeg"] >= 360 else "%d°" % s["sweepDeg"])
                L.append("| %s | %d | %sm · %s | %s · %s · %s초 | %s · %s초 | %s |" % (
                    s["name"], s["damage"], fmt(s["reach"]), ang, fmt(s["windup"]), fmt(s["swing"]), fmt(s["recover"]),
                    fmt(s["knockback"]), fmt(s["stun"]), ", ".join(extra) or "—"))
            sp = w["special"]
            L.append("")
            if w["id"] == "bell":
                L.append("")
                L.append("요령은 원 범위라 둘레의 적을 한꺼번에 맞힌다. 지수는 한 마리 기준이라 적이 셋 이상이면 실제 총 피해는 철삭보다 클 수 있다(QA 확인).")
            L.append("")
            L.append("무기 기술 **%s** (%s, 재사용 %s초): %s. 천도: %s. 파혼: %s. 이름 있는 물건: %s." % (
                sp["name"], sp["key"], fmt(sp["cd"]), sp["desc"], w["judge"]["tendo"], w["judge"]["pahon"], " · ".join(w["named"])))
    elif part == 3:
        names = {r["id"]: r["name"] for r in RARITIES}
        slotn = {s["id"]: s["name"] for s in SLOTS}
        L.append("### A-3. 장비 옵션 풀 · 한 벌 · 시즌 1 이름 있는 물건")
        L.append("")
        L.append("옵션은 등급별 굴림 범위를 적었다(흔한 / 손본 / 귀한). 상한은 장비·능력치·도술·인을 모두 합친 값이다. ★는 시연판에 먼저 들어가는 옵션이다. 드롭은 맺힘 0 때 35% 확률로 1회 굴리고(천도·파혼 무관), 그중 귀한 8%, 손본 30%, 나머지 흔한이다. 사나운 적은 귀한 확정(예비안 70% 이상).")
        for g in ["손", "몸", "혼", "업"]:
            L.append("")
            L.append("**%s 묶음.**" % {"손": "손(싸움)", "몸": "몸(버티기)", "혼": "혼(천도 쪽)", "업": "업(파혼 쪽)"}[g])
            L.append("")
            L.append("| 옵션 | 붙는 칸 | 흔한 / 손본 / 귀한 | 합계 상한 |")
            L.append("|---|---|---|---|")
            for a in AFFIXES:
                if a["group"] != g:
                    continue
                rng = " / ".join("%s~%s" % (fmt(a["ranges"][k][0]), fmt(a["ranges"][k][1])) for k in ["common", "crafted", "rare"])
                L.append("| %s%s | %s | %s | %s |" % ("★" if a["demo"] else "", a["name"], "·".join(slotn[s] for s in a["slots"]), rng, a["cap"]))
        L.append("")
        L.append("**기울기 옵션 (귀한 등급 이상, 한 물건에 하나).**")
        L.append("")
        L.append("| 이름 | 올라가는 쪽 | 내려가는 쪽 | 기울기 | QA |")
        L.append("|---|---|---|---|---|")
        for t in TILTS:
            L.append("| %s%s | %s | %s | %s | %s |" % ("★" if t["demo"] else "", t["name"] + ("(%s)" % t["desc"] if t.get("desc") else ""), t["plus"], t["minus"], t["lean"], t["qa"]))
        L.append("")
        L.append("만들지 않는 옵션: " + " / ".join(FORBIDDEN_AFFIXES) + ".")
        L.append("")
        L.append("**한 벌 셋의 단계 효과.**")
        L.append("")
        L.append("| 한 벌 | 부위 | 2부위 | 3부위 | 4부위 |")
        L.append("|---|---|---|---|---|")
        for s in SETS:
            L.append("| %s (%s) | %s | %s | %s | %s |" % (s["name"], s["lean"], "·".join(s["pieces"]), s["bonus"]["2"], s["bonus"]["3"], s["bonus"]["4"]))
        L.append("")
        L.append("**시즌 1 이름 있는 물건.** 확정은 서사 문서에 이미 있는 보상이다. ‘처결 뒤’는 보스의 소품을 숨은 자리 보상으로 쓴 것으로, 그 보스를 처결한 뒤(천도든 파혼이든)에만 나온다. 그래야 낮 단서와 겹치지 않고 어느 쪽 선택도 손해가 없다(서사팀 확인). 설명 칸의 기억 한 줄은 서사 데이터의 기억 칸을 그대로 쓴다.")
        L.append("")
        L.append("| 물건 | 칸 | 얻는 곳 | 고유 효과 | 상태 |")
        L.append("|---|---|---|---|---|")
        for n in NAMED_S1:
            L.append("| %s | %s | %s | %s | %s |" % (n["name"], n["slot"], n["boss"], n["unique"], {"canon": "확정", "after_boss": "확정(처결 뒤)"}.get(n["status"], "제안")))
        L.append("")
        L.append("장비가 아닌 시즌 1 보스 파혼 보상: " + NON_ITEM_REWARDS_S1 + ".")
    elif part == 4:
        cn = {c["id"]: c["name"].replace(" 넋", "") for c in NEOK_COLORS}
        L.append("### A-4. 넋 다섯 빛깔과 인 15종")
        L.append("")
        L.append("넋 빛깔은 혼이 죽은 자리와 까닭으로 정해진다(서사팀 확인). 화면에는 한글 빛깔명으로 보인다. 인은 서낭당에서 두 빛깔을 합쳐 만들고, 작은 인은 넋 %d, 큰 인은 넋 %d(효과 2배)이 든다. 무기·갓·도포의 홈(0~2)에 끼운다." % (SEAL_COST["small"], SEAL_COST["large"]))
        L.append("")
        L.append("| 빛깔 | 오방 | 죽은 자리·까닭 | 예시 구역 | 성향 |")
        L.append("|---|---|---|---|---|")
        for c in NEOK_COLORS:
            L.append("| %s | %s | %s | %s | %s |" % (c["name"], c["obang"], c["death"], c["zones"], c["lean"]))
        L.append("")
        L.append("| 조합 | 인 | 작은 인 효과 | 큰 인 효과 | 기울기 |")
        L.append("|---|---|---|---|---|")
        for a, b, n, e, l in SEALS:
            L.append("| %s+%s | %s | %s | 2배 | %s |" % (cn[a], cn[b], n, e, l))
        L.append("")
        L.append("%s(%s)은 %s" % (SPECIAL_SEAL["name"], SPECIAL_SEAL["source"], SPECIAL_SEAL["note"] + "."))
    return "\n".join(L)


# ── 코드팀 로더용 덮어쓰기 파일 ──────────────────────────────
# 왜: 코드팀(Unity)이 unity/Assets/Resources/Data/growth_overrides.json 을 읽는
#     로더를 만들었다. 그 로더는 "도술 이름·재사용 시간"과 "옵션 기본값"만 읽는다.
#     그래서 growth.json 전체가 아니라, 로더가 아는 이름(코드 이름)으로 바꾼 작은 파일을 따로 만든다.
# 도술 id 짝: 기획 id → 코드 id (코드에 이미 있는 시연판 도술 셋만)
CODE_SKILL_IDS = {"burum_hold": "HoldCall", "jul_coil": "Bind", "eol_burst": "StainBurst"}
# 옵션 짝: 기획 id → 코드 kind (코드에 이미 있는 8종만)
CODE_OPTION_KINDS = {
    "dmg_pct": "DamagePct", "aspd_pct": "AttackSpeedPct", "tendo_cast": "CastReducePct",
    "pahon_radius": "PahonAreaPct", "pahon_dmg": "PahonDamagePct", "life": "HpFlat",
    "move_pct": "MoveSpeedPct", "coin_pct": "CoinPct",
}
PAHON_BASE_RADIUS = 3.0  # 파혼 기준 반경(m). 반경 +m 옵션을 면적 %로 바꿀 때 쓴다(면적은 반경의 제곱에 비례)


def build_overrides():
    """기본값(base) = '흔한' 등급 굴림 범위의 가운데 값. % 옵션은 소수로(5% → 0.05), 생명은 그대로."""
    skills = []
    for sk in SKILLS:
        if sk["id"] in CODE_SKILL_IDS:
            skills.append({"id": CODE_SKILL_IDS[sk["id"]], "name": sk["name"], "cooldown": sk["cd"]["base"]})
    opts = []
    for a in AFFIXES:
        kind = CODE_OPTION_KINDS.get(a["id"])
        if not kind:
            continue
        lo, hi = a["ranges"]["common"]
        mid = (lo + hi) / 2
        if kind == "HpFlat":
            base = mid
        elif kind == "PahonAreaPct":
            # 반경 +mid m → 면적 증가율. 예: 3m→3.075m 이면 (3.075/3)^2 − 1 ≈ 0.051
            base = ((PAHON_BASE_RADIUS + mid) / PAHON_BASE_RADIUS) ** 2 - 1
        else:
            base = mid / 100
        opts.append({"kind": kind, "base": round(base, 4)})
    return {"_설명": "tools/growth_data.py가 만든 파일. 직접 고치지 말고 생성기를 고친다. base = 흔한 등급 범위 가운데 값.",
            "skills": skills, "optionBase": opts}


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(root, "data"), exist_ok=True)
    with open(os.path.join(root, "data", "growth.json"), "w", encoding="utf-8") as f:
        json.dump(build_json(), f, ensure_ascii=False, indent=2)
    with open(os.path.join(root, "data", "growth_overrides.json"), "w", encoding="utf-8") as f:
        json.dump(build_overrides(), f, ensure_ascii=False, indent=2)
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "planning", "growth")
    os.makedirs(outdir, exist_ok=True)
    for p in range(1, 5):
        with open(os.path.join(outdir, "appendix-%d.md" % p), "w", encoding="utf-8") as f:
            f.write(md_part(p))
    print("만듦: data/growth.json, %s/appendix-1~4.md" % outdir)
    for w in WEAPONS:
        print(w["name"], round(combo_dps(w["combo"]), 1), round(combo_dps(w["combo"]) / combo_dps(WEAPONS[0]["combo"]) * 100, 1))
