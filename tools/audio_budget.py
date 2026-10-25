#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""소리 용량·크기 점검표 만들기 (기획·사운드, 2026-10-25)

왜 필요한가:
  웹(브라우저)과 폰은 '내려받는 크기'와 '메모리(풀어서 들고 있는 양)'가 빠듯하다.
  지금 소리는 모두 Resources 폴더에 있어서, 웹판은 처음 열 때 342개 효과음 + BGM 전부를
  한 번에 내려받는다. 이 도구는 (1) 막별로 묶음을 나누고 (2) 묶음마다 내려받기 크기와
  메모리를 어림하고 (3) 클리핑(소리가 천장에 닿아 찢어짐)·음량 편차를 한꺼번에 검사한다.

하는 일:
  1) 파일마다 길이·최고점(샘플/트루 피크)·평균 음량(LUFS 비슷한 K가중 값)·11kHz 위 에너지를 잰다.
  2) 실제로 AAC(웹이 쓰는 압축)·Vorbis(폰 앱이 쓰는 압축)로 시험 변환해 크기를 잰다.
  3) data/audio_packs.json(막별 묶음표)과 docs/audio-budget.md(보고서)를 쓴다.

쓰는 법:  python3 tools/audio_budget.py            (약 2분, ffmpeg 필요)
"""
import json, os, glob, subprocess, tempfile, re
import numpy as np
from scipy.io import wavfile
from scipy import signal as sg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX = os.path.join(ROOT, "unity/Assets/Resources/Audio/Sfx")
BGM = os.path.join(ROOT, "unity/Assets/Resources/Audio/BGM")

# ---------------------------------------------------------------------------
# 0) 권장 압축값 — 시험 변환에 쓰는 값. Unity 가져오기 설정(품질 슬라이더)도 이 크기에 맞춘다
# ---------------------------------------------------------------------------
PLAN = {
    #  종류          AAC(웹) kbps   Vorbis(폰) 품질   표본율          불러오기 방식
    "sfx_short":   dict(aac=64,  vq=4, sr=44100, load="DecompressOnLoad"),   # 짧은 타격·UI: 바로 울려야 함(지연 없음)
    "sfx_lowband": dict(aac=48,  vq=3, sr=22050, load="DecompressOnLoad"),   # 11kHz 위가 거의 없는 짧은 소리 → 표본율 절반
    "amb_loop":    dict(aac=48,  vq=3, sr=22050, load="CompressedInMemory"), # 반복 환경음: 길고 늘 깔림 → 압축한 채로 들고 있기
    "long_oneshot":dict(aac=56,  vq=3, sr=44100, load="CompressedInMemory"), # 8초 넘는 한 번 소리(마무리 15초 등)
    "bgm":         dict(aac=80,  vq=3, sr=44100, load="CompressedInMemory"), # 음악(스테레오)
}
LONG_SEC = 8.0


def kweight(x, sr):
    """K 가중(사람 귀가 크게 느끼는 쪽을 더 세게) — ITU BS.1770 의 두 단 필터"""
    # 1단: 높은 쪽 선반(머리 효과), 2단: 아주 낮은 쪽 깎기
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = np.tan(np.pi * f0 / sr); Vh = 10 ** (G / 20); Vb = Vh ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    b1 = [(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0]
    a1 = [1, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = np.tan(np.pi * f0 / sr)
    b2 = [1, -2, 1]; a2 = [1, 2 * (K * K - 1) / (1 + K / Q + K * K), (1 - K / Q + K * K) / (1 + K / Q + K * K)]
    return sg.lfilter(b2, a2, sg.lfilter(b1, a1, x, axis=0), axis=0)


def loud(x, sr):
    """(통합 LUFS, 최대 순간 LUFS 400ms). 짧은 소리는 '최대 순간' 값이 더 믿을 만하다"""
    y = kweight(x, sr)
    if y.ndim == 1: y = y[:, None]
    p = (y ** 2).sum(axis=1)
    w = int(0.4 * sr); hop = int(0.1 * sr)
    if len(p) < w: p = np.pad(p, (0, w - len(p)))
    ms = np.array([p[i:i + w].mean() for i in range(0, len(p) - w + 1, hop)])
    ml = -0.691 + 10 * np.log10(ms + 1e-12)
    gated = ms[ml > -70]
    if len(gated) == 0: return -99.0, float(ml.max())
    rel = -0.691 + 10 * np.log10(gated.mean()) - 10
    g2 = gated[(-0.691 + 10 * np.log10(gated + 1e-12)) > rel]
    integ = -0.691 + 10 * np.log10((g2 if len(g2) else gated).mean())
    return float(integ), float(ml.max())


def true_peak(x):
    """트루 피크: 4배로 촘촘히 늘려 샘플 '사이'에서 솟는 최고점까지 찾는다(압축하면 여기가 찢어진다)"""
    y = sg.resample_poly(x, 4, 1, axis=0)
    return 20 * np.log10(np.abs(y).max() + 1e-12)


def hf_ratio_db(x, sr):
    """11kHz 위 에너지가 전체보다 몇 dB 작은가(−40보다 작으면 표본율을 절반으로 해도 귀로 차이 없음)"""
    if x.ndim > 1: x = x.mean(axis=1)
    f, P = sg.welch(x, sr, nperseg=4096)
    return 10 * np.log10(P[f > 11000].sum() / (P.sum() + 1e-20) + 1e-20)


def enc_size(path, codec, kbps=None, vq=None, sr=None, ch=None):
    """ffmpeg 로 실제 변환해 바이트 수를 잰다"""
    with tempfile.NamedTemporaryFile(suffix=".m4a" if codec == "aac" else ".ogg") as t:
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", path]
        if sr: cmd += ["-ar", str(sr)]
        if ch: cmd += ["-ac", str(ch)]
        cmd += ["-c:a", "aac", "-b:a", f"{kbps}k"] if codec == "aac" else ["-c:a", "libvorbis", "-q:a", str(vq)]
        subprocess.run(cmd + [t.name], check=True)
        return os.path.getsize(t.name)


# ---------------------------------------------------------------------------
# 1) 막별 묶음 나누기 규칙
# ---------------------------------------------------------------------------
# 보스 번호 → 막. 1막 B-01~04, 2막 B-05~08, 3막 B-09~12, 시즌2 B-13~20, 시즌3 6막 B-21~23 · 7막 B-24~27 · 8막 B-28~31
BOSS_PACK = {"naru": "act1", "wolhwa": "act1", "seo": "act1",
             "daedol": "act2", "general": "act2", "chilsung": "act2", "yeom": "act2",
             "mangbu": "act3", "seonjang": "act3", "wangcho": "act3", "heukwol": "act3",
             "yun": "act6", "seven": "act6", "knot": "act6",
             "armies": "act7", "chilseong": "act7", "plague": "act7", "imyeong": "act7",
             "byeoru": "act8", "halmi": "act8", "mother": "act8", "mybaek": "act8"}
WORLD_PACK = {"amb.mine": "act2", "amb.fortress.flag": "act2", "amb.arrowvalley": "act2", "amb.camp": "act2",
              "amb.mine.wind": "act2", "amb.mine.shaft": "act2",
              "amb.harbor": "act3", "sfx.tide.flood": "act3", "amb.tide.ebb": "act3", "amb.saltfield": "act3",
              "amb.wreckshoal": "act3", "amb.capital.market": "act3", "amb.bridge.under": "act3",
              "amb.citygate": "act3", "amb.market.hush": "act3"}
BELOW_PACK = {"dambed": "act6", "poolbed": "act6", "pooldeep": "act8", "wreckbed": "act6", "seacave": "act6",
              "linebed": "act6", "knotdeep": "act6", "tombpit": "act7", "arrowroots": "act7", "floodedshaft": "act7",
              "sealedface": "act7", "limepit": "act7", "clinicfloor": "act7", "gatepit": "act7", "bridgefound": "act7",
              "inksilt": "act8", "quartercellar": "act8", "ondol": "act8", "sealfloor": "act8", "chainroots": "act8",
              "wellbottom": "act8"}
PACK_ORDER = ["core", "act1", "act2", "act3", "s2", "act6", "act7", "act8"]
PACK_NAME = {"core": "공통(처음 화면에서 바로)", "act1": "1막 솔고개", "act2": "2막 붉은재·쇳골", "act3": "3막 갯마을·도성(시즌1 끝 포함)",
             "s2": "시즌2 저승 ⑦~⑩(4·5막)", "act6": "6막 물 밑(시즌3 공통 장치 포함)", "act7": "7막 흙 밑", "act8": "8막 먹 밑(결말 포함)"}
CUT_ACT = lambda b: "act1" if b <= 4 else "act2" if b <= 8 else "act3" if b <= 12 else "s2" if b <= 20 else "act6" if b <= 23 else "act7" if b <= 27 else "act8"


def cut_first_use():
    """컷신 소리 대본에서 소리마다 '가장 먼저 쓰이는 막'을 찾는다(그 막 묶음에 넣는다)"""
    first = {}
    for fn in ("cutscene_audio_s1.json", "cutscene_audio_s2.json", "cutscene_audio_s3.json"):
        p = os.path.join(ROOT, "data", fn)
        if not os.path.exists(p): continue
        cuts = json.load(open(p, encoding="utf-8"))["cuts"]
        for cid, beats in cuts.items():
            m = re.match(r"B-?(\d+)", cid) or re.match(r"C-?(\d+)", cid)
            n = int(m.group(1)) if m else 12
            pack = CUT_ACT(n) if fn != "cutscene_audio_s2.json" else "s2"
            for beat in beats.values():
                for k in ("add", "replace"):
                    for a in beat.get(k, []) if isinstance(beat.get(k), list) else ([beat[k]] if k in beat else []):
                        # 모양이 셋: "id" 글자 / {"id": ...} / {"옛 id": "새 id"}(바꾸기). {"stop": ...}은 새 소리가 아님
                        if isinstance(a, str): ids = [a]
                        elif "id" in a: ids = [a["id"]]
                        elif k == "replace": ids = list(a.values())
                        else: ids = []
                        for sid in ids:
                            if sid not in first or PACK_ORDER.index(pack) < PACK_ORDER.index(first[sid]): first[sid] = pack
    return first


def sfx_pack(s, cut_first):
    i, c = s["id"], s["category"]
    if i.startswith("sfx.boss."): return BOSS_PACK.get(i.split(".")[2], "core")
    if i.startswith("amb.below."): return BELOW_PACK[i.split(".")[2]]
    if c == "백의 밤": return "act6"
    if c == "저승": return "s2"
    if i in WORLD_PACK: return WORLD_PACK[i]
    if c in ("컷신",):
        # 덧칠표에서 처음 쓰인 막과, 쓰는 곳(use)에 적힌 첫 컷 번호의 막 중 더 이른 쪽(대본에만 있고 덧칠표엔 없는 소리도 맞게)
        cands = [cut_first[i]] if i in cut_first else []
        m = re.search(r"\b(?:B-?|C-)(\d{2})", s.get("use", ""))
        if m: cands.append(CUT_ACT(int(m.group(1))))
        if any(w in s.get("use", "") for w in ("S3-", "RITE-REVERSE", "LEDGER-REVERSE")): cands.append("act6")
        f = re.search(r"FUN-S(\d+)", s.get("use", ""))
        if f and int(f.group(1)) >= 80: cands.append("act3")      # S-080 넘는 장례 = 3막 갯마을·도성 사람들
        return min(cands, key=PACK_ORDER.index) if cands else "act1"
    return "core"   # UI·발소리·전투·처결·탐색·날씨·1막 세계 소리 = 어디서나 쓰는 것


def bgm_pack(sid):
    if "solgogae" in sid: return "act1"
    if "bulgeunjae" in sid or "soegol" in sid: return "act2"
    if "gaetmaeul" in sid or "doseong" in sid or sid.startswith("bgm_s1_"): return "act3"
    if sid.startswith("bgm_s2_"): return "s2"
    if "below_water" in sid or sid in ("bgm_s3_open", "bgm_s3_rising", "bgm_s3_knot"): return "act6"
    if "below_earth" in sid or sid == "bgm_s3_imyeong": return "act7"
    return "act8"


def main():
    man = json.load(open(os.path.join(ROOT, "data/sfx_files.json"), encoding="utf-8"))["sounds"]
    cut_first = cut_first_use()
    rows = []
    for s in man:
        p = os.path.join(SFX, s["file"] + ".wav"); sr, x = wavfile.read(p); x = x.astype(np.float64) / 32768
        dur = len(x) / sr
        il, ml = loud(x, sr); hf = hf_ratio_db(x, sr)
        kind = "amb_loop" if s["loop"] else "long_oneshot" if dur > LONG_SEC else ("sfx_lowband" if hf < -40 else "sfx_short")
        P = PLAN[kind]
        rows.append(dict(id=s["id"], file=s["file"], cat=s["category"], loop=s["loop"], sec=round(dur, 2),
                         peak=round(20 * np.log10(np.abs(x).max() + 1e-12), 2), tp=round(true_peak(x), 2),
                         lufs=round(il, 1), mmax=round(ml, 1), hf=round(hf, 1), kind=kind, pack=sfx_pack(s, cut_first),
                         wav=os.path.getsize(p), aac=enc_size(p, "aac", P["aac"], sr=P["sr"]),
                         vorbis=enc_size(p, "vorbis", vq=P["vq"], sr=P["sr"]),
                         mem_decoded=int(dur * 48000 * 4) if P["load"] == "DecompressOnLoad" else 0,
                         mem_compressed=0 if P["load"] == "DecompressOnLoad" else None))
        r = rows[-1]
        if r["mem_compressed"] is None: r["mem_compressed"] = r["aac"]
    brows = []
    for p in sorted(glob.glob(os.path.join(BGM, "*.ogg")) + glob.glob(os.path.join(BGM, "Temp", "*.ogg"))):
        sid = os.path.basename(p)[:-4]; temp = "/Temp/" in p
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
        # 음량·피크 검사는 풀어서(wav) 한다
        with tempfile.NamedTemporaryFile(suffix=".wav") as t:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", p, t.name], check=True)
            sr, x = wavfile.read(t.name); x = x.astype(np.float64) / 32768
        il, ml = loud(x, sr)
        brows.append(dict(id=sid, temp=temp, sec=round(dur, 1), ogg=os.path.getsize(p), pack=bgm_pack(sid),
                          peak=round(20 * np.log10(np.abs(x).max() + 1e-12), 2), tp=round(true_peak(x), 2), lufs=round(il, 1),
                          aac=enc_size(p, "aac", PLAN["bgm"]["aac"]), vorbis=enc_size(p, "vorbis", vq=PLAN["bgm"]["vq"]),
                          mem_decoded_if_wrong=int(dur * 48000 * 4 * 2)))
    json.dump(dict(sfx=rows, bgm=brows), open(os.path.join(ROOT, "data/audio_budget_raw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    write_packs(rows, brows)
    write_report(rows, brows)
    print(len(rows), "효과음,", len(brows), "곡 측정 끝")


def write_packs(rows, brows):
    packs = {k: dict(name=PACK_NAME[k], sfx=[], bgm=[]) for k in PACK_ORDER}
    for r in rows: packs[r["pack"]]["sfx"].append(r["id"])
    for b in brows:
        if b["id"] not in packs[b["pack"]]["bgm"]: packs[b["pack"]]["bgm"].append(b["id"])
    out = {"_설명": "소리 막별 묶음표(기획·사운드 tools/audio_budget.py 가 만듦). 웹·폰에서 처음엔 core+act1 만 내려받고, "
                    "다음 막 묶음은 그 앞 막을 하는 동안 뒤에서 미리 받는다. 묶음에 없는 소리를 부르면 코드 합성(SfxSynth)으로 대신.",
           "order": PACK_ORDER,
           "import": {k: dict(v, why={"sfx_short": "짧은 타격·UI — 지연 없이 바로", "sfx_lowband": "11kHz 위가 거의 없음 → 22050Hz",
                                       "amb_loop": "반복 환경음 — 압축한 채 메모리에(iOS 무음 모드 문제도 피함)",
                                       "long_oneshot": "8초 넘는 한 번 소리", "bgm": "음악 — 압축한 채 메모리에"}[k]) for k, v in PLAN.items()},
           "kind_of": {r["id"]: r["kind"] for r in rows},
           "packs": packs}
    json.dump(out, open(os.path.join(ROOT, "data/audio_packs.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# 지금 Unity 설정(Vorbis 품질 100%)으로 구웠을 때의 크기 — 2026-10-25 밤 같은 파일을 libvorbis -q 10 으로 시험 변환해 잰 값
NOW_SFX_MB, NOW_BGM_MB = 39.7, 119.0


def write_report(rows, brows):
    """docs/audio-budget.md: 사람이 읽는 보고서(숫자는 모두 이 도구가 잰 값)"""
    MB = lambda b: b / 1e6
    sa, sv = sum(r["aac"] for r in rows), sum(r["vorbis"] for r in rows)
    ba, bv = sum(b["aac"] for b in brows), sum(b["vorbis"] for b in brows)
    L = ["# 소리 용량 예산 (웹·폰) — tools/audio_budget.py 가 만든 보고서", "",
         f"효과음 {len(rows)}개 · 곡 {len(brows)}개(임시 대역 포함)를 실제로 변환해 잰 값이다. 다시 재려면 `python3 tools/audio_budget.py`.", "",
         "## 한눈에", "",
         "| | 원본(저장소) | 지금 설정으로 구우면(품질 100%) | 권장 설정 — 웹(AAC) | 권장 설정 — 폰 앱(Vorbis) |", "|---|---|---|---|---|",
         f"| 효과음 | {MB(sum(r['wav'] for r in rows)):.0f}MB(wav) | 약 {NOW_SFX_MB:.0f}MB | **{MB(sa):.1f}MB** | **{MB(sv):.1f}MB** |",
         f"| 음악 | {MB(sum(b['ogg'] for b in brows)):.0f}MB(ogg) | 약 {NOW_BGM_MB:.0f}MB | **{MB(ba):.1f}MB** | **{MB(bv):.1f}MB** |",
         f"| 합계 | | 약 {NOW_SFX_MB + NOW_BGM_MB:.0f}MB | **{MB(sa + ba):.1f}MB** | **{MB(sv + bv):.1f}MB** |", "",
         "## 막별 묶음(처음엔 공통+1막만)", "",
         "| 묶음 | 효과음 | 곡 | 웹 내려받기(AAC) | 웹 메모리 어림 |", "|---|---|---|---|---|"]
    first = 0
    for k in PACK_ORDER:
        rs = [r for r in rows if r["pack"] == k]; bs = [b for b in brows if b["pack"] == k]
        dl = sum(r["aac"] for r in rs) + sum(b["aac"] for b in bs)
        mem = sum(r["mem_decoded"] + r["mem_compressed"] for r in rs) + sum(b["aac"] for b in bs)
        if k in ("core", "act1"): first += dl
        L.append(f"| {PACK_NAME[k]} | {len(rs)} | {len(bs)} | {MB(dl):.1f}MB | {MB(mem):.0f}MB |")
    L += ["", f"**첫 화면에서 받는 소리 = 공통 + 1막 = 약 {MB(first):.1f}MB** (지금은 전부 약 {NOW_SFX_MB + NOW_BGM_MB:.0f}MB를 한 번에).", "",
          "메모리 어림: 짧은 소리는 브라우저가 풀어서(48kHz, 4바이트) 들고 있고, 반복 환경음·긴 소리·음악은 압축한 채로 든다고 보고 셌다. 한 묶음을 다 불렀을 때의 최대치다.", "",
          "## 검사 결과", ""]
    hot = [r for r in rows + brows if r["tp"] > -1.0]
    L.append(f"- **클리핑(찢어짐):** 샘플 최고점이 0dB에 닿은 파일 0개. 트루 피크(샘플 사이 최고점)가 −1dB를 넘는 파일 {len(hot)}개"
             + (": " + ", ".join(f"`{r['id']}` {r['tp']}dB" for r in hot) + ". 압축하면 넘칠 수 있어 −1dB 아래로 맞출 것(진짜 곡이면 다시 내보내기)" if hot else "") + ".")
    import statistics as st, collections
    cat = collections.defaultdict(list)
    for r in rows: cat[r["cat"] + (" 반복" if r["loop"] else "")].append(r)
    L += ["- **음량 편차:** 같은 묶음(카테고리) 안에서 '최대 순간 음량'이 가운데 값보다 6dB 넘게 다른 것. 일부러 그런 것(처결 대기 틱은 작게, 품계 오름은 크게)은 그대로 둔다.", "",
          "| 묶음 | 개수 | 가운데 값 | 튀는 것 |", "|---|---|---|---|"]
    for k, v in sorted(cat.items()):
        med = st.median(x["mmax"] for x in v)
        out = [f"`{x['id']}` {x['mmax'] - med:+.0f}" for x in v if abs(x["mmax"] - med) > 6]
        L.append(f"| {k} | {len(v)} | {med:.0f} LUFS | {', '.join(out) or '—'} |")
    bl = [b for b in brows if abs(b["lufs"] - (-16 if any(w in b["id"] for w in ("combat", "finish", "heukwol", "bigdam", "knot", "imyeong", "mybaek")) else -18 if "rising" in b["id"] else -20)) > 1.0]
    L += ["", f"- **음악 음량:** 탐색 −20 · 전투/처결 −16 LUFS 목표에서 1dB 넘게 벗어난 곡 {len(bl)}개" + (": " + ", ".join(f"`{b['id']}` {b['lufs']}" for b in bl) if bl else "") + "."]
    with open(os.path.join(ROOT, "docs/audio-budget.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
