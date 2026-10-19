// ============================================================================
// main.ts — 게임의 시작점. 부품들을 조립하고 매 프레임 돌린다.
// ============================================================================
import * as THREE from 'three';
import { PLAYER } from './config';
import { ClickMarker, DamageNumbers, HitFeel } from './effects';
import { EnemyManager } from './enemy';
import { Input } from './input';
import { Player } from './player';
import { Stage } from './stage';

const stage = new Stage(document.getElementById('app')!);
const feel = new HitFeel();
const numbers = new DamageNumbers(document.getElementById('numbers')!, stage.camera);
const marker = new ClickMarker(stage.scene);

const enemies = new EnemyManager(stage.scene, new THREE.Vector3(0, 0, 0));
const player = new Player(stage.scene, enemies, feel, numbers);
new Input(stage.renderer.domElement, stage.camera, enemies, player, marker);

const shake = new THREE.Vector2();
let last = performance.now();

/**
 * 게임 루프: 브라우저가 화면을 그릴 때마다(보통 초당 60번) 한 번씩 호출된다.
 *
 * 핵심 아이디어 — 시간을 두 종류로 나눈다:
 *   realDt : 진짜로 흐른 시간. 화면 흔들림, 데미지 숫자처럼 "멈추면 안 되는 것"에 사용.
 *   dt     : 게임 세계 시간. 히트스톱 중에는 0 → 캐릭터/적/사슬이 얼어붙는다.
 * 이렇게 하면 "세계는 멈췄는데 화면만 부르르 떨리는" 타격감이 자연스럽게 만들어진다.
 */
function frame(now: number): void {
  // 탭을 오래 비웠다 돌아와도 한 번에 순간이동하지 않도록 최대 0.05초로 제한
  const realDt = Math.min(0.05, (now - last) / 1000);
  last = now;

  const frozen = feel.tick(realDt);
  const dt = frozen ? 0 : realDt;

  player.update(dt);
  enemies.update(dt, player.pos, PLAYER.RADIUS);

  numbers.update(realDt);
  marker.update(realDt);
  stage.render(player.pos, feel.getShakeOffset(shake), realDt);

  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
