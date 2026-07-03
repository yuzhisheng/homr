import { useState, useEffect, useRef } from 'react';
import type { Score } from '../types';
import { calculateLayout, render, DEFAULT_THEME, setupCanvasDPI, DEFAULT_CONFIG } from '../engine';
import type { LayoutConfig } from '../engine';

interface ManifestEntry {
  file: string;
  title: string;
  measures: number;
}

const bwTheme = {
  ...DEFAULT_THEME,
  backgroundColor: '#ffffff',
  noteColor: '#000000',
  symbolColor: '#000000',
  dashColor: '#000000',
  dotColor: '#000000',
  underlineColor: '#000000',
  barlineColor: '#000000',
  tieColor: '#000000',
  lyricColor: '#000000',
  techniqueColor: '#000000',
  repeatDotColor: '#000000',
};

export default function TrainingViewer() {
  const [entries, setEntries] = useState<ManifestEntry[]>([]);
  const [scores, setScores] = useState<Map<string, Score>>(new Map());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/training/index.json')
      .then(r => r.json())
      .then(async (list: ManifestEntry[]) => {
        setEntries(list);
        const map = new Map<string, Score>();
        for (const e of list) {
          const r = await fetch(`/training/${e.file}`);
          map.set(e.file, await r.json());
        }
        setScores(map);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-8 text-gray-400">加载训练素材中...</div>;

  const handleDownloadAll = () => {
    const canvases = document.querySelectorAll('canvas.training-canvas');
    canvases.forEach((canvas, i) => {
      setTimeout(() => {
        (canvas as HTMLCanvasElement).toBlob(blob => {
          if (!blob) return;
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `score_${String(i + 1).padStart(3, '0')}.png`;
          a.click();
          URL.revokeObjectURL(url);
        });
      }, i * 200);
    });
  };

  return (
    <div className="p-6" style={{ background: '#ffffff', minHeight: '100vh' }}>
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-xl font-bold" style={{ color: '#111' }}>训练素材</h1>
        <span className="text-sm" style={{ color: '#666' }}>{entries.length} 个</span>
        <button onClick={handleDownloadAll}
          className="px-3 py-1 text-xs rounded bg-green-500 text-white hover:bg-green-600">下载全部 PNG</button>
      </div>
      <div className="flex flex-col gap-6 max-w-[1200px]">
        {entries.map((e, idx) => (
          <ScoreCard
            key={e.file}
            index={idx}
            entry={e}
            score={scores.get(e.file)!}
          />
        ))}
      </div>
    </div>
  );
}

function ScoreCard({ index, entry, score }: { index: number; entry: ManifestEntry; score: Score }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !score) return;
    const config: LayoutConfig = {
      ...DEFAULT_CONFIG,
      canvasWidth: 1200,
      paddingVertical: 10,
    };
    const layout = calculateLayout(score, config);
    canvasRef.current.width = layout.width;
    canvasRef.current.height = layout.height;
    const ctx = setupCanvasDPI(canvasRef.current, layout.width, layout.height);
    render(ctx, layout, score, config, bwTheme);
  }, [score]);

  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.toBlob(blob => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = entry.file.replace('.json', '.png');
      a.click();
      URL.revokeObjectURL(url);
    });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center font-bold">{index + 1}</span>
        <span className="text-sm font-medium" style={{ color: '#333' }}>{entry.title}</span>
        <span className="text-xs" style={{ color: '#999' }}>{entry.measures} 小节</span>
      </div>
      <canvas ref={canvasRef} className="training-canvas" style={{ maxWidth: '100%', border: '1px solid #e5e5e5', borderRadius: 4, background: '#fff' }} />
      <button
        onClick={handleDownload}
        className="mt-2 px-3 py-1 text-xs rounded bg-blue-500 text-white hover:bg-blue-600"
      >下载 PNG</button>
    </div>
  );
}
