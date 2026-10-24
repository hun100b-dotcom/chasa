# =============================================================================
# click_marker.gd — 이동 클릭 지점에 나타났다 모이는 링 (src/effects.ts 의 ClickMarker)
# =============================================================================
class_name ClickMarker
extends MeshInstance3D

var _age := INF  # 처음엔 안 보이는 상태
var _mat: StandardMaterial3D

func _init() -> void:
	# 납작한 원환(도넛)을 링으로 쓴다
	var torus := TorusMesh.new()
	torus.inner_radius = 0.3
	torus.outer_radius = 0.42
	torus.rings = 28
	mesh = torus
	scale = Vector3(1, 0.05, 1)
	_mat = U.flat_unlit(Config.CLICK_MARKER_COLOR)
	_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material_override = _mat
	visible = false

func show_at(point: Vector3) -> void:
	position = Vector3(point.x, 0.04, point.z)
	_age = 0.0
	visible = true

func tick(dt: float) -> void:
	if not visible:
		return
	_age += dt
	var t := _age / Config.CLICK_MARKER_LIFETIME
	if t >= 1.0:
		visible = false
		return
	var s := 1.6 - 0.9 * t  # 바깥에서 안쪽으로 모이는 링
	scale = Vector3(s, 0.05, s)
	_mat.albedo_color.a = 1.0 - t
