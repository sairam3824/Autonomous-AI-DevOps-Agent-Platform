'use client';
import dynamic from 'next/dynamic';

const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface YAMLEditorProps {
  value: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  height?: string;
}

export default function YAMLEditor({ value, onChange, readOnly = false, height = '420px' }: YAMLEditorProps) {
  return (
    <div className="premium-surface rounded-[30px] p-4">
      <div className="mb-3 flex items-center justify-between px-2">
        <div>
          <p className="premium-label">Pipeline Content</p>
          <p className="mt-1 text-lg text-[var(--ink)]">{readOnly ? 'Preview' : 'Editor'}</p>
        </div>
        <span className="rounded-full bg-white/56 px-3 py-1 text-xs text-[var(--ink-soft)]">{readOnly ? 'Read only' : 'Editable'}</span>
      </div>
      <div className="overflow-hidden rounded-[24px] bg-[rgba(250,247,241,0.9)]">
        <Editor
          height={height}
          defaultLanguage="yaml"
          value={value}
          onChange={(val) => onChange?.(val || '')}
          theme="vs-light"
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            padding: { top: 12 },
            wordWrap: 'on',
            tabSize: 2,
          }}
        />
      </div>
    </div>
  );
}
