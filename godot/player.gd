# =============================================================================
# player.gd — 플레이어(차사). 이동 / 철삭 3타 콤보 / 우클릭 견인. (src/player.ts)
#
# 구조: "상태 머신"(지금 뭘 하는 중인지 하나만 기억하는 방식)
#   FREE   : 가만히 있거나 이동 중
#   ATTACK : 콤보 중 (windup 준비 → swing 휘두름 → recover 후딜)
#   PULL   : 견인 중 (throw 던짐 → drag 끌어당김 → retract 되감기)
# 한 번에 한 상태만 가지므로 "공격하면서 견인" 같은 꼬임이 생기지 않는다.
# =============================================================================
class_name Player
extends Node3D

enum State { FREE, ATTACK, PULL }

var enemies: EnemyManager
var feel: HitFeel
var numbers: DamageNumbers
var chain: ChainVisual

var facing := 0.0            # 바라보는 방향 (바닥 평면 각도, 0 = +x)
var state := State.FREE
var move_target = null       # Vector3 또는 null
var chase_target: Enemy = null  # "저 적을 때리러 가는 중"

var combo_step := 0          # 마지막으로 시작한 콤보 단계 (0 = 없음)
var combo_timer := 0.0       # 콤보 이음 허용 남은 시간
var atk = null               # 진행 중인 한 타 기록 (Dictionary) 또는 null
var has_buffered := false    # 후딜 중 눌러둔 다음 클릭이 있나
var buffered: Enemy = null   # 그 클릭의 대상
var pull_run = null          # 견인 진행 기록 (Dictionary) 또는 null
var pull_cooldown := 0.0
var chain_lag := 0.0         # 사슬이 뒤처지는 각도

func _ready() -> void:
	# 몸: 파란 캡슐 + 노란 박스(코). 코가 있어야 어느 쪽을 보는지 보인다.
	var body := MeshInstance3D.new()
	var cap := CapsuleMesh.new()
	cap.radius = Config.PLAYER_RADIUS * 0.9
	cap.height = 0.8 + Config.PLAYER_RADIUS * 1.8
	body.mesh = cap
	body.material_override = U.matte(Color("3b82f6"))
	body.position.y = 0.9
	add_child(body)
	var nose := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.4, 0.25, 0.25)
	nose.mesh = box
	nose.material_override = U.matte(Color("ffe066"))
	nose.position = Vector3(Config.PLAYER_RADIUS * 0.9, 1.35, 0)  # 로컬 +x 가 '앞'
	add_child(nose)

# =============================================================================
# 명령 (입력 쪽에서 호출) — "무엇을 하라"만 받고 실제 행동은 tick 이 한다
# =============================================================================
func command_move(point: Vector3) -> void:
	move_target = Vector3(
		clampf(point.x, -Config.ARENA_HALF_SIZE, Config.ARENA_HALF_SIZE), 0,
		clampf(point.z, -Config.ARENA_HALF_SIZE, Config.ARENA_HALF_SIZE))
	chase_target = null
	has_buffered = false  # 이동을 지시하면 눌러둔 다음 타는 취소

func command_attack(enemy: Enemy) -> void:
	if state == State.ATTACK:
		# 콤보 중이면 "다음 타 예약" (후딜이 끝나는 순간 이어진다)
		has_buffered = true
		buffered = enemy
	elif state == State.FREE:
		chase_target = enemy
		move_target = null

func command_pull(enemy: Enemy, aim: Vector3) -> void:
	if pull_cooldown > 0.0:
		return
	# 후딜은 견인으로 끊을 수 있다
	var can_cancel: bool = state == State.ATTACK and atk != null and atk.phase == "recover"
	if state != State.FREE and not can_cancel:
		return
	_start_pull(enemy, aim)

# =============================================================================
# 매 프레임 갱신 (dt = 게임 세계 시간, 히트스톱 중엔 0)
# =============================================================================
func tick(dt: float) -> void:
	pull_cooldown = maxf(0.0, pull_cooldown - dt)
	match state:
		State.FREE: _tick_free(dt)
		State.ATTACK: _tick_attack(dt)
		State.PULL: _tick_pull(dt)
	rotation.y = -facing  # 로컬 +x 가 facing 방향을 향하도록
	chain.trail.tick(dt)

# ---- 이동 ---------------------------------------------------------------------
func _tick_free(dt: float) -> void:
	combo_timer = maxf(0.0, combo_timer - dt)
	if dt <= 0.0:
		return
	if chase_target:
		var e := chase_target
		if not e.alive:
			chase_target = null
		else:
			var d := Vector2(e.position.x - position.x, e.position.z - position.z)
			facing = U.turn_toward(facing, atan2(d.y, d.x), Config.PLAYER_TURN_SPEED * dt)
			if d.length() - e.radius <= Config.ATTACK_START_RANGE:
				chase_target = null
				_start_attack(e, combo_timer > 0.0)
			else:
				_step_toward(e.position, dt)
			return
	if move_target != null:
		var d := Vector2(move_target.x - position.x, move_target.z - position.z)
		if d.length() <= Config.PLAYER_ARRIVE_DISTANCE:
			move_target = null
		else:
			facing = U.turn_toward(facing, atan2(d.y, d.x), Config.PLAYER_TURN_SPEED * dt)
			_step_toward(move_target, dt)

func _step_toward(target: Vector3, dt: float) -> void:
	# 목표를 지나치지 않게 한 걸음
	var d := Vector2(target.x - position.x, target.z - position.z)
	var dist := d.length()
	if dist < 1e-5:
		return
	var step := minf(dist, Config.PLAYER_MOVE_SPEED * dt)
	position.x += d.x / dist * step
	position.z += d.y / dist * step
	_clamp_to_arena()

func _clamp_to_arena() -> void:
	var lim := Config.ARENA_HALF_SIZE - Config.PLAYER_RADIUS
	position.x = clampf(position.x, -lim, lim)
	position.z = clampf(position.z, -lim, lim)

func _hand() -> Vector3:
	return Vector3(position.x, Config.PLAYER_HAND_HEIGHT, position.z)

# =============================================================================
# 철삭 3타 콤보
# =============================================================================
func _start_attack(target: Enemy, continue_combo: bool) -> void:
	var step := (combo_step % Config.COMBO.size()) + 1 if continue_combo else 1
	combo_step = step
	var cfg: Dictionary = Config.COMBO[step - 1]
	if target and target.alive:
		facing = atan2(target.position.z - position.z, target.position.x - position.x)
	var start_angle: float = facing - cfg.dir * deg_to_rad(cfg.start_offset_deg)
	state = State.ATTACK
	atk = {
		"step": step, "cfg": cfg, "phase": "windup", "t": 0.0,
		"start_angle": start_angle,
		"total_sweep": cfg.dir * deg_to_rad(cfg.sweep_deg),
		"prev_angle": start_angle,
		"hit": {},              # 이번 타에 이미 맞은 적 (한 번 휘두를 때 한 번만)
		"first_sample": true,   # 잔상의 첫 점인가
	}
	has_buffered = false
	chain.visible = true

func _tick_attack(dt: float) -> void:
	var a: Dictionary = atk
	var cfg: Dictionary = a.cfg
	a.t += dt
	var hand := _hand()

	if a.phase == "windup":
		# 준비: 사슬을 시작 위치로 끌어 모은다 (살짝 앞 → 뒤로 당기는 예비동작)
		var p := clampf(a.t / cfg.windup, 0.0, 1.0)
		var angle: float = a.start_angle + cfg.dir * 0.4 * (1.0 - U.ease_out_quad(p))
		chain_lag *= exp(-14.0 * dt)
		chain.set_shape(hand, angle, lerpf(0.3, 0.55, p) * cfg.reach, hand.y + 0.25 * p, chain_lag, 0.25)
		a.prev_angle = a.start_angle
		if a.t >= cfg.windup:
			a.phase = "swing"
			a.t = 0.0
		return

	if a.phase == "swing":
		var p := clampf(a.t / cfg.swing, 0.0, 1.0)
		var angle: float = a.start_angle + a.total_sweep * U.ease_out_quad(p)  # 확 휘두르고 끝에서 감속
		var radius: float = cfg.reach * (0.55 + 0.45 * U.ease_out_quad(minf(1.0, p / 0.3)))  # 쭉 펴진다
		var head_y := hand.y + 0.25 - 0.3 * p
		if dt > 0.0:
			# 사슬 휘어짐: 빠를수록 많이 뒤처진다
			var ang_vel: float = absf(angle - a.prev_angle) / dt
			var target_lag: float = cfg.dir * minf(ang_vel * 0.04, 1.1)
			chain_lag = lerpf(chain_lag, target_lag, 0.5)
			_sweep_hits(a, a.prev_angle, angle)
			_record_trail(a, hand, a.prev_angle, angle, radius, head_y)
			# 휘두르며 앞으로 미끄러져 들어간다 (제자리 휘두르기는 가벼워 보인다)
			if cfg.lunge > 0.0:
				var v: float = cfg.lunge / cfg.swing * dt
				position.x += cos(facing) * v
				position.z += sin(facing) * v
				_clamp_to_arena()
		chain.set_shape(_hand(), angle, radius, head_y, chain_lag, 0.0)
		a.prev_angle = angle
		if a.t >= cfg.swing:
			a.phase = "recover"
			a.t = 0.0
		return

	# recover: 후딜. 사슬을 거둬들인다.
	var p := clampf(a.t / cfg.recover, 0.0, 1.0)
	var angle: float = a.start_angle + a.total_sweep + cfg.dir * 0.2 * U.ease_out_quad(p)  # 관성
	chain_lag *= exp(-10.0 * dt)
	chain.set_shape(hand, angle, cfg.reach * (1.0 - 0.85 * U.ease_in_quad(p)), hand.y - 0.05, chain_lag, 0.4 * p)
	if a.t >= cfg.recover:
		_finish_attack()

func _finish_attack() -> void:
	# 한 타 종료: 예약된 클릭이 있으면 바로 다음 타, 없으면 대기
	var finished_step: int = atk.step
	atk = null
	if has_buffered:
		var next := buffered
		has_buffered = false
		if finished_step >= Config.COMBO.size():
			combo_step = 0  # 3타까지 끝났으면 다음은 1타
		_start_attack(next, true)
		return
	state = State.FREE
	chain.visible = false
	if finished_step >= Config.COMBO.size():
		combo_step = 0
		combo_timer = 0.0
	else:
		combo_timer = Config.COMBO_RESET_TIME

func _sweep_hits(a: Dictionary, prev: float, cur: float) -> void:
	# 이번 프레임에 사슬 끝이 훑은 구간에 걸린 적을 모두, 지나가는 순서대로 때린다
	var reach: float = a.cfg.reach
	for e in enemies.list:
		if not e.alive or a.hit.has(e):
			continue
		var d := Vector2(e.position.x - position.x, e.position.z - position.z)
		var dist := d.length()
		if dist - e.radius > reach + Config.HIT_PADDING:
			continue  # 사슬이 안 닿는 거리
		# 적 몸통이 각도로 얼마나 넓은지 (가까울수록 넓게 보임)
		var half_width := asin(clampf((e.radius + Config.HIT_PADDING) / maxf(dist, 0.01), 0.0, 1.0))
		if not U.swept_through(prev, cur, atan2(d.y, d.x), half_width):
			continue
		a.hit[e] = true
		var n := d / dist if dist > 0.0 else d
		_hit_enemy(e, a, n.x, n.y)

func _hit_enemy(e: Enemy, a: Dictionary, rx: float, rz: float) -> void:
	# 데미지 + 넉백 + 히트스톱 + 흔들림 + 숫자
	var cfg: Dictionary = a.cfg
	# 넉백 방향 = 바깥쪽 + 휘두른 방향(접선)을 조금 섞음 → 사슬에 쓸려 날아가는 느낌
	var mix: float = Config.FEEL_KNOCKBACK_TANGENT_MIX * cfg.dir
	var dir := Vector3(rx - rz * mix, 0, rz + rx * mix).normalized()
	var damage := maxi(1, roundi(cfg.damage * (1.0 + randf_range(-Config.DAMAGE_VARIANCE, Config.DAMAGE_VARIANCE))))
	var killed := e.take_hit(damage, dir, cfg.knockback, cfg.stun)
	feel.hit_stop(cfg.hit_stop_frames + (Config.FEEL_KILL_BONUS_FRAMES if killed else 0))
	feel.add_shake(cfg.shake + (Config.FEEL_KILL_BONUS_SHAKE if killed else 0.0))
	numbers.spawn(e.get_head_position(), damage, "heavy" if a.step == Config.COMBO.size() else "normal")

func _record_trail(a: Dictionary, hand: Vector3, prev: float, cur: float, radius: float, y: float) -> void:
	# 지난 프레임 → 이번 프레임 사이를 잘게 쪼개 곡선이 매끈하게
	for i in range(1, Config.TRAIL_SUBSTEPS + 1):
		var ang := lerpf(prev, cur, float(i) / Config.TRAIL_SUBSTEPS)
		var c := cos(ang)
		var s := sin(ang)
		var outer := Vector3(hand.x + c * radius, y, hand.z + s * radius)
		var inner := Vector3(hand.x + c * radius * Config.TRAIL_INNER_RATIO, y, hand.z + s * radius * Config.TRAIL_INNER_RATIO)
		chain.trail.add(inner, outer, a.first_sample)
		a.first_sample = false

# =============================================================================
# 우클릭 견인
# =============================================================================
func _start_pull(enemy: Enemy, aim: Vector3) -> void:
	# 콤보 후딜을 끊고 들어온 경우 정리
	atk = null
	has_buffered = false
	move_target = null
	chase_target = null
	combo_timer = 0.0
	combo_step = 0
	var target: Enemy = enemy if enemy and enemy.alive else null
	var goal := target.position if target else aim
	var d := Vector2(goal.x - position.x, goal.z - position.z)
	var dist := d.length()
	if target and dist > Config.PULL_RANGE:
		target = null  # 사거리 밖이면 허공에 던진다(빗나감)
	facing = atan2(d.y, d.x)
	var reach := minf(dist, Config.PULL_RANGE)
	var hand := _hand()
	state = State.PULL
	pull_run = {
		"phase": "throw", "t": 0.0, "target": target,
		"aim": Vector3(hand.x + cos(facing) * reach, Config.PLAYER_HAND_HEIGHT, hand.z + sin(facing) * reach),
		"from": Vector3.ZERO,
	}
	chain.visible = true

func _tick_pull(dt: float) -> void:
	var r: Dictionary = pull_run
	var hand := _hand()
	r.t += dt
	var target: Enemy = r.target

	if r.phase == "throw":
		# 사슬이 목표로 쭉 날아간다. 대상이 움직여도 따라가도록 매 프레임 목표를 다시 읽는다
		var goal: Vector3 = Vector3(target.position.x, Config.PLAYER_HAND_HEIGHT, target.position.z) if target else r.aim
		var p := U.ease_out_quad(clampf(r.t / Config.PULL_THROW_TIME, 0.0, 1.0))
		_set_straight_chain(hand, hand.lerp(goal, p), 0.2 * (1.0 - p))
		if r.t >= Config.PULL_THROW_TIME:
			if target:
				_hit_pull(target)
				r.phase = "drag"
			else:
				r.from = goal
				r.phase = "retract"
			r.t = 0.0
		return

	if r.phase == "drag":
		# 적이 끌려오는 동안 사슬은 팽팽하게 적에게 붙어 있다
		var head := Vector3(target.position.x, Config.PLAYER_HAND_HEIGHT, target.position.z)
		_set_straight_chain(hand, head, 0.0)
		facing = atan2(target.position.z - position.z, target.position.x - position.x)
		if not target.pulled:
			# 도착: 한 번 더 쿵
			if dt > 0.0 and target.alive:
				feel.hit_stop(2)
				feel.add_shake(Config.PULL_ARRIVE_SHAKE)
			r.from = head
			r.phase = "retract"
			r.t = 0.0
		return

	# retract: 사슬을 손으로 되감는다
	var p2 := U.ease_in_quad(clampf(r.t / Config.PULL_RETRACT_TIME, 0.0, 1.0))
	_set_straight_chain(hand, (r.from as Vector3).lerp(hand, p2), 0.1)
	if r.t >= Config.PULL_RETRACT_TIME:
		state = State.FREE
		pull_run = null
		pull_cooldown = Config.PULL_COOLDOWN
		chain.visible = false

func _hit_pull(e: Enemy) -> void:
	# 견인 적중: 넉백 0 (끌려오는 게 핵심), 방향은 플레이어 쪽
	var dir := Vector3(position.x - e.position.x, 0, position.z - e.position.z).normalized()
	var damage := maxi(1, roundi(Config.PULL_DAMAGE * (1.0 + randf_range(-Config.DAMAGE_VARIANCE, Config.DAMAGE_VARIANCE))))
	var killed := e.take_hit(damage, dir, 0.0, Config.PULL_STUN)
	feel.hit_stop(Config.PULL_HITSTOP_FRAMES + (Config.FEEL_KILL_BONUS_FRAMES if killed else 0))
	feel.add_shake(Config.PULL_SHAKE)
	numbers.spawn(e.get_head_position(), damage, "pull")
	if not killed:
		e.start_pulled()

func _set_straight_chain(hand: Vector3, head: Vector3, sag: float) -> void:
	# 손에서 head 까지 일직선(약간 처짐)
	var d := Vector2(head.x - hand.x, head.z - hand.z)
	chain.set_shape(hand, atan2(d.y, d.x), d.length(), head.y, 0.0, sag)
