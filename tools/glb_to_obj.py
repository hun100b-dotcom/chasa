#!/usr/bin/env python3
"""
glb_to_obj.py — 아트팀 GLB(정적 소품)를 유니티가 바로 읽는 OBJ+MTL 로 바꾼다.

왜? 유니티는 GLB 를 기본으로 못 읽는다(glTFast 패키지가 있어야 함). 패키지 없이도 되도록 정적 소품은 OBJ 로 바꿔 넣는다.
  - 재질별 색(baseColorFactor, 선형값)을 sRGB 로 바꿔 MTL 의 Kd 에 적는다.
  - 좌표는 그대로 쓴다: 유니티 OBJ 가져오기가 X 를 뒤집어 주므로 결과적으로 거울상이 되지 않는다.
  - 뼈대(스킨)가 있는 주인공은 OBJ 로 못 옮기니 대상이 아니다(FBX/glTFast 필요).
사용: python3 tools/glb_to_obj.py <입력.glb> <출력폴더>
"""
import json, struct, sys, os
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}

def load(path):
    b = open(path, "rb").read()
    _, _, _ = struct.unpack("<4sII", b[:12])
    off = 12; js = None; bin_ = b""
    while off < len(b):
        n, t = struct.unpack("<I4s", b[off:off + 8]); d = b[off + 8: off + 8 + n]; off += 8 + n
        if t == b"JSON": js = json.loads(d)
        elif t == b"BIN\x00": bin_ = d
    return js, bin_

def acc(js, bin_, i):
    a = js["accessors"][i]; bv = js["bufferViews"][a["bufferView"]]
    dt = CT[a["componentType"]]; nc = NC[a["type"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", 0) or dt().itemsize * nc
    cnt = a["count"]
    raw = np.frombuffer(bin_, dtype=np.uint8, count=stride * (cnt - 1) + dt().itemsize * nc, offset=start)
    rows = [np.frombuffer(raw[k * stride: k * stride + dt().itemsize * nc].tobytes(), dtype=dt) for k in range(cnt)]
    return np.array(rows).reshape(cnt, nc)

def srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055

def node_matrix(n):
    if "matrix" in n: return np.array(n["matrix"]).reshape(4, 4).T
    t = np.array(n.get("translation", [0, 0, 0])); r = n.get("rotation", [0, 0, 0, 1]); s = np.array(n.get("scale", [1, 1, 1]))
    x, y, z, w = r
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4); M[:3, :3] = R * s; M[:3, 3] = t
    return M

def convert(src, outdir):
    js, bin_ = load(src)
    name = os.path.splitext(os.path.basename(src))[0]
    mats = js.get("materials", [])
    lines = ["# from %s" % os.path.basename(src), "mtllib %s.mtl" % name]
    base = 1
    used = {}
    def walk(ni, parent):
        nonlocal base
        n = js["nodes"][ni]; M = parent @ node_matrix(n)
        if "mesh" in n:
            for pi, p in enumerate(js["meshes"][n["mesh"]]["primitives"]):
                pos = acc(js, bin_, p["attributes"]["POSITION"]).astype(float)
                pos = (np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3]
                nrm = None
                if "NORMAL" in p["attributes"]:
                    nrm = acc(js, bin_, p["attributes"]["NORMAL"]).astype(float) @ np.linalg.inv(M[:3, :3]).T
                    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
                idx = acc(js, bin_, p["indices"]).reshape(-1) if "indices" in p else np.arange(len(pos))
                mi = p.get("material", 0); mn = "m%d" % mi; used[mn] = mi
                lines.append("o %s_%d_%d" % (name, ni, pi)); lines.append("usemtl " + mn)
                for v in pos: lines.append("v %.5f %.5f %.5f" % tuple(v))
                if nrm is not None:
                    for v in nrm: lines.append("vn %.4f %.4f %.4f" % tuple(v))
                for k in range(0, len(idx) - 2, 3):
                    a, b, c = (int(idx[k + j]) + base for j in range(3))
                    if nrm is not None: lines.append("f %d//%d %d//%d %d//%d" % (a, a, b, b, c, c))
                    else: lines.append("f %d %d %d" % (a, b, c))
                base += len(pos)
        for c in n.get("children", []): walk(c, M)
    for r in js["scenes"][js.get("scene", 0)]["nodes"]: walk(r, np.eye(4))
    mtl = []
    for mn, mi in used.items():
        f = mats[mi].get("pbrMetallicRoughness", {}).get("baseColorFactor", [0.8, 0.8, 0.8, 1])
        mtl += ["newmtl " + mn, "Kd %.4f %.4f %.4f" % tuple(srgb(x) for x in f[:3]), "Ka 0 0 0", "Ks 0 0 0", "d 1", ""]
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, name + ".obj"), "w").write("\n".join(lines) + "\n")
    open(os.path.join(outdir, name + ".mtl"), "w").write("\n".join(mtl))
    return name, len(used)

if __name__ == "__main__":
    print(*convert(sys.argv[1], sys.argv[2]))
