/** 音高：1-7 对应 do-si，0 为休止符 */
export type Pitch = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;

/** 八度偏移：-2 到 +2，0 为中央八度 */
export type Octave = -2 | -1 | 0 | 1 | 2;

/** 升降号 */
export type Accidental = 'sharp' | 'flat' | 'natural';

/** 升降号显示位置 */
export type AccidentalPosition = 'before' | 'after';

/** 附点数量：0=无附点，1=单附点，2=双附点 */
export type DotCount = 0 | 1 | 2;

/** 吐音类型 */
export type Articulation = 'single' | 'double' | 'triple';

/** 竹笛技巧类型 */
export type DiziTechniqueType =
  | 'zengyin'      // 赠音
  | 'dieyin'       // 叠音
  | 'liyin'        // 历音
  | 'huayin'       // 滑音
  | 'dayin'        // 打音
  | 'yinyin'       // 倚音
  | 'chanyin'      // 颤音
  | 'qizhenyin'    // 气震音
  | 'tuyin'        // 吐音
  | 'huashe'       // 花舌
  | 'xunhuan'      // 循环换气
  | 'fanyin'      // 泛音
  | 'boyin'        // 波音（上波音用顺回音符号）
  | 'dunyin';       // 顿音（倒三角▼）

/** 滑音方向 */
export type SlideDirection = 'up' | 'down';

/** 历音方向 */
export type LiyinDirection = 'up' | 'down';

/** 竹笛技巧 */
export interface DiziTechnique {
  type: DiziTechniqueType;
  /** 倚音/历音的附加音符 */
  graceNotes?: Pitch[];
  /** 倚音/历音音符的八度偏移 */
  graceOctave?: Octave;
  /** 滑音方向 */
  slideDirection?: SlideDirection;
  /** 历音方向 */
  liyinDirection?: LiyinDirection;
  /** 吐音类型 */
  articulation?: Articulation;
  /** 赠音音高 */
  giftPitch?: Pitch;
  /** 赠音八度偏移 */
  giftOctave?: Octave;
}

/** 音符 */
export interface Note {
  /** 音高 */
  pitch: Pitch;
  /** 八度偏移，默认 0 */
  octave?: Octave;
  /** 时值分数，1=四分音符，0.5=八分音符，0.25=十六分音符，2=二分音符，4=全音符 */
  duration: number;
  /** 附点数量，默认 0 */
  dot?: DotCount;
  /** 升降号 */
  accidental?: Accidental;
  /** 升降号位置，默认 before */
  accidentalPosition?: AccidentalPosition;
  /** 竹笛技巧列表 */
  techniques?: DiziTechnique[];
  /** 连音线 ID（相同 ID 的音符被连音线连接） */
  tieId?: string;
  /** 圆滑线 ID（相同 ID 的音符被圆滑线连接） */
  slurId?: string;
  /** 三连音组 ID */
  tripletId?: string;
  /** 重音标记 */
  accent?: boolean;
  /** 保持音标记 */
  tenuto?: boolean;
  /** 延长记号（自由延长） */
  fermata?: boolean;
  /** 力度突变标记 (sf/sfp/fp) */
  forceAccent?: 'sf' | 'sfp' | 'fp';
  /** 力度标记 (pp/p/mp/mf/f/ff 等)，显示在音符下方 */
  dynamic?: string;
  /** 歌词（第一行） */
  lyric?: string;
  /** 多行歌词（如歌谱多段词），每行独立数组 */
  lyrics?: string[];
}

/** 增时线（单独的时值延长线） */
export interface Dash {
  type: 'dash';
  /** 所属的时值分数 */
  duration: number;
  /** 连音线 ID */
  tieId?: string;
}

/** 小节线类型 */
export type BarlineType = 'single' | 'double' | 'end' | 'repeat-start' | 'repeat-end';

/** 反复跳跃记号 */
export interface RepeatEnding {
  /** 跳跃编号，如 1、2 */
  numbers: number[];
}

/** 小节 */
export interface Measure {
  /** 小节内的音符/增时线列表 */
  notes: (Note | Dash)[];
  /** 小节线类型（画在小节右侧），默认 single */
  barline?: BarlineType;
  /** 反复跳跃记号 */
  repeatEnding?: RepeatEnding;
  /** 渐强/渐弱标记 */
  dynamics?: { type: 'crescendo' | 'descrescendo'; endMeasureIndex?: number };
}

/** 拍号 */
export interface TimeSignature {
  /** 分子（每小节拍数） */
  numerator: number;
  /** 分母（音符类型，4=四分音符，8=八分音符） */
  denominator: number;
}

/** 力度记号 */
export type DynamicMark = 'pp' | 'p' | 'mp' | 'mf' | 'f' | 'ff';

/** 乐谱 */
export interface Score {
  /** 乐谱标题 */
  title?: string;
  /** 调号，如 "C"、"D"、"G" */
  key: string;
  /** 拍号 */
  timeSignature: TimeSignature;
  /** 速度（BPM） */
  tempo?: number;
  /** 速度文字描述 */
  tempoText?: string;
  /** 力度 */
  dynamics?: DynamicMark;
  /** 谱面力度术语（一次性） */
  dynamicsText?: Array<{ text: string; measureIndex: number; noteIndex: number }>;
  /** 前奏小节数（用括号包起） */
  introMeasureCount?: number;
  /** 小节列表 */
  measures: Measure[];
}

/** 布局相关类型 */

/** 符号位置信息 */
export interface SymbolPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** 音符布局 */
export interface NoteLayout {
  type: 'note' | 'dash';
  /** 音符数据引用 */
  data: Note | Dash;
  /** 小节索引 */
  measureIndex: number;
  /** 音符在小节内的索引 */
  noteIndex: number;
  /** 音符主体位置 */
  position: SymbolPosition;
  /** 八度上方点位置列表 */
  upperDotPositions: SymbolPosition[];
  /** 八度下方点位置列表 */
  lowerDotPositions: SymbolPosition[];
  /** 附点位置列表 */
  dotPositions: SymbolPosition[];
  /** 升降号位置 */
  accidentalPosition?: SymbolPosition;
  /** 减时线 Y 坐标和宽度列表 */
  underlines: { y: number; width: number; xOffset: number }[];
  /** 增时线位置列表（duration>1 音符的时值延长横线） */
  dashLinePositions: SymbolPosition[];
  /** 技巧符号位置列表 */
  techniquePositions: { technique: DiziTechnique; position: SymbolPosition; mainNotePos?: SymbolPosition }[];
  /** 连音线起点/终点信息 */
  tieStart?: boolean;
  tieEnd?: boolean;
  tieId?: string;
  /** 圆滑线 */
  slurStart?: boolean;
  slurEnd?: boolean;
  slurId?: string;
  /** 三连音 */
  tripletId?: string;
  tripletStart?: boolean;
  tripletEnd?: boolean;
  /** 重音位置 */
  accentPosition?: SymbolPosition;
  /** 保持音位置 */
  tenutoPosition?: SymbolPosition;
  /** 延长记号位置 */
  fermataPosition?: SymbolPosition;
  /** 顿音位置 */
  staccatoPosition?: SymbolPosition;
  /** 换气位置 */
  breathPosition?: SymbolPosition;
  /** 歌词位置（第一行） */
  lyricPosition?: SymbolPosition;
  /** 多行歌词每行位置 */
  lyricPositions?: SymbolPosition[];
  /** 力度标记位置 (pp/mp/f 等) */
  dynamicPosition?: SymbolPosition;
}

/** 小节布局 */
export interface MeasureLayout {
  /** 小节数据引用 */
  data: Measure;
  /** 小节整体位置 */
  position: SymbolPosition;
  /** 小节线位置 */
  barlinePosition?: SymbolPosition;
  /** 音符布局列表 */
  notes: NoteLayout[];
  /** 反复跳跃记号位置 */
  repeatEndingPosition?: SymbolPosition;
  /** 前奏左括号位置 */
  bracketLeft?: SymbolPosition;
  /** 前奏右括号位置 */
  bracketRight?: SymbolPosition;
}

/** 行布局 */
export interface RowLayout {
  /** 行 Y 坐标 */
  y: number;
  /** 行高度 */
  height: number;
  /** 小节布局列表 */
  measures: MeasureLayout[];
}

/** 乐谱布局 */
export interface ScoreLayout {
  /** 总宽度 */
  width: number;
  /** 总高度 */
  height: number;
  /** 标题位置 */
  titlePosition?: SymbolPosition;
  /** 调号位置 */
  keyPosition?: SymbolPosition;
  /** 拍号位置 */
  timeSignaturePosition?: SymbolPosition;
  /** 速度位置 */
  tempoPosition?: SymbolPosition;
  /** 行布局列表 */
  rows: RowLayout[];
}
