# 3막 ⑤ 갯마을 땅·배치 (코드팀 전달용, 아트 2026-10-25)
생성: `python3 tools/art3d/terrain_act3.py` → `assets3d/terrain_act3_east/` · 미리보기 `assets3d/previews/act3_east_terrain_map.png`
배치: `python3 tools/art3d/place_act3_east.py` → `assets3d/layouts/act3_east_layout.json`(440개), `act3_east_report.json`(겹침 0, 못 놓음 0, 옮긴 10곳 walk_snap)

## 땅
- 월드 x 768~1280, y 0~1024 (512×1024 m), `origin_m [768,0]`, 높이맵 513×1025, 행 0 = 남쪽(2막과 같은 약속).
- **높이 약속**: 썰물 물높이 −0.5, 밀물 +0.6(`terrain.json`의 `tide_low_m`, `tide_high_m`), 깊은 바다 바닥 −2.5, 갯벌·여울 바닥 0.0(썰물에 드러남), 포구·염전 1.25~1.4, 곶 3.5, 보스 마당(B-09 3.0, B-10 0.0).
- 높이 범위 −3 ~ 10 m (`height_min_m`, `height_max_m`).
- 서낭당 SH3-1과 보스 마당 둘레 기울기 0.
- 층 뜻: dirt=마른 흙·갯벌 흙, grass=갯풀, gravel=자갈·바위, paddy(A)=소금 흰색, splat_b G=물거품(썰물선 띠), B=젖은 갯벌(밀물에 잠기는 높이). leaf(R)는 ⑥ 눈용이라 ⑤에서는 0.

## 물판
- `tide_water.glb`(64×64 m)를 바다가 있는 칸(56곳)에 깔아 두었다. 기준 z=−0.5(썰물). **코드가 25분 주기로 −0.5↔+0.6 사이를 오르내리게 해 달라**(월드 시계 0분에 썰물 시작).
- 선창(`harbor_pier`) 널판은 z 1.5로 밀물에도 잠기지 않는다. 배(`harbor_boat`)는 기준 z 0.1, 흔들림·물 높이 따라 올림은 코드.
- 난파선 갑판·여울 바위는 z 0.0 바닥에 앉아 있어 썰물(−0.5)에 드러나고 밀물(+0.6)에 잠긴다 → B-10 썰물 밤 규칙과 자연스럽게 맞는다.

## 아직 안 한 것
⑥ 도성 아랫마을 땅(−640~0, 0~640), 해안 길 띠(y −128~0, 벼랑·갯골 세 곳), 큰 다리 배치(`bridge_deck`·`bridge_pier`), 3막 보스 4종.
