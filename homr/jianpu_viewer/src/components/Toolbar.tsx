import { Download, ZoomIn, ZoomOut, FileMusic, Code, Sun, Moon } from 'lucide-react';
import { examples } from '../data/examples';

interface ToolbarProps {
  onExampleSelect: (key: string) => void;
  onExport: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  zoom: number;
  isValid: boolean;
  showEditor: boolean;
  onToggleEditor: () => void;
  isDarkTheme: boolean;
  onToggleTheme: () => void;
  noteSpacing: number;
  rowGap: number;
  onNoteSpacingChange: (v: number) => void;
  onRowGapChange: (v: number) => void;
}

export default function Toolbar({ onExampleSelect, onExport, onZoomIn, onZoomOut, zoom, isValid, showEditor, onToggleEditor, isDarkTheme, onToggleTheme, noteSpacing, rowGap, onNoteSpacingChange, onRowGapChange }: ToolbarProps) {
  const bg = isDarkTheme ? 'bg-dark-900' : 'bg-white';
  const border = isDarkTheme ? 'border-gray-800' : 'border-gray-200';
  const text = isDarkTheme ? 'text-gray-200' : 'text-gray-800';
  const subText = isDarkTheme ? 'text-gray-500' : 'text-gray-400';
  const selectBg = isDarkTheme ? 'bg-gray-800' : 'bg-gray-100';
  const selectText = isDarkTheme ? 'text-gray-300' : 'text-gray-700';
  const selectBorder = isDarkTheme ? 'border-gray-700' : 'border-gray-300';
  const btnBorder = isDarkTheme ? 'border-gray-700' : 'border-gray-300';

  return (
    <div className={`h-12 flex items-center justify-between px-4 border-b shadow-lg transition-colors duration-200 ${bg} ${border}`}>
      {/* 左侧标题 */}
      <div className="flex items-center gap-3">
        <FileMusic className={`w-5 h-5 ${isDarkTheme ? 'text-primary-400' : 'text-primary-600'}`} />
        <h1 className={`text-sm font-semibold tracking-wide ${text}`}>简谱渲染器</h1>
        <span className={`text-[10px] px-2 py-0.5 rounded-full ${isDarkTheme ? 'text-gray-500 bg-gray-800' : 'text-gray-400 bg-gray-200'}`}>v1.0</span>
      </div>

      {/* 右侧操作 */}
      <div className="flex items-center gap-2">
        {/* 主题切换 */}
        <button
          className={`flex items-center gap-1.5 text-xs rounded-md px-2.5 py-1.5 font-medium transition-all ${isDarkTheme ? 'text-gray-400 bg-gray-800 border border-gray-700 hover:border-gray-500' : 'text-gray-600 bg-gray-100 border border-gray-300 hover:border-gray-400'}`}
          onClick={onToggleTheme}
          title={isDarkTheme ? '切换为白底主题' : '切换为暗色主题'}
        >
          {isDarkTheme ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
        </button>

        {/* 编辑器切换 */}
        <button
          className={`flex items-center gap-1.5 text-xs rounded-md px-2.5 py-1.5 font-medium transition-all ${
            showEditor
              ? isDarkTheme
                ? 'bg-primary-500/20 text-primary-400 border border-primary-500/40'
                : 'bg-primary-500/10 text-primary-600 border border-primary-500/30'
              : `${isDarkTheme ? 'text-gray-400 bg-gray-800 border border-gray-700 hover:border-gray-500' : 'text-gray-600 bg-gray-100 border border-gray-300 hover:border-gray-400'}`
          }`}
          onClick={onToggleEditor}
          title={showEditor ? '隐藏编辑器' : '显示编辑器'}
        >
          <Code className="w-3.5 h-3.5" />
        </button>

        {/* 示例选择 */}
        <select
          className={`text-xs rounded-md px-3 py-1.5 border focus:outline-none cursor-pointer transition-colors ${selectBg} ${selectText} ${selectBorder} focus:border-primary-500 hover:border-gray-500`}
          onChange={(e) => onExampleSelect(e.target.value)}
          defaultValue=""
        >
          <option value="" disabled>选择示例乐谱</option>
          {Object.entries(examples).map(([key, { name }]) => (
            <option key={key} value={key}>{name}</option>
          ))}
        </select>

        {/* 缩放控制 */}
        <div className={`flex items-center rounded-md border overflow-hidden ${isDarkTheme ? 'bg-gray-800 border-gray-700' : 'bg-gray-100 border-gray-300'}`}>
          <button
            className={`px-2 py-1.5 transition-colors ${isDarkTheme ? 'text-gray-400 hover:text-white hover:bg-gray-700' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-200'}`}
            onClick={onZoomOut}
            title="缩小"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className={`text-xs min-w-[42px] text-center ${isDarkTheme ? 'text-gray-400' : 'text-gray-500'}`}>{Math.round(zoom * 100)}%</span>
          <button
            className={`px-2 py-1.5 transition-colors ${isDarkTheme ? 'text-gray-400 hover:text-white hover:bg-gray-700' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-200'}`}
            onClick={onZoomIn}
            title="放大"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* 音符间距 */}
        <div className="flex items-center gap-1">
          <span className={`text-[10px] w-5 text-center ${subText}`}>音距</span>
          <input type="range" min="14" max="32" value={noteSpacing}
            className="w-16 h-1 accent-primary-500 cursor-pointer"
            onChange={e => onNoteSpacingChange(Number(e.target.value))}
            title={`音符间距: ${noteSpacing}px`} />
          <span className={`text-[10px] w-6 ${subText}`}>{noteSpacing}</span>
        </div>

        {/* 行间距 */}
        <div className="flex items-center gap-1">
          <span className={`text-[10px] w-5 text-center ${subText}`}>行距</span>
          <input type="range" min="4" max="36" value={rowGap}
            className="w-16 h-1 accent-primary-500 cursor-pointer"
            onChange={e => onRowGapChange(Number(e.target.value))}
            title={`行间距: ${rowGap}px`} />
          <span className={`text-[10px] w-6 ${subText}`}>{rowGap}</span>
        </div>

        {/* 导出按钮 */}
        <button
          className={`flex items-center gap-1.5 text-xs rounded-md px-3 py-1.5 font-medium transition-all ${
            isValid
              ? isDarkTheme
                ? 'bg-primary-500 text-white hover:bg-primary-600 shadow-md shadow-primary-500/25'
                : 'bg-primary-600 text-white hover:bg-primary-700 shadow-md shadow-primary-600/25'
              : `${isDarkTheme ? 'bg-gray-700 text-gray-500' : 'bg-gray-200 text-gray-400'} cursor-not-allowed`
          }`}
          onClick={onExport}
          disabled={!isValid}
          title="导出 PNG 图片"
        >
          <Download className="w-3.5 h-3.5" />
          导出 PNG
        </button>
      </div>
    </div>
  );
}
