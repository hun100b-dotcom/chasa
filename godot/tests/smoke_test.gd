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
	var m0 := e.maedhim
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
	var total_lost := 0
	for x in em.list:
		total_lost += x.maedhim_max - x.maedhim
	check(total_lost > 0 or not e.alive or e.maedhim < m0, "적의 맺힘이 깎임")
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
	# 적이 이제 공격하므로, 끝난 직전에 맞으면 '휘청(HURT)'일 수도 있다 → "견인은 끝났나"만 본다
	check(p.state != Player.State.PULL, "견인 종료 후 대기로 복귀")

	print("[5-2] 키보드: Space 제자리 휘두르기, Q 견인")
	step(60)
	p.state = Player.State.FREE
	p.atk = null
	p.move_target = null
	var pos_before := p.position
	var key := InputEventKey.new()
	key.keycode = KEY_SPACE
	key.pressed = true
	main._unhandled_input(key)
	check(p.state == Player.State.ATTACK and p.chase_target == null, "Space → 그 자리에서 휘두르기 시작(달려가지 않음)")
	step(60)
	p.pull_cooldown = 0.0
	p.state = Player.State.FREE
	p.atk = null
	var key_q := InputEventKey.new()
	key_q.keycode = KEY_Q
	key_q.pressed = true
	main._unhandled_input(key_q)
	check(p.state == Player.State.PULL, "Q → 견인 시작")
	step(40)

	_core_loop_tests(p, em)

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


# =============================================================================
# 핵심 루프: 적 공격 → 무릎(처결 대기) → 천도 / 파혼 → 얼룩 → 사나운 적
# =============================================================================
func _reset_player(p: Player) -> void:
	p.state = Player.State.FREE
	p.atk = null
	p.pull_run = null
	p.chain.visible = false
	p.move_target = null
	p.chase_target = null
	p.judge_target = null
	p.has_buffered = false

func _freeze_others(em: EnemyManager, keep: Enemy) -> void:
	# 검사 대상 말고는 멀리 치우고 오래 경직시켜 끼어들지 못하게
	for x in em.list:
		if x != keep:
			x.position = Vector3(18, 0, 18)
			x.stun = 999.0
			x._windup = -1.0

func _core_loop_tests(p: Player, em: EnemyManager) -> void:
	print("[7] 적이 공격해서 플레이어 체력이 깎인다")
	step(30)
	_reset_player(p)
	p.position = Vector3.ZERO
	p.hp = Config.PLAYER_MAX_HP
	var a: Enemy = em.list[0]
	if a.state != Enemy.S.ACTIVE:
		a.respawn(Vector3(1.5, 0, 0))
	_freeze_others(em, a)
	a.position = Vector3(1.5, 0, 0)
	a.stun = 0.0
	a._atk_cd = 0.0
	var hp_before := p.hp
	step(60)  # 예비동작 0.4초 + 여유
	check(p.hp == hp_before - a.attack_damage(), "적 공격 1회 = 체력 -%d (%d → %d)" % [a.attack_damage(), hp_before, p.hp])

	print("[8] 맺힘 0 → 죽지 않고 무릎 꿇음(처결 대기)")
	_reset_player(p)
	a.stun = 999.0
	var knelt := a.take_hit(a.maedhim, Vector3(1, 0, 0), 0.0, 0.1)
	check(knelt and a.kneeling, "무릎 꿇음 상태 진입")
	check(absf(a.wait_left - a.wait_time_for_soul()) < 0.01, "혼 종류(%s)별 대기 시간 %.0f초" % [a.soul, a.wait_left])
	step(30)
	check(a.wait_left < a.wait_total, "대기 타이머가 흐름")

	print("[9] 길게 누르면 천도: 캐스팅 → 넋/기억 획득, 시야 좁아짐")
	if not a.can_tendo():
		a.soul = "fresh"  # 덩어리면 천도가 안 되니 검사용으로 바꾼다
	a.position = Vector3(1.5, 0, 0)
	a.wait_left = 10.0
	var neok0 := p.neok
	main._update_camera(1.0)
	var scr: Vector2 = main.camera.unproject_position(a.position + Vector3(0, 0.4, 0))
	var down := InputEventMouseButton.new()
	down.button_index = MOUSE_BUTTON_LEFT
	down.pressed = true
	down.position = scr
	main._unhandled_input(down)
	step(25)  # 0.3초 넘게 누름
	check(p.state == Player.State.CAST and a.state == Enemy.S.SENDING, "누르고 있으니 천도 캐스팅 시작")
	step(15)
	check(main.vision_ratio() < 0.65, "캐스팅 중 시야 좁아짐 (%.2f)" % main.vision_ratio())
	var up := InputEventMouseButton.new()
	up.button_index = MOUSE_BUTTON_LEFT
	up.pressed = false
	up.position = scr
	main._unhandled_input(up)
	check(p.state == Player.State.CAST, "손을 떼도 캐스팅은 계속 (짧은 클릭으로 오인하지 않음)")
	step(80)
	check(a.state == Enemy.S.GONE and a.gone_by == "tendo", "천도 완료: 혼이 떠남")
	check(p.neok == neok0 + Config.TENDO_NEOK, "넋 +%d" % Config.TENDO_NEOK)
	check(p.tendo_chain_left > 0.0, "연속 천도 창 열림 (%.1f초)" % p.tendo_chain_left)

	print("[10] 연속 천도는 0.8초로 빨라짐")
	var b: Enemy = em.list[1]
	b.respawn(Vector3(-1.5, 0, 0))
	b.soul = "fresh"
	_freeze_others(em, b)
	b.take_hit(b.maedhim, Vector3.ZERO, 0.0, 0.1)
	b.stun = 999.0
	p.command_tendo(b)
	step(2)
	check(p.state == Player.State.CAST and absf(p.cast_total - Config.TENDO_CHAIN_CAST_TIME) < 0.01, "캐스팅 시간 %.1f초" % p.cast_total)
	step(60)
	check(b.state == Enemy.S.GONE, "두 번째 천도 완료")

	print("[11] 캐스팅 중 맞으면 끊김 (T-008 임시 해석)")
	var c: Enemy = em.list[2]
	c.respawn(Vector3(0, 0, 1.5))
	c.soul = "year"
	_freeze_others(em, c)
	c.take_hit(c.maedhim, Vector3.ZERO, 0.0, 0.1)
	c.stun = 999.0
	p.command_tendo(c)
	step(2)
	p.take_damage(5)
	check(c.kneeling and p.state == Player.State.HURT, "혼은 다시 대기, 플레이어는 휘청")
	step(30)

	print("[12] 짧게 클릭하면 파혼: 즉시 터짐, 엽전·업, 주변 적 피해, 얼룩")
	_reset_player(p)
	var victim: Enemy = em.list[3]
	victim.respawn(Vector3(0, 0, -1.5))
	_freeze_others(em, c)
	victim.position = c.position + Vector3(1.5, 0, 0)  # 폭발 반경 안에 다른 적
	victim.stun = 999.0
	var vm := victim.maedhim
	var coin0 := p.coin
	var karma0 := p.karma
	var stains0: int = main.stains.count()
	main._update_camera(1.0)
	click(main.camera.unproject_position(c.position + Vector3(0, 0.4, 0)), MOUSE_BUTTON_LEFT)
	step(2)
	check(c.state == Enemy.S.GONE and c.gone_by == "pahon", "파혼: 혼이 터짐")
	check(p.coin == coin0 + Config.PAHON_COIN and p.karma == karma0 + Config.PAHON_KARMA, "엽전 +%d, 업 +%d" % [Config.PAHON_COIN, Config.PAHON_KARMA])
	check(victim.maedhim == vm - Config.PAHON_DAMAGE, "폭발 반경 안 적 맺힘 -%d" % Config.PAHON_DAMAGE)
	check(main.stains.count() == stains0 + 1, "원념 얼룩 생김")

	print("[13] 얼룩 위는 느림, 3개 겹치면 사나운 적 소환")
	main.stains.clear()
	main.stains.add(Vector3(-6, 0, -6))
	p.position = Vector3(-6, 0, -6)
	step(1)
	check(absf(p.speed_mult - (1.0 - Config.STAIN_SLOW)) < 0.01, "얼룩 위 이동속도 x%.1f" % p.speed_mult)
	var n0 := em.list.size()
	main.stains.add(Vector3(-5, 0, -6))
	p.on_pahon.call(Vector3(-5.5, 0, -5))
	check(em.list.size() == n0 + 1 and em.list[-1].fierce, "사나운 적 1마리 소환 (총 %d)" % em.list.size())
	check(main.stains.count() == 0, "겹친 얼룩은 소환에 쓰여 사라짐")
	var f: Enemy = em.list[-1]
	check(f.maedhim_max == int(Config.MAEDHIM_NORMAL * Config.FIERCE_MULT), "사나운 적 맺힘 %d (+50%%)" % f.maedhim_max)

	print("[14] 덩어리 혼은 천도 불가")
	var l: Enemy = em.list[4]
	l.respawn(p.position + Vector3(1.5, 0, 0))
	l.soul = "lump"
	_freeze_others(em, l)
	l.take_hit(l.maedhim, Vector3.ZERO, 0.0, 0.1)
	_reset_player(p)
	p.command_tendo(l)
	step(3)
	check(p.state != Player.State.CAST and l.kneeling, "천도 거부, 계속 대기")

	print("[14-2] 업 단계 (P1-015)")
	var kk := p.karma
	p.karma = 9
	check(p.karma_tier() == 0 and p.reward_mult() == 1.0, "업 9 = K-001, 보상 그대로")
	p.karma = 10
	check(p.karma_tier() == 1, "업 10 = K-002")
	p.karma = 30
	check(p.karma_tier() == 2 and absf(p.reward_mult() - 0.9) < 0.001, "업 30 = K-003, 보상 x0.9")
	p.karma = 60
	check(p.karma_tier() == 3, "업 60 = K-004")
	p.karma = kk

	print("[15] 체력 0 → 판 다시 시작")
	_reset_player(p)
	p.hp = 1
	main.enemies.on_attack.call(em.list[0])
	step(1)
	check(p.hp == Config.PLAYER_MAX_HP and main.stains.count() == 0, "체력 회복, 얼룩 정리")
	var extras := 0
	for x in em.list:
		if x.extra:
			extras += 1
	check(extras == 0 and em.list.size() == Config.ENEMY_COUNT, "소환된 적 정리 (%d마리)" % em.list.size())
