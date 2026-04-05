import { useEffect, useRef, useState } from 'react'
import Editor from '@monaco-editor/react'

const STAR_PATH = 'M 0 -10 L 2.2 -2.2 L 10 0 L 2.2 2.2 L 0 10 L -2.2 2.2 L -10 0 L -2.2 -2.2 Z'
const RAND = (min, max) => Math.floor(Math.random() * (max - min + 1) + min)
const SIGN = () => (Math.random() > 0.5 ? -1 : 1)

const DEFAULT_SETTINGS = {
  fontSize: 13,
  tabSize: 4,
  wordWrap: 'on',
  fontLigatures: true,
  renderWhitespace: 'trailing',
  bracketPairColorization: true,
  smoothScrolling: true,
  folding: true,
  renderLineHighlight: 'gutter',
  mouseWheelZoom: true,
  theme: 'auto',
}

// ── Settings toggle helper ────────────────────────────────────────────────────
function SettingsToggle({ id, checked, onChange }) {
  return (
    <button
      id={id}
      role="switch"
      aria-checked={checked}
      className={`settings-toggle${checked ? ' settings-toggle--on' : ''}`}
      onClick={() => onChange(!checked)}
    >
      <span className="settings-toggle-thumb" />
    </button>
  )
}

// ── Settings panel sub-component ─────────────────────────────────────────────
function EditorSettingsPanel({ settings, onChangeSetting, onReset }) {
  return (
    <div className="editor-settings-panel" role="dialog" aria-label="Editor settings">

      {/* ── Editable settings ── */}
      <div className="settings-section-title">Editor Settings</div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-fontSize">Font Size</label>
        <input
          id="setting-fontSize"
          className="settings-input-number"
          type="number"
          min={10}
          max={24}
          value={settings.fontSize}
          onChange={(e) => onChangeSetting('fontSize', Number(e.target.value))}
        />
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-tabSize">Tab Size</label>
        <select
          id="setting-tabSize"
          className="settings-select"
          value={settings.tabSize}
          onChange={(e) => onChangeSetting('tabSize', Number(e.target.value))}
        >
          <option value={2}>2</option>
          <option value={4}>4</option>
          <option value={8}>8</option>
        </select>
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-wordWrap">Word Wrap</label>
        <select
          id="setting-wordWrap"
          className="settings-select"
          value={settings.wordWrap}
          onChange={(e) => onChangeSetting('wordWrap', e.target.value)}
        >
          <option value="on">On</option>
          <option value="off">Off</option>
        </select>
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-fontLigatures">Font Ligatures</label>
        <SettingsToggle
          id="setting-fontLigatures"
          checked={settings.fontLigatures}
          onChange={(v) => onChangeSetting('fontLigatures', v)}
        />
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-renderWhitespace">Whitespace</label>
        <select
          id="setting-renderWhitespace"
          className="settings-select"
          value={settings.renderWhitespace}
          onChange={(e) => onChangeSetting('renderWhitespace', e.target.value)}
        >
          <option value="none">None</option>
          <option value="boundary">Boundary</option>
          <option value="trailing">Trailing</option>
          <option value="all">All</option>
        </select>
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-bracketPairColorization">Bracket Colors</label>
        <SettingsToggle
          id="setting-bracketPairColorization"
          checked={settings.bracketPairColorization}
          onChange={(v) => onChangeSetting('bracketPairColorization', v)}
        />
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-smoothScrolling">Smooth Scroll</label>
        <SettingsToggle
          id="setting-smoothScrolling"
          checked={settings.smoothScrolling}
          onChange={(v) => onChangeSetting('smoothScrolling', v)}
        />
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-folding">Code Folding</label>
        <SettingsToggle
          id="setting-folding"
          checked={settings.folding}
          onChange={(v) => onChangeSetting('folding', v)}
        />
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-renderLineHighlight">Line Highlight</label>
        <select
          id="setting-renderLineHighlight"
          className="settings-select"
          value={settings.renderLineHighlight}
          onChange={(e) => onChangeSetting('renderLineHighlight', e.target.value)}
        >
          <option value="none">None</option>
          <option value="gutter">Gutter</option>
          <option value="line">Line</option>
          <option value="all">All</option>
        </select>
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-mouseWheelZoom">Ctrl+Scroll Zoom</label>
        <SettingsToggle
          id="setting-mouseWheelZoom"
          checked={settings.mouseWheelZoom}
          onChange={(v) => onChangeSetting('mouseWheelZoom', v)}
        />
      </div>

      <div className="settings-row">
        <label className="settings-label" htmlFor="setting-theme">Theme</label>
        <select
          id="setting-theme"
          className="settings-select"
          value={settings.theme}
          onChange={(e) => onChangeSetting('theme', e.target.value)}
        >
          <option value="auto">Auto</option>
          <option value="vs-dark">Dark</option>
          <option value="vs">Light</option>
          <option value="auto-hc">Auto (High Contrast)</option>
          <option value="hc-black">High Contrast Dark</option>
          <option value="hc-light">High Contrast Light</option>
        </select>
      </div>
      <div className="settings-row-hint">Auto follows the app theme toggle</div>

      {/* ── Fixed (locked) settings ── */}
      <div className="settings-divider" />
      <div className="settings-section-title">Fixed Settings</div>

      <div className="settings-row settings-row--locked">
        <span className="settings-label">Minimap</span>
        <span className="settings-locked-value">Off</span>
      </div>
      <div className="settings-row-hint">Disabled to maximize editor space</div>

      <div className="settings-row settings-row--locked">
        <span className="settings-label">Scroll Beyond Last Line</span>
        <span className="settings-locked-value">Off</span>
      </div>
      <div className="settings-row-hint">Controlled by app layout</div>

      <div className="settings-row settings-row--locked">
        <span className="settings-label">Language</span>
        <span className="settings-locked-value">Python</span>
      </div>
      <div className="settings-row-hint">Only Python analysis is supported</div>

      <button className="settings-reset-btn" onClick={onReset}>
        Reset to Defaults
      </button>
    </div>
  )
}

// FR-DASH-001
// FR-DASH-002
function CodeEditor({ code, onCodeChange, onRun, loading, isDark, highlightLine }) {
  const btnRef = useRef(null)
  const editorRef = useRef(null)
  const decorationsRef = useRef([])
  const [copied, setCopied] = useState(false)

  const [settings, setSettings] = useState(() => {
    try {
      const raw = localStorage.getItem('codepulse_editor_settings')
      return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : DEFAULT_SETTINGS
    } catch {
      return DEFAULT_SETTINGS
    }
  })
  const [settingsOpen, setSettingsOpen] = useState(false)
  const settingsPanelRef = useRef(null)

  const handleCopy = () => {
    if (!code?.trim()) return
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  const handleChangeSetting = (key, value) =>
    setSettings((prev) => ({ ...prev, [key]: value }))

  const handleResetSettings = () => {
    setSettings(DEFAULT_SETTINGS)
    localStorage.removeItem('codepulse_editor_settings')
  }

  useEffect(() => {
    const editor = editorRef.current
    if (!editor) return
    if (highlightLine != null) {
      decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [{
        range: { startLineNumber: highlightLine, endLineNumber: highlightLine, startColumn: 1, endColumn: 1 },
        options: { isWholeLine: true, className: 'editor-highlight-line' },
      }])
    } else {
      decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [])
    }
  }, [highlightLine])

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

  useEffect(() => {
    localStorage.setItem('codepulse_editor_settings', JSON.stringify(settings))
  }, [settings])

  useEffect(() => {
    if (!settingsOpen) return
    const handler = (e) => {
      if (settingsPanelRef.current && !settingsPanelRef.current.contains(e.target)) {
        setSettingsOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [settingsOpen])

  return (
    <div className="editor-panel">
      <div className="editor-toolbar">
        <div className="editor-toolbar-left">
          <span className="editor-label">Editor</span>

          <div className="editor-settings-wrapper" ref={settingsPanelRef}>
            <button
              className="settings-gear-btn"
              onClick={() => setSettingsOpen((v) => !v)}
              aria-haspopup="dialog"
              aria-expanded={settingsOpen}
              aria-label="Editor settings"
              title="Editor settings"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" width="14" height="14">
                <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
              </svg>
            </button>

            {settingsOpen && (
              <EditorSettingsPanel
                settings={settings}
                onChangeSetting={handleChangeSetting}
                onReset={handleResetSettings}
              />
            )}
          </div>
        </div>
        <div className="editor-toolbar-right">
          <button
            className="copy-btn"
            onClick={handleCopy}
            disabled={!code?.trim()}
            title="Copy code"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
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
      </div>
      <div className="editor-monaco">
        <Editor
          height="100%"
          defaultLanguage="python"
          theme={
            settings.theme === 'auto' ? (isDark ? 'vs-dark' : 'vs') :
            settings.theme === 'auto-hc' ? (isDark ? 'hc-black' : 'hc-light') :
            settings.theme
          }
          value={code}
          onMount={(editor) => { editorRef.current = editor }}
          onChange={(value) => onCodeChange(value ?? '')}
          options={{
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbersMinChars: 3,
            padding: { top: 8 },
            fontSize: settings.fontSize,
            tabSize: settings.tabSize,
            wordWrap: settings.wordWrap,
            fontLigatures: settings.fontLigatures,
            renderWhitespace: settings.renderWhitespace,
            bracketPairColorization: { enabled: settings.bracketPairColorization },
            smoothScrolling: settings.smoothScrolling,
            folding: settings.folding,
            renderLineHighlight: settings.renderLineHighlight,
            mouseWheelZoom: settings.mouseWheelZoom,
          }}
        />
      </div>
    </div>
  )
}

export default CodeEditor
