import { render, screen, fireEvent } from '@testing-library/react'
import CodeEditor from '../CodeEditor'

// Monaco Editor doesn't work in jsdom — replace it with a plain textarea
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange }) => (
    <textarea
      data-testid="mock-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}))

describe('CodeEditor', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  // TC-DASH-001
  it('renders the editor and run button', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    expect(screen.getByTestId('mock-editor')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /run analysis/i })).toBeInTheDocument()
  })

  // TC-DASH-002
  it('calls onRun with the current editor content when button is clicked', () => {
    const onRun = jest.fn()
    render(<CodeEditor code='print("hello")' onCodeChange={() => {}} onRun={onRun} loading={false} />)

    fireEvent.click(screen.getByRole('button', { name: /run analysis/i }))

    expect(onRun).toHaveBeenCalledWith('print("hello")')
  })

  // TC-DASH-003
  it('disables the run button when loading is true', () => {
    render(<CodeEditor code="x = 1" onCodeChange={() => {}} onRun={() => {}} loading={true} />)
    expect(screen.getByRole('button', { name: /analyzing/i })).toBeDisabled()
  })

  // TC-DASH-004
  it('renders the copy button and it is disabled when code is empty', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    expect(screen.getByRole('button', { name: /copy/i })).toBeDisabled()
  })

  // TC-DASH-005
  it('renders the settings gear button with correct ARIA attributes', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    const btn = screen.getByRole('button', { name: /editor settings/i })
    expect(btn).toBeInTheDocument()
    expect(btn).toHaveAttribute('aria-haspopup', 'dialog')
    expect(btn).toHaveAttribute('aria-expanded', 'false')
  })

  // TC-DASH-006
  it('opens the settings panel when the gear button is clicked', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    const btn = screen.getByRole('button', { name: /editor settings/i })
    fireEvent.click(btn)
    expect(screen.getByRole('dialog', { name: /editor settings/i })).toBeInTheDocument()
    expect(btn).toHaveAttribute('aria-expanded', 'true')
  })

  // TC-DASH-007
  it('closes the settings panel when clicking outside', () => {
    render(
      <div>
        <CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />
        <button>outside</button>
      </div>
    )
    fireEvent.click(screen.getByRole('button', { name: /editor settings/i }))
    expect(screen.getByRole('dialog', { name: /editor settings/i })).toBeInTheDocument()
    fireEvent.mouseDown(screen.getByRole('button', { name: /outside/i }))
    expect(screen.queryByRole('dialog', { name: /editor settings/i })).not.toBeInTheDocument()
  })

  // TC-DASH-008
  it('updates fontSize setting when the number input changes', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    fireEvent.click(screen.getByRole('button', { name: /editor settings/i }))
    const input = screen.getByLabelText(/font size/i)
    fireEvent.change(input, { target: { value: '16' } })
    expect(input).toHaveValue(16)
  })

  // TC-DASH-009
  it('toggles fontLigatures when its switch is clicked', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    fireEvent.click(screen.getByRole('button', { name: /editor settings/i }))
    const toggle = screen.getByRole('switch', { name: /font ligatures/i })
    expect(toggle).toHaveAttribute('aria-checked', 'true')
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  // TC-DASH-010
  it('persists settings to localStorage when a setting changes', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    fireEvent.click(screen.getByRole('button', { name: /editor settings/i }))
    fireEvent.change(screen.getByLabelText(/font size/i), { target: { value: '18' } })
    const stored = JSON.parse(localStorage.getItem('codepulse_editor_settings'))
    expect(stored.fontSize).toBe(18)
  })

  // TC-DASH-011
  it('initialises settings from localStorage on mount', () => {
    localStorage.setItem('codepulse_editor_settings', JSON.stringify({ fontSize: 20 }))
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    fireEvent.click(screen.getByRole('button', { name: /editor settings/i }))
    expect(screen.getByLabelText(/font size/i)).toHaveValue(20)
  })
})
