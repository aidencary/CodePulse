import { useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'

const STAR_PATH = 'M 0 -10 L 2.2 -2.2 L 10 0 L 2.2 2.2 L 0 10 L -2.2 2.2 L -10 0 L -2.2 -2.2 Z'
const RAND = (min, max) => Math.floor(Math.random() * (max - min + 1) + min)
const SIGN = () => (Math.random() > 0.5 ? -1 : 1)

function CodeEditor({ code, onCodeChange, onRun, loading, isDark }) {
  const btnRef = useRef(null)

  useEffect(() => {
    if (!btnRef.current) return
    btnRef.current.querySelectorAll('.particle').forEach(p => {
      p.style.setProperty('--x', RAND(20, 80))
      p.style.setProperty('--y', RAND(20, 80))
      p.style.setProperty('--dur', RAND(6, 20))
      p.style.setProperty('--delay', RAND(-12, 0))
      p.style.setProperty('--ox', `${RAND(300, 800) * SIGN()}%`)
      p.style.setProperty('--oy', `${RAND(300, 800) * SIGN()}%`)
    })
  }, [])

  return (
    <div className="editor-panel">
      <div className="editor-toolbar">
        <div className="editor-toolbar-left">
          <span className="editor-label">Editor</span>
        </div>
        <button
          ref={btnRef}
          className="sparkle-btn"
          onClick={() => onRun(code)}
          disabled={loading || !code?.trim()}
        >
          {Array.from({ length: 8 }, (_, i) => (
            <span key={i} className="particle" aria-hidden="true">
              <svg viewBox="-12 -12 24 24">
                <path d={STAR_PATH} />
              </svg>
            </span>
          ))}
          <span className="btn-label">{loading ? 'Analyzing…' : 'Run Analysis'}</span>
        </button>
      </div>
      <div className="editor-monaco">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme={isDark ? 'vs-dark' : 'vs'}
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
