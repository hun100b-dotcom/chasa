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

func _ready() -> void:
	_build_stage()
	enemies = EnemyManager.new()
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

	_add_hint()

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
	player.tick(dt)
	enemies.tick(dt, player.position, Config.PLAYER_RADIUS)
	numbers.tick(real_dt)
	marker.tick(real_dt)
	_update_camera(real_dt)

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
	label.text = "Godot  |  tap/left: move+attack  |  right: pull"  # 기본 글꼴에 한글이 없어 영문으로 표기
	label.position = Vector2(12, 8)
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
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and not mb.pressed:
			_holding_move = false
			return
		if not mb.pressed:
			return
		var origin := camera.project_ray_origin(mb.position)
		var dir := camera.project_ray_normal(mb.position)
		var ground = _ground_point(origin, dir)
		if mb.button_index == MOUSE_BUTTON_LEFT:
			var enemy := enemies.pick(origin, dir, ground, Config.ENEMY_PICK_RADIUS)
			if enemy:
				player.command_attack(enemy)
			elif ground != null:
				player.command_move(ground)
				marker.show_at(ground)
				_holding_move = true
		elif mb.button_index == MOUSE_BUTTON_RIGHT:
			# 근처에 적이 없으면 그 방향 허공으로 던진다
			var enemy := enemies.pick(origin, dir, ground, Config.PULL_PICK_RADIUS)
			player.command_pull(enemy, ground if ground != null else player.position)
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
