// ============================================================================
// player.ts — 플레이어(차사). 이동 / 철삭 3타 콤보 / 우클릭 견인.
//
// 구조: "상태 머신"(지금 뭘 하는 중인지 하나만 기억하는 방식)
//   free   : 가만히 있거나 이동 중
//   attack : 콤보 중  (windup 준비 → swing 휘두름 → recover 후딜)
//   pull   : 견인 중  (throw 던짐 → drag 끌어당김 → retract 되감기)
// 한 번에 한 가지 상태만 가지므로 "공격하면서 견인" 같은 꼬이는 상황이 생기지 않는다.
// ============================================================================
import * as THREE from 'three';
import {
  ARENA, ATTACK_START_RANGE, COMBO, COMBO_RESET_TIME, DAMAGE_VARIANCE, FEEL, HIT_PADDING, PLAYER, PULL, TRAIL,
  type ComboStep,
} from './config';
import { ChainVisual } from './chain';
import type { Enemy, EnemyManager } from './enemy';
import type { DamageNumbers, HitFeel } from './effects';
import { clamp, easeInQuad, easeOutQuad, lerp, rand, sweptThrough, turnToward } from './util';

type State = 'free' | 'attack' | 'pull';

/** 콤보 한 타를 진행 중일 때의 기록 */
interface AttackRun {
  step: number;                     // 1~3
  cfg: ComboStep;
  phase: 'windup' | 'swing' | 'recover';
  t: number;                        // 현재 phase 안에서 흐른 시간
  startAngle: number;               // 휘두르기 시작 각도
  totalSweep: number;               // 훑는 총 각도(부호 포함)
  prevAngle: number;                // 직전 프레임의 사슬 끝 각도 (훑은 구간 판정용)
  hit: Set<Enemy>;                  // 이번 타에 이미 맞은 적 (한 번 휘두를 때 한 번만 맞게)
  firstSample: boolean;             // 잔상의 첫 점인가
}

/** 견인 진행 기록 */
interface PullRun {
  phase: 'throw' | 'drag' | 'retract';
  t: number;
  target: Enemy | null;             // null = 허공에 던짐(빗나감)
  aim: THREE.Vector3;               // 빗나갈 때 사슬이 날아갈 끝 지점
  from: THREE.Vector3;              // 되감기 시작 위치
  dragT: number;
}

export class Player {
  readonly group = new THREE.Group();
  private readonly chain: ChainVisual;

  private facing = 0;               // 바라보는 방향 (바닥 평면 각도. 0 = +x 방향)
  private state: State = 'free';
  private moveTarget: THREE.Vector3 | null = null;
  private chaseTarget: Enemy | null = null;   // "저 적을 때리러 가는 중"

  private comboStep = 0;            // 마지막으로 시작한 콤보 단계 (0 = 없음)
  private comboTimer = 0;           // 콤보 이음 허용 남은 시간
  private atk: AttackRun | null = null;
  private buffered: Enemy | null | undefined = undefined; // 후딜 중 눌러둔 다음 클릭 (undefined = 없음)
  private pullRun: PullRun | null = null;
  private pullCooldown = 0;

  private chainLag = 0;             // 사슬이 뒤처지는 각도 (부호 포함)
  private readonly tmpA = new THREE.Vector3();
  private readonly tmpB = new THREE.Vector3();
  private readonly tmpHand = new THREE.Vector3();

  constructor(
    private readonly scene: THREE.Scene,
    private readonly enemies: EnemyManager,
    private readonly feel: HitFeel,
    private readonly numbers: DamageNumbers,
  ) {
    // 몸: 파란 캡슐 + 노란 박스(코). 코가 있어야 어느 쪽을 보는지 보인다.
    const body = new THREE.Mesh(
      new THREE.CapsuleGeometry(PLAYER.RADIUS * 0.9, 0.8, 6, 14),
      new THREE.MeshLambertMaterial({ color: 0x3b82f6 }),
    );
    body.position.y = 0.9;
    body.castShadow = true;
    const nose = new THREE.Mesh(
      new THREE.BoxGeometry(0.4, 0.25, 0.25),
      new THREE.MeshLambertMaterial({ color: 0xffe066 }),
    );
    nose.position.set(PLAYER.RADIUS * 0.9, 1.35, 0); // 로컬 +x 가 '앞'
    this.group.add(body, nose);
    scene.add(this.group);

    this.chain = new ChainVisual(scene);
  }

  get pos(): THREE.Vector3 {
    return this.group.position;
  }

  // =========================================================================
  // 명령 (입력 쪽에서 호출) — "무엇을 하라"만 받고, 실제 행동은 update 가 한다
  // =========================================================================

  /** 바닥 클릭: 그 지점으로 이동 */
  commandMove(point: THREE.Vector3): void {
    this.moveTarget = point.clone();
    this.moveTarget.x = clamp(this.moveTarget.x, -ARENA.HALF_SIZE, ARENA.HALF_SIZE);
    this.moveTarget.z = clamp(this.moveTarget.z, -ARENA.HALF_SIZE, ARENA.HALF_SIZE);
    this.chaseTarget = null;
    this.buffered = undefined; // 이동을 지시하면 눌러둔 다음 타는 취소
  }

  /** 적 클릭: 콤보 공격 */
  commandAttack(enemy: Enemy): void {
    if (this.state === 'attack') {
      // 콤보 중이면 "다음 타 예약" (후딜이 끝나는 순간 바로 이어진다)
      this.buffered = enemy;
    } else if (this.state === 'free') {
      this.chaseTarget = enemy;
      this.moveTarget = null;
    }
  }

  /** 우클릭: 견인. enemy가 null이면 aim 방향으로 허공에 던진다. */
  commandPull(enemy: Enemy | null, aim: THREE.Vector3): void {
    if (this.pullCooldown > 0) return;
    const canCancel = this.state === 'attack' && this.atk?.phase === 'recover'; // 후딜은 견인으로 끊을 수 있다
    if (this.state !== 'free' && !canCancel) return;
    this.startPull(enemy, aim);
  }

  // =========================================================================
  // 매 프레임 갱신
  // =========================================================================
  update(dt: number): void {
    this.pullCooldown = Math.max(0, this.pullCooldown - dt);
    switch (this.state) {
      case 'free': this.updateFree(dt); break;
      case 'attack': this.updateAttack(dt); break;
      case 'pull': this.updatePull(dt); break;
    }
    this.group.rotation.y = -this.facing; // 로컬 +x 가 facing 방향을 향하도록
    this.chain.trail.update(dt);
  }

  // ---- 이동 -----------------------------------------------------------------
  private updateFree(dt: number): void {
    this.comboTimer = Math.max(0, this.comboTimer - dt);
    if (dt <= 0) return;

    // 적을 때리러 가는 중
    if (this.chaseTarget) {
      const e = this.chaseTarget;
      if (!e.alive) {
        this.chaseTarget = null;
      } else {
        const dx = e.pos.x - this.pos.x;
        const dz = e.pos.z - this.pos.z;
        const dist = Math.hypot(dx, dz);
        this.facing = turnToward(this.facing, Math.atan2(dz, dx), PLAYER.TURN_SPEED * dt);
        if (dist - e.radius <= ATTACK_START_RANGE) {
          this.chaseTarget = null;
          this.startAttack(e, this.comboTimer > 0);
        } else {
          this.stepToward(e.pos, dt);
        }
        return;
      }
    }

    // 바닥 클릭 지점으로 이동
    if (this.moveTarget) {
      const dx = this.moveTarget.x - this.pos.x;
      const dz = this.moveTarget.z - this.pos.z;
      const dist = Math.hypot(dx, dz);
      if (dist <= PLAYER.ARRIVE_DISTANCE) {
        this.moveTarget = null;
      } else {
        this.facing = turnToward(this.facing, Math.atan2(dz, dx), PLAYER.TURN_SPEED * dt);
        this.stepToward(this.moveTarget, dt);
      }
    }
  }

  /** target 쪽으로 한 걸음. 목표를 지나치지 않게 거리 제한 */
  private stepToward(target: THREE.Vector3, dt: number): void {
    const dx = target.x - this.pos.x;
    const dz = target.z - this.pos.z;
    const dist = Math.hypot(dx, dz);
    if (dist < 1e-5) return;
    const step = Math.min(dist, PLAYER.MOVE_SPEED * dt);
    this.pos.x += (dx / dist) * step;
    this.pos.z += (dz / dist) * step;
    this.clampToArena();
  }

  private clampToArena(): void {
    const lim = ARENA.HALF_SIZE - PLAYER.RADIUS;
    this.pos.x = clamp(this.pos.x, -lim, lim);
    this.pos.z = clamp(this.pos.z, -lim, lim);
  }

  private handPosition(out: THREE.Vector3): THREE.Vector3 {
    return out.set(this.pos.x, PLAYER.HAND_HEIGHT, this.pos.z);
  }

  // =========================================================================
  // 철삭 3타 콤보
  // =========================================================================
  private startAttack(target: Enemy | null, continueCombo: boolean): void {
    // 콤보가 이어지는 중이면 다음 단계, 아니면 1타부터
    const step = continueCombo ? (this.comboStep % COMBO.length) + 1 : 1;
    this.comboStep = step;
    const cfg = COMBO[step - 1];

    // 대상 쪽으로 몸을 돌린다. 대상이 없으면 보던 방향 그대로.
    if (target && target.alive) {
      this.facing = Math.atan2(target.pos.z - this.pos.z, target.pos.x - this.pos.x);
    }

    const startAngle = this.facing - cfg.dir * THREE.MathUtils.degToRad(cfg.startOffsetDeg);
    this.state = 'attack';
    this.atk = {
      step, cfg,
      phase: 'windup', t: 0,
      startAngle,
      totalSweep: cfg.dir * THREE.MathUtils.degToRad(cfg.sweepDeg),
      prevAngle: startAngle,
      hit: new Set(),
      firstSample: true,
    };
    this.buffered = undefined;
    this.chain.show();
  }

  private updateAttack(dt: number): void {
    const a = this.atk!;
    const cfg = a.cfg;
    a.t += dt;
    const hand = this.handPosition(this.tmpHand);

    if (a.phase === 'windup') {
      // 준비: 사슬을 시작 위치로 끌어 모은다 (살짝 앞에서 → 뒤로 당기는 예비동작)
      const p = clamp(a.t / cfg.windup, 0, 1);
      const angle = a.startAngle + cfg.dir * 0.4 * (1 - easeOutQuad(p));
      this.chainLag *= Math.exp(-14 * dt);
      this.chain.set(hand, angle, lerp(0.3, 0.55, p) * cfg.reach, hand.y + 0.25 * p, this.chainLag, 0.25);
      a.prevAngle = a.startAngle;
      if (a.t >= cfg.windup) { a.phase = 'swing'; a.t = 0; }
      return;
    }

    if (a.phase === 'swing') {
      const p = clamp(a.t / cfg.swing, 0, 1);
      const angle = a.startAngle + a.totalSweep * easeOutQuad(p); // 확 휘두르고 끝에서 살짝 감속
      const radius = cfg.reach * (0.55 + 0.45 * easeOutQuad(Math.min(1, p / 0.3))); // 휘두르며 사슬이 쭉 펴진다
      const headY = hand.y + 0.25 - 0.3 * p;

      if (dt > 0) {
        // 사슬 휘어짐: 빠를수록 많이 뒤처진다
        const angVel = Math.abs(angle - a.prevAngle) / dt;
        const targetLag = cfg.dir * Math.min(angVel * 0.04, 1.1);
        this.chainLag = lerp(this.chainLag, targetLag, 0.5);

        this.sweepHits(a, a.prevAngle, angle);
        this.recordTrail(a, hand, a.prevAngle, angle, radius, headY);

        // 휘두르는 동안 앞으로 살짝 미끄러져 들어간다 (제자리에서 휘두르면 가벼워 보인다)
        if (cfg.lunge > 0) {
          const v = (cfg.lunge / cfg.swing) * dt;
          this.pos.x += Math.cos(this.facing) * v;
          this.pos.z += Math.sin(this.facing) * v;
          this.clampToArena();
        }
      }
      this.chain.set(this.handPosition(this.tmpHand), angle, radius, headY, this.chainLag, 0);
      a.prevAngle = angle;
      if (a.t >= cfg.swing) { a.phase = 'recover'; a.t = 0; }
      return;
    }

    // recover: 후딜. 사슬을 거둬들인다.
    const p = clamp(a.t / cfg.recover, 0, 1);
    const angle = a.startAngle + a.totalSweep + cfg.dir * 0.2 * easeOutQuad(p); // 관성으로 조금 더 따라감
    this.chainLag *= Math.exp(-10 * dt);
    this.chain.set(hand, angle, cfg.reach * (1 - 0.85 * easeInQuad(p)), hand.y - 0.05, this.chainLag, 0.4 * p);
    if (a.t >= cfg.recover) this.finishAttack();
  }

  /** 한 타 종료: 예약된 클릭이 있으면 바로 다음 타, 없으면 대기로 */
  private finishAttack(): void {
    const finishedStep = this.atk!.step;
    this.atk = null;

    if (this.buffered !== undefined) {
      const next = this.buffered;
      this.buffered = undefined;
      // 3타까지 끝났으면 콤보 리셋(다음은 1타)
      if (finishedStep >= COMBO.length) this.comboStep = 0;
      this.startAttack(next, true);
      return;
    }

    this.state = 'free';
    this.chain.hide();
    if (finishedStep >= COMBO.length) {
      this.comboStep = 0;
      this.comboTimer = 0;
    } else {
      this.comboTimer = COMBO_RESET_TIME;
    }
  }

  /**
   * 이번 프레임에 사슬 끝이 prev→cur 각도로 훑은 구간에 걸린 적을 모두 때린다.
   * "범위 공격"의 핵심: 사슬이 지나가는 부채꼴(또는 원) 안의 적은 전부, 지나가는 순서대로 맞는다.
   */
  private sweepHits(a: AttackRun, prev: number, cur: number): void {
    const reach = a.cfg.reach;
    for (const e of this.enemies.list) {
      if (!e.alive || a.hit.has(e)) continue;
      const dx = e.pos.x - this.pos.x;
      const dz = e.pos.z - this.pos.z;
      const dist = Math.hypot(dx, dz);
      if (dist - e.radius > reach + HIT_PADDING) continue; // 사슬이 안 닿는 거리
      // 적 몸통이 각도로 얼마나 넓은지 (가까울수록 넓게 보임)
      const halfWidth = Math.asin(clamp((e.radius + HIT_PADDING) / Math.max(dist, 0.01), 0, 1));
      if (!sweptThrough(prev, cur, Math.atan2(dz, dx), halfWidth)) continue;
      a.hit.add(e);
      this.hitEnemy(e, a, dx / (dist || 1), dz / (dist || 1));
    }
  }

  /** 적 한 마리에게 타격 적용: 데미지 + 넉백 + 히트스톱 + 화면 흔들림 + 숫자 */
  private hitEnemy(e: Enemy, a: AttackRun, rx: number, rz: number): void {
    const cfg = a.cfg;
    // 넉백 방향 = 바깥쪽(플레이어로부터 멀어지는 방향) + 휘두른 방향(접선)을 조금 섞는다
    //   → 사슬에 쓸려 날아가는 느낌.
    //   접선 = 바깥 방향 (rx, rz) 를 90° 돌린 (-rz, rx). cfg.dir 부호로 사슬이 도는 쪽을 따른다.
    const mix = FEEL.KNOCKBACK_TANGENT_MIX * cfg.dir;
    const dir = this.tmpA.set(rx - rz * mix, 0, rz + rx * mix).normalize();

    const damage = Math.max(1, Math.round(cfg.damage * (1 + rand(-DAMAGE_VARIANCE, DAMAGE_VARIANCE))));
    const killed = e.takeHit(damage, dir, cfg.knockback, cfg.stun);

    this.feel.hitStop(cfg.hitStopFrames + (killed ? FEEL.KILL_BONUS_FRAMES : 0));
    this.feel.addShake(cfg.shake + (killed ? FEEL.KILL_BONUS_SHAKE : 0));
    this.numbers.spawn(e.getHeadPosition(this.tmpB), damage, a.step === COMBO.length ? 'heavy' : 'normal');
  }

  /** 잔상 점 기록: 지난 프레임 → 이번 프레임 사이를 잘게 쪼개 곡선이 매끈하게 */
  private recordTrail(a: AttackRun, hand: THREE.Vector3, prev: number, cur: number, radius: number, y: number): void {
    const inner = new THREE.Vector3();
    const outer = new THREE.Vector3();
    for (let i = 1; i <= TRAIL.SUBSTEPS; i++) {
      const ang = lerp(prev, cur, i / TRAIL.SUBSTEPS);
      const c = Math.cos(ang);
      const s = Math.sin(ang);
      outer.set(hand.x + c * radius, y, hand.z + s * radius);
      inner.set(hand.x + c * radius * TRAIL.INNER_RATIO, y, hand.z + s * radius * TRAIL.INNER_RATIO);
      this.chain.trail.add(inner, outer, a.firstSample);
      a.firstSample = false;
    }
  }

  // =========================================================================
  // 우클릭 견인
  // =========================================================================
  private startPull(enemy: Enemy | null, aim: THREE.Vector3): void {
    // 콤보 후딜을 끊고 들어온 경우 정리
    this.atk = null;
    this.buffered = undefined;
    this.moveTarget = null;
    this.chaseTarget = null;
    this.comboTimer = 0;
    this.comboStep = 0;

    // 사거리 밖이면 대상 없이 허공에 던진다 (빗나감)
    let target = enemy && enemy.alive ? enemy : null;
    const dx = (target ? target.pos.x : aim.x) - this.pos.x;
    const dz = (target ? target.pos.z : aim.z) - this.pos.z;
    const dist = Math.hypot(dx, dz);
    if (target && dist > PULL.RANGE) target = null;

    this.facing = Math.atan2(dz, dx);
    const reach = Math.min(dist, PULL.RANGE);
    const hand = this.handPosition(this.tmpHand);
    this.state = 'pull';
    this.pullRun = {
      phase: 'throw', t: 0, target, dragT: 0,
      aim: new THREE.Vector3(hand.x + Math.cos(this.facing) * reach, PLAYER.HAND_HEIGHT, hand.z + Math.sin(this.facing) * reach),
      from: new THREE.Vector3(),
    };
    this.chain.show();
  }

  private updatePull(dt: number): void {
    const r = this.pullRun!;
    const hand = this.handPosition(this.tmpHand);
    r.t += dt;

    if (r.phase === 'throw') {
      // 사슬이 목표를 향해 쭉 날아간다. 대상이 움직여도 따라가도록 매 프레임 목표 위치를 다시 읽는다.
      const goal = r.target ? this.tmpA.set(r.target.pos.x, PLAYER.HAND_HEIGHT, r.target.pos.z) : r.aim;
      const p = easeOutQuad(clamp(r.t / PULL.THROW_TIME, 0, 1));
      this.setStraightChain(hand, lerp3(hand, goal, p, this.tmpB), 0.2 * (1 - p));
      if (r.t >= PULL.THROW_TIME) {
        if (r.target) {
          this.hitPull(r.target);
          r.phase = 'drag';
        } else {
          r.from.copy(goal);
          r.phase = 'retract';
        }
        r.t = 0;
      }
      return;
    }

    if (r.phase === 'drag') {
      // 적이 끌려오는 동안 사슬은 팽팽하게 적을 향해 붙어 있다
      const e = r.target!;
      const head = this.tmpB.set(e.pos.x, PLAYER.HAND_HEIGHT, e.pos.z);
      this.setStraightChain(hand, head, 0);
      this.facing = Math.atan2(e.pos.z - this.pos.z, e.pos.x - this.pos.x);
      if (!e.pulled) {
        // 도착: 한 번 더 쿵 하는 느낌을 준다
        if (dt > 0 && e.alive) {
          this.feel.hitStop(2);
          this.feel.addShake(PULL.ARRIVE_SHAKE);
        }
        r.from.copy(head);
        r.phase = 'retract';
        r.t = 0;
      }
      return;
    }

    // retract: 사슬을 손으로 되감는다
    const p = easeInQuad(clamp(r.t / PULL.RETRACT_TIME, 0, 1));
    this.setStraightChain(hand, lerp3(r.from, hand, p, this.tmpB), 0.1);
    if (r.t >= PULL.RETRACT_TIME) {
      this.state = 'free';
      this.pullRun = null;
      this.pullCooldown = PULL.COOLDOWN;
      this.chain.hide();
    }
  }

  /** 견인이 적중한 순간 */
  private hitPull(e: Enemy): void {
    // 넉백은 0 (끌려오는 게 핵심이므로 밀어내지 않음). 방향은 플레이어 쪽.
    const dir = this.tmpA.set(this.pos.x - e.pos.x, 0, this.pos.z - e.pos.z).normalize();
    const damage = Math.max(1, Math.round(PULL.DAMAGE * (1 + rand(-DAMAGE_VARIANCE, DAMAGE_VARIANCE))));
    const killed = e.takeHit(damage, dir, 0, PULL.STUN);
    this.feel.hitStop(PULL.HITSTOP_FRAMES + (killed ? FEEL.KILL_BONUS_FRAMES : 0));
    this.feel.addShake(PULL.SHAKE);
    this.numbers.spawn(e.getHeadPosition(this.tmpB), damage, 'pull');
    if (!killed) e.startPulled(); // 안 죽었으면 끌어당기기 시작
  }

  /** 손(hand)에서 head 까지 일직선(약간 처짐)으로 사슬을 그린다 */
  private setStraightChain(hand: THREE.Vector3, head: THREE.Vector3, sag: number): void {
    const dx = head.x - hand.x;
    const dz = head.z - hand.z;
    this.chain.set(hand, Math.atan2(dz, dx), Math.hypot(dx, dz), head.y, 0, sag);
  }
}

/** a→b 를 t 만큼 보간해 out 에 담는다 */
function lerp3(a: THREE.Vector3, b: THREE.Vector3, t: number, out: THREE.Vector3): THREE.Vector3 {
  return out.set(lerp(a.x, b.x, t), lerp(a.y, b.y, t), lerp(a.z, b.z, t));
}
