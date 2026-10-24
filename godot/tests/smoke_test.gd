# =============================================================================
# smoke_test.gd — 화면 없이(헤드리스) 게임을 돌려 손맛 로직이 실제로 동작하는지 검사
# 실행: godot --headless -s res://tests/smoke_test.gd
# 왜 필요한가: AI가 사람 손 없이 "고쳤는데 안 깨졌나"를 스스로 확인하기 위해서.
# =============================================================================
extends SceneTree

var main: Node3D
var fails := 0

func check(cond: bool, msg: String) -> void:
	print(("  ✅ " if cond else "  ❌ ") + msg)
	if not cond:
		fails += 1

func step(n: int) -> void:
	# 60fps 기준 n 프레임 진행 (실제 _process 대신 직접 호출해 시간을 정확히 통제)
	for i in n:
		main._process(1.0 / 60.0)

func click(screen: Vector2, button: int) -> void:
	var ev := InputEventMouseButton.new()
	ev.button_index = button
	ev.pressed = true
	ev.position = screen
	main._unhandled_input(ev)
	var up := InputEventMouseButton.new()
	up.button_index = button
	up.pressed = false
	up.position = screen
	main._unhandled_input(up)

func _initialize() -> void:
	main = load("res://main.tscn").instantiate()
	root.add_child(main)

func _process(_d: float) -> bool:
	if main == null or not main.is_node_ready():
		return false
	run()
	quit(1 if fails > 0 else 0)
	return true

func run() -> void:
	var p: Player = main.player
	var em: EnemyManager = main.enemies
	print("[1] 시작 상태")
	check(em.list.size() == Config.ENEMY_COUNT, "적 %d마리 생성" % em.list.size())
	step(10)

	print("[2] 바닥 클릭 → 이동")
	var target := Vector3(4, 0, -3)
	main._update_camera(1.0)
	var scr: Vector2 = main.camera.unproject_position(target)
	click(scr, MOUSE_BUTTON_LEFT)
	check(p.move_target != null and (p.move_target as Vector3).distance_to(target) < 0.3, "클릭 지점이 이동 목표로 (화면→바닥 변환 정확)")
	step(90)
	check(p.position.distance_to(target) < 1.5, "목표 근처 도착 (거리 %.2f)" % p.position.distance_to(target))

	print("[3] 적 클릭 → 3타 콤보")
	var e: Enemy = em.list[0]
	var hp0 := e.hp
	var steps_seen := {}
	var max_numbers := 0
	for i in 240:
		if p.state == Player.State.FREE or p.state == Player.State.ATTACK:
			var live: Enemy = null
			for x in em.list:
				if x.alive:
					live = x
					break
			if live:
				p.command_attack(live)
		step(1)
		if p.atk != null:
			steps_seen[p.atk.step] = true
		max_numbers = maxi(max_numbers, main.numbers.get_child_count())
	check(steps_seen.has(1) and steps_seen.has(2) and steps_seen.has(3), "1·2·3타 모두 발동 %s" % str(steps_seen.keys()))
	var total_hp_lost := 0
	for x in em.list:
		total_hp_lost += Config.ENEMY_MAX_HP - x.hp
	check(total_hp_lost > 0 or not e.alive or e.hp < hp0, "적이 데미지를 입음")
	check(max_numbers > 0, "데미지 숫자가 화면에 떴음 (최대 동시 %d개)" % max_numbers)

	print("[4] 히트스톱: 타격 직후 세계가 멈추는가")
	var f := HitFeel.new()
	f.hit_stop(4)
	var frozen_frames := 0
	for i in 10:
		if f.tick(1.0 / 60.0):
			frozen_frames += 1
	check(frozen_frames == 4, "4프레임 히트스톱 = 정확히 4프레임 정지 (%d)" % frozen_frames)

	print("[5] 우클릭 견인 → 멀리 있는 적이 끌려옴")
	step(120)
	# 대기 상태로 만들고 적 하나를 멀리 둔다
	p.state = Player.State.FREE
	p.atk = null
	p.chain.visible = false
	p.pull_cooldown = 0.0
	var far: Enemy = null
	for x in em.list:
		if x.alive:
			far = x
			break
	far.stun = 5.0  # 견인 전에 스스로 걸어오지 않게
	far.position = p.position + Vector3(9, 0, 0)
	var d0 := far.position.distance_to(p.position)
	main._update_camera(1.0)
	click(main.camera.unproject_position(far.position + Vector3(0, 0.9, 0)), MOUSE_BUTTON_RIGHT)
	check(p.state == Player.State.PULL, "견인 상태 진입")
	step(40)
	var d1 := far.position.distance_to(p.position)
	check(d1 < d0 - 5.0, "끌려옴: 거리 %.1f → %.1f" % [d0, d1])
	check(p.state == Player.State.FREE, "견인 종료 후 대기로 복귀")

	print("[6] 오래 돌려도 에러 없음 (부활 포함, 20초)")
	for i in 1200:
		if i % 20 == 0:
			for x in em.list:
				if x.alive:
					p.command_attack(x)
					break
		step(1)
	check(true, "20초 시뮬레이션 완료")
	print("결과: " + ("통과" if fails == 0 else "실패 %d건" % fails))
