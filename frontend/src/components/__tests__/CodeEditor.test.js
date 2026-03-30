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
  it('renders the editor and run button', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    expect(screen.getByTestId('mock-editor')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /run analysis/i })).toBeInTheDocument()
  })

  it('calls onRun with the current editor content when button is clicked', () => {
    const onRun = jest.fn()
    render(<CodeEditor code='print("hello")' onCodeChange={() => {}} onRun={onRun} loading={false} />)

    fireEvent.click(screen.getByRole('button', { name: /run analysis/i }))

    expect(onRun).toHaveBeenCalledWith('print("hello")')
  })

  it('disables the run button when loading is true', () => {
    render(<CodeEditor code="x = 1" onCodeChange={() => {}} onRun={() => {}} loading={true} />)
    expect(screen.getByRole('button', { name: /analyzing/i })).toBeDisabled()
  })

  it('renders the copy button and it is disabled when code is empty', () => {
    render(<CodeEditor code="" onCodeChange={() => {}} onRun={() => {}} loading={false} />)
    expect(screen.getByRole('button', { name: /copy/i })).toBeDisabled()
  })
})
