#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bgm_temp_render.py — 아직 오너가 뽑지 않은 BGM 자리에 넣을 '임시 대역 음악'을 코드로 합성한다 (기획·사운드).

왜 필요한가
  2막(붉은재·쇳골)·3막(갯마을·도성)과 시즌1 끝 컷신 곡은 오너가 Gemini로 뽑을 예정인데, 그 전까지는
  해당 지역에 들어가면 음악이 뚝 끊긴다. 그래서 국악 장단(리듬 틀)과 드론(길게 깔리는 음)으로 짧은 반복곡을
  만들어 빈자리를 메운다. 진짜 곡이 아니므로 화려하지 않게, '자리를 지키는 소리' 정도로만 만든다.

바꿔 끼우는 규칙(이름 규칙)
  - 진짜 곡:  Resources/Audio/BGM/<id>.ogg        (예: bgm_soegol_day_a.ogg)
  - 임시 곡:  Resources/Audio/BGM/Temp/<id>.ogg   (같은 이름, Temp 폴더만 다름)
  - 게임은 진짜 곡을 먼저 찾고, 없을 때만 Temp를 쓴다. 그래서 오너 곡을 BGM 폴더에 넣기만 하면
    코드 수정 없이 바로 바뀐다. 임시 곡은 지우지 않아도 되고, 나중에 정리해도 된다.
  - id 모양: bgm_<지역>_<층>  지역 = bulgeunjae·soegol·gaetmaeul·doseong / 층 = day_a·night·combat·finish
    시즌1 끝 곡은 bgm_s1_heukwol·finale_a·finale_b·dawn·credits (cutscene_audio_s1.json 의 이름 그대로)

음량
  기존 진짜 곡과 똑같이 파일 음량을 맞춰 둔다(data/bgm.json 설명: 탐색 -20 LUFS, 전투·처결 -16 LUFS).
  LUFS(사람 귀 기준 평균 크기)는 ffmpeg 의 ebur128 측정으로 잰다.

같은 코드면 같은 소리
  난수 씨앗을 곡 이름에서 만들어(crc32) 몇 번을 다시 돌려도 같은 파일이 나온다.

쓰는 법
  python3 tools/bgm_temp_render.py            # 21곡 전부
  python3 tools/bgm_temp_render.py soegol     # 이름에 soegol 이 들어간 곡만
  --preview 폴더    # 미리듣기용 mp3 도 함께 만든다
"""
import os, sys, json, zlib, hashlib, subprocess, re, tempfile
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt, lfilter
from scipy.ndimage import maximum_filter1d

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "unity/Assets/Resources/Audio/BGM/Temp")


# =============================================================================
# 1) 기본 도구 — 음 높이, 필터(특정 높이의 소리만 남기는 체), 잡음
# =============================================================================
def mtof(m):
    """MIDI 음 번호(피아노 건반 번호 같은 것, 60=가운데 도)를 주파수(Hz)로 바꾼다"""
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _sos(kind, f):
    f = np.atleast_1d(f) / (SR / 2)
    f = np.clip(f, 1e-4, 0.999)
    return butter(2, f if len(f) > 1 else f[0], kind, output="sos")


def lp(x, f): return sosfilt(_sos("low", f), x)        # 낮은 소리만 통과(먹먹하게)
def hp(x, f): return sosfilt(_sos("high", f), x)       # 높은 소리만 통과(웅웅거림 제거)
def bp(x, lo, hi): return sosfilt(_sos("band", [lo, hi]), x)   # 가운데 띠만 통과


def T(sec): return np.arange(int(sec * SR)) / SR


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) if len(x) else 0
    return x * (peak / m) if m > 1e-9 else x


def edge(x, a=0.003, r=0.03):
    """앞뒤 끝을 아주 짧게 페이드 — 소리가 '딱' 하고 튀는 잡음(클릭)을 막는다"""
    n = len(x); a = min(int(a * SR), n // 2); r = min(int(r * SR), n // 2)
    if a: x[:a] *= np.linspace(0, 1, a)
    if r: x[-r:] *= np.linspace(1, 0, r)
    return x


# =============================================================================
# 2) 악기 — 진짜 녹음 없이 '그 악기다운 특징'만 흉내 낸다
# =============================================================================
def pluck(rng, midi, dur, kind="gayageum", vib=0.0, bend=0.0):
    """뜯는 현악기(가야금·거문고·양금).
    국악 현악기의 핵심은 '농현'(줄을 눌러 흔들어 음을 떨게 하거나 꺾는 것)이라 vib(떨림 깊이, 반음 단위)·
    bend(끝에서 미끄러지는 양)를 준다. 서양 기타처럼 음이 고정되면 국악처럼 안 들린다."""
    f = mtof(midi)
    n = int(dur * SR); t = np.arange(n) / SR
    semi = np.zeros(n)
    if vib:   # 뜯고 0.2초쯤 뒤부터 떨림이 깊어진다(왼손으로 줄을 누르기 시작)
        semi += vib * np.sin(2 * np.pi * 4.6 * t) * np.clip((t - 0.2) / 0.5, 0, 1)
    if bend:  # 끝부분에서 bend 반음만큼 밀어 올리거나 내린다(꺾는 소리)
        semi += bend * np.clip((t - dur * 0.45) / (dur * 0.25), 0, 1)
    ph = 2 * np.pi * np.cumsum(f * 2 ** (semi / 12)) / SR
    cfg = {"gayageum": (1.6, 0.55, 0.22, 12), "geomungo": (2.2, 0.35, 0.3, 9), "yanggeum": (1.1, 0.8, 0.12, 14)}[kind]
    decay, bright, pos, H = cfg
    out = np.zeros(n)
    for k in range(1, H + 1):
        if k * f > 9000: break
        amp = (1.0 / k ** (1.7 - bright)) * (abs(np.sin(np.pi * k * pos)) + 0.12)   # 뜯는 자리에 따라 빠지는 배음
        dk = decay / (1 + 0.55 * (k - 1) * (1.25 - bright))                         # 높은 배음일수록 빨리 사라짐
        out += amp * np.sin(k * ph + rng.uniform(0, 6.28)) * np.exp(-t / dk)
        if kind == "yanggeum":   # 양금은 한 음에 쇠줄 여러 가닥 → 살짝 어긋난 음을 겹쳐 '찰랑'
            out += 0.6 * amp * np.sin(k * ph * 1.0025 + rng.uniform(0, 6.28)) * np.exp(-t / dk)
    na = int(0.015 * SR)
    att = rng.standard_normal(na) * np.exp(-np.arange(na) / (0.003 * SR))
    if kind == "geomungo":   # 거문고는 술대(막대)로 내리쳐 '툭' 하는 나무 소리가 섞인다
        att = lp(att, 900) * 3.0
        tk = T(0.06); out[:len(tk)] += 0.5 * np.sin(2 * np.pi * 180 * tk) * np.exp(-tk / 0.012)
    else:
        att = bp(att, 1500, 6000) * 0.6
    out[:na] += att
    return edge(norm(out))


# 관악기·찰현악기(활로 긋는 현악기)의 배음 모양: 피리는 콧소리처럼 배음이 많고, 단소는 거의 순음
_WIND = {
    #          배음 크기                                  숨소리  떨림깊이 떨림속도 시작(초) 거칢
    "daegeum": ([1, .38, .22, .1, .06, .03],               0.22,  0.32,   4.4,    0.10,   0.0),
    "piri":    ([1, .85, .7, .55, .45, .35, .28, .2, .15], 0.08,  0.45,   5.2,    0.05,   0.25),
    "danso":   ([1, .16, .06, .03],                        0.26,  0.22,   4.8,    0.08,   0.0),
    "haegeum": ([1, .7, .5, .42, .33, .27, .2, .16, .12, .09], 0.05, 0.55, 5.6,  0.06,   0.35),
    "ajaeng":  ([1, .8, .62, .5, .4, .32, .26, .2, .16, .12, .09], 0.10, 0.6, 3.8, 0.12,   0.6),
    "nagak":   ([1, .55, .3, .16, .08],                    0.20,  0.08,   3.0,    0.45,   0.1),
}


def phrase(rng, notes, kind="daegeum"):
    """관악기·해금·아쟁 한 소절. notes = [(시작초, 길이초, midi, 꾸밈)].
    음과 음 사이를 미끄러지듯 잇고(국악의 '시김새'), 긴 음일수록 뒤에서 깊게 떤다(농음).
    꾸밈 'v' = 아주 깊게 떠는 음(계면조의 떠는 음), 'd' = 끝에서 아래로 꺾는 음."""
    harm, breath, vdep, vrate, att, rasp = _WIND[kind]
    end = max(t + d for t, d, m, o in notes) + 0.4
    n = int(end * SR); t = np.arange(n) / SR
    tgt = np.full(n, np.nan); amp = np.zeros(n); vib = np.zeros(n)
    for (t0, d, m, orn) in notes:
        i0, i1 = int(t0 * SR), min(n, int((t0 + d) * SR))
        if i1 <= i0: continue
        tt = np.arange(i1 - i0) / SR
        s = np.full(i1 - i0, float(m))
        if orn == "d": s -= 2.0 * np.clip((tt - d * 0.6) / (d * 0.25 + 1e-3), 0, 1)
        if orn == "u": s += 1.0 * np.clip(1 - tt / 0.12, 0, 1)            # 위에서 내려 꽂는 앞꾸밈
        tgt[i0:i1] = s
        a = np.clip(tt / att, 0, 1) * np.clip((d - tt) / 0.12, 0, 1)
        a *= 0.85 + 0.25 * np.clip(tt / max(d, 0.3), 0, 1)                # 긴 음은 뒤로 갈수록 살짝 부푼다
        amp[i0:i1] = np.maximum(amp[i0:i1], a)
        dv = vdep * (2.2 if orn == "v" else 1.0)
        vib[i0:i1] = dv * np.clip((tt - 0.3) / 0.5, 0, 1)
    # 음이 없는 틈은 앞 음 높이를 유지(그래야 다음 음으로 미끄러질 때 자연스럽다)
    idx = np.where(~np.isnan(tgt), np.arange(n), 0); np.maximum.accumulate(idx, out=idx)
    tgt = tgt[idx]; tgt[np.isnan(tgt)] = notes[0][2]
    a1 = np.exp(-1 / (0.045 * SR))
    semi = lfilter([1 - a1], [1, -a1], tgt, zi=[tgt[0] * a1])[0]          # 0.045초에 걸쳐 미끄러짐
    semi += vib * np.sin(2 * np.pi * vrate * t + rng.uniform(0, 6.28))
    semi += 0.04 * lp(rng.standard_normal(n), 3)                           # 사람 숨이라 아주 미세하게 흔들림
    f = mtof(semi)
    ph = 2 * np.pi * np.cumsum(f) / SR
    a2 = np.exp(-1 / (0.012 * SR)); env = lfilter([1 - a2], [1, -a2], amp)
    out = np.zeros(n)
    for k, h in enumerate(harm, 1):
        bright = np.clip(0.5 + 0.7 * env, 0, 1.2) ** (k * 0.35)          # 세게 불수록 밝아진다
        out += h * bright * np.sin(k * ph) * (f * k < 12000)
    out *= env
    if rasp:   # 활 긁힘·서(리드) 떨림: 진폭을 거칠게 흔든다
        out *= 1 + rasp * 0.35 * lp(rng.standard_normal(n), 80)
    br = bp(rng.standard_normal(n), 900, 5500) * env * breath * 0.6        # 숨소리
    out += br
    if kind == "daegeum":   # 대금의 '청'(갈대 막) 울림: 센 음에서 지글거리는 높은 소리
        out += bp(rng.standard_normal(n), 2500, 6000) * env ** 2 * 0.12
    if kind in ("haegeum", "piri"):
        out = np.tanh(out * 1.4) / 1.4                                     # 콧소리 같은 거친 맛
    if kind == "ajaeng":
        out = lp(out, 2200)
    return edge(norm(out))


def drone(rng, midis, sec, kind="saenghwang"):
    """길게 깔리는 음(드론). 생황(여러 관을 한꺼번에 부는 악기)이나 아쟁 저음처럼 숨 쉬듯 출렁인다"""
    n = int(sec * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for j, m in enumerate(midis):
        f = mtof(m)
        for det in (-0.12, 0.12):   # 두 관을 아주 살짝 어긋나게 → 느린 맥놀이(웅~웅~)
            ff = f * 2 ** (det / 100 * 12 / 12)
            ph = 2 * np.pi * ff * t + rng.uniform(0, 6.28)
            for k in range(1, 8):
                if ff * k > 6000: break
                out += (1 / k ** (1.3 if kind == "saenghwang" else 1.0)) * np.sin(k * ph) / (1 + 0.6 * j)
    if kind == "ajaeng":
        out *= 1 + 0.25 * lp(rng.standard_normal(n), 40)
        out = lp(out, 900)
    else:
        out = lp(out, 1800)
    out *= 0.75 + 0.25 * np.sin(2 * np.pi * t / max(sec, 1) * 1 + rng.uniform(0, 6.28))
    return norm(out)


# ---- 타악기 ----
def buk(rng, big=1.0):
    """북(절고·소리북): 낮게 '둥' — 처음엔 높다가 금방 내려앉는 음 + 가죽 잡음"""
    t = T(0.9 * big)
    f = 52 + 40 * np.exp(-t / 0.04)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.32 * big))
    s += lp(rng.standard_normal(len(t)), 400) * np.exp(-t / 0.05) * 0.5
    return edge(norm(s))


def janggu(rng, stroke):
    """장구. 덩=양쪽 함께, 쿵=왼쪽(궁편, 낮고 둥근), 덕=오른쪽(채편, 높고 딱), 기덕=채 꾸밈 두 번"""
    def kung():
        t = T(0.45); f = 95 + 50 * np.exp(-t / 0.03)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18) + lp(rng.standard_normal(len(t)), 300) * np.exp(-t / 0.03) * 0.3
    def deok():
        t = T(0.25)
        s = bp(rng.standard_normal(len(t)), 1800, 5000) * np.exp(-t / 0.018)
        s += 0.5 * np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.05)
        return s
    if stroke == "kung": s = kung()
    elif stroke == "deok": s = deok()
    elif stroke == "gi":   # 기덕: 짧은 꾸밈음 뒤 덕
        s = np.zeros(int(0.32 * SR)); g = deok() * 0.45; s[:len(g)] += g
        d = deok(); o = int(0.07 * SR); s[o:o + len(d)] += d[:len(s) - o]
    else:
        k = kung(); d = deok(); s = np.zeros(max(len(k), len(d))); s[:len(k)] += k; s[:len(d)] += d * 0.9
    return edge(norm(s))


def jing(rng, midi=45, sec=6.0):
    """징: 큰 놋쇠 징. 맞는 순간보다 조금 뒤에 '웅~' 하고 부풀며 음이 살짝 올라간다. 길게 운다"""
    t = T(sec); f0 = mtof(midi)
    out = np.zeros(len(t))
    for r, a, d in [(1, 1, 4.5), (1.47, .45, 2.5), (2.02, .35, 2.0), (2.68, .2, 1.2), (3.4, .12, .8), (4.2, .07, .5)]:
        ff = f0 * r * (1 + 0.012 * (1 - np.exp(-t / 0.6)))          # 음이 조금씩 올라감
        ph = 2 * np.pi * np.cumsum(ff) / SR + rng.uniform(0, 6.28)
        out += a * np.sin(ph) * np.exp(-t / d) * (1 + 0.25 * np.sin(2 * np.pi * (0.9 + r * 0.3) * t))
    swell = np.clip(t / 0.15, 0, 1) * (0.6 + 0.4 * np.clip(t / 0.5, 0, 1))
    out *= swell
    out += lp(rng.standard_normal(len(t)), 500) * np.exp(-t / 0.03) * 0.3   # 채의 '퍽'
    return edge(norm(out), 0.002, 0.3)


def kkwaeng(rng, damp=False):
    """꽹과리: 작은 쇠 징. 높고 날카롭게 '깽'. damp=True 면 손으로 막아 짧게 '갠'"""
    t = T(0.12 if damp else 0.6)
    out = np.zeros(len(t))
    for r, a in [(1, 1), (1.53, .7), (2.11, .5), (2.79, .4), (3.6, .25)]:
        out += a * np.sin(2 * np.pi * 1180 * r * t + rng.uniform(0, 6.28))
    out *= np.exp(-t / (0.03 if damp else 0.22))
    out += bp(rng.standard_normal(len(t)), 3000, 9000) * np.exp(-t / 0.01) * 0.4
    return edge(norm(out))


def bak(rng):
    """박: 나무 조각 여러 장을 한 번에 접어 치는 '딱!'. 곡의 시작과 끝을 알린다"""
    s = np.zeros(int(0.2 * SR))
    for o in (0, 0.004, 0.009):
        n = int(0.06 * SR); x = bp(rng.standard_normal(n), 900, 4200) * np.exp(-np.arange(n) / (0.008 * SR))
        i = int(o * SR); s[i:i + n] += x
    return edge(norm(s))


def bell(rng, midi=84, sec=3.0):
    """요령·풍경 같은 작은 종: 높은 쇳소리가 길게 남는다"""
    t = T(sec); f = mtof(midi); out = np.zeros(len(t))
    for r, a, d in [(1, 1, 1.6), (2.76, .5, .7), (5.4, .25, .3), (8.9, .12, .15)]:
        out += a * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6.28)) * np.exp(-t / d)
    return edge(norm(out), 0.001, 0.2)


# =============================================================================
# 3) 믹서 — 소리를 시간축에 놓고, 좌우 자리(팬)와 울림(리버브)을 준다. 반복곡이면 끝과 처음을 잇는다
# =============================================================================
class Mix:
    def __init__(self, sec, loop=True, tail=9.0):
        self.sec, self.loop = sec, loop
        self.n = int(sec * SR); m = self.n + int(tail * SR)
        self.d = np.zeros((2, m)); self.w = np.zeros((2, m))

    def add(self, sig, t, pan=0.0, gain=1.0, rev=0.3):
        i = max(0, int(t * SR))   # 박 흔들림(사람 손 맛)으로 0초보다 조금 앞서도 0에 놓는다
        if i >= self.d.shape[1] or gain <= 0: return
        s = sig[: self.d.shape[1] - i] * gain
        a = (np.clip(pan, -1, 1) + 1) * np.pi / 4     # 같은 크기로 들리게 좌우를 나누는 '등전력 팬'
        for c, g in ((0, np.cos(a)), (1, np.sin(a))):
            self.d[c, i:i + len(s)] += s * g * (1 - rev * 0.5)
            self.w[c, i:i + len(s)] += s * g * rev

    def render(self, rt=3.0, dark=3500):
        """울림을 입히고 반복 이음매를 처리한다.
        반복곡: 끝을 넘어간 소리(꼬리)를 맨 앞에 더해 넣는다 → 한 바퀴 돌아도 끊김 없이 이어짐"""
        rng = np.random.default_rng(7)
        n = int(rt * SR); t = np.arange(n) / SR
        out = self.d.copy()
        for c in range(2):
            ir = lp(rng.standard_normal(n), dark) * np.exp(-t * 6.9 / rt)   # 6.9 = 60dB 감쇠
            ir[: int(0.012 * SR)] = 0                                         # 첫 반사까지 12ms
            ir = ir / np.sqrt(np.sum(ir ** 2)) * 0.9
            out[c] += fftconvolve(self.w[c], ir)[: out.shape[1]]
        if self.loop:
            body = out[:, : self.n].copy(); tail = out[:, self.n:]
            k = min(tail.shape[1], self.n); body[:, :k] += tail[:, :k]
            return body
        return out


def circ(fn, x, loop, *a):
    """반복곡에 필터를 걸 때는 끝 1초를 앞에 붙여 걸고 떼어 낸다.
    그냥 걸면 필터가 '곡의 처음'을 새 출발로 여겨, 끝→처음 이음매에서 '틱' 소리가 난다"""
    if not loop: return fn(x, *a)
    k = min(SR, x.shape[1])
    y = fn(np.concatenate([x[:, -k:], x], axis=1), *a)
    return y[:, k:]


def limit(x, ceil=0.89):
    """갑자기 큰 소리가 0dB를 넘어 찌그러지지 않게 순간 음량을 눌러 준다(리미터)"""
    pk = np.max(np.abs(x), axis=0)
    g = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    g = -maximum_filter1d(-g, int(0.02 * SR))           # 20ms 앞뒤로 가장 많이 눌러야 하는 값
    a = np.exp(-1 / (0.05 * SR)); g = lfilter([1 - a], [1, -a], g, zi=[g[0] * a])[0]
    return x * np.minimum(g, 1.0)


def lufs(x):
    """ffmpeg 로 '사람 귀 기준 평균 크기(LUFS)'를 잰다"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: p = f.name
    write_wav(p, x)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    os.unlink(p)
    v = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(v[-1]) if v else -70.0


def write_wav(path, x):
    import wave
    y = (np.clip(x, -1, 1) * 32767).astype("<i2").T.copy()
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())


# =============================================================================
# 4) 장단(리듬 틀)과 선율 만들기
# =============================================================================
# 장단 = 한 바퀴를 몇 칸으로 나누고 어느 칸에 무엇을 치는지. sub = 한 박을 몇 칸으로 쪼개나
JANGDAN = {
    # 중모리: 12박 한 바퀴, 보통 빠르기. 이야기를 차분히 풀어 갈 때
    "jungmori":   dict(beats=12, sub=1, hits=[(0, "deong"), (2, "kung"), (4, "kung"), (5, "deok"), (6, "kung"), (8, "kung"), (9, "kung"), (10, "deok")]),
    # 중중모리: 4박×3칸. 어깨가 들썩이는 걸음
    "jungjung":   dict(beats=4, sub=3, hits=[(0, "deong"), (2, "deok"), (3, "kung"), (5, "deok"), (6, "kung"), (7, "deok"), (8, "kung"), (9, "kung"), (11, "deok")]),
    # 굿거리: 4박×3칸. 흥겹고 넉넉한 장터 느낌
    "gutgeori":   dict(beats=4, sub=3, hits=[(0, "deong"), (2, "gi"), (3, "kung"), (5, "deok"), (6, "kung"), (8, "deok"), (9, "kung"), (10, "gi")]),
    # 자진모리: 4박×3칸, 빠르게. 싸움·쫓김
    "jajinmori":  dict(beats=4, sub=3, hits=[(0, "deong"), (2, "deok"), (3, "kung"), (5, "deok"), (6, "kung"), (8, "deok"), (9, "kung"), (10, "deok")]),
    # 진양: 아주 느린 6박×4. 밤·슬픔. 거의 비어 있다
    "jinyang":    dict(beats=24, sub=1, hits=[(0, "deong"), (12, "kung"), (17, "deok"), (18, "kung"), (22, "deok")]),
}

PYEONG = [0, 2, 5, 7, 9]     # 평조: 밝고 담담(도 레 파 솔 라 모양)
GYEMYEON = [0, 3, 5, 7, 10]  # 계면조: 슬프고 애달픔(도 미♭ 파 솔 시♭ 모양). 5도는 떨고, 4도는 꺾는다


def scale_notes(tonic, mode, lo, hi):
    out = []
    for o in range(-3, 4):
        for s in mode:
            m = tonic + 12 * o + s
            if lo <= m <= hi: out.append(m)
    return out


def orn_for(m, tonic, mode, dur):
    """계면조 꾸밈: 5도(떠는 음)는 깊게 떨고, 4도(꺾는 음)는 긴 음일 때 끝을 아래로 꺾는다"""
    if mode is GYEMYEON:
        iv = (m - tonic) % 12
        if iv == 7 and dur > 0.6: return "v"
        if iv == 5 and dur > 0.8: return "d"
    return ""


def make_melody(rng, tonic, mode, lo, hi, cyc_sec, cycles, t0=0.0, cells=None, rest=0.25, var=0.35):
    """한 바퀴짜리 가락(motif)을 만들고, 바퀴마다 조금씩 바꿔 되풀이한다.
    국악 가락은 '같은 말을 조금씩 달리 되풀이'하는 맛이 있어서, 매번 새로 지어내는 것보다 이게 자연스럽다.
    cells = 한 바퀴를 나누는 길이 비율 목록(합 1). 끝음은 두 바퀴마다 으뜸음(tonic)으로 맺는다."""
    sc = scale_notes(tonic, mode, lo, hi)
    cells = cells or [0.25, 0.125, 0.125, 0.25, 0.25]
    # 시작은 가운데쯤
    home = min(range(len(sc)), key=lambda i: abs(sc[i] - (tonic + 12 if tonic + 12 <= hi else tonic)))
    idx = home; motif = []
    for c in cells:
        idx = int(np.clip(idx + rng.choice([-2, -1, -1, 0, 1, 1, 2]), 0, len(sc) - 1))
        motif.append(idx)
    notes = []
    for cy in range(cycles):
        t = t0 + cy * cyc_sec
        for j, (c, mi) in enumerate(zip(cells, motif)):
            d = c * cyc_sec
            if rng.random() < rest and j not in (0, len(cells) - 1):
                t += d; continue
            i = mi
            if rng.random() < var: i = int(np.clip(i + rng.choice([-1, 1]), 0, len(sc) - 1))
            if j == len(cells) - 1 and cy % 2 == 1:   # 두 바퀴째 끝: 으뜸음으로 맺음
                i = min(range(len(sc)), key=lambda q: abs(sc[q] - sc[i]) + (0 if (sc[q] - tonic) % 12 == 0 else 50))
            m = sc[i]
            notes.append((t, d * 0.94, m, orn_for(m, tonic, mode, d)))
            t += d
    return notes


def play_jangdan(mix, rng, name, bpm, t0, sec, pan=0.15, gain=0.6, rev=0.2, accent_first=1.0, skip=0.0):
    """장구 장단을 sec 초 동안 되풀이해 친다. 리턴 = 한 바퀴 길이(초)"""
    jd = JANGDAN[name]
    beat = 60.0 / bpm; subd = beat / jd["sub"]
    cyc = jd["beats"] * beat
    cache = {}
    k = 0
    while t0 + k * cyc < t0 + sec - 1e-6:
        for (s, st) in jd["hits"]:
            t = t0 + k * cyc + s * subd
            if t >= t0 + sec: break
            if s != 0 and rng.random() < skip: continue
            if st not in cache: cache[st] = [janggu(rng, st) for _ in range(3)]
            g = gain * (accent_first if s == 0 else 1.0) * rng.uniform(0.85, 1.05)
            mix.add(cache[st][rng.integers(3)], t + rng.normal(0, 0.004), pan, g, rev)
        k += 1
    return cyc


def lay_drone(mix, rng, midis, sec, kind="saenghwang", gain=0.25, pan=0.0, rev=0.4, win=12.0):
    """드론을 반복 이음매 없이 깔기: 12초짜리 조각을 반씩 겹쳐(한 조각이 사라질 때 다음이 커짐) 이어 붙인다"""
    hop = sec / max(1, round(sec / (win / 2))); w = hop * 2
    blk = drone(rng, midis, w, kind)
    hann = np.sin(np.pi * np.arange(len(blk)) / len(blk)) ** 2
    # 반복곡: 첫 조각은 앞쪽 반이 비어 있지만, 마지막 조각의 꼬리가 맨 앞에 더해져(Mix.render) 크기가 일정해진다
    # 1회곡: 앞쪽 반 조각만큼 서서히 커지며 시작한다(자연스러운 페이드 인)
    k = 0
    while k * hop < sec - 1e-6:
        mix.add(blk * hann, k * hop, pan, gain, rev)
        k += 1


# =============================================================================
# 5) 지역별 설정 (Gemini 지시문 5~20번의 빠르기·음·악기를 그대로 따른다)
# =============================================================================
REGIONS = {
    #             으뜸음 MIDI  빠르기  조          주 가락     받침 현      낮 장단      특이 악기
    "bulgeunjae": dict(tonic=55, bpm=66, mode=GYEMYEON, lead="piri",    pl="geomungo", day="jungmori",  extra="nagak",  name="붉은재 싸움터"),
    "soegol":     dict(tonic=48, bpm=80, mode=GYEMYEON, lead="haegeum", pl="geomungo", day="jungjung",  extra="kkwaeng", name="쇳골 광산"),
    "gaetmaeul":  dict(tonic=57, bpm=70, mode=GYEMYEON, lead="piri",    pl="geomungo", day="jungmori",  extra="jing",   name="갯마을 포구", lead2="haegeum"),
    "doseong":    dict(tonic=53, bpm=92, mode=PYEONG,   lead="danso",   pl="yanggeum", day="gutgeori",  extra="bak",    name="도성 아랫마을"),
}


def fit(sec, cyc):
    """곡 길이를 장단 한 바퀴의 정수배로 맞춘다(그래야 반복 이음매에서 박자가 안 어긋남)"""
    return max(1, round(sec / cyc)) * cyc


def song_day(rng, R):
    jd = JANGDAN[R["day"]]; cyc = jd["beats"] * 60 / R["bpm"]
    sec = fit(80, cyc); cycles = int(round(sec / cyc))
    mx = Mix(sec)
    tn, md = R["tonic"], R["mode"]
    lay_drone(mx, rng, [tn - 12, tn - 5], sec, gain=0.16)
    play_jangdan(mx, rng, R["day"], R["bpm"], 0, sec, gain=0.42, skip=0.12)
    # 받침 현: 바퀴 첫 박에 으뜸음, 중간에 5도 — 걸음의 바닥을 잡아 준다
    for k in range(cycles):
        t = k * cyc
        mx.add(pluck(rng, tn - 12, 2.6, R["pl"], vib=0.25), t, -0.3, 0.42, 0.3)
        mx.add(pluck(rng, tn - 5, 1.8, R["pl"], vib=0.2), t + cyc * 0.5, -0.25, 0.3, 0.3)
        if R["pl"] == "yanggeum":   # 양금은 잘게 펼쳐 치는 맛(아르페지오)
            sc = scale_notes(tn, md, tn + 7, tn + 24)
            for j in range(6):
                mx.add(pluck(rng, sc[(k * 2 + j * 2) % len(sc)], 0.9, "yanggeum"), t + cyc * (0.08 + j * 0.14), 0.35, 0.16, 0.35)
    # 가락: 첫 두 바퀴는 비워 두고(들어가기 전 숨), 나머지에서 되풀이
    lead_lo, lead_hi = (tn, tn + 19) if R["lead"] != "haegeum" else (tn + 7, tn + 24)
    mel = make_melody(rng, tn, md, lead_lo, lead_hi, cyc, cycles - 2, t0=cyc * 2, rest=0.3)
    # 숨 쉬는 자리: 네 바퀴마다 한 바퀴씩 쉰다
    mel = [m for m in mel if int((m[0] - cyc * 2) / cyc) % 4 != 3]
    mx.add(phrase(rng, mel, R["lead"]), 0, 0.12, 0.5, 0.35)
    if R.get("lead2"):   # 갯마을: 해금이 쉬는 바퀴에 대답
        ans = make_melody(rng, tn, md, tn + 7, tn + 24, cyc, cycles, rest=0.45)
        ans = [m for m in ans if int(m[0] / cyc) % 4 == 1 and m[0] >= cyc * 2]
        if ans: mx.add(phrase(rng, ans, R["lead2"]), 0, -0.2, 0.36, 0.4)
    return mx, -20.0


def song_night(rng, R):
    beat = 60 / (R["bpm"] * 0.75); cyc = 24 * beat   # 밤은 진양처럼 아주 느리게
    sec = fit(90, cyc); cycles = int(round(sec / cyc))
    mx = Mix(sec)
    tn, md = R["tonic"], R["mode"]
    lay_drone(mx, rng, [tn - 12, tn - 5], sec, "ajaeng", gain=0.2, rev=0.5)
    play_jangdan(mx, rng, "jinyang", R["bpm"] * 0.75, 0, sec, gain=0.22, rev=0.4, skip=0.3)
    for k in range(cycles):
        t = k * cyc
        mx.add(pluck(rng, tn - 12, 3.5, "geomungo" if R["pl"] != "yanggeum" else "gayageum", vib=0.35), t, -0.3, 0.38, 0.45)
        # 드문드문 한 음씩, 대답 없는 물음처럼
        sc = scale_notes(tn, md, tn, tn + 14)
        for j in range(2):
            m = sc[rng.integers(len(sc))]
            mx.add(pluck(rng, m, 2.8, "gayageum", vib=0.3, bend=(-1.0 if rng.random() < 0.3 else 0)), t + cyc * rng.uniform(0.25, 0.85), 0.3, 0.26, 0.5)
    # 긴 숨 가락은 두 바퀴에 한 번만
    mel = make_melody(rng, tn, md, tn - 2, tn + 14, cyc, cycles, cells=[0.3, 0.2, 0.3, 0.2], rest=0.35)
    mel = [m for m in mel if int(m[0] / cyc) % 2 == 1]
    lead = "daegeum" if R["lead"] != "haegeum" else "haegeum"
    if mel: mx.add(phrase(rng, mel, lead), 0, 0.15, 0.4, 0.5)
    if R["extra"] == "nagak":   # 붉은재: 멀리서 나각(소라 나팔) — 오래전 싸움의 부름
        for k in range(0, cycles, 2):
            mx.add(phrase(rng, [(0, 3.2, tn - 12, ""), (3.4, 2.0, tn - 5, "")], "nagak"), k * cyc + cyc * 0.55, -0.6, 0.22, 0.7)
    if R["extra"] == "jing":
        for k in range(cycles): mx.add(jing(rng, tn - 24 + 12), k * cyc + cyc * 0.5, 0.0, 0.25, 0.55)
    if R["extra"] == "kkwaeng":   # 쇳골 밤: 꽹과리 대신 멀리서 쇠 두드리는 한 번
        for k in range(cycles): mx.add(kkwaeng(rng, True), k * cyc + cyc * 0.7, 0.5, 0.08, 0.8)
    return mx, -20.0


def song_combat(rng, R):
    bpm = R.get("combat_bpm") or {"bulgeunjae": 108, "soegol": 120, "gaetmaeul": 112, "doseong": 132}[next(k for k, v in REGIONS.items() if v is R)]
    cyc = 4 * 60 / bpm
    sec = fit(44, cyc); cycles = int(round(sec / cyc))
    mx = Mix(sec)
    tn, md = R["tonic"], R["mode"]
    lay_drone(mx, rng, [tn - 12, tn - 5], sec, "ajaeng", gain=0.16, rev=0.3)
    play_jangdan(mx, rng, "jajinmori", bpm, 0, sec, gain=0.55, rev=0.15, accent_first=1.2)
    b = [buk(rng, 1.2) for _ in range(2)]
    for k in range(cycles):
        t = k * cyc
        mx.add(b[k % 2], t, 0.0, 0.8, 0.15)
        if k % 2 == 1: mx.add(b[0], t + cyc * 0.75, 0.0, 0.5, 0.15)
        mx.add(pluck(rng, tn - 12, 1.2, "geomungo"), t, -0.3, 0.42, 0.2)
        if R["extra"] == "kkwaeng":   # 쇳골: 꽹과리가 앞에서 몰아친다
            for s in range(12):
                if s in (0, 3, 6, 9) or rng.random() < 0.35:
                    mx.add(kkwaeng(rng, s % 3 != 0), t + s * cyc / 12, 0.35, 0.22 if s % 3 == 0 else 0.13, 0.2)
        if R["extra"] == "jing" and k % 4 == 0: mx.add(jing(rng, tn - 12), t, 0.0, 0.35, 0.3)
        if R["extra"] == "nagak" and k % 8 == 4:
            mx.add(phrase(rng, [(0, 1.6, tn - 12, ""), (1.7, 1.4, tn - 5, "")], "nagak"), t, -0.5, 0.25, 0.4)
        if R["extra"] == "bak" and k % 8 == 0: mx.add(bak(rng), t, 0.2, 0.4, 0.3)
    lead = R["lead"] if R["lead"] != "danso" else "piri"
    mel = make_melody(rng, tn, md, tn + 5, tn + 22, cyc, cycles - 1, t0=cyc, cells=[1 / 6, 1 / 6, 1 / 6, 1 / 4, 1 / 4], rest=0.2)
    mel = [m for m in mel if int(m[0] / cyc) % 4 != 0]
    mx.add(phrase(rng, mel, lead), 0, 0.15, 0.45, 0.25)
    return mx, -16.0


def song_finish(rng, R):
    """처결: 적이 무릎 꿇는 순간 1회. 6.9초(BgmDirector.FinishClipSec)에 맞춰 울리고 사라진다"""
    mx = Mix(6.9, loop=False, tail=0.1)
    tn = R["tonic"]
    mx.add(jing(rng, tn - 12, 6.8), 0.0, 0.0, 0.7, 0.45)
    mx.add(buk(rng, 1.4), 0.0, 0.0, 0.5, 0.3)
    mx.add(pluck(rng, tn, 5.0, "geomungo" if R["pl"] != "yanggeum" else "gayageum", vib=0.4, bend=-1.0), 0.5, -0.3, 0.35, 0.5)
    mx.add(phrase(rng, [(1.0, 3.6, tn + 7, "v"), (4.7, 1.8, tn + 12 if R["mode"] is PYEONG else tn + 5, "d")], "daegeum"), 0, 0.2, 0.3, 0.6)
    return mx, -16.0


# ---- 보스전 곡(2026-10-26, 기획·사운드) ----
# 왜: 보스 맺힘이 커져 싸움이 3~5분인데 지역 전투 곡(44초)만 쓰면 5~7번 되풀이돼 귀에 걸린다.
#     1단계는 긴 곡 하나가 "조용히 시작 → 차오름 → 절정 → 한 번 숨 → 다시 몰아침" 흐름을 만들고,
#     2단계(맺힘 50% 아래)는 처음부터 끝까지 거센 곡으로 바꾼다(BgmPlayer 쪽 규칙은 data/bgm.json layers.boss).
def _boss_bpm(R):
    return R.get("combat_bpm") or {"bulgeunjae": 108, "soegol": 120, "gaetmaeul": 112, "doseong": 132}[next(k for k, v in REGIONS.items() if v is R)]


def _boss_extra(mx, rng, R, t, cyc, k, hot):
    """지역마다 다른 특이 악기(전투 곡과 같은 규칙). hot=True 면 더 자주"""
    tn = R["tonic"]
    if R["extra"] == "kkwaeng":
        for s in range(12):
            if s in (0, 3, 6, 9) or rng.random() < (0.5 if hot else 0.25):
                mx.add(kkwaeng(rng, s % 3 != 0), t + s * cyc / 12, 0.35, 0.22 if s % 3 == 0 else 0.13, 0.2)
    if R["extra"] == "jing" and k % (2 if hot else 4) == 0: mx.add(jing(rng, tn - 12), t, 0.0, 0.35, 0.3)
    if R["extra"] == "nagak" and k % (4 if hot else 8) == 2:
        mx.add(phrase(rng, [(0, 1.6, tn - 12, ""), (1.7, 1.4, tn - 5, "")], "nagak"), t, -0.5, 0.25, 0.4)
    if R["extra"] == "bak" and k % (4 if hot else 8) == 0: mx.add(bak(rng), t, 0.2, 0.4, 0.3)


def song_boss(rng, R):
    """보스 1단계: 약 150초 반복. 구간(장단 바퀴 수 비율) = 시작 1 · 차오름 3 · 절정 4 · 숨 1 · 몰아침 3"""
    bpm = _boss_bpm(R) - 4                      # 필드 전투보다 조금 무겁게(느리게)
    cyc = 4 * 60 / bpm
    cycles = int(round(fit(150, cyc) / cyc)); sec = cycles * cyc
    unit = cycles / 12.0
    cut = [round(unit * a) for a in (1, 4, 8, 9)]   # 구간 경계(바퀴 번호)
    mx = Mix(sec)
    tn, md = R["tonic"], R["mode"]
    lay_drone(mx, rng, [tn - 24, tn - 12, tn - 5], sec, "ajaeng", gain=0.18, rev=0.35)
    b = [buk(rng, 1.4) for _ in range(2)]
    lead = R["lead"] if R["lead"] != "danso" else "piri"
    for k in range(cycles):
        t = k * cyc
        sect = sum(k >= c for c in cut)         # 0 시작 · 1 차오름 · 2 절정 · 3 숨 · 4 몰아침
        if sect == 0:
            if k % 1 == 0: mx.add(b[0], t, 0.0, 0.55, 0.3)
            continue
        if sect == 3:                           # 숨: 북과 아쟁만 남긴다
            mx.add(b[0], t, 0.0, 0.7, 0.25); mx.add(b[1], t + cyc * 0.5, 0.0, 0.45, 0.25)
            continue
        hot = sect in (2, 4)
        play_jangdan(mx, rng, "jajinmori", bpm, t, cyc, gain=0.4 + 0.1 * (sect >= 2) + 0.05 * (sect == 4), rev=0.15, accent_first=1.2)
        mx.add(b[k % 2], t, 0.0, 0.8, 0.15)
        if hot or k % 2: mx.add(b[0], t + cyc * 0.75, 0.0, 0.5, 0.15)
        if sect == 4: mx.add(b[1], t + cyc * 0.5, 0.0, 0.55, 0.15)
        mx.add(pluck(rng, tn - 12, 1.2, "geomungo"), t, -0.3, 0.42, 0.2)
        if sect >= 2: _boss_extra(mx, rng, R, t, cyc, k, hot)
        if k % 4 == 0 and sect >= 2: mx.add(jing(rng, tn - 12, 4.0), t, 0.0, 0.3, 0.35)
    # 가락: 차오름은 낮게, 절정·몰아침은 높게
    m1 = make_melody(rng, tn, md, tn - 2, tn + 12, cyc, cut[1] - cut[0], t0=cut[0] * cyc, cells=[0.25] * 4, rest=0.3)
    m2 = make_melody(rng, tn, md, tn + 5, tn + 22, cyc, cut[2] - cut[1], t0=cut[1] * cyc, cells=[1 / 6, 1 / 6, 1 / 6, 1 / 4, 1 / 4], rest=0.2)
    m3 = make_melody(rng, tn, md, tn + 7, tn + 24, cyc, cycles - cut[3], t0=cut[3] * cyc, cells=[1 / 6] * 3 + [1 / 4, 1 / 4], rest=0.15)
    mx.add(phrase(rng, m1, "haegeum" if lead != "haegeum" else "daegeum"), 0, -0.15, 0.4, 0.3)
    mx.add(phrase(rng, m2, lead), 0, 0.15, 0.45, 0.25)
    mx.add(phrase(rng, m3, lead), 0, 0.15, 0.48, 0.25)
    return mx, -16.0


def song_boss_p2(rng, R):
    """보스 2단계: 약 90초 반복. 처음부터 거세게, 앞뒤 절반 가락을 달리해 되풀이가 덜 들리게"""
    bpm = _boss_bpm(R) + 6
    cyc = 4 * 60 / bpm
    cycles = int(round(fit(90, cyc) / cyc)); sec = cycles * cyc
    mx = Mix(sec)
    tn, md = R["tonic"], R["mode"]
    lay_drone(mx, rng, [tn - 24, tn - 12, tn - 5], sec, "ajaeng", gain=0.22, rev=0.3)
    play_jangdan(mx, rng, "jajinmori", bpm, 0, sec, gain=0.58, rev=0.15, accent_first=1.3)
    b = [buk(rng, 1.5) for _ in range(2)]
    for k in range(cycles):
        t = k * cyc
        for q in range(2): mx.add(b[(k + q) % 2], t + q * cyc / 2, 0.0, 0.85 - 0.25 * q, 0.15)
        mx.add(pluck(rng, tn - 12, 1.0, "geomungo"), t, -0.3, 0.45, 0.2)
        _boss_extra(mx, rng, R, t, cyc, k, True)
        if k % 4 == 0: mx.add(jing(rng, tn - 12, 4.0), t, 0.0, 0.36, 0.35)
    lead = R["lead"] if R["lead"] != "danso" else "piri"
    h = cycles // 2
    ma = make_melody(rng, tn, md, tn + 5, tn + 22, cyc, h, t0=0, cells=[1 / 6] * 3 + [1 / 4, 1 / 4], rest=0.15)
    mb = make_melody(rng, tn, md, tn + 9, tn + 26, cyc, cycles - h, t0=h * cyc, cells=[1 / 6] * 6, rest=0.12)
    mx.add(phrase(rng, ma, lead), 0, 0.15, 0.5, 0.25)
    mx.add(phrase(rng, mb, "ajaeng"), 0, -0.15, 0.45, 0.3)
    return mx, -16.0


# ---- 시즌1 끝 컷신 곡(지시문 21~25) ----
def s1_heukwol(rng):
    """흑월 결전: 느린 진양에서 점점 빨라짐(60→100). 큰 북이 끌고, 아쟁이 울고, 징 세 번마다 거세진다. D음"""
    tn = 50; md = GYEMYEON
    stages = [(60, 4), (72, 4), (86, 4), (100, 6)]   # (빠르기, 바퀴 수) — 자진모리 4박
    total = sum(4 * 60 / b * c for b, c in stages)
    mx = Mix(total + 5, loop=False, tail=6)
    lay_drone(mx, rng, [tn - 12, tn - 5], total + 4, "ajaeng", gain=0.2, rev=0.35)
    t = 0.0; stage = 0
    b = buk(rng, 1.5)
    for bpm, cyc_n in stages:
        cyc = 4 * 60 / bpm
        for j in range(3):   # 단계가 바뀔 때마다 징 세 번
            mx.add(jing(rng, tn - 12, 4.0), t + j * (cyc / 3 if stage else cyc / 2), 0.0, 0.32, 0.45)
        play_jangdan(mx, rng, "jajinmori" if stage else "jinyang", bpm if stage else bpm * 2.5, t, cyc * cyc_n, gain=0.35 + 0.08 * stage, rev=0.2)
        for k in range(cyc_n):
            for q in range(1 + stage):
                mx.add(b, t + k * cyc + q * cyc / (1 + stage), 0.0, 0.75, 0.25)
        mel = make_melody(rng, tn, md, tn - 2, tn + 15, cyc, cyc_n, t0=t, cells=[0.25, 0.25, 0.25, 0.25] if stage < 2 else [1 / 6] * 3 + [0.25, 0.25], rest=0.2)
        mx.add(phrase(rng, mel, "ajaeng"), 0, -0.1, 0.45 + 0.05 * stage, 0.35)
        if stage in (1, 3):
            mx.add(phrase(rng, [(t + cyc * 1.5, cyc * 1.8, tn + 19, "v")], "daegeum"), 0, 0.3, 0.3, 0.6)
        t += cyc * cyc_n; stage += 1
    mx.add(jing(rng, tn - 12, 5.0), t, 0, 0.6, 0.5); mx.add(b, t, 0, 0.9, 0.3)
    return mx, -16.0


def s1_heukwol_fight(rng):
    """B-12 흑월 2차 1·2단계(싸움 6~8분 중 앞 4분쯤): 100 빠르기 자진모리로 고정한 약 180초 반복.
    왜: bgm_s1_heukwol(66초)은 60→100으로 빨라지다 끝에서 닫히는 1회용이라, 반복하면 66초마다 끊기고 느린 처음으로 돌아간다"""
    tn = 50; md = GYEMYEON; bpm = 100
    cyc = 4 * 60 / bpm; cycles = int(round(fit(180, cyc) / cyc)); sec = cycles * cyc
    mx = Mix(sec)
    lay_drone(mx, rng, [tn - 24, tn - 12, tn - 5], sec, "ajaeng", gain=0.2, rev=0.35)
    b = buk(rng, 1.5)
    q4 = cycles // 4
    for k in range(cycles):
        t = k * cyc; sect = min(3, k // q4)     # 4구간: 누름 · 밀어붙임 · 숨(북만) · 다시 몰아침
        if sect == 2 and k < 2 * q4 + q4 // 2:
            mx.add(b, t, 0.0, 0.8, 0.25); mx.add(b, t + cyc / 2, 0.0, 0.5, 0.25); continue
        play_jangdan(mx, rng, "jajinmori", bpm, t, cyc, gain=0.45 + 0.06 * (sect != 0), rev=0.18, accent_first=1.2)
        for q in range(1 + (sect != 0)): mx.add(b, t + q * cyc / (1 + (sect != 0)), 0.0, 0.8, 0.25)
        if k % 4 == 0: mx.add(jing(rng, tn - 12, 4.0), t, 0.0, 0.34, 0.45)
    for s0, s1, lo, hi, ins in ((0, q4, tn - 2, tn + 12, "ajaeng"), (q4, 2 * q4, tn + 3, tn + 17, "ajaeng"),
                                (2 * q4 + q4 // 2, cycles, tn + 5, tn + 19, "ajaeng")):
        mel = make_melody(rng, tn, md, lo, hi, cyc, s1 - s0, t0=s0 * cyc, cells=[0.25] * 4 if s0 == 0 else [1 / 6] * 3 + [0.25, 0.25], rest=0.2)
        mx.add(phrase(rng, mel, ins), 0, -0.1, 0.48, 0.35)
    for k in range(q4, cycles, 6):
        mx.add(phrase(rng, [(k * cyc + cyc * 1.5, cyc * 1.8, tn + 19, "v")], "daegeum"), 0, 0.3, 0.3, 0.6)
    return mx, -16.0


def s1_heukwol_flood(rng):
    """B-12 흑월 2차 3단계(큰물): 약 120초 반복. 더 낮고 무겁게, 큰 북을 셋잇단으로 몰고 징을 자주. 물이 차오르는 느낌은 저음 드론을 넓게"""
    tn = 50; md = GYEMYEON; bpm = 108
    cyc = 4 * 60 / bpm; cycles = int(round(fit(120, cyc) / cyc)); sec = cycles * cyc
    mx = Mix(sec)
    lay_drone(mx, rng, [tn - 24, tn - 17, tn - 12], sec, "ajaeng", gain=0.26, rev=0.45)
    play_jangdan(mx, rng, "jajinmori", bpm, 0, sec, gain=0.55, rev=0.2, accent_first=1.3)
    b = buk(rng, 1.7)
    for k in range(cycles):
        t = k * cyc
        for q in range(3): mx.add(b, t + q * cyc / 3, 0.0, 0.9 - 0.2 * q, 0.25)
        if k % 2 == 0: mx.add(jing(rng, tn - 12, 4.5), t, 0.0, 0.4, 0.45)
    h = cycles // 2
    ma = make_melody(rng, tn, md, tn - 5, tn + 12, cyc, h, cells=[1 / 6] * 3 + [0.25, 0.25], rest=0.15)
    mb = make_melody(rng, tn, md, tn + 2, tn + 17, cyc, cycles - h, t0=h * cyc, cells=[1 / 6] * 6, rest=0.12)
    mx.add(phrase(rng, ma, "ajaeng"), 0, -0.1, 0.5, 0.35)
    mx.add(phrase(rng, mb, "ajaeng"), 0, -0.1, 0.5, 0.35)
    mx.add(phrase(rng, [(n[0], n[1], n[2] + 12, n[3]) for n in mb[::3]], "piri"), 0, 0.3, 0.3, 0.4)
    return mx, -16.0


def s1_finale_a(rng):
    """A판 큰물 밤의 기억: 장단 없이. 30초 해금 혼자 같은 가락 되풀이 → 거문고·피리 → 1분쯤 뚝 멈춤 → 대금 한 음"""
    tn = 50; md = GYEMYEON
    mx = Mix(118, loop=False, tail=8)
    motif = [(0, 1.6, tn + 7, "v"), (1.7, 0.9, tn + 5, "d"), (2.7, 1.2, tn + 3, ""), (4.0, 2.4, tn, "")]
    hg = []
    for r in range(10):   # 건지러 다시 들어가는 걸음처럼 같은 가락을 거듭
        o = r * 7.0
        for (a, d, m, orn) in motif:
            hg.append((o + a, d, m + (0 if r % 3 else 0), orn))
    mx.add(phrase(rng, [n for n in hg if n[0] < 60], "haegeum"), 0, -0.1, 0.5, 0.45)
    lay_drone(mx, rng, [tn - 12], 30, "ajaeng", gain=0.12, rev=0.5)
    for k in range(5):   # 30초부터 거문고가 무겁게
        mx.add(pluck(rng, tn - 12 if k % 2 == 0 else tn - 5, 5.0, "geomungo", vib=0.4), 30 + k * 6.0, -0.35, 0.45, 0.45)
    pr = make_melody(rng, tn, md, tn + 12, tn + 24, 7.0, 4, t0=31.0, cells=[0.3, 0.2, 0.25, 0.25], rest=0.25)
    mx.add(phrase(rng, [n for n in pr if n[0] + n[1] < 60], "piri"), 0, 0.3, 0.35, 0.5)
    # 60초: 모든 소리가 뚝 → 3초 비움 → 대금 한 음만 길게
    mx.d[:, int(60.4 * SR): int(63.5 * SR)] *= 0.0; mx.w[:, int(60.4 * SR): int(63.5 * SR)] *= 0.0
    mx.add(phrase(rng, [(0, 9.0, tn + 12, "v")], "daegeum"), 63.5, 0.0, 0.5, 0.6)
    mx.add(drone(rng, [tn - 12, tn - 5], 45), 73, 0.0, 0.18, 0.5)
    tail = make_melody(rng, tn, md, tn, tn + 14, 8.0, 5, t0=74, cells=[0.4, 0.3, 0.3], rest=0.2)
    mx.add(phrase(rng, tail, "haegeum"), 0, -0.15, 0.4, 0.5)
    for k in range(5): mx.add(pluck(rng, tn - 12, 5.0, "geomungo", vib=0.3), 74 + k * 8, -0.3, 0.35, 0.5)
    return mx, -20.0


def s1_finale_b(rng):
    """B판 빈 눈밭: 아쟁 한 음을 오래, 가야금이 드문드문, 끝까지 맺지 않는다. D음"""
    tn = 50; md = GYEMYEON
    mx = Mix(88, loop=False, tail=8)
    mx.add(phrase(rng, [(1.0, 40, tn - 12, ""), (42.0, 38, tn - 12, "")], "ajaeng"), 0, -0.1, 0.35, 0.5)
    sc = scale_notes(tn, md, tn, tn + 15)
    t = 4.0
    while t < 80:
        mx.add(pluck(rng, sc[rng.integers(len(sc))], 4.0, "gayageum", vib=0.35, bend=(-1 if rng.random() < 0.25 else 0)), t, rng.uniform(-0.4, 0.5), 0.35, 0.6)
        t += rng.uniform(4.5, 8.0)
    mx.add(pluck(rng, tn + 5, 6.0, "gayageum", vib=0.5), 81.0, 0.2, 0.32, 0.65)   # 마지막은 4도에서 멈춤(맺지 않음)
    return mx, -20.0


def s1_dawn(rng):
    """마지막 새벽: 대금이 여리게, 가야금이 이슬처럼. 중간에 한 번 잦아들었다 다시. A음 평조"""
    tn = 57; md = PYEONG
    mx = Mix(92, loop=False, tail=9)
    lay_drone(mx, rng, [tn - 12, tn - 5], 86, gain=0.12, rev=0.5)
    m1 = make_melody(rng, tn, md, tn, tn + 14, 8.0, 5, t0=2.0, cells=[0.35, 0.15, 0.25, 0.25], rest=0.2)
    m2 = make_melody(rng, tn, md, tn, tn + 14, 8.0, 4, t0=50.0, cells=[0.35, 0.15, 0.25, 0.25], rest=0.25)
    mx.add(phrase(rng, m1, "daegeum"), 0, 0.1, 0.42, 0.55)
    mx.add(phrase(rng, m2, "daegeum"), 0, 0.1, 0.38, 0.55)
    sc = scale_notes(tn, md, tn + 7, tn + 24)
    t = 6.0
    while t < 84:
        if not (42 < t < 50):   # 바람이 지나가듯 잦아드는 자리
            mx.add(pluck(rng, sc[rng.integers(len(sc))], 3.0, "gayageum", vib=0.2), t, rng.uniform(-0.5, 0.5), 0.26, 0.6)
        t += rng.uniform(2.5, 5.0)
    mx.add(pluck(rng, tn, 8.0, "gayageum", vib=0.3), 84.0, 0.0, 0.32, 0.7)
    return mx, -20.0


def s1_credits(rng):
    """끝 글씨·크레딧: 느린 중모리(70) 장구, 해금·대금이 주고받음, 가운데 거문고 깊게 한 번, 끝에 요령. G음"""
    tn = 55; md = PYEONG; bpm = 70
    cyc = 12 * 60 / bpm
    cycles = 12; sec = cyc * cycles
    mx = Mix(sec + 6, loop=False, tail=8)
    lay_drone(mx, rng, [tn - 12, tn - 5], sec + 4, gain=0.12, rev=0.45)
    play_jangdan(mx, rng, "jungmori", bpm, cyc, sec - cyc, gain=0.3, rev=0.3, skip=0.15)
    for k in range(cycles):
        lead = "haegeum" if k % 2 == 0 else "daegeum"
        lo, hi = (tn + 7, tn + 22) if lead == "haegeum" else (tn, tn + 17)
        m = make_melody(rng, tn, md, lo, hi, cyc, 1, t0=k * cyc, rest=0.25)
        if k >= 1: mx.add(phrase(rng, m, lead), 0, -0.2 if lead == "haegeum" else 0.2, 0.42, 0.45)
        mx.add(pluck(rng, tn - 12, 2.5, "gayageum", vib=0.2), k * cyc, -0.3, 0.25, 0.4)
    mx.add(pluck(rng, tn - 24 + 12, 7.0, "geomungo", vib=0.4), cyc * 6, -0.2, 0.55, 0.55)   # 가운데 깊은 한 번
    mx.add(bell(rng, 88, 4.0), sec + 0.5, 0.25, 0.3, 0.6)                                   # 요령 한 번으로 맺음
    mx.add(pluck(rng, tn, 6.0, "gayageum", vib=0.3), sec + 0.5, 0.0, 0.3, 0.6)
    return mx, -20.0


# =============================================================================
# 6) 곡 목록과 출력
# =============================================================================
SONGS = {}
for rk, R in REGIONS.items():
    SONGS[f"bgm_{rk}_day_a"] = (lambda R: lambda rng: song_day(rng, R))(R)
    SONGS[f"bgm_{rk}_night"] = (lambda R: lambda rng: song_night(rng, R))(R)
    SONGS[f"bgm_{rk}_combat"] = (lambda R: lambda rng: song_combat(rng, R))(R)
    SONGS[f"bgm_{rk}_finish"] = (lambda R: lambda rng: song_finish(rng, R))(R)
    SONGS[f"bgm_{rk}_boss"] = (lambda R: lambda rng: song_boss(rng, R))(R)
    SONGS[f"bgm_{rk}_boss_p2"] = (lambda R: lambda rng: song_boss_p2(rng, R))(R)
SONGS.update({"bgm_s1_heukwol": s1_heukwol, "bgm_s1_heukwol_fight": s1_heukwol_fight, "bgm_s1_heukwol_flood": s1_heukwol_flood, "bgm_s1_finale_a": s1_finale_a, "bgm_s1_finale_b": s1_finale_b,
              "bgm_s1_dawn": s1_dawn, "bgm_s1_credits": s1_credits})


# ---- 시즌2 컷신 곡(지시문 42~45, cutscene_audio_s2.json 의 play) ----
# 저승 규칙: 박이 흐릿하고, 사람 목소리 없이, 울림을 길고 어둡게. E 계면조(⑦ 삼도천과 같은 음)
def s2_open(rng):
    """시즌2 여는 장면: 먹빛으로 검어지는 강. 장단 없이 생황 드론 위로 대금이 드문드문, 끝에 아쟁이 낮게 받침"""
    tn = 52; md = GYEMYEON
    mx = Mix(64, loop=False, tail=9)
    lay_drone(mx, rng, [tn - 12, tn - 5], 60, gain=0.16, rev=0.6)
    mel = make_melody(rng, tn, md, tn + 7, tn + 22, 9.0, 5, t0=4.0, cells=[0.4, 0.25, 0.35], rest=0.35)
    mx.add(phrase(rng, mel, "daegeum"), 0, 0.15, 0.4, 0.6)
    mx.add(phrase(rng, [(36.0, 12.0, tn - 12, ""), (48.5, 10.0, tn - 5, "")], "ajaeng"), 0, -0.2, 0.3, 0.55)
    for k in range(6): mx.add(pluck(rng, tn + [0, 7, 3, 10, 5, 12][k], 4.0, "gayageum", vib=0.35, bend=(-1 if k % 3 == 2 else 0)), 8 + k * 8.5, 0.3, 0.22, 0.65)
    return mx, -20.0


def s2_bigdam(rng):
    """물막이 바닥 결전(B-20): 느리고 무거운 자진모리 + 큰 북 + 징, 아쟁이 긁어 울고, 웅웅 드론이 짓누름. 반복용"""
    tn = 52; md = GYEMYEON; bpm = 96
    cyc = 4 * 60 / bpm; sec = fit(64, cyc); cycles = int(round(sec / cyc))
    mx = Mix(sec)
    lay_drone(mx, rng, [tn - 24, tn - 12, tn - 5], sec, "ajaeng", gain=0.22, rev=0.4)
    play_jangdan(mx, rng, "jajinmori", bpm, 0, sec, gain=0.5, rev=0.2, accent_first=1.3)
    b = buk(rng, 1.6)
    for k in range(cycles):
        mx.add(b, k * cyc, 0.0, 0.85, 0.25)
        if k % 2: mx.add(b, k * cyc + cyc * 0.5, 0.0, 0.5, 0.25)
        if k % 4 == 0: mx.add(jing(rng, tn - 12, 5.0), k * cyc, 0.0, 0.38, 0.4)
    mel = make_melody(rng, tn, md, tn - 2, tn + 15, cyc * 2, cycles // 2, cells=[0.25, 0.25, 1 / 6, 1 / 6, 1 / 6], rest=0.15)
    mel = [m for m in mel if int(m[0] / (cyc * 2)) % 4 != 0]
    mx.add(phrase(rng, mel, "ajaeng"), 0, -0.1, 0.5, 0.35)
    return mx, -16.0


def s2_finale_a(rng):
    """풀어내기판: 강이 흐른다 — 가야금이 물처럼 잘게 흐르고 해금이 길게. 64초에 뚝 멈췄다가(배가 돌아옴) 대금 한 음, 마지막은 맺지 않음"""
    tn = 52; md = PYEONG
    mx = Mix(104, loop=False, tail=9)
    lay_drone(mx, rng, [tn - 12, tn - 5], 62, gain=0.13, rev=0.5)
    sc = scale_notes(tn, md, tn + 7, tn + 24)
    t = 8.0
    while t < 62:   # 흐르는 물: 잘게 펼쳐지는 가야금
        for j in range(4): mx.add(pluck(rng, sc[(int(t * 3) + j * 2) % len(sc)], 1.6, "gayageum", vib=0.15), t + j * 0.32, rng.uniform(-0.4, 0.4), 0.16, 0.5)
        t += 2.6
    mel = make_melody(rng, tn, md, tn + 7, tn + 22, 8.0, 6, t0=12.0, cells=[0.35, 0.2, 0.25, 0.2], rest=0.2)
    mx.add(phrase(rng, [m for m in mel if m[0] + m[1] < 63], "haegeum"), 0, -0.15, 0.42, 0.5)
    mx.d[:, int(64.0 * SR): int(70.0 * SR)] *= 0.0; mx.w[:, int(64.0 * SR): int(70.0 * SR)] *= 0.0   # 음악도 멈춘다(대본)
    mx.add(phrase(rng, [(76.0, 10.0, tn + 12, "v")], "daegeum"), 0, 0.0, 0.45, 0.6)
    mx.add(drone(rng, [tn - 12], 26), 76, 0.0, 0.14, 0.55)
    mx.add(pluck(rng, tn + 5, 6.0, "gayageum", vib=0.4), 90.0, 0.2, 0.28, 0.65)       # 4도에서 멈춤 — 맺지 않음
    return mx, -20.0


def s2_finale_b(rng):
    """파혼판: 사나운 강이 지나간 빈 기슭. 아쟁 낮은 한 음 + 거문고가 드문드문 무겁게. 차갑게"""
    tn = 52; md = GYEMYEON
    mx = Mix(48, loop=False, tail=8)
    mx.add(phrase(rng, [(0.5, 22, tn - 12, ""), (23.0, 22, tn - 12, "")], "ajaeng"), 0, -0.1, 0.32, 0.55)
    for k, m in enumerate([tn - 12, tn - 5, tn - 9, tn - 12, tn - 7]):
        mx.add(pluck(rng, m, 6.0, "geomungo", vib=0.35, bend=(-1 if k == 2 else 0)), 3 + k * 8.5, -0.25, 0.42, 0.55)
    return mx, -20.0


SONGS.update({"bgm_s2_open": s2_open, "bgm_s2_bigdam": s2_bigdam, "bgm_s2_finale_a": s2_finale_a, "bgm_s2_finale_b": s2_finale_b})


META_AUDIO = """fileFormatVersion: 2
guid: {guid}
AudioImporter:
  externalObjects: {{}}
  serializedVersion: 8
  defaultSettings:
    serializedVersion: 2
    loadType: 0
    sampleRateSetting: 0
    sampleRateOverride: 44100
    compressionFormat: 1
    quality: 1
    conversionMode: 0
    preloadAudioData: 0
  platformSettingOverrides: {{}}
  forceToMono: 0
  normalize: 1
  loadInBackground: 0
  ambisonic: 0
  3D: 1
  userData:
  assetBundleName:
  assetBundleVariant:
"""
META_DIR = """fileFormatVersion: 2
guid: {guid}
folderAsset: yes
DefaultImporter:
  externalObjects: {{}}
  userData:
  assetBundleName:
  assetBundleVariant:
"""


def guid(s):
    """유니티 파일 표(.meta)의 고유 번호. 이름에서 만들어 다시 돌려도 같은 번호가 나온다"""
    return hashlib.md5(("chasa-bgm-temp:" + s).encode()).hexdigest()


# ---- 시즌3 「백의 밤」 아래층 곡(지시문 46~54) ----
# 아래층은 밤에만 열린다 → 낮 곡(day_a)은 만들지 않는다. 코드가 day_a 를 찾으면 night 로 대신 쓸 것(docs/bgm-temp.md).
# 규칙: 위층 같은 막의 곡보다 한 단계 느리고 낮다(물이 빠진 바닥 = 무겁고 갇힌 곳). 사람 목소리 없음.
BELOW = {
    #               으뜸음        빠르기   조         밤 가락(lead)  받침 현          특이 악기   싸움 빠르기
    "below_water": dict(tonic=50, bpm=60, mode=GYEMYEON, lead="daegeum", pl="gayageum", extra="jing",    combat_bpm=100, name="6막 물 밑(①⑤⑦)"),
    "below_earth": dict(tonic=55, bpm=66, mode=GYEMYEON, lead="piri",    pl="geomungo", extra="nagak",   combat_bpm=112, name="7막 흙 밑(③④②⑥)"),
    "below_ink":   dict(tonic=51, bpm=56, mode=PYEONG,   lead="haegeum", pl="geomungo", extra="kkwaeng", combat_bpm=104, name="8막 먹 밑(⑧⑨⑩)"),
}
for bk, R in BELOW.items():
    SONGS[f"bgm_{bk}_night"] = (lambda R: lambda rng: song_night(rng, R))(R)
    SONGS[f"bgm_{bk}_combat"] = (lambda R: lambda rng: song_combat(rng, R))(R)
    SONGS[f"bgm_{bk}_finish"] = (lambda R: lambda rng: song_finish(rng, R))(R)


# ---- 시즌3 특별 곡(지시문 55~62) ----
def s3_rising(rng):
    """새벽 물 차오름(2분, 반복용): 장단은 없고, 낮은 북이 심장처럼 점점 잦아지는 느낌을 30초 한 바퀴에 담는다.
    코드는 물 차오름 2분 동안 이 곡을 깔고 크기를 0.5→1.0 으로 키운다(amb.water.rising 과 같은 곡선)"""
    tn = 50; mx = Mix(32.0)
    lay_drone(mx, rng, [tn - 12, tn - 11], 32.0, "ajaeng", gain=0.2, rev=0.45)      # 반음 부딪는 드론 = 불안
    t, gap = 0.0, 1.6
    while t < 31.5:
        mx.add(buk(rng, 0.9), t, 0.0, 0.5, 0.3); t += gap; gap = max(0.8, gap * 0.97)
    for k in range(4):
        mx.add(pluck(rng, tn + [0, 3, 1, 0][k], 3.0, "geomungo", vib=0.4, bend=-1.0 if k == 2 else 0), 2 + k * 7.5, -0.3, 0.3, 0.45)
    return mx, -18.0


def s3_knot(rng):
    """B-23 매듭(반복용): 수천 가닥 실 = 해금·아쟁이 같은 음을 조금씩 어긋나게 길게 긋는다. 중중모리가 감기고 풀리듯"""
    tn = 50; md = GYEMYEON; bpm = 84
    jd = JANGDAN["jungjung"]; cyc = jd["beats"] * 60 / bpm; sec = fit(60, cyc); cycles = int(round(sec / cyc))
    mx = Mix(sec)
    lay_drone(mx, rng, [tn - 12, tn - 5, tn + 1], sec, "ajaeng", gain=0.2, rev=0.4)
    play_jangdan(mx, rng, "jungjung", bpm, 0, sec, gain=0.5, rev=0.2, accent_first=1.2)
    for k in range(cycles):
        mx.add(buk(rng, 1.2), k * cyc, 0.0, 0.7, 0.25)
        if k % 4 == 0: mx.add(jing(rng, tn - 12, 4.0), k * cyc, 0.0, 0.3, 0.4)
    mel = make_melody(rng, tn, md, tn + 5, tn + 20, cyc, cycles - 1, t0=cyc, cells=[1 / 3, 1 / 3, 1 / 3], rest=0.15)
    mx.add(phrase(rng, mel, "haegeum"), 0, 0.2, 0.42, 0.3)
    mx.add(phrase(rng, [(m[0] + 0.12, m[1], m[2] - 12, m[3]) for m in mel if int(m[0] / cyc) % 2 == 1], "ajaeng"), 0, -0.2, 0.3, 0.3)   # 실이 겹쳐 엉킴
    return mx, -16.0


def s3_imyeong(rng):
    """B-27 이명/흑월의 몸(반복용): 시즌1 흑월 결전과 같은 D음·같은 큰 북 — 그러나 한 단계 낮고 차갑다. 언 땅 = 편경 같은 높은 쇠"""
    tn = 50; md = GYEMYEON; bpm = 92
    cyc = 4 * 60 / bpm; sec = fit(56, cyc); cycles = int(round(sec / cyc))
    mx = Mix(sec)
    lay_drone(mx, rng, [tn - 24, tn - 12], sec, "ajaeng", gain=0.22, rev=0.4)
    play_jangdan(mx, rng, "jajinmori", bpm, 0, sec, gain=0.5, rev=0.2, accent_first=1.3)
    b = buk(rng, 1.6)
    for k in range(cycles):
        mx.add(b, k * cyc, 0.0, 0.85, 0.25)
        if k % 2: mx.add(bell(rng, tn + 36, 2.0), k * cyc + cyc * 0.5, 0.35, 0.12, 0.5)    # 언 땅의 높은 쇠
    mel = make_melody(rng, tn, md, tn - 2, tn + 15, cyc * 2, cycles // 2, cells=[0.25, 0.25, 0.25, 0.25], rest=0.2)
    mx.add(phrase(rng, mel, "piri"), 0, 0.1, 0.45, 0.3)
    return mx, -16.0


def s3_mybaek(rng):
    """B-31 나의 백(반복용): 물속. 박이 흐릿한 진양 위에 대금 — 1막 솔고개 첫 곡과 같은 으뜸음(A)으로 돌아와 처음과 끝을 잇는다"""
    tn = 57; md = GYEMYEON; bpm = 52
    beat = 60 / bpm; cyc = 24 * beat; sec = fit(84, cyc); cycles = int(round(sec / cyc))
    mx = Mix(sec)
    lay_drone(mx, rng, [tn - 24, tn - 12, tn - 5], sec, "saenghwang", gain=0.2, rev=0.6)
    play_jangdan(mx, rng, "jinyang", bpm, 0, sec, gain=0.3, rev=0.45, skip=0.2)
    for k in range(cycles):
        mx.add(buk(rng, 1.0), k * cyc, 0.0, 0.5, 0.45)
        mx.add(jing(rng, tn - 12, 6.0), k * cyc + cyc * 0.5, 0.0, 0.25, 0.6)
    mel = make_melody(rng, tn, md, tn - 2, tn + 14, cyc / 2, cycles * 2, cells=[0.3, 0.2, 0.3, 0.2], rest=0.25)
    mx.add(phrase(rng, mel, "daegeum"), 0, 0.12, 0.45, 0.6)
    return mx, -16.0


def s3_open(rng):
    """시즌3 여는 장면(C-21, 약 70초): 물 빠진 강바닥. 장단 없이 아쟁 드론, 가야금이 물방울처럼 떨어지고, 끝에 사슬이 바닥에 닿는 징 한 번"""
    tn = 50; md = GYEMYEON
    mx = Mix(70, loop=False, tail=8)
    lay_drone(mx, rng, [tn - 12, tn - 5], 64, "ajaeng", gain=0.15, rev=0.6)
    sc = scale_notes(tn, md, tn + 7, tn + 26)
    for k in range(14):
        mx.add(pluck(rng, sc[rng.integers(len(sc))], 3.0, "gayageum", vib=0.3), 4 + k * 3.6 + rng.uniform(0, 1), rng.uniform(-0.4, 0.4), 0.2, 0.65)
    mel = make_melody(rng, tn, md, tn + 5, tn + 19, 10.0, 3, t0=24.0, cells=[0.4, 0.3, 0.3], rest=0.3)
    mx.add(phrase(rng, mel, "daegeum"), 0, 0.15, 0.36, 0.6)
    mx.add(jing(rng, tn - 12, 7.0), 60.0, 0.0, 0.5, 0.6)
    return mx, -20.0


def s3_end_a(rng):
    """결말 A 이름을 부르다(약 4분 중 앞부분 대역 150초): 평조로 밝아짐. 상여 소리처럼 느린 중모리 → 해금·대금이 함께, 끝에 맺음(으뜸음)"""
    tn = 57; md = PYEONG; bpm = 60
    jd = JANGDAN["jungmori"]; cyc = jd["beats"] * 60 / bpm; sec = fit(144, cyc); cycles = int(round(sec / cyc))
    mx = Mix(sec + 8, loop=False, tail=8)
    lay_drone(mx, rng, [tn - 12, tn - 5], sec, gain=0.14, rev=0.5)
    play_jangdan(mx, rng, "jungmori", bpm, cyc * 2, sec - cyc * 3, gain=0.32, rev=0.35, skip=0.15)
    mel = make_melody(rng, tn, md, tn, tn + 19, cyc, cycles - 3, t0=cyc, rest=0.25)
    mx.add(phrase(rng, mel, "daegeum"), 0, 0.15, 0.42, 0.5)
    ans = make_melody(rng, tn, md, tn + 7, tn + 24, cyc, cycles, rest=0.4)
    mx.add(phrase(rng, [m for m in ans if int(m[0] / cyc) % 3 == 2 and m[0] > cyc * 4], "haegeum"), 0, -0.2, 0.32, 0.5)
    mx.add(pluck(rng, tn - 12, 7.0, "gayageum", vib=0.3), sec - 1.0, 0.0, 0.4, 0.6)        # 맺음: 으뜸음
    return mx, -20.0


def s3_end_b(rng):
    """결말 B 번진 명부(대역 110초): 같은 가락이 계면조로 — 먹이 번지듯 음이 끝마다 흘러내림(꺾는 소리). 맺지 않고 5도에서 멈춤"""
    tn = 57; md = GYEMYEON
    mx = Mix(110, loop=False, tail=8)
    lay_drone(mx, rng, [tn - 12], 104, "saenghwang", gain=0.14, rev=0.6)
    mel = make_melody(rng, tn, md, tn, tn + 15, 9.0, 10, t0=6.0, cells=[0.35, 0.3, 0.35], rest=0.3)
    mx.add(phrase(rng, [(a, b, c, "d") for a, b, c, d in mel], "haegeum"), 0, 0.1, 0.4, 0.55)
    for k in range(9): mx.add(pluck(rng, tn - 12 + [0, 7, 5, 3][k % 4], 5.0, "geomungo", vib=0.35, bend=-1.0), 4 + k * 11, -0.3, 0.32, 0.55)
    mx.add(pluck(rng, tn + 7, 6.0, "gayageum", vib=0.4), 100.0, 0.2, 0.3, 0.65)
    return mx, -20.0


def s3_end_c(rng):
    """결말 C 다음 검은 갓(대역 80초): 가락 없음. 아쟁 한 음과 먼 큰 북이 느리게 — 다음 회차 1막의 첫 북으로 이어지는 문턱"""
    tn = 50
    mx = Mix(80, loop=False, tail=8)
    mx.add(phrase(rng, [(1.0, 36.0, tn - 12, ""), (38.0, 36.0, tn - 12, "")], "ajaeng"), 0, -0.1, 0.3, 0.55)
    for k in range(8): mx.add(buk(rng, 1.3), 6 + k * 8.5, 0.0, 0.45 + k * 0.03, 0.5)
    return mx, -20.0


SONGS.update({"bgm_s3_rising": s3_rising, "bgm_s3_knot": s3_knot, "bgm_s3_imyeong": s3_imyeong, "bgm_s3_mybaek": s3_mybaek,
              "bgm_s3_open": s3_open, "bgm_s3_end_a": s3_end_a, "bgm_s3_end_b": s3_end_b, "bgm_s3_end_c": s3_end_c})


def title(rng):
    """타이틀 화면(반복 64초): 밤 서낭당 고개, 안개. 장단 없이 아쟁 드론 위로 대금이 길게 한 가락, 거문고가 드문드문 깊게,
    한 바퀴에 한 번 먼 요령. 계면조 D — 1막 솔고개 밤과 같은 집안 소리지만 더 느리고 비어 있게"""
    tn = 50; md = GYEMYEON
    mx = Mix(64, loop=True)
    lay_drone(mx, rng, [tn - 12, tn - 5], 64, "ajaeng", gain=0.14, rev=0.6)
    mel = make_melody(rng, tn, md, tn + 2, tn + 17, 12.0, 4, t0=6.0, cells=[0.45, 0.25, 0.3], rest=0.3)
    mx.add(phrase(rng, mel, "daegeum"), 0, 0.15, 0.4, 0.6)
    for k in range(6):
        mx.add(pluck(rng, tn - 12 + [0, 7, 5, 0, 3, 7][k], 5.0, "geomungo", vib=0.35, bend=(-1 if k == 4 else 0)), 2 + k * 10.3, -0.3, 0.3, 0.55)
    mx.add(bell(rng, 86, 4.0), 58.0, 0.35, 0.18, 0.7)
    return mx, -20.0


SONGS["bgm_title"] = title


def render(sid, preview=None):
    rng = np.random.default_rng(zlib.crc32(sid.encode()))
    mx, target = SONGS[sid](rng)
    x = mx.render(rt=3.2 if any(k in sid for k in ("combat", "boss", "heukwol", "knot", "imyeong")) else 4.2)
    x = circ(hp, x, mx.loop, 35)
    if not mx.loop:   # 반복하지 않는 곡은 끝을 3초에 걸쳐 닫는다
        f = int(3.0 * SR); x[:, -f:] *= np.linspace(1, 0, f) ** 2
    for _ in range(3):   # 크기 맞추기: 재고 → 키우거나 줄이고 → 다시 잰다
        x = circ(limit, x * 10 ** ((target - lufs(x)) / 20), mx.loop)
    got = lufs(x)
    os.makedirs(OUT_DIR, exist_ok=True)
    wav = os.path.join(tempfile.gettempdir(), sid + ".wav"); write_wav(wav, x)
    ogg = os.path.join(OUT_DIR, sid + ".ogg")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "4",
                    "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", ogg], check=True)
    meta = ogg + ".meta"
    if not os.path.exists(meta):
        open(meta, "w").write(META_AUDIO.format(guid=guid(sid)))
    if preview:
        os.makedirs(preview, exist_ok=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", wav, "-c:a", "libmp3lame", "-b:a", "112k",
                        os.path.join(preview, sid + ".mp3")], check=True)
    os.unlink(wav)
    return dict(id=sid, sec=round(x.shape[1] / SR, 2), loop=mx.loop, lufs=round(got, 1), target=target,
                peak_db=round(20 * np.log10(np.max(np.abs(x)) + 1e-9), 1))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    preview = None
    if "--preview" in sys.argv: preview = sys.argv[sys.argv.index("--preview") + 1]; args = [a for a in args if a != preview]
    ids = [s for s in SONGS if not args or any(a in s for a in args)]
    dmeta = OUT_DIR + ".meta"
    if not os.path.exists(dmeta):
        os.makedirs(OUT_DIR, exist_ok=True); open(dmeta, "w").write(META_DIR.format(guid=guid("Temp")))
    rows = []
    for s in ids:
        r = render(s, preview); rows.append(r)
        print(f"{r['id']:26s} {r['sec']:7.2f}s  {'반복' if r['loop'] else '1회'}  {r['lufs']:6.1f} LUFS (목표 {r['target']})  최고 {r['peak_db']} dB")
    # 목록 파일(코드·기획이 무엇이 임시인지 알 수 있게)
    lst = os.path.join(ROOT, "data/bgm_temp.json")
    old = json.load(open(lst, encoding="utf-8")) if os.path.exists(lst) else {}
    clips = old.get("clips", {}); clips.update({r["id"]: {k: r[k] for k in ("sec", "loop", "lufs")} for r in rows})
    json.dump({"_설명": "임시 대역 BGM(코드 합성, tools/bgm_temp_render.py). 파일은 Resources/Audio/BGM/Temp/<id>.ogg. "
                        "진짜 곡을 Resources/Audio/BGM/<id>.ogg 로 넣으면 그것이 먼저 쓰인다(코드 수정 불필요).",
               "clips": dict(sorted(clips.items()))}, open(lst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
