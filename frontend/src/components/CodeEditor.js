import Editor from '@monaco-editor/react'

function CodeEditor({ code, onCodeChange, onRun, loading }) {
  return (
    <div className="editor-panel">
      <div className="editor-toolbar">
        <span className="editor-label">Editor</span>
        <button
          className="run-btn"
          onClick={() => onRun(code)}
          disabled={loading || !code?.trim()}
        >
          {loading ? 'Analyzing…' : 'Run Analysis'}
        </button>
      </div>
      <div className="editor-monaco">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs"
          value={code}
          onChange={(value) => onCodeChange(value ?? '')}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            scrollBeyondLastLine: false,
            lineNumbersMinChars: 3,
            padding: { top: 8 },
          }}
        />
      </div>
    </div>
  )
}

export default CodeEditor
