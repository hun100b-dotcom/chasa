# =============================================================================
# glb_split_prims.py — 뼈대(skin)가 있는 GLB 의 "재질별 조각(primitive)"을 각각 따로 된 메시로 나눠 다시 저장한다.
#
# 왜 필요한가
#   Blender 는 재질이 여러 개인 몸 하나를 "메시 1개 + 조각 7개"로 내보낸다. Unity 의 glTFast 6.10.1 은
#   이런 뼈대 메시를 들여올 때 뼈 가중치 계산 작업(SortAndNormalizeBoneWeightsJob)끼리 부딪혀
#   InvalidOperationException 을 내고 모델 읽기에 실패한다(2026-10-25 PC 확인).
#   조각마다 메시를 따로 만들고 같은 뼈대를 쓰게 하면 그대로 읽힌다(뼈 16·동작 9개 정상).
#   데이터(정점·뼈·동작)는 한 바이트도 바꾸지 않고, 목차(JSON)의 묶는 방식만 바꾼다.
#
# 사용법: python tools/glb_split_prims.py <원본.glb> <저장할.glb>
# =============================================================================
import json
import struct
import sys

src, dst = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read()
jl = struct.unpack('<I', d[12:16])[0]                 # JSON 덩어리 길이
j = json.loads(d[20:20 + jl])
binchunk = d[20 + jl:]                                # 바이너리 덩어리(정점 등)는 그대로 옮긴다

old = j['meshes'][0]
if len(old['primitives']) < 2:
    sys.exit('조각이 1개뿐이라 나눌 필요가 없습니다')
# 조각 하나 = 메시 하나
j['meshes'] = [{'name': f"{old.get('name', 'm')}_{i}", 'primitives': [p]} for i, p in enumerate(old['primitives'])]
# 원래 메시를 달고 있던 노드는 빈 묶음 노드로 두고, 그 밑에 조각 노드들을 같은 뼈대(skin)로 붙인다
host = next(i for i, n in enumerate(j['nodes']) if n.get('mesh') == 0)
skin = j['nodes'][host]['skin']
kids = []
for i in range(len(j['meshes'])):
    j['nodes'].append({'name': f"{j['nodes'][host]['name']}_part{i}", 'mesh': i, 'skin': skin})
    kids.append(len(j['nodes']) - 1)
del j['nodes'][host]['mesh']
del j['nodes'][host]['skin']
j['nodes'][host]['children'] = j['nodes'][host].get('children', []) + kids

js = json.dumps(j, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
js += b' ' * ((4 - len(js) % 4) % 4)                  # GLB 규칙: 4바이트 단위로 맞춘다(공백 채움)
out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + len(binchunk)) + struct.pack('<I4s', len(js), b'JSON') + js + binchunk
open(dst, 'wb').write(out)
print('메시', len(j['meshes']), '노드', len(j['nodes']))
