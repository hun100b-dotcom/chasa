// =============================================================================
// Config.cs — 손맛 튜닝용 "조절판" (Godot판 config.gd 와 같은 값)
//
// 왜 같은 값인가? 세 엔진(Three.js / Godot / Unity)을 "엔진만 바꿔" 비교하기 위해서다.
// 흔들림·키보드 조작은 PD 피드백(2026-10-24)을 반영한 Godot판 최신값을 따른다.
// 단위: 거리=월드 단위(캐릭터 키 약 1.8) / 시간=초 / 히트스톱만 프레임(1/60초) / 각도=도(°)
// =============================================================================
using UnityEngine;

public struct ComboStep
{
    public string name;
    public int damage;          // 기본 데미지
    public float reach;         // 사슬 길이 = 공격 반경
    public float sweepDeg;      // 훑는 각도
    public float startOffsetDeg;// 정면 기준 시작 옆각
    public int dir;             // +1 반시계, -1 시계
    public float windup, swing, recover; // 선딜 / 휘두름 / 후딜
    public int hitStopFrames;   // 히트스톱 프레임
    public float shake;         // 흔들림 세기(0~1)
    public float knockback;     // 넉백 초기 속도
    public float stun;          // 멍한 시간
    public float lunge;         // 휘두르며 전진하는 거리
}

public static class Config
{
    // 1) 카메라
    public const float CAMERA_PITCH_DEG = 30f;   // 시연판: 아트팀 그림이 진짜 2:1 등각 기준이라 45° → 30° (되돌리기: 45)
    public const float CAMERA_YAW_DEG = 45f;
    public const float CAMERA_VIEW_HEIGHT = 16f;
    public const float CAMERA_FOLLOW_SMOOTHNESS = 8f;

    // 2) 맵
    // (바닥 크기는 Core/MapLayout 의 MinX~MaxX, MinZ~MaxZ 가 원본 — 아트 배치표에서 나온다)

    // 3) 플레이어
    public const float PLAYER_MOVE_SPEED = 9f;
    public const float PLAYER_RADIUS = 0.5f;
    public const float PLAYER_TURN_SPEED = 22f;
    public const float PLAYER_HAND_HEIGHT = 1.0f;
    public const float PLAYER_ARRIVE_DISTANCE = 0.15f;

    // 4) 철삭 3타 콤보
    public static readonly ComboStep[] COMBO =
    {
        new ComboStep { name = "1타 (횡베기)", damage = 12, reach = 4.6f, sweepDeg = 150f, startOffsetDeg = 75f, dir = 1,
            windup = 0.09f, swing = 0.15f, recover = 0.13f, hitStopFrames = 3, shake = 0.18f, knockback = Balance.COMBO1_KNOCKBACK_DIST * Balance.ENEMY_KNOCKBACK_FRICTION, stun = 0.28f, lunge = 0.9f },
        new ComboStep { name = "2타 (역횡베기)", damage = 14, reach = 4.6f, sweepDeg = 150f, startOffsetDeg = 75f, dir = -1,
            windup = 0.08f, swing = 0.15f, recover = 0.13f, hitStopFrames = 3, shake = 0.22f, knockback = Balance.COMBO2_KNOCKBACK_DIST * Balance.ENEMY_KNOCKBACK_FRICTION, stun = 0.3f, lunge = 0.9f },
        new ComboStep { name = "3타 (회전 후려치기)", damage = 30, reach = 5.6f, sweepDeg = 360f, startOffsetDeg = 35f, dir = 1,
            windup = 0.16f, swing = 0.3f, recover = 0.36f, hitStopFrames = 6, shake = 0.45f, knockback = Balance.COMBO3_KNOCKBACK_DIST * Balance.ENEMY_KNOCKBACK_FRICTION, stun = 0.65f, lunge = 0f },
    };
    public const float COMBO_RESET_TIME = 0.6f;
    public const float ATTACK_START_RANGE = 3.6f;
    public const float DAMAGE_VARIANCE = 0.1f;
    public const float HIT_PADDING = 0.25f;

    // 5) 견인
    public const float PULL_RANGE = 13f;
    public const float PULL_THROW_TIME = 0.12f;
    public const float PULL_DRAG_SPEED = 42f;
    public const float PULL_STOP_DISTANCE = 2.0f;
    public const float PULL_RETRACT_TIME = 0.14f;
    public const int PULL_DAMAGE = 8;
    public const int PULL_HITSTOP_FRAMES = 4;
    public const float PULL_SHAKE = 0.25f;
    public const float PULL_ARRIVE_SHAKE = 0.4f;
    public const float PULL_STUN = 0.8f;
    public const float PULL_COOLDOWN = 0.5f;
    public const float PULL_PICK_RADIUS = 3.0f;

    // 6) 타격감 (흔들림은 PD 피드백으로 절반: 0.55 → 0.28, 감쇠 3.8 → 5.0)
    public const float FEEL_FRAME_TIME = 1f / 60f;
    public const float FEEL_SHAKE_MAX_OFFSET = 0.28f;
    public const float FEEL_SHAKE_DECAY = 1.6f;
    public const int FEEL_KILL_BONUS_FRAMES = 2;
    public const float FEEL_KILL_BONUS_SHAKE = 0.3f;
    public const float FEEL_KNOCKBACK_TANGENT_MIX = 0.35f;

    // 7) 사슬 + 잔상
    public const int CHAIN_SEGMENTS = 18;
    public static readonly Color CHAIN_LINK_COLOR = Hex(0xdfe9ff);
    public static readonly Color CHAIN_HEAD_COLOR = Hex(0xff9a2e);
    public const float TRAIL_LIFETIME = 0.26f;
    public const float TRAIL_ALPHA = 0.85f;
    public const float TRAIL_FADE_POWER = 1.6f;
    public const int TRAIL_SUBSTEPS = 4;
    public const float TRAIL_INNER_RATIO = 0.45f;
    public const int TRAIL_MAX_SAMPLES = 120;
    public static readonly Color TRAIL_COLOR_OUTER = Hex(0xc8f4ff);
    public static readonly Color TRAIL_COLOR_INNER = Hex(0x4f8cff);

    // 8) 데미지 숫자
    public const float NUMBER_LIFETIME = 0.85f;
    public const float NUMBER_FADE_TIME = 0.3f;
    public const float NUMBER_POP_SPEED_MIN = 300f;
    public const float NUMBER_POP_SPEED_MAX = 420f;
    public const float NUMBER_SPREAD_SPEED = 110f;
    public const float NUMBER_GRAVITY = 1100f;
    public const float NUMBER_POP_SCALE = 1.9f;
    public const float NUMBER_POP_TIME = 0.14f;
    public const float NUMBER_FONT_BASE = 22f;
    public const float NUMBER_FONT_PER_DAMAGE = 0.9f;
    public const float NUMBER_FONT_MAX = 60f;
    public static readonly Color NUMBER_COLOR_NORMAL = Hex(0xffffff);
    public static readonly Color NUMBER_COLOR_HEAVY = Hex(0xffd23f);
    public static readonly Color NUMBER_COLOR_PULL = Hex(0x7fd8ff);

    // 9) 적
    public const int ENEMY_COUNT = Balance.ENEMY_COUNT;   // 값의 원본은 balance.json (QA M6 조정)
    public const int ENEMY_MAX_HP = 80;
    public const float ENEMY_RADIUS = 0.6f;
    public const float ENEMY_HEIGHT = 1.8f;
    public const float ENEMY_SPEED = 2.8f;
    public const float ENEMY_SPEED_VARIANCE = 0.2f;
    public const float ENEMY_STOP_DISTANCE = 1.7f;
    public const float ENEMY_KNOCKBACK_FRICTION = 5.5f;
    public const float ENEMY_FLASH_TIME = Balance.ENEMY_FLASH_TIME;
    public const float ENEMY_SQUASH = 0.25f;
    public const float ENEMY_KILL_KNOCKBACK_MULT = 1.5f;
    public const float ENEMY_DEATH_HOLD = 0.25f;
    public const float ENEMY_DEATH_SHRINK = 0.3f;
    public const float ENEMY_RESPAWN_DELAY = 1.6f;
    public const float ENEMY_SPAWN_DISTANCE = 11f;
    public const float ENEMY_SPAWN_POP_TIME = 0.3f;
    public const float ENEMY_PICK_RADIUS = 1.0f;

    // 10) 클릭 표시
    public const float CLICK_MARKER_LIFETIME = 0.45f;
    public static readonly Color CLICK_MARKER_COLOR = Hex(0x7fe3ff);

    /// <summary>0xRRGGBB 숫자를 색으로 (Three.js/Godot판과 같은 색 코드를 그대로 쓰려고)</summary>
    public static Color Hex(int rgb) =>
        new Color(((rgb >> 16) & 0xff) / 255f, ((rgb >> 8) & 0xff) / 255f, (rgb & 0xff) / 255f, 1f);
}
