import { useState } from 'react'
import Editor from '@monaco-editor/react'

/**
 * Code editor panel with a "Run Analysis" trigger.
 *
 * @param {Object} props
 * @param {function(string): void} props.onRun - Called with the current editor
 *   content when the user clicks "Run Analysis".
 * @param {boolean} props.loading - When true, the run button is disabled.
 */
function CodeEditor({ onRun, loading }) {
  const [code, setCode] = useState('')

  return (
    <div className="editor-panel">
      <div className="panel-header">
        <h2 className="panel-title">Code Editor</h2>
        <button
          className="run-btn"
          onClick={() => onRun(code)}
          disabled={loading}
        >
          {loading ? 'Analyzing…' : 'Run Analysis'}
        </button>
      </div>
      <Editor
        height="400px"
        defaultLanguage="python"
        theme="vs-dark"
        value={code}
        onChange={(value) => setCode(value ?? '')}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          scrollBeyondLastLine: false,
        }}
      />
    </div>
  )
}

export default CodeEditor
