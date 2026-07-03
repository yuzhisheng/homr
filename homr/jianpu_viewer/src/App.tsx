import { useState, useCallback, useRef, useEffect } from 'react';
import { Code, Sun } from 'lucide-react';
import type { Score, ScoreLayout } from './types';
import type { RenderTheme } from './engine';
import type { EditorHandle } from './components/Editor';
import { examples, moonSong } from './data/examples';
import { downloadPNG, DEFAULT_THEME, LIGHT_THEME } from './engine';
import Editor from './components/Editor';
import Preview from './components/Preview';
import Toolbar from './components/Toolbar';
import TrainingViewer from './components/TrainingViewer';

export default function App() {
  // 从 localStorage 恢复主题和示例选择
  const [isDarkTheme, setIsDarkTheme] = useState(() => {
    const saved = localStorage.getItem('jianpu-theme');
    return saved !== null ? saved === 'dark' : true;
  });
  const savedExampleKey = localStorage.getItem('jianpu-example') || 'moon';
  const savedExample = examples[savedExampleKey] || examples['moon'];
  const [jsonValue, setJsonValue] = useState(() => JSON.stringify(savedExample.data, null, 2));
  const [score, setScore] = useState<Score | null>(savedExample.data);
  const [zoom, setZoom] = useState(1);
  const [isValid, setIsValid] = useState(true);
  const [showEditor, setShowEditor] = useState(true);
  const [showTraining, setShowTraining] = useState(false);
  const [noteSpacing, setNoteSpacing] = useState(() => {
    const s = localStorage.getItem('jianpu-noteSpacing');
    return s !== null ? Number(s) : 22;
  });
  const [rowGap, setRowGap] = useState(() => {
    const s = localStorage.getItem('jianpu-rowGap');
    return s !== null ? Number(s) : 14;
  });
  const canvasLayoutRef = useRef<ScoreLayout | null>(null);
  const editorRef = useRef<EditorHandle>(null);
  const noteLineMapRef = useRef<Map<string, number>>(new Map());

  const theme: RenderTheme = isDarkTheme ? DEFAULT_THEME : LIGHT_THEME;

  // 初始构建行号映射
  useEffect(() => {
    buildNoteLineMap(jsonValue);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 从 JSON 字符串构建音符到行号的映射（brace-depth 感知）
  const buildNoteLineMap = useCallback((jsonStr: string) => {
    const lines = jsonStr.split('\n');
    const map = new Map<string, number>();
    let measureIdx = -1;
    let noteIdx = 0;
    let state: 'idle' | 'in-measures' | 'in-measure' | 'in-notes' = 'idle';
    let braceDepth = 0;

    for (let i = 0; i < lines.length; i++) {
      const raw = lines[i];
      const trimmed = raw.trim();
      // JSON.stringify 可能产生末尾逗号：},  ],  去掉以便匹配
      const clean = trimmed.replace(/,$/, '');

      if (clean === '"measures": [') {
        state = 'in-measures';
        continue;
      }

      if (state === 'in-measures') {
        if (clean === '{') {
          measureIdx++;
          noteIdx = 0;
          state = 'in-measure';
          continue;
        }
        if (clean === ']') {
          state = 'idle';
          continue;
        }
      }

      if (state === 'in-measure') {
        if (clean.endsWith('"notes": [')) {
          state = 'in-notes';
          braceDepth = 0;
          continue;
        }
        if (clean === '}') {
          state = 'in-measures';
          continue;
        }
      }

      if (state === 'in-notes') {
        if (clean === '{') {
          if (braceDepth === 0) {
            map.set(`${measureIdx}:${noteIdx}`, i);
            noteIdx++;
          }
          braceDepth++;
          continue;
        }
        if (clean === '}') {
          braceDepth--;
          continue;
        }
        if (clean === ']' && braceDepth === 0) {
          state = 'in-measure';
          continue;
        }
      }
    }
    noteLineMapRef.current = map;
  }, []);

  const handleJsonChange = useCallback((value: string, parsedScore: Score | null) => {
    setJsonValue(value);
    setScore(parsedScore);
    setIsValid(parsedScore !== null);
    buildNoteLineMap(value);
  }, [buildNoteLineMap]);

  const handleExampleSelect = useCallback((key: string) => {
    const example = examples[key];
    if (example) {
      const json = JSON.stringify(example.data, null, 2);
      setJsonValue(json);
      setScore(example.data);
      setIsValid(true);
      buildNoteLineMap(json);
      localStorage.setItem('jianpu-example', key);
    }
  }, [buildNoteLineMap]);

  const handleZoomIn = useCallback(() => {
    setZoom(z => Math.min(z + 0.25, 3));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(z => Math.max(z - 0.25, 0.25));
  }, []);

  const handleExport = useCallback(() => {
    const canvas = document.querySelector('canvas');
    if (canvas && canvasLayoutRef.current) {
      const title = score?.title || 'jianpu-score';
      downloadPNG(canvas, `${title}.png`, 2);
    }
  }, [score]);

  const handleLayoutChange = useCallback((layout: ScoreLayout) => {
    canvasLayoutRef.current = layout;
  }, []);

  const handleToggleEditor = useCallback(() => {
    setShowEditor(v => !v);
  }, []);

  const handleToggleTheme = useCallback(() => {
    setIsDarkTheme(v => {
      const next = !v;
      localStorage.setItem('jianpu-theme', next ? 'dark' : 'light');
      return next;
    });
  }, []);

  const handleNoteSpacingChange = useCallback((v: number) => {
    setNoteSpacing(v);
    localStorage.setItem('jianpu-noteSpacing', String(v));
  }, []);

  const handleToggleTraining = useCallback(() => {
    setShowTraining(v => !v);
  }, []);

  const handleRowGapChange = useCallback((v: number) => {
    setRowGap(v);
    localStorage.setItem('jianpu-rowGap', String(v));
  }, []);

  const handleNoteClick = useCallback((measureIndex: number, noteIndex: number) => {
    const line = noteLineMapRef.current.get(`${measureIndex}:${noteIndex}`);
    if (line !== undefined) {
      // Monaco 使用 1-based 行号
      editorRef.current?.revealLine(line + 1);
    }
  }, []);

  const editorBg = isDarkTheme ? '#252526' : '#ffffff';
  const editorBorder = isDarkTheme ? 'border-gray-800' : 'border-gray-200';
  const editorHeaderBg = isDarkTheme ? 'bg-dark-900' : 'bg-gray-100';
  const editorHeaderBorder = isDarkTheme ? 'border-gray-800' : 'border-gray-200';

  if (showTraining) {
    return (
      <div className="h-screen w-screen flex flex-col overflow-hidden" style={{backgroundColor: '#f5f5f5'}}>
        <div className="h-10 flex items-center px-4 bg-white border-b shadow-sm gap-3">
          <button onClick={handleToggleTraining}
            className="text-xs px-3 py-1 rounded bg-gray-200 hover:bg-gray-300">返回编辑器</button>
        </div>
        <div className="flex-1 overflow-auto">
          <TrainingViewer />
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden transition-colors duration-200" style={{backgroundColor: isDarkTheme ? '#1e1e1e' : '#f5f5f5'}}>
      <Toolbar
        onExampleSelect={handleExampleSelect}
        onExport={handleExport}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        zoom={zoom}
        isValid={isValid}
        showEditor={showEditor}
        onToggleEditor={handleToggleEditor}
        isDarkTheme={isDarkTheme}
        onToggleTheme={handleToggleTheme}
        noteSpacing={noteSpacing}
        rowGap={rowGap}
        onNoteSpacingChange={handleNoteSpacingChange}
        onRowGapChange={handleRowGapChange}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* 左侧编辑器 */}
        {showEditor && (
          <div className={`w-[40%] min-w-[300px] border-r relative transition-colors duration-200 ${editorBorder}`} style={{backgroundColor: editorBg}}>
            <div className={`absolute top-0 left-0 right-0 h-7 flex items-center px-3 z-10 border-b ${editorHeaderBg} ${editorHeaderBorder}`}>
              <span className="text-[10px] font-medium uppercase tracking-wider" style={{color: isDarkTheme ? '#6b7280' : '#9ca3af'}}>JSON Editor</span>
              <div className="ml-auto flex items-center gap-1.5">
                <div className={`w-1.5 h-1.5 rounded-full ${isValid ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-[10px]" style={{color: isDarkTheme ? '#6b7280' : '#9ca3af'}}>{isValid ? '有效' : '语法错误'}</span>
              </div>
            </div>
            <div className="pt-7 h-full">
              <Editor ref={editorRef} value={jsonValue} onChange={handleJsonChange} isDarkTheme={isDarkTheme} />
            </div>
          </div>
        )}

        {/* 右侧预览 */}
        <div className="flex-1 relative">
          <div className={`absolute top-0 left-0 right-0 h-7 flex items-center px-3 z-10 border-b ${editorHeaderBg} ${editorHeaderBorder}`}>
            <span className="text-[10px] font-medium uppercase tracking-wider" style={{color: isDarkTheme ? '#6b7280' : '#9ca3af'}}>Preview</span>
            <button onClick={handleToggleTraining} className="mx-2 text-[10px] px-2 py-0.5 rounded bg-blue-500 text-white hover:bg-blue-600">训练素材</button>
            <span className="ml-auto text-[10px]" style={{color: isDarkTheme ? '#4b5563' : '#d1d5db'}}>{Math.round(zoom * 100)}%</span>
          </div>
          <div className="pt-7 h-full">
            <Preview score={score} zoom={zoom} theme={theme} onLayoutChange={handleLayoutChange} onNoteClick={handleNoteClick} noteSpacing={noteSpacing} rowGap={rowGap} />
          </div>
        </div>
      </div>
    </div>
  );
}
