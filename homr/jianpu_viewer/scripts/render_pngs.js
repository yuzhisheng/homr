#!/usr/bin/env node
/**
 * 将 public/training/ 下的 JSON 简谱渲染为 PNG
 * 启动一个临时 HTML 页通过浏览器渲染
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const trainDir = path.join(__dirname, '..', 'public', 'training');
const files = fs.readdirSync(trainDir).filter(f => f.endsWith('.json'));

// 生成一个 HTML 文件，包含所有简谱的 Canvas 渲染
const scores = files.map(f => ({
  name: f.replace('.json', ''),
  data: JSON.parse(fs.readFileSync(path.join(trainDir, f), 'utf-8')),
}));

const html = `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Render</title></head>
<body style="margin:0;padding:0;background:white;">
${scores.map((s, i) => `
<div style="margin:20px 0; padding:10px;">
  <canvas id="c${i}" style="border:1px solid #ccc;"></canvas>
</div>`).join('\n')}
<script type="module">
import { calculateLayout, DEFAULT_CONFIG, render, DEFAULT_THEME } from '/src/engine/index.ts';
import { setupCanvasDPI } from '/src/engine/index.ts';

const scores = ${JSON.stringify(scores.map(s => s.data))};

async function renderAll() {
  for (let i = 0; i < scores.length; i++) {
    const canvas = document.getElementById('c' + i);
    const config = { ...DEFAULT_CONFIG, canvasWidth: 900 };
    const layout = calculateLayout(scores[i], config);
    const ctx = setupCanvasDPI(canvas, layout.width, layout.height);
    render(ctx, layout, scores[i], config, DEFAULT_THEME);
  }
}

renderAll().then(() => {
  document.body.setAttribute('data-ready', 'true');
});
</script>
</body></html>`;

fs.writeFileSync(path.join(trainDir, 'render.html'), html);
console.log(`Generated render.html with ${scores.length} scores`);
console.log('Open http://localhost:5173/training/render.html to view');
console.log('Then manually screenshot each canvas or use browser dev tools');
