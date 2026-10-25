#!/usr/bin/env python3
"""새 땅(아트 산출물) → 유니티 Resources/Terrain 으로 넣기.
사용:  python3 tools/build_terrain_data.py <땅 폴더>        # 아트가 준 폴더(terrain.json, heightmap.png, splat_a.png ...)
       python3 tools/build_terrain_data.py --demo <폴더>     # 시험용 완만한 언덕 땅을 그 폴더에 만든다(Resources 에는 넣지 않음)
형식 약속은 docs/TERRAIN-FORMAT.md. PNG 는 유니티가 '읽을 수 있는 그림'으로 안 줘서 .bytes 로 이름만 바꿔 넣는다.
"""
import json, math, os, shutil, struct, sys, zlib

OUT = os.path.join(os.path.dirname(__file__), '..', 'unity', 'Assets', 'Resources', 'Terrain')
REQUIRED = ['terrain.json', 'heightmap.png', 'splat_a.png']
OPTIONAL = ['splat_b.png'] + ['layer_%s.png' % n for n in ('dirt', 'grass', 'gravel', 'paddy', 'leaf')]


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        raise SystemExit('PNG 가 아니다: ' + path)
    return struct.unpack('>II', head[16:24])


def write_png(path, w, h, rows):  # rows: bytes 행 목록(RGBA 4바이트 x w)
    raw = b''.join(b'\x00' + r for r in rows)
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def make_demo(folder):
    os.makedirs(folder, exist_ok=True)
    size, hres, sres, hmin, hmax = 640.0, 641, 320, 0.0, 6.0
    meta = dict(size=size, height_res=hres, splat_res=sres, height_min_m=hmin, height_max_m=hmax, layer_tile_m=[6, 6, 6, 6, 6])
    json.dump(meta, open(os.path.join(folder, 'terrain.json'), 'w'), indent=1)
    def hgt(x, z):  # 완만한 언덕 몇 개(최대 약 3m). 서낭당(시작 근처)은 평평하게 눌러 둔다
        v = 1.5 + 0.9 * math.sin(x / 70.0) * math.cos(z / 90.0) + 0.6 * math.sin((x + z) / 45.0)
        return max(0.0, min(hmax, v))
    rows = []
    for j in range(hres):
        r = bytearray()
        for i in range(hres):
            v = int((hgt(i * size / (hres - 1), j * size / (hres - 1)) - hmin) / (hmax - hmin) * 65535)
            r += bytes((v >> 8, v & 255, 0, 255))
        rows.append(bytes(r))
    write_png(os.path.join(folder, 'heightmap.png'), hres, hres, rows)
    ra, rb = [], []
    for j in range(sres):
        a, b = bytearray(), bytearray()
        for i in range(sres):
            x, z = i * size / (sres - 1), j * size / (sres - 1)
            road = max(0.0, 1 - abs((x - z * 0.6) - 100) / 6.0)          # 비스듬한 흙길
            paddy = 1.0 if (x > 300 and z < 200 and math.sin(x / 9.0) > -0.2) else 0.0   # 논
            gravel = max(0.0, 1 - abs(z - 330) / 5.0) * 0.8                # 냇가 자갈
            leaf = 0.7 if (x < 200 and z > 400) else 0.0                   # 숲 낙엽
            grass = max(0.0, 1 - road - paddy - gravel - leaf)
            a += bytes((int(road * 255), int(grass * 255), int(gravel * 255), int(paddy * 255)))
            b += bytes((int(leaf * 255), 0, 0, 255))
        ra.append(bytes(a)); rb.append(bytes(b))
    write_png(os.path.join(folder, 'splat_a.png'), sres, sres, ra)
    write_png(os.path.join(folder, 'splat_b.png'), sres, sres, rb)
    print('시험용 땅을 만들었다:', folder)


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == '--demo':
        return make_demo(args[1])
    if len(args) != 1:
        raise SystemExit(__doc__)
    src = args[0]
    for f in REQUIRED:
        if not os.path.exists(os.path.join(src, f)):
            raise SystemExit('빠진 파일: ' + f)
    meta = json.load(open(os.path.join(src, 'terrain.json')))
    hw, hh = png_size(os.path.join(src, 'heightmap.png'))
    if hw != meta['height_res'] or hh != meta['height_res']:
        raise SystemExit('heightmap.png 크기 %dx%d 가 terrain.json height_res %d 와 다르다' % (hw, hh, meta['height_res']))
    sw, sh = png_size(os.path.join(src, 'splat_a.png'))
    if sw != meta['splat_res'] or sh != meta['splat_res']:
        raise SystemExit('splat_a.png 크기 %dx%d 가 splat_res %d 와 다르다' % (sw, sh, meta['splat_res']))
    if os.path.exists(os.path.join(src, 'splat_b.png')) and png_size(os.path.join(src, 'splat_b.png')) != (sw, sh):
        raise SystemExit('splat_b.png 는 splat_a.png 와 같은 크기여야 한다')
    os.makedirs(OUT, exist_ok=True)
    shutil.copy(os.path.join(src, 'terrain.json'), os.path.join(OUT, 'terrain.json'))
    n = 1
    for f in REQUIRED[1:] + OPTIONAL:
        p = os.path.join(src, f)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OUT, f[:-4] + '.bytes')); n += 1
    print('넣은 파일 %d개 -> %s (높이 %.1f~%.1fm, 한 변 %.0fm)' % (n, os.path.normpath(OUT), meta['height_min_m'], meta['height_max_m'], meta['size']))


if __name__ == '__main__':
    main()
