// ============================================================================
// input.ts — 마우스 입력
//   좌클릭 : 바닥 → 이동 / 적 → 철삭 3타 콤보
//   우클릭 : 견인 (적을 끌어당김)
// 이 파일은 "마우스가 3D 세계의 어디를 눌렀나"만 알아내서 Player 에게 명령을 전달한다.
// ============================================================================
import * as THREE from 'three';
import { ENEMY, PULL } from './config';
import type { EnemyManager } from './enemy';
import type { Player } from './player';
import type { ClickMarker } from './effects';

export class Input {
  private readonly raycaster = new THREE.Raycaster();
  private readonly ndc = new THREE.Vector2();
  /** 눈에 안 보이는 y=0 바닥 평면. 마우스 광선과 만나는 점이 '바닥 클릭 지점' */
  private readonly groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  private readonly groundPoint = new THREE.Vector3();
  private holdingMove = false; // 좌클릭을 누른 채 바닥을 끌고 다니는 중인가

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly camera: THREE.Camera,
    private readonly enemies: EnemyManager,
    private readonly player: Player,
    private readonly marker: ClickMarker,
  ) {
    // 우클릭 시 브라우저 메뉴가 뜨면 게임이 안 되므로 막는다
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    canvas.addEventListener('pointerdown', (e) => this.onDown(e));
    window.addEventListener('pointerup', (e) => {
      if (e.button === 0) this.holdingMove = false;
    });
    canvas.addEventListener('pointermove', (e) => this.onMove(e));
  }

  /** 마우스 위치로 광선을 쏘고, 바닥과 만나는 점을 구한다. 못 구하면 null */
  private aim(e: PointerEvent): THREE.Vector3 | null {
    const rect = this.canvas.getBoundingClientRect();
    // 화면 픽셀 좌표 → -1~1 좌표(카메라가 이해하는 형식)
    this.ndc.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    this.raycaster.setFromCamera(this.ndc, this.camera);
    const hit = this.raycaster.ray.intersectPlane(this.groundPlane, this.groundPoint);
    return hit ? this.groundPoint : null;
  }

  private onDown(e: PointerEvent): void {
    const ground = this.aim(e);

    if (e.button === 0) {
      // 좌클릭: 적 위인가? → 공격.  아니면 → 이동
      const enemy = this.enemies.pick(this.raycaster, ground, ENEMY.PICK_RADIUS);
      if (enemy) {
        this.player.commandAttack(enemy);
      } else if (ground) {
        this.player.commandMove(ground);
        this.marker.show(ground);
        this.holdingMove = true;
      }
    } else if (e.button === 2) {
      // 우클릭: 커서 근처 적을 견인. 근처에 적이 없으면 그 방향으로 허공에 던진다.
      const enemy = this.enemies.pick(this.raycaster, ground, PULL.PICK_RADIUS);
      this.player.commandPull(enemy, ground ?? this.player.pos);
    }
  }

  private onMove(e: PointerEvent): void {
    // 좌클릭을 누른 채 마우스를 움직이면 이동 목표가 계속 갱신된다 (마우스 따라 걷기)
    if (!this.holdingMove) return;
    const ground = this.aim(e);
    if (ground) this.player.commandMove(ground);
  }
}
