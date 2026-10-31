// SVG → 투명 PNG 렌더러 (Playwright). 사용: node tools/art/render_sprites.js
// 왜: SVG 그대로는 Unity가 읽지 못하므로, 크기를 정확히 맞춰 PNG로 굽는다.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const src = path.join(__dirname, '..', '..', 'assets', 'sprites_src');
const out = path.join(__dirname, '..', '..', 'assets', 'sprites');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ deviceScaleFactor: 1 });
  let n = 0;
  for (const dir of fs.readdirSync(src)) {
    const d = path.join(src, dir);
    if (!fs.statSync(d).isDirectory()) continue;
    fs.mkdirSync(path.join(out, dir), { recursive: true });
    for (const f of fs.readdirSync(d).filter(f => f.endsWith('.svg'))) {
      const svg = fs.readFileSync(path.join(d, f), 'utf8');
      const m = svg.match(/width="(\d+)" height="(\d+)"/);
      await p.setViewportSize({ width: +m[1], height: +m[2] });
      await p.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
      await p.screenshot({ path: path.join(out, dir, f.replace('.svg', '.png')), omitBackground: true, clip: { x: 0, y: 0, width: +m[1], height: +m[2] } });
      n++;
    }
  }
  await b.close();
  console.log(n + ' png');
})();
