#!/usr/bin/env python3
"""아트팀 마을 배치표(data/maps/solgogae_village_layout.json) → Unity Core 의 MapData.cs 생성.
왜 생성? 배치표는 아트가 고치고 충돌 규칙(Core)은 코드라서, 사람이 옮겨 적다 틀리지 않게 자동 변환한다.
사용: python3 tools/gen_map.py   (결과 unity/Assets/Scripts/Core/MapData.cs 는 손으로 고치지 않는다)"""
import json
d = json.load(open('data/maps/solgogae_village_layout.json', encoding='utf-8'))
code = {'stone_path': 'S', 'grass': 'G', 'dirt_road': 'D', 'yard': 'Y', 'paddy': 'P', 'stepping_stones': 'T'}
rows = [''.join(code[c] for c in r) for r in d['ground']]
out = ['// 자동 생성 파일 — tools/gen_map.py 로 만든다. 손으로 고치지 않는다.',
       '// 원본: data/maps/solgogae_village_layout.json (아트팀 마을 배치표 v1)',
       'namespace Chasa.Core', '{', '    public struct PropDef',
       '    {', '        public string Sprite; public float Ax, Ay; public int W, H;',
       '        public PropDef(string s, float ax, float ay, int w, int h) { Sprite = s; Ax = ax; Ay = ay; W = w; H = h; }', '    }', '',
       '    public static class MapData', '    {',
       f'        public const int Cols = {d["grid"]["w"]};   // 가로 칸 수 (gx)',
       f'        public const int Rows = {d["grid"]["h"]};   // 세로 칸 수 (gy)',
       '        // 땅 종류: S 돌바닥, G 풀, D 흙길, Y 마당, P 논, T 징검다리. 줄 = gy, 글자 = gx',
       '        public static readonly string[] Ground =', '        {']
out += [f'            "{r}",' for r in rows]
out += ['        };', '', '        public static readonly PropDef[] Props =', '        {']
for p in d['props']:
    out.append(f'            new PropDef("{p["sprite"]}", {p["anchor"][0]}f, {p["anchor"][1]}f, {p["w"]}, {p["h"]}),')
out += ['        };', '    }', '}', '']
open('unity/Assets/Scripts/Core/MapData.cs', 'w', encoding='utf-8').write('\n'.join(out))
print('MapData.cs 생성:', len(rows), '줄', len(d['props']), '소품')
