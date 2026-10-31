# =============================================================================
# stain_field.gd — 원념 얼룩. 파혼한 자리에 남는 검붉은 웅덩이 (COMBAT-SPEC P-007~P-011)
#
# 왜 있나? 파혼은 즉시 끝나고 엽전도 주지만, 그 대가가 '땅에 남는다'.
#   - 밟으면 느려진다 (P-009)
#   - 3개가 겹치면 사나운 적이 솟아난다 (P-010)
#   → "빨리 끝낼까(파혼), 시간을 들일까(천도)" 선택에 무게가 생긴다.
# =============================================================================
class_name StainField
extends Node3D

var _items: Array = []   # { node, mat, pos, age }

func add(pos: Vector3) -> Variant:
	# 얼룩 하나 추가. 겹친 얼룩이 3개 이상이 되면 그 가운데 지점(Vector3)을 돌려준다 → 소환 신호
	var node := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = Config.STAIN_RADIUS
	cyl.bottom_radius = Config.STAIN_RADIUS
	cyl.height = 0.02
	cyl.radial_segments = 32
	node.mesh = cyl
	var mat := U.flat_unlit(Color(0.45, 0.04, 0.08, 0.55))
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	node.material_override = mat
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.position = Vector3(pos.x, 0.02 + _items.size() * 0.002, pos.z)  # 살짝씩 높여 겹친 곳이 깜빡이지 않게
	add_child(node)
	var item := {"node": node, "mat": mat, "pos": Vector3(pos.x, 0, pos.z), "age": 0.0}
	_items.append(item)

	# 새 얼룩과 겹치는(중심 거리 < 반경×2) 얼룩들을 모은다
	var group: Array = []
	for it in _items:
		if (it.pos as Vector3).distance_to(item.pos) < Config.STAIN_RADIUS * 2.0:
			group.append(it)
	if group.size() < Config.STAIN_SUMMON_COUNT:
		return null
	# 소환: 겹친 얼룩들은 '사나운 적'으로 뭉쳐 사라진다
	var center := Vector3.ZERO
	for it in group:
		center += it.pos
		(it.node as Node).queue_free()
		_items.erase(it)
	return center / group.size()

func count() -> int:
	return _items.size()

func is_on_stain(pos: Vector3) -> bool:
	for it in _items:
		if Vector2(pos.x - it.pos.x, pos.z - it.pos.z).length() <= Config.STAIN_RADIUS:
			return true
	return false

func clear() -> void:
	for it in _items:
		(it.node as Node).queue_free()
	_items.clear()

func tick(dt: float) -> void:
	for i in range(_items.size() - 1, -1, -1):
		var it: Dictionary = _items[i]
		it.age += dt
		var remain: float = Config.STAIN_DURATION - it.age
		if remain <= 0.0:
			(it.node as Node).queue_free()
			_items.remove_at(i)
			continue
		# 마지막 2초 동안 서서히 옅어진다 (언제 없어질지 눈으로 보이게)
		var fade := clampf(remain / 2.0, 0.0, 1.0)
		(it.mat as StandardMaterial3D).albedo_color.a = 0.55 * fade
