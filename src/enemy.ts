// ============================================================================
// enemy.ts — 적 (캡슐/박스 샌드백). AI는 일부러 "플레이어를 향해 걸어온다"가 전부.
// 이 단계의 목적은 "때리는 맛"이므로, 적은 맞아주는 역할만 잘 하면 된다.
// ============================================================================
import * as THREE from 'three';
import { ARENA, ENEMY, PULL } from './config';
import { clamp, easeOutQuad, rand } from './util';

export class Enemy {
  readonly group = new THREE.Group();
  readonly mesh: THREE.Mesh;
  private readonly material: THREE.MeshLambertMaterial;

  readonly radius = ENEMY.RADIUS;
  readonly height = ENEMY.HEIGHT;
  /** 넉백 속도. 맞으면 이 값이 크게 세팅되고 마찰로 서서히 줄어든다. */
  readonly vel = new THREE.Vector3();

  hp = ENEMY.MAX_HP;
  alive = true;
  /** 남은 기절 시간. 기절 중에는 플레이어를 쫓아오지 않는다. */
  stun = 0;
  /** 견인으로 끌려오는 중인가 */
  pulled = false;
  /** 죽은 뒤 부활해도 되는 상태가 되었나 (EnemyManager가 확인) */
  respawnReady = false;

  private readonly speed = ENEMY.SPEED * (1 + rand(-ENEMY.SPEED_VARIANCE, ENEMY.SPEED_VARIANCE));
  private flash = 0;       // 1 → 0 으로 줄어드는 '맞음' 번쩍임
  private deathT = 0;      // 죽은 뒤 경과 시간
  private spawnT = 0;      // 등장 후 경과 시간 (팝인 연출)
  private pulledT = 0;     // 끌려오는 중 경과 시간 (안전장치)

  constructor(scene: THREE.Scene, shape: 'capsule' | 'box', position: THREE.Vector3) {
    // 도형 두 종류를 섞어서 "다른 적"처럼 보이게 한다 (에셋 없이 구분하는 가장 싼 방법)
    const geo =
      shape === 'capsule'
        ? new THREE.CapsuleGeometry(this.radius * 0.85, this.height - this.radius * 1.7, 6, 14)
        : new THREE.BoxGeometry(this.radius * 1.9, this.height, this.radius * 1.9);
    this.material = new THREE.MeshLambertMaterial({
      color: shape === 'capsule' ? 0xd9534f : 0xc2692f,
      emissive: 0xffffff,
    });
    this.material.emissiveIntensity = 0; // 평소엔 안 빛나고, 맞으면 1로 올렸다 내린다
    this.mesh = new THREE.Mesh(geo, this.material);
    this.mesh.position.y = this.height / 2; // 발바닥이 바닥(y=0)에 오도록 위로 올림
    this.mesh.castShadow = true;
    this.mesh.userData.enemy = this; // 클릭 판정에서 "이 메쉬 = 어떤 적?" 을 찾기 위한 꼬리표
    this.group.add(this.mesh);
    this.group.position.copy(position);
    scene.add(this.group);
    this.spawnT = 0;
  }

  get pos(): THREE.Vector3 {
    return this.group.position;
  }

  /** 데미지 숫자가 튀어나올 위치 (머리 위) */
  getHeadPosition(out: THREE.Vector3): THREE.Vector3 {
    return out.set(this.pos.x, this.height + 0.3, this.pos.z);
  }

  /**
   * 한 대 맞았다.
   * @param dir       넉백 방향 (길이 1, 바닥 평면)
   * @param knockback 넉백 초기 속도
   * @returns 이번 타격으로 죽었으면 true
   */
  takeHit(damage: number, dir: THREE.Vector3, knockback: number, stun: number): boolean {
    this.hp -= damage;
    this.flash = 1;
    this.stun = Math.max(this.stun, stun);
    this.pulled = false; // 끌려오던 중에 맞으면 견인 취소
    // 속도를 '더하지' 않고 '덮어쓴다': 연타해도 무한히 빨라지지 않고, 마지막 타격 방향이 곧 날아가는 방향이 된다
    this.vel.copy(dir).multiplyScalar(knockback);

    if (this.hp <= 0) {
      this.alive = false;
      this.deathT = 0;
      this.respawnReady = false;
      this.vel.multiplyScalar(ENEMY.KILL_KNOCKBACK_MULT);
      return true;
    }
    return false;
  }

  /** 견인 시작: 이제부터 플레이어 쪽으로 빠르게 끌려온다 */
  startPulled(): void {
    this.pulled = true;
    this.pulledT = 0;
    this.vel.set(0, 0, 0);
  }

  /** 죽었다가 다시 등장 */
  respawn(position: THREE.Vector3): void {
    this.hp = ENEMY.MAX_HP;
    this.alive = true;
    this.respawnReady = false;
    this.stun = 0;
    this.pulled = false;
    this.flash = 0;
    this.spawnT = 0;
    this.vel.set(0, 0, 0);
    this.pos.copy(position);
    this.applyVisual();
  }

  update(dt: number, playerPos: THREE.Vector3): void {
    if (!this.alive) {
      this.updateDead(dt);
      return;
    }

    this.spawnT += dt;
    this.flash = Math.max(0, this.flash - dt / ENEMY.FLASH_TIME);

    if (this.pulled) {
      this.updatePulled(dt, playerPos);
    } else {
      // 넉백 이동: 속도만큼 움직이고, 마찰로 지수적으로 줄인다 (프레임레이트와 무관)
      this.pos.addScaledVector(this.vel, dt);
      this.vel.multiplyScalar(Math.exp(-ENEMY.KNOCKBACK_FRICTION * dt));

      this.stun -= dt;
      if (this.stun <= 0) this.chase(dt, playerPos);
    }

    this.clampToArena();
    this.applyVisual();
  }

  /** 가장 단순한 AI: 플레이어 방향으로 걷다가, 가까워지면 멈춘다 */
  private chase(dt: number, playerPos: THREE.Vector3): void {
    const dx = playerPos.x - this.pos.x;
    const dz = playerPos.z - this.pos.z;
    const dist = Math.hypot(dx, dz);
    if (dist > ENEMY.STOP_DISTANCE) {
      this.pos.x += (dx / dist) * this.speed * dt;
      this.pos.z += (dz / dist) * this.speed * dt;
    }
  }

  /** 견인: 플레이어 앞 STOP_DISTANCE 까지 빠르게 날아온다 */
  private updatePulled(dt: number, playerPos: THREE.Vector3): void {
    this.pulledT += dt;
    const dx = playerPos.x - this.pos.x;
    const dz = playerPos.z - this.pos.z;
    const dist = Math.hypot(dx, dz);
    const step = PULL.DRAG_SPEED * dt;
    if (dist - step <= PULL.STOP_DISTANCE || this.pulledT > 1) {
      // 도착! 멈추고 잠깐 멍해진다. (도착 연출은 Player 가 pulled 가 꺼진 것을 보고 처리)
      const keep = Math.max(PULL.STOP_DISTANCE, 0);
      if (dist > keep) {
        this.pos.x = playerPos.x - (dx / dist) * keep;
        this.pos.z = playerPos.z - (dz / dist) * keep;
      }
      this.pulled = false;
      this.stun = PULL.STUN;
      this.flash = 1;
      return;
    }
    this.pos.x += (dx / dist) * step;
    this.pos.z += (dz / dist) * step;
  }

  /** 죽은 뒤: 마지막 넉백으로 날아가다가 → 쪼그라들어 사라짐 → 일정 시간 뒤 부활 대기 */
  private updateDead(dt: number): void {
    this.deathT += dt;
    this.flash = Math.max(0, this.flash - dt / ENEMY.FLASH_TIME);
    this.pos.addScaledVector(this.vel, dt);
    this.vel.multiplyScalar(Math.exp(-ENEMY.KNOCKBACK_FRICTION * dt));
    this.clampToArena();
    this.applyVisual();
    if (this.deathT >= ENEMY.RESPAWN_DELAY) this.respawnReady = true;
  }

  private clampToArena(): void {
    const lim = ARENA.HALF_SIZE - this.radius;
    this.pos.x = clamp(this.pos.x, -lim, lim);
    this.pos.z = clamp(this.pos.z, -lim, lim);
  }

  /** 번쩍임/찌그러짐/등장·소멸 크기를 몸에 반영 */
  private applyVisual(): void {
    this.material.emissiveIntensity = this.flash * 0.9;

    // 등장 팝인(0→1) 또는 죽은 뒤 쪼그라듦(1→0)
    let base = easeOutQuad(clamp(this.spawnT / ENEMY.SPAWN_POP_TIME, 0, 1));
    if (!this.alive) {
      base = 1 - clamp((this.deathT - ENEMY.DEATH_HOLD) / ENEMY.DEATH_SHRINK, 0, 1);
    }
    // 맞은 순간: 옆으로 넓어지고 키가 줄어드는 찌그러짐 (타격의 무게감을 눈으로 보여줌)
    const sx = 1 + ENEMY.SQUASH * this.flash;
    const sy = 1 - ENEMY.SQUASH * 0.8 * this.flash;
    this.group.scale.set(base * sx, Math.max(0.001, base * sy), base * sx);
  }
}

/** 적 무리 관리: 생성, 서로 겹침 방지, 부활, 클릭 대상 찾기 */
export class EnemyManager {
  readonly list: Enemy[] = [];
  private readonly meshes: THREE.Object3D[] = [];

  constructor(private readonly scene: THREE.Scene, playerPos: THREE.Vector3) {
    for (let i = 0; i < ENEMY.COUNT; i++) {
      // 플레이어 둘레에 균등하게 배치
      const pos = this.spawnPoint(playerPos, (i / ENEMY.COUNT) * Math.PI * 2 + 0.4);
      const enemy = new Enemy(scene, i % 2 === 0 ? 'capsule' : 'box', pos);
      this.list.push(enemy);
      this.meshes.push(enemy.mesh);
    }
  }

  private spawnPoint(center: THREE.Vector3, angle: number): THREE.Vector3 {
    const lim = ARENA.HALF_SIZE - 1;
    return new THREE.Vector3(
      clamp(center.x + Math.cos(angle) * ENEMY.SPAWN_DISTANCE, -lim, lim),
      0,
      clamp(center.z + Math.sin(angle) * ENEMY.SPAWN_DISTANCE, -lim, lim),
    );
  }

  update(dt: number, playerPos: THREE.Vector3, playerRadius: number): void {
    for (const e of this.list) {
      e.update(dt, playerPos);
      // 부활: 죽은 지 충분히 지났으면 플레이어에게서 먼 곳에 새로 등장
      if (!e.alive && e.respawnReady) {
        e.respawn(this.spawnPoint(playerPos, Math.random() * Math.PI * 2));
      }
    }
    if (dt <= 0) return; // 히트스톱 중엔 밀어내기 계산도 멈춘다

    // 서로 겹치지 않게 밀어낸다 (살아있는 적끼리 + 플레이어 몸통)
    const alive = this.list.filter((e) => e.alive);
    for (let i = 0; i < alive.length; i++) {
      const a = alive[i];
      for (let j = i + 1; j < alive.length; j++) {
        const b = alive[j];
        if (a.pulled || b.pulled) continue; // 끌려오는 중엔 간섭 없음
        this.separate(a, b.pos, a.radius + b.radius, 0.5, b);
      }
      if (!a.pulled) this.separate(a, playerPos, a.radius + playerRadius, 1);
    }
  }

  /** a 를 other 로부터 minDist 이상 떨어지게 민다. (other가 Enemy면 서로 절반씩 민다) */
  private separate(a: Enemy, otherPos: THREE.Vector3, minDist: number, share: number, other?: Enemy): void {
    const dx = a.pos.x - otherPos.x;
    const dz = a.pos.z - otherPos.z;
    const d = Math.hypot(dx, dz);
    if (d >= minDist || d < 1e-5) return;
    const push = (minDist - d) * share;
    a.pos.x += (dx / d) * push;
    a.pos.z += (dz / d) * push;
    if (other) {
      other.pos.x -= (dx / d) * push;
      other.pos.z -= (dz / d) * push;
    }
  }

  /**
   * 마우스 아래의 적 찾기.
   * 1순위: 광선이 적 몸에 직접 닿음. 2순위: 바닥 클릭 지점 근처(반경 안)의 가장 가까운 적.
   * 2순위가 있는 이유: 움직이는 작은 도형을 정확히 누르는 건 어렵기 때문 (조작 관대함).
   */
  pick(raycaster: THREE.Raycaster, ground: THREE.Vector3 | null, nearRadius: number): Enemy | null {
    const hits = raycaster.intersectObjects(this.meshes, false);
    for (const h of hits) {
      const e = h.object.userData.enemy as Enemy;
      if (e.alive) return e;
    }
    if (!ground) return null;
    let best: Enemy | null = null;
    let bestD = nearRadius;
    for (const e of this.list) {
      if (!e.alive) continue;
      const d = Math.hypot(e.pos.x - ground.x, e.pos.z - ground.z);
      if (d <= bestD) {
        bestD = d;
        best = e;
      }
    }
    return best;
  }
}
