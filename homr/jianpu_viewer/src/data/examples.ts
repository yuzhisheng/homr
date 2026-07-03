import type { Score } from '../types';

/** 茉莉花 - 基础简谱示例 */
export const jasmineFlower: Score = {
  title: '茉莉花',
  key: 'G',
  timeSignature: { numerator: 2, denominator: 4 },
  tempo: 72,
  tempoText: 'Andante',
  measures: [
    {
      notes: [
        { pitch: 3, duration: 1, lyric: '好' },
        { pitch: 5, duration: 1, lyric: '一' },
        { pitch: 6, duration: 1, lyric: '朵' },
        { pitch: 1, octave: 1, duration: 1, lyric: '茉' },
      ],
    },
    {
      notes: [
        { pitch: 6, duration: 1, lyric: '莉' },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 0.5 },
        { pitch: 5, duration: 1, techniques: [{ type: 'huayin', slideDirection: 'up' }], lyric: '花' },
        { pitch: 3, duration: 1 },
      ],
    },
    {
      notes: [
        { pitch: 2, duration: 0.5, lyric: '好' },
        { pitch: 3, duration: 0.5, lyric: '一' },
        { pitch: 5, duration: 1, lyric: '朵' },
        { pitch: 3, duration: 1, lyric: '茉' },
      ],
    },
    {
      notes: [
        { pitch: 2, duration: 1, lyric: '莉' },
        { pitch: 1, duration: 0.5 },
        { pitch: 6, octave: -1, duration: 0.5 },
        { pitch: 1, duration: 1 },
      ],
      barline: 'end',
    },
  ],
};

/** 姑苏行片段 - 竹笛技巧示例 */
export const guSuXing: Score = {
  title: '姑苏行（片段）',
  key: 'D',
  timeSignature: { numerator: 4, denominator: 4 },
  tempo: 60,
  measures: [
    {
      notes: [
        { pitch: 5, duration: 0.5, techniques: [{ type: 'liyin', liyinDirection: 'down', graceNotes: [6], graceOctave: 1 }] },
        { pitch: 6, duration: 0.5 },
        { pitch: 1, octave: 1, duration: 1, techniques: [{ type: 'dayin' }] },
        { pitch: 6, duration: 0.5 },
        { pitch: 5, duration: 0.5, techniques: [{ type: 'huayin', slideDirection: 'down' }] },
        { pitch: 3, duration: 1 },
      ],
    },
    {
      notes: [
        { pitch: 5, duration: 0.5, techniques: [{ type: 'yinyin', graceNotes: [6], graceOctave: 1 }, { type: 'chanyin' }] },
        { pitch: 3, duration: 0.5 },
        { pitch: 2, duration: 1, techniques: [{ type: 'chanyin' }] },
        { pitch: 3, duration: 0.5 },
        { pitch: 5, duration: 0.5 },
        { pitch: 6, duration: 1 },
      ],
    },
    {
      notes: [
        { pitch: 1, octave: 1, duration: 1, techniques: [{ type: 'tuyin', articulation: 'single' }] },
        { pitch: 6, duration: 1, techniques: [{ type: 'tuyin', articulation: 'single' }] },
        { pitch: 5, duration: 1, techniques: [{ type: 'huashe' }] },
        { pitch: 3, duration: 1, fermata: true },
      ],
    },
    {
      notes: [
        { pitch: 5, duration: 0.5, techniques: [{ type: 'zengyin', giftPitch: 6 }] },
        { pitch: 3, duration: 0.5 },
        { pitch: 2, duration: 1, techniques: [{ type: 'liyin', liyinDirection: 'up', graceNotes: [1], graceOctave: 1 }] },
        { pitch: 1, duration: 2, dot: 1 },
      ],
    },
    // 第5-7小节，凑成两行
    {
      notes: [
        { pitch: 6, duration: 0.5, techniques: [{ type: 'dieyin' }] },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 1, techniques: [{ type: 'qizhenyin' }] },
        { pitch: 5, duration: 0.5, techniques: [{ type: 'huayin', slideDirection: 'up' }] },
        { pitch: 6, duration: 1 },
      ],
    },
    {
      notes: [
        { pitch: 1, octave: 1, duration: 1, techniques: [{ type: 'tuyin', articulation: 'double' }] },
        { pitch: 6, duration: 0.5 },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 1, techniques: [{ type: 'xunhuan' }] },
      ],
    },
    {
      notes: [
        { pitch: 2, duration: 1, techniques: [{ type: 'fanyin' }] },
        { pitch: 1, duration: 1 },
        { pitch: 6, octave: -1, duration: 1 },
        { pitch: 1, duration: 1 },
      ],
      barline: 'end',
    },
  ],
};

/** 综合技巧示例 - 展示所有符号 */
export const techniqueDemo: Score = {
  title: '竹笛技巧演示',
  key: 'C',
  timeSignature: { numerator: 4, denominator: 4 },
  tempo: 80,
  measures: [
    {
      notes: [
        { pitch: 1, duration: 0.5, techniques: [{ type: 'tuyin', articulation: 'single' }] },
        { pitch: 2, duration: 0.5, techniques: [{ type: 'tuyin', articulation: 'single' }] },
        { pitch: 3, duration: 0.5, techniques: [{ type: 'tuyin', articulation: 'double' }] },
        { pitch: 5, duration: 0.5, techniques: [{ type: 'tuyin', articulation: 'double' }] },
        { pitch: 6, duration: 0.5, techniques: [{ type: 'tuyin', articulation: 'triple' }] },
        { pitch: 5, duration: 0.5, techniques: [{ type: 'tuyin', articulation: 'triple' }] },
        { pitch: 3, duration: 0.5, techniques: [{ type: 'dieyin' }] },
        { pitch: 2, duration: 0.5, techniques: [{ type: 'dayin' }] },
      ],
    },
    {
      notes: [
        { pitch: 1, duration: 1, techniques: [{ type: 'chanyin' }] },
        { pitch: 2, duration: 1, techniques: [{ type: 'huashe' }] },
        { pitch: 3, duration: 1, techniques: [{ type: 'qizhenyin' }] },
        { pitch: 5, duration: 1, techniques: [{ type: 'fanyin' }] },
      ],
    },
    {
      notes: [
        { pitch: 6, duration: 1, techniques: [{ type: 'huayin', slideDirection: 'up' }] },
        { pitch: 1, octave: 1, duration: 1, techniques: [{ type: 'huayin', slideDirection: 'down' }] },
        { pitch: 6, duration: 0.5, techniques: [{ type: 'liyin', liyinDirection: 'up', graceNotes: [5], graceOctave: 1 }] },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 1, techniques: [{ type: 'zengyin', giftPitch: 5 }] },
      ],
    },
    {
      notes: [
        { pitch: 5, duration: 0.5, techniques: [{ type: 'yinyin', graceNotes: [6], graceOctave: 1 }] },
        { pitch: 3, duration: 0.5 },
        { pitch: 2, duration: 1, techniques: [{ type: 'xunhuan' }] },
        { pitch: 1, duration: 2 },
      ],
      barline: 'end',
    },
  ],
};

/** 反复记号示例 */
export const repeatDemo: Score = {
  title: '反复记号演示',
  key: 'G',
  timeSignature: { numerator: 2, denominator: 4 },
  tempo: 100,
  measures: [
    {
      notes: [
        { pitch: 1, duration: 1 },
        { pitch: 2, duration: 1 },
        { pitch: 3, duration: 1 },
        { pitch: 5, duration: 1 },
      ],
      barline: 'repeat-start',
    },
    {
      notes: [
        { pitch: 6, duration: 1 },
        { pitch: 5, duration: 1 },
        { pitch: 3, duration: 1 },
        { pitch: 2, duration: 1 },
      ],
      repeatEnding: { numbers: [1] },
    },
    {
      notes: [
        { pitch: 3, duration: 1 },
        { pitch: 5, duration: 1 },
        { pitch: 2, duration: 1 },
        { pitch: 1, duration: 1 },
      ],
      repeatEnding: { numbers: [2] },
      barline: 'repeat-end',
    },
  ],
};

/** 升降号与附点示例 */
export const accidentalDemo: Score = {
  title: '升降号与附点演示',
  key: 'D',
  timeSignature: { numerator: 3, denominator: 4 },
  tempo: 90,
  measures: [
    {
      notes: [
        { pitch: 1, duration: 1, accidental: 'sharp' },
        { pitch: 2, duration: 1, dot: 1 },
        { pitch: 4, duration: 0.5 },
        { pitch: 5, duration: 1, accidental: 'flat' },
        { pitch: 6, duration: 0.5, dot: 1 },
        { pitch: 5, duration: 0.25 },
      ],
    },
    {
      notes: [
        { pitch: 3, duration: 2, dot: 1 },
        { pitch: 2, duration: 1, accidental: 'natural' },
      ],
      barline: 'end',
    },
  ],
};

/** 连音与圆滑线示例 */
export const tieDemo: Score = {
  title: '连音与圆滑线演示',
  key: 'C',
  timeSignature: { numerator: 4, denominator: 4 },
  tempo: 80,
  measures: [
    {
      notes: [
        { pitch: 1, duration: 0.5, tieId: 't1' },
        { pitch: 1, duration: 0.5, tieId: 't1' },
        { pitch: 3, duration: 0.5, slurId: 's1' },
        { pitch: 5, duration: 0.5, slurId: 's1' },
      ],
    },
    {
      notes: [
        { pitch: 6, duration: 0.5 },
        { pitch: 5, duration: 0.5, tieId: 't2' },
        { pitch: 5, duration: 0.5, tieId: 't2' },
        { pitch: 2, duration: 1 },
      ],
      barline: 'end',
    },
  ],
};

/** 综合练习曲 - 带反复记号与小房子 */
export const comprehensiveDemo: Score = {
  title: '综合练习曲',
  key: 'C',
  timeSignature: { numerator: 4, denominator: 4 },
  tempo: 90,
  measures: [
    {
      notes: [
        { pitch: 1, duration: 0.5, staccato: true },
        { pitch: 2, duration: 0.5 },
        { pitch: 3, duration: 0.5, breathMark: true },
        { pitch: 5, duration: 0.5 },
        { pitch: 6, duration: 0.5 },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 0.5 },
        { pitch: 2, duration: 0.5 },
      ],
    },
    {
      notes: [
        { pitch: 1, duration: 0.5, techniques: [{ type: 'dieyin' }] },
        { pitch: 2, duration: 0.5 },
        { pitch: 3, duration: 0.5, dot: 1 },
        { pitch: 5, duration: 0.25 },
        { pitch: 3, duration: 0.25 },
        { pitch: 2, duration: 1 },
      ],
      barline: 'repeat-start',
    },
    {
      notes: [
        { pitch: 3, duration: 0.5, techniques: [{ type: 'dayin' }] },
        { pitch: 5, duration: 0.5 },
        { pitch: 6, duration: 0.5 },
        { pitch: 1, octave: 1, duration: 0.5 },
        { pitch: 6, duration: 0.5 },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 1 },
      ],
      repeatEnding: { numbers: [1] },
    },
    {
      notes: [
        { pitch: 5, duration: 0.5, techniques: [{ type: 'zengyin', giftPitch: 6 }] },
        { pitch: 3, duration: 0.5 },
        { pitch: 2, duration: 0.5 },
        { pitch: 1, duration: 0.5, techniques: [{ type: 'chanyin' }] },
        { pitch: 6, octave: -1, duration: 0.5 },
        { pitch: 1, duration: 0.5 },
        { pitch: 2, duration: 0.5 },
        { pitch: 3, duration: 0.5 },
      ],
      repeatEnding: { numbers: [2] },
      barline: 'repeat-end',
    },
    {
      notes: [
        { pitch: 5, duration: 0.5, techniques: [{ type: 'huayin', slideDirection: 'up' }] },
        { pitch: 6, duration: 0.5 },
        { pitch: 1, octave: 1, duration: 1, dot: 1 },
        { pitch: 6, duration: 0.5 },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 1 },
      ],
    },
    {
      notes: [
        { pitch: 2, duration: 1, techniques: [{ type: 'liyin', liyinDirection: 'up', graceNotes: [1] }] },
        { pitch: 3, duration: 0.5 },
        { pitch: 5, duration: 0.5 },
        { pitch: 6, duration: 1 },
        { pitch: 1, octave: 1, duration: 1 },
      ],
    },
    {
      notes: [
        { pitch: 6, duration: 0.5 },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 1, techniques: [{ type: 'qizhenyin' }] },
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 0.5 },
        { pitch: 1, duration: 1, fermata: true },
      ],
      barline: 'end',
    },
  ],
};

/** 月亮代表我的心 — 经典流行歌曲 */
export const moonSong: Score = {
  title: '月亮代表我的心',
  key: 'C',
  timeSignature: { numerator: 4, denominator: 4 },
  tempo: 76,
  introMeasureCount: 2,
  measures: [
    // ===== 前奏 =====
    {
      notes: [
        { pitch: 5, duration: 0.5 },
        { pitch: 3, duration: 0.5 },
        { pitch: 2, duration: 0.5 },
        { pitch: 1, duration: 0.5 },
        { pitch: 5, duration: 1 },
        { pitch: 3, duration: 0.5 },
        { pitch: 0, duration: 0.5 },
      ],
    },
    {
      notes: [
        { pitch: 6, octave: -1, duration: 1 },
        { pitch: 1, duration: 1 },
        { pitch: 2, duration: 0.5 },
        { pitch: 3, duration: 0.5, techniques: [{ type: 'boyin' }] },
        { pitch: 5, duration: 0.5 },
        { pitch: 6, duration: 0.5 },
      ],
    },

    // ===== A段：主歌 =====
    // 你问 我爱你 有多深
    {
      notes: [
        { pitch: 5, duration: 0.5, lyric: '你' },
        { pitch: 3, duration: 0.5, lyric: '问' },
        { pitch: 2, duration: 0.25, lyric: '我' },
        { pitch: 1, duration: 0.25, lyric: '爱', slurId: 's1' },
        { pitch: 6, octave: -1, duration: 0.5, lyric: '你', slurId: 's1' },
        { pitch: 6, octave: -1, duration: 0.5 },
        { pitch: 3, duration: 0.5, lyric: '有' },
        { pitch: 2, duration: 0.5 },
        { pitch: 1, duration: 0.5, lyric: '多' },
      ],
    },
    {
      notes: [
        { pitch: 6, octave: -1, duration: 1, dot: 1, lyric: '深' },
        { pitch: 6, octave: -1, duration: 0.5 },
        { pitch: 1, duration: 0.5 },
        { pitch: 2, duration: 0.5, lyric: '我' },
        { pitch: 3, duration: 0.5, lyric: '爱' },
        { type: 'dash', duration: 0.5 },
      ],
    },
    // 我爱你有几分
    {
      notes: [
        { pitch: 6, duration: 0.5, lyric: '我' },
        { pitch: 5, duration: 0.5, lyric: '爱', slurId: 's2' },
        { pitch: 6, duration: 1, lyric: '你', slurId: 's2' },
        { pitch: 5, duration: 0.5, lyric: '有' },
        { pitch: 3, duration: 0.5, lyric: '几', slurId: 's3' },
        { pitch: 2, duration: 1, lyric: '分', slurId: 's3' },
      ],
    },
    // 我的情也真  我的爱
    {
      notes: [
        { pitch: 1, duration: 0.5, lyric: '我' },
        { pitch: 2, duration: 0.25, lyric: '的' },
        { pitch: 3, duration: 0.25 },
        { pitch: 5, duration: 0.5, lyric: '情', techniques: [{ type: 'boyin' }] },
        { pitch: 6, duration: 0.5, lyric: '也' },
        { pitch: 5, duration: 1, lyric: '真' },
        { pitch: 3, duration: 0.5, lyric: '我' },
        { pitch: 2, duration: 0.5, lyric: '的' },
      ],
    },
    {
      notes: [
        { pitch: 1, duration: 0.5, lyric: '爱' },
        { pitch: 6, octave: -1, duration: 0.5, lyric: '也' },
        { pitch: 1, duration: 1, lyric: '真' },
        { pitch: 3, duration: 0.5 },
        { pitch: 3, duration: 0.5 },
        { pitch: 5, duration: 0.5 },
        { pitch: 6, duration: 0.5 },
      ],
    },
    // 月亮代表我的心
    {
      notes: [
        { pitch: 1, octave: 1, duration: 0.5, lyric: '月', slurId: 's4' },
        { pitch: 6, duration: 0.5, lyric: '亮', slurId: 's4' },
        { pitch: 5, duration: 0.5, lyric: '代', slurId: 's5' },
        { pitch: 3, duration: 0.5, lyric: '表', slurId: 's5' },
        { pitch: 5, duration: 0.5, lyric: '我', slurId: 's6' },
        { pitch: 3, duration: 0.5, lyric: '的', slurId: 's6' },
        { pitch: 2, duration: 0.5, lyric: '心' },
        { pitch: 1, duration: 0.5 },
      ],
    },
    {
      notes: [
        { pitch: 1, duration: 1 },
        { pitch: 5, duration: 1 },
        { pitch: 3, duration: 0.5 },
        { pitch: 2, duration: 1, lyric: '—' },
        { pitch: 0, duration: 0.5 },
      ],
    },

    // ===== B段：过渡 =====
    // 轻轻地一个吻
    {
      notes: [
        { pitch: 6, octave: -1, duration: 0.5, lyric: '轻' },
        { pitch: 1, duration: 0.25, lyric: '轻' },
        { pitch: 2, duration: 0.25 },
        { pitch: 3, duration: 0.5, lyric: '的' },
        { pitch: 5, duration: 0.5, lyric: '一' },
        { pitch: 6, duration: 1, lyric: '个' },
        { pitch: 1, octave: 1, duration: 1, lyric: '吻' },
      ],
    },
    // 已经打动我的心
    {
      notes: [
        { pitch: 6, duration: 0.5, lyric: '已' },
        { pitch: 5, duration: 0.5, lyric: '经', slurId: 's7' },
        { pitch: 3, duration: 0.5, lyric: '打', slurId: 's7' },
        { pitch: 2, duration: 0.5, lyric: '动' },
        { pitch: 1, duration: 0.5, lyric: '我' },
        { pitch: 2, duration: 0.25, lyric: '的' },
        { pitch: 3, duration: 0.25 },
        { pitch: 5, duration: 1, lyric: '心' },
      ],
    },
    // 深深的一段情
    {
      notes: [
        { pitch: 6, duration: 0.5, lyric: '深' },
        { pitch: 5, duration: 0.5, lyric: '深', slurId: 's8' },
        { pitch: 3, duration: 0.5, lyric: '的', slurId: 's8' },
        { pitch: 2, duration: 0.5, lyric: '一' },
        { pitch: 1, duration: 0.5, lyric: '段' },
        { pitch: 6, octave: -1, duration: 0.5, lyric: '情' },
        { pitch: 1, duration: 0.5 },
        { pitch: 2, duration: 0.5 },
      ],
    },
    // 教我思念到如今
    {
      notes: [
        { pitch: 3, duration: 0.5, lyric: '教' },
        { pitch: 5, duration: 0.5, lyric: '我', slurId: 's9' },
        { pitch: 6, duration: 0.5, lyric: '思', slurId: 's9' },
        { pitch: 5, duration: 0.5, lyric: '念' },
        { pitch: 6, duration: 0.5, lyric: '到', slurId: 's10' },
        { pitch: 5, duration: 0.5, lyric: '如', slurId: 's10' },
        { pitch: 3, duration: 0.5, lyric: '今' },
        { pitch: 2, duration: 0.5 },
      ],
    },
    {
      notes: [
        { pitch: 2, duration: 1 },
        { pitch: 3, duration: 1 },
        { pitch: 5, duration: 0.5 },
        { pitch: 6, duration: 0.5, lyric: '月' },
        { pitch: 1, octave: 1, duration: 1, lyric: '亮' },
      ],
    },

    // ===== C段：副歌（带反复和小房子） =====
    {
      notes: [
        { pitch: 6, duration: 0.5, lyric: '代', slurId: 's11' },
        { pitch: 5, duration: 0.5, lyric: '表', slurId: 's11' },
        { pitch: 3, duration: 0.5, lyric: '我', slurId: 's12' },
        { pitch: 2, duration: 0.5, lyric: '的', slurId: 's12' },
        { pitch: 1, duration: 0.5, lyric: '心' },
        { pitch: 3, duration: 0.5 },
        { pitch: 5, duration: 0.5, lyric: '永' },
        { pitch: 6, duration: 0.5, lyric: '远' },
      ],
      barline: 'repeat-start',
    },
    // 小房子 1.
    {
      notes: [
        { pitch: 1, octave: 1, duration: 0.5, lyric: '不' },
        { pitch: 6, duration: 0.5, lyric: '变' },
        { pitch: 5, duration: 0.5, lyric: '的' },
        { pitch: 3, duration: 0.25 },
        { pitch: 2, duration: 0.25 },
        { pitch: 1, duration: 2 },
      ],
      repeatEnding: { numbers: [1] },
      barline: 'double',
    },
    // 衔接段（分隔两个小房子）
    {
      notes: [
        { pitch: 5, duration: 1, lyric: '你' },
        { pitch: 3, duration: 1, lyric: '的' },
        { pitch: 2, duration: 0.5 },
        { pitch: 1, duration: 1.5, lyric: '心' },
      ],
      barline: 'double',
    },
    // 小房子 2.
    {
      notes: [
        { pitch: 1, octave: 1, duration: 0.5, lyric: '不' },
        { pitch: 6, duration: 0.5, lyric: '变' },
        { pitch: 5, duration: 0.5, lyric: '的' },
        { pitch: 3, duration: 0.25 },
        { pitch: 2, duration: 0.25 },
        { pitch: 1, duration: 2 },
      ],
      repeatEnding: { numbers: [2] },
      barline: 'end',
    },
  ],
};

export const examples: Record<string, { name: string; data: Score }> = {
  jasmine: { name: '茉莉花', data: jasmineFlower },
  gusu: { name: '姑苏行（片段）', data: guSuXing },
  technique: { name: '竹笛技巧演示', data: techniqueDemo },
  tie: { name: '连音与圆滑线', data: tieDemo },
  repeat: { name: '反复记号演示', data: repeatDemo },
  accidental: { name: '升降号与附点', data: accidentalDemo },
  comprehensive: { name: '综合练习曲', data: comprehensiveDemo },
  moon: { name: '月亮代表我的心', data: moonSong },
};
