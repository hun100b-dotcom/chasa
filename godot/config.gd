# =============================================================================
# config.gd — 손맛 튜닝용 "조절판" (Three.js판 src/config.ts 를 숫자 그대로 옮김)
#
# 왜 숫자를 그대로 옮기나?
#   이 Godot판의 목적은 "엔진만 바꿨을 때 손맛이 같은가/다른가"를 비교하는 것이다.
#   숫자가 다르면 엔진 차이인지 숫자 차이인지 구분할 수 없다. 그래서 1:1로 맞췄다.
#
# 단위: 거리=월드 단위(캐릭터 키 약 1.8) / 시간=초 / 히트스톱만 프레임(1/60초) / 각도=도(°)
#
# ★ 빠른 찾기표는 src/config.ts 맨 위와 같다. 이름 규칙: config.ts 의 CAMERA.PITCH_DEG → CAMERA_PITCH_DEG
# =============================================================================
class_name Config

# --- 1) 카메라: 고정 쿼터뷰 ---------------------------------------------------
const CAMERA_PITCH_DEG := 45.0        # 내려다보는 각도
const CAMERA_YAW_DEG := 45.0          # 좌우 회전각 (45 = 마름모 쿼터뷰)
const CAMERA_VIEW_HEIGHT := 16.0      # 화면 세로로 보이는 월드 길이 (작을수록 확대)
const CAMERA_FOLLOW_SMOOTHNESS := 8.0 # 카메라가 따라가는 부드러움

# --- 2) 맵 ---------------------------------------------------------------------
const ARENA_HALF_SIZE := 14.0         # 28 x 28 정사각형 바닥

# --- 3) 플레이어 ---------------------------------------------------------------
const PLAYER_MOVE_SPEED := 9.0
const PLAYER_RADIUS := 0.5
const PLAYER_TURN_SPEED := 22.0       # 몸 돌리는 속도(라디안/초)
const PLAYER_HAND_HEIGHT := 1.0       # 사슬이 시작되는 손 높이
const PLAYER_ARRIVE_DISTANCE := 0.15

# --- 4) 철삭 3타 콤보 (한 줄이 한 타) ------------------------------------------
# 각 항목 뜻은 config.ts 의 ComboStep 주석과 같다.
#   damage 데미지 / reach 사슬 길이 / sweep_deg 훑는 각도 / start_offset_deg 시작 옆각
#   dir 휘두르는 방향(+1 반시계, -1 시계) / windup 선딜 / swing 휘두름 / recover 후딜
#   hit_stop_frames 히트스톱 / shake 흔들림 / knockback 넉백 / stun 멍함 / lunge 전진
const COMBO := [
	{ "name": "1타 (횡베기)", "damage": 12, "reach": 4.6, "sweep_deg": 150.0, "start_offset_deg": 75.0, "dir": 1,
	  "windup": 0.09, "swing": 0.15, "recover": 0.13,
	  "hit_stop_frames": 2, "shake": 0.35, "knockback": 9.0, "stun": 0.28, "lunge": 0.9 },
	{ "name": "2타 (역횡베기)", "damage": 14, "reach": 4.6, "sweep_deg": 150.0, "start_offset_deg": 75.0, "dir": -1,
	  "windup": 0.08, "swing": 0.15, "recover": 0.13,
	  "hit_stop_frames": 2, "shake": 0.45, "knockback": 10.0, "stun": 0.3, "lunge": 0.9 },
	{ "name": "3타 (회전 후려치기)", "damage": 30, "reach": 5.6, "sweep_deg": 360.0, "start_offset_deg": 35.0, "dir": 1,
	  "windup": 0.16, "swing": 0.3, "recover": 0.36,
	  "hit_stop_frames": 4, "shake": 1.0, "knockback": 24.0, "stun": 0.65, "lunge": 0.0 },
]
const COMBO_RESET_TIME := 0.6         # 콤보 이음 허용 시간
const ATTACK_START_RANGE := 3.6       # 이 거리 안이면 휘두르기 시작(멀면 달려감)
const DAMAGE_VARIANCE := 0.1          # 데미지 ±10%
const HIT_PADDING := 0.25             # 판정 후함

# --- 5) 우클릭 견인 -------------------------------------------------------------
const PULL_RANGE := 13.0
const PULL_THROW_TIME := 0.12
const PULL_DRAG_SPEED := 42.0
const PULL_STOP_DISTANCE := 2.0
const PULL_RETRACT_TIME := 0.14
const PULL_DAMAGE := 8
const PULL_HITSTOP_FRAMES := 3
const PULL_SHAKE := 0.5
const PULL_ARRIVE_SHAKE := 0.4
const PULL_STUN := 0.8
const PULL_COOLDOWN := 0.5
const PULL_PICK_RADIUS := 3.0

# --- 6) 타격감 ------------------------------------------------------------------
const FEEL_FRAME_TIME := 1.0 / 60.0
const FEEL_SHAKE_MAX_OFFSET := 0.28   # PD 피드백(10-24) "흔들림이 너무 심함" → 0.55에서 절반으로
const FEEL_SHAKE_DECAY := 5.0         # 흔들림이 더 빨리 가라앉게 (3.8 → 5.0)
const FEEL_KILL_BONUS_FRAMES := 2
const FEEL_KILL_BONUS_SHAKE := 0.3
const FEEL_KNOCKBACK_TANGENT_MIX := 0.35

# --- 7) 사슬 모양 + 잔상 ---------------------------------------------------------
const CHAIN_SEGMENTS := 18
const CHAIN_LINK_COLOR := Color("dfe9ff")
const CHAIN_HEAD_COLOR := Color("ff9a2e")

const TRAIL_LIFETIME := 0.26
const TRAIL_ALPHA := 0.85
const TRAIL_FADE_POWER := 1.6
const TRAIL_SUBSTEPS := 4
const TRAIL_INNER_RATIO := 0.45
const TRAIL_MAX_SAMPLES := 120
const TRAIL_COLOR_OUTER := Color("c8f4ff")
const TRAIL_COLOR_INNER := Color("4f8cff")

# --- 8) 데미지 숫자 ---------------------------------------------------------------
const NUMBER_LIFETIME := 0.85
const NUMBER_FADE_TIME := 0.3
const NUMBER_POP_SPEED_MIN := 300.0
const NUMBER_POP_SPEED_MAX := 420.0
const NUMBER_SPREAD_SPEED := 110.0
const NUMBER_GRAVITY := 1100.0
const NUMBER_POP_SCALE := 1.9
const NUMBER_POP_TIME := 0.14
const NUMBER_FONT_BASE := 22.0
const NUMBER_FONT_PER_DAMAGE := 0.9
const NUMBER_FONT_MAX := 60.0
const NUMBER_COLOR_NORMAL := Color("ffffff")
const NUMBER_COLOR_HEAVY := Color("ffd23f")
const NUMBER_COLOR_PULL := Color("7fd8ff")

# --- 9) 적 (접근형 샌드백) ----------------------------------------------------------
const ENEMY_COUNT := 4
const ENEMY_MAX_HP := 80
const ENEMY_RADIUS := 0.6
const ENEMY_HEIGHT := 1.8
const ENEMY_SPEED := 2.8
const ENEMY_SPEED_VARIANCE := 0.2
const ENEMY_STOP_DISTANCE := 1.7
const ENEMY_KNOCKBACK_FRICTION := 5.5
const ENEMY_FLASH_TIME := 0.14
const ENEMY_SQUASH := 0.25
const ENEMY_KILL_KNOCKBACK_MULT := 1.5
const ENEMY_DEATH_HOLD := 0.25
const ENEMY_DEATH_SHRINK := 0.3
const ENEMY_RESPAWN_DELAY := 1.6
const ENEMY_SPAWN_DISTANCE := 11.0
const ENEMY_SPAWN_POP_TIME := 0.3
const ENEMY_PICK_RADIUS := 1.0

# --- 10) 클릭 표시 -------------------------------------------------------------------
const CLICK_MARKER_LIFETIME := 0.45
const CLICK_MARKER_COLOR := Color("7fe3ff")
