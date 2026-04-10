import { Link } from 'react-router-dom'
import '../styles/legal.css'

function TermsPage() {
  return (
    <div className="legal-page">
      <div className="legal-card">
        <Link to="/login" className="legal-back">&larr; Back to Login</Link>
        <h1>Terms of Service</h1>
        <p className="legal-updated">Last updated: April 9, 2026</p>

        <section>
          <h2>1. Acceptance of Terms</h2>
          <p>
            By accessing or using CodePulse ("the Service"), you agree to be bound by these
            Terms of Service. If you do not agree to these terms, do not use the Service.
          </p>
        </section>

        <section>
          <h2>2. Description of Service</h2>
          <p>
            CodePulse is a hybrid static analysis and machine learning pipeline for automated
            Python bug detection. The Service allows users to submit Python source code for
            analysis and receive automated quality reports.
          </p>
        </section>

        <section>
          <h2>3. User Accounts</h2>
          <p>
            You are responsible for maintaining the confidentiality of your account credentials.
            You agree to provide accurate information during registration and to update it as
            necessary. You must notify us immediately of any unauthorized use of your account.
          </p>
        </section>

        <section>
          <h2>4. Acceptable Use</h2>
          <p>You agree not to:</p>
          <ul>
            <li>Use the Service for any unlawful purpose</li>
            <li>Submit malicious code designed to exploit or damage the Service</li>
            <li>Attempt to gain unauthorized access to the Service or its infrastructure</li>
            <li>Interfere with or disrupt the Service for other users</li>
            <li>Reverse engineer, decompile, or disassemble the Service</li>
          </ul>
        </section>

        <section>
          <h2>5. Intellectual Property</h2>
          <p>
            You retain all rights to the code you submit for analysis. CodePulse does not claim
            ownership of your submitted content. The Service, including its analysis engines,
            models, and interface, is the intellectual property of the CodePulse team.
          </p>
        </section>

        <section>
          <h2>6. Data Handling</h2>
          <p>
            Submitted code is processed for analysis purposes and stored in association with
            your account. You may export or delete your data at any time through your account
            settings. See our <Link to="/privacy">Privacy Policy</Link> for full details.
          </p>
        </section>

        <section>
          <h2>7. Disclaimer of Warranties</h2>
          <p>
            The Service is provided "as is" without warranties of any kind. CodePulse does not
            guarantee that analysis results are complete, accurate, or free of errors. The
            Service should not be used as the sole means of validating code for production use.
          </p>
        </section>

        <section>
          <h2>8. Limitation of Liability</h2>
          <p>
            To the maximum extent permitted by law, CodePulse shall not be liable for any
            indirect, incidental, special, or consequential damages arising from your use of
            the Service.
          </p>
        </section>

        <section>
          <h2>9. Changes to Terms</h2>
          <p>
            We reserve the right to modify these terms at any time. Continued use of the
            Service after changes constitutes acceptance of the updated terms.
          </p>
        </section>

        <section>
          <h2>10. Contact</h2>
          <p>
            Questions about these terms may be directed to{' '}
            <a href="mailto:codepulsepp@gmail.com">codepulsepp@gmail.com</a>.
          </p>
        </section>
      </div>
    </div>
  )
}

export default TermsPage
