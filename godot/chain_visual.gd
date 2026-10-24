# =============================================================================
# chain_visual.gd — 철삭(쇠사슬)의 "모습" + 휘두른 자리의 빛 잔상 (src/chain.ts)
# 판정(누가 맞나)은 player.gd 에서 하고, 여기는 그림만 담당한다.
# =============================================================================
class_name ChainVisual
extends Node3D

var trail: SwingTrail
var _links: Array[MeshInstance3D] = []
var _head: MeshInstance3D
var _points: Array[Vector3] = []
var _spin := 0.0

func _init() -> void:
	# 마디 하나 = 납작한 박스. 하나씩 90도 돌려 끼우면 사슬 고리처럼 보인다.
	var link_mesh := BoxMesh.new()
	link_mesh.size = Vector3(0.2, 0.07, 1.0)  # 길이(z)는 1, 나중에 마디 간격만큼 늘린다
	var link_mat := U.flat_unlit(Config.CHAIN_LINK_COLOR)
	for i in Config.CHAIN_SEGMENTS:
		var m := MeshInstance3D.new()
		m.mesh = link_mesh
		m.material_override = link_mat
		_links.append(m)
		add_child(m)
	for i in Config.CHAIN_SEGMENTS + 1:
		_points.append(Vector3.ZERO)
	# 끝의 추: 주황 큐브
	_head = MeshInstance3D.new()
	var head_mesh := BoxMesh.new()
	head_mesh.size = Vector3(0.42, 0.42, 0.42)
	_head.mesh = head_mesh
	_head.material_override = U.flat_unlit(Config.CHAIN_HEAD_COLOR)
	add_child(_head)
	visible = false
	trail = SwingTrail.new()

func set_shape(hand: Vector3, angle: float, radius: float, head_y: float, lag: float, sag: float) -> void:
	# 손(hand) 기준 극좌표(각도, 거리)로 사슬 끝을 받는다.
	# lag = 휘두를 때 사슬 몸통이 끝보다 뒤처지는 각도 → 채찍처럼 휘어 보여 속도감이 난다
	# sag = 중력으로 처지는 정도
	var n := Config.CHAIN_SEGMENTS
	for i in n + 1:
		var t := float(i) / n  # 0 = 손, 1 = 끝
		var a := angle - lag * pow(1.0 - t, 1.5)  # 손 쪽일수록 많이 뒤처짐
		var r := radius * t
		_points[i] = Vector3(
			hand.x + cos(a) * r,
			hand.y + (head_y - hand.y) * t - sag * sin(PI * t),
			hand.z + sin(a) * r)
	for i in n:
		var p := _points[i]
		var q := _points[i + 1]
		var d := q - p
		var length := d.length()
		var link := _links[i]
		if length < 1e-4:
			link.visible = false
			continue
		link.visible = true
		# 박스의 긴 쪽이 다음 점을 향하게. 거의 수직이면 기준 '위' 방향을 바꿔 계산 오류를 피한다
		var up := Vector3.UP if absf(d.normalized().y) < 0.99 else Vector3.RIGHT
		var basis := Basis.looking_at(d, up)
		if i % 2 == 1:
			basis = basis * Basis(Vector3(0, 0, 1), PI / 2)  # 번갈아 눕혀 고리 느낌
		basis = basis * Basis.from_scale(Vector3(1, 1, maxf(0.01, length * 0.92)))
		link.transform = Transform3D(basis, (p + q) * 0.5)
	_head.position = _points[n]
	_spin += 0.35
	_head.rotation = Vector3(_spin, _spin * 0.7, 0)


# -----------------------------------------------------------------------------
# 궤적 잔상: 매 순간 "사슬 안쪽 점"과 "사슬 끝 점"을 기록해 띠(리본)로 잇고,
# 오래된 부분일수록 투명하게 → 휘두른 자리에 빛나는 호가 남았다가 사라진다.
# -----------------------------------------------------------------------------
class SwingTrail:
	extends MeshInstance3D

	var _samples: Array = []  # { inner, outer, age, start }
	var _im := ImmediateMesh.new()  # 매 프레임 모양을 새로 그리는 메쉬

	func _init() -> void:
		mesh = _im
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.vertex_color_use_as_albedo = true        # 정점마다 색/투명도를 따로
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD  # 빛처럼 겹칠수록 밝아짐
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED    # 위아래 어디서 봐도 보이게
		material_override = mat
		# 모양이 계속 바뀌므로 화면 밖 판정에 걸려 사라지지 않게 넉넉한 범위를 준다
		custom_aabb = AABB(Vector3(-100, -10, -100), Vector3(200, 20, 200))

	func add(inner: Vector3, outer: Vector3, start: bool) -> void:
		_samples.append({ "inner": inner, "outer": outer, "age": 0.0, "start": start })
		if _samples.size() > Config.TRAIL_MAX_SAMPLES:
			_samples.pop_front()

	func _alpha_of(s: Dictionary) -> float:
		return Config.TRAIL_ALPHA * pow(1.0 - s.age / Config.TRAIL_LIFETIME, Config.TRAIL_FADE_POWER)

	func tick(dt: float) -> void:
		for s in _samples:
			s.age += dt
		while _samples.size() > 0 and _samples[0].age >= Config.TRAIL_LIFETIME:
			_samples.pop_front()
		_im.clear_surfaces()
		var tri_count := 0
		for i in range(1, _samples.size()):
			if not _samples[i].start:
				tri_count += 1
		if tri_count == 0:
			return  # 그릴 게 없으면 빈 메쉬 (빈 surface 를 만들면 경고가 난다)
		_im.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
		for i in range(1, _samples.size()):
			var a: Dictionary = _samples[i - 1]
			var b: Dictionary = _samples[i]
			if b.start:
				continue  # 새 휘두르기의 첫 점은 이전 것과 잇지 않는다
			var aa := _alpha_of(a)
			var ab := _alpha_of(b)
			# 안쪽 끝은 옅게(×0.15), 바깥(사슬 끝 궤적)은 진하게 → 칼날 같은 빛줄기
			_put(a.inner, Config.TRAIL_COLOR_INNER, aa * 0.15)
			_put(a.outer, Config.TRAIL_COLOR_OUTER, aa)
			_put(b.outer, Config.TRAIL_COLOR_OUTER, ab)
			_put(a.inner, Config.TRAIL_COLOR_INNER, aa * 0.15)
			_put(b.outer, Config.TRAIL_COLOR_OUTER, ab)
			_put(b.inner, Config.TRAIL_COLOR_INNER, ab * 0.15)
		_im.surface_end()

	func _put(p: Vector3, c: Color, alpha: float) -> void:
		_im.surface_set_color(Color(c.r, c.g, c.b, alpha))
		_im.surface_add_vertex(p)
