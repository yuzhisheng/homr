import type {
  Score, Measure, Note as NoteType, Dash,
  ScoreLayout, RowLayout, MeasureLayout, NoteLayout, SymbolPosition,
  DiziTechnique,
} from '../types';

/** 布局配置参数 */
export interface LayoutConfig {
  /** 画布宽度 */
  canvasWidth: number;
  /** 左右边距 */
  paddingHorizontal: number;
  /** 上下边距 */
  paddingVertical: number;
  /** 音符主体字体大小 */
  noteFontSize: number;
  /** 音符宽度（占位宽度） */
  noteWidth: number;
  /** 音符高度 */
  noteHeight: number;
  /** 小节间距 */
  measureGap: number;
  /** 行间距 */
  rowGap: number;
  /** 八度点直径 */
  dotRadius: number;
  /** 八度点间距 */
  dotGap: number;
  /** 附点直径 */
  accentDotRadius: number;
  /** 减时线偏移 */
  underlineOffset: number;
  /** 减时线间距 */
  underlineGap: number;
  /** 减时线粗细 */
  underlineThickness: number;
  /** 增时线粗细 */
  dashThickness: number;
  /** 小节线宽度 */
  barlineWidth: number;
  /** 技巧符号字体大小 */
  techniqueFontSize: number;
  /** 技巧符号偏移 */
  techniqueOffset: number;
  /** 标题字体大小 */
  titleFontSize: number;
  /** 元信息字体大小 */
  metaFontSize: number;
  /** 连音线弧度 */
  tieCurveHeight: number;
  /** 歌词字体大小 */
  lyricFontSize: number;
  /** 歌词偏移 */
  lyricOffset: number;
}

export const DEFAULT_CONFIG: LayoutConfig = {
  canvasWidth: 800,
  paddingHorizontal: 24,
  paddingVertical: 24,
  noteFontSize: 18,
  noteWidth: 22,
  noteHeight: 22,
  measureGap: 12,
  rowGap: 14,
  dotRadius: 1.5,
  dotGap: 2,
  accentDotRadius: 1.5,
  underlineOffset: 2.5,
  underlineGap: 2.5,
  underlineThickness: 1,
  dashThickness: 1.2,
  barlineWidth: 1,
  techniqueFontSize: 9,
  techniqueOffset: 0,
  titleFontSize: 14,
  metaFontSize: 11,
  tieCurveHeight: 6,
  lyricFontSize: 9,
  lyricOffset: 14,
};

function isNote(item: NoteType | Dash): item is NoteType {
  return 'pitch' in item;
}

/** 音符主体之间的水平间距：固定 noteWidth（不按时值区分） */
function getNoteSpacing(_duration: number, cfg: LayoutConfig): number {
  return cfg.noteWidth;
}

/** 计算单个音符的布局 */
function layoutNote(
  item: NoteType | Dash,
  x: number,
  y: number,
  config: LayoutConfig,
  measureIndex: number,
  noteIndex: number,
  groupInfo?: { underlineLevel: number; groupStartX: number; groupWidth: number },
): NoteLayout {
  const pos: SymbolPosition = { x, y, width: config.noteWidth, height: config.noteHeight };
  const upperDots: SymbolPosition[] = [];
  const lowerDots: SymbolPosition[] = [];
  const dotPositions: SymbolPosition[] = [];

  if (isNote(item)) {
    const note = item;
    // 八度点
    const octave = note.octave || 0;
    if (octave > 0) {
      for (let i = 0; i < octave; i++) {
        upperDots.push({
          x: x + config.noteWidth / 2 - config.dotRadius,
          y: y - config.dotRadius + 2 - (i > 0 ? config.dotGap * i : 0),
          width: config.dotRadius * 2,
          height: config.dotRadius * 2,
        });
      }
    }
    if (octave < 0) {
      for (let i = 0; i < -octave; i++) {
        lowerDots.push({
          x: x + config.noteWidth / 2 - config.dotRadius,
          y: y + config.noteHeight - 3.5 + config.dotGap * i,
          width: config.dotRadius * 2,
          height: config.dotRadius * 2,
        });
      }
    }

    // 附点（紧贴音符右侧）
    const dotCount = note.dot || 0;
    for (let i = 0; i < dotCount; i++) {
      dotPositions.push({
        x: x + config.noteWidth - 3 + i * (config.accentDotRadius * 2 + 3),
        y: y + config.noteHeight / 2 - config.accentDotRadius,
        width: config.accentDotRadius * 2,
        height: config.accentDotRadius * 2,
      });
    }

    // 升降号位置（左上角紧贴音符）
    let accidentalPos: SymbolPosition | undefined;
    if (note.accidental) {
      accidentalPos = {
        x: x - 2,
        y: y - 3,
        width: 16,
        height: 16,
      };
    }

    // 减时线（比音符宽度略窄，留出左右边距）
    const underlines: { y: number; width: number; xOffset: number }[] = [];
    if (groupInfo && groupInfo.underlineLevel > 0) {
      // 分组音符：横线从组内第一个音符左边缘到最后一个音符右边缘
      for (let i = 0; i < groupInfo.underlineLevel; i++) {
        underlines.push({
          y: y + config.noteHeight + config.underlineOffset + config.underlineGap * i,
          width: groupInfo.groupWidth,
          xOffset: groupInfo.groupStartX - x,
        });
      }
    } else if (!groupInfo) {
      const levels = getUnderlineLevel(note.duration);
      // 单个音符：宽度占位用全宽，渲染时按实际数字宽度调整
      for (let i = 0; i < levels; i++) {
        underlines.push({
          y: y + config.noteHeight + config.underlineOffset + config.underlineGap * i,
          width: config.noteWidth,
          xOffset: 0,
        });
      }
    }

    // 技巧符号位置（装饰符号尽量靠近音符顶部但不重叠）
    const techniquePositions: { technique: DiziTechnique; position: SymbolPosition }[] = [];
    const techYBase = y - config.techniqueFontSize + 4;
    const hasYinyin = note.techniques?.some(t => t.type === 'yinyin') ?? false;
    if (note.techniques) {
      note.techniques.forEach((tech, idx) => {
        if (tech.type === 'yinyin') {
          const notes = tech.graceNotes || [];
          const label = notes.join('');
          const gFontSize = config.techniqueFontSize + 1;
          const width = label.length * gFontSize * 0.6 + 2;
          techniquePositions.push({
            technique: tech,
            position: {
              x: x - width + 4,
              y: y - gFontSize - 2,
              width,
              height: gFontSize + 6,
            },
            mainNotePos: { x: x + config.noteWidth / 2, y: y + 2, width: 0, height: 0 },
          });
          return;
        }
        // 历音 - 下历音在左侧(像倚音), 上历音在右侧(像赠音)
        if (tech.type === 'liyin') {
          const gFontSize = config.techniqueFontSize + 1;
          const width = gFontSize * 0.6 + 2;
          const isDown = tech.liyinDirection === 'down';
          techniquePositions.push({
            technique: tech,
            position: {
              x: isDown ? x - width + 4 : x + config.noteWidth - 2,
              y: y - gFontSize - 2,
              width,
              height: gFontSize + 6,
            },
            mainNotePos: { x: x + config.noteWidth / 2, y: y + 2, width: 0, height: 0 },
          });
          return;
        }
        // 赠音 - 在音符右侧，与倚音对称
        if (tech.type === 'zengyin') {
          const label = tech.giftPitch !== undefined ? String(tech.giftPitch) : '赠';
          const gFontSize = config.techniqueFontSize + 1;
          const width = label.length * gFontSize * 0.6 + 2;
          techniquePositions.push({
            technique: tech,
            position: {
              x: x + config.noteWidth - 2,
              y: y - gFontSize - 2,
              width,
              height: gFontSize + 6,
            },
            mainNotePos: { x: x + config.noteWidth / 2, y: y + 2, width: 0, height: 0 },
          });
          return;
        }
        // 倚音上叠加颤音 — 颤音"tr"定位在倚音区域上方
        if (tech.type === 'chanyin' && hasYinyin) {
          const yinyinTech = note.techniques!.find(t => t.type === 'yinyin')!;
          const graceNotes = yinyinTech.graceNotes || [];
          const label = graceNotes.join('');
          const gFontSize = config.techniqueFontSize + 1;
          const yinyinWidth = label.length * gFontSize * 0.6 + 2;
          techniquePositions.push({
            technique: tech,
            position: {
              x: x - yinyinWidth + 4,
              y: y - gFontSize - 2 - config.techniqueFontSize - 6,
              width: yinyinWidth,
              height: config.techniqueFontSize + 4,
            },
          });
          return;
        }
        const label = getTechniqueLabel(tech);
        const width = label.length * config.techniqueFontSize * 0.7;
        techniquePositions.push({
          technique: tech,
          position: {
            x: x + config.noteWidth / 2 - width / 2,
            y: techYBase,
            width,
            height: config.techniqueFontSize,
          },
        });
      });
    }

    // 重音、保持音、延长记号（音符上方，避免重叠）
    const hasTechniques = (note.techniques?.length || 0) > 0;
    const accentY = hasTechniques
      ? techYBase - config.techniqueFontSize - 2
      : y - 8;

    const accentPosition = note.accent ? {
      x: x + config.noteWidth / 2 - 5,
      y: accentY,
      width: 10, height: 8,
    } : undefined;

    const tenutoPosition = note.tenuto ? {
      x: x + config.noteWidth / 2 - 8,
      y: y - 8,
      width: 16, height: 3,
    } : undefined;

    const fermataPosition = note.fermata ? {
      x: x + config.noteWidth / 2 - 10,
      y: hasTechniques ? accentY - 10 : y - 12,
      width: 20, height: 14,
    } : undefined;

    const staccatoPosition = note.staccato ? {
      x: x + config.noteWidth / 2 - 8,
      y: y - 6,
      width: 16, height: 8,
    } : undefined;

    const breathPosition = note.breathMark ? {
      x: x + config.noteWidth + 2,
      y: y - 2,
      width: 16, height: 8,
    } : undefined;

    // 歌词（支持多行）
    const allLines = note.lyrics || (note.lyric ? [note.lyric] : []);
    const lineGap = 2;
    const baseLyricY = y + config.noteHeight + config.lyricOffset
      + (groupInfo?.underlineLevel || 0) * config.underlineGap + config.underlineOffset;
    const lyricPositions = allLines.map((line, idx) => ({
      x: x + config.noteWidth / 2 - line.length * config.lyricFontSize * 0.5,
      y: baseLyricY + config.lyricFontSize + idx * (config.lyricFontSize + lineGap),
      width: line.length * config.lyricFontSize,
      height: config.lyricFontSize,
    }));
    const lyricPosition = lyricPositions.length > 0 ? lyricPositions[0] : undefined;

    // 力度标记 (pp/mp/mf/f/ff 等)，与渐强渐弱符号同一水平线
    const dynamicPosition = note.dynamic ? {
      x: x + config.noteWidth / 2 - note.dynamic.length * config.lyricFontSize * 0.4,
      y: y + config.noteHeight + 11,
      width: note.dynamic.length * config.lyricFontSize,
      height: config.lyricFontSize,
    } : undefined;

    return {
      type: 'note',
      data: note,
      measureIndex,
      noteIndex,
      position: pos,
      upperDotPositions: upperDots,
      lowerDotPositions: lowerDots,
      dotPositions,
      accidentalPosition: accidentalPos,
      underlines,
      dashLinePositions: [],
      techniquePositions,
      tieStart: !!note.tieId,
      tieEnd: !!note.tieId,
      tieId: note.tieId,
      slurStart: !!note.slurId,
      slurEnd: !!note.slurId,
      slurId: note.slurId,
      tripletId: note.tripletId,
      tripletStart: !!note.tripletId,
      tripletEnd: !!note.tripletId,
      accentPosition,
      tenutoPosition,
      fermataPosition,
      staccatoPosition,
      breathPosition,
      lyricPosition,
      lyricPositions: lyricPositions.length > 1 ? lyricPositions : undefined,
      dynamicPosition,
    };
  }

  // Dash (增时线)
  return {
    type: 'dash',
    data: item,
    measureIndex,
    noteIndex,
    position: pos,
    upperDotPositions: upperDots,
    lowerDotPositions: lowerDots,
    dotPositions,
    underlines: [],
    dashLinePositions: [],
    techniquePositions: [],
    tieId: item.tieId,
  };
}

/** 获取技巧符号显示文本 */
function getTechniqueLabel(tech: DiziTechnique): string {
  const labels: Record<string, string> = {
    zengyin: '赠',
    dieyin: '又',
    liyin: tech.liyinDirection === 'up' ? '历↑' : '历↓',
    huayin: tech.slideDirection === 'up' ? '↗' : '↘',
    dayin: '扌',
    yinyin: '倚',
    chanyin: 'tr',
    qizhenyin: '〰',
    tuyin: tech.articulation === 'double' ? 'TK' : tech.articulation === 'triple' ? 'TKT' : 'T',
    huashe: '✱',
    xunhuan: '↻',
    fanyin: 'o',
  };
  return labels[tech.type] || tech.type;
}

/** 分析小节中的减时线分组：按拍号划界，同一拍内的所有短音符共享一组 */
interface UnderlineGroup {
  startIndex: number;
  endIndex: number;
  level: number;
}

function analyzeUnderlineGroups(
  notes: (NoteType | Dash)[],
  beatsPerMeasure: number,
  beatUnitDuration: number,
): UnderlineGroup[] {
  const groups: UnderlineGroup[] = [];
  // 按拍号切拍：每拍 = beatUnitDuration 时值
  // 同一拍内所有带减时线的短音符合并为一组，level 取组内最大
  // Dash（增时线）不参与累计和分组
  // 大时值音符（duration >= beatUnitDuration）独占对应拍位但不参与减时线分组
  let i = 0;
  let beatIdx = 0;

  while (i < notes.length && beatIdx < beatsPerMeasure) {
    let acc = 0;
    let curStart = -1;
    let curEnd = -1;
    let curLevel = 0;

    // 在当前拍内累计时值
    while (acc < beatUnitDuration - 1e-6 && i < notes.length) {
      const item = notes[i];
      if (!isNote(item)) {
        i++;
        continue;
      }
      const noteLevel = getUnderlineLevel(item.duration);

      if (noteLevel > 0) {
        // 短音符：参与当前拍组
        if (curStart < 0) curStart = i;
        curEnd = i;
        if (noteLevel > curLevel) curLevel = noteLevel;
      } else {
        // 大时值音符（duration >= 0.5，level=0）：独立成"无横线"组，
        // 但只有当它正好占满当前拍剩余空间时才不影响后面的累计；否则跳过
      }

      acc += item.duration;
      i++;
    }

    if (curStart >= 0) {
      groups.push({ startIndex: curStart, endIndex: curEnd, level: curLevel });
    }
    beatIdx++;
  }

  // 处理超出所有拍的小节尾部（数据不规范时）
  // 把剩余的连续短音符合并成最后一个组
  let curStart = -1;
  let curEnd = -1;
  let curLevel = 0;
  while (i < notes.length) {
    const item = notes[i];
    if (!isNote(item)) { i++; continue; }
    const noteLevel = getUnderlineLevel(item.duration);
    if (noteLevel > 0) {
      if (curStart < 0) curStart = i;
      curEnd = i;
      if (noteLevel > curLevel) curLevel = noteLevel;
    }
    i++;
  }
  if (curStart >= 0) {
    groups.push({ startIndex: curStart, endIndex: curEnd, level: curLevel });
  }

  return groups;
}

function getUnderlineLevel(duration: number): number {
  if (duration <= 0.125) return 3;
  if (duration <= 0.25) return 2;
  if (duration <= 0.5) return 1;
  return 0;
}

/** 计算一行中能容纳的小节数 */
function fitMeasuresInRow(
  measures: Measure[],
  startIdx: number,
  availWidth: number,
  config: LayoutConfig,
): number {
  let width = 0;
  let count = 0;
  for (let i = startIdx; i < measures.length; i++) {
    const m = measures[i];
    const noteCount = m.notes.length;
    const dashCount = m.notes.filter(n => !isNote(n)).length;
    let mWidth = 0;
    m.notes.forEach(n => {
      if (isNote(n)) {
        mWidth += getNoteSpacing(n.duration, config);
        if ((n.dot || 0) > 0) {
          mWidth += (n.dot || 0) * (config.accentDotRadius * 2 + 10);
        }
        if (n.accidental) {
          mWidth += 10;
        }
      } else {
        mWidth += config.noteWidth;
      }
    });
    mWidth += config.barlineWidth;
    if (count > 0) mWidth += config.measureGap;
    if (width + mWidth > availWidth && count > 0) break;
    width += mWidth;
    count++;
  }
  return Math.max(count, 1);
}

/** 主布局计算函数 */
export function calculateLayout(score: Score, config: LayoutConfig = DEFAULT_CONFIG): ScoreLayout {
  const cfg = { ...DEFAULT_CONFIG, ...config };
  const contentWidth = cfg.canvasWidth - cfg.paddingHorizontal * 2;
  let currentY = cfg.paddingVertical;

  // 标题
  const titlePosition: SymbolPosition | undefined = score.title ? {
    x: cfg.paddingHorizontal,
    y: currentY,
    width: contentWidth,
    height: cfg.titleFontSize + 8,
  } : undefined;
  if (titlePosition) currentY += titlePosition.height + 8;

  // 调号、拍号、速度标记
  const metaY = currentY;
  const keyText = `1=${score.key}`;
  const tempoText = score.tempo ? `♩=${score.tempo}` : '';

  const keyPosition: SymbolPosition = {
    x: cfg.paddingHorizontal,
    y: metaY,
    width: keyText.length * cfg.metaFontSize * 0.7,
    height: cfg.metaFontSize + 4,
  };
  // 拍号放在调号右边，垂直居中对齐
  const tsDigitWidth = cfg.metaFontSize * 0.65;
  const tsLineWidth = tsDigitWidth + 4;
  const tsTotalHeight = cfg.metaFontSize * 2 + 10; // 两个数字 + 横线 + 间距
  const keyCenterY = metaY + (cfg.metaFontSize + 4) / 2;
  const timeSignaturePosition: SymbolPosition = {
    x: keyPosition.x + keyPosition.width + 6,
    y: keyCenterY - tsTotalHeight / 2,
    width: tsLineWidth,
    height: tsTotalHeight,
  };
  // 速度标记放在调号下方，左对齐
  let tempoPosition: SymbolPosition | undefined;
  if (tempoText) {
    tempoPosition = {
      x: cfg.paddingHorizontal,
      y: metaY + (cfg.metaFontSize + 4) + 6,
      width: tempoText.length * cfg.metaFontSize * 0.6,
      height: cfg.metaFontSize + 4,
    };
  }
  currentY = tempoPosition
    ? tempoPosition.y + tempoPosition.height + 4
    : timeSignaturePosition.y + tsTotalHeight + 4;
  currentY += 60; // 谱子主体额外下移

  // 计算行布局
  const rows: RowLayout[] = [];
  let measureIdx = 0;

  while (measureIdx < score.measures.length) {
    const fitCount = fitMeasuresInRow(score.measures, measureIdx, contentWidth, cfg);
    const rowMeasures = score.measures.slice(measureIdx, measureIdx + fitCount);

    const measureLayouts: MeasureLayout[] = [];
    // 所有行统一为前奏左括号预留空间，保证各行第一个音符左对齐
    const introBracketGap = score.introMeasureCount ? cfg.noteWidth * 0.6 : 0;
    let currentX = cfg.paddingHorizontal + introBracketGap;
    let prevBarlineX = currentX; // 追踪上一个小节线位置（用于小房子左端对齐）

    // 如果有小房子（反复跳跃记号），整行往下移给小房子腾空间
    if (rowMeasures.some(m => m.repeatEnding)) {
      currentY += 34;
    }

    for (let mi = 0; mi < rowMeasures.length; mi++) {
      const m = rowMeasures[mi];
      const mStartX = currentX;

      // 分析减时线分组（按拍号划界）
      const groups = analyzeUnderlineGroups(
        m.notes,
        score.timeSignature.numerator,
        4 / score.timeSignature.denominator,
      );

      // 计算小节宽度
      let mWidth = m.notes.length * cfg.noteWidth;
      m.notes.forEach(n => {
        if (isNote(n) && (n.dot || 0) > 0) {
          mWidth += (n.dot || 0) * (cfg.accentDotRadius * 2 + 12);
        }
        if (isNote(n) && n.accidental) {
          mWidth += 14;
        }
      });
      mWidth += cfg.barlineWidth;

      // 音符布局
      const noteLayouts: NoteLayout[] = [];
      let noteX = mStartX;

      for (let ni = 0; ni < m.notes.length; ni++) {
        const item = m.notes[ni];

        // 查找是否属于某个减时线分组
        const group = groups.find(g => ni >= g.startIndex && ni <= g.endIndex);
        // 属于分组的音符不创建独立横线，由后面 post-processing 统一绘制
        const groupInfo = group ? { underlineLevel: 0, groupStartX: 0, groupWidth: 0 } : undefined;

        const nl = layoutNote(item, noteX, currentY, cfg, measureIdx + mi, ni, groupInfo);
        noteLayouts.push(nl);

        let advanceX = isNote(item) ? getNoteSpacing(item.duration, cfg) : cfg.noteWidth;
        if (isNote(item) && (item.dot || 0) > 0) {
          advanceX += (item.dot || 0) * (cfg.accentDotRadius * 2 + 10);
        }
        if (isNote(item) && item.accidental) {
          advanceX += 10;
        }
        noteX += advanceX;
      }

      // 根据音符实际位置修正分组减时线
      // 每个层级分别计算连续覆盖区间：
      //   第1层覆盖组内全部短音符；第2/3层只覆盖 level>=2/3 的连续音符
      groups.forEach(g => {
        const first = noteLayouts[g.startIndex];
        if (!first) return;

        type UL = {
          y: number; width: number; xOffset: number;
          groupFirstCenter: number; groupLastCenter: number;
          groupFirstPitch: number; groupLastPitch: number;
        };
        const arr: UL[] = [];

        // 对每个层级，找出该层级对应的连续音符段
        for (let li = 0; li < g.level; li++) {
          const requiredLevel = li + 1;
          let segStart = -1;
          for (let ni = g.startIndex; ni <= g.endIndex; ni++) {
            const item = m.notes[ni];
            const nLevel = isNote(item) ? getUnderlineLevel(item.duration) : 0;
            const inSeg = nLevel >= requiredLevel;
            if (inSeg && segStart < 0) {
              segStart = ni;
            }
            // 段结束：当前音符不在段内，或到达组末尾
            const isLastInGroup = ni === g.endIndex;
            if ((!inSeg || isLastInGroup) && segStart >= 0) {
              const segEnd = inSeg && isLastInGroup ? ni : ni - 1;
              const sFirst = noteLayouts[segStart];
              const sLast = noteLayouts[segEnd];
              if (sFirst && sLast) {
                const fCenter = sFirst.position.x + sFirst.position.width / 2;
                const lCenter = sLast.position.x + sLast.position.width / 2;
                const fPitch = 'pitch' in sFirst.data ? sFirst.data.pitch : -1;
                const lPitch = 'pitch' in sLast.data ? sLast.data.pitch : -1;
                arr.push({
                  y: currentY + cfg.noteHeight + cfg.underlineOffset + cfg.underlineGap * li,
                  width: lCenter - fCenter,
                  xOffset: fCenter - first.position.x,
                  groupFirstCenter: fCenter,
                  groupLastCenter: lCenter,
                  groupFirstPitch: fPitch,
                  groupLastPitch: lPitch,
                });
              }
              segStart = -1;
            }
          }
        }
          // 组内只有第一个音符的 underlines 保留有效数据
        first.underlines = arr as unknown as { y: number; width: number; xOffset: number }[];
        for (let gi = g.startIndex + 1; gi <= g.endIndex; gi++) {
          noteLayouts[gi].underlines = [];
        }
      });
      // 单独的音符（不在分组中）使用 layoutNote 已创建的独立横线

      // 每次小节线前留出间距，与后面间距一致
      noteX += 10;
      if (m.barline === 'repeat-end' || m.barline === 'repeat-start') {
        noteX += 6;
      }

      // 小节线
      const barlinePos: SymbolPosition = {
        x: noteX,
        y: currentY - 4,
        width: cfg.barlineWidth,
        height: cfg.noteHeight + 8,
      };

      // 反复跳跃记号（小房子左端对齐上一个小节线，右端对齐当前小节线）
      const repeatEndingPos = m.repeatEnding ? {
        x: prevBarlineX,
        y: currentY - 34,
        width: noteX - prevBarlineX,
        height: 18,
      } as SymbolPosition : undefined;

      const globalMeasureIdx = measureIdx + mi;
      const bracketLeft = (score.introMeasureCount && globalMeasureIdx === 0) ? {
        x: cfg.paddingHorizontal + introBracketGap / 2,
        y: currentY + cfg.noteHeight / 2,
        width: cfg.noteWidth,
        height: cfg.noteHeight,
      } as SymbolPosition : undefined;
      const lastNoteX = noteLayouts.length > 0
        ? noteLayouts[noteLayouts.length - 1].position.x + noteLayouts[noteLayouts.length - 1].position.width
        : noteX;
      const bracketRight = (score.introMeasureCount && globalMeasureIdx === score.introMeasureCount - 1) ? {
        x: lastNoteX + 4,
        y: currentY + cfg.noteHeight / 2,
        width: cfg.noteWidth,
        height: cfg.noteHeight,
      } as SymbolPosition : undefined;

      measureLayouts.push({
        data: m,
        position: { x: mStartX, y: currentY, width: mWidth, height: cfg.noteHeight },
        barlinePosition: barlinePos,
        notes: noteLayouts,
        repeatEndingPosition: repeatEndingPos,
        bracketLeft,
        bracketRight,
      });

      currentX = noteX + cfg.barlineWidth + 10;
      prevBarlineX = noteX;
    }

    // 计算本行最大高度
    let maxBottom = currentY + cfg.noteHeight;
    measureLayouts.forEach(ml => {
      ml.notes.forEach(nl => {
        // 考虑下加点和减时线
        if (nl.lowerDotPositions.length > 0) {
          const lastDot = nl.lowerDotPositions[nl.lowerDotPositions.length - 1];
          maxBottom = Math.max(maxBottom, lastDot.y + lastDot.height + 4);
        }
        if (nl.underlines.length > 0) {
          const lastLine = nl.underlines[nl.underlines.length - 1];
          maxBottom = Math.max(maxBottom, lastLine.y + cfg.underlineThickness + 2);
        }
        if (nl.dynamicPosition) {
          maxBottom = Math.max(maxBottom, nl.dynamicPosition.y + nl.dynamicPosition.height + 2);
        }
        if (nl.lyricPositions && nl.lyricPositions.length > 0) {
          const last = nl.lyricPositions[nl.lyricPositions.length - 1];
          maxBottom = Math.max(maxBottom, last.y + last.height + 2);
        } else if (nl.lyricPosition) {
          maxBottom = Math.max(maxBottom, nl.lyricPosition.y + nl.lyricPosition.height + 2);
        }
      });
    });

    const rowHeight = maxBottom - currentY + 8;
    rows.push({ y: currentY, height: rowHeight, measures: measureLayouts });
    currentY += rowHeight + cfg.rowGap;
    measureIdx += fitCount;
  }

  return {
    width: cfg.canvasWidth,
    height: currentY + cfg.paddingVertical,
    titlePosition,
    keyPosition,
    timeSignaturePosition,
    tempoPosition,
    rows,
  };
}
