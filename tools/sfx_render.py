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


# ===== UI 소리: 한지·먹 분위기(2026-10-25 정비) =====
# 왜 이렇게: UI 소리는 한 판에 수백 번 듣는다. 그래서 (1) 짧고(대부분 0.1~0.5초) (2) 귀를 찌르는 높은 쇳소리 없이
# 종이·붓·나무·도장처럼 '손에 닿는 재질'로 만들고 (3) 자주 나는 것일수록 작게 둔다(버튼 -21, 들은 말 -21(부드러운 결이라 실제로는 더 작게 들림), 자동 저장 -31).
# 큰일(품계 오름)만 크고 길다 → 귀가 '이건 중요하다'를 바로 안다.
def _paper(r, sec, lo=1500, hi=6500, a=.004, hold=0.0):
    """한지 스침: 높은 쪽만 남긴 잡음(종이의 사각거림). lo~hi 사이만 통과"""
    m = int(sec * SR)
    return filt(filt(noise(m, r), "high", lo), "low", hi) * env(m, a, sec * .35, 4, hold=hold)


def _crinkle(r, sec, count, f=(2000, 6000), amp=(.2, 1)):
    """종이 구김: 아주 짧은 '틱' 알갱이를 흩뿌림(cut.paper.tear 와 같은 원리, 더 적게)"""
    tick = lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(*f), 2.5) * env(int(.004 * SR), .0002, .0012) * r.uniform(*amp)
    return grains(sec, r, count, tick)


def _thump(r, sec=.12, f=180, body=600):
    """한지 덮인 나무를 손끝으로 누름: 낮은 둥 + 짧은 몸통 울림(딱딱한 '딱' 대신 먹먹한 '톡')"""
    m = int(sec * SR)
    return tone(sec, f * 1.4, f) * env(m, .002, sec * .3, 3) + filt(noise(m, r), "band", body, 1.2) * env(m, .001, .015) * .6


@sfx("sfx.ui.click", -21, "UI", "버튼 누름: 한지 바른 나무를 손끝으로 톡(먹먹하게, 0.1초)", use="버튼·탭·목록 고르기(가장 자주 남 → 가장 작게)")
def _(r):
    buf = np.zeros(int(.14 * SR))
    place(buf, _thump(r, .1, 210, 900), 0)
    place(buf, _crinkle(r, .03, 4, (2500, 5000), (.1, .3)), .002)   # 종이 결이 살짝 바스락
    return reverb(buf, .25, .06)


@sfx("sfx.ui.confirm", -17, "UI", "확인: 붓끝 톡 + 도장 꾹(낮고 짧게 맺힘, 0.35초)", use="선택 확정·사기·배우기")
def _(r):
    buf = np.zeros(int(.5 * SR))
    place(buf, filt(noise(int(.012 * SR), r), "band", 1600, 1) * env(int(.012 * SR), .0005, .004) * .5, 0)   # 붓끝 닿음
    place(buf, _thump(r, .2, 150, 520) * 1.1, .07)                                                         # 인주 묻은 도장이 꾹
    place(buf, modal(.35, [(880, .09, .35), (1320, .05, .15)], r), .07)                                      # 도장 손잡이(나무) 짧은 울림
    return reverb(buf, .4, .1)


@sfx("sfx.ui.back", -21, "UI", "뒤로·취소: 종이를 옆으로 스윽 밀어 둠(위로 올라가지 않고 내려앉는 결, 0.22초)", use="취소·창 하나 뒤로·설정 닫기")
def _(r):
    m = int(.22 * SR)
    x = sweep_filt(noise(m, r), "band", 3200, 1400, 1.2) * env(m, .02, .08, 4, hold=.06)   # 높→낮으로 쓸림 = '물러남'
    return reverb(x * .8 + np.pad(_thump(r, .08, 170, 700), (int(.15 * SR), 0))[:m] * .35, .25, .06)


@sfx("sfx.ui.tab", -17, "UI", "탭 넘김: 얇은 한지 한 장 끝을 손톱으로 넘김(팔락, 0.15초)", use="명부 안 탭(명부/들은 말/장비…) 바꿀 때")
def _(r):
    buf = np.zeros(int(.2 * SR))
    place(buf, _paper(r, .1, 1800, 7000, .006) * .7, 0)
    place(buf, filt(noise(int(.05 * SR), r), "low", 900) * env(int(.05 * SR), .003, .015) * .5, .07)   # 종이가 내려앉는 바람
    return reverb(buf, .2, .05)


@sfx("sfx.ui.deny", -21, "UI", "안 됨: 먹먹한 나무 두 번 툭툭(낮게, 꾸짖지 않게, 0.3초)", use="엽전 모자람·못 누르는 버튼·칸이 꽉 참")
def _(r):
    buf = np.zeros(int(.34 * SR))
    place(buf, _thump(r, .1, 140, 380), 0); place(buf, _thump(r, .1, 125, 340), .12, .8)
    return reverb(buf, .2, .05)


@sfx("sfx.ui.ledger.open", -16, "UI", "명부 펼침: 두꺼운 표지 들림 + 한지 장이 촤라락 + 마지막 장이 툭 내려앉음(0.8초)", use="C로 명부(캐릭터 창) 열 때")
def _(r):
    sec = .85; buf = np.zeros(int(sec * SR))
    place(buf, _thump(r, .14, 120, 350) * .7, 0)                                   # 표지가 들리며 책등이 눌림
    dens = lambda k, r: .06 + .38 * (k / 26) ** 1.4 + r.uniform(0, .008)            # 처음엔 촘촘하다가 점점 느려짐(장이 덜 넘어감)
    flip = lambda r, k: _paper(r, .045, 1500, 6500, .003) * r.uniform(.3, .7) * (1 - k / 40)
    place(buf, grains(.6, r, 26, flip, spread=dens), 0)
    place(buf, filt(noise(int(.09 * SR), r), "low", 700) * env(int(.09 * SR), .004, .03) * .6, .58)   # 펼친 장이 바람을 밀며 툭
    return reverb(buf, .5, .12)


@sfx("sfx.ui.ledger.close", -17, "UI", "명부 덮음: 장이 한데 모이는 사락 + 표지 탁(낮고 포근하게, 0.5초)", use="C·Esc·닫기로 명부 닫을 때")
def _(r):
    sec = .55; buf = np.zeros(int(sec * SR))
    m = int(.22 * SR); place(buf, sweep_filt(noise(m, r), "band", 2500, 1200, 1) * env(m, .05, .06, 3, hold=.08) * .55, 0)   # 장들이 미끄러져 모임
    place(buf, _thump(r, .18, 110, 300), .2)                                          # 표지가 닫힘
    place(buf, filt(noise(int(.1 * SR), r), "low", 500) * env(int(.1 * SR), .002, .03) * .5, .2)   # 닫히며 밀려난 공기
    return reverb(buf, .4, .1)


@sfx("sfx.ui.heard.open", -21, "UI", "들은 말 창 뜸: 접힌 쪽지를 펴는 사락 + 아주 옅은 숨결(0.45초, 싸움 소리에 묻혀도 됨)", use="들은 말 창이 새로 뜰 때(엿듣기·지켜보기 완료)")
def _(r):
    sec = .5; buf = np.zeros(int(sec * SR))
    place(buf, _paper(r, .2, 1300, 5500, .03) * .6, 0)
    place(buf, _crinkle(r, .2, 6, (2000, 4500), (.1, .35)), .02)
    place(buf, filt(noise(int(.4 * SR), r), "band", 700, .7) * env(int(.4 * SR), .12, .15, 3) * .25, .05)   # 혼이 엿듣는 숨결(낮은 바람)
    return reverb(buf, .7, .2)


@sfx("sfx.ui.heard.clue", -19, "UI", "단서를 들음: 붓 한 획 스윽 + 맑은 방울 두 번 띵—딩(낮은 쪽→높은 쪽, 0.9초)", use="들은 말에 단서(금빛)가 붙어 명부에 새로 적힐 때")
def _(r):
    sec = 1.0; buf = np.zeros(int(sec * SR))
    m = int(.28 * SR)
    place(buf, filt(filt(noise(m, r), "high", 1800), "low", 6500) * env(m, .02, .08, 4, hold=.12) * .35, 0)   # 붓이 이름 옆에 한 줄 긋다
    place(buf, modal(.8, [(1174.7, .35, 1), (2349, .18, .35), (3524, .08, .12)], r) * .45, .2)   # D6
    place(buf, modal(.7, [(1568, .32, 1), (3136, .15, .3)], r) * .4, .36)                        # G6 (4도 위 = 맺힘)
    return reverb(buf, 1.0, .25)


@sfx("sfx.ui.rank.up", -12, "UI", "품계 오름: 먹물 한 방울 똑 → 물에 번지는 쏴아(부풂) → 편경 세 음 차례로 + 작은 북 둥(2.4초)", use="넋이 차서 품계가 오를 때(한 번에 여러 품이 올라도 한 번만)")
def _(r):
    sec = 2.6; n = int(sec * SR); buf = np.zeros(n)
    place(buf, bubble(.08, 900, 1.9, .018) * .6, 0)                                  # 먹물이 물에 똑
    m = int(.9 * SR)
    bloom = sweep_filt(noise(m, r), "band", 400, 2600, .9) * env(m, .55, .3, 2.5)        # 먹이 번지며 부푼다(낮→높)
    place(buf, bloom * .35, .05)
    stone = lambda f: modal(1.6, [(f, .9, 1), (f * 2.76, .35, .35), (f * 5.4, .12, .12)], r, strike=.003)   # 편경(돌 악기): 정수배 아닌 배음 = 돌의 맑음
    for k, f in enumerate([587.3, 784.0, 1174.7]):                                  # D5–G5–D6: 평조 계열, 위로 오르는 세 음
        place(buf, stone(f) * (.5 + .1 * k), .55 + k * .2)
    drum = tone(1.0, 110, 72) * env(int(1.0 * SR), .003, .28, 3)
    place(buf, drum * .55, .55)                                                       # 첫 음과 함께 작은 북
    return reverb(buf, 1.6, .3, tone_hz=4500)


@sfx("sfx.ui.save", -17, "UI", "저장(직접 누름): 도장을 꾹 눌렀다가 종이에서 떼는 '똑'(0.5초)", use="설정의 저장하기 버튼")
def _(r):
    sec = .55; buf = np.zeros(int(sec * SR))
    place(buf, _thump(r, .22, 120, 420) * 1.1, 0)                                     # 꾹 누름
    m = int(.12 * SR); place(buf, filt(noise(m, r), "band", 900, 2) * env(m, .03, .03, 3) * .3, .06)   # 인주가 눌리는 미세한 질척임
    place(buf, bubble(.05, 1400, 1.4, .01) * .35, .32)                                # 종이에서 떼는 똑
    return reverb(buf, .4, .1)


@sfx("sfx.ui.save.auto", -31, "UI", "자동 저장: 붓끝이 종이를 스치는 아주 작은 사각(0.15초, 거의 안 들림)", use="45초마다 자동 저장될 때(들리면 귀찮으니 아주 작게, 원하면 꺼도 됨)")
def _(r):
    return reverb(_paper(r, .12, 2000, 6000, .01) * .6, .2, .05)


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


# ===== 3막 지역 환경음 (⑤ 갯마을 포구 · ⑥ 도성 아랫마을, 서사 boss_clues_act3.json, 2026-10-25) =====
def _wave(r, sec, size=1.0):
    """파도 한 번: 밀려오며 커지는 쏴아(높이가 올라감) → 부서지는 찰싹 → 빠지며 자갈·거품 사르르"""
    n = int(sec * SR); tt = np.arange(n) / SR
    rise = sweep_filt(noise(n, r), "band", 300, 1200 * size, .8) * np.clip(tt / (sec * .45), 0, 1) ** 2 * (tt < sec * .5)
    crash = filt(noise(n, r), "low", 4000) * env(n, sec * .45, sec * .25, 3)
    fizz = grains(sec, r, int(120 * size), lambda r, k: bubble(.02, r.uniform(2500, 6000), 1.3, .003) * r.uniform(.05, .3),
                  spread=lambda k, r: sec * .5 + r.uniform(0, sec * .45))
    return (rise * .5 + crash * .8 + fizz * .4) * size


@sfx("amb.harbor", -22, "세계", "갯마을 포구: 선창 기둥에 찰싹이는 잔파도 + 줄에 묶인 빈 배가 삐걱 + 먼 갈매기(반복용 16초)", loop=True, use="⑤ 포구(Harbor)")
def _(r):
    sec = 16.4; n = int(sec * SR); buf = np.zeros(n)
    at = .2
    while at < sec - 1:
        d = r.uniform(2.2, 3.4); place(buf, _wave(r, d, r.uniform(.4, .7)), at); at += d * r.uniform(.6, .9)
    slap = grains(sec, r, 14, lambda r, k: filt(noise(int(.06 * SR), r), "low", 1500) * env(int(.06 * SR), .002, .02, 4) * r.uniform(.2, .5))   # 기둥에 찰싹
    creak = grains(sec, r, 6, lambda r, k: sweep_filt(noise(int(.7 * SR), r), "band", r.uniform(350, 500), r.uniform(500, 700), 14) * env(int(.7 * SR), .1, .2, 4, hold=.3) * .5)   # 배끼리·줄 삐걱
    gull = np.zeros(n)
    for at in (4.0, 4.35, 11.5):
        d = .45; f0 = curve(d, [(0, 1500), (.1, 1900), (.4, 1300)])
        place(gull, voice(f0, [(2200, 4, 1), (3600, 5, .4)], .3, r, nh=10) * env(int(d * SR), .02, .15, 3, hold=.15), at)
    gull = reverb(filt(gull, "low", 3500), 1.8, .5)[:n]
    return loopify(buf + slap + creak + gull * .25 + filt(noise(n, r), "low", 150) * .2, .5)


@sfx("sfx.tide.flood", -12, "세계", "밀물 신호: 먼바다에서 낮게 웅— 밀려오는 큰 물소리가 점점 차오름 + 징 한 번(약 5초) — 20초 안에 붙잡아라", bypass_cast=True, use="⑤ 밀물 신호 순간(물 혼이 떠밀려 가기 시작)")
def _(r):
    sec = 5.2; n = int(sec * SR); buf = np.zeros(n)
    surge = sweep_filt(noise(n, r), "low", 200, 1800) * curve(sec, [(0, 0), (3.5, 1), (5.2, .6)])
    swell = tone(sec, 55, 65) * curve(sec, [(0, 0), (3, .6), (5.2, 0)])
    jing = modal(4.5, [(150, 2.5, 1), (151.2, 2.5, .8), (322, 1.4, .5), (463, .9, .3)], r)   # 징: 맥놀이가 긴 놋쇠 울림
    place(buf, jing * .7, 0)
    buf += surge * .7 + swell * .4
    return reverb(buf, 2.0, .3)


@sfx("amb.tide.ebb", -24, "세계", "썰물 갯벌: 물 빠진 갯벌이 뽀글뽀글 숨 쉼 + 게 구멍 톡톡 + 멀어진 파도(반복용 15초)", loop=True, use="⑤ 썰물 때 포구·난파 여울 바닥")
def _(r):
    sec = 15.4; n = int(sec * SR)
    far = filt(noise(n, r), "low", 500) * (.5 + .3 * np.sin(2 * np.pi * T(sec) / 7.7))      # 멀리 물러난 바다
    mud = grains(sec, r, 500, lambda r, k: bubble(.03, r.uniform(800, 2500), 1.6, .006) * r.uniform(.05, .4))   # 갯벌 숨구멍
    crab = grains(sec, r, 40, lambda r, k: modal(.03, [(r.uniform(3000, 5000), .006, 1)], r) * r.uniform(.05, .2))
    drain = filt(noise(n, r), "band", 1800, 1.5) * .06                                     # 갯골로 흘러 나가는 가는 물
    return loopify(far * .6 + mud * .5 + crab + drain, .5)


@sfx("amb.saltfield", -23, "세계", "소금밭: 탁 트인 바닷바람 + 소금 결정이 바람에 서걱 + 아주 먼 파도(반복용 14초)", loop=True, use="⑤ 소금밭(SaltField)")
def _(r):
    sec = 14.4; n = int(sec * SR)
    g = _gust_curve(sec, r, 2, .4)
    wind = filt(noise(n, r), "band", 600, .6) * (.4 + .6 * g)
    salt = grains(sec, r, 900, lambda r, k: filt(noise(int(.002 * SR), r), "high", 5000) * r.uniform(.02, .12)) * np.repeat(g, 1)[:n]
    sea = filt(noise(n, r), "low", 300) * .3
    return loopify(wind * .5 + salt + sea, .5)


@sfx("amb.wreckshoal", -21, "세계", "난파 여울: 암초 사이를 빠르게 흐르는 물살 + 부서진 배 나무가 물에 부딪혀 쿵·삐걱(반복용 15초)", loop=True, use="⑤ 난파 여울(WreckShoal)·B-10 갑판")
def _(r):
    sec = 15.4; n = int(sec * SR); t = T(sec)
    rush = filt(filt(noise(n, r), "high", 200), "low", 3500) * (.8 + .2 * np.sin(2 * np.pi * t / 3.1))
    churn = grains(sec, r, 400, lambda r, k: bubble(.06, r.uniform(250, 900), 2, .015) * r.uniform(.1, .6))   # 물살 속 공기 방울
    hull = grains(sec, r, 7, lambda r, k: (modal(.5, [(r.uniform(70, 110), .2, 1), (r.uniform(220, 300), .1, .4)], r) + filt(noise(int(.5 * SR), r), "low", 400) * env(int(.5 * SR), .002, .05, 4) * .5) * r.uniform(.3, .7))   # 배 조각이 바위에 쿵
    creak = grains(sec, r, 5, lambda r, k: sweep_filt(noise(int(.8 * SR), r), "band", 280, 420, 16) * env(int(.8 * SR), .1, .2, 4, hold=.35) * .5)
    return loopify(rush * .6 + churn * .4 + hull + creak, .5)


@sfx("amb.capital.market", -24, "세계", "도성 저잣거리: 촘촘한 사람 소리(뜻 안 들림) + 장사꾼의 길게 끄는 외침 + 엽전·그릇·수레·소 방울 + 먼 장구(반복용 16초)", loop=True, use="⑥ 저잣거리(Market) — 1막 장터보다 크고 바쁘다")
def _(r):
    sec = 16.4; n = int(sec * SR); buf = np.zeros(n)
    vowels = [[(750, 4, 1), (1200, 5, .5)], [(450, 4, 1), (1900, 6, .4)], [(320, 4, 1), (2300, 7, .35)], [(550, 4, 1), (900, 5, .6)]]
    for p in range(24):                                       # 사람이 장터보다 많다
        base = r.uniform(110, 280); at = r.uniform(0, 1.0)
        while at < sec - .3:
            d = r.uniform(.07, .22); m = int(d * SR)
            f0 = np.linspace(base * r.uniform(.9, 1.2), base * r.uniform(.8, 1.05), m)
            place(buf, voice(f0, vowels[r.integers(4)], .2, r, nh=16) * env(m, .012, d * .4, 3, hold=d * .4) * r.uniform(.2, .8), at)
            at += d + (r.uniform(.02, .07) if r.random() > .12 else r.uniform(.3, 1.2))
    buf = filt(buf, "low", 2000)
    for at in (2.0, 9.0, 13.5):                               # 장사꾼 외침: 길게 끌어 올렸다 내림(말뜻 없음)
        d = 1.3; f0 = curve(d, [(0, 200), (.2, 300), (.9, 290), (1.3, 220)])
        place(buf, filt(voice(f0, [(700, 4, 1), (1150, 5, .5)], .25, r, nh=25), "low", 2500) * env(int(d * SR), .05, .3, 3, hold=.8) * .5, at)
    coins = grains(sec, r, 40, lambda r, k: modal(.12, [(r.uniform(3500, 5500), .03, 1), (r.uniform(6500, 8000), .015, .4)], r) * r.uniform(.05, .2))
    cart = grains(sec, r, 4, lambda r, k: filt(noise(int(.6 * SR), r), "band", r.uniform(450, 700), 6) * env(int(.6 * SR), .1, .2, 3, hold=.2) * .3)
    cowbell = grains(sec, r, 6, lambda r, k: modal(.5, [(r.uniform(700, 800), .15, 1), (r.uniform(1700, 1900), .08, .4)], r) * .1)
    drum = np.zeros(n)
    for k in range(int(sec / .5)):                             # 아주 멀리 장구 굿거리 비슷한 박
        if k % 6 in (0, 3, 4):
            place(drum, tone(.2, 120, 90) * env(int(.2 * SR), .002, .06, 4) * (1 if k % 6 == 0 else .5), k * .5)
    drum = filt(drum, "low", 600) * .15
    return loopify(reverb(buf + coins + cart + cowbell + drum + filt(noise(n, r), "low", 350) * .1, 1.0, .25, tone_hz=3000)[:n], .5)


@sfx("amb.bridge.under", -24, "세계", "큰 다리 밑: 다리 아래로 흐르는 강물 + 머리 위 돌다리를 지나는 둔탁한 발소리·수레 + 거적 움막 바스락(반복용 15초)", loop=True, use="⑥ 큰 다리 밑(BridgeUnder)·움막촌")
def _(r):
    sec = 15.4; n = int(sec * SR)
    river = filt(filt(noise(n, r), "high", 150), "low", 1800) * .5 + grains(sec, r, 200, lambda r, k: bubble(.05, r.uniform(300, 800), 1.8, .012) * r.uniform(.1, .4))
    steps = np.zeros(n); at = 1.0
    while at < sec - 1:                                         # 위를 지나는 사람들(돌을 지나 먹먹하게)
        for j in range(r.integers(4, 9)):
            place(steps, filt(noise(int(.08 * SR), r), "low", 300) * env(int(.08 * SR), .002, .03, 4) * r.uniform(.3, .7), at + j * .5)
        at += r.uniform(3, 6)
    roll = np.zeros(n); place(roll, filt(noise(int(2.5 * SR), r), "low", 180) * np.sin(np.pi * np.linspace(0, 1, int(2.5 * SR))) * .8, 8.0)   # 수레가 다리를 건넘
    straw = grains(sec, r, 25, lambda r, k: filt(noise(int(.05 * SR), r), "band", r.uniform(2000, 4000), 1.5) * env(int(.05 * SR), .005, .015, 4) * r.uniform(.05, .2))
    return loopify(reverb(river * .6 + steps + roll + straw, 1.2, .35, tone_hz=2500)[:n], .5)


@sfx("amb.citygate", -21, "세계", "닫힌 성문 밖의 밤: 성벽을 따라 부는 찬 바람 + 성문 쇠고리가 가끔 덜컥 + 아주 먼 개 짖음(반복용 16초)", loop=True, use="⑥ 성문 밖(CityGate)·팻말 없는 무덤")
def _(r):
    sec = 16.4; n = int(sec * SR)
    g = _gust_curve(sec, r, 3, .3)
    wind = sweep_filt(noise(n, r), "band", 250, 380, 2) * (.5 + .5 * g) + filt(noise(n, r), "low", 120) * .4
    knock = grains(sec, r, 4, lambda r, k: modal(.6, [(r.uniform(400, 500), .15, 1), (r.uniform(1100, 1300), .08, .5), (r.uniform(2400, 2700), .04, .3)], r) * .35)   # 쇠고리 덜컥(큰 나무문 울림)
    dog = np.zeros(n)
    for at in (6.0, 6.4, 6.75, 13.0):
        d = .22; f0 = curve(d, [(0, 420), (.05, 520), (d, 380)])
        place(dog, voice(f0, [(900, 3, 1), (1800, 4, .5)], .4, r, nh=15) * env(int(d * SR), .005, .08, 4), at)
    dog = reverb(filt(dog, "low", 1500), 2.5, .6, tone_hz=1500)[:n]
    return loopify(wind * .7 + knock + dog * .35, .5)


# ===== 무기 5종 타격음·휘두름 (2026-10-25 점검: 지금은 다섯 무기가 모두 sfx.hit.chain / sfx.hit.heavy 하나를 같이 씀) =====
# 무기마다 '재료'가 다르게 들리게 한다. 귀가 무기를 구분하는 단서는 셋: 높이(밝기), 길이(꼬리), 첫 순간의 모양.
#   철삭(Chain)     쇠사슬 철컥 — 중고음, 고리가 차례로 부딪힘 (기존 sfx.hit.chain/heavy 그대로)
#   육모방망이(Mace) 단단한 나무 몸통 퍽 — 가장 낮고 두꺼움, 꼬리 짧음
#   요령방울(Bell)   놋쇠 방울 짤랑 — 가장 밝고 꼬리 김(맞을 때마다 '울린다')
#   삼지창(Trident)  쇠끝이 박힘 — 아주 짧고 날카로운 시작 + 찔려 들어가는 소리
#   명부 붓(Brush)   먹이 튀며 획이 박힘 — 가볍고 촉촉함, 3타는 도장 '탁'
def _flesh(r, sec=.25, f=800, a=.5):
    """맞은 몸(혼)의 살 느낌: 짧은 대역 잡음 퍽"""
    n = int(sec * SR); return filt(noise(n, r), "band", f, 1.2) * env(n, .001, .035) * a


@sfx("sfx.hit.mace", -8, "전투", "육모방망이 타격: 단단한 나무 몸통이 퍽 — 낮고 두껍고 짧다", use="육모방망이 1·2타 적중")
def _(r):
    n = int(.35 * SR)
    wood = modal(.35, [(r.uniform(230, 250), .05, 1), (r.uniform(520, 560), .035, .7), (r.uniform(980, 1050), .02, .4), (1800, .01, .2)], r)   # 단단한 나무(배음이 정수배가 아님)
    thump = tone(.35, 120, 55) * env(n, .001, .08, 3)
    crack = filt(noise(n, r), "band", 1600, 1.5) * env(n, .0005, .012)          # 모서리(육모)가 박히는 딱
    return reverb(wood * .6 + thump * 1.0 + crack * .5 + _flesh(r, .35, 600, .6), .45, .1)


@sfx("sfx.hit.mace.heavy", -5, "전투", "육모방망이 3타 내려찍기: 땅까지 울리는 쿵 + 흙 튐 + 나무 울림(반경 3m 기절)", use="육모방망이 3타(내려찍기) 적중·땅 찍기")
def _(r):
    n = int(.9 * SR); buf = np.zeros(n)
    boom = tone(.9, 80, 32) * env(n, .002, .25, 3)
    ground = filt(noise(n, r), "low", 350) * env(n, .001, .15, 3)
    wood = modal(.4, [(210, .07, 1), (470, .05, .6), (900, .03, .3)], r)
    dirt = grains(.7, r, 50, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(1000, 4000), 2) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .5), spread=lambda k, r: .03 + r.exponential(.12))
    buf += boom * 1.0 + ground * .8; place(buf, dirt * .5, 0); place(buf, wood * .6, 0)
    return reverb(buf, .9, .15)


# 2026-10-25 밤 음량 검사(tools/audio_budget.py): 방울은 꼬리가 길어 같은 최고점이라도 귀에는 다른 타격보다 약 8dB 크게 들림 → 4dB 내림
@sfx("sfx.hit.bell", -14, "전투", "요령방울 타격: 놋쇠 방울이 짤랑 울리며 맞음 — 밝고 꼬리가 길다(맞을 때마다 '울린다')", use="요령방울 1·2타 적중(360° 원 범위라 여럿이 동시에 맞으면 1번만 재생)")
def _(r):
    n = int(.8 * SR); buf = np.zeros(n)
    f = r.uniform(2050, 2200)
    bell = modal(.8, [(f, .3, 1), (f * 1.006, .3, .7), (f * 2.32, .18, .5), (f * 3.9, .08, .3)], r)   # 방울: 맥놀이 + 높은 배음
    jingle = grains(.15, r, 5, lambda r, k: modal(.15, [(r.uniform(3500, 5500), .04, 1)], r) * .4, spread=lambda k, r: k * .02 + r.uniform(0, .01))   # 방울 속 구슬이 짤랑
    place(buf, bell * .7, 0); place(buf, jingle * .5, .005)
    buf += np.concatenate([_flesh(r, .2, 1100, .35), np.zeros(n - int(.2 * SR))])
    return reverb(buf, 1.0, .2)


@sfx("sfx.hit.bell.heavy", -11, "전투", "요령방울 3타 '울림': 큰 방울 댕— 퍼지는 소리 + 공기가 둥글게 밀려나는 웅(원 범위 넉백)", use="요령방울 3타(toll) 적중")
def _(r):
    n = int(1.6 * SR); buf = np.zeros(n)
    f = 1046
    bell = modal(1.6, [(f, .7, 1), (f * 1.004, .7, .8), (f * 2.0, .45, .5), (f * 2.76, .3, .4), (f * 5.4, .12, .2)], r)
    wave = sweep_filt(noise(n, r), "low", 900, 150) * env(n, .005, .25, 3)          # 둥글게 밀려나는 공기
    sub = tone(1.6, 70, 50) * env(n, .003, .2, 3)
    buf += bell * .7 + wave * .5 + sub * .6
    return reverb(buf, 1.6, .3)


@sfx("sfx.hit.trident", -9, "전투", "삼지창 찌르기 적중: 쇠끝이 '칙' 박히고 쑥 들어가는 소리 — 가장 짧고 날카로운 시작", use="삼지창 1·2타 적중(관통: 둘째·셋째 대상은 0.03초씩 늦춰 작게)")
def _(r):
    n = int(.3 * SR); buf = np.zeros(n)
    tip = filt(noise(int(.012 * SR), r), "high", 3500) * env(int(.012 * SR), .0002, .003)     # 쇠끝이 닿는 칙
    place(buf, tip * 1.0, 0)
    prong = modal(.25, [(r.uniform(2900, 3100), .025, 1), (r.uniform(4400, 4700), .015, .5), (r.uniform(6900, 7300), .008, .3)], r)   # 세 갈래 날의 짧은 쇳소리
    place(buf, prong * .4, .002)
    sink = sweep_filt(noise(int(.15 * SR), r), "band", 1500, 500, 2) * env(int(.15 * SR), .005, .05, 4)   # 쑥 들어감(높이가 내려감)
    place(buf, sink * .6, .01)
    place(buf, tone(.12, 200, 120) * env(int(.12 * SR), .001, .03, 4) * .5, .01)
    return reverb(buf, .35, .08)


@sfx("sfx.hit.trident.heavy", -6, "전투", "삼지창 3타 꿰뚫기: 세 번 연달아 칙-칙-칙 박히고 마지막에 깊게 쾅 + 쇠 떨림", use="삼지창 3타(skewer) 적중")
def _(r):
    n = int(.8 * SR); buf = np.zeros(n)
    for k in range(3):
        tip = filt(noise(int(.01 * SR), r), "high", 3500) * env(int(.01 * SR), .0002, .003)
        place(buf, tip * (.3 + .1 * k), k * .035)
        place(buf, modal(.15, [(3000 + 150 * k, .02, 1), (4600, .012, .4)], r) * .3, k * .035)
    deep = tone(.5, 140, 50) * env(int(.5 * SR), .001, .12, 3) + filt(noise(int(.5 * SR), r), "low", 600) * env(int(.5 * SR), .001, .06, 4) * .8
    place(buf, deep * 1.8, .1)
    shiver = modal(.6, [(1850, .25, 1), (1862, .25, .8)], r) * .25                      # 박힌 창대가 부르르 떪(맥놀이)
    place(buf, shiver, .1)
    return reverb(buf, .6, .12)


@sfx("sfx.hit.brush", -11, "전투", "명부 붓 획 적중: 먹물이 '촥' 튀며 획이 박힘 — 가볍고 촉촉하다", use="명부 붓 1·2타 적중(먼 거리)")
def _(r):
    n = int(.35 * SR); buf = np.zeros(n)
    swish = sweep_filt(noise(int(.08 * SR), r), "band", 4000, 1800, 1.5) * env(int(.08 * SR), .002, .025, 4)   # 붓끝이 긋는 촥
    place(buf, swish * .8, 0)
    splat = grains(.35, r, 18, lambda r, k: bubble(.03, r.uniform(500, 1400), 1.5, .007) * r.uniform(.2, .7), spread=lambda k, r: .01 + r.exponential(.05))   # 먹물 방울
    buf += splat * .5
    buf += np.concatenate([_flesh(r, .15, 1300, .3), np.zeros(n - int(.15 * SR))])
    return reverb(buf, .4, .1)


@sfx("sfx.hit.brush.heavy", -8, "전투", "명부 붓 3타 '인(도장)': 도장이 탁 찍히며 먹이 퍽 번짐 + 종이 위 붉은 인 같은 짧은 울림", use="명부 붓 3타(seal) 적중")
def _(r):
    n = int(.8 * SR); buf = np.zeros(n)
    stamp = modal(.3, [(330, .05, 1), (740, .03, .5), (1500, .015, .3)], r) + tone(.3, 110, 60) * env(int(.3 * SR), .001, .06, 4)
    place(buf, stamp, 0)
    place(buf, filt(noise(int(.04 * SR), r), "low", 2500) * env(int(.04 * SR), .0005, .01, 4) * .8, 0)   # 도장 면이 닿는 탁
    bloom = sweep_filt(noise(int(.5 * SR), r), "low", 2500, 400) * env(int(.5 * SR), .01, .12, 4) * .4   # 먹이 퍽 번짐
    place(buf, bloom, .02)
    place(buf, modal(.6, [(1568, .25, 1), (2349, .15, .4)], r) * .2, .03)              # 인이 찍힌 짧은 울림
    return reverb(buf, .7, .15)


# 휘두르는 소리(헛스윙 포함): 맞기 전, 휘두름 시작(windup 끝)에 재생. 무기 무게가 들려야 손맛이 산다
@sfx("sfx.swing.chain", -16, "전투", "철삭 휘두름: 사슬이 차르륵 풀리며 휙", use="철삭 휘두름 시작(windup 끝)")
def _(r):
    n = int(.3 * SR)
    whoosh = sweep_filt(noise(n, r), "band", 900, 2500, 1.5) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    rattle = grains(.25, r, 9, lambda r, k: modal(.04, [(r.uniform(3000, 5500), .008, 1)], r) * r.uniform(.3, .8), spread=lambda k, r: k * .025 + r.uniform(0, .008))
    return whoosh * .7 + np.concatenate([rattle, np.zeros(n - len(rattle))]) * .4


@sfx("sfx.swing.mace", -14, "전투", "육모방망이 휘두름: 무거운 몸통이 낮게 부웅", use="육모방망이 휘두름 시작")
def _(r):
    n = int(.4 * SR)
    return sweep_filt(noise(n, r), "band", 200, 700, 1.2) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 + tone(.4, 70, 90) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * .3


@sfx("sfx.swing.bell", -16, "전투", "요령방울 휘두름: 방울이 흔들려 짤랑짤랑 + 가벼운 휙", use="요령방울 휘두름 시작")
def _(r):
    n = int(.35 * SR)
    whoosh = sweep_filt(noise(n, r), "band", 1200, 2500, 1.5) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * .4
    jing = grains(.3, r, 6, lambda r, k: modal(.2, [(r.uniform(4000, 5500), .05, 1), (r.uniform(2100, 2300), .08, .4)], r) * r.uniform(.3, .7), spread=lambda k, r: k * .045 + r.uniform(0, .01))
    return whoosh + np.concatenate([jing, np.zeros(max(0, n - len(jing)))])[:n] * .5


@sfx("sfx.swing.trident", -16, "전투", "삼지창 찌름: 짧고 곧게 쉭 — 높이가 위로 쏘아 올라감", use="삼지창 찌르기 시작")
def _(r):
    n = int(.18 * SR)
    return sweep_filt(noise(n, r), "band", 1500, 5000, 2) * env(n, .03, .05, 4, hold=.04)


@sfx("sfx.swing.brush", -18, "전투", "명부 붓 휘두름: 붓털이 공기를 쓸며 사악 + 먹 한 방울 튐", use="명부 붓 휘두름 시작(획이 날아감)")
def _(r):
    n = int(.25 * SR); buf = np.zeros(n)
    buf += filt(filt(noise(n, r), "high", 2500), "low", 8000) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * .5
    place(buf, bubble(.04, 900, 1.5, .008) * .3, .15)
    return buf


# ===== 무기별 천도·파혼 변형 (무기 특성표 Core/Gear.cs: 요령방울=천도 빠름·파혼 약함, 육모방망이=파혼 강함, 삼지창=파혼 날카로움, 붓=천도 넋 많음·파혼 약함, 철삭=연속 천도) =====
# 바탕은 기존 sfx.tendo.done / sfx.pahon.burst 그대로(같은 고정 난수) + 무기 재료의 짧은 '꾸밈' 한 겹.
# 강조하는 쪽은 꾸밈을 크게·길게(그리고 파일 크기를 1~2dB 높게), 약한 쪽은 바탕을 덜어 낸다.
def _base(id):
    """기존 소리를 같은 난수로 다시 만든다(바탕). 기존 파일과 똑같은 소리"""
    return np.asarray(REG[id]["fn"](np.random.default_rng(zlib.crc32(id.encode()) & 0xffffffff)), dtype=np.float64)


def _mix(base, accent, at=0.0, a=1.0):
    n = max(len(base), int(at * SR) + len(accent))
    out = np.zeros(n); out[:len(base)] += base / (np.abs(base).max() + 1e-9)
    place(out, accent / (np.abs(accent).max() + 1e-9) * a, at)
    return out


@sfx("sfx.tendo.done.chain", -7, "처결", "천도 완료(철삭): 기본 천도음 + 풀린 사슬이 차르르 내려앉음", use="철삭으로 천도 성공")
def _(r):
    links = grains(.6, r, 10, lambda r, k: modal(.08, [(r.uniform(2800, 4500), .02, 1)], r) * (1 - k / 12), spread=lambda k, r: k * .05 + r.uniform(0, .01))
    return _mix(_base("sfx.tendo.done"), links, .35, .25)


@sfx("sfx.tendo.done.mace", -9, "처결", "천도 완료(육모방망이): 기본 천도음을 조금 낮고 작게 + 나무 '톡' 한 번(천도는 이 무기의 강점이 아니다)", use="육모방망이로 천도 성공")
def _(r):
    b = filt(_base("sfx.tendo.done"), "low", 4000)
    return _mix(b, modal(.3, [(240, .05, 1), (540, .03, .5)], r), .05, .3)


@sfx("sfx.tendo.done.bell", -5, "처결", "천도 완료(요령방울) — 강조: 기본 천도음 위로 요령이 길게 짤랑짤랑 울려 퍼지며 한 음 더 높이 올라감", use="요령방울로 천도 성공(이 무기의 강점)")
def _(r):
    sec = 3.0; acc = np.zeros(int(sec * SR))
    for k in range(9):                                            # 요령을 흔드는 짤랑 — 점점 잦아듦
        f = r.uniform(2050, 2250)
        place(acc, modal(1.0, [(f, .35, 1), (f * 1.006, .35, .7), (f * 2.32, .2, .4)], r) * (1 - k / 11), .05 + k * .16 + r.uniform(0, .02))
    place(acc, modal(2.2, [(1568 * 2, 1.0, 1), (1568 * 2 * 1.004, 1.0, .7)], r) * .6, 1.5)   # 마지막에 한 음 더 높이(G7)
    return reverb(_mix(_base("sfx.tendo.done"), acc, 0, .7), 1.2, .15)


@sfx("sfx.tendo.done.trident", -7, "처결", "천도 완료(삼지창): 기본 천도음 + 세 갈래 날이 맑게 '팅' 세 번", use="삼지창으로 천도 성공")
def _(r):
    acc = np.zeros(int(.8 * SR))
    for k, f in enumerate((2960, 3520, 4186)):
        place(acc, modal(.5, [(f, .2, 1), (f * 1.003, .2, .6)], r) * .6, k * .09)
    return _mix(_base("sfx.tendo.done"), acc, .3, .3)


@sfx("sfx.tendo.done.brush", -6, "처결", "천도 완료(명부 붓) — 넋이 많다: 기본 천도음 + 붓이 이름을 한 획 긋고 먹빛 반짝임이 여러 번 피어오름", use="명부 붓으로 천도 성공(넋 보너스)")
def _(r):
    acc = np.zeros(int(2.0 * SR))
    m = int(.5 * SR); place(acc, filt(filt(noise(m, r), "high", 1800), "low", 6500) * env(m, .03, .12, 4, hold=.25) * .5, 0)   # 이름 한 획
    for k in range(7):                                            # 넋이 송골송골 피어오름(위로 올라가는 작은 방울들)
        place(acc, bubble(.25, 900 + 220 * k, 1.6, .05) * .35, .5 + k * .14); place(acc, modal(.6, [(1760 + 200 * k, .25, 1)], r) * .25, .5 + k * .14)
    return _mix(_base("sfx.tendo.done"), acc, .2, .5)


@sfx("sfx.pahon.burst.chain", -4, "처결", "파혼(철삭): 기본 파혼음 + 사슬이 팽팽히 당겨졌다 '쩡' 끊기듯 튕김", use="철삭으로 파혼")
def _(r):
    snap = modal(.6, [(1240, .12, 1), (1873, .09, .8), (2631, .06, .6)], r)
    place(snap, filt(noise(int(.02 * SR), r), "high", 2500) * env(int(.02 * SR), .0003, .005), 0)
    return _mix(_base("sfx.pahon.burst"), snap, .0, .35)


@sfx("sfx.pahon.burst.mace", -2, "처결", "파혼(육모방망이) — 강조: 기본 파혼음 + 나무 몸통이 땅을 내리치는 거대한 쿵 + 땅 울림 + 흙 튐(가장 크고 무겁다)", use="육모방망이로 파혼(이 무기의 강점: 넉백·피해 큼)")
def _(r):
    sec = 1.6; n = int(sec * SR); acc = np.zeros(n)
    acc += tone(sec, 70, 28) * env(n, .002, .4, 3) * 1.2 + filt(noise(n, r), "low", 300) * env(n, .001, .25, 3)
    place(acc, modal(.5, [(200, .08, 1), (450, .05, .6), (880, .03, .3)], r) * .8, 0)
    place(acc, grains(1.2, r, 80, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(800, 3500), 2) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .5), spread=lambda k, r: .03 + r.exponential(.2)), 0)
    return reverb(_mix(_base("sfx.pahon.burst"), acc, 0, 1.3), 1.0, .12)


@sfx("sfx.pahon.burst.bell", -7, "처결", "파혼(요령방울) — 약함: 기본 파혼음을 덜어 내고, 방울이 금 간 소리로 '찌릉' 어긋나게 울림", use="요령방울로 파혼(이 무기의 약점: 파혼 피해 작음)")
def _(r):
    b = filt(_base("sfx.pahon.burst"), "high", 180) * .7
    cracked = modal(1.0, [(2100, .3, 1), (2230, .3, .9), (3300, .15, .5)], r)   # 반음 가까이 어긋난 두 음 = 금 간 방울
    place(cracked, filt(noise(int(.3 * SR), r), "band", 3000, 2) * env(int(.3 * SR), .002, .05, 4) * .4, 0)
    return _mix(b, cracked, .05, .5)


@sfx("sfx.pahon.burst.trident", -4, "처결", "파혼(삼지창) — 날카로움: 기본 파혼음 + 쇠가 찢기듯 높게 '끼익' 긁히며 꿰뚫음", use="삼지창으로 파혼(파혼 넉백·피해 보정)")
def _(r):
    m = int(.6 * SR)
    scream = sweep_filt(noise(m, r), "band", 6000, 2500, 8) * env(m, .005, .15, 4, hold=.1)   # 쇠 긁힘
    pierce = modal(.5, [(3100, .1, 1), (4650, .06, .6), (7200, .03, .3)], r)
    return _mix(_base("sfx.pahon.burst"), scream * .7 + np.concatenate([pierce, np.zeros(m - len(pierce))])[:m], .0, .5)


@sfx("sfx.pahon.burst.brush", -7, "처결", "파혼(명부 붓) — 약함: 기본 파혼음을 덜어 내고, 종이 이름이 '찌익' 찢기며 먹이 흩어짐", use="명부 붓으로 파혼(이 무기의 약점)")
def _(r):
    b = _base("sfx.pahon.burst") * .7
    m = int(.7 * SR)
    tear = sweep_filt(noise(m, r), "band", 1500, 4000, 1.5) * env(m, .02, .1, 4, hold=.3)
    tear += grains(.7, r, 60, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(2000, 6000), 2) * env(int(.003 * SR), .0002, .001) * r.uniform(.2, 1))
    return _mix(b, tear, .05, .5)


# ===== 처결 대기 긴장음 (무릎 꿇은 혼의 남은 시간: 갓 죽은 10초 · 해 넘긴 7초 · 오래된 4초, balance WAIT_*) =====
# 방식: 혼 나이별 '똑딱' 한 개를 코드가 남은 시간에 맞춰 점점 빨리 친다(간격 1.0초 → 0.15초).
# 왜 긴 파일 하나가 아니라 똑딱인가? 대기 시간은 장비·도술(TILT_WAIT_ADD, SKILL_HOLD_WAIT_BONUS 등)로 늘거나 줄기 때문.
@sfx("sfx.wait.tick.fresh", -16, "처결", "대기 똑딱(갓 죽은 혼): 아직 사람 같은 낮은 심장 소리 '두근'", bypass_cast=True, use="갓 죽은 혼이 무릎 꿇고 기다리는 동안 반복(남은 시간에 따라 간격을 줄임)")
def _(r):
    buf = np.zeros(int(.4 * SR))
    for at, a in ((0, 1), (.14, .7)):                              # 두-근
        place(buf, tone(.15, 62, 48) * env(int(.15 * SR), .004, .05, 4) * a + filt(noise(int(.15 * SR), r), "band", 450, 1.2) * env(int(.15 * SR), .002, .03, 4) * .6 * a, at)   # 폰 스피커에도 들리게 400Hz대 '툭'을 섞음
    return buf


@sfx("sfx.wait.tick.year", -16, "처결", "대기 똑딱(해 넘긴 혼): 마른 나무를 치는 '똑'(목탁 비슷하게 속이 빈 소리)", bypass_cast=True, use="해 넘긴 혼이 기다리는 동안 반복")
def _(r):
    return modal(.25, [(r.uniform(560, 600), .05, 1), (r.uniform(1450, 1550), .025, .4), (2900, .01, .15)], r)


@sfx("sfx.wait.tick.old", -15, "처결", "대기 똑딱(오래된 혼): 녹슨 쇠를 긁듯 '칙' + 낮은 금 간 쇳소리 — 가장 거칠고 불안하다", bypass_cast=True, use="오래된 혼·덩어리가 기다리는 동안 반복")
def _(r):
    n = int(.3 * SR)
    rust = modal(.3, [(410, .06, 1), (437, .06, .9), (1210, .03, .5)], r)   # 가까운 두 음이 부딪혀 거칠게 떪
    grit = filt(noise(n, r), "band", 2500, 2) * env(n, .001, .02, 4)
    return rust + grit * .6


@sfx("sfx.wait.final", -14, "처결", "대기 마지막 1.5초: 숨을 들이켜듯 올라가는 소리 + 고리가 조여드는 떨림 — 지금 고르지 않으면 일어선다", bypass_cast=True, use="남은 시간 1.5초에 한 번(혼 나이 상관없이 같음)")
def _(r):
    sec = 1.5; n = int(sec * SR); t = T(sec)
    breath = sweep_filt(noise(n, r), "band", 500, 2200, 2) * curve(sec, [(0, .1), (1.4, 1), (1.5, 0)])
    trem = tone(sec, 220, 440) * (.5 + .5 * np.sin(2 * np.pi * curve(sec, [(0, 6), (1.5, 18)]).cumsum() / SR)) * curve(sec, [(0, 0), (1.4, .5), (1.5, 0)])
    return breath * .6 + trem * .35


@sfx("sfx.wait.expire", -14, "처결", "놓침: 혼이 다시 일어섬 — 무릎 꿇은 기운이 툭 끊기고 낮게 '우웅' 되살아나는 소리", bypass_cast=True, use="대기 시간이 다 돼 혼이 맺힘 50%로 일어설 때")
def _(r):
    sec = 1.2; n = int(sec * SR); buf = np.zeros(n)
    place(buf, filt(noise(int(.05 * SR), r), "low", 1500) * env(int(.05 * SR), .001, .015, 4) * .8, 0)   # 툭 끊김
    rise = tone(sec, 70, 140) * curve(sec, [(0, 0), (.15, .8), (.9, .6), (1.2, 0)])
    moan = voice(curve(sec, [(0, 90), (.8, 150), (1.2, 140)]), [(500, 4, 1), (900, 5, .5)], .4, r, nh=20) * curve(sec, [(0, 0), (.2, .5), (1.0, .4), (1.2, 0)])
    buf += rise * .6 + moan * .4
    return reverb(buf, .8, .2)


# ===== 1막 보스 전투 소리 보강 (B-01 나루 영감 · B-02 월화 · B-03 서 의원, 2026-10-25 밤) =====
# 왜: 컷신 소리는 대본에 다 맞춰져 있지만, '싸우는 동안' 1막 보스는 거의 말이 없다.
#   나루 영감은 일반 혼과 같은 예고음, 월화는 컷신용 방울 하나, 서 의원은 경고음만 있고 '터지는' 소리가 없다.
#   보스는 크게 읽혀야 하므로(BOSS-01 기획 ① 예비동작 0.6초) 예고 → 실제 공격을 소리로도 나눈다.
def _splash(r, sec=.6, size=1.0):
    """물보라: 물이 깨지는 쏴 + 굵은 방울이 흩어져 떨어짐"""
    n = int(sec * SR); buf = np.zeros(n)
    place(buf, filt(noise(n, r), "low", 3500) * env(n, .004, sec * .3, 3) * size, 0)
    place(buf, grains(sec, r, int(30 * size), lambda r, k: bubble(.06, r.uniform(500, 1800), 1.8, .012) * r.uniform(.2, .7), t0=.05), 0, .5)
    return buf


@sfx("sfx.boss.naru.sweep.telegraph", -12, "보스", "나루 영감 삿대 휩쓸기 예고: 삿대를 물에서 끌어올리는 물 뚝뚝 + 배가 삐걱 기울어짐(0.6초, 이 소리 끝에 휩쓸림)", bypass_cast=True, use="B-01: 삿대 휩쓸기 예비동작 시작(일반 혼 예고음 대신)")
def _(r):
    sec = .75; buf = np.zeros(int(sec * SR))
    m = int(.5 * SR); place(buf, sweep_filt(noise(m, r), "band", 400, 1300, 1.2) * env(m, .15, .1, 3, hold=.15) * .6, 0)   # 삿대가 물을 가르며 올라옴
    place(buf, grains(.6, r, 9, lambda r, k: bubble(.08, r.uniform(900, 1900), 1.6, .012) * r.uniform(.3, .7), t0=.15), 0)   # 물 뚝뚝
    creak = tone(.45, 210, 160) * (1 + .6 * np.sign(np.sin(2 * np.pi * 34 * T(.45)))) * env(int(.45 * SR), .05, .2, 3, hold=.1)   # 배 나무 삐걱(울퉁불퉁한 낮은 음)
    place(buf, filt(creak, "band", 700, 1.5) * .45, .1)
    return reverb(buf, .9, .2, tone_hz=3500)


@sfx("sfx.boss.naru.sweep", -9, "보스", "삿대 휩쓸기: 굵은 나무 장대가 크게 휘익 + 물보라 촤악(0.9초)", use="B-01: 휩쓸기 판정이 나가는 순간(맞든 안 맞든)")
def _(r):
    sec = 1.0; buf = np.zeros(int(sec * SR))
    m = int(.4 * SR); place(buf, sweep_filt(noise(m, r), "band", 300, 1100, 2) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2, 0)   # 긴 장대라 낮고 굵은 휘익
    place(buf, _splash(r, .7, 1.2), .25, .8)
    place(buf, tone(.4, 80, 50) * env(int(.4 * SR), .005, .12) * .5, .25)
    return reverb(buf, 1.0, .22, tone_hz=4000)


@sfx("sfx.boss.naru.rise", -14, "보스", "물에 빠진 혼 둘이 올라옴(전투용 짧은 판): 물이 꿀렁 솟고 뚝뚝(0.9초)", use="B-01 ①: 강물에서 혼 2마리가 올라올 때마다(컷신 cut.water.hands 보다 짧고 작게)")
def _(r):
    sec = .95; n = int(sec * SR); buf = np.zeros(n)
    m = int(.6 * SR); place(buf, sweep_filt(noise(m, r), "band", 250, 1200, 1.2) * env(m, .2, .2, 3) * .7, 0)
    place(buf, grains(.8, r, 14, lambda r, k: bubble(.1, r.uniform(250, 800), 2, .02) * r.uniform(.3, .9)), 0, .4)
    place(buf, tone(.5, 65, 50) * env(int(.5 * SR), .1, .2) * .4, .05)
    return reverb(buf, 1.0, .25, tone_hz=3000)


@sfx("sfx.boss.naru.flood", -10, "보스", "큰물: 강이 불어 바닥을 삼킴 — 낮은 우르릉 + 물이 밀려드는 쏴아아(3초, 한 번)", bypass_cast=True, use="B-01 ② 맺힘 50%: 싸울 바닥이 18m→11m로 좁아지기 시작할 때")
def _(r):
    sec = 3.2; n = int(sec * SR); t = T(sec)
    rush = sweep_filt(noise(n, r), "band", 250, 900, .7) * env(n, 1.2, 1.0, 2.5, hold=.8)
    rumble = filt(noise(n, r), "low", 120) * env(n, .6, 1.2, 2, hold=1.0) * 1.4
    lap = grains(sec, r, 40, lambda r, k: bubble(.09, r.uniform(300, 900), 1.7, .02) * r.uniform(.2, .6), t0=.8)
    return reverb(rush * .7 + rumble + lap * .35, 1.8, .3, tone_hz=2500)


@sfx("sfx.boss.naru.bigwater", -9, "보스", "큰물귀신이 생김: 흘러간 파혼 얼룩 셋이 모여 물기둥이 솟음 — 꿀렁 셋 + 쿠와아 솟구침(1.6초)", use="B-01 ②: 얼룩 3개가 모여 큰물귀신이 될 때")
def _(r):
    sec = 1.8; n = int(sec * SR); buf = np.zeros(n)
    for k in range(3): place(buf, bubble(.25, 180 + 40 * k, 1.8, .06) * .7, k * .18)   # 얼룩 셋이 하나씩 꿀렁
    m = int(1.1 * SR)
    place(buf, sweep_filt(noise(m, r), "band", 200, 1400, 1) * env(m, .25, .5, 3) * .9, .55)   # 물기둥이 위로 솟는다
    place(buf, tone(1.0, 55, 40) * env(int(1.0 * SR), .2, .4) * .7, .55)
    place(buf, _splash(r, .7, 1.0), 1.0, .5)
    return reverb(buf, 1.5, .3, tone_hz=3000)


@sfx("sfx.boss.wolhwa.warn", -12, "보스", "월화 열두 거리 예고: 요령 짤랑 + 굿판 잔들이 바르르 떨림(1초, 열릴 부채꼴 쪽 잔이 운다)", bypass_cast=True, use="B-02: 파동 예고 시작(지금 컷신용 cut.yoryeong.ring 자리)")
def _(r):
    sec = 1.1; buf = np.zeros(int(sec * SR))
    jingle = lambda r, k: modal(.4, [(f := r.uniform(2400, 3400), .12, 1), (f * 1.52, .08, .4)], r) * r.uniform(.3, .7)
    place(buf, grains(.25, r, 7, jingle), 0, .7)                                     # 방울 한 번 흔듦(짤랑)
    rattle = lambda r, k: modal(.05, [(r.uniform(1800, 2600), .015, 1), (r.uniform(3800, 4600), .01, .4)], r) * r.uniform(.15, .4)
    place(buf, grains(.75, r, 28, rattle, spread=lambda k, r: .25 + k * .026 + r.uniform(0, .01)), 0)   # 사기 잔이 받침과 부딪혀 바르르
    return reverb(buf, 1.0, .25)


@sfx("sfx.boss.wolhwa.burst", -10, "보스", "부채꼴이 열림: 오방 천 펄럭이는 바람 휙 + 무가 장구 '덩' 한 번(0.7초)", use="B-02: 예고가 끝나 부채꼴 판정이 나갈 때(파동마다 1번만)")
def _(r):
    sec = .8; buf = np.zeros(int(sec * SR))
    m = int(.35 * SR); place(buf, sweep_filt(noise(m, r), "band", 600, 2400, 1.3) * np.sin(np.pi * np.linspace(0, 1, m)) ** 1.5 * .7, 0)   # 천이 휙 펼쳐짐
    place(buf, _flutter(.35, r, np.ones(int(.35 * SR)), (12, 20), 2600) * .3, .05)
    drum = tone(.5, 150, 95) * env(int(.5 * SR), .002, .14, 3) + filt(noise(int(.5 * SR), r), "band", 900, 1) * env(int(.5 * SR), .001, .02) * .4   # 장구 북편 '덩'
    place(buf, drum, .08)
    return reverb(buf, .9, .22)


@sfx("sfx.boss.wolhwa.frenzy", -9, "보스", "월화가 몰아침: 장구가 빨라지는 덩덕덩덕덩덕 + 방울을 마구 흔듦(2초) — 이제부터 잔이 더 많이 열린다", bypass_cast=True, use="B-02 맺힘 50% 이하로 처음 내려갈 때 한 번")
def _(r):
    sec = 2.2; buf = np.zeros(int(sec * SR))
    at = 0.0; gap = .28
    for k in range(10):
        low = k % 2 == 0
        n = int(.3 * SR)
        hit = (tone(.3, 150, 95) * env(n, .002, .12, 3) if low else filt(noise(n, r), "band", 2200, 2) * env(n, .001, .03))   # 덩(북편) / 덕(채편)
        place(buf, hit * (.6 + .04 * k), at)
        at += gap; gap = max(.12, gap * .88)                                         # 점점 빨라짐 = 몰아침
    jingle = lambda r, k: modal(.3, [(f := r.uniform(2400, 3600), .1, 1), (f * 1.5, .06, .3)], r) * r.uniform(.2, .5)
    place(buf, grains(1.8, r, 30, jingle), .2, .6)
    return reverb(buf, 1.1, .25)


@sfx("sfx.boss.seo.burst", -10, "보스", "서 의원 번호 칸이 터짐: 약재 가루가 퍽 + 탕약 끓어 넘치는 지글(0.6초, 파동마다 1번)", use="B-03: 예고(cut.floor.flash) 뒤 칸들이 실제로 터질 때")
def _(r):
    sec = .7; n = int(sec * SR); buf = np.zeros(n)
    place(buf, filt(noise(n, r), "low", 2200) * env(n, .002, .09, 4), 0)              # 가루가 퍽
    place(buf, tone(.3, 110, 60) * env(int(.3 * SR), .002, .08) * .7, 0)
    sizzle = grains(.5, r, 70, lambda r, k: bubble(.02, r.uniform(1500, 4000), 1.4, .004) * r.uniform(.05, .3))   # 뜨거운 약물이 지글
    place(buf, sizzle, .05, .6)
    return reverb(buf, .7, .18)


@sfx("sfx.boss.seo.streak", -15, "보스", "파동을 피했다(약점까지 한 걸음): 약장 서랍 고리가 달칵 — 첫 번째는 낮게, 두 번째는 높게(0.3초)", use="B-03: 파동을 맞지 않고 넘겼을 때. 1번째는 pitch 1.0, 2번째는 1.25로 재생(3번째는 cut.drawer)")
def _(r):
    buf = np.zeros(int(.35 * SR))
    place(buf, modal(.25, [(1250, .05, 1), (2900, .03, .5), (620, .06, .4)], r), 0)   # 놋쇠 서랍 고리
    place(buf, _thump(r, .1, 160, 500) * .5, .03)                                     # 서랍이 살짝 들썩
    return reverb(buf, .5, .15)


@sfx("sfx.boss.seo.weak.close", -14, "보스", "약점 끝: 열렸던 약장 서랍이 탁 닫힘(0.35초) — 다시 단단해졌다", use="B-03: 약점 3초가 끝나 서랍이 닫힐 때")
def _(r):
    buf = np.zeros(int(.4 * SR))
    m = int(.12 * SR); place(buf, filt(noise(m, r), "band", 900, 1.2) * env(m, .02, .03, 3) * .5, 0)   # 드르륵 짧게
    place(buf, modal(.25, [(420, .05, 1), (980, .03, .5)], r), .1); place(buf, _thump(r, .12, 130, 400), .1)        # 탁
    return reverb(buf, .5, .12)


# ===== 날씨 환경음 보강 (비·안개·역병 안개·흐린 밤, 2026-10-25 밤) =====
# 왜: 지금은 안개와 역병 안개가 같은 'fog_night' 하나를 쓰고, 흐림은 낮이든 밤이든 'wind' 하나다.
#   역병 안개는 이동이 느려지고 서 있으면 깎이는 '해로운' 날씨라(Weather.cs) 귀로도 달라야 한다.
#   모두 반복용(loop), 크기는 기존 날씨와 같은 -23 ~ -27 근처(실제 평균 음량 -38 ~ -42dB).
@sfx("amb.weather.fog", -26, "날씨", "낮 안개: 소리가 먹힌 듯 먹먹한 공기 + 젖은 풀잎에서 물방울 + 아주 먼 까마귀 소리가 흐릿하게(반복용 14초)", loop=True, use="낮에 안개 낀 날(밤 안개는 기존 fog_night)")
def _(r):
    sec = 14.3; n = int(sec * SR); t = T(sec)
    air = filt(noise(n, r), "low", 220) * (.75 + .25 * np.sin(2 * np.pi * t / 14.3 * 2))
    hush = filt(filt(noise(n, r), "band", 900, .5), "low", 1600) * .12                 # 높은 소리가 깎인 '먹먹함'
    drips = grains(sec, r, 18, lambda r, k: bubble(.14, r.uniform(700, 1500), 1.9, .018) * r.uniform(.2, .6))
    crow = np.zeros(n)
    for at in (3.1, 3.55, 9.8):                                                     # 먼 까마귀 '까악'(안개 너머라 낮고 흐리게)
        f0 = curve(.32, [(0, 620), (.08, 700), (.3, 560)])
        place(crow, voice(f0, [(1100, 3, 1), (1800, 4, .5)], .4, r, nh=16) * env(int(.32 * SR), .02, .12, 3) * .35, at)
    crow = filt(crow, "low", 1400)
    return loopify(reverb(air + hush + drips * .3 + crow, 2.2, .4, tone_hz=1800)[:n], .5)


@sfx("amb.weather.plague", -25, "날씨", "역병 안개: 무겁게 낮게 맥놀이하는 공기 + 멀리서 앓는 기침 + 파리 웅— (반복용 16초, 서 있으면 깎이는 해로운 날씨)", loop=True, use="역병 안개(검은여울 등). 3호를 처결하면 덜 온다")
def _(r):
    sec = 16.2; n = int(sec * SR); t = T(sec)
    drone = (tone(sec, 61.0) + tone(sec, 63.2) * .8 + tone(sec, 91.8) * .35) * .25    # 가까운 두 음 = 느린 맥놀이(속이 메스꺼운 떨림)
    air = filt(noise(n, r), "low", 300) * (.7 + .3 * np.sin(2 * np.pi * t / 8.1))
    sick = filt(filt(noise(n, r), "band", 520, 2.5), "low", 900) * (.5 + .5 * np.sin(2 * np.pi * t / 5.4)) * .25   # 미지근하게 고인 공기
    fly = np.zeros(n)
    for at, dur in ((1.5, 2.2), (8.6, 1.6), (12.4, 2.4)):                           # 파리가 가까이 왔다 멀어짐
        m = int(dur * SR); tt = T(dur)
        f = 190 + 25 * np.sin(2 * np.pi * .9 * tt) + 8 * np.sin(2 * np.pi * 7 * tt)
        buzz = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
        place(fly, filt(buzz, "band", 600, 1.2) * .25, at)
    cough = np.zeros(n)
    for at in (5.2, 13.6):                                                          # 먼 기침 두 번(초가 안에서)
        for k, d in enumerate((.18, .14)):
            m = int(d * SR); src = noise(m, r) * env(m, .004, d * .5, 4)
            place(cough, (filt(src, "band", 600, 1.5) + filt(src, "band", 1600, 2.5) * .5) * (1 - .3 * k), at + k * .28)
    cough = filt(cough, "low", 1800) * .3
    return loopify(reverb(drone + air * .7 + sick + fly + cough, 2.0, .35, tone_hz=2000)[:n], .5)


@sfx("amb.weather.cloudy.night", -24, "날씨", "흐린 밤: 별 없는 하늘의 낮은 바람 웅— + 구름 너머 아주 먼 우르릉 한 번 + 먼 개 짖음 + 문풍지 떨림(반복용 18초)", loop=True, use="흐린 날 밤(낮 흐림은 기존 wind)")
def _(r):
    sec = 18.2; n = int(sec * SR); t = T(sec)
    base = filt(noise(n, r), "low", 200) * (.6 + .3 * np.sin(2 * np.pi * t / 9.1))
    gust = np.zeros(n); m = int(5.0 * SR)
    place(gust, sweep_filt(noise(m, r), "band", 250, 600, 4) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2, 4.0)
    paper = np.zeros(n); m2 = int(1.6 * SR)                                          # 돌풍에 문풍지가 바르르
    place(paper, filt(noise(m2, r), "band", 1800, 3) * (.5 + .5 * np.sign(np.sin(2 * np.pi * 23 * T(1.6)))) * np.sin(np.pi * np.linspace(0, 1, m2)) * .12, 6.0)
    thunder = np.zeros(n); m3 = int(4.0 * SR)                                        # 비 없이 구름 속에서만 우는 먼 천둥
    place(thunder, filt(noise(m3, r), "low", 110) * env(m3, .8, 1.4, 2, hold=.6) * 1.2, 11.5)
    dog = np.zeros(n)
    for k in range(3):
        f0 = curve(.2, [(0, 480), (.05, 560), (.2, 420)])
        place(dog, voice(f0, [(800, 3, 1), (1500, 4, .4)], .35, r, nh=18) * env(int(.2 * SR), .01, .08, 3) * .25, 15.0 + k * .45)
    dog = filt(dog, "low", 1200)
    return loopify(reverb(base + gust * .7 + paper + thunder + dog, 2.0, .35, tone_hz=2200)[:n], .5)


@sfx("amb.weather.rain.heavy", -21, "날씨", "큰비: 굵은 빗줄기가 쏴— 땅을 두드림 + 처마 낙숫물 줄줄 + 물웅덩이 첨벙(반복용 12초)", loop=True, use="나루 영감 보스 날(비), 비가 가장 셀 때")
def _(r):
    sec = 12.2; n = int(sec * SR); t = T(sec)
    roar = filt(filt(noise(n, r), "high", 400), "low", 7000) * (.9 + .1 * np.sin(2 * np.pi * t / 6.1))
    patter = grains(sec, r, 2600, lambda r, k: bubble(.03, r.uniform(1800, 5500), 1.3, .003) * r.uniform(.05, .45))
    eave = grains(sec, r, 160, lambda r, k: bubble(.07, r.uniform(500, 1100), 1.8, .012) * r.uniform(.2, .6))   # 처마에서 떨어지는 굵은 물
    low = filt(noise(n, r), "low", 160) * .5
    return loopify(roar * .5 + patter * .3 + eave * .25 + low, .4)


@sfx("sfx.weather.thunder.far", -12, "날씨", "먼 천둥: 쩌억 갈라지는 소리 없이 산 너머로 굴러가는 우르르릉(4초, 한 번)", use="비·큰비 중 20~60초에 한 번 무작위(화면 번쩍 없이 소리만도 가능)")
def _(r):
    sec = 4.5; n = int(sec * SR); buf = np.zeros(n)
    for k in range(5):                                                              # 산에 부딪혀 여러 번 굴러 옴
        m = int(r.uniform(.8, 1.6) * SR)
        place(buf, filt(noise(m, r), "low", r.uniform(90, 160)) * env(m, .08, .5, 2) * r.uniform(.5, 1), .1 + k * r.uniform(.4, .7))
    place(buf, filt(noise(int(.4 * SR), r), "band", 400, 1) * env(int(.4 * SR), .02, .15) * .4, .1)   # 첫 번째 울림의 결
    return reverb(buf, 2.5, .4, tone_hz=1200)


# ===== 3막 장례 대본(funerals_act3.json, 9a1ed9b) 추가 요청 10종 =====
@sfx("cut.net.shake", -15, "컷신", "그물 터는 소리: 젖은 그물을 바다 쪽으로 크게 한 번 털어 물방울이 촤르르 흩어지고 찌(나무 부표)가 달각(약 1.8초)", use="FUN-S085 갯골댁: 며느리가 기운 그물을 턴다")
def _(r):
    sec = 1.9; buf = np.zeros(int(sec * SR))
    m = int(.35 * SR); place(buf, sweep_filt(noise(m, r), "band", 500, 1600, 1.2) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2 * .6, 0)   # 그물이 휙 들림
    place(buf, filt(noise(int(.12 * SR), r), "low", 1500) * env(int(.12 * SR), .002, .04) * .9, .32)                               # 털리는 순간 퍽(젖은 삼베 그물)
    place(buf, grains(1.2, r, 110, lambda r, k: bubble(.03, r.uniform(1500, 5000), 1.3, .004) * r.uniform(.05, .35), spread=lambda k, r: r.uniform(0, 1) ** 2 * 1.1), .34)   # 물방울 촤르르(처음에 몰림)
    for k in range(3): place(buf, modal(.12, [(r.uniform(700, 1100), .03, 1), (r.uniform(1800, 2400), .015, .4)], r) * .4, .36 + k * .09)   # 찌가 서로 달각
    return reverb(buf, 1.0, .2)


@sfx("cut.shovel.dig", -15, "컷신", "삽질: 젖은 흙에 삽날이 서걱 박히고 푹 퍼서 휙 던지면 흙이 툭 쏟아짐 × 네 번(약 6초)", use="FUN-S086 헛묘지기 영감: 손자가 몸이 든 무덤을 짓는다")
def _(r):
    sec = 6.2; buf = np.zeros(int(sec * SR)); at = .1
    for k in range(4):
        place(buf, modal(.15, [(r.uniform(1900, 2400), .03, 1), (r.uniform(3600, 4400), .015, .4)], r) * .35, at)   # 삽날이 돌에 살짝 쨍
        m = int(.18 * SR); place(buf, filt(noise(m, r), "band", 700, 1) * env(m, .005, .05) * .8, at)                  # 흙에 서걱 박힘
        place(buf, tone(.12, 90, 60) * env(int(.12 * SR), .002, .03) * .5, at + .02)                                    # 발로 삽을 밟아 푹
        m2 = int(.3 * SR); place(buf, filt(noise(m2, r), "band", 1100, .8) * env(m2, .05, .08, 3, hold=.1) * .35, at + .45)   # 퍼 올림
        place(buf, grains(.4, r, 40, lambda r, k: filt(noise(int(.008 * SR), r), "band", r.uniform(500, 1600), 2) * env(int(.008 * SR), .0005, .003) * r.uniform(.2, .8)), at + .95)   # 흙이 툭 쏟아짐
        place(buf, tone(.15, 80, 55) * env(int(.15 * SR), .003, .05) * .4, at + .95)
        at += 1.45 + r.uniform(-.1, .15)
    return reverb(buf, .6, .12)


@sfx("cut.salt.scatter", -17, "컷신", "소금 한 줌 흩기: 손안에서 사각 쥐었다가 쏴— 흩어져 물에 떨어지는 자잘한 소리(약 2.5초, 파도는 amb.harbor가 깐다)", use="FUN-S087 소금장수 덕보: 이웃 염부가 바다에 소금을 뿌린다")
def _(r):
    sec = 2.6; buf = np.zeros(int(sec * SR))
    place(buf, grains(.35, r, 50, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(2500, 5000), 3) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .5)), 0)   # 손안 소금 알갱이 사각
    m = int(.4 * SR); place(buf, filt(filt(noise(m, r), "high", 1500), "low", 6000) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2 * .3, .5)   # 팔을 휘둘러 흩음: 쏴
    rain = lambda r, k: bubble(.015, r.uniform(2200, 5000), 1.25, .0025) * r.uniform(.05, .3)
    place(buf, grains(1.4, r, 380, rain, spread=lambda k, r: r.uniform(0, 1) ** .7 * 1.3), .75)   # 수면에 자잘하게 쏟아짐
    return reverb(buf, 1.2, .2)


@sfx("cut.oar.row", -15, "컷신", "노 젓기: 노가 놋좆(나무 받침)에 끼익 + 물을 꿀렁 밀고 빠질 때 찰랑 — 다섯 번, 점점 가까워짐(약 7초)", use="FUN-S088 순덕: 포구로 배 한 척이 들어온다")
def _(r):
    sec = 7.2; buf = np.zeros(int(sec * SR)); at = .2
    for k in range(5):
        near = .45 + .55 * k / 4                                                     # 점점 가까워진다
        cr = tone(.35, 330, 260) * (1 + .7 * np.sign(np.sin(2 * np.pi * 45 * T(.35)))) * env(int(.35 * SR), .05, .15, 3, hold=.1)
        place(buf, filt(cr, "band", 900, 2) * .3 * near, at)                         # 나무 끼익
        m = int(.5 * SR); place(buf, sweep_filt(noise(m, r), "band", 300, 900, 1.2) * env(m, .08, .2, 3) * .6 * near, at + .25)   # 물을 밀어냄
        place(buf, grains(.4, r, 12, lambda r, k: bubble(.06, r.uniform(600, 1800), 1.6, .01) * r.uniform(.2, .6)), at + .65, near)   # 빠질 때 찰랑
        at += 1.35
    return reverb(buf, 1.4, .3, tone_hz=3500)


@sfx("cut.lamp.snuff", -18, "컷신", "등잔 심지 끄기: 작은 불꽃이 파르르 하다 '훅' 하고 꺼지고 연기가 쉬— 가늘게(약 1.6초)", use="FUN-S089 등대지기: 딸이 등잔을 끈다(아침이니까)")
def _(r):
    sec = 1.7; n = int(sec * SR); buf = np.zeros(n)
    m = int(.5 * SR); place(buf, filt(noise(m, r), "band", 600, 1) * (.5 + .5 * np.sin(2 * np.pi * 11 * T(.5))) * env(m, .05, .2, 3, hold=.2) * .35, 0)   # 불꽃이 파르르
    m2 = int(.18 * SR); place(buf, filt(noise(m2, r), "low", 900) * env(m2, .01, .06, 3) * .9, .5)   # 훅(숨 또는 심지 누르개)
    m3 = int(1.0 * SR); place(buf, filt(noise(m3, r), "band", 3500, 2) * env(m3, .1, .5, 3) * .12, .6)   # 연기 쉬—
    return reverb(buf, .7, .15)


@sfx("cut.kids.steps", -15, "컷신", "아이들 맨발 발소리: 무거운 상여를 메고 비틀비틀 → 아이들이 더 달려와(넷이 여덟) → 발이 하나로 맞아 착 착(약 8초)", use="FUN-S103 떡장수 할미: 다리 밑 아이들이 상여를 멘다")
def _(r):
    sec = 8.2; buf = np.zeros(int(sec * SR))
    def bare(r, g):
        m = int(.08 * SR)
        return g * (tone(.08, r.uniform(130, 170), 90) * env(m, .002, .015) * .7 + filt(noise(m, r), "band", r.uniform(900, 1500), 1.2) * env(m, .001, .012) * .5)   # 맨발: 흙에 착(높고 가볍게)
    at = .1                                                                          # ① 넷이 비틀거림: 박자가 제각각
    while at < 3.0:
        place(buf, bare(r, r.uniform(.5, .9)), at + r.uniform(-.05, .05)); at += r.uniform(.18, .38)
    for k in range(10):                                                              # ② 더 달려오는 아이들: 빠른 잰걸음, 멀리서 가까이
        place(buf, bare(r, .25 + .05 * k), 2.6 + k * .12 + r.uniform(0, .02))
    for k in range(9):                                                               # ③ 여덟이 발을 맞춤: 같은 박자에 여러 발(조금씩 어긋나 두께가 생김)
        t0 = 4.4 + k * .42
        for j in range(8): place(buf, bare(r, .22), t0 + r.uniform(0, .025))
    return reverb(buf, .6, .12)


@sfx("amb.market.hush", -24, "세계", "웅성거림이 잦아드는 장터: 장터 소리가 한 사람씩 말을 멈추며 줄어들고, 마지막엔 그릇 하나 달그락과 먼 바람만(약 9초, 한 번)", use="FUN-S104 짐꾼 곰: 지게가 지나가자 장터가 조용해짐(amb.market 위에서 갈아 끼움)")
def _(r):
    base = _base("amb.market")[: int(9.0 * SR)]
    n = len(base); t = np.arange(n) / SR
    base = base / (np.abs(base).max() + 1e-9)
    hush = np.clip(1 - (t - 1.0) / 5.5, 0, 1) ** 1.6                                  # 1초부터 6.5초까지 점점 잦아듦
    dull = filt(base, "low", 1200)                                                   # 잦아들수록 높은 소리부터 사라짐(먹먹해짐)
    y = base * hush * (t < 3.5) + dull * hush * (t >= 3.5) * 1.1
    y = y * 1.0 + filt(noise(n, r), "low", 300) * .06                                 # 남는 바람
    place(y, modal(.4, [(2300, .08, 1), (4200, .04, .3)], r) * .25, 7.2)                # 마지막 그릇 하나 달그락
    return y


@sfx("cut.needle.sew", -19, "컷신", "바느질: 바늘이 무명을 톡 뚫고 실이 스르륵 당겨짐 × 여섯 땀, 마지막에 실을 이로 끊음(약 6초)", use="FUN-S105 움막촌 어미: 배냇저고리 안에 아이 이름을 바느질")
def _(r):
    sec = 6.2; buf = np.zeros(int(sec * SR)); at = .2
    for k in range(6):
        place(buf, filt(noise(int(.006 * SR), r), "band", 3800, 3) * env(int(.006 * SR), .0003, .002) * .6, at)   # 바늘이 천을 톡
        m = int(r.uniform(.45, .7) * SR)
        place(buf, filt(filt(noise(m, r), "high", 2500), "low", 7000) * env(m, .05, .1, 3, hold=m / SR * .5) * .22, at + .08)   # 실이 천을 스르륵
        at += m / SR + r.uniform(.25, .4)
    m = int(.05 * SR); place(buf, filt(noise(m, r), "band", 2000, 2) * env(m, .001, .01) * .5, at + .2)   # 실을 이로 툭 끊음
    return reverb(buf, .35, .08)


@sfx("cut.charcoal.draw", -17, "컷신", "숯으로 돌기둥에 그리기: 숯이 거친 돌을 긁는 사각사각 — 꽃잎 다섯 번 짧게 + 줄기 한 번 길게, 숯가루 톡(약 4.5초)", use="FUN-S106 쥐똥이: 아이들이 다리 기둥 별명 옆에 꽃을 그린다")
def _(r):
    sec = 4.6; buf = np.zeros(int(sec * SR)); at = .15
    def stroke(r, d):
        m = int(d * SR)
        grit = grains(d, r, int(d * 220), lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(1500, 4000), 2) * env(int(.003 * SR), .0002, .001) * r.uniform(.2, .8))
        rub = filt(noise(m, r), "band", 1100, 1.5) * .3
        return (grit + rub) * env(m, .02, .05, 3, hold=d * .6)
    for k in range(5): place(buf, stroke(r, r.uniform(.22, .32)), at); at += .45            # 꽃잎 다섯
    place(buf, stroke(r, .9), at + .2)                                                      # 줄기 길게
    place(buf, grains(.3, r, 6, lambda r, k: filt(noise(int(.004 * SR), r), "band", 2500, 2) * env(int(.004 * SR), .0003, .0015) * .4), at + 1.2)   # 숯가루 떨어짐
    return reverb(buf, .6, .15)


@sfx("cut.gate.creak", -13, "컷신", "큰 나무 성문: 무거운 문짝이 끼이이익 길게 돌다가 멈춤(빗장 쥔 채 잠깐) → 다시 조금 → 틈으로 누가 뛰어 들어오는 발소리 다다닥(약 7초)", use="FUN-S107 성문 문지기: 아들이 문을 조금 늦게 닫는다")
def _(r):
    sec = 7.2; buf = np.zeros(int(sec * SR))
    def creak(d, f0, f1):
        m = int(d * SR); tt = T(d)
        f = np.linspace(f0, f1, m) * (1 + .08 * np.sin(2 * np.pi * 3 * tt))
        stick = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .6).astype(float)             # 나무가 걸렸다 미끄러짐(스틱-슬립)
        y = filt(stick - stick.mean(), "band", 650, 2) + filt(stick - stick.mean(), "band", 1500, 3) * .4
        return y * env(m, .15, .3, 3, hold=d - .5)
    place(buf, creak(2.4, 38, 26), 0)                                                # 끼이이익(문짝이 돈다)
    place(buf, tone(.6, 60, 45) * env(int(.6 * SR), .05, .3) * .5, .1)               # 큰 문짝의 낮은 무게
    place(buf, modal(.5, [(780, .1, 1), (1650, .06, .5)], r) * .3, 2.5)              # 빗장 쇠가 손에서 달칵(멈춤)
    place(buf, creak(.9, 30, 24) * .8, 3.9)                                          # 조금 더 닫힘
    for k in range(9):                                                               # 틈으로 뛰어 들어오는 발소리(멀리 → 가까이)
        m = int(.1 * SR)
        st = tone(.1, r.uniform(95, 120), 60) * env(m, .002, .02) + filt(noise(m, r), "band", 1800, 1) * env(m, .001, .02) * .4
        place(buf, st * (.25 + .07 * k), 5.0 + k * .2)
    return reverb(buf, 1.2, .25, tone_hz=3500)


# ===== 3막 보스 전투 소리 (B-09 망부석 아낙 · B-10 만선호 선장 · B-11 다리 밑 왕초 · B-12 흑월 2차, SCENARIO-ACT3) =====
@sfx("sfx.boss.mangbu.call", -11, "보스", "망부석 아낙이 바다를 부름: 여인이 길게 부르는 소리(말뜻 없음, '오—') + 먼 바다가 웅 하고 답함(2.2초) — 곧 파도가 줄지어 온다", bypass_cast=True, use="B-09: 파도 장판 예고 시작")
def _(r):
    sec = 2.4; n = int(sec * SR); buf = np.zeros(n)
    f0 = curve(1.8, [(0, 330), (.2, 392), (1.2, 380), (1.8, 300)]) * (1 + .012 * np.sin(2 * np.pi * 5.5 * T(1.8)))
    v = voice(f0, [(500, 4, 1), (900, 5, .5), (2800, 8, .15)], .25, r, nh=24) * env(int(1.8 * SR), .15, .5, 3, hold=.9)
    place(buf, v * .6, 0)
    place(buf, filt(noise(n, r), "low", 160) * env(n, .8, .8, 2, hold=.4) * 1.2, .3)   # 바다가 낮게 웅
    return reverb(buf, 2.2, .4, tone_hz=2500)


@sfx("sfx.boss.mangbu.wave", -10, "보스", "파도 장판: 큰 파도가 밀려와 바위에 촤아악 부서지며 물보라가 시야를 덮음(1.8초, 줄마다 1번)", use="B-09: 파도 한 줄이 덮칠 때")
def _(r):
    sec = 2.0; buf = np.zeros(int(sec * SR))
    place(buf, _wave(r, 1.8, 1.4), 0)
    place(buf, tone(.6, 70, 45) * env(int(.6 * SR), .01, .2) * .6, .8)                 # 바위에 부딪히는 둔한 쿵
    return reverb(buf, 1.4, .3, tone_hz=4000)


@sfx("sfx.boss.mangbu.cloth.throw", -16, "보스", "옷을 바다에 던지려 함: 젖은 옷이 크게 휘둘려 펄럭 + 낮게 떨리는 경고음(2초 동안 — 이 사이 사슬로 낚아채라)", bypass_cast=True, use="B-09 맺힘 50%: 2초 낚아채기 창이 열릴 때")
def _(r):
    sec = 2.1; n = int(sec * SR); buf = np.zeros(n)
    g = np.clip(np.sin(np.pi * np.linspace(0, 1, n)) * 1.2, 0, 1)
    place(buf, _flutter(sec, r, g, (5, 10), 1500) * .5, 0)                           # 젖은 천이라 느리고 무겁게 펄럭
    t = T(sec); place(buf, (tone(sec, 98) + tone(sec, 100.5)) * (.3 + .7 * t / sec) * .25, 0)   # 낮은 맥놀이가 점점 커짐 = 남은 시간
    return reverb(buf, 1.0, .25)


@sfx("sfx.boss.mangbu.cloth.catch", -10, "보스", "옷을 낚아챔: 사슬이 차르르 날아가 젖은 천을 휘감아 툭 당겨 옴 + 맑은 방울 하나(1.2초, 맺힘 −15%)", use="B-09: 2초 안에 사슬로 옷을 낚아챘을 때")
def _(r):
    sec = 1.3; buf = np.zeros(int(sec * SR))
    link = lambda r, k: modal(.1, [(r.uniform(2600, 4200), .02, 1), (r.uniform(5000, 7000), .01, .4)], r) * .5
    place(buf, grains(.35, r, 10, link, spread=lambda k, r: k * .03), 0)               # 사슬 날아감
    place(buf, filt(noise(int(.15 * SR), r), "low", 1200) * env(int(.15 * SR), .003, .05) * .8, .35)   # 젖은 천을 감아 툭
    place(buf, modal(.9, [(1318.5, .35, 1), (2637, .15, .3)], r) * .4, .45)              # E6 맑게(잘했다)
    return reverb(buf, 1.0, .25)


@sfx("sfx.boss.seonjang.tilt", -12, "보스", "갑판이 기움: 큰 배 나무가 우지끈 끼익 + 갑판 위 물이 한쪽으로 쏴 쏠림(2초) — 미끄러진다", bypass_cast=True, use="B-10: 갑판이 좌우로 기울기 시작할 때마다")
def _(r):
    sec = 2.2; n = int(sec * SR); buf = np.zeros(n)
    m = int(1.6 * SR); tt = T(1.6)
    f = np.linspace(48, 34, m); stick = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .7).astype(float)
    place(buf, (filt(stick - stick.mean(), "band", 420, 2) + filt(stick - stick.mean(), "band", 950, 3) * .4) * env(m, .2, .4, 3, hold=.8) * .7, 0)   # 선체 끼익
    place(buf, sweep_filt(noise(int(1.4 * SR), r), "band", 400, 1200, 1) * env(int(1.4 * SR), .4, .4, 3) * .5, .4)   # 물이 쏠림
    place(buf, tone(.8, 55, 40) * env(int(.8 * SR), .1, .3) * .5, .1)
    return reverb(buf, 1.3, .3, tone_hz=3000)


@sfx("sfx.boss.seonjang.rope.telegraph", -12, "보스", "줄 끊기 예고: 젖은 밧줄을 머리 위로 휘휘 돌리는 소리(점점 빨라짐, 1초)", bypass_cast=True, use="B-10: 직선 장판 예고 시작")
def _(r):
    sec = 1.1; buf = np.zeros(int(sec * SR)); at = 0; gap = .32
    while at < 1.0:
        m = int(.2 * SR); place(buf, sweep_filt(noise(m, r), "band", 400, 1300, 2) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2 * .6, at)
        at += gap; gap *= .78
    return reverb(buf, .7, .15)


@sfx("sfx.boss.seonjang.rope.cut", -9, "보스", "줄 끊기: 팽팽한 밧줄이 툭! 끊어지며 채찍처럼 휘익 일직선으로(0.8초)", use="B-10: 직선 장판 판정이 나갈 때")
def _(r):
    sec = .9; buf = np.zeros(int(sec * SR))
    place(buf, modal(.15, [(180, .04, 1), (410, .03, .6), (950, .02, .3)], r), 0)   # 굵은 줄이 끊기는 둔한 툭
    place(buf, filt(noise(int(.04 * SR), r), "low", 3000) * env(int(.04 * SR), .0005, .01) * .9, 0)
    m = int(.4 * SR); place(buf, sweep_filt(noise(m, r), "band", 2400, 700, 2.5) * env(m, .005, .15, 3) * .7, .03)   # 휘익(높→낮)
    return reverb(buf, .8, .2)


@sfx("sfx.boss.seonjang.crew.fall", -14, "보스", "선원 혼이 바다로 떨어짐: 짧은 외마디(말뜻 없음)가 멀어지고 아래에서 첨벙(1.2초)", use="B-10: 줄 끊기 장판이 난간의 선원 혼을 지나갈 때")
def _(r):
    sec = 1.3; buf = np.zeros(int(sec * SR))
    place(buf, filt(_shout(r, .45, 260, 150, "o", .4), "low", 2500) * .5, 0)
    place(buf, _splash(r, .6, .8), .55, .6)
    return reverb(buf, 1.3, .3, tone_hz=2800)


@sfx("sfx.boss.wangcho.call", -11, "보스", "왕초가 별명을 부름: 거친 사내가 짧게 두 번 부르는 소리(말뜻 없음) + 목걸이 나무 조각들이 달그락(1.3초)", use="B-11: 별명을 불러 무적 혼을 일으킬 때")
def _(r):
    sec = 1.4; buf = np.zeros(int(sec * SR))
    place(buf, _shout(r, .32, 210, 160, "a", .45) * .6, 0); place(buf, _shout(r, .38, 230, 150, "o", .45) * .6, .4)
    clack = lambda r, k: modal(.06, [(r.uniform(900, 1500), .015, 1), (r.uniform(2400, 3200), .008, .4)], r) * r.uniform(.2, .5)
    place(buf, grains(.5, r, 12, clack), .8)                                         # 나무 조각 목걸이 달그락
    return reverb(buf, .9, .25)


@sfx("sfx.boss.wangcho.rise", -14, "보스", "이름 불린 혼이 일어남: 거적·누더기가 바스락 + 낮게 웅 (0.9초)", use="B-11: 별명이 불린 무적 혼이 일어나 협공할 때")
def _(r):
    sec = 1.0; n = int(sec * SR); buf = np.zeros(n)
    place(buf, _crinkle(r, .6, 25, (800, 3000), (.2, .7)), 0)
    place(buf, filt(noise(int(.5 * SR), r), "band", 600, 1) * env(int(.5 * SR), .1, .2, 3) * .4, 0)
    place(buf, tone(.7, 80, 70) * env(int(.7 * SR), .2, .3) * .4, .1)
    return reverb(buf, 1.0, .25)


@sfx("sfx.boss.wangcho.turn", -14, "보스", "낮에 들은 별명의 혼이 나를 돌아봄: 일어나다 멈추는 숨 + 따뜻한 낮은 방울 하나(1.2초) — 이 혼은 지금 바로 천도할 수 있다", use="B-11: 왕초가 불렀는데 플레이어가 아는 별명이라 일어나지 않을 때")
def _(r):
    sec = 1.3; buf = np.zeros(int(sec * SR))
    m = int(.4 * SR); place(buf, sweep_filt(noise(m, r), "band", 1200, 700, 2) * env(m, .1, .2, 3) * .25, 0)   # 숨이 멈춤
    place(buf, modal(1.1, [(587.3, .5, 1), (1174.7, .25, .35), (1761, .1, .15)], r) * .5, .25)   # D5 낮고 따뜻한 방울
    return reverb(buf, 1.2, .3)


@sfx("sfx.boss.heukwol.steal", -11, "보스", "흑월이 내 혼을 먼저 천도해 감: 천도 방울이 거꾸로 내려가며 넋이 그쪽으로 쓸려감 + 먼 사슬 차르르(1.4초)", use="B-12 ① 두 차사: 내가 고르던 혼을 흑월이 가로챌 때")
def _(r):
    sec = 1.5; buf = np.zeros(int(sec * SR))
    for k, f in enumerate([1568, 1318.5, 1046.5, 784]):                              # 위에서 아래로 = 내 것이 아니라 그쪽으로
        place(buf, modal(.6, [(f, .25, 1), (f * 2.01, .1, .3)], r) * .35, k * .12)
    m = int(.9 * SR); place(buf, sweep_filt(noise(m, r), "band", 2500, 600, 1.5) * env(m, .2, .4, 3) * .3, .2)   # 넋이 쓸려감
    place(buf, filt(grains(.5, r, 10, lambda r, k: modal(.08, [(r.uniform(2600, 4000), .02, 1)], r) * .3), "low", 3000), .8)   # 먼 사슬
    return reverb(buf, 1.6, .35)


@sfx("sfx.boss.heukwol.line.draw", -11, "보스", "명단 줄 긋기: 사슬 끝이 눈밭을 길게 스으윽 긁고 줄 끝에서 낮게 웅(1.3초, 줄마다 1번)", bypass_cast=True, use="B-12 ② 명단: 가로줄 장판이 하나 생길 때")
def _(r):
    sec = 1.4; n = int(sec * SR); buf = np.zeros(n)
    m = int(1.0 * SR)
    snow = filt(filt(noise(m, r), "high", 900), "low", 5000) * env(m, .05, .2, 3, hold=.6) * .5   # 눈이 긁힘(부드러운 사각)
    links = grains(1.0, r, 20, lambda r, k: modal(.05, [(r.uniform(2400, 3600), .012, 1)], r) * r.uniform(.1, .3))
    place(buf, snow + links, 0)
    place(buf, (tone(.6, 110) + tone(.6, 111.8)) * env(int(.6 * SR), .05, .3) * .35, .85)   # 이 줄은 밟지 마라
    return reverb(buf, 1.4, .3)


@sfx("sfx.boss.heukwol.line.drain", -20, "보스", "줄 위에 섬(넋이 샘): 먹이 번지듯 쉬— 하는 바람 + 아주 천천히 내려가는 가는 음(반복용 2초) — 서 있는 동안만", loop=True, bypass_cast=True, use="B-12 ②: 플레이어가 줄 위에 있는 동안 반복, 벗어나면 0.2초에 끔")
def _(r):
    sec = 2.0; n = int(sec * SR); t = T(sec)
    hiss = filt(noise(n, r), "band", 1800, 1.2) * (.6 + .4 * np.sin(2 * np.pi * t / sec)) * .5
    fall = np.sin(2 * np.pi * np.cumsum(np.linspace(880, 830, n)) / SR) * .15     # 이름이 지워지는 가는 음(느리게 내려감)
    return loopify(hiss + fall + filt(noise(n, r), "low", 200) * .2, .25)


@sfx("sfx.boss.heukwol.flood", -10, "보스", "큰물이 다시 옴: 눈이 비로 바뀌는 쏴— + 성문 밖이 물에 잠기는 우르릉(3.5초, 한 번) — 그 밤의 재현", bypass_cast=True, use="B-12 ③ 큰물: 맺힘 40%에서 무대가 바뀔 때")
def _(r):
    sec = 3.6; n = int(sec * SR); buf = np.zeros(n)
    place(buf, filt(filt(noise(n, r), "high", 600), "low", 7000) * np.clip(T(sec) / 1.5, 0, 1) * .35, 0)   # 비가 점점 굵어짐
    m = int(2.6 * SR); place(buf, sweep_filt(noise(m, r), "band", 250, 800, .7) * env(m, 1.0, .9, 2.5, hold=.6) * .7, .8)
    place(buf, filt(noise(m, r), "low", 120) * env(m, .5, 1.0, 2, hold=.8) * 1.2, .8)
    return reverb(buf, 2.0, .35, tone_hz=2500)


@sfx("sfx.boss.heukwol.chain.down", -12, "보스", "흑월이 사슬을 내려놓음: 무거운 사슬이 눈밭에 차르르 천천히 내려앉고 — 고요 — 먼 새벽 바람(3초)", bypass_cast=True, use="B-12 ④ 맺힘 15%: 그가 사슬을 내려놓을 때(BGM은 이때 줄이기)")
def _(r):
    sec = 3.2; n = int(sec * SR); buf = np.zeros(n)
    link = lambda r, k: modal(.15, [(r.uniform(2200, 3800), .03, 1), (r.uniform(4500, 6500), .015, .4), (r.uniform(300, 500), .04, .3)], r) * (1 - k / 22) * .6
    place(buf, grains(1.2, r, 18, link, spread=lambda k, r: (k / 18) ** 1.5 * 1.1 + r.uniform(0, .02)), 0)   # 사슬이 천천히 내려앉음(점점 느려짐)
    place(buf, filt(noise(int(.3 * SR), r), "low", 800) * env(int(.3 * SR), .01, .1) * .4, 1.1)            # 눈에 푹 묻힘
    m = int(1.6 * SR); place(buf, filt(noise(m, r), "band", 500, .6) * env(m, .6, .6, 2, hold=.3) * .2, 1.6)   # 새벽 바람
    return reverb(buf, 2.4, .35, tone_hz=3000)


# ===== 시즌1 컷신 44컷(cutscenes_s1.json, bf5edb4) 요청 16종 + 빈 박자 채우기 9종 (2026-10-25 밤) =====
# 요청 16종은 대본 sfx_request 이름 그대로 → 서사 쪽 sfx_map.promote 가 다음 생성 때 sfx 로 옮긴다.
# 채우기 9종은 소리 없던 박자용(data/cutscene_audio_s1.json 이 박자에 붙인다).
def _bird(r, f0=3200, n=3):
    """새 한 마리 짹짹: 위로 휘는 짧은 휘파람 몇 번"""
    buf = np.zeros(int(.12 * n * SR + .3 * SR))
    for k in range(n):
        d = r.uniform(.05, .09); m = int(d * SR)
        f = np.linspace(f0 * r.uniform(.9, 1.0), f0 * r.uniform(1.15, 1.35), m)
        place(buf, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(m, .005, d * .4, 3) * r.uniform(.5, 1), k * r.uniform(.1, .14))
    return buf


@sfx("cut.soldier.rise", -13, "컷신", "갑옷 혼이 땅에서 일어남: 흙이 갈라지는 바스락 + 녹슨 미늘(갑옷 쇳조각)이 철컥철컥 맞물림 + 낮은 웅(1.6초)", use="B05-INTRO 2.4: 대돌이 입을 열 때마다 병사 혼이 일어남")
def _(r):
    sec = 1.7; buf = np.zeros(int(sec * SR))
    place(buf, grains(.6, r, 30, lambda r, k: filt(noise(int(.008 * SR), r), "band", r.uniform(500, 1400), 2) * env(int(.008 * SR), .0005, .003) * r.uniform(.2, .7)), 0)   # 흙 갈라짐
    scale = lambda r, k: modal(.08, [(r.uniform(1500, 2600), .02, 1), (r.uniform(3200, 4800), .01, .4)], r) * r.uniform(.2, .5)
    place(buf, grains(.8, r, 16, scale, spread=lambda k, r: .3 + k * .05 + r.uniform(0, .02)), 0)   # 미늘 철컥철컥
    place(buf, tone(1.2, 75, 62) * env(int(1.2 * SR), .3, .4) * .5, .2)
    return reverb(buf, 1.0, .25)


@sfx("cut.stone.carve", -15, "컷신", "봉분 돌에 이름이 새겨짐: 정 소리가 아니라 빛이 돌을 파고드는 낮은 '스으' + 돌가루 바스락이 위에서 아래로 줄마다(2초)", use="B05-TENDO 3.5: 봉분에 이름들이 한 줄씩 새겨짐")
def _(r):
    sec = 2.2; buf = np.zeros(int(sec * SR))
    for k in range(4):
        m = int(.35 * SR)
        place(buf, filt(noise(m, r), "band", 900 - k * 120, 3) * env(m, .05, .12, 3, hold=.15) * .5, k * .45)   # 줄마다 낮아짐(위→아래)
        place(buf, grains(.3, r, 10, lambda r, j: filt(noise(int(.004 * SR), r), "band", r.uniform(2000, 4500), 2) * env(int(.004 * SR), .0003, .0015) * r.uniform(.1, .4)), k * .45 + .1)
    place(buf, tone(2.0, 98) * env(int(2.0 * SR), .5, .8) * .2, 0)
    return reverb(buf, 1.6, .3)


@sfx("cut.war.drum", -9, "컷신", "큰 북 한 번: 진중 북이 둥— 깊게 울리고 군막 터에 퍼짐(2초)", use="B06-INTRO 1.6·3.0: 장수의 북(3.0은 두 번 틀기)")
def _(r):
    sec = 2.2; n = int(sec * SR)
    hit = tone(sec, 72, 48) * env(n, .003, .55, 3) + filt(noise(n, r), "low", 500) * env(n, .001, .04) * .5
    skin = filt(noise(n, r), "band", 220, 2) * env(n, .002, .12) * .3                   # 소가죽 떨림
    return reverb(hit + skin, 2.0, .3, tone_hz=1500)


@sfx("cut.tag.drop", -16, "컷신", "나무패가 땅에 떨어짐: 끈이 툭 풀리고 패가 흙에 탁 — 한 번 튐(0.6초). 북채·작은 나무 물건에도 씀", use="B06-TENDO 3.0(여러 번 틀기) · B06-KNEEL 북채")
def _(r):
    buf = np.zeros(int(.7 * SR))
    place(buf, filt(noise(int(.03 * SR), r), "band", 1800, 2) * env(int(.03 * SR), .001, .01) * .3, 0)   # 끈 풀림
    place(buf, modal(.2, [(r.uniform(900, 1200), .04, 1), (r.uniform(2200, 2700), .02, .5)], r), .12)
    place(buf, modal(.15, [(r.uniform(900, 1200), .03, 1)], r) * .35, .25)            # 한 번 튐
    return reverb(buf, .5, .12)


@sfx("amb.sea.wind", -26, "컷신", "먼 바닷바람: 막혔던 갱도 끝으로 들어오는 서늘한 바람 + 아주 먼 파도 쏴— (반복용 10초)", loop=True, use="B07-TENDO 5.0: 갱도 끝이 열려 바다 바람이 들어옴(컷 끝까지)")
def _(r):
    sec = 10.2; n = int(sec * SR); t = T(sec)
    wind = sweep_filt(noise(n, r), "band", 400, 700, 3) * (.6 + .4 * np.sin(2 * np.pi * t / 5.1))
    tunnel = filt(noise(n, r), "band", 180, 4) * .5                                    # 갱도가 낮게 울림
    surf = filt(noise(n, r), "low", 900) * (.5 + .5 * np.sin(2 * np.pi * t / 10.2) ** 2) * .35
    return loopify(reverb(wind * .6 + tunnel + surf, 1.5, .3, tone_hz=2500)[:n], .5)


@sfx("cut.wave.row", -12, "컷신", "줄지어 밀려오는 파도: 먼 바다에서 파도 셋이 차례로 일어나 점점 커짐(4초)", use="B09-INTRO 2.8: 파도마다 물 혼 하나씩")
def _(r):
    sec = 4.6; buf = np.zeros(int(sec * SR))
    for k in range(3): place(buf, filt(_wave(r, 2.0, .7 + .25 * k), "low", 2500 + 1200 * k) * (.45 + .25 * k), k * 1.1)   # 멀리→가까이: 점점 밝고 크게
    return reverb(buf, 1.8, .35, tone_hz=3000)


@sfx("cut.hull.creak", -14, "컷신", "배 몸체 삐걱: 반쯤 가라앉은 큰 배가 기울며 길게 끼이익 — 끝에 물이 선체를 철썩(3초)", use="B10-INTRO 0.0(2.6에 한 번 더): 기운 갑판")
def _(r):
    sec = 3.2; buf = np.zeros(int(sec * SR))
    m = int(2.2 * SR); f = np.linspace(42, 30, m); stick = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .65).astype(float)
    place(buf, (filt(stick - stick.mean(), "band", 380, 2) + filt(stick - stick.mean(), "band", 880, 3) * .4) * env(m, .3, .5, 3, hold=1.2) * .8, 0)
    place(buf, _splash(r, .7, .7) * .5, 2.2)
    return reverb(buf, 1.4, .3, tone_hz=3000)


@sfx("cut.rope.untie", -16, "컷신", "젖은 매듭이 풀림: 굵은 밧줄이 스르륵 미끄러지고 매듭이 툭 빠짐(0.8초, 일곱 번 틀기)", use="B10-TENDO 4.0: 이름을 부를 때마다 매듭 하나씩")
def _(r):
    buf = np.zeros(int(.9 * SR))
    m = int(.45 * SR); place(buf, filt(noise(m, r), "band", 700, 1.5) * env(m, .05, .15, 3, hold=.15) * .5, 0)   # 젖은 줄 스르륵
    place(buf, tone(.12, 140, 90) * env(int(.12 * SR), .002, .03) * .6, .45)            # 매듭이 툭
    place(buf, grains(.3, r, 4, lambda r, k: bubble(.05, r.uniform(1200, 2200), 1.5, .008) * .3), .5)   # 물기 뚝
    return reverb(buf, .7, .15)


@sfx("cut.soul.rise", -16, "컷신", "혼이 일어남: 거적 아래에서 낮게 들이쉬는 숨 '흐으' + 천이 스르륵(1.2초, 말소리 없음)", use="B11-INTRO 1.4·2.6: 거적 사이에서 혼이 일어나 왕초를 돌아봄")
def _(r):
    sec = 1.3; n = int(sec * SR); buf = np.zeros(n)
    m = int(.8 * SR); place(buf, sweep_filt(noise(m, r), "band", 500, 1100, 2) * env(m, .35, .25, 3) * .5, 0)   # 들이쉬는 숨
    place(buf, _crinkle(r, .5, 12, (900, 2500), (.15, .4)), .3)
    return reverb(buf, 1.0, .25)


@sfx("amb.snow.wind", -26, "컷신", "눈밭 바람: 성문 밖 언 들판 — 낮고 찬 바람 휘— + 눈발이 사락사락 + 아무것도 없는 고요(반복용 14초)", loop=True, use="B12-INTRO 0.0 · C-12B 20.0(빈 눈밭)")
def _(r):
    sec = 14.2; n = int(sec * SR); t = T(sec)
    base = filt(noise(n, r), "low", 220) * (.6 + .3 * np.sin(2 * np.pi * t / 7.1))
    whistle = np.zeros(n); m = int(4.5 * SR)
    place(whistle, sweep_filt(noise(m, r), "band", 700, 1100, 9) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2 * .35, 4.0)   # 휘— (좁은 대역 = 휘파람 같은 바람)
    flakes = filt(filt(noise(n, r), "high", 3000), "low", 8000) * (.5 + .5 * np.sin(2 * np.pi * t / 3.55) ** 2) * .05   # 눈발이 옷깃에 사락
    return loopify(reverb(base + whistle + flakes, 2.4, .35, tone_hz=2500)[:n], .5)


@sfx("cut.chain.drag", -13, "컷신", "사슬이 눈을 긁음: 무거운 사슬 끝이 눈밭에 스으윽 길게 끌리며 고리가 자글자글(2초)", use="B12-P2 0.0: 흑월이 눈밭에 명단 줄을 긋는다")
def _(r):
    sec = 2.1; n = int(sec * SR); buf = np.zeros(n)
    m = int(1.8 * SR)
    place(buf, filt(filt(noise(m, r), "high", 700), "low", 4500) * env(m, .1, .3, 3, hold=1.1) * .5, 0)
    place(buf, grains(1.8, r, 40, lambda r, k: modal(.05, [(r.uniform(2200, 3800), .012, 1), (r.uniform(400, 600), .02, .3)], r) * r.uniform(.1, .35)), 0)
    return reverb(buf, 1.2, .25)


@sfx("cut.water.recede", -14, "컷신", "물이 빠짐: 불었던 물이 꼬르륵 땅으로 스며들며 쏴— 하고 물러남, 끝에 물방울 몇(3초)", use="B12-KNEEL 0.0: 물이 빠지고 새벽빛")
def _(r):
    sec = 3.2; n = int(sec * SR); buf = np.zeros(n)
    place(buf, sweep_filt(noise(n, r), "band", 1100, 250, .8) * env(n, .2, 1.2, 2.5, hold=.6) * .6, 0)   # 높→낮 = 물러남
    place(buf, grains(2.0, r, 30, lambda r, k: bubble(.12, r.uniform(200, 600), 2.2, .03) * r.uniform(.2, .6)), .2, .5)   # 꼬르륵
    place(buf, grains(1.0, r, 6, lambda r, k: bubble(.1, r.uniform(1000, 2000), 1.5, .012) * .4), 2.1)
    return reverb(buf, 1.6, .3, tone_hz=3000)


@sfx("cut.splash.pull", -12, "컷신", "물에서 사람을 끌어올림: 물을 가르는 큰 첨벙 + 젖은 몸이 물에서 빠져나오는 쏴아 + 둑 흙에 털썩(2.5초)", use="C-12A 10.0(일곱 번, 간격 2초쯤) · 38.0(차사가 끌어냄, 0.8배)")
def _(r):
    sec = 2.6; buf = np.zeros(int(sec * SR))
    place(buf, _splash(r, .7, 1.3), 0)
    m = int(.9 * SR); place(buf, sweep_filt(noise(m, r), "band", 400, 1500, 1) * env(m, .2, .4, 3) * .6, .5)   # 물에서 끌려 나옴
    place(buf, grains(.8, r, 20, lambda r, k: bubble(.06, r.uniform(700, 2000), 1.6, .01) * r.uniform(.2, .5)), 1.0)   # 몸에서 떨어지는 물
    place(buf, tone(.3, 90, 55) * env(int(.3 * SR), .003, .08) * .7, 1.8)          # 둑에 털썩
    return reverb(buf, 1.4, .3, tone_hz=3500)


@sfx("cut.snow.settle", -20, "컷신", "눈 위에 가벼운 것이 놓임: 붓 한 자루가 눈에 사박 — 아주 작게, 그 뒤 고요(1.2초)", use="C-12A 82.0: 눈밭에 붓 한 자루")
def _(r):
    buf = np.zeros(int(1.3 * SR))
    m = int(.12 * SR); place(buf, filt(filt(noise(m, r), "high", 1500), "low", 6000) * env(m, .01, .04, 3) * .6, 0)
    place(buf, modal(.6, [(1046.5, .3, 1), (2093, .12, .25)], r) * .15, .05)           # 아주 옅은 맺힘(C6)
    return reverb(buf, 1.8, .35)


@sfx("amb.dawn.birds", -27, "컷신", "새벽 새 한두 마리: 동트기 전 고요한 공기 + 멀리 새 한 마리 짹짹, 조금 뒤 다른 새 한 번(반복용 16초)", loop=True, use="C-13 0.0~: 솔고개 서낭당 동트기 전(44.0 나룻불부터는 끄고 바람만)")
def _(r):
    sec = 16.2; n = int(sec * SR); t = T(sec)
    air = filt(noise(n, r), "low", 300) * .25 * (.8 + .2 * np.sin(2 * np.pi * t / 8.1))
    birds = np.zeros(n)
    place(birds, _bird(r, 3400, 3) * .4, 2.5); place(birds, _bird(r, 3400, 2) * .3, 3.4)
    place(birds, _bird(r, 2600, 4) * .25, 10.2)                                        # 다른 새, 더 멀리
    birds = filt(birds, "low", 5000)
    return loopify(reverb(air + birds, 1.8, .35, tone_hz=4000)[:n], .5)


@sfx("amb.wind.gust", -16, "컷신", "바람 한 줄기: 고요하다가 한 번 크게 불어와 서낭나무 천 조각을 흔들고 지나감(7초, 한 번)", use="C-13 34.0: 당할미가 고개를 든다. 44.0 나룻불까지 이어짐(나룻불 장면은 소리 빼고 바람만)")
def _(r):
    sec = 7.2; n = int(sec * SR)
    g = np.exp(-((T(sec) - 2.6) / 1.4) ** 2)
    gust = sweep_filt(noise(n, r), "band", 300, 650, 3) * g
    leaves = filt(noise(n, r), "band", 3500, 1) * g * .15
    cloth = _flutter(sec, r, g, (8, 16), 2400) * .25                                     # 천 조각
    return reverb(gust + leaves + cloth + filt(noise(n, r), "low", 200) * .15, 1.8, .3)


@sfx("cut.names.glow", -16, "컷신", "이름에 하나씩 빛이 듦: 낮은 돌 '통' 위에 맑은 음이 차례로 올라감(다섯 음, 2.2초)", use="B05-TENDO 1.5(칼금 이름) · B11-TENDO 1.5(목걸이 조각, 마지막 하나는 안 울림)")
def _(r):
    sec = 2.6; buf = np.zeros(int(sec * SR))
    for k, f in enumerate([587.3, 659.3, 784.0, 880.0, 1046.5]):                    # 평조 오음 위로
        place(buf, modal(.9, [(f, .4, 1), (f * 2.76, .12, .25)], r, strike=.004) * .4, k * .38)
        place(buf, modal(.12, [(r.uniform(400, 600), .03, 1)], r) * .25, k * .38)       # 나무·돌에 닿는 통
    return reverb(buf, 1.6, .3)


@sfx("cut.paper.burn", -14, "컷신", "장부가 불탐: 종이에 불이 확 붙는 화르륵 + 타닥타닥 + 재가 사락 내려앉음(2.2초)", use="B08-PAHON 0.0~0.8: 장부가 불붙고 재가 내림")
def _(r):
    sec = 2.4; n = int(sec * SR); buf = np.zeros(n)
    m = int(.5 * SR); place(buf, filt(noise(m, r), "band", 1200, .7) * env(m, .05, .25, 3) * .8, 0)   # 화르륵
    place(buf, filt(filt(noise(n, r), "band", 1600, .8), "low", 5000) * env(n, .2, .8, 3, hold=.6) * .2, .2)
    place(buf, grains(1.8, r, 50, lambda r, k: filt(noise(int(.005 * SR), r), "band", r.uniform(1200, 3500), 2) * env(int(.005 * SR), .0003, .002) * r.uniform(.2, .8)), .3)   # 타닥
    return reverb(buf, .9, .2)


@sfx("cut.paper.ascend", -15, "컷신", "숫자 종이들이 하늘로 빨려 올라감: 종이 수십 장이 펄럭이며 위로 휘이— 멀어짐(2.5초)", use="B08-TENDO 3.0: 앞장 숫자들이 하늘로")
def _(r):
    sec = 2.6; n = int(sec * SR); buf = np.zeros(n)
    flap = lambda r, k: _paper(r, .05, 1500, 6000, .003) * r.uniform(.2, .6) * (1 - k / 60)
    place(buf, grains(2.0, r, 50, flap, spread=lambda k, r: (k / 50) * 1.8 + r.uniform(0, .05)), 0)
    place(buf, sweep_filt(noise(n, r), "band", 600, 2400, 1.2) * env(n, .5, 1.2, 2.5) * .4, 0)   # 위로 빨려 올라가는 바람
    return reverb(buf, 1.6, .3)


@sfx("cut.stone.crack", -13, "컷신", "바위에 금이 감: 큰 바위 속에서 우직— 하고 한 줄 갈라지는 소리 + 돌가루(1.2초)", use="B09-PAHON 1.5: 망부석 바위에 금")
def _(r):
    sec = 1.3; buf = np.zeros(int(sec * SR))
    place(buf, grains(.35, r, 25, lambda r, k: modal(.03, [(r.uniform(1500, 3500), .006, 1)], r) * r.uniform(.3, 1), spread=lambda k, r: (k / 25) ** .7 * .35), 0)   # 우지직
    place(buf, tone(.6, 85, 50) * env(int(.6 * SR), .005, .2) * .7, 0)
    place(buf, grains(.6, r, 15, lambda r, k: filt(noise(int(.005 * SR), r), "band", r.uniform(2000, 4000), 2) * env(int(.005 * SR), .0003, .002) * .3), .3)
    return reverb(buf, 1.2, .25)


@sfx("cut.anchor.drop", -11, "컷신", "닻이 여울 바닥에 박힘: 쇠사슬 차르르 + 무거운 쇠가 돌·뻘에 쿵 + 물 철썩(1.6초)", use="B10-PAHON 1.5")
def _(r):
    sec = 1.7; buf = np.zeros(int(sec * SR))
    place(buf, grains(.5, r, 12, lambda r, k: modal(.08, [(r.uniform(2000, 3500), .02, 1)], r) * .35, spread=lambda k, r: k * .035), 0)
    place(buf, modal(.8, [(160, .2, 1), (420, .12, .5), (1130, .05, .25)], r), .45)   # 쇠 쿵
    place(buf, _splash(r, .6, .9) * .5, .48)
    return reverb(buf, 1.3, .3)


@sfx("cut.beads.scatter", -15, "컷신", "목걸이 줄이 끊겨 나무 조각들이 흩어짐: 툭 끊김 + 작은 나무 조각들이 둔치에 달그락달그락 흩어져 구름(1.5초)", use="B11-PAHON 0.8")
def _(r):
    sec = 1.6; buf = np.zeros(int(sec * SR))
    place(buf, filt(noise(int(.03 * SR), r), "band", 1500, 2) * env(int(.03 * SR), .001, .01) * .5, 0)
    clack = lambda r, k: modal(.07, [(r.uniform(1100, 1900), .015, 1), (r.uniform(2800, 3600), .008, .4)], r) * r.uniform(.2, .7) * (1 - k / 30)
    place(buf, grains(1.3, r, 26, clack, spread=lambda k, r: (k / 26) ** 1.6 * 1.2 + r.uniform(0, .02)), .05)
    return reverb(buf, .7, .15)


@sfx("cut.color.shift", -22, "컷신", "기억 색이 내 혼불 색으로 바뀜: 아주 느리게 피어오르는 낮은 화음(두 음이 하나로 겹쳐짐, 6초) — 말 대신 이 소리가 '같다'를 말한다", use="C-12A 66.0 같은 색(F9를 소리로만 맞춘다)")
def _(r):
    sec = 6.5; n = int(sec * SR); t = T(sec)
    a = tone(sec, 196.0) + tone(sec, 293.7) * .6                                        # G3·D4
    b = tone(sec, 196.0 * 1.012) * np.clip(1 - t / 4.5, 0, 1)                            # 처음엔 살짝 어긋나 울다(맥놀이) 4.5초에 하나로 겹침
    pad = (a + b * .8) * env(n, 2.0, 2.0, 2, hold=2.0) * .3
    shimmer = filt(noise(n, r), "band", 2600, 4) * env(n, 2.5, 2.0, 2, hold=1.5) * .05
    return reverb(pad + shimmer, 3.0, .45, tone_hz=3000)


@sfx("cut.soul.brush", -18, "컷신", "흩어지는 조각이 내 혼불을 스침: 아주 가까이 휙 지나가는 맑은 쉬익 + 한 음이 반짝 켜졌다 꺼짐(1.2초)", use="C-12B 12.0 스침")
def _(r):
    sec = 1.3; n = int(sec * SR); buf = np.zeros(n)
    m = int(.5 * SR); place(buf, sweep_filt(noise(m, r), "band", 1500, 4000, 3) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2 * .4, 0)
    place(buf, modal(.8, [(1318.5, .15, 1), (2637, .06, .3)], r) * .35, .2)              # 같은 색으로 잠깐 빛남(E6) — 짧게 꺼짐
    return reverb(buf, 1.4, .3)


@sfx("cut.straw.set", -18, "컷신", "짚신·밥그릇을 차림: 짚이 바스락 + 사기그릇이 상에 톡 닿음(1.2초)", use="C-13 16.0 선 자리 · 24.0 짚신(A판: 고쳐 놓음)")
def _(r):
    buf = np.zeros(int(1.3 * SR))
    place(buf, _crinkle(r, .5, 18, (1500, 4000), (.2, .5)), 0)                          # 마른 짚
    place(buf, filt(noise(int(.3 * SR), r), "band", 2200, 1) * env(int(.3 * SR), .05, .1, 3) * .15, .05)
    place(buf, modal(.3, [(2350, .06, 1), (4100, .03, .3)], r) * .25, .7)                # 그릇 톡
    return reverb(buf, .7, .15)


# ===== 시즌2 저승 ⑦~⑩ 환경음·장치음 (season2_outline·npc_act4·memories_act4, 2026-10-25 밤) =====
# 저승 소리 규칙(sound-direction.md 시즌2 절):
#   ① 산 것의 소리가 없다 — 새·벌레·개구리·개·닭·사람 발소리 무리 금지. 대신 물·종이·먹·쇠·숨.
#   ② 말은 들리되 뜻은 안 들린다 — 혼과 서리는 '저희끼리' 웅얼거린다(높은 소리를 깎아 자음을 지움).
#   ③ 물은 제대로 흐르지 않는다 — 고이고, 끈적하고, 막혀서 웅 운다(하류가 깨진 가루로 막힘 F12).
#   ④ 울림이 길고 어둡다 — 이승보다 잔향 1.5배, 4kHz 위를 깎는다.
def _murmur(r, sec, people=10, f0=(90, 170), lp=1400, breath=.45, gap=(.3, 1.2)):
    """뜻 없는 웅얼거림: 숨이 많이 섞인 낮은 음절을 여럿이 겹쳐 낸다(줄 선 혼·서리). 높은 쪽을 깎아 말뜻을 지운다"""
    n = int(sec * SR); buf = np.zeros(n)
    vowels = [[(500, 4, 1), (900, 5, .5)], [(400, 4, 1), (1600, 6, .3)], [(650, 4, 1), (1100, 5, .5)]]
    for p in range(people):
        base = r.uniform(*f0); at = r.uniform(0, 1.5)
        while at < sec - .4:
            d = r.uniform(.12, .35); m = int(d * SR)
            f = np.linspace(base * r.uniform(.95, 1.1), base * r.uniform(.85, 1.0), m)
            place(buf, voice(f, vowels[r.integers(3)], breath, r, nh=12) * env(m, .03, d * .4, 3, hold=d * .3) * r.uniform(.3, 1), at)
            at += d + (r.uniform(.03, .1) if r.random() > .3 else r.uniform(*gap))
    return filt(buf, "low", lp)


def _still_water(r, sec, lap=30, lo=200, hi=700):
    """고인 검은 물: 거의 안 흐르고 가끔 끈적하게 찰박"""
    n = int(sec * SR)
    body = filt(noise(n, r), "low", 260) * .5
    laps = grains(sec, r, lap, lambda r, k: bubble(.18, r.uniform(lo, hi), 1.5, .05) * r.uniform(.2, .6))
    return body + laps * .5


# ---- ⑦ 삼도천 기슭 ----
@sfx("amb.styx.reeds", -25, "저승", "갈대늪: 검은 강가 은빛 갈대가 바람 없이도 사르륵 + 고인 물이 끈적하게 찰박 — 벌레·새 없음(반복용 15초)", loop=True, use="⑦ Reeds")
def _(r):
    sec = 15.3; n = int(sec * SR); t = T(sec)
    reed = filt(filt(noise(n, r), "band", 2600, .8), "low", 4500) * (.4 + .6 * _gust_curve(sec, r, 3, .3)) * .25   # 은빛 갈대 스침
    tick = grains(sec, r, 60, lambda r, k: filt(noise(int(.006 * SR), r), "band", r.uniform(2000, 3500), 3) * env(int(.006 * SR), .0004, .002) * r.uniform(.05, .25))   # 걸린 가루가 갈대에 톡
    return loopify(reverb(reed + tick + _still_water(r, sec, 26) * .8, 3.0, .4, tone_hz=3500)[:n], .5)


@sfx("amb.styx.ferry", -24, "저승", "빈 나루 마을: 끝이 안 보이는 줄에 선 혼들의 낮은 웅얼거림(뜻 없음) + 말뚝에 고인 물 찰박 + 아주 멀리 배 방울(반복용 18초)", loop=True, use="⑦ Ferrytown(업 60이면 웅얼거림을 0으로 — 줄 전체가 등을 돌림)")
def _(r):
    sec = 18.3; n = int(sec * SR)
    crowd = _murmur(r, sec, 16, (85, 150), 1100, .55)                                 # 숨 섞인 낮은 웅얼거림
    bell = np.zeros(n)
    for at in (6.0, 6.7): place(bell, modal(2.0, [(740, .8, 1), (1110, .5, .4), (1850, .25, .2)], r) * .12, at)   # 아주 먼 배 방울(F#5)
    bell = filt(bell, "low", 2500)
    return loopify(reverb(crowd * .6 + _still_water(r, sec, 20) * .6 + bell, 3.2, .45, tone_hz=3000)[:n], .5)


@sfx("amb.styx.inkrapids", -22, "저승", "먹물 여울: 관아에서 버린 먹이 섞여 검고 빠른 물 — 무겁게 꿀렁이며 끈적하게 쏟아짐(반복용 12초)", loop=True, use="⑦ InkRapids")
def _(r):
    sec = 12.2; n = int(sec * SR); t = T(sec)
    rush = filt(filt(noise(n, r), "band", 600, .6), "low", 2200) * (.8 + .2 * np.sin(2 * np.pi * t / 6.1))
    glug = grains(sec, r, 120, lambda r, k: bubble(.12, r.uniform(150, 450), 2.2, .035) * r.uniform(.2, .8))   # 끈적한 꿀렁(낮은 방울)
    return loopify(reverb(rush * .6 + glug * .5 + filt(noise(n, r), "low", 120) * .5, 2.0, .3, tone_hz=2500)[:n], .4)


@sfx("amb.styx.dam", -24, "저승", "물안개 둑: 귀를 대면 이름 수천이 한꺼번에 들리는 둑 — 아주 많은 속삭임이 한 덩어리로 웅— + 막힌 물이 낮게 짓누르는 소리(반복용 16초)", loop=True, use="⑦ Dam · B-14 덩어리 터")
def _(r):
    sec = 16.3; n = int(sec * SR); t = T(sec)
    whisper = filt(_murmur(r, sec, 30, (110, 220), 3000, .9, (.1, .4)), "high", 500)   # 속삭임 수천 = 숨만 남은 높은 웅얼거림
    press = filt(noise(n, r), "low", 90) * (1 + .3 * np.sin(2 * np.pi * t / 8.15)) * 1.2   # 막힌 강이 둑을 짓누름
    drone = (tone(sec, 49) + tone(sec, 49.6) * .8) * .2
    return loopify(reverb(whisper * .5 + press + drone, 3.5, .45, tone_hz=2500)[:n], .5)


@sfx("sfx.styx.boat.arrive", -12, "저승", "배가 나루에 닿음: 안개 속에서 방울 두 번 딸랑 — 노가 물을 밀고 — 뱃머리가 말뚝에 쿵(4초). 줄 선 혼들의 웅얼거림이 잠깐 멈춘다", use="⑦ 새벽 틈 시작: 배가 2분 닿음(배웅 시작 신호)")
def _(r):
    sec = 4.2; buf = np.zeros(int(sec * SR))
    for at in (0.0, .55): place(buf, modal(2.0, [(740, .8, 1), (1110, .5, .4), (1850, .25, .2)], r) * .4, at)
    for k in range(2):
        m = int(.5 * SR); place(buf, sweep_filt(noise(m, r), "band", 300, 800, 1.2) * env(m, .08, .2, 3) * .5, 1.4 + k * 1.0)
    place(buf, modal(.6, [(150, .15, 1), (380, .08, .5)], r) * .8, 3.3)                # 뱃머리 쿵(나무)
    place(buf, _splash(r, .5, .5) * .4, 3.32)
    return reverb(buf, 2.6, .4, tone_hz=3000)


@sfx("sfx.styx.line.step", -13, "저승", "줄이 처음으로 한 칸 움직임: 백 년 서 있던 수백의 발이 한꺼번에 스윽 한 걸음 + 낮게 퍼지는 숨(2.5초)", use="B-13 천도: 줄이 처음 한 칸 움직이는 순간")
def _(r):
    sec = 2.6; buf = np.zeros(int(sec * SR))
    shuffle = lambda r, k: filt(noise(int(.15 * SR), r), "band", r.uniform(500, 1200), 1) * env(int(.15 * SR), .02, .05, 3) * r.uniform(.1, .3)
    place(buf, grains(.7, r, 80, shuffle, spread=lambda k, r: r.normal(.3, .12) % .7), 0)   # 수백의 한 걸음(거의 같은 순간)
    m = int(1.6 * SR); place(buf, sweep_filt(noise(m, r), "band", 400, 900, 2) * env(m, .3, .8, 3) * .4, .5)   # 낮은 숨
    return reverb(buf, 2.5, .4)


@sfx("sfx.name.slip.float", -13, "저승", "이름 쪽지가 떠오름: 파혼 가루 속에서 종이 한 장이 사르륵 떠오르며 맑은 음이 떨림(1.5초 창 — 지금 사슬로 낚아라)", bypass_cast=True, use="⑦~⑩ 파혼 직후 이름 줍기 창이 열릴 때")
def _(r):
    sec = 1.6; n = int(sec * SR); buf = np.zeros(n)
    place(buf, _paper(r, .4, 1500, 6000, .05) * .5, 0)
    trem = modal(1.5, [(1568, 1.2, 1), (3136, .5, .2)], r) * (.6 + .4 * np.sin(2 * np.pi * 9 * T(1.5)))   # 떨리는 G6 = 곧 사라짐
    place(buf, trem * .35 * np.linspace(1, .3, len(trem)), .05)
    return reverb(buf, 1.4, .3)


@sfx("sfx.name.slip.catch", -12, "저승", "이름 쪽지를 낚음: 사슬 끝이 종이를 착 감고 — 떨리던 음이 또렷하게 멈춤(0.9초). 물막이 눈금은 절반만", use="⑦~⑩ 이름 줍기 성공")
def _(r):
    sec = 1.0; buf = np.zeros(int(sec * SR))
    place(buf, grains(.2, r, 6, lambda r, k: modal(.08, [(r.uniform(2800, 4000), .02, 1)], r) * .4, spread=lambda k, r: k * .03), 0)
    place(buf, _paper(r, .08, 1500, 6000, .003) * .6, .18)
    place(buf, modal(.8, [(1568, .4, 1), (2352, .25, .4)], r) * .45, .2)                # 같은 G6가 떨림 없이 맺힘
    return reverb(buf, 1.2, .3)


@sfx("sfx.dam.gauge.up", -16, "저승", "물막이 눈금이 오름: 멀리 하류에서 무거운 물이 한 번 꿀렁 짓눌림(1.4초, 낮고 짧게 — 겁주지 않고 무겁게만)", use="⑦~⑩ 파혼으로 물막이 눈금이 오를 때(이름 줍기 성공 땐 0.6배)")
def _(r):
    sec = 1.5; n = int(sec * SR); buf = np.zeros(n)
    place(buf, bubble(.6, 70, 1.5, .18) * .7, 0)
    place(buf, filt(noise(n, r), "low", 110) * env(n, .2, .6, 2) * .8, 0)
    return reverb(buf, 2.0, .3, tone_hz=1500)


# ---- ⑧ 명부전 담장 밖 ----
@sfx("amb.clerk.quarters", -24, "저승", "서리 숙사: 긴 행랑 — 붓 말리는 줄이 달그락, 종이 넘기는 사락, 부엌 아궁이 불 타닥, 빨래에서 물 뚝, 서리들 낮은 웅얼거림(뜻 없음)(반복용 16초)", loop=True, use="⑧ ClerkQuarters(업 30 근처 서리는 말을 멈춤 → 웅얼거림만 0.4배)")
def _(r):
    sec = 16.3; n = int(sec * SR)
    talk = _murmur(r, sec, 7, (100, 190), 1600, .3)
    pages = grains(sec, r, 14, lambda r, k: _paper(r, .12, 1500, 5500, .01) * r.uniform(.2, .5))
    brushes = grains(sec, r, 10, lambda r, k: modal(.1, [(r.uniform(900, 1400), .02, 1)], r) * r.uniform(.1, .3))   # 줄에 걸린 붓대 달그락
    fire = grains(sec, r, 90, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1000, 3000), 2) * env(int(.004 * SR), .0003, .0015) * r.uniform(.05, .3)) + filt(noise(n, r), "band", 300, .8) * .08
    drip = grains(sec, r, 12, lambda r, k: bubble(.1, r.uniform(900, 1600), 1.8, .012) * r.uniform(.1, .3))
    return loopify(reverb(talk * .5 + pages + brushes + fire * .5 + drip, 1.6, .3, tone_hz=3500)[:n], .5)


@sfx("amb.inkroom", -22, "저승", "먹방: 거대한 벼루 여럿에서 먹 가는 소리가 느린 원을 그리며 겹침 + 국자로 물 붓는 쪼르륵 + 돌 울림(반복용 14초)", loop=True, use="⑧ InkRoom")
def _(r):
    sec = 14.2; n = int(sec * SR); t = T(sec); y = np.zeros(n)
    for k, hz in enumerate((.42, .55, .31)):                                         # 일꾼 셋이 각자 다른 빠르기로 먹을 간다
        sp = .3 + .7 * np.abs(np.sin(2 * np.pi * hz * t + k))
        y += filt(noise(n, r), "band", 900 + 300 * k, .9) * sp * .3 + filt(filt(noise(n, r), "band", 250 + 60 * k, 4), "low", 600) * sp * .25   # 쓸림 + 큰 벼루 돌 울림
    pour = np.zeros(n)
    for at in (4.0, 11.0):
        m = int(1.2 * SR); place(pour, np.sin(2 * np.pi * np.cumsum(np.linspace(500, 900, m)) / SR) * filt(noise(m, r), "low", 2000) * env(m, .1, .3, 3, hold=.6) * .4, at)   # 쪼르륵(높아지며 차오름)
    return loopify(reverb(y + pour, 1.8, .35, tone_hz=3000)[:n], .5)


@sfx("amb.archive", -29, "저승", "문서 창고: 끝없는 서가의 마른 고요 — 오래된 나무 선반이 가끔 끼익, 먼 곳에서 한 장 넘기는 사락, 먼지가 내려앉는 듯한 아주 옅은 쉬—(반복용 18초)", loop=True, use="⑧ Archive(아홉째 칸 앞은 이 소리도 0.5배 — 비어서 더 조용)")
def _(r):
    sec = 18.2; n = int(sec * SR)
    air = filt(filt(noise(n, r), "band", 3000, .5), "low", 6000) * .03 + filt(noise(n, r), "low", 150) * .25
    creak = np.zeros(n)
    for at in (3.5, 12.2):
        m = int(.6 * SR); f = np.linspace(260, 200, m); st = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .7).astype(float)
        place(creak, filt(st - st.mean(), "band", 900, 3) * env(m, .1, .2, 3, hold=.2) * .3, at)
    pages = np.zeros(n); place(pages, _paper(r, .2, 1500, 5000, .02) * .3, 8.0); place(pages, _paper(r, .15, 1500, 5000, .02) * .2, 15.5)
    return loopify(reverb(air + creak + pages, 2.8, .45, tone_hz=3000)[:n], .5)


@sfx("amb.numberyard", -25, "저승", "숫자 마당: 번호순으로 줄 선 혼 수백이 아무 말 없이 서 있음 — 목에 건 나무 번호패들이 바람에 아주 작게 딸각딸각 + 낮은 웅(반복용 15초)", loop=True, use="⑧ NumberYard")
def _(r):
    sec = 15.2; n = int(sec * SR); t = T(sec)
    tags = grains(sec, r, 160, lambda r, k: modal(.05, [(r.uniform(1100, 1700), .012, 1)], r) * r.uniform(.03, .15)) * (.5 + .5 * _gust_curve(sec, r, 2, .4))
    hum = (tone(sec, 73.4) + tone(sec, 110) * .4) * .15 * (.8 + .2 * np.sin(2 * np.pi * t / 7.6))
    return loopify(reverb(tags + hum + filt(noise(n, r), "low", 200) * .2, 2.5, .4, tone_hz=3000)[:n], .5)


@sfx("sfx.clerk.hush", -18, "저승", "서리들이 말을 멈춤: 웅얼거림이 한꺼번에 뚝 — 붓 하나 내려놓는 톡, 그리고 정적(1.2초)", use="⑧ 업 높은 차사가 서리 곁을 지날 때(같은 순간 amb.clerk.quarters 웅얼거림을 줄임)")
def _(r):
    sec = 1.3; buf = np.zeros(int(sec * SR))
    m = int(.35 * SR); place(buf, filt(_murmur(r, .35, 5, (100, 180), 1500, .3), "low", 1500) * np.linspace(1, 0, m)[:int(.35 * SR)] * .6, 0)   # 말소리가 뚝 끊김
    place(buf, modal(.2, [(1100, .04, 1)], r) * .3, .45)                                  # 붓 내려놓음
    return reverb(buf, 1.4, .3)


# ---- ⑨ 빈 관할 ----
@sfx("amb.blank.town", -25, "저승", "빈 고을: 솔고개와 똑같은데 아무것도 살지 않음 — 바람이 지나가는 소리만, 서낭나무 빈 종이가 팔락, 그리고 소리가 끝나기 전에 사라지는 이상한 울림(반복용 18초)", loop=True, use="⑨ BlankTown(새벽빛 없는 안개 낮·밤 공통)")
def _(r):
    sec = 18.2; n = int(sec * SR)
    wind = sweep_filt(noise(n, r), "band", 300, 520, 3) * (.3 + .7 * _gust_curve(sec, r, 2, .2)) * .5
    flap = np.zeros(n)
    for at in (5.0, 5.4, 13.0): place(flap, _paper(r, .1, 1200, 5000, .005) * .35, at)   # 문패 없는 종이
    hollow = reverb(flap + wind, 3.5, .6, tone_hz=2000)[:n]
    rev = hollow[::-1] * .15                                                             # 거꾸로 된 울림 = 소리가 '오다 만' 느낌
    return loopify(hollow + rev, .5)


@sfx("amb.blank.market", -22, "저승", "도장 없는 장터: 사람 모양 혼들이 서로 '어이' '어이'만 부르는 소리(이름 없음, 뜻 없음) + 그릇 달그락 몇 번 — 활기 없이(반복용 16초)", loop=True, use="⑨ SeallessMarket")
def _(r):
    sec = 16.2; n = int(sec * SR); buf = np.zeros(n)
    for k in range(14):                                                               # 짧게 두 음절로 부름: 어-이
        at = r.uniform(0, sec - 1); f = r.uniform(130, 210)
        f0 = curve(.5, [(0, f), (.18, f * 1.05), (.25, f * 1.2), (.5, f * .95)])
        y = voice(f0, [(560, 4, 1), (1000, 5, .5)], .35, r, nh=14) * env(int(.5 * SR), .02, .15, 3, hold=.2)
        place(buf, y * r.uniform(.2, .6), at)
    buf = filt(buf, "low", 1500)
    clink = grains(sec, r, 8, lambda r, k: modal(.15, [(r.uniform(1800, 3000), .04, 1)], r) * r.uniform(.1, .25))
    return loopify(reverb(buf + clink, 2.5, .45, tone_hz=2500)[:n], .5)


@sfx("amb.sealcave", -21, "저승", "인장 굴: 깊은 굴 물방울 똑— 긴 울림 + 벽 어딘가에서 도장을 찍는 듯한 희미한 톡… 톡 + 낮은 굴 울림(반복용 15초)", loop=True, use="⑨ SealCave")
def _(r):
    sec = 15.2; n = int(sec * SR)
    drips = grains(sec, r, 10, lambda r, k: bubble(.2, r.uniform(700, 1300), 2.0, .025) * r.uniform(.3, .7))
    stamp = np.zeros(n)
    for at in (2.2, 6.8, 7.3, 12.5): place(stamp, _thump(r, .1, 130, 420) * .25, at)    # 이마 높이 붉은 자국 — 누가 찍는 듯
    rumble = filt(noise(n, r), "band", 70, 3) * .5
    return loopify(reverb(drips + stamp + rumble, 4.0, .55, tone_hz=2200)[:n], .5)


@sfx("sfx.map.draw", -16, "저승", "기억 지도가 그려짐: 붓이 빈 종이 위로 사사삭 퍼져 나가며 땅을 그림 + 먹이 번지는 낮은 쉬—(2.5초)", use="⑨ 천도한 혼의 기억이 미니맵 주변을 그릴 때")
def _(r):
    sec = 2.6; n = int(sec * SR); buf = np.zeros(n)
    strokes = lambda r, k: filt(filt(noise(int(.15 * SR), r), "high", 1800), "low", 6500) * env(int(.15 * SR), .01, .05, 3) * r.uniform(.2, .5)
    place(buf, grains(2.0, r, 14, strokes, spread=lambda k, r: (k / 14) ** .8 * 1.9), 0)   # 점점 넓게(간격이 벌어짐)
    place(buf, sweep_filt(noise(n, r), "band", 500, 1500, 1) * env(n, .4, 1.0, 2.5) * .25, 0)
    return reverb(buf, 1.6, .3)


@sfx("sfx.keeper.note", -16, "저승", "먹지기의 쪽지: 접힌 종이가 펴지는 사락 + 낮고 따뜻한 나무 '통' 한 번(1초) — 누군가 대신 주워 둔 것", use="⑨ 먹지기 흔적을 만져 쪽지가 나올 때")
def _(r):
    buf = np.zeros(int(1.1 * SR))
    place(buf, _paper(r, .25, 1300, 5500, .03) * .5, 0)
    place(buf, modal(.7, [(440, .3, 1), (880, .12, .3)], r) * .4, .25)                    # A4 나무 통
    return reverb(buf, 1.3, .3)


# ---- ⑩ 열째 관할 ----
@sfx("amb.first.village", -26, "저승", "처음 마을: 늘 같은 새벽빛 — 아주 옅은 바람, 우물 두레박 줄이 한 번 삐걱, 아무것도 깨어나지 않는 고요(새도 닭도 없음)(반복용 18초)", loop=True, use="⑩ FirstVillage")
def _(r):
    sec = 18.2; n = int(sec * SR)
    air = filt(noise(n, r), "band", 400, .5) * .12 * (.8 + .2 * np.sin(2 * np.pi * T(sec) / 9.1))
    rope = np.zeros(n); m = int(1.2 * SR); f = np.linspace(300, 240, m); st = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .75).astype(float)
    place(rope, filt(st - st.mean(), "band", 1000, 3) * env(m, .2, .4, 3, hold=.3) * .2, 9.0)
    return loopify(reverb(air + rope + filt(noise(n, r), "low", 120) * .15, 2.6, .4, tone_hz=3500)[:n], .5)


@sfx("amb.chain.graves", -22, "저승", "사슬 무덤: 들판에 비석처럼 선 녹슨 사슬들이 바람에 아주 느리게 짤그랑 + 녹이 갈리는 끼익(반복용 16초)", loop=True, use="⑩ ChainGraves")
def _(r):
    sec = 16.2; n = int(sec * SR)
    g = _gust_curve(sec, r, 3, .2)
    clink = grains(sec, r, 70, lambda r, k: modal(.25, [(r.uniform(1400, 2600), .08, 1), (r.uniform(3200, 4800), .03, .3)], r) * r.uniform(.05, .25))
    clink = filt(clink, "low", 4000) * (.3 + .7 * g)                                     # 녹슬어 맑지 않게
    grind = np.zeros(n)
    for at in (4.0, 11.5):
        m = int(.8 * SR); place(grind, filt(noise(m, r), "band", 1200, 4) * (.5 + .5 * np.sign(np.sin(2 * np.pi * 30 * T(.8)))) * env(m, .1, .3, 3, hold=.3) * .15, at)
    wind = sweep_filt(noise(n, r), "band", 300, 600, 3) * g * .3
    return loopify(reverb(clink + grind + wind, 2.5, .4, tone_hz=3000)[:n], .5)


@sfx("amb.wellyard", -22, "저승", "우물터: 깊은 우물 안으로 물방울이 똑— 하고 아주 길게 울림 + 작은 신발·큰 신발 곁의 고요(반복용 14초)", loop=True, use="⑩ WellYard")
def _(r):
    sec = 14.2; n = int(sec * SR); buf = np.zeros(n)
    for at in (1.5, 6.2, 10.9):
        place(buf, bubble(.25, r.uniform(500, 800), 1.8, .03) * .6, at)
    well = reverb(filt(buf, "low", 2500), 4.5, .7, tone_hz=1500)[:n]                     # 우물 속 긴 울림(관 울림)
    well = well + filt(well, "band", 180, 6) * .8
    return loopify(well + filt(noise(n, r), "low", 100) * .12, .5)


@sfx("amb.bigdam", -21, "저승", "물막이 바닥: 모든 관할의 깨진 이름이 고인 거대한 덩어리 — 막힌 강이 땅 밑에서 신음하듯 우우웅 짓눌리고, 가루가 서로 갈리는 사각사각(반복용 16초)", loop=True, use="⑩ BigDam · B-20 터(물막이 눈금이 높을수록 1.0배에 가깝게, 낮으면 0.6배)")
def _(r):
    sec = 16.2; n = int(sec * SR); t = T(sec)
    groan = filt(noise(n, r), "low", 80) * (1 + .5 * np.sin(2 * np.pi * t / 5.4)) * 1.3
    moan = sweep_filt(noise(n, r), "band", 90, 160, 5) * (.5 + .5 * np.sin(2 * np.pi * t / 16.2)) * .6   # 강이 운다
    dust = grains(sec, r, 400, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 3500), 2) * env(int(.004 * SR), .0003, .0015) * r.uniform(.03, .15))
    return loopify(reverb(groan + moan + dust, 3.5, .45, tone_hz=2000)[:n], .5)


@sfx("sfx.fragment.link", -13, "저승", "이름 조각 셋이 이어짐: 떨어진 세 음이 차례로 울리다가 하나의 화음으로 맞물림 + 사슬 차르르(2초)", use="⑩ 같은 색 조각 셋을 사슬로 이었을 때")
def _(r):
    sec = 2.2; buf = np.zeros(int(sec * SR))
    notes = [523.3, 659.3, 784.0]                                                        # C5·E5·G5
    for k, f in enumerate(notes): place(buf, modal(.5, [(f, .2, 1), (f * 2, .08, .3)], r) * .3, k * .25)
    place(buf, grains(.3, r, 8, lambda r, k: modal(.06, [(r.uniform(2800, 4000), .015, 1)], r) * .3, spread=lambda k, r: k * .03), .75)
    chord = sum(modal(1.3, [(f, .7, 1), (f * 2, .3, .25)], r) for f in notes)
    place(buf, chord * .3, .85)                                                           # 하나로 맞물린 화음
    return reverb(buf, 1.8, .35)


@sfx("sfx.chain.unrust", -17, "저승", "녹슨 사슬 하나가 조금 덜 녹슬어 보임: 둔한 쇠가 한 번 울리다 맑아짐(1.6초)", use="⑩ 잇기(장례 변주) 마지막 컷")
def _(r):
    sec = 1.7; n = int(sec * SR); buf = np.zeros(n)
    dull = filt(modal(1.4, [(1320, .6, 1), (2900, .3, .4)], r), "low", 1600)
    clear = modal(1.4, [(1320, .6, 1), (2900, .3, .4)], r)
    k = np.clip(T(1.4) / 1.0, 0, 1)                                                       # 1초에 걸쳐 둔함→맑음
    place(buf, (dull * (1 - k) + clear * k) * .5, 0)
    return reverb(buf, 1.6, .3)


# ===== 시즌2 컷신(cutscenes_s2.json) 요청 소리 10개 (2026-10-25) =====
# 저승 규칙 그대로: 산 것의 소리 없음, 말은 뜻 없이, 물은 막혀 있다가 마지막에야 흐른다.
@sfx("cut.knife.notch", -15, "컷신", "나무 말뚝에 칼금 하나: 칼날이 젖은 나무를 짧게 긁어 파는 '삭—' + 끝의 작은 '톡'(0.6초)", use="B13-INTRO 3.2: 노인이 말뚝에 칼금을 하나 더 긋는다")
def _(r):
    sec = .7; n = int(sec * SR); buf = np.zeros(n)
    m = int(.32 * SR)
    scrape = sweep_filt(noise(m, r), "band", 1800, 1100, 2.0) * env(m, .02, .12, 3, hold=.15)   # 칼날이 결을 거슬러 긁힘(점점 낮게)
    grit = grains(.3, r, 18, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 3000), 3) * env(int(.004 * SR), .0003, .0015) * r.uniform(.2, .6))
    place(buf, scrape * .7, 0); place(buf, grit * .5, 0)
    place(buf, _thump(r, .08, 260, 1100) * .5, .33)                                       # 칼끝이 빠지며 톡
    return reverb(buf, .9, .2, tone_hz=4000)


@sfx("cut.door.slide", -15, "컷신", "오래된 나무 미닫이가 밀려 열림: 홈에 걸려 드르륵 끼이— 하다 툭 멈춤 + 빈 방 울림(1.8초)", use="C-16 58.0: 아홉째 칸 빈 서가 뒤 문이 열려 있다")
def _(r):
    sec = 2.0; n = int(sec * SR); buf = np.zeros(n)
    m = int(1.3 * SR); t = T(1.3)
    rate = 18 + 10 * np.sin(2 * np.pi * t / 2.6)                                           # 홈에 걸리는 드르륵 빠르기
    judder = (np.sin(2 * np.pi * np.cumsum(rate) / SR) > .6).astype(float)
    rattle = filt(noise(m, r), "band", 700, 1.2) * filt(judder, "low", 120) * env(m, .08, .5, 3, hold=.7)
    m2 = int(.7 * SR); f = np.linspace(520, 430, m2)
    creak = filt(((np.sin(2 * np.pi * np.cumsum(f) / SR)) > .8).astype(float), "band", 1300, 3) * env(m2, .1, .25, 3, hold=.3)
    place(buf, rattle * .8, 0); place(buf, creak * .35, .35)
    place(buf, _thump(r, .14, 140, 500) * .7, 1.3)                                          # 끝에 닿아 툭
    return reverb(buf, 1.8, .35, tone_hz=3000)


@sfx("cut.paper.set", -19, "컷신", "종이 한 장을 바위 위에 놓음: 한지가 스르륵 + 돌에 닿는 아주 작은 톡(0.6초)", use="C-17 24.0: 먹지기가 종이 한 장을 바위 위에 놓는다")
def _(r):
    buf = np.zeros(int(.7 * SR))
    place(buf, _paper(r, .35, 1200, 5500, .06), 0)
    place(buf, _crinkle(r, .12, 5, (2500, 5000), (.1, .3)), .1)
    place(buf, _thump(r, .06, 320, 1600) * .25, .32)                                       # 돌에 닿음(종이라 아주 작게)
    return reverb(buf, .8, .15)


@sfx("cut.wire.untie", -17, "컷신", "눈꺼풀을 꿴 가는 쇠줄이 풀림: 가는 철사가 고리에서 미끄러지며 찌잉— + 작은 쇳소리 세 번 + 마지막에 힘 빠지듯 낮아짐(1.6초)", use="B17-TENDO 1.8: 문지기가 눈꺼풀의 철사를 푼다")
def _(r):
    sec = 1.8; n = int(sec * SR); buf = np.zeros(n)
    m = int(1.1 * SR)
    sing = tone(1.1, 2400, 1500, .004, 7) * env(m, .05, .4, 3, hold=.4)                   # 팽팽하던 쇠줄이 풀리며 높이가 내려감
    rub = filt(noise(m, r), "band", 3800, 3) * env(m, .02, .3, 3, hold=.5)
    place(buf, sing * .18 + rub * .25, 0)
    for k, at in enumerate((.15, .5, .85)):                                                # 고리 하나씩 빠짐
        place(buf, modal(.25, [(r.uniform(3200, 4200), .05, 1), (r.uniform(5600, 6800), .02, .4)], r) * (.4 - k * .08), at)
    place(buf, filt(noise(int(.3 * SR), r), "low", 900) * env(int(.3 * SR), .03, .1) * .2, 1.2)   # 줄이 툭 늘어짐
    return reverb(buf, 1.4, .25)


@sfx("cut.seal.thud", -14, "컷신", "돌도장이 이마에 닿는 둔한 소리: 무거운 돌이 살에 '둑' + 찍히지 않고 미끄러지는 젖은 소리(0.7초)", use="B18-INTRO 1.8·3.2: 인을 제 이마에 찍는다(찍히지 않음)")
def _(r):
    sec = .8; n = int(sec * SR); buf = np.zeros(n)
    place(buf, tone(.3, 120, 70) * env(int(.3 * SR), .002, .07, 3), 0)                     # 둑(높은 '딱' 없이)
    place(buf, filt(noise(int(.06 * SR), r), "band", 500, 1) * env(int(.06 * SR), .001, .015) * .5, 0)
    m = int(.35 * SR)
    place(buf, sweep_filt(noise(m, r), "band", 900, 500, 1.5) * env(m, .03, .15, 3) * .25, .12)   # 붉은 물이 번지며 미끄러짐
    return reverb(buf, .9, .2, tone_hz=3000)


@sfx("amb.dawn.still", -28, "저승", "바람 없는 새벽: 아무것도 움직이지 않는 고요 — 아주 낮은 공기, 멀리 우물물 한 방울, 새·벌레·닭 없음(반복용 16초)", loop=True, use="B19-INTRO 0.0(우물터 새벽) · 처음 마을의 '같은 새벽'")
def _(r):
    sec = 16.2; n = int(sec * SR)
    air = filt(noise(n, r), "low", 180) * .5 + filt(noise(n, r), "band", 600, .5) * .08     # 거의 들리지 않는 공기
    drip = np.zeros(n)
    for at in (4.1, 11.7):                                                                   # 우물 속 물방울, 깊이 울림
        place(drip, bubble(.25, r.uniform(700, 850), 1.8, .05) * .25, at)
    drip = reverb(drip, 3.5, .6, tone_hz=2500)[:n]
    return loopify(reverb(air, 2.5, .3, tone_hz=2500)[:n] + drip, .5)


@sfx("amb.names.many", -20, "저승", "수천 사람이 한꺼번에 낮게 이름을 부름: 겹겹의 웅얼거림이 파도처럼 부풀었다 가라앉음 — 말뜻은 안 들림(반복용 14초)", loop=True, use="B20-INTRO 3.0~(물막이 바닥 덩어리). 크기는 물막이 눈금+시즌1 파혼 수로 키울 것")
def _(r):
    sec = 14.2; n = int(sec * SR); t = T(sec)
    near = _murmur(r, sec, 14, (90, 160), 1200, .5, (.1, .4))                              # 가까운 몇
    far = filt(_murmur(r, sec, 30, (80, 200), 900, .6, (.05, .3)), "low", 700)            # 멀리 겹친 수천(뭉개짐)
    swell = .65 + .35 * np.sin(2 * np.pi * t / (sec / 2))                                  # 두 번 부풀었다 가라앉음(반복 이음 맞춤)
    drone = filt(noise(n, r), "band", 220, .8) * .15                                        # 웅웅 깔림
    return loopify(reverb((near * .5 + far * .8) * swell + drone, 3.5, .5, tone_hz=2200)[:n], .5)


@sfx("cut.names.release", -14, "컷신", "덩어리가 이름 하나하나로 풀려 강물에 실림: 웅얼거림이 낱낱의 맑은 소리로 갈라져 퍼지며 물 위로 사라짐(4초)", use="C-20A 0.0: 풀어내기 첫 순간")
def _(r):
    sec = 4.4; n = int(sec * SR); buf = np.zeros(n); t = T(sec)
    m = int(1.6 * SR)
    place(buf, _murmur(r, 1.6, 20, (90, 170), 1100, .5, (.05, .2)) * env(m, .05, .4, 3, hold=.6) * .6, 0)   # 뭉친 웅얼거림이
    scale = [392.0, 440.0, 523.3, 587.3, 659.3, 784.0, 880.0]                               # 평조 음들(맑게 풀림)
    glint = lambda r, k: modal(.9, [(scale[r.integers(7)] * (2 if r.random() < .3 else 1), .35, 1), (scale[0] * 3.01, .1, .15)], r) * r.uniform(.08, .2)
    place(buf, grains(3.0, r, 40, glint, spread=lambda k, r: .4 + (k / 40) ** .8 * 2.6 + r.uniform(0, .05)), 0)   # 하나씩 풀려 나감(점점 성기게)
    place(buf, filt(noise(n, r), "band", 900, .6) * env(n, 1.0, 1.5, 2.5, hold=1.0) * .12, 0)   # 물에 실리는 흐름
    return reverb(buf, 2.8, .4)


@sfx("cut.river.flow", -14, "컷신", "막혔던 강이 흐르기 시작: 바닥에서 우르르 하고 둑이 풀리며, 고인 물이 점점 맑고 고르게 흐르는 소리로 바뀜(8초, 끝은 amb.river.mist로 이어짐)", use="C-20A 10.0: 강이 흐른다. 물빛이 먹빛에서 맑아진다")
def _(r):
    sec = 8.5; n = int(sec * SR); t = T(sec); buf = np.zeros(n)
    k = np.clip(t / 6.0, 0, 1)
    groan = tone(sec, 55, 75) * env(n, .5, 2.0, 3) * .4                                   # 바닥에서 풀리는 우르르
    flow = sweep_filt(noise(n, r), "band", 300, 1400, .7) * (.15 + .6 * k)                  # 흐름이 점점 밝고 커짐
    babble = grains(sec, r, 140, lambda r, k2: bubble(.08, r.uniform(500, 1600), 2.0, .02) * r.uniform(.1, .4),
                    spread=lambda j, r: (j / 140) ** .6 * (sec - .2))                       # 물방울 소리가 점점 잦아짐(맑은 물)
    buf += groan + flow * .6 + babble * .6
    buf[-int(1.0 * SR):] *= np.linspace(1, .6, int(1.0 * SR))                                # 끝은 줄여서 강 배경음에 넘김
    return reverb(buf, 2.2, .3)


@sfx("cut.river.rush", -12, "컷신", "거센 물살: 둑이 터진 뒤 강이 사납게 쏟아져 가루를 쓸고 감 — 낮게 웅웅 + 흰 물보라(반복용 8초)", loop=True, use="C-20B 2.0~16.0: 사나운 강(소리 대본에서 loop로 켜고 16초에 줄여 끔)")
def _(r):
    sec = 8.2; n = int(sec * SR); t = T(sec)
    roar = filt(filt(noise(n, r), "low", 900), "high", 60) * (.85 + .15 * np.sin(2 * np.pi * t / 4.1))
    spray = filt(noise(n, r), "band", 3000, .7) * .25 * (.7 + .3 * np.sin(2 * np.pi * t / 2.05 + 1))
    rumble = filt(noise(n, r), "low", 90) * .6
    clunk = grains(sec, r, 12, lambda r, k: tone(.25, r.uniform(70, 110), 50) * env(int(.25 * SR), .005, .08) * r.uniform(.2, .5))   # 물속에서 돌·가루가 부딪힘
    return loopify(reverb(roar + spray + rumble + clunk, 1.5, .25)[:n], .5)



# ===== 시즌3 「백의 밤」 — 열 관할의 아래층 (2026-10-25) =====
# 소리 규칙(docs/sound-direction.md 시즌3 절):
#  1) 아래층은 '물이 빠진 바닥'이다: 뚝뚝 떨어지는 물, 젖은 흙, 갇힌 공기. 위층 소리는 머리 위에서 먹먹하게만 새어 든다
#  2) 백(몸)은 말하지 않는다: 웅얼거림도 없다. 몸의 소리(흙이 밀림·천 스침)와 '원념의 실'의 팽팽한 울림만
#  3) 물 차오름 = 새벽 신호: 경고는 멀리서 차오르는 물소리, 귀로 먼저 안다
#  4) 눕히기는 '내려앉음'(흙이 숨을 내쉬듯 가라앉음 + 작은 방울 하나), 깨뜨리기는 흙·물이 터지는 둔한 폭발
def _drips(r, sec, count, lo=600, hi=1400, dec=.04, amp=(.15, .5)):
    """동굴·바닥의 물방울: 띄엄띄엄 똑(높이 제각각)"""
    return grains(sec, r, count, lambda r, k: bubble(.15, r.uniform(lo, hi), 1.8, dec) * r.uniform(*amp))


def _mud(r, sec, count, f=(150, 450)):
    """젖은 흙·뻘: 끈적하게 찌걱(낮은 방울 + 짧은 잡음)"""
    def one(r, k):
        m = int(.09 * SR)
        return (bubble(.09, r.uniform(*f), 1.4, .03) * .6 + filt(noise(m, r), "band", r.uniform(300, 800), 1.5) * env(m, .005, .03) * .4) * r.uniform(.2, .7)
    return grains(sec, r, count, one)


def _above(r, sec, kind="wind"):
    """머리 위(위층)에서 먹먹하게 새어 드는 소리: 바람 / 물 / 줄 선 혼들"""
    n = int(sec * SR)
    if kind == "wind": x = filt(noise(n, r), "band", 300, .5) * (.6 + .4 * _gust_curve(sec, r, 3, .3))
    elif kind == "water": x = filt(noise(n, r), "band", 450, .6)
    else: x = _murmur(r, sec, 14, (85, 150), 900, .55)
    return filt(x, "low", 380 if kind != "line" else 500)


def _thread_hum(r, sec, f=330, n_threads=3):
    """원념의 실: 팽팽한 검은 물줄기 실이 아주 가늘게 우는 소리(맥놀이 + 활로 긋는 듯한 잡음)"""
    n = int(sec * SR); t = T(sec); x = np.zeros(n)
    for k in range(n_threads):
        ff = f * (1 + .013 * k) * r.uniform(.99, 1.01)
        x += np.sin(2 * np.pi * ff * t + r.uniform(0, 6.28)) * (.6 + .4 * np.sin(2 * np.pi * r.uniform(.07, .2) * t + r.uniform(0, 6.28)))
    bow = filt(noise(n, r), "band", f * 3, 4) * .15
    return (x / n_threads + bow) * .5


def _settle(r, sec, size=1.0):
    """흙이 내려앉음: 낮은 숨 같은 우웅 + 흙알갱이 사르르(무덤이 닫히듯)"""
    n = int(sec * SR)
    sigh = sweep_filt(noise(n, r), "low", 900, 160) * env(n, sec * .25, sec * .3, 3) * .7
    low = tone(sec, 75, 52) * env(n, sec * .2, sec * .3, 3) * .5
    grit = grains(sec, r, int(60 * size), lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 4000), 3) * env(int(.004 * SR), .0003, .0015) * r.uniform(.05, .3),
                  spread=lambda k, r: sec * (.2 + .6 * r.random()))
    return (sigh + low + grit) * size


def _below(r, sec, parts, rt=3.0, wet=.45, tone_hz=2800):
    """아래층 환경음 조립: 부품 합 → 울림 → 반복 이음"""
    n = int(sec * SR)
    x = sum(p[:n] if len(p) >= n else np.pad(p, (0, n - len(p))) for p in parts)
    return loopify(reverb(x, rt, wet, tone_hz=tone_hz)[:n], .5)


# ---- 아래층 환경음 21 (구역마다 하나, ZoneAmbient 의 구역 code 그대로) ----
@sfx("amb.below.dambed", -24, "백의 밤", "① 둑 밑: 무너진 둑 아래 흙탕 — 뻘이 찌걱, 박다 만 말뚝이 아주 가끔 삐걱, 머리 위 밤바람이 먹먹하게(반복용 16초)", loop=True, use="① DamBed")
def _(r):
    sec = 16.2; n = int(sec * SR)
    stake = np.zeros(n); m = int(.8 * SR)
    st = (np.sin(2 * np.pi * np.cumsum(np.linspace(210, 170, m)) / SR) > .8).astype(float)
    place(stake, filt(st - st.mean(), "band", 900, 3) * env(m, .15, .25, 3, hold=.2) * .15, 7.3)
    return _below(r, sec, [_mud(r, sec, 22) * .6, _drips(r, sec, 8, 500, 900) * .5, _above(r, sec, "wind") * .5, stake], 2.4, .4)


@sfx("amb.below.poolbed", -24, "백의 밤", "① 소 밑: 물 빠진 깊은 소 바닥 — 큰 물방울이 깊게 울리고, 뒤집힌 나룻배 뱃전에서 물이 톡톡, 낮게 눌린 물 기운(반복용 15초)", loop=True, use="① PoolBed")
def _(r):
    sec = 15.2; n = int(sec * SR)
    hull = grains(sec, r, 14, lambda r, k: modal(.25, [(r.uniform(280, 420), .08, 1), (r.uniform(700, 900), .03, .3)], r) * r.uniform(.1, .3))   # 나무 뱃전에 물방울
    press = filt(noise(n, r), "low", 110) * .35
    return _below(r, sec, [_drips(r, sec, 12, 450, 900, .06) * .6, hull, press, _mud(r, sec, 8) * .4], 3.8, .5, 2200)


@sfx("amb.below.pooldeep", -23, "백의 밤", "① 소 가장 깊은 곳: 물이 끝내 빠지지 않는 곳 — 물속처럼 먹먹한 웅웅 + 올라가는 거품 + 아주 먼 강물(반복용 14초)", loop=True, use="① PoolDeep(8막 끝 무대) — 물속에서 듣는 소리")
def _(r):
    sec = 14.2; n = int(sec * SR)
    under = filt(filt(noise(n, r), "low", 260), "high", 40) * (.8 + .2 * np.sin(2 * np.pi * T(sec) / 7.1))
    bub = grains(sec, r, 40, lambda r, k: bubble(.1, r.uniform(250, 700), 2.4, .03) * r.uniform(.1, .4))
    return _below(r, sec, [under * .9, filt(bub, "low", 1500) * .6], 2.0, .35, 1500)


@sfx("amb.below.wreckbed", -23, "백의 밤", "⑤ 난파 여울 바닥: 짐승 뼈 같은 배 늑골이 바람에 끼익, 젖은 모래에서 물이 빠지며 쉬익, 머리 위 먼 파도가 먹먹하게(반복용 16초)", loop=True, use="⑤ WreckBed")
def _(r):
    sec = 16.2; n = int(sec * SR); t = T(sec)
    seep = filt(noise(n, r), "band", 2400, .9) * .06 * (.5 + .5 * np.sin(2 * np.pi * t / 8.1) ** 2)   # 모래에서 물 빠짐
    ribs = np.zeros(n)
    for at in (3.0, 10.4):
        m = int(1.3 * SR); f = np.linspace(330, 260, m); st = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .85).astype(float)
        place(ribs, filt(st - st.mean(), "band", 1100, 3) * env(m, .3, .4, 3, hold=.4) * .12, at)
    waves = filt(_wave(r, 8.1, .7), "low", 500); waves = np.tile(waves, 3)[:n]
    return _below(r, sec, [seep, ribs, waves * .35, _drips(r, sec, 6) * .3], 2.6, .4)


@sfx("amb.below.seacave", -22, "백의 밤", "⑤ 곶 밑 바다굴: 썰물 굴 — 멀리 굴 입구에서 물이 쿵 하고 밀려들었다 빠지는 울림(8초마다) + 굴 천장 물방울(반복용 16초)", loop=True, use="⑤ SeaCave")
def _(r):
    sec = 16.2; n = int(sec * SR); surge = np.zeros(n)
    for at in (1.0, 9.1):
        m = int(4 * SR)
        place(surge, (tone(4, 48, 40) * .6 + filt(noise(m, r), "low", 350) * .6) * env(m, .6, 1.2, 3), at)
    return _below(r, sec, [surge * .8, _drips(r, sec, 14, 700, 1500, .05) * .45], 4.2, .55, 2400)


@sfx("amb.below.linebed", -24, "백의 밤", "⑦ 줄 밑: 줄 바로 아래 강바닥 — 머리 위 줄 선 혼들의 웅얼거림이 물 너머로 아주 먹먹하게, 발목에서 내려온 실들이 가늘게 운다(반복용 18초)", loop=True, use="⑦ LineBed (업 60이면 위 웅얼거림 0 — ⑦ 위층 규칙과 같음)")
def _(r):
    sec = 18.2
    return _below(r, sec, [_above(r, sec, "line") * .6, _thread_hum(r, sec, 290, 4) * .25, _mud(r, sec, 10) * .3, _drips(r, sec, 6) * .25], 3.4, .5, 2200)


@sfx("amb.below.knotdeep", -22, "백의 밤", "⑦ 닻 여울: 무릎 깊이 물이 철벙이고, 수천 가닥 실이 한데 엉켜 낮게 웅— 우는 화음, 가끔 실이 조여 끼익(반복용 16초)", loop=True, use="⑦ KnotDeep (B-23 무대)")
def _(r):
    sec = 16.2; n = int(sec * SR)
    hum = sum(_thread_hum(r, sec, f, 3) for f in (146.8, 220.0, 293.7, 329.6)) * .2   # 엉킨 실 화음(D·A·D·E)
    slosh = filt(noise(n, r), "band", 700, .7) * .12 * (.6 + .4 * np.sin(2 * np.pi * T(sec) / 4.05))
    creak = np.zeros(n)
    for at in (5.2, 12.8):
        m = int(.9 * SR); place(creak, sweep_filt(noise(m, r), "band", 900, 600, 4) * env(m, .2, .3, 3, hold=.2) * .25, at)
    return _below(r, sec, [hum, slosh, creak], 3.0, .45)


@sfx("amb.below.tombpit", -25, "백의 밤", "③ 큰 무덤 속: 봉분 안쪽 — 갇힌 공기, 흙벽에서 흙알갱이가 사르르, 아주 멀리 흙을 울리는 둥 둥(옛 번호 호령의 북)(반복용 18초)", loop=True, use="③ TombPit")
def _(r):
    sec = 18.2; n = int(sec * SR)
    trickle = grains(sec, r, 50, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1200, 3000), 3) * env(int(.004 * SR), .0003, .0015) * r.uniform(.03, .15))
    drum = np.zeros(n)
    for at in (6.0, 6.7, 7.4): place(drum, filt(tone(.5, 70, 50) * env(int(.5 * SR), .005, .12, 3), "low", 200) * .35, at)   # 흙 너머 북 세 번
    air = filt(noise(n, r), "low", 140) * .3
    return _below(r, sec, [trickle, drum, air], 1.6, .3, 1800)


@sfx("amb.below.arrowroots", -24, "백의 밤", "③ 화살골 뿌리 밑: 바위 뿌리 틈으로 바람이 가늘게 휘— , 녹슨 촉이 바위에 틱, 뿌리가 삐걱(반복용 16초)", loop=True, use="③ ArrowRoots")
def _(r):
    sec = 16.2; n = int(sec * SR)
    whistle = filt(noise(n, r), "band", 1250, 6) * .2 * _gust_curve(sec, r, 3, .15)
    tick = grains(sec, r, 10, lambda r, k: modal(.08, [(r.uniform(2400, 3400), .02, 1)], r) * r.uniform(.05, .2))
    root = np.zeros(n); m = int(1.1 * SR)
    place(root, sweep_filt(noise(m, r), "band", 500, 380, 5) * env(m, .3, .3, 3, hold=.3) * .3, 9.5)
    return _below(r, sec, [whistle, tick, root, _above(r, sec, "wind") * .3], 2.2, .35)


@sfx("amb.below.floodedshaft", -23, "백의 밤", "④ 물 찬 갱도: 갱 안에 고인 물이 철썩, 버팀목이 무게에 끄으응, 녹슨 수레바퀴가 한 번 끼익, 물방울 울림(반복용 17초)", loop=True, use="④ FloodedShaft")
def _(r):
    sec = 17.2; n = int(sec * SR)
    lap = _still_water(r, sec, 24, 180, 520) * .6
    beam = np.zeros(n)
    for at in (2.5, 11.0):
        m = int(1.6 * SR); place(beam, sweep_filt(noise(m, r), "band", 260, 190, 5) * env(m, .4, .5, 3, hold=.5) * .45, at)
    wheel = np.zeros(n); m = int(.7 * SR); f = np.linspace(900, 700, m)
    place(wheel, filt(((np.sin(2 * np.pi * np.cumsum(f) / SR)) > .9).astype(float), "band", 2200, 3) * env(m, .05, .25, 3, hold=.2) * .12, 7.4)
    return _below(r, sec, [lap, beam, wheel, _drips(r, sec, 10, 500, 1100, .05) * .4], 3.4, .5, 2400)


@sfx("amb.below.sealedface", -25, "백의 밤", "④ 막힌 막장 안쪽: 쌓인 돌 틈으로 바깥 바람이 가늘게 새는 휘— , 돌 부스러기가 툭, 숨 막히게 고요(반복용 16초)", loop=True, use="④ SealedFace (B-25 무대)")
def _(r):
    sec = 16.2; n = int(sec * SR)
    leak = filt(noise(n, r), "band", 1800, 8) * .12 * (.5 + .5 * _gust_curve(sec, r, 2, .2))
    pebble = grains(sec, r, 5, lambda r, k: modal(.15, [(r.uniform(900, 1600), .03, 1), (r.uniform(2500, 3500), .015, .4)], r) * r.uniform(.15, .35))
    return _below(r, sec, [leak, pebble, filt(noise(n, r), "low", 120) * .3], 1.4, .3, 2000)


@sfx("amb.below.limepit", -25, "백의 밤", "② 석회 구덩이: 물 한 방울 없이 바싹 마른 곳 — 흰 가루가 바람에 사아 날리고, 발 디딘 자리 가루가 바스락, 잿빛 정적(반복용 16초)", loop=True, use="② LimePit (역병의 숨 장판은 sfx.boss.plague.breath)")
def _(r):
    sec = 16.2; n = int(sec * SR)
    dust = filt(filt(noise(n, r), "high", 2500), "low", 7000) * .05 * (.4 + .6 * _gust_curve(sec, r, 3, .2))
    crunch = grains(sec, r, 18, lambda r, k: _crinkle(r, .05, 6, (2500, 6000), (.05, .2)))
    return _below(r, sec, [dust, crunch, filt(noise(n, r), "low", 100) * .25], 1.2, .25, 4000)


@sfx("amb.below.clinicfloor", -25, "백의 밤", "② 역병막 마루 밑: 머리 위 마룻바닥이 바람에 삐걱, 내려앉은 약장 나무가 끄응, 먼지가 틈으로 사르르(반복용 16초)", loop=True, use="② ClinicFloor")
def _(r):
    sec = 16.2; n = int(sec * SR); board = np.zeros(n)
    for at, f0 in ((3.1, 260), (9.8, 230), (13.2, 280)):
        m = int(.6 * SR); f = np.linspace(f0, f0 * .85, m); st = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .85).astype(float)
        place(board, filt(st - st.mean(), "band", 1000, 3) * env(m, .1, .2, 3, hold=.15) * .15, at)
    dust = grains(sec, r, 30, lambda r, k: filt(noise(int(.005 * SR), r), "band", r.uniform(2000, 5000), 3) * env(int(.005 * SR), .0003, .002) * r.uniform(.03, .12))
    return _below(r, sec, [board, dust, _above(r, sec, "wind") * .35], 1.6, .3)


@sfx("amb.below.gatepit", -24, "백의 밤", "⑥ 성문 밖 구덩이: 언 땅 — 흙이 얼며 틱틱 갈라지는 소리, 머리 위 눈바람이 먹먹하게, 아무 물기 없음(반복용 16초)", loop=True, use="⑥ GatePit (B-27 무대)")
def _(r):
    sec = 16.2
    frost = grains(sec, r, 40, lambda r, k: modal(.04, [(r.uniform(3000, 6000), .006, 1)], r) * r.uniform(.03, .15))   # 얼음 갈라짐
    return _below(r, sec, [frost, _above(r, sec, "wind") * .7], 1.8, .35, 3500)


@sfx("amb.below.bridgefound", -23, "백의 밤", "⑥ 다리 기초 밑: 옆으로 큰내가 먹먹하게 흐르고, 돌기둥이 무게에 끄응, 이끼 낀 돌에서 물방울(반복용 15초)", loop=True, use="⑥ BridgeFound")
def _(r):
    sec = 15.2; n = int(sec * SR)
    groan = np.zeros(n); m = int(2.0 * SR)
    place(groan, (tone(2.0, 58, 52) * .5 + sweep_filt(noise(m, r), "band", 200, 150, 5) * .4) * env(m, .6, .6, 3, hold=.5), 6.0)
    return _below(r, sec, [_above(r, sec, "water") * .8, groan * .6, _drips(r, sec, 10, 600, 1300, .05) * .4], 2.4, .4)


@sfx("amb.below.inksilt", -23, "백의 밤", "⑧ 먹 앙금: 수백 년 가라앉은 검은 진흙이 느리게 꿀렁, 머리 위 벼루들이 도는 낮은 갈림 소리(반복용 16초)", loop=True, use="⑧ InkSilt (이동 −15% 장판과 함께)")
def _(r):
    sec = 16.2; n = int(sec * SR); t = T(sec)
    glug = grains(sec, r, 30, lambda r, k: bubble(.25, r.uniform(90, 220), 1.6, .08) * r.uniform(.2, .6))     # 진득한 거품
    grind = filt(noise(n, r), "band", 160, 1.2) * .3 * (.7 + .3 * np.sin(2 * np.pi * t / 4.05))              # 위에서 벼루가 돎
    return _below(r, sec, [glug, filt(grind, "low", 400), _mud(r, sec, 10, (90, 250)) * .3], 2.8, .45, 1800)


@sfx("amb.below.quartercellar", -26, "백의 밤", "⑧ 숙사 밑: 서리들이 일하다 잠든 자세 그대로 — 종이 한 장이 스르륵 미끄러지고, 붓대가 굴러 톡, 그 밖엔 아무 소리도 없음(반복용 18초)", loop=True, use="⑧ QuarterCellar")
def _(r):
    sec = 18.2; n = int(sec * SR); b = np.zeros(n)
    place(b, _paper(r, .6, 1200, 5000, .1) * .25, 4.0)
    place(b, grains(.6, r, 3, lambda r, k: modal(.08, [(r.uniform(900, 1400), .02, 1)], r) * .2, spread=lambda k, r: k * .18), 12.5)
    return _below(r, sec, [b, filt(noise(n, r), "low", 120) * .25], 2.6, .45, 2500)


@sfx("amb.below.ondol", -25, "백의 밤", "⑨ 아랫목: 구들 밑 고래(연기 길)로 바람이 우— 하고 빠지고, 식은 재가 사락, 아주 가끔 그릇 뚜껑이 달각(반복용 16초)", loop=True, use="⑨ Ondol (B-29 무대)")
def _(r):
    sec = 16.2; n = int(sec * SR)
    flue = filt(noise(n, r), "band", 220, 2) * .3 * (.5 + .5 * _gust_curve(sec, r, 2, .3))
    lid = np.zeros(n); place(lid, modal(.4, [(1680, .12, 1), (3900, .05, .4)], r) * .12, 10.7)   # 사기 뚜껑
    ash = grains(sec, r, 20, lambda r, k: filt(noise(int(.005 * SR), r), "band", r.uniform(1500, 3000), 3) * env(int(.005 * SR), .0003, .002) * r.uniform(.03, .1))
    return _below(r, sec, [flue, lid, ash], 1.8, .35, 3000)


@sfx("amb.below.sealfloor", -23, "백의 밤", "⑨ 인장 굴 바닥: 붉은 물이 바닥까지 가늘게 흘러내리고, 물방울이 굴 바닥에 깊게 톡(반복용 15초)", loop=True, use="⑨ SealFloor")
def _(r):
    sec = 15.2; n = int(sec * SR)
    trickle = filt(noise(n, r), "band", 1300, 1.2) * .05 * (.7 + .3 * np.sin(2 * np.pi * T(sec) / 7.6))
    return _below(r, sec, [trickle, _drips(r, sec, 12, 400, 800, .07) * .55, _mud(r, sec, 6) * .25], 3.8, .5, 2200)


@sfx("amb.below.chainroots", -23, "백의 밤", "⑩ 사슬 무덤 밑: 땅에 꽂힌 사슬이 머리 위에서 바람에 흔들릴 때마다 흙 속으로 차르륵 당김이 전해지고, 흙이 사르르(반복용 16초)", loop=True, use="⑩ ChainRoots")
def _(r):
    sec = 16.2; n = int(sec * SR); tug = np.zeros(n)
    for at in (2.2, 7.9, 12.6):
        place(tug, filt(grains(.5, r, 8, lambda r, k: modal(.08, [(r.uniform(1200, 2200), .03, 1)], r) * .3, spread=lambda k, r: k * .05), "low", 1500), at)
        place(tug, tone(.6, 90, 70) * env(int(.6 * SR), .05, .15, 3) * .25, at)
    return _below(r, sec, [tug, _settle(r, sec, .3) * .3, _above(r, sec, "wind") * .35], 2.0, .35)


@sfx("amb.below.wellbottom", -23, "백의 밤", "⑩ 첫 우물 밑: 둥근 벽을 따라 물이 8초마다 차올랐다(3초) 빠짐(5초) — 그 숨, 위에서 늘어진 새끼줄이 삐걱(반복용 16초)", loop=True, use="⑩ WellBottom (B-30 파도형 장판 주기와 같음)")
def _(r):
    sec = 16.0; n = int(sec * SR); t = T(sec)
    ph = (t % 8.0)
    level = np.where(ph < 3, ph / 3, 1 - (ph - 3) / 5)                       # 3초 오름, 5초 내림
    water = sweep_filt(noise(n, r), "band", 300, 300, .6) * (.15 + .5 * level)
    rope = np.zeros(n)
    for at in (2.6, 10.6):
        m = int(.8 * SR); f = np.linspace(260, 220, m); st = (np.sin(2 * np.pi * np.cumsum(f) / SR) > .8).astype(float)
        place(rope, filt(st - st.mean(), "band", 900, 3) * env(m, .15, .3, 3, hold=.2) * .12, at)
    return _below(r, sec, [water, rope, _drips(r, sec, 6, 500, 900, .08) * .3], 3.2, .55, 2200)


# ---- 시즌3 장치음 12 ----
@sfx("sfx.below.stairs", -16, "백의 밤", "아래층으로 내려감: 젖은 돌계단 발소리 넷 + 귀가 먹먹해지는 공기 압력(1.8초)", use="위층→아래층 계단을 내려갈 때(화면 전환과 함께)")
def _(r):
    sec = 2.0; n = int(sec * SR); buf = np.zeros(n)
    for k in range(4):
        place(buf, _thump(r, .12, 150 - k * 10, 700) * (.6 - k * .08), k * .38)          # 돌계단 딛기
        place(buf, _splash(r, .2, .2) * .3 * (.6 - k * .08), k * .38)                     # 젖은 돌이라 찰박
    place(buf, sweep_filt(noise(n, r), "low", 2500, 300) * env(n, .5, .6, 3) * .25, 0)
    return reverb(buf, 1.8, .35, tone_hz=2500)


@sfx("sfx.water.drain", -14, "백의 밤", "저녁에 물이 빠짐: 큰 물이 바닥 구멍으로 꿀렁꿀렁 빨려 내려가며 멀어지고 바닥이 드러남(6초)", use="해 질 녘 물 빠짐 시작(저녁 2분의 첫머리)")
def _(r):
    sec = 6.5; n = int(sec * SR); t = T(sec)
    swirl = sweep_filt(noise(n, r), "band", 900, 250, .8) * env(n, .5, 2.0, 2.5, hold=2.0)
    glug = grains(sec, r, 60, lambda r, k: bubble(.15, r.uniform(120, 400), 1.6, .05) * r.uniform(.2, .7) * (1 - k / 70),
                  spread=lambda k, r: (k / 60) * 5.0 + r.uniform(0, .1))
    return reverb(swirl * .6 + glug * .6, 2.4, .35)


@sfx("sfx.water.warn", -12, "백의 밤", "새벽 30초 전 경고: 멀리 하류에서 물이 차오르는 낮은 우르르가 점점 커지고, 바닥 물웅덩이가 떨리는 찰랑(4초)", bypass_cast=True, use="물 차오름 30초 전(화면 가장자리 물빛과 함께). 천도 중에도 들리게")
def _(r):
    sec = 4.2; n = int(sec * SR); t = T(sec)
    rumble = filt(noise(n, r), "low", 220) * np.clip(t / 3.5, 0, 1) ** 1.5
    roar = filt(noise(n, r), "band", 600, .7) * np.clip(t / 3.5, 0, 1) ** 2 * .4
    ripple = grains(sec, r, 20, lambda r, k: bubble(.06, r.uniform(800, 1400), 1.3, .01) * .2, spread=lambda k, r: 1.5 + r.uniform(0, 2.5))
    return reverb(rumble + roar + ripple, 2.6, .35)


@sfx("amb.water.rising", -16, "백의 밤", "새벽 물 차오름(2분 동안 반복): 사방에서 물이 밀려 들어와 차오르는 쏴— 콸콸, 낮은 웅웅(반복용 10초)", loop=True, use="새벽 2분 물 차오름 내내. 코드가 시간에 따라 크기를 0.5→1.0으로 키울 것")
def _(r):
    sec = 10.2; n = int(sec * SR); t = T(sec)
    rush = filt(filt(noise(n, r), "band", 700, .5), "low", 3000) * (.8 + .2 * np.sin(2 * np.pi * t / 5.1))
    low = filt(noise(n, r), "low", 120) * .6
    burble = grains(sec, r, 100, lambda r, k: bubble(.1, r.uniform(200, 900), 2.0, .03) * r.uniform(.1, .4))
    return loopify(reverb(rush * .5 + low + burble * .4, 2.0, .3)[:n], .5)


@sfx("sfx.flood.pushup", -12, "백의 밤", "새벽 물에 떠밀려 위층으로: 물이 확 덮치는 쏴 + 몸이 들려 올라가는 우웅 + 계단 위로 철퍽 내려섬(2.2초, 벌 없음이라 무섭지 않게)", use="새벽까지 아래층에 남았을 때 가장 가까운 계단 위로 올라옴")
def _(r):
    sec = 2.4; n = int(sec * SR); buf = np.zeros(n)
    m = int(1.4 * SR)
    place(buf, sweep_filt(noise(m, r), "band", 300, 1500, .7) * env(m, .05, .5, 3, hold=.4) * .7, 0)   # 덮쳐 올라감
    place(buf, tone(1.2, 90, 160) * env(int(1.2 * SR), .1, .3, 3) * .3, .1)
    place(buf, _splash(r, .6, .8) * .6, 1.55)
    return reverb(buf, 1.4, .25)


@sfx("sfx.thread.cut", -10, "백의 밤", "원념의 실을 끊음: 팽팽한 검은 물줄기가 젖은 소리로 툭 끊기며 낮게 튕기는 웅— (0.8초)", use="백을 묶은 실을 사슬로 끊을 때(무릎 꿇리기 직전)")
def _(r):
    sec = 1.0; n = int(sec * SR); buf = np.zeros(n)
    place(buf, filt(noise(int(.03 * SR), r), "band", 1800, 1.5) * env(int(.03 * SR), .0005, .008), 0)        # 끊어지는 순간
    place(buf, tone(.8, 320, 140, .02, 11) * env(int(.8 * SR), .002, .2, 3) * .5, 0)                          # 튕기는 실
    place(buf, _splash(r, .4, .4) * .5, .02)                                                                   # 물줄기라 젖은 소리
    return reverb(buf, 1.0, .2)


@sfx("amb.thread.hum", -24, "백의 밤", "원념의 실 가까이: 몸과 혼을 잇는 실이 팽팽하게 가늘게 우는 소리(반복용 6초)", loop=True, use="백 곁(실이 보이는 거리)에서 3D로 작게. 실이 끊기면 멈춤")
def _(r):
    sec = 6.2; n = int(sec * SR)
    return loopify(reverb(_thread_hum(r, sec, 310, 3), 1.5, .3)[:n], .5)


@sfx("sfx.baek.kneel", -10, "백의 밤", "백이 무릎 꿇음: 젖은 흙에 무릎이 털썩 + 흙이 밀림 + 요령 대신 아주 낮은 나무 방울 하나(1.3초)", use="백 맺힘 0 — 눕히기/깨뜨리기 고를 때(시즌1 sfx.kneel 의 백 판)")
def _(r):
    sec = 1.5; n = int(sec * SR); buf = np.zeros(n)
    place(buf, _thump(r, .25, 90, 400) * .8, 0)
    place(buf, _mud(r, .5, 6) * .7, .02)
    place(buf, modal(1.0, [(523, .4, 1), (1046, .15, .3), (1570, .08, .15)], r) * .25, .3)                  # 낮은 목탁 같은 방울
    return reverb(buf, 1.6, .3)


@sfx("sfx.baek.laydown", -9, "백의 밤", "눕히기 완료: 이름을 부른 몸이 흙에 눕는다 — 흙이 숨을 내쉬듯 가라앉고, 맑은 방울 한 번이 위로 멀어진다(3초)", use="눕히기 캐스팅 끝(시즌1 천도 마무리의 백 판)")
def _(r):
    sec = 3.4; n = int(sec * SR); buf = np.zeros(n)
    place(buf, _settle(r, 2.4, 1.0), 0)
    place(buf, modal(2.2, [(784, .9, 1), (1568, .4, .35), (2352, .2, .15)], r) * .3, .9)                    # 맑은 방울(G5)
    place(buf, sweep_filt(noise(int(1.5 * SR), r), "band", 1200, 3500, 2) * env(int(1.5 * SR), .4, .5, 3) * .08, 1.2)   # 위로 멀어짐
    return reverb(buf, 2.4, .35)


@sfx("sfx.baek.stepaside", -14, "백의 밤", "비켜서는 백: 이미 이름을 찾은 몸이 스스로 일어나 흙을 털고 한 걸음 비켜선다 — 싸움 없이(1.6초)", use="7·8막: 시즌1·2에서 천도한 사람의 백에 다가갈 때")
def _(r):
    sec = 1.8; n = int(sec * SR); buf = np.zeros(n)
    place(buf, _mud(r, .5, 8) * .5, 0)                                                                         # 흙에서 몸이 빠짐
    place(buf, grains(.6, r, 25, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 3500), 3) * env(int(.004 * SR), .0003, .0015) * .2), .4)   # 흙 털림
    place(buf, _thump(r, .15, 120, 600) * .5, 1.1)                                                           # 한 걸음
    return reverb(buf, 1.6, .3)


@sfx("sfx.baek.break", -5, "백의 밤", "깨뜨리기: 몸이 흙·물째 터지는 둔한 폭발 + 반음 부딪는 쇳소리(파혼과 같은 찜찜함) + 흙비가 후드득(1.8초)", use="깨뜨리기 폭발(시즌1 sfx.pahon.burst 의 백 판)")
def _(r):
    sec = 1.9; n = int(sec * SR); buf = np.zeros(n)
    place(buf, sweep_filt(noise(n, r), "low", 2500, 140) * env(n, .002, .45, 3), 0)
    place(buf, tone(1.6, 58, 38) * env(int(1.6 * SR), .003, .4, 3) * .9, 0)
    place(buf, modal(1.4, [(1661, .2, 1), (1760, .2, 1)], r) * .12, 0)
    place(buf, grains(1.3, r, 40, lambda r, k: filt(noise(int(.01 * SR), r), "band", r.uniform(800, 2500), 2) * env(int(.01 * SR), .001, .004) * r.uniform(.1, .4),
                      spread=lambda k, r: .25 + r.exponential(.3)), 0)                                         # 흙비
    return reverb(buf, 1.6, .25, tone_hz=2200)


@sfx("sfx.farlight.on", -15, "백의 밤", "저편 나룻불 하나가 켜짐: 아주 먼 곳에서 작은 불이 훅 + 맑고 여린 화음 한 번(시즌3 진행 막대)(2.4초)", use="눕힌 혼의 배가 저편에 닿을 때 / 서낭당에서 저편 불빛이 늘 때")
def _(r):
    sec = 2.6; n = int(sec * SR); buf = np.zeros(n)
    place(buf, filt(noise(int(.4 * SR), r), "band", 700, 1) * env(int(.4 * SR), .05, .1) * .25, 0)
    chord = sum(modal(2.2, [(f, .9, 1), (f * 2, .3, .2)], r) for f in (587.3, 880.0, 1174.7)) * .18
    place(buf, filt(chord, "low", 5000), .1)
    return reverb(buf, 2.8, .5, tone_hz=4000)


# ---- 시즌3 보스 11종 전투음 (B-21~B-31, 서사 season3_outline.json) ----
# 시즌1·2 보스와 같은 규칙: 예비동작(예고)은 bypass_cast 로 천도·눕히기 중에도 들리고, 실제 공격은 더 크고 짧다.
# 백 보스는 말하지 않으므로 '목소리' 대신 몸·흙·물·실·사물 소리로만 성격을 낸다.
def _buf(sec):
    """빈 소리판(sec초)"""
    return np.zeros(int(sec * SR))


def _creak(r, sec, f=180, rough=30, bp=700):
    """나무·밧줄 삐걱: 낮은 음을 울퉁불퉁 끊어(rough Hz) 띠 필터로 깎음"""
    m = int(sec * SR)
    c = tone(sec, f * 1.2, f) * (1 + .6 * np.sign(np.sin(2 * np.pi * rough * T(sec)))) * env(m, sec * .2, sec * .4, 3, hold=sec * .2)
    return filt(c, "band", bp, 1.5)


def _rope_taut(r, sec, f=95):
    """밧줄이 팽팽하게 당겨짐: 섬유가 끼이익 우는 낮은 마찰음 + 아주 낮은 웅"""
    m = int(sec * SR)
    fric = filt(noise(m, r), "band", 900, 3) * (.6 + .4 * np.sin(2 * np.pi * 23 * T(sec))) * .5
    return (fric + tone(sec, f, f * 1.15) * .4) * env(m, sec * .3, sec * .3, 3, hold=sec * .3)


def _drum(r, f=70, dec=.35, a=1.0):
    """큰 북 한 번: 낮은 둥 + 가죽 때리는 퍽"""
    m = int((dec * 3) * SR)
    return (tone(dec * 3, f * 1.5, f) * env(m, .002, dec, 3) + filt(noise(m, r), "band", 500, 1) * env(m, .001, .03) * .5) * a


def _hands(r, sec, count=6):
    """흙에서 손이 솟음: 젖은 흙이 위로 밀리며 찌걱 + 손가락이 흙을 긁는 사각"""
    b = _buf(sec)
    place(b, _mud(r, sec, count * 2, (120, 320)), 0)
    place(b, grains(sec, r, count * 3, lambda r, k: filt(noise(int(.03 * SR), r), "band", r.uniform(1500, 3000), 2) * env(int(.03 * SR), .005, .01) * r.uniform(.1, .3)), 0)
    place(b, sweep_filt(noise(len(b), r), "low", 250, 900) * env(len(b), sec * .5, sec * .2, 3) * .5, 0)
    return b


# B-21 윤 영감 — ① 소 밑(물 빠진 바닥의 나룻배)
@sfx("sfx.boss.yun.sweep.telegraph", -12, "보스", "윤 영감 배 휩쓸기 예고: 물 없는 바닥에서 뒤집힌 나룻배가 진흙을 긁으며 크게 삐걱 기울어짐(0.6초)", bypass_cast=True, use="B-21: 배 휩쓸기 예비동작")
def _(r):
    b = _buf(.8)
    place(b, _creak(r, .55, 150, 28, 600) * .7, 0)
    place(b, _mud(r, .6, 8, (100, 260)) * .6, .05)
    return reverb(b, 1.2, .25)


@sfx("sfx.boss.yun.sweep", -9, "보스", "윤 영감 배 휩쓸기: 나룻배 한 척이 바닥 뻘을 쓸며 휙 지나감 — 묵직한 나무 몸통 + 흙탕이 확 튐(0.9초)", use="B-21: 배 휩쓸기 판정")
def _(r):
    b = _buf(1.1); m = int(.8 * SR)
    place(b, sweep_filt(noise(m, r), "band", 300, 900, .8) * env(m, .1, .25, 3, hold=.15) * .8, 0)          # 배가 지나가는 바람
    place(b, _thump(r, .35, 70, 300) * .9, .2)                                                              # 나무 몸통
    place(b, _splash(r, .6, .9) * .6, .25)                                                                  # 흙탕
    return reverb(b, 1.2, .2)


@sfx("sfx.boss.yun.hands", -11, "보스", "윤 영감 맺힘 50%: 소 바닥에서 빠진 이들의 손이 사방에서 솟아오름 — 젖은 흙 밀림·긁힘(1.5초)", use="B-21 ② 손 솟음 장판 시작")
def _(r):
    return reverb(_hands(r, 1.5, 8), 1.6, .3)


@sfx("sfx.boss.yun.waist", -14, "보스", "윤 영감 맺힘 25%: 빠졌던 물이 허리까지 다시 차오름 — 낮은 콸콸 + 웅(2초)", use="B-21 ③ 허리 물(이동 느려짐)과 함께")
def _(r):
    b = _buf(2.2); m = int(2 * SR)
    place(b, filt(noise(m, r), "low", 700) * env(m, .8, .6, 3, hold=.4) * .7, 0)
    place(b, grains(2, r, 25, lambda r, k: bubble(.1, r.uniform(250, 700), 1.6, .03) * r.uniform(.2, .6)), 0)
    return reverb(b, 2.0, .35, tone_hz=2500)


@sfx("sfx.boss.yun.letgo", -13, "보스", "윤 영감이 노를 놓음: 손에서 미끄러진 노가 물에 철벙 — 그리고 고요, 물이 잔잔히 가라앉음(2.5초)", bypass_cast=True, use="B-21 맺힘 0: 영감이 노를 놓을 때(BGM 줄이기)")
def _(r):
    b = _buf(2.8)
    place(b, _thump(r, .2, 110, 500) * .5, 0)
    place(b, _splash(r, .7, .7) * .7, .05)
    place(b, _still_water(r, 2.2, 8) * env(int(2.2 * SR), .3, .8, 3) * .3, .5)
    return reverb(b, 2.4, .35)


# B-22 일곱 뱃사람 — ⑤ 난파 여울 바닥
@sfx("sfx.boss.seven.rope.telegraph", -12, "보스", "일곱 뱃사람 밧줄 휘두르기 예고: 젖은 밧줄이 머리 위에서 부웅 부웅 두 바퀴(0.6초)", bypass_cast=True, use="B-22: 밧줄 휘두르기 예비동작")
def _(r):
    b = _buf(.75); m = int(.65 * SR); t = T(.65)
    whoosh = filt(noise(m, r), "band", 500, 1.2) * (.3 + .7 * np.abs(np.sin(2 * np.pi * 3.1 * t))) * env(m, .1, .2, 3, hold=.3)
    place(b, whoosh * .8, 0)
    return reverb(b, .9, .2)


@sfx("sfx.boss.seven.rope.pull", -10, "보스", "일곱 뱃사람 밧줄 당기기: 밧줄이 몸에 감겨 확 당겨짐 — 섬유 끼이익 + 물 튐(0.8초)", use="B-22: 밧줄 당김 판정(끌려감)")
def _(r):
    b = _buf(1.0)
    place(b, filt(noise(int(.05 * SR), r), "band", 1200, 1) * env(int(.05 * SR), .001, .015) * .8, 0)    # 휙 감김
    place(b, _rope_taut(r, .6, 90) * .9, .03)
    place(b, _splash(r, .4, .5) * .5, .1)
    return reverb(b, 1.0, .2)


@sfx("sfx.boss.seven.liftone", -12, "보스", "여섯이 하나를 끌어 올림: 여섯 몸이 한 줄을 동시에 당기는 끄응 — 끄응 두 번 + 물에서 몸 하나가 들림(1.8초)", use="B-22 맺힘 50%: 여섯이 막내를 끌어 올리는 장면(전투 중 연출)")
def _(r):
    b = _buf(2.0)
    for at in (0, .7):
        place(b, _rope_taut(r, .5, 80) * .8, at)
        place(b, _thump(r, .2, 85, 350) * .5, at + .05)
    place(b, _splash(r, .6, .8) * .6, 1.25)
    return reverb(b, 1.4, .3)


@sfx("sfx.boss.seven.kneel", -11, "보스", "일곱이 함께 무릎 꿇음: 젖은 모래에 일곱 무릎이 거의 한꺼번에 털썩 — 조금씩 어긋난 일곱 번(1.4초)", bypass_cast=True, use="B-22 맺힘 0")
def _(r):
    b = _buf(1.6)
    for k in range(7):
        place(b, _thump(r, .2, r.uniform(80, 110), 380) * r.uniform(.4, .7), .03 + k * .045 + r.uniform(0, .02))
    place(b, _mud(r, .6, 10) * .5, .05)
    return reverb(b, 1.6, .3)


# B-23 매듭 — ⑦ 닻 여울(실 덩어리)
@sfx("sfx.boss.knot.tighten.telegraph", -12, "보스", "매듭 조이기 예고: 수천 가닥 실이 한꺼번에 팽팽해지며 음이 위로 끼이잉 올라감(0.6초)", bypass_cast=True, use="B-23: 조이기 예비동작")
def _(r):
    b = _buf(.75); m = int(.65 * SR)
    hum = _thread_hum(r, .65, 300, 5)
    place(b, sweep_filt(hum * 2, "band", 300, 900, 2) * env(m, .5, .1, 3) * .9, 0)
    return reverb(b, .9, .25)


@sfx("sfx.boss.knot.tighten", -9, "보스", "매듭 조이기: 실 덩어리가 확 오므라들며 안쪽을 조임 — 젖은 실 뭉치가 쥐어짜이는 끄윽 + 물이 짜여 나옴(0.8초)", use="B-23: 조이기 판정")
def _(r):
    b = _buf(1.0)
    place(b, _rope_taut(r, .5, 120), 0)
    place(b, _mud(r, .5, 10, (200, 500)) * .7, .05)
    place(b, grains(.6, r, 14, lambda r, k: bubble(.07, r.uniform(700, 1600), 1.6, .012) * r.uniform(.2, .5)), .1)
    return reverb(b, 1.0, .25)


@sfx("sfx.boss.knot.untie", -13, "보스", "실 한 가닥 풀림: 엉킨 실 하나가 스르륵 빠져나오며 음이 낮게 풀림(0.7초)", use="B-23: 매듭 한 곳을 사슬로 풀 때(약점)")
def _(r):
    b = _buf(.9); m = int(.7 * SR)
    place(b, filt(noise(m, r), "band", 1600, 2) * env(m, .05, .25, 3) * .4, 0)
    place(b, tone(.7, 420, 260) * env(m, .02, .3, 3) * .4, 0)
    return reverb(b, 1.2, .3)


@sfx("sfx.boss.knot.snag", -11, "보스", "나룻배가 실에 걸림: 뱃사공의 배가 실 덩어리에 걸려 쿵 멈추고 뱃전이 끼익(1.2초)", bypass_cast=True, use="B-23 맺힘 25%: 뱃사공 배 걸림 연출")
def _(r):
    b = _buf(1.4)
    place(b, _thump(r, .3, 75, 300) * .8, 0)
    place(b, _creak(r, .7, 170, 26, 650) * .6, .15)
    place(b, _thread_hum(r, .8, 330, 4) * env(int(.8 * SR), .01, .3, 3) * .5, .05)
    return reverb(b, 1.4, .3)


# B-24 두 군대 — ③ 큰 무덤 속·화살골 뿌리
@sfx("sfx.boss.armies.drum", -10, "보스", "번호 호령의 북: 흙 속에서 울리는 큰 북 세 번(둥 둥 둥) — 다음 돌격 신호(1.4초)", bypass_cast=True, use="B-24: 돌격 예비동작(북이 세 번 울린 뒤 돌격)")
def _(r):
    b = _buf(1.8)
    for k in range(3):
        place(b, _drum(r, 62, .3, .9), k * .42)
    return reverb(filt(b, "low", 2500), 2.2, .35, tone_hz=1800)


@sfx("sfx.boss.armies.charge", -8, "보스", "두 군대 돌격: 흙 몸들이 한 줄로 밀려옴 — 수십 발 흙 밟는 우르르 + 녹슨 창끝 쩔렁(1.2초)", use="B-24: 돌격 판정")
def _(r):
    b = _buf(1.4); m = int(1.2 * SR)
    place(b, grains(1.2, r, 60, lambda r, k: _thump(r, .1, r.uniform(70, 110), 400) * r.uniform(.2, .5)), 0)
    place(b, filt(noise(m, r), "low", 500) * env(m, .3, .4, 3, hold=.3) * .6, 0)
    place(b, grains(1.0, r, 10, lambda r, k: _stone_hit(r, .4) * r.uniform(.1, .3)), .1)
    return reverb(b, 1.3, .25, tone_hz=2500)


@sfx("sfx.boss.armies.fall", -12, "보스", "흙 몸들이 쓰러짐: 한 줄이 흙더미로 무너져 내림 — 둔한 털썩 여럿 + 흙이 쏟아짐(1.5초)", use="B-24 맺힘 50%·25%: 한 패의 몸이 무너질 때")
def _(r):
    b = _buf(1.7)
    for k in range(8):
        place(b, _thump(r, .25, r.uniform(60, 90), 300) * r.uniform(.4, .7), k * .12 + r.uniform(0, .05))
    place(b, _settle(r, 1.4, .8), .1)
    return reverb(b, 1.6, .3)


@sfx("sfx.boss.armies.flags", -13, "보스", "두 깃발이 엇갈려 눕음: 두 군기가 천천히 기울다 X자로 흙에 눕는 펄럭 — 툭(2초)", bypass_cast=True, use="B-24 맺힘 0: 두 깃발이 X자로 누울 때")
def _(r):
    b = _buf(2.2); sec = 1.4
    place(b, _flutter(sec, r, np.linspace(.6, .1, int(sec * SR)), (5, 10), 1800) * .5, 0)
    place(b, _thump(r, .25, 90, 400) * .5, 1.3)
    place(b, _thump(r, .25, 80, 380) * .45, 1.45)
    return reverb(b, 1.8, .3)


# B-25 칠성 — ④ 막힌 막장 안쪽
@sfx("sfx.boss.chilseong.collapse.telegraph", -11, "보스", "막장 무너짐 예고: 천장 흙이 사르르 먼저 흘러내리고 버팀목이 끄으응(0.7초)", bypass_cast=True, use="B-25: 천장 무너짐 예비동작(떨어질 자리)")
def _(r):
    b = _buf(.9)
    place(b, grains(.7, r, 40, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 4000), 3) * env(int(.004 * SR), .0003, .0015) * r.uniform(.1, .4)), 0)
    place(b, _creak(r, .6, 110, 18, 450) * .6, .05)
    return reverb(b, 1.0, .25)


@sfx("sfx.boss.chilseong.collapse", -7, "보스", "막장 무너짐: 흙과 돌이 쿠르릉 쏟아져 내림 — 낮은 굉음 + 돌 굴러떨어짐(1.4초)", use="B-25: 무너짐 판정")
def _(r):
    b = _buf(1.6); m = int(1.4 * SR)
    place(b, sweep_filt(noise(m, r), "low", 1500, 150) * env(m, .005, .5, 3) * .9, 0)
    place(b, tone(1.2, 55, 38) * env(int(1.2 * SR), .005, .4, 3) * .8, 0)
    place(b, grains(1.2, r, 18, lambda r, k: _stone_hit(r, .2) * r.uniform(.2, .5), spread=lambda k, r: r.exponential(.3)), 0)
    return reverb(b, 1.4, .3, tone_hz=2200)


@sfx("sfx.boss.chilseong.dig", -12, "보스", "칠성의 파는 손: 흙 속에서 손 여럿이 바깥을 향해 파고드는 사각사각(반복용 3초)", loop=True, use="B-25 ② 파는 손 장판(근처에서 3D)")
def _(r):
    sec = 3.2; b = _buf(sec)
    place(b, grains(sec, r, 45, lambda r, k: filt(noise(int(.05 * SR), r), "band", r.uniform(1200, 2800), 2) * env(int(.05 * SR), .01, .015) * r.uniform(.2, .5)), 0)
    place(b, _mud(r, sec, 8, (150, 300)) * .3, 0)
    return loopify(reverb(b, 1.0, .25)[:int(sec * SR)], .3)


@sfx("sfx.boss.chilseong.prop", -11, "보스", "버팀목 받치기: 사슬로 끌어온 통나무가 천장 밑에 쿵 박힘 — 나무 울림 + 흙이 멈춤(0.9초)", use="B-25: 플레이어가 버팀목을 세울 때(무너짐 막기)")
def _(r):
    b = _buf(1.1)
    place(b, modal(.8, [(180, .25, 1), (420, .12, .5), (760, .06, .3)], r) * .7, 0)
    place(b, _thump(r, .25, 80, 350) * .6, 0)
    return reverb(b, 1.2, .25)


@sfx("sfx.boss.chilseong.count", -18, "보스", "소리 없이 세는 숫자: 일곱이 속으로 하나씩 세는 듯한 아주 낮은 맥박 일곱 번(그중 하나는 비어 있음)(4.5초)", use="B-25 맺힘 0 직전 연출 — 말 대신 맥박. 일곱째 자리가 비어 '하나 모자람'")
def _(r):
    b = _buf(4.8)
    for k in range(7):
        if k == 5: continue                                    # 한 자리는 비어 있다(돌아오지 못한 하나)
        place(b, _drum(r, 48, .25, .6) * (1 - k * .06), .2 + k * .6)
    return reverb(filt(b, "low", 900), 2.6, .4, tone_hz=1200)


# B-26 두 겹의 역병 — ② 석회 구덩이·역병막 마루 밑
@sfx("sfx.boss.plague.breath", -16, "보스", "역병의 숨: 마른 석회 가루를 머금은 탁한 숨이 장판처럼 깔림 — 쿨럭이는 듯한 낮은 바람(반복용 4초)", loop=True, use="B-26 ① 역병 숨 안개 장판(안에 있을 때)")
def _(r):
    sec = 4.2; n = int(sec * SR); t = T(sec)
    x = filt(noise(n, r), "band", 600, .6) * (.5 + .5 * np.sin(2 * np.pi * .5 * t) ** 2) * .6
    x += filt(noise(n, r), "high", 3000) * .06
    return loopify(reverb(x, 1.0, .3)[:n], .4)


@sfx("sfx.boss.plague.crack", -10, "보스", "석회 띠가 갈라짐: 바닥 흰 띠가 쩍 갈라지며 가루가 확 피어오름(0.8초)", use="B-26: 석회 띠 갈라짐 판정")
def _(r):
    b = _buf(1.0)
    place(b, grains(.15, r, 12, lambda r, k: filt(noise(int(.006 * SR), r), "band", r.uniform(2000, 5000), 3) * env(int(.006 * SR), .0003, .002) * r.uniform(.4, 1)), 0)
    place(b, _thump(r, .2, 100, 600) * .6, 0)
    m = int(.7 * SR); place(b, filt(noise(m, r), "high", 1500) * env(m, .05, .25, 3) * .35, .05)
    return reverb(b, 1.0, .2)


@sfx("sfx.boss.plague.fall", -10, "보스", "아래 겹으로 떨어짐: 마루가 꺼지며 한 층 더 밑(역병막 마루 밑)으로 쿵 — 판자 부서짐(1.2초)", use="B-26 맺힘 50%: 바닥이 꺼져 다음 겹으로")
def _(r):
    b = _buf(1.4)
    place(b, grains(.3, r, 14, lambda r, k: modal(.15, [(r.uniform(300, 900), .04, 1)], r) * r.uniform(.2, .5)), 0)
    place(b, sweep_filt(noise(int(.5 * SR), r), "band", 800, 250, 1) * env(int(.5 * SR), .2, .1, 3) * .4, .05)
    place(b, _thump(r, .4, 60, 300) * 1.0, .55)
    return reverb(b, 1.5, .3)


@sfx("sfx.boss.plague.stones", -12, "보스", "돌 마흔 개가 일어섬: 바닥 곳곳에서 작은 돌이 하나씩 딸깍 딸깍 세워짐 — 점점 빨라짐(3초)", bypass_cast=True, use="B-26 맺힘 0: 마흔 개의 돌이 일어설 때")
def _(r):
    sec = 3.2; b = _buf(sec)
    ts = np.cumsum(np.linspace(.13, .03, 40))
    for k, at in enumerate(ts):
        place(b, modal(.12, [(r.uniform(1800, 2600), .02, 1), (r.uniform(3500, 4500), .01, .4)], r) * .3, .1 + at * (2.6 / ts[-1]))
    return reverb(b, 2.0, .35)


# B-27 이명 / 흑월의 몸 — ⑥ 성문 밖 구덩이
@sfx("sfx.boss.imyeong.write", -12, "보스", "언 땅에 글씨: 손가락이 언 흙을 긁어 획을 긋는 끼익 — 획마다 바닥이 차갑게 울림(0.8초)", bypass_cast=True, use="B-27: 땅 글씨 공격 예비동작(획이 그어진 자리가 터짐)")
def _(r):
    b = _buf(1.0); m = int(.6 * SR)
    place(b, filt(noise(m, r), "band", 2400, 3) * env(m, .05, .2, 3, hold=.25) * .5, 0)
    place(b, modal(.7, [(1320, .2, 1), (1980, .1, .4)], r) * .15, .5)
    return reverb(b, 1.4, .3, tone_hz=4000)


@sfx("sfx.boss.imyeong.gate", -17, "보스", "성문이 닫혀 감: 아주 큰 나무 문이 천천히 끄으으응 밀리는 소리(반복용 6초) — 120초 동안 코드가 크기를 키울 것", loop=True, use="B-27 ② 성문 닫힘(그림자 줄어듦) 내내. 남은 시간이 줄수록 크게")
def _(r):
    sec = 6.2; n = int(sec * SR); t = T(sec)
    groan = filt(tone(sec, 58, 58) * (1 + .5 * np.sign(np.sin(2 * np.pi * 9 * t + 2 * np.sin(2 * np.pi * .3 * t)))), "band", 300, 1.2) * .5
    grind = filt(noise(n, r), "band", 180, .8) * .4
    return loopify(reverb(groan + grind, 2.0, .35, tone_hz=1500)[:n], .5)


@sfx("sfx.boss.imyeong.freeze", -11, "보스", "땅이 얼어붙음: 발밑 흙이 순식간에 쩌적 얼며 퍼져 나감 — 차갑고 높은 갈라짐(1초)", use="B-27: 언 땅 장판 생김")
def _(r):
    b = _buf(1.2)
    place(b, grains(.8, r, 50, lambda r, k: filt(noise(int(.005 * SR), r), "band", r.uniform(3000, 7000), 4) * env(int(.005 * SR), .0002, .0015) * r.uniform(.2, .7),
                    spread=lambda k, r: (k / 50) * .8), 0)
    place(b, tone(.9, 2200, 1500) * env(int(.9 * SR), .01, .3, 3) * .05, 0)
    return reverb(b, 1.6, .35, tone_hz=6000)


@sfx("sfx.boss.imyeong.unbind", -10, "보스", "사슬이 풀림: 흑월의 몸을 감던 사슬이 한 바퀴씩 차르르 풀려 언 땅에 떨어짐(2.2초)", bypass_cast=True, use="B-27 맺힘 0 직전: 몸을 묶은 사슬이 풀릴 때")
def _(r):
    b = _buf(2.4)
    for k in range(9):
        place(b, modal(.25, [(r.uniform(2400, 3200), .05, 1), (r.uniform(4800, 5600), .02, .5)], r) * r.uniform(.15, .35), .1 + k * .17 + r.uniform(0, .03))
    place(b, _thump(r, .3, 90, 500) * .6, 1.8)
    return reverb(b, 1.8, .3)


@sfx("sfx.boss.imyeong.finish", -12, "보스", "10초 마무리: 성문 앞 언 땅이 녹으며 똑, 똑 — 사이사이 아무것도 없는 고요(10초)", bypass_cast=True, use="B-27 마무리 10초(BGM은 이 동안 멈춤)")
def _(r):
    sec = 10; b = _buf(sec)
    for k, at in enumerate((1.2, 3.0, 4.4, 6.1, 7.0, 8.6)):
        place(b, bubble(.2, r.uniform(700, 1000), 1.7, .05) * .4, at)
    m = int(sec * SR); place(b, filt(noise(m, r), "band", 350, .5) * env(m, 2.0, 3.0, 2, hold=3) * .05, 0)
    return reverb(b, 3.0, .45)


# B-28 벼루지기의 몸 — ⑧ 먹 앙금
@sfx("sfx.boss.byeoru.grind.telegraph", -12, "보스", "천장 벼루 갈기 예고: 머리 위 큰 벼루가 돌기 시작하며 돌과 돌이 그르르 갈림(0.7초)", bypass_cast=True, use="B-28: 회전 갈기 예비동작")
def _(r):
    b = _buf(.9); m = int(.7 * SR); t = T(.7)
    place(b, filt(noise(m, r), "band", 260, 1) * (.5 + .5 * np.abs(np.sin(2 * np.pi * 6 * t))) * env(m, .3, .1, 3, hold=.2) * .8, 0)
    return reverb(b, 1.2, .3)


@sfx("sfx.boss.byeoru.grind", -9, "보스", "벼루 갈기: 천장 돌판이 한 바퀴 휩쓸며 아래를 갊 — 묵직한 그르르릉 + 먹물이 튐(1.2초)", use="B-28: 회전 판정")
def _(r):
    b = _buf(1.4); m = int(1.1 * SR); t = T(1.1)
    place(b, filt(noise(m, r), "band", 200, .8) * (.6 + .4 * np.abs(np.sin(2 * np.pi * 9 * t))) * env(m, .05, .4, 3, hold=.3), 0)
    place(b, tone(1.1, 50, 45) * env(m, .05, .4, 3, hold=.3) * .6, 0)
    place(b, _splash(r, .5, .5) * .4, .6)
    return reverb(b, 1.3, .25)


@sfx("sfx.boss.byeoru.inkrain", -12, "보스", "먹비: 천장에서 굵은 먹물 방울이 후드득 쏟아짐 — 끈적하게 철벅(1.5초)", use="B-28: 먹비 장판 생김")
def _(r):
    sec = 1.5; b = _buf(sec)
    place(b, grains(sec, r, 60, lambda r, k: bubble(.12, r.uniform(250, 600), 1.4, .04) * r.uniform(.2, .6)), 0)
    place(b, filt(noise(int(sec * SR), r), "low", 1200) * env(int(sec * SR), .1, .5, 3, hold=.4) * .25, 0)
    return reverb(b, 1.2, .25)


@sfx("sfx.boss.byeoru.hands", -11, "보스", "앙금에서 손: 검은 진흙에서 손들이 꿀렁 솟아 발목을 쥠(1.2초)", use="B-28 ② 앙금 손 + 느린 웅덩이")
def _(r):
    b = _hands(r, 1.2, 6)
    place(b, tone(1.0, 90, 70) * env(int(1.0 * SR), .2, .3, 3) * .3, 0)
    return reverb(b, 1.3, .3)


# B-29 사잣밥 할미 — ⑨ 아랫목
@sfx("sfx.boss.halmi.table", -13, "보스", "상 차림: 할미가 상을 놓고 밥그릇·나물 접시를 달각 달각 놓음(1.5초) — 놓인 자리에 상이 깔림", bypass_cast=True, use="B-29: 상 차림 공격 예비동작(상 둘레가 장판)")
def _(r):
    b = _buf(1.7)
    place(b, _thump(r, .25, 120, 500) * .6, 0)
    for k, at in enumerate((.35, .6, .82, 1.05)):
        place(b, modal(.35, [(r.uniform(1500, 2200), .08, 1), (r.uniform(3200, 3900), .04, .4)], r) * .25, at)
    return reverb(b, 1.0, .2)


@sfx("sfx.boss.halmi.ondol.telegraph", -11, "보스", "구들 꺼짐 예고: 발밑 구들장이 뜨겁게 금 가며 틱틱 + 아래 고래에서 불바람 우—(0.7초)", bypass_cast=True, use="B-29: 구들 꺼짐 예비동작")
def _(r):
    b = _buf(.9); m = int(.7 * SR)
    place(b, grains(.6, r, 10, lambda r, k: filt(noise(int(.005 * SR), r), "band", r.uniform(2000, 4000), 3) * env(int(.005 * SR), .0003, .002) * r.uniform(.3, .7)), 0)
    place(b, filt(noise(m, r), "band", 250, .8) * env(m, .3, .2, 3, hold=.1) * .6, 0)
    return reverb(b, 1.0, .25)


@sfx("sfx.boss.halmi.ondol", -8, "보스", "구들 꺼짐: 구들장이 쿵 내려앉고 재와 불티가 확 일어남(1.1초)", use="B-29: 구들 꺼짐 판정(뜨거운 칸 생김)")
def _(r):
    b = _buf(1.3); m = int(1.0 * SR)
    place(b, _thump(r, .4, 65, 350) * 1.0, 0)
    place(b, grains(.4, r, 10, lambda r, k: modal(.2, [(r.uniform(400, 900), .05, 1)], r) * r.uniform(.2, .4)), 0)
    place(b, filt(noise(m, r), "high", 2000) * env(m, .03, .3, 3) * .3, .05)
    place(b, grains(.8, r, 25, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(3000, 6000), 3) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .3)), .1)
    return reverb(b, 1.2, .25)


@sfx("sfx.boss.halmi.hotcell", -20, "보스", "뜨거운 칸: 달궈진 구들 위에서 공기가 아지랑이처럼 지글(반복용 3초)", loop=True, use="B-29 뜨거운 칸 위에 있을 때")
def _(r):
    sec = 3.1; n = int(sec * SR)
    x = filt(noise(n, r), "high", 4000) * (.5 + .5 * filt(r.standard_normal(n), "low", 6) / .05).clip(0, 2) * .15
    x += grains(sec, r, 20, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(3000, 6000), 3) * env(int(.003 * SR), .0002, .001) * r.uniform(.1, .3))
    return loopify(x, .3)


@sfx("sfx.boss.halmi.shoes", -14, "보스", "짚신을 내밂: 할미가 짚신 한 켤레를 상 위에 가만히 놓음 — 짚 바스락 + 툭(1.2초)", bypass_cast=True, use="B-29 맺힘 0: 짚신을 건넬 때(BGM 줄이기)")
def _(r):
    b = _buf(1.4)
    place(b, _crinkle(r, .5, 30, (1500, 4000), (.1, .35)), 0)
    place(b, _thump(r, .15, 150, 700) * .35, .55)
    place(b, _thump(r, .15, 140, 650) * .3, .72)
    return reverb(b, 1.2, .25)


# B-30 어머니의 몸 — ⑩ 첫 우물 밑
@sfx("sfx.boss.mother.wave", -13, "보스", "우물 파도: 둥근 벽을 따라 물이 3초 동안 차오르며 커졌다(쏴아) 5초 동안 빠짐 — 8초 한 주기(반복용 8초)", loop=True, use="B-30 파도형 장판. 주기를 코드 타이머(3초 오름/5초 내림)와 맞춰 0초에 시작")
def _(r):
    sec = 8.0; n = int(sec * SR); t = T(sec)
    lvl = np.where(t < 3, t / 3, 1 - (t - 3) / 5) ** 1.5
    wn = noise(n, r)
    x = (filt(wn, "low", 600) * (1 - lvl) + filt(wn, "low", 2000) * lvl) * (.15 + .85 * lvl)   # 물이 높을수록 밝고 크게
    x += grains(sec, r, 40, lambda r, k: bubble(.1, r.uniform(300, 900), 1.6, .03) * r.uniform(.1, .4)) * .5
    x = reverb(x, 2.0, .35, tone_hz=2500)[:n]
    return x  # 8초 주기 그 자체가 반복 단위(끝과 처음이 모두 '가장 낮음'이라 이음매가 없다)


@sfx("sfx.boss.mother.rope.hold", -12, "보스", "새끼줄 붙잡기(3초): 우물 줄을 사슬로 감아 버티는 끼이익 — 3초 동안 점점 팽팽해짐", use="B-30: 줄 붙잡기 1회(3번 필요). 성공 때마다 재생")
def _(r):
    b = _buf(3.2)
    place(b, _rope_taut(r, 3.0, 85) * np.linspace(.4, 1, int(3.0 * SR)), 0)
    place(b, _creak(r, .6, 200, 30, 800) * .4, 2.4)
    return reverb(b, 1.4, .3)


@sfx("sfx.boss.mother.oar", -13, "보스", "뱃사공이 노를 기댐: 위에서 노 하나가 우물 벽에 기대어져 쿵 — 나무가 둥글게 울림(1.5초)", bypass_cast=True, use="B-30 맺힘 25%: 뱃사공이 노를 우물에 기댈 때(줄 대신 노)")
def _(r):
    b = _buf(1.7)
    place(b, modal(1.3, [(140, .4, 1), (330, .2, .5), (610, .1, .3)], r) * .7, 0)
    place(b, _creak(r, .5, 160, 25, 600) * .3, .1)
    return reverb(b, 2.4, .45, tone_hz=2500)


@sfx("sfx.boss.mother.shoe", -16, "보스", "작은 신 한 짝: 우물 바닥 물에 아이 신 한 짝이 톡 떨어져 동동 뜸(1.6초)", bypass_cast=True, use="B-30 맺힘 0: 작은 신이 떠오를 때(BGM 거의 0)")
def _(r):
    b = _buf(1.8)
    place(b, bubble(.25, 520, 1.8, .05) * .5, 0)
    place(b, grains(1.2, r, 6, lambda r, k: bubble(.15, r.uniform(800, 1200), 1.5, .04) * r.uniform(.05, .15), t0=.2), 0)
    return reverb(b, 2.6, .5)


# B-31 나의 백 — ① 소 가장 깊은 곳(물속)
@sfx("sfx.boss.mybaek.torch", -20, "보스", "물속 횃불: 물속에서 꺼지지 않고 타는 불 — 먹먹한 웅 + 불꽃 대신 물거품이 보글(반복용 4초)", loop=True, use="B-31 내내 횃불 곁(3D)")
def _(r):
    sec = 4.1; n = int(sec * SR); t = T(sec)
    x = filt(noise(n, r), "low", 400) * (.6 + .4 * np.sin(2 * np.pi * .7 * t)) * .5
    x += grains(sec, r, 30, lambda r, k: bubble(.12, r.uniform(400, 900), 2.0, .03) * r.uniform(.1, .3))
    return loopify(filt(x, "low", 1500), .3)


@sfx("sfx.boss.mybaek.tether", -11, "보스", "사슬 끝 8m 당김: 나와 나의 백을 잇는 사슬이 끝까지 늘어나 팽 — 물속이라 먹먹한 쇠 울림(0.9초)", use="B-31: 거리 8m에 닿아 사슬이 팽팽해질 때")
def _(r):
    b = _buf(1.1)
    place(b, filt(modal(.9, [(r.uniform(900, 1100), .2, 1), (r.uniform(2300, 2600), .1, .4)], r), "low", 1800) * .6, 0)
    place(b, _rope_taut(r, .5, 70) * .5, 0)
    return reverb(filt(b, "low", 2000), 1.6, .4, tone_hz=1500)


@sfx("sfx.boss.mybaek.child", -14, "보스", "아이의 실(개똥이): 가늘고 높은 실 한 가닥이 떨리며 우는 소리 — 다가가면 가만히 끊어짐(2초)", bypass_cast=True, use="B-31 맺힘 50%: 개똥이의 실이 보일 때")
def _(r):
    b = _buf(2.2); m = int(1.6 * SR)
    place(b, _thread_hum(r, 1.6, 660, 2) * env(m, .3, .5, 3, hold=.5) * .7, 0)
    place(b, filt(noise(int(.02 * SR), r), "band", 3000, 2) * env(int(.02 * SR), .0005, .005) * .3, 1.6)
    return reverb(filt(b, "low", 3000), 2.0, .45)


@sfx("sfx.boss.mybaek.lights", -14, "보스", "일곱 불빛: 물 위 저편에서 나룻불 일곱이 하나씩 켜짐 — 맑은 방울 일곱(물 너머라 먹먹)(4초)", bypass_cast=True, use="B-31 맺힘 25%: 일곱 불이 켜질 때(시즌1·2 천도한 이들)")
def _(r):
    b = _buf(4.6)
    notes = (587.3, 659.3, 784.0, 880.0, 987.8, 1174.7, 1318.5)
    for k, f in enumerate(notes):
        place(b, modal(1.6, [(f, .9, 1), (f * 2, .3, .25)], r) * .22, .2 + k * .5)
    return reverb(filt(b, "low", 2600), 2.8, .5, tone_hz=2500)


@sfx("sfx.boss.mybaek.push", -10, "보스", "밀어 보냄: 내가 나의 백을 위로 밀어 올림 — 물이 크게 갈라지는 우웅 + 몸이 멀어지며 수면으로(1.8초)", use="B-31 맺힘 0: 밀어 보내기")
def _(r):
    b = _buf(2.0); m = int(1.6 * SR)
    place(b, sweep_filt(noise(m, r), "low", 300, 1500) * env(m, .1, .5, 3, hold=.4) * .8, 0)
    place(b, tone(1.4, 70, 140) * env(int(1.4 * SR), .1, .5, 3) * .4, 0)
    place(b, grains(1.4, r, 30, lambda r, k: bubble(.1, r.uniform(500, 1400), 2.0, .02) * r.uniform(.1, .4), t0=.3), 0)
    return reverb(b, 2.0, .4, tone_hz=2500)


@sfx("sfx.boss.mybaek.finish", -14, "보스", "15초 마무리: 물속의 먹먹함이 천천히 걷히고(수면으로 오름) — 마지막에 아주 먼 새벽 강물과 방울 한 번(15초)", bypass_cast=True, use="B-31 마무리 15초(BGM 멈춤) → 결말 컷신으로")
def _(r):
    sec = 15; n = int(sec * SR); t = T(sec)
    water = sweep_filt(noise(n, r), "low", 250, 3000) * np.clip(1 - t / 12, 0, 1) * .3
    river = filt(noise(n, r), "band", 900, .6) * np.clip((t - 9) / 4, 0, 1) * .12
    b = water + river
    place(b, modal(3.0, [(784, 1.4, 1), (1568, .5, .3)], r) * .25, 12.2)
    return reverb(b, 3.0, .4)

# ===== 시즌3 컷신 89컷 요청 소리 26개 (서사 cutscenes_s3.json 의 sfx_request, 2026-10-25 밤) =====
# 규칙은 시즌3 절과 같다: 백은 말하지 않고, 아래층은 젖은 흙·물·실·사슬로 채운다.
# 게임 중 소리(sfx.baek.*·sfx.thread.cut 등)와 이름이 다른 것은 '컷신용 판'이라서다 — 컷신은 화면이 가까워 더 작고 자세하다.
def _chain_links(r, sec, count, spread=None, muffle=4500):
    """사슬 고리 여럿이 부딪침: 짧은 쇳소리 알갱이(높은 울림 + 낮은 몸통)"""
    one = lambda r, k: modal(.08, [(r.uniform(2000, 3600), .02, 1), (r.uniform(450, 700), .03, .35)], r) * r.uniform(.15, .45)
    return filt(grains(sec, r, count, one, spread=spread), "low", muffle)


@sfx("amb.underwater.low", -24, "컷신", "물속의 먹먹한 낮은 울림: 귀가 물에 잠긴 듯 웅— + 아주 느린 거품, 높은 소리는 전혀 없음(반복용 12초)", loop=True, use="C-21 16.0 · C-27A/B 48.0 · C-30 0.0 · B31-INTRO 0.0 (물속 장면 내내 깔고 장면이 바뀌면 끔)")
def _(r):
    sec = 12.2; n = int(sec * SR); t = T(sec)
    hum = filt(noise(n, r), "low", 220) * (.7 + .3 * np.sin(2 * np.pi * t / 6.1)) * .9
    hum += tone(sec, 55, 55) * .12 * (.6 + .4 * np.sin(2 * np.pi * t / 4.07))
    bub = grains(sec, r, 14, lambda r, k: bubble(.25, r.uniform(180, 420), 1.6, .07) * r.uniform(.15, .4))
    return loopify(filt(reverb(hum + bub, 2.5, .4, tone_hz=900)[:n], "low", 900), .5)


@sfx("cut.water.rise", -12, "컷신", "물이 빠르게 차오름: 사방에서 물이 밀려와 쏴아— 콸콸 높아지며 커짐(2.5초)", use="S3-DAWN-PUSH 0.0 · B21-FLOOD 0.0")
def _(r):
    sec = 2.6; b = _buf(sec); m = int(2.4 * SR)
    place(b, sweep_filt(noise(m, r), "band", 300, 1400, .7) * env(m, 1.2, .5, 3, hold=.4) * .8, 0)
    place(b, filt(noise(m, r), "low", 300) * env(m, .8, .6, 3, hold=.6) * .6, 0)
    place(b, grains(2.2, r, 40, lambda r, k: bubble(.08, r.uniform(400, 1200), 1.7, .02) * r.uniform(.1, .4)), .3)
    return reverb(b, 1.4, .3)


@sfx("cut.water.rise.far", -14, "컷신", "멀리서 물이 차오르기 시작: 아주 먼 하류에서 낮은 우르르가 차츰 커짐(2초)", bypass_cast=True, use="S3-DAWN-WARN 0.0 (게임 중 경고는 sfx.water.warn, 이것은 컷 2초 판)")
def _(r):
    sec = 2.3; b = _buf(sec); m = int(2.1 * SR)
    place(b, filt(noise(m, r), "low", 380) * np.linspace(0, 1, m) ** 1.5 * .9, 0)
    place(b, filt(noise(m, r), "band", 700, 1) * np.linspace(0, 1, m) ** 2 * .25, 0)
    return reverb(b, 2.2, .45, tone_hz=1500)


@sfx("sfx.laydown", -11, "컷신", "몸이 젖은 흙에 천천히 눕는 소리: 무릎·어깨가 차례로 내려앉는 둔한 털썩 둘 + 젖은 흙 찌걱 + 천 스침(1.8초) — 방울 없음", use="BAEK-LAY · B21~B30-LAY · C-31A 6.0: 몸이 눕는 순간(눕히기 완료음 sfx.baek.laydown 과 따로)")
def _(r):
    b = _buf(2.0)
    place(b, _thump(r, .25, 85, 380) * .6, 0)
    place(b, _thump(r, .3, 70, 320) * .8, .55)
    place(b, _mud(r, .9, 9, (120, 300)) * .6, .05)
    m = int(.8 * SR); place(b, filt(noise(m, r), "band", 1500, 1) * env(m, .15, .3, 3) * .12, .3)      # 젖은 천 스침
    return reverb(b, 1.4, .25)


@sfx("cut.thread.snap", -12, "컷신", "검은 실이 끊김(컷신판): 물줄기 같은 실이 툭 — 낮게 웅 튕기고 물이 똑 떨어짐(1초)", use="Bxx-KNEEL 0.0 · C-23B 0.0")
def _(r):
    b = _buf(1.2)
    place(b, filt(noise(int(.025 * SR), r), "band", 1300, 1.5) * env(int(.025 * SR), .0005, .007), 0)
    place(b, tone(.9, 240, 110, .02, 9) * env(int(.9 * SR), .002, .25, 3) * .5, 0)
    place(b, bubble(.15, 700, 1.7, .03) * .3, .35)
    return reverb(b, 1.2, .25)


@sfx("cut.bones.crumble", -10, "컷신", "젖은 흙과 뼈가 함께 부서짐: 둔하게 와르르 — 마른 나무 같은 뼈 부딪침 + 흙덩이 철퍽(1.5초)", use="Bxx-BREAK 0.0 (sfx.baek.break 폭발 바로 뒤에 겹침)")
def _(r):
    b = _buf(1.7)
    place(b, _thump(r, .3, 65, 300) * .8, 0)
    place(b, grains(1.0, r, 26, lambda r, k: modal(.1, [(r.uniform(600, 1300), .025, 1), (r.uniform(1800, 2600), .012, .3)], r) * r.uniform(.1, .4),
                    spread=lambda k, r: r.exponential(.25)), .03)
    place(b, _mud(r, 1.0, 10, (100, 260)) * .6, .1)
    return reverb(b, 1.3, .25, tone_hz=2500)


@sfx("cut.chain.taut", -12, "컷신", "사슬이 팽팽하게 당겨짐: 고리들이 차르륵 일어서다 팽 — 쇠가 낮게 끄응(1.3초)", use="C-27A/B 20.0 · C-30 26.0")
def _(r):
    b = _buf(1.5)
    place(b, _chain_links(r, .5, 14, spread=lambda k, r: (k / 14) * .45), 0)
    place(b, modal(.9, [(r.uniform(850, 950), .25, 1), (r.uniform(2100, 2300), .1, .3)], r) * .35, .48)
    place(b, _rope_taut(r, .7, 75) * .4, .45)
    return reverb(b, 1.4, .3)


@sfx("cut.chain.fall", -12, "컷신", "사슬이 흙 위로 감기며 떨어짐: 고리가 차르르르 둥글게 쌓이며 흙에 묻히는 먹먹한 소리(1.8초)", use="B27-LAY 8.0 · C-31A 140.0")
def _(r):
    b = _buf(2.0)
    place(b, _chain_links(r, 1.5, 36, spread=lambda k, r: (k / 36) ** .8 * 1.4, muffle=3000), 0)
    for k in range(4): place(b, _thump(r, .12, 120, 500) * .3, .2 + k * .32)
    return reverb(b, 1.3, .25)


@sfx("cut.rewind.soft", -16, "컷신", "거꾸로 감김: 종이 장이 뒤에서 앞으로 부드럽게 넘어가는 소리 — 소리 자체를 거꾸로 뒤집어 '빨려 들듯' 끝남(2.4초)", use="RITE-REVERSE 0.0 · LEDGER-REVERSE 0.0")
def _(r):
    sec = 2.4; b = _buf(sec)
    for k in range(6):
        at = .1 + k * .34
        place(b, _paper(r, .3, 1200, 6000, .01) * .5, at)
        place(b, _crinkle(r, .12, 8, (2500, 6000), (.1, .3)), at + .05)
    b = reverb(b, 1.4, .35)[::-1].copy()       # 울림까지 거꾸로 = 꼬리가 앞으로 와서 시간이 되감기는 느낌
    return b


@sfx("cut.thread.reel", -14, "컷신", "실이 감겨 올라감: 가는 실이 위로 말려 올라가며 음이 끼잉 올라감 + 물방울 몇(2초)", use="THREAD-RISE 0.0 · C-23A 0.0")
def _(r):
    sec = 2.1; b = _buf(sec); m = int(1.8 * SR)
    place(b, sweep_filt(_thread_hum(r, 1.8, 300, 3) * 2, "band", 350, 1400, 2.5) * env(m, .3, .5, 3, hold=.7) * .6, 0)
    place(b, grains(1.6, r, 6, lambda r, k: bubble(.1, r.uniform(900, 1500), 1.6, .02) * .2), .2)
    return reverb(b, 1.5, .35)


@sfx("cut.soil.shift", -13, "컷신", "젖은 흙에서 몸이 일어남: 흙이 몸에서 떨어지며 찌걱 + 흙알 사르르 + 무릎 펴는 둔한 소리(1.6초)", use="STEP-ASIDE 0.0 · C-24 36.0(B-05 천도판)")
def _(r):
    b = _buf(1.8)
    place(b, _mud(r, .8, 12, (140, 380)) * .6, 0)
    place(b, grains(1.0, r, 30, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 3500), 3) * env(int(.004 * SR), .0003, .0015) * r.uniform(.05, .25)), .4)
    place(b, _thump(r, .2, 100, 420) * .4, 1.1)
    return reverb(b, 1.3, .25)


@sfx("cut.hull.beach", -12, "컷신", "나무배가 모래에 올라앉음: 배 밑이 모래를 스으윽 밀고 올라가 쿵 멈춤 + 판자 삐걱(1.8초)", use="C-23A 38.0 · C-23B 36.0")
def _(r):
    b = _buf(2.0); m = int(1.1 * SR)
    place(b, filt(noise(m, r), "band", 900, .8) * env(m, .2, .3, 3, hold=.5) * .5, 0)          # 모래 밀림
    place(b, _thump(r, .35, 75, 300) * .8, 1.05)
    place(b, _creak(r, .5, 180, 26, 650) * .35, 1.15)
    return reverb(b, 1.4, .25)


@sfx("cut.hull.scrape", -12, "컷신", "뒤집힌 나무배가 바닥을 긁음: 배 등판이 뻘·자갈을 끄으윽 끌며 다가옴(1.8초)", use="B21-INTRO 3.0")
def _(r):
    b = _buf(2.0); m = int(1.6 * SR); t = T(1.6)
    place(b, filt(noise(m, r), "band", 450, .9) * (.6 + .4 * np.abs(np.sin(2 * np.pi * 7 * t))) * env(m, .3, .4, 3, hold=.6) * .7, 0)
    place(b, _creak(r, 1.0, 140, 22, 550) * .4, .3)
    place(b, _mud(r, 1.2, 8) * .4, .2)
    return reverb(b, 1.3, .25)


@sfx("cut.earth.drum", -12, "컷신", "땅속에서 울리는 북 같은 진동: 흙에 막힌 큰 북 둥— 둥— 둥, 높은 소리는 없음(3초)", use="C-24 24.0 · B24-INTRO 3.0(B-06 천도 아님 판)")
def _(r):
    b = _buf(3.4)
    for k in range(3): place(b, _drum(r, 52, .35, .9 - k * .1), .1 + k * .9)
    place(b, filt(noise(int(3.0 * SR), r), "low", 120) * .15, 0)
    return reverb(filt(b, "low", 600), 2.0, .4, tone_hz=900)


@sfx("cut.straw.tie", -14, "컷신", "짚신 끈을 맴: 짚이 바스락 비벼지고 끈을 두 번 쭉 당겨 묶음(1.4초)", use="B29-LAY 4.8")
def _(r):
    b = _buf(1.5)
    place(b, _crinkle(r, .6, 30, (1500, 4500), (.1, .35)), 0)
    for at in (.7, 1.0):
        m = int(.15 * SR); place(b, filt(noise(m, r), "band", 1800, 2) * env(m, .02, .06, 3) * .35, at)
    return reverb(b, .9, .2)


@sfx("cut.rope.taut", -12, "컷신", "젖은 밧줄이 팽팽해짐: 여섯이 한꺼번에 당긴 줄이 끄익 + 물이 짜여 똑똑(0.9초)", use="B22-INTRO 3.2")
def _(r):
    b = _buf(1.1)
    place(b, _rope_taut(r, .6, 95), 0)
    place(b, grains(.6, r, 6, lambda r, k: bubble(.07, r.uniform(800, 1500), 1.6, .015) * .25), .2)
    return reverb(b, 1.0, .2)


@sfx("cut.rope.fall", -14, "컷신", "새끼줄이 우물에 떨어짐: 줄이 스르르 미끄러져 내려와 우물 물에 철퍽 — 둥근 벽이 울림(1.8초)", use="B30-LAY 13.0")
def _(r):
    b = _buf(2.0); m = int(.7 * SR)
    place(b, filt(noise(m, r), "band", 1300, 1.2) * env(m, .3, .15, 3) * .3, 0)
    place(b, _splash(r, .6, .6) * .7, .7)
    return reverb(b, 2.6, .5, tone_hz=2500)


@sfx("cut.pole.lay", -12, "컷신", "나무 깃대 둘이 흙에 눕음: 긴 나무가 천천히 기울다 하나, 또 하나 둔하게 툭 — 나무 몸통이 낮게 울림(1.6초)", use="B24-LAY 4.8")
def _(r):
    b = _buf(1.8)
    for at in (.2, .55):
        place(b, modal(.6, [(r.uniform(160, 200), .2, 1), (r.uniform(420, 480), .08, .4)], r) * .5, at)
        place(b, _thump(r, .2, 90, 380) * .5, at)
    place(b, grains(1.0, r, 20, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 3500), 3) * env(int(.004 * SR), .0003, .0015) * .15), .3)
    return reverb(b, 1.2, .25)


@sfx("cut.lime.step", -15, "컷신", "마른 석회 가루를 밟음: 발이 고운 가루에 푹 — 사각, 세 걸음(1.8초)", use="B26-INTRO 0.0")
def _(r):
    b = _buf(1.9)
    for k in range(3):
        m = int(.18 * SR); at = .1 + k * .55
        place(b, filt(noise(m, r), "band", 2500, .8) * env(m, .01, .06, 3) * .4, at)
        place(b, _thump(r, .1, 110, 500) * .3, at)
    return reverb(b, .8, .15)


@sfx("cut.lime.crack", -11, "컷신", "굳은 석회가 갈라짐: 쩌억 — 흰 띠가 길게 금 가며 가루가 확 피어오름(1.1초)", use="B26-SPLIT 0.0")
def _(r):
    b = _buf(1.3)
    place(b, grains(.35, r, 30, lambda r, k: filt(noise(int(.006 * SR), r), "band", r.uniform(1800, 5000), 3) * env(int(.006 * SR), .0003, .002) * r.uniform(.3, 1),
                    spread=lambda k, r: (k / 30) * .3), 0)
    place(b, _thump(r, .25, 90, 500) * .6, .3)
    m = int(.7 * SR); place(b, filt(noise(m, r), "high", 1500) * env(m, .05, .25, 3) * .3, .35)
    return reverb(b, 1.0, .2)


@sfx("cut.gate.close", -10, "컷신", "큰 나무 성문이 닫힘: 문짝이 끄으으응 밀리다 쿵 — 빗장 소리(3초)", use="B27-GATE 0.0")
def _(r):
    b = _buf(3.4); m = int(2.0 * SR); t = T(2.0)
    groan = filt(tone(2.0, 62, 52) * (1 + .5 * np.sign(np.sin(2 * np.pi * 10 * t))), "band", 320, 1.2) * env(m, .4, .4, 3, hold=1.0) * .5
    place(b, groan, 0)
    place(b, _thump(r, .6, 50, 250) * 1.0, 2.0)
    place(b, modal(.5, [(r.uniform(700, 800), .12, 1), (r.uniform(1700, 1900), .05, .4)], r) * .3, 2.45)   # 빗장
    return reverb(b, 2.2, .35, tone_hz=2000)


@sfx("cut.cloth.wave", -16, "컷신", "무명 저고리가 바람에 크게 흔들림: 지붕 위에서 휘두르는 천이 펄럭 펄럭 + 높은 바람(4초)", use="C-31A 70.0")
def _(r):
    sec = 4.2; n = int(sec * SR); t = T(sec)
    g = .55 + .45 * np.abs(np.sin(2 * np.pi * .55 * t))           # 팔로 휘두르는 주기
    x = _flutter(sec, r, g, (6, 13), 1900) * .7
    x += filt(noise(n, r), "band", 700, .6) * (.3 + .3 * g) * .3
    return reverb(x, 1.2, .2)


@sfx("cut.book.set", -14, "컷신", "묶은 장부를 젖은 돌에 내려놓음: 두꺼운 종이 묶음이 툭 + 젖은 돌이라 살짝 철벅(0.8초)", use="C-28 36.0")
def _(r):
    b = _buf(1.0)
    place(b, _thump(r, .2, 140, 650) * .7, 0)
    place(b, _paper(r, .2, 1500, 5000, .004) * .25, 0)
    place(b, _splash(r, .25, .2) * .25, .01)
    return reverb(b, 1.0, .2)


@sfx("amb.wind.dry", -24, "컷신", "마른 들바람: 해 질 녘 붉은재 — 물기 없는 바람이 마른 풀을 쓸고 지나감, 새·벌레 없음(반복용 14초)", loop=True, use="C-24 0.0 (붉은재 큰 무덤, 장면이 봉분 안으로 들어가면 끔)")
def _(r):
    sec = 14.2; n = int(sec * SR)
    g = _gust_curve(sec, r, 3, .3)
    x = filt(noise(n, r), "band", 450, .5) * (.5 + .5 * g) * .6
    x += filt(filt(noise(n, r), "high", 2500), "low", 7000) * g * .12          # 마른 풀
    return loopify(x, .5)


@sfx("amb.ondol.fire", -24, "컷신", "아궁이 불: 작은 장작불이 타닥 타닥 + 고래로 빨려 드는 바람 우—(반복용 8초)", loop=True, use="B29-INTRO 0.0 (B-29 무대 내내 깔아도 됨)")
def _(r):
    sec = 8.2; n = int(sec * SR)
    x = filt(noise(n, r), "band", 250, .7) * .35
    x += grains(sec, r, 45, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 5000), 3) * env(int(.004 * SR), .0002, .0012) * r.uniform(.1, .5))
    x += grains(sec, r, 6, lambda r, k: _thump(r, .08, 160, 800) * .2)
    return loopify(reverb(x, .8, .2)[:n], .4)


@sfx("vo.far.reply", -20, "컷신", "아주 먼 물길에서 오는 짧은 대답: 사람 목소리 한마디가 물 너머로 — 말뜻은 전혀 안 들림, 아주 작게(1.6초)", use="B25-LAY 7.0(S-209 눕힘일 때만)")
def _(r):
    b = _buf(1.8); d = .55; m = int(d * SR)
    f = np.linspace(190, 165, m)
    place(b, voice(f, [(500, 4, 1), (900, 5, .4)], .4, r, nh=12) * env(m, .05, .2, 3, hold=.2), .2)
    return reverb(filt(b, "low", 550), 2.8, .6, tone_hz=900)

# ===== 시즌3 장례 대본(funerals_s3.json, 서사 PR #32) 요청 17종 + 먹방 '끊김' 3종 =====
# 장례는 이승 낮(산 사람 소리 허용)과 저승 새벽 틈(산 것 없음) 두 가지. 저승 쪽은 새·벌레 없이 고요하게.
def _sum(*xs):
    """길이가 다른 소리를 앞머리 맞춰 더함(짧은 쪽은 뒤를 0으로 채움)"""
    b = np.zeros(max(len(x) for x in xs))
    for x in xs:
        b[:len(x)] += x
    return b


def _wood_tap(r, f=900, dec=.03, a=1.0):
    """나무 '똑': 속 빈 나무 울림 두세 개 + 아주 짧은 닿는 소리"""
    y = modal(.25, [(f * r.uniform(.97, 1.03), dec, 1), (f * 2.3 * r.uniform(.98, 1.02), dec * .6, .45), (f * .52, dec * 1.4, .4)], r)
    k = int(.004 * SR); place(y, filt(noise(k, r), "high", 2500) * env(k, .0002, .001) * .5, 0)
    return y * a


@sfx("amb.crow.far", -22, "세계", "먼 까마귀 한 번: 골짜기 너머에서 까악— 한 마디, 메아리처럼 길게 사라짐(3초)", use="FUN-S-221·B24 등 장례 아침 0.0 (이승 낮에만)")
def _(r):
    b = _buf(3.2)
    for at, f, a in ((.1, 1.0, 1.0), (.52, .96, .7)):                      # 까악·까악(두 번째는 조금 낮고 작게)
        d = .34; f0 = curve(d, [(0, 500 * f), (.07, 590 * f), (d, 470 * f)])
        place(b, voice(f0, [(1150, 3, 1), (2300, 4, .45)], .55, r, nh=15) * env(int(d * SR), .015, .1, 3, hold=.1) * a, at)
    return reverb(filt(b, "low", 1900), 2.6, .65, tone_hz=1700)           # 멀리 → 높은 소리 깎고 울림 많이


@sfx("amb.river.morning", -26, "세계", "아침 강물: 잔잔하게 흐르는 물 — 낮은 흐름 쏴— + 돌 사이 작은 졸졸·퐁, 바람 거의 없음(반복용 14초)", loop=True, use="FUN-S-181·189·B21 등 이승 장례 아침 0.0")
def _(r):
    sec = 14.4; n = int(sec * SR); t = T(sec)
    flow = filt(noise(n, r), "band", 520, .6) * (.75 + .25 * np.sin(2 * np.pi * .13 * t + 1)) * .5      # 넓은 물 흐름
    ripple = filt(noise(n, r), "band", 1600, 1.2) * (.5 + .5 * np.abs(np.sin(2 * np.pi * .37 * t))) * .12  # 물결 반짝임
    plop = grains(sec, r, 70, lambda r, k: bubble(r.uniform(.03, .07), r.uniform(500, 1300)) * r.uniform(.05, .25))
    return loopify(reverb(flow + ripple + filt(plop, "low", 3500), 1.0, .2)[:n], .6)


@sfx("cut.bell.shaman", -15, "컷신", "무당 방울 한 번: 놋방울 여럿이 한 번 흔들려 짤랑— 하고 길게 사라짐(요령보다 작고 맑게, 2.5초)", use="FUN-S-283 10.0 (처음으로 소리가 남 / 문고리에 걸린 방울이 바람 없이 한 번)")
def _(r):
    pitches = [2650, 2980, 3370, 3720, 4210]                               # 크기가 조금씩 다른 방울 다섯
    def bell(r, k):
        f = pitches[k % 5] * r.uniform(.99, 1.01)
        return modal(2.2, [(f, .7, 1), (f * 1.006, .7, .6), (f * 2.76, .3, .35), (f * 5.4, .12, .15)], r) * r.uniform(.4, 1)
    y = grains(2.4, r, 9, bell, spread=lambda k, r: .02 + k * .028 + r.uniform(0, .012))   # 한 번 흔든 동안 방울들이 잇달아 닿음
    return reverb(y, 1.8, .3)


@sfx("cut.bell.small", -15, "컷신", "작은 종 한 번: 손바닥만 한 놋종을 종채로 땡— (맥놀이가 천천히 일렁이며 3초 사라짐)", use="FUN-S-284 10.0 (아이가 종을 한 번 침 / 종채만 놓여 있으면 쓰지 않음)")
def _(r):
    f = 1320
    y = modal(3.4, [(f, 1.6, 1), (f * 1.003, 1.6, .8), (f * 2.41, .9, .5), (f * 3.98, .5, .3), (f * 5.9, .25, .15), (f * .5, 1.0, .2)], r)
    k = int(.006 * SR); place(y, filt(noise(k, r), "band", 3500, 1) * env(k, .0002, .002) * .6, 0)   # 종채가 닿는 '딱'
    return reverb(y, 1.6, .25)


@sfx("cut.chain.scratch", -18, "컷신", "사슬 끝으로 한 줄 긋기: 쇠끝이 돌·나무를 가늘게 끼이익— 긁고, 사슬 고리가 짤랑 따라옴(1.4초)", use="반쪽 장례(-HALF) 6.0: F를 누르면 빈 돌·나무·팻말에 한 줄 (FUN-S-193~·S-217~·S-229~·S-253~ 새김 장례 관할)")
def _(r):
    sec = 1.5; b = _buf(sec); d = 1.0; m = int(d * SR); td = T(d)
    slip = .55 + .45 * (np.sin(2 * np.pi * 37 * td) > 0)                   # 걸렸다 미끄러지는 결(초당 37번)
    scr = filt(noise(m, r), "band", 4200, 2.5) * slip + filt(noise(m, r), "band", 1900, 4) * .4
    scr = scr * env(m, .03, .15, 3, hold=.7) * (.7 + .3 * np.sin(np.pi * td / d))
    place(b, scr, .12)
    place(b, _stone_hit(r, .5) * .5, .1)                                    # 처음 대는 '틱'
    place(b, _chain_links(r, sec, 6) * .5, 0)                               # 손에 쥔 사슬이 따라 흔들림
    return reverb(b, .6, .15)


@sfx("cut.flint.strike", -14, "컷신", "부싯돌 두 번: 쇠와 돌이 딱! 하며 불티가 치익 튐 × 2, 두 번째에 작은 불이 붙어 화르(2.2초)", use="FUN-S-199 19.0 (포구 사람이 등잔을 켬)")
def _(r):
    b = _buf(2.4)
    def strike(r, spark):
        y = _stone_hit(r, 1.3)
        sp = grains(.35, r, spark, lambda r, k: filt(noise(int(.002 * SR), r), "high", 4500) * env(int(.002 * SR), .0001, .0008) * r.uniform(.1, .5))
        place(y, sp, .005); return y
    place(b, strike(r, 12), .1)
    place(b, strike(r, 20) * 1.1, .85)
    m = int(1.2 * SR)                                                       # 심지에 불이 옮겨 붙는 작은 화르
    place(b, filt(noise(m, r), "band", 700, .8) * env(m, .15, .5, 3, hold=.3) * .35, 1.0)
    return reverb(b, .5, .12)


@sfx("cut.footstep.leave", -20, "컷신", "맨발 걸음이 멀어짐: 마루·흙바닥을 맨발로 사박 사박 여섯 걸음, 점점 작고 먹먹하게(4초)", use="저승 새벽 장례(⑧⑨, FUN-S-265~288) 10.0: 혼이 일을 놓고 줄 쪽으로 나감 · FUN-B28 20.0")
def _(r):
    sec = 4.2; b = _buf(sec)
    for k in range(6):
        g = (1 - k / 6.5)                                       # 걸음마다 작아짐
        d = .14; m = int(d * SR)
        step = _sum(filt(noise(m, r), "low", 900 - k * 90) * env(m, .004, .05, 3) * .8, _thump(r, .1, 110, 500) * .5)
        place(b, filt(step, "low", 2600 - k * 330) * g, .1 + k * .62 + r.uniform(-.03, .03))
    return reverb(b, 1.6, .3, tone_hz=2500)


@sfx("cut.kiln.light", -14, "컷신", "숯가마에 불 넣기: 장작 밀어 넣는 덜컥 + 불이 훅 붙어 가마 속으로 우우— 빨려 들며 타닥 타닥(4초)", use="FUN-S-192 19.0 (숯막 사람들이 다시 불을 넣음)")
def _(r):
    sec = 4.2; n = int(sec * SR); b = _buf(sec)
    place(b, _wood_tap(r, 420, .05) * .7, .05); place(b, _thump(r, .15, 120, 600) * .6, .08)   # 장작을 아궁이에 밀어 넣음
    m = int(3.6 * SR)
    whoosh = sweep_filt(noise(m, r), "low", 200, 900) * env(m, .5, 1.6, 3, hold=.8)           # 훅— 불이 붙음
    draft = filt(noise(m, r), "band", 160, 1.2) * env(m, 1.0, 1.2, 3, hold=1.0) * .8          # 가마 속으로 빨려 드는 낮은 우—
    place(b, whoosh * .6 + draft, .4)
    place(b, grains(3.4, r, 30, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 5000), 3) * env(int(.004 * SR), .0002, .0012) * r.uniform(.1, .5), t0=.7), 0)
    return reverb(b[:n], 1.0, .25)


@sfx("cut.knife.carve", -17, "컷신", "칼로 나무 새기기: 칼끝이 결을 따라 슥·슥 파고 작은 나뭇조각이 톡 떨어짐 × 여섯(4초)", use="새김 장례(②③④⑥, FUN-S-193~·S-217~·S-229~·S-253~) 19.0: 빈 돌·목패·버팀목·점호판에 이름을 새김")
def _(r):
    sec = 4.2; b = _buf(sec)
    for k in range(6):
        d = r.uniform(.25, .4); m = int(d * SR)
        cut = sweep_filt(noise(m, r), "band", 2600, 3800, 3) * env(m, .01, .06, 3, hold=d * .5) * .6
        cut += filt(noise(m, r), "band", 900, 3) * env(m, .005, .05, 3) * .35            # 나무 결이 울리는 몸통
        at = .1 + k * .65 + r.uniform(-.05, .05)
        place(b, cut, at)
        place(b, _wood_tap(r, r.uniform(1800, 2600), .012, .25), at + d + r.uniform(.03, .1))   # 조각이 톡
    return reverb(b, .5, .12)


@sfx("cut.stake.drive", -12, "컷신", "메로 말뚝 박기 세 번: 나무 메가 말뚝 머리를 퉁! — 젖은 흙으로 쑥 들어가는 둔한 울림 × 3(3초)", use="FUN-S-182 19.0 (갑술 영감이 말뚝을 마저 박음)")
def _(r):
    b = _buf(3.2)
    for k in range(3):
        at = .1 + k * .95
        place(b, _sum(_wood_tap(r, 260, .07, 1.0), _thump(r, .25, 85 - k * 5, 380) * 1.1), at)
        place(b, _mud(r, .3, 3, (100, 220)) * .4, at + .03)                # 젖은 흙이 받아 냄
    return reverb(b, .9, .2)


@sfx("cut.stone.roll", -13, "컷신", "큰 돌 굴리기: 무거운 돌이 흙길을 구르르 구르며 쿵 쿵 걸리고, 자갈이 깔려 부서짐(4.5초)", use="G-ELEVEN 5.0 · FUN-B24 12.0 (마을 사람들이 비석 돌을 굴려 옴)")
def _(r):
    sec = 4.6; n = int(sec * SR); t = T(sec)
    roll = filt(noise(n, r), "low", 140) * (.6 + .4 * np.sin(2 * np.pi * .9 * t) ** 2) * 1.4    # 한 바퀴마다 무게가 실림
    grit = grains(sec, r, 120, lambda r, k: filt(noise(int(.006 * SR), r), "band", r.uniform(1200, 3500), 2) * env(int(.006 * SR), .0003, .002) * r.uniform(.05, .3))
    y = roll + grit
    for at in (.7, 1.8, 2.9, 3.8):
        place(y, _thump(r, .2, 70, 300) * .9, at + r.uniform(-.06, .06))   # 돌 모서리가 땅에 걸리는 쿵
    return reverb(y * env(n, .5, .7, 3, hold=sec - 1.3), .8, .2)


@sfx("cut.tag.sway", -19, "컷신", "나무 목패가 서로 부딪침: 걸이에 걸린 목패 여럿이 흔들려 딸그락 딸그락 마른 나무 소리(2.5초)", use="FUN-B25 5.0 (목패 걸이의 열넷)")
def _(r):
    y = grains(2.6, r, 16, lambda r, k: _wood_tap(r, r.uniform(1100, 1900), .015, r.uniform(.2, .8)) * (1 - k / 20),
               spread=lambda k, r: .05 + (k ** .8) * .13 + r.uniform(-.03, .03))
    return reverb(y, .6, .15)


@sfx("cut.tool.set", -21, "컷신", "작은 물건 내려놓기: 붓·먹·열쇠를 상이나 벼루 위에 조용히 톡 — 나무 닿는 소리 + 아주 작은 쇠·돌 울림(0.6초)", use="저승 새벽 장례(⑧⑨, FUN-S-265~288) 10.0: 혼이 하던 일의 도구를 놓음 · FUN-B28 12.0")
def _(r):
    b = _buf(.7)
    place(b, _wood_tap(r, 1400, .02, .7), .02)
    place(b, modal(.4, [(r.uniform(2800, 3400), .06, .25), (r.uniform(5200, 6000), .03, .1)], r), .03)   # 열쇠·먹돌의 작은 울림(살짝만)
    place(b, _wood_tap(r, 1700, .012, .25), .11)                          # 한 번 더 자리 잡는 톡
    return reverb(b, .5, .12)


@sfx("cut.water.still", -22, "컷신", "물이 잔잔해짐: 우물 물결이 찰랑… 찰… 점점 작아지다 완전히 멈춤(3.5초, 끝은 무음)", use="FUN-S-298 10.0 (우물 물이 잔잔해짐, 무덤 하나가 끝남)")
def _(r):
    sec = 3.6; b = _buf(sec)
    for k in range(7):
        a = (1 - k / 7) ** 1.6                                            # 물결이 잦아듦
        place(b, filt(noise(int(.25 * SR), r), "band", 500 + k * 30, 2) * env(int(.25 * SR), .03, .12, 3) * a * .6, .05 + k * .42)
        if k < 4: place(b, bubble(.05, r.uniform(700, 1000)) * a * .2, .12 + k * .42)
    return reverb(b, 1.8, .35, tone_hz=2500)                              # 우물 돌벽 울림


@sfx("cut.well.bucket", -16, "컷신", "두레박 줄: 젖은 줄이 우물 턱을 스르륵 긁으며 끼익, 두레박이 턱에 툭 걸리고 물방울 똑(3초)", use="FUN-S-297 10.0 (노파가 두레박을 우물 턱에 걸고 감)")
def _(r):
    b = _buf(3.2)
    place(b, _rope_taut(r, 1.4, 110) * .8, .05)
    place(b, _creak(r, .8, 210, 26, 800) * .6, .4)                        # 도르래·턱 나무가 끼익
    place(b, _sum(_wood_tap(r, 340, .06, 1.0), _thump(r, .15, 130, 500) * .5), 1.55)   # 두레박이 턱에 툭
    place(b, _drips(r, 1.4, 4, 700, 1300), 1.75)
    return reverb(b, 1.2, .25)


@sfx("mus.boat.answer", -18, "컷신", "뱃노래 받는 소리만: 메기는 소리 없이 뱃사람 여럿이 '어—야—' 하고 받는 두 마디, 가사 안 들림, 바닷가 울림(7초)", use="FUN-S-198 19.0 (메기던 사람이 없다 — 앞소리는 일부러 없음)")
def _(r):
    sec = 7.4; b = _buf(sec)
    def phrase(dur, notes, voices):
        m = len(notes); pts = []
        for i, f in enumerate(notes):
            pts += [(dur * i / m, f), (dur * (i + .85) / m, f)]
        f0 = curve(dur, pts); y = np.zeros(int(dur * SR))
        for v in range(voices):                                           # 여럿이 조금씩 어긋나게
            fv = f0 * (1 + r.uniform(-.014, .014)) * (1 + .02 * np.sin(2 * np.pi * r.uniform(4.5, 6) * T(dur) + r.uniform(0, 6)))
            y += voice(fv, [(650, 4, 1), (1050, 5, .55), (2500, 8, .15)], .12, r, nh=25)   # '어'·'아' 사이 모음
        return y * env(len(y), .25, dur * .25, 3, hold=dur * .55)
    place(b, phrase(2.8, [220, 247, 220, 196], 7), .3)                   # 받는 소리 1
    place(b, phrase(3.2, [196, 220, 196, 165], 7) * .9, 3.6)             # 받는 소리 2(내려앉으며 끝남)
    return reverb(filt(b, "low", 2200), 2.4, .5, tone_hz=1800)


@sfx("vo.sumbi", -16, "컷신", "숨비소리: 해녀들이 물가에서 한 사람씩 '호오이—' 길게 내쉬는 휘파람 같은 숨 × 다섯, 높이가 조금씩 다름(9초)", use="FUN-S-195 19.0 (망사리를 묻고 한 번씩 숨비소리)")
def _(r):
    sec = 9.4; b = _buf(sec)
    for k in range(5):
        d = r.uniform(1.1, 1.5); m = int(d * SR)
        f = r.uniform(1700, 2300)
        f0 = curve(d, [(0, f * .9), (.15, f * 1.05), (d * .7, f), (d, f * .82)])     # 확 올라갔다가 길게 끌며 내려옴
        ph = 2 * np.pi * np.cumsum(f0) / SR
        tonal = np.sin(ph) * (.5 + .5 * filt(noise(m, r), "low", 30) * 3).clip(0, 1.5)  # 입술 휘파람(흔들리는 순음)
        air = filt(noise(m, r), "band", f * 1.1, 2.5) * .7                 # 숨 바람
        y = (tonal * .45 + air) * env(m, .06, .35, 3, hold=d * .5)
        place(b, y * r.uniform(.6, 1.0), .2 + k * 1.75 + r.uniform(-.1, .1))
    return reverb(filt(b, "low", 6000), 2.0, .45, tone_hz=3500)          # 바닷가 바위 울림


@sfx("cut.seal.set.nine", -18, "컷신", "멀리서 인 찍는 소리 아홉 번: 안쪽 방에서 도장이 쿵… 쿵… 일정하게 아홉 번, 먹먹하고 멀게(약 7초)", use="FUN-S-276 10.0 (멀리서 인 찍는 소리가 아홉 번 — cut.seal.set을 아홉 번 부르는 대신)")
def _(r):
    b = _buf(7.4)
    for k in range(9):
        n = int(.5 * SR)
        st = _sum(tone(.5, 130, 85) * env(n, .002, .07) + filt(noise(n, r), "low", 700) * env(n, .001, .03) * .5, _wood_tap(r, 520, .03, .4))
        place(b, st * (1 - .03 * k), .1 + k * .74 + r.uniform(-.02, .02))   # 일정한 손놀림
    return reverb(filt(b, "low", 1200), 2.2, .55, tone_hz=1200)          # 벽 너머라 높은 소리 없음


# ── FUN-B28 먹방: '먹 가는 소리가 처음으로 1초 끊김' ──
def _grinders(r, sec, count):
    """먹 가는 손 여럿: 각자 속도가 조금씩 다른 원 돌리기 사각사각을 겹침"""
    n = int(sec * SR); t = T(sec); y = np.zeros(n)
    for k in range(count):
        rate = r.uniform(.85, 1.25); ph = r.uniform(0, 6)
        speed = .35 + .65 * np.abs(np.sin(2 * np.pi * rate * t + ph))
        rub = filt(noise(n, r), "band", r.uniform(1100, 1700), .9) * speed
        wet = filt(noise(n, r), "low", 450) * speed * .4
        y += (rub * .5 + wet + filt(rub, "band", r.uniform(280, 360), 4) * .4) * r.uniform(.5, 1)
    return y / np.sqrt(count)


@sfx("cut.ink.grind.room", -22, "컷신", "먹방 전체가 먹을 감: 여러 손이 저마다의 빠르기로 사각사각 원을 그리는 소리가 겹친 큰 방(반복용 10초)", loop=True, use="FUN-B28-LAY 0.0 부터 깔기 (20.0에서 cut.ink.grind.stop 으로 넘김)")
def _(r):
    sec = 10.3; n = int(sec * SR)
    return loopify(reverb(_grinders(r, sec, 8), 1.4, .3)[:n], .5)


@sfx("cut.ink.grind.stop", -22, "컷신", "먹 가는 소리가 처음으로 끊김: 방 전체의 사각사각(0.5초) → 칼같이 멈춤 → 정확히 1.0초 거의 완전한 고요 → 몇 사람만 다시 갈기 시작(3명, 6초)", use="FUN-B28-LAY 20.0에 재생 + 같은 순간 cut.ink.grind.room 을 페이드 없이 끔 → 20.5~21.5 가 끊긴 1초(앞 0.5초가 이음매를 감춤)")
def _(r):
    sec = 7.5; n = int(sec * SR); b = np.zeros(n)
    room = reverb(_grinders(r, .5, 8), 1.4, .3)                            # 앞 0.5초는 room 과 같은 결(이어 붙는 자리)
    m = int(.5 * SR); room = room[:m] * env(m, .0, .0, 1, hold=.49)
    room[-int(.012 * SR):] *= np.linspace(1, 0, int(.012 * SR))          # 12ms 만에 뚝 — 울림 꼬리도 남기지 않음
    # 1.5초부터: 세 사람이 하나씩 다시 갈기 시작(울림은 이 부분에만 — 끊긴 1초에 앞소리 울림이 번지지 않게)
    for k, at in enumerate((1.5, 2.3, 3.4)):
        d = sec - at - .2; g = _grinders(r, d, 1) * env(int(d * SR), .6, 1.2, 3, hold=d - 1.8) * (.55 - k * .08)
        place(b, g, at)
    b = reverb(b, 1.0, .2)[:n]
    place(b, room, 0)
    # 0.5 ~ 1.5초: 무음(아주 작은 공기만 −60dB 근처로 깔아 '고장'이 아니라 '고요'로 들리게)
    place(b, filt(noise(int(1.0 * SR), r), "low", 200) * .001, .5)
    return b


# ===== 처음 10분에 빠진 소리 (기획 first-10min-benchmark M1·M3·M4·M6·M7·M9·M10, first-elite-and-dosul-cards) =====
# 원칙: 천도 보상(혼불)과 파혼 보상(엽전)은 같은 길이·같은 크기. 장비 빛줄기는 등급이 오를수록 '음이 하나씩 늘어남'(색 대신 귀로도 구분).
def _jing(r, f=150, sec=4.5, swell=.15):
    """징: 큰 놋쇠. 맞은 뒤 '웅~' 하고 부풀며 음이 아주 조금 올라가고, 맥놀이가 길게 운다"""
    n = int(sec * SR); t = T(sec); y = np.zeros(n)
    for k, a, d in ((1, 1, 2.2), (1.008, .7, 2.2), (1.47, .45, 1.3), (2.02, .35, 1.0), (2.68, .2, .6), (3.4, .12, .4)):
        ff = f * k * (1 + .012 * (1 - np.exp(-t / .6)))                  # 음이 살짝 올라감(징 특유)
        y += a * np.sin(2 * np.pi * np.cumsum(ff) / SR + r.uniform(0, 6.28)) * np.exp(-t / d)
    y *= np.clip(t / swell, 0, 1) * (.6 + .4 * np.clip(t / .5, 0, 1))     # 맞은 뒤에 부풂
    y += filt(noise(n, r), "low", 500) * np.exp(-t / .03) * .3             # 채의 '퍽'
    return y


def _orb_whoosh(r, sec, f0, f1, q=2.0):
    """빛 덩이가 날아옴: 좁은 띠 바람이 f0→f1로 올라가며 다가옴"""
    m = int(sec * SR)
    return sweep_filt(noise(m, r), "band", f0, f1, q) * env(m, sec * .7, sec * .2, 3)


def _chime(r, f, dec=.5, a=1.0):
    """맑은 한 음(놋 편경 비슷): 기본음 + 비조화 배음 둘"""
    return modal(dec * 3, [(f, dec, 1), (f * 2.76, dec * .4, .3), (f * 5.4, dec * .2, .1)], r) * a


# ── M6 품계 인 · 첫 손보기 ──
@sfx("sfx.rank.seal", -8, "UI", "품계 인이 찍힘: 명부 종이에 붉은 인이 쿵 + 바로 뒤 맑은 종 한 번이 길게(인 1.0초, 종 꼬리 2초)", use="M6 품계 승급 연출(화면 가운데 명부에 인이 찍히는 1.0초). 화면이 살짝 어두워질 때 다른 소리를 0.6배로 낮추기")
def _(r):
    b = _buf(3.2); n = int(.6 * SR)
    stamp = tone(.6, 120, 70) * env(n, .002, .09) + filt(noise(n, r), "low", 900) * env(n, .001, .03) * .6
    place(b, stamp, .05)
    place(b, _paper(r, .12) * .3, .03)                                    # 종이가 눌림
    bell = modal(3.0, [(392, 1.4, 1), (393.2, 1.4, .7), (941, .8, .4), (1530, .4, .2)], r)   # 종(G4) 맥놀이
    place(b, bell * .7, .18)
    return reverb(b, 1.8, .3)


@sfx("sfx.repair.first", -8, "UI", "손보기 성공: 쇠망치가 모루를 탕! 탕! 두 번 + 장비 이름이 금빛으로 번쩍하는 맑은 쨍—(품계 인과 같은 크기, 1.6초)", use="M6 첫 손보기 성공(이후 손보기 성공에도 씀)")
def _(r):
    b = _buf(2.6)
    for k, at in enumerate((.05, .42)):
        hit = modal(.8, [(r.uniform(1800, 2000), .25, 1), (r.uniform(3900, 4300), .12, .5), (r.uniform(640, 700), .3, .6)], r)
        place(b, hit * (.8 + .2 * k), at)
    for k, f in enumerate((1568, 2093, 2637)):                            # 금빛 번쩍 = 세 음이 아주 빠르게
        place(b, _chime(r, f, .5, .35), .82 + k * .04)
    return reverb(b, 1.4, .25)


# ── M3 처결 보상이 몸으로 ──
@sfx("sfx.reward.honbul", -14, "처결", "혼불 하나가 가슴에 들어옴: 맑은 바람이 쉬이— 다가오다 몸에 닿는 순간 따뜻한 한 음 '팅'(0.55초)", use="M3 천도 보상: 혼불 1~3개마다 하나씩(0.08초 간격, 높이 ±3% 무작위). 엽전 소리와 같은 길이·크기")
def _(r):
    b = _buf(.9)
    place(b, _orb_whoosh(r, .42, 900, 2600) * .6, 0)
    place(b, _chime(r, 1046, .18, .8), .40)                           # 몸에 닿음
    place(b, tone(.3, 262, 262) * env(int(.3 * SR), .01, .12, 3) * .35, .40)   # 가슴에 스미는 낮은 웅
    return reverb(b, .7, .2)


@sfx("sfx.reward.coin.pop", -15, "처결", "엽전이 튐: 파혼 뒤 엽전 3~5닢이 땅에서 짤랑 튀어 오름(0.3초)", use="M3 파혼 보상: 엽전이 튀는 순간")
def _(r):
    coin = lambda r, k: modal(.2, [(r.uniform(3800, 4600), .05, 1), (r.uniform(6400, 7600), .03, .5)], r) * r.uniform(.4, 1)
    return reverb(grains(.5, r, 5, coin, spread=lambda k, r: k * .035 + r.uniform(0, .02)), .4, .12)


@sfx("sfx.reward.coin.gather", -14, "처결", "엽전이 발밑으로 빨려 옴: 쉭— 끌려오다 허리춤에 짤랑 모임(0.55초, 혼불과 같은 길이·크기)", use="M3 파혼 보상: 튀고 0.6초 뒤 빨려 옴. 혼불 소리와 같은 길이·크기")
def _(r):
    b = _buf(.9)
    place(b, _orb_whoosh(r, .38, 2400, 900, 1.5) * .45, 0)                # 높은 데서 내려오는 쪽(혼불과 거울)
    coin = lambda r, k: modal(.25, [(r.uniform(3600, 4400), .07, 1), (r.uniform(6000, 7200), .04, .4)], r) * r.uniform(.5, 1)
    place(b, grains(.4, r, 6, coin, spread=lambda k, r: k * .022 + r.uniform(0, .01)), .38)
    place(b, _thump(r, .1, 160, 700) * .3, .40)
    return reverb(b, .5, .15)


@sfx("sfx.reward.bar.open", -18, "UI", "넋 막대가 처음 펼쳐짐: 한지 두루마리가 스르륵 펴지고 끝에 톡(0.3초)", use="M3 넋 막대·엽전 칸이 처음 나타날 때 한 번")
def _(r):
    b = _buf(.45)
    place(b, _paper(r, .26, 1500, 6000) * .6, 0)
    place(b, _wood_tap(r, 1500, .015, .4), .27)
    return reverb(b, .4, .1)


# ── M4 장비가 바닥에 떨어짐 · 등급 빛줄기 ──
@sfx("sfx.drop.land", -15, "전투", "장비가 바닥에 떨어짐: 툭 떨어져 한 번 튀는 작은 소리(0.4초) — 빛줄기 소리와 함께", use="M4 맺힘 0 때 장비가 떨어지는 순간(등급 무관)")
def _(r):
    b = _buf(.5)
    place(b, _thump(r, .12, 200, 900) * .7, 0)
    place(b, modal(.25, [(r.uniform(1400, 1800), .05, .5), (r.uniform(3200, 3800), .03, .25)], r), .005)
    place(b, _thump(r, .08, 260, 1100) * .25, .16)                         # 한 번 튐
    return reverb(b, .4, .1)


def _beam(r, notes, sec, shimmer=.3, low=0):
    """빛줄기: 아래에서 위로 쏟아지는 맑은 소리. notes 개수가 등급(1·2·3·…)"""
    b = _buf(sec)
    m = int(sec * SR)
    place(b, sweep_filt(noise(m, r), "band", 600, 5000, 3) * env(m, .25, sec * .5, 3) * shimmer, 0)   # 위로 솟는 바람
    for k, f in enumerate(notes):
        place(b, _chime(r, f, .7, .7 - k * .05), .08 + k * .09)
    if low:
        place(b, _jing(r, low, 2.5, .1) * .45, .05)
    return reverb(b, 1.6, .35)


@sfx("sfx.drop.beam.common", -20, "전투", "흔한 장비 빛줄기(미색): 맑은 한 음 '팅'이 위로 살짝 솟음(1초, 작게)", use="M4 흔한 등급 장비가 떨어졌을 때")
def _(r):
    return _beam(r, [880], 1.0, .15)


@sfx("sfx.drop.beam.fine", -17, "전투", "손본 장비 빛줄기(청록): 두 음 '팅·딩'이 위로 솟으며 반짝(1.4초)", use="M4 손본 등급 장비(거센 혼 확정 드롭 포함)")
def _(r):
    return _beam(r, [880, 1318], 1.4, .25)


@sfx("sfx.drop.beam.rare", -13, "전투", "귀한 장비 빛줄기(금빛): 세 음이 차르르 올라가 화음 + 반짝이는 쉬이—(2초, 멀리서도 들림)", use="M4 귀한 등급 장비(사나운 적 확정 드롭)")
def _(r):
    return _beam(r, [880, 1108, 1318, 1760], 2.0, .35)


@sfx("sfx.drop.beam.named", -11, "전투", "이름 있는 물건 빛줄기: 낮은 징이 웅— 받치고 그 위로 네 음이 차례로 솟는 큰 소리(2.8초)", use="이름 있는 물건(가장 높은 등급)이 떨어졌을 때")
def _(r):
    return _beam(r, [659, 880, 1108, 1318, 1760], 2.8, .4, low=110)


@sfx("sfx.pickup.gear", -16, "UI", "장비 줍기: 천에 싸 허리춤에 넣는 사락 + 작은 쇠 짤랑(0.35초)", use="M4 2m 안 자동 줍기 / F 줍기")
def _(r):
    b = _buf(.45)
    place(b, _paper(r, .2, 800, 4000) * .5, 0)
    place(b, modal(.2, [(r.uniform(2800, 3300), .05, .5), (r.uniform(4800, 5400), .03, .25)], r), .14)
    return reverb(b, .35, .1)


# ── M9 도술 카드 세 장 ──
@sfx("sfx.card.rise", -16, "UI", "카드 세 장이 올라옴: 한지 카드가 아래에서 스윽·스윽·스윽 펼쳐지고 아주 낮은 북 둥(0.5초)", use="M9 카드 세 장이 뜰 때(0.25초 펼침)")
def _(r):
    b = _buf(.8)
    for k in range(3):
        place(b, _paper(r, .16, 1200, 5000) * (.6 + .1 * k), k * .07)
    place(b, _drum(r, 90, .12, .4), .2)
    return reverb(b, .6, .15)


@sfx("sfx.card.flip", -17, "UI", "카드 뒤집기: 빳빳한 한지 한 장이 팔락 뒤집힘(0.18초)", use="M9 카드가 앞면으로 뒤집힐 때(한 장씩, 0.06초 간격)")
def _(r):
    b = _buf(.25)
    place(b, _paper(r, .1, 1800, 7000) * .7, 0)
    place(b, _wood_tap(r, 1900, .01, .25), .09)
    return b


@sfx("sfx.card.hover", -24, "UI", "카드 위에 올림: 종이 끝이 살짝 들리는 아주 작은 스윽(0.08초)", use="M9 마우스가 카드 위로/1·2·3 키로 고르기 전 강조")
def _(r):
    return _paper(r, .07, 2500, 7000) * .5


@sfx("sfx.card.pick", -10, "UI", "카드를 고름: 카드가 슉 날아가 스킬바 칸에 먹 도장처럼 꾹 박힘 + 맑은 한 음(0.8초)", use="M9 고른 카드가 0.5초 날아가 박히는 순간(날기 시작에 맞춰 재생, 박히는 소리는 0.48초에 있음)")
def _(r):
    b = _buf(1.4)
    place(b, _orb_whoosh(r, .46, 700, 2200, 1.4) * .5, 0)
    n = int(.4 * SR)
    place(b, tone(.4, 150, 95) * env(n, .002, .07) + filt(noise(n, r), "low", 800) * env(n, .001, .03) * .5, .48)   # 먹 찍힘
    place(b, _chime(r, 784, .4, .45), .5)
    return reverb(b, .9, .2)


@sfx("sfx.card.scatter", -19, "UI", "안 고른 두 장이 흩어짐: 종이 두 장이 바람에 휙 날아가며 사라짐(0.4초)", use="M9 고른 뒤 남은 두 장")
def _(r):
    b = _buf(.6)
    for k in range(2):
        m = int(.3 * SR)
        place(b, sweep_filt(noise(m, r), "band", 3000, 1200, 2) * env(m, .02, .2, 3) * .5, k * .06)
    return reverb(b, .5, .15)


@sfx("sfx.card.reroll", -15, "UI", "다시 뽑기: 엽전 짤랑 + 세 장이 한데 모여 촤라락 섞임(0.7초)", use="M9 '엽전 20 · 다시' 누름")
def _(r):
    b = _buf(1.0)
    coin = lambda r, k: modal(.2, [(r.uniform(3800, 4500), .05, 1)], r) * r.uniform(.4, .9)
    place(b, grains(.2, r, 4, coin), 0)
    place(b, _crinkle(r, .4, 18, (1500, 6000), (.1, .5)), .15)
    place(b, _wood_tap(r, 1300, .02, .4), .58)
    return reverb(b, .5, .12)


# ── M10 거센 혼(첫 강적: 두레 좌상 오봉 — 징으로 들일꾼을 모으던 사람) ──
@sfx("sfx.elite.appear", -8, "전투", "거센 혼 등장: 먼 징이 둔하게 한 번 + 땅이 울리는 큰 북 둥 + 낮게 끓는 숨 '흐으으'(1.8초) — 이름 띠 펼침과 함께", bypass_cast=True, use="M10 거센 혼이 처음 보일 때(이름 띠 0.6초 펼침에 맞춤). BGM 전투층 한 단계 위로 올리는 순간")
def _(r):
    b = _buf(3.0)
    place(b, filt(_jing(r, 120, 2.8, .08), "low", 1500) * .6, 0)
    place(b, _drum(r, 55, .5, 1.0), .02)
    d = 1.4; m = int(d * SR)
    f0 = curve(d, [(0, 70), (.5, 85), (d, 60)])
    place(b, voice(f0, [(350, 3, 1), (700, 4, .5)], .8, r, nh=20) * env(m, .3, .5, 3, hold=.5) * .5, .3)   # 낮은 숨(말 없음)
    return reverb(b, 1.6, .3)


@sfx("sfx.elite.slam.telegraph", -12, "전투", "거센 혼 내려치기 예고: 팔을 들며 무겁게 들이쉬는 숨 + 낮은 쇳소리가 1.2초 동안 차오름", bypass_cast=True, use="M10 내려치기 예고(1.2초, 첫 만남은 1.3배로 늘려 재생)")
def _(r):
    sec = 1.25; m = int(sec * SR)
    rise = sweep_filt(noise(m, r), "band", 200, 900, 2) * env(m, sec * .85, .1, 2)
    scr = filt(noise(m, r), "band", 1800, 6) * env(m, sec * .9, .08, 2) * .35
    f0 = curve(sec, [(0, 75), (sec, 110)])
    br = voice(f0, [(400, 3, 1)], .9, r, nh=10) * env(m, sec * .8, .1, 2) * .3
    return rise * .7 + scr + br


@sfx("sfx.elite.slam", -6, "전투", "거센 혼 내려치기: 땅이 쾅 꺼지는 큰 충격 + 흙이 튀고 낮게 울림(0.9초)", bypass_cast=True, use="M10 내려치기 맞는 순간(원 r 2.5m)")
def _(r):
    b = _buf(1.4)
    place(b, _drum(r, 48, .45, 1.2), 0)
    place(b, _stone_hit(r, .3) * .6, 0)
    place(b, grains(.6, r, 30, lambda r, k: filt(noise(int(.01 * SR), r), "band", r.uniform(800, 2500), 2) * env(int(.01 * SR), .001, .005) * r.uniform(.1, .4), t0=.03), 0)
    return reverb(b, 1.0, .2)


@sfx("sfx.elite.pounce.telegraph", -12, "전투", "거센 혼 덮치기 예고: 몸을 낮추며 짧게 그르릉 + 발이 흙을 긁음(1.0초)", bypass_cast=True, use="M10 덮치기 예고(앞으로 띠 6m, 1.0초)")
def _(r):
    sec = 1.0; b = _buf(sec + .1); m = int(sec * SR)
    f0 = curve(sec, [(0, 90), (sec, 120)]) * (1 + .1 * np.sign(np.sin(2 * np.pi * 28 * T(sec))))   # 그르릉(떨림)
    place(b, voice(f0, [(500, 3, 1), (900, 4, .4)], .6, r, nh=12) * env(m, .5, .1, 2, hold=.3) * .5, 0)
    place(b, _mud(r, .5, 4, (200, 500)) * .5, .2)
    return b


@sfx("sfx.elite.pounce", -8, "전투", "거센 혼 덮침: 큰 몸이 휙 덮쳐 오는 바람 + 붙잡힐 때 팔이 감기는 퍽·사슬 짤랑(0.7초)", bypass_cast=True, use="M10 덮치기 돌진(맞으면 1초 붙잡힘 — 풀릴 때는 sfx.swing 그대로)")
def _(r):
    b = _buf(1.0)
    place(b, _orb_whoosh(r, .35, 300, 1200, 1.0) * .8, 0)
    place(b, _thump(r, .2, 90, 500) * .9, .33)
    place(b, _chain_links(r, .3, 5) * .5, .35)
    return reverb(b, .6, .15)


@sfx("sfx.elite.call", -7, "전투", "거센 혼 부르기: 징을 세게 한 번 치며 길게 울부짖음 '오—'(말뜻 없음, 0.8초) + 징 꼬리가 들판에 퍼짐", bypass_cast=True, use="M10 부르기(맺힘 50%에서 한 번, 0.8초 예고). 잔넋 셋은 이 징에 끌려온다")
def _(r):
    b = _buf(3.6); d = .85; m = int(d * SR)
    f0 = curve(d, [(0, 180), (.15, 230), (.6, 220), (d, 170)]) * (1 + .03 * np.sin(2 * np.pi * 6 * T(d)))
    place(b, voice(f0, [(650, 4, 1), (1100, 5, .5), (2500, 8, .15)], .5, r, nh=25) * env(m, .05, .25, 3, hold=.45) * .7, .05)
    place(b, _jing(r, 150, 3.4, .12) * .9, 0)
    return reverb(b, 2.2, .4)


@sfx("cut.jing", -9, "전투", "들판에 퍼지는 큰 징 한 번: 두레패 징을 힘껏 쳐서 웅— 하고 부풀어 들판 끝까지 퍼지는 긴 맥놀이(5초)", use="EL-001 두레 좌상 오봉: 부르기에 섞는 징(서사 요청) · 천도 뒤 징채 소품 자리")
def _(r):
    return reverb(_jing(r, 140, 5.0, .15), 3.0, .45, tone_hz=3500)


@sfx("cut.jing.crack", -9, "전투", "징이 갈라짐: 징을 치는 순간 쩍! 금이 가며 울림이 찢어진 듯 덜덜 떨다 툭 끊김(1.6초)", use="EL-001 파혼: 징이 갈라지는 소리 한 번(서사 요청)")
def _(r):
    sec = 1.8; n = int(sec * SR); t = T(sec)
    j = _jing(r, 140, sec, .05)
    rattle = 1 + .9 * np.sign(np.sin(2 * np.pi * 37 * t))                 # 금 간 쇠가 덜덜(찢어진 울림)
    j = j * rattle * np.exp(-t / .35)
    crack = filt(noise(n, r), "high", 2500) * env(n, .0005, .02) * 1.2           # 쩍! 금 가는 소리
    b = j * .8 + crack
    place(b, _stone_hit(r, 1.5) * .6, 0)
    return reverb(b, 1.2, .25)


@sfx("sfx.mote.spawn", -16, "전투", "잔넋이 일어남: 들판 흙에서 작은 혼이 퐁 솟으며 짧은 숨 '흐'(0.4초, 셋이 잇달아)", use="M10 부르기 뒤 잔넋 셋이 나타날 때(하나마다 0.15초 간격)")
def _(r):
    b = _buf(.6)
    place(b, _mud(r, .2, 2, (200, 450)) * .5, 0)
    d = .25; m = int(d * SR)
    place(b, voice(curve(d, [(0, 300), (d, 380)]), [(700, 4, 1)], .9, r, nh=8) * env(m, .03, .1, 3) * .25, .06)
    return reverb(b, .7, .2)


# ── M7 싸움 끝 신호 · M8 마지막 혼 처치감 ──
@sfx("sfx.fight.end.jing", -10, "전투", "싸움 끝 징: 무리가 다 처결되면 가까운 징 한 번 — '이제 끝났다'는 둥근 울림, 거센 혼 징보다 맑고 짧게(3초)", use="M7 무리를 다 처결한 순간. 같은 때 전투 BGM 층을 2초에 걸쳐 내림")
def _(r):
    return reverb(_jing(r, 196, 3.0, .08), 1.6, .3)


@sfx("sfx.fight.end.slow", -12, "전투", "마지막 혼 슬로: 시간이 늘어지는 우우웅— 낮게 가라앉는 바람 + 소리가 물속처럼 먹먹해짐(0.9초)", bypass_cast=True, use="M8 무리의 마지막 혼이 무릎 꿇는 순간 짧은 슬로(0.4초 카메라와 함께), 끝나면 sfx.fight.end.jing")
def _(r):
    sec = 1.0; m = int(sec * SR)
    low = sweep_filt(noise(m, r), "low", 1800, 250, .8) * env(m, .02, .5, 3, hold=.3)
    hum = tone(sec, 140, 70) * env(m, .02, .5, 3, hold=.2) * .5
    return reverb(low * .7 + hum, 1.4, .35, tone_hz=1500)


# ── M1 타이틀 화면 ──
@sfx("amb.title.fog", -26, "세계", "타이틀 배경: 밤 서낭당 고개 — 안개 흐르는 낮은 바람, 오색천이 가끔 펄럭, 아주 먼 풀벌레, 사람 소리 없음(반복용 16초)", loop=True, use="M1 타이틀 화면 내내(타이틀 곡 bgm_title 아래 깔기)")
def _(r):
    sec = 16.4; n = int(sec * SR)
    g = _gust_curve(sec, r, 3, .3)
    wind = filt(noise(n, r), "low", 380) * (.5 + .5 * g) * .7
    cloth = _flutter(sec, r, g * .7, rate=(6, 14), bright=2400) * .25
    bug = grains(sec, r, 60, lambda r, k: modal(.06, [(r.uniform(4200, 4600), .01, 1)], r) * r.uniform(.02, .07))
    return loopify(reverb(wind + cloth + filt(bug, "low", 5000), 2.4, .4, tone_hz=2500)[:n], .6)


@sfx("sfx.title.start", -9, "UI", "새로 시작: 깊은 종 한 번 + 바람이 훅 일며 안개가 걷히는 소리(2.6초) — 오프닝 C-01로 넘어감", use="M1 '새로 시작' 누름(이어하기는 sfx.ui.confirm)")
def _(r):
    b = _buf(4.0); m = int(2.4 * SR)
    place(b, modal(4.0, [(98, 2.0, 1), (98.6, 2.0, .7), (236, 1.2, .5), (412, .7, .3), (640, .4, .15)], r) * .9, 0)
    place(b, sweep_filt(noise(m, r), "band", 250, 1400, .8) * env(m, .8, 1.0, 3, hold=.3) * .5, .2)
    return reverb(b, 2.6, .4)


# ===== 천도 시전 중 위험을 귀로 (코디 요청 10-26, 연결법 docs/cast-danger-sound.md) =====
# 천도 중엔 세상이 먹먹해진다(Sfx.cs 저역 통과 1.2kHz). 이 소리들은 모두 bypass_cast — 먹먹함을 뚫고 또렷이 들린다.
# 혼 종류마다 '결'이 다르고, 모두 짧은 소리(0.2~0.4초)라 코드가 거리에 따라 반복 간격·좌우·밝기를 바꿔 방향을 알린다.
# 높이는 일부러 500~3000Hz 쪽 — 사람 귀가 좌우를 가장 잘 가리는 대역.
@sfx("sfx.warn.plain", -14, "전투", "시야 밖 보통 혼이 다가옴: 맨발이 흙을 끄는 '스윽' + 짧게 끊긴 숨 '흐'(0.3초) — 거리마다 반복", bypass_cast=True, use="천도 중 좁아진 시야 밖에서 다가오는 보통 혼(Plain). 반복 간격·좌우는 코드가 정함")
def _(r):
    b = _buf(.4); m = int(.22 * SR)
    place(b, filt(noise(m, r), "band", 1300, 1.5) * env(m, .04, .12, 3) * .7, 0)
    d = .14; k = int(d * SR)
    place(b, voice(curve(d, [(0, 160), (d, 140)]), [(700, 3, 1), (1200, 4, .5)], 1.2, r, nh=10) * env(k, .01, .08, 3) * .5, .12)
    return b


@sfx("sfx.warn.wail", -14, "전투", "시야 밖 넋두리가 노림: 흐느끼는 높은 숨이 '히이—' 짧게 떨림(0.35초) — 멀리서 던지는 혼", bypass_cast=True, use="천도 중 시야 밖 넋두리(Wail). 던지기 예비동작이면 간격을 가장 짧게")
def _(r):
    d = .34; m = int(d * SR)
    f0 = curve(d, [(0, 520), (.1, 640), (d, 560)]) * (1 + .04 * np.sin(2 * np.pi * 9 * T(d)))
    return voice(f0, [(1800, 4, 1), (2600, 6, .5)], .8, r, nh=10) * env(m, .03, .15, 3, hold=.1) * .8


@sfx("sfx.warn.mote", -16, "전투", "시야 밖 잔넋 무리: 작은 혼 여럿이 찍·찍·찍 잘게(0.25초) — 하나가 아니라 떼", bypass_cast=True, use="천도 중 시야 밖 잔넋(Mote). 여럿이어도 이 소리 하나로(무리 중심 방향)")
def _(r):
    one = lambda r, k: tone(.035, r.uniform(2400, 3000), r.uniform(1900, 2300)) * env(int(.035 * SR), .002, .02, 3) * r.uniform(.5, 1)
    return grains(.28, r, 4, one, spread=lambda k, r: k * .06 + r.uniform(0, .015))


@sfx("sfx.warn.buried", -12, "전투", "발밑 가까이 묻힌 혼: 땅속에서 낮게 우르릉 + 흙이 금 가는 짧은 바스락(0.4초) — 보이지 않는 곳 아래", bypass_cast=True, use="천도 중 묻힌 혼(Buried)이 가까이 숨어 있거나 솟기 직전")
def _(r):
    d = .42; m = int(d * SR)
    rum = filt(noise(m, r), "low", 160) * env(m, .08, .2, 3, hold=.1) * 1.6
    crk = grains(d, r, 8, lambda r, k: filt(noise(int(.006 * SR), r), "band", r.uniform(900, 2200), 2) * env(int(.006 * SR), .0005, .003) * r.uniform(.2, .6), t0=.12)
    return rum + crk


@sfx("sfx.warn.fierce", -11, "전투", "시야 밖 거센 혼·덩어리: 무거운 발 '쿵' + 아주 짧은 징 울림(0.4초) — 큰 놈이 온다", bypass_cast=True, use="천도 중 시야 밖 거센 혼(Fierce/엘리트)·덩어리(Lump)·보스의 졸개")
def _(r):
    b = _buf(.6)
    place(b, _drum(r, 60, .12, 1.0), 0)
    j = _jing(r, 196, .5, .02) * env(int(.5 * SR), .005, .15, 3)
    place(b, filt(j, "band", 900, .8) * .5, .01)
    return b


@sfx("sfx.warn.wind", -12, "전투", "시야 밖에서 공격 준비: 바람이 '휙' 빨려 드는 짧은 소리(0.25초) — 종류와 상관없이 '지금 친다'", bypass_cast=True, use="천도 중 시야 밖 적이 예비동작(Winding)에 들어간 그 순간 한 번. 종류별 경고음 위에 얹음")
def _(r):
    m = int(.26 * SR)
    return sweep_filt(noise(m, r), "band", 700, 2600, 3) * env(m, .2, .04, 2)


@sfx("amb.cast.heart", -18, "처결", "천도 중 심장 박동: 쿵·쿵 낮은 두 박이 한 번(반복용 1초 = 1분에 60박). 코드가 위험할수록 빠르게(최대 1.8배)", loop=True, bypass_cast=True, use="천도 시전 중 내내. 위험도(가까운 시야 밖 혼)에 따라 pitch 1.0~1.8, 음량 0.3~1.0. 마지막 30%에 한 단계 더")
def _(r):
    sec = 1.0; b = _buf(sec)
    place(b, _drum(r, 52, .09, 1.0), .02)
    place(b, _drum(r, 48, .08, .65), .27)
    return loopify(filt(b, "low", 400), .02)


@sfx("sfx.cast.peak", -14, "처결", "천도 마무리 직전: 먹먹하던 소리가 숨을 멈춘 듯 '훅' 끊기고 높은 실 같은 음이 가늘게 떨림(0.5초)", bypass_cast=True, use="천도 시전 끝 0.5초 전(마무리 순간이 가장 위험). 이 0.5초 동안 경고음만 남기고 다른 소리는 0.4배")
def _(r):
    d = .55; m = int(d * SR)
    thread = tone(d, 1760, 1800) * (1 + .3 * np.sin(2 * np.pi * 13 * T(d))) * env(m, .15, .1, 2, hold=.25) * .3
    inhale = sweep_filt(noise(m, r), "band", 500, 1600, 2) * env(m, .4, .05, 2) * .5
    return thread + inhale


# ===== 파혼 손맛 · 업 배경층 · 원념 얼룩 (코디 요청 10-26, 연결법 docs/pahon-karma-sound.md) =====
# 파혼은 '시원하지만 찜찜하게'. 손맛(넉백·연쇄)은 아주 시원하게, 대신 그 뒤에 남는 것(업·얼룩)이 조금씩 귀를 탁하게 만든다.
# 겹침 규칙: 첫 폭발(sfx.pahon.burst.*)만 땅을 울리는 저음을 갖는다. 연쇄 소리에는 저음이 없고 한 단씩 높아진다 → 겹쳐도 뭉개지지 않고 '차르르 번지는' 느낌.
@sfx("sfx.pahon.knock", -11, "처결", "파혼 넉백: 폭발에 날린 혼 하나가 몸으로 퍽 맞고 흙바닥을 쓰윽 미끄러짐(0.45초)", use="파혼 폭발에 밀려난 적 하나마다(최대 4, 0.03초 간격, 음높이 +4%씩). 첫 폭발 0.05초 뒤")
def _(r):
    b = _buf(.6)
    place(b, _flesh(r, .2, 700, .9), 0)
    place(b, _thump(r, .12, 120, 600) * .7, 0)
    m = int(.35 * SR)
    place(b, filt(noise(m, r), "band", 900, 1.2) * env(m, .02, .2, 3, hold=.1) * .45, .06)   # 흙바닥을 쓸며 밀려남
    return b


def _chain_burst(r, step):
    """연쇄 파혼 한 칸: 저음 없이 깨지는 유리·쇠 + 짧은 폭풍. step(1·2·3)마다 높아지고 밝아짐"""
    sec = .8; n = int(sec * SR); up = 2 ** (step * 2 / 12)                # 한 칸에 온음(2반음)씩 위로
    blast = sweep_filt(noise(n, r), "band", 2500 * up, 700 * up, 1.0) * env(n, .002, .18, 3)
    crack = modal(sec, [(1661 * up, .18, 1), (1760 * up, .18, .9), (3322 * up, .08, .4)], r) * .3   # 반음 두 음(찜찜함은 그대로)
    shards = grains(sec, r, 10 + step * 4, lambda r, k: filt(noise(int(.012 * SR), r), "band", r.uniform(3000, 7000), 3) * env(int(.012 * SR), .0004, .005) * r.uniform(.2, .6),
                    spread=lambda k, r: r.exponential(.12))
    return reverb(filt(blast + crack + shards * .5, "high", 250), .9, .22)  # 250Hz 아래를 걷어 첫 폭발 저음과 안 부딪힘


@sfx("sfx.pahon.chain.2", -8, "처결", "연쇄 파혼 둘째: 폭발이 옆 혼에 번져 한 번 더 '쨍' — 저음 없이 깨지는 소리만(0.6초)", use="파혼 폭발로 둘째 혼(잔넋 포함)이 함께 깨질 때")
def _(r):
    return _chain_burst(r, 1)


@sfx("sfx.pahon.chain.3", -8, "처결", "연쇄 파혼 셋째: 한 단 더 높게 '쨍'(0.6초)", use="연쇄 셋째")
def _(r):
    return _chain_burst(r, 2)


@sfx("sfx.pahon.chain.4", -8, "처결", "연쇄 파혼 넷째 이상: 가장 높고 밝게 '쨍' — 넷째부터는 이것만 반복(0.6초)", use="연쇄 넷째부터(같은 소리 동시 최대 2개)")
def _(r):
    return _chain_burst(r, 3)


@sfx("sfx.pahon.cascade", -10, "처결", "큰 연쇄 마무리: 셋 이상 함께 깨진 뒤 부서진 조각이 비처럼 차르르 떨어지고 엽전이 짤랑 모임(1.4초) — 시원함의 꼬리", use="한 번의 파혼으로 셋 이상 깨졌을 때, 마지막 연쇄 0.15초 뒤 한 번")
def _(r):
    b = _buf(1.8)
    place(b, grains(1.4, r, 60, lambda r, k: filt(noise(int(.01 * SR), r), "band", r.uniform(2500, 8000), 3) * env(int(.01 * SR), .0004, .004) * r.uniform(.1, .5) * (1 - k / 70),
                    spread=lambda k, r: (k / 60) ** 1.4 * 1.2 + r.uniform(0, .03)), 0)
    coin = lambda r, k: modal(.25, [(r.uniform(3800, 4600), .06, 1), (r.uniform(6400, 7400), .03, .4)], r) * r.uniform(.3, .8)
    place(b, grains(.5, r, 7, coin), .7)
    return reverb(b, 1.0, .2)


# ── 업이 쌓일수록 탁해지는 배경 층(업 10 · 30 · 60) — 구역 환경음 '위에' 겹쳐 까는 아주 작은 반복음 ──
@sfx("amb.karma.1", -36, "세계", "업 10~29: 거의 안 들리는 낮은 웅 — 세상 밑바닥에서 무언가 조금 어긋남(반복용 20초, 귀를 기울여야 들림)", loop=True, use="업 10 이상. 구역 환경음 위에 음량 1.0으로 겹침(파일이 이미 아주 작다)")
def _(r):
    sec = 20.4; n = int(sec * SR); t = T(sec)
    hum = (np.sin(2 * np.pi * 55 * t) + .6 * np.sin(2 * np.pi * 55.7 * t)) * (.6 + .4 * np.sin(2 * np.pi * .05 * t))   # 0.7Hz 맥놀이
    air = filt(noise(n, r), "low", 220) * .6
    return loopify(hum * .5 + air, .8)


@sfx("amb.karma.2", -32, "세계", "업 30~59: 어긋난 두 음이 천천히 비벼지는 드론 + 가끔 먼 데서 들이쉬는 숨(뜻 없음) — 마음이 편치 않음(반복용 24초)", loop=True, use="업 30 이상. amb.karma.1 과 함께 겹침(1 을 끄지 않음)")
def _(r):
    sec = 24.4; n = int(sec * SR); t = T(sec)
    dr = filt(np.sin(2 * np.pi * 146.8 * t) + np.sin(2 * np.pi * 155.6 * t) * .8, "low", 600) * (.5 + .5 * np.sin(2 * np.pi * t / sec * 2) ** 2)   # D와 D#: 반음 비빔
    b = dr * .35
    for at in (5.0, 15.5):
        d = 1.2; m = int(d * SR)
        place(b, filt(noise(m, r), "band", 900, 2) * env(m, .7, .4, 2) * .25, at)     # 먼 숨
    return loopify(reverb(b, 3.0, .5, tone_hz=1500)[:n], 1.0)


@sfx("amb.karma.3", -18, "세계", "업 60 이상: 공기가 탁함 — 바닥에서 지글지글 끓는 잡음 + 느린 맥박 같은 울렁임 + 아주 먼 곳의 깨지는 소리 메아리(반복용 28초)", loop=True, use="업 60 이상. 1·2 위에 겹침. 같이 구역 환경음 전체에 저역 통과 6kHz(맑은 높은 소리가 사라짐)")
def _(r):
    sec = 28.4; n = int(sec * SR); t = T(sec)
    grit = grains(sec, r, 900, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(400, 1500), 2) * env(int(.003 * SR), .0002, .0015) * r.uniform(.05, .3))
    throb = filt(noise(n, r), "low", 120) * (.5 + .5 * np.sin(2 * np.pi * .4 * t)) ** 3 * 1.2   # 2.5초마다 울렁
    b = grit * .6 + throb
    for at in (9.0, 21.0):
        place(b, filt(_chain_burst(r, 0), "low", 1800) * .12, at)              # 아주 먼 파혼의 메아리
    return loopify(reverb(b, 2.5, .4, tone_hz=1800)[:n], 1.0)


# ── 원념 얼룩 ──
@sfx("sfx.stain.form", -15, "처결", "얼룩이 생김: 폭발 자리 땅에 검붉은 것이 '쯔으—' 스며 번지며 낮게 끓음(1초)", use="파혼 직후 얼룩이 바닥에 생길 때(폭발 0.4초 뒤)")
def _(r):
    sec = 1.1; n = int(sec * SR)
    seep = sweep_filt(noise(n, r), "band", 1800, 500, 2) * env(n, .1, .5, 3, hold=.3) * .6
    boil = grains(sec, r, 14, lambda r, k: bubble(.06, r.uniform(180, 380)) * r.uniform(.2, .5), t0=.2)
    return reverb(seep + boil, .8, .2)


@sfx("sfx.stain.step", -17, "처결", "얼룩을 밟음: 끈적하게 '쩍' 들러붙었다 떨어지는 발 + 발밑에서 작게 '흐' 하는 원념(0.35초) — 느려진 걸음마다", use="얼룩 위 발소리마다(재질 발소리 대신). 이동 −20% 동안")
def _(r):
    b = _buf(.45); m = int(.18 * SR)
    place(b, filt(noise(m, r), "band", 600, 2) * env(m, .005, .1, 3) * .7, 0)
    place(b, _mud(r, .25, 3, (200, 420)) * .6, .02)
    k = int(.12 * SR)                                                     # 떨어질 때 '쩍'
    place(b, filt(noise(k, r), "band", 2200, 4) * env(k, .002, .04, 3) * .4, .16)
    d = .2; q = int(d * SR)
    place(b, voice(curve(d, [(0, 120), (d, 100)]), [(500, 3, 1)], 1.2, r, nh=8) * env(q, .02, .1, 3) * .25, .1)
    return b


@sfx("amb.stain.near", -26, "처결", "얼룩 곁: 낮게 끓는 거품 + 웅웅 떨리는 원념(반복용 6초) — 얼룩 자리에서 3D로", loop=True, use="얼룩마다 하나(3D, 최소 1m · 최대 8m), 사라질 때 1초 페이드. 최대 4개")
def _(r):
    sec = 6.2; n = int(sec * SR); t = T(sec)
    boil = grains(sec, r, 40, lambda r, k: bubble(r.uniform(.04, .08), r.uniform(150, 350)) * r.uniform(.1, .4))
    hum = filt(noise(n, r), "band", 230, 4) * (.6 + .4 * np.sin(2 * np.pi * 3.3 * t)) * .5
    return loopify(boil + hum, .4)


@sfx("sfx.stain.overlap", -10, "처결", "얼룩 셋이 겹침(사나운 적이 온다): 세 끓는 소리가 한데 모여 꿀렁 꿀렁 꿀렁 + 땅속에서 낮게 부풀어 오름(1.6초)", bypass_cast=True, use="얼룩 3개가 겹쳐 사나운 적이 소환되기 직전")
def _(r):
    b = _buf(2.0)
    for k in range(3):
        place(b, _mud(r, .3, 3, (140, 300)) * (.6 + .15 * k), .1 + k * .32)
    m = int(1.3 * SR)
    place(b, sweep_filt(noise(m, r), "low", 80, 400) * env(m, 1.0, .2, 2) * 1.2, .4)
    return reverb(b, 1.2, .25)


@sfx("sfx.stain.fade", -22, "처결", "얼룩이 마름: 끓던 것이 '스으' 잦아들며 땅에 말라붙음(0.8초)", use="얼룩 지속 15초가 끝날 때")
def _(r):
    m = int(.8 * SR)
    return sweep_filt(noise(m, r), "band", 900, 300, 1.5) * env(m, .05, .5, 3) * .6


# ===== 1막 솔고개 주변 소리: 서낭당 5곳 · 외톨이 야영지 · 처음 10분 길 (코디 요청 10-26, 배치표 data/act1_soundscape.json) =====
# 서낭당은 구역마다 다른 모델(아트 PR #37 seonang_set)이라 소리도 '무엇이 매달려 있나'로 나눴다:
#   ① 솔고개 마을=가꿔진 곳(오방색 천·금줄 종이·촛불)  ② 보릿들=농사(짚·보리 이삭·솟대)  ③ 물막이 골=물(이끼 돌탑 물방울·물동이)
#   ④ 검은여울=역병(끊어진 금줄·재·고요)  ⑤ 폐당집=폐허(고사목·기와·혼불 하나)
def _owl(r, f=420):
    """부엉이 '부엉—부엉': 낮고 둥근 두 음(목소리 합성, 멀리)"""
    b = _buf(1.4)
    for k, at in enumerate((0, .55)):
        d = .32; f0 = curve(d, [(0, f * (1 - .04 * k)), (.08, f * 1.05), (d, f * .9)])
        place(b, voice(f0, [(f * 1.0, 3, 1), (f * 2.1, 4, .2)], .3, r, nh=6) * env(int(d * SR), .04, .14, 3, hold=.08), at)
    return filt(b, "low", 1500)


def _crickets(sec, r, rate=(18, 26), f=(3800, 4600), count=6, amp=.06):
    """풀벌레: 몇 마리가 각자 빠르기로 찌르르 — 낮게 깔기"""
    n = int(sec * SR); t = T(sec); y = np.zeros(n)
    for k in range(count):
        fr = r.uniform(*f); rt = r.uniform(*rate); ph = r.uniform(0, 6)
        gate = (np.sin(2 * np.pi * rt * t + ph) > .3) * (np.sin(2 * np.pi * r.uniform(.15, .4) * t + ph) > -.2)
        y += np.sin(2 * np.pi * fr * t) * filt(gate.astype(float), "low", 300) * r.uniform(.4, 1)
    return y * amp


def _paper_strips(sec, r, gust, count=60):
    """금줄에 끼운 한지 조각이 바람에 사락사락"""
    return grains(sec, r, count, lambda r, k: _paper(r, r.uniform(.04, .1), 2500, 7000) * r.uniform(.1, .4)) * (.4 + .6 * np.interp(np.arange(int(sec * SR)), np.arange(len(gust)), gust))[:int(sec * SR)]


@sfx("amb.seonang.solgogae", -24, "세계", "서낭당 ① 솔고개 마을: 오방색 천 다섯이 펄럭이고 금줄 한지가 사락사락, 제물상 촛불이 아주 작게 타닥, 나무 위로 지나는 바람(반복용 16초)", loop=True, use="서낭당 ①(188,36) 3D 반복. 최소 2m·최대 14m. 첫 깨어남(0:20)의 첫 소리")
def _(r):
    sec = 16.4; n = int(sec * SR); g = _gust_curve(sec, r, 3, .3)
    wind = filt(noise(n, r), "band", 420, .6) * (.4 + .6 * g) * .6
    cloth = _flutter(sec, r, g * .8, rate=(6, 13), bright=2400) * .35
    paper = _paper_strips(sec, r, g, 70) * .5
    candle = grains(sec, r, 18, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(2000, 4000), 2) * env(int(.003 * SR), .0002, .001) * r.uniform(.05, .2))
    return loopify(reverb(wind + cloth + paper + candle + _crickets(sec, r, count=3, amp=.03), 1.2, .25)[:n], .6)


@sfx("amb.seonang.boritdeul", -24, "세계", "서낭당 ② 보릿들: 짚단과 보리 이삭이 바람에 서걱, 솟대 나무가 아주 낮게 삐걱, 노랑 헝겊 펄럭, 둘레 풀벌레(반복용 16초)", loop=True, use="서낭당 ②(160,180) 3D 반복. 최소 2m·최대 14m")
def _(r):
    sec = 16.4; n = int(sec * SR); g = _gust_curve(sec, r, 3, .35)
    straw = filt(filt(noise(n, r), "high", 1800), "low", 7000) * (.3 + .7 * g) * .3        # 마른 짚·이삭 서걱
    cloth = _flutter(sec, r, g * .6, rate=(6, 12), bright=2200) * .25
    b = straw + cloth + filt(noise(n, r), "low", 300) * (.4 + .6 * g) * .4
    for at in (4.0, 11.5): place(b, _creak(r, .9, 150, 18, 600) * .25, at)   # 솟대
    return loopify(reverb(b + _crickets(sec, r, count=7, amp=.05), 1.0, .2)[:n], .6)


@sfx("amb.seonang.mulmagi", -24, "세계", "서낭당 ③ 물막이 골 어귀: 이끼 돌탑에서 물방울이 똑… 똑… 물동이에 떨어지고, 젖은 마당, 가까운 개울 졸졸, 푸른 헝겊 느리게(반복용 16초)", loop=True, use="서낭당 ③(356,324) 3D 반복. 최소 2m·최대 14m")
def _(r):
    sec = 16.4; n = int(sec * SR); g = _gust_curve(sec, r, 2, .25)
    brook = filt(noise(n, r), "band", 900, 1.0) * (.7 + .3 * np.sin(2 * np.pi * .21 * T(sec))) * .25
    drips = _drips(r, sec, 26, 700, 1500, .05, (.2, .6))
    pot = grains(sec, r, 8, lambda r, k: bubble(.05, r.uniform(380, 520)) * .4)              # 물동이 속으로 떨어지는 낮은 퐁
    cloth = _flutter(sec, r, g * .5, rate=(5, 10), bright=1800) * .2
    return loopify(reverb(brook + drips + pot + cloth + filt(noise(n, r), "low", 250) * .3, 1.6, .3)[:n], .6)


@sfx("amb.seonang.geomeun", -26, "세계", "서낭당 ④ 검은여울 어귀(역병): 거의 고요 — 끊어진 금줄 끝이 가끔 장승에 톡, 재가 바람에 스스스, 성긴 잎 마른 바스락, 벌레 소리 없음(반복용 18초)", loop=True, use="서낭당 ④(108,452) 3D 반복. 최소 2m·최대 12m. 다른 서낭당보다 일부러 비어 있게")
def _(r):
    sec = 18.4; n = int(sec * SR); g = _gust_curve(sec, r, 2, .15)
    air = filt(noise(n, r), "low", 260) * (.3 + .7 * g) * .5
    ash = filt(noise(n, r), "band", 3000, 1.0) * g ** 2 * .08
    b = air + ash
    for at in (3.2, 9.8, 15.1): place(b, _wood_tap(r, 700, .02, .3), at)   # 끊긴 줄 끝이 톡
    b += grains(sec, r, 10, lambda r, k: _crinkle(r, .2, 6, (1800, 5000), (.05, .2)))
    return loopify(reverb(b, 2.2, .35, tone_hz=2500)[:n], .6)


@sfx("amb.seonang.pyedang", -25, "세계", "서낭당 ⑤ 폐당집 어귀(폐허): 잎 없는 고사목 가지가 삐걱, 내려앉은 기와가 가끔 달각, 혼불 하나가 낮게 웅— 떨림(반복용 18초)", loop=True, use="서낭당 ⑤(574,552) 3D 반복. 최소 2m·최대 14m. 혼불 웅은 밤에만 크게(낮엔 0.4배)")
def _(r):
    sec = 18.4; n = int(sec * SR); t = T(sec); g = _gust_curve(sec, r, 3, .2)
    wind = filt(noise(n, r), "band", 300, .7) * (.3 + .7 * g) * .5
    hum = (np.sin(2 * np.pi * 196 * t) + .4 * np.sin(2 * np.pi * 197.3 * t)) * (.6 + .4 * np.sin(2 * np.pi * .7 * t)) * .08   # 혼불 떨림
    b = wind + filt(hum, "low", 900)
    for at in (2.5, 8.0, 14.2): place(b, _creak(r, 1.1, 120, 14, 500) * .3, at)          # 고사목
    for at in (5.6, 12.9): place(b, modal(.3, [(r.uniform(900, 1300), .04, 1), (r.uniform(2200, 2800), .02, .4)], r) * .25, at)   # 기와 달각
    return loopify(reverb(b, 2.0, .35, tone_hz=2600)[:n], .6)


@sfx("amb.soulpath.gate", -25, "세계", "넋길 입구(밤): 새끼줄에 매단 혼불 다섯이 각자 낮게 웅웅 — 서로 조금씩 다른 높이로 떨고, 줄이 가끔 삐걱(반복용 12초)", loop=True, use="넋길 정류장 3곳(292,144 · 368,352 · 576,496) 3D 반복, 밤에만(낮 _off 모델일 땐 끔). 최소 1.5m·최대 10m")
def _(r):
    sec = 12.3; n = int(sec * SR); t = T(sec); y = np.zeros(n)
    for k, f in enumerate((174.6, 196.0, 220.0, 233.1, 261.6)):
        y += np.sin(2 * np.pi * f * t + r.uniform(0, 6)) * (.5 + .5 * np.sin(2 * np.pi * r.uniform(.2, .6) * t + k)) * .06
    b = filt(y, "low", 1200)
    for at in (3.0, 9.0): place(b, _creak(r, .7, 200, 22, 700) * .2, at)
    return loopify(reverb(b, 1.6, .3)[:n], .5)


# ── 외톨이 야영지: 무리에서 12~16m 떨어져 혼자 무릎 꿇고 기다리는 혼 ──
@sfx("amb.loner", -27, "처결", "외톨이 혼: 홀로 무릎 꿇은 혼이 아주 작게 흐느끼듯 숨을 쉼 — 들이쉼이 떨리고, 가끔 코를 훌쩍, 말은 없음(반복용 10초)", loop=True, use="외톨이 혼 자리에 3D 반복. 최소 1m·최대 9m. 처결하면 0.5초에 끔. 싸움 중엔 0.5배(무리 소리에 묻혀도 됨)")
def _(r):
    sec = 10.2; b = _buf(sec)
    for k, at in enumerate((.4, 3.1, 5.9, 8.4)):
        d = r.uniform(1.0, 1.4); m = int(d * SR)
        trem = 1 + .25 * np.sign(np.sin(2 * np.pi * 7 * T(d)))                # 떨리는 들숨
        place(b, filt(noise(m, r), "band", 800, 2) * env(m, d * .6, d * .3, 2) * trem * .4, at)
        place(b, filt(noise(int(.9 * SR), r), "band", 600, 1.5) * env(int(.9 * SR), .05, .6, 3) * .25, at + d)   # 날숨
    place(b, filt(noise(int(.12 * SR), r), "band", 2500, 3) * env(int(.12 * SR), .005, .05, 3) * .3, 7.3)       # 훌쩍
    return loopify(reverb(b, 1.0, .2), .3)


@sfx("sfx.loner.notice", -18, "처결", "외톨이 혼이 이쪽을 알아챔: 고개를 드는 옷자락 스륵 + 숨을 멈췄다가 길게 내쉬는 '하아—'(1.4초) — 놀람이 아니라 기다림이 끝나는 쪽", use="차사가 외톨이 혼 8m 안에 처음 들어올 때 한 번")
def _(r):
    b = _buf(1.8)
    place(b, _paper(r, .3, 600, 3000) * .4, 0)
    d = 1.0; m = int(d * SR)
    place(b, voice(curve(d, [(0, 150), (d, 120)]), [(600, 3, 1), (1100, 4, .4)], 1.4, r, nh=8) * env(m, .1, .6, 3) * .4, .45)
    return reverb(b, 1.0, .2)


# ── 처음 10분 길(솔고개 마을 → 보릿들 둑길): 구역 바탕 소리 ──
@sfx("amb.village.night", -26, "세계", "솔고개 마을 밤: 사람들은 잠듦 — 문풍지가 바람에 떨고, 아궁이 불씨 타닥, 어느 집 소가 한 번 콧김, 장독 사이 풀벌레(반복용 18초)", loop=True, use="구역 '솔고개 마을'(160~232, 24~100) 바탕. 밤. 낮은 기존 amb.field")
def _(r):
    sec = 18.4; n = int(sec * SR); g = _gust_curve(sec, r, 3, .25)
    air = filt(noise(n, r), "low", 350) * (.4 + .6 * g) * .45
    paper = _flutter(sec, r, g * .5, rate=(14, 26), bright=1600) * .12        # 문풍지
    ember = grains(sec, r, 25, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(1500, 3500), 2) * env(int(.003 * SR), .0002, .001) * r.uniform(.03, .12))
    b = air + paper + ember + _crickets(sec, r, count=5, amp=.04)
    m = int(.7 * SR); place(b, filt(noise(m, r), "band", 300, 1.2) * env(m, .05, .4, 3) * .25, 11.0)   # 소 콧김
    return loopify(reverb(b, 1.2, .25)[:n], .6)


@sfx("amb.boritdeul.night", -25, "세계", "보릿들 밤: 넓은 보리밭이 바람에 물결치며 쏴— 서걱, 밭고랑 풀벌레가 촘촘, 먼 논 개구리 몇, 허수아비 천 가끔(반복용 20초)", loop=True, use="구역 '보릿들'(208~448, 40~240) 바탕. 밤. 거센 혼(7~9분) 들머리도 여기")
def _(r):
    sec = 20.4; n = int(sec * SR); g = _gust_curve(sec, r, 4, .3)
    field = filt(filt(noise(n, r), "high", 1200), "low", 6000) * g ** 1.5 * .35   # 보리 물결
    low = filt(noise(n, r), "low", 280) * (.4 + .6 * g) * .4
    frogs = grains(sec, r, 30, lambda r, k: voice(np.full(int(.09 * SR), r.uniform(260, 340)), [(700, 3, 1)], .1, r, nh=10) * env(int(.09 * SR), .005, .04, 3) * r.uniform(.02, .06))
    b = field + low + filt(frogs, "low", 1500) + _crickets(sec, r, count=10, amp=.05)
    return loopify(reverb(b, 1.4, .25)[:n], .8)


@sfx("amb.mulmagi.night", -25, "세계", "물막이 골 밤: 벼랑 사이로 개울이 흐르는 소리가 바탕, 물막이 둑 너머 물이 낮게 넘침, 벼랑에 부딪는 바람, 풀벌레 드묾(반복용 18초)", loop=True, use="구역 '물막이 골'(264~504, 240~500) 바탕. 밤")
def _(r):
    sec = 18.4; n = int(sec * SR); g = _gust_curve(sec, r, 2, .3)
    brook = filt(noise(n, r), "band", 700, .8) * .35 + filt(noise(n, r), "band", 1800, 1.5) * .08
    weir = filt(noise(n, r), "low", 180) * .4
    cliff = filt(noise(n, r), "band", 500, 2) * g ** 2 * .3
    return loopify(reverb(brook + weir + cliff + _crickets(sec, r, count=2, amp=.03), 1.8, .3)[:n], .6)


# ── 처음 10분 길: 자리 소리(3D, data/act1_soundscape.json 좌표) ──
@sfx("amb.campfire.small", -24, "세계", "작은 모닥불: 장작이 타닥 타닥 + 불이 낮게 훅훅 숨 쉼 + 가끔 불티 탁(반복용 8초)", loop=True, use="1막 모닥불 7곳(prop_campfire) 3D. 최소 1m·최대 8m")
def _(r):
    sec = 8.2; n = int(sec * SR)
    x = filt(noise(n, r), "band", 300, .8) * (.6 + .4 * np.abs(np.sin(2 * np.pi * .6 * T(sec)))) * .35
    x += grains(sec, r, 60, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(1500, 5000), 3) * env(int(.004 * SR), .0002, .0012) * r.uniform(.1, .6))
    x += grains(sec, r, 5, lambda r, k: _thump(r, .06, 220, 1200) * .25)
    return loopify(reverb(x, .6, .15)[:n], .4)


@sfx("amb.forge.idle", -24, "세계", "밤의 대장간(박돌쇠): 식어 가는 화덕 숯이 쉬익 낮게, 걸어 둔 쇠가 식으며 틱… 틱, 풀무가 아주 느리게 한 번 숨(반복용 12초)", loop=True, use="대장간 화덕(222.9, 62.2) 3D. 최소 1.5m·최대 10m. 박돌쇠(4:40~5:00) 앞")
def _(r):
    sec = 12.3; n = int(sec * SR)
    coal = filt(noise(n, r), "band", 500, .7) * .25 + grains(sec, r, 30, lambda r, k: filt(noise(int(.003 * SR), r), "band", r.uniform(1800, 4200), 3) * env(int(.003 * SR), .0002, .001) * r.uniform(.05, .2))
    b = coal
    for at in (1.5, 4.2, 6.0, 9.7): place(b, modal(.4, [(r.uniform(3200, 4200), .05, 1), (r.uniform(6500, 7500), .02, .3)], r) * .18, at)   # 식는 쇠 틱
    m = int(1.8 * SR); place(b, filt(noise(m, r), "low", 400) * env(m, .8, .8, 3) * .4, 7.5)   # 풀무 한 숨
    return loopify(reverb(b, .9, .2)[:n], .5)


@sfx("amb.stream.small", -25, "세계", "작은 개울: 돌 사이를 졸졸 흐르는 맑은 물 + 작은 퐁(반복용 10초)", loop=True, use="개울 칸(terrain_tile_stream)을 따라 12m 간격 3D 점(최대 6개, 가까운 순). 최소 1m·최대 9m")
def _(r):
    sec = 10.3; n = int(sec * SR)
    x = filt(noise(n, r), "band", 1100, 1.2) * (.7 + .3 * np.sin(2 * np.pi * .43 * T(sec))) * .3
    x += grains(sec, r, 50, lambda r, k: bubble(r.uniform(.02, .05), r.uniform(700, 1800)) * r.uniform(.05, .25))
    return loopify(reverb(x, .7, .15)[:n], .4)


@sfx("amb.tree.old", -25, "세계", "큰 고목: 높은 가지 사이로 바람이 쏴— 지나가고 굵은 가지가 낮게 삐걱, 잎이 한꺼번에 쓸림(반복용 14초)", loop=True, use="고목 5곳(prop_old_tree) 3D. 최소 2m·최대 12m")
def _(r):
    sec = 14.3; n = int(sec * SR); g = _gust_curve(sec, r, 3, .2)
    leaves = filt(filt(noise(n, r), "high", 1500), "low", 6500) * g ** 1.3 * .3
    b = leaves + filt(noise(n, r), "band", 350, .7) * (.3 + .7 * g) * .35
    for at in (2.2, 7.8, 11.6): place(b, _creak(r, 1.3, 95, 11, 420) * .35, at)
    return loopify(reverb(b, 1.4, .25)[:n], .6)


@sfx("amb.scarecrow", -27, "세계", "허수아비: 낡은 저고리 천이 바람에 툭툭 펄럭이고 짚 몸통이 서걱, 매단 깡통 대신 마른 박 두 개가 서로 똑(반복용 12초)", loop=True, use="허수아비 19곳(prop_scarecrow) 3D, 가까운 2개만. 최소 1m·최대 7m")
def _(r):
    sec = 12.3; n = int(sec * SR); g = _gust_curve(sec, r, 3, .25)
    b = _flutter(sec, r, g * .7, rate=(5, 11), bright=1500) * .35 + filt(filt(noise(n, r), "high", 2000), "low", 6000) * g * .12
    for at in (3.4, 8.9): place(b, _wood_tap(r, 520, .03, .35) , at); place(b, _wood_tap(r, 610, .03, .25), at + .12)
    return loopify(reverb(b, .8, .2)[:n], .5)


# ── 처음 10분 길: 흩뿌리는 한 번짜리(구역마다 무작위 간격 · 무작위 방향 · 거리 15~40m) — '촘촘함'은 여기서 나온다 ──
@sfx("sfx.night.owl", -22, "세계", "먼 부엉이: 부엉— 부엉(1.4초)", use="밤 · 보릿들·물막이 골·고목 근처. 25~60초마다 한 번, 먼 쪽에서")
def _(r):
    return reverb(_owl(r, 400), 2.2, .5, tone_hz=1600)


@sfx("sfx.night.dog.far", -22, "세계", "먼 개 짖음: 마을 너머 개가 컹 컹 두 번(1.6초) — 업 10 이상이면 따로 있는 '차사 쪽 짖음'과 다름(멀고 무심)", use="밤 · 솔고개 마을·보릿들 가장자리. 40~90초마다 한 번")
def _(r):
    b = _buf(1.4)
    for k, at in enumerate((.05, .42)):
        d = .2; f0 = curve(d, [(0, 520), (.05, 640), (d, 430)])
        place(b, voice(f0, [(900, 3, 1), (1800, 4, .5)], .6, r, nh=14) * env(int(d * SR), .005, .08, 3, hold=.04) * (1 - .2 * k), at)
    return reverb(filt(b, "low", 1800), 2.0, .55, tone_hz=1500)


@sfx("sfx.night.frog", -24, "세계", "개구리 몇 마리 한꺼번에: 개굴개굴 짧게 한 마디(1초)", use="밤 · 보릿들 논두렁·개울가. 15~35초마다")
def _(r):
    one = lambda r, k: voice(np.full(int(.08 * SR), r.uniform(240, 360)) * (1 + .08 * np.sign(np.sin(2 * np.pi * 40 * T(.08)))), [(650, 3, 1), (1300, 4, .3)], .15, r, nh=12) * env(int(.08 * SR), .004, .03, 3) * r.uniform(.4, 1)
    return reverb(filt(grains(1.0, r, 9, one, spread=lambda k, r: k * .1 + r.uniform(0, .04)), "low", 2200), 1.0, .3)


@sfx("sfx.night.gust", -20, "세계", "지나가는 돌풍: 멀리서 바람이 쏴아— 다가와 지나감(3초)", use="밤 · 모든 구역. 30~70초마다(바탕 소리의 돌풍과 따로 놀아 반복이 덜 들림)")
def _(r):
    sec = 3.0; n = int(sec * SR)
    return sweep_filt(noise(n, r), "band", 300, 1200, .8) * env(n, 1.2, 1.4, 3, hold=.2) * .7


@sfx("sfx.village.shutter", -21, "세계", "어느 집 덧문이 바람에 덜컹 — 한 번 부딪고 삐걱 멈춤(0.9초)", use="밤 · 솔고개 마을 안. 30~80초마다, 가까운 집 쪽")
def _(r):
    b = _buf(1.1)
    place(b, _wood_tap(r, 300, .06, 1.0), 0); place(b, _thump(r, .1, 140, 700) * .5, 0)
    place(b, _creak(r, .5, 260, 30, 900) * .3, .18)
    return reverb(b, .8, .2)


@sfx("sfx.barley.wave", -20, "세계", "보리 물결: 바람이 보리밭을 한쪽에서 다른 쪽으로 쓸고 지나가는 쏴르르(2.6초) — 좌우로 움직이게", use="밤·낮 · 보릿들. 20~45초마다. 왼→오른(또는 반대)으로 panStereo를 2.6초 동안 옮기면 바람이 '지나간다'")
def _(r):
    sec = 2.6; n = int(sec * SR)
    return sweep_filt(filt(noise(n, r), "high", 900), "low", 2500, 7000, .7) * env(n, .9, 1.2, 3, hold=.3) * .6


# ═══════════════════════════════════════════════════════════════════════════
# 장비 장착 · 손보기(강화) — 등급마다 다르게 (10-26)
# 등급: 흔한(미색) < 손본(청록) < 귀한(금빛) < 이름 있는(주홍) / 한 벌(옥빛)
# 장착 = '몸' 소리(무엇을 걸쳤나: 쇠·천·노리개) + '등급 머리' 소리(얼마나 귀한가)를 같이 튼다.
#   → 몸 3 × 등급 5 = 15가지 조합을 파일 8개로 만든다(같은 등급이면 무기든 갓이든 같은 '머리')
# 손보기 = 등급마다 망치 횟수·쇠 무게·마무리 소리가 다르다. +1→+5 로 갈수록 코드가 높이를 조금씩 올린다
# 흔한 것은 일부러 수수하게: 모든 것이 반짝이면 귀한 것이 안 귀하다
# ═══════════════════════════════════════════════════════════════════════════
@sfx("sfx.equip.body.metal", -15, "UI", "장착(무기·쇠붙이): 쇠고리가 철컥 맞물리고 손에 쥐는 가죽 끼익 + 짧은 쇠 울림(0.5초)", use="무기 칸(철삭·육모방망이·요령방울·삼지창·명부 붓)에 낄 때. sfx.equip.tier.* 와 같은 순간에 함께")
def _(r):
    b = _buf(.8)
    place(b, _chain_links(r, .12, 3) * .6, 0)                                            # 쇠고리 철컥
    place(b, modal(.5, [(r.uniform(1150, 1250), .12, 1), (r.uniform(2900, 3100), .06, .4), (r.uniform(520, 560), .18, .5)], r) * .6, .07)
    m = int(.18 * SR); place(b, filt(noise(m, r), "band", 1300, 3) * env(m, .03, .08, 3) * .3, .1)   # 손잡이 가죽 끼익
    return reverb(b, .5, .12)


@sfx("sfx.equip.body.cloth", -17, "UI", "장착(갓·도포·띠·신): 무명 천이 훅 펼쳐져 어깨에 내려앉고 끈을 매는 사락 + 매듭 톡(0.6초)", use="갓·도포·띠·신 칸에 낄 때. sfx.equip.tier.* 와 함께")
def _(r):
    b = _buf(.8)
    m = int(.25 * SR); place(b, filt(noise(m, r), "band", 700, .8) * env(m, .06, .1, 3) * .7, 0)   # 천이 훅
    place(b, _paper(r, .16, 900, 3500) * .45, .2)                                        # 끈 사락
    place(b, _wood_tap(r, 1400, .015, .25), .42)                                         # 매듭 톡
    return reverb(b, .4, .1)


@sfx("sfx.equip.body.trinket", -17, "UI", "장착(노리개): 술이 사르르 흔들리고 옥 두 알이 딸깍 부딪혀 작게 맑게 운다(0.6초)", use="노리개 칸에 낄 때. sfx.equip.tier.* 와 함께")
def _(r):
    b = _buf(.9)
    place(b, _paper(r, .2, 2500, 7000) * .3, 0)                                          # 술 사르르
    for at in (.12, .2):
        place(b, modal(.5, [(r.uniform(2400, 2700), .09, 1), (r.uniform(5600, 6200), .04, .4)], r) * .45, at)   # 옥 딸깍
    return reverb(b, .6, .15)


@sfx("sfx.equip.tier.common", -26, "UI", "흔한 장비 장착 머리: 소리 거의 없음 — 몸에 맞는 낮은 '툭' 하나(0.2초)", use="흔한 등급 장착. 몸 소리를 거의 그대로 들리게 하려고 일부러 작다")
def _(r):
    return _thump(r, .12, 170, 500) * .6


@sfx("sfx.equip.tier.crafted", -19, "UI", "손본 장비 장착 머리(청록): 맑은 한 음 '팅'이 몸에 스며듦(0.8초)", use="손본 등급 장착")
def _(r):
    b = _buf(1.2)
    place(b, _chime(r, 1318, .35, .8), .02)
    return reverb(b, .9, .25)


@sfx("sfx.equip.tier.rare", -15, "UI", "귀한 장비 장착 머리(금빛): 두 음 '팅·딩'이 화음으로 + 몸을 감싸는 짧은 쉬이—(1.2초)", use="귀한 등급 장착")
def _(r):
    b = _buf(1.8)
    m = int(.5 * SR); place(b, sweep_filt(noise(m, r), "band", 1500, 4500, 3) * env(m, .15, .2, 3) * .25, 0)
    place(b, _chime(r, 1108, .5, .7), .04); place(b, _chime(r, 1661, .5, .6), .1)
    return reverb(b, 1.2, .3)


@sfx("sfx.equip.tier.named", -11, "UI", "이름 있는 물건 장착 머리(주홍): 낮은 징 웅— 이 몸 안에서 울리고, 물건이 깨어나듯 낮은 숨 + 세 음이 천천히 내려앉음(2.2초)", use="이름 있는 물건(월화 방울 등) 장착. 몸 소리 다음 0.1초에")
def _(r):
    b = _buf(3.0)
    place(b, _jing(r, 98, 2.6, .2) * .5, 0)
    m = int(1.2 * SR); place(b, filt(noise(m, r), "low", 600) * env(m, .5, .4, 3) * .3, .1)   # 물건이 숨 쉼
    for k, f in enumerate((1760, 1318, 1108)):
        place(b, _chime(r, f, .7, .55), .35 + k * .22)
    return reverb(b, 1.8, .35)


@sfx("sfx.equip.tier.set", -15, "UI", "한 벌 장비 장착 머리(옥빛): 옥 편경 두 음이 '함께' 울림 — 짝을 찾는 맑은 맥놀이(1.2초)", use="한 벌 등급 하나를 낄 때(몇 벌째인지는 sfx.equip.set.complete 가 따로)")
def _(r):
    b = _buf(1.8)
    place(b, modal(1.5, [(880, .6, 1), (884, .6, .8), (2430, .2, .3)], r) * .5, 0)          # 맥놀이 = 둘이 짝
    place(b, modal(1.5, [(1320, .5, 1), (1326, .5, .7)], r) * .35, .12)
    return reverb(b, 1.3, .3)


@sfx("sfx.equip.set.complete", -10, "UI", "한 벌이 다 갖춰짐: 옥 편경 다섯 음이 차례로 쌓여 한 화음으로 + 은은한 바람이 몸을 한 바퀴(2.5초)", use="한 벌 장비의 마지막 조각을 낄 때(한 벌 효과가 켜지는 순간). 장착 소리 0.25초 뒤")
def _(r):
    b = _buf(3.4)
    m = int(1.6 * SR); place(b, sweep_filt(noise(m, r), "band", 600, 2400, 2) * env(m, .6, .5, 3) * .2, 0)
    for k, f in enumerate((660, 880, 990, 1320, 1760)):
        place(b, modal(2.0, [(f, .9, 1), (f * 1.004, .9, .7), (f * 2.76, .25, .2)], r) * (.5 - k * .04), k * .14)
    return reverb(b, 2.0, .35)


@sfx("sfx.equip.remove", -18, "UI", "장비 풀기: 매듭을 푸는 사락 + 내려놓는 낮은 툭(0.4초). 등급 무관", use="장비 풀기 버튼·자리 비우기")
def _(r):
    b = _buf(.6)
    place(b, _paper(r, .14, 800, 3000) * .45, 0)
    place(b, _thump(r, .1, 150, 450) * .5, .16)
    return reverb(b, .35, .08)


# ── 손보기(강화) ──
def _anvil(r, heavy=1.0):
    """쇠망치가 모루를 '탕': heavy가 클수록 낮고 두꺼운 쇠(귀한·이름 있는 물건일수록 무겁게)"""
    f = 1900 / heavy
    return modal(.9, [(f * r.uniform(.97, 1.03), .22 * heavy, 1), (f * 2.1 * r.uniform(.98, 1.02), .1, .5), (f * .36, .3 * heavy, .55 * heavy)], r)


def _quench(r, sec=.9):
    """달군 쇠를 물에 담금: 치이익— (높은 쉬 소리가 줄어듦 + 작은 방울)"""
    m = int(sec * SR)
    return sweep_filt(noise(m, r), "band", 5200, 2200, 2) * env(m, .01, sec * .45, 3) * .5 + grains(sec, r, 14, lambda r, k: bubble(.04, r.uniform(1500, 3000)) * .1)


@sfx("sfx.enhance.common", -12, "UI", "흔한 장비 손보기: 망치 탕! 한 번 + 짧은 쇠 울림(0.7초). 수수하게", use="흔한 등급 손보기 성공. +N 단계마다 높이 ×(1 + 0.03×(N−1))")
def _(r):
    b = _buf(1.2)
    place(b, _anvil(r, 1.0), .03)
    return reverb(b, .9, .2)


@sfx("sfx.enhance.crafted", -10, "UI", "손본 장비 손보기: 탕! 탕! 두 번 + 청록빛 한 음 '팅'(1.1초)", use="손본 등급 손보기 성공. +N 높이 규칙 같음")
def _(r):
    b = _buf(1.8)
    for k, at in enumerate((.03, .34)): place(b, _anvil(r, 1.0) * (.85 + .15 * k), at)
    place(b, _chime(r, 1318, .45, .5), .62)
    return reverb(b, 1.1, .22)


@sfx("sfx.enhance.rare", -9, "UI", "귀한 장비 손보기: 무거운 탕! 탕! 탕! 세 번 + 금빛 세 음이 차르르(1.6초)", use="귀한 등급 손보기 성공. +N 높이 규칙 같음")
def _(r):
    b = _buf(2.6)
    for k, at in enumerate((.03, .3, .57)): place(b, _anvil(r, 1.2) * (.8 + .1 * k), at)
    for k, f in enumerate((1568, 2093, 2637)): place(b, _chime(r, f, .5, .4), .86 + k * .05)
    return reverb(b, 1.4, .25)


@sfx("sfx.enhance.named", -8, "UI", "이름 있는 물건 손보기: 아주 무거운 탕—탕—탕 + 달군 쇠를 물에 담그는 치이익 + 낮은 징이 웅(2.6초)", use="이름 있는 물건 손보기 성공. +N 높이 규칙 같음")
def _(r):
    b = _buf(3.8)
    for k, at in enumerate((.03, .38, .73)): place(b, _anvil(r, 1.5) * (.8 + .1 * k), at)
    place(b, _quench(r, 1.0), 1.05)
    place(b, _jing(r, 110, 2.4, .2) * .35, 1.15)
    return reverb(b, 1.8, .3)


@sfx("sfx.enhance.set", -9, "UI", "한 벌 장비 손보기: 탕! 탕! 두 번 + 옥 편경 두 음이 함께 맥놀이(1.5초)", use="한 벌 등급 손보기 성공. +N 높이 규칙 같음")
def _(r):
    b = _buf(2.4)
    for k, at in enumerate((.03, .34)): place(b, _anvil(r, 1.1) * (.85 + .15 * k), at)
    place(b, modal(1.5, [(1320, .5, 1), (1325, .5, .8), (3640, .15, .2)], r) * .45, .66)
    return reverb(b, 1.3, .28)


@sfx("sfx.enhance.max", -8, "UI", "+5 다 손봄: 마지막 탕! 뒤에 쇠가 오래 노래하듯 우는 긴 울림 + 화덕 불이 확 일어남(2.4초)", use="손보기로 최대 단계(+5)에 닿은 순간. 등급 소리 대신(등급 소리 끝 대신 이것)")
def _(r):
    b = _buf(3.6)
    place(b, _anvil(r, 1.3), .02)
    place(b, modal(2.6, [(1046, 1.2, 1), (1049, 1.2, .8), (2093, .7, .4), (3136, .3, .2)], r) * .55, .1)   # 쇠가 길게 노래
    m = int(1.0 * SR); place(b, filt(noise(m, r), "band", 420, .7) * env(m, .15, .5, 3) * .5, .05)          # 화덕 불 확
    return reverb(b, 1.8, .3)


@sfx("sfx.enhance.fail", -17, "UI", "엽전이 모자람: 빈 엽전 꾸러미를 흔드는 성긴 짤랑 둘 + 나무 '똑' 하나(0.5초). 실패지만 벌 주는 소리 아님", use="손보기 버튼을 눌렀는데 엽전이 모자랄 때")
def _(r):
    b = _buf(.7)
    for at in (0, .09): place(b, modal(.25, [(r.uniform(3100, 3500), .04, 1), (r.uniform(5200, 5800), .02, .3)], r) * .3, at)
    place(b, _wood_tap(r, 520, .04, .6), .25)
    return reverb(b, .35, .08)


# ═══════════════════════════════════════════════════════════════════════════
# 검은여울 구역 보강 (10-26) — 역병이 돈 물가 마을. 원칙: '살아 있는 소리가 빠진 자리'
#   · 벌레 소리가 없다(보릿들·물막이 골과 가장 크게 다른 점). 대신 파리, 먼 기침, 무거운 물
#   · 물은 맑게 졸졸이 아니라 낮고 끈적하게 꿀렁(솔고개 개울 amb.stream.small 과 대비)
#   · 사람 말소리는 넣지 않는다(산 사람은 말 걸기 없음 — 기침·숨·문소리로만 '사람이 있다')
# ═══════════════════════════════════════════════════════════════════════════
def _cough(r, n_fit=2, muffle=1800):
    """기침 한 번(목소리 없이 숨이 터지는 소리): 짧은 잡음 덩이 2~3개를 목 울림 필터로. 벽 너머면 muffle 낮게"""
    b = _buf(.25 * n_fit + .3)
    for k in range(n_fit):
        m = int(r.uniform(.09, .14) * SR)
        burst = noise(m, r) * env(m, .004, .05, 3)
        y = filt(burst, "band", r.uniform(420, 520), 2) * .8 + filt(burst, "band", r.uniform(1300, 1600), 3) * .5
        place(b, y * (1 - .15 * k), k * r.uniform(.2, .28))
    return filt(b, "low", muffle)


def _crow(r, f=620):
    """까마귀 '까악': 거칠고 쉰 높은 목소리 한 번"""
    d = .38; f0 = curve(d, [(0, f), (.06, f * 1.12), (d, f * .82)])
    y = voice(f0, [(1250, 3, 1), (2500, 4, .5), (3600, 5, .2)], .9, r, nh=24)
    return y * env(int(d * SR), .02, .16, 3, hold=.12)


def _heavy_water(sec, r, f=260, glug=40, amp=.3):
    """검은 물: 낮은 쏴(띠 잡음) + 굵고 느린 꿀렁 방울"""
    n = int(sec * SR)
    x = filt(noise(n, r), "band", f * 2.2, .9) * (.75 + .25 * np.sin(2 * np.pi * .21 * T(sec))) * amp
    x += grains(sec, r, glug, lambda r, k: bubble(r.uniform(.06, .12), r.uniform(f * .6, f * 1.3), 1.5, .045) * r.uniform(.08, .3))
    return x


@sfx("amb.geomeun.night", -26, "세계", "검은여울 밤 바탕: 벌레 소리 없는 죽은 공기 — 아주 낮은 웅 맥놀이, 먼 곳에서 무겁게 흐르는 물, 띄엄띄엄 물방울 한두 번(반복용 20초)", loop=True, use="검은여울 구역 밤 바탕(2D). amb.weather.fog_night 대신. 보릿들에서 넘어오면 풀벌레가 '빠지는' 것이 신호")
def _(r):
    sec = 20.4; n = int(sec * SR); t = T(sec)
    hum = (np.sin(2 * np.pi * 55 * t) + .8 * np.sin(2 * np.pi * 55.6 * t)) * .05
    air = filt(noise(n, r), "low", 300) * .35
    far = filt(_heavy_water(sec, r, 220, 25, .25), "low", 900) * .5
    b = hum + air + far
    place(b, _drips(r, 3.0, 2, 500, 1000, .05, (.1, .2)), 6.0)
    return loopify(reverb(b, 1.6, .3)[:n], .8)


@sfx("amb.geomeun.day", -26, "세계", "검은여울 낮 바탕: 파리 몇 마리가 웅— 오가고, 잎 없는 나무 사이 마른 바람, 먼 물(반복용 18초). 새소리 없음", loop=True, use="검은여울 구역 낮 바탕(2D). 다른 구역 낮은 amb.field 그대로")
def _(r):
    sec = 18.4; n = int(sec * SR); t = T(sec); g = _gust_curve(sec, r, 2, .25)
    wind = filt(noise(n, r), "band", 650, .7) * (.35 + .65 * g) * .45
    flies = np.zeros(n)
    for k in range(3):
        f = r.uniform(180, 240); lfo = .5 + .5 * np.sin(2 * np.pi * r.uniform(.05, .12) * t + r.uniform(0, 6))
        flies += filt(np.sign(np.sin(2 * np.pi * (f + 8 * np.sin(2 * np.pi * 3 * t)) * t)), "band", 600, 1.5) * lfo ** 3 * .05
    far = filt(_heavy_water(sec, r, 240, 20, .2), "low", 1000) * .4
    return loopify(reverb(wind + flies + far, 1.2, .2)[:n], .7)


@sfx("amb.geomeun.river", -24, "세계", "검은 여울물: 맑게 졸졸이 아니라 낮고 끈적하게 꿀렁꿀렁 흐르는 검은 물(반복용 12초)", loop=True, use="여울 물줄기 선(x≈84, z 280~640)을 따라: 플레이어와 가장 가까운 선 위 점 하나에 3D 소리를 붙여 따라 움직임. 최소 3m·최대 22m")
def _(r):
    sec = 12.3; n = int(sec * SR)
    return loopify(reverb(_heavy_water(sec, r, 260, 70, .32), .8, .15)[:n], .5)


@sfx("amb.geomeun.bridge", -22, "세계", "검은여울 돌다리 밑: 다리 기둥에 부딪쳐 빨라진 물살이 쏴아— 거칠게 + 다리 밑 굴에서 울리는 웅(반복용 10초)", loop=True, use="돌다리 한가운데(84,452) 3D. 최소 2m·최대 16m. 여울 선 소리보다 앞에 들림")
def _(r):
    sec = 10.3; n = int(sec * SR)
    rush = filt(noise(n, r), "band", 900, .6) * (.8 + .2 * np.sin(2 * np.pi * .37 * T(sec))) * .45
    x = rush + _heavy_water(sec, r, 300, 60, .2)
    return loopify(reverb(x, 1.4, .35, 3000)[:n], .5)


@sfx("amb.foul.pool", -27, "세계", "썩은 물웅덩이: 진득한 거품이 아주 천천히 '뽀글…' 올라와 터짐(반복용 9초)", loop=True, use="썩은 웅덩이(prop_foul_pool) 3D, 가까운 순 3개. 최소 1m·최대 6m")
def _(r):
    sec = 9.3; n = int(sec * SR); b = filt(noise(n, r), "low", 200) * .05
    for at in np.sort(r.uniform(0, sec - .5, 7)):
        place(b, _sum(bubble(.18, r.uniform(110, 190), 1.3, .07) * .5, _mud(r, .2, 2, (120, 260))), at)
    return loopify(reverb(b, .5, .12)[:n], .4)


@sfx("amb.sick.lantern", -22, "세계", "병자 등(창백한 초록 불): 장대에 매단 종이 등이 바람에 끼익… 흔들리고 심지가 작게 지직(반복용 8초)", loop=True, use="병자 등(prop_sick_lantern) 3D, 가까운 순 3개. 최소 1m·최대 6m. 밤에만")
def _(r):
    sec = 8.3; n = int(sec * SR)
    b = grains(sec, r, 25, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(2500, 5000), 3) * env(int(.004 * SR), .0003, .0015) * r.uniform(.04, .15))
    for at in (1.0, 4.6): place(b, _creak(r, .7, r.uniform(150, 190), 24, 900) * .35, at)
    place(b, _paper(r, .3, 1200, 4000) * .12, 2.4)
    return loopify(reverb(b, .6, .15)[:n], .4)


@sfx("amb.plague.banner", -28, "세계", "역병 깃발: 젖어 무거운 천이 바람에 느리게 펄… 펄 — 가볍게 나부끼지 않는다(반복용 10초)", loop=True, use="역병 깃발(prop_plague_banner) 3D, 가까운 순 2개. 최소 1m·최대 8m")
def _(r):
    sec = 10.3; n = int(sec * SR); g = _gust_curve(sec, r, 2, .2)
    cloth = filt(_flutter(sec, r, g, rate=(2.5, 5), bright=900), "low", 1500) * .6
    pole = _buf(sec); place(pole, _creak(r, .5, 120, 18, 500) * .3, 5.2)
    return loopify(reverb(cloth + pole, .6, .15)[:n], .5)


@sfx("amb.quarantine.hut", -29, "세계", "격리 움막 안: 벽 너머 먹먹한 기침, 거적이 사각 뒤척, 느린 숨(반복용 16초). 말소리 없음", loop=True, use="격리 움막(prop_quarantine_hut) 3D, 가까운 순 2개. 최소 1m·최대 7m. 밤·낮 모두(낮엔 0.7배). '엿듣기'의 바탕")
def _(r):
    sec = 16.4; n = int(sec * SR); t = T(sec)
    breath = filt(noise(n, r), "band", 500, 1.2) * (np.clip(np.sin(2 * np.pi * .23 * t), 0, None) ** 2) * .08
    b = breath
    place(b, _cough(r, 3, 1100) * .5, 2.5); place(b, _cough(r, 2, 1000) * .35, 10.8)
    place(b, filt(_paper(r, .5, 400, 1800), "low", 1500) * .2, 7.0)                  # 거적 뒤척
    return loopify(reverb(b, .5, .2, 2500)[:n], .6)


@sfx("amb.doctor.house", -26, "세계", "의원 집(서 의원): 약탕기가 보글보글 끓고, 약연(약 가는 맷돌)이 드르륵… 드르륵, 가끔 약재 서랍 톡(반복용 14초)", loop=True, use="의원 집(52,468) 3D. 최소 1.5m·최대 10m. 약탕기(prop_herb_pot)들은 따로 소리 없이 이 하나로 대표. 보스 ③ 무대 후보라 보스 날엔 끔")
def _(r):
    sec = 14.4; n = int(sec * SR)
    simmer = grains(sec, r, 140, lambda r, k: bubble(r.uniform(.02, .04), r.uniform(500, 1100), 1.8, .012) * r.uniform(.05, .2)) + filt(noise(n, r), "band", 1500, .8) * .03
    b = simmer
    for at in (1.2, 5.8, 10.5):
        m = int(1.4 * SR); grind = filt(noise(m, r), "band", 300, 1.2) * (.5 + .5 * np.abs(np.sin(2 * np.pi * 1.6 * T(1.4)))) * env(m, .2, .5, 3, hold=.6)
        place(b, grind * .35, at)
    place(b, _wood_tap(r, 1100, .02, .3), 8.6)
    return loopify(reverb(b, .7, .2)[:n], .5)


@sfx("amb.ferry.idle", -25, "세계", "빈 나룻배: 매어 둔 배가 말뚝에 텅… 부딪히고, 밧줄이 끼익, 뱃전에 물이 찰박(반복용 12초)", loop=True, use="나루터(88.4,548) 3D. 최소 2m·최대 12m. 2막 뱃사공이 오면 그 장면 소리로 바뀜")
def _(r):
    sec = 12.3; n = int(sec * SR)
    lap = grains(sec, r, 30, lambda r, k: (bubble(.08, r.uniform(250, 500), 1.4, .04) + filt(noise(int(.08 * SR), r), "band", 900, 1.5) * env(int(.08 * SR), .005, .03)) * r.uniform(.1, .3))
    b = lap + _heavy_water(sec, r, 250, 10, .12)
    for at in (2.0, 7.4): place(b, modal(.7, [(r.uniform(140, 170), .2, 1), (r.uniform(380, 430), .1, .4)], r) * .5, at)   # 배가 말뚝에 텅
    place(b, _rope_taut(r, .9, 100) * .25, 4.6)
    return loopify(reverb(b, .9, .2)[:n], .5)


@sfx("amb.willow", -29, "세계", "물가 버드나무: 늘어진 가지가 물낯을 쓸며 스스스— 아주 부드럽게(반복용 12초)", loop=True, use="버드나무(br_willow_a/b) 3D, 가까운 순 2개. 최소 2m·최대 9m")
def _(r):
    sec = 12.3; n = int(sec * SR); g = _gust_curve(sec, r, 2, .3)
    x = filt(noise(n, r), "band", 2600, 1.0) * (.25 + .75 * g) * .3 + _paper_strips(sec, r, g, 40) * .3
    return loopify(reverb(x, .6, .15)[:n], .5)


@sfx("amb.reed.wet", -28, "세계", "젖은 갈대밭: 갈대 줄기가 서로 쓸리는 사르르 + 밑동에서 물이 찰랑(반복용 12초)", loop=True, use="갈대밭(br_reed_field) 3D, 가까운 순 2개. 최소 2m·최대 10m")
def _(r):
    sec = 12.3; n = int(sec * SR); g = _gust_curve(sec, r, 3, .25)
    x = filt(noise(n, r), "band", 3600, 1.4) * (.2 + .8 * g) * .3 + grains(sec, r, 70, lambda r, k: _paper(r, r.uniform(.05, .12), 1800, 5000) * r.uniform(.05, .2))
    x += grains(sec, r, 12, lambda r, k: bubble(.06, r.uniform(400, 800), 1.6, .03) * .1)
    return loopify(reverb(x, .6, .15)[:n], .5)


@sfx("amb.mist.bank", -30, "세계", "물안개 덩이 속: 소리가 먹히는 먹먹한 쉬— + 젖은 잎에서 물방울(반복용 10초). 들어가면 다른 소리를 저역 통과로 흐리게", loop=True, use="물안개 덩이(prop_mist_bank·prop_mist_pillar) 안 4m. 가장 가까운 하나만. 안에 있는 동안 구역 바탕·점 소리에 저역 통과 2.5kHz")
def _(r):
    sec = 10.3; n = int(sec * SR)
    x = filt(noise(n, r), "low", 450) * .4 + _drips(r, sec, 6, 700, 1300, .04, (.05, .15))
    return loopify(reverb(x, 1.2, .3, 2500)[:n], .5)


@sfx("amb.graves", -30, "세계", "무덤 다섯: 마른 풀이 사스락, 그 아래 귀를 기울여야 들리는 아주 낮은 웅— (넋이 남은 자리, 반복용 14초)", loop=True, use="무덤 무리(약 101,499) 3D. 최소 1m·최대 8m. 밤에만. 천도 대상이 아닐 때도 늘 깔림")
def _(r):
    sec = 14.4; n = int(sec * SR); t = T(sec); g = _gust_curve(sec, r, 2, .3)
    grass = grains(sec, r, 50, lambda r, k: _paper(r, r.uniform(.05, .1), 1500, 4500) * r.uniform(.05, .15)) * 1.0
    hum = (np.sin(2 * np.pi * 73 * t) + .6 * np.sin(2 * np.pi * 110.4 * t)) * (.6 + .4 * np.sin(2 * np.pi * .07 * t)) * .04
    gg = np.interp(np.arange(n), np.arange(len(g)), g)
    return loopify(reverb(_sum(grass[:n] * (.4 + .6 * gg[:len(grass[:n])]), hum), 1.4, .3)[:n], .6)


# ── 검은여울 가끔 섞기(한 번짜리) ──
@sfx("sfx.geomeun.cough.far", -27, "세계", "멀리서 누가 기침 세 번(먹먹하게, 1.2초). 말소리 없음", use="검은여울 가끔 섞기 40~90초")
def _(r):
    return reverb(_cough(r, 3, 1400), 1.2, .35)


@sfx("sfx.geomeun.crow", -24, "세계", "까마귀 두 번 까악… 까악(멀리, 1.4초)", use="검은여울 가끔 섞기 35~80초(낮 위주, 밤엔 0.3배 확률)")
def _(r):
    b = _buf(1.6)
    place(b, _crow(r, 620), 0); place(b, _crow(r, 590) * .85, .6)
    return reverb(filt(b, "low", 3500), 1.5, .35)


@sfx("sfx.geomeun.plop", -24, "세계", "무언가 검은 물에 떨어짐: 무겁게 '퐁' + 천천히 번지는 물결(1.0초)", use="검은여울 가끔 섞기 25~60초. 여울 선 쪽 방향에서")
def _(r):
    b = _buf(1.4)
    place(b, bubble(.25, 160, 1.6, .08) * .8, 0)
    place(b, _drips(r, .9, 5, 400, 800, .05, (.08, .2)), .15)
    return reverb(b, 1.0, .25)


@sfx("sfx.geomeun.clapper", -25, "세계", "먼 곳 야경꾼 딱따기: 딱! 딱! 딱! 세 번(멀리, 1.5초) — 역병 마을 밤 순찰", use="검은여울 밤 가끔 섞기 70~140초")
def _(r):
    b = _buf(1.4)
    for k, at in enumerate((0, .38, .76)): place(b, (_wood_tap(r, 1250, .025) + _wood_tap(r, 1180, .02) * .6) * (1 - .1 * k), at)
    return reverb(filt(b, "low", 3000), 2.0, .45)


@sfx("sfx.geomeun.door", -24, "세계", "움막 거적문이 끼이익 닫힘 + 나무 문틀에 툭(1.0초)", use="검은여울 가끔 섞기 50~110초. 격리 움막 쪽 방향에서")
def _(r):
    b = _buf(1.3)
    place(b, _creak(r, .6, 210, 28, 800) * .6, 0)
    place(b, _thump(r, .1, 160, 500) * .5, .62)
    return reverb(b, .6, .2)


@sfx("sfx.geomeun.groan", -22, "세계", "여울이 앓음: 물 밑에서 큰 거품이 웅— 하고 낮게 올라와 터짐(1.8초). 원념이 고인 물이라는 암시", use="검은여울 밤 가끔 섞기 90~180초(가장 드물게). 업 30 이상이면 간격 절반")
def _(r):
    b = _buf(2.2)
    m = int(1.2 * SR); t = T(1.2)
    place(b, tone(1.2, 48, 62) * env(m, .5, .35, 3) * .5 + filt(noise(m, r), "low", 220) * env(m, .5, .35, 3) * .4, 0)
    place(b, bubble(.35, 90, 1.4, .12) * .7, 1.0)
    return reverb(b, 1.4, .3)


# ═══════════════════════════════════════════════════════════════════════════
# 2막 ③ 붉은재(산성)·④ 쇳골(광산) 주변 소리 — 1막 수준으로 보강 (10-26)
# 1막과 같은 세 겹: 구역 바탕 / 자리·소품 점 소리 / 가끔 섞기. 여기에 '엿듣기 자리 생활 소리'(소문 15곳)를 더한다
#   · ③ 아랫마을은 산 사람이 많은 마을: 낮엔 생활 소리가 가장 촘촘하다(솔고개 마을보다 바쁘게)
#   · ④ 광부촌은 쇠·돌·석탄 소리. 사람 이름 대신 번호로 불리는 마을이라 '사람 목소리'는 늘 멀고 흐리다
#   · 말뜻이 들리는 목소리는 넣지 않는다(엿듣기 문구는 글자로 나온다). 웅얼거림은 높은 쪽을 깎아 뜻을 지움
# ═══════════════════════════════════════════════════════════════════════════
def _hoe(r, a=1.0):
    """호미·괭이가 돌 섞인 흙을 콕: 흙 퍽 + 작은 돌 틱"""
    m = int(.08 * SR)
    return (filt(noise(m, r), "band", r.uniform(500, 900), 1.2) * env(m, .002, .03, 3) * .7 + modal(.12, [(r.uniform(2500, 3500), .02, .3)], r)[:m]) * a


def _bat(r, a=1.0):
    """빨래 방망이가 젖은 천을 돌 위에서 탁: 물 먹은 퍽 + 돌 울림"""
    m = int(.15 * SR)
    return (filt(noise(m, r), "band", 700, 1.0) * env(m, .001, .03, 3) + modal(.15, [(r.uniform(380, 450), .04, .5)], r)[:m] * .5
            + grains(.15, r, 4, lambda r, k: bubble(.03, r.uniform(800, 1600)) * .15)) * a


def _axe(r, a=1.0):
    """도끼가 나무에 턱: 묵직한 나무 울림 + 쪼개지는 짧은 바삭"""
    m = int(.3 * SR)
    return _sum(_wood_tap(r, r.uniform(320, 380), .06, 1.0), filt(noise(m, r), "band", 2200, 1.5) * env(m, .001, .02, 3) * .4) * a


def _hoof(r, a=1.0):
    """발굽 한 번 '딱': 단단한 굽이 흙·돌에 닿음"""
    return _sum(_wood_tap(r, r.uniform(700, 850), .02, .8), _thump(r, .08, 140, 400) * .5) * a


def _bed_wind(sec, r, f=500, q=.7, amp=.4, gusts=3):
    """구역 바탕용 바람(돌풍 곡선 실은 띠 잡음)"""
    n = int(sec * SR); g = _gust_curve(sec, r, gusts, .3)
    gg = np.interp(np.arange(n), np.arange(len(g)), g)
    return filt(noise(n, r), "band", f, q) * (.35 + .65 * gg) * amp, gg


# ── ③ 구역 바탕 ──
@sfx("amb.fv.day", -24, "세계", "산성 아랫마을 낮: 먼 마당의 웅얼거림(뜻 안 들림), 닭 몇 마리 꼬꼬, 어디선가 방망이 탁탁·도끼 턱, 개 한 번 — 사람이 사는 마을(반복용 20초)", loop=True, use="FortressVillage 낮 바탕(2D). 다른 2막 구역 낮은 지금 ZoneAmbient 소리 그대로")
def _(r):
    sec = 20.4; n = int(sec * SR)
    b, _g = _bed_wind(sec, r, 600, .7, .18, 2)
    b = b + filt(_murmur(r, sec, 6, (110, 210), 1100, .35, (.6, 2.0)), "low", 1100) * .25
    for at in (2.0, 2.4, 9.1, 15.8): place(b, filt(_bird(r, 900, 2), "low", 2500) * .2, at)                 # 닭 꼬꼬(낮은 새 소리)
    for k in range(6): place(b, _bat(r, .25), 5.0 + k * .45)                                                  # 먼 방망이
    for k in range(3): place(b, _axe(r, .3), 12.0 + k * 1.1)                                                  # 먼 도끼
    return loopify(reverb(b, 1.3, .3)[:n], .8)


@sfx("amb.fv.night", -26, "세계", "산성 아랫마을 밤: 풀벌레 몇, 술도가 쪽 아주 작은 보글, 산에서 내려오는 찬 바람, 담 너머 가끔 기침 — 불 꺼진 산마을(반복용 18초)", loop=True, use="FortressVillage 밤 바탕(2D)")
def _(r):
    sec = 18.4; n = int(sec * SR)
    b, _g = _bed_wind(sec, r, 380, .6, .3, 2)
    b = b + _crickets(sec, r, count=4, amp=.04)
    place(b, filt(_cough_soft(r), "low", 1000) * .25, 11.0)
    return loopify(reverb(b, 1.4, .3)[:n], .8)


def _cough_soft(r):
    """담 너머 작은 기침 두 번(먹먹하게)"""
    b = _buf(.6)
    for k in range(2):
        m = int(.1 * SR); place(b, filt(noise(m, r), "band", 480, 2) * env(m, .004, .04, 3) * (1 - .3 * k), k * .22)
    return b


@sfx("amb.bigtomb", -25, "세계", "큰 무덤: 비석 없는 큰 봉분 위를 넘는 바람 쏴— 마른 풀이 한쪽으로 쓸림, 땅 밑 아주 낮은 웅(묻힌 혼 많음), 먼 까마귀(반복용 18초)", loop=True, use="BigTomb 바탕(2D) 밤·낮. 밤엔 웅을 1.5배(믹스 쪽에서)")
def _(r):
    sec = 18.4; n = int(sec * SR); t = T(sec)[:n]
    w, gg = _bed_wind(sec, r, 700, .6, .35, 3)
    grass = grains(sec, r, 70, lambda r, k: _paper(r, r.uniform(.05, .1), 1800, 5000) * r.uniform(.05, .15))[:n] * (.3 + .7 * gg)
    hum = (np.sin(2 * np.pi * 61 * t) + .7 * np.sin(2 * np.pi * 61.5 * t) + .3 * np.sin(2 * np.pi * 92 * t)) * .035
    b = w + grass + hum
    place(b, reverb(filt(_crow(r, 600), "low", 3000), 1.2, .3) * .2, 7.5)
    return loopify(reverb(b, 1.4, .3)[:n], .8)


# ── ④ 구역 바탕 ──
@sfx("amb.sorting.day", -22, "세계", "선탄장 낮: 평상 위에서 석탄 덩이를 고르는 달그락 사르르, 삽이 무더기를 쓱, 소쿠리 쏟는 와르르, 먼 웅얼거림(반복용 18초)", loop=True, use="Sorting 낮 바탕(2D)")
def _(r):
    sec = 18.4; n = int(sec * SR)
    coal = grains(sec, r, 160, lambda r, k: modal(.06, [(r.uniform(1800, 3800), .012, 1)], r) * r.uniform(.03, .15))
    b = coal + filt(_murmur(r, sec, 4, (160, 240), 900, .4, (.8, 2.5)), "low", 900) * .18
    for at in (3.0, 9.5, 14.0):
        m = int(.5 * SR); place(b, filt(noise(m, r), "band", 1500, 1.2) * env(m, .05, .2, 3) * .35, at)   # 삽 쓱
    m = int(1.1 * SR); place(b, grains(1.1, r, 60, lambda r, k: modal(.08, [(r.uniform(1200, 3000), .02, 1)], r) * r.uniform(.05, .25)), 6.5)   # 소쿠리 쏟음
    return loopify(reverb(b, .9, .2)[:n], .7)


@sfx("amb.sorting.night", -27, "세계", "선탄장 밤: 아무도 없는 평상, 검은 가루가 바람에 사르르 날리고, 기대 둔 삽이 가끔 삐걱(반복용 16초). 벌레 소리 거의 없음", loop=True, use="Sorting 밤 바탕(2D)")
def _(r):
    sec = 16.4; n = int(sec * SR)
    w, gg = _bed_wind(sec, r, 900, .9, .3, 3)
    dust = grains(sec, r, 120, lambda r, k: filt(noise(int(.01 * SR), r), "high", 4000) * env(int(.01 * SR), .001, .004) * r.uniform(.02, .08))[:n] * gg
    b = w + dust
    place(b, _creak(r, .5, 170, 22, 800) * .2, 9.0)
    return loopify(reverb(b, 1.1, .25)[:n], .7)


@sfx("amb.collapse", -24, "세계", "무너진 막장: 막힌 굴 입구 — 돌이 아직 자리 잡느라 가끔 바스스, 버팀목이 낮게 끄응, 고인 물 똑… 똑, 바람이 들어가지 못하는 먹먹함(반복용 16초)", loop=True, use="Collapse 바탕(2D). 지금 amb.mine.shaft 대신. B-07 날엔 보스 음악 쪽")
def _(r):
    sec = 16.4; n = int(sec * SR)
    b = filt(noise(n, r), "low", 180) * .3 + _drips(r, sec, 9, 500, 900, .06, (.1, .3))
    for at in (3.5, 11.0): place(b, grains(.8, r, 25, lambda r, k: modal(.07, [(r.uniform(900, 2400), .015, 1)], r) * r.uniform(.05, .2)), at)   # 돌 바스스
    place(b, _creak(r, 1.2, 70, 12, 300) * .4, 7.0)                                                          # 버팀목 끄응
    return loopify(reverb(b, 2.0, .45, 2500)[:n], .8)


# ── ③ 자리 점 소리 ──
@sfx("amb.seonang.bulgeunjae", -24, "세계", "붉은재 서낭당: 고갯마루 센 바람에 붉은 천이 펄럭펄럭, 돌무더기 틈 바람 휘— , 금줄 한지 사락(반복용 16초)", loop=True, use="SH2-1(112,790) 3D. 최소 2m·최대 14m. 1막 서낭당 다섯과 같은 크기")
def _(r):
    sec = 16.4; n = int(sec * SR)
    w, gg = _bed_wind(sec, r, 520, .6, .5, 3)
    cloth = _flutter(sec, r, gg, rate=(8, 15), bright=2000)[:n] * .4
    whistle = filt(noise(n, r), "band", 1900, 12) * gg ** 2 * .25
    return loopify(reverb(w + cloth + whistle + _paper_strips(sec, r, gg, 50)[:n] * .4, .9, .2)[:n], .6)


@sfx("amb.seonang.sanshin", -25, "세계", "산신각(광부촌 남쪽): 작은 각 안 — 바람 막힌 고요, 엎어 둔 막걸리 사발에 바람이 웅— 맴돌고, 처마 끝 풍경 하나가 아주 가끔 땡(반복용 18초)", loop=True, use="SH2-2(455,790) 3D. 최소 2m·최대 12m")
def _(r):
    sec = 18.4; n = int(sec * SR)
    w, gg = _bed_wind(sec, r, 300, .6, .25, 2)
    bowl = filt(noise(n, r), "band", 640, 10) * gg * .2
    b = w + bowl
    for at in (4.0, 13.2): place(b, modal(2.5, [(1480, .9, 1), (1486, .9, .7), (3900, .3, .2)], r) * .15, at)   # 풍경
    return loopify(reverb(b, 1.2, .25)[:n], .7)


@sfx("amb.sooldoga", -21, "세계", "술도가: 줄지은 술독 안에서 술이 익는 보글… 톡톡(아주 작은 거품), 독 뚜껑이 가끔 툭, 누룩 냄새 같은 따뜻한 고요(반복용 14초)", loop=True, use="술도가(95,875) 3D. 최소 1.5m·최대 10m. S-049 장례 뒤에도 그대로(손녀가 잇는다)")
def _(r):
    sec = 14.4; n = int(sec * SR)
    fizz = grains(sec, r, 260, lambda r, k: bubble(r.uniform(.01, .025), r.uniform(1500, 3500), 1.6, .006) * r.uniform(.02, .1))
    b = fizz + grains(sec, r, 20, lambda r, k: bubble(.08, r.uniform(250, 450), 1.4, .03) * r.uniform(.05, .15))
    for at in (5.2, 11.0): place(b, modal(.4, [(r.uniform(260, 300), .08, 1), (r.uniform(700, 780), .04, .4)], r) * .3, at)   # 독 뚜껑 툭
    return loopify(reverb(b, .7, .2)[:n], .5)


@sfx("amb.stonemason", -23, "세계", "석수 일터(쌓다 만 성벽): 정이 돌을 깡… 깡 쪼는 소리 몇 번 쉬었다가, 돌 부스러기 사르르, 큰 돌을 지렛대로 끄응(반복용 16초). 낮에만", loop=True, use="석수 일터(148,915) 3D, 낮에만. 최소 2m·최대 16m. S-051 장례 뒤엔 정 소리가 반으로(제자 혼자)")
def _(r):
    sec = 16.4; n = int(sec * SR); b = _buf(sec)
    at = .5
    while at < sec - 1:
        for _k in range(r.integers(3, 6)):
            place(b, modal(.4, [(r.uniform(2400, 2900), .05, 1), (r.uniform(5200, 6000), .02, .4), (r.uniform(900, 1100), .07, .4)], r) * r.uniform(.4, .8), at); at += r.uniform(.42, .6)
        place(b, grains(.6, r, 15, lambda r, k: modal(.05, [(r.uniform(2000, 4500), .01, 1)], r) * .1), at)
        at += r.uniform(2.0, 3.5)
    place(b, _creak(r, .9, 90, 14, 400) * .3, 8.0)
    return loopify(reverb(b, 1.2, .3)[:n], .6)


@sfx("amb.village.shrine", -27, "세계", "마을 사당('장군지위'): 문살 사이로 바람이 스— , 향 연기처럼 가는 쉬이, 사당 노인이 앉는 돌계단의 고요(반복용 14초)", loop=True, use="마을 사당(132,900) 3D. 최소 1.5m·최대 9m")
def _(r):
    sec = 14.4; n = int(sec * SR)
    w, gg = _bed_wind(sec, r, 1400, 3, .2, 2)
    b = w + filt(noise(n, r), "high", 5000) * .02
    place(b, _creak(r, .6, 200, 30, 900) * .15, 6.0)
    return loopify(reverb(b, 1.0, .3)[:n], .6)


@sfx("amb.well.village", -21, "세계", "마을 우물: 두레박 줄이 도르래에 끼익 감기고, 물 담긴 두레박이 우물 벽에 툭, 물 쏟는 쏴— (반복용 14초)", loop=True, use="아랫마을 우물(115,858)·광부촌 우물가(470,836) 3D. 낮·저녁만. 최소 1m·최대 8m. 엿듣기 R2-02·R2-12 자리")
def _(r):
    sec = 14.4; n = int(sec * SR); b = filt(noise(n, r), "low", 200) * .03
    place(b, _creak(r, 1.6, 230, 34, 900) * .4, 1.0)                                                   # 도르래
    place(b, modal(.5, [(r.uniform(180, 220), .1, 1), (r.uniform(520, 600), .05, .4)], r) * .4, 2.9)  # 두레박 툭
    place(b, _splash(r, 1.0, .7) * .5, 4.0)                                                            # 물 쏟음
    place(b, _drips(r, 2.0, 8, 600, 1200, .04, (.1, .25)), 5.0)
    return loopify(reverb(b, .9, .25)[:n], .6)


@sfx("amb.laundry", -24, "세계", "빨래터: 방망이가 돌 위 젖은 천을 탁 탁 탁, 천을 물에 헹구는 철벙 찰박, 비틀어 짜는 주르륵(반복용 14초)", loop=True, use="아랫마을 마당(110,862, 엿듣기 R2-01, 낮)·광부촌 우물가(470,836, R2-12, 저녁) 3D. 최소 1m·최대 10m")
def _(r):
    sec = 14.4; n = int(sec * SR); b = _buf(sec)
    at = .3
    for burst in range(3):
        for _k in range(r.integers(5, 9)): place(b, _bat(r, r.uniform(.5, .9)), at); at += r.uniform(.32, .42)
        place(b, _splash(r, .7, .5) * .4, at + .3); at += 1.2
        m = int(.9 * SR); place(b, grains(.9, r, 30, lambda r, k: bubble(.03, r.uniform(900, 2000)) * .12), at); at += r.uniform(1.0, 1.6)
    return loopify(reverb(b, .7, .2)[:n], .5)


@sfx("amb.whetstone", -27, "세계", "담 너머 낫 가는 소리: 숫돌에 쓱— 싹— 쓱— 싹, 물 한 번 끼얹는 찰박(벽에 먹혀 먹먹, 반복용 12초)", loop=True, use="벌초꾼 집(125,840) 담 너머, 저녁. 엿듣기 R2-03. 최소 1m·최대 7m")
def _(r):
    sec = 12.3; n = int(sec * SR); b = _buf(sec)
    at = .4
    while at < sec - 1:
        for k in range(r.integers(6, 10)):
            m = int(.35 * SR); place(b, filt(noise(m, r), "band", 3200 if k % 2 else 2600, 3) * env(m, .08, .12, 3, hold=.08) * .5, at); at += .42
        place(b, _splash(r, .4, .3) * .3, at); at += r.uniform(1.5, 2.5)
    return loopify(filt(reverb(b, .5, .2), "low", 2200)[:n], .5)


@sfx("amb.lamp.room", -24, "세계", "담 너머 밤의 방: 등잔 심지가 지직, 종이(명단·장부)를 넘기는 사락, 무릎을 고쳐 앉는 옷 스침(먹먹, 반복용 14초). 말소리 없음", loop=True, use="밤 담 너머 엿듣기 자리 바탕: 이장 집(104,850, R2-06)·순돌 집(445,890, R2-14). 엿듣기 문구가 뜨는 동안만. 최소 1m·최대 6m")
def _(r):
    sec = 14.4; n = int(sec * SR)
    b = grains(sec, r, 30, lambda r, k: filt(noise(int(.004 * SR), r), "band", r.uniform(2000, 4000), 3) * env(int(.004 * SR), .0003, .0015) * r.uniform(.04, .12))
    for at in (3.0, 9.0): place(b, _paper(r, .35, 900, 4000) * .3, at)
    place(b, filt(noise(int(.6 * SR), r), "band", 600, 1) * env(int(.6 * SR), .2, .2, 3) * .15, 6.0)
    return loopify(filt(reverb(b, .5, .25), "low", 2000)[:n], .5)


@sfx("amb.herb.dig", -25, "세계", "약초 캐기: 호미가 바위틈 흙을 콕 콕, 뿌리를 쑥 뽑는 소리, 소쿠리에 툭 담음(반복용 12초)", loop=True, use="화살골 어귀(215,920) 낮. 엿듣기 R2-04. 최소 1m·최대 8m. 화살골 바람 위에 얹힘")
def _(r):
    sec = 12.3; n = int(sec * SR); b = _buf(sec)
    at = .5
    while at < sec - 1.5:
        for _k in range(r.integers(3, 6)): place(b, _hoe(r, r.uniform(.5, .9)), at); at += r.uniform(.35, .55)
        m = int(.3 * SR); place(b, filt(noise(m, r), "band", 900, 1) * env(m, .1, .1, 3) * .4, at)        # 뿌리 쑥
        place(b, _thump(r, .1, 220, 700) * .3, at + .6); at += r.uniform(2.0, 3.0)
    return loopify(reverb(b, .9, .25)[:n], .5)


@sfx("amb.woodcutter", -25, "세계", "나무꾼: 산비탈에서 도끼가 턱… 턱… 몇 번(울림 큼), 장작 다발을 지게에 얹는 와르르 툭(반복용 16초)", loop=True, use="산성 문(118,962) 앞 낮. 엿듣기 R2-05. 최소 2m·최대 20m(멀리서도 들림)")
def _(r):
    sec = 16.4; n = int(sec * SR); b = _buf(sec)
    at = .5
    for burst in range(2):
        for _k in range(r.integers(4, 6)): place(b, _axe(r, r.uniform(.6, 1)), at); at += r.uniform(.9, 1.2)
        place(b, grains(.6, r, 8, lambda r, k: _wood_tap(r, r.uniform(500, 900), .03, .3)), at + .5); at += 3.0
    return loopify(reverb(b, 2.0, .45)[:n], .6)


@sfx("amb.peddler", -25, "세계", "길 가는 장꾼: 짐 진 지게가 걸음마다 삐걱 삐걱, 흙길 발소리 두 사람, 허리춤 작은 방울 짤랑(반복용 12초)", loop=True, use="아랫마을 남쪽 어귀(110,812) 낮. 엿듣기 R2-07. 최소 1m·최대 10m")
def _(r):
    sec = 12.3; n = int(sec * SR); b = _buf(sec)
    for k in range(int(sec / .55)):
        at = .2 + k * .55
        place(b, filt(noise(int(.07 * SR), r), "band", 600, 1) * env(int(.07 * SR), .003, .03, 3) * .35, at)
        place(b, filt(noise(int(.07 * SR), r), "band", 520, 1) * env(int(.07 * SR), .003, .03, 3) * .3, at + .27)
        if k % 2 == 0: place(b, _creak(r, .25, 260, 40, 1100) * .2, at + .05)
        if k % 5 == 2: place(b, modal(.4, [(r.uniform(4200, 4800), .06, 1), (r.uniform(6800, 7400), .03, .4)], r) * .1, at + .1)
    return loopify(reverb(b, .7, .2)[:n], .5)


@sfx("amb.grave.tending", -27, "세계", "무덤 돌보기: 손으로 풀을 뜯는 뚝 뚝, 싸리비로 봉분 앞을 쓱— 쓸고, 작은 잔을 돌상에 톡(반복용 14초)", loop=True, use="작은 무덤 떼(60,1205) 낮. 엿듣기 R2-08. 최소 1m·최대 8m")
def _(r):
    sec = 14.4; n = int(sec * SR); b = _buf(sec)
    for at in np.sort(r.uniform(.5, 5.5, 8)): place(b, filt(noise(int(.05 * SR), r), "band", 1800, 2) * env(int(.05 * SR), .002, .015, 3) * .3, at)
    for k in range(5):
        m = int(.6 * SR); place(b, filt(noise(m, r), "band", 2400, .9) * env(m, .15, .25, 3) * .3, 6.5 + k * .8)
    place(b, modal(.5, [(r.uniform(2100, 2400), .08, 1), (r.uniform(5000, 5600), .03, .3)], r) * .2, 12.0)
    return loopify(reverb(b, .9, .25)[:n], .6)


# ── ④ 자리 점 소리 ──
@sfx("amb.shift.change", -20, "세계", "새벽 교대: 무거운 짚신 발소리 여럿이 지나가고, 허리에 찬 쇠 등잔이 짤그랑, 곡괭이 자루를 어깨에 고쳐 메는 툭, 기침 한 번(반복용 14초)", loop=True, use="광부촌 어귀(458,805) 새벽. 엿듣기 R2-09. 최소 1m·최대 10m")
def _(r):
    sec = 14.4; n = int(sec * SR); b = _buf(sec)
    for p in range(4):
        st = r.uniform(0, 1.5)
        for k in range(int((sec - 2) / .6)):
            place(b, filt(noise(int(.08 * SR), r), "band", r.uniform(350, 550), 1) * env(int(.08 * SR), .004, .035, 3) * .2, st + k * .6 + r.uniform(-.03, .03))
    for at in (2.2, 7.8): place(b, _chain_links(r, .2, 3) * .25, at)
    place(b, _wood_tap(r, 600, .04, .3), 5.0)
    place(b, _cough_soft(r) * .4, 10.5)
    return loopify(reverb(b, .9, .25)[:n], .6)


@sfx("amb.gukbap", -23, "세계", "국밥집 저녁: 큰 가마솥이 설설 끓고, 국자가 솥전을 땡, 뚝배기에 숟가락 달그락, 나무 걸상 삐걱, 먼 웅얼거림(반복용 16초)", loop=True, use="국밥집(462,875) 저녁·밤. 엿듣기 R2-10. 최소 1.5m·최대 10m. S-069 장례 뒤엔 솥 소리만")
def _(r):
    sec = 16.4; n = int(sec * SR)
    boil = grains(sec, r, 220, lambda r, k: bubble(r.uniform(.02, .05), r.uniform(350, 900), 1.7, .015) * r.uniform(.04, .15)) + filt(noise(n, r), "band", 900, .8) * .05
    b = boil + filt(_murmur(r, sec, 4, (100, 160), 800, .4, (.8, 2.5)), "low", 800) * .2
    for at in (3.0, 10.4): place(b, modal(.8, [(r.uniform(1100, 1250), .25, 1), (r.uniform(2900, 3200), .1, .4)], r) * .2, at)   # 국자 땡
    for at in np.sort(r.uniform(1, sec - 1, 9)): place(b, modal(.15, [(r.uniform(2600, 3600), .03, 1)], r) * .1, at)            # 숟가락
    place(b, _creak(r, .4, 190, 30, 900) * .15, 7.2)
    return loopify(reverb(b, .7, .25)[:n], .6)


@sfx("amb.mule.stable", -21, "세계", "노새 마구간: 발굽으로 바닥을 딱 딱 구르고, 코로 푸르르, 여물 씹는 소리, 굴레 쇠고리 짤랑(반복용 14초)", loop=True, use="노새 마구간(492,842) 낮. 엿듣기 R2-11. 최소 1m·최대 8m")
def _(r):
    sec = 14.4; n = int(sec * SR); b = _buf(sec)
    for at in (1.0, 1.35, 7.4, 7.7, 8.0): place(b, _hoof(r, .5), at)
    m = int(.7 * SR); snort = filt(noise(m, r), "band", 500, 1.5) * env(m, .05, .25, 3) * (1 + .5 * np.sin(2 * np.pi * 28 * T(.7)[:m]))
    for at in (3.5, 11.6): place(b, snort * .5, at)
    for k in range(18): place(b, filt(noise(int(.06 * SR), r), "band", 1600, 2) * env(int(.06 * SR), .003, .02, 3) * .1, 4.6 + k * .21)   # 여물 씹기
    place(b, _chain_links(r, .15, 2) * .15, 9.5)
    return loopify(reverb(b, .6, .2)[:n], .6)


@sfx("amb.mokpae.board", -25, "세계", "목패 걸이 판: 갱 오르막 길가, 걸린 나무 목패들이 바람에 서로 딸깍 딸각 — 빈 고리 몇 개가 쇠소리로 짤랑(반복용 14초)", loop=True, use="목패 걸이 판(520,935) 3D. 최소 1m·최대 9m. 돌아오지 않은 목패 열넷")
def _(r):
    sec = 14.4; n = int(sec * SR)
    w, gg = _bed_wind(sec, r, 700, .8, .15, 3)
    tags = grains(sec, r, 80, lambda r, k: _wood_tap(r, r.uniform(1300, 1900), .015, r.uniform(.1, .35)))[:n] * (.3 + .7 * gg)
    rings = grains(sec, r, 10, lambda r, k: modal(.3, [(r.uniform(3200, 3800), .05, 1)], r) * .08)[:n]
    return loopify(reverb(w + tags + rings, .8, .2)[:n], .6)


@sfx("amb.shaft.timber", -24, "세계", "갱도 골 버팀목: 아치 버팀목이 산 무게를 견디며 낮게 끄응… 삐걱, 틈에서 흙이 사르르, 레일 이음매가 한 번 땡(반복용 16초)", loop=True, use="갱도 골 버팀목(640,1090)·갱 입구(560,980) 3D. 최소 1.5m·최대 10m. 엿듣기 R2-13·R2-15")
def _(r):
    sec = 16.4; n = int(sec * SR); b = filt(noise(n, r), "low", 220) * .08
    for at in (1.5, 6.8, 12.4): place(b, _creak(r, r.uniform(.9, 1.4), r.uniform(70, 95), 12, 350) * .45, at)
    for at in (4.0, 10.0): place(b, grains(.7, r, 25, lambda r, k: filt(noise(int(.01 * SR), r), "band", r.uniform(1500, 3500), 2) * env(int(.01 * SR), .001, .004) * .1), at)
    place(b, modal(1.0, [(r.uniform(620, 700), .35, 1), (r.uniform(1700, 1900), .15, .4)], r) * .15, 8.5)
    return loopify(reverb(b, 1.6, .4, 3000)[:n], .7)


# ── 2막 가끔 섞기 ──
@sfx("sfx.fv.jar.lid", -24, "세계", "술독 뚜껑을 여닫는 툭… 탁(0.6초)", use="FortressVillage 낮 가끔 30~70초")
def _(r):
    b = _buf(.8)
    place(b, modal(.4, [(280, .08, 1), (740, .04, .4)], r) * .6, 0); place(b, modal(.4, [(300, .07, 1), (790, .03, .4)], r) * .7, .32)
    return reverb(b, .6, .2)


@sfx("sfx.fv.rooster.near", -20, "세계", "가까운 닭 홰치기: 날개 푸드덕 + 꼬꼬댁(1.2초)", use="FortressVillage 낮 가끔 40~90초. 새벽엔 amb.rooster")
def _(r):
    b = _buf(1.4)
    m = int(.4 * SR); place(b, _flutter(.4, r, np.ones(m), rate=(18, 26), bright=1800)[:m] * .5, 0)
    for k, at in enumerate((.35, .55, .7, .9)): place(b, filt(_bird(r, 1100 - 60 * k, 1), "low", 3000) * .6, at)
    return reverb(b, .7, .2)


@sfx("sfx.fortress.stone", -21, "세계", "무너진 성벽에서 돌 하나가 굴러떨어짐: 덜컥 — 데굴데굴 — 툭(1.6초)", use="Fortress 가끔 40~100초")
def _(r):
    b = _buf(2.0)
    place(b, _stone_hit(r) * .6, 0)
    for k in range(6): place(b, _stone_hit(r) * (.35 - .04 * k), .25 + k * r.uniform(.12, .2))
    return reverb(b, 1.4, .35)


@sfx("sfx.fortress.count", -27, "세계", "해 진 성안에서 아주 멀리 무언가 수를 세는 듯한 낮은 웅얼거림 — 일정한 박자로 이어지다 뚝 끊김(3초). 말뜻은 안 들림", use="Fortress 밤 가끔 90~180초(드물게). 엿듣기 R2-05 '수 세는 소리'의 실체. 업 무관")
def _(r):
    b = _buf(3.6)
    for k in range(7):
        d = .28; m = int(d * SR); f0 = np.linspace(118 - k * .5, 108, m)
        place(b, voice(f0, [(480, 4, 1), (950, 5, .4)], .5, r, nh=10) * env(m, .03, .12, 3, hold=.1) * .6, .2 + k * .4)
    return reverb(filt(b, "low", 700), 2.2, .55)


@sfx("sfx.arrow.rattle", -24, "세계", "바위틈 녹슨 화살촉이 바람에 떨어져 돌틈을 짤그랑 굴러감(0.9초)", use="ArrowValley 가끔 30~70초")
def _(r):
    b = _buf(1.1)
    for k in range(5): place(b, modal(.2, [(r.uniform(2800, 4200), .03, 1), (r.uniform(6000, 7500), .015, .3)], r) * (.5 - .07 * k), k * r.uniform(.1, .17))
    return reverb(b, 1.0, .35)


@sfx("sfx.hawk.far", -24, "세계", "골짜기 위 매 한 마리 끼이— 하고 길게(1.2초, 멀리)", use="ArrowValley·Fortress 낮 가끔 60~120초")
def _(r):
    d = .9; f0 = curve(d, [(0, 2300), (.15, 2700), (d, 1900)])
    y = voice(f0, [(2600, 3, 1), (5000, 4, .3)], .3, r, nh=6) * env(int(d * SR), .05, .4, 3, hold=.3)
    return reverb(filt(y, "low", 4500), 1.8, .5)


@sfx("sfx.camp.pole", -23, "세계", "군막 터 기둥에 매달린 쇠고리가 바람에 기둥을 땅… 땅 두 번(1.4초)", use="Camp 가끔 30~70초")
def _(r):
    b = _buf(1.6)
    for at in (0, .55): place(b, _wood_tap(r, 380, .05, .5) + modal(.6, [(r.uniform(1300, 1500), .2, 1)], r)[:int(.25 * SR)] * .3, at)
    return reverb(b, 1.2, .35)


@sfx("sfx.tomb.cup", -25, "세계", "큰 무덤 술상 돌 위에 누가 잔을 놓은 듯 톡 — 아무도 없다(0.6초)", use="BigTomb 밤 가끔 80~160초(드물게)")
def _(r):
    return reverb(modal(.5, [(2250, .09, 1), (5300, .03, .3), (880, .05, .3)], r) * .7, 1.4, .4)


@sfx("sfx.mine.pick.far", -24, "세계", "먼 갱 안 곡괭이질 세 번 깡 깡 깡(울림 큼, 1.8초)", use="MinerTown·MainShaft 가끔 20~50초. 낮이 많고 밤엔 0.3배 확률")
def _(r):
    b = _buf(2.0)
    for k in range(3): place(b, _stone_hit(r) * (.8 - .1 * k), k * r.uniform(.6, .75))
    return reverb(filt(b, "low", 3000), 2.4, .6, 2500)


@sfx("sfx.mine.cart.far", -24, "세계", "레일 위 석탄 수레가 덜컹 덜컹 굴러갔다가 멈춤(3초, 멀리)", use="MinerTown·Sorting·MainShaft 가끔 40~90초")
def _(r):
    sec = 3.2; m = int(sec * SR); b = _buf(sec + .5)
    roll = filt(noise(m, r), "band", 260, 1.0) * env(m, .5, 1.0, 3, hold=1.2) * .5
    place(b, roll, 0)
    for k in range(6): place(b, modal(.2, [(r.uniform(900, 1100), .04, 1)], r) * .3, .3 + k * .42)
    return reverb(b, 1.8, .45, 3000)


@sfx("sfx.mine.gong", -22, "세계", "교대를 알리는 먼 징 두 번(광산 위에서, 3초)", use="MinerTown 새벽·저녁 한 번씩(교대 시각). 가끔 섞기 아님 — 시각에 맞춰")
def _(r):
    b = _buf(4.5)
    place(b, _jing(r, 170, 3.0, .1) * .7, 0); place(b, _jing(r, 170, 3.0, .1) * .6, 1.3)
    return reverb(filt(b, "low", 3000), 2.4, .5)


@sfx("sfx.mine.rockfall", -21, "세계", "멀리 갱 안에서 돌이 무너지는 우르르 — 짧고 낮게(1.6초)", use="MainShaft·Collapse 가끔 60~140초. B-07 전엔 조금 잦게")
def _(r):
    b = _buf(2.0)
    m = int(1.2 * SR); place(b, filt(noise(m, r), "low", 400) * env(m, .05, .5, 3) * .7, 0)
    place(b, grains(1.2, r, 30, lambda r, k: _stone_hit(r) * r.uniform(.05, .2)), .05)
    return reverb(b, 2.2, .55, 2000)


@sfx("sfx.sorting.basket", -23, "세계", "소쿠리 하나를 평상에 와르르 쏟음(0.9초)", use="Sorting 낮 가끔 15~40초")
def _(r):
    return reverb(grains(.9, r, 50, lambda r, k: modal(.08, [(r.uniform(1200, 3200), .02, 1)], r) * r.uniform(.05, .3)), .7, .2)


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
