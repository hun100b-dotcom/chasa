// ============================================================================
// stage.ts — 무대 설치: 렌더러, 카메라, 조명, 바닥
// ============================================================================
import * as THREE from 'three';
import { ARENA, CAMERA } from './config';

export class Stage {
  readonly scene = new THREE.Scene();
  readonly renderer: THREE.WebGLRenderer;
  /** 직교(Orthographic) 카메라: 멀리 있어도 작아지지 않는다 = 원근감 없는 쿼터뷰 */
  readonly camera: THREE.OrthographicCamera;
  private readonly sun: THREE.DirectionalLight;
  /** 카메라가 바라보는 점 (플레이어를 부드럽게 따라간다) */
  private readonly focus = new THREE.Vector3();
  /** 카메라가 focus 에서 떨어진 방향/거리 (고정 각도) */
  private readonly offset = new THREE.Vector3();

  constructor(container: HTMLElement) {
    this.scene.background = new THREE.Color(0x14161c);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true; // 그림자가 있어야 캐릭터가 바닥에서 안 떠 보인다
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    container.appendChild(this.renderer.domElement);

    // --- 카메라: 각도(pitch/yaw)로 방향을 계산한다 ---
    const pitch = THREE.MathUtils.degToRad(CAMERA.PITCH_DEG);
    const yaw = THREE.MathUtils.degToRad(CAMERA.YAW_DEG);
    const dist = 60; // 직교 카메라는 거리가 화면 크기에 영향을 안 주므로, 뭐든 멀리만 두면 된다
    this.offset.set(
      Math.cos(yaw) * Math.cos(pitch) * dist,
      Math.sin(pitch) * dist,
      Math.sin(yaw) * Math.cos(pitch) * dist,
    );
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 300);

    // --- 조명: 은은한 전체 조명 + 그림자를 만드는 햇빛 ---
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.75));
    this.sun = new THREE.DirectionalLight(0xffffff, 1.6);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    const s = 22; // 그림자가 그려지는 범위(플레이어 주변)
    Object.assign(this.sun.shadow.camera, { left: -s, right: s, top: s, bottom: -s, near: 1, far: 120 });
    this.scene.add(this.sun, this.sun.target);

    this.buildFloor();
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  /** 바닥 + 격자 + 테두리. 격자는 '내가 움직이고 있다'는 걸 눈으로 느끼게 해준다. */
  private buildFloor(): void {
    const size = ARENA.HALF_SIZE * 2;
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(size, size),
      new THREE.MeshLambertMaterial({ color: 0x2b303b }),
    );
    floor.rotation.x = -Math.PI / 2; // 세워진 판을 눕힌다
    floor.receiveShadow = true;
    this.scene.add(floor);

    const grid = new THREE.GridHelper(size, size / 2, 0x4a5262, 0x383e4b);
    grid.position.y = 0.01; // 바닥과 겹쳐 깜빡이는 현상 방지
    this.scene.add(grid);

    // 맵 끝을 알려주는 붉은 테두리
    const h = ARENA.HALF_SIZE;
    const border = new THREE.LineLoop(
      new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-h, 0.02, -h), new THREE.Vector3(h, 0.02, -h),
        new THREE.Vector3(h, 0.02, h), new THREE.Vector3(-h, 0.02, h),
      ]),
      new THREE.LineBasicMaterial({ color: 0x9b3b3b }),
    );
    this.scene.add(border);
  }

  /** 창 크기가 바뀌면 카메라 비율을 다시 맞춘다 (안 하면 화면이 찌그러진다) */
  private resize(): void {
    const w = window.innerWidth;
    const h = window.innerHeight;
    this.renderer.setSize(w, h);
    const viewH = CAMERA.VIEW_HEIGHT;
    const viewW = viewH * (w / h);
    this.camera.left = -viewW / 2;
    this.camera.right = viewW / 2;
    this.camera.top = viewH / 2;
    this.camera.bottom = -viewH / 2;
    this.camera.updateProjectionMatrix();
  }

  /**
   * 한 프레임 그리기.
   * @param target 카메라가 따라갈 대상 위치
   * @param shake  화면 흔들림 (화면 기준 x=좌우, y=상하, 월드 거리 단위)
   * @param dt     진짜 경과 시간
   */
  render(target: THREE.Vector3, shake: THREE.Vector2, dt: number): void {
    // 1) 따라가기: 지수 보간 → 프레임레이트와 상관없이 같은 부드러움
    const k = 1 - Math.exp(-CAMERA.FOLLOW_SMOOTHNESS * dt);
    this.focus.lerp(target, k);

    // 2) 카메라 배치 (각도는 항상 고정)
    this.camera.position.copy(this.focus).add(this.offset);
    this.camera.lookAt(this.focus);
    this.camera.updateMatrixWorld();

    // 3) 흔들림: 카메라의 '오른쪽/위쪽' 방향으로 위치를 밀어준다 → 화면이 평행하게 떨린다
    const right = new THREE.Vector3().setFromMatrixColumn(this.camera.matrixWorld, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(this.camera.matrixWorld, 1);
    this.camera.position.addScaledVector(right, shake.x).addScaledVector(up, shake.y);
    this.camera.updateMatrixWorld();

    // 4) 햇빛(그림자 범위)도 플레이어 주변을 따라다니게
    this.sun.position.copy(this.focus).add(new THREE.Vector3(14, 30, 8));
    this.sun.target.position.copy(this.focus);

    this.renderer.render(this.scene, this.camera);
  }
}
