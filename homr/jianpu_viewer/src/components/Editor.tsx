import { useRef, useCallback, forwardRef, useImperativeHandle } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import type { Score } from '../types';
import schema from '../schema/jianpu.schema.json';

export interface EditorHandle {
  scrollToLine: (line: number) => void;
  revealLine: (line: number) => void;
}

interface EditorProps {
  value: string;
  onChange: (value: string, score: Score | null) => void;
  isDarkTheme?: boolean;
}

const JsonEditor = forwardRef<EditorHandle, EditorProps>(({ value, onChange, isDarkTheme = true }, ref) => {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  useImperativeHandle(ref, () => ({
    scrollToLine(line: number) {
      editorRef.current?.revealLineInCenter(line);
    },
    revealLine(line: number) {
      editorRef.current?.revealLineInCenter(line);
    },
  }), []);

  const handleMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;
    monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
      validate: true,
      schemas: [{
        uri: 'jianpu://schema',
        fileMatch: ['*'],
        schema,
      }],
    });
  }, []);

  const handleChange = useCallback((val: string | undefined) => {
    const str = val || '';
    let score: Score | null = null;
    try {
      const parsed = JSON.parse(str);
      if (parsed && typeof parsed === 'object' && parsed.measures) {
        score = parsed as Score;
      }
    } catch {
      // JSON 解析失败，score 保持 null
    }
    onChange(str, score);
  }, [onChange]);

  return (
    <div className="h-full w-full overflow-hidden">
      <Editor
        height="100%"
        defaultLanguage="json"
        value={value}
        onChange={handleChange}
        onMount={handleMount}
        theme={isDarkTheme ? 'vs-dark' : 'light'}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          tabSize: 2,
          automaticLayout: true,
          padding: { top: 12 },
          renderWhitespace: 'none',
          bracketPairColorization: { enabled: true },
        }}
      />
    </div>
  );
});

export default JsonEditor;
