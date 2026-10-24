# =============================================================================
# hit_feel.gd — 히트스톱(순간 정지) + 화면 흔들림 (src/effects.ts 의 HitFeel)
# =============================================================================
class_name HitFeel
extends RefCounted

var _hit_stop_timer := 0.0  # 남은 정지 시간(초). 0보다 크면 게임 세계가 멈춘다.
var _shake := 0.0           # 현재 흔들림 세기(0~1)

func hit_stop(frames: int) -> void:
	# 여러 마리를 동시에 때리면 정지가 합쳐져 한참 멈추므로, 가장 긴 것 하나만 쓴다
	_hit_stop_timer = maxf(_hit_stop_timer, frames * Config.FEEL_FRAME_TIME)

func add_shake(strength: float) -> void:
	# 흔들림도 가장 센 것 하나만
	_shake = clampf(maxf(_shake, strength), 0.0, 1.0)

func tick(real_dt: float) -> bool:
	# 매 프레임 호출. true = 지금 정지 중.
	# 정지 중에도 흔들림은 계속 줄어든다 → "멈춘 화면이 부르르 떨리는" 손맛의 핵심
	_shake = maxf(0.0, _shake - Config.FEEL_SHAKE_DECAY * real_dt)
	if _hit_stop_timer > 1e-4:  # 1e-4 = 2프레임이 3프레임으로 늘어나는 오차 방지
		_hit_stop_timer -= real_dt
		return true
	_hit_stop_timer = 0.0
	return false

func get_shake_offset() -> Vector2:
	# 이번 프레임에 카메라를 얼마나 흔들지 (화면 기준 좌우 x, 상하 y)
	if _shake <= 0.0:
		return Vector2.ZERO
	var amp := Config.FEEL_SHAKE_MAX_OFFSET * _shake
	var angle := randf() * TAU  # 매 프레임 무작위 방향 → '지잉~' 진동
	return Vector2(cos(angle), sin(angle)) * amp
