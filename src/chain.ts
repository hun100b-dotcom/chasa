// ============================================================================
// chain.ts — 철삭(쇠사슬)의 "모습"
//   ChainVisual : 작은 박스 마디들을 이어붙인 사슬 + 끝의 쇳덩이(추)
//   SwingTrail  : 휘두른 자리에 남는 빛나는 띠 (궤적 잔상)
// 판정(누가 맞나)은 player.ts 에서 하고, 여기는 순수하게 그림만 담당한다.
// ============================================================================
import * as THREE from 'three';
import { CHAIN, TRAIL } from './config';

export class ChainVisual {
  readonly group = new THREE.Group();
  readonly trail: SwingTrail;
  private readonly links: THREE.Mesh[] = [];
  private readonly head: THREE.Mesh;
  private readonly points: THREE.Vector3[] = [];
  private spin = 0;

  constructor(scene: THREE.Scene) {
    // 마디 하나: 납작한 박스. 하나씩 90도 돌려 끼우면 사슬 고리처럼 보인다.
    const linkGeo = new THREE.BoxGeometry(0.2, 0.07, 1); // 길이(z)는 1로 두고 나중에 마디 간격에 맞춰 늘린다
    const linkMat = new THREE.MeshBasicMaterial({ color: CHAIN.LINK_COLOR });
    for (let i = 0; i < CHAIN.SEGMENTS; i++) {
      const m = new THREE.Mesh(linkGeo, linkMat);
      this.links.push(m);
      this.group.add(m);
    }
    for (let i = 0; i <= CHAIN.SEGMENTS; i++) this.points.push(new THREE.Vector3());

    // 끝의 추: 주황색 큐브
    this.head = new THREE.Mesh(
      new THREE.BoxGeometry(0.42, 0.42, 0.42),
      new THREE.MeshBasicMaterial({ color: CHAIN.HEAD_COLOR }),
    );
    this.group.add(this.head);

    this.group.visible = false;
    scene.add(this.group);
    this.trail = new SwingTrail(scene);
  }

  show(): void { this.group.visible = true; }
  hide(): void { this.group.visible = false; }

  /**
   * 사슬 모양을 정한다.
   * 손(hand)을 중심으로 한 극좌표 (각도, 거리)로 사슬 끝 위치를 받는다.
   *
   * @param angle   사슬 끝의 방향 (바닥 평면 각도)
   * @param radius  손에서 사슬 끝까지의 거리
   * @param headY   사슬 끝의 높이
   * @param lag     휘두를 때 사슬 몸통이 끝보다 "뒤처지는" 각도 (부호 = 휘두르는 방향).
   *                채찍처럼 휘어 보이게 해서 속도감을 준다.
   * @param sag     사슬이 중력으로 처지는 정도
   */
  set(hand: THREE.Vector3, angle: number, radius: number, headY: number, lag: number, sag: number): void {
    const n = CHAIN.SEGMENTS;
    for (let i = 0; i <= n; i++) {
      const t = i / n; // 0 = 손, 1 = 끝
      // 손에 가까운 부분일수록 많이 뒤처진다 → 끝만 앞서가는 채찍 모양
      const a = angle - lag * Math.pow(1 - t, 1.5);
      const r = radius * t;
      this.points[i].set(
        hand.x + Math.cos(a) * r,
        hand.y + (headY - hand.y) * t - sag * Math.sin(Math.PI * t),
        hand.z + Math.sin(a) * r,
      );
    }
    // 점과 점 사이에 박스 마디를 배치
    for (let i = 0; i < n; i++) {
      const p = this.points[i];
      const q = this.points[i + 1];
      const link = this.links[i];
      link.position.copy(p).add(q).multiplyScalar(0.5);
      link.lookAt(q); // 박스의 긴 쪽(z)이 q를 향하게
      link.rotateZ(i % 2 === 0 ? 0 : Math.PI / 2); // 번갈아 눕혀서 고리 느낌
      link.scale.z = Math.max(0.01, p.distanceTo(q) * 0.92);
    }
    this.head.position.copy(this.points[n]);
    this.spin += 0.35;
    this.head.rotation.set(this.spin, this.spin * 0.7, 0);
  }

  /** 사슬 끝 위치 (잔상, 판정 등에서 참고용) */
  getHeadPosition(out: THREE.Vector3): THREE.Vector3 {
    return out.copy(this.points[CHAIN.SEGMENTS]);
  }
}

// ---------------------------------------------------------------------------
// 궤적 잔상
//
// 원리: 사슬이 움직이는 동안 매 순간 "사슬 안쪽 점"과 "사슬 끝 점"을 기록한다.
//       기록된 점들을 이어서 띠(리본)를 만들고, 오래된 부분일수록 투명하게 한다.
//       → 휘두른 자리에 빛나는 호가 남았다가 스르륵 사라진다.
// ---------------------------------------------------------------------------
interface TrailSample {
  inner: THREE.Vector3;
  outer: THREE.Vector3;
  age: number;
  /** 새 휘두르기의 첫 점인가. 그렇다면 직전 휘두르기와 이어붙이지 않는다. */
  start: boolean;
}

export class SwingTrail {
  private readonly samples: TrailSample[] = [];
  private readonly geometry = new THREE.BufferGeometry();
  private readonly positions: Float32Array;
  private readonly colors: Float32Array;
  private readonly mesh: THREE.Mesh;
  private readonly cOuter = new THREE.Color(TRAIL.COLOR_OUTER);
  private readonly cInner = new THREE.Color(TRAIL.COLOR_INNER);

  constructor(scene: THREE.Scene) {
    // 점 한 쌍(안쪽/바깥쪽) 사이 사각형 = 삼각형 2개 = 정점 6개. 미리 최대치만큼 메모리를 잡아둔다.
    const maxVerts = TRAIL.MAX_SAMPLES * 6;
    this.positions = new Float32Array(maxVerts * 3);
    this.colors = new Float32Array(maxVerts * 4); // r, g, b, 알파
    this.geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));
    this.geometry.setAttribute('color', new THREE.BufferAttribute(this.colors, 4));
    this.geometry.setDrawRange(0, 0);

    const mat = new THREE.MeshBasicMaterial({
      vertexColors: true,       // 정점마다 색/투명도를 따로 쓴다
      transparent: true,
      blending: THREE.AdditiveBlending, // 빛처럼 겹칠수록 밝아짐
      depthWrite: false,        // 투명한 것이 다른 물체를 가리지 않게
      side: THREE.DoubleSide,   // 위/아래 어느 쪽에서 봐도 보이게
    });
    this.mesh = new THREE.Mesh(this.geometry, mat);
    this.mesh.frustumCulled = false; // 모양이 계속 바뀌므로 '화면 밖 판정'을 끈다
    scene.add(this.mesh);
  }

  /** 점 한 쌍 기록 */
  add(inner: THREE.Vector3, outer: THREE.Vector3, start: boolean): void {
    this.samples.push({ inner: inner.clone(), outer: outer.clone(), age: 0, start });
    if (this.samples.length > TRAIL.MAX_SAMPLES) this.samples.shift();
  }

  /** 나이를 먹이고(오래된 건 제거) 띠 모양을 다시 만든다 */
  update(dt: number): void {
    for (const s of this.samples) s.age += dt;
    while (this.samples.length > 0 && this.samples[0].age >= TRAIL.LIFETIME) this.samples.shift();

    let v = 0; // 쓴 정점 수
    const p = this.positions;
    const c = this.colors;
    const put = (pt: THREE.Vector3, col: THREE.Color, alpha: number): void => {
      p[v * 3] = pt.x; p[v * 3 + 1] = pt.y; p[v * 3 + 2] = pt.z;
      c[v * 4] = col.r; c[v * 4 + 1] = col.g; c[v * 4 + 2] = col.b; c[v * 4 + 3] = alpha;
      v++;
    };
    const alphaOf = (s: TrailSample): number =>
      TRAIL.ALPHA * Math.pow(1 - s.age / TRAIL.LIFETIME, TRAIL.FADE_POWER);

    for (let i = 1; i < this.samples.length; i++) {
      const a = this.samples[i - 1];
      const b = this.samples[i];
      if (b.start) continue; // 새 휘두르기의 첫 점은 이전 것과 잇지 않는다
      const aa = alphaOf(a);
      const ab = alphaOf(b);
      // 안쪽 끝은 옅게(×0.15), 바깥쪽(사슬 끝 궤적)은 진하게 → 칼날 같은 빛줄기
      put(a.inner, this.cInner, aa * 0.15); put(a.outer, this.cOuter, aa); put(b.outer, this.cOuter, ab);
      put(a.inner, this.cInner, aa * 0.15); put(b.outer, this.cOuter, ab); put(b.inner, this.cInner, ab * 0.15);
    }

    this.geometry.setDrawRange(0, v);
    this.geometry.attributes.position.needsUpdate = true;
    this.geometry.attributes.color.needsUpdate = true;
  }
}
