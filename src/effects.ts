// ============================================================================
// effects.ts — 타격감 연출 도구들
//   1) HitFeel      : 히트스톱(순간 정지) + 화면 흔들림
//   2) DamageNumbers: 튀어오르는 데미지 숫자
//   3) ClickMarker  : 이동 클릭 지점 표시 링
// (사슬 궤적 잔상은 chain.ts, 넉백은 enemy.ts 에 있다)
// ============================================================================
import * as THREE from 'three';
import { CLICK_MARKER, FEEL, NUMBER } from './config';
import { clamp, rand } from './util';

// ---------------------------------------------------------------------------
// 1) 히트스톱 + 화면 흔들림
// ---------------------------------------------------------------------------
export class HitFeel {
  /** 남은 정지 시간(초). 0보다 크면 게임 세계가 멈춘다. */
  private hitStopTimer = 0;
  /** 현재 흔들림 세기 (0~1). 시간이 지나면 저절로 줄어든다. */
  private shake = 0;

  /**
   * 히트스톱 요청.
   * 왜 "더 큰 값만" 받나? 한 번 휘두르면 적 여러 마리가 동시에 맞는다.
   * 그때마다 정지 시간이 합쳐지면 한참 멈춰버리므로, 가장 긴 것 하나만 적용한다.
   */
  hitStop(frames: number): void {
    this.hitStopTimer = Math.max(this.hitStopTimer, frames * FEEL.FRAME_TIME);
  }

  /** 화면 흔들림 요청 (0~1). 마찬가지로 가장 센 것만 적용한다. */
  addShake(strength: number): void {
    this.shake = clamp(Math.max(this.shake, strength), 0, 1);
  }

  /**
   * 매 프레임 호출. 반환값이 true면 "지금 정지 중"이라는 뜻.
   * 정지 중에도 화면 흔들림은 계속 줄어든다(=멈춘 화면이 부르르 떨리는 것이 손맛의 핵심).
   * realDt: 게임이 멈춰도 흐르는 '진짜 시간'
   */
  tick(realDt: number): boolean {
    this.shake = Math.max(0, this.shake - FEEL.SHAKE_DECAY * realDt);
    // 1e-4 는 부동소수점 오차 방어용: 2프레임짜리가 3프레임으로 늘어나는 것을 막는다
    if (this.hitStopTimer > 1e-4) {
      this.hitStopTimer -= realDt;
      return true;
    }
    this.hitStopTimer = 0;
    return false;
  }

  /** 이번 프레임에 카메라를 얼마나 흔들지 (화면 기준 좌우 x, 상하 y). 세기에 비례. */
  getShakeOffset(out: THREE.Vector2): THREE.Vector2 {
    if (this.shake <= 0) return out.set(0, 0);
    const amp = FEEL.SHAKE_MAX_OFFSET * this.shake;
    // 매 프레임 무작위 방향으로 튀게 해서 '지잉~' 하는 진동을 만든다
    const angle = Math.random() * Math.PI * 2;
    return out.set(Math.cos(angle) * amp, Math.sin(angle) * amp);
  }
}

// ---------------------------------------------------------------------------
// 2) 데미지 숫자
//    3D 글자(텍스처 필요) 대신 HTML 글자를 화면 위에 띄운다. 에셋이 필요 없고 선명하다.
// ---------------------------------------------------------------------------
export type NumberKind = 'normal' | 'heavy' | 'pull';

interface FloatingNumber {
  el: HTMLDivElement;
  x: number; y: number;   // 화면 좌표(픽셀)
  vx: number; vy: number; // 화면 속도(픽셀/초)
  age: number;
}

export class DamageNumbers {
  private readonly items: FloatingNumber[] = [];
  private readonly tmp = new THREE.Vector3();

  constructor(
    private readonly layer: HTMLElement,
    private readonly camera: THREE.Camera,
  ) {}

  /** 월드 좌표 worldPos 에서 숫자를 튀어나오게 한다. */
  spawn(worldPos: THREE.Vector3, value: number, kind: NumberKind): void {
    // 3D 위치 → 화면 픽셀 위치로 변환 (project 는 -1~1 범위로 바꿔준다)
    this.tmp.copy(worldPos).project(this.camera);
    const x = (this.tmp.x * 0.5 + 0.5) * this.layer.clientWidth;
    const y = (-this.tmp.y * 0.5 + 0.5) * this.layer.clientHeight;

    const el = document.createElement('div');
    el.className = 'dmg';
    el.textContent = String(value);
    el.style.fontSize = `${Math.min(NUMBER.FONT_MAX, NUMBER.FONT_BASE + value * NUMBER.FONT_PER_DAMAGE)}px`;
    el.style.color =
      kind === 'heavy' ? NUMBER.COLOR_HEAVY : kind === 'pull' ? NUMBER.COLOR_PULL : NUMBER.COLOR_NORMAL;
    this.layer.appendChild(el);

    this.items.push({
      el, x, y,
      vx: rand(-NUMBER.SPREAD_SPEED, NUMBER.SPREAD_SPEED),
      vy: -rand(NUMBER.POP_SPEED_MIN, NUMBER.POP_SPEED_MAX), // 화면은 아래가 +라서 위로는 마이너스
      age: 0,
    });
  }

  /** 숫자들을 움직인다. dt 는 '진짜 시간' (히트스톱 중에도 숫자는 자연스럽게 흐른다) */
  update(dt: number): void {
    for (let i = this.items.length - 1; i >= 0; i--) {
      const n = this.items[i];
      n.age += dt;
      if (n.age >= NUMBER.LIFETIME) {
        n.el.remove();
        this.items.splice(i, 1);
        continue;
      }
      n.vy += NUMBER.GRAVITY * dt; // 중력: 위로 솟았다가 떨어진다
      n.x += n.vx * dt;
      n.y += n.vy * dt;

      // 팝 연출: 처음에 크게 나타났다가 정상 크기로 쪼그라든다
      const pop = Math.max(0, 1 - n.age / NUMBER.POP_TIME);
      const scale = 1 + (NUMBER.POP_SCALE - 1) * pop;
      // 끝부분에서 서서히 투명
      const remain = NUMBER.LIFETIME - n.age;
      const opacity = remain < NUMBER.FADE_TIME ? remain / NUMBER.FADE_TIME : 1;

      n.el.style.transform = `translate(${n.x}px, ${n.y}px) translate(-50%, -50%) scale(${scale})`;
      n.el.style.opacity = String(opacity);
    }
  }
}

// ---------------------------------------------------------------------------
// 3) 클릭 표시 링 — "여기로 가는구나" 를 알려주는 작은 피드백
// ---------------------------------------------------------------------------
export class ClickMarker {
  private readonly mesh: THREE.Mesh;
  private readonly material: THREE.MeshBasicMaterial;
  private age = Infinity; // 처음엔 안 보이는 상태

  constructor(scene: THREE.Scene) {
    const geo = new THREE.RingGeometry(0.3, 0.42, 28);
    geo.rotateX(-Math.PI / 2); // 링을 바닥에 눕힌다
    this.material = new THREE.MeshBasicMaterial({ color: CLICK_MARKER.COLOR, transparent: true, depthWrite: false });
    this.mesh = new THREE.Mesh(geo, this.material);
    this.mesh.visible = false;
    scene.add(this.mesh);
  }

  show(point: THREE.Vector3): void {
    this.mesh.position.set(point.x, 0.04, point.z);
    this.age = 0;
    this.mesh.visible = true;
  }

  update(dt: number): void {
    if (!this.mesh.visible) return;
    this.age += dt;
    const t = this.age / CLICK_MARKER.LIFETIME;
    if (t >= 1) {
      this.mesh.visible = false;
      return;
    }
    this.mesh.scale.setScalar(1.6 - 0.9 * t); // 바깥에서 안쪽으로 모이는 링
    this.material.opacity = 1 - t;
  }
}
