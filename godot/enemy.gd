# =============================================================================
# enemy.gd — 적 (캡슐/박스 샌드백). AI는 "플레이어를 향해 걸어온다"가 전부. (src/enemy.ts)
# 이 단계의 목적은 "때리는 맛"이므로, 적은 맞아주는 역할만 잘 하면 된다.
# =============================================================================
class_name Enemy
extends Node3D

var radius := Config.ENEMY_RADIUS
var height := Config.ENEMY_HEIGHT
var vel := Vector3.ZERO     # 넉백 속도. 맞으면 크게 세팅되고 마찰로 줄어든다
var hp := Config.ENEMY_MAX_HP
var alive := true
var stun := 0.0             # 남은 기절 시간 (기절 중엔 쫓아오지 않음)
var pulled := false         # 견인으로 끌려오는 중인가
var respawn_ready := false  # 죽은 뒤 부활해도 되는가

var _speed := 0.0
var _flash := 0.0           # 1 → 0 으로 줄어드는 '맞음' 번쩍임
var _death_t := 0.0
var _spawn_t := 0.0         # 등장 팝인 연출용
var _pulled_t := 0.0        # 끌려오는 시간 (안전장치)
var _body: MeshInstance3D
var _mat: StandardMaterial3D

func _init(shape: String, start_pos: Vector3) -> void:
	_speed = Config.ENEMY_SPEED * (1.0 + randf_range(-Config.ENEMY_SPEED_VARIANCE, Config.ENEMY_SPEED_VARIANCE))
	# 도형 두 종류를 섞어 "다른 적"처럼 보이게 (에셋 없이 구분하는 가장 싼 방법)
	_body = MeshInstance3D.new()
	if shape == "capsule":
		var c := CapsuleMesh.new()
		c.radius = radius * 0.85
		c.height = height
		_body.mesh = c
	else:
		var b := BoxMesh.new()
		b.size = Vector3(radius * 1.9, height, radius * 1.9)
		_body.mesh = b
	_mat = U.matte(Color("d9534f") if shape == "capsule" else Color("c2692f"))
	_mat.emission_enabled = true
	_mat.emission = Color.WHITE
	_mat.emission_energy_multiplier = 0.0  # 평소엔 안 빛나고, 맞으면 올렸다 내린다
	_body.material_override = _mat
	_body.position.y = height / 2.0  # 발바닥이 바닥(y=0)에 오게
	add_child(_body)
	position = start_pos

func get_head_position() -> Vector3:
	return Vector3(position.x, height + 0.3, position.z)

func take_hit(damage: int, dir: Vector3, knockback: float, stun_time: float) -> bool:
	# 한 대 맞음. 이번 타격으로 죽으면 true
	hp -= damage
	_flash = 1.0
	stun = maxf(stun, stun_time)
	pulled = false  # 끌려오던 중에 맞으면 견인 취소
	# 속도를 '덮어쓴다': 연타해도 무한히 빨라지지 않고 마지막 타격 방향으로 날아간다
	vel = dir * knockback
	if hp <= 0:
		alive = false
		_death_t = 0.0
		respawn_ready = false
		vel *= Config.ENEMY_KILL_KNOCKBACK_MULT
		return true
	return false

func start_pulled() -> void:
	pulled = true
	_pulled_t = 0.0
	vel = Vector3.ZERO

func respawn(at: Vector3) -> void:
	hp = Config.ENEMY_MAX_HP
	alive = true
	respawn_ready = false
	stun = 0.0
	pulled = false
	_flash = 0.0
	_spawn_t = 0.0
	vel = Vector3.ZERO
	position = at
	_apply_visual()

func tick(dt: float, player_pos: Vector3) -> void:
	if not alive:
		_tick_dead(dt)
		return
	_spawn_t += dt
	_flash = maxf(0.0, _flash - dt / Config.ENEMY_FLASH_TIME)
	if pulled:
		_tick_pulled(dt, player_pos)
	else:
		# 넉백: 속도만큼 이동, 마찰로 지수 감속 (프레임레이트와 무관)
		position += vel * dt
		vel *= exp(-Config.ENEMY_KNOCKBACK_FRICTION * dt)
		stun -= dt
		if stun <= 0.0:
			_chase(dt, player_pos)
	_clamp_to_arena()
	_apply_visual()

func _chase(dt: float, player_pos: Vector3) -> void:
	# 가장 단순한 AI: 플레이어 쪽으로 걷다가 가까우면 멈춘다
	var d := Vector2(player_pos.x - position.x, player_pos.z - position.z)
	var dist := d.length()
	if dist > Config.ENEMY_STOP_DISTANCE:
		position.x += d.x / dist * _speed * dt
		position.z += d.y / dist * _speed * dt

func _tick_pulled(dt: float, player_pos: Vector3) -> void:
	# 견인: 플레이어 앞 STOP_DISTANCE 까지 빠르게 날아온다
	_pulled_t += dt
	var d := Vector2(player_pos.x - position.x, player_pos.z - position.z)
	var dist := d.length()
	var step := Config.PULL_DRAG_SPEED * dt
	if dist - step <= Config.PULL_STOP_DISTANCE or _pulled_t > 1.0:
		# 도착! 멈추고 멍해진다 (도착 연출은 Player 가 pulled 꺼진 걸 보고 처리)
		var keep := Config.PULL_STOP_DISTANCE
		if dist > keep:
			position.x = player_pos.x - d.x / dist * keep
			position.z = player_pos.z - d.y / dist * keep
		pulled = false
		stun = Config.PULL_STUN
		_flash = 1.0
		return
	position.x += d.x / dist * step
	position.z += d.y / dist * step

func _tick_dead(dt: float) -> void:
	# 죽은 뒤: 마지막 넉백으로 날아가다 → 쪼그라들어 사라짐 → 부활 대기
	_death_t += dt
	_flash = maxf(0.0, _flash - dt / Config.ENEMY_FLASH_TIME)
	position += vel * dt
	vel *= exp(-Config.ENEMY_KNOCKBACK_FRICTION * dt)
	_clamp_to_arena()
	_apply_visual()
	if _death_t >= Config.ENEMY_RESPAWN_DELAY:
		respawn_ready = true

func _clamp_to_arena() -> void:
	var lim := Config.ARENA_HALF_SIZE - radius
	position.x = clampf(position.x, -lim, lim)
	position.z = clampf(position.z, -lim, lim)

func _apply_visual() -> void:
	_mat.emission_energy_multiplier = _flash * 0.9
	# 등장 팝인(0→1) 또는 죽은 뒤 쪼그라듦(1→0)
	var base := U.ease_out_quad(clampf(_spawn_t / Config.ENEMY_SPAWN_POP_TIME, 0.0, 1.0))
	if not alive:
		base = 1.0 - clampf((_death_t - Config.ENEMY_DEATH_HOLD) / Config.ENEMY_DEATH_SHRINK, 0.0, 1.0)
	# 맞은 순간: 옆으로 넓어지고 키가 줄어드는 찌그러짐 (타격의 무게감)
	var sx := 1.0 + Config.ENEMY_SQUASH * _flash
	var sy := 1.0 - Config.ENEMY_SQUASH * 0.8 * _flash
	scale = Vector3(maxf(0.001, base * sx), maxf(0.001, base * sy), maxf(0.001, base * sx))

func ray_hits_body(origin: Vector3, dir: Vector3) -> bool:
	# 마우스 광선이 몸통(세로 원기둥으로 근사)을 지나가나?
	# 광선 위에서 몸통 중심 높이와 가장 가까운 지점까지의 수평 거리로 판단한다.
	if not alive:
		return false
	var center := position + Vector3(0, height / 2.0, 0)
	var t := (center - origin).dot(dir)
	var closest := origin + dir * t
	if absf(closest.y - center.y) > height / 2.0 + 0.2:
		return false
	return Vector2(closest.x - center.x, closest.z - center.z).length() <= radius * 1.1
