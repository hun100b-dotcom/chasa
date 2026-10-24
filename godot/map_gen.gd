# =============================================================================
# map_gen.gd — 구역제 맵 1차 생성기 (TASKS P1-017)
#
# 원칙(TASKS): 뼈대 지형은 손으로, 내부 배치만 ProcGen.
#   왜? 전부 자동 생성하면 "오늘 밤 어디까지 갈 것인가"라는 전략이 무의미해진다.
#   → 구역의 순서·거리·보상 배율은 config 표(손작업), 구역 안의 혼 위치·종류만 시드 무작위.
# 같은 시드는 항상 같은 맵 → 버그 재현과 밸런스 시뮬(P1-040)에 필요.
# =============================================================================
class_name MapGen
extends RefCounted

## 맵 생성. 반환: Array[Dictionary] 구역 목록
##   { name, ring, center(Vector3), radius, reward_mult, souls: [ {pos, soul} ] }
static func generate(seed_value: int) -> Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var zones: Array = []
	for ring in Config.MAP_ZONE_NAMES.size():
		# 구역은 한 방향(동쪽 +x)으로 이어진 길이 아니라, 고리마다 방향만 시드로 흔든다
		# → 뼈대(거리·순서)는 고정, 가는 방향의 모양만 달라진다
		var angle := rng.randf_range(-0.6, 0.6) + float(ring) * 0.35
		var dist: float = Config.MAP_ZONE_DIST[ring]
		var center := Vector3(cos(angle) * dist, 0, sin(angle) * dist)
		var zone := {
			"name": Config.MAP_ZONE_NAMES[ring], "ring": ring, "center": center,
			"radius": Config.MAP_ZONE_RADIUS,
			"reward_mult": 1.0 + Config.MAP_REWARD_PER_RING * ring,
			"souls": _place_souls(rng, center, ring),
		}
		zones.append(zone)
	return zones

static func _place_souls(rng: RandomNumberGenerator, center: Vector3, ring: int) -> Array:
	var souls: Array = []
	var want: int = Config.MAP_SOULS_PER_ZONE[ring]
	var lump_p: float = Config.MAP_LUMP_BASE + Config.MAP_LUMP_PER_RING * ring
	var tries := 0
	while souls.size() < want and tries < want * 30:
		tries += 1
		# 원 안에 고르게 흩뿌리기: 반지름은 sqrt 를 써야 중심에 몰리지 않는다
		var a := rng.randf() * TAU
		var r := sqrt(rng.randf()) * (Config.MAP_ZONE_RADIUS - 2.0)
		var pos := center + Vector3(cos(a) * r, 0, sin(a) * r)
		var ok := true
		for s in souls:
			if (s.pos as Vector3).distance_to(pos) < Config.MAP_MIN_SOUL_GAP:
				ok = false
				break
		if not ok:
			continue
		var kind: String = "lump" if rng.randf() < lump_p else ["fresh", "year", "old"][rng.randi() % 3]
		souls.append({"pos": pos, "soul": kind})
	return souls

## 허브에서 가장 먼 구역까지의 고리 번호 → "어디까지 갈 것인가"의 선택지 수
static func max_ring() -> int:
	return Config.MAP_ZONE_NAMES.size() - 1
