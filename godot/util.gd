# =============================================================================
# util.gd — 여러 파일에서 같이 쓰는 작은 수학 도구 (src/util.ts 와 같은 동작)
# =============================================================================
class_name U

static func ease_out_quad(t: float) -> float:
	# 처음엔 빠르고 끝에서 느려짐 (채찍처럼 확 뻗는 느낌)
	return 1.0 - (1.0 - t) * (1.0 - t)

static func ease_in_quad(t: float) -> float:
	# 처음엔 느리고 끝에서 빨라짐 (되감기)
	return t * t

static func wrap_pi(a: float) -> float:
	# 각도를 -π ~ +π 로 정리 (360° 돌면 제자리라서 필요)
	a = fmod(a + PI, TAU)
	if a < 0.0:
		a += TAU
	return a - PI

static func turn_toward(a: float, b: float, max_step: float) -> float:
	# a 에서 b 로 '가까운 쪽'으로 최대 max_step 만큼만 돈다
	var diff := wrap_pi(b - a)
	if absf(diff) <= max_step:
		return b
	return a + signf(diff) * max_step

static func swept_through(prev: float, cur: float, target: float, half_width: float) -> bool:
	# "사슬 끝이 prev→cur 각도로 훑는 동안 target 각도의 적을 스쳤나?"
	# 사슬은 한 순간이 아니라 호를 그리며 지나가므로, 프레임 사이 구간 전체를 검사한다.
	# half_width = 적 몸통 폭(각도). 몸통에 닿기만 해도 맞은 걸로 친다.
	var delta := cur - prev
	if delta == 0.0:
		return false
	var s := signf(delta)
	var from := prev - s * half_width
	var length := absf(delta) + half_width * 2.0
	var d := (target - from) * s
	d = fmod(fmod(d, TAU) + TAU, TAU)
	return d <= length

static func flat_unlit(color: Color) -> StandardMaterial3D:
	# 조명 영향 없이 색 그대로 보이는 재질 (사슬처럼 '빛나는' 물체용)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = color
	return m

static func matte(color: Color) -> StandardMaterial3D:
	# 반짝임 없는 무광 재질 (Three.js 의 Lambert 재질과 비슷한 느낌)
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = 1.0
	m.metallic_specular = 0.0
	return m
