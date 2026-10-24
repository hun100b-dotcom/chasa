"""애니메이션 공용 도구(Blender 5.x). 뼈대에 키프레임을 찍고, GLB에 '뼈대(스킨)+동작'을 함께 내보내고, 다시 읽어 검증한다.
왜 필요한가: 이전 영웅 GLB는 뼈대가 내보내기에서 빠져 정지 모델이었다(내보낼 때 부모인 아마추어를 선택하지 않았기 때문).
이제 export_rig()는 아마추어와 메시를 함께 골라 내보내고, verify()가 파일을 직접 열어 뼈대·동작 수를 센다.
좌표: 포즈는 '캐릭터 기준 세계축'으로 적는다. +X=캐릭터 왼쪽, -Y=앞, +Z=위. 회전은 XYZ 순서(X 먼저, 마지막에 Z).
 - 아래로 늘어진 팔·다리: rx가 음수면 앞으로 간다.  - 위로 솟은 몸통·머리: rx가 양수면 앞으로 숙인다.
 - rz가 양수면 위에서 볼 때 반시계(앞이 캐릭터 왼쪽으로)."""
import bpy, math, json, os, struct
from mathutils import Vector, Euler, Matrix

FPS = 60

def setup_scene():
    sc = bpy.context.scene; sc.render.fps = FPS
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"

def _rest3(pb): return pb.bone.matrix_local.to_3x3()

def _apply(pb, spec):
    """spec: {'r':(rx,ry,rz)도, 'l':(x,y,z)m, 's':(sx,sy,sz)} — 세계축 기준 값을 뼈 고유축으로 바꿔 넣는다."""
    m = _rest3(pb); mi = m.inverted()
    r = spec.get("r", (0, 0, 0)); R = Euler([math.radians(a) for a in r], "XYZ").to_matrix()
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (mi @ R @ m).to_quaternion()
    pb.location = mi @ Vector(spec.get("l", (0, 0, 0)))
    s = spec.get("s", (1, 1, 1)); loc = [1, 1, 1]
    for i in range(3):   # 뼈 고유축 i가 가장 가까운 세계축을 찾아 그 배율을 쓴다
        col = m.col[i]; ax = max(range(3), key=lambda k: abs(col[k])); loc[i] = s[ax]
    pb.scale = tuple(loc)

def clip(arm, name, keys, interp="LINEAR"):
    """keys=[(프레임, {뼈이름: spec})]. 안 적은 뼈는 기본 자세로 둔다. 끝나면 NLA 트랙에 넣어 따로 내보내지게 한다."""
    ad = arm.animation_data or arm.animation_data_create()
    act = bpy.data.actions.new(name); ad.action = act
    bpy.context.preferences.edit.keyframe_new_interpolation_type = interp
    for f, spec in keys:
        for pb in arm.pose.bones:
            _apply(pb, spec.get(pb.name, {}))
            pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f); pb.keyframe_insert("scale", frame=f)
    for pb in arm.pose.bones: _apply(pb, {})
    f0, f1 = keys[0][0], keys[-1][0]
    ad.action = None
    tr = ad.nla_tracks.new(); tr.name = name
    st = tr.strips.new(name, int(f0), act); st.name = name
    return {"name": name, "frames": int(f1 - f0) + 1, "length_sec": round((f1 - f0) / FPS, 3)}

def export_rig(arm, path):
    """아마추어와 그 자식 메시를 함께 골라 내보낸다(스킨+동작 포함)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for x in bpy.context.view_layer.objects: x.select_set(False)
    arm.select_set(True); bpy.context.view_layer.objects.active = arm
    for c in arm.children_recursive: c.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=False, export_yup=True, export_materials="EXPORT",
                              export_skins=True, export_animations=True, export_animation_mode="NLA_TRACKS", export_force_sampling=True,
                              export_cameras=False, export_lights=False, export_extras=True)

def verify(path):
    """GLB를 직접 열어 뼈대(스킨)·동작·글로벌 정보를 센다."""
    b = open(path, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n])
    skins = j.get("skins", []); anims = j.get("animations", [])
    return {"file": os.path.basename(path), "skins": len(skins), "joints": len(skins[0]["joints"]) if skins else 0, "animations": [a.get("name") for a in anims],
            "size_kb": round(len(b) / 1024)}

def sheet(arm, clipname, frames, path, ortho=3.2, center=(0, 0, 1.0), cell=(220, 280)):
    """동작 중 고른 프레임들을 나란히 그려 한 장으로 만든다(눈으로 확인용). 렌더 설정은 호출 전에 setup_render로."""
    from PIL import Image
    ad = arm.animation_data; ad.action = None
    tr = [t for t in ad.nla_tracks if t.name == clipname][0]
    for t in ad.nla_tracks: t.mute = t.name != clipname
    imgs = []
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = cell
    sc.cycles.samples = 6
    for f in frames:
        sc.frame_set(f); p = path + f"_{f}.png"; sc.render.filepath = p; bpy.ops.render.render(write_still=True); imgs.append(Image.open(p).convert("RGB"))
    W = Image.new("RGB", (cell[0] * len(imgs), cell[1] + 0), "#000")
    for i, im in enumerate(imgs): W.paste(im, (i * cell[0], 0))
    for t in ad.nla_tracks: t.mute = False
    for f in frames: os.remove(path + f"_{f}.png")
    W.save(path + ".png"); return path + ".png"
