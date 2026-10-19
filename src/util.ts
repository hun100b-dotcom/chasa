// ============================================================================
// util.ts — 여러 파일에서 같이 쓰는 작은 수학 도구 모음
// ============================================================================

export const TAU = Math.PI * 2; // 한 바퀴(360°)를 라디안으로 표현한 값

/** 값을 min~max 범위 안으로 가둔다. 예) clamp(15, 0, 10) → 10 */
export const clamp = (v: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, v));

/** a에서 b로 t(0~1) 만큼 간다. t=0 → a, t=1 → b */
export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

/** min~max 사이 랜덤 실수 */
export const rand = (min: number, max: number): number => min + Math.random() * (max - min);

/** 처음엔 빠르고 끝에서 느려지는 움직임 (채찍처럼 확 뻗는 느낌에 사용) */
export const easeOutQuad = (t: number): number => 1 - (1 - t) * (1 - t);

/** 처음엔 느리고 끝에서 빨라지는 움직임 (되감기 등에 사용) */
export const easeInQuad = (t: number): number => t * t;

/** 각도를 -π ~ +π 범위로 정리한다. (각도는 360° 돌면 제자리라서 필요) */
export function wrapPi(a: number): number {
  a = (a + Math.PI) % TAU;
  if (a < 0) a += TAU;
  return a - Math.PI;
}

/** 각도 a에서 b로 '가까운 쪽 방향'으로 최대 maxStep 만큼만 돈다. */
export function turnToward(a: number, b: number, maxStep: number): number {
  const diff = wrapPi(b - a);
  if (Math.abs(diff) <= maxStep) return b;
  return a + Math.sign(diff) * maxStep;
}

/**
 * "사슬 끝이 prev 각도에서 cur 각도까지 쓸고 지나가는 동안, target 각도에 있는 적을 스쳤나?"
 *
 * 왜 이렇게 하나?
 *   사슬은 한 순간에 때리는 게 아니라 호를 그리며 지나간다.
 *   프레임마다 '지난 프레임 → 이번 프레임' 사이 구간을 검사하면
 *   화면에 보이는 사슬이 적을 스치는 바로 그 순간에 맞는다.
 *   halfWidth 는 적의 몸통 폭(각도로 환산)이다. 몸통에 닿기만 해도 맞은 걸로 친다.
 */
export function sweptThrough(prev: number, cur: number, target: number, halfWidth: number): boolean {
  const delta = cur - prev;
  if (delta === 0) return false;
  const sign = Math.sign(delta);
  // 구간 양끝을 몸통 폭만큼 바깥으로 넓힌다
  const from = prev - sign * halfWidth;
  const len = Math.abs(delta) + halfWidth * 2;
  // from 에서 sign 방향으로 target 까지 몇 라디안 가야 하는지 (0 ~ 2π 로 정리)
  let d = (target - from) * sign;
  d = ((d % TAU) + TAU) % TAU;
  return d <= len;
}
