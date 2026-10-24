# =============================================================================
# enemy.gd — 적(떠도는 혼). 이제 "맞아주는 샌드백"이 아니라 실제로 공격하고,
#            맺힘이 0이 되면 죽지 않고 무릎 꿇어 '처결 대기'에 든다. (COMBAT-SPEC 1-1, 1-2)
#
# 상태(한 번에 하나만):
#   ACTIVE  : 싸우는 중 (쫓아오기 / 예비동작 / 공격)
#   KNEEL   : 처결 대기. 타이머가 흐른다. 플레이어가 천도 또는 파혼을 고른다
#   SENDING : 천도 캐스팅을 받는 중 (타이머 멈춤)
#   GONE    : 천도로 떠났거나 파혼으로 터짐 → 잠시 뒤 새 혼으로 다시 등장
# =============================================================================
class_name Enemy
extends Node3D

enum S { ACTIVE, KNEEL, SENDING, GONE }

var radius := Config.ENEMY_RADIUS
var height := Config.ENEMY_HEIGHT
var vel := Vector3.ZERO      # 넉백 속도
var state := S.ACTIVE
var soul := "fresh"          # 혼 종류: fresh(갓 죽은) / year(해 넘긴) / old(오래된) / lump(덩어리)
var fierce := false          # 얼룩 3개가 겹쳐 소환된 '사나운 적'인가 (맺힘·공격력 +50%)
var extra := false           # 소환된 추가 적이면 true → 사라지면 다시 나타나지 않는다
var maedhim := 100           # 맺힘 (체력 대신 깎이는 수치)
var maedhim_max := 100
var stun := 0.0              # 남은 경직 시간 (경직 중엔 움직이지도 공격하지도 않음)
var pulled := false
var respawn_ready := false
var wait_left := 0.0         # 처결 대기 남은 시간
var wait_total := 1.0
var gone_by := ""            # "tendo"(천도로 떠남) / "pahon"(파혼으로 터짐)

## 공격 관련
var on_attack: Callable      # 공격이 닿았을 때 부를 함수 (main 이 연결: 플레이어가 아파함)
var _atk_cd := 0.0           # 다음 공격까지 남은 시간
var _windup := -1.0          # 예비동작 진행 시간 (-1 = 예비동작 아님)

var _speed := 0.0
var _flash := 0.0
var _gone_t := 0.0
var _spawn_t := 0.0
var _pulled_t := 0.0
var _body: MeshInstance3D
var _mat: StandardMaterial3D
var _base_color := Color.WHITE
var _shape := "capsule"
var _bar_bg: MeshInstance3D   # 머리 위 막대 배경
var _bar: MeshInstance3D      # 머리 위 막대 (활동 중 = 맺힘, 무릎 = 처결 대기 남은 시간)
var _bar_mat: StandardMaterial3D

## 다른 코드에서 "때릴 수 있는 적인가"를 물을 때 쓰는 이름 (콤보·견인 대상)
var alive: bool:
	get: return state == S.ACTIVE

## 무릎 꿇고 처결을 기다리는 중인가 (천도·파혼 대상)
var kneeling: bool:
	get: return state == S.KNEEL

func _init(shape: String, start_pos: Vector3) -> void:
	_shape = shape
	_body = MeshInstance3D.new()
	_mat = U.matte(Color.WHITE)
	_mat.emission_enabled = true
	_mat.emission = Color.WHITE
	_body.material_override = _mat
	add_child(_body)
	# 머리 위 막대: 화면을 향하는 얇은 판 두 장(배경 + 채움)
	_bar_bg = _make_bar(Color(0, 0, 0, 0.6))
	_bar = _make_bar(Color.WHITE)
	_bar_mat = _bar.material_override
	# 투명한 판끼리는 그리는 순서가 뒤섞일 수 있다 → 채움 막대를 항상 배경 위에 그리도록 순서를 올린다
	_bar_mat.render_priority = 1
	position = start_pos
	_setup_soul(randf() < Config.LUMP_SPAWN_CHANCE, false)

func _make_bar(c: Color) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(1.2, 0.14)
	m.mesh = q
	var mat := U.flat_unlit(c)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED  # 항상 카메라를 본다
	mat.no_depth_test = true                               # 다른 물체에 가려지지 않게
	m.material_override = mat
	m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(m)
	return m

func _setup_soul(lump: bool, is_fierce: bool) -> void:
	# 혼 종류를 정하고 그에 맞게 몸 모양·맺힘을 맞춘다
	fierce = is_fierce
	if lump:
		soul = "lump"
	else:
		soul = ["fresh", "year", "old"][randi() % 3]
	var size_mult := 1.35 if lump else 1.0
	radius = Config.ENEMY_RADIUS * size_mult
	height = Config.ENEMY_HEIGHT * size_mult
	if lump:
		var b := BoxMesh.new()
		b.size = Vector3(radius * 1.9, height, radius * 1.9)
		_body.mesh = b
		_base_color = Color("5b4a78")
	elif _shape == "capsule":
		var c := CapsuleMesh.new()
		c.radius = radius * 0.85
		c.height = height
		_body.mesh = c
		_base_color = Color("d9534f")
	else:
		var b2 := BoxMesh.new()
		b2.size = Vector3(radius * 1.9, height, radius * 1.9)
		_body.mesh = b2
		_base_color = Color("c2692f")
	if fierce:
		_base_color = Color("7a0f1c")  # 사나운 적: 짙은 핏빛
	_mat.albedo_color = _base_color
	_body.position = Vector3(0, height / 2.0, 0)
	_body.rotation = Vector3.ZERO
	maedhim_max = Config.MAEDHIM_LUMP if lump else Config.MAEDHIM_NORMAL
	if fierce:
		maedhim_max = int(maedhim_max * Config.FIERCE_MULT)
	maedhim = maedhim_max
	_speed = Config.ENEMY_SPEED * (1.0 + randf_range(-Config.ENEMY_SPEED_VARIANCE, Config.ENEMY_SPEED_VARIANCE))
	_atk_cd = randf_range(0.5, Config.ENEMY_ATTACK_INTERVAL)  # 다 같이 동시에 때리지 않게 처음 박자를 흩뜨린다
	_windup = -1.0

func attack_damage() -> int:
	return int(Config.ENEMY_ATTACK_DAMAGE * (Config.FIERCE_MULT if fierce else 1.0))

func wait_time_for_soul() -> float:
	match soul:
		"fresh": return Config.WAIT_FRESH
		"year": return Config.WAIT_YEAR
		"old": return Config.WAIT_OLD
	return Config.WAIT_LUMP

func can_tendo() -> bool:
	# 덩어리는 천도 불가 → 파혼만 (W-004)
	return soul != "lump"

func get_head_position() -> Vector3:
	return Vector3(position.x, height + 0.3, position.z)

# =============================================================================
# 맞음 / 처결
# =============================================================================
func take_hit(damage: int, dir: Vector3, knockback: float, stun_time: float) -> bool:
	# 맺힘이 깎인다. 이번 타격으로 0이 되면 true (= 무릎 꿇음. 죽는 게 아니다)
	if state != S.ACTIVE:
		return false
	maedhim -= damage
	_flash = 1.0
	stun = maxf(stun, maxf(stun_time, Config.ENEMY_HIT_STAGGER))
	_windup = -1.0   # 맞으면 예비동작이 끊긴다 (때려서 공격을 막는 맛)
	pulled = false
	vel = dir * knockback
	if maedhim <= 0:
		maedhim = 0
		_enter_kneel()
		return true
	return false

func _enter_kneel() -> void:
	state = S.KNEEL
	wait_total = wait_time_for_soul()
	wait_left = wait_total
	vel *= 0.5  # 무릎 꿇으며 조금만 미끄러진다

func begin_sending() -> void:
	# 천도 캐스팅 시작: 타이머를 멈추고 혼을 붙잡는다
	if state == S.KNEEL:
		state = S.SENDING

func cancel_sending() -> void:
	# 캐스팅이 끊겼다 → 다시 대기 (남은 시간은 그대로)
	if state == S.SENDING:
		state = S.KNEEL

func finish(by: String) -> void:
	# by = "tendo"(하늘로 떠남) / "pahon"(터져 흩어짐)
	state = S.GONE
	gone_by = by
	_gone_t = 0.0
	respawn_ready = false
	vel = Vector3.ZERO

func start_pulled() -> void:
	pulled = true
	_pulled_t = 0.0
	vel = Vector3.ZERO

func respawn(at: Vector3) -> void:
	state = S.ACTIVE
	respawn_ready = false
	stun = 0.0
	pulled = false
	_flash = 0.0
	_spawn_t = 0.0
	vel = Vector3.ZERO
	position = at
	_setup_soul(randf() < Config.LUMP_SPAWN_CHANCE, false)
	_apply_visual()

func make_fierce() -> void:
	# 얼룩 3개 겹침으로 소환된 '사나운 적'으로 만든다 (P-010, P-011)
	extra = true
	_setup_soul(false, true)

# =============================================================================
# 매 프레임
# =============================================================================
func tick(dt: float, player_pos: Vector3) -> void:
	_flash = maxf(0.0, _flash - dt / Config.ENEMY_FLASH_TIME)
	match state:
		S.GONE:
			_tick_gone(dt)
			return
		S.KNEEL:
			_slide(dt)
			wait_left -= dt
			if wait_left <= 0.0:
				# W-005 (임시 해석): 시간 초과 → 맺힘 일부를 되찾고 다시 일어선다
				state = S.ACTIVE
				maedhim = maxi(1, int(maedhim_max * Config.WAIT_TIMEOUT_RECOVER))
				stun = 0.4
				_atk_cd = Config.ENEMY_ATTACK_INTERVAL * 0.5
		S.SENDING:
			_slide(dt)
		S.ACTIVE:
			_spawn_t += dt
			if pulled:
				_tick_pulled(dt, player_pos)
			else:
				_slide(dt)
				stun -= dt
				_atk_cd -= dt
				if stun <= 0.0:
					_tick_ai(dt, player_pos)
	_clamp_to_arena()
	_apply_visual()

func _slide(dt: float) -> void:
	# 넉백: 속도만큼 이동, 마찰로 지수 감속 (프레임레이트와 무관)
	position += vel * dt
	vel *= exp(-Config.ENEMY_KNOCKBACK_FRICTION * dt)

func _tick_ai(dt: float, player_pos: Vector3) -> void:
	var d := Vector2(player_pos.x - position.x, player_pos.z - position.z)
	var dist := d.length()
	if _windup >= 0.0:
		# 예비동작 중: 제자리에서 몸을 부풀리며 신호를 준다 → 끝나는 순간 공격 판정
		_windup += dt
		if _windup >= Config.ENEMY_ATTACK_WINDUP:
			_windup = -1.0
			_atk_cd = Config.ENEMY_ATTACK_INTERVAL
			# 예비동작 동안 플레이어가 충분히 멀어졌으면 빗나감 (피할 수 있어야 공격이 '읽힌다')
			if dist <= Config.ENEMY_ATTACK_RANGE + Config.ENEMY_ATTACK_DODGE_MARGIN and on_attack.is_valid():
				on_attack.call(self)
		return
	if dist <= Config.ENEMY_ATTACK_RANGE and _atk_cd <= 0.0:
		_windup = 0.0  # 공격 시작 (예비동작부터)
		return
	if dist > Config.ENEMY_STOP_DISTANCE:
		position.x += d.x / dist * _speed * dt
		position.z += d.y / dist * _speed * dt

func _tick_pulled(dt: float, player_pos: Vector3) -> void:
	_pulled_t += dt
	var d := Vector2(player_pos.x - position.x, player_pos.z - position.z)
	var dist := d.length()
	var step := Config.PULL_DRAG_SPEED * dt
	if dist - step <= Config.PULL_STOP_DISTANCE or _pulled_t > 1.0:
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

func _tick_gone(dt: float) -> void:
	_gone_t += dt
	_apply_visual()
	if _gone_t >= Config.ENEMY_RESPAWN_DELAY:
		respawn_ready = true

func _clamp_to_arena() -> void:
	var lim := Config.ARENA_HALF_SIZE - radius
	position.x = clampf(position.x, -lim, lim)
	position.z = clampf(position.z, -lim, lim)

# =============================================================================
# 모습
# =============================================================================
func _apply_visual() -> void:
	var col := _base_color
	var glow := _flash * 0.9
	var sx := 1.0 + Config.ENEMY_SQUASH * _flash
	var sy := 1.0 - Config.ENEMY_SQUASH * 0.8 * _flash
	var base := U.ease_out_quad(clampf(_spawn_t / Config.ENEMY_SPAWN_POP_TIME, 0.0, 1.0))
	var lift := 0.0
	var tilt := 0.0
	match state:
		S.ACTIVE:
			if _windup >= 0.0:
				# 예비동작: 붉게 달아오르고 커진다 = "곧 때린다" 신호
				var w := _windup / Config.ENEMY_ATTACK_WINDUP
				col = _base_color.lerp(Color("ff2a2a"), w)
				glow = maxf(glow, 0.6 * w)
				sx *= 1.0 + 0.18 * w
		S.KNEEL, S.SENDING:
			# 무릎 꿇음: 키가 줄고 앞으로 숙인다, 색이 바랜다
			col = _base_color.lerp(Color("8a8f99"), 0.55)
			sy *= 0.55
			tilt = 0.35
			if state == S.SENDING:
				col = col.lerp(Config.MEMORY_TINT, 0.6)
				glow = maxf(glow, 0.5)
		S.GONE:
			var t := clampf(_gone_t / 0.6, 0.0, 1.0)
			if gone_by == "tendo":
				# 천도: 빛이 되어 위로 떠오르며 사라진다
				col = Config.MEMORY_TINT
				glow = 1.2 * (1.0 - t)
				lift = 2.5 * t
				base = 1.0 - t
			else:
				# 파혼: 순간 부풀었다가 터져 사라진다
				col = Color("2a0a0e")
				base = (1.0 + 0.6 * t) * (1.0 - t)
	_mat.albedo_color = col
	_mat.emission = col.lerp(Color.WHITE, 0.5)
	_mat.emission_energy_multiplier = glow
	scale = Vector3(maxf(0.001, base * sx), maxf(0.001, base * sy), maxf(0.001, base * sx))
	_body.position.y = height / 2.0 + lift / maxf(0.001, scale.y)
	_body.rotation.x = tilt
	_update_bar()

func _update_bar() -> void:
	# 활동 중 = 맺힘 막대(흰색), 처결 대기 = 남은 시간 막대(혼 종류 색)
	var show := state != S.GONE
	_bar.visible = show
	_bar_bg.visible = show
	if not show:
		return
	var ratio := 1.0
	var c := Color(1, 1, 1, 0.85)
	if state == S.ACTIVE:
		ratio = float(maedhim) / float(maedhim_max)
		c = Color(1, 0.35, 0.35, 0.9) if fierce else Color(1, 1, 1, 0.85)
	else:
		ratio = clampf(wait_left / wait_total, 0.0, 1.0)
		c = Config.SOUL_COLOR[soul]
	_bar_mat.albedo_color = c
	# 부모(적)의 찌그러짐 크기 영향을 상쇄해서 막대 크기가 흔들리지 않게 한다
	var inv := Vector3(1.0 / maxf(scale.x, 0.001), 1.0 / maxf(scale.y, 0.001), 1.0 / maxf(scale.z, 0.001))
	var top := (height + 0.55) * inv.y
	_bar_bg.position = Vector3(0, top, 0)
	_bar_bg.scale = inv * (1.6 if state != S.ACTIVE else 1.0)
	_bar.scale = Vector3(maxf(ratio, 0.001), 1, 1) * inv * (1.6 if state != S.ACTIVE else 1.0)
	_bar.position = Vector3(0, top, 0)

func ray_hits_body(origin: Vector3, dir: Vector3) -> bool:
	# 마우스 광선이 몸통(세로 원기둥으로 근사)을 지나가나? 무릎 꿇은 적도 고를 수 있다
	if state == S.GONE:
		return false
	var h := height * (0.55 if state != S.ACTIVE else 1.0)
	var center := position + Vector3(0, h / 2.0, 0)
	var t := (center - origin).dot(dir)
	var closest := origin + dir * t
	if absf(closest.y - center.y) > h / 2.0 + 0.3:
		return false
	return Vector2(closest.x - center.x, closest.z - center.z).length() <= radius * 1.2
