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


# ===== 땅 재질별 발소리 (2026-10-25) =====
# 코드의 땅 재질 층 순서(GroundTerrain): 0 흙 · 1 풀 · 2 자갈 · 3 논 · 4 낙엽, 그리고 물(얕은 물·강가)
# 한 걸음 = 뒤꿈치(heel) 닿는 소리 + 0.06~0.09초 뒤 앞꿈치(toe) 소리. 재질마다 '알갱이'가 다르다.
# 변형 4개: 같은 재질도 매번 조금씩 달라야 기계처럼 안 들린다(같은 파일만 반복하면 귀가 금방 알아챈다).
STEP_VARIANTS = 4


def _heel_toe(r, part):
    """part(r, 세기) → 한 번 닿는 소리. 뒤꿈치(세게) + 앞꿈치(약하게, 조금 뒤) 두 번을 붙인다"""
    gap = r.uniform(.055, .09)
    buf = np.zeros(int(.45 * SR))
    place(buf, part(r, 1.0), 0)
    place(buf, part(r, r.uniform(.45, .65)), gap)
    return buf


def _step_dirt(r, k):
    def part(r, g):
        n = int(.12 * SR)
        thump = tone(.12, r.uniform(95, 120), 60) * env(n, .002, .025)
        grit = filt(noise(n, r) * (r.random(n) > .55), "band", r.uniform(1800, 2600), 1) * env(n, .002, .035)
        return g * (thump * .8 + grit * .45)
    return _heel_toe(r, part)


def _step_grass(r, k):
    def part(r, g):
        n = int(.2 * SR)
        swish = filt(noise(n, r), "band", r.uniform(3000, 4200), 1.2) * env(n, .015, .06, 3)    # 풀잎이 스치는 '쉭'(시작이 부드럽다)
        thump = tone(.2, r.uniform(80, 100), 55) * env(n, .004, .03) * .5                       # 흙보다 먹먹한 바닥
        return g * (swish * .6 + filt(thump, "low", 400))
    return _heel_toe(r, part)


def _step_gravel(r, k):
    def part(r, g):
        n = int(.18 * SR)
        pebbles = grains(.18, r, int(r.integers(9, 15)), lambda r, i: modal(.04, [(r.uniform(1800, 5200), .008, 1), (r.uniform(5200, 8000), .005, .5)], r) * r.uniform(.2, 1),
                         spread=lambda i, r: r.exponential(.025))                                   # 자갈끼리 부딪히는 '자글'
        crunch = filt(noise(n, r), "band", 2500, .8) * env(n, .002, .04)
        thump = tone(.18, 110, 65) * env(n, .002, .02) * .6
        return g * (pebbles * .55 + crunch * .4 + thump)
    return _heel_toe(r, part)


def _step_paddy(r, k):
    def part(r, g):
        n = int(.3 * SR)
        thump = filt(tone(.3, r.uniform(70, 90), 50) * env(n, .006, .04), "low", 300)
        suck = bubble(.3, r.uniform(140, 220), 2.6, .05) * env(n, .03, .08, 3, hold=.03)        # 진흙에서 발을 뺄 때 '쩍'(낮게 올라가는 음)
        squish = filt(noise(n, r), "low", 900) * (1 + np.sin(2 * np.pi * r.uniform(35, 55) * T(.3))) * env(n, .01, .07) * .5
        return g * (thump + suck * .5 + squish * .5)
    return _heel_toe(r, part)


def _step_leaves(r, k):
    def part(r, g):
        n = int(.2 * SR)
        crackle = grains(.2, r, int(r.integers(18, 30)), lambda r, i: filt(noise(int(.004 * SR), r), "high", r.uniform(3000, 6000)) * env(int(.004 * SR), .0002, .0015) * r.uniform(.2, 1),
                         spread=lambda i, r: r.exponential(.04))                                    # 마른 잎이 바스러지는 '바삭'
        rustle = filt(noise(n, r), "band", 2200, 1) * env(n, .01, .06, 3) * .4
        thump = tone(.2, 95, 60) * env(n, .003, .02) * .35
        return g * (crackle * .7 + rustle + thump)
    return _heel_toe(r, part)


def _step_water(r, k):
    def part(r, g):
        n = int(.35 * SR)
        splash = filt(noise(n, r), "band", r.uniform(1400, 2200), .9) * env(n, .004, .08, 3)
        bub = grains(.35, r, 6, lambda r, i: bubble(.1, r.uniform(400, 1200), 2, .015) * r.uniform(.3, 1), spread=lambda i, r: .01 + r.exponential(.05))
        slap = filt(tone(.35, 140, 80) * env(n, .002, .03), "low", 500) * .5
        return g * (splash * .7 + bub * .4 + slap)
    return _heel_toe(r, part)


# 최대 크기(dBFS)는 재질마다 다르게: 낙엽처럼 뾰족한 소리는 최대값만 크고 평균은 작아서, 귀로 듣는 크기(평균 −38dB 근처)를 맞추려고 조정함
STEPS = [("dirt", "흙", _step_dirt, -20, "흙길: 낮은 툭 + 고운 흙 사각"),
         ("grass", "풀", _step_grass, -19, "풀밭: 풀잎 스치는 쉭 + 먹먹한 바닥"),
         ("gravel", "자갈", _step_gravel, -21, "자갈: 돌 알갱이 자글자글 + 바삭"),
         ("paddy", "논", _step_paddy, -23, "논·진흙: 질척 + 발 빼는 쩍"),
         ("leaves", "낙엽", _step_leaves, -13, "낙엽: 마른 잎 바스러짐 + 바스락"),
         ("water", "물", _step_water, -22, "얕은 물: 첨벙 + 물방울")]
for _key, _ko, _fn, _g, _desc in STEPS:
    for _k in range(1, STEP_VARIANTS + 1):
        sfx(f"sfx.step.{_key}.{_k}", _g, "발소리", f"{_desc} (변형 {_k})", use=f"{_ko} 위를 걸을 때 한 걸음")(lambda r, f=_fn, k=_k: f(r, k))


# ===== 날씨 소리 (반복용) =====
@sfx("amb.weather.rain", -23, "날씨", "비: 고른 빗줄기 + 지붕·잎에 떨어지는 톡톡 + 낮은 웅웅(반복용 12초)", loop=True, use="비 오는 날 필드 배경(옛 amb.rain보다 길고 풍성)")
def _(r):
    sec = 12.3; n = int(sec * SR); t = T(sec)
    hiss = filt(filt(noise(n, r), "high", 700), "low", 8000) * (.85 + .15 * np.sin(2 * np.pi * t / 6))
    patter = grains(sec, r, 1600, lambda r, k: bubble(.025, r.uniform(2500, 6500), 1.3, .0025) * r.uniform(.05, .4))
    leaf = grains(sec, r, 120, lambda r, k: filt(noise(int(.01 * SR), r), "band", r.uniform(1200, 3000), 2) * env(int(.01 * SR), .0005, .004) * r.uniform(.1, .5))
    roof = grains(sec, r, 40, lambda r, k: modal(.08, [(r.uniform(600, 1100), .02, 1)], r) * r.uniform(.2, .6))   # 처마·나무에 맞는 굵은 방울
    rumble = filt(noise(n, r), "low", 180) * .35
    return loopify(hiss * .45 + patter * .25 + leaf * .3 + roof * .25 + rumble, .4)


@sfx("amb.weather.rain_light", -27, "날씨", "가랑비: 성긴 빗방울 + 잎사귀 톡톡(반복용 10초)", loop=True, use="비가 오기 시작·그칠 때")
def _(r):
    sec = 10.3; n = int(sec * SR)
    hiss = filt(filt(noise(n, r), "high", 1500), "low", 7000) * .15
    patter = grains(sec, r, 260, lambda r, k: bubble(.03, r.uniform(2200, 5500), 1.3, .003) * r.uniform(.1, .5))
    drips = grains(sec, r, 25, lambda r, k: bubble(.12, r.uniform(700, 1400), 2, .015) * r.uniform(.3, .7))
    return loopify(hiss + patter * .35 + drips * .4, .4)


@sfx("amb.weather.wind", -24, "날씨", "바람: 낮게 웅— 하다가 가끔 휘잉 불어오는 돌풍 + 마른 풀 스치는 소리(반복용 16초)", loop=True, use="고개·능선·바람 부는 날")
def _(r):
    sec = 16.4; n = int(sec * SR); t = T(sec)
    base = filt(noise(n, r), "low", 260) * (.6 + .25 * np.sin(2 * np.pi * t / 16.0))
    # 돌풍 두 번: 바람 '음높이'가 올라갔다 내려감(좁은 대역 잡음의 중심이 움직임)
    gust = np.zeros(n)
    for at, dur in [(2.5, 4.5), (9.5, 5.0)]:
        m = int(dur * SR)
        g = sweep_filt(noise(m, r), "band", 300, 900, 5) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
        g2 = sweep_filt(noise(m, r), "band", 900, 350, 5) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
        place(gust, np.concatenate([g[:m // 2], g2[m // 2:]]), at)
    grass = filt(noise(n, r), "band", 3500, 1) * (.2 + .8 * np.clip(np.abs(gust) * 0, 0, 1))
    grass = grass * (.15 + .85 * filt(np.abs(gust), "low", 3) / (np.abs(filt(np.abs(gust), "low", 3)).max() + 1e-9)) * .2
    return loopify(base + gust * .9 + grass, .5)


@sfx("amb.weather.fog_night", -27, "날씨", "안개 낀 밤 공기: 거의 고요한 낮은 공기 울림 + 먼 개구리·풀벌레 + 가끔 물방울(반복용 15초)", loop=True, use="안개 낀 밤, 원념 짙은 곳 직전의 고요")
def _(r):
    sec = 15.4; n = int(sec * SR); t = T(sec)
    air = filt(noise(n, r), "low", 140) * (.8 + .2 * np.sin(2 * np.pi * t / 7.7))           # 들릴 듯 말 듯한 낮은 공기
    hum = (tone(sec, 55) * .3 + tone(sec, 82.6) * .15) * (.5 + .5 * np.sin(2 * np.pi * t / 15.4 * 2))   # 아주 느리게 숨 쉬는 밑음
    frogs = grains(sec, r, 22, lambda r, k: (tone(.09, r.uniform(380, 520)) * (np.sin(2 * np.pi * 28 * T(.09)) > 0)) * env(int(.09 * SR), .005, .05) * r.uniform(.2, .6),
                   spread=lambda k, r: (k // 3) * 2.0 + (k % 3) * .14 + r.uniform(0, .03))   # 먼 개구리: 세 번씩 '개굴'
    frogs = filt(frogs, "low", 1500)
    insect = np.sin(2 * np.pi * 4100 * t) * (np.sin(2 * np.pi * 24 * t) > .3) * (np.sin(2 * np.pi * .21 * t) > .4) * .02
    drips = grains(sec, r, 7, lambda r, k: bubble(.15, r.uniform(800, 1300), 2, .02) * r.uniform(.2, .5))
    return loopify(reverb(air * .9 + hum * .4 + frogs * .35 + insect + drips * .3, 2.5, .35, tone_hz=2500)[:n], .5)


# ===== 1막 장례 대본(funerals_act1.json, 4a40857) 추가 요청 6종 =====
@sfx("amb.market", -24, "세계", "장터 웅성거림: 여러 사람 말소리가 겹쳐 뜻은 안 들림 + 그릇·엽전 달그락 + 수레 삐걱(반복용 14초)", loop=True, use="장날 장터 배경·장터 장례 시작")
def _(r):
    sec = 14.4; n = int(sec * SR); buf = np.zeros(n)
    # 사람 말소리: 짧은 음절(0.08~0.25초)을 사람마다 다른 음높이·모음으로 이어 붙인다 → 많이 겹치면 '웅성웅성'이 된다
    vowels = [[(750, 4, 1), (1200, 5, .5)], [(450, 4, 1), (1900, 6, .4)], [(320, 4, 1), (2300, 7, .35)], [(550, 4, 1), (900, 5, .6)]]
    for p in range(14):                                       # 14명이 동시에 떠든다
        base = r.uniform(110, 260); at = r.uniform(0, 1.0)
        while at < sec - .3:
            d = r.uniform(.08, .25); m = int(d * SR)
            f0 = np.linspace(base * r.uniform(.9, 1.2), base * r.uniform(.8, 1.05), m)
            y = voice(f0, vowels[r.integers(4)], .2, r, nh=18) * env(m, .015, d * .4, 3, hold=d * .4)
            place(buf, y * r.uniform(.3, 1) * (.4 + .6 * (p % 4 == 0)), at)
            at += d + (r.uniform(.02, .08) if r.random() > .15 else r.uniform(.4, 1.5))   # 말하다 가끔 쉰다
    buf = filt(buf, "low", 2200)                               # 뜻이 들리지 않게 높은 소리(자음)를 깎는다
    clink = grains(sec, r, 26, lambda r, k: modal(.15, [(r.uniform(1800, 3500), .04, 1), (r.uniform(4000, 6000), .02, .4)], r) * r.uniform(.1, .35))
    cart = grains(sec, r, 3, lambda r, k: filt(noise(int(.5 * SR), r), "band", r.uniform(500, 800), 6) * env(int(.5 * SR), .1, .2, 3, hold=.15) * .3)
    floor = filt(noise(n, r), "low", 400) * .08                # 사람 많은 곳의 바닥 웅웅
    return loopify(reverb(buf + clink * .5 + cart + floor, 1.2, .3, tone_hz=3000)[:n], .5)


@sfx("cut.kids.clap", -14, "컷신", "아이 둘의 손뼉 장단: 덩-덩-덕 박자를 흉내 내다 자꾸 어긋남(약 7초)", use="상여 뒤 장터 아이들이 손뼉으로 장단 흉내")
def _(r):
    sec = 7.5; buf = np.zeros(int(sec * SR))
    def clap(r, small):
        m = int(.06 * SR)
        x = noise(m, r) * env(m, .0005, .012, 5)
        f = r.uniform(1300, 1900) if small else r.uniform(1000, 1400)      # 아이 손은 작아서 소리가 높다
        return filt(x, "band", f, 1.2) + filt(x, "band", f * 2.1, 2) * .4
    pattern = [0, .5, .75, 1.25]                              # 한 마디(1.5초): 짝—짝짝—짝 (자진모리 비슷한 3·2 느낌)
    for kid in range(2):
        drift = 0.0; g = 1.0 if kid == 0 else .7
        for bar in range(5):
            for b in pattern:
                drift += r.normal(0, .025) + (.012 if kid == 1 else 0)    # 둘째 아이는 조금씩 늦어진다 = 박자 어긋남
                if r.random() < .08: continue                             # 가끔 한 번 빼먹는다
                place(buf, clap(r, kid == 1) * g * r.uniform(.7, 1), .1 + bar * 1.5 + b + drift)
    return reverb(buf, .9, .25, tone_hz=4500)


@sfx("cut.paper.tear", -15, "컷신", "기둥에 붙은 종이를 떼는 소리: 풀 떨어지며 바스락 찌익— 마지막에 툭 떨어짐(약 1.6초)", use="주막 기둥 종이 떼는 장면")
def _(r):
    sec = 1.6; n = int(sec * SR); buf = np.zeros(n)
    # 한지가 풀에서 떨어질 때 = 아주 짧은 '틱' 알갱이가 점점 촘촘해졌다가 사라짐
    dens = lambda k, r: .05 + 1.0 * (k / 220) ** .7 + r.uniform(0, .01)
    tick = lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1800, 6000), 2.5) * env(int(.004 * SR), .0002, .0012) * r.uniform(.2, 1)
    buf += grains(sec, r, 220, tick, spread=dens)
    rip = sweep_filt(noise(int(.9 * SR), r), "band", 1500, 3200, 1.5) * env(int(.9 * SR), .2, .2, 4, hold=.35)
    place(buf, rip * .35, .1)
    flap = filt(noise(int(.15 * SR), r), "low", 900) * env(int(.15 * SR), .005, .05, 4)   # 종이가 손에서 펄럭
    place(buf, flap * .6, 1.15)
    return reverb(buf, .5, .12)


@sfx("cut.steam.rise", -20, "컷신", "시루에 김 오르는 소리: 솥 물 보글보글 + 시루 틈으로 쉬— 새는 김 + 뚜껑 달그락(약 6초)", use="부엌에서 떡을 다시 찌는 장면")
def _(r):
    sec = 6.0; n = int(sec * SR); t = T(sec)
    boil = grains(sec, r, 260, lambda r, k: bubble(.05, r.uniform(250, 700), 1.8, .012) * r.uniform(.2, 1))
    boil = filt(boil, "low", 1500)                            # 솥 안이라 먹먹하게
    hiss = filt(filt(noise(n, r), "high", 2500), "low", 9000)
    hiss = hiss * curve(sec, [(0, .05), (1.5, .5), (3, .8), (6, .7)]) * (1 + .25 * np.sin(2 * np.pi * .7 * t))   # 김이 점점 세지며 일렁임
    lid = grains(sec, r, 7, lambda r, k: modal(.1, [(r.uniform(900, 1300), .03, 1), (r.uniform(2400, 3000), .02, .5)], r) * .25,
                 spread=lambda k, r: 3.0 + k * .38 + r.uniform(0, .05))   # 김에 밀려 뚜껑이 달그락
    return reverb(boil * .7 + hiss * .25 + lid, .7, .2)


@sfx("cut.brass.tap", -14, "컷신", "놋그릇을 숟가락으로 두드림: 댕— 긴 놋쇠 울림 네 번, 걸음 박자(약 4.5초)", use="문짝 들것 행렬 앞사람이 놋그릇을 침")
def _(r):
    sec = 4.6; buf = np.zeros(int(sec * SR))
    def bowl(r, g):
        f = 640 * r.uniform(.995, 1.005)                       # 놋쇠 주발: 기본음 + 정수배가 아닌 높은 울림들, 가까운 두 음이 맥놀이
        y = modal(1.8, [(f, .9, 1), (f * 1.004, .9, .7), (f * 2.71, .5, .6), (f * 2.716, .5, .4), (f * 5.1, .25, .3), (f * 8.2, .1, .15)], r)
        place(y, filt(noise(int(.006 * SR), r), "high", 3000) * .8, 0)   # 숟가락 끝이 닿는 짧은 '딱'
        return y * g
    for k in range(4):                                         # 걸음에 맞춰 약 0.95초마다
        place(buf, bowl(r, (1.0, .8, .9, .75)[k]), .02 + k * .95 + r.uniform(-.03, .03))
    return reverb(buf, 1.4, .25, tone_hz=6000)


@sfx("cut.ink.grind", -20, "컷신", "벼루에 먹 가는 소리: 물기 있는 사각사각이 원을 그리며 느리게 반복(약 5초)", use="서당 아이들이 먹을 가는 장면")
def _(r):
    sec = 5.2; n = int(sec * SR); t = T(sec)
    circ = np.sin(2 * np.pi * 1.1 * t)                        # 먹을 원으로 돌림(1초에 1.1바퀴)
    speed = .35 + .65 * np.abs(circ)                           # 원의 옆구리에서 빨라지고 끝에서 느려짐
    rub = filt(noise(n, r), "band", 1400, .9) * speed
    grit = grains(sec, r, 700, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(2500, 5500), 3) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .6))
    grit = grit * speed
    wet = filt(noise(n, r), "low", 500) * (.4 + .6 * np.abs(np.sin(2 * np.pi * .55 * t)))    # 물기 머금은 낮은 쓸림
    stone = filt(rub, "band", 320, 4) * .5                     # 벼루 돌의 짧은 울림
    y = (rub * .5 + grit * .35 + wet * .25 + stone) * env(n, .25, .4, 3, hold=sec - .9)
    return reverb(y, .5, .12)


# ===== 2막 장례 대본(funerals_act2.json, 822391c) 추가 요청 9종 =====
def _stone_hit(r, metal=1.0):
    """돌에 쇠가 박히는 '딱': 높은 쇠 울림(짧게) + 돌 몸통 울림 + 부스러기 잡음"""
    m = modal(.25, [(r.uniform(2200, 3200), .03 * metal, metal), (r.uniform(4500, 6000), .015, .5 * metal),
                    (r.uniform(700, 1100), .02, .7), (r.uniform(180, 260), .03, .5)], r)
    k = int(.01 * SR); place(m, filt(noise(k, r), "high", 2000) * env(k, .0002, .003) * .8, 0)
    return m


@sfx("amb.mine", -20, "세계", "광부촌: 갱 안에서 울려 나오는 먼 곡괭이 소리 + 가끔 구르는 수레 + 낮은 바람·물방울(반복용 15초)", loop=True, use="광부촌·갱 입구 배경")
def _(r):
    sec = 15.4; n = int(sec * SR); buf = np.zeros(n)
    at = .3
    while at < sec - .5:                                       # 곡괭이질: 두세 번 치고 쉰다
        for _k in range(r.integers(2, 4)):
            place(buf, _stone_hit(r) * r.uniform(.4, 1), at); at += r.uniform(.7, .95)
        at += r.uniform(1.0, 2.5)
    picks = reverb(filt(buf, "low", 3500), 2.2, .55, tone_hz=2500)[:n]   # 갱(굴)은 울림이 길다
    cart = np.zeros(n)
    for c0 in (4.0, 11.0):                                      # 수레 두 번: 구르는 웅웅 + 레일 이음매 덜컹
        m = int(3.0 * SR)
        roll = filt(noise(m, r), "low", 220) * np.sin(np.pi * np.linspace(0, 1, m)) ** 1.5
        place(cart, roll * .8, c0)
        for j in range(7):
            place(cart, modal(.12, [(r.uniform(300, 420), .04, 1), (r.uniform(900, 1200), .02, .4)], r) * .35 * np.sin(np.pi * (j + .5) / 7), c0 + .2 + j * .38)
    cart = reverb(filt(cart, "low", 1500), 1.8, .5, tone_hz=1500)[:n]
    wind = filt(noise(n, r), "low", 180) * .35
    drips = grains(sec, r, 8, lambda r, k: bubble(.15, r.uniform(700, 1200), 2, .02) * .3)
    return loopify(picks * .8 + cart * .7 + wind + drips, .5)


@sfx("cut.pour.liquor", -18, "컷신", "잔에 술 따르기: 쪼르륵 차오르며 소리가 높아짐 × 세 잔, 잠시 쉬고 한 잔 더(약 8초)", use="무덤 앞에 술을 붓는 장면")
def _(r):
    sec = 8.2; buf = np.zeros(int(sec * SR))
    def pour(r, d):
        m = int(d * SR); tt = np.arange(m) / SR
        stream = filt(noise(m, r), "band", 2200, 1.2) * (.6 + .4 * np.sin(2 * np.pi * 9 * tt + r.uniform(0, 6)))   # 물줄기 쉬—
        fill = sweep_filt(noise(m, r), "band", 600, 1500, 8)    # 잔이 차면 공기 기둥이 짧아져 울림이 높아진다
        glug = grains(d, r, int(d * 14), lambda r, k: bubble(.04, r.uniform(500, 1100), 1.6, .01) * r.uniform(.2, .6))
        return (stream * .25 + fill * .9 + glug * .3) * env(m, .05, .08, 4, hold=d - .15)
    clink = lambda r: modal(.4, [(2650, .12, 1), (4100, .07, .4), (6900, .03, .2)], r)   # 병 주둥이가 사기잔에 닿는 딩
    at = .1
    for k, d in enumerate((1.2, 1.1, 1.2)):
        place(buf, clink(r) * .35, at); place(buf, pour(r, d), at + .05); at += d + .5
    at += .9                                                    # 다 부은 뒤 잠깐 멈췄다가 — 한 잔 더(할아버지 몫)
    place(buf, clink(r) * .25, at); place(buf, pour(r, 1.4) * .9, at + .08)
    return reverb(buf, .8, .2)


@sfx("cut.hoe.dig", -15, "컷신", "호미로 흙 파기: 툭 박히고 슥 긁어 당김 × 네 번, 흙 알갱이 흩어짐(약 4.5초)", use="바위틈 약초 캐는 장면")
def _(r):
    sec = 4.6; buf = np.zeros(int(sec * SR))
    for k in range(4):
        at = .1 + k * 1.05 + r.uniform(-.05, .05)
        m = int(.12 * SR)
        thud = filt(noise(m, r), "low", 700) * env(m, .001, .03, 4) + tone(.12, 150, 90) * env(m, .001, .04, 4) * .6
        place(buf, thud, at)
        if k == 2: place(buf, _stone_hit(r, .4) * .35, at + .005)          # 한 번은 돌에 닿아 쨍
        m2 = int(.35 * SR)
        scrape = filt(noise(m2, r), "band", 1600, 1.0) * env(m2, .05, .1, 4, hold=.15)
        place(buf, scrape * .45, at + .15)
        soil = grains(.4, r, 30, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(1500, 5000), 2) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .5))
        place(buf, soil * .6, at + .3)
    return reverb(buf, .6, .12)


@sfx("cut.chisel.tap", -14, "컷신", "정으로 돌에 글자 새기기: 망치가 정을 때리는 쨍 + 돌 부스러기, 일정한 박자 열 번(약 5초)", use="성돌에 스승 이름을 새기는 장면")
def _(r):
    sec = 5.2; buf = np.zeros(int(sec * SR))
    for k in range(10):
        at = .1 + k * .48 + r.uniform(-.02, .02)
        if k == 5: at += .25                                     # 한 획 끝나고 정을 옮겨 대는 짧은 쉼
        hit = modal(.5, [(3150 * r.uniform(.99, 1.01), .12, 1), (5240, .06, .5), (1420, .05, .5), (7600, .02, .2)], r)   # 쇠정 울림
        place(buf, hit * r.uniform(.8, 1), at)
        place(buf, _stone_hit(r, .2) * .5, at)
        chips = grains(.15, r, 8, lambda r, k: filt(noise(int(.003 * SR), r), "high", 3500) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .4))
        place(buf, chips, at + .01)
    return reverb(buf, .9, .2)


@sfx("cut.sickle.cut", -13, "컷신", "낫으로 풀 베기: 숫돌에 한 번 쓱 갈고, 쉭— 서걱 네 번(약 5.5초)", use="무덤 벌초 장면")
def _(r):
    sec = 5.6; buf = np.zeros(int(sec * SR))
    m = int(.8 * SR)                                              # 숫돌질: 쇠가 돌에 미끄러지는 쓱—
    hone = sweep_filt(noise(m, r), "band", 3500, 5500, 4) * env(m, .1, .2, 4, hold=.4) + tone(.8, 4200) * env(m, .1, .2, 4, hold=.4) * .05
    place(buf, hone * .5, .05)
    for k in range(4):
        at = 1.25 + k * 1.0 + r.uniform(-.05, .05)
        m = int(.3 * SR)
        swish = sweep_filt(noise(m, r), "band", 900, 2600, 2) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2   # 낫이 바람을 가름
        place(buf, swish * .35, at)
        cut = grains(.12, r, 35, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(2000, 6000), 2) * env(int(.004 * SR), .0002, .0015) * r.uniform(.2, 1))   # 풀줄기 끊어짐 서걱
        place(buf, cut, at + .2)
        place(buf, filt(noise(int(.2 * SR), r), "low", 800) * env(int(.2 * SR), .01, .06, 4) * .3, at + .3)   # 베인 풀이 쓰러짐
    return reverb(buf, .5, .1)


@sfx("cut.tag.unhook", -16, "컷신", "고리에서 나무 목패 떼기: 쇠고리 끽 + 패가 옆 패에 딱 부딪힘 + 손에 쥠(약 1.4초)", use="동료가 순돌의 목패를 떼는 장면")
def _(r):
    buf = np.zeros(int(1.5 * SR))
    m = int(.25 * SR)
    creak = sweep_filt(noise(m, r), "band", 1800, 2600, 10) * env(m, .03, .08, 4, hold=.1)   # 녹슨 쇠고리 비빔
    place(buf, creak * .5, .05)
    wood = lambda r, f: modal(.15, [(f, .03, 1), (f * 2.4, .015, .5), (f * 4.1, .008, .2)], r)   # 마른 나무패 딱
    place(buf, wood(r, 900) * .9, .3); place(buf, wood(r, 1150) * .5, .38); place(buf, wood(r, 1000) * .3, .44)   # 옆 패들이 흔들려 따라 부딪힘
    place(buf, modal(.3, [(3300, .08, 1), (5200, .04, .4)], r) * .15, .3)   # 고리 짤랑
    grab = filt(noise(int(.12 * SR), r), "low", 1200) * env(int(.12 * SR), .005, .04, 4) * .4   # 손에 쥐는 소리
    place(buf, grab, .85)
    return reverb(buf, .6, .15)


@sfx("cut.coal.sort", -18, "컷신", "평상에서 석탄 고르기: 덩이끼리 달그락 + 나무판에 쓸어 밀기 + 바구니에 툭(약 5초)", use="딸이 어머니 자리에서 석탄을 고르는 장면")
def _(r):
    sec = 5.2; n = int(sec * SR); buf = np.zeros(n)
    lump = lambda r, k: modal(.06, [(r.uniform(1800, 3800), .012, 1), (r.uniform(4500, 7000), .006, .5)], r) * r.uniform(.15, .8)   # 석탄은 가볍고 잘 깨지는 유리 같은 소리
    for g0 in (.2, 1.6, 3.1):                                    # 한 줌씩 세 번
        place(buf, grains(.8, r, 14, lump), g0)
        m = int(.5 * SR)
        place(buf, filt(noise(m, r), "band", 1100, .8) * env(m, .05, .15, 4, hold=.2) * .2, g0 + .4)   # 판 위에 쓸어 밀기
        place(buf, filt(noise(int(.1 * SR), r), "low", 600) * env(int(.1 * SR), .002, .03, 4) * .5 + modal(.1, [(420, .03, .4)], r), g0 + 1.1)   # 바구니에 툭
    return reverb(buf, .5, .12)


@sfx("cut.brush.write", -22, "컷신", "붓으로 종이에 쓰기: 붓끝이 닿는 톡 + 사악— 획 긋는 소리 여섯 획, 중간에 한 번 멈춤(약 5초)", use="외상 장부에 이름을 적어 넣는 장면")
def _(r):
    sec = 5.0; buf = np.zeros(int(sec * SR))
    at = .15
    for k in range(6):
        d = r.uniform(.25, .55); m = int(d * SR)
        stroke = filt(filt(noise(m, r), "high", 1800), "low", 6500) * env(m, .02, .08, 4, hold=d - .12) * (1 + .3 * np.sin(np.linspace(0, 3, m)))
        place(buf, filt(noise(int(.01 * SR), r), "band", 1500, 1) * env(int(.01 * SR), .0005, .004) * .5, at)   # 붓끝 닿음
        place(buf, stroke * .4, at + .01)
        at += d + r.uniform(.12, .3)
        if k == 3: at += 1.0                                    # 모르는 번호 앞에서 붓이 멈춘다
    return reverb(buf, .4, .08)


@sfx("cut.mule.hoof", -15, "컷신", "노새 발굽: 흙길 위 네 발 걸음 따각따각, 갱 입구 앞에서 멈춤(약 6초)", use="풀려난 노새가 상여를 따라가는 장면")
def _(r):
    sec = 6.2; buf = np.zeros(int(sec * SR))
    def clop(r):
        m = modal(.12, [(r.uniform(380, 520), .025, 1), (r.uniform(1100, 1500), .012, .6), (r.uniform(2400, 3000), .006, .3)], r)   # 단단한 발굽
        k = int(.05 * SR); place(m, filt(noise(k, r), "low", 1500) * env(k, .001, .015, 4) * .7, 0)   # 흙이 눌리는 퍽
        return m
    stride = .62                                                # 걸음: 한 주기에 네 발(좌뒤-좌앞-우뒤-우앞)
    for s in range(8):
        for j, off in enumerate((0, .16, .31, .47)):
            slow = 1 + max(0, s - 5) * .25                       # 마지막 두 걸음은 느려지며 멈춘다
            place(buf, clop(r) * r.uniform(.6, 1) * (1 - .1 * (j % 2)), .1 + s * stride * slow + off * slow + r.uniform(-.012, .012))
    place(buf, filt(noise(int(.4 * SR), r), "low", 300) * env(int(.4 * SR), .05, .15, 4) * .3, 5.4)   # 멈춰 서서 코로 푸르르
    return reverb(buf, .7, .15)


# ===== 2막 지역 환경음 (③ 붉은재 싸움터 · ④ 쇳골 광산, 2026-10-25) =====
def _flutter(sec, r, gust, rate=(7, 16), bright=2200):
    """천(깃발·천막) 펄럭임: 잡음을 빠르게 '툭툭' 끊어 주는 맥박(초당 rate번)으로 곱한다.
    gust(0~1 곡선)가 셀수록 더 빠르고 크게 펄럭이고, 센 순간마다 '탁' 하고 천이 튕긴다"""
    n = int(sec * SR)
    hz = rate[0] + (rate[1] - rate[0]) * gust
    ph = np.cumsum(hz) / SR
    pulse = (0.5 + 0.5 * np.sin(2 * np.pi * ph)) ** 6                  # 뾰족한 맥박 = 천이 펄럭 접혔다 펴짐
    cloth = filt(filt(noise(n, r), "low", bright), "high", 150) * pulse * gust
    snaps = np.zeros(n)
    for i in np.where(np.diff((gust > .75).astype(int)) == 1)[0]:     # 바람이 확 셀 때 '탁'
        k = int(.03 * SR); place(snaps, filt(noise(k, r), "low", 3000) * env(k, .001, .008, 4), i / SR)
    return cloth + snaps * .8


def _gust_curve(sec, r, n_gust=3, base=.25):
    """느린 돌풍 곡선(0~1): 기본 바람 위에 n번 확 불었다 잦아듦"""
    t = T(sec); g = np.full(len(t), base)
    for k in range(n_gust):
        c = (k + .5) * sec / n_gust + r.uniform(-1, 1); w = r.uniform(1.2, 2.5)
        g += (1 - base) * np.exp(-((t - c) / w) ** 2) * r.uniform(.7, 1)
    g += .08 * filt(r.standard_normal(len(t)), "low", 2) / .02
    return np.clip(g, 0, 1)


@sfx("amb.fortress.flag", -22, "세계", "무너진 산성 위: 높은 곳의 센 바람 + 찢어진 깃발이 펄럭이다 탁 튕김(반복용 16초)", loop=True, use="③ 무너진 산성·산성 아랫마을 높은 곳")
def _(r):
    sec = 16.4; n = int(sec * SR)
    g = _gust_curve(sec, r, 3, .3)
    wind = sweep_filt(noise(n, r), "band", 350, 500, 1.2) * (.4 + .6 * g) + filt(noise(n, r), "low", 200) * .5
    flag = _flutter(sec, r, g)
    rope = grains(sec, r, 6, lambda r, k: sweep_filt(noise(int(.35 * SR), r), "band", 900, 1300, 12) * env(int(.35 * SR), .05, .1, 4, hold=.15) * .3)   # 깃대 밧줄 삐걱
    return loopify(wind * .7 + flag * .55 + rope, .5)


@sfx("amb.arrowvalley", -24, "세계", "화살골: 바위틈을 지나는 가는 휘파람 바람 + 녹슨 화살촉이 바람에 떨리는 아주 작은 쇳소리(반복용 15초)", loop=True, use="③ 화살골 골짜기")
def _(r):
    sec = 15.4; n = int(sec * SR); t = T(sec)
    g = _gust_curve(sec, r, 2, .35)
    base = filt(noise(n, r), "low", 300) * .6
    whistle = np.zeros(n)
    for f, a in ((620, 1), (930, .5), (1480, .3)):                    # 바위틈 = 좁은 구멍 → 높이가 정해진 휘파람
        whistle += sweep_filt(noise(n, r), "band", f * .97, f * 1.03, 40) * a
    whistle *= np.clip(g - .3, 0, 1) ** 1.5 * 2.5
    tinks = grains(sec, r, 9, lambda r, k: modal(.4, [(r.uniform(2800, 3600), .15, 1), (r.uniform(5000, 6000), .08, .4)], r) * r.uniform(.05, .15))
    return loopify(reverb(base + whistle * .5 + tinks, 1.6, .35, tone_hz=4000)[:n], .5)


@sfx("amb.camp", -18, "세계", "빈 군막 터: 기둥만 남은 평지, 너덜한 천 조각 펄럭임 + 밧줄 삐걱 + 먼 까마귀(반복용 14초)", loop=True, use="③ 군막 터")
def _(r):
    sec = 14.4; n = int(sec * SR)
    g = _gust_curve(sec, r, 2, .2)
    wind = filt(noise(n, r), "low", 400) * (.5 + .5 * g)
    rag = _flutter(sec, r, g * .8, rate=(10, 22), bright=3500) * .5           # 작은 천 조각은 더 빠르고 가볍게 떤다
    creak = grains(sec, r, 5, lambda r, k: sweep_filt(noise(int(.5 * SR), r), "band", 600, 900, 15) * env(int(.5 * SR), .05, .15, 4, hold=.2) * .35)
    crow = np.zeros(n)
    for at in (3.0, 3.45, 10.2):                                      # 까악— (목소리 합성, 멀리)
        d = .35; f0 = curve(d, [(0, 520), (.08, 600), (d, 480)])
        place(crow, voice(f0, [(1200, 3, 1), (2400, 4, .5)], .5, r, nh=15) * env(int(d * SR), .02, .12, 3, hold=.1), at)
    crow = reverb(filt(crow, "low", 2200), 2.0, .6, tone_hz=2000)[:n]
    return loopify(wind * .8 + rag + creak + crow * .5, .5)


@sfx("amb.mine.wind", -22, "세계", "갱 입구 바람: 굴속으로 빨려 드는 낮은 웅— 공명(관 울림) + 입구 판자 덜컹(반복용 16초)", loop=True, use="④ 광부촌 갱 입구·큰 갱도 입구")
def _(r):
    sec = 16.4; n = int(sec * SR); t = T(sec)
    g = _gust_curve(sec, r, 3, .4)
    tube = np.zeros(n)
    for k, a in ((1, 1), (2, .55), (3, .3), (5, .12)):              # 긴 굴 = 큰 관. 관 길이로 정해진 낮은 음과 그 배음이 운다
        f = 72 * k * (1 + .01 * np.sin(2 * np.pi * t / 9))
        tube += sweep_filt(noise(n, r), "band", f[0], f[-1], 25) * a
    tube *= .4 + .6 * g
    hiss = filt(filt(noise(n, r), "high", 600), "low", 3000) * g * .25
    boards = grains(sec, r, 5, lambda r, k: modal(.2, [(r.uniform(180, 260), .05, 1), (r.uniform(500, 700), .03, .5)], r) * .5)   # 입구 판자문이 바람에 덜컹
    return loopify(reverb(tube * .9 + hiss + boards, 1.5, .3, tone_hz=1500)[:n], .5)


@sfx("amb.mine.shaft", -24, "세계", "큰 갱도 안: 끝없는 어둠의 울림, 물방울 똑똑 + 버팀목 삐걱 + 멀리 돌 구르는 소리 + 석탄 가루 사락(반복용 15초)", loop=True, use="④ 큰 갱도·무너진 막장")
def _(r):
    sec = 15.4; n = int(sec * SR)
    room = filt(noise(n, r), "low", 120) * .4
    drips = grains(sec, r, 18, lambda r, k: bubble(.2, r.uniform(900, 1600), 2.2, .02) * r.uniform(.3, 1))
    timber = grains(sec, r, 4, lambda r, k: sweep_filt(noise(int(.8 * SR), r), "band", 300, 420, 18) * env(int(.8 * SR), .1, .25, 4, hold=.3) * .6)   # 무거운 버팀목이 짓눌려 끄응
    rocks = np.zeros(n)
    for at in (6.0, 12.5):
        place(rocks, grains(1.2, r, 12, lambda r, k: modal(.15, [(r.uniform(400, 900), .04, 1), (r.uniform(1500, 2500), .02, .3)], r) * (1 - k / 14) * .5), at)
    dust = grains(sec, r, 300, lambda r, k: filt(noise(int(.002 * SR), r), "high", 4000) * r.uniform(.02, .1))
    y = room + drips * .4 + timber + filt(rocks, "low", 2000) * .7 + dust
    return loopify(reverb(y, 3.0, .55, tone_hz=2200)[:n], .6)


# ===== 신종 혼 3종 공격 예고 (넋두리 wail · 잔넋 mote · 묻힌 혼 buried, 아트 SOUL-TYPES.md) =====
# 예고음은 '피할 시간'을 귀로 알려 주는 소리라 천도 먹먹함을 무시하고(bypass_cast) 선딜 길이에 맞춘다.
@sfx("sfx.enemy.wail.telegraph", -12, "전투", "넋두리 예고(0.7초): 흐느끼는 숨이 올라가며 원념 구슬이 웅— 차오름, 끝에 짧게 번쩍", bypass_cast=True, use="넋두리가 원념을 던지기 전 선딜 0.7초")
def _(r):
    sec = .75; n = int(sec * SR)
    f0 = curve(sec, [(0, 210), (.5, 300), (.7, 340)])
    moan = voice(f0, [(700, 4, 1), (1100, 5, .5), (2600, 7, .2)], .35, r, nh=20) * curve(sec, [(0, 0), (.15, .5), (.62, 1), (.7, .2), (.75, 0)])
    hum = tone(sec, 110, 220) * curve(sec, [(0, 0), (.65, 1), (.72, 0)]) + tone(sec, 331, 662) * curve(sec, [(0, 0), (.65, .4), (.72, 0)])   # 구슬이 차오르며 음이 오름
    flash = filt(noise(int(.05 * SR), r), "high", 3000) * env(int(.05 * SR), .001, .015, 4)
    buf = moan * .6 + hum * .4; place(buf, flash * .7, .66)
    return reverb(buf, .5, .15)


@sfx("sfx.enemy.wail.throw", -12, "전투", "넋두리 투척: 원념 구슬이 휙 날아가며 웅웅 떨리는 소리(약 0.6초)", bypass_cast=True, use="넋두리 투척 순간(탄 발사)")
def _(r):
    sec = .6; n = int(sec * SR); tt = T(sec)
    whoosh = sweep_filt(noise(n, r), "band", 1800, 600, 2) * env(n, .01, .2, 4, hold=.1)
    wobble = tone(sec, 240, 180) * (.6 + .4 * np.sin(2 * np.pi * 18 * tt)) * env(n, .005, .3, 3)
    return whoosh * .7 + wobble * .4


@sfx("sfx.enemy.mote.telegraph", -16, "전투", "잔넋 예고(0.3초): 작은 혼이 찍— 하고 몸을 움츠림. 여럿이 겹쳐도 시끄럽지 않게 짧고 높게", bypass_cast=True, use="잔넋 무리 선딜 0.3~0.4초(동시에 여러 마리면 최대 3개만 재생 권장)")
def _(r):
    sec = .32; n = int(sec * SR)
    f0 = curve(sec, [(0, 900), (.12, 1400), (.25, 1250)])
    chirp = voice(f0, [(2200, 5, 1), (3600, 6, .4)], .3, r, nh=8) * env(n, .01, .08, 4, hold=.12)
    shiver = filt(noise(n, r), "band", 5000, 3) * (np.sin(2 * np.pi * 40 * T(sec)) > 0) * env(n, .02, .1, 4, hold=.1) * .3   # 몸을 떠는 바스락
    return reverb(chirp * .6 + shiver, .3, .1)


@sfx("sfx.enemy.buried.telegraph", -15, "전투", "묻힌 혼 예고(0.73초): 땅속에서 우르릉 올라오며 흙이 갈라지는 소리 — 커지는 쪽으로 피하라", bypass_cast=True, use="묻힌 혼이 솟기 전 선딜 0.73초(땅 갈라짐 예고와 같이)")
def _(r):
    sec = .8; n = int(sec * SR)
    rumble = sweep_filt(noise(n, r), "low", 80, 260) * curve(sec, [(0, 0), (.6, 1), (.73, 1), (.8, 0)])
    thump = tone(sec, 45, 70) * curve(sec, [(0, 0), (.7, .8), (.8, 0)])
    crack = grains(sec, r, 40, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(800, 3000), 2) * env(int(.004 * SR), .0002, .0015) * r.uniform(.2, 1),
                   spread=lambda k, r: .2 + .5 * (k / 40) ** .5 + r.uniform(0, .02))   # 끝으로 갈수록 촘촘히 갈라짐
    return rumble * .9 + thump * .5 + crack * .5


@sfx("sfx.enemy.buried.burst", -9, "전투", "묻힌 혼이 솟구침: 흙이 퍽 터지며 손이 움켜쥠 + 흙 부스러기 떨어짐(약 1초)", bypass_cast=True, use="묻힌 혼 Attack 적중 프레임(솟구침)")
def _(r):
    sec = 1.0; n = int(sec * SR); buf = np.zeros(n)
    m = int(.25 * SR)
    place(buf, filt(noise(m, r), "low", 900) * env(m, .002, .06, 4) + tone(.25, 90, 50) * env(m, .002, .08, 4) * .8, 0)
    place(buf, modal(.15, [(r.uniform(300, 400), .04, 1), (r.uniform(800, 1000), .02, .4)], r) * .4, .05)   # 뼈 같은 손이 움켜쥠
    buf += grains(sec, r, 60, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(1000, 4000), 2) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .5),
                  spread=lambda k, r: .1 + r.exponential(.2))
    return reverb(buf, .5, .12)


# ===== 2막 보스 전용 소리 (서사 SCENARIO-ACT2: B-05 기수 대돌 · B-06 이름 없는 장수 · B-07 갱도 반장 칠성 · B-08 장부꾼 염씨) =====
# 대사는 서사 원칙상 글(말풍선)로 나오므로, 소리는 '말뜻 없는 목소리 + 신호 소리'로만 만든다.
def _shout(r, sec, f_hi, f_lo, vowel="a", rough=.35):
    """말뜻 없는 외침(목소리 합성): f_hi에서 시작해 f_lo로 떨어지는 사내 목소리"""
    f0 = curve(sec, [(0, f_lo * 1.1), (sec * .15, f_hi), (sec * .7, f_hi * .95), (sec, f_lo)])
    f0 = f0 * (1 + .015 * np.sin(2 * np.pi * 6 * T(sec)))
    form = {"a": [(750, 4, 1), (1200, 5, .55), (2600, 7, .25)], "o": [(500, 4, 1), (850, 5, .6), (2500, 8, .15)]}[vowel]
    return voice(f0, form, rough, r, nh=30) * env(int(sec * SR), .03, sec * .3, 3, hold=sec * .55)


@sfx("sfx.boss.daedol.call", -11, "보스", "기수 대돌이 동료를 부름: 깃발 휘두르며 길게 외치는 소리(말뜻 없음) + 땅에서 병사 혼이 일어나는 갑옷 철컥(약 2초)", use="B-05: 이름을 불러 병사 혼을 일으킬 때")
def _(r):
    sec = 2.2; buf = np.zeros(int(sec * SR))
    place(buf, _shout(r, 1.0, 190, 140, "o") * .8, 0)
    m = int(.6 * SR); place(buf, sweep_filt(noise(m, r), "band", 500, 1500, 1.5) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2 * .4, .1)   # 깃발이 크게 휙
    rise = sweep_filt(noise(int(1.0 * SR), r), "low", 100, 400) * env(int(1.0 * SR), .4, .3, 4) * .6
    place(buf, rise, 1.0)
    for k in range(5):                                                   # 일어서는 병사들의 낡은 갑옷 철컥
        place(buf, modal(.2, [(r.uniform(1800, 2600), .04, 1), (r.uniform(3500, 4500), .02, .5), (r.uniform(500, 700), .03, .4)], r) * .35, 1.3 + k * .12 + r.uniform(0, .05))
    return reverb(buf, 1.6, .35)


@sfx("sfx.boss.daedol.number", -10, "보스", "번호로 부름: 이름 대신 짧게 끊어 외치는 거친 소리 + 징이 둔탁하게 '퉁' — 더 사나운 병사가 일어난다는 경고(약 1.4초)", use="B-05: 이름을 잊어 번호로 부를 때(맺힘 +30% 병사)")
def _(r):
    sec = 1.5; buf = np.zeros(int(sec * SR))
    place(buf, _shout(r, .35, 240, 200, "a", .6) * .8, 0); place(buf, _shout(r, .3, 230, 180, "a", .6) * .7, .4)
    gong = modal(1.2, [(98, .8, 1), (196.5, .5, .6), (277, .35, .5), (412, .2, .3)], r)   # 둔탁하게 막힌 징
    place(buf, filt(gong, "low", 1200) * .9, .4)
    return reverb(buf, 1.4, .3)


@sfx("sfx.boss.general.command", -10, "보스", "이름 없는 장수의 호령: 큰 북 두 번 '둥둥' + 짧은 외침 — 대형이 바뀐다는 신호(약 1.3초)", use="B-06: 진법 호령(번호)으로 병사 대형을 바꾸기 직전. 이 소리를 듣고 대형을 읽는다")
def _(r):
    sec = 1.4; buf = np.zeros(int(sec * SR))
    drum = lambda r: tone(.5, 80, 55) * env(int(.5 * SR), .002, .15, 4) + filt(noise(int(.5 * SR), r), "low", 400) * env(int(.5 * SR), .001, .04, 4) * .6
    place(buf, drum(r), 0); place(buf, drum(r) * .9, .28)
    place(buf, _shout(r, .5, 170, 130, "o", .5) * .7, .6)
    return reverb(buf, 1.6, .3)


@sfx("sfx.boss.general.formation", -12, "보스", "대형이 바뀜: 병사 혼 여럿이 한꺼번에 발을 구르고 창끝이 철컥 맞춰짐(약 1.2초)", use="B-06: 대형 이동이 끝나는 순간(빈틈이 생긴 쪽으로 파고들 때)")
def _(r):
    sec = 1.3; buf = np.zeros(int(sec * SR))
    for beat in (0, .45):
        for v in range(8):                                               # 여덟 명이 거의 같이 = 쿵
            m = int(.15 * SR)
            place(buf, filt(noise(m, r), "low", 500) * env(m, .002, .04, 4) * .4 + tone(.15, 70) * env(m, .002, .05, 4) * .2, beat + r.uniform(0, .03))
    for v in range(6):
        place(buf, modal(.25, [(r.uniform(2000, 3000), .05, 1), (r.uniform(4000, 5500), .03, .4)], r) * .25, .9 + r.uniform(0, .04))
    return reverb(buf, 1.2, .25)


@sfx("sfx.boss.chilsung.count", -12, "보스", "갱도 반장 칠성이 셈: 곡괭이 자루로 레일을 '깡' 한 번 + 낮게 웅얼거리는 셈(말뜻 없음). 광부 혼 하나가 출구로 걸어 나갈 때마다(약 0.9초)", use="B-07: 광부 혼을 한 명씩 내보낼 때마다 한 번")
def _(r):
    sec = 1.0; buf = np.zeros(int(sec * SR))
    rail = modal(.8, [(1180, .3, 1), (1730, .2, .6), (2950, .12, .4), (4400, .05, .2)], r)   # 쇠 레일
    place(buf, rail * .7, 0)
    f0 = curve(.5, [(0, 120), (.2, 135), (.5, 110)])
    place(buf, voice(f0, [(500, 4, 1), (900, 5, .5)], .3, r, nh=25) * env(int(.5 * SR), .03, .15, 3, hold=.25) * .5, .25)
    return reverb(filt(buf, "low", 5000), 2.0, .45, tone_hz=2500)          # 막장(굴) 울림


@sfx("sfx.boss.chilsung.rage", -9, "보스", "셈이 틀려 광폭해짐: 막장이 우르릉 흔들리며 돌가루가 쏟아지고, 반장이 짐승처럼 울부짖음(약 2.2초)", use="B-07: 광부 혼을 파혼해 숫자가 틀렸을 때(맺힘 회복)")
def _(r):
    sec = 2.3; n = int(sec * SR); buf = np.zeros(n)
    quake = filt(noise(n, r), "low", 150) * curve(sec, [(0, 0), (.3, 1), (1.6, .8), (2.3, 0)]) + tone(sec, 38, 30) * curve(sec, [(0, 0), (.3, .6), (2.3, 0)])
    roar = _shout(r, 1.2, 160, 90, "a", .9)
    rocks = grains(sec, r, 40, lambda r, k: modal(.12, [(r.uniform(300, 900), .03, 1)], r) * r.uniform(.2, .7), t0=.4)
    dust = filt(noise(n, r), "high", 3000) * curve(sec, [(0, 0), (.5, .3), (2.3, 0)])
    buf += quake * .8 + rocks * .4 + dust * .15; place(buf, roar * .7, .25)
    return reverb(buf, 2.0, .4, tone_hz=2500)


@sfx("sfx.boss.yeom.throw", -12, "보스", "장부꾼 염씨가 숫자를 날림: 장부 낱장이 촤르륵 넘어가며 종이가 휙휙 날아감(약 1초)", use="B-08: 숫자 지뢰를 날리는 순간")
def _(r):
    sec = 1.1; buf = np.zeros(int(sec * SR))
    flip = grains(.4, r, 14, lambda r, k: filt(noise(int(.02 * SR), r), "band", r.uniform(2000, 4500), 2) * env(int(.02 * SR), .001, .006, 4) * r.uniform(.4, 1),
                  spread=lambda k, r: k * .025)                          # 장부가 촤르륵
    place(buf, flip, 0)
    for k in range(4):
        m = int(.3 * SR)
        place(buf, sweep_filt(noise(m, r), "band", 2500, 900, 2.5) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2 * .45, .35 + k * .12)
    return reverb(buf, .6, .15)


@sfx("sfx.boss.yeom.land", -11, "보스", "숫자가 바닥에 박힘: 도장을 찍듯 '탁' + 낮게 웅 울리는 경고(이 칸 밟지 마라)(약 0.7초)", bypass_cast=True, use="B-08: 숫자 지뢰가 바닥에 꽂힐 때(위치 예고)")
def _(r):
    sec = .75; buf = np.zeros(int(sec * SR))
    stamp = modal(.2, [(320, .05, 1), (710, .03, .4)], r) * .6
    place(stamp, filt(noise(int(.08 * SR), r), "low", 1500) * env(int(.08 * SR), .001, .02, 4), 0)   # 도장 찍는 탁
    place(buf, stamp, 0)
    warn = tone(.6, 147) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * T(.6))) * env(int(.6 * SR), .05, .2, 4, hold=.2)   # 낮은 박동 경고
    place(buf, warn * .4, .08)
    return reverb(buf, .6, .15)


@sfx("sfx.boss.yeom.burst", -9, "보스", "숫자를 밟음: 먹물이 퍽 터지며 붓 자국이 흩어짐(약 0.9초)", use="B-08: 플레이어가 숫자 칸을 밟아 피해를 입을 때")
def _(r):
    sec = .9; n = int(sec * SR); buf = np.zeros(n)
    m = int(.3 * SR)
    place(buf, filt(noise(m, r), "low", 1200) * env(m, .002, .07, 4) + tone(.3, 110, 60) * env(m, .002, .08, 4) * .7, 0)
    splat = grains(.6, r, 30, lambda r, k: bubble(.04, r.uniform(300, 900), 1.5, .01) * r.uniform(.2, .6), spread=lambda k, r: .03 + r.exponential(.12))   # 먹물 튐(끈적한 물방울)
    buf += np.concatenate([splat, np.zeros(n - len(splat))]) * .5
    m2 = int(.4 * SR); place(buf, sweep_filt(noise(m2, r), "band", 3000, 1200, 2) * env(m2, .01, .12, 4) * .3, .05)   # 붓 획이 흩어짐
    return reverb(buf, .6, .15)


@sfx("sfx.boss.yeom.backpage", -16, "보스", "장부 뒷장(이름이 적힌 종이)을 밟음: 종이가 부드럽게 사락 + 맑은 방울 한 번 — 해롭지 않고 맺힘이 깎인다(약 1.2초)", use="B-08: 뒷장 종이를 밟았을 때(이로운 쪽)")
def _(r):
    sec = 1.3; buf = np.zeros(int(sec * SR))
    m = int(.4 * SR); place(buf, filt(filt(noise(m, r), "high", 1500), "low", 6000) * env(m, .03, .12, 4, hold=.1) * .4, 0)
    place(buf, modal(1.1, [(1568, .5, 1), (2352, .35, .5), (3920, .15, .2)], r) * .5, .12)   # G6 맑은 방울
    return reverb(buf, 1.2, .3)


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
    # 발소리 표: 코드의 땅 재질 층 번호(0 흙·1 풀·2 자갈·3 논·4 낙엽) → 파일 이름 앞부분. 물속(wet)이면 water
    manifest["footsteps"] = {"_설명": "Sfx.PlayStep: 가장 큰 재질 층을 골라 '<prefix>_<1~variants 무작위>' 재생. 직전과 같은 번호는 피하기. 높낮이 ±4% 무작위만, 재질별 피치·크기 보정은 파일에 이미 들어 있음",
                             "layers": ["sfx_step_dirt", "sfx_step_grass", "sfx_step_gravel", "sfx_step_paddy", "sfx_step_leaves"],
                             "wet": "sfx_step_water", "variants": STEP_VARIANTS}
    with open(os.path.join(ROOT, "data/sfx_files.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(len(REG), "개")


if __name__ == "__main__":
    main()
