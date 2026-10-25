"""혼 공격 예고 점검: 예고(Windup) 동작이 '그림자(실루엣)'만 봐도 0.3~0.7초 안에 읽히는지 숫자로 잰다.
방법: 게임 카메라(50° 쿼터뷰, 혼 키 약 100px)에서 몸을 까맣게 칠해 예고 프레임들을 찍고, 쉬는 자세(Float 0프레임)와 얼마나 모양이 달라졌는지를
 변화율 D = (달라진 픽셀 수) / (쉬는 자세 면적) 로 잰다. 앞모습(적이 플레이어를 보는 방향)과 옆모습 둘 다 잰다.
읽힘 기준(제안): 예고 시작 후 0.3초에 D ≥ 0.10(앞·옆 중 큰 쪽) 이고, 예고 끝(번쩍 직전)에 D ≥ 0.25. 첫 신호 시각 = D가 처음 0.10을 넘는 때.
실행: python3 soul_tele_check.py [out.json]"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image
from lib3d import *
import anim
from characters import souls, rig, to_group
import soul_anim as sa
import soul_types as st
from npc_silhouette import black_everything
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets3d")
FPS = 60

REST = {"buried": "Hidden"}   # 쉬는 자세로 삼을 동작(묻힌 혼은 땅속 대기)

def models():
    """(이름, 만드는 함수, 뼈, 동작 함수, 예고 동작 이름들)"""
    M = [("basic", lambda: to_group(souls()["day"](), "Body"), sa.BONES, sa.clips, ["Windup"])]
    for t in ("wail", "mote", "buried", "elite"):
        fn, bones, cl, ko, desc = st.TYPES[t]; M.append((t, (lambda fn=fn: fn("day")), bones, cl, {"elite": ["SlamWindup", "PounceWindup", "Call"]}.get(t, ["Windup"])))
    return M

def mask_of(path):
    a = np.asarray(Image.open(path).convert("L"), np.float32); return a < 128

def measure(name, build, bones, clipfn, wind, step=3):
    res = {}
    for yaw in (0, 90):
        reset(); anim.setup_scene(); o = join(name, build()); arm = rig(o, bones); C = clipfn()
        for cn, (keys, interp, loop, ev) in C.items(): anim.clip(arm, cn, keys, interp)
        o.parent.rotation_euler = (0, 0, math.radians(yaw)) if o.parent else (0, 0, 0)
        big = 2.7 if name != "mote" else 1.0; cz = 0.9 if name != "mote" else 0.28
        setup_render(big, (0, 0, cz), size=(110, 140), ground_size=8); black_everything()
        bpy.context.scene.cycles.samples = 4
        ad = arm.animation_data; ad.action = None
        for cn in wind:
            for t in ad.nla_tracks: t.mute = t.name != cn
            n = max(f for f in [int(k.frame_end) if hasattr(k, "frame_end") else 0 for k in [s for t in ad.nla_tracks if t.name == cn for s in t.strips]] or [0])
            last = int(max(s.frame_end for t in ad.nla_tracks if t.name == cn for s in t.strips)); first = int(min(s.frame_start for t in ad.nla_tracks if t.name == cn for s in t.strips))
            # 쉬는 자세: Float
            for t in ad.nla_tracks: t.mute = t.name != REST.get(name, "Float")
            bpy.context.scene.frame_set(int(min(s.frame_start for t in ad.nla_tracks if t.name == REST.get(name, "Float") for s in t.strips))); p0 = os.path.join(OUT, "previews", "_tele0.png"); bpy.context.scene.render.filepath = p0; bpy.ops.render.render(write_still=True); m0 = mask_of(p0)
            for t in ad.nla_tracks: t.mute = t.name != cn
            frames = list(range(0, last - first + 1, step)); frames = frames + ([last - first] if frames[-1] != last - first else []); D = []
            for f in frames:
                bpy.context.scene.frame_set(first + f); p = os.path.join(OUT, "previews", "_tele.png"); bpy.context.scene.render.filepath = p; bpy.ops.render.render(write_still=True)
                m = mask_of(p); D.append(float(np.logical_xor(m, m0).sum() / max(1, m0.sum())))
            res.setdefault(cn, {})[yaw] = {"frames": frames, "D": D, "len": last - first}
    for p in ("_tele0.png", "_tele.png"):
        try: os.remove(os.path.join(OUT, "previews", p))
        except OSError: pass
    return res

TELL_END = {"Call": 28}   # 예고가 끝나는 프레임(울부짖음은 28프레임에 징을 치고 그 뒤는 외침이라 예고 끝 = 28)

def summarize(res, thr=0.10, end_thr=0.25):
    out = {}
    for cn, d in res.items():
        fr = d[0]["frames"]; L = d[0]["len"]; Df = d[0]["D"]; Ds = d[90]["D"]; Dm = [max(a, b) for a, b in zip(Df, Ds)]
        first = next((fr[i] / FPS for i, v in enumerate(Dm) if v >= thr), None)
        i03 = min(range(len(fr)), key=lambda i: abs(fr[i] - 0.3 * FPS)); d03 = Df[i03]; ie = (min(range(len(fr)), key=lambda i: abs(fr[i] - TELL_END[cn])) if cn in TELL_END else len(fr) - 1); dend = Df[ie]      # 앞모습 기준(적은 플레이어를 바라본다)
        first = next((fr[i] / FPS for i, v in enumerate(Df) if v >= thr), None)
        out[cn] = {"seconds": round(L / FPS, 2), "first_cue_s": None if first is None else round(first, 2), "D_at_0.3s": round(d03, 3), "D_end": round(dend, 3), "D_front_end": round(Df[ie], 3), "D_side_end": round(Ds[-1], 3),
                   "D_side_at_0.3s": round(Ds[i03], 3), "pass": bool(d03 >= thr and dend >= end_thr)}
    return out

def strips(path, only=None):
    """예고 동작을 0 · 0.1 · 0.2 · 0.3 · 0.5초와 끝에서 앞모습 실루엣으로 찍어 한 장에 놓는다(줄마다 한 동작). 게임 카메라, 혼 키 약 100px."""
    from PIL import ImageDraw
    rows = []
    for name, build, bones, clipfn, wind in models():
        if only and name not in only: continue
        for cn in wind:
            reset(); anim.setup_scene(); o = join(name, build()); arm = rig(o, bones); C = clipfn()
            for k, (keys, interp, loop, ev) in C.items(): anim.clip(arm, k, keys, interp)
            big = 2.7 if name != "mote" else 1.0; cz = 0.9 if name != "mote" else 0.28
            setup_render(big, (0, 0, cz), size=(110, 140), ground_size=8); black_everything(); bpy.context.scene.cycles.samples = 4
            ad = arm.animation_data; ad.action = None; last = int(max(s.frame_end for t in ad.nla_tracks if t.name == cn for s in t.strips))
            for t in ad.nla_tracks: t.mute = t.name != cn
            fr = [0, 6, 12, 18, 30, last]; tiles = []
            for f in fr:
                bpy.context.scene.frame_set(min(f, last)); p = os.path.join(OUT, "previews", "_tl.png"); bpy.context.scene.render.filepath = p; bpy.ops.render.render(write_still=True)
                im = Image.open(p).convert("RGB"); d = ImageDraw.Draw(im); d.text((4, 3), f"{f / FPS:.2f}s", fill=(120, 40, 30)); tiles.append(im)
            row = Image.new("RGB", (110 * len(tiles), 140), (237, 235, 224)); [row.paste(t, (i * 110, 0)) for i, t in enumerate(tiles)]; rows.append((f"{name}:{cn}", row))
    W = Image.new("RGB", (110 * 6, 140 * len(rows)), (237, 235, 224))
    for i, (lab, r) in enumerate(rows): W.paste(r, (0, i * 140)); ImageDraw.Draw(W).text((4, i * 140 + 126), lab, fill=(30, 30, 40))
    W.save(path); os.remove(os.path.join(OUT, "previews", "_tl.png"))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--strips": strips(sys.argv[2]); sys.exit()
    rep = {}
    for name, build, bones, clipfn, wind in models():
        res = measure(name, build, bones, clipfn, wind); rep[name] = summarize(res); print(name, json.dumps(rep[name], ensure_ascii=False))
    json.dump(rep, open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "souls", "_tele_check.json"), "w"), ensure_ascii=False, indent=1)

