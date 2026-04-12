import { useEffect } from 'react'

function HelpModal({ onClose }) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  const handleBackdrop = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div className="help-backdrop" data-testid="help-backdrop" onClick={handleBackdrop}>
      <div
        className="help-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="help-title"
      >
        <div className="help-header">
          <h2 className="help-title" id="help-title">How CodePulse Works</h2>
          <button
            className="help-close"
            onClick={onClose}
            aria-label="Close help"
            type="button"
          >
            ✕
          </button>
        </div>

        <div className="help-body">
          <section className="help-section">
            <h3>Getting Started</h3>
            <ol>
              <li>Paste or write Python code in the editor on the left.</li>
              <li>Optionally give your submission a name in the toolbar.</li>
              <li>Click <strong>Run Analysis</strong> to score your code.</li>
              <li>Review the results panel on the right, then drag its left edge to resize it.</li>
              <li>Click a submission in the sidebar to reload it. Click <strong>Export</strong> to download a printable HTML report.</li>
            </ol>
          </section>

          <section className="help-section">
            <h3>Reading the Score</h3>
            <p>
              Your overall score starts at <strong>100</strong> and drops based on the issues found. Each static finding and each
              unflagged predicted bug subtracts a penalty proportional to its severity. The colored ring around the number gives
              you a quick read: <span className="help-swatch help-swatch--good" /> green is healthy, <span className="help-swatch help-swatch--fair" /> yellow is borderline,
              and <span className="help-swatch help-swatch--poor" /> red means the code needs real attention.
            </p>
          </section>

          <section className="help-section">
            <h3>Static Analysis</h3>
            <p>
              These are deterministic checks run against the AST of your code — things like missing docstrings,
              bare <code>except</code> clauses, mutable default arguments, and many more. They are fast, reproducible,
              and always correct about what they report, because they don't guess. Severity is either <em>Low</em>,
              <em>Med</em>, or <em>High</em>. Hover a finding to highlight its line in the editor.
            </p>
          </section>

          <section className="help-section">
            <h3>AI Bug Predictions</h3>
            <p>
              A language model reviews your code and proposes latent bugs that static analysis can't catch — logic errors, null
              dereferences, race conditions, off-by-one mistakes, and similar. Each prediction includes a short description and
              a suggested fix you can expand. Because these are generated, they are <strong>predictions, not proofs</strong>:
              treat them as leads to investigate rather than facts.
            </p>
          </section>

          <section className="help-section">
            <h3>CodeBERT Confidence</h3>
            <p>
              Every AI-predicted bug is re-scored by a fine-tuned CodeBERT model that estimates the probability the line is
              actually buggy. That percentage shows up as a pill on each bug card. Use the <strong>Min confidence</strong> slider
              above the bug list to hide low-confidence predictions.
            </p>
            <ul>
              <li><strong>High confidence (≥ 70%)</strong> — CodeBERT agrees with the LLM. Most likely a real issue.</li>
              <li><strong>Medium (30–70%)</strong> — worth a look but not guaranteed.</li>
              <li><strong>Low (&lt; 30%)</strong> — CodeBERT thinks this is likely a false positive. The bug is <em>flagged</em>, visually dimmed, and excluded from your overall score.</li>
            </ul>
            <p>
              This is why your score can stay high even when the LLM surfaces bugs: flagged predictions don't cost you points.
              The flag is the model's way of saying "the LLM may have hallucinated this one."
            </p>
          </section>

          <section className="help-section">
            <h3>Tips</h3>
            <ul>
              <li>Click the <code>✕</code> on any finding or bug to ignore it for the rest of the session.</li>
              <li>Use the <strong>Severity</strong> / <strong>Line</strong> pills to re-sort either list.</li>
              <li>Toggle severity-colored line highlights from the editor settings (the gear in the editor toolbar).</li>
              <li>Running analysis on identical code will give you identical results — predictions are deterministic.</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  )
}

export default HelpModal
