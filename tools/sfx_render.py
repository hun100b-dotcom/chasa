# -*- coding: utf-8 -*-
"""
차사 효과음 오프라인 합성기 (기획·사운드, 2026-10-25)

왜 따로 만드나:
  게임 안 SfxSynth.cs는 시작할 때 몇십 ms 안에 소리를 만들어야 해서 단순한 사인파·잡음만 쓴다.
  여기서는 시간 제약이 없으니 '울림(잔향)', '쇠붙이의 맥놀이(가까운 두 음이 부딪혀 우는 떨림)',
  '물방울(올라가는 짧은 음)', '나무 갈라짐(짧은 잡음 알갱이 여러 개)' 같은 걸 넣어 더 그럴듯하게 만든다.
  결과는 WAV 파일 → Unity가 Resources/Audio/Sfx 에서 먼저 찾고, 없으면 기존 코드 합성으로 돌아간다.

실행:  python3 tools/sfx_render.py      (numpy, scipy 필요)
결과:  unity/Assets/Resources/Audio/Sfx/<id의 점을 밑줄로>.wav  +  data/sfx_files.json(목록)
같은 id는 항상 같은 소리(고정 난수)라서 다시 돌려도 파일이 바뀌지 않는다.
"""
import json, os, zlib
import numpy as np
from scipy import signal as sg
from scipy.io import wavfile

SR = 44100                      # 1초에 44100번 소리 높이를 기록(CD 음질)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "unity/Assets/Resources/Audio/Sfx")


# ---------------------------------------------------------------------------
# 기본 재료
# ---------------------------------------------------------------------------
def T(sec):
    """길이 sec초짜리 시간축(초)"""
    return np.arange(int(sec * SR)) / SR


def env(n, a, d, curve=4.0, hold=0.0):
    """소리 크기 모양: a초 동안 커지고(어택), hold초 유지, d초 동안 줄어듦(감쇠). curve가 클수록 빨리 꺼짐"""
    t = np.arange(n) / SR
    e = np.ones(n)
    if a > 0:
        e = np.where(t < a, t / a, e)
    rel = np.clip((t - a - hold) / max(d, 1e-4), 0, None)
    e = e * np.exp(-curve * rel)
    e[t > a + hold + d * 2.5] = 0
    return e


def noise(n, rng):
    """하얀 잡음(모든 높이가 고르게 섞인 '쉬' 소리)"""
    return rng.standard_normal(n)


def filt(x, kind, f, q=0.7):
    """고정 필터. kind: low(낮은 소리만 통과) / high(높은 소리만) / band(f 근처만)"""
    if kind == "band":
        bw = f / q
        lo, hi = max(20, f - bw / 2), min(SR / 2 - 100, f + bw / 2)
        sos = sg.butter(2, [lo, hi], btype="bandpass", fs=SR, output="sos")
    else:
        sos = sg.butter(2, min(f, SR / 2 - 100), btype="lowpass" if kind == "low" else "highpass", fs=SR, output="sos")
    return sg.sosfilt(sos, x)


def sweep_filt(x, kind, f0, f1, q=0.7, block=256):
    """시간에 따라 필터 위치가 f0→f1로 미끄러지는 필터(숨 들이켜기, 폭발 뒤 먹먹해짐 등).
    256샘플씩 잘라 필터를 바꾸되, 필터 '기억'(zi)을 이어 받아 끊김이 없게 한다"""
    n = len(x); y = np.zeros(n); zi = None
    for i in range(0, n, block):
        k = i / max(n - 1, 1)
        f = f0 * (f1 / f0) ** k                     # 귀는 비율로 듣기 때문에 지수로 이동
        if kind == "band":
            bw = f / q
            sos = sg.butter(2, [max(20, f - bw / 2), min(SR / 2 - 100, f + bw / 2)], btype="bandpass", fs=SR, output="sos")
        else:
            sos = sg.butter(2, min(f, SR / 2 - 100), btype="lowpass" if kind == "low" else "highpass", fs=SR, output="sos")
        if zi is None or zi.shape[0] != sos.shape[0]:
            zi = sg.sosfilt_zi(sos) * 0
        y[i:i + block], zi = sg.sosfilt(sos, x[i:i + block], zi=zi)
    return y


def tone(sec, f0, f1=None, vib=0.0, vib_hz=5.0):
    """사인파 한 음. f0→f1로 미끄러지고, vib(반음 비율)만큼 떨림(비브라토)"""
    t = T(sec); f1 = f0 if f1 is None else f1
    f = f0 * (f1 / f0) ** (t / max(sec, 1e-4))
    f = f * (1 + vib * np.sin(2 * np.pi * vib_hz * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def modal(sec, modes, rng=None, strike=0.002):
    """쇠·나무·사기그릇처럼 '두드리면 여러 높이가 각자 꺼지는' 소리.
    modes = [(주파수, 꺼지는 시간초, 크기), ...] — 배음이 정수배가 아니면 쇠붙이처럼 들린다"""
    t = T(sec); y = np.zeros(len(t))
    for f, dec, a in modes:
        ph = 0 if rng is None else rng.uniform(0, 2 * np.pi)
        y += a * np.sin(2 * np.pi * f * t + ph) * np.exp(-t / dec)
    n = int(strike * SR)                              # 때리는 순간이 너무 딱딱하지 않게 아주 짧게 키움
    if n > 1:
        y[:n] *= np.linspace(0, 1, n)
    return y


def bubble(sec, f0, rise=2.2, dec=0.03):
    """물방울: 물속 공기 방울이 올라가며 '똑' — 짧게 올라가는 음(물 소리의 핵심)"""
    t = T(sec)
    f = f0 * (1 + (rise - 1) * np.clip(t / (dec * 3), 0, 1))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec)


def place(buf, x, at, gain=1.0):
    """buf의 at초 위치에 x를 더한다(넘치면 자름)"""
    i = int(at * SR)
    if i >= len(buf):
        return buf
    m = min(len(x), len(buf) - i)
    buf[i:i + m] += gain * x[:m]
    return buf


def grains(sec, rng, count, maker, spread=None, t0=0.0):
    """짧은 소리 알갱이를 여러 개 흩뿌림(엽전 쏟아짐, 나무 쪼개짐, 종이 바스락)"""
    buf = np.zeros(int(sec * SR))
    for k in range(count):
        at = t0 + (rng.uniform(0, sec - t0) if spread is None else spread(k, rng))
        place(buf, maker(rng, k), at)
    return buf


def reverb(x, rt=1.2, wet=0.25, tone_hz=5000, rng=None, pre=0.012):
    """울림(잔향): 소리가 공간에 부딪혀 남는 꼬리. 잡음이 서서히 꺼지는 '방 모양'을 곱해 만든다.
    rt = 울림이 60dB 줄어드는 시간(초), wet = 울림 섞는 양"""
    rng = rng or np.random.default_rng(7)
    n = int(rt * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-6.9 * t / rt)
    ir = filt(ir, "low", tone_hz)
    ir[: int(pre * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum()) + 1e-9
    tail = sg.fftconvolve(x, ir)
    dry = np.concatenate([x, np.zeros(len(tail) - len(x))])   # 길이 맞추기
    return dry * (1 - wet * 0.5) + tail * wet * 3


def trim(x, thr_db=-70):
    """끝의 거의 안 들리는 부분은 잘라 파일을 줄인다"""
    a = np.abs(x); thr = a.max() * 10 ** (thr_db / 20)
    idx = np.where(a > thr)[0]
    return x[: idx[-1] + int(0.02 * SR)] if len(idx) else x


def fade(x, a=0.002, d=0.02):
    n1, n2 = int(a * SR), int(d * SR)
    if n1: x[:n1] *= np.linspace(0, 1, n1)
    if n2: x[-n2:] *= np.linspace(1, 0, n2)
    return x


def loopify(x, cf=0.25):
    """반복 재생용: 끝 cf초를 처음과 겹쳐 이음매를 없앤다(크기 일정한 cos/sin 교차)"""
    c = int(cf * SR)
    body = x[c:].copy()
    w = np.linspace(0, np.pi / 2, c)
    body[-c:] = body[-c:] * np.cos(w) + x[:c] * np.sin(w)
    return body


# ---------------------------------------------------------------------------
# 소리 목록. 각 함수는 (샘플, 설명) 을 돌려준다. gain = 최대 크기(dBFS) — 기존 SfxSynth 와 같은 기준
# ---------------------------------------------------------------------------
REG = {}


def sfx(id, gain, cat, desc, loop=False, bypass_cast=False, use=""):
    def deco(fn):
        REG[id] = dict(fn=fn, gain=gain, cat=cat, desc=desc, loop=loop, bypass_cast=bypass_cast, use=use)
        return fn
    return deco


# ===== P0: 전투 손맛 =====
@sfx("sfx.hit.chain", -9, "전투", "철삭 타격: 쇠사슬 철컥 + 둔탁한 살 + 짧은 울림", use="휘두르기 적중")
def _(r):
    n = int(0.35 * SR)
    clank = modal(0.35, [(1240, .05, 1), (1873, .04, .8), (2631, .03, .6), (3410, .02, .4), (4980, .012, .3)], r)
    links = grains(0.35, r, 5, lambda r, k: modal(0.06, [(r.uniform(2800, 5200), .012, 1), (r.uniform(5200, 7400), .008, .6)], r),
                   spread=lambda k, r: 0.004 + k * 0.011 + r.uniform(0, .004))      # 사슬 고리들이 차례로 부딪힘
    thud = tone(0.35, 170, 80) * env(n, .001, .07)
    flesh = filt(noise(n, r), "band", 900, 1.2) * env(n, .001, .04)
    x = clank * .45 + links * .25 + thud * .9 + flesh * .5
    return reverb(x, .5, .12)


@sfx("sfx.hit.heavy", -6, "전투", "3타 막타: 낮고 무거운 쿵 + 맨 앞 딱 + 쇠 울림", use="3타·강공격 적중")
def _(r):
    n = int(0.6 * SR)
    boom = tone(.6, 95, 38) * env(n, .002, .18, 3)
    body = filt(noise(n, r), "low", 500) * env(n, .001, .1)
    snap = filt(noise(n, r), "band", 2200, 1.5) * env(n, .0005, .018)
    ring = modal(.6, [(620, .12, .5), (947, .09, .4), (1520, .06, .3)], r)
    x = boom * 1.0 + body * .7 + snap * .5 + ring * .25
    return reverb(x, .8, .15)


@sfx("sfx.enemy.telegraph", -10, "전투", "적 공격 예고: 숨 들이켜듯 올라가는 바람 + 낮은 쇳소리 긁힘", bypass_cast=True, use="적이 공격 준비할 때(천도 먹먹함 무시)")
def _(r):
    n = int(.42 * SR)
    breath = sweep_filt(noise(n, r), "band", 450, 2600, 2.5) * env(n, .30, .1, 6)
    scrape = tone(.42, 300, 460) * (1 + .5 * np.sign(np.sin(2 * np.pi * 37 * T(.42)))) * env(n, .28, .1, 6)
    return breath * .9 + filt(scrape, "band", 900, 2) * .25


@sfx("sfx.kneel", -8, "처결", "적 무릎: 기운이 빠지는 하강음 + 요령(무당 방울) 한 번 짤랑", use="적이 무릎 꿇는 순간(천도/파혼 고를 때)")
def _(r):
    n = int(1.4 * SR)
    fall = tone(1.4, 420, 180, .004, 5) * env(n, .005, .35, 3)
    bell = grains(1.4, r, 4, lambda r, k: modal(.9, [(2140 * (1 + .01 * k), .35, 1), (3215, .22, .6), (4870, .12, .35), (6230, .06, .2)], r),
                  spread=lambda k, r: .05 + k * .045 + r.uniform(0, .01))          # 방울 안 구슬이 몇 번 부딪힘
    return reverb(fall * .5 + bell * .3, 1.4, .3)


@sfx("sfx.tendo.cast", -12, "처결", "천도 캐스팅 반복음: 낮은 드론 두 겹 + 숨 섞인 대금 기운(반복용 4초)", loop=True, use="천도 시전 중 반복(코드가 음높이를 올림)")
def _(r):
    sec = 4.25; n = int(sec * SR); t = T(sec)
    d1 = tone(sec, 110) * (1 + .25 * np.sin(2 * np.pi * .5 * t))     # 4초에 두 번 숨 쉬는 크기 변화(반복과 맞물리게 0.5Hz)
    d2 = tone(sec, 165.5) * .5                                         # 살짝 어긋난 5도 = 느린 맥놀이
    air = filt(noise(n, r), "band", 660, 6) * (1 + .5 * np.sin(2 * np.pi * .5 * t + 1)) * .35
    x = d1 * .7 + d2 * .4 + air
    return loopify(x, .25)


@sfx("sfx.tendo.done", -7, "처결", "천도 완료: 맑은 방울 두 음이 위로 + 숨 내쉼 + 긴 울림", use="천도 성공")
def _(r):
    n = int(2.2 * SR)
    b1 = modal(2.2, [(880, .9, 1), (1763, .5, .4), (2650, .3, .25)], r)
    b2 = np.roll(modal(2.2, [(1320, .9, 1), (2644, .5, .4), (3970, .25, .2)], r), int(.16 * SR)); b2[:int(.16 * SR)] = 0
    exhale = sweep_filt(noise(n, r), "high", 700, 5500) * env(n, .05, .35, 4)
    return reverb(b1 * .55 + b2 * .5 + exhale * .25, 2.2, .35)


@sfx("sfx.pahon.burst", -4, "처결", "파혼: 저음 폭발 + 깨지는 고음 반음 부딪힘(찜찜함) + 먹먹해지는 꼬리", use="파혼 폭발")
def _(r):
    n = int(1.6 * SR)
    blast = sweep_filt(noise(n, r), "low", 3500, 160) * env(n, .002, .45, 3)
    sub = tone(1.6, 62, 40) * env(n, .003, .4, 3)
    crack = modal(1.6, [(1661, .25, 1), (1760, .25, 1), (3322, .12, .5), (3520, .12, .5)], r)   # 반음 차이 두 음 = 불편한 떨림
    debris = grains(1.6, r, 18, lambda r, k: filt(noise(int(.03 * SR), r), "band", r.uniform(1500, 5000), 3) * env(int(.03 * SR), .0005, .01),
                    spread=lambda k, r: .02 + r.exponential(.18))
    return reverb(blast * 1.0 + sub * .9 + crack * .18 + debris * .3, 1.6, .25, tone_hz=2500)


@sfx("sfx.player.hurt", -9, "전투", "주인공 피격: 둔탁한 퍽 + 숨 막힘", use="주인공이 맞을 때")
def _(r):
    n = int(.3 * SR)
    thud = tone(.3, 75, 48) * env(n, .001, .09)
    puff = filt(noise(n, r), "band", 700, 1.5) * env(n, .003, .06)
    return thud + puff * .5


@sfx("sfx.dodge", -12, "전투", "회피: 옷자락이 바람을 가르는 쉭", use="회피")
def _(r):
    n = int(.32 * SR)
    whoosh = sweep_filt(noise(n, r), "band", 380, 1900, 1.4) * env(n, .07, .12, 4)
    cloth = filt(noise(n, r) * (r.random(n) > .7), "band", 3000, 2) * env(n, .05, .1) * .15
    return whoosh + cloth


@sfx("sfx.clue", -11, "탐색", "단서 발견: 대금 같은 숨 섞인 한 음 + 살짝 울림", use="단서·기억 조각 획득")
def _(r):
    n = int(1.0 * SR)
    f = tone(1.0, 659, 659, .006, 5.5) * env(n, .06, .35, 3, hold=.15)
    air = filt(noise(n, r), "band", 659, 5) * env(n, .04, .3, 3, hold=.1)
    oct = tone(1.0, 1318) * env(n, .08, .2, 4) * .15
    return reverb(f * .7 + air * .35 + oct, 1.6, .3)


@sfx("sfx.bell", -7, "세계", "인정·파루 종: 낮고 긴 절 종(쇠 배음 + 맥놀이)", use="월드 시계 밤 시작·끝")
def _(r):
    m = [(98, 4.5, .8), (196.6, 4, 1), (198.2, 4, .7), (391, 3, .5), (588, 2.2, .35), (1013, 1.2, .25), (1570, .6, .12)]
    return reverb(modal(5, m, r, strike=.004), 2.5, .25, tone_hz=3000)


@sfx("amb.field", -24, "탐색", "들판 바람 + 풀벌레(반복용 8초). BGM이 있으면 꺼짐", loop=True, use="BGM 없을 때 임시 배경")
def _(r):
    sec = 8.3; n = int(sec * SR); t = T(sec)
    wind = filt(noise(n, r), "low", 380) * (0.6 + .4 * np.sin(2 * np.pi * t / 8.0 * 1 - 1)) * 1.0
    gust = sweep_filt(noise(n, r), "band", 300, 300, 1.5) * (.5 + .5 * np.sin(2 * np.pi * t / 4.0)) * .3
    chirp = np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 28 * t) > .2) * (np.sin(2 * np.pi * .55 * t) > .3) * .05
    return loopify(wind + gust + chirp, .3)


# ===== 기획 문서에 있었지만 코드에 없던 것 =====
@sfx("sfx.footstep", -20, "탐색", "흙길 발소리(바스락 + 낮은 툭)", use="걸음마다(코드가 음높이 무작위)")
def _(r):
    n = int(.16 * SR)
    thump = tone(.16, 110, 70) * env(n, .002, .03)
    grit = filt(noise(n, r) * (r.random(n) > .6), "band", 2500, 1) * env(n, .002, .04)
    return thump * .8 + grit * .5


@sfx("sfx.ui.click", -18, "UI", "버튼 누름: 나무 딱", use="버튼·탭")
def _(r):
    return modal(.08, [(1850, .012, 1), (3100, .008, .5), (720, .02, .4)], r)


@sfx("sfx.ui.confirm", -16, "UI", "확인: 나무 딱 + 작은 방울", use="선택 확정·창 닫기")
def _(r):
    x = modal(.6, [(1850, .012, 1), (720, .02, .4)], r)
    return reverb(x + np.roll(modal(.6, [(2640, .18, .5), (3960, .1, .25)], r), int(.05 * SR)) * .6, .8, .2)


@sfx("sfx.danger.enter", -11, "세계", "위험 지역 진입: 먼 징 한 번(낮게 우는 맥놀이)", use="원념 짙은 구역 들어설 때")
def _(r):
    m = [(146.0, 3, 1), (147.6, 3, .8), (291, 2, .45), (437, 1.4, .3), (690, .8, .2)]
    x = modal(3.5, m, r, strike=.008)
    x = filt(x, "low", 2500)
    return reverb(x, 3.0, .45, tone_hz=1800)


@sfx("sfx.clock.toll", -10, "세계", "시각 알림: 북 두 번(둥 — 둥)", use="월드 시계 큰 시각(동틀 녘 등)")
def _(r):
    def drum(r):
        n = int(1.2 * SR)
        return tone(1.2, 92, 70) * env(n, .003, .35, 3) + filt(noise(n, r), "low", 400) * env(n, .001, .05) * .4
    buf = np.zeros(int(2.4 * SR)); place(buf, drum(r), 0); place(buf, drum(r), .9, .8)
    return reverb(buf, 1.8, .3, tone_hz=2000)


# ===== 서사 컷신(보스 B-01 나루 영감 · B-02 월화 · B-03 서 의원)에 필요한 소리 =====
@sfx("amb.river.mist", -26, "컷신", "강가 물안개: 흐르는 물 + 낮은 바람(반복용 6초)", loop=True, use="B01 나루터 구역 배경")
def _(r):
    sec = 6.3; n = int(sec * SR)
    flow = filt(filt(noise(n, r), "band", 900, .6), "low", 2500) * .5
    bub = grains(sec, r, 40, lambda r, k: bubble(.12, r.uniform(500, 1400), 1.8, r.uniform(.01, .025)) * r.uniform(.2, .6))
    low = filt(noise(n, r), "low", 200) * .6
    return loopify(flow + bub * .25 + low, .3)


@sfx("cut.water.pole", -14, "컷신", "삿대로 물 짚기: 퐁 + 물 튐", use="B01 등장: 영감이 삿대로 물을 짚음")
def _(r):
    n = int(.9 * SR)
    plop = bubble(.9, 380, 2.4, .04)
    splash = filt(noise(n, r), "band", 2200, 1) * env(n, .003, .12, 4)
    drips = grains(.9, r, 6, lambda r, k: bubble(.1, r.uniform(900, 1800), 1.6, .012), spread=lambda k, r: .12 + r.uniform(0, .5))
    return reverb(plop * .8 + splash * .4 + drips * .3, 1.0, .2)


@sfx("cut.water.hands", -13, "컷신", "물에서 손이 올라옴: 물 가르며 솟는 소리 + 물 뚝뚝", use="B01 등장: 물에 빠진 혼 2마리")
def _(r):
    n = int(1.6 * SR)
    surge = sweep_filt(noise(n, r), "band", 300, 1600, 1.2) * env(n, .25, .4, 3)
    bub = grains(1.6, r, 25, lambda r, k: bubble(.12, r.uniform(250, 900), 2.0, .02) * r.uniform(.3, 1))
    drips = grains(1.6, r, 10, lambda r, k: bubble(.1, r.uniform(1000, 2200), 1.5, .01), spread=lambda k, r: .6 + r.uniform(0, .9))
    low = tone(1.6, 70, 55) * env(n, .2, .5) * .4
    return reverb(surge * .7 + bub * .35 + drips * .25 + low, 1.2, .25, tone_hz=3000)


@sfx("cut.water.drop", -16, "컷신", "작은 물건이 물에 떨어짐: 톡 + 작은 파문", use="B01 무릎: 삿대가 손에서 미끄러져 물에 뜸")
def _(r):
    return reverb(bubble(.5, 520, 2.6, .03) + grains(.5, r, 3, lambda r, k: bubble(.08, r.uniform(1200, 2000), 1.5, .008), spread=lambda k, r: .08 + k * .07) * .3, .9, .2)


@sfx("cut.coins.few", -14, "컷신", "엽전 몇 닢 짤랑(허리끈에 다시 매달림)", use="B01 천도: 엽전 다섯 닢")
def _(r):
    coin = lambda r, k: modal(.25, [(r.uniform(3800, 4400), .06, 1), (r.uniform(6100, 6800), .04, .6), (r.uniform(8900, 9600), .02, .3)], r)
    return reverb(grains(.9, r, 7, coin, spread=lambda k, r: k * .07 + r.uniform(0, .03)), .6, .15)


@sfx("cut.coins.spill", -11, "컷신", "엽전이 쏟아짐: 짤랑 무더기 + 물에 떨어지는 소리", use="B01 파혼: 엽전 ×30")
def _(r):
    coin = lambda r, k: modal(.25, [(r.uniform(3500, 4600), .05, 1), (r.uniform(5800, 7000), .03, .6)], r) * r.uniform(.3, 1)
    jingle = grains(1.8, r, 40, coin, spread=lambda k, r: r.exponential(.35))
    plops = grains(1.8, r, 14, lambda r, k: bubble(.12, r.uniform(600, 1500), 2, .015) * .6, spread=lambda k, r: .1 + r.exponential(.4))
    return reverb(jingle * .6 + plops * .4, 1.0, .2)


@sfx("cut.boat.break", -6, "컷신", "나룻배가 터짐: 나무 쪼개짐 + 판자 흩어짐 + 큰 물 튐", use="B01 파혼 폭발(약장 터짐에도 사용)")
def _(r):
    n = int(2.0 * SR)
    crack = grains(2.0, r, 30, lambda r, k: filt(noise(int(.04 * SR), r), "band", r.uniform(300, 1800), 2) * env(int(.04 * SR), .0005, .012) * r.uniform(.4, 1),
                   spread=lambda k, r: r.exponential(.06))
    planks = grains(2.0, r, 8, lambda r, k: modal(.4, [(r.uniform(180, 320), .08, 1), (r.uniform(520, 900), .05, .5)], r), spread=lambda k, r: .25 + r.uniform(0, 1.1))
    splash = filt(noise(n, r), "band", 1500, .8) * env(n, .01, .4, 3)
    boom = tone(2.0, 70, 40) * env(n, .003, .3)
    return reverb(crack * .9 + planks * .5 + splash * .35 + boom * .7, 1.4, .25, tone_hz=3500)


@sfx("cut.ledger.open", -15, "컷신", "명부가 펼쳐짐: 두꺼운 종이 넘김 + 낮은 울림", use="천도 컷신 시작(B01·B02·B03 공통)")
def _(r):
    n = int(1.2 * SR)
    flap = sweep_filt(noise(n, r), "band", 1200, 3500, 1.2) * env(n, .08, .15, 4)
    crinkle = filt(noise(n, r) * (r.random(n) > .93), "high", 3000) * env(n, .05, .2) * .5
    hum = tone(1.2, 196) * env(n, .2, .5, 3) * .25
    return reverb(flap + crinkle + hum, 1.4, .3)


@sfx("cut.brush.stroke", -17, "컷신", "붓 획: 한지 위를 쓸고 지나가는 사각 소리", use="천도: 명부에 붓 획이 이어짐")
def _(r):
    n = int(.7 * SR)
    swish = filt(noise(n, r), "band", 2400, 1.0) * env(n, .12, .25, 3, hold=.15)
    tex = filt(noise(n, r) * (r.random(n) > .85), "high", 4000) * env(n, .1, .3) * .3
    return swish + tex


@sfx("cut.seal.set", -13, "컷신", "인이 또렷해짐/찍힘: 도장 쿵 + 맑게 번지는 울림", use="천도: 흐렸던 인이 또렷해짐 · B03 붉은 인")
def _(r):
    n = int(1.6 * SR)
    stamp = tone(1.6, 140, 90) * env(n, .002, .06) + filt(noise(n, r), "low", 900) * env(n, .001, .03) * .5
    glow = modal(1.6, [(1046, .7, .6), (1568, .5, .4), (2093, .35, .25)], r)
    glow = np.roll(glow, int(.06 * SR)); glow[:int(.06 * SR)] = 0
    return reverb(stamp + glow * .35, 1.6, .3)


@sfx("cut.seal.fade", -18, "컷신", "인이 흐릿하게 떨리다 꺼짐: 떨리는 음이 내려가며 사라짐", use="단서 부족 천도 시도(B01·B02·B03 NOCLUE)")
def _(r):
    n = int(1.3 * SR)
    wob = tone(1.3, 880, 520, .02, 9) * env(n, .03, .4, 3, hold=.2)
    return reverb(wob * .6 + filt(noise(n, r), "band", 880, 4) * env(n, .03, .3) * .2, 1.0, .3)


@sfx("cut.stroke.scatter", -15, "컷신", "획이 흩어짐: 먹 가루가 바람에 날리는 쉬익 + 마른 바스락", use="파혼: 명부 이름 획이 흩어짐")
def _(r):
    n = int(1.8 * SR)
    blow = sweep_filt(noise(n, r), "band", 2500, 600, 1.5) * env(n, .05, .6, 3)
    grit = grains(1.8, r, 50, lambda r, k: filt(noise(int(.01 * SR), r), "high", 3500) * env(int(.01 * SR), .0005, .004), spread=lambda k, r: r.uniform(0, 1.4))
    return blow * .7 + grit * .3


@sfx("cut.lantern.light", -16, "컷신", "먼 곳에 불·등이 켜짐: 훅 + 따뜻한 낮은 화음", use="천도 마지막: 나룻불·처마 등·주막 등")
def _(r):
    n = int(2.2 * SR)
    whoof = sweep_filt(noise(n, r), "low", 300, 1400) * env(n, .04, .2, 4)
    warm = (tone(2.2, 220) + tone(2.2, 330) * .6 + tone(2.2, 440.8) * .3) * env(n, .3, .9, 3, hold=.3)
    return reverb(whoof * .6 + warm * .35, 2.0, .35, tone_hz=3500)


@sfx("cut.yoryeong.ring", -10, "컷신", "무당 방울(요령) 크게 한 번 흔듦", use="B02 등장: 방울이 한 번 울림")
def _(r):
    hit = lambda r, k: modal(1.5, [(2140 * r.uniform(.99, 1.01), .5, 1), (2180, .5, .6), (3215, .3, .5), (4870, .15, .3), (6230, .08, .2)], r) * (1 - k * .12)
    return reverb(grains(1.6, r, 6, hit, spread=lambda k, r: k * .055 + r.uniform(0, .01)), 1.6, .3)


@sfx("cut.bell.roll", -16, "컷신", "방울이 바닥을 굴러감: 작게 짤랑 짤랑 멀어짐", use="B02 무릎·파혼: 방울이 굴러 나감")
def _(r):
    hit = lambda r, k: modal(.4, [(2140, .12, 1), (3215, .08, .5)], r) * (1 - k / 14) * r.uniform(.5, 1)
    roll = filt(noise(int(1.5 * SR), r), "band", 600, 1) * env(int(1.5 * SR), .02, .6) * .15
    return reverb(grains(1.5, r, 12, hit, spread=lambda k, r: k * .1 + r.uniform(0, .03)) + roll, 1.0, .25)


@sfx("cut.cups.topple", -10, "컷신", "잔 열두 개가 한꺼번에 엎어짐: 사기 부딪힘 여러 번", use="B02 파혼")
def _(r):
    cup = lambda r, k: modal(.5, [(r.uniform(2400, 3200), .12, 1), (r.uniform(4100, 5200), .07, .6), (r.uniform(6400, 7600), .04, .3)], r) * r.uniform(.5, 1)
    return reverb(grains(1.4, r, 12, cup, spread=lambda k, r: r.exponential(.12)), 1.0, .2)


@sfx("cut.cups.set", -15, "컷신", "잔을 바로 세움: 사기 그릇 탁 한 번 + 맑은 여운", use="B02 천도: 열두째 잔 세움")
def _(r):
    return reverb(modal(1.0, [(2780, .25, 1), (4630, .15, .5), (7010, .07, .25), (420, .03, .4)], r), 1.4, .3)


@sfx("cut.cloth.flutter", -17, "컷신", "천 조각이 흩날림: 펄럭펄럭", use="B02 천도·파혼: 오방 천")
def _(r):
    n = int(1.6 * SR); t = T(1.6)
    flap = filt(noise(n, r), "band", 1100, .9) * (.5 + .5 * np.sin(2 * np.pi * 7 * t + 3 * np.sin(2 * np.pi * .7 * t))) ** 3
    return flap * env(n, .1, .7, 3, hold=.3)


@sfx("cut.dissolve", -16, "컷신", "혼이 빛으로 흩어짐: 반짝이는 높은 음들이 위로 퍼지며 사라짐", use="천도 마지막(오방 천 빛·약탕 빛)")
def _(r):
    sp = lambda r, k: tone(.6, r.uniform(1500, 4500) * (1 + k / 30)) * env(int(.6 * SR), .01, .15, 3) * r.uniform(.3, 1)
    n = int(2.2 * SR)
    air = sweep_filt(noise(n, r), "high", 1500, 7000) * env(n, .3, .6, 3) * .2
    return reverb(grains(2.2, r, 30, sp, spread=lambda k, r: k * .045 + r.uniform(0, .05)) * .3 + air, 1.8, .4)


@sfx("cut.drawer", -15, "컷신", "나무 서랍이 밀려 나왔다 들어감: 드르륵 — 탁", use="B03 등장·천도: 약장 서랍")
def _(r):
    n = int(1.0 * SR); t = T(1.0)
    slide = filt(noise(n, r), "band", 800, 2) * (np.sin(2 * np.pi * 45 * t) > 0) * (env(n, .05, .15, 2, hold=.15))
    knock = np.zeros(n); place(knock, modal(.3, [(260, .05, 1), (610, .03, .5)], r), .55)
    return reverb(slide * .5 + knock, .7, .15)


@sfx("cut.bottles.roll", -14, "컷신", "약병이 마당에 구름: 유리 딸깍 + 데구루루", use="B03 파혼: 회복약 다섯 병")
def _(r):
    clink = lambda r, k: modal(.3, [(r.uniform(3000, 3600), .08, 1), (r.uniform(5200, 6100), .05, .5)], r) * r.uniform(.4, 1)
    n = int(1.6 * SR)
    roll = filt(noise(n, r), "band", 450, 1.2) * env(n, .05, .7, 3) * .3
    return reverb(grains(1.6, r, 10, clink, spread=lambda k, r: r.exponential(.3)) * .6 + roll, .8, .2)


@sfx("cut.floor.flash", -14, "컷신", "바닥 칸이 붉게 깜빡: 낮게 웅 — 경고 박동", bypass_cast=True, use="B03 등장(전투 중 장판 예고에도 사용 가능)")
def _(r):
    n = int(.8 * SR)
    pulse = (tone(.8, 82) + tone(.8, 123) * .5) * env(n, .03, .25, 3, hold=.1)
    buzz = filt(noise(n, r), "band", 300, 3) * env(n, .03, .2) * .3
    return pulse + buzz



# ===== 서사 대본(705bcf0) 추가 요청 9종 =====
def voice(f0, formants, breath=0.15, rng=None, nh=40):
    """사람·동물 목소리 흉내(포먼트 합성): 성대 떨림(배음 많은 소리) → 입·목 모양 필터(포먼트).
    f0 = 매 샘플의 음높이 배열, formants = [(중심 주파수, Q, 크기), ...] (모음 '아'는 700·1200·2600Hz 근처)"""
    n = len(f0); ph = 2 * np.pi * np.cumsum(f0) / SR
    src = np.zeros(n)
    for k in range(1, nh + 1):
        src += np.where(k * f0 < SR / 2 - 500, np.sin(k * ph) / k, 0)      # 톱니파(배음 1/k) = 성대 소리 대용
    if rng is not None:
        src += breath * rng.standard_normal(n)                               # 숨소리 섞기
    out = np.zeros(n)
    for fc, bw, a in formants:
        out += a * filt(src, "band", fc, bw)                                 # bw = Q(날카로움): 클수록 좁은 공명
    return out


def curve(sec, pts):
    """[(초, 값), ...] 점들을 이은 곡선(음높이 윤곽 그리기용)"""
    t = T(sec); xs, ys = zip(*pts)
    return np.interp(t, xs, ys)


@sfx("amb.rain", -24, "세계", "빗소리: 고른 쏴아 + 처마 물방울 톡톡(반복용 8초)", loop=True, use="비 오는 날·장례 장면 배경")
def _(r):
    sec = 8.3; n = int(sec * SR)
    hiss = filt(filt(noise(n, r), "high", 900), "low", 9000) * .5
    patter = grains(sec, r, 900, lambda r, k: bubble(.03, r.uniform(2500, 6000), 1.3, .003) * r.uniform(.1, .5))
    drips = grains(sec, r, 30, lambda r, k: bubble(.12, r.uniform(700, 1500), 2, .015) * r.uniform(.3, .8))
    rumble = filt(noise(n, r), "low", 250) * .25
    return loopify(hiss + patter * .25 + drips * .35 + rumble, .3)


@sfx("cut.torch.sink", -13, "컷신", "횃불이 물에 잠김: 치익 김 빠지는 소리 + 불꽃 툭툭 꺼짐 + 물 꿀렁", use="횃불이 물에 잠기는 장면")
def _(r):
    n = int(2.2 * SR)
    fire = grains(.5, r, 25, lambda r, k: filt(noise(int(.008 * SR), r), "band", r.uniform(1500, 5000), 2) * env(int(.008 * SR), .0003, .003) * r.uniform(.3, 1))
    hiss = sweep_filt(noise(n, r), "high", 2500, 5500) * env(n, .03, .6, 3, hold=.2)
    plunge = bubble(1.0, 300, 2.0, .05)
    gl = grains(2.2, r, 15, lambda r, k: bubble(.1, r.uniform(300, 900), 2, .02) * .5, spread=lambda k, r: .1 + r.uniform(0, .9))
    buf = np.zeros(n); place(buf, fire, 0); place(buf, hiss * .6, .25); place(buf, plunge * .8, .25); buf += gl * .4
    return reverb(buf, 1.0, .2)


@sfx("cut.chain.wrap", -12, "컷신", "사슬이 손목에 감김: 차르르 고리 미끄러짐 + 마지막 철컥 조임", use="철삭이 손목에 감기는 장면")
def _(r):
    link = lambda r, k: modal(.12, [(r.uniform(2600, 4200), .02, 1), (r.uniform(5000, 7500), .012, .5)], r) * (.4 + .6 * k / 18)
    rattle = grains(1.2, r, 18, link, spread=lambda k, r: .02 + .9 * (k / 18) ** .8 + r.uniform(0, .015))   # 점점 빨라지며 감김
    slide = filt(noise(int(1.2 * SR), r), "band", 3500, 1.5) * env(int(1.2 * SR), .1, .4, 3, hold=.4) * .15
    lock = modal(.5, [(1240, .08, 1), (1873, .06, .8), (2631, .05, .6), (180, .05, .8)], r)
    buf = rattle + slide; place(buf, lock * .9, .98)
    return reverb(buf, .6, .15)


@sfx("cut.cough", -14, "컷신", "서 의원 마른기침: 콜록 두 번 + 숨 들이켬(목소리 합성)", use="B03 등장: 의원이 기침")
def _(r):
    def burst(r, dur):
        n = int(dur * SR)
        src = noise(n, r) * env(n, .004, dur * .5, 4)
        y = filt(src, "band", 600, 1.5) * .8 + filt(src, "band", 1700, 2.5) * .6 + filt(src, "band", 2700, 3) * .3   # 거친 '에' 모음 모양 잡음
        f0 = np.full(n, r.uniform(140, 170)) * np.linspace(1.05, .9, n)
        y += voice(f0, [(600, 1.5, 1), (1700, 2.5, .5)], .1, r) * env(n, .006, dur * .4, 5) * .25          # 목이 살짝 울리는 소리
        return y
    buf = np.zeros(int(1.6 * SR))
    place(buf, burst(r, .22), 0); place(buf, burst(r, .18) * .8, .32); place(buf, burst(r, .12) * .5, .58)
    inhale = sweep_filt(noise(int(.5 * SR), r), "band", 900, 1800, 2) * env(int(.5 * SR), .3, .1, 5) * .2
    place(buf, inhale, 1.0)
    return reverb(buf, .6, .12)


@sfx("amb.rooster", -18, "세계", "먼 닭울음: 꼬끼오— 마을 너머에서 들림(목소리 합성, 멀리 깎음)", use="동틀 녘 마을")
def _(r):
    sec = 2.4
    f0 = curve(sec, [(0, 520), (.12, 560), (.18, 700), (.35, 760), (.45, 820), (.7, 900), (1.3, 880), (1.6, 700), (1.75, 600)])
    f0 = f0 * (1 + .02 * np.sin(2 * np.pi * 22 * T(sec)))                     # 닭 특유의 떨림
    amp = curve(sec, [(0, 0), (.03, 1), (.13, .9), (.15, .2), (.19, 1), (.33, .9), (.36, .3), (.40, 1), (1.55, .9), (1.8, 0), (2.4, 0)])
    y = voice(f0, [(900, 3, 1), (1900, 4, .6), (3100, 5, .3)], .25, r, nh=20) * amp
    y = filt(y, "low", 2500)                                                     # 멀리서 들리면 높은 소리가 먼저 사라진다
    return reverb(y, 2.2, .6, tone_hz=2000)


@sfx("vo.wail", -14, "컷신", "말 없는 곡소리: '아—이—' 길게 흐느끼며 내려가는 울음(목소리 합성, 가사 없음)", use="장례·곡하는 장면")
def _(r):
    sec = 5.5; t = T(sec)
    f0 = curve(sec, [(0, 330), (.4, 392), (1.2, 370), (1.8, 330), (2.2, 294), (2.6, 330), (3.4, 294), (4.2, 262), (5.2, 247)])
    f0 = f0 * (1 + .025 * np.sin(2 * np.pi * 5.5 * t) + .01 * np.sin(2 * np.pi * 1.3 * t))   # 흐느끼는 떨림
    sob = 1 - .6 * (np.sin(2 * np.pi * t / 1.4 - 1) > .85)                     # 중간중간 끊기는 흐느낌
    amp = curve(sec, [(0, 0), (.25, 1), (2.0, .9), (2.15, .3), (2.4, 1), (4.5, .7), (5.5, 0)]) * sob
    # 모음이 '아'에서 '이'로 천천히 바뀜 → 포먼트 이동
    a_mix = curve(sec, [(0, 1), (1.8, 1), (2.6, 0), (3.6, 0), (4.4, 1), (5.5, 1)])
    va = voice(f0, [(800, 5, 1), (1250, 6, .5), (2800, 8, .25)], .12, r)
    vi = voice(f0, [(320, 4, 1), (2300, 7, .45), (3000, 8, .25)], .12, r)
    y = (va * a_mix + vi * (1 - a_mix)) * amp
    return reverb(y, 2.0, .45, tone_hz=4000)


@sfx("mus.sangyeo.far", -18, "컷신", "먼 상여소리: 요령 소리에 맞춰 여러 사내가 받는 낮은 소리(가사 안 들림, 반복용 12초)", loop=True, use="장례 행렬이 멀리 지나갈 때")
def _(r):
    sec = 12.6; n = int(sec * SR); buf = np.zeros(n)
    # 앞소리(한 명) → 뒷소리(여럿이 받음) 두 마디 반복. 계면조 비슷한 음 D-F-G-A
    lead = [(0.0, 2.4, [294, 349, 330, 294]), (6.3, 2.4, [294, 392, 349, 294])]
    chorus = [(3.0, 2.8, [220, 262, 247, 220]), (9.3, 2.8, [220, 262, 220, 196])]
    def phrase(dur, notes, voices, rng):
        m = len(notes); pts = []
        for i, f in enumerate(notes):
            pts += [(dur * i / m, f), (dur * (i + .8) / m, f)]
        f0 = curve(dur, pts)
        y = np.zeros(int(dur * SR))
        for v in range(voices):                                               # 여러 사람이 조금씩 어긋나게 = 합창
            det = 1 + rng.uniform(-.012, .012)
            fv = f0 * det * (1 + .02 * np.sin(2 * np.pi * rng.uniform(4.5, 6) * T(dur) + rng.uniform(0, 6)))
            y += voice(fv, [(500, 4, 1), (850, 5, .6), (2500, 8, .15)], .1, rng, nh=25)   # '오' 비슷한 모음
        return y * env(len(y), .3, dur * .2, 3, hold=dur * .6)
    for at, d, notes in lead:
        place(buf, phrase(d, notes, 1, r), at)
    for at, d, notes in chorus:
        place(buf, phrase(d, notes, 6, r) * .5, at)
    bell = lambda r, k: modal(.6, [(2140, .25, 1), (3215, .15, .5)], r) * .25
    for k in range(int(sec / .7)):                                              # 요령이 박마다 짤랑
        place(buf, bell(r, k), k * .7 + .05)
    y = filt(buf, "low", 1800)                                                  # 멀리서 들림
    return loopify(reverb(y, 2.5, .55, tone_hz=1500)[:n + int(.3 * SR)], .3)


@sfx("cut.bellows", -13, "컷신", "풀무질과 불꽃: 훅—훅 바람 두 번 + 불이 확 살며 튀는 불티", use="대장간·풀무 장면")
def _(r):
    sec = 3.0; n = int(sec * SR); buf = np.zeros(n)
    def puff(r):
        m = int(.7 * SR)
        return filt(noise(m, r), "low", 500) * env(m, .15, .25, 3, hold=.1) + tone(.7, 60) * env(m, .15, .25, 3) * .3
    place(buf, puff(r), 0); place(buf, puff(r), 1.2)
    roar = filt(noise(n, r), "band", 700, .8) * curve(sec, [(0, 0), (.4, .4), (.8, .15), (1.6, .6), (2.2, .3), (3, .1)])
    sparks = grains(sec, r, 45, lambda r, k: filt(noise(int(.006 * SR), r), "band", r.uniform(2500, 7000), 3) * env(int(.006 * SR), .0002, .002) * r.uniform(.2, 1),
                    spread=lambda k, r: (.4 if k < 15 else 1.6) + r.exponential(.3))
    return reverb(buf * .9 + roar * .4 + sparks * .5, .8, .15)


@sfx("sfx.dog.whine", -16, "세계", "개 낑낑: 높게 올라갔다 내려가는 짧은 콧소리 세 번(합성)", use="마을 개·겁먹은 개")
def _(r):
    buf = np.zeros(int(2.0 * SR))
    for k, (at, d, hi) in enumerate([(0, .45, 1150), (.6, .35, 1050), (1.1, .6, 1250)]):
        f0 = curve(d, [(0, 700), (d * .35, hi), (d, 650)])
        y = voice(f0, [(1200, 4, 1), (2600, 5, .4), (400, 3, .3)], .3, r, nh=10) * env(int(d * SR), .04, d * .4, 3, hold=d * .3)
        place(buf, y * (1 - .15 * k), at)
    return reverb(buf, .7, .15)


# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {"_설명": "효과음 파일 목록(기획·사운드 tools/sfx_render.py가 만듦). 코드는 Resources.Load('Audio/Sfx/'+file)로 먼저 찾고, 없으면 SfxSynth 코드 합성으로 대신한다. 크기(dBFS)는 파일에 이미 맞춰 둠 → 재생 볼륨 1.0. 직접 합성이라 외부 저작권 없음.",
                "sounds": []}
    for id, s in REG.items():
        seed = zlib.crc32(id.encode()) & 0xffffffff               # id마다 고정 난수 → 다시 돌려도 같은 소리
        r = np.random.default_rng(seed)
        x = np.asarray(s["fn"](r), dtype=np.float64)
        if not s["loop"]:
            x = fade(trim(x))
        x = x / (np.abs(x).max() + 1e-12) * 10 ** (s["gain"] / 20)    # 최대 크기를 gain dBFS로
        name = id.replace(".", "_")
        wavfile.write(os.path.join(OUT, name + ".wav"), SR, (x * 32767).astype(np.int16))
        manifest["sounds"].append(dict(id=id, file=name, category=s["cat"], desc=s["desc"], use=s["use"],
                                       loop=s["loop"], bypass_cast_filter=s["bypass_cast"],
                                       length_sec=round(len(x) / SR, 2), peak_dbfs=s["gain"]))
        print(f"{id:22s} {len(x)/SR:5.2f}s  {s['cat']}")
    with open(os.path.join(ROOT, "data/sfx_files.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(len(REG), "개")


if __name__ == "__main__":
    main()
