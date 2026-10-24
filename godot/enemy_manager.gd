# =============================================================================
# enemy_manager.gd — 적 무리 관리: 생성, 겹침 방지, 부활, 클릭 대상 찾기, 사나운 적 소환
# =============================================================================
class_name EnemyManager
extends Node3D

var list: Array[Enemy] = []
## 적의 공격이 닿았을 때 부를 함수. main 이 "플레이어가 아파한다"를 연결해 준다.
## 왜 여기서 한 번에 넘기나? 적이 새로 생길 때마다(부활·소환) 빠짐없이 연결되게 하려고.
var on_attack: Callable

func spawn_all(player_pos: Vector3) -> void:
	for i in Config.ENEMY_COUNT:
		# 플레이어 둘레에 균등 배치
		var pos := _spawn_point(player_pos, float(i) / Config.ENEMY_COUNT * TAU + 0.4)
		_add(Enemy.new("capsule" if i % 2 == 0 else "box", pos))

func _add(e: Enemy) -> Enemy:
	e.on_attack = on_attack
	list.append(e)
	add_child(e)
	return e

func spawn_fierce(at: Vector3) -> Enemy:
	# 원념 얼룩 3개가 겹친 자리에서 '사나운 적'이 솟아난다 (P-010)
	var e := _add(Enemy.new("capsule", at))
	e.make_fierce()
	return e

func reset_all(player_pos: Vector3) -> void:
	# 플레이어가 쓰러졌을 때: 소환된 추가 적은 지우고, 기본 적은 새 혼으로 다시 배치
	for e in list.duplicate():
		if e.extra:
			list.erase(e)
			e.queue_free()
	for i in list.size():
		list[i].respawn(_spawn_point(player_pos, float(i) / list.size() * TAU + 0.4))

func _spawn_point(center: Vector3, angle: float) -> Vector3:
	var lim := Config.ARENA_HALF_SIZE - 1.0
	return Vector3(
		clampf(center.x + cos(angle) * Config.ENEMY_SPAWN_DISTANCE, -lim, lim), 0,
		clampf(center.z + sin(angle) * Config.ENEMY_SPAWN_DISTANCE, -lim, lim))

func tick(dt: float, player_pos: Vector3, player_radius: float) -> void:
	# duplicate(): 도는 도중에 목록에서 빼도(추가 적 제거) 꼬이지 않게 사본으로 돈다
	for e in list.duplicate():
		e.tick(dt, player_pos)
		if e.state == Enemy.S.GONE and e.respawn_ready:
			if e.extra:
				# 소환된 적은 한 번 처리하면 끝 (계속 늘어나지 않게)
				list.erase(e)
				e.queue_free()
			else:
				e.respawn(_spawn_point(player_pos, randf() * TAU))
	if dt <= 0.0:
		return  # 히트스톱 중엔 밀어내기 계산도 멈춘다
	# 서로 겹치지 않게 밀어낸다 (적끼리 + 플레이어 몸통). 무릎 꿇은 적도 몸은 있으니 포함
	var bodies: Array[Enemy] = list.filter(func(x: Enemy) -> bool: return x.state != Enemy.S.GONE)
	for i in bodies.size():
		var a := bodies[i]
		for j in range(i + 1, bodies.size()):
			var b := bodies[j]
			if a.pulled or b.pulled:
				continue  # 끌려오는 중엔 간섭 없음
			_separate(a, b.position, a.radius + b.radius, 0.5, b)
		if not a.pulled:
			_separate(a, player_pos, a.radius + player_radius, 1.0, null)

func _separate(a: Enemy, other_pos: Vector3, min_dist: float, share: float, other: Enemy) -> void:
	var d := Vector2(a.position.x - other_pos.x, a.position.z - other_pos.z)
	var dist := d.length()
	if dist >= min_dist or dist < 1e-5:
		return
	var push := (min_dist - dist) * share
	var n := d / dist
	a.position.x += n.x * push
	a.position.z += n.y * push
	if other:
		other.position.x -= n.x * push
		other.position.z -= n.y * push

func pick(ray_origin: Vector3, ray_dir: Vector3, ground, near_radius: float, kneel_only := false) -> Enemy:
	# 1순위: 광선이 적 몸에 직접 닿음. 2순위: 바닥 클릭 지점 근처의 가장 가까운 적.
	# 2순위가 있는 이유: 움직이는 작은 도형을 정확히 누르기 어렵기 때문 (조작 관대함)
	# kneel_only = true 면 처결 대기 중인 적만 고른다 (천도·파혼 키)
	for e in list:
		if kneel_only and not e.kneeling:
			continue
		if e.ray_hits_body(ray_origin, ray_dir):
			return e
	if ground == null:
		return null
	var best: Enemy = null
	var best_d := near_radius
	for e in list:
		if kneel_only and not e.kneeling:
			continue
		if not (e.alive or e.kneeling):
			continue
		var d := Vector2(e.position.x - ground.x, e.position.z - ground.z).length()
		if d <= best_d:
			best_d = d
			best = e
	return best
