# =============================================================================
# main.gd — 시작점. 무대(카메라·조명·바닥)를 세우고, 부품을 조립하고, 매 프레임 돌린다.
# (Three.js판의 main.ts + stage.ts + input.ts 를 한 파일로 합침)
#
# 왜 씬 편집기 대신 코드로 다 만드나?
#   이 프로젝트는 AI가 텍스트 파일만 고쳐서 개발한다. 화면을 코드로 만들면
#   에디터를 열지 않고도 전부 수정·검증할 수 있다.
# =============================================================================
extends Node3D

var feel := HitFeel.new()
var camera: Camera3D
var sun: DirectionalLight3D
var player: Player
var enemies: EnemyManager
var numbers: DamageNumbers
var marker: ClickMarker
var _focus := Vector3.ZERO      # 카메라가 바라보는 점 (플레이어를 부드럽게 따라감)
var _offset := Vector3.ZERO     # 카메라가 focus 에서 떨어진 방향/거리 (고정 각도)
var _holding_move := false      # 좌클릭을 누른 채 바닥을 끌고 다니는 중인가
var _cursor := Vector2.ZERO     # 마지막 마우스 위치(화면 픽셀). 키보드 기술이 '어디로' 쓸지 정할 때 쓴다

## ---- 핵심 루프(처결) ----
var stains: StainField
var _judge_press: Enemy = null  # 무릎 꿇은 적 위에서 좌클릭을 누르고 있는 중이면 그 적
var _judge_hold := 0.0          # 누르고 있은 시간 (0.3초 넘으면 천도)
var _judge_fired := false       # 이번 누름으로 이미 천도를 시작했나
var _fallen := false            # 이번 프레임에 플레이어가 쓰러졌나 (적 처리 도중엔 판을 못 바꿔서 표시만)
var _vision: ColorRect          # 화면 가장자리를 어둡게 덮는 판 (시야)
var _vision_mat: ShaderMaterial
var _vision_ratio := 1.0        # 현재 시야 배율 (1 = 평소, 0.6 = 천도 중)
var _hud: Label
var _hp_fill: ColorRect
var _cast_bg: ColorRect
var _cast_fill: ColorRect

func _ready() -> void:
	_build_stage()
	stains = StainField.new()
	add_child(stains)
	enemies = EnemyManager.new()
	# 적의 공격이 닿으면 플레이어가 맞는다. 쓰러지면 표시만 해 두고 프레임 끝에 판을 다시 짠다
	enemies.on_attack = func(e: Enemy) -> void:
		if player.take_damage(e.attack_damage()):
			_fallen = true
	add_child(enemies)
	enemies.spawn_all(Vector3.ZERO)

	numbers = DamageNumbers.new()
	numbers.camera = camera
	add_child(numbers)

	marker = ClickMarker.new()
	add_child(marker)

	player = Player.new()
	player.enemies = enemies
	player.feel = feel
	player.numbers = numbers
	player.chain = ChainVisual.new()
	add_child(player)
	add_child(player.chain)
	add_child(player.chain.trail)
	# 파혼한 자리에 얼룩을 남긴다. 얼룩이 3개 겹치면 사나운 적 소환
	player.on_pahon = func(at: Vector3) -> void:
		var summon = stains.add(at)
		if summon != null:
			enemies.spawn_fierce(summon)
			numbers.spawn_text(summon + Vector3(0, 2.0, 0), "FIERCE!", Color("ff3344"))
			feel.add_shake(0.5)

	_add_vision()
	_add_hud()
	_add_hint()
	_add_touch_buttons()

# -----------------------------------------------------------------------------
# 게임 루프
#   real_dt : 진짜 흐른 시간 → 화면 흔들림·데미지 숫자처럼 "멈추면 안 되는 것"
#   dt      : 게임 세계 시간. 히트스톱 중엔 0 → 캐릭터·적·사슬이 얼어붙는다
#   → "세계는 멈췄는데 화면만 부르르 떨리는" 타격감 (Three.js판과 같은 원리)
# -----------------------------------------------------------------------------
func _process(delta: float) -> void:
	var real_dt := minf(0.05, delta)  # 탭을 오래 비웠다 돌아와도 순간이동하지 않게
	var frozen := feel.tick(real_dt)
	var dt := 0.0 if frozen else real_dt
	# 얼룩을 밟고 있으면 느려진다 (P-009)
	player.speed_mult = 1.0 - Config.STAIN_SLOW if stains.is_on_stain(player.position) else 1.0
	_tick_judge_hold(real_dt)
	player.tick(dt)
	enemies.tick(dt, player.position, Config.PLAYER_RADIUS)
	stains.tick(dt)
	if _fallen:
		_fall()
	numbers.tick(real_dt)
	marker.tick(real_dt)
	_update_camera(real_dt)
	_update_vision(real_dt)
	_update_hud()

func _tick_judge_hold(real_dt: float) -> void:
	# 무릎 꿇은 적을 '길게 누르면' 천도. 0.3초를 넘기는 순간 바로 시작한다
	# (손을 뗄 때까지 기다리면 굼뜨게 느껴지므로)
	if _judge_press == null or _judge_fired:
		return
	_judge_hold += real_dt
	if _judge_hold >= Config.TENDO_HOLD_TIME:
		_judge_fired = true
		player.command_tendo(_judge_press)

func _fall() -> void:
	# 플레이어가 쓰러짐 → 체력·적·얼룩을 처음 상태로. 모은 넋/엽전/업은 남긴다
	_fallen = false
	player.reset_after_fall()
	enemies.reset_all(Vector3.ZERO)
	stains.clear()
	numbers.spawn_text(Vector3(0, 2.5, 0), "FALLEN - RETRY", Color("ff5555"))

# -----------------------------------------------------------------------------
# 무대: 배경·조명·카메라·바닥
# -----------------------------------------------------------------------------
func _build_stage() -> void:
	# 배경색 + 은은한 전체 조명 (Three.js 의 AmbientLight 역할)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("14161c")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.WHITE
	env.ambient_light_energy = 0.45  # Three.js판과 밝기를 눈으로 맞춘 값
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	# 그림자를 만드는 햇빛 (그림자가 있어야 캐릭터가 바닥에서 안 떠 보인다)
	sun = DirectionalLight3D.new()
	sun.light_energy = 0.9
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 60.0
	add_child(sun)
	# 햇빛 방향: Three.js판과 같이 (14, 30, 8) 쪽에서 비춘다
	sun.look_at_from_position(Vector3(14, 30, 8), Vector3.ZERO)

	# 직교(Orthographic) 카메라: 멀리 있어도 작아지지 않는다 = 원근감 없는 쿼터뷰
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = Config.CAMERA_VIEW_HEIGHT  # 세로로 보이는 월드 길이
	camera.keep_aspect = Camera3D.KEEP_HEIGHT
	camera.near = 0.1
	camera.far = 300.0
	add_child(camera)
	var pitch := deg_to_rad(Config.CAMERA_PITCH_DEG)
	var yaw := deg_to_rad(Config.CAMERA_YAW_DEG)
	var dist := 60.0  # 직교 카메라는 거리가 화면 크기에 영향이 없으니 멀리만 두면 된다
	_offset = Vector3(cos(yaw) * cos(pitch) * dist, sin(pitch) * dist, sin(yaw) * cos(pitch) * dist)

	_build_floor()

func _build_floor() -> void:
	# 바닥 판
	var size := Config.ARENA_HALF_SIZE * 2.0
	var floor_mesh := PlaneMesh.new()
	floor_mesh.size = Vector2(size, size)
	var floor_node := MeshInstance3D.new()
	floor_node.mesh = floor_mesh
	floor_node.material_override = U.matte(Color("2b303b"))
	add_child(floor_node)

	# 격자: '내가 움직이고 있다'는 걸 눈으로 느끼게 해준다 (2칸 간격, 가운데 줄은 밝게)
	var im := ImmediateMesh.new()
	var h := Config.ARENA_HALF_SIZE
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	var x := -h
	while x <= h + 0.001:
		var col := Color("4a5262") if absf(x) < 0.001 else Color("383e4b")
		im.surface_set_color(col)
		im.surface_add_vertex(Vector3(x, 0.01, -h))
		im.surface_add_vertex(Vector3(x, 0.01, h))
		im.surface_add_vertex(Vector3(-h, 0.01, x))
		im.surface_add_vertex(Vector3(h, 0.01, x))
		x += 2.0
	im.surface_end()
	# 맵 끝을 알려주는 붉은 테두리
	im.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
	im.surface_set_color(Color("9b3b3b"))
	for p in [Vector3(-h, 0.02, -h), Vector3(h, 0.02, -h), Vector3(h, 0.02, h), Vector3(-h, 0.02, h), Vector3(-h, 0.02, -h)]:
		im.surface_add_vertex(p)
	im.surface_end()
	var lines := MeshInstance3D.new()
	lines.mesh = im
	var lm := StandardMaterial3D.new()
	lm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	lm.vertex_color_use_as_albedo = true
	lines.material_override = lm
	lines.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(lines)

func _add_hint() -> void:
	# 화면 왼쪽 위 조작 안내 (Three.js판에는 없지만, 폰으로 처음 열었을 때 헤매지 않게)
	var layer := CanvasLayer.new()
	var label := Label.new()
	label.text = "Mouse: move / attack   Q: pull   Space: swing\nKneeling soul: HOLD click (or E) = SEND   tap (or R) = SHATTER"  # 기본 글꼴에 한글이 없어 영문으로 표기
	label.position = Vector2(12, 34)  # 맨 위 줄은 상태 표시줄(HUD) 자리
	label.add_theme_color_override("font_color", Color(1, 1, 1, 0.55))
	label.add_theme_font_size_override("font_size", 14)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(label)
	add_child(layer)

func _update_camera(dt: float) -> void:
	# 1) 따라가기: 지수 보간 → 프레임레이트와 상관없이 같은 부드러움
	var k := 1.0 - exp(-Config.CAMERA_FOLLOW_SMOOTHNESS * dt)
	_focus = _focus.lerp(Vector3(player.position.x, 0, player.position.z), k)
	# 2) 카메라 배치 (각도 고정)
	camera.look_at_from_position(_focus + _offset, _focus)
	# 3) 흔들림: 카메라의 '오른쪽/위쪽' 방향으로 밀어 화면이 평행하게 떨린다
	var shake := feel.get_shake_offset()
	camera.position += camera.global_basis.x * shake.x + camera.global_basis.y * shake.y

# -----------------------------------------------------------------------------
# 입력: 좌클릭 바닥 → 이동 / 좌클릭 적 → 콤보 / 우클릭 → 견인
# -----------------------------------------------------------------------------
func _unhandled_input(event: InputEvent) -> void:
	# 키보드 = 기술. 마우스로 위치·대상을 정하고, 키로 '무엇을 할지'를 고른다 (디아블로식 분업)
	if event is InputEventKey and event.pressed and not event.echo:
		match (event as InputEventKey).keycode:
			KEY_Q: _skill_pull(_cursor)    # Q: 커서 근처 적을 견인
			KEY_SPACE: _skill_swing(_cursor)  # Space: 제자리에서 커서 방향으로 휘두르기
			KEY_E: _skill_judge(_cursor, "tendo")   # E: 커서 근처 무릎 꿇은 혼을 천도
			KEY_R: _skill_judge(_cursor, "pahon")   # R: 커서 근처 무릎 꿇은 혼을 파혼
		return
	if event is InputEventMouseMotion:
		_cursor = (event as InputEventMouseMotion).position
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and not mb.pressed:
			_holding_move = false
			# 무릎 꿇은 적 위에서 짧게 눌렀다 뗐다 = 파혼 (길게 눌렀으면 이미 천도가 시작됨)
			if _judge_press != null and not _judge_fired:
				player.command_pahon(_judge_press)
			_judge_press = null
			return
		if not mb.pressed:
			return
		var origin := camera.project_ray_origin(mb.position)
		var dir := camera.project_ray_normal(mb.position)
		var ground = _ground_point(origin, dir)
		if mb.button_index == MOUSE_BUTTON_LEFT:
			var enemy := enemies.pick(origin, dir, ground, Config.ENEMY_PICK_RADIUS)
			if enemy and enemy.kneeling:
				# 처결 대기 중인 혼: 얼마나 오래 누르는지 재기 시작 (짧게 = 파혼, 길게 = 천도)
				_judge_press = enemy
				_judge_hold = 0.0
				_judge_fired = false
			elif enemy:
				player.command_attack(enemy)
			elif ground != null:
				player.command_move(ground)
				marker.show_at(ground)
				_holding_move = true
		elif mb.button_index == MOUSE_BUTTON_RIGHT:
			_skill_pull(mb.position)  # 우클릭도 견인 (Q와 같음)
	elif event is InputEventMouseMotion and _holding_move:
		# 좌클릭을 누른 채 움직이면 이동 목표가 계속 갱신 (마우스 따라 걷기)
		var mm := event as InputEventMouseMotion
		var ground = _ground_point(camera.project_ray_origin(mm.position), camera.project_ray_normal(mm.position))
		if ground != null:
			player.command_move(ground)

func _ground_point(origin: Vector3, dir: Vector3):
	# 마우스 광선이 y=0 바닥과 만나는 점. 못 만나면 null
	if absf(dir.y) < 1e-6:
		return null
	var t := -origin.y / dir.y
	if t < 0.0:
		return null
	return origin + dir * t

# -----------------------------------------------------------------------------
# 기술 (키보드·우클릭·터치 버튼이 모두 이 함수를 부른다 → 입력 방식이 늘어도 동작은 한 곳)
# -----------------------------------------------------------------------------
func _skill_pull(screen: Vector2) -> void:
	# 커서 근처 적을 견인. 근처에 없으면 그 방향 허공으로 던진다(빗나감)
	var origin := camera.project_ray_origin(screen)
	var dir := camera.project_ray_normal(screen)
	var ground = _ground_point(origin, dir)
	var enemy := enemies.pick(origin, dir, ground, Config.PULL_PICK_RADIUS)
	player.command_pull(enemy, ground if ground != null else player.position)

func _skill_swing(screen: Vector2) -> void:
	var ground = _ground_point(camera.project_ray_origin(screen), camera.project_ray_normal(screen))
	player.command_swing(ground if ground != null else player.position + Vector3(cos(player.facing), 0, sin(player.facing)))

func _skill_judge(screen: Vector2, kind: String) -> void:
	var origin := camera.project_ray_origin(screen)
	var dir := camera.project_ray_normal(screen)
	var e := enemies.pick(origin, dir, _ground_point(origin, dir), Config.PULL_PICK_RADIUS, true)
	if e == null:
		e = _nearest_enemy(Config.PULL_RANGE, true)  # 커서 근처에 없으면 가장 가까운 무릎 꿇은 혼
	if kind == "tendo":
		player.command_tendo(e)
	else:
		player.command_pahon(e)

func _nearest_enemy(max_dist: float, kneel_only := false) -> Enemy:
	var best: Enemy = null
	var best_d := max_dist
	for e in enemies.list:
		var ok: bool = e.kneeling if kneel_only else e.alive
		if ok and e.position.distance_to(player.position) <= best_d:
			best_d = e.position.distance_to(player.position)
			best = e
	return best

func _add_touch_buttons() -> void:
	# 폰에는 키보드가 없으니 화면 오른쪽 아래에 같은 기술 버튼 두 개를 띄운다.
	# 터치 화면이 없는 PC에서는 숨긴다(키보드를 쓰면 되므로).
	if not DisplayServer.is_touchscreen_available():
		return
	var layer := CanvasLayer.new()
	var box := HBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	box.offset_left = -500
	box.offset_top = -110
	box.offset_right = -16
	box.offset_bottom = -16
	box.add_theme_constant_override("separation", 12)
	for spec in [["PULL", "pull"], ["SWING", "swing"], ["SEND", "tendo"], ["SHATTER", "pahon"]]:
		var b := Button.new()
		b.text = spec[0]
		b.custom_minimum_size = Vector2(110, 90)
		b.add_theme_font_size_override("font_size", 20)
		b.focus_mode = Control.FOCUS_NONE
		var kind: String = spec[1]
		b.pressed.connect(func() -> void: _touch_skill(kind))
		box.add_child(b)
	layer.add_child(box)
	add_child(layer)

func _touch_skill(kind: String) -> void:
	# 터치는 커서가 없으니 '가장 가까운 적'을 자동으로 고른다
	if kind == "tendo" or kind == "pahon":
		var k := _nearest_enemy(Config.PULL_RANGE, true)
		if kind == "tendo":
			player.command_tendo(k)
		else:
			player.command_pahon(k)
		return
	var e := _nearest_enemy(Config.PULL_RANGE)
	if kind == "pull":
		player.command_pull(e, e.position if e else player.position)
	else:
		player.command_swing(e.position if e else player.position + Vector3(cos(player.facing), 0, sin(player.facing)))

# -----------------------------------------------------------------------------
# 시야 (밤): 플레이어 둘레만 보이고 가장자리는 어둡다.
# 천도 중엔 0.2초에 걸쳐 60%로 좁아지고, 어둠이 '생전 기억' 색으로 물든다 (T-004, T-005, P1-034)
# 왜 셰이더(그래픽카드에서 도는 작은 그림 프로그램)? 화면 전체를 매 프레임 칠하는 일은 CPU보다 훨씬 빠르다.
# -----------------------------------------------------------------------------
const VISION_SHADER := """
shader_type canvas_item;
uniform vec2 center;        // 시야 중심 (화면 픽셀)
uniform vec2 rect_size;     // 화면 크기 (픽셀)
uniform float radius;       // 시야 반경 (픽셀)
uniform float soft;         // 경계 번짐 비율
uniform float cast_amt;     // 0 = 평소, 1 = 천도 중
uniform vec4 tint : source_color;  // 생전 기억 색
void fragment() {
	vec2 p = UV * rect_size;
	vec2 rel = p - center;
	float d = length(rel);
	// 천도 중엔 경계가 아지랑이처럼 일렁인다 (기억이 스며드는 느낌)
	float wobble = sin(atan(rel.y, rel.x) * 7.0 + TIME * 3.0) * 0.03 * cast_amt;
	float r = radius * (1.0 + wobble);
	float edge = smoothstep(r * (1.0 - soft), r, d);
	vec3 night = vec3(0.02, 0.02, 0.05);
	vec3 col = mix(night, tint.rgb * 0.5, cast_amt * (0.4 + 0.6 * edge));
	COLOR = vec4(col, edge * mix(0.85, 0.9, cast_amt));
}
"""

func _add_vision() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 0  # 게임 화면 바로 위. 데미지 숫자·HUD(기본 layer 1)는 이보다 위에 그려진다
	_vision = ColorRect.new()
	_vision.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_vision.mouse_filter = Control.MOUSE_FILTER_IGNORE  # 클릭은 통과
	var sh := Shader.new()
	sh.code = VISION_SHADER
	_vision_mat = ShaderMaterial.new()
	_vision_mat.shader = sh
	_vision_mat.set_shader_parameter("soft", Config.VISION_EDGE_SOFT)
	_vision_mat.set_shader_parameter("tint", Config.MEMORY_TINT)
	_vision.material = _vision_mat
	layer.add_child(_vision)
	add_child(layer)

func _update_vision(real_dt: float) -> void:
	var goal := Config.TENDO_VISION_RATIO if player.cast_ratio() > 0.0 else 1.0
	# 0.2초 동안 일정한 속도로 목표 배율까지 이동 (1 → 0.6, 거리 0.4 를 0.2초에)
	var speed := (1.0 - Config.TENDO_VISION_RATIO) / Config.TENDO_VISION_BLEND
	_vision_ratio = move_toward(_vision_ratio, goal, speed * real_dt)
	var size := get_viewport().get_visible_rect().size
	var center := camera.unproject_position(player.position + Vector3(0, 0.9, 0))
	var amt := (1.0 - _vision_ratio) / (1.0 - Config.TENDO_VISION_RATIO)  # 좁아진 정도 0~1
	_vision_mat.set_shader_parameter("center", center)
	_vision_mat.set_shader_parameter("rect_size", size)
	_vision_mat.set_shader_parameter("radius", size.y * Config.VISION_BASE_RATIO * _vision_ratio)
	_vision_mat.set_shader_parameter("cast_amt", amt)

func vision_ratio() -> float:
	return _vision_ratio

# -----------------------------------------------------------------------------
# 상태 표시줄 (HUD): 체력 막대 + 넋·기억·엽전·업 + 천도 캐스팅 막대
# -----------------------------------------------------------------------------
func _make_rect(layer: CanvasLayer, color: Color, pos: Vector2, size: Vector2) -> ColorRect:
	var r := ColorRect.new()
	r.color = color
	r.position = pos
	r.size = size
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(r)
	return r

func _add_hud() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 2  # 시야 어둠보다 위
	_make_rect(layer, Color(0, 0, 0, 0.6), Vector2(12, 10), Vector2(180, 16))
	_hp_fill = _make_rect(layer, Color("e04848"), Vector2(14, 12), Vector2(176, 12))
	_hud = Label.new()
	_hud.position = Vector2(202, 6)
	_hud.add_theme_font_size_override("font_size", 16)
	_hud.add_theme_color_override("font_outline_color", Color.BLACK)
	_hud.add_theme_constant_override("outline_size", 4)
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(_hud)
	# 천도 캐스팅 막대: 플레이어 머리 위에 '얼마나 남았나'를 보여준다
	_cast_bg = _make_rect(layer, Color(0, 0, 0, 0.6), Vector2.ZERO, Vector2(70, 8))
	_cast_fill = _make_rect(layer, Config.MEMORY_TINT, Vector2.ZERO, Vector2(0, 6))
	add_child(layer)

func _update_hud() -> void:
	_hp_fill.size.x = 176.0 * float(player.hp) / float(Config.PLAYER_MAX_HP)
	var t := "HP %d   Neok %d   Memory %d   Coin %d   Karma %d (tier %d)" % [player.hp, player.neok, player.memory, player.coin, player.karma, player.karma_tier()]
	if player.tendo_chain_left > 0.0:
		t += "   CHAIN x%d (%.1fs)" % [player.tendo_streak, player.tendo_chain_left]
	_hud.text = t
	var casting := player.state == Player.State.CAST
	_cast_bg.visible = casting
	_cast_fill.visible = casting
	if casting:
		var head := camera.unproject_position(player.position + Vector3(0, 2.4, 0))
		_cast_bg.position = head - Vector2(35, 4)
		_cast_fill.position = head - Vector2(34, 3)
		_cast_fill.size.x = 68.0 * player.cast_progress()
