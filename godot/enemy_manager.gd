# =============================================================================
# enemy_manager.gd — 적 무리 관리: 생성, 겹침 방지, 부활, 클릭 대상 찾기 (src/enemy.ts)
# =============================================================================
class_name EnemyManager
extends Node3D

var list: Array[Enemy] = []

func spawn_all(player_pos: Vector3) -> void:
	for i in Config.ENEMY_COUNT:
		# 플레이어 둘레에 균등 배치
		var pos := _spawn_point(player_pos, float(i) / Config.ENEMY_COUNT * TAU + 0.4)
		var e := Enemy.new("capsule" if i % 2 == 0 else "box", pos)
		list.append(e)
		add_child(e)

func _spawn_point(center: Vector3, angle: float) -> Vector3:
	var lim := Config.ARENA_HALF_SIZE - 1.0
	return Vector3(
		clampf(center.x + cos(angle) * Config.ENEMY_SPAWN_DISTANCE, -lim, lim), 0,
		clampf(center.z + sin(angle) * Config.ENEMY_SPAWN_DISTANCE, -lim, lim))

func tick(dt: float, player_pos: Vector3, player_radius: float) -> void:
	for e in list:
		e.tick(dt, player_pos)
		if not e.alive and e.respawn_ready:
			e.respawn(_spawn_point(player_pos, randf() * TAU))
	if dt <= 0.0:
		return  # 히트스톱 중엔 밀어내기 계산도 멈춘다
	# 서로 겹치지 않게 밀어낸다 (적끼리 + 플레이어 몸통)
	var alive_list: Array[Enemy] = list.filter(func(x: Enemy) -> bool: return x.alive)
	for i in alive_list.size():
		var a := alive_list[i]
		for j in range(i + 1, alive_list.size()):
			var b := alive_list[j]
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

func pick(ray_origin: Vector3, ray_dir: Vector3, ground, near_radius: float) -> Enemy:
	# 1순위: 광선이 적 몸에 직접 닿음. 2순위: 바닥 클릭 지점 근처의 가장 가까운 적.
	# 2순위가 있는 이유: 움직이는 작은 도형을 정확히 누르기 어렵기 때문 (조작 관대함)
	for e in list:
		if e.ray_hits_body(ray_origin, ray_dir):
			return e
	if ground == null:
		return null
	var best: Enemy = null
	var best_d := near_radius
	for e in list:
		if not e.alive:
			continue
		var d := Vector2(e.position.x - ground.x, e.position.z - ground.z).length()
		if d <= best_d:
			best_d = d
			best = e
	return best
