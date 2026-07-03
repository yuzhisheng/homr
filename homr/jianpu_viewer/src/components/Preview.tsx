import { useRef, useEffect, useCallback, useState } from 'react';
import type { Score, ScoreLayout } from '../types';
import { calculateLayout, DEFAULT_CONFIG, render, DEFAULT_THEME, setupCanvasDPI } from '../engine';
import type { LayoutConfig, RenderTheme } from '../engine';


interface PreviewProps {
  score: Score | null;
  zoom: number;
  theme: RenderTheme;
  onLayoutChange?: (layout: ScoreLayout) => void;
  onNoteClick?: (measureIndex: number, noteIndex: number) => void;
  noteSpacing?: number;
  rowGap?: number;
}

export default function Preview({ score, zoom, theme, onLayoutChange, onNoteClick, noteSpacing, rowGap }: PreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [canvasKey, setCanvasKey] = useState(0);
  const layoutRef = useRef<ScoreLayout | null>(null);

  const renderScore = useCallback(() => {
    if (!canvasRef.current || !score) return;

    const config: LayoutConfig = { ...DEFAULT_CONFIG, noteWidth: noteSpacing ?? DEFAULT_CONFIG.noteWidth, rowGap: rowGap ?? DEFAULT_CONFIG.rowGap };
    const layout = calculateLayout(score, config);
    layoutRef.current = layout;

    const ctx = setupCanvasDPI(canvasRef.current, layout.width, layout.height);
    render(ctx, layout, score, config, theme);

    onLayoutChange?.(layout);
  }, [score, theme, onLayoutChange, noteSpacing, rowGap]);

  useEffect(() => {
    if (score) {
      setCanvasKey(k => k + 1);
    }
  }, [score, noteSpacing, rowGap]);

  useEffect(() => {
    renderScore();
  }, [renderScore, canvasKey]);

  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !layoutRef.current || !onNoteClick) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    // 画布 CSS 尺寸 = 逻辑尺寸，ctx 已通过 ctx.scale(dpr) 处理
    // CSS transform: scale(${zoom}) 放大显示，点击坐标需除以 zoom 回到逻辑坐标
    const clickX = (e.clientX - rect.left) / zoom;
    const clickY = (e.clientY - rect.top) / zoom;

    const layout = layoutRef.current;

    // 遍历所有行/小节/音符检测命中
    for (const row of layout.rows) {
      for (const measure of row.measures) {
        for (const note of measure.notes) {
          const pos = note.position;
          if (
            clickX >= pos.x && clickX <= pos.x + pos.width &&
            clickY >= pos.y && clickY <= pos.y + pos.height
          ) {
            onNoteClick(note.measureIndex, note.noteIndex);
            return;
          }

          // 也检测技巧符号区域（倚音等）
          for (const tp of note.techniquePositions) {
            const tpPos = tp.position;
            if (
              clickX >= tpPos.x && clickX <= tpPos.x + tpPos.width &&
              clickY >= tpPos.y && clickY <= tpPos.y + tpPos.height
            ) {
              onNoteClick(note.measureIndex, note.noteIndex);
              return;
            }
          }
        }
      }
    }
  }, [zoom, onNoteClick]);

  const isDark = theme.backgroundColor === '#1e1e1e';

  return (
    <div className="h-full w-full overflow-auto flex items-start justify-center p-6 transition-colors duration-200" style={{backgroundColor: isDark ? '#1e1e1e' : '#f5f5f5'}}>
      {!score ? (
        <div className="flex items-center justify-center h-full w-full">
          <div className="flex flex-col items-center" style={{color: isDark ? '#6b7280' : '#9ca3af'}}>
            <div className="text-5xl mb-4">♫</div>
            <p className="text-lg">在左侧编辑 JSON 即可预览简谱</p>
            <p className="text-sm mt-2" style={{color: isDark ? '#4b5563' : '#d1d5db'}}>或选择一个示例乐谱开始</p>
          </div>
        </div>
      ) : (
        <div style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }} className="transition-transform duration-200">
          <canvas key={canvasKey} ref={canvasRef} className="shadow-lg rounded-sm cursor-pointer" onClick={handleCanvasClick} />
        </div>
      )}
    </div>
  );
}
