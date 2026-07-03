#!/usr/bin/env node
/**
 * 生成训练素材的 PNG + YOLOv8 标注文件
 * 用法: npx tsx scripts/generate_training_pngs.cjs
 */
const fs = require('fs');
const path = require('path');
const { createCanvas, Path2D } = require('@napi-rs/canvas');

globalThis.Path2D = Path2D;
globalThis.document = { createElement: () => createCanvas(1, 1) };

const trainDir = 'public/training';
const files = fs.readdirSync(trainDir).filter(f => f.endsWith('.json') && f !== 'index.json');

const bwTheme = {
  backgroundColor: '#ffffff', noteColor: '#000000', symbolColor: '#000000',
  dashColor: '#000000', dotColor: '#000000', underlineColor: '#000000',
  barlineColor: '#000000', tieColor: '#000000', lyricColor: '#000000',
  techniqueColor: '#000000', repeatDotColor: '#000000',
  paddingHorizontal: 30, paddingVertical: 15, canvasWidth: 800,
};

// ===== YOLOv8 类别定义 =====
const CLASS = {
  // 音符数字 (pitch parsed from NoteLayout.data)
  // pitch_1..7 => 0..6, pitch_0 => 7
  NOTE_BASE: 0,   // 音符1的class = NOTE_BASE + pitch - 1
  REST: 7,        // 休止符 pitch=0
  DASH: 8,        // 增时线
  UNDERLINE_1: 9, // 第一条减时线
  UNDERLINE_2: 10,// 第二条减时线
  DOT: 11,         // 附点
  UPPER_DOT: 12,   // 高音点
  LOWER_DOT: 13,   // 低音点
  ACC_SHARP: 14,   // ♯
  ACC_FLAT: 15,    // ♭
  ACC_NATURAL: 16, // ♮
  FERMATA: 17,     // 延长
  TENUTO: 18,      // 保持音
  ACCENT: 19,      // 重音 >
  BOYIN: 20,       // 波音
  CHANYIN: 21,     // 颤音 tr
  TIE: 22,         // 连音线
  SLUR: 23,        // 圆滑线
  DAYIN: 24,       // 打音
  TUYIN: 25,       // 吐音
  DIEYIN: 26,      // 叠音
  LIYIN: 27,       // 历音
  HUAYIN: 28,      // 滑音
  YINYIN: 29,      // 倚音
  DUNYIN: 30,      // 顿音 ▼
  DYNAMIC_TXT: 31, // pp/mp/f 等
  BAR_SINGLE: 32,   // |
  BAR_DOUBLE: 33,   // ||
  BAR_END: 34,      // |]
  BAR_REPEAT_S: 35, // |:
  BAR_REPEAT_E: 36,  // :|
  REPEAT_ENDING: 37, // 小房子
  CRESCENDO: 38,      // 渐强 <
  DESCRESCENDO: 39,   // 渐弱 >
  LYRIC: 40,          // 歌词
  FORCE_ACCENT: 41,   // sf/sfp/fp
};

// ===== 将绝对值转为 YOLO 归一化值 =====
function toYolo(bb, imgW, imgH) {
  const cx = (bb.x + bb.w / 2) / imgW;
  const cy = (bb.y + bb.h / 2) / imgH;
  const nw = bb.w / imgW;
  const nh = bb.h / imgH;
  // 夹紧到 [0,1]
  return [
    Math.max(0, Math.min(1, cx)),
    Math.max(0, Math.min(1, cy)),
    Math.max(0, Math.min(1, nw)),
    Math.max(0, Math.min(1, nh)),
  ];
}

function collectAnnotations(score, layout, imgW, imgH) {
  const anns = [];
  const push = (cl, x, y, w, h) => {
    if (w <= 0 || h <= 0) return;
    anns.push(`${cl} ${toYolo({x,y,w,h}, imgW, imgH).join(' ')}`);
  };

  let globalMeasureIdx = 0;

  for (const row of layout.rows) {
    for (const measure of row.measures) {
      // === 小节线 ===
      if (measure.barlinePosition) {
        const bp = measure.barlinePosition;
        const bt = measure.data.barline || 'single';
        const cls = {
          single: CLASS.BAR_SINGLE, double: CLASS.BAR_DOUBLE,
          end: CLASS.BAR_END, 'repeat-start': CLASS.BAR_REPEAT_S, 'repeat-end': CLASS.BAR_REPEAT_E,
        }[bt];
        if (cls !== undefined) push(cls, bp.x, bp.y, bp.width, bp.height);
      }

      // === 反复跳跃 ===
      if (measure.repeatEndingPosition) {
        const rp = measure.repeatEndingPosition;
        push(CLASS.REPEAT_ENDING, rp.x, rp.y, rp.width, rp.height);
      }

      // === 渐强/渐弱 ===
      if (measure.data.dynamics && measure.data.dynamics.endMeasureIndex !== undefined) {
        // 找到终点小节
        let endM = null;
        for (const r2 of layout.rows) {
          for (const m2 of r2.measures) {
            if (m2.data === score.measures[measure.data.dynamics.endMeasureIndex]) {
              endM = m2;
            }
          }
        }
        if (endM) {
          const cls = measure.data.dynamics.type === 'crescendo' ? CLASS.CRESCENDO : CLASS.DESCRESCENDO;
          const x1 = measure.position.x;
          const x2 = endM.position.x + endM.position.width;
          const y1 = measure.position.y + measure.position.height + 6;
          const h = 12;
          // 检查起始小节是否有其他力度标记占位
          let xStart = x1;
          for (const nl of measure.notes) {
            if (nl.dynamicPosition) {
              const te = nl.dynamicPosition.x + nl.dynamicPosition.width;
              if (te > xStart) xStart = te + 4;
            }
          }
          push(cls, xStart, y1, x2 - xStart, h);
        }
      }

      for (const nl of measure.notes) {
        const pos = nl.position;
        const data = nl.data;

        // === 音符数字 / 休止符 ===
        if (data.pitch !== undefined) {
          const cl = data.pitch === 0 ? CLASS.REST : (CLASS.NOTE_BASE + data.pitch - 1);
          // 音符数字的实际宽度（比 pos.width 窄一些）
          const dw = pos.width * 0.55;
          const dx = pos.x + pos.width / 2 - dw / 2;
          push(cl, dx, pos.y + 2, dw, pos.height - 4);
        }

        // === 增时线 ===
        if (data.type === 'dash') {
          push(CLASS.DASH, pos.x + pos.width * 0.35, pos.y + pos.height / 2 - 1, pos.width * 0.3, 2);
        }

        // === 附点 ===
        for (const dp of (nl.dotPositions || [])) {
          push(CLASS.DOT, dp.x, dp.y, dp.width, dp.height);
        }

        // === 高音点 ===
        for (const up of (nl.upperDotPositions || [])) {
          push(CLASS.UPPER_DOT, up.x, up.y, up.width, up.height);
        }

        // === 低音点 ===
        for (const lp of (nl.lowerDotPositions || [])) {
          push(CLASS.LOWER_DOT, lp.x, lp.y, lp.width, lp.height);
        }

        // === 升降号 ===
        if (nl.accidentalPosition) {
          const ap = nl.accidentalPosition;
          const accMap = { sharp: CLASS.ACC_SHARP, flat: CLASS.ACC_FLAT, natural: CLASS.ACC_NATURAL };
          const cl = accMap[data.accidental];
          if (cl !== undefined) push(cl, ap.x, ap.y, ap.width, ap.height);
        }

        // === 减时线 ===
        let ulIdx = 0;
        for (const ul of (nl.underlines || [])) {
          const sx = nl.position.x + (ul.xOffset || 0);
          if (ul.width > 0) {
            push(ulIdx === 0 ? CLASS.UNDERLINE_1 : CLASS.UNDERLINE_2, sx, ul.y, ul.width, 1.5);
          }
          ulIdx++;
        }

        // === 重音 ===
        if (nl.accentPosition) {
          push(CLASS.ACCENT, nl.accentPosition.x, nl.accentPosition.y, nl.accentPosition.width, nl.accentPosition.height);
        }

        // === 保持音 ===
        if (nl.tenutoPosition) {
          push(CLASS.TENUTO, nl.tenutoPosition.x, nl.tenutoPosition.y, nl.tenutoPosition.width, nl.tenutoPosition.height);
        }

        // === 延长记号 ===
        if (nl.fermataPosition) {
          push(CLASS.FERMATA, nl.fermataPosition.x, nl.fermataPosition.y, nl.fermataPosition.width, nl.fermataPosition.height);
        }

        // === 歌词 ===
        const lyricPositions = nl.lyricPositions || (nl.lyricPosition ? [nl.lyricPosition] : []);
        for (const lp of lyricPositions) {
          push(CLASS.LYRIC, lp.x, lp.y, lp.width, lp.height);
        }

        // === 技巧符号 ===
        for (const tp of (nl.techniquePositions || [])) {
          const tpos = tp.position;
          const tech = tp.technique;
          let cl;
          switch (tech.type) {
            case 'boyin': cl = CLASS.BOYIN; break;
            case 'chanyin': cl = CLASS.CHANYIN; break;
            case 'dayin': cl = CLASS.DAYIN; break;
            case 'tuyin': cl = CLASS.TUYIN; break;
            case 'dieyin': cl = CLASS.DIEYIN; break;
            case 'liyin': cl = CLASS.LIYIN; break;
            case 'huayin': cl = CLASS.HUAYIN; break;
            case 'yinyin': cl = CLASS.YINYIN; break;
            case 'dunyin': cl = CLASS.DUNYIN; break;
          }
          if (cl !== undefined) {
            // 技巧符号区域通常包含了文字，宽高需要调整
            const tw = tpos.width || 16;
            const th = tpos.height || 12;
            push(cl, tpos.x, tpos.y, tw, th);
          }
        }

        // === 力度文字 (pp/mp/f 等) ===
        if (nl.dynamicPosition) {
          push(CLASS.DYNAMIC_TXT, nl.dynamicPosition.x, nl.dynamicPosition.y, nl.dynamicPosition.width, nl.dynamicPosition.height);
        }

        // === 力度突变 (sf/sfp/fp) ===
        if (data.forceAccent) {
          // forceAccent 的近似位置：音符上方偏左
          const fax = pos.x + pos.width / 2 - 10;
          const fay = pos.y - 16;
          push(CLASS.FORCE_ACCENT, fax, fay, 20, 14);
        }
      }

      // === 连音线和圆滑线（从 tieStarts/slurStarts 收集） ===
      // 需要在行遍历时收集配对信息
      globalMeasureIdx++;
    }
  }

  // === 第二遍遍历：收集连音线/圆滑线配对 ===
  const tieStarts = new Map();
  const slurStarts = new Map();
  const allMeasures = [];
  for (const row of layout.rows) {
    for (const m of row.measures) {
      allMeasures.push(m);
      for (const nl of m.notes) {
        if (nl.tieId) {
          if (!tieStarts.has(nl.tieId)) {
            tieStarts.set(nl.tieId, { note: nl, measure: m });
          } else {
            const start = tieStarts.get(nl.tieId);
            // 计算连音线包围盒
            const x1 = start.note.position.x + start.note.position.width / 2;
            const x2 = nl.position.x + nl.position.width / 2;
            const y1 = start.note.position.y - 4;
            const dist = x2 - x1;
            const ch = Math.max(6, dist * 0.2);
            const minX = Math.min(x1, x2);
            const maxX = Math.max(x1, x2);
            push(CLASS.TIE, minX - 4, y1 - ch - 2, maxX - minX + 8, ch + 4);
            tieStarts.delete(nl.tieId);
          }
        }
        if (nl.slurId) {
          if (!slurStarts.has(nl.slurId)) {
            slurStarts.set(nl.slurId, { note: nl });
          } else {
            const start = slurStarts.get(nl.slurId);
            const x1 = start.note.position.x + start.note.position.width / 2;
            const x2 = nl.position.x + nl.position.width / 2;
            const y1 = start.note.position.y - 2;
            const dist = x2 - x1;
            const ch = Math.max(10, dist * 0.2);
            const minX = Math.min(x1, x2);
            const maxX = Math.max(x1, x2);
            push(CLASS.SLUR, minX - 4, y1 - ch - 2, maxX - minX + 8, ch + 4);
            slurStarts.delete(nl.slurId);
          }
        }
      }
    }
  }

  return anns;
}

// ===== 主流程 =====
let count = 0;
for (const file of files) {
  const data = JSON.parse(fs.readFileSync(`${trainDir}/${file}`, 'utf-8'));
  delete data.title; delete data.key; delete data.tempo; delete data.tempoText; delete data.introMeasureCount;

  // 动态加载
  delete require.cache[require.resolve('../src/engine/index')];
  delete require.cache[require.resolve('../src/engine/layout')];
  delete require.cache[require.resolve('../src/engine/renderer')];
  delete require.cache[require.resolve('../src/engine/symbols')];

  const { calculateLayout, DEFAULT_CONFIG, render } = require('../src/engine/index');
  const config = { ...DEFAULT_CONFIG, ...bwTheme, paddingVertical: 10 };
  const layout = calculateLayout(data, config);

  layout.titlePosition = undefined;
  layout.keyPosition = undefined;
  layout.timeSignaturePosition = undefined;

  // === PNG ===
  const canvas = createCanvas(layout.width, layout.height);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, layout.width, layout.height);
  render(ctx, layout, data, config, bwTheme);

  const pngFile = file.replace('.json', '.png');
  fs.writeFileSync(`${trainDir}/${pngFile}`, canvas.toBuffer('image/png'));

  // === YOLOv8 标注 ===
  const anns = collectAnnotations(data, layout, layout.width, layout.height);
  const labelFile = file.replace('.json', '.txt');
  fs.writeFileSync(`${trainDir}/${labelFile}`, anns.join('\n') + (anns.length ? '\n' : ''));

  console.log(`✓ ${pngFile} (${anns.length} labels)`);
  count++;
}
console.log(`\nDone! ${count} PNGs + labels → ${trainDir}/`);

// 生成 YOLOv8 的 data.yaml
const classNames = [
  'pitch_1','pitch_2','pitch_3','pitch_4','pitch_5','pitch_6','pitch_7','rest',
  'dash','underline_1','underline_2','dot','upper_dot','lower_dot',
  'sharp','flat','natural','fermata','tenuto','accent',
  'boyin','chanyin','tie','slur','dayin','tuyin','dieyin','liyin','huayin','yinyin','dunyin',
  'dynamic','bar_single','bar_double','bar_end','bar_repeat_start','bar_repeat_end',
  'repeat_ending','crescendo','descrescendo','lyric','force_accent',
];
const yaml = `# YOLOv8 training data config
path: ${path.resolve(trainDir)}
train: .
val: .

nc: ${classNames.length}
names: ${JSON.stringify(classNames)}
`;
fs.writeFileSync(`${trainDir}/data.yaml`, yaml);
console.log(`✓ data.yaml (${classNames.length} classes)`);
