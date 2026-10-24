# =============================================================================
# damage_numbers.gd — 튀어오르는 데미지 숫자 (src/effects.ts 의 DamageNumbers)
# 3D 글자 대신 화면 위 2D 글자(Label)를 띄운다. 에셋이 필요 없고 선명하다.
# =============================================================================
class_name DamageNumbers
extends CanvasLayer

var camera: Camera3D
var _items: Array = []  # { label, pos(Vector2 화면 픽셀), vel, age }

func spawn(world_pos: Vector3, value: int, kind: String) -> void:
	# 3D 위치 → 화면 픽셀 위치로 변환
	var screen := camera.unproject_position(world_pos)
	var label := Label.new()
	label.text = str(value)
	var size := minf(Config.NUMBER_FONT_MAX, Config.NUMBER_FONT_BASE + value * Config.NUMBER_FONT_PER_DAMAGE)
	label.add_theme_font_size_override("font_size", int(size))
	var color := Config.NUMBER_COLOR_NORMAL
	if kind == "heavy":
		color = Config.NUMBER_COLOR_HEAVY
	elif kind == "pull":
		color = Config.NUMBER_COLOR_PULL
	elif kind == "hurt":
		color = Config.NUMBER_COLOR_HURT
	_push(label, screen, color)

func spawn_text(world_pos: Vector3, text: String, color: Color) -> void:
	# 숫자 대신 짧은 글자(예: "+10 NEOK", "CAN'T SEND")를 같은 방식으로 띄운다
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 22)
	_push(label, camera.unproject_position(world_pos), color)

func _push(label: Label, screen: Vector2, color: Color) -> void:
	label.add_theme_color_override("font_color", color)
	# 검은 테두리: 어두운/밝은 바닥 어디서든 읽히게 (CSS text-shadow 와 같은 역할)
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.add_theme_constant_override("outline_size", 6)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE  # 클릭은 아래 게임 화면으로 통과
	add_child(label)
	_items.append({
		"label": label, "pos": screen, "age": 0.0,
		"vel": Vector2(randf_range(-Config.NUMBER_SPREAD_SPEED, Config.NUMBER_SPREAD_SPEED),
			-randf_range(Config.NUMBER_POP_SPEED_MIN, Config.NUMBER_POP_SPEED_MAX)),  # 화면은 아래가 + → 위로는 마이너스
	})

func tick(dt: float) -> void:
	# dt = 진짜 시간. 히트스톱 중에도 숫자는 자연스럽게 흐른다.
	for i in range(_items.size() - 1, -1, -1):
		var n: Dictionary = _items[i]
		n.age += dt
		var label: Label = n.label
		if n.age >= Config.NUMBER_LIFETIME:
			label.queue_free()
			_items.remove_at(i)
			continue
		n.vel.y += Config.NUMBER_GRAVITY * dt  # 중력: 솟았다가 떨어진다
		n.pos += n.vel * dt
		# 팝 연출: 처음에 크게 → 정상 크기로
		var pop := maxf(0.0, 1.0 - n.age / Config.NUMBER_POP_TIME)
		var s := 1.0 + (Config.NUMBER_POP_SCALE - 1.0) * pop
		var remain: float = Config.NUMBER_LIFETIME - n.age
		var opacity := remain / Config.NUMBER_FADE_TIME if remain < Config.NUMBER_FADE_TIME else 1.0
		# 글자 가운데를 기준으로 확대되도록 pivot 을 가운데에 둔다
		label.pivot_offset = label.size * 0.5
		label.position = n.pos - label.size * 0.5
		label.scale = Vector2(s, s)
		label.modulate.a = opacity
